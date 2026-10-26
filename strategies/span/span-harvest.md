# SPAN Harvest

Buys an in-play Polymarket underdog on a deep dip below its opening price with a three-rung ladder, then harvests, trails or settles three inventory slices.

| | |
|---|---|
| **Family** | SPAN |
| **Source** | SPAN HARVEST UNIFIED 1.2.0 (PZOE + APZI), from the Galath / GrokBot desk; priors from TimePortal's public tapes |
| **Asset** | Prediction markets |
| **Timeframe** | Trade prints (60 s passes) |
| **Universe** | Polymarket MLB, NPB, UFC and boxing moneylines |
| **Style** | In-play mean reversion |
| **Status** | waiting |

## Entry

- Matches: Polymarket two-way moneylines, found up to 24 h before the start; tennis is off.
- Side: the underdog, the lower Gamma price at a pregame read ≤ 2 h before the start, else the lower first post-start print; no side 30 minutes in skips the match.
- Profile (PZOE), chosen once at the first print: from older matches only, the first group with ≥ 30 priors (sport + cohort + opening bucket, sport + cohort, cohort + bucket, sport, cohort, all; buckets < 20c, 20-40c, 40-60c, ≥ 60c); each of 14 frozen profiles is replayed on it.
- A profile qualifies with ≥ 5 resolved fills, ≥ 85% coverage and positive 95% lower bounds (Bonferroni over the 14, and clustered by sport-day), with and without its best trade; the highest Bonferroni bound wins; none qualifying is no trade.
- Rung 1 (APZI): the first print in 15-85c at or under 55% of the opening price until 25% of the sport's game clock, 38% after; filled at the limit if price had been above it, else at the print.
- Rungs 2-3: price in band and under the limit, ≥ 1.5c above the prior 8-minute low, 6-minute slope ≥ 0; no entries after 80% of the clock or after any exit.
- Shock profiles enter only after a 4-minute normalized drop ≤ -2.5 has turned back up.
- Entries rest as limits at the replay's fill price for 10 minutes.

## Exit

- Inventory: A 34%, B 33%, C 33% of the shares bought.
- A: sold at ceil(max(2.15 × average fill, average + 18c)).
- B: sold at ≥ max(72c, average + 0.5c), or after giving back 38% of the run-up with the 6-minute slope ≤ 0.002.
- C: rides; moves to B when the winner-state score (price, slope, recovery) ≤ 0.28.
- Salvage at ≤ 8c while falling; flatten 240 minutes after the start (180 for the fast-flatten profile).
- What is left settles on the resolution (read every 10 minutes from 1 h after the start): $1 won, the tape cut at the first 3 prints ≥ 99.9c; 0.1c lost. An unknown end stays unresolved; tracking stops after 3 days.
- Exits sell at the live bid: a limit at 0.1c, 1-hour window.

## Sizing

- 1% of the $100,000 book per match ($1,000, the source's $1 unit), split 45% / 35% / 20% over the rungs; whole shares; no fees.

## Data

- Polymarket Gamma events (every 10 minutes), the tracked token's trade prints, CLOB quotes and resolutions; priors from TimePortal's tape release (refreshed weekly) plus the sleeve's last 2,000 completed tapes; per-sport game clocks.

## Code

- **Master desk**: `sleeves/span/prediction_markets.py`, `sleeves/span/vendor/span_harvest/span_harvest_unified.py`, `sleeves/span/feedlib/polymarket.py`
- **Rule lines**: [docs/verify/span.md](../../docs/verify/span.md)

## Notes

- 14 profiles: base 55% / 38%, deeper, more patient and wider zones, a deeper late zone, tighter and wider harvests, tighter and looser trails, and five shock-gated ones.
- Live matches carry the cohort label "cohort unavailable", so only priors with that label share their cohort groups.
