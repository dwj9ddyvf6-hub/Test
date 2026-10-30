# lz_s_q07w_c52_sm_cheap5_mom6_vix20: Recreation Package

Status: INCOMPLETE-CODE. The code for this strategy could not be located in any GitHub repo searched (listed in Provenance). This package records everything the record holds and does not reconstruct code from the description.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Q07 w_cyan H52 small cheap5+mom6+stress_vix20 (test)", type trend following, family 1w. Algorithm grade PARTIAL in the accounting, with the recorded gap: sizing not recorded in any consulted source. Alias `lz_s_q07w_c52_sm_cheap5_mom6_vix20` (md2_catalog status: installed). No Test catalog entry in the accounting (test_entries empty).
- Code search performed for this package: the fresh Test tree taken at batch start was searched for the sleeve id (with and without the `lz_` prefix), for the wrapper / adapter / integration paths every sibling Q07 lane has, for a row in `config/sleeves.json`, and for a SPECS row in the shared Q07 engine `desk3/lazarus_q07.py`. None exists: there is no `s_q07w_c52_sm_cheap5_mom6_vix20` wrapper, adapter, config row or SPECS entry in Test. (The engine does hold the different lane `s_q07w_c52_sm_cheap5_ins2_mom6`, filters cheap5/ins2/mom6, which is not this strategy: its filter set differs.) The Silicon, quant-research-backup and Midna trees were searched for Q07 / lazarus code and for this sleeve id; no matching file was found in any of them.
- Because no code was found, nothing was vendored for this package, and the algorithm below is exactly what the accounting record holds, no more.

## What this strategy is

A Q07 weekly lane as recorded: w_cyan family, 52-week hold (H52), small cap band, with the cheap5 + mom6 + stress_vix20 filter tokens carried in its recorded name. Beyond the accounting record quoted in Full algorithm, what this strategy is: not in the record.

## Full algorithm

Everything the accounting record holds, verbatim in substance:

- Entry record: {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}.
- Exit record: {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}.
- Data / filter record: sleeve_feed composer (tracker ledger + alt-data tags), fire file shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Sizing: not in the record (the accounting's recorded gap).
- The precise filter definitions for cheap5, mom6 and vix20 as applied to this lane, the fire shape it consumed, its slot count and budget, and its evaluation order beyond the entry/exit records above: not in the record (no code was located; see Provenance). Sibling Q07 lanes in Test run on `desk3/lazarus_q07.py`, but that engine holds no row for this lane, so its rules are not claimed for this strategy.

## Files in this repo

- This doc: `docs/LZ_S_Q07W_C52_SM_CHEAP5_MOM6_VIX20-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md` (the strategy's only record in Test).
- No sleeve code, adapter, config row or engine SPECS row for this canonical id exists in Test (searched as listed in Provenance), and no code was vendored by this package.

## Configuration

- Canonical id: `lz_s_q07w_c52_sm_cheap5_mom6_vix20`; recorded hold 52 weeks; recorded entry window 5 sessions; recorded order type capped_limit_day with limit_band_pct 5.0, limit_buffer_pct 1.0, max_delay_minutes 65, no_chase_mult 1.02.
- Universe, timeframe beyond the weekly (1w) family tag, sizing, cadence and state: not in the record.

## Data inputs

- Per the accounting filter record: the sleeve_feed composer (tracker ledger + alt-data tags), fire file shadow/paper_sleeve/live/sleeve_fires_v1.json. Anything further: not in the record.

## Install and run

1. This package cannot be installed or run: no code for this strategy was located in any GitHub repo searched (Test, Silicon, quant-research-backup, Midna; see Provenance).
2. To complete it, the original lane code (a wrapper plus an engine SPECS row, by the pattern of its sibling lanes) would have to be recovered from a source outside those repos and vendored byte-identical; until then the strategy is graded INCOMPLETE-CODE.
3. Do not substitute a sibling lane's code or parameters for this lane's: the sibling with the closest name differs in its filter set.

## Verification

- The absence claim is itself verifiable: search the fresh Test tree, `config/sleeves.json` and `desk3/lazarus_q07.py` for `c52_sm_cheap5_mom6_vix20`; no wrapper, config row or SPECS row is present.
- Behaviour verification of a recreation is not possible until code is recovered; no checklist is offered, because none can be derived from the record alone without inventing rules.
