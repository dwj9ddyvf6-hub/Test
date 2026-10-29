"""Tensor Swing (flagship) — lean-desk port.

The Tensor engine (v698 pin, Decision #108) runs ONLY inside core
Data's vendored canonical door. This sleeve NEVER imports the engine:
it receives engine output as data via context.extra.

master-desk: the old desk's flagship (scan_and_trade.py, "Femto (Griffith
reborn)") restored on that output — its own decision law, not a staging
shim. The feed (desk/feedlib/tensor.py) runs the byte-exact engine on the
canonical Yahoo 60m RTH series of every basket / held name; this module
carries scan_and_trade's decide(), pass 2 and manage_positions():

  signals .. the engine's confirmed swings on the last 5 closed canonical
             bars (detect_signals: entry = the swing bar's close, stop =
             invalidation, target, confidence = the 11-factor score,
             phenotype, candle regime, confirmationAgeBars).
  decide ... the newest confirmed swing: older than 3 bars -> skip (no
             chase); older than 6 clock hours -> WATCH (dead prices); bar
             already acted on -> skip; confidence below the watch cutoff
             -> skip, below the trade cutoff -> WATCH (the calibration as
             pinned 2026-10-13: trade 8 / watch 6 every phenotype, 1D/1W
             alignment weights 0/0, no trend delta, no sector penalty);
             the bought-extended gate (entry > 0.5 ATR over the signal
             bar's open or the bar ran > 1.5 ATR — the shared rule,
             Tensor-scoped); held / working -> skip; 10 positions; the
             latest bar already through the stop -> skip. rank_score =
             confidence + alignment + 1 for a swing in a bearish (yellow)
             candle regime. Size: 1% of equity at risk on the engine's
             entry - stop, scaled 0.75 / 0.5 by the max 1H-return
             correlation with a held name (>= 0.65 / >= 0.80), at least
             one share, notional capped at 50% of equity. Bracket: limit
             at the entry, take-profit at the target, stop-loss at the
             stop, GTC; a working entry dies after 24 hours.
  pass 2 ... TRADE candidates by rank (a BROKEN daily structure — the
             structural screen — demoted below every other), the free
             slots filled in that order, 3 positions per sector.
  exits .... a held name exits at market when either of the last 2 closed
             canonical bars shows the engine's bearish conflict, bear
             votes over bull votes or consensus-sell, or once more than 20
             closed bars have printed since the entry bar (the time stop).

Gone under the cutover doctrine: the earnings blackout, circuit breaker,
market-green gate, 5-day buy delay, red-day gate, chart gate (Decision
#75), drawdown brake, 150% desk cap, risk gate and context gate. Named
divergences: positions, slots and sector counts are this sleeve's own
book (the old read the shared account: every sleeve's holdings consumed
Tensor's ten slots); the correlation reads the canonical 1H returns (the
old read the Alpaca extended-hours series it still fetched).

Inputs via context.extra: "tensor" (the feed), "meta" (acted bars),
"sleeve_state". Bars: the basket's completed daily bars (the structural
screen)."""
import hashlib
import math

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig
from ...vendor.old_desk_research import extension_gate as ext_gate
from ...vendor.old_desk_research import risk as desk_risk
from ...vendor.old_desk_research import structural_screen as sscreen

MIN_CONF = 7  # desk swing-watch floor used across Tensor consumers (the femto port's staging floor)
MAX_POSITIONS = 10
RISK_PCT = 0.01
MIN_BARS_AFTER_STRIP = 60
MAX_SIGNAL_AGE_BARS = 3
MAX_SIGNAL_AGE_HOURS = 6
EXIT_TIME_STOP_BARS = 20
CORR_LOOKBACK_BARS = 60
CORR_MED_THRESHOLD = 0.65
CORR_HIGH_THRESHOLD = 0.80
EXT_SHADOW_ATR_LEN = 14
NOTIONAL_CAP = 0.5
STALE_ENTRY_S = 24 * 3600
# desk/calibration.json at the pin (updated_by fixall-2026-10-13-decision-107)
CALIBRATION = {"trade_cutoff": {"BREAKOUT": 8, "RECLAIM": 8, "REVERSAL": 8, "TRANSITION": 8, "default": 8},
               "watch_cutoff": {"BREAKOUT": 6, "RECLAIM": 6, "REVERSAL": 6, "TRANSITION": 6, "default": 6},
               "rank_weight_daily": 0, "rank_weight_weekly": 0,
               "trend_delta": {"CHOP": 0, "DOWNTREND": 0, "UPTREND": 0}, "sector_penalty": 0}

CONFIG = SleeveConfig(
    sleeve_id="tensor_swing", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def stage_candidates(signals, held, gold_diamond=None, max_new=None):
    """The femto port's staging (kept for its callers): preserve engine order; drop held symbols, sub-floor
    confidence and extended candidates; annotate (never gate on) Gold Diamond."""
    out = []
    gd = gold_diamond or {}
    for s in signals or []:
        if not isinstance(s, dict):
            continue
        sym = s.get("symbol")
        if not sym or sym in held:
            continue
        try:
            conf = int(s.get("confidence"))
        except (TypeError, ValueError):
            continue
        if conf < MIN_CONF:
            continue
        if s.get("extended"):
            continue
        row = dict(s)
        row["gold_diamond"] = (gd.get(sym) or {}).get("stamp")
        out.append(row)
        if max_new is not None and len(out) >= max_new:
            break
    return out


# ---------------------------------------------------------------------------
# the old desk's pure helpers (scan_and_trade.py), epoch bar times
# ---------------------------------------------------------------------------
def signals_of(bars, res):
    """detect_signals: each confirmed swing among the engine's evaluations -> the desk's signal schema."""
    by_ts = {int(b["t"]): b for b in bars}
    diags = {d["timestamp"]: d for d in (res or {}).get("diagnostics") or []}
    sigs = []
    for ev in (res or {}).get("swings") or []:
        s = ev.get("swing") or {}
        if not s.get("confirmed"):
            continue
        src = by_ts.get(ev.get("timestamp"))
        if src is None:
            continue
        d = diags.get(ev["timestamp"], {})
        sigs.append({"t": int(src["t"]), "setup": True, "confirmation": True, "swing_confirmed": True,
                     "bull_votes": d.get("bullishVotes"), "bear_votes": d.get("bearishVotes"),
                     "confidence": int(s.get("score", 0) or 0), "phenotype": s.get("phenotype"), "atr": None,
                     "stop": s.get("invalidation"), "target": s.get("target"), "entry": float(src["c"]),
                     "age": s.get("confirmationAgeBars"), "bearish_conflict": bool(s.get("bearishConflict")),
                     "regime": ev.get("regime"), "factors": s.get("factors") or [], "engine": "tensor-exact-v698"})
    return sigs


def _ext_simple_atr14(bars_upto):
    try:
        win = list(bars_upto)[-EXT_SHADOW_ATR_LEN:]
        if len(win) < EXT_SHADOW_ATR_LEN:
            return None
        trs, prev_c = [], None
        for b in win:
            h, l, c = float(b["h"]), float(b["l"]), float(b["c"])
            trs.append(h - l if prev_c is None else max(h - l, abs(h - prev_c), abs(l - prev_c)))
            prev_c = c
        atr = sum(trs) / EXT_SHADOW_ATR_LEN
        return atr if atr > 0 else None
    except (KeyError, TypeError, ValueError):
        return None


def extension_shadow(bars, signal):
    """the signal bar's run / range and the entry's distance from its open, in 1H ATR14 units (simple mean)."""
    try:
        if not signal or not signal.get("t"):
            return None
        t = signal["t"]
        idx = next((i for i, b in enumerate(bars or []) if b.get("t") == t), None)
        if idx is None:
            return None
        sb = bars[idx]
        o, h, l, c = float(sb["o"]), float(sb["h"]), float(sb["l"]), float(sb["c"])
        atr = _ext_simple_atr14(bars[:idx + 1])
        if atr is None:
            return None
        entry = float(signal.get("entry"))
        entry_atr = (entry - o) / atr
        return {"shadow_only": True, "atr14_1h": round(atr, 4), "signal_bar_t": t,
                "bar_run_atr": round((c - o) / atr, 3), "bar_range_atr": round((h - l) / atr, 3),
                "entry_ext_atr": round(entry_atr, 3), "ext_gt_0p5": bool(entry_atr > 0.5),
                "ext_gt_1p0": bool(entry_atr > 1.0)}
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _log_returns(closes):
    out = []
    for i in range(1, len(closes)):
        try:
            a, b = float(closes[i - 1]), float(closes[i])
        except (TypeError, ValueError):
            continue
        if a > 0 and b > 0:
            out.append(math.log(b / a))
    return out


def returns_correlation(bars_a, bars_b, lookback=CORR_LOOKBACK_BARS):
    """Pearson correlation of 1H log returns over the last `lookback` timestamp-aligned bars; None when < 20."""
    try:
        map_a, map_b = {}, {}
        for b in bars_a or []:
            if b.get("t") is not None and b["t"] not in map_a:
                map_a[b["t"]] = b
        for b in bars_b or []:
            if b.get("t") is not None and b["t"] not in map_b:
                map_b[b["t"]] = b
        common = sorted(set(map_a) & set(map_b))[-lookback:]
        if len(common) < 20:
            return None
        ra = _log_returns([map_a[t].get("c") for t in common])
        rb = _log_returns([map_b[t].get("c") for t in common])
        m = min(len(ra), len(rb))
        if m < 19:
            return None
        ra, rb = ra[-m:], rb[-m:]
        ma, mb = sum(ra) / m, sum(rb) / m
        num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
        da = math.sqrt(sum((x - ma) ** 2 for x in ra))
        db = math.sqrt(sum((y - mb) ** 2 for y in rb))
        if da == 0 or db == 0:
            return None
        return num / (da * db)
    except Exception:
        return None


def correlation_risk_multiplier(candidate_bars, held_bars):
    try:
        best = best_sym = None
        for sym, hb in (held_bars or {}).items():
            c = returns_correlation(candidate_bars, hb)
            if c is not None and (best is None or c > best):
                best, best_sym = c, sym
        if best is None:
            return 1.0, "no correlation baseline"
        if best >= CORR_HIGH_THRESHOLD:
            return 0.5, "max 1H-return corr %.2f vs %s >= %.2f: risk halved" % (best, best_sym, CORR_HIGH_THRESHOLD)
        if best >= CORR_MED_THRESHOLD:
            return 0.75, "max 1H-return corr %.2f vs %s >= %.2f: risk cut 25%%" % (best, best_sym, CORR_MED_THRESHOLD)
        return 1.0, "max 1H-return corr %.2f vs %s: no adjustment" % (best, best_sym)
    except Exception:
        return 1.0, "correlation read failed"


def confirm_tag(confirm):
    c = confirm or {}
    return "1D=%s 1W=%s" % ("green" if c.get("daily_green") else "--", "buy" if c.get("weekly_buy") else "--")


def cutoffs(phenotype, cal=CALIBRATION):
    """(trade, watch, trend delta) — desk/calibrator get_effective_cutoffs with the trend regime UNKNOWN."""
    p = str(phenotype or "").upper()
    tc, wc = cal["trade_cutoff"], cal["watch_cutoff"]
    return int(tc.get(p, tc["default"])), int(wc.get(p, wc["default"])), 0


def client_order_id(symbol, acted_bar_t, order):
    """the old deterministic_client_order_id: same signal bar + same bracket geometry -> the same id."""
    from datetime import datetime, timezone
    iso = datetime.fromtimestamp(int(acted_bar_t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ev = "|".join((str(symbol).upper(), iso, "%.2f" % order["limit_price"], "%.2f" % order["stop_loss"],
                   "%.2f" % order["take_profit"], str(order["qty"])))
    return "femto-%s-%s-%s" % (iso[:10].replace("-", ""), str(symbol).upper(),
                               hashlib.sha256(ev.encode("utf-8")).hexdigest()[:10])


def decide(sym, bars, equity, held, working, acted, signals, confirm=None, held_bars=None, now=None,
           cal=CALIBRATION):
    """scan_and_trade.decide() minus the desk gates (see the module docstring)."""
    confirm = dict(confirm or {})
    align = ((cal.get("rank_weight_daily", 1) if confirm.get("daily_green") else 0) +
             (cal.get("rank_weight_weekly", 0) if confirm.get("weekly_buy") else 0))
    st = {"regime_pref": 0}

    def result(decision, reason, signal=None, order=None, acted_bar_t=None, base_conf=0):
        return {"symbol": sym, "decision": decision, "reason": reason, "signal": signal, "order": order,
                "acted_bar_t": acted_bar_t, "rank_score": base_conf + align + st["regime_pref"], "confirm": confirm}

    swung = [s for s in signals or [] if s["swing_confirmed"]]
    if not swung:
        return result("SKIP_NO_SIGNAL", "no swing_confirmed bar among %d completed bars (tensor-exact)" % len(bars))
    sig = swung[-1]
    if sig.get("regime") == "bearish":
        st["regime_pref"] = 1
    try:
        hi20 = max(float(b["h"]) for b in bars[-20:] if b.get("h") is not None)
        sig["extension_vs_high_pct"] = ((float(bars[-1]["c"]) / hi20 - 1.0) * 100.0 if hi20 > 0 else None)
    except Exception:
        sig["extension_vs_high_pct"] = None
    try:
        sig_age = float(sig.get("age")) if sig.get("age") is not None else None
    except (TypeError, ValueError):
        sig_age = None
    if sig_age is not None and sig_age > MAX_SIGNAL_AGE_BARS:
        return result("SKIP_STALE_SIGNAL", "newest confirmed swing is %.0f bars old (> %d): no chase"
                      % (sig_age, MAX_SIGNAL_AGE_BARS), signal=sig, base_conf=sig["confidence"])
    age_h = (float(now) - float(sig["t"])) / 3600.0 if now is not None else None
    if age_h is not None and age_h > MAX_SIGNAL_AGE_HOURS:
        return result("WATCH", "stale signal: bar %s is %.1f clock-hours old (> %dh): demoted to watch, no trade on "
                      "dead prices" % (sig["t"], age_h, MAX_SIGNAL_AGE_HOURS), signal=sig, base_conf=sig["confidence"])
    if str((acted or {}).get(sym)) == str(sig["t"]):
        return result("SKIP_DUPLICATE", "already acted on bar %s" % sig["t"], signal=sig, base_conf=sig["confidence"])
    conf = sig["confidence"]
    tag = confirm_tag(confirm)
    t_cut, w_cut, _td = cutoffs(sig.get("phenotype"), cal)
    if conf < w_cut:
        return result("SKIP_LOW_CONF", "confidence %d below watch floor %d [%s]" % (conf, w_cut, tag), signal=sig,
                      base_conf=conf)
    if conf < t_cut:
        return result("WATCH", "moderate confidence %d (watch %d-%d): monitoring, no order [%s]"
                      % (conf, w_cut, t_cut - 1, tag), signal=sig, base_conf=conf)
    ext = extension_shadow(bars, sig) or {}
    skip, why = ext_gate.check(ext.get("entry_ext_atr"), ext.get("bar_range_atr"))
    if skip:
        return result("SKIP_EXTENDED", why + " [%s]" % tag, signal=sig, base_conf=conf)
    if sym in held or sym in (working or ()):
        return result("SKIP_ALREADY_HELD", "position already open or entry working in %s [%s]" % (sym, tag),
                      signal=sig, base_conf=conf)
    if len(held) + len(set(working or ()) - set(held)) >= MAX_POSITIONS:
        return result("SKIP_MAX_POSITIONS", "at cap: %d concurrent positions [%s]" % (len(held), tag), signal=sig,
                      base_conf=conf)
    entry, stop, target = sig["entry"], sig["stop"], sig["target"]
    if entry is None or stop is None or target is None:
        return result("SKIP_INVALID_RISK", "engine omitted entry/stop/target (entry=%s stop=%s target=%s) [%s]"
                      % (entry, stop, target, tag), signal=sig, base_conf=conf)
    per_share = entry - stop
    if per_share <= 0:
        return result("SKIP_INVALID_RISK", "per-share risk %.4f not positive (entry=%.4f stop=%.4f) [%s]"
                      % (per_share or 0.0, entry or 0.0, stop or 0.0, tag), signal=sig, base_conf=conf)
    try:
        latest_low = float(bars[-1]["l"])
    except (IndexError, KeyError, TypeError, ValueError):
        latest_low = None
    if latest_low is not None and latest_low <= stop:
        return result("SKIP_STOP_BREACHED", "latest 1H bar low $%.2f already through planned stop $%.2f: bracket "
                      "stop dead on arrival, no trade [%s]" % (latest_low, stop, tag), signal=sig, base_conf=conf)
    risk = RISK_PCT * equity
    mult, mdet = correlation_risk_multiplier(bars, held_bars)
    risk = risk * mult
    qty = max(1, int(math.floor(risk / per_share)))
    capped = max(1, int(math.floor(NOTIONAL_CAP * equity / entry)))
    cap_note = ""
    if qty > capped:
        cap_note = "; NOTIONAL CAP: qty %d -> %d (notional $%.0f capped at 50%% of equity)" % (qty, capped,
                                                                                            capped * entry)
        qty = capped
    order = {"symbol": sym, "side": "buy", "qty": qty, "type": "limit", "limit_price": round(entry, 2),
             "time_in_force": "gtc", "order_class": "bracket", "take_profit": round(target, 2),
             "stop_loss": round(stop, 2)}
    order["client_order_id"] = client_order_id(sym, sig["t"], order)
    reason = ("confidence %d >= %d (%s%s) [%s]: risking $%.2f (%.0f%% of $%.2f equity%s), per-share risk $%.4f -> "
              "qty %d @ $%.2f (TP $%.2f / SL $%.2f)%s"
              % (conf, t_cut, sig["phenotype"], " yellow-regime+1" if st["regime_pref"] else "", tag, risk,
                 RISK_PCT * 100, equity, (" x %.2f corr" % mult) if mult < 1.0 else "", per_share, qty,
                 round(entry, 2), round(target, 2), round(stop, 2), cap_note))
    return result("TRADE", reason, signal=sig, order=order, acted_bar_t=sig["t"], base_conf=conf)


def bearish_exit_trigger(res):
    """either of the last two closed bars: bearish conflict, bear votes > bull votes, or consensus-sell."""
    try:
        swings = (res or {}).get("swings") or []
        diags = {d.get("timestamp"): d for d in ((res or {}).get("diagnostics") or [])}
        for ev in swings[-2:]:
            s = ev.get("swing") or {}
            ts = ev.get("timestamp")
            if s.get("bearishConflict"):
                return True, "bearish conflict on bar %s" % ts
            d = diags.get(ts) or {}
            bull, bear = d.get("bullishVotes"), d.get("bearishVotes")
            if bull is not None and bear is not None and bear > bull:
                return True, "bear votes %d > bull votes %d on bar %s" % (bear, bull, ts)
            if "consensus-sell" in (d.get("enrichmentIds") or []):
                return True, "consensus-sell (bearish 5-of-7) on bar %s" % ts
    except Exception:
        pass
    return False, None


def bars_since_entry(entry_bar_t, bars):
    """closed bars strictly after the entry bar's open (None when the entry predates / postdates the window)."""
    if not entry_bar_t:
        return None
    try:
        e = int(entry_bar_t)
        stamps = [int(b["t"]) for b in bars]
    except (TypeError, ValueError, KeyError):
        return None
    if e in stamps:
        return len(bars) - 1 - stamps.index(e)
    if stamps and e < stamps[0]:
        return None
    if stamps and e > stamps[-1]:
        return None
    return sum(1 for s in stamps if s > e)


def time_stop_due(entry_bar_t, bars):
    """(due, bars_held | None, note): more than 20 closed bars since entry; an entry older than the window is due."""
    try:
        n = bars_since_entry(entry_bar_t, bars)
        if n is not None:
            return n > EXIT_TIME_STOP_BARS, n, None
        oldest = int(bars[0]["t"]) if bars else None
        if entry_bar_t and oldest and int(entry_bar_t) < oldest:
            return True, None, "entry bar %s older than %d-bar window" % (entry_bar_t, len(bars))
    except Exception:
        pass
    return False, None, None


# ---------------------------------------------------------------------------
# the pass
# ---------------------------------------------------------------------------
def _book(state):
    return {s: v["position"] for s, v in (state or {}).items() if isinstance(v, dict) and v.get("position")}


def _working(state):
    return {s for s, v in (state or {}).items() if isinstance(v, dict) and v.get("pending_entry") and not v.get("position")}


def fill_slots(trades, book, working):
    """pass 2: TRADE candidates by (rank desc, symbol), the free slots (10 - held - working) filled in that order;
    held / working names skipped, a fourth name in one sector skipped (desk/risk.check_concentration over this
    book and this pass's fills). Returns the filled candidates; the others carry their skip decision."""
    cands = sorted(trades, key=lambda p: (-p["rank_score"], p["symbol"]))
    slots = MAX_POSITIONS - len(book) - len(set(working) - set(book))
    view = {s: {"sector": desk_risk.sector(s)} for s in book}
    filled = []
    for p in cands:
        if p["symbol"] in book or p["symbol"] in working:
            p.update(decision="SKIP_ALREADY_HELD", order=None, acted_bar_t=None)
            continue
        if len(filled) >= slots:
            p.update(decision="SKIP_MAX_POSITIONS", order=None, acted_bar_t=None,
                     reason="tiebreak: only %d slot(s) free; rank_score %d (%s) below cutoff"
                            % (max(0, slots - len(filled)), p["rank_score"], confirm_tag(p.get("confirm"))))
            continue
        if desk_risk.check_concentration(p["symbol"], view):
            p.update(decision="SKIP_CONCENTRATION", order=None, acted_bar_t=None,
                     reason="sector %s already holds 3 positions (max 3 per sector)" % desk_risk.sector(p["symbol"]))
            continue
        filled.append(p)
        view[p["symbol"]] = {"sector": desk_risk.sector(p["symbol"])}
    return filled


def evaluate(daily, context):
    """the pass's decisions: (pending decisions by symbol in basket order, entry decisions filled, exits)."""
    extra = context.extra or {}
    feed = extra.get("tensor") or {}
    state = extra.get("sleeve_state") or {}
    meta = extra.get("meta") or {}
    acted = meta.get("acted") or {}
    series, engine = feed.get("series") or {}, feed.get("engine") or {}
    errors, confirms = feed.get("errors") or {}, feed.get("confirm") or {}
    equity = float(context.equity or 0.0)
    now = float(context.now)
    book = _book(state)
    working = _working(state)
    held_bars = {s: series[s] for s in book if s in series}
    pending = []
    for sym in list(dict.fromkeys(list(series) + list(errors))):
        if sym in errors and sym not in engine:
            pending.append({"symbol": sym, "decision": "SKIP_DATA_ERROR", "reason": str(errors[sym])[:200],
                            "signal": None, "order": None, "acted_bar_t": None, "rank_score": 0, "confirm": {}})
            continue
        bars = series.get(sym) or []
        if len(bars) < MIN_BARS_AFTER_STRIP:
            pending.append({"symbol": sym, "decision": "SKIP_INSUFFICIENT_BARS",
                            "reason": "only %d completed canonical bars (need %d)" % (len(bars), MIN_BARS_AFTER_STRIP),
                            "signal": None, "order": None, "acted_bar_t": None, "rank_score": 0, "confirm": {}})
            continue
        d = decide(sym, bars, equity, set(book), working, acted, signals_of(bars, engine.get(sym)),
                   confirm=confirms.get(sym), held_bars={s: b for s, b in held_bars.items() if s != sym}, now=now)
        pending.append(d)
    for p in pending:
        if p["decision"] == "TRADE":
            sv = sscreen.screen_from_bars(p["symbol"], (daily or {}).get(p["symbol"]) or [])
            p["structure"] = sv
            if sv.get("verdict") == "BROKEN":
                p["rank_score"] = sscreen.apply_structure_rank(p["rank_score"], "BROKEN")
                p["reason"] += " | structure BROKEN (rank demoted): " + "; ".join(sv.get("reasons", []))
    filled = fill_slots([p for p in pending if p["decision"] == "TRADE"], set(book), working)
    exits = []
    for sym, pos in book.items():
        if pos.get("exit_submitted"):
            continue
        bars = series.get(sym)
        trig, why = (bearish_exit_trigger(engine[sym]) if sym in engine else (False, None))
        due, n, note = time_stop_due(pos.get("entry_bar_t"), bars or [])
        if not trig and due and bars:
            trig = True
            why = ("time stop: %d closed bars since entry (edge horizon %d)" % (n, EXIT_TIME_STOP_BARS)
                   if n is not None else "time stop: %s (edge horizon %d bars)" % (note, EXIT_TIME_STOP_BARS))
        if trig:
            exits.append({"symbol": sym, "reason": why, "bars_held": n})
    return pending, filled, exits


def _pass(daily, context):
    extra = context.extra
    memo = extra.get("_ts_pass") if isinstance(extra, dict) else None
    if memo is None:
        memo = evaluate(daily, context)
        if isinstance(extra, dict):
            extra["_ts_pass"] = memo
    return memo


class TensorSwing(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        if "tensor" not in extra:            # the femto port's staging path (engine output as tensor_signals)
            state = extra.get("sleeve_state") or {}
            held = {s for s, st in state.items() if (st or {}).get("position")}
            out = []
            for row in stage_candidates(extra.get("tensor_signals"), held, extra.get("gold_diamond"),
                                        extra.get("max_new")):
                bl = bars.get(row["symbol"]) or []
                reason = ("tensor_swing staged: phenotype=%s conf=%s regime=%s"
                          % (row.get("phenotype"), row.get("confidence"), row.get("regime")))
                if row.get("gold_diamond"):
                    reason += " gold_diamond=%s (annotation only)" % row["gold_diamond"]
                out.append(Intent("enter", row["symbol"], price_hint=round(float(bl[-1]["c"]), 2) if bl else None,
                                  reason=reason))
            return out
        pending, filled, exits = _pass(bars, context)
        out = []
        for p in filled:
            o, sig = p["order"], p["signal"]
            out.append(Intent(
                "enter", p["symbol"], qty_hint=int(o["qty"]), price_hint=o["limit_price"], stop=o["stop_loss"],
                target=o["take_profit"],
                exit_rules=(ExitRule("stop", o["stop_loss"]), ExitRule("target", o["take_profit"])),
                order={"type": "limit", "limit_price": o["limit_price"], "tif": "gtc", "window_s": STALE_ENTRY_S},
                signal_key=o["client_order_id"],
                position_meta={"entry_bar_t": int(sig["t"]), "phenotype": sig.get("phenotype"),
                               "confidence": sig.get("confidence"), "regime": sig.get("regime"),
                               "sector": desk_risk.sector(p["symbol"]), "rank_score": p["rank_score"],
                               "engine": sig.get("engine")},
                reason=("tensor TRADE: " + p["reason"])[:300]))
        for e in exits:
            out.append(Intent("exit", e["symbol"], signal_key="%s:%s:tensor-exit" % (e["symbol"], context.session),
                              reason=("tensor exit: " + e["reason"])[:300]))
        return out


def signal(bars, slice_state, context):
    return TensorSwing().signal(bars, slice_state, context)


def fresh_signals(pending):
    """the old journal's fresh_signals: every decision of the pass (after pass 2) that is TRADE or WATCH, in
    basket order — what tensor_red_dip reads."""
    out = []
    for p in pending:
        if p.get("decision") in ("TRADE", "WATCH"):
            s = p.get("signal") or {}
            out.append({"symbol": p["symbol"], "decision": p["decision"], "confidence": s.get("confidence"),
                        "phenotype": s.get("phenotype")})
    return out


def next_meta(bars, slice_state, context, intents=()):
    """acted[]: the signal bar of every entry sent (a bar is acted on once). fresh_signals: this session's
    latest pass that held any TRADE / WATCH (the old read_fresh_signals: the latest journal entry with
    fresh_signals wins)."""
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    if "tensor" not in extra:
        return meta
    pending, filled, _exits = _pass(bars, context)
    if filled:
        acted = dict(meta.get("acted") or {})
        for p in filled:
            acted[p["symbol"]] = int(p["acted_bar_t"])
        meta["acted"] = acted
    fresh = fresh_signals(pending)
    if fresh:
        meta["fresh_signals"] = {"session": context.session, "at": float(context.now), "signals": fresh}
    return meta


def monitor(mod, bars, context):
    """the decisions the old ledger and learning store recorded for every fresh signal (TRADE / WATCH / the
    skips of a qualified signal) — observations, never orders."""
    extra = context.extra or {}
    if "tensor" not in extra:
        return []
    pending, _filled, _exits = _pass(bars, context)
    out = []
    for p in pending:
        if p.get("signal") and p["decision"] not in ("SKIP_NO_SIGNAL", "SKIP_DUPLICATE"):
            s = p["signal"]
            out.append((p["symbol"], "tensor %s conf=%s %s: %s" % (p["decision"], s.get("confidence"),
                                                                  s.get("phenotype"), p["reason"]),
                        {"decision": p["decision"], "signal_t": s.get("t"), "confidence": s.get("confidence"),
                         "phenotype": s.get("phenotype"), "rank_score": p["rank_score"]}))
    return out
