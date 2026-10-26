#!/usr/bin/env python3
"""Daily facts for the three board sleeves. The pass trades them. This script does not.

The last bar is dropped when it is dated today in New York, so a session that
is still printing is not a signal. Output is data/equity-desk/board-signals.json.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

BASKET = "quant-research/galath-research/shadow/swing_basket_v1.json"
OUT = "data/equity-desk/board-signals.json"
ET = ZoneInfo("America/New_York")


def fetch(sym: str) -> dict | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1y"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-desk/1.5"})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            body = json.loads(response.read().decode())
    except Exception:
        return None
    result = (body.get("chart") or {}).get("result") or [None]
    result = result[0]
    if not result:
        return None
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    stamps = result.get("timestamp") or []
    rows = []
    for i, stamp in enumerate(stamps):
        o = (quote.get("open") or [None])[i] if i < len(quote.get("open") or []) else None
        h = (quote.get("high") or [None])[i] if i < len(quote.get("high") or []) else None
        l = (quote.get("low") or [None])[i] if i < len(quote.get("low") or []) else None
        c = (quote.get("close") or [None])[i] if i < len(quote.get("close") or []) else None
        v = (quote.get("volume") or [None])[i] if i < len(quote.get("volume") or []) else None
        if not (h and l and c and h > 0 and l > 0 and c > 0):
            continue
        day = datetime.fromtimestamp(stamp, ET).date().isoformat()
        rows.append((day, float(h), float(l), float(c), float(v or 0)))
    return {"rows": rows}


def ema(values: list[float], n: int) -> list[float]:
    a = 2 / (n + 1)
    out = []
    prev = None
    for value in values:
        prev = value if prev is None else a * value + (1 - a) * prev
        out.append(prev)
    return out


def atr(rows: list[tuple], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(rows)
    prev_close = None
    acc = 0.0
    seeded = None
    for i, (_d, h, l, c, _v) in enumerate(rows):
        tr = h - l if prev_close is None else max(h - l, abs(h - prev_close), abs(l - prev_close))
        prev_close = c
        if seeded is None:
            acc += tr
            if i + 1 == n:
                seeded = acc / n
                out[i] = seeded
        else:
            seeded = (seeded * (n - 1) + tr) / n
            out[i] = seeded
    return out


def cci_at(rows: list[tuple], i: int, n: int = 20) -> float | None:
    if i + 1 < n:
        return None
    window = rows[i + 1 - n : i + 1]
    typical = [(h + l + c) / 3 for _d, h, l, c, _v in window]
    mean = sum(typical) / n
    mad = sum(abs(value - mean) for value in typical) / n
    if mad <= 0:
        return None
    return (typical[-1] - mean) / (0.015 * mad)


def vwap_at(rows: list[tuple], i: int, n: int = 20) -> float | None:
    if i + 1 < n:
        return None
    window = rows[i + 1 - n : i + 1]
    num = 0.0
    den = 0.0
    for _d, h, l, c, v in window:
        typical = (h + l + c) / 3
        num += typical * v
        den += v
    if den <= 0:
        return None
    return num / den


def prior_high(rows: list[tuple], i: int, n: int) -> float | None:
    if i < n:
        return None
    return max(row[1] for row in rows[i - n : i])


def prior_low(rows: list[tuple], i: int, n: int) -> float | None:
    if i < n:
        return None
    return min(row[2] for row in rows[i - n : i])


def bar_for(rows: list[tuple]) -> dict | None:
    today = datetime.now(ET).date().isoformat()
    done = [row for row in rows if row[0] < today]
    if len(done) < 60:
        return None
    i = len(done) - 1
    closes = [row[3] for row in done]
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd = [a - b for a, b in zip(ema12, ema26)]
    signal = ema(macd, 9)
    ema4 = ema(closes, 4)
    a20 = atr(done, 20)[i]
    a14 = atr(done, 14)[i]
    high20 = prior_high(done, i, 20)
    high20_y = prior_high(done, i - 1, 20) if i else None
    high55 = prior_high(done, i, 55)
    high55_y = prior_high(done, i - 1, 55) if i else None
    low10 = prior_low(done, i, 10)
    cci = cci_at(done, i)
    vw = vwap_at(done, i)
    vw_prev = vwap_at(done, i - 1) if i else None
    vw_5 = vwap_at(done, i - 5) if i >= 5 else None
    close = closes[i]
    prev = closes[i - 1]
    if a20 is None or a14 is None or high20 is None or low10 is None or cci is None or vw is None or vw_prev is None:
        return None
    above20 = close > high20
    above20_y = high20_y is not None and prev > high20_y
    above55 = high55 is not None and close > high55
    above55_y = high55_y is not None and prev > high55_y
    cross_up = macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]
    cross_dn = macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]
    vw_up = ema4[i] > vw and ema4[i - 1] <= vw_prev
    vw_dn = ema4[i] < vw and (vw_prev is None or ema4[i - 1] >= vw_prev)
    return done[i][0], {
        "close": close,
        "atr20": a20,
        "atr14": a14,
        "enter20": bool(above20 and not above20_y),
        "enter55": bool(above55 and not above55_y),
        "exit10": bool(close < low10),
        "macdUp": bool(cross_up),
        "macdDown": bool(cross_dn),
        "cci": cci,
        "vwapUp": bool(vw_up),
        "vwapDown": bool(vw_dn),
        "vwapRising": bool(vw_5 is not None and vw > vw_5),
    }


def main() -> None:
    basket = json.load(open(BASKET))
    symbols = [row["sym"] if isinstance(row, dict) else row for row in basket["symbols"]]
    found = []
    for sym in symbols:
        fetched = fetch(sym)
        if not fetched:
            continue
        fact = bar_for(fetched["rows"])
        if not fact:
            continue
        found.append((sym, fact[0], fact[1]))
    days = [day for _sym, day, _fact in found]
    as_of = max(set(days), key=days.count) if days else None
    bars = [{"sym": sym, **fact} for sym, day, fact in found if day == as_of]
    payload = {"asOf": as_of, "builtAt": datetime.now(ET).isoformat(), "bars": bars}
    tmp = OUT + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(payload, handle)
    import os

    os.replace(tmp, OUT)
    print(f"board signals {as_of} bars {len(bars)}", flush=True)


if __name__ == "__main__":
    main()
