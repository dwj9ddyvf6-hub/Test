"""rsi_meanrev_options: old rsi_meanrev_options.py scan_pass() vs the restored port's decide() on the same case.

The OLD module runs its real scan_pass(): manage_positions (spread_close_value on the legs' latest quotes, exit_due:
50% of max profit, the 7-DTE stop, current_rsi2 over its real fetch_daily_bars and the stock sleeve's real pandas
rsi_wilder; close_spread at each leg's natural), then the entry loop (live = positions + awaiting fills + closing, at
most 5; maybe_enter: rsi_signal over its real fetch_daily_bars (the forming bar dropped), _spread_for -> the real
desk/options_exec.select_debit_spread, _size_spreads -> spread_qty_for_risk, _stage_entry -> _submit_spread -> the
real options_exec.submit_debit_spread). Stubbed: the clock (FakeDT, also behind select_debit_spread's local import),
equity, the basket, the bars / chain / quote / order CLIs (the case's; the chain CLI's expiry window and tradable
filter, the order CLI's refusal of a non-positive limit), state load / save, the log, and the gates the cutover
removed (kill switch, drawdown brake -> ok, the Decision #8 earnings blackout -> clear, Decision #75 pre_buy ->
proceed, the 150% desk cap and its exposure ledger); fills are not promoted (state as given).

Compared, per case: the spreads opened (symbol, long, short, contracts, debit, each leg's price), the exit decisions
(symbol -> reason), the closes sent (symbol, contracts, net at the legs' naturals = the OMS's package natural), and the
old's skip events against the port's own filter walk. Named divergences counted, not failed, each checked against
the port's own decision under the old rule: a short leg bid at nothing (the old's order CLI refused its zero limit,
so the old sent the long alone; the port's package carries both legs, the same long); a close with the long leg bid
at zero (the old's close_spread sent nothing; the port's package closes at the natural with that leg at zero, the
same exit decision); an off-session pass (the old cron ran hourly at :31 around the clock; the port's schedule runs
only in the session -- its decide() at that instant is compared all the same). A close the old could not send for a
leg unquoted on its closing side is no divergence: the OMS defers the package (no natural) -- counted."""
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.oms import OMS
from desk.schedule import is_open
from desk.sleeves.families.femto_specs import SPECS
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("rsi_meanrev_options")
N_CASES = 1500
BATCH = 250
NAMES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "JJJ", "KKK", "LLL", "MMM", "NNN", "PPP"]
SCHEDULE = SPECS["rsi_meanrev_options"]["schedule"]

OLD = r'''
import sys, types
from datetime import datetime as _dt, timezone
import datetime as _dtmod
import rsi_meanrev_options as O
import desk as _D
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O.check_kill_switch = lambda sym: True
O._stock._earnings_ok = lambda sym, today: True
O._stock._drawdown_action = lambda: ("ok", "drawdown brake stubbed (gone under the cutover)")
O._cap_gate_entry = lambda sym, notional, equity: True
O._dx_add = lambda *a, **k: None
O._dx_remove = lambda *a, **k: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
d75.sweep_releases = lambda *a, **k: []
sys.modules["desk.decision75"] = d75
_D.decision75 = d75
O.replay_chart_gate_releases = lambda st, now, equity=None: None
O.promote_fills = lambda st, now: None
O._get_order = lambda oid: None
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
SHIM = types.ModuleType("datetime")
SHIM.__dict__.update(_dtmod.__dict__)
SHIM.datetime = FakeDT
_SDS = O._oe.select_debit_spread
def sds(*a, **k):                              # its ET 'today' comes from a function-local datetime import
    sys.modules["datetime"] = SHIM
    try:
        return _SDS(*a, **k)
    finally:
        sys.modules["datetime"] = _dtmod
O._oe.select_debit_spread = sds
class SkillError(RuntimeError):
    pass
def _arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.get_equity = lambda e=case["equity"]: e
    O.load_universe = lambda b=case["basket"]: list(b)
    def run_cli(script, args, timeout=90, case=case):
        args = [str(a) for a in args]
        if script == "alpaca_get_bars_1h.py":
            sym = _arg(args, "--symbol")
            closes = case["closes"].get(sym) or []
            ts = case["stamps"][len(case["stamps"]) - len(closes):]
            rows = [{"t": t, "o": c, "h": c, "l": c, "c": c, "v": 1e6} for t, c in zip(ts, closes)]
            if sym in case["forming"]:
                rows.append({"t": case["today_stamp"], "o": case["forming"][sym], "h": case["forming"][sym],
                             "l": case["forming"][sym], "c": case["forming"][sym], "v": 1e5})
            return rows[-int(_arg(args, "--limit") or 10):]
        raise SkillError("unexpected CLI " + script)
    O.desk.run_cli = run_cli
    def chain(ticker, expiry_gte=None, expiry_lte=None, option_type="call", C=case["chains"]):
        if ticker not in C:
            return []                                  # the CLI failed: get_option_chain returns []
        return [{"symbol": r["symbol"], "expiration": r["expiration"], "strike": r["strike"], "type": "call",
                 "multiplier": "100"} for r in C[ticker]
                if r.get("tradable", True) and (expiry_gte is None or r["expiration"] >= expiry_gte)
                and (expiry_lte is None or r["expiration"] <= expiry_lte)]
    O._oe.get_option_chain = chain
    O._oe.get_option_quote = lambda occ, Q=case["quotes"]: (dict(Q[occ]) if occ in Q else None)
    ORD = []
    def sub(occ, qty, side, limit_price, position_intent, client_id, tif="day", ORD=ORD):
        if not float(limit_price) > 0:
            raise SkillError("alpaca_option_order.py failed (exit 1): --limit-price must be a positive finite number")
        ORD.append([occ, side, int(qty), float(limit_price), position_intent])
        return {"id": "o%d" % len(ORD), "status": "accepted"}
    O._oe.submit_option_order = sub
    EV.clear()
    O.scan_pass(FakeDT.NOW)
    keep = ("exit_signal", "exit_quotes_onesided", "rsi2_signal", "entry_skipped_no_signal", "entry_skipped_no_spread",
            "entry_skipped_zero_contracts", "entry_skipped_equity_unknown", "scan_symbol_failed",
            "spread_leg_mismatch", "spread_submitted")
    out.append({"orders": ORD, "events": [{k: e.get(k) for k in ("event", "symbol", "reason", "leg", "bars", "sma200",
                                                                  "qty", "debit")} for e in EV
                                          if e.get("event") in keep]})
print(json.dumps(out))
'''


# ---------------------------------------------------------------------------------------------------- the corpus
def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _stamp(d):
    """an Alpaca daily-bar stamp: 00:00 ET of the session, in UTC."""
    return datetime(d.year, d.month, d.day, tzinfo=ET).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sessions_before(today, n):
    out, d = [], today - timedelta(days=1)
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return list(reversed(out))


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _call(S, K, T, vol, r=0.04):
    if T <= 0:
        return max(S - K, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * vol * vol) * T) / (vol * math.sqrt(T))
    return S * _ncdf(d1) - K * math.exp(-r * T) * _ncdf(d1 - vol * math.sqrt(T))


def _grid(S):
    return 0.5 if S < 25 else (1.0 if S < 60 else (2.5 if S < 150 else 5.0))


def _quote(rnd, fair):
    """a quote around a model price: mostly inside the 10% gate, some wide, a few one-sided / crossed / zero."""
    if fair < 0.03:
        return {"bid": 0.0, "ask": rnd.choice((0.01, 0.05))}
    h = rnd.choice((0.004, 0.01, 0.02, 0.03, 0.04, 0.045, 0.05, 0.055, 0.07, 0.1))
    bid = round(max(0.01, fair * (1 - h)), 2)
    ask = round(max(bid + 0.01, fair * (1 + h)), 2)
    u = rnd.random()
    if u < 0.03:
        bid = 0.0
    elif u < 0.04:
        ask = 0.0
    elif u < 0.05:
        bid, ask = ask, bid                                  # crossed
    return {"bid": bid, "ask": ask}


def _path(rnd, n, tail):
    """daily closes: a drifting walk, then a tail -- a washout (two to four down days), a bounce or nothing."""
    px = rnd.uniform(8, 400)
    drift = rnd.choice((rnd.uniform(0.0008, 0.003), rnd.uniform(0.0008, 0.003), rnd.uniform(-0.003, -0.0005),
                        rnd.uniform(-0.0006, 0.0009)))
    vol = rnd.uniform(0.006, 0.03)
    k = rnd.randint(2, 4) if tail in ("washout", "bounce") else 0
    out = []
    for i in range(n):
        if i >= n - k:
            m = rnd.uniform(0.003, 0.05)
            px *= (1 - m) if tail == "washout" else (1 + m)
        else:
            px = max(1.0, px * (1 + rnd.gauss(drift, vol)))
        out.append(px)
    nd = rnd.choice((2, 4, 4))
    return [round(max(0.5, c), nd) for c in out]


def _chain(rnd, sym, S, today):
    """call rows of 1-4 expiries 3-50 DTE (some cases none in 14-30), strikes on the name's grid."""
    grid = _grid(S) if rnd.random() < 0.8 else rnd.choice((0.5, 1.0, 2.5))
    lo = rnd.choice((0.6, 0.8, 0.9, 0.95, 0.95, 1.004, 1.02))       # >= 1: no strike at or below the close
    hi = rnd.choice((1.03, 1.06, 1.12, 1.2, 1.3, 1.5))              # < 1.08: often no short strike
    vol = rnd.uniform(0.2, 0.9)
    if rnd.random() < 0.1:
        dtes = rnd.sample([d for d in range(3, 51) if not 14 <= d <= 30], rnd.randint(1, 3))
    else:
        dtes = rnd.sample(range(3, 51), rnd.randint(1, 4))
        if not any(14 <= d <= 30 for d in dtes):
            dtes.append(rnd.randint(14, 30))
    rows, quotes = [], {}
    for dte in sorted(dtes):
        exp = (today + timedelta(days=dte)).isoformat()
        k = max(grid, math.floor(S * lo / grid) * grid if lo < 1 else math.ceil(S * lo / grid) * grid)
        while k <= S * hi + 1e-9:
            occ = _occ(sym, exp, k)
            row = {"symbol": occ, "strike": k, "expiration": exp}
            if rnd.random() < 0.02:
                row["tradable"] = False
            rows.append(row)
            if rnd.random() < 0.97:
                quotes[occ] = _quote(rnd, _call(S, k, dte / 365.0, vol))
            k = round(k + grid, 4)
    window = sorted({r["expiration"] for r in rows if 14 <= (date.fromisoformat(r["expiration"]) - today).days <= 30})
    if window and rnd.random() < 0.16:            # the would-be legs' quote edge cases: no ask, no debit, short unbid
        legs = sorted((r for r in rows if r["expiration"] == window[0] and r.get("tradable", True)),
                      key=lambda r: r["strike"])
        lo = ([r for r in legs if r["strike"] <= S] or legs[:1] or [None])[-1]
        so = next((r for r in legs if r["strike"] >= lo["strike"] * 1.08), None) if lo else None
        u = rnd.random()
        if lo is None:
            pass
        elif u < 0.3:
            quotes[lo["symbol"]] = {"bid": rnd.choice((0.0, 0.5)), "ask": 0.0}
        elif so is not None and u < 0.6 and lo["symbol"] in quotes:
            quotes[so["symbol"]] = {"bid": round(quotes[lo["symbol"]]["ask"] + rnd.choice((0.0, 0.05)), 2),
                                    "ask": round(quotes[lo["symbol"]]["ask"] + 0.1, 2)}
        elif so is not None:
            quotes[so["symbol"]] = {"bid": 0.0, "ask": rnd.choice((0.05, 0.1))}
    if rnd.random() < 0.15:
        rnd.shuffle(rows)
    return rows, quotes


def _held(rnd, sym, S, today, quotes, closing):
    """a held call debit spread: strikes on a grid around an entry close, 0-30 DTE (rarely past expiry), the legs
    quoted around a model price -- or around a close value set at the 50% line -- some one-sided or unquoted."""
    S0 = S * rnd.uniform(0.85, 1.12)
    grid = _grid(S0)
    k1 = math.floor(S0 / grid) * grid
    k2 = k1 + grid * max(1, math.ceil(k1 * 0.08 / grid - 1e-9))
    dte = rnd.choice((rnd.randint(0, 30), rnd.randint(8, 30), rnd.randint(5, 9), -1 if rnd.random() < 0.1 else 3))
    exp = (today + timedelta(days=dte)).isoformat()
    lo_occ, so_occ = _occ(sym, exp, k1), _occ(sym, exp, k2)
    width = k2 - k1
    long_fill = round(rnd.uniform(0.25, 0.65) * width + rnd.uniform(0.2, 2.0), 2)
    short_fill = round(max(0.01, long_fill - rnd.uniform(0.2, 0.65) * width), 2)
    entry_debit = round(long_fill - short_fill, 2)
    sel_debit = round(entry_debit + rnd.choice((0.0, 0.0, 0.01, -0.02, 0.05)), 2)
    if rnd.random() < 0.04:
        sel_debit = round(width + 0.05, 2)                              # max profit <= 0: no profit target
    spread = {"ticker": sym, "expiry": exp,
              "long_leg": {"occ": lo_occ, "strike": k1, "ask": long_fill, "bid": round(long_fill * 0.97, 2)},
              "short_leg": {"occ": so_occ, "strike": k2, "bid": short_fill},
              "width": round(width, 2), "debit": sel_debit, "max_profit": round(width - sel_debit, 2),
              "breakeven": round(k1 + sel_debit, 2)}
    vol, T = rnd.uniform(0.25, 0.8), max(dte, 0) / 365.0
    if rnd.random() < 0.35 and spread["max_profit"] > 0:                # the close value at the 50% line
        cv = round(entry_debit + 0.5 * spread["max_profit"] + rnd.choice((-0.02, -0.01, 0.0, 0.0, 0.01, 0.03)), 2)
        sa = round(rnd.uniform(0.05, 1.5), 2)
        lq, sq = {"bid": round(cv + sa, 2), "ask": round(cv + sa + 0.05, 2)}, {"bid": round(sa - 0.03, 2), "ask": sa}
    else:
        lq, sq = _quote(rnd, _call(S, k1, T, vol)), _quote(rnd, _call(S, k2, T, vol))
    u = rnd.random()
    if u < 0.07:
        lq["bid"] = 0.0                                                  # the long leg bid at nothing
    elif u < 0.10:
        lq = None                                                        # the long leg unquoted
    elif u < 0.13:
        sq["ask"] = 0.0
    elif u < 0.15:
        sq = None
    if lq is not None:
        quotes[lo_occ] = lq
    if sq is not None:
        quotes[so_occ] = sq
    n = rnd.randint(1, 8)
    opened = datetime(today.year, today.month, today.day, 10, 31, tzinfo=ET).timestamp() - rnd.randint(1, 20) * 86400
    old = {"ticker": sym, "spread": spread, "qty": n, "entry_debit": entry_debit,
           "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat(), "order_ids": {}}
    port = {"qty": n, "net_entry": long_fill - short_fill, "opened_at": opened, "entry_date": None, "stop_px": None,
            "legs": {lo_occ: n, so_occ: -n}, "spread": spread, "exit_submitted": True if closing else None}
    return old, port


def _case(rnd, idx):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 330))
    if rnd.random() < 0.85:                                              # the port's own passes: :31 in the session
        while not cal.is_trading_day(today):
            today += timedelta(days=1)
        hh = rnd.randint(9, 15)
    else:                                                                # the old cron's other passes
        hh = rnd.choice((0, 2, 5, 8, 9, 16, 17, 19, 20, 21, 23)) if cal.is_trading_day(today) else rnd.randint(0, 23)
    now_dt = datetime(today.year, today.month, today.day, hh, 31, rnd.randint(0, 59), tzinfo=ET)
    now = now_dt.timestamp()
    session = today.isoformat()
    started = cal.is_trading_day(today) and (hh, 31) >= (9, 30)
    days = _sessions_before(today, 259)
    stamps = [_stamp(d) for d in days]
    basket = rnd.sample(NAMES, rnd.randint(5, 11))
    others = [s for s in NAMES if s not in basket]
    closes, forming, chains, quotes = {}, {}, {}, {}
    for sym in NAMES:
        u = rnd.random()
        if u < 0.03:
            continue                                                     # no bars at all
        n = 1 if u < 0.04 else (rnd.randint(150, 199) if u < 0.12 else rnd.choice((200, 201, 230, 259, 259)))
        tail = rnd.choice(("washout", "washout", "washout", "bounce", "none"))
        cs = _path(rnd, n, tail)
        if rnd.random() < 0.25 and n >= 200:                             # the close a hair off a strike: the cent
            g = _grid(cs[-1])
            k = round(cs[-1] / g) * g
            cs[-1] = round(k - rnd.choice((0.0001, 0.0004, 0.003, 0.004, 0.006, -0.003)), 4)
        closes[sym] = cs
        if started:
            forming[sym] = round(cs[-1] * rnd.uniform(0.97, 1.03), 2)
        if rnd.random() < 0.9:
            rows, q = _chain(rnd, sym, round(cs[-1], 2), today)
            chains[sym] = rows
            quotes.update(q)
    state = {"positions": {}, "awaiting_fills": {}, "closing": {}}
    ss = {}
    k_held = rnd.choice((0, 0, 1, 2, 3, 4, 5, 6))
    for sym in rnd.sample(basket + others, min(k_held, len(NAMES))):
        u = rnd.random()
        if u < 0.2:                                                      # an entry in flight
            state["awaiting_fills"][sym] = {"ticker": sym, "qty": 1, "order_ids": {},
                                            "submitted_at": datetime.fromtimestamp(now - 600, tz=timezone.utc).isoformat()}
            pe = {"qty": 1.0, "filled": 0.0, "key": "%s:%s:rmo" % (sym, session), "ref_px": None}
            # the adapter files a package in flight under the package's id (MLEG:<sym>:<group> -> its last part)
            ss[("%08x" % rnd.getrandbits(32)) if rnd.random() < 0.7 else sym] = {"position": None, "pending_entry": pe}
            continue
        S = closes[sym][-1] if sym in closes else rnd.uniform(10, 300)
        closing = u < 0.32
        old, port = _held(rnd, sym, S, today, quotes, closing)
        (state["closing"] if closing else state["positions"])[sym] = old
        ss[sym] = {"position": port}
    u = rnd.random()
    equity = None if u < 0.06 else (0.0 if u < 0.09 else (rnd.uniform(15_000, 60_000) if u < 0.25 else
                                                          rnd.uniform(60_000, 3_000_000)))
    return {"idx": idx, "now": now, "session": session, "today_stamp": _stamp(today), "stamps": stamps,
            "closes": closes, "forming": forming, "basket": basket, "chains": chains, "quotes": quotes,
            "state": state, "ss": ss, "equity": equity, "in_session": is_open(SCHEDULE, now)}


# ---------------------------------------------------------------------------------------------------- the port
def _bars(c):
    days = _sessions_before(date.fromisoformat(c["session"]), 259)
    ts = [datetime(d.year, d.month, d.day, tzinfo=ET).timestamp() for d in days]
    return {s: [{"t": t, "o": x, "h": x, "l": x, "c": x, "v": 1e6} for t, x in zip(ts[len(ts) - len(cs):], cs)]
            for s, cs in c["closes"].items()}


def _port_chains(c):
    """the chain snapshot's rows: each contract with its quote (no quote: neither bid nor ask)."""
    out = {}
    for s, rows in c["chains"].items():
        out[s] = [dict(r, type="call", strike=float(r["strike"]), **(c["quotes"].get(r["symbol"]) or
                                                                      {"bid": None, "ask": None})) for r in rows]
    return out


def _port(c, bars):
    held = {o for st in c["ss"].values() for o in ((st.get("position") or {}).get("legs") or {})}
    uni = list(c["basket"]) + [s for s, st in c["ss"].items() if st.get("position") and s not in c["basket"]]
    extra = {"universe": uni, "chains": _port_chains(c),
             "option_quotes": {o: c["quotes"][o] for o in held if o in c["quotes"]}, "sleeve_state": c["ss"]}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=float(c["equity"] or 0.0), extra=extra)
    return F.decide(bars, ctx)


def _natural(c, pos):
    """the OMS's natural for closing the package (sell the long at its bid, buy the short at its ask)."""
    lo = pos["spread"]["long_leg"]["occ"]
    so = pos["spread"]["short_leg"]["occ"]
    child = {"action": "exit", "legs": [{"symbol": lo, "side": "sell", "ratio": 1}, {"symbol": so, "side": "buy",
                                                                                      "ratio": 1}]}
    q = {"OPT:" + o: c["quotes"][o] for o in (lo, so) if o in c["quotes"]}
    nat, _legs = OMS._mleg_natural(child, q)
    return nat


def _walk(c, bars, tal):
    """the port's entry filters, walked in decide()'s order over the basket (for the coverage tallies)."""
    held, flight = set(), set()
    for key, st in c["ss"].items():
        if st.get("position"):
            held.add(key)
        elif st.get("pending_entry"):
            flight.add(F._flight_symbol(key, st["pending_entry"]))
    live = len(held | flight)
    got = {}
    for sym in c["basket"]:
        if sym in held or sym in flight:
            why = "held_or_in_flight"
        elif live >= F.MAX_POSITIONS:
            tal["slots_full"] = tal.get("slots_full", 0) + 1
            break
        elif c["equity"] is None:                 # the old: unknown equity skips; 0.0 reaches the sizing (0 spreads)
            why = "equity_unknown"
        else:
            cs = [float(b["c"]) for b in bars.get(sym) or []]
            ok, info = F.rsi_signal(cs)
            if len(cs) < 2:
                why = "no_bars"
            elif not ok:
                why = info.get("note") or "rsi_not_oversold"
            else:
                sp, why = F.pick_spread(_port_chains(c).get(sym), info["close"], c["session"])
                if sp is not None:
                    why = "zero_contracts" if F.size_spreads(float(c["equity"]), sp["debit"]) <= 0 else "entered"
                    if why == "entered":
                        live += 1
        tal[why] = tal.get(why, 0) + 1
        got[why] = got.get(why, 0) + 1
    return got


# ---------------------------------------------------------------------------------------------------- compare
def _old_view(o):
    ent, cls = {}, {}
    for occ, side, qty, px, intent in o["orders"]:
        sym = occ[:-15]
        if intent == "buy_to_open":
            ent.setdefault(sym, {})["long"] = (occ, qty, px)
        elif intent == "sell_to_open":
            ent.setdefault(sym, {})["short"] = (occ, qty, px)
        elif intent == "sell_to_close":
            cls.setdefault(sym, {})["long"] = (occ, qty, px)
        elif intent == "buy_to_close":
            cls.setdefault(sym, {})["short"] = (occ, qty, px)
    exits = {e["symbol"]: e["reason"] for e in o["events"] if e["event"] == "exit_signal"}
    onesided = {e["symbol"] for e in o["events"] if e["event"] == "exit_quotes_onesided"}
    return ent, cls, exits, onesided


def _old_skips(o):
    out = {}
    for e in o["events"]:
        ev = e["event"]
        k = {"entry_skipped_no_spread": "no_spread", "entry_skipped_zero_contracts": "zero_contracts",
             "entry_skipped_equity_unknown": "equity_unknown", "scan_symbol_failed": "no_bars",
             "rsi2_signal": "entered"}.get(ev)
        if ev == "entry_skipped_no_signal":
            k = "ma200_warmup" if e.get("bars") is not None else ("below_ma200" if e.get("sma200") is not None else None)
        if k:
            out[k] = out.get(k, 0) + 1
    return out


def _compare(c, o, intents, stats):
    """[] when the case is identical up to the named divergences (counted in stats); else what differs."""
    bad = []
    ent, cls, oex, onesided = _old_view(o)
    pent = {i.symbol: i for i in intents if i.kind == "enter"}
    pex = {i.symbol: i for i in intents if i.kind == "exit"}
    for sym in sorted(set(ent) | set(pent)):
        oe, pe = ent.get(sym), pent.get(sym)
        if oe is None or pe is None or "long" not in oe:
            bad.append(("entry", sym))
            continue
        sp = pe.position_meta["spread"]
        lo, so = sp["long_leg"], sp["short_leg"]
        close = c["closes"][sym][-1]
        if close < lo["strike"] <= round(close, 2):
            stats["long_strike_at_the_cent"] += 1         # the strike sits between the close and its cent
        elif lo["strike"] > round(close, 2):
            stats["long_lowest_strike_fallback"] += 1     # no strike at or below the close
        lpart = oe["long"] == (lo["occ"], int(pe.qty_hint), lo["ask"]) and pe.legs[0]["symbol"] == lo["occ"]
        if "short" not in oe:                     # named: the old's order CLI refused the short's zero limit
            if lpart and so["bid"] == 0 and pe.net_price == round(lo["ask"], 2):
                stats["unbid_short_entries"] += 1
            else:
                bad.append(("entry_unbid_short", sym))
            continue
        if not (lpart and oe["short"] == (so["occ"], int(pe.qty_hint), so["bid"]) and pe.legs[1]["symbol"] == so["occ"]
                and pe.net_price == round(oe["long"][2] - oe["short"][2], 2)):
            bad.append(("entry", sym))
        stats["opened"] += 1
    preason = {s: i.reason.split(": ", 1)[1].split(" ")[0] for s, i in pex.items()}
    if preason != oex:
        bad.append(("exit_decisions", sorted(set(preason.items()) ^ set(oex.items()))))
    for sym, why in oex.items():
        kind = why.rsplit("_", 1)[0] if why.startswith(("dte_", "rsi2_")) else why
        stats["exit_decisions"][kind] = stats["exit_decisions"].get(kind, 0) + 1
    for sym, i in pex.items():
        pos = c["ss"][sym]["position"]
        nat = _natural(c, pos)
        oc = cls.get(sym)
        if oc is not None:                        # the old sent both closes at each leg's natural
            ok = ("long" in oc and "short" in oc and oc["long"][1] == oc["short"][1] == int(i.qty_hint)
                  and nat is not None and abs(-nat - (oc["long"][2] - oc["short"][2])) < 1e-9)
            if not ok:
                bad.append(("close", sym))
            else:
                k = preason[sym].rsplit("_", 1)[0] if preason[sym].startswith(("dte_", "rsi2_")) else preason[sym]
                stats["closed"][k] = stats["closed"].get(k, 0) + 1
        elif sym in onesided:
            lq = c["quotes"].get(pos["spread"]["long_leg"]["occ"]) or {}
            sq = c["quotes"].get(pos["spread"]["short_leg"]["occ"]) or {}
            if nat is None:                       # the OMS defers the package too: no order either way
                stats["close_deferred_unquoted"] += 1
            elif lq.get("bid") == 0 and float(sq.get("ask") or 0) > 0:
                stats["close_long_unbid"] += 1    # named: the port closes with the long leg at zero
            else:
                bad.append(("close_onesided", sym))
        else:
            bad.append(("close_missing", sym))
    if set(cls) - set(pex):
        bad.append(("close_extra", sorted(set(cls) - set(pex))))
    return bad


def run():
    rnd = random.Random(1016)
    cases = [_case(rnd, i) for i in range(N_CASES)]
    old = []
    for b in range(0, len(cases), BATCH):
        old += old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("ss", "session", "in_session", "idx")}
                                       for c in cases[b:b + BATCH]]})
    stats = {"in_session": 0, "off_session": 0, "off_session_with_orders": 0, "opened": 0, "unbid_short_entries": 0,
             "long_strike_at_the_cent": 0, "long_lowest_strike_fallback": 0, "exit_decisions": {}, "closed": {},
             "close_long_unbid": 0, "close_deferred_unquoted": 0, "entry_filters": {}}
    diffs = []
    for c, o in zip(cases, old):
        bars = _bars(c)
        intents = _port(c, bars)
        bad = _compare(c, o, intents, stats)
        got = _walk(c, bars, stats["entry_filters"])
        want = _old_skips(o)
        mine = {k: v for k, v in got.items() if k in ("ma200_warmup", "below_ma200", "zero_contracts", "equity_unknown",
                                                       "no_bars", "entered")}
        spread_whys = sum(v for k, v in got.items() if k in ("no_expiry_in_window", "no_short_strike", "leg_unquoted",
                                                              "long_no_ask", "long_illiquid", "no_debit"))
        if spread_whys:
            mine["no_spread"] = spread_whys
        if mine != want:
            bad.append(("filters", mine, want))
        if c["in_session"]:
            stats["in_session"] += 1
        else:                                     # named: the old cron's off-session pass (the port: not scheduled)
            stats["off_session"] += 1
            stats["off_session_with_orders"] += bool(o["orders"])
        if bad:
            diffs.append({"case": c["idx"], "session": c["session"], "now": c["now"], "what": bad[:6],
                          "old_orders": o["orders"][:8]})
    res = {"sleeve": "rsi_meanrev_options", "cases": len(cases), "identical": len(cases) - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "method": "old scan_pass (clock, equity, basket, bars/chain/quote/order CLIs and the removed gates stubbed; "
                     "its real fetch_daily_bars, the stock sleeve's pandas rsi_wilder, options_exec.select_debit_spread "
                     "and submit_debit_spread) vs port decide()"}
    write_receipt("rsi_meanrev_options", res)
    return res
