# KG-4: HOLD-PHASE AND SEGMENT DECOMPOSITION OF THE FLEET AND THE BOOK

Coverage, counted on the final artifacts: 214 decomposition cells in KG-4-REGISTER.jsonl, built from 6708 dispatcher entry events (6664 priceable at night 1 on the 149-symbol bar cache as widened by UNBLOCK-1), 435 entry events with held-session segment decompositions on the 1Min cache, the book's 4 realised trades and 7 open positions, and the Ghost Book's 21 resolutions. Decisions API lens: 13 objects, 117 questions, $0.004047 (bank kg4-phase-decomposition v1.0); seats set no grades.

## POTENTIAL EDGE FOUND

**K4-1, the fleet's equity phase shape: night 1 earns, every later phase bleeds.** Equity-symbol entries only (excess bp vs QQQ): N1 [n=5648, clusters=12, mean=43.4bp, win=0.569]; N2-3 [n=4566, clusters=10, mean=-152.3bp, win=0.388]; N4-5 [n=3500, clusters=8, mean=-260.5bp, win=0.29]; N4+ [n=1886, clusters=3, mean=-839.1bp, win=0.25]. The fleet as recorded is a night-1 book carrying multi-night holds. Cheapest forward check: re-run this exact decomposition on the forward dispatcher stream at 20 live sessions from Mon 2026-11-16 (Lane 3's standing forward design, now with phase fields). Seat lens mean 0.536, adversarial artifact probability 0.58, the least skeptical family-level read in this lane.

**K4-2, Tensor is the phase-shape extreme: its recorded entries earn only in phase N1 and decay monotonically.** N1 [n=4737, clusters=10, mean=29.0bp, win=0.567]; N2-3 [n=3722, clusters=8, mean=-235.8bp, win=0.364]; N4-5 [n=2780, clusters=6, mean=-237.8bp, win=0.237]. At sleeve level the two aster_tensor_d20 sleeves print the same shape at size (N1 +413bp and +443bp excess on 684 and 420 events over 7 dates, N4-5 at -329bp and -413bp). Tensor's multi-night holds are, on this record, a decay position. Cheapest forward check: a shadow night-1-only exit on Tensor-family entries in the forward stream, graded against the family's actual holds at 20 sessions.

**K4-3, two families run the opposite phase shape, so a fleet-wide hold rule would destroy both.** Fires and singles: N1 [n=128, clusters=8, mean=-429.8bp, win=0.375] then N2-3 [n=108, clusters=7, mean=1378.2bp, win=0.898] and N4+ [n=90, clusters=3, mean=1027.2bp, win=0.878]: slow starters that earn late. Aster: N1 [n=196, clusters=11, mean=67.8bp, win=0.439], N2-3 [n=158, clusters=9, mean=500.6bp, win=0.519]: earns in nights 2-3. Lazarus/Q07/MN: N1 [n=392, clusters=5, mean=390.4bp, win=0.944] with win rate 0.944, then N4+ [n=352, clusters=2, mean=-1545.5bp, win=0.009] on 2 dates: a night-1 spike that fully decays. Phase is a family property, not a fleet property; any hold-length rule must be registered per family.

**K4-4, the held tape's segment shape on the fleet's own names reproduces Lane 3's universe shape.** Direction-signed bp per held session (1Min cache, RTH): OPEN_DRIVE [n=1546, clusters=52, mean=18.4bp, win=0.682]; MIDDAY [n=1613, clusters=54, mean=-34.2bp, win=0.257]; CLOSE_HOUR [n=1630, clusters=54, mean=-2.3bp, win=0.485]; OVERNIGHT [n=1196, clusters=42, mean=-16.8bp, win=0.579]. While the fleet held positions, the open drive carried and midday bled, the same ordering Lane 3 measured on an independent large-cap universe. Seat lens mean 0.756, the highest in this lane. Cheapest forward check: Lane 3's registered H-D (entries graded by segment at the first 20 resolved shadow fires per family), extended with a held-session segment log on the forward stream.

**K4-5, Lazarus-held sessions almost never rise at midday.** MIDDAY [n=702, clusters=14, mean=-67.0bp, win=0.009] (win rate 0.009 over 702 held sessions, 14 clusters) against OPEN_DRIVE [n=701, clusters=13, mean=31.2bp, win=0.749]. Whatever Lazarus holds, its tape falls between 10:30 and 15:00 in this window with near-perfect consistency: either its names are structurally midday-weak, or its entries systematically precede midday declines. Cheapest forward check: H-D conditioned on Lazarus entries specifically, from the forward stream's first 20 sessions.

**K4-6, the book's losses are a phase-N1 and exit-day phenomenon, not a selection phenomenon (all cells n<=4, leads-with-n).** 3 of the book's 4 realised trades were held exactly 1 night and carry -$2,208.70 of the -$2,460.13 total loss (89.8%) inside phase N1; the open book's marks through Fri 2026-11-14 are also N1-negative (OKLO -665.1bp N1 and -216.8bp N2-3; CRDO -69.2bp; PLTR -62.7bp; MU -39.9bp). The one fully decomposed trade, NVDA, earned in every carried segment (midday remainder +8.1bp, close hour +128.2bp, overnight +217.7bp) and lost -615.9bp in the exit day's intraday residual before its 10:45 ET L-07 exit: the position was right for a day and a night and was destroyed in one morning. Entry-segment census of realised trades: MIDDAY entries 2 trades, -$1,370.22; OPEN_DRIVE 1 trade, -$838.48; PREMARKET 1 trade, -$251.43. Cheapest forward check: phase and entry-segment fields on every new card's journal record (the G19 probability fields are already wired at drafting and signing), graded at the first 20 resolved book trades.

**K4-7, the Ghost Book has no phase structure on the first-touch basis: it is a night-1 stop-distance object.** All 21 resolved fires completed inside phase N1 (mean -0.8997R); the 11 entry-viable fires all stopped at exactly -1.0R, and the 10 sub-1.0 fires averaged -0.789R including the only target hit (CLS, +1.1065R). Phases N2-3 and N4+ carry zero observations by construction. Any phase claim about Ghost expressions waits on the hold-to-expiry resolver variant (KG-2's lane); on this basis, the only lever is stop distance inside night 1.

## BASIS WARNINGS (printed, not buried)

- **Option-contract fills are a different object.** 1,016 of the 6,664 priceable entry events are fills on option-contract symbols (the investandbefree_dmac complex and kin), priced on the contracts' own daily closes. Their phase profile (N1 [n=1016, clusters=5, mean=-4559.2bp, win=0.134]; N2-3 [n=1016, clusters=5, mean=4138.4bp, win=0.375]; N4-5 [n=582, clusters=3, mean=-5792.7bp, win=0.416]) is dominated by contract Greeks and expiry geometry, not by the sleeves' underlying signals, and the dmac complex is one signal stream in four mirrored costumes (Lane 3), so its effective n is a quarter of its printed n. These rows stand in the register under BASIS-OPTION-CONTRACTS and are excluded from every fleet-equity claim above.
- **Clustering is the binding limit everywhere.** Fleet phase cells rest on 12 distinct entry dates at N1, 10 at N2-3, 8 at N4-5, 3 at N4+; family N4+ cells rest on 1 to 3 dates. Phase means are printed with their cluster counts in every register row, and no phase cell in this deliverable is a verdict: each is a lead whose forward check is named.
- **Segment cells measure the held tape, not sleeve PnL.** A segment cell is the direction-signed tape move during sessions a position was open, summed per held session; it decomposes exposure, and it is not additive with the phase cells (different basis, different windows).

## FULL TABLES

### Desk, hold phase by family (excess bp vs QQQ; raw bp in the register)

| Family | N1 | N2-3 | N4-5 | N4+ |
|---|---|---|---|---|
| Tensor | 29.0 (n=4737, d=10) | -235.8 (n=3722, d=8) | -237.8 (n=2780, d=6) | -846.2 (n=1368, d=1) |
| Aster | 67.8 (n=196, d=11) | 500.6 (n=158, d=9) | 227.0 (n=139, d=8) | 23.1 (n=60, d=3) |
| Lazarus/Q07/MN | 390.4 (n=392, d=5) | -62.4 (n=392, d=5) | -789.8 (n=376, d=4) | -1545.5 (n=352, d=2) |
| Spec-built | -3828.0 (n=1211, d=10) | 3480.4 (n=1202, d=8) | -4988.5 (n=681, d=7) | 1572.6 (n=16, d=2) |
| Fires and singles | -429.8 (n=128, d=8) | 1378.2 (n=108, d=7) | 381.9 (n=106, d=6) | 1027.2 (n=90, d=3) |

### Desk, held-session segments by family (bp per held session)

| Family | Overnight | Open drive | Midday | Close hour |
|---|---|---|---|---|
| Tensor | -517.6 (n=4, win=0.0) | 89.4 (n=81, win=1.0) | 223.7 (n=88, win=1.0) | 60.5 (n=90, win=0.956) |
| Aster | 19.8 (n=213, win=0.568) | 27.2 (n=224, win=0.763) | -0.1 (n=268, win=0.59) | -14.6 (n=279, win=0.444) |
| Lazarus/Q07/MN | -22.2 (n=527, win=0.664) | 31.2 (n=701, win=0.749) | -67.0 (n=702, win=0.009) | 14.3 (n=702, win=0.5) |
| Spec-built | -29.6 (n=414, win=0.502) | -11.5 (n=489, win=0.528) | -63.9 (n=499, win=0.224) | -28.2 (n=502, win=0.42) |
| Fires and singles | 45.0 (n=38, win=0.342) | -21.4 (n=51, win=0.373) | 72.7 (n=56, win=0.911) | -17.0 (n=57, win=0.333) |

### Sleeve phase extremes (n>=30 events, excess bp; full set in the register)

- investandbefree_dmac_intraday N1: mean -9224.7bp, n=179, dates=3, win=0.0
- investandbefree_dmac_dailyonly N4-5: mean -5857.5bp, n=194, dates=3, win=0.412
- investandbefree_dmac N4-5: mean -5821.1bp, n=195, dates=3, win=0.415
- investandbefree_dmac_premacd N4-5: mean -5742.5bp, n=192, dates=3, win=0.417
- investandbefree_dmac_intraday N2-3: mean 4165.2bp, n=179, dates=3, win=0.223
- investandbefree_dmac_dailyonly N2-3: mean 4150.4bp, n=279, dates=4, win=0.409
- investandbefree_dmac N2-3: mean 4128.6bp, n=280, dates=4, win=0.407
- investandbefree_dmac_premacd N2-3: mean 4068.2bp, n=277, dates=4, win=0.404
- investandbefree_dmac_premacd N1: mean -3576.5bp, n=277, dates=4, win=0.159
- investandbefree_dmac N1: mean -3533.6bp, n=280, dates=4, win=0.164
- investandbefree_dmac_dailyonly N1: mean -3528.4bp, n=279, dates=4, win=0.165
- s_mn_hourly_1w N4+: mean -2816.4bp, n=176, dates=1, win=0.0
- aster_trader_donchian55 N2-3: mean 1883.9bp, n=42, dates=3, win=0.952
- s_mn_hourly_1w N4-5: mean -1808.7bp, n=181, dates=3, win=0.006
- tensor_swing N4+: mean -846.2bp, n=1368, dates=1, win=0.25

### Book and Ghost Book

- BOOK REALISED PHASE N1: n=3, sum=$-2208.7. trades held exactly 1 night: SHOP, MO, NVDA; all realised PnL sits in phase N1
- BOOK REALISED PHASE N1+N2 (ELF, split not carried): n=1, mean=-416.2 (usd_pnl), sum=$-251.43. ELF held 2 nights (2026-11-10 to 2026-11-12), realised -$251.43; the night-1/night-2 split needs ELF daily closes, absent from the desk bar cache
- BOOK REALISED ENTRY-SEGMENT MIDDAY: n=2, sum=$-1370.22. symbols: SHOP, NVDA
- BOOK REALISED ENTRY-SEGMENT OPEN_DRIVE: n=1, sum=$-838.48. symbols: MO
- BOOK REALISED ENTRY-SEGMENT PREMARKET: n=1, sum=$-251.43. symbols: ELF
- BOOK OPEN-OKLO PHASE N1: n=1, mean=-665.1 (raw_bp_mark). open position mark, sessions observed 2 through 2026-11-14
- BOOK OPEN-OKLO PHASE N2-3: n=1, mean=-216.8 (raw_bp_mark). open position mark through 2026-11-14 (partial phase)
- BOOK OPEN-CRDO PHASE N1: n=1, mean=-69.2 (raw_bp_mark). open position mark, sessions observed 1 through 2026-11-14
- BOOK OPEN-PLTR PHASE N1: n=1, mean=-62.7 (raw_bp_mark). open position mark, sessions observed 1 through 2026-11-14
- BOOK OPEN-MU PHASE N1: n=1, mean=-39.9 (raw_bp_mark). open position mark, sessions observed 1 through 2026-11-14
- BOOK REALISED-NVDA SEGMENT-PATH MIDDAY remainder 2026-11-12 (fill 12:30-15:00): n=1, mean=8.1 (raw_bp). anchored at the ledger fills (164.047 in, 159.7502 out) with RTH 1Min closes at the segment joints; the 2026-11-13 NVDA 1Min cache is truncated at 09:32 ET (333 bars incl. extended hours), so that day's intraday segments are not carried and the residual row absorbs them: carried segments plus residual equal the trade return -261.9bp (additive bp)
- BOOK REALISED-NVDA SEGMENT-PATH CLOSE_HOUR 2026-11-12: n=1, mean=128.2 (raw_bp). anchored at the ledger fills (164.047 in, 159.7502 out) with RTH 1Min closes at the segment joints; the 2026-11-13 NVDA 1Min cache is truncated at 09:32 ET (333 bars incl. extended hours), so that day's intraday segments are not carried and the residual row absorbs them: carried segments plus residual equal the trade return -261.9bp (additive bp)
- BOOK REALISED-NVDA SEGMENT-PATH OVERNIGHT 11-12->11-13: n=1, mean=217.7 (raw_bp). anchored at the ledger fills (164.047 in, 159.7502 out) with RTH 1Min closes at the segment joints; the 2026-11-13 NVDA 1Min cache is truncated at 09:32 ET (333 bars incl. extended hours), so that day's intraday segments are not carried and the residual row absorbs them: carried segments plus residual equal the trade return -261.9bp (additive bp)
- BOOK REALISED-NVDA SEGMENT-PATH RESIDUAL 2026-11-13 intraday to exit fill (10:45): n=1, mean=-615.9 (raw_bp). anchored at the ledger fills (164.047 in, 159.7502 out) with RTH 1Min closes at the segment joints; the 2026-11-13 NVDA 1Min cache is truncated at 09:32 ET (333 bars incl. extended hours), so that day's intraday segments are not carried and the residual row absorbs them: carried segments plus residual equal the trade return -261.9bp (additive bp)
- GHOST ALL PHASE N1: n=21, mean=-0.8997 (realized_R). path-session distribution across all 21 resolutions: {1: 20, 2: 1}; the one 2-row path (VRT) was already at value 0.0 on its first path close, so all 21 fires' losses completed inside phase N1 and phases N2-3 / N4+ carry zero incremental observations
- GHOST VIABLE PHASE N1: n=11, mean=-1.0 (realized_R). entry-viability split inside phase N1 (R>=1.0 at entry)
- GHOST SUB-1.0 PHASE N1: n=10, mean=-0.7893 (realized_R). entry-viability split inside phase N1 (R<1.0 at entry)
- GHOST ALL SEGMENT NOT CARRIED: n=0. resolutions carry daily closes only; the intraday segment shape of the 21 fires is not in the record (the resolver's named basis limit)

### Seat lens (lens only; adversarial = probability the split is entirely artifact)

- BOOK_PHASE: lens mean 0.679 (7 lenses answered), adversarial artifact 0.6, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- GHOST_PHASE: lens mean 0.533 (6 lenses answered), adversarial artifact 0.72, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_Aster: lens mean 0.213 (7 lenses answered), adversarial artifact 0.66, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_FLEET_EQUITY: lens mean 0.536 (7 lenses answered), adversarial artifact 0.58, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_Fires and singles: lens mean 0.267 (7 lenses answered), adversarial artifact 0.69, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_Lazarus/Q07/MN: lens mean 0.176 (7 lenses answered), adversarial artifact 0.76, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_Spec-built: lens mean 0.219 (7 lenses answered), adversarial artifact 0.68, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- PHASE_Tensor: lens mean 0.237 (7 lenses answered), adversarial artifact 0.65, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SEG_Aster: lens mean 0.441 (7 lenses answered), adversarial artifact 0.62, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SEG_FLEET: lens mean 0.756 (7 lenses answered), adversarial artifact 0.58, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SEG_Lazarus/Q07/MN: lens mean 0.33 (7 lenses answered), adversarial artifact 0.79, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SEG_Spec-built: lens mean 0.354 (7 lenses answered), adversarial artifact 0.74, action level index 1 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)
- SEG_Tensor: lens mean 0.284 (5 lenses answered), adversarial artifact 0.78, action level index 2 (bands 0=0-20, 1=20-40, 2=40-60, 3=60-80, 4=80-100)

STATUS: PARTIAL. The decomposition is proven on the final artifacts (214 cells counted in KG-4-REGISTER.jsonl: desk phase and segment cells on 6,664 priceable entry events and 435 segment-decomposed events, book cells on all 4 realised trades and the 4 bar-carrying open positions (5 phase cells), Ghost cells on all 21 resolutions); the PARTIAL names what the record cannot carry: ELF's night split and EW's and RKLB's open-position phase marks (daily bars absent from the cache), the Ghost Book's segment shape (daily closes only), and every phase claim's forward proof, which waits on the 20-session forward stream from Mon 2026-11-16 named in each lead's cheapest check.
