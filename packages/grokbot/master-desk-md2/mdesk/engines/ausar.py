"""Ausar/Aster paper books, implemented from the attached spec (inputs/*.tsv: education_logic / exit / parameters).
Source code for these books (work/ausar-archive/...) is not on GitHub or this box; every rule below cites its TSV row.
Books whose spec is incomplete or whose inputs are unavailable are registered as BLOCKED with the exact reason."""
import csv, json, math, numpy as np
from ..sleeve import Sleeve, Signal
from ..data import Missing
from .. import ind

TSV = "/workspace/desk2/inputs/c2b63943dfe4e31d9470479e3258933a18e0fac8a0896aa2de843369f3f76fe5.tsv"
H4 = 4 * 3600
LIVENESS_H = 96   # the family's own longest specified holding (fixed96)
STALE_1D = 5 * 86400   # a daily bar older than 5 days (Fri open -> Tue after a holiday Monday) = the feed stopped

def _book_id(alias): return "ausar_" + alias.lower().replace("paper book ", "pb").replace(" ", "_")

class _Daily(Sleeve):
    """features computed once per symbol per pass (fan-out via hub memo), shared by every daily book."""
    tf = "1d"; min_px = 0.0
    def __init__(self, row, P):
        self.row, self.P = row, P; self.sid = _book_id(row["book_alias"]); self.source = "ausar"; self.family = row["family"]
        self.slots = int(P.get("maximum_slots", 10)); self.pos_frac = float(P.get("entry_cap_equity", 0.1)); self.dv_cap = float(P.get("entry_cap_native_dv", 0.01))
        self.max_hold = int(P.get("max_hold_bars") or P.get("hold_native_bars") or 0)
    def universe(self, hub, ctx): return ctx.get("universe") or hub.universe()
    def scan(self, hub, ctx):
        """daily rules only change when a new completed bar lands: results are cached per (symbol, last bar time)."""
        out = []; memo = self.__dict__.setdefault("_memo", {})
        for s in self.universe(hub, ctx):
            b = hub.equity(s)
            if isinstance(b, Missing) or len(b) < 210: continue      # cannot evaluate != negative
            if ctx.get("now") and ctx["now"] - b.t[-1] > STALE_1D: continue   # stale bars are missing evidence, not a fresh signal
            k = (s, b.t[-1])
            if k not in memo: memo[k] = self.entry(b)
            r = memo[k]
            if r is not None and b.c[-1] >= self.min_px:
                out.append(Signal(s, f"{s}|{int(b.t[-1])}|{self.sid}", float(b.c[-1]), float(r), meta=dict(atr=float(ind.atr(b.h, b.l, b.c)[-1]), dv20=float(np.mean(b.c[-20:] * b.v[-20:])))))
        return out
    def exit_reason(self, hub, pos, ctx):
        if pos.get("bars_held", 0) < 1: return None   # rules judge COMPLETED holding bars only (never the signal bar itself)
        b = hub.equity(pos["symbol"])
        if isinstance(b, Missing): return "time" if pos.get("bars_held", 0) >= self.max_hold > 0 else None   # missing: only the time exit stays live
        r = self.exit(b, pos)
        if r: return r
        return "time" if self.max_hold and pos.get("bars_held", 0) >= self.max_hold else None
    def exit(self, b, pos): return None

class RSI2Dip(_Daily):        # PB1: Entry wilder_rsi2<=5 & close>sma200 & close<sma5. Exit close>sma5 or 10 bars; no stop.
    def entry(self, b):
        r = ind.wilder_rsi(b.c, 2)[-1]; c = b.c[-1]
        return (5 - r) if r <= 5 and c > ind.sma(b.c, 200)[-1] and c < ind.sma(b.c, 5)[-1] else None
    def exit(self, b, pos): return "close>sma5" if b.c[-1] > ind.sma(b.c, 5)[-1] else None

class Squeeze(_Daily):        # PB2
    def entry(self, b):
        inside, mom = ind.squeeze(b.h[-80:], b.l[-80:], b.c[-80:])
        ok = inside[-2] and not inside[-1] and mom[-1] > 0 and mom[-1] > mom[-2] and b.c[-1] > b.h[-21:-1].max()
        return float(mom[-1]) if ok else None
    def exit(self, b, pos):
        _, mom = ind.squeeze(b.h[-80:], b.l[-80:], b.c[-80:])
        if b.c[-1] < ind.ema(b.c, 20)[-1]: return "close<ema20"
        if mom[-1] <= 0: return "momentum<=0"
        st = pos.get("meta", {}).get("stop")
        return "initial_2atr_stop" if st and b.l[-1] <= st else None

class Trend55(_Daily):        # PB157
    def entry(self, b):
        sm = ind.sma(b.c, 200)[-1]; return (b.c[-1] / b.h[-56:-1].max() - 1) if b.c[-1] > b.h[-56:-1].max() and b.c[-1] > sm else None
    def exit(self, b, pos):
        if b.c[-1] < b.l[-21:-1].min(): return "close<prior20low"
        if b.c[-1] < ind.sma(b.c, 200)[-1]: return "close<sma200"
        st = pos.get("meta", {}).get("stop")
        return "initial_2atr_stop" if st and b.l[-1] <= st else None

class FixedETF(Sleeve):
    """PB97-107 fixed portfolios. BUY_HOLD: one initial allocation, hold units. MONTHLY: rebalance to target at the
    first session of each month (09:35-09:40 ET window), sells before buys."""
    tf = "1d"
    def __init__(self, row, P, weights):
        self.row, self.P = row, P; self.sid = _book_id(row["book_alias"]); self.source = "ausar"; self.family = "etf"
        self.weights = weights; self.gross = float(P["gross_target"]); self.monthly = P["frequency"] == "MONTHLY"; self.slots = len(weights)
        self.fee_bps = float(P.get("cost_bps_per_side", 15))
    def targets(self, hub, equity):
        out = {}
        for s, w in self.weights.items():
            b = hub.equity(s)
            if isinstance(b, Missing): return b
            out[s] = math.floor(equity * self.gross * w / (b.c[-1] * (1 + self.fee_bps / 1e4)))   # fee-funded whole shares
        return out

class CryptoBook(Sleeve):
    """PB5-6,44-82,109-126: OKX 4H completed spot bars (Ausar used Binance USDT; Binance/Bybit return 451/403 from this host,
    OKX USDT markets are the closest observable venue — recorded as a venue substitution). Long spot, shadow paper only."""
    tf = "4h"; venue = "shadow-crypto"
    def __init__(self, row, P, kind):
        self.row, self.P, self.kind = row, P, kind; self.sid = _book_id(row["book_alias"]); self.source = "ausar"; self.family = row["family"]
        self.fee_bps = float(P.get("fee_bps", 10)); self.sym = P["symbol"]; self.inst = self.sym.replace("USDT", "-USDT"); self.exit_policy = P.get("exit_policy", "fixed16")
        self.capacity = P.get("capacity", "fullcash"); self.slots = 1; self.pos_frac = 1.0
    def _absorb(self, b):
        """confirmed absorption (PB5 spec): shock bar [-2]: v > 2*EMA20(v) incl., c<o, c<EMA50(c) incl.; confirm bar [-1]: c>o and c>(shock h+l)/2."""
        if len(b) < 300: return None
        ev, ec = ind.ema(b.v, 20), ind.ema(b.c, 50); i = len(b) - 2
        shock = b.v[i] > 2 * ev[i] and b.c[i] < b.o[i] and b.c[i] < ec[i]
        return bool(shock and b.c[-1] > b.o[-1] and b.c[-1] > (b.h[i] + b.l[i]) / 2)
    def _breakout(self, b): return len(b) >= 21 and b.c[-1] > b.h[-21:-1].max()
    def scan(self, hub, ctx):
        b = hub.okx_4h(self.inst)
        if isinstance(b, Missing): return []
        k = self.kind
        if k in ("absorption_base", "confirmed_absorption", "absorption_negative_funding", "absorption_nonnegative_funding"):
            if not self._absorb(b): return []
        elif k in ("breakout_base", "negative_funding_squeeze"):
            if not self._breakout(b): return []
        if k in ("negative_funding_squeeze", "absorption_negative_funding", "absorption_nonnegative_funding"):
            f = hub.funding(self.inst + "-SWAP")
            if isinstance(f, Missing): return []                 # missing funding is NOT assumed zero (spec)
            if (k == "absorption_nonnegative_funding") != (f >= 0): return []
        qty = None
        if self.capacity == "volume1pct": qty = 0.01 * float(b.v[-1])   # <=1% of the preceding 4h volume (base units)
        lvl = float(b.h[-21:-1].max()) if len(b) >= 21 else None
        return [Signal(self.sym, f"{self.sym}|{int(b.t[-1])}|{self.sid}", float(b.c[-1]), 1.0, qty=qty, meta=dict(confirm_t=float(b.t[-1]) + H4, level=lvl))]
    def exit_reason(self, hub, pos, ctx):
        m = pos.get("meta", {}); due = {"fixed16": 16, "fixed96": 96}.get(self.exit_policy)
        age_h = (ctx["now"] - m.get("confirm_t", pos.get("entry_ts", ctx["now"]))) / 3600
        if due: return f"fixed{due}h" if age_h >= due else None
        b = hub.okx_4h(self.inst)
        if isinstance(b, Missing): return None
        lost = m.get("level") and b.c[-1] < m["level"]
        if self.exit_policy == "lost_breakout": return "lost_breakout" if lost else None
        f = hub.funding(self.inst + "-SWAP")
        if isinstance(f, Missing):   # Edge desk-runtime 4: a feed that never returns must not trap the position forever
            return f"funding unobservable for {age_h:.0f}h >= {LIVENESS_H}h (liveness backstop)" if age_h >= LIVENESS_H else None
        if self.exit_policy == "normalization": return "funding_reset" if f >= 0 else None
        if self.exit_policy == "normalization_failure": return "funding_reset+price_failure" if f >= 0 and lost else None
        return None

class SMA200Spot(Sleeve):
    fee_bps = 20.0   # spec fee_per_side 0.002
    """PB7-8: Coinbase USD spot daily; each asset held at 50% target while close>SMA200, reduced when below."""
    tf = "1d"; venue = "shadow-crypto"
    def __init__(self, row, P):
        self.row, self.P = row, P; self.sid = _book_id(row["book_alias"]); self.source = "ausar"; self.family = "native_trend"; self.slots = 2; self.pos_frac = 0.5
    def scan(self, hub, ctx):
        out = []
        for prod in ("BTC-USD", "ETH-USD"):
            b = hub.coinbase_1d(prod)
            if isinstance(b, Missing): continue
            if b.c[-1] > ind.sma(b.c, 200)[-1]: out.append(Signal(prod, f"{prod}|{int(b.t[-1])}|{self.sid}", float(b.c[-1]), 1.0))
        return out
    def exit_reason(self, hub, pos, ctx):
        b = hub.coinbase_1d(pos["symbol"])
        if isinstance(b, Missing): return None
        return "close<sma200" if b.c[-1] < ind.sma(b.c, 200)[-1] else None

FIXED = {"QLD_ONLY_BUY_HOLD": {"QLD": 1}, "QLD_ONLY_MONTHLY": {"QLD": 1}, "QQQ_HOLD_FULL": {"QQQ": 1}, "QQQ_MONTHLY": {"QQQ": 1},
         "QQQ_QLD_50_50_BUY_HOLD": {"QQQ": .5, "QLD": .5}, "QQQ_QLD_50_50_MONTHLY": {"QQQ": .5, "QLD": .5}, "SMH_HOLD": {"SMH": 1},
         "SPY_HOLD_FULL": {"SPY": 1}, "SPY_MONTHLY": {"SPY": 1}}
CRYPTO_KINDS = {"negative_funding_squeeze", "breakout_base", "absorption_base", "absorption_negative_funding", "absorption_nonnegative_funding", "confirmed_absorption"}
DUP_OF_MUSE = {"midna_em_1587": "em_1587", "midna_po10_qqq": "po10_qqq", "midna_saty_day": "saty_day", "midna_saty_sol_0dte": "saty_sol_0dte", "midna_saty_sol": "saty_sol"}

def rows():
    return list(csv.DictReader(open(TSV), delimiter="\t"))

def load():
    """-> (installed sleeves, catalog rows for every book with status/reason/dedupe)."""
    out, cat = [], []
    for r in rows():
        P = json.loads(r["education_parameters_json"] or "{}"); fam = r["family"]; title = r["strategy_title"]; sl = None; status, reason, dd = "installed", "", None
        if fam == "public_recipe":
            cls = {"RSI2 dip rebound": RSI2Dip, "Volatility-squeeze breakout": Squeeze, "55-bar trend breakout": Trend55}.get(title)
            if cls: sl = cls(r, P)
            elif title == "High-volume trend candle" or title == "Large-body momentum candle" or title == "Filtered RSI2 dip rebound":
                dd = {"High-volume trend candle": "fwd_alpaca_link_ai_volume", "Large-body momentum candle": "fwd_alpaca_enj_iu_body", "Filtered RSI2 dip rebound": "fwd_alpaca_ada_rsi2"}[title]
                status, reason = "merged", f"same public recipe/symbol as muse-desk-v2 {dd} (runs there)"
        elif fam == "etf":
            if P["policy"] in FIXED: sl = FixedETF(r, P, FIXED[P["policy"]])
            else: status, reason = "blocked", "ranked ETF policy: the 'configured ETF basket' membership is not in the spec TSV and the Ausar source (work/ausar-archive) is not on GitHub or this box"
        elif fam in CRYPTO_KINDS: sl = CryptoBook(r, P, fam)
        elif fam == "native_trend": sl = SMA200Spot(r, P)
        elif fam in DUP_OF_MUSE: dd = DUP_OF_MUSE[fam]; status, reason = "merged", f"same Midna port as muse-desk-v2 {dd}"
        elif fam in ("recovery", "core_reserve", "xsp_pcs", "opening_gamma", "pead", "tensor_leaps"):
            status, reason = "blocked", "options book: needs option chain + reference-model pricing feed (not yet wired in md2)"
        elif fam in ("G4", "C1", "BETA", "tensor", "hourly"):
            status, reason = "blocked", "needs canonical Tensor v698 event/feature mapping (buy-green/cyan events, depth60, vote panel) - columns exist in the engine CSVs, mapping not yet verified"
        else:
            status, reason = "blocked", f"intraday family '{fam}' (10m/30m bars) not yet wired"
        if sl: out.append(sl)
        cat.append(dict(sid=_book_id(r["book_alias"]), source="ausar", family=fam, strategy=r["exact_variant"], entry=r["education_logic"][:400],
                        exit=r["education_exit_summary"][:300], data=r["education_inputs"][:200], status=status, reason=reason, merged_into=dd,
                        origin=r["sleeve_local_sources"].split(" | ")[0]))
    return out, cat
