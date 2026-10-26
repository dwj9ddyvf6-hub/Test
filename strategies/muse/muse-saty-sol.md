# Sol's Saty engine (SPY options)

Buys SPY calls or puts on the first cross of the ±38.2% ATR level, or calls on a 3-minute close above the 23.6% trigger after an open inside the box, and sells everything at the target or on invalidation.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Sol (ChatGPT), autonomous engine design v1.0 of the Saty / Milkman Trades day system |
| **Asset** | SPY options |
| **Timeframe** | 1m · 3m · 10m |
| **Universe** | SPY |
| **Style** | Intraday ATR levels |
| **Status** | 2 waiting |

## Entry

- Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); x = the price's distance from the anchor in units, signed with the trade.
- Golden Gate (both sides): armed when the session opens with x < 0.382; the first cross of 0.382 by a 1-minute close or the live quote mid is the one chance; entered only with x still within 0.382-0.412 and the 0.618 target not yet printed.
- Trigger (calls only): on a session opening inside ±0.236, the first completed 3-minute close above +0.236; entered while price stays above the trigger, below +0.382 and within 0.03 ATR of that close.
- Each event is acted on only by the first pass that sees it (within 2 minutes), then spent; entries 09:35-14:30 and at least 90 minutes before the close; one position or working entry at a time, Golden Gate first.
- Contract: the nearest expiry 2-4 calendar days out (today's in the 0DTE row), strike nearest the spot; its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old; a limit at the ask.

## Exit

- Golden Gate: all out at the first mark at x ≥ 0.618, or on a 10-minute close at x < 0.236 after the fill, whichever comes first (a tie is invalidation).
- Trigger: all out at the first mark at or above +0.382, or on a 3-minute close below +0.236 after the fill.
- Exits are limits at the bid; liquidation from 10 minutes before the close (market with no quote); a position from an earlier session is sold at once.

## Sizing

- Session premium budget: 0.5% of the $10,000 slice less premium already spent today; floor(budget / (100 × ask)) contracts, which can be 0 (no trade).
- A 1% daily loss (fills plus the open position at the bid) halts new entries for the session.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY 5-minute bars (about 22,000) and 1-minute bars (1,200), IEX quotes, the SPY option chain and quotes, the sleeve's own fills.

## Variants

| Variant | Rows | Expiry |
|---|---|---|
| Sol's original | `muse_saty_sol`; Midna v3 `saty_sol` | nearest expiry 2-4 calendar days out |
| 0DTE | `muse_saty_sol_0dte`; Midna v3 `saty_sol_0dte` | today's expiry only |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/saty_sol.py`, `desk/sleeves/muse/sleeves/saty_sol_0dte.py`. The strategy file is Midna v3's `sleeves/saty_sol.py`
- **Midna v3**: `sleeves/saty_sol.py`, `integration/saty_sol_adapter.py`
- **Midna v3 (0DTE)**: `sleeves/saty_sol_0dte.py`, `integration/saty_sol_0dte_adapter.py`

## Notes

- On the $10,000 slice the session budget is $50: only a contract at or under $0.50 can be bought.
- The 1-hour Phase Oscillator tag is recorded on every Golden Gate event, never a gate; Sol's Bilbo, ribbon, NQ-confirm, range-reject, trend-runner and put-trigger experiments stay off.
