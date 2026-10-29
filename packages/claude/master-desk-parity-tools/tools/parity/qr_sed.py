"""qr_sed: the Spectral Echo Drift row (qr_spectral_echo_drift) vs its source on randomized top-of-book streams.

SOURCE: quant-research-critical@0be4c575 research/2026-10-10-spectral-echo-drift/engine.py (blob 95d5f34f, vendored
byte-exact as desk/vendor/quant_research/sed/engine.py -- the bytes are checked here against the blob sha):
build_features(lob, posts) + event_backtest(features, lob, model="core") on each scenario's stream written as the
source's MBP-10 frame (the touch at level 0, levels 1-9 priced a tick apart with no size; no posts).
PORT: the same stream as Alpaca quote dicts (RFC 3339 nanosecond times) through sed.Tape, read in desk passes every
30 s (random phase) through one second before each pass; sed.features; and the SED sleeve itself driven pass by pass
on views carrying the tape, its fills mirrored at the replay's prices (the IOC limit at the entry update's ask; the
exit at the replay's exit update, partial-depth valuation included) and its NAV kept by the replay's ledger.
Compared: every minute row's core feature columns exactly (NaN = NaN) -- the source's full two-session frame vs the
port's features over both sessions' records, and the sleeve's per-pass (memoised, session-scoped) features vs the
same rows; every trade exactly (symbol, signal minute, entry update, shares, entry price, stop, exit reason, exit
update, exit price, NAV after).

Streams: per scenario two consecutive sessions x 3 symbols, alternating coherent regimes (imbalance changes driven by
the returns 2-5 minutes earlier at three 3-15-minute periods) and noise; 12+ updates a minute, cent ticks, 1-3 cent
spreads, occasional timestamp ties, locked / zero-priced books, pre-open and post-close updates and empty minutes."""
import dataclasses
import hashlib
import math
import os
import time

import numpy as np

from . import write_receipt

N_SCEN = int(os.environ.get("SED_PARITY_SCENARIOS", 40))
SEED = 20261016
COLS = ("minute", "known_at", "mid_close", "imbalance", "return_1m", "return_3m", "atr_20", "fractal_dim",
        "fractal_low", "coherence", "entropy", "lag_bars", "lag_corr", "entropy_falling", "signal_core")
BLOB = "95d5f34ff2eb64087e0c12ff0a16f6e8cb52b565"


def blob_sha(path):
    b = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def gen_session(rng, day, px, sym_seed):
    """one symbol's session: a list of (t_ns, bid, bid size, ask, ask size) and the closing mid."""
    from desk.sleeves.quant_research import sed as S
    lo = S.et_ns(day, 9, 30)
    periods = rng.choice(np.arange(3.0, 15.5, 0.5), 3, replace=False)
    phases = rng.uniform(0, 2 * np.pi, 3)
    amp = rng.uniform(2e-4, 8e-4)
    lag = int(rng.integers(2, 6))
    beta = rng.uniform(300, 900)
    lam = rng.uniform(4, 30)
    out = []
    regime_left = int(rng.integers(20, 300))
    coherent = rng.random() < 0.6
    r_hist = [0.0] * 6
    x = rng.uniform(0.05, 0.3)
    mid = px
    for t0 in range(-3, 393):                                   # 09:27 .. 16:02: pre-open / post-close updates dropped
        if regime_left <= 0:
            coherent = not coherent
            regime_left = int(rng.integers(150, 300) if coherent else rng.integers(20, 120))
        regime_left -= 1
        k = t0
        sig = amp * sum(np.sin(2 * np.pi * k / p + ph) for p, ph in zip(periods, phases))
        r = sig + rng.normal(0, amp / 3) if coherent else rng.normal(0, amp)
        r_hist.append(r)
        if coherent:
            x = 0.92 * x + 0.08 * 0.25 + beta * r_hist[-1 - lag] + rng.normal(0, 0.02)
        else:
            x = 0.7 * x + 0.3 * rng.normal(0.05, 0.3)
        x = float(np.clip(x, -0.9, 0.9))
        target = mid * math.exp(r)
        if rng.random() < 0.001:                                # an empty minute
            mid = target
            continue
        n = 12 + int(rng.poisson(lam)) if rng.random() > 0.002 else int(rng.integers(1, 11))
        base = lo + k * S.MIN_NS
        ts = np.sort(rng.integers(0, S.MIN_NS, n))
        if n > 3 and rng.random() < 0.05:
            ts[2] = ts[1]                                       # a timestamp tie (the stream's order holds)
        for i, dt in enumerate(ts):
            f = (i + 1) / n
            m_i = mid + (target - mid) * f + rng.normal(0, abs(target - mid) * 0.3 + 0.004)
            s = 0.01 * int(rng.integers(1, 4))
            bid = round(m_i - s / 2, 2)
            ask = round(bid + s, 2)
            if rng.random() < 0.002:
                ask = bid                                       # a locked book (dropped)
            if rng.random() < 0.001:
                bid = 0.0                                       # a broken one (dropped)
            d = rng.uniform(100, 1500)
            xi = float(np.clip(x + rng.normal(0, 0.05), -0.95, 0.95))
            bs = max(1, int(round(d * (1 + xi) / 2)))
            az = max(1, int(round(d * (1 - xi) / 2)))
            out.append((int(base + dt), float(bid), float(bs), float(ask), float(az)))
        mid = target
    return out, mid


def scenario(rng, k):
    from desk import calendar as cal
    from desk.sleeves.quant_research import sed as S
    d0 = cal._as_date("2027-01-04")
    day1 = cal.next_trading_day(d0, int(rng.integers(0, 240)))
    days = [day1.isoformat(), cal.next_trading_day(day1).isoformat()]
    syms = [chr(65 + (k + j) % 26) * 2 + chr(65 + j) for j in range(3)]
    stream = {}
    for j, sym in enumerate(syms):
        px = float(rng.uniform(20, 300))
        rows = []
        for day in days:
            got, px = gen_session(rng, day, px * math.exp(rng.normal(0, 0.01)), k * 7 + j)
            rows += got
        stream[sym] = rows
    return days, syms, stream


def source_frame(stream):
    import pandas as pd
    recs = {"ts_event": [], "symbol": [], "sequence": []}
    cols = {f"{side}_{f}_{l:02d}": [] for side in ("bid", "ask") for f in ("px", "sz") for l in range(10)}
    for sym, rows in stream.items():
        for seq, (t, bp, bs, ap, az) in enumerate(rows):
            recs["ts_event"].append(t)
            recs["symbol"].append(sym)
            recs["sequence"].append(seq)
            for l in range(10):
                cols[f"bid_px_{l:02d}"].append(round(bp - 0.01 * l, 2) if bp > 0 else 0.0)
                cols[f"ask_px_{l:02d}"].append(round(ap + 0.01 * l, 2))
                cols[f"bid_sz_{l:02d}"].append(bs if l == 0 else 0.0)
                cols[f"ask_sz_{l:02d}"].append(az if l == 0 else 0.0)
    df = pd.DataFrame(dict(recs, **cols))
    df["ts_event"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


def padded_row(bp, bs, ap, az):
    import pandas as pd
    row = {}
    for l in range(10):
        row[f"bid_px_{l:02d}"] = round(bp - 0.01 * l, 2)
        row[f"ask_px_{l:02d}"] = round(ap + 0.01 * l, 2)
        row[f"bid_sz_{l:02d}"] = bs if l == 0 else 0.0
        row[f"ask_sz_{l:02d}"] = az if l == 0 else 0.0
    return pd.Series(row)


def same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        a, b = float(a), float(b)
        return (math.isnan(a) and math.isnan(b)) or a == b
    return a == b


def run_source(E, stream):
    import pandas as pd
    lob = source_frame(stream)
    posts = pd.DataFrame({"observed_at": pd.Series([], dtype="datetime64[ns, UTC]"), "symbol": [], "post_id": [],
                          "author_id": [], "is_repost": []})
    cfg = E.Config()
    feats = E.build_features(lob, posts, cfg)
    trades, _ = E.event_backtest(feats, lob, cfg, model="core")
    rows = {}
    for r in feats.itertuples(index=False):
        rows[(r.symbol, int(r.minute.value))] = {
            "minute": int(r.minute.value), "known_at": int(r.known_at.value), "mid_close": float(r.mid_close),
            "imbalance": float(r.imbalance), "return_1m": float(r.return_1m), "return_3m": float(r.return_3m),
            "atr_20": float(r.atr_20), "fractal_dim": float(r.fractal_dim), "fractal_low": float(r.fractal_low),
            "coherence": float(r.coherence), "entropy": float(r.entropy), "lag_bars": float(r.lag_bars),
            "lag_corr": float(r.lag_corr), "entropy_falling": bool(r.entropy_falling),
            "signal_core": bool(r.signal_core)}
    tr = []
    for t in trades.to_dict("records"):
        tr.append({"symbol": t["symbol"], "signal": int(pd.Timestamp(t["signal_time"]).value),
                   "entry": int(pd.Timestamp(t["entry_time"]).value), "shares": int(t["shares"]),
                   "entry_vwap": float(t["entry_vwap"]), "stop": float(t["initial_stop"]),
                   "exit_reason": t["exit_reason"], "exit": int(pd.Timestamp(t["exit_time"]).value),
                   "exit_vwap": float(t["exit_vwap"]), "nav_after": float(t["nav_after"])})
    return rows, tr


def run_port(S, E, days, syms, stream, rng):
    from desk import calendar as cal
    from desk.contract import View
    cfg = E.Config()
    arrays = {s: (np.array([r[0] for r in rows], dtype=np.int64), np.array([r[1:] for r in rows]))
              for s, rows in stream.items()}

    def read(symbols, a, b):
        out = {}
        for s in symbols:
            t, v = arrays[s]
            i, j = np.searchsorted(t, a, "left"), np.searchsorted(t, b, "left")
            out[s] = [{"t": S.iso_ns(int(t[k])), "bp": v[k, 0], "bs": v[k, 1], "ap": v[k, 2], "as": v[k, 3]}
                      for k in range(i, j)]
        return out

    sleeve = S.SED()
    sleeve.CONFIG = dataclasses.replace(sleeve.CONFIG, universe=tuple(syms))
    state, nav, held, trades, tapes, incremental = {}, float(cfg.starting_nav), {}, [], {}, {}
    open_tr = None
    for day in days:
        tape = S.Tape(day)
        prev = tapes[days[0]].minutes if day != days[0] else {}
        p = S.et_ns(day, 9, 30) + int(rng.integers(0, 30 * S.NS))
        while p < S.et_ns(day, 16, 0):
            tape.advance(read, syms, p, budget_s=1e9)
            now = p / S.NS
            pos = {}
            if open_tr:
                pos["EQ:" + open_tr["symbol"]] = {"qty": float(open_tr["shares"]), "avg": open_tr["entry_vwap"]}
            cash = nav - (open_tr["shares"] * open_tr["entry_vwap"] if open_tr else 0.0)
            view = View(now=now, session=day, quotes={}, positions=pos, equity=nav, cash=cash, state=state,
                        extra={"qr_sed_tape": {"tape": tape, "prev": prev}, "pending_orders": []})
            intents = sleeve.signal(view)
            state = sleeve.update_state(view, intents)
            for it in intents:
                if it.kind == "exit":
                    c = next(c for c in state["closing"] if c["sym"] == it.symbol)
                    tt, vv = arrays[it.symbol]
                    lo_i, hi_i = np.searchsorted(tt, S.et_ns(day, 9, 30)), np.searchsorted(tt, S.et_ns(day, 16, 0))
                    ok = np.array([S.valid_row({"t": int(tt[k]), "bp": vv[k, 0], "bs": vv[k, 1], "ap": vv[k, 2],
                                                "as": vv[k, 3]}, tape.lo, tape.hi) is not None
                                   for k in range(lo_i, hi_i)], dtype=bool)
                    st_t, st_v = tt[lo_i:hi_i][ok], vv[lo_i:hi_i][ok]
                    j = S.exit_update(st_t, c, c["trigger"])
                    j = len(st_t) - 1 if j is None else j
                    bp, bs, ap, az = (float(x) for x in st_v[j])
                    row = padded_row(bp, bs, ap, az)
                    vwap, filled = E.walk_book(row, "sell", open_tr["shares"])
                    if filled != open_tr["shares"] or not np.isfinite(vwap):
                        vwap, filled = E._partial_liquidation_value(row, open_tr["shares"])
                        c["why"] = "unfilled_exit_depth"
                    entry_notional = open_tr["entry_vwap"] * open_tr["shares"]
                    exit_notional = vwap * filled
                    fees = cfg.fee_per_share_per_side * (open_tr["shares"] + filled)
                    fees += (cfg.fee_bps_per_side / 10_000.0) * (entry_notional + exit_notional)
                    nav += exit_notional - entry_notional - fees
                    trades.append(dict(open_tr, exit_reason=c["why"], exit=int(st_t[j]), exit_vwap=float(vwap),
                                       nav_after=nav))
                    open_tr = None
                elif it.kind == "enter":
                    ps = state["pos"]
                    q = int(it.qty)
                    open_tr = {"symbol": it.symbol, "signal": ps["signal_t"], "entry": ps["entry_t"], "shares": q,
                               "entry_vwap": (q * ps["ask"]) / q, "stop": ps["stop"]}
            p += 30 * S.NS
        tape.advance(read, syms, tape.hi + S.LAG_NS, budget_s=1e9)     # the next session's catch-up (feed_tape)
        tapes[day] = tape
        prev_recs = tapes[days[0]].minutes if day != days[0] else {}
        for sym in syms:
            recs = list(prev_recs.get(sym) or []) + tape.records(sym)
            got = S.features(recs, sleeve._cache.get((day, sym)), since=tape.lo)
            for r in got:
                incremental[(sym, r["minute"])] = r
    full = {}
    for sym in syms:
        recs = []
        for day in days:
            recs += tapes[day].records(sym)
        for r in S.features(recs):
            full[(sym, r["minute"])] = r
    return full, incremental, trades


def run():
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from desk.sleeves.quant_research import sed as S
    E = S.E()
    vend = os.path.join(os.path.dirname(E.__file__), "engine.py")
    out = {"family": "quant_research", "sleeves": [S.SID], "byte_exact_vendoring": {"engine.py": blob_sha(vend) == BLOB},
           "source": {"repo": "quant-research-critical", "commit": "0be4c57569e363d052bd23564cf0664697439927",
                      "path": "research/2026-10-10-spectral-echo-drift/engine.py", "blob_sha": BLOB}}
    rng = np.random.default_rng(SEED)
    f_st = {"cases": 0, "identical": 0}
    i_st = {"cases": 0, "identical": 0}
    t_st = {"cases": 0, "identical": 0, "source_trades": 0, "port_trades": 0, "exit_reasons": {}}
    sig_rows = 0
    diffs = []
    t0 = time.time()
    for k in range(N_SCEN):
        days, syms, stream = scenario(rng, k)
        src_rows, src_tr = run_source(E, stream)
        full, inc, port_tr = run_port(S, E, days, syms, stream, np.random.default_rng(SEED + k))
        keys = set(src_rows) | set(full)
        for key in sorted(keys):
            f_st["cases"] += 1
            a, b = src_rows.get(key), full.get(key)
            bad = [c for c in COLS if a is None or b is None or not same(a[c], b[c])]
            if not bad:
                f_st["identical"] += 1
                sig_rows += bool(a["signal_core"])
            elif len(diffs) < 50:
                diffs.append({"part": "features", "scenario": k, "key": [key[0], key[1]], "cols": bad[:6],
                              "source": None if a is None else {c: a[c] for c in bad[:3]},
                              "port": None if b is None else {c: b[c] for c in bad[:3]}})
        for key, b in inc.items():
            i_st["cases"] += 1
            a = full.get(key)
            if a is not None and all(same(a[c], b[c]) for c in COLS):
                i_st["identical"] += 1
            elif len(diffs) < 50:
                diffs.append({"part": "incremental_features", "scenario": k, "key": [key[0], key[1]]})
        t_st["source_trades"] += len(src_tr)
        t_st["port_trades"] += len(port_tr)
        for j in range(max(len(src_tr), len(port_tr))):
            t_st["cases"] += 1
            a = src_tr[j] if j < len(src_tr) else None
            b = port_tr[j] if j < len(port_tr) else None
            if a is not None:
                t_st["exit_reasons"][a["exit_reason"]] = t_st["exit_reasons"].get(a["exit_reason"], 0) + 1
            if a is not None and b is not None and all(same(a[c], b[c]) for c in a):
                t_st["identical"] += 1
            elif len(diffs) < 50:
                diffs.append({"part": "trades", "scenario": k, "index": j, "source": a, "port": b})
        print(f"scenario {k}: rows {len(src_rows)} trades {len(src_tr)}/{len(port_tr)} "
              f"elapsed {time.time() - t0:.0f}s", flush=True)
    out.update(features=f_st, incremental_features=i_st, trades=t_st, signal_rows=sig_rows, scenarios=N_SCEN,
               cases=f_st["cases"] + i_st["cases"] + t_st["cases"],
               identical=f_st["identical"] + i_st["identical"] + t_st["identical"], n_diffs=len(diffs),
               diffs=diffs, method="randomized two-session, three-symbol top-of-book streams: the source's feature "
               "builder and core replay on the padded MBP-10 frame vs the port's tape, features and the SED sleeve "
               "driven pass by pass (fills mirrored at the replay's prices, NAV on the replay's ledger)",
               not_in_this_comparison=["the book itself: IEX top of book vs MBP-10 (divergence 1)", "universe (3)",
                                       "desk execution prices and timing (4, 5)", "desk NAV / fee model (6)",
                                       "history before the previous session (7)"])
    write_receipt("qr_sed", out)
    return out


if __name__ == "__main__":
    import json
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}),
          json.dumps({k: r[k] for k in ("features", "incremental_features", "trades", "signal_rows",
                                        "byte_exact_vendoring")}))
