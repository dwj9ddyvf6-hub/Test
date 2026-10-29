"""Qullamaggie pass-3 research desk (qullamaggie-research-pass3 @00f8d0a2 inferred_rules.md; its implementation, the
temporally fixed desk_fixed.py, lives in midna @7969b522 workspace/qualla_desk/pass3/ and is vendored byte-exact as
desk/vendor/qullamaggie_pass3/desk_fixed.py, DEFAULTS = the repo's config_inferred.json) — its three setups, one
sleeve each, the source's own AgenticResearchDesk.scan deciding every entry:

  qm_leader_breakout_pass3  breakout: a top-2% leader (best of the 21/63/126-session return percentiles) after a
                            >= 30% impulse, in a tight (<= 28%), tightening, higher-low 10-session base riding its
                            rising 10/20-day averages, $5M ADV, QQQ risk-on (10 > 20-day SMA, both rising); the
                            1-minute tape crosses max(5-minute opening-range high, base pivot) -> long, stop = the
                            low before the trigger bar within 1 ATR.
  qm_episodic_pivot         episodic pivot: a verified catalyst public before the trigger minute, gap >= 10%, first-20
                            minute volume >= 0.5x the 20-day average, 126-session return <= 30%, risk-on; the tape
                            crosses the opening-range high at minute 20 or later -> long.
  qm_parabolic_short        parabolic short: >= 3 up closes, a 3-session run >= 50% (>= 300% under $300M market cap),
                            borrow; the opening-range low breaks with the bar's close under the session VWAP -> short at
                            the next bar, stop = the high before the fill, half the long risk.

Sizing (the source's size_position / RiskGateAgent / PortfolioGovernorAgent, per sleeve book of $100,000): 0.35% of
the session's opening equity on the stressed loss per share (stop distance + the 95th-percentile overnight gap +
round-trip friction), capped by 20% notional per name, 100% gross, 25% per sector, 4% aggregate open risk, 1% of
ADV, 15 positions; proposals reserved by score. Management (the source's backtest): the hard stop; at the close of
the third session held, in profit: 1/3 off and the stop to breakeven; a close under the 10-day SMA (the 20-day when
the close is more than 1.5 ATR above the 10-day; shorts always the 10-day) after three sessions queues the exit for
the next open; shorts cover at max(10-day, 20-day SMA) of the completed closes.

Removed under the cutover doctrine: desk_eod_loss_lock (the book down >= 1.5% on the day flattened every position
at the close) — a drawdown brake.

Named divergences:
  1. one setup per sleeve: setup_precedence = [the sleeve's setup] (the source's one book resolved a name matching
     two setups to EP > breakout > short); each setup trades its own book, so a name may be held by two sleeves.
  2. universe: the desk's 1,838-name genome without its ETFs (Nasdaq Trader symbol directory) — the protocol named
     current S&P 1500 / Russell 1000 constituents; daily bars are the genome cache's split-adjusted bars (refreshed
     by the genome job after each close), the last 140 sessions per name (the features read the last 127), and a
     name without the last completed session in the cache is left out of that session's frame.
  3. events: SEC EDGAR 8-K / 6-K current reports, the acceptance time as the public timestamp, news_verified = True
     (desk/feedlib/qm_inputs.py) — the source read a licensed / manually verified catalyst file.
  4. universe metadata: sector = the filer's SEC EDGAR industry office, market cap = the latest EDGAR cover-page
     share count x the last close, borrowable = True (the router sends a short Alpaca cannot borrow to the desk's
     simulated equity venue on live quotes) — the source read a point-in-time universe file. A name without EDGAR
     data is sector UNKNOWN and has no market cap (no parabolic short), exactly as the source's metadata default.
  5. live session: the source scanned each completed session once (all of the day's triggers reserved by score,
     positions stopped later that day released before the scan). Here a pass every minute scans the completed
     1-minute bars so far: a trigger is decided at the pass after its bar completes, against the session's opening
     equity and the book at that moment (holdings at their open marks + the session's earlier entries as the
     governor reserved them); a trigger refused for budget is not retried later in the session.
  6. fills: entries are marketable orders at that pass (the source filled at max(trigger, bar open) + 10 bps; the
     short at the next bar's open); the stop is engine-held and exits at the pass whose mark trades through it (the
     source: min(open, stop) on the minute bar); fees are the venue's (the source: 1 bp + 10 bps slippage).
  7. the scale is decided on the 15:45 ET price (the source read the close it sold at) and sold market-on-close.
  8. the trail is decided after the close on the official daily bar; its exit routes at the next session's first
     pass (the source: at the open).
  9. the short's moving-average target is engine-held, refreshed each session, and covers the whole position when
     the mark reaches it (the source settled it at the end of the day, after that close's scale, at min(open, target)).
 10. cadence: a pass every 60 s — the pre-market screen (once the genome cache carries the last session), every
     minute of the session, the trail after the close (the source was a batch backtest).

Not a duplicate of femto_qullamaggie / femto_qullamaggie_paper: those run Agentic-Trading-Desk's qulla_sleeve
engine (a different, earlier implementation) on 20 mega-caps, long breakouts only."""
import math
import os

import pandas as pd

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import qm_inputs as Q
from ...util import et_date
from ...vendor.qullamaggie_pass3 import desk_fixed as E

HERE = os.path.dirname(os.path.abspath(__file__))
GENOME_FILE = os.path.join(HERE, "..", "..", "vendor", "universes", "old_desk", "genome_universe_1838.txt")
UNIVERSE = tuple(dict.fromkeys(l.strip().upper() for l in open(GENOME_FILE) if l.strip() and not l.startswith("#")))
SOURCE = {"repo": "qullamaggie-research-pass3", "ref": "main", "commit": "00f8d0a206663054659f1e81afa72ba33ecfb7a3",
          "path": "inferred_rules.md", "blob_sha": "82074098606147ca2d36c915feab4e1aed913a4e",
          "implementation": {"repo": "midna", "ref": "main", "commit": "7969b5229c46403a92290d16da23228e59e7b064",
                             "path": "workspace/qualla_desk/pass3/desk_fixed.py",
                             "blob_sha": "6df5d6cbd67acf577065a71fe1f66483347e8b2d"}}
SETUP_OF = {"qm_leader_breakout_pass3": "breakout", "qm_episodic_pivot": "episodic_pivot",
            "qm_parabolic_short": "parabolic_short"}
CFG = E.load_config(None)
PROXY = CFG["market_proxy"]
OR_MIN = int(CFG["opening_range_minutes"])
EP_EARLIEST = 20                     # build_proposals: _intraday_trigger(..., earliest_minute=20) for the EP
DAILY_N = 140
DAILY_COLS = ["date", "symbol", "open", "high", "low", "close", "volume"]
INTRADAY_COLS = ["date", "symbol", "minute_from_open", "open", "high", "low", "close", "volume"]
EVENT_COLS = ["date", "symbol", "event_type", "news_verified", "event_minute"]
UNIVERSE_COLS = ["symbol", "sector", "market_cap", "borrowable"]
ENTRY_WINDOW_S = 900
STALE_RETRY_S = 900
SCALE_FROM_S, SCALE_UNTIL_S = 15 * 60, 10 * 60     # 15:45-15:50 ET: before the closing-auction cutoff
EOD_LAST_CHANCE_S = 200 * 60                       # trail with what is in by close + 200 min

_MEMO = {"session": None}


def reset():
    """drop the shared session memo (tests; a process restart does the same)."""
    _MEMO.clear()
    _MEMO["session"] = None


# -- frames (the source's layouts) -----------------------------------------------------------------------------------
def frame_from_bars(bars_by_sym, before, keep=DAILY_N, require_last=None):
    """the source's daily frame from engine bars: sessions < `before`, the last `keep` per name, positive prices
    (a name with a bad print is left out); `require_last`: names whose last row is not that session are left out."""
    rows = []
    for sym, bl in (bars_by_sym or {}).items():
        sub = [(et_date(b["t"]), b) for b in bl or []]
        sub = [(d, b) for d, b in sub if d < before][-keep:]
        if not sub or (require_last and sub[-1][0] != require_last):
            continue
        rs = [(d, sym, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0.0))
              for d, b in sub]
        if any(min(r[2:6]) <= 0 or r[6] < 0 for r in rs):
            continue
        rows += rs
    df = pd.DataFrame(rows, columns=DAILY_COLS)
    return df.sort_values(["date", "symbol"]).reset_index(drop=True)


def tape_frame(bars1m, sym, session):
    """today's completed regular-session minute bars in the source's intraday layout (minute 0 = 09:30 ET); gaps are
    left as they are (the source's _validate_minute_bars fails such a tape closed)."""
    o, c = cal.session_open(session), cal.session_close(session)
    rows = []
    for b in bars1m or []:
        t = float(b["t"])
        if o <= t < c:
            rows.append((session, sym, int((t - o) // 60), float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]),
                         float(b.get("v") or 0.0)))
    if not rows:
        return None
    x = pd.DataFrame(sorted(rows, key=lambda r: r[2]), columns=INTRADAY_COLS)
    return x.drop_duplicates("minute_from_open", keep="last").reset_index(drop=True)


def session_rows(tapes, session):
    """a session row per taped name (the DataStewardAgent wants the session; features fence to dates < it)."""
    return pd.DataFrame([(session, s, float(x.open.iloc[0]), float(x.high.max()), float(x.low.min()),
                          float(x.close.iloc[-1]), float(x.volume.sum())) for s, x in tapes.items()],
                        columns=DAILY_COLS)


def long_allowed(state, cfg=CFG):
    """build_proposals: longs in risk_on (market_filter hard), risk_on or caution when scaled."""
    if cfg.get("market_filter") == "scaled":
        return state in {"risk_on", "caution"}
    return state == "risk_on"


def screen(frame, session, cfg=CFG):
    """the session's point-in-time screen over the frame (dates < session): market state, leader ranks and the
    source's stock features per name — exactly what build_proposals computes before it reads a minute."""
    histories = E.daily_histories(frame, session)
    rank_h = {s: h for s, h in histories.items() if s != cfg["market_proxy"]}
    ranks = E.leader_scores(E.point_in_time_returns(rank_h))
    state, mas = E.market_state(frame, session, cfg["market_proxy"])
    feats = {s: E.stock_features(h, cfg) for s, h in rank_h.items()}
    closes = {s: h.close.astype(float).tolist()[-25:] for s, h in histories.items()}
    return {"state": state, "mas": mas, "ranks": ranks, "features": feats, "closes": closes}


def breakout_watch(sc, cfg=CFG):
    """names whose completed sessions satisfy build_proposals' breakout prefilter (risk-on, $5M ADV, leader,
    structure) — the only names the scan can propose a breakout for this session: {sym: pivot}."""
    if not long_allowed(sc["state"], cfg):
        return {}
    out = {}
    for s, f in sorted(sc["features"].items()):
        if not f.get("ready") or f["adv20"] < cfg["min_average_dollar_volume"]:
            continue
        if sc["ranks"].get(s, (0.0, 0))[0] < cfg["leader_percentile"]:
            continue
        if (f["prior_impulse"] >= cfg["prior_impulse_min_pct"] and f["base_tightness"] <= cfg["base_range_max_pct"]
                and f["tightening_ratio"] <= cfg["tightening_ratio_max"]
                and f["higher_low_slope"] >= cfg["higher_low_slope_min"] and f["ma_support"] >= 0.70
                and f["sma10_rising"] and f["sma20_rising"]):
            out[s] = float(f["pivot"])
    return out


def ep_pool(sc, cfg=CFG):
    """names an episodic pivot can come from this session (risk-on, $5M ADV, quiet 126-session tape)."""
    if not long_allowed(sc["state"], cfg):
        return []
    return sorted(s for s, f in sc["features"].items() if f.get("ready")
                  and f["adv20"] >= cfg["min_average_dollar_volume"] and f["ret126"] <= cfg["ep_quiet_126d_max_return"])


def ep_opening_ok(x, f, last_close, cfg=CFG):
    """the EP's opening conditions, fixed once minute 19 has printed: gap >= 10% and first-20-minute volume >=
    0.5x the 20-day average (build_proposals' gap_pct / ep_volume, verbatim)."""
    gap_pct = float(x.open.iloc[0]) / float(last_close) - 1
    first20_vol = float(x[x.minute_from_open < 20].volume.sum())
    adv_shares = f["avg_vol20"]
    ep_volume = first20_vol / adv_shares if adv_shares > 0 else 0
    return gap_pct >= cfg["ep_min_gap_pct"] and ep_volume >= cfg["ep_min_first20_adv"]


def short_candidates(sc, cfg=CFG):
    """names a parabolic short can come from (before the market cap picks the run threshold)."""
    lo = min(cfg["parabolic_small_cap_runup_pct"], cfg["parabolic_large_cap_runup_pct"])
    return sorted(s for s, f in sc["features"].items() if f.get("ready")
                  and f["adv20"] >= cfg["min_average_dollar_volume"]
                  and f["consecutive_up_days"] >= cfg["parabolic_up_days_min"] and f["three_day_runup"] >= lo)


def short_ok(f, mcap, cfg=CFG):
    """build_proposals' parabolic structure for a known market cap (borrow supplied by the venue: divergence 4)."""
    small = math.isfinite(mcap) and mcap <= cfg["parabolic_small_cap_threshold"]
    required = cfg["parabolic_small_cap_runup_pct"] if small else cfg["parabolic_large_cap_runup_pct"]
    return (math.isfinite(mcap) and f["consecutive_up_days"] >= cfg["parabolic_up_days_min"]
            and f["three_day_runup"] >= required)


def triggered(setup, x, sym, session, pivot=None):
    """the vendored _intraday_trigger with the scan's own arguments for the setup (None until it fires)."""
    if setup == "breakout":
        return E._intraday_trigger(x, sym, session, OR_MIN, 1, pivot)
    if setup == "episodic_pivot":
        return E._intraday_trigger(x, sym, session, OR_MIN, 1, earliest_minute=EP_EARLIEST)
    return E._intraday_trigger(x, sym, session, OR_MIN, -1)


def ma_target(closes):
    """_prior_parabolic_target on the completed closes before the session: max(10-day, 20-day SMA), None < 20."""
    if len(closes) < 20:
        return None
    return max(E.sma(closes, 10), E.sma(closes, 20))


def friction(entry, cfg=CFG):
    return entry * 2 * (float(cfg["slippage_bps"]) + float(cfg["commission_bps"])) / 10_000


def occupied_row(sym, qty, entry, stop, gap_pct, sector, mark, cfg=CFG):
    """the backtest's occupied row: notional at the open mark, risk = qty x (|entry - stop| + gap buffer/share +
    round-trip friction), the gap buffer = the proposal's gap_buffer_pct x the entry fill."""
    q = abs(float(qty))
    return {"symbol": sym, "notional": q * float(mark), "sector": sector or "UNKNOWN",
            "risk": q * (abs(float(entry) - float(stop)) + float(gap_pct or 0.0) * float(entry) + friction(float(entry), cfg))}


def trail_exit(hist, side, held, cfg=CFG):
    """the backtest's end-of-day trail on a name's daily frame through the session (None when it does not apply):
    True = a close under the 10-day SMA (the 20-day when extended > 1.5 ATR above the 10-day, longs) with held >= 3."""
    if len(hist) < 20:
        return None
    close = float(hist.close.iloc[-1])
    c = hist.close.astype(float).to_numpy()
    ma10, ma20 = E.sma(c, 10), E.sma(c, 20)
    atr_abs = float(E.stock_features(hist.iloc[:-1], cfg).get("atr_pct", 0.0)) * close if len(hist) > 128 else 0
    extended = (side == 1 and close - ma10 > cfg["extension_threshold_atr"] * max(atr_abs, 0.01))
    trail_ma = int(cfg["trail_extended_ma"] if extended else cfg["trail_default_ma"])
    ma = ma20 if trail_ma == 20 else ma10
    return bool(held >= 3 and side * (close - ma) < 0)


def scale_qty(qty, cfg=CFG):
    return max(1, int(math.floor(abs(float(qty)) * float(cfg["scale_fraction"]))))


def sessions_held(entry_session, session):
    """the backtest's held = day_index - entry_index + 1 (the entry session counts as 1)."""
    return cal.trading_days_between(entry_session, session) + 1


# -- the sleeves -------------------------------------------------------------------------------------------------------
class QullaSetup(Sleeve):
    def __init__(self, sleeve_id, universe=None):
        self.setup = SETUP_OF[sleeve_id]
        self.cfg = dict(CFG, setup_precedence=[self.setup])
        self.universe = tuple(universe or UNIVERSE)
        feeds = ["qm_listing", "qm_meta"] + (["qm_events"] if self.setup == "episodic_pivot" else [])
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="qullamaggie", cadence_s=60,
            schedule="premarket,rth,after_close+15:after_close+240", universe=self.universe,
            capital=float(CFG["initial_cash"]),
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": DAILY_N, "cache_only": True,
                             "symbols_for": "screen", "key": "genome"},
                            {"source": "equity_split", "interval": "1d", "n": 300, "symbols_for": "eod"},
                            {"source": "yahoo", "interval": "1m", "n": 400, "symbols_for": "tape"}],
                   "quotes": {"source": "equity"}, "feeds": feeds},
            params={"setup": self.setup, "setup_precedence": [self.setup], "config": "desk_fixed.DEFAULTS"},
            source=SOURCE)
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
        return sorted(i.split(":", 1)[1] for i in ((book.positions if book is not None else {}) or {})
                      if i.startswith("EQ:"))

    # -- what the engine fetches -----------------------------------------------------------------------------------
    def universe_now(self, now, book=None):
        return list(self.universe)

    def bar_symbols(self, need, now, book=None):
        kind = need.get("symbols_for")
        session = et_date(now)
        if not cal.is_trading_day(session):
            return []
        close = cal.session_close(session)
        if kind == "screen":
            if now >= close or _MEMO.get("session") == session:
                return []
            if _MEMO.get("pending") == session and now - float(_MEMO.get("tried_at") or 0) < STALE_RETRY_S:
                return []
            return list(self.universe)
        if kind == "eod":
            if now < close or (self._state().get("eod") or {}).get("session") == session:
                return []
            return self._book_syms(book)
        if kind == "tape":
            if not cal.is_rth(now):
                return []
            return self.tape_names(self._state(), session, now)
        return []

    def quote_universe(self, now, book=None):
        return self._book_syms(book) if cal.is_rth(now) else []

    def tape_names(self, st, session, now):
        """the names whose minute tape the scan needs this pass: the session's undecided watch names (the EP's
        candidates once minute 20 has printed)."""
        w = st.get("watch") or {}
        if w.get("session") != session:
            return []
        day = st.get("day") or {}
        decided = set((day.get("decided") or {}) if day.get("session") == session else ())
        minute = int((now - cal.session_open(session)) // 60)
        if self.setup == "episodic_pivot":
            if minute < EP_EARLIEST:
                return []
            evs = set(w.get("event_syms") or [])
            checked = (day.get("ep_checked") or {}) if day.get("session") == session else {}
            names = [s for s in w.get("pool") or [] if s in evs and checked.get(s) is not False]
        else:
            names = list(w.get("names") or [])
        return sorted(s for s in names if s not in decided)

    def meta_symbols(self, now):
        """(names that need a sector, names that need a share count) for the meta feed."""
        st = self._state()
        w = st.get("watch") or {}
        names = set(w.get("names") or []) | set((st.get("pos") or {}))
        if self.setup == "episodic_pivot":
            names |= set(s for s in w.get("pool") or [] if s in set(w.get("event_syms") or []))
        shares = set(w.get("short_candidates") or []) if self.setup == "parabolic_short" else set()
        return sorted(names | shares), shares

    # -- the pass ------------------------------------------------------------------------------------------------------
    def signal(self, view):
        now, session = float(view.now), view.session
        st = {k: v for k, v in (view.state or {}).items()}
        out = []
        self._st = st
        if not cal.is_trading_day(session):
            return out
        extra = view.extra or {}
        memo = _memo_for(session, extra.get("bars_genome"), extra.get("qm_listing"), now)
        held = self._held(view)
        self._sync_pos(st, held, session)
        out += self._scale_book(st, held, session)
        o, c = cal.session_open(session), cal.session_close(session)
        if memo is not None and (st.get("watch") or {}).get("session") != session:
            st["watch"] = self._screen(memo, session)
            w = st["watch"]
            out.append(Intent("signal", PROXY, reason=f"{self.CONFIG.sleeve_id} screen {session}: market "
                              f"{w['market_state']}; watch {w.get('names') or w.get('pool_n') or []}"[:300],
                              meta={"market_state": w["market_state"], "names": w.get("names"),
                                    "pool": len(w.get("pool") or []), "candidates": w.get("short_candidates")},
                              signal_key=f"qm:{self.CONFIG.sleeve_id}:{session}:screen"))
        if (st.get("watch") or {}).get("session") == session:
            self._refresh_watch(st, extra, memo, session)
        if o <= now < c:
            out += self._open_pass(view, st, memo, held)
            out += self._entries(view, st, memo, held)
            if c - SCALE_FROM_S <= now < c - SCALE_UNTIL_S:
                out += self._scale(view, st, memo, held)
        elif now >= c:
            out += self._after_close(view, st, held)
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})

    # -- book ---------------------------------------------------------------------------------------------------------
    def _held(self, view):
        exiting = {p["inst"].split(":", 1)[1] for p in (view.extra or {}).get("pending_orders", [])
                   if p["action"] == "exit"}
        out = {}
        for inst, p in (view.positions or {}).items():
            if not inst.startswith("EQ:") or abs(float(p["qty"])) <= 1e-12:
                continue
            sym = inst.split(":", 1)[1]
            m = p.get("meta") or {}
            out[sym] = {"qty": float(p["qty"]), "avg": float(p["avg"]), "opened_at": float(p.get("opened_at") or 0),
                        "stop": m.get("stop"), "pm": m.get("position_meta") or {}, "mark": p.get("mark"),
                        "exiting": sym in exiting}
        return out

    @staticmethod
    def _sync_pos(st, held, session):
        pos = st.setdefault("pos", {})
        for s in list(pos):
            if s not in held:
                pos.pop(s)
        for s, h in held.items():
            rec = pos.setdefault(s, {})
            if rec.get("opened_at") != h["opened_at"]:
                rec.clear()
                rec.update(opened_at=h["opened_at"], entry_session=et_date(h["opened_at"]) if h["opened_at"] else session)

    # -- screen --------------------------------------------------------------------------------------------------------
    def _screen(self, memo, session):
        sc = memo["screen"]
        w = {"session": session, "market_state": sc["state"], "built_at": memo.get("built_at")}
        if self.setup == "breakout":
            piv = breakout_watch(sc, self.cfg)
            w["names"], w["pivots"] = sorted(piv), piv
        elif self.setup == "episodic_pivot":
            w["pool"] = ep_pool(sc, self.cfg)
            w["pool_n"] = len(w["pool"])
            w["names"], w["event_syms"] = [], []
        else:
            w["short_candidates"] = short_candidates(sc, self.cfg)
            w["names"], w["mcap"] = [], {}
        return w

    def _refresh_watch(self, st, extra, memo, session):
        w = st["watch"]
        if self.setup == "episodic_pivot":
            evs = [e for e in (extra.get("qm_events") or []) if e.get("date") == session]
            pool = set(w.get("pool") or [])
            w["event_syms"] = sorted({e["symbol"] for e in evs if e["symbol"] in pool})
            w["events"] = [{k: e[k] for k in EVENT_COLS} for e in evs if e["symbol"] in pool]
        elif self.setup == "parabolic_short" and memo is not None:
            meta = extra.get("qm_meta") or {}
            names, mcaps = [], dict(w.get("mcap") or {})
            for s in w.get("short_candidates") or []:
                sh = (meta.get(s) or {}).get("shares")
                if sh and s not in mcaps:
                    mcaps[s] = float(sh) * float(memo["screen"]["closes"][s][-1])
                f = memo["screen"]["features"].get(s) or {}
                if s in mcaps and f.get("ready") and short_ok(f, mcaps[s], self.cfg):
                    names.append(s)
            w["mcap"], w["names"] = mcaps, names
        sec = dict(w.get("sector") or {})
        for s, m in (extra.get("qm_meta") or {}).items():
            if m.get("sector"):
                sec[s] = m["sector"]
        w["sector"] = sec

    # -- the session's open --------------------------------------------------------------------------------------------
    def _open_pass(self, view, st, memo, held):
        session = view.session
        if (st.get("day") or {}).get("session") == session:
            return []
        marks = {}
        for s, h in held.items():
            q = (view.quotes or {}).get(s) or {}
            px = q.get("day_open") if q.get("day_date") in (None, session) else None
            marks[s] = float(px or h["mark"] or h["avg"])
        equity = float(view.cash) + sum(h["qty"] * marks[s] for s, h in held.items())
        pend = st.get("pending_exits") or {}
        queued = [s for s in (pend.get("syms") or []) if pend.get("session") == session and s in held]
        st["day"] = {"session": session, "equity": equity, "marks": marks, "decided": {}, "entries": {},
                     "ep_checked": {}, "exiting": queued}
        out = []
        for s in queued:
            if held[s]["exiting"]:
                continue
            out.append(Intent("exit", s, side="long" if held[s]["qty"] > 0 else "short",
                              signal_key=f"qm:{self.setup}:{session}:{s}:trail",
                              reason=f"{self.CONFIG.sleeve_id} close_below_trailing_MA: queued at the close, sold at "
                                     f"the open"))
        if self.setup == "parabolic_short" and memo is not None:
            for s, h in held.items():
                if h["qty"] < 0 and s not in queued:
                    tgt = ma_target(memo["screen"]["closes"].get(s) or [])
                    if tgt is not None:
                        out.append(Intent("adjust", s, side="short", target=float(tgt),
                                          reason=f"{self.CONFIG.sleeve_id} parabolic_MA_target {tgt:.4f} for {session}"))
        return out

    # -- entries ---------------------------------------------------------------------------------------------------------
    def _entries(self, view, st, memo, held):
        session, now = view.session, float(view.now)
        day, w = st.get("day") or {}, st.get("watch") or {}
        minute = int((now - cal.session_open(session)) // 60)
        if memo is None or day.get("session") != session or w.get("session") != session or minute < OR_MIN:
            return []
        b1 = (view.bars or {}).get("1m") or {}
        tapes = {}
        for s in self.tape_names(st, session, now):
            x = tape_frame(b1.get(s), s, session)
            if x is None:
                continue
            if self.setup == "episodic_pivot" and s not in day["ep_checked"]:
                last = (x.minute_from_open.astype(int) >= EP_EARLIEST - 1).any()
                if not last:
                    continue                              # minute 19 not in yet: the opening read is incomplete
                f = memo["screen"]["features"].get(s) or {}
                day["ep_checked"][s] = bool(ep_opening_ok(x, f, memo["screen"]["closes"][s][-1], self.cfg))
                if not day["ep_checked"][s]:
                    day["decided"][s] = {"minute": minute, "entered": False, "why": "gap / first-20 volume"}
                    continue
            tapes[s] = x
        fresh = {s: x for s, x in tapes.items()
                 if triggered(self.setup, x, s, session, (w.get("pivots") or {}).get(s)) is not None}
        if not fresh:
            return []
        props, audit = self._scan(view, st, memo, fresh, held)
        out = []
        for s in fresh:
            day["decided"][s] = {"minute": minute, "entered": False, "why": audit.get(s, "no proposal")}
        n_pos = sum(1 for s, h in held.items() if not h["exiting"])
        pend = {p["inst"].split(":", 1)[1] for p in (view.extra or {}).get("pending_orders", [])
                if p["action"] == "enter" and p["inst"].startswith("EQ:")}
        n_pos += sum(1 for s in pend if s not in held)
        gross = sum(abs(h["qty"]) * float(day["marks"].get(s) or (day["entries"].get(s) or {}).get("open")
                                          or h["mark"] or h["avg"]) for s, h in held.items() if not h["exiting"])
        gross += sum(float(r["qty"]) * float(r["open"]) for s, r in day["entries"].items() if s in pend and s not in held)
        max_pos = min(int(self.cfg["max_open_positions"]), int(self.cfg["max_positions_hard"]))
        equity = float(day["equity"])
        for p in props:                                    # the governor's order (score, descending)
            if n_pos >= max_pos:
                break
            if p.symbol in held or p.symbol in pend:
                continue
            if gross + p.notional > max(equity, 1) * float(self.cfg["max_gross_exposure_pct"]):
                continue
            side = "long" if int(p.side) == 1 else "short"
            tgt = ma_target(memo["screen"]["closes"].get(p.symbol) or []) if side == "short" else None
            out.append(Intent(
                "enter", p.symbol, side=side, qty=float(p.quantity), stop=float(p.stop),
                target=float(tgt) if tgt is not None else None, order=OrderSpec(window_s=ENTRY_WINDOW_S),
                signal_key=f"qm:{self.setup}:{session}:{p.symbol}",
                reason=(f"{self.CONFIG.sleeve_id} {p.setup} {p.trigger_time}: entry {p.entry} stop {p.stop}, "
                        f"qty {p.quantity}, score {p.score:.3f}; " + "; ".join(p.reasons[:2]))[:300],
                meta={"position_meta": {"setup": p.setup, "sector": p.sector, "gap_buffer_pct": float(p.gap_buffer_pct),
                                        "stressed_loss_per_share": float(p.stressed_loss_per_share),
                                        "entry_ref": float(p.entry), "stop": float(p.stop), "score": float(p.score),
                                        "trigger_time": p.trigger_time, "market_state": p.market_state,
                                        "session": session}}))
            x = fresh[p.symbol]
            day["entries"][p.symbol] = {"symbol": p.symbol, "notional": float(p.notional), "sector": p.sector,
                                        "risk": float(p.quantity) * float(p.stressed_loss_per_share),
                                        "qty": float(p.quantity), "open": float(x.open.iloc[0])}
            day["decided"][p.symbol].update(entered=True, why="accepted")
            n_pos += 1
            gross += float(p.quantity) * float(x.open.iloc[0])
        for s in fresh:
            d = day["decided"][s]
            out.append(Intent("signal", s, reason=f"{self.CONFIG.sleeve_id} trigger {s} minute {minute}: "
                              f"{'entered' if d['entered'] else d['why']}"[:300],
                              signal_key=f"qm:{self.CONFIG.sleeve_id}:{session}:{s}:decided", meta=dict(d)))
        return out

    def _scan(self, view, st, memo, fresh, held):
        """AgenticResearchDesk.scan (the source) on this pass's triggered tapes. Returns (accepted, audit)."""
        session = view.session
        day, w = st["day"], st["watch"]
        if self.setup == "breakout":                       # leader ranks read the whole frame
            base = memo["frame"]
        else:                                              # EP / short read no rank: their names + the proxy suffice
            base = memo["frame"][memo["frame"].symbol.isin(list(fresh) + [PROXY])]
        daily = pd.concat([base, session_rows(fresh, session)], ignore_index=True)
        daily = daily.sort_values(["date", "symbol"]).reset_index(drop=True)
        intraday = pd.concat(list(fresh.values()), ignore_index=True)
        events = pd.DataFrame(w.get("events") or [], columns=EVENT_COLS) if self.setup == "episodic_pivot" \
            else pd.DataFrame(columns=EVENT_COLS)
        sectors = w.get("sector") or {}
        mcaps = w.get("mcap") or {}
        universe = pd.DataFrame([{"symbol": s, "sector": sectors.get(s, "UNKNOWN"),
                                  "market_cap": float(mcaps.get(s, float("nan"))), "borrowable": True} for s in fresh],
                                columns=UNIVERSE_COLS)
        occupied = []
        for s, h in held.items():
            if h["exiting"] or s in day["entries"]:
                continue
            pm = h["pm"]
            stop = h["stop"] if h["stop"] is not None else pm.get("stop", h["avg"])
            occupied.append(occupied_row(s, h["qty"], h["avg"], stop, pm.get("gap_buffer_pct"), pm.get("sector"),
                                         day["marks"].get(s) or h["mark"] or h["avg"], self.cfg))
        occupied += [{k: r[k] for k in ("symbol", "notional", "sector", "risk")} for r in day["entries"].values()]
        try:
            accepted, audit, _trace = E.AgenticResearchDesk(self.cfg).scan(
                session, daily, intraday, events, universe, max(float(day["equity"]), 1.0), occupied)
        except ValueError as e:
            return [], {s: f"scan error: {str(e)[:120]}" for s in fresh}
        return [p for p in accepted if p.setup == self.setup], audit

    # -- the close -------------------------------------------------------------------------------------------------------
    def _scale(self, view, st, memo, held):
        session = view.session
        out = []
        for s, h in held.items():
            ps = st["pos"].get(s) or {}
            if h["exiting"] or ps.get("scaled") or (ps.get("scale_sent") or {}).get("session") == session:
                continue
            if s in ((st.get("day") or {}).get("exiting") or []):
                continue
            n_hist = len((memo or {}).get("screen", {}).get("closes", {}).get(s) or []) + 1 if memo else 20
            if n_hist < 20:
                continue
            q = (view.quotes or {}).get(s) or {}
            px = q.get("last") or h["mark"]
            if not px:
                continue
            side = 1 if h["qty"] > 0 else -1
            held_n = sessions_held(ps.get("entry_session") or session, session)
            if held_n >= int(self.cfg["scale_days"]) and side * (float(px) - h["avg"]) > 0:
                trim = scale_qty(h["qty"], self.cfg)
                out.append(Intent("exit", s, side="long" if side == 1 else "short", qty=float(trim),
                                  order=OrderSpec(type="market", tif="cls"),
                                  signal_key=f"qm:{self.setup}:{session}:{s}:scale",
                                  reason=f"{self.CONFIG.sleeve_id} scale_after_strength: {trim} of {abs(h['qty']):g} "
                                         f"at the close, held {held_n} sessions, {float(px):.2f} vs entry "
                                         f"{h['avg']:.2f}; residual stop -> breakeven"))
                st["pos"].setdefault(s, {})["scale_sent"] = {"session": session, "qty": abs(h["qty"])}
        return out

    def _scale_book(self, st, held, session):
        """a scale sale that filled (the position shrank) commits the third and moves the residual stop to breakeven
        (the backtest: stop = max(stop, entry) for longs, min for shorts — the engine's ratchet); a market-on-close
        sale still unfilled when the next session starts is dropped (the third stays unsold)."""
        out = []
        for s, ps in st["pos"].items():
            sent = ps.get("scale_sent")
            if not sent:
                continue
            h = held.get(s)
            if h is not None and abs(h["qty"]) < float(sent["qty"]) - 1e-9:
                ps["scaled"] = True
                ps.pop("scale_sent", None)
                out.append(Intent("adjust", s, side="long" if h["qty"] > 0 else "short", stop=float(h["avg"]),
                                  meta={"ratchet": True},
                                  reason=f"{self.CONFIG.sleeve_id} scaled 1/3 at the close: stop -> breakeven "
                                         f"{h['avg']:.4f}"))
            elif sent.get("session") != session:
                ps.pop("scale_sent", None)
        return out

    def _after_close(self, view, st, held):
        session, now = view.session, float(view.now)
        out = []
        if (st.get("eod") or {}).get("session") == session:
            return out
        daily = (view.bars or {}).get("1d") or {}
        frames = {}
        for s in held:
            f = frame_from_bars({s: daily.get(s) or []}, cal.next_trading_day(session).isoformat(), keep=300)
            frames[s] = f
        complete = all(len(f) and f.date.iloc[-1] == session for f in frames.values())
        if not complete and now < cal.session_close(session) + EOD_LAST_CHANCE_S:
            return out
        pend = []
        for s, h in held.items():
            f = frames[s]
            if not len(f) or f.date.iloc[-1] != session:
                continue
            ps = st["pos"].get(s) or {}
            r = trail_exit(f, 1 if h["qty"] > 0 else -1, sessions_held(ps.get("entry_session") or session, session),
                           self.cfg)
            if r:
                pend.append(s)
        st["pending_exits"] = {"session": cal.next_trading_day(session).isoformat(), "syms": pend}
        st["eod"] = {"session": session, "trail": pend}
        if pend:
            out.append(Intent("signal", pend[0], reason=f"{self.CONFIG.sleeve_id} trail {session}: exit at the next "
                              f"open {pend}"[:300], signal_key=f"qm:{self.CONFIG.sleeve_id}:{session}:trail",
                              meta={"syms": pend}))
        return out


# -- the session memo (shared by the three sleeves; the screen reads the whole genome once a session) ----------------
def _memo_for(session, genome_bars, etf, now):
    if _MEMO.get("session") == session:
        return _MEMO
    if not genome_bars:
        return None
    last = cal.prev_trading_day(session).isoformat()
    proxy = [b for b in genome_bars.get(PROXY) or [] if et_date(b["t"]) < session]
    if not proxy or et_date(proxy[-1]["t"]) != last:          # the genome job has not written the last session yet
        _MEMO.update(pending=session, tried_at=now)
        return None
    skip = set(etf or ())
    bars = {s: b for s, b in genome_bars.items() if s == PROXY or s not in skip}
    frame = frame_from_bars(bars, session, DAILY_N, require_last=last)
    _MEMO.clear()
    _MEMO.update(session=session, frame=frame, screen=screen(frame, session), built_at=now,
                 n_names=int(frame.symbol.nunique()), n_etf_skipped=len(set(genome_bars) & skip))
    return _MEMO


# -- feeds -------------------------------------------------------------------------------------------------------------
def _root(feeds):
    return os.path.dirname(feeds.hub.cache.root) if getattr(feeds, "hub", None) is not None else "cache"


_REPORTS = {}


def _feed_events(feeds, sleeve, now, arg):
    d = Q.cache_dir(_root(feeds))
    cr = _REPORTS.get(d)
    if cr is None:
        cr = _REPORTS[d] = Q.CurrentReports(os.path.join(d, "edgar_current.json"))
    cr.refresh(now)
    return cr.events(et_date(now), Q.tickers_by_cik(d, now), set(getattr(sleeve, "universe", None) or UNIVERSE))


def _feed_meta(feeds, sleeve, now, arg):
    syms, share_syms = sleeve.meta_symbols(now) if hasattr(sleeve, "meta_symbols") else ([], set())
    if not syms:
        return {}
    d = Q.cache_dir(_root(feeds))
    inv = Q.ciks_by_ticker(Q.tickers_by_cik(d, now))
    budget = [Q.MAX_LOOKUPS]
    out = {}
    for s in syms:
        cik = inv.get(Q.norm(s))
        if not cik:
            continue
        p = Q.profile(d, cik, now, budget=budget) or {}
        rec = {"cik": cik, "sector": p.get("sector")}
        if s in share_syms:
            rec["shares"] = (Q.shares(d, cik, now, budget=budget) or {}).get("shares")
        out[s] = rec
    return out


def _feed_listing(feeds, sleeve, now, arg):
    return Q.listing(Q.cache_dir(_root(feeds)), now)


FEEDS = {"qm_events": _feed_events, "qm_meta": (_feed_meta, {"per_sleeve": True}), "qm_listing": _feed_listing}


def sleeves():
    return [QullaSetup(sid) for sid in ("qm_leader_breakout_pass3", "qm_episodic_pivot", "qm_parabolic_short")]
