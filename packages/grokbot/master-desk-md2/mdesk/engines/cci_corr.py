"""t_cci_corr - CCI correction pullback, long-only daily (Trader t1234u, 2026-10-25 19:29 ET: "install it in our desk").
Spec + provenance: /workspace/cci_correction/STRATEGY.md (from @onlybreakouts' X post 2114454472248230234: Lowest(CCI(27),18) < -100,
"16.5M filter tests on NASDAQ"); posted reply https://x.com/TraderHandle/status/2114499017761546388. NOT backtested; data-mining risk.

Entry (completed daily bar, filled by core at the next open venue): price >= $5, ADV20 >= $20M, close > SMA200, SMA50 > SMA200,
SPY close > SPY SMA200, VIX < 30, min(CCI27 over last 18 bars) < -100, trigger = CCI crosses back above -100 OR (close > prior
high AND CCI rising AND CCI < 0). Rank: lowest 18-bar CCI first.
Exit (completed bars after the fill): initial stop entry - 2*ATR14(signal), target entry + 3R (R = 2*ATR), trail highest close
since fill - 3*ATR14 (ratchets up only), close < SMA200, 20 bars held.
Test-lane sizing ($1k book): 5 slots x $200 (spec's 0.5%-risk sizing is below one share on a $1k book; $200 <= the 15% cap is
not possible either, so the slot is the cap). Symbols priced > $200 are skipped (cannot buy one whole share)."""
import numpy as np
from ..sleeve import Sleeve, Signal
from ..data import Missing
from .. import ind

CCI_N, LOOK, THR = 27, 18, -100.0
FAST, SLOW, ATR_N = 50, 200, 14
STOP_ATR, TRAIL_ATR, TGT_R, MAX_BARS = 2.0, 3.0, 3.0, 20
MIN_PX, MIN_DV, VIX_MAX = 5.0, 20e6, 30.0
STALE_1D = 5 * 86400
POLICY = "cci-v1"

def cci(h, l, c, n=CCI_N):
    tp = (np.asarray(h, float) + np.asarray(l, float) + np.asarray(c, float)) / 3; out = np.full(len(tp), np.nan)
    if len(tp) < n: return out
    w = np.lib.stride_tricks.sliding_window_view(tp, n); m = w.mean(axis=1); md = np.abs(w - m[:, None]).mean(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"): out[n - 1:] = np.where(md > 0, (tp[n - 1:] - m) / (0.015 * md), 0.0)
    return out

def entry(b):
    """signal dict on the LAST completed bar of `b` (Bars), or None."""
    if len(b) < SLOW + 2: return None
    h, l, c, v = (np.asarray(x, float) for x in (b.h, b.l, b.c, b.v))
    px = c[-1]
    if px < MIN_PX: return None
    if np.mean(c[-20:] * v[-20:]) < MIN_DV: return None
    s50, s200 = ind.sma(c, FAST)[-1], ind.sma(c, SLOW)[-1]
    if not (px > s200 and s50 > s200): return None
    k = cci(h, l, c)
    if np.isnan(k[-LOOK:]).any() or np.isnan(k[-2]): return None
    lo = float(np.min(k[-LOOK:]))
    if lo >= THR: return None
    cross = k[-2] <= THR < k[-1]
    turn = c[-1] > h[-2] and k[-1] > k[-2] and k[-1] < 0
    if not (cross or turn): return None
    a = float(ind.atr(h, l, c, ATR_N)[-1])
    if not a > 0: return None
    return dict(px=float(px), atr=a, cci=float(k[-1]), cci_min18=lo, trigger="cross" if cross else "turn")

def regime(hub):
    """(ok, why). SPY > SMA200 and VIX < 30; missing evidence = no entries (never a guess)."""
    s = hub.equity("SPY")
    if isinstance(s, Missing) or len(s) < SLOW: return False, "spy_missing"
    if not s.c[-1] > ind.sma(np.asarray(s.c, float), SLOW)[-1]: return False, "spy_below_sma200"
    x = hub.equity("_VIX")
    if isinstance(x, Missing) or not len(x): return False, "vix_missing"
    if not float(x.c[-1]) < VIX_MAX: return False, "vix_ge_30"
    return True, "ok"

class CCICorr(Sleeve):
    sid = "t_cci_corr"; source = "x-onlybreakouts"; owner = "md2"; family = "daily_pullback_cci_correction"; tf = "1d"
    slots = 5; principal = 1000.0; pos_frac = 0.2; pos_usd = 200.0; dv_cap = 0; status = "installed"; venue = "test"
    reason = "Test account, $1k (5x$200), long-only daily; CCI(27) 18-bar dip < -100 + uptrend + SPY>200d & VIX<30; 2ATR stop/3R/3ATR trail/20 bars"
    def universe(self, hub, ctx): return [s for s in (ctx.get("universe") or hub.universe()) if s.isalpha()]
    def scan(self, hub, ctx):
        ok, _ = regime(hub)
        if not ok: return []
        out = []; memo = self.__dict__.setdefault("_memo", {})
        for s in self.universe(hub, ctx):
            b = hub.equity(s)
            if isinstance(b, Missing) or len(b) < SLOW + 2: continue
            if ctx.get("now") and ctx["now"] - b.t[-1] > STALE_1D: continue
            k = (s, b.t[-1])
            if k not in memo: memo[k] = entry(b)
            e = memo[k]
            if not e or e["px"] > self.pos_usd: continue
            out.append(Signal(s, f"{s}|{int(b.t[-1])}|cci", e["px"], -e["cci_min18"],
                              meta=dict(atr=e["atr"], stop_atr=STOP_ATR, cci=round(e["cci"], 1), cci_min18=round(e["cci_min18"], 1),
                                        trigger=e["trigger"], policy=POLICY)))
        out.sort(key=lambda x: -x.score)   # most oversold first
        return out
    def exit_reason(self, hub, pos, ctx):
        held = pos.get("bars_held", 0)
        if held < 1: return None
        b = hub.equity(pos["symbol"])
        if isinstance(b, Missing): return "time" if held >= MAX_BARS else None
        m = pos.get("meta") or {}; avg = float(pos.get("avg") or 0); a0 = float(m.get("atr") or 0)
        ft = pos.get("fill_ts") or pos.get("entry_ts") or 0
        h, l, c = (np.asarray(x, float) for x in (b.h, b.l, b.c)); after = np.asarray(b.t) > ft
        if avg and a0 > 0 and after.any():
            stop = avg - STOP_ATR * a0; tgt = avg + TGT_R * STOP_ATR * a0
            a = ind.atr(h, l, c, ATR_N); best = -np.inf; trail = -np.inf
            for i in np.nonzero(after)[0]:
                lvl = max(stop, trail)
                if l[i] <= lvl: return f"{'trail' if trail > stop else 'stop'} {lvl:.4g}"
                if h[i] >= tgt: return f"target {tgt:.4g}"
                best = max(best, c[i])
                if not np.isnan(a[i]): trail = max(trail, best - TRAIL_ATR * a[i])
        s200 = ind.sma(c, SLOW)[-1]
        if not np.isnan(s200) and c[-1] < s200: return "close<sma200"
        return "time" if held >= MAX_BARS else None

def load():
    s = CCICorr()
    row = dict(sid=s.sid, source=s.source, family=s.family, status="installed", strategy="CCI correction pullback (Lowest(CCI27,18)<-100, @onlybreakouts)",
               reason=s.reason, origin="/workspace/cci_correction/STRATEGY.md")
    return [s], [row]
