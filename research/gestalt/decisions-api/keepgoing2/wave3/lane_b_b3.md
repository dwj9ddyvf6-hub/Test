# Wave 3 Lane B3: Sleeve Demography, Lifetimes

Sources: wave2/birth_register_v1.json (339 rows), wave2/death_register_v1.json (61 rows), wave2/attribution_ledger_v1_1.json (339 per-sleeve rows, 8,928 source fills), all as of 2026-11-14. Machine record with the full merged lifetime table (all 339 sleeves) in lane_b_b3.json.

## Lifetime distribution

Sessions alive (register sessions field): min 0, median 13, p75 14, max 14, mean 11.54.

| Lifetime bucket | Sleeves |
|---|---|
| 0 sessions | 26 |
| 1 to 9 sessions | 38 |
| 10 to 14 sessions | 275 |
| 15 to 19 | 0 |
| 20+ | 0 |

Cohorts by first_seen_date: 2026-10-23 founding cohort 135, 2026-10-24 cohort 107, then a long tail (2026-10-27: 21, 2026-11-02: 16, 2026-11-03: 11, others 1 to 9 each), and 26 sleeves with first_seen_date UNKNOWN (the same 26 at 0 sessions). Klass distribution: NOT FIRED 223, PARKED 54, LOW SAMPLE 62.

The fleet is 14 sessions old at its oldest. Lifetime here is fleet age, not longevity in any mature sense.

## Deaths

Death register: 61 rows, formal_deaths 0, formal_death true for 0 rows. No sleeve carries a DSR, forward Sharpe CI, or mechanism invalidation record, so nothing in the fleet has formally died; the register records park and block states. Criteria: D1_PARKED only 52, D2_CEASED_FIRING_IN_WINDOW only 7, both 2. Cause or blocker text (board trigger_or_blocker verbatim, the closest cause text on record): "Outside state: underlying does not trade on this door" 28 rows; "Fed 2026-11-14; evaluates on the real served product" 17; "Submitted or filled in the last 10 trading sessions" 6; "Parked by design / ruling" 5; the remaining 5 rows carry Tensor serve-shape, fixture-proven, and two SOLVE-IN-FLIGHT texts at 1 to 2 rows each. Full text in the JSON.

## Lifetime expectancy table (the only sleeves with own closes)

Attribution totals: 3 of 339 sleeves have any own closes; 13 per-close rows; total realized $5,850.22 on $2,967,192 allocated. Clean verdict-grade sleeves: 0.

| Sleeve | Sessions | Own closes | Realized USD | Expectancy USD per close | Win rate |
|---|---|---|---|---|---|
| aster_trader_donchian55 | 12 | 8 | 5,489.35 | 686.17 | 1.00 |
| bta_onebar_rth | 8 | 3 | 661.36 | 220.45 | 1.00 |
| bta_onebar_qqq | 8 | 2 | -300.49 | -150.25 | 0.00 |

Every other sleeve: own closes 0, realized $0, expectancy null. Full per-sleeve table in the JSON.

## Does lifetime predict anything?

Tested three ways, counts printed in the JSON:

- Sessions at or above the median (13): 242 sleeves, 0 with own closes, close rate 0.0000, realized $0. Below median: 97 sleeves, 3 with own closes, close rate 0.0309, realized $5,850.22.
- Sessions at the maximum (14, the founding cohort): 135 sleeves, 0 with own closes. The rest: 204 sleeves, close rate 0.0147.
- Sessions 60 or more (the territory's example threshold): 0 sleeves. The cohort does not exist; the fleet maximum is 14 sessions.

Claim supported by the counts, and only this: no positive lifetime effect exists in this data. All realized closes sit in shorter-session sleeves, which is what a 14-session-old fleet with 13 total closes would produce under almost any assignment; with 3 closing sleeves out of 339, no lifetime-predicts-performance claim in either direction survives the counts. The honest one-level-up statement is demographic, not predictive: the fleet is a young, mostly never-fired population (223 of 339 NOT FIRED) whose death register is a park register, and expectancy is currently a 3-sleeve fact, not a fleet property.

STATUS: GREEN for the demography as scoped (all three registers recounted and merged, table printed in the JSON). Evidence pointer: lane_b_b3.json in this folder.
