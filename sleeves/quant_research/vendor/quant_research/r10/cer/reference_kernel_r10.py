"""R10 CER bounded kernel, with finite-output conversion guard.

Copied immutable R4; chronology/economic definitions unchanged.

The kernel does not extract text, estimate project economics, infer historical
availability, fit return forecasts or place orders. Values are caller-supplied
and must have independently supported finite units and bounds.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite


class State(Enum):
    UNKNOWN = "UNKNOWN"
    FALSE = "FALSE"
    TRUE = "TRUE"
    CONFLICT = "CONFLICT"


def _aware(t: datetime) -> datetime:
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("A verified timezone-aware clock is required")
    return t


def _number(x: float) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x):
        raise ValueError("Finite numeric value required; Boolean is not a quantity")
    return float(x)


@dataclass(frozen=True)
class Proof:
    project_id: str
    predicate_id: str
    origin_family: str
    body_sha256: str
    state: State
    published: datetime
    received: datetime
    extracted: datetime
    verified: datetime
    effective_from: datetime
    effective_until: datetime | None = None

    def __post_init__(self):
        if not all(isinstance(x, str) and x for x in (self.project_id, self.predicate_id, self.origin_family)):
            raise ValueError("Nonempty exact identity and source family required")
        if len(self.body_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.body_sha256):
            raise ValueError("SHA256 body binding required")
        if not isinstance(self.state, State) or self.state == State.CONFLICT:
            raise ValueError("A proof must carry an explicit atomic state")
        for t in (self.published, self.received, self.extracted, self.verified, self.effective_from):
            _aware(t)
        if self.extracted < self.received or self.verified < self.extracted:
            raise ValueError("Extraction/verification must follow actual receipt")
        if self.effective_until is not None and _aware(self.effective_until) <= self.effective_from:
            raise ValueError("Invalid effective interval")

    @property
    def available(self) -> datetime:
        return max(self.published, self.received, self.extracted, self.verified)

    def usable(self, cutoff: datetime) -> bool:
        _aware(cutoff)
        return self.available <= cutoff and self.effective_from <= cutoff and (
            self.effective_until is None or cutoff < self.effective_until
        )


@dataclass(frozen=True)
class Graph:
    project_id: str
    required: tuple[str, ...]
    frozen_at: datetime
    contract_sha256: str

    def __post_init__(self):
        _aware(self.frozen_at)
        if not isinstance(self.project_id, str) or not self.project_id or not isinstance(self.required, tuple) or not 1 <= len(self.required) <= 8:
            raise ValueError("An exact project and 1..8 frozen AND prerequisites are required")
        if any(not isinstance(x, str) or not x for x in self.required) or len(set(self.required)) != len(self.required):
            raise ValueError("Unique nonempty prerequisites required")
        if len(self.contract_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.contract_sha256):
            raise ValueError("Original contract body hash required")


def snapshot(graph: Graph, proofs: tuple[Proof, ...], cutoff: datetime) -> dict[str, State]:
    """Conflicts remain blocked. Supersession must be resolved by the caller first.

    A syndicated duplicate has no effect, and a proof from a different project
    cannot close this project's gate. UNKNOWN assertions do not negate verified
    truth, but they also cannot supply a required occurrence proof.
    """
    _aware(cutoff)
    if graph.frozen_at > cutoff:
        raise ValueError("Graph unavailable at cutoff")
    result = {k: State.UNKNOWN for k in graph.required}
    for key in graph.required:
        observations = {
            p.state for p in proofs if p.project_id == graph.project_id
            and p.predicate_id == key and p.usable(cutoff)
            and p.state != State.UNKNOWN
        }
        if State.TRUE in observations and State.FALSE in observations:
            result[key] = State.CONFLICT
        elif observations:
            result[key] = next(iter(observations))
    return result


def closure(graph: Graph, proofs: tuple[Proof, ...], prior: datetime, cutoff: datetime) -> bool:
    """Knowledge-set closure only; it predicts neither causal occurrence nor price."""
    _aware(prior); _aware(cutoff)
    if not graph.frozen_at <= prior < cutoff:
        raise ValueError("A strictly older, frozen graph snapshot is required")
    old = snapshot(graph, proofs, prior)
    new = snapshot(graph, proofs, cutoff)
    # A preannounced effective date maturing is not newly observed evidence.
    # The economic anticipation model is still needed even for a fresh proof.
    new_required_proof = any(
        p.project_id == graph.project_id and p.predicate_id in old
        and old[p.predicate_id] != State.TRUE and new[p.predicate_id] == State.TRUE
        and p.state == State.TRUE and prior < p.available <= cutoff and p.usable(cutoff)
        for p in proofs
    )
    return (all(v == State.TRUE for v in new.values())
            and not all(v == State.TRUE for v in old.values()) and new_required_proof)


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    def __post_init__(self):
        lo, hi = _number(self.low), _number(self.high)
        if lo > hi:
            raise ValueError("Invalid uncertainty bounds")


def difference(after: Interval, before: Interval) -> Interval:
    """Conservative independent-extrema difference; not a financial CI."""
    return Interval(after.low - before.high, after.high - before.low)


def branch_revenue_delta(delivered_mwh: Interval, before_usd_mwh: float,
                         after_usd_mwh: float) -> Interval:
    """Simple fixed-rate branch delta, not equity profit or NPV.

    Retains any early-payment branch. Requires caller to supply eligible
    delivered-MWh bounds; MW capacity alone is not a valid substitute.
    Negative rate changes remain negative rather than silently floored.
    """
    if delivered_mwh.low < 0:
        raise ValueError("Delivered energy bounds must be nonnegative")
    delta = _number(after_usd_mwh) - _number(before_usd_mwh)
    a, b = delivered_mwh.low * delta, delivered_mwh.high * delta
    return Interval(min(a, b), max(a, b))


def robust_conversion_screen(after: Interval | None, before: Interval | None,
                             equity_value: float) -> float | None:
    """None means unsupported economics, not zero uncertainty or a buy order."""
    cap = _number(equity_value)
    if cap <= 0:
        raise ValueError("Positive dated equity value required")
    if after is None or before is None:
        return None
    result = max(difference(after, before).low, 0.0) / cap
    if not isfinite(result):
        raise ValueError("Conversion quotient outside finite numeric domain")
    return result
