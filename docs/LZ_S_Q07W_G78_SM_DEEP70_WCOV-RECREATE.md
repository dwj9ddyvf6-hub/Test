# LZ_S_Q07W_G78_SM_DEEP70_WCOV Recreation Package

Status: INCOMPLETE-CODE. No code file carrying this exact canonical id was located in any GitHub repo searched (see Provenance). This package holds the best evidence on file and does not claim that code for this exact lane is present in this repo.

## Provenance

- Canonical id: `lz_s_q07w_g78_sm_deep70_wcov`
- Canonical name: Q07 w_green H78 small deep70+wiki_cov (test)
- Aliases in the ALL-SLEEVES accounting: lz_s_q07w_g78_sm_deep70_wcov
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_green H78 small deep70+wiki_cov (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Source accounting: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` (also `docs/ALL-SLEEVES.md`), strategy entry named above. Algorithm grade in the accounting: PARTIAL. Unresolved in the accounting: false.
- Algorithm sources per the accounting: md2 catalog entry/exit/strategy text. Gaps per the accounting: sizing not recorded in any consulted source.
- Type in the accounting: trend following. Family: 1w. Universe in the accounting: not recorded in consulted sources. Timeframe in the accounting: not recorded. Asset class in the accounting: not recorded.
- Code searched in:
  - Test (dwj9ddyvf6-hub/Test), fresh recursive tree at batch start: sleeves/, strategies/, packages/, adapters3/, integration/, desk3/, docs/ searched for the exact canonical id and for the id without the lz_ prefix
  - Silicon (dwj9ddyvf6-hub/Silicon), recursive tree: no q07 path found (the GitHub tree response is truncated, so this is a tree-level search, not a content search)
  - quant-research-backup (dwj9ddyvf6-hub/quant-research-backup), recursive tree: no q07 path found (tree-level search, truncated response)
  - Midna (dwj9ddyvf6-hub/Midna), recursive tree: no q07 path found (tree-level search)
- Related code found in Test for the distinct roster id `s_q07w_g78_sm_deep70_wcov` (the same name without the lz_ prefix; the accounting lists that id as a separate canonical strategy, so it is NOT claimed as this lane's code): `sleeves/s_q07w_g78_sm_deep70_wcov.py`, `adapters3/s_q07w_g78_sm_deep70_wcov.py`, `integration/s_q07w_g78_sm_deep70_wcov_adapter.py`, an entry in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, and the shared engines `desk3/q07_engine.py` and `desk3/lazarus_q07.py`.
- Shared family evidence in Test: `desk3/q07_engine.py` (Q07 alt-data confluence engine), `desk3/lazarus_q07.py` (Lazarus Q07 weekly lanes, catalog section 4.1 family rule), `docs/Q07-1W-SWING-LZ-ALGORITHM.md`, and `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`.

## What this strategy is

A Q07 weekly (1w) trend-following cell: family w_green (Green), cap band small (sm), hold 78 weeks, with the alt-data filter set deep70, wcov. It is one cell of the Q07 confluence grid recorded in the md2 catalog. The accounting description is exactly the canonical name above; no fuller description is in the record.

## Full algorithm

Algorithm grade PARTIAL in the accounting. Everything the record holds is written below; specific gaps are marked 'not in the record' and are not filled in.

Evaluation order, as recorded for this lane and for the Q07 family in Test:

1. Signal: a sleeve_feed fire for this lane. Data per the accounting filter record: sleeve_feed composer (tracker ledger + alt-data tags) :: `shadow/paper_sleeve/live/sleeve_fires_v1.json`. The family rule in `desk3/lazarus_q07.py` and `desk3/q07_engine.py`: take the Tensor 1W signal of the named family (here Green / w_green) in the named cap band (here small). Cap-band dollar bounds for this exact lane: not in the record. (The distinct `desk3/q07_engine.py` reading for its own lanes is sm = $300,000,000 to $2,000,000,000; that engine carries no spec for this lane, so that bound is a family-engine reading, not a recorded parameter of this lane.)
2. Filters, all must pass: deep70, wcov. Filter readings found in Test family code and config research notes:
   - deep70: close at or below 70% of the trailing 252-session high, i.e. at least a 30% drawdown (desk3/q07_engine.py); desk3/lazarus_q07.py also accepts an explicit deep70 tag, a drawdown_from_high >= 0.30 tag, or price <= 0.70 * high_52w. Config research note gives a different research-stage reading: deep70 = c_depth60 >= 70. Which reading governed the original md2 lane is not in the record; both Test readings are named here, neither is presented as the original md2 definition.
   - wcov (wiki_cov): Wikipedia coverage present: wiki_views_30d > 0 (desk3/q07_engine.py); desk3/lazarus_q07.py: wiki_cov tag true, or wiki_views > 0.
   A filter with no evidence fails closed in both Test family engines.
3. Entry timing and order, exactly as recorded in the accounting entry record for this lane:
   - `[lz_s_q07w_g78_sm_deep70_wcov] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}`
   In plain terms from that record: policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day. The family reading in Test code is: buy only on a QQQ-down day within 5 sessions of the signal, and the stock must also be red.
4. Exit, exactly as recorded in the accounting exit record for this lane:
   - `[lz_s_q07w_g78_sm_deep70_wcov] {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}`
   In plain terms: 15% disaster stop (recorded as L-130) and a time exit at 78 weeks; hold is counted from fill, in calendar weeks after the fire week, as a desk weekly time exit. stop_pct, max_bars and rest are null in the record; plan_overrides is empty.
5. Position management: 1 slot only in the Test family engines (an occupied slot blocks new entries in `desk3/q07_engine.py`); whether that rule governed this exact md2 lane is not in the record. No other position-management rule is in the record.

Gaps marked as not in the record:
- Sizing: not in the record (the accounting gap list says sizing not recorded in any consulted source). The Test family standard is 1 slot at $1,000 in both family engines, and the related config entries below use that standard where present; that standard is NOT recorded for this exact lane in the accounting.
- Universe, timeframe and asset class beyond kind 1w / family 1w: not in the record.
- Exact original code for this lane: not located (see Provenance).

## Files in this repo

- This package: `docs/LZ_S_Q07W_G78_SM_DEEP70_WCOV-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Shared Q07 family code present in Test (family rule, not a spec for this exact lane): `desk3/q07_engine.py`, `desk3/lazarus_q07.py`
- Shared Q07 family config present in Test: `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`
- Family algorithm doc present in Test: `docs/Q07-1W-SWING-LZ-ALGORITHM.md`
- Related distinct roster lane (separate canonical strategy in the accounting): `sleeves/s_q07w_g78_sm_deep70_wcov.py`, `adapters3/s_q07w_g78_sm_deep70_wcov.py`, `integration/s_q07w_g78_sm_deep70_wcov_adapter.py`, `docs/S_Q07W_G78_SM_DEEP70_WCOV-ALGORITHM.md`
- Related config entry for `s_q07w_g78_sm_deep70_wcov` in the sleeves.json above: kind 1w, enabled True, state live, sizing budget_usd 1000, max_slots 1, position_usd 1000. Research notes on that entry:
  - DESK_INTEGRATION/EDGE_INVENTORY.csv Q07-w_green-H78-small-deep70+wiki_cov (CONFIRMED; ADD paper-test ($1k) -> core candidate)
  - CORPUS_AUDIT/out/Q07_confluence_cells.csv deep70+wiki_cov w_green H78 small red band: n 58, names 49, edge +180.8 [82.7, 323.7], q_fam 0.0136, CONFIRMED
  - CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)
- Vendored files for this package: none. Nothing was vendored, because no code for this exact canonical id was located outside Test, and reconstructing code from the algorithm description is not permitted for this program.

## Configuration

- Kind: 1w (weekly). Family: w_green. Cap band: small. Hold: 78 weeks.
- Filters: deep70, wcov
- Entry: policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
- Exit: 15% disaster stop / time exit at 78 weeks from fill.
- Sizing: not in the record for this lane.
- Cadence: weekly lane consuming sleeve_feed fires; exact run cadence for this lane is not in the record.
- State: installed, per the accounting alias status history (source md2_catalog, status installed). Enabled / live state for this exact lz_ id: not in the record.

## Data inputs

- sleeve_feed composer (tracker ledger + alt-data tags), file `shadow/paper_sleeve/live/sleeve_fires_v1.json`, per the accounting filter record.
- In the Test family engines: fires, daily bars for the symbol and for QQQ, VIX where a vix filter applies (not a filter of this lane), and current positions. Which of those inputs the original md2 lane consumed beyond the sleeve_feed file is not in the record.
- Alt-data tags named by the filters of this lane, per the filter definitions above.

## Install and run

This package is INCOMPLETE-CODE, so a faithful install of this exact lane is not possible from this repo alone. The steps below are the honest recreation path using the family machinery already in Test; they do not claim to reproduce the original md2 lane code.

1. Clone dwj9ddyvf6-hub/Test.
2. Read this package, `docs/ALL-SLEEVES.json` entry for Q07 w_green H78 small deep70+wiki_cov (test), `desk3/q07_engine.py` and `desk3/lazarus_q07.py`.
3. Confirm there is no spec entry for this canonical id in either family engine. Do not substitute the spec of a different lane and present it as this lane.
4. To experiment with the family rule, add a spec for this lane to a local copy of a family engine using only the parameters recorded in the Configuration section above, with sizing left unset because sizing is not in the record, and run it only as a research experiment, not as a recreation of the original.
5. Feed it sleeve_feed fires in the recorded file shape and daily bars, and check behaviour against the Verification checklist below.

## Verification

No tests for this exact lane were found in Test. Behavior checklist, from the algorithm section above:

- A fire older than 5 sessions produces no entry.
- No entry on a day when QQQ is not red, and no entry when the stock is not red.
- Every named filter (deep70, wcov) must pass with positive evidence; a missing tag or missing data produces no entry.
- An entry order is a capped limit day order respecting limit_band_pct 5.0, limit_buffer_pct 1.0 and no_chase_mult 1.02, within max_delay_minutes 65.
- An open position exits at a 15% disaster stop, or at the 78-week time exit counted from fill, whichever comes first.
- Sizing cannot be verified for this lane: it is not in the record.
