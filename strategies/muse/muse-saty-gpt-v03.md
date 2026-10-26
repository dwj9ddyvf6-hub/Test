# Saty opportunity engine v0.3 (SPY shares)

Trades SPY shares long or short on the best-ranked of ten independent Saty-vocabulary setups from 10-minute bars, with structural stops, scale-outs and a 1-ATR runner trail.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Sol (ChatGPT), Saty Adaptive Opportunity Engine v0.3.0, from Saty Mahajan's public vocabulary |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 10m · 1h |
| **Universe** | SPY (QQQ and IWM as context) |
| **Style** | Intraday trend and reversal |
| **Status** | waiting |

## Entry

- Ten setups on completed 10-minute SPY bars, named from Saty's vocabulary: three Vomy ribbon transitions (EMA 13, 48 and 21 rejections), Golden Gate, compression breakout and retest, pivot-ribbon pullback, ATR-level retest, and two countertrend reversals (pivot divergence; the Phase Oscillator leaving ±61.8). Each family runs independently.
- Golden Gate: in an EMA 8 > 21 > 48 stack, a close through ±38.2% of the day's ATR ladder, then a pullback to the gate or EMA 21 that holds EMA 48, then a close beyond that bar's extreme and EMA 8; targets 50% and 61.8%.
- Every signal: a stop 0.1 ATR beyond its structure; the close within 0.4 ATR of the setup's anchor; net reward to the nearest level ahead ≥ 1.5 × net risk after a 2-cent round trip; good for 6 bars.
- Ranking: net reward/risk to the first obstacle, then fit with the SPY / QQQ / IWM path regime (directional for trend setups, choppy for reversals), then chase room left, then age; only the top candidate's direction survives, an exact opposite tie waits.
- At the quote (≤ 5 s old): the stop still valid, every target still ahead, chase ≤ 0.4 ATR, adverse gap ≤ 0.15 ATR, net R to the nearest target still ≥ 1.5; a limit at the ask (long) or bid (short).
- Entries from the open to 30 minutes before the close, one position at a time, after 1,000 completed 10-minute and 1-hour bars.

## Exit

- Stop: a completed 10-minute close beyond the stop sells everything.
- Targets in order: the first sells half the shares, each later one a quarter (a 1-share lot closes whole).
- After the first scale-out the stop moves to the entry and trails 1 ATR behind the best price since entry; stops never loosen.
- Exits are limits at the bid (long) or ask (short).

## Sizing

- Risk R = 0.25% of the session-start slice ($25 on $10,000) a trade, half for a countertrend setup; shares = floor(risk / per-share risk), at most 100% of the slice in notional; none after a 2R loss or 3 entries in the session.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY, QQQ and IWM 5-minute regular-session bars (about 34,000, built into 10-minute and 1-hour bars), SPY daily bars (200), IEX quotes ≤ 5 s old, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/saty_gpt_v03.py`, `desk/sleeves/muse/core/saty_gpt_v03/`. The strategy file is Midna v3's `sleeves/saty_gpt_v03.py`
- **Midna v3**: `sleeves/saty_gpt_v03.py`, `integration/saty_gpt_v03_adapter.py`

## Notes

- No end-of-day flat: a position carries overnight until its stop or a target.
