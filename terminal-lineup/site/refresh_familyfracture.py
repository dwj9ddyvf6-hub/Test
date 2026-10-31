#!/usr/bin/env python3
"""Refresh the Family Fracture forecaster (Forecast Engine 17).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - The disagreement between independent kinds of evidence is the
     signal; agreement is never the signal and no direction is ever
     forecast. The target (how wide a 5-session move is) belongs to
     the one target class the corpus validates: movement size, not
     direction. The benchmark this engine must beat is the plain
     forecast from recent movement alone (the HAR construction of
     Engine 1, grade A in the corpus record): deliberately a hard
     bar. No corpus study measures disagreement between evidence
     families directly; the mechanism is plausible and untested,
     which is the point of recording it forward.
   - This engine's own live record: none before today.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - Voting families: exactly four, one vote each, taken from the
     family registry's input list for this engine: price,
     options prints, modelled inventory, and filings/positioning.
     The recent-movement (volatility) family is NOT a voter: it is
     the benchmark and the base, and counting it as a vote would
     make the signal partly its own benchmark. Independently, the
     volatility pages on record hold no SPY or QQQ reading at all,
     so a volatility vote is impossible today.
   - Signed votes: +1 positive, 0 mixed (a PRESENT reading that is
     neither positive nor cautious; it counts as speaking), -1
     cautious. An absent family casts NO vote; absence is never
     written as a zero vote. Stance rules are the sister tool
     Second Opinion's verbatim rules:
       price (the scored trading day record): +1 if the name passed
         every check; 0 if its score is 60 or more and it did not
         pass every check; -1 if its score is below 60.
       options prints (the tape record): the sign of the day's net
         premium: +1 above zero, -1 below zero, 0 exactly zero.
         Side labels carry the declared latest-quote limitation.
       modelled inventory (the morning map record): -1 if the price
         stands below the flip level AND the net positioning figure
         is negative; +1 if the price stands at or above the flip
         AND the figure is zero or positive; otherwise 0.
       filings/positioning: NO signed per-index reading exists on
         record. The filings bundle covers 50 company names and
         neither index fund is among them; the insider record
         likewise carries neither fund. The family's last reading
         on record is the quarterly holdings report aggregate
         (period ended 2026-06-30, 8,857 holders), which publishes
         no per-index signed figure. So this family is CARRIED as
         context with its age printed and its vote is ABSENT on
         every session. It is never given a stand-in vote.
   - Sessions: a forecast for the morning of day T may use only
     readings published before that morning. Per producer session,
     the LAST full run in the permanent log is the record (an early
     partial run is superseded). The scored-day record keeps only
     its freshest run as a file; its earlier runs are overwritten
     and the permanent log's published rows never contain SPY or
     QQQ, so price votes for earlier decision mornings are
     UNRECOVERABLE and are recorded absent, never reconstructed.
     The joint sessions that exist are exactly three decision
     mornings: 2026-10-27 and 2026-10-28 (prints and inventory
     speaking) and 2026-10-29 (price, prints and inventory
     speaking; the only full session, and the freshest). History
     is exactly those three, labelled, never padded. No longer
     joint record exists on disk, so there is nothing honest to
     fit on: the construction below is a fixed mapping registered
     here before computing, stated as this design's own
     construction, not fitted to any outcome.
   - Issue rule: at least 2 speaking families are required, else
     no forecast is issued for that index that morning (recorded
     as a no-data absence).
   - Disagreement shapes, tested in this order:
       G0 ALIGNED: every speaking family's sign is the same and
         not zero.
       G1 LEVERAGED-CONSENSUS: price and prints agree on a
         non-zero sign and modelled inventory opposes them (the
         design's named example of a leveraged-consensus state).
       G2 PRINTS-ISOLATED: prints opposes price and inventory,
         which agree on a non-zero sign.
       G4 OTHER-SPLIT: any other opposition among speaking
         families.
       G3 MIXED-CONTAINING: no opposition, but at least one
         speaking family is mixed (0). Residual class.
     (Class labels keep their G-numbers; the test order is G0,
     G1, G2, G4, then G3 as the residual.)
   - Fracture multiplier per shape (fixed, this design's own, not
     fitted): G0 x1.00, G3 x1.10, G2 x1.20, G4 x1.20, G1 x1.35.
   - Recent-movement base (Engine 1's construction REUSED, never
     forked): the equal-weight mean of the 1, 5 and 22-session
     squared-log-return components from the price history on
     record, annualised with sqrt(252); the 5-session expected
     move (1 EM) is that figure times sqrt(5/252) times 0.88.
     The script recomputes it from the price history and checks
     it against Engine 1's published bands for the same as-of
     close (SPY 1.1753 percent, QQQ 2.1094 percent at 5 sessions,
     as of 2026-10-23), failing closed on any disagreement.
   - Range base: the full expected-move band width (2 x 1 EM)
     times 0.91, the driftless-walk constant: the expected
     high-to-low range divided by the close-to-close full width
     is sqrt(8/pi) / (2 x 0.88), about 0.91. A theory constant,
     not fitted. Fracture range forecast = range base x shape
     multiplier x dispersion factor. The benchmark (plain
     recent-movement only) range forecast = range base x 1.00,
     recorded the same day under its own marker, same grading.
   - Breach chance: the base chance that the absolute 5-session
     return exceeds 1 EM is 2 x (1 - Phi(0.88)) = 0.3789 under a
     driftless normal walk (1 EM is 0.88 of the 5-session standard
     movement by construction). Fracture breach chance = that
     base chance times the shape multiplier, held inside 0.01 to
     0.99. Benchmark breach chance = the base chance, recorded
     the same day under its own marker.
   - Dispersion of family track records: the second registered
     input is the spread (population standard deviation) of the
     speaking families' recent success rates, entering as a
     factor of 1 + 0.15 x that spread. NO family-level success
     rate exists at the 5-session horizon for any family today:
     the scored-day record is graded at 1 session only (its
     5-session count is 0), the map record holds 6 graded
     one-session level tests, the tape record holds no graded
     record, and the filings family holds none. So the spread is
     ABSENT today, the factor is exactly 1.00, and the page says
     the signal is shape-only in its current state. Any future
     rate built on fewer than 30 graded cases is counts only.
   - Grading: at 5 sessions, the realised range is (highest high
     minus lowest low over the 5 horizon sessions) divided by the
     base close, as a percent; range error is the absolute
     difference between forecast and realised, for this engine
     and for the plain benchmark on identical days. The breach
     chance is graded for calibration on the same days (whether
     the absolute return at the horizon close exceeded 1 EM).
     Known grading note, stated like the earlier engines stated
     theirs: the shared grading runner has no multi-session
     range outcome kind yet, so the range leg grades when the
     runner is next extended; and no row can mature until the
     price history on record extends past its horizon (that
     history ends 2026-10-23, before every joint session).
   - Only the freshest decision morning is recorded in advance;
     the two earlier joint mornings are shown as labelled history
     and record nothing (a forecast written after its window
     opened would break the record-before-the-window law).

3. NON-CLAIMS
   - No direction is forecast, ever. The count of agreeing
     families is never the signal. No family's absence is filled
     with a zero, a stand-in, or another family's reading. The
     fixed multipliers are this design's own construction, not
     measured effects. Nothing is claimed beyond SPY and QQQ.

=====================================================================
Behaviour: cross-checks the tape card file and the map card file
against the permanent log's freshest full runs, the scored-day
file's index rows, and the recomputed recent-movement base against
Engine 1's published bands, failing closed on any disagreement;
builds the vote pattern for every joint session on record; appends
the freshest morning's forecasts (this engine's and the plain
benchmark's, under separate markers) through the forecast
machinery API only; writes data.json. All timestamps come from
the sources, never the clock, so reruns are idempotent.

Usage: python3 refresh_familyfracture.py
"""

import json
import math
import os
import sys
from datetime import date, timedelta
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
MORGUE = os.path.expanduser("~/workspace/morgue")
LOG_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
TAPE_CARD_PATH = os.path.join(MORGUE, "output", "tape_card.json")
MAP_CARD_PATH = os.path.join(MORGUE, "output", "map_card.json")
BOARD_PATH = os.path.join(MORGUE, "output", "board_full.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
BANDS_PATH = os.path.join(HERE, "corrected-band", "data.json")
FILINGS_PATH = os.path.join(HERE, "13f-tracker", "data.json")
SECOND_OPINION_PATH = os.path.join(HERE, "second-opinion", "data.json")
OUT_PATH = os.path.join(HERE, "family-fracture", "data.json")
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


_forecast_ledger = _load("forecast_ledger_mod",
                         os.path.join(LINEUP, "forecast", "ledger.py"))
_forecast_registry = _load("forecast_registry_mod",
                           os.path.join(LINEUP, "forecast", "registry.py"))
Ledger = _forecast_ledger.Ledger
file_sha256 = _forecast_ledger.file_sha256
Registry = _forecast_registry.Registry

ENGINE_ID = "engine_17"
SYMBOLS = ("SPY", "QQQ")
PLAIN_NAME = {"SPY": "SPY (the big S&P 500 fund)",
              "QQQ": "QQQ (the big Nasdaq-100 fund)"}
K5 = 0.88
RANGE_FACTOR = 0.91
MULTIPLIER = {"G0": 1.00, "G3": 1.10, "G2": 1.20, "G4": 1.20,
              "G1": 1.35}
SHAPE_WORDS = {
    "G0": ("All speaking families point the same way",
           "aligned"),
    "G1": ("Price and options trading agree, and modelled "
           "positioning leans the other way",
           "leveraged consensus"),
    "G2": ("Options trading stands alone against price and "
           "modelled positioning",
           "options trading isolated"),
    "G4": ("The speaking families are split, in a pattern that "
           "is none of the named shapes",
           "another split"),
    "G3": ("No family opposes another, but at least one speaking "
           "family is mixed",
           "mixed, no opposition"),
}
FAMILY_WORDS = {"price": "Price and trading history",
                "prints": "Options trading",
                "inventory": "Modelled positioning",
                "filings": "Filings and big holders"}
VOTE_WORDS = {1: "positive", 0: "mixed", -1: "cautious"}
P0 = 2.0 * (1.0 - NormalDist().cdf(K5))
TARGET_SESSIONS = 100
THIN = 30

SOURCE_WORDS = ("The scored trading day record, the daily options "
                "trading record and the morning positioning record "
                "for SPY and QQQ, plus the quarterly holdings "
                "report carried as context")


def fail(message):
    print(f"Family Fracture refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def weekdays_from(start_iso, count):
    """`count` weekdays starting at start_iso (inclusive)."""
    d = date.fromisoformat(start_iso)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def next_weekday(after_iso):
    d = date.fromisoformat(after_iso) + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def price_vote(row):
    if row["qualified"]:
        return 1
    if row["score"] >= 60:
        return 0
    return -1


def prints_vote(net_premium):
    if net_premium > 0:
        return 1
    if net_premium < 0:
        return -1
    return 0


def inventory_vote(spot, flip, net_gex):
    if spot < flip and net_gex < 0:
        return -1
    if spot >= flip and net_gex >= 0:
        return 1
    return 0


def classify(votes):
    """votes: {family: sign} for speaking families only.
    Returns the shape id under the registered test order."""
    signs = list(votes.values())
    if signs and all(s == signs[0] for s in signs) and signs[0] != 0:
        return "G0"
    price = votes.get("price")
    prints = votes.get("prints")
    inventory = votes.get("inventory")
    if price is not None and prints is not None and \
            inventory is not None and price == prints != 0 and \
            inventory == -price:
        return "G1"
    if price is not None and prints is not None and \
            inventory is not None and price == inventory != 0 and \
            prints == -price:
        return "G2"
    nonzero = [s for s in signs if s != 0]
    if 1 in nonzero and -1 in nonzero:
        return "G4"
    return "G3"


def har_annualised(sq_returns, i):
    """Engine 1's construction, reused verbatim: equal-weight mean
    of the 1, 5 and 22-session squared-log-return components."""
    daily = sq_returns[i - 1]
    weekly = sum(sq_returns[i - 5:i]) / 5.0
    monthly = sum(sq_returns[i - 22:i]) / 22
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


def band_widen(bands):
    """The widening Engine 1 applies to its published bands: its
    session-quality guard's factor when the guard reports
    deterioration, else 1.0 (the same condition refresh_
    correctedband uses). Family Fracture's own recent-movement
    base stays the raw recomputation; only the cross-check
    against the published band compares widened figures
    (engine refresh cure, 2026-10-30)."""
    guard = (bands.get("live") or {}).get("session_quality_guard")
    if guard is not None and guard.get("deterioration") is not None:
        return guard["band_widen_factor"]
    return 1.0


def positioning_card_session(map_card, map_runs, symbols):
    """The session the positioning card file represents, or None
    when it agrees with no permanent log run.

    Session based agreement (cure FAMILY-CARD-SESSION-20261031):
    the card is built by the morgue positioning producer on its
    own cadence, which includes mornings with no matching tape
    run (a Saturday rebuild for the session it just ran). The old
    check required the card's build date to equal the freshest
    positioning day on or before the freshest tape day, so any
    card built on a later calendar day failed closed even when
    its readings matched the log run for its own session exactly.
    The agreement that matters is readings, per symbol, against
    the log run for the session the card represents: the freshest
    positioning run on or before the card's build date."""
    built_day = (map_card.get("built_utc") or "")[:10]
    candidates = [d for d in map_runs if d <= built_day]
    if not candidates:
        return None
    day = max(candidates)
    if not set(symbols) <= set(map_runs[day]):
        return None
    mc_by_sym = {c["underlying"]: c for c in map_card["cards"]}
    for sym in symbols:
        if sym not in mc_by_sym:
            return None
        _ts, r = map_runs[day][sym]
        c = mc_by_sym[sym]
        if c["spot"] != r["spot"] or \
                c["zero_gamma"] != r["zero_gamma"] or \
                c["net_gex_usd_per_1pct"] != r["net_gex_usd_per_1pct"]:
            return None
    return day


def build():
    for path in (LOG_PATH, TAPE_CARD_PATH, MAP_CARD_PATH, BOARD_PATH,
                 PANEL_PATH, BANDS_PATH, FILINGS_PATH,
                 SECOND_OPINION_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    tape_card = load_json(TAPE_CARD_PATH)
    map_card = load_json(MAP_CARD_PATH)
    board = load_json(BOARD_PATH)
    panel = load_json(PANEL_PATH)
    bands = load_json(BANDS_PATH)
    filings_doc = load_json(FILINGS_PATH)
    second_opinion = load_json(SECOND_OPINION_PATH)

    # ---- Producer sessions: last full run per session date ----
    tape_runs = {}
    for r in log_rows:
        if r.get("component") == "tape-aggregate":
            v = r["value"]
            tape_runs.setdefault(r["ts_utc"][:10], {})[v["underlying"]] = (
                r["ts_utc"], v)
    map_runs = {}
    for r in log_rows:
        if r.get("component") == "gex_static_v1":
            map_runs.setdefault(r["ts_utc"][:10], {})[r["underlying"]] = (
                r["ts_utc"], r)
    tape_days = sorted(tape_runs)
    if not tape_days:
        return fail("the permanent log holds no options trading runs")
    for day in tape_days:
        if not set(SYMBOLS) <= set(tape_runs[day]):
            return fail(f"options trading session {day} does not "
                        f"carry both index funds")
        prior_maps = [d for d in map_runs if d <= day]
        if not prior_maps:
            return fail(f"no positioning run on or before {day}")
        mday = max(prior_maps)
        if not set(SYMBOLS) <= set(map_runs[mday]):
            return fail(f"positioning session {mday} does not carry "
                        f"both index funds")
    freshest_day = tape_days[-1]

    # ---- Card files must agree with the freshest full runs ----
    card_by_sym = {c["underlying"]: c for c in tape_card["cards"]}
    for sym in SYMBOLS:
        ts, v = tape_runs[freshest_day][sym]
        if card_by_sym[sym]["net_premium"] != v["net_premium"]:
            return fail(f"the options trading card file's {sym} net "
                        f"figure disagrees with the permanent log's "
                        f"freshest run")
    map_day_fresh = max(d for d in map_runs if d <= freshest_day)
    # Session based card agreement (FAMILY-CARD-SESSION-20261031):
    # the card must match the log run for the session it
    # represents (see positioning_card_session), and that session
    # must not predate the freshest tape aligned positioning run,
    # so a stale card still fails closed.
    card_day = positioning_card_session(map_card, map_runs, SYMBOLS)
    if card_day is None:
        return fail("the positioning card file's readings disagree "
                    "with the permanent log run for the session "
                    "the card represents")
    if card_day < map_day_fresh:
        return fail("the positioning card file is older than the "
                    "permanent log's freshest positioning run")

    # ---- Scored-day (price) votes: freshest run only ----
    board_rows = {r["symbol"]: r for r in board["rows"]}
    for sym in SYMBOLS:
        if sym not in board_rows:
            return fail(f"the scored-day record holds no {sym} row")
    board_as_of = board["as_of_session"]
    board_published = second_opinion["board_published_at_utc"][:10]
    if second_opinion.get("filings_as_of") is None:
        return fail("the sister record holds no filings date")
    # The run that produced the scored-day file was published on
    # board_published; the first morning that may use it is the
    # next weekday after that publication date.
    price_decision_day = next_weekday(board_published)

    # ---- Recent-movement base, checked against Engine 1 ----
    panel_last = panel["SPY"][-1][0]
    base_info = {}
    band_by_sym = {n["symbol"]: n for n in bands["live"]["names"]}
    for sym in SYMBOLS:
        rows = panel[sym]
        # Panel length is the panel's own (cure G2, 2026-10-29: the
        # panel advances daily past its original 399 sessions); the
        # binding is that every name shares SPY's length and last
        # session, not a frozen session count.
        if len(rows) != len(panel["SPY"]) or rows[-1][0] != panel_last:
            return fail(f"price history disagreement for {sym}")
        closes = [float(r[4]) for r in rows]
        rets = [math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))]
        sq = [r * r for r in rets]
        vol = har_annualised(sq, len(closes) - 1)
        em_pct = vol * math.sqrt(5 / 252.0) * K5 * 100.0
        published = None
        for hz in band_by_sym[sym]["horizons"]:
            if hz["sessions"] == 5:
                for b in hz["bands"]:
                    if b["level"] == 68:
                        published = b["half_pct"]
        if published is None or round(em_pct * band_widen(bands), 4) != published:
            return fail(f"the recomputed expected move for {sym} "
                        f"({round(em_pct, 4)}) disagrees with the "
                        f"published band figure ({published}); "
                        f"refusing to publish")
        base_info[sym] = {
            "recent_movement_pct": round(vol * 100.0, 2),
            "expected_move_pct": round(em_pct, 4),
            "range_base_pct": round(2.0 * em_pct * RANGE_FACTOR, 4),
            "base_close": closes[-1],
            "base_close_date": panel_last,
        }

    # ---- Filings family: carried reading, vote absent ----
    filings_period = filings_doc["current_period"]
    filings_holders = filings_doc["holders_on_record"]
    filings_prior_period = filings_doc["prior_period"]
    filings_prior_holders = filings_doc["prior_holders_on_record"]

    # ---- Vote patterns for every joint session on record ----
    sessions = []
    for day in tape_days:
        decision = next_weekday(day)
        mday = max(d for d in map_runs if d <= day)
        per_symbol = {}
        for sym in SYMBOLS:
            votes = {}
            detail = {}
            _tts, tv = tape_runs[day][sym]
            votes["prints"] = prints_vote(tv["net_premium"])
            detail["prints"] = {
                "net_premium": tv["net_premium"],
                "reading_date": day,
            }
            _mts, mr = map_runs[mday][sym]
            votes["inventory"] = inventory_vote(
                mr["spot"], mr["zero_gamma"],
                mr["net_gex_usd_per_1pct"])
            detail["inventory"] = {
                "spot": mr["spot"], "flip": mr["zero_gamma"],
                "net_positioning": mr["net_gex_usd_per_1pct"],
                "reading_date": mday,
            }
            if decision == price_decision_day:
                brow = board_rows[sym]
                votes["price"] = price_vote(brow)
                detail["price"] = {
                    "score": brow["score"],
                    "passed_every_check": brow["qualified"],
                    "checks_in_favour": brow["confirming"],
                    "reading_date": board_as_of,
                }
            shape = classify(votes) if len(votes) >= 2 else None
            per_symbol[sym] = {"votes": votes, "detail": detail,
                               "shape": shape}
        age = (date.fromisoformat(decision) -
               date.fromisoformat(filings_period)).days
        sessions.append({"readings_through": day,
                         "decision": decision,
                         "filings_age_days": age,
                         "symbols": per_symbol})
    today = sessions[-1]
    # Cure G17, 2026-10-29: the original equality demanded the
    # freshest tape decision morning be exactly the first morning
    # the scored-day record may be used. Once the tape lane advances
    # past the board's publication, that equality fails closed on a
    # coherent record forever. The law that matters is the
    # no-lookahead direction: the freshest decision morning must
    # not precede the first usable morning for the scored record.
    # The price vote still attaches only to its own decision day in
    # the session construction above.
    if today["decision"] < price_decision_day:
        return fail("the freshest decision morning precedes the "
                    "first morning the scored-day record may be "
                    "used on; the session construction needs "
                    "re-checking")
    for sym in SYMBOLS:
        if today["symbols"][sym]["shape"] is None:
            return fail(f"fewer than 2 families speak for {sym} on "
                        f"the freshest morning; no forecast may be "
                        f"issued")

    # ---- Today's forecasts ----
    horizon = weekdays_from(today["decision"], 5)
    horizon_open, horizon_close = horizon[0], horizon[-1]
    today_out = {}
    for sym in SYMBOLS:
        entry = today["symbols"][sym]
        shape = entry["shape"]
        mult = MULTIPLIER[shape]
        base = base_info[sym]
        fracture_range = round(base["range_base_pct"] * mult, 4)
        fracture_breach = round(min(max(P0 * mult, 0.01), 0.99), 4)
        vote_rows = []
        for fam in ("price", "prints", "inventory", "filings"):
            if fam == "filings":
                vote_rows.append({
                    "family": fam, "family_name": FAMILY_WORDS[fam],
                    "state": "absent",
                    "vote": None, "vote_word": "no reading",
                    "detail": ("No signed reading for this fund "
                               "exists. The family's last reading "
                               "is the quarterly holdings report "
                               f"for the period ended "
                               f"{filings_period}, carried below "
                               f"with its age. It casts no vote."),
                })
                continue
            if fam not in entry["votes"]:
                vote_rows.append({
                    "family": fam, "family_name": FAMILY_WORDS[fam],
                    "state": "absent", "vote": None,
                    "vote_word": "no reading",
                    "detail": ("No reading for this morning is on "
                               "record; earlier readings were not "
                               "kept, so none is reconstructed."),
                })
                continue
            d = entry["detail"][fam]
            if fam == "price":
                detail = (f"Score {d['score']} out of 100 on the "
                          f"scored day of {d['reading_date']}, "
                          f"{d['checks_in_favour']} of 8 checks in "
                          f"favour, "
                          + ("passed every check."
                             if d["passed_every_check"] else
                             "did not pass every check."))
            elif fam == "prints":
                detail = (f"Net money in the day's options trades "
                          f"was {money(d['net_premium'])} on "
                          f"{d['reading_date']}.")
            else:
                detail = (f"Price {d['spot']:,.2f} against a flip "
                          f"level of {d['flip']:,.2f}, with a net "
                          f"positioning figure of "
                          f"{money(d['net_positioning'])} on "
                          f"{d['reading_date']}.")
            vote_rows.append({
                "family": fam, "family_name": FAMILY_WORDS[fam],
                "state": "speaking",
                "vote": entry["votes"][fam],
                "vote_word": VOTE_WORDS[entry["votes"][fam]],
                "detail": detail,
            })
        today_out[sym] = {
            "symbol": sym, "name": PLAIN_NAME[sym],
            "votes": vote_rows,
            "families_speaking": len(entry["votes"]),
            "shape": shape,
            "shape_words": SHAPE_WORDS[shape][0],
            "shape_label": SHAPE_WORDS[shape][1],
            "multiplier": mult,
            "expected_move_pct": base["expected_move_pct"],
            "range_base_pct": base["range_base_pct"],
            "fracture_range_pct": fracture_range,
            "benchmark_range_pct": base["range_base_pct"],
            "fracture_breach_pct": round(fracture_breach * 100, 2),
            "benchmark_breach_pct": round(P0 * 100, 2),
        }

    # ---- Record the freshest morning, machinery API only ----
    registry = Registry()
    ledger = Ledger(os.path.join(LINEUP, "forecast", "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    fresh_tape_ts = tape_runs[freshest_day]["SPY"][0]
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (LOG_PATH, TAPE_CARD_PATH, MAP_CARD_PATH,
                      BOARD_PATH, PANEL_PATH, BANDS_PATH,
                      FILINGS_PATH)],
        "note": ("Freshest decision morning's disagreement shape "
                 "per index fund, with the plain recent-movement "
                 "forecast recorded the same day under its own "
                 "marker. The filings family is absent on every "
                 "row: it has no signed reading for either fund."),
        "clocks": {
            "event_time": fresh_tape_ts,
            "publication_time": tape_card["generated_at_utc"],
            "first_available_time": fresh_tape_ts,
            "ingestion_time": tape_card["generated_at_utc"],
            "decision_as_of": today["decision"],
        },
    }
    speaking_families = {
        "price": "price", "prints": "options_prints",
        "inventory": "modelled_inventory",
    }
    created_total = 0
    for sym in SYMBOLS:
        entry = today["symbols"][sym]
        fams = [speaking_families[f] for f in entry["votes"]]
        out_range = {"symbol": sym, "kind": "realised_range_5s",
                     "base_date": today["readings_through"],
                     "at_date": horizon_close,
                     "window_open": horizon_open,
                     "window_close": horizon_close}
        out_breach = {"symbol": sym, "kind": "abs_return",
                      "base_date": today["readings_through"],
                      "at_date": horizon_close}
        specs = [
            ("Predicted 5-session realised range, as a percent of "
             "price, from the disagreement pattern",
             {"estimate": today_out[sym]["fracture_range_pct"],
              "cell": "fracture_range",
              "shape": entry["shape"],
              "multiplier": MULTIPLIER[entry["shape"]],
              "dispersion_factor": 1.0,
              "absent_families": ["filings_positioning"]},
             out_range),
            ("Benchmark: predicted 5-session realised range, as a "
             "percent of price, from recent movement alone",
             {"estimate": today_out[sym]["benchmark_range_pct"],
              "cell": "benchmark_range",
              "absent_families": ["filings_positioning"]},
             out_range),
            ("Chance the absolute 5-session return exceeds 1 "
             "expected move, from the disagreement pattern",
             {"p": round(today_out[sym]["fracture_breach_pct"] / 100.0, 4),
              "estimate": round(today_out[sym]["fracture_breach_pct"] / 100.0, 4),
              "cell": "fracture_breach",
              "shape": entry["shape"],
              "multiplier": MULTIPLIER[entry["shape"]],
              "absent_families": ["filings_positioning"]},
             out_breach),
            ("Benchmark: chance the absolute 5-session return "
             "exceeds 1 expected move, from recent movement alone",
             {"p": round(P0, 4), "estimate": round(P0, 4),
              "cell": "benchmark_breach",
              "absent_families": ["filings_positioning"]},
             out_breach),
        ]
        for quantity, value, outcome in specs:
            _row, created = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=fresh_tape_ts,
                subject=sym, quantity=quantity, value=value,
                horizon_open=horizon_open,
                horizon_close=horizon_close, lineage=lineage,
                families=fams, outcome=outcome)
            created_total += int(created)
    if not ledger.verify_chain():
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    recorded = graded = 0
    decision_days = set()
    for row in ledger.rows():
        if row.get("engine_id") != ENGINE_ID:
            continue
        if row.get("type") == "forecast":
            recorded += 1
            decision_days.add(row["lineage"]["clocks"]
                              ["decision_as_of"])
        if row.get("type") == "grade":
            graded += 1

    # ---- History rows (labelled, record nothing) ----
    history_out = []
    for sess in sessions[:-1]:
        syms = {}
        for sym in SYMBOLS:
            e = sess["symbols"][sym]
            syms[sym] = {
                "votes": [
                    {"family_name": FAMILY_WORDS[f],
                     "vote_word": VOTE_WORDS[v]}
                    for f, v in e["votes"].items()],
                "families_speaking": len(e["votes"]),
                "shape_label": (SHAPE_WORDS[e["shape"]][1]
                                if e["shape"] else None),
                "multiplier": (MULTIPLIER[e["shape"]]
                               if e["shape"] else None),
            }
        history_out.append({
            "decision": sess["decision"],
            "readings_through": sess["readings_through"],
            "filings_age_days": sess["filings_age_days"],
            "symbols": syms,
        })

    data = {
        "tool": "Family Fracture",
        "state": "proving",
        "source": SOURCE_WORDS,
        "decision_date": today["decision"],
        "readings_through": today["readings_through"],
        "horizon_open": horizon_open,
        "horizon_close": horizon_close,
        "panel_last_session": panel_last,
        "today": [today_out[s] for s in SYMBOLS],
        "filings_carried": {
            "period": filings_period,
            "holders": filings_holders,
            "prior_period": filings_prior_period,
            "prior_holders": filings_prior_holders,
            "age_days": today["filings_age_days"],
            "words": (f"The last filings reading on record is the "
                      f"quarterly holdings report for the period "
                      f"ended {filings_period}: {filings_holders:,} "
                      f"holders filed, against "
                      f"{filings_prior_holders:,} for the period "
                      f"ended {filings_prior_period}. It names no "
                      f"reading for either fund, so it is carried "
                      f"here as background, {today['filings_age_days']} "
                      f"days old on the morning of this forecast, "
                      f"and it casts no vote."),
        },
        "dispersion": {
            "state": "not yet available",
            "factor": 1.0,
            "words": ("One part of the design is not in place yet: "
                      "how much the families' recent success rates "
                      "disagree with each other. No family has a "
                      "graded record at the 5 trading day stretch "
                      "to measure that from, so today the forecast "
                      "rests on the disagreement shape alone, and "
                      "the missing part changes nothing in the "
                      "numbers above."),
        },
        "construction": {
            "words": ("The adjustment for each shape was written "
                      "down in advance and is fixed, not fitted to "
                      "past outcomes: only three mornings of joint "
                      "readings exist, which is far too few to fit "
                      "anything honestly."),
            "rows": [
                {"shape": SHAPE_WORDS[k][1], "multiplier": v}
                for k, v in (("G0", 1.00), ("G3", 1.10),
                             ("G2", 1.20), ("G4", 1.20),
                             ("G1", 1.35))],
            "base_words": ("The starting point for both forecasts "
                           "is the plain movement forecast: how "
                           "wide a move recent movement alone "
                           "suggests over the next 5 trading days. "
                           "The plain forecast stops there. This "
                           "one widens that starting point by the "
                           "shape's fixed adjustment, and widens "
                           "the big-move chance the same way."),
        },
        "history": {
            "label": "History: the mornings on record, worked out "
                     "after the fact and recorded nowhere in "
                     "advance",
            "sessions": history_out,
            "sessions_on_record": len(sessions),
            "outcomes_note": (f"No outcome is graded yet for any "
                              f"of these mornings: the price "
                              f"history on record ends {panel_last}, "
                              f"before every morning above, so the "
                              f"5 trading days after each one are "
                              f"not on record yet. When they are, "
                              f"each morning's range miss will be "
                              f"shown beside the plain forecast's "
                              f"miss on the same days."),
        },
        "live": {"forecasts_recorded": recorded,
                 "forecasts_graded": graded,
                 "sessions_recorded": len(decision_days),
                 "target_sessions": TARGET_SESSIONS},
        "kill_criterion": (
            "After 100 mornings with a recorded forecast, this "
            "tool is retired if its range misses are not smaller "
            "than the plain movement forecast's misses on the same "
            "days. That head-to-head comparison, stated here in "
            "advance, is the test it has to pass."),
        "thin_rule": ("Below 30 graded, counts only: no percentage "
                      "and no score is drawn from a handful of "
                      "tests."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: decision morning {today['decision']} "
          f"(readings through {today['readings_through']}), "
          f"{created_total} new forecasts, {recorded} recorded in "
          f"total; shapes: "
          + ", ".join(f"{s} {today['symbols'][s]['shape']}"
                      for s in SYMBOLS))
    return 0


if __name__ == "__main__":
    sys.exit(build())
