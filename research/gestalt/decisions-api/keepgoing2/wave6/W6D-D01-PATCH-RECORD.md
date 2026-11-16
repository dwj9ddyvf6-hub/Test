# W6D D-01 REJECT PAYLOAD PATCH RECORD

Wave 6 Lane D, 2026-11-15. Spec:
keepgoing2/wave5/W5D-REJECT-PAYLOAD-SPEC.md. Work done on a copy
only; the live desk tree was never written.

SCOPE: Surface, desk3/dispatcher.py reject rows on the copy plus
one new blocker test file. Constraints, live tree frozen and
read only, no Tensor engine files, no saty files, no strategy,
gate, sizing, or threshold logic changed. Outcome, every
intent_rejected row carries the spec section 3 stamp from one
helper at both reject sites. Proof, fail-first blocker, blocker
pass on the patched copy, one full gate run on the copy, patch
applies clean to the live tree, live tree verified untouched.
Edges, grading unlock is forward only, no backfill.

## 1. The copy

- Source: ~/workspace/muse-desk-v3 at HEAD
  3e474e1f03d872a34c7e9c7562921aea15530035.
- Destination: keepgoing2/wave6/desk-copy/, full copy including
  .git and all of state/ (2.5G, 9,464 files on both sides,
  counted). NO exclusions: the gate demonstrably reads real state
  (state/snapshots/*.json in test_gate_distance_20261114_blockers
  and test_f4_crypto_barkey_20261114_blockers,
  state/warm_bars.json in the investandbefree tests,
  state/daily20/ in the tensor daily20 tests), so nothing was
  left out and no exclusion had to be justified.
- Copy integrity: file counts equal (9,464 and 9,464),
  desk3/dispatcher.py sha256 identical on both sides at copy time
  (65703151b9f6240059d37c4f1141fe2951af0d7a1c5db48a7b618f6fa432dfd9),
  diff -qr clean on desk3/ and tests/.
- One copy blemish, recorded: cp -a exited 1 with "failed to
  preserve ownership" warnings (source files are root owned).
  Contents copied completely, as the counts and hashes above
  prove; only ownership metadata differs on the copy.

## 2. Spec to code mapping

All changes are in desk3/dispatcher.py, insertions only.

| Spec item | Code |
|---|---|
| Section 2, one helper, both sites | New method Dispatcher._reject_stamp(intent); _reject() merges it with row.update(self._reject_stamp(intent)); the inline insufficient_options_bp_csp site merges it identically before append_line. A grep of the patched file confirms exactly two intent_rejected construction sites (the _reject row and the CSP row), and both are stamped. The pending_drain_deferred row is a different event and is out of scope. |
| ts_utc, never null, dispatcher clock | From self._now_fn() (the dispatcher's injectable clock), converted to UTC, formatted YYYY-MM-DDTHH:MM:SSZ. |
| symbol, side, kind, qty copied from the intent | Copied verbatim when well formed (symbol a non-empty string, side buy or sell, kind entry or exit, qty a non-bool number greater than 0). |
| reference_price precedence, section 4 steps 1 to 3 | price_hint, then limit_price, then stop_price, each only when a non-bool number greater than 0; sources intent_price_hint, intent_limit_price, intent_stop_price. |
| Section 4 step 4, dispatcher held quote mid | Reads the dispatcher's _quote_mids mapping when it holds one, source dispatcher_quote_mid_at_reject. Named design note: the production dispatcher today holds NO quote mid store, so this step does not fire in production and rows fall through to step 5. Its price_lookup is a last bar close, not a mid, and was deliberately NOT relabeled as a mid; no new fetch was introduced (the spec forbids fetching and backfill). The branch is proven by a blocker test that installs a held mid. |
| Section 4 step 5 and section 5, never silent omission | reference_price null with reference_price_source "unavailable"; every unavailable graded field is an explicit null, named in missing_fields, with missing_reason in plain words (for example "intent carried no symbol", "intent qty was malformed", "no price on intent and no quote held at reject time"). A malformed qty or kind (the bad_qty and bad_kind path) is stamped null on the same rule. missing_reason is null exactly when missing_fields is empty. |
| stamp_version | Constant integer 1 on every stamped row. |
| Existing fields and extras retained | event, intent_id, sleeve, reason unchanged; reconcile_halt still merges _halt_context (discrepancies, cash_halt) and its symbol line; the CSP row keeps required_collateral_usd and options_buying_power_usd. Proven by blocker assertions on both. |
| Stamp is read only | The helper copies fields and never mutates the intent; a blocker test deep-compares the intent before and after. No reject logic, reason, ordering, or order flow changed: the dispatcher diff is 97 insertions and 0 deletions. |

## 3. Fail-first evidence (blocker on the UNPATCHED copy)

Blocker written first, at the desk suite's own location and in
its style: tests/test_d01_reject_payload_20261115_blockers.py
(13 tests). The gate discovers tests/test_*_blockers.py, so the
file is wired into run_regression_blockers.sh by name, per spec
acceptance check 2; no gate script edit was needed or made.

Command: python3 -m unittest
tests.test_d01_reject_payload_20261115_blockers -v
Run against the unpatched copy, exit 1. Verbatim tail:

```text
Ran 13 tests in 0.041s

FAILED (failures=12)
```

Every failure is the same seam absence, first assertion verbatim
(from the CSP test): "AssertionError: 'ts_utc' not found in
{'event': 'intent_rejected', 'intent_id': 'd01-csp-1',
'options_buying_power_usd': 10000.0, 'reason':
'insufficient_options_bp_csp', 'required_collateral_usd':
49700.0, 'sleeve': 'qqq_put_ladder', 'symbol':
'QQQ261204P00500000'} : stamped key absent: ts_utc". The 12
failing tests cover both reject paths, all precedence steps, and
the never-silent-omission cases. The 1 passing test is
test_stamp_does_not_mutate_intent, a preservation invariant that
correctly passes in both directions. Full verbatim output:
keepgoing2/wave6/W6D-D01-FAILFIRST.log (156 lines).

## 4. Blocker on the patched copy

Same command on the patched copy, and repeated once more after
the final diff was staged (the tested artifact is the delivered
artifact):

```text
Ran 13 tests in 0.025s

OK
```

## 5. Full gate on the patched copy (run once)

Canonical route, found in the repo: ./run_regression_blockers.sh
(the script whose receipt at live HEAD 3e474e1 reads "Ran 2249
tests in 110.653s", exit 0, run_id 20261114T230122Z-16791).

Receipt on the copy, state/gate_receipts/receipts.jsonl, run_id
20261115T051900Z-15059:

```text
Ran 2262 tests in 117.180s
FAILED (errors=2)
gate exit code 1
```

Count arithmetic: 2,249 baseline plus the 13 new D-01 blockers
equals 2,262, as run. The 2 errors, both proven copy-location
artifacts and neither touching the dispatcher:

1. test_feed80_timing_20261114_blockers
   test_builder_stamps_reconstruction_provenance:
   FileNotFoundError for
   ".../keepgoing2/wave6/research_notes/sleeve-activation-calibration-20261111/build_timing_signals_drop.py".
   The test resolves a sibling research_notes path from the desk
   root; nested under wave6 that path does not exist.
   Discriminator: with the patch stashed, the same module run on
   the copy fails with the identical error.
2. test_supervision_harden_20261114_blockers
   test_notify_delivers_datagram: OSError AF_UNIX path too long
   at srv.bind(path). The gate redirects TMPDIR under the repo;
   at the copy's deep path the socket path exceeds the AF_UNIX
   limit. Discriminator: with a gate-length TMPDIR the module
   errors identically patched and unpatched (errors=1 both ways),
   and passes at a normal TMPDIR length.

Gate verdict, exact: PARTIAL on the copy. 2,260 of 2,262 tests
pass, including all 13 new blockers; the 2 named errors are
proven independent of the patch and are functions of the copy's
path, which disappears when the patch lands at the live path. A
clean full gate at the live path is an open row for the landing
lane (section 7), not a claim made here. The gate was run once,
per the one-heavy-job rail.

## 6. The patch

File: keepgoing2/wave6/W6D-D01-PAYLOAD-PATCH.diff, a git diff
against HEAD 3e474e1 (staged diff on the copy), 392 lines.

```text
desk3/dispatcher.py                                |  97 +++
tests/test_d01_reject_payload_20261115_blockers.py | 267 +++
2 files changed, 364 insertions(+), 0 deletions
```

No Tensor engine file and no saty file appears in the diff (the
diff's file list is the two files above; a grep for tensor or
saty over the patch returns 0). Verified applicable to the live
tree with git apply --check, which passed (check only, nothing
landed).

## 7. Landing note and open rows

- LANDING: the patch rides the next desk cure window. Landing
  steps for that lane: apply W6D-D01-PAYLOAD-PATCH.diff at HEAD
  3e474e1 (or rebase the two files if HEAD has moved), add the
  dated BUGLOG entry per the desk bug log law, and run
  ./run_regression_blockers.sh at the live path, where the two
  copy-location errors cannot occur, before calling it landed.
- GRADING UNLOCK AFTER LANDING: after 5 sessions of stamped
  rows, reconcile_halt and insufficient_slice_bp are gradeable
  by class at cluster level (sleeve, symbol, session), per spec
  sections 8 and 9, from the rows alone with no fill ledger
  reconstruction; spec acceptance check 3 is the live re-census
  over new rows only (100 percent stamp_version 1; symbol share
  100 percent minus exactly the rows whose missing_fields names
  symbol). Legacy rows stay ungradeable; no backfill.
- OPEN ROW 1: full clean gate at the live path, owed at landing
  (see section 5).
- OPEN ROW 2: reference_price step 4 (dispatcher quote mid) is
  dormant in production until a dispatcher actually holds a
  quote mid store; rows without an intent price stamp
  "unavailable" with the reason named, per spec, in the
  meantime.
- OPEN ROW 3: the 5-session live re-census above, owed after
  landing.

## 8. Live tree verification (final, after all work)

Run in ~/workspace/muse-desk-v3 at the end:

```text
$ git rev-parse HEAD
3e474e1f03d872a34c7e9c7562921aea15530035
$ git status --porcelain
(clean, no output)
```

STATUS: PARTIAL, bounded portion proven (blocker fail-first and
pass, patch clean and applicable, 2,260 of 2,262 gate tests on
the copy), the rest named open in section 7. EVIDENCE POINTER:
this record, sections 3 to 6 and 8;
keepgoing2/wave6/W6D-D01-PAYLOAD-PATCH.diff;
keepgoing2/wave6/W6D-D01-FAILFIRST.log; the copy's gate receipt
state/gate_receipts/unittest-20261115T051900Z-15059.log inside
keepgoing2/wave6/desk-copy/.
