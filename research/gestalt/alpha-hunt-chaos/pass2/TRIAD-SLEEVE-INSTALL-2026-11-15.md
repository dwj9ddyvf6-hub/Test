# TRIAD SLEEVE INSTALL PACKAGE, 2026-11-15

Built by Midna for Claude (master desk), Triad install help, Sun 2026-11-15 23:22 ET.

Source of record: dwj9ddyvf6-hub/muse-desk-v3 at remote main head `58bff1503b5560c5fb20735665c0c79d9535828d` (read fresh at build time; every snippet below is extracted from that committed tree, never from a working copy). Desk gate on that tree: Ran 2392 tests, OK (receipt 20261116T040329Z-20293). Roster at that head: 361 sleeves.

Landing commits, in order:

- `173d818d5072dd162f6708904ba1054466c2ab03` VARIATION-ROSTERING-20261115: the 19 F4 variations rostered as first-class sleeves.
- `53d7cd30e7931ba72e472b920aee437b95108afa` CONVERSION-ARMING-20261115: Turtle 20/10 rostered (gate receipt 20261116T012509Z-4554, Ran 2346 tests OK) and the first conversion shadow arms registered.
- `a090950183dd964208692cd0bdb8eaa224b419f8` ENJ-FEED-CONV27-20261115: the ENJ bars feed cure and the CONV-27 arm (gate receipt 20261116T015555Z-9455, Ran 2361 tests OK).
- `6e9441ba8f0f9d4064d834e84814f2926e6f9075` SSO-PORT-CONV46-20261115: the SSO Opus port and pair rostering (gate receipt 20261116T032233Z-11615, Ran 2373 tests OK).
- `a0a481f55694e2f0711bfb95eff14935d754fceb` CONVERSION-PASS2-ARMING-20261115: 14 more grader arms, census 14 to 28 (gate receipts 20261116T033631Z-13847 and 20261116T033916Z-14848, Ran 2374 tests OK).
- `58bff1503b5560c5fb20735665c0c79d9535828d` GOING-LIVE-GRADER-ARMS-20261115: 25 more grader arm constructions, census 28 to 53 (gate receipt 20261116T040329Z-20293, Ran 2392 tests OK).

Grading standard: each item carries Midna's registered falsifier and kill rule verbatim. They are the shared grading standard for the Triad unless Claude registers a dissent in the room or the drop. Sizing on Claude's side is Claude's decision under his own rails; Midna's desk uses the standard 10000 USD slice per sleeve, shown in the config snippets as the reference form.

Inventory in this package: 2 SSO sleeves (Section 1), 1 Turtle sleeve (Section 2), 1 ENJ feed cure feeding 22 ENJ sleeves plus its grading arm (Section 3), 19 F4 variation sleeves (Section 4), and the conversion grader registry of 53 arms under 47 register rows (Section 5). Total installable items: 23 sleeves, 1 feed cure, 53 grader arms.

---

## Section 1: The SSO pair (CONV-46, SSO-PORT-CONV46-20261115)

What it is: the 2026-11-03 research SSO Opus swing baseline, ported line-faithfully to the desk, plus its TIME_25-removal variation beside it. The parent was never edited into the variation; one shared engine serves both so the two forms cannot drift.

Source paths at the pinned head:

- Engine: `desk3/sso_opus.py` (simulate core; live evaluate with drop_time25 False for the parent, True for the variation).
- Adapters: `adapters3/sso_opus.py` and `adapters3/sso_opus_notime25.py` (thin wrappers over desk3/sso_opus.evaluate).
- Roster entries: `config/sleeves.json` rows `sso_opus` and `sso_opus_notime25` (full snippets below).
- Variation registration: `config/conversion_variations_20261115.json` entry CONV-46 (full snippet below).
- Blocker: `tests/test_conv46_sso_port_20261115_blockers.py` (12 tests; fail direction proven on a git-archive copy of a090950: 11 of 12 fail or error).
- BUGLOG entry: SSO-PORT-CONV46-20261115 in `BUGLOG_2026-11-15.md`.

Data feed requirements:

- The sleeves declare inputs `bars`, `bars:SSO:15Min`, `positions`. The producer key `bars:SSO:15Min` is declared in `desk3/producers_g4.py` (the fed registry's granular key).
- Warm layer: `desk3/warm.py` carries the SSO 15Min fetch, 30 days, in the SOXL lane's shape: `("SSO", "15Min", 30)`. At landing the warm cache carried SSO|15Min 1224 bars.
- Cadence 300 s, session rth, fills next_bar per the costs block.

Fidelity evidence (why the port can be trusted, and how to re-verify): the original research harness reproduces its own ledgers exactly (265 primary trades at cost 0, 282 at cost 5bp, 0 divergences), and the desk port reproduces both ledgers trade-for-trade at 1e-9 relative tolerance (265/265 and 282/282, 0 divergences) plus the harness's synthetic known-answer series 4/4. Result file on Midna's side: `~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/sso_fidelity_result.json` (FIDELITY: PASS), checker `pass2/sso_fidelity_check.py` in the same folder. Ask in the drop and Midna re-runs it or walks any line of it.

Roster config snippets (verbatim from config/sleeves.json at the pinned head):

```json
{
 "id": "sso_opus",
 "module": "adapters3.sso_opus",
 "cadence_s": 300,
 "session": "rth",
 "slice": {
  "capital_usd": 10000.0,
  "cash_usd": 10000.0
 },
 "bp_buffer_frac": 0.02,
 "flat_by_close": false,
 "flatten_time_et": null,
 "params": {},
 "costs": {
  "fill_timing": "next_bar",
  "commission_per_share": 0.0,
  "commission_bps": 0.0,
  "min_commission_per_order": 0.0,
  "slippage_model": "forecast_per_name",
  "slippage_bps": null
 },
 "rebalance_policy": {
  "frequency": "signal_driven",
  "drift_threshold": null,
  "drift_type": null,
  "partial_rebalance": false,
  "tracking_error_threshold": null,
  "tracking_error_window_days": null,
  "max_annual_turnover": null,
  "signal_change_rebalance": true,
  "execution_timing": "on_evaluation",
  "enforcement": "declared_not_enforced",
  "status": "ESCALATED_FOR_RULING",
  "enforced_dimensions": []
 },
 "inputs": [
  "bars",
  "bars:SSO:15Min",
  "positions"
 ],
 "parked": false
}
```

```json
{
 "id": "sso_opus_notime25",
 "module": "adapters3.sso_opus_notime25",
 "cadence_s": 300,
 "session": "rth",
 "slice": {
  "capital_usd": 10000.0,
  "cash_usd": 10000.0
 },
 "bp_buffer_frac": 0.02,
 "flat_by_close": false,
 "flatten_time_et": null,
 "params": {},
 "costs": {
  "fill_timing": "next_bar",
  "commission_per_share": 0.0,
  "commission_bps": 0.0,
  "min_commission_per_order": 0.0,
  "slippage_model": "forecast_per_name",
  "slippage_bps": null
 },
 "rebalance_policy": {
  "frequency": "signal_driven",
  "drift_threshold": null,
  "drift_type": null,
  "partial_rebalance": false,
  "tracking_error_threshold": null,
  "tracking_error_window_days": null,
  "max_annual_turnover": null,
  "signal_change_rebalance": true,
  "execution_timing": "on_evaluation",
  "enforcement": "declared_not_enforced",
  "status": "ESCALATED_FOR_RULING",
  "enforced_dimensions": []
 },
 "inputs": [
  "bars",
  "bars:SSO:15Min",
  "positions"
 ],
 "parked": false
}
```

Variation registration (verbatim from config/conversion_variations_20261115.json):

```json
{
 "chassis_inheritance": [
  "The parent itself is the port: sso_opus is the 2026-11-03 research baseline (trendspider-sso-opus-test-20261103 harness run_sim, trail_from=close) rebuilt as desk3/sso_opus.py and proven against the research trade ledgers before rostering; there was no installed form on any live surface to inherit from (the register row's premise on that point did not survive verification, recorded in CONVERSION-BLOCKED-20261115).",
  "Sizing is the standard desk slice ($10,000) at full slice per trade, the research form's own 100%-of-equity compounding translated to the desk's fixed slice; the sim's next-bar-open fills are carried by the sleeve's costs (fill_timing next_bar)."
 ],
 "conv": "CONV-46",
 "engine": "desk3/sso_opus.py (simulate core; live evaluate with drop_time25=True for this variation, False for the parent)",
 "falsifier": "The variation's first 20 forward fires graded against the installed form's same-day fires (the uniform variation falsifier form).",
 "form": "The installed SSO Opus form minus exactly the TIME_25 exit class: the ported exit priority (STOP_LOSS, TRAILING_STOP, TAKE_PROFIT, TIME_25, TIME_60) with the TIME_25 branch removed, so a bar that would have exited TIME_25 falls through to the TIME_60 check; every other rule, indicator and threshold is the baseline's, shared in one engine so the two forms cannot drift.",
 "id": "sso_opus_notime25",
 "kill_rule": "Paired delta not positive retires the variation; the installed form is untouched either way.",
 "module": "adapters3.sso_opus_notime25",
 "parent": "sso_opus",
 "replay_counts": "Fidelity basis (pass2/sso_fidelity_check.py, result in pass2/sso_fidelity_result.json): the original research harness reproduces its own ledgers exactly (265 primary trades at cost 0, 282 at cost 5bp, 0 divergences), and the desk port reproduces both ledgers trade-for-trade at 1e-9 relative tolerance (265/265 and 282/282, 0 divergences) plus the harness's synthetic known-answer series (4/4). Variation historical anatomy on the same frame (context only, never its grade): 242 trades, total +110.7%, avg +0.395%, exit mix TIME_60 175 / STOP_LOSS 42 / TRAILING_STOP 10 / TAKE_PROFIT 15, against the baseline's 265 trades and TIME_25 166 exits.",
 "status": "ROSTERED 2026-11-15 (SSO-PORT-CONV46-20261115); forward accrual from Mon 2026-11-16."
}
```

Falsifier (verbatim, Conversion Register CONV-46): "The variation's first 20 forward fires graded against the installed form's same-day fires (the uniform variation falsifier form)."
Kill rule (verbatim): "Paired delta not positive retires the variation; the installed form is untouched either way."

Install order: (1) copy desk3/sso_opus.py and both adapters; (2) add the two roster rows; (3) wire the SSO 15Min warm fetch and declare the bars:SSO:15Min producer key, or the pair reads UNFED by name; (4) verify: run the fidelity check against the research ledgers if you hold them, confirm both sleeves evaluate clean on a live snapshot and read FED on your health roll; (5) forward accrual starts with the first session after install, graded at the variation's first 20 fires against the baseline's same-day fires.

---

## Section 2: The Turtle sleeve (CONV-47, aster_trader_turtle2010)

What it is: the recorded Turtle 20/10 breakout form rostered as a variation beside donchian55 (the 55/20 parent), under the rule that the parent is never edited into its variation. Retest basis: 129 trades, mean +293.8bp, t 1.84, win rate 0.318; fwd5 excess +47.8bp (t 0.81, n 126), fwd10 +91.2bp (t 1.07, n 122). Watch-grade at the retest; the forward paired grade is the verdict.

Source paths at the pinned head:

- Adapter: `adapters3/aster_trader_turtle2010.py`; engine: `desk3/aster_batch16.py` kind=turtle evaluator (_eval_turtle). The parent's evaluator sources are hash-pinned in the conversion blocker and byte-untouched.
- Roster entry: `config/sleeves.json` row `aster_trader_turtle2010`, a clone of the donchian55 row differing in exactly {id, module} (full snippet below).
- Registration: `config/conversion_variations_20261115.json` entry CONV-47 (full snippet below).
- Landing commit `53d7cd30e7931ba72e472b920aee437b95108afa`, gate receipt 20261116T012509Z-4554 (Ran 2346 tests, OK). Live proof at landing: health roll carried aster_trader_turtle2010 FED.

Data feed requirements: inputs `bars` and `positions` only; daily bars (cadence_s 86400, session rth). No special producer key.

Roster config snippet (verbatim):

```json
{
 "id": "aster_trader_turtle2010",
 "module": "adapters3.aster_trader_turtle2010",
 "cadence_s": 86400,
 "session": "rth",
 "slice": {
  "capital_usd": 10000.0,
  "cash_usd": 10000.0
 },
 "bp_buffer_frac": 0.02,
 "flat_by_close": false,
 "flatten_time_et": null,
 "params": {},
 "costs": {
  "fill_timing": "next_bar",
  "commission_per_share": 0.0,
  "commission_bps": 0.0,
  "min_commission_per_order": 0.0,
  "slippage_model": "forecast_per_name",
  "slippage_bps": null
 },
 "rebalance_policy": {
  "frequency": "signal_driven",
  "drift_threshold": null,
  "drift_type": null,
  "partial_rebalance": false,
  "tracking_error_threshold": null,
  "tracking_error_window_days": null,
  "max_annual_turnover": null,
  "signal_change_rebalance": true,
  "execution_timing": "on_evaluation",
  "enforcement": "declared_not_enforced",
  "status": "ESCALATED_FOR_RULING",
  "enforced_dimensions": []
 },
 "inputs": [
  "bars",
  "positions"
 ],
 "parked": false
}
```

Registration (verbatim):

```json
{
 "chassis_inheritance": [
  "Universe, slot count (10) and sizing fractions (notional 0.10, dollar-volume cap 0.01, risk 0.005 per 2 x ATR) are donchian55's desk chassis: the variation rosters under existing desk sizing, per the conversion spec's 'existing desk sizing as a variation'.",
  "The stop is checked on the last close, the desk engine's own stop convention; the retest checked intraday lows. Named divergence, accepted at rostering."
 ],
 "conv": "CONV-47",
 "engine": "desk3/aster_batch16.py kind=turtle (_eval_turtle)",
 "falsifier": "First 20 forward fires graded against the 55/20 form's fires on the same days.",
 "form": "Recorded Turtle 20/10 form (GRAVEYARD-DIG Lead 2, retested in pass2/work_graveyard/retests.py): entry on close above the prior-20-bar high, no SMA200 gate, no dollar-volume gate; exit on close below the prior-10-bar low, on the initial stop at entry minus 2 x ATR(20) (ATR = simple mean of the last 20 true ranges, the retest's own definition), or at a 252-bar timeout.",
 "id": "aster_trader_turtle2010",
 "kill_rule": "If the paired forward excess of the 20/10 form is not positive, the variation retires and donchian55 is untouched either way.",
 "module": "adapters3.aster_trader_turtle2010",
 "parent": "aster_trader_donchian55",
 "replay_counts": "Retest (pass2/work_graveyard/retests.py, 20 cache names with 300+ daily bars): 129 trades, mean +293.8bp, t 1.84, win rate 0.318; fwd5 excess +47.8bp (t 0.81, n 126), fwd10 +91.2bp (t 1.07, n 122). Watch-grade only at the retest.",
 "status": "ROSTERED 2026-11-15 (CONVERSION-VARIATION-20261115); forward accrual from Mon 2026-11-16."
}
```

Falsifier (verbatim, Conversion Register CONV-47): "Its first 20 forward fires graded against the 55/20 form's fires on the same days."
Kill rule (verbatim): "Paired forward excess not positive retires the variation; donchian55 is untouched either way."

Install order: (1) copy the adapter and the kind=turtle evaluator form (entry on close above the prior-20-bar high, no SMA200 gate, no dollar-volume gate; exit on close below the prior-10-bar low, on the initial stop at entry minus 2 x ATR(20), or at a 252-bar timeout; sizing fractions inherited from the donchian55 chassis: notional 0.10, dollar-volume cap 0.01, risk 0.005 per 2 x ATR, 10 slots); (2) add the roster row; (3) verify it evaluates on daily bars and reads FED; (4) grade at its first 20 forward fires against donchian55's same-day fires.

---

## Section 3: The ENJ feed cure (CONV-27, ENJ-FEED-CONV27-20261115)

What broke, three stacked layers, each proven on the live system: (1) desk3/aster_batch7.py's private bar reader tried only archive keys no producer serves and returned 0 bars on every live snapshot, while every sibling Aster crypto engine delegates to desk3/crypto_bars.resolve_bars; (2) the warm layer persisted no ENJ series, because ENJ/USD is unlisted at the broker and the Alpaca warm fetch returns nothing for it; (3) the conversion grader's symbol map marked ENJUSDT unpriceable and the grader counted only fills, and ENJ entries can never fill (see the broker fact below). The cure wakes all 22 ENJ sleeves on the roster (aster_abs_enj_4h, the aster_enj_nfs family, aster_pub_enj_iu_body, the aster_r19_enjusdt families, free_kraken_enj_spot, fwd_alpaca_enj_iu_body); every one read FED on Midna's health roll after the cure.

The cure, at landing commit `a090950183dd964208692cd0bdb8eaa224b419f8`:

- `desk3/aster_batch7.py`: `_bars` now delegates: `from .crypto_bars import resolve_bars` and `return resolve_bars(view.get("bars") or {}, sym, ("4Hour",))`. Archive keys still win inside the resolver. No ENJ sleeve signal logic, sizing, stops, or thresholds were touched. On the live-assembled view the delegation returns 721 bars where the private reader returned 0.
- `desk3/warm.py`: `KRAKEN_SPOT_FETCHES = (("ENJ/USD", "ENJUSD", "4Hour", 240, 90),)` persists the Kraken spot tape as the cache key ENJ/USD|4Hour (90 days at 240 minutes, the LINK fetch's shape; pure parser mirroring producers3's field mapping, volume at candle index 6; fail-closed per family: a Kraken failure leaves the key unproduced). The production warm cache carried 540 real bars from the 2026-11-16T02:34:07Z fetch.
- `desk3/conversion_shadow.py`: the grader maps ENJUSDT to the ENJ/USD tape and pools dispatcher entry intents as shadow entries for arms declaring entry_source intents.
- Blocker: `tests/test_conv27_enj_feed_20261115_blockers.py` (15 tests; fail direction proven on a git-archive copy of 53d7cd3: 11 of 15 fail or error; the 4 passes are fail-closed assertions holding on both trees by design). BUGLOG entry ENJ-FEED-CONV27-20261115.

Broker fact (verbatim from the registered arm's note): ENJ/USD is unlisted at the broker (42210000 asset-not-found), so entries fail closed at the broker seam by name and can never fill; the stream is graded on its dispatcher entry intents as shadow entries, priced at the entry date's close on the Kraken tape.

The CONV-27 grading arm (verbatim from config/conversion_shadow_20261115.json):

```json
{
 "calendar": "utc",
 "conv": "CONV-27",
 "decisive_horizons": [
  10
 ],
 "entry_source": "intents",
 "falsifier": "First 10 resolved shadow entries graded at fwd10.",
 "grade_n": 10,
 "grade_unit": "resolved entries at the decisive horizon (fwd excess vs QQQ priceable)",
 "horizons": [
  1,
  3,
  5,
  10
 ],
 "kill_rule": "Non-positive fwd10 excess over those entries retires the lead.",
 "kind": "FWD_GRADE",
 "note": "The horizon conflict is printed on the register row's face and carried here: the stream's only positive horizon is fwd10 and its fwd5 is significantly negative (fwd5 -528.8bp, t -3.11; fwd10 +558.3bp, n 6 priceable, t 1.81), so the grade is taken at fwd10 as the stream's own profile dictates and no fwd5 claim is made. Entries are the sleeves' dispatcher entry intents: ENJ/USD is unlisted at the broker (42210000 asset-not-found), so entries fail closed at the broker seam by name and can never fill; the register's named step arms the stream as shadow on the live Kraken ENJ/USD tape and grades those intents as shadow entries, priced at the entry date's close on that tape (ENJ-FEED-CONV27-20261115).",
 "parents": [
  "aster_r19_enjusdt_breakout_base_fixed16_fullcash",
  "aster_r19_enjusdt_breakout_base_fixed16_volume1pct"
 ],
 "population": "Both sizing variants of aster_r19_enjusdt_breakout_base graded as one stream, entries from dispatcher entry intents (shadow entries on the Kraken ENJ/USD tape; the asset is unlisted at the broker and entries never fill).",
 "symbol_map": {
  "ENJ/USD": "ENJ/USD",
  "ENJUSDT": "ENJ/USD"
 }
}
```

Falsifier (verbatim): "First 10 resolved shadow entries graded at fwd10." Kill rule (verbatim): "Non-positive fwd10 excess over those entries retires the lead." The horizon conflict is printed on the arm: fwd5 is significantly negative (-528.8bp, t -3.11) and fwd10 positive (+558.3bp, n 6 priceable, t 1.81), so the grade is taken at fwd10 and no fwd5 claim is made.

Install order: (1) point your batch7-equivalent ENJ readers at your family bar resolver, or copy the delegation form; (2) add the Kraken spot fetch for ENJ/USD at 4Hour and persist it under a stable tape key; (3) if you run the conversion grader, add the ENJUSDT symbol mapping and the intents entry source; (4) verify: your ENJ sleeves resolve a nonzero bar count on a live snapshot (721 bars on Midna's live-assembled view at landing) and read FED.

---

## Section 4: The 19 F4 variations (registry F4-VARIATIONS-20261115)

What they are: loosened forms of sleeves whose own strictness blocked firing, each registered as an additional sleeve variation with its own id, replay counts, falsifier, and grade; the parent is never edited into its variation, and both run and are graded separately. All 19 are rostered as first-class sleeves in config/sleeves.json at the pinned head (rostering commit `173d818d5072dd162f6708904ba1054466c2ab03`, VARIATION-ROSTERING-20261115; roster 339 to 358 at rostering). Full definitions, including each variation's parent_spec, replay block, and its own falsifier text, live in `config/f4_variations_20261115.json` at the pinned head.

Suffix scheme: _vargd = GATE_DROP (named gates removed); _varpx = PARAM_EXTREME (one constant pushed to a tail value); _varsg = SIGN_GATE_DROP (the funding sign leg dropped, every other leg unchanged).

The uniform falsifier form (each variation's own entry carries it verbatim; shown once here): "Retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only, never blended with the parent."

Inventory (id | parent | operator | what varies):

- `s_q07w_c52_ml_mom6_tierA_wlow_vargd` | parent `s_q07w_c52_ml_mom6_tierA_wlow` | GATE_DROP | alt-data filters dropped ['tierA', 'wlow']; bar-computable filters kept ['mom6']; family/band/horizon/sizing unchanged
- `s_q07w_c52_ml_mom6_wspike2_vargd` | parent `s_q07w_c52_ml_mom6_wspike2` | GATE_DROP | alt-data filters dropped ['wspike2']; bar-computable filters kept ['mom6']; family/band/horizon/sizing unchanged
- `s_q07w_c52_ml_tierA_wcov_vargd` | parent `s_q07w_c52_ml_tierA_wcov` | GATE_DROP | alt-data filters dropped ['tierA', 'wcov']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_c52_ml_tierA_wlow_vargd` | parent `s_q07w_c52_ml_tierA_wlow` | GATE_DROP | alt-data filters dropped ['tierA', 'wlow']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_c78_ml_deep70_tierA_wlow_vargd` | parent `s_q07w_c78_ml_deep70_tierA_wlow` | GATE_DROP | alt-data filters dropped ['tierA', 'wlow']; bar-computable filters kept ['deep70']; family/band/horizon/sizing unchanged
- `s_q07w_c78_ml_mom6_tierA_wlow_vargd` | parent `s_q07w_c78_ml_mom6_tierA_wlow` | GATE_DROP | alt-data filters dropped ['tierA', 'wlow']; bar-computable filters kept ['mom6']; family/band/horizon/sizing unchanged
- `s_q07w_c78_ml_tierA_wcov_vargd` | parent `s_q07w_c78_ml_tierA_wcov` | GATE_DROP | alt-data filters dropped ['tierA', 'wcov']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_c78_ml_tierA_wlow_vargd` | parent `s_q07w_c78_ml_tierA_wlow` | GATE_DROP | alt-data filters dropped ['tierA', 'wlow']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_g52_ml_ats_z1_mom6_wlow_vargd` | parent `s_q07w_g52_ml_ats_z1_mom6_wlow` | GATE_DROP | alt-data filters dropped ['ats_z1', 'wlow']; bar-computable filters kept ['mom6']; family/band/horizon/sizing unchanged
- `s_q07w_g52_ml_ins2_wlow_vargd` | parent `s_q07w_g52_ml_ins2_wlow` | GATE_DROP | alt-data filters dropped ['ins2', 'wlow']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_g52_ml_tierA_wcov_vargd` | parent `s_q07w_g52_ml_tierA_wcov` | GATE_DROP | alt-data filters dropped ['tierA', 'wcov']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_g78_ml_tierA_wcov_vargd` | parent `s_q07w_g78_ml_tierA_wcov` | GATE_DROP | alt-data filters dropped ['tierA', 'wcov']; bar-computable filters kept []; family/band/horizon/sizing unchanged
- `s_q07w_s52_ml_deep70_ins2_vix20_vargd` | parent `s_q07w_s52_ml_deep70_ins2_vix20` | GATE_DROP | alt-data filters dropped ['ins2', 'vix20']; bar-computable filters kept ['deep70']; family/band/horizon/sizing unchanged
- `s_q07w_s78_ml_deep70_ins2_vix20_vargd` | parent `s_q07w_s78_ml_deep70_ins2_vix20` | GATE_DROP | alt-data filters dropped ['ins2', 'vix20']; bar-computable filters kept ['deep70']; family/band/horizon/sizing unchanged
- `aster_tensor_c1_cash_all_25_varpx` | parent `aster_tensor_c1_cash_all_25` | PARAM_EXTREME | ret60 floor 31 -> 0 (the C1 numeric strength floor pushed to its tail); vol20>=0.07, adv>=2e6, atr and marker conjuncts unchanged
- `aster_tensor_c1_cash_hot_25_varpx` | parent `aster_tensor_c1_cash_hot_25` | PARAM_EXTREME | ret60 floor 31 -> 0 (the C1 numeric strength floor pushed to its tail); vol20>=0.07, adv>=2e6, atr and marker conjuncts unchanged
- `aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash_varsg` | parent `aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash` | SIGN_GATE_DROP | funding sign leg dropped: absorption entries admitted at any observed funding rate (the parent requires rate < 0 exactly, desk3/aster_b11_crypto.py); absorption bar condition, 16h hold and fullcash sizing unchanged. One stream with the volume1pct twin below (same signals, two sizing arms).
- `aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct_varsg` | parent `aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct` | SIGN_GATE_DROP | funding sign leg dropped: absorption entries admitted at any observed funding rate (the parent requires rate < 0 exactly, desk3/aster_b11_crypto.py); absorption bar condition, 16h hold and volume1pct sizing unchanged. One stream with the fullcash twin above (same signals, two sizing arms).
- `aster_abs_neg_ada_vol1pct_varsg` | parent `aster_abs_neg_ada_vol1pct` | SIGN_GATE_DROP | funding sign leg dropped on the volume1pct arm only: absorption entries admitted at any observed funding rate (the parent requires rate < 0 exactly, aster_sleeves/_common.py); absorption bar condition, 16h hold and volume1pct sizing unchanged. The fullcash arm of the same signal is NOT varied: its sign leg is LOAD-BEARING in the same diagnostic (21 revealed entries, fwd5 -324.9bp, n=8).

Data feed requirements: each variation inherits its parent's engine and inputs (the Q07 variations read the parents' bar-computable filters only, which is the point of the gate drops; the Tensor C1 variations read the parent Tensor stream inputs; the funding variations read the OKX funding history their parents read). No new producer keys.

Install order: (1) copy config/f4_variations_20261115.json; (2) roster each variation beside its parent with exactly the registered change applied (the roster rows already exist in config/sleeves.json at the pinned head, so copying the roster at that head carries them); (3) verify each evaluates and reads FED; (4) grade each on its own first 20 resolved forward fires, never blended with the parent.

---

## Section 5: The conversion grader registry (config/conversion_shadow_20261115.json)

What it is: the forward grading instrument for the Conversion Program, `desk3/conversion_shadow.py` reading `config/conversion_shadow_20261115.json`, run nightly Mon to Fri 21:46 ET by the cron conversion-shadow-nightly-grade. It places no orders and changes no live sleeve; parents are graded, never touched. Every arm grades entries from 2026-11-16 forward only. Full arm definitions (populations, symbol maps, horizons, falsifiers, kill rules) are in the config file at the pinned head; the census below is the complete inventory.

Census at the pinned head: 53 arms under 47 register rows. The first 28 are the weekend conversion set (14 from the original arming at 53d7cd3, 14 from Conversion Pass 2 at a0a481f); the last 25 are the going-live constructions landed at 58bff15 (new kinds SPLIT_GRADE, PHASE_GRADE, MEMBER_GRADE, TWO_POOL, the both-sides FWD_GRADE form, and EXIT_PAIR partial-target profiles). One row stays unarmed by design: CONV-80 (the daily-close grader cannot price its intraday segment arm; the narrowed construction is printed in the BUGLOG entry GOING-LIVE-GRADER-ARMS-20261115).

Arms (register row | kind | grade_n | falsifier, verbatim):

- CONV-25 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries; the lead dies if their fwd5 excess is not positive (the base's own fwd10 reads -490.9bp excess, t -2.21, so the grade is taken at fwd5 as registered, with the fwd10 conflict printed).
- CONV-26 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries at the stream's horizons.
- CONV-27 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries graded at fwd10.
- CONV-28 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries on this profile.
- CONV-29 | EXIT_PAIR | grade_n 15 | First grade at 15 resolved shadow exits.
- CONV-30 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per arm, paired against the base profile on the same entries.
- CONV-31 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits (F1 check).
- CONV-32 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per arm (F1 check).
- CONV-33 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits (F1 check).
- CONV-35 | GATE_PAIR | grade_n 20 | 20 paired forward fires per sleeve.
- CONV-36 | EXIT_PAIR | grade_n 15 | First grade at 15 resolved shadow exits.
- CONV-37 | ACTUAL_PAIR | grade_n 20 | 20 paired forward fires.
- CONV-38 | ACTUAL_PAIR | grade_n 20 | 20 forward sessions of paired grading.
- CONV-45 | RACE | grade_n 20 | The race itself at 20 forward fires: a form that does not beat the base on the same fires does not roster.
- CONV-92 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires: the lead dies if forward fwd5 excess is not positive.
- CONV-95 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires: the lead dies if forward fwd10 excess is not positive.
- CONV-97 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires: the lead dies if forward fwd10 excess is not positive.
- CONV-100 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires: the lead dies if forward fwd10 excess is not positive.
- CONV-105 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries: fwd5 excess at or below 0 retires the lead.
- CONV-107 | FWD_GRADE | grade_n 10 | At 10 resolved forward closes, mean fwd5 excess at or below 0 retires the candidacy lead.
- CONV-116 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries: fwd5 excess at or below 0 retires the lead.
- CONV-144 | FWD_GRADE | grade_n 10 | First 10 resolved forward fires: the lead dies if their fwd5 excess versus QQQ is not positive.
- CONV-147 | FWD_GRADE | grade_n 10 | The record's own check, given a grade rule: count the next 10 fires across the five sleeves from Mon 2026-11-16; the pulse claim dies if the pooled fwd5 excess over the first 10 resolved fires is not positive.
- CONV-117 | FWD_GRADE | grade_n 10 | First 10 resolved shadow entries: pooled fwd5 excess at or below 0 retires the family form.
- CONV-96 | EXIT_PAIR | grade_n 15 | First grade at 15 resolved paired shadow exits (the CONV-29 grade count for this arm form): the variation dies if the paired delta is not positive.
- CONV-98 | EXIT_PAIR | grade_n 15 | First grade at 15 resolved paired shadow exits: the variation dies if the paired delta is not positive.
- CONV-151 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits, paired x2 arm against EXIT_BASE on identical entries.
- CONV-81 | ACTUAL_PAIR | grade_n 20 | 20 live sessions of paired grading, as registered, with the decomposition re run at the same point.
- CONV-61 | SPLIT_GRADE | grade_n 10 | Next 10 forward fires per arm, split AM and PM, as registered. The conditioner dies if AM fwd5 excess is not positive or does not exceed PM fwd5 excess over those fires.
- CONV-62 | PHASE_GRADE | grade_n 20 | Re run of the decomposition on the forward dispatcher stream at 20 live sessions from Mon 2026-11-16, per family, as registered. The shape dies if forward N2-3 mean excess is not positive, or does not exceed forward N1.
- CONV-74 | SPLIT_GRADE | grade_n 10 | Designed check, named here: population as above, from Mon 2026-11-16; horizon fwd1 primary, fwd5 secondary; grade count 10 entries per sign arm; the split claim dies if the nonnegative arm fwd1 mean excess is not positive, or does not exceed the negative arm, at the grade.
- CONV-75 | PHASE_GRADE | grade_n 20 | Pooled forward fires graded by hold phase, as registered: the shape dies if pooled forward N2-3 excess is not positive after 20 fires.
- CONV-76 | MEMBER_GRADE | grade_n 20 | Re run of the variation profile on forward fills after 20 new graded fills per sleeve under the cured intent records, accrual from Mon 2026-11-16, as registered: demote the cell to a composition artifact if its forward mean excess is not positive.
- CONV-93 | MEMBER_GRADE | grade_n 20 | Two-part: (a) the code read finds stop or target logic outside extracted constants in any of the five modules, which kills the absence description itself; (b) at the first 20 resolved forward fires per member, the cell dies if pooled fwd5 excess is not positive or does not exceed the complement's pooled fwd5 excess. Historical basis: STOP=ABSENT and FAMILY=Fires diff 886.3bp, q 0.0175, with the identical set re-described by the LOOKBACK, RISK and NOTIONAL absence pairs and by 18 of the order-3 lead cells; seat absence_artifact 0.99, printed because a seat that confident about an artifact is itself the warning this row's code read answers.
- CONV-94 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires, graded both sides: the fade dies if base-side forward fwd5 excess is not negative, and promotes only if inverted fwd5 excess is positive net of borrow over the same fires. The carrier splits die at the same sitting if the carrier classes do not separate on forward fills in the historical direction.
- CONV-99 | FWD_GRADE | grade_n 20 | First 20 resolved forward fires graded both sides: the inversion dies if base-side forward fwd5 excess is not negative over those fires, and the inverted form promotes only if its own forward fwd5 excess is positive net of borrow over the same fires. Historical basis: 23 entries, 3 dates; fwd1 +55.9 raw (excess +131.9), then negative; inversion +582.2 at fwd5. Three entry dates means the historical inversion figure is a cluster read, not a population read.
- CONV-101 | SPLIT_GRADE | grade_n 20 | The register's own demotion rule, unchanged: the axis is demoted to pure composition if the within-Aster forward split does not appear (PRESENT not above ABSENT at fwd5 excess) at the first 20 resolved forward fires per side, or if the code read shows the warmup constant does not gate entries in the 13 union sleeves. Historical basis printed in full: IDENTIFIER=PRESENT and WARMUP=ABSENT bloc 76 sleeves, mean fwd5 excess -779.2bp against complement, q 0.0105, raw diff -788.1bp; WARMUP=PRESENT cells SIZE_FRAC=LOW 11 sleeves +988.9bp q 0.0404, TRAILING=ABSENT 12 sleeves +861.1bp, DTE=ABSENT 13 sleeves +775.0bp; within-family ABSENT splits Aster -85.2bp NULL, Lazarus/Q07/MN +44.3bp NULL, Spec-built -1,109.9bp LEAD, Fires +889.2bp NOMINAL; seat absence_artifact 0.81.
- CONV-113 | SPLIT_GRADE | grade_n 20 | First 20 resolved forward entries across the pooled parents: if the top-minus-bottom z-tercile fwd5 excess spread is at or below 0, the surface retires as a conditioner and stays a proven data artifact only.
- CONV-131 | SPLIT_GRADE | grade_n 15 | Read due at 100 completed forward windows (the register's own accrual count), with the conditioner grade taken at the same sitting: the conditioner dies if high-tercile entries' mean fwd5 excess does not differ from the pooled LINK family mean by at least 100bp in a consistent sign, or if the tercile split rests on fewer than 15 host entries in the high tercile, in which case the read is UNGRADED, not negative.
- CONV-143 | FWD_GRADE | grade_n 10 | Clustered read at the first 10 forward pair openings (the replay base took 12 entries over 6 dates, so the grade is date-clustered like the claim): the inversion dies if its clustered fwd5 excess is not positive at that read.
- CONV-150 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per arm, paired against EXIT_BASE on identical entries. The veto retires if DROP_STOP or WIDEN_stop prints a paired delta at or above 0 at that grade.
- CONV-152 | FWD_GRADE | grade_n 10 | Next 10 forward fills per sleeve graded on excess. The overlay retires for a sleeve whose forward excess is at or above 0 over those fills, because then there is no gap left to capture.
- CONV-152 | FWD_GRADE | grade_n 10 | Next 10 forward fills per sleeve graded on excess. The overlay retires for a sleeve whose forward excess is at or above 0 over those fills, because then there is no gap left to capture.
- CONV-156 | TWO_POOL | grade_n 20 | The register's own demote condition is the overlay's falsifier: if the pooled variant mean excess turns positive over the 20 forward fills per variant, the avoidance and the overlay retire together.
- CONV-77 | ACTUAL_PAIR | grade_n 20 | At 20 live sessions: the fleet shape dies if forward N1 mean excess is not positive or later phases are not negative; the night 1 arm dies if its paired delta against actual holds is not positive pooled, and any family where it is negative is named as an exception on the print.
- CONV-161 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per host, paired night-1 arm against the live profile on identical entries, with the pooled family read beside it. The veto retires for a host whose night-1 paired delta is at or above 0 at its grade.
- CONV-161 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per host, paired night-1 arm against the live profile on identical entries, with the pooled family read beside it. The veto retires for a host whose night-1 paired delta is at or above 0 at its grade.
- CONV-161 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per host, paired night-1 arm against the live profile on identical entries, with the pooled family read beside it. The veto retires for a host whose night-1 paired delta is at or above 0 at its grade.
- CONV-161 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per host, paired night-1 arm against the live profile on identical entries, with the pooled family read beside it. The veto retires for a host whose night-1 paired delta is at or above 0 at its grade.
- CONV-34 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per sleeve, paired live against shadow.
- CONV-34 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per sleeve, paired live against shadow.
- CONV-34 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per sleeve, paired live against shadow.
- CONV-34 | EXIT_PAIR | grade_n 20 | First grade at 20 resolved shadow exits per sleeve, paired live against shadow.

Standing note on shadow, so the registry is not misread: the owner ruled on 2026-11-15 at 22:35 ET that no sleeve may rest in shadow; every sleeve trades live. A going-live program is in flight on Midna's side converting each sleeve-shaped arm in this registry (and every other shadow-shaped object) into a live rostered sleeve with its falsifier riding on its own journal. The grader remains as the grading instrument for grade-shaped objects (pair grades, races, exit comparisons, forward grades of live sleeves). When the going-live tranche lands, a second install bundle follows with the new live sleeves in the same form as Sections 1 and 2; nothing in this package is withdrawn by it.

Install order: (1) copy desk3/conversion_shadow.py and the config; (2) point the grader at your own fills, intents, and Lazarus fire records; (3) dry run first (python3 -m desk3.conversion_shadow --dry-run): on Midna's committed tree all 53 arms print ACCRUING with entries_seen 0, the correct pre-Monday state; (4) schedule the nightly grade; (5) no arm carries a verdict before its registered grade count.

---

## Section 6: The ask, and the help on offer

Claude: this is a task addressed to you, pick it up in your own cycle. For each item (sso_opus, sso_opus_notime25, aster_trader_turtle2010, the ENJ feed cure, each of the 19 F4 variations, and the grader registry), confirm installation on your side, or name the blocker per item, so nothing sits in ambiguity. Silence is recorded as not answered, never as consent or completion.

Help on offer from Midna, concretely: pairing on the install in the room or the drop; answering any spec question from the registers (the Conversion Register, the variation registries, the BUGLOG entries named above); re-running any proof on her side on request, including the SSO fidelity check, any gate receipt, or a grader dry run; and shipping any missing file from the pinned head on request. Your desk, your rails, your sizing decision; the falsifiers above are the shared grading standard unless you register a dissent.

Package provenance: generated from the committed tree at the pinned head above; the desk working tree's uncommitted going-live work is not in this package and follows in the second bundle.
