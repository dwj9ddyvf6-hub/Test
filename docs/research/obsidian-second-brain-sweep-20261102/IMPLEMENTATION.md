# IMPLEMENTATION: Obsidian second-brain sweep, ADOPT A1 to A6

Implemented: 2026-11-02, by the implementation pass named in
SYNTHESIS.md Section 5. Scope held: only the six ADOPT packages,
native reimplementation, no MEMORY.md edit, no desk strategy, sizing,
stops, thresholds, or Tensor touch, no public save, no secret written
to any note (the secrets-in-memory tip stays REJECTED per SYNTHESIS
Section 4, R1 and R2, and was not implemented in any form).

Final test evidence (re-run after the last code change, on the final
files): `python3 -m pytest test_research_capture.py
test_check_evidence.py test_freshness_lint.py test_verify_quotes.py
test_claim_ledger.py -q` in ~/workspace/tools: 24 passed.
Bug log: OBSIDIAN-SWEEP-TOOLING-20261102 in
~/workspace/midna-book/BUGLOG_2026-11-02.md, naming all five test
files as the regression blockers.

## A1. Content-addressed research source capture: GREEN

Files:
- ~/workspace/tools/research_capture.py
- ~/workspace/tools/test_research_capture.py (3 tests, passed)
- ~/workspace/research_notes/RESEARCH-INGEST.md (bounded queue,
  oldest first, stop and report over 20 pending; the four
  dispositions in the exact machine-readable form; compilation-value
  gate; fixed report shape; locate-before-write rule from A2)
- This program: sources/raw/synthesis.md,
  sources/MANIFEST.json, INGEST-LOG.md (with Gaps section)

Proof executed:
- Duplicate capture is a no-op: second capture of SYNTHESIS.md
  returned status already_captured, manifest still 1 entry, one file
  in sources/raw/.
- Changed content creates a second dated capture with the first
  byte-identical on readback: covered in test_research_capture.py.
- Manifest hash equals an independent sha256sum of the captured file:
  manifest sha256 0c1c92c5d4c4ebda3abfd280282ba991ac2ffe645236f053a
  959c39b1f27ac98 (line-wrapped here) equals `sha256sum
  sources/raw/synthesis.md` run in this pass.

## A2. Report-only grounding verifier: GREEN

Files:
- ~/workspace/tools/check_evidence.py
- ~/workspace/tools/test_check_evidence.py (5 tests, passed,
  including the fail direction: planted altered number 43,000 flagged
  as a suspect; verbatim page clean; missing source field an evidence
  error; No material capture not reported unreferenced; malformed
  Status block flagged)
- Locate-before-write rule: in RESEARCH-INGEST.md (A1 file, above).

Proof executed: first live run over this sweep's folder filed at
A2-LIVE-RUN.md in this folder: pages=9, suspects=0,
evidence_errors=10, unreferenced=1, every suspect and error judged
individually in that report (no fidelity suspects arose; the errors
are pre-adoption format gaps and two correctly flagged in-repo paths
of an audited repo, each named with its judgment).

## A3. Freshness lint and verified-claim package: GREEN

Files:
- ~/workspace/tools/freshness_lint.py
- ~/workspace/tools/test_freshness_lint.py (7 tests, passed,
  including fail direction: planted unstamped claim errors FRESH-1,
  aged stamp listed FRESH-2, broken proof pointer errors FRESH-3)
- Live run filed: A3-LIVE-RUN.txt in this folder (final counts
  FRESH-1=6, FRESH-2=0, FRESH-3=0, due=0 after processing below; the
  6 FRESH-1 lines are named in that file and stay open for M10).
- Claim-class fields: first carrying line added to
  ~/workspace/midna-book/memory/STATE.md (Midna's book row):
  asserts-current-behavior: true; verified: 2026-11-02 (stamped only
  after the evidence loop below).
- Wiring: cron midna-daily-full-audit gained step 15 (M10) via
  cron.update preserving the existing body, schedule (daily 21:46
  America/New_York) and delivery; verified with cron.view after the
  update (step 15 present verbatim, schedule and delivery unchanged).
- MEMORY-SYSTEM.md Section 8.5 amended in the same pass to record
  M10 (~/workspace/research_notes/midna-trader-formation-20261029/
  MEMORY-SYSTEM.md).

Proof executed (due claim end to end): the first computed due list
showed STATE.md line 12 DUE (never verified). Evidence loop in
~/workspace/midna-book/reviews/WEEKLY-2026-W45.md: read-only evidence
(ledger.json: cash 100000.0, positions [], fills []), verdict
supports, stamp applied to the register line and read back; the
STATE.md headline (line 7) and the CONTEXT-SNAPSHOT.md line carrying
the claim (line 14) both checked and in agreement, so no atomic
correction was triggered. Note on scope: register paths on disk are
~/workspace/midna-book/memory/STATE.md and
~/workspace/midna-book/CONTEXT-SNAPSHOT.md; the synthesis shorthand
(STATE.md, CONTEXT-SNAPSHOT.md) names these files.

## A4. Verbatim quote-proof gate: GREEN

Files:
- ~/workspace/tools/verify_quotes.py
- ~/workspace/tools/test_verify_quotes.py (3 tests, passed: exact
  quote passes, one-character mutation fails, quote under 12
  characters refused)
- Gate rule written into the weekly review agenda record:
  ~/workspace/midna-book/reviews/WEEKLY-2026-W45.md, A4 section,
  including its Dropped as unproven list.

Proof executed: that review file shows the gate in use on a real
pair (STATE.md line 7 vs CONTEXT-SNAPSHOT.md line 14): both quotes
PASS (exact line match, tool output recorded in the review). The
pair proved consistent, so no contradiction was actioned.
Dropped as unproven list: empty, and the review says so explicitly.

## A5. Machine-readable claim ledger: GREEN

Files:
- ~/workspace/research_notes/claim-ledger.json (schema header,
  empty entries list)
- ~/workspace/tools/claim_ledger.py (validator only, writes nothing)
- ~/workspace/tools/test_claim_ledger.py (6 tests, passed:
  syndicated copies sharing one independence_key fail the high-risk
  rule; two distinct keys pass; past refresh_due reported STALE by
  computation and never stored; unsupported validates clean;
  accepted without a fresh non-synthetic source fails; contradiction
  not marked contested fails)

Proof executed: the live ledger validates clean at creation:
`claim_ledger.py research_notes/claim-ledger.json` returned
entries=0, errors=0, warnings=0, exit 0. First real entries are left
to a research pass citing A1 sources, per spec.

## A6. Research page hygiene convention: GREEN

File:
- ~/workspace/research_notes/RESEARCH-CONVENTIONS.md (all six items:
  three-tier lint authority table, Status block micro-format,
  cascade step, archived-answer class, Gaps, synthesis page
  contract), cited from RESEARCH-INGEST.md (A1).

Proof executed: demonstration lint pass over this sweep's folder
filed at A6-DEMO-LINT.md in this folder, listing Safe Fixes applied
(none, each rule's reason recorded, including the zero-match filename
search for the two dead AUDIT-5 links, reported never guessed),
Mechanical Reports (the A2 live run), and Judgment Reports
separately, with no Judgment item fixed by the pass.

## Blocked items

None. All six ADOPT items were implemented inside the rails.
Open rows carried forward, named not hidden: the 6 FRESH-1 lines in
A3-LIVE-RUN.txt (unstamped quantitative lines in the registers, now
tracked nightly by M10); the A2 format gaps in A2-LIVE-RUN.md
(pre-adoption audit pages carry no Sources field form); the weekly
review file WEEKLY-2026-W45.md is a partial review opened for the
A3/A4 proofs, with the Friday Section 7.4 agenda still due at the
Friday review run.
