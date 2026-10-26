"""Pure synthetic lifecycle reference; not a native feed parser, policy or backtest.

Integer price units are adapter-defined and consistent with the frozen bands.
Sequence is a contiguous adapter transition index including NOP rows; a native
ITCH transport sequence is not itself an instrument-specific transition index.
No event/feature uses a final order lifetime or an unreceived message.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping

NS = 1_000_000_000

def integer(value, name, *, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value

@dataclass
class Order:
    side: str
    price: int
    remaining: int
    received: int
    cohort: bool

def cohort_memory(events: Iterable[Mapping], *, episode_receipt_ns: int,
                  episode_exchange_ns: int, asof_receipt_ns: int,
                  bid_band: tuple[int, int], ask_band: tuple[int, int],
                  episode_sequence: int, asof_sequence: int,
                  exchange_to_receipt_offset_ns: int,
                  clock_uncertainty_ns: int = 0, initial_sequence: int = 1,
                  maturity_ns: int = 20 * NS) -> dict:
    """Replay first-received, validated canonical transitions to one cutoff.

    The explicitly supplied offset converts exchange-domain timestamps to the
    receipt domain; it and its uncertainty require external calibration proof.
    Each visible event must not be future-dated beyond that calibrated bound.
    Episode membership is strictly after the processed trigger anchor; as-of
    includes only transitions at or before the composite (receipt, sequence)
    boundary. Sequence is a complete adapter processing ordinal, not a native
    per-instrument sequence. Whole normalized source events must be closed
    atomically by a separately certified adapter before assigning anchors.
    Call with the complete known starting book/add history; unknown references
    are errors. Snapshot reconstruction and broken-trade reconciliation belong
    to the absent, separately validated adapter. Retain NOP rows for continuity.
    """
    integer(episode_receipt_ns, 'episode receipt')
    integer(episode_exchange_ns, 'episode exchange')
    integer(asof_receipt_ns, 'asof receipt')
    integer(maturity_ns, 'maturity', minimum=1)
    integer(episode_sequence, 'episode sequence')
    integer(asof_sequence, 'asof sequence')
    integer(initial_sequence, 'initial sequence', minimum=1)
    if type(exchange_to_receipt_offset_ns) is not int:
        raise ValueError('calibrated exchange-to-receipt offset must be an exact signed integer')
    integer(clock_uncertainty_ns, 'clock uncertainty')
    if episode_exchange_ns + exchange_to_receipt_offset_ns > episode_receipt_ns + clock_uncertainty_ns:
        raise ValueError('episode exchange anchor is unavailable under calibrated clocks')
    if asof_sequence < episode_sequence or (asof_receipt_ns, asof_sequence) < (episode_receipt_ns, episode_sequence):
        raise ValueError('asof precedes episode')
    bands = {'B': bid_band, 'A': ask_band}
    for band in bands.values():
        if type(band) is not tuple or len(band) != 2:
            raise ValueError('band must be a 2-tuple')
        integer(band[0], 'band lower', minimum=1)
        integer(band[1], 'band upper', minimum=1)
        if band[0] > band[1]:
            raise ValueError('reversed band')
    if bid_band[1] >= ask_band[0]:
        raise ValueError('bands must not touch/cross')
    book: dict[str, Order] = {}
    seen: set[str] = set()
    totals = {s: {'added': 0, 'executed': 0, 'cancelled': 0} for s in bands}
    previous_sequence = previous_receipt = None
    episode_anchor_seen = episode_sequence == 0

    def add(event):
        oid = event['order_id']
        if not isinstance(oid, str) or not oid or oid in seen:
            raise ValueError('missing/reused order ID')
        side = event['side']
        if side not in bands:
            raise ValueError('unknown side')
        price = integer(event['price'], 'price', minimum=1)
        qty = integer(event['quantity'], 'add quantity', minimum=1)
        received = event['receipt_ns']
        lo, hi = bands[side]
        cohort = ((received, event['sequence']) > (episode_receipt_ns, episode_sequence) and
                  event['exchange_ns'] >= episode_exchange_ns and lo <= price <= hi)
        book[oid] = Order(side, price, qty, received, cohort)
        seen.add(oid)
        if cohort:
            totals[side]['added'] += qty

    def remove(oid, qty, kind):
        if oid not in book:
            raise ValueError('unknown order reference')
        order = book[oid]
        integer(qty, 'remove quantity', minimum=1)
        if qty > order.remaining:
            raise ValueError('overdrawn order quantity')
        if order.cohort:
            totals[order.side][kind] += qty
        order.remaining -= qty
        if order.remaining == 0:
            del book[oid]

    for event in events:
        received = integer(event['receipt_ns'], 'receipt')
        if received > asof_receipt_ns:
            continue  # Future content, even invalid content, cannot affect this state.
        sequence = integer(event['sequence'], 'sequence', minimum=1)
        if sequence > asof_sequence:
            continue  # Equal-receipt later processing is unavailable at this anchor.
        integer(event['exchange_ns'], 'exchange')
        if event['exchange_ns'] + exchange_to_receipt_offset_ns > received + clock_uncertainty_ns:
            raise ValueError('exchange event is unavailable under calibrated receipt clocks')
        if previous_sequence is None and sequence != initial_sequence:
            raise ValueError('missing authenticated starting transition prefix')
        if previous_sequence is not None and sequence != previous_sequence + 1:
            raise ValueError('sequence gap/duplicate; block until authenticated recovery')
        if previous_receipt is not None and received < previous_receipt:
            raise ValueError('not first-receipt order')
        if sequence == episode_sequence:
            if received != episode_receipt_ns:
                raise ValueError('episode processed ordinal does not match its receipt anchor')
            episode_anchor_seen = True
        previous_sequence, previous_receipt = sequence, received
        action = event['action']
        if action == 'NOP':
            continue
        if action == 'ADD':
            add(event)
        elif action in ('EXECUTE', 'CANCEL'):
            remove(event['order_id'], event['quantity'], 'executed' if action == 'EXECUTE' else 'cancelled')
        elif action == 'DELETE':
            oid = event['order_id']
            if oid not in book:
                raise ValueError('unknown delete reference')
            remove(oid, book[oid].remaining, 'cancelled')
        elif action == 'REPLACE':
            oid = event['order_id']
            if oid not in book:
                raise ValueError('unknown replace reference')
            side = book[oid].side
            new_id = event['new_order_id']
            if not isinstance(new_id, str) or not new_id or new_id in seen:
                raise ValueError('invalid replacement ID')
            integer(event['price'], 'replacement price', minimum=1)
            integer(event['quantity'], 'replacement quantity', minimum=1)
            remove(oid, book[oid].remaining, 'cancelled')
            new = dict(event, order_id=new_id, side=side)
            add(new)
        else:
            raise ValueError('unsupported action; reconciliation/adapter required')
    if (previous_sequence or 0) != asof_sequence:
        raise ValueError('asof processed anchor is missing from the received prefix')
    if not episode_anchor_seen:
        raise ValueError('episode processed anchor is missing from the received prefix')
    result = {'asof_receipt_ns': asof_receipt_ns, 'asof_sequence': asof_sequence,
              'episode_sequence': episode_sequence, 'source': 'r10_anchored_canonical_lifecycle_reference'}
    for side in ('B', 'A'):
        live = sum(o.remaining for o in book.values() if o.side == side and o.cohort)
        mature = sum(o.remaining for o in book.values() if o.side == side and o.cohort and
                     asof_receipt_ns - o.received >= maturity_ns)
        summary = dict(totals[side], live=live, mature_live=mature)
        A, E, C = summary['added'], summary['executed'], summary['cancelled']
        if A != E + C + live:
            raise AssertionError('share conservation failed')
        summary.update(supported=A > 0, commitment=(E - C + mature) / A if A else None,
                       spent_fraction=E / A if A else None, withdrawn_fraction=C / A if A else None,
                       mature_remaining_fraction=mature / A if A else None)
        result[side] = summary
    result['bid_minus_ask_commitment'] = (result['B']['commitment'] - result['A']['commitment']
                                        if result['B']['supported'] and result['A']['supported'] else None)
    return result

def admit(*, gross_lower_bp: float, qqq_upper_bp: float, incremental_lower_bp: float,
          cost_upper_bp: float, overhead_bp: float) -> bool:
    """Two-inequality cost/increment primitive, without any fitted estimates.

    The full CPDW wedge, support, clocks, risk and settlement gates are absent;
    a true return here cannot authorize a policy entry or paper order.
    """
    vals = (gross_lower_bp, qqq_upper_bp, incremental_lower_bp, cost_upper_bp, overhead_bp)
    if any(type(v) not in (int, float) or not isfinite(v) for v in vals):
        raise ValueError('all admission estimates must be finite real scalars')
    if cost_upper_bp < 15 or overhead_bp < 0:
        raise ValueError('15 bp minimum round-trip budget and nonnegative overhead required')
    return incremental_lower_bp > 5 and gross_lower_bp - qqq_upper_bp > 2 * cost_upper_bp + overhead_bp + 10

def neutralize_disposition(summary: Mapping, gamma: float) -> dict:
    """Conservation-preserving model-input shadow, never a native book event.

    Actual observed book/OFI/trades stay untouched. This representation can be
    physically inconsistent with those messages and is not a causal estimate.
    """
    if type(gamma) not in (int, float) or not isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError('gamma must be finite in [0,1]')
    A, E, C, L, mature = [summary[k] for k in ('added','executed','cancelled','live','mature_live')]
    for value in (A, E, C, L, mature):
        integer(value, 'actual lifecycle quantity')
    if A <= 0 or A != E + C + L or mature > L:
        raise ValueError('supported conserved actual summary required')
    neutral = (E + C) / 2
    spent = (1-gamma)*E + gamma*neutral
    withdrawn = (1-gamma)*C + gamma*neutral
    return {'added':A,'executed':spent,'cancelled':withdrawn,'live':L,'mature_live':mature,
            'commitment':(spent-withdrawn+mature)/A, 'spent_fraction':spent/A,
            'withdrawn_fraction':withdrawn/A, 'mature_remaining_fraction':mature/A,
            'gamma':gamma,'status':'MODEL_INPUT_SHADOW_NOT_PHYSICAL_INTERVENTION'}
