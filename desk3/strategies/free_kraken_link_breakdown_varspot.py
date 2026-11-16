"""FREE_KRAKEN_LINK_BREAKDOWN_VARSPOT -- spot-expression variation
of free_kraken_link_breakdown (PF-SPOT-VARIATIONS-20261116; desk
full audit escalation 3, owner ruling 2026-11-16 09:22 ET:
"Fix them").

VARIATION DOCTRINE: an ADDITIONAL sleeve with its own id,
falsifier and grade path (config/pf_spot_variations_20261116.json,
candidate CAND-CTB-SPOT-LINK). The parent is byte-untouched and
keeps failing closed by name at the PF_ seam.

SIGNAL (the parent's construction, spot instrument substituted):
the parent's breakdown_decision() -- on completed 4h bars, the
signal bar is the latest whose entry is due (open(i+2)); entry
fires when the signal close is below the prior 20 bars' low --
computed on the desk's served LINK/USD spot 4h tape instead of
PF_LINKUSD bars. The PF bars carry no information the spot tape
does not for this construction: the perp tracks spot (the H1
conveyor measured the LINK basis range at -21.7..+21.2bps over
the 546-bar overlap, 2026-11-14), and the decision function,
window, shift and 16h hold are the parent's own, imported
unedited. The parent's ENH-20261024 breakdown-validity gate is a
gate on a short fill price; it has no spot object to gate and
is named here as not carried, not silently dropped.

EXPRESSION -- AMENDED 2026-11-16 (MAKE-IT-WORK Decision C,
PF-PAIRED-RV-20261116; owner ruling 2026-11-16 12:46 ET: "Make
it work"): the breakdown side is SHORT and Alpaca serves no
crypto spot shorting, so the original registered form recorded
an entry_ready decision as a NAMED NO-TRADE and the sleeve
never traded. Under Decision C the same entry_ready instead
enters the PAIRED RELATIVE-VALUE expression the escalation
record named as the standing alternative: LONG BTC/USD spot
(Alpaca-listed, the desk's existing route) at the same due time
the short would have entered, sized by this sleeve's own slice
(fractional qty = slice cash net of the per-side fee over the
BTC price; the dispatcher's normal slice check still gates the
intent), held for the parent's own 16h hold clock, then the
full held BTC quantity exits through the normal intent path.
The signal computation is NOT edited: spot_decision carries the
parent's decision fields unchanged and only the expression
status changed. The pure-short form is RETAINED in the registry
record as the named future-venue form -- it becomes the trade
form only on a venue the owner authorizes; it is not deleted,
and no fabricated short is ever emitted here.

FAIL CLOSED: if the anchor leg cannot be entered -- the BTC/USD
served tape is missing or stale under the same freshness
discipline the basis variations apply to their spot reference
(newest bar opened within two 4h bars of now), or the slice
sizes to nothing -- the sleeve records a NAMED ABSTENTION
(extra["paired_rv_abstentions"], status
named_abstention_anchor_stale / named_abstention_slice) and
emits zero intents. No short signal active = flat, zero intents.

GRADING (spread): per event, BTC/USD's return over the 16h
holding window minus LINK/USD's return over the same window,
net of the desk's Alpaca crypto fee convention -- 10bp per side
on the traded BTC leg (desk3/aster_crypto.py FEE=0.001;
desk3/t474u_crypto.py FEE_1X_CRYPTO=0.001, "fee 10bp one-way";
aster_sleeves/_common.py FEE = Decimal("0.001"), "10 bps each
side (crypto_rules.json)"). spread_grade() below is the grading
primitive; the registry grade path grades from this sleeve's
own BTC fills in the dispatcher record plus the LINK/USD served
spot tape over the same window.
"""
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

from desk3.strategies import free_kraken_link_breakdown as _parent

PARENT_ID = "free_kraken_link_breakdown"
SLEEVE_ID = "free_kraken_link_breakdown_varspot"
INSTRUMENT = "LINK/USD"
PF_INSTRUMENT = _parent.INSTRUMENT  # PF_LINKUSD

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_link_breakdown_varspot", cadence_s=3600,
    universe=(INSTRUMENT, "BTC/USD"), state_schema={"position": "dict|None"},
    risk_pct=None)

ANCHOR = "BTC/USD"
# Fee convention (cited, not invented): the desk's crypto code
# prices Alpaca crypto at 10bp per side -- desk3/aster_crypto.py
# FEE=0.001, desk3/t474u_crypto.py FEE_1X_CRYPTO=0.001 ("fee 10bp
# one-way"), aster_sleeves/_common.py FEE = Decimal("0.001")
# "# 10 bps each side (crypto_rules.json)". The paired leg trades
# ONE instrument (BTC/USD, entry + exit), so a round trip carries
# 2 x FEE_PER_SIDE; the signal asset leg is measured on its served
# tape and is not traded, so it carries no fee.
FEE_PER_SIDE = 0.001
BAR_SECONDS = _parent.BAR_SECONDS
HOLD = _parent.HOLD
REF_MAX_AGE = timedelta(seconds=2 * BAR_SECONDS)


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _anchor_reference(bars, now):
    """(price, fresh) from the served BTC/USD spot tape: newest
    bar's close, fresh under the same discipline the basis
    variations apply to their spot reference (newest bar opened
    within two 4h bars of now; REF_MAX_AGE in the basis
    variations)."""
    best = None
    for b in bars or []:
        try:
            t = float(b["t"])
            c = float(b["c"])
        except (KeyError, TypeError, ValueError):
            continue
        if c <= 0:
            continue
        if best is None or t > best[0]:
            best = (t, c)
    if best is None:
        return None, False
    opened = datetime.fromtimestamp(best[0], tz=timezone.utc)
    return best[1], (timedelta(0) <= now - opened <= REF_MAX_AGE)


def _position(extra, slice_state):
    """Held BTC/USD quantity + entry time, in the basis
    variations' sleeve_state shapes (keyed by the traded symbol)."""
    candidates = []
    for source in (extra.get("sleeve_state") or {},
                   extra.get("sleeve_state_flat") or {}):
        if isinstance(source, dict) and ANCHOR in source:
            candidates.append(source[ANCHOR])
    if isinstance(slice_state, dict) and ANCHOR in slice_state:
        candidates.append(slice_state[ANCHOR])
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


def _slice_cash(extra, context):
    for v in ((extra or {}).get("cash"), getattr(context, "equity", None)):
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f > 0:
            return f
    return None


def paired_qty(price, cash):
    """Fractional BTC quantity sized by the sleeve's own slice:
    slice cash net of the per-side fee over the anchor price (the
    aster_crypto sizing form, qty = cash*(1-FEE)/price). The
    dispatcher's normal slice check still gates the intent."""
    if not price or not cash or float(price) <= 0 or float(cash) <= 0:
        return None
    q = float(cash) * (1.0 - FEE_PER_SIDE) / float(price)
    return q if q > 0 else None


def spread_grade(btc_entry, btc_exit, signal_entry, signal_exit):
    """Per-event spread grade (PF-PAIRED-RV-20261116): BTC/USD
    return over the holding window minus the signal asset's
    return over the same window, net of the desk's crypto fee
    convention above (round trip on the traded BTC leg only)."""
    try:
        be, bx, se, sx = (float(btc_entry), float(btc_exit),
                          float(signal_entry), float(signal_exit))
    except (TypeError, ValueError):
        return None
    if min(be, bx, se, sx) <= 0:
        return None
    btc_ret = bx / be - 1.0
    sig_ret = sx / se - 1.0
    gross = btc_ret - sig_ret
    fees = 2.0 * FEE_PER_SIDE
    return {"btc_return": btc_ret, "signal_return": sig_ret,
            "gross_spread": gross, "fee_per_side": FEE_PER_SIDE,
            "round_trip_fees": fees, "net_spread": gross - fees}


def _record(extra, treatment, decision, **kw):
    try:
        rec = {"sleeve": SLEEVE_ID, "gate": "paired_rv_expression",
               "gate_on": True,
               "signal_event_id": decision.get("signal_event_id"),
               "entry_due_at": decision.get("entry_due_at"),
               "control_decision": "enter_short_pf",
               "treatment_decision": treatment}
        rec.update(kw)
        (extra.setdefault("enhance_paired", [])).append(rec)
        if treatment.startswith("named_abstention"):
            (extra.setdefault("paired_rv_abstentions", [])).append(
                {**rec, "status": treatment})
    except Exception:
        pass


def spot_decision(rows, now):
    """Parent breakdown decision on spot rows, with the spot
    expression status mapped by name. AMENDED 2026-11-16
    (PF-PAIRED-RV-20261116): entry_ready now maps to the paired
    relative-value expression, not the named no-trade; every
    other parent field is carried unchanged."""
    decision = _parent.breakdown_decision(rows, now,
                                          instrument=INSTRUMENT)
    if decision.get("status") == "entry_ready":
        return {**decision, "status": "paired_rv_entry_ready",
                "expression": "paired_relative_value_long_btc",
                "anchor": ANCHOR, "side": "buy",
                "reason": "Breakdown entry_ready on the LINK/USD spot "
                          "tape (event=%s, entry_due=%s); the side is "
                          "short and Alpaca serves no crypto spot "
                          "shorting, so under MAKE-IT-WORK Decision C "
                          "(2026-11-16) the sleeve enters the paired "
                          "relative-value expression: LONG BTC/USD "
                          "spot for the parent's 16h hold, graded on "
                          "the BTC-minus-LINK spread. The pure-short "
                          "form is retained in the registry as the "
                          "named future-venue form."
                          % (decision.get("signal_event_id"),
                             decision.get("entry_due_at"))}
    return {**decision, "expression": "paired_relative_value_long_btc"}


class FreeKrakenLinkBreakdownVarspot(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra
        if extra is None:
            extra = {}
        try:
            now = datetime.fromtimestamp(float(context.now),
                                         tz=timezone.utc)
        except (TypeError, ValueError):
            return []
        qty, entry_time = _position(extra, slice_state)
        if qty > 0:
            # LONG BTC OPEN: exit the full held quantity once the
            # parent's 16h hold clock elapses; a fresh anchor tape
            # is required to price the exit, else hold (fail closed).
            if entry_time is None or now < entry_time + HOLD:
                return []
            price, fresh = _anchor_reference(bars.get(ANCHOR) or [], now)
            if not fresh or price is None:
                return []
            return [Intent(
                "exit", ANCHOR, qty=float(qty),
                price_hint=round(float(price), 6), side="sell",
                position_intent="sell_to_close",
                reason="free_kraken_link_breakdown_varspot sell BTC/USD paired leg at spot tape "
                       "close (sell_to_close); 16h hold elapsed since "
                       "%s (PF-PAIRED-RV-20261116)"
                       % entry_time.isoformat())]
        if qty < 0:
            return []  # anchor book is long-only; fail closed
        rows = _parent.normalize(bars.get(INSTRUMENT) or [])
        decision = spot_decision(rows, now)
        if decision.get("status") != "paired_rv_entry_ready":
            return []
        price, fresh = _anchor_reference(bars.get(ANCHOR) or [], now)
        if not fresh or price is None:
            _record(extra, "named_abstention_anchor_stale", decision,
                    anchor=ANCHOR,
                    detail="BTC/USD served spot tape missing or stale "
                           "(newest bar opened more than two 4h bars "
                           "before now); paired leg not entered.")
            return []
        q = paired_qty(price, _slice_cash(extra, context))
        if q is None:
            _record(extra, "named_abstention_slice", decision,
                    anchor=ANCHOR,
                    detail="Sleeve slice sizes the BTC leg to nothing; "
                           "paired leg not entered.")
            return []
        _record(extra, "paired_rv_long_btc", decision, anchor=ANCHOR,
                qty=q, prior_20_low=decision.get("prior_20_low"))
        return [Intent(
            "enter", ANCHOR, qty=float(q),
            price_hint=round(float(price), 6), side="buy",
            position_intent="buy_to_open",
            reason="free_kraken_link_breakdown_varspot LONG BTC/USD spot (buy_to_open) paired "
                   "relative-value leg at spot tape close; LINK "
                   "breakdown event=%s entry_due=%s "
                   "(PF-PAIRED-RV-20261116)"
                   % (decision.get("signal_event_id"),
                      decision.get("entry_due_at")))]



def signal(bars, slice_state, context):
    return FreeKrakenLinkBreakdownVarspot().signal(bars, slice_state, context)
