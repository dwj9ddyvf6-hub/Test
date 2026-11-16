# BLOCKED-EXIT CURE RECORD 2026-10-29 (phase: cure)

Diagnosis: state/blocked_exit_diagnosis_20261029.md. Buglog:
BUGLOG_2026-10-29.md, entry BLOCKED-EXIT-20261029 (cure section).

## Code changed (minimum sufficient, exit/dispatch path only)

- desk3/broker.py: PaperDoor.submit_order sends position_intent +
  stop_price; get_open_orders(); cancel_order() tolerant of 204
  empty body; PaperDoor.live_book=True. FakeBroker parity
  (live_book=False default; records position_intent/stop_price;
  get_open_orders/cancel_order).
- desk3/dispatcher.py: _normalize_broker_symbol (ADAUSDT/ADAUSD ->
  ADA/USD for known crypto bases); _terminal_broker_answer (403
  subclasses: wash trade, insufficient qty available,
  held_for_orders, position intent mismatch, insufficient
  balance); _apply_broker_dialect on every intent (symbol + crypto
  TIF gtc, journaled symbol_normalized); _reconcile_exit pre-flight
  for exits on live_book brokers (no position -> terminal
  exit_satisfied_no_broker_position; resting covers full ->
  terminal exit_already_resting_at_broker; else side/intent
  derived from position sign, qty clamped to uncovered remainder,
  journaled exit_reconciled_to_broker_book); submit passes
  position_intent + stop_price (stop types only); terminal 403
  subclasses break the retry loop as non-transient. _exit_book
  cached per instance, invalidated on submit.
- desk3/aster_crypto.py: _broker_symbol (USDT -> /USD); evaluate()
  positions filtered to own symbol; exit/entry intents emitted in
  broker dialect.
- tests/test_scale_fault_blockers.py: one test double gained the
  two new optional submit kwargs (interface parity only).
- tests/test_blocked_exit_20261029_blockers.py: NEW, 15 tests,
  gate-wired via the test_*_blockers.py discover pattern.

No strategy, sizing, stop-design, threshold, roster or Tensor
change. No Tensor file touched.

## Fail direction (pre-cure tree, files temporarily restored)

- Blocker file: FAILED at import (helpers absent).
- Probe on old code: TSEM exit with no broker position ->
  "submitted", submit_count 1 (phantom open path alive).
- Probe on old code: PaperDoor wire body keys were only
  [client_order_id, qty, side, symbol, time_in_force, type] — no
  position_intent.
- Probe on old code: aster_crypto.evaluate over FFIV/SOXL
  positions returned ADAUSDT exits sized 796 and 6,156.
- On cured code: 15/15 blocker tests pass; adjacent suites
  (pending drain, drain class, 422 body/aster/smn, registry
  dispatcher, scale fault, blocker ratchet) 39/39 pass.

## Live execution (paper PA36X7WU3, identity proven from desk keys)

Timeline UTC 2026-10-29:
- 21:22:49 watchdog relaunched runner after pid 4940 was stopped:
  new pid 10484, mode dispatch, cured code (watchdog journal).
- First execution pass: cancel of 989aa32c LANDED but the script
  died on fetch_json parsing Alpaca's 204 empty DELETE body.
  Door cancel_order fixed (fetch_bytes; empty body = canceled)
  and blocked by test before the second pass.
- Second pass: 989aa32c already canceled; e60aafbd cancelled,
  read back canceled (canceled_at 2026-10-29T21:24:34Z). A second
  DELETE is an idempotent no-op success; by-id status remains
  canceled. The status=open LIST still shows e60aafbd accepted
  (broker list/by-id inconsistency) — watch item.
- Drain (cured Dispatcher + PaperDoor, session 2026-10-29):
  pass 0: before 840 -> {drained_terminal: 839, submitted: 1} ->
  after 0. Journal: 642 exit_already_resting_at_broker, 183
  exit_satisfied_no_broker_position, 2 symbol_normalized, 1
  exit_reconciled_to_broker_book, 0 broker_unavailable.
- The 1 submitted: donchian55 CORZ exit intent
  aster_trader_donchian55-20261029T042106-2 -> order da98efd1,
  buy 9,234 buy_to_close, accepted (rests for the 2026-10-30
  session; DAY market order submitted after close).

## Final state read back (2026-10-29 ~21:31 UTC)

- Account PA36X7WU3 ACTIVE; equity ~$983-990k (moving with marks);
  buying_power $38,393.46 at the pre-drain read (regt $0 while the
  short book stands — irrelevant to closes, which bypass BP).
- Pending store: 0 entries (was 840 at execution start, 776 at
  the close review).
- Positions (all short, unchanged quantities): ANF -171,
  AXTI -13,414, CORZ -9,234, FFIV -796, SOXL -6,156, TWST -7,
  VSAT -27; qty_available 0 on all (fully reserved).
- Resting full closes (buy_to_close market, accepted): ANF 171
  e95e7a5f, AXTI 13,414 e32f4e27, CORZ 9,234 da98efd1, FFIV 796
  5039691f, SOXL 6,156 a6462ab9, TWST 7 d53273e5, VSAT 27
  cf87037b. (Plus the e60aafbd ghost in the open LIST only;
  canceled by id.)
- Runner pid 10484 cycle 1 completed 21:30:16Z on cured code:
  broker_unavailable total unchanged (1,648), +16 phantom exits
  terminally rejected at pre-flight, pending stayed 0.

## Stops

The desk's intent contract admits only market/limit order types
(models.validate_intent); stop_price is sleeve reference data
(contract.py: "reference prices from the signal bar, not order
instructions"). Protection is therefore the exit-intent path by
design. After the drain every open position's FULL exit rests at
the broker as a market close — stronger than a stop — and
qty_available=0 makes any additional order on those positions
impossible until the closes resolve. Nothing further to place.

## Open items handed to verify

1. At/after the 2026-10-30 open: read back the 7 resting covers
   by order id — filled qty/price per name; positions flat or
   named remainder.
2. e60aafbd: confirm it never fills and leaves the open list.
3. Watch donchian55: a re-emitted CORZ sell_to_open entry resting
   again would re-create the wash block for any future cover;
   the desk needs an entry-side ruling/fence if it recurs (NOT
   cured here — entry behaviour is sleeve strategy territory).
4. Sleeve virtual-book divergence (donchian55/s_mn_vwap phantom
   longs) remains: cured dispatch rejects their phantom exits
   terminally each cycle with named reasons, but the ledgers
   themselves are a separate bookkeeping cure.
5. Full regression gate: GREEN on the final cured tree
   (run_regression_blockers.sh GATE_RC=0, 1,449 tests). Clean
   comparison: pre-cure tree 1,434 GREEN in the same window; the
   cured tree's initial clean run failed only 8 tests, all in the
   cure's blast radius (7 crypto-dialect state assertions in
   aster b5/batch6/7/11/12 + remainders, updated to the broker
   dialect with BLOCKED-EXIT-20261029 tags; 1 cancel-204 test
   whose fix had been lost in a restore shuffle and was
   re-applied). Two earlier gate attempts returned rc=1 during a
   transient platform write-EPERM event (~21:36-21:49 UTC) and
   are environmental, documented in the BUGLOG.
6. RESOLVED after this record's first write: the e60aafbd open-
   list ghost cleared (~22:02 UTC) — open list now shows exactly
   the 7 buy_to_close covers; verify only needs the fills check
   (item 1) and the donchian55 re-entry watch (item 3).
