"""midna_kronos_topk's producer end to end: the original scripts/kronos-forecast.py (paper-desk 68315288, blob
f44b3aef) run unmodified vs desk/feedlib/midna_kronos_runner.py fed by the family job's hub rows
(midna_kronos.bar_rows), both on Kronos-base @ 2b554741 with Kronos-Tokenizer-base from the weights cache, on one
CPU thread. Run it with the interpreter that carries torch (the job's midna_kronos_python):

    <torch python> -m tools.parity.midna_kronos_forecast <weights dir>

Per case, deterministic from the seed: daily payloads for some of the 24 names (random walks of 95-130 completed
sessions ending at the case's signal day, with rows the source drops: a missing field, a zero close, a negative
volume), one name short of the 90-session context, the rest unserved. The source fetches through a stubbed
urllib.request.urlopen answering Yahoo chart JSON built from the payloads (an unserved name raises); the port reads the
rows file the job writes from the same bars as the hub serves them ({t, o, h, l, c, v}). One model is loaded and
shared (from_pretrained memoised: the same files either way), and torch's generator is seeded before each forecast
by the forecast's ordinal, identically in both runs (the predictor samples ten paths at T 0.6, top-p 0.9).
Compared exactly: the whole kronos-forecast.json (status, signal day, every score / last close / forecast close in
order, error, note, model fields). The source's module globals OUT / WEIGHTS point at the case's scratch dir and the
weights cache. Two cases (a ready forecast, and an error with fewer than four scores): each forecast costs about 40 s
on one thread, so the case count is bounded by the model's cost, not by choice."""
import importlib.util
import io
import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

from desk.feedlib import midna_kronos as MK
from desk.feedlib import midna_kronos_runner as RN

from . import write_receipt
from .midna_common import check_pin

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "desk", "vendor",
                      "midna", "kronos")
CASES = [{"served": 6, "short": 1, "signal": "2026-03-13"}, {"served": 3, "short": 0, "signal": "2026-07-02"}]


def walk(rnd, days):
    c, out = rnd.uniform(20, 400), []
    for d in days:
        o = c
        c = max(0.5, c * (1 + rnd.gauss(0.0005, 0.02)))
        out.append({"day": d, "open": round(o, 4), "high": round(max(o, c) * (1 + abs(rnd.gauss(0, 0.006))), 4),
                    "low": round(min(o, c) * (1 - abs(rnd.gauss(0, 0.006))), 4), "close": round(c, 4),
                    "volume": float(rnd.randint(200_000, 40_000_000))})
    return out


def sessions_to(last, n):
    out, d = [], last
    while len(out) < n:
        out.append(d)
        d = RN.datetime.strptime(d, "%Y-%m-%d")
        d -= RN.timedelta(days=1)
        while d.weekday() >= 5 or d.strftime("%Y-%m-%d") in RN.HOLIDAYS:
            d -= RN.timedelta(days=1)
        d = d.strftime("%Y-%m-%d")
    return out[::-1]


def gen_case(rnd, spec):
    names = list(RN.UNIVERSE)
    rnd.shuffle(names)
    data = {}
    for i, sym in enumerate(names[:spec["served"] + spec["short"]]):
        n = 80 if i >= spec["served"] else rnd.randint(95, 130)
        rows = walk(rnd, sessions_to(spec["signal"], n))
        if i < spec["served"]:
            for j in rnd.sample(range(5, n - 1), 3):           # rows the source drops (inside the window or not)
                k = rnd.choice(["open", "close", "volume"])
                rows[j][k] = {"open": None, "close": 0.0, "volume": -1.0}[k]
        data[sym] = rows
    return data


def stamp(day):
    """Yahoo's daily stamp: the session's 09:30 ET open (13:30 / 14:30 UTC, the same UTC date)."""
    from desk.sleeves.midna import common as M
    return int(M.et_to_epoch(day, 9, 30))


def chart(rows):
    return {"chart": {"result": [{"timestamp": [stamp(r["day"]) for r in rows],
                                  "indicators": {"quote": [{k: [r[k] for r in rows] for k in
                                                            ("open", "high", "low", "close", "volume")}]}}],
                      "error": None}}


def hub_bars(rows):
    return [{"t": stamp(r["day"]), "o": r["open"], "h": r["high"], "l": r["low"], "c": r["close"], "v": r["volume"]}
            for r in rows]


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def run(weights, seed=20261016):
    os.environ["HF_HUB_OFFLINE"] = "1"
    sys.path.insert(0, VENDOR)
    import torch
    import model as KM                                            # the vendored model package (byte-exact)
    torch.set_num_threads(1)
    loaded = {}
    for cls in (KM.Kronos, KM.KronosTokenizer):
        orig = cls.from_pretrained

        def memo(*a, _orig=orig, _name=cls.__name__, **kw):
            key = (_name, a[0] if a else None, kw.get("revision"))
            if key not in loaded:
                loaded[key] = _orig(*a, **kw)
            return loaded[key]
        cls.from_pretrained = memo
    calls = {"n": 0}
    predict = KM.KronosPredictor.predict

    def seeded(self, *a, **kw):
        torch.manual_seed(1000 + calls["n"])
        calls["n"] += 1
        return predict(self, *a, **kw)
    KM.KronosPredictor.predict = seeded

    src_path = check_pin("paper", "scripts/kronos-forecast.py")
    work = tempfile.mkdtemp(prefix="midna_kronos_fc_")
    rnd = random.Random(seed)
    diffs, stats, t0 = [], {"forecasts": 0, "scores": 0, "errors_listed": 0, "statuses": []}, time.time()
    import urllib.request
    real_urlopen = urllib.request.urlopen
    try:
        for ci, spec in enumerate(CASES):
            data = gen_case(rnd, spec)
            case_dir = os.path.join(work, f"c{ci}")
            os.makedirs(os.path.join(case_dir, "scripts"))
            shutil.copyfile(src_path, os.path.join(case_dir, "scripts", "kronos-forecast.py"))
            # -- the source, unmodified: its fetch answered from the payloads
            def urlopen(request, timeout=None, _data=data):
                sym = request.full_url.split("/chart/")[1].split("?")[0]
                if sym not in _data:
                    raise LookupError("the desk's data hub served none")
                return _Resp(json.dumps(chart(_data[sym])).encode())
            urllib.request.urlopen = urlopen
            spec_ = importlib.util.spec_from_file_location(f"kronos_forecast_src_{ci}",
                                                           os.path.join(case_dir, "scripts", "kronos-forecast.py"))
            src = importlib.util.module_from_spec(spec_)
            spec_.loader.exec_module(src)
            src.WEIGHTS = Path(weights)
            calls["n"] = 0
            rc_src = src.main()
            urllib.request.urlopen = real_urlopen
            n_src = calls["n"]
            doc_src = json.load(open(src.OUT))
            # -- the port, on the job's rows file built from the same bars
            rows = {s: MK.bar_rows(hub_bars(r), spec["signal"]) for s, r in data.items()}
            rows_path = os.path.join(case_dir, "kronos-input.json")
            with open(rows_path, "w") as f:
                json.dump({"asOf": spec["signal"], "rows": {s: r for s, r in rows.items() if r}}, f)
            out = os.path.join(case_dir, "port", "kronos-forecast.json")
            calls["n"] = 0
            rc_port = RN.main(out, weights, spec["signal"], rows_path)
            doc_port = json.load(open(out))
            stats["forecasts"] += n_src + calls["n"]
            stats["scores"] += len(doc_src.get("scores") or [])
            stats["errors_listed"] += len([e for e in (doc_src.get("error") or "").split("; ") if e])
            stats["statuses"].append(doc_src.get("status"))
            if doc_src != doc_port or rc_src != rc_port or n_src != calls["n"]:
                diffs.append({"case": ci, "rc": [rc_src, rc_port], "forecasts": [n_src, calls["n"]],
                              "source": doc_src, "port": doc_port})
            print(f"case {ci}: {doc_src.get('status')} scores={len(doc_src.get('scores') or [])} "
                  f"identical={doc_src == doc_port} {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    finally:
        urllib.request.urlopen = real_urlopen
        shutil.rmtree(work, ignore_errors=True)
    res = {"cases": len(CASES), "identical": len(CASES) - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:2],
           "stats": dict(stats, seconds=round(time.time() - t0), torch=torch.__version__),
           "sleeves": ["midna_kronos_topk"],
           "model": {"model": RN.MODEL, "tokenizer": RN.TOKENIZER, "revision": RN.REVISION},
           "method": "kronos-forecast.py run unmodified (urlopen stubbed with chart JSON of the case's rows; OUT / "
                     "WEIGHTS at the scratch dir and the weights cache) vs midna_kronos_runner.main on the job's rows "
                     "file (midna_kronos.bar_rows over the same bars); one shared Kronos-base load, torch seeded per "
                     "forecast by its ordinal in both runs, one thread; the whole forecast JSON exact"}
    write_receipt("midna_kronos_forecast", res)
    return res


if __name__ == "__main__":
    r = run(sys.argv[1])
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
