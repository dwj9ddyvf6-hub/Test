# lz_s_wait_chase - Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "CHASE (WAIT)", type momentum (classification evidence: Test catalog entry lz-wait-chase: style Momentum, weekly lane on a liquid cross-section; this row is its lz_s test form), algorithm grade PARTIAL with gap: sizing not recorded in the accounting; alias lz_s_wait_chase (md2_catalog, status off).
- Accounting record: entry policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day; exit: the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = n/a), hold_from plan, hold_unit_kind 1w; data: sleeve_feed composer :: shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Code found in Test already: `sleeves/lazarus/lazarus.py` (WAIT_SPEC entry for s_wait_chase, wait_lane resolver, LIVE_RULES, live_row) and the WAIT feed producer in `sleeves/lazarus/`, both documented in full in the existing package `docs/S_WAIT_CHASE-RECREATE.md` for the same lane without the lz_ prefix; config rows in `sleeves/lazarus/vendor/lazarus/sleeves.json`, `packages/grokbot/rl64/lz_engine/config/sleeves.json` and `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` (id s_wait_chase, label "CHASE (WAIT)").
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

CHASE (WAIT): the lz_s test form of the Lazarus WAIT lane CHASE. A placeholder row in the original sleeve_feed config (enabled false, state dead in the vendor copy for s_wait_chase) that the Test Lazarus runtime port runs on its frozen Research Lab spec: weekly Cyan fires in the top tenth of 126-day momentum within 5% of their 63-day high, held 52 weeks.

## Full algorithm

From `docs/S_WAIT_CHASE-RECREATE.md` (the code that runs this lane in Test), in evaluation order:

1. Fire production (WAIT feed producer in `sleeves/lazarus/`): a tracker 1W Cyan fire whose mom126 rank against the liquid cross-section LQ is >= 0.90 (mom126 = close[t]/close[t-126] - 1, rank by searchsorted right / n, >= 50 LQ names; LQ = bar present, dv20 >= $0.5M UC pre-filter, SIC operating company and not an ETF, close >= $5, dv20 >= $1M) and close[t] / max(close over the last 63 sessions, minimum 40 periods) - 1 > -0.05. The producer writes `shadow/paper_sleeve/live/wait_fires_v1.json`; a lane with a missing input keeps its previous fires when the fire day is inside the 5-session window and the evidence is at most 80 hours old (carry-forward, stamped carried_from), with lane status "input missing".
2. Lane resolution (`sleeves/lazarus/lazarus.py`): LIVE_RULES maps s_wait_chase to wait_lane, which takes the wait feed's tradeable fires for this lane, normalises them, and attaches each fire's entry price cap (limit_cap).
3. WAIT_SPEC for this lane: kind="1w", unit="1w", hold_from="plan", H=52*5 sessions; rule text: exit W52 from the 1W fire week; no stop; entry at the next open.
4. Sizing (live_row): the source row is sized at zero (budget_usd 0, max_slots 0), so the lane takes the paper-test sizing: K = min(20, ceil(20 x H / 126)) = 20 positions of $1,000, i.e. budget_usd 20000, max_slots 20, position_usd 1000, global_slot_usd 1000; cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000 stand.
5. Entry mechanics of the runtime port: fires are deduplicated by key and a decided key is skipped; the lane cap counts open plus working entries; a fire of a closed day waits; entry triggers from the open of its research entry bar for max_delay_minutes 65; the capped DAY limit is live reference x (1 + limit_buffer_pct 1.0%), capped at fire close x (1 + limit_band_pct 5.0%); size is slot dollars subject to the dv20 cap, whole shares and the min_dv20 floor; an unknown live price waits. The source config's fear_day gate was removed at cutover as a desk-wide doctrine in the port (both readings are recorded in docs/S_WAIT_CHASE-RECREATE.md).
6. Exit mechanics: the time exit fires at the first pass at or after time_exit_at - 20 minutes (35 minutes on a half-day close); a plan stop below 99% would sell on the live reference (this lane records no stop, so none fires); exits are one DAY limit at reference x (1 - 1%). Plan exit: W52 from the 1W fire week; no stop.

## Files in this repo

- This package: `docs/LZ_S_WAIT_CHASE-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/lazarus/lazarus.py`, the WAIT feed producer module in `sleeves/lazarus/` (see docs/S_WAIT_CHASE-RECREATE.md for its identification), `sleeves/lazarus/vendor/lazarus/`
- Config (already in Test): `sleeves/lazarus/vendor/lazarus/sleeves.json`, `packages/grokbot/rl64/lz_engine/config/sleeves.json`, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json`, each with a row for s_wait_chase
- Existing package for the same lane: `docs/S_WAIT_CHASE-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

Source config row (vendor copy, verbatim in docs/S_WAIT_CHASE-RECREATE.md): id s_wait_chase, kind 1w, label "CHASE (WAIT)", enabled false, state dead, status_text "WAIT placeholder", entry fear_day / 65 / 5.0 / 1.0 / 5 / 1.02 / stock_red true / qqq_red true / capped_limit_day, sizing budget_usd 0, max_slots 0, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Effective sizing under live_row: max_slots 20, budget_usd 20000. WAIT_SPEC: kind 1w, hold_from plan, H = 52*5 sessions. The lz_s accounting row's state is off (md2_catalog).

## Data inputs

Wait fires: `shadow/paper_sleeve/live/wait_fires_v1.json` from the WAIT feed producer, lane s_wait_chase; upstream tracker ledger and the tracker engine's daily store; daily bars and live reference prices for entry caps, the dv20 floor and the time exit.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read this package and `docs/S_WAIT_CHASE-RECREATE.md`.
3. Confirm the WAIT_SPEC entry, wait_lane resolver and live_row sizing for s_wait_chase in `sleeves/lazarus/lazarus.py`.
4. Run the WAIT feed producer so wait_fires_v1.json carries this lane's fires.
5. Run the Lazarus pass for this lane and verify against the Verification section.

## Verification

- WAIT_SPEC in `sleeves/lazarus/lazarus.py` contains s_wait_chase with the kind, hold and rule in Configuration, LIVE_RULES maps it to wait_lane, and live_row yields max_slots 20 and budget_usd 20000 for its zero-sized source row.
- A fire is produced only when the rule in step 1 holds exactly; a missing upstream input produces carry-forward inside the 5-session / 80-hour bounds and an "input missing" status, never a fabricated fire; entries follow step 5 and exits step 6, with no stop exit for this lane.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
