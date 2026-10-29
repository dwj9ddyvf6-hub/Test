"""free_kraken_* (the Aurelia source desk's seven Kraken books): the SOURCE desk's own code (Agentic-Trading-Desk
aurelia-paper-desk @1720157f768e, run in its own tree: AURELIA_SRC) vs the ports, case by case.

  source  kraken_paper.run(now, ledger=<seeded>, place=True) — the real pass: kraken_history.collect() (instrument
          identity, perpetual + spot candles, funding, alignment, basis_decision), each breakdown and crowded row,
          the placement loop through experiment_executor.submit, _audit_existing / _cover_due on the seeded ledger,
          and the ENJ row. Stubbed: only its HTTP (_get of kraken_paper / kraken_history serves the case's public
          payloads by URL) and its state paths (a scratch STATE_DIR). The desk-wide pre-trade block (kill switch,
          clock skew) lives outside run() in free_paper and is not called (place=True).
  port    each sleeve's decide() on the same payloads in the desk's shapes: the hub's completed candles (the
          sleeve's n), the hub's ticker row (femto _quote_row), the feeds' funding / instrument / depth values, and
          the position the seeded history leaves (entry_due_at of the open short).
Compared exactly per sleeve: the decision row (every key the source writes), the entry fill (side, quantity, price)
and the cover fill (quantity, price). A difference is either a port bug or one of the named divergences below,
each re-verified against the port's own decision under the source's rule and counted:
  same_day_reentry    BREAKDOWN, a short covered earlier today: the source refuses the new event's entry as a
                      duplicate of its per-day client id; the port enters (one entry per signal event).
  exit_key_collision  BREAKDOWN, the open short's exit-due date equals an earlier cover's: the source's cover id
                      collides and the short is never bought back; the port covers on its 16h clock.
  crowded_cover       CROWDED, the open short's 16h exit is due: the source's _cover_due matches only BREAKDOWN rows;
                      the port covers.
  empty_funding       CROWDED, the breakdown fired and the funding call returned no rows: the source's run() took the
                      breakdown's row (entry_ready); the port's row is crowded()'s WARMING_UP (0 prints).
Case corpus: tools/parity/stubs/aurelia_crypto_cases.py (deterministic by seed; both sides build from it)."""
import os
from datetime import datetime

from desk.sleeves.families.femto import _quote_row
from desk.vendor.aurelia import kraken as K
from desk.vendor.aurelia import kraken_clock as KC

from . import femto_module, old_run, write_receipt

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("aurelia_crypto_cases",
                                     os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs",
                                                  "aurelia_crypto_cases.py"))
G = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(G)

N_CASES = 1500
SEED0 = 202610160
H4 = 4 * 3600
NAMES = ("free_kraken_ada_breakdown", "free_kraken_link_breakdown", "free_kraken_ada_crowded",
         "free_kraken_link_crowded", "free_kraken_ada_basis", "free_kraken_link_basis")
ENJ_WATCH = "FREE_KRAKEN_ENJ_SPOT_V1"    # the source's ENJ watch row: no rule, removed from the desk (2026-10-26)
M = {n: femto_module(n) for n in NAMES}
BOOK_OF = {"breakdown": "BREAKDOWN", "crowded": "CROWDED"}

SRC = r'''
import json, pathlib, shutil, tempfile
from datetime import datetime
import aurelia_crypto_cases as G
import desk.config as CFG
import desk.kraken_history as KH
import desk.kraken_paper as KP
out = []
for seed in PAYLOAD["seeds"]:
    case = G.kraken_case(seed)
    tmp = pathlib.Path(tempfile.mkdtemp())
    CFG.STATE_DIR = tmp
    KH.CACHE, KH.RECEIPT, KP.STATE = tmp / "kraken_history.json", tmp / "basis_receipt.json", tmp / "kraken_paper.json"
    R = G.routes(case)
    def _get(url, R=R):
        return json.loads(json.dumps(R[url]))
    KP._get = _get
    KH._get = _get
    ledger = tmp / "experiment_ledger.jsonl"
    if case["ledger"]:
        ledger.write_text("".join(json.dumps(r) + "\n" for r in case["ledger"]))
    body = KP.run(datetime.fromisoformat(case["now"]), ledger=ledger, place=True)
    rows = [json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    seeded = {r["client_order_id"] for r in case["ledger"]}
    fills = [{k: r[k] for k in ("sleeve", "symbol", "side", "quantity", "price", "client_order_id")}
             for r in rows if r.get("status") == "filled" and r["client_order_id"] not in seeded]
    out.append({"decisions": body["decisions"], "fills": fills})
    shutil.rmtree(tmp)
print(json.dumps(out))
'''


def _hub(chart, now_ts, n):
    """the hub's completed 4h candles (KrakenFutures.bars / cache): t + 4h <= now, the last n."""
    rows = [{"t": c["time"] / 1000.0, "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]),
             "c": float(c["close"]), "v": float(c.get("volume") or 0)} for c in chart]
    return [r for r in rows if r["t"] + H4 <= now_ts][-n:]


def _hub_spot(rows, now_ts, n):
    out = [{"t": float(x[0]), "o": float(x[1]), "h": float(x[2]), "l": float(x[3]), "c": float(x[4]), "v": float(x[6])}
           for x in rows]
    return [r for r in out if r["t"] + H4 <= now_ts][-n:]


def _quote(ticker, now_ts):
    """the hub's kraken_futures quote row for the symbol -> the femto @quote shape."""
    if ticker is None:
        return None
    return _quote_row({"bid": ticker.get("bid"), "ask": ticker.get("ask"), "last": ticker.get("last"), "t": now_ts,
                       "_at": now_ts})


def port_case(case):
    now = datetime.fromisoformat(case["now"])
    ts = now.timestamp()
    out = {}
    for name, b in case["books"].items():
        low = name.lower()
        q = _quote(b["ticker"], ts)
        rows60 = None
        for kind in ("breakdown", "crowded"):
            mod = M["free_kraken_%s_%s" % (low, kind)]
            rows60 = mod.candle_rows(_hub(b["chart"], ts, 60), now)
            held = case["state"][name][BOOK_OF[kind]]
            if kind == "breakdown":
                d = mod.decide(rows60, now, q, held, False)
            else:
                d = mod.decide(rows60, b["rates"], now, q, held, False)
            out[mod.ID] = {"row": d["row"], "entry": ["sell", 1.0, d["enter"]["price"]] if d["enter"] else None,
                           "cover": [d["cover"]["qty"], d["cover"]["price"]] if d["cover"] else None, "_d": d}
        bm = M["free_kraken_%s_basis" % low]
        bd = bm.decide(bm.candle_rows(_hub(b["chart"], ts, 800)), bm.candle_rows(_hub_spot(b["spot"], ts, 720)),
                       b["rates"], case["instruments"], now)
        out[bm.ID] = {"row": bd["row"], "entry": None, "cover": None}
    return out


def source_view(src):
    rows = {r["id"]: r for r in src["decisions"] if r["id"] != ENJ_WATCH}
    out = {}
    for ident, r in rows.items():
        sells = [f for f in src["fills"] if f["sleeve"] == ident and f["side"] == "sell"]
        buys = [f for f in src["fills"] if f["sleeve"] == ident and f["side"] == "buy"]
        out[ident] = {"row": r, "entry": ["sell", sells[0]["quantity"], sells[0]["price"]] if sells else None,
                      "cover": [buys[0]["quantity"], buys[0]["price"]] if buys else None}
    return out


PLACEMENT = ("status", "reason", "fill", "result_series")


def _same_decision(a, b):
    return {k: v for k, v in a.items() if k not in PLACEMENT} == {k: v for k, v in b.items() if k not in PLACEMENT}


def _row_entry(ident, case, s, p, rows):
    """the decision row + entry differ: a named divergence verified against the port's own decision, or None."""
    name, book = ident.split("_")[2], ident.split("_")[3]
    scen = case["scenario"].get(name, {}).get(book)
    b = case["books"][name]
    now = datetime.fromisoformat(case["now"])
    tick = b.get("ticker") or {}
    if book == "BREAKDOWN" and scen == "covered_same_day":
        earlier = [r for r in case["ledger"] if r["sleeve"] == ident and r["side"] == "sell"]
        # the port judges the new event on its merits: the fill at the bid, or submit's own refusal that the
        # source's earlier duplicate-id check pre-empted (its checks run: duplicate id, quote, price, cap)
        entered = p["row"].get("status") == "entry_ready" and p["entry"] == ["sell", 1.0, float(tick["bid"])]
        refused = p["row"].get("status") == "BLOCKED_INPUT" and p["entry"] is None and p["row"].get("reason") in (
            "order exceeds the sleeve exposure cap", "quote is incomplete or crossed")
        if (s["row"].get("status") == "duplicate" and s["row"].get("reason") == "duplicate client_order_id"
                and s["entry"] is None and (entered or refused) and _same_decision(s["row"], p["row"])
                and earlier and earlier[-1]["client_order_id"] == "%s-%s" % (ident, now.date().isoformat())
                and p["row"]["signal_open_at"] > KC.breakdown_decision(
                    rows, KC._parse(earlier[-1]["filled_at"]), instrument=b["perp"])["signal_open_at"]):
            return "same_day_reentry"
    if book == "CROWDED" and b.get("rates") == []:
        bd = KC.breakdown_decision(rows, now, instrument=b["perp"])
        head = {"id": ident, "instrument": b["perp"], "quote_currency": "USD"}
        if (bd["status"] == "entry_ready" and p["row"] == dict(head, **K.crowded(rows, [], now)) and p["entry"] is None
                and {k: v for k, v in s["row"].items() if k not in PLACEMENT}
                == dict(head, **{k: v for k, v in bd.items() if k not in PLACEMENT})):
            return "empty_funding"
    return None


def _cover(ident, case, s, p):
    """the cover differs: a named divergence verified against the port's own 16h clock, or None."""
    name, book = ident.split("_")[2], ident.split("_")[3]
    scen = case["scenario"].get(name, {}).get(book)
    now = datetime.fromisoformat(case["now"])
    tick = case["books"][name].get("ticker") or {}
    held = case["state"][name].get(book)
    if s["cover"] is not None or p["cover"] is None or not held:
        return None
    due = KC.exit_due_at(KC._parse(held["entry_due_at"]))
    if p["cover"] != [1.0, float(tick["ask"])] or now < due:
        return None
    if book == "CROWDED" and scen in ("open_due", "open_not_due"):
        return "crowded_cover"
    covers = [r["client_order_id"] for r in case["ledger"] if r["sleeve"] == ident and r["side"] == "buy"]
    if book == "BREAKDOWN" and scen == "collision" and "%s-exit-%s" % (ident, due.date().isoformat()) in covers:
        return "exit_key_collision"
    return None


def classify(ident, case, s, p, rows):
    """each differing component (the row + entry, the cover) must be a named divergence; returns its labels, or
    None when any component stays unexplained."""
    labels = []
    if (s["row"], s["entry"]) != (p["row"], p["entry"]):
        lab = _row_entry(ident, case, s, p, rows)
        if lab is None:
            return None
        labels.append(lab)
    if s["cover"] != p["cover"]:
        lab = _cover(ident, case, s, p)
        if lab is None:
            return None
        labels.append(lab)
    return labels


def run():
    seeds = [SEED0 + i for i in range(N_CASES)]
    src = old_run(SRC, {"seeds": seeds}, timeout=3600, tree=os.environ.get("AURELIA_SRC"))
    per = {M[n].ID: {"cases": 0, "identical": 0, "named": {}, "unexplained": 0, "statuses": {}, "entries": 0,
                     "covers": 0} for n in NAMES}
    diffs = []
    for seed, so in zip(seeds, src):
        case = G.kraken_case(seed)
        pv = port_case(case)
        sv = source_view(so)
        for ident, p in pv.items():
            s = sv.get(ident) or {"row": None, "entry": None, "cover": None}
            st = per[ident]
            st["cases"] += 1
            st["statuses"][str(s["row"] and s["row"].get("status"))] = st["statuses"].get(
                str(s["row"] and s["row"].get("status")), 0) + 1
            st["entries"] += bool(s["entry"])
            st["covers"] += bool(s["cover"])
            pc = {k: p[k] for k in ("row", "entry", "cover")}
            if pc == s:
                st["identical"] += 1
                continue
            why = None
            if "_d" in p:
                name = ident.split("_")[2]
                now = datetime.fromisoformat(case["now"])
                rows = M["free_kraken_%s_breakdown" % name.lower()].candle_rows(
                    _hub(case["books"][name]["chart"], now.timestamp(), 60), now)
                why = classify(ident, case, s, pc, rows)
            if why:
                st["named_cases"] = st.get("named_cases", 0) + 1
                for lab in why:
                    st["named"][lab] = st["named"].get(lab, 0) + 1
            else:
                st["unexplained"] += 1
                if len(diffs) < 10:
                    diffs.append({"seed": seed, "sleeve": ident, "source": s, "port": pc})
    total = sum(v["cases"] for v in per.values())
    named = sum(v.get("named_cases", 0) for v in per.values())
    unexplained = sum(v["unexplained"] for v in per.values())
    res = {"sleeve": "free_kraken", "family": None,
           "sleeves": ["femto_" + n for n in NAMES],
           "cases": total, "identical": total - named - unexplained, "named_divergences": named,
           "named_by_kind": {k: sum(v["named"].get(k, 0) for v in per.values())
                             for k in ("same_day_reentry", "exit_key_collision", "crowded_cover", "empty_funding")},
           "diffs": diffs, "n_diffs": unexplained, "per_sleeve": per, "case_corpus": N_CASES,
           "method": "source kraken_paper.run(now, ledger, place=True) in its own tree (HTTP + state paths stubbed) "
                     "vs each port's decide() on the same payloads"}
    write_receipt("free_kraken", res)
    return res
