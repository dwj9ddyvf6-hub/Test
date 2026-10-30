# lz_s_moonshot - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Moonshot (test)", type other, family 1w, algorithm grade PARTIAL with the single recorded gap "sizing not recorded in any consulted source"; algorithm sources: md2 catalog entry/exit/strategy text. Classification evidence on the entry (2026-10-30): the config shows only a fear_day execution policy and a 52 or 78 week time exit; the upstream sleeve_feed fire signal is not recorded in the accounting. The sizing gap is closed by the rl64 config entry cited below.
- Executable record in this repo: the entry (id `s_moonshot`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, kind 1w, enabled false, state live, status "staged, log-only fires (inventory thresholds)"), run by the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`; sleeve id "lz_" + config id). Research lines on the entry: DESK_PLAN section 3 (Moonshot: W52 43%, DD -48.8, 1% weights); EDGE_INVENTORY X-MOONSHOT-SLEEVE (1W Cyan px <= $14.94 & depth60 >= 70.35, 10 names, W52); and a draft spec (0.1-DRAFT, NOT frozen: W78, 1W Cyan OR Green, px < $15 & depth60 >= 70, dv20 >= $1M, max 10 names, next open). Flags: staged off / log-only; turned ON at cutover 2026-10-14 (was off) per one flag while the config enabled field is false; runs side by side with s_mn_moonshot as a separate experiment.
- The v3 desk implementation of the sibling sleeve is in this repo: `sleeves/s_moonshot.py` / `adapters3/s_moonshot.py` (thin wrapper over `desk3/lazarus.py` SPECS s_moonshot), its package `docs/S_MOONSHOT-RECREATE.md`, algorithm doc `docs/S_MOONSHOT-ALGORITHM.md` and card `strategies/lazarus/lz-moonshot.md`. The Midna repo tree also carries a research lane named MOONSHOT_LANE (its MOONSHOT_LANE directory, code ms1/ms2/ms3/ms4); that is a research lane, not this config sleeve, and nothing was vendored from it.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A weekly Lazarus fire-consumer lane for the Moonshot inventory setup: cheap, deeply pulled-back cyan weekly names (price at or below $14.94 with a deep60 tag, per the inventory line), bought only on a fear (red) day and held on a long weekly horizon. It does not generate its own signal; the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires.

## Full algorithm

Config layer (rl64 entry s_moonshot, canonical for this lz_ id):

1. Source: sleeve_feed composer (tracker ledger + alt-data tags), file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, lane s_moonshot.
2. Entry policy: fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day, limit_band_pct 5.0, limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true.
3. Entry gate mechanics for the fear_day policy, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day / capped_limit / size): buy only when QQQ is below its prior close AND the stock is at or below its prior close AND at or below 1.02 x the fire close (the config no_chase_mult), decided inside the afternoon window (close-40 to close-10 minutes) of a session in the red window D+1..D+5 after the fire session (window_sessions 5); nothing by D+5 means skip; every unknown price means wait, never a false trigger. The capped limit is live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap. Sizing under that gate: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, and the lane dollar budget shrunk to the remaining budget when that is at least min_slot_fraction of the position.
4. Exit (config): the sleeve feed fire's plan: a 15% disaster stop (L-130) or the time exit; hold = 52 weeks (W52, inventory) / W78 (draft spec); hold_from plan, hold_unit_kind 1w, no plan overrides. The record itself carries both horizons (frozen inventory W52 and the unfrozen draft W78); neither is chosen over the other here.
5. Sizing (config, closing the accounting gap): budget_usd 2581, max_slots 2, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.

v3 engine layer (`desk3/lazarus.py` SPECS s_moonshot, per `docs/S_MOONSHOT-RECREATE.md`): slots=10, capital=2581.0, cadence_s=3600, session rth, max_age_min=11520, stop_pct=0.15, horizon_sessions=252, family cyan, tf 1W, max_price=14.94 (inclusive), deep60=True. Exits first (15% stop, then stored target, then the 252-session time exit); entries only below 10 held, per-slot 258.10, fires aged 0..11520 minutes with matching sleeve_id, buy/long side, carried family containing cyan, price at or below 14.94 and a deep60/deep_pullback60 tag; fresh-price reprice and bound guard default ON; qty = int(258.10 // price); entry market day buy with stop_price round(price x 0.85, 4), reason s_moonshot_tensor_fire. The v3 SPEC and the md2 config differ on slots (10 vs 2) and on the exit form (252 sessions vs W52/W78); both records are kept here exactly as found, the config being the record for this lz_ id and the SPEC being the v3 sleeve's own rule.

## Files in this repo

- This package: `docs/LZ_S_MOONSHOT-RECREATE.md`
- Executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_moonshot`); installer `packages/grokbot/rl64/tools/install_rl64.py`; md2 host `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`
- Vendored Lazarus gate: `sleeves/lazarus/vendor/lazarus/gate.py`
- v3 wrapper and engine: `sleeves/s_moonshot.py`, `adapters3/s_moonshot.py`, `integration/s_moonshot_adapter.py`, `desk3/lazarus.py` (SPECS s_moonshot)
- Sibling package, algorithm doc and card: `docs/S_MOONSHOT-RECREATE.md`, `docs/S_MOONSHOT-ALGORITHM.md`, `strategies/lazarus/lz-moonshot.md`
- Roster row: `config/sleeves.json` (row id s_moonshot; parked true), also `engines/config/sleeves.json`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Canonical id `lz_s_moonshot` = "lz_" + config id `s_moonshot`. Kind 1w, account TEST, enabled false, state live (staged, log-only).
- Config sizing: budget $2,581, max_slots 2, position $1,000 (Full algorithm).
- v3 roster row for s_moonshot: module adapters3.s_moonshot, cadence_s 3600, session rth, slice capital_usd 2581.0 / cash_usd 2581.0, bp_buffer_frac 0.02, params {}, inputs [lazarus_fires, bars, positions], parked true.

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane s_moonshot; delivered to the v3 engine as lazarus_fires with symbol, side, fired_at/ts, family, price and tags (deep60 / deep_pullback60, any target_price).
- Bars per symbol (and SPY bars for session counting); positions (broker readback); sleeve state in laz_state.json.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Take the rl64 entry `s_moonshot` as this lane's configuration; respect its enabled false / staged state: log-only, no live entries, exactly as recorded.
4. Run under the md2 Lazarus host, or evaluate the v3 form through `adapters3/s_moonshot.py` into `desk3/lazarus.py` with the s_moonshot SPECS entry.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated test file for this exact canonical id was found in Test):

- Config layer: an entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the fire and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- v3 layer: a cyan fire priced at exactly 14.94 with a deep60 tag computes qty int(258.10 // 14.94) and stop_price round(14.94 x 0.85, 4); priced above 14.94 or without the deep60 tag it produces no entry.
- A held v3 position at or below avg_price x 0.85 exits in full (reason s_moonshot_stop15) with no entry in the same call.
- The lane's staged state is preserved: with enabled false, fires are logged and no order is routed.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
