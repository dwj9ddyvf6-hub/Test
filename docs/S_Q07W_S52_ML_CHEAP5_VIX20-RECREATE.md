# s_q07w_s52_ml_cheap5_vix20 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): two entries touch this id. The canonical entry (name equal to the id) is UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description", with algorithm grade FULL from the lz_engine config alone (entry/exit/sizing). A merged sibling entry, "Q07 w_swing H52 midlarge cheap5+stress_vix20 (test)", carries the same config values under the alias lz_s_q07w_s52_ml_cheap5_vix20 with grade PARTIAL (sizing gap). Type trend following, family 1w; style evidence (repair round 2, 2026-10-30): the Q07 family is one type, trend following; vix20 is a gate and ml is a cap band per desk3/q07_engine.py. Universe, asset class, timeframe and creator are "not recorded" on the canonical entry.
- Executable record in this repo: the entry (id `s_q07w_s52_ml_cheap5_vix20`) in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (account TEST, broker_account TEST_MWJW, kind 1w, enabled true, state live, status "ready (md2 RL64 2026-10-24, Trader t181u)"), installed by `packages/grokbot/rl64/tools/install_rl64.py`. The md2 host is `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve; its sleeve id is "lz_" + the config id, giving the sibling canonical id lz_s_q07w_s52_ml_cheap5_vix20, whose own package `docs/LZ_S_Q07W_S52_ML_CHEAP5_VIX20-RECREATE.md` already exists in this repo).
- Research lines on the config entry: "DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H52-midlarge-cheap5+stress_vix20 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red (Q07 'red'))"; "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+stress_vix20 w_swing H52 midlarge red band: n 48, names 18, edge +56.5 [14.4, 124.1], q_fam 0.0836, CONFIRMED; px pool n/a UNPROVEN (n<10)"; and the corpus tag definitions (cheap5 = px_fire < 5; cap bands are PIT SEC bands).
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

One cell of the Research Lab Q07 weekly (1w) confluence grid: the Tensor 1W w_swing (Swing) signal in the midlarge (ml) cap band, restricted to fires carrying the cheap5 + stress_vix20 confluence tags, bought only on a fear (red) day, held 52 weeks. It is a fire-consumer: the sleeve_feed composer (tracker ledger + alt-data tags) emits its fires. The UNRESOLVED flag stands because the accounting could not settle this singleton's description from a Test entry or a sleeve module; the config record below is the best evidence on file.

## Full algorithm

Evaluation order, from the rl64 config entry and the recorded family rule:

1. Signal: the composer emits a fire for lane `s_q07w_s52_ml_cheap5_vix20` (source file `shadow/paper_sleeve/live/sleeve_fires_v1.json`) when a Tensor 1W w_swing signal in the midlarge cap band (ml = market cap $2,000,000,000 and above, the reading in desk3/q07_engine.py) carries both tags: cheap5 (px_fire < 5) and stress_vix20 (VIX >= 20, the vix20 gate reading used by both v3 Q07 engines in this repo).
2. Entry policy (config): fear_day; max_delay_minutes 65; window_sessions 5; order capped_limit_day with limit_band_pct 5.0 and limit_buffer_pct 1.0; no_chase_mult 1.02; stock_red true; qqq_red true.
3. Entry gate mechanics for the fear_day policy, from the vendored Lazarus gate in this repo (`sleeves/lazarus/vendor/lazarus/gate.py`, fear_day / capped_limit / size): buy only when QQQ is below its prior close AND the stock is at or below its prior close AND at or below 1.02 x the fire close (the config no_chase_mult), decided inside the afternoon window (close-40 to close-10 minutes) of a session in the red window D+1..D+5 after the fire session (window_sessions 5); nothing by D+5 means skip; every unknown price means wait, never a false trigger. The capped limit is live ref x (1 + limit_buffer_pct), capped by fire close x (1 + limit_band_pct) and by the 1.02x no-chase cap; rounding never lifts a limit above its cap. Sizing under that gate: slot capped at dv20 x cap_pct_of_dv20 / 100, free-cash check against min_slot_fraction, whole shares, and the lane dollar budget shrunk to the remaining budget when that is at least min_slot_fraction of the position.
4. Position management: 1 slot only (max_slots 1); a second fire does not add while the slot is occupied.
5. Exit, per the fire's plan as recorded on the config entry: a 15% disaster stop (L-130; the md2 Lazarus host holds DISASTER_STOP = 15.0), or the time exit at hold = 52 weeks (calendar weeks after the fire week; the price-family params record the exit as the close of the last NYSE session <= D + 364 calendar days). hold_from = fill, hold_unit_kind = 1w, no plan overrides.
6. Sizing (config): budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000, position_usd_by_class {}, one_share_max_usd null. (The sibling merged accounting entry recorded sizing as its gap; the config entry itself carries these values, and they are recorded here without resolving the accounting's UNRESOLVED flag.)
7. Gap that keeps this package UNRESOLVED: no Test catalog entry and no sleeve module docstring or catalog description for this exact id exists in the record; the algorithm above is the config-level record only.

## Files in this repo

- This package: `docs/S_Q07W_S52_ML_CHEAP5_VIX20-RECREATE.md`
- Executable config entry: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry id `s_q07w_s52_ml_cheap5_vix20`); installer `packages/grokbot/rl64/tools/install_rl64.py`
- md2 host: `packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py` (LazarusSleeve, DISASTER_STOP 15.0)
- Vendored Lazarus gate: `sleeves/lazarus/vendor/lazarus/gate.py`
- Sibling package for the lz_ form: `docs/LZ_S_Q07W_S52_ML_CHEAP5_VIX20-RECREATE.md`
- v3 Q07 engines (sibling cells, cap-band and vix20 readings): `desk3/lazarus_q07.py`, `desk3/q07_engine.py`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md` (UNRESOLVED canonical entry)

## Configuration

- Canonical id `s_q07w_s52_ml_cheap5_vix20`; config id the same; the md2 host form is lz_s_q07w_s52_ml_cheap5_vix20. Kind 1w, family w_swing, horizon 52 weeks, cap band midlarge (ml), filters cheap5 + stress_vix20.
- Entry, exit and sizing blocks: verbatim values in the Full algorithm section. Account TEST, enabled true, state live.

## Data inputs

- Sleeve fires: `shadow/paper_sleeve/live/sleeve_fires_v1.json` from the sleeve_feed composer (tracker ledger + alt-data tags), lane `s_q07w_s52_ml_cheap5_vix20`.
- Alt-data tags on the fires: px_fire, VIX, market cap band, as required by this cell's tags.
- Daily bars for the entry-day red checks (the stock and QQQ), the 15% disaster stop and the weekly time exit.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, including its UNRESOLVED status, and the accounting entries for this id.
3. Take the entry id `s_q07w_s52_ml_cheap5_vix20` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` as this cell's configuration; do not edit its entry, exit or sizing fields.
4. Run it under the md2 Lazarus host (`packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py`), feeding the composer fire file and daily bars as described under Data inputs.
5. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated test file for this cell was found in Test):

- A fire missing either tag (cheap5 or stress_vix20), or in the wrong cap band, produces no entry.
- An entry is attempted only on a day when both the stock and QQQ are red, within 5 sessions of the fire and 65 minutes of the trigger, as a capped limit day order that never chases above 1.02x.
- Exactly one position of $1,000 is opened; a second fire while the slot is occupied produces no entry.
- A position down 15% from its fill exits on the disaster stop; any surviving position exits at the 52-week time exit (close of the last NYSE session <= D + 364 calendar days).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
