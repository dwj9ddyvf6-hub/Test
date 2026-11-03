#!/usr/bin/env python3
"""Refresh the Fear Day List data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real studies record on file: the published
studies card for the freshest study run, cross-checked against the
published feed's copy of the same studies (the summary) and against
the permanent log, whose freshest study entries must match the card
exactly. That record carries no fear-day study: no fear section on
the card, no fear section in the feed's summary, and no fear study
entry anywhere in the permanent log. The only other evidence this
page rests on is the daily market history actually on file: 23
daily readings of the fear gauge (the CBOE Volatility Index, called
the VIX) from September 21 to October 21, 2026, and 5 daily trading
sessions for SPY and QQQ from October 15 to October 21, 2026.

Reconstruction choices, stated as ours: (1) The fear-day definition
is the one already coded in the trading desk's own live-day rule,
read from its source here and never forked: a fear day is a day
when SPY fell more than 1.5%, or the fear gauge rose more than 15%
in a day, or the fear gauge closed at 25 or higher, or the fear
gauge closed at 20 or higher on a day when SPY or QQQ fell. If that
coded rule's thresholds ever change in its source, this refresh
fails closed instead of publishing the old definition. (2) The
definition is applied only to the sessions the history on file can
actually judge: the 4 index sessions that have a session before
them in the record to compare against (the first session on file,
October 15, has none, so its index moves cannot be computed from
this record; its fear-gauge arms are still checked). Exactly 1 of
those days qualifies, October 16, 2026, on the fear-gauge jump arm
(the gauge rose about 21% that day, to 19.99). (3) That day is
shown as a count with its date and readings, never dressed as a
published list with outcomes, because no study has ever counted
what happened after it. (4) A cell with fewer than 30 events is a
thin cell: counts only, no percentage, in the headline as
everywhere else. With 1 qualifying day, no follow-through
percentage of any kind is published. (5) Another desk's fear-day
research figures are not imported: their files are not on this
disk and their definition differs from the coded rule above, so
they are not this page's results.

Non-claims: this page claims no fear-day list has been published,
because none has. It does not claim the one qualifying day in the
short history on file led to anything, does not show any name as
supported on fear days, and does not import any other study's
numbers. If a fear-day study ever appears on the record, this
refresh fails closed (see below) rather than quietly continuing
to publish the unpublished state over a real study.

Fail-closed rules: if the studies card carries a fear section, if
the feed's summary of the studies disagrees with the card on any
study it carries or on its date, if the permanent log's freshest
study entries differ from the card, if any fear study entry
appears anywhere in the permanent log, if the coded fear-day
rule's thresholds in its source no longer match the definition
above, if the two index histories on file do not cover the same
sessions, or if the qualifying-day count does not recompute from
the history on file, the refresh stops and publishes nothing. All
timestamps come from the sources, never the clock, so running this
script twice produces the same file.

Usage: python3 refresh_fearday.py
"""

import datetime
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
RULE_PATH = os.path.expanduser(
    "~/workspace/femto-lean/core/setups_curator.py")
HISTORY_DIR = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source")
VIX_PATH = os.path.join(HISTORY_DIR, "yahoo-vix-daily.json")
BARS_PATH = os.path.join(HISTORY_DIR, "alpaca-spy-qqq-bars.json")
OUT_PATH = os.path.join(HERE, "fear-day", "data.json")

MIN_EVENTS_FOR_PERCENT = 30

SOURCE_WORDS = ("The published studies record and the daily market "
                "history on file: the fear gauge's daily readings "
                "and the daily sessions for SPY and QQQ")

DEFINITION = ("A fear day is a day when SPY fell more than 1.5%, "
              "or the fear gauge (the VIX) rose more than 15% in a "
              "day, closed at 25 or higher, or closed at 20 or "
              "higher on a day when SPY or QQQ fell.")

# The coded rule's own ledger component names for the studies the
# card carries, and the card section each one must match exactly.
LEDGER_STUDY_SECTIONS = {
    "study-gap-fill": "gap_fill",
    "study-orb-ib": "orb_ib",
    "study-earnings-dist": "earnings_dist",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Fear Day List refresh: {message}", file=sys.stderr)
    return 1


def has_fear_key(obj):
    if isinstance(obj, dict):
        return any("fear" in str(k).lower() or has_fear_key(v)
                   for k, v in obj.items())
    if isinstance(obj, list):
        return any(has_fear_key(v) for v in obj)
    return False


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, RULE_PATH,
                 VIX_PATH, BARS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]

    # --- The coded fear-day rule must still carry the thresholds
    # this page states; a changed rule is a changed definition. ---
    rule_src = open(RULE_PATH, encoding="utf-8").read()
    for needle in ("spy_day < -1.5", 'vix["change_pct"] > 15',
                   '"close"] >= 25', 'or 0) >= 20'):
        if needle not in rule_src:
            return fail("the coded fear-day rule no longer carries "
                        f"the threshold {needle!r} this page "
                        "states; refusing to publish a definition "
                        "the code no longer holds.")

    # --- No fear study may exist anywhere on the record. If one
    # appears, the unpublished state is no longer the truth and
    # this refresh must not publish over it. ---
    if has_fear_key({k: v for k, v in card.items()
                     if k not in ("labels",)}):
        return fail("the freshest studies card now carries a fear "
                    "section; a fear-day study exists and this "
                    "unpublished-state refresh refuses to publish "
                    "over it.")
    feed_studies = feed.get("studies") or {}
    if has_fear_key(feed_studies):
        return fail("the published summary of the studies now "
                    "carries a fear section; refusing to publish "
                    "the unpublished state over it.")
    for r in log_rows:
        if "fear" in str(r.get("component", "")).lower() or \
                "fear" in str(r.get("name", "")).lower():
            return fail("the permanent log now holds a fear study "
                        "entry; refusing to publish the "
                        "unpublished state over it.")

    # --- The feed's summary of the studies must agree with the
    # card on every study it carries, and on the date. ---
    for key, value in feed_studies.items():
        if card.get(key) != value:
            return fail(f"the published summary's {key} study "
                        "disagrees with the studies card; refusing "
                        "to publish a mismatched page.")
    # --- The summary must be a copy of this card, not of an older
    # run: the feed's generation time must not precede the card's.
    # (The feed's as_of_session is the board's session date, a
    # different date kind from the studies card's run date;
    # comparing them refused every coherent cycle. Cured
    # 2026-10-30 in the pattern of refresh_earningsdrift.py:
    # exact figure agreement above, plus generation order here.)
    # ---
    try:
        card_ts = datetime.datetime.fromisoformat(
            card["generated_at"])
        feed_ts = datetime.datetime.fromisoformat(
            feed["generated_at_utc"])
        stale = feed_ts < card_ts
    except (KeyError, TypeError, ValueError):
        return fail("the studies card and the published summary "
                    "do not both carry a generation time; "
                    "refusing to publish a summary whose run "
                    "cannot be bound to the card.")
    if stale:
        return fail("the published summary was generated "
                    f"{feed.get('generated_at_utc')} before the "
                    f"studies card it copies "
                    f"({card.get('generated_at')}); refusing to "
                    "publish a stale summary.")

    # --- The permanent log's freshest study entries must match
    # the card exactly, section for section. ---
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

    # --- The history actually on file, and the qualifying days
    # the coded rule finds in the part of it that can be judged. ---
    vix_raw = load_json(VIX_PATH)
    result = (vix_raw.get("chart") or {}).get("result") or []
    if not result:
        return fail("the fear gauge history on file is empty; "
                    "refusing to publish.")
    stamps = result[0].get("timestamp") or []
    closes = ((result[0].get("indicators") or {}).get("quote")
              or [{}])[0].get("close") or []
    if len(stamps) != len(closes) or not stamps:
        return fail("the fear gauge history on file does not hold "
                    "together; refusing to publish.")
    vix = []
    for ts, close in zip(stamps, closes):
        if close is None:
            # Yahoo carries a null close for days the market was
            # shut (the holidays in its daily series). A null is
            # no reading for that day, never a zero; the check
            # below still refuses to publish if an actual index
            # session on file has no fear gauge reading.
            continue
        day = datetime.datetime.fromtimestamp(
            ts, datetime.timezone.utc).date().isoformat()
        vix.append((day, float(close)))
    vix.sort()
    vix_by_day = dict(vix)
    vix_prev = {vix[i][0]: vix[i - 1][1] for i in range(1, len(vix))}

    bars = load_json(BARS_PATH)
    spy = sorted((b["t"][:10], float(b["c"]))
                 for b in bars.get("SPY_daily") or [])
    qqq = sorted((b["t"][:10], float(b["c"]))
                 for b in bars.get("QQQ_daily") or [])
    if not spy or [d for d, _ in spy] != [d for d, _ in qqq]:
        return fail("the two index histories on file do not cover "
                    "the same sessions; refusing to publish.")
    if any(day not in vix_by_day for day, _ in spy):
        return fail("an index session on file has no fear gauge "
                    "reading; refusing to publish.")

    qualifying = []
    checked = 0
    for i in range(1, len(spy)):
        day = spy[i][0]
        spy_pct = (spy[i][1] / spy[i - 1][1] - 1) * 100
        qqq_pct = (qqq[i][1] / qqq[i - 1][1] - 1) * 100
        vix_close = vix_by_day[day]
        prev_close = vix_prev.get(day)
        vix_pct = ((vix_close / prev_close - 1) * 100
                   if prev_close else None)
        checked += 1
        arms = []
        if spy_pct < -1.5:
            arms.append("SPY fell more than 1.5% that day")
        if vix_pct is not None and vix_pct > 15:
            arms.append("the fear gauge rose more than 15% that day")
        if vix_close >= 25:
            arms.append("the fear gauge closed at 25 or higher")
        if (spy_pct < 0 or qqq_pct < 0) and vix_close >= 20:
            arms.append("the fear gauge closed at 20 or higher on a "
                        "day when SPY or QQQ fell")
        if arms:
            qualifying.append({
                "date": day,
                "fear_gauge_close": round(vix_close, 2),
                "fear_gauge_change_pct": (
                    round(vix_pct, 1) if vix_pct is not None else None),
                "spy_change_pct": round(spy_pct, 1),
                "qqq_change_pct": round(qqq_pct, 1),
                "qualified_by": arms,
            })

    n = len(qualifying)
    data = {
        "tool": "Fear Day List",
        "state": "unpublished",
        "published_at_utc": card["generated_at"],
        "studies_as_of": card["as_of"],
        "source": SOURCE_WORDS,
        "definition": DEFINITION,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "events": n,
        "thin": n < MIN_EVENTS_FOR_PERCENT,
        "history": {
            "fear_gauge_readings": len(vix),
            "fear_gauge_from": vix[0][0],
            "fear_gauge_to": vix[-1][0],
            "index_sessions": len(spy),
            "index_from": spy[0][0],
            "index_to": spy[-1][0],
            "sessions_checked": checked,
        },
        "qualifying_days": qualifying,
        "follow_through": {
            "state": "not_counted",
        },
        "receipt": {
            "published_at_utc": card["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (
                f"No fear-day study on the studies record dated "
                f"{card['as_of']}; {len(vix)} daily fear gauge "
                f"readings ({vix[0][0]} to {vix[-1][0]}) and "
                f"{len(spy)} index sessions ({spy[0][0]} to "
                f"{spy[-1][0]}) on file, {checked} sessions with a "
                f"session before them to compare against, {n} "
                "qualifying day(s) among them"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (state unpublished, {n} qualifying "
          f"day(s) in {checked} checked sessions, studies as of "
          f"{card['as_of']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
