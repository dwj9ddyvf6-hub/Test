"""ENH2 batch-18 adapter-layer gates (Edge pass, second look).

These gates live at the v3 adapter layer ONLY: the ported strategy
files under sleeves/ are sha256-pinned to v2 and are never edited by
this program. Each gate post-filters ENTRY intents emitted by the
underlying sleeve; exits are never filtered (a held position must
always be able to leave). Every gate is switched per sleeve (default
ON; OFF restores the pre-change rule exactly — the filter becomes a
pass-through) and appends a paired control/treatment record to
LAST_PAIRED (and to view extra["enh2_paired"] when writable) for
every entry candidate it judges, so the shadow control is evaluated
on the same opportunities without ever emitting.

Gates:
- stale_bar_gate (red_day_reversal, rsi_meanrev, rule_1d_cyan_
  smallcap, rule_1d_green_tom, rule_1w_cyan_mom_adx, rule_1w_swing_
  beta_wt, s_1dg, s_1dgp5 on 1Day bars; rule_1h_cyan_raw on 1Hour
  bars): refuse entries whose symbol's newest bar is more than
  MAX_BAR_AGE_DAYS old at decision time. These sleeves' first Edge
  enhancements cured in-signal leaks (range gate, SMA5 exit, debit
  cap, disaster stop, TOM fail-closed, signal-low stop, mom-
  inversion exit, beta sizing, Lazarus fresh-price repricing), but
  none of them ever compares the newest bar's timestamp to the
  decision clock: a dead bars feed leaves the signal bar days old
  and the sleeve still enters at its stale close (measured: every
  one of these sleeves entered on a 9-20 day old bar pre-change).
  The bound is 7 days: the longest legitimate gap (a Friday bar
  read on the Tuesday after a Monday holiday) is ~4.4 days.
- short_leg_spread_gate (rsi_meanrev_options): refuse a call debit
  spread entry when the SHORT leg's quoted spread exceeds
  SHORT_LEG_MAX_SPREAD_FRAC of its mid. The first enhancement caps
  the debit at half the width, and select_debit_spread gates only
  the LONG leg's spread (LIQ_GATE_FRAC = 10%); the debit is priced
  off the short leg's bid while the exit value is priced off its
  ask, so a blown-out short leg makes the exit cost unpriceable at
  entry (measured: short spread/mid = 1.43 still entered).
"""
import re
from datetime import datetime, timezone

MAX_BAR_AGE_DAYS = 7.0
SHORT_LEG_MAX_SPREAD_FRAC = 0.50

LAST_PAIRED = []

_STALE_TF = {
    "red_day_reversal": "1Day",
    "rsi_meanrev": "1Day",
    "rule_1d_cyan_smallcap": "1Day",
    "rule_1d_green_tom": "1Day",
    "rule_1h_cyan_raw": "1Hour",
    "rule_1w_cyan_mom_adx": "1Day",
    "rule_1w_swing_beta_wt": "1Day",
    "s_1dg": "1Day",
    "s_1dgp5": "1Day",
}
_SWITCH_FIELD = {
    "rsi_meanrev_options": "short_leg_spread_gate",
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
    field = _SWITCH_FIELD.get(sleeve_id, "stale_bar_gate")
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
    rec = {"sleeve": sleeve_id, "gate": gate, "switch_on": True,
           "control_decision": "enter",
           "treatment_decision": "refuse" if refused else "enter"}
    rec.update(fields)
    LAST_PAIRED.append(rec)
    ex = (view or {}).get("extra")
    if isinstance(ex, dict):
        try:
            ex.setdefault("enh2_paired", []).append(rec)
        except Exception:
            pass
    return rec


def _bar_stale(view, sleeve_id, intent):
    now = _now_dt(view)
    if now is None:
        return False, {}
    tf = _STALE_TF[sleeve_id]
    bars = ((view or {}).get("bars") or {}).get(
        f"{intent.get('symbol')}|{tf}") or []
    if not bars:
        return False, {}
    last = _parse_ts(bars[-1].get("t"))
    if last is None:
        return False, {}
    age_days = (now - last).total_seconds() / 86400.0
    return age_days > MAX_BAR_AGE_DAYS, {"bar_age_days": round(age_days, 2),
                                         "tf": tf}


def _short_leg_wide(intent, quotes):
    m = re.search(r"short=([A-Z0-9]+)@", str(intent.get("reason") or ""))
    if not m:
        return False, {}
    occ = m.group(1)
    q = (quotes or {}).get(occ) or {}
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
    except (TypeError, ValueError):
        return False, {}
    if bid <= 0 or ask <= 0 or ask < bid:
        return False, {}
    mid = (bid + ask) / 2.0
    frac = (ask - bid) / mid if mid > 0 else 0.0
    return frac > SHORT_LEG_MAX_SPREAD_FRAC, {
        "short_leg": occ, "short_spread_frac": round(frac, 4)}


def filter_entries(sleeve_id, intents, view, quotes=None):
    """Return intents with gated entries removed (gate ON only).

    For rsi_meanrev_options pass the quotes dict the adapter served;
    other sleeves are judged on the view's bars."""
    if sleeve_id == "rsi_meanrev_options":
        if not gate_enabled(view, sleeve_id):
            return intents
        out = []
        for it in intents or []:
            if it.get("kind") != "entry":
                out.append(it)
                continue
            refused, fields = _short_leg_wide(it, quotes)
            _record(view, sleeve_id, "short_leg_spread_gate", refused,
                    symbol=it.get("symbol"), **fields)
            if not refused:
                out.append(it)
        return out
    if sleeve_id not in _STALE_TF or not gate_enabled(view, sleeve_id):
        return intents
    out = []
    for it in intents or []:
        if it.get("kind") != "entry":
            out.append(it)
            continue
        refused, fields = _bar_stale(view, sleeve_id, it)
        _record(view, sleeve_id, "stale_bar_gate", refused,
                symbol=it.get("symbol"), **fields)
        if not refused:
            out.append(it)
    return out
