"""t_kz_sweep - JadeCap-style ICT liquidity-sweep reversal (Trader OK 2026-10-24 21:23 ET). Spec + provenance:
/workspace/othersidebj/othersidebj_compiled.md (X @OtherSideBJ posts 2112004867137175768, 2113928736131391980); doc docs/KZ_SWEEP.md.

Levels (prior Globex day H/L, untouched D-2/D-3 H/L, Asia 20-24, London 02-05, pre-open H/L) are built on 15m futures bars
(NQ=F -> QQQ, ES=F -> SPY) or on BTC-USD itself, entry = a 15m close back across a swept level inside 09:45-10:30 ET, stop beyond
the session extreme, target = nearest untouched opposite level with R:R >= 1.5, hard time exit 12:00 ET, never overnight.
Futures prices are translated to the traded ETF by % distance from the signal close. Adds are OFF (slot stays $1k).
Feed: Yahoo chart API 15m (prepost), cached to state/kz_feed, fetched only when needed (weekday 09:40-12:10 ET or cold cache)."""
import os, json, time, urllib.request, datetime as dt
from zoneinfo import ZoneInfo
from ..sleeve import Sleeve, Signal
ET = ZoneInfo("America/New_York"); ROOT = "/workspace/desk2"; FEED = f"{ROOT}/state/kz_feed"
UNIVERSE = {"QQQ": "NQ=F", "SPY": "ES=F", "BTC-USD": "BTC-USD"}   # traded symbol -> level source
LONG_ONLY = {"BTC-USD"}                                             # Alpaca crypto: no shorts
WIN0, WIN1, TSTOP = dt.time(9, 45), dt.time(10, 30), dt.time(12, 0)
MIN_RR, BUF, LOOKBACK, STEP = 1.5, 0.0002, 3, 900
POLICY = "kz-v2"   # v1 c7deaa3; v2 = Edge Lab v3 review (docs/KZ_SWEEP.md section Edge review): EDGE-1 revalidate, EDGE-2 log, EDGE-3 source exits
DLOG = f"{ROOT}/state/kz_decisions.jsonl"

class Feed:
    """15m OHLCV per Yahoo symbol: list of (t_epoch_start, o, h, l, c). Network at most once per `ttl` s per symbol."""
    def __init__(self, ttl=240, http=None, clock=time.time):
        self.ttl, self.clock, self.http, self.mem = ttl, clock, http or self._http, {}
    @staticmethod
    def _http(sym):
        u = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=15m&range=8d&includePrePost=true"
        return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=8).read())
    def _parse(self, j):
        r = j["chart"]["result"][0]; q = r["indicators"]["quote"][0]; out = []
        for i, t in enumerate(r.get("timestamp") or []):
            v = [q[k][i] for k in ("open", "high", "low", "close")]
            if None not in v: out.append((int(t), *map(float, v)))
        return out
    def bars(self, sym, refresh=True):
        now = self.clock(); m = self.mem.get(sym)
        if m and (now - m[0] < self.ttl or not refresh): return m[1]
        path = f"{FEED}/{sym.replace('=', '_')}.json"
        if refresh:
            try:
                b = self._parse(self.http(sym))
                if b:
                    os.makedirs(FEED, exist_ok=True); tmp = path + ".tmp"; json.dump(b, open(tmp, "w")); os.replace(tmp, path)
                    self.mem[sym] = (now, b); return b
            except Exception: pass   # fall through to disk cache; freshness is judged by the caller (alert, never a guess)
        try: b = [tuple(x) for x in json.load(open(path))]; self.mem[sym] = (now, b); return b
        except (OSError, ValueError): return []

def _et(t): return dt.datetime.fromtimestamp(t, ET)
def _sday(t): return (_et(t) + dt.timedelta(hours=6)).date()   # Globex day rolls 18:00 ET
def _open(day): return dt.datetime.combine(day, dt.time(9, 30), ET).timestamp()
def _inwin(t, a, b): x = _et(t).time(); return (a <= x < b) if a < b else (x >= a or x < b)

def levels(bars, day):
    """liquidity pools known before the 09:30 open of Globex day `day`: name -> (px, 'high'|'low', formed_t)."""
    days = sorted({_sday(b[0]) for b in bars}); days = [d for d in days if d < day]
    if len(days) < LOOKBACK: return {}
    o = _open(day); pre = [b for b in bars if _sday(b[0]) == day and b[0] < o]; lv = {}
    for k in range(1, LOOKBACK + 1):
        d = [b for b in bars if _sday(b[0]) == days[-k]]
        if not d: continue
        tag = "PD" if k == 1 else f"D-{k}"; hi = max(d, key=lambda b: b[2]); lo = min(d, key=lambda b: b[3])
        lv[tag + "H"] = (hi[2], "high", hi[0]); lv[tag + "L"] = (lo[3], "low", lo[0])
    for n, a, z in (("Asia", dt.time(20), dt.time(0)), ("Lon", dt.time(2), dt.time(5)), ("Pre", dt.time(18), dt.time(9, 30))):
        w = [b for b in pre if _inwin(b[0], a, z)]
        if w: lv[n + "H"] = (max(b[2] for b in w), "high", w[-1][0]); lv[n + "L"] = (min(b[3] for b in w), "low", w[-1][0])
    out = {}
    for n, (px, s, t) in lv.items():   # older-day levels count only while untouched up to the open
        later = [b for b in bars if t < b[0] < o]
        hit = any(b[2] >= px for b in later) if s == "high" else any(b[3] <= px for b in later)
        if not (n.startswith("D-") and hit): out[n] = (px, s, t)
    return out

def signal_at(bars, day, upto, long_only=False):
    """first qualifying sweep-and-reclaim among 15m bars CLOSED by `upto` (epoch) on `day`. Returns dict or None."""
    lv = levels(bars, day)
    if not lv: return None
    o = _open(day); cur = [b for b in bars if _sday(b[0]) == day and b[0] + STEP <= upto]
    for i, b in enumerate(cur):
        close_t = b[0] + STEP; ct = _et(close_t).time()
        if b[0] < o or not (WIN0 <= ct <= WIN1): continue
        sofar = cur[:i + 1]
        if "PDH" in lv and "PDL" in lv and max(x[2] for x in sofar) >= lv["PDH"][0] and min(x[3] for x in sofar) <= lv["PDL"][0]:
            return None   # both prior-day extremes swept -> range day, stand aside [SRC]
        ny = [x for x in sofar if x[0] >= o]; lo = min(x[3] for x in ny); hi = max(x[2] for x in ny); c = b[4]
        L = [px for px, s, _ in lv.values() if s == "low" and lo < px < c]
        H = [] if long_only else [px for px, s, _ in lv.values() if s == "high" and hi > px > c]
        if bool(L) == bool(H): continue
        side = "buy" if L else "sell"; e = c
        stop = lo * (1 - BUF) if L else hi * (1 + BUF); risk = abs(e - stop)
        opp = "high" if L else "low"; tg = []
        for n, (px, s, t) in lv.items():
            if s != opp or (px <= e if L else px >= e): continue
            seg = [x for x in bars if t < x[0] <= b[0]]
            if any((x[2] >= px) if L else (x[3] <= px) for x in seg): continue   # line already stopped
            if risk > 0 and abs(px - e) / risk >= MIN_RR: tg.append((abs(px - e) / risk, n, px))
        if not tg: continue
        rr, tn, tv = min(tg)
        lvl = max(L) if L else min(H)
        name = next(n for n, v in lv.items() if v[0] == lvl)
        return dict(side=side, level=name, level_px=lvl, entry=e, stop=stop, target=tv, target_name=tn, rr=round(rr, 2), close_t=close_t)
    return None

class KZSweep(Sleeve):
    sid = "t_kz_sweep"; source = "x-othersidebj"; owner = "md2"; family = "intraday_reversal_liquidity_sweep"; tf = "15m"
    slots = 3; principal = 3000.0; pos_frac = 1 / 3; pos_usd = 1000.0; dv_cap = 0; status = "installed"; venue = "test"
    reason = "Test account, 3x$1k, QQQ/SPY (NQ/ES levels) + BTC-USD long-only; 09:45-10:30 entries, 12:00 ET flat"
    def __init__(self, feed=None, clock=time.time, dlog=None):
        self.feed = feed or Feed(clock=clock); self.clock = clock; self._seen = set(); self.dlog = dlog or DLOG
    def _live(self, now): d = _et(now); return d.weekday() < 5 and dt.time(9, 40) <= d.time() <= dt.time(12, 10)
    def mark(self, hub, sym):
        b = self.feed.bars(sym, refresh=self._live(self.clock()))
        return b[-1][4] if b and self.clock() - b[-1][0] < 1800 else None   # stale -> None (core waits + alerts; never a guess)
    def _log(self, row):
        """EDGE-2 (Edge Lab v3 s.7/validation s.7): append-only decision log incl. abstentions, written BEFORE outcomes, so the
        forward test has the full eligible-opportunity population (not only fills). One row per (day, symbol, outcome)."""
        k = (row["day"], row["sym"], row["outcome"])
        if k in self._seen: return
        self._seen.add(k)
        try:
            os.makedirs(os.path.dirname(self.dlog), exist_ok=True)
            with open(self.dlog, "a") as f: f.write(json.dumps(dict(row, policy=POLICY, logged_at=self.clock())) + "\n")
        except OSError: pass   # logging never blocks a decision
    def scan(self, hub, ctx):
        now = ctx["now"]; d = _et(now)
        if d.weekday() >= 5 or not (WIN0 <= d.time() <= dt.time(10, 31)): return []
        out, stale = [], []
        for sym, src in UNIVERSE.items():
            b = self.feed.bars(src); base = dict(day=f"{d:%F}", sym=sym, src=src, cluster=None)
            if not b or now - b[-1][0] > 1800: stale.append(src); self._log(dict(base, outcome="abstain:stale_feed")); continue
            s = signal_at(b, d.date(), now, long_only=sym in LONG_ONLY)
            if not s: continue
            base.update(cluster=f"{d:%F}|{s['side']}" if src != sym else None, level=s["level"], rr_signal=s["rr"],
                        signal_close_et=_et(s["close_t"]).strftime("%H:%M"), bar_age_s=round(now - (b[-1][0] + STEP)))
            if now - s["close_t"] > 1200: self._log(dict(base, outcome="abstain:signal_older_than_20min")); continue
            # EDGE-1: revalidate at the submission boundary on the source's latest CLOSED bar - the R:R and stop side must still
            # hold at the price we can actually get, not only at the signal close (the old rule could fill past the stop/target).
            closed = [x for x in b if x[0] + STEP <= now]; px = closed[-1][4] if closed else s["entry"]
            up = s["side"] == "buy"; risk = (px - s["stop"]) if up else (s["stop"] - px); rew = (s["target"] - px) if up else (px - s["target"])
            if risk <= 0 or rew / risk < MIN_RR:
                self._log(dict(base, outcome="abstain:rr_at_fill_below_min", rr_now=round(rew / risk, 2) if risk > 0 else None)); continue
            self._log(dict(base, outcome="signal", side=s["side"], src_px=px, src_stop=s["stop"], src_target=s["target"], rr_now=round(rew / risk, 2)))
            k = lambda v: v / px
            out.append(Signal(sym, f"{sym}|{d:%F}|kz", px if src == sym else (self.mark(hub, sym) or 0.0), rew / risk,
                              meta=dict(side=s["side"], stop_rel=k(s["stop"]), target_rel=k(s["target"]), src=src, src_stop=s["stop"],
                                        src_target=s["target"], level=s["level"], target_name=s["target_name"], rr=round(rew / risk, 2),
                                        cluster=base["cluster"], day=f"{d:%F}", time_exit="12:00 ET", policy=POLICY)))
        if stale: raise RuntimeError(f"kz feed stale/missing for {','.join(stale)} inside the entry window")   # alert-only path
        return out
    def exit_reason(self, hub, pos, ctx):
        now = ctx["now"]; d = _et(now); m = pos.get("meta") or {}; ft = pos.get("fill_ts") or pos.get("entry_ts") or now
        if d.date() != _et(ft).date() or d.time() >= TSTOP: return "time_stop_1200_et"
        q = pos.get("qty") or 0
        if "src_stop" in m:
            # EDGE-3: stop/target are judged on the SOURCE bars at the absolute levels the signal defined (NQ/ES), not on
            # %-translated ETF prices: measured 15m QQQ-NQ / SPY-ES basis noise is 2.9 / 2.5 bp sd, above the 2 bp stop buffer.
            src, stop, tgt = m["src"], m["src_stop"], m["src_target"]; up = q > 0
        else:   # positions opened by policy kz-v1 (none were) keep their original rule
            avg = pos.get("avg") or 0
            if not avg or "stop_rel" not in m: return None
            src, stop, tgt, up = pos["symbol"], avg * m["stop_rel"], avg * m["target_rel"], q > 0
        bars = [b for b in self.feed.bars(src, refresh=self._live(now)) if b[0] >= ft]   # bars after the fill only
        for b in bars:
            if up and b[3] <= stop or not up and b[2] >= stop: return f"stop {stop:.6g} ({src})"
            if up and b[2] >= tgt or not up and b[3] <= tgt: return f"target {tgt:.6g} ({src})"
        return None

def load():
    s = KZSweep()
    row = dict(sid=s.sid, source=s.source, family=s.family, status="installed", strategy="ICT killzone sweep & reclaim (JadeCap via @OtherSideBJ)",
               reason=s.reason, origin="/workspace/othersidebj/othersidebj_compiled.md")
    return [s], [row]
