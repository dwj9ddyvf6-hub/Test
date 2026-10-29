"""qqq_put_ladder: the SOURCE desk's own ladder_broker.sync() (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e,
run in its own tree: AURELIA_SRC) vs the port's decide(), over multi-pass sequences of randomized cases.

Every pass both sides get the same book: the source its state file (layers, week_opened) built from the port's
fill-based book; the port the matching positions / working orders, and the cash that leaves exactly the source's
options buying power. Stubbed in the source, I/O only: the Alpaca chain / account / order calls, the Yahoo closes,
the plan (its QQQ price = the case's spot, its brain level = the case's posture), the kill switch (off: gone under
the cutover doctrine), the memory / ledger record. Two source runs per pass:
  adapted  the chain stub also answers the open layers' own contracts outside the requested windows, and the
           account re-read during the sends answers the buying power after the buy-backs already sent (the two
           named divergences) -> compared EXACTLY with the port: the actions, the add block, the candidate, the
           ordered sends (and skipped roll sales), the week stamp;
  strict   the source as it ran (only the requested 38-52 / 0-25 DTE windows; the re-read answers the account
           unchanged) -> every pass where it differs from `adapted` is classified (gap_quote: an open layer 26-37
           DTE out, quoted only in `adapted`; after_close_bp: a roll sale the two re-reads decide differently) and
           counted; a difference with neither cause is a diff.
After each in-window pass the source's own state file (its _apply_fill) is compared with the port's book after
its fills: a skipped roll sale the source wrote down as a new working layer (phantom_layer), and orders the
harness leaves unfilled (unfilled_sale / unfilled_buyback: the source recorded the layer at acceptance), and two
layers that landed in one contract (merged_layer: one position in the port's book), are classified and counted;
anything else is a diff."""
import math
import os
import random
from datetime import date, datetime, timedelta

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

L = femto_module("qqq_put_ladder")
PL = L.PL
N_SEQS, N_STEPS = 170, 8

SRC = r'''
import json, os, pathlib, tempfile
os.environ["DESK_ALLOW_ORDERS"] = "1"
os.environ["APCA_ENV"] = "paper"
import desk.config as CFG
tmp = pathlib.Path(tempfile.mkdtemp())
CFG.STATE_DIR = tmp
import desk.ladder_broker as LB
import desk.ausar_gate as AG
import desk.data.alpaca as A
AG.kill_switch_on = lambda: False
LB._remember = lambda body: body.__setitem__("log", None)
LB.STATE = tmp / "put_ladder.json"
ST = {}
def option_chain(underlying, gte, lte, option_type="put", feed="indicative", limit=1000):
    if ST.get("chain_error"):
        raise RuntimeError("chain unavailable")
    out = {}
    for sym, snap in ST["snaps"]:
        exp = "20%s-%s-%s" % (sym[3:5], sym[5:7], sym[7:9])
        if gte <= exp <= lte:
            out[sym] = snap
    if ST["mode"] == "adapted" and not ST.get("extra_done"):
        ST["extra_done"] = True
        for sym, snap in ST["extra_snaps"]:
            out[sym] = snap
    return out
def account():
    if ST["obp"] is None:
        raise RuntimeError("account unavailable")
    return {"options_buying_power": str(ST["obp_now"]), "regt_buying_power": "0", "buying_power": "0"}
def submit_option_order(symbol, qty, side, limit, intent, client_id):
    ST["sent"].append([symbol, side, int(qty), float(limit), intent])
    if ST["mode"] == "adapted" and ST["obp"] is not None:
        k = int(symbol[-8:]) / 1000.0
        if intent == "buy_to_close":
            ST["obp_now"] += (k - float(limit)) * 100.0 * int(qty)
        else:
            ST["obp_now"] -= max(0.0, k - float(limit)) * 100.0 * int(qty)
    return {"status": "accepted", "id": "o%d" % len(ST["sent"])}
A.option_chain, A.account, A.submit_option_order = option_chain, account, submit_option_order
LB._closes = lambda: list(ST["closes"])
def norm_leg(l):
    if not l:
        return None
    keys = ("symbol", "side", "qty", "limit", "position_intent", "expiration", "strike", "delta", "bid", "ask", "dte",
            "cash_required")
    return {k: l.get(k) for k in keys if k in l}
out = []
for case in PAYLOAD["steps"]:
    res = {}
    for mode in ("adapted", "strict"):
        ST.clear()
        ST.update(case)
        ST.update(mode=mode, sent=[], obp_now=case["obp"])
        LB.STATE.write_text(json.dumps(case["state"]))
        plan = {"orders": [], "mode": "in_band"}
        if case["spot"] is not None:
            plan["prices"] = {"QQQ": case["spot"]}
        if case["posture"] != "unknown":
            plan["brain"] = {"level": case["posture"]}
        body = LB.sync(plan, case["clock"])
        state = json.loads(LB.STATE.read_text())
        res[mode] = {"actions": [{"kind": a["kind"], "layer_id": a.get("layer_id"), "reason": a["reason"],
                                  "close": norm_leg(a.get("close")), "open": norm_leg(a.get("open"))}
                                 for a in body["actions"]],
                     "add_block": body["add_block"], "candidate": (body.get("candidate") or {}).get("symbol"),
                     "submit_block": body["submit_block"],
                     "sent": [[r["symbol"], r["side"], r["qty"], r["limit"], r["position_intent"], r.get("status")]
                              for r in (body.get("sent") or [])],
                     "calls": ST["sent"],
                     "layers": [{k: l.get(k) for k in ("id", "opened", "symbol", "qty", "entry_credit", "entry_spot",
                                                       "entry_delta", "rolled_on", "status")}
                                for l in state.get("layers") or []],
                     "week_opened": state.get("week_opened")}
    out.append(res)
print(json.dumps(out))
'''


def occ(exp, k):
    return "QQQ%s%s%sP%08d" % (exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _put(S, K, dte, vol):
    T = max(dte, 0.5) / 365.0
    d1 = (math.log(S / K) + 0.5 * vol * vol * T) / (vol * math.sqrt(T))
    d2 = d1 - vol * math.sqrt(T)
    return K * _ncdf(-d2) - S * _ncdf(-d1), _ncdf(-d1)


def _expirations(today):
    """Fridays (Thursday when Friday is a holiday) and some Wednesdays, 0-60 days out."""
    out, d = [], today
    while (d - today).days <= 60:
        if d.weekday() in (2, 4):
            e = d if cal.is_trading_day(d) else d - timedelta(days=1)
            if e >= today and (d.weekday() == 4 or d.day % 2 == 0):
                out.append(e)
        d += timedelta(days=1)
    return sorted(set(out))


def _row(rnd, S, exp, k, today, vol):
    dte = (exp - today).days
    px, dl = _put(S, k, dte, vol)
    spread = round(max(0.01, rnd.uniform(0.01, 0.12) * (1 + px * 0.05)), 2)
    bid = round(max(0.0, px - spread / 2), 2)
    ask = round(bid + spread, 2)
    u = rnd.random()
    delta = None if u < 0.03 else -round(min(1.0, dl * rnd.uniform(0.9, 1.1)), 4)
    if 0.03 <= u < 0.05:
        bid = 0.0
    elif 0.05 <= u < 0.07:
        ask = round(max(0.0, bid - 0.05), 2)                    # crossed / locked
    elif 0.07 <= u < 0.10:
        ask = round(bid + rnd.uniform(0.3, 2.0), 2)            # wide
    return {"symbol": occ(exp.isoformat(), k), "expiration": exp.isoformat(), "strike": float(k), "type": "put",
            "bid": bid, "ask": ask, "delta": delta}


def _chain(rnd, S, today, held):
    vol = rnd.uniform(0.14, 0.34)
    step = max(1.0, round(S * rnd.choice((0.005, 0.0075, 0.01)) / 1.0))
    rows = {}
    for exp in _expirations(today):
        k = math.floor(S * 0.80 / step) * step
        while k <= S * 1.01:
            r = _row(rnd, S, exp, k, today, vol)
            rows[r["symbol"]] = r
            k += step
    for sym in held:                                           # the layers' own contracts (sometimes unquoted)
        if sym not in rows and rnd.random() > 0.04:
            exp = date(2000 + int(sym[3:5]), int(sym[5:7]), int(sym[7:9]))
            rows[sym] = _row(rnd, S, exp, int(sym[-8:]) / 1000.0, today, vol)
    return [rows[s] for s in sorted(rows)]


def _snap(r):
    return [r["symbol"], {"greeks": None if r["delta"] is None else {"delta": r["delta"]},
                          "latestQuote": {"bp": r["bid"], "ap": r["ask"]}}]


def _clock(rnd, d):
    op, cl = cal.session_open(d), cal.session_close(d)
    u = rnd.random()
    if u < 0.06:
        t = op - rnd.randint(60, 4000)
    elif u < 0.12:
        t = cl - rnd.randint(0, 899)
    elif u < 0.15:
        t = cl + rnd.randint(60, 4000)
    else:
        t = op + rnd.randint(0, int(cl - op - 901))
    is_open = op <= t < cl
    nc = cl if t < cl else cal.session_close(cal.next_trading_day(d))
    iso = lambda x: datetime.fromtimestamp(x, tz=ET).isoformat()
    return t, {"is_open": is_open, "timestamp": iso(t), "next_close": iso(nc), "next_open": iso(op)}


TAPES = {"normal": {"vix": 15.0, "ndx_day": 0.002}, "cautious": {"vix": 30.0, "ndx_day": -0.01},
         "stand_down": {"vix": 45.0, "ndx_day": -0.02}}


def _layer_rec(l):
    rec = {k: l[k] for k in ("id", "opened", "entry_credit", "entry_spot", "entry_delta") if l.get(k) is not None}
    if l.get("rolled_on"):
        rec["rolled_on"] = l["rolled_on"]
    return rec


def _port_book(layers):
    """the port's book for the state's layers: open -> a held short put; closing -> held + a working buy-back;
    working -> a working sale."""
    legs, pending = {}, []
    for l in layers:
        rec = _layer_rec(l)
        if l["status"] == "working":
            pending.append({"action": "enter", "occ": l["symbol"], "side": "sell", "qty": l["qty"],
                            "limit": l["entry_credit"], "meta": {"layer": rec}})
            continue
        legs[l["symbol"]] = {"qty": -l["qty"], "avg": l["entry_credit"], "opened_at": 0, "meta": {"layer": rec}}
        if l["status"] == "closing":
            pending.append({"action": "exit", "occ": l["symbol"], "side": "buy", "qty": l["qty"]})
    return legs, pending


def _held_cash(legs, pending):
    c = sum(int(s[-8:]) / 1000.0 * 100.0 * -p["qty"] for s, p in legs.items())
    c += sum(max(0.0, int(o["occ"][-8:]) / 1000.0 - float(o["limit"])) * 100.0 * o["qty"]
             for o in pending if o["action"] == "enter")
    return c


def _bars(today, closes):
    days, d = [], today - timedelta(days=1)
    while len(days) < len(closes):
        if cal.is_trading_day(d):
            days.append(d)
        d -= timedelta(days=1)
    return {"QQQ": [{"t": datetime(x.year, x.month, x.day, tzinfo=ET).timestamp(), "o": c, "h": c, "l": c, "c": c,
                     "v": 1.0} for x, c in zip(reversed(days), closes)]}


def _initial_layers(rnd, S, today, week_days):
    out, used = [], set()
    for _ in range(rnd.choice((0, 0, 1, 2, 3, 4))):
        exp = today + timedelta(days=rnd.randint(0, 52))
        while not cal.is_trading_day(exp):
            exp -= timedelta(days=1)
        if exp < today or exp in used:
            continue
        used.add(exp)
        k = round(S * rnd.uniform(0.82, 1.0))
        opened = cal.prev_trading_day(today, rnd.randint(1, 40)).isoformat()
        l = {"id": "%s:%s" % (exp.isoformat(), float(k)), "opened": opened, "expiration": exp.isoformat(),
             "strike": float(k), "symbol": occ(exp.isoformat(), k), "qty": rnd.choice((3, 3, 3, 1, 2, 6)),
             "entry_credit": round(rnd.uniform(0.1, 3.5), 2), "entry_spot": round(S * rnd.uniform(0.9, 1.08), 2),
             "entry_delta": round(rnd.uniform(0.03, 0.12), 4), "status": "open"}
        u = rnd.random()
        if u < 0.06:
            l["status"] = "closing"
        elif u < 0.11:
            l["status"] = "working"
        if rnd.random() < 0.08:
            l["rolled_on"] = today.isoformat()
        out.append(l)
    return out


def _sequences(rnd):
    days = []
    d = date(2025, 1, 6)
    while d <= date(2026, 9, 25):
        if cal.is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    seqs = []
    for _ in range(N_SEQS):
        today = rnd.choice(days)
        S = rnd.uniform(380, 720)
        layers = _initial_layers(rnd, S, today, days)
        wk = rnd.choice((None, PL.iso_week(today), PL.iso_week(today - timedelta(days=7))))
        closes = [S * (1 + rnd.gauss(0, 0.01)) for _ in range(rnd.choice((4, 5, 6, 7, 9)))]
        steps = []
        for k in range(N_STEPS):
            if k:
                u = rnd.random()
                gap = 0 if u < 0.2 else (1 if u < 0.5 else (rnd.randint(2, 4) if u < 0.75 else rnd.randint(5, 10)))
                if gap:
                    closes = (closes + [S])[-9:]
                    today = cal.next_trading_day(today, gap)
                S *= math.exp(rnd.gauss(0.0005 * max(gap, 1), 0.012 * math.sqrt(max(gap, 1))))
                if rnd.random() < 0.08:
                    S *= rnd.uniform(0.92, 1.03)
            steps.append({"today": today, "S": S, "closes": list(closes), "week": wk})
            # placeholders: layers/week evolve from the port's fills when the sequence runs
        seqs.append({"start_layers": layers, "steps": steps, "seed": rnd.random()})
    return seqs


def _step_case(rnd, st, layers, week):
    today = st["today"]
    t, clock = _clock(rnd, today)
    S = st["S"]
    held = [l["symbol"] for l in layers]
    chain = _chain(rnd, S, today, held)
    if rnd.random() < 0.05:                                   # a thin chain: no band put at all
        chain = [r for r in chain if r["symbol"] in held or not 38 <= (date.fromisoformat(r["expiration"]) - today).days <= 52]
    any_open = any(l["status"] in ("working", "open") for l in layers)
    far = {r["symbol"] for r in chain if 38 <= (date.fromisoformat(r["expiration"]) - today).days <= 52}
    near = {r["symbol"] for r in chain if any_open and 0 <= (date.fromisoformat(r["expiration"]) - today).days <= 25}
    extra = [r for r in chain if r["symbol"] in held and r["symbol"] not in far and r["symbol"] not in near]
    u = rnd.random()
    posture = "normal" if u < 0.74 else ("cautious" if u < 0.82 else ("stand_down" if u < 0.91 else "unknown"))
    obp = None if rnd.random() < 0.07 else round(rnd.choice((rnd.uniform(0, 400_000), rnd.uniform(150_000, 900_000))), 2)
    spot = None if rnd.random() < 0.02 else round(S, 2)
    closes = [round(c, 2) for c in st["closes"]] if spot is not None else []
    if spot is not None and rnd.random() < 0.5 and len(closes) > 5:            # a down week half the time
        closes[-6] = round(closes[-1] * rnd.choice((0.97, 1.03)), 2)
    chain_error = rnd.random() < 0.03
    state = {"layers": [dict(l) for l in layers], "week_opened": week}
    return t, {"clock": clock, "spot": spot, "closes": closes, "posture": posture, "obp": obp, "chain_error": chain_error,
               "snaps": [_snap(r) for r in chain if 0 <= (date.fromisoformat(r["expiration"]) - today).days <= 52],
               "extra_snaps": [_snap(r) for r in extra], "state": state}, chain


def _port(t, case, chain, layers, week):
    today = date.fromisoformat(case["clock"]["timestamp"][:10])
    legs, pending = _port_book(layers)
    cash = None if case["obp"] is None else case["obp"] + _held_cash(legs, pending)
    rows = [r for r in chain if 0 <= (date.fromisoformat(r["expiration"]) - today).days <= 52]
    extra = {"legs": legs, "pending": pending, "cash": cash,
             "quotes": {"QQQ": {"bid": case["spot"], "ask": case["spot"]}} if case["spot"] is not None else {},
             "aurelia": dict(TAPES[case["posture"]], as_of="x") if case["posture"] != "unknown" else {"error": "x"},
             "meta": {"week_opened": week} if week else {}}
    if not case["chain_error"]:
        extra["chain"] = {"QQQ": rows}
    ctx = fc.Context(now=float(t), session=today.isoformat(), equity=0.0, extra=extra)
    return L.decide(_bars(today, case["closes"]), ctx)


def _norm_actions(actions):
    keys = ("symbol", "side", "qty", "limit", "position_intent", "expiration", "strike", "delta", "bid", "ask", "dte",
            "cash_required")
    nl = lambda l: None if not l else {k: l.get(k) for k in keys if k in l}
    return [{"kind": a["kind"], "layer_id": a.get("layer_id"), "reason": a["reason"], "close": nl(a.get("close")),
             "open": nl(a.get("open"))} for a in actions]


def _port_sent(out):
    rows = []
    for kind, a, leg in out["log"]:
        if kind == "close":
            rows.append([leg["symbol"], "buy", int(leg["qty"]), float(leg["limit"]), "buy_to_close", "accepted"])
        elif kind == "open":
            rows.append([leg["symbol"], "sell", int(leg["qty"]), float(leg["limit"]), "sell_to_open", "accepted"])
        else:
            rows.append([leg["symbol"], "sell", int(leg["qty"]), float(leg["limit"]), "sell_to_open", "skipped"])
    return rows


def _fills(rnd, out, layers, today, spot):
    """the port's book after its orders: each fills at its limit (4% left unfilled)."""
    by = {l["symbol"]: dict(l) for l in layers}
    unfilled, dead = [], set()
    for kind, a, leg in out["log"]:
        if kind == "skip":
            continue
        if id(a) not in dead and kind == "close" or a["kind"] == "sell_open":
            if rnd.random() < 0.04:                           # this action's orders die unfilled with the day
                dead.add(id(a))
        if id(a) in dead:
            unfilled.append((kind, leg["symbol"]))
            if kind == "close" and leg["symbol"] in by:
                by[leg["symbol"]]["status"] = "open"
            continue
        if kind == "close":
            by.pop(leg["symbol"], None)
            continue
        if a["kind"] == "sell_open":
            rec = {"id": "%s:%s" % (leg["expiration"], leg["strike"]), "opened": today}
        else:
            old = next((l for l in layers if l["id"] == a.get("layer_id")), {})
            rec = {"id": old.get("id") or a.get("layer_id"), "opened": old.get("opened"), "rolled_on": today}
        prev = by.get(leg["symbol"])
        n = {"symbol": leg["symbol"], "expiration": leg["expiration"], "strike": leg["strike"], "status": "open",
             "qty": int(leg["qty"]) + (prev["qty"] if prev else 0), "entry_credit": leg["bid"], "entry_spot": spot,
             "entry_delta": leg["delta"], **rec}
        if prev:                                              # one contract, one position: the first record stays
            n = dict(prev, qty=n["qty"])
        by[leg["symbol"]] = n
    for sym, l in list(by.items()):                           # day orders end with the day: nothing works on
        if l["status"] == "working":
            l["status"] = "open"                              # the working sale filled
        if l["status"] == "closing":                          # the working buy-back filled (4%: it died unfilled)
            if rnd.random() < 0.04:
                l["status"] = "open"
                unfilled.append(("close", sym))
            else:
                by.pop(sym)
    return [l for l in by.values()], unfilled


def _norm_state(layers):
    return sorted((l["symbol"], int(l["qty"]), l.get("id"), l.get("opened"), l.get("entry_credit"),
                   round(float(l.get("entry_spot") or 0), 4), l.get("entry_delta"), l.get("rolled_on"))
                  for l in layers if l.get("status") in ("working", "open"))


def run():
    rnd = random.Random(20261016)
    seqs = _sequences(rnd)
    steps, plans = [], []
    # the sequences evolve from the port's fills, so the cases are built pass by pass: first all the port
    # passes (with their source cases recorded), then one source run over every case
    for seq in seqs:
        srnd = random.Random(seq["seed"])
        layers, week = [dict(l) for l in seq["start_layers"]], seq["steps"][0]["week"]
        for st in seq["steps"]:
            layers = [l for l in layers if l["expiration"] >= st["today"].isoformat()]   # expired: the engine settles
            t, case, chain = _step_case(srnd, st, layers, week)
            out = _port(t, case, chain, layers, week)
            window = case["clock"]["is_open"] and t < cal.session_close(st["today"]) - 900
            rec = {"case": case, "layers_in": [dict(l) for l in layers], "week_in": week, "window": window,
                   "decision": {"actions": _norm_actions(out["decision"]["actions"]),
                                "add_block": out["decision"]["add_block"],
                                "candidate": (out["decision"].get("candidate") or {}).get("symbol")},
                   "sent": _port_sent(out) if window else []}
            if window:
                layers, unfilled = _fills(srnd, out, layers, st["today"].isoformat(), out["spot"])
                week = out["week_stamp"] or week
                rec["unfilled"] = unfilled
            rec["layers_out"], rec["week_out"] = [dict(l) for l in layers], week
            steps.append(case)
            plans.append(rec)
    src = old_run(SRC, {"steps": steps}, timeout=3600, tree=os.environ.get("AURELIA_SRC"))
    diffs, stats = [], {"passes": len(plans), "in_window": 0, "actions": {}, "add_blocks": {}, "sends": 0,
                        "skipped_roll_sales": 0, "named": {"gap_quote": 0, "after_close_bp": 0, "phantom_layer": 0,
                                                           "unfilled_sale": 0, "unfilled_buyback": 0}}
    for rec, res in zip(plans, src):
        a = res["adapted"]
        src_dec = {"actions": a["actions"], "add_block": a["add_block"], "candidate": a["candidate"]}
        if src_dec != rec["decision"]:
            diffs.append({"part": "decision", "case": rec["case"], "source": src_dec, "port": rec["decision"]})
            continue
        src_sent = a["sent"] if rec["window"] else []
        if not rec["window"] and a["calls"]:
            diffs.append({"part": "sent outside the window", "source": a["calls"]})
        if src_sent != rec["sent"]:
            diffs.append({"part": "sends", "case": rec["case"], "source": src_sent, "port": rec["sent"]})
            continue
        for x in rec["decision"]["actions"]:
            k = "%s: %s" % (x["kind"], x["reason"])
            stats["actions"][k] = stats["actions"].get(k, 0) + 1
        b = rec["decision"]["add_block"] or "added"
        stats["add_blocks"][b] = stats["add_blocks"].get(b, 0) + 1
        stats["sends"] += sum(1 for r in rec["sent"] if r[5] == "accepted")
        stats["skipped_roll_sales"] += sum(1 for r in rec["sent"] if r[5] == "skipped")
        # strict (the source as it ran) vs adapted: classified, counted
        s = res["strict"]
        if (s["actions"], s["add_block"], s["candidate"], s["sent"]) != (a["actions"], a["add_block"], a["candidate"], a["sent"]):
            today = date.fromisoformat(rec["case"]["clock"]["timestamp"][:10])
            gap = any(26 <= (date.fromisoformat(l["expiration"]) - today).days <= 37
                      for l in rec["layers_in"] if l["status"] in ("working", "open"))
            rolls = (s["actions"], s["add_block"], s["candidate"]) == (a["actions"], a["add_block"], a["candidate"])
            if gap:
                stats["named"]["gap_quote"] += 1
            elif rolls:
                stats["named"]["after_close_bp"] += 1
            else:
                diffs.append({"part": "strict vs adapted", "case": rec["case"], "strict": s, "adapted": a})
        if not rec["window"]:
            continue
        stats["in_window"] += 1
        # post-pass state: the source's _apply_fill vs the port's book after its fills
        src_state, port_state = _norm_state(a["layers"]), _norm_state(rec["layers_out"])
        if src_state != port_state or a["week_opened"] != rec["week_out"]:
            skipped = {r[0] for r in rec["sent"] if r[5] == "skipped"}
            sale_unfilled = {sym for kind, sym in rec.get("unfilled") or [] if kind == "open"}
            buy_unfilled = {sym for kind, sym in rec.get("unfilled") or [] if kind == "close"}
            extra_src = {x for x in src_state if x not in port_state}
            extra_port = {x for x in port_state if x not in src_state}
            qty = lambda st, sym: sum(x[1] for x in st if x[0] == sym)
            merged = {x[0] for x in extra_port if sum(1 for y in src_state if y[0] == x[0]) > 1
                      and qty(src_state, x[0]) == x[1]}           # two source layers in one contract: one position
            extra_src = {x for x in extra_src if x[0] not in merged}
            extra_port = {x for x in extra_port if x[0] not in merged}
            stats["named"]["merged_layer"] = stats["named"].get("merged_layer", 0) + len(merged)
            ok = all(x[0] in skipped or x[0] in sale_unfilled for x in extra_src) and \
                all(x[0] in buy_unfilled for x in extra_port)
            if a["week_opened"] != rec["week_out"]:
                ok = ok and bool(skipped) and a["week_opened"] == PL.iso_week(today_of(rec))
            if not ok:
                diffs.append({"part": "state", "case": rec["case"], "source": src_state, "port": port_state,
                              "source_week": a["week_opened"], "port_week": rec["week_out"]})
            else:
                stats["named"]["phantom_layer"] += sum(1 for x in extra_src if x[0] in skipped)
                stats["named"]["unfilled_sale"] += sum(1 for x in extra_src if x[0] in sale_unfilled)
                stats["named"]["unfilled_buyback"] += len(extra_port)
    res = {"sleeve": "qqq_put_ladder", "cases": len(plans), "identical": len(plans) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "source ladder_broker.sync() in its own tree (I/O stubbed; adapted + strict runs) vs "
                     "qqq_put_ladder.decide() on the same book, chain, closes, spot, posture and buying power"}
    write_receipt("qqq_put_ladder", res)
    return res


def today_of(rec):
    return date.fromisoformat(rec["case"]["clock"]["timestamp"][:10])
