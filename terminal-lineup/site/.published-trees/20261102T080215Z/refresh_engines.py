#!/usr/bin/env python3
"""Daily refresh runner for the 30 forecast engines plus the Record.

Scope (the owner's approval, 2026-10-29): every forecast-engine page in the
terminal, plus the Record page, then the terminal smoke check.

The engine slug set is derived from the program record
(FORECAST30-PROGRESS.md, the site/<slug>/ paths its build lines name),
minus the Record itself and minus pages with no matching refresh script
(those are upstream tools the engines read, refreshed by their own
lanes). Each engine's refresher is site/refresh_<slug, dashes removed>.py
where that naming holds; an engine slug with no matching script is a
named failure, never silently skipped.

Exit code is nonzero when any refresher, the Record, or the smoke check
fails. The report names failures individually.

Proof log (cure REFRESH-PROOF-LOG-20261031): every run, scheduled or
manual, writes its own full output to terminal-lineup/
refresh_proof.log under a dated header naming the exit code, so the
final state carries the evidence of the last run instead of relying
on a cron result summary or a stale hand kept log. Before this cure
the log still held the 2026-10-30 02:57 run with 17 failures and no
later run updated it.
"""
import contextlib
import io
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROGRESS = ROOT / "FORECAST30-PROGRESS.md"
PROOF_LOG = ROOT / "refresh_proof.log"


class _Tee(io.TextIOBase):
    """Mirror everything printed during a run to a buffer, so the
    run can file its own proof log at the end."""

    def __init__(self, real):
        self._real = real
        self.buffer = io.StringIO()

    def write(self, s):
        self.buffer.write(s)
        return self._real.write(s)

    def flush(self):
        return self._real.flush()


def write_proof_log(text: str, exit_code: int,
                    path: Path = PROOF_LOG) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (f"# refresh_engines.py run finished {stamp} "
              f"exit {exit_code}\n")
    path.write_text(header + text, encoding="utf-8")


def main() -> int:
    tee = _Tee(sys.stdout)
    code = 1
    try:
        with contextlib.redirect_stdout(tee):
            code = _run()
    finally:
        write_proof_log(tee.buffer.getvalue(), code)
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


def _run() -> int:
    scripts = {norm(f.stem.replace("refresh_", "")): f for f in HERE.glob("refresh_*.py")}
    failures: list[str] = []
    ran: list[str] = []
    import time
    # Panel through date (PANEL-THROUGH-EXPLICIT-20261031): the
    # advance lanes are invoked with an explicit --through naming
    # the freshest completed session, computed once here, instead
    # of relying on each lane's default. The lanes keep the same
    # default for standalone runs; the explicit pass makes this
    # runner's intent auditable in its own source and immune to a
    # lane default drifting back to a wall-clock offset.
    try:
        sys.path.insert(0, str(HERE))
        from completed_session import freshest_completed_session
        panel_through = freshest_completed_session()
    except Exception:
        panel_through = None
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
    t0 = time.time()
    adv = subprocess.run(
        [sys.executable, str(HERE / "advance_deep_panel.py"),
         *through_args],
        capture_output=True, text=True)
    print(f"done deep-panel-advance in {time.time() - t0:.0f}s "
          f"exit {adv.returncode} (non-fatal)", flush=True)
    atail = (adv.stdout or adv.stderr or "").strip()[-500:]
    if atail:
        print(f"deep-panel-advance output: {atail}", flush=True)
    # VIX / VIX3M daily capture (hookup cure, 2026-10-30): the fear
    # family and Engine 1 read one VIX store that no lane advanced
    # (it ended 2026-10-21) and no VIX3M series existed, so Engine
    # 1's backwardation state was permanently no_data. Non-fatal by
    # the deep-panel pattern: a failed capture leaves the prior
    # store on disk and consumers publish their named stale states.
    t0 = time.time()
    vix = subprocess.run(
        [sys.executable, str(HERE / "capture_vix_daily.py")],
        capture_output=True, text=True)
    print(f"done vix-capture in {time.time() - t0:.0f}s "
          f"exit {vix.returncode} (non-fatal)", flush=True)
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
    t0 = time.time()
    conv = subprocess.run(
        [sys.executable, str(HERE / "build_deep_binary.py")],
        capture_output=True, text=True)
    print(f"done deep-binary-store in {time.time() - t0:.0f}s "
          f"exit {conv.returncode} (non-fatal)", flush=True)
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
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s "
              f"exit {r.returncode} (non-fatal)", flush=True)
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
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s exit {r.returncode}",
              flush=True)
        if r.stdout:
            print(r.stdout.strip()[-2000:], flush=True)
        if r.returncode != 0:
            failures.append(f"{label} (exited {r.returncode})")
            print("FAILURES: " + "; ".join(failures))
            return 1
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
        print(f"start {label}", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, capture_output=True, text=True)
        print(f"done {label} in {time.time() - t0:.0f}s "
              f"exit {r.returncode} (non-fatal)", flush=True)
        tail = (r.stdout or r.stderr or "").strip()[-500:]
        if tail:
            print(f"{label} output: {tail}", flush=True)
    for slug in engine_slugs():
        script = scripts.get(norm(slug))
        if script is None:
            continue  # upstream tool page, refreshed by its own lane
        print(f"start {slug} ({script.name})", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        print(f"done {slug} in {time.time() - t0:.0f}s exit {r.returncode}", flush=True)
        if r.returncode != 0:
            failures.append(f"{slug} ({script.name} exited {r.returncode})")
            # Name the failure, not just the count (cure G17,
            # 2026-10-29): the runner used to discard the
            # refresher's own output, so a failed leg's reason was
            # unrecoverable from the run log.
            tail = (r.stderr or r.stdout or "").strip()[-800:]
            if tail:
                print(f"failure output {slug}: {tail}", flush=True)
        else:
            ran.append(slug)
    rec = subprocess.run([sys.executable, str(HERE / "refresh_record.py")],
                         capture_output=True, text=True)
    if rec.returncode != 0:
        failures.append(f"record (refresh_record.py exited {rec.returncode})")
    # Record-surface cure (2026-10-31): every page's data must carry
    # its full record before the smoke check verifies the tree.
    enr = subprocess.run([sys.executable, str(HERE / "enrich_all.py")],
                         capture_output=True, text=True)
    print(f"record-surface enrich exit {enr.returncode}", flush=True)
    if enr.returncode != 0:
        failures.append("record-surface enrich (enrich_all.py) failed")
    smoke = subprocess.run(["bash", str(HERE / "verify_terminal.sh")],
                           capture_output=True, text=True)
    if smoke.returncode != 0:
        failures.append("smoke check (verify_terminal.sh) failed")
    # Publish step (serve-live route, 2026-10-31): after verify, prove
    # the always-on server serves this exact tree (publish_live.py).
    pub = subprocess.run([sys.executable, str(HERE / "publish_live.py")],
                         capture_output=True, text=True)
    print(f"publish-live proof exit {pub.returncode}", flush=True)
    if pub.returncode != 0:
        failures.append("publish proof (publish_live.py) failed")
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
    print("record refreshed: " + ("yes" if rec.returncode == 0 else "NO"))
    print("smoke check: " + ("passed" if smoke.returncode == 0 else "FAILED"))
    if failures:
        print("FAILURES: " + "; ".join(failures))
        return 1
    print("FAILURES: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
