# lz_s_mn_faber - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Faber (Midna port)", type trend following, family 1d, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. Classification evidence on the entry (2026-10-30): sleeves/s_mn_faber.py holds each of five ETFs only while its close is above its 10-month (210-session) average and exits below it. The sizing gap is closed by the rl64 config entry cited below.
- Executable record in this repo: the entry (id `s_mn_faber`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, kind 1d, enabled true, state live, status "ready (Midna port; start FLAT; Midna positions are reference only)"), run by the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`; sleeve id "lz_" + config id). Research lines: "Midna quantpedia.ts Faber five ETFs above 10-month average"; "faithful Midna rules; start FLAT; no fake feeds/fills"; the reference positions file is comparison only. Flags: lane budget raised to $5,000 / 5 slots (2026-10-15), then L-146 scaled x0.611 to $3,000 / 3 slots (the config sizing block below).
- Strategy code in this repo: `sleeves/s_mn_faber.py` (also `adapters/s_mn_faber.py` and `integration/s_mn_faber_adapter.py`), with its own recreation package `docs/S_MN_FABER-RECREATE.md`. Its module docstring records the catalog rule and two ledger readings: the five ETFs are the classic Faber GTAA-5 set (the catalog says "five ETFs" without naming them), and the book holds every qualifying ETF with an equal share of the budget (the catalog's "3 slots" conflicts with a five-ETF hold-any rule; the ledger records the reading).
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

The Midna port of the Faber trend rule: hold each of SPY, EFA, EEM, VNQ and AGG only while its daily close is above its 10-month (210-session) simple moving average; exit when the close falls below it. A monthly method traded on the daily clock: entries and exits evaluate every session.

## Full algorithm

Strategy code (`sleeves/s_mn_faber.py`, signal(bars, slice_state, context)), in code order:

1. Constants: ETFS = (SPY, EFA, EEM, VNQ, AGG); BUDGET = 3000.0; PER_ETF = 3000/5 = 600.0; MA_BARS = 210; SleeveConfig sleeve_id s_mn_faber, cadence_s 300, universe the five ETFs, state_schema {position: dict|None}.
2. For each ETF in order: skip when fewer than 210 bars are available. ma = SMA of the last 210 closes; px = the last bar's close.
3. Exit first per symbol: if the ETF is held and px < ma, emit an exit for the full held quantity, sell_to_close, price_hint px, reason naming the close below the 10-month average.
4. Entry: if the ETF is not held and px > ma, and the stale-bar gate passes, qty = qty_for(600.0, px) (whole shares the $600 share buys); if qty > 0 emit a buy_to_open entry, price_hint px, reason naming the close above the average. A close exactly equal to the average produces neither an entry nor an exit.
5. Stale-bar gate (ENH19-FABER-STALE-20261024, default ON; OFF via extra["s_mn_faber_enh19"]["stale_gate"]=False): an entry is refused when the decision bar's date is more than 4 calendar days before the session date (a Monday after a Friday and a post-holiday Tuesday pass); a refusal is journaled to extra["enh19_journal"] when that list is supplied. Exits are not gated.

Config layer (rl64 entry s_mn_faber, the canonical record for this lz_ id): source producer sleeve_midna (Midna entire-branch signal files + Yahoo), file `shadow/paper_sleeve/live/midna/midna_fires_v1.json`, lane s_mn_faber. Entry policy midna_block: max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions null, no_chase_mult null, stock_red false, qqq_red false, order capped_limit_day. Exit: "Midna plan: Faber below 10m SMA exit", hold_from plan, hold_unit_kind 1d, stop_pct 99.0, max_bars 0, rest time. Sizing block: budget_usd 3000, max_slots 3, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000. Where the config sizing block (3 slots x $1,000) and the strategy code ($600 per ETF across five ETFs) differ, both are recorded here; the code is the executable truth for the v3 sleeve and the config block is the md2 lane's record.

## Files in this repo

- This package: `docs/LZ_S_MN_FABER-RECREATE.md`
- Strategy code (already in Test): `sleeves/s_mn_faber.py`; copies at `adapters/s_mn_faber.py` and `integration/s_mn_faber_adapter.py`
- Shared helpers: `sleeves/laz8_common.py` (Intent, SleeveConfig, closes, held_positions, qty_for, sma)
- Executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_mn_faber`); md2 host `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Sibling package: `docs/S_MN_FABER-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `lz_s_mn_faber` = "lz_" + config id `s_mn_faber`. Kind 1d, account TEST, enabled true, state live.
- Strategy constants: BUDGET 3000.0, PER_ETF 600.0, MA_BARS 210, cadence_s 300, universe (SPY, EFA, EEM, VNQ, AGG).
- Config entry entry/exit/sizing blocks: verbatim in the Full algorithm section.
- Switch: extra["s_mn_faber_enh19"]["stale_gate"], default ON.

## Data inputs

- Daily bars for the five ETFs (at least 210 sessions each), from the sleeve_midna signal files + Yahoo per the config source block (`shadow/paper_sleeve/live/midna/midna_fires_v1.json`).
- Held positions (slice_state) and the session date (context) for the stale-bar gate.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Confirm `sleeves/s_mn_faber.py` is present and its constants match the Configuration section, and take the rl64 entry `s_mn_faber` as the lane's config record.
4. Wire daily bars for the five ETFs and the held-position state; call signal(bars, slice_state, context) each session (cadence 300 s in the desk cycle).
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the code (no dedicated test file for this exact canonical id was found in Test):

- With 209 bars for an ETF, that ETF produces no intent.
- A held ETF whose last close is below its 210-session SMA exits in full; at exactly the SMA it does not.
- An unheld ETF closing above its SMA with a fresh bar enters with qty = whole shares $600 buys at that close; the same setup with a decision bar more than 4 calendar days old enters nothing (gate ON).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
