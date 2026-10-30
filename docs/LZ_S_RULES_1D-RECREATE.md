# lz_s_rules_1d - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Lab rule 1D (test)", type other, family 1d, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. Classification evidence on the entry (2026-10-30): the config shows only a fear_day capped-limit execution policy and a time exit; the upstream lab_live book signal that fires it is not recorded in the accounting. The sizing gap is closed by the rl64 config entry cited below.
- Executable record in this repo: the entry (id `s_rules_1d`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, kind 1d, enabled true, state live, status "ready (unarmed: desk staged)"), run by the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`; sleeve id "lz_" + config id). Research lines: DESK_PLAN F1 (43 clean-support frozen rules, CORPUS_AUDIT/outside_lab_orig/olx_rules43.csv) + F2 (MOC next close, hold H+1); the desk playbook lane t_rules_1d. Flag: L-146 scaled x0.611, $73,616 to $44,000 / 44 slots.
- The v3 implementation is in this repo: `sleeves/s_rules_1d.py` / `adapters3/s_rules_1d.py` (wrapper note: Lab rule 1D, 43 frozen rules, CSV ON, Live), the shared engine `desk3/lazarus.py` SPECS s_rules_1d, its package `docs/S_RULES_1D-RECREATE.md`, algorithm doc `docs/S_RULES_1D-ALGORITHM.md` and card `strategies/lazarus/lz-lab-rules.md`.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A daily Lazarus fire-consumer lane for the research lab's 43 frozen rules: each rule's fire carries its own horizon H, and the lane holds the position H+1 sessions with no price stop, exiting at a stored target or at the time exit. Signal generation (the 43 rules themselves) stays upstream in the lab_live books.

## Full algorithm

Config layer (rl64 entry s_rules_1d, canonical for this lz_ id):

1. Source: lab_live books (native Lazarus routing), file `DESK_INTEGRATION/lab_live/out/latest/*.json`, lane s_rules_1d.
2. Entry policy: fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day, limit_band_pct 5.0, limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true.
3. Entry gate mechanics for the fear_day policy, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day / capped_limit / size): buy only when QQQ is below its prior close AND the stock is at or below its prior close AND at or below 1.02 x the fire close (the config no_chase_mult), decided inside the afternoon window (close-40 to close-10 minutes) of a session in the red window D+1..D+5 after the fire session (window_sessions 5); nothing by D+5 means skip; every unknown price means wait, never a false trigger. The capped limit is live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap. Sizing under that gate: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, and the lane dollar budget shrunk to the remaining budget when that is at least min_slot_fraction of the position.
4. Exit (config): the sleeve feed fire's plan: no stop, time exit at hold = the rule horizon H + 1 sessions, hold_from fill, hold_unit_kind 1d, no plan overrides.
5. Sizing (config, closing the accounting gap): budget_usd 44000, max_slots 44, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.

v3 engine layer (`desk3/lazarus.py` SPECS s_rules_1d, per `docs/S_RULES_1D-RECREATE.md`): slots=44, capital=44000.0, cadence_s=300, session rth, max_age_min=2880, stop_pct=None, horizon_sessions=22, horizon_from_fire=True, horizon_plus_one=True, per-slot 1000.0. Exits first (stored target, then the stored horizon time exit; the stored horizon is the fire's horizon_sessions when present, plus 1 because horizon_plus_one is set, otherwise 22). Entries only below 44 held; candidate fires are reordered freshest-first (ENH25-RULES-FRESH-20261024, default ON for the rules lanes); a fire is skipped on sleeve_id mismatch, held symbol, non-buy side, unparseable fired_at, or age outside 0..2880 minutes; the SPEC sets no family, tier, cap, max_price, deep or vix filter. Fresh-price reprice (default ON) and the bound guard (default ON, refuses a fresh price at or above the fire target_price) apply; qty = int(1000.0 // price); entry market day buy, stop_price None, reason s_rules_1d_tensor_fire.

## Files in this repo

- This package: `docs/LZ_S_RULES_1D-RECREATE.md`
- Executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_rules_1d`); md2 host `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Vendored Lazarus gate: `sleeves/lazarus/vendor/lazarus/gate.py`
- v3 wrapper and engine: `sleeves/s_rules_1d.py`, `adapters3/s_rules_1d.py`, `integration/s_rules_1d_adapter.py`, `desk3/lazarus.py` (SPECS s_rules_1d)
- Sibling package, algorithm doc and card: `docs/S_RULES_1D-RECREATE.md`, `docs/S_RULES_1D-ALGORITHM.md`, `strategies/lazarus/lz-lab-rules.md`
- Roster row: `config/sleeves.json` (row id s_rules_1d), also `engines/config/sleeves.json`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `lz_s_rules_1d` = "lz_" + config id `s_rules_1d`. Kind 1d, account TEST, enabled true, state live.
- Config sizing: budget $44,000, max_slots 44, position $1,000 (Full algorithm).
- v3 roster row for s_rules_1d: module adapters3.s_rules_1d, cadence_s 300, session rth, slice capital_usd 44000.0 / cash_usd 44000.0, bp_buffer_frac 0.02, params {}, inputs [lazarus_fires, bars, positions], parked false.

## Data inputs

- lab_live fire books: `DESK_INTEGRATION/lab_live/out/latest/*.json` (config layer), delivered to the v3 engine as lazarus_fires with symbol, side, fired_at/ts, price, horizon_sessions and any target_price.
- Bars per symbol (and SPY bars for session counting); positions; sleeve state (horizon and target per symbol) in laz_state.json.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Take the rl64 entry `s_rules_1d` as this lane's configuration; do not edit its entry, exit or sizing fields.
4. Run under the md2 Lazarus host, or through the v3 adapter `adapters3/s_rules_1d.py` into `desk3/lazarus.py` with the s_rules_1d SPECS entry.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated test file for this exact canonical id was found in Test):

- A qualifying fire aged within 2880 minutes computes qty int(1000.0 // price) with stop_price None and reason s_rules_1d_tensor_fire, up to 44 slots; aged above 2880 minutes it produces no entry.
- A held position whose stored target_price is reached exits in full (reason s_rules_1d_target) with no entry in the same call.
- A held position reaching its stored horizon (the fire horizon plus 1, otherwise 22 sessions) exits in full on the time exit; no price move alone exits it.
- Config layer: entries only on a red stock and red QQQ day, within 5 sessions and 65 minutes, capped at 1.02x.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
