# Leader-1d event

Buys a stock after a daily leader event (3 of 5 momentum tests plus a UT Bot cyan or green gate) and holds about 20 sessions; variants differ by universe, regime filter, bar size and side.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Leader-1d research, via Femto-lean; its killed study, forward-tested |
| **Asset** | US equities |
| **Timeframe** | 1d (one variant 1h) |
| **Universe** | 1,838-name genome · small-cap band · 41-name basket |
| **Style** | Momentum event |
| **Status** | 2 live · 3 waiting |

## Entry

- Event on a closed daily bar: score ≥ 3 of 5 (close ≥ 8% over EMA(21); RSI(12) ≥ 60; volume ≥ 1.2× its 20-day mean; 20-day path efficiency ≥ 0.30; ≥ 4 of 7 trend votes) and a gate: a UT Bot buy flip (cyan) or an EMA 8/21 cross after a recent flip (green), each with the votes lined up.
- Daily: the last close's event ranks after 16:40 ET (≥ 252 bars, once per event) and buys from 10:40 ET the next session; the Femto daily variant only while SPY's 60-session return ≤ 0.
- Small caps: the bottom tenth of the genome by trailing 52-week mean weekly dollar volume (at least 9 names); no regime filter.
- Hourly (basket): the first regular-hours hourly bar after the event date, at least 20 hourly bars after the last entry.

## Exit

- Daily: sold once 19 bars have closed after entry (the 20th session); backstop 32 days; a 25% disaster stop.
- Hourly: sold 20 hourly bars after the entry bar; backstop 4 days; 25% stop.
- Killed study: in at the next open, out at the close of the 20th session; one hold per name.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Modeled cost a side: 5 bps (daily), 150 bps (small caps), 10 bps (hourly).
- Killed study: $100,000 / 300 a name long (genome), / 41 short (basket).
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The genome job's daily leader-event rows; split-adjusted daily bars (600); hourly bars for the hourly variant.

## Variants

| Variant | Rows | Universe | Filter | Hold | Side |
|---|---|---|---|---|---|
| Daily | `femto_leader_d`; Midna v3 `leader_d` | genome | SPY 60-session return ≤ 0 | 20 sessions | long |
| Small caps | `femto_leader_sc`; Midna v3 `leader_sc` | bottom tenth by dollar volume | none | 20 sessions | long |
| Hourly | `femto_gate_1h`; Midna v3 `gate_1h` | 41-name basket | none | 20 hourly bars | long |
| Killed study | `killed_leader1d_long` | genome | none | open t+1 to close t+20 | long |
| Killed study | `killed_leader1d_short` | 41-name basket | none | open t+1 to close t+20 | short |

Rows: 5 on the master desk, 3 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/leader_d.py`, `desk/sleeves/femto/leader_sc.py`, `desk/sleeves/femto/gate_1h.py`, `desk/sleeves/femto/leader_core.py`, `desk/feedlib/leader.py`, `desk/vendor/old_desk_research/leader1d_long_fulluniverse_2026-10-02.py`
- **Master desk (killed study)**: `sleeves/killed/daily.py`
- **Midna v3**: `sleeves/leader_d.py`
- **Midna v3 (small caps)**: `sleeves/leader_sc.py`
- **Midna v3 (hourly)**: `sleeves/gate_1h.py`

## Notes

- The Tensor research [Leader genome](../tensor_research/tr-genome-leader.md) runs the same five tests on any Tensor buy bar, hourly, daily or weekly.
- The old desk killed the Leader-1d research; the master desk forward-tests it in its long and short form.
- Midna v3 adds Edge-IMPROVE changes (2026-10-24, on by default): a stale event (daily) or a stale first bar (hourly) is refused.
