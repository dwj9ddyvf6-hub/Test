# lz-wait-olx — Recreation Package

## Provenance

- Canonical name: OLX R1/R2 books; algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: lz_wait_olx_books.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "OLX R1/R2 books" (also docs/ALL-SLEEVES.md); Test catalog entry 'lz-wait-olx' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

- Sanitized for the public repo: 14 mention(s) of the originating research family name were replaced with a neutral placeholder; no rule, parameter, or code content was changed.

## What this strategy is

OLX R1/R2 books (WAIT lane s_wait_olx_books): buys fires of the 29 frozen OLX clean-support R1/R2 rules scored by the live lab, holding each position for its rule horizon. Family lazarus; type other; universe Lab panel names; asset class US equities; timeframe 1d.

## Full algorithm

Signal producer: sleeves/lazarus/the family research line_wait_feed.py, functions olx(books, since, until), lab_fires(...) and olx_ids_from_readme(...); producer job sleeves/lazarus/the family research line_wait.py, function olx_pass(...). Evaluation order:
1. Rule set: the frozen ids in olx_r12_other.ids (vendored with the frozen spec.json files; 29 live-loadable rules of the 30-row README rule table). When that file is absent, the ids fall back to the README table rows flagged live-loadable (regex OLX_ROW parses id, lane, signal, hold, clean-in flags and the live-loadable flag).
2. Lab pass (the family research line_wait.py): run the live lab producer (lab_live.mjs --frozen-ids --no-books, frozen rules only, on the lab_live panel) for the 9 OLX jobs: (1D green full), (1D green covered), (1D swing full), (1D swing covered), plus the remaining lane/signal/universe combinations enumerated in OLX_JOBS in that module; outputs land in DESK_INTEGRATION/lab_live/out/olx/<lane>-<signal>-<universe>.json. The accounting records no R1/R2 rule definitions themselves: the individual rule conditions are not in the record (gap, see below).
3. Fire selection (olx()): for each lab job output fire, for each frozen rule id on that fire whose frozen_rules entry carries a horizon H, emit one fire tagged :H<H> with why "olx rule <rid> (<job>)". Fires outside [since, until] are skipped; duplicate keys merge their why lists.
4. Hold: plan = plan(H + 1, "sessions") (the s_rules mechanics: exit after the rule's H sessions, H + 1 from the fill), no stop.
Execution mechanics (strategies/lazarus card for this lane, master-desk lazarus.live_row mechanics it names):
- Entry: buy from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.
- Exit execution: time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.
- The fire plan itself (the family research line_wait_feed.py plan()) is: scheme 'no stop / time exit <N> <unit>', stop_pct 99.0, first_target_pct None, sell_fraction 1.0, rest 'time', exit_on_engine_sell False.
- Fire window / freshness (the family research line_wait_feed.py): WINDOW_SESSIONS = 5, FEED_MAX_AGE_H = 80; a lane whose input is missing keeps its previous fires whose fire day is inside the 5-session window and whose evidence is at most 80 h old (carry_forward), stamped carried_from, instead of losing them.
Accounting gaps (marked, not filled): entry/signal rule not recorded in any consulted source in the accounting (the R1/R2 rule definitions appear in no consulted source); exit rule not recorded in the accounting; sizing not recorded in the accounting. The code and the strategy card in this repo supply the mechanics above; the frozen rules' own conditions remain not in the record.

## Files in this repo

- This package: `docs/LZ_WAIT_OLX-RECREATE.md`
- Signal producer: `sleeves/lazarus/the family research line_wait_feed.py` (olx(), lab_fires(), olx_rules_from_readme(), olx_ids_from_readme())
- Producer job: `sleeves/lazarus/the family research line_wait.py` (olx_pass(), OLX_JOBS, olx_ids())
- Strategy card: `strategies/lazarus/lz-wait-olx.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md` (strategy entry "OLX R1/R2 books"); catalog entry `lz-wait-olx` in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/lazarus/the family research line_wait_feed.py, sleeves/lazarus/the family research line_wait.py, desk3/lazarus.py and strategies/lazarus/lz-wait-*.md in this repo, so no further repo was needed for code; trees of dwj9ddyvf6-hub/Silicon (21,337 entries), dwj9ddyvf6-hub/quant-research-backup (47,379 entries) and dwj9ddyvf6-hub/Midna (7,855 entries) were also listed and carry no lazarus WAIT-lane module). Code was already in Test, so nothing was vendored.

## Configuration

- Lane id s_wait_olx_books (alias lz_wait_olx_books); Test catalog status: live; strategy card status: live.
- Frozen rule ids: olx_r12_other.ids (29 live-loadable rules); lab jobs: the 9 (lane, signal, universe) combinations in OLX_JOBS in sleeves/lazarus/the family research line_wait.py.
- Sizing (strategy card): $1,000 a position; K = 20; fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data inputs

- The lab's OLX job outputs (DESK_INTEGRATION/lab_live/out/olx/*.json: fires with frozen rule ids, frozen_rules with per-rule horizons, asof, panel_last_day).
- Frozen spec files: olx_r12_other.ids and the s_wait_olx_books README rule table (fallback).
- Output: shadow/paper_sleeve/live/wait_fires_v1.json (key fires_wait).

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/lazarus/the family research line_wait_feed.py` and `sleeves/lazarus/the family research line_wait.py` at those paths, with the frozen spec files (olx_r12_other.ids, the lane README) under DESK_INTEGRATION/sleeve_specs/s_wait_olx_books/.
3. Run the producer job so the OLX lab pass writes the 9 job outputs, then the feed composition writes wait_fires_v1.json (python the family research line_wait_feed.py --research <root>/inputs/lazarus --scratch <root>/cache/the family research line/scratch).
4. Run the desk cycle so the Lazarus live engine consumes the fires and applies the entry/exit execution mechanics above.
5. First evaluation: fixture one lab output whose fire carries a frozen rule with horizon H; confirm exactly one s_wait_olx_books fire with plan max_bars H + 1 sessions.

## Verification

- Fixture above: exactly one fire per (symbol, rule) with a no-stop plan of H + 1 sessions.
- Fixture with a rule id not in olx_r12_other.ids, or a frozen rule with no horizon: no fire for that rule.
- Fixture with no OLX lab output: the lane reports input missing and carries forward prior fires inside the 5-session / 80 h window instead of erasing them.
- A held position reaches its rule horizon (H + 1 from the fill): one full time exit; no price stop fires before it.
