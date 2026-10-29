"""earnings_buyback: old earnings_buyback_sleeve.py scan_pass() vs the restored port's decide() on the same case.

The OLD module runs its real scan_pass(): manage_positions (_sync_earnings_date over desk/earnings.py fed the case's
calendar, exit_due: the weekday T+15 clock, spread_close_cost / call_bid against +-50% of the debit, the 5-DTE
floor; close_trade: every leg's quote fetched first, never one-sided, the long sold at its bid, the short bought at
its ask, the call sold at its bid), then -- while fewer than 4 slots are used (positions + closing + awaiting fills
+ pending) -- scan_signals over its real latest_scan (the case's scan files on disk: newest by mtime, the 8-day age
from scan_date or the mtime) and maybe_enter: the held / slot checks, _sector_blocked over the real desk/risk.py
SECTORS, its real earnings_window_ok over desk/earnings.py (calendar freshness, has_entry, is_blackout -- left
live: inside the 8-15 day window it can never bind -- and the window), the completed-event check, build_trade over
the real options_exec select_debit_spread / select_long_call / spread_qty_for_risk on the case's chain and quote
CLIs, _submit_trade (the long leg, then the short leg). Stubbed: the clock (FakeDT, also inside options_exec's
selectors), equity, the stock price, the calendar's file, the chain / quote / order CLIs, state load/save, logs,
and the gates the cutover removed: the kill switch, the cross-sleeve check, the 150% desk cap and its exposure
ledger, Decision #75 pre_buy -> proceed and its release replay; fills are not promoted (the state as given).

The PORT runs decide() on the same case: the scan through its own feed reader (desk/feedlib/edgar_buyback
load_latest over the same files), the chain rows carrying the case's quotes, the held positions as the engine's
sleeve_state renders them (spread groups, long calls, a working close as exit_submitted, an entry in flight as
pending_entry, a just-closed position's event as ebb_event).

Compared exactly: the structures opened (symbol, kind, legs, contracts, natural debit / ask), the structures closed
(symbol, contracts, reason, natural net / leg and limit), every exit decision (the old's exit_signal events,
including exits whose close had to wait for two-sided quotes), each held position's re-anchored earnings date and
the traded-event keys. Named divergences counted, not failed: each spread is one package (the old: two single-leg
orders at the same prices); a scan file that is not a JSON object is no scan for the port (the old's entry loop
raised on it, after its exits). A spread reduced to one leg (the old's ghost-leg prune) is decided as the old --
the engine never produces one (packages fill and settle whole). The schedule, chain-snapshot quotes, the live-quote
spot, book equity and re-decided unfilled orders are outside a single-pass comparison (unit tests:
tests/test_femto_earnings_buyback.py)."""
import json
import math
import os
import random
import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.feedlib import edgar_buyback as EB
from desk.sleeves.families.femto_specs import _risk_sectors
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("earnings_buyback")
N_CASES = 1500
BATCH = 250
POOL = ["AEHR", "LITE", "AAOI", "AXTI", "LASR", "OUST", "ALAB", "CRDO", "POET", "TSEM", "ARM", "MU",   # semis
        "NBIS", "WDC", "IREN", "HIVE", "SNDK", "TEM", "CORZ", "VRT",                                    # tech
        "CRML", "AG", "USAR", "FCEL", "OKLO", "ANF", "CVNA", "KEEL",                                    # others
        "AAPL", "MSFT", "NVDA", "AMZN", "JPM", "XOM", "WMT", "COST"]                                    # no sector

OLD = r'''
import os, sys, types
sys.dont_write_bytecode = True
import datetime as _dtmod
from datetime import datetime as _dt, timezone
import earnings_buyback_sleeve as O
import desk.earnings as E
import desk as _D
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
# the gates the cutover removed, stubbed open
O.check_kill_switch = lambda sym: True
O.cross_sleeve_ok = lambda sym: True
O._cap_gate_entry = lambda sym, n, e: True
O._dx_add = lambda *a, **k: None
O._dx_remove = lambda *a, **k: None
O.replay_chart_gate_releases = lambda st, now, equity=None: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
d75.sweep_releases = lambda *a, **k: []
sys.modules["desk.decision75"] = d75
_D.decision75 = d75
O.promote_fills = lambda st, now: None            # fills are the engine's
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
E.datetime = FakeDT
O._HAS_EARN = True
O._earn = E
def _clocked(fn):
    def w(*a, **k):
        saved = _dtmod.datetime
        _dtmod.datetime = FakeDT                  # options_exec's selectors read their ET date from the clock
        try:
            return fn(*a, **k)
        finally:
            _dtmod.datetime = saved
    return w
O.select_debit_spread = _clocked(O.select_debit_spread)
O.select_long_call = _clocked(O.select_long_call)
def _arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.get_account_equity = lambda e=case["equity"]: e
    O._get_stock_price = lambda sym, P=case["spots"]: P.get(sym)
    O.SCAN_GLOB = os.path.join(case["scan_dir"], "buyback_scan_*.json")
    E.load_earnings = lambda c=case["calendar"]: dict(c)
    E.calendar_status = lambda f=case["cal_ts"]: (f, 10)
    ORD = []
    def run_cli(script, args, timeout=90, C=case["chains"], Q=case["quotes"], ORD=ORD):
        args = [str(a) for a in args]
        if script == "alpaca_option_chain.py":
            u, typ = _arg(args, "--underlying"), _arg(args, "--type")
            lo, hi = _arg(args, "--expiry-gte"), _arg(args, "--expiry-lte")
            return [dict(r, strike=str(r["strike"]), type="call", multiplier="100") for r in C.get(u, [])
                    if typ == "call" and lo <= r["expiration"] <= hi]
        if script == "alpaca_option_quotes.py":
            occ = _arg(args, "--symbols")
            q = Q.get(occ)
            if q is None:
                return {}
            b, a = float(q["bid"]), float(q["ask"])
            mid = (b + a) / 2.0 if b > 0 and a > 0 else 0.0
            return {occ: {"bid": b, "ask": a, "mid": round(mid, 4), "spread_frac": (a - b) / mid if mid > 0 else None}}
        if script == "alpaca_option_order.py":
            ORD.append([_arg(args, "--symbol"), _arg(args, "--side"), int(_arg(args, "--qty")),
                        float(_arg(args, "--limit-price")), _arg(args, "--position-intent")])
            return {"id": "o%d" % len(ORD), "status": "accepted"}
        raise RuntimeError("unexpected CLI " + script)
    O.desk.run_cli = run_cli
    EV.clear()
    failed = None
    try:
        O.scan_pass(FakeDT.NOW)
    except Exception as e:
        failed = "%s: %s" % (type(e).__name__, str(e)[:120])
    exits = {e["symbol"]: e["reason"] for e in EV if e.get("event") == "exit_signal"}
    kinds = {}
    for e in EV:
        k = e.get("event")
        if k == "buyback_signal":
            k += ":" + str(e.get("kind"))
        elif k == "exit_signal":
            k += ":" + str(e.get("reason"))
        kinds[k] = kinds.get(k, 0) + 1
    dates = {}
    for s in case["held"]:
        p = st["positions"].get(s) or st["closing"].get(s)
        if p is not None:
            dates[s] = p.get("earnings_date")
    out.append({"orders": ORD, "exits": exits, "events": kinds, "dates": dates, "completed": st["completed"],
                "failed": failed})
print(json.dumps(out))
'''


# ------------------------------------------------------------------------------------------------- the corpus
def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _call(S, K, T, iv, r=0.04):
    if T <= 0:
        return max(0.0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
    return S * _ncdf(d1) - K * math.exp(-r * T) * _ncdf(d1 - iv * math.sqrt(T))


def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _grid(S, rnd):
    if S < 25:
        return rnd.choice((0.5, 1.0, 2.5))
    if S < 100:
        return rnd.choice((1.0, 2.5, 5.0))
    if S < 250:
        return rnd.choice((2.5, 5.0, 10.0))
    return rnd.choice((5.0, 10.0))


def _quote(rnd, fair):
    u = rnd.random()
    if u < 0.04:
        return None                                       # no quote at all
    if u < 0.06:
        return {"bid": 0.0, "ask": 0.0}                   # an empty book
    h = rnd.choice((0.005, 0.01, 0.02, 0.03, 0.04, 0.045, 0.05, 0.06, 0.07, 0.09))
    bid = round(max(0.01, fair * (1 - h)), 2)
    ask = round(max(bid + 0.01, fair * (1 + h)), 2)
    if u < 0.09:
        bid = 0.0                                         # offered only
    elif u < 0.10:
        ask = 0.0                                         # bid only
    return {"bid": bid, "ask": ask}


def _chain(rnd, sym, S, today):
    """calls on 1-4 expiries (some outside 30-45 DTE) and their quotes."""
    g = _grid(S, rnd)
    lo, hi = rnd.choice(((0.7, 1.4), (0.7, 1.4), (0.7, 1.4), (1.03, 1.4), (0.7, 1.06)))
    iv = rnd.choice((rnd.uniform(0.15, 0.5), rnd.uniform(0.3, 1.2)))
    rows, quotes = [], {}
    for d in sorted(rnd.sample(list(range(20, 60)), rnd.randint(1, 4))):
        exp = (today + timedelta(days=d)).isoformat()
        k = max(g, math.ceil(S * lo / g) * g)
        while k <= S * hi:
            occ = _occ(sym, exp, k)
            rows.append({"symbol": occ, "strike": float(k), "expiration": exp})
            q = _quote(rnd, max(0.01, _call(S, k, d / 365.0, iv)))
            if q is not None:
                quotes[occ] = q
            k = round(k + g, 4)
    return rows, quotes


def _date_str(rnd, d):
    """a calendar / filing date string, now and then in an odd but parseable or an unparseable spelling."""
    u = rnd.random()
    if u < 0.92:
        return d.isoformat()
    if u < 0.94:
        return " %s " % d.isoformat()                      # padded: the old strips
    if u < 0.96:
        return "%d-%d-%d" % (d.year, d.month, d.day)        # single-digit fields: strptime accepts them
    return rnd.choice(("TBD", "2026-02-30", "2026-13-01", d.isoformat() + "T00:00:00", ""))


def _held(rnd, sym, today, now, quotes, kind):
    """a held structure: the old's position record and the port's sleeve_state position."""
    S = rnd.uniform(10, 300)
    g = _grid(S, rnd)
    exp = (today + timedelta(days=rnd.choice((1, 3, 4, 5, 6, 7, 10, 15, 20, 30, 40)))).isoformat()
    ed = (today + timedelta(days=rnd.choice((-35, -24, -23, -22, -21, -20, -19, -15, -10, -5, -1, 0, 3, 8, 12))))
    ed = ed.isoformat()
    n = rnd.randint(1, 12)
    opened = float(int(now) - rnd.randint(1, 40) * 86400 - rnd.randint(0, 86399))
    if kind == "debit_spread":
        kl = max(g, round(S / g) * g)
        ks = kl + g * max(1, math.ceil(kl * 0.1 / g))
        lo, so = _occ(sym, exp, kl), _occ(sym, exp, ks)
        width = ks - kl
        debit = round(width * rnd.uniform(0.25, 0.5), 2)
        sf = round(rnd.uniform(0.1, 2.0), 2)
        lf = round(debit + sf + rnd.choice((0.0, 0.0, 0.01, -0.01)), 2)
        value = round((lf - sf) * rnd.choice((rnd.uniform(0.1, 0.5), rnd.uniform(0.5, 1.5), rnd.uniform(1.5, 2.5),
                                              0.5, 1.5)), 2)
        sa = round(rnd.uniform(0.05, 1.5), 2)
        lb = round(max(0.0, value + sa), 2)
        lq = {"bid": lb, "ask": round(lb + rnd.choice((0.05, 0.1, 0.2)), 2)}
        sq = {"bid": round(max(0.0, sa - rnd.choice((0.05, 0.1))), 2), "ask": sa}
        u = rnd.random()
        if u < 0.05:
            lq = None
        elif u < 0.10:
            sq = None
        elif u < 0.15:
            lq["bid"] = 0.0
        elif u < 0.18:
            sq["ask"] = 0.0
        for occ, q in ((lo, lq), (so, sq)):
            if q is None:
                quotes.pop(occ, None)
            else:
                quotes[occ] = q
        old = {"symbol": sym, "kind": kind, "contracts": n, "debit": round(lf - sf, 2), "long_occ": lo,
               "short_occ": so, "expiry": exp, "earnings_date": ed,
               "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat()}
        port = {"qty": n, "net_entry": lf - sf, "opened_at": opened, "legs": {lo: n, so: -n},
                "entry_date": datetime.fromtimestamp(opened, tz=ET).date().isoformat(), "stop_px": None,
                "kind": kind, "earnings_date": ed, "expiry": exp, "long_occ": lo, "short_occ": so}
        single = None
        if rnd.random() < 0.06:                       # a spread reduced to one leg (the old's ghost-leg prune)
            keep_long = rnd.random() < 0.6
            old["short_occ" if keep_long else "long_occ"] = None
            single = lo if keep_long else so
            port = {k: v for k, v in port.items() if k not in ("legs", "net_entry")}
            port.update(qty=n if keep_long else -n, entry_px=lf if keep_long else sf, occ=single, contracts=n)
        return old, port, single
    k = max(g, math.ceil(S * 1.02 / g) * g)
    occ = _occ(sym, exp, k)
    fpx = round(rnd.uniform(0.3, 12.0), 2)
    bid = round(fpx * rnd.choice((rnd.uniform(0.1, 0.5), rnd.uniform(0.5, 1.5), rnd.uniform(1.5, 2.5), 0.5, 1.5)), 2)
    u = rnd.random()
    if u < 0.06:
        quotes.pop(occ, None)
    else:
        quotes[occ] = {"bid": 0.0 if u < 0.12 else bid, "ask": round(bid + rnd.choice((0.05, 0.1, 0.3)), 2)}
    old = {"symbol": sym, "kind": kind, "contracts": n, "debit": round(fpx, 2), "occ": occ, "strike": k,
           "expiry": exp, "earnings_date": ed, "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat()}
    port = {"qty": n, "entry_px": fpx, "occ": occ, "contracts": n, "opened_at": opened, "stop_px": None,
            "entry_date": datetime.fromtimestamp(opened, tz=ET).date().isoformat(), "kind": kind,
            "earnings_date": ed, "expiry": exp, "strike": k}
    return old, port, occ


def _scan_files(rnd, d, now, rows):
    """the case's scan files: none, a corrupt newest one, a non-object one, or a scan (and maybe an older decoy)."""
    os.makedirs(d, exist_ok=True)
    now_dt = datetime.fromtimestamp(now, tz=timezone.utc)
    u = rnd.random()
    if u < 0.04:
        return "none"
    mtime = now - rnd.uniform(0, 12) * 86400
    name = "buyback_scan_%s.json" % datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M")
    if rnd.random() < 0.35:                                   # an older decoy, sometimes the later name
        dname = "buyback_scan_%s.json" % ("29991231_2359" if rnd.random() < 0.5 else "20000101_0000")
        with open(os.path.join(d, dname), "w") as f:
            json.dump({"scan_date": now_dt.replace(tzinfo=None).isoformat(),
                       "results": [{"ticker": "AAPL", "filing_date": "2026-01-01", "buyback_pct": 9.0}]}, f)
        os.utime(os.path.join(d, dname), (mtime - 3600, mtime - 3600))
    path = os.path.join(d, name)
    if u < 0.07:
        with open(path, "w") as f:
            f.write("{not json")
        os.utime(path, (mtime, mtime))
        return "corrupt"
    if u < 0.08:
        with open(path, "w") as f:
            json.dump([{"ticker": "AAPL"}], f)
        os.utime(path, (mtime, mtime))
        return "non_object"
    v = rnd.random()
    doc = {"days_back": 30, "tickers_scanned": sorted({r.get("ticker") or "" for r in rows}), "results": rows,
           "count": len(rows), "errors": [], "tickers_failed": 0}
    if v < 0.62:
        doc["scan_date"] = (now_dt - timedelta(days=rnd.uniform(0, 7.99))).replace(tzinfo=None).isoformat()
        kind = "fresh"
    elif v < 0.74:
        doc["scan_date"] = (now_dt - timedelta(days=rnd.uniform(8.0001, 20))).replace(tzinfo=None).isoformat()
        kind = "stale"
    elif v < 0.77:
        doc["scan_date"] = (now_dt - timedelta(days=8)).replace(tzinfo=None).isoformat()
        kind = "age_8_exact"
    elif v < 0.79:
        doc["scan_date"] = (now_dt - timedelta(days=8, microseconds=1)).replace(tzinfo=None).isoformat()
        kind = "age_8_plus"
    elif v < 0.83:
        doc["scan_date"] = (now_dt - timedelta(days=rnd.uniform(0, 10))).strftime("%Y-%m-%dT%H:%M:%SZ")
        kind = "zulu"
    elif v < 0.86:
        doc["scan_date"] = (now_dt - timedelta(days=rnd.uniform(0, 10))).astimezone(ET).isoformat()
        kind = "offset"
    elif v < 0.92:
        kind = "undated_mtime"
    elif v < 0.95:
        doc["scan_date"] = "not-a-date"
        kind = "garbage_mtime"
    else:
        doc["results"] = []
        doc["scan_date"] = now_dt.replace(tzinfo=None).isoformat()
        kind = "empty"
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
    os.utime(path, (mtime, mtime))
    return kind


def _case(rnd, idx, base):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 340))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(10, 15), 25, rnd.randint(0, 59),
                   rnd.randint(0, 999999), tzinfo=ET).timestamp()
    calendar, spots, chains, quotes, rows = {}, {}, {}, {}, []
    names = POOL[:12] if rnd.random() < 0.25 else POOL          # a semis-heavy case: the sector cap binds
    sigs = [rnd.choice(names) for _ in range(rnd.randint(0, 9))]
    for s in sigs:
        ed = today + timedelta(days=rnd.choice((2, 3, 5, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 15, 15, 16, 18,
                                                     22)))
        u = rnd.random()
        if s not in calendar:
            if u < 0.86:
                calendar[s] = _date_str(rnd, ed)
            elif u < 0.91:
                calendar[s] = None                              # confirmed no earnings
            # else absent: unknown
        dd = rnd.choice((10, 14, 15, 15, 16, 18, 20, 20, 22, 25, 25, 28, 29, 30, 30, 31, 40))
        filing = _date_str(rnd, ed - timedelta(days=dd)) if rnd.random() < 0.95 else rnd.choice((None, 20261001))
        pct = rnd.choice((3.0, 4.99, 5.0, 5.0, 5.5, 6.0, 7.0, 7.0, 8.5, 10.0, 25.0, 12.5))
        if rnd.random() < 0.04:
            pct = rnd.choice((None, "6.5", "abc", 0))
        rows.append({"ticker": s.lower() if rnd.random() < 0.05 else s, "filing_date": filing, "buyback_pct": pct,
                     "dollar_amount": None, "dollar_formatted": rnd.choice((None, "$1.5B", "$500M")),
                     "meets_threshold": True, "matched_text": "share repurchase program"})
        if s not in spots:
            v = rnd.random()
            spots[s] = (None if v < 0.05 else 0 if v < 0.07 else round(rnd.uniform(3, 9.99), 2) if v < 0.15
                        else 10.0 if v < 0.17 else round(rnd.uniform(10, 400), 2))
            if spots[s] and rnd.random() < 0.92:
                ch, q = _chain(rnd, s, spots[s], today)
                chains[s] = ch
                quotes.update(q)
    d = os.path.join(base, "c%d" % idx)
    scan_kind = _scan_files(rnd, d, now, rows)
    u = rnd.random()
    now_dt = datetime.fromtimestamp(now, tz=timezone.utc)
    cal_ts = ((now_dt - timedelta(days=2)).isoformat() if u < 0.86 else (now_dt - timedelta(days=9)).isoformat()
              if u < 0.95 else None if u < 0.98 else "garbage")
    state = {"positions": {}, "closing": {}, "awaiting_fills": {}, "pending": {}, "completed": []}
    ss, single, held = {}, {}, []
    for s in rnd.sample(names, rnd.choice((0, 0, 0, 1, 1, 2, 2, 3, 4, 5))):
        u = rnd.random()
        if u < 0.15:
            state["awaiting_fills"][s] = {"symbol": s, "kind": "debit_spread", "contracts": 1}
            ss[s] = {"position": None, "pending_entry": {"qty": 1.0, "filled": 0.0,
                                                         "key": "%s:%s:earnings-buyback" % (s, today), "ref_px": None}}
            continue
        old, port, leg = _held(rnd, s, today, now, quotes, "debit_spread" if rnd.random() < 0.7 else "long_call")
        if leg:
            single[s] = leg
        held.append(s)
        v = rnd.random()                                       # the calendar against the held date
        if v < 0.35:
            calendar[s] = (date.fromisoformat(old["earnings_date"]) - timedelta(days=rnd.randint(1, 10))).isoformat()
        elif v < 0.55:
            calendar[s] = (date.fromisoformat(old["earnings_date"]) + timedelta(days=rnd.randint(1, 90))).isoformat()
        elif v < 0.65:
            calendar[s] = old["earnings_date"]
        elif v < 0.70:
            calendar[s] = "TBD"
        elif v < 0.75:
            calendar[s] = None
        if u < 0.30:
            state["closing"][s] = dict(old, close_order_ids=["c-" + s])
            port["exit_submitted"] = True
        else:
            state["positions"][s] = old
        ss[s] = {"position": port}
    completed = []
    for s in sigs:
        if s not in ss and rnd.random() < 0.12 and isinstance(calendar.get(s), str) and F._parse_date(calendar[s]):
            key_d = F._parse_date(calendar[s]).isoformat()
            if rnd.random() < 0.5:
                completed.append("%s|%s" % (s, key_d))           # traded before
            else:
                ss[s] = {"position": None, "ebb_event": key_d}  # its position just closed (the old: completed)
                state["completed"].append("%s|%s" % (s, key_d))
    completed += ["%s|%s" % (rnd.choice(POOL), (today - timedelta(days=rnd.choice((30, 119, 121, 200)))).isoformat())
                  for _ in range(rnd.randint(0, 2))]
    state["completed"] = completed + state["completed"]
    equity = rnd.choice((rnd.uniform(1_000, 20_000), rnd.uniform(20_000, 500_000), rnd.uniform(500_000, 5_000_000)))
    if rnd.random() < 0.02:
        equity = rnd.choice((None, 0.0, -5.0))
    return {"now": now, "session": today.isoformat(), "scan_dir": d, "scan_kind": scan_kind, "calendar": calendar,
            "cal_ts": cal_ts, "spots": spots, "chains": chains, "quotes": quotes, "state": state, "ss": ss,
            "meta_completed": completed, "single": single, "held": held, "equity": equity}


# ------------------------------------------------------------------------------------------------- the port
def _fresh(cal_ts, now):
    """the old calendar_status freshness: updated_ts parseable and at most 8 days old."""
    if not isinstance(cal_ts, str):
        return False
    try:
        dt = datetime.fromisoformat(cal_ts.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.fromtimestamp(now, tz=timezone.utc) - dt) <= timedelta(days=8)


def _port_inputs(c, sectors):
    today = date.fromisoformat(c["session"])
    lo, hi = (today + timedelta(days=F.DTE_MIN)).isoformat(), (today + timedelta(days=F.DTE_MAX)).isoformat()
    chains = {s: [dict(r, type="call", **(c["quotes"].get(r["symbol"]) or {"bid": None, "ask": None}))
                  for r in rows if lo <= r["expiration"] <= hi] for s, rows in c["chains"].items()}
    held_occs = set()
    for st in c["ss"].values():
        pos = st.get("position") or {}
        held_occs |= set(pos.get("legs") or ({pos["occ"]: 1} if pos.get("occ") else {}))
    extra = {"scan": EB.load_latest(c["scan_dir"]), "earnings": dict(c["calendar"]),
             "earnings_fresh": _fresh(c["cal_ts"], c["now"]), "chains": chains,
             "option_quotes": {o: dict(c["quotes"][o]) for o in held_occs if o in c["quotes"]},
             "quotes": {s: {"bid": None, "ask": None, "last": v} for s, v in c["spots"].items() if v is not None},
             "sectors": sectors, "meta": {"completed": list(c["meta_completed"])}, "closed_trades": [],
             "sleeve_state": json.loads(json.dumps(c["ss"]))}
    return fc.Context(now=c["now"], session=c["session"], equity=float(c["equity"] or 0.0), extra=extra)


def _port(c, sectors):
    ctx = _port_inputs(c, sectors)
    d = F.decide({}, ctx)
    opened, closed = [], []
    for i in d["intents"]:
        if i.kind == "enter":
            if i.asset == "mleg":
                opened.append([i.symbol, "debit_spread", i.legs[0]["symbol"], i.legs[1]["symbol"], int(i.qty_hint),
                               round(i.net_price, 2)])
            else:
                opened.append([i.symbol, "long_call", i.legs[0]["symbol"], int(i.qty_hint),
                               float(i.order["limit_price"])])
        else:
            why = i.reason.split(": ", 1)[1].split(" ")[0]
            if i.net_price is not None:
                closed.append([i.symbol, int(i.qty_hint), why, round(i.net_price, 2)])
            else:
                closed.append([i.symbol, c["single"][i.symbol], int(i.qty_hint), why, float(i.order["limit_price"])])
    dates = {s: ((d["symbols"].get(s) or {}).get("pos") or {}).get("earnings_date") for s in c["held"]}
    return opened, closed, d, dates


def _old_view(o):
    opened, closed = [], []
    by_sym = {}
    for occ, side, qty, px, intent in o["orders"]:
        by_sym.setdefault(occ[:-15], []).append((occ, side, qty, px, intent))
    for sym, legs in by_sym.items():
        op = {}
        for x in legs:
            op.setdefault(x[4], []).append(x)
        bto, sto = op.get("buy_to_open") or [], op.get("sell_to_open") or []
        if bto or sto:
            if len(bto) == 1 and len(sto) == 1 and bto[0][2] == sto[0][2]:
                opened.append([sym, "debit_spread", bto[0][0], sto[0][0], bto[0][2], round(bto[0][3] - sto[0][3], 2)])
            elif len(bto) == 1 and not sto:
                opened.append([sym, "long_call", bto[0][0], bto[0][2], bto[0][3]])
            else:
                opened.append([sym, "malformed", legs])
        stc, btc = op.get("sell_to_close") or [], op.get("buy_to_close") or []
        if stc or btc:
            if len(stc) == 1 and len(btc) == 1 and stc[0][2] == btc[0][2]:
                closed.append([sym, stc[0][2], o["exits"].get(sym), round(btc[0][3] - stc[0][3], 2)])
            elif len(stc) + len(btc) == 1:
                x = (stc or btc)[0]
                closed.append([sym, x[0], x[2], o["exits"].get(sym), x[3]])
            else:
                closed.append([sym, "malformed", legs])
    return opened, closed


def _prune(keys, now):
    cut = (datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(days=F.COMPLETED_KEEP_DAYS)).date().isoformat()
    return [k for k in keys if not isinstance(k, str) or k.rsplit("|", 1)[-1] >= cut]


def run():
    rnd = random.Random(1016)
    base = tempfile.mkdtemp(prefix="ebb_parity_")
    sectors = _risk_sectors()
    try:
        cases = [_case(rnd, i, base) for i in range(N_CASES)]
        old = []
        for b in range(0, len(cases), BATCH):
            old += old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("ss", "single", "meta_completed")}
                                           for c in cases[b:b + BATCH]]})
        diffs = []
        stats = {"opened": {}, "closed": {}, "exit_decisions": {}, "exits_waiting_one_sided": 0, "packages_opened": 0,
                 "packages_closed": 0, "single_leg_spreads": 0, "re_anchored": 0, "scan_files": {},
                 "port_entry_skips": {}, "old_events": {}, "non_object_scan_old_failed": 0, "cap_full_cases": 0}
        for c, o in zip(cases, old):
            po, pc, d, pdates = _port(c, sectors)
            oo, oc = _old_view(o)
            bad = []
            if sorted(map(json.dumps, po)) != sorted(map(json.dumps, oo)):
                bad.append("opened")
            if sorted(map(json.dumps, pc)) != sorted(map(json.dumps, oc)):
                bad.append("closed")
            if d["exits"] != o["exits"]:
                bad.append("exit_decisions")
            if pdates != o["dates"]:
                bad.append("earnings_dates")
            if set(d["completed"]) != set(_prune(o["completed"], c["now"])):
                bad.append("completed")
            non_object = c["scan_kind"] == "non_object" and o["failed"] is not None
            if o["failed"] is not None and not non_object:
                bad.append("old_failed")
            if bad:
                diffs.append({"session": c["session"], "now": c["now"], "what": bad, "failed": o["failed"],
                              "old": [oo, oc, o["exits"], o["dates"]], "port": [po, pc, d["exits"], pdates]})
            stats["non_object_scan_old_failed"] += non_object
            stats["scan_files"][c["scan_kind"]] = stats["scan_files"].get(c["scan_kind"], 0) + 1
            for x in oo:
                stats["opened"][x[1]] = stats["opened"].get(x[1], 0) + 1
            stats["packages_opened"] += sum(1 for x in po if x[1] == "debit_spread")
            stats["packages_closed"] += sum(1 for x in pc if len(x) == 4)
            for x in oc:
                r = x[2] if len(x) == 4 else x[3]
                stats["closed"][r] = stats["closed"].get(r, 0) + 1
            for r in o["exits"].values():
                stats["exit_decisions"][r] = stats["exit_decisions"].get(r, 0) + 1
            stats["exits_waiting_one_sided"] += len(set(o["exits"]) - {x[0] for x in oc})
            stats["single_leg_spreads"] += len(c["single"]) - sum(
                1 for s in c["single"] if (c["ss"][s]["position"] or {}).get("kind") == "long_call")
            stats["re_anchored"] += sum(1 for s, v in o["dates"].items()
                                        if v != (c["state"]["positions"].get(s) or c["state"]["closing"].get(s) or {})
                                        .get("earnings_date"))
            for _, why in d["skips"]:
                stats["port_entry_skips"][why] = stats["port_entry_skips"].get(why, 0) + 1
            for k, v in o["events"].items():
                stats["old_events"][k] = stats["old_events"].get(k, 0) + v
            used = len([s for s, st in c["ss"].items() if st.get("position") or st.get("pending_entry")])
            stats["cap_full_cases"] += used >= F.MAX_POSITIONS
    finally:
        shutil.rmtree(base, ignore_errors=True)
    res = {"sleeve": "earnings_buyback", "cases": len(cases), "identical": len(cases) - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "divergences": {"one_package_per_spread": "counted: packages_opened / packages_closed (the old: two "
                                                     "single-leg orders each way, at the same prices)",
                           "non_object_scan": "counted: non_object_scan_old_failed (the old's entry loop raised "
                                              "after its exits; the port reads no scan)",
                           "not_in_single_pass": ["hourly passes at :25 in the session", "chain-snapshot leg quotes",
                                                  "the spot from the live quote", "sizing on the book's equity",
                                                  "unfilled orders re-decided at the next pass",
                                                  "events marked traded when the book is flat"]},
           "method": "old scan_pass (clock incl. options_exec's selectors, equity, stock price, calendar file, "
                     "chain/quote/order CLIs and removed gates stubbed; its real latest_scan over the case's files, "
                     "scan_signals, manage_positions / _sync_earnings_date / exit_due / close_trade, maybe_enter / "
                     "_sector_blocked over desk/risk.py SECTORS / earnings_window_ok over desk/earnings.py incl. "
                     "is_blackout / build_trade / select_debit_spread / select_long_call / _submit_trade) vs port "
                     "decide() with its own feed reader on the same files"}
    write_receipt("earnings_buyback", res)
    return res
