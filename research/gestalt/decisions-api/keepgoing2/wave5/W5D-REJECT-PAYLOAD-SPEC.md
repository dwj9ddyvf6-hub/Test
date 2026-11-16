# W5-6 D-01 REJECT PAYLOAD SPEC

Dated 2026-11-14. Wave 5 Lane D. Spec only: this document makes
no desk edit. It is written precisely enough for the desk lane
to land the change without further design decisions. Source of
the finding: keepgoing2/wave4/V3-REJECT-COUNTERFACTUAL.md,
section 4 (the named cure), with the seam verified tonight
against the live dispatcher source, read only.

## 1. The defect, in census numbers

Snapshot 2026-11-15T03:22:10Z (Wave 4 V3 census, reproduced
across two full runs): 29,360 intent_rejected rows in the
dispatcher journal and its rotations.

- Only 7,023 rows (23.9 percent) carry a symbol at all, and
  those are exactly the reconcile_halt rows.
- No reject row of any class carries side, kind, quantity, or
  reference price.
- All 760 insufficient_slice_bp rows are ungradeable by
  construction: nothing about what was blocked can be recovered
  from any persisted per-intent payload.
- Only reconcile_halt (7,023 rows) is gradeable at all today,
  and even it required reconstructing side from the fill ledger
  under a long convention.
- Net: 76.1 percent of the reject book is ungradeable by
  construction. The corpus finding, not any trading verdict, is
  what this spec cures.

## 2. Where the stamp is written: the reject seam

Verified in the desk source tonight (read only):
desk3/dispatcher.py, method _reject(self, intent, sleeve_id,
reason), builds the row dict {"event": "intent_rejected",
"intent_id": ..., "sleeve": sleeve_id, "reason": reason} and
appends it with append_line(self.djournal, row). That is the
primary seam: the stamp is added inside _reject, to the row,
from the intent dict itself, before append_line is called. The
intent dict at that point already carries symbol, side, kind,
qty, limit_price, price_hint, stop_price, and position_intent;
nothing needs to be fetched to stamp the first four fields.

One direct construction site exists outside _reject and must
receive the identical stamp: the insufficient_options_bp_csp
row built inline in the submit path (it already carries symbol
and two class-specific fields). Implementation rule for the
desk lane, no discretion left: factor the stamp into one helper
on the dispatcher, _reject_stamp(intent), returning the field
dict of section 3; _reject merges it into its row, the inline
site merges it into its row, and any future site that writes an
intent_rejected row must merge the same helper's output. A row
written without the stamp after landing is a defect, not a
variant.

The stamp is read-only with respect to the intent: it copies
fields, it never mutates the intent, never changes reject
logic, reasons, ordering, or order flow, and it is O(1) per
reject.

## 3. The fields

Every intent_rejected row written after landing carries all of
the following keys on every row, of every class. Types are
JSON types as written to the JSONL journal.

| field | type | source and rule |
|---|---|---|
| event | string | Existing. Constant "intent_rejected". |
| intent_id | string or null | Existing. intent.get("intent_id"), as today. The legacy intent_id format (no embedded timestamp) stops being emitted as part of this change, per the V3 cure; where a legacy id still arrives from upstream, it is copied verbatim and ts_utc below carries the time. |
| ts_utc | string | NEW. The explicit event timestamp the V3 cure requires, so no consumer parses time out of intent_id. ISO 8601 UTC, format YYYY-MM-DDTHH:MM:SSZ, from the dispatcher's own clock at the moment of rejection. Never null. |
| sleeve | string | Existing. The sleeve_id argument, as today. |
| reason | string | Existing field, and it IS the reject class. Values are the dispatcher's reason strings; the census classes are reconcile_halt, insufficient_slice_bp, insufficient_options_bp_csp, exit_already_resting_at_broker, exit_satisfied_no_broker_position, exit_satisfied_no_sleeve_position, exit_blocked_opposite_side_resting, bad_qty, bad_kind. New classes use new strings; the field name does not change, for compatibility with every existing consumer. |
| symbol | string or null | NEW for all classes (exists today only on reconcile_halt rows and the inline options site). intent.get("symbol"), copied verbatim: ticker for equities, OCC code for options, pair string for crypto, exactly as the intent carries it. |
| side | string or null | NEW. intent.get("side"), copied verbatim (the dispatcher's own values, buy or sell). Never inferred, never reconstructed from position state. |
| kind | string or null | NEW. intent.get("kind"), copied verbatim (the dispatcher's own kind values, including entry and exit kinds and position_intent distinctions the intent itself carries). Never remapped. |
| qty | number or null | NEW. intent.get("qty") as a JSON number. |
| reference_price | number or null | NEW. The price the blocked intent was referenced against at reject time, by the precedence in section 4. |
| reference_price_source | string | NEW. Names where reference_price came from; one of the section 4 values, including "unavailable" when the price is null. Never null, never omitted. |
| missing_fields | array of strings | NEW. Names every field among symbol, side, kind, qty, reference_price that is null on this row. Empty array when nothing is missing. |
| missing_reason | string or null | NEW. Null when missing_fields is empty; otherwise one string naming why the fields are unavailable (for example "intent carried no symbol", "no price on intent and no quote held at reject time"). |
| stamp_version | integer | NEW. Constant 1 on every stamped row, so graders can separate stamped rows from legacy rows mechanically. |
| cash_halt, discrepancies | as today | Existing reconcile_halt extras, retained unchanged on that class. Other class-specific extras (for example required_collateral_usd and options_buying_power_usd on insufficient_options_bp_csp) are retained unchanged. |

Row shape, one stamped insufficient_slice_bp row (the class
that is ungradeable today), shown in full:

{"event": "intent_rejected", "intent_id": "<id>", "ts_utc":
"2026-11-16T14:03:22Z", "sleeve": "<sleeve_id>", "reason":
"insufficient_slice_bp", "symbol": "<ticker>", "side": "buy",
"kind": "<kind>", "qty": 12.5, "reference_price": 148.20,
"reference_price_source": "intent_price_hint",
"missing_fields": [], "missing_reason": null,
"stamp_version": 1}

## 4. The reference price and its named source

Precedence, first match wins, evaluated at reject time inside
the seam:

1. intent price_hint, if present and greater than 0:
   reference_price_source "intent_price_hint".
2. intent limit_price, if present and greater than 0:
   "intent_limit_price".
3. intent stop_price, if present and greater than 0:
   "intent_stop_price".
4. The dispatcher's own last held quote mid for the symbol at
   reject time, if the dispatcher holds one for this dispatch
   cycle: "dispatcher_quote_mid_at_reject".
5. Otherwise reference_price is null and
   reference_price_source is "unavailable", with
   reference_price listed in missing_fields and the absence
   explained in missing_reason.

No other source is permitted. In particular the price is never
backfilled from bars after the fact and never taken from the
fill ledger; a grader must be able to trust that the stamped
price is what the dispatcher saw when it rejected.

## 5. When a field is genuinely unavailable

The rule is absolute: a key is never silently omitted. Every
field of section 3 is present on every stamped row. A genuinely
unavailable value is written as an explicit null, the field
name is listed in missing_fields, and missing_reason says why,
in plain words, at write time. bad_qty and bad_kind rows are
the expected users of this path (a malformed qty is stamped as
qty null with missing_reason naming the malformation, and the
raw offending value, if the desk lane wants it kept, goes in a
class-specific extra, never in place of the typed field). A
stamped row with a null among the five graded fields and an
empty missing_fields, or a missing_reason of null while
missing_fields is non-empty, is a spec violation and a blocker
test failure (section 7).

## 6. Forward-only application

The stamp applies to rows written after the change lands. No
backfill is claimed, attempted, or implied: the 29,360 snapshot
rows and every legacy row stay exactly as written, stamp_version
absent, and graders filter on stamp_version = 1 (or ts_utc
present) when they mean stamped rows. Any report that mixes
legacy and stamped rows must say so and give both counts.

## 7. Acceptance checks for the landing lane

1. Fixture check: drive one intent per census class through the
   dispatcher in a test harness and assert every written
   intent_rejected row carries all section 3 keys, with nulls
   only via the section 5 path.
2. Regression blocker, per the desk bug-log law: a named test
   in tests/test_d01_reject_payload_*.py asserting the same
   invariant against the _reject seam and the inline
   insufficient_options_bp_csp site, failing on the pre-change
   code and passing on the landed code, wired into
   desk/run_regression_blockers.sh.
3. Live re-census: after 5 live sessions on stamped rows,
   re-run the V3 census over new rows only. Success reads:
   100 percent of new intent_rejected rows carry stamp_version
   1, and the symbol-carrying share of new rows is 100 percent
   minus exactly the rows whose missing_fields names symbol.

## 8. The grading unlock, quantified

Against the Wave 4 snapshot proportions (29,360 rows):

- Today: 7,023 of 29,360 rows gradeable (23.9 percent),
  reconcile_halt only, and only with side reconstructed from
  the fill ledger.
- With the stamp, on stamped rows going forward:
  reconcile_halt (7,023 snapshot rows, 23.9 percent) plus
  insufficient_slice_bp (760 snapshot rows, 2.6 percent) are
  gradeable by class immediately, from the row alone, with no
  ledger reconstruction: 7,783 rows, 26.5 percent of the
  snapshot, is the unlocked share at snapshot proportions.
- Beyond those two classes: every future reject class is
  gradeable from its first stamped row, because the graded
  fields no longer depend on class-specific extras. The exit
  classes, whose grading is a bookkeeping audit, become
  verifiable per symbol and side instead of trusted on the
  reason string alone.
- What the stamp does not unlock, named so nobody overclaims:
  it does not make legacy rows gradeable (section 6), and it
  does not by itself prove any class rejects winners or earns
  its keep. That verdict still needs the graded sample, at
  cluster level, per section 9.

## 9. The cluster caveat, carried into grading

The stamp fixes identity, not independence. One halt re-fires:
in the Wave 4 grading, 5,331 graded reconcile_halt rows
collapsed to 126 independent sleeve, symbol, session clusters,
and the row-level t statistics of 10 to 29 were repetition
inflation, not evidence. Every grading run on stamped rows must
therefore aggregate at (sleeve, symbol, session) cluster level
first, report cluster counts beside row counts, and treat
row-level significance as inadmissible. intent_id dedupe inside
a cluster is required where the same intent re-fires inside one
session. A grading that reports only row-level numbers violates
this spec regardless of the stamp.

Spec written 2026-11-14, Wave 5 Lane D. No desk file was edited
in its preparation; the dispatcher source was read only.
