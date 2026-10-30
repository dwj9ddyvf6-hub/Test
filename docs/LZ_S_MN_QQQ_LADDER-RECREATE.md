# lz_s_mn_qqq_ladder: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna QQQ Ladder (Midna port)", type "other", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_none", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: ladder mark-to-market (shadow)", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 0, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Code in Test: `sleeves/midna/ladder.py`, whose header names its source as the QQQ ladder module of the Midna source desk (src/lib/equity/qqq-ladder.ts) ported line for line, on the listed QQQ chain of the option-marks producer. The accounting recorded only the shadow mark-to-market plan line above; the ladder rules below are the code's own header, verbatim in substance.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

The Midna QQQ ladder: a cash-secured short-put ladder on QQQ. It sells one new band put layer a week, three contracts a layer, on its own $1,000,000 book, and manages each layer by challenge state: buy-backs on severe challenge or short datedness, rolls up or down inside the 8 to 21 DTE window. The accounting entry for this id is the shadow mark-to-market record of that book (policy midna_none, no stop, no time bars).

## Full algorithm

From the header of `sleeves/midna/ladder.py` (constants in the same file), in evaluation order. Session: regular hours from 10:00 ET. Sales are booked at the bid, buy-backs at the ask, per contract x 100.

1. Severe challenge (checked first): spot (QQQ last, else the chain's) at or below the strike, or ask at least 3 x the sale credit (SEVERE_MULT = 3), or live put delta at least 0.35 (SEVERE_DELTA): the put is bought back; this needs today's fresh chain and the cash for it.
2. Short datedness: anything with 7 days or fewer left (CLOSE_DTE = 7) is bought back.
3. Roll up: 8 to 21 DTE (MANAGE_DTE = 21), not rolled before, not challenged: QQQ above the sale's spot (quote and chain within 2%), the put's ask at most half its credit (DECAYED = 0.5): buy it back and sell the band put above it in the same expiration (band = delta 0.05 to 0.08, nearest 0.065, lower strike on a tie) whose bid is at least that ask, when the cash still secures it.
4. Roll down: 8 to 21 DTE, challenged (ask at least 2 x credit, CHALLENGED_MULT = 2; delta at least 0.20, CHALLENGED_DELTA; or QQQ at or below strike) but not severe: buy back and sell the band put below the strike in the later expiration nearest 45 days (38 to 52) whose bid is at least half the old credit, when the cash still secures it.
5. New layer, once per ISO week: QQQ not down on the day and VIX not up on the day (both quoted with a previous close); no open put challenged; today's fresh chain (at most 20 minutes old, MARKS_FRESH_MS) whose spot is within 2% of QQQ's quote (MAX_SPOT_GAP = 0.02); the expiration nearest 45 days (38 to 52, a tie takes the later) not already held; sell the band put (delta 0.05 to 0.08, nearest 0.065, TARGET_DELTA); the cash after the credit, less the strikes already secured, must secure 3 x strike x 100. Quantity: 3 contracts a layer (LADDER_QTY = 3).
6. Expiry: a put still open on its expiration day settles at intrinsic x 100 in the source; the port's header records the engine divergence that a held option settles by the engine's delivery rule instead.
7. Orders (port divergence, recorded in the header): sales are DAY limits at the bid, buy-backs DAY limits at the ask; a working order counts as done. The source's 4% annual cash yield accrual (LADDER_YIELD = 0.04) is not paid by the engine, as the header records.

## Files in this repo

- This doc: `docs/LZ_S_MN_QQQ_LADDER-RECREATE.md`
- Code (already in Test): `sleeves/midna/ladder.py` (the ladder book; helpers calendar_days / occ_symbol / bs_price in the same file, ported from the options-surface module named in its header)
- Producer named in the code: the option-marks feed (listed QQQ chain, Cboe delayed quotes) as `desk/feedlib/midna_options.py` in the source layout; in Test the feedlib lives under `packages/claude/master-desk-feedlib/desk/feedlib/midna_options.py`
- Accounting: `docs/ALL-SLEEVES.json` entry for this id (shadow mark-to-market plan)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: QQQ listed puts only. Book: $1,000,000 of its own. Contracts per layer: 3.
- Target expiration: nearest 45 days, window 38 to 52. Band: put delta 0.05 to 0.08, target 0.065.
- Manage window: 8 to 21 DTE; forced buy-back at 7 DTE or fewer. Challenged at ask >= 2 x credit or delta >= 0.20; severe at ask >= 3 x credit or delta >= 0.35 or spot <= strike.
- Chain freshness: at most 20 minutes; spot gap at most 2%. Minimum bid 0.05 (MIN_BID); maximum relative spread 1 (MAX_REL_SPREAD).
- State: per-layer expiration, strike, entry spot, credit, rolledUp flag, entry day (the KEEP tuple in the code).

## Data inputs

The listed QQQ options chain from the option-marks producer (Cboe delayed quotes, at most 20 minutes old in session); QQQ and VIX quotes with previous closes for the new-layer gates.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_qqq_ladder` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/midna/ladder.py`; confirm LADDER_NAV = 1,000,000, LADDER_QTY = 3, TARGET_DELTA = 0.065, the 38 to 52 DTE window and the challenged / severe multipliers 2 and 3. Serve the fresh QQQ chain plus QQQ and VIX quotes in regular hours from 10:00 ET and run the book's step per pass; at most one new layer is sold per ISO week.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- No new layer is sold in a week that already has one, on a QQQ-down day, on a VIX-up day, or while any open put is challenged.
- A put with spot at or below strike, ask at least 3 x credit, or delta at least 0.35 is bought back before any roll is considered.
- Every open put with 7 or fewer days left is bought back.
- A roll-up candidate must be 8 to 21 DTE, unrolled and unchallenged, with ask at most half its credit; otherwise no roll up.
- A new layer is sold only when the post-credit cash, net of strikes already secured, still secures 3 x strike x 100.
