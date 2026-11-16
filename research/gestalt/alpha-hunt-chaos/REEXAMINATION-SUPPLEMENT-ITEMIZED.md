# REEXAMINATION SUPPLEMENT: ITEMIZED ROWS

Built Sun 2026-11-15 in answer to the owner's challenge: "I doubt you rechecked everything that fast." The doubt was well aimed at granularity. The Reexamination covered the corpus at source granularity: 735 reads, named items individually, register populations in named counted classes. This supplement itemizes the five class-covered populations from their own registers, one row per item, each row carrying only its own register's numbers.

## Method statement (read this first)

Every row in this supplement was generated mechanically by one script, `build_supplement_itemized.py`, in this directory, from the five named source registers. No row was written by hand. No field was invented: a field a register does not carry prints as NOT-IN-REGISTER in the rows file. Tiers are assigned by the mechanical rules stated below, from register fields only. The full row set lives in `REEXAMINATION-SUPPLEMENT-ROWS.jsonl` (26,723 rows, counted back after generation). This markdown carries the method, the coverage table reconciling every count, the tier censuses, and the lead and flagged rows in full.

Tier rules, cited:
- Sweep rows (S1): Lane 7's separator rule, fixed before its results were read (panel: n of at least 30, nights of at least 4, absolute nightly-cluster t of at least 3, BH q of at most 0.10 within family; forecast: n of at least 20, q of at most 0.10). A row with separates true would tier SEPARATOR; the register contains zero. Lane 7's named leads (its section 4 list plus the forecast midday slot, its section 5) tier LEAD after the generator verified each against the register row's own n and mean (all 9 matched; zero mismatches). UNGRADABLE-YET is carried exactly where Lane 7's register graded it so. Block A's route statuses (GRADED-VIA-PANEL and kin) carry as their own tier labels.
- Campaign rows (S2): the campaign's own sealed funnel dispositions. Survivor true advances; a scored row (DSR present) tiers SCORED-NO-SURVIVAL; a stage 1 fail tiers STAGE1-FAIL; the rest tier by the register's own stage 2 reason string.
- Board rows (S3): the board's own state class is the tier, per the Reexamination's sleeve treatment.
- Pairs (S4): Lane 6's own marks, decoded E examined, E* examined-unresolved, C co-read, N never examined, with Lane 7's sweep status carried beside each.
- Triples (S4): Lane 6's printed mark for all 48 is NEVER EXAMINED, with two partial exceptions that are constructions or practices, not examinations.
- Prototype rows (S5): REGISTERED-NOT-EVALUATED. Lane 2's own record states the prototype proved generation only; no prototype candidate was ever evaluated.

## Coverage table (reconciled against each register's own count)

| Section | Source register | Source count | Rows generated | Delta |
|---|---|---|---|---|
| S1 sweep cells | GESTALT-SWEEP-REGISTER.jsonl | 24,517 lines | 24,517 | 0 |
| S2 campaign candidates | CAMPAIGN1-REGISTER.jsonl | 2,403 lines = 1 header + 1,200 candidates + 1,200 evaluations + 1 peek + 1 cohort summary | 1,200 (candidate joined to its evaluation on trial_index) | 0 |
| S3 board sleeves | execution_board.csv | 340 lines = header + 339 | 339 | 0 |
| S4 Lane 6 pairs | LANE6-GESTALT-FULL.md full pair enumeration | 561 printed | 561 | 0 |
| S4 Lane 6 triples | LANE6-GESTALT-FULL.md triples section | 48 screened | 6 individually named in print + 42 named remainder (see below) | 42 unitemizable, reason printed |
| S5 prototype candidates | prototype_candidates.jsonl | 100 lines | 100 | 0 |
| Total itemized rows | | | 26,723 | |

Cross-checks run by the generator, all passing unless named in the discrepancies section:
- Sweep tier census reconciles exactly to Lane 7's printed status accounting: GRADED 4,289 (4,279 no-separation + 9 leads + 1 control), LOW-N 8,537, EMPTY 5,105, UNGRADABLE-YET 6,522, GRADED-VIA-PANEL 41, GRADED-VIA-FORECAST 1, GRADED-VIA-CONTROL-LINE 1, EXAMINED-NOT-GRADED 11, CO-READ-NOT-GRADED 4, CURATED-SCREENED-NOT-GRADED 6. Sum 24,517.
- All 9 Lane 7 named leads matched a register row on block, horizon, n and mean excess. Zero mismatches.
- All 561 Lane 6 pairs matched the sweep register's Block A rows on mark and seat probability. Zero mismatches.
- Campaign funnel reconciles exactly to CAMPAIGN1-VERDICT.md: stage 1 fails 1,078 (no parent event stream 691, near-miss feed has no symbol/side/price 154, expression not priceable 104, gate blocked set unpriceable 94, byte duplicate 35); stage 2 of the 122 passes: engine-required 57 (register reason: signal generation operator not evaluable from event stream), insufficient 59, data-fail 4 (universe random 1, universe inverse 3), scored 2, survivors 0.
- Board class counts as read from the CSV itself at generation: LIVE-FIRING 68, FIXTURE-PROVEN 37, ARMED-PROVEN 231, UNFED 2, DEFECT 1. Sum 339.

## Discrepancies (printed, none smoothed)

- D-SP1, triples remainder: Lane 6 screened 48 curated triples, but only 6 are individually named anywhere in print (the seat's top 5, plus the A01xA10xA08 construction exception). The full list with individual probabilities was stated to live in Lane 6's run record; the searches recorded here (LANE6-GESTALT-FULL.md full text, gestalt_audit_ledger.jsonl, which carries run metadata only, the typed-layer ledger.jsonl, and a workspace-wide filename and content search for the named triple codes) found no persisted per-triple record. The remaining 42 triples therefore cannot be itemized without inventing their identities, which this supplement does not do. What print does carry for all 48: the mark NEVER EXAMINED (two partial exceptions noted on their rows), and the seat probability range 0.28 to 0.57. Lane 6's own axis space beyond the curated 48 is not lost: the sweep register's Block A carries all 5,984 axis triples, itemized in section S1.
- D-SP2, campaign candidate ids: the register carries 1,200 candidate records under 1,165 unique candidate_ids; the 35 byte-duplicates share their original's id. The generator's first pass joined on candidate_id and silently collapsed 35 rows; caught in this pass's reconciliation, cured by joining on trial_index, and the register's own counts now reconcile exactly. Recorded because a supplement about not missing things should show its own near-miss.
- D-SP3, board counts moved: the CSV's class counts at generation (68 / 37 / 231 / 2 / 1) differ from the Sat 2026-11-14 night summary carried in other files (65 / 38 / 233 / 1 / 2). The CSV is the register of record and carries Sun 2026-11-15 fresh checks inside its own evidence fields; its counts govern here. The difference is a board update between the two reads, printed so nobody reconciles against the stale summary.
- D-SP4, prototype aggregates: Lane 2's printed summary of its own prototype says 90 distinct parents and 168 operator applications. The register file itself carries 93 distinct parent names across 104 parent slots and 164 operator applications. The rows in S5 carry the register's fields; the summary prose and the register disagree, and the register governs. No field in the register derives Lane 2's 90 or 168.

## Tier censuses

S1 sweep (24,517): GRADED-NO-SEPARATION 4,279; LEAD 9; GRADED-CONTROL-SEPARATES-FROM-ZERO-PER-REGISTER-NOTE 1; LOW-N-BELOW-REPORTING-FLOOR 8,537; EMPTY-N0-CELL-NEVER-OCCURRED 5,105; UNGRADABLE-YET 6,522; GRADED-VIA-PANEL 41; GRADED-VIA-FORECAST 1; GRADED-VIA-CONTROL-LINE 1; EXAMINED-NOT-GRADED 11; CO-READ-NOT-GRADED 4; CURATED-SCREENED-NOT-GRADED 6. SEPARATOR 0.

S2 campaign (1,200): STAGE1-FAIL 1,078; STAGE2-INSUFFICIENT 59; STAGE2 engine-required 57; STAGE2 data-fail 4; SCORED-NO-SURVIVAL 2; SURVIVOR 0.

S3 board (339): LIVE-FIRING 68; FIXTURE-PROVEN 37; ARMED-PROVEN 231; UNFED 2; DEFECT 1.

S4 pairs (561): NEVER-EXAMINED 545; EXAMINED 11; EXAMINED-UNRESOLVED 1; CO-READ 4.

S5 prototype (100): REGISTERED-NOT-EVALUATED 100 (59 in novelty cells empty in the parent fleet).

## Flagged rows in full
### Flagged: Lane 7 named leads and the separating control (10 rows)

| row | block | combo | horizon | n | nights | mean_exc_bp | hit_rate | t_night | q_bh | tier |
|---|---|---|---|---|---|---|---|---|---|---|
| SW-00323 | P | VOLR=NORMxDAY=FLAT | overnight | 35 | 6 | 53.4 | 0.5714 | 3.038 | 0.9998 | LEAD |
| SW-06463 | P | DAY=UPxPOS10=MID | fwd1 | 40 | 7 | 42.88 | 0.575 | 3.256 | 0.995 | LEAD |
| SW-11861 | P | RSI=OS | fwd5 | 32 | 4 | 521.37 | 0.8125 | 3.09 | 0.6905 | LEAD |
| SW-11872 | P | VOLR=HEAVY | fwd5 | 70 | 4 | 268.49 | 0.6714 | 3.393 | 0.6905 | LEAD |
| SW-11900 | P | RSI=OSxMACD=BEAR- | fwd5 | 31 | 4 | 527.49 | 0.8065 | 3.165 | 0.715 | LEAD |
| SW-11937 | P | RSI=OSxRS10=WEAK | fwd5 | 30 | 4 | 532.65 | 0.8 | 3.007 | 0.715 | LEAD |
| SW-12047 | P | RSI=HIGHxPOS10=MID | fwd5 | 34 | 3 | 144.04 | 0.5 | 10.012 | 0.715 | LEAD |
| SW-12071 | P | MACD=BULL+xRS10=STRONG | fwd5 | 51 | 3 | 146.52 | 0.6078 | 3.364 | 0.715 | LEAD |
| SW-17791 | F | slot=midday | - | 61 | - | - | 0.9016 | - | 0.1881 | LEAD |
| SW-17931 | M | anti_midna_sign (A29) overnight, C-1 founding measurement | - | 58 | - | - | - | - | - | GRADED-CONTROL-SEPARATES-FROM-ZERO-PER-REGISTER-NOTE |

### Flagged: Block M, all rows (9)

| row | combo | n | status | tier | note |
|---|---|---|---|---|---|
| SW-17930 | book_resolved_trades_pooled | 4 | LOW-N | LOW-N-BELOW-REPORTING-FLOOR | 4 resolved book trades, all losses, total $-2460.13; singles/pairs/triples of trade-level gestalt states ungradable at n=4 |
| SW-17931 | anti_midna_sign (A29) overnight, C-1 founding measurement | 58 | GRADED | GRADED-CONTROL-SEPARATES-FROM-ZERO-PER-REGISTER-NOTE | anti-Midna positions: mean +268.80bp (t 4.37); equal-weight fade-everything control +272.13bp; selection excess -3.33bp. Source: ANTI-MIDNA-CONTROL-LINE-SPEC-2026-11-15 (research_notes/decisions-api-leverage-20261114/conversion/). The anti portfolio separates from zero; Midna selection does not separate from the anti control. |
| SW-17932 | anti_midna forward cohort (frozen 2026-11-13 close, 29 names, 28 short bias) | 0 | UNGRADABLE-YET | UNGRADABLE-YET | overnight read lands Mon 2026-11-16, 5-session read Fri 2026-11-20, inside the night study control line block. Accrual wiring exists (control line step in the night study body). |
| SW-17933 | ghost_book expressions (J03 family) | 0 | UNGRADABLE-YET | UNGRADABLE-YET | 21 Tensor fires priced, 0 resolved. Wiring: Lane 8 expression shadow-ledger resolver, build priority one, not built. |
| SW-17934 | pattern_ledger continuation (A10 family) | 0 | UNGRADABLE-YET | UNGRADABLE-YET | 35 pattern records posed; continuation resolutions pending on 70 of 70 checks (Lane 3 count). Wiring: pattern panel resolver runs at 5/10-session horizons. |
| SW-17935 | section11 self-audit leg census (I-family) | 0 | UNGRADABLE-YET | UNGRADABLE-YET | selfaudit_resolutions.jsonl is empty (0 bytes of resolutions); no completed leg census on record. Wiring: resolve_selfaudit.py plus the four-week census. |
| SW-17936 | ledger_vs_surface | 0 | UNGRADABLE-YET | UNGRADABLE-YET | 9,491 sealed held-out forecast rows grade Thu 2026-11-19; Lens page due the same day. |
| SW-17937 | desk sleeve outcomes x gestalt states | 0 | UNGRADABLE-YET | UNGRADABLE-YET | desk journals carry no symbols on intent records (Lane 3); INTENT-LOG-FIELDS cure landed 2026-11-15 (commit 87a3956) so accrual starts Mon 2026-11-16; first gradable census after a full session population accrues. |
| SW-17938 | forecast_twin book-record status | 0 | UNGRADABLE-YET | UNGRADABLE-YET | the book own resolver (resolve_forecast_twin.py) has never run; all 37 poses stand pending in FORECAST-TWIN-RECORDS.md. Sweep-side resolutions live in Block T of this register and do not amend the book record. |

### Flagged: Block T, all rows (11)

| row | combo | n | event_rate | mean_p | brier | hit_rate | status | tier |
|---|---|---|---|---|---|---|---|---|
| SW-17919 | twin_pooled | 37 | 0.7297 | 0.6959 | 0.2165 | - | GRADED | GRADED-NO-SEPARATION |
| SW-17920 | twin_bucket=p<0.6 | 13 | 0.6923 | 0.4446 | 0.3013 | - | GRADED | GRADED-NO-SEPARATION |
| SW-17921 | twin_bucket=p0.6-0.8 | 10 | 0.5 | 0.677 | 0.3045 | - | GRADED | GRADED-NO-SEPARATION |
| SW-17922 | twin_bucket=p0.8-0.95 | 5 | 1.0 | 0.876 | 0.0167 | - | LOW-N | LOW-N-BELOW-REPORTING-FLOOR |
| SW-17923 | twin_bucket=p>=0.95 | 9 | 0.8889 | 0.98 | 0.1072 | - | LOW-N | LOW-N-BELOW-REPORTING-FLOOR |
| SW-17924 | midna_pooled | 37 | - | - | - | 0.8108 | GRADED | GRADED-NO-SEPARATION |
| SW-17925 | midna_conf=low | 7 | - | - | - | 0.7143 | LOW-N | LOW-N-BELOW-REPORTING-FLOOR |
| SW-17926 | midna_conf=medium | 21 | - | - | - | 0.8571 | GRADED | GRADED-NO-SEPARATION |
| SW-17927 | midna_conf=high | 5 | - | - | - | 1.0 | LOW-N | LOW-N-BELOW-REPORTING-FLOOR |
| SW-17928 | pair=twin_midna_agree (midna graded) | 29 | - | - | - | 0.8276 | GRADED | GRADED-NO-SEPARATION |
| SW-17929 | pair=twin_midna_disagree (midna graded) | 8 | - | - | - | 0.75 | LOW-N | LOW-N-BELOW-REPORTING-FLOOR |

### Flagged: Block A rows graded via a route (43)

| row | combo | lane7 status (tier) | lane6 mark | lane6 seat p |
|---|---|---|---|---|
| SW-17941 | A03 RSI | GRADED-VIA-PANEL | - | - |
| SW-17942 | A04 MACD | GRADED-VIA-PANEL | - | - |
| SW-17943 | A05 SMA stack | GRADED-VIA-PANEL | - | - |
| SW-17946 | A08 volume state | GRADED-VIA-PANEL | - | - |
| SW-17947 | A09 level proximity | GRADED-VIA-PANEL | - | - |
| SW-17949 | A11 RS line | GRADED-VIA-PANEL | - | - |
| SW-17965 | A27 decision slot | GRADED-VIA-FORECAST | - | - |
| SW-17967 | A29 anti-Midna sign | GRADED-VIA-CONTROL-LINE | - | - |
| SW-18038 | A03xA04 RSI x MACD | GRADED-VIA-PANEL | N | 0.69 |
| SW-18039 | A03xA05 RSI x SMA stack | GRADED-VIA-PANEL | N | 0.6 |
| SW-18042 | A03xA08 RSI x volume state | GRADED-VIA-PANEL | N | 0.7 |
| SW-18043 | A03xA09 RSI x level proximity | GRADED-VIA-PANEL | N | 0.73 |
| SW-18045 | A03xA11 RSI x RS line | GRADED-VIA-PANEL | N | 0.61 |
| SW-18069 | A04xA05 MACD x SMA stack | GRADED-VIA-PANEL | N | 0.69 |
| SW-18072 | A04xA08 MACD x volume state | GRADED-VIA-PANEL | N | 0.69 |
| SW-18073 | A04xA09 MACD x level proximity | GRADED-VIA-PANEL | N | 0.71 |
| SW-18075 | A04xA11 MACD x RS line | GRADED-VIA-PANEL | N | 0.67 |
| SW-18101 | A05xA08 SMA stack x volume state | GRADED-VIA-PANEL | N | 0.75 |
| SW-18102 | A05xA09 SMA stack x level proximity | GRADED-VIA-PANEL | N | 0.77 |
| SW-18104 | A05xA11 SMA stack x RS line | GRADED-VIA-PANEL | N | 0.71 |
| SW-18183 | A08xA09 volume state x level proximity | GRADED-VIA-PANEL | E | 0.73 |
| SW-18185 | A08xA11 volume state x RS line | GRADED-VIA-PANEL | N | 0.67 |
| SW-18210 | A09xA11 level proximity x RS line | GRADED-VIA-PANEL | N | 0.7 |
| SW-19558 | A03xA04xA05 RSI x MACD x SMA stack | GRADED-VIA-PANEL | - | - |
| SW-19561 | A03xA04xA08 RSI x MACD x volume state | GRADED-VIA-PANEL | - | - |
| SW-19562 | A03xA04xA09 RSI x MACD x level proximity | GRADED-VIA-PANEL | - | - |
| SW-19564 | A03xA04xA11 RSI x MACD x RS line | GRADED-VIA-PANEL | - | - |
| SW-19590 | A03xA05xA08 RSI x SMA stack x volume state | GRADED-VIA-PANEL | - | - |
| SW-19591 | A03xA05xA09 RSI x SMA stack x level proximity | GRADED-VIA-PANEL | - | - |
| SW-19593 | A03xA05xA11 RSI x SMA stack x RS line | GRADED-VIA-PANEL | - | - |
| SW-19672 | A03xA08xA09 RSI x volume state x level proximity | GRADED-VIA-PANEL | - | - |
| SW-19674 | A03xA08xA11 RSI x volume state x RS line | GRADED-VIA-PANEL | - | - |
| SW-19699 | A03xA09xA11 RSI x level proximity x RS line | GRADED-VIA-PANEL | - | - |
| SW-20025 | A04xA05xA08 MACD x SMA stack x volume state | GRADED-VIA-PANEL | - | - |
| SW-20026 | A04xA05xA09 MACD x SMA stack x level proximity | GRADED-VIA-PANEL | - | - |
| SW-20028 | A04xA05xA11 MACD x SMA stack x RS line | GRADED-VIA-PANEL | - | - |
| SW-20107 | A04xA08xA09 MACD x volume state x level proximity | GRADED-VIA-PANEL | - | - |
| SW-20109 | A04xA08xA11 MACD x volume state x RS line | GRADED-VIA-PANEL | - | - |
| SW-20134 | A04xA09xA11 MACD x level proximity x RS line | GRADED-VIA-PANEL | - | - |
| SW-20513 | A05xA08xA09 SMA stack x volume state x level proximity | GRADED-VIA-PANEL | - | - |
| SW-20515 | A05xA08xA11 SMA stack x volume state x RS line | GRADED-VIA-PANEL | - | - |
| SW-20540 | A05xA09xA11 SMA stack x level proximity x RS line | GRADED-VIA-PANEL | - | - |
| SW-21594 | A08xA09xA11 volume state x level proximity x RS line | GRADED-VIA-PANEL | - | - |

### Flagged: Campaign 1 scored candidates (2 rows)

| row | trial | candidate | parents | operators | family | n_events | n_days | mean_daily_excess_bp | t_clustered | p | q | sr_daily | dsr | survivor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1-0147 | 147 | MUT-1be9175ea843 | aster_etf_qqq_monthly_c098 | INVERT_SIGNAL | adapters3 | 46 | 8 | -1.61 | -0.008 | 0.9942014364119284 | 0.9942 | -0.0027 | 0.0 | False |
| C1-0307 | 307 | MUT-529febfb3aac | aster_etf_qqq_monthly_c098 | BOLT_RANDOM_VARIABLE | adapters3 | 10 | 4 | -83.49 | -2.929 | 0.06105730843760212 | 0.1221 | -1.4644 | 0.0 | False |

### Flagged: board DEFECT and UNFED rows (3)

| row | sleeve | state (tier) | cure_id | trigger_or_blocker | evidence_pointer |
|---|---|---|---|---|---|
| BD-054 | aster_open_gamma_a | UNFED | FEED80-OPENING | SOLVE-IN-FLIGHT: everything buildable is built (R5 chain live; dual-feed quote pattern: delayed SIP authoritative, IEX sanity/abort only). The computed-delta question is POSED to the Triad as a decision (dead drop marker midna-inbox:2026-11-14-clear-the-board-asks; no votes by close); in-window live proof is Mon 2026-11-16's session by nature and is registered as the dated proof event. | grokbot-inbox/INBOX.md marker midna-inbox:2026-11-14-clear-the-board-asks; CLEAR-THE-BOARD-2026-11-14.md |
| BD-055 | aster_open_gamma_b | UNFED | FEED80-OPENING | SOLVE-IN-FLIGHT: everything buildable is built (R5 chain live; dual-feed quote pattern: delayed SIP authoritative, IEX sanity/abort only). The computed-delta question is POSED to the Triad as a decision (dead drop marker midna-inbox:2026-11-14-clear-the-board-asks; no votes by close); in-window live proof is Mon 2026-11-16's session by nature and is registered as the dated proof event. | grokbot-inbox/INBOX.md marker midna-inbox:2026-11-14-clear-the-board-asks; CLEAR-THE-BOARD-2026-11-14.md |
| BD-163 | bb_rsi_divergence | DEFECT | CR-4 | SOLVE-IN-FLIGHT: ballot-owed. Freshness cure (latest-completed-RTH-bar semantics) lands on a second Triad YES; tally 1 of 3 (Midna YES); chase 3 posted and read back in the dead drop (marker midna-inbox:2026-11-14-clear-the-board-asks); no ballots arrived by close; hard deadline Fri 2026-11-20 B5. Concurrency-cap half landed 2026-11-12. | grokbot-inbox/INBOX.md marker midna-inbox:2026-11-14-clear-the-board-asks; CLEAR-THE-BOARD-2026-11-14.md |

### Flagged: Lane 6 pairs carrying an E, E* or C mark (16 rows)

| row | pair | mark | decoded | lane6 seat p | Lane 7 sweep status |
|---|---|---|---|---|---|---|
| PR-A01xA10 | A01xA10 | C | CO-READ | 0.51 | CO-READ-NOT-GRADED |
| PR-A01xA18 | A01xA18 | E | EXAMINED | 0.59 | EXAMINED-NOT-GRADED |
| PR-A02xA18 | A02xA18 | E | EXAMINED | 0.5 | EXAMINED-NOT-GRADED |
| PR-A02xA29 | A02xA29 | E | EXAMINED | 0.46 | EXAMINED-NOT-GRADED |
| PR-A02xA30 | A02xA30 | C | CO-READ | 0.5 | CO-READ-NOT-GRADED |
| PR-A08xA09 | A08xA09 | E | EXAMINED | 0.73 | GRADED-VIA-PANEL |
| PR-A08xA10 | A08xA10 | E | EXAMINED | 0.72 | EXAMINED-NOT-GRADED |
| PR-A09xA26 | A09xA26 | E | EXAMINED | 0.71 | EXAMINED-NOT-GRADED |
| PR-A12xA13 | A12xA13 | E* | EXAMINED-UNRESOLVED | 0.57 | EXAMINED-NOT-GRADED |
| PR-A12xA14 | A12xA14 | C | CO-READ | 0.71 | CO-READ-NOT-GRADED |
| PR-A13xA14 | A13xA14 | C | CO-READ | 0.68 | CO-READ-NOT-GRADED |
| PR-A17xA24 | A17xA24 | E | EXAMINED | 0.54 | EXAMINED-NOT-GRADED |
| PR-A21xA24 | A21xA24 | E | EXAMINED | 0.82 | EXAMINED-NOT-GRADED |
| PR-A22xA24 | A22xA24 | E | EXAMINED | 0.8 | EXAMINED-NOT-GRADED |
| PR-A23xA24 | A23xA24 | E | EXAMINED | 0.77 | EXAMINED-NOT-GRADED |
| PR-A24xA31 | A24xA31 | E | EXAMINED | 0.73 | EXAMINED-NOT-GRADED |

### Flagged: Lane 6 triples individually named in print (6 rows)

| row | triple | axis names | lane6 seat p | tier | exception note |
|---|---|---|---|---|---|
| TR-A32xA15xA18 | A32xA15xA18 | breadth x regime x lens consensus | 0.57 | NEVER-EXAMINED | - |
| TR-A22xA23xA24 | A22xA23xA24 | event x IV x expression | 0.49 | NEVER-EXAMINED | partial exception per Lane 6: the playbook earnings expression, examined as a practice, never graded as a joint state |
| TR-A19xA20xA02 | A19xA20xA02 | Echo x engine agreement x Pass B | 0.49 | NEVER-EXAMINED | - |
| TR-A31xA18xA24 | A31xA18xA24 | wave fire x lens x expression | 0.47 | NEVER-EXAMINED | - |
| TR-A10xA17xA31 | A10xA17xA31 | pattern x Tensor x wave fire | 0.47 | NEVER-EXAMINED | - |
| TR-A01xA10xA08 | A01xA10xA08 | stage x pattern x volume | - | NEVER-EXAMINED | partial exception per Lane 6: the VCP family's definition, a construction rather than an examination; seat p not printed individually |

## What this supplement does and does not change

It changes the granularity, not the verdicts. Every tier here is computed from the same register numbers the Reexamination read at class granularity, so the two files agree wherever both speak: zero separators in the sweep, zero campaign survivors, the viability of nothing promoted on a class average. What the itemization adds is the per-item receipt: any single cell, candidate, sleeve, pair or prototype can now be pulled by its row id and read with its own numbers, and the counts above were reconciled row by row rather than carried. Two of the four discrepancies it surfaced (the collapsed campaign join, the prototype summary-versus-register mismatch) are exactly the failure class the owner's challenge pointed at, and both are printed above rather than buried.

Named remainders, carried open: the 42 unitemized Lane 6 triples (D-SP1, blocked on Lane 6's unpersisted run record); the Reexamination's own remainders stand unchanged (96 items whose seat reads were lost to the provider rate limit, tiers on the record alone; seven-lens panels on its 26 screened surprise items, runner ready; six Dive Five items blocked on their source).

STATUS: PARTIAL. Proven on the final artifacts: 26,723 itemized rows generated mechanically by `build_supplement_itemized.py` and counted back from `REEXAMINATION-SUPPLEMENT-ROWS.jsonl`; coverage reconciled to zero delta on the sweep (24,517), campaign (1,200), board (339), pairs (561) and prototype (100); all 9 Lane 7 leads and all 561 pair marks cross-verified against their registers with zero mismatches; campaign funnel and sweep status accounting reconciled exactly to their verdict files. The bounded remainder is named: 42 of Lane 6's 48 curated triples cannot be itemized from any persisted register (D-SP1), so the triples population stands at 6 itemized rows plus a counted, reasoned remainder, and Lane 6's full axis-triple space is separately itemized inside S1's Block A rows.

Evidence pointers: rows file `~/workspace/research_notes/alpha-hunt-chaos-20261115/REEXAMINATION-SUPPLEMENT-ROWS.jsonl` (26,723 rows); generator `~/workspace/research_notes/alpha-hunt-chaos-20261115/build_supplement_itemized.py`; sources `GESTALT-SWEEP-REGISTER.jsonl`, `CAMPAIGN1-REGISTER.jsonl`, `LANE6-GESTALT-FULL.md`, `prototype_candidates.jsonl` in the same directory, and `~/workspace/research_notes/sleeve-activation-calibration-20261111/execution_board.csv`; parent deliverable `REEXAMINATION-POTENTIAL-EDGE.md`.
