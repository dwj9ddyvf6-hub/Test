"""Griffith / Ledge intraday sleeves: the auditable 20/50 trend agent (app.py TrendAgent), the legacy agentic setups
(agentic_runtime.py SetupAgents: momentum_breakout / vwap_pullback / gap_continuation) and ORB20 (the R4 lab's
registered opening-range candidate). agentic-trading-desk main @4c8c179c; the source modules cannot be imported here
(app.py builds its desk — config, sqlite — at import), so their decision functions are ported line for line below and
proven against the source run in its own tree (tools/parity/griffith_intraday.py).

griffith_auditable_20_50_trend — TrendAgent.proposals every 15 minutes (refresh_seconds 900) on SPY's last 50 IEX
  5-minute bars: a new newest bar only (de-duplicated), nothing while an order is working; SMA20 > SMA50 x 1.001 and
  flat -> buy round($100 / price, 6) shares; SMA20 < SMA50 and long -> sell the held quantity; day limit at price x
  (1 +/- 0.001). A data-host error skips the bar (a DATA_HOST blocker; the next try one cadence later, EQ-08).
griffith_momentum_breakout / griffith_vwap_pullback / griffith_gap_continuation — one agentic cycle every 15 minutes:
  IEX snapshots of SPY / QQQ / IWM + the SCOPE radar (the top 100 names of the persistent candidate states the
  three-strategy funnel writes: PX_1_3_0_CHALLENGER / LR_1_1_0_CORRECTED / LF_2_1_0_CORRECTED decisions, BUY / SETUP /
  WATCH = RADAR) + held names; broad_scan (price 5..1000, spread <= 0.6%, score = 0.8|gap| + |intraday| +
  min(rvol, 5) + log10($ volume)/3), the 15 leaders' Alpaca news scored by the ResearchEngine (sentiment words +
  0.5 x catalyst words), the 8 best decided on their last 200 IEX 1-minute bars by the ordered if/elif chain
  (momentum_breakout, else vwap_pullback, else gap_continuation; anti-chase AVOID; BUY at setup score >= 5 outside a
  risk_off regime). Each sleeve buys its own setup's BUYs in the premarket / regular session: $100 (target_notional),
  round(100 / price, 6) shares, day limit at price x 1.001; at most 30 positions, never a held or working name.
  Exits: the GTC OCO the runtime restores on every unprotected long — stop 1.5% below / target 3% above the entry.

Gone under the cutover doctrine: the RiskGate (kill switch, SPY-only allowlist, $5,000 order cap, buying power,
daily loss, 50% gross / 8% symbol exposure, signal age); the Tensor 5-minute execution authority (a chart gate);
the desk switch legacy_intraday_execution=false that disabled the three setups; new-entry admission.
Named divergences: completed bars only (the source's newest IEX bar could still be forming); premarket orders wait
for the regular open (the engine does not route extended-hours equity orders); the OCO legs are engine stop /
target rules on the mark; the scan universe omits other strategies' armed handoffs and holdings (each sleeve's own
book); positions are counted per sleeve; without Alpaca keys the inputs are Yahoo (no bid/ask, so the spread filter
cannot be evaluated and passes) and Yahoo Finance RSS headlines."""
import math
from dataclasses import asdict, dataclass
from datetime import datetime, time as wall_time, timezone

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import griffith as tape
from ...feedlib import griffith_intraday as src
from ...util import ET, et_date
from ...venues.alpaca import BrokerError
from .griffith import FEED, SOURCE, ThreeStrategySleeve, source_config, vendored

AGENT = source_config()["agentic"]
TREND = source_config()["strategy"]
RISK = source_config()["risk"]
SCOPE = source_config()["three_strategy"]["scope"]
STRATEGY_VERSIONS = {"PARALLAX": "PX_1_3_0_CHALLENGER", "LEADERS_REST": "LR_1_1_0_CORRECTED",
                     "foliotend-location-first-swing": "LF_2_1_0_CORRECTED"}       # scope_runtime.STRATEGY_VERSIONS
LEGACY = {"griffith_momentum_breakout": "momentum_breakout", "griffith_vwap_pullback": "vwap_pullback",
          "griffith_gap_continuation": "gap_continuation"}
LEGACY_FEED = "griffith_legacy_cycle"
RUNTIME = dict(SOURCE, path="agentic_runtime.py", blob="4e7ce0427b329e955ca664d167a0bd937140389e", lines="251-287")
APP = dict(SOURCE, path="app.py", blob="4e359ca8ce17195830ec4e8c74d64a08686959ff", lines="308-348")


# -- agentic_runtime.py helpers, line for line -------------------------------------------------------------------
def mean(values):
    return sum(values) / len(values) if values else 0.0


def ema(values, period):
    if not values:
        return 0.0
    alpha = 2 / (period + 1)
    value = values[0]
    for current in values[1:]:
        value = alpha * current + (1 - alpha) * value
    return value


def rsi(values, period=14):
    if len(values) <= period:
        return 50.0
    changes = [values[i] - values[i - 1] for i in range(1, len(values))][-period:]
    gains = mean([max(change, 0) for change in changes])
    losses = mean([max(-change, 0) for change in changes])
    return 100.0 if losses == 0 else 100 - 100 / (1 + gains / losses)


def atr(bars, period=14):
    if len(bars) < 2:
        return 0.0
    ranges = []
    for previous, current in zip(bars[:-1], bars[1:]):
        ranges.append(max(float(current["h"]) - float(current["l"]), abs(float(current["h"]) - float(previous["c"])),
                          abs(float(current["l"]) - float(previous["c"]))))
    return mean(ranges[-period:])


def vwap(bars):
    weighted = sum(float(b.get("vw", b["c"]) if b.get("vw") is not None else b["c"]) * float(b.get("v", 0))
                   for b in bars)
    volume = sum(float(b.get("v", 0)) for b in bars)
    return weighted / volume if volume else float(bars[-1]["c"])


def session_name(ts):
    """agentic_runtime.session_name on the ET clock (weekends closed; the runtime's broker calendar for holidays)."""
    now = datetime.fromtimestamp(ts, tz=ET)
    clock = now.time()
    if now.weekday() >= 5 or not cal.is_trading_day(now.date()):
        return "closed"
    if wall_time(4, 0) <= clock < wall_time(9, 30):
        return "premarket"
    if wall_time(9, 30) <= clock < wall_time(16, 0):
        return "regular"
    if wall_time(16, 0) <= clock < wall_time(20, 0):
        return "afterhours"
    return "overnight"


@dataclass
class Candidate:
    symbol: str
    price: float
    score: float
    gap_percent: float
    intraday_percent: float
    relative_volume: float
    spread_percent: float
    dollar_volume: float
    technical: dict = None
    catalyst_score: float = 0.0
    headlines: list = None
    setup: str = None
    decision: str = "WAIT"
    thesis: str = ""
    market_timestamp: str = None


POSITIVE = {"beat", "raises", "raised", "approval", "contract", "growth", "record", "upgrade", "surge", "profit"}
NEGATIVE = {"miss", "cuts", "cut", "offering", "investigation", "downgrade", "loss", "recall", "bankruptcy", "lawsuit"}
CATALYST = {"earnings", "guidance", "fda", "merger", "acquisition", "contract", "offering", "upgrade", "downgrade",
            "sec"}


def analyze(news, symbols):
    """ResearchEngine.analyze."""
    result = {symbol: (0.0, []) for symbol in symbols}
    for item in news:
        headline = str(item.get("headline", ""))
        words = set(headline.lower().replace("-", " ").split())
        sentiment = len(words & POSITIVE) - len(words & NEGATIVE)
        catalyst = 1 if words & CATALYST else 0
        for symbol in item.get("symbols", []):
            if symbol not in result:
                continue
            score, headlines = result[symbol]
            result[symbol] = (score + sentiment + catalyst * 0.5, (headlines + [headline])[:5])
    return result


def decide(candidate, bars, regime):
    """SetupAgents.decide — the ordered if/elif chain."""
    closes = [float(bar["c"]) for bar in bars]
    highs = [float(bar["h"]) for bar in bars]
    lows = [float(bar["l"]) for bar in bars]
    technical = {"ema9": ema(closes[-30:], 9), "ema20": ema(closes[-60:], 20), "rsi14": rsi(closes),
                 "atr14": atr(bars), "vwap": vwap(bars), "range_high20": max(highs[-20:]),
                 "range_low20": min(lows[-20:])}
    candidate.technical = technical
    price = candidate.price
    setup_score = candidate.score + candidate.catalyst_score
    if price >= technical["range_high20"] * 0.999 and candidate.relative_volume >= 1.5 and technical["rsi14"] < 78:
        candidate.setup = "momentum_breakout"
        setup_score += 3
    elif technical["ema9"] > technical["ema20"] and abs(price - technical["vwap"]) / price < 0.004 \
            and technical["rsi14"] < 68:
        candidate.setup = "vwap_pullback"
        setup_score += 2
    elif candidate.gap_percent >= 2 and price > technical["vwap"] and technical["ema9"] > technical["ema20"]:
        candidate.setup = "gap_continuation"
        setup_score += 2
    else:
        candidate.setup = "none"
    anti_chase = price > technical["ema20"] + 2.5 * max(technical["atr14"], price * 0.002)
    if anti_chase:
        candidate.decision = "AVOID"
        candidate.thesis = "Price is extended beyond the anti-chase limit."
    elif candidate.setup != "none" and setup_score >= 5 and regime != "risk_off":
        candidate.decision = "BUY"
        candidate.thesis = f"{candidate.setup}; score {setup_score:.1f}; regime {regime}."
    else:
        candidate.decision = "WAIT"
        candidate.thesis = f"No approved high-confidence setup; score {setup_score:.1f}."
    return candidate


def fresh_snapshot_price(snap):
    """AgenticDesk._fresh_snapshot_price."""
    candidates = []
    for payload, field, priority in ((snap.get("minuteBar") or {}, "c", 1), (snap.get("latestQuote") or {}, "mid", 2),
                                     (snap.get("latestTrade") or {}, "p", 3)):
        raw_time = payload.get("t")
        try:
            observed = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00")).astimezone(timezone.utc)
            if field == "mid":
                bid, ask = float(payload.get("bp") or 0), float(payload.get("ap") or 0)
                value = (bid + ask) / 2 if bid > 0 and ask >= bid else float(ask or bid)
            else:
                value = float(payload.get(field) or 0)
            if value > 0:
                candidates.append((observed, priority, value, str(raw_time)))
        except (TypeError, ValueError):
            continue
    if candidates:
        _, _, price, stamp = max(candidates, key=lambda item: (item[0], item[1]))
        return price, stamp
    day = snap.get("dailyBar") or {}
    try:
        return float(day.get("c") or 0), str(day.get("t") or "") or None
    except (TypeError, ValueError):
        return 0.0, None


def broad_scan(snapshots, spread_known=True):
    """AgenticDesk.broad_scan (spread_known=False: a quote source without bid/ask — the filter cannot apply)."""
    out = []
    for symbol, snap in snapshots.items():
        day, previous = snap.get("dailyBar") or {}, snap.get("prevDailyBar") or {}
        quote = snap.get("latestQuote") or {}
        price, market_timestamp = fresh_snapshot_price(snap)
        previous_close = float(previous.get("c") or 0)
        if price <= 0 or previous_close <= 0:
            continue
        bid, ask = float(quote.get("bp") or 0), float(quote.get("ap") or 0)
        spread = ((ask - bid) / price * 100) if bid > 0 and ask >= bid else (99 if spread_known else 0.0)
        day_volume, previous_volume = float(day.get("v") or 0), float(previous.get("v") or 1)
        rel_volume = day_volume / max(previous_volume, 1)
        gap = (float(day.get("o") or price) / previous_close - 1) * 100
        intraday = (price / float(day.get("o") or price) - 1) * 100
        dollar_volume = day_volume * price
        if price < float(AGENT["min_price"]) or price > float(AGENT["max_price"]):
            continue
        if spread > float(AGENT["max_spread_percent"]):
            continue
        score = abs(gap) * 0.8 + abs(intraday) + min(rel_volume, 5) + math.log10(max(dollar_volume, 1)) / 3
        out.append(Candidate(symbol, price, score, gap, intraday, rel_volume, spread, dollar_volume,
                             market_timestamp=market_timestamp))
    return sorted(out, key=lambda item: item.score, reverse=True)


def market_regime(snapshots):
    signals = []
    for symbol in ("SPY", "QQQ", "IWM"):
        snap = snapshots.get(symbol, {})
        day, previous = snap.get("dailyBar") or {}, snap.get("prevDailyBar") or {}
        if day.get("c") and previous.get("c"):
            signals.append(float(day["c"]) / float(previous["c"]) - 1)
    average = mean(signals)
    return "risk_on" if average > 0.002 else "risk_off" if average < -0.006 else "neutral"


# -- the SCOPE funnel / radar (scope_runtime.funnel + watch_population) -------------------------------------------
def funnel(decisions, states, radar_max=100, armed_max=25, hands_max=12):
    """scope_runtime.funnel on the persistent candidate states {"SYM|STRATEGY": [tier, score]} (updated in place)."""
    radar_max = max(1, min(int(radar_max), 250))
    armed_max = max(1, min(int(armed_max), radar_max))
    hands_max = max(1, min(int(hands_max), armed_max))
    ranked = {}
    for item in decisions:
        if item.scannerVersion != STRATEGY_VERSIONS.get(item.strategyId):
            continue
        tier = "RADAR" if item.status in {"BUY", "SETUP", "WATCH"} else "DISCOVERY"
        score = float(item.score or 0)
        prior = ranked.get(item.symbol)
        if prior is None or score > prior[0]:
            ranked[item.symbol] = (score, tier, item.strategyId)
    radar = [s for s, v in sorted(ranked.items(), key=lambda x: (-x[1][0], x[0])) if v[1] == "RADAR"][:radar_max]
    armed = radar[:armed_max]
    hands = armed[:hands_max]
    for symbol, (score, tier, strategy) in ranked.items():
        final = "ACTIVE_HAND" if symbol in hands else "ARMED" if symbol in armed else "RADAR" if symbol in radar \
            else tier
        states[f"{symbol}|{strategy}"] = [final, score]
    return {"radar": radar, "armed": armed, "hands": hands}


def watch_population(states, limit=50):
    limit = max(1, min(int(limit), 250))
    best = {}
    for key, (tier, score) in states.items():
        if tier in ("RADAR", "ARMED", "ACTIVE_HAND"):
            sym = key.split("|", 1)[0]
            best[sym] = max(best.get(sym, -math.inf), float(score))
    return [s for s, _ in sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))][:limit]


def location_first_decisions(hub, bars, now):
    """the Location-First decisions the source's completing run made: the SCOPE run's final shard (its location watch
    in the aggressive paper lane), each on its last 200 IEX 15-minute bars and its last 15-minute close."""
    V = vendored()
    lf = V.strategy_system.LocationFirst()
    uni = tape.universe()
    size = int(source_config()["three_strategy"]["scope"]["symbols_per_shard"])
    shard = uni[(len(uni) - 1) // size * size:]
    out = []
    for s in shard:
        if s in tape.ACCOUNTING_ONLY or s not in bars:
            continue
        intraday, _ = src.bars_desc(hub, s, "15Min", 200, 45, now)
        if not intraday:
            continue
        raw = tape.raw_rows(bars[s])
        ib = tape.raw_rows(intraday)
        price = float(intraday[-1]["c"])
        out.append(lf.evaluate(s, raw, ib, price, corrected=False))
        out.append(lf.evaluate(s, raw, ib, price, corrected=True))
    return out


# -- the shared agentic cycle (one per pass, all three legacy sleeves) --------------------------------------------
def legacy_cycle(feeds, sleeve, now, arg=None):
    """FEED griffith_legacy_cycle: the agentic cycle's decided candidates for this pass."""
    hub = feeds.hub
    eng = getattr(sleeve, "engine", None)
    st = (eng.store.sleeve_get("griffith_momentum_breakout") or {}) if eng is not None else {}
    states = dict(st.get("candidate_states") or {})
    held = set()
    if eng is not None:
        for sid in LEGACY:
            held |= {i.split(":", 1)[1] for i in eng.books.get(sid, 100_000.0).positions if i.startswith("EQ:")}
    symbols = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + watch_population(states, int(SCOPE.get("radar_max", 50)))
                                 + sorted(held)))
    snaps, label = src.snapshots(hub, symbols)
    leaders = broad_scan(snaps, spread_known=label != "yahoo")[:int(AGENT["research_candidates"])]
    research = {}
    if leaders:
        try:
            rows, _ = src.news(hub, [c.symbol for c in leaders], 50)
            research = analyze(rows, [c.symbol for c in leaders])
        except Exception:
            research = {}
    regime = market_regime(snaps)
    out = []
    for c in leaders[:int(AGENT["deep_analysis_candidates"])]:
        c.catalyst_score, c.headlines = research.get(c.symbol, (0.0, []))
        bars, _ = src.bars_desc(hub, c.symbol, "1Min", 200, 20, now)
        bars = [b for b in bars if b["t"] + 60 <= now]                 # completed minutes only
        if len(bars) < 30:
            continue
        out.append(asdict(decide(c, bars, regime)))
    return {"at": now, "regime": regime, "source": label, "decisions": out, "universe": len(symbols)}


class _Own(Sleeve):
    def __init__(self):
        self.engine = None

    def bind(self, engine):
        self.engine = engine


class LegacySetup(_Own):
    """one setup label of the legacy agentic chain, on its own book."""

    def __init__(self, sleeve_id, setup):
        super().__init__()
        self.setup = setup
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="griffith_intraday", cadence_s=int(AGENT["cycle_seconds"]),
            universe=("SPY", "QQQ", "IWM"), schedule="ext",
            needs={"feeds": [LEGACY_FEED, FEED], "quotes": {"source": "equity"}},
            params={"setup": setup, "target_notional": float(AGENT["target_notional"]),
                    "max_positions": int(AGENT["max_positions"]), "hard_stop_fraction": AGENT["hard_stop_fraction"],
                    "profit_target_fraction": AGENT["profit_target_fraction"]},
            source=RUNTIME, state_schema={"candidate_states": "dict", "funnel_session": "str|None"})

    def wants_tape(self, now):
        """the funnel (owned by the first legacy sleeve) refreshes once per session from the day's decisions."""
        if self.CONFIG.sleeve_id != "griffith_momentum_breakout" or self.engine is None:
            return False
        st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}
        return cal.is_trading_day(et_date(now)) and st.get("funnel_session") != et_date(now)

    def quote_universe(self, now, book):
        return sorted(i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:"))

    def signal(self, view):
        st = dict(view.state or {})
        now = float(view.now)
        if self.CONFIG.sleeve_id == "griffith_momentum_breakout":
            t = view.extra.get(FEED)
            if isinstance(t, dict) and t.get("bars") and st.get("funnel_session") != view.session:
                states = dict(st.get("candidate_states") or {})
                decisions = list(ThreeStrategySleeve.tape_decisions(t))
                try:
                    hub = self.engine.hub if self.engine is not None else None
                    decisions += location_first_decisions(hub, t["bars"], now) if hub is not None else []
                except Exception as e:
                    st["lf_error"] = f"{type(e).__name__}: {str(e)[:120]}"
                funnel(decisions, states, SCOPE.get("radar_max", 50), SCOPE.get("armed_max", 15),
                       SCOPE.get("hands_max", 7))
                st.update(candidate_states=states, funnel_session=view.session)
        cyc = view.extra.get(LEGACY_FEED) or {}
        intents = []
        session = session_name(now)
        if session in AGENT["enabled_sessions"]:
            held = {i.split(":", 1)[1] for i, p in view.positions.items() if float(p["qty"]) != 0}
            pending = {po["inst"].split(":", 1)[1] for po in view.extra.get("pending_orders") or []}
            n = len(held)
            for d in cyc.get("decisions") or []:
                if d["decision"] != "BUY" or d["setup"] != self.setup:
                    continue
                sym = d["symbol"]
                if n >= int(AGENT["max_positions"]) or sym in held | pending:
                    continue
                target = min(float(AGENT["target_notional"]), float(RISK["max_order_notional"]))
                qty = round(target / d["price"], 6)
                limit = float(f"{d['price'] * (1 + float(RISK['limit_price_buffer_fraction'])):.2f}")
                close = cal.session_close(view.session)
                intents.append(Intent(
                    "enter", sym, qty=qty, price_hint=d["price"],
                    order=OrderSpec(type="limit", limit_price=limit, tif="day", window_s=max(60.0, close - now)),
                    exit_rules=(ExitRule("stop_pct", 100 * float(AGENT["hard_stop_fraction"])),
                                ExitRule("target_pct", 100 * float(AGENT["profit_target_fraction"]))),
                    signal_key=f"{sym}:{d.get('market_timestamp') or now}:{self.setup}",
                    reason=f"legacy {self.setup}: {d['thesis']}",
                    meta={"score": d["score"], "catalyst": d["catalyst_score"], "regime": cyc.get("regime")}))
                pending.add(sym)
                n += 1
        st["last_cycle"] = {"at": cyc.get("at"), "regime": cyc.get("regime"), "source": cyc.get("source"),
                            "decided": len(cyc.get("decisions") or [])}
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


# -- the auditable trend agent (app.py) ---------------------------------------------------------------------------
def trend_proposal(series, last_bar, position_qty, pending):
    """TrendAgent.proposals for SPY -> (proposal | None, new last_bar). proposal = (side, qty, price)."""
    short_window, long_window = int(TREND["short_window"]), int(TREND["long_window"])
    if len(series) < long_window:
        return None, last_bar
    newest = series[-1]
    if newest.get("t") == last_bar or pending:
        return None, last_bar
    last_bar = newest.get("t")
    closes = [float(bar["c"]) for bar in series]
    short_avg = sum(closes[-short_window:]) / short_window
    long_avg = sum(closes[-long_window:]) / long_window
    price = closes[-1]
    if short_avg > long_avg * (1 + float(TREND["entry_threshold_fraction"])) and not position_qty:
        return ("buy", round(float(TREND["target_notional"]) / price, 6), price), last_bar
    if short_avg < long_avg and position_qty and float(position_qty) > 0:
        return ("sell", float(position_qty), price), last_bar
    return None, last_bar


class AuditableTrend(_Own):
    def __init__(self):
        super().__init__()
        self.CONFIG = SleeveConfig(
            sleeve_id="griffith_auditable_20_50_trend", family="griffith_intraday", cadence_s=900,
            universe=tuple(source_config()["symbol_allowlist"]), schedule="ext",
            needs={"quotes": {"source": "equity"}},
            params={**TREND, "limit_price_buffer_fraction": RISK["limit_price_buffer_fraction"]},
            source=APP, state_schema={"last_bar": "str|None"})

    def signal(self, view):
        st = dict(view.state or {})
        now = float(view.now)
        hub = self.engine.hub if self.engine is not None else None
        sym = self.CONFIG.universe[0]
        series = view.extra.get("trend_bars")
        if series is None and hub is not None:            # one extra bar: the forming one is dropped
            try:
                series, st["source"] = src.bars_desc(hub, sym, TREND["timeframe"], int(TREND["long_window"]) + 1, 20,
                                                     now)
            except BrokerError as e:
                # EQ-08: the data host refused (2026-10-20: HTTP 401 for 12 hours, 792 sleeve_errors, a call every pass
                # because a failed evaluation leaves the sleeve due). Skip the bar: no decision, the blocker on the
                # record, the next try one 900 s cadence later.
                code = "HTTP %s" % e.status if e.status else "transport"
                st["data_error"] = {"at": now, "error": str(e)[:200]}
                self._st = st
                return [Intent("signal", sym, reason="blocker: DATA_HOST: " + code,
                               meta={"blocker": "DATA_HOST", "error": str(e)[:200]},
                               signal_key="blk:data_host:%s:%s" % (code, view.session))]
            st.pop("data_error", None)
        series = [dict(b, t=tape.iso(b["t"])) for b in (series or []) if b["t"] + 300 <= now]
        series = series[-int(TREND["long_window"]):]
        pos = view.positions.get("EQ:" + sym)
        pending = any(po["inst"] == "EQ:" + sym for po in view.extra.get("pending_orders") or [])
        prop, st["last_bar"] = trend_proposal(series, st.get("last_bar"), pos and float(pos["qty"]), pending)
        intents = []
        if prop:
            side, qty, price = prop
            buf = float(RISK["limit_price_buffer_fraction"])
            limit = float(f"{price * (1 + buf if side == 'buy' else 1 - buf):.2f}")
            close = cal.session_close(view.session) if cal.is_trading_day(view.session) else now + 86400
            kind = "enter" if side == "buy" else "exit"
            intents.append(Intent(kind, sym, qty=qty, price_hint=price,
                                  order=OrderSpec(type="limit", limit_price=limit, tif="day",
                                                  window_s=max(60.0, close - now)),
                                  signal_key=f"{sym}:{st['last_bar']}:{side}",
                                  reason=f"auditable trend {side}: SMA{TREND['short_window']} vs "
                                         f"SMA{TREND['long_window']} on {TREND['timeframe']}"))
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


# -- ORB20_RVOL_1_0_0 (r4_parallel_strategy_lab SPECS) --------------------------------------------------------------
ORB = {"range_minutes": 20, "rvol_multiple": 2.0, "rvol_sessions": 20, "flat_minutes_before_close": 5}
LAB = dict(SOURCE, path="r4_parallel_strategy_lab.py", blob="224b31c200b277bc82fefac552ff22b01a51cdb4", lines="19-43")


def opening_window(bars, day):
    """the session's 09:30-09:50 ET 5-minute bars (start stamps inside the first 20 minutes)."""
    o = cal.session_open(day)
    return [b for b in bars if o <= b["t"] < o + ORB["range_minutes"] * 60]


def orb_levels(bars, day):
    """(range high, range low, window volume, median same-window volume of the prior 20 complete sessions) or None."""
    win = opening_window(bars, day)
    if len(win) != ORB["range_minutes"] // 5:
        return None
    vols = []
    d = cal._as_date(day)
    for _ in range(60):
        d = cal.prev_trading_day(d)
        w = opening_window(bars, d)
        if len(w) == ORB["range_minutes"] // 5:
            vols.append(sum(float(b["v"]) for b in w))
        if len(vols) == ORB["rvol_sessions"]:
            break
    if len(vols) < ORB["rvol_sessions"]:
        return None
    vols.sort()
    k = len(vols)
    med = (vols[k // 2 - 1] + vols[k // 2]) / 2 if k % 2 == 0 else vols[k // 2]
    return (max(float(b["h"]) for b in win), min(float(b["l"]) for b in win), sum(float(b["v"]) for b in win), med)


def orb_breakout(bars, day, high, now):
    """the first completed 5-minute bar after the range that closes above the range high (its stamp) or None."""
    start = cal.session_open(day) + ORB["range_minutes"] * 60
    for b in bars:
        if start <= b["t"] and b["t"] + 300 <= now and float(b["c"]) > high:
            return b["t"]
    return None


class ORB20(_Own):
    """ORB20_RVOL_1_0_0: the 09:30-09:50 ET range on completed regular-session 5-minute bars, first-20-minute volume
    >= 2x the 20-session median of the same window; long the first 5-minute close above the range high, stop at the
    range low, flat at 15:55 ET. The lab registered no direction, stop, sizing or universe; the port takes the
    Griffith desk's long-only book, the standard opening-range stop (the range low), the SCOPE universe and the R4
    fixed slot (capital / 550) — named divergences."""

    def __init__(self):
        super().__init__()
        # the anchor runs it once in the 15:55-16:00 flat window whatever the cadence: runs 300-330 s apart (the host,
        # 2026-10-16) can step over a 300 s window and hold the position into the next session
        self.CONFIG = SleeveConfig(
            sleeve_id="griffith_orb20", family="griffith_intraday", cadence_s=300,
            universe=tuple(tape.tape_symbols()), schedule="rth,!close-5:close+0",
            needs={"quotes": {"source": "equity"}}, params=dict(ORB, slots=550),
            source=dict(LAB, spec="ORB20_RVOL_1_0_0"),
            state_schema={"day": "str|None", "qualified": "dict", "entered": "list"})

    def quote_universe(self, now, book):
        st = (self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}) if self.engine is not None else {}
        names = set(st.get("qualified") or {}) if st.get("day") == et_date(now) else set()
        return sorted(names | {i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")})

    def _bars(self, view, symbols, n):
        if "orb_bars" in view.extra:
            return {s: view.extra["orb_bars"].get(s) or [] for s in symbols}
        hub = self.engine.hub if self.engine is not None else None
        if hub is None or not symbols:
            return {}
        return hub.bars("equity", "5m", list(symbols), n)

    def signal(self, view):
        st = dict(view.state or {})
        now, day = float(view.now), view.session
        if not cal.is_trading_day(day):
            self._st = st
            return []
        close = cal.session_close(day)
        held = {i.split(":", 1)[1]: p for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"])}
        intents = []
        if now >= close - ORB["flat_minutes_before_close"] * 60:
            for s in sorted(held):
                intents.append(Intent("exit", s, signal_key=f"{s}:{day}:flat", reason="ORB20 flat at 15:55 ET",
                                      order=OrderSpec(window_s=300)))
            self._st = st
            return intents
        if st.get("day") != day:
            if now < cal.session_open(day) + ORB["range_minutes"] * 60 + 60:
                self._st = st
                return []
            bars = self._bars(view, self.CONFIG.universe, 78 * 22)
            qual = {}
            for s, bl in bars.items():
                lv = orb_levels(bl or [], day)
                if lv and lv[3] > 0 and lv[2] >= ORB["rvol_multiple"] * lv[3]:
                    qual[s] = {"high": lv[0], "low": lv[1], "volume": lv[2], "median": lv[3]}
            st.update(day=day, qualified=qual, entered=[])
        entered = list(st.get("entered") or [])
        pending = {po["inst"].split(":", 1)[1] for po in view.extra.get("pending_orders") or []}
        todo = [s for s in sorted(st.get("qualified") or {}) if s not in entered and s not in held and s not in pending]
        if todo:
            bars = self._bars(view, todo, 90)
            slot = float(self.CONFIG.capital) / 550
            for s in todo:
                lv = st["qualified"][s]
                hit = orb_breakout(bars.get(s) or [], day, lv["high"], now)
                q = view.quotes.get(s) or {}
                px = q.get("ask") or q.get("last")
                if hit is None or not px or float(px) <= lv["low"]:
                    continue
                intents.append(Intent("enter", s, notional=slot, price_hint=float(px), signal_key=f"{s}:{day}:orb",
                                      exit_rules=(ExitRule("stop", lv["low"]),),
                                      reason=f"ORB20 breakout above {lv['high']:.2f} "
                                             f"(rvol {lv['volume'] / lv['median']:.2f}x)",
                                      order=OrderSpec(window_s=600), meta={"range_high": lv["high"],
                                                                           "range_low": lv["low"], "bar": hit}))
                entered.append(s)
        st["entered"] = entered
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [AuditableTrend(), ORB20()] + [LegacySetup(sid, setup) for sid, setup in LEGACY.items()]


FEEDS = {LEGACY_FEED: legacy_cycle}
