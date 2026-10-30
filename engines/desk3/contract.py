"""Sleeve contract — spec section 3 as code.

Every sleeve is ONE file with:
  * a config block (SleeveConfig: id, cadence, universe, state schema), and
  * a pure signal function: signal(bars, slice_state, context) -> [Intent]

A sleeve never touches the broker, never writes files, never mints order
ids, never reads the clock directly, never gates or sizes its own orders.
The clock arrives inside Context (injected by the dispatcher); the exit
rules a sleeve wants are expressed as DATA (ExitRule) the core executes.
Conformance is enforced statically by core/conformance.py.
"""
import math
from dataclasses import dataclass, field

EXIT_RULE_KINDS = {"stop", "target", "time_bars", "trailing_pct"}


@dataclass(frozen=True)
class ExitRule:
    """One exit rule as data: kind + numeric value (price, pct, or bar count)."""
    kind: str
    value: float

    def __post_init__(self):
        if self.kind not in EXIT_RULE_KINDS:
            raise ValueError(f"unknown exit-rule kind: {self.kind!r}")
        if not math.isfinite(float(self.value)):
            raise ValueError(f"non-finite exit-rule value: {self.value!r}")


POSITION_INTENTS = {"buy_to_open", "sell_to_open", "buy_to_close", "sell_to_close"}
_SIDE_FOR_INTENT = {"buy_to_open": "buy", "buy_to_close": "buy",
                    "sell_to_open": "sell", "sell_to_close": "sell"}


@dataclass(frozen=True)
class Intent:
    """A sleeve's only output. kind is 'enter' or 'exit'; sizing is a HINT —
    Risk owns the final quantity. price_hint/stop/target are reference
    prices from the signal bar, not order instructions.

    Wave-0 (2026-10-15) execution fields — OPTIONAL, core-owned semantics:
    `side` / `position_intent` / `legs` / `package_id` let a sleeve declare
    exactly how its intent must be submitted (sell_to_open, short, multi-leg
    package). Legacy sleeves declare the same facts in `reason` (the ported
    encoding the ports/*.md name); core/dispatch resolves BOTH encodings and
    REJECTS an intent whose declared side cannot be represented exactly —
    it never coerces a side.

    C-1/C-1b (2026-10-16, the owner's ruling "fix these now") representation
    fields — OPTIONAL, exact-order semantics: `qty` is the sleeve's OWN
    computed order quantity, carried exactly (fractional quantities are
    representable: crypto books size in fractions of a coin). When `qty`
    is set, dispatch submits it as-is — no whole-unit rounding, no
    risk-formula substitution. `limit_price` is an ORDER INSTRUCTION
    (unlike price_hint, which stays reference-only): when set, dispatch
    submits a limit order at exactly that price. The books that size
    fractionally or price their source orders as limits (donchian_crypto,
    the fwd recipes, morning_dip, qqq_put_ladder) declare these fields;
    every other sleeve is untouched by them."""
    kind: str
    symbol: str
    qty_hint: int | None = None
    qty: float | None = None
    limit_price: float | None = None
    price_hint: float | None = None
    stop: float | None = None
    target: float | None = None
    exit_rules: tuple = ()
    reason: str = ""
    side: str | None = None
    position_intent: str | None = None
    legs: tuple | None = None
    package_id: str | None = None
    # The date the underlying signal itself was confirmed, when the
    # sleeve knows it (Tensor's swing bar date, carried from the
    # staged decision). Distinct from the session the intent is
    # emitted in: a swing confirms once and may be re-signalled
    # while in age. Dispatch persists it on the signal_intent
    # ledger row so downstream readers (the setups curator) can
    # date the evidence instead of assuming it is today's.
    signal_date: str | None = None

    def __post_init__(self):
        if self.kind not in ("enter", "exit"):
            raise ValueError(f"intent kind must be enter|exit, got {self.kind!r}")
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("intent needs a symbol")
        if self.qty_hint is not None and (int(self.qty_hint) != self.qty_hint or self.qty_hint <= 0):
            raise ValueError(f"qty_hint must be a positive whole number, got {self.qty_hint!r}")
        if self.qty is not None:
            if self.qty_hint is not None:
                raise ValueError("intent declares both qty and qty_hint — one quantity, exactly")
            if isinstance(self.qty, bool) or not math.isfinite(float(self.qty)) or float(self.qty) <= 0:
                raise ValueError(f"qty must be a positive finite quantity, got {self.qty!r}")
        if self.limit_price is not None and (
                not math.isfinite(float(self.limit_price)) or float(self.limit_price) <= 0):
            raise ValueError(f"limit_price must be positive and finite, got {self.limit_price!r}")
        for name in ("price_hint", "stop", "target"):
            v = getattr(self, name)
            if v is not None and (not math.isfinite(float(v))
                                  or float(v) <= 0):
                raise ValueError(
                    f"intent {name} must be positive and finite, "
                    f"got {v!r}")
        if self.signal_date is not None:
            import datetime as _dt
            try:
                _dt.date.fromisoformat(self.signal_date)
            except (TypeError, ValueError):
                raise ValueError(
                    f"signal_date must be an ISO date, got {self.signal_date!r}")
        for r in self.exit_rules:
            if not isinstance(r, ExitRule):
                raise ValueError("exit_rules must be ExitRule data, not callables")
        if self.side is not None and self.side not in ("buy", "sell"):
            raise ValueError(f"intent side must be buy|sell, got {self.side!r}")
        if self.position_intent is not None:
            if self.position_intent not in POSITION_INTENTS:
                raise ValueError(f"unknown position_intent: {self.position_intent!r}")
            want = _SIDE_FOR_INTENT[self.position_intent]
            if self.side is not None and self.side != want:
                raise ValueError(
                    f"intent side {self.side!r} contradicts position_intent "
                    f"{self.position_intent!r} (requires {want!r})")
        if self.legs is not None:
            if not self.legs:
                raise ValueError("intent legs must be non-empty when given")
            for leg in self.legs:
                if not isinstance(leg, dict) or not leg.get("symbol"):
                    raise ValueError(f"intent leg needs a symbol: {leg!r}")
                pi = leg.get("position_intent")
                if pi is not None and pi not in POSITION_INTENTS:
                    raise ValueError(f"unknown leg position_intent: {pi!r}")
                ls = leg.get("side")
                if pi is not None and ls is not None and ls != _SIDE_FOR_INTENT[pi]:
                    raise ValueError(f"leg side {ls!r} contradicts position_intent {pi!r}")
                if ls is not None and ls not in ("buy", "sell"):
                    raise ValueError(f"leg side must be buy|sell, got {ls!r}")


@dataclass
class Context:
    """Everything a signal may know about 'now' and the world, injected by
    the core. `now` is epoch seconds from the dispatcher's clock — a sleeve
    reads context.now and NEVER the system clock (checker-enforced)."""
    now: float
    session: str  # ET session date, YYYY-MM-DD
    equity: float = 0.0
    # ACCOUNT equity (the broker account's total, from the door's
    # read-back cached at warm) — distinct from `equity`, which is the
    # sleeve's SLICE equity every sizing consumer uses. Only gate-
    # semantic consumers read this (spx_premium's $37k honesty gate is
    # an account-size rule; the sleeve never sizes off equity).
    # None = no account read-back available -> gates fail closed.
    account_equity: float | None = None
    market: dict = field(default_factory=dict)   # e.g. {"qqq_red": True, "regime": "yellow"}
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if not math.isfinite(float(self.now)):
            raise ValueError("context.now must be finite")


@dataclass(frozen=True)
class SleeveConfig:
    """The config block. risk_pct is by REFERENCE to Risk (the sleeve names
    its register value; it does not size its own orders). state_schema maps
    slice-state field names to type names the core persists verbatim."""
    sleeve_id: str
    cadence_s: int
    universe: tuple = ()
    state_schema: dict = field(default_factory=dict)
    risk_pct: float | None = None
    parked: bool = False  # ruling preserved on port (e.g. Decision #86); dispatcher skips entries
    monitor_only: bool = False  # MAC-4 (desk review 2026-10-19): the
    # sleeve is a MONITOR by its source contract — its signal() returns
    # [] unconditionally and forever (an unlisted instrument, a model-
    # test-only book, a spot book with no perpetual). It stays
    # registered (its status helper is a production record), but it is
    # not a trading sleeve: rolls and counts must name it as a monitor
    # instead of counting it among sleeves that can emit.
    settlement_exit: bool = False  # the sleeve's exit is a hard-deadline settlement
    # close (an expiring PM-settled index spread the broker will not accept
    # after the close): the dispatcher evaluates such sleeves FIRST in every
    # tick, so the intent -> submission lag is seconds, not a pass position
    # (SETTLEFIX, 2026-10-16 — see sleeves/spx_premium.py).

    def __post_init__(self):
        if not self.sleeve_id:
            raise ValueError("sleeve config needs an id")
        if int(self.cadence_s) <= 0:
            raise ValueError("cadence_s must be positive")


class BaseSleeve:
    """Base class form of the contract. A sleeve module sets CONFIG and
    implements signal(). A plain module-level `CONFIG` + `signal(...)`
    function pair is equally valid (the checker accepts either shape)."""
    CONFIG: SleeveConfig = None

    def signal(self, bars, slice_state, context):
        raise NotImplementedError

    def describe(self):
        c = self.CONFIG
        return {"id": c.sleeve_id, "cadence_s": c.cadence_s,
                "universe": list(c.universe), "state_schema": dict(c.state_schema),
                "risk_pct": c.risk_pct, "parked": c.parked}


class Registry:
    """Sleeves self-describe here; the dispatcher iterates the registry and
    nothing else — a sleeve that is not registered does not run."""
    def __init__(self):
        self._sleeves = {}

    def register(self, sleeve):
        desc = sleeve.describe() if hasattr(sleeve, "describe") else _describe_config(sleeve.CONFIG)
        sid = desc["id"]
        if sid in self._sleeves:
            raise ValueError(f"duplicate sleeve id: {sid}")
        self._sleeves[sid] = sleeve
        return sleeve

    def get(self, sleeve_id):
        return self._sleeves[sleeve_id]

    def all(self):
        return list(self._sleeves.values())

    def describe_all(self):
        return [s.describe() if hasattr(s, "describe") else _describe_config(s.CONFIG)
                for s in self._sleeves.values()]

    def clear(self):
        self._sleeves.clear()


def _describe_config(c):
    return {"id": c.sleeve_id, "cadence_s": c.cadence_s, "universe": list(c.universe),
            "state_schema": dict(c.state_schema), "risk_pct": c.risk_pct, "parked": c.parked}


REGISTRY = Registry()
