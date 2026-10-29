"""Kronos-base forecasts for qr_kronosbasezeroshotustransfer, run in its own process by an interpreter that carries
torch (the desk job `qr_kronos`; tools/parity/qr_kronos.py). This is run_financial.py's per-date loop: the frozen
24-name universe's 90-session contexts (open, high, low, close, volume, amount = volume x vwap), the next ten session
dates, batches of four series in universe order seeded 100 + panel session index x 1000 + batch ordinal, the
reconstruction's FP32 KV-cache predictor (cached_inference.py, vendored) over the released Kronos-base and its
tokenizer (temperature 0.6, top-p 0.9, ten paths), score = (mean forecast close over the ten sessions - last close) /
last close.

usage: python kronos_runner.py <input.json> <output.json> <weights_dir>
input: {"t": int, "decision_date": str, "symbols": [...], "contexts": {sym: {field: [90 floats]}},
        "x_dates": [90 iso dates], "y_dates": [10 iso dates], "batch": 4, "threads": 2}
The weights are the lock's (desk/vendor/quant_research/kronos/weights-lock.json): read from <weights_dir> when their
sha256 match, else fetched from their pinned Hugging Face revisions into it."""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "vendor", "quant_research", "kronos")
FIELDS = ["open", "high", "low", "close", "volume", "amount"]
SEED = 100
REPOS = {"Kronos-base": "NeoQuasar/Kronos-base", "Kronos-Tokenizer-base": "NeoQuasar/Kronos-Tokenizer-base"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_weights(wdir):
    lock = json.load(open(os.path.join(VENDOR, "weights-lock.json")))
    for e in lock:
        if e["repo_id"] not in REPOS.values():
            continue
        name = e["repo_id"].split("/")[-1]
        dest = os.path.join(wdir, name, e["filename"])
        if os.path.exists(dest) and sha256(dest) == e["sha256"]:
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        from huggingface_hub import hf_hub_download
        got = hf_hub_download(e["repo_id"], e["filename"], revision=e["revision"], local_dir=os.path.dirname(dest))
        if os.path.abspath(got) != os.path.abspath(dest):
            os.replace(got, dest)
        if sha256(dest) != e["sha256"]:
            raise SystemExit(f"weights {e['repo_id']}/{e['filename']} differ from the lock")


def main(argv):
    inp, out, wdir = argv[1:4]
    job = json.load(open(inp))
    ensure_weights(wdir)
    sys.path.insert(0, os.path.join(VENDOR, "source", "vendor"))
    sys.path.insert(0, VENDOR)
    import numpy as np
    import pandas as pd
    import torch
    from model import Kronos, KronosTokenizer
    from cached_inference import CachedPredictor
    torch.set_num_threads(int(job.get("threads", 2)))
    torch.set_num_interop_threads(1)
    tokenizer = KronosTokenizer.from_pretrained(os.path.join(wdir, "Kronos-Tokenizer-base")).eval()
    model = Kronos.from_pretrained(os.path.join(wdir, "Kronos-base")).eval()
    predictor = CachedPredictor(model, tokenizer, device="cpu", max_context=512)
    t, syms = int(job["t"]), list(job["symbols"])
    x_ts = pd.Series(pd.to_datetime(job["x_dates"]))
    y_ts = pd.Series(pd.to_datetime(job["y_dates"]))
    scores, means, seeds, priors = {}, {}, {}, {}
    batch = int(job.get("batch", 4))
    for number, offset in enumerate(range(0, len(syms), batch)):
        sel = syms[offset:offset + batch]
        frames = [pd.DataFrame({k: np.array(job["contexts"][s][k], dtype=np.float64) for k in FIELDS}) for s in sel]
        seed = SEED + t * 1000 + number
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        preds = predictor.predict_batch(frames, [x_ts] * len(sel), [y_ts] * len(sel), 10, T=.6, top_k=0, top_p=.9,
                                        sample_count=10, verbose=False)
        for s, f, p in zip(sel, frames, preds):
            fm = float(p[FIELDS].to_numpy(dtype=np.float32)[:, 3].mean())
            prior = float(f["close"].values[-1])
            scores[s], means[s], seeds[s], priors[s] = (fm - prior) / prior, fm, seed, prior
    doc = {"decision_date": job["decision_date"], "t": t, "scores": scores, "forecast_mean_close": means,
           "prior_close": priors, "seeds": seeds, "torch": torch.__version__}
    with open(out + ".tmp", "w") as f:
        json.dump(doc, f)
    os.replace(out + ".tmp", out)


if __name__ == "__main__":
    main(sys.argv)
