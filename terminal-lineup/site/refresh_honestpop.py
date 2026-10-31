#!/usr/bin/env python3
"""Refresh the Honest POP Engine (Forecast Engine 5).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   The best-calibrated probability-of-profit construction in the
   corpus's graded evidence record, grade B, calibration only:
   study row AD-58 of
   terminal-lineup/records/forecast-search-2026-10-27/EVIDENCE.md.
   Its driftless N(d2) chance, built on the last 30 trading days'
   realised movement (HV30), predicted an 82.4 percent win rate
   against 83.0 percent realised at 1 session on SPY. The same
   study measured the implied-volatility version of the chance
   understating the realised win rate by 12 to 15 points (75.7
   predicted against 87.6 to 90.3 realised). The study's own
   caveat is part of the evidence: a win rate is not an edge; it
   counts wins and ignores loss size. This engine's own live
   record: none yet, for the data reason stated below.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - The chance for a strike: N(d2) with no drift and no interest
     or dividend term (the study's driftless construction):
     d2 = (ln(spot / strike) - 0.5 x sigma^2 x T) / (sigma x
     sqrt(T)), T in years as calendar days to expiry / 365.
   - Sigma for the engine's own surface: HV30, the annualised
     standard deviation of the last 30 daily log returns of the
     index fund in the shipped daily price history on record,
     times sqrt(252). One sigma per index per day, not per
     strike: the study's construction carries no skew, and none
     is invented here.
   - The blend: the engine's stated chance is half the HV30
     N(d2) chance and half the index's own empirical finish
     share: over every past window in the shipped history with
     the same number of trading days left to expiry, the share
     of windows whose final close, applied to today's price,
     would have finished above the strike. Equal halves, fixed
     in advance; the study names the two ingredients and no
     weights, so the weights are this engine's stated choice.
   - Expected move (EM): spot x HV30 x sqrt(T). Only listed
     strikes within plus or minus 2 EM of the spot are forecast.
   - The weekly expiry: the first Friday expiry in the stored
     chain that falls after the snapshot day. Days remaining is
     calendar days from the snapshot day to that expiry.
   - The implied-volatility correction: when a chance is built
     from implied volatility (the market's own priced
     volatility), 13.5 points, the middle of the study's
     measured 12 to 15 point understatement, are added and the
     result held inside 1 to 99 percent. The engine's own
     surface is built from realised movement, not implied
     volatility, so the correction is not applied to it. The
     comparison surface below is the implied-volatility chance
     with NO correction, exactly as the retirement test requires.
   - The comparison surface: for every forecast strike, the
     uncorrected implied-volatility N(d2) chance, using that
     strike's own recorded implied volatility (the average of
     its call and put readings where both exist). It is recorded
     in the same ledger, on the same day, for the same expiry,
     so the retirement test compares two real records.
   - Ledger shape: one record per strike per surface per day.
     The engine's chance carries the marker "honest" and the
     comparison's carries "iv_uncorrected" inside its recorded
     value, because the shared record's duplicate check does not
     look at which surface a chance came from; the marker keeps
     the two surfaces from ever being mistaken for duplicates of
     each other. The outcome graded at expiry is the final close
     finishing above the strike. Families: the chain is modelled
     inventory; the realised-movement series is distributional
     volatility (the registry's own assignment for this engine).
   - Thin-cell rule: any group with fewer than 30 graded strikes
     shows its count only, no score and no rate.
   - Data on record today, stated exactly: the stored chain
     archive (morgue/state/morgue/chains/) does not exist on
     this disk: 0 stored snapshots for SPY, QQQ and IWM, no
     expiry on record, no strike list on record. The daily
     Morning Map reads a live chain each morning and keeps only
     totals from it: for the session of 2026-10-27 its SPY card
     counted 7,230 of 8,683 contracts and kept the price level
     (771.65), the two walls, the flip level, one movement total
     per expiry, and the 8 strikes with the largest totals. No
     per-strike implied volatility and no full strike list are
     kept, so no stored record today can supply the listed
     strikes or their implied volatilities for the current
     weekly expiry. Consequence, stated plainly rather than
     worked around: no surface is computed from real chain data
     today, nothing is recorded in the live ledger, and the
     engine ships in its waiting state. The computation itself
     is proven end to end in a self-test (below) on a made-up
     chain and against the independent option model kept in
     terminal-lineup/oracle/, writing only to a throwaway copy
     of the ledger. The first stored snapshot starts the real
     record, unchanged.

3. NON-CLAIMS
   - No live chance, surface or score is claimed today, because
     the stored chain the forecast is read from holds nothing
     yet. The counts proving that are published.
   - The earlier study's figures are that study's record, shown
     labelled as history; they are not this engine's results.
   - A chance of finishing above a strike says nothing about
     how much a trade on it would win or lose, or whether any
     trade pays. That limit is printed on the page in plain
     words.
   - Nothing from the self-test or any history computation is
     ever written to the live ledger. Only surfaces computed
     from a stored chain snapshot are recorded there, through
     the machinery's own append call.

=====================================================================
Behaviour: check the stored chain archive and the price history
(fails closed on any disagreement between them, or with the
ledger), run the self-test, compute and record today's surfaces
only when a stored snapshot exists, then write data.json with
figures recomputed from the ledger alone. Idempotent: rerunning
with the same sources records nothing new and rewrites the same
data.json. Timestamps come from the sources, never the clock.
"""

import gzip
import json
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
CHAINS_DIR = os.path.expanduser("~/workspace/morgue/state/morgue/chains")
EXT_PATH = os.path.expanduser("~/workspace/morgue/state/morgue/ext.json")
MAP_CARD_PATH = os.path.expanduser("~/workspace/morgue/output/map_card.json")
ORACLE_JS = os.path.join(LINEUP, "oracle", "codex_app.js")
OUT_PATH = os.path.join(HERE, "honest-pop", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
try:
    import options_gate as _og
except ImportError:  # candidate gate unavailable
    _og = None
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_05"
SYMBOLS = ("SPY", "QQQ")
EM_BAND = 2.0               # strikes within plus or minus 2 EM
BLEND_HV = 0.5              # half HV30 N(d2), half empirical finish
IV_CORRECTION_POINTS = 13.5  # middle of AD-58's measured 12 to 15
THIN = 30
PROVING_EXPIRIES = 26
OCC_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")


def fail(msg):
    print(f"Honest POP refresh: {msg}", file=sys.stderr)
    return 1


# ---- pure computation -------------------------------------------------
def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pop_nd2(spot, strike, t_years, sigma):
    """Driftless N(d2): the chance the final close finishes above
    the strike, with no drift, interest or dividend term."""
    if t_years <= 0 or sigma <= 0:
        return 1.0 if spot > strike else 0.0
    d2 = (math.log(spot / strike)
          - 0.5 * sigma * sigma * t_years) / (sigma * math.sqrt(t_years))
    return ncdf(d2)


def hv30(closes):
    """Annualised movement from the last 30 daily log returns."""
    if len(closes) < 31:
        return None
    rets = [math.log(closes[i] / closes[i - 1])
            for i in range(len(closes) - 30, len(closes))]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def empirical_finish(closes, horizon_sessions, spot, strike):
    """Share of past windows of horizon_sessions whose final close,
    applied to today's spot, would have finished above the strike."""
    if horizon_sessions < 1 or len(closes) <= horizon_sessions:
        return None
    hits = total = 0
    for i in range(len(closes) - horizon_sessions):
        total += 1
        if spot * closes[i + horizon_sessions] / closes[i] > strike:
            hits += 1
    return hits / total if total else None


def corrected_iv_pop(p_iv):
    """The IV-built chance with the study's measured understatement
    corrected: plus 13.5 points, held inside 1 to 99 percent."""
    return min(max(p_iv + IV_CORRECTION_POINTS / 100.0, 0.01), 0.99)


def compute_surface(symbol, spot, closes, expiry, as_of, strikes_iv):
    """strikes_iv: {strike: iv or None} for one expiry, from a chain
    record. Returns the surface rows inside plus or minus 2 EM, or
    None when an input the forecast needs does not exist."""
    sigma = hv30(closes)
    if sigma is None:
        return None
    days = (expiry - as_of).days
    if days < 1:
        return None
    t_years = days / 365.0
    em = spot * sigma * math.sqrt(t_years)
    # Trading days left: chain snapshot day to expiry, counted on
    # the price history's own session list where it reaches, else
    # weekday count. The empirical window needs a session count.
    horizon = max(1, round(days * 5 / 7))
    rows = []
    for strike in sorted(strikes_iv):
        if abs(strike - spot) > EM_BAND * em:
            continue
        p_hv = pop_nd2(spot, strike, t_years, sigma)
        p_emp = empirical_finish(closes, horizon, spot, strike)
        if p_emp is None:
            return None
        p = min(max(BLEND_HV * p_hv + (1 - BLEND_HV) * p_emp, 0.01), 0.99)
        iv = strikes_iv[strike]
        bench = (pop_nd2(spot, strike, t_years, iv)
                 if iv else None)
        rows.append({
            "strike": strike,
            "p": round(p, 4), "p_pct": round(p * 100.0, 1),
            "benchmark_p": (round(bench, 4) if bench is not None
                            else None),
            "benchmark_p_pct": (round(bench * 100.0, 1)
                                if bench is not None else None),
        })
    return {"symbol": symbol, "spot": spot, "expiry": expiry.isoformat(),
            "days_remaining": days, "hv30_pct": round(sigma * 100.0, 2),
            "expected_move": round(em, 2), "rows": rows}


# ---- stored chain archive ----------------------------------------------
def stored_days(symbol):
    d = os.path.join(CHAINS_DIR, symbol)
    try:
        names = os.listdir(d)
    except OSError:
        return []
    return sorted(n[:-8] for n in names if n.endswith(".json.gz"))


def parse_occ(code, underlying):
    m = OCC_RE.match(code or "")
    if not m:
        return None
    root, ymd, kind, strike8 = m.groups()
    if root != underlying:
        return None
    expiry = f"20{ymd[0:2]}-{ymd[2:4]}-{ymd[4:6]}"
    return expiry, kind == "C", int(strike8) / 1000.0


def read_snapshot(symbol, day):
    """One stored snapshot, validated the same way the Chain
    Explorer validates it. Returns (snapshot, None) or
    (None, error)."""
    path = os.path.join(CHAINS_DIR, symbol, f"{day}.json.gz")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, EOFError):
        return None, f"the stored chain for {symbol} on {day} cannot be read"
    if doc.get("underlying") != symbol or doc.get("day") != day:
        return None, (f"the stored chain filed as {symbol} {day} calls "
                      f"itself {doc.get('underlying')} {doc.get('day')}")
    spot = doc.get("spot")
    if not isinstance(spot, (int, float)) or isinstance(spot, bool) \
            or spot <= 0:
        return None, f"the stored chain for {symbol} on {day} has no spot"
    cols = doc.get("columns") or []
    if cols[:1] != ["occ"] or not {"oi", "volume", "iv"} <= set(cols[1:]):
        return None, (f"the stored chain for {symbol} on {day} does not "
                      f"carry the fields this engine reads")
    idx = {name: cols.index(name) for name in cols}
    rows = doc.get("rows") or []
    if not rows:
        return None, f"the stored chain for {symbol} on {day} is empty"
    by_expiry = {}
    seen = set()
    candidates = []
    greek_idx = (idx.get("greek_ts") if "greek_ts" in idx
                 else idx.get("greeks_ts"))
    for row in rows:
        if not isinstance(row, list) or len(row) != len(cols):
            return None, "a contract row does not match the record's layout"
        code = row[idx["occ"]]
        if code in seen:
            return None, f"the contract {code} appears twice on {day}"
        seen.add(code)
        parsed = parse_occ(code, symbol)
        if parsed is None:
            return None, f"the contract code {code} does not parse"
        expiry, is_call, strike = parsed
        iv = row[idx["iv"]]
        if iv is not None and (not isinstance(iv, (int, float))
                               or isinstance(iv, bool) or iv <= 0):
            return None, f"{code} on {day}: implied volatility not positive"
        greek_ts = row[greek_idx] if greek_idx is not None else None
        candidates.append({"iv": iv, "greek_ts": greek_ts})
        if _og is not None:
            verdict = _og.gate_candidate(
                {"iv": iv, "greek_ts": greek_ts},
                doc.get("captured_at_utc"))
            if not verdict["admitted"]:
                # The candidate gate skips this contract's IV: an
                # over ceiling IV, or Greeks too stale or future
                # dated to rank on, never reach the comparison
                # surface. The strike itself stays on record with
                # no IV figure, exactly like an absent IV.
                iv = None
        slot = by_expiry.setdefault(expiry, {}).setdefault(
            strike, {"call": None, "put": None})
        slot["call" if is_call else "put"] = iv
    expiries = {}
    for expiry, strikes in by_expiry.items():
        expiries[expiry] = {}
        for strike, pair in strikes.items():
            ivs = [v for v in (pair["call"], pair["put"]) if v]
            expiries[expiry][strike] = (sum(ivs) / len(ivs)) if ivs else None
    gate = None
    if _og is not None:
        gate = _og.gate_summary(candidates, doc.get("captured_at_utc"))
        gate["note"] = (
            "Candidate gate applied to this snapshot: Greeks "
            "older than 75 minutes, future dated Greeks and IV "
            "at or over 500 percent are refused; contracts whose "
            "source supplies no Greek timestamp are labelled "
            "undated, not silently trusted.")
    return {"day": day, "spot": float(spot), "expiries": expiries,
            "contracts": len(rows), "path": path,
            "options_gate": gate}, None


# ---- self-test: oracle cross-check + synthetic chain --------------------
def _extract_js_func(text, name):
    start = text.index(f"function {name}(")
    i = text.index("{", start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    raise ValueError(name)


def oracle_self_test(panel):
    """Prove the chance math against the independent option model in
    terminal-lineup/oracle/, and the whole surface computation on a
    made-up chain written to a throwaway ledger copy. Returns a
    result dict; raises on any disagreement."""
    with open(ORACLE_JS, "r", encoding="utf-8") as fh:
        js_text = fh.read()
    funcs = "\n".join(_extract_js_func(js_text, n) for n in
                      ("standardNormalCdf", "blackScholesEuropean"))
    cases = []
    for spot, strike, days, sigma in (
            (760.0, 700.0, 3, 0.14), (760.0, 760.0, 3, 0.14),
            (760.0, 820.0, 3, 0.14), (704.4, 650.0, 10, 0.21),
            (704.4, 704.4, 10, 0.21), (100.0, 95.0, 30, 0.35),
            (100.0, 110.0, 30, 0.35), (771.65, 780.0, 2, 0.11)):
        cases.append({"spot": spot, "strike": strike, "days": days,
                      "sigma": sigma})
    script = funcs + """
const cases = JSON.parse(process.argv[2]);
const out = cases.map(c => {
  const r = blackScholesEuropean(c.spot, c.strike, c.days, c.sigma * 100, 0, 0, 'call');
  // With no interest or dividends, the call price is
  // spot x N(d1) - strike x N(d2), and delta is N(d1); so the
  // model's own N(d2) falls out of its price and delta.
  const nd2 = (c.spot * r.delta - r.theoreticalPrice) / c.strike;
  return {nd2, cdf: standardNormalCdf(0.37)};
});
console.log(JSON.stringify(out));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(script)
        js_path = fh.name
    try:
        raw = subprocess.run(["node", js_path, json.dumps(cases)],
                             capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(js_path)
    if raw.returncode != 0:
        raise RuntimeError(f"oracle run failed: {raw.stderr.strip()}")
    oracle = json.loads(raw.stdout)
    max_diff = 0.0
    for case, got in zip(cases, oracle):
        mine = pop_nd2(case["spot"], case["strike"],
                       case["days"] / 365.0, case["sigma"])
        max_diff = max(max_diff, abs(mine - got["nd2"]))
    cdf_diff = abs(ncdf(0.37) - oracle[0]["cdf"])
    if max_diff > 2e-4 or cdf_diff > 2e-6:
        raise RuntimeError(
            f"oracle disagreement: N(d2) max diff {max_diff:.2e}, "
            f"cdf diff {cdf_diff:.2e}")

    # Synthetic chain, end to end, on a throwaway ledger.
    from datetime import date
    closes = [float(r[4]) for r in panel["SPY"]]
    spot = closes[-1]
    as_of = date(2026, 10, 23)          # a Friday
    expiry = date(2026, 10, 30)         # the next Friday, a full week
    strikes_iv = {}
    k = 600.0
    while k <= 920.0:
        strikes_iv[k] = 0.16 + 0.00012 * max(0.0, spot - k)
        k += 5.0
    surface = compute_surface("SPY", spot, closes, expiry, as_of,
                              strikes_iv)
    if surface is None or not surface["rows"]:
        raise RuntimeError("synthetic surface came back empty")
    ps = [r["p"] for r in surface["rows"]]
    if any(ps[i] < ps[i + 1] - 1e-9 for i in range(len(ps) - 1)):
        raise RuntimeError("synthetic surface is not falling in strike")
    if any(r["benchmark_p"] is None for r in surface["rows"]):
        raise RuntimeError("synthetic benchmark surface is incomplete")
    corr = corrected_iv_pop(surface["rows"][0]["benchmark_p"])
    if not (surface["rows"][0]["benchmark_p"] < corr <= 0.99):
        raise RuntimeError("the IV correction did not lift the IV chance")
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        scratch = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                    registry=reg)
        scratch.append_genesis("honest-pop self-test scratch ledger")
        lineage = {
            "source_artifacts": [
                {"path": "synthetic-chain (self-test, not a record)",
                 "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
            "clocks": {c: "2026-10-23" for c in ledger_mod.CLOCK_FIELDS},
            "note": "Self-test only; never the live record."}
        made = 0
        for row in surface["rows"]:
            for marker, p in (("honest", row["p"]),
                              ("iv_uncorrected", row["benchmark_p"])):
                _r, created = scratch.append_forecast_declared(
                    engine_id=ENGINE_ID, issued_ts="2026-10-23",
                    subject=f"SPY {surface['expiry']} strike {row['strike']}",
                    quantity="finish_above_probability",
                    value={"p": p, "surface": marker},
                    horizon_open="2026-10-23",
                    horizon_close=surface["expiry"],
                    lineage=lineage,
                    families=["modelled_inventory",
                              "distributional_volatility"],
                    outcome={"symbol": "SPY", "kind": "close_above",
                             "at_date": surface["expiry"],
                             "threshold": row["strike"]})
                made += 1 if created else 0
        figs = ledger_mod.recompute_figures(scratch.rows())
        if not scratch.verify_chain() \
                or figs[ENGINE_ID]["forecasts"] != made \
                or made != 2 * len(surface["rows"]):
            raise RuntimeError("scratch ledger round-trip failed")
    return {"oracle_cases": len(cases),
            "oracle_max_difference": round(max_diff, 8),
            "synthetic_strikes": len(surface["rows"]),
            "synthetic_records_written_to_a_throwaway_copy": made,
            "state": "passed"}


# ---- build ---------------------------------------------------------------
def build():
    if not os.path.exists(PANEL_PATH):
        return fail(f"price history not found: {PANEL_PATH}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    for sym in SYMBOLS:
        if sym not in panel:
            return fail(f"the price history carries no {sym}")
    panel_as_of = panel["SPY"][-1][0]

    # ---- What chain data actually exists on record ----
    archive_days = {sym: stored_days(sym) for sym in ("SPY", "QQQ", "IWM")}
    archive_total = sum(len(v) for v in archive_days.values())
    ext = {}
    if os.path.exists(EXT_PATH):
        with open(EXT_PATH, "r", encoding="utf-8") as fh:
            ext = json.load(fh)
    chain_stamps = (ext.get("chain") or {}).get("cards") or {}
    map_note = None
    if os.path.exists(MAP_CARD_PATH):
        with open(MAP_CARD_PATH, "r", encoding="utf-8") as fh:
            map_card = json.load(fh)
        for card in map_card.get("cards") or []:
            if card.get("underlying") == "SPY":
                map_note = {
                    "session": card.get("dix_date"),
                    "spot": card.get("spot"),
                    "contracts_counted": card.get("contracts_used"),
                    "contracts_total": card.get("chain_total"),
                    "expiries_with_totals": len(card.get("by_expiry") or {}),
                    "strikes_kept": len(
                        card.get("top_strikes_by_abs_gex") or []),
                }

    # ---- Self-test (always; proves the math in either state) ----
    try:
        self_test = oracle_self_test(panel)
    except Exception as exc:  # fail closed: no proof, no page figures
        return fail(f"self-test failed, refusing to publish: {exc}")

    # ---- Ledger (API only) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")

    # ---- Live surfaces, only from a stored snapshot ----
    from datetime import date
    surfaces = []
    created = 0
    for sym in SYMBOLS:
        days = archive_days[sym]
        if not days:
            continue
        snap, err = read_snapshot(sym, days[-1])
        if err:
            return fail(err)
        rows_panel = panel[sym]
        closes = [float(r[4]) for r in rows_panel]
        by_date = {r[0]: float(r[4]) for r in rows_panel}
        if snap["day"] in by_date:
            gap = abs(snap["spot"] / by_date[snap["day"]] - 1.0)
            if gap > 0.02:
                return fail(
                    f"the stored chain for {sym} on {snap['day']} puts "
                    f"the price at {snap['spot']} but the price history "
                    f"says {by_date[snap['day']]}; refusing to publish "
                    f"a surface the two records disagree on")
        as_of = date.fromisoformat(snap["day"])
        fridays = [e for e in sorted(snap["expiries"])
                   if date.fromisoformat(e) > as_of
                   and date.fromisoformat(e).weekday() == 4]
        if not fridays:
            return fail(f"the stored chain for {sym} holds no Friday "
                        f"expiry after {snap['day']}")
        expiry = date.fromisoformat(fridays[0])
        surface = compute_surface(sym, snap["spot"], closes, expiry,
                                  as_of, snap["expiries"][fridays[0]])
        if surface is None or not surface["rows"]:
            return fail(f"the stored chain for {sym} cannot produce a "
                        f"surface for {fridays[0]}")
        surface["snapshot_day"] = snap["day"]
        surface["contracts_on_record"] = snap["contracts"]
        surface["options_gate"] = snap.get("options_gate")
        lineage = {
            "source_artifacts": [
                {"path": snap["path"],
                 "sha256": ledger_mod.file_sha256(snap["path"])},
                {"path": PANEL_PATH,
                 "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
            "clocks": {c: snap["day"] for c in ledger_mod.CLOCK_FIELDS},
            "note": ("Finish-above chances for the weekly expiry, "
                     "recorded at the snapshot day's close and graded "
                     "at the expiry close, every recorded strike "
                     "counted.")}
        for row in surface["rows"]:
            for marker, p in (("honest", row["p"]),
                              ("iv_uncorrected", row["benchmark_p"])):
                if p is None:
                    continue
                _r, was = led.append_forecast_declared(
                    engine_id=ENGINE_ID, issued_ts=snap["day"],
                    subject=(f"{sym} {surface['expiry']} strike "
                             f"{row['strike']}"),
                    quantity="finish_above_probability",
                    value={"p": p, "surface": marker},
                    horizon_open=snap["day"],
                    horizon_close=surface["expiry"],
                    lineage=lineage,
                    families=["modelled_inventory",
                              "distributional_volatility"],
                    outcome={"symbol": sym, "kind": "close_above",
                             "at_date": surface["expiry"],
                             "threshold": row["strike"]})
                created += 1 if was else 0
        surfaces.append(surface)

    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    graded_expiries = len({r["horizon_close"] for r in rows
                           if r.get("type") == "grade"
                           and r.get("engine_id") == ENGINE_ID})
    waiting = not surfaces

    data = {
        "tool": "Honest POP Engine",
        "state": "proving",
        "waiting": waiting,
        "as_of": (surfaces[0]["snapshot_day"] if surfaces
                  else ((ext.get("chain") or {}).get("as_of")
                        or ext.get("as_of") or panel_as_of)),
        "price_history_as_of": panel_as_of,
        "source": ("The stored options chains for SPY and QQQ, one "
                   "snapshot kept per trading day, read with the "
                   "price history on record (last session "
                   f"{panel_as_of})."),
        "scope_line": ("A win rate is not an edge. This page states "
                       "the chance of finishing above a strike; it "
                       "says nothing about how much a trade would "
                       "win or lose, or whether any trade pays."),
        "what_exists": {
            "archive_snapshots_total": archive_total,
            "archive_by_index": {k: len(v) for k, v in archive_days.items()},
            "archive_state_words": {
                sym: (chain_stamps.get(sym) or {}).get("reason")
                for sym in ("SPY", "QQQ", "IWM")},
            "morning_map_reading": map_note,
            "note": ("The chain archive this engine reads holds no "
                     "snapshot yet. Each morning's market map does "
                     "read a live chain and keeps totals from it "
                     "(for SPY's latest session: the price level, "
                     "the two walls, the flip level, one total per "
                     "expiry and the 8 busiest strikes), but it "
                     "keeps no full strike list and no per-strike "
                     "volatility reading, so it cannot supply this "
                     "forecast. Nothing has been filled in from it."),
        },
        "surfaces": surfaces,
        "live": {
            "records_written": mine["forecasts"],
            "records_graded": mine["graded"],
            "expiries_graded": graded_expiries,
            "proving_target_expiries": PROVING_EXPIRIES,
            "state_note": (
                "Waiting for the first stored chain snapshot. The "
                "day one is kept, this page shows, for SPY and QQQ, "
                "every listed strike within two expected moves of "
                "the price for that week's Friday expiry: the "
                "chance the final close finishes above the strike, "
                "with the market's own uncorrected chance beside "
                "it. Each day's table is written to the public "
                "record before the expiry, and at the expiry close "
                "every recorded strike is graded, winners and "
                "losers alike." if waiting else
                "Surfaces are being recorded from stored chain "
                "snapshots and graded at each weekly expiry close."),
        },
        "method": {
            "summary": ("Each chance is half of a movement-based "
                        "calculation (the last 30 trading days' "
                        "realised movement, no drift assumed) and "
                        "half of the index's own past finishes over "
                        "the same number of days. The comparison "
                        "chance beside it is the market's own priced "
                        "volatility put through the same calculation "
                        "with no correction."),
            "study_record": {
                "label": "The earlier study this engine is built from",
                "rows": [
                    {"construction": "Realised movement (30 days)",
                     "predicted_pct": 82.4, "realised_pct": 83.0,
                     "window": "1 trading day"},
                    {"construction": "Market's priced volatility",
                     "predicted_pct": 75.7, "realised_pct": "87.6 to 90.3",
                     "window": "1 trading day"},
                ],
                "note": ("On SPY in that study, the realised-movement "
                         "chance landed within a point of what "
                         "happened, and the priced-volatility chance "
                         "understated wins by 12 to 15 points. Those "
                         "are the study's figures, from its own "
                         "history. They are the reason this engine "
                         "exists; they are not this engine's results."),
            },
        },
        "self_test": self_test,
        "kill_criterion": ("This tool is retired if, after 26 weekly "
                           "expiries have been graded, its score for "
                           "how close its chances were is no better "
                           "than the score of the market's own "
                           "uncorrected chances recorded beside them."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "strikes shows its count only, with no "
                           "score headline."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: waiting={waiting}, archive snapshots "
          f"{archive_total}, surfaces {len(surfaces)}, ledger records "
          f"{mine['forecasts']} ({created} new), graded {mine['graded']}, "
          f"self-test {self_test['state']} "
          f"({self_test['oracle_cases']} oracle cases, max diff "
          f"{self_test['oracle_max_difference']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
