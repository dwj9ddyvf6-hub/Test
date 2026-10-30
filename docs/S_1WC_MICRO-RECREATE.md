# s_1wc_micro: Recreation package

Provenance: Source row in strategies/lazarus/lz-weekly-cyan-tier-a.md in this repo: Family Lazarus; Source research (tracker sc_tag / ue_tag tiers), run by Lazarus (the doc's Source row names the research source in a form the repo gate blocks, so the blocked attribution token is omitted here and the rest is verbatim); the per-sleeve algorithm doc docs/S_1WC_MICRO-ALGORITHM.md states it was derived from the sleeve code on 2026-10-29 (no author spec on file).

## What this sleeve is
This is a long-only US equity Lazarus fire-consumer sleeve: signal generation stays upstream in the fire producer and this sleeve's thin adapter delegates to the shared desk3/lazarus.py engine with its own SPECS entry. It buys fresh matching fires into its slots and manages held positions with the engine's stop, target and time exits. Sources: adapters3/laz_s_1wc_micro.py and desk3/lazarus.py (SPECS entry s_1wc_micro) on the desk.

## Full algorithm
This sleeve's SPECS entry (desk3/lazarus.py): slots=1, capital=1000.0, cadence_s=3600, session="rth", max_age_min=11520 (60*24*8), stop_pct=0.15, horizon_sessions=252, family="cyan", tf="1W", cap_tier="micro", signal_tier="A". No qqq_down, max_price, deep or min_vix key is set.

Sleeve-specific gates: family cyan and timeframe 1W are enforced only on fires carrying a family/color field; a carried signal_tier/tier must equal A and a carried cap_tier must equal micro. The 15% stop applies: entry stop_price = round(price * 0.85, 4) and the stop exit reason is <sleeve>_stop15.

Common engine evaluation, in code order (desk3/lazarus.py evaluate()):

Exits first, per held position, first trigger wins, and if any exit intent is emitted the call returns with no entries evaluated: (1) stop, only where the spec sets stop_pct: current price (fire price if carried, else latest bar close) at or below avg_price * (1 - stop_pct), sold in full, reason <sleeve>_stop15; (2) target: current price at or above the target_price stored in the sleeve state at entry, sold in full; (3) partial, only where partial_pct is set (this sleeve sets none, unless its spec above says otherwise); (4) target_pct, only where set (this sleeve sets none, unless stated above); (5) time: sessions held at or above the stored horizon_sessions (or the spec horizon when no stored value exists), sold in full. Sessions held are counted from extra session_dates when supplied, else from SPY bar dates, else business days. Exits are market, day, sell.

Entries, only when no exit fired and open positions are fewer than slots: fires are read from view lazarus_fires, extra lazarus_fires, view tensor_fires, or extra fires (the first list found). A fire is skipped when it is not a dict, its sleeve_id (when present) differs from this sleeve, its symbol is missing or already held, its side is not buy/long, its fired_at/ts is unparseable, or its age is below 0 or above max_age_min. Family, signal-tier and cap-tier filters are enforced only when the fire carries that field: a carried family/color must contain the spec family, a carried signal_tier/tier must equal the spec signal_tier, and a carried cap_tier must be in the spec cap tier(s). The sleeve-specific gates in the spec paragraph above then apply in code order (ml_pick, max_price on the fire price, deep/deep60, min_vix, qqq_down, both_red where set). Price: the fire price is the base price, falling back to the latest bar close; with the fresh-price enhancement on by default (ENH-LAZ-REPRICE-20261024; switched by extra <sleeve>_improve fresh_price), sizing, stop anchor and price_hint use the freshest completed bar close when it exists and differs, with the fire-price decision recorded as the paired shadow control on the intent. The bound guard (ENH19-LAZ-BOUND-20261024, on by default) then refuses an entry whose fresh price is at or above the fire target_price, or at/above the spec max_price where one is set (above it where the spec marks the cap inclusive). Sizing: per_slot = capital / slots; qty = int(per_slot // execution price); qty below 1 emits nothing. Entry intents are market, day, buy, reason <sleeve>_tensor_fire, with stop_price = round(price * (1 - stop_pct), 4) when the spec sets a stop, otherwise None. On entry the sleeve state file (laz_state.json under ctx state_dir) records horizon_sessions (the fire's own horizon when the spec sets horizon_from_fire or the fire carries one, otherwise the spec horizon; plus one where horizon_plus_one is set, which this sleeve does not set unless stated above), target_price and entry_at. Entries stop once slots are filled.

## Files in this repo
- Adapter (sleeve module): adapters3/laz_s_1wc_micro.py (thin wrapper; SLEEVE_ID=s_1wc_micro); also copied in this repo at integration/s_1wc_micro_adapter.py and sleeves/s_1wc_micro.py.
- Shared engine: desk3/lazarus.py (repo path desk3/lazarus.py; the SPECS entry for s_1wc_micro and evaluate()).
- Existing strategy doc: strategies/lazarus/lz-weekly-cyan-tier-a.md.
- Per-sleeve algorithm doc: docs/S_1WC_MICRO-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_1wc_micro); also config/sleeves.json in this repo.

## Configuration
Module adapters3.laz_s_1wc_micro; cadence_s 3600; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [lazarus_fires, bars, positions]; parked false. Source: muse-desk-v3/config/sleeves.json row id=s_1wc_micro. Per-slot capital from the engine spec is 1000.0 / 1 = 1000.0.

## Data inputs
Lazarus fires: a list of fire dicts {sleeve_id, symbol, fired_at, price, target_price?, horizon_sessions?, horizon_hours?, cap_tier?, signal_tier?, color/family?, ml_pick?, qqq_red?, stock_red?, tags?} supplied by the desk's Tensor bundle producer into view lazarus_fires (or extra lazarus_fires / tensor_fires / extra fires), substituting for the upstream tracker fire file, which is unreachable from the desk; daily bars {SYM|1Day} (and SPY bars for the session count fallback) and positions from the snapshot; sleeve state from laz_state.json under the ctx state_dir. Fail-closed: no fresh matching fire means no entry, and missing QQQ-red data for a QQQ-down sleeve means no entry.

## Install and run
1. Place the adapter at adapters3/laz_s_1wc_micro.py (also copied in this repo at integration/s_1wc_micro_adapter.py and sleeves/s_1wc_micro.py) and the shared engine desk3/lazarus.py at its repo path desk3/lazarus.py, plus every other shared file listed under Files in this repo.
2. Register the config row for `s_1wc_micro` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so lazarus_fires, bars and positions arrive in the snapshot view in the shapes the algorithm section describes; the engine consumes only ingested fires and never fetches the upstream tracker itself.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which delegates to desk3.lazarus.evaluate(SLEEVE_ID, view, ctx) with this sleeve's SPECS entry.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): one fresh fire matching this sleeve's family, tier, cap and sleeve-specific gates, with slots free, produces one market buy sized int((capital / slots) // execution price) with the spec stop_price rule and reason <sleeve>_tensor_fire. Fixture B: the same fire aged past max_age_min, or carrying a failing sleeve-specific gate value, produces no entry.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
