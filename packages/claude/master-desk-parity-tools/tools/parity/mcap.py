"""mcap: the old desk/mcap_edgar.log_mcap (vendored byte-identical, its SEC / Alpaca reads stubbed) vs
desk/feedlib/mcap.log_mcap on the same ticker map, EntityPublicFloat frames and split-adjusted closes.

Random cases: unknown tickers, dotted / dashed share classes, frame lists with ends inside / outside the
[bar - 730d, bar - 290d] window, $1M floats, price histories with gaps around the float's end, malformed bar
dates. Compared: the log market cap (None = fail closed) for every case."""
import importlib.util
import os
import random
from datetime import date, timedelta

from desk.feedlib import mcap

from . import trading_dates, write_receipt

N_CASES = 2000


def _old():
    spec = importlib.util.spec_from_file_location(
        "old_mcap_edgar", os.path.join(os.path.dirname(mcap.__file__), "..", "vendor", "old_desk_research", "mcap_edgar.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run():
    rnd = random.Random(31)
    O = _old()
    days = trading_dates("2023-01-02", 1000)
    n = same = 0
    diffs = []
    counts = {"valued": 0, "fail_closed": 0}
    for k in range(N_CASES):
        sym = rnd.choice(("AAA", "BRK.B", "BF-B", "ZZZ", "CCC"))
        cmap = {"AAA": "0000000001", "BRK-B": "0000000002", "BF.B": "0000000003", "CCC": "0000000004"}
        frames = sorted({((date(2023, 1, 1) + timedelta(days=rnd.randint(0, 1200))).isoformat(),
                          float(rnd.choice((5e5, 2e6, 3e8, 4e9, 1.2e10)))) for _ in range(rnd.randint(0, 6))})
        frames = [(e, v) for e, v in frames if v > 1e6]
        px = rnd.uniform(2, 200)
        closes = []
        for d in days:
            if rnd.random() < 0.02:
                continue
            px = max(0.5, px * (1 + rnd.gauss(0, 0.02)))
            closes.append((d, round(px, 4)))
        bar = rnd.choice(days[400:]) if rnd.random() > 0.01 else "2026-13-45"
        O._load_cik_map = lambda cmap=cmap: cmap
        O.float_frames = lambda cik, force=False, frames=frames: list(frames)
        O._split_bars = lambda s, start, limit=1500, closes=closes: [(d, c) for d, c in closes if d >= start]
        a, _ = O.log_mcap(sym, bar)
        b, _ = mcap.log_mcap(sym, bar, cmap, lambda c, frames=frames: list(frames), closes)
        n += 1
        same += a == b
        if a != b:
            diffs.append({"ref": k, "sym": sym, "bar": bar, "old": a, "new": b})
        counts["valued" if a is not None else "fail_closed"] += 1
    res = {"sleeve": "mcap", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("mcap", res)
    return res
