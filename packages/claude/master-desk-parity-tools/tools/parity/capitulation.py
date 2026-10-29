"""capitulation: old capitulation_sleeve.py vs the restored femto port.

  detection  old calc_atr_pct + detect_capitulation  == femto atr_filter_ok + detect_capitulation
  entry      old maybe_enter sizing (size_qty on the last 1H close; tranche 1 = max(1, int(q/2)); tranche 2 =
             the rest) == femto entry qty_hint + position_meta tranche2_qty (fear gate open, earnings clear)
  exits      old check_exit(pos, h1, now) (session VWAP of the pass day) == femto check_exit(pos, h1, session)
  tranche 2  old _maybe_tranche2 timing (weekday sessions since the fill, > 5 expires, 5/20 turn) == femto
Synthetic 1H RTH grids (7 bars/session) over 260 daily bars, with injected capitulation shapes."""
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, walk, write_receipt

F = femto_module("capitulation")
ET = ZoneInfo("America/New_York")

OLD = r'''
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import capitulation_sleeve as O
ET = ZoneInfo("America/New_York")
out = {"det": [], "size": [], "exit": [], "t2": []}
for c in PAYLOAD["det"]:
    a = O.calc_atr_pct(c["daily"])
    ok = a is not None and a > O.ATR_PCT_FILTER
    sig = O.detect_capitulation(c["h1"], c["daily"]) if ok else None
    out["det"].append(None if not sig else [sig["rsi"], sig["climax_vol_mult"]])
for eq, px in PAYLOAD["size"]:
    q = O.size_qty(eq, px)
    out["size"].append(None if q <= 0 else [max(1, int(q * O.TRANCHE1_FRACTION)), q - max(1, int(q * O.TRANCHE1_FRACTION))])
for c in PAYLOAD["exit"]:
    now = datetime.fromtimestamp(c["now"], tz=ET)
    for b in c["h1"]:
        b["t"] = datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz is None else now.astimezone(tz)
    O.datetime = FakeDT
    out["exit"].append(O.check_exit(c["pos"], c["h1"], now))
O.datetime = datetime
for c in PAYLOAD["t2"]:
    since, today = date.fromisoformat(c["since"]), date.fromisoformat(c["today"])
    age = O._sessions_between(since, today)
    out["t2"].append(bool(age <= O.TRANCHE2_MAX_WAIT and O.turn_confirmed(c["daily"])))
print(json.dumps(out))
'''


def _h1_grid(daily_rows, rnd, inject=False):
    """7 RTH clock-hour bars per session (09:00..15:00 ET starts) shaped around each daily bar."""
    out = []
    for r in daily_rows:
        d = date.fromisoformat(r["d"])
        px = r["o"]
        for h in range(9, 16):
            t = datetime(d.year, d.month, d.day, h, 0, tzinfo=ET)
            target = r["c"] if h == 15 else px * (1 + rnd.gauss(0, 0.01))
            o, c = px, target
            hi, lo = max(o, c) * (1 + abs(rnd.gauss(0, 0.004))), min(o, c) * (1 - abs(rnd.gauss(0, 0.004)))
            out.append({"t": t.timestamp(), "o": round(o, 4), "h": round(hi, 4), "l": round(lo, 4), "c": round(c, 4),
                        "v": float(int(rnd.uniform(1e4, 2e5)))})
            px = c
    if inject and len(out) > 40:              # a continuous waterfall, a climax bar, then a green reversal bar
        prev_c = out[-14]["c"]
        for i, k in enumerate(range(-13, -2)):
            nc = prev_c * 0.975
            out[k] = dict(out[k], o=round(prev_c, 4), c=round(nc, 4), h=round(prev_c * 1.002, 4),
                          l=round(nc * 0.998, 4))
            prev_c = nc
        o = prev_c
        cc = o * 0.97
        out[-2] = dict(out[-2], o=round(o, 4), c=round(cc, 4), h=round(o * 1.001, 4), l=round(cc * 0.99, 4),
                       v=float(int(rnd.uniform(6e5, 3e6))))
        out[-1] = dict(out[-1], o=round(cc, 4), c=round(cc * 1.012, 4), h=round(cc * 1.014, 4), l=round(cc * 0.999, 4))
    return out


def run():
    rnd = random.Random(99)
    det, size, exits, t2 = [], [], [], []
    for k in range(300):
        rows = walk(70_000 + k, 270, start_px=rnd.uniform(5, 200), vol=rnd.uniform(0.04, 0.09), drift=rnd.uniform(-0.002, 0.003))
        daily = [{"t": r["d"], "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows[:-1]]
        h1 = _h1_grid(rows[-12:], rnd, inject=rnd.random() < 0.7)
        if rnd.random() < 0.5:          # place the climax low right at the daily EMA200 sometimes
            ema = F.calc_ema200([{"c": b["c"]} for b in daily])
            if ema:
                lo = h1[-2]["l"]
                scale = ema / lo * rnd.uniform(0.985, 1.015)
                h1 = [dict(b, o=b["o"] * scale, h=b["h"] * scale, l=b["l"] * scale, c=b["c"] * scale) for b in h1]
        det.append({"daily": daily, "h1": h1})
        size.append([rnd.choice((50_000.0, 100_000.0)), round(h1[-1]["c"], 4)])
        # exits: a position entered a few sessions ago; pass time inside the last session
        last = date.fromisoformat(rows[-1]["d"])
        entry = last - timedelta(days=rnd.randint(0, 6))
        now = datetime(last.year, last.month, last.day, rnd.choice((10, 12, 15)), 27, tzinfo=ET)
        sess_bars = [b for b in h1 if datetime.fromtimestamp(b["t"], tz=ET).date() <= last
                     and b["t"] + 3600 <= now.timestamp()]
        pos = {"entry_px": round(h1[-8]["c"] * rnd.uniform(0.9, 1.08), 4), "entry_date": entry.isoformat(), "qty": 10}
        exits.append({"pos": pos, "h1": sess_bars, "now": now.timestamp(), "session": last.isoformat()})
        since = last - timedelta(days=rnd.randint(0, 9))
        t2.append({"since": since.isoformat(), "today": last.isoformat(), "daily": daily})
    old = old_run(OLD, {"det": det, "size": size, "exit": exits, "t2": t2})
    n = same = 0
    diffs = []

    def cmp(kind, i, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "i": i, "old": a, "new": b})

    for i, c in enumerate(det):
        d_ep = [{"t": datetime.fromisoformat(b["t"]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
                 **{k: b[k] for k in "ohlcv"}} for b in c["daily"]]
        sig = F.detect_capitulation(c["h1"], d_ep) if F.atr_filter_ok(d_ep) else None
        cmp("det", i, old["det"][i], None if not sig or sig.get("shadow_beyond_ema_band") else [sig["rsi"], sig["climax_vol_mult"]])
    for i, (eq, px) in enumerate(size):
        q = F.size_qty(eq, px)
        cmp("size", i, old["size"][i], None if q <= 0 else [max(1, int(q * F.TRANCHE1_FRACTION)), q - max(1, int(q * F.TRANCHE1_FRACTION))])
    for i, c in enumerate(exits):
        cmp("exit", i, old["exit"][i], F.check_exit(c["pos"], c["h1"], c["session"]))
    for i, c in enumerate(t2):
        # femto tranche-2 gate: drive the sleeve with a held position whose entry_date = since
        d_ep = [{"t": datetime.fromisoformat(b["t"]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
                 **{k: b[k] for k in "ohlcv"}} for b in c["daily"]]
        h1 = det[i]["h1"]
        st = {"SYM": {"position": {"qty": 10, "entry_px": h1[-1]["c"] * 0.5, "entry_date": c["since"],
                                   "tranche2_qty": 7}}}
        ctx = fc.Context(now=datetime.fromisoformat(c["today"]).replace(hour=14, tzinfo=timezone.utc).timestamp(),
                         session=c["today"], equity=100_000.0,
                         extra={"sleeve_state": st, "bars_1h": {"SYM": h1}, "universe": ["SYM"]})
        out = F.signal({"SYM": d_ep}, {"SYM": 10}, ctx)
        # an exit pre-empts tranche 2 in both codes (manage_position runs first); compare only when no exit
        if any(x.kind == "exit" for x in out):
            continue
        cmp("t2", i, old["t2"][i], any(x.kind == "enter" and "tranche2" in x.reason for x in out))
    res = {"sleeve": "capitulation", "cases": n, "identical": same, "diffs": diffs[:30], "n_diffs": len(diffs),
           "signals_fired": sum(1 for x in old["det"] if x)}
    write_receipt("capitulation" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
