#!/usr/bin/env python3
"""Canonical reading-date resolution (freshness cure, 2026-10-31).

ONE resolver for every surface: the hub (refresh_hub.py), the record
surface (record_surface.py) and, mirrored in JS, live.js / visual.js.
Before this module the terminal had four different freshness fields
giving four different answers, and live.js measured the data file's
Last-Modified stamp, which enrich_all.py rewrites hourly, so a stale
reading was always drawn as current.

The reading date is the date of the page's own reading, resolved from
the page's data in this order (first plausible date wins):

  record_surface.current_reading.as_of (when already enriched),
  as_of_session, session, as_of, freshest_session, freshest_date,
  modelled_freshest_date, precomputed_freshest_date,
  scored_run_session, assembled_on, replay_date, grading_run_at,
  state.date / state.as_of (composite pages), date,
  generated_at, generated_at_utc, published_at_utc, recorded_on

A candidate more than 370 days older than the file's generated_at is
a series start date sitting in an as-of field, not a reading date,
and is skipped. No date is ever invented: when nothing resolves the
answer is None and every surface must say so plainly.
"""
import re
from datetime import date

TOP_KEYS = ("as_of_session", "session", "as_of", "freshest_session",
            "freshest_date", "modelled_freshest_date",
            "precomputed_freshest_date", "scored_run_session",
            "assembled_on", "replay_date", "grading_run_at", "date",
            "panel_last_session", "readings_through",
            "newest_source_time", "published_date",
            "generated_at", "generated_at_utc", "published_at_utc",
            "recorded_on")
GEN_KEYS = ("generated_at", "generated_at_utc", "published_at_utc")


def parse_date(value):
    if not isinstance(value, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def reading_date(data):
    """The page data's own reading date, or None. Never file mtime."""
    if not isinstance(data, dict):
        return None
    rs = data.get("record_surface")
    if isinstance(rs, dict):
        cr = rs.get("current_reading")
        if isinstance(cr, dict):
            d = parse_date(cr.get("as_of"))
            if d is not None:
                return d
    generated = None
    for key in GEN_KEYS:
        generated = parse_date(data.get(key))
        if generated is not None:
            break

    def plausible(d):
        if d is None:
            return False
        if generated is not None and (generated - d).days > 370:
            return False  # series start, not a reading date
        return True

    for key in TOP_KEYS:
        d = parse_date(data.get(key))
        if plausible(d):
            return d
    gradings = data.get("gradings")
    if isinstance(gradings, list) and gradings and isinstance(gradings[0], dict):
        d = parse_date(gradings[0].get("date"))
        if plausible(d):
            return d
    for block_name in ("state", "wire"):
        block = data.get(block_name)
        if isinstance(block, dict):
            for key in ("date", "as_of", "grading_run_at"):
                d = parse_date(block.get(key))
                if plausible(d):
                    return d
    return None
