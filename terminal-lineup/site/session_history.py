#!/usr/bin/env python3
"""Append-only session keeping for terminal pages (cure 2026-10-31,
terminal-state-the-information, Wave 3 Item F).

Four pages (agent-debate, gamma-ladder, morning-map,
sponsored-reset) kept no past sessions, so their record charts had
nothing honest to draw. Each page's refresh producer now calls
append_session once per run with the charted subject values it just
built, and carries the returned list in its data.json under
"session_history" so record_surface.py can plot the kept sessions.

The store is one file per page, <slug>/session-history.json, shaped
{"sessions": [{"session": "YYYY-MM-DD", "values": ...}]}. It is
append-only: a new dated entry is appended, earlier entries are
never rewritten. One guard: an identical repeat of the latest entry
(same session, same values) is not duplicated, because chained
re-runs inside one lane pass (the Morning Map refresh re-runs the
Gamma Ladder) would otherwise stack copies of one session. Nothing
is ever backfilled: the first entry a page keeps is the session of
the first run after this cure landed.
"""
import json
import os


def load_sessions(store_path):
    """The kept sessions in a store file, oldest first."""
    try:
        with open(store_path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return []
    sessions = doc.get("sessions") if isinstance(doc, dict) else None
    return sessions if isinstance(sessions, list) else []


def append_session(store_path, session, values):
    """Append one dated snapshot of a page's charted subject values
    and return the full kept list, oldest first. See the module
    docstring for the one identical-repeat guard."""
    sessions = load_sessions(store_path)
    entry = {"session": session, "values": values}
    if not sessions or sessions[-1] != entry:
        sessions.append(entry)
    os.makedirs(os.path.dirname(os.path.abspath(store_path)),
                exist_ok=True)
    tmp = store_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"sessions": sessions}, fh, indent=2,
                  sort_keys=True)
        fh.write("\n")
    os.replace(tmp, store_path)
    return sessions
