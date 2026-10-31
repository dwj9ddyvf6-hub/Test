#!/usr/bin/env python3
"""Refresh the Expected Move Map data file.

The map on the page is the published 15.87 expected-move
construction, reproduced, not invented here: the percent move
priced for a session is the prior close of the volatility index
divided by 15.87; the expected move in points is that percent of
the name's prior close, rounded to the nearest tenth of a point
before anything is drawn from it; the session band is the close
plus and minus the move; the week band widens the rounded move
by the square root of five and rounds again the same way.

What the sources carry (and what this script therefore shows):
- A permanent log of trading days on which a map was actually
  drawn and filed at the time, each with the close it was
  measured from, the volatility close used, the session move,
  the five lines and the weekly move. The first maps were filed
  on 2026-10-22 and 2026-10-23, for the two names the method's
  records support (the big S&P 500 fund and the big Nasdaq-100
  fund). No map was ever filed for the small-cap fund, so it is
  published as not enough data. Since the EXPECTED-MOVE-FILING
  cure of 2026-10-30, the live desk (muse-desk-v3) files each
  new session's map into the same log at evaluation time
  (rows stamped filing="filed_at_time", source_desk=
  "muse-desk-v3"). The five sessions the lane missed while its
  producer was dark (2026-10-26 to 2026-10-30) were rebuilt
  later from the saved primary price records and are filed
  with filing="reconstructed" and their true computation time;
  they are labelled reconstructed wherever they are published,
  never presented as filed at the time.
- Independent saved price records (daily closes for both funds
  and daily closes of the volatility index) covering the days
  before the 2026-10-22 session, plus a second saved daily
  price record for the same closes.

Fail-closed cross-checks, all of them:
- Every filed map is recomputed with the construction's own
  arithmetic (the same module the filed maps were drawn with);
  any field that does not reproduce exactly stops the refresh.
- The 2026-10-22 session was filed with two different maps
  during the day: a short-lived one built on the volatility
  close of the day before the prior day, and the map built on
  the true prior close, which is also the first one filed and
  the one most ticks carry. The independent volatility record
  names the prior close (16.68 for the session of 2026-10-22),
  and only the map matching it may be published; if no filed
  map matched it, the refresh would stop instead of choosing.
  The 2026-10-23 session's filings all agree with each other.
- For the Nasdaq-100 fund, the filed record carries its session
  move but not the close it was measured from. A band is
  published for it only for a session whose measured-from close
  stands on a saved primary price record AND whose recomputed
  move equals the filed move. Two records cover the early
  sessions (the Azrael daily bars and the price panel): where
  both cover a date they must agree with each other. The
  Azrael record ends 2026-10-21; sessions after that are
  measured from the price panel alone (the same primary record
  the reconstructed maps were built from, and the record every
  panel tool publishes). That holds for the session of
  2026-10-22 (close 725.20, move 7.6) and for every filed and
  reconstructed session after it whose panel close reproduces
  its filed move: a band whose starting price cannot be shown
  is not published. (EMAP-QQQ-PANEL-20261031 cure: the earlier
  two-record-only rule froze QQQ at 2026-10-22 while the panel
  carried its closes all along.)
- The S&P 500 fund's session band edges are the filed map's own
  upper and lower lines, and its week edges are its filed
  weekly move measured from the map's own centre line.

Honesty rules:
- Sessions and times are read off the sources, never from the
  clock: the time a map is shown as drawn is the moment it
  first appears in the permanent log. Running this script twice
  produces the same file.
- Nothing is extrapolated to newer sessions or other names.
  When newer maps are filed, this refresh picks them up on its
  own rules; until then the page shows the newest maps on
  record and says so.

Usage: python3 refresh_expected_move.py
"""

import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.expanduser("~/workspace/femto-lean/state/ledger.jsonl")
BARS_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/"
    "alpaca-spy-qqq-bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/"
    "yahoo-vix-daily.json")
CACHE_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "expected-move", "data.json")

sys.path.insert(0, os.path.expanduser("~/workspace/femto-lean"))
from core import em_1587 as em  # noqa: E402  the construction itself

NAMES = ["SPY", "QQQ", "IWM"]
FULL_NAMES = {
    "SPY": "SPY (the big S&P 500 fund)",
    "QQQ": "QQQ (the big Nasdaq-100 fund)",
    "IWM": "IWM (the big small-cap fund)",
}

SOURCE_WORDS = ("Daily closing prices for each fund and the daily "
                "close of the volatility index, drawn and filed "
                "at the time in a permanent log of trading days")

RECONSTRUCTED_SOURCE_WORDS = (
    "Daily closing prices for each fund and the daily close of "
    "the volatility index, computed later from the saved primary "
    "price records and labelled reconstructed; this map was not "
    "filed at the time")

# ---- Azrael increment (DEEP-PASS 3.1 via Section 2.5, L07) --------
# Adopted as is into this tool: the square root of time funding
# curve, the wall classification and the regime bands from Ausar's
# reading of the same Azrael map. The desk's own construction
# module (femto-lean core em_1587) carries the same funded range
# and the same regime thresholds under its desk names; the labels
# published here are the Azrael lab's (CALM, MIXED, FAST).
SESSION_MINUTES = 390
FUNDED_ELAPSED = (0, 30, 60, 120, 240, 390)


def regime_label(vix_close):
    """VIX below 15 CALM, above 18.5 FAST, else MIXED."""
    v = float(vix_close)
    if v < 15.0:
        return "CALM"
    if v > 18.5:
        return "FAST"
    return "MIXED"


def funded_move(em_points, elapsed_minutes,
                session_minutes=SESSION_MINUTES):
    """The funded (elapsed) move: EM x sqrt(elapsed / session),
    with elapsed held inside the session."""
    if session_minutes <= 0:
        return 0.0
    frac = min(max(float(elapsed_minutes) / float(session_minutes),
                   0.0), 1.0)
    return float(em_points) * math.sqrt(frac)


def funded_curve(close, em_points,
                 session_minutes=SESSION_MINUTES):
    """The funding curve as published points: for each elapsed
    mark, how much of the session move is funded by then, and
    the band that funding implies around the close."""
    out = []
    for elapsed in FUNDED_ELAPSED:
        pts = funded_move(em_points, elapsed, session_minutes)
        out.append({
            "elapsed_minutes": elapsed,
            "funded_points": round(pts, 2),
            "lower": round(float(close) - pts, 2),
            "upper": round(float(close) + pts, 2)})
    return out


def walls_for(close, em_points):
    """The map's walls and half moves (shelves) around a close."""
    c, e = float(close), float(em_points)
    return {"centre": round(c, 2),
            "upper_wall": round(c + e, 2),
            "lower_wall": round(c - e, 2),
            "upper_half": round(c + 0.5 * e, 2),
            "lower_half": round(c - 0.5 * e, 2)}


def classify_target(price, close, em_points):
    """Classify a candidate price against the walls and the
    central half move. Returns one of: beyond_upper_wall,
    at_upper_wall, upper_half_inside, central, lower_half_inside,
    at_lower_wall, beyond_lower_wall, or no_classification when
    the inputs cannot support a classification."""
    try:
        p, c, e = float(price), float(close), float(em_points)
    except (TypeError, ValueError):
        return "no_classification"
    if p <= 0 or e <= 0:
        return "no_classification"
    if p > c + e:
        return "beyond_upper_wall"
    if p == c + e:
        return "at_upper_wall"
    if p > c + 0.5 * e:
        return "upper_half_inside"
    if p < c - e:
        return "beyond_lower_wall"
    if p == c - e:
        return "at_lower_wall"
    if p < c - 0.5 * e:
        return "lower_half_inside"
    return "central"


def fail(message):
    print(f"Expected Move Map refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def iso_utc(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def weekday_on_or_after(day, count):
    """The date `count` weekdays (Mon-Fri) from `day`, counting
    `day` itself as the first when it is a weekday."""
    d = day
    seen = 0
    while True:
        if d.weekday() < 5:
            seen += 1
            if seen == count:
                return d
        d += timedelta(days=1)


def prior_weekday(day):
    d = day - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def filed_maps():
    """{session: {map_key: (map, first_epoch, bars_served,
    filing)}} from the permanent log's tick records. filing is
    the row's provenance stamp: "filed_at_time" for maps filed
    when they were drawn (the default for the log's original
    rows, which predate the stamp), "reconstructed" for maps
    rebuilt later from the primary price records."""
    out = {}
    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            if '"em_1587"' not in line or '"weekly_em"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            ev = (row.get("evaluations") or {}).get("em_1587") or {}
            stamp = ev.get("sleeve_stamp") or {}
            m = stamp.get("map")
            if not m or stamp.get("session") != row.get("session"):
                continue
            key = json.dumps(m, sort_keys=True)
            slot = out.setdefault(row["session"], {})
            if key not in slot:
                slot[key] = (m, row["now"], ev.get("bars_served") or {},
                             row.get("filing") or "filed_at_time")
    return out


def expected_sessions(filed_sessions, cache_daily):
    """The weekday sessions the filing lane should hold, from
    the first filed session through the most recent completed
    session the saved records can prove: the weekday after the
    last daily close on the independent board cache record,
    capped at the freshest completed session itself. The cap
    matters since the PANEL-SAME-DAY-20261031 cure: the panel
    now carries the just-completed session's close on the same
    evening, so the uncapped weekday-after rule would demand a
    map for the NEXT session (on a Saturday, Monday's) before
    that session exists. Returns (expected, missing,
    horizon_session)."""
    last_close = max(cache_daily["SPY"])
    horizon = weekday_on_or_after(
        date.fromisoformat(last_close) + timedelta(days=1), 1)
    try:
        from completed_session import freshest_completed_session
        completed = date.fromisoformat(freshest_completed_session())
        if horizon > completed:
            horizon = completed
    except Exception:
        pass  # helper unavailable: the uncapped rule still holds
        # on any day the panel lags, which is when it was written
    start = date.fromisoformat(min(filed_sessions))
    expected = []
    d = start
    while d <= horizon:
        if d.weekday() < 5:
            expected.append(d.isoformat())
        d += timedelta(days=1)
    missing = [s for s in expected if s not in filed_sessions]
    return expected, missing, horizon.isoformat()


def long_day(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def check_map(m):
    """Recompute one filed map with the construction itself.
    Returns an error string, or None when it reproduces."""
    rebuilt = em.build_map(m["anchor_close"], m["vix_close"])
    if round(rebuilt["pct"], 4) != m["pct"]:
        return f"percent {m['pct']} does not reproduce"
    if rebuilt["em"] != m["em"]:
        return f"session move {m['em']} does not reproduce"
    if rebuilt["lines"] != m["lines"]:
        return "the five lines do not reproduce"
    if rebuilt["weekly_em"] != m["weekly_em"]:
        return f"weekly move {m['weekly_em']} does not reproduce"
    if rebuilt["session_1r"] != m["session_1r"]:
        return "the half move does not reproduce"
    if round(rebuilt["funded_at_flat"], 2) != m["funded_at_flat"]:
        return "the funded range does not reproduce"
    if rebuilt["regime"] != m["regime"]:
        return "the regime does not reproduce"
    return None


def build():
    for path in (LOG_PATH, BARS_PATH, VIX_PATH, CACHE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    bars = load_json(BARS_PATH)
    cache = load_json(CACHE_PATH)
    vix_doc = load_json(VIX_PATH)
    daily = {}
    for sym in ("SPY", "QQQ"):
        daily[sym] = {r["t"][:10]: float(r["c"])
                      for r in bars[f"{sym}_daily"]}
    cache_daily = {}
    for sym in ("SPY", "QQQ"):
        cache_daily[sym] = {r[0]: float(r[4]) for r in cache[sym]}
    result = vix_doc["chart"]["result"][0]
    vix = {}
    for ts, close in zip(result["timestamp"],
                         result["indicators"]["quote"][0]["close"]):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        vix[day.isoformat()] = float(close)

    filed = filed_maps()
    if not filed:
        return fail("the permanent log holds no filed map at all; "
                    "refusing to show a map that is not on the "
                    "record.")

    # --- Resolve each session to one map, and prove it. ---
    resolved = {}  # session -> (map, first_epoch, bars_served, filing)
    for session in sorted(filed):
        candidates = filed[session]
        prior = prior_weekday(date.fromisoformat(session)).isoformat()
        verified_vix = vix.get(prior)
        chosen = None
        for key, (m, epoch, served, filing) in candidates.items():
            err = check_map(m)
            if err:
                return fail(f"the map filed for {session} fails "
                            f"its own construction: {err}; "
                            "refusing to publish it.")
            if verified_vix is not None and m["vix_close"] == verified_vix:
                if chosen is not None:
                    return fail(f"two different maps filed for "
                                f"{session} both match the prior "
                                f"volatility close on record; "
                                "refusing to choose between them.")
                chosen = (m, epoch, served, filing)
        if verified_vix is not None:
            if chosen is None:
                return fail(f"no map filed for {session} uses the "
                            f"prior volatility close on record "
                            f"({verified_vix} on {prior}); refusing "
                            "to publish an unverified map.")
        else:
            if len(candidates) != 1:
                return fail(f"the maps filed for {session} "
                            "disagree and no independent volatility "
                            "record covers that week; refusing to "
                            "choose between them.")
            chosen = next(iter(candidates.values()))
        resolved[session] = chosen

    sessions_desc = sorted(resolved, reverse=True)

    # --- SPY: the freshest resolved session's filed map. ---
    spy_session = sessions_desc[0]
    spy_map, spy_epoch, spy_served, spy_filing = resolved[spy_session]
    spy_prior = prior_weekday(
        date.fromisoformat(spy_session)).isoformat()
    # Independent cross-checks where the records reach: the
    # volatility close and the session move for the earlier
    # session are on independent record and must agree.
    for session in sessions_desc:
        m = resolved[session][0]
        prior = prior_weekday(date.fromisoformat(session)).isoformat()
        if prior in vix and m["vix_close"] != vix[prior]:
            return fail(f"the map filed for {session} uses a "
                        f"volatility close of {m['vix_close']} but "
                        f"the independent record for {prior} says "
                        f"{vix[prior]}; refusing to publish.")
        if prior in daily["SPY"]:
            if em.expected_move(daily["SPY"][prior],
                                m["vix_close"]) != m["em"]:
                return fail(f"the session move filed for {session} "
                            "does not match the move recomputed "
                            "from the independently saved close; "
                            "refusing to publish.")

    # --- QQQ: the freshest session whose measured-from close is
    # on a saved primary price record and whose recomputed move
    # equals the filed move. Where both the Azrael daily record
    # and the price panel cover the prior date they must agree;
    # where only the panel covers it (every session after the
    # Azrael record ends, 2026-10-21) the panel close is the
    # record, the same primary record the reconstructed maps
    # were built from. Every covered session is collected, not
    # just the freshest, so the filing lane can state QQQ
    # completeness per name. ---
    qqq_entry = None
    qqq_covered_sessions = []
    for session in sessions_desc:
        m, epoch, served, filing = resolved[session]
        prior = prior_weekday(date.fromisoformat(session)).isoformat()
        close_a = daily["QQQ"].get(prior)
        close_b = cache_daily["QQQ"].get(prior)
        if close_b is None:
            continue  # the close is not on the panel record
        if close_a is not None and close_a != close_b:
            return fail(f"the two saved price records disagree on "
                        f"the QQQ close of {prior}: {close_a} vs "
                        f"{close_b}; refusing to publish.")
        close = close_b
        q_em = em.expected_move(close, m["vix_close"])
        if q_em != m["em_qqq"]:
            return fail(f"the QQQ move filed for {session} is "
                        f"{m['em_qqq']} but the close on record "
                        f"({close} on {prior}) gives {q_em}; "
                        "refusing to publish.")
        qqq_covered_sessions.append(session)
        if qqq_entry is None:
            qqq_entry = (session, m, epoch, served, prior, close,
                         q_em, filing)
    if qqq_entry is None:
        return fail("no session has a QQQ close on record that "
                    "reproduces its filed move; refusing to "
                    "publish a QQQ band.")

    def band(close, points, pct):
        return {
            "points": points,
            "pct": pct,
            "upper": round(close + points, 2),
            "lower": round(close - points, 2),
        }

    def entry(symbol, session, m, epoch, served, prior, close,
              session_points, filing="filed_at_time"):
        reconstructed = filing == "reconstructed"
        pct = round(m["pct"], 4)
        weekly_points = (m["weekly_em"] if symbol == "SPY"
                         else em.weekly_em(session_points))
        week_pct = round(weekly_points / close * 100.0, 2)
        through = weekday_on_or_after(
            date.fromisoformat(session), 5).isoformat()
        bars_n = served.get(symbol)
        coverage = (f"Measured from the closing price of {prior} "
                    f"and the volatility index close of the same "
                    f"day ({m['vix_close']:.2f})")
        if bars_n:
            coverage += (f"; {bars_n} five-minute price bars for "
                         f"the name were on record when the map "
                         "was drawn")
        if reconstructed:
            coverage += ("; this map was reconstructed later from "
                         "the saved primary price records, not "
                         "filed at the time")
        receipt = {
            "session": session,
            "measured_from": prior,
            "computed_at_utc": iso_utc(epoch),
            "filing": filing,
            "source": (RECONSTRUCTED_SOURCE_WORDS if reconstructed
                       else SOURCE_WORDS),
            "coverage": coverage,
        }
        return {
            "symbol": symbol,
            "name": FULL_NAMES[symbol],
            "state": "ok",
            "reconstructed": reconstructed,
            "close": close,
            "close_date": prior,
            "vix_close": round(m["vix_close"], 2),
            "session_band": band(close, session_points,
                                 round(pct, 2)),
            "week_band": band(close, weekly_points, week_pct),
            "week_through": through,
            "regime": {"label": regime_label(m["vix_close"]),
                       "vix_close": round(m["vix_close"], 2),
                       "rule": ("CALM below 15, FAST above 18.5, "
                                "MIXED between")},
            "walls": walls_for(close, session_points),
            "funded_curve": funded_curve(close, session_points),
            "session_minutes": SESSION_MINUTES,
            "receipt": receipt,
        }

    spy_close = spy_map["lines"]["MAGNET"]
    spy = entry("SPY", spy_session, spy_map, spy_epoch, spy_served,
                spy_prior, spy_close, spy_map["em"], spy_filing)
    # The filed lines are the band edges, exactly as drawn.
    spy["session_band"]["upper"] = spy_map["lines"]["WALL_UP"]
    spy["session_band"]["lower"] = spy_map["lines"]["WALL_DN"]

    (q_session, q_map, q_epoch, q_served, q_prior, q_close,
     q_em, q_filing) = qqq_entry
    qqq = entry("QQQ", q_session, q_map, q_epoch, q_served,
                q_prior, q_close, q_em, q_filing)

    iwm = {
        "symbol": "IWM",
        "name": FULL_NAMES["IWM"],
        "state": "no_data",
        "regime": None,
        "walls": None,
        "funded_curve": [],
        "reason": ("No expected-move map was ever drawn or filed "
                   "for this name in the saved records, so there "
                   "is no band to show."),
        "receipt": {
            "session": None,
            "measured_from": None,
            "computed_at_utc": None,
            "source": SOURCE_WORDS,
            "coverage": "No map on record for this name",
        },
    }

    freshest = max(spy["receipt"]["session"], qqq["receipt"]["session"])
    published = max(spy["receipt"]["computed_at_utc"],
                    qqq["receipt"]["computed_at_utc"])

    # --- Chain-derived map (2026-10-29 cure, G14/G5): redrawn
    # from the freshest chain snapshots now that they carry
    # content. The priced move uses the snapshot's MODELLED
    # at-the-money IV (chain_content) for the nearest expiry
    # after the snapshot day; it is labelled modelled on its
    # face and never mixed into the filed 15.87 bands above,
    # which stay the archive they are. ---
    chain_map = {"state": "no_data", "names": []}
    try:
        import gzip as _gz
        import chain_content as _ccx
        chains_dir = os.path.expanduser(
            "~/workspace/morgue/state/morgue/chains")
        cm_names = []
        for sym in NAMES:
            d = os.path.join(chains_dir, sym)
            days = sorted(n[:-8] for n in os.listdir(d)
                          if n.endswith(".json.gz")) if os.path.isdir(d) else []
            if not days:
                cm_names.append({"symbol": sym, "state": "no_data"})
                continue
            day = days[-1]
            with _gz.open(os.path.join(d, f"{day}.json.gz"),
                          "rt", encoding="utf-8") as fh:
                snap = json.load(fh)
            move = _ccx.chain_expected_move(
                snap.get("rows") or [], float(snap["spot"]), day)
            if move is None:
                cm_names.append({"symbol": sym, "state": "no_data",
                                 "snapshot_day": day})
            else:
                cm_names.append({
                    "symbol": sym, "state": "ok",
                    "snapshot_day": day, "spot": snap["spot"],
                    "oi_date": snap.get("oi_date"),
                    "iv_basis": "MODELLED",
                    "expected_move": move})
        if any(n.get("state") == "ok" for n in cm_names):
            chain_map = {
                "state": "ok",
                "basis": ("MODELLED at-the-money implied volatility "
                          "from the freshest chain snapshot "
                          "(Black-Scholes inversion of indicative "
                          "quote midpoints); the move is spot x IV "
                          "x sqrt(time to the nearest expiry)"),
                "names": cm_names}
    except Exception as exc:  # chain leg absent: filed map still
        chain_map = {"state": "no_data", "names": [],  # publishes
                     "reason": f"{type(exc).__name__}: {exc}"}

    # --- One live band per name (TRADING-PATH-EMAP-20261031): the
    # canonical live band for each name is the chain map band for
    # the page session, published once under canonical_bands. The
    # filed 15.87 maps in names[] are an archive construction with
    # a different basis and a different measured-from close; before
    # this cure the same file carried both with no ruling on which
    # was live (SPY 749.4 to 765.92 in the chain map beside SPY
    # 761.06 to 777.66 in names, and a QQQ map eight sessions old
    # beside a fresh chain map). Now: every names entry states its
    # role on its face, and a names entry whose session is not the
    # page session is published as no_data, never as a live band.
    canonical_bands = []
    for _n in chain_map.get("names", []):
        if _n.get("state") == "ok":
            _em = _n["expected_move"]
            canonical_bands.append({
                "symbol": _n["symbol"], "state": "ok",
                "snapshot_day": _n.get("snapshot_day"),
                "spot": _n.get("spot"), "lower": _em["lower"],
                "upper": _em["upper"], "expiry": _em["expiry"],
                "iv_basis": _n.get("iv_basis")})
    for _e in (spy, qqq):
        if _e.get("state") != "ok":
            continue
        _e["band_role"] = "filed_archive_not_the_live_band"
        _e["live_band_source"] = "canonical_bands"
        if _e["receipt"]["session"] != freshest:
            _e["state"] = "no_data"
            _e["reason"] = (
                f"Its newest filed map is for the session of "
                f"{_e['receipt']['session']}, not the page session "
                f"{freshest}, so it is shown as no data rather than "
                f"as a live band. The filed map stays in the filing "
                f"lane record.")

    # --- Filing lane completeness (EXPECTED-MOVE-FILING
    # 20261030): expected weekday sessions versus filed sessions,
    # computed from the records on every run, never written by
    # hand. Missing sessions are named; reconstructed sessions
    # are named as reconstructed. ---
    filed_sessions = sorted(resolved)
    exp_sessions, missing_sessions, horizon = expected_sessions(
        filed_sessions, cache_daily)
    reconstructed_sessions = sorted(
        s for s in filed_sessions
        if resolved[s][3] == "reconstructed")

    # Per-name completeness (EMAP-QQQ-PANEL-20261031): a session
    # counts as filed for the lane only at session level; each
    # covered name states its own newest session and its own
    # missing sessions, so a name frozen behind the lane (QQQ
    # at 2026-10-22 under the old rule) can never hide under a
    # complete lane claim again. SPY is the map anchor, so its
    # covered sessions are the filed sessions themselves. IWM
    # has no map at all and is stated as such, not as missing.
    qqq_missing = [s for s in exp_sessions
                   if s not in qqq_covered_sessions]
    lane_names = {
        "SPY": {"newest_session": spy["receipt"]["session"],
                "missing_sessions": list(missing_sessions)},
        "QQQ": {"newest_session": qqq["receipt"]["session"],
                "missing_sessions": qqq_missing},
        "IWM": {"newest_session": None, "missing_sessions": [],
                "state": "no_data"},
    }

    def _newest_words(symbol, entry_):
        words = (f"The newest map on record for {symbol} is for "
                 f"the session of {long_day(entry_['receipt']['session'])}")
        if entry_.get("reconstructed"):
            words += (", reconstructed later from the saved "
                      "primary price records, not filed at the time")
        return words

    note_parts = [
        "This edition covers the two names the saved records "
        "support, SPY and QQQ.",
        _newest_words("SPY", spy) + "; " +
        _newest_words("QQQ", qqq)[0].lower() +
        _newest_words("QQQ", qqq)[1:] + ", the newest session "
        "whose measured-from closing price is also on record.",
        "No map was ever filed for IWM.",
    ]
    if reconstructed_sessions:
        note_parts.append(
            "The sessions of "
            + ", ".join(long_day(s) for s in reconstructed_sessions)
            + " were missing from the filing log and were "
            "reconstructed later from the saved primary price "
            "records; they are labelled reconstructed wherever "
            "they appear.")
    if missing_sessions:
        note_parts.append(
            "No map was filed for the sessions of "
            + ", ".join(long_day(s) for s in missing_sessions)
            + "; those sessions stay gaps on the record.")
    for _sym in ("SPY", "QQQ"):
        _miss = lane_names[_sym]["missing_sessions"]
        if _miss and _miss != missing_sessions:
            note_parts.append(
                f"No {_sym} map was published for the sessions of "
                + ", ".join(long_day(s) for s in _miss)
                + "; those sessions stay gaps for that name.")
    if missing_sessions or qqq_missing or freshest < horizon:
        note_parts.append(
            "The records end there, so treat these bands as the "
            "last ones on record, not today's.")
    else:
        note_parts.append(
            "The filing lane holds a map for every weekday "
            "session through the most recent completed session "
            "the saved records can prove.")

    data = {
        "tool": "Expected Move Map",
        "session": freshest,
        "published_at_utc": published,
        "source": SOURCE_WORDS,
        "coverage_note": " ".join(note_parts),
        "filing_lane": {
            "filed_sessions": filed_sessions,
            "expected_sessions": exp_sessions,
            "missing_sessions": missing_sessions,
            "reconstructed_sessions": reconstructed_sessions,
            "latest_completed_session": horizon,
            "names": lane_names,
        },
        "names": [spy, qqq, iwm],
        "chain_map": chain_map,
        "canonical_bands": canonical_bands,
        "canonical_band_note": ("The live expected move band for "
                                "each name is the one listed under "
                                "canonical_bands, taken from the "
                                "chain map for the page session. "
                                "The per-name filed maps are an "
                                "archive construction on a different "
                                "basis and are not live bands."),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (SPY map for {spy_session}, QQQ map "
          f"for {q_session}, IWM not enough data)")
    return 0


def main():
    rc = build()
    if rc != 0:
        return rc
    # Chain cure (REGIME-FEAR-CHAIN-20261031): the Regime Dial
    # reads this record's fear gauge close. Every republication
    # of this record therefore re-runs the dial in the same
    # process, so a standalone rebuild of this page can never
    # again leave the dial standing on a superseded input (the
    # dial also runs in its normal assembly slot in the tools
    # chain, where it re-reads every other source fresh). A dial
    # failure fails this refresh loudly rather than leaving the
    # pair out of sync.
    import subprocess
    regime = os.path.join(HERE, "refresh_regime.py")
    r = subprocess.run([sys.executable, regime],
                       capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        print("Expected Move Map refresh: chained Regime Dial "
              "re-run failed"
              + (f": {tail[-1]}" if tail else ""),
              file=sys.stderr)
        return 1
    print("Expected Move Map refresh: Regime Dial re-run chained "
          "to this republication succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
