"""ENH2 batch-26 adapter-layer gates (Edge pass, second look).

These gates live at the v3 adapter layer ONLY: the ported strategy
files under sleeves/ and adapters/ are sha256-pinned to v2
(tests/test_port_b7_blockers.py) and are never edited by this
program. Each gate post-processes ENTRY intents emitted by the
underlying sleeve; exits are never touched (a held position must
always be able to leave). Every gate is switched per sleeve
(default ON; OFF restores the pre-change rule exactly — the filter
becomes a pass-through) and appends a paired control/treatment
record to LAST_PAIRED (and to view extra["enh26_paired"] when
writable) for every entry candidate it judges, so the shadow
control is evaluated on the same opportunities without ever
emitting.

Gates (exp ENH-B26, 2026-10-24):
- snapback / fresh_price_reprice: the strategy sizes entries off
  the signal week's WEEKLY close (row["close"]) — up to a week
  stale at the fill. Cure: reprice the entry at the symbol's
  latest daily close and re-size with the sleeve's own rule
  (1% of slice equity per name); a budget that buys nothing at
  the fresh price takes no position (OBS-1 semantics).
- spx_premium / entry_window_gate: the author's spec enters
  "~10:00 ET" on the week's first trading day, but entry_day_ok
  has no upper bound — a first pass delayed to mid-afternoon
  sells the same prior-week strikes/credit hours after the
  designed moment. Cure: refuse entries at/after 11:00 ET (the
  designed entry hour 10:00-10:59 ET).
- tensor_red_dip / exec_price_reprice: the adapter feeds 1Day
  bars, so entries are sized/priced/stopped off YESTERDAY's
  close while the sleeve's own day_returns prove the symbol is
  red intraday. At a -9% day return the placed stop (0.92 x
  yesterday's close) sits ABOVE the market — an instant stop-out
  at the fill. Cure: reprice at the executable estimate the
  sleeve already consumes, close x (1 + day_return), and
  re-derive qty (0.25% risk / 8% stop), stop and target from it.
- tensor_swing / stale_signal_gate: staged decisions are priced
  at the swing bar's own entry/stop/target; nothing ages the
  staged bar. A decision whose swing_bar_date is more than
  STALE_SIGNAL_DAYS before the session is refused (entries
  only). No bar date on the intent = no evidence = pass.
- ts_momentum_decile / stale_bar_gate: rank_decile drops the
  forming bar but never ages the newest closed bar — a symbol
  whose feed died weeks ago still ranks and is entered at its
  stale close. Cure: refuse entries whose symbol's newest 1Day
  bar is more than STALE_BAR_DAYS old (batch-18 bound: the
  longest legitimate gap, Fri bar read Tue after a Mon holiday,
  is ~4.4 days). Exits (rebalance sells) are never filtered.
"""
import math
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
EXP_ID = "ENH-B26-20261024"
STALE_BAR_DAYS = 7.0
STALE_SIGNAL_DAYS = 7
SPX_ENTRY_CUTOFF_ET = (11, 0)  # designed entry hour is 10:00 ET

LAST_PAIRED = []

_SWITCHES = {
    "snapback": ("snapback_enhance2", "fresh_price_reprice"),
    "spx_premium": ("spx_premium_enhance2", "entry_window_gate"),
    "tensor_red_dip": ("tensor_red_dip_improve2", "exec_price_reprice"),
    "tensor_swing": ("tensor_swing_improve2", "stale_signal_gate"),
    "ts_momentum_decile": ("ts_momentum_decile_improve2", "stale_bar_gate"),
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
    key, field = _SWITCHES[sleeve_id]
    ov = _extra_of(view, extra).get(key)
    if isinstance(ov, dict) and field in ov:
        return bool(ov[field])
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
    rec = {"exp_id": EXP_ID, "sleeve": sleeve_id, "gate": gate,
           "switch_on": True,
           "control_decision": "enter",
           "treatment_decision": "refuse" if refused else "enter"}
    rec.update(fields)
    LAST_PAIRED.append(rec)
    ex = (view or {}).get("extra")
    if isinstance(ex, dict):
        j = ex.get("enh26_paired")
        if isinstance(j, list):
            j.append(rec)
    return rec


def _equity(view):
    sl = (view or {}).get("slice") or {}
    try:
        eq = float(sl.get("capital_usd") or 0)
    except (TypeError, ValueError):
        eq = 0.0
    return eq if eq > 0 else None


def _last_daily_close(view, sym):
    bars = ((view or {}).get("bars") or {}).get(f"{sym}|1Day") or []
    if not bars:
        return None
    try:
        px = float(bars[-1].get("c"))
    except (TypeError, ValueError, AttributeError):
        return None
    return px if px > 0 else None


# ------------------------------------------------------------ snapback
def _snapback(view, intent, extra):
    sym = intent.get("symbol")
    px_old = intent.get("price_hint")
    px_new = _last_daily_close(view, sym)
    if not px_old or not px_new or px_new == float(px_old):
        return False, {}
    eq = _equity(view)
    if eq is not None:
        qty_new = int((eq * 0.01) // px_new)  # sleeve's own sizing rule
    else:
        qty_new = int(int(intent.get("qty") or 0) * float(px_old) / px_new)
    fields = {"symbol": sym, "control_px": float(px_old),
              "treatment_px": px_new, "control_qty": int(intent.get("qty") or 0),
              "treatment_qty": qty_new}
    if qty_new < 1:
        return True, fields  # budget buys nothing at the fresh price
    intent["qty"] = qty_new
    intent["price_hint"] = round(px_new, 2)
    return False, fields


# ------------------------------------------------------------ spx_premium
def _spx_window(view, intent, extra):
    now = _now_dt(view)
    if now is None:
        return False, {}
    et = now.astimezone(ET)
    late = (et.hour, et.minute) >= SPX_ENTRY_CUTOFF_ET
    return late, {"et_time": et.strftime("%H:%M"),
                  "cutoff_et": "%02d:%02d" % SPX_ENTRY_CUTOFF_ET}


# ------------------------------------------------------------ tensor_red_dip
def _day_returns(view, extra):
    ex = _extra_of(view, extra)
    dr = ex.get("day_returns")
    if isinstance(dr, dict) and dr:
        return dr
    bundle = (view or {}).get("tensor") or {}
    sub = ((bundle.get("sleeves") or {}).get("tensor_red_dip") or {})
    dr = sub.get("day_returns")
    return dr if isinstance(dr, dict) else {}


def _red_dip(view, intent, extra):
    sym = intent.get("symbol")
    r = _day_returns(view, extra).get(sym)
    px_old = intent.get("price_hint")
    if r is None or not px_old:
        return False, {}
    try:
        r = float(r)
    except (TypeError, ValueError):
        return False, {}
    px_new = float(px_old) * (1.0 + r)
    fields = {"symbol": sym, "day_return": r,
              "control_px": float(px_old), "treatment_px": round(px_new, 4),
              "control_qty": int(intent.get("qty") or 0),
              "control_stop": intent.get("stop_price")}
    if px_new <= 0:
        fields["treatment_qty"] = 0
        fields["treatment_stop"] = None
        return True, fields
    eq = _equity(view)
    if eq is not None:
        # sleeve's own size_qty: floor(risk$ / (px x 8% stop))
        qty_new = math.floor((eq * 0.0025) / (px_new * 0.08))
        qty_new = int(qty_new) if qty_new >= 1 else 0
    else:
        qty_new = int(int(intent.get("qty") or 0) * float(px_old) / px_new)
    stop_new = round(px_new * 0.92, 2)
    target_new = round(px_new * 1.03, 2)
    fields["treatment_qty"] = qty_new
    fields["treatment_stop"] = stop_new
    if qty_new < 1:
        return True, fields
    intent["qty"] = qty_new
    intent["price_hint"] = round(px_new, 2)
    intent["stop_price"] = stop_new
    for rule in intent.get("exit_rules") or []:
        if rule.get("kind") == "stop":
            rule["value"] = stop_new
        elif rule.get("kind") == "target":
            rule["value"] = target_new
    return False, fields


# ------------------------------------------------------------ tensor_swing
def _tensor_swing_stale(view, intent, extra):
    m = re.search(r"swing_bar_date=(\d{4}-\d{2}-\d{2})",
                  str(intent.get("reason") or ""))
    now = _now_dt(view)
    if not m or now is None:
        return False, {}
    try:
        bar_date = datetime.fromisoformat(m.group(1)).date()
    except ValueError:
        return False, {}
    age = (now.astimezone(ET).date() - bar_date).days
    return age > STALE_SIGNAL_DAYS, {"symbol": intent.get("symbol"),
                                     "swing_bar_date": m.group(1),
                                     "bar_age_days": age}


# ------------------------------------------------------------ ts_momentum_decile
def _ts_stale(view, intent, extra):
    now = _now_dt(view)
    if now is None:
        return False, {}
    bars = ((view or {}).get("bars") or {}).get(
        f"{intent.get('symbol')}|1Day") or []
    if not bars:
        return False, {}
    last = _parse_ts(bars[-1].get("t"))
    if last is None:
        return False, {}
    age_days = (now - last).total_seconds() / 86400.0
    return age_days > STALE_BAR_DAYS, {
        "symbol": intent.get("symbol"), "bar_age_days": round(age_days, 2)}


_CHECKS = {
    "snapback": ("fresh_price_reprice", _snapback),
    "spx_premium": ("entry_window_gate", _spx_window),
    "tensor_red_dip": ("exec_price_reprice", _red_dip),
    "tensor_swing": ("stale_signal_gate", _tensor_swing_stale),
    "ts_momentum_decile": ("stale_bar_gate", _ts_stale),
}


def filter_entries(sleeve_id, intents, view, extra=None):
    """Return intents with gated entries removed / repriced (gate ON
    only). Exits pass through untouched, always."""
    if sleeve_id not in _CHECKS or not gate_enabled(view, sleeve_id, extra):
        return intents
    gate, check = _CHECKS[sleeve_id]
    out = []
    for intent in intents or []:
        if not isinstance(intent, dict) or intent.get("kind") != "entry":
            out.append(intent)
            continue
        refused, fields = check(view, intent, extra)
        _record(view, sleeve_id, gate, refused, **fields)
        if not refused:
            out.append(intent)
    return out
