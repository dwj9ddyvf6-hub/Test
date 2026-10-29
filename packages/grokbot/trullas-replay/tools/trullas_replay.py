"""t_trullas + t_trullas_v01..v10 SIGNALS-ONLY replay sanity check (no fills, no P&L, no backtest): feeds the last <=5 sessions of Yahoo 1m bars to each
sleeve's scan() at every md2 pass time (5-min grid +20 s) inside its entry window and counts distinct signals / abstentions. Counts only.
  python3 tools/trullas_replay.py [--json PATH]"""
import sys, os, json, tempfile, datetime as dt, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mdesk.engines import trullas as T, trullas_var as V

class Fake:
    def __init__(self, m): self.m = m
    def bars(self, sym, refresh=True): return self.m.get(sym, [])

def run(feeds=None):
    f = T.Feed(ttl=0); feeds = feeds or {s: f.bars(s) for s in ("QQQ", "NQ=F", "QQQM")}
    days = sorted({T._et(b[0]).date() for b in feeds["QQQ"]})
    days = [d for d in days if d > days[0] and d < dt.datetime.now(T.ET).date()]    # first session has no warm-up; today excluded (still forming)
    sleeves = [("t_trullas", lambda **k: T.Trullas(**k))] + [(vid, (lambda vid=vid: lambda **k: V.build(vid, **k))()) for vid in V.VARIANTS]
    res = {}
    for sid, mk in sleeves:
        cnt = collections.Counter(); bydir = collections.Counter(); kinds = collections.Counter(); lots = collections.Counter()
        for d in days:
            lg = tempfile.mktemp(suffix=".jsonl"); now = None
            sl = mk(feed=Fake(feeds), dlog=lg)
            t = dt.datetime.combine(d, dt.time(9, 35, 20), T.ET)
            while t.time() <= dt.time(11, 6):
                now = t.timestamp(); fk = Fake({k: [b for b in v if b[0] + 60 <= now] for k, v in feeds.items()}); sl.feed = fk; sl.clock = (lambda n=now: n)
                try: sl.scan(None, dict(now=now))
                except RuntimeError: cnt["stale_feed_passes"] += 1
                t += dt.timedelta(minutes=5)
            if os.path.exists(lg):
                for r in map(json.loads, open(lg)):
                    cnt[r["outcome"]] += 1
                    if r["outcome"] == "signal": bydir[r["side"]] += 1; kinds[r["kind"]] += 1; lots[r["lots"]] += 1
        res[sid] = dict(days=len(days), outcomes=dict(cnt), sides=dict(bydir), kinds=dict(kinds), lots=dict(lots))
    return res

def wide(feeds=None):
    """diagnostic only: distinct setups (P2,side) per sleeve over the whole RTH session (entry window removed), to show the engine finds setups at all."""
    import dataclasses
    f = T.Feed(ttl=0); feeds = feeds or {s: f.bars(s) for s in ("QQQ", "NQ=F")}
    days = [d for d in sorted({T._et(b[0]).date() for b in feeds["QQQ"]})[1:] if d < dt.datetime.now(T.ET).date()]; out = {}
    for sid in ["t_trullas"] + list(V.VARIANTS):
        P = T.base_params() if sid == "t_trullas" else V.build(sid).P; W = dataclasses.replace(P, win0=dt.time(9, 30), win1=dt.time(15, 59)); n = 0
        for d in days:
            seen = set(); t = dt.datetime.combine(d, dt.time(9, 31), T.ET)
            while t.time() < dt.time(15, 59):
                now = t.timestamp(); s = T.signal_at([x for x in feeds.get(P.src, []) if x[0] + 60 <= now], now, W)
                if s: seen.add((s["p2"], s["side"]))
                t += dt.timedelta(minutes=1)
            n += len(seen)
        out[sid] = n
    return out

if __name__ == "__main__":
    if "--wide" in sys.argv: print(json.dumps(wide())); sys.exit(0)
    r = run()
    for sid, x in r.items(): print(f"{sid:14s} days={x['days']} signals={x['outcomes'].get('signal', 0):2d} sides={x['sides']} kinds={x['kinds']} lots={x['lots']} abstain={ {k: v for k, v in x['outcomes'].items() if k != 'signal'} }")
    if "--json" in sys.argv: json.dump(r, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
