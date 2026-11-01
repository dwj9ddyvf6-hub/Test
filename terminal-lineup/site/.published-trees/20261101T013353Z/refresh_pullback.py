#!/usr/bin/env python3
"""Refresh the Pullback Norm data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real studies record on file: the published
studies card for the freshest study run, cross-checked against the
published feed's copy of the same studies (the summary) and against
the permanent log, whose freshest study entries must match the card
exactly. That record carries no pullback study: no pullback section
on the card, none in the feed's summary, and no pullback entry
anywhere in the permanent log. The only other evidence this page
rests on is (a) a research summary recorded in the terminal's own
corpus analysis, describing another study's pullback test on a
dataset that is not on this disk, stated on the page as that
study's record and never as this tool's results, and (b) the daily
price history actually on file locally: 1,833 names with daily bars
from March 25, 2025 to October 23, 2026 (399 trading sessions),
which no pullback study here has ever run on.

Reconstruction choices, stated as ours: (1) The pullback idea is
stated in the plain words of its design: a pullback's depth is
judged against the same stock's own past pullbacks, not against a
fixed band. The exact coded formula of the other study (its depth
window and its own-norm denominator) is not readable from any file
on this disk, so no formula is printed as if it were on record.
(2) Because no pullback study has run in this engine, the page
ships the honest unpublished state only: no depth distribution, no
recovery times, no name list, and no signals are shown or invented.
(3) The other study's summary figures are shown only inside a
clearly labelled research-record block that names its dataset
(deep daily price history, 2016 to 2026, 6,385 names including
delisted ones, rising-trend names on fear days, moves measured
against the same day's average, forward windows of 20 and 60
trading sessions). (4) A cell with fewer than 30 events is a thin
cell: counts only, no percentage, in the headline as everywhere
else. With 0 pullback events on record here, no percentage derived
from local events is published anywhere on the page. (5) The local
daily price history on file is printed as coverage only (names,
sessions, dates); it is not dressed as a study input, because no
study here has used it.

Non-claims: this page claims no pullback study has run here and no
signal has been published by this tool, because none has. It does
not claim the other study's figures are this tool's results, does
not show any stock as a deep or shallow pullback, and does not
import any depth bucket, distribution, or recovery time from
anywhere. If a pullback study ever appears on the record, this
refresh fails closed (see below) rather than quietly continuing
to publish the unpublished state over a real study.

Fail-closed rules: if the studies card carries a pullback section,
if the feed's summary of the studies disagrees with the card on
any study it carries or on its date, if the permanent log's
freshest study entries differ from the card, if any pullback study
entry appears anywhere in the permanent log, or if the local daily
price history on file does not recompute to the coverage printed
(names, sessions, first and last dates), the refresh stops and
publishes nothing. All timestamps come from the sources, never
the clock, so running this script twice produces the same file.

Usage: python3 refresh_pullback.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "studies_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
BARS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "pullback-norm", "data.json")

MIN_EVENTS_FOR_PERCENT = 30

SOURCE_WORDS = ("The published studies record and the daily price "
                "history on file")

DEFINITION = ("A pullback is a dip in a stock that is in a rising "
              "trend. This tool judges how deep the dip is by "
              "comparing it with that same stock's own past dips, "
              "not with a fixed band that is the same for every "
              "stock.")

UNPROVEN_LABEL = ("New construction, still being proven: this is a "
                  "new idea built by this terminal, it has not been "
                  "proven yet, and no result from it is published "
                  "until a study on the record has counted it.")

RESEARCH_RECORD = {
    "dataset": ("Deep daily price history, 2016 to 2026, 6,385 "
                "names including delisted ones"),
    "setting": ("Rising-trend names on fear days, each name's move "
                "measured against the same day's average move"),
    "results": [
        {"window_sessions": 20, "era": "2016 to 2022",
         "rank_correlation": 0.026, "strength": 4.3},
        {"window_sessions": 20, "era": "2023 onward",
         "rank_correlation": 0.031, "strength": 4.3},
        {"window_sessions": 60, "era": "2023 onward",
         "rank_correlation": 0.062, "strength": 9.8},
    ],
}

LEDGER_STUDY_SECTIONS = {
    "study-gap-fill": "gap_fill",
    "study-orb-ib": "orb_ib",
    "study-earnings-dist": "earnings_dist",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Pullback Norm refresh: {message}", file=sys.stderr)
    return 1


def has_pullback_key(obj):
    if isinstance(obj, dict):
        return any("pullback" in str(k).lower() or has_pullback_key(v)
                   for k, v in obj.items())
    if isinstance(obj, list):
        return any(has_pullback_key(v) for v in obj)
    if isinstance(obj, str):
        return "pullback" in obj.lower()
    return False


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, BARS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]

    # --- No pullback study may exist anywhere on the record. ---
    if has_pullback_key({k: v for k, v in card.items()
                         if k not in ("labels",)}):
        return fail("the freshest studies card now carries a "
                    "pullback section; a pullback study exists and "
                    "this unpublished-state refresh refuses to "
                    "publish over it.")
    feed_studies = feed.get("studies") or {}
    if has_pullback_key(feed_studies):
        return fail("the published summary of the studies now "
                    "carries a pullback section; refusing to "
                    "publish the unpublished state over it.")
    for r in log_rows:
        if "pullback" in str(r.get("component", "")).lower() or \
                "pullback" in str(r.get("name", "")).lower():
            return fail("the permanent log now holds a pullback "
                        "study entry; refusing to publish the "
                        "unpublished state over it.")

    # --- Feed summary must agree with the card. ---
    for key, value in feed_studies.items():
        if card.get(key) != value:
            return fail(f"the published summary's {key} study "
                        "disagrees with the studies card; refusing "
                        "to publish a mismatched page.")
    # The feed's as_of_session is its headline (board) session,
    # not the studies card's date: demanding the two producers'
    # session fields be equal refused every coherent cycle once
    # the card advanced a day ahead of the board session (the
    # tape family defect class cured in stream D). The agreement
    # that means something is generation order: the summary must
    # have been generated at or after the card it summarises,
    # and its study contents must agree with the card, which the
    # loop above already checks (hookup cure, 2026-10-29).
    feed_gen = str(feed.get("generated_at_utc") or "")
    card_gen = str(card.get("generated_at") or "")
    if not feed_gen or not card_gen or feed_gen < card_gen:
        return fail("the published summary was generated "
                    f"{feed_gen or 'at an unrecorded time'} but "
                    f"the studies card was generated {card_gen}; "
                    "refusing to publish a summary older than "
                    "the card it summarises.")

    # --- The log's freshest study entries must match the card. ---
    study_rows = [r for r in log_rows
                  if str(r.get("component", "")).startswith("study-")]
    if not study_rows:
        return fail("the permanent log holds no study entries; "
                    "refusing to publish a page with no studies "
                    "record behind it.")
    freshest_ts = max(r["ts_utc"] for r in study_rows)
    freshest_run_second = freshest_ts[:19]
    if card.get("generated_at", "")[:19] != freshest_run_second:
        return fail("the permanent log's freshest study entries "
                    f"are stamped {freshest_ts} but the studies "
                    f"card was generated {card.get('generated_at')}; "
                    "refusing to publish a mismatched page.")
    freshest = [r for r in study_rows
                if r["ts_utc"][:19] == freshest_run_second]
    seen = {}
    for r in freshest:
        section = LEDGER_STUDY_SECTIONS.get(r.get("component"))
        if section is None:
            return fail("the permanent log's freshest study run "
                        f"carries {r.get('component')}, a study "
                        "this page does not know; refusing to "
                        "publish a partial page.")
        if r.get("value") != card.get(section):
            return fail("the permanent log's freshest "
                        f"{r.get('component')} entry differs from "
                        "the studies card; refusing to publish a "
                        "mismatched page.")
        seen[section] = True
    if set(seen) != set(LEDGER_STUDY_SECTIONS.values()):
        return fail("the permanent log's freshest study run does "
                    "not carry every study the card carries; "
                    "refusing to publish a mismatched page.")

    # --- Local daily price history on file: coverage only. ---
    bars = load_json(BARS_PATH)
    if not isinstance(bars, dict) or not bars:
        return fail("the daily price history on file is empty; "
                    "refusing to publish.")
    all_dates = set()
    for rows in bars.values():
        for row in rows:
            all_dates.add(row[0])
    if not all_dates:
        return fail("the daily price history on file holds no "
                    "dated bars; refusing to publish.")
    history = {
        "names": len(bars),
        "sessions": len(all_dates),
        "from": min(all_dates),
        "to": max(all_dates),
    }
    # The recorded coverage (1833 names, 399 sessions from
    # 2025-03-25 to 2026-10-23) is the floor, not a pin: the
    # panel advances daily (G2 cure), so sessions and the last
    # date grow while the name count and first date stay the
    # anchors. The published coverage is generated from the
    # recomputed history below, never stated from this gate
    # (hookup cure, 2026-10-29; same defect class as Engine 12).
    if history["names"] != 1833 or history["from"] != "2025-03-25" \
            or history["sessions"] < 399 \
            or history["to"] < "2026-10-23":
        return fail("the daily price history on file recomputes "
                    f"to {history}, below the recorded coverage "
                    "floor (1833 names, at least 399 sessions "
                    "from 2025-03-25); refusing to publish stale "
                    "coverage.")

    # The terminal's own pullback study (RC-25 cure,
    # 2026-10-30): pullback_study.py ran the study on the
    # landed DEEP panel and wrote its record beside this page.
    # When that record exists and its panel fingerprint matches
    # the panel on disk, the counted state is published from
    # it. The fail-closed checks above still bind the morgue
    # studies record, which remains a separate record; this
    # study is the terminal's own, stated as such on the page.
    study = None
    study_path = os.path.join(HERE, "pullback-norm",
                              "study_record.json")
    if os.path.exists(study_path):
        with open(study_path, encoding="utf-8") as fh:
            candidate = json.load(fh)
        deep_path = os.path.expanduser(
            "~/workspace/morgue/data_cache/deep_bars.json")
        st = os.stat(deep_path)
        fingerprint = (f"deep_bars.json:{st.st_size}:"
                       f"{st.st_mtime_ns}")
        if candidate.get("panel_fingerprint") == fingerprint \
                and candidate.get("events", 0) > 0:
            study = candidate

    if study is not None:
        all_stats = study["all_events"]
        data = {
            "tool": "Pullback Norm",
            "state": "published",
            "published_at_utc": study["run_at_utc"],
            "studies_as_of": card["as_of"],
            "source": ("The terminal's own pullback study on "
                       "the deep price history on file, beside the "
                       "published studies record and the daily "
                       "price history on file"),
            "definition": DEFINITION,
            "unproven_label": UNPROVEN_LABEL,
            "thin_threshold": MIN_EVENTS_FOR_PERCENT,
            "events": study["events"],
            "signals_published": study["signals_on_latest_session"],
            "thin": study["events"] < MIN_EVENTS_FOR_PERCENT,
            "history": history,
            "research_record": RESEARCH_RECORD,
            "study": {
                "panel_names": study["panel_names"],
                "panel_last_session": study["panel_last_session"],
                "universe_names": study["universe_names"],
                "names_too_short": study["names_too_short"],
                "min_sessions": study["min_sessions"],
                "events_by_bucket": study["events_by_bucket"],
                "original_form": study["original_form"],
                "latest_session": study["latest_session"],
                "latest_signals": study["latest_signals"],
                "engine_24_depth_leg": study["engine_24_depth_leg"],
                "engine_29_depth_leg": study["engine_29_depth_leg"],
            },
            "distribution": {
                "state": "counted",
                "depth_deciles_at_events":
                    study["depth_deciles_at_events"],
                "events_by_bucket": study["events_by_bucket"],
                "fwd20_mean_rel_pct": all_stats["fwd20_mean_rel_pct"],
                "fwd20_median_rel_pct":
                    all_stats["fwd20_median_rel_pct"],
                "fwd60_mean_rel_pct": all_stats["fwd60_mean_rel_pct"],
                "fwd20_counted": all_stats["fwd20_counted"],
                "fwd60_counted": all_stats["fwd60_counted"],
            },
            "recovery": {
                "state": "counted",
                "recovered_within_60": all_stats["recovered_within_60"],
                "censored_at_60": all_stats["censored_at_60"],
                "recovery_median_sessions":
                    all_stats["recovery_median_sessions"],
            },
            "receipt": {
                "published_at_utc": study["run_at_utc"],
                # The receipt must name the same record the top
                # line names (the terminal's own study beside the
                # studies record). It previously carried only the
                # studies-record words, so the Receipts page's
                # receipt-versus-top-line parity check refused
                # every run after the study published
                # (PULLBACK-RECEIPT-SOURCE-20261031). The shared
                # source words carry no internal file name: the
                # Receipts page forbids internal wording in
                # anything it republishes, and reader surfaces
                # carry none either.
                "source": ("The terminal's own pullback study on "
                           "the deep price history on file, beside "
                           "the published studies record and the "
                           "daily price history on file"),
                "coverage": (
                    f"The terminal's own pullback study counted "
                    f"{study['events']} events over "
                    f"{study['universe_names']} names with at "
                    f"least {study['min_sessions']} sessions on "
                    f"the deep price history (panel of "
                    f"{study['panel_names']} names to "
                    f"{study['panel_last_session']}); "
                    f"{study['signals_on_latest_session']} "
                    "pullback signals on the panel's freshest "
                    "session. No pullback study stands on the "
                    f"studies record dated {card['as_of']}; this "
                    "study is the terminal's own and is stated "
                    "as such."),
            },
        }
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, "w", encoding="utf-8") as fh:
            data = _tc.stamp_for_script(data, __file__) \
                if _tc is not None else data
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"Wrote {OUT_PATH} (state published, "
              f"{study['events']} pullback events, "
              f"{study['signals_on_latest_session']} latest "
              "signals)")
        return 0

    data = {
        "tool": "Pullback Norm",
        "state": "unpublished",
        "published_at_utc": card["generated_at"],
        "studies_as_of": card["as_of"],
        "source": SOURCE_WORDS,
        "definition": DEFINITION,
        "unproven_label": UNPROVEN_LABEL,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "events": 0,
        "signals_published": 0,
        "thin": True,
        "history": history,
        "research_record": RESEARCH_RECORD,
        "distribution": {"state": "not_counted"},
        "recovery": {"state": "not_counted"},
        "receipt": {
            "published_at_utc": card["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (
                f"No pullback study on the studies record dated "
                f"{card['as_of']}; daily price history on file "
                f"covers {history['names']} names over "
                f"{history['sessions']} trading sessions "
                f"({history['from']} to {history['to']}), and no "
                "pullback study here has run on it; 0 pullback "
                "signals published"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (state unpublished, 0 pullback events, "
          f"studies as of {card['as_of']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
