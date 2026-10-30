"""One trading pass, in the order that matters.

   recover  ->  exits first  ->  entries (caps, windows)  ->  reconcile  ->  snapshot/backup

Properties:
  * the whole pass runs under a monotonic deadline; side jobs run detached with their own limits;
  * each sleeve is wrapped in try/except: one bad input never aborts the pass for the others;
  * exits are evaluated BEFORE entries and never wait behind a slow entry path;
  * an exit that is due but has no observable price waits and alerts (it does not guess);
  * every decision that can create an order first writes an `intent` to the ledger.
"""
from __future__ import annotations
from typing import Callable

from .alerts import Alerts
from .broker import Order, Refused, SendUnknown
from .ids import client_order_id, signal_key
from .ledger import Ledger
from .netguard import PassDeadline


class Desk:
    def __init__(self, ledger: Ledger, broker, alerts: Alerts, sleeves: list, lanes: dict, mark: Callable[[str], float | None]):
        self.ledger, self.broker, self.alerts, self.sleeves, self.lanes, self.mark = ledger, broker, alerts, sleeves, lanes, mark

    def run_pass(self, deadline_s: float = 600.0) -> dict:
        dl = PassDeadline(deadline_s)
        summary = {"orders": 0, "skipped": 0, "errors": 0}
        self.ledger.append("pass_start", {})
        # 1. recover: read back every non-final order by cid (omitted here; see docs/06).
        # 2. exits first, 3. entries
        for phase in ("exits", "entries"):
            for sl in self.sleeves:
                if dl.expired():
                    self.alerts.raise_("pass_deadline", "warn", f"pass deadline hit during {phase}")
                    break
                try:
                    for intent in getattr(sl, phase)():
                        self._execute(intent, summary)
                except Exception as e:                       # isolate the sleeve, keep going
                    summary["errors"] += 1
                    self.alerts.raise_(f"sleeve_error:{sl.name}", "warn", repr(e))
        self.ledger.append("pass_end", summary)
        return summary

    def _execute(self, it: dict, summary: dict):
        key = signal_key(it["sleeve"], it["symbol"], it["bar_ts"], it["kind"], it["side"])
        cid = client_order_id("dsk", key, attempt=it.get("attempt", 0))
        if self.ledger.has("entry_sent" if it["kind"] == "entry" else "exit_sent", cid=cid):
            summary["skipped"] += 1                          # restart-safe dedupe: already sent
            self.ledger.append("intent_skipped", {"cid": cid, "why": "duplicate"})
            return
        if it["kind"] == "exit" and self.mark(it["symbol"]) is None:
            self.alerts.raise_(f"no_mark:{it['symbol']}", "warn", "exit due but no observable price; waiting")
            return
        lane = self.lanes.get(it["sleeve"])
        if it["kind"] == "entry":
            if lane is None or not lane.can_take():
                summary["skipped"] += 1
                self.ledger.append("blocked", {"cid": cid, "why": "lane_full", "sleeve": it["sleeve"]})
                return
            lane.take()
        # PERSIST the id BEFORE the network call.
        self.ledger.append("entry_sent" if it["kind"] == "entry" else "exit_sent", {"cid": cid, **{k: it[k] for k in ("sleeve", "symbol", "side", "qty")}})
        try:
            res = self.broker.submit(Order(cid, it["symbol"], it["side"], it["qty"], it.get("limit")))
        except Refused:
            if it["kind"] == "entry" and lane:
                lane.release()
            self.ledger.append("refused", {"cid": cid})
            return
        except SendUnknown:
            self.ledger.append("send_unknown", {"cid": cid})  # resolved next pass by lookup(cid)
            return
        summary["orders"] += 1
        if res.status == "filled":
            self.ledger.append("fill", {"cid": cid, "sleeve": it["sleeve"], "symbol": it["symbol"], "side": it["side"],
                                        "qty": res.filled_qty, "price": res.avg_price})
