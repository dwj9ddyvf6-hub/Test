"""Reference maximum-cancellation kernel for TCFT; no prices, orders or P&L.

The kernel proves statements about a supplied graph, not future market orders.
The finite scenario envelope is not an infinite-set robust optimization theorem.
All time windows, missing-fund allowances and external inventory bounds must be
constructed causally outside this module. Unknown allowances prohibit admission.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections import deque
import math
from fractions import Fraction

VERSION = "r10-exact-rational-transport-v1"


def utc_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a UTC offset")
    return parsed


@dataclass(frozen=True)
class Lot:
    lot_id: str
    owner_id: str
    security_id: str
    kind: str
    shares: float
    slot: int
    available_at: str
    measurement: str
    source_sha256: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    lots: tuple[Lot, ...]
    # This flag means all *registered model* allowances have finite bounds.
    # It is not a statement that the complete market or AP book was observed.
    model_allowances_complete: bool


def _validate(lots: tuple[Lot, ...], cutoff: str, max_carry_slots: int) -> None:
    t = utc_time(cutoff)
    if type(max_carry_slots) is not int or not 0 <= max_carry_slots <= 63:
        raise ValueError("max_carry_slots must be an integer in [0, 63]")
    identities: set[str] = set()
    for lot in lots:
        if not all(isinstance(x, str) and x.strip() for x in
                   (lot.lot_id, lot.owner_id, lot.security_id)):
            raise ValueError("permanent lot, owner and security identities required")
        if lot.lot_id in identities:
            raise ValueError("a physical adjustment lot cannot be counted twice")
        identities.add(lot.lot_id)
        if lot.kind not in {"DEMAND", "SUPPLY"}:
            raise ValueError("lot kind must be DEMAND or SUPPLY")
        if type(lot.shares) is bool or not isinstance(lot.shares, (int, float)):
            raise ValueError("share amounts must be numeric, never booleans")
        if not math.isfinite(lot.shares) or lot.shares <= 0:
            raise ValueError("share amounts must be strictly positive and finite")
        if type(lot.slot) is not int or not 0 <= lot.slot <= 63:
            raise ValueError("time slots must be integer session offsets in [0, 63]")
        if utc_time(lot.available_at) > t:
            raise ValueError("an unavailable lot cannot enter the historical graph")
        if lot.measurement not in {"OBSERVED_INVENTORY", "MODEL_ADJUSTMENT",
                                   "MODEL_BRIDGE_ALLOWANCE"}:
            raise ValueError("measurement must explicitly identify observation or model")
        if (not isinstance(lot.source_sha256, str) or len(lot.source_sha256) != 64 or
                any(c not in "0123456789abcdef" for c in lot.source_sha256)):
            raise ValueError("source SHA-256 must be lowercase hexadecimal")


def cancellation(lots: tuple[Lot, ...], cutoff: str, max_carry_slots: int = 5,
                 relax_time: bool = False) -> dict:
    """Maximize cancellable shares by permanent security, respecting each lot once.

    A supply lot can meet a demand only when its modeled release slot precedes
    that demand's deadline and the carry is within the registered allowance.
    Same-owner edges are prohibited: preprocessing must net one owner's ledger.
    Relaxing time changes only temporal feasibility, preserving shares/identity.
    Results never assert an off-exchange cross occurred or is available to us.
    """
    if type(relax_time) is not bool:
        raise ValueError("relax_time must be an exact boolean")
    _validate(lots, cutoff, max_carry_slots)
    results = {}
    for security in sorted({x.security_id for x in lots}):
        supplies = sorted((x for x in lots if x.security_id == security and
                           x.kind == "SUPPLY"), key=lambda x: x.lot_id)
        demands = sorted((x for x in lots if x.security_id == security and
                          x.kind == "DEMAND"), key=lambda x: x.lot_id)
        # Exact rational arithmetic on the decimal spelling of every supplied
        # numeric value. No global epsilon can erase a small physical lot.
        total = sum((Fraction(str(x.shares)) for x in demands), Fraction())
        available = sum((Fraction(str(x.shares)) for x in supplies), Fraction())
        try:
            if not all(math.isfinite(float(v)) for v in (total, available)):
                raise ValueError("aggregate shares exceed finite output domain")
        except OverflowError as exc:
            raise ValueError("aggregate shares exceed finite output domain") from exc
        scale = 1
        source, sink = 0, 1
        size = 2 + len(supplies) + len(demands)
        graph: list[list[list]] = [[] for _ in range(size)]
        names = {0: "SOURCE", 1: "SINK"}
        originals = []

        def edge(u: int, v: int, cap: float, label: str) -> None:
            a = [v, len(graph[v]), cap]
            b = [u, len(graph[u]), Fraction()]
            graph[u].append(a)
            graph[v].append(b)
            originals.append((u, v, cap, a, label))

        for j, lot in enumerate(supplies):
            node = 2 + j
            names[node] = "SUPPLY:" + lot.lot_id
            edge(source, node, Fraction(str(lot.shares)), lot.lot_id)
        for k, lot in enumerate(demands):
            node = 2 + len(supplies) + k
            names[node] = "DEMAND:" + lot.lot_id
            edge(node, sink, Fraction(str(lot.shares)), lot.lot_id)
        for j, supply in enumerate(supplies):
            for k, demand in enumerate(demands):
                valid_time = 0 <= demand.slot - supply.slot <= max_carry_slots
                if supply.owner_id != demand.owner_id and (relax_time or valid_time):
                    edge(2 + j, 2 + len(supplies) + k, min(total, available),
                         supply.lot_id + "->" + demand.lot_id)

        # Edmonds-Karp is intentionally small and independently checkable.
        # A production large graph can use a separately verified LP/max-flow engine.
        flow = Fraction()
        eps = 0
        while True:
            parent = {source: None}
            queue = deque([source])
            while queue and sink not in parent:
                u = queue.popleft()
                for index, arc in enumerate(graph[u]):
                    if arc[2] > eps and arc[0] not in parent:
                        parent[arc[0]] = (u, index)
                        queue.append(arc[0])
            if sink not in parent:
                break
            delta = float("inf")
            v = sink
            while v != source:
                u, index = parent[v]
                delta = min(delta, graph[u][index][2])
                v = u
            v = sink
            while v != source:
                u, index = parent[v]
                arc = graph[u][index]
                arc[2] -= delta
                graph[v][arc[1]][2] += delta
                v = u
            flow += delta

        reached = {source}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for arc in graph[u]:
                if arc[2] > eps and arc[0] not in reached:
                    reached.add(arc[0])
                    queue.append(arc[0])
        cut = [(u, v, cap, label) for u, v, cap, _, label in originals
               if u in reached and v not in reached]
        cut_capacity = sum((x[2] for x in cut), Fraction())
        matched = flow * scale
        tolerance = 0
        if matched != cut_capacity:
            raise ArithmeticError("max-flow/min-cut witness does not reconcile")
        if matched > min(total, available) + tolerance:
            raise ArithmeticError("the cancellation exceeds physical model lots")
        matches = [{"edge": label, "shares": float(cap - arc[2]),
                    "exact_shares": str(cap - arc[2])}
                   for u, v, cap, arc, label in originals
                   if names[u].startswith("SUPPLY:") and
                   names[v].startswith("DEMAND:") and cap - arc[2] > eps]
        results[security] = {
            "demand_shares": float(total), "supply_shares": float(available),
            "cancelled_shares": float(matched),
            "unmatched_buy_shares": float(max(Fraction(), total - matched)),
            "exact_certificate": {"demand": str(total), "supply": str(available),
                                  "matched": str(matched),
                                  "unmatched": str(total - matched),
                                  "cut": str(cut_capacity)},
            "matches": matches,
            "witness": {"source_side": sorted(names[x] for x in reached),
                        "cut_capacity_shares": float(cut_capacity),
                        "cut_edges": [{"from": names[u], "to": names[v],
                                       "shares": float(cap), "exact_shares": str(cap),
                                       "label": label}
                                      for u, v, cap, label in cut]},
        }
    return results


def finite_envelope(scenarios: tuple[Scenario, ...], cutoff: str,
                    max_carry_slots: int = 5) -> dict:
    """Transport-gap bounds over *only* the fully declared finite scenarios.

    An incomplete registered allowance makes the strategy unavailable. It is
    not replaced with a favorable zero external-inventory or custom-basket guess.
    Securities absent in any scenario have zero demand in that scenario.
    """
    if not scenarios:
        raise ValueError("at least one complete joint scenario is required")
    ids = [s.scenario_id for s in scenarios]
    if len(ids) != len(set(ids)) or any(not x.strip() for x in ids):
        raise ValueError("scenario identities must be nonempty and unique")
    for s in scenarios:
        if type(s.model_allowances_complete) is not bool:
            raise ValueError("model completeness flag must be boolean")
        _validate(s.lots, cutoff, max_carry_slots)
    if any(not s.model_allowances_complete for s in scenarios):
        return {"status": "NO_TRADE_UNBOUNDED_MODEL_ALLOWANCE",
                "financial_edge_validated": False, "securities": {},
                "scope": "finite registered model only; actual market demand unidentified"}
    cases = []
    for s in scenarios:
        timed = cancellation(s.lots, cutoff, max_carry_slots)
        relaxed = cancellation(s.lots, cutoff, max_carry_slots, relax_time=True)
        gaps = {}
        for security in timed:
            debt = Fraction(timed[security]["exact_certificate"]["unmatched"])
            no_time = Fraction(relaxed[security]["exact_certificate"]["unmatched"])
            if no_time > debt:
                raise ArithmeticError("relaxing time cannot increase unmatched demand")
            gaps[security] = {"timed_debt_shares": float(debt),
                              "relaxed_debt_shares": float(no_time),
                              "time_cut_gap_shares": float(debt - no_time),
                              "exact_timed_debt": str(debt),
                              "exact_relaxed_debt": str(no_time),
                              "exact_time_cut_gap": str(debt - no_time)}
        cases.append({"scenario_id": s.scenario_id, "securities": gaps,
                      "timed": timed, "relaxed": relaxed})
    securities = sorted({i for case in cases for i in case["securities"]})
    summary = {}
    for i in securities:
        debt = [c["securities"].get(i, {}).get("timed_debt_shares", 0.0)
                for c in cases]
        gap = [c["securities"].get(i, {}).get("time_cut_gap_shares", 0.0)
               for c in cases]
        summary[i] = {"timed_debt_lower_shares": min(debt),
                      "timed_debt_upper_shares": max(debt),
                      "time_cut_gap_lower_shares": min(gap),
                      "time_cut_gap_upper_shares": max(gap),
                      "structural_candidate": min(debt) > 0 and min(gap) > 0}
    return {"status": "MODEL_ENVELOPE_COMPUTED", "securities": summary,
            "cases": cases, "financial_edge_validated": False,
            "scope": "finite registered model only; actual market demand unidentified"}
