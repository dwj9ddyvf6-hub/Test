# Psychology Engine: integration principles

Research date: 2026-10-30. Original design synthesis; not a validated trading strategy.

## Decision-centered state

Do not ask a single score to represent all investors. Track population, instrument, horizon and information clock. A consumer may fear unemployment while a leveraged investor increases equity exposure. A bullish analyst may already hold the maximum permitted position; a bearish hedger may buy because a liability requires it. Expressed sentiment, beliefs, risk appetite, attention and capacity to act must be separate.

Model the path as evidence → inferred state → possible demand change → price response conditional on liquidity → usable decision. Each arrow needs independent evidence. Avoid assuming that a correct text classification establishes return predictability.

The useful unit is an episode. Preserve a pre-event expectation snapshot, event surprise, initial interpretation, subsequent diffusion and market response. Distinguish a source changing its mind from a changing mix of sources. A single prolific poster or syndicated story should not become hundreds of independent observations.

## Two forecast targets, then a decision test

1. Forecast an observable next-period psychological proxy: next survey balance, next-window source-level stance distribution, attention share or uncertainty language. Compare with persistence and seasonal baselines.
2. Separately forecast market consequences conditional on prices, liquidity and event information. Compare a price-aware model with the same model plus psychological variables.
3. Only then test whether the change improves decisions after costs and the existing timing rules. A better belief forecast can have no trade value if already priced or too late.

Point estimates should not masquerade as measured confidence. Coverage quality is not forecast probability. Unknown positioning must remain unknown even if language is strongly optimistic. Prospective evidence collection is needed before claiming a live edge.

## Practical decision card

- As-of timestamp, entity, market session and horizon.
- What people say: stance, emotion, certainty and supporting topics by source population.
- What they do: positioning and flows, with publication lag and proxy caveats.
- What price does: response to favorable/unfavorable information, relative strength and liquidity.
- What changed: within-source change versus source-composition change, new information versus repeated story.
- Competing explanations and the next observation that separates them.
- Advisory output: supporting context, conflicting context, crowding/fragility warning, or insufficient evidence. This layer cannot authorize an entry or override Tensor.

## Read-specific research observations

Adams, Ajello, Silva and Vazquez-Grande (2023), Federal Reserve FEDS 2023-034, methodology and return-regression sections read (PDF pages 1–16). The paper uses an enterprise Twitter sample, near-replica filtering and financial-domain sentiment; platform character-limit changes affect collection. It distinguishes overnight text from contemporaneous text. Reported next-day associations are not a reproduced executable strategy here. Published regression controls and data availability must be reconciled before translating the finding into a point-in-time backtest. Source: https://www.federalreserve.gov/econres/feds/files/2023034pap.pdf

FRBSF Daily News Sentiment Index methodology page read, updated October 26, 2026. Daily observations are released through weekly updates; a current download is not proof historical values were available daily. Source: https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/

Baker and Wurgler's primary NBER abstract describes differential sentiment sensitivity among hard-to-value/hard-to-arbitrage equities. Treat this as motivation for cross-sectional stratification, not a rule to fade all high sentiment. Abstract read; direct PDF request returned403 and was not bypassed. Source: https://www.nber.org/papers/w13189

The Social Signal (2024) primary publisher abstract differentiates cross-platform sentiment and attention. Full article opening returned403. Use as an identified research lead, not a full-paper audit. Source: https://doi.org/10.1016/j.jfineco.2024.103870
