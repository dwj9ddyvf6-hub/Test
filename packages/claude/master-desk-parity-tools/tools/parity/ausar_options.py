"""ausar_options: the SOURCE runtime's own snapshot path and evaluator (agentic-trading-desk aurelia-paper-desk @1720157f,
ausar-archive/.../desk-source/backend, run in its own tree AUSAR_SRC) vs the port (desk/sleeves/families/ausar_options.py
over engine-shaped Views), on deterministic random multi-step sequences, each side carrying its own book and state.

  SOURCE  r19_data.Collector._calendar (session block + calendar_sessions now-1700d..now+390d) ->
          Collector._history_rows (raw Alpaca-shaped daily bars -> native rows) -> r19_option_data.normalize_contract /
          normalize_quote (Alpaca-shaped contract census rows, OPRA snapshots, SIP quotes) -> enrich_snapshot ->
          r19_cli.bounded_snapshot -> r19_options.evaluate; fills applied with r19_options.prepare_package's own
          cash_delta / position_metadata (the r19_core._package accounting, proceeds credited at once — N4).
  PORT    AusarOptionBook.signal(View) with the same market in the desk's shapes (epoch bars, chain rows, equity
          quotes, engine positions); fills applied with the same harness fill model to its own book.

Compared per step: package entries (signal id, package id, legs + ratios, quantity, reason, natural limit, risk budget,
entry spot, exit session, pre-expiry session), package exits (package, legs, signal id, reason, natural close value),
the QQQ core purchase (quantity, signal id), the non-quiet blocker reasons, the recovery signal observations
(symbol, pass) and the frozen entry-attempt ledger (signal id -> consumed). Plus the six monitor cards' diagnostics.

Stubbed in the source (I/O only): httpx (transport module, never called), backend.providers._nyse (the
exchange_calendars XNYS session table, served from the payload: the desk calendar's sessions 2019-2028) and the
path of r19_options.RULES (the commit's options_rules.json, blob 6e2aa298 — present in the commit tree but not in
the checkout — read from its hash-verified vendored copy).
Qualified inputs on BOTH sides (named divergence N1 — the source's own probe left greeks_market_at=None, had no
deliverable registry, no exercise_checks producer and never set actions_verified on underlying_quotes, so it could
not admit any entry): option / underlying quotes and Greeks stamped at the decision clock, a verified standard
deliverable, a complete chain (legacy complete_option_chains), exercise_checks without an assignment alert, the QQQ
quote actions-verified. Displayed sizes (N2): unbounded on both sides, or the same carried sizes on both sides."""
import bisect
import hashlib
import json
import math
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.contract import View
from desk.data.options import occ_parse, occ_symbol
from desk.sleeves.families import ausar_options as AO
from desk.util import ET
from desk.vendor.ausar_r19 import r19_options as vo

from . import old_run, write_receipt

SRC = os.environ.get("AUSAR_SRC", "/home/user/br/agentic-trading-desk@aurelia-paper-desk/ausar-archive/ausar-receiver/"
                     "original-payload/desk-source")
N_SEQ = int(os.environ.get("AUSAR_OPT_SEQS", "700"))
UTC = timezone.utc
UNDER = {"IWM": 220.0, "QQQ": 480.0, "SPY": 600.0}
QUIET = set(AO.QUIET_BLOCKERS)
BIG = AO.UNBOUNDED_SIZE

SOURCE_SCRIPT = r'''
import bisect, sys, types, json
from decimal import Decimal
from datetime import datetime, timezone, timedelta
sys.modules['httpx'] = types.ModuleType('httpx')
import pandas as pd
CAL = {d: tuple(v) for d, v in PAYLOAD['calendar'].items()}
DATES = sorted(CAL)
class XNYS:
    @staticmethod
    def _d(x):
        return str(x)[:10]
    def is_session(self, d):
        return self._d(d) in CAL
    def date_to_session(self, d, direction='none'):
        d = self._d(d)
        if d in CAL:
            return pd.Timestamp(d)
        i = bisect.bisect_left(DATES, d)
        if direction == 'previous':
            return pd.Timestamp(DATES[i - 1])
        if direction == 'next':
            return pd.Timestamp(DATES[i])
        raise ValueError('not a session: ' + d)
    def session_open(self, s):
        return pd.Timestamp(CAL[self._d(s)][0], unit='s', tz='UTC')
    def session_close(self, s):
        return pd.Timestamp(CAL[self._d(s)][1], unit='s', tz='UTC')
    def previous_session(self, s):
        return pd.Timestamp(DATES[bisect.bisect_left(DATES, self._d(s)) - 1])
    def next_session(self, s):
        return pd.Timestamp(DATES[bisect.bisect_right(DATES, self._d(s))])
    def sessions_in_range(self, a, b):
        return [pd.Timestamp(x) for x in DATES[bisect.bisect_left(DATES, self._d(a)):bisect.bisect_right(DATES, self._d(b))]]
import backend
prov = types.ModuleType('backend.providers')
prov._nyse = lambda: XNYS()
sys.modules['backend.providers'] = prov
backend.providers = prov
from backend import r19_options as RO, r19_option_data as OD, r19_data as RD, r19_cli as CLI
import pathlib
RO.RULES = pathlib.Path(PAYLOAD['rules_path'])   # the commit's options_rules.json (blob 6e2aa298, not checked out)
UTC = timezone.utc
QUIET = set(PAYLOAD['quiet'])
D = Decimal

def stamp_iso(ts):
    return datetime.fromtimestamp(ts, tz=UTC).isoformat()

def quote(sym, q, now_iso, feed):
    raw = {'bp': q['bid'], 'ap': q['ask'], 'bs': q['bs'], 'as': q['as'], 't': now_iso}
    return OD.normalize_quote(sym, raw, {'received_at': now_iso, 'source_sha256': 'harness-' + feed}, feed)

def contract(r, now_iso):
    reg = {r['symbol']: {'verified': True, 'source_sha256': 'harness-deliverable', 'settlement': 'physical',
                         'schema': None, 'deliverable': {'shares': 100, 'cash': 0}}}
    raw = {'id': 'id-' + r['symbol'], 'symbol': r['symbol'], 'root_symbol': r['root'], 'underlying_symbol': r['u'],
           'expiration_date': r['exp'], 'strike_price': r['strike'], 'type': r['right'], 'multiplier': '100',
           'style': 'american', 'status': 'active', 'tradable': True}
    c = OD.normalize_contract(raw, {'received_at': now_iso, 'source_sha256': 'harness-census'}, reg)
    c['delta'] = r['delta']
    c['greeks_received_at'] = now_iso
    c['greeks_market_at'] = now_iso      # N1: a qualified Greek clock (the source probe left it None)
    return c

def natural(legs, quotes, opening):
    tot = 0.0
    for l in legs:
        q = quotes[l['symbol']]
        r = int(l['ratio'])
        side = ('ask' if r > 0 else 'bid') if opening else ('bid' if r > 0 else 'ask')
        tot += float(q[side]) * r
    return round(tot, 4)

def liquidation(book, s):
    v = 0.0
    for sym, p in book['positions'].items():
        m = p['metadata']
        if 'legs' in m:
            try:
                v += natural(m['legs'], s['option_quotes'], False) * 100 * int(p['quantity'])
            except KeyError:
                pass
        else:
            uq = s['underlying_quotes'].get(sym)
            if uq:
                v += float(uq['bid']) * float(p['quantity'])
    return v

out = []
for seq in PAYLOAD['seqs']:
    cfg = next(c for c in RO.register() if c['id'] == seq['rule'])
    book = {'id': cfg['id'], 'strategy_id': cfg['id'], 'config': cfg, 'initial_capital': cfg['initial_capital'],
            'cash': D(str(cfg['initial_capital'])), 'collateral': '0', 'enabled': True,
            'installed_at': seq['installed_at'], 'state': {}, 'positions': {}}
    outcomes = []
    res_steps = []
    for st in seq['steps']:
        now = datetime.fromtimestamp(st['now'], tz=UTC)
        now_iso = now.isoformat()
        today, metadata, _prev, _cal = RD.Collector._calendar(None, now)
        by_session = {x['session']: x for x in metadata}
        snapshot = {'asof': now_iso, 'now': now_iso, 'calendar': today, 'calendar_sessions': metadata, 'histories': {}}
        for sym, allbars in seq['bars'].items():
            bars = allbars[:st['nb']]
            item = {'value': {'bars': bars}, 'observed_at': st['bars_observed_at'], 'source_sha256': 'harness-bars-' + sym}
            snapshot['histories'][sym] = RD.Collector._history_rows(item, by_session, now, 'RAW')
        obs = {'option_quotes': {}, 'underlying_quotes': {}, 'option_contracts': [], 'option_fees': dict(OD.DEFAULT_PAPER_OPTION_FEES),
               'complete_option_chains': []}
        for u, rows in st['chains'].items():
            obs['complete_option_chains'].append(u)
            for r in rows:
                obs['option_contracts'].append(contract(r, now_iso))
                if r['bid'] is not None:
                    obs['option_quotes'][r['symbol']] = quote(r['symbol'], r, now_iso, 'opra')
        for occ, q in st['leg_quotes'].items():
            if q['bid'] is not None:
                obs['option_quotes'][occ] = quote(occ, q, now_iso, 'opra')
        for sym, q in st['uquotes'].items():
            obs['underlying_quotes'][sym] = dict(quote(sym, q, now_iso, 'sip'), actions_verified=True)   # N1
        s = OD.enrich_snapshot(snapshot, {'snapshot': obs, 'receipts': [], 'observed_at': now_iso})
        far = (now + timedelta(days=3650)).date().isoformat()
        s['exercise_checks'] = {u: {'verified': True, 'source_sha256': 'harness-exercise', 'received_at': now_iso,
                                    'valid_through': far, 'assignment_alert': False} for u in st['exercise']}
        book['cash'] = D(str(book['cash']))
        book['nav'] = str(float(book['cash']) + liquidation(book, s))
        book['cash'] = str(book['cash'])
        book['state']['last_evaluation'] = {'outcomes': outcomes}
        bs = CLI.bounded_snapshot(s, book)
        r = RO.evaluate(bs, book)
        if r.get('state') is not None:
            book['state'].update(r['state'])
        step = {'opens': [], 'closes': [], 'core': [], 'blockers': sorted({str(b.get('reason')) for b in r['blockers']
                                                                            if b.get('reason') and b.get('reason') not in QUIET}),
                'obs': sorted([o['symbol'], bool(o['pass'])] for o in r['observations'] if 'pass' in o and o.get('symbol'))}
        outcomes = []
        cash = D(book['cash'])
        for it in r['intents']:
            if it.get('type') != 'option_package':
                uq = bs['underlying_quotes'][it['symbol']]
                step['core'].append({'sid': it['signal_id'], 'sym': it['symbol'], 'qty': int(it['quantity'])})
                if st['fill_open']:
                    q = int(it['quantity'])
                    cost = D(str(uq['ask'])) * q
                    cash -= cost + cost * D('0.0015')
                    book['positions'][it['symbol']] = {'symbol': it['symbol'], 'quantity': str(q),
                                                       'metadata': dict(it.get('metadata', {}))}
                continue
            if it['action'] == 'open':
                m = it['metadata']
                step['opens'].append({'sid': it['signal_id'], 'pkg': it['symbol'],
                                      'legs': sorted([l['symbol'], int(l['ratio'])] for l in it['legs']),
                                      'qty': int(it['quantity']), 'reason': it['reason'],
                                      'net': natural(it['legs'], bs['option_quotes'], True),
                                      'risk_budget': m['risk_budget'], 'entry_spot': m['entry_spot'],
                                      'exit_session': m['exit_session'], 'expiry_exit_session': m['expiry_exit_session']})
                if st['fill_open']:
                    pp = RO.prepare_package(it, bs, book)
                    cash += D(pp['cash_delta'])
                    book['positions'][it['symbol']] = {'symbol': it['symbol'], 'quantity': str(int(it['quantity'])),
                                                       'metadata': dict(pp['position_metadata'], type='option_package')}
                    outcomes.append({'symbol': it['symbol'], 'action': 'open', 'status': 'filled'})
            elif it['action'] == 'close':
                legs = book['positions'][it['symbol']]['metadata']['legs']
                step['closes'].append({'sid': it['signal_id'], 'pkg': it['symbol'],
                                       'legs': sorted([l['symbol'], int(l['ratio'])] for l in legs),
                                       'qty': int(it['quantity']), 'reason': it['reason'],
                                       'net': natural(legs, bs['option_quotes'], False)})
                if st['fill_close']:
                    pp = RO.prepare_package(it, bs, book)
                    cash += D(pp['cash_delta'])
                    book['positions'].pop(it['symbol'])
            else:
                step['closes'].append({'sid': it['signal_id'], 'pkg': it['symbol'], 'settle': True})
        book['cash'] = str(cash)
        step['attempts'] = {k: bool(v.get('consumed')) for k, v in book['state'].get('option_entry_attempts', {}).items()}
        step['cash'] = round(float(cash), 6)
        res_steps.append(step)
    out.append(res_steps)

mon = []
for m in PAYLOAD['monitors']:
    cfg = next(c for c in RO.register() if c['id'] == m['rule'])
    now = datetime.fromtimestamp(m['now'], tz=UTC)
    today, metadata, _p, _c = RD.Collector._calendar(None, now)
    s = OD.enrich_snapshot({'asof': now.isoformat(), 'now': now.isoformat(), 'calendar': today,
                            'calendar_sessions': metadata, 'histories': {}}, None)
    book = {'id': cfg['id'], 'config': cfg, 'cash': '0', 'debt': '0', 'positions': {}, 'state': {}, 'enabled': False,
            'installed_at': now.isoformat(), 'nav': None}
    r = RO.evaluate(s, book)
    mon.append({'observations': r['observations'], 'blockers': [b.get('reason') for b in r['blockers']],
                'intents': len(r['intents'])})
print(json.dumps({'seqs': out, 'monitors': mon}))
'''


# -- market generation ----------------------------------------------------------------------------------
def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs(S, K, T, iv, right):
    if T <= 0:
        return max(0.0, S - K) if right == "call" else max(0.0, K - S), (1.0 if S > K else 0.0) if right == "call" else (-1.0 if S < K else 0.0)
    d1 = (math.log(S / K) + 0.5 * iv * iv * T) / (iv * math.sqrt(T))
    d2 = d1 - iv * math.sqrt(T)
    c = S * _ncdf(d1) - K * _ncdf(d2)
    if right == "call":
        return c, _ncdf(d1)
    return c - S + K, _ncdf(d1) - 1.0


def _sessions_between(a, b):
    out, d = [], a
    while d <= b:
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _midnight_et(d):
    return datetime(d.year, d.month, d.day, tzinfo=ET).timestamp()


def _series(rng, days, start, dip_at, trend):
    """closes over `days` with a washout ending at index dip_at (or none)."""
    px, out = start, []
    drift = {"up": 0.0009, "flat": 0.0, "down": -0.0009}[trend]
    vol = rng.uniform(0.006, 0.016)
    for i, d in enumerate(days):
        r = rng.gauss(drift, vol)
        if dip_at is not None and dip_at - 2 <= i <= dip_at:
            r = -abs(rng.gauss(0.012, 0.006))
        o = px * (1 + rng.gauss(0, vol / 3))
        c = max(1.0, px * (1 + r))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
        out.append({"d": d, "o": round(o, 2), "h": round(h, 2), "l": round(lo, 2), "c": round(c, 2),
                    "v": int(rng.uniform(5e6, 6e7))})
        px = c
    for b in out:                                     # rounding can break the OHLC geometry: restore it
        b["h"] = max(b["h"], b["o"], b["c"])
        b["l"] = min(b["l"], b["o"], b["c"])
    return out


def _expiries(day0):
    out, d = [], day0 + timedelta(days=5)
    while d <= day0 + timedelta(days=45):
        if d.weekday() == 4:
            e = d
            while not cal.is_trading_day(e):
                e -= timedelta(days=1)
            out.append(e)
        d += timedelta(days=1)
    return out


def _chain(rng, u, spot, now, expiries, strikes, rights, sized, iv):
    rows = []
    for e in expiries:
        T = max(1e-6, (cal.session_close(e) - now) / (365 * 86400))
        for k in strikes:
            for right in rights:
                fair, delta = _bs(spot, float(k), T, iv * (1 + 0.15 * (k - spot) / spot * (-1)), right)
                spread = max(0.01, round(max(fair, 0.05) * rng.uniform(0.003, 0.04), 2))
                bid = max(0.0, round(fair - spread / 2, 2))
                ask = round(max(bid + spread, 0.01), 2)
                occ = occ_symbol(u, e.isoformat(), right, k)
                r = {"symbol": occ, "u": u, "root": u, "exp": e.isoformat(), "strike": str(k), "right": right,
                     "delta": round(delta, 4), "bid": bid, "ask": ask, "bs": BIG, "as": BIG}
                x = rng.random()
                if x < 0.02:
                    r["delta"] = None
                elif x < 0.03:
                    r["bid"] = None
                if sized:
                    r["bs"], r["as"] = rng.randint(1, 40), rng.randint(1, 40)
                rows.append(r)
    return rows


def _price_leg(rng, occ, spot, now, iv, sized):
    _, exp, right, k = occ_parse(occ)
    T = max(1e-6, (cal.session_close(exp) - now) / (365 * 86400))
    fair, _ = _bs(spot, k, T, iv, right)
    spread = max(0.01, round(max(fair, 0.05) * rng.uniform(0.005, 0.06), 2))
    bid = max(0.0, round(fair - spread / 2, 2))
    return {"bid": bid, "ask": round(max(bid + spread, 0.01), 2), "bs": rng.randint(1, 40) if sized else BIG,
            "as": rng.randint(1, 40) if sized else BIG}


FUNDED = [c for c in vo.register() if not c.get("monitor_only")]
RECOVERY = [c["id"] for c in FUNDED if c["family"] == "recovery"]
CORE = [c["id"] for c in FUNDED if c["family"] == "core_reserve"]
# the event families with their producers' inputs absent (no calendar run, no R5 record, no bridge feed): both
# sides see no events; their producer paths are compared in tools/parity/ausar_option_producers.py (XSP always
# builds its state, so it is compared there only)
BLOCKED = [c["id"] for c in FUNDED if c["family"] in ("pead", "opening_gamma", "tensor_leaps")]
# the six monitor cards left the desk (the owner, 2026-10-26, D39): no monitor cases; their last comparison is in
# docs/receipts/parity/ausar_options.json
MONITORS = []


def _at(d, h, m, s=0):
    return datetime(d.year, d.month, d.day, h, m, s, tzinfo=ET).timestamp()


def make_sequence(seed):
    rng = random.Random(seed)
    x = rng.random()
    rule = rng.choice(RECOVERY) if x < 0.72 else (rng.choice(CORE) if x < 0.9 else rng.choice(BLOCKED))
    cfg = next(c for c in FUNDED if c["id"] == rule)
    sessions = _sessions_between(date(2025, 2, 3), date(2026, 11, 30))
    day0 = rng.choice(sessions)
    hist = _sessions_between(day0 - timedelta(days=700), day0 + timedelta(days=20))
    i0 = hist.index(day0)
    hist = hist[max(0, i0 - 240):i0 + 12]
    i0 = hist.index(day0)
    series = {}
    for u, base in UNDER.items():
        trend = rng.choice(("up", "up", "up", "flat", "down"))
        dip = (i0 - 1) if rng.random() < 0.6 else None
        series[u] = _series(rng, hist, base * rng.uniform(0.7, 1.0), dip, trend)
    sized = rng.random() < 0.2
    rights = ("call",) if rng.random() < 0.7 else ("call", "put")
    lo, hi = AO.entry_window(cfg["family"])
    w0 = _at(day0, lo[0], lo[1])
    w1 = _at(day0, hi[0], hi[1])
    times = []
    if rng.random() < 0.15:
        times.append(w0 - rng.randint(1, 240))                     # flat before the window: silent
    t1 = w0 + rng.uniform(0, (w1 - w0) - 1)
    times.append(t1)
    times.append(min(t1 + rng.choice((30, 60, 90)), w1 + rng.choice((-1, 5))))
    later = [d for d in hist[i0:i0 + 9]]
    for _ in range(rng.randint(1, 3)):
        d = rng.choice(later[:7])
        times.append(_at(d, rng.choice((9, 10, 11, 13, 14, 15)), rng.randint(30 if d == day0 else 0, 59) if True else 0))
    # the planned exit: 15:55 of the fifth session (and its last minute before), the next open when missed
    fut = later[:6]
    if len(fut) >= 5:
        times += [_at(fut[4], 15, 54, 30), _at(fut[4], 15, 55, rng.randint(0, 50))]
        if len(fut) >= 6:
            times.append(_at(fut[5], 9, 31))
    times = sorted({round(t, 3) for t in times if cal.is_rth(t)})
    fill_open = rng.random() < 0.85
    spot_now = {}
    steps = []
    expiries = _expiries(day0)
    strikes = {u: list(range(int(series[u][i0 - 1]["c"] * 0.94), int(series[u][i0 - 1]["c"] * 1.06) + 1)) for u in UNDER}
    ivs = {u: rng.uniform(0.07, 0.30) for u in UNDER}
    for t in times:
        d = cal._as_date(t)
        k = hist.index(d)
        st = {"now": t, "fill_open": fill_open, "fill_close": True, "nb": k}   # bars: sessions before the step's
        st["bars_observed_at"] = datetime.fromtimestamp(cal.session_close(hist[k - 1]) + 3600, tz=UTC).isoformat()
        uq = {}
        for u in UNDER:
            last = series[u][k - 1]["c"]
            jump = 0.026 if rng.random() < 0.25 else 0.0
            s = round(last * (1 + jump + rng.gauss(0.0, 0.006)), 2)
            spot_now[u] = s
            if rng.random() < 0.03:
                continue                                              # no consolidated quote this pass
            uq[u] = {"bid": round(s - 0.01, 2), "ask": round(s + 0.01, 2), "bs": BIG, "as": BIG}
        st["uquotes"] = uq
        st["chains"] = {}
        in_win = lo <= (datetime.fromtimestamp(t, tz=ET).hour, datetime.fromtimestamp(t, tz=ET).minute) < hi
        if in_win and cfg["family"] in ("recovery", "core_reserve"):
            for u in cfg["universe"]:
                st["chains"][u] = _chain(rng, u, spot_now[u], t, expiries, strikes[u], rights, sized, ivs[u])
        st["exercise"] = sorted(set(st["chains"]) | set(UNDER))
        st["sized"] = sized
        steps.append(st)
    last = [{u: series[u][hist.index(cal._as_date(st["now"])) - 1]["c"] for u in UNDER} for st in steps]
    bars_src = {u: [{"t": datetime.fromtimestamp(_midnight_et(b["d"]), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]} for b in series[u]] for u in UNDER}
    bars_port = {u: [{"t": _midnight_et(b["d"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                     for b in series[u]] for u in UNDER}
    return {"bars_src": bars_src, "bars_port": bars_port, "series_last": last, "rule": rule, "seed": seed, "installed_at": datetime.fromtimestamp(_at(day0, 9, 0) - 30 * 86400, tz=UTC).isoformat(),
            "steps": steps, "ivs": ivs, "spot": spot_now}


# -- the port side -------------------------------------------------------------------------------------
class _Opts:
    def __init__(self):
        self.rows, self.legq = {}, {}

    def chain(self, u, dte_min=None, dte_max=None, typ=None, now=None):
        rows = self.rows.get(u)
        if rows is None:
            return None
        d0 = datetime.fromtimestamp(now, tz=UTC).date()
        out = []
        for r in rows:
            dte = (date.fromisoformat(r["exp"]) - d0).days
            if (dte_min is not None and dte < dte_min) or (dte_max is not None and dte > dte_max):
                continue
            out.append(_desk_row(r))
        return out

    def quotes(self, occs):
        return {o: self.legq[o] for o in occs if o in self.legq}


def _desk_row(r):
    row = {"symbol": r["symbol"], "underlying": r["u"], "expiration": r["exp"], "type": r["right"],
           "strike": float(r["strike"]), "bid": r["bid"], "ask": r["ask"], "last": None, "iv": None,
           "delta": r["delta"], "t": 0, "source": "harness"}
    if r["as"] != BIG:
        row.update(bid_size=r["bs"], ask_size=r["as"])
    return row


def _leg_price(seq, i, occ, st):
    """a held contract's quote at step i: priced from the step's underlying quote (deterministic per seed/step/OCC)."""
    rng = random.Random(int(hashlib.sha256(f"{seq['seed']}:{i}:{occ}".encode()).hexdigest()[:12], 16))
    u = occ_parse(occ)[0]
    q = st["uquotes"].get(u)
    spot = (q["bid"] + q["ask"]) / 2 if q else seq["series_last"][i][u]
    return _price_leg(rng, occ, spot, st["now"], seq["ivs"][u], st["sized"])


def run_port(seq):
    cfg = next(c for c in FUNDED if c["id"] == seq["rule"])
    sl = AO.AusarOptionBook(cfg)
    opts = _Opts()
    sl.bind(type("E", (), {"hub": type("H", (), {"options": opts})()})())
    cash = float(cfg["initial_capital"])
    positions = {}
    state = {"installed_at": seq["installed_at"]}
    out = []
    for i, st in enumerate(seq["steps"]):
        now = st["now"]
        st["leg_quotes"] = {}
        for inst in positions:
            if inst.startswith("OPT:"):
                st["leg_quotes"][inst[4:]] = _leg_price(seq, i, inst[4:], st)
        opts.rows = st["chains"]
        opts.legq = {}
        for occ, q in st["leg_quotes"].items():
            if q["bid"] is not None:
                opts.legq[occ] = dict(q, t=0) if q["as"] == BIG else dict(q, bid_size=q["bs"], ask_size=q["as"], t=0)
        for u, rows in st["chains"].items():
            for r in rows:
                if r["bid"] is not None:
                    opts.legq.setdefault(r["symbol"], _desk_row(r))
        quotes = {u: {"bid": q["bid"], "ask": q["ask"], "last": None, "t": now} for u, q in st["uquotes"].items()}
        for inst, p in positions.items():
            if inst.startswith("OPT:"):
                q = opts.legq.get(inst[4:])
                p["mark"] = (q["bid"] + q["ask"]) / 2 if q else p["avg"]
        bars = {u: bl[:st["nb"]] for u, bl in seq["bars_port"].items()}
        view = View(now=now, session=datetime.fromtimestamp(now, tz=ET).date().isoformat(), bars={"1d": bars},
                    quotes=quotes, positions={k: dict(v) for k, v in positions.items()}, equity=cash, cash=cash,
                    state=json.loads(json.dumps(state)), extra={"pending_orders": [], "closed_trades": []})
        intents = sl.signal(view)
        state = sl.update_state(view, intents) or state
        step = {"opens": [], "closes": [], "core": [], "blockers": [], "obs": []}
        for it in intents:
            if it.kind == "signal":
                if " blocked: " in it.reason:
                    step["blockers"].append(it.reason.split(" blocked: ", 1)[1])
                elif (it.meta or {}).get("observation"):
                    step["obs"].append([it.symbol, bool(it.meta["observation"]["pass"])])
                continue
            if it.kind == "enter" and it.asset == "equity":
                step["core"].append({"sid": it.signal_key, "sym": it.symbol, "qty": int(it.qty)})
                if st["fill_open"]:
                    q = st["uquotes"][it.symbol]
                    cash -= it.qty * q["ask"] * 1.0015
                    positions["EQ:" + it.symbol] = {"qty": it.qty, "avg": q["ask"], "opened_at": now,
                                                    "meta": {"position_meta": dict(it.meta.get("position_meta") or {})},
                                                    "mark": q["bid"]}
                continue
            pm = (it.meta or {}).get("position_meta") or {}
            pkg = (it.meta or {}).get("ausar_package")
            if it.kind == "enter":
                legs = [[it.symbol, 1]] if it.asset == "option" else \
                    [[l.symbol, 1 if l.side == "buy" else -1] for l in it.legs]
                step["opens"].append({"sid": it.signal_key, "pkg": pkg, "legs": sorted(legs), "qty": int(it.qty),
                                      "reason": it.reason.split(": ", 1)[1], "net": round(it.order.limit_price, 4),
                                      "risk_budget": pm.get("risk_budget"), "entry_spot": pm.get("entry_spot"),
                                      "exit_session": pm.get("exit_session"),
                                      "expiry_exit_session": pm.get("expiry_exit_session")})
                if st["fill_open"]:
                    n = int(it.qty)
                    fee = 0.65 * len(legs)
                    cash -= (it.order.limit_price * 100 + fee) * n
                    for sym, ratio in legs:
                        positions["OPT:" + sym] = {"qty": float(n * ratio), "avg": 0.0, "opened_at": now, "mark": 0.0,
                                                   "meta": {"ausar_package": pkg, "position_meta": pm,
                                                            "underlying": it.meta.get("underlying"),
                                                            "group": it.meta.get("group")}}
            else:
                held = [(inst, p) for inst, p in positions.items() if (p.get("meta") or {}).get("ausar_package") == pkg]
                legs = sorted([inst[4:], 1 if p["qty"] > 0 else -1] for inst, p in held)
                n = int(min(abs(p["qty"]) for _, p in held)) if held else 0
                net = it.price_hint if it.asset == "option" else -it.order.limit_price
                step["closes"].append({"sid": it.signal_key, "pkg": pkg, "legs": legs, "qty": n,
                                       "reason": it.reason.split(" exit: ", 1)[1], "net": round(net or 0.0, 4)})
                if st["fill_close"]:
                    cash += ((net or 0.0) * 100 - 0.65 * len(legs)) * n
                    for inst, _ in held:
                        positions.pop(inst)
        step["blockers"] = sorted(set(step["blockers"]))
        step["obs"] = sorted(step["obs"])
        step["attempts"] = {k: bool(v.get("consumed")) for k, v in (state.get("option_entry_attempts") or {}).items()}
        step["cash"] = round(cash, 6)
        out.append(step)
    return out


def _norm(kind, v):
    """risk_budget / entry_spot are Decimal strings: compared by value (their digits depend on the NAV string)."""
    if kind != "opens":
        return v
    return [dict(o, risk_budget=round(float(o["risk_budget"]), 9), entry_spot=round(float(o["entry_spot"]), 9))
            for o in v]


def _calendar_table():
    out = {}
    for d in _sessions_between(date(2019, 1, 1), date(2028, 12, 31)):
        out[d.isoformat()] = [cal.session_open(d), cal.session_close(d)]
    return out


def _payload(seqs, mons):
    rules = os.path.join(os.path.dirname(vo.__file__), "..", "strategies", "r19", "options_rules.json")
    body = open(rules, "rb").read()
    assert hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest() == AO.SOURCE["rules_blob"]
    return {"rules_path": os.path.abspath(rules), "calendar": _calendar_table(), "quiet": sorted(QUIET), "monitors": mons,
            "seqs": [{"rule": s["rule"], "installed_at": s["installed_at"], "bars": s["bars_src"],
                      "steps": [{"now": st["now"], "fill_open": st["fill_open"], "fill_close": st["fill_close"],
                                 "nb": st["nb"], "bars_observed_at": st["bars_observed_at"], "chains": st["chains"],
                                 "leg_quotes": st["leg_quotes"], "uquotes": st["uquotes"], "exercise": st["exercise"]}
                                for st in s["steps"]]} for s in seqs]}


BATCH = int(os.environ.get("AUSAR_OPT_BATCH", "50"))


def run():
    mons = []
    rng = random.Random(77)
    for rule in MONITORS:
        for _ in range(4):
            d = rng.choice(_sessions_between(date(2025, 2, 3), date(2026, 11, 30)))
            mons.append({"rule": rule, "now": _at(d, rng.randint(0, 23), rng.randint(0, 59))})
    diffs, steps, old_mon = [], 0, None
    stats = {"sequences": 0, "steps": 0, "entries": 0, "exits": {}, "core": 0, "blocked_steps": 0,
             "signal_obs": 0, "passes": 0, "blockers": {}, "by_family": {}, "sized_sequences": 0}
    for b0 in range(0, N_SEQ, BATCH):
        seqs = [make_sequence(9100 + i) for i in range(b0, min(N_SEQ, b0 + BATCH))]
        ports = [run_port(seq) for seq in seqs]      # also fixes each step's held-leg quotes (shared with the source)
        old = old_run(SOURCE_SCRIPT, _payload(seqs, mons if old_mon is None else []), timeout=7200, tree=SRC)
        if old_mon is None:
            old_mon = old["monitors"]
        stats["sequences"] += len(seqs)
        stats["sized_sequences"] += sum(1 for s in seqs if s["steps"] and s["steps"][0]["sized"])
        for seq, src_steps, port_steps in zip(seqs, old["seqs"], ports):
            fam = next(c for c in FUNDED if c["id"] == seq["rule"])["family"]
            stats["by_family"][fam] = stats["by_family"].get(fam, 0) + len(port_steps)
            for i, (a, b) in enumerate(zip(src_steps, port_steps)):
                steps += 1
                stats["entries"] += len(a["opens"])
                stats["core"] += len(a["core"])
                stats["signal_obs"] += len(a["obs"])
                stats["blocked_steps"] += 1 if a["blockers"] else 0
                for r in a["blockers"]:
                    stats["blockers"][r] = stats["blockers"].get(r, 0) + 1
                stats["passes"] += sum(1 for o in a["obs"] if o[1])
                for c in a["closes"]:
                    stats["exits"][c.get("reason", "settle")] = stats["exits"].get(c.get("reason", "settle"), 0) + 1
                bad = [k for k in ("opens", "closes", "core", "blockers", "obs", "attempts")
                       if _norm(k, a[k]) != _norm(k, b[k])]
                if abs(a["cash"] - b["cash"]) > 1e-4:
                    bad.append("cash")
                if bad:
                    diffs.append({"rule": seq["rule"], "seed": seq["seed"], "step": i,
                                  "at": datetime.fromtimestamp(seq["steps"][i]["now"], tz=ET).isoformat(),
                                  "what": bad, "source": {k: a[k] for k in bad}, "port": {k: b[k] for k in bad}})
        del seqs, ports, old
    old = {"monitors": old_mon}
    stats["steps"] = steps
    mon_diffs = []
    for m, r in zip(mons, old["monitors"]):
        cfg = next(c for c in vo.register() if c["id"] == m["rule"])
        sl = AO.AusarOptionMonitor(cfg)
        (it,) = sl.signal(View(now=m["now"], session=datetime.fromtimestamp(m["now"], tz=ET).date().isoformat()))
        port = {"observations": [it.meta["observation"]], "blockers": it.meta["blockers"], "intents": 0}
        if json.loads(json.dumps(port)) != json.loads(json.dumps(r)):
            mon_diffs.append({"monitor": m["rule"], "source": r, "port": port})
    res = {"sleeve": "ausar_options", "cases": steps + len(mons), "identical": steps - len(diffs) + len(mons) - len(mon_diffs),
           "diffs": (diffs + mon_diffs)[:10], "n_diffs": len(diffs) + len(mon_diffs), "stats": stats,
           "monitor_cases": len(mons), "monitor_note": "6 static diagnostics x 4 clocks: no producer feeds their inputs, "
                                                       "so the decision space is the 6 cards",
           "scope": "recovery, core_reserve, the 6 monitors, and pead / opening_gamma / tensor_leaps with their "
                    "producers' inputs absent; the producer families: docs/receipts/parity/ausar_option_producers.json",
           "source_tree": SRC, "source_commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
           "named_divergences_in_cases": {"N1": "applied identically on both sides (qualified inputs)",
                                          "N2": "unbounded sizes on both sides, or the same carried sizes",
                                          "N4": "harness fill model credits proceeds at once on both sides",
                                          "N3/N6/N7": "engine execution only: not exercised by the decision harness"},
           "method": "multi-step sequences (flat -> entry window -> fills -> exits over the following sessions); each "
                     "side carries its own book, attempts and outcomes"}
    write_receipt("ausar_options", res)
    return res
