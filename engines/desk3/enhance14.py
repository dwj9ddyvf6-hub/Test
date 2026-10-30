"""ENH batch-14 adapter-layer gates (Edge pass, second look).

These gates live at the v3 adapter layer ONLY: the ported strategy
files under sleeves/ (and, for batch-2 sleeves, adapters/) are
sha256-pinned to v2 and are never edited by this program. Each gate
post-filters or reprices ENTRY intents emitted by the underlying
sleeve; exits are never filtered (a held position must always be
able to leave). Every gate is switched per sleeve via
extra["<sleeve>_enh2"][<field>] (default ON; OFF restores the
pre-change rule exactly — the filter becomes a pass-through) and
appends a paired control/treatment record to LAST_PAIRED (and to
view extra["enh14_paired"] when writable) for every entry candidate
it judges, so the shadow control is evaluated on the same
opportunities without ever emitting.

Gates (one conceptual change per sleeve, at its binding leak):
- aurelia_ndx / complete_plan (special two-phase evaluate, see
  aurelia_ndx_evaluate): the sleeve's ENH first-evaluation freeze is
  consumed by a PARTIALLY priced plan — one own-symbol leg without
  a bar is skipped, the priced subset emits, and the session is
  frozen, so the missing leg is never rebalanced that day.
- beatendown / current_bar_pricing: entries are sized and priced
  off the qualifier's signal-WEEK close (up to a week stale) while
  the desk serves current daily bars; reprice/resize each entry
  off the symbol's last served bar close (selection untouched).
- confluence / dedupe_entries: duplicate qualifier rows for one
  symbol each produce an entry intent in the same pass (the sleeve
  tests the pre-pass book, not its own staged intents); drop repeat
  entry intents for a symbol after the first.
- donchian / chase_gate: the equity twin never got donchian_crypto's
  ENH chase refusal; refuse an entry whose price_hint (the breakout
  close) sits more than ATR_MULT x ATR(14) above the 20-bar channel
  level, recomputed from the served bars.
- donchian_crypto / stale_bar_gate (15Min bars): a dead Kraken/SIP
  feed leaves the last 15m bar hours old and the sleeve still
  enters the stale breakout at a dead price.
- bilbo_options / stale_bar_gate (5Min bars): episode detection
  reads the served 5-min bars; a stale feed's "first bar out" is a
  dead print. The sleeve's time gate reads the BAR's clock, never
  the decision clock.
- capitulation_options / stale_bar_gate (1Hour bars): the
  capitulation signature is read off the last closed 1H bar; a dead
  hourly feed leaves entries firing on an hours-old signature.
  Intraday stale bounds are span-adaptive: the newest bar's close
  is more than 4 of the series' own bar-spans old.
- earnings_buyback / stale_bar_gate (1Day bars, 7 days): spot is
  the last daily close; structures are selected and sized off it.
  Bound follows the batch-18 stale-bar precedent (longest
  legitimate gap ~4.4 days).
- em_1587 / target_consumed: the signal stays "fresh" for 1800s
  while the sleeve evaluates every 60s; if the current spot (the
  entry intent's price_hint) has already reached the setup's
  target (parsed from the intent reason), the room the trade was
  taken for no longer exists — refuse the entry.
"""
from datetime import datetime, timezone

LAST_PAIRED = []

SWITCH_FIELDS = {
    "aurelia_ndx": "complete_plan",
    "beatendown": "current_bar_pricing",
    "confluence": "dedupe_entries",
    "donchian": "chase_gate",
    "donchian_crypto": "stale_bar_gate",
    "bilbo_options": "stale_bar_gate",
    "capitulation_options": "stale_bar_gate",
    "earnings_buyback": "stale_bar_gate",
    "em_1587": "target_consumed",
}

_STALE_TF = {
    "donchian_crypto": "15Min",
    "bilbo_options": "5Min",
    "capitulation_options": "1Hour",
    "earnings_buyback": "1Day",
}
# Intraday stale bound: the newest bar's CLOSE is more than this many
# of the series' own bar-spans old at decision time (span-adaptive:
# a 15Min series binds at >4 missed bars; the bound reads the served
# series, never a hardcoded clock, so it cannot false-fire on a
# legitimately coarser series). Daily series use the batch-18 flat
# bound (7 days; longest legitimate gap ~4.4 days).
_STALE_MAX_SPANS = 4.0
_STALE_DAILY_AGE_S = 7.0 * 86400.0

EXP_IDS = {
    "aurelia_ndx": "ENH2-AURELIA-NDX-20261024",
    "beatendown": "ENH2-BEATENDOWN-20261024",
    "bilbo_options": "ENH2-BILBO-20261024",
    "capitulation_options": "ENH2-CAPOPT-20261024",
    "confluence": "ENH2-CONFLUENCE-20261024",
    "donchian": "ENH2-DONCHIAN-20261024",
    "donchian_crypto": "ENH2-DONCHIAN-CRYPTO-20261024",
    "earnings_buyback": "ENH2-EARNINGS-BUYBACK-20261024",
    "em_1587": "ENH2-EM1587-20261024",
}


def _extra_of(view, extra=None):
    view = view or {}
    merged = {}
    params = view.get("params") or {}
    if isinstance(params.get("extra"), dict):
        merged.update(params["extra"])
    if isinstance(view.get("extra"), dict):
        merged.update(view["extra"])
    if isinstance(extra, dict):
        merged.update(extra)
    return merged


def gate_enabled(view, sleeve_id, extra=None):
    field = SWITCH_FIELDS[sleeve_id]
    ov = _extra_of(view, extra).get(sleeve_id + "_enh2")
    if isinstance(ov, dict) and field in ov:
        return bool(ov[field])
    if isinstance(ov, bool):
        return ov
    return True


def _now_dt(view):
    raw = (view or {}).get("now")
    if isinstance(raw, datetime):
        dt = raw
    elif raw is None:
        return None
    else:
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _parse_ts(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        pass
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _record(view, sleeve_id, gate, refused, **fields):
    rec = {"exp_id": EXP_IDS[sleeve_id], "sleeve": sleeve_id,
           "gate": gate, "switch_on": True,
           "control_decision": "enter",
           "treatment_decision": "refuse" if refused else "enter"}
    rec.update(fields)
    LAST_PAIRED.append(rec)
    ex = (view or {}).get("extra")
    if isinstance(ex, dict):
        try:
            ex.setdefault("enh14_paired", []).append(rec)
        except Exception:
            pass
    return rec


def _bars(view, symbol, tf):
    return ((view or {}).get("bars") or {}).get(f"{symbol}|{tf}") or []


def _last_close(view, symbol, tf):
    bars = _bars(view, symbol, tf)
    if not bars:
        return None
    try:
        px = float(bars[-1].get("c"))
    except (TypeError, ValueError, AttributeError):
        return None
    return px if px > 0 else None


# ------------------------------------------------------------- stale bars
def _bar_stale(view, sleeve_id, intent):
    tf = _STALE_TF[sleeve_id]
    now = _now_dt(view)
    if now is None:
        return False, {}
    bars = _bars(view, intent.get("symbol"), tf)
    if not bars:
        return False, {}
    stamps = [_parse_ts(b.get("t")) for b in bars]
    stamps = [s for s in stamps if s is not None]
    if not stamps:
        return False, {}
    last = stamps[-1]
    if tf == "1Day":
        age_s = (now - last).total_seconds()
        return age_s > _STALE_DAILY_AGE_S, {
            "bar_age_s": round(age_s, 1), "tf": tf}
    spans = [(b - a).total_seconds()
             for a, b in zip(stamps[-6:-1], stamps[-5:])]
    spans = sorted(s for s in spans if s > 0)
    if not spans:
        return False, {}
    span = spans[len(spans) // 2]
    close_age_s = (now - last).total_seconds() - span
    return close_age_s > _STALE_MAX_SPANS * span, {
        "bar_close_age_s": round(close_age_s, 1), "tf": tf,
        "bar_span_s": span}


# ------------------------------------------------------------- beatendown
def _beatendown_reprice(view, intent):
    """Return (refused, fields, new_intent_or_None)."""
    bar_px = _last_close(view, intent.get("symbol"), "1Day")
    if bar_px is None:
        return False, {}, None
    try:
        ctrl_px = float(intent.get("price_hint") or 0)
        ctrl_qty = int(intent.get("qty") or 0)
    except (TypeError, ValueError):
        return False, {}, None
    if ctrl_px <= 0 or bar_px == ctrl_px:
        return False, {}, None
    capital = float(((view or {}).get("slice") or {}).get(
        "capital_usd") or 0)
    if capital <= 0:
        return False, {}, None
    per_name = capital * 0.30 / 10.0  # SLEEVE_CAP / MAX_POSITIONS
    qty = int(per_name // bar_px)
    fields = {"control_px": ctrl_px, "treatment_px": bar_px,
              "control_qty": ctrl_qty, "treatment_qty": qty}
    if qty < 1:
        return True, fields, None
    new = dict(intent)
    new["qty"] = qty
    new["price_hint"] = round(bar_px, 2)
    return False, fields, new


# --------------------------------------------------------------- donchian
def _donchian_chase(view, intent):
    bars = _bars(view, intent.get("symbol"), "1Day")
    if len(bars) < 21:
        return False, {}
    try:
        close = float(intent.get("price_hint") or 0)
        level = max(float(b["h"]) for b in bars[-21:-1])
    except (TypeError, ValueError, KeyError):
        return False, {}
    if close <= 0:
        return False, {}
    from sleeves.donchian import calc_atr, ATR_MULT
    atr = calc_atr(bars)
    if atr is None:
        return False, {}
    refused = (close - level) > ATR_MULT * atr
    return refused, {"close": close, "level": level,
                     "atr": round(atr, 4),
                     "chase_premium": round(close - level, 4)}


# ---------------------------------------------------------------- em_1587
def _em1587_consumed(intent):
    import re
    reason = str(intent.get("reason") or "")
    m = re.search(r"target=\S+ ([0-9]+(?:\.[0-9]+)?)", reason)
    if not m:
        return False, {}
    target = float(m.group(1))
    try:
        spot = float(intent.get("price_hint") or 0)
    except (TypeError, ValueError):
        return False, {}
    if spot <= 0:
        return False, {}
    dm = re.search(r"enter \w+ (long|short)\b", reason)
    if not dm:
        return False, {}
    long_side = dm.group(1) == "long"
    consumed = spot >= target if long_side else spot <= target
    return consumed, {"spot": spot, "target": target,
                      "direction": "long" if long_side else "short"}


# ------------------------------------------------------------ filter core
def filter_entries(sleeve_id, intents, view, extra=None):
    """Apply sleeve_id's ENH2 gate to ENTRY intents (gate ON only).

    Exits pass through untouched, always."""
    if sleeve_id not in SWITCH_FIELDS or sleeve_id == "aurelia_ndx":
        return intents
    if not gate_enabled(view, sleeve_id, extra):
        return intents
    gate = SWITCH_FIELDS[sleeve_id]
    out = []
    seen_entries = set()
    for it in intents or []:
        if it.get("kind") != "entry":
            out.append(it)
            continue
        if sleeve_id in _STALE_TF:
            refused, fields = _bar_stale(view, sleeve_id, it)
            _record(view, sleeve_id, gate, refused,
                    symbol=it.get("symbol"), **fields)
            if not refused:
                out.append(it)
            continue
        if sleeve_id == "beatendown":
            refused, fields, new = _beatendown_reprice(view, it)
            _record(view, sleeve_id, gate, refused,
                    symbol=it.get("symbol"), **fields)
            if refused:
                continue
            out.append(new if new is not None else it)
            continue
        if sleeve_id == "confluence":
            sym = it.get("symbol")
            refused = sym in seen_entries
            _record(view, sleeve_id, gate, refused, symbol=sym,
                    control_decision="enter_duplicate")
            if not refused:
                seen_entries.add(sym)
                out.append(it)
            continue
        if sleeve_id == "donchian":
            refused, fields = _donchian_chase(view, it)
            _record(view, sleeve_id, gate, refused,
                    symbol=it.get("symbol"), **fields)
            if not refused:
                out.append(it)
            continue
        if sleeve_id == "em_1587":
            refused, fields = _em1587_consumed(it)
            _record(view, sleeve_id, gate, refused,
                    symbol=it.get("symbol"), **fields)
            if not refused:
                out.append(it)
            continue
        out.append(it)
    return out


# -------------------------------------------------------------- aurelia_ndx
_AURELIA_OWN = ("QQQ", "TQQQ", "BIL")


def aurelia_ndx_evaluate(view, ctx, delegate):
    """Two-phase complete-plan gate for aurelia_ndx.

    delegate(view, ctx) runs the ported sleeve. When any own-symbol
    leg lacks bars in the view, first run a SHADOW evaluation in a
    throwaway state dir (restoring the strategy module's session set
    afterwards, so the shadow cannot consume the real freeze):
    - shadow emits nothing -> the real run would emit nothing too;
      run it for its journal bookkeeping and return its output.
    - shadow emits a plan -> the plan is partially priced; emitting
      it would consume the sleeve's once-per-session freeze with
      the unpriced leg silently skipped. Defer: return [] WITHOUT
      running the real evaluation, so a later same-session pass
      with complete bars can still execute the full plan.
    With complete bars (or the gate OFF) this is exactly the
    pre-change single evaluation."""
    if not gate_enabled(view, "aurelia_ndx"):
        return delegate(view, ctx)
    bars = (view or {}).get("bars") or {}
    missing = [s for s in _AURELIA_OWN if not bars.get(f"{s}|1Day")]
    if not missing:
        return delegate(view, ctx)
    import tempfile
    import sleeves.aurelia_ndx as strat
    before = set(strat._EMITTED_SESSIONS)
    tmp = tempfile.mkdtemp(prefix="enh14-aurelia-shadow-")
    shadow_ctx = dict(ctx or {})
    shadow_ctx["state_dir"] = tmp
    try:
        shadow = delegate(view, shadow_ctx) or []
    finally:
        strat._EMITTED_SESSIONS.intersection_update(before)
    if not shadow:
        return delegate(view, ctx)
    _record(view, "aurelia_ndx", "complete_plan", True,
            missing_bars=missing,
            control_intents=len(shadow),
            treatment="deferred_unpriced_plan")
    return []
