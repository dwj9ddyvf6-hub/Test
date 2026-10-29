"""ausar_daily20: the SOURCE runtime's own daily path vs the port, on deterministic random tapes, plus the research's
own decision ledger.

  SOURCE  in the source tree (agentic-trading-desk @1720157f, desk-source): backend/tensor_runtime.canonical_native_bars
          over a Yahoo-shaped provider revision of the tape (the runtime's canonicalization: native periods,
          completion / usable clocks) -> backend/tensor_engine.extract_native_feature_rows (Node, frozen v690) ->
          backend/tensor_daily_models.evaluate_daily20 at each ordinal. The checkout lacks the models and the engine
          manifest: SD.ASSET_ROOT / SE.ENGINE_ROOT read their vendored copies (byte-identical, hash-verified by the
          modules themselves). backend.providers is stubbed (NY, utc_clock, the XNYS session table of the tape).
  PORT    desk/sleeves/families/ausar_daily20.assess (tape identity against the anchor, native bars on the desk
          calendar, warm-up / phase / exclusions, the engine, evaluate_daily20) on the same tape in the desk's shape.
  Tapes   anchored names sharing AMD's anchor clocks, on the exchange's real session opens / closes (the research
          AMD tape's own clocks 2016-09-26 .. 2026-09-24, less the sessions the name's pinned seed does not hold:
          its seed's own sessions, D1; the source here runs without its seed, so a tape holding such a session would
          test the source's absent quarantine, not the port) + 0-60 forward
          sessions; random OHLCV regimes; some tapes lose a session (endpoint ordinal) or their origin.
  Cases   every in-phase ordinal after warm-up (both books: selected / reason / prediction / ordinal) + random
          off-phase and warm-up ordinals; plus the AMD C01 ledger oracle (35 features and both predictions at 32
          decision points), computed by the port's vendored engine and models.
The engine is causal (a prefix's rows equal the full run's): each side runs it once per tape and evaluates prefixes;
the harness also re-runs two random prefixes per tape through the port's engine and requires identical rows."""
import json
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.families import ausar_daily20 as A
from desk.vendor.ausar_tensor import tensor_daily_models as TD
from desk.vendor.ausar_tensor import tensor_engine as TE

from . import ausar_options as H
from . import old_run, write_receipt

SRC = H.SRC
N_TAPES = int(os.environ.get("AUSAR_D20_TAPES", "14"))
UTC = timezone.utc
VEND = os.path.join(os.path.dirname(A.__file__), "..", "..", "vendor", "strategies")

SOURCE_SCRIPT = r'''
import bisect, types, hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.modules['httpx'] = types.ModuleType('httpx')
import pandas as pd
UTC = timezone.utc
CAL = {d: tuple(v) for d, v in PAYLOAD['calendar'].items()}
DATES = sorted(CAL)
class XNYS:
    @staticmethod
    def _d(x):
        return str(x)[:10]
    def is_session(self, d):
        return self._d(d) in CAL
    def session_open(self, s):
        return pd.Timestamp(CAL[self._d(s)][0], unit='s', tz='UTC')
    def session_close(self, s):
        return pd.Timestamp(CAL[self._d(s)][1], unit='s', tz='UTC')
    def next_session(self, s):
        return pd.Timestamp(DATES[bisect.bisect_right(DATES, self._d(s))])
    def previous_session(self, s):
        return pd.Timestamp(DATES[bisect.bisect_left(DATES, self._d(s)) - 1])
    def sessions_in_range(self, a, b):
        return [pd.Timestamp(x) for x in DATES[bisect.bisect_left(DATES, self._d(a)):bisect.bisect_right(DATES, self._d(b))]]
import backend
from backend.store import DeskError
prov = types.ModuleType('backend.providers')
prov.NY = ZoneInfo('America/New_York')
prov._nyse = lambda: XNYS()
def utc_clock(clock=None):
    value = clock or datetime.now(UTC)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None or value.utcoffset() is None:
        raise DeskError('Clock must have a timezone', 422)
    return value.astimezone(UTC)
prov.utc_clock = utc_clock
sys.modules['backend.providers'] = prov
backend.providers = prov
from pathlib import Path
from backend import tensor_runtime as TR, tensor_engine as SE, tensor_daily_models as SD
SD.ASSET_ROOT = Path(PAYLOAD['models'])
SE.ENGINE_ROOT = Path(PAYLOAD['engine'])
out = []
for tp in PAYLOAD['tapes']:
    now = datetime.fromtimestamp(tp['now'], tz=UTC)
    rows = [{'timestamp': datetime.fromtimestamp(b['t'], tz=UTC).isoformat(), 'open': b['o'], 'high': b['h'],
             'low': b['l'], 'close': b['c'], 'volume': b['v']} for b in tp['bars']]
    body = json.dumps(rows, sort_keys=True).encode()
    h = hashlib.sha256(body).hexdigest()
    payload = {'revision_id': h, 'content_sha256': h, 'symbol': tp['symbol'], 'interval': '1d', 'vendor_interval': '1d',
               'observed_at': now.isoformat(), 'fetched_at': now.isoformat(), 'provider': 'yahoo',
               'adjustment': 'yahoo_split_adjusted_ohlc', 'completeness': {'status': 'complete_vendor_response'},
               'omitted_rows': 0, 'omitted_bar_rows': [], 'bars': rows}
    res = []
    try:
        bars = TR.canonical_native_bars(payload, '1d', now, expected_symbol=tp['symbol'])
        full = SE.extract_native_feature_rows(tp['symbol'], '1d', bars, as_of_ms=int(tp['now'] * 1000),
                                              timeout_seconds=300).rows   # a loaded harness host: no timeouts
    except Exception as e:
        out.append({'error': type(e).__name__ + ': ' + str(e)[:200], 'cases': []})
        continue
    for k in tp['ordinals']:
        try:
            dec = SD.evaluate_daily20(tp['symbol'], list(full[:k + 1]), as_of_ms=int(tp['now'] * 1000))
            res.append({'k': k, 'status': 'ok', 'books': {d.sleeve_id: [d.selected, d.reason, d.score, d.bar_index,
                                                                         d.close, d.dollar_volume20] for d in dec}})
        except SD.DailyModelInputError as e:
            res.append({'k': k, 'status': 'failed', 'reason': str(e)})
    out.append({'error': None, 'cases': res, 'n_rows': len(full)})
print(json.dumps({'tapes': out}))
'''


def _true_sessions():
    """{date: (open, close)}: the research AMD tape's clocks (the exchange's real history) to its endpoint, then the
    desk calendar."""
    fx = json.load(open(os.path.join(VEND, "tensor_state_repair", "engine", "fixtures", "AMD-1d-completed.json")))
    out = {}
    for b in fx["bars"]:
        d = datetime.fromtimestamp(b["timestamp_ms"] / 1000, tz=H.ET).date().isoformat()
        out[d] = (b["timestamp_ms"] // 1000, b["completed_at_ms"] // 1000)
    d = date.fromisoformat(max(out)) + timedelta(days=1)
    while d <= date(2027, 6, 30):
        if cal.is_trading_day(d):
            out[d.isoformat()] = (int(cal.session_open(d)), int(cal.session_close(d)))
        d += timedelta(days=1)
    return out


def make_tape(seed, sessions, names):
    rng = random.Random(seed)
    sym = rng.choice(names)
    a = TD.anchor_for(sym)
    skip = A.non_seed_sessions(sym)
    days = [d for d in sorted(sessions) if a.first_timestamp <= sessions[d][0] <= a.last_timestamp and d not in skip]
    assert len(days) == a.original_rows, sym                     # the seed's own sessions (D1)
    fwd = [d for d in sorted(sessions) if sessions[d][0] > a.last_timestamp][:rng.randint(0, 60)]
    days += fwd
    px, vol, out = rng.uniform(8, 150), rng.uniform(0.012, 0.035), []
    drift = 0.0
    for d in days:
        if rng.random() < 0.03:
            drift = rng.choice((-0.004, -0.002, 0.0, 0.002, 0.004))
        o = px * (1 + rng.gauss(0, vol / 3))
        c = max(0.5, px * (1 + rng.gauss(drift, vol)))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
        out.append({"t": float(sessions[d][0]), "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                    "v": float(int(rng.uniform(1e5, 6e6)))})
        px = c
    kind = rng.random()
    if kind < 0.08:                                              # a session lost before the anchor's endpoint
        out = out[:300] + out[301:]
    elif kind < 0.12:                                            # the origin lost
        out = out[1:]
    last = cal._as_date(out[-1]["t"])
    now = sessions[last.isoformat()][1] + 1800
    n = len(out)
    inphase = [k for k in range(233, n) if k % 20 == a.phase]
    other = rng.sample([k for k in range(150, n) if k % 20 != a.phase], 12)
    return {"seed": seed, "symbol": sym, "bars": out, "now": now, "ordinals": sorted(inphase + other), "kind": kind}


def real_tapes(sessions, names):
    """the research's own AMD tape (real prices: its decisions include selections), and the same prices under two
    other anchored names with AMD's ordinal count (other phases -> other evaluated ordinals)."""
    fx = json.load(open(os.path.join(VEND, "tensor_state_repair", "engine", "fixtures", "AMD-1d-completed.json")))
    bars = [{"t": float(b["timestamp_ms"] // 1000), "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"],
             "v": b["volume"]} for b in fx["bars"]]
    out = []
    same = [n for n in names if TD.anchor_for(n).original_rows == len(bars) and n != "AMD"]
    for i, sym in enumerate(["AMD"] + same[:2]):
        a = TD.anchor_for(sym)
        n = len(bars)
        inphase = [k for k in range(233, n) if k % 20 == a.phase]
        rng = random.Random(7300 + i)
        other = rng.sample([k for k in range(150, n) if k % 20 != a.phase], 12)
        now = sessions[cal._as_date(bars[-1]["t"]).isoformat()][1] + 1800
        out.append({"seed": 7300 + i, "symbol": sym, "bars": bars, "now": now, "ordinals": sorted(inphase + other),
                    "kind": 1.0})
    return out


class _Cached:
    """the real engine, run once on the tape; a prefix reads the full run's rows (the engine is causal)."""

    def __init__(self, full):
        self.full = full

    def __call__(self, symbol, frame, bars, as_of_ms):
        rows = self.full[:len(bars)]

        class Hist:
            pass
        Hist.rows = rows
        return Hist


def run_port(tp):
    now_ms = int(tp["now"] * 1000)
    a = TD.anchor_for(tp["symbol"])
    full = None
    # the engine runs once on the whole tape from its origin (a prefix that ends before the anchor's endpoint is
    # admissible even when the full tape later loses an ordinal; assess() judges each prefix itself)
    rows = [x for x in tp["bars"] if int(x["t"]) >= a.first_timestamp]
    if rows and int(rows[0]["t"]) == a.first_timestamp:
        try:
            full = TE.extract_native_feature_rows(tp["symbol"], "1d", A.native_bars(rows, now_ms), as_of_ms=now_ms,
                                                  timeout_seconds=300).rows
        except TE.TensorEngineError:
            full = None
    eng = _Cached(full or [])
    res = []
    for k in tp["ordinals"]:
        st, reason, dec = A.assess(tp["symbol"], tp["bars"][:k + 1], now_ms, engine=eng)
        res.append({"k": k, "status": st, "reason": reason,
                    "books": {sid: [x["selected"], x["reason"], x["score"], x["bar_index"], x["close"],
                                    x["dollar_volume20"]] for sid, x in dec.items()}})
    checks = []
    if full:
        rng = random.Random(tp["seed"] + 1)
        for k in rng.sample(range(240, len(rows)), 2):
            pre = TE.extract_native_feature_rows(tp["symbol"], "1d", A.native_bars(rows[:k], now_ms), as_of_ms=now_ms,
                                                 timeout_seconds=300).rows
            checks.append(list(pre) == list(full[:k]))
    return res, checks


def _same(src, port, tp):
    """one ordinal: the source decisions / failure vs the port's assessment."""
    a = TD.anchor_for(tp["symbol"])
    if src["status"] == "failed":
        return port["status"] == "failed"
    k = src["k"]
    want = src["books"]
    reason = want["D20_PV"][1]
    if reason in ("phase_not_selected", "warmup", "excluded_symbol"):
        exp = {"phase_not_selected": "phase_not_selected", "warmup": "native_history_warming",
               "excluded_symbol": "excluded_symbol"}[reason]
        return port["status"] in ("ready", "ineligible") and port["reason"] == exp and not port["books"]
    if reason in ("native_not_ready", "price_below_5", "liquidity_below_1m", "invalid_atr"):
        if k % 20 != a.phase:                     # D2: an off-phase name is labelled by its phase (no engine run)
            return port["status"] == "ready" and port["reason"] == "phase_not_selected" and not port["books"]
        return port["status"] == "ready" and port["books"] and all(port["books"][s][1] == reason for s in want)
    return port["books"] and all(
        port["books"][s][:2] == want[s][:2] and port["books"][s][3] == want[s][3] and
        ((port["books"][s][2] is None) == (want[s][2] is None)) and
        (want[s][2] is None or abs(port["books"][s][2] - want[s][2]) <= 1e-15) for s in want)


def _oracle():
    fx = json.load(open(os.path.join(VEND, "tensor_state_repair", "engine", "fixtures", "AMD-1d-completed.json")))
    bars = [TE.NativeBar(timestamp_ms=b["timestamp_ms"], completed_at_ms=b["completed_at_ms"], usable_at_ms=b["usable_at_ms"],
                         open=b["open"], high=b["high"], low=b["low"], close=b["close"], volume=b["volume"]) for b in fx["bars"]]
    ff = TD.feature_frame(list(TE.extract_native_feature_rows("AMD", "1d", bars, as_of_ms=bars[-1].usable_at_ms,
                                                              timeout_seconds=300).rows))
    models = TD.load_frozen_models()
    oracle = json.load(open(os.path.join(VEND, "tensor_daily20", "models", "AMD_C01_LEDGER_ORACLE.json")))
    cases, bad = 0, []
    for r in oracle["records"]:
        i = r["bar_index"]
        cases += 1
        if any((ff[i][k] is None) != (v is None) or (v is not None and abs(ff[i][k] - v) > 1e-12)
               for k, v in r["features"].items()):
            bad.append({"bar_index": i, "what": "features"})
        for name, want in r["original_ledger_predictions"].items():
            cases += 1
            got = models[name].predict(ff[i])
            if abs(got - want) > 1e-12:
                bad.append({"bar_index": i, "model": name, "got": got, "want": want})
    return cases, bad


def run():
    sessions = _true_sessions()
    first, last = TD.anchor_for("AMD").first_timestamp, TD.anchor_for("AMD").last_timestamp
    names = [s for s in A.enrollment() if TD.anchor_for(s).first_timestamp == first and
             TD.anchor_for(s).last_timestamp == last and TD.anchor_for(s).original_rows <= 2513]
    tapes = real_tapes(sessions, names) + [make_tape(6200 + i, sessions, names) for i in range(N_TAPES)]
    ports = [run_port(tp) for tp in tapes]
    payload = {"calendar": {d: list(v) for d, v in sessions.items()},
               "models": os.path.abspath(os.path.join(VEND, "tensor_daily20", "models")),
               "engine": os.path.abspath(os.path.join(VEND, "tensor_state_repair", "engine")),
               "tapes": [{k: tp[k] for k in ("symbol", "bars", "now", "ordinals")} for tp in tapes]}
    src = old_run(SOURCE_SCRIPT, payload, timeout=7200, tree=SRC)["tapes"]
    diffs, cases = [], 0
    stats = {"tapes": len(tapes), "in_phase": 0, "off_phase": 0, "selected": {"D20_PV": 0, "D20_TENSOR": 0},
             "failed_tapes": 0, "reasons": {}, "prefix_recompute_checks": 0, "d2_relabelled": 0}
    for tp, s, (p, checks) in zip(tapes, src, ports):
        stats["prefix_recompute_checks"] += len(checks)
        if not all(checks):
            diffs.append({"seed": tp["seed"], "what": "engine prefix rows differ from the full run"})
        if s["error"]:
            stats["failed_tapes"] += 1
            cases += 1
            if any(x["status"] != "failed" for x in p if x["k"] >= 233):
                diffs.append({"seed": tp["seed"], "symbol": tp["symbol"], "source": s["error"],
                              "port": [x["reason"] for x in p][:3]})
            continue
        for a, b in zip(s["cases"], p):
            cases += 1
            if a["status"] == "ok":
                r = a["books"]["D20_PV"][1]
                if r in ("native_not_ready", "price_below_5", "liquidity_below_1m", "invalid_atr") and \
                        a["k"] % 20 != TD.anchor_for(tp["symbol"]).phase:
                    stats["d2_relabelled"] += 1
                stats["reasons"][r] = stats["reasons"].get(r, 0) + 1
                stats["in_phase" if r not in ("phase_not_selected", "warmup") else "off_phase"] += 1
                for sid in ("D20_PV", "D20_TENSOR"):
                    stats["selected"][sid] += 1 if a["books"][sid][0] else 0
            if not _same(a, b, tp):
                diffs.append({"seed": tp["seed"], "symbol": tp["symbol"], "k": a["k"], "source": a, "port": b})
    oc, obad = _oracle()
    res = {"sleeve": "ausar_daily20", "cases": cases + oc, "identical": cases + oc - len(diffs) - len(obad),
           "diffs": (diffs + obad)[:10], "n_diffs": len(diffs) + len(obad), "stats": stats,
           "oracle": {"cases": oc, "diffs": len(obad), "source": "strategies/tensor_daily20/models/AMD_C01_LEDGER_ORACLE.json "
                                                                  "(research C01 ledger: 32 decisions x 35 features + 2 predictions)"},
           "source_tree": SRC, "source_commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
           "named_divergences_in_cases": {
               "D1": "the same tape on both sides (the source path canonicalizes a Yahoo-shaped revision of it)",
               "D2": "off-phase / warm-up ordinals: the port assesses them without the engine (reason compared; an "
                     "off-phase name the source labels by an earlier rule - price / liquidity / ATR / readiness - is "
                     "'phase_not_selected' in the port: same outcome, counted in stats.d2_relabelled)",
               "D3/D4": "book execution (exit clock, sizing price): not exercised by this decision harness"},
           "method": "per tape: the source canonicalization + engine + evaluate_daily20 at every in-phase ordinal and 12 "
                     "random others vs the port's assess; plus the research ledger oracle"}
    write_receipt("ausar_daily20", res)
    return res
