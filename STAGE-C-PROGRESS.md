# Stage C — Re-baseline to the empty book (PA36X7WU3)

SCOPE: Surface = state/broker_pending.jsonl + state/broker_pending.json, state/reconcile_baseline.json, per-sleeve state files claiming open positions, state/capital_epoch.json, state/PAUSED-FOR-RESET.json. Constraints = no strategy/sizing/threshold changes; Tensor untouched; sleeves/saty_sol.py byte-identical (sha256 verified 36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc before work); append-only journals not rewritten except the pending store's own compaction mechanism. Outcome = empty pending store with journaled mass_expiry, fresh baseline from the empty broker book via desk3.reconcile record_baseline, position-claiming sleeve state archived + reset flat with manifest, capital epoch written, pause marker removed last. Proof = read-backs of every file after writing.

## Inventory (2026-10-26T20:14Z)
- Pending store: snapshot (authoritative, live) = 1311 entries; broker_pending.jsonl = 1449 lines.
- Reconcile baseline (old): 85 symbols, cash_offset_usd -1289014.55 — pre-reset book.
- Per-sleeve state files: only 6 non-journal JSON state files exist under state/<sleeve>/ (bb_rsi_state.json, trullas_state.json, cci_state.json, aster_b1_aster_squeeze_1d.json, 3x aster_batch15_state.json). All other sleeves derive position state from the broker `positions` snapshot producer (empty on the new account). Of the 6, ONLY t_cci_corr (state/t_cci_corr/cci_state.json) claims an open position: positions={TEM: {...}}, pending={}.
- Sleeve journals (state/<sleeve>/journal.jsonl) are append-only eval/intent history, not position state — not rewritten.

## Steps — ALL DONE, read back from final state 2026-10-26T20:14Z
- [x] 1. Mass-expire pending store: 1311 live entries expired. PendingStore's own compaction rewrote broker_pending.json ([]) and broker_pending.jsonl; a mass_expiry record {count:1311, expired_count:1311, reason:account_switch, account:PA36X7WU3, ts:2026-10-26T20:14:13.614856+00:00} was appended via desk3.journal.append_line to broker_pending.jsonl (sole line) and to state/dispatcher.jsonl (last line). Pre-expiry copies kept: state/broker_pending.jsonl.pre-reset-20261026T201413Z, state/broker_pending.json.pre-reset-20261026T201413Z. Read-back: PendingStore.load() == [].
- [x] 2. Fresh reconcile baseline via desk3.reconcile(record_baseline=True) against the empty broker book ({} positions, cash 1000000, slice capital from config/sleeves.json): state/reconcile_baseline.json = {"positions": {}, "cash_offset_usd": -1765114.11}, status BASELINE_RECORDED. Old baseline archived: state/reconcile_baseline.json.pre-reset-20261026T201418Z.
- [x] 3. Sleeve state reset: t_cci_corr only (positions {TEM} -> {}, pending {} -> {}). Archived: state/t_cci_corr/cci_state.json.pre-reset-20261026T201430Z. Manifest: state/reset_manifest_20261026.json listing sleeves_reset=[t_cci_corr] + full inventory note.
- [x] 4. state/capital_epoch.json = {epoch_start_utc: 2026-10-26T20:14:30.681985+00:00, account: PA36X7WU3, start_equity: 1000000, benchmarks: [SPY, QQQ]} — read back verified.
- [x] 5. state/PAUSED-FOR-RESET.json removed AFTER all read-backs passed. saty_sol.py sha256 still 36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc.

Note: reconcile positions check on the next live cycle compares baseline+journal-derived fills (historical dispatcher.jsonl, append-only, untouched by design) — the baseline was recorded with the desk's own record_baseline mechanism exactly as on day one; any historical-journal discrepancy naming is the reconcile system's own reporting, not hidden here.

## Cure — RECONCILE-HALT-20261026 (RECONCILE-EPOCH-20261026), 2026-10-26T20:48-21:01Z

The note at the end of the Stage C section above named the open defect: post-resume cycles rejected entries from 23 sleeves as reconcile_halt (178 rows in state/dispatcher.jsonl) because reconcile's journal-derived truth (baseline + ENTIRE dispatcher.jsonl) was never scoped to the capital epoch this file created — capital_epoch.json had zero code readers.

- [x] desk3/reconcile.py: journal_derived() epoch-aware (first reader of capital_epoch.json; only fills ts >= epoch_start_utc count, positions + spend; no-ts/unparseable = pre-epoch; no epoch file = legacy unscoped). Tolerances and dispatcher.py untouched; dispatcher.jsonl never rewritten.
- [x] Baseline re-recorded via live PaperDoor read-back on PA36X7WU3 ({} / $1,000,000 / ACTIVE): archived state/reconcile_baseline.json.pre-cure-20261026T204821Z; new baseline {"positions": {}, "cash_offset_usd": -1707192.0} read-back verified.
- [x] Blockers: tests/test_reconcile_epoch_20261026_blockers.py (6 tests, gate-wired by discover pattern). Fail direction proven pre-cure: (a) unscoped positions returned, (d) offset -1765114.11 vs -1707192.00. Post-cure 6/6; gate 1255/1255 OK exit 0.
- [x] Runner restarted through the watchdog's own mechanism (documented Stop on pid 29634 -> watchdog restart 20:49:04Z -> new pid 34388; an environment restart recycled supervision and the current watchdog pid 926 relaunched pid 949 at 20:50:28Z from the cured tree). First cured cycle: runner.json pid 949 cycle 1 ok, 16 dispatched; dispatcher rows 18091 -> 18107, ZERO reconcile_halt; 10 order_submitted from previously halted sleeves (tensor_swing x8, s_mn_hourly_1w, s_mn_macd) with broker read-back accepted on PA36X7WU3. Offline reconcile on final state: OK / halted [] / cash_halt False.
- Full record: BUGLOG_2026-10-26.md, RECONCILE-HALT-20261026.

## DIAGNOSTIC NOTE — broker 422 class (Midna, 2026-10-26 22:22 ET, read-only)
- The 422 rejections are STILL firing every cycle tonight (latest rows 2026-10-27T02:14Z) for exactly: aster_native_btc_eth_sma200 (BTC-USD), s_mn_reversal, s_mn_vwap. All other sleeves submit fine.
- Journal rows carry only "FetchError:HTTP 422 for https://paper-api.alpaca.markets/v2/orders" — the response BODY (Alpaca's code/message naming the failing field) is NOT journaled, so the failing field is currently unknowable from desk records. First cure step: make the door journal the 422 body.
- Suspects to check against the body, in order: client_order_id length (aster's is ~86 chars, Alpaca caps at 48; s_mn_reversal's is exactly 48), crypto order parameters for BTC-USD, then qty/TIF fields. Night inspection owns the cure (BUGLOG + blocker per law).
- Payload shape (desk3/broker.py submit_order): {symbol, side, qty:str, type, time_in_force (default "day"), client_order_id, limit_price:str if set}. Dispatcher journal does NOT record qty/type/limit_price per intent, so payload values are also unrecoverable from desk records tonight.
- client_order_id = "v3-{sleeve}-{intent_id}" (sleeve name doubled). Measured lengths: tensor_swing (works) 46; s_mn_vwap 40 (under any cap, so length is NOT its cause); s_mn_reversal exactly 48; aster_native_btc_eth_sma200 ~86 (Alpaca caps client_order_id at 48 — aster fails on length alone, near-certain).
- aster stacks a second suspect: crypto orders on Alpaca reject time_in_force "day" (crypto requires gtc/ioc); the door defaults to "day".
- s_mn_reversal / s_mn_vwap remaining prime suspect: unrounded limit_price precision (Alpaca 422s sub-penny prices on >=$1 stocks) or fractional qty on a non-fractionable asset. The 422 body names the field outright; journaling it remains step one of the cure.
