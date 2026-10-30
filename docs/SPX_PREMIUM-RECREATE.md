# spx_premium: Recreation package

Provenance: The shared XSP put-credit-spread card in this repo (strategies/ausar/opt-xsp-pcs.md) is NOT this sleeve's spec; this sleeve's provenance is the desk module header: extracted from the old desk's spx_premium.py, the author's spec followed exactly there and here (desk sleeves/spx_premium.py header, ports/spx_premium.md on the desk).

## What this sleeve is
This sleeve sells one XSP weekly put credit spread at an ATR level: on the week's first trading day at about 10:00 ET it shorts the put struck at the prior weekly close minus one prior-week ATR(14), buys a wing 5 points below, and holds to settlement with no stop or defense. Sources: desk sleeves/spx_premium.py (WING_WIDTH=5, ATR_PERIOD=14, SPX_EQUIV=1.0, LOT_QTY=1, EQUITY_GATE=37000.0, ENTRY_HOUR_ET=10, FULL_WIDTH_LOSS_USD=-450.0, COOLDOWN_WEEKS=4, UNDERLYING=XSP, LEVEL_PROXY=SPY, SETTLEMENT_CLOSE_HM=(15,15), CREDIT_FLOOR_FRAC=1/3) and desk3/enhance26.py (spx_premium entry_window_gate). Note the existing repo doc strategies/ausar/opt-xsp-pcs.md describes a different (Aster XSP) rule and must not be used for this sleeve, per the audit record.

## Full algorithm
Evaluation order in desk sleeves/spx_premium.py SpxPremium.signal(bars, slice_state, context); the bars argument is unused (levels are weekly).
1. Settlement exit first and only: if a position is held and its expiry equals the session date and the ET clock is at or after the settlement arm time (SETTLEMENT_CLOSE_HM 15:15, adjusted by settlement_arm_hm for the session), emit one exit Intent for the held quantity (default LOT_QTY=1), reason naming spx_premium settlement_close with the short and long OCCs, expiry and credit. The sleeve has no other exit: no stop, no defense. A held position returns after this check in all cases.
2. Entry day rule (entry_day_ok): today must be in traded_dates and be the week's first trading day (Monday, or Tuesday when Monday was not a traded date; any other weekday fails) and the ET clock must be at or after 10:00. Adapter-layer gate (desk3/enhance26.py, default ON; switch extra[spx_premium_enhance2][entry_window_gate]): entries at or after 11:00 ET are also refused, so the effective entry window is 10:00-10:59 ET.
3. Once per week and cooldown: if state last_entry_week equals this ISO week, no entry. If state cooldown_until is set and this ISO week is at or before it, no entry (the Monty Carlo policy: a settlement losing at least 90 percent of the 5-wide, i.e. settle_pnl at or below -$450, arms a cooldown_until week 4 weeks out, recorded by the core Ledger helpers settle_pnl / is_full_width_loss / cooldown_until_week ported in the module).
4. Equity honesty gate: context.account_equity (the broker account total, NOT the $10,000 slice; extra[account_equity] is the fixture fallback, absent read-back means 0.0) must be at least $37,000, else no entry. The sleeve never sizes off equity: 1 lot always.
5. Level: prior_week_level over the completed SPY weekly bars (at least 14): prior_close = the last weekly close; atr14 = the Wilder ATR(14) of the weekly bars (SMA-seeded at index 13). Short strike = round1(prior_close - 1.0 x atr14) (round to the nearest 1, XSP scale; round5 is kept for SPX-scale parity); long strike = short - 5.
6. Expiry and chain: expiry is the LAST expiry within this week's Monday-Friday window that carries both strikes in the XSP put chain (extra[chains][XSP]); if either strike is missing at that expiry, no entry.
7. Credit: natural credit = short leg bid - long leg ask (extra[quotes] by OCC). The author's rule skips unless credit > 0. ENH credit floor (ENH-SPX-PREMIUM-20261024, default ON; OFF via extra[spx_premium_enhance][credit_floor]=False restores the credit > 0 rule exactly): refuse when credit < width/3 (CREDIT_FLOOR_FRAC x 5 = 1.6667; equality is taken).
8. Entry intent: one enter Intent on XSP, qty_hint=1, price_hint = round(prior_close, 2), reason naming spx_premium put_credit_spread with both OCCs and strikes, expiry, credit, prior_close, atr14, wing_width=5 and the Decision #85/#96 gate exemption (net-credit premium sales are exempt from the Decision #75 gates).

## Files in this repo
- Sleeve module: sleeves/spx_premium.py (strategy logic and CONFIG).
- v3 adapter: adapters3/spx_premium.py (SLEEVE_ID=spx_premium; evaluate(view, ctx) rebuilds the v2 SleeveContext via adapters3/_snapshot_ctx.SnapshotSleeveContext, delegates to adapters/spx_premium.py, then applies desk3/enhance26.filter_entries; the _snapshot_ctx glue itself is not in this repo at its canonical path, as the audit record notes).
- v2 adapter mirror: integration/spx_premium_adapter.py in this repo (the adapters/spx_premium.py evaluate it mirrors).
- Shared engine file: engines/desk3/enhance26.py (desk desk3/enhance26.py: ENH-B26-20261024 adapter-layer gates, default ON per sleeve).
- Existing strategy doc: strategies/ausar/opt-xsp-pcs.md (a different sleeve's card; see the Provenance line).
- Config: engines/config/sleeves.json (row id=spx_premium), also at config/sleeves.json.

## Configuration
Module adapters3.spx_premium; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, options]; parked false. Universe: XSP weekly puts (levels from SPY weekly bars); timeframe weekly for levels, intraday clock for the entry and settlement arms. Source: muse-desk-v3/config/sleeves.json row id=spx_premium.

## Data inputs
Inputs are bars and options. Via context.extra the sleeve consumes: weekly_bars (completed SPY weekly bars {t,o,h,l,c,v}, at least 14), traded_dates (sessions with SPY 1H bars), chains {XSP: [{symbol, strike, expiration}]} (puts), quotes {OCC: {bid, ask}}, sleeve_state {XSP: {position, cooldown_until, last_entry_week}}, and the account equity read-back (context.account_equity). The entry clock is context.now in ET. Missing weekly bars, chain legs or quotes fail closed (no entry).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `spx_premium` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/spx_premium.py, whose evaluate(view, ctx) delegates to adapters/spx_premium.py, which runs sleeves/spx_premium.py signal(bars, slice_state, context), after which desk3/enhance26.filter_entries is applied.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on the week's first trading day at 10:30 ET with account equity $37,000 or more, 14+ completed SPY weekly bars, both strikes present at the week's last expiry, and a natural credit of 1.67 or more: exactly one enter intent, qty 1, short strike round1(prior close - ATR14), long strike 5 below.
- The same fixture at 11:00 ET or later, or with credit 1.00 (above 0 but below the 5/3 floor): no entry under the default gates; with the credit floor switched OFF and credit 1.00: an entry.
- Fixture with a held spread whose expiry is today and the clock at or after 15:15 ET: exactly one settlement_close exit; before 15:15: no exit, and no entry either.
- Fixture in a cooldown week (this ISO week at or before cooldown_until): no entry.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
