# span-harvest: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "SPAN Harvest", type mean reversion, family span, style "In-play mean reversion", universe "Polymarket MLB, NPB, UFC and boxing moneylines", asset class prediction markets, timeframe "Trade prints (60 s passes)", creator recorded as SPAN HARVEST UNIFIED 1.2.0 (PZOE + APZI) from the GrokBot desk, priors from TimePortal's public tapes. Algorithm grade PARTIAL in the accounting, with gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card in this repo (see Files).
- Test catalog entry `span-harvest` (`docs/CATALOG.json`): status waiting (1), card `strategies/span/span-harvest.md`, master-desk row `span_harvest_unified`.
- Alias: `span_harvest_unified`.

## What this strategy is

Buys an in-play Polymarket underdog on a deep dip below its opening price with a three-rung ladder, then harvests, trails or settles three inventory slices (A 34%, B 33%, C 33%).

## Full algorithm

From `strategies/span/span-harvest.md` (the card) and the code in Files, in evaluation order:

1. Matches: Polymarket two-way moneylines, found up to 24 h before the start; tennis is off.
2. Side: the underdog, the lower Gamma price at a pregame read <= 2 h before the start, else the lower first post-start print; no side 30 minutes in skips the match.
3. Profile (PZOE), chosen once at the first print: from older matches only, the first group with >= 30 priors (sport + cohort + opening bucket, sport + cohort, cohort + bucket, sport, cohort, all; buckets < 20c, 20-40c, 40-60c, >= 60c); each of 14 frozen profiles is replayed on it.
4. Profile qualification: >= 5 resolved fills, >= 85% coverage and positive 95% lower bounds (Bonferroni over the 14, and clustered by sport-day), with and without its best trade; the highest Bonferroni bound wins; none qualifying is no trade. The 14 profiles: base 55% / 38%, deeper, more patient and wider zones, a deeper late zone, tighter and wider harvests, tighter and looser trails, and five shock-gated ones.
5. Rung 1 (APZI): the first print in 15-85c at or under 55% of the opening price until 25% of the sport's game clock, 38% after; filled at the limit if price had been above it, else at the print.
6. Rungs 2-3: price in band and under the limit, >= 1.5c above the prior 8-minute low, 6-minute slope >= 0; no entries after 80% of the clock or after any exit.
7. Shock profiles enter only after a 4-minute normalized drop <= -2.5 has turned back up.
8. Entries rest as limits at the replay's fill price for 10 minutes.
9. Exit A: sold at ceil(max(2.15 x average fill, average + 18c)). Exit B: sold at >= max(72c, average + 0.5c), or after giving back 38% of the run-up with the 6-minute slope <= 0.002. Exit C: rides; moves to B when the winner-state score (price, slope, recovery) <= 0.28.
10. Salvage at <= 8c while falling; flatten 240 minutes after the start (180 for the fast-flatten profile).
11. Settlement: what is left settles on the resolution (read every 10 minutes from 1 h after the start): $1 won, the tape cut at the first 3 prints >= 99.9c; 0.1c lost. An unknown end stays unresolved; tracking stops after 3 days.
12. Exits sell at the live bid: a limit at 0.1c, 1-hour window.
13. Note on the card: live matches carry the cohort label "cohort unavailable", so only priors with that label share their cohort groups.

## Files in this repo

- This doc: `docs/SPAN_HARVEST-RECREATE.md`
- Strategy card: `strategies/span/span-harvest.md`
- Code (already in Test, master-desk paths): `sleeves/span/prediction_markets.py`, `sleeves/span/vendor/span_harvest/span_harvest_unified.py`, `sleeves/span/feedlib/polymarket.py`; parity copy `packages/claude/master-desk-parity-tools/tools/parity/span_harvest.py`
- Rule lines: `docs/verify/span.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Searched for code outside Test: Silicon, quant-research-backup and Midna trees were searched; no distinct span_harvest original was found there. The code above in Test is the home used.

## Configuration

- Universe: Polymarket MLB, NPB, UFC and boxing moneylines. Timeframe: trade prints, 60 s passes.
- Book: $100,000. Sizing: 1% of the book per match ($1,000), split 45% / 35% / 20% over the rungs; whole shares; no fees.
- Inventory split: A 34%, B 33%, C 33%.

## Data inputs

- Polymarket Gamma events (every 10 minutes), the tracked token's trade prints, CLOB quotes and resolutions; priors from TimePortal's tape release (refreshed weekly) plus the sleeve's last 2,000 completed tapes; per-sport game clocks.

## Install and run

1. Clone the Test repo.
2. Read `strategies/span/span-harvest.md` and `docs/verify/span.md`.
3. Open `sleeves/span/vendor/span_harvest/span_harvest_unified.py` (the unified engine, version 1.2.0) with `sleeves/span/prediction_markets.py` and `sleeves/span/feedlib/polymarket.py`.
4. Provide Polymarket Gamma, trade-print, CLOB and resolution feeds plus the priors tape described under Data inputs.
5. Run on 60-second passes during in-play matches and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- No trade when no profile qualifies under the >= 5 fills, >= 85% coverage and positive Bonferroni lower-bound rules.
- Rung 1 does not fire above 55% of opening before 25% of the clock, or above 38% after it.
- No rung 2 or 3 entry after 80% of the clock or after any exit.
- Inventory is split A 34% / B 33% / C 33%, and slice A exits at ceil(max(2.15 x average fill, average + 18c)).
- Remaining inventory flattens at 240 minutes after the start (180 for the fast-flatten profile).
