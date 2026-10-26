"""The M2 weekly qualifier + HOLD9 feature blocks shared by beatendown and confluence.

The old desk's qualify_week.mjs (vendored byte-identical; its host paths are rewritten into a run copy) runs
the Tensor Anna replica + enrichment (vendored byte-identical) over the frozen research weekly bars (dev
2016-2022 and holdout 2022-2026, vendored) merged with live Alpaca 1Week top-ups (SIP, adjustment=all, the
last 12 weeks, merged by bar time, the old confluence_weekly_incr.json). The feature blocks are the old
compute_features verbatim (E/X/M/Q/P): the weekly ETF series (SPY, UUP, the desk sector and industry ETFs),
the qualifier's daily bars, the vendored math_lanes.rqa_det_lam on the frozen dev cut, and the sector bucket
(the old desk map in the vendored risk.py, else the 60-week return correlation with the desk sector ETFs).
The twins differ only in the daily bars their rank saw: beatendown (16:20) includes the rank day's session,
confluence (16:05, fetch_daily k < today) excludes it — both feature sets are written.

run() is the weekly job: it writes cache/m2/qualifiers.json ({"rank_date", "asof_monday", "qualifiers": [...]})
or {"rank_date", "wait": reason} when the inputs fail closed (the old rank_wait)."""
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
from datetime import date, datetime, timedelta, timezone

from ..util import ET, read_json, write_json_atomic

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "old_desk_research")
OLD_HOST = "<workspace>/alpaca-swing-desk/"
CUT_LAM = 0.17647058823529413   # frozen dev tercile cut (study §1)
FETCH_ERR_LIMIT = 35            # weekly-universe fail-closed threshold
INCR_KEEP = 170                 # the old incremental cache bound (~3 years of weeklies)
DESK_SECTOR_ETF = {"semis": "SOXX", "tech": "XLK", "materials": "XLB", "consumer": "XLY", "retail": "XRT",
                   "energy": "XLE", "industrials": "XLI"}          # old desk/market_context.py, verbatim
IND_OF_BUCKET = {"semis": "SMH", "tech": "IGV", "materials": "XME", "consumer": "XLY", "retail": "XRT",
                 "energy": "XLE", "industrials": "XLI"}
SECTOR_ETFS = list(DESK_SECTOR_ETF.values())
ETF_WEEKLY = ["SPY", "UUP"] + sorted(set(SECTOR_ETFS) | set(IND_OF_BUCKET.values()))
_MODS = {}


def _vendored(name, filename):
    if name not in _MODS:
        spec = importlib.util.spec_from_file_location(name, os.path.join(VENDOR, filename))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODS[name] = mod
    return _MODS[name]


def desk_sector(sym):
    return _vendored("old_desk_risk", "risk.py").sector(sym)


def rqa_det_lam(returns):
    return _vendored("old_math_lanes", "math_lanes.py").rqa_det_lam(returns)


# -- the weekly series ------------------------------------------------------------------------------------
def workdir(root):
    d = os.path.join(root, "cache", "m2")
    os.makedirs(d, exist_ok=True)
    return d


def _research(root, name):
    """the vendored research file decompressed once into the cache (re-done when the vendored bytes change)."""
    src = os.path.join(VENDOR, "weekly", name + ".json.gz")
    tag = hashlib.sha256(open(src, "rb").read()).hexdigest()[:16]
    out = os.path.join(workdir(root), f"{name}.{tag}.json")
    if not os.path.exists(out):
        tmp = out + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(gzip.decompress(open(src, "rb").read()))
        os.replace(tmp, out)
    return out


def universe(root):
    """the 1,754-symbol dev universe (weekly_bars_dev.json keys) — the qualifier's own symbol list."""
    path = os.path.join(workdir(root), "universe.json")
    u = read_json(path, None)
    if not u:
        u = sorted(json.load(open(_research(root, "weekly_bars_dev"))))
        write_json_atomic(path, u)
    return u


def _iso_day(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT00:00:00Z")


def _alpaca_weekly(hub, symbols, start_ts, now):
    """raw Alpaca 1Week bars (SIP, adjustment=all) INCLUDING the current week — the old fetch_weekly kept the
    week the rank ran in (complete after Friday's close); the hub's completed-bar filter would drop it."""
    from ..data.providers import parse_ts
    if hub.alpaca is None:
        raise RuntimeError("alpaca data unavailable (no credentials)")
    out = {}
    syms = list(symbols)
    for i in range(0, len(syms), 200):
        r = hub.alpaca.c.stock_bars(syms[i:i + 200], "1Week", start=_iso_day(start_ts),
                                    end=datetime.fromtimestamp(now - 16 * 60, tz=timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"), feed="sip", adjustment="all")
        for s, bl in (r or {}).items():
            out[s] = sorted(({"t": int(parse_ts(b["t"])), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                              "v": b.get("v") or 0} for b in bl), key=lambda b: b["t"])
    return out


def topup(hub, root, symbols, now, weeks_back=12):
    """old update_weekly_cache: the last 12 weeks per symbol merged into the incremental cache by t, bounded to
    170 bars. Returns (n_ok, errs)."""
    path = os.path.join(workdir(root), "weekly_incr.json")
    cache = read_json(path, {}) or {}
    errs, fresh = [], {}
    syms = list(symbols)
    for i in range(0, len(syms), 200):                  # a failed request fails each of its symbols (old: per symbol)
        batch = syms[i:i + 200]
        try:
            fresh.update(_alpaca_weekly(hub, batch, now - weeks_back * 7 * 86400, now))
        except Exception as e:  # noqa: BLE001
            errs += [(s, str(e)[:100]) for s in batch]
    failed = {e[0] for e in errs}
    for s in symbols:
        if s in failed:
            continue
        if s not in fresh:
            errs.append((s, "no bars"))
            continue
        by_t = {b["t"]: b for b in cache.get(s, [])}
        for b in fresh[s]:
            by_t[b["t"]] = b
        cache[s] = sorted(by_t.values(), key=lambda b: b["t"])[-INCR_KEEP:]
    write_json_atomic(path, cache)
    return len(symbols) - len(errs), errs


def run_qualifiers(root, node="node", timeout=1800):
    """the vendored qualify_week.mjs over dev + holdout + incremental bars; its old-host import and data paths
    are rewritten into a run copy (the vendored file stays byte-identical)."""
    src = open(os.path.join(VENDOR, "confluence", "qualify_week.mjs")).read()
    wd = workdir(root)
    reps = {
        json.dumps(OLD_HOST + "engine/tensor_exact/lib/anna-replica.mjs"):
            json.dumps(os.path.join(VENDOR, "tensor_exact", "lib", "anna-replica.mjs")),
        json.dumps(OLD_HOST + "engine/tensor_exact/lib/tensor-enrichment-signals.mjs"):
            json.dumps(os.path.join(VENDOR, "tensor_exact", "lib", "tensor-enrichment-signals.mjs")),
        'const DEV = REPO + "desk/research/weekly-phenotypes/weekly_bars_dev.json";':
            "const DEV = %s;" % json.dumps(_research(root, "weekly_bars_dev")),
        'const PLUS = REPO + "desk/research/winner-confluence/holdout/weekly_2022plus.json";':
            "const PLUS = %s;" % json.dumps(_research(root, "weekly_2022plus")),
        'const INCR = REPO + "desk/hidden_state/confluence_weekly_incr.json";':
            "const INCR = %s;" % json.dumps(os.path.join(wd, "weekly_incr.json")),
    }
    for a, b in reps.items():
        if src.count(a) != 1:
            raise RuntimeError(f"qualify_week.mjs path anchor not found: {a[:60]}")
        src = src.replace(a, b)
    run = os.path.join(wd, "qualify_week.run.mjs")
    with open(run, "w") as fh:
        fh.write(src)
    p = subprocess.run([node, run], capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        try:
            return json.loads(p.stdout)
        except Exception:
            raise RuntimeError(f"qualify_week.mjs failed rc={p.returncode}: {(p.stderr or p.stdout)[:300]}")
    return json.loads(p.stdout)


# -- features (old compute_features, verbatim) -------------------------------------------------------------
def etf_px(hub, sym, now):
    """old fetch_weekly_etf: 90 weeks of weekly closes keyed by the bar's ET Monday date."""
    out = {}
    for b in _alpaca_weekly(hub, [sym], now - 90 * 7 * 86400, now).get(sym, []):
        dt = datetime.fromtimestamp(b["t"], tz=ET)
        out[(dt + timedelta(hours=4)).date().isoformat()] = b["c"]
    return out


def etf_series(px_by_date, monday, n):
    md = datetime.strptime(monday, "%Y-%m-%d").date()
    return [px_by_date.get((md - timedelta(weeks=k)).isoformat()) for k in range(n - 1, -1, -1)]


def wret(closes, k):
    if len(closes) < k + 1 or closes[0] is None or closes[-1] is None or closes[0] == 0:
        return None
    return closes[-1] / closes[0] - 1


def sector_bucket(sym, wcloses, etf_px_map, monday):
    """desk sector map, else the study's 60-week return-correlation fallback."""
    b = desk_sector(sym)
    if b:
        return b
    import numpy as np
    if not wcloses or len(wcloses) < 41:
        return None
    c61 = wcloses[-61:]
    if len(c61) < 41 or any(x is None or x == 0 for x in c61):
        return None
    nr = np.diff(np.log(np.array(c61, dtype=float)))
    nr = nr[np.isfinite(nr)]
    best, bestb = -2, None
    for se in SECTOR_ETFS:
        sc = etf_series(etf_px_map.get(se, {}), monday, 61)
        if any(x is None for x in sc):
            continue
        sca = np.array(sc, dtype=float)
        if (sca <= 0).any():
            continue
        sr = np.diff(np.log(sca))
        m = min(len(nr), len(sr))
        if m >= 40:
            cc = np.corrcoef(nr[-m:], sr[-m:])[0, 1]
            if np.isfinite(cc) and cc > best:
                best, bestb = cc, {v: k for k, v in DESK_SECTOR_ETF.items()}[se]
    return bestb


def compute_features(quals, etf_px_map, monday, fetch_daily_fn):
    """the old compute_features: [(qualifier, feat)] for the 9 HOLDING rules (E/X/M/Q/P blocks)."""
    import numpy as np
    scored = []
    daily_cache = {}
    for q in quals:
        sym = q["symbol"]
        b0 = q["bar"]
        feat = {}
        feat["E_WEEK_BIGRANGE"] = ((b0["h"] - b0["l"]) / b0["c"] > 0.08 if b0["c"] else False)
        feat["E_ENR_EXTENSION"] = "extension-warning" in (q.get("enrich") or [])
        feat["E_FAST_BULL"] = q.get("fastState") == "bullish"
        cal, cl = q.get("calendarAvwap"), q.get("close")
        feat["E_AVWAP_CAL_ABOVE"] = cal is not None and cl > cal
        feat["E_AVWAP_CAL_FAR"] = (cal is not None and cal > 0 and (cl - cal) / cal > 0.05)
        feat["E_VOTES_NET_HIGH"] = ((q.get("bull") or 0) - (q.get("bear") or 0)) >= 4
        uup = etf_series(etf_px_map.get("UUP", {}), monday, 14)
        r = wret(uup, 13)
        feat["X_DOLLAR_WEAK"] = r is not None and r < 0
        bucket = sector_bucket(sym, q.get("wcloses") or [], etf_px_map, monday)
        feat["_bucket"] = bucket
        if bucket:
            se = etf_series(etf_px_map.get(DESK_SECTOR_ETF[bucket], {}), monday, 61)
            sp = etf_series(etf_px_map.get("SPY", {}), monday, 14)
            if all(x is not None for x in se) and all(x is not None for x in sp):
                rs, rm = wret(se[-14:], 13), wret(sp, 13)
                if rs is not None and rm is not None:
                    feat["X_SECT_LEAD"] = (rs - rm) > 0.03
        if sym not in daily_cache:
            try:
                daily_cache[sym] = fetch_daily_fn(sym)
            except Exception:
                daily_cache[sym] = []
        db = daily_cache[sym]
        di = None
        for i in range(len(db) - 1, -1, -1):
            if db[i]["date"] <= q["friday"]:
                di = i
                break
        if di is not None and di >= 60:
            w = db[di - 59: di + 1]
            h20 = max(b["h"] for b in w[-20:])
            l20 = min(b["l"] for b in w[-20:])
            feat["M_DAILY_RANGE_HI"] = bool((w[-1]["c"] - l20) / (h20 - l20) >= 0.8) if h20 > l20 else False
        lr = None
        wc = [x for x in (q.get("wcloses") or []) if x]
        if len(wc) >= 41 and all(x > 0 for x in wc):
            lr = np.diff(np.log(np.array(wc[-52:], dtype=float)))
        elif di is not None and di >= 60:
            dc = np.array([b["c"] for b in db[di - 59: di + 1]], dtype=float)
            if (dc > 0).all():
                lr = np.diff(np.log(dc))
        if lr is not None and np.all(np.isfinite(lr)):
            try:
                _det, lam = rqa_det_lam(lr)
                feat["Q_LAM_HIGH"] = lam >= CUT_LAM
            except Exception:
                pass
        if bucket and bucket in IND_OF_BUCKET:
            ic = etf_series(etf_px_map.get(IND_OF_BUCKET[bucket], {}), monday, 61)
            if all(x is not None for x in ic):
                feat["P_IND_TREND"] = ic[-1] > float(np.mean(ic[-40:]))
        scored.append((q, feat))
    return scored


def _daily(hub, sym, today, include_today):
    """old fetch_daily(days=120): adjustment=all daily bars by ET session date; confluence's drops the rank day."""
    bl = hub.bars("equity", "1d", [sym], 110).get(sym) or []
    rows = [{"date": datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat(),
             "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b.get("v") or 0} for b in bl]
    return rows if include_today else [r for r in rows if r["date"] < today]


def _valid(q):
    return isinstance(q, dict) and q.get("symbol") and isinstance(q.get("bar"), dict) and q.get("friday") \
        and "m2" in q


# -- the weekly job -----------------------------------------------------------------------------------------
def run(hub, root, now, node="node"):
    today = datetime.fromtimestamp(now, tz=ET).date().isoformat()
    path = os.path.join(workdir(root), "qualifiers.json")
    done = read_json(path, None) or {}
    if done.get("rank_date") == today and not done.get("wait"):
        return {"rank_date": today, "skip": "already written", "asof_monday": done.get("asof_monday")}
    syms = universe(root)
    n_ok, errs = topup(hub, root, syms, now)
    if len(errs) > FETCH_ERR_LIMIT:
        out = {"rank_date": today, "wait": f"{len(errs)}/{len(syms)} weekly fetches failed", "errs": errs[:8]}
        write_json_atomic(path, out)
        return out
    qres = run_qualifiers(root, node=node)
    if qres.get("error") or not qres.get("asof_monday") or not isinstance(qres.get("qualifiers"), list):
        out = {"rank_date": today, "wait": "qualifier pass: %s" % (qres.get("error") or "malformed payload")}
        write_json_atomic(path, out)
        return out
    monday = qres["asof_monday"]
    quals = [q for q in qres["qualifiers"] if _valid(q)]
    px, etf_errs = {}, []
    for e in ETF_WEEKLY:
        try:
            px[e] = etf_px(hub, e, now)
        except Exception:  # noqa: BLE001
            etf_errs.append(e)
    if "SPY" in etf_errs or "UUP" in etf_errs:
        out = {"rank_date": today, "wait": f"ETF fetch failed for {etf_errs}"}
        write_json_atomic(path, out)
        return out
    bd = compute_features(quals, px, monday, lambda s: _daily(hub, s, today, True))
    cf = compute_features(quals, px, monday, lambda s: _daily(hub, s, today, False))
    rows = [dict(q, feat_bd=fb, feat_cf=fc) for (q, fb), (_q, fc) in zip(bd, cf)]
    out = {"rank_date": today, "computed_at": now, "asof_monday": monday, "n_symbols": qres.get("n_symbols"),
           "n_short": qres.get("n_short"), "n_stale": qres.get("n_stale"), "n_topup_errors": len(errs),
           "etf_errors": etf_errs, "qualifiers": rows}
    write_json_atomic(path, out)
    return out


def load_file(path, today):
    """the qualifier file written for this rank day, else None (the rank waits)."""
    d = read_json(path, None)
    if not d or d.get("rank_date") != today:
        return None
    return d
