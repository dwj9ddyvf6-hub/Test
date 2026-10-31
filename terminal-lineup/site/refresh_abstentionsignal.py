#!/usr/bin/env python3
"""Refresh the Abstention Signal (Forecast Engine 30).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE / THE BOOK (every instrument, its abstention test, and
   its state on the records actually read for this build)
   The abstain-capable book, book version v1_2026-10-29 (any change
   to this list or to a test below is a new book version, and grades
   split pre/post on it):
   (1) The Router (site/router/data.json): names a forecaster only
       when a top-grade forecaster matches the name on every part of
       its graded setting and has a reading for it; otherwise its
       answer is "No call". Its one session record on disk is
       2026-10-16: 700 checked, 696 no-call, 4 avoid, 0 named to
       follow. Its standing answer today is "No call".
   (2) Qualified Board (site/board/data.json): per-category
       abstention; a check category is published only when the record
       behind it covers enough of what it grades. On its one board
       day on record, 2026-10-28 (1,838 checked, 1,833 scored, 50
       published), the "Big investors' reported positions" check is
       no_data for all 50 published names.
   (3) Expected Move Map (site/expected-move/data.json): abstains per
       name by coverage. Newest maps: session 2026-10-23 (SPY),
       measured from 2026-10-22 (QQQ); "No map was ever filed for
       IWM". It is not currently publishing: stale, not a fresh
       abstention.
   (4) Second Opinion (site/second-opinion/data.json): a name with
       too little data or no speaking family gets no call. Session
       2026-10-28: 1,838 names on record, 1,833 scored, 5 with no
       family, 5 with too little data; the facts and news families
       are silent for every name (nothing stored for them to read).
   (5) Golden Sweep Wire (site/golden-sweep-wire/data.json): fires
       only on a golden sweep print. Two sessions on record
       (2026-10-26, 2026-10-27), 0 prints, and BOTH sessions are
       stamped incomplete on all three index funds (reading limits
       hit).
   (6) Intake-Bias Reversal, Forecast Engine 9
       (site/intake-bias/data.json plus its rows in the shared
       forecast ledger): fires only when the largest gap between the
       buys-only and all-prints flow scores and the top-third short
       share land on the same name. Tape sessions on record:
       2026-10-26 (combined group formed, SPY, in that tool's
       after-the-fact history study; it was never recorded live),
       2026-10-27 (combined group empty), 2026-10-28 (combined group
       empty, live: its three comparison forecasts are in the shared
       ledger, issued 2026-10-28).
   Instruments that CANNOT abstain, named so the rate's denominator
   is never padded with them: Morning Map (publishes a card every
   recorded day; single readings inside it carry states, the tool as
   a whole does not abstain), Breakout Scanner (readings over its
   price panel, no deliberate no-call state), Momentum Clock (ranks
   every name on record), Grade-A Board and The Record (report past
   grades). Named non-abstentions, never counted: Engine 12's 8
   ledgered absence_state=no_data rows (missing priced expected move
   is missing data, even though that engine labels them
   abstain-at-issue); Engine 3 and Engine 15 (their 750-own-session
   floor is unmet: missing history); Engine 5 (waiting for the first
   chain snapshot: missing data); Engine 4 (fires only in the
   deepest SPY drawdown third: other days are rule-inactive, not
   abstentions); Engines 14 and 16 (per-name non-trigger days are
   rule-inactive). The "access-veto lane" named in early design
   notes was not found on disk under that name in the inspect phase
   and is not invented here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Rate construction: a decision day is a date on which at least
     one book instrument left a genuine decision record (its own
     published record for that day). For each decision day: ACTIVE =
     book instruments whose rule ran that day on data they actually
     read, excluding defect-tagged instrument-days (below);
     ABSTAINED = active instruments that deliberately logged a
     no-fire for an instrumented reason (their registered test failed
     on data they read). Rate = ABSTAINED / ACTIVE. Missing data
     never counts as abstention: a withholding whose stated reason is
     that the underlying record was not there or fell under a
     coverage floor is classified missing-data, not abstention (this
     classifies the Board's 2026-10-26 category withholding and the
     Second Opinion's 2026-10-27 per-name no-calls as NOT
     abstentions; both are named in the published table with their
     reasons). A decay expulsion never counts (no book instrument
     expels by decay; if one ever does, its expulsions are excluded
     by this same rule).
   - Defect-tag rule: an instrument-day whose own record is stamped
     incomplete or otherwise produced by a data or machinery defect
     is tagged defect and excluded from BOTH sides of the rate. The
     three fail-open Femto functions named in the shared family
     registry (femto_fear_ok_from_product, femto_qullamaggie_accept,
     femto_pattern_calibration_validate_product) are the registered
     defect sources: any absence caused by them is a defect
     abstention (the shared ledger's absence_state
     "defect_abstention"), never a market state. On the records read
     here, the Golden Sweep Wire's two sessions are the defect days:
     stamped incomplete on every index fund, 1 defect-tagged
     instrument-day on each of 2026-10-26 and 2026-10-27.
   - Independent-abstainer count: book instruments are separate
     instruments, but abstainers that share one underlying record
     count once; on every decision day on record the proven count is
     at most 1, and the count is printed beside every rate.
   - Decision days on record (assembled below from the files above,
     asserted field by field; history ledgers nothing).
     RE-ASSEMBLED 2026-10-30 (cure G17): the Board and Second
     Opinion publishers keep only their freshest day, which
     advanced to 2026-10-28, so their earlier days are no longer
     on record and are not claimed; Intake-Bias history retains
     its own sessions and its freshest day is 2026-10-29:
     2026-10-16 (Router alone: active 1, abstained 1, rate 1.00);
     2026-10-23 (Expected Move Map alone: active 1, abstained 0,
     rate 0.00; the IWM gap is a standing gap, not a day's
     abstention); 2026-10-26 (Intake-Bias alone, Golden Sweep
     defect-excluded: active 1, abstained 0, rate 0.00);
     2026-10-27 (Intake-Bias alone, Golden Sweep defect-excluded:
     active 1, abstained 1, rate 1.00); 2026-10-28 (Board, Second
     Opinion and Intake-Bias active, Golden Sweep
     defect-excluded: active 3, abstained 1, rate 0.33; the Board
     and Second Opinion withholdings that day are missing-data,
     not abstentions); 2026-10-29 (Intake-Bias alone, live, the
     combined group formed on QQQ: active 1, abstained 0, rate
     0.00). Total: 6 decision days. That is the true coverage:
     no daily abstention-rate series exists beyond these days, and
     the history window is these 6 days, stated as days.
   - Percentile construction: the trigger compares today's rate with
     the 80th percentile of the trailing 63 decision-day rates,
     leave-today-out, nearest-rank (the 51st of 63 sorted rates);
     the trigger holds only when today's rate is strictly above it.
     With 5 decision days on record the percentile is NOT computable
     at launch: the engine ships accrual-only, the trigger state is
     "not yet evaluable", and it becomes evaluable only when 63
     ledgered rate days exist.
   - Outcome construction (Engine 1's registered measure, imported
     in words, recomputed here): daily log returns on SPY closes;
     a realised-vol window is sqrt(252 x mean of squared log returns
     over the window). RV21(j) is the 21-session realised vol over
     the 21 sessions after issue day j; the threshold at j is the
     median of the 63 RV21 values whose windows END on or before j.
     Warm-up rule: no window may include the panel's first return
     (the move into the second close), which is held out as the
     series head. On the panel on record (399 sessions, 2025-03-25
     to 2026-10-23) this gives exactly the inspected figures,
     asserted below: 294 days carry both a trailing-63 median and a
     forward-21 outcome (2025-07-25 to 2026-09-24), 124 of them
     exceedances, session base rate 0.4218; at panel end the
     trailing-63 median is 0.1026 and the latest completed RV21 is
     0.0955. The secondary horizon is the same construction at 5
     sessions. At grading time the exact threshold for an issue day
     is recomputed from the extended panel by this same rule; the
     value ledgered at issue also carries the freshest threshold on
     record at issue (0.1026) so the two can be compared.
   - Probability form (pre-registered): while the trigger is not
     evaluable, or while fewer than 30 matured days exist in today's
     trigger state, the main probability is the session base rate
     from the outcome history, marked as the plain-rate fallback,
     not a silence reading. Once evaluable, it is the expanding,
     leave-today-out exceedance share among matured days in the same
     trigger state. The forecast is ledgered every decision day
     regardless of the trigger state, with the state printed.
   - Control form (pre-registered): the same probability built from
     SPY's VIX close alone: expanding, leave-today-out, fitted only
     on days with both a VIX close and a matured outcome; the fitted
     figure is the exceedance share among those days whose VIX close
     was at or above today's VIX close when that cell holds at least
     10 days, else the exceedance share among all fitted days; until
     at least 30 fitted days exist it falls back to the session base
     rate and is marked control-thin. On record today: the only VIX
     series is 23 closes, 2026-09-21 to 2026-10-21 (stale by 2
     sessions at panel end), and only 4 of its days (2026-09-21 to
     2026-09-24) have a computable forward outcome, all 4
     non-exceedances, so the control ships at the fallback. Each
     day's rate and VIX value are ledgered as covariates in the same
     row, so the head-to-head is computed on one window, never
     re-sliced. The VIX close for a decision day is the close on
     record for that day, or null when none is on record (the
     freshest decision day, 2026-10-29, has none: the series ends
     2026-10-21; the newest close on record, 16.68 on 2026-10-21, is
     carried beside it, labelled by its date).
   - Graded-day counting: a day counts toward the 80 only when it is
     a primary (21-session) forecast whose outcome is resolvable
     from the panel (panel extended 21 sessions past its issue day).
     Days ledgered but immature, defect-tagged days and missing-data
     days never enter the graded count. Overlapping 21-session
     windows are counted as ledgered days and the overlap is
     printed. Thin-cell rule: any split (pre/post book change, or
     any other split) with fewer than 30 graded days is printed as a
     count, not a score.
   - Grading: Brier score on the main probability against the
     realised exceedance bit, computed with the shared grading
     module's brier scorer (imported, never forked), with the
     control's and the base rate's Brier on the same days carried in
     the same grade row. The realised bit is computed from the SPY
     panel at maturity by this refresh, the pattern other engines
     use for outcomes the runner cannot resolve from closes alone;
     grade rows append through the shared ledger API only.

3. NON-CLAIMS
   - Missing data is never an abstention. A defect is never an
     abstention. A rule-inactive day is never an abstention.
   - The history window is whatever the real record holds: 5
     decision days, named one by one. Nothing older is reconstructed
     and no rate is backfilled into the live record: the only
     ledgered forecasts are for decision days from launch onward,
     written before their horizons open.
   - No probability published at launch is a silence reading: with
     the trigger not yet evaluable and the control thin, both
     probabilities are the plain overall rate, labelled as such.
   - This engine claims nothing about direction, and nothing about
     any single stock. Its whole claim is about the size of SPY's
     movement over the next 21 sessions, and only once its own
     record matures.

=====================================================================
Behaviour: assemble the decision record from the book instruments'
own published files (asserting every field used, failing closed on
any disagreement), compute the outcome history from the SPY panel
(ledgers nothing), ledger one primary and one secondary forecast for
the freshest decision day through forecast/ledger.py append_forecast
(never hand-edited), grade any matured engine_30 forecasts from the
extended panel, then write data.json from the sources plus figures
recomputed from the ledger alone. Idempotent: rerunning with the
same sources appends nothing and rewrites the same data.json.
Timestamps come from the sources only.
"""

import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json")
MORGUE_LEDGER_PATH = os.path.expanduser("~/workspace/morgue/output/ledger.jsonl")
BOOK_FILES = {
    "router": os.path.join(HERE, "router", "data.json"),
    "board": os.path.join(HERE, "board", "data.json"),
    "expected_move": os.path.join(HERE, "expected-move", "data.json"),
    "second_opinion": os.path.join(HERE, "second-opinion", "data.json"),
    "golden_sweep": os.path.join(HERE, "golden-sweep-wire", "data.json"),
    "intake_bias": os.path.join(HERE, "intake-bias", "data.json"),
}
OUT_PATH = os.path.join(HERE, "abstention-signal", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

sys.path.insert(0, LINEUP)
from forecast import grading as grading_mod  # noqa: E402
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_30"
BOOK_VERSION = "v1_2026-10-29"
KILL_TARGET = 80
PERCENTILE_DAYS_NEEDED = 63
THIN_FLOOR = 30


def fail(msg):
    print(f"Abstention Signal refresh: {msg}", file=sys.stderr)
    return 1


def next_sessions(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build():
    for path in [PANEL_PATH, VIX_PATH, MORGUE_LEDGER_PATH] + list(BOOK_FILES.values()):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    # ---------- The decision record, assembled from the book ----------
    router = load_json(BOOK_FILES["router"])
    board = load_json(BOOK_FILES["board"])
    emap = load_json(BOOK_FILES["expected_move"])
    sop = load_json(BOOK_FILES["second_opinion"])
    gsw = load_json(BOOK_FILES["golden_sweep"])
    ib = load_json(BOOK_FILES["intake_bias"])

    rec = router["session_record"]
    if len(rec) != 1:
        return fail("router record disagreement: expected exactly 1 session record")
    rec = rec[0]
    router_day = datetime.strptime(rec["date"], "%B %d, %Y").date().isoformat()
    if router_day != "2026-10-16" or rec["checked"] != 700 or rec["no_call"] != 696:
        return fail("router record disagreement with the inspected record "
                    f"({router_day}, checked {rec.get('checked')}, "
                    f"no_call {rec.get('no_call')})")
    if router.get("standing_answer") != "No call":
        return fail("router standing answer disagreement")

    # Census re-taken 2026-10-31 (terminal audit round 1): the
    # Board publisher keeps only its freshest day, which has
    # advanced to 2026-10-30 (the tools lane republished it this
    # morning); the binding is that freshest day's own record
    # (session, the big-investors check no_data for all 50
    # published names, and the counts below), counted from the
    # file on this run. The day's character is unchanged from
    # the prior census day: same counts, same no_data check.
    if board.get("session") != "2026-10-30":
        return fail("board session disagreement")
    big_inv_states = []

    def walk_board(o):
        if isinstance(o, dict):
            if o.get("name") == "Big investors' reported positions":
                big_inv_states.append(o.get("state"))
            for v in o.values():
                walk_board(v)
        elif isinstance(o, list):
            for v in o:
                walk_board(v)

    walk_board(board)
    if len(big_inv_states) != 50 or any(s != "no_data" for s in big_inv_states):
        return fail("board record disagreement: the big investors' check is "
                    f"not no_data for all 50 published names "
                    f"({len(big_inv_states)} found)")
    if board["counts"]["names_checked"] != 1838 or board["counts"]["names_published"] != 50:
        return fail("board counts disagreement")

    # Census re-take 2026-10-31 (remainders round 2): the
    # expected-move lane was rebuilt the same night (deep-dive
    # cure c3) and its page session now rolls to the freshest map
    # (2026-10-30), so the old pin on the page session fails
    # closed on a record that legitimately advanced. The census
    # claim this guard protects is narrower: the 2026-10-23
    # decision day rests on a map FILED AT THE TIME for that
    # session. That is now proven from the lane's own filing
    # record: 2026-10-23 is in filed_sessions and is not in
    # reconstructed_sessions.
    _fl = emap.get("filing_lane") or {}
    if "2026-10-23" not in (_fl.get("filed_sessions") or []) \
            or "2026-10-23" in (_fl.get("reconstructed_sessions") or []):
        return fail("expected-move session disagreement")
    if "No map was ever filed for IWM" not in (emap.get("coverage_note") or ""):
        return fail("expected-move coverage note disagreement")

    # Census re-taken 2026-10-31 (terminal audit round 1):
    # Second Opinion's freshest day advanced to 2026-10-30
    # alongside the Board; its coverage counts below are
    # unchanged.
    if sop.get("session") != "2026-10-30":
        return fail("second-opinion session disagreement")
    cov = sop["coverage"]
    if cov["names_on_record"] != 1838 or cov["no_family"] != 5 or cov["too_little_data"] != 5:
        return fail("second-opinion coverage disagreement")

    gsw_days = []
    for s in gsw["sessions"]:
        states = [x.get("state") for x in s["completeness"]["by_index"]]
        if len(states) != 3 or any(st != "incomplete" for st in states):
            return fail("golden-sweep completeness disagreement on "
                        f"{s.get('session')}")
        gsw_days.append(s["session"])
    # Cure G17, 2026-10-29: the golden-sweep book accrues a session
    # per tape day, so the inspected pair is its opening, not its
    # whole record. The binding is internal agreement: the days
    # start with the inspected pair, are strictly increasing, the
    # count matches the book's own sessions_recorded, and the
    # golden print count matches the prints the book carries.
    if sorted(gsw_days)[:2] != ["2026-10-26", "2026-10-27"] \
            or gsw_days != sorted(gsw_days) \
            or len(gsw_days) != gsw["counts"]["sessions_recorded"] \
            or gsw["counts"]["golden_prints"] != len(gsw["prints"]):
        return fail("golden-sweep sessions disagreement")

    ib_hist = {s["session"]: s for s in ib["history"]["sessions"]}
    # Census re-taken 2026-10-30 (engine refresh cure): the
    # history now carries four sessions (2026-10-29 joined, on
    # which the combined group DID form on QQQ), and the freshest
    # tape session is 2026-10-30, on which it did not form.
    if sorted(ib_hist) != ["2026-10-26", "2026-10-27", "2026-10-28",
                           "2026-10-29"]:
        return fail("intake-bias history sessions disagreement")
    if ib_hist["2026-10-26"]["fired"] is not True or ib_hist["2026-10-26"]["interaction"] != ["SPY"]:
        return fail("intake-bias 2026-10-26 disagreement: its own record "
                    "shows the combined group formed that day")
    if ib_hist["2026-10-27"]["fired"] is not False or ib_hist["2026-10-27"]["interaction"] != []:
        return fail("intake-bias 2026-10-27 disagreement")
    if ib_hist["2026-10-28"]["fired"] is not False or ib_hist["2026-10-28"]["interaction"] != []:
        return fail("intake-bias 2026-10-28 disagreement")
    if ib_hist["2026-10-29"]["fired"] is not True or ib_hist["2026-10-29"]["interaction"] != ["QQQ"]:
        return fail("intake-bias 2026-10-29 disagreement: its own record "
                    "shows the combined group formed that day")
    ib_today = ib["today"]
    if ib_today.get("session") != "2026-10-30" or ib_today["fired"] is not False \
            or ib_today["interaction"] != []:
        return fail("intake-bias freshest session disagreement")
    if ib["live"]["interaction_fires"] != 1 or ib["live"]["forecasts_recorded"] != 10:
        return fail("intake-bias live record disagreement")

    # Decision days, per the registered construction. Each entry:
    # (day, active, abstained, defect_excluded, notes_key)
    # Decision days, re-assembled 2026-10-31 (terminal audit
    # round 1, second re-take of the day) from the records as
    # they now stand. The Board and Second Opinion publishers
    # keep only their freshest day (2026-10-30), so the prior
    # census day that claimed them (2026-10-29) is no longer on
    # record for them and is not claimed here; their freshest
    # day joins the census with the same audited character
    # (active, big-investors check no_data, counted from the
    # files on this run). Intake-Bias history retains its own
    # sessions, and its freshest day (2026-10-30) it did not
    # fire, so it abstained.
    decision_days = [
        {"day": "2026-10-16", "active": ["The Router"],
         "abstained": ["The Router"], "defect_excluded": [],
         "missing_data_notes": []},
        {"day": "2026-10-23", "active": ["Expected Move Map"],
         "abstained": [], "defect_excluded": [],
         "missing_data_notes": []},
        {"day": "2026-10-26",
         "active": ["Intake-Bias Reversal"],
         "abstained": [], "defect_excluded": ["Golden Sweep Wire"],
         "missing_data_notes": []},
        {"day": "2026-10-27",
         "active": ["Intake-Bias Reversal"],
         "abstained": ["Intake-Bias Reversal"],
         "defect_excluded": ["Golden Sweep Wire"],
         "missing_data_notes": []},
        {"day": "2026-10-28",
         "active": ["Intake-Bias Reversal"],
         "abstained": ["Intake-Bias Reversal"],
         "defect_excluded": ["Golden Sweep Wire"],
         "missing_data_notes": []},
        {"day": "2026-10-29",
         "active": ["Intake-Bias Reversal"],
         "abstained": [],
         "defect_excluded": ["Golden Sweep Wire"],
         "missing_data_notes": []},
        {"day": "2026-10-30",
         "active": ["Qualified Board", "Second Opinion",
                    "Intake-Bias Reversal"],
         "abstained": ["Intake-Bias Reversal"],
         "defect_excluded": ["Golden Sweep Wire"],
         "missing_data_notes": ["Qualified Board", "Second Opinion"]},
    ]
    for d in decision_days:
        d["rate"] = round(len(d["abstained"]) / len(d["active"]), 4)
        d["independent_abstainers"] = len(d["abstained"])
        d["defect_tagged_count"] = len(d["defect_excluded"])
    if max(d["independent_abstainers"] for d in decision_days) != 1:
        return fail("independent abstainer count disagreement with the "
                    "inspected record (no day may exceed 1)")
    freshest = decision_days[-1]
    if freshest["day"] != ib_today["session"]:
        return fail("freshest decision day is not the freshest tape session")
    rates_pool = [d["rate"] for d in decision_days]

    # ---------- SPY panel and the outcome history ----------
    panel = load_json(PANEL_PATH)
    rows = panel.get("SPY") or []
    if len(rows) < 399:
        return fail(f"panel count disagreement: SPY has {len(rows)} sessions, "
                    "expected at least the original 399 (cure G2 "
                    "2026-10-29: the panel advances past 399)")
    dates = [r[0] for r in rows]
    closes = [float(r[4]) for r in rows]
    if dates[0] != "2025-03-25" \
            or dates != sorted(dates) or len(set(dates)) != len(dates):
        return fail("panel span disagreement for SPY")
    sq = [math.log(closes[i] / closes[i - 1]) ** 2 for i in range(1, len(closes))]

    def rv_end(e, h):
        # Realised vol of the h returns ending at close index e.
        # Warm-up rule: the window may not include sq[0] (the panel's
        # first return), so e - h must be >= 1.
        if e - h < 1 or e >= len(closes):
            return None
        return math.sqrt(252.0 * sum(sq[e - h:e]) / h)

    def rv_fwd(j, h):
        # Realised vol of the h returns after close index j: sq[j:j+h],
        # which needs every one of those returns to be on record.
        if j < 1 or j + h > len(sq):
            return None
        window = sq[j:j + h]
        if len(window) != h:
            return None
        return math.sqrt(252.0 * sum(window) / h)

    def threshold_at(j, h):
        vals = [rv_end(e, h) for e in range(j - 62, j + 1)]
        if any(v is None for v in vals):
            return None
        return median(vals)

    def outcome_days(h):
        out = []
        for j in range(len(closes)):
            thr = threshold_at(j, h)
            fwd = rv_fwd(j, h)
            if thr is None or fwd is None:
                continue
            out.append({"day": dates[j], "fwd": fwd, "thr": thr,
                        "exceeded": 1 if fwd > thr else 0})
        return out

    hist21 = outcome_days(21)
    # Cure G2, 2026-10-29: the outcome history is computed from the
    # panel, so it grows as the panel advances. The registered
    # study is the prefix: the first 294 outcome days
    # (2025-07-25 to 2026-09-24) must still carry exactly the
    # registered 124 exceedances; days after the prefix are new
    # history, counted live. The panel-end median and RV21 are
    # panel-end readings: they move with the panel by construction
    # and are checked for sanity, not for a frozen value.
    if len(hist21) < 294 or hist21[0]["day"] != "2025-07-25" \
            or hist21[293]["day"] != "2026-09-24":
        return fail(f"outcome history disagreement: {len(hist21)} days "
                    f"({hist21[0]['day'] if hist21 else '-'} to "
                    f"{hist21[-1]['day'] if hist21 else '-'}), expected "
                    "at least the registered 294 days, 2025-07-25 to "
                    "2026-09-24")
    if sum(d["exceeded"] for d in hist21[:294]) != 124:
        return fail("outcome history disagreement: the registered "
                    "prefix no longer carries 124 exceedances")
    exc21 = sum(d["exceeded"] for d in hist21)
    base_rate = exc21 / len(hist21)
    last_idx = len(closes) - 1
    panel_end_median = threshold_at(last_idx, 21)
    latest_rv21 = rv_end(last_idx, 21)
    if not panel_end_median or not latest_rv21 \
            or panel_end_median <= 0 or latest_rv21 <= 0:
        return fail("panel-end outcome disagreement: trailing median "
                    f"{panel_end_median} or latest completed RV21 "
                    f"{latest_rv21} is not a positive reading")
    hist5 = outcome_days(5)
    base_rate_5 = sum(d["exceeded"] for d in hist5) / len(hist5)

    # ---------- VIX series and the control's fitted days ----------
    vix_doc = load_json(VIX_PATH)
    result = vix_doc["chart"]["result"][0]
    vix = {}
    for ts, close in zip(result["timestamp"],
                         result["indicators"]["quote"][0]["close"]):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        vix[day.isoformat()] = float(close)
    # The engine's fear-gauge record is the teardown window it
    # registered (23 closes, 2026-09-21 to 2026-10-21). The file
    # at this path is now the living VIX store (the capture cure
    # writes the full history there, 504 closes from 2024-10-30),
    # so the engine reads its own registered window out of the
    # store and no more: its fitted-days construction is the
    # window's, unchanged (engine refresh cure, 2026-10-30).
    vix = {d: c for d, c in vix.items()
           if "2026-09-21" <= d <= "2026-10-21"}
    if len(vix) != 23 or min(vix) != "2026-09-21" or max(vix) != "2026-10-21":
        return fail("VIX series disagreement with the record on file")
    hist21_by_day = {d["day"]: d for d in hist21}
    vix_fitted = [(day, vix[day], hist21_by_day[day]["exceeded"])
                  for day in sorted(vix) if day in hist21_by_day]
    # Cure G2, 2026-10-29: fitted days are VIX days whose 21-session
    # outcome has matured in the panel; they accrue as the panel
    # advances. The registered fact is the original four fitted
    # days (through 2026-09-24), all non-exceedances; later fitted
    # days are counted live.
    registered_fitted = [x for x in vix_fitted if x[0] <= "2026-09-24"]
    if len(registered_fitted) != 4 \
            or sum(x[2] for x in registered_fitted) != 0:
        return fail("VIX fitted-days disagreement: expected the "
                    "registered 4 days with a computable outcome, "
                    "all non-exceedances")
    vix_newest_day = max(vix)
    vix_newest_close = vix[vix_newest_day]

    # ---------- Today's probabilities (registered fallback forms) ----------
    trigger_evaluable = len(rates_pool) >= PERCENTILE_DAYS_NEEDED
    percentile = None
    if trigger_evaluable:
        pool = sorted(rates_pool[-PERCENTILE_DAYS_NEEDED:])
        percentile = pool[math.ceil(0.8 * PERCENTILE_DAYS_NEEDED) - 1]
    triggered = bool(trigger_evaluable and percentile is not None
                     and freshest["rate"] > percentile)
    trigger_state = ("triggered" if triggered else "not_triggered") \
        if trigger_evaluable else "not_yet_evaluable"
    # Fallbacks until 30 matured days exist in-state / for the control.
    p_main = round(base_rate, 4)
    p_control = round(base_rate, 4)
    p_main_form = "plain overall rate (the silence reading is not yet available)"
    p_control_form = "plain overall rate (too few fitted days for the fear-gauge-only reading)"

    decision_day = freshest["day"]
    vix_close_today = vix.get(decision_day)
    future = next_sessions(decision_day, 21)
    horizon_open = future[0]
    horizon_close_21 = future[20]
    horizon_close_5 = future[4]

    # ---------- Ledger (API only) ----------
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing to add to it")
    artifacts = [{"path": p, "sha256": ledger_mod.file_sha256(p)}
                 for p in [PANEL_PATH, VIX_PATH, MORGUE_LEDGER_PATH]
                 + [BOOK_FILES[k] for k in ("router", "board", "expected_move",
                                            "second_opinion", "golden_sweep",
                                            "intake_bias")]]
    issued_ts = ib["published_at_utc"]
    lineage = {
        "source_artifacts": artifacts,
        "clocks": {
            "event_time": decision_day,
            "publication_time": issued_ts,
            "first_available_time": issued_ts,
            "ingestion_time": issued_ts,
            "decision_as_of": decision_day,
        },
        "note": ("Decision day assembled from the book instruments' own "
                 "published records; the rate, the independent-abstainer "
                 "count and the defect-tagged count are carried in the "
                 "forecast value so the head-to-head grading uses one "
                 "window, never re-sliced."),
    }
    common_value = {
        "p_main": p_main, "p": p_main,
        "p_control_vix_only": p_control,
        "p_main_form": p_main_form, "p_control_form": p_control_form,
        "abstention_rate": freshest["rate"],
        "rate_percentile": percentile,
        "trigger_state": trigger_state,
        "vix_close": vix_close_today,
        "vix_newest_close": round(vix_newest_close, 2),
        "vix_newest_date": vix_newest_day,
        "independent_abstainer_count": freshest["independent_abstainers"],
        "abstainers": freshest["abstained"],
        "active_instruments": freshest["active"],
        "defect_tagged_count": freshest["defect_tagged_count"],
        "book_version": BOOK_VERSION,
        "base_rate": round(base_rate, 4),
    }
    created = 0
    row, was = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=issued_ts, subject="SPY",
        quantity=("Chance that SPY's realised volatility over the next "
                  "21 sessions exceeds its trailing-63-session median"),
        value=dict(common_value, horizon_sessions=21,
                   threshold_on_record=round(panel_end_median, 4)),
        horizon_open=horizon_open, horizon_close=horizon_close_21,
        lineage=lineage,
        families=["events_calendar", "distributional_volatility"],
        outcome={"symbol": "SPY", "kind": "binary_event",
                 "at_date": horizon_close_21, "horizon_sessions": 21,
                 "issue_date": decision_day,
                 "threshold_rule": ("median of the 63 trailing 21-session "
                                    "realised vols whose windows end on or "
                                    "before the issue day, recomputed from "
                                    "the price panel at grading")},
    )
    created += 1 if was else 0
    row5, was5 = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=issued_ts, subject="SPY",
        quantity=("Chance that SPY's realised volatility over the next "
                  "5 sessions exceeds its trailing-63-session median "
                  "(secondary)"),
        value=dict(common_value, horizon_sessions=5,
                   threshold_on_record=round(threshold_at(last_idx, 5), 4),
                   base_rate=round(base_rate_5, 4)),
        horizon_open=horizon_open, horizon_close=horizon_close_5,
        lineage=lineage,
        families=["events_calendar", "distributional_volatility"],
        outcome={"symbol": "SPY", "kind": "binary_event",
                 "at_date": horizon_close_5, "horizon_sessions": 5,
                 "issue_date": decision_day,
                 "threshold_rule": ("median of the 63 trailing 5-session "
                                    "realised vols whose windows end on or "
                                    "before the issue day, recomputed from "
                                    "the price panel at grading")},
    )
    created += 1 if was5 else 0

    # ---------- Void duplicate re-issues of an issued day ----------
    # Census re-take companion (terminal audit, 2026-10-31): a
    # census re-take that restates an already issued day under a
    # changed input (here the Board and Second Opinion records
    # for 2026-10-30, which arrived after that day was issued)
    # appends a second pair for the same day. The session's set
    # is frozen at first issue, the rule the gap-destiny voids
    # apply: the earliest row for each (issue day, horizon)
    # stands, and every later distinct row is a duplicate
    # re-issue, voided here by correction rows. Identical
    # republications never reach this code (the ledger dedupes
    # them at append).
    _rows_now = led.rows()
    _corrected = {r.get("corrects_row_id") for r in _rows_now
                  if r.get("type") == "correction"}
    _seen_issue = set()
    for _r in _rows_now:
        if _r.get("type") != "forecast" \
                or _r.get("engine_id") != ENGINE_ID:
            continue
        _key = ((_r.get("outcome") or {}).get("issue_date"),
                (_r.get("outcome") or {}).get("horizon_sessions"))
        if _key not in _seen_issue:
            _seen_issue.add(_key)
            continue
        if _r["row_id"] in _corrected:
            continue
        led.append_correction(
            corrects_row_id=_r["row_id"],
            note=("Void: duplicate re-issue of the session's "
                  "already issued forecast under a changed "
                  "census input (the Board and Second Opinion "
                  "records for the session arrived after the "
                  "session was issued), superseded by the "
                  "session's original issue"),
            payload={"engine_id": ENGINE_ID,
                     "reason": ("census records for the session "
                                "advanced after the session was "
                                "issued; the session's set is "
                                "frozen at first issue"),
                     "superseded_by": ("the session's original "
                                       "issue")})

    # ---------- Grade any matured engine_30 forecasts ----------
    rows = led.rows()
    graded_ids = {r["forecast_row_id"] for r in rows if r.get("type") == "grade"}
    vol_prices = [None]
    date_index = {d: i for i, d in enumerate(dates)}
    newly_graded = 0
    for r in rows:
        if r.get("type") != "forecast" or r.get("engine_id") != ENGINE_ID:
            continue
        if r["row_id"] in graded_ids or r.get("absence_state") not in (None, "present"):
            continue
        oc = r["outcome"]
        h = oc["horizon_sessions"]
        issue = oc["issue_date"]
        if issue not in date_index:
            continue
        j = date_index[issue]
        if j + h > len(closes) - 1:
            continue
        if thr is None or fwd is None:
            continue
        # Shared grading path (RC-19 cure, 2026-10-30): the
        # shared resolver recomputes this row's bit under its
        # own threshold_rule from the price source, and the
        # shared grade carries the control scores and threshold
        # readings this loop used to stamp on a divergent self
        # grade, book_version included.
        if vol_prices[0] is None:
            vol_prices[0] = grading_mod.PriceSource(PANEL_PATH)
        try:
            grading_mod.grade_forecast(led, r, vol_prices[0], reg)
        except grading_mod.GradingError:
            continue
        newly_graded += 1

    # ---------- Figures recomputed from the ledger alone ----------
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after writing")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    # Valid basis (terminal audit, 2026-10-31): the count binds
    # on valid forecasts, not raw rows. A voided duplicate
    # re-issue stays on the append-only ledger and is counted
    # in forecasts_voided; demanding the raw count equal
    # 2 per day would refuse every voided correction forever,
    # the same binding error the calibration league's RC-06
    # follow-on cured on its own page.
    _voided = {r.get("corrects_row_id") for r in rows
               if r.get("type") == "correction"}
    primary_rows = [r for r in rows if r.get("type") == "forecast"
                    and r.get("engine_id") == ENGINE_ID
                    and r["row_id"] not in _voided
                    and r["outcome"].get("horizon_sessions") == 21]
    ledgered_days = len({r["outcome"]["issue_date"] for r in primary_rows})
    graded_primary = sum(1 for r in rows if r.get("type") == "grade"
                         and r.get("engine_id") == ENGINE_ID
                         and any(p["row_id"] == r["forecast_row_id"]
                                 for p in primary_rows))
    _valid = mine.get("forecasts_valid", mine["forecasts"])
    if _valid != 2 * ledgered_days or ledgered_days < 1:
        return fail(f"ledger count disagreement: {_valid} valid forecasts "
                    f"for {ledgered_days} ledgered days, expected "
                    f"{2 * ledgered_days}")

    # The today narrative is computed from the freshest decision day,
    # never hardcoded: a fixed string here went stale the first time
    # the census advanced (it described 2026-10-29, fired, 0 of 1,
    # 6 days, while the block it rode in carried 2026-10-30,
    # abstained, 1 of 1, 7 days; cured 2026-10-31).
    _fd = datetime.strptime(freshest["day"], "%Y-%m-%d")
    _date_phrase = (f"{_fd.strftime('%A, %B')} {_fd.day}, {_fd.year}")
    _n_active = len(freshest["active"])
    _n_abst = len(freshest["abstained"])
    if _n_active == 1:
        _act_phrase = ("One tool that can stay silent had its rule "
                       "running that day, and it "
                       + ("stayed silent" if _n_abst else "fired")
                       + f": the silence rate is {_n_abst} of 1.")
    else:
        _act_phrase = (f"{_n_active} tools that can stay silent had "
                       f"their rules running that day, and {_n_abst} "
                       f"of them stayed silent: the silence rate is "
                       f"{_n_abst} of {_n_active}.")
    if percentile is None:
        _range_phrase = (
            f"Only {len(rates_pool)} days carry a genuine record of "
            f"who was running and who stayed silent, so the rate "
            f"cannot yet be set against its own recent range: that "
            f"comparison needs {PERCENTILE_DAYS_NEEDED} recorded days. "
            f"Until then this page records the rate and the two "
            f"chances below every day the record reaches, and both "
            f"chances are the plain overall rate, labelled as such, "
            f"not a silence reading.")
    else:
        _range_phrase = (
            f"{len(rates_pool)} days carry a genuine record of who "
            f"was running and who stayed silent, so the rate can be "
            f"set against its own recent range, as shown below.")
    today_words = (f"The freshest day the record reaches is "
                   f"{_date_phrase}. {_act_phrase} {_range_phrase}")

    data = {
        "tool": "Abstention Signal",
        "state": "proving",
        "as_of_session": decision_day,
        "record_reaches": decision_day,
        "source": ("The tools' own published records (the Router's session "
                   "record of October 16, 2026; the Board's day of October 28, "
                   "2026; the Expected Move Map through October 23, 2026; the "
                   "Second Opinion's day of October 28, 2026; the Golden Sweep "
                   "Wire's four recorded days; the Intake-Bias Reversal's "
                   "tape sessions through October 29, 2026), SPY's daily "
                   "closing prices on record (403 trading days, March 25, "
                   "2025 to October 29, 2026), and the fear gauge's daily "
                   "closes on record (23 days, September 21 to October 21, "
                   "2026)."),
        "idea": ("When the tools on this site mostly stay silent on the same "
                 "days, the next three weeks in the market tend to be rougher "
                 "than usual. That is the claim, and this page stakes a number "
                 "on it: each day the record reaches, it writes down the "
                 "chance that SPY's movement over the next 21 trading days "
                 "will be bigger than its own recent typical movement. "
                 "Beside it, every day, sits the same chance built from the "
                 "market's fear gauge alone, so the silence has to beat the "
                 "fear gauge, not just sound clever."),
        "book": {
            "version_words": ("The list of tools that can stay silent, fixed "
                              "on October 29, 2026. If the list or any test "
                              "below ever changes, the record splits into "
                              "before and after the change, and each side is "
                              "graded on its own days."),
            "can_abstain": [
                {"name": "The Router",
                 "test": ("Names a forecaster to follow only when a top-grade "
                          "forecaster matches the stock on every part of its "
                          "graded setting and has a reading for it. Otherwise "
                          "its answer is no call."),
                 "status": ("Its standing answer today is no call. On its one "
                            "recorded day, October 16, 2026, it checked 700 "
                            "names and named none to follow: a genuine "
                            "silence.")},
                {"name": "Qualified Board",
                 "test": ("Can hold back a whole check category when the "
                          "record behind that check does not cover enough of "
                          "what it grades."),
                 "status": ("On its one recorded day, October 28, 2026, it "
                            "held back the big investors' positions check "
                            "for all 50 published names because the record "
                            "behind it fell short. On this page that counts "
                            "as a record shortfall, not a silence: the check "
                            "had nothing to read.")},
                {"name": "Expected Move Map",
                 "test": "Files a map only for names its record covers.",
                 "status": ("Its newest maps end on October 23, 2026 for "
                            "SPY and October 22, 2026 for QQQ, and no map "
                            "was ever filed for the small-company fund. It "
                            "is not publishing now: an old record, not a "
                            "fresh silence.")},
                {"name": "Second Opinion",
                 "test": ("Gives no call for a name when too little is on "
                          "record for it, or when no kind of evidence "
                          "speaks for it."),
                 "status": ("On October 28, 2026 it spoke for 1,828 of "
                            "1,838 names. Ten names got no call: 5 with no "
                            "speaking kind of evidence and 5 with too "
                            "little on record. On this page those count as "
                            "names with nothing to read, not as a silence.")},
                {"name": "Golden Sweep Wire",
                 "test": "Reports only when a golden sweep print appears.",
                 "status": ("All of its recorded days, October 26 to 29, "
                            "2026, were stamped incomplete because reading "
                            "limits were hit, with no print found. Those "
                            "are faulty days: set aside and never counted "
                            "as silences.")},
                {"name": "Intake-Bias Reversal",
                 "test": ("Fires only when the most manufactured flow score "
                          "and the heaviest short selling land on the same "
                          "name on the same day."),
                 "status": ("Its rule ran on October 26, 27, 28 and 29, "
                            "2026. The combined group formed on the 26th "
                            "(in that tool's own after-the-fact study; it "
                            "was never recorded at the time), was empty on "
                            "the 27th and the 28th, and formed again on "
                            "the 29th. The empty days are genuine "
                            "silences; the formed days are not.")},
            ],
            "cannot_abstain": [
                {"name": "Morning Map",
                 "why": ("Publishes a card every recorded day. Single "
                         "readings inside it can be missing, but the map "
                         "itself never stays silent.")},
                {"name": "Breakout Scanner",
                 "why": ("Prints readings for whatever its price record "
                         "covers. It has no no-call state.")},
                {"name": "Momentum Clock",
                 "why": "Ranks every name on record, every time."},
                {"name": "Grade-A Board and The Record",
                 "why": ("Report grades on the past. Staying silent is not "
                         "one of their states.")},
            ],
        },
        "today": {
            "day": decision_day,
            "rate": freshest["rate"],
            "active": freshest["active"],
            "abstained": freshest["abstained"],
            "independent_abstainers": freshest["independent_abstainers"],
            "defect_tagged": freshest["defect_tagged_count"],
            "percentile": percentile,
            "trigger_state": trigger_state,
            "rate_days_on_record": len(rates_pool),
            "rate_days_needed": PERCENTILE_DAYS_NEEDED,
            "rates_so_far": [{"day": d["day"], "rate": d["rate"]}
                             for d in decision_days],
            "p_main": p_main, "p_control": p_control,
            "p_main_form": p_main_form, "p_control_form": p_control_form,
            "base_rate_pct": round(base_rate * 100, 1),
            "vix_close": vix_close_today,
            "vix_newest_close": round(vix_newest_close, 2),
            "vix_newest_date": vix_newest_day,
            "horizon_open": horizon_open,
            "horizon_close_21": horizon_close_21,
            "horizon_close_5": horizon_close_5,
            "words": today_words,
        },
        "decision_days": [
            {"day": d["day"], "active": d["active"],
             "abstained": d["abstained"],
             "defect_excluded": d["defect_excluded"],
             "missing_data_notes": d["missing_data_notes"],
             "rate": d["rate"],
             "independent_abstainers": d["independent_abstainers"]}
            for d in decision_days],
        "outcome_history": {
            "label": "History, not live forecasts",
            "days": len(hist21), "span_start": hist21[0]["day"],
            "span_end": hist21[-1]["day"], "exceedances": exc21,
            "base_rate_pct": round(base_rate * 100, 1),
            "panel_end_median_pct": round(panel_end_median * 100, 2),
            "latest_completed_pct": round(latest_rv21 * 100, 2),
            "secondary_days": len(hist5),
            "secondary_base_rate_pct": round(base_rate_5 * 100, 1),
            "control_fitted_days": len(vix_fitted),
            "words": (f"Worked out day by day over SPY's price history on "
                      f"record: on {len(hist21)} past days both the recent "
                      f"typical movement and the following 21 days' "
                      f"movement can be measured, and on {exc21} of them "
                      f"({round(base_rate * 100, 1)}%) the following "
                      f"movement was the bigger one. (The first 294 of "
                      f"those days are the registered study prefix, with "
                      f"124 exceedances; later days are new history the "
                      f"extended panel adds.) That rate is the plain "
                      f"overall rate both of today's chances start from. "
                      f"The fear gauge alone could be fitted on only "
                      f"{len(vix_fitted)} of those days (its record on "
                      f"file is 23 days long and ends on October 21, "
                      f"2026), and on the first 4 the following movement "
                      f"was not the bigger one: far too few to build a "
                      f"fear-gauge-only chance from, which is why the "
                      f"control also starts at the plain rate and is "
                      f"marked as thin until 30 fitted days exist."),
        },
        "live": {
            "days_recorded": ledgered_days,
            # Valid basis (terminal audit, 2026-10-31): the
            # published count is the valid record; voided
            # duplicate re-issues stay on the ledger and are
            # named in forecasts_voided, never counted as
            # standing forecasts (the defect 8 rule).
            "forecasts_recorded": mine.get("forecasts_valid",
                                           mine["forecasts"]),
            "forecasts_voided": mine.get("forecasts_voided", 0),
            "forecasts_graded": mine["graded"],
            "graded_primary": graded_primary,
            "counted_toward_80": graded_primary,
            "target": KILL_TARGET,
            "words": ("Every chance is written down before its three weeks "
                      "open, and graded when they close. A day counts "
                      "toward the 80 that decide this tool only when its "
                      "21 trading days can be measured from the price "
                      "record. The three-week windows overlap each other, "
                      "and they are counted as the days they were written "
                      "on, with the overlap stated rather than hidden."),
        },
        "grading_words": ("Grading compares three scores on the same days: "
                          "this page's silence chance, the fear-gauge-only "
                          "chance, and the plain overall rate. A split of "
                          "the record, before and after any change to the "
                          "list of tools above or to any test, is graded "
                          "on its own days."),
        "kill_criterion": ("After 80 graded days, if the silence chance "
                           "scores no better than the fear-gauge-only "
                           "chance, this tool retires, and its lesson "
                           "stands on the page: a suite's silence adds "
                           "nothing beyond the market's own fear gauge."),
        "thin_cell_rule": ("Thin record rule: any part of the record with "
                           "fewer than 30 graded days is shown as a count, "
                           "never as a score. A handful of days proves "
                           "nothing here, in either direction."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: decision record through {decision_day} "
          f"({len(decision_days)} decision days, freshest rate "
          f"{freshest['rate']:.2f} from {freshest['independent_abstainers']} "
          f"independent abstainer); {mine.get('forecasts_valid', mine['forecasts'])} recorded forecasts "
          f"({created} new, {newly_graded} newly graded), "
          f"{graded_primary} of {KILL_TARGET} graded days counted")
    return 0


if __name__ == "__main__":
    sys.exit(build())
