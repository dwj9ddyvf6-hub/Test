# ausar_r19_R19_TIMING_OVERNIGHT_25BP: Recreation package

## Provenance

- Canonical id: `ausar_r19_R19_TIMING_OVERNIGHT_25BP`; canonical name: Strong-afternoon continuation; aliases: ausar_r19_R19_TIMING_OVERNIGHT_25BP.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type momentum, family overnight, algorithm grade PARTIAL; accounting gaps: exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Strong-afternoon continuation" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/aster_r19_timing_overnight_25bp.py + desk3/aster_batch15.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Strong-afternoon continuation: buys US equities near the close when the early-afternoon move ranks in the top fifth of its own history, and sells at the next session open. This canonical id is the 25 bp cost variant. Accounting grade PARTIAL: exit and sizing were not recorded in the accounting sources, but both are present in the code cited above, which is the truth here.

## Full algorithm

From `desk3/aster_batch15.py` (SPECS: kind="overnight", risk=0.0025, notional=0.1, fee_bps=25, slots=8, inputs=("bars","positions","quotes"), cadence_s=300) and the existing aster recreation doc in this repo, in evaluation order:

1. Exits first (`_eval_timing`, before entries, for every non-zero position): bid is the sell quote, else the last close. In order: stop set and bid <= stop gives `observed_stop_trigger`; target set and bid >= target gives `observed_target`; exit_at set and now >= exit_at gives `scheduled_time_exit`; (hourly only) 20 native bars after signal_end gives the deadline exit. Any exit suppresses entries that cycle. This sleeve's signal carries no stop and no target, so the only exit that can fire is the scheduled exit at exit_at, 09:30 ET on the next session.
2. Overnight signal (`overnight_signal`), per symbol in the frozen 42-name UNIVERSE42 order, skipping held symbols; at least 252 30-minute bars required by the caller: today must be a weekday session in the snapshot calendar; build the 12:30 and 14:30 ET 30-minute bars per session; for each prior full session with both bars the afternoon return is close(14:30 bar) / close(12:30 bar) - 1 (the family card phrases this as the 13:00-15:00 ET move from those bar closes; early-close days are excluded per the accounting entry). Require at least 126 prior sessions; threshold is the 80th percentile (linear interpolation) of the last 252 prior returns. Signal only if today's afternoon return >= that threshold. signal_end is the end of today's 14:30 bar; actionable_at = signal_end + 30 minutes; exit_at = 09:30 ET on the next session; no next session means no signal.
3. Entry clock: entries only when 15:30 <= ET time < 15:35, and only when actionable_at <= now < actionable_at + 5 minutes.
4. Sizing (common timing sizing): fee = 25/10000; budget = min(cash, 10000.0 * 0.1); qty = floor(budget / (price * (1 + fee))); with no stop there is no risk-cap term, so qty = floor(min(cash, 1000.0) / (price * 1.0025)). Refuse if qty <= 0. At most slots=8 held-plus-new positions, one per symbol.
5. Mid-price limit enhancement (ENH-ASTERB15-MIDLIMIT-20261024, this sleeve only, switch extra["enh_aster_r19_timing_overnight_25bp"] or extra["aster_b15_enh"] {"mid_limit": bool}, default ON): with a two-sided quote the entry is a limit at round(mid, 2) instead of a market order, the ask recorded as control price; OFF restores the market order. The scheduled exit keeps market form in this sleeve.
6. Entry intent: day buy_to_open with exit_at carried, reason naming overnight_qualified_actual_quote.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve wrapper (already in Test): `sleeves/aster_r19_timing_overnight_25bp.py` (also `adapters3/aster_r19_timing_overnight_25bp.py`, `integration/aster_r19_timing_overnight_25bp_adapter.py`); SLEEVE_ID `aster_r19_timing_overnight_25bp`, delegating to `desk3/aster_batch15.evaluate`.
- Shared engine (already in Test): `desk3/aster_batch15.py` (SPECS entry kind overnight, `overnight_signal`, `_eval_timing`).
- Existing family card and recreation doc for the aster id (already in Test): `strategies/ausar/r19-timing-overnight.md`, `docs/ASTER_R19_TIMING_OVERNIGHT_25BP-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "Strong-afternoon continuation".

## Configuration

- Universe: frozen 42-name list UNIVERSE42 in `desk3/aster_batch15.py`: AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI. Asset: US equities. Timeframe: 30-minute bars.
- Slice: capital_usd 10000.0, cash_usd 10000.0; notional 0.1, risk 0.0025, fee_bps 25, slots 8, cadence_s 300, session rth (per the aster recreation doc's roster reading).

## Data inputs

IEX 30-minute regular-session bars (family card); engine producers: tensor_bundle -> tensor_fires (93600 s), bars -> bars (900 s), broker_readback -> positions (900 s), quotes -> quotes (60 s). view bars keyed by symbol/timeframe, quotes with bid/ask, positions with qty and stop/target/exit_at or the same under meta.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- Fewer than 126 prior sessions, a non-session today, or a missing next session each produce no entry.
- Today's 12:30-to-14:30-bar return below the interpolated 80th percentile of the last 252 prior returns produces no entry; at or above it produces one entry inside 15:30-15:35 ET only.
- Sizing: qty equals floor(min(cash, 1000.0) / (price * 1.0025)); slots capped at 8.
- Mid-limit: enhancement ON with a two-sided quote gives a limit at round(mid, 2); OFF gives a market order.
- The only exit is the scheduled exit at the next session's 09:30 ET, and it suppresses entries that cycle.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
