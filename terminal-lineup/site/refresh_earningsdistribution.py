#!/usr/bin/env python3
"""Refresh the Earnings Move Distribution Engine (Engine 12).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - Upcoming calendar (the GOVERNING date source): the Earnings
     Calendar page's record, the union of the two desk earnings
     files (alpaca-swing-desk/desk/earnings.json and
     phase_earnings.json), both stamped 2026-10-12T21:57:32Z and
     checked name by name on the names they share: 77 names, 73
     with a report date (2026-10-13 to 2026-12-17), 4 with no date
     scheduled, a priced-move field that is EMPTY for all 73 dated
     names, and NO report timing (before or after the open)
     anywhere. The calendar is stale by its own page's rule
     (gathered 2026-10-12, more than 8 days before today).
   - Past report dates (the only stored past dates on disk): the
     desk gate-audit store (Nasdaq calendar, scraped 2026-10-02,
     labelled point-in-time reported actuals): 41 names, 321
     events, 2022-02-24 to 2024-12-19. Report dates are used
     EXACTLY as recorded. The known one-session-late date fault
     belonged to a vendor panel that is not on this disk and is
     never used here; it is not inherited.
   - Daily bars for those past reports: the desk's own daily-bar
     cache (45 names, daily bars into 2026-10-01). All 321 past
     events have a computable report-day move and a computable
     5-session move from this cache (asserted; the refresh fails
     closed otherwise).
   - Report days inside the shipped price history: a second
     upcoming-dates list (a Nasdaq sweep gathered 2026-10-12,
     4,474 names with one date each) crossed with the shipped
     daily history (1,833 names, 399 sessions, 2025-03-25 to
     2026-10-23) gives 247 report days inside that history
     (report sessions 2026-10-13 to 2026-10-23; the size leg is
     computable for all 247, the full 5-session leg for 42).
     This second list DISAGREES with the governing calendar on
     some names (for example META, AAPL and CAT carry different
     dates). It is never merged into the calendar and never
     governs anything upcoming; its days that already lie inside
     the price history are used only as past observations in the
     group history below, exactly as the inspect recorded them.
   - Group (size tier) record: the only size record on disk is
     an index-membership list (1,503 tagged names: 503 in the
     largest-company list, 400 mid-sized, 600 smaller). There is
     NO dollar market-size record on disk; tiers here are
     membership tiers, named as such, never dollar sizes. A name
     on none of the lists is its own group ("not on the lists"),
     never reclassified as small.
   - Priced expected moves: ZERO on record, confirmed first-hand
     in this build like the engine before it: the calendar field
     is empty for all 73, the chain archive holds 0 snapshots,
     and the per-name volatility record holds a volatility level
     only, which is never converted into a priced move.
   - The pooled past-earnings summary (35 reports across AAPL,
     MSFT and NVDA, a pooled average and middle only) stores no
     individual dates or moves and is used for nothing here.
   - The long price panel the original study ran on is NOT on
     this disk. Past own history on record is 2022 to 2024 only,
     and the page says so.

2. RECONSTRUCTION CHOICES (every constant fixed before computing)
   - THE FORECAST: for every name on the calendar, at the close
     before its report: the spread, in steps of a tenth, of its
     earnings-day move size (either way) and of its signed move
     over the 5 trading days after the report day, plus the
     chance its earnings-day move beats its priced expected
     move. Season claim: the middle-80-percent range covers 75
     to 85 percent of a season's reports.
   - Denominator: all 77 calendar names stay in the count: the
     73 dated names form the season, and the 4 no-date names are
     carried as no-date rows. Nobody is silently dropped.
   - Earnings session = the first stored session on or after
     the recorded date (the past-earnings study's own mapping,
     used verbatim). Earnings-day move = that session's close
     against the prior session's close. The 5-session move =
     the close 5 stored sessions after the report session
     against the report session's close.
   - The blend, fixed here: a name's own past report moves carry
     half the weight in total and its group's past moves carry
     half, but the own half counts ONLY when the name has at
     least 8 past reports on record; below that the forecast is
     group-only and the name's own count is printed. When the
     own half counts, the name's own events are left out of the
     group half so nothing is counted twice.
   - Thin rule, everywhere: a leg (size or 5-session) is not
     published for a group whose past pool for that leg holds
     fewer than 30 events; that leg is marked as not recorded,
     with the count and the reason. The same 30-event floor
     governs whether a season's coverage share is printed in
     history (below it, counts only).
   - Steps of a tenth (the 10th to 90th steps) are weighted
     shares of the pooled past moves: sort the moves, give each
     its blend weight, and take the move at which the running
     weight first reaches each tenth.
   - The signed 5-session spread is CENTRED ON ZERO DRIFT: its
     steps are shifted by exactly its own middle step, so the
     middle lands on zero. The record holds no drift edge, so
     no drift is forecast; the signed spread is never centred
     anywhere else. The size spread is never shifted.
   - Priced-move scaling: the design scales the spread by the
     priced expected-move ratio for the group. That ratio does
     not exist on record for any group, so the scaling is
     applied NOWHERE and the page says so. The bigger-than-
     priced chance, when a priced move for a name one day
     exists, is the weighted share of that name's blended past
     move sizes larger than the priced move; until then that
     leg is marked not recorded for every name, with the reason.
   - The small-company earnings-gap fade finding (an earlier
     graded study: smaller companies' earnings jumps faded over
     the next week, by 0.41 points in one era and 1.05 points
     in the other) enters ONLY as a tail conditioner for the
     smallest group: for those names, after centring, 1.05
     points (the worse era's recorded figure, fixed here) is
     taken off the three lowest steps of the signed spread.
     No name on this season's calendar is in the smallest
     group, so the conditioner is registered and dormant: it
     fires for no name this season.
   - Seasons in history are the calendar quarters of the report
     session (for example 2024 Q3). History walks every report
     day on record in date order and forecasts each one ONLY
     from report days recorded strictly before it, under the
     exact blend and thin rules above; a report whose group
     pool was still too thin is counted as skipped, never
     graded. History records nothing in the live record.
   - Issue rule: the issue day is the freshest dated source on
     record for today (the morning map card's build day,
     2026-10-28 at this build). Reports dated on or before the
     issue day are missed at issue: their pre-report close had
     already passed when this engine first ran, and they are
     never backfilled; they stay in the season count with that
     reason. The next report date after the issue day is the
     live cohort: its names are recorded at the issue day's
     close. Later reports are shown with the same spread,
     marked as waiting for the close before their own report;
     each will be recorded then, unchanged in method.
   - The 5-session horizon date is counted in weekdays after
     the report date (weekends skipped; no holiday list is on
     record, and that is named here).
   - Grading note: this engine's registered scoring is the
     step-loss rule, whose scorer reads the published steps
     directly, and both live legs carry outcomes the shared
     price source can resolve (the size of the report-day move;
     the 5-session return) once the price history passes their
     dates. No live row can mature yet: the price history ends
     2026-10-23, before every live report date. The bigger-
     than-priced leg has no grade until a priced move exists.
   - Kill criterion, from the design, in plain words: after
     two full seasons, the engine is retired if the middle-80-
     percent range's coverage of a season's reports sits
     outside 70 to 90 percent, or if the score for its bigger-
     than-priced chances is no better than simply quoting the
     priced move's own implied chance.

   - FE17 / FE18 adoption (DEEP-PASS 3.2 item 6, 2026-10-29):
     FE17's blend (site/engine_adaptations.py) is registered
     as this engine's centre and replaces the middle step when
     its inputs exist. Its priced move and timing quality
     inputs landed on 2026-10-30, and its dispersion input is
     the forecast error dispersion on record, adopted as the
     registered input under its own true name by the registry
     amendment of 2026-10-30 (the owner's decision, delegated
     to Midna that day); it is not cross analyst estimate
     dispersion, which no free source carries and which was
     never renamed into this input. The centre is recorded
     per name when its inputs exist; a name missing an input
     stays not_recorded with the input named and the
     historical middle stands, labelled. FE18 is a
     ledgered sub forecast of this engine: it consumes the
     signed drift over the 5 sessions after the report day,
     may only be issued after that window closes, and grades
     over the next 5 sessions; standardized surprise and
     revision breadth have no source on disk, named as the
     open remainder in the page data and the execution ledger.
     The FE04 fair gap residual conditioner (Engine 28) waits
     on a fair gap model neither side has; named open, not
     fabricated.

3. NON-CLAIMS
   - No priced move is invented, and no bigger-than-priced
     chance is shown for any name until a record carries a
     priced move for that name.
   - No drift is claimed for the 5-session leg: it is centred
     on zero because the record holds no drift edge.
   - Membership tiers are not dollar sizes, and a name on no
     list is never called small.
   - The second dates list never governs an upcoming report;
     the governing calendar's dates are used exactly as
     recorded, disagreements named, never merged.
   - History is labelled history and proves nothing about the
     live record; the live record starts with the next cohort.

=====================================================================
Behaviour: recounts the calendar from its two raw files and
fails closed on any disagreement with the published calendar
(shared names, dates, counts, priced fields); recounts the past
store against its own header; asserts every past event computes
from the bar cache; recounts the in-history report days against
the recorded counts; verifies the forecast record's chain before
and after; walks history; computes the live cohort's spreads and
records them through the forecast machinery only, with a
not-recorded row for each leg that cannot be computed; writes
data.json. Every timestamp comes from a source, never the
clock, so reruns are identical.

Usage: python3 refresh_earningsdistribution.py
"""

import bisect
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
MORGUE = os.path.join(WORKSPACE, "morgue")
RAW_CAL_PATHS = [
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk",
                 "earnings.json"),
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk",
                 "phase_earnings.json"),
]
# The calendar producer (refresh_earningscal.py) governs from the
# re-checked record written by fetch_earnings_calendar.py whenever
# it exists, and only falls back to the two raw records above when
# it does not. This consumer must read the same governing record
# the producer published from: reading only the raw records makes
# its stamp check fail on every run after a re-check lands
# (hookup cure, 2026-10-29).
FRESH_CAL_PATH = os.path.join(HERE, "earnings-calendar",
                              "record.json")
CALENDAR_PATH = os.path.join(HERE, "earnings-calendar", "data.json")
# Publication cures 2026-10-30: the earnings record lane
# (earnings_record.py), the per name priced move record
# (priced_moves.py) and the FE04 fair gap record
# (fair_gap_model.py). Each is read when present; absence keeps
# the honest not_recorded states, never a substituted figure.
EARNINGS_RECORD_PATH = os.path.join(
    HERE, "earnings-record", "record.json")
PRICED_MOVES_PATH = os.path.join(
    HERE, "earnings-record", "priced_moves.json")
FAIR_GAP_PATH = os.path.join(
    HERE, "gap-destiny", "fair_gap_record.json")


def _optional_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


_EARNINGS_RECORD = None
_PRICED_MOVES = None
_FAIR_GAP = None


def earnings_record():
    global _EARNINGS_RECORD
    if _EARNINGS_RECORD is None:
        _EARNINGS_RECORD = _optional_json(EARNINGS_RECORD_PATH)
    return _EARNINGS_RECORD


def priced_moves():
    global _PRICED_MOVES
    if _PRICED_MOVES is None:
        _PRICED_MOVES = _optional_json(PRICED_MOVES_PATH)
    return _PRICED_MOVES


def fair_gap_record():
    global _FAIR_GAP
    if _FAIR_GAP is None:
        _FAIR_GAP = _optional_json(FAIR_GAP_PATH)
    return _FAIR_GAP
GATE_PATH = os.path.join(
    WORKSPACE, "alpaca-swing-desk", "desk", "research",
    "gate-audit", "earnings_calendar.json")
CACHE_PATH = os.path.join(
    WORKSPACE, "alpaca-swing-desk", "desk", "hidden_state",
    "ovndrift_daily_cache.json")
SWEEP_PATH = os.path.join(
    WORKSPACE, "goals", "alpaca-swing-trading-desk-paper",
    "hidden_files", "earnings_nasdaq_sweep_2026-10-12.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
GICS_PATH = os.path.join(WORKSPACE, "femto-lean", "config",
                         "gics_sectors.json")
MAP_CARD_PATH = os.path.join(MORGUE, "output", "map_card.json")
CHAINS_DIR = os.path.join(MORGUE, "state", "morgue", "chains")
FORECAST_DIR = os.path.join(WORKSPACE, "terminal-lineup", "forecast")
OUT_PATH = os.path.join(HERE, "earnings-distribution", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

import importlib.util  # noqa: E402


def _load(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_adapt = _load("engine_adaptations_mod12",
               os.path.join(HERE, "engine_adaptations.py"))
_forecast_ledger = _load("forecast_ledger_mod12",
                         os.path.join(FORECAST_DIR, "ledger.py"))
_forecast_registry = _load("forecast_registry_mod12",
                           os.path.join(FORECAST_DIR, "registry.py"))
Ledger = _forecast_ledger.Ledger
file_sha256 = _forecast_ledger.file_sha256
Registry = _forecast_registry.Registry

ENGINE_ID = "engine_12"
OWN_FLOOR = 8
THIN = 30
OWN_WEIGHT = 0.50
A12_SHIFT = 1.05  # points, worse-era recorded next-week fade
STEPS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
# Recorded ground truth from the inspect (fail closed on drift):
EXPECT_GATE_EVENTS = 321
EXPECT_PANEL_EVENTS = 247
EXPECT_PANEL_SIGNED = 42
EXPECT_PANEL_SESSIONS = 399
EXPECT_PANEL_LAST = "2026-10-23"

TIER_LABELS = {
    "sp500": "Largest companies (on the largest-company list)",
    "sp400": "Mid-sized companies (on the mid-sized list)",
    "sp600": "Smaller companies (on the smaller-company list)",
    "untagged": "Not on any of the size lists",
}
TIER_SHORT = {
    "sp500": "largest companies",
    "sp400": "mid-sized companies",
    "sp600": "smaller companies",
    "untagged": "companies not on the size lists",
}

SOURCE_WORDS = ("The scheduled earnings calendar gathered on "
                "October 12, 2026, the stored past report dates "
                "from 2022 to 2024, and the daily price history "
                "on record")


def fail(message):
    print(f"Earnings Distribution refresh: {message}",
          file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def weighted_step(pairs, q):
    """pairs: [(value, weight)]. Smallest value whose running
    weight first reaches share q of the total weight."""
    ordered = sorted(pairs)
    total = sum(w for _v, w in ordered)
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= q * total - 1e-12:
            return value
    return ordered[-1][0]


def blended_steps(own_values, tier_values, own_counts):
    """own_values / tier_values: the focal name's own past moves
    and its group's past moves with the name itself left out.
    Returns (steps dict, blend label) or (None, reason)."""
    if own_counts >= OWN_FLOOR and own_values:
        if not tier_values:
            return None, "group pool empty"
        pairs = ([(v, OWN_WEIGHT / len(own_values))
                  for v in own_values]
                 + [(v, (1.0 - OWN_WEIGHT) / len(tier_values))
                    for v in tier_values])
        label = "own_and_group"
    else:
        all_tier = tier_values + (own_values or [])
        if len(all_tier) < THIN:
            return None, f"only {len(all_tier)} past moves in group"
        pairs = [(v, 1.0 / len(all_tier)) for v in all_tier]
        label = "group_only"
    steps = {q: weighted_step(pairs, q) for q in STEPS}
    return steps, label


def distribution_for(symbol, tier, events, leg):
    """events: the full past-event list to draw from. leg is
    'abs' or 'sgn'. Returns a dict or an abstain dict."""
    own = [e for e in events if e["sym"] == symbol
           and e[leg] is not None]
    tier_ex = [e for e in events if e["tier"] == tier
               and e["sym"] != symbol and e[leg] is not None]
    tier_all = [e for e in events if e["tier"] == tier
                and e[leg] is not None]
    if len(tier_all) < THIN:
        return {"state": "not_recorded",
                "reason": (f"its group holds only "
                           f"{len(tier_all)} past moves for "
                           f"this part; {THIN} are needed"),
                "own_events": len(own),
                "group_events": len(tier_all)}
    if len(own) >= OWN_FLOOR:
        if len(tier_ex) < 1:
            return {"state": "not_recorded",
                    "reason": "no other past moves in its group",
                    "own_events": len(own),
                    "group_events": len(tier_all)}
        steps, label = blended_steps(
            [e[leg] for e in own], [e[leg] for e in tier_ex],
            len(own))
    else:
        if len(tier_all) < THIN:
            return {"state": "not_recorded",
                    "reason": (f"its group holds only "
                               f"{len(tier_all)} past moves for "
                               f"this part; {THIN} are needed"),
                    "own_events": len(own),
                    "group_events": len(tier_all)}
        steps, label = blended_steps(
            [e[leg] for e in own], [e[leg] for e in tier_ex],
            len(own))
    if steps is None:
        return {"state": "not_recorded", "reason": label,
                "own_events": len(own),
                "group_events": len(tier_all)}
    conditioner = False
    if leg == "sgn":
        middle = steps[0.5]
        steps = {q: v - middle for q, v in steps.items()}
        if tier == "sp600":
            for q in (0.1, 0.2, 0.3):
                steps[q] -= A12_SHIFT
            conditioner = True
    return {"state": "recorded" if leg == "abs" else "computed",
            "steps_pct": {str(q): round(v, 4)
                          for q, v in steps.items()},
            "typical_pct": round(steps[0.5], 4),
            "low80_pct": round(steps[0.1], 4),
            "high80_pct": round(steps[0.9], 4),
            "blend": label,
            "own_events": len(own),
            "group_events": len(tier_all),
            "conditioner_applied": conditioner}


FE18_QUANTITY = ("FE18 post earnings drift after controls: "
                 "signed drift score for the 5 sessions after "
                 "the observed drift window")
# FE18 consumes the signed move over the 5 sessions after the
# report day (the signed leg's own window). Its sub forecast
# covers the NEXT 5 sessions and may only be issued once that
# drift window has closed.
FE18_DRIFT_SESSIONS = 5
FE18_HORIZON_SESSIONS = 5


def fe17_for_view(view_abs, priced_move_pct, symbol=None):
    """FE17's blend as this name's centre (DEEP-PASS 3.2 item
    6). Historical input is the distribution's own typical
    (middle) past move. Implied move is the name's priced move
    from the priced move record, and timing quality comes from
    the earnings record lane's report time classes (both landed
    2026-10-30). The dispersion input is the earnings record's
    forecast error dispersion: the standard deviation of the
    name's own prior forecast errors, z scored across reporting
    names. It is not cross analyst estimate dispersion, which
    no free source carries, and it is never named as such; the
    registry amendment of 2026-10-30, made under the owner's
    decision delegated to Midna that day, adopted it as this
    centre's registered dispersion input under its own true
    name, and the lane's earlier refusal to rename it into
    analyst dispersion stands as correct. Where an input is
    still missing the centre stays not_recorded with that
    input named, and the historical middle stands as the
    centre."""
    historical = view_abs.get("typical_pct") \
        if view_abs.get("state") == "recorded" else None
    timing = None
    dispersion_z = None
    if symbol:
        rec = earnings_record().get("names", {}).get(symbol) or {}
        timing = rec.get("timing_quality")
        fed = rec.get("forecast_error_dispersion") or {}
        if fed.get("state") == "recorded":
            dispersion_z = fed.get("cross_section_z")
    return _adapt.fe17_centre(priced_move_pct, historical,
                              dispersion_z, timing)


def fe18_state_for_view(report_date, today_iso):
    """FE18 sub forecast state for an upcoming reporter: its
    drift window has not opened, and two of its four inputs
    have no source on disk at all."""
    if report_date > today_iso:
        return {"state": "awaiting_drift_window",
                "missing": ["standardized_surprise_z",
                            "observed_post_event_drift",
                            "sector_residual_z",
                            "revision_breadth"],
                "detail": ("the report has not happened yet; "
                           "the sub forecast is issued only "
                           "after the 5 session drift window it "
                           "consumes has closed, and is graded "
                           "from there")}
    rec = earnings_record()
    surprise_on = rec.get("names_with_surprise_recorded", 0)
    if surprise_on:
        return {"state": "not_recorded",
                "missing": ["revision_breadth"],
                "detail": ("a standardized earnings surprise "
                           "record now exists on disk (the "
                           "earnings record lane, "
                           f"{surprise_on} names recorded); the "
                           "remaining missing input is revision "
                           "breadth, whose registered cross "
                           "series analogue accrues forward from "
                           "the lane's daily consensus snapshots "
                           "and cannot be backfilled honestly")}
    return {"state": "not_recorded",
            "missing": ["standardized_surprise_z",
                        "revision_breadth"],
            "detail": ("no standardized earnings surprise "
                       "record and no analyst revision breadth "
                       "record exist on disk")}


def _fe17_page_block():
    pm = priced_moves()
    rec = earnings_record()
    n_priced = pm.get("priced_moves_on_record", 0)
    n_timing = rec.get("names_with_timing", 0)
    fed = [(r.get("forecast_error_dispersion") or {})
           for r in rec.get("names", {}).values()]
    fed = [f for f in fed if f.get("state") == "recorded"]
    n_disp = len(fed)
    definition = (fed[0].get("definition") if fed else
                  ("forecast error dispersion: sd of the "
                   "name's own prior forecast errors, z scored "
                   "across reporting names. Not cross analyst "
                   "dispersion."))
    return {
        "state": "inputs_recorded",
        "priced_moves_on_record": n_priced,
        "names_with_timing": n_timing,
        "names_with_dispersion_on_record": n_disp,
        "dispersion_input": "forecast_error_dispersion",
        "dispersion_definition": definition,
        "missing": [],
        "detail": ("FE17's blend (0.60 of the priced implied "
                   "move plus 0.40 of the historical event "
                   "move, adjusted for dispersion and timing "
                   "quality) is registered as this engine's "
                   "centre, and it takes over on each name "
                   "whose inputs exist. All three inputs are "
                   "on record: a per name priced move record "
                   f"({n_priced} upcoming reporters priced "
                   "from stored at the money straddle quotes), "
                   "a report timing record from the earnings "
                   f"record lane ({n_timing} names with a "
                   "timing quality), and a dispersion record "
                   f"({n_disp} names). The dispersion input is "
                   "forecast error dispersion: the standard "
                   "deviation of the name's own prior forecast "
                   "errors, z scored across reporting names, "
                   "carried by the earnings record. It is not "
                   "cross analyst estimate dispersion, which "
                   "no free source carries; the two quantities "
                   "are different and neither is renamed into "
                   "the other. The registered definition "
                   "originally named cross analyst estimate "
                   "dispersion as this input. By the registry "
                   "amendment of 2026-10-30, made under the "
                   "owner's decision delegated to Midna that "
                   "day, the registered dispersion input is "
                   "the forecast error dispersion on record, "
                   "adopted under its own true name. A name "
                   "missing any other input keeps the "
                   "historical middle as its centre, labelled "
                   "as such, with the missing input named.")}


def _fe18_page_block():
    rec = earnings_record()
    n_surprise = rec.get("names_with_surprise_recorded", 0)
    return {
        "state": "awaiting_first_window",
        "surprise_recorded_names": n_surprise,
        "missing": ["revision_breadth"],
        "detail": ("FE18's post earnings drift score (half "
                   "standardized surprise, 0.30 of the observed "
                   "post report drift, 0.20 of the sector "
                   "residual, scaled by revision breadth) is a "
                   "ledgered sub forecast of this engine. It "
                   "consumes already observed drift, so it is "
                   "timestamped only after the 5 session drift "
                   "window it consumes has closed and graded "
                   "over the 5 sessions after that. The "
                   "standardized surprise input landed on "
                   "2026-10-30: the earnings record lane "
                   f"records a SUE figure for {n_surprise} "
                   "names from reported versus consensus EPS "
                   "over their prior forecast errors. The one "
                   "remaining missing input is revision "
                   "breadth: no free source carries individual "
                   "analyst revisions, and the registered "
                   "cross series analogue accrues forward "
                   "from the lane's daily consensus snapshots "
                   "starting 2026-10-30, so the first cohort "
                   "whose drift window closes after a breadth "
                   "reading exists is the first that can "
                   "ledger. Nothing is substituted for it.")}


def _fe04_page_block():
    fg = fair_gap_record()
    if not fg:
        return {
            "state": "open",
            "detail": ("The FE04 fair gap residual "
                       "conditioner for Engine 28 waits on a "
                       "fair gap model record that is not on "
                       "disk yet. No model is fabricated to "
                       "fill it.")}
    counts = fg.get("counts", {})
    return {
        "state": "recorded_market_sector",
        "session": fg.get("session"),
        "counts": counts,
        "news_leg_evidence": fg.get("news_leg_evidence"),
        "detail": ("The FE04 fair gap model now exists "
                   "(fair_gap_model.py) and its record for "
                   f"session {fg.get('session')} decomposes "
                   f"{counts.get('gap_names', 0)} gap names "
                   "into a market leg (rolling overnight "
                   "beta times the index overnight gap) and a "
                   "sector leg (sector median gap, "
                   "orthogonalised, with a labelled "
                   "correlation cluster fallback for names "
                   "with no sector on record), publishing a "
                   "market and sector residual per name in "
                   "gap-destiny/fair_gap_record.json. The "
                   "news leg carries no registered "
                   "coefficient, and the model's own record "
                   "now proves why none can be estimated from "
                   "the records on hand: for this session "
                   f"{counts.get('news_on_record', 0)} of the "
                   f"{counts.get('gap_names', 0)} gap names "
                   "have an overnight article on record, and "
                   "the news store's articles carry no signed "
                   "direction field at all, so the missing "
                   "inputs are a signed per article direction "
                   "record and coverage beyond the tracked "
                   "universe (named in the record's "
                   "news_leg_evidence block). Residuals "
                   "are published as market and sector "
                   "residuals, never as full fair gap "
                   "residuals. Engine 28's raw gap legs "
                   "continue unchanged so the residual leg "
                   "can be graded against them. The FE04 "
                   "failed gap sign flip half already stands "
                   "as Engine 28's separately graded sub "
                   "claim.")}


def _exceedance_page_block(chain_snapshots):
    pm = priced_moves()
    n = pm.get("priced_moves_on_record", 0)
    if not n:
        return {"state": "not_recorded",
                "detail": ("No record carries a priced "
                           "expected move for any name yet, "
                           "so no bigger than priced chance "
                           "can be recorded. A volatility "
                           "level is never turned into a "
                           "priced move here.")}
    return {"state": "recorded",
            "priced_moves_on_record": n,
            "detail": (f"A per name priced move record now "
                       f"exists ({n} upcoming reporters priced "
                       "from stored at the money straddle "
                       "quotes, priced_moves.py). Each priced "
                       "name's bigger than priced chance is "
                       "recorded on its own block as the share "
                       "of its group pool past moves bigger "
                       "than that priced move. Names with no "
                       "priced move on record stay "
                       "not_recorded, named per name.")}


def _exceedance_for(sym, tier, priced_pct, events):
    """Bigger than priced chance from a real priced move: the
    share of the name's group pool past moves (the same pool
    its distribution is built from) bigger than the priced
    move on record. No priced move, no figure."""
    if priced_pct is None:
        return {"state": "not_recorded",
                "reason": ("no priced expected move is on "
                           "record for this name, so no "
                           "bigger-than-priced chance can be "
                           "recorded for it yet")}
    pool = [e["abs"] for e in events
            if e["tier"] == tier and e["abs"] is not None]
    if not pool:
        return {"state": "not_recorded",
                "reason": "no past moves in its group pool"}
    share = sum(1 for v in pool if v > priced_pct) / len(pool)
    return {"state": "recorded", "priced_move_pct": priced_pct,
            "pool_moves": len(pool),
            "share_bigger_than_priced": round(share, 4)}


def ledger_fe18_sub_forecast(ledger, *, symbol, issued_ts,
                             drift_close, horizon_open,
                             horizon_close, inputs, lineage):
    """Ledger one FE18 sub forecast (or its abstention) for a
    name whose drift window has closed. Refuses to issue at or
    before drift_close: the form consumes observed drift, so
    an earlier timestamp would grade it from before its own
    input existed. inputs is the fe18_score input dict."""
    if issued_ts[:10] <= drift_close:
        raise ValueError(
            "FE18 sub forecast must be timestamped after the "
            f"drift window it consumes (drift closed "
            f"{drift_close}, issued {issued_ts[:10]})")
    scored = _adapt.fe18_score(
        inputs.get("standardized_surprise_z"),
        inputs.get("observed_post_event_drift_z"),
        inputs.get("sector_residual_z"),
        inputs.get("revision_breadth"))
    value = {"leg": "fe18_pead", "drift_close": drift_close,
             "inputs": inputs, "score": scored["score"]}
    outcome = {"symbol": symbol, "kind": "return",
               "base_date": drift_close, "at_date": horizon_close}
    if scored["state"] == "recorded":
        return ledger.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=issued_ts,
            subject=symbol, quantity=FE18_QUANTITY, value=value,
            horizon_open=horizon_open,
            horizon_close=horizon_close, lineage=lineage,
            families=["events_calendar", "price"],
            outcome=outcome)
    reasons = [_forecast_ledger.feature_reason(
        "missing", m if m != "observed_post_event_drift"
        else "observed_post_event_drift")
        for m in scored["missing"]]
    value = {**value, "state": "abstain_at_issue",
             "missing": scored["missing"]}
    return ledger.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=issued_ts,
        subject=symbol, quantity=FE18_QUANTITY, value=value,
        horizon_open=horizon_open, horizon_close=horizon_close,
        lineage=lineage, families=["events_calendar", "price"],
        outcome=outcome, absence_state="no_data",
        abstain_reasons=reasons)


def _history_reason(view_leg):
    """Per feature abstention reason code for a distribution leg
    that could not be recorded (DEEP-PASS 3.1 item 6, the fixed
    vocabulary in forecast/ledger.py): the past event history
    feature is either absent entirely (no past moves in the group)
    or present but below the floor the distribution needs."""
    cause = "missing" if not view_leg.get("group_events") \
        else "quality_below_floor"
    return [_forecast_ledger.feature_reason(cause,
                                            "past_event_history")]


def weekdays_after(start_iso, count):
    d = date.fromisoformat(start_iso) + timedelta(days=1)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def season_of(iso):
    y, m = iso[:4], int(iso[5:7])
    return f"{y} Q{(m - 1) // 3 + 1}"


def self_test():
    cases = 0
    passed = 0
    # Equal weights over [1,2,3,4]: the middle step is 2.
    pairs = [(float(v), 1.0) for v in (1, 2, 3, 4)]
    cases += 1
    if weighted_step(pairs, 0.5) == 2.0:
        passed += 1
    cases += 1
    if weighted_step(pairs, 0.1) == 1.0 and \
            weighted_step(pairs, 0.9) == 4.0:
        passed += 1
    # Half-and-half blend: own [10] at half weight, group [0, 0]
    # at a quarter each: sorted weights 0:.25, 0:.25, 10:.5, so
    # the middle step is 0 and the 90th step is 10.
    steps, label = blended_steps([10.0], [0.0, 0.0], 8)
    cases += 1
    if label == "own_and_group" and steps[0.5] == 0.0 and \
            steps[0.9] == 10.0:
        passed += 1
    return {"cases": cases, "passed": passed,
            "ok": passed == cases}


def build():
    for path in (CALENDAR_PATH, GATE_PATH, CACHE_PATH, SWEEP_PATH,
                 PANEL_PATH, GICS_PATH, MAP_CARD_PATH,
                 *RAW_CAL_PATHS):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    calendar = load_json(CALENDAR_PATH)
    gate = load_json(GATE_PATH)
    cache = load_json(CACHE_PATH)
    sweep = load_json(SWEEP_PATH)
    panel = load_json(PANEL_PATH)
    gics = load_json(GICS_PATH)
    map_card = load_json(MAP_CARD_PATH)
    issue_day = map_card["built_utc"][:10]
    issued_ts = map_card["built_utc"]

    # ---- Governing calendar: rebuild the union from its two raw
    # files and fail closed on any disagreement with the page's
    # published record.
    stamps = []
    merged = {}
    shared = 0
    if os.path.exists(FRESH_CAL_PATH):
        doc = load_json(FRESH_CAL_PATH)
        stamps.append(doc.get("updated_ts"))
        entries = doc.get("entries")
        if not isinstance(entries, dict) or not entries:
            return fail("the re-checked calendar record carries "
                        "no name list")
        merged = dict(entries)
        governing_cal_paths = [FRESH_CAL_PATH]
    else:
        governing_cal_paths = list(RAW_CAL_PATHS)
        for path in RAW_CAL_PATHS:
            doc = load_json(path)
            stamps.append(doc.get("updated_ts"))
            for name, value in doc.items():
                if name == "updated_ts":
                    continue
                if name in merged:
                    shared += 1
                    if merged[name] != value:
                        return fail(
                            f"the two calendar records disagree on "
                            f"{name}: {merged[name]!r} vs {value!r}")
                else:
                    merged[name] = value
    if len(set(stamps)) != 1 or stamps[0] != calendar["recorded_at"]:
        return fail("the calendar records' stamps disagree with "
                    "the published calendar")
    if shared != calendar["shared_names_checked"]:
        return fail("the shared-name count disagrees with the "
                    "published calendar")
    raw_dated = {s: d for s, d in merged.items() if d}
    raw_undated = sorted(s for s, d in merged.items() if not d)
    pub = {n["symbol"]: n for n in calendar["names"]}
    if set(pub) != set(raw_dated):
        return fail("the published calendar's names disagree "
                    "with the raw records' dated names")
    for sym, d in raw_dated.items():
        if pub[sym]["date"] != d:
            return fail(f"the published calendar's date for {sym} "
                        "disagrees with the raw record")
        if pub[sym].get("expected_move") is not None:
            # A published move is allowed only when it recounts
            # exactly from the priced move record (the raw source):
            # same name, same report date, same formatted figure.
            entry = priced_moves().get("names", {}).get(sym)
            expect = None
            if isinstance(entry, dict) \
                    and entry.get("report_date") == d \
                    and isinstance(entry.get("priced_move_pct"),
                                   (int, float)) \
                    and not isinstance(entry.get("priced_move_pct"),
                                       bool):
                expect = f"{entry['priced_move_pct']:.1f}%"
            if expect is None or pub[sym]["expected_move"] != expect:
                return fail(f"a priced move appeared for {sym} in "
                            "the published calendar without a raw "
                            "source")
    if len(raw_dated) != calendar["dated_names"] or \
            len(merged) != calendar["names_on_record"] or \
            len(raw_undated) != calendar["names_with_no_date"]:
        return fail("the calendar counts disagree with a recount")
    dated = sorted(
        ({"symbol": s, "date": d} for s, d in raw_dated.items()),
        key=lambda x: (x["date"], x["symbol"]))

    # ---- Groups (membership tiers), recounted
    symbols_map = gics["symbols"]

    def tier_of(sym):
        entry = symbols_map.get(sym)
        return entry["index"] if entry else "untagged"

    tier_counts = {}
    for entry in symbols_map.values():
        tier_counts[entry["index"]] = \
            tier_counts.get(entry["index"], 0) + 1
    if len(symbols_map) != 1503 or tier_counts.get("sp500") != 503:
        return fail("the size-list record disagrees with its "
                    "recorded counts")

    # ---- Past events: the stored past dates x the bar cache
    if gate["n_events"] != EXPECT_GATE_EVENTS:
        return fail("the past-dates store's header disagrees "
                    "with the recorded count")
    gate_events_raw = [(s, d) for s, ds in gate["calendar"].items()
                       for d in ds]
    if len(gate_events_raw) != EXPECT_GATE_EVENTS:
        return fail("the past-dates store recount disagrees "
                    "with its header")

    def event_moves(bars_of, pairs):
        out = []
        for sym, ev in pairs:
            dates, closes = bars_of(sym)
            if not dates:
                continue
            i = bisect.bisect_left(dates, ev)
            if i == 0 or i >= len(dates):
                continue
            sess = dates[i]
            abs_move = abs(closes[sess] / closes[dates[i - 1]]
                           - 1.0) * 100.0
            signed = None
            if i + 5 < len(dates):
                signed = (closes[dates[i + 5]] / closes[sess]
                          - 1.0) * 100.0
            out.append({"sym": sym, "date": ev, "sess": sess,
                        "abs": abs_move, "sgn": signed,
                        "tier": tier_of(sym), "src": "past"})
        return out

    def cache_bars(sym):
        closes = {r["t"][:10]: float(r["c"])
                  for r in cache.get(sym, [])}
        return sorted(closes), closes

    past_events = event_moves(cache_bars, gate_events_raw)
    if len(past_events) != EXPECT_GATE_EVENTS or \
            any(e["sgn"] is None for e in past_events):
        return fail("not every stored past report computes from "
                    "the bar cache, against the recorded ground "
                    "truth")

    # ---- Report days inside the shipped price history
    spy_rows = panel["SPY"]
    # The recorded in-history reconstruction is pinned to the
    # panel shape it was recorded on (EXPECT_PANEL_*), but the
    # panel itself now advances daily (G2 cure), so the shipped
    # history is longer than the recorded shape. Reconstruct from
    # the sessions up to the recorded last session, fail closed
    # if that prefix is not exactly the recorded shape, and let
    # the live leg read the full advanced panel (hookup cure,
    # 2026-10-29).
    spy_recorded = [r for r in spy_rows if r[0] <= EXPECT_PANEL_LAST]
    if len(spy_recorded) != EXPECT_PANEL_SESSIONS or \
            spy_recorded[-1][0] != EXPECT_PANEL_LAST:
        return fail("the shipped price history disagrees with "
                    "its recorded shape")
    panel_last = spy_rows[-1][0]
    panel_closes = {s: {r[0]: float(r[4]) for r in rows
                        if r[0] <= EXPECT_PANEL_LAST}
                    for s, rows in panel.items()}

    def panel_bars(sym):
        closes = panel_closes.get(sym, {})
        return sorted(closes), closes

    sweep_pairs = [(s, d) for s, ds in sweep.items() for d in ds]
    panel_events = event_moves(panel_bars, sweep_pairs)
    for e in panel_events:
        e["src"] = "panel"
    panel_signed = sum(1 for e in panel_events
                       if e["sgn"] is not None)
    if len(panel_events) != EXPECT_PANEL_EVENTS or \
            panel_signed != EXPECT_PANEL_SIGNED:
        return fail("the in-history report-day recount disagrees "
                    "with the recorded counts (a source changed)")

    all_events = sorted(past_events + panel_events,
                        key=lambda x: (x["date"], x["sym"]))

    # ---- Tier pools over everything on record
    tier_pools = {}
    for t in ("sp500", "sp400", "sp600", "untagged"):
        pool = [e for e in all_events if e["tier"] == t]
        tier_pools[t] = {
            "tier": t, "label": TIER_LABELS[t],
            "abs_events": len(pool),
            "signed_events": sum(1 for e in pool
                                 if e["sgn"] is not None)}

    test = self_test()
    if not test["ok"]:
        return fail(f"the step arithmetic failed its own check: "
                    f"{test['passed']} of {test['cases']}")

    # ---- History: walk every report day on record, forecasting
    # each only from days recorded strictly before it.
    seasons = {}
    signed_hist = {"graded": 0, "hits": 0}
    for e in all_events:
        pool = [x for x in all_events if x["date"] < e["date"]]
        own = [x for x in pool if x["sym"] == e["sym"]]
        tier_ex = [x for x in pool if x["tier"] == e["tier"]
                   and x["sym"] != e["sym"]]
        tier_all = [x for x in pool if x["tier"] == e["tier"]]
        rec = seasons.setdefault(
            season_of(e["sess"]),
            {"season": season_of(e["sess"]), "events": 0,
             "graded": 0, "skipped": 0, "hits": 0})
        rec["events"] += 1
        if len(own) >= OWN_FLOOR:
            pairs = ([(x["abs"], OWN_WEIGHT / len(own))
                      for x in own]
                     + [(x["abs"], (1.0 - OWN_WEIGHT)
                         / len(tier_ex)) for x in tier_ex]) \
                if tier_ex else None
        elif len(tier_all) >= THIN:
            pairs = [(x["abs"], 1.0 / len(tier_all))
                     for x in tier_all]
        else:
            pairs = None
        if pairs is None:
            rec["skipped"] += 1
            continue
        lo = weighted_step(pairs, 0.1)
        hi = weighted_step(pairs, 0.9)
        rec["graded"] += 1
        if lo <= e["abs"] <= hi:
            rec["hits"] += 1
        if e["sgn"] is not None:
            own_s = [x for x in own if x["sgn"] is not None]
            tier_ex_s = [x for x in tier_ex
                         if x["sgn"] is not None]
            tier_all_s = [x for x in tier_all
                          if x["sgn"] is not None]
            spairs = None
            if len(own) >= OWN_FLOOR and own_s and tier_ex_s:
                spairs = ([(x["sgn"], OWN_WEIGHT / len(own_s))
                           for x in own_s]
                          + [(x["sgn"], (1.0 - OWN_WEIGHT)
                              / len(tier_ex_s))
                             for x in tier_ex_s])
            elif len(own) < OWN_FLOOR and \
                    len(tier_all_s) >= THIN:
                spairs = [(x["sgn"], 1.0 / len(tier_all_s))
                          for x in tier_all_s]
            if spairs is not None:
                raw = {q: weighted_step(spairs, q) for q in STEPS}
                mid = raw[0.5]
                lo_s, hi_s = raw[0.1] - mid, raw[0.9] - mid
                if e["tier"] == "sp600":
                    lo_s -= A12_SHIFT
                signed_hist["graded"] += 1
                if lo_s <= e["sgn"] <= hi_s:
                    signed_hist["hits"] += 1
    season_rows = []
    for name in sorted(seasons):
        rec = seasons[name]
        cov = None
        if rec["graded"] >= THIN:
            cov = round(rec["hits"] / rec["graded"], 4)
        season_rows.append({**rec, "coverage": cov})
    pooled_graded = sum(r["graded"] for r in season_rows)
    pooled_hits = sum(r["hits"] for r in season_rows)
    pooled = {"events": sum(r["events"] for r in season_rows),
              "graded": pooled_graded,
              "skipped": sum(r["skipped"] for r in season_rows),
              "hits": pooled_hits,
              "coverage": (round(pooled_hits / pooled_graded, 4)
                           if pooled_graded else None)}
    signed_pooled = {
        "graded": signed_hist["graded"], "hits": signed_hist["hits"],
        "coverage": (round(signed_hist["hits"]
                           / signed_hist["graded"], 4)
                     if signed_hist["graded"] else None)}

    # ---- Season split of the calendar against the issue day
    missed = [n for n in dated if n["date"] <= issue_day]
    future = [n for n in dated if n["date"] > issue_day]
    if not future:
        return fail("no upcoming report date after the issue day")
    next_date = future[0]["date"]
    next_cohort = [n for n in future if n["date"] == next_date]
    rest = [n for n in future if n["date"] != next_date]
    decision_as_of = issue_day

    def name_view(n):
        sym = n["symbol"]
        tier = tier_of(sym)
        abs_dist = distribution_for(sym, tier, all_events, "abs")
        sgn_dist = distribution_for(sym, tier, all_events, "sgn")
        own_n = sum(1 for e in past_events if e["sym"] == sym)
        priced_rec = priced_moves().get("names", {}).get(sym)
        priced_pct = priced_rec["priced_move_pct"] \
            if priced_rec else None
        fe17 = fe17_for_view(abs_dist, priced_pct, sym)
        if fe17["state"] == "recorded" and \
                abs_dist.get("state") == "recorded":
            # FE17 is the centre when its inputs exist: the
            # middle step and the typical move become its point
            # estimate. Reachable since 2026-10-30: priced move
            # and timing records landed, and the dispersion
            # input is the forecast error dispersion on record
            # under the registry amendment of that day.
            abs_dist = dict(abs_dist)
            steps = dict(abs_dist["steps_pct"])
            steps["0.5"] = fe17["centre_pct"]
            abs_dist["steps_pct"] = steps
            abs_dist["typical_pct"] = fe17["centre_pct"]
            abs_dist["centre_source"] = "fe17_blend"
        return {"symbol": sym, "date": n["date"], "tier": tier,
                "tier_label": TIER_LABELS[tier],
                "own_events": own_n,
                "abs": abs_dist, "signed": sgn_dist,
                "fe17_centre": fe17,
                "fe18_pead": fe18_state_for_view(n["date"],
                                                 issue_day),
                "priced_move_pct": priced_pct,
                "exceedance": _exceedance_for(
                    sym, tier, priced_pct, all_events)}

    next_views = [name_view(n) for n in next_cohort]
    rest_views = [name_view(n) for n in rest]

    chain_snapshots = 0
    if os.path.isdir(CHAINS_DIR):
        chain_snapshots = sum(len(files) for _r, _d, files
                              in os.walk(CHAINS_DIR))

    # ---- Record the live cohort through the machinery only.
    registry = Registry()
    ledger = Ledger(os.path.join(FORECAST_DIR, "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast record's chain does not verify")
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (CALENDAR_PATH, GATE_PATH, CACHE_PATH,
                      SWEEP_PATH, PANEL_PATH, GICS_PATH,
                      MAP_CARD_PATH, *governing_cal_paths)],
        "note": ("Spreads built from every report day on record "
                 "(321 stored past reports from 2022 to 2024 and "
                 "247 report days inside the shipped price "
                 "history) under the registered blend; governing "
                 "dates exactly as recorded in the calendar."),
        "clocks": {
            "event_time": next_date,
            "publication_time": calendar["recorded_at"],
            "first_available_time": calendar["recorded_at"],
            "ingestion_time": issued_ts,
            "decision_as_of": decision_as_of,
        },
    }
    created = 0
    horizon_signed_close = weekdays_after(next_date, 5)[-1]
    for view in next_views:
        sym = view["symbol"]
        if view["abs"]["state"] == "recorded":
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Size of the earnings-day move, either "
                          "way, in percent: spread of past moves "
                          "in steps of a tenth"),
                value={"leg": "abs_day",
                       "quantiles": view["abs"]["steps_pct"],
                       "typical_pct": view["abs"]["typical_pct"],
                       "band80_pct": [view["abs"]["low80_pct"],
                                      view["abs"]["high80_pct"]],
                       "blend": view["abs"]["blend"],
                       "own_events": view["abs"]["own_events"],
                       "group_events":
                           view["abs"]["group_events"],
                       "tier": view["tier"]},
                horizon_open=next_date, horizon_close=next_date,
                lineage=lineage,
                families=["events_calendar", "price"],
                outcome={"symbol": sym, "kind": "abs_return",
                         "base_date": decision_as_of,
                         "at_date": next_date})
            created += int(was)
        else:
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Size of the earnings-day move, either "
                          "way, in percent: spread of past moves "
                          "in steps of a tenth"),
                value={"leg": "abs_day",
                       "state": "abstain_at_issue",
                       "reason": view["abs"]["reason"],
                       "own_events": view["abs"]["own_events"],
                       "group_events":
                           view["abs"]["group_events"],
                       "tier": view["tier"]},
                horizon_open=next_date, horizon_close=next_date,
                lineage=lineage,
                families=["events_calendar", "price"],
                outcome={"symbol": sym, "kind": "abs_return",
                         "base_date": decision_as_of,
                         "at_date": next_date},
                absence_state="no_data",
                abstain_reasons=_history_reason(view["abs"]))
            created += int(was)
        if view["signed"]["state"] == "computed":
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Move over the 5 trading days after "
                          "the report day, in percent: spread of "
                          "past moves in steps of a tenth, "
                          "centred on no drift"),
                value={"leg": "signed_5s",
                       "quantiles": view["signed"]["steps_pct"],
                       "typical_pct":
                           view["signed"]["typical_pct"],
                       "band80_pct":
                           [view["signed"]["low80_pct"],
                            view["signed"]["high80_pct"]],
                       "centred": "zero_drift",
                       "blend": view["signed"]["blend"],
                       "own_events":
                           view["signed"]["own_events"],
                       "group_events":
                           view["signed"]["group_events"],
                       "tier": view["tier"]},
                horizon_open=next_date,
                horizon_close=horizon_signed_close,
                lineage=lineage,
                families=["events_calendar", "price"],
                outcome={"symbol": sym, "kind": "return",
                         "base_date": next_date,
                         "at_date": horizon_signed_close})
            created += int(was)
        else:
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Move over the 5 trading days after "
                          "the report day, in percent: spread of "
                          "past moves in steps of a tenth, "
                          "centred on no drift"),
                value={"leg": "signed_5s",
                       "state": "abstain_at_issue",
                       "reason": view["signed"]["reason"],
                       "own_events":
                           view["signed"]["own_events"],
                       "group_events":
                           view["signed"]["group_events"],
                       "tier": view["tier"]},
                horizon_open=next_date,
                horizon_close=horizon_signed_close,
                lineage=lineage,
                families=["events_calendar", "price"],
                outcome={"symbol": sym, "kind": "return",
                         "base_date": next_date,
                         "at_date": horizon_signed_close},
                absence_state="no_data",
                abstain_reasons=_history_reason(view["signed"]))
            created += int(was)
        # The bigger-than-priced leg (publication cure
        # 2026-10-30): where the priced move record covers this
        # name, the chance is the share of its group pool past
        # moves bigger than the priced move, ledgered as a real
        # forecast. Where it does not, the not-recorded
        # abstention row stands, exactly as before.
        exc = view["exceedance"]
        if exc.get("state") == "recorded":
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Chance the earnings-day move beats "
                          "the priced expected move"),
                value={"leg": "exceedance",
                       "state": "recorded",
                       "p": exc["share_bigger_than_priced"],
                       "priced_move_pct": exc["priced_move_pct"],
                       "pool_moves": exc["pool_moves"],
                       "tier": view["tier"]},
                horizon_open=next_date, horizon_close=next_date,
                lineage=lineage,
                families=["events_calendar", "modelled_inventory"],
                outcome={"symbol": sym, "kind": "binary_event",
                         "at_date": next_date})
        else:
            _row, was = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=issued_ts,
                subject=sym,
                quantity=("Chance the earnings-day move beats "
                          "the priced expected move"),
                value={"leg": "exceedance",
                       "state": "abstain_at_issue", "p": None,
                       "priced_move_pct": None,
                       "reason": exc["reason"],
                       "tier": view["tier"]},
                horizon_open=next_date, horizon_close=next_date,
                lineage=lineage,
                families=["events_calendar",
                          "modelled_inventory"],
                outcome={"symbol": sym, "kind": "binary_event",
                         "at_date": next_date},
                absence_state="no_data",
                abstain_reasons=[_forecast_ledger.feature_reason(
                    "missing", "priced_expected_move")])
        created += int(was)
    if not ledger.verify_chain():
        return fail("the forecast record's chain broke during "
                    "recording")

    recorded = abstained = graded = 0
    recorded_names = set()
    for row in ledger.rows():
        if row.get("engine_id") != ENGINE_ID:
            continue
        if row.get("type") == "forecast":
            if row.get("absence_state") == "present":
                recorded += 1
                recorded_names.add(row["subject"])
            else:
                abstained += 1
        if row.get("type") == "grade":
            graded += 1

    own_on_calendar = sum(
        1 for n in dated
        if any(e["sym"] == n["symbol"] for e in past_events))
    own_full = sum(
        1 for n in dated
        if sum(1 for e in past_events if e["sym"] == n["symbol"])
        >= OWN_FLOOR)

    data = {
        "tool": "Earnings Move Distribution",
        "state": "proving",
        "source": SOURCE_WORDS,
        "issued_ts": issued_ts,
        "issue_day": issue_day,
        "decision_as_of": decision_as_of,
        "panel_last_session": panel_last,
        "claim": {
            "text": ("For each company about to report, this "
                     "page publishes how big its earnings-day "
                     "move is likely to be, as a range built from "
                     "its own past reports and from similar-sized "
                     "companies. The promise it is graded on, "
                     "season by season: the range that is meant "
                     "to hold 80 out of every 100 reports will "
                     "hold between 75 and 85 of them."),
            "band_pct": 80, "claim_low": 75, "claim_high": 85},
        "how_built": (
            "Half of each range comes from the company's own "
            "past report days and half from companies in its "
            "size group, but the company's own half only counts "
            "when at least 8 of its past reports are on record; "
            "below that, the range is built from its group alone "
            "and its own count is printed. The 5-day range after "
            "the report is centred on no drift at all, because "
            "the record holds no evidence that reports drift one "
            "way or the other. Nothing is stretched or shrunk by "
            "a priced expected move, because no priced move is "
            "on record to scale by."),
        "calendar": {
            "recorded_on": calendar["recorded_on"],
            "recorded_at": calendar["recorded_at"],
            "names_on_record": len(merged),
            "dated": len(dated),
            "no_date": len(raw_undated),
            "no_date_names": raw_undated,
            "priced_moves_on_record": priced_moves().get(
                "priced_moves_on_record", 0),
            "chain_snapshots": chain_snapshots,
            "stale_note": ("The calendar was gathered on "
                           "October 12, 2026 and is out of date "
                           "by its own page's rule. Its dates are "
                           "used exactly as recorded."),
            "timing_note": ("Report timing now comes from "
                            "the earnings record lane, which "
                            "keeps the calendar source's own "
                            "time class for each dated name "
                            "(pre market, after hours, or not "
                            "supplied by the source). Names "
                            "whose class is not supplied keep "
                            "the report date itself as the "
                            "earnings day, named as a partial "
                            "reading, not a fact about the "
                            "company."),
            "second_list_note": ("A second list of upcoming "
                                 "dates disagrees with the "
                                 "calendar on a few names. It "
                                 "never governs an upcoming "
                                 "report here; the calendar does. "
                                 "Days from that second list that "
                                 "already sit inside the price "
                                 "history are counted only as "
                                 "past observations in the group "
                                 "history.")},
        "past_record": {
            "past_reports": len(past_events),
            "past_names": len({e["sym"] for e in past_events}),
            "panel_reports": len(panel_events),
            "panel_signed": panel_signed,
            "total_reports": len(all_events),
            "own_names_on_calendar": own_on_calendar,
            "own_full_names": own_full,
            "vintage_note": ("A company's own past reports on "
                             "record run from 2022 to 2024 "
                             "only. No stored report dates exist "
                             "after December 19, 2024 until the "
                             "report days inside the recent "
                             "price history, and no long price "
                             "panel is on file. The page claims "
                             "nothing beyond that.")},
        "tiers": [tier_pools[t] for t in
                  ("sp500", "sp400", "sp600", "untagged")],
        "next": {"date": next_date,
                 "decision_as_of": decision_as_of,
                 "signed_horizon_close": horizon_signed_close,
                 "names": next_views,
                 "count": len(next_views),
                 "new_rows_today": created},
        "rest": {"names": rest_views, "count": len(rest_views)},
        "missed": {
            "names": [{"symbol": n["symbol"], "date": n["date"],
                       "reason": ("its pre-report close had "
                                  "already passed when this "
                                  "engine first ran; it is "
                                  "counted, never backfilled")}
                      for n in missed],
            "count": len(missed)},
        "fe17_centre": _fe17_page_block(),
        "fe18_pead": _fe18_page_block(),
        "fe04_fair_gap_remainder": _fe04_page_block(),
        "exceedance": _exceedance_page_block(chain_snapshots),
        "history": {
            "label": ("History: every past report day on "
                      "record, forecast only from the report "
                      "days before it"),
            "seasons": season_rows,
            "pooled": pooled,
            "signed_pooled": signed_pooled,
            "note": ("Each past report below was forecast "
                     "using only report days recorded before "
                     "it, under the same half-and-half rule and "
                     "the same thin rule as the live ranges. "
                     "Early seasons had little history to draw "
                     "on, so many of their reports are counted "
                     "as skipped rather than graded. A season's "
                     "share is printed only when at least 30 "
                     "of its reports were graded. There are no "
                     "report days on record in 2025. This is "
                     "history, labelled as history; it is not "
                     "the live record.")},
        "live": {
            "names_recorded": len(recorded_names),
            "distribution_forecasts_recorded": recorded,
            "not_recorded_rows": abstained,
            "forecasts_graded": graded,
            "season_dated_names": len(dated),
            "season_all_names": len(merged),
            "target": "two full seasons",
            "seasons_completed": 0},
        "self_test": {"cases": test["cases"],
                      "passed": test["passed"]},
        "kill_criterion": (
            "After two full seasons, this engine is retired if "
            "a season's middle-80-percent range covers less "
            "than 70 percent or more than 90 percent of that "
            "season's reports, or if the score for its "
            "bigger-than-priced chances is no better than "
            "simply quoting the priced move's own implied "
            "chance."),
        "thin_rule": (
            "A part is not published from a thin pool: a "
            "company's own history counts only at 8 or more of "
            "its past reports, a group's part needs at least 30 "
            "past moves in that group, and a season's coverage "
            "share is printed only at 30 or more graded "
            "reports. Below those counts, the count itself is "
            "shown with the reason."),
        "grading_note": (
            "Grading uses the shared scoring machinery once "
            "the price history passes each report date; the "
            f"price history on record ends {panel_last}. "
            + (f"{graded} live forecasts are graded so far; "
               "the rest grade as their report dates pass. "
               if graded else
               "No live forecast has matured yet, so nothing "
               "live is graded so far. ")
            + "The bigger-than-priced "
            "part has no grade until a priced move exists for "
            "a name."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (calendar {len(dated)} dated + "
          f"{len(raw_undated)} no-date; past {len(past_events)} "
          f"+ panel {len(panel_events)} report days; history "
          f"pooled coverage {pooled['coverage']} over "
          f"{pooled['graded']} graded; next cohort {next_date}: "
          f"{len(next_views)} names, {created} new rows, "
          f"{recorded} recorded + {abstained} not-recorded in "
          "total)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
