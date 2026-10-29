"""legends_ema: old legends_ema.py vs the restored femto port.

The OLD module's own functions run in its own process with the bar fetches stubbed to a synthetic QQQ tape
(SIP 5-minute bars; the old bucketing builds its 15m grid from them) and the clock pinned:
  setup     _evaluate_setup_inner(prior session)  ->  trend, trend_day, no_touch, ema_last, atr14
  entry     the old main() entry decision at the open: side toward the EMA (open > ema_last -> sell),
            qty = equity x 0.25% // (0.5 x ATR14), TP/SL = exit_geometry(side, fill, ema_last, atr14)
  refresh   current_ema_target() at several times of the next session, and the >= $0.20 refresh decision
The port gets the same tape as 15m bars (o first, h max, l min, c last per :00/:15/:30/:45 bucket) and
daily bars, and answers through setup_for / signal / exit_levels / current_ema_target.
Desk gates (risk, context, Decision #75 long gate and short chart staging, 150% cap) are out of scope."""
import os
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, trading_dates, write_receipt

F = femto_module("legends_ema")
ET = ZoneInfo("America/New_York")
N_CASES = 300

OLD = r'''
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import legends_ema as O
ET = ZoneInfo("America/New_York")
O.log = lambda e: None
FIVE, DAILY, NOW = [], [], [None]
def _fetch(start_utc, end_utc):
    s, e = start_utc.timestamp(), end_utc.timestamp()
    return [b for b in FIVE if s <= b["ts"] < e]
O.fetch_1min = _fetch
O.desk.run_cli = lambda script, args, timeout=None: list(DAILY)
class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW[0] if tz is None else NOW[0].astimezone(tz)
out = []
for c in PAYLOAD["cases"]:
    FIVE[:] = c["five"]
    DAILY[:] = c["daily"]
    O.datetime = FakeDT
    sess = FakeDT.fromisoformat(c["setup_day"]).replace(hour=12, tzinfo=ET)
    NOW[0] = FakeDT.fromisoformat(c["today"]).replace(hour=9, minute=31, tzinfo=ET)
    setup = O._evaluate_setup_inner(sess)
    res = {"setup": None if not setup else {k: setup[k] for k in ("trend", "trend_day", "no_touch", "ema_last", "atr14")}}
    if setup and setup["atr14"] and setup["trend_day"] and setup["no_touch"]:
        ref = c["open"]
        side = "sell" if ref > setup["ema_last"] else "buy"
        qty = int((c["equity"] * O.RISK_FRACTION) // (O.STOP_ATR_MULT * setup["atr14"]))
        tp, sl = O.exit_geometry(side, c["fill"], setup["ema_last"], setup["atr14"])
        res["entry"] = None if qty < 1 else {"side": side, "qty": qty, "tp": tp, "sl": sl}
    tg = []
    for hh, mm, tp0 in c["checks"]:
        NOW[0] = FakeDT.fromisoformat(c["today"]).replace(hour=hh, minute=mm, tzinfo=ET)
        t = O.current_ema_target()
        tg.append([t, None if t is None else bool(abs(t - tp0) >= O.REFRESH_DEADBAND)])
    O.datetime = datetime
    res["targets"] = tg
    out.append(res)
print(json.dumps(out))
'''


def _sessions(rnd, dates):
    """5-minute RTH bars per session: random drift with occasional strong one-way trend days."""
    px = rnd.uniform(300, 520)
    five, daily = [], []
    for d in dates:
        trend = rnd.random() < 0.35
        drift = (rnd.choice((-1, 1)) * rnd.uniform(0.0006, 0.0016)) if trend else rnd.uniform(-0.0003, 0.0003)
        vol = rnd.uniform(0.0006, 0.0015) * (0.5 if trend else 1.0)
        gap = rnd.gauss(0, 0.006) + (rnd.choice((-1, 1)) * rnd.uniform(0.004, 0.012) if rnd.random() < 0.3 else 0)
        px *= 1 + gap
        o0 = px
        hi, lo = -1e18, 1e18
        for k in range(78):
            t = datetime.fromisoformat(d).replace(hour=9, minute=30, tzinfo=ET) + timedelta(minutes=5 * k)
            o = px
            c = px * (1 + rnd.gauss(drift, vol))
            h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
            l = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
            ts = t.timestamp()
            five.append({"t": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "ts": ts,
                         "o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4),
                         "v": float(int(rnd.uniform(1e5, 1e6)))})
            hi, lo = max(hi, h), min(lo, l)
            px = c
        daily.append({"d": d, "o": round(o0, 4), "h": round(hi, 4), "l": round(lo, 4), "c": round(px, 4)})
    return five, daily


def _to15(five):
    out = {}
    for b in five:
        k = int(b["ts"] // 900) * 900
        e = out.setdefault(k, {"t": float(k), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": 0.0})
        e["h"], e["l"], e["c"] = max(e["h"], b["h"]), min(e["l"], b["l"]), b["c"]
        e["v"] += b["v"]
    return [out[k] for k in sorted(out)]


def run():
    rnd = random.Random(57)
    cases = []
    for k in range(N_CASES):
        dates = trading_dates("2025-%02d-%02d" % (rnd.randint(1, 10), rnd.randint(1, 26)), 22)
        five, daily = _sessions(rnd, dates)
        today = dates[-1]
        setup_day = dates[-2]
        # the old code sees only bars it fetched; keep today's tape out of the setup windows by time
        open_px = five[-78]["o"]
        fill = round(open_px * (1 + rnd.gauss(0, 0.0005)), 4)
        b15 = _to15(five)
        checks = []
        for hh, mm in ((10, 16), (11, 1), (13, 31), (15, 46)):
            now = datetime.fromisoformat(today).replace(hour=hh, minute=mm, tzinfo=ET).timestamp()
            t = F.current_ema_target([b for b in b15 if b["t"] + 900 <= now], now)
            near = t is not None and rnd.random() < 0.5          # half the checks sit around the deadband
            checks.append((hh, mm, round(t + rnd.uniform(-0.4, 0.4), 2) if near else
                           round(rnd.uniform(open_px * 0.99, open_px * 1.01), 2)))
        dbars = [{"t": r["d"] + "T04:00:00Z", "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": 1e6}
                 for r in daily]
        cases.append({"five": five, "daily": dbars, "setup_day": setup_day, "today": today, "open": open_px,
                      "fill": fill, "equity": rnd.choice((50_000.0, 100_000.0, 250_000.0)), "checks": checks,
                      "daily_rows": daily})
    old = old_run(OLD, {"cases": [{k: v for k, v in c.items() if k != "daily_rows"} for c in cases]}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"armed": 0, "entries": 0, "shorts": 0, "targets": 0, "refresh": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    def r6(x):
        return None if x is None else round(float(x), 6)

    for ci, (c, o) in enumerate(zip(cases, old)):
        bars15 = _to15(c["five"])
        daily = [{"t": datetime.fromisoformat(r["d"]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
                  "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": 1e6} for r in c["daily_rows"]]
        today = c["today"]
        now_open = datetime.fromisoformat(today).replace(hour=9, minute=31, tzinfo=ET).timestamp()
        visible = [b for b in bars15 if b["t"] + 900 <= now_open]
        setup, sday = F.setup_for(visible, daily[:-1], datetime.fromisoformat(today).date())
        a = o["setup"]
        b = None if not setup else {k: setup[k] for k in ("trend", "trend_day", "no_touch", "ema_last", "atr14")}
        cmp("setup", [ci, sday], None if a is None else {k: (r6(v) if isinstance(v, float) else v) for k, v in a.items()},
            None if b is None else {k: (r6(v) if isinstance(v, float) else v) for k, v in b.items()})
        if setup and setup["trend_day"] and setup["no_touch"]:
            counts["armed"] += 1
        # entry through the sleeve's own signal() at 09:31
        ctx = fc.Context(now=now_open, session=today, equity=c["equity"],
                         extra={"sleeve_state": {"QQQ": {"position": None}}, "bars_15m": visible,
                                "forming": {"QQQ": {"o": c["open"], "c": c["open"], "v": 1.0, "h": c["open"],
                                                    "l": c["open"]}}})
        out = F.signal({"QQQ": daily[:-1]}, {}, ctx)
        new_entry = None
        if out:
            it = out[0]
            sd = [r.value for r in it.exit_rules if r.kind == "stop_dist"][0]
            side = "buy" if it.side == "long" else "sell"
            new_entry = {"side": side, "qty": it.qty_hint, "tp": it.target,
                         "sl": round(c["fill"] - sd if side == "buy" else c["fill"] + sd, 2)}
            counts["entries"] += 1
            counts["shorts"] += side == "sell"
        cmp("entry", ci, o.get("entry"), new_entry)
        # TP refresh: the old current_ema_target and the deadband decision vs exit_levels
        for (hh, mm, tp0), (t_old, ref_old) in zip(c["checks"], o["targets"]):
            now = datetime.fromisoformat(today).replace(hour=hh, minute=mm, tzinfo=ET).timestamp()
            vis = [b for b in bars15 if b["t"] + 900 <= now]
            t_new = F.current_ema_target(vis, now)
            cmp("target", [ci, hh, mm], r6(t_old), r6(t_new))
            ctx = fc.Context(now=now, session=today, equity=c["equity"],
                             extra={"sleeve_state": {"QQQ": {"position": {"qty": 10, "target_px": tp0}}},
                                    "bars_15m": vis})
            lv = F.exit_levels({}, {}, ctx)
            ref_new = None if t_new is None else bool(lv)
            cmp("refresh", [ci, hh, mm], ref_old, ref_new)
            counts["targets"] += t_old is not None
            counts["refresh"] += bool(ref_old)
    res = {"sleeve": "legends_ema", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("legends_ema" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
