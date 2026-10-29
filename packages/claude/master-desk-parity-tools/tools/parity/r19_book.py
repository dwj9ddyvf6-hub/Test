"""R19 per-book cycle parity: the SOURCE cycle — the vendored r19_cli._current_book + r19_cli.bounded_snapshot +
r19_core.Ledger.process (housekeeping, cancel_signal_ids, _execute, settlement, state merge) — vs the port's
desk.feedlib.r19_book.R19Book.signal on a desk book that fills each emitted intent at its price (the venue
acknowledgement held exact), on the r19_ledger harness's randomized cases (tools/parity/r19_ledger.py: random R19
timing or tensor config, 8-24 cycles across sessions, settlement releases, stale / indicative / inactive /
re-contracted quotes, depth from zero, stable re-emitted, changed, expired and cancelled signal ids).

Both sides call one pure stub evaluator per cycle (the pre-drawn intents and cancels; it also records the book
view it is handed and returns a state carrying one dropped and one counted key), so the comparison covers exactly
the wrapper: the book view (quantities, settled cash, unsettled claims, installation clock), the bounded decision
view, cancellation, execution order, fills, fees, settlement claims and the desk book's cash / holdings, and the
merged strategy state. The case config's symbols are the case's names (bounded_snapshot keeps only a book's own
names); the source runs with its spread gate neutralised, as in r19_ledger. Compared per cycle: each fill (symbol,
side, quantity, price, fee, order id), the evaluator's view of cash / positions / unsettled, and the persisted
state; at the end: settled cash + unsettled claims vs the desk book's cash, and the holdings.

    python3 -m tools.parity.run r19_book"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

from tools.parity import write_receipt
from tools.parity import r19_ledger as LH

UTC = timezone.utc
N_CASES = int(os.environ.get("R19_BOOK_CASES", "1200"))


def _norm(x):
    return str(Decimal(str(x)).normalize())


def _stub(cyc, intents, seen):
    def evaluator(snapshot, book):
        pos = {s: str(p["quantity"]) for s, p in sorted(book.get("positions", {}).items())}
        unsettled = sum((Decimal(str(u.get("amount"))) for u in (book.get("unsettled") or [])), Decimal(0))
        seen.append({"cash": _norm(book.get("cash", 0)), "positions": {s: _norm(q) for s, q in pos.items()},
                     "unsettled": _norm(unsettled), "quotes": sorted((snapshot.get("quotes") or {}))})
        state = dict(book.get("state") or {})
        state.pop("dropped", None)                      # a key the evaluator drops survives the merge
        state["n"] = int(state.get("n", 0)) + 1
        if not state.get("dropped_once"):
            state["dropped"] = True
            state["dropped_once"] = True
        return {"intents": [dict(x) for x in intents], "cancel_signal_ids": list(cyc["cancels"]),
                "state": state, "blockers": [], "observations": {}}
    return evaluator


def _case(seed):
    c = LH.case(seed)
    c["cfg"] = dict(c["cfg"], symbols=list(c["syms"]))
    return c


def _snap(c, cyc, held):
    s = LH._snapshot(c, cyc, held)
    s["now"] = s["asof"]
    s["r19_tensor_quote_symbols"] = list(c["syms"])
    return s


def source_run(c):
    from tools.parity.batch_tmp import case_tmp
    with case_tmp() as d:                     # the source ledger's sqlite, removed however the case ends
        return _source_run(c, d)


def _source_run(c, d):
    from desk.feedlib import r19_source as RS
    m = RS.vendored()
    core, cli = m["r19_core"], m["r19_cli"]
    clock = [0.0]
    led = core.Ledger(os.path.join(d, "r19.sqlite"), clock=lambda: datetime.fromtimestamp(clock[0], tz=UTC))
    start = c["cycles"][0]["t"] - 60
    led.install([c["cfg"]], enabled=True, at=datetime.fromtimestamp(start, tz=UTC).isoformat())
    bid = c["cfg"]["id"]
    out, seen, held, views, states = [], 0, {}, [], []
    for i, cyc in enumerate(c["cycles"]):
        snap = _snap(c, cyc, held)
        intents = LH._intents(c, cyc, snap)
        clock[0] = cyc["t"] + 0.001
        book = cli._current_book(led, bid)
        try:
            led.process(bid, cli.bounded_snapshot(snap, book), _stub(cyc, intents, views))
        except Exception as e:
            out.append([i, "error", type(e).__name__])
        con = sqlite3.connect(os.path.join(d, "r19.sqlite"))
        for seq, kind, payload in con.execute("SELECT seq,kind,payload_json FROM r19_events WHERE book_id=? AND seq>? "
                                              "ORDER BY seq", (bid, seen)).fetchall():
            seen = seq
            if kind == "fill":
                p = json.loads(payload)
                out.append([i, "fill", p["symbol"], p["side"], _norm(p["quantity"]), _norm(p["price"]),
                            _norm(p["fee"]), p["order_id"]])
        held = {r[0]: json.loads(r[1]).get("contract_id") for r in
                con.execute("SELECT symbol,metadata_json FROM r19_positions WHERE book_id=?", (bid,))}
        st = json.loads(con.execute("SELECT state_json FROM r19_books WHERE id=?", (bid,)).fetchone()[0])
        states.append({k: v for k, v in st.items() if k != "last_evaluation"})
        con.close()
    book = led.books()[0]
    unsettled = sum((Decimal(s["amount"]) for s in book["receivables"]), Decimal(0))
    return {"events": out, "views": views, "states": states, "cash": _norm(Decimal(book["cash"]) + unsettled),
            "unsettled": _norm(unsettled),
            "positions": {s: _norm(p["quantity"]) for s, p in sorted(book["positions"].items())}}


def port_run(c):
    from desk.contract import SleeveConfig, View
    from desk.feedlib.r19_book import R19Book
    cfg = c["cfg"]
    tensor = cfg["module"] == "backend.r19_tensor"
    views = []

    class Port(R19Book):
        FEED = "snap"
        INT_QUANTITY = tensor

        def __init__(self):
            self.rule = cfg
            self.CONFIG = SleeveConfig(sleeve_id=cfg["id"].lower(), family="r19", universe=tuple(c["syms"]),
                                       capital=float(cfg["initial_capital"]))

        def evaluate(self, snapshot, book):
            return self.stub(snapshot, book)

    sl = Port()
    cash = Decimal(cfg["initial_capital"])
    pos = {}                                            # sym -> [qty Decimal, avg, meta]
    state = {"installed_at": datetime.fromtimestamp(c["cycles"][0]["t"] - 60, tz=UTC).isoformat()}
    out, states = [], []
    for i, cyc in enumerate(c["cycles"]):
        held = {s: (p[2].get("position_meta") or {}).get("contract_id") for s, p in pos.items()}
        held = {s: (state.get("metadata") or {}).get(s, {}).get("contract_id") or v for s, v in held.items()}
        snap = _snap(c, cyc, held)
        intents = LH._intents(c, cyc, snap)
        sl.stub = _stub(cyc, intents, views)
        positions = {"EQ:" + s: {"qty": float(p[0]), "avg": p[1], "opened_at": cyc["t"], "meta": p[2], "mark": p[1]}
                     for s, p in pos.items()}
        equity = cash + sum(p[0] * Decimal(str(p[1])) for p in pos.values())
        view = View(now=cyc["t"], session="", positions=positions, equity=float(equity), cash=float(cash),
                    state=json.loads(json.dumps(state)), extra={"snap": snap, "pending_orders": []})
        res = sl.signal(view)
        state = sl.update_state(view, res) or state
        for it in res:
            if it.kind not in ("enter", "exit"):
                continue
            q, px, bps = Decimal(str(it.qty)), Decimal(str(it.price_hint)), Decimal(str(it.meta["cost_bps"]))
            fee = q * px * bps / 10000
            side = "buy" if it.kind == "enter" else "sell"
            if side == "buy":
                cash -= q * px + fee
                p = pos.setdefault(it.symbol, [Decimal(0), float(px), dict(it.meta)])
                p[0] += q
            else:
                cash += q * px - fee
                pos[it.symbol][0] -= q
                if pos[it.symbol][0] <= 0:
                    pos.pop(it.symbol)
            out.append([i, "fill", it.symbol, side, _norm(q), _norm(px), _norm(fee), it.meta["order_id"]])
        states.append(dict(state.get("evaluator") or {}))
    unsettled = sum((Decimal(u["amount"]) for u in state["ledger"]["unsettled"]), Decimal(0))
    return {"events": out, "views": views, "states": states, "cash": _norm(cash), "unsettled": _norm(unsettled),
            "positions": {s: _norm(p[0]) for s, p in sorted(pos.items())}}


def run():
    from desk.feedlib import r19_source as RS
    RS.install_shims()
    diffs, stats = [], {"cycles": 0, "fills": 0, "source_errors": 0, "by_family": {"timing": 0, "tensor": 0},
                        "integer_quantity_views": 0}
    for seed in range(1, N_CASES + 1):
        c = _case(seed)
        s, p = source_run(c), port_run(c)
        tensor = c["cfg"]["module"] == "backend.r19_tensor"
        stats["cycles"] += len(c["cycles"])
        stats["fills"] += sum(1 for e in s["events"] if e[1] == "fill")
        stats["source_errors"] += sum(1 for e in s["events"] if e[1] == "error")
        stats["by_family"]["tensor" if tensor else "timing"] += 1
        if tensor:                                      # the named divergence: the port hands integers
            stats["integer_quantity_views"] += sum(1 for v in p["views"] if v["positions"])
        keys = ("events", "views", "states", "cash", "unsettled", "positions")
        if any(s[k] != p[k] for k in keys):
            first = next(k for k in keys if s[k] != p[k])
            diffs.append({"seed": seed, "cfg": c["cfg"]["id"], "first": first,
                          "source": json.dumps(s[first])[:600], "port": json.dumps(p[first])[:600]})
    res = {"cases": N_CASES, "identical": N_CASES - len(diffs), "diffs": diffs[:20], "n_diffs": len(diffs),
           "stats": stats, "sleeves": LH.r19_sleeve_ids(),
           "source": {"cycle": "desk/vendor/ausar_r19/r19_cli.py _current_book + bounded_snapshot (blob 2e246ed1)",
                      "ledger": "desk/vendor/ausar_r19/r19_core.py Ledger.process (blob e12a2bf6)"},
           "port": "desk/feedlib/r19_book.py R19Book.signal + desk/feedlib/r19_ledger.py",
           "named_divergences": {"integer_quantity_views_tensor": stats["integer_quantity_views"]}}
    write_receipt("r19_book", res)
    return dict(res, sleeve="r19_book")
