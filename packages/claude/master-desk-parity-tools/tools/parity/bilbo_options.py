"""bilbo_options: the old bilbo_options.py entry scan / exit sweep vs the restored port's decide() on the same case.

The OLD module runs its real passes: on a scan pass (:22-:26 of an hour 10-15 ET) the old "sweep" mode — run_entry
(_reconcile_pending_entries: fills promoted, partial fills cut to their filled contracts with the remainder cancelled,
stale entries cancelled; then per universe name fetch_5min('sip', 60 days) -> bos.detect_episodes / daily_rth, every
broke episode through seen_episodes, the 20-minute SIP cutoff, the staleness guard, the time gate, the EMA21 gate (both
marking the episode seen), option_chain over the entry date's 21-37 DTE window, select_expiry / target_strike, the
averaged three-snapshot gate3_spread_ok, size_contracts, max positions, the broker-held check, the buy at round(mid, 2))
then run_exit; on any other pass run_exit alone (both reconcilers; for pending exits the bounded cancel-replace at the
fresh mid and the manual-review stop after three; for open positions fetch_5min('iex'), the forming-bar drop, the
09:30-15:55 filter, bos.evaluate_exits, the sell at the mid on a two-sided quote). Stubbed: the clock (FakeDT), the
alpaca CLIs (bars, chain, quotes, orders, order lookups, cancels, positions — the case's), state load / save, the log,
time.sleep, and the gates the cutover removed (risk gate, drawdown brake, context gate, Decision #75 pre_buy ->
proceed and its release replay, the desk cap and its exposure ledger).

Bars are generated, not shipped: GEN (below) is executed identically on both sides from each case's seeds — a
mean-reverting extended-hours 5-minute walk with bursts, thinned pre-market; the scan pass is anchored on a natural
breakout of the case's primary name so the filters after the breakout fire. The SIP feed serves bars completed
16-18 minutes before the pass; the IEX feed 08:00-16:00 bars including the forming one.

Compared: the calls bought (contract, contracts, limit, and the episode levels stored for its exits), the new exits
(contract, contracts, limit, reason), each working exit's limit and size after the pass, the partial-fill entry
cancels, the seen episodes and the scan stamp. Named divergences counted, each verified against the port's own
decision under the old rule: gate 3 on one quote (the port re-run on the old's averaged snapshots must reproduce the
old exactly); the re-price past the old's three attempts (the old left the order at its stale limit; the port's new
limit must be the fresh mid); a contract whose entry is still working (the port re-run with only filled contracts
blocking reproduces the old's second buy); a filled exit the old had not reconciled (the port re-run with that slot
counted reproduces the old). The bar-cache ceiling is counted as a statistic: the port's decisions on the newest 5,000
SIP bars against its decisions on the old's 60-day window."""
import json
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("bilbo_options")
N_CASES = 1200
BATCH = 150
UNIVERSE = list(F.UNIVERSE)
CACHE_KEEP = 5000

GEN = r'''
import math as _m
import random as _r
from datetime import datetime as _dt
from zoneinfo import ZoneInfo as _Z
_ET = _Z("America/New_York")


def _t0(day):
    y, mo, d = (int(x) for x in day.split("-"))
    return _dt(y, mo, d, 4, 0, tzinfo=_ET).timestamp()


def gen_path(spec):
    """5-minute extended-hours bars [[t, o, h, l, c]] (t = bar start, 04:00-19:55 ET of each listed session): closes
    revert (kappa) to an anchor that random-walks (vol * avol, drift); an hour may burst (an anchor jump spread over
    the hour); wicks on every bar; early pre-market bars thinned (sparse); nothing after spec["end"]."""
    rnd = _r.Random(spec["seed"])
    px = anchor = spec["px"]
    vol, wick, drift, kappa, avol = spec["vol"], spec["wick"], spec["drift"], spec["kappa"], spec["avol"]
    pb, bmin, bmax, up = spec["burst_p"], spec["burst_min"], spec["burst_max"], spec["burst_up"]
    end, sparse, out = spec["end"], spec.get("sparse", 0.0), []
    jump = 0.0
    for day in spec["days"]:
        anchor *= _m.exp(rnd.gauss(0.0, vol * avol * 6))
        px *= _m.exp(rnd.gauss(0.0, vol * 2))
        base = _t0(day)
        for k in range(192):
            t = base + k * 300
            if t > end:
                return out
            if k % 12 == 0:
                jump = 0.0
                if rnd.random() < pb:
                    jump = (1 if rnd.random() < up else -1) * rnd.uniform(bmin, bmax) * vol / 12.0
            anchor *= _m.exp(drift + rnd.gauss(0.0, vol * avol) + jump)
            o = px
            c = o * _m.exp(rnd.gauss(0.0, vol) - kappa * _m.log(o / anchor) + jump)
            hi = max(o, c) * (1.0 + abs(rnd.gauss(0.0, wick)))
            lo = min(o, c) * (1.0 - abs(rnd.gauss(0.0, wick)))
            px = c
            if k < 36 and rnd.random() < sparse:
                continue
            o, hi, lo, c = round(o, 2), round(hi, 2), round(lo, 2), round(c, 2)
            out.append([t, o, max(hi, o, c), min(lo, o, c), c])
    return out
'''
_NS = {}
exec(GEN, _NS)
gen_path = _NS["gen_path"]

OLD = r'''
import sys, types, time as _time
from datetime import datetime as _dt, timezone, timedelta
from zoneinfo import ZoneInfo
exec(PAYLOAD["gen"])
import bilbo_options as O
import desk as _D
ET = ZoneInfo("America/New_York")
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O._HAS_RISK_GATE = True
O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda s, u: (True, []), blocked_reasons=lambda r: r)
_ddb = types.ModuleType("desk.drawdown_brake"); _ddb.check_drawdown = lambda: ("ok", "")
_cg = types.ModuleType("desk.context_gate"); _cg.check_and_log = lambda sym, sleeve: (True, "")
_d75 = types.ModuleType("desk.decision75"); _d75.pre_buy = lambda *a, **k: "proceed"
_d75.sweep_releases = lambda *a, **k: []
for _n, _mod in (("drawdown_brake", _ddb), ("context_gate", _cg), ("decision75", _d75)):
    sys.modules["desk." + _n] = _mod
    setattr(_D, _n, _mod)
O._replay_chart_gate_releases = lambda st: None
O._cap_gate_entry = lambda sym, n, e: True
O._dx_add = lambda *a, **k: None
O._dx_remove = lambda *a, **k: None
O.time = types.SimpleNamespace(sleep=lambda s: None, time=_time.time)
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
S = {}
def _arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
def _iso_z(t):
    return _dt.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def _hour(t):
    return _dt.fromtimestamp(t, tz=ET).hour
def _path(sym):
    if sym not in S["paths"]:
        S["paths"][sym] = gen_path(S["case"]["paths"][sym]["spec"])
    return S["paths"][sym]
def run_cli(name, *args):
    C = S["case"]
    args = [str(a) for a in args]
    if name == "alpaca_get_bars_5min.py":
        sym, feed = _arg(args, "--symbol"), _arg(args, "--feed")
        sp = C["paths"].get(sym)
        if sp is None or not sp.get(feed):
            return []
        if feed + "_error" in sp.get("flags", []):
            raise RuntimeError("alpaca_get_bars_5min.py failed: HTTP 500")
        st = _dt.strptime(_arg(args, "--start"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        now = C["now"]
        if feed == "sip":
            rows = [r for r in _path(sym) if r[0] >= st and r[0] + 300 <= now - C["sip_delay"]]
        else:
            rows = [r for r in _path(sym) if r[0] >= st and r[0] <= now and 8 <= _hour(r[0]) < 16]
        rows = rows[-int(_arg(args, "--limit")):]
        return [{"t": _iso_z(r[0]), "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": 1000} for r in rows]
    if name == "alpaca_option_chain.py":
        ch = C["chains"].get(_arg(args, "--underlying"))
        if ch == "error":
            raise RuntimeError("alpaca_option_chain.py failed: HTTP 500")
        lo, hi = _arg(args, "--expiry-gte"), _arg(args, "--expiry-lte")
        return [dict(r) for r in ch or [] if lo <= r["expiration"] <= hi]
    if name == "alpaca_option_quotes.py":
        out = {}
        for occ in _arg(args, "--symbols").split(","):
            snaps = C["snaps"].get(occ)
            if not snaps:
                continue
            i = S["count"].get(occ, 0)
            S["count"][occ] = i + 1
            s = snaps[i % len(snaps)]
            if s == "error":
                raise RuntimeError("alpaca_option_quotes.py failed: HTTP 429")
            if s is None:
                continue
            b, a = float(s[0]), float(s[1])
            mid = (b + a) / 2.0 if b > 0 and a > 0 else 0.0
            out[occ] = {"bid": b, "ask": a, "mid": round(mid, 4), "spread_frac": (a - b) / mid if mid > 0 else None}
        return out
    if name == "alpaca_option_order.py":
        S["orders"].append([_arg(args, "--symbol"), _arg(args, "--side"), int(_arg(args, "--qty")),
                            float(_arg(args, "--limit-price")), _arg(args, "--position-intent"),
                            _arg(args, "--client-order-id")])
        return {"id": "n%d" % len(S["orders"]), "status": "accepted"}
    if name == "alpaca_get_order.py":
        oid = _arg(args, "--order-id")
        o = C["order_status"].get(oid) or {"status": "new", "filled_qty": "0"}
        return dict(o, id=oid)
    if name == "alpaca_cancel_order.py":
        S["cancels"].append(_arg(args, "--order-id"))
        return {}
    if name == "alpaca_list_positions.py":
        return [dict(p) for p in C["broker"]]
    if name == "alpaca_list_orders.py":
        return []
    if name == "alpaca_get_account.py":
        return {"equity": str(C["equity"])}
    raise RuntimeError("unexpected CLI " + name)
O._run_cli = run_cli
KEEP = ("status", "qty", "exit_limit", "exit_attempts", "exit_reason", "entry_ts", "entry_spot", "box_hi", "box_lo",
        "datr14_prior", "entry_date", "entry_order_id")
out = []
for C in PAYLOAD["cases"]:
    S.update(case=C, paths={}, count={}, orders=[], cancels=[])
    EV.clear()
    FakeDT.NOW = _dt.fromtimestamp(C["now"], tz=timezone.utc)
    st = O._blank_state()
    st.update(json.loads(json.dumps(C["state"])))
    O.load_state = lambda st=st: st
    if C["entry_pass"]:
        O.run_entry(list(C["universe"]), C["equity"])
    S["count"] = {}
    O.run_exit(None)
    skips = {}
    for e in EV:
        if e.get("event") in ("entry_skipped", "entry_scan_nodata", "entry_scan_error"):
            k = str(e.get("reason") or e.get("event"))
            skips[k] = skips.get(k, 0) + 1
    out.append({"orders": S["orders"], "cancels": S["cancels"], "seen": list(st.get("seen_episodes") or []),
                "last_scan": st.get("last_entry_scan"), "skips": skips,
                "positions": {o: {k: p.get(k) for k in KEEP} for o, p in (st.get("positions") or {}).items()}})
print(json.dumps(out))
'''


# ------------------------------------------------------------------ helpers
def _iso(t):
    return datetime.fromtimestamp(float(t), tz=timezone.utc).astimezone(ET).isoformat()


def _et(d, hh, mm=0, ss=0):
    return datetime(d.year, d.month, d.day, hh, mm, ss, tzinfo=ET).timestamp()


def _sessions(d0, d1):
    out, d = [], d0
    while d <= d1:
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _bar(r):
    return {"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": 1000.0}


def _hour(t):
    return datetime.fromtimestamp(float(t), tz=timezone.utc).astimezone(ET).hour


def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _strike_str(k):
    return ("%.3f" % k).rstrip("0").rstrip(".")


def _grid(px):
    return 0.5 if px < 25 else (1.0 if px < 100 else (2.5 if px < 250 else 5.0))


def _spec(rnd, sym, days, end, px=None):
    vol = rnd.uniform(0.0006, 0.0022)
    return {"seed": rnd.randint(0, 10 ** 9), "days": [d.isoformat() for d in days], "end": end,
            "px": round(px or rnd.uniform(15, 450), 2), "vol": vol, "wick": vol * rnd.uniform(0.6, 1.6),
            "drift": rnd.uniform(-0.00003, 0.00005), "kappa": rnd.choice((0.03, 0.06, 0.1)),
            "avol": rnd.uniform(0.2, 0.6), "burst_p": rnd.uniform(0.03, 0.08), "burst_min": 4, "burst_max": 22,
            "burst_up": rnd.uniform(0.55, 0.85), "sparse": rnd.choice((0.0, 0.05, 0.2))}


def _scan_time(d, hh, rnd):
    return _et(d, hh, rnd.randint(22, 26), rnd.randint(0, 59))


def _prev_scan(now, rnd):
    """the previous hourly scan before `now` (:22-:26 of an hour 10-15 ET on a trading day)."""
    t = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(ET)
    d, hh = t.date(), t.hour - 1
    while True:
        if hh < 10 or not cal.is_trading_day(d):
            d = cal.prev_trading_day(d)
            hh = 15
            continue
        if hh > 15:
            hh = 15
            continue
        return _scan_time(d, hh, rnd)


def _snapshots(rnd, fair):
    """three indicative snapshots for a contract: clean / wide / boundary / noisy / one-sided / missing / erroring."""
    mid = max(0.05, round(fair, 2))
    u = rnd.random()

    def q(m, f):
        b = round(m * (1 - f / 2), 2)
        a = round(max(b + 0.01, m * (1 + f / 2)), 2)
        return [b, a]
    if u < 0.55:
        s = q(mid, rnd.uniform(0.004, 0.049))
        return [s, list(s), list(s)]
    if u < 0.65:
        s = q(mid, rnd.uniform(0.051, 0.14))
        return [s, list(s), list(s)]
    if u < 0.70:                                          # exactly 5% of mid in decimal
        m = round(rnd.choice((1.0, 2.0, 4.0, 6.0, 8.0, 10.0)), 2)
        s = [round(m - m * 0.025, 2), round(m + m * 0.025, 2)]
        return [s, list(s), list(s)]
    if u < 0.82:                                          # snapshot noise (the old averaged it)
        f = rnd.uniform(0.01, 0.07)
        return [q(round(mid + rnd.choice((-1, 0, 1)) * rnd.randint(0, 6) * 0.01, 2) or mid, f + rnd.uniform(-0.01, 0.01))
                for _ in range(3)]
    if u < 0.88:                                          # one-sided on some snapshots
        s = q(mid, rnd.uniform(0.004, 0.045))
        return [[0.0, s[1]] if rnd.random() < 0.6 else list(s) for _ in range(3)]
    if u < 0.93:                                          # missing on some snapshots
        s = q(mid, rnd.uniform(0.004, 0.045))
        return [None if rnd.random() < 0.6 else list(s) for _ in range(3)]
    s = q(mid, rnd.uniform(0.004, 0.045))                 # fetch errors
    return ["error" if rnd.random() < 0.7 else list(s) for _ in range(3)]


def _chain(rnd, sym, spot, today):
    """weekly (or monthly-only, or out-of-window) call expiries 14-45 days out, strikes on the price's grid."""
    if rnd.random() < 0.04:
        return "error"
    if rnd.random() < 0.03:
        return []
    fridays = [today + timedelta(days=i) for i in range(14, 46) if (today + timedelta(days=i)).weekday() == 4]
    u = rnd.random()
    if u < 0.12:
        fridays = [d for d in fridays if 15 <= d.day <= 21] or fridays[:1]
    elif u < 0.18:
        fridays = [d for d in fridays if (d - today).days < 21 or (d - today).days > 40] or fridays[:1]
    g = _grid(spot)
    lo, hi = round(spot * 0.85 / g) * g, round(spot * 1.25 / g) * g
    rows = []
    for d in fridays:
        exp = d.isoformat()
        k = lo
        while k <= hi + 1e-9:
            rows.append({"symbol": _occ(sym, exp, k), "expiration": exp, "strike": _strike_str(k), "type": "call",
                         "multiplier": "100"})
            k = round(k + g, 4)
    return rows


def _fair(spot, k, dte):
    return max(0.05, max(0.0, spot - k) + 0.4 * spot * (max(dte, 1) / 365.0) ** 0.5 * 0.45)


# ------------------------------------------------------------------ the case
def _case(rnd, idx):
    D = date(2026, 2, 3) + timedelta(days=rnd.randint(0, 225))
    while not cal.is_trading_day(D):
        D += timedelta(days=1)
    entry_pass = rnd.random() < 0.68
    hist_days = _sessions(D - timedelta(days=rnd.choice((74, 74, 66, 50, 40))), D)
    end_of_d = _et(D, 20, 0)
    paths, chains, snaps = {}, {}, {}
    syms = rnd.sample(UNIVERSE, rnd.randint(1, 3))
    primary = syms[0]
    now = None
    scenario = "random"
    target = None
    if entry_pass:
        want_window = rnd.random() < 0.8                  # mostly a breakout whose close lands 10:00-15:00 ET
        for k in range(6):                                # anchor the pass on a natural breakout of the primary name
            spec = _spec(rnd, primary, hist_days, end_of_d)
            path = gen_path(spec)
            df = F.frame([_bar(r) for r in path])
            eps = [e for e in F.bos.detect_episodes(df) if e["broke"]]
            lim = _et(hist_days[-8] if len(hist_days) > 8 else hist_days[0], 0)
            eps = [e for e in eps if F._epoch(e["entry_ts"]) >= lim]
            inw = [e for e in eps if F.bos.time_gate_ok(e["entry_ts"])]
            if want_window and inw:
                target = rnd.choice(inw)
                break
            if eps and (not want_window or k == 5):
                target = rnd.choice(eps)
                break
        paths[primary] = {"spec": spec, "sip": True, "iex": True, "flags": []}
    else:
        paths[primary] = {"spec": _spec(rnd, primary, hist_days, end_of_d), "sip": True, "iex": True, "flags": []}
    if entry_pass and target is not None:
        T = F._epoch(target["entry_ts"])
        td = datetime.fromtimestamp(T, tz=timezone.utc).astimezone(ET)
        first = None                                      # the first scan whose cutoff reaches T
        d, hh = td.date(), td.hour
        while first is None:
            if cal.is_trading_day(d) and 10 <= hh <= 15:
                cand = _et(d, hh, 22)
                if cand - 1200 >= T:
                    first = cand
            hh += 1
            if hh > 15:
                d, hh = d + timedelta(days=1), 10
        fd = datetime.fromtimestamp(first, tz=timezone.utc).astimezone(ET)
        u = rnd.random()
        early = datetime.fromtimestamp(T - 3600, tz=timezone.utc).astimezone(ET)
        if u < 0.08 and cal.is_trading_day(early.date()) and 10 <= early.hour <= 15:
            scenario = "early"                            # the scan inside the breakout's own hour (the SIP lag)
            now = _scan_time(early.date(), early.hour, rnd)
            last = _prev_scan(now, rnd)
        elif u < 0.62:
            scenario = "fresh"
            now = _scan_time(fd.date(), fd.hour, rnd)
            last = _prev_scan(now, rnd) if rnd.random() < 0.88 else None
        elif u < 0.78:
            scenario = "retry"                            # a later scan: the earlier ones skipped it without marking
            now = first
            for _ in range(rnd.randint(1, 3)):
                n2 = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(ET)
                d, hh = n2.date(), n2.hour + 1
                while not (cal.is_trading_day(d) and 10 <= hh <= 15):
                    hh += 1
                    if hh > 15:
                        d, hh = d + timedelta(days=1), 10
                now = _et(d, hh, 22)
            nd = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(ET)
            now = _scan_time(nd.date(), nd.hour, rnd)
            last = _prev_scan(now, rnd)
        else:
            scenario = "late"                             # stale by the previous scan, or a first scan's 24 hours
            n2 = first + 3600 * rnd.randint(2, 30)
            nd = datetime.fromtimestamp(n2, tz=timezone.utc).astimezone(ET)
            d, hh = nd.date(), nd.hour
            while not (cal.is_trading_day(d) and 10 <= hh <= 15):
                hh += 1
                if hh > 15:
                    d, hh = d + timedelta(days=1), 10
            now = _scan_time(d, hh, rnd)
            last = None if rnd.random() < 0.3 else _prev_scan(now, rnd)
        D2 = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(ET).date()
        if D2 > D:                                        # the scan falls on a later session: extend the walk
            spec = dict(paths[primary]["spec"])
            spec["days"] = spec["days"] + [x.isoformat() for x in _sessions(D + timedelta(days=1), D2)]
            spec["end"] = _et(D2, 20, 0)
            paths[primary]["spec"] = spec
        D = D2
    elif entry_pass:
        now = _scan_time(D, rnd.randint(10, 15), rnd)
        last = None if rnd.random() < 0.15 else _prev_scan(now, rnd)
    else:
        now = _et(D, 9, 30) + rnd.randint(0, 389) * 60 + rnd.randint(1, 59)
        t = datetime.fromtimestamp(now, tz=timezone.utc).astimezone(ET)
        if 10 <= t.hour <= 15 and t.minute >= 22:         # this hour's scan already ran
            mark = _et(D, t.hour, 22)
            last = mark + rnd.uniform(0, now - mark)
        else:
            last = _prev_scan(now, rnd)
    session = D.isoformat()
    for s in syms[1:]:
        paths[s] = {"spec": _spec(rnd, s, _sessions(D - timedelta(days=rnd.choice((74, 66, 45))), D), _et(D, 20, 0)),
                    "sip": True, "iex": True, "flags": []}
    for s, p in paths.items():
        p["spec"]["end"] = min(p["spec"]["end"], now + 600)
        if rnd.random() < 0.04:
            p["flags"].append("sip_error")
        if rnd.random() < 0.03:
            p["flags"].append("iex_error")
    sip_delay = rnd.choice((960, 1020, 1080))
    P = {s: gen_path(p["spec"]) for s, p in paths.items()}
    meta_seen = []
    # the chains, and the snapshots of the contracts the fresh episodes resolve to
    fresh_after = (last - 7200) if last is not None else now - 86400
    for s in list(paths):
        rows = P[s]
        sipb = [_bar(r) for r in rows if r[0] + 300 <= now - sip_delay]
        if not sipb:
            continue
        spot = sipb[-1]["c"]
        ch = _chain(rnd, s, spot, D)
        chains[s] = ch
        hist = F.history(sipb, now)
        if len(hist) < 100:
            continue
        df = F.frame(hist)
        eps = F.bos.detect_episodes(df)
        for e in eps:
            if e["broke"] and rnd.random() < 0.05:
                meta_seen.append(F.episode_key(s, e))
        if not isinstance(ch, list):
            continue
        for e in eps:
            if not e["broke"] or F._epoch(e["entry_ts"]) <= fresh_after - 3600:
                continue
            got = F.contract_for(e, [dict(r, strike=float(r["strike"])) for r in ch])
            if got is None:
                continue
            row, expiry, strike = got
            dte = (date.fromisoformat(expiry) - D).days
            snaps[row["symbol"]] = _snapshots(rnd, _fair(e["spot"], strike, dte))
            if rnd.random() < 0.08:
                meta_seen.append(F.episode_key(s, e))
    # the book: held calls, working exits, entries in flight
    state = {"positions": {}, "seen_episodes": [], "submitted_orders": {}}
    order_status, broker, port_held, port_orders, kinds = {}, [], {}, [], {}
    n_book = rnd.choice((0, 0, 1, 1, 2, 2, 3, 4, 5, 6))
    for j in range(n_book):
        if rnd.random() < 0.5 and paths:
            und = rnd.choice(list(paths))
        else:
            und = rnd.choice(UNIVERSE)
            if und not in paths:
                paths[und] = {"spec": _spec(rnd, und, _sessions(D - timedelta(days=30), D), min(_et(D, 20, 0), now + 600)),
                              "sip": rnd.random() < 0.5, "iex": rnd.random() < 0.95, "flags": []}
                P[und] = gen_path(paths[und]["spec"])
        rows = [r for r in P[und] if r[0] + 300 <= now]
        sess = sorted({datetime.fromtimestamp(r[0], tz=timezone.utc).astimezone(ET).date() for r in rows
                       if 10 <= _hour(r[0]) <= 15})
        if not sess:
            continue
        kind = rnd.choices(("open", "pending_exit", "partial_entry", "filled_entry", "exit_filled", "pending", "dead"),
                           (46, 22, 6, 7, 7, 9, 3))[0]
        back = rnd.randint(0, min(13, len(sess) - 1)) if kind not in ("pending", "partial_entry") else 0
        ed = sess[-1 - back]
        hh = rnd.randint(10, 15)
        T = _et(ed, hh)
        if T + 1500 > now:
            T = max(r[0] for r in rows if r[0] + 300 <= now) - 3600 * 2
            T = T - (T % 3600)
        before = [r for r in rows if r[0] < T]
        if not before:
            continue
        espot = before[-1][4]
        datr = round(espot * rnd.uniform(0.006, 0.04), 4)
        box_lo = round(espot * (1 - rnd.uniform(0.001, 0.05)), 2)
        exp = (D + timedelta(days=rnd.choice((1, 3, 5, 6, 8, 12, 20, 30, 40)))).isoformat()
        occ = _occ(und, exp, round(espot * 1.02 / _grid(espot)) * _grid(espot))
        if occ in state["positions"] or occ in port_held:
            continue
        qty = rnd.randint(1, 15)
        sig = datetime.fromtimestamp(T, tz=timezone.utc).astimezone(ET).date().isoformat()
        rec = {"underlying": und, "occ": occ, "qty": qty, "entry_ts": _iso(T), "entry_spot": espot,
               "entry_premium_mid": 2.0, "box_hi": round(espot * 0.999, 2), "box_lo": box_lo, "datr14_prior": datr,
               "entry_date": sig, "client_order_id": "femto-bilboopt-x", "status": "open", "entry_order_id": None,
               "pending_since": None}
        pmeta = {"entry_ts": rec["entry_ts"], "entry_spot": espot, "box_hi": rec["box_hi"], "box_lo": box_lo,
                 "datr14_prior": datr, "signal_date": sig, "underlying": und}
        mid0 = max(0.1, round(rnd.uniform(0.3, 9.0), 2))
        u = rnd.random()
        if u < 0.84:
            s0 = [round(mid0 - rnd.choice((0.01, 0.02, 0.05, 0.1)), 2), round(mid0 + rnd.choice((0.01, 0.02, 0.05)), 2)]
        elif u < 0.91:
            s0 = [0.0, mid0]
        elif u < 0.96:
            s0 = None
        else:
            s0 = "error"
        snaps.setdefault(occ, [s0, s0, s0])
        key = "%s|%s" % (und, _iso(T - 3600 * rnd.randint(2, 9)))
        pos = dict(pmeta, qty=qty, occ=occ, contracts=qty, entry_px=mid0, entry_date=sig, opened_at=T + 1400)
        kinds[occ] = kind
        if kind == "open":
            state["positions"][occ] = rec
            broker.append({"symbol": occ, "qty": str(qty)})
            port_held[occ] = pos
        elif kind == "pending_exit":
            filled = rnd.randint(1, qty - 1) if (qty > 1 and rnd.random() < 0.25) else 0
            cur = round((s0[0] + s0[1]) / 2.0, 2) if isinstance(s0, list) and s0[0] > 0 else mid0
            l0 = cur if rnd.random() < 0.45 else round(max(0.05, cur + rnd.choice((-1, 1)) * rnd.randint(1, 30) * 0.01), 2)
            oid = "ox%d" % j
            state["positions"][occ] = dict(rec, status="pending_exit", exit_order_id=oid,
                                           exit_attempts=rnd.choice((0, 0, 1, 2, 3, 3, 4)), exit_limit=l0,
                                           exit_reason="box_low", exit_ts=_iso(now - 600), exit_cid="femto-bilboopt-x")
            order_status[oid] = {"status": "partially_filled" if filled else rnd.choice(("new", "accepted")),
                                 "filled_qty": str(filled)}
            broker.append({"symbol": occ, "qty": str(qty - filled)})
            port_held[occ] = dict(pos, qty=qty - filled, contracts=qty - filled, exit_submitted=True)
            port_orders.append({"inst": "OPT:" + occ, "side": "sell", "action": "exit", "vqty": float(qty),
                                "filled_v": float(filled), "signal_key": F.exit_key(occ, session, l0), "ref": None})
        elif kind in ("partial_entry", "filled_entry", "pending", "dead"):
            oid = "oe%d" % j
            age = rnd.uniform(1, 55) if kind in ("partial_entry", "pending") else rnd.uniform(1, 120)
            if kind == "pending" and rnd.random() < 0.3:
                age = rnd.uniform(61, 200)
            state["positions"][occ] = dict(rec, status="pending_entry", entry_order_id=oid,
                                           pending_since=_iso(now - age * 60))
            if kind == "partial_entry":
                k = rnd.randint(1, max(1, qty - 1)) if qty > 1 else 1
                order_status[oid] = {"status": "partially_filled", "filled_qty": str(k)}
                if k < qty:
                    port_orders.append({"inst": "OPT:" + occ, "side": "buy", "action": "enter", "vqty": float(qty),
                                        "filled_v": float(k), "signal_key": key, "ref": None})
                broker.append({"symbol": occ, "qty": str(k)})
                port_held[occ] = dict(pos, qty=k, contracts=k)
                kinds[occ] = "partial_entry" if k < qty else "filled_entry"
            elif kind == "filled_entry":
                order_status[oid] = {"status": "filled", "filled_qty": str(qty)}
                broker.append({"symbol": occ, "qty": str(qty)})
                port_held[occ] = pos
            elif kind == "pending":
                order_status[oid] = {"status": rnd.choice(("new", "accepted")), "filled_qty": "0"}
                if age < 60:
                    port_orders.append({"inst": "OPT:" + occ, "side": "buy", "action": "enter", "vqty": float(qty),
                                        "filled_v": 0.0, "signal_key": key, "ref": None})
            else:
                order_status[oid] = {"status": rnd.choice(("canceled", "rejected", "expired")), "filled_qty": "0"}
        elif kind == "exit_filled":
            oid = "ox%d" % j
            state["positions"][occ] = dict(rec, status="pending_exit", exit_order_id=oid, exit_attempts=0,
                                           exit_limit=mid0, exit_reason="giveback", exit_ts=_iso(now - 900))
            order_status[oid] = {"status": "filled", "filled_qty": str(qty)}
    # a fresh episode's contract already in flight from another episode (the old bought it again)
    for occ in list(snaps):
        und = occ[:-15]
        if und in paths and occ not in state["positions"] and rnd.random() < 0.10 and isinstance(snaps[occ], list):
            oid = "od%d" % len(state["positions"])
            qty = rnd.randint(1, 6)
            T = now - 3600 * 2
            T -= T % 3600
            state["positions"][occ] = {"underlying": und, "occ": occ, "qty": qty, "entry_ts": _iso(T),
                                       "entry_spot": 100.0, "entry_premium_mid": 1.0, "box_hi": 99.0, "box_lo": 98.0,
                                       "datr14_prior": 2.0, "entry_date": _iso(T)[:10], "client_order_id": "x",
                                       "status": "pending_entry", "entry_order_id": oid,
                                       "pending_since": _iso(now - 600)}
            order_status[oid] = {"status": "new", "filled_qty": "0"}
            port_orders.append({"inst": "OPT:" + occ, "side": "buy", "action": "enter", "vqty": float(qty),
                                "filled_v": 0.0, "signal_key": "%s|%s" % (und, _iso(T - 7200)), "ref": None})
            kinds[occ] = "in_flight"
    state["seen_episodes"] = list(dict.fromkeys(meta_seen))
    if last is not None:
        state["last_entry_scan"] = datetime.fromtimestamp(last, tz=timezone.utc).isoformat()
    equity = rnd.choice((rnd.uniform(4_000, 40_000), rnd.uniform(40_000, 400_000), rnd.uniform(400_000, 3_000_000)))
    return {"idx": idx, "now": now, "session": session, "entry_pass": entry_pass, "scenario": scenario,
            "universe": list(UNIVERSE), "paths": paths, "chains": chains, "snaps": snaps, "state": state,
            "order_status": order_status, "broker": broker, "equity": equity, "sip_delay": sip_delay,
            "last": last, "port_held": port_held, "port_orders": port_orders, "kinds": kinds}


# ------------------------------------------------------------------ the port
def _quote(c, occ, avg=False):
    snaps = c["snaps"].get(occ)
    if not snaps:
        return {"bid": None, "ask": None}
    if not avg:
        s = snaps[0]
        return {"bid": s[0], "ask": s[1]} if isinstance(s, list) else {"bid": None, "ask": None}
    ok = [s for s in snaps if isinstance(s, list) and s[0] > 0 and s[1] > 0 and s[1] >= s[0]]
    if not ok:
        return {"bid": None, "ask": None}
    return {"bid": sum(s[0] for s in ok) / len(ok), "ask": sum(s[1] for s in ok) / len(ok)}


def _extra(c, P, cap=None, avg=False):
    now = c["now"]
    sip, rth = {}, {}
    for s, p in c["paths"].items():
        fl = p.get("flags") or []
        if p.get("sip") and "sip_error" not in fl:
            bl = [_bar(r) for r in P[s] if r[0] + 300 <= now - c["sip_delay"]]
            sip[s] = bl[-cap:] if cap else bl
        if p.get("iex") and "iex_error" not in fl:
            rth[s] = [_bar(r) for r in P[s] if r[0] + 300 <= now and 8 <= _hour(r[0]) < 16]
    d = date.fromisoformat(c["session"])
    lo, hi = d.isoformat(), (d + timedelta(days=60)).isoformat()
    chains = {}
    for s, ch in c["chains"].items():
        if ch == "error":
            continue
        chains[s] = [dict({"symbol": r["symbol"], "strike": float(r["strike"]), "expiration": r["expiration"],
                           "type": "call"}, **_quote(c, r["symbol"], avg)) for r in ch if lo <= r["expiration"] <= hi]
    ss = {o: {"position": dict(p)} for o, p in c["port_held"].items()}
    for o in c["port_orders"]:
        if o["action"] == "enter":
            st = ss.setdefault(o["inst"][4:-15], {})
            st.setdefault("position", None)
            st["pending_entry"] = {"qty": o["vqty"], "filled": o["filled_v"], "key": o["signal_key"], "ref_px": None}
    oq = {}
    for o in c["port_held"]:
        q = _quote(c, o)
        if q["bid"] is not None:
            oq[o] = q
    meta = {"seen_episodes": list(c["state"]["seen_episodes"])}
    if c["last"] is not None:
        meta["last_entry_scan"] = c["last"]
    return {"universe": list(c["universe"]), "meta": meta, "bars_5m": sip, "bars_rth": rth, "chains": chains,
            "option_quotes": oq, "orders": [dict(o) for o in c["port_orders"]], "sleeve_state": ss,
            "session_close": cal.session_close(c["session"])}


def _ctx(c, extra):
    return fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)


ENTRY_META = ("entry_ts", "entry_spot", "box_hi", "box_lo", "datr14_prior")


def _entries(intents):
    return [[i.symbol, int(i.qty_hint), round(float(i.order["limit_price"]), 2)]
            + [i.position_meta[k] for k in ENTRY_META] + [i.position_meta["signal_date"]]
            for i in intents if i.kind == "enter"]


def _port(c, P, cap=None):
    extra = _extra(c, P, cap=cap)
    ctx = _ctx(c, extra)
    intents, upd = F.decide({}, ctx)
    exits = {}
    for i in intents:
        if i.kind == "exit":
            exits[i.symbol] = [int(i.qty_hint), round(float(i.order["limit_price"]), 2),
                               i.reason.split(": ", 1)[1].split(" ")[0]]
    cancels = sorted(i.symbol for i in intents if i.kind == "cancel" and "partial fill" in i.reason)
    return {"entries": _entries(intents), "exits": exits, "cancels": cancels,
            "seen": (upd or {}).get("seen_episodes"), "last_scan": (upd or {}).get("last_entry_scan"),
            "intents": intents}


def _scan(c, P, avg=False, old_block=False, old_count=False, trace=None):
    """the port's scan under (parts of) the old rule: gate 3 on the old's averaged snapshots, only filled contracts
    blocking a buy, an exit fill the old had not reconciled still holding its slot."""
    extra = _extra(c, P, avg=avg)
    held, entering, exiting = F.book(extra)
    occupied = set(held) | set(entering)
    blocked = set(occupied)
    if old_block:
        blocked = {o for o, k in c["kinds"].items() if k in ("open", "pending_exit", "partial_entry", "filled_entry")}
    if old_count:
        occupied |= {o for o, k in c["kinds"].items() if k == "exit_filled"}
    meta = extra["meta"]
    intents, upd = F.scan(_ctx(c, extra), extra, meta, occupied, blocked=blocked, trace=trace)
    return _entries(intents), upd["seen_episodes"]


def _old_view(c, o):
    pos = o["positions"]
    entries, exits, reprices = [], {}, {}
    for occ, side, qty, px, intent, cid in o["orders"]:
        if side == "buy":
            r = pos.get(occ) or {}
            entries.append([occ, qty, px] + [r.get(k) for k in ENTRY_META] + [r.get("entry_date")])
        elif "-xr" in cid:
            reprices[occ] = [qty, px]
        else:
            exits[occ] = [qty, px, (pos.get(occ) or {}).get("exit_reason")]
    ids = {}
    for occ, r in c["state"]["positions"].items():
        if r.get("entry_order_id"):
            ids[r["entry_order_id"]] = occ
    cancels = sorted(ids[i] for i in o["cancels"] if i in ids and c["kinds"].get(ids[i]) == "partial_entry")
    last = o["last_scan"]
    return {"entries": entries, "exits": exits, "reprices": reprices, "cancels": cancels, "seen": o["seen"],
            "last_scan": datetime.fromisoformat(last).timestamp() if last else None}


def run():
    rnd = random.Random(1022)
    cases = [_case(rnd, i) for i in range(N_CASES)]
    olds = []
    for b in range(0, len(cases), BATCH):
        part = [{k: v for k, v in c.items() if k not in ("port_held", "port_orders", "kinds", "last", "scenario")}
                for c in cases[b:b + BATCH]]
        olds += old_run(OLD, {"gen": GEN, "cases": part}, timeout=3600)
    diffs = []
    stats = {"entry_passes": 0, "exit_only_passes": 0, "entries": 0, "contracts_bought": 0, "oversize": 0,
             "exits": {}, "reprices": 0, "kept_working": 0, "partial_entry_cancels": 0,
             "scan_filters": {}, "old_skip_events": {}, "scenarios": {},
             "divergence_gate3_one_quote": 0, "divergence_reprice_past_three": 0,
             "divergence_inflight_contract": 0, "divergence_unreconciled_exit_fill": 0,
             "cache_window_5000_cases": 0, "cache_window_5000_differing": 0}
    for c, o in zip(cases, olds):
        P = {s: gen_path(p["spec"]) for s, p in c["paths"].items()}
        if F.entry_due(c["now"], {"last_entry_scan": c["last"]}) != c["entry_pass"]:
            raise SystemExit("case %d: pass kind and the port's scan clock disagree" % c["idx"])
        p = _port(c, P)
        ov = _old_view(c, o)
        labels, bad = [], []
        stats["scenarios"][c["scenario"]] = stats["scenarios"].get(c["scenario"], 0) + 1
        # entries and the seen episodes (scan passes)
        if c["entry_pass"]:
            stats["entry_passes"] += 1
            tr = {}
            _scan(c, P, trace=tr)
            for k, v in tr.items():
                stats["scan_filters"][k] = stats["scan_filters"].get(k, 0) + v
            if p["entries"] != ov["entries"] or p["seen"] != ov["seen"]:
                hit = None
                for combo in ((True, False, False), (False, True, False), (False, False, True), (True, True, False),
                              (True, False, True), (False, True, True), (True, True, True)):
                    e2, s2 = _scan(c, P, avg=combo[0], old_block=combo[1], old_count=combo[2])
                    if e2 == ov["entries"] and s2 == ov["seen"]:
                        hit = combo
                        break
                if hit is None:
                    bad.append("entries")
                else:
                    for flag, name in zip(hit, ("divergence_gate3_one_quote", "divergence_inflight_contract",
                                                "divergence_unreconciled_exit_fill")):
                        if flag:
                            stats[name] += 1
                            labels.append(name)
            if p["last_scan"] != c["now"] or ov["last_scan"] is None or abs(ov["last_scan"] - c["now"]) > 1e-6:
                bad.append("last_scan")
            capped = _port(c, P, cap=CACHE_KEEP)
            sip_long = any(len([r for r in P[s] if r[0] + 300 <= c["now"] - c["sip_delay"]]) > CACHE_KEEP
                           for s, q in c["paths"].items() if q.get("sip"))
            if sip_long:
                stats["cache_window_5000_cases"] += 1
                if capped["entries"] != p["entries"]:
                    stats["cache_window_5000_differing"] += 1
        else:
            stats["exit_only_passes"] += 1
            if p["entries"] or ov["entries"] or p["seen"] is not None:
                bad.append("entries_outside_scan")
        for k, v in o["skips"].items():
            stats["old_skip_events"][k] = stats["old_skip_events"].get(k, 0) + v
        # new exits on positions without a working exit
        working = {occ for occ, k in c["kinds"].items() if k == "pending_exit"}
        pe = {k: v for k, v in p["exits"].items() if k not in working}
        if pe != ov["exits"]:
            bad.append("exits")
        # each working exit's limit and size after the pass
        for occ in working:
            rec = c["state"]["positions"][occ]
            held_q = c["port_held"][occ]["qty"]
            port_after = p["exits"][occ][:2] if occ in p["exits"] else [held_q, rec["exit_limit"]]
            old_after = ov["reprices"].get(occ) or [held_q, rec["exit_limit"]]
            if port_after == old_after:
                if occ in p["exits"]:
                    stats["reprices"] += 1
                else:
                    stats["kept_working"] += 1
                continue
            q0 = _quote(c, occ)
            fresh = F.exit_mid(q0)
            if (int(rec.get("exit_attempts") or 0) >= 3 and occ not in ov["reprices"] and fresh is not None
                    and port_after == [held_q, round(fresh, 2)]):
                stats["divergence_reprice_past_three"] += 1
                labels.append("divergence_reprice_past_three")
            else:
                bad.append("working_exit:" + occ)
        if p["cancels"] != ov["cancels"]:
            bad.append("partial_entry_cancels")
        stats["partial_entry_cancels"] += len(ov["cancels"])
        stats["entries"] += len(ov["entries"])
        stats["contracts_bought"] += sum(e[1] for e in ov["entries"])
        stats["oversize"] += sum(1 for i in p["intents"] if i.kind == "enter" and i.position_meta.get("oversize"))
        for occ, x in ov["exits"].items():
            stats["exits"][x[2]] = stats["exits"].get(x[2], 0) + 1
        if bad:
            diffs.append({"idx": c["idx"], "session": c["session"], "now": c["now"], "what": bad, "labels": labels,
                          "old": {k: ov[k] for k in ("entries", "exits", "reprices", "cancels")},
                          "port": {k: p[k] for k in ("entries", "exits", "cancels")}})
    res = {"sleeve": "bilbo_options", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old run_entry / run_exit (clock, alpaca CLIs, state, log, sleep and the removed gates stubbed; "
                     "its real bilbo_options_signals, gate3_spread_ok averaging and reconcilers) vs port decide() on "
                     "the same generated bars, chains, snapshots and book"}
    write_receipt("bilbo_options", res)
    return res
