"""capitulation_options: one old cron run (capitulation_options.py --mode scan, then --mode reconcile) vs the restored
port's two passes (the scan, then the reconcile echo) on the same case.

The OLD module runs its real scan_pass() then reconcile_pass(): promote_fills over the case's in-flight buys (working,
partly filled, filled since, terminal partial, dead), the scan loop over the basket (its fetch floors: >= 200 daily and
>= 36 RTH 1H bars; live_count = positions + awaiting fills + closing < 5; maybe_enter: calc_atr_pct, detect_capitulation,
User's fear gate, select_long_call over the chain / quote CLIs, qty_for_risk, submit_long_call at the ask),
manage_positions (exit_due on the latest quote's mid, call_dte, the last RTH 1H close; close_call at the bid),
verify_closes (a working close waits, a dead one re-fires at the then-bid), then the reconcile (this run's buys filled as
the case says, ghosts, manage_positions again on its own 1H fetch). Stubbed: the clock (FakeDT, also the datetime
module's for options_exec), equity, the basket, the daily bars, the 1H fetches (the API's start date and the 65-minute
forming-bar drop emulated), the chain / quote / order / get-order / list-positions CLIs (the case's), state load / save,
the ledger and the exposure ledger, and the gates the cutover removed (kill switch, drawdown brake, Decision #75 pre_buy
-> proceed, the Decision #8 earnings blackout, the 150% desk cap). The old tree is never written.

The port: decide() on the adapter's view of the same case (the 1H bars trimmed by the adapter's own _trim, the 0-7 DTE
call rows with their quotes, the held calls' quotes), the first pass's buys filled as the case fills them, then decide()
again with scan False (the reconcile echo).

Compared: every buy (OCC, contracts, limit) and every sell (OCC, contracts, limit, reason). Named divergences are
counted, never failed, each verified against the port's own decision under the old rule: a dead close the old re-fired
at the then-bid whatever its exit rules said (the port decides it again); a close that filled since the last run, still
counted by the old during its entry loop (the port frees its slot and its symbol)."""
import copy
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.families.femto import _trim
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("capitulation_options")
N_CASES = 1500
NAMES = ["AAOI", "SOXL", "NBIS", "IREN", "CORZ", "HIVE", "POET", "ARQQ", "WYFI", "AEHR", "AXTI", "VELO", "DGXX",
         "SNDK"]
MODES = (("signal", 0.40), ("ema_out", 0.08), ("red_last", 0.07), ("rsi_flat", 0.07), ("rsi_high", 0.07),
         ("vol_low", 0.07), ("atr_low", 0.06), ("short_daily", 0.03), ("no_daily", 0.02), ("short_h1", 0.03),
         ("no_h1", 0.02), ("noise", 0.08))

OLD = r'''
import copy, sys, types
import datetime as _dtmod
from datetime import datetime as _dt, timedelta, timezone
import capitulation_options as O
import options_exec as X
import sleeve_core as C
import desk as _D


class FakeDT(_dt):
    NOW = None

    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW


EV, SELLS, ORD = [], [], []


def _log(e):
    e = dict(e)
    EV.append(e)
    if e.get("event") == "call_closed":
        SELLS.append([e["occ"], int(e["qty"]), float(e["limit"]), e["reason"]])


def _mod(name, **fns):
    m = types.ModuleType("desk." + name)
    for k, v in fns.items():
        setattr(m, k, v)
    sys.modules["desk." + name] = m
    setattr(_D, name, m)
    return m


O.log = _log
O.save_state = lambda s: None
O.DRY_RUN = False
O._dx_add = lambda *a, **k: None                                  # the exposure ledger: never written
O._dx_remove = lambda *a, **k: None
O._cap_gate_entry = lambda sym, notional, equity: True            # 150% desk cap: gone
O.check_kill_switch = lambda sym: True                            # risk gate: gone
O.check_drawdown_ok = lambda: "ok"                                # drawdown brake: gone
O.check_earnings_ok = lambda sym: True                            # Decision #8 earnings blackout: gone
O.replay_chart_gate_releases = lambda st, now, equity=None: None  # Decision #75 staging / release: gone
_mod("decision75", pre_buy=lambda *a, **k: "proceed", sweep_releases=lambda *a, **k: [])
_mod("judgment_telemetry", screen_out=lambda *a, **k: None)
SENT = _mod("sentiment", fear_gate_ok=lambda: (True, "stub"))
O.datetime = FakeDT
_dtmod.datetime = FakeDT          # options_exec reads the clock via `from datetime import datetime` at call time

out = []
for case in PAYLOAD["cases"]:
    NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    FakeDT.NOW = NOW
    ST = O.fresh_state()
    ST.update(copy.deepcopy(case["state"]))
    O.load_state = lambda ST=ST: ST
    O.get_equity = lambda e=case["equity"]: e
    O.load_basket = lambda b=case["basket"]: list(b)
    SENT.fear_gate_ok = lambda f=case["fear"]: (bool(f), "stub composite")

    def daily(sym, limit=260, D=case["daily"]):
        if sym not in D:
            raise RuntimeError("no daily bars for %s" % sym)
        return [dict(b) for b in D[sym]][-limit:]
    O.fetch_daily_bars = daily

    def h1_fetch(sym, days, H=case["h1"], NOW=NOW):
        if sym not in H:
            raise RuntimeError("no 1h bars for %s" % sym)
        start = (NOW.astimezone(O.ET).date() - timedelta(days=days + 5)).isoformat() + "T00:00:00Z"
        return [dict(b) for b in H[sym] if b["t"] >= start
                and (NOW - _dt.fromisoformat(b["t"].replace("Z", "+00:00"))).total_seconds() >= 65 * 60]

    def batch(symbols, days=30, max_workers=6, f=h1_fetch):
        res, errs = {}, []
        for s in symbols:
            try:
                r = f(s, days)
            except Exception as e:
                errs.append("%s: %s" % (s, e))
                continue
            if r:
                res[s] = r
        return res, errs
    C.fetch_1h_bars_batch = batch
    C.fetch_1h_bars = lambda sym, days=30, attempts=3, f=h1_fetch: f(sym, days)
    ORDERS = {k: dict(v) for k, v in case["orders"].items()}
    FILL, FLAT = set(case["fill_now"]), set(case["flat_occs"])
    PHASE = {"p": "scan"}
    del ORD[:], SELLS[:], EV[:]

    def run_cli(script, args, timeout=90, K=case, ORDERS=ORDERS):
        a = [str(x) for x in args]

        def arg(flag):
            return a[a.index(flag) + 1] if flag in a else None
        if script == "alpaca_option_chain.py":
            u = arg("--underlying")
            if u in K["chain_fail"] or u not in K["chains"]:
                raise RuntimeError("chain fetch failed")
            lo, hi, typ = arg("--expiry-gte"), arg("--expiry-lte"), arg("--type")
            return [dict(r) for r in K["chains"][u] if r["type"] == typ and lo <= r["expiration"] <= hi]
        if script == "alpaca_option_quotes.py":
            res = {}
            for occ in arg("--symbols").split(","):
                q = K["quotes"].get(occ)
                if q is None:
                    continue
                b, k = float(q.get("bid") or 0), float(q.get("ask") or 0)
                mid = (b + k) / 2.0 if b > 0 and k > 0 else 0.0
                res[occ] = {"bid": b, "ask": k, "mid": round(mid, 4), "spread_frac": (k - b) / mid if mid > 0 else None}
            return res
        if script == "alpaca_option_order.py":
            oid = "run%d" % (len(ORD) + 1)
            row = [arg("--side"), arg("--symbol"), int(arg("--qty")), float(arg("--limit-price")),
                   arg("--position-intent")]
            ORD.append(row)
            ORDERS[oid] = {"id": oid, "status": "accepted", "filled_qty": "0", "filled_avg_price": None,
                           "symbol": row[1], "side": row[0], "qty": row[2], "limit": row[3]}
            return {"id": oid, "status": "accepted"}
        raise RuntimeError("unexpected CLI " + script)
    O.desk.run_cli = run_cli

    def get_order(oid, ORDERS=ORDERS, FILL=FILL, PHASE=PHASE):
        o = ORDERS.get(str(oid))
        if o is None:
            return None
        if PHASE["p"] == "reconcile" and str(oid).startswith("run") and o["side"] == "buy" \
                and o["symbol"][:-15] in FILL:                     # this run's buy, filled by the reconcile
            return dict(o, status="filled", filled_qty=str(o["qty"]), filled_avg_price=str(o["limit"]))
        return dict(o)
    O._get_order = get_order

    def broker(ST=ST, ORDERS=ORDERS, FLAT=FLAT):
        res = {}
        for bucket in ("positions", "closing"):
            for p in (ST.get(bucket) or {}).values():
                if isinstance(p, dict) and p.get("occ") and p["occ"] not in FLAT:
                    res[p["occ"]] = float(p.get("qty") or 0)
        for af in (ST.get("awaiting_fills") or {}).values():
            fq = float((ORDERS.get(str(af.get("order_id"))) or {}).get("filled_qty") or 0)
            if fq > 0:
                res[af["call"]["occ"]] = fq
        return res
    O.broker_option_positions = broker
    O.scan_pass(NOW)
    PHASE["p"] = "reconcile"
    O.reconcile_pass(NOW)
    ev = {}
    for e in EV:
        ev[e.get("event")] = ev.get(e.get("event"), 0) + 1
    out.append({"buys": sorted([o[1], o[2], o[3]] for o in ORD if o[0] == "buy"),
                "signals": sorted(e["symbol"] for e in EV if e.get("event") == "capitulation_signal"),
                "buy_intents": sorted(o[4] for o in ORD if o[0] == "buy"),
                "sell_intents": sorted(o[4] for o in ORD if o[0] == "sell"),
                "n_sell_orders": sum(1 for o in ORD if o[0] == "sell"), "sells": sorted(SELLS), "events": ev})
print(json.dumps(out))
'''


# ------------------------------------------------------------------------------------------------ the synthetic world
def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _iso_z(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sessions_before(d, n):
    out = []
    d = cal.prev_trading_day(d)
    while len(out) < n:
        out.append(d)
        d = cal.prev_trading_day(d)
    return list(reversed(out))


def _daily(rnd, today, n, px, vol):
    rows = []
    for d in _sessions_before(today, n):
        c = max(1.0, px * (1 + rnd.gauss(0, vol)))
        o = px * (1 + rnd.gauss(0, vol / 3))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        rows.append({"d": d.isoformat(), "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                     "v": float(int(rnd.uniform(3e5, 6e6)))})
        px = c
    return rows


def _h1(rnd, today, now, px, mode, sessions_back=12):
    """clock-hour 1H bars (04..19 ET starts) of the sessions since today - 17 days, completed by `now` (the hub's
    rule: the hour ended >= 16 minutes ago); the RTH bars (09..15) carry the capitulation shape at the end."""
    days = [d for d in _sessions_before(today, sessions_back) if (today - d).days <= 17]
    if cal.is_trading_day(today):
        days.append(today)
    if mode == "short_h1":
        days = days[-3:]
    rows = []
    for d in days:
        for hh in range(4, 20):
            t = datetime(d.year, d.month, d.day, hh, 0, tzinfo=ET).timestamp()
            if t + 3600 > now - 960:
                continue
            o = px
            c = max(0.5, px * (1 + rnd.gauss(0, 0.008 if 9 <= hh <= 15 else 0.003)))
            rows.append({"t": t, "o": o, "h": max(o, c) * (1 + abs(rnd.gauss(0, 0.003))),
                         "l": min(o, c) * (1 - abs(rnd.gauss(0, 0.003))), "c": c,
                         "v": float(int(rnd.uniform(2e4, 2e5) if 9 <= hh <= 15 else rnd.uniform(1e3, 2e4)))})
            px = c
    rth = [i for i, b in enumerate(rows) if 9 <= datetime.fromtimestamp(b["t"], tz=ET).hour <= 15]
    if len(rth) >= 16 and mode not in ("noise", "short_h1"):
        drops = 3 if mode == "rsi_high" else rnd.randint(9, 13)
        step = 0.995 if mode == "rsi_high" else rnd.uniform(0.97, 0.985)
        seq = rth[-(drops + 2):]
        prev_c = rows[seq[0] - 1]["c"] if seq[0] > 0 else rows[seq[0]]["o"]
        for i in seq[:-2]:                                     # the waterfall
            nc = prev_c * step
            rows[i] = dict(rows[i], o=prev_c, c=nc, h=prev_c * 1.002, l=nc * 0.998)
            prev_c = nc
        i_cl, i_gr = seq[-2], seq[-1]
        cc = prev_c * rnd.uniform(0.955, 0.975)
        base = sum(rows[j]["v"] for j in rth[-22:-2]) / 20.0
        vmult = rnd.uniform(1.2, 1.95) if mode == "vol_low" else rnd.uniform(2.3, 6.0)
        rows[i_cl] = dict(rows[i_cl], o=prev_c, c=cc, h=prev_c * 1.001, l=cc * rnd.uniform(0.985, 0.998),
                          v=float(int(base * vmult)))
        if mode == "red_last":
            go, gc = cc * 1.004, cc * 0.997
        elif mode == "rsi_flat":
            go, gc = cc * 0.985, cc * 0.995                   # green, but the close is under the climax close
        else:
            go, gc = cc * rnd.uniform(0.997, 1.0), cc * rnd.uniform(1.006, 1.02)
        rows[i_gr] = dict(rows[i_gr], o=go, c=gc, h=max(go, gc) * 1.003, l=min(go, gc) * 0.998,
                          v=float(int(rnd.uniform(5e4, 3e5))))
    return rows, [rows[i] for i in rth]


def _scale_to_ema(rnd, rows, rth, ema, mode):
    if not rth or not ema or len(rth) < 2:
        return rows
    lo = rth[-2]["l"]
    if mode == "ema_out":
        k = rnd.choice((-1, 1)) * rnd.uniform(0.021, 0.06)
    elif mode in ("signal", "red_last", "rsi_flat", "rsi_high", "vol_low", "atr_low", "short_daily"):
        k = rnd.uniform(-0.0195, 0.0195)
    else:
        return rows
    f = ema * (1 + k) / lo
    for b in rows:
        for x in ("o", "h", "l", "c"):
            b[x] = round(b[x] * f, 4)
    return rows


def _chain(rnd, sym, spot, today):
    grid = 0.5 if spot < 15 else (1.0 if spot < 40 else 2.5)
    dtes = sorted(rnd.sample((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 14), rnd.choice((1, 2, 2, 3, 3, 4))))
    hi = spot * rnd.choices((1.0, 1.03, 1.1, 1.25), (0.08, 0.12, 0.40, 0.40))[0]
    rows, quotes = [], {}
    for dte in dtes:
        exp = (today + timedelta(days=dte)).isoformat()
        k = max(grid, math.floor(spot * 0.85 / grid) * grid)
        while k <= hi:
            occ = _occ(sym, exp, k)
            rows.append({"symbol": occ, "expiration": exp, "strike": ("%g" % k), "type": "call", "multiplier": "100"})
            otm = (k - spot) / spot
            fair = max(0.01, spot * (0.012 + 0.004 * dte) * math.exp(-max(otm, 0) * 18) + max(spot - k, 0))
            u = rnd.random()
            if u < 0.05:
                k = round(k + grid, 4)
                continue                                       # no quote
            bid = round(fair * rnd.uniform(0.93, 0.99), 2)
            ask = round(max(bid + 0.01, fair * rnd.uniform(1.01, 1.07)), 2)
            if u < 0.10:
                bid = 0.0                                      # one-sided: the 15% gate is skipped
            elif u < 0.13:
                ask = 0.0                                      # no ask
            elif u < 0.25:
                ask = round(bid * rnd.uniform(1.17, 1.6) + 0.01, 2)   # wide
            quotes[occ] = {"bid": bid, "ask": ask}
            k = round(k + grid, 4)
    return rows, quotes


def _position(rnd, sym, today, last_close, quotes, chains):
    """a held call: an OCC on a 0-8 DTE expiry, its quote around its premium."""
    exp = (today + timedelta(days=rnd.randint(0, 8))).isoformat()
    k = round((last_close or rnd.uniform(5, 50)) * rnd.uniform(0.95, 1.1), 1)
    occ = _occ(sym, exp, k)
    fill = round(rnd.uniform(0.15, 2.5), rnd.choice((2, 2, 2, 3, 4)))
    prem = round(fill, 2)
    mid_target = prem * rnd.choice((0.3, 0.8, 1.2, 1.7, 1.75, 1.76, 1.9, 2.5))
    half = rnd.choice((0.005, 0.01, 0.02, 0.05))
    u = rnd.random()
    if u < 0.06:
        quotes.pop(occ, None)                                  # no quote
    else:
        bid, ask = round(max(0.0, mid_target - half), 2), round(mid_target + half, 2)
        if u < 0.12:
            bid = 0.0                                          # no bid: no close
        quotes[occ] = {"bid": bid, "ask": ask}
    ref = round(last_close * rnd.choice((0.96, 1.0, 1.02, 1.0305, 1.031, 1.05, 1.08)), 2) if last_close else \
        round(rnd.uniform(5, 50), 2)
    call = {"occ": occ, "strike": k, "expiry": exp, "ask": prem, "bid": max(0.01, prem - 0.05),
            "mid": prem, "ticker": sym}
    return occ, exp, k, fill, prem, ref, call


def _case(rnd, idx):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 300))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    hour = rnd.randint(9, 15)
    if today.isoformat() in ("2026-11-27", "2026-12-24") and hour >= 13:   # early closes
        hour = 12
    now = datetime(today.year, today.month, today.day, hour, 31, rnd.randint(0, 59), tzinfo=ET).timestamp()
    basket = rnd.sample(NAMES, rnd.randint(6, 12))
    held_names = rnd.sample(NAMES, rnd.choice((0, 0, 1, 1, 2, 3, 4, 5)))     # some held names are off the basket
    daily, h1, h1_rth, chains, quotes, modes = {}, {}, {}, {}, {}, {}
    for sym in [s for s in NAMES if s in basket or s in held_names]:
        mode = rnd.random()
        acc = 0.0
        for m, p in MODES:
            acc += p
            if mode < acc:
                mode = m
                break
        else:
            mode = "noise"
        modes[sym] = mode
        px = rnd.uniform(4, 70)
        vol = rnd.uniform(0.006, 0.012) if mode == "atr_low" else rnd.uniform(0.045, 0.09)
        n = rnd.randint(150, 199) if mode == "short_daily" else rnd.choice((230, 260, 260, 300))
        if mode != "no_daily":
            daily[sym] = _daily(rnd, today, n, px, vol)
        if mode == "no_h1":
            continue
        rows, rth = _h1(rnd, today, now, rnd.uniform(4, 70), mode)
        ema = None
        if sym in daily:
            ema = F.cap.calc_ema200([{"c": b["c"]} for b in daily[sym][-260:]])
        rows = _scale_to_ema(rnd, rows, rth, ema, mode)
        h1[sym] = rows
        h1_rth[sym] = [b for b in rows if 9 <= datetime.fromtimestamp(b["t"], tz=ET).hour <= 15]
        last = h1_rth[sym][-1]["c"] if h1_rth[sym] else rows[-1]["c"] if rows else None
        if last and rnd.random() < 0.93:
            rows_c, q = _chain(rnd, sym, last, today)
            chains[sym] = rows_c
            quotes.update(q)
    chain_fail = [s for s in chains if rnd.random() < 0.04]
    state = {"positions": {}, "awaiting_fills": {}, "closing": {}, "pending": {}}
    ss, orders, flat, entering, meta = {}, {}, [], [], {"kinds": {}}
    for sym in held_names:
        last = h1_rth[sym][-1]["c"] if h1_rth.get(sym) else None
        occ, exp, k, fill, prem, ref, call = _position(rnd, sym, today, last, quotes, chains)
        n = rnd.randint(1, 9)
        opened = now - rnd.randint(1, 6) * 86400
        kind = rnd.choices(("pos", "closing_working", "closing_dead", "closing_flat", "aw_working",
                            "aw_partial_working", "aw_filled", "aw_terminal_partial", "aw_dead"),
                           (0.40, 0.06, 0.12, 0.08, 0.08, 0.06, 0.08, 0.06, 0.06))[0]
        if n == 1 and kind in ("aw_partial_working", "aw_terminal_partial"):
            kind = "aw_working"                                 # one contract cannot be partly filled
        meta["kinds"][kind] = meta["kinds"].get(kind, 0) + 1
        port_pos = {"qty": n, "entry_px": fill, "occ": occ, "expiry": exp, "strike": k, "entry_stock_px": ref,
                    "opened_at": opened, "entry_date": datetime.fromtimestamp(opened, tz=ET).date().isoformat(),
                    "contracts": n, "ask": prem}
        old_pos = {"ticker": sym, "occ": occ, "strike": k, "expiry": exp, "qty": n, "entry_premium": prem,
                   "entry_stock_px": ref, "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat(),
                   "order_id": "e-%s" % sym, "cid": "c-%s" % sym}
        if kind == "pos":
            state["positions"][sym] = old_pos
            ss[sym] = {"position": port_pos}
        elif kind.startswith("closing"):
            oid = "x-%s" % sym
            orders[oid] = {"id": oid, "status": "accepted" if kind != "closing_dead" else
                           rnd.choice(("expired", "canceled", "rejected")), "filled_qty": "0", "symbol": occ,
                           "side": "sell", "qty": n}
            state["closing"][sym] = dict(old_pos, close_order_ids=[oid])
            if kind == "closing_working":
                ss[sym] = {"position": dict(port_pos, exit_submitted=True)}
            elif kind == "closing_dead":
                ss[sym] = {"position": port_pos}                # the exit child expired: held, no exit working
            else:
                flat.append(occ)                                # the close filled since the last run: gone
                meta.setdefault("flat_syms", []).append(sym)
                meta.setdefault("flat_pos", {})[sym] = dict(port_pos, exit_submitted=True)
        else:
            oid = "e-%s" % sym
            sub = datetime.fromtimestamp(now - rnd.randint(600, 30 * 3600), tz=timezone.utc).isoformat()
            state["awaiting_fills"][sym] = {"ticker": sym, "call": call, "qty": n, "cid": "c-%s" % sym,
                                            "order_id": oid, "ref_px": ref, "submitted_at": sub}
            part = rnd.randint(1, n - 1) if n > 1 else 1
            if kind == "aw_working":
                orders[oid] = {"id": oid, "status": "accepted", "filled_qty": "0", "filled_avg_price": None}
                ss[sym] = {"position": None, "pending_entry": {"qty": n, "filled": 0}}
                entering.append(sym)
            elif kind == "aw_partial_working":
                orders[oid] = {"id": oid, "status": "partially_filled", "filled_qty": str(part),
                               "filled_avg_price": str(fill)}
                ss[sym] = {"position": dict(port_pos, qty=part, contracts=part)}
                entering.append(sym)
            elif kind == "aw_filled":
                orders[oid] = {"id": oid, "status": "filled", "filled_qty": str(n), "filled_avg_price": str(fill)}
                ss[sym] = {"position": port_pos}
            elif kind == "aw_terminal_partial":
                orders[oid] = {"id": oid, "status": rnd.choice(("canceled", "expired")), "filled_qty": str(part),
                               "filled_avg_price": str(fill)}
                ss[sym] = {"position": dict(port_pos, qty=part, contracts=part)}
            else:
                orders[oid] = {"id": oid, "status": rnd.choice(("expired", "canceled", "rejected")),
                               "filled_qty": "0", "filled_avg_price": None}
    fear = rnd.random() < 0.85
    equity = rnd.choices((100_000.0, 1_000_000.0, 25_000.0, None, round(rnd.uniform(50_000, 400_000), 2)),
                         (0.45, 0.25, 0.05, 0.05, 0.20))[0]
    fill_now = [s for s in NAMES if rnd.random() < 0.75 and (s in basket or s in held_names)]
    return {"idx": idx, "now": now, "session": today.isoformat(), "basket": basket, "daily": daily, "h1": h1,
            "chains": chains, "quotes": quotes, "chain_fail": chain_fail, "state": state, "orders": orders,
            "flat_occs": flat, "fill_now": fill_now, "fear": fear, "equity": equity, "ss": ss, "entering": entering,
            "modes": modes, "meta": meta}


def _old_payload(c):
    """the old desk's shapes: daily bars dated YYYY-MM-DD, 1H bars stamped ISO Z, chain strikes as strings."""
    return {"now": c["now"], "basket": c["basket"], "equity": c["equity"], "fear": c["fear"],
            "daily": {s: [{"t": r["d"], **{k: r[k] for k in "ohlcv"}} for r in rows] for s, rows in c["daily"].items()},
            "h1": {s: [dict(b, t=_iso_z(b["t"])) for b in rows] for s, rows in c["h1"].items()},
            "chains": c["chains"], "quotes": c["quotes"], "chain_fail": c["chain_fail"], "state": c["state"],
            "orders": c["orders"], "fill_now": c["fill_now"], "flat_occs": c["flat_occs"]}


# ------------------------------------------------------------------------------------------------ the port's passes
def _view(c, ss, scan):
    universe = list(c["basket"]) + [s for s in ss if s not in c["basket"]]
    bars = {s: [{"t": datetime.fromisoformat(r["d"]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
                 **{k: r[k] for k in "ohlcv"}} for r in c["daily"][s]][-260:] for s in universe if s in c["daily"]}
    h1 = {s: _trim(c["h1"][s], c["now"], 15, True) for s in universe if s in c["h1"]}
    d0 = datetime.fromtimestamp(c["now"], tz=timezone.utc).date()   # OptionsData.chain's 0-7 DTE window
    chains = {}
    for s, rows in c["chains"].items():
        if s in c["chain_fail"]:
            continue
        chains[s] = [dict(r, strike=float(r["strike"]), bid=(c["quotes"].get(r["symbol"]) or {}).get("bid"),
                          ask=(c["quotes"].get(r["symbol"]) or {}).get("ask")) for r in rows
                     if 0 <= (date.fromisoformat(r["expiration"]) - d0).days <= 7]
    held = [st["position"]["occ"] for st in ss.values() if (st or {}).get("position")]
    oq = {o: dict(c["quotes"][o]) for o in held if o in c["quotes"]}
    close_at = cal.session_close(c["session"]) if cal.is_trading_day(c["session"]) else None
    extra = {"universe": universe, "bars_1h": h1, "chains": chains, "option_quotes": oq, "fear_ok": c["fear"],
             "session_close": close_at, "scan": scan, "entering": list(c["entering"]), "sleeve_state": ss}
    return bars, fc.Context(now=c["now"], session=c["session"], equity=c["equity"] or 0.0, extra=extra)


def _rows(intents, ss):
    buys, sells = [], []
    for i in intents:
        if i.kind == "enter":
            buys.append([i.legs[0]["symbol"], int(i.qty_hint), float(i.order["limit_price"])])
        else:
            occ = ss[i.symbol]["position"]["occ"]
            sells.append([occ, int(i.qty_hint), float(i.order["limit_price"]), i.reason.split(": ", 1)[1].split(" ")[0]])
    return buys, sells


def _port(c, ss=None):
    """pass 1 (the scan) and pass 2 (the reconcile echo, exits only) of the port on the case."""
    ss = copy.deepcopy(c["ss"] if ss is None else ss)
    bars, ctx = _view(c, ss, True)
    out1 = F.decide(bars, ctx)
    b1, s1 = _rows(out1, ss)
    ss2 = copy.deepcopy(ss)
    fill = set(c["fill_now"])
    entering = list(c["entering"])
    for i in out1:
        if i.kind == "exit":
            ss2[i.symbol]["position"]["exit_submitted"] = True
        elif i.symbol in fill:                                 # filled before the echo, at its limit
            pm = i.position_meta
            ss2[i.symbol] = {"position": dict(pm, qty=int(i.qty_hint), contracts=int(i.qty_hint),
                                              entry_px=float(i.order["limit_price"]), opened_at=c["now"],
                                              entry_date=c["session"])}
        else:
            ss2[i.symbol] = {"position": None, "pending_entry": {"qty": int(i.qty_hint), "filled": 0}}
            entering.append(i.symbol)
    c2 = dict(c, entering=entering)
    bars, ctx2 = _view(c2, ss2, False)
    out2 = F.decide(bars, ctx2)
    b2, s2 = _rows(out2, ss2)
    assert not b2, "the reconcile echo made an entry"
    return sorted(b1 + b2), sorted(s1 + s2), out1, len(s2)


def _first_failing_rule(c, out1):
    """coverage, not comparison: for each basket name the first entry rule that stopped it on the scan pass, in
    decide()'s order (fetch floors, held / in flight, the 5-call cap, part 5 then parts 4/1/2/3 of the signature,
    the fear gate, the selector's steps, the size) — checked against the port's own entries."""
    cap = F.cap
    ss = c["ss"]
    bars, ctx = _view(c, ss, True)
    h1map, chains = ctx.extra["bars_1h"], ctx.extra["chains"]
    entered = [i.symbol for i in out1 if i.kind == "enter"]
    live = sum(1 for st in ss.values() if (st or {}).get("position") or (st or {}).get("pending_entry"))
    out = {}
    for sym in ctx.extra["universe"]:
        daily, h1 = bars.get(sym) or [], h1map.get(sym) or []
        st = ss.get(sym) or {}
        if len(daily) < F.DAILY_MIN_BARS:
            why = "daily_floor"
        elif len(h1) < F.H1_MIN_BARS:
            why = "h1_floor"
        elif st.get("position") or st.get("pending_entry") or sym in c["entering"]:
            why = "held_or_in_flight"
        elif ctx.equity <= 0:
            why = "no_equity"
        elif live >= F.MAX_POSITIONS:
            why = "five_live"
        elif not cap.atr_filter_ok(daily):
            why = "atr_pct"
        else:
            rsi = cap.calc_rsi_1h([b["c"] for b in h1])
            vols = [b.get("v") or 0 for b in h1[-(cap.VOL_LOOKBACK + 2):-2]]
            avg = sum(vols) / len(vols) if vols else 0
            ema = cap.calc_ema200(daily)
            if not h1[-1]["c"] > h1[-1]["o"]:
                why = "last_bar_not_green"
            elif not rsi[-1] > rsi[-2]:
                why = "rsi_not_turning_up"
            elif not rsi[-2] < cap.RSI_OVERSOLD:
                why = "climax_rsi_not_below_20"
            elif avg <= 0 or h1[-2].get("v", 0) <= cap.VOL_CLIMAX_MULT * avg:
                why = "no_volume_climax"
            elif not ema or abs(h1[-2]["l"] - ema) / ema > cap.EMA_TOLERANCE:
                why = "climax_low_off_ema200"
            elif not c["fear"]:
                why = "fear_gate"
            else:
                why = _select_step(chains.get(sym), float(h1[-1]["c"]), c["session"], ctx.equity)
        if why == "entered":
            live += 1
        out[why] = out.get(why, 0) + 1
        if (why == "entered") != (sym in entered):
            raise AssertionError("coverage tally disagrees with the port on %s case %s: %s" % (sym, c["idx"], why))
    return out


def _select_step(rows, spot, session, equity):
    ref = date.fromisoformat(session)
    if rows is None:
        return "no_chain"
    win = [r for r in rows if F.DTE_MIN <= (date.fromisoformat(r["expiration"]) - ref).days <= F.DTE_MAX]
    if not win:
        return "no_expiry_0_7_dte"
    exp = min(r["expiration"] for r in win)
    sel = next((r for r in sorted((r for r in win if r["expiration"] == exp), key=lambda r: r["strike"])
                if r["strike"] >= spot * (1 + F.OTM_PCT)), None)
    if sel is None:
        return "no_strike_2pct_otm"
    ask, bid = F._px(sel, "ask"), F._px(sel, "bid")
    if ask <= 0:
        return "no_ask"
    if bid > 0 and (ask - bid) / ((ask + bid) / 2) > F.QUOTE_GATE_FRAC:
        return "spread_over_15pct"
    return "zero_contracts" if F.qty_for_risk(ask, equity) <= 0 else "entered"


def _dead_close_rule(c, sell):
    """the old rule for a dead close: re-fire at the then-bid (a quote and a bid), whatever the exit rules say —
    evaluated on the port's own view of that call."""
    occ = sell[0]
    st = next((st for st in c["ss"].values() if ((st or {}).get("position") or {}).get("occ") == occ), None)
    q = c["quotes"].get(occ)
    if st is None or q is None or F._px(q, "bid") <= 0:
        return None
    return [occ, int(st["position"]["qty"]), round(F._px(q, "bid"), 2), "close_retry_dead"]


CHUNK = 100


def _pairs(rnd, n):
    """(case, the old run's result) — one old-desk process per chunk of cases (bounded memory)."""
    for lo in range(0, n, CHUNK):
        cases = [_case(rnd, i) for i in range(lo, min(n, lo + CHUNK))]
        old = old_run(OLD, {"cases": [_old_payload(c) for c in cases]}, timeout=1800)
        yield from zip(cases, old)


def run():
    rnd = random.Random(1017)
    diffs, n_cases = [], 0
    stats = {"buys": 0, "sells": {}, "dead_close_refire": 0, "dead_close_same_order": 0, "slot_freed_on_fill": 0,
             "echo_sells": 0, "old_same_run_round_trips": 0, "cap_bound_cases": 0, "modes": {},
             "signals_by_mode": {}, "state_kinds": {}, "old_events": {}, "fear_closed_cases": 0,
             "no_equity_cases": 0, "entry_rule_stops": {}, "port_entries": 0, "slot_freed_extra_entries": 0}
    keep = ("capitulation_signal", "deferred_fear_gate", "entry_skipped_no_call", "entry_skipped_zero_qty",
            "entry_submitted", "exit_signal", "call_closed", "close_aborted_no_quote", "close_dead_retry",
            "close_pending", "close_already_working", "call_opened", "call_opened_partial", "entry_dead",
            "close_confirmed", "bars_failed")
    for c, o in _pairs(rnd, N_CASES):
        n_cases += 1
        stats["fear_closed_cases"] += 0 if c["fear"] else 1
        pb, ps, out1, n_echo = _port(c)
        stats["port_entries"] += len(pb)
        for k, v in _first_failing_rule(c, out1).items():
            stats["entry_rule_stops"][k] = stats["entry_rule_stops"].get(k, 0) + v
        ob, os_ = [list(x) for x in o["buys"]], [list(x) for x in o["sells"]]
        why = []
        # a close filled since the last run: the old still counted it in its entry loop (named) — the port's own
        # decision with that call held to the end of the pass (the old rule) must be the old's, buys and sells
        if c["meta"].get("flat_syms") and (pb != ob or ps != os_):
            ss = copy.deepcopy(c["ss"])
            ss.update({s: {"position": dict(p)} for s, p in c["meta"]["flat_pos"].items()})
            rb, rs, _o1, rn = _port(c, ss)
            if rb == ob and rb != pb:
                stats["slot_freed_on_fill"] += 1
                stats["slot_freed_extra_entries"] += len(pb) - len(rb)
                why.append("slot_freed_on_fill")
                pb, ps, n_echo = rb, rs, rn
        # a dead close: the old re-fired it at the then-bid whatever its exit rules said; the port decides it again
        for s in [x for x in os_ if x[3] == "close_retry_dead"]:
            same = next((p for p in ps if p[:3] == s[:3]), None)
            if same is not None:                               # the port's own exit rule sells the same order
                stats["dead_close_same_order"] += 1
                ps.remove(same)
                os_.remove(s)
            elif _dead_close_rule(c, s) == s:                  # the old rule on the port's view of that call
                stats["dead_close_refire"] += 1
                why.append("dead_close_refire")
                os_.remove(s)
        if pb != ob or ps != os_ or o["n_sell_orders"] != len(o["sells"]) or \
                any(x != "buy_to_open" for x in o["buy_intents"]) or any(x != "sell_to_close" for x in o["sell_intents"]):
            diffs.append({"idx": c["idx"], "session": c["session"], "now": c["now"], "old": [ob, os_],
                          "port": [pb, ps], "classified": why})
        stats["buys"] += len(o["buys"])
        for x in o["sells"]:
            stats["sells"][x[3]] = stats["sells"].get(x[3], 0) + 1
        stats["echo_sells"] += n_echo
        stats["old_same_run_round_trips"] += len({b[0] for b in o["buys"]} & {s[0] for s in o["sells"]})
        if c["equity"] in (None, 0.0):
            stats["no_equity_cases"] += 1
        for k, v in o["events"].items():
            if k in keep:
                stats["old_events"][k] = stats["old_events"].get(k, 0) + v
        for s in c["basket"]:
            stats["modes"][c["modes"][s]] = stats["modes"].get(c["modes"][s], 0) + 1
        for s in o["signals"]:
            stats["signals_by_mode"][c["modes"][s]] = stats["signals_by_mode"].get(c["modes"][s], 0) + 1
        for k, v in c["meta"]["kinds"].items():
            stats["state_kinds"][k] = stats["state_kinds"].get(k, 0) + v
        held = sum(1 for st in c["ss"].values() if (st or {}).get("position") or (st or {}).get("pending_entry"))
        if held + sum(1 for i in out1 if i.kind == "enter") >= F.MAX_POSITIONS:
            stats["cap_bound_cases"] += 1
    res = {"sleeve": "capitulation_options", "cases": n_cases, "identical": n_cases - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "method": "one old cron run (scan_pass then reconcile_pass; clock, equity, basket, bars, 1H fetches, chain/"
                     "quote/order/get-order/positions CLIs, state, ledgers and the removed gates stubbed) vs the port's "
                     "decide() scan pass and its exits-only reconcile echo on the same case"}
    write_receipt("capitulation_options", res)
    return res
