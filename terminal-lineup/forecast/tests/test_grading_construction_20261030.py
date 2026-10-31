"""Regression blockers for the RC-19 grading construction cure and
the RC-04 Engine 3 session calendar, 2026-10-30.

Fail direction, per item, on the pre-cure tree:
- Engine 15: its quantiles are in percent but the shared resolver
  returned a fraction for kind "return", so the first maturity
  (2026-11-26) would have graded a percent band against a
  fraction, a factor of 100 out. No return_percent resolver and
  no registered convention existed.
- Engines 13 and 16: point estimates in points of excess against
  SPY under kind "return" against an own return fraction
  resolver; no excess resolver existed at all.
- Engine 3: the same two-symbol gap for its chance that the
  excess is positive, plus the live branch fail closing for lack
  of a forward session calendar.
- Engine 30: binary_event rows carry no realised field and the
  shared resolver refused them; only a divergent self grade in
  its refresher could grade them.
- Engine 27: self grades in a divergent schema beside the shared
  pin resolvers, and kind pin_in_band unknown to the resolver.
- The non-price kinds (league_interval, league_ranking,
  recheck_replication, cohort_barrier_race) had no shared
  grading path at all.

Every dry run below grades a row carrying an actually issued
row's value, outcome spec and quantity (copied from the live
ledger where the engine has issued rows) on a scratch ledger,
through the shared grade_forecast, and checks the grade lands
on the registered scale.
"""
import json
import math
import os
import sys
from datetime import date, timedelta

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
sys.path.insert(0, FORECAST)
import grading as G  # noqa: E402
import ledger as ledger_mod  # noqa: E402
import registry as registry_mod  # noqa: E402
import session_calendar as cal  # noqa: E402

REG = registry_mod.load()
LINEAGE = {"source_artifacts": [{"path": "test", "sha256": "0" * 64}],
           "clocks": {c: "2026-10-30" for c in ledger_mod.CLOCK_FIELDS},
           "note": "RC-19 dry run on a scratch ledger."}


class FakePrices:
    path = "fixture-prices"

    def __init__(self, closes):
        # closes: {symbol: [(date, close), ...]}
        self.bars = {}
        self.volumes = {}
        self.calendars = {}
        for sym, series in closes.items():
            self.bars[sym] = {d: (c, c, c, c) for d, c in series}
            self.volumes[sym] = {d: 1000000 for d, _c in series}
            self.calendars[sym] = sorted(self.bars[sym])

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        return self.bars[s][d]

    def close(self, s, d):
        return self.bars[s][d][3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


def scratch(tmp_path):
    led = ledger_mod.Ledger(str(tmp_path / "ledger.jsonl"),
                            registry=REG)
    led.append_genesis("rc19 dry run")
    return led


def issue(led, **kw):
    kw.setdefault("lineage", LINEAGE)
    kw.setdefault("families", ["price"])
    row, made = led.append_forecast_declared(**kw)
    assert made
    return row


def grade_of(led, row):
    grades = [r for r in led.rows() if r.get("type") == "grade"
              and r.get("forecast_row_id") == row["row_id"]]
    assert len(grades) == 1
    return grades[0]["grade"]


# ---- registry conventions -------------------------------------------

def test_conventions_registered_before_first_maturities():
    for eng in ("engine_15", "engine_13", "engine_16", "engine_03",
                "engine_30", "engine_27", "engine_20", "engine_23",
                "engine_29"):
        conv = REG.grading_convention(eng)
        assert conv is not None, eng
        assert conv["effective_date"] == "2026-10-30"
        assert conv["affected_outstanding"]["count"] >= 0
        assert conv["affected_outstanding"]["named_in"] == \
            "forecast/grading_conventions_20261030.json"
    named = json.load(open(os.path.join(
        FORECAST, "grading_conventions_20261030.json")))
    total = sum(v["count"] for v in named["affected"].values())
    assert total >= 10521 + 46 + 4 + 8 + 64 + 1
    e15 = named["affected"]["engine_15|return"]
    assert e15["count"] == 10521 and len(e15["row_ids"]) == 10521


# ---- Engine 15: percent quantiles -----------------------------------

def test_engine15_issued_row_grades_in_percent(tmp_path):
    led = scratch(tmp_path)
    # An actually issued Engine 15 row (symbol A, issued
    # 2026-10-29): quantiles in percent.
    row = issue(led, engine_id="engine_15", issued_ts="2026-10-29",
                subject="A",
                quantity="own_return_21s_percent_distribution",
                value={"quantiles": {"0.1": -6.7742, "0.5": 2.9,
                                     "0.9": 11.5264}},
                horizon_open="2026-10-29",
                horizon_close="2026-11-26",
                outcome={"symbol": "A", "kind": "return",
                         "base_date": "2026-10-28",
                         "at_date": "2026-11-26"})
    prices = FakePrices({"A": [("2026-10-28", 100.0),
                               ("2026-11-26", 105.0)]})
    G.grade_forecast(led, row, prices, REG)
    grade = grade_of(led, row)
    # Realised is 5.0 percent, not the 0.05 fraction: inside the
    # percent band, and the pinball losses are on the percent
    # scale (the 0.5 pinball is |5.0 - 2.9| / 2, not ~0.05 scale).
    assert grade["realised"] == pytest.approx(5.0)
    assert grade["scores"]["coverage_hit"] == 1.0
    assert grade["scores"]["pinball@0.5"] == pytest.approx(1.05)


def test_engine15_new_kind_return_percent():
    prices = FakePrices({"A": [("2026-10-28", 100.0),
                               ("2026-11-26", 93.0)]})
    realised, _ = G.resolve_outcome(
        {"symbol": "A", "kind": "return_percent",
         "base_date": "2026-10-28", "at_date": "2026-11-26"}, prices)
    assert realised == pytest.approx(-7.0)


# ---- Engines 13 and 16: excess points --------------------------------

def _excess_prices():
    return FakePrices({
        "ABR": [("2026-10-23", 100.0), ("2026-11-20", 103.0)],
        "SPY": [("2026-10-23", 100.0), ("2026-11-20", 101.0)]})


def test_engine16_issued_row_grades_in_excess_points(tmp_path):
    led = scratch(tmp_path)
    # An actually issued Engine 16 row (ABR): estimate 1.0 points
    # of excess. Own +3 percent, SPY +1 percent: realised excess
    # is 2.0 points, so the absolute error is 1.0 point. On the
    # pre-cure resolver the realised value was the own fraction
    # 0.03 and the error 0.97 of a point-valued estimate.
    row = issue(led, engine_id="engine_16", issued_ts="2026-10-26",
                subject="ABR",
                quantity="median_20_session_excess_points",
                value={"estimate": 1.0},
                horizon_open="2026-10-26",
                horizon_close="2026-11-20",
                outcome={"symbol": "ABR", "kind": "return",
                         "base_date": "2026-10-23",
                         "at_date": "2026-11-20"})
    G.grade_forecast(led, row, _excess_prices(), REG)
    grade = grade_of(led, row)
    assert grade["realised"] == pytest.approx(2.0)
    assert grade["scores"]["abs_error"] == pytest.approx(1.0)


def test_engine13_style_row_grades_in_excess_points(tmp_path):
    led = scratch(tmp_path)
    # Engine 13's documented issuance shape (persist leg,
    # estimate +0.5 points); it has no live rows yet, so the dry
    # run uses its issuing record's own values.
    row = issue(led, engine_id="engine_13", issued_ts="2026-10-26",
                subject="ABR",
                quantity="persist_median_20_session_excess_points",
                value={"estimate": 0.5},
                horizon_open="2026-10-26",
                horizon_close="2026-11-20",
                outcome={"symbol": "ABR", "kind": "return",
                         "base_date": "2026-10-23",
                         "at_date": "2026-11-20"})
    G.grade_forecast(led, row, _excess_prices(), REG)
    grade = grade_of(led, row)
    assert grade["realised"] == pytest.approx(2.0)
    assert grade["scores"]["abs_error"] == pytest.approx(1.5)


# ---- Engine 3: excess sign plus the session calendar ------------------

def test_engine3_excess_sign_dry_run(tmp_path):
    led = scratch(tmp_path)
    row = issue(led, engine_id="engine_03", issued_ts="2026-10-23",
                subject="ABR",
                quantity="chance the name's next 20 sessions beat "
                         "SPY, with the median excess in points",
                value={"p": 0.6, "estimate": 1.5},
                horizon_open="2026-10-26",
                horizon_close="2026-11-20",
                outcome={"symbol": "ABR", "kind": "excess_sign",
                         "benchmark": "SPY",
                         "base_date": "2026-10-23",
                         "at_date": "2026-11-20"})
    G.grade_forecast(led, row, _excess_prices(), REG)
    grade = grade_of(led, row)
    assert grade["binary_outcome"] == 1.0
    assert grade["scores"]["brier"] == pytest.approx(0.16)


def test_session_calendar_on_record_and_verified():
    days = cal.load_calendar()
    assert days[0] == "2026-01-02" and days[-1] == "2028-12-29"
    # Known NYSE closures are not sessions.
    for closed in ("2026-11-26", "2026-12-25", "2026-07-03",
                   "2027-01-01", "2027-03-26", "2026-01-19"):
        assert closed not in days, closed
    # Known sessions are sessions.
    for open_day in ("2026-10-29", "2026-11-27", "2026-10-30"):
        assert open_day in days, open_day
    fut = cal.next_sessions("2026-10-23", 20)
    assert fut[0] == "2026-10-26" and fut[-1] == "2026-11-20"
    assert len(fut) == 20


def test_engine3_refresher_uses_calendar_not_fail_close():
    src = open(os.path.join(
        FORECAST, "..", "site", "refresh_ownnormdepth.py")).read()
    assert "session_calendar" in src
    assert "next_sessions" in src
    assert "calendar beyond the as-of session is not on" not in src
    assert '"kind": "excess_sign"' in src


# ---- Engine 30: binary_event under its own threshold rule -------------

def _spy_vol_prices():
    days = []
    d = date(2026, 5, 1)
    closes = []
    i = 0
    while d <= date(2026, 11, 26):
        days.append(d.isoformat())
        # Quiet trailing history, then a loud forward window after
        # the issue session, so the bit must come out 1.
        step = 0.002 if d <= date(2026, 10, 28) else 0.03
        closes.append(100.0 * math.exp(step * i))
        i += 1
        d += timedelta(days=1)
    return FakePrices({"SPY": list(zip(days, closes))})


def test_engine30_issued_row_grades_through_shared_path(tmp_path):
    led = scratch(tmp_path)
    # An actually issued Engine 30 row's outcome spec (21 session
    # leg, issued 2026-10-28); the row carries no realised field.
    row = issue(led, engine_id="engine_30", issued_ts="2026-10-28",
                subject="SPY",
                quantity="Chance that SPY's realised volatility "
                         "over the next 21 sessions exceeds its "
                         "trailing-63-session median",
                value={"p": 0.4218, "p_control_vix_only": 0.4218,
                       "base_rate": 0.4218,
                       "book_version": "v1_2026-10-29"},
                horizon_open="2026-10-29",
                horizon_close="2026-11-26",
                outcome={"symbol": "SPY", "kind": "binary_event",
                         "at_date": "2026-11-26",
                         "horizon_sessions": 21,
                         "issue_date": "2026-10-28",
                         "threshold_rule": "median of the 63 "
                         "trailing 21-session realised vols whose "
                         "windows end on or before the issue day, "
                         "recomputed from the price panel at "
                         "grading"})
    G.grade_forecast(led, row, _spy_vol_prices(), REG)
    grade = grade_of(led, row)
    assert grade["binary_outcome"] == 1.0
    assert grade["scores"]["brier"] == pytest.approx(
        (0.4218 - 1.0) ** 2)
    assert grade["scores"]["brier_control"] == pytest.approx(
        (0.4218 - 1.0) ** 2)
    assert grade["threshold_used"] > 0
    assert grade["realised_vol"] > grade["threshold_used"]
    assert grade["book_version"] == "v1_2026-10-29"


def test_binary_event_without_realised_or_rule_still_refused():
    with pytest.raises(G.GradingError):
        G.resolve_outcome({"symbol": "SPY", "kind": "binary_event",
                           "at_date": "2026-11-26"}, _spy_vol_prices())


# ---- Engine 27: shared pin schema -------------------------------------

def test_engine27_breach_row_grades_in_shared_schema(tmp_path):
    led = scratch(tmp_path)
    # The actually issued Engine 27 companion row (IWM
    # 2026-10-29, pin 282.0, em 0.7627); the panel close that day
    # was 284.01, a 0.7128 percent distance, beyond half the
    # expected move, so the breach bit is 1.
    row = issue(led, engine_id="engine_27", issued_ts="2026-10-29",
                subject="2026-10-29 IWM pin morning: breach_chance",
                quantity="pin_or_escape_breach_chance",
                value={"p": 0.6636},
                horizon_open="2026-10-29",
                horizon_close="2026-10-29",
                outcome={"kind": "pin_breach_half_em",
                         "symbol": "IWM", "at_date": "2026-10-29",
                         "pin": 282.0, "em_pct": 0.7627})
    prices = FakePrices({"IWM": [("2026-10-29", 284.01)]})
    G.grade_forecast(led, row, prices, REG)
    grade = grade_of(led, row)
    assert grade["rule_id"] == "brier"
    assert grade["realised"] == pytest.approx(0.7128, abs=1e-4)
    assert grade["binary_outcome"] == 1.0
    assert grade["scores"]["brier"] == pytest.approx(
        (0.6636 - 1.0) ** 2)
    assert grade["price_source"] == "fixture-prices"


def test_engine27_pin_in_band_shared_kind(tmp_path):
    led = scratch(tmp_path)
    row = issue(led, engine_id="engine_27", issued_ts="2026-10-29",
                subject="2026-10-29 SPY pin morning: arm_a",
                quantity="pin_or_escape_arm_a",
                value={"arm": "arm_a", "claim_pct": 55.0,
                       "pin": 750.0},
                horizon_open="2026-10-29",
                horizon_close="2026-10-29",
                outcome={"kind": "pin_in_band", "symbol": "SPY",
                         "at_date": "2026-10-29", "pin": 750.0})
    prices = FakePrices({"SPY": [("2026-10-29", 751.0)]})
    G.grade_forecast(led, row, prices, REG)
    grade = grade_of(led, row)
    assert grade["scores"]["in_band"] == 1.0
    assert grade["in_band"] is True and grade["arm"] == "arm_a"


def test_pin_and_abstention_refreshers_use_shared_grading():
    for name in ("refresh_pinorescape.py",
                 "refresh_abstentionsignal.py"):
        src = open(os.path.join(FORECAST, "..", "site", name)).read()
        assert "grading_mod.grade_forecast" in src, name
    pin_src = open(os.path.join(
        FORECAST, "..", "site", "refresh_pinorescape.py")).read()
    assert '"rule": ("the close landed within' not in pin_src


# ---- Non-price kinds: shared grading path ------------------------------

def test_league_interval_and_ranking_grade_through_shared(tmp_path):
    led = scratch(tmp_path)
    # 60 graded fake entrant forecasts, stated 68 points, 40 hit:
    # realised error is 100*40/60 - 68 = -1.33 points.
    for i in range(60):
        f = issue(led, engine_id="engine_01",
                  issued_ts="2026-11-02", subject=f"T{i}",
                  quantity="band",
                  value={"lower": 0.0, "upper": 1.0,
                         "stated_coverage": 68.0},
                  horizon_open="2026-11-02",
                  horizon_close="2026-11-03",
                  outcome={"kind": "close", "symbol": "SPY",
                           "at_date": "2026-11-03"})
        led.append_grade(
            forecast_row=f, grade={
                "rule_id": "coverage", "realised": 0.5,
                "binary_outcome": None,
                "scores": {"coverage_hit": 1.0 if i < 40 else 0.0}},
            **(ledger_mod.frozen_label_identity(f) or {}))
    # The actually issued league interval row for engine_01.
    row = issue(led, engine_id="engine_20", issued_ts="2026-10-30",
                subject="2026-11:engine_01",
                quantity="signed calibration error over the "
                         "entrant's next 60 graded forecasts, "
                         "in points",
                value={"stated_pct": 68.0, "centre_error_pts": -6.53,
                       "err_low_pts": -19.2, "err_high_pts": 4.7,
                       "rate_low_pct": 48.8, "rate_high_pct": 72.7,
                       "rival_err_low_pts": -19.2,
                       "rival_err_high_pts": 4.7, "n_next": 60},
                horizon_open="2026-11-02",
                horizon_close="2027-11-02",
                outcome={"kind": "league_interval",
                         "entrant": "engine_01", "round": "2026-11"})
    prices = FakePrices({"SPY": [("2027-11-02", 100.0)]})
    G.grade_forecast(led, row, prices, REG, as_of="2027-11-02")
    grade = grade_of(led, row)
    assert grade["realised"] == pytest.approx(-1.33, abs=0.01)
    assert grade["scores"]["interval_hit"] == 1.0
    assert grade["scores"]["coverage_hit"] == 1.0
    # Ranking: the realised order is computed from the round's
    # graded intervals when a record supplies this entrant only;
    # here a record outcome supplies the order directly.
    rank = issue(led, engine_id="engine_20", issued_ts="2026-10-30",
                 subject="2026-11:ranking",
                 quantity="ranking of entrants by predicted "
                          "calibration error size, smallest first",
                 value={"order": ["engine_01", "engine_02"],
                        "family_order": []},
                 horizon_open="2026-11-02",
                 horizon_close="2027-11-02",
                 outcome={"kind": "league_ranking",
                          "round": "2026-11"})
    G.grade_forecast(led, rank, prices, REG, as_of="2027-11-02",
                     record_outcomes={rank["row_id"]: {
                         "realised_order": ["engine_02",
                                            "engine_01"]}})
    rgrade = grade_of(led, rank)
    assert rgrade["realised_ranking"] == ["engine_02", "engine_01"]
    assert rgrade["scores"]["rank_agreement"] == pytest.approx(-1.0)


def test_recheck_and_cohort_grade_from_supplied_records(tmp_path):
    led = scratch(tmp_path)
    prices = FakePrices({"SPY": [("2027-01-27", 100.0)]})
    rec = issue(led, engine_id="engine_23", issued_ts="2026-10-29",
                subject="cell:avoid.deadcat",
                quantity="chance this top-grade combination fails "
                         "the next recheck (anything except "
                         "reaching the top grade again; "
                         "cannot-be-tested counts as failed)",
                value={"cell": "all", "forecaster": "avoid.deadcat",
                       "p": 0.974509, "rank": 1,
                       "target": "up_excess_20"},
                horizon_open="2026-10-29",
                horizon_close="2027-01-27",
                outcome={"grading_event": "next pre-registered "
                         "recheck", "kind": "recheck_replication",
                         "leg": "cell_failure"})
    # Without the recheck record the shared path refuses, naming
    # the record; it never invents a realised value.
    with pytest.raises(G.GradingError):
        G.grade_forecast(led, rec, prices, REG, as_of="2027-01-27")
    G.grade_forecast(led, rec, prices, REG, as_of="2027-01-27",
                     record_outcomes={rec["row_id"]: {"failed": 1}})
    grade = grade_of(led, rec)
    assert grade["binary_outcome"] == 1.0
    assert grade["scores"]["brier"] == pytest.approx(
        (0.974509 - 1.0) ** 2)

    cohort = issue(led, engine_id="engine_29",
                   issued_ts="2026-10-29",
                   subject="gap_day:2026-10-29",
                   quantity="cohort timing density: barrier race "
                            "at 5/10/21/60 sessions plus "
                            "sessions-since hazard panel",
                   value={"resolved_by": {"5": 0.0, "10": 0.009,
                                          "21": 0.0436,
                                          "60": 0.2447}},
                   horizon_open="2026-10-30",
                   horizon_close="2027-01-21",
                   outcome={"kind": "cohort_barrier_race",
                            "event_class": "gap_day",
                            "entry_session": "2026-10-29"})
    G.grade_forecast(led, cohort, prices, REG, as_of="2027-01-21",
                     record_outcomes={cohort["row_id"]: {
                         "sessions_to_resolution": 12.0}})
    cgrade = grade_of(led, cohort)
    assert cgrade["realised"] == 12.0
    assert cgrade["scores"]["brier@10"] == pytest.approx(0.009 ** 2)
    assert cgrade["scores"]["brier@21"] == pytest.approx(
        (0.0436 - 1.0) ** 2)


def test_league_refresher_delegates_and_repeats_frozen_identity():
    src = open(os.path.join(
        FORECAST, "..", "site", "refresh_calibrationleague.py")).read()
    # One realised error computation: the shared machinery's.
    assert "grading_mod.league_entrant_realised_error" in src
    # Every grade append in the refresher repeats the forecast's
    # frozen label identity (the RC-21 rule its self-test broke
    # on before this cure).
    assert src.count("ledger_frozen_identity(row)") >= 3
