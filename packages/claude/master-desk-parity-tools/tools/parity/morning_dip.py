"""morning_dip: old morning_dip.py vs the restored femto port.

The OLD module builds its candles itself (fetch_3min over a stubbed 1Min feed + closed_candles) and decides
with its own indicators / _arm_plan, in main()'s order: window -> 16 closed candles -> signal candle inside
10:00-12:00 ET -> ATR > 0 -> ER <= 0.35 -> plan (qty, limit, target, stop) or a skip. The port answers the
same pass through signal() on the same 1-minute bars. Synthetic tape: 09:00-12:10 ET minute bars with a
sparse pre-market and occasional missing minutes (unhealthy candles), random dips and chop.
Desk gates (cap clamp #87, risk gate, context gate, Decision #75) are out of scope."""
import os
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, trading_dates, write_receipt

F = femto_module("morning_dip")
ET = ZoneInfo("America/New_York")
N_CASES = 1500

OLD = r'''
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import alpaca_lib as lib
import morning_dip as O
ET = ZoneInfo("America/New_York")
O.log = lambda e: None
MIN, NOW = [], [None]
lib.api_request = lambda method, url, params=None, **k: {"bars": [b for b in MIN if b["ts"] < NOW[0].timestamp()]}
lib.data_base = lambda: "x"
class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW[0] if tz is None else NOW[0].astimezone(tz)
O.datetime = FakeDT
out = []
for c in PAYLOAD["cases"]:
    MIN[:] = c["min"]
    NOW[0] = FakeDT.fromtimestamp(c["now"], tz=timezone.utc)
    now_utc = NOW[0]
    now_et = now_utc.astimezone(ET)
    res = {"candles": None, "plan": None, "why": None}
    if not O.in_window(now_et):
        res["why"] = "window"; out.append(res); continue
    candles = O.closed_candles(O.fetch_3min(), now_utc)
    res["candles"] = [[datetime.fromisoformat(x["t"]).timestamp(), x["o"], x["h"], x["l"], x["c"], x["healthy"]]
                      for x in candles[-20:]]
    if len(candles) < O.ER_CANDLES + 1:
        res["why"] = "few"; out.append(res); continue
    sig = candles[-1]
    sig_et = O.desk.parse_bar_t(sig["t"]).astimezone(ET)
    if not (O.WINDOW_START <= (sig_et.hour, sig_et.minute) < O.WINDOW_END):
        res["why"] = "sig_outside"; out.append(res); continue
    atr, er = O.indicators(candles)
    if atr is None or atr <= 0:
        res["why"] = "atr"; out.append(res); continue
    if er is None or er > O.ER_MAX:
        res["why"] = "er"; out.append(res); continue
    plan, skip = O._arm_plan(sig, sig_et, sig["t"], atr, er, c["equity"])
    if plan is None:
        res["why"] = skip["event"]; out.append(res); continue
    res["plan"] = [plan["qty"], plan["limit"], plan["target"], plan["stop"]]
    out.append(res)
print(json.dumps(out))
'''


def _tape(rnd, day):
    t0 = datetime.fromisoformat(day).replace(hour=9, minute=0, tzinfo=ET)
    px = rnd.uniform(350, 520)
    vol = rnd.uniform(0.0003, 0.0012)
    out = []
    for k in range(190):
        t = t0 + timedelta(minutes=k)
        pre = t.hour == 9 and t.minute < 30
        if rnd.random() < (0.35 if pre else 0.03):
            continue
        shock = -rnd.uniform(0.002, 0.006) if rnd.random() < 0.02 else 0.0
        o = px
        c = px * (1 + rnd.gauss(0, vol) + shock)
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        ts = t.timestamp()
        out.append({"t": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "ts": ts,
                    "o": round(o, 2), "h": round(h, 2), "l": round(lo, 2), "c": round(c, 2), "v": 1000})
        px = c
    return out


def run():
    rnd = random.Random(73)
    days = trading_dates("2025-06-02", 200)
    cases = []
    for k in range(N_CASES):
        day = rnd.choice(days)
        mins = _tape(random.Random(rnd.randint(0, 10**9)), day)
        hh, mm = rnd.choice(((9, 58), (10, 0), (10, 2), (10, 17), (10, 41), (11, 5), (11, 33), (11, 58), (12, 1)))
        now = datetime.fromisoformat(day).replace(hour=hh, minute=mm, second=rnd.randint(0, 59), tzinfo=ET)
        cases.append({"min": mins, "now": now.timestamp(), "equity": rnd.choice((50_000.0, 100_000.0, 400_000.0)),
                      "day": day})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"armed": 0, "window": 0, "few": 0, "sig_outside": 0, "atr": 0, "er": 0, "skip_shape": 0,
              "skip_size": 0, "candle_sets": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        bars = [{"t": b["ts"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                for b in c["min"] if b["ts"] < c["now"]]
        if o["candles"] is not None:
            got = F.candles_3min(bars, c["now"])[-20:]
            cmp("candles", ci, o["candles"], [[x["t"], x["o"], x["h"], x["l"], x["c"], x["healthy"]] for x in got])
            counts["candle_sets"] += 1
        ctx = fc.Context(now=c["now"], session=c["day"], equity=c["equity"],
                         extra={"sleeve_state": {"QQQ": {"position": None}}})
        out = F.signal({"QQQ": bars}, {}, ctx)
        new = None
        if out:
            it = out[0]
            new = [it.qty_hint, it.order["limit_price"], it.target, it.stop]
        cmp("plan", [ci, c["day"], c["now"]], o["plan"], new)
        counts["armed" if o["plan"] else (o["why"] or "x")] = counts.get("armed" if o["plan"] else (o["why"] or "x"), 0) + 1
    res = {"sleeve": "morning_dip", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("morning_dip" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
