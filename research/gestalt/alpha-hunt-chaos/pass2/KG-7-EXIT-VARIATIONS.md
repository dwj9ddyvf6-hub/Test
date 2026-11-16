# KG-7: EXIT-PROFILE VARIATION ACROSS ALL FAMILIES

Coverage, counted on the final artifacts: 57 sleeves (the full union of Unblock Lane 2's REPLAY-SCORED and REPLAY-INDICATIVE tiers) over 37 distinct entry streams (mirror sizing variants share streams and are flagged per row), 285 sleeve-variation rows in KG-7-REGISTER.jsonl (197 GRADED, 88 NOT_APPLICABLE with the reason printed in the row) plus 5 family night-1 check rows. Every row carries evidence class REPLAY. Bases: 23 sleeves on their REGISTERED Lane C exit params, 34 on the stated DEFAULT_HOLD10 base (no stop, no target, 10 sessions) because their maps carry no exit params at all. All grading reuses Unblock-2's machinery (close-based path sim on stored daily closes, 6bp exit cost, paired per-trade deltas vs base). Seat lens: 8 objects, 72 questions, bank kg7-exit-variations v1.0; seats set no grades.

## POTENTIAL EDGE FOUND

Every sleeve-variation row moving mean outcome by more than +200bp per trade with n >= 15 paired trades: 17 rows over 9 distinct streams. Each lead prints its base convention, because half of them are measured against the DEFAULT_HOLD10 base, not a registered exit.

### Stop loosening (the F1 generalization)

- 1w (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1725.0bp -> 3148.0bp, paired delta 1423.0bp (n=28, t=1.37)
- 1w (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1725.0bp -> 2937.8bp, paired delta 1212.8bp (n=28, t=1.12)
- 1wa (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1256.3bp -> 2285.5bp, paired delta 1029.1bp (n=34, t=1.13)
- 1wa (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1256.3bp -> 2277.4bp, paired delta 1021.0bp (n=34, t=1.18)
- s_1wlab (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=126): base 587.6bp -> 1263.9bp, paired delta 676.4bp (n=80, t=1.91)
- s_1wlab (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=126): base 587.6bp -> 1241.7bp, paired delta 654.1bp (n=80, t=1.87)

Cheapest forward check: run the dropped/widened stop as a shadow exit arm beside the registered profile on Monday's Lazarus fire stream; first grade at 20 resolved shadow exits per sleeve. Counterweight in the same test set: 1d, the fourth stop-carrying sleeve at n >= 15, gets worse when its stop is dropped (+267.0bp -> +53.8bp, delta -213.3, n=56, t=-2.2); its base carries the family's only +20% partial target, so the stop and the partial work as a pair there.

### Horizon extension

- aster_abs_link_4h (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -260.8bp -> 422.1bp, paired delta 682.9bp (n=18, t=1.78) [mirror of aster_r19_linkusdt_absorption_base_fixed16_fullcash, aster_r19_linkusdt_absorption_base_fixed16_volume1pct]
- aster_r19_linkusdt_absorption_base_fixed16_fullcash (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -260.8bp -> 422.1bp, paired delta 682.9bp (n=18, t=1.78) [mirror of aster_abs_link_4h, aster_r19_linkusdt_absorption_base_fixed16_volume1pct]
- aster_r19_linkusdt_absorption_base_fixed16_volume1pct (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -260.8bp -> 422.1bp, paired delta 682.9bp (n=18, t=1.78) [mirror of aster_abs_link_4h, aster_r19_linkusdt_absorption_base_fixed16_fullcash]
- s_rules_1w (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=27): base 365.2bp -> 862.9bp, paired delta 497.7bp (n=58, t=2.28)
- s_mn_kronos (Lazarus/Q07/MN, DEFAULT_HOLD10 base stop=None target=None h=10): base 174.9bp -> 551.5bp, paired delta 376.6bp (n=26, t=1.53)
- aster_breakout_ada_fullcash (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -497.3bp -> -124.7bp, paired delta 372.6bp (n=32, t=2.11) [mirror of aster_breakout_ada_vol1pct]
- aster_breakout_ada_vol1pct (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -497.3bp -> -124.7bp, paired delta 372.6bp (n=32, t=2.11) [mirror of aster_breakout_ada_fullcash]
- phase_daily (Fires and singles, DEFAULT_HOLD10 base stop=None target=None h=10): base 128.2bp -> 496.2bp, paired delta 368.1bp (n=34, t=2.52)

Cheapest forward check: shadow the x2 horizon on the LINK absorption and ADA streams (both run on live PF tapes) and on s_rules_1w's fire stream; first grade at 15 resolved shadow exits. Counterweight: 1dc extended x2 is the strongest negative statistic in the run (delta -604.3bp, n=280, t=-4.06); horizon extension is sleeve-specific, never family-wide.

### Night-1-only (against the KG-4 prediction, see the check below)

- aster_breakout_ada_fullcash (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -497.3bp -> 23.9bp, paired delta 521.2bp (n=32, t=3.73) [mirror of aster_breakout_ada_vol1pct]
- aster_breakout_ada_vol1pct (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -497.3bp -> 23.9bp, paired delta 521.2bp (n=32, t=3.73) [mirror of aster_breakout_ada_fullcash]
- aster_etf_qqq_qld_monthly (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base -450.3bp -> 36.2bp, paired delta 486.5bp (n=15, t=3.45)

Both night-1 movers are Aster sleeves on DEFAULT_HOLD10 bases: what they prove is that the accidental 10-session default is the wrong hold for those two streams, not that night-1 exits are a family rule. Cheapest forward check: register a night-1 exit arm on the ADA breakout stream's live PF tape; first grade at 15 resolved entries.

## THE KG-4 PREDICTION CHECK (printed in full, misses included)

KG-4's hold-phase decomposition of the desk's LIVE dispatcher record predicted: night-1-only exits HELP the night-1-shaped families (Tensor, Lazarus/Q07/MN) and HURT the late-shaped families (Aster, Fires and singles). KG-7 tested the actual exit rule on the replay streams. Family pooled paired deltas (night-1-only vs base):

| Family | KG-4 shape | Prediction | Pooled night-1 delta | n | t | Sleeve signs (+/-/0) | Verdict |
|---|---|---|---|---|---|---|---|
| Aster | LATE | HURT | 44.3bp | 427 | 1.04 | 12/5/0 | MISS |
| Fires and singles | LATE | HURT | 13.2bp | 83 | 0.17 | 2/1/0 | MISS |
| Lazarus/Q07/MN | NIGHT1 | HELP | -176.6bp | 1231 | -2.18 | 4/27/0 | MISS |
| Spec-built | UNCLASSIFIED | NONE | -111.6bp | 1 | None | 0/1/0 | NO PREDICTION |
| Tensor | NIGHT1 | HELP | 2688.9bp | 5 | 3.21 | 4/1/0 | MATCH |

Read plainly: the prediction is confirmed in 1 of the 4 classified families, and that one (Tensor) rests on 5 paired trades from 5 single-entry sleeves, which cannot carry a confirmation. Lazarus, the family with the deepest n, misses in the opposite direction (pooled -176.6bp, t=-2.18): the miss is concentrated in the long-horizon registered sleeves (1w h=252 delta -1666.5 n=28; 1wa h=252 -1237.2 n=34; s_1wlab h=126 -558.9 n=80; 1d h=40 -312.2 n=56), while the horizon-only Lazarus sleeves sit near flat (s_rules_1d -44.5 n=415; 1dc +32.4 n=280; s_1dg +26.9 n=204). Aster and Fires miss by sign on pooled deltas that are statistically null (t=1.04 and t=0.17), and two Aster streams are strongly night-1-positive against their family prediction. Interpretation, labeled as such: KG-4's phases are mark-to-market marks on a different population (the live record), and a base exit already traverses the earning phase; the marginal value of an exit rule lives in the tail paths (target partials, recoveries, post-horizon decay), which phase means do not measure. Phase shape is therefore not a usable exit-design input on this record. What IS load-bearing in this run: the registered horizon of 1dc (extension destroys -604.3bp at t=-4.06) and the registered stops of 1w/1wa/s_1wlab (loosening adds +654 to +1423bp).

## NEGATIVE MOVERS (avoidance side, delta < -200bp, n >= 15)

- 1w (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1725.0bp -> 58.5bp, paired delta -1666.5bp (n=28, t=-1.59) - NIGHT1_ONLY
- 1wa (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=252): base 1256.3bp -> 19.1bp, paired delta -1237.2bp (n=34, t=-1.4) - NIGHT1_ONLY
- 1dc (Lazarus/Q07/MN, REGISTERED base stop=None target=None h=21): base -13.8bp -> -618.1bp, paired delta -604.3bp (n=280, t=-4.06) - EXTEND_HORIZON_X2
- s_1wlab (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=None h=126): base 587.6bp -> 28.7bp, paired delta -558.9bp (n=80, t=-1.11) - NIGHT1_ONLY
- 1d (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=0.2 h=40): base 267.0bp -> -45.2bp, paired delta -312.2bp (n=56, t=-1.83) - NIGHT1_ONLY
- aster_pub_link_ai_volume (Aster, DEFAULT_HOLD10 base stop=None target=None h=10): base 283.7bp -> 27.0bp, paired delta -256.7bp (n=37, t=-1.33) - NIGHT1_ONLY
- 1d (Lazarus/Q07/MN, REGISTERED base stop=0.15 target=0.2 h=40): base 267.0bp -> 53.8bp, paired delta -213.3bp (n=56, t=-2.2) - DROP_STOP

## FULL SLEEVE TABLE (base and every variation, sleeves with any paired n >= 15 first)

### s_rules_1d (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=None target=None h=22)
- EXIT_BASE: mean 67.8bp (n=415, t=0.82, win 51.1%, exits {'horizon': 415})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -2.1bp (n=415), paired delta -69.9bp (n=415, t=-0.78), exits {'horizon': 415}
- NIGHT1_ONLY: mean 23.3bp (n=415), paired delta -44.5bp (n=415, t=-0.58), exits {'horizon': 415}

### 1dc (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=None target=None h=21)
- EXIT_BASE: mean -13.8bp (n=280, t=-0.06, win 44.3%, exits {'horizon': 280})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -618.1bp (n=280), paired delta -604.3bp (n=280, t=-4.06), exits {'horizon': 280}
- NIGHT1_ONLY: mean 18.7bp (n=280), paired delta 32.4bp (n=280, t=0.14), exits {'horizon': 280}

### s_1dg (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=None target=None h=21)
- EXIT_BASE: mean -18.1bp (n=204, t=-0.17, win 46.1%, exits {'horizon': 204})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 141.4bp (n=204), paired delta 159.5bp (n=204, t=1.65), exits {'horizon': 204}
- NIGHT1_ONLY: mean 8.8bp (n=204), paired delta 26.9bp (n=204, t=0.26), exits {'horizon': 204}

### aster_etf_leader1_c098 (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 102.8bp (n=122, t=2.94, win 54.1%, exits {'horizon': 122})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 229.5bp (n=122), paired delta 126.7bp (n=122, t=3.53), exits {'horizon': 122}
- NIGHT1_ONLY: mean 8.7bp (n=122), paired delta -94.2bp (n=122, t=-2.86), exits {'horizon': 122}

### s_1wlab (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=0.15 target=None h=126)
- EXIT_BASE: mean 587.6bp (n=80, t=1.16, win 38.8%, exits {'horizon': 39, 'stop': 41})
- DROP_STOP: mean 1263.9bp (n=80), paired delta 676.4bp (n=80, t=1.91), exits {'horizon': 80}
- WIDEN_STOP_X2: mean 1241.7bp (n=80), paired delta 654.1bp (n=80, t=1.87), exits {'horizon': 66, 'stop': 14}
- EXTEND_HORIZON_X2: mean 481.3bp (n=80), paired delta -106.3bp (n=80, t=-0.73), exits {'horizon': 39, 'stop': 41}
- NIGHT1_ONLY: mean 28.7bp (n=80), paired delta -558.9bp (n=80, t=-1.11), exits {'horizon': 80}

### s_rules_1w (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=0.15 target=None h=27)
- EXIT_BASE: mean 365.2bp (n=58, t=1.67, win 53.4%, exits {'horizon': 49, 'stop': 9})
- DROP_STOP: mean 285.4bp (n=58), paired delta -79.8bp (n=58, t=-1.68), exits {'horizon': 58}
- WIDEN_STOP_X2: mean 279.1bp (n=58), paired delta -86.1bp (n=58, t=-1.78), exits {'horizon': 56, 'stop': 2}
- EXTEND_HORIZON_X2: mean 862.9bp (n=58), paired delta 497.7bp (n=58, t=2.28), exits {'horizon': 45, 'stop': 13}
- NIGHT1_ONLY: mean 169.6bp (n=58), paired delta -195.7bp (n=58, t=-0.87), exits {'horizon': 58}

### 1d (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=0.15 target=0.2 h=40)
- EXIT_BASE: mean 267.0bp (n=56, t=1.43, win 57.1%, exits {'horizon': 25, 'target': 15, 'stop': 16})
- DROP_STOP: mean 53.8bp (n=56), paired delta -213.3bp (n=56, t=-2.2), exits {'horizon': 41, 'target': 15}
- WIDEN_STOP_X2: mean 103.3bp (n=56), paired delta -163.7bp (n=56, t=-2.27), exits {'horizon': 35, 'target': 15, 'stop': 6}
- EXTEND_HORIZON_X2: mean 416.1bp (n=56), paired delta 149.0bp (n=56, t=1.94), exits {'horizon': 16, 'target': 22, 'stop': 18}
- NIGHT1_ONLY: mean -45.2bp (n=56), paired delta -312.2bp (n=56, t=-1.83), exits {'horizon': 56}

### aster_r19_linkusdt_breakout_base_fixed16_fullcash (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_r19_linkusdt_breakout_base_fixed16_volume1pct)
- EXIT_BASE: mean 124.1bp (n=50, t=0.74, win 40.0%, exits {'horizon': 50})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 130.6bp (n=50), paired delta 6.5bp (n=50, t=0.05), exits {'horizon': 50}
- NIGHT1_ONLY: mean -70.1bp (n=50), paired delta -194.2bp (n=50, t=-1.33), exits {'horizon': 50}

### aster_r19_linkusdt_breakout_base_fixed16_volume1pct (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_r19_linkusdt_breakout_base_fixed16_fullcash)
- EXIT_BASE: mean 124.1bp (n=50, t=0.74, win 40.0%, exits {'horizon': 50})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 130.6bp (n=50), paired delta 6.5bp (n=50, t=0.05), exits {'horizon': 50}
- NIGHT1_ONLY: mean -70.1bp (n=50), paired delta -194.2bp (n=50, t=-1.33), exits {'horizon': 50}

### momentum_rotation (Fires and singles, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 27.7bp (n=48, t=0.25, win 64.6%, exits {'horizon': 48})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 56.0bp (n=48), paired delta 28.3bp (n=48, t=0.38), exits {'horizon': 48}
- NIGHT1_ONLY: mean 44.4bp (n=48), paired delta 16.7bp (n=48, t=0.21), exits {'horizon': 48}

### aster_pub_link_ai_volume (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 283.7bp (n=37, t=1.38, win 51.4%, exits {'horizon': 37})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 382.6bp (n=37), paired delta 98.9bp (n=37, t=0.58), exits {'horizon': 37}
- NIGHT1_ONLY: mean 27.0bp (n=37), paired delta -256.7bp (n=37, t=-1.33), exits {'horizon': 37}

### 1wa (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 1256.3bp (n=34, t=1.42, win 44.1%, exits {'horizon': 17, 'stop': 17})
- DROP_STOP: mean 2285.5bp (n=34), paired delta 1029.1bp (n=34, t=1.13), exits {'horizon': 34}
- WIDEN_STOP_X2: mean 2277.4bp (n=34), paired delta 1021.0bp (n=34, t=1.18), exits {'horizon': 25, 'stop': 9}
- EXTEND_HORIZON_X2: mean 1233.1bp (n=34), paired delta -23.2bp (n=34, t=-1.14), exits {'horizon': 16, 'stop': 18}
- NIGHT1_ONLY: mean 19.1bp (n=34), paired delta -1237.2bp (n=34, t=-1.4), exits {'horizon': 34}

### phase_daily (Fires and singles, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 128.2bp (n=34, t=1.18, win 58.8%, exits {'horizon': 34})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 496.2bp (n=34), paired delta 368.1bp (n=34, t=2.52), exits {'horizon': 34}
- NIGHT1_ONLY: mean 31.6bp (n=34), paired delta -96.6bp (n=34, t=-0.91), exits {'horizon': 34}

### aster_breakout_ada_fullcash (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_breakout_ada_vol1pct)
- EXIT_BASE: mean -497.3bp (n=32, t=-3.18, win 28.1%, exits {'horizon': 32})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -124.7bp (n=32), paired delta 372.6bp (n=32, t=2.11), exits {'horizon': 32}
- NIGHT1_ONLY: mean 23.9bp (n=32), paired delta 521.2bp (n=32, t=3.73), exits {'horizon': 32}

### aster_breakout_ada_vol1pct (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_breakout_ada_fullcash)
- EXIT_BASE: mean -497.3bp (n=32, t=-3.18, win 28.1%, exits {'horizon': 32})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -124.7bp (n=32), paired delta 372.6bp (n=32, t=2.11), exits {'horizon': 32}
- NIGHT1_ONLY: mean 23.9bp (n=32), paired delta 521.2bp (n=32, t=3.73), exits {'horizon': 32}

### 1w (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 1725.0bp (n=28, t=1.65, win 50.0%, exits {'horizon': 15, 'stop': 13})
- DROP_STOP: mean 2937.8bp (n=28), paired delta 1212.8bp (n=28, t=1.12), exits {'horizon': 28}
- WIDEN_STOP_X2: mean 3148.0bp (n=28), paired delta 1423.0bp (n=28, t=1.37), exits {'horizon': 22, 'stop': 6}
- EXTEND_HORIZON_X2: mean 1699.2bp (n=28), paired delta -25.8bp (n=28, t=-1.05), exits {'horizon': 15, 'stop': 13}
- NIGHT1_ONLY: mean 58.5bp (n=28), paired delta -1666.5bp (n=28, t=-1.59), exits {'horizon': 28}

### s_mn_kronos (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 174.9bp (n=26, t=0.77, win 57.7%, exits {'horizon': 26})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 551.5bp (n=26), paired delta 376.6bp (n=26, t=1.53), exits {'horizon': 26}
- NIGHT1_ONLY: mean 22.3bp (n=26), paired delta -152.6bp (n=26, t=-0.67), exits {'horizon': 26}

### aster_abs_link_4h (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_r19_linkusdt_absorption_base_fixed16_fullcash, aster_r19_linkusdt_absorption_base_fixed16_volume1pct)
- EXIT_BASE: mean -260.8bp (n=18, t=-0.97, win 50.0%, exits {'horizon': 18})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 422.1bp (n=18), paired delta 682.9bp (n=18, t=1.78), exits {'horizon': 18}
- NIGHT1_ONLY: mean -126.6bp (n=18), paired delta 134.2bp (n=18, t=0.52), exits {'horizon': 18}

### aster_r19_linkusdt_absorption_base_fixed16_fullcash (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_abs_link_4h, aster_r19_linkusdt_absorption_base_fixed16_volume1pct)
- EXIT_BASE: mean -260.8bp (n=18, t=-0.97, win 50.0%, exits {'horizon': 18})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 422.1bp (n=18), paired delta 682.9bp (n=18, t=1.78), exits {'horizon': 18}
- NIGHT1_ONLY: mean -126.6bp (n=18), paired delta 134.2bp (n=18, t=0.52), exits {'horizon': 18}

### aster_r19_linkusdt_absorption_base_fixed16_volume1pct (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_abs_link_4h, aster_r19_linkusdt_absorption_base_fixed16_fullcash)
- EXIT_BASE: mean -260.8bp (n=18, t=-0.97, win 50.0%, exits {'horizon': 18})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 422.1bp (n=18), paired delta 682.9bp (n=18, t=1.78), exits {'horizon': 18}
- NIGHT1_ONLY: mean -126.6bp (n=18), paired delta 134.2bp (n=18, t=0.52), exits {'horizon': 18}

### aster_etf_qqq_qld_monthly (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean -450.3bp (n=15, t=-2.99, win 26.7%, exits {'horizon': 15})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -533.7bp (n=15), paired delta -83.4bp (n=15, t=-0.55), exits {'horizon': 15}
- NIGHT1_ONLY: mean 36.2bp (n=15), paired delta 486.5bp (n=15, t=3.45), exits {'horizon': 15}

### aster_etf_qld_monthly (Aster, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean -500.2bp (n=12, t=-2.83, win 16.7%, exits {'horizon': 12})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -671.9bp (n=12), paired delta -171.7bp (n=12, t=-0.96), exits {'horizon': 12}
- NIGHT1_ONLY: mean 18.0bp (n=12), paired delta 518.2bp (n=12, t=3.11), exits {'horizon': 12}

### s_mn_pairs (Lazarus/Q07/MN, Unblock-2 REPLAY-SCORED, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 34.4bp (n=12, t=0.2, win 50.0%, exits {'horizon': 12})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 33.8bp (n=12), paired delta -0.6bp (n=12, t=-0.01), exits {'horizon': 12}
- NIGHT1_ONLY: mean 17.1bp (n=12), paired delta -17.3bp (n=12, t=-0.11), exits {'horizon': 12}

### aster_abs_base_ada_fullcash (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_abs_base_ada_vol1pct)
- EXIT_BASE: mean -488.0bp (n=9, t=-1.15, win 33.3%, exits {'horizon': 9})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -886.2bp (n=9), paired delta -398.2bp (n=9, t=-0.98), exits {'horizon': 9}
- NIGHT1_ONLY: mean -218.1bp (n=9), paired delta 269.9bp (n=9, t=0.81), exits {'horizon': 9}

### aster_abs_base_ada_vol1pct (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of aster_abs_base_ada_fullcash)
- EXIT_BASE: mean -488.0bp (n=9, t=-1.15, win 33.3%, exits {'horizon': 9})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -886.2bp (n=9), paired delta -398.2bp (n=9, t=-0.98), exits {'horizon': 9}
- NIGHT1_ONLY: mean -218.1bp (n=9), paired delta 269.9bp (n=9, t=0.81), exits {'horizon': 9}

### s_1wc_ml (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 4526.2bp (n=6, t=1.58, win 66.7%, exits {'horizon': 4, 'stop': 2})
- DROP_STOP: mean 7255.7bp (n=6), paired delta 2729.5bp (n=6, t=1.18), exits {'horizon': 6}
- WIDEN_STOP_X2: mean 7255.7bp (n=6), paired delta 2729.5bp (n=6, t=1.18), exits {'horizon': 6}
- EXTEND_HORIZON_X2: mean 4442.1bp (n=6), paired delta -84.1bp (n=6, t=-0.75), exits {'horizon': 4, 'stop': 2}
- NIGHT1_ONLY: mean 23.2bp (n=6), paired delta -4502.9bp (n=6, t=-1.62), exits {'horizon': 6}

### s_q07w_c78_ml_deep70_tierA_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_s52_ml_deep70_ins2_vix20, s_q07w_s78_ml_deep70_ins2_vix20)
- EXIT_BASE: mean 168.7bp (n=4, t=0.51, win 50.0%, exits {'horizon': 4})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 281.5bp (n=4), paired delta 112.8bp (n=4, t=0.12), exits {'horizon': 4}
- NIGHT1_ONLY: mean 65.2bp (n=4), paired delta -103.5bp (n=4, t=-0.23), exits {'horizon': 4}

### s_q07w_s52_ml_deep70_ins2_vix20 (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base REGISTERED stop=0.15 target=None h=20, mirror of s_q07w_c78_ml_deep70_tierA_wlow, s_q07w_s78_ml_deep70_ins2_vix20)
- EXIT_BASE: mean 262.8bp (n=4, t=0.32, win 50.0%, exits {'stop': 1, 'horizon': 3})
- DROP_STOP: mean 281.5bp (n=4), paired delta 18.7bp (n=4, t=1.0), exits {'horizon': 4}
- WIDEN_STOP_X2: mean 281.5bp (n=4), paired delta 18.7bp (n=4, t=1.0), exits {'horizon': 4}
- EXTEND_HORIZON_X2: mean 581.0bp (n=4), paired delta 318.2bp (n=4, t=0.45), exits {'stop': 2, 'horizon': 2}
- NIGHT1_ONLY: mean 65.2bp (n=4), paired delta -197.6bp (n=4, t=-0.22), exits {'horizon': 4}

### s_q07w_s78_ml_deep70_ins2_vix20 (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base REGISTERED stop=0.15 target=None h=20, mirror of s_q07w_c78_ml_deep70_tierA_wlow, s_q07w_s52_ml_deep70_ins2_vix20)
- EXIT_BASE: mean 262.8bp (n=4, t=0.32, win 50.0%, exits {'stop': 1, 'horizon': 3})
- DROP_STOP: mean 281.5bp (n=4), paired delta 18.7bp (n=4, t=1.0), exits {'horizon': 4}
- WIDEN_STOP_X2: mean 281.5bp (n=4), paired delta 18.7bp (n=4, t=1.0), exits {'horizon': 4}
- EXTEND_HORIZON_X2: mean 581.0bp (n=4), paired delta 318.2bp (n=4, t=0.45), exits {'stop': 2, 'horizon': 2}
- NIGHT1_ONLY: mean 65.2bp (n=4), paired delta -197.6bp (n=4, t=-0.22), exits {'horizon': 4}

### aster_etf_qqq_qld_buy_hold (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 140.4bp (n=2, t=3.68, win 100.0%, exits {'horizon': 2})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 674.1bp (n=2), paired delta 533.7bp (n=2, t=2.97), exits {'horizon': 2}
- NIGHT1_ONLY: mean 170.6bp (n=2), paired delta 30.2bp (n=2, t=1.54), exits {'horizon': 2}

### s_1dgp5 (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=None target=None h=40)
- EXIT_BASE: mean -3236.3bp (n=2, t=-2.31, win 0.0%, exits {'horizon': 2})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -3619.9bp (n=2), paired delta -383.6bp (n=2, t=-1.0), exits {'horizon': 2}
- NIGHT1_ONLY: mean -65.8bp (n=2), paired delta 3170.5bp (n=2, t=1.71), exits {'horizon': 2}

### s_1wg_small (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 4996.8bp (n=2, t=2.77, win 100.0%, exits {'horizon': 2})
- DROP_STOP: mean 4996.8bp (n=2), paired delta 0.0bp (n=2, t=None), exits {'horizon': 2}
- WIDEN_STOP_X2: mean 4996.8bp (n=2), paired delta 0.0bp (n=2, t=None), exits {'horizon': 2}
- EXTEND_HORIZON_X2: mean 4744.6bp (n=2), paired delta -252.2bp (n=2, t=-0.65), exits {'horizon': 2}
- NIGHT1_ONLY: mean -34.3bp (n=2), paired delta -5031.1bp (n=2, t=-2.46), exits {'horizon': 2}

### s_1wsw (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=0.15 target=None h=126)
- EXIT_BASE: mean 1204.2bp (n=2, t=3.2, win 100.0%, exits {'horizon': 2})
- DROP_STOP: mean 1204.2bp (n=2), paired delta 0.0bp (n=2, t=None), exits {'horizon': 2}
- WIDEN_STOP_X2: mean 1204.2bp (n=2), paired delta 0.0bp (n=2, t=None), exits {'horizon': 2}
- EXTEND_HORIZON_X2: mean 2295.4bp (n=2), paired delta 1091.2bp (n=2, t=1.0), exits {'horizon': 2}
- NIGHT1_ONLY: mean 71.3bp (n=2), paired delta -1132.9bp (n=2, t=-4.84), exits {'horizon': 2}

### aster_etf_qld_buy_hold (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 178.6bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 892.0bp (n=1), paired delta 713.4bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean 228.4bp (n=1), paired delta 49.8bp (n=1, t=None), exits {'horizon': 1}

### aster_etf_qqq_buy_hold (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean -295.9bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 23.2bp (n=1), paired delta 319.1bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -32.6bp (n=1), paired delta 263.3bp (n=1, t=None), exits {'horizon': 1}

### aster_etf_spy_buy_hold (Aster, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 9.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -370.0bp (n=1), paired delta -379.3bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -13.1bp (n=1), paired delta -22.5bp (n=1, t=None), exits {'horizon': 1}

### aster_tensor_c1_cash_all_25 (Tensor, Unblock-2 REPLAY-INDICATIVE, stream tensorregen, base REGISTERED stop=None target=None h=260)
- EXIT_BASE: mean 583.4bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 583.4bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -73.3bp (n=1), paired delta -656.7bp (n=1, t=None), exits {'horizon': 1}

### aster_tensor_g4_cash_all_10 (Tensor, Unblock-2 REPLAY-INDICATIVE, stream tensorregen, base REGISTERED stop=None target=None h=260, mirror of aster_tensor_g4_cash_all_25, aster_tensor_g4_cash_cool_25, aster_tensor_g4_cash_hot_25)
- EXIT_BASE: mean -4246.8bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -4246.8bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -721.5bp (n=1), paired delta 3525.3bp (n=1, t=None), exits {'horizon': 1}

### aster_tensor_g4_cash_all_25 (Tensor, Unblock-2 REPLAY-INDICATIVE, stream tensorregen, base REGISTERED stop=None target=None h=260, mirror of aster_tensor_g4_cash_all_10, aster_tensor_g4_cash_cool_25, aster_tensor_g4_cash_hot_25)
- EXIT_BASE: mean -4246.8bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -4246.8bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -721.5bp (n=1), paired delta 3525.3bp (n=1, t=None), exits {'horizon': 1}

### aster_tensor_g4_cash_cool_25 (Tensor, Unblock-2 REPLAY-INDICATIVE, stream tensorregen, base REGISTERED stop=None target=None h=260, mirror of aster_tensor_g4_cash_all_10, aster_tensor_g4_cash_all_25, aster_tensor_g4_cash_hot_25)
- EXIT_BASE: mean -4246.8bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -4246.8bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -721.5bp (n=1), paired delta 3525.3bp (n=1, t=None), exits {'horizon': 1}

### aster_tensor_g4_cash_hot_25 (Tensor, Unblock-2 REPLAY-INDICATIVE, stream tensorregen, base REGISTERED stop=None target=None h=260, mirror of aster_tensor_g4_cash_all_10, aster_tensor_g4_cash_all_25, aster_tensor_g4_cash_cool_25)
- EXIT_BASE: mean -4246.8bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -4246.8bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -721.5bp (n=1), paired delta 3525.3bp (n=1, t=None), exits {'horizon': 1}

### coffin_rebuilt (Spec-built, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean 114.5bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -46.2bp (n=1), paired delta -160.7bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean 2.9bp (n=1), paired delta -111.6bp (n=1, t=None), exits {'horizon': 1}

### rule_1d_cyan_smallcap (Fires and singles, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=None target=None h=21)
- EXIT_BASE: mean -4003.5bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -4003.5bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -424.2bp (n=1), paired delta 3579.3bp (n=1, t=None), exits {'horizon': 1}

### s_1wc_micro (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 3193.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: mean 3193.3bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- WIDEN_STOP_X2: mean 3193.3bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- EXTEND_HORIZON_X2: mean 3326.2bp (n=1), paired delta 132.9bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean 210.0bp (n=1), paired delta -2983.3bp (n=1, t=None), exits {'horizon': 1}

### s_mn_moonshot (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base DEFAULT_HOLD10 stop=None target=None h=10)
- EXIT_BASE: mean -1165.5bp (n=1, t=None, win 0.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean -40.7bp (n=1), paired delta 1124.8bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -487.2bp (n=1), paired delta 678.2bp (n=1, t=None), exits {'horizon': 1}

### s_moonshot (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream base, base REGISTERED stop=0.15 target=None h=252)
- EXIT_BASE: mean 3071.4bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: mean 3071.4bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- WIDEN_STOP_X2: mean 3071.4bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- EXTEND_HORIZON_X2: mean 3071.4bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean 593.3bp (n=1), paired delta -2478.1bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c52_ml_mom6_tierA_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c52_ml_mom6_wspike2 (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream dropf_wspike2, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c52_ml_tierA_wcov (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c52_ml_tierA_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c78_ml_mom6_tierA_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c78_ml_tierA_wcov (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_c78_ml_tierA_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_g52_ml_ats_z1_mom6_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_g52_ml_ins2_wlow (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base REGISTERED stop=0.15 target=None h=20, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_tierA_wcov, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 261.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: mean 261.3bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- WIDEN_STOP_X2: mean 261.3bp (n=1), paired delta 0.0bp (n=1, t=None), exits {'horizon': 1}
- EXTEND_HORIZON_X2: mean -351.8bp (n=1), paired delta -613.2bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -268.1bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_g52_ml_tierA_wcov (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g78_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

### s_q07w_g78_ml_tierA_wcov (Lazarus/Q07/MN, Unblock-2 REPLAY-INDICATIVE, stream drop_altfilters, base DEFAULT_HOLD10 stop=None target=None h=10, mirror of s_q07w_c52_ml_mom6_tierA_wlow, s_q07w_c52_ml_mom6_wspike2, s_q07w_c52_ml_tierA_wcov, s_q07w_c52_ml_tierA_wlow, s_q07w_c78_ml_mom6_tierA_wlow, s_q07w_c78_ml_tierA_wcov, s_q07w_c78_ml_tierA_wlow, s_q07w_g52_ml_ats_z1_mom6_wlow, s_q07w_g52_ml_ins2_wlow, s_q07w_g52_ml_tierA_wcov)
- EXIT_BASE: mean 694.3bp (n=1, t=None, win 100.0%, exits {'horizon': 1})
- DROP_STOP: NOT_APPLICABLE (base carries no stop)
- WIDEN_STOP_X2: NOT_APPLICABLE (base carries no stop)
- EXTEND_HORIZON_X2: mean 261.3bp (n=1), paired delta -433.0bp (n=1, t=None), exits {'horizon': 1}
- NIGHT1_ONLY: mean -6.7bp (n=1), paired delta -701.0bp (n=1, t=None), exits {'horizon': 1}

## SEAT LENS (lens only; adversarial = probability the object is entirely artifact)

- STOP_LOOSEN_LAZARUS: lens mean 0.484 (7 lenses answered), adversarial artifact 0.58, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- NIGHT1_PREDICTION_MISS: lens mean 0.8 (7 lenses answered), adversarial artifact 0.6, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- ADA_BREAKOUT_NIGHT1: lens mean 0.607 (7 lenses answered), adversarial artifact 0.61, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- LINK_ABSORPTION_EXTEND: lens mean 0.267 (7 lenses answered), adversarial artifact 0.66, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SRULES1W_EXTEND: lens mean 0.74 (7 lenses answered), adversarial artifact 0.52, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- QQQQLD_MONTHLY_NIGHT1: lens mean 0.587 (7 lenses answered), adversarial artifact 0.64, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- ONEDC_EXTEND_DESTROYS: lens mean 0.661 (7 lenses answered), adversarial artifact 0.68, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- TENSOR_NIGHT1_THIN: lens mean 0.923 (7 lenses answered), adversarial artifact 0.79, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)

Seat spend this lane: $0.003025 over 8 seated objects (Midna's terms; the typed seat never set a grade above).

## METHOD AND LIMITS

- Machinery: Unblock-2's Book.path on stored daily closes (the 149-symbol widened cache plus PF daily for ADA/LINK), close-based first touch of stop/target, 6bp exit cost per trade, returns raw per-trade bp (not benchmark excess), deltas paired trade-by-trade against the sleeve's own base. Close-based stops understate intraday stop-outs; every stop result inherits that basis.
- Bases: REGISTERED = Lane C's extracted stop/target/horizon (horizon defaults to 20 where a stop or target exists without one, Unblock-2's own convention). DEFAULT_HOLD10 = no exit params exist in the sleeve's map; the base is a plain 10-session hold, the Lane C standard. Variations against a DEFAULT base measure the default's wrongness as much as the variation's merit; those rows are labeled per row and in every lead above.
- Stop variations are NOT_APPLICABLE on stop-less bases: 88 rows, being DROP_STOP and WIDEN_STOP_X2 for 44 sleeves (34 DEFAULT_HOLD10 bases and 10 REGISTERED bases that carry a horizon but no stop: the 5 Tensor sleeves, 1dc, s_1dg, s_1dgp5, s_rules_1d, rule_1d_cyan_smallcap). Nothing was silently skipped; the register carries the reason in each row.
- Clustering: replay entry dates concentrate on few dates per sleeve (the Lazarus fire stream fires basket-wide on the same dates), so paired t values overstate independence; n is trades, not independent bets. Mirror sizing variants share one stream and double-count in any pooled figure; distinct-stream counts are printed wherever a lead is stated.
- The Tensor union is 5 sleeves with 1 entry each: no Tensor exit claim in this lane carries evidence, including the family row's +2688.9bp, which is printed only to be refused as a claim.

STATUS: PARTIAL - the variation set is proven on the final register (285 sleeve rows over 57 of 57 union sleeves, 57 sleeves with at least one GRADED variation, 17 mover rows over 9 distinct streams, the KG-4 prediction checked family by family with its misses printed). The PARTIAL names the remainders: 88 NOT_APPLICABLE stop rows on stop-less bases (68 on DEFAULT bases, 20 on REGISTERED horizon-only bases; the question is undefined there, not unanswered); the Tensor family's n=5 makes its prediction cell untestable in this union; every lead is a replay result whose arming check is the named forward shadow run, not yet executed; and the DEFAULT_HOLD10 bases mean 34 of 57 sleeves were varied against a convention, not against their own (nonexistent) registered exits.
