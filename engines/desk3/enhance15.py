"""ENH2 batch-15 adapter-layer gates (Edge pass, second look).

These gates live at the v3 adapter layer ONLY: the ported strategy
files under sleeves/ and adapters/ are sha256-pinned to v2 and are
never edited by this program. Each gate post-filters ENTRY intents
emitted by the underlying sleeve; exits are never filtered (a held
position must always be able to leave). Every gate is switched per
sleeve (default ON; OFF restores the pre-change rule exactly — the
filter becomes a pass-through) and appends a paired
control/treatment record to LAST_PAIRED whenever it sees an entry
candidate, so the shadow control is evaluated on the same
opportunities without ever emitting.

Gates:
- ema_vwap / stale_bar_gate: refuse entries whose symbol's newest
  daily bar is more than STALE_BAR_DAYS old at decision time. The
  sleeve decides on the last closed daily bar; a dead feed leaves
  that bar days old and the sleeve still enters at its close.
- ema_vwap_options / short_leg_spread_gate: refuse a call debit
  spread entry when the SHORT leg's quoted spread exceeds
  SHORT_LEG_MAX_SPREAD_FRAC of its mid. Entry debit is priced off
  the short leg's bid only, while the conservative exit value is
  priced off its ask; the strategy gates only the long leg
  (LIQ_GATE_FRAC = 10%). A blown-out short leg makes the exit cost
  unpriceable at entry.
- free_kraken_ada_basis / pair_freshness_gate: refuse entries when
  the newest completed aligned pair completed more than
  PAIR_MAX_AGE_S ago. The strategy requires pair_t + 4h <= now but
  puts no upper bound on pair age, so a basis print from a dead
  collector still fires a short days later.
"""
import re
from datetime import datetime, timezone

STALE_BAR_DAYS = 10.0
SHORT_LEG_MAX_SPREAD_FRAC = 0.50
PAIR_MAX_AGE_S = 8 * 3600.0  # two 4h bars
BAR_SECONDS = 4 * 3600

LAST_PAIRED = []

_SWITCHES = {
    "ema_vwap": ("ema_vwap_enh2", "stale_bar_gate"),
    "ema_vwap_options": ("ema_vwap_options_enh2", "short_leg_spread_gate"),
    "free_kraken_ada_basis": ("free_kraken_ada_basis_enh2", "pair_freshness_gate"),
    "free_kraken_link_basis": ("free_kraken_link_basis_enh2", "pair_freshness_gate"),
    "free_kraken_enj_spot": ("free_kraken_enj_spot_enh2", "book_freshness_gate"),
}

BOOK_MAX_AGE_S = 3600.0  # one cadence


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


def _record(sleeve_id, gate, refused, **fields):
    rec = {"sleeve": sleeve_id, "gate": gate, "switch_on": True,
           "control_decision": "enter",
           "treatment_decision": "refuse" if refused else "enter"}
    rec.update(fields)
    LAST_PAIRED.append(rec)
    return rec


def _pair_stale(view, intent, extra=None):
    now = _now_dt(view)
    if now is None:
        return False, {}
    ex = _extra_of(view, extra)
    book = ex.get("basis") or {}
    series = ex.get("series") or book.get("series") or []
    newest = None
    for row in series:
        if not isinstance(row, dict):
            continue
        t = _parse_ts(row.get("t"))
        if t is None:
            continue
        done = t.timestamp() + BAR_SECONDS
        if done <= now.timestamp() and (newest is None or done > newest):
            newest = done
    if newest is None:
        return False, {}
    age = now.timestamp() - newest
    return age > PAIR_MAX_AGE_S, {"pair_age_s": round(age, 1)}


def _book_stale(view, intent, extra=None):
    now = _now_dt(view)
    if now is None:
        return False, {}
    book = _extra_of(view, extra).get("book") or {}
    stamps = []
    for side in ("bids", "asks"):
        for row in book.get(side) or []:
            try:
                stamps.append(float(row[2]))
            except (TypeError, ValueError, IndexError, KeyError):
                continue
    if not stamps:
        return False, {}
    age = now.timestamp() - max(stamps)
    return age > BOOK_MAX_AGE_S, {"book_age_s": round(age, 1)}


def _ema_vwap_stale(view, intent, extra=None):
    now = _now_dt(view)
    if now is None:
        return False, {}
    bars = ((view or {}).get("bars") or {}).get(f"{intent.get('symbol')}|1Day") or []
    if not bars:
        return False, {}
    last = _parse_ts(bars[-1].get("t"))
    if last is None:
        return False, {}
    age_days = (now - last).total_seconds() / 86400.0
    return age_days > STALE_BAR_DAYS, {"bar_age_days": round(age_days, 2)}


def _short_leg_wide(view, intent, extra=None):
    reason = str(intent.get("reason") or "")
    m = re.search(r"short=([A-Z0-9]+)@", reason)
    if not m:
        return False, {}
    occ = m.group(1)
    quotes = _extra_of(view).get("quotes") or {}
    q = quotes.get(occ) or {}
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


_CHECKS = {
    "ema_vwap": ("stale_bar_gate", _ema_vwap_stale),
    "ema_vwap_options": ("short_leg_spread_gate", _short_leg_wide),
    "free_kraken_ada_basis": ("pair_freshness_gate", _pair_stale),
    "free_kraken_link_basis": ("pair_freshness_gate", _pair_stale),
    "free_kraken_enj_spot": ("book_freshness_gate", _book_stale),
}


def filter_entries(sleeve_id, intents, view, extra=None):
    """Return intents with gated entries removed (gate ON only)."""
    if sleeve_id not in _CHECKS or not gate_enabled(view, sleeve_id, extra):
        return intents
    gate, check = _CHECKS[sleeve_id]
    out = []
    seen_spreads = set()
    for it in intents or []:
        if it.get("kind") != "entry":
            out.append(it)
            continue
        refused, fields = check(view, it, extra)
        key = (it.get("reason"), refused)
        if key not in seen_spreads:
            seen_spreads.add(key)
            _record(sleeve_id, gate, refused, symbol=it.get("symbol"), **fields)
        if not refused:
            out.append(it)
    return out
