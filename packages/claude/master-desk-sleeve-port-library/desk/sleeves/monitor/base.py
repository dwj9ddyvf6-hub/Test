"""The monitor sleeve: one manifest row = one ported source evaluator run over its universe on completed bars;
its output becomes observations on the ledger (Intent "signal"), never orders.

Observation policy (a named divergence shared by every monitor — the sources recomputed their read on every page
view / cron tick and displayed it; the desk records what changed):
  * mode "event": a bar-specific event (a marker printed, a range break on this bar) is recorded once for every
    completed bar on which the source reports it (signal_key symbol:bar:state);
  * mode "state": a persistent state (a regime, a watching hypothesis, a compression, a candidate pattern) is
    recorded when it is entered or changes, and once more when it clears ("cleared: <state>").
A symbol the data hub could not serve this pass keeps its previous state (no invented clear).

Every observation carries the source's own output for that symbol in meta["read"] (bounded), the state, the
previous state and the completed bar it was computed on."""
import json
from dataclasses import dataclass, field

from ...contract import Intent, Sleeve, SleeveConfig

MAX_META = 6000


@dataclass
class MonitorSpec:
    sleeve_id: str
    title: str
    source: dict
    evaluate: object                    # evaluate(view, monitor) -> {symbol: Obs | None}
    universe: tuple = ()
    needs: dict = field(default_factory=dict)
    schedule: str = "after_close+20:after_close+300"
    cadence_s: int = 6 * 3600
    mode: str = "state"                 # state | event
    params: dict = field(default_factory=dict)


@dataclass
class Obs:
    state: str                          # the decision-relevant output, e.g. "breakout-20:confirmed"
    reason: str
    bar_t: float                        # the completed bar the read was computed on
    read: dict = field(default_factory=dict)
    price: float = None


def _bounded(read):
    try:
        s = json.dumps(read, default=str)
    except (TypeError, ValueError):
        return {"unserializable": True}
    if len(s) <= MAX_META:
        return json.loads(s)
    return {"truncated": True, "head": s[:MAX_META]}


class Monitor(Sleeve):
    def __init__(self, spec):
        self.spec = spec
        self.CONFIG = SleeveConfig(sleeve_id=spec.sleeve_id, family="monitor", cadence_s=spec.cadence_s,
                                   universe=tuple(spec.universe), needs=spec.needs, schedule=spec.schedule,
                                   params=dict(spec.params, mode=spec.mode), source=dict(spec.source),
                                   status="monitor")
        self._next = None
        self.engine = None

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        self._extra = {}
        reads = self.spec.evaluate(view, self) or {}
        last = dict((view.state or {}).get("last") or {})
        out, intents = dict(last), []
        for sym in sorted(reads):
            ob = reads[sym]
            prev = last.get(sym) or {}
            if ob is None:
                if prev.get("state") and self.spec.mode == "state":
                    intents.append(Intent("signal", sym, reason=("cleared: " + prev["state"])[:300],
                                          meta={"state": None, "prev_state": prev["state"], "monitor": self.spec.title},
                                          signal_key="%s:cleared:%s:%s" % (sym, prev["state"][:60], prev.get("bar_t"))))
                out.pop(sym, None)
                continue
            new = {"state": ob.state, "bar_t": ob.bar_t}
            changed = ob.state != prev.get("state")
            if self.spec.mode == "event":
                changed = changed or ob.bar_t != prev.get("bar_t")
            if changed:
                intents.append(Intent("signal", sym, reason=ob.reason[:300], price_hint=ob.price,
                                      meta={"state": ob.state, "prev_state": prev.get("state"), "bar_t": ob.bar_t,
                                            "monitor": self.spec.title, "read": _bounded(ob.read)},
                                      signal_key="%s:%s:%s" % (sym, int(ob.bar_t), ob.state[:80])))
            out[sym] = new
        self._next = out
        return intents

    def update_state(self, view, intents):
        if self._next is None:
            return None
        st = dict(view.state or {})
        st["last"] = self._next
        st.update(self._extra or {})
        return st
