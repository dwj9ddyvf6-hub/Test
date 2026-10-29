"""fwd_alpaca_* (the Aurelia source desk's Alpaca USD forwards: ADA RSI(2), LINK AI-volume, ENJ IU-body): the SOURCE
desk's own code (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e, run in its own tree: AURELIA_SRC) vs the
ports, case by case.

  source  forward_cycle.run_cycle(now, state, ledger=<seeded>, fetch_bars, fetch_quote, send, ...) — the real pass:
          each book's completed_bars, alpaca_forward.decide() (first without a quote, then with it when needed) on
          the recipe's source_features (strategies/public_recipes/public_source_sleeves.py loaded by
          sleeve_history._recipes() from the source tree's Ausar archive), _place's one-send-per-client-id, the
          ledger's holding and the state's entry bar close. Stubbed: its Alpaca I/O only — fetch_bars returns the
          case's bars from the requested start date, fetch_quote the case's quote (or raises: unreachable), send
          records the order and fills it — and sleeve_history.SOURCE (the archive's path in the source tree). The
          kill switch is passed off.
  port    each sleeve's decide() on the same inputs in the desk's shapes: the hub's completed bars (the sleeve's n),
          the hub's crypto quote (femto _quote_row), the holding / entry bar close of its position, meta.sent.
Compared exactly per book: the decision (the last decide() of the pass: every key) and the order sent (client id,
side, quantity, limit, bar close). Counted divergences (verified, not hidden):
  quote_unreachable  the quote call failed: the source's row carries the exception text (no second decide()), the
                     port decides once more on no quote — BLOCKED "missing inside the decision window"; no order on
                     either side.
  sale_uncapped      the source's cap check refused to sell a holding worth more than $10,000.01; the port sells the
                     whole holding at the bid (every other key of the decision identical).
  venue_substitution the ENJ book: the source blocks it at its Alpaca listing (HTTP 404); the port trades Kraken
                     ENJUSD on the sim venue (its stop is proven against the recipe in tests/test_femto_fwd_enj.py).
Case corpus: tools/parity/stubs/aurelia_crypto_cases.py alpaca_case (deterministic by seed)."""
import os
from datetime import datetime
from decimal import Decimal

from desk.sleeves.families.femto import _quote_row
from desk.util import parse_ts

from . import femto_module, old_run, write_receipt

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("aurelia_crypto_cases",
                                     os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs",
                                                  "aurelia_crypto_cases.py"))
G = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(G)

N_CASES = 1500
SEED0 = 202610161
NAMES = ("fwd_alpaca_ada_rsi2", "fwd_alpaca_link_ai_volume", "fwd_alpaca_enj_iu_body")
M = {n: femto_module(n) for n in NAMES}
BY_SYMBOL = {M[n].SYMBOL: M[n] for n in NAMES}
HUB_N = {"ADA/USD": 1000, "LINK/USD": 260}

SRC = r'''
import json, pathlib, shutil, tempfile
from datetime import datetime
import aurelia_crypto_cases as G
import desk.sleeve_history as SH
SH.SOURCE = pathlib.Path(PAYLOAD["tree"]) / "ausar-archive" / "ausar-receiver" / "original-payload" / "desk-source"
import desk.forward_cycle as FC
REC = []
_decide = FC.decide
def decide(spec, now, bars, quote, held, entry):
    d = _decide(spec, now, bars, quote, held, entry)
    REC.append([spec["id"], json.loads(json.dumps(d, default=str))])
    return d
FC.decide = decide
out = []
for seed in PAYLOAD["seeds"]:
    case = G.alpaca_case(seed)
    now = datetime.fromisoformat(case["now"])
    tmp = pathlib.Path(tempfile.mkdtemp())
    ledger = tmp / "experiment_ledger.jsonl"
    rows, entries, attempts = [], {}, {}
    for sym, b in case["books"].items():
        if b["held"] > 0:
            rows.append({"status": "filled", "paper_only": True, "writer": "alpaca_crypto_limit",
                         "sleeve": G.FWD_IDS[sym], "symbol": sym, "side": "buy", "quantity": b["held"], "price": 1.0,
                         "client_order_id": "seed-" + sym, "filled_at": case["now"]})
            if b["entry"]:
                entries[sym] = b["entry"]
        for cid in b["sent"]:
            attempts[cid] = {"done": True, "broker_status": "canceled", "filled_qty": 0.0, "reason": "canceled",
                             "ack": {"status": "canceled", "filled_qty": "0", "id": "seed"}}
    if rows:
        ledger.write_text("".join(json.dumps(r) + "\n" for r in rows))
    state = {"coinbase": {"decisions": {}, "missed": []}, "attempts": attempts, "entries": entries, "bars": {}}
    sent = []
    def fetch_bars(symbol, timeframe, start, case=case):
        return [r for r in case["books"][symbol]["raw"] if r["t"] >= start], "sha256"
    def fetch_quote(symbol, case=case):
        q = case["books"][symbol]["quote"]
        if q is None:
            raise RuntimeError("Alpaca crypto quote has no %s book" % symbol)
        return {"bid": q["bid"], "ask": q["ask"], "exchange_at": q["exchange_at"]}
    def send(order, sent=sent):
        sent.append({k: order[k] for k in ("symbol", "client_order_id", "side", "quantity", "limit_price", "bar_close_at")})
        return {"status": "filled", "filled_qty": order["quantity"], "filled_avg_price": order["limit_price"], "id": "p"}
    del REC[:]
    res = FC.run_cycle(now, state, ledger=ledger, fetch_bars=fetch_bars, fetch_quote=fetch_quote, send=send,
                       coinbase_history=lambda: [], coinbase_quote=lambda: None, kill=False)
    last = {}
    for ident, d in REC:
        last[ident] = d
    rows = {r["id"]: {"status": r["status"], "reason": r["reason"]} for r in res["sleeves"]}
    out.append({"decisions": last, "rows": rows, "sent": sent})
    shutil.rmtree(tmp)
print(json.dumps(out))
'''


def port_case(case):
    now = datetime.fromisoformat(case["now"])
    ts = now.timestamp()
    out = {}
    for sym, b in case["books"].items():
        mod = BY_SYMBOL[sym]
        step = mod.SPEC["step_seconds"]
        hub = [{"t": parse_ts(r["t"]), "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in b["raw"]]
        hub = [x for x in hub if x["t"] + step <= ts][-HUB_N[sym]:]          # the hub's completed bars, its n
        q = b["quote"]
        row = _quote_row({"bid": q["bid"], "ask": q["ask"], "last": None, "t": parse_ts(q["exchange_at"]), "_at": ts}) \
            if q is not None else None
        held = Decimal(str(b["held"])) if b["held"] > 0 else Decimal(0)
        d = mod.decide(now, mod.raw_bars(hub, now), mod.quote_of(row), held, b["entry"] if b["held"] > 0 else None)
        order = d.get("order")
        send = order if order and order["client_order_id"] not in set(b["sent"]) else None
        out[mod.SPEC["id"]] = {"decision": d, "sent": [{k: send[k] for k in ("symbol", "client_order_id", "side",
                                                                             "quantity", "limit_price", "bar_close_at")}]
                               if send else []}
    enj = M["fwd_alpaca_enj_iu_body"]          # trades Kraken ENJUSD: no Alpaca decision to compare (venue_substitution)
    out[enj.SPEC["id"]] = {"decision": None, "sent": []}
    return out


ENJ_ID = M["fwd_alpaca_enj_iu_body"].SPEC["id"]
CAP = "Order size is outside the sleeve cap."


def named_kind(ident, case, sd, ss, pd, psent, row):
    """the counted divergence a mismatch is, or None (unexplained)."""
    if ident == ENJ_ID:
        return "venue_substitution" if (sd or {}).get("status") == "BLOCKED" and str(sd.get("reason")).startswith(
            "Alpaca GET /v2/assets/ENJ/USD returned HTTP 404") and not ss else None
    sym = next(s for s, m in BY_SYMBOL.items() if m.SPEC["id"] == ident)
    b = case["books"][sym]
    if (b["quote"] is None and sd and sd.get("needs_quote") and row.get("status") == "BLOCKED"
            and row.get("reason") == "Alpaca crypto quote has no %s book" % sym and not ss and not psent
            and pd.get("status") == "BLOCKED" and pd.get("order") is None
            and pd.get("reason") == "Alpaca quote is missing inside the decision window."):
        return "quote_unreachable"
    if (sd and sd.get("status") == "BLOCKED" and sd.get("reason") == CAP and b["held"] > 0 and not ss
            and pd.get("sale_uncapped") is True and pd.get("status") == "PAPER-ACTIVE"
            and pd["order"]["side"] == "sell" and pd["order"]["quantity"] == float(Decimal(str(b["held"])))
            and pd["order"]["limit_price"] == float(b["quote"]["bid"])
            and {k: v for k, v in sd.items() if k not in ("status", "reason", "order", "orders_disabled")}
            == {k: v for k, v in pd.items() if k not in ("status", "reason", "order", "orders_disabled",
                                                          "sale_uncapped")}):
        return "sale_uncapped"
    return None


def _norm(d):
    import json
    return json.loads(json.dumps(d, default=str))


def run():
    seeds = [SEED0 + i for i in range(N_CASES)]
    tree = os.environ.get("AURELIA_SRC")
    src = old_run(SRC, {"seeds": seeds, "tree": tree}, timeout=3600, tree=tree)
    per = {M[n].SPEC["id"]: {"cases": 0, "identical": 0, "named": {}, "unexplained": 0, "statuses": {}, "orders": {},
                             "reasons": {}} for n in NAMES}
    diffs = []
    for seed, so in zip(seeds, src):
        case = G.alpaca_case(seed)
        pv = port_case(case)
        for ident, p in pv.items():
            st = per[ident]
            st["cases"] += 1
            sd = so["decisions"].get(ident)
            ss = [x for x in so["sent"] if x["client_order_id"].startswith(ident[:40])]
            pd = _norm(p["decision"])
            status = (sd or {}).get("status")
            st["statuses"][str(status)] = st["statuses"].get(str(status), 0) + 1
            if status == "BLOCKED":
                r = str(sd.get("reason"))[:48]
                st["reasons"][r] = st["reasons"].get(r, 0) + 1
            for x in ss:
                st["orders"][x["side"]] = st["orders"].get(x["side"], 0) + 1
            if sd == pd and ss == _norm(p["sent"]):
                st["identical"] += 1
                continue
            row = so["rows"].get(ident) or {}
            kind = named_kind(ident, case, sd, ss, pd or {}, p["sent"], row)
            if kind:
                st["named"][kind] = st["named"].get(kind, 0) + 1
                continue
            st["unexplained"] += 1
            if len(diffs) < 10:
                diffs.append({"seed": seed, "sleeve": ident, "source": {"decision": sd, "sent": ss, "row": row},
                              "port": {"decision": pd, "sent": p["sent"]}})
    total = sum(v["cases"] for v in per.values())
    named = sum(sum(v["named"].values()) for v in per.values())
    unexplained = sum(v["unexplained"] for v in per.values())
    by_kind = {}
    for v in per.values():
        for k, n in v["named"].items():
            by_kind[k] = by_kind.get(k, 0) + n
    res = {"sleeve": "fwd_alpaca", "family": None, "sleeves": ["femto_" + n for n in NAMES],
           "cases": total, "identical": total - named - unexplained, "named_divergences": named,
           "named_by_kind": by_kind, "diffs": diffs, "n_diffs": unexplained, "per_sleeve": per,
           "case_corpus": N_CASES,
           "method": "source forward_cycle.run_cycle in its own tree (Alpaca I/O + the archive path stubbed) vs each "
                     "port's decide() on the same bars / quote / holding"}
    write_receipt("fwd_alpaca", res)
    return res
