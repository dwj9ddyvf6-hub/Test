# s_q07w_s52_sm_cheap5_vix20: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_s52_sm_cheap5_vix20", type trend following, family unrecorded, universe / asset class / timeframe / creator not recorded in consulted sources, description: no strategy description recorded. Algorithm grade FULL in the accounting, from the lz_engine config (entry / exit / sizing recorded verbatim below). Alias status: live (source md2_lz_engine). No Test catalog entry (test_entries empty). The accounting marks this strategy UNRESOLVED: singleton with no Test entry and no recorded strategy description; it would be settled by the sleeve module docstring or a catalog description.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start and searched by filename for the canonical id, its alias and its distinguishing tokens, across sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, laz_sleeves/, config/ and docs/; the Silicon, quant-research-backup and Midna trees in this run's workspace were searched the same way. No file named for this id exists in any of those trees: there is no sleeve module, adapter, integration file or per-sleeve ALGORITHM doc for it in Test, and no code for it in Silicon, quant-research-backup or Midna. A prior package for the lz_-prefixed alias of this same cell exists at `docs/LZ_S_Q07W_S52_SM_CHEAP5_VIX20-RECREATE.md` in Test and likewise records no code.
- Shared Q07 family engines ARE in Test (`desk3/q07_engine.py`, `desk3/lazarus_q07.py`), but neither contains a spec for this id, and a generic family engine without this sleeve's spec is not this strategy's code. This package is therefore INCOMPLETE-CODE: no code is vendored and none is reconstructed.

## What this strategy is

A Q07 weekly swing cell: small band, holding period 52 weeks, filters cheap5, vix20, traded only under the recorded fear-day entry policy. Signal generation itself (the underlying Tensor 1W swing signal) is not in the record for this cell: not in the record.

## Full algorithm

Everything the record holds, in evaluation order. Gaps are marked, not filled.

1. Signal: a sleeve fire for this sleeve id. The fire's own signal generation is not in the record.
2. Filters (from the id; family readings in the shared engine `desk3/q07_engine.py` in Test are listed for reference, and whether this exact cell used those exact readings is not in the record):
- cheap5: last close < $5.00.
- vix20: VIX >= 20.0; a missing VIX value fails closed in the family reading.
- Band: small = market cap $300,000,000 to $2,000,000,000.
3. Entry policy (recorded verbatim in the accounting, lz_engine entry config): {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}. That is: buy only on a fear day (stock red and QQQ red), within 5 sessions of the signal and 65 minutes' delay, as a capped limit day order with a 5.0% limit band, 1.0% buffer and a 1.02 no-chase multiplier.
4. Exit (recorded verbatim, lz_engine exit config): the sleeve feed fire's plan: 15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit), hold from fill, hold unit kind 1w, no plan overrides.
5. Sizing (recorded verbatim, lz_engine sizing): {"budget_usd": 1000, "max_slots": 1, "position_usd": 1000, "position_usd_by_class": {}, "one_share_max_usd": null, "cap_pct_of_dv20": 1.0, "min_slot_fraction": 0.9, "global_slot_usd": 1000, "min_dv20_usd": 100000}.

## Files in this repo

- This package: `docs/S_Q07W_S52_SM_CHEAP5_VIX20-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Prior alias package: `docs/LZ_S_Q07W_S52_SM_CHEAP5_VIX20-RECREATE.md`
- Shared family engines (already in Test; NOT this sleeve's code): `desk3/q07_engine.py`, `desk3/lazarus_q07.py`; family doc `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- No sleeve module, adapter or per-sleeve algorithm doc for this id exists in Test. Nothing was vendored, because no code for this strategy was found in any GitHub repo.

## Configuration

- Band: small (market cap $300,000,000 to $2,000,000,000). Holding period: 52 weeks. Timeframe: weekly (1w) per the exit config's hold unit kind.
- Entry policy, exit and sizing: as recorded verbatim in the Full algorithm.
- Universe beyond the band, asset class, cadence and state: not in the record.

## Data inputs

- Sleeve fires for this id, daily bars, the VIX level (the vix20 filter), and positions, as used by the family engines in Test. The exact declared input list for this cell is not in the record.

## Install and run

1. Clone the Test repo.
2. Read this package and the accounting entry in `docs/ALL-SLEEVES.json`.
3. Note the blocker: there is no runnable code for this sleeve in the repo (INCOMPLETE-CODE). Do not substitute the shared family engines and claim this sleeve; a faithful install requires the missing sleeve module / spec, which is not in any searched GitHub repo.
4. If that module is later located, vendor it byte-identical under `engines/universe/s_q07w_s52_sm_cheap5_vix20/`, add its spec, and re-run the Verification checklist below before any use.

## Verification

No test for this sleeve was found in Test. Behaviour checklist from the recorded algorithm:

- No entry occurs except on a fear day (stock red and QQQ red) within 5 sessions of the signal, as a capped limit day order with the recorded 5.0% band, 1.0% buffer and 1.02 no-chase multiplier.
- Every filter in {cheap5, vix20} passes under the family readings listed; a fire failing any one produces no entry.
- At most 1 slot is held, sized from the recorded $1,000 position / budget values.
- The position exits on the 15% disaster stop or at the 52-week time exit, and on no other recorded rule.
