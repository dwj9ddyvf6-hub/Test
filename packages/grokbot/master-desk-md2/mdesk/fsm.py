"""Per-(sleeve,symbol) position state machine, folded from ledger events.
flat -> pending (entry order sent) -> open (filled) -> exiting (exit order sent) -> flat (exit filled)
pending -> flat (entry cancelled/rejected/expired). Illegal transitions raise: they mean a bug, never silently pass."""
FLAT, PENDING, OPEN, EXITING = "flat", "pending", "open", "exiting"
T = {("flat", "entry_sent"): PENDING, ("pending", "entry_filled"): OPEN, ("pending", "entry_void"): FLAT,
     ("open", "exit_sent"): EXITING, ("exiting", "exit_filled"): FLAT, ("exiting", "exit_void"): OPEN,
     ("open", "manage"): OPEN, ("open", "adjust_filled"): OPEN, ("pending", "manage"): PENDING, ("exiting", "manage"): EXITING}

class IllegalTransition(Exception): pass

class Book:
    """Fold of events -> positions + cash + realized P&L per sleeve. Correct accounting is a pure function of the ledger."""
    def __init__(self):
        self.pos = {}      # (sleeve,sym) -> dict(state, qty, avg, entry_ts, bars_held, cid, meta)
        self.cash = {}     # sleeve -> cash
        self.realized = {} # sleeve -> realized pnl
        self.fees = {}
        self.seq = 0
    def apply(self, e):
        k = e["kind"]; sl = e["sleeve"]; self.seq = max(self.seq, e.get("seq", 0))
        if k == "fund": self.cash[sl] = self.cash.get(sl, 0.0) + float(e["amount"]); return
        if k == "note":
            p = self.pos.get((sl, e.get("symbol")))
            if p is not None and "t1_done" in e: p["t1_done"] = bool(e["t1_done"])
            return
        if k not in ("entry_sent", "entry_filled", "entry_void", "exit_sent", "exit_filled", "exit_void", "manage", "adjust_filled"): return
        key = (sl, e["symbol"]); p = self.pos.get(key) or dict(state=FLAT, qty=0.0, avg=0.0)
        nxt = T.get((p["state"], k))
        if nxt is None: raise IllegalTransition(f"{key} {p['state']} --{k}--> ?")
        if k == "entry_sent": p.update(cid=e["cid"], entry_ts=e["ts"], meta=e.get("meta", {}), bars_held=0, signal_key=e.get("signal_key"))
        elif k == "entry_filled":
            q, px, fee = float(e["qty"]), float(e["price"]), float(e.get("fee", 0))
            p["avg"] = px; p["qty"] = q; p["fill_ts"] = e["ts"]; p["peak"] = px
            self.cash[sl] = self.cash.get(sl, 0.0) - q * px - fee; self.fees[sl] = self.fees.get(sl, 0) + fee
        elif k == "exit_sent": p["exit_cid"] = e["cid"]; p["exit_reason"] = e.get("reason")
        elif k == "exit_filled":
            q, px, fee = float(e["qty"]), float(e["price"]), float(e.get("fee", 0))
            self.cash[sl] = self.cash.get(sl, 0.0) + q * px - fee; self.fees[sl] = self.fees.get(sl, 0) + fee
            self.realized[sl] = self.realized.get(sl, 0.0) + q * (px - p["avg"]) - fee - p.get("entry_fee", 0)
            p = dict(state=FLAT, qty=0.0, avg=0.0)
        elif k == "adjust_filled":   # rebalance: signed qty delta at price (target-weight books)
            dq, px, fee = float(e["dqty"]), float(e["price"]), float(e.get("fee", 0))
            if dq < 0: self.realized[sl] = self.realized.get(sl, 0.0) + (-dq) * (px - p["avg"]) - fee
            else: p["avg"] = (p["avg"] * p["qty"] + dq * px) / (p["qty"] + dq)
            p["qty"] += dq; self.cash[sl] = self.cash.get(sl, 0.0) - dq * px - fee; self.fees[sl] = self.fees.get(sl, 0) + fee
        elif k == "manage": p["bars_held"] = int(e.get("bars_held", p.get("bars_held", 0))); p["peak"] = max(p.get("peak", 0), float(e.get("px", 0)))
        if k == "entry_filled": p["entry_fee"] = float(e.get("fee", 0))
        p["state"] = nxt; self.pos[key] = p
    @classmethod
    def replay(cls, ledger):
        b = cls()
        for e in ledger.events(): b.apply(e)
        return b
    def open_positions(self, sleeve=None):
        return {k: v for k, v in self.pos.items() if v["state"] != FLAT and (sleeve is None or k[0] == sleeve)}
    def equity(self, sleeve, marks):
        return self.cash.get(sleeve, 0.0) + sum(v["qty"] * marks.get(k[1], v["avg"]) for k, v in self.pos.items() if k[0] == sleeve and v["state"] in (OPEN, EXITING))
