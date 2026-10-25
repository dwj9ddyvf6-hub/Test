"""FREE_KRAKEN_ADA_BASIS — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_kraken_paper.py run(): the basis rows read a
Kraken history book (perpetual vs spot alignment) that on the old desk
was FENCED — the history collector was not imported into Femto, so
every basis row reported BLOCKED_INPUT with the fence reason, and
basis rows were explicitly excluded from order placement even when
ready. The lean port originally preserved exactly that.

UNFENCE-119 (owner ruling 2026-10-24 10:38 ET): the Decision #119
monitor-only fence is REVERSED for this sleeve in muse-desk-v2 —
CONFIG.monitor_only=False and the adapter routes signal() intents
to the dispatcher instead of journaling monitor_status.

DESIGNED-ORDER-LOGIC (DESIGNED-ORDER-LOGIC.md §1, owner ruling
2026-10-24 11:41 ET "Fix that defect"): no basis order logic existed
in any source to port, so the logic below was AUTHORED to the locked
design. These constants were authored under the owner's 2026-10-24
'Fix that defect' ruling: ENTRY_BASIS_BPS = 25, EXIT_BASIS_BPS = 5,
HOLD_HOURS = 16, QTY = 1. Design: on completed aligned 4h pairs only
(pair t + 4h <= now), basis_bps on the newest completed pair =
(perp_close - spot_close) / spot_close * 10000. FLAT and basis READY
(aligned == required > 0 in extra["basis"]) and basis_bps >= 25 and a
valid live quote (bid > 0, bid <= ask) -> short QTY 1 PF_ADAUSD at the
bid. SHORT OPEN: exit (cover at the ask) when basis_bps <= 5 on the
newest completed pair OR now >= entry_time + 16h; a valid quote is
required, else no exit. One open position at a time; fail closed on
missing, stale, crossed, or malformed inputs; never raise. Series
arrives via extra["basis"]["series"] (or extra["series"]); the quote
arrives via extra["quote"] — both produced at warm time by
runtime/kraken_warm.py, never fetched during evaluation.
basis_status() is retained as a status helper, fed from
context.extra["basis"] when the producer supplies it.

VIRTUAL BOOK MAPPING: sizing goes through the existing slice
machinery (config slice capital_usd = 10000 for this sleeve).
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

FENCE = ("kraken history collector fenced in Femto (Decision #119); "
         "basis history was not collected.")

INSTRUMENT = "PF_ADAUSD"
SPOT = "ADAUSD"
ENTRY_BASIS_BPS = 25
EXIT_BASIS_BPS = 5
HOLD_HOURS = 16
QTY = 1
BAR_SECONDS = 4 * 3600
HOLD = timedelta(hours=HOLD_HOURS)

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_ada_basis", cadence_s=3600, monitor_only=False,
    universe=("PF_ADAUSD",), state_schema={}, risk_pct=None)


def basis_status(extra=None):
    book = (extra or {}).get("basis") or {}
    decision = book.get("decision") or {}
    aligned, required = book.get("aligned"), book.get("required")
    status = decision.get("status")
    reason = decision.get("reason")
    if not status:
        try:
            ready = required is not None and int(required) > 0 \
                and int(aligned) == int(required)
        except (TypeError, ValueError):
            ready = False
        status = "READY" if ready else "BLOCKED_INPUT"
        reason = ("Designed basis logic armed: short 1 PF_ADAUSD at "
                  "basis >= 25bps, exit at <= 5bps or after 16h."
                  if ready else FENCE)
    return {
        "id": "FREE_KRAKEN_ADA_BASIS_V1", "instrument": "PF_ADAUSD",
        "spot": "ADAUSD", "quote_currency": "USD",
        "aligned": aligned, "required": required,
        "status": status, "reason": reason,
    }


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _pair_time(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        pass
    try:
        return _parse(value)
    except Exception:
        return None


def _completed_pairs(series):
    rows = []
    for row in series or []:
        try:
            t = _pair_time(row["t"])
            spot = float(row["spot_close"])
            perp = float(row["perp_close"])
        except (KeyError, TypeError, ValueError, AttributeError):
            continue  # malformed pair: fail closed, never raise
        if t is None or spot <= 0:
            continue
        rows.append({"t": t, "spot_close": spot, "perp_close": perp})
    rows.sort(key=lambda r: r["t"])
    return rows


def _quote_valid(quote):
    try:
        bid, ask = float((quote or {}).get("bid")), float((quote or {}).get("ask"))
    except (TypeError, ValueError, AttributeError):
        return False, None, None
    return (bid > 0 and bid <= ask), bid, ask


def _event_id(instrument, pair, basis_bps):
    payload = json.dumps(
        {"instrument": instrument, "pair_t": pair["t"].isoformat(),
         "spot_close": pair["spot_close"], "perp_close": pair["perp_close"],
         "basis_bps": round(float(basis_bps), 6)},
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def basis_decision(series, quote, now, *, instrument=INSTRUMENT):
    """Designed basis decision (family style of
    sleeves/free_kraken_ada_breakdown.py): completed aligned pairs
    only; basis_bps on the newest completed pair."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    quote_ok, bid, ask = _quote_valid(quote)
    done = [r for r in _completed_pairs(series)
            if r["t"] + timedelta(seconds=BAR_SECONDS) <= now]
    if not done:
        return {"status": "BLOCKED_INPUT",
                "reason": "No completed aligned spot/perp pair "
                          "(pair t + 4h <= now required).",
                "basis_bps": None, "quote_ok": quote_ok}
    newest = done[-1]
    basis_bps = (newest["perp_close"] - newest["spot_close"]) \
        / newest["spot_close"] * 10000.0
    base = {"basis_bps": basis_bps, "pair_t": newest["t"].isoformat(),
            "spot_close": newest["spot_close"],
            "perp_close": newest["perp_close"],
            "event_id": _event_id(instrument, newest, basis_bps),
            "quote_ok": quote_ok, "decision_at": now.isoformat()}
    if basis_bps >= ENTRY_BASIS_BPS:
        return {**base, "status": "entry_ready", "side": "sell",
                "reason": "Perp premium basis %.2fbps >= entry %dbps."
                          % (basis_bps, ENTRY_BASIS_BPS)}
    return {**base, "status": "QUALIFIED/AWAITING SIGNAL",
            "reason": "Basis %.2fbps below entry %dbps."
                      % (basis_bps, ENTRY_BASIS_BPS)}


def _position(extra, slice_state):
    """(qty, entry_time) from sleeve_state in any served shape:
    flat {SYM: {qty, entry_due_at|opened_at}}, nested
    {SYM: {position: {...}}}, sleeve_state_flat, or slice_state."""
    candidates = []
    for source in (extra.get("sleeve_state") or {},
                   extra.get("sleeve_state_flat") or {}):
        if isinstance(source, dict) and INSTRUMENT in source:
            candidates.append(source[INSTRUMENT])
    if isinstance(slice_state, dict) and INSTRUMENT in slice_state:
        candidates.append(slice_state[INSTRUMENT])
    for pos in candidates:
        if isinstance(pos, dict) and isinstance(pos.get("position"), dict):
            pos = pos["position"]
        if isinstance(pos, (int, float)):
            return float(pos), None
        if not isinstance(pos, dict):
            continue
        try:
            qty = float(pos.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        entry_time = None
        for key in ("entry_due_at", "opened_at", "entry_time", "entry_at"):
            if pos.get(key):
                try:
                    entry_time = _parse(pos[key])
                except Exception:
                    entry_time = None
                break
        return qty, entry_time
    return 0.0, None


class FreeKrakenBasis(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        try:
            now = datetime.fromtimestamp(float(context.now),
                                         tz=timezone.utc)
        except (TypeError, ValueError):
            return []
        quote = extra.get("quote") or {}
        quote_ok, bid, ask = _quote_valid(quote)
        book = extra.get("basis") or {}
        series = extra.get("series") or book.get("series") or []
        qty, entry_time = _position(extra, slice_state)
        if qty < 0:
            # SHORT OPEN: exit on normalization or the 16h hold;
            # a valid live quote is required, else hold (fail closed).
            if not quote_ok:
                return []
            decision = basis_decision(series, quote, now)
            basis_bps = decision.get("basis_bps")
            normalized = basis_bps is not None \
                and basis_bps <= EXIT_BASIS_BPS
            hold_due = entry_time is not None and now >= entry_time + HOLD
            if not (normalized or hold_due):
                return []
            why = ("basis normalized to %.2fbps <= exit %dbps"
                   % (basis_bps, EXIT_BASIS_BPS)) if normalized else \
                  ("16h hold elapsed since %s" % entry_time.isoformat())
            return [Intent(
                "exit", INSTRUMENT, qty_hint=int(abs(qty)),
                price_hint=round(float(ask), 6),
                reason="free_kraken_ada_basis cover short at live ask "
                       "(buy_to_close); %s; event=%s"
                       % (why, decision.get("event_id") or "hold"))]
        if qty > 0:
            return []  # designed book is short-only; never add
        # FLAT: READY basis + premium + valid quote -> short 1 contract.
        try:
            aligned = int(book.get("aligned"))
            required = int(book.get("required"))
        except (TypeError, ValueError):
            return []
        if not (required > 0 and aligned == required):
            return []
        if not quote_ok:
            return []
        decision = basis_decision(series, quote, now)
        if decision.get("status") != "entry_ready":
            return []
        return [Intent(
            "enter", INSTRUMENT, qty_hint=QTY,
            price_hint=round(float(bid), 6),
            reason="free_kraken_ada_basis SHORT (sell_to_open) 1 "
                   "PF_ADAUSD at live bid; basis_bps=%.2f >= %d; event=%s"
                   % (decision["basis_bps"], ENTRY_BASIS_BPS,
                      decision["event_id"]))]


def signal(bars, slice_state, context):
    return FreeKrakenBasis().signal(bars, slice_state, context)
