"""t_kz_sweep checks. ALERT-ONLY (prints, never trades, never halts anything).
  python3 tools/kz_check.py          health: feed freshness, sleeve registered, no t_kz_sweep position held past 12:05 ET / overnight
  python3 tools/kz_check.py dryrun   what the sleeve would have signalled on the cached/fetched recent 15m bars (signals only)"""
import sys, os, json, time, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mdesk.engines import kz_sweep as K

def health(now=None):
    now = now or time.time(); d = K._et(now); f = K.Feed(); alerts = []
    for src in sorted(set(K.UNIVERSE) | set(K.UNIVERSE.values())):
        b = f.bars(src, refresh=True)
        age = (now - b[-1][0]) / 60 if b else None
        if age is None: alerts.append(f"feed {src}: no bars")
        elif d.weekday() < 5 and dt.time(9, 45) <= d.time() <= dt.time(12, 0) and age > 30: alerts.append(f"feed {src}: last bar {age:.0f} min old in session")
    from mdesk import registry
    if "t_kz_sweep" not in {s.sid for s in registry.load_all()[0]}: alerts.append("t_kz_sweep not in the registry")
    try:
        from mdesk.ledger import Ledger; from mdesk.fsm import Book
        op = Book.replay(Ledger(f"{K.ROOT}/state/ledger.sqlite")).open_positions("t_kz_sweep")
        late = [k[1] for k, v in op.items() if K._et(v.get("fill_ts") or v.get("entry_ts") or now).date() != d.date() or d.time() >= dt.time(12, 5)]
        if late: alerts.append(f"t_kz_sweep holds {late} past the 12:00 ET time exit")
    except Exception as e: alerts.append(f"ledger read {type(e).__name__}")
    return dict(at=d.strftime("%F %T %Z"), ok=not alerts, alerts=alerts)

def dryrun(days=6):
    f = K.Feed(); out = []
    for sym, src in K.UNIVERSE.items():
        b = f.bars(src); tb = f.bars(sym)
        for day in sorted({K._sday(x[0]) for x in b})[-days:]:
            if day.weekday() >= 5: continue
            hit = None
            for m in range(0, 50, 5):   # md2 passes :00:20 .. 10:30:20, fresh-close rule (<= 20 min) as in scan()
                now = dt.datetime.combine(day, dt.time(9, 45), K.ET).timestamp() + m * 60 + 20
                s = K.signal_at(b, day, now, long_only=sym in K.LONG_ONLY)
                if s and now - s["close_t"] <= 1200: hit = (now, s); break
            if not hit: out.append(dict(sym=sym, day=str(day), signal=None)); continue
            now, s = hit; closed = [x for x in b if x[0] + K.STEP <= now]; spx = closed[-1][4]; up = s["side"] == "buy"
            risk = (spx - s["stop"]) if up else (s["stop"] - spx); rew = (s["target"] - spx) if up else (spx - s["target"])
            r = dict(sym=sym, src=src, day=str(day), pass_et=K._et(now).strftime("%H:%M:%S"), side=s["side"], level=s["level"], rr_signal=s["rr"],
                     src_px=spx, src_stop=round(s["stop"], 2), src_target=s["target"], target=s["target_name"])
            if risk <= 0 or rew / risk < K.MIN_RR: r["outcome"] = f"abstain:rr_at_fill {rew / risk if risk > 0 else None}"; out.append(r); continue   # EDGE-1
            mk = [x for x in tb if x[0] + K.STEP <= now]; px = mk[-1][4] if mk else None; ex = None
            for x in b:   # EDGE-3: exits on the source bars at the signal's absolute levels
                if x[0] < now: continue
                if K._et(x[0]).time() >= K.TSTOP: ex = ("time_stop_1200", x[0]); break
                if (up and x[3] <= s["stop"]) or (not up and x[2] >= s["stop"]): ex = ("stop", x[0]); break
                if (up and x[2] >= s["target"]) or (not up and x[3] <= s["target"]): ex = ("target", x[0]); break
            xp = next((y[1] for y in tb if ex and y[0] >= ex[1]), None) if ex else None
            r.update(outcome="signal", rr_now=round(rew / risk, 2), px=px and round(px, 2), qty=(int(1000 // px) if sym != "BTC-USD" else round(1000 / px, 6)) * (1 if up else -1) if px else None,
                     would_exit=ex and dict(why=ex[0], at=K._et(ex[1]).strftime("%F %H:%M"), etf_px_next_open=xp and round(xp, 2)))
            out.append(r)
    return out

if __name__ == "__main__":
    print(json.dumps(dryrun() if sys.argv[1:] == ["dryrun"] else health(), indent=1, default=str))
