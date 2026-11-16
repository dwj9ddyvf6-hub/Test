# CONV EXPRESSION ROUTES: HELD-DATA READS FOR CONV-43/CONV-19 AND CONV-41/CONV-42

Built Sun 2026-11-15 night. Book-side and research-side files only. Nothing trades, nothing is sized, no conversion register file was edited, and the desk tree was touched only by reading its 1Min bar cache.

SCOPE. Surface: this file and the scratch scripts with their results JSON in this pass2 directory (conv_expression_intraday.py, conv_expression_intraday_variants.py). Constraints: held data only; the redesigned-basis diagnostic in Part A is in-sample and does not replace the registered forward test (the next 21 forward fires on the redesigned basis, plus the hold-to-expiry settlement reruns after the 2026-11-27 and 2026-12-18 sessions); the Part B read is a coverage and executability PRE-READ only and does not replace the registered decisive read of Tue 2026-11-17 on the first production chain capture of Mon 2026-11-16 16:46 ET. Outcome: for each of the four blocked rows, either a computed held-data result with headline numbers, or the exact remaining gap with its source named. Proof: the per-fire and per-construction tables below, computed tonight from the files named in each section.

## ROUTES TRIED LEDGER

Part A routes, in order:
1. Desk 1Min cache (~/workspace/muse-desk-v3/cache/bars/<SYM>/1Min.jsonl), read only. Result: files exist for 10 of the 21 Ghost Book underlyings; the intraday walk ran on those 10 (section A3).
2. The same cache checked for the other 11 underlyings. Result: 1Day.jsonl only, no 1Min file (section A5).
3. Other held intraday sources searched for the missing 11 and for intraday option marks: the DH3 widening register (Focus 29 only, so it cannot cover the non-Focus names), the terminal-lineup deep store (daily bar panel, not intraday), the morgue pername tape (options trade print aggregates, no underlying bars and no quotes), the typed-layer wave1_bars route behind both shadow resolvers (Alpaca SIP daily bars only, per the resolver docstrings), and the dry capture chain store of 2026-11-14 (one snapshot, spot basis the 2026-11-13 close, no intraday path). Result: no held intraday underlying bars for the 11, and no held intraday option marks for any of the 21 (section A4).

Part B routes, in order:
1. The Potential-Edge Register rows register[31] and register[34], then their sources SIX-CONSTRUCTIONS-RUN-2-2026-11-15.md and C2C6-RUNFILE.md, then the development lock addendum C2C6-LOCK-ADDENDUM-2026-11-15.md in the same home (~/workspace/research_notes/six-constructions-20261115/). Result: the constructions are registered at liability level only; no strike family, expiry family, named decision event, or numeric premium hurdle exists in any of the three files (section B1).
2. The held Focus chain panel from DH4 (the dry capture store). Result: quote-carrying rows exist for all 31 panel underlyings; a coverage pre-read at panel level ran (section B2). No spread could be priced, because route 1 found no registered spread to price (section B3).

## PART A: CONV-43 AND CONV-19, GHOST BOOK EXPRESSION ON THE REDESIGNED BASIS

### A1. The 21 fires as recorded

Source: ~/workspace/midna-book/GHOST-BOOK.md and ~/workspace/midna-book/ghost-book-ledger.jsonl, grades from ~/workspace/midna-book/ghost-book-resolutions.jsonl. Every fire is a Tensor fire of bar date 2026-11-11, expressed as a vertical debit call spread at expiry 2026-11-27 (TTMI at 2026-12-18), priced 2026-11-13 off the live TastyTrade chain. The retired basis (shadow_resolver.py) walks SIP daily closes after the bar date: first close at or above target is TARGET_HIT, first close at or below stop is STOPPED_OUT, exit at intrinsic value at that close.

| Symbol | Entry | Stop | Target | Spread (long/short) | Expiry | Debit | Entry R | Retired basis |
|---|---|---|---|---|---|---|---|---|
| NBIS | 157.14 | 155.96 | 164.91 | 157.5 / 165.0 | 2026-11-27 | 0.705 | 9.511 | STOPPED_OUT 2026-11-12, -1.000R |
| LITE | 659.91 | 658.00 | 685.72 | 660.0 / 690.0 | 2026-11-27 | 10.150 | 1.534 | STOPPED_OUT 2026-11-12, -1.000R |
| SOXL | 67.56 | 67.00 | 72.50 | 68.0 / 73.0 | 2026-11-27 | 1.625 | 1.769 | STOPPED_OUT 2026-11-12, -1.000R |
| AAOI | 56.50 | 56.20 | 59.62 | 57.0 / 60.0 | 2026-11-27 | 0.925 | 1.832 | STOPPED_OUT 2026-11-12, -1.000R |
| WDC | 316.15 | 315.00 | 323.21 | 317.5 / 325.0 | 2026-11-27 | 3.025 | 0.889 | STOPPED_OUT 2026-11-12, -1.000R |
| IREN | 21.49 | 21.09 | 22.53 | 21.5 / 23.0 | 2026-11-27 | 0.360 | 1.866 | STOPPED_OUT 2026-11-12, -1.000R |
| AXTI | 47.74 | 47.40 | 50.30 | 48.0 / 51.0 | 2026-11-27 | 0.725 | 2.172 | STOPPED_OUT 2026-11-12, -1.000R |
| ALAB | 235.30 | 234.46 | 241.21 | 237.5 / 242.5 | 2026-11-27 | 2.150 | 0.728 | STOPPED_OUT 2026-11-12, -1.000R |
| CRDO | 143.47 | 142.75 | 150.36 | 144.0 / 152.5 | 2026-11-27 | 3.100 | 1.053 | STOPPED_OUT 2026-11-12, -1.000R |
| FCEL | 10.82 | 10.76 | 11.58 | 11.0 / 12.0 | 2026-11-27 | 0.275 | 1.109 | STOPPED_OUT 2026-11-12, -1.000R |
| HIVE | 1.78 | 1.77 | 1.87 | 2.0 / 2.5 | 2026-11-27 | 0.025 | -1.000 | STOPPED_OUT 2026-11-12, -1.000R |
| SNDK | 995.10 | 990.56 | 1029.52 | 997.5 / 1030.0 | 2026-11-27 | 11.150 | 1.872 | STOPPED_OUT 2026-11-12, -1.000R |
| TSEM | 160.26 | 159.74 | 165.96 | 162.5 / 170.0 | 2026-11-27 | 1.900 | 0.821 | STOPPED_OUT 2026-11-12, -1.000R |
| ARM | 205.04 | 204.12 | 211.15 | 207.5 / 212.5 | 2026-11-27 | 1.825 | 0.999 | STOPPED_OUT 2026-11-12, -1.000R |
| KEEL | 2.13 | 2.11 | 2.22 | 2.5 / 3.0 | 2026-11-27 | 0.015 | -1.000 | STOPPED_OUT 2026-11-12, -1.000R |
| MU | 818.23 | 816.15 | 841.09 | 820.0 / 845.0 | 2026-11-27 | 9.125 | 1.311 | STOPPED_OUT 2026-11-12, -1.000R |
| CLS | 246.42 | 244.74 | 251.17 | 247.5 / 255.0 | 2026-11-27 | 3.100 | 0.184 | TARGET_HIT 2026-11-12, +1.1065R |
| TTMI | 81.06 | 80.68 | 82.62 | 85.0 / 90.0 | 2026-12-18 | 1.250 | -1.000 | STOPPED_OUT 2026-11-12, -1.000R |
| CVNA | 73.87 | 73.61 | 75.33 | 74.0 / 76.0 | 2026-11-27 | 0.600 | 1.217 | STOPPED_OUT 2026-11-12, -1.000R |
| VRT | 209.18 | 208.40 | 215.40 | 210.0 / 217.5 | 2026-11-27 | 3.125 | 0.726 | STOPPED_OUT 2026-11-13, -1.000R |
| USAR | 8.69 | 8.66 | 8.98 | 9.0 / 9.5 | 2026-11-27 | 0.130 | -1.000 | STOPPED_OUT 2026-11-12, -1.000R |

Retired basis total, as registered: 20 STOPPED_OUT at -1.000R, 1 TARGET_HIT at +1.1065R, summed P and L -4,875.50 dollars per contract across the 21.

### A2. What the F20 stop geometry actually is

The register phrase "stop geometry per the F20 researched levels" resolves, in its source (~/workspace/research_notes/options-wave3-20261114/REPORT.md, candidate F20, "0DTE Long Premium Stop Geometry"), to a stop on the option premium, not on the underlying: arm A is the book's current registered invalidation (here, the fire's stamped underlying stop), and arm B is a flat minus 50 percent premium stop; the minus 30 percent level is refuted in the source as a disguised time stop. The re-examination (REEXAMINATION-POTENTIAL-EDGE.md, entry E22) carries no numeric levels beyond that, and states the geometry is graded through this redesign's fires. Two consequences, both computed below:

1. Arm A on an intraday path is computable from held underlying bars: walk 1Min bars, exit at the first bar touching the stamped stop or target, at intrinsic value at the touched level. This is the intraday-path half of the redesign and it ran (section A3).
2. Arm B is not computable on the estate's intrinsic basis, and no held intraday option marks exist to compute it on a premium basis. Intrinsic value at the entry price is 0.000 for all 21 fires (every long strike sits above its entry), so a minus 50 percent stop measured on intrinsic value is already breached at entry and grades nothing. On a true premium basis it needs intraday marks for the named spread contracts on 2026-11-12 and 2026-11-13; the only held option quotes for these contracts are the dry capture's single snapshot at the 2026-11-13 close basis, whose executable spread values (long bid minus short ask, Alpaca indicative) are negative on 5 of the 10 covered names (LITE -4.29, AXTI -0.30, ALAB -4.76, FCEL -0.05, ARM -1.16 against debits of 0.275 to 10.15), which is quote width, not a mark path. The gap is named per fire in section A4. Its sources, when they exist, are forward only: the production chain panel capture from Mon 2026-11-16 (which cannot backfill 2026-11-12), or the costed intraday tape decision the wave 3 report already surfaces (Databento OPRA or ORATS Live Intraday, owner decision, not purchased).

### A3. Intraday re-resolution of the covered subset: 10 of 21

Coverage: the desk 1Min cache holds files for LITE, AAOI, WDC, AXTI, ALAB, CRDO, FCEL, SNDK, ARM and MU, each spanning 2026-09-01 to 2026-11-13 (the DH3 widened window), so the full retired-basis window (sessions after the 2026-11-11 bar date through the last retired exit, 2026-11-13) is covered for all 10. These 10 are exactly the covered fires whose retired grade was STOPPED_OUT; the one retired TARGET_HIT (CLS) is in the uncovered set.

Method (conv_expression_intraday.py): 1Min bars in timestamp order; a bar whose low is at or below the stop is a stop touch, a bar whose high is at or above the target is a target touch, first touch wins, a bar touching both would be reported ambiguous (none occurred). Exit value is spread intrinsic at the touched level; the stop level sits below every long strike, so the stop exit value is 0.000 and realized R is -1.000 on the original resolver's risk denominator (debit minus value at stop), identical units to the retired basis. Three window conventions were run, because the registration does not fix one:

- Primary, like for like: the retired window (from 2026-11-12) at intraday granularity, all bars including premarket.
- RTH only: the same window restricted to 09:30 to 16:00 ET bars.
- Post-fire: from each fire's fired_at stamp on 2026-11-11 (secondary only; see the basis caveat below).

| Symbol | Retired basis | Primary intraday (from 2026-11-12) | RTH only | Post-fire 2026-11-11 (secondary) |
|---|---|---|---|---|
| LITE | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar 09:30 ET, -1.000R | STOPPED_OUT 14:26 ET, -1.000R |
| AAOI | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:26 ET, -1.000R |
| WDC | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:18 ET, -1.000R |
| AXTI | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:26 ET, -1.000R |
| ALAB | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 13:18 ET, -1.000R |
| CRDO | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:26 ET, -1.000R |
| FCEL | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, second bar 2026-11-12 04:01 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:25 ET, -1.000R |
| SNDK | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 15:11 ET, -1.000R |
| ARM | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 14:26 ET, -1.000R |
| MU | STOPPED_OUT 2026-11-12, -1.000R | STOPPED_OUT, first bar 2026-11-12 04:00 ET, -1.000R | STOPPED_OUT, first RTH bar, -1.000R | STOPPED_OUT 15:06 ET, -1.000R |

Headline: on the covered subset the intraday-path basis ties the retired basis exactly, 0 TARGET_HIT in 10 against the retired subset's 0 in 10, every fire at -1.000R, summed -4,245.00 dollars per contract on both bases for these 10. No covered fire touches its target before its stop under any of the three window conventions; nine of ten are already below their stop on the first bar of 2026-11-12, before the regular open. The diagnostic therefore does not kill the redesign outright (the registered test is the next 21 forward fires, and the single historical target hit, CLS, sits in the uncovered set), but it removes the in-sample version of the rescue story for the covered majority: on these fires the daily-close basis was not hiding intraday target touches, because there were none to hide, and finer granularity changes no outcome. What narrows: any remaining in-sample hope for the redesign rests on the 11 uncovered fires (section A5) and, separately, on the F20 premium arm, which this sample cannot evaluate at all (section A4).

Basis caveat on the secondary column: the fires' stamped entries do not reconcile to the 1Min cache close at the fired_at stamp (cache closes run 0.2 to 2.4 percent above the stamped entries across the 10, for example LITE stamped 659.91 against a cache close of 668.53 at its stamp), so same-day touches are printed as observations, not relied on. The primary and RTH columns do not depend on that reconciliation: they read the same sessions as the retired basis and test granularity only, and they agree with each other and with the retired basis on all 10.

### A4. The F20 premium arm: exact gap, all 21 fires

For every one of the 21 fires, the minus 50 percent premium stop (arm B) is NOT COMPUTABLE from held data. Missing asset, identical in kind for all 21: intraday option marks (bid and ask, or a traded premium series) for the fire's named spread (strikes and expiry in table A1) over 2026-11-12 to its exit, at any granularity. Where it would come from: a live chain capture during the holding window (the production chain panel starts Mon 2026-11-16 and is forward only), a TastyTrade or DXLink intraday capture made at the time (none was made for these contracts; the Ghost Book entry pricing of 2026-11-13 is a single delayed snapshot per fire, not a path), or the purchased intraday tape named in the wave 3 report (Databento OPRA, ORATS Live Intraday; an owner cost decision, not held). The morgue chain store holds SPY, QQQ and IWM only (DH4 census), so it carries none of these contracts at any date. This gap does not block the registered forward test, whose fires will live through windows the production panel captures; it blocks only this historical diagnostic's premium arm.

### A5. The uncovered 11: exact per-fire gap

Each fire below has no 1Min file in the desk cache (1Day.jsonl only), is not a Focus 30 name (so the DH3 widening never fetched it), and has no other held intraday underlying source per the route ledger above. Missing asset for each: 1Min (or finer) underlying bars for the holding window 2026-11-12 to the fire's retired exit date (2026-11-12 for all but VRT, 2026-11-13), of the same Alpaca SIP raw basis as the cache. Where it would come from: the same Alpaca bars route DH3 used (feed sip, adjustment raw, timeframe 1Min), run for these 11 symbols over 2026-11-11 to 2026-11-13; that is a fetch, not a purchase, and it is the one route tonight's scope (read the cache only) did not take.

| Symbol | Spread | Expiry | Retired basis | Missing window |
|---|---|---|---|---|
| NBIS | 157.5 / 165.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| SOXL | 68.0 / 73.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| IREN | 21.5 / 23.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| HIVE | 2.0 / 2.5 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| TSEM | 162.5 / 170.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| KEEL | 2.5 / 3.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| CLS | 247.5 / 255.0 | 2026-11-27 | TARGET_HIT 2026-11-12, +1.1065R | 1Min bars 2026-11-12 (the one fire whose intraday ordering of stop against target is still unobserved) |
| TTMI | 85.0 / 90.0 | 2026-12-18 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| CVNA | 74.0 / 76.0 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |
| VRT | 210.0 / 217.5 | 2026-11-27 | STOPPED_OUT 2026-11-13, -1.000R | 1Min bars 2026-11-12 to 2026-11-13 |
| USAR | 9.0 / 9.5 | 2026-11-27 | STOPPED_OUT 2026-11-12, -1.000R | 1Min bars 2026-11-12 |

CONV-19 note: the lens row inherits CONV-43 exactly. The lens itself stays a live signal source on its own grade (corpus pass 264 of 264); its expression remains blocked on the same redesigned-basis grade, and tonight's diagnostic moves that grade's in-sample expectation down without touching the forward test.

## PART B: CONV-41 AND CONV-42, C2 AND C6 SELL-THE-BAND CONSTRUCTIONS, PRE-READ

### B1. What is actually registered: no strikes, no expiry, no hurdle

register[31] (C2) and register[34] (C6) register one shared liability object, L = min(max(ST - K1, 0), K2 - K1) per share, terminal P and L of c minus L before costs for C6 (C2 adds the held stock leg), one trial charged jointly, and a first read of Tue 2026-11-17, coverage and executability only. Neither register row names an underlying, a strike, an expiry, or a premium figure. Their sources agree: C2C6-RUNFILE.md section 5 leaves the strike family (K1 as a moneyness offset, K2 as a width above K1) and the expiry family (a horizon band) to a development lock addendum, and the addendum as filed (C2C6-LOCK-ADDENDUM-2026-11-15.md, section 2) dispositions them NAMED UNSET: P01 strike-selection rule NAMED UNSET, P02 expiry-selection rule NAMED UNSET, P03 C6 put comparator strike family NAMED UNSET, P05 conditioning field list and minimum event count NAMED UNSET, P06 credit threshold NAMED UNSET (no numeric minimum surplus beyond the registered claim inequality, c exceeds E[L | I] plus all costs, exists in any source), P07 fee schedule NAMED UNSET. The addendum's consequence rule is explicit: until a further dated addendum sets P01 and P02 from development data only, no spread in this study is specified at strike level, and no credit-versus-liability read is lawful for any leg. The universes are set (P10, P13: flag archives, not named names), and no specific flag event has been selected as a decision event for either construction in any file read tonight.

Consequence for tonight's step 2 and step 3 as tasked: there is no registered underlying, K1, K2, or expiry to look up in the panel, and no registered premium hurdle to test a computed c against. That branch of the task does not trigger, not because the panel failed, but because the construction does not yet exist at strike level. What a pre-read can lawfully establish tonight is panel-level coverage and executability surface, which is section B2.

### B2. Panel pre-read on the held Focus chain panel (PRE-READ, not the Tue read)

Source: the DH4 dry capture store (~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave4/dry_capture/store/), one session dated 2026-11-14, spot basis the 2026-11-13 close, 31 underlyings, 115,718 contracts in the snapshot store and 27,405 quote-carrying rows in its iv_ledger_modelled.jsonl (quote_bid, quote_ask, quote_mid on every ledger row). Two standing cautions from the runfile itself (section 8, item 2, and section 10): this capture is a forced dry run outside the close window, excluded from history and from any efficacy claim; tonight's use is existence and coverage only, the same mechanism-proof use the runfile records. The Tue 2026-11-17 decisive read runs on the production capture, not on this file.

Quote-carrying coverage, per underlying (ledger rows; calls are the C2 and C6 short-band leg type):

| Underlying | Spot (2026-11-13 close) | Quote rows | Call rows | Expiries | Call strikes in band |
|---|---|---|---|---|---|
| SMH | 486.75 | 1,420 | 612 | 13, 2026-11-16 to 2027-02-19 | 76, 370.0 to 605.0 |
| SOXX | 149.30 | 893 | 419 | 9, 2026-11-20 to 2027-02-19 | 96, 113.33 to 185.0 |
| NVDA | 162.85 | 747 | 371 | 13, 2026-11-16 to 2027-02-19 | 79, 123.0 to 202.5 |
| AVGO | 347.01 | 1,027 | 502 | 13, 2026-11-16 to 2027-02-19 | 68, 262.5 to 432.5 |
| AMD | 534.06 | 1,559 | 789 | 13, 2026-11-16 to 2027-02-19 | 107, 402.5 to 667.5 |
| MRVL | 156.76 | 404 | 202 | 9, 2026-11-20 to 2027-02-19 | 45, 120.0 to 195.0 |
| ARM | 190.53 | 391 | 198 | 9, 2026-11-20 to 2027-02-19 | 42, 143.0 to 235.0 |
| TSM | 398.73 | 640 | 331 | 9, 2026-11-20 to 2027-02-19 | 58, 300.0 to 495.0 |
| AMAT | 370.50 | 636 | 318 | 9, 2026-11-20 to 2027-02-19 | 60, 280.0 to 460.0 |
| MU | 778.31 | 1,894 | 952 | 13, 2026-11-16 to 2027-02-19 | 115, 585.0 to 970.0 |
| SNDK | 885.01 | 1,230 | 614 | 9, 2026-11-20 to 2027-02-19 | 94, 665.0 to 1105.0 |
| WDC | 295.65 | 487 | 239 | 8, 2026-11-20 to 2027-01-15 | 53, 225.0 to 365.0 |
| AAOI | 49.89 | 356 | 178 | 9, 2026-11-20 to 2027-02-19 | 32, 38.0 to 62.0 |
| COHR | 218.15 | 432 | 216 | 9, 2026-11-20 to 2027-02-19 | 42, 165.0 to 270.0 |
| LITE | 596.62 | 924 | 461 | 9, 2026-11-20 to 2027-02-19 | 75, 450.0 to 745.0 |
| CRDO | 131.51 | 363 | 182 | 9, 2026-11-20 to 2027-02-19 | 52, 100.0 to 162.5 |
| ALAB | 221.83 | 400 | 200 | 8, 2026-11-20 to 2027-01-15 | 44, 167.5 to 275.0 |
| AXTI | 41.84 | 327 | 163 | 9, 2026-11-20 to 2027-02-19 | 35, 32.0 to 52.0 |
| CRWV | 53.13 | 412 | 206 | 9, 2026-11-20 to 2027-02-19 | 41, 40.0 to 66.0 |
| PLTR | 167.99 | 316 | 162 | 9, 2026-11-20 to 2027-02-19 | 30, 130.0 to 207.5 |
| RKLB | 61.53 | 369 | 188 | 8, 2026-11-20 to 2027-01-15 | 34, 46.5 to 76.0 |
| FLNC | 4.68 | 16 | 8 | 4, 2026-11-20 to 2027-02-19 | 2, 4.0 to 5.0 |
| EOSE | 1.91 | 34 | 17 | 9, 2026-11-20 to 2027-02-19 | 2, 1.5 to 2.0 |
| FCEL | 9.68 | 136 | 69 | 8, 2026-11-20 to 2027-01-15 | 10, 7.5 to 12.0 |
| BE | 191.99 | 397 | 198 | 9, 2026-11-20 to 2027-02-19 | 40, 145.0 to 237.5 |
| OKLO | 23.92 | 193 | 94 | 8, 2026-11-20 to 2027-01-15 | 22, 18.0 to 29.0 |
| VST | 133.01 | 608 | 291 | 9, 2026-11-20 to 2027-02-19 | 53, 100.0 to 165.0 |
| CEG | 280.20 | 403 | 201 | 9, 2026-11-20 to 2027-01-15 | 43, 215.0 to 350.0 |
| XLE | 64.96 | 529 | 226 | 12, 2026-11-16 to 2027-01-15 | 45, 49.5 to 80.0 |
| SPY | 754.37 | 4,997 | 2,082 | 19, 2026-11-16 to 2027-02-26 | 277, 570.0 to 940.0 |
| QQQ | 679.89 | 4,865 | 2,051 | 18, 2026-11-16 to 2027-02-19 | 267, 510.0 to 849.0 |

Panel-level findings, stated as coverage facts only:
1. Presence: quote-carrying call rows exist for 31 of 31 panel underlyings, 12,740 call rows in total, inside the collector enrichment scope (expiries within 120 days, moneyness 0.75 to 1.25 of spot). No panel underlying is absent, so a future locked band family will have a quote surface to be tested against on every panel name, subject to finding 3.
2. Expiry surface: the first listed expiry in the ledger is 2026-11-16 for the index and weekly names (AMD, AVGO, MU, NVDA, SMH, XLE, SPY, QQQ) and 2026-11-20 for the remaining single names; the surface runs to 2027-01-15 or 2027-02-19 (SPY 2027-02-26). Any horizon band a later addendum locks inside roughly 1 to 100 days has listed expiries on this surface.
3. Thin names: FLNC (8 call rows, 2 call strikes) and EOSE (17 call rows, 2 call strikes) cannot span any two-strike band above spot inside the enrichment band on this capture (their only call strikes sit at or below spot: FLNC 4.0 and 5.0 against spot 4.68, EOSE 1.5 and 2.0 against spot 1.91, so at most one strike sits above spot on each). FCEL is thin but spanned (10 call strikes, 7.5 to 12.0 against spot 9.68). If a flagged decision event ever lands on FLNC or EOSE, its expected cohort on this evidence is the runfile's missing-options reason "no listed strikes spanning the locked family", subject to re-check on the production capture.
4. Quote quality limit, printed because it bounds any future executability read: the ledger quotes are Alpaca indicative, and on this capture they are wide enough that 5 of the 10 Ghost Book spreads in Part A showed negative executable value at the same snapshot basis. Presence of a quote row is therefore coverage, not proof of an executable credit at a useful price; the Tue read's executability leg has to grade width and crossed state per leg, exactly as the runfile's reason codes provide (quote missing or crossed for either leg).
5. Manifest exceptions already on record for this capture (DH4): WDC and FCEL each carry 2 error lines from earlier attempts in the same run (a chain item count ValueError and an OCC parse ValueError) and then stored ok in the same run; the collector excludes adjusted chain items (observed on WDC and FCEL), which is the runfile's "adjusted only" cohort route if a needed contract ever exists only in adjusted form.

### B3. Per-construction verdicts

| Row | Construction | Priced on held panel? | Hurdle test | Exact remaining gap |
|---|---|---|---|---|
| CONV-41 | C2, sell the band against a held recovery stock | No, and not priceable: no registered underlying, K1, K2, or expiry exists | Not runnable: P06 NAMED UNSET, no numeric hurdle; the registered claim c exceeds E[L \| I] plus costs also needs E[L \| I], which needs P01, P02 and P05 set and a development survival curve fitted, none of which exists | (1) A further dated lock addendum setting P01 (strike offsets), P02 (expiry band) and P05 from development data only; (2) a named C2 decision event from the P10 flag archives; (3) the Mon 2026-11-16 16:46 ET production capture, then the Tue 2026-11-17 coverage and executability read as registered. Panel coverage itself is not a gap: section B2. |
| CONV-42 | C6, sell the band on bearish-flagged names, no stock | No, identically: the shared liability object has no strike-level specification | Not runnable, identically (P06 NAMED UNSET; P03 put comparator family also NAMED UNSET) | Identical to CONV-41, with the P13 bearish flag archives as the decision-event source and P03 additionally unset for the put comparator leg. One trial stays charged jointly for the cell, as registered. |

## STATUS LINES

- CONV-43 (with CONV-19): PARTIAL. The intraday-path diagnostic is computed on 10 of 21 fires and ties the retired basis exactly (0 target hits in 10, all -1.000R, no target touch before any stop under three window conventions), which narrows the redesign's in-sample case to the 11 uncovered fires and to forward data; the F20 premium arm and the 11 non-Focus fires carry the exact gaps in sections A4 and A5. The registered decisive test (next 21 forward fires, settlement reruns after 2026-11-27 and 2026-12-18) is untouched and still governs. Evidence pointer: sections A1 to A5 of this file, conv_expression_intraday.py with conv_expression_intraday_results.json (post-fire walk) and conv_expression_intraday_variants.py with conv_expression_intraday_variants.json (primary and RTH walks) in this directory.
- CONV-41 and CONV-42: PARTIAL. The coverage pre-read is computed (31 of 31 panel underlyings carry quote rows; FLNC and EOSE named as unspannable on this capture), and the pricing branch is closed with its exact reason: no registered strike family, expiry family, decision event, or premium hurdle exists (lock addendum rows P01, P02, P03, P05, P06, P07 NAMED UNSET), so no premium c and no hurdle verdict can be computed tonight by any route on held data. The registered decisive read stays Tue 2026-11-17 on the Mon 2026-11-16 production capture. Evidence pointer: sections B1 to B3 of this file, C2C6-RUNFILE.md and C2C6-LOCK-ADDENDUM-2026-11-15.md in ~/workspace/research_notes/six-constructions-20261115/, and the DH4 census in this directory.
