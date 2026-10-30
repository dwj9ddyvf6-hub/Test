# lz-wait-q14 — Recreation Package

## Provenance

- Canonical name: Q14 under-$5 weekly book; algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: lz_wait_q14.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q14 under-$5 weekly book" (also docs/ALL-SLEEVES.md); Test catalog entry 'lz-wait-q14' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

- Sanitized for the public repo: 11 mention(s) of the originating research family name were replaced with a neutral placeholder; no rule, parameter, or code content was changed.

## What this strategy is

Q14 under-$5 weekly book (WAIT lane s_wait_q14): buys tier-A weekly Cyan or Green tracker fires closing at or under $5.00, and holds 78 weeks. Family lazarus; type trend following (classification evidence: the q14 rule follows the weekly trend state in cheap names); universe Tracker universe; asset class US equities; timeframe 1w.

## Full algorithm

Signal producer: sleeves/lazarus/the family research line_wait_feed.py, function q14(L), constants Q14 = dict(px_cap=5.0, tier="A", sigs=("cyan", "green"), hold_weeks=78). Evaluation order:
1. Iterate the tracker ledger fires in sorted key order; keep only lane "1w" with signal cyan or green.
2. Tier and price: ue = the fire's addons_ue tag (ue_tag tier, = research tier_c1); close_D = ue values close_D, else the fire record close. Skip unless tier is exactly "A" and close_D is present and <= 5.00.
3. Emit a fire: lane s_wait_q14, unit wait-q14-W78, plan = plan(78, "weeks") (no stop / time exit 78 weeks), strategy text "Q14 cheap-stock book (test)", limit_cap = 5.00 (the README's OPG limit at 5.00; the desk's next-open DAY limit capped at $5.00 stands in for the OPG order, the one named divergence for this lane).
Execution mechanics (strategies/lazarus card for this lane, master-desk lazarus.live_row mechanics it names):
- Entry: buy from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.
- Exit execution: time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.
- The fire plan itself (the family research line_wait_feed.py plan()) is: scheme 'no stop / time exit <N> <unit>', stop_pct 99.0, first_target_pct None, sell_fraction 1.0, rest 'time', exit_on_engine_sell False.
- Fire window / freshness (the family research line_wait_feed.py): WINDOW_SESSIONS = 5, FEED_MAX_AGE_H = 80; a lane whose input is missing keeps its previous fires whose fire day is inside the 5-session window and whose evidence is at most 80 h old (carry_forward), stamped carried_from, instead of losing them.
Accounting gaps (marked, not filled): the accounting records no entry, exit or sizing rule in its consulted sources; the code and the strategy card in this repo supply the complete rule above.

## Files in this repo

- This package: `docs/LZ_WAIT_Q14-RECREATE.md`
- Signal producer: `sleeves/lazarus/the family research line_wait_feed.py` (q14(), Q14 constants, plan(), fire())
- Producer job: `sleeves/lazarus/the family research line_wait.py`
- Strategy card: `strategies/lazarus/lz-wait-q14.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md` (strategy entry "Q14 under-$5 weekly book"); catalog entry `lz-wait-q14` in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/lazarus/the family research line_wait_feed.py, sleeves/lazarus/the family research line_wait.py, desk3/lazarus.py and strategies/lazarus/lz-wait-*.md in this repo, so no further repo was needed for code; trees of dwj9ddyvf6-hub/Silicon (21,337 entries), dwj9ddyvf6-hub/quant-research-backup (47,379 entries) and dwj9ddyvf6-hub/Midna (7,855 entries) were also listed and carry no lazarus WAIT-lane module). Code was already in Test, so nothing was vendored.

## Configuration

- Lane id s_wait_q14 (alias lz_wait_q14); Test catalog status: waiting; strategy card status: waiting.
- Q14 constants: px_cap 5.0, tier A, sigs (cyan, green), hold_weeks 78; entry limit capped at $5.00.
- Sizing (strategy card): $1,000 a position; K = min(20, ceil(20 x 390 / 126)) = 20 slots; fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data inputs

- Tracker ledger (1W fires with ue_tag tiers and close_D).
- Output: shadow/paper_sleeve/live/wait_fires_v1.json (key fires_wait) consumed by the Lazarus live engine.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/lazarus/the family research line_wait_feed.py` and `sleeves/lazarus/the family research line_wait.py` at those paths with the vendored research modules the feed imports available on the research root.
3. Run the producer: python the family research line_wait_feed.py --research <root>/inputs/lazarus --scratch <root>/cache/the family research line/scratch [--cache dir] [--now epoch]; it writes shadow/paper_sleeve/live/wait_fires_v1.json.
4. Run the desk cycle so the Lazarus live engine consumes the fires_wait file and applies the entry/exit execution mechanics above, with the entry limit capped at $5.00.
5. First evaluation: fixture one 1W Cyan tier-A fire at close $4.50; confirm exactly one s_wait_q14 fire with limit_cap 5.00 and a 78-week no-stop plan.

## Verification

- Fixture above: exactly one fire, plan max_bars 78 weeks, stop_pct 99.0, rest time, limit_cap 5.00.
- Fixture with tier B, or signal neither cyan nor green, or lane not 1w, or close $5.01: no fire. Close exactly $5.00 fires.
- A held position reaches the close of the 78th weekly bar: one full time exit; no price stop fires before it.
