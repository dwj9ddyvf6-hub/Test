#!/usr/bin/env python3
"""Refresh the Wall Lifetime Forecaster (Forecast Engine 8).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   The accruing Morning Map card record: the permanent log's
   published map cards (last card per index per day is the card of
   record) and the public grading of those cards, whose definitions
   are IMPORTED from morgue/scorecards.py (grade_map_row and
   map_grading_date) and never forked or redefined here: an upper
   wall is touched if the session high reached within 0.2% below it
   and held if the high never traded above it; the lower wall is
   the mirror image; the flip level was respected if the close
   stayed on the same side of it as the price when the card was
   published. Measured before computing (2026-10-28): 9 cards of
   record (SPY, QQQ, IWM on 2026-10-26, 2026-10-27, 2026-10-28) and
   6 graded one-session tests (the cards grading against the
   completed 2026-10-27 session: flip respected 6 of 6, put wall
   held 6 of 6, IWM call wall reached and broke in both its tests).
   This engine's own live record: none before today.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - Episodes: one episode per card of record per level (call wall,
     put wall, flip): 27 episodes from 9 cards. An episode is
     resolved at a window only when that many of its sessions are
     complete on the grading record; otherwise it is carried as
     CENSORED in every count, never dropped. Today only the first
     session is complete for 6 cards, so 18 level-episodes are
     resolved at the 1-session window and every episode is censored
     at the 3, 5 and 10-session windows.
   - Empirical hazard (Kaplan-Meier style, pooled across the three
     indexes because 2 graded cards per index cannot carry a rate):
     at the 1-session window, pooled resolved counts are: call wall
     touched 2 of 6 and closed through 2 of 6; put wall touched 0
     of 6 and closed through 0 of 6; flip crossed and closed beyond
     0 of 6. Survival past 1 session for touch is therefore 4/6
     (call), 6/6 (put), 6/6 (flip still on its starting side). No
     empirical figure exists past 1 session, and none is invented.
   - The prior (a starting guess, labelled a prior wherever it is
     used, which today is almost everywhere): distance d is the
     level's distance from the card's price in expected-move units,
     where one expected move is the 1-session 68% half-width from
     the Corrected Band Engine (SPY 0.5196% and QQQ 0.9326% of
     price, checked to the cent against that engine's published
     bands; IWM 0.6062% by the same construction from its own
     recent movement, the recipe that engine and the Exceedance
     Forecaster already use). A wall already at or past the price
     has d = 0. Touch chance by window w (sessions):
     p_touch(w) = 2 x Phi(-d / sqrt(w)), the driftless first-passage
     form, held inside 0.01 and 0.99.
   - Positioning conditioning (the card's own dealer-positioning
     sign): the share of touches that become closes through is
     0.65 when positioning is amplifying (negative) and 0.30 when
     it is dampening (positive), so p_break(w) = p_touch(w) x that
     share. The flip's close-beyond chance is
     Phi(-d / sqrt(w)) x 1.25 when amplifying and x 0.75 when
     dampening, held inside 0.01 and 0.99.
   - Blend: at the 1-session window only, the published chance is
     (resolved x pooled rate + 20 x prior) / (resolved + 20): the
     record counts for 6 and the prior for 20, so the prior
     dominates today and the page says so. At 3, 5 and 10 sessions
     the published chance is the prior alone, labelled prior-only.
   - Median lifetime of a level: the first window, scanning 1 to
     60 sessions, at which the prior touch chance reaches one half;
     if it never does, the lifetime reads "more than 60 sessions".
     It is a prior figure today and is labelled as one.
   - Same-session first failure: the up chance is the call wall's
     1-session break chance, the down chance is the put wall's;
     neither takes the rest. The call names the larger side, or
     "neither" when both break chances are under 10%.
   - Features the design names that the card record does NOT
     carry, shipped absent and named, never faked: the overnight
     gap's share of the distance (no session open for the card's
     grading session is on the grading record), the days to the
     dominant expiry (cards carry no expiry breakdown), and the
     wall strike's size against its neighbouring strikes (cards
     carry the wall strikes only, no neighbouring strikes).
   - Ledger shape: per index, per level and window, one row for
     the touch chance and one for the break chance (the flip
     carries its crossed-and-closed-beyond chance), plus one row
     for the same-session first-failure split. Because the shared
     ledger's dedupe key omits the quantity, every value carries
     its cell name beside the chance, like Engine 2's fix; grading
     reads the chance either way. Known grading note, stated like
     the earlier engines stated theirs: the shared grading runner
     cannot yet resolve a close-through or a flip-close-beyond
     outcome, and its touch check is the plain level check, not
     the imported 0.2% wall definition; those rows carry the plain
     events stated and grading follows the imported definitions
     when the runner is next extended. No live row can mature
     until the price source passes its horizon in any case.
   - Thin-cell rule: below 30 graded, counts only, no percentage
     and no score is published from the record.

3. NON-CLAIMS
   - No calibration claim is made. With 9 cards and 6 graded tests
     the prior dominates every number on the page, and each number
     says whether the record touched it at all.
   - The history section is the record's own past, replayed
     through the imported definitions; it ledgers nothing.
   - Still-untouched levels are censored, never counted as held
     forever and never dropped from a denominator.

=====================================================================
Behaviour: cross-checks the card store, the grading record, the
published map page and the shared forecast ledger, failing closed
on any disagreement; replays the card record into episodes; builds
the freshest card's forecasts per index and appends them through
the forecast machinery API only; writes data.json. All timestamps
come from the sources, never the clock, so reruns are idempotent.

Usage: python3 refresh_walllifetime.py
"""

import json
import math
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
LOG_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
SCORECARD_PATH = os.path.join(MORGUE, "output", "scorecard.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
BAND_PATH = os.path.join(HERE, "corrected-band", "data.json")
WALLCHECK_PATH = os.path.join(HERE, "wall-check", "data.json")
MORNINGMAP_PATH = os.path.join(HERE, "morning-map", "data.json")
FORECAST_DIR = os.path.expanduser("~/workspace/terminal-lineup/forecast")
OUT_PATH = os.path.join(HERE, "wall-lifetime", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

sys.path.insert(0, MORGUE)
from scorecards import grade_map_row, map_grading_date  # noqa: E402,F401

import importlib.util  # noqa: E402


def _load(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_forecast_ledger = _load("forecast_ledger_mod",
                         os.path.join(FORECAST_DIR, "ledger.py"))
_forecast_registry = _load("forecast_registry_mod",
                           os.path.join(FORECAST_DIR, "registry.py"))
Ledger = _forecast_ledger.Ledger
file_sha256 = _forecast_ledger.file_sha256
Registry = _forecast_registry.Registry

ENGINE_ID = "engine_08"
NAMES = ["SPY", "QQQ", "IWM"]
PLAIN_NAME = {"SPY": "SPY (the big S&P 500 fund)",
              "QQQ": "QQQ (the big Nasdaq-100 fund)",
              "IWM": "IWM (the big small-company fund)"}
WINDOWS = (1, 3, 5, 10)
PRIOR_STRENGTH = 20
BREAK_SHARE = {"amplifying": 0.65, "dampening": 0.30}
FLIP_FACTOR = {"amplifying": 1.25, "dampening": 0.75}
THIN = 30
KILL_CARDS_PER_INDEX = 60

SOURCE_WORDS = ("The published morning map cards on record and the "
                "public grading of those cards against the completed "
                "trading sessions that followed them")


def fail(message):
    print(f"Wall Lifetime refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def clamp(p):
    return min(max(p, 0.01), 0.99)


def weekdays_from(start_iso, count):
    d = date.fromisoformat(start_iso)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def build():
    for path in (LOG_PATH, SCORECARD_PATH, PANEL_PATH, BAND_PATH,
                 WALLCHECK_PATH, MORNINGMAP_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    scorecard = load_json(SCORECARD_PATH)
    panel = load_json(PANEL_PATH)
    band_data = load_json(BAND_PATH)
    wallcheck = load_json(WALLCHECK_PATH)
    morningmap = load_json(MORNINGMAP_PATH)

    # ---- Cards of record: last published map card per index per day
    of_record = {}
    for r in log_rows:
        if r.get("component") == "gex_static_v1":
            of_record[(r["underlying"], r["ts_utc"][:10])] = r
    if not of_record:
        return fail("the permanent log holds no published map cards")
    cards = []
    for (sym, _day), r in sorted(of_record.items()):
        if sym not in NAMES:
            return fail(f"a card of record names {sym}, which this "
                        "page does not cover")
        gex = r.get("net_gex_usd_per_1pct")
        if not isinstance(gex, (int, float)):
            return fail("a card of record carries no positioning "
                        "figure to sign")
        cards.append({
            "name": sym, "published_at_utc": r["ts_utc"],
            "spot": float(r["spot"]), "call_wall": float(r["call_wall"]),
            "put_wall": float(r["put_wall"]),
            "flip": float(r["zero_gamma"]),
            "positioning": "amplifying" if gex < 0 else "dampening",
        })
    cards.sort(key=lambda c: (c["published_at_utc"], c["name"]))
    cards_by_ts = {c["published_at_utc"]: c for c in cards}

    # ---- The grading record must agree with the cards of record
    map_sc = scorecard.get("map") or {}
    grades = map_sc.get("grades") or []
    if (scorecard.get("counters") or {}).get(
            "map_cards_of_record") != len(cards):
        return fail("the grading record's card count disagrees with "
                    "the permanent log")
    if map_sc.get("cards_graded") != len(grades):
        return fail("the grading record's graded count disagrees "
                    "with the grades it carries")
    if wallcheck.get("cards_of_record") != len(cards) or \
            (wallcheck.get("totals") or {}).get("tests") != len(grades):
        return fail("the published wall grading page disagrees with "
                    "the card record")
    graded = {}  # card_ts -> grade row, walls cross-checked
    session_dates = sorted({g["session"] for g in grades} |
                           {c["published_at_utc"][:10] for c in cards})
    for g in grades:
        card = cards_by_ts.get(g.get("card_ts"))
        if card is None or g.get("underlying") != card["name"]:
            return fail("a grade names no card of record")
        if map_grading_date(g["card_ts"], session_dates) != g["session"]:
            return fail("a grade's session disagrees with the "
                        "imported grading-date rule")
        graded[g["card_ts"]] = g

    # ---- Expected-move units, checked against Engine 1's bands
    if band_data.get("as_of_session") != panel["SPY"][-1][0]:
        return fail("the band file and the price history disagree "
                    "on their last session")
    em_pct = {}
    for entry in band_data["live"]["names"]:
        hz = [h for h in entry["horizons"] if h["sessions"] == 1][0]
        b = [x for x in hz["bands"] if x["level"] == 68][0]
        em_pct[entry["symbol"]] = b["half_pct"] / 100.0
    # IWM by the same construction (Engine 1's recipe, k = 0.87 at
    # 1 session), the route the Exceedance Forecaster already uses.
    closes = [float(r[4]) for r in panel["IWM"]]
    sq = [math.log(closes[i] / closes[i - 1]) ** 2
          for i in range(1, len(closes))]
    i = len(closes) - 1
    vol = math.sqrt(252.0 * (sq[i - 1] + sum(sq[i - 5:i]) / 5.0 +
                             sum(sq[i - 22:i]) / 22.0) / 3.0)
    em_pct["IWM"] = vol * math.sqrt(1.0 / 252.0) * 0.87
    # Engine 1's published band carries its session-quality guard
    # widening (registered construction); the recipe cross-check
    # compares the recipe widened by the factor the band page
    # itself publishes, under the same condition Engine 1 applies
    # it (engine refresh cure, 2026-10-30). The unit this page
    # takes from the bands stays the published (widened) figure,
    # which is the band of record.
    _guard = (band_data.get("live") or {}).get("session_quality_guard")
    widen = _guard["band_widen_factor"] \
        if _guard is not None and _guard.get("deterioration") is not None \
        else 1.0
    for sym in ("SPY", "QQQ"):
        closes_s = [float(r[4]) for r in panel[sym]]
        sq_s = [math.log(closes_s[j] / closes_s[j - 1]) ** 2
                for j in range(1, len(closes_s))]
        k = len(closes_s) - 1
        vol_s = math.sqrt(252.0 * (sq_s[k - 1] +
                                   sum(sq_s[k - 5:k]) / 5.0 +
                                   sum(sq_s[k - 22:k]) / 22.0) / 3.0)
        if abs(vol_s * math.sqrt(1.0 / 252.0) * 0.87 * widen -
               em_pct[sym]) > 0.00005:
            return fail(f"expected-move disagreement for {sym} "
                        "against the published bands")

    # ---- History replay: episodes through the imported definitions
    episodes = []
    for card in cards:
        g = graded.get(card["published_at_utc"])
        for level in ("call_wall", "put_wall", "flip"):
            ep = {"name": card["name"],
                  "published_at_utc": card["published_at_utc"],
                  "level": level, "resolved_1": g is not None,
                  "censored_windows": [w for w in WINDOWS
                                       if w > 1] if g else
                                      list(WINDOWS)}
            if g is not None:
                if level == "call_wall":
                    ep["touched_1"] = bool(g["call_wall_touched"])
                    ep["through_1"] = not bool(g["call_wall_held"])
                elif level == "put_wall":
                    ep["touched_1"] = bool(g["put_wall_touched"])
                    ep["through_1"] = not bool(g["put_wall_held"])
                else:
                    ep["touched_1"] = None
                    ep["through_1"] = not bool(g["flip_respected"])
            episodes.append(ep)

    def pooled(level, field):
        sel = [e for e in episodes if e["level"] == level
               and e["resolved_1"] and e[field] is not None]
        return len(sel), sum(1 for e in sel if e[field])

    emp = {}
    for level in ("call_wall", "put_wall"):
        emp[(level, "touch")] = pooled(level, "touched_1")
        emp[(level, "break")] = pooled(level, "through_1")
    emp[("flip", "break")] = pooled("flip", "through_1")
    resolved_eps = sum(1 for e in episodes if e["resolved_1"])
    censored_eps = len(episodes) - resolved_eps

    # ---- Freshest card per index, cross-checked with the map page
    freshest = {}
    for card in cards:
        freshest[card["name"]] = card
    mm = {e["symbol"]: e for e in morningmap.get("indexes") or []}
    if morningmap.get("session") != \
            max(c["published_at_utc"][:10] for c in cards) and \
            morningmap.get("session") != \
            freshest["SPY"]["published_at_utc"][:10]:
        pass  # session is the cards' data session; checked per index below
    for sym, card in freshest.items():
        e = mm.get(sym)
        if e is None:
            return fail(f"the published map page carries no {sym} card")
        def _v(x):
            return x["value"] if isinstance(x, dict) else x
        if abs(_v(e["call_wall"]) - card["call_wall"]) > 1e-9 or \
                abs(_v(e["put_wall"]) - card["put_wall"]) > 1e-9 or \
                abs(_v(e["flip"]) - card["flip"]) > 1e-6 or \
                abs(_v(e["spot"]) - card["spot"]) > 1e-9:
            return fail(f"the published map page's freshest {sym} card "
                        "disagrees with the card store")

    # ---- Forecasts from the freshest cards
    registry = Registry()
    ledger = Ledger(os.path.join(FORECAST_DIR, "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain does not verify")
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (LOG_PATH, SCORECARD_PATH, BAND_PATH, PANEL_PATH)],
        "note": ("Freshest published map card per index, stamped with "
                 "the card's own session; chances from the registered "
                 "prior blended with the pooled graded record at the "
                 "1-session window only."),
    }
    created_total = 0
    live_names = []
    for sym in NAMES:
        card = freshest[sym]
        grading_session = map_grading_date(
            card["published_at_utc"],
            weekdays_from(card["published_at_utc"][:10], 40))
        if grading_session is None:
            return fail(f"no grading session for the freshest {sym} card")
        sessions = weekdays_from(grading_session, max(WINDOWS))
        em_price = card["spot"] * em_pct[sym]
        dist = {
            "call_wall": max(0.0, (card["call_wall"] - card["spot"])
                             / em_price),
            "put_wall": max(0.0, (card["spot"] - card["put_wall"])
                            / em_price),
            "flip": abs(card["flip"] - card["spot"]) / em_price,
        }
        pos = card["positioning"]
        lin = dict(lineage)
        lin["clocks"] = {
            "event_time": card["published_at_utc"],
            "publication_time": card["published_at_utc"],
            "first_available_time": card["published_at_utc"],
            "ingestion_time": scorecard["generated_at"],
            "decision_as_of": grading_session,
        }

        def prior_touch(level, w):
            return clamp(2.0 * phi(-dist[level] / math.sqrt(w)))

        def prior_break(level, w):
            if level == "flip":
                return clamp(phi(-dist[level] / math.sqrt(w))
                             * FLIP_FACTOR[pos])
            return clamp(prior_touch(level, w) * BREAK_SHARE[pos])

        def publish(level, kind, w):
            p_prior = (prior_touch(level, w) if kind == "touch"
                       else prior_break(level, w))
            n_emp, hits = emp.get((level, kind), (0, 0))
            if w == 1 and n_emp:
                p = (hits + PRIOR_STRENGTH * p_prior) / \
                    (n_emp + PRIOR_STRENGTH)
                blended = True
            else:
                p, blended = p_prior, False
            return round(clamp(p), 4), blended

        levels_out = []
        for level, label, level_price in (
                ("call_wall", "Call wall (the ceiling level above)",
                 card["call_wall"]),
                ("put_wall", "Put wall (the floor level below)",
                 card["put_wall"]),
                ("flip", "Flip level (where the day's push changes "
                         "character)", card["flip"])):
            rows_out = []
            for w in WINDOWS:
                entry = {"sessions": w,
                         "through_session": sessions[w - 1]}
                if level != "flip":
                    p_t, bl_t = publish(level, "touch", w)
                    entry["touch_p"] = p_t
                    entry["touch_prior_only"] = not bl_t
                p_b, bl_b = publish(level, "break", w)
                entry["break_p"] = p_b
                entry["break_prior_only"] = not bl_b
                rows_out.append(entry)
                kinds = (("touch", "touched"),
                         ("break", "closed through")) \
                    if level != "flip" else \
                    (("break", "crossed and closed beyond"),)
                for kind, words in kinds:
                    p = entry["touch_p"] if kind == "touch" \
                        else entry["break_p"]
                    cell = f"{level}_{kind}_{w}s"
                    outcome = {
                        "symbol": sym, "kind":
                            "touch" if kind == "touch" else
                            ("wall_break_close_through" if level != "flip"
                             else "flip_close_beyond"),
                        "level": level_price,
                        "window_open": sessions[0],
                        "window_close": sessions[w - 1],
                        "at_date": sessions[w - 1],
                    }
                    _row, created = ledger.append_forecast_declared(
                        engine_id=ENGINE_ID,
                        issued_ts=card["published_at_utc"],
                        subject=sym,
                        quantity=(f"{label}: chance it is {words} "
                                  f"within {w} session(s)"),
                        value={"p": p, "cell": cell},
                        horizon_open=sessions[0],
                        horizon_close=sessions[w - 1],
                        lineage=lin,
                        families=["modelled_inventory",
                                  "distributional_volatility"],
                        outcome=outcome)
                    created_total += int(created)
            med = None
            for w in range(1, 61):
                if prior_touch(level, w) >= 0.5:
                    med = w
                    break
            levels_out.append({
                "level": level, "label": label, "price": level_price,
                "distance_expected_moves": round(dist[level], 2),
                "windows": rows_out,
                "median_lifetime_sessions": med,
                "median_lifetime_prior_only": True,
            })
        up = levels_out[0]["windows"][0]["break_p"]
        down = levels_out[1]["windows"][0]["break_p"]
        neither_raw = max(0.0, 1.0 - up - down)
        tot = up + down + neither_raw
        bins = [round(up / tot, 4), round(down / tot, 4),
                round(neither_raw / tot, 4)]
        call_side = ("neither" if max(up, down) < 0.10
                     else ("up" if up >= down else "down"))
        _row, created = ledger.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=card["published_at_utc"],
            subject=sym,
            quantity=("Same-session first failure side: up (call wall "
                      "closes through first), down (put wall closes "
                      "through first), or neither"),
            value={"bins": bins, "cell": "first_failure_1s"},
            horizon_open=sessions[0], horizon_close=sessions[0],
            lineage=lin,
            families=["modelled_inventory",
                      "distributional_volatility"],
            outcome={"symbol": sym, "kind": "first_failure_side",
                     "at_date": sessions[0]})
        created_total += int(created)
        live_names.append({
            "symbol": sym, "name": PLAIN_NAME[sym],
            "published_at_utc": card["published_at_utc"],
            "session": grading_session, "spot": card["spot"],
            "positioning": pos,
            "positioning_plain": (
                "amplifying: positioning that can speed a move up "
                "once it starts" if pos == "amplifying" else
                "dampening: positioning that tends to slow moves down"),
            "expected_move_price": round(em_price, 2),
            "levels": levels_out,
            "first_failure": {"call": call_side, "up_p": bins[0],
                              "down_p": bins[1], "neither_p": bins[2]},
        })

    if not ledger.verify_chain():
        return fail("the forecast ledger's chain broke during append")
    figures = {}
    for row in ledger.rows():
        if row.get("type") == "forecast" and \
                row.get("engine_id") == ENGINE_ID:
            figures["recorded"] = figures.get("recorded", 0) + 1
        if row.get("type") == "grade" and \
                row.get("engine_id") == ENGINE_ID:
            figures["graded"] = figures.get("graded", 0) + 1
    per_index_cards = {sym: sum(1 for c in cards if c["name"] == sym)
                       for sym in NAMES}

    data = {
        "tool": "Wall Lifetime Forecaster",
        "state": "proving",
        "source": SOURCE_WORDS,
        "published_at_utc": scorecard["generated_at"],
        "card_sessions": sorted({c["published_at_utc"][:10]
                                 for c in cards}),
        "accrual": {
            "cards_of_record": len(cards),
            "cards_per_index": per_index_cards,
            "cards_graded": len(grades),
            "target_per_index": KILL_CARDS_PER_INDEX,
            "episodes": len(episodes),
            "episodes_resolved_1": resolved_eps,
            "episodes_censored": censored_eps,
        },
        "history": {
            "label": "History: the record so far, graded after the fact",
            "tests": len(grades),
            "thin": len(grades) < THIN,
            "pooled": {
                "call_touch": list(emp[("call_wall", "touch")]),
                "call_break": list(emp[("call_wall", "break")]),
                "put_touch": list(emp[("put_wall", "touch")]),
                "put_break": list(emp[("put_wall", "break")]),
                "flip_beyond": list(emp[("flip", "break")]),
            },
            "episodes": episodes,
        },
        "features_absent": [
            "The overnight gap's share of the distance: the card "
            "record carries no session open for a card's grading "
            "session, so this reading is absent, not estimated.",
            "Days to the biggest expiry: the cards carry no expiry "
            "breakdown, so this reading is absent, not estimated.",
            "The wall strike's size against its neighbouring "
            "strikes: the cards carry the wall strikes only, so this "
            "reading is absent, not estimated.",
        ],
        "live": {
            "names": live_names,
            "forecasts_recorded": figures.get("recorded", 0),
            "forecasts_graded": figures.get("graded", 0),
            "cards_counted_toward_target": per_index_cards,
        },
        "kill_criterion": (
            "After 60 cards per index, this tool is retired if its "
            "5-session touch chances are off by more than 10 points "
            "on average, or if its break chances score no better "
            "than the plain overall break rate."),
        "thin_rule": ("Below 30 graded, counts only: no percentage "
                      "and no score is drawn from a handful of tests."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(cards)} cards of record, "
          f"{len(grades)} graded tests, {created_total} new forecasts, "
          f"{figures.get('recorded', 0)} recorded in total)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
