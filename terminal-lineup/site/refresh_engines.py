#!/usr/bin/env python3
"""Daily refresh runner for the 30 forecast engines plus the Record.

Scope (the owner's approval, 2026-10-29): every forecast-engine page in
the terminal, plus the Record page, then the terminal smoke check.

The engine slug set is derived from the program record
(FORECAST30-PROGRESS.md, the site/<slug>/ paths its build lines
name), minus the Record itself and minus pages with no matching
refresh script (those are upstream tools the engines read,
refreshed by their own lanes). Each engine's refresher is
site/refresh_<slug, dashes removed>.py where that naming holds;
an engine slug with no matching script is a named failure, never
silently skipped.

Exit code is nonzero when any refresher, the Record, or the smoke
check fails. The report names failures individually.

Proof log (cure REFRESH-PROOF-LOG-20261031): every run, scheduled
or manual, writes its own full output to terminal-lineup/
refresh_proof.log under a dated header naming the exit code, so
the final state carries the evidence of the last run instead of
relying on a cron result summary or a stale hand kept log. Before
this cure the log still held the 2026-10-30 02:57 run with 17
failures and no later run updated it.

Checkpoint, resume and streaming proof (cure
REFRESH-RESUME-20261111): the pre-cure runner held the whole run
in memory and wrote the proof log only at the end, so any kill
(a 2026-11-10 OOM kill inside self-analogue after ~2.9 hours, a
2026-11-11 machine restart at gamma-earnings-trap) burned the
entire run: no proof log, no recorded progress, and the next
invocation restarted from zero on a run whose legs take hours.
The legs themselves were already resumable in substance (they
regenerate their pages deterministically; their ledger appends
dedupe). The runner now:

- streams every printed line to the proof log as it is produced
  (a fresh session truncates it under a started header; a resume
  appends under a resumed header; the finished header naming the
  exit code closes whichever invocation completes the run), so a
  kill leaves the evidence of every completed leg on disk;
- records per-step completion in refresh_checkpoint.json,
  flushed after every step, keyed by the run's session (the
  freshest completed session the spine advances the panel to);
  a fresh invocation with an incomplete checkpoint for the same
  session skips steps already proven complete and runs only the
  remainder (a step that failed is retried, never skipped);
- invalidates the verification tail (the final attestation
  recount and re-attach, the Record, the enrich, the smoke check
  and the publish proof) whenever an upstream step completes
  after it, so the tail always verifies the final tree of the
  session, never an intermediate one;
- takes an exclusive flock on refresh_engines.lock for the whole
  run, so two invocations (the daily cron and a manual lane)
  serialise instead of interleaving appends on the shared
  ledger, the race the 2026-11-10 W5 verification hit.

A checkpoint whose run reached the end with no failures is
marked complete; the next invocation for the same session then
starts fresh, so a deliberate re-run re-proves everything.

Board republishing (same cure): refresh_board.py republishes
site/board/data.json from the morgue's published board card. It
ran only in the 19:00 tools refresh, after this runner, while the
morgue board build publishes the just-completed session's card
in the late afternoon (2026-11-11: 16:59 ET). The abstention
-signal leg's freshness check (Board session must equal the
panel's freshest session, cure ABSTENTION-SESSION-PIN-20261107)
therefore read a one-generation-stale page at 17:46 every day
the board advanced and failed closed on a healthy record. The
runner now republishes the Board in its own spine, after the
panel advance and before the engine loop; the republishing is
deterministic from the card, so no page content changes beyond
carrying the card's current session, which is what every
consumer of the page already expects.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # non-unix fallback: run unlocked
    fcntl = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROGRESS = ROOT / "FORECAST30-PROGRESS.md"
PROOF_LOG = ROOT / "refresh_proof.log"
CHECKPOINT = ROOT / "refresh_checkpoint.json"
LOCK_PATH = ROOT / "refresh_engines.lock"

# The verification tail: steps whose proofs must always describe
# the final tree of the session. Any upstream completion after
# one of them invalidates it and everything after it.
FINAL_STEPS = ("attestation-refresh-final", "attestation-reattach",
               "record", "record-enrich", "smoke", "publish-live")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Tee(io.TextIOBase):
    """Mirror everything printed during a run to a buffer and,
    when a proof stream is attached, to the proof log file,
    flushed per write so a kill mid-run leaves the evidence of
    every completed leg on disk (cure REFRESH-RESUME-20261111;
    before this the buffer was the only copy and died with the
    process)."""

    def __init__(self, real, proof_fh=None):
        self._real = real
        self._proof_fh = proof_fh
        self.buffer = io.StringIO()

    def write(self, s):
        self.buffer.write(s)
        if self._proof_fh is not None:
            self._proof_fh.write(s)
            self._proof_fh.flush()
        return self._real.write(s)

    def flush(self):
        if self._proof_fh is not None:
            self._proof_fh.flush()
        return self._real.flush()


def write_proof_log(text: str, exit_code: int,
                    path: Path = PROOF_LOG) -> None:
    """Kept for compatibility with the REFRESH-PROOF-LOG-20261031
    contract: a whole run's output under a finished header naming
    the exit code. main() now streams the proof log instead (cure
    REFRESH-RESUME-20261111); this remains for any caller that
    still files a completed run's text in one piece."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (f"# refresh_engines.py run finished {stamp} "
              f"exit {exit_code}\n")
    path.write_text(header + text, encoding="utf-8")


class _Checkpoint:
    """Per-step completion for one session's run, flushed after
    every step (cure REFRESH-RESUME-20261111). A step is skippable
    only when its last recorded attempt exited 0 in this session;
    a failed step is retried by the next invocation, and its
    failure string is carried until a retry clears it."""

    def __init__(self, session: str):
        self.session = session
        self.started_at = _now_iso()
        self.complete = False
        self.steps: dict = {}
        self.failures: dict = {}

    @classmethod
    def load(cls, session: str):
        """The incomplete checkpoint for this session, or None
        (no checkpoint, a different session, a completed run, or
        an unreadable file all mean: run fresh)."""
        try:
            data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        except Exception:
            return None
        if data.get("session") != session or data.get("complete"):
            return None
        cp = cls(session)
        cp.started_at = data.get("started_at", cp.started_at)
        cp.steps = data.get("steps") or {}
        cp.failures = data.get("failures") or {}
        return cp

    def save(self) -> None:
        payload = {"session": self.session,
                   "runner": "refresh_engines.py",
                   "started_at": self.started_at,
                   "updated_at": _now_iso(),
                   "complete": self.complete,
                   "steps": self.steps,
                   "failures": self.failures}
        tmp = CHECKPOINT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=1),
                       encoding="utf-8")
        os.replace(tmp, CHECKPOINT)

    def done(self, key: str) -> bool:
        return (self.steps.get(key) or {}).get("exit") == 0

    def mark(self, key: str, exit_code: int, seconds: float,
             failure: str = None) -> None:
        self.steps[key] = {"exit": exit_code,
                           "seconds": round(float(seconds), 1),
                           "at": _now_iso()}
        if exit_code == 0:
            self.failures.pop(key, None)
            # Invalidate the verification tail: an upstream step
            # completing after a tail step (in a later invocation
            # of the same session) means that tail step's proof
            # describes an intermediate tree, so it and every
            # tail step after it must run again. Inside the tail
            # itself only the later steps are invalidated. In a
            # single uninterrupted run nothing downstream is
            # marked yet, so this is a no-op on the happy path.
            if key in FINAL_STEPS:
                for later in FINAL_STEPS[FINAL_STEPS.index(key) + 1:]:
                    self.steps.pop(later, None)
            else:
                for tail in FINAL_STEPS:
                    self.steps.pop(tail, None)
        elif failure is not None:
            self.failures[key] = failure
        self.save()

    def ordered_failures(self, order: list) -> list:
        """Failure strings in canonical execution order, for the
        run summary: a failure recorded by an earlier invocation
        of this session is the run's failure until a retry of
        that step clears it."""
        out = [self.failures[k] for k in order if k in self.failures]
        out += [v for k, v in self.failures.items() if k not in order]
        return out


def _session_key(panel_through) -> str:
    if panel_through:
        return panel_through
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _panel_through():
    """The freshest completed session, computed once in main so
    the checkpoint's session key and the advance lanes' explicit
    --through can never disagree (PANEL-THROUGH-EXPLICIT-20261031
    intent, extended by REFRESH-RESUME-20261111)."""
    try:
        sys.path.insert(0, str(HERE))
        from completed_session import freshest_completed_session
        return freshest_completed_session()
    except Exception:
        return None


STAGE_TIMINGS_LOG = ROOT / "stage_timings.jsonl"


def main() -> int:
    import time as _time
    from datetime import datetime as _dt, timezone as _tz
    _started = _time.monotonic()
    _started_iso = _dt.now(_tz.utc).isoformat()
    # Serialise invocations before touching any shared state
    # (cure REFRESH-RESUME-20261111): the lock is held for the
    # process's life and released by the OS on any death,
    # including a kill or a machine restart.
    lock_fh = LOCK_PATH.open("a+")
    if fcntl is not None:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
    panel_through = _panel_through()
    session = _session_key(panel_through)
    cp = _Checkpoint.load(session)
    resumed = cp is not None
    if cp is None:
        cp = _Checkpoint(session)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proof_fh = PROOF_LOG.open("a" if resumed else "w",
                              encoding="utf-8")
    proof_fh.write(f"# refresh_engines.py run "
                   f"{'resumed' if resumed else 'started'} {stamp} "
                   f"session {session}\n")
    proof_fh.flush()
    tee = _Tee(sys.stdout, proof_fh)
    code = 1
    try:
        with contextlib.redirect_stdout(tee):
            code = _run(panel_through, cp)
    finally:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        proof_fh.write(f"# refresh_engines.py run finished {stamp} "
                       f"exit {code}\n")
        proof_fh.flush()
        proof_fh.close()
    # Stage timings (GLORY item 2b): one structured record per run,
    # built from the runner's own duration prints plus this timer.
    # Additive only: a stamp failure must never fail a refresh.
    try:
        sys.path.insert(0, str(HERE))
        import stage_timings as _st
        _rec = _st.build_record(
            tee.buffer.getvalue(), _time.monotonic() - _started, code,
            started_at=_started_iso)
        _st.append_record(_rec, STAGE_TIMINGS_LOG)
    except Exception as _e:  # noqa: BLE001 - stamp is evidence, not a gate
        print(f"stage timings stamp failed: {_e}", file=sys.stderr)
    return code

try:
    import terminal_common as _tc
except ImportError:  # runner stays runnable standalone
    _tc = None


def norm(s: str) -> str:
    return s.replace("-", "").replace("_", "")


def engine_slugs() -> list[str]:
    slugs = sorted(set(re.findall(r"site/([a-z][a-z0-9\-]+)/", PROGRESS.read_text())))
    return [s for s in slugs if s != "record"]


def _run(panel_through=None, cp: _Checkpoint = None) -> int:
    scripts = {norm(f.stem.replace("refresh_", "")): f for f in HERE.glob("refresh_*.py")}
    failures: list[str] = []
    ran: list[str] = []
    import time
    if cp is None:
        cp = _Checkpoint(_session_key(panel_through))
    cp.save()  # the session's checkpoint exists from the outset
    # Canonical step order, for the summary's failure ordering and
    # the checkpoint's tail invalidation bookkeeping.
    order = ["deep-panel-advance", "vix-capture", "deep-binary-store",
             "earnings-record", "first-minutes", "fair-gap-model",
             "form4-footnotes", "session-quality", "leadlag-record",
             "xbrl-route", "news-leg-estimation",
             "price-panel-advance", "forecast-grading",
             "attestation-refresh", "priced-moves",
             "earnings-calendar", "board-republish"]

    def skip(key: str) -> bool:
        if cp.done(key):
            print(f"skip {key} (checkpoint: complete for session "
                  f"{cp.session})", flush=True)
            return True
        return False

    # Panel through date (PANEL-THROUGH-EXPLICIT-20261031): the
    # advance lanes are invoked with an explicit --through naming
    # the freshest completed session, computed once in main (cure
    # REFRESH-RESUME-20261111: _run used to recompute it here),
    # instead of relying on each lane's default. The lanes keep
    # the same default for standalone runs; the explicit pass
    # makes this runner's intent auditable in its own source and
    # immune to a lane default drifting back to a wall-clock
    # offset.
    through_args = ["--through", panel_through] if panel_through else []
    # DEEP panel advance (cure G3 scheduling, 2026-10-30): the
    # DEEP panel (deep_bars.json) was built once ending 2026-10-28
    # and no lane advanced it; advance it BEFORE the binary store
    # rebuild below so the store derives from the freshest panel.
    # Non-fatal by the deep-binary pattern: a failed advance leaves
    # the prior panel on disk and the engines publish from it, so
    # the failure degrades freshness (named here, and the daily
    # audit's freshness surveillance flags a stale panel), never
    # correctness.
    if not skip("deep-panel-advance"):
        t0 = time.time()
        adv = subprocess.run(
            [sys.executable, str(HERE / "advance_deep_panel.py"),
             *through_args],
            capture_output=True, text=True)
        print(f"done deep-panel-advance in {time.time() - t0:.0f}s "
              f"exit {adv.returncode} (non-fatal)", flush=True)
        cp.mark("deep-panel-advance", adv.returncode, time.time() - t0)
        atail = (adv.stdout or adv.stderr or "").strip()[-500:]
        if atail:
            print(f"deep-panel-advance output: {atail}", flush=True)
    # VIX / VIX3M daily capture (hookup cure, 2026-10-30): the fear
    # family and Engine 1 read one VIX store that no lane advanced
    # (it ended 2026-10-21) and no VIX3M series existed, so Engine
    # 1's backwardation state was permanently no_data. Non-fatal by
    # the deep-panel pattern: a failed capture leaves the prior
    # store on disk and consumers publish their named stale states.
    if not skip("vix-capture"):
        t0 = time.time()
        vix = subprocess.run(
            [sys.executable, str(HERE / "capture_vix_daily.py")],
            capture_output=True, text=True)
        print(f"done vix-capture in {time.time() - t0:.0f}s "
              f"exit {vix.returncode} (non-fatal)", flush=True)
        cp.mark("vix-capture", vix.returncode, time.time() - t0)
        vtail = (vix.stdout or vix.stderr or "").strip()[-500:]
        if vtail:
            print(f"vix-capture output: {vtail}", flush=True)
    # DEEP binary store (DEEP runtime cure, 2026-10-30): keep the
    # derived binary panel store current before the engines run.
    # Non-fatal by design: build_deep_binary.py is a fast no-op
    # when the store already matches the panel fingerprint, and
    # the engines' shared reader falls back to mmap over the
    # panel JSON whenever no current store exists, so a failed
    # rebuild degrades speed, never correctness.
    if not skip("deep-binary-store"):
        t0 = time.time()
        conv = subprocess.run(
            [sys.executable, str(HERE / "build_deep_binary.py")],
            capture_output=True, text=True)
        print(f"done deep-binary-store in {time.time() - t0:.0f}s "
              f"exit {conv.returncode} (non-fatal)", flush=True)
        cp.mark("deep-binary-store", conv.returncode, time.time() - t0)
        if conv.returncode != 0:
            tail = (conv.stderr or conv.stdout or "").strip()[-500:]
            if tail:
                print(f"deep-binary-store output: {tail}", flush=True)
    # Publication record lanes (cures 2026-10-30): the earnings
    # record, the per name priced moves, the first minutes
    # acceptance record, the FE04 fair gap record and the Form 4
    # footnote record feed Engines 12, 28 and 10. Non-fatal by
    # the deep-binary pattern above: a failed lane leaves the
    # prior record on disk and the consumers publish their
    # honest not_recorded states, so a lane failure degrades
    # freshness, never correctness, and is named in the log.
    for label, argv in (
            ("earnings-record",
             [sys.executable, str(HERE / "earnings_record.py"),
              "--past", "10", "--forward", "60"]),
            # Priced moves and the earnings calendar moved after
            # the price panel advance below (PANEL-RESYNC-20261031):
            # priced_moves.py stamps each name's spot and
            # spot_session from the panel's last row, so running it
            # before the advance froze every name at the previous
            # session whenever the advance landed a new one. The
            # two lanes now run in the spine block, after the
            # advance and before the engines. The earnings
            # calendar still republishes from the fresh priced
            # record inside this cycle, before the engines run
            # (Engine refresh cure, 2026-10-30: Engine 12 recounts
            # the calendar's priced moves exactly from that
            # record, so the calendar must not lag it).
            ("first-minutes",
             [sys.executable, str(HERE / "first_minutes.py")]),
            ("fair-gap-model",
             [sys.executable, str(HERE / "fair_gap_model.py")]),
            ("form4-footnotes",
             [sys.executable, str(HERE / "form4_footnotes.py")]),
            # Stream C record lanes (2026-10-30): the FE12
            # session quality record (Engine 1's guard inputs),
            # the FE07 lead-lag estimation record and the FE21
            # XBRL route record. Same non-fatal pattern: a
            # failed lane leaves the prior record on disk and
            # consumers publish their named states.
            ("session-quality",
             [sys.executable, str(HERE / "build_session_quality.py")]),
            ("leadlag-record",
             [sys.executable, str(HERE / "build_leadlag_record.py")]),
            ("xbrl-route",
             [sys.executable, str(HERE / "build_xbrl_route.py")]),
            # Sweep stream 4 (2026-10-30): the FE04 news leg
            # estimation, run after the fair gap model above so
            # each new session's record is estimated against
            # the directed news record the same day.
            ("news-leg-estimation",
             [sys.executable, str(HERE / "estimate_news_leg.py")])):
        if skip(label):
            continue
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s "
              f"exit {r.returncode} (non-fatal)", flush=True)
        cp.mark(label, r.returncode, time.time() - t0)
        tail = (r.stdout or r.stderr or "").strip()[-500:]
        if tail:
            print(f"{label} output: {tail}", flush=True)
    # Spine first (cure G1/G2, 2026-10-29): advance the grading
    # price panel to the latest completed session (explicit
    # --through, PANEL-THROUGH-EXPLICIT-20261031), then grade
    # every matured forecast, before any engine page is refreshed.
    # Before this wiring the panel never advanced and no live
    # grading runner existed, so the ledger carried zero grades.
    for label, argv in (
            ("price-panel-advance",
             [sys.executable, str(HERE / "advance_price_panel.py"),
              *through_args]),
            ("forecast-grading",
             [sys.executable, str(ROOT / "forecast" / "run_grading.py")]),
            # Attestation recount (cure ATTESTATION-RECOUNT-20261031):
            # the registry calibration attestations are a derived
            # record of the ledger, regenerated from the void aware
            # recount right after grading and before any engine
            # page is refreshed, so every page published by this
            # run carries an attestation block that agrees with
            # the ledger it attests. Fatal like grading: a failed
            # recount must not publish stale attestations.
            ("attestation-refresh",
             [sys.executable,
              str(ROOT / "forecast" / "refresh_attestations.py"),
              "--registry-only"])):
        if skip(label):
            continue
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s exit {r.returncode}",
              flush=True)
        if r.stdout:
            print(r.stdout.strip()[-2000:], flush=True)
        if r.returncode != 0:
            fstr = f"{label} (exited {r.returncode})"
            failures.append(fstr)
            cp.mark(label, r.returncode, time.time() - t0, fstr)
            print("FAILURES: " + "; ".join(failures))
            return 1
        cp.mark(label, r.returncode, time.time() - t0)
    # Panel-derived publication lanes, after the panel advance
    # (PANEL-RESYNC-20261031): the priced move record stamps spot
    # and spot_session from the panel's last row per name, and the
    # earnings calendar republishes those priced moves. Non-fatal
    # by the record lane pattern above: a failed lane leaves the
    # prior record on disk and consumers publish from it, with the
    # failure named in the log.
    for label, argv in (
            ("priced-moves",
             [sys.executable, str(HERE / "priced_moves.py")]),
            ("earnings-calendar",
             [sys.executable, str(HERE / "refresh_earningscal.py")])):
        if skip(label):
            continue
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s "
              f"exit {r.returncode} (non-fatal)", flush=True)
        cp.mark(label, r.returncode, time.time() - t0)
        tail = (r.stdout or r.stderr or "").strip()[-500:]
        if tail:
            print(f"{label} output: {tail}", flush=True)
    # Board republishing (cure REFRESH-RESUME-20261111): the
    # Qualified Board page is an upstream input to the engine
    # loop (the abstention-signal leg's freshness check binds its
    # session to the panel's freshest, and the panel has just
    # advanced), but its republishing step ran only in the 19:00
    # tools refresh, after this runner, so the page the loop read
    # was the previous session's republication whenever the
    # morgue's board card had advanced that afternoon. Republish
    # it here, from the card, deterministically; a failed
    # republishing is a named failure of this run (the consumer
    # check downstream will fail closed on the stale page as
    # well, and both lines name the same cause).
    if not skip("board-republish"):
        print("start board-republish (refresh_board.py)", flush=True)
        t0 = time.time()
        r = subprocess.run(
            [sys.executable, str(HERE / "refresh_board.py")],
            capture_output=True, text=True)
        print(f"done board-republish in {time.time() - t0:.0f}s "
              f"exit {r.returncode}", flush=True)
        tail = (r.stdout or r.stderr or "").strip()[-500:]
        if tail:
            print(f"board-republish output: {tail}", flush=True)
        if r.returncode != 0:
            fstr = (f"board-republish (refresh_board.py exited "
                    f"{r.returncode})")
            failures.append(fstr)
            cp.mark("board-republish", r.returncode,
                    time.time() - t0, fstr)
        else:
            cp.mark("board-republish", r.returncode, time.time() - t0)
    slugs = engine_slugs()
    order += slugs + list(FINAL_STEPS)
    for slug in slugs:
        script = scripts.get(norm(slug))
        if script is None:
            continue  # upstream tool page, refreshed by its own lane
        if skip(slug):
            ran.append(slug)
            continue
        print(f"start {slug} ({script.name})", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        print(f"done {slug} in {time.time() - t0:.0f}s exit {r.returncode}", flush=True)
        if r.returncode != 0:
            fstr = f"{slug} ({script.name} exited {r.returncode})"
            failures.append(fstr)
            cp.mark(slug, r.returncode, time.time() - t0, fstr)
            # Name the failure, not just the count (cure G17,
            # 2026-10-29): the runner used to discard the
            # refresher's own output, so a failed leg's reason was
            # unrecoverable from the run log.
            tail = (r.stderr or r.stdout or "").strip()[-800:]
            if tail:
                print(f"failure output {slug}: {tail}", flush=True)
        else:
            cp.mark(slug, r.returncode, time.time() - t0)
            ran.append(slug)
    # Attestation resync (cure WEEK-READINESS-R2-20261102-N): the
    # engines above appended new rows to the ledger during the
    # loop, so the attestations they attached at write time no
    # longer recount against the final ledger and the smoke check
    # fails on an otherwise clean run. Recount the registry on the
    # final ledger, then re-attach every page's block from it.
    # Fatal like the first recount: publishing stale attestations
    # is the defect this cures, never a state to ship.
    for label, argv in (
            ("attestation-refresh-final",
             [sys.executable,
              str(ROOT / "forecast" / "refresh_attestations.py"),
              "--registry-only"]),
            ("attestation-reattach",
             [sys.executable, str(HERE / "reattach_attestations.py")])):
        if skip(label):
            continue
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s "
              f"exit {r.returncode}", flush=True)
        if r.stdout:
            print(r.stdout.strip()[-1000:], flush=True)
        if r.returncode != 0:
            fstr = f"{label} (exited {r.returncode})"
            failures.append(fstr)
            cp.mark(label, r.returncode, time.time() - t0, fstr)
        else:
            cp.mark(label, r.returncode, time.time() - t0)
    if skip("record"):
        rec_code = 0
    else:
        t0 = time.time()
        rec = subprocess.run([sys.executable, str(HERE / "refresh_record.py")],
                             capture_output=True, text=True)
        rec_code = rec.returncode
        if rec.returncode != 0:
            fstr = f"record (refresh_record.py exited {rec.returncode})"
            failures.append(fstr)
            cp.mark("record", rec.returncode, time.time() - t0, fstr)
        else:
            cp.mark("record", rec.returncode, time.time() - t0)
    # Record-surface cure (2026-10-31): every page's data must carry
    # its full record before the smoke check verifies the tree.
    if skip("record-enrich"):
        enr_code = 0
    else:
        t0 = time.time()
        enr = subprocess.run([sys.executable, str(HERE / "enrich_all.py")],
                             capture_output=True, text=True)
        enr_code = enr.returncode
        print(f"record-surface enrich exit {enr.returncode}", flush=True)
        if enr.returncode != 0:
            fstr = "record-surface enrich (enrich_all.py) failed"
            failures.append(fstr)
            cp.mark("record-enrich", enr.returncode, time.time() - t0, fstr)
        else:
            cp.mark("record-enrich", enr.returncode, time.time() - t0)
    if skip("smoke"):
        smoke_code = 0
    else:
        t0 = time.time()
        smoke = subprocess.run(["bash", str(HERE / "verify_terminal.sh")],
                               capture_output=True, text=True)
        smoke_code = smoke.returncode
        if smoke.returncode != 0:
            fstr = "smoke check (verify_terminal.sh) failed"
            failures.append(fstr)
            cp.mark("smoke", smoke.returncode, time.time() - t0, fstr)
        else:
            cp.mark("smoke", smoke.returncode, time.time() - t0)
    # Publish step (serve-live route, 2026-10-31): after verify, prove
    # the always-on server serves this exact tree (publish_live.py).
    if skip("publish-live"):
        pub_code = 0
    else:
        t0 = time.time()
        pub = subprocess.run([sys.executable, str(HERE / "publish_live.py")],
                             capture_output=True, text=True)
        pub_code = pub.returncode
        print(f"publish-live proof exit {pub.returncode}", flush=True)
        if pub.returncode != 0:
            fstr = "publish proof (publish_live.py) failed"
            failures.append(fstr)
            cp.mark("publish-live", pub.returncode, time.time() - t0, fstr)
        else:
            cp.mark("publish-live", pub.returncode, time.time() - t0)
    # The run's verdict is the session's state, not this
    # invocation's alone (cure REFRESH-RESUME-20261111): failures
    # an earlier invocation recorded stand until their step's
    # retry clears them, and a run that reaches this summary with
    # none left is the settled run, so its checkpoint completes.
    failures = cp.ordered_failures(order)
    cp.complete = not failures
    cp.save()
    # Provenance stamp (R-09 cure, 2026-10-30): this runner
    # publishes no page of its own, so its run summary is the
    # record it stamps, the same shipyard stamp every refresher
    # it runs carries on its page.
    summary = {"runner": "refresh_engines.py",
               "engines_refreshed": len(ran), "pages": ran,
               "failures": failures}
    summary = _tc.stamp_for_script(summary, __file__) \
        if _tc is not None else summary
    print(f"run provenance: feed={summary.get('feed')} "
          f"price_basis={summary.get('price_basis')} "
          f"execution_pricing={summary.get('execution_pricing')}")
    print(f"engines refreshed: {len(ran)}")
    print("pages: " + ", ".join(ran))
    print("record refreshed: " + ("yes" if rec_code == 0 else "NO"))
    print("smoke check: " + ("passed" if smoke_code == 0 else "FAILED"))
    if failures:
        print("FAILURES: " + "; ".join(failures))
        return 1
    print("FAILURES: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
