"""GrokBot's CCI correction pullback on this desk: t_cci_corr, "CCI correction (GrokBot)", a forward test.

The owner asked for it on 2026-10-26 ("Add this sleeve please"). GrokBot installed it on its own desk on 2026-10-25 as
a $1k Test sleeve (its master-desk 3acf52d, mdesk/engines/cci_corr.py, not reachable from here). This port follows the
written spec, research/cci_correction/STRATEGY.md (quant-research-backup @75515ada, blob 6d3a4cea), and its reference
code, research/cci_correction/cci_correction.py (blob 49310345), vendored byte-exact as
desk/vendor/cci_correction/cci_correction.py. The reference's cci(), atr(), signals() and size() decide every entry
and size here; this module only carries them onto the engine. Its backtest() is never run: sleeves are never
backtested, and this one has no performance claim.

Rules (long-only, daily bars; evaluated on the completed session t, filled at the next open):
  1. price >= $5 and 20-day average dollar volume >= $20M;
  2. close > SMA200 and SMA50 > SMA200;
  3. SPY close > SPY SMA200, and VIX < 30;
  4. min(CCI(27) over the last 18 bars) < -100;
  5. trigger: CCI crosses back above -100, or close > the prior high while CCI is rising and still below 0;
  6. ranking: lowest CCI first when there are more signals than open slots;
  7. initial stop: entry - 2 x ATR(14) (Wilder's, ewm alpha 1/14, the reference's atr()); target 3R (entry + 6 x ATR);
  8. trailing stop: the highest close since entry - 3 x ATR, ratcheting up only;
  9. exits: the stop or the target during the session (a gap through either sells at the open); a close below
     SMA200; 20 sessions held.
Sizing, the spec's own (GrokBot rendered it as five $200 whole-share slots for its $1k book): shares = 0.5% of equity /
(entry - stop), at most 15% of equity per position, whole shares (the reference's size()); at most 10 positions.
Capital $100,000, the desk's standard sleeve book. Costs are the desk's own fill model; the spec's 5 bps per side is
not charged on top.

Universe: the genome roster (desk/vendor/universes/old_desk/genome_universe_1838.txt, 1,838 names), the universe of
the desk's daily equity scanners, whose split-adjusted daily bars the genome job refreshes after every close (16:21-
19:30 ET). They are read cache-only, the last 260 sessions per name; SPY comes from the same cache, and ^VIX from the
desk's Yahoo daily series.

Clock:
  decide  once per session, at the first pass from 07:00 ET (pre-market), on the last completed session t, once the
          cache holds SPY's and ^VIX's bars for t (until then it waits and asks again every 15 minutes; it never decides
          on older bars). A name without its bar for t is left out. A desk that missed the pre-market decides at its
          first pass in the opening window on the same bars, so a new install or a restart before 09:35 ET still trades
          t's signals at that open. Every held name's completed bars are assessed once: a close below SMA200 owes an
          exit, and the trailing stop is the highest of each session's highest-close-less-3-ATR since the entry.
  open    09:30-09:35 ET: owed exits, then entries for the best-ranked candidates while slots remain (10, counting the
          held names not exiting at this open and the working entries), sized on the quote (the ask, else the last) and
          sent as marketable orders for 300 s.
  hold    the engine holds every exit: the initial stop (ExitRule stop_dist, 2 x ATR of t below the fill), the stop and
          target the sleeve anchors to the fill at its first pass after it (adjust; the stop only ever ratchets up, and
          the trail moves it each session), and the time stop (ExitRule time_sessions 20: twenty sessions counting the
          entry session, sold at the next open).

Named divergences (the reference backtest is the comparison; it is never run):
  1. the close-decided exits, a close below SMA200 and the 20-session time stop, sell at the next open, as the spec's
     header has every rule ("evaluated at the daily close, filled at the next open"); the backtest sold at that close.
  2. the stop and the target trigger on the desk's live marks in the session (the engine's rules), not on the bar's
     low and high; a gap through either at the open sells at the first pass's market.
  3. sizing reads the book's marked equity and the opening quote; the backtest sized on its cash balance at the
     official open. An entry the book's cash cannot pay for (with what this open's exits release) is skipped, not
     resized, and its slot is not given to the next name, as in the backtest.
  4. a name held at the decision (one whose exit is due at that open included) is not a candidate; the backtest could
     buy back a name it sold at that close.
  5. the 3R target is set from the entry quote when the order goes out and re-anchored to the actual fill at the
     sleeve's first pass after the fill (the backtest knew the open).
  6. a missed opening window drops that session's entries (the backtest fills only at the next open); an owed exit
     waits for the next opening."""
import math
import os

import numpy as np
import pandas as pd

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import et_date
from ...vendor.cci_correction import cci_correction as R

SLEEVE_ID = "t_cci_corr"
FAMILY = "grokbot"
TITLE = "CCI correction (GrokBot)"
HERE = os.path.dirname(os.path.abspath(__file__))
GENOME_FILE = os.path.join(HERE, "..", "..", "vendor", "universes", "old_desk", "genome_universe_1838.txt")
UNIVERSE = tuple(dict.fromkeys(l.strip().upper() for l in open(GENOME_FILE) if l.strip() and not l.startswith("#")))
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "75515ada7f938cc5aedf968d5cf7a5b54e5a438d",
          "path": "research/cci_correction/cci_correction.py", "blob": "49310345e84ce7121f25acb453e1dc6dbe63a812",
          "spec": {"path": "research/cci_correction/STRATEGY.md", "blob": "6d3a4ceab82e4c74bfc45b4c3c6e93a7f5213503"},
          "grokbot": "master-desk 3acf52d mdesk/engines/cci_corr.py (GrokBot's install, 2026-10-25)"}
P = R.P()                       # the reference's parameters, unchanged
CAPITAL = 100_000.0
BARS_N = 260                    # a year of sessions: SMA200, CCI(27) over 18 bars, and ATR's ewm settled (13/14)^259
PROXY, VIX = "SPY", "^VIX"
OPEN_WINDOW_S = 300             # entries and owed exits in the session's first five minutes (open+0:open+5)
ORDER_WINDOW_S = 300
RETRY_S = 900                   # a decision waiting for the cache asks again after 15 minutes (pre-market)
MARGIN = 1e-9                   # the pre-screen keeps any name within this of a bound: the reference decides it
TIE = 1e-9
BASIS = (0.6, 1 / 0.6)          # an opening quote this far from t's close is another price basis (a split), not a gap


def _num(x):
    x = float(x)
    return x if math.isfinite(x) else None


# -- frames ------------------------------------------------------------------------------------------------------------
def rows_through(bars, through):
    """{session: bar} of the completed bars up to and including session `through` (the last copy of a session)."""
    out = {}
    for b in bars or ():
        d = et_date(b["t"])
        if d <= through:
            out[d] = b
    return out


def frame(bars, through, n=BARS_N):
    """the reference's daily frame (open, high, low, close, volume on a session-date index) of the last n completed
    bars through session `through`; None when the newest of them is not that session."""
    rows = rows_through(bars, through)
    if not rows or max(rows) != through:
        return None
    days = sorted(rows)[-n:]
    return pd.DataFrame({"open": [float(rows[d]["o"]) for d in days], "high": [float(rows[d]["h"]) for d in days],
                         "low": [float(rows[d]["l"]) for d in days], "close": [float(rows[d]["c"]) for d in days],
                         "volume": [float(rows[d].get("v") or 0.0) for d in days]},
                        index=pd.DatetimeIndex(pd.to_datetime(days)))


def could_enter(df, p=P):
    """False only when the bar at t certainly fails the reference's liquidity or trend rule (rules 1-2), with MARGIN to
    spare for summation order; every other name goes to the reference's signals(), which decides it."""
    c = df.close.to_numpy()
    if len(c) < p.sma_slow or not c[-1] >= p.min_price:
        return False
    v = df.volume.to_numpy()
    if np.mean(c[-20:] * v[-20:]) < p.min_dollar_vol * (1 - MARGIN):
        return False
    slow, fast = np.mean(c[-p.sma_slow:]), np.mean(c[-p.sma_fast:])
    return bool(c[-1] > slow * (1 - MARGIN) and fast > slow * (1 - MARGIN))


def screen(genome, vix_bars, t, held=(), p=P, n=BARS_N):
    """the decision on the completed session t: the reference's signals() on every name's last n bars through t, with
    SPY's frame and ^VIX's closes as its regime inputs. Returns (decision, {held name: its reference frame}) or
    (None, why) while SPY or ^VIX lacks its bar for t."""
    spy = frame(genome.get(PROXY), t, n)
    vixf = frame(vix_bars, t, n)
    if spy is None or vixf is None:
        return None, f"waiting for the {t} bars of " + " and ".join(s for s, f in ((PROXY, spy), (VIX, vixf)) if f is None)
    vix = vixf.close
    spy_sma = float(spy.close.rolling(p.sma_slow).mean().iloc[-1])
    spy_ok = bool((spy.close > spy.close.rolling(p.sma_slow).mean()).iloc[-1])
    vix_ok = bool(vix.iloc[-1] < p.vix_max)
    regime = spy_ok and vix_ok                # the reference's regime at t, the same for every name
    held = set(held)
    cands, held_frames, n_names, n_missing, n_read = [], {}, 0, 0, 0
    for sym in sorted(genome):
        if sym == VIX:
            continue
        df = frame(genome[sym], t, n)
        if df is None:
            n_missing += 1
            continue
        n_names += 1
        mine = sym in held
        if not mine and not (regime and could_enter(df, p)):
            continue
        d = R.signals(df, p, spy, vix)
        n_read += 1
        if mine:
            held_frames[sym] = d
            continue
        last = d.iloc[-1]
        if bool(last.entry):
            cands.append([sym, float(last.cci), float(last.atr), float(last.close)])
    cands.sort(key=lambda r: (r[1], r[0]))     # rule 6: the most oversold first (a tie by symbol)
    dec = {"signal": t, "regime": regime, "spy_close": float(spy.close.iloc[-1]), "spy_sma200": _num(spy_sma),
           "vix": float(vix.iloc[-1]), "names": n_names, "missing": n_missing, "computed": n_read,
           "held": sorted(held), "ranked": cands}
    return dec, held_frames


def shares(equity, entry, atr, p=P):
    """the reference's size() for an entry at `entry` with its initial stop 2 x ATR below."""
    return R.size(float(equity), float(entry), float(entry) - p.stop_atr * float(atr), p)


def trail_since(d, entry_session, avg, p=P):
    """the trailing stop through the frame's last session: the highest of each session's (highest close since the
    entry, the fill included) - 3 x that session's ATR, from the entry session on (the reference's ratchet)."""
    hi, best = float(avg), None
    for day, c, a in zip(d.index, d.close.to_numpy(), d.atr.to_numpy()):
        if day.date().isoformat() < entry_session or not (math.isfinite(c) and math.isfinite(a)):
            continue
        hi = max(hi, float(c))
        lvl = hi - p.trail_atr * float(a)
        best = lvl if best is None else max(best, lvl)
    return best


def below_sma(d, entry_session, after):
    """the first session from the entry session on and after `after` whose close is below its SMA200: (day, close,
    sma) or None (the reference: r.close < r.sma_s)."""
    for day, c, s in zip(d.index, d.close.to_numpy(), d.sma_s.to_numpy()):
        iso = day.date().isoformat()
        if iso < entry_session or (after and iso <= after):
            continue
        if c < s:
            return iso, float(c), float(s)
    return None


# -- the sleeve --------------------------------------------------------------------------------------------------------
class CciCorrection(Sleeve):
    def __init__(self, universe=None):
        self.universe = tuple(universe or UNIVERSE)
        self.spec = {"cache_only": True}        # the genome job keeps these daily bars fresh (desk/jobs.py genome)
        self.CONFIG = SleeveConfig(
            sleeve_id=SLEEVE_ID, family=FAMILY, cadence_s=60, schedule="premarket,rth", universe=self.universe,
            capital=CAPITAL,
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": BARS_N, "cache_only": True,
                             "symbols_for": "screen", "key": "genome"},
                            {"source": "yahoo", "interval": "1d", "n": BARS_N, "symbols_for": "vix", "key": "vix"}],
                   "quotes": {"source": "equity"}},
            params={"title": TITLE, "timeframe": "1d", "hold_sessions": P.max_bars, "cci_len": P.cci_len,
                    "look": P.look, "cci_thr": P.cci_thr, "cci_trig": P.cci_trig, "sma_fast": P.sma_fast,
                    "sma_slow": P.sma_slow, "atr_len": P.atr_len, "stop_atr": P.stop_atr, "trail_atr": P.trail_atr,
                    "target_r": P.target_r, "max_bars": P.max_bars, "risk_pct": P.risk_pct, "max_pos": P.max_pos,
                    "max_pos_pct": P.max_pos_pct, "min_price": P.min_price, "min_dollar_vol": P.min_dollar_vol,
                    "vix_max": P.vix_max, "bars": BARS_N, "universe": "genome_universe_1838"},
            source=SOURCE, state_schema={"decision": "dict", "wait": "dict", "pos": "dict", "owed": "dict",
                                         "open": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _state(self):
        if self.engine is None:
            return {}
        return self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}

    @staticmethod
    def _book_syms(book):
        return sorted(i.split(":", 1)[1] for i, p in ((book.positions if book is not None else {}) or {}).items()
                      if i.startswith("EQ:") and float(p.get("qty") or 0) > 0)

    # -- what the engine reads ---------------------------------------------------------------------------------------
    def universe_now(self, now, book=None):
        return list(dict.fromkeys(list(self.universe) + self._book_syms(book)))

    def decision_due(self, now, st):
        """the session's decision is still to make at `now`: pre-market or in the opening window of a trading day, no
        decision on the last completed session yet, and no wait for the cache recorded within RETRY_S (a cache that is
        not ready is read again every 15 minutes, never at every pass of the open)."""
        session = et_date(now)
        if not cal.is_trading_day(session):
            return False
        o = cal.session_open(session)
        if now > o + OPEN_WINDOW_S:
            return False
        t = cal.prev_trading_day(session).isoformat()
        if (st.get("decision") or {}).get("signal") == t:
            return False
        w = st.get("wait") or {}
        return not (w.get("signal") == t and now - float(w.get("at") or 0) < RETRY_S)

    def bar_symbols(self, need, now, book=None):
        if not self.decision_due(now, self._state()):
            return []
        if need.get("symbols_for") == "vix":
            return [VIX]
        return list(dict.fromkeys(list(self.universe) + self._book_syms(book) + [PROXY]))

    def quote_universe(self, now, book=None):
        """quotes in the opening window only: the held names and the decision's best-ranked names."""
        session = et_date(now)
        if not cal.is_trading_day(session):
            return []
        o = cal.session_open(session)
        if not o <= now <= o + OPEN_WINDOW_S:
            return []
        dec = self._state().get("decision") or {}
        top = [r[0] for r in (dec.get("ranked") or [])[:2 * P.max_pos]]
        return list(dict.fromkeys(self._book_syms(book) + top))

    # -- the pass --------------------------------------------------------------------------------------------------------
    def signal(self, view):
        now, session = float(view.now), view.session
        st = {k: v for k, v in (view.state or {}).items()}
        self._st = st
        if not cal.is_trading_day(session):
            return []
        held = self._held(view)
        self._sync(st, held)
        o = cal.session_open(session)
        opening = o <= now <= o + OPEN_WINDOW_S
        t = cal.prev_trading_day(session).isoformat()
        out, trails = [], {}
        if self.decision_due(now, st):
            out += self._decide(view, st, t, held, trails)
        out += self._manage(view, st, held, trails, opening)
        if opening:
            out += self._entries(view, st, held, t)
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})

    # -- book ------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _held(view):
        exiting = {p["inst"].split(":", 1)[1] for p in (view.extra or {}).get("pending_orders", [])
                   if p["action"] == "exit" and str(p["inst"]).startswith("EQ:")}
        out = {}
        for inst, p in (view.positions or {}).items():
            if not inst.startswith("EQ:") or float(p["qty"]) <= 1e-12:
                continue
            sym = inst.split(":", 1)[1]
            m = p.get("meta") or {}
            opened = float(p.get("opened_at") or view.now)
            out[sym] = {"qty": float(p["qty"]), "avg": float(p["avg"]), "opened_at": opened,
                        "entry_session": et_date(opened), "stop": m.get("stop"), "target": m.get("target"),
                        "pm": m.get("position_meta") or {}, "mark": p.get("mark"), "exiting": sym in exiting}
        return out

    @staticmethod
    def _sync(st, held):
        pos = st.setdefault("pos", {})
        for s in list(pos):
            if s not in held or pos[s].get("opened_at") != held[s]["opened_at"]:
                pos.pop(s)
        for s, h in held.items():
            pos.setdefault(s, {"opened_at": h["opened_at"]})
        owed = st.setdefault("owed", {})
        for s in list(owed):
            if s not in held or owed[s].get("opened_at") != held[s]["opened_at"]:
                owed.pop(s)

    # -- the decision ----------------------------------------------------------------------------------------------------
    def _decide(self, view, st, t, held, trails):
        ex = view.extra or {}
        dec, more = screen(ex.get("bars_genome") or {}, (ex.get("bars_vix") or {}).get(VIX) or [], t, held)
        if dec is None:
            st["wait"] = {"signal": t, "at": float(view.now), "why": more}
            return [Intent("signal", PROXY, reason=f"{SLEEVE_ID} {t}: {more}", signal_key=f"cci:{t}:wait",
                           meta={"signal": t, "waiting": more})]
        dec["at"] = float(view.now)
        st["decision"] = dec
        st.pop("wait", None)
        for s, d in more.items():                 # every held name's completed bars, assessed once
            h, rec = held[s], st["pos"][s]
            trail = trail_since(d, h["entry_session"], h["avg"])
            if trail is not None:                 # applied in this pass only: a split later rescales the engine's stop
                rec["trail"], rec["trail_at"] = trail, t
                trails[s] = trail
            hit = below_sma(d, h["entry_session"], rec.get("assessed"))
            rec["assessed"] = t
            if hit is not None and s not in st["owed"]:
                st["owed"][s] = {"opened_at": h["opened_at"], "signal": hit[0], "close": hit[1], "sma200": hit[2]}
        top = dec["ranked"][:P.max_pos]
        spy_off = dec["spy_sma200"] is None or dec["spy_close"] <= dec["spy_sma200"]
        why = ("regime off: " + ("SPY %.2f <= SMA200 %s" % (dec["spy_close"], "n/a" if dec["spy_sma200"] is None else
                                                            "%.2f" % dec["spy_sma200"])
                                 if spy_off else "VIX %.2f >= %g" % (dec["vix"], P.vix_max))
               ) if not dec["regime"] else (f"{len(dec['ranked'])} candidates of {dec['names']} names; by lowest CCI: "
                                            + ", ".join(f"{r[0]} {r[1]:.1f}" for r in top))
        return [Intent("signal", PROXY, reason=f"{SLEEVE_ID} {t}: {why}"[:300], signal_key=f"cci:{t}:decision",
                       meta={"signal": t, "regime": dec["regime"], "spy_close": dec["spy_close"],
                             "spy_sma200": dec["spy_sma200"], "vix": dec["vix"], "names": dec["names"],
                             "missing": dec["missing"], "candidates": len(dec["ranked"]),
                             "ranked": dec["ranked"][:25], "owed": sorted(st["owed"])})]

    # -- held positions ----------------------------------------------------------------------------------------------------
    def _manage(self, view, st, held, trails, opening):
        out = []
        for s, h in sorted(held.items()):
            atr0 = h["pm"].get("atr_px")                # *_px: the engine rescales it with the position on a split
            stop, target = None, None
            if atr0 is not None and math.isfinite(float(atr0)):
                risk = P.stop_atr * float(atr0)
                want_tgt = h["avg"] + P.target_r * risk
                if h["target"] is None or abs(float(h["target"]) - want_tgt) > TIE * max(1.0, want_tgt):
                    target = want_tgt                  # 3R from the actual fill
                if h["stop"] is None:
                    stop = h["avg"] - risk             # the initial stop, now engine-held at its level
            tr = trails.get(s)
            cur = h["stop"] if h["stop"] is not None else stop
            if tr is not None and (cur is None or tr > float(cur) + TIE * max(1.0, abs(tr))):
                stop = tr
            if stop is not None or target is not None:
                out.append(Intent("adjust", s, stop=stop, target=target, meta={"ratchet": True},
                                  reason=f"{SLEEVE_ID} {s}: " + "; ".join(
                                      x for x in ((f"stop {stop:.4f}" + (" (trail)" if stop == tr else " (entry - 2 ATR)")
                                                   if stop is not None else ""),
                                                  (f"target {target:.4f} (fill + 3R)" if target is not None else ""))
                                      if x)))
            o = st["owed"].get(s)
            if o is not None and opening and not h["exiting"]:
                out.append(Intent("exit", s, signal_key=f"cci:{view.session}:{s}:exit",
                                  order=OrderSpec(window_s=ORDER_WINDOW_S + 60),
                                  reason=f"{SLEEVE_ID} {s}: close {o['close']:.2f} below SMA200 {o['sma200']:.2f} on "
                                         f"{o['signal']}, sold at the next open"))
        return out

    # -- entries -----------------------------------------------------------------------------------------------------------
    def _entries(self, view, st, held, t):
        dec = st.get("decision") or {}
        if dec.get("signal") != t or not dec.get("regime") or not dec.get("ranked"):
            return []
        now = float(view.now)
        pend = {}
        for p in (view.extra or {}).get("pending_orders", []):
            if p["action"] == "enter" and str(p["inst"]).startswith("EQ:"):
                sym = p["inst"].split(":", 1)[1]
                left = max(0.0, float(p["vqty"]) - float(p.get("filled_v") or 0.0))
                pend[sym] = pend.get(sym, 0.0) + left * float(p.get("ref") or 0.0)
        exiting = {s for s, h in held.items() if s in st["owed"] or h["exiting"]
                   or cal.trading_days_between(h["opened_at"], now) >= P.max_bars}
        n_open = len(set(held) - exiting) + len(set(pend) - set(held))
        slots = max(0, P.max_pos - n_open)
        log = st.get("open") if (st.get("open") or {}).get("session") == view.session else None
        if log is None:
            log = st["open"] = {"session": view.session, "signal": t, "sent": [], "skipped": {}}
        if slots == 0:
            return []
        skip = set(dec.get("held") or []) | set(held) | set(pend)
        picks = [r for r in dec["ranked"] if r[0] not in skip][:slots]
        cash = float(view.cash) - sum(pend.values()) + sum(
            h["qty"] * float(h["mark"] or h["avg"]) for s, h in held.items() if s in exiting)
        equity = float(view.equity)
        out = []
        for sym, cci, atr, close in picks:
            q = (view.quotes or {}).get(sym) or {}
            px = q.get("ask") or q.get("last")
            if not px or float(px) <= 0:
                log["skipped"][sym] = "no quote"
                continue
            px = float(px)
            if not BASIS[0] <= px / close <= BASIS[1]:
                log["skipped"][sym] = f"quote {px:.2f} vs close {close:.2f}: another price basis"
                continue
            qty = shares(equity, px, atr)
            if qty < 1:
                log["skipped"][sym] = "size 0"
                continue
            if qty * px > cash + 1e-6:
                log["skipped"][sym] = f"cash {cash:.2f} < {qty * px:.2f}"
                continue
            cash -= qty * px
            risk = P.stop_atr * atr
            log["sent"] = sorted(set(log["sent"]) | {sym})
            log["skipped"].pop(sym, None)
            rank = 1 + [r[0] for r in dec["ranked"]].index(sym)
            out.append(Intent(
                "enter", sym, qty=float(qty), price_hint=px, target=px + P.target_r * risk,
                exit_rules=(ExitRule("stop_dist", risk), ExitRule("time_sessions", float(P.max_bars))),
                order=OrderSpec(window_s=ORDER_WINDOW_S), signal_key=f"cci:{t}:{sym}",
                reason=(f"{SLEEVE_ID} {sym} on {t}: CCI {cci:.1f} (rank {rank} of {len(dec['ranked'])}), close "
                        f"{close:.2f}, ATR {atr:.4f}; {qty} shares at {px:.2f}, stop 2 ATR below the fill, target 3R, "
                        f"trail 3 ATR, 20 sessions")[:300],
                meta={"timeframe": "1d", "position_meta": {
                    "setup": "cci_correction", "signal": t, "cci": cci, "atr_px": atr, "close_px": close,
                    "entry_px": px, "rank": rank, "stop_atr": P.stop_atr, "target_r": P.target_r,
                    "trail_atr": P.trail_atr, "max_bars": P.max_bars}}))
        return out


def sleeves():
    return [CciCorrection()]
