"""tensor_swing: the old flagship scanner's decision law (scan_and_trade.decide, bearish_exit_trigger,
_time_stop_due, _pass2_fill_slots) vs the restored sleeve's, on REAL canonical Yahoo 1H series — the six
canonical fixtures the old desk's parity study carried (AEHR ARM CORZ CVNA HUT TEM, 2025-10-14..2026-10-13,
tests/fixtures/canonical_tensor_20261013) — each engine evaluated by its own side: the OLD process runs its own
engine/tensor_exact.py over its own engine tree, the port runs the vendored engine (desk/feedlib/tensor.py).

Per case: a symbol, a pass time (the series cut at a random bar, the pass ~2 minutes after that bar closed, or
later — fresh and stale swings), an equity, a book (0-10 held names, working entries, a signal bar already acted
on), the same calibration on both sides (desk/calibration.json as pinned 2026-10-13); the old desk gates
(earnings blackout, circuit breaker, market-green, buy delay, red-day) stubbed to pass — the cutover doctrine
removed them. The old bars argument is the canonical series too (the port's correlation reads it; the old read
the Alpaca series it still fetched — a named data divergence, not a law difference). Compared: the decision,
rank score, reason, order geometry (qty, limit, take-profit, stop-loss), the bearish-exit verdict and the
time-stop verdict for a position entered N bars back; pass 2 on ranked candidate sets (slots, held / working,
3 per sector)."""
import json
import os
import random
from datetime import datetime, timezone

from desk.feedlib import tensor as T

from . import femto_module, old_run, write_receipt

F = femto_module("tensor_swing")
FIX = os.path.join(os.path.dirname(T.VENDOR), "tensor_fixtures")
SYMS = ("AEHR", "ARM", "CORZ", "CVNA", "HUT", "TEM")
N_CASES = 420
N_PASS2 = 300

OLD = r'''
import sys, types
from datetime import datetime, timezone
sys.argv = ["x"]
import scan_and_trade as O
import desk
CAL = PAYLOAD["cal"]
O._get_calibration = lambda: CAL
O._get_trend = lambda: "UNKNOWN"
O._scan_context = lambda s: ("UNKNOWN", False, "UNKNOWN")
O.append_ledger = lambda e: None
O.save_state = lambda s: None
class _E:
    @staticmethod
    def is_blackout(s): return False
    @staticmethod
    def has_entry(s): return True
    @staticmethod
    def load_earnings(): return {}
O.desk_earnings = _E
cb = types.ModuleType("desk.circuit_breaker"); cb.check_circuit_breaker = lambda: ("ok", "")
rd = types.ModuleType("desk.red_day_gate"); rd.market_green_day = lambda now=None: (False, ""); rd.check = lambda s, now=None: (True, "")
d75 = types.ModuleType("desk.decision75"); d75.buy_delay_ok = lambda sl, s, now=None: (True, "")
for m in (cb, rd, d75):
    sys.modules[m.__name__] = m
    setattr(desk, m.__name__.split(".")[1], m)
O.CHART_GATE_ENABLED = False

def iso(t):
    return datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def shape(bars):
    return [{"t": iso(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]} for b in bars]

SER = {s: json.load(open(p)) for s, p in PAYLOAD["fixtures"].items()}
out = {"cases": [], "pass2": []}
for c in PAYLOAD["cases"]:
    bars = shape(SER[c["sym"]][:c["cut"]])
    res = O.tensor_exact.exact_swing_signal(c["sym"], O.bars_to_exact(bars), swing_lookback=O.EXACT_SWING_LOOKBACK)
    sigs = O.detect_signals(c["sym"], bars)
    held_bars = {h: shape(SER[h][:c["held_cut"][h]]) for h in c["held_bars"]}
    state = {"acted": {k: iso(v) for k, v in c["acted"].items()}, "open_trades": {}}
    positions = {s: {"symbol": s, "qty": "10"} for s in c["held"]}
    now = datetime.fromtimestamp(c["now"], tz=timezone.utc)
    d = O.decide(c["sym"], bars, c["equity"], positions, state, confirm={}, signals=sigs, held_bars=held_bars,
                 now_utc=now, working_entries=set(c["working"]), dry_run=False, canonical_bars=bars)
    trig = O.bearish_exit_trigger(res)
    ts = O._time_stop_due({"entry_bar_t": iso(c["entry_t"]) if c["entry_t"] else None}, bars)
    sig = d.get("signal") or {}
    o = d.get("order") or {}
    out["cases"].append({"decision": d["decision"], "rank": d["rank_score"], "reason": d["reason"],
                         "sig_t": sig.get("t"), "order": {k: o.get(k) for k in ("qty", "limit_price", "take_profit",
                                                                                 "stop_loss")} if o else None,
                         "acted_bar_t": d.get("acted_bar_t"), "exit": list(trig), "ts": list(ts)})
for c in PAYLOAD["pass2"]:
    state = {"open_trades": {}, "acted": {}}
    positions = {s: {"symbol": s, "qty": "1"} for s in c["held"]}
    sent = []
    O._fill_trade_candidate = lambda p, state, positions, dry_run, ts_utc, equity=None: (sent.append(p["symbol"]), positions.setdefault(p["symbol"], {"_pending": True}), True)[-1]
    cands = [{"symbol": s, "decision": "TRADE", "reason": "", "rank_score": r, "confirm": {}, "order": {"qty": 1},
              "acted_bar_t": "x", "signal": {}} for s, r in c["cands"]]
    cands = sorted(cands, key=lambda p: (-p["rank_score"], p["symbol"]))
    slots = O.MAX_POSITIONS - len(positions) - len(set(c["working"]) - set(positions))
    O._pass2_fill_slots(cands, slots, state, positions, False, "2026-10-13T15:00:00Z", working_entries=set(c["working"]))
    out["pass2"].append({"sent": sent, "decisions": {p["symbol"]: p["decision"] for p in cands}})
print(json.dumps(out))
'''


def _cal():
    return {k: v for k, v in F.CALIBRATION.items()}


def run():
    rnd = random.Random(29)
    ser = {s: json.load(open(os.path.join(FIX, s + "_canonical.json"))) for s in SYMS}
    # every confirmed swing in the six real series: the engine at each 5th cut covers the last 5 bars
    from concurrent.futures import ThreadPoolExecutor
    grid = [(s, cut) for s in SYMS for cut in range(300, len(ser[s]) + 1, 5)]
    with ThreadPoolExecutor(max_workers=8) as ex:
        scans = list(ex.map(lambda sc: T.run(sc[0], ser[sc[0]][:sc[1]], swing_lookback=T.SWING_LOOKBACK), grid))
    swing_cuts = []
    for (s, cut), res in zip(grid, scans):
        idx = {b["t"]: i for i, b in enumerate(ser[s][:cut])}
        for ev in res.get("swings") or []:
            if (ev.get("swing") or {}).get("confirmed"):
                swing_cuts.append((s, idx[ev["timestamp"]] + 1, int((ev["swing"].get("score") or 0))))
    swing_cuts = sorted(set(swing_cuts))
    hi = [x for x in swing_cuts if x[2] >= 8]
    cases = []
    for k in range(N_CASES):
        if k % 3 == 0:                                     # anywhere
            sym = rnd.choice(SYMS)
            cut = rnd.randint(500, len(ser[sym]))
        else:                                              # on / just after a real confirmed swing (TRADE-grade 2:1)
            sym, cut, _sc = rnd.choice(hi if (hi and k % 3 == 1) else swing_cuts)
            cut = min(len(ser[sym]), cut + rnd.choice((0, 0, 0, 1, 2, 4)))
        last_t = ser[sym][cut - 1]["t"]
        now = last_t + 3600 + rnd.choice((120, 120, 120, 1800, 3 * 3600, 20 * 3600))
        others = [s for s in SYMS if s != sym]
        held = rnd.sample(others, rnd.randint(0, len(others))) + (["X%02d" % j for j in range(rnd.choice((0, 0, 0, 4, 9)))])
        if rnd.random() < 0.1:
            held.append(sym)
        working = rnd.sample(others, rnd.randint(0, 2)) if rnd.random() < 0.3 else []
        held_bars = [h for h in held if h in ser]
        held_cut = {h: min(len(ser[h]), max(100, sum(1 for b in ser[h] if b["t"] <= last_t))) for h in held_bars}
        acted = {}
        entry_t = ser[sym][cut - 1 - rnd.randint(0, 40)]["t"] if rnd.random() < 0.8 else (ser[sym][0]["t"] - 3600)
        cases.append({"sym": sym, "cut": cut, "now": now, "equity": round(rnd.uniform(4e4, 2e5), 2), "held": held,
                      "working": working, "held_bars": held_bars, "held_cut": held_cut, "acted": acted,
                      "entry_t": entry_t})
    # acted: the newest confirmed swing of some cases (the duplicate path) — found by the port's own engine run
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        runs = list(ex.map(lambda c: T.run(c["sym"], ser[c["sym"]][:c["cut"]], swing_lookback=T.SWING_LOOKBACK), cases))
    new_res = {}
    for k, c in enumerate(cases):
        res = runs[k]
        new_res[k] = res
        sigs = F.signals_of(ser[c["sym"]][:c["cut"]], res)
        if sigs and rnd.random() < 0.15:
            c["acted"] = {c["sym"]: sigs[-1]["t"]}
    pass2 = []
    sectors = ("AEHR", "LITE", "AAOI", "AXTI", "LASR", "OUST", "ALAB", "NBIS", "WDC", "IREN", "SNDK", "ANF", "CVNA",
               "FCEL", "OKLO", "TE", "AG", "CRML", "USAR", "ZZZ1", "ZZZ2", "ZZZ3", "ZZZ4")
    for k in range(N_PASS2):
        held = rnd.sample(sectors, rnd.randint(0, 9))
        working = rnd.sample([s for s in sectors if s not in held], rnd.randint(0, 2))
        cands = [(s, rnd.choice((8, 9, 10, 11, -990))) for s in rnd.sample(sectors, rnd.randint(1, 8))]
        pass2.append({"held": held, "working": working, "cands": cands})
    old = old_run(OLD, {"cal": _cal(), "fixtures": {s: os.path.join(FIX, s + "_canonical.json") for s in SYMS},
                        "cases": cases, "pass2": pass2}, timeout=5400)
    n = same = 0
    diffs = []
    counts = {}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": str(a)[:500], "new": str(b)[:500]})

    def iso(t):
        return datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None

    for k, (c, o) in enumerate(zip(cases, old["cases"])):
        bars = ser[c["sym"]][:c["cut"]]
        res = new_res[k]
        held_bars = {h: ser[h][:c["held_cut"][h]] for h in c["held_bars"]}
        d = F.decide(c["sym"], bars, c["equity"], set(c["held"]), set(c["working"]), c["acted"],
                     F.signals_of(bars, res), confirm={}, held_bars=held_bars, now=c["now"])
        sig = d.get("signal") or {}
        od = d.get("order") or {}
        new = {"decision": d["decision"], "rank": d["rank_score"], "reason": d["reason"],
               "sig_t": iso(sig.get("t")) if sig else None,
               "order": {kk: od.get(kk) for kk in ("qty", "limit_price", "take_profit", "stop_loss")} if od else None,
               "acted_bar_t": iso(d.get("acted_bar_t"))}
        old_dec = {kk: o[kk] for kk in ("decision", "rank", "reason", "sig_t", "order", "acted_bar_t")}
        # the reason quotes the signal bar time: the old ISO string, the port's epoch
        if o["sig_t"] and sig:
            old_dec["reason"] = old_dec["reason"].replace(o["sig_t"], str(sig.get("t")))
        cmp("decide", [k, c["sym"], c["cut"]], old_dec, new)
        cmp("bearish_exit", [k, c["sym"]], o["exit"], list(F.bearish_exit_trigger(res)))
        due, nb, note = F.time_stop_due(c["entry_t"], bars)
        ots = o["ts"]
        if ots[2]:
            ots = [ots[0], ots[1], ots[2].replace(iso(c["entry_t"]), str(c["entry_t"]))]
        cmp("time_stop", [k, c["sym"]], ots, [due, nb, note])
        counts[o["decision"]] = counts.get(o["decision"], 0) + 1
        counts["exit_" + str(o["exit"][0])] = counts.get("exit_" + str(o["exit"][0]), 0) + 1
        counts["time_stop_" + str(o["ts"][0])] = counts.get("time_stop_" + str(o["ts"][0]), 0) + 1
    for k, (c, o) in enumerate(zip(pass2, old["pass2"])):
        cands = [{"symbol": s, "decision": "TRADE", "rank_score": r, "confirm": {}, "reason": ""} for s, r in c["cands"]]
        filled = F.fill_slots(cands, set(c["held"]), set(c["working"]))
        cmp("pass2", k, o, {"sent": [p["symbol"] for p in filled], "decisions": {p["symbol"]: p["decision"]
                                                                                  for p in cands}})
        for v in o["decisions"].values():
            counts["pass2_" + v] = counts.get("pass2_" + v, 0) + 1
    counts["real_confirmed_swings"] = len(swing_cuts)
    counts["real_trade_grade_swings"] = len(hi)
    res = {"sleeve": "tensor_swing", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("tensor_swing", res)
    return res
