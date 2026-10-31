#!/usr/bin/env python3
"""Refresh the Pin-or-Escape engine (Forecast Engine 27).

=====================================================================
REGISTER TRIPLE (written before any computation, per the lineup's
adopted standards)

1. EVIDENCE CLASS
   The pin level itself has NO forward grading anywhere in the
   record: the Expiry Pin Watch publishes no pin at all today
   (0 pins on record), because no stored record carries per-strike
   open interest for a named expiry. The honest prior is therefore
   stated as UNTESTED, in the design's own words: this engine's
   first year is the first test the pin claim has ever had, and
   nothing is borrowed from the level's popularity. The graded
   definitions this engine builds on are the Morning Map record's
   own (the same card record Engine 8 imported its graded map
   definitions from, never forked here): the cards carry, per index
   fund, the price, the modelled net dealer pull and its sign, the
   walls and the flip level. This engine's own live record: none.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - The pin reading: when a stored chain snapshot exists for a
     named expiry, the pin for an index fund and that expiry is
     the strike carrying the most contracts still open (calls and
     puts added together) for that expiry in that snapshot. A
     snapshot is a kept file in the chain archive holding, per
     contract or per strike, a strike, an expiry and a count of
     contracts still open. No other level is ever substituted for
     the pin: not a wall, not the strike with the strongest pull,
     not the flip level. Today the archive holds 0 snapshots, so
     there is no pin, for any fund or any expiry, and no morning
     can be recorded.
   - Pin proximity: on the morning of an expiry day, the test is
     the session's opening price against the pin taken from the
     prior session's snapshot: within 0.3 percent either way
     (|open / pin - 1| <= 0.003) is inside the test; anything else
     is outside it and no arm forms, though the morning is counted.
   - The arms (SPY only, per the design): Arm A forms when the
     opening price is within the pin's 0.3 percent AND the index's
     net dealer pull on the prior session's card is positive AND
     the variance premium (below) is in its bottom half. Its claim:
     SPY closes within plus or minus 0.25 percent of the pin in at
     least 40 percent of such weeks. Arm B forms on the same
     proximity with the net pull negative (the variance premium is
     NOT part of Arm B's condition, per the design verbatim). Its
     claim: the close lands inside that band in at most 20 percent
     of such weeks. The arms are rate claims over weeks, not
     per-week chances: each qualifying morning records one yes/no
     outcome (did the close land in the band) and the rates are
     counted over weeks.
   - The baseline row: every pin-proximity morning, whichever arm
     it belongs to or neither, also records an unconditional row
     on the same terms, so the arms are always graded against the
     plain pin-hit rate for all near-pin mornings.
   - Net dealer pull sign readings: the sign of the prior
     session's Morning Map card figure for the fund (positive or
     negative; a card figure of exactly zero forms neither arm).
     The sign at the pin strike, used only inside the failure
     score, is read from the snapshot itself when it carries a
     per-strike pull figure; otherwise from the card's listed
     strongest strikes when the pin strike is among them; otherwise
     it is unknown, never guessed.
   - The variance premium test: no such series exists on disk, so
     its construction is fixed here, before any week is graded.
     For each SPY session t in the shipped price history: implied
     variance = (the fear gauge's close on the session before t,
     divided by 100) squared; realised variance = 252 times the
     mean of the squared daily log returns over the 21 sessions
     ending the session before t; the premium = implied minus
     realised. The fear gauge series used is the long daily file
     on this box (1990-01-02 to 2026-10-01, 9,257 rows); the
     terminal's own short gauge file (23 closes) is too thin for a
     half split and is never used for this test. The design's
     2010-to-2026 wording is NOT claimed: SPY's shipped history
     runs 2025-03-25 to 2026-10-23 (399 sessions), so the premium
     is computable only over their overlap, and its real span is
     measured and printed. Bottom half at a morning: that
     morning's premium (from the prior session) is at or below the
     middle of every premium computable BEFORE it (today's own
     value left out of its own yardstick).
   - The failure score: ONE score, fixed here, never tuned per
     week: the count of these four, each worth one point:
     (1) negative pull at the pin strike;
     (2) a big scheduled event inside the expiry session, read
         from the Week Ahead record, whose coverage is
         2026-01-01 to 2027-12-31 and whose kinds are only central
         bank decisions, consumer prices and jobs reports;
     (3) a gap opening beyond the pin strike's neighbourhood: the
         neighbourhood is the pin plus or minus one strike step
         (the typical spacing between neighbouring strikes for
         that expiry in the snapshot); the point scores when the
         opening price lands outside that neighbourhood;
     (4) a weak pin: the pin strike's open contracts are below
         the middle of the open contracts at the four nearest
         strikes (two either side).
     A part that cannot be read scores nothing and is reported as
     not readable, with the score labelled by how many of the
     four parts could be read. Today exactly 1 of the 4 parts is
     readable (the calendar part).
   - Companion rows (the same mornings, for SPY, QQQ and IWM, per
     the design's companion claim): (a) the chance the close lands
     more than half an expected move from the pin, graded as a
     probability; the expected move is Engine 1's one-session 68
     percent half-width for that fund, built by that engine's own
     recipe from the shipped price history (recent-movement
     average of the last 1, 5 and 22 sessions' squared log
     returns, annualised, times sqrt(1/252), times 0.87), never
     forked from another source. The stated chance is the plain
     no-drift bell-curve reading: the close's distance from the
     pin, in percent, is treated as a centred bell curve whose
     spread is the fund's one-session daily movement from the same
     recipe, and the chance is the share of that curve lying
     beyond half an expected move from the pin. (b) The predicted
     absolute close-to-pin distance in percent: the same bell
     curve's expected absolute distance, spread times
     sqrt(2 / pi). Both scorings are carried in the rows' outcome
     specs: the chance graded by the probability rule, the
     distance by the distance-error rule, although this engine's
     registered rule names the probability rule alone.
   - Recording: rows are written on the morning of the expiry
     day, once the opening price exists (the opening price is
     what the proximity test is made from), before the close they
     predict, through the shared record's own append call only.
     Per SPY proximity morning: the arm row (when an arm forms),
     the baseline row, and the failure-score reading carried in
     both. Per fund (SPY, QQQ, IWM) proximity morning: the two
     companion rows. A morning whose opening price or pin is not
     on record is never recorded, and past mornings are never
     backfilled.
   - Grading: at the expiry session's close, once that close is
     in the shipped price history: each arm and baseline row is
     graded yes/no on the band, with its close-to-pin distance;
     each companion chance is graded against whether the close
     really landed more than half an expected move from the pin;
     each companion distance against the real distance. Grades go
     through the shared record's own grade call, scored with the
     shared scoring functions, never a forked runner.
   - Thin-cell rule: an arm or the baseline with fewer than 30
     graded weeks shows its count only, no rate headline, on the
     page and in the verdict alike. The same holds for the
     companion figures per fund.
   - Kill criterion, in plain words, printed in advance: after
     52 weeks have been counted, if the two arms' in-band rates
     cannot be told apart, this engine retires. Told apart is
     fixed here: the plain two-share comparison of the two arms'
     rates gives a gap at least twice its own typical wobble
     (a two-proportion z of 2 or more, either way). Both arms
     must be populated for the test to run at all.
   - Ship date: this engine first published on 2026-10-29.
     Anything before that date is history, never recorded.

3. NON-CLAIMS
   - No wall, strongest-pull strike or flip level is ever shown
     or used as a pin, here or anywhere in this engine.
   - The card figures for the three funds (price, walls, flip,
     net pull) are shown only as what the map record holds; none
     of them is a pin and none enters the test until a pin exists.
   - Nothing from any history computation or self-test is ever
     written to the live record. Only a real expiry morning,
     formed from a stored snapshot's pin and that morning's
     opening price, on or after the ship date, is recorded.

=====================================================================
Behaviour: read the pin watch record, the Morning Map card, the
Week Ahead record, the shipped price history, the long fear-gauge
file and the chain archive (fails closed on any disagreement
between them, or with the shared record), run the self-test,
recompute every reading that exists today, record a morning only
when a stored snapshot gives a pin for an expiry day that is
today and its opening price is on record, grade any matured
recorded morning, then write data.json with the live figures
recomputed from the shared record alone. Idempotent: rerunning
with the same sources records nothing new and rewrites the same
data.json. Timestamps come from the sources, never the clock.
"""

import csv
import json
import math
import os
import sys
import tempfile
from datetime import date, timedelta
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
MAP_PATH = os.path.expanduser("~/workspace/morgue/output/map_card.json")
PINWATCH_PATH = os.path.join(HERE, "expiry-pin-watch", "data.json")
WEEKAHEAD_PATH = os.path.join(HERE, "week-ahead", "data.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/alpaca-swing-desk/desk/research/short-program/"
    "d6_vix_daily.csv")
CHAIN_DIR = os.path.expanduser("~/workspace/morgue/state/morgue/chains")
OUT_PATH = os.path.join(HERE, "pin-or-escape", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
try:
    import intake as _intake
except ImportError:  # guarded CSV intake unavailable; loader fails closed below
    _intake = None
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402
from forecast import grading as grading_mod  # noqa: E402

ENGINE_ID = "engine_27"
SHIP_DATE = "2026-10-29"
FUNDS = ("SPY", "QQQ", "IWM")
PROXIMITY = 0.003
BAND = 0.0025
ARM_A_CLAIM_PCT = 40.0
ARM_B_CLAIM_PCT = 20.0
THIN = 30
PROVING_WEEKS = 52
_ND = NormalDist()


def fail(msg):
    print(f"Pin-or-Escape refresh: {msg}", file=sys.stderr)
    return 1


# ---- the pin ------------------------------------------------------------------
def pin_from_strikes(strikes):
    """strikes: [{strike, open_interest}] for one fund and expiry.
    The pin is the strike with the most contracts still open."""
    if not strikes:
        return None
    best = max(strikes, key=lambda s: (s["open_interest"], -s["strike"]))
    return float(best["strike"])


def load_snapshots():
    """Read every stored chain snapshot in the accepted shapes.
    Returns {fund: {expiry: [{strike, open_interest,
    gamma_sign (optional)}]}} and the file count.

    Two shapes are accepted: the legacy per-contract JSON files
    directly under CHAIN_DIR, and the collector store (2026-10-29
    content cure): <CHAIN_DIR>/<FUND>/<day>.json.gz documents
    whose rows are [occ, oi, volume, iv] with MEASURED oi. For
    the collector shape, call and put open interest at the same
    strike and expiry are summed, because the pin is the strike
    with the most contracts still open in total."""
    out = {}
    count = 0
    if not os.path.isdir(CHAIN_DIR):
        return out, 0
    # Collector store shape (gzip rows).
    import gzip as _gzip
    import re as _re
    _occ = _re.compile(r"^([A-Z]+)(\d{6})[CP](\d{8})$")
    for fund in FUNDS:
        fund_dir = os.path.join(CHAIN_DIR, fund)
        if not os.path.isdir(fund_dir):
            continue
        for name in sorted(os.listdir(fund_dir)):
            if not name.endswith(".json.gz"):
                continue
            count += 1
            with _gzip.open(os.path.join(fund_dir, name), "rt",
                            encoding="utf-8") as fh:
                doc = json.load(fh)
            agg = {}
            for row in doc.get("rows") or []:
                if not isinstance(row, list) or len(row) < 2:
                    continue
                m = _occ.match(row[0] or "")
                oi = row[1]
                if not m or not isinstance(oi, (int, float)):
                    continue
                yy = 2000 + int(m.group(2)[:2])
                expiry = (f"{yy}-{m.group(2)[2:4]}-"
                          f"{m.group(2)[4:6]}")
                strike = int(m.group(3)) / 1000.0
                key = (expiry, strike)
                agg[key] = agg.get(key, 0.0) + float(oi)
            for (expiry, strike), oi in agg.items():
                out.setdefault(fund, {}).setdefault(
                    expiry, []).append(
                    {"strike": strike, "open_interest": oi})
    for name in sorted(os.listdir(CHAIN_DIR)):
        if not name.endswith(".json"):
            continue
        count += 1
        with open(os.path.join(CHAIN_DIR, name),
                  encoding="utf-8") as fh:
            doc = json.load(fh)
        contracts = doc.get("contracts") or doc.get("strikes") or []
        for c in contracts:
            fund = c.get("symbol") or c.get("underlying") \
                or doc.get("symbol") or doc.get("underlying")
            expiry = c.get("expiry") or c.get("expiration") \
                or doc.get("expiry")
            strike = c.get("strike")
            oi = c.get("open_interest", c.get("openInterest"))
            if fund in FUNDS and expiry and strike is not None \
                    and isinstance(oi, (int, float)):
                row = {"strike": float(strike),
                       "open_interest": float(oi)}
                g = c.get("gamma")
                if isinstance(g, (int, float)):
                    row["gamma_sign"] = 1 if g > 0 else (
                        -1 if g < 0 else 0)
                out.setdefault(fund, {}).setdefault(expiry,
                                                    []).append(row)
    return out, count


# ---- readings ---------------------------------------------------------------------
def proximity(open_price, pin):
    return abs(open_price / pin - 1.0)


def in_band(close, pin):
    return abs(close / pin - 1.0) <= BAND


def arm_for(prox, net_sign, vrp_bottom_half):
    if prox > PROXIMITY:
        return None
    if net_sign > 0 and vrp_bottom_half:
        return "arm_a"
    if net_sign < 0:
        return "arm_b"
    return None


def strike_spacing(strikes):
    ks = sorted({s["strike"] for s in strikes})
    gaps = [b - a for a, b in zip(ks, ks[1:]) if b > a]
    if not gaps:
        return None
    gaps.sort()
    return gaps[len(gaps) // 2]


def failure_score(pin, strikes, open_price, events_today,
                  pin_strike_sign):
    """The one pre-registered score. Returns (score, readable,
    parts) where parts names each part's state."""
    parts = {}
    readable = 0
    score = 0
    # (1) negative pull at the pin strike
    if pin_strike_sign is None:
        parts["negative_pull_at_pin"] = "not readable"
    else:
        readable += 1
        hit = pin_strike_sign < 0
        parts["negative_pull_at_pin"] = "yes" if hit else "no"
        score += 1 if hit else 0
    # (2) a big scheduled event inside the session
    readable += 1
    parts["event_in_session"] = "yes" if events_today else "no"
    score += 1 if events_today else 0
    # (3) gap opening beyond the pin's neighbourhood
    spacing = strike_spacing(strikes) if strikes else None
    if pin is None or open_price is None or spacing is None:
        parts["gap_beyond_neighbourhood"] = "not readable"
    else:
        readable += 1
        hit = abs(open_price - pin) > spacing
        parts["gap_beyond_neighbourhood"] = "yes" if hit else "no"
        score += 1 if hit else 0
    # (4) a weak pin: pin OI below the middle of its neighbours
    by_strike = {s["strike"]: s["open_interest"] for s in strikes} \
        if strikes else {}
    if pin is None or pin not in by_strike:
        parts["weak_pin"] = "not readable"
    else:
        ks = sorted(by_strike)
        i = ks.index(pin)
        neigh = [by_strike[k] for k in ks[max(0, i - 2):i + 3]
                 if k != pin]
        if not neigh:
            parts["weak_pin"] = "not readable"
        else:
            readable += 1
            neigh.sort()
            med = neigh[len(neigh) // 2] if len(neigh) % 2 else \
                0.5 * (neigh[len(neigh) // 2 - 1] + neigh[len(neigh) // 2])
            hit = by_strike[pin] < med
            parts["weak_pin"] = "yes" if hit else "no"
            score += 1 if hit else 0
    return score, readable, parts


def har_vol(rows, i):
    """Engine 1's recent-movement recipe at close index i: the
    equal-weight mean of the last 1, last 5 and last 22 squared
    log returns, annualised. rows are the fund's bars."""
    closes = [float(r[4]) for r in rows]
    sq = [math.log(closes[j + 1] / closes[j]) ** 2
          for j in range(len(closes) - 1)]
    daily = sq[i - 1]
    weekly = sum(sq[i - 5:i]) / 5.0
    monthly = sum(sq[i - 22:i]) / 22.0
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


def expected_move_pct(rows, i):
    """One-session 68 percent half-width in percent, Engine 1's
    recipe: annualised recent movement times sqrt(1/252) times
    0.87."""
    return 100.0 * har_vol(rows, i) * math.sqrt(1.0 / 252.0) * 0.87


def companion_forecasts(pin, open_price, em_pct, daily_vol_pct):
    """The two companion figures from the registered bell curve."""
    dist_open_pct = abs(open_price / pin - 1.0) * 100.0
    # The close is centred on the pin under the registered reading;
    # its distance from the pin follows the bell curve with the
    # fund's one-session spread.
    z = (0.5 * em_pct) / daily_vol_pct if daily_vol_pct > 0 else 0.0
    p_breach = 2.0 * (1.0 - _ND.cdf(z))
    pred_dist = daily_vol_pct * math.sqrt(2.0 / math.pi)
    return {"p_breach": round(min(max(p_breach, 0.001), 0.999), 4),
            "predicted_distance_pct": round(pred_dist, 4),
            "open_distance_pct": round(dist_open_pct, 4)}


def vrp_series(panel_spy, vix):
    """The registered variance premium over the overlap of the
    shipped SPY history and the long fear-gauge file. Returns a
    list of (session, premium) in session order."""
    dates = [r[0] for r in panel_spy]
    closes = [float(r[4]) for r in panel_spy]
    sq = [math.log(closes[j + 1] / closes[j]) ** 2
          for j in range(len(closes) - 1)]
    out = []
    for i in range(22, len(dates)):
        prev = dates[i - 1]
        if prev not in vix:
            continue
        implied = (vix[prev] / 100.0) ** 2
        realised = 252.0 * (sum(sq[i - 22:i]) / 22.0)
        out.append((dates[i], implied - realised))
    return out


def bottom_half(premiums_before, value):
    if not premiums_before:
        return None
    s = sorted(premiums_before)
    med = s[len(s) // 2] if len(s) % 2 else \
        0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2])
    return value <= med, med


def two_share_z(hits_a, n_a, hits_b, n_b):
    if not n_a or not n_b:
        return None
    pa, pb = hits_a / n_a, hits_b / n_b
    p = (hits_a + hits_b) / (n_a + n_b)
    se = math.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    if se == 0:
        return None
    return (pa - pb) / se


# ---- self-test ----------------------------------------------------------------------
def self_test(panel):
    strikes = [{"strike": 740.0, "open_interest": 100.0},
               {"strike": 745.0, "open_interest": 400.0},
               {"strike": 750.0, "open_interest": 900.0},
               {"strike": 755.0, "open_interest": 300.0},
               {"strike": 760.0, "open_interest": 200.0}]
    if pin_from_strikes(strikes) != 750.0:
        raise RuntimeError("the pin reading picked the wrong strike")
    if pin_from_strikes([]) is not None:
        raise RuntimeError("an empty strike list produced a pin")
    if abs(proximity(751.5, 750.0) - 0.002) > 1e-12:
        raise RuntimeError("the proximity reading is wrong")
    if arm_for(0.002, 1, True) != "arm_a" \
            or arm_for(0.002, -1, False) != "arm_b" \
            or arm_for(0.002, 1, False) is not None \
            or arm_for(0.01, -1, True) is not None:
        raise RuntimeError("the arm assignment is wrong on known cases")
    if not in_band(751.0, 750.0) or in_band(760.0, 750.0):
        raise RuntimeError("the in-band test is wrong on known closes")
    weak = [{"strike": 740.0, "open_interest": 900.0},
            {"strike": 745.0, "open_interest": 800.0},
            {"strike": 750.0, "open_interest": 150.0},
            {"strike": 755.0, "open_interest": 700.0},
            {"strike": 760.0, "open_interest": 600.0}]
    score, readable, parts = failure_score(
        750.0, weak, 762.0, ["Jobs report"], -1)
    if score != 4 or readable != 4:
        raise RuntimeError(f"the failure score gave {(score, readable, parts)}"
                           " on a case built to score 4 of 4")
    score2, readable2, _ = failure_score(
        750.0, strikes, 750.5, [], 1)
    if score2 != 0 or readable2 != 4:
        raise RuntimeError("the failure score gave a nonzero score on a "
                           "case built to score 0")
    score3, readable3, _ = failure_score(None, [], None, [], None)
    if score3 != 0 or readable3 != 1:
        raise RuntimeError("with no pin, only the calendar part of the "
                           "failure score may be readable")
    bh = bottom_half([0.01, 0.02, 0.03, 0.04], 0.02)
    if not bh or bh[0] is not True or abs(bh[1] - 0.025) > 1e-12:
        raise RuntimeError("the bottom-half test is wrong on known values")
    comp = companion_forecasts(750.0, 751.5, 0.52, 0.60)
    if not (0.0 < comp["p_breach"] < 1.0) \
            or abs(comp["predicted_distance_pct"]
                   - round(0.60 * math.sqrt(2 / math.pi), 4)) > 1e-9:
        raise RuntimeError("the companion figures are wrong on known inputs")
    z = two_share_z(16, 40, 4, 20)
    if z is None or abs(z - 1.5492) > 0.01:
        raise RuntimeError(f"the two-share comparison gave {z}")
    # Recording and grading round trip on a throwaway copy.
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        scratch = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                    registry=reg)
        scratch.append_genesis("pin-or-escape self-test")
        lineage = {"source_artifacts": [
                       {"path": "synthetic (self-test, not a record)",
                        "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
                   "clocks": {c: "2026-10-30"
                              for c in ledger_mod.CLOCK_FIELDS},
                   "note": "Self-test only; never the live record."}
        made = 0
        for kind, value, outcome in (
                ("arm_a", {"arm": "arm_a", "claim_pct": ARM_A_CLAIM_PCT,
                           "claim_direction": "at_least",
                           "pin": 750.0, "failure_score": 1,
                           "failure_parts_readable": 4},
                 {"kind": "pin_in_band", "symbol": "SPY",
                  "at_date": "2026-10-30", "pin": 750.0}),
                ("baseline", {"arm": "baseline", "pin": 750.0,
                              "failure_score": 1,
                              "failure_parts_readable": 4},
                 {"kind": "pin_in_band", "symbol": "SPY",
                  "at_date": "2026-10-30", "pin": 750.0}),
                ("breach_chance", {"p": 0.42},
                 {"kind": "pin_breach_half_em", "symbol": "SPY",
                  "at_date": "2026-10-30", "pin": 750.0,
                  "em_pct": 0.52}),
                ("distance", {"estimate": 0.48},
                 {"kind": "pin_abs_distance_pct", "symbol": "SPY",
                  "at_date": "2026-10-30", "pin": 750.0})):
            _row, created = scratch.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts="2026-10-30",
                subject=f"2026-10-30 SPY pin morning: {kind}",
                quantity="pin_or_escape_" + kind, value=value,
                horizon_open="2026-10-30", horizon_close="2026-10-30",
                lineage=lineage,
                families=["modelled_inventory",
                          "distributional_volatility", "events_calendar"],
                outcome=outcome)
            made += 1 if created else 0
        figs = ledger_mod.recompute_figures(scratch.rows())
        if not scratch.verify_chain() or made != 4 \
                or figs[ENGINE_ID]["forecasts"] != 4:
            raise RuntimeError("throwaway morning recording failed")
    return {"state": "passed", "feature_cases_checked": 9,
            "ledger_rows_checked": 4}


# ---- live recording -------------------------------------------------------------------
def ledger_morning(led, expiry, fund, pin, open_price, net_sign,
                   vrp_bottom, score, readable, parts, em_pct,
                   daily_vol_pct, lineage_files):
    """Record one fund's expiry morning. SPY also gets its arm and
    baseline rows. Returns the number of new rows."""
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": ledger_mod.file_sha256(p)}
            for p in lineage_files],
        "clocks": {c: expiry for c in ledger_mod.CLOCK_FIELDS},
        "morning": {"expiry": expiry, "fund": fund, "pin": pin,
                    "open": open_price,
                    "note": ("Recorded on the morning of the expiry "
                             "day, from the opening price, before "
                             "the close it predicts.")}}
    comp = companion_forecasts(pin, open_price, em_pct, daily_vol_pct)
    created = 0
    rows = (
        ("breach_chance", {"p": comp["p_breach"]},
         {"kind": "pin_breach_half_em", "symbol": fund,
          "at_date": expiry, "pin": pin, "em_pct": em_pct}),
        ("distance", {"estimate": comp["predicted_distance_pct"]},
         {"kind": "pin_abs_distance_pct", "symbol": fund,
          "at_date": expiry, "pin": pin}),
    )
    if fund == "SPY":
        arm = arm_for(proximity(open_price, pin), net_sign, vrp_bottom)
        base_value = {"pin": pin, "failure_score": score,
                      "failure_parts_readable": readable,
                      "failure_parts": parts}
        extra = []
        if arm:
            extra.append((arm, dict(
                base_value, arm=arm,
                claim_pct=(ARM_A_CLAIM_PCT if arm == "arm_a"
                           else ARM_B_CLAIM_PCT),
                claim_direction=("at_least" if arm == "arm_a"
                                 else "at_most")),
                {"kind": "pin_in_band", "symbol": "SPY",
                 "at_date": expiry, "pin": pin}))
        extra.append(("baseline", dict(base_value, arm="baseline"),
                      {"kind": "pin_in_band", "symbol": "SPY",
                       "at_date": expiry, "pin": pin}))
        rows = tuple(extra) + rows
    for kind, value, outcome in rows:
        _row, was = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=expiry,
            subject=f"{expiry} {fund} pin morning: {kind}",
            quantity="pin_or_escape_" + kind, value=value,
            horizon_open=expiry, horizon_close=expiry,
            lineage=lineage,
            families=["modelled_inventory", "distributional_volatility",
                      "events_calendar"],
            outcome=outcome)
        created += 1 if was else 0
    return created


def ledger_passed_expiry(led, expiry, fund, issued_ts, lineage_files):
    """Record one passed expiry as a scored zero (DEEP-PASS 3.1
    item 7, the FE26 convention): an expiry that had a pin on record
    but whose morning was never recorded ledgers a taken row with
    score zero and the event_passed driver, instead of silence, so
    the coverage audit can distinguish event over from engine
    broken. The row is issued on the day it is recorded (issued_ts),
    never backdated to the expiry. Returns the number of new rows."""
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": ledger_mod.file_sha256(p)}
            for p in lineage_files],
        "clocks": {c: issued_ts for c in ledger_mod.CLOCK_FIELDS},
        "morning": {"expiry": expiry, "fund": fund,
                    "note": ("This expiry had a pin on record but "
                             "no forecast morning was recorded for "
                             "it; ledgered as a scored zero under "
                             "the passed event convention.")}}
    _row, was = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=issued_ts,
        subject=f"{expiry} {fund} pin morning: event_passed",
        quantity="pin_or_escape_event_passed",
        value={"estimate": 0.0, "event_passed": 1.0,
               "time_weight": 0.0},
        horizon_open=expiry, horizon_close=expiry,
        lineage=lineage,
        families=["modelled_inventory", "distributional_volatility",
                  "events_calendar"],
        outcome={"kind": "pin_event_passed", "symbol": fund,
                 "at_date": expiry},
        scored_zero={"drivers": {"event_passed": 1.0,
                                 "time_weight": 0.0}})
    return 1 if was else 0


# ---- build ------------------------------------------------------------------------------
def build():
    for path, label in ((PANEL_PATH, "price history"),
                        (MAP_PATH, "map card"),
                        (PINWATCH_PATH, "pin watch record"),
                        (WEEKAHEAD_PATH, "week ahead record"),
                        (VIX_PATH, "fear gauge file")):
        if not os.path.exists(path):
            return fail(f"{label} not found: {path}")
    with open(PANEL_PATH, encoding="utf-8") as fh:
        panel_raw = json.load(fh)
    panel = {sym: sorted(rows, key=lambda r: r[0])
             for sym, rows in panel_raw.items()}
    for fund in FUNDS:
        if fund not in panel:
            return fail(f"the price history carries no {fund}")
    with open(MAP_PATH, encoding="utf-8") as fh:
        map_doc = json.load(fh)
    with open(PINWATCH_PATH, encoding="utf-8") as fh:
        pinwatch = json.load(fh)
    with open(WEEKAHEAD_PATH, encoding="utf-8") as fh:
        weekahead = json.load(fh)
    vix = {}
    if _intake is None:
        return fail("the guarded CSV intake (site/intake.py) is "
                    "unavailable; refusing to read the fear gauge "
                    "file unguarded")
    try:
        with open(VIX_PATH, encoding="utf-8") as fh:
            vix_rows = _intake.read_csv_dicts_guarded(fh.read())
    except _intake.IntakeError as exc:
        return fail(f"the fear gauge file was refused at intake: {exc}")
    for row in vix_rows:
        try:
            vix[row["date"]] = float(row["close"])
        except (KeyError, ValueError):
            continue
    if not vix:
        return fail("the fear gauge file carries no readable closes")

    cards = {c["underlying"]: c for c in map_doc.get("cards") or []}
    for fund in FUNDS:
        if fund not in cards:
            return fail(f"the map card carries no {fund} card")
    map_session = max(cards[f]["dix_date"] for f in FUNDS) \
        if all(cards[f].get("dix_date") for f in FUNDS) else None
    # The card's own session: the newest by_expiry keys and the build
    # stamp are the card's; its data session is read from the funds'
    # dark readings, which the card dates itself.
    spy_panel = panel["SPY"]
    panel_dates = [r[0] for r in spy_panel]
    panel_as_of = panel_dates[-1]

    # ---- Chain archive and the pin: read exactly as stored ----
    snapshots, snapshot_files = load_snapshots()
    pins_on_record = pinwatch.get("pins_on_record")
    if pins_on_record is None:
        return fail("the pin watch record does not state its pin count")
    if snapshot_files == 0 and pins_on_record != 0:
        return fail("the pin watch record claims pins while the chain "
                    "archive is empty; refusing to publish from records "
                    "that disagree")
    pins = {}
    for fund in FUNDS:
        for expiry, strikes in (snapshots.get(fund) or {}).items():
            p = pin_from_strikes(strikes)
            if p is not None:
                pins.setdefault(fund, {})[expiry] = p

    # ---- Variance premium, measured over its real span ----
    series = vrp_series(spy_panel, vix)
    if not series:
        return fail("the variance premium could not be computed over "
                    "any session; refusing to publish without it")
    latest_session, latest_vrp = series[-1]
    bh = bottom_half([v for _d, v in series[:-1]], latest_vrp)
    vrp = {"sessions_computed": len(series),
           "from": series[0][0], "to": latest_session,
           "latest": round(latest_vrp, 4),
           "middle_before_latest": round(bh[1], 4) if bh else None,
           "latest_in_bottom_half": (bh[0] if bh else None),
           "gauge_from": min(vix), "gauge_to": max(vix),
           "gauge_rows": len(vix),
           "spy_history_from": panel_dates[0],
           "spy_history_to": panel_as_of,
           "spy_sessions": len(panel_dates)}

    # ---- Expected moves per fund (Engine 1's recipe) ----
    ems = {}
    for fund in FUNDS:
        rows = panel[fund]
        i = len(rows) - 1
        ems[fund] = {"em_pct": round(expected_move_pct(rows, i), 4),
                     "daily_pct": round(100.0 * har_vol(rows, i)
                                        / math.sqrt(252.0), 4),
                     "as_of": rows[-1][0]}

    # ---- Calendar ----
    events = weekahead.get("events") or []
    events_by_date = {}
    for e in events:
        events_by_date.setdefault(e["date"], []).append(e)

    # ---- The next weekly expiry on the cards' own tables ----
    expiries = sorted({k for f in FUNDS
                       for k in (cards[f].get("by_expiry") or {})})
    upcoming = [e for e in expiries if e >= SHIP_DATE]
    next_expiry = upcoming[0] if upcoming else None
    next_expiry_events = events_by_date.get(next_expiry, []) \
        if next_expiry else []

    # ---- Today's failure score: 1 of 4 parts readable ----
    score_today, readable_today, parts_today = failure_score(
        None, [], None,
        [e["name"] for e in next_expiry_events] if next_expiry else [],
        None)

    # ---- Self-test ----
    try:
        test = self_test(panel)
    except Exception as exc:
        return fail(f"self-test failed, refusing to publish: {exc}")

    # ---- Ledger (API only) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")

    # ---- Live: record only a genuine expiry morning formed today ----
    created = 0
    today = None
    # A morning is recordable only when the panel carries today's
    # session open for the fund, a snapshot pin exists for today's
    # expiry, and today is on or after the ship date. Timestamps in
    # the data come from the sources: the freshest panel session is
    # the newest day any source can speak about.
    candidate_day = panel_as_of
    if candidate_day >= SHIP_DATE:
        for fund in FUNDS:
            fund_pins = pins.get(fund) or {}
            if candidate_day not in fund_pins:
                continue
            rows = panel[fund]
            bar = next((r for r in rows if r[0] == candidate_day), None)
            if bar is None:
                continue
            pin = fund_pins[candidate_day]
            open_price = float(bar[1])
            if proximity(open_price, pin) > PROXIMITY:
                continue
            net_sign = 0
            if fund == "SPY":
                net = cards["SPY"]["net_gex_usd_per_1pct"]
                net_sign = 1 if net > 0 else (-1 if net < 0 else 0)
            strikes = (snapshots.get(fund) or {}).get(candidate_day) or []
            pin_sign = None
            for s in strikes:
                if s["strike"] == pin and "gamma_sign" in s:
                    pin_sign = s["gamma_sign"]
            if pin_sign is None:
                for s in cards[fund].get("top_strikes_by_abs_gex") or []:
                    if s["strike"] == pin:
                        pin_sign = 1 if s["gex"] > 0 else (
                            -1 if s["gex"] < 0 else 0)
            sc, rd, pt = failure_score(
                pin, strikes, open_price,
                [e["name"] for e in events_by_date.get(candidate_day, [])],
                pin_sign)
            created += ledger_morning(
                led, candidate_day, fund, pin, open_price, net_sign,
                vrp["latest_in_bottom_half"], sc, rd, pt,
                ems[fund]["em_pct"], ems[fund]["daily_pct"],
                [PANEL_PATH, MAP_PATH, WEEKAHEAD_PATH, VIX_PATH])
            today = candidate_day

    # ---- Passed expiries: scored zeros, not silence (3.1 item 7) ----
    # An expiry on or after the ship date that already had a pin on
    # record, is now in the past, and has no forecast row of any kind
    # for its fund ledgers one scored zero row, issued today.
    if candidate_day >= SHIP_DATE:
        recorded_keys = {
            (r.get("horizon_close"), (r.get("outcome") or {}).get("symbol"))
            for r in led.rows()
            if r.get("type") == "forecast"
            and r.get("engine_id") == ENGINE_ID}
        for fund in FUNDS:
            for expiry in sorted((pins.get(fund) or {})):
                if SHIP_DATE <= expiry < candidate_day \
                        and (expiry, fund) not in recorded_keys:
                    created += ledger_passed_expiry(
                        led, expiry, fund, candidate_day,
                        [PANEL_PATH, MAP_PATH, PINWATCH_PATH])
                    recorded_keys.add((expiry, fund))

    # ---- Grade any recorded morning whose close is now on record ----
    rows = led.rows()
    graded_now = 0
    pin_prices = [None]
    for row in list(rows):
        if row.get("type") != "forecast" or row.get("engine_id") != ENGINE_ID:
            continue
        if any(g.get("type") == "grade"
               and g.get("forecast_row_id") == row["row_id"] for g in rows):
            continue
        outcome = row.get("outcome") or {}
        fund = outcome.get("symbol")
        day = outcome.get("at_date")
        pin = outcome.get("pin")
        if not fund or not day or pin is None:
            continue
        bar = next((r for r in panel.get(fund, []) if r[0] == day), None)
        if bar is None:
            continue
        # Shared grading path (RC-19 cure, 2026-10-30): this
        # engine no longer grades itself in a divergent schema.
        # The shared grade_forecast resolves the pin kinds from
        # the price source, scores them under the registered
        # rule, and stamps the shared grade fields plus the arm
        # and in_band fields the page below reads.
        if pin_prices[0] is None:
            pin_prices[0] = grading_mod.PriceSource(PANEL_PATH)
        try:
            grading_mod.grade_forecast(led, row, pin_prices[0],
                                       reg)
        except grading_mod.GradingError:
            continue
        graded_now += 1
        rows = led.rows()

    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})

    # ---- Live figures from the ledger alone ----
    def arm_stats(arm):
        rec = grd = hits = 0
        for r in rows:
            if r.get("type") == "forecast" \
                    and r.get("engine_id") == ENGINE_ID \
                    and (r.get("value") or {}).get("arm") == arm:
                rec += 1
        for r in rows:
            if r.get("type") == "grade" \
                    and r.get("engine_id") == ENGINE_ID \
                    and (r.get("grade") or {}).get("arm") == arm:
                grd += 1
                hits += 1 if r["grade"].get("in_band") else 0
        return {"recorded": rec, "graded": grd, "hits": hits,
                "rate_pct": (round(100.0 * hits / grd, 1)
                             if grd >= THIN else None),
                "thin": grd < THIN}
    arm_a, arm_b, baseline = (arm_stats("arm_a"), arm_stats("arm_b"),
                              arm_stats("baseline"))
    weeks = sorted({r["horizon_close"] for r in rows
                    if r.get("type") == "forecast"
                    and r.get("engine_id") == ENGINE_ID})
    z = two_share_z(arm_a["hits"], arm_a["graded"],
                    arm_b["hits"], arm_b["graded"]) \
        if arm_a["graded"] and arm_b["graded"] else None
    retired = bool(len(weeks) >= PROVING_WEEKS and z is not None
                   and abs(z) < 2.0)

    fund_cards = []
    for fund in FUNDS:
        c = cards[fund]
        net = c["net_gex_usd_per_1pct"]
        fund_cards.append({
            "fund": fund, "price": c["spot"],
            "net_pull_usd_per_1pct": round(net),
            "net_pull_billions": round(net / 1e9, 2),
            "net_pull_sign": ("positive" if net > 0 else
                              "negative" if net < 0 else "zero"),
            "call_wall": c["call_wall"], "put_wall": c["put_wall"],
            "flip": round(c["zero_gamma"], 2),
            "next_expiry_pull_usd": (
                round((c.get("by_expiry") or {}).get(next_expiry))
                if next_expiry and (c.get("by_expiry") or {}).get(
                    next_expiry) is not None else None)})

    data = {
        "tool": "Pin-or-Escape",
        "state": "proving",
        "retired": retired,
        "as_of": panel_as_of,
        "map_built": map_doc.get("built_utc"),
        "map_session": map_session,
        "source": ("The pin watch record checked "
                   f"{pinwatch.get('checked')}, the morning map card "
                   f"built {map_doc.get('built_utc')} (its readings "
                   f"are for the session of {map_session}), the week "
                   "ahead record assembled "
                   f"{weekahead.get('assembled_on')} (coverage "
                   f"{weekahead.get('coverage_start')} to "
                   f"{weekahead.get('coverage_end')}), the shipped "
                   f"daily price history ({panel_dates[0]} to "
                   f"{panel_as_of}) and the long daily fear-gauge "
                   f"file ({vrp['gauge_from']} to {vrp['gauge_to']})."),
        "idea": ("On the day a week's options run out, the price of "
                 "the big S&P 500 fund often ends the day very close "
                 "to one strike price, the level where the most "
                 "contracts are still open. That level is called the "
                 "pin. Most pin products simply publish the level, as "
                 "if naming it were the forecast. It is not. Whether "
                 "the pin holds depends on the position of the "
                 "dealers on the other side of those contracts: when "
                 "their book makes them buy as price falls and sell "
                 "as it rises, price gets pulled back toward the pin; "
                 "when their book works the other way, moves get "
                 "pushed away from it. This page forecasts whether "
                 "the pin holds, given the dealer's book, and grades "
                 "both answers in public."),
        "claim": {
            "words": ("Into a weekly expiry, when the fund opens "
                      "within 0.3 percent of the pin and the dealers' "
                      "net position is positive and the premium for "
                      "protection is in its cheaper half: the fund "
                      "closes within plus or minus 0.25 percent of "
                      "the pin in at least 40 percent of weeks. In "
                      "the same closeness to the pin with the "
                      "dealers' net position negative: it closes "
                      "inside that band in at most 20 percent of "
                      "weeks."),
            "arm_a_claim_pct": ARM_A_CLAIM_PCT,
            "arm_b_claim_pct": ARM_B_CLAIM_PCT,
            "proximity_pct": 0.3, "band_pct": 0.25},
        "companions": {
            "words": ("On the same mornings, for each of the three "
                      "index funds, two more forecasts are written "
                      "down: the chance the close lands more than "
                      "half an expected move away from the pin, and "
                      "the predicted distance from the close to the "
                      "pin, in percent. An expected move is the "
                      "typical one-day move the first forecast "
                      "engine on this site works out for each fund."),
            "expected_moves": ems},
        "failure_score": {
            "words": ("One warning score, fixed in advance and "
                      "never adjusted week by week: one point each "
                      "when the dealers' position at the pin strike "
                      "itself is negative, when a big scheduled "
                      "event falls inside the expiry day, when the "
                      "day opens with a gap beyond the pin strike's "
                      "own neighbourhood (one strike step either "
                      "side of it), and when the pin strike holds "
                      "fewer open contracts than the middle of its "
                      "nearest neighbours, which makes it a weak "
                      "pin. The higher the score, the more ways the "
                      "pin has to fail that week."),
            "score_today": score_today,
            "parts_readable_today": readable_today,
            "parts": parts_today,
            "parts_words": {
                "negative_pull_at_pin": ("dealers' position at the "
                                         "pin strike is negative"),
                "event_in_session": ("a big scheduled event falls "
                                     "inside the expiry day"),
                "gap_beyond_neighbourhood": ("the day opens beyond "
                                             "the pin strike's "
                                             "neighbourhood"),
                "weak_pin": ("the pin strike holds fewer open "
                             "contracts than its neighbours' middle")}},
        "pin_state": {
            "pins_on_record": pins_on_record,
            "chain_snapshots_on_record": snapshot_files,
            "state": pinwatch.get("state"),
            "words": (
                f"Pins are on record: {pins_on_record} pin(s) "
                f"from {snapshot_files} kept chain snapshot(s) "
                "carrying the dated count of contracts still "
                "open at each strike. A pin is read from that "
                "kept count only: no wall, no strongest strike "
                "and no flip level is ever shown or used as a "
                "pin."
                if pins_on_record else
                "There is no pin on record today, for any "
                "fund or any expiry. A pin is made from a "
                "count of contracts still open at each strike, "
                "and no record kept here carries that count: "
                "the kept chain archive holds 0 snapshots. "
                "The daily map read does fetch that count "
                "live every day, but it keeps only totals, "
                "the two walls, the flip level and the eight "
                "strongest strikes, and throws the full "
                "strike-by-strike count away. So nothing is "
                "substituted: no wall, no strongest strike and "
                "no flip level is ever shown or used as a "
                "pin.")},
        "readings": {
            "funds": fund_cards,
            "next_expiry": next_expiry,
            "next_expiry_events": next_expiry_events,
            "variance_premium": vrp,
            "variance_words": ("The premium for protection is "
                               "worked out here because no such "
                               "series is kept anywhere: for each "
                               "trading day, the fear gauge's "
                               "implied swing for the month ahead "
                               "minus the swing the fund actually "
                               "made over the prior 21 trading days. "
                               "It is computable only where the "
                               "fund's shipped history (399 trading "
                               "days, from March 25, 2025) meets the "
                               "gauge file, and only through the "
                               "gauge file's last day, October 1, "
                               "2026: that overlap, not any longer "
                               "span, is what is printed.")},
        "arms_today": {
            "state": ("cannot form: there is no pin to be close "
                      "to, so no morning can be tested, in either "
                      "arm" if not pins else "formed from the "
                      "recorded morning"),
            "recorded_today": created,
            "morning": today},
        "live": {
            "weeks_counted": len(weeks), "weeks": weeks,
            "proving_target_weeks": PROVING_WEEKS,
            "records_written": mine["forecasts"],
            "records_graded": mine["graded"],
            "arm_a": arm_a, "arm_b": arm_b, "baseline": baseline,
            "arms_gap_z": (round(z, 3) if z is not None else None),
            "wait": (
                f"The first expiry morning is on record: "
                f"{mine['forecasts']} companion forecast(s) "
                f"written and {mine['graded']} graded. The two "
                "arms themselves fill only on weekly expiry "
                "mornings when a fund opens near its pin, so "
                "their counts can still read zero while the "
                "companions grade. "
                if mine["forecasts"] else
                "No expiry morning has been recorded yet, "
                "and none can be until the first kept chain "
                "snapshot carrying the count of contracts "
                "still open at each strike for a named expiry "
                "lands: that single arrival unblocks the pin. ") + (
                     "From then on, each weekly expiry morning the "
                     "fund opens near its pin, this page writes "
                     "down its two arms, its plain near-pin row and "
                     "its two companion forecasts for each of the "
                     "three index funds (about three index "
                     "forecasts a week), before that day's close, "
                     "and grades them at the close against the "
                     "plain near-pin rate. One caution is printed "
                     "in advance: on every map session on record "
                     "the dealers' net position has been negative "
                     "for all three funds, so the positive arm may "
                     "fill slowly, and the 52-week verdict needs "
                     "both arms filled.")},
        "self_test": test,
        "kill_criterion": ("After 52 weeks have been counted, if "
                           "the two arms' rates for closing inside "
                           "the band cannot be told apart, this "
                           "tool retires. Both arms have to be "
                           "filled for that test to run at all."),
        "thin_cell_rule": ("Any arm, and the plain near-pin row, "
                           "with fewer than 30 graded weeks shows "
                           "its count only, with no rate headline. "
                           "The same holds for each fund's "
                           "companion figures."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: pins on record {pins_on_record}, chain "
          f"snapshots {snapshot_files}, next expiry {next_expiry}, "
          f"premium over {vrp['sessions_computed']} sessions "
          f"({vrp['from']} to {vrp['to']}), live records "
          f"{mine['forecasts']} ({created} new), graded "
          f"{mine['graded']} ({graded_now} new), self-test "
          f"{test['state']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
