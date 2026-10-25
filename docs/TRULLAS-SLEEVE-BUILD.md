# TRULLAS-SLEEVE-BUILD — trullas_divergence install report

Date: 2026-10-25. Spec: `~/workspace/goals/ai-top50-pattern-study/files/TRULLAS-SPEC-2026-10-25.md` (v1.0, FROZEN), PRIMARY ARM ONLY. The spec's control/secondary/sensitivity arms are backtest machinery and were not built as sleeve behavior.

## Scope (InfinityBlade)

- **Surface:** new strategy `sleeves/trullas_divergence.py`; plumbing pair `adapters/trullas_divergence.py` + `adapters3/trullas_divergence.py` (bb_rsi pattern); one config row in `config/sleeves.json`; one key added to `desk3/producers_g4._BARS_TF_KEYS` (`bars:QQQ:1Min`); new tests `tests/test_trullas_blockers.py`; proof `proof/install/trullas_divergence.json`; BUGLOG entry TRULLAS-INSTALL-20261025.
- **Constraints:** no existing sleeve's logic touched (saty_sol untouched); verified paths preserved (strategy pure on the `core/sleeve.py` contract; adapter reuses `adapters/_bridge.bars_old` and the SnapshotSleeveContext path every ported sleeve uses).
- **Outcome:** a FED, parked=false paper sleeve on QQQ 1-minute SIP bars implementing the frozen primary arm.
- **Proof:** golden/causality/management/cap blocker tests (fail-first proven), desk gate run, config-reload activation per `desk3/run_live.py` ConfigWatcher (no service restart — OPERATIONS.md names none for a roster add).
- **Edges:** daily-loss-stop and entries/day counters are sleeve-state estimates from its own emitted intents' plan prices (the sleeve contract has no fill-P&L channel); the dispatcher's stop/target ExitRules also guard the open position.

## What was built

QQQ only; 1-minute bars from the warm SIP product (`view['bars']['QQQ|1Min']`, 6,618 rows at 2026-10-25T15:41Z). Pivots k=5, confirmed only after 5 right-side bars close (no repaint). Consecutive same-kind pivot pairs, same day, 10–120 bars apart. MACD(12,26,9) on the MACD line — divergence REQUIRED; RSI(14) and volume divergences counted (1–3 → risk units). Fib swing per spec §6 (bearish: A = lowest low between the highs, B = second high; bullish mirrored). Entry at level(0.236) − 1 tick, expiring after 30 bars or on extreme break; stop 1 tick beyond the extreme; TP1 at 38.2 exits half and moves the stop to entry; TP2 at 61.8. Pessimistic intrabar ordering (stop before targets). Entries 09:30–11:00 ET only; hard flat 12:00 ET (the strategy's own rule — config `flat_by_close` stays false with `flatten_time_et` null so no second flatten path exists); max 5 entries/day; daily loss stop −0.75% of slice equity; unit risk 0.25%; notional cap 25% per trade. Strategy state (pending setup, plan, day counters) round-trips through the adapter's state file `state/trullas_divergence/trullas_state.json` with a journal-persisted bar cursor.

## Frozen parameter table

| Parameter | Value | Spec |
|---|---|---|
| Instrument / timeframe | QQQ / 1Min (Alpaca SIP) | §2 |
| Pivot k / separation | 5 / 10–120 bars | §4 |
| MACD | (12, 26, 9), MACD line, required | §5 |
| RSI | 14 | §5 |
| Volume divergence | 2nd extreme on lower bar volume | §5 |
| Entry / stop / TP1 / TP2 | 23.6% − tick / extreme + tick / 38.2% / 61.8% | §6 |
| Entry expiry | 30 bars or extreme break | §6 |
| TP1 action | exit half, stop → entry | §8 |
| Session | entries 09:30–11:00 ET, flat 12:00 ET, ≤5 entries/day | §3 |
| Risk | unit 0.25% equity, cap 25% notional, day stop −0.75% | §7 |
| Slice | $10,000 capital / $10,000 cash (desk norm — 224/311 rows, every recent install) | scout norm |

## Tests

`tests/test_trullas_blockers.py` — 12 tests, all passing, gate-wired automatically by the gate's `test_*_blockers.py` discover.

- **Golden fixture:** hand-built 1-minute series with a known bearish triple divergence (pivot highs 110.0 → 111.0, swing low A = 103.8, volumes 5000 → 2000). Expected entry 109.2908, stop 111.01, TP1 108.2496, TP2 106.5504, qty 22 are computed independently inside the test from A and B (Fib arithmetic + sizing formula), never via sleeve helpers. The adapter-level drive on the same series (live snapshot shape) emits the identical entry.
- **Causality:** no pending setup and no entry before the second pivot's confirmation bar (bar 79); truncating the series at 50/70/79/80/82/84 never changes an earlier decision.
- **Management:** a bar spanning both stop and TP1 exits fully at the stop (pessimistic); a TP1-only bar exits half (11 of 22) and moves the stop to entry, and a later touch of entry exits the rest; 12:00 ET flat exits everything.
- **Caps/expiry:** 5-entries/day cap and the −0.75% daily loss stop each block a trigger bar; a setup untriggered for 30 bars expires and a later trigger-shaped bar does not enter.
- **Wiring:** config row shape and the `bars:QQQ:1Min` producer key (BarsProjection serves it from a warm map containing QQQ|1Min).

**Fail-first proof:** a deliberately broken variant of the strategy with the right-side pivot confirmation window removed (pivots usable the bar they print — the repaint failure the spec bans) was run against the golden + causality tests: **3 of 4 fail**. The real module passes 12/12. Method and variant recipe are recorded here so the check is repeatable; the variant itself was scratch, not committed.

## Gate

GREEN at head fdd5126: `run_regression_blockers.sh` (house TMPDIR rule, gate-owned `.gate_tmp`) — **1096 tests, OK**. The first gate run at the pre-pin head showed exactly 2 failures, both roster-count pins (311 → 312 in `tests/test_deploy_blockers.py` and `tests/test_harden_batch1_blockers.py`) caused directly by this install's new config row; the pins were updated at the source and the gate re-run green. No unrelated failures. Commits after fdd5126 are docs-only (this report and the proof JSON gate field).

## Activation state

Per-cycle config reload, no restart: `desk3/run_live.py` ConfigWatcher hashes `config/sleeves.json` each cycle and rebuilds the Desk before the next 60 s cycle on change. The sleeve is FED on all six declared inputs (`bars` and `bars_1min` from the warm product, `bars:QQQ:1Min` via the cured producer key, `positions`, `quotes`, `session_fills`). First live-cycle FED/read-back evidence belongs to the next desk cycle after this commit and is not claimed here.
