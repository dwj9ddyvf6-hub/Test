# aster_saty_research: Recreation package

Provenance: Aster research program, hosted sleeves on the desk engine (provenance line in docs/ASTER_SATY_RESEARCH-ALGORITHM.md in this repo: derived from the sleeve code on 2026-10-29; no author spec on file).

## What this sleeve is
This is a TSV-as-spec meta-ranker shell on SPY only: the authored source for its 10 setup families is absent from the archive and is not invented in the code, so candidates arrive pre-formed via the saty_setups snapshot key and the shell owns only ranking, risk sizing, limits, deadlines and structural exits. No v3 producer emits saty_setups, so the sleeve is visibly UNFED and monitor-only in production. Sources: desk adapters3/aster_saty_research.py and desk3/aster_batch16.py.

## Full algorithm
This sleeve is a thin wrapper: adapters3/aster_saty_research.py evaluate(view, ctx) delegates to desk3/aster_batch16.py evaluate(), SPEC kind="saty", _eval_saty().

SPEC and constants (desk3/aster_batch16.py): kind="saty", inputs=("saty_setups", "quotes", "bars", "positions"), cadence_s=600, SLICE=10000.0. SATY_RISK_USD = 0.0025 times SLICE = 25.00 (1R, halved for mean-reversion families); SATY_COST_PER_SHARE=0.02; SATY_MAX_ENTRIES_DAY=3; SATY_DAILY_LOSS_R=2.0; SATY_OPEN_RISK_R=2.0; SATY_CORRELATED_R=1.0 (single-instrument book: all SPY); SATY_QUOTE_MAX_AGE_S=5.0; SATY_ENTRY_DEADLINE=15:40 ET; SATY_FINAL_EXIT=15:50 ET. Instrument: SPY only.

Evaluation order in _eval_saty():
1. Price: the SPY quote mid when a two-sided quote exists, else the last 10-minute bar close, else None.
2. Exits first; if any exit is emitted, return with no entry. Per held position, in order: structural invalidation (price at or below invalidation for a long, at or above for a short) closes the full position; else at or after 15:50 ET the final-exit deadline closes the full position; else target-1 scale (an unscaled position reaching targets[0] is half closed, exit_qty = abs(qty) // 2 or the full qty when that is 0); else a scaled position returning to its entry reference (avg_price) closes in full (trail to breakeven after scale). Exits are market, day intents, sell_to_close for a long and buy_to_close for a short.
3. Entry gates: no entry at or after 15:40 ET; no entry after 3 entries today (saty_state entries_today); no entry when realised R today is at or below -2.0; a fresh two-sided SPY quote is required (quote timestamp within 5.0 seconds of now and not in the future, else fail closed); price must exist.
4. Candidates: each saty_setups item must be a dict for SPY, SPY must not already be held, and net room must be positive both at the planned entry and at the current price, where net room = (distance to targets[0] minus 0.02 per share) divided by (distance to invalidation), direction-aware; non-positive refuses.
5. Ranking: net room at the current price descending, then context descending, then age_min ascending, then family name. If the top two candidates have opposite directions and equal top rank (within 1e-9), no entry is emitted.
6. Open-risk gate: open risk is summed over held positions as qty times |avg_price - invalidation|; a new entry is refused when open risk plus the new risk_usd would exceed min(2.0, 1.0) times 25.00, i.e. the 1R correlated cap.
7. Sizing: risk_usd is 25.00, halved to 12.50 when the family name marks mean reversion. Executable-risk sizing ENH-B26-SATYEXEC-20261024 (default ON): qty = int(risk_usd // |current price - invalidation|); with the switch OFF the planned entry price is used instead. Qty below 1 emits nothing. One entry per evaluation: a market, day intent on SPY, buy (buy_to_open) for a long candidate and sell (sell_to_open) for a short one, reason naming the family, direction, net room, risk, invalidation and targets.

## Files in this repo
- Adapter: adapters3/aster_saty_research.py (SLEEVE_ID=aster_saty_research; evaluate(view, ctx) delegates to desk3/aster_batch16.evaluate; INPUTS imported as SATY_INPUTS from that engine).
- Shared engine file: desk3/aster_batch16.py (SPECS entry for aster_saty_research, _eval_saty, _saty_net_room, _saty_price).
- Existing per-sleeve algorithm doc in this repo: docs/ASTER_SATY_RESEARCH-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=aster_saty_research), also at config/sleeves.json.

## Configuration
Module adapters3.aster_saty_research; cadence_s 600; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [saty_setups, quotes, bars, positions]; parked false. Universe: SPY only; timeframe intraday (quote-driven, 10-minute bar fallback for price). Source: muse-desk-v3/config/sleeves.json row id=aster_saty_research.

## Data inputs
Inputs are saty_setups, quotes, bars and positions. Producers named in desk3/aster_batch16.py PRODUCERS: saty_setup_families (outputs saty_setups, freshness_sla_s 60), quotes (freshness_sla_s 60), bars (freshness_sla_s 900) and broker_readback (outputs positions, freshness_sla_s 900). The batch-16 note states run_live registers only bars and broker_readback today, so saty_setups and quotes have no live producer yet and the sleeve is visibly UNFED rather than fake-fed. Candidates are pre-formed dicts with symbol SPY, direction, entry, invalidation, targets, context, age_min and family.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `aster_saty_research` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/aster_saty_research.py, whose evaluate(view, ctx) calls desk3/aster_batch16.evaluate(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- No per-sleeve test file for this sleeve exists in this repo (audit: no tests/test_aster_* in the Test tree); use this behaviour checklist instead.
- Fixture with no saty_setups, a stale SPY quote (older than 5 seconds), a time at or after 15:40 ET, 3 entries already today, or realised R at or below -2.0: no entry.
- Fixture with one qualifying SPY candidate, a fresh quote and positive net room at the current price: exactly one entry, qty int(25.00 // |price - invalidation|) (int(12.50 // ...) for a mean-reversion family), reason naming the family and net room.
- Fixture with a held long whose price is at or below its invalidation: exactly one full-qty exit, reason containing structural_invalidation; fixture at or after 15:50 ET with a held position: a full exit, reason containing final_exit_deadline.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
