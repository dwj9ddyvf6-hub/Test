# lz_s_mn_kronos: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Kronos (Midna port)", type "forecast and ML models", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: Kronos topK rebalance / min hold 5", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 5, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test: `strategies/midna/mn-kronos-topk.md`; rule lines in `docs/verify/midna.md` (Kronos-base TopkDropout section). The card states the Kronos model code and weights keep their upstream license and are not copied into the repo; the desk-side books below are in Test.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A forecast book: every ten sessions the Kronos-base model ranks a frozen 24-name universe by its ten-session price forecast, and the book holds the top 4 under a TopkDropout replacement rule with a five-session minimum hold. The v3 lane (`s_mn_kronos`) is the fire-consumer form of the same book: it consumes forecast fires and owns the hold/drop management desk-side.

## Full algorithm

Two recorded forms, both in Test; do not merge them silently.

A. v3 fire-consumer (`sleeves/s_mn_kronos.py`), in evaluation order:
1. Read forecast fires for sleeve_id s_mn_kronos from context.extra fires. Keep only fires aged 0 to 7 days (MAX_FIRE_AGE_DAYS = 7); take the latest fire date only. No fresh forecast: return nothing (fail closed, no entries and no churn).
2. Rank that date's names by rank when every row carries one, else by score descending. The target set is the first 4 (TOP_N = 4).
3. Exits first: a held name outside the target set exits only when it has been held at least 5 sessions (MIN_HOLD = 5, the accounting record's max_bars 5 / min hold 5; stop_pct 99.0 records no price stop).
4. Entries: fill free slots (4 minus surviving held names) from the target set in rank order, skipping held names and names whose feed is cross-stale (the ENH20 gate in the code). Size: $500 per name (PER_NAME = 500.0; the file's catalog note records a $2,000 total budget and that the named top-4 rule wins over a conflicting 2-slot catalog cell). Cadence 300 seconds.

B. Master-desk book (card `strategies/midna/mn-kronos-topk.md`, code in the packages tree named in Files):
1. Score = forecast close in 10 sessions / last close - 1, rebuilt every 10 sessions. The quant-research reconstruction: from 2024-07-01, after every 10th session's close, the released Kronos-base model reads each name's last 90 sessions and samples 10 paths 10 sessions ahead (temperature 0.6, top-p 0.9, fixed seeds); the score uses their mean.
2. Eligibility: 252 complete prior sessions, 20-session average dollar volume at least $10M, close at least $5. Universe: the 24 most liquid eligible names on 2024-06-28.
3. TopkDropout: drop the worst held name held at least 5 sessions and out of today's top 5, then fill back to 4. Exit: sold when dropped from the targets.
4. Sizing (Midna book): slice = 95% of equity / 4 on its own $100,000 book; whole shares at last plus or minus 0.1%. (The card also records a separate $1,000,000 quant-research book with 1%-of-ADV caps and fractional shares; that is a different book, not this id's v3 lane.)

## Files in this repo

- This doc: `docs/LZ_S_MN_KRONOS-RECREATE.md`
- Code (already in Test): `sleeves/s_mn_kronos.py` (v3 fire-consumer; imports `sleeves/laz8_common.py`, present in Test at `engines/sleeves/laz8_common.py`)
- Code (already in Test, master-desk port library): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/midna/kronos.py`, `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/kronos.py`, `packages/claude/master-desk-sleeve-port-library/desk/sleeves/quant_research/kronos_runner.py`
- Strategy card: `strategies/midna/mn-kronos-topk.md`
- Rule lines: `docs/verify/midna.md` (Kronos-base TopkDropout section)
- NOT in Test: the Kronos-base model weights themselves (the card records they are not copied into the repo); a recreation must supply the released Kronos-base weights from upstream.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: 24 frozen names (the 24 most liquid eligible names on 2024-06-28, per the card). Timeframe: 1d, 10-session cycle.
- v3 lane: TOP_N 4, $500 per name, minimum hold 5 sessions, maximum fire age 7 days, cadence 300 s, state = the held position set with entry dates.
- Master book: $100,000, slice 95% of equity / 4, whole shares.
- Accounting entry policy for this id: midna_block, max delay 65 minutes, limit band 5.0%, limit buffer 1.0%, capped_limit_day orders.

## Data inputs

Split-adjusted daily bars of the 24 names; Kronos-base forecasts on daily bars (v3: forecast fires in context.extra; master book: the pinned Kronos-base weights run by a separate interpreter with torch, per the card).

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_kronos` in `docs/ALL-SLEEVES.json`.
3. For the v3 lane, open `sleeves/s_mn_kronos.py`; confirm TOP_N = 4, PER_NAME = 500.0, MIN_HOLD = 5 and MAX_FIRE_AGE_DAYS = 7, serve daily bars plus forecast fires carrying sleeve_id, symbol, date and rank or score, and call `signal` per pass. For the master book, follow the card and the packages-tree kronos modules, supplying the upstream Kronos-base weights (not in this repo).
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- With no forecast fire aged 0 to 7 days, the v3 lane emits nothing at all.
- Only the latest fire date is used; the target set has at most 4 names.
- A held name outside the target set is sold only after at least 5 sessions held.
- Entries never exceed $500 of notional per name in the v3 lane and never take the book past 4 names.
- In the master book, a name with under 252 prior sessions, under $10M 20-session dollar volume, or a close under $5 is never scored.
