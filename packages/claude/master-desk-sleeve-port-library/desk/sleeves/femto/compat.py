"""Femto-lean sleeve contract, re-homed in the master desk.

Types and validation are core/sleeve.py of Femto-lean @7f2a996 (blob identical in behaviour: the 60
vendored sleeves import from here instead of `core.sleeve`, a one-line rewrite). The ONE extension:
Intent gains OPTIONAL structured fields, all defaulting to "absent", so a sleeve can state as data
what the femto dispatcher could only read from prose — the reason it bought the underlying for
put-spread, short and option signals:

  side           "long" | "short"                  (absent = long)
  asset          equity | crypto | option | mleg | perp | spot
  legs           ({"symbol", "side": buy|sell, "ratio", "position_intent"}, ...) for multi-leg packages
  qty            fractional quantity (crypto) where qty_hint (whole units) cannot carry it
  notional       size in quote currency
  position_meta  fields the sleeve wants stored on its position at fill (read back via sleeve_state)
  state          sleeve-private per-symbol state to persist (read back via sleeve_state[SYM])
  venue, order, signal_key, net_price   execution facts (net_price = mleg net limit, debit > 0)

An Intent built without these fields is exactly the femto Intent."""
import math
from dataclasses import dataclass, field

EXIT_RULE_KINDS = {"stop", "target", "time_bars", "trailing_pct", "earnings_flatten",
                   "stop_dist"}   # master-desk: stop_dist = a stop this far from the actual fill
ASSETS = (None, "equity", "crypto", "option", "mleg", "perp", "spot")


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


@dataclass(frozen=True)
class Intent:
    """A sleeve's only output. kind is 'enter' or 'exit'; sizing is a HINT —
    Risk owns the final quantity. price_hint/stop/target are reference
    prices from the signal bar, not order instructions."""
    kind: str
    symbol: str
    qty_hint: int | None = None
    price_hint: float | None = None
    stop: float | None = None
    target: float | None = None
    exit_rules: tuple = ()
    reason: str = ""
    # -- optional structure (master-desk extension; absent == femto semantics) --
    side: str | None = None
    asset: str | None = None
    legs: tuple = ()
    qty: float | None = None
    notional: float | None = None
    position_meta: dict | None = field(default=None, compare=False)
    state: dict | None = field(default=None, compare=False)
    venue: str | None = None
    order: dict | None = field(default=None, compare=False)
    signal_key: str | None = None
    net_price: float | None = None

    def __post_init__(self):
        if self.kind not in ("enter", "exit", "cancel"):     # cancel: master-desk (withdraw a working entry)
            raise ValueError(f"intent kind must be enter|exit|cancel, got {self.kind!r}")
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("intent needs a symbol")
        if self.qty_hint is not None and (int(self.qty_hint) != self.qty_hint or self.qty_hint <= 0):
            raise ValueError(f"qty_hint must be a positive whole number, got {self.qty_hint!r}")
        for name in ("price_hint", "stop", "target", "qty", "notional", "net_price"):
            v = getattr(self, name)
            if v is not None and not math.isfinite(float(v)):
                raise ValueError(f"non-finite intent {name}: {v!r}")
        for r in self.exit_rules:
            if not isinstance(r, ExitRule):
                raise ValueError("exit_rules must be ExitRule data, not callables")
        if self.side not in (None, "long", "short"):
            raise ValueError(f"intent side must be long|short, got {self.side!r}")
        if self.asset not in ASSETS:
            raise ValueError(f"intent asset {self.asset!r} not in {ASSETS[1:]}")
        if self.qty is not None and self.qty <= 0:
            raise ValueError("qty is a positive magnitude; use side for direction")
        for leg in self.legs:
            if not isinstance(leg, dict) or not leg.get("symbol") or leg.get("side") not in ("buy", "sell"):
                raise ValueError(f"leg must be a dict with symbol and side buy|sell, got {leg!r}")
        if self.asset == "mleg" and len(self.legs) < 2:
            raise ValueError("an mleg intent needs at least two legs")


@dataclass
class Context:
    """Everything a signal may know about 'now' and the world, injected by
    the core. `now` is epoch seconds from the dispatcher's clock — a sleeve
    reads context.now and NEVER the system clock (checker-enforced)."""
    now: float
    session: str  # ET session date, YYYY-MM-DD
    equity: float = 0.0
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
    """Sleeves self-describe here (kept for the ported femto tests)."""
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
