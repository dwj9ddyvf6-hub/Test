"""Options helpers for Lazarus batch 8 options ports.

Chain/quote access via context.extra (the vix_hedge convention):
  extra["chains"]: {UNDERLYING: [{"symbol","strike","expiration","type"}]}
  extra["quotes"]: {OCC: {"bid","ask"}}
Selection: calls/puts 21-75 DTE, strike nearest spot, two-sided quote
with spread <= 30% of mid — else fail closed (no vehicle).
"""
import re
from datetime import date

OCC_RE = re.compile(r"^([A-Z]{1,6})\d{6}[CP]\d{8}$")
MIN_DTE, MAX_DTE = 21, 75
MAX_SPREAD_FRAC = 0.30  # CONSTANTS-DERIVATIONS-20261116: DERIVED (route-4, 2026-11-16) on standalone reasoning, NOT on the circular desk-precedent chain (aster_batch3 citing this file as precedent): a spread wider than 30% of mid means the half-spread alone exceeds 15% of the contract's value, so the quoted price is unrepresentative of executable cost and crossing it would donate over 15% before any edge; fail closed instead.


def underlying_of(occ):
    m = OCC_RE.match(occ or "")
    return m.group(1) if m else None


def pick_option(context, underlying, spot, right):
    chains = (context.extra or {}).get("chains") or {}
    quotes = (context.extra or {}).get("quotes") or {}
    try:
        today = date.fromisoformat(str(context.session)[:10])
    except (ValueError, TypeError):
        return None
    cands = []
    for c in chains.get(underlying) or []:
        if str(c.get("type") or "").lower() not in (right, right[0]):
            continue
        try:
            exp = date.fromisoformat(str(c["expiration"])[:10])
        except (KeyError, ValueError):
            continue
        dte = (exp - today).days
        if not (MIN_DTE <= dte <= MAX_DTE):
            continue
        q = quotes.get(c["symbol"]) or {}
        bid, ask = q.get("bid"), q.get("ask")
        if bid is None or ask is None or ask <= 0 or bid <= 0:
            continue
        mid = (float(bid) + float(ask)) / 2.0
        if mid <= 0 or (float(ask) - float(bid)) / mid > MAX_SPREAD_FRAC:
            continue
        cands.append((abs(float(c["strike"]) - spot), abs(dte - 45),
                      c["symbol"], float(ask)))
    if not cands:
        return None
    cands.sort()
    return cands[0][2], cands[0][3]


def contracts_for(budget, ask):
    if ask is None or ask <= 0:
        return 0
    return max(0, int(budget // (float(ask) * 100.0)))


def sizing_zero_journal(context, sleeve_id, symbol, price, budget):
    """SILENT-SKIP-SIZING-20261116: options contracts are whole by
    the instrument, so a budget that floors to 0 contracts cannot
    fractionalize; the fail-closed row is NAMED instead of silent
    (the DMAC sizing_zero_or_cap shape), appended to the sizing
    journal in context.extra when the channel is present (the
    xstale_refused enh20_journal convention in this family)."""
    j = (getattr(context, "extra", None) or {}).get("sizing_journal")
    if isinstance(j, list):
        j.append({"sizing_zero_or_cap": True, "sleeve": sleeve_id,
                  "symbol": symbol, "price": price, "budget": budget})
