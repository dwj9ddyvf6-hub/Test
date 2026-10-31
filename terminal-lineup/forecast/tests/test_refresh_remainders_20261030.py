"""Regression blockers for the 2026-10-30 G17 remainder cures
(cure stream A continuation: G1/G2/G15/G17).

Fail directions, each proven against the pre-cure code:
- refresh_gapdestiny pinned its live set to the build day's issue
  (1,216 entries, index {SPY, IWM} on 2026-10-23), so the first
  session after the G2 panel advance failed closed forever. The
  cure cross-checks the live set by an independent recount of the
  as-of session; source assertions pin the removal of the frozen
  expectation, and a final-data test recounts the 2026-10-29 set
  (1,445 entries, index {QQQ}) from the panel itself.
- refresh_abstentionsignal pinned its census to the Board day
  2026-10-26 / Second Opinion day 2026-10-27 / Intake-Bias
  freshest 2026-10-28; all three records advanced, so it failed
  closed on "board session disagreement". Source assertions pin
  the re-taken census, and a final-data test reads the published
  decision record (6 days through 2026-10-29).
- refresh_inregimeoracle failed closed the moment any population
  cleared the 30 graded call bar, because no per-call live series
  builder existed. The builder now constructs the Board gate
  series from the Record's own calls graded against the panel,
  cross-checked against Horizon Grades' aggregates; the test
  below rebuilds it from the final files (47 calls, 26 rose) and
  computes the registered inputs for the 2026-11-02 issue.
- refresh_calibrationleague asserted Engine 15's zero-record
  state forever; after the DEEP panel landed and Engine 15 began
  issuing, that assertion became the next failure. Source
  assertion pins the re-registration (its binding is now the
  ledger-vs-page count cross-check in main()).
- refresh_selfanalogue's reference forecast takes ~66s per name
  on a 2,973-session history, which is weeks over the DEEP
  panel's qualifying names. The fast path added alongside it
  must reproduce the reference exactly; the equivalence tests
  below pin that on a synthetic history and on the S6 normalise
  function itself.
"""
import importlib.util
import json
import math
import os
import random
import sys

LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
SITE = os.path.join(LINEUP, "site")
PANEL = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")


def _src(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def _load_site_module(name):
    path = os.path.join(SITE, name)
    spec = importlib.util.spec_from_file_location(
        name.replace(".py", "").replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- Gap Destiny: the live set is a recount, not a register ----
def test_gapdestiny_live_set_not_pinned():
    src = _src("refresh_gapdestiny.py")
    assert "expected 1216" not in src
    assert '{"SPY", "IWM"}' not in src
    assert "independent recount" in src
    assert "1,445 qualifying gaps" in src  # measured instance, dated


def test_gapdestiny_live_set_recount_matches_final_panel():
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    # Re-taken 2026-10-31 (terminal audit): the registered claim
    # is the 2026-10-29 set, recounted from that session's own
    # rows in the panel's history, which stays on record as the
    # panel advances. The old form pinned the panel's last
    # session to 2026-10-29, so every legitimate panel advance
    # broke the blocker without any engine being wrong.
    as_of = "2026-10-29"
    assert panel["SPY"][-1][0] >= as_of
    recount = []
    for sym, rows in panel.items():
        for i in range(1, len(rows)):
            if rows[i][0] != as_of:
                continue
            prev_close = float(rows[i - 1][4])
            o = float(rows[i][1])
            if prev_close > 0 and o > 0 \
                    and abs((o - prev_close) / prev_close) >= 0.005:
                recount.append(sym)
            break
    assert len(recount) == 1445
    assert sorted(s for s in recount if s in ("SPY", "QQQ", "IWM")) == ["QQQ"]
    with open(os.path.join(SITE, "gap-destiny", "data.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    # Re-taken again 2026-10-31 (engines-b cure pass): the page
    # assertion now binds the page to the panel's own freshest
    # session, not to the registered set's session. The previous
    # form pinned the published page to 2026-10-29, which is
    # exactly the one-session lag the cure removed; the
    # registered 2026-10-29 recount above stays as the historical
    # claim.
    assert data["as_of_session"] == panel["SPY"][-1][0]
    assert data["live_record"]["gap_sets_recorded"] >= 1445


# ---- Abstention Signal: census re-taken on the advanced records ----
def test_abstention_census_retaken():
    src = _src("refresh_abstentionsignal.py")
    # Re-taken again 2026-10-31 (terminal audit round 1): the
    # Board and Second Opinion publishers advanced to the
    # 2026-10-30 session, which joined the census with the same
    # audited character; the 2026-10-29 census day no longer
    # claims them, because their publishers keep only the
    # freshest day.
    assert 'board.get("session") != "2026-10-30"' in src
    assert 'sop.get("session") != "2026-10-30"' in src
    assert 'ib_today.get("session") != "2026-10-30"' in src
    assert '{"day": "2026-10-30",' in src
    assert '"abstained": ["Intake-Bias Reversal"]' in src
    # The 2026-10-23 census day is proven from the rebuilt
    # expected-move lane's own filing record (filed at the time,
    # not reconstructed), not from the page's rolling session.
    assert '"2026-10-23" not in (_fl.get("filed_sessions")' in src


def test_abstention_published_decision_record():
    with open(os.path.join(SITE, "abstention-signal", "data.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["as_of_session"] == "2026-10-30"
    assert len(data["decision_days"]) == 7
    assert data["today"]["day"] == "2026-10-30"
    # Re-taken 2026-10-31 (terminal audit round 1): the freshest
    # day's census now counts the Board and Second Opinion
    # records that stand for 2026-10-30, so 3 tools were running
    # and 1 stayed silent; the day's first-issue forecast pair
    # stands on the ledger and the re-issue pair is voided and
    # named, so the valid recorded count is still 6.
    assert data["today"]["rate"] == 0.3333
    assert data["live"]["forecasts_recorded"] == 6
    assert data["live"]["forecasts_voided"] == 2
    # The narrative must agree with the block it rides in (it once
    # described the previous census day, fired, 0 of 1, 6 days,
    # while the block carried the new day; cured 2026-10-31 by
    # computing the words from the freshest decision day).
    words = data["today"]["words"]
    assert "Friday, October 30, 2026" in words
    assert "the silence rate is 1 of 3" in words
    assert "Only 7 days carry" in words


# ---- In-Regime Oracle: the Board gate series builder ----
def test_inregimeoracle_board_gate_series_builder():
    mod = _load_site_module("refresh_inregimeoracle.py")
    with open(os.path.join(SITE, "record", "data.json"),
              encoding="utf-8") as fh:
        record = json.load(fh)
    with open(os.path.join(SITE, "horizon-grades", "data.json"),
              encoding="utf-8") as fh:
        horizon = json.load(fh)
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    series, dates = mod.board_gate_series(record, horizon, panel)
    # Re-taken 2026-10-31 (engines-b cure pass): the gate series
    # is a growing graded record (47 calls and 26 hits at the
    # first registration; 63 and 35 after the 2026-10-31
    # horizon-grades republication added graded calls). The
    # exact pin failed on legitimate accrual, the same rolling
    # source class as SESSION-PIN-FLOORS-20261031, so the counts
    # are floors and the binding assertion is internal
    # consistency: the computed inputs trail the whole series.
    assert len(series) >= 47
    assert sum(c["hit"] for c in series) >= 26
    sessions = mod.sessions_through(dates, "2026-11-02")
    calc = mod.compute_inputs(series, sessions,
                              sessions.index("2026-11-02"))
    assert calc is not None
    assert calc["trailing_calls"] == len(series)
    assert 0.0 < calc["p"] < 1.0
    with open(os.path.join(SITE, "in-regime-oracle", "data.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["census"]["populations_included"] == 1


# ---- Calibration League: Engine 15 re-registered ----
def test_calibration_engine15_reregistered():
    src = _src("refresh_calibrationleague.py")
    assert "no longer in its registered zero-record state" not in src
    assert "Re-registered 2026-10-30 (cure G17)" in src


# ---- Self-Analogue: the fast path equals the reference ----
def test_selfanalogue_normalise_fast_exact():
    sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))
    import studies as s6  # noqa: E402
    mod = _load_site_module("refresh_selfanalogue.py")
    rng = random.Random(20261030)
    series = [rng.gauss(0.0, 1.0) for _ in range(500)]
    series[::41] = [None] * len(series[::41])
    fast = mod._normalise_series_fast(series)
    for i, v in enumerate(series):
        if v is None:
            continue
        ref = s6.normalise(v, [x for x in series[:i] if x is not None])
        assert (ref is None) == (fast[i] is None)
        if ref is not None:
            assert abs(ref - fast[i]) < 1e-12


def test_selfanalogue_forecast_fast_equivalent():
    mod = _load_site_module("refresh_selfanalogue.py")
    rng = random.Random(20261028)
    rows = []
    price = 100.0
    day = 0
    import datetime as _dt
    d = _dt.date(2023, 1, 2)
    while len(rows) < 900:
        if d.weekday() < 5:
            drift = 0.0004 + 0.004 * math.sin(day / 40.0)
            shock = rng.gauss(0.0, 0.011)
            open_ = price * (1.0 + rng.gauss(0.0, 0.002))
            close = price * math.exp(drift + shock)
            high = max(open_, close) * (1.0 + abs(rng.gauss(0.0, 0.004)))
            low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, 0.004)))
            vol = 1_000_000 * (1.0 + 0.3 * math.sin(day / 25.0)
                               + abs(rng.gauss(0.0, 0.1)))
            rows.append([d.isoformat(), round(open_, 4), round(high, 4),
                         round(low, 4), round(close, 4), int(vol)])
            price = close
            day += 1
        d += _dt.timedelta(days=1)
    ref = mod.self_analogue_forecast(rows)
    fast = mod.self_analogue_forecast_fast(rows)
    assert ref is not None and fast is not None
    assert ref["usable_states"] == fast["usable_states"]
    assert ref["matched"] == fast["matched"]
    for k in ("p10", "p50", "p90"):
        assert abs(ref[k] - fast[k]) < 1e-9
