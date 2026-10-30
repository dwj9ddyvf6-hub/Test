# bb_rsi_divergence: Recreation package

Provenance: Provenance line in docs/BB_RSI_Divergence_Research.md in this repo: Midna's desk: a TradingView indicator reconstructed from a chart screenshot, and its desk sleeve. Code: sleeves/bb_rsi_divergence.py. The sleeve module header states it is ported from the Test package sleeve v2.2 (sleeves/bb_rsi_divergence.py) with the indicator math, pivot/divergence detection, adaptive context, gates and sizing frozen, plus an expansion dated 2026-10-24.

## What this sleeve is
This sleeve trades Bollinger-band-touch RSI divergence on completed 1-hour regular-hours bars: a bullish lower-band pivot divergence opens a long toward the Bollinger basis, and, with the expansion on, a bearish upper-band divergence opens a mirrored short. It runs through the v3 adapter, which rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/bb_rsi_divergence.py (the expanded copy in this repo is sleeves/bb_rsi_divergence_expanded.py). Exits are the pivot stop, the basis target, the opposite divergence and a 24-bar time exit.

## Full algorithm
Frozen constants (sleeves/bb_rsi_divergence.py): BB_LENGTH = 20, BB_MULTIPLIER = 2.0 (Bollinger basis = 20-bar SMA, bands at plus/minus 2.0 population standard deviations), RSI_LENGTH = 14 (Wilder), ATR_LENGTH = 14 (Wilder), PIVOT_LEFT = 3, PIVOT_RIGHT = 3, RSI_ALIGN_RADIUS = 1, MIN_PIVOT_GAP = 5, MAX_PIVOT_GAP = 60, MIN_RSI_DIVERGENCE = 2.0, MIN_PRICE_EXTENSION_PCT = 0.0, REQUIRE_CLOSE_BACK_INSIDE = False, STOP_ATR_BUFFER = 0.5, MIN_REWARD_RISK = 1.2, MAX_HOLD_BARS = 24, RISK_PCT = 0.0025, MAX_NOTIONAL_PCT = 0.05, MAX_SPREAD_BPS = 15.0, QUOTE_MAX_AGE_S = 60.0, BAR_MAX_AGE_S = 600.0, BAR_SECONDS = 3600.0, entry-close window ENTRY_CLOSE_START = 10:00 to ENTRY_CLOSE_END = 15:00 ET, MAX_CONCURRENT_POSITIONS = 3. CONFIG: cadence_s 300, risk_pct RISK_PCT, parked False.

Universe: UNIVERSE_12 = SPY, QQQ, IWM, DIA, GLD, SLV, TLT, IEF, USO, UUP, XLF, XLK. With the expansion on (extra["bb_rsi_divergence_expansion"]["enabled"], default ON; OFF restores v2.2 exactly, including the 12-symbol universe and long-only behaviour), UNIVERSE adds XLE, XLV, XLI, XLP, XLY, XLB, XLRE, XLC, AAPL, MSFT, NVDA, AMZN, GOOGL, META, AVGO, JPM, UNH, HD, COST, LLY, XOM, CVX, MA, V, BAC, AMD, TSLA, CRM (40 symbols total). An extra active_universe list, when supplied, overrides the requested universe; held symbols are always appended for exit management.

Per-symbol frame gates, in code order: bars are filtered to regular hours; fewer than BB_LENGTH + RSI_LENGTH + MAX_PIVOT_GAP + PIVOT_LEFT + PIVOT_RIGHT = 100 bars is blocked_warmup; an intraday gap is blocked_intraday_gap; the latest bar's close time must be within -1 to +600 seconds of now or the symbol is blocked_stale_bar; a bar already consumed (its start at or before the journal-persisted cursor in extra meta last_evaluated_bar_by_symbol) is not re-signalled.

Signal detection (_latest_confirmed_signals): pivots are confirmed only after PIVOT_RIGHT = 3 bars. A bullish setup pairs two price pivot lows 5 to 60 bars apart where the later low is lower, its low touches or pierces the lower Bollinger band, and the Wilder RSI(14) at the later pivot (aligned within radius 1) is higher than at the earlier pivot by at least MIN_RSI_DIVERGENCE = 2.0 points (regular bullish divergence). A bearish setup is the mirror at the upper band (higher price high, lower RSI high). The adaptive context layer (v2, in _adaptive_context) scales risk: the volatility scale is clip(1 / sqrt(max(1, ATR/close divided by its trailing 60-bar median)), 0.5, 1.0); a downtrend band-walk flag (signed 12-bar efficiency ratio at or below -0.55 with at least two of the last four closes at or below the lower band; mirrored for shorts) halves risk; the combined risk_scale has a 0.25 floor and can only reduce the base risk, never increase it. Candidates are ranked deterministically by risk scale, planned reward/risk, divergence size, normalised band penetration, spread and ticker.

Entries, in code order: entries require the latest bar's close time inside 10:00 to 15:00 ET, a fresh quote (age at most 60 seconds, spread at most 15 bps), no working opening order or partial fill for the symbol in the session order state, no entry activity already recorded today for the symbol beyond the code's limits, and fewer than 3 concurrent positions sleeve-wide. Long entry: a limit at the ask rounded to a cent (the code's _limit_cents rounding); stop = pivot low - 0.5 x ATR(14); target = the confirmation bar's Bollinger basis; the trade is refused unless planned reward/risk is at least 1.2. Short entry (expansion only): a limit at the bid rounded down to a cent; stop = pivot high + 0.5 x ATR; target = the Bollinger basis; the same 1.2 reward/risk gate, gates and risk_scale (direction -1 adaptive context) apply. Sizing: quantity from RISK_PCT = 0.0025 of equity times risk_scale divided by the per-share stop distance, capped at MAX_NOTIONAL_PCT = 0.05 of equity in notional.

Exits, evaluated before entries for held positions (session order state must be available or the evaluation blocks with blocked_exit_order_state_unavailable): a long exits when its stop or target is reached, when a bearish divergence confirms against it, or after MAX_HOLD_BARS = 24 bars; a short exits on its mirrored stop or target, when a bullish divergence confirms, or after 24 bars. Protective working orders (stop, stop_limit, trailing_stop types) and working close orders are respected by the code's order-state checks rather than duplicated.

Position management: at most 3 concurrent positions, one position per symbol, no pyramiding in this module beyond the entry rules above.

## Files in this repo
- Sleeve module (desk sleeves/bb_rsi_divergence.py): `sleeves/bb_rsi_divergence.py`; the expanded desk copy is present as `sleeves/bb_rsi_divergence_expanded.py`.
- v3 adapter (desk adapters3/bb_rsi_divergence.py): `adapters3/bb_rsi_divergence.py`; also present as `integration/bb_rsi_divergence_expanded_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py); the audit record also names `adapters/_bridge.py` as a shared dependency of the v2 adapter chain.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing research doc: `docs/BB_RSI_Divergence_Research.md`.

## Configuration
- Universe: the 40-symbol expanded universe above (12-symbol UNIVERSE_12 with the expansion off). Asset: US-listed ETFs and equities. Timeframe: 1h completed regular-hours bars; entry closes 10:00 to 15:00 ET.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.0025 in CONFIG (see the Full algorithm sizing rule, with the 5 percent notional cap).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions, quotes, session_fills.

## Data inputs
- bars: hourly bars per symbol (t, o, h, l, c, v), fresh rolling frames each evaluation (the research doc's wiring note: only provider-side caching that refreshes the latest closed interval is permitted); the desk integration specifies SIP hourly bars.
- quotes: warm-cache SIP quotes per symbol with bid, ask and timestamps; a quote older than 60 seconds or wider than 15 bps blocks entry.
- positions, session_fills and session order state: held quantities, today's fills and working orders, plus the journal-persisted bar cursor in extra meta last_evaluated_bar_by_symbol and the expansion switch in extra.

## Install and run
1. Place the sleeve module at sleeves/bb_rsi_divergence.py and the adapter at adapters3/bb_rsi_divergence.py (repo copies at the same paths). The module needs the desk BaseSleeve / SleeveConfig / Intent plumbing it imports in the fresh desk.
2. Register the roster row for `bb_rsi_divergence` exactly as in the Configuration section in config/sleeves.json (module adapters3.bb_rsi_divergence).
3. Wire the producers so every snapshot carries: fresh hourly bars for the universe, SIP quotes, this sleeve's positions, session fills and order state, and the persisted bar cursor.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot with fewer than 100 bars per symbol, a stale bar, or a consumed bar returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check warmup and freshness: 99 bars, an intraday gap, or a latest bar older than 600 seconds each block the symbol with the named state; a consumed bar is never re-signalled.
- Check the divergence definition on fixtures: pivot spacing outside 5 to 60, RSI divergence under 2.0 points, or no band touch at the later pivot each produce no setup; a qualifying bullish pair produces a long setup and, with the expansion on, a qualifying bearish pair produces a short setup.
- Check entry gates: a bar closing outside 10:00 to 15:00 ET, a quote older than 60 seconds or wider than 15 bps, planned reward/risk under 1.2, or 3 positions already open each produce no entry.
- Check sizing and prices: long quantity follows 0.25 percent of equity times risk_scale over the stop distance (stop = pivot low - 0.5 x ATR, target = basis), capped at 5 percent notional; the long limit is at the ask rounded to a cent and the short limit at the bid rounded down.
- Check exits and the expansion switch: stop, target, opposite divergence and the 24-bar time exit each close a position, and setting the expansion switch off restores the 12-symbol long-only v2.2 behaviour.
