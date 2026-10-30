# lz_s_wait_olx_books: Recreation Package

## Provenance

- Canonical id: `lz_s_wait_olx_books`; canonical name: OLX R1/R2 books for the other lanes (WAIT); aliases: lz_s_wait_olx_books. The lz_ prefix is the md2 Lazarus host's sleeve id ('lz_' + the config id `s_wait_olx_books`).
- ALL-SLEEVES accounting for this lz_ entry: type other, family 1w, algorithm grade PARTIAL, gaps: sizing not recorded; sources: md2 catalog entry/exit/strategy text. Status history: off. (The separate unprefixed canonical `s_wait_olx_books` is UNRESOLVED in the accounting; its package is `docs/S_WAIT_OLX_BOOKS-RECREATE.md`. This lz_ entry is not flagged unresolved in the plan or the accounting, and its strategy card, below, records its description.)
- Strategy card in Test: `strategies/lazarus/lz-wait-olx.md` ('OLX R1/R2 books': buys fires of 29 frozen OLX clean-support rules scored by the live lab, holds each for its horizon; family Lazarus, asset US equities, timeframe 1d, universe lab panel names, style rule set, status live).
- Config in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_wait_olx_books` (kind 1w, enabled false, state dead, account TEST, status 'WAIT placeholder', research ['DESK_INTEGRATION/DESK_PLAN.md section 6 WAIT: queued'], sizing budget_usd 0, max_slots 0, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000).
- Executable code in Test: `sleeves/lazarus/lazarus.py` (WAIT_SPEC entry for `s_wait_olx_books`, wait_lane resolver, LIVE_RULES, live_row) and the WAIT feed producer module in `sleeves/lazarus/` whose filename is not reproduced here because it carries a token excluded under the repo rule; its header states it is the producer of the six WAIT lanes on the Research Lab frozen rules. The sibling package for the unprefixed id documents that code in full; this package incorporates it for the same lane.
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4609 entries, plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21337 entries; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47379 entries; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7855 entries; no path named for this id). Desk source /home/hatch/workspace/muse-desk-v3 was also read for the v3 engines named below. Code was found in Test, so nothing was vendored.

## What this strategy is

One of the six Lazarus WAIT lanes, in its md2 catalog (lz_) form: it buys fires of the 29 frozen OLX R1/R2 clean-support rules scored by the live lab, and holds each position for its rule's horizon. The source config row is a WAIT placeholder (enabled false, state dead, zero budget/slots); the in-repo Lazarus runtime port runs the lane on its intended frozen spec instead (see live_row sizing below).

## Full algorithm

In evaluation order, from the card, the config and the code in this repo:
1. Fire production (WAIT feed producer): the lane's rule is the 29 live-loadable OLX R1/R2 clean-support frozen rules scored by the live lab producer (frozen rules only, on the lab_live panel); each lab fire carries the frozen rule ids that produced it and each rule's own horizon H. The producer writes `shadow/paper_sleeve/live/wait_fires_v1.json`; a lane whose input is missing keeps its previous fires when the fire day is inside the 5-session window and the evidence is at most 80 hours old (carry-forward, stamped carried_from), with lane status 'input missing'.
2. Lane resolution (`sleeves/lazarus/lazarus.py`): LIVE_RULES maps `s_wait_olx_books` to wait_lane, which takes the wait feed's tradeable fires for this lane, normalises them, and attaches each fire's own entry price cap (limit_cap).
3. WAIT_SPEC for this lane: kind="1d", unit="1d", hold_from="fill", H=126 sessions in the WAIT_SPEC table (the per-rule horizon H comes from each frozen rule); rule text: exit entry + H sessions, i.e. H + 1 from the fill, per frozen rule; no stop; entry at the next session. The card states the same plan: no stop, exit after the rule's H sessions (H + 1 from the fill); buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.
4. live_row sizing: the source row is sized at zero, so the lane takes the paper-test sizing K = min(20, ceil(20 x H / 126)) = 20 positions of $1,000 (budget_usd 20000, max_slots 20, position_usd 1000, global_slot_usd 1000); cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000 stand.
5. Entry mechanics of the runtime port: fires are deduplicated by key and a decided key is skipped; the lane cap counts open plus working entries; a fire of a closed day waits; entry triggers from the open of its research entry bar for max_delay_minutes (65 in the config entry); the capped DAY limit is live reference x (1 + limit_buffer_pct 1.0%), capped at fire close x (1 + limit_band_pct 5.0%); size is the slot dollars subject to the dv20 cap, whole shares and the min_dv20_usd floor; an unknown live price waits. The source config's fear_day entry policy (fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day) is the source record; the port removed that desk-wide gate at cutover, as documented in the sibling package.
6. Exit mechanics of the runtime port: the time exit fires at the first pass at or after time_exit_at - 20 minutes (35 minutes on a half-day close); a plan stop below 99% would sell on the live reference (this lane's plan records no stop, so none fires); exits are one DAY limit at reference x (1 - 1%).

## Files in this repo

- This package: `docs/LZ_S_WAIT_OLX_BOOKS-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/lazarus/lazarus.py` (WAIT_SPEC, wait_lane, LIVE_RULES, live_row), the WAIT feed producer module in `sleeves/lazarus/` (filename not reproduced, see Provenance), `sleeves/lazarus/vendor/lazarus/` (vendored lane package and sleeves.json)
- Config: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_wait_olx_books` (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and the vendor sleeves.json, with the exit-text difference noted in the sibling package)
- Card: `strategies/lazarus/lz-wait-olx.md`; sibling package: `docs/S_WAIT_OLX_BOOKS-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Source config row: kind 1w, label 'OLX R1/R2 books for the other lanes (WAIT)', enabled false, state dead, entry fear_day as in step 5, exit 'the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = n/a)', hold_from plan, hold_unit_kind 1w, sizing budget 0 / slots 0 / position 1000 as in Provenance.
- WAIT_SPEC (code): kind 1d, unit 1d, hold_from fill, H=126 table value with per-rule H. Effective sizing under live_row: max_slots 20, budget_usd 20000, position_usd 1000.

## Data inputs

- Wait fires: `shadow/paper_sleeve/live/wait_fires_v1.json` from the WAIT feed producer, lane `s_wait_olx_books`; upstream, the lab's OLX job outputs / live lab panel (card: 'The lab's OLX job outputs').
- Daily bars and live reference prices for entry caps, the dv20 floor and the time exit.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and the sibling package `docs/S_WAIT_OLX_BOOKS-RECREATE.md` for the full port mechanics.
3. Confirm the WAIT_SPEC entry, wait_lane resolver and live_row sizing for `s_wait_olx_books` in `sleeves/lazarus/lazarus.py` match the algorithm above.
4. Run the WAIT feed producer so wait_fires_v1.json carries this lane's fires, and wire the Lazarus inputs the module header describes.
5. Run the Lazarus pass for lane `s_wait_olx_books`; verify against Verification before treating the recreation as faithful.

## Verification

- WAIT_SPEC contains `s_wait_olx_books` with the kind, hold and rule in Configuration, LIVE_RULES maps it to wait_lane, and live_row yields max_slots 20 and budget_usd 20000 for its zero-sized source row.
- A fire is produced only by one of the 29 frozen OLX R1/R2 rules; a missing upstream input produces carry-forward inside the 5-session / 80-hour bounds and an 'input missing' status, never a fabricated fire.
- Entries follow step 5 and exits step 6, with no stop exit for this lane; one position per symbol, $1,000 per position, K = 20.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
