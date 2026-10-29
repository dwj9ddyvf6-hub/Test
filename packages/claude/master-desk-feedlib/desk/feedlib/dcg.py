"""The DCG scoring job: the daily-cyan GBM and the four daily/weekly GBM-rule sleeves read one nightly pass.

After each close (once the genome refresh has landed) the old scorers' shared frame is built the old way —
the genome's completed daily bars (split-adjusted, the desk bar policy; >= 60 bars), the market series
(build_market verbatim: SPY TLT HYG IEF UUP GLD USO IWM QQQ SMH closes, the four ETFs' OHLC, ^VIX daily
closes forward-filled — the old CBOE CSV had no writer, so the VIX comes from Yahoo with the old staleness
rule: more than 2 weekdays behind the last scored day fails the pass), the cross-sectional features (the
vendored dcg_xsect.compute_xsect over the genome, point in time, recomputed every night — the old
xsect_cache.json had no writer either and days past it scored with nulls), the FOMC day indices — and the
vendored Node scorers run over every genome name but SPY/QQQ/IWM/SMH, in batches of 50 with the old retry
law (a failed batch is retried once, then name by name): dcg_score.mjs (the frozen GBM) and
dcg_rule_score.mjs per (lane, signal) the rule sleeves read. Only fires on each name's last bar are kept.

Named divergence (calendar): the scorers' day axis carries the next 10 trading days of the desk calendar
after the last bar, so the GBM's turn-of-month and pre-FOMC features at the signal bar are the research's
values (the old live scorer had no day after the signal bar: tom was always 1 and prefomc always 0 there;
the old desk patched tom for rule_1d_green_tom only). Every other feature looks backward.

Writes cache/dcg/scores.json: {"date", "gbm": {sym: {date, score}}, "rules": {"1D:cyan": {sym: features}},
"facts": {sym: {date, px, dv20}}} or {"date", "wait": reason}."""
import json
import math
import os
import subprocess
import time
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "old_desk_research")
SCORER = os.path.join(VENDOR, "dcg_scorer", "dcg_score.mjs")
RULE_SCORER = os.path.join(VENDOR, "dcg_scorer", "dcg_rule_score.mjs")
MODEL = os.path.join(VENDOR, "models", "tensor_gbm_v4_1D_cyan_full.json")
MARKET_ETFS = ("SPY", "TLT", "HYG", "IEF", "UUP", "GLD", "USO", "IWM", "QQQ", "SMH")
NOT_SCORED = ("SPY", "QQQ", "IWM", "SMH")
RULE_LANES = (("1D", "cyan"), ("1D", "green"), ("1W", "cyan"), ("1W", "swing"))
CAL_AHEAD = 10
MIN_FRESH = 0.5
_MODS = {}


def _xsect_mod():
    if "x" not in _MODS:
        import importlib.util
        spec = importlib.util.spec_from_file_location("old_dcg_xsect", os.path.join(VENDOR, "dcg_scorer", "dcg_xsect.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _MODS["x"] = m
    return _MODS["x"]


def bar_date(t):
    return datetime.fromtimestamp(float(t) + 4 * 3600, tz=timezone.utc).date().isoformat()


def rows_of(bars):
    """epoch bar dicts -> the old cache rows [date, o, h, l, c, v]."""
    return [[bar_date(b["t"]), float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0)]
            for b in bars]


def vix_staleness(last_vix_date, last_scored):
    """trading days (weekdays) the VIX series trails the last scored day (the old fail-loud law)."""
    d0, d1 = date.fromisoformat(last_vix_date), date.fromisoformat(last_scored)
    n, cur = 0, d0
    while cur < d1:
        cur = cur.fromordinal(cur.toordinal() + 1)
        if cur.weekday() < 5:
            n += 1
    return n


def build_market(days, bars, vix_by_date):
    """old build_market: closes aligned to days, the four ETFs' OHLC, ^VIX forward-filled (stale -> raise)."""
    D = len(days)
    didx = {d: i for i, d in enumerate(days)}

    def series(sym):
        out = [None] * D
        for b in bars.get(sym, []):
            i = didx.get(b[0])
            if i is not None:
                out[i] = b[4]
        return out

    def ohlc(sym):
        return sorted([[b[0], b[1], b[2], b[3], b[4], b[5]] for b in bars.get(sym, [])])

    vix = [None] * D
    last_vix = None
    for d, v in sorted((vix_by_date or {}).items()):
        if last_vix is None or d > last_vix:
            last_vix = d
        i = didx.get(d)
        if i is not None and v is not None:
            vix[i] = float(v)
    if days:
        if last_vix is None:
            raise RuntimeError("VIX series missing: refusing to score with a null VIX feature")
        lag = vix_staleness(last_vix, str(days[-1])[:10])
        if lag > 2:
            raise RuntimeError("VIX series is stale: last %s vs last scored day %s (%d trading days)"
                               % (last_vix, days[-1], lag))
    last = None
    for i in range(D):
        if vix[i] is None:
            vix[i] = last
        else:
            last = vix[i]
    return {"spyC": series("SPY"), "vix": vix, "tltC": series("TLT"), "hygC": series("HYG"),
            "iefC": series("IEF"), "uupC": series("UUP"), "gldC": series("GLD"), "usoC": series("USO"),
            "btcC": [None] * D, "vix3m": [None] * D, "iwmC": series("IWM"), "qqqC": series("QQQ"),
            "smhC": series("SMH"), "spyBars": ohlc("SPY"), "qqqBars": ohlc("QQQ"), "iwmBars": ohlc("IWM"),
            "smhBars": ohlc("SMH")}


def xsect(bars, days):
    """the vendored compute_xsect over genome rows on a day list (NaN -> None)."""
    m = _xsect_mod()
    return m.nan_to_null(m.compute_xsect(bars, days))


def fomc_dates():
    """FOMC decision days: the old desk's macro_events.json, completed with the desk calendar's schedule."""
    from ..feeds import FOMC_2025_2027
    ev = json.load(open(os.path.join(VENDOR, "macro_events.json")))
    out = {e["date"] for e in ev.get("events", []) if "FOMC" in e.get("name", "").upper()}
    return sorted(out | set(FOMC_2025_2027) | set(FOMC_2024))


FOMC_2024 = ["2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07",
             "2024-12-18"]


def extend_calendar(days, n=CAL_AHEAD):
    """the desk calendar's next n trading days after the last bar (the scorer's turn-of-month / pre-FOMC)."""
    out, d = [], date.fromisoformat(days[-1])
    while len(out) < n:
        d = cal.next_trading_day(d)
        out.append(d.isoformat())
    return out


def _nan_to_null(v):
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, dict):
        return {k: _nan_to_null(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_nan_to_null(x) for x in v]
    return v


def _run(script, payload, timeout=900, node="node"):
    p = subprocess.run([node, script], input=json.dumps(_nan_to_null(payload)), capture_output=True, text=True,
                       timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError((p.stdout[:400] + " | " + p.stderr[:400])[:600])
    res = json.loads(p.stdout)
    if not isinstance(res, dict) or not isinstance(res.get("results"), list) or not res.get("ok"):
        raise RuntimeError("scorer error: %s" % str(res.get("error") if isinstance(res, dict) else res)[:200])
    return {r["sym"]: r["fires"] for r in res["results"] if isinstance(r, dict) and "sym" in r and "fires" in r}


def score(script, base, symbols, batch=50, deadline_s=1800, node="node"):
    """the old score_symbols / score_rule_symbols: batches of 50; a failed batch is retried once (rules) and then
    name by name; unscorable names are skipped. Returns ({sym: fires}, [skipped])."""
    out, skipped = {}, []
    t0 = time.time()
    for i in range(0, len(symbols), batch):
        if time.time() - t0 > deadline_s:
            skipped += [s["sym"] for s in symbols[i:]]
            break
        chunk = symbols[i:i + batch]
        try:
            out.update(_run(script, dict(base, symbols=chunk), node=node))
            continue
        except Exception:
            pass
        try:
            out.update(_run(script, dict(base, symbols=chunk), node=node))
            continue
        except Exception:
            pass
        for s in chunk:
            try:
                out.update(_run(script, dict(base, symbols=[s]), node=node))
            except Exception:
                skipped.append(s["sym"])
    return out, skipped


def dv20(bl, idx):
    if idx < 19:
        return 0
    return sum(b[4] * b[5] for b in bl[idx - 19:idx + 1]) / 20


def frame(genome_rows, vix_by_date, today, ahead_n=CAL_AHEAD, fomc=None):
    """the scorers' shared payload base + the scored symbol list from genome rows ({sym: rows}). ahead_n=0 and
    the old macro_events FOMC list reproduce the old desk's payload exactly (the parity harness)."""
    bars = {s: [b for b in bl if b[0] <= today] for s, bl in genome_rows.items()}
    bars = {s: bl for s, bl in bars.items() if len(bl) >= 60}
    days = sorted({b[0] for bl in bars.values() for b in bl})
    days = [d for d in days if d <= today]
    market = build_market(days, bars, vix_by_date)
    allbars = {s: [b for b in bl if b[0] <= today] for s, bl in genome_rows.items()}
    alldays = sorted({b[0] for bl in allbars.values() for b in bl})
    xs_all = xsect(allbars, alldays)                  # the old cache: every cached name, every cached day
    xmap = {d: i for i, d in enumerate(alldays)}
    xs = {k: [vals[xmap[d]] if d in xmap else None for d in days] for k, vals in xs_all.items()}
    ahead = extend_calendar(days, ahead_n) if days and ahead_n else []
    ext = days + ahead
    pad = [None] * len(ahead)
    market = {k: (v + pad if k in ("spyC", "vix", "tltC", "hygC", "iefC", "uupC", "gldC", "usoC", "btcC", "vix3m",
                                   "iwmC", "qqqC", "smhC") else v) for k, v in market.items()}
    xs = {k: list(v) + pad for k, v in xs.items()}
    didx = {d: i for i, d in enumerate(ext)}
    fidx = sorted(didx[d] for d in (fomc_dates() if fomc is None else fomc) if d in didx)
    base = {"modelPath": MODEL, "days": ext, "market": market, "xsect": xs, "fomcIdx": fidx}
    syms = [{"sym": s, "bars": bars[s]} for s in sorted(bars) if s not in NOT_SCORED]
    return base, syms, bars


def last_bar_fires(fires_by_sym, bars):
    out = {}
    for s, fires in fires_by_sym.items():
        bl = bars.get(s) or []
        if not bl:
            continue
        for f in fires:
            if f.get("date") == bl[-1][0]:
                out[s] = f
    return out


def run(hub, root, now, node="node"):
    """the nightly job: cache/dcg/scores.json for today's session (once; retried until written)."""
    from ..sleeves.families.femto_specs import GENOME
    today = datetime.fromtimestamp(now, tz=ET).date().isoformat()
    path = os.path.join(root, "cache", "dcg", "scores.json")
    done = read_json(path, None) or {}
    if done.get("date") == today and not done.get("wait"):
        return {"date": today, "skip": "already written"}
    syms = list(dict.fromkeys(list(GENOME) + list(MARKET_ETFS)))
    got = {}
    for i in range(0, len(syms), 200):
        got.update(hub.bars("equity_split", "1d", syms[i:i + 200], 600, cache_only=True))
    rows = {s: rows_of(bl) for s, bl in got.items() if bl}
    fresh = sum(1 for bl in rows.values() if bl[-1][0] == today)
    if not rows or fresh < MIN_FRESH * len(rows):
        out = {"date": today, "wait": f"genome carries today's session for {fresh}/{len(rows)} names"}
        write_json_atomic(path, out)
        return out
    vbl = hub.bars("yahoo", "1d", ["^VIX"], 600).get("^VIX") or []
    vix = {datetime.fromtimestamp(float(b["t"]), tz=ET).date().isoformat(): float(b["c"]) for b in vbl}
    try:
        base, symbols, bars = frame(rows, vix, today)
    except RuntimeError as e:
        out = {"date": today, "wait": str(e)[:200]}
        write_json_atomic(path, out)
        return out
    gbm, skipped = score(SCORER, base, symbols, node=node)
    out = {"date": today, "computed_at": now, "n_scored": len(symbols), "skipped": {"gbm": skipped},
           "gbm": {s: {"date": f["date"], "score": f["score"]} for s, f in last_bar_fires(gbm, bars).items()},
           "rules": {}, "facts": {}}
    for lane, sig in RULE_LANES:
        fires, sk = score(RULE_SCORER, dict(base, lane=lane, signal=sig), symbols, node=node)
        out["skipped"][f"{lane}:{sig}"] = sk
        out["rules"][f"{lane}:{sig}"] = {s: {"date": f["date"], "features": f.get("features") or {}}
                                         for s, f in last_bar_fires(fires, bars).items()}
    for s, bl in bars.items():
        out["facts"][s] = {"date": bl[-1][0], "px": bl[-1][4], "dv20": dv20(bl, len(bl) - 1)}
    out["recent_days"] = base["days"][:len(base["days"]) - CAL_AHEAD][-30:]     # the old _is_tom's market days
    from . import mcap                       # rule_1d_cyan_smallcap's EDGAR log market cap, its price band only
    cmap = None
    for s, f in (out["rules"].get("1D:cyan") or {}).items():
        fa = out["facts"].get(s) or {}
        if fa.get("px") is None or not (5.0 <= fa["px"] < 10.0):
            continue
        if cmap is None:
            cmap = mcap.cik_map(root, now)
        lm, detail = mcap.log_mcap(s, f["date"], cmap, lambda c: mcap.float_frames(root, c, now),
                                   [(r[0], r[4]) for r in bars.get(s) or []])
        fa["log_mcap"], fa["mcap_detail"] = lm, detail
    write_json_atomic(path, out)
    return out


def load_file(path, today):
    d = read_json(path, None)
    if not d or d.get("date") != today or d.get("wait"):
        return None
    return d


RULE_1H = os.path.join(VENDOR, "dcg_scorer", "dcg_rule_1h.mjs")


def score_1h(bars_1h, smh_daily, node="node", timeout=600):
    """the old rule_1h_cyan_raw.score_1h: the vendored dcg_rule_1h.mjs over the basket's 1H bars (ISO bar starts,
    >= 100 bars) and SMH's daily rows (its weekly UT regime). Returns {sym: [fires]}."""
    syms = [{"sym": s, "bars": [[datetime.fromtimestamp(float(b["t"]), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 b["o"], b["h"], b["l"], b["c"], b.get("v") or 0] for b in bl]}
            for s, bl in sorted(bars_1h.items()) if len(bl) >= 100]
    if not syms:
        return {}
    p = subprocess.run([node, RULE_1H], input=json.dumps({"symbols": syms, "smhDaily": smh_daily}),
                       capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError("1H scorer failed: " + (p.stdout[:300] + " | " + p.stderr[:300])[:600])
    res = json.loads(p.stdout)
    if not isinstance(res, dict) or not isinstance(res.get("results"), list) or not res.get("ok"):
        raise RuntimeError("1H scorer error: %s" % str(res)[:200])
    return {r["sym"]: r["fires"] for r in res["results"] if isinstance(r, dict) and "sym" in r and "fires" in r}
