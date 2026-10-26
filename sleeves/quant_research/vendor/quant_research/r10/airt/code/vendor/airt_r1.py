"""Research kernels for frozen AIRT v0.1; not a trained trading strategy.

All clocks below use UTC Unix seconds or integer completed-minute boundaries.
No broker client, network access, fabricated market prices or implicit defaults.
Mandatory upstream auction/universe/receipt/PIT contracts remain external.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
from collections import defaultdict
from typing import Iterable

class EvidenceUnavailable(ValueError):
    pass

def finite(*values):
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in values):
        raise EvidenceUnavailable("nonfinite or nonnumeric observation")

@dataclass(frozen=True)
class Quote:
    event: float
    receipt: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int

    def validate(self, available_at: float, reference_time: float | None = None):
        reference = available_at if reference_time is None else reference_time
        finite(self.event, self.receipt, self.bid, self.ask, available_at, reference)
        if not 0 < self.bid < self.ask or self.event > self.receipt or self.receipt > available_at:
            raise EvidenceUnavailable("locked/crossed, invalid or unavailable quote")
        if not 0 <= reference - self.event <= 1 or reference > available_at:
            raise EvidenceUnavailable("quote older than one second")
        if any(type(s) is not int or s < 0 for s in (self.bid_size, self.ask_size)):
            raise EvidenceUnavailable("invalid displayed shares")
        return self

    @property
    def midpoint(self):
        return (self.bid + self.ask) / 2

    @property
    def spread_bp(self):
        return 10000 * (self.ask - self.bid) / self.midpoint

@dataclass(frozen=True)
class Trade:
    event: float
    receipt: float
    price: float
    shares: int
    quote: Quote | None
    auction: bool = False

def classified_flow(trades: Iterable[Trade], cutoff: float):
    """Dollar denominator includes eligible unclassified continuous trades."""
    total = covered = signed = 0.0
    for t in trades:
        finite(t.event, t.receipt, t.price, cutoff)
        if t.event > t.receipt or t.receipt > cutoff or t.price <= 0 or type(t.shares) is not int or t.shares <= 0:
            raise EvidenceUnavailable("invalid or unavailable trade")
        if t.auction:
            continue
        dollars = t.price * t.shares
        total += dollars
        q = t.quote
        if q is None:
            continue
        try:
            q.validate(t.receipt, reference_time=t.event)
        except EvidenceUnavailable:
            continue
        if not q.event < t.event or not q.receipt < t.receipt or t.event - q.event > 1:
            continue
        covered += dollars
        signed += dollars * ((t.price > q.midpoint) - (t.price < q.midpoint))
    if total <= 0 or covered / total < .8:
        raise EvidenceUnavailable("classified dollar coverage below80percent")
    return signed / total, covered / total

def residual_bp(stock_ratio, market_ratio, sector_ratio, beta_market, beta_sector):
    finite(stock_ratio, market_ratio, sector_ratio, beta_market, beta_sector)
    if min(stock_ratio, market_ratio, sector_ratio) <= 0:
        raise EvidenceUnavailable("nonpositive gross-price ratio")
    return 10000 * (math.log(stock_ratio) - beta_market * math.log(market_ratio)
                    - beta_sector * (math.log(sector_ratio) - math.log(market_ratio)))

def sigma0(prior_residuals):
    values = sorted(prior_residuals)
    if len(values) != 20:
        raise EvidenceUnavailable("exact20 prior eligible windows required")
    finite(*values)
    median = (values[9] + values[10]) / 2
    deviation = sorted(abs(x - median) for x in values)
    return max(10., 1.4826 * (deviation[9] + deviation[10]) / 2)

@dataclass(frozen=True)
class Minute:
    end: int
    dollars: float
    x: float

@dataclass(frozen=True)
class Probe:
    start: int
    end: int
    dollars: float
    x_start: float
    x_end: float

    def eta(self, quota):
        finite(quota)
        if quota <= 0 or self.dollars <= 0:
            raise EvidenceUnavailable("nonpositive quota or probe dose")
        return (self.x_end - self.x_start) * quota / self.dollars

def matched_probes(minutes, quota, x0, start=5, latest=20):
    """Minute5=09:35; consume only the completed prefix of disjoint probes.

    Entire overshoot is retained. Later observations are not inspected once
    both probes complete, so future corruption cannot rewrite a prior result.
    """
    finite(quota, x0)
    if quota <= 0 or type(start) is not int or type(latest) is not int:
        raise EvidenceUnavailable("invalid quota")
    rows=iter(minutes);initial_start=start;previous=None
    def take(expected):
        nonlocal previous
        while True:
            try:r=next(rows)
            except StopIteration:raise EvidenceUnavailable("incomplete continuous coverage") from None
            if type(r.end) is not int or (previous is not None and r.end <= previous):
                raise EvidenceUnavailable("unordered, duplicate or invalid consumed boundary")
            previous=r.end
            if r.end <= initial_start:continue
            if r.end != expected:raise EvidenceUnavailable("missing consumed minute boundary")
            finite(r.dollars,r.x)
            if r.dollars < 0:raise EvidenceUnavailable("negative continuous dollars")
            return r
    probes = []
    for _ in range(2):
        dose = 0.
        for end in range(start + 1, start + 8):
            if end > latest:
                raise EvidenceUnavailable("deadline or incomplete continuous coverage")
            row=take(end);dose += row.dollars
            if end - start >= 2 and dose >= quota:
                p = Probe(start, end, dose, x0, row.x)
                probes.append(p); start = end; x0 = p.x_end
                break
        else:
            raise EvidenceUnavailable("probe quota timeout")
    return tuple(probes)

def route(*, x0, x1, x2, v0, a0, scale, spread0, spread2, q1, q2,
          eta1, eta2, midpoint, vwap1, vwap2):
    finite(x0, x1, x2, v0, a0, scale, spread0, spread2, q1, q2,
           eta1, eta2, midpoint, vwap1, vwap2)
    if scale < 10 or min(spread0, spread2) < 0 or min(midpoint, vwap1, vwap2) <= 0 or max(abs(q1), abs(q2)) > 1:
        raise EvidenceUnavailable("invalid scale, flow, spread or price")
    D = abs(x0)
    if v0 < 2 or a0 < 1.25 or D < max(20, 1.5 * scale):
        return None
    if spread2 > 8 or spread2 > .7 * spread0:
        return None
    if (x0 > 0 and min(x1, x2) / x0 >= .8 and min(q1, q2) >= .1
            and eta1 >= .05 * D and eta2 >= .5 * eta1 and midpoint > max(vwap1, vwap2)):
        return "continuation"
    if (x0 < 0 and q1 <= -.1 and eta1 >= -.05 * D and q2 >= -.05
            and eta2 >= .2 * D and x2 < 0 and midpoint > vwap1):
        return "recovery"
    return None

def cell(route_name, v0, D, scale):
    finite(v0, D, scale)
    if route_name not in {"continuation", "recovery"} or D <= 0 or scale <= 0:
        raise EvidenceUnavailable("invalid calibration cell")
    return (route_name, int(v0 >= 3), int(D / scale >= 2.5))

def policy_label_bp(net_dollars, itemized_execution_cost_dollars, initial_reserved_dollars):
    finite(net_dollars, itemized_execution_cost_dollars, initial_reserved_dollars)
    if itemized_execution_cost_dollars < 0 or initial_reserved_dollars <= 0:
        raise EvidenceUnavailable("invalid execution costs/reservation")
    return 10000 * (net_dollars + itemized_execution_cost_dollars) / initial_reserved_dollars

def calibration(records, now, expected_policy_sha, expected_cell):
    """Records are pre-expectancy technical-shadow labels, not admitted winners.

    The cold-start cohort is an explicit research completion choice. Grouped
    event-weighted intercept SE is not a simultaneous performance certificate.
    """
    by_day = defaultdict(list)
    values = []
    seen = set()
    for r in records:
        if not r["technical_eligible"] or not r["mature"]:
            raise EvidenceUnavailable("ineligible or immature calibration target")
        if r["policy_sha"] != expected_policy_sha or r["available_at"] >= now:
            raise EvidenceUnavailable("policy mismatch or not strictly prior")
        if tuple(r["cell"]) != tuple(expected_cell):
            raise EvidenceUnavailable("calibration cells mixed")
        identity = (r["permanent_id"], r["day"])
        if identity in seen:
            raise EvidenceUnavailable("duplicate issuer/session target")
        seen.add(identity)
        finite(r["event_at"], r["outcome_at"], r["available_at"], now)
        if not r["event_at"] <= r["outcome_at"] <= r["available_at"] < now:
            raise EvidenceUnavailable("target precedes origin or receipt")
        y = policy_label_bp(r["net"], r["execution_cost"], r["reserved"])
        values.append(y); by_day[r["day"]].append(y)
    n, groups = len(values), len(by_day)
    if n < 200 or groups < 60:
        raise EvidenceUnavailable("calibration requires200events and60sessiondates")
    mean = math.fsum(values) / n
    se = math.sqrt(groups / (groups - 1) * math.fsum(math.fsum(x - mean for x in ys)**2 for ys in by_day.values()) / n**2)
    return mean, se

def expectancy_admitted(mean_bp, se_bp, expected_round_trip_bp):
    finite(mean_bp, se_bp, expected_round_trip_bp)
    if min(se_bp, expected_round_trip_bp) < 0:
        raise EvidenceUnavailable("negative uncertainty or costs")
    return mean_bp - 1.645 * se_bp > 2 * expected_round_trip_bp + 10

def decision_ready(probe2_boundary, receipts, quote):
    if not receipts:
        raise EvidenceUnavailable("missing required message receipts")
    finite(probe2_boundary, *receipts)
    available = max(max(receipts), probe2_boundary + 2)
    quote.validate(quote.receipt)
    if quote.receipt < available + 1:
        raise EvidenceUnavailable("decision watermark or one-second wait not complete")
    return quote.receipt

def size_shares(equity, d, adv20, observed_last60_dollars, entry_price):
    finite(equity, d, adv20, observed_last60_dollars, entry_price)
    if min(equity, d, adv20, entry_price) <= 0 or observed_last60_dollars < 0:
        raise EvidenceUnavailable("invalid risk/liquidity budget")
    return math.floor(min(.001 * equity / d, .10 * equity,
                          .001 * adv20, .02 * observed_last60_dollars) / entry_price)

def stop_distance(D, sigma1m):
    finite(D, sigma1m)
    if min(D, sigma1m) < 0:
        raise EvidenceUnavailable("negative displacement/risk scale")
    return max(10, .5 * D, 2 * sigma1m) / 10000

def portfolio_capacity(*, equity, available_cash, gross_with_reservations,
                       sector_with_reservations, occupied_names, sector, proposed_shares,
                       price_cap, session_return, peak_drawdown):
    """Conservative reservations count against name/gross/sector capacity."""
    finite(equity, available_cash, gross_with_reservations, price_cap,
           session_return, peak_drawdown, *sector_with_reservations.values())
    if equity <= 0 or price_cap <= 0 or min(available_cash, gross_with_reservations, peak_drawdown) < 0:
        raise EvidenceUnavailable("invalid account state")
    if sector not in sector_with_reservations or type(proposed_shares) is not int or proposed_shares < 0:
        raise EvidenceUnavailable("unknown sector or invalid shares")
    if type(occupied_names) is not int or occupied_names < 0 or any(v < 0 for v in sector_with_reservations.values()):
        raise EvidenceUnavailable("invalid name count or sector exposure")
    if session_return <= -.005 or peak_drawdown >= .05 or occupied_names >= 4:
        return 0
    dollars = min(available_cash, .4 * equity - gross_with_reservations,
                  .25 * equity - sector_with_reservations[sector], .1 * equity)
    return min(proposed_shares, max(0, math.floor(dollars / price_cap)))

def entry_cancel_reason(*, route_name, x0, x1, current_x, midpoint,
                        vwap1, vwap2, quote, now, first_submission, fixed_cap,
                        halted=False, risk_allowed=True, data_good=True):
    finite(x0, x1, current_x, midpoint, vwap1, vwap2, now, first_submission, fixed_cap)
    if not data_good: return "bad_data"
    if halted: return "halt"
    if not risk_allowed: return "risk"
    if now < first_submission: raise EvidenceUnavailable("order clock reversed")
    if now >= first_submission + 90: return "timeout"
    quote.validate(now)
    if quote.ask > fixed_cap: return "price_cap"
    if quote.spread_bp > 8: return "spread"
    if route_name == "continuation":
        if current_x < .8 * x0 or midpoint <= max(vwap1, vwap2): return "thesis"
    elif route_name == "recovery":
        if current_x >= 0 or current_x < x1 - .1 * abs(x0) or midpoint <= vwap1: return "thesis"
    else:
        raise EvidenceUnavailable("unknown route")
    return None

def next_quote_fill(quote, *, submitted_at, fixed_cap, child_shares):
    """Conservative L1 simulation, not evidence of queue priority or real fill."""
    finite(submitted_at, fixed_cap)
    if type(child_shares) is not int or child_shares < 0 or fixed_cap <= 0:
        raise EvidenceUnavailable("invalid child order")
    quote.validate(quote.receipt)
    if quote.receipt <= submitted_at or quote.event <= submitted_at:
        return (0, None)
    if quote.ask > fixed_cap or quote.spread_bp > 8:
        return (0, None)
    shares = min(child_shares, quote.ask_size // 10)
    return (shares, quote.ask if shares else None)

@dataclass
class AttemptRegistry:
    attempts: set = field(default_factory=set)
    def begin(self, symbol, session):
        key = (symbol, session)
        if key in self.attempts: return False
        self.attempts.add(key); return True

def child_quantity(quote, observed_market_shares, own_fills, now, remaining):
    quote.validate(now)
    if type(observed_market_shares) is not int or observed_market_shares < 0 or type(remaining) is not int or remaining < 0:
        raise EvidenceUnavailable("invalid participation shares")
    used = 0
    for time, qty in own_fills:
        finite(time)
        if type(qty) is not int or qty < 0 or time > now:
            raise EvidenceUnavailable("invalid or future own execution")
        if now - 60 < time <= now:
            used += qty
    return max(0, min(quote.ask_size // 10, math.floor(.02 * observed_market_shares) - used, remaining))

def exit_reason(bid, average_fill, d, now, first_fill, route_name, x, halted=False,
                flatten_at=None):
    finite(bid, average_fill, d, now, first_fill, x)
    if route_name not in {'continuation', 'recovery'}:
        raise EvidenceUnavailable("unknown route")
    if flatten_at is not None:
        finite(flatten_at)
    if min(bid, average_fill, d) <= 0 or now < first_fill:
        raise EvidenceUnavailable("invalid position/exit clock")
    if halted:
        return "pending_reopening"
    if flatten_at is not None and now >= flatten_at: return "scheduled_flatten"
    if bid <= average_fill * (1 - d): return "stop"
    if bid >= average_fill * (1 + 2 * d): return "target"
    if route_name == "recovery" and x >= 0: return "thesis"
    if now >= first_fill + 1800: return "time"
    return None

@dataclass
class ResearchLedger:
    """Long-only cash simulation; sale proceeds settle on supplied next session.

    This ledger consumes already evidenced executions; it does not assert a
    quote touched a limit or guarantee liquidity. Costs embedded in executable
    prices are not debited again. Fees are explicit separate cash debits.
    """
    cash: float
    orders: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    pending: list = field(default_factory=list)
    fees: float = 0.
    current_session: int = 1
    settlement_lag_sessions: int = 1
    execution_ids: set = field(default_factory=set)
    last_execution_time: float = -math.inf

    def __post_init__(self):
        finite(self.cash)
        if self.cash < 0: raise EvidenceUnavailable("negative initial cash")
        if type(self.current_session) is not int or self.current_session < 1:
            raise EvidenceUnavailable("invalid verified exchange-session ordinal")
        if type(self.settlement_lag_sessions) is not int or self.settlement_lag_sessions not in (1, 2):
            raise EvidenceUnavailable("verified historical T+1/T+2 settlement schedule required")

    def _execution(self, execution_id, time, session):
        finite(time)
        if not isinstance(execution_id, str) or not execution_id or execution_id in self.execution_ids:
            raise EvidenceUnavailable("missing or duplicate immutable execution ID")
        if type(session) is not int or session != self.current_session or time < self.last_execution_time:
            raise EvidenceUnavailable("reversed execution clock or wrong exchange session")

    def _record_execution(self, execution_id, time):
        self.execution_ids.add(execution_id)
        self.last_execution_time = time

    @property
    def reserved(self):
        return math.fsum(o["remaining"] * (o["cap"] + o["fee_ceiling_per_share"]) for o in self.orders.values())

    @property
    def free_cash(self): return self.cash - self.reserved

    def reserve(self, key, symbol, shares, cap, fee_ceiling_per_share=0.):
        finite(cap, fee_ceiling_per_share)
        if key in self.orders or type(shares) is not int or shares <= 0 or cap <= 0 or fee_ceiling_per_share < 0:
            raise EvidenceUnavailable("invalid or duplicate buy reservation")
        amount = shares * (cap + fee_ceiling_per_share)
        if amount > self.free_cash + 1e-8:
            raise EvidenceUnavailable("settled available cash insufficient")
        self.orders[key] = dict(symbol=symbol, remaining=shares, cap=cap, fee_ceiling_per_share=fee_ceiling_per_share)

    def fill(self, key, shares, price, time, fee=0., *, execution_id=None, session=None):
        finite(price, time, fee)
        self._execution(execution_id, time, session)
        o = self.orders[key]
        if type(shares) is not int or not 0 < shares <= o["remaining"] or price <= 0 or price > o["cap"] or not 0 <= fee <= shares * o["fee_ceiling_per_share"] + 1e-8:
            raise EvidenceUnavailable("unevidenced/invalid simulated fill")
        p = self.positions.setdefault(o["symbol"], dict(shares=0, cost=0., first_fill=time))
        if time < p["first_fill"]: raise EvidenceUnavailable("out-of-order execution")
        p["shares"] += shares; p["cost"] += shares * price
        self.cash -= shares * price + fee; self.fees += fee; o["remaining"] -= shares
        self._record_execution(execution_id, time)
        if not o["remaining"]: del self.orders[key]
        if self.free_cash < -1e-8: raise AssertionError("reservation self-financing failed")

    def cancel(self, key): self.orders.pop(key, None)

    def liquidate(self, symbol, shares, price, fee, settle_session, *,
                  execution_id=None, time=None, sale_session=None):
        finite(price, fee)
        self._execution(execution_id, time, sale_session)
        if type(settle_session) is not int or settle_session != sale_session + self.settlement_lag_sessions:
            raise EvidenceUnavailable("sale proceeds require verified historical exchange-session settlement")
        p = self.positions[symbol]
        if type(shares) is not int or not 0 < shares <= p["shares"] or price <= 0 or fee < 0 or fee > shares * price:
            raise EvidenceUnavailable("invalid sell execution")
        fraction = shares / p["shares"]
        p["cost"] *= 1 - fraction; p["shares"] -= shares
        self.pending.append((settle_session, shares * price - fee)); self.fees += fee
        self._record_execution(execution_id, time)
        if not p["shares"]: del self.positions[symbol]

    def settle(self, session):
        if type(session) is not int or session < self.current_session:
            raise EvidenceUnavailable("settlement session clock reversed")
        self.cash += math.fsum(amount for due, amount in self.pending if due <= session)
        self.pending = [(due, amount) for due, amount in self.pending if due > session]
        self.current_session = session

    def nav(self, executable_marks):
        stock = 0.
        for symbol, p in self.positions.items():
            if symbol not in executable_marks: raise EvidenceUnavailable("missing actual position mark")
            value = executable_marks[symbol]; finite(value)
            if value < 0: raise EvidenceUnavailable("negative mark")
            stock += p["shares"] * value
        return self.cash + math.fsum(a for _, a in self.pending) + stock
