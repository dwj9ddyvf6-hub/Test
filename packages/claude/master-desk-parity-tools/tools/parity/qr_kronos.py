"""qr_kronos: the six-strategy reconstruction's frozen Kronos-base forecasts vs desk/sleeves/quant_research/kronos.py
(+ kronos_runner.py).

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/source.zip.parts, extracted
(SIXAI_X): kronos/scores-with-terminal-extension.csv (run_financial.py's scores: the released Kronos-base checkpoint,
the reconstruction's FP32 KV-cache predictor, seeds 100 + session index x 1000 + batch ordinal) and the real panel
(data/panel.npz).
PORT: on sampled forecast dates, kronos.job_input() from the panel's bars through the date (the production input
builder: eligibility, 90-session contexts with amount = volume x vwap, the next ten sessions, the panel session index)
and kronos_runner.py run by TORCH_PYTHON (the interpreter that carries torch) with the locked weights (downloaded to
KRONOS_WEIGHTS once, sha256-checked). Compared per name: the scored set exactly, the score within 1e-6 relative
(float32 forecasts; the same seeds and kernels should give bitwise-equal paths)."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from . import write_receipt

SIXAI_X = os.environ.get("SIXAI_X", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/"
                                    "sixai/x")
TORCH_PYTHON = os.environ.get("TORCH_PYTHON")
WEIGHTS = os.environ.get("KRONOS_WEIGHTS", os.path.join(tempfile.gettempdir(), "qr_kronos_weights"))
N_DATES = int(os.environ.get("KRONOS_PARITY_DATES", 6))


def frames_from_panel(z, upto_i, syms):
    dates = pd.DatetimeIndex(np.array(z["dates"][:upto_i + 1]))
    col = {s: j for j, s in enumerate(z["symbols"])}
    out = {}
    for s in syms:
        j = col[s]
        f = pd.DataFrame({k: np.array(z[n][:upto_i + 1, j], dtype=float)
                          for k, n in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume"),
                                       ("vw", "vwap"))}, index=dates)
        out[s] = f[np.array(z["valid"][:upto_i + 1, j])]
    return out


def run():
    from desk.sleeves.quant_research import kronos as K
    if not TORCH_PYTHON:
        raise SystemExit("set TORCH_PYTHON to an interpreter with torch")
    z = np.load(os.path.join(SIXAI_X, "data/panel.npz"), allow_pickle=False, mmap_mode="r")
    dates = list(np.array(z["dates"]))
    sc = pd.read_csv(os.path.join(SIXAI_X, "kronos/scores-with-terminal-extension.csv"), float_precision="round_trip")
    grid = sorted(sc.date.unique())
    rng = np.random.default_rng(11)
    picks = sorted(set([grid[0], grid[-1]]) | set(rng.choice(grid, max(0, N_DATES - 2), replace=False)))
    st = {"dates": 0, "scores": 0, "bad": 0, "set_bad": 0, "cadence_bad": 0, "max_rel": 0.0, "diffs": []}
    port_grid = [d for d in dates if K.is_forecast_date(d)]
    st["cadence_bad"] = len(set(port_grid) ^ set(d for d in grid if d in dates))
    os.makedirs(WEIGHTS, exist_ok=True)
    for d in picks:
        i = dates.index(d)
        frames = frames_from_panel(z, i, K.UNIVERSE)
        job, extra = K.job_input(frames, d)
        if d == dates[-1] or i + 10 >= len(dates):
            job["y_dates"] = K.next_sessions(d)
        tmp = tempfile.mkdtemp(prefix="qr_kronos_parity_")
        try:
            inp, out = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
            json.dump(job, open(inp, "w"))
            r = subprocess.run([TORCH_PYTHON, K.RUNNER, inp, out, WEIGHTS], capture_output=True, text=True,
                               timeout=7200)
            if r.returncode:
                raise RuntimeError(r.stderr[-2000:])
            res = json.load(open(out))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
        want = sc[sc.date == d].set_index("symbol")
        got = pd.Series(res["scores"])
        common = want.index.intersection(got.index)
        rel = np.abs(got[common].values - want.score[common].values) / np.maximum(1e-12, np.abs(want.score[common].values))
        seeds_ok = all(int(res["seeds"][s]) == int(want.seed[s]) for s in common)
        st["dates"] += 1
        st["scores"] += len(want)
        nb = int((rel > 1e-6).sum()) + (0 if seeds_ok else 1)
        sd = len(want.index.symmetric_difference(got.index))
        st["bad"] += nb
        st["set_bad"] += sd
        st["max_rel"] = max(st["max_rel"], float(rel.max()) if len(rel) else 0.0)
        if nb or sd:
            st["diffs"].append({"date": d, "bad": nb, "set_diff": sd, "seeds_ok": seeds_ok})
        print(d, json.dumps({k: st[k] for k in ("dates", "scores", "bad", "set_bad", "max_rel")}), flush=True)
    cases = st["scores"] + len(port_grid)
    nbad = st["bad"] + st["set_bad"] + st["cadence_bad"]
    out = {"family": "quant_research", "sleeves": ["qr_kronosbasezeroshotustransfer"], "cases": cases,
           "identical": cases - nbad, "n_diffs": nbad, "forecasts": st, "forecast_dates_checked": picks,
           "cadence_dates": len(port_grid), "torch_python": TORCH_PYTHON,
           "source": {"archive": "quant-research-critical@0be4c57569e363d052bd23564cf0664697439927 research/"
                                 "2026-10-08-six-strategy-reconstruction/source.zip.parts",
                      "scores_sha256": hashlib.sha256(open(os.path.join(
                          SIXAI_X, "kronos/scores-with-terminal-extension.csv"), "rb").read()).hexdigest()},
           "method": "the frozen run_financial scores vs kronos.job_input + kronos_runner on the real panel, same "
                     "seeds; the ten-session cadence over the panel's sessions"}
    write_receipt("qr_kronos", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["forecasts"])[:1000])
