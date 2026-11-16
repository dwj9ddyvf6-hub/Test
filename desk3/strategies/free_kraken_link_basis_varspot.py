"""FREE_KRAKEN_LINK_BASIS_VARSPOT — spot-expression variation of
free_kraken_link_basis (PF-SPOT-VARIATIONS-20261116; desk full
audit escalation 3, owner ruling 2026-11-16 09:22 ET: "Fix them").

VARIATION DOCTRINE: an ADDITIONAL sleeve with its own id,
falsifier and grade path (config/pf_spot_variations_20261116.json,
candidate CAND-CTB-SPOT-LINK). The parent free_kraken_link_basis
is byte-untouched and keeps failing closed by name at the PF_
seam.

SIGNAL (unchanged from the parent): the parent's own basis
reading — basis_bps on the newest completed aligned 4h pair,
(perp_close - spot_close) / spot_close * 10000, computed by the
parent's basis_decision() on the KrakenProducer basis series the
desk already serves (parent sleeve key in kraken_inputs). The PF
instrument carries information spot alone does not — the perp leg
of the pair — and the variation does NOT drop it: the basis
series remains the signal, exactly as registered in
CAND-CTB-SPOT-LINK ("The signal source (unchanged)"). What
changes is only the TRADED instrument: LINK/USD spot on Alpaca
(listed) instead of PF_LINKUSD (not an Alpaca instrument).

EXPRESSION (the candidate's registered trade shape, verbatim in
substance): Alpaca serves no crypto spot shorting, so the
parent's side (short the perp on a perp PREMIUM >= +25bps) is a
named no-trade in spot — never a fabricated short. The spot leg
trades the direction spot can lawfully take: LONG spot when the
perp trades at a DISCOUNT beyond the same band
(basis_bps <= -25), exit when the basis normalizes to >= -5bps
(the mirror of the parent's +5 exit) or after the parent's 16h
hold. QTY is the parent's QTY = 1.

PRICING: no spot quote is served for LINK/USD on this desk (the
kraken.quote the parent reads is the PF futures ticker). The
variation prices at the served spot tape's newest bar close,
supplied by its adapter as extra["spot_reference"], and requires
that reference fresh (newest bar opened within two 4h bars of
now) — the PF quote's bid/ask spread information has no spot
served equivalent; that gap is named here, not silently dropped.

Position state arrives keyed by the traded symbol "LINK/USD".
Fail closed on missing, stale or malformed inputs; never raise.
"""
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

from desk3.strategies import free_kraken_link_basis as _parent

PARENT_ID = "free_kraken_link_basis"
INSTRUMENT = "LINK/USD"
PF_INSTRUMENT = _parent.INSTRUMENT  # PF_LINKUSD
ENTRY_BASIS_BPS = _parent.ENTRY_BASIS_BPS      # 25, the band
EXIT_BASIS_BPS = _parent.EXIT_BASIS_BPS        # 5, normalization
HOLD = _parent.HOLD                            # 16h
QTY = _parent.QTY                              # 1
BAR_SECONDS = _parent.BAR_SECONDS
REF_MAX_AGE = timedelta(seconds=2 * BAR_SECONDS)

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_link_basis_varspot", cadence_s=3600,
    monitor_only=False, universe=(INSTRUMENT,), state_schema={},
    risk_pct=None)


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _reference(extra, now):
    """(price, fresh) from the adapter-supplied spot tape reference."""
    ref = (extra or {}).get("spot_reference") or {}
    try:
        price = float(ref.get("price"))
        opened = _parse(ref.get("bar_t"))
    except (TypeError, ValueError, AttributeError):
        return None, False
    if price <= 0:
        return None, False
    return price, (now - opened) <= REF_MAX_AGE


def _position(extra, slice_state):
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


def spot_decision(series, extra, now):
    """The variation's decision on the parent's basis reading:
    entry_ready_long (discount beyond band),
    named_no_trade_premium_side (the parent's own entry condition;
    un-expressible in spot, recorded by name), or awaiting."""
    book = (extra or {}).get("basis") or {}
    decision = _parent.basis_decision(series, {}, now,
                                      instrument=PF_INSTRUMENT)
    basis_bps = decision.get("basis_bps")
    try:
        aligned = int(book.get("aligned"))
        required = int(book.get("required"))
        ready = required > 0 and aligned == required
    except (TypeError, ValueError):
        ready = False
    out = {**decision, "basis_ready": ready,
           "expression": "spot_long_discount_only"}
    if basis_bps is None:
        return {**out, "status": decision.get("status") or "BLOCKED_INPUT"}
    if basis_bps >= ENTRY_BASIS_BPS:
        return {**out, "status": "named_no_trade_premium_side",
                "reason": "Perp premium basis %.2fbps >= entry %dbps is "
                          "the parent's short side; Alpaca serves no "
                          "crypto spot shorting, so the spot expression "
                          "records a named no-trade (CAND-CTB-SPOT-LINK), "
                          "never a fabricated short." % (basis_bps,
                                                          ENTRY_BASIS_BPS)}
    if basis_bps <= -ENTRY_BASIS_BPS:
        return {**out, "status": "entry_ready_long", "side": "buy",
                "reason": "Perp discount basis %.2fbps <= -%dbps: long "
                          "the spot leg (CAND-CTB-SPOT-LINK registered "
                          "form)." % (basis_bps, ENTRY_BASIS_BPS)}
    return {**out, "status": "QUALIFIED/AWAITING SIGNAL",
            "reason": "Basis %.2fbps inside the +/-%dbps band."
                      % (basis_bps, ENTRY_BASIS_BPS)}


class FreeKrakenLinkBasisVarspot(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        try:
            now = datetime.fromtimestamp(float(context.now),
                                         tz=timezone.utc)
        except (TypeError, ValueError):
            return []
        book = extra.get("basis") or {}
        series = extra.get("series") or book.get("series") or []
        price, fresh = _reference(extra, now)
        qty, entry_time = _position(extra, slice_state)
        if qty > 0:
            if not fresh:
                return []
            decision = spot_decision(series, extra, now)
            basis_bps = decision.get("basis_bps")
            normalized = basis_bps is not None \
                and basis_bps >= -EXIT_BASIS_BPS
            hold_due = entry_time is not None and now >= entry_time + HOLD
            if not (normalized or hold_due):
                return []
            why = ("basis normalized to %.2fbps >= exit -%dbps"
                   % (basis_bps, EXIT_BASIS_BPS)) if normalized else \
                  ("16h hold elapsed since %s" % entry_time.isoformat())
            return [Intent(
                "exit", INSTRUMENT, qty_hint=int(abs(qty)),
                price_hint=round(float(price), 6),
                reason="free_kraken_link_basis_varspot sell spot long at "
                       "spot tape close (sell_to_close); %s; event=%s"
                       % (why, decision.get("event_id") or "hold"))]
        if qty < 0:
            return []  # spot book is long-only; fail closed
        decision = spot_decision(series, extra, now)
        if decision.get("status") != "entry_ready_long":
            return []
        if not decision.get("basis_ready") or not fresh:
            return []
        return [Intent(
            "enter", INSTRUMENT, qty_hint=QTY,
            price_hint=round(float(price), 6),
            reason="free_kraken_link_basis_varspot LONG spot (buy_to_open) "
                   "1 LINK/USD at spot tape close; basis_bps=%.2f <= -%d "
                   "(perp discount beyond band, CAND-CTB-SPOT-LINK); "
                   "event=%s" % (decision["basis_bps"], ENTRY_BASIS_BPS,
                                 decision["event_id"]))]


def signal(bars, slice_state, context):
    return FreeKrakenLinkBasisVarspot().signal(bars, slice_state, context)
