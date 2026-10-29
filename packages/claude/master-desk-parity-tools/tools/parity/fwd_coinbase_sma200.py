"""fwd_coinbase_sma200 (the Aurelia source desk's Coinbase daily sleeve FWD_COINBASE_SMA200_V1): the SOURCE desk's own
code (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e, run in its own tree: AURELIA_SRC) vs the port, over
three-pass sequences sharing one decision state (the day's first pass, a later pass that day, the next day's).

  source  forward_cycle.run_cycle(now, state, ledger, ..., coinbase_history=_coinbase_history,
          coinbase_quote=_coinbase_quote) — the real pass: its own candle and ticker fetchers (their urlopen
          serving the case's Coinbase payloads), coinbase_forward -> coinbase_schedule.decide (one decision per
          sleeve, version, product and UTC day) -> experiment_executor.submit. Stubbed: urlopen and the clock (a
          FakeDT whose now() is the decision clock while the candles arrive and the ticker's receipt time when the
          ticker arrives — the source stamps the quote with now() at receipt); the Alpaca fetch (raises: those
          books are not under test); the kill switch is passed off.
  port    fwd_coinbase_sma200.decide() on the same candles (the hub's completed daily bars, its n) and ticker
          (femto _quote_row: received_at = the receipt time), carrying its own decisions between passes.
Compared exactly per pass: the decision record (id, sleeve, version, product, day, status, reason, close,
duplicate) and the buy (quantity, price). Counted divergences (verified against the port's own decision):
  receipt_after_clock  the ticker was received after the decision clock was read (the source's own order of
                       operations in every live pass): the source refuses its quote as "stale or future"; the port
                       ages a quote from its receipt to the decision that reads it (0 s) and decides on it.
  carried              a later pass of that day: both duplicates, the recorded first decision differing only
                       because of a receipt_after_clock divergence that day.
Case corpus: tools/parity/stubs/aurelia_crypto_cases.py coinbase_case (deterministic by seed)."""
import os
from datetime import datetime

from desk.sleeves.families.femto import _quote_row
from desk.util import parse_ts

from . import femto_module, old_run, write_receipt

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("aurelia_crypto_cases",
                                     os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs",
                                                  "aurelia_crypto_cases.py"))
G = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(G)

N_CASES = 1200
SEED0 = 202610162
F = femto_module("fwd_coinbase_sma200")
KEYS = ("id", "sleeve", "version", "product", "day", "status", "reason", "close", "duplicate")

SRC = r'''
import io, json, pathlib, shutil, tempfile
import urllib.error, urllib.request
from datetime import datetime, timezone
import aurelia_crypto_cases as G
import desk.forward_cycle as FC
CLOCK = {}
class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return CLOCK["now"]
FC.datetime = FakeDT
STEP = {}
class Resp(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def urlopen(url, timeout=None):
    st = STEP["st"]
    if url.endswith("/ticker"):
        if st["quote"] is None:
            raise urllib.error.HTTPError(url, 503, "unavailable", {}, None)
        CLOCK["now"] = datetime.fromisoformat(st["received_at"])
        q = st["quote"]
        return Resp(json.dumps({"bid": repr(q["bid"]), "ask": repr(q["ask"]), "price": repr(q["ask"]),
                                "time": st["received_at"]}).encode())
    CLOCK["now"] = datetime.fromisoformat(st["moment"])
    rows = [[h["t"], h["c"], h["c"], h["c"], h["c"], 1.0] for h in st["history"]]
    return Resp(json.dumps(rows[::-1]).encode())
urllib.request.urlopen = urlopen
REC = []
_cf = FC.coinbase_forward
def coinbase_forward(*a, **k):
    d = _cf(*a, **k)
    REC.append(json.loads(json.dumps(d, default=str)))
    return d
FC.coinbase_forward = coinbase_forward
def no_bars(*a):
    raise OSError("not under test")
out = []
for seed in PAYLOAD["seeds"]:
    case = G.coinbase_case(seed)
    tmp = pathlib.Path(tempfile.mkdtemp())
    ledger = tmp / "experiment_ledger.jsonl"
    state = {"coinbase": {"decisions": {}, "missed": []}, "attempts": {}, "entries": {}, "bars": {}}
    steps = []
    for st in case["steps"]:
        STEP["st"] = st
        moment = datetime.fromisoformat(st["moment"])
        CLOCK["now"] = moment
        del REC[:]
        try:
            FC.run_cycle(moment, state, ledger=ledger, fetch_bars=no_bars, fetch_quote=no_bars, send=no_bars,
                         coinbase_history=FC._coinbase_history, coinbase_quote=FC._coinbase_quote, kill=False)
            d = REC[-1]
            fill = d.get("order")
            steps.append({"decision": d, "order": [fill["quantity"], fill["price"]] if fill else None})
        except Exception as exc:
            steps.append({"decision": None, "order": None, "raised": type(exc).__name__})
    out.append(steps)
    shutil.rmtree(tmp)
print(json.dumps(out))
'''


def port_steps(case):
    decisions = {}
    out = []
    for st in case["steps"]:
        moment = datetime.fromisoformat(st["moment"])
        bars = [{"t": float(h["t"]), "o": h["c"], "h": h["c"], "l": h["c"], "c": h["c"], "v": 1.0} for h in st["history"]]
        bars = [b for b in bars if b["t"] + 86400 <= moment.timestamp()][-300:]     # the hub's completed, its n
        q = st["quote"]
        row = _quote_row({"bid": q["bid"], "ask": q["ask"], "last": q["ask"], "t": parse_ts(st["received_at"]),
                          "_at": parse_ts(st["received_at"])}) if q is not None else None
        d, order, decisions = F.pass_decision(moment, bars, row, decisions)
        out.append({"decision": d, "order": [order["qty"], order["price"]] if order else None})
    return out


def _rec(d):
    return None if d is None else {k: d.get(k) for k in KEYS}


def run():
    seeds = [SEED0 + i for i in range(N_CASES)]
    tree = os.environ.get("AURELIA_SRC")
    src = old_run(SRC, {"seeds": seeds}, timeout=3600, tree=tree)
    stats = {"passes": 0, "identical": 0, "named": {}, "unexplained": 0, "statuses": {}, "orders": 0, "raised": 0}
    diffs = []
    for seed, sseq in zip(seeds, src):
        case = G.coinbase_case(seed)
        pseq = port_steps(case)
        receipt_days = set()
        for st, s, p in zip(case["steps"], sseq, pseq):
            stats["passes"] += 1
            sd, pd = _rec(s["decision"]), _rec(p["decision"])
            key = "raised" if s.get("raised") else ("duplicate" if (sd or {}).get("duplicate") else (sd or {}).get("status"))
            stats["statuses"][str(key)] = stats["statuses"].get(str(key), 0) + 1
            stats["orders"] += bool(s["order"])
            stats["raised"] += bool(s.get("raised"))
            if sd == pd and s["order"] == p["order"]:
                stats["identical"] += 1
                continue
            moment = datetime.fromisoformat(st["moment"])
            got = None
            if (sd and pd and not sd["duplicate"] and not pd["duplicate"] and sd["status"] == "blocked"
                    and sd["reason"] == "Native quote is stale or future." and s["order"] is None
                    and datetime.fromisoformat(st["received_at"]) > moment
                    and {k: sd[k] for k in ("id", "sleeve", "version", "product", "day")}
                    == {k: pd[k] for k in ("id", "sleeve", "version", "product", "day")}
                    and pd["reason"] != "Native quote is stale or future."):
                got = "receipt_after_clock"
                receipt_days.add(sd["day"])
            elif (sd and pd and sd["duplicate"] and pd["duplicate"] and sd["day"] in receipt_days
                  and s["order"] is None and p["order"] is None
                  and {k: sd[k] for k in ("id", "sleeve", "version", "product", "day")}
                  == {k: pd[k] for k in ("id", "sleeve", "version", "product", "day")}):
                got = "carried"
            if got:
                stats["named"][got] = stats["named"].get(got, 0) + 1
                continue
            stats["unexplained"] += 1
            if len(diffs) < 10:
                diffs.append({"seed": seed, "step": {k: v for k, v in st.items() if k != "history"},
                              "source": s, "port": {"decision": pd, "order": p["order"]}})
    named = sum(stats["named"].values())
    res = {"sleeve": "fwd_coinbase_sma200", "family": None, "sleeves": ["femto_fwd_coinbase_sma200"],
           "cases": stats["passes"], "identical": stats["identical"], "named_divergences": named,
           "named_by_kind": stats["named"], "diffs": diffs, "n_diffs": stats["unexplained"], "stats": stats,
           "case_corpus": N_CASES,
           "method": "source forward_cycle.run_cycle with its own Coinbase fetchers (urlopen + clock stubbed) vs "
                     "fwd_coinbase_sma200.decide over three-pass sequences"}
    write_receipt("fwd_coinbase_sma200", res)
    return res
