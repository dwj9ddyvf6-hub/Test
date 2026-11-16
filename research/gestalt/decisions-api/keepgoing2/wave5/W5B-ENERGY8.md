# W5B. ENERGY8 SUB-BASKET TRADABLE FORM (Wave 5, Lane B, 2026-11-14)

SCOPE: the ON_energy8 sub-basket (FLNC, EOSE, FCEL, BE, OKLO, VST, CEG, XLE) given the full Wave 4 V1 treatment: measured friction on its own names, its honest pre-registered family position, a wired forward accrual mirroring focus29's falsifier, and one advisory typed seat. Paper and shadow only. No desk tree edits, no wave4 file edits, no production ledger written tonight. Every number below recounts from the artifact named beside it.

## VERDICT

**Energy8 is tradeable in exactly one form, the auction form, and more extremely so than focus29.** Equal-weight gross +21.12bp per night; net at crossing **-49.24bp** (focus29: -27.17bp); net at auction **+18.13bp** (focus29: +19.53bp). Its crossing carry subset is **empty: zero of eight names are net positive at crossing**, where focus29 had five carry names. A marketable-order implementation of this basket is not a degraded version of the find; it is a different, losing trade. The operating rule from Wave 4 applies with more force here: any name whose auction access fails on a given night is dropped that night, never crossed.

## 1. FRICTION, FULL V1 TREATMENT (w5b_energy8_friction.json)

Method: identical formulas to keepgoing2/wave4/v1_friction2.py, recomputed from the held raw crawl (wave4/v1_friction_raw.json, SIP quotes and prints, 10 sessions 2026-11-02 to 2026-11-13). No fresh crawl was needed or made: the held raw holds complete open and close quotes and prints for all 8 names on all 10 sessions (no null legs, verified in the compute script by assertion). The compute script (w5b_energy8_friction.py) asserts its recomputed medians match wave4/v1_friction.json to 1e-9 for all 8 names, so these are the same measurements, subset, not new ones. Gross per name is the full-history overnight mean from wave3/focus_bars.json via the Wave 4 artifact.

| Name | Gross/night | Crossing RT (median) | Net at crossing | Auction RT (median, signed) | Net at auction |
|---|---|---|---|---|---|
| FLNC | +20.78bp | 82.64bp | -61.86bp | +38.35bp | -17.57bp |
| EOSE | +29.97bp | 82.61bp | -52.64bp | -50.58bp | +80.55bp |
| FCEL | +42.03bp | 107.15bp | -65.12bp | +28.66bp | +13.37bp |
| BE | +22.97bp | 43.85bp | -20.88bp | -5.95bp | +28.92bp |
| OKLO | +20.84bp | 65.83bp | -44.99bp | +9.66bp | +11.18bp |
| VST | +10.46bp | 109.78bp | -99.32bp | -5.82bp | +16.28bp |
| CEG | +16.62bp | 64.95bp | -48.34bp | +10.27bp | +6.35bp |
| XLE | +5.33bp | 6.12bp | -0.80bp | -0.64bp | +5.97bp |
| **Basket, equal weight** | **+21.12bp** | **mean 70.37bp, median name 74.22bp** | **-49.24bp** | **basket cost +2.99bp** | **+18.13bp** |

Basket gross notes, both bases on the record as in Wave 4: +21.12bp is the mean of the 8 per-name full-history means (the basis the friction nets use); the family exam's own basket series prints +21.36bp per night (mean_daily 0.002136) over its 2,088 formed sessions.

**CARRY subset at crossing: none.** All eight names classify FRICTION-DEAD at crossing; the closest is XLE at -0.80bp, and there is not even a marginal name. This is the sharpest split from focus29, whose five crossing survivors (SNDK, CRWV, RKLB, NVDA, AMD) are all outside this sub-basket.

**Auction-form carry set: 7 of 8, indicative only.** At per-name auction medians, EOSE, FCEL, BE, OKLO, VST, CEG and XLE are net positive and FLNC alone is negative (-17.57bp). The standing caveat governs this set in full: per-name auction medians on these wide names are mid-reference noise (EOSE's +80.55bp net rests on a -50.58bp signed median, prints landing inside a very wide spread), so the set is reported as measured, never as a tradable name list. Only the basket-level auction figure (+2.99bp cost, +18.13bp net) is cited as a cost.

**FCEL auction prints, specifically measured** (fcel_auction_detail in w5b_energy8_friction.json): auction signed cost median **+28.66bp over n = 10 sessions**, against a crossing median of 107.15bp. Per-session signed values run from -63.43bp to +93.87bp, positive (a cost) in 6 of 10 sessions. Spread context: FCEL's median quoted full spread at the open over these sessions is 187.05bp (range 127.26bp to 322.11bp) and 28.00bp at the close, so the bracketing mid the signed cost is measured against sits inside a spread several times the cost itself. Reading: FCEL is crossing-dead at 107bp and its auction median, taken alone, would leave it net positive (+13.37bp), but that median is the noisiest single number in this lane's table; the forward accrual, which grades the basket from the bar auction prints session by session, is the cure, and no FCEL-specific claim is made from these 10 sessions.

## 2. COUNT (verified from wave4/v2_family_exam.json)

Energy8's pre-registered position, stated honestly: **ON_energy8 is 1 of 42 variants in the overnight family matrix, at the family's combined trial count of 45** (42 matrix variants plus dive three's 3 off-matrix trials). At that count its recorded values are **DSR 0.99994 (0.9999 rounded), Sharpe 1.79, t 5.32, mean +0.214% per night**, inside a family graded PROMOTE (PBO 0.000, SPA 0.000 vs SPY and 0.001 vs QQQ, 2,229 sessions, energy8 formed on 2,088 of them). No smaller family is invented for it in this record. This tradable-form study adds no new selection: the member was chosen by the family exam, its names and its count were fixed there, and the friction and accrual work here only asks how that already-selected member could be traded and forward-graded.

## 3. FORWARD ACCRUAL, WIRED AND PROVEN (w5b_energy8_accrual.py)

Clone of wave4/v1_shadow_accrual.py with only the forced adaptations, each named in the script header: basket is the 8 energy names; ledger is keepgoing2/wave5/on_energy8_shadow.jsonl; every record carries "basket": "ON_energy8" beside the same fields as focus29's records (date, names, gross_bp, net5_bp, crossing_cost_bp, net_crossing_bp, auction_cost_bp, net_auction_bp); friction legs are read at runtime from w5b_energy8_friction.json, which is written in the same schema shape as v1_friction.json, so the measured_costs reader logic carries over unchanged apart from the name list (crossing leg +70.367bp, auction leg +2.994bp); a session records only with at least 6 of 8 names present (the focus29 floor of 10 of 29, tightened proportionally for an 8-name basket); ANCHOR 2026-11-13; same 60-session discipline from Mon 2026-11-16 and the same verdict line (SURVIVES if mean net of 5bp is positive at 60 sessions, DEMOTED otherwise).

Proof, from a scratch dry run tonight (anchor shifted to 2026-11-12 via the script's W5B_ANCHOR and W5B_LEDGER overrides, scratch ledger w5b_scratch_shadow.jsonl in wave5/): one row appended for Fri 2026-11-13, `{"basket": "ON_energy8", "date": "2026-11-13", "names": 8, "gross_bp": 72.54, "net5_bp": 67.54, "crossing_cost_bp": 70.367, "net_crossing_bp": 2.173, "auction_cost_bp": 2.994, "net_auction_bp": 69.547}`; a second run appended 0 (idempotent). That row is a wiring proof on a historical session, not a forward session, and it grades nothing. **The production ledger on_energy8_shadow.jsonl was not written tonight** (verified absent after the dry run).

**Cron arming spec for the parent to arm and read back (NOT armed by this lane):**
- Proposed id: `on-energy8-shadow-accrual`
- Schedule: weekdays 09:46 ET (mirroring on-focus29-shadow-accrual)
- Command: `python3 ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave5/w5b_energy8_accrual.py`
- First production record would be session 1 (Fri 2026-11-13 close to Mon 2026-11-16 open), recorded Mon 2026-11-16.

## 4. TYPED SEAT (w5b_typed_seat.json, advisory only)

One request through ~/workspace/midna-book/typed-layer/decisions_harness.py (bank id w5b-energy8-tradable-form, version 1), pack carrying the measured numbers for both baskets. Question: peer standing with its own parallel falsifier, or weaker sibling riding focus29's falsifier only. **The seat chose stands_beside at 0.77 against weaker_sibling at 0.23**, and put 0.60 probability on energy8's basket-level auction net staying positive over a 60-session forward window. Advisory only; the accrual above is wired regardless of the seat, and the seat gates nothing. Spend: **1 request, 862 input tokens, $0.000086**.

## ARTIFACTS

- Friction artifact: keepgoing2/wave5/w5b_energy8_friction.json (compute script w5b_energy8_friction.py)
- Accrual script: keepgoing2/wave5/w5b_energy8_accrual.py
- Dry-run ledger: keepgoing2/wave5/w5b_scratch_shadow.jsonl (1 row, 2026-11-13, wiring proof only)
- Typed seat record: keepgoing2/wave5/w5b_typed_seat.json (script w5b_typed_seat.py)
- Production ledger (not yet created, by design): keepgoing2/wave5/on_energy8_shadow.jsonl

## SUMMARY FOR THE WAVE REPORT

ON_energy8, the family exam's strongest basket member after focus29 (DSR 0.99994 at the combined count of 45, 1 of 42 variants, no new selection made here), is tradeable only in its auction form and has no crossing fallback at all: measured on the same 10 sessions and the same V1 method as focus29, its equal-weight gross is +21.12bp per night, its net at crossing is -49.24bp with an empty carry subset (zero of eight names net positive at crossing, XLE closest at -0.80bp), and its basket-level net at auction is +18.13bp against a +2.99bp signed cost, with FCEL's specifically measured auction prints printing a +28.66bp median signed cost on n = 10 inside a median 187bp opening spread, a number reported with its noise context and not as a per-name claim. Its forward falsifier is wired as a clone of focus29's accrual (ledger on_energy8_shadow.jsonl, anchor 2026-11-13, 60 sessions from Mon 2026-11-16, demoted if mean net of 5bp is not positive), proven by a scratch dry run that produced the Fri 2026-11-13 row shape and appended nothing on re-run, with the production ledger untouched and the cron spec (on-energy8-shadow-accrual, weekdays 09:46 ET) left for the parent to arm and read back; a typed seat, advisory only, backed peer standing with its own parallel falsifier at 0.77 for $0.000086.

STATUS: PARTIAL (friction, count and typed seat proven on their artifacts; accrual wiring proven on the scratch ledger; the production cron is unarmed and the production ledger unwritten, both named above for the parent). EVIDENCE POINTER: keepgoing2/wave5/w5b_energy8_friction.json, keepgoing2/wave5/w5b_scratch_shadow.jsonl, keepgoing2/wave5/w5b_typed_seat.json.
