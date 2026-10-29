"""Native sleeve contract. A sleeve is pure: scan() proposes entries from DataHub evidence, exit_reason() judges one open
position. It never touches the broker, ledger or clock (ctx.now is injected). Core owns orders, sizing caps and accounting."""
from dataclasses import dataclass, field

@dataclass
class Signal:
    symbol: str
    key: str            # unique signal identity (symbol|bar time|rule) -> deterministic cid
    px: float           # reference price (signal close)
    score: float = 0.0  # ranking within the sleeve (higher first)
    qty: float | None = None        # optional exact qty (target-weight books)
    meta: dict = field(default_factory=dict)

class Sleeve:
    sid = ""; source = ""; owner = "md2"; family = ""; tf = "1d"; slots = 10; principal = 100_000.0
    pos_frac = 0.1; dv_cap = 0.01; status = "installed"; reason = ""; dedupe = None; venue = "shadow"
    def scan(self, hub, ctx): return []
    def exit_reason(self, hub, pos, ctx): return None
    def describe(self): return dict(sid=self.sid, source=self.source, owner=self.owner, family=self.family, tf=self.tf,
                                    slots=self.slots, principal=self.principal, status=self.status, reason=self.reason, venue=self.venue)
