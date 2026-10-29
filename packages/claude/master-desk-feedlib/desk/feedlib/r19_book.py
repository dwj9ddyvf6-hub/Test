"""The R19 runtime's per-book cycle (backend/r19_cli.py _cycle -> Ledger.process) for an equity cash book held on
this desk: the shared wrapper of the r19_timing and r19_tensor families.

Each pass, as the source did for each book: matured sale proceeds are released (Ledger._housekeeping), the book's
decision view is cut from the cycle snapshot by the source's own bounded_snapshot (vendored r19_cli), the vendored
evaluator decides on (snapshot, book) — book = the ledger's view: config, persisted strategy state, positions
(whole-unit quantity strings with the ledger's position metadata), settled cash, pending sale claims, installation
time —, cancel_signal_ids withdraw their working orders, then each intent is sized and priced by the ledger's
execution rules (desk.feedlib.r19_ledger) in the evaluator's order and sent to the desk's venue. The returned
strategy state is merged into the persisted state as Ledger.process merged it (a key the evaluator drops survives).
An evaluator exception leaves the book untouched for the pass and is recorded (the source's book_error health)."""
from datetime import datetime, timezone
from decimal import Decimal

from .. import calendar as dcal
from ..contract import Intent, OrderSpec, Sleeve
from . import r19_ledger as L
from . import r19_source as RS

UTC = timezone.utc
ZERO = Decimal(0)


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=UTC).isoformat()


def dec(x):
    return Decimal(str(x))


def reconcile(model, inflight, positions, working):
    """acknowledgement seam: once a decided fill's child has left the venue, units the venue did not execute are
    returned to the order (decided again on a later quote) and to the sale claim (desk.feedlib.r19_ledger.unfill)."""
    for sym in list(inflight):
        if sym in working:
            continue
        fills = inflight.pop(sym)
        now_q = dec(positions.get(sym, {}).get("quantity", 0))
        for f in reversed(fills):                      # the latest decision absorbs a shortfall first
            q = dec(f["quantity"])
            done = (now_q - dec(f["before"])) if f["side"] == "buy" else (dec(f["before"]) - now_q)
            L.unfill(model, f, q - min(max(done, ZERO), q))


class R19Book(Sleeve):
    """an R19 equity cash book on the desk. Subclasses set FEED (the cycle snapshot feed), MODULE (the vendored
    evaluator) and build CONFIG / rule."""
    FEED = ""
    MODULE = ""
    CHILD_WINDOW_S = 120
    INT_QUANTITY = False          # the ledger's book view carries quantities as the TEXT column's strings
    STATE_SCHEMA = {"evaluator": "dict", "installed_at": "str", "ledger": "dict", "metadata": "dict",
                    "inflight": "dict", "action_symbols": "list"}

    def positions_view(self, view, st):
        positions = {}
        for inst, p in view.positions.items():
            if not inst.startswith("EQ:") or float(p["qty"]) <= 0:
                continue
            sym = inst.split(":", 1)[1]
            meta = st.get("metadata", {}).get(sym) or (p.get("meta") or {}).get("position_meta") or {}
            q = int(round(float(p["qty"])))
            positions[sym] = {"symbol": sym, "quantity": q if self.INT_QUANTITY else str(q),
                              "cost": repr(float(p.get("avg") or 0)), "entry_at": iso(p.get("opened_at") or view.now),
                              "metadata": meta}
        return positions

    def evaluate(self, snapshot, book):
        return RS.vendored()[self.MODULE].evaluate(snapshot, book)

    def top_up(self, snap, symbols):
        """hook: quotes for held names the pass snapshot lacks (the tensor books' per-book refresh)."""

    def _note(self, reason, key, **meta):
        return Intent("signal", self.CONFIG.universe[0], reason=reason[:200], meta=meta, signal_key=key[:80])

    def warming_only(self, view):
        """a pass before a session's open (the families' premarket window): the view's feed has acquired the cycle
        snapshot for the open; nothing is decided, ordered or written (named divergence: acquisition time only)"""
        d = dcal._as_date(view.now)
        if dcal.is_trading_day(d) and float(view.now) < dcal.session_open(d):
            self._st = None
            return True
        return False

    def signal(self, view):
        if self.warming_only(view):
            return []
        cfg = self.rule
        snap = view.extra.get(self.FEED)
        st = dict(view.state or {})
        st.setdefault("installed_at", iso(view.now))
        st.setdefault("ledger", L.fresh())
        st.setdefault("metadata", {})
        st.setdefault("inflight", {})
        st.setdefault("action_symbols", [])
        self._st = st
        if not snap:
            return []
        if snap.get("blocked"):
            return [self._note(snap["blocked"], "blk:" + snap["blocked"][:40], blocker=snap["blocked"])]
        m = RS.vendored()
        model = st["ledger"]
        pending = view.extra.get("pending_orders") or []
        working = {p["inst"].split(":", 1)[1]: p for p in pending}
        positions = self.positions_view(view, st)
        self.top_up(snap, positions)
        reconcile(model, st["inflight"], positions, working)
        L.release(model, view.now)

        def claimed(u):                                # a sale still working at the venue has not paid in yet
            for fills in st["inflight"].values():
                for f in fills:
                    if f["order_id"] == u.get("order"):
                        p = working.get(f["symbol"])
                        return dec(u["amount"]) * (dec(p["filled_v"]) / dec(p["vqty"])
                                                   if p and float(p["vqty"] or 0) > 0 else ZERO)
            return dec(u["amount"])
        cash = dec(repr(float(view.cash))) - sum((claimed(u) for u in model["unsettled"]), ZERO)
        book = {"id": cfg["id"], "config": cfg, "state": dict(st.get("evaluator") or {}), "positions": positions,
                "cash": str(cash), "enabled": True, "installed_at": st["installed_at"],
                "unsettled": [dict(u) for u in model["unsettled"]], "action_symbols": sorted(st["action_symbols"])}
        snapshot = m["r19_cli"].bounded_snapshot(snap, book)
        try:
            out = self.evaluate(snapshot, book)
        except Exception as exc:                       # r19_cli: one book's failure is recorded, nothing changes
            err = f"book_error: {type(exc).__name__}: {exc}"
            return [self._note(err, "err:" + err[:60], book_error=err[:300])]
        state = dict(book["state"])
        state.update(out.get("state") or {})
        st["evaluator"] = state
        obs = out.get("observations") or {}
        census = obs.get("census")                     # how far the enrollment got (the tensor gate)
        failed = ["%s: %s" % (f.get("symbol"), str(f.get("reason"))[:120]) for f in obs.get("data_failures") or []]
        more = dict({"census": census} if census else {}, **({"data_failures": failed[:20]} if failed else {}))
        if census is not None or failed:               # EQ-09: every cycle's coverage receipt, on the book's state
            st["coverage"] = {"at": iso(view.now), "census": census, "data_failures": len(failed), "failures": failed[:20],
                              "blockers": [str(b)[:120] for b in out.get("blockers", [])[:5]]}
        intents = [self._note(f"blocker: {b}", "blk:" + str(b)[:60], blocker=str(b)[:300], **more)
                   for b in out.get("blockers", [])[:20]]
        cancelled = set(out.get("cancel_signal_ids", []))
        L.cancel(model, cancelled)
        for p in pending:
            sk = p.get("signal_key") or ""
            if any(sk.startswith(sid + ":") for sid in cancelled):
                intents.append(Intent("cancel", p["inst"].split(":", 1)[1], signal_key=sk,
                                      reason=f"{cfg['id']}: signal cancelled / expired"))
        nav = dec(repr(float(view.equity)))
        held_value = nav - dec(repr(float(view.cash)))
        actual = m["r19_core"].stamp(snapshot["asof"]).timestamp() + 0.001     # acknowledged after the snapshot
        for it in out["intents"]:
            sym = it.get("symbol")
            if sym in working:
                continue                                  # the decided remainder is still at the venue
            owned = dec(positions.get(sym, {}).get("quantity", 0))
            held_meta = positions.get(sym, {}).get("metadata") or {}
            fill, why = L.execute(model, cfg["id"], cfg, it, snapshot, owned, cash, nav, held_value, actual,
                                  owned_contract=held_meta.get("contract_id"))
            if fill is None:
                if why not in ("target_satisfied", "idempotent"):
                    sid = str(it.get("signal_id"))
                    intents.append(self._note(f"{sid[:12]}: {why}", f"gate:{sid[:16]}:{why[:40]}", gate=why))
                continue
            qty, px = fill["quantity"], fill["price"]
            meta = {"cost_bps": float(L.fee_rule(cfg, sym, px)), "signal_id": it["signal_id"],
                    "decided_qty": str(qty), "order_id": fill["order_id"]}
            key = f"{it['signal_id']}:{fill['side']}:{view.now}"
            st["inflight"].setdefault(sym, []).append(
                {"symbol": sym, "side": fill["side"], "quantity": str(qty), "before": str(owned),
                 "order_id": fill["order_id"], "depth_key": fill["depth_key"], "release_at": fill.get("release_at")})
            if sym not in st["action_symbols"]:
                st["action_symbols"].append(sym)
            if fill["side"] == "buy":                    # the ledger's position metadata: the first fill's intent
                pm = dict(held_meta) if owned > 0 else dict(it.get("metadata") or {})      # metadata, then the
                pm.update(contract_id=fill["contract_id"], asset_class=snapshot["quotes"][sym]["asset_class"],
                          last_fill_at=iso(actual))                 # contract / asset class / clock of each fill
                st["metadata"][sym] = pm
                cash -= qty * px + fill["fee"]
                positions.setdefault(sym, {"symbol": sym, "entry_at": iso(actual)}).update(
                    quantity=int(owned + qty) if self.INT_QUANTITY else str(owned + qty), metadata=pm)
                meta["position_meta"] = pm
                intents.append(Intent("enter", sym, qty=float(qty), price_hint=float(px), signal_key=key,
                                      reason=f"{cfg['id']} {it.get('reason')}: buy {qty} at the ask {px}"[:300],
                                      order=OrderSpec(window_s=self.CHILD_WINDOW_S), meta=meta))
            else:
                left = owned - qty
                if left > 0:
                    positions[sym]["quantity"] = int(left) if self.INT_QUANTITY else str(left)
                else:
                    positions.pop(sym, None)
                intents.append(Intent("exit", sym, qty=float(qty), price_hint=float(px), signal_key=key,
                                      reason=f"{cfg['id']} {it.get('reason')}: sell {qty} at the bid {px}"[:300],
                                      order=OrderSpec(window_s=self.CHILD_WINDOW_S), meta=meta))
        L.trim(model)
        live = set(positions) | set(working) | set(st["inflight"])
        st["metadata"] = {k: v for k, v in st["metadata"].items() if k in live}
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)
