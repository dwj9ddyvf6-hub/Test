# lz_s_rules_1w - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Lab rule 1W (test)", type other, family 1w, algorithm grade PARTIAL with gap: sizing not recorded in any consulted source. Accounting entry (verbatim): entry {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}; exit {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = the rule horizon H + 1 sessions)", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}; data: lab_live books (native Lazarus routing) :: DESK_INTEGRATION/lab_live/out/latest/*.json. Alias lz_s_rules_1w, status md2_catalog installed. Classification evidence in the accounting: only generic fear_day execution and lab_live book routing are recorded for this id, with the rule book content itself not in any readable source.
- The canonical id carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same lane uses the id without the lz_ prefix, s_rules_1w. That mapping is evidenced by the identical label, entry, exit and data source in the lz_engine config row for s_rules_1w (see Configuration) and by the existing recreation package for the unprefixed form, `docs/S_RULES_1W-RECREATE.md`.
- Existing Test packages for the unprefixed form: `docs/S_RULES_1W-RECREATE.md` and `docs/S_RULES_1W-ALGORITHM.md`; strategy doc `strategies/lazarus/lz-lab-rules.md` (source row: research lab (frozen rules), run by Lazarus; one attribution token in that row is blocked by the repo gate and is omitted here).
- Wrapper note in Test (`sleeves/s_rules_1w.py`): "v3 Lazarus fire-consumer sleeve s_rules_1w (batch 2). Engine: desk3/lazarus.py. Lab rule 1W - 43 frozen rules (CSV ON, Live). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2."
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `sleeves/s_rules_1w.py`, `desk3/lazarus.py` SPECS entry s_rules_1w, `config/sleeves.json` row s_rules_1w and `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_rules_1w: all found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: no lazarus rules sleeve path); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no executable rules sleeve for this lane); dwj9ddyvf6-hub/Midna (recursive tree: no rules 1w sleeve path). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A long-only weekly Lazarus fire-consumer lane for the research lab's frozen rules (43 frozen rules, CSV ON, Live): signal generation stays upstream in the lab_live books, and this lane buys qualifying lab fires only on a QQQ-down day, in up to 6 slots at $1,000 per slot from a $6,000 slice, with a 15% stop, exiting also at a stored target or at each rule's horizon plus one session. The rule book content itself is not in any readable source in the accounting; the lane's executable behaviour is the shared Lazarus engine under its s_rules_1w SPECS entry.

## Full algorithm

Two layers, both in the record; do not merge them.

Layer A - the md2 / lz_engine lane record for this canonical id (accounting, verbatim values):
1. Entry wrapper: policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
2. Exit wrapper: the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = the rule horizon H + 1 sessions), hold_from fill, hold_unit_kind 1d, stop_pct null, max_bars null, plan_overrides [].
3. Data: lab_live books (native Lazarus routing), files DESK_INTEGRATION/lab_live/out/latest/*.json.
4. Sizing: not in the accounting record (accounting gap). The lz_engine config row for the unprefixed form records sizing budget_usd 6000, max_slots 6, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000, with flags: lane budget raised to $10,000 / 10 slots (Trader 2026-10-15), then L-146 scaled x0.611 ($10,000 -> $6,000 / 6 slots).

Layer B - the executable engine in Test (`desk3/lazarus.py`, SPECS entry s_rules_1w, reached through the thin adapter `sleeves/s_rules_1w.py` / `adapters3/s_rules_1w.py`, whose evaluate(view, ctx) delegates to desk3.lazarus.evaluate with SLEEVE_ID s_rules_1w), evaluation order in evaluate():
1. SPECS entry: slots 6, capital 6000.0, cadence_s 3600, session rth, max_age_min 11520 (60*24*8), qqq_down True, stop_pct 0.15, horizon_sessions 27, horizon_from_fire True, horizon_plus_one True. Per-slot budget is capital / slots = 1000.0. No family, signal_tier, cap_tier, max_price, deep or min_vix key is set.
2. Exits first, per held position, first trigger wins, and if any exit intent is emitted the call returns with no entries evaluated: (1) stop: current price at or below avg_price * (1 - 0.15), sold in full, reason s_rules_1w_stop15; (2) target: current price at or above the target_price stored in sleeve state at entry, sold in full; (3) time: sessions held at or above the stored horizon (the fire's horizon_sessions where horizon_from_fire applies, plus 1 where horizon_plus_one applies; otherwise the SPECS horizon 27), sold in full. Sessions held are counted from extra session_dates when supplied, else SPY bar dates, else business days. Exits are market, day, sell. The partial and target_pct branches do not apply to this SPECS entry (it sets neither).
3. Freshest-first for the rules lanes (ENH25-RULES-FRESH-20261024, default ON for s_rules_1d and s_rules_1w; OFF restores producer list order): candidate fires for this sleeve id are reordered freshest fired_at first (stable) when 2 or more candidates exist, with a paired journal record.
4. Entries, only when no exit fired and open positions are fewer than slots (6): fires are read from view lazarus_fires, extra lazarus_fires, view tensor_fires, or extra fires (the first list found). A fire is skipped when it is not a dict, its sleeve_id (when present) differs from this sleeve, its symbol is missing or already held, its side is not buy/long, its fired_at/ts is unparseable, or its age is below 0 or above max_age_min 11520.
5. Gates: family, tier and cap filters are enforced only when the SPECS entry names them; this entry sets none, so none of those checks filter this sleeve. The QQQ-down gate applies: the fire's qqq_red/qqq_down value is used, else QQQ red is derived from QQQ bars; missing QQQ-red data means no entry.
6. Price: the fire price is the base price, falling back to the latest bar close; with the fresh-price enhancement on by default (ENH-LAZ-REPRICE-20261024), sizing, stop anchor and price_hint use the freshest completed bar close when it exists and differs, with the fire-price decision recorded as the paired shadow control on the intent. The bound guard (ENH19-LAZ-BOUND-20261024, on by default) then refuses an entry whose fresh price is at or above the fire target_price.
7. Sizing and state: qty = int(per_slot // execution price) = int(1000.0 // price); qty below 1 emits nothing. Entry intents are market, day, buy, reason s_rules_1w_tensor_fire, with stop_price = round(price * (1 - 0.15), 4). On entry the sleeve state file (laz_state.json under ctx state_dir) records horizon_sessions (the fire's own horizon where present, plus 1 under horizon_plus_one; otherwise 27), target_price and entry_at. Entries stop once slots are filled.
8. Fail-closed: no fresh matching fire means no entry; the engine consumes only ingested fires and never fetches the upstream tracker itself.

## Files in this repo

- This package: `docs/LZ_S_RULES_1W-RECREATE.md`
- Adapter / sleeve module (already in Test): `sleeves/s_rules_1w.py` (thin wrapper; SLEEVE_ID s_rules_1w; the 43-frozen-rules note); also at `adapters3/s_rules_1w.py` and `integration/s_rules_1w_adapter.py`.
- Shared engine (already in Test): `desk3/lazarus.py` (SPECS entry s_rules_1w and evaluate()).
- Existing packages for the unprefixed form: `docs/S_RULES_1W-RECREATE.md`, `docs/S_RULES_1W-ALGORITHM.md`.
- Strategy doc: `strategies/lazarus/lz-lab-rules.md`.
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_rules_1w; roster row s_rules_1w in `config/sleeves.json` (also `engines/config/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, entry "Lab rule 1W (test)".

## Configuration

- lz_engine config row for s_rules_1w in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim values): kind 1w, label "Lab rule 1W (test)", enabled true, state live, status_text "ready (unarmed: desk staged)", source {producer: "lab_live books (native Lazarus routing)", file: "DESK_INTEGRATION/lab_live/out/latest/*.json", lane: "s_rules_1w"}, entry and exit as in Layer A, sizing and flags as in Layer A item 4, research lines naming DESK_INTEGRATION/DESK_PLAN.md F1 + F2 and the desk playbook lane t_rules_1w.
- Roster row for s_rules_1w in `config/sleeves.json`: module adapters3.s_rules_1w, cadence_s 3600, session rth, slice capital_usd 6000.0 and cash_usd 6000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, params {}, inputs [lazarus_fires, bars, positions], parked false, timeout_s null.
- Engine SPECS values are in the Full algorithm, Layer B.

## Data inputs

- lab_live book files (DESK_INTEGRATION/lab_live/out/latest/*.json) as the upstream signal source for the lane record; on the desk the engine consumes ingested fires in the snapshot: view lazarus_fires (or extra lazarus_fires / view tensor_fires / extra fires), fire dicts {sleeve_id, symbol, fired_at, price, target_price?, horizon_sessions?, qqq_red?, stock_red?}.
- Daily bars (and SPY bars for the session-count fallback, QQQ bars for the red check), and positions from the snapshot.
- Sleeve state from laz_state.json under the ctx state_dir.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry in `docs/ALL-SLEEVES.json`, and the unprefixed package `docs/S_RULES_1W-RECREATE.md`.
3. Place the adapter at `sleeves/s_rules_1w.py` (also `adapters3/s_rules_1w.py`) and the shared engine at `desk3/lazarus.py`, at those repo paths.
4. Register the config rows for s_rules_1w from `config/sleeves.json` and `packages/grokbot/rl64/lz_engine/config/sleeves.json` exactly as given in Configuration, with no parameter overrides (roster params {}).
5. Wire the producers named in Data inputs so lazarus_fires, bars and positions arrive in the snapshot view in the shapes the Full algorithm describes.
6. Run the desk cycle; the entry point is the adapter's evaluate(view, ctx), which delegates to desk3.lazarus.evaluate(SLEEVE_ID, view, ctx). Verify against the Verification section before enabling live paper routing.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- Entry fixture: a qualifying fire aged within 11520 minutes on a QQQ-down day, with slots free and no fresher different close, produces a market buy sized int(1000.0 // price) with stop_price round(price * 0.85, 4) and reason s_rules_1w_tensor_fire, up to 6 slots.
- No-entry fixtures: the same fire on a day that is not QQQ-down, aged above 11520 minutes, with side not buy/long, or with a fresh price at or above the fire target_price, produces no entry.
- Exit fixtures: a held position at or below avg_price * 0.85 produces exactly one full sell exit (reason s_rules_1w_stop15) and no entry in the same call; a held position reaching its stored horizon (the fire horizon plus 1 where the fire carried one, otherwise 27 sessions) with no stop or target hit produces one full time exit.
- Ordering fixture: with two or more candidate fires and the freshest-first switch on, the freshest fired_at is allocated first; with it off, producer list order is restored exactly.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
