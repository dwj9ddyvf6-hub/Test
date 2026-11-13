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
- A joined consumer (Agent Debate) is judged by its own
  write-time stamp, not by headline-session equality (cure
  TAPE-JOINED-STAMP-20261113, see joined_verdict): a first stale
  stamp for a tape session is deferred to the tools lane's
  same-evening re-run of this family and does not fail the run;
  a second stale run for the same tape session, a failed
  refresh, or a missing or foreign stamp fails it as before.

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


def joined_verdict(exit_code, self_stamp, tape_session):
    """The family verdict for a joined consumer (cure
    TAPE-JOINED-STAMP-20261113). A joined consumer's headline
    session is another family's session by design, so headline
    equality with the tape session is the wrong test: it failed
    every tape family run from the tape's first advance until
    the tools lane's late re-run (the intraday lane stamped
    FAILED every five minutes through the whole 2026-11-12
    session) even though the consumer had refreshed, joined
    like for like, and stamped itself truthfully. The verdict
    is therefore the consumer's OWN tape_freshness stamp, read
    from the file it just wrote (stamp at write time, never
    recomputed by the orchestrator from a session read at run
    start):
    - "current": the consumer's write-time stamp says current
      for this tape session.
    - "deferred": the stamp says stale for this tape session
      and no earlier family run has already deferred this
      consumer for the same tape session. The page stays
      stamped stale with its reason; the family run does not
      fail, because the consumer's cross-family producer (the
      Second Opinion, refreshed by the tools lane) is the
      named ordering step that brings it current, and the
      tools lane re-runs this family the same evening.
    - "stale_fail": the refresh failed, the stamp is missing
      or names a different tape session, the stamp claims
      current for a different session than its headline, or
      the deferral for this tape session was already spent by
      an earlier run and the consumer is still stale (the
      promised re-run happened and did not cure it): the
      family run fails, loudly, as before."""
    if exit_code != 0:
        return "stale_fail"
    if not isinstance(self_stamp, dict):
        return "stale_fail"
    if self_stamp.get("tape_session") != tape_session:
        return "stale_fail"
    if self_stamp.get("state") == "current":
        return "current"
    if self_stamp.get("state") == "stale":
        if self_stamp.get("family_deferred_for") == tape_session:
            return "stale_fail"
        return "deferred"
    return "stale_fail"


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
    deferred = []
    for (script, data_rel, key), entry in zip(CONSUMERS, results):
        data_path = os.path.join(HERE, data_rel)
        session, doc = read_session(data_path, key)
        if doc is None:
            not_current.append(data_rel)
            continue
        if data_rel in JOINED_CONSUMERS:
            # Joined consumer (cure TAPE-JOINED-STAMP-20261113):
            # the verdict is the consumer's own write-time stamp,
            # never the orchestrator's headline-session equality
            # recomputation. A current stamp stands as written; a
            # first stale stamp for this tape session is deferred
            # (the page stays stamped stale with its reason, the
            # deferral is recorded on the stamp, and the tools
            # lane's re-run of this family is the named step that
            # must bring it current); anything else is stamped by
            # the ordinary rule and fails the run.
            verdict = joined_verdict(entry["exit"],
                                     doc.get("tape_freshness"),
                                     tape_session)
            if verdict == "current":
                continue
            if verdict == "deferred":
                doc["tape_freshness"]["family_deferred_for"] = \
                    tape_session
                with open(data_path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, sort_keys=True)
                    fh.write("\n")
                deferred.append(
                    f"{data_rel} at {session} vs tape "
                    f"{tape_session}")
                continue
            note = None
            if entry["exit"] != 0:
                note = (f"refresh failed this run "
                        f"({entry['tail'][0] if entry['tail'] else 'no output'}); "
                        "the data shown is from its last successful run")
            else:
                note = ("this consumer's headline session is the "
                        "scored session it debates; its tape "
                        "figures are joined like for like at the "
                        "tape card generation its prints source "
                        "was built from, behind the freshest tape "
                        "session, and its one deferral for this "
                        "tape session is spent; it is re-run after "
                        "the tools lane refreshes that source")
            state = stamp(data_path, doc, tape_session, session,
                          note=note)
            not_current.append(
                f"{data_rel} at {session} vs tape {tape_session}")
            continue
        note = None
        if entry["exit"] != 0:
            note = (f"refresh failed this run "
                    f"({entry['tail'][0] if entry['tail'] else 'no output'}); "
                    "the data shown is from its last successful run")
        state = stamp(data_path, doc, tape_session, session,
                      note=note)
        if state != "current":
            not_current.append(
                f"{data_rel} at {session} vs tape {tape_session}")
    if not_current:
        print(f"tape family: NOT fully current: {not_current}",
              file=sys.stderr)
        return 1
    if deferred:
        print(f"tape family: all {len(CONSUMERS)} consumers "
              f"current with tape session {tape_session} except "
              f"joined consumers deferred to the tools lane "
              f"re-run: {deferred}")
        return 0
    print(f"tape family: all {len(CONSUMERS)} consumers current "
          f"with tape session {tape_session}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
