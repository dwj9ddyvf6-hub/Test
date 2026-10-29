"""ausar_options producer families — XSP calm / graded (xsp_pcs), opening gamma, PEAD, Tensor LEAPS — the SOURCE
evaluator path vs the port, on deterministic random multi-step sequences (each side its own book and state).

  SOURCE  the source runtime's snapshot path and evaluator, in its own tree (as tools/parity/ausar_options.py:
          r19_data.Collector._calendar -> r19_option_data.normalize_contract / normalize_quote -> enrich_snapshot ->
          r19_cli.bounded_snapshot -> r19_options.evaluate, prepare_package accounting incl. collateral), with each
          family's input built there by an INDEPENDENT implementation of its research definition:
            xsp_pcs        weekly bars = pandas W-FRI resample of the S&P 500 sessions / 10; ATR by the evaluator's
                           _weekly_atr14; adjacent puts at prior close - 1 ATR; prior digitals = the research CSV
                           (pandas-free reader) + the side's own weekly _xsp_digital readings;
            opening_gamma  R5 events by the research script itself (run_r5_overnight_gap_long.last2h, numpy
                           quantile over the trailing 252 with 126 minimum), seeded with the derived research
                           history; the next open's events from the first 5-minute bar and the quote mid;
            pead           events from the calendar rows and their observation clocks, history surprises from
                           pandas closes (causal_pead.py: close(t+1)/close(t-1) - SPY), every event of the
                           session three sessions back handed to the evaluator;
            tensor_leaps   the G4 events as published by the bridge (shared input), scoped by bounded_snapshot.
  PORT    AusarOptionBook.signal on engine-shaped Views carrying the raw data: ^GSPC daily bars, 30-minute and
          5-minute bars, the PEAD producer (desk/feedlib/ausar_pead.run, twice: two evenings before the event
          and the evening before the entry) and the bridge feed — each producer computes its input itself.

Compared per step: package entries / exits (as tools/parity/ausar_options.py), the frozen attempt ledger, cash,
non-quiet blockers (PEAD: those not tied to one event — N11 hands the evaluator only the producer's pre-evaluated
passing events, so the source's per-event blockers / failing observations for the others are not compared) and
passing signal observations. XSP index fees (N8) on both sides; the evaluator's 'settle' (N6) is replaced on both
sides by the harness settling at the Friday S&P 500 close / 10."""
import hashlib
import json
import os
import random
import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.contract import View
from desk.data.options import occ_parse, occ_symbol
from desk.feedlib import ausar_pead as AP
from desk.sleeves.families import ausar_options as AO
from desk.util import ET
from desk.vendor.ausar_r19 import r19_options as vo

from . import ausar_options as H
from . import old_run, write_receipt

SRC = H.SRC
R5_SCRIPT = os.environ.get("R5_SCRIPT", "/home/user/br/midna@main/workspace/alpaca-swing-desk/desk/research/resurrection/"
                           "code/run_r5_overnight_gap_long.py")
R5_SCRIPT_BLOB = "63e5497cad4faf722bd82d0ff0783ede5a9e59b8"
N_SEQ = int(os.environ.get("AUSAR_PROD_SEQS", "240"))
BATCH = int(os.environ.get("AUSAR_PROD_BATCH", "20"))
UTC = timezone.utc
QUIET = set(AO.QUIET_BLOCKERS)
FUNDED = {c["id"]: c for c in vo.register() if not c.get("monitor_only")}
BY_FAM = {}
for _c in FUNDED.values():
    BY_FAM.setdefault(_c["family"], []).append(_c["id"])
FAMILIES = ("xsp_pcs", "opening_gamma", "pead", "tensor_leaps")

SOURCE_SCRIPT = H.SOURCE_SCRIPT.split("\nout = []\n")[0] + r'''
import csv as _csv, importlib.util, os as _os
import numpy as np
from zoneinfo import ZoneInfo
ETZ = ZoneInfo('America/New_York')
spec = importlib.util.spec_from_file_location('r5research', PAYLOAD['r5_script'])
R5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R5)
SEED = json.load(open(PAYLOAD['r5_seed']))
DIG = []
for r in _csv.DictReader(open(PAYLOAD['digitals_csv'])):
    if 0 < Decimal(r['implied']) < 1:
        d = datetime.fromisoformat(r['entry_d'])
        DIG.append({'week_end': r['week_end'], 'value': r['implied'], 'source_sha256': 'research-csv',
                    'available_at': datetime(d.year, d.month, d.day, 10, 0, tzinfo=ETZ).isoformat()})

def xsp_contract(r, now_iso):
    reg = {r['symbol']: {'verified': True, 'source_sha256': 'harness-deliverable', 'settlement': 'cash_PM',
                         'schema': 'aster-option-deliverable-v1',
                         'deliverable': {'shares': 0, 'cash_settlement_multiplier': 100, 'settlement_index': 'XSP'}}}
    raw = {'id': 'id-' + r['symbol'], 'symbol': r['symbol'], 'root_symbol': 'XSP', 'underlying_symbol': 'XSP',
           'expiration_date': r['exp'], 'strike_price': r['strike'], 'type': r['right'], 'multiplier': '100',
           'style': 'european', 'status': 'active', 'tradable': True}
    c = OD.normalize_contract(raw, {'received_at': now_iso, 'source_sha256': 'harness-census'}, reg)
    c['delta'] = r['delta']
    c['greeks_received_at'] = c['greeks_market_at'] = now_iso
    return c

def weekly(daily, session):
    df = pd.DataFrame(daily)
    df['date'] = pd.to_datetime(df['d'])
    df = df[df['date'] < pd.Timestamp(session)]
    df['wk'] = df['date'].dt.to_period('W-FRI')
    df = df[df['wk'] != pd.Timestamp(session).to_period('W-FRI')]
    g = df.groupby('wk').agg(o=('o', 'first'), h=('h', 'max'), l=('l', 'min'), c=('c', 'last'), we=('d', 'last'))
    rows = []
    for _, w in g.tail(260).iterrows():
        px = {k: str(D(repr(float(w[k]))) / 10) for k in ('o', 'h', 'l', 'c')}
        rows.append({'week_end': w['we'], 'open': px['o'], 'high': px['h'], 'low': px['l'], 'close': px['c'],
                     'complete': True, 'source_sha256': 'pandas-W-FRI',
                     'usable_after': datetime.fromtimestamp(CAL[w['we']][1] + 900, tz=UTC).isoformat()})
    return rows

def xsp_state(s, daily, recorded, now):
    c = s['calendar']
    bars = weekly(daily, c['session'])
    have = {x['week_end'] for x in DIG}
    st = {'weekly_bars': bars, 'prior_digitals': DIG + [x for x in recorded if x['week_end'] not in have],
          'adjacent_put_symbols': [], 'source_sha256': 'src',
          'usable_after': max([b['usable_after'] for b in bars]) if bars else datetime.fromtimestamp(0, tz=UTC).isoformat()}
    try:
        atr, prior = RO._weekly_atr14(bars, now, c['session'])
        puts = [x for x in s['option_contracts'] if x['underlying'] == 'XSP' and x['right'] == 'put'
                and x['expiry'] == c['weekly_PM_expiry']]
        k = min(puts, key=lambda x: (abs(D(x['strike']) - (prior - atr)), x['symbol']))
        w = max([x for x in puts if D(x['strike']) < D(k['strike'])], key=lambda x: D(x['strike']))
        st['adjacent_put_symbols'] = [w['symbol'], k['symbol']]
    except (ValueError, KeyError, TypeError, ArithmeticError):
        pass
    return st

def r5_events(bars30, session):
    out = []
    for sym in sorted(bars30):
        b30 = {}
        for b in bars30[sym]:
            dt = datetime.fromtimestamp(b['t'], tz=UTC).astimezone(ETZ)
            b30[(dt.date().isoformat(), dt.strftime('%H:%M'))] = b
        seed = SEED.get(sym) or []
        last = seed[-1][0] if seed else ''
        hist = [v for d, v in seed if d < session]
        live = {d: R5.last2h(b30, d) for d in sorted({d for d, _ in b30}) if d > last}
        hist += [v for d, v in sorted(live.items()) if v is not None and d < session]
        today = live.get(session)
        if today is None or len(hist) < 126:
            continue
        p80 = float(np.quantile(hist[-252:], 0.80))
        if today >= p80:
            out.append({'symbol': sym, 'signal_at': datetime.fromtimestamp(CAL[session][1], tz=UTC).isoformat()})
    return out

def opening(st, r5, today, now_iso):
    if not r5 or r5['session'] != today['previous_session']:
        return []
    opened = CAL[today['session']][0]
    out = []
    for e in sorted(r5['events'], key=lambda x: x['symbol']):
        bar, q = st['open5'].get(e['symbol']), st['uquotes'].get(e['symbol'])
        if not bar or not q:
            continue
        ev = {'event_id': e['symbol'] + ':' + r5['session'] + ':R5', 'symbol': e['symbol'], 'session': today['session'],
              'prior_afternoon_session': r5['session'],
              'first_5min_start_at': datetime.fromtimestamp(opened, tz=UTC).isoformat(),
              'first_5min_end_at': datetime.fromtimestamp(opened + 300, tz=UTC).isoformat(),
              'first_5min_received_at': now_iso, 'first_5min_complete': True,
              'first_5min_return': repr(bar['c'] / bar['o'] - 1), 'first_5min_low': repr(bar['l']),
              'observed_break_price': repr((q['bid'] + q['ask']) / 2), 'break_market_at': now_iso,
              'break_received_at': now_iso, 'R5_signal_at': e['signal_at'], 'R5_received_at': r5['received_at'],
              'causal_R5_prior_afternoon': True, 'source_sha256': 'src-opening'}
        out.append(ev)
    return out

def bound(d, bucket):
    y, m, dd = map(int, d.split('-'))
    return datetime(y, m, dd, 16 if bucket == 'time-after-hours' else 0, 0, tzinfo=ETZ)

def pead_inputs(seq, today, now):
    """events of every calendar row; history: the resolved surprises (causal_pead.py) on pandas closes."""
    closes = {s: pd.Series({b['d']: b['c'] for b in bl}) for s, bl in seq['bars'].items()}
    sessions = DATES
    evs, hist = [], []
    q0 = datetime(int(today['session'][:4]), 3 * ((int(today['session'][5:7]) - 1) // 3) + 1, 1).date()
    lo = q0.replace(year=q0.year - 1).isoformat()
    for d, rows in sorted(seq['pead_rows'].items()):
        if d not in CAL:
            continue
        for r in rows:
            first = datetime.fromtimestamp(r['first_seen'], tz=UTC).astimezone(ETZ)
            ann = bound(d, r['time'])
            e = {'event_id': r['symbol'] + ':' + d, 'symbol': r['symbol'], 'event_date': d,
                 'first_published_at': first.isoformat(), 'announcement_at': ann.isoformat(), 'source_sha256': 'src'}
            evs.append(e)
            i = sessions.index(d)
            a, b = sessions[i - 1], sessions[i + 1]
            cs, sp = closes.get(r['symbol']), closes['SPY']
            if d < lo or d >= today['session'] or cs is None or a not in cs or b not in cs or d not in cs \
                    or a not in sp or b not in sp or CAL[b][1] > now.timestamp():
                continue
            hist.append({'event_id': e['event_id'], 'symbol': r['symbol'], 'event_date': d,
                         'surprise': repr(float(cs[b]) / float(cs[a]) - float(sp[b]) / float(sp[a])),
                         'signal_available_at': datetime.fromtimestamp(CAL[b][1], tz=UTC).isoformat(),
                         'first_published_at': (first if first <= ann else ann).isoformat(), 'source_sha256': 'src'})
    return evs, hist

out = []
for seq in PAYLOAD['seqs']:
    cfg = next(c for c in RO.register() if c['id'] == seq['rule'])
    fam = cfg['family']
    fee = PAYLOAD['xsp_fees'] if fam == 'xsp_pcs' else dict(OD.DEFAULT_PAPER_OPTION_FEES)
    book = {'id': cfg['id'], 'strategy_id': cfg['id'], 'config': cfg, 'initial_capital': cfg['initial_capital'],
            'cash': D(str(cfg['initial_capital'])), 'collateral': '0', 'enabled': True,
            'installed_at': seq['installed_at'], 'state': {}, 'positions': {}}
    outcomes, res_steps, recorded, r5 = [], [], [], None
    for st in seq['steps']:
        now = datetime.fromtimestamp(st['now'], tz=UTC)
        now_iso = now.isoformat()
        for sett in st.get('settle', []):                     # harness settlement (N6), both sides alike
            for pkg, p in list(book['positions'].items()):
                legs = p['metadata'].get('legs') or []
                if not legs or legs[0]['expiry'] > sett['expiry']:
                    continue
                value = 0.0
                for l in legs:
                    k = float(l['strike'])
                    intr = max(0.0, sett['px'] - k) if l['right'] == 'call' else max(0.0, k - sett['px'])
                    value += intr * int(l['ratio']) * 100
                book['positions'].pop(pkg)
                book['cash'] = D(str(book['cash'])) + D(str(round(value, 10))) * int(p['quantity'])
                book['collateral'] = str(D(book['collateral']) - D(p['metadata']['collateral_per_package']) * int(p['quantity']))
        today, metadata, _prev, _cal = RD.Collector._calendar(None, now)
        by_session = {x['session']: x for x in metadata}
        snapshot = {'asof': now_iso, 'now': now_iso, 'calendar': today, 'calendar_sessions': metadata, 'histories': {}}
        for sym, allbars in seq.get('dbars', {}).items():
            bars = [b for b in allbars if b['t'][:10] < today['session']]
            item = {'value': {'bars': bars}, 'observed_at': now_iso, 'source_sha256': 'harness-bars-' + sym}
            snapshot['histories'][sym] = RD.Collector._history_rows(item, by_session, now, 'RAW')
        obs = {'option_quotes': {}, 'underlying_quotes': {}, 'option_contracts': [], 'option_fees': fee,
               'complete_option_chains': []}
        for u, rows in st['chains'].items():
            obs['complete_option_chains'].append(u)
            for r in rows:
                obs['option_contracts'].append(xsp_contract(r, now_iso) if u == 'XSP' else contract(r, now_iso))
                if r['bid'] is not None:
                    obs['option_quotes'][r['symbol']] = quote(r['symbol'], r, now_iso, 'opra')
        for occ, q in st['leg_quotes'].items():
            if q['bid'] is not None:
                obs['option_quotes'][occ] = quote(occ, q, now_iso, 'opra')
        for sym, q in st['uquotes'].items():
            if sym == 'XSP':
                obs['underlying_quotes'][sym] = quote(sym, q, now_iso, 'official_index')
            else:
                obs['underlying_quotes'][sym] = dict(quote(sym, q, now_iso, 'sip'), actions_verified=True)
        s = OD.enrich_snapshot(snapshot, {'snapshot': obs, 'receipts': [], 'observed_at': now_iso})
        if not s.get('option_settlement_calendar_verified'):        # N5 on both sides (the table ends with 2026)
            nxt = DATES[bisect.bisect_right(DATES, today['session'])]
            s['option_cash_release_at'] = datetime.fromtimestamp(CAL[nxt][0], tz=UTC).isoformat()
            s['option_settlement_calendar_verified'] = True
        far = (now + timedelta(days=3650)).date().isoformat()
        s['exercise_checks'] = {u: {'verified': True, 'source_sha256': 'harness-exercise', 'received_at': now_iso,
                                    'valid_through': far, 'assignment_alert': False} for u in st['exercise']}
        et = now.astimezone(ETZ)
        if fam == 'xsp_pcs' and s['calendar'].get('first_session_of_week') and (10, 0) <= (et.hour, et.minute) < (10, 5) \
                and not any('legs' in p['metadata'] for p in book['positions'].values()):
            s['xsp_state'] = xsp_state(s, seq['gspc'], recorded, now)
            try:
                v = RO._xsp_digital(s, s['xsp_state'], now)
                wk = s['calendar']['weekly_PM_expiry']
                if 0 < v < 1 and not any(x['week_end'] == wk for x in recorded):
                    recorded.append({'week_end': wk, 'value': str(v), 'available_at': now_iso, 'source_sha256': 'src'})
            except (ValueError, KeyError, TypeError, ArithmeticError):
                pass
        if fam == 'opening_gamma':
            if st.get('bars30') is not None and (r5 is None or r5['session'] != today['session']) \
                    and now.timestamp() >= CAL[today['session']][1] + PAYLOAD['r5_delay_s']:
                r5 = {'session': today['session'], 'received_at': now_iso, 'events': r5_events(st['bars30'], today['session'])}
            if (9, 35) <= (et.hour, et.minute) < (9, 45) and not any('legs' in p['metadata'] for p in book['positions'].values()):
                s['opening_reversal_events'] = opening(st, r5, s['calendar'], now_iso)
        if fam == 'pead':
            evs, hist = pead_inputs(seq, today, now)
            s['earnings_events'] = evs
            s['earnings_history'] = hist
        if fam == 'tensor_leaps':
            s['tensor_G4_events'] = st['g4']
            s['tensor_G4_exit_events'] = []
        book['cash'] = D(str(book['cash']))
        book['nav'] = str(float(book['cash']) + liquidation(book, s))
        book['cash'] = str(book['cash'])
        book['state']['last_evaluation'] = {'outcomes': outcomes}
        bs = CLI.bounded_snapshot(s, book)
        r = RO.evaluate(bs, book)
        if r.get('state') is not None:
            book['state'].update(r['state'])
        step = {'opens': [], 'closes': [], 'core': [],
                'blockers': sorted({str(b.get('reason')) for b in r['blockers'] if b.get('reason') and b.get('reason') not in QUIET}),
                'blockers_noevent': sorted({str(b.get('reason')) for b in r['blockers'] if b.get('reason')
                                            and b.get('reason') not in QUIET and not b.get('event_id')}),
                'blockers_ev': sorted({(b['event_id'], str(b.get('reason'))) for b in r['blockers']
                                       if b.get('event_id') and b.get('reason') not in QUIET}),
                'obs': sorted([o['symbol'], bool(o['pass'])] for o in r['observations'] if 'pass' in o and o.get('symbol')),
                'r5': [e['symbol'] for e in (r5 or {}).get('events', [])] if fam == 'opening_gamma' else None,
                'pead_events': len(bs.get('earnings_events') or []),
                'recorded': [[x['week_end'], x['value']] for x in recorded] if fam == 'xsp_pcs' else None}
        outcomes = []
        cash = D(book['cash'])
        for it in r['intents']:
            if it['action'] == 'open':
                m = it['metadata']
                step['opens'].append({'sid': it['signal_id'], 'pkg': it['symbol'],
                                      'legs': sorted([l['symbol'], int(l['ratio'])] for l in it['legs']),
                                      'qty': int(it['quantity']), 'reason': it['reason'],
                                      'net': natural(it['legs'], bs['option_quotes'], True),
                                      'risk_budget': m['risk_budget'], 'entry_spot': m.get('entry_spot'),
                                      'exit_session': m['exit_session'], 'expiry_exit_session': m.get('expiry_exit_session')})
                if st['fill_open']:
                    pp = RO.prepare_package(it, bs, book)
                    cash += D(pp['cash_delta'])
                    book['collateral'] = str(D(book['collateral']) + D(pp['collateral_delta']))
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
                    book['collateral'] = str(D(book['collateral']) + D(pp['collateral_delta']))
                    book['positions'].pop(it['symbol'])
        book['cash'] = str(cash)
        step['attempts'] = {k: bool(v.get('consumed')) for k, v in book['state'].get('option_entry_attempts', {}).items()}
        step['cash'] = round(float(cash), 6)
        res_steps.append(step)
    out.append(res_steps)
print(json.dumps({'seqs': out}))
'''


# -- markets ----------------------------------------------------------------------------------------------------------
def _sessions(a, b):
    return H._sessions_between(a, b)


def _walk(rng, days, start, vol):
    px, out = start, []
    for d in days:
        r = rng.gauss(0.0003, vol)
        o = px * (1 + rng.gauss(0, vol / 3))
        c = max(1.0, px * (1 + r))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
        out.append({"d": d.isoformat(), "o": round(o, 2), "h": round(max(h, o, c), 2), "l": round(min(lo, o, c), 2),
                    "c": round(c, 2), "v": int(rng.uniform(2e5, 3e6))})
        px = c
    return out


def _quote(rng, fair, sized):
    spread = max(0.01, round(max(fair, 0.05) * rng.uniform(0.004, 0.05), 2))
    bid = max(0.0, round(fair - spread / 2, 2))
    return bid, round(max(bid + spread, 0.01), 2)


def _rows(rng, u, spot, now, expiries, strikes, rights, iv, sized=False, root=None):
    rows = []
    for e in expiries:
        T = max(1e-6, (cal.session_close(e) - now) / (365 * 86400))
        for k in strikes:
            for right in rights:
                fair, delta = H._bs(spot, float(k), T, iv * (1 + 0.6 * max(0.0, (spot - k) / spot)), right)
                bid, ask = _quote(rng, fair, sized)
                occ = occ_symbol(root or u, e.isoformat(), right, k)
                r = {"symbol": occ, "u": u, "root": root or u, "exp": e.isoformat(), "strike": str(k), "right": right,
                     "delta": round(delta, 4), "bid": bid, "ask": ask, "bs": H.BIG, "as": H.BIG}
                x = rng.random()
                if x < 0.015:
                    r["bid"] = None
                elif x < 0.025:
                    r["delta"] = None
                if sized:
                    r["bs"], r["as"] = rng.randint(1, 30), rng.randint(1, 30)
                rows.append(r)
    return rows


def _at(d, h, m, s=0):
    return H._at(d, h, m, s)


def _base(rule, seed, installed):
    return {"rule": rule, "seed": seed, "installed_at": installed, "steps": [], "dbars": {}, "spot": {}, "ivs": {}}


def _step(t, **kw):
    st = {"now": t, "fill_open": True, "fill_close": True, "chains": {}, "uquotes": {}, "leg_quotes": {},
          "exercise": [], "sized": False}
    st.update(kw)
    return st


def make_xsp(rng, seed):
    rule = rng.choice(BY_FAM["xsp_pcs"])
    mondays = [d for d in _sessions(date(2025, 3, 3), date(2026, 12, 14))
               if cal.prev_trading_day(d).isocalendar()[:2] != d.isocalendar()[:2]]
    w0 = rng.choice(mondays)
    weeks = [w0] + ([mondays[mondays.index(w0) + 1]] if rng.random() < 0.4 and mondays.index(w0) + 1 < len(mondays) else [])
    last = weeks[-1]
    days = _sessions(w0 - timedelta(days=2000), last + timedelta(days=6))
    gspc = _walk(rng, days, rng.uniform(4000, 6800), rng.uniform(0.006, 0.013))
    seq = _base(rule, seed, datetime.fromtimestamp(_at(w0, 9, 0) - 20 * 86400, tz=UTC).isoformat())
    seq["gspc"] = gspc
    iv = rng.uniform(0.04, 0.12) if rng.random() < 0.6 else rng.uniform(0.12, 0.28)   # calm and hot weeks
    for wi, mon in enumerate(weeks):
        c = AO.session_calendar(_at(mon, 10, 0))
        expiry = date.fromisoformat(c["weekly_PM_expiry"])
        prev = [b for b in gspc if b["d"] < mon.isoformat()][-1]
        spot = round(prev["c"] / 10 * (1 + rng.gauss(0, 0.004)), 2)
        strikes = list(range(int(spot * 0.86), int(spot * 1.01) + 1))
        times = sorted({_at(mon, 10, 0, rng.randint(0, 40)), _at(mon, 10, 1, rng.randint(0, 59)),
                        _at(mon, 10, rng.randint(2, 4), rng.randint(0, 59))})
        if rng.random() < 0.3:
            times.insert(0, _at(mon, 9, 59, 30))
        if rng.random() < 0.3:
            times.append(_at(mon, 10, 5, 10))
        settle = []
        if wi:
            settle = [{"week": weeks[wi - 1].isoformat()}]
        for j, t in enumerate(times):
            rows = _rows(rng, "XSP", spot, t, [expiry], strikes, ("put",), iv, root="XSP")
            for r in rows:
                if rng.random() < 0.004:
                    r["bid"] = None
            st = _step(t, chains={"XSP": rows}, uquotes={"XSP": {"bid": spot, "ask": spot, "bs": H.BIG, "as": H.BIG}},
                       exercise=["XSP"], spot=spot, settle=settle if j == 0 else [])
            seq["steps"].append(st)
    seq["weeks"] = [w.isoformat() for w in weeks]
    return seq


def make_gamma(rng, seed):
    rule = rng.choice(BY_FAM["opening_gamma"])
    days = _sessions(date(2026, 10, 7), date(2026, 12, 28))
    D0 = rng.choice(days)
    N1 = cal.next_trading_day(D0)
    syms = rng.sample(AO.R5_UNIVERSE, rng.randint(1, 3))
    seq = _base(rule, seed, datetime.fromtimestamp(_at(D0, 9, 0) - 10 * 86400, tz=UTC).isoformat())
    live = _sessions(date(2026, 10, 5), D0)
    bars30, spot = {}, {}
    for s in syms:
        px = rng.uniform(8, 300)
        rows = []
        for d in live:
            for i in range(13):
                hh, mm = 9 + (30 + 30 * i) // 60, (30 + 30 * i) % 60
                px *= 1 + rng.gauss(0, 0.004)
                if d == D0 and (hh, mm) == (15, 30):
                    px *= 1 + rng.choice((0.0, 0.01, 0.03, 0.06, -0.01))
                rows.append({"t": _at(d, hh, mm), "o": round(px, 4), "h": round(px, 4), "l": round(px, 4),
                             "c": round(px, 4), "v": 1000})
        bars30[s] = rows
        spot[s] = round(px, 2)
    ac = cal.session_close(D0)
    seq["steps"].append(_step(ac + rng.choice((600, 1300, 1500, 2400)), bars30=bars30, exercise=list(syms)))
    if rng.random() < 0.15:
        seq["steps"].append(_step(ac + 2700, bars30=bars30, exercise=list(syms)))
    open5, uq = {}, {}
    for s in syms:
        o = round(spot[s] * (1 + rng.gauss(0, 0.004)), 2)
        c = round(o * (1 + (rng.uniform(-0.02, -0.001) if rng.random() < 0.65 else rng.uniform(0.0, 0.015))), 2)
        lo = round(min(o, c) * (1 - rng.uniform(0.0005, 0.006)), 2)
        hi = round(max(o, c) * (1 + rng.uniform(0.0, 0.004)), 2)
        open5[s] = {"t": cal.session_open(N1), "o": o, "h": hi, "l": lo, "c": c, "v": 1}
        m = round(lo * (1 - rng.uniform(0.0005, 0.01)) if rng.random() < 0.6 else (lo + c) / 2, 2)
        uq[s] = {"bid": round(m - 0.01, 2), "ask": round(m + 0.01, 2), "bs": H.BIG, "as": H.BIG}
    expiries = [e for e in H._expiries(N1 - timedelta(days=5)) if e >= N1][:3]
    dl = [N1] if N1.weekday() == 4 else []
    expiries = sorted(set(expiries + dl + [cal.next_trading_day(N1)]))
    iv = {s: rng.uniform(0.12, 0.45) for s in syms}
    for t in sorted({_at(N1, 9, 35, rng.randint(0, 50)), _at(N1, 9, rng.randint(36, 44), rng.randint(0, 59))}):
        chains = {}
        for s in syms:
            m = (uq[s]["bid"] + uq[s]["ask"]) / 2
            step_k = 0.5 if m < 25 else 1 if m < 100 else 5
            ks = [round(m * 0.9 + step_k * i, 1) for i in range(int(m * 0.2 / step_k) + 1)]
            ks = sorted({round(k / step_k) * step_k for k in ks if k > 0})
            ks = [int(k) if float(k).is_integer() else k for k in ks]
            chains[s] = _rows(rng, s, m, t, expiries, ks, ("put",), iv[s])
        seq["steps"].append(_step(t, chains=chains, uquotes=uq, open5=open5, exercise=list(syms)))
    for t in (_at(N1, 9, 59, 40), _at(N1, 10, 0, rng.randint(0, 50)), _at(N1, 10, 30)):
        seq["steps"].append(_step(t, uquotes=uq, open5=open5, exercise=list(syms)))
    seq["spot"] = spot
    seq["ivs"] = iv
    return seq


def make_pead(rng, seed):
    rule = rng.choice(BY_FAM["pead"])
    T = rng.choice(_sessions(date(2026, 2, 2), date(2026, 12, 15)))
    E = cal.prev_trading_day(T, 3)
    q0 = date(E.year, 3 * ((E.month - 1) // 3) + 1, 1)
    lo = AP.window_start(T)
    hist_days = [d for d in _sessions(lo, T - timedelta(days=1)) if d != E]
    names = ["H" + chr(65 + i // 26) + chr(65 + i % 26) for i in range(30)]       # 1-5 capitals: common tickers
    rows = {}
    for n in names:                                           # 12 reports each over the window
        for d in rng.sample(hist_days, 12):
            rows.setdefault(d.isoformat(), []).append({"symbol": n, "time": rng.choice(
                ("time-after-hours", "time-pre-market", "time-not-supplied"))})
    cur = ["CX" + chr(65 + i) for i in range(rng.randint(1, 3))]
    rows.setdefault(E.isoformat(), [])
    rows[E.isoformat()] = [r for r in rows[E.isoformat()] if r["symbol"] not in cur] + \
        [{"symbol": c, "time": rng.choice(("time-after-hours", "time-pre-market"))} for c in cur]
    days = _sessions(lo - timedelta(days=60), T + timedelta(days=20))
    dbars = {}
    for n in names + cur + ["SPY"]:
        series = _walk(rng, days, rng.uniform(4, 90) if n != "SPY" else 600.0, rng.uniform(0.008, 0.03))
        if n in cur:                                          # the reaction around the event
            k = [b["d"] for b in series].index(E.isoformat())
            shock = rng.choice((-0.16, -0.12, -0.08, -0.03, 0.02))
            for b in series[k:]:
                for f in ("o", "h", "l", "c"):
                    b[f] = round(b[f] * (1 + shock), 2)
            for b in series:
                b["v"] = int(rng.choice((1e4, 5e5, 2e6)))
        dbars[n] = series
    # the observation clocks: the producer ran two evenings before the event and the evening before the entry
    run1 = _at(cal.prev_trading_day(E, 2), 18, 0)
    run2 = _at(cal.prev_trading_day(T), 18, 0)
    seen = {}
    for d, rs in rows.items():
        for r in rs:
            r["first_seen"] = run1 if d <= (datetime.fromtimestamp(run1, tz=ET).date() + timedelta(days=AP.AHEAD_DAYS)).isoformat() \
                else run2
    seq = _base(rule, seed, datetime.fromtimestamp(_at(T, 9, 0) - 30 * 86400, tz=UTC).isoformat())
    seq["pead_rows"] = rows
    seq["runs"] = [run1, run2]
    seq["bars"] = {n: [{"d": b["d"], "c": b["c"]} for b in bl] for n, bl in dbars.items()}
    mid = lambda d: H._midnight_et(date.fromisoformat(d))
    seq["dbars"] = {n: [{"t": datetime.fromtimestamp(mid(b["d"]), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": b["o"],
                         "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]} for b in bl]
                    for n, bl in dbars.items() if n in cur or n == "SPY"}
    seq["dbars_port"] = {n: [{"t": mid(b["d"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                             for b in bl] for n, bl in dbars.items()}
    spot = {n: [b for b in dbars[n] if b["d"] < T.isoformat()][-1]["c"] for n in cur}
    expiries = [e for e in H._expiries(T) if 20 <= (e - T).days <= 40]
    iv = {n: rng.uniform(0.3, 0.9) for n in cur}
    uq = {n: {"bid": round(spot[n] - 0.01, 2), "ask": round(spot[n] + 0.01, 2), "bs": H.BIG, "as": H.BIG}
          for n in cur}
    uq["SPY"] = {"bid": 600.0, "ask": 600.02, "bs": H.BIG, "as": H.BIG}
    for t in sorted({_at(T, 9, 35, rng.randint(0, 59)), _at(T, 9, rng.randint(36, 39), rng.randint(0, 59))}):
        chains = {}
        for n in cur:
            step_k = 0.5 if spot[n] < 25 else 1
            ks = sorted({round(round(spot[n] * (0.85 + 0.01 * i) / step_k) * step_k, 2) for i in range(26)})
            ks = [int(k) if float(k).is_integer() else k for k in ks if k > 0]
            chains[n] = _rows(rng, n, spot[n], t, expiries, ks, ("put",), iv[n])
        seq["steps"].append(_step(t, chains=chains, uquotes=uq, exercise=list(cur) + ["SPY"]))
    ex = cal.next_trading_day(T, 9)
    for t in (_at(cal.next_trading_day(T, 2), 11, 0), _at(ex, 15, 54, 30), _at(ex, 15, 55, 20)):
        seq["steps"].append(_step(t, uquotes=uq, exercise=list(cur) + ["SPY"]))
    seq["spot"], seq["ivs"], seq["cur"] = spot, iv, cur
    return seq


def make_g4(rng, seed):
    rule = rng.choice(BY_FAM["tensor_leaps"])
    T = rng.choice(_sessions(date(2025, 6, 2), date(2026, 12, 15)))
    inst = _at(T, 9, 0) - rng.choice((40, 3, 1)) * 86400
    seq = _base(rule, seed, datetime.fromtimestamp(inst, tz=UTC).isoformat())
    names = ["G%d" % i for i in range(rng.randint(1, 3))]
    events = []
    for i, n in enumerate(names):
        sig = _at(cal.prev_trading_day(T), 16, 0) - rng.choice((0, 0, 0, 86400 * 60))
        dl = _at(T + timedelta(days=rng.choice((300, 360, 380))), 15, 55)
        while not cal.is_trading_day(datetime.fromtimestamp(dl, tz=ET).date()):
            dl -= 86400
        events.append({"symbol": n, "source_symbol": n, "event_id": "g4-%d-%d" % (seed, i),
                       "qualified_native_G4": rng.random() < 0.9, "source_sha256": "sha-%d" % i,
                       "available_at": datetime.fromtimestamp(sig + 3600, tz=UTC).isoformat(),
                       "signal_end": datetime.fromtimestamp(sig, tz=UTC).isoformat(),
                       "entry_session": T.isoformat() if rng.random() < 0.9 else cal.next_trading_day(T).isoformat(),
                       "original_G4_exit_at": datetime.fromtimestamp(dl, tz=UTC).isoformat(),
                       "original_G4_exit_session": datetime.fromtimestamp(dl, tz=ET).date().isoformat()})
    spot = {n: round(rng.uniform(2, 25), 2) for n in names}
    iv = {n: rng.uniform(0.4, 1.0) for n in names}
    leaps = [e for e in (date(T.year + 1, 12, 17), date(T.year + 2, 1, 21), date(T.year + 2, 6, 16),
                         date(T.year + 2, 12, 15)) if 540 <= (e - T).days <= 720]
    leaps = [e if cal.is_trading_day(e) else cal.prev_trading_day(e) for e in leaps]
    uq = {n: {"bid": round(spot[n] - 0.01, 2), "ask": round(spot[n] + 0.01, 2), "bs": H.BIG, "as": H.BIG}
          for n in names}
    for t in sorted({_at(T, 9, 35, rng.randint(0, 59)), _at(T, 9, rng.randint(36, 39), rng.randint(0, 59))}):
        chains = {}
        for n in names:
            ks = sorted({max(0.5, round(spot[n] * (0.4 + 0.05 * i) * 2) / 2) for i in range(16)})
            ks = [int(k) if float(k).is_integer() else k for k in ks]
            chains[n] = _rows(rng, n, spot[n], t, leaps, ks, ("call",), iv[n])
        seq["steps"].append(_step(t, chains=chains, uquotes=uq, exercise=list(names), g4=events))
    dl0 = min(datetime.fromisoformat(e["original_G4_exit_at"]).timestamp() for e in events)
    later = [_at(cal.next_trading_day(T, 3), 12, 0), dl0 - 120, dl0 + 30]
    chk = T + timedelta(days=365)
    while not cal.is_trading_day(chk):
        chk += timedelta(days=1)
    later += [_at(chk, 15, 54), _at(chk, 15, 55, 30)]
    for t in sorted(x for x in later if cal.is_rth(x)):
        seq["steps"].append(_step(t, uquotes=uq, exercise=list(names), g4=events))
    seq["spot"], seq["ivs"] = spot, iv
    return seq


MAKERS = {"xsp_pcs": make_xsp, "opening_gamma": make_gamma, "pead": make_pead, "tensor_leaps": make_g4}


def make_sequence(seed):
    rng = random.Random(seed)
    fam = FAMILIES[seed % len(FAMILIES)]
    seq = MAKERS[fam](rng, seed)
    seq["family"] = fam
    return seq


# -- the port side ---------------------------------------------------------------------------------------------------
class _Opts(H._Opts):
    def __init__(self):
        super().__init__()
        self.spots = {}

    def spot(self, u):
        return self.spots.get(u)


class _Hub:
    def __init__(self, bars):
        self.b = bars

    def bars(self, source, interval, symbols, n=300, cache_only=False):
        return {s: self.b[s][-n:] for s in symbols if s in self.b}


def _leg_price(seq, i, occ, st):
    rng = random.Random(int(hashlib.sha256(f"{seq['seed']}:{i}:{occ}".encode()).hexdigest()[:12], 16))
    root, exp, right, k = occ_parse(occ)
    u = "XSP" if root == "XSP" else root
    q = st["uquotes"].get(u)
    spot = (q["bid"] + q["ask"]) / 2 if q else (seq.get("spot") or {}).get(u, k)
    iv = (seq.get("ivs") or {}).get(u, 0.3)
    T = max(1e-6, (cal.session_close(exp) - st["now"]) / (365 * 86400))
    fair, _ = H._bs(spot, k, T, iv, right)
    bid, ask = _quote(rng, fair, False)
    return {"bid": bid, "ask": ask, "bs": H.BIG, "as": H.BIG}


def _settle_xsp(seq, week, positions_port, port_cash, src_settles, st):
    """harness settlement at the Friday S&P 500 close / 10 (N6), recorded for the source side too."""
    fri = AO.session_calendar(_at(date.fromisoformat(week), 10, 0))["weekly_PM_expiry"]
    px = next(b["c"] for b in seq["gspc"] if b["d"] == fri) / 10
    by_pkg = {}
    for inst, p in list(positions_port.items()):
        pkg = (p.get("meta") or {}).get("ausar_package")
        if inst.startswith("OPT:") and pkg:
            by_pkg.setdefault(pkg, []).append((inst, p))
    for pkg, legs in by_pkg.items():
        n = int(min(abs(p["qty"]) for _, p in legs))
        value = 0.0
        for inst, p in legs:
            _, _, right, k = occ_parse(inst[4:])
            intr = max(0.0, px - k) if right == "call" else max(0.0, k - px)
            value += intr * (1 if p["qty"] > 0 else -1) * 100
            positions_port.pop(inst)
        port_cash += value * n
    src_settles.append({"expiry": fri, "px": px})
    return port_cash


def run_port(seq, workdir):
    cfg = FUNDED[seq["rule"]]
    fam = cfg["family"]
    sl = AO.AusarOptionBook(cfg)
    opts = _Opts()
    root = None
    if fam == "pead":
        root = tempfile.mkdtemp(dir=workdir)
        rows = seq["pead_rows"]
        for run_at in seq["runs"]:
            def fetch(url, params=None, _at=run_at, **kw):
                return {"data": {"rows": [{"symbol": r["symbol"], "time": r["time"]} for r in rows.get(params["date"], [])
                                          if r["first_seen"] <= _at]}}
            AP.run(root, _Hub({n: [b for b in bl if b["t"] < cal.session_open(cal._as_date(run_at))]
                               for n, bl in seq["dbars_port"].items()}),
                   clock=lambda _at=run_at: _at, fetch=fetch, sleep=lambda s: None)
    sl.bind(type("E", (), {"hub": type("H", (), {"options": opts})(), "root": root})())
    cash = float(cfg["initial_capital"])
    positions, state, out = {}, {"installed_at": seq["installed_at"]}, []
    week_i = 0
    for i, st in enumerate(seq["steps"]):
        now = st["now"]
        st["src_settle"] = []
        if fam == "xsp_pcs" and st.get("settle"):
            cash = _settle_xsp(seq, seq["weeks"][week_i], positions, cash, st["src_settle"], st)
            week_i += 1
        st["leg_quotes"] = {}
        for inst in positions:
            if inst.startswith("OPT:"):
                st["leg_quotes"][inst[4:]] = _leg_price(seq, i, inst[4:], st)
        opts.rows = st["chains"]
        opts.spots = {"XSP": st["uquotes"]["XSP"]["bid"]} if "XSP" in st["uquotes"] else {}
        opts.legq = {o: dict(q, t=0) for o, q in st["leg_quotes"].items() if q["bid"] is not None}
        for u, rows in st["chains"].items():
            for r in rows:
                if r["bid"] is not None:
                    opts.legq.setdefault(r["symbol"], H._desk_row(r))
        quotes = {u: {"bid": q["bid"], "ask": q["ask"], "last": None, "t": now} for u, q in st["uquotes"].items()
                  if u != "XSP"}
        for inst, p in positions.items():
            q = opts.legq.get(inst[4:])
            p["mark"] = (q["bid"] + q["ask"]) / 2 if q else p["avg"]
        extra = {"pending_orders": [], "closed_trades": []}
        bars = {}
        if fam == "xsp_pcs":
            extra["bars_index"] = {"^GSPC": [{"t": datetime(int(b["d"][:4]), int(b["d"][5:7]), int(b["d"][8:]), 13, 30,
                                                            tzinfo=UTC).timestamp(), "o": b["o"], "h": b["h"],
                                              "l": b["l"], "c": b["c"], "v": b["v"]} for b in seq["gspc"]]}
        if fam == "opening_gamma":
            if st.get("bars30") is not None:
                extra["bars_r5"] = st["bars30"]
            if st.get("open5"):
                extra["bars_open5"] = {s: [b] for s, b in st["open5"].items()}
        if fam == "pead":
            day = datetime.fromtimestamp(now, tz=ET).date().isoformat()
            bars = {"1d": {n: [b for b in bl if datetime.fromtimestamp(b["t"], tz=ET).date().isoformat() < day]
                           for n, bl in seq["dbars_port"].items() if n in seq["cur"] or n == "SPY"}}
        if fam == "tensor_leaps":
            extra[AO.G4_FEED] = {"tensor_G4_events": st["g4"], "tensor_G4_exit_events": []}
        view = View(now=now, session=datetime.fromtimestamp(now, tz=ET).date().isoformat(), bars=bars, quotes=quotes,
                    positions={k: dict(v) for k, v in positions.items()}, equity=cash, cash=cash,
                    state=json.loads(json.dumps(state)), extra=extra)
        intents = sl.signal(view)
        state = sl.update_state(view, intents) or state
        step = {"opens": [], "closes": [], "core": [], "blockers": [], "obs": [], "blockers_ev": [],
                "handed": [c["event_id"] for c in AO.pead_today(AP.load(root), datetime.fromtimestamp(now, tz=ET).date()
                                                                .isoformat())] if fam == "pead" else [],
                "r5": [e["symbol"] for e in (state.get("r5") or {}).get("events", [])] if fam == "opening_gamma" else None,
                "recorded": [[x["week_end"], x["value"]] for x in state.get("xsp_digitals") or []]
                if fam == "xsp_pcs" else None}
        for it in intents:
            if it.kind == "signal":
                if " blocked: " in it.reason:
                    blk = (it.meta or {}).get("blocker") or {}
                    if blk.get("event_id"):
                        step["blockers_ev"].append([blk["event_id"], str(blk.get("reason"))])
                    else:
                        step["blockers"].append(it.reason.split(" blocked: ", 1)[1])
                elif (it.meta or {}).get("observation"):
                    step["obs"].append([it.symbol, bool(it.meta["observation"]["pass"])])
                continue
            pm = (it.meta or {}).get("position_meta") or {}
            pkg = (it.meta or {}).get("ausar_package")
            fee = 0.72 if fam == "xsp_pcs" else 0.65
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
                    cash -= (it.order.limit_price * 100 + fee * len(legs)) * n
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
                    cash += ((net or 0.0) * 100 - fee * len(legs)) * n
                    for inst, _ in held:
                        positions.pop(inst)
        step["blockers"] = sorted(set(step["blockers"]))
        step["obs"] = sorted(step["obs"])
        step["attempts"] = {k: bool(v.get("consumed")) for k, v in (state.get("option_entry_attempts") or {}).items()}
        step["cash"] = round(cash, 6)
        out.append(step)
    if root:
        shutil.rmtree(root, ignore_errors=True)
    return out


def _payload(seqs):
    base = H._payload([], [])
    base.pop("seqs")
    base.update(r5_script=R5_SCRIPT, r5_seed=os.path.join(AO.RESEARCH, "derived", "r5_last2h_seed.json"),
                digitals_csv=os.path.join(AO.RESEARCH, "implied_digital_atr100.csv"), xsp_fees=AO.XSP_FEES,
                r5_delay_s=AO.R5_DELAY_MIN * 60)
    base["seqs"] = [{"rule": s["rule"], "installed_at": s["installed_at"], "gspc": s.get("gspc"),
                     "dbars": s.get("dbars", {}), "bars": s.get("bars", {}), "pead_rows": s.get("pead_rows", {}),
                     "steps": [{"now": st["now"], "fill_open": st["fill_open"], "fill_close": st["fill_close"],
                                "chains": st["chains"], "leg_quotes": st["leg_quotes"], "uquotes": st["uquotes"],
                                "exercise": st["exercise"], "settle": st.get("src_settle", []),
                                "bars30": st.get("bars30"), "open5": st.get("open5", {}), "g4": st.get("g4", [])}
                               for st in s["steps"]]} for s in seqs]
    return base


def _num9(x):
    return None if x is None else round(float(x), 9)


def _norm(kind, v):
    """risk_budget / entry_spot are Decimal strings (XSP packages carry no entry spot): compared by value."""
    if kind != "opens":
        return v
    return [dict(o, risk_budget=_num9(o["risk_budget"]), entry_spot=_num9(o["entry_spot"])) for o in v]


def _compare(fam, a, b):
    keys = ["opens", "closes", "attempts"] + (["r5"] if fam == "opening_gamma" else []) + \
        (["recorded"] if fam == "xsp_pcs" else [])
    if fam == "xsp_pcs":                                # N1: the XSP package id digests the full contract records
        a, b = ({k: ([dict(o, pkg=None) for o in x[k]] if k in ("opens", "closes") else x[k]) for k in x} for x in (a, b))
    bad = [k for k in keys if _norm(k, a[k]) != _norm(k, b[k])]
    if fam == "pead":                                   # N11: only the producer's passing events reach the port
        pb = [r for r in b["blockers"] if not (r == "causal_published_earnings_events_required" and a["pead_events"])]
        handed = set(b["handed"])
        if a["blockers_noevent"] != pb or sorted(tuple(x) for x in a["blockers_ev"] if x[0] in handed) != \
                sorted(tuple(x) for x in b["blockers_ev"]):
            bad.append("blockers")
        if sorted(o for o in a["obs"] if o[1]) != b["obs"]:
            bad.append("obs")
    else:
        if a["blockers"] != sorted(set(b["blockers"]) | {x[1] for x in b["blockers_ev"]}):
            bad.append("blockers")
        if a["obs"] != b["obs"]:
            bad.append("obs")
    if abs(a["cash"] - b["cash"]) > 1e-4:
        bad.append("cash")
    return bad


def run():
    import hashlib
    body = open(R5_SCRIPT, "rb").read()
    assert hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest() == R5_SCRIPT_BLOB
    diffs, steps = [], 0
    stats = {"sequences": 0, "steps": 0, "by_family": {}, "entries": {}, "exits": {}, "r5_events": 0,
             "xsp_readings": 0, "blockers": {}, "pead_handed_events": 0}
    work = tempfile.mkdtemp()
    try:
        for b0 in range(0, N_SEQ, BATCH):
            seqs = [make_sequence(31000 + i) for i in range(b0, min(N_SEQ, b0 + BATCH))]
            ports = [run_port(s, work) for s in seqs]
            old = old_run(SOURCE_SCRIPT, _payload(seqs), timeout=7200, tree=SRC)
            stats["sequences"] += len(seqs)
            for seq, src_steps, port_steps in zip(seqs, old["seqs"], ports):
                fam = seq["family"]
                stats["by_family"][fam] = stats["by_family"].get(fam, 0) + len(port_steps)
                for i, (a, b) in enumerate(zip(src_steps, port_steps)):
                    steps += 1
                    stats["entries"][fam] = stats["entries"].get(fam, 0) + len(a["opens"])
                    for c in a["closes"]:
                        stats["exits"][c.get("reason", "?")] = stats["exits"].get(c.get("reason", "?"), 0) + 1
                    for r in a["blockers"]:
                        stats["blockers"][r] = stats["blockers"].get(r, 0) + 1
                    if fam == "opening_gamma" and i == 0:
                        stats["r5_events"] += len(a["r5"] or [])
                    bad = _compare(fam, a, b)
                    if bad:
                        diffs.append({"rule": seq["rule"], "seed": seq["seed"], "step": i,
                                      "at": datetime.fromtimestamp(seq["steps"][i]["now"], tz=ET).isoformat(),
                                      "what": bad, "source": {k: a.get(k) for k in bad},
                                      "port": {k: b.get(k) for k in bad}})
                if fam == "xsp_pcs":
                    stats["xsp_readings"] += len(src_steps[-1]["recorded"] or [])
            del seqs, ports, old
    finally:
        shutil.rmtree(work, ignore_errors=True)
    stats["steps"] = steps
    res = {"sleeve": "ausar_option_producers", "cases": steps, "identical": steps - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats, "source_tree": SRC,
           "source_commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
           "r5_research_script": {"path": R5_SCRIPT, "blob": R5_SCRIPT_BLOB},
           "named_divergences_in_cases": {
               "N1/N2": "qualified inputs and unbounded sizes on both sides (as tools/parity/ausar_options.py)",
               "N6": "the evaluator's settle replaced on both sides by the harness settlement at the S&P 500 close / 10",
               "N8": "the index-inclusive XSP fee schedule on both sides",
               "N9": "both sides compute their XSP inputs from the same S&P 500 sessions / research series",
               "N10": "both sides compute R5 from the same 30-minute bars and the derived research seed",
               "N11": "the port receives only the producer's pre-evaluated passing PEAD events: the source's "
                      "per-event blockers and failing observations of the other events are not compared",
               "N12": "the same published G4 events on both sides"},
           "method": "multi-step sequences per family; each side builds its family input itself (source: an "
                     "independent research implementation in the source tree; port: the sleeve's producers)"}
    write_receipt("ausar_option_producers", res)
    return res
