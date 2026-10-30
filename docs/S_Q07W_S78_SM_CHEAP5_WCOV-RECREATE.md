# s_q07w_s78_sm_cheap5_wcov: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 fire-consumer sleeve in the swing family, small band, with a 78-week horizon and the filters cheap5, wcov. It is parked: the engine manages exits on held positions (15 percent stop or the 78-week horizon) and refuses new entries while parked. Sources: desk adapters3/s_q07w_s78_sm_cheap5_wcov.py and desk3/lazarus_q07.py SPECS.

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) delegates to desk3/lazarus_q07.py evaluate_sleeve(SLEEVE_ID, view, ctx), with SPEC = SPECS[SLEEVE_ID] from that engine. Wrapper note (desk adapters3/<id>.py): Lazarus Q07 batch 4. Q07 Swing H78 small cheap5+wiki_cov (CSV off => parked; exits managed). $1,194 slice.

SPEC (desk3/lazarus_q07.py SPECS): family="swing", band="small", horizon_w=78, filters=('cheap5', 'wcov'), slots=1, budget=1194.0, parked=True in the engine SPEC. Constants in the engine: STOP_FRAC=0.15, WINDOW_SESSIONS=5. Inputs: fires, bars, positions.

Evaluation order in desk3/lazarus_q07.py evaluate_sleeve():
1. Exits first (parked lanes still manage exits). For each held position with qty above 0 and entry (avg_price) above 0: last price is the last close from bars (or current_price fallback). If price is at or below entry times (1 - 0.15), sell the full quantity, reason "q07 exit: stop_15pct". Otherwise, if held calendar days (session date minus opened_at / entry_date) are at least horizon_w times 7 (546 days for 78 weeks), sell the full quantity, reason "q07 exit: horizon_78w". Exits are market, day, sell_to_close.
2. Parked gate: because this SPEC has parked=True, entries are then refused and only the exits above are returned. The entry rules below are the engine rules that apply when the lane is unparked; they are stated here so the recreation is complete.
3. Entries require an open slot (slots minus distinct held symbols above 0) and a QQQ-down day: extra["qqq_red"] if it is a bool, else market["qqq_red"] if it is a bool, else QQQ last close below its prior close (needs at least 2 QQQ closes). If QQQ is not down, return only any exits.
4. Fires are read from view["fires"]. A fire is skipped if it has no symbol, its sleeve_id / sleeve (when carried) differs from this sleeve, its family does not normalise to "swing" (swing accepts swing / w_swing / s; green accepts green / w_green / g; cyan accepts cyan / w_cyan / c), its band / cap_band does not normalise to "small" (small accepts sm / small; midlarge accepts ml / midlarge / mid_large / mid/large), or its symbol is already held.
5. Signal age: sessions since signal_date / fired_at / fire_date / date, counted on QQQ bar dates when available else calendar days times 5/7, must be present and at most WINDOW_SESSIONS=5.
6. Freshest-first (ENH-Q07FRESH-20261024, default ON; OFF restores producer list order): when 2 or more candidate fires pass the sleeve / family / band / held checks, allocate the slot freshest-signal-first.
7. Filters, all must pass and a filter with no evidence fails closed: cheap5: the evaluated price is below 5.00; wcov: a wiki_cov tag, when present, must be true; else wiki_views above 0; else a true wiki_coverage tag; else wiki_attention in (covered, high, spike); no wiki evidence fails closed.
8. Execution price (ENH-Q07EXEC-20261024, default ON; OFF restores the fire-price rule): filters, sizing and stop are revalidated at the latest bar close; the fire price (falling back to the latest close) is the stale / control price.
9. Sizing: qty = int((budget / slots) // price) = int(1194.0 // price); qty at or below 0 emits nothing. Emit a market, day, buy_to_open entry with stop_price = round(price times (1 - 0.15), 4) and a reason naming q07 entry, the family, 1w, the band, the filters, the horizon, the age in sessions and the price.

## Files in this repo
- Adapter: adapters3/s_q07w_s78_sm_cheap5_wcov.py (SLEEVE_ID=s_q07w_s78_sm_cheap5_wcov; SPEC = SPECS[SLEEVE_ID]; evaluate(view, ctx) delegates to desk3/lazarus_q07.evaluate_sleeve, with INPUTS and PRODUCERS imported from that engine). Also present as sleeves/s_q07w_s78_sm_cheap5_wcov.py and integration/s_q07w_s78_sm_cheap5_wcov_adapter.py.
- Shared engine file: desk3/lazarus_q07.py (SPECS entry for s_q07w_s78_sm_cheap5_wcov, evaluate_sleeve, passes_filters, QQQ-down and signal-age helpers).
- Existing strategy doc: strategies/lazarus/lz-q07.md. Per-sleeve algorithm doc in this repo: docs/S_Q07W_S78_SM_CHEAP5_WCOV-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_q07w_s78_sm_cheap5_wcov), also at config/sleeves.json.

## Configuration
Module adapters3.s_q07w_s78_sm_cheap5_wcov; cadence_s 86400; session rth; slice capital_usd 1194.0, cash_usd 1194.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [fires, bars, positions]; parked true. Universe: Tensor 1W fires in the swing family and small band that pass the named filters; timeframe 1W (weekly fires, daily bars for prices and QQQ). Engine SPEC slots=1, budget=1194.0 (per-slot 1194.0). Source: muse-desk-v3/config/sleeves.json row id=s_q07w_s78_sm_cheap5_wcov.

## Data inputs
Inputs are fires, bars and positions. Producers named in desk3/lazarus_q07.py PRODUCERS: sleeve_feed_composer (outputs fires, freshness_sla_s 604800), bars (freshness_sla_s 3600) and broker_readback (outputs positions, freshness_sla_s 3600). Fires carry symbol, family, band / cap_band, signal_date / fired_at, price and the alt-data tags the filters read (tags may be under fire["tags"] or flat on the fire); bars give closes per symbol including QQQ (at least 2 QQQ closes for the QQQ-down check, and up to 127 closes when mom6 must be computed from bars); positions is the broker readback with qty, avg_price and opened_at / entry_date. No fresh fires means no entry, and a filter with no evidence fails closed.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/laz_sleeves/_common.py is laz_sleeves/_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_q07w_s78_sm_cheap5_wcov` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_q07w_s78_sm_cheap5_wcov.py, whose evaluate(view, ctx) calls desk3/lazarus_q07.evaluate_sleeve(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with a held position whose last price is at or below avg_price times 0.85: exactly one sell_to_close exit for the full quantity, reason containing stop_15pct, even though the lane is parked.
- Fixture with a held position held for at least 546 calendar days and no stop hit: exactly one sell_to_close exit, reason containing horizon_78w.
- Fixture with no held position and a fully qualifying swing / small fire on a QQQ-down day: no entry while parked is true (the parked gate in evaluate_sleeve returns exits only).
- With the parked gate removed in a test harness only: a QQQ-down fixture with a fire aged at most 5 sessions passing every filter (cheap5, wcov) gives exactly one market buy_to_open entry, qty int(1194.0 // price), stop_price round(price times 0.85, 4).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
