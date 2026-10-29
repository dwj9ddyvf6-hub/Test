"""ema_vwap_options: old ema_vwap_options.py scan_pass() vs the restored port's decide() on the same case.

The OLD module runs its real scan_pass(): manage_positions (ev.add_indicators over the case's completed daily bars,
the 31-bar guard, exit_due: the conservative value against 50% of max profit, the 7-DTE stop, ev.reverted_to_vwap,
the 21-day hold; close_spread: the long sold at its bid and the short bought at its ask, never one-sided), then --
while fewer than 5 spreads are live (positions + awaiting fills + closing) -- the universe in order: the 31-bar
warmup, maybe_enter (ev.deviation_below, pick_spread over the real desk/options_exec.select_debit_spread on the case's
chain and quote CLIs, spread_qty_for_risk, _submit_spread: refresh_spread_quotes, then submit_debit_spread, the long
leg and the short leg). Stubbed: the clock (FakeDT, also inside select_debit_spread), equity, the universe, the daily
bars, the chain / quote / order CLIs, and the gates the cutover removed (kill switch, drawdown brake, Decision #75
pre_buy -> proceed and its release replay, the Decision #8 earnings veto, the 150% desk cap); fills are not promoted
(the state as given).

Compared exactly: the spreads opened (symbol, long, short, contracts, debit), every exit decision (symbol -> reason:
the old's exit_signal events, including exits whose close could not go out), the spreads closed (symbol, contracts,
natural net). Named divergences counted, not failed: each spread is one package (the old: two single-leg orders at
the same prices); an in-flight package the adapter files under its group id is recognised by its order key (the
case puts some there). The schedule, chain-snapshot quotes, re-decided unfilled orders and the fill-time 21-day
clock are outside a single-pass comparison (unit tests: tests/test_femto_ema_vwap_options.py)."""
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import as_epoch, femto_module, old_run, write_receipt

F = femto_module("ema_vwap_options")
N_CASES = 1500
BATCH = 250
NAMES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ", "KKK", "LLL"]

OLD = r'''
import sys, types
import datetime as _dtmod
from datetime import datetime as _dt, timezone
import pandas as pd
import ema_vwap_options as O
import ema_vwap_sleeve as ev
import desk as _D
from desk import options_exec as _oe
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O.kill_switch_blocks = lambda sym: False
O.drawdown_allows = lambda sym: (True, 1)
O._cap_gate_entry = lambda sym, n, e: True
O._dx_add = lambda *a, **k: None
O._dx_remove = lambda *a, **k: None
O.replay_chart_gate_releases = lambda *a, **k: None
O.promote_fills = lambda st, now: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
d75.sweep_releases = lambda *a, **k: []
sys.modules["desk.decision75"] = d75
_D.decision75 = d75
ev.earnings_veto = lambda *a, **k: None
ev.load_earnings = lambda: ({}, True)
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
_real_select = _oe.select_debit_spread
def _select(*a, **k):
    saved = _dtmod.datetime
    _dtmod.datetime = FakeDT                      # select_debit_spread reads its ET date from the clock
    try:
        return _real_select(*a, **k)
    finally:
        _dtmod.datetime = saved
_oe.select_debit_spread = _select
def frame(rows):
    df = pd.DataFrame([(pd.Timestamp(r["d"]), r["o"], r["h"], r["l"], r["c"], r["v"]) for r in rows],
                      columns=["date", "o", "h", "l", "c", "v"]).set_index("date").sort_index()
    return df
def _arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    _oe.get_account_equity = lambda e=case["equity"]: e
    ev.universe = lambda u=case["universe"]: list(u)
    B = case["bars"]
    def fetch(sym, limit=ev.BARS_LIMIT, B=B):
        if sym not in B:
            raise RuntimeError("bars fetch failed for %s" % sym)
        return frame(B[sym]).tail(limit)
    ev.fetch_daily = fetch
    def fetch_par(symbols, workers=8, B=B):
        res = {}
        for s in symbols:
            try:
                res[s] = (True, fetch(s))
            except Exception as e:
                res[s] = (False, e)
        return res
    ev.fetch_daily_parallel = fetch_par
    ORD = []
    def run_cli(script, args, timeout=90, C=case["chains"], Q=case["quotes"], ORD=ORD):
        args = [str(a) for a in args]
        if script == "alpaca_option_chain.py":
            u, typ = _arg(args, "--underlying"), _arg(args, "--type")
            lo, hi = _arg(args, "--expiry-gte"), _arg(args, "--expiry-lte")
            return [dict(r, strike="%g" % r["strike"], type="call", multiplier="100") for r in C.get(u, [])
                    if typ == "call" and lo <= r["expiration"] <= hi]
        if script == "alpaca_option_quotes.py":
            occ = _arg(args, "--symbols")
            q = Q.get(occ)
            return {occ: {"bid": q["bid"], "ask": q["ask"]}} if q else {}
        if script == "alpaca_option_order.py":
            ORD.append([_arg(args, "--symbol"), _arg(args, "--side"), int(_arg(args, "--qty")),
                        float(_arg(args, "--limit-price")), _arg(args, "--position-intent")])
            return {"id": "o%d" % len(ORD), "status": "accepted"}
        raise RuntimeError("unexpected CLI " + script)
    O.desk.run_cli = run_cli
    EV.clear()
    O.scan_pass(FakeDT.NOW.astimezone(O.ET))
    exits = {e["symbol"]: e["reason"] for e in EV if e.get("event") == "exit_signal"}
    kinds = {}
    for e in EV:
        kinds[e.get("event")] = kinds.get(e.get("event"), 0) + 1
    out.append({"orders": ORD, "exits": exits, "events": kinds})
print(json.dumps(out))
'''


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _call(S, K, T, iv, r=0.04):
    if T <= 0:
        return max(0.0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
    return S * _ncdf(d1) - K * math.exp(-r * T) * _ncdf(d1 - iv * math.sqrt(T))


def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _days(end, n):
    out, d = [], end
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def _vwap(rows):
    num = den = 0.0
    for b in rows:
        if not b["v"]:
            return None
        num += (b["h"] + b["l"] + b["c"]) / 3.0 * b["v"]
        den += b["v"]
    return num / den if den else None


def _bars(rnd, end, n, zero_p=0.01, steer=(0.90, 1.05)):
    """completed daily bars ending at `end`; the last close steered against the VWAP of the 20 sessions."""
    px = rnd.choice((rnd.uniform(6, 30), rnd.uniform(30, 150), rnd.uniform(150, 600)))
    rows = []
    for d in _days(end, n):
        o = px * (1 + rnd.gauss(0, 0.006))
        c = max(1.0, px * (1 + rnd.gauss(0, 0.02)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.008)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.008)))
        v = 0.0 if rnd.random() < zero_p else float(int(rnd.uniform(2e5, 5e6)))
        rows.append({"d": d.isoformat(), "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                     "v": v})
        px = c
    if len(rows) >= 21 and rnd.random() < 0.9:
        vw = _vwap(rows[-21:-1])
        if vw:
            last = rows[-1]
            last["c"] = round(vw * rnd.uniform(*steer), 4)
            last["h"] = round(max(last["o"], last["c"]) * 1.004, 4)
            last["l"] = round(min(last["o"], last["c"]) * 0.996, 4)
    return rows


def _grid(S, rnd):
    if S < 25:
        return rnd.choice((0.5, 1.0))
    if S < 100:
        return rnd.choice((1.0, 2.5))
    if S < 250:
        return rnd.choice((2.5, 5.0))
    return rnd.choice((5.0, 10.0))


def _quote(rnd, fair):
    u = rnd.random()
    if u < 0.04:
        return None                                       # no quote at all
    if u < 0.06:
        return {"bid": 0.0, "ask": 0.0}                   # an empty book
    h = rnd.choice((0.01, 0.015, 0.02, 0.03, 0.04, 0.045, 0.05, 0.07))
    bid = round(max(0.01, fair * (1 - h)), 2)
    ask = round(max(bid + 0.01, fair * (1 + h)), 2)
    if u < 0.09:
        bid = 0.0                                         # offered only
    elif u < 0.11:
        bid, ask = round(fair * 3 + 0.5, 2), round(fair * 3 + 0.6, 2)    # a stale / crossed print
    return {"bid": bid, "ask": ask}


def _chain(rnd, sym, S, today):
    """call contracts on 1-3 expiries (some outside 14-30 DTE) and their quotes."""
    g = _grid(S, rnd)
    lo, hi = rnd.choice(((0.8, 1.25), (0.8, 1.25), (0.8, 1.25), (1.04, 1.3), (0.7, 1.05)))
    iv = rnd.uniform(0.2, 0.9)
    rows, quotes = [], {}
    for dte in sorted(rnd.sample(list(range(5, 45)), rnd.randint(1, 3))):
        exp = (today + timedelta(days=dte)).isoformat()
        k = max(g, math.ceil(S * lo / g) * g)
        while k <= S * hi:
            occ = _occ(sym, exp, k)
            rows.append({"symbol": occ, "strike": float(k), "expiration": exp})
            q = _quote(rnd, max(0.01, _call(S, k, dte / 365.0, iv)))
            if q is not None:
                quotes[occ] = q
            k = round(k + g, 4)
    return rows, quotes


def _held(rnd, sym, S, today, now, quotes):
    """a spread held since `opened`: the old's position record and the port's book group."""
    g = _grid(S, rnd)
    exp = (today + timedelta(days=rnd.randint(2, 32))).isoformat()
    kl = max(g, round(S * rnd.uniform(0.92, 1.06) / g) * g)
    ks = kl + g * max(1, round(kl * 0.06 / g))
    lo_occ, sh_occ = _occ(sym, exp, kl), _occ(sym, exp, ks)
    width = round(ks - kl, 2)
    debit = round(width * rnd.uniform(0.15, 0.7), 2)
    la = round(debit + rnd.uniform(0.2, 2.0), 2)
    sb = round(la - debit, 2)
    spread = {"ticker": sym, "expiry": exp, "long_leg": {"occ": lo_occ, "strike": kl, "ask": la, "bid": round(la - 0.05, 2)},
              "short_leg": {"occ": sh_occ, "strike": ks, "bid": sb}, "width": width, "debit": debit,
              "max_profit": round(width - debit, 2), "breakeven": round(kl + debit, 2)}
    lf = round(la + rnd.choice((0.0, 0.0, -0.01, -0.03, 0.02)), 2)
    sf = round(sb + rnd.choice((0.0, 0.0, 0.01, -0.02)), 2)
    entry_debit = round(lf - sf, 2)
    value = entry_debit + spread["max_profit"] * rnd.uniform(-0.9, 0.95)
    sa = round(rnd.uniform(0.05, 1.5), 2)
    lb = round(max(0.0, value + sa), 2)
    u = rnd.random()
    lq = {"bid": lb, "ask": round(lb + rnd.choice((0.05, 0.1, 0.2)), 2)}
    sq = {"bid": round(max(0.0, sa - rnd.choice((0.05, 0.1))), 2), "ask": sa}
    if u < 0.05:
        lq = None
    elif u < 0.10:
        sq = None
    elif u < 0.15:
        lq["bid"] = 0.0
    elif u < 0.18:
        sq["ask"] = 0.0
    for occ, q in ((lo_occ, lq), (sh_occ, sq)):
        if q is None:
            quotes.pop(occ, None)
        else:
            quotes[occ] = q
    n = rnd.randint(1, 9)
    opened = int(now) - rnd.randint(0, 26) * 86400 - rnd.randint(0, 86399)
    old = {"ticker": sym, "spread": spread, "contracts": n, "entry_debit": entry_debit,
           "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat(),
           "order_ids": {"long": "l-" + sym, "short": "s-" + sym}}
    port = {"qty": n, "net_entry": lf - sf, "opened_at": float(opened), "legs": {lo_occ: n, sh_occ: -n},
            "spread": spread, "entry_date": datetime.fromtimestamp(opened, tz=ET).date().isoformat(), "stop_px": None}
    return old, port


def _case(rnd, idx):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 280))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(9, 15), 31, rnd.randint(0, 59), tzinfo=ET).timestamp()
    prev = cal.prev_trading_day(today)
    universe = rnd.sample(NAMES, rnd.randint(3, 8))
    bars, chains, quotes = {}, {}, {}
    steer = rnd.choice(((0.90, 1.05), (0.90, 0.99), (0.95, 1.02)))
    for s in universe:
        u = rnd.random()
        if u < 0.04:
            continue                                         # the fetch fails
        n = rnd.randint(15, 30) if u < 0.09 else rnd.randint(31, 45)
        bars[s] = _bars(rnd, prev, n, zero_p=rnd.choice((0.0, 0.0, 0.0, 0.004, 0.02)), steer=steer)
        if rnd.random() < 0.92:
            rows, q = _chain(rnd, s, bars[s][-1]["c"], today)
            chains[s] = rows
            quotes.update(q)
    state = {"positions": {}, "awaiting_fills": {}, "closing": {}, "pending": {}}
    ss = {}
    held_n = rnd.choice((0, 0, 1, 2, 3, 4, 5, 6))
    for s in rnd.sample(NAMES, held_n):
        u = rnd.random()
        if s not in bars and rnd.random() < 0.9:
            bars[s] = _bars(rnd, prev, rnd.randint(25, 45) if rnd.random() < 0.1 else rnd.randint(31, 45),
                            zero_p=0.01, steer=(0.93, 1.07))
        S = bars[s][-1]["c"] if s in bars else rnd.uniform(10, 300)
        if u < 0.15:
            state["awaiting_fills"][s] = {"ticker": s, "contracts": 1}
            k = s if rnd.random() < 0.3 else "%010x" % rnd.getrandbits(40)      # the adapter: the group id
            ss[k] = {"position": None,
                     "pending_entry": {"qty": 1.0, "filled": 0.0, "key": "%s:%s:ema-vwap-options" % (s, today.isoformat()),
                                       "ref_px": None}}
            continue
        old, port = _held(rnd, s, S, today, now, quotes)
        if u < 0.25:
            state["closing"][s] = dict(old, close_order_ids=["c-" + s], close_reason="dte_time_stop_7")
            port["exit_submitted"] = True
        else:
            state["positions"][s] = old
        ss[s] = {"position": port}
    equity = rnd.choice((rnd.uniform(2_000, 30_000), rnd.uniform(30_000, 300_000), rnd.uniform(300_000, 3_000_000)))
    return {"now": now, "session": today.isoformat(), "universe": universe, "bars": bars, "chains": chains,
            "quotes": quotes, "state": state, "ss": ss, "equity": equity}


def _port_inputs(c):
    today = date.fromisoformat(c["session"])
    lo, hi = (today + timedelta(days=F.DTE_MIN)).isoformat(), (today + timedelta(days=F.DTE_MAX)).isoformat()
    chains = {s: [dict(r, type="call", **(c["quotes"].get(r["symbol"]) or {"bid": None, "ask": None}))
                  for r in rows if lo <= r["expiration"] <= hi] for s, rows in c["chains"].items()}
    held = {o for st in c["ss"].values() for o in ((st.get("position") or {}).get("legs") or {})}
    extra = {"universe": list(c["universe"]), "chains": chains, "closed_trades": [],
             "option_quotes": {o: dict(c["quotes"][o]) for o in held if o in c["quotes"]}, "sleeve_state": c["ss"]}
    bars = {s: as_epoch(rows) for s, rows in c["bars"].items()}
    return bars, fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)


def _port(c):
    bars, ctx = _port_inputs(c)
    intents = F.decide(bars, ctx)
    opened, closed = [], []
    for i in intents:
        if i.kind == "enter":
            opened.append([i.symbol, i.legs[0]["symbol"], i.legs[1]["symbol"], int(i.qty_hint), round(i.net_price, 2)])
        else:
            closed.append([i.symbol, int(i.qty_hint), i.reason.split(": ", 1)[1].split(" ")[0], round(i.net_price, 2)])
    # every exit decision (also those whose close must wait), from the port's own exit rules
    exits = {}
    for s, st in c["ss"].items():
        pos = st.get("position")
        if not pos or pos.get("exit_submitted"):
            continue
        h = F.held_spread(pos)
        bl = bars.get(s) or []
        if h is None or len(bl) < F.WARMUP_BARS + 1:
            continue
        value = F.spread_value(h["spread"], ctx.extra["option_quotes"])
        why = F.exit_due(h["spread"], h["entry_debit"], bl, value, c["now"], h["opened_at"], c["session"])
        if why:
            exits[s] = why
    return opened, closed, exits, bars, ctx


def _old_view(o):
    opened, closed = [], []
    by_sym = {}
    for occ, side, qty, px, intent in o["orders"]:
        by_sym.setdefault(occ[:-15], []).append((occ, side, qty, px, intent))
    for sym, legs in by_sym.items():
        op = {}
        for x in legs:
            op.setdefault(x[4], []).append(x)
        if "buy_to_open" in op or "sell_to_open" in op:
            if len(op.get("buy_to_open") or ()) != 1 or len(op.get("sell_to_open") or ()) != 1:
                opened.append([sym, "malformed", legs])
            else:
                lg, sh = op["buy_to_open"][0], op["sell_to_open"][0]
                opened.append([sym, lg[0], sh[0], lg[2] if lg[2] == sh[2] else [lg[2], sh[2]],
                               round(lg[3] - sh[3], 2)])
        if "sell_to_close" in op or "buy_to_close" in op:
            if len(op.get("sell_to_close") or ()) != 1 or len(op.get("buy_to_close") or ()) != 1:
                closed.append([sym, "malformed", legs])
            else:
                lc, sc = op["sell_to_close"][0], op["buy_to_close"][0]
                closed.append([sym, lc[2] if lc[2] == sc[2] else [lc[2], sc[2]], o["exits"].get(sym),
                               round(sc[3] - lc[3], 2)])
    return opened, closed


def _entry_why(c, sym, bars, ctx):
    """diagnostics only: the first entry rule a universe name fails, by the port's own helpers (the cap aside)."""
    st = c["ss"]
    if sym in {s for s, x in st.items() if x.get("position")} | set(F.in_flight(st)):
        return "held_or_in_flight"
    bl = bars.get(sym) or []
    if len(bl) < F.WARMUP_BARS + 1:
        return "missing_bars" if sym not in bars else "warmup_31"
    if F.rolling_vwap(bl) is None:
        return "vwap_void_zero_volume"
    if not F.deviation_below(bl):
        return "no_deviation"
    if not c["chains"].get(sym):
        return "no_chain"
    rows = ctx.extra["chains"].get(sym)
    if not rows:
        return "no_expiry_14_30"
    q = {r["symbol"]: r for r in rows}
    sp = F.pick_spread(rows, q, float(bl[-1]["c"]), c["session"])
    if not sp:
        exp = sorted({r["expiration"] for r in rows})[0]
        legs = sorted((r for r in rows if r["expiration"] == exp), key=lambda r: r["strike"])
        tgt = float(bl[-1]["c"]) * (1 + F.LONG_OTM_PCT)
        lg = ([r for r in legs if r["strike"] <= tgt] or [legs[0]])[-1]
        sh = next((r for r in legs if r["strike"] >= lg["strike"] * (1 + F.WIDTH_PCT)), None)
        if sh is None:
            return "no_short_leg"
        if lg["symbol"] not in c["quotes"] or sh["symbol"] not in c["quotes"]:
            return "leg_unquoted"
        la, lb, sb = float(lg.get("ask") or 0), float(lg.get("bid") or 0), float(sh.get("bid") or 0)
        if la <= 0:
            return "long_ask_zero"
        if lb > 0 and (la - lb) / ((la + lb) / 2) > F.LIQ_GATE_FRAC:
            return "long_too_wide"
        return "debit_not_positive"
    if sp["short_leg"]["occ"] not in c["quotes"]:
        return "leg_unquoted"
    if F.spread_qty_for_risk(sp["debit"], c["equity"]) <= 0:
        return "size_zero"
    if F.requote(sp, q) is None:
        return "requote_one_sided"
    below = [r for r in rows if r["expiration"] == sp["expiry"] and r["strike"] <= float(bl[-1]["c"]) * 1.02]
    return "eligible_long_fallback" if not below else "eligible"


def run():
    rnd = random.Random(1016)
    cases = [_case(rnd, i) for i in range(N_CASES)]
    old = []
    for b in range(0, len(cases), BATCH):
        old += old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("ss", "session")}
                                       for c in cases[b:b + BATCH]]})
    diffs = []
    stats = {"opened": 0, "packages_opened": 0, "packages_closed": 0, "closed": {}, "exit_decisions": {},
             "exits_waiting_one_sided": 0, "held_skipped_bars": 0, "closing_skipped": 0, "in_flight": 0,
             "in_flight_by_group_key": 0, "cap_full_cases": 0, "entry_rules": {}, "old_events": {}}
    for c, o in zip(cases, old):
        po, pc, pex, bars, ctx = _port(c)
        oo, oc = _old_view(o)
        bad = []
        if sorted(po) != sorted(oo):
            bad.append("opened")
        if sorted(pc) != sorted(oc):
            bad.append("closed")
        if pex != o["exits"]:
            bad.append("exit_decisions")
        if bad:
            diffs.append({"session": c["session"], "now": c["now"], "what": bad, "old": [oo, oc, o["exits"]],
                          "port": [po, pc, pex]})
        stats["opened"] += len(oo)
        stats["packages_opened"] += len(po)
        stats["packages_closed"] += len(pc)
        for x in oc:
            stats["closed"][x[2]] = stats["closed"].get(x[2], 0) + 1
        for s, r in o["exits"].items():
            stats["exit_decisions"][r] = stats["exit_decisions"].get(r, 0) + 1
        stats["exits_waiting_one_sided"] += len(set(o["exits"]) - {x[0] for x in oc})
        for k, v in o["events"].items():
            stats["old_events"][k] = stats["old_events"].get(k, 0) + v
        for s, st in c["ss"].items():
            pos = st.get("position")
            if pos and pos.get("exit_submitted"):
                stats["closing_skipped"] += 1
            elif pos and len(bars.get(s) or []) < F.WARMUP_BARS + 1:
                stats["held_skipped_bars"] += 1
            if st.get("pending_entry") and not pos:
                stats["in_flight"] += 1
                stats["in_flight_by_group_key"] += s not in NAMES
        live = len({s for s, st in c["ss"].items() if st.get("position")} | set(F.in_flight(c["ss"])))
        if live >= F.MAX_POSITIONS:
            stats["cap_full_cases"] += 1
            continue
        for s in c["universe"]:
            w = _entry_why(c, s, bars, ctx)
            stats["entry_rules"][w] = stats["entry_rules"].get(w, 0) + 1
    res = {"sleeve": "ema_vwap_options", "cases": len(cases), "identical": len(cases) - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "divergences": {"one_package_per_spread": "counted: packages_opened / packages_closed (the old: two "
                                                     "single-leg orders each, at the same prices)",
                           "in_flight_by_group_key": "counted: the adapter files an in-flight package under its "
                                                     "group id; recognised by its order key",
                           "not_in_single_pass": ["hourly passes at :31 in the session", "chain-snapshot leg quotes",
                                                  "unfilled orders re-decided at the next pass",
                                                  "21-day clock from the fill"]},
           "method": "old scan_pass (clock incl. select_debit_spread's, equity, universe, bars, chain/quote/order CLIs "
                     "and removed gates stubbed; its real exit_due / close_spread / maybe_enter / pick_spread / "
                     "select_debit_spread / refresh_spread_quotes / submit_debit_spread) vs port decide()"}
    write_receipt("ema_vwap_options", res)
    return res
