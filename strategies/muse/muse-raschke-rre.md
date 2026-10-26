# Raschke RRE adaptive desk (SPY)

Scores Linda Raschke-style first-cross pullbacks and failed breaks of the prior day's range on SPY 5-minute bars; with no event calendar it vetoes every candidate and does not trade.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Astra's RRE Adaptive Desk v0.2.0, on Linda Raschke's methods |
| **Asset** | SPY shares |
| **Timeframe** | 5m |
| **Universe** | SPY |
| **Style** | Intraday trend and reversal |
| **Status** | waiting |

## Entry

- Today it trades nothing: the desk has no event calendar, so every bar's context is DATA_BLOCK and the router vetoes every candidate.
- First cross: the slow line (16-bar average of SMA 3 - SMA 10) changes sign; within 12 bars (65 minutes), after the first pullback of the fast line, the first bar resuming sets a trigger one tick beyond the last pullback bar; a close at the trigger enters; stop 0.1 ATR beyond the pullback's extreme; a second pullback or a wick through the stop cancels.
- Failed break: in rotation (slow line within 0.15 ATR of zero, fast slope flipping twice in 6 bars), a bar sweeps a tick through the prior session's low and closes back above it (mirror at the high); VWAP must lie ahead.
- Attempt: from 30 minutes after the open, the close within 0.2 ATR past the trigger, target = the nearer of 1.5R and the prior high / low / close (and VWAP), net R ≥ 1.2.
- Admission: one thesis at a time, a 15-minute cooldown after flat, a marketable limit from an IEX quote ≤ 5 s old; longs only (no borrow check on the desk); the baseline RRE1 lane is journaled, never traded.

## Exit

- Quote-triggered stop and target, a 30-minute hold limit from the first fill, flat 5 minutes before the close; exits are limits at the bid.

## Sizing

- Whole shares, the least of: slice ÷ per-share loss, slice ÷ max(loss, $2), slice ÷ price, and half the quoted size ($10,000 slice); the desk's quotes carry no size, which leaves 0.

## Data

- SPY 5-minute regular-session bars (5,000), IEX quotes, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/raschke_rre.py`, `desk/sleeves/muse/core/raschke_rre/`. The strategy file is Midna v3's `sleeves/raschke_rre.py`
- **Midna v3**: `sleeves/raschke_rre.py`, `integration/raschke_rre_adapter.py`
- **Rule lines**: [docs/verify/muse.md](../../docs/verify/muse.md)

## Notes

- Two blocks stand between it and a trade: the absent event calendar, then zero depth capacity at admission.
