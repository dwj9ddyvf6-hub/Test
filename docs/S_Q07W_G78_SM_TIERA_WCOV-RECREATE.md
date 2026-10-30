# s_q07w_g78_sm_tierA_wcov: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 fire-consumer sleeve in the green family, small band, with a 78-week horizon and the filters tierA, wcov. It buys one $1,000 slot only on a QQQ-down day within 5 sessions of a Tensor 1W fire that passes every named filter, and exits on a 15 percent stop or at the horizon. Sources: desk adapters3/s_q07w_g78_sm_tierA_wcov.py and desk3/lazarus_q07.py SPECS.

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) delegates to desk3/lazarus_q07.py evaluate_sleeve(SLEEVE_ID, view, ctx), with SPEC = SPECS[SLEEVE_ID] from that engine. Wrapper note (desk adapters3/<id>.py): Q07 Green H78 small tierA+wiki_cov (CSV ON), Lazarus Q07 batch 4.

SPEC (desk3/lazarus_q07.py SPECS): family="green", band="small", horizon_w=78, filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False in the engine SPEC. Constants in the engine: STOP_FRAC=0.15, WINDOW_SESSIONS=5. Inputs: fires, bars, positions.

Evaluation order in desk3/lazarus_q07.py evaluate_sleeve():
1. Exits first. For each held position with qty above 0 and entry (avg_price) above 0: last price is the last close from bars (or current_price fallback). If price is at or below entry times (1 - 0.15), sell the full quantity, reason "q07 exit: stop_15pct". Otherwise, if held calendar days (session date minus opened_at / entry_date) are at least horizon_w times 7 (546 days for 78 weeks), sell the full quantity, reason "q07 exit: horizon_78w". Exits are market, day, sell_to_close.
2. The engine SPEC parked flag is False for this sleeve, so entries are evaluated after exits as below.
3. Entries require an open slot (slots minus distinct held symbols above 0) and a QQQ-down day: extra["qqq_red"] if it is a bool, else market["qqq_red"] if it is a bool, else QQQ last close below its prior close (needs at least 2 QQQ closes). If QQQ is not down, return only any exits.
4. Fires are read from view["fires"]. A fire is skipped if it has no symbol, its sleeve_id / sleeve (when carried) differs from this sleeve, its family does not normalise to "green" (cyan accepts cyan / w_cyan / c; green accepts green / w_green / g; swing accepts swing / w_swing / s), its band / cap_band does not normalise to "small" (midlarge accepts ml / midlarge / mid_large / mid/large; small accepts sm / small), or its symbol is already held.
5. Signal age: sessions since signal_date / fired_at / fire_date / date, counted on QQQ bar dates when available else calendar days times 5/7, must be present and at most WINDOW_SESSIONS=5.
6. Freshest-first (ENH-Q07FRESH-20261024, default ON; OFF restores producer list order): when 2 or more candidate fires pass the sleeve / family / band / held checks, allocate the slot freshest-signal-first.
7. Filters, all must pass and a filter with no evidence fails closed: tierA: a tier tag equal to "A", or a true tier_a tag; wcov: a true wiki_cov tag, else wiki_views above 0, else a true wiki_coverage tag, else wiki_attention in (covered, high, spike); no wiki evidence fails closed.
8. Execution price (ENH-Q07EXEC-20261024, default ON; OFF restores the fire-price rule): filters, sizing and stop are revalidated at the latest bar close; the fire price (falling back to the latest close) is the stale / control price.
9. Sizing: qty = int((budget / slots) // price) = int(1000.0 // price); qty at or below 0 emits nothing. Emit a market, day, buy_to_open entry with stop_price = round(price times (1 - 0.15), 4) and a reason naming q07 entry, the family, 1w, the band, the filters, the horizon, the age in sessions and the price.

## Files in this repo
- Adapter: adapters3/s_q07w_g78_sm_tierA_wcov.py (SLEEVE_ID=s_q07w_g78_sm_tierA_wcov; SPEC = SPECS[SLEEVE_ID]; evaluate(view, ctx) delegates to desk3/lazarus_q07.evaluate_sleeve, with INPUTS and PRODUCERS imported from that engine).
- Shared engine file: desk3/lazarus_q07.py (SPECS entry for s_q07w_g78_sm_tierA_wcov, evaluate_sleeve, passes_filters, QQQ-down and signal-age helpers).
- Existing strategy doc: strategies/lazarus/lz-q07.md. Per-sleeve algorithm doc in this repo: docs/S_Q07W_G78_SM_TIERA_WCOV-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_q07w_g78_sm_tierA_wcov), also at config/sleeves.json.

## Configuration
Module adapters3.s_q07w_g78_sm_tierA_wcov; cadence_s 86400; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [fires, bars, positions]; parked false. Universe: Tensor 1W fires in the green family and small band that pass the named filters; timeframe 1W (weekly fires, daily bars for prices and QQQ). Source: muse-desk-v3/config/sleeves.json row id=s_q07w_g78_sm_tierA_wcov.

## Data inputs
Inputs are fires, bars and positions. Producers named in desk3/lazarus_q07.py PRODUCERS: sleeve_feed_composer (outputs fires, freshness_sla_s 604800), bars (freshness_sla_s 3600) and broker_readback (outputs positions, freshness_sla_s 3600). Fires carry symbol, family, band / cap_band, signal_date / fired_at, price and the alt-data tags the filters read (tags may be under fire["tags"] or flat on the fire); bars give closes per symbol including QQQ (at least 2 QQQ closes for the QQQ-down check, and up to 127 closes when mom6 must be computed from bars) and VIX / ^VIX closes when a vix20 filter needs them; positions is the broker readback with qty, avg_price and opened_at / entry_date. No fresh fires means no entry, and a filter with no evidence fails closed.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (a desk3/ path is the same path on a fresh desk; an engines/ path maps back to the desk path after engines/). No extra files beyond the listed adapter, engine and config.
2. Register the config row for `s_q07w_g78_sm_tierA_wcov` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_q07w_g78_sm_tierA_wcov.py, whose evaluate(view, ctx) calls desk3/lazarus_q07.evaluate_sleeve(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a green / small fire aged at most 5 sessions that passes every filter (tierA, wcov), no held position and a latest close giving qty above 0: exactly one market buy_to_open entry, qty int(1000.0 // price), stop_price round(price times 0.85, 4), reason naming q07 entry, the filters and horizon=78w.
- Fixture on a day that is not QQQ-down, or with any one named filter lacking positive evidence, or with the fire aged more than 5 sessions: no entry.
- Fixture with a held position whose last price is at or below avg_price times 0.85: exactly one market sell_to_close exit for the full quantity, reason containing stop_15pct, and no entry in the same call.
- Fixture with a held position held for at least 546 calendar days and no stop hit: exactly one sell_to_close exit, reason containing horizon_78w.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
