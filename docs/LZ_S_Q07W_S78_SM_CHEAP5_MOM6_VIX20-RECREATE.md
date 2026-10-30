# lz_s_q07w_s78_sm_cheap5_mom6_vix20: Recreation Package

Status: INCOMPLETE-CODE. No code for this exact sleeve was found in any searched GitHub repo; see Provenance. This package records everything the record holds and does not reconstruct code.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Q07 w_swing H78 small cheap5+mom6+stress_vix20 (test)", type trend following, family 1w. Algorithm grade PARTIAL, gap: sizing not recorded in any consulted source. Sources: md2 catalog entry/exit/strategy text. Alias record source md2_catalog, status installed. No Test catalog entry (test_entries empty).
- Search record: Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, docs/) plus Silicon, quant-research-backup and Midna trees were searched by filename for the canonical id, its alias and its distinguishing tokens. No file named for this id or for its distinguishing tokens (cheap5 with vix20, with or without mom6, in the s78 small swing cell) exists in any of those trees; there is no `sleeves/`, `adapters3/` or `integration/` module for it and no `docs/S_Q07W_S78_SM_CHEAP5...VIX20-ALGORITHM.md` doc in Test.
- Shared Q07 family engines ARE in Test (`desk3/q07_engine.py`, `desk3/lazarus_q07.py`), but neither contains a spec for this id: `desk3/lazarus_q07.py` SPECS has no entry for it (its closest s78 small swing entry is the wcov sibling, a different filter set), and `desk3/q07_engine.py` is a generic `evaluate_q07(spec, view, ctx)` that requires a caller-supplied spec which is not in the record for this id. A generic family engine without this sleeve's spec is not this strategy's code.

## What this strategy is

Q07 w_swing H78 small cheap5+mom6+stress_vix20 (test): a Q07 weekly (1w) swing cell, small-cap band, holding period 78 weeks, with the recorded filters cheap5 (close < $5), mom6 (positive 6-month momentum) and stress_vix20 (VIX >= 20), traded only under the recorded fear-day entry policy below.

## Full algorithm

Everything the accounting record holds, in evaluation order. Gaps are marked, not filled.

1. Signal: a sleeve_feed composer fire (tracker ledger + alt-data tags, `shadow/paper_sleeve/live/sleeve_fires_v1.json`) for this sleeve id. The underlying Tensor 1W swing signal generation is not in the record for this cell.
2. Filters (from the name and the family readings in the shared engines in Test, `desk3/q07_engine.py` / `desk3/lazarus_q07.py`): cheap5 (close < $5), mom6 (positive 6-month momentum) and stress_vix20 (VIX >= 20). In `desk3/q07_engine.py` the readings are: cheap5 = last close < $5; mom6 = close above the close 126 sessions ago; vix20 = VIX >= 20; small band = market cap $300M to $2,000M. Whether this exact cell used those exact readings is not in the record: not in the record.
3. Entry policy (recorded verbatim in the accounting): {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}. That is: buy only on a fear day (stock red and QQQ red), within 5 sessions of the signal and 65 minutes' delay, as a capped limit day order with a 5.0% limit band, 1.0% buffer and a 1.02 no-chase multiplier.
4. Exit (recorded): the sleeve feed fire's plan: 15% disaster stop / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit), hold from fill, hold unit kind 1w, no plan overrides.
5. Sizing: not in the record (the accounting's named gap). The family engines in Test use 1 slot at $1,000 for most Q07 cells, but that value is not recorded for this cell and must not be assumed as its sizing.

## Files in this repo

- This package: `docs/LZ_S_Q07W_S78_SM_CHEAP5_MOM6_VIX20-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Shared family engines (already in Test; NOT this sleeve's code, listed so a recreator does not mistake them for it): `desk3/q07_engine.py`, `desk3/lazarus_q07.py`, family doc `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- No sleeve module, adapter or per-sleeve algorithm doc for this id exists in Test. Nothing was vendored for this package, because no code for this strategy was found in any GitHub repo.

## Configuration

- Universe / band: small (the name's `sm` band). Timeframe: weekly (1w), hold 78 weeks. Asset class: not in the record.
- Entry policy and exit as recorded in the Full algorithm. Sizing, cadence and state: not in the record.

## Data inputs

- Sleeve fires from the sleeve_feed composer (tracker ledger + alt-data tags): `shadow/paper_sleeve/live/sleeve_fires_v1.json` (per the accounting filter record).
- Daily bars for the candidate names and QQQ, and the VIX value, as required by the recorded filters and the fear-day gate: inferred from the filter definitions in the shared family engines; the exact feed list for this cell is not in the record.

## Install and run

1. Clone the Test repo.
2. Read `docs/ALL-SLEEVES.json` for this entry and this package.
3. STOP: there is no code for this exact sleeve in the repo to install. Do not substitute the wcov sibling module or a hand-written reconstruction and present it as this strategy.
4. To recreate it, first obtain the original spec / sleeve module for `lz_s_q07w_s78_sm_cheap5_mom6_vix20` (its entry in the Lazarus config or its desk3 spec) from the original desk, then wire it to `desk3/q07_engine.py` or `desk3/lazarus_q07.py` using the recorded entry policy, filters and 78-week / 15% exit above.
5. Verify any such recreation against the Verification checklist before any use.

## Verification

No tests for this sleeve were found in Test. Behaviour checklist from the recorded algorithm:

- No entry except on a fear day (stock red and QQQ red), within 5 sessions of the fire, as a capped limit day order with the recorded band, buffer and no-chase multiplier.
- No entry unless every recorded filter passes: cheap5 (close < $5), mom6 (positive 6-month momentum) and stress_vix20 (VIX >= 20).
- Exit at a 15% fall from fill, or at 78 calendar weeks after the fire week, whichever the fire's plan reaches first.
- A name at or above $5, with non-positive 126-session momentum, or with VIX under 20, must not enter.
