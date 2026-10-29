"""R19 execution parity: the SOURCE ledger — the vendored backend/r19_core.py Ledger (its sqlite books, orders,
settlements, quote-depth consumption, Ledger.process -> _housekeeping / _mark / cancel_signal_ids / _execute) — vs
the port's desk.feedlib.r19_ledger model (what the r19_timing and r19_tensor wrappers run), on randomized cycles.
The R19 evaluators themselves are vendored byte-exact and called identically by the port, so the port's own code is
this execution layer: every decision the ledger makes from an intent must match.

Each case: one installed book (a random R19 timing or tensor config), 8-24 cycles over a few XNYS sessions (in and
out of the session, across weekends / holidays and T+1 settlement releases), three symbols with fresh or stale
IEX quotes (age 0-3 s; a held name is always quotable, so the ledger's mark is complete), displayed sizes from
zero up, an occasionally changed contract id, a missing action census, an inactive asset, an indicative feed, a
2-share lot step, wrong fee schedules; a stub evaluator (pure, pre-drawn per cycle) emits absolute targets for a
small pool of stable signal ids (re-emitted, changed, expired) and cancel_signal_ids. The source is run with the
ledger's spread gate neutralised (max_spread_bps 1e9) — the gate the port removes; how often it would have refused
an executed fill is counted. Compared per cycle: every fill (symbol, side, quantity, price, fee, order id) and the
end-of-case cash, unsettled claims and holdings.

    python3 -m tools.parity.run r19_ledger"""
import json
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from tools.parity import write_receipt

UTC = timezone.utc
N_CASES = int(os.environ.get("R19_LEDGER_CASES", "1500"))


def _cfgs():
    from desk.feedlib import r19_source as RS
    m = RS.vendored()
    out = [dict(c, module="backend.r19_timing") for c in m["r19_timing"].register()]
    out += [dict(c, module="backend.r19_tensor") for c in m["r19_tensor"].register()]
    return out


def _sessions(rnd):
    from desk.feedlib.r19_source import DeskXNYS, is_session
    cal = DeskXNYS()
    d = date(2025, 6, 2) + timedelta(days=rnd.randint(0, 420))
    out = []
    while len(out) < 4:
        if is_session(d):
            out.append((d, cal.session_open(d).timestamp(), cal.session_close(d).timestamp()))
        d += timedelta(days=1)
    return out


def case(seed):
    rnd = random.Random(seed)
    cfgs = _cfgs()
    cfg = dict(rnd.choice(cfgs), max_spread_bps=1e9)
    sess = _sessions(rnd)
    syms = ["AAA", "BBB", "QQQ"] if cfg["module"] == "backend.r19_tensor" else ["AAA", "BBB", "CCC"]
    px = {s: rnd.choice((3.2, 4.9, 12.0, 19.5, 47.0, 180.0)) for s in syms}
    t = sess[0][1] + rnd.randint(-900, 3600)
    cycles = []
    pool = {s: [f"sig:{s}:{k}" for k in range(3)] for s in syms}
    for _ in range(rnd.randint(8, 24)):
        t += rnd.choice((30, 60, 300, 900, 3600, 3 * 3600, 20 * 3600))
        for s in syms:
            px[s] = max(1.0, round(px[s] * (1 + rnd.gauss(0, 0.01)), 2))
        draws = {s: {"age": rnd.choice((0.0, 0.4, 1.0, 1.9, 2.5, 3.0)), "spread": rnd.choice((0.01, 0.02, 0.05, 0.4)),
                     "bs": rnd.choice((0, 50, 200, 1000, 20000)), "as": rnd.choice((0, 50, 200, 1000, 20000)),
                     "contract": "c:" + s + (":2" if rnd.random() < 0.03 else ""),
                     "actions_verified": rnd.random() > 0.05, "status": "active" if rnd.random() > 0.04 else "inactive",
                     "feed": "iex" if rnd.random() > 0.03 else "indicative", "step": 1 if rnd.random() > 0.03 else 2,
                     "px": px[s]} for s in syms}
        intents = []
        for s in syms:
            if rnd.random() < 0.55:
                target = rnd.choice((0, 0, 10, 37, 100, 250, 1000, 5000))
                fee = None
                if rnd.random() < 0.03:
                    fee = 99
                intents.append({"symbol": s, "target_quantity": target, "signal_id": rnd.choice(pool[s]),
                                "expires_at": datetime.fromtimestamp(t + rnd.choice((-30, 120, 300, 3600, 86400)),
                                                                     tz=UTC).isoformat(),
                                "reason": "stub", "fee": fee})
        rnd.shuffle(intents)
        cancels = [rnd.choice(pool[s]) for s in syms if rnd.random() < 0.08]
        cycles.append({"t": t, "q": draws, "intents": intents, "cancels": cancels})
    return {"seed": seed, "cfg": cfg, "syms": syms, "cycles": cycles}


def _snapshot(c, cyc, held):
    from desk.feedlib.r19_source import DeskXNYS, is_session
    cal = DeskXNYS()
    t = cyc["t"]
    d = datetime.fromtimestamp(t, tz=UTC).astimezone(__import__("desk.util", fromlist=["ET"]).ET).date()
    if is_session(d):
        o, cl = cal.session_open(d).timestamp(), cal.session_close(d).timestamp()
        calendar = {"is_open": o <= t < cl, "open": datetime.fromtimestamp(o, tz=UTC).isoformat(),
                    "close": datetime.fromtimestamp(cl, tz=UTC).isoformat(), "session": d.isoformat()}
    else:
        calendar = {"is_open": False}
    quotes = {}
    for s, q in cyc["q"].items():
        h = s in held                   # a held name stays quotable under its own contract: the ledger's mark is
        age = min(q["age"], 1.5) if h else q["age"]                     # complete (the NAV coupling is not ported)
        mid = q["px"]
        quotes[s] = {"symbol": s, "contract_id": held[s] if h else q["contract"], "asset_class": "equity",
                     "currency": "USD",
                     "price_basis": "RAW", "bid": round(mid - q["spread"] / 2, 2), "ask": round(mid + q["spread"] / 2, 2),
                     "bid_size": q["bs"], "ask_size": q["as"],
                     "market_at": datetime.fromtimestamp(t - age, tz=UTC).isoformat(),
                     "received_at": datetime.fromtimestamp(t, tz=UTC).isoformat(), "feed": "iex" if h else q["feed"],
                     "step_size": q["step"], "actions_verified": q["actions_verified"], "tradable": True,
                     "status": q["status"]}
    return {"asof": datetime.fromtimestamp(t, tz=UTC).isoformat(), "calendar": calendar, "quotes": quotes,
            "calendar_sessions": [], "corporate_actions": []}


def _intents(c, cyc, snapshot):
    from desk.feedlib import r19_ledger as L
    out = []
    for it in cyc["intents"]:
        q = snapshot["quotes"][it["symbol"]]
        fee = it["fee"] if it["fee"] is not None else float(L.fee_rule(c["cfg"], it["symbol"], Decimal(str(q["ask"]))))
        out.append({"symbol": it["symbol"], "target_quantity": it["target_quantity"], "signal_id": it["signal_id"],
                    "expires_at": it["expires_at"], "reason": it["reason"], "metadata": {"fee_bps": fee}})
    return out


def source_run(c):
    from tools.parity.batch_tmp import case_tmp
    with case_tmp() as d:                     # the source ledger's sqlite, removed however the case ends
        return _source_run(c, d)


def _source_run(c, d):
    from desk.feedlib import r19_source as RS
    m = RS.vendored()["r19_core"]
    clock = [0.0]
    led = m.Ledger(os.path.join(d, "r19.sqlite"), clock=lambda: datetime.fromtimestamp(clock[0], tz=UTC))
    start = c["cycles"][0]["t"] - 60
    led.install([c["cfg"]], enabled=True, at=datetime.fromtimestamp(start, tz=UTC).isoformat())
    bid = c["cfg"]["id"]
    out, seen, held = [], 0, {}
    for i, cyc in enumerate(c["cycles"]):
        snap = _snapshot(c, cyc, held)
        intents = _intents(c, cyc, snap)
        clock[0] = cyc["t"] + 0.001

        def evaluator(snapshot, book):
            return {"intents": [dict(x) for x in intents], "cancel_signal_ids": list(cyc["cancels"]),
                    "state": book.get("state") or {}, "blockers": [], "observations": {}}
        try:
            led.process(bid, snap, evaluator)
        except Exception as e:
            out.append([i, "error", type(e).__name__])
        import sqlite3
        con = sqlite3.connect(os.path.join(d, "r19.sqlite"))
        for seq, kind, payload in con.execute("SELECT seq,kind,payload_json FROM r19_events WHERE book_id=? AND seq>? "
                                              "ORDER BY seq", (bid, seen)).fetchall():
            seen = seq
            if kind == "fill":
                p = json.loads(payload)
                out.append([i, "fill", p["symbol"], p["side"], str(Decimal(p["quantity"]).normalize()),
                            str(Decimal(p["price"]).normalize()), str(Decimal(p["fee"]).normalize()), p["order_id"]])
        held = {r[0]: json.loads(r[1]).get("contract_id") for r in
                con.execute("SELECT symbol,metadata_json FROM r19_positions WHERE book_id=?", (bid,))}
        con.close()
    book = led.books()[0]
    unsettled = sum((Decimal(s["amount"]) for s in book["receivables"]), Decimal(0))
    return {"events": out, "cash": str(Decimal(book["cash"]).normalize()), "unsettled": str(unsettled.normalize()),
            "positions": {s: str(Decimal(p["quantity"]).normalize()) for s, p in sorted(book["positions"].items())}}


def port_run(c):
    from desk.feedlib import r19_ledger as L
    cfg = c["cfg"]
    model, cash, held, out, contracts = L.fresh(), Decimal(cfg["initial_capital"]), {}, [], {}
    gate_would = 0
    for i, cyc in enumerate(c["cycles"]):
        snap = _snapshot(c, cyc, contracts)
        intents = _intents(c, cyc, snap)
        now = cyc["t"]
        cash += L.release(model, now)
        L.cancel(model, set(cyc["cancels"]))
        actual = now + 0.001
        for it in intents:
            owned = Decimal(str(held.get(it["symbol"], 0)))
            marked = sum(Decimal(str(q)) * Decimal(str(snap["quotes"][s]["bid"])) for s, q in held.items() if q)
            nav = cash + L.unsettled(model) + marked
            fill, why = L.execute(model, cfg["id"], cfg, it, snap, owned, cash, nav, marked, actual,
                                  owned_contract=contracts.get(it["symbol"]))
            if fill is None:
                continue
            q = snap["quotes"][fill["symbol"]]
            if (Decimal(str(q["ask"])) - Decimal(str(q["bid"]))) / ((Decimal(str(q["ask"])) + Decimal(str(q["bid"]))) / 2) * 10000 > 30:
                gate_would += 1
            if fill["side"] == "buy":
                cash -= fill["quantity"] * fill["price"] + fill["fee"]
                held[fill["symbol"]] = float(owned + fill["quantity"])
                contracts.setdefault(fill["symbol"], fill["contract_id"])
            else:
                held[fill["symbol"]] = float(owned - fill["quantity"])
                if held[fill["symbol"]] <= 0:
                    held.pop(fill["symbol"])
                    contracts.pop(fill["symbol"], None)
            out.append([i, "fill", fill["symbol"], fill["side"], str(fill["quantity"].normalize()),
                        str(fill["price"].normalize()), str(fill["fee"].normalize()), fill["order_id"]])
    return {"events": out, "cash": str(cash.normalize()), "unsettled": str(L.unsettled(model).normalize()),
            "positions": {s: str(Decimal(str(q)).normalize()) for s, q in sorted(held.items())}, "gate_would": gate_would}


def r19_sleeve_ids():
    """the sleeves whose execution layer this receipt proves: the eight timing and 22 tensor books."""
    from desk.feedlib import r19_source as RS
    m = RS.vendored()
    return sorted(c["id"].lower() for mod in ("r19_timing", "r19_tensor") for c in m[mod].register())


def run():
    from desk.feedlib import r19_source as RS
    RS.install_shims()
    rows, diffs = [], []
    stats = {"fills_buy": 0, "fills_sell": 0, "cycles": 0, "spread_gate_would_refuse": 0, "source_errors": 0,
             "by_family": {}}
    for seed in range(1, N_CASES + 1):
        c = case(seed)
        s, p = source_run(c), port_run(c)
        fam = "tensor" if c["cfg"]["module"] == "backend.r19_tensor" else "timing"
        stats["by_family"][fam] = stats["by_family"].get(fam, 0) + 1
        stats["cycles"] += len(c["cycles"])
        stats["spread_gate_would_refuse"] += p["gate_would"]
        stats["source_errors"] += sum(1 for e in s["events"] if e[1] == "error")
        for e in s["events"]:
            if e[1] == "fill":
                stats["fills_" + e[3]] += 1
        se = [e for e in s["events"] if e[1] == "fill"]
        if se != p["events"] or [s["cash"], s["unsettled"], s["positions"]] != [p["cash"], p["unsettled"], p["positions"]]:
            diffs.append({"seed": seed, "cfg": c["cfg"]["id"], "source": se[:8], "port": p["events"][:8],
                          "source_end": [s["cash"], s["unsettled"], s["positions"]],
                          "port_end": [p["cash"], p["unsettled"], p["positions"]],
                          "errors": [e for e in s["events"] if e[1] == "error"][:3]})
    res = {"cases": N_CASES, "identical": N_CASES - len(diffs), "diffs": diffs[:20], "stats": stats,
           "source": {"ledger": "desk/vendor/ausar_r19/r19_core.py (blob e12a2bf6), settlement_calendar.py (blob 5241b3a7)",
                      "port": "desk/feedlib/r19_ledger.py"},
           "named_divergences": {"spread_gate_removed_fills": stats["spread_gate_would_refuse"]}}
    res["sleeves"] = r19_sleeve_ids()
    write_receipt("r19_ledger", res)
    return dict(res, sleeve="r19_ledger")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "stats")}))
    sys.exit(1 if r["diffs"] else 0)
