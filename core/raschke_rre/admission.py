"""SPY-linear admission, adapted from Astra's RRE v0.2.0
execution.py (PORT-SPEC section 2.5). Pure decision only: no
broker, reservation, order, or P&L code. Dropped in adaptation
(each named in ports/raschke_rre.md): ES/MES futures branches and
instrument validation, admit_spy_0dte entire, OptionContract,
Greeks, BrokerDeadlines, OptionLimits, canonical_option_limits,
_canonical_options. LinearInstrument is SPY-only: kind must be
"SPY", multiplier 1, symbol SPY. The 0/0 quote-depth desk ruling
(PORT-SPEC section 6.5) lives in the sleeve wrapper, which marks
depth unknown before constructing the Quote; this module's math
is his, unchanged for every input it receives.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
import math

from .raschke_core import Session, _dt, _number, _integer, _identifier


def _D(value):
    return Decimal(str(value))


def _nums(obj, names, positive=False):
    for name in names.split():
        object.__setattr__(obj, name, _number(getattr(obj, name), name, minimum=0, strictly_positive=positive))


def _times(obj, names):
    for name in names.split():
        object.__setattr__(obj, name, _dt(getattr(obj, name), name))


def _bools(obj, names):
    for name in names.split():
        if not isinstance(getattr(obj,name),bool):
            raise ValueError(f"{name}: bool required")


def _durations(obj, names):
    # These are buffers inside one execution session, not multi-day timers.
    for name in names.split():
        if getattr(obj,name)>86400:raise ValueError(f"{name}: exceeds one day")


@dataclass(frozen=True)
class Quote:
    quote_id: str
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    event_at: datetime
    received_at: datetime
    feed: str
    session_id: str
    size_unit: str
    conditions_accepted: bool
    sequence_complete: bool
    entitlement_verified: bool

    def __post_init__(self):
        for key in ("quote_id","symbol","feed","session_id","size_unit"):
            _identifier(getattr(self,key),key)
        _nums(self,"bid ask")
        _integer(self.bid_size,"bid_size");_integer(self.ask_size,"ask_size")
        _times(self,"event_at received_at")
        _bools(self,"conditions_accepted sequence_complete entitlement_verified")


@dataclass(frozen=True)
class Costs:
    entry_slippage_price: float
    additional_exit_cost_price: float
    round_trip_fee_per_unit: float
    stress_loss_per_unit: float

    def __post_init__(self):
        _nums(self,"entry_slippage_price additional_exit_cost_price round_trip_fee_per_unit")
        _nums(self,"stress_loss_per_unit",positive=True)


@dataclass(frozen=True)
class RiskSnapshot:
    snapshot_id: str
    as_of: datetime
    valid_until: datetime
    risk_remaining: float
    session_loss_remaining: float
    stress_remaining: float
    buying_power_remaining: float
    gross_notional_remaining: float
    max_units_remaining: int
    depth_units_remaining: int
    delivery_cash_remaining: float
    delivery_shares_remaining: int

    def __post_init__(self):
        _identifier(self.snapshot_id,"snapshot_id");_times(self,"as_of valid_until")
        if self.valid_until <= self.as_of:raise ValueError("invalid risk validity interval")
        _nums(self,"risk_remaining session_loss_remaining stress_remaining buying_power_remaining gross_notional_remaining delivery_cash_remaining")
        for key in ("max_units_remaining","depth_units_remaining","delivery_shares_remaining"):
            _integer(getattr(self,key),key)


@dataclass(frozen=True)
class Gates:
    reconciled: bool
    account_permitted: bool
    event_coverage_known: bool
    events_clear: bool
    market_open: bool
    borrow_verified: bool
    residual_policy_verified: bool

    def __post_init__(self):
        _bools(self,"reconciled account_permitted event_coverage_known events_clear market_open borrow_verified residual_policy_verified")


@dataclass(frozen=True)
class Limits:
    max_quote_age_seconds: float
    max_receive_age_seconds: float
    max_risk_age_seconds: float
    max_spread_price: float
    max_spread_fraction: float
    depth_participation: float
    chase_atr_multiple: float
    adverse_gap_atr_multiple: float
    min_net_rr: float
    max_crossing_cost_dollars: float
    max_crossing_cost_fraction: float
    entry_delay_seconds: float
    linear_flatten_buffer_seconds: float
    allowed_linear_feeds: tuple[str,...]

    def __post_init__(self):
        _nums(self,"max_quote_age_seconds max_receive_age_seconds max_risk_age_seconds",positive=True)
        _nums(self,"max_spread_price max_spread_fraction depth_participation chase_atr_multiple adverse_gap_atr_multiple min_net_rr max_crossing_cost_dollars max_crossing_cost_fraction entry_delay_seconds linear_flatten_buffer_seconds")
        if not 0 < self.depth_participation <= 1 or self.max_spread_fraction > 1 or self.max_crossing_cost_fraction > 1:
            raise ValueError("invalid fractional limit")
        if not isinstance(self.allowed_linear_feeds,tuple) or not self.allowed_linear_feeds:
            raise ValueError("explicit allowed_linear_feeds tuple required")
        for value in self.allowed_linear_feeds:_identifier(value,"allowed feed")
        _durations(self,"entry_delay_seconds linear_flatten_buffer_seconds")


@dataclass(frozen=True)
class LinearInstrument:
    symbol: str
    kind: str
    multiplier: float
    tick_size: float
    margin_per_unit: float
    verified_at: datetime
    valid_until: datetime
    last_trade_at: datetime
    short_allowed: bool
    exchange_limits_verified: bool

    def __post_init__(self):
        _identifier(self.symbol,"symbol")
        if self.kind != "SPY":raise ValueError("unsupported linear instrument")
        _nums(self,"multiplier tick_size",positive=True);_nums(self,"margin_per_unit")
        _times(self,"verified_at valid_until last_trade_at")
        _bools(self,"short_allowed exchange_limits_verified")
        if self.valid_until <= self.verified_at:raise ValueError("invalid instrument validity interval")
        if self.multiplier != 1:raise ValueError("instrument multiplier mismatch")
        if self.symbol != "SPY":raise ValueError("SPY identity mismatch")


def canonical_limits(*,max_risk_age_seconds,max_spread_price,max_spread_fraction,
                     depth_participation,adverse_gap_atr_multiple,
                     max_crossing_cost_dollars,max_crossing_cost_fraction,
                     allowed_linear_feeds):
    """Conservative profile template; liquidity/risk-dependent inputs stay required."""
    return Limits(1,1,max_risk_age_seconds,max_spread_price,max_spread_fraction,
                  depth_participation,.2,adverse_gap_atr_multiple,1.2,
                  max_crossing_cost_dollars,max_crossing_cost_fraction,
                  1800,300,allowed_linear_feeds)


@dataclass(frozen=True)
class Admission:
    allowed: bool
    reason: str
    source_id: str
    expression: str
    units: int = 0
    entry_limit: float | None = None
    reserved_risk: float = 0.0
    reserved_buying_power: float = 0.0
    reserved_gross_notional: float = 0.0
    reserved_delivery_cash: float = 0.0
    reserved_delivery_shares: int = 0
    underlying_net_rr: float | None = None
    flatten_at: datetime | None = None
    entry_expires_at: datetime | None = None
    max_hold_seconds: int = 0
    quote_ids: tuple[str,...] = ()
    risk_snapshot_id: str = ""
    reserved_stress: float = 0.0


def _intent(intent):
    d={name:getattr(intent,name) for name in ("source_id","variant","symbol","direction","signal_at","available_at","expires_at","entry_reference","trigger","stop","target","atr14","session_id","session_close","max_hold_seconds")}
    for key in ("source_id","variant","symbol","session_id"):_identifier(d[key],key)
    if isinstance(d["direction"],bool) or d["direction"] not in (-1,1):raise ValueError("invalid intent direction")
    for key in ("signal_at","available_at","expires_at","session_close"):d[key]=_dt(d[key],key)
    for key in ("entry_reference","trigger","stop","target","atr14"):d[key]=_number(d[key],key,strictly_positive=True)
    _integer(d["max_hold_seconds"],"max_hold_seconds",1)
    if not d["signal_at"] <= d["available_at"] < d["expires_at"] <= min(d["signal_at"]+timedelta(minutes=5),d["session_close"]):
        raise ValueError("invalid intent clocks")
    return d


def _reject(d,expression,reason):
    return Admission(False,reason,d["source_id"],expression)


def _common(d,session,now,risk,gates,limits):
    if not isinstance(session,Session):raise ValueError("Session required")
    if d["session_id"] != session.id or d["session_close"] != session.close:return "SESSION_MISMATCH"
    if not session.open <= d["signal_at"] < session.close:return "SIGNAL_OUTSIDE_SESSION"
    if now < d["available_at"]:return "INTENT_NOT_AVAILABLE"
    if now >= d["expires_at"]:return "INTENT_EXPIRED"
    if not session.open+timedelta(seconds=limits.entry_delay_seconds) <= now < session.close:return "ENTRY_WINDOW_CLOSED"
    if not risk.as_of <= now < risk.valid_until or (now-risk.as_of).total_seconds()>limits.max_risk_age_seconds:return "RISK_SNAPSHOT_STALE"
    for key,reason in (("reconciled","UNRECONCILED"),("account_permitted","ACCOUNT_NOT_PERMITTED"),("event_coverage_known","EVENT_COVERAGE_UNKNOWN"),("events_clear","EVENT_BLACKOUT"),("market_open","MARKET_NOT_OPEN")):
        if not getattr(gates,key):return reason
    return None


def _quote(q,d,now,limits,feeds,size_unit,max_spread,max_fraction):
    if q.session_id != d["session_id"]:return "QUOTE_SESSION_MISMATCH"
    if q.feed not in feeds or not q.entitlement_verified:return "QUOTE_FEED_UNVERIFIED"
    if not q.conditions_accepted or not q.sequence_complete:return "QUOTE_CONDITION_OR_SEQUENCE"
    if q.size_unit != size_unit:return "QUOTE_SIZE_UNIT"
    if not 0 < q.bid <= q.ask or min(q.bid_size,q.ask_size)<=0:return "QUOTE_PRICE_OR_DEPTH"
    if not d["available_at"] < q.event_at <= q.received_at <= now:return "QUOTE_CLOCK_OR_PREINTENT"
    if (now-q.event_at).total_seconds()>limits.max_quote_age_seconds or (now-q.received_at).total_seconds()>limits.max_receive_age_seconds:return "QUOTE_STALE"
    spread=_D(q.ask)-_D(q.bid)
    if spread>_D(max_spread) or spread/((_D(q.ask)+_D(q.bid))/2)>_D(max_fraction):return "QUOTE_SPREAD"
    return None


def _geometry(d,entry,cost,limits):
    direction=d["direction"]
    entry,cost=_D(entry),_D(cost)
    if direction*(entry-_D(d["trigger"]))<0:return "TRIGGER_LOST",None
    if abs(entry-_D(d["trigger"]))>_D(limits.chase_atr_multiple)*_D(d["atr14"]):return "NO_CHASE",None
    if direction*(entry-_D(d["entry_reference"]))>_D(limits.adverse_gap_atr_multiple)*_D(d["atr14"]):return "ADVERSE_GAP",None
    loss=direction*(entry-_D(d["stop"]));room=direction*(_D(d["target"])-entry)
    if loss<=0 or room<=0:return "INVALID_GEOMETRY",None
    if room-cost<=0:return "NO_NET_ROOM",None
    rr=(room-cost)/(loss+cost)
    if not math.isfinite(float(rr)):return "DERIVED_NONFINITE",None
    if rr<_D(limits.min_net_rr):return "NET_RR",float(rr)
    return None,float(rr)


def _limit(price,tick,buy,slippage=0):
    direction=ROUND_FLOOR if buy else ROUND_CEILING
    cap=_D(price)+(1 if buy else -1)*_D(slippage)
    return float((cap/_D(tick)).to_integral_value(rounding=direction)*_D(tick))


def _tick_aligned(q,tick):
    # Enough precision for every finite binary-float decimal representation.
    with localcontext() as context:
        context.prec=1000
        return _D(q.bid)%_D(tick)==0 and _D(q.ask)%_D(tick)==0


def _size(risk,loss,stress,buying_power,notional,depth,delivery_cash=0,delivery_shares=0):
    if not all(math.isfinite(x) and x>0 for x in (loss,stress,buying_power,notional)):return 0
    capacities=[_D(risk.max_units_remaining),_D(risk.depth_units_remaining),_D(depth),
                _D(risk.risk_remaining)/_D(loss),_D(risk.session_loss_remaining)/_D(loss),
                _D(risk.stress_remaining)/_D(stress),_D(risk.buying_power_remaining)/_D(buying_power),
                _D(risk.gross_notional_remaining)/_D(notional)]
    if delivery_cash:capacities.append(_D(risk.delivery_cash_remaining)/_D(delivery_cash))
    if delivery_shares:capacities.append(_D(risk.delivery_shares_remaining)/_D(delivery_shares))
    return max(0,math.floor(min(capacities)))


def _crossing_ok(crossing,loss,limits):
    return math.isfinite(crossing) and _D(crossing)<=_D(limits.max_crossing_cost_dollars) and _D(crossing)<=_D(limits.max_crossing_cost_fraction)*_D(loss)


def admit_linear(intent,quote,instrument,costs,risk,gates,limits,session,now):
    """Return an admission proposal for SPY shares."""
    d=_intent(intent);now=_dt(now,"now");kind=instrument.kind
    failure=_common(d,session,now,risk,gates,limits)
    if failure:return _reject(d,kind,failure)
    if d["variant"] not in ("RRE1","RRE2"):return _reject(d,kind,"UNSUPPORTED_PROFILE")
    if d["symbol"]!=instrument.symbol or quote.symbol!=instrument.symbol:return _reject(d,kind,"INSTRUMENT_MISMATCH")
    if not instrument.verified_at<=now<min(instrument.valid_until,instrument.last_trade_at):return _reject(d,kind,"INSTRUMENT_REFERENCE_STALE")
    if not instrument.exchange_limits_verified:return _reject(d,kind,"EXCHANGE_LIMITS_UNKNOWN")
    if d["direction"]<0 and (not instrument.short_allowed or kind=="SPY" and not gates.borrow_verified):return _reject(d,kind,"SHORT_NOT_EXPRESSIBLE")
    if d["direction"]<0 and kind=="SPY" and instrument.margin_per_unit<=0:return _reject(d,kind,"SHORT_MARGIN_UNKNOWN")
    failure=_quote(quote,d,now,limits,limits.allowed_linear_feeds,"shares" if kind=="SPY" else "contracts",limits.max_spread_price,limits.max_spread_fraction)
    if failure:return _reject(d,kind,failure)
    if not _tick_aligned(quote,instrument.tick_size):return _reject(d,kind,"QUOTE_OFF_TICK")
    flatten=session.close-timedelta(seconds=limits.linear_flatten_buffer_seconds)
    if now>=flatten:return _reject(d,kind,"FLATTEN_WINDOW")
    buy=d["direction"]>0;reference=quote.ask if buy else quote.bid
    if d["direction"]*(_D(reference)-_D(d["trigger"]))<0:return _reject(d,kind,"TRIGGER_LOST")
    entry=_limit(reference,instrument.tick_size,buy,costs.entry_slippage_price)
    if entry<=0 or buy and entry<quote.ask or not buy and entry>quote.bid:return _reject(d,kind,"NO_MARKETABLE_LIMIT")
    additional=float(_D(costs.additional_exit_cost_price)+_D(costs.round_trip_fee_per_unit)/_D(instrument.multiplier))
    failure,rr=_geometry(d,entry,additional,limits)
    if failure:return _reject(d,kind,failure)
    loss=float(_D(instrument.multiplier)*(d["direction"]*(_D(entry)-_D(d["stop"]))+_D(costs.additional_exit_cost_price))+_D(costs.round_trip_fee_per_unit))
    crossing=float(_D(instrument.multiplier)*((_D(quote.ask)-_D(quote.bid))+_D(costs.entry_slippage_price)+_D(costs.additional_exit_cost_price))+_D(costs.round_trip_fee_per_unit))
    if not _crossing_ok(crossing,loss,limits):return _reject(d,kind,"CROSSING_COST")
    buying_power=(entry if kind=="SPY" and buy else instrument.margin_per_unit)+costs.round_trip_fee_per_unit
    notional=entry*instrument.multiplier
    depth=math.floor(_D(quote.ask_size if buy else quote.bid_size)*_D(limits.depth_participation))
    stress=max(loss,costs.stress_loss_per_unit)
    units=_size(risk,loss,stress,buying_power,notional,depth)
    if units<1:return _reject(d,kind,"ZERO_CAPACITY")
    return Admission(True,"ADMITTED",d["source_id"],kind,units,entry,units*loss,
                     units*buying_power,units*notional,underlying_net_rr=rr,
                     flatten_at=flatten,entry_expires_at=min(d["expires_at"],flatten),
                     max_hold_seconds=d["max_hold_seconds"],quote_ids=(quote.quote_id,),risk_snapshot_id=risk.snapshot_id,
                     reserved_stress=units*stress)


