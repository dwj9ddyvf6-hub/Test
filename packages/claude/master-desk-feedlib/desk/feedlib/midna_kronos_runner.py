"""Midna's Kronos-base forecast (scripts/kronos-forecast.py @ cursor/paper-desk-f184 68315288, blob f44b3aef), ported
line for line as a standalone runner (it needs torch, pandas, huggingface_hub, einops, tqdm and safetensors — run it
with the interpreter configured as midna_kronos_python):

    python -m desk.feedlib.midna_kronos_runner <out.json> <weights dir> <last completed session YYYY-MM-DD> [rows.json]

One Kronos-base forecast for the frozen 24-name shadow: for each name its last 90 completed daily sessions (Yahoo
1d range 2y; a row needs open / high / low / close / volume, close > 0, volume >= 0), amount = volume x mean(OHLC),
the next ten sessions' stamps (weekdays off the source's 2026 holiday table), KronosPredictor.predict(T 0.6, top_p 0.9,
ten paths averaged inside the released predictor, pred_len 10, max_context 512) from NeoQuasar/Kronos-base at
revision 2b554741 with NeoQuasar/Kronos-Tokenizer-base; score = the tenth forecast close / the last close - 1; sorted
best first; "ready" with four or more scores, else "error" (no order).

The model code is vendored byte-exact (desk/vendor/midna/kronos/model, the source's vendor/kronos/model). Named
divergences: the rows are cut at the last completed session (the desk kicked the script at its 09:20 pass, when
Yahoo's daily chart held completed sessions only); the weights cache is the desk's (cache/midna/kronos-weights); with
a rows file (the family job's: each name's daily rows read through the desk's data hub, parseBars's filter applied)
the names are not fetched here, and a name the file does not carry is reported as the script reported a failed fetch.
Parity: tools/parity/midna_kronos_forecast.py (the original script run unmodified against this runner, on the model)."""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(os.path.dirname(HERE), "vendor", "midna", "kronos")
UNIVERSE = ["ABBV", "ABNB", "ADI", "AMZN", "AON", "AXP", "CHWY", "COST", "CRWD", "DIS", "DKNG", "FCX", "MCK", "MO",
            "ORCL", "PEP", "PM", "PYPL", "SBUX", "SMCI", "TMO", "TSLA", "WFC", "ZS"]
CONTEXT = 90
PRED_LEN = 10
PATHS = 10
TEMPERATURE = 0.6
TOP_P = 0.9
MODEL = "NeoQuasar/Kronos-base"
TOKENIZER = "NeoQuasar/Kronos-Tokenizer-base"
REVISION = "2b554741eca47781b64468546e77fef3e85130e6"
HOLIDAYS = {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25"}


def session_day(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d")


def parse_bars(body, last_day=None):
    result = body["chart"]["result"][0]
    stamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, stamp in enumerate(stamps):
        op, hi, lo, cl, vol = (quote["open"][i], quote["high"][i], quote["low"][i], quote["close"][i],
                               quote["volume"][i])
        if None in (op, hi, lo, cl, vol) or cl <= 0 or vol < 0:
            continue
        day = session_day(stamp)
        if last_day is not None and day > last_day:
            continue
        rows.append({"day": day, "open": float(op), "high": float(hi), "low": float(lo), "close": float(cl),
                     "volume": float(vol)})
    return rows


def fetch_bars(sym, last_day=None):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2y"
    request = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.load(response)
    return parse_bars(body, last_day)


def future_days(last, count):
    cursor = datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)
    out = []
    while len(out) < count:
        day = cursor.strftime("%Y-%m-%d")
        if cursor.weekday() < 5 and day not in HOLIDAYS:
            out.append(day)
        cursor += timedelta(days=1)
    return out


def payload(status, signal_day, scores, error, note):
    return {"status": status, "signalDay": signal_day, "model": MODEL, "revision": REVISION, "context": CONTEXT,
            "predLen": PRED_LEN, "samples": PATHS, "temperature": TEMPERATURE, "topP": TOP_P, "scores": scores,
            "error": error, "note": note}


def write(out, doc):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        f.write(json.dumps(doc, indent=2) + "\n")
    os.replace(tmp, out)


def served_bars(served, sym, last_day=None):
    """a name's rows from the job's rows file (already filtered as parse_bars filters)."""
    rows = served.get(sym)
    if not rows:
        raise LookupError("the desk's data hub served none")
    return [r for r in rows if last_day is None or r["day"] <= last_day]


def main(out, weights, last_day, rows_path=None):
    write(out, payload("running", None, [], None, "Kronos-base is loading the frozen checkpoint."))
    served = None
    if rows_path:
        with open(rows_path) as f:
            served = json.load(f).get("rows") or {}
    os.environ.setdefault("HF_HUB_CACHE", weights)
    sys.path.insert(0, VENDOR)
    import pandas as pd
    import torch
    from model import Kronos, KronosPredictor, KronosTokenizer

    torch.set_num_threads(1)                                # one CPU thread: the desk host is small and shared

    os.makedirs(weights, exist_ok=True)
    tokenizer = KronosTokenizer.from_pretrained(TOKENIZER, cache_dir=weights)
    model = Kronos.from_pretrained(MODEL, revision=REVISION, cache_dir=weights)
    predictor = KronosPredictor(model, tokenizer, max_context=512)
    scores, errors, signal_day = [], [], None
    for sym in UNIVERSE:
        try:
            bars = fetch_bars(sym, last_day) if served is None else served_bars(served, sym, last_day)
        except Exception as caught:                         # noqa: BLE001 — one name must not drop the book
            errors.append(f"{sym} had no bars ({caught})")
            continue
        if len(bars) < CONTEXT:
            errors.append(f"{sym} has {len(bars)} sessions, needs {CONTEXT}")
            continue
        window = bars[-CONTEXT:]
        signal_day = window[-1]["day"]
        frame = pd.DataFrame(window)
        frame["amount"] = frame["volume"] * frame[["open", "high", "low", "close"]].mean(axis=1)
        x_df = frame[["open", "high", "low", "close", "volume", "amount"]]
        x_ts = pd.Series(pd.to_datetime(frame["day"]))
        y_ts = pd.Series(pd.to_datetime(future_days(signal_day, PRED_LEN)))
        forecast = predictor.predict(df=x_df, x_timestamp=x_ts, y_timestamp=y_ts, pred_len=PRED_LEN, T=TEMPERATURE,
                                     top_p=TOP_P, sample_count=PATHS, verbose=False)
        last_close = float(window[-1]["close"])
        forecast_close = float(forecast["close"].iloc[-1])
        if not (last_close > 0 and forecast_close > 0):
            errors.append(f"{sym} forecast was not a price")
            continue
        scores.append({"sym": sym, "score": forecast_close / last_close - 1, "lastClose": last_close,
                       "forecastClose": forecast_close})
        print(f"{sym} {scores[-1]['score']:+.4f}", flush=True)
    scores.sort(key=lambda row: (-row["score"], row["sym"]))
    if signal_day is None or len(scores) < 4:
        write(out, payload("error", signal_day, scores, "; ".join(errors[:4]) or "Kronos did not score four names.",
                           "No order. The shadow stays in cash until a full forecast lands."))
        return 1
    write(out, payload("ready", signal_day, scores, "; ".join(errors[:4]) or None,
                       f"Kronos-base forecast from the {signal_day} close. Ten paths, ten sessions, top 4."))
    return 0


if __name__ == "__main__":
    o, w, d = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
    try:
        raise SystemExit(main(o, w, d, sys.argv[4] if len(sys.argv) > 4 else None))
    except SystemExit:
        raise
    except Exception as caught:                             # noqa: BLE001
        write(o, payload("error", None, [], str(caught), "Kronos-base did not finish. No order was sent."))
        raise
