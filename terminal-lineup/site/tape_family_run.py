#!/usr/bin/env python3
"""Tape family orchestrator (G7 cure, 2026-10-29).

The drift mechanism this cures: every tape consumer was refreshed
by hand, in no fixed order, so when the tape advanced (Flow Tape to
2026-10-29) its consumers stayed behind (seven consumers at
2026-10-27) and silently disagreed with each other. There was no
single run that owned the family and no stamp that said which tape
session a consumer was built from.

This orchestrator is that single run:
- It runs the consumers in dependency order (the tape first, then
  the consumers that read the tape card directly, then the ones
  that read other consumers).
- After the run it stamps EVERY consumer's data file (including
  Flow Tape's own) with a shared freshness stamp:
  tape_freshness {tape_session, consumer_session, state, 
  sessions_behind} where state is "current" when the consumer's
  session equals the freshest tape session and "stale" otherwise.
- A consumer whose refresh fails keeps its previous data file,
  gets stamped "stale" with the failure named, and the family run
  exits 1: the drift is loud, never silent. (Agent Debate also
  consumes non-tape families; when it refuses on a cross-family
  session disagreement its tape stamp says exactly that.)

Usage: python3 tape_family_run.py
Exit 0 only when every consumer is current with the tape session.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (script, data file, session key in that file) in dependency order.
CONSUMERS = [
    ("refresh_flow_tape.py", "flow-tape/data.json", "session"),
    ("refresh_activity.py", "activity-profile/data.json",
     "current_session"),
    ("refresh_premiummeter.py", "premium-meter/data.json",
     "freshest_session"),
    ("refresh_sweep_wire.py", "golden-sweep-wire/data.json",
     "freshest_session"),
    ("refresh_flowengine.py", "flow-engine/data.json", "session"),
    ("refresh_tapeheatmap.py", "tape-heatmap/data.json", "session"),
    ("refresh_alerttape.py", "alert-tape/data.json",
     "freshest_session"),
    ("refresh_flowboard.py", "flow-board/data.json",
     "freshest_session"),
    ("refresh_agentdebate.py", "agent-debate/data.json", "session"),
]

# Consumers whose headline session is another family's session
# by design: Agent Debate's session is the scored (price family)
# session it debates; its tape figures are joined at the
# freshest tape session and its refresh fail-closes when that
# join is absent or disagrees. For these, "current" means the
# refresh succeeded in this run, not headline-session equality
# (hookup cure, 2026-10-29: the equality stamp marked it stale
# forever and the family run could never exit 0).
JOINED_CONSUMERS = {"agent-debate/data.json"}


def read_session(path, key):
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        return doc.get(key), doc
    except (OSError, ValueError):
        return None, None


def stamp(path, doc, tape_session, consumer_session, note=None):
    """Write the shared freshness stamp into a consumer data file."""
    state = "current" if consumer_session == tape_session else "stale"
    doc["tape_freshness"] = {
        "tape_session": tape_session,
        "consumer_session": consumer_session,
        "state": state,
        "note": note or (
            "built from the freshest tape session"
            if state == "current" else
            "this consumer is behind the freshest tape session; "
            "do not combine its figures with a fresher tape "
            "consumer as if they confirmed each other"),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return state


def family_sessions(results):
    """{tool data path: session} from a results list, for tests."""
    return {r["data"]: r["session"] for r in results}


def main():
    results = []
    tape_session = None
    for script, data_rel, key in CONSUMERS:
        data_path = os.path.join(HERE, data_rel)
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, script)],
            capture_output=True, text=True)
        session, doc = read_session(data_path, key)
        if script == "refresh_flow_tape.py":
            tape_session = session
        entry = {"script": script, "data": data_rel,
                 "session": session, "exit": proc.returncode,
                 "tail": (proc.stdout + proc.stderr).strip()
                 .splitlines()[-1:] or []}
        results.append(entry)
        print(f"{script}: exit {proc.returncode}, session {session}"
              + (f" | {entry['tail'][0]}" if entry["tail"] else ""))
    if tape_session is None:
        print("tape family: Flow Tape produced no session; "
              "refusing to stamp", file=sys.stderr)
        return 1
    not_current = []
    for (script, data_rel, key), entry in zip(CONSUMERS, results):
        data_path = os.path.join(HERE, data_rel)
        session, doc = read_session(data_path, key)
        if doc is None:
            not_current.append(data_rel)
            continue
        note = None
        if entry["exit"] != 0:
            note = (f"refresh failed this run "
                    f"({entry['tail'][0] if entry['tail'] else 'no output'}); "
                    "the data shown is from its last successful run")
        if data_rel in JOINED_CONSUMERS and entry["exit"] == 0:
            doc["tape_freshness"] = {
                "tape_session": tape_session,
                "consumer_session": session,
                "state": "current",
                "note": ("this consumer's headline session is "
                         "the scored session it debates; its "
                         "tape figures are joined at the "
                         "freshest tape session and its refresh "
                         "fail-closes when that join is absent"),
            }
            with open(data_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, sort_keys=True)
                fh.write("\n")
            state = "current"
        else:
            state = stamp(data_path, doc, tape_session, session,
                          note=note)
        if state != "current":
            not_current.append(
                f"{data_rel} at {session} vs tape {tape_session}")
    if not_current:
        print(f"tape family: NOT fully current: {not_current}",
              file=sys.stderr)
        return 1
    print(f"tape family: all {len(CONSUMERS)} consumers current "
          f"with tape session {tape_session}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
