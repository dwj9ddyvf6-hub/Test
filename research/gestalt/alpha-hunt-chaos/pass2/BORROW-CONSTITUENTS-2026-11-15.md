# BORROW CONSTITUENT NAMING PASS: s_1wlab, tensor_swing, s_mn_pairs, LS5

Date: 2026-11-15. Companion to DATA-HUNT-2-BORROW.md and DH2-BORROW-SERIES.jsonl in this folder.

SCOPE: Surface, the constituent symbol lists for the four short objects DATA-HUNT-2 left borrow-unpriced because the ShortSide register names no single symbol for them. Constraints, held records only, desk sources read only and unmodified, no register or DH2 file edited, no constituents invented. Outcome, one named symbol list per object that the daily IB snapshot archive accruing from Mon 2026-11-16 can consume directly, or an exact statement of the record that would name them. Proof, every census below was recomputed from its source file in this pass and recounts exactly against the ShortSide register (see the recount table). Edges, a traded-symbols census names what an object has traded, not what it may trade next; where a fixed definition exists it governs and the census is printed as its instance; where no fixed definition exists the naming rule is printed beside the census so the archive knows the list is open.

## RECOUNT TABLE (proof the censuses are the graded streams, not neighbours of them)

| Object | Register row (SHORTSIDE-REGISTER.jsonl) | Census source recomputed in this pass | Recount |
|---|---|---|---|
| s_1wlab | REPLAY, n_entries 80, 25 dates, LEAD-INVERSION | pass2/work/runs/s_1wlab.json, entries array | 80 entries, 25 distinct dates, match |
| tensor_swing | LIVE-RECORD, n_entries 3,778, fwd5 n 2,096 on 6 dates, NEAR-INVERSION | muse-desk-v3/state/dispatcher.jsonl plus its .1 to .4 rotations, fill events for sleeve tensor_swing (stamped buy_to_open fills plus unstamped buy fills, the exact construction in pass2/work/shortside_compute.py) | 3,778 entries, match; fwd5-priceable subset recomputed at 2,096 entries on the same 6 dates (2026-10-27, 2026-11-02 to 2026-11-06), match |
| s_mn_pairs | REPLAY, n_entries 12, 6 dates, NEAR-INVERSION | pass2/work/runs/s_mn_pairs.json, entries array | 12 entries, 6 distinct dates, match |
| LS5 | NEGATIVE-OBJECT, 26 calls, 10 hits, TRADEABLE-FORM (shadow) | retrospective_rows.jsonl filtered exactly as pass2/stack_work/run_stacks.py test F5 (forecast rows with an outcome, axis A21 value numeric_band, axis A22 value none_mentioned) | 26 rows, 10 hits, match |

Archive consumption: the four code blocks below hold 93 object-symbol rows and 82 distinct symbols. One archive pass over the 82 distinct symbols prices all four objects.

## 1. s_1wlab: NAMED, 37 symbols, traded-symbols census (dynamic basket)

What it is. A Lazarus fire-consumer sleeve (family Lazarus/Q07/MN, unit listed in its run file as Lazarus catalog singles). Desk definition: muse-desk-v3/desk3/lazarus.py SPECS entry s_1wlab (slots 22, capital 22,000 dollars, cadence 3600s, family cyan, timeframe 1W, horizon 126 sessions, stop_pct None since the 2026-11-15 fix program dropped its 15 percent stop). It holds no fixed universe: its sleeve config in muse-desk-v3/config/sleeves.json carries empty params and no universe list, and the engine consumes whatever symbols arrive in the lazarus_fires or tensor_fires feed that match its sleeve_id and its family filter. The graded object in the ShortSide register is the replay of that stream, 80 entries on 25 dates, disposition TRADEABLE-INVERSION: a shadow short of the stream's own entries at fwd5.

Which side needs borrow. The inversion shorts the stream's own entries. All 80 replay entries are long entries (dir +1 on every row), so the short side of the inverted object is every symbol the stream entered. Borrow set equals the full census below.

Naming rule (dynamic). Any symbol carried by a fire addressed to s_1wlab (family cyan, 1W) can enter the basket, up to 22 concurrent slots. The list is therefore open: the archive should price the census below daily and append any new symbol the stream fires on from Mon 2026-11-16 forward.

Most recent held instance (the graded replay census). Source: pass2/work/runs/s_1wlab.json, entries array, replay span 2025-11-10 to 2026-11-13, entry dates 2025-11-10 to 2026-11-06. Counts are entry events per symbol.

| Symbol | Entries | Symbol | Entries | Symbol | Entries |
|---|---|---|---|---|---|
| AEHR | 5 | CRWD | 4 | NFLX | 3 |
| AAOI | 4 | MU | 2 | PANW | 3 |
| ALAB | 4 | AAPL | 2 | PLTR | 3 |
| AMAT | 4 | AG | 2 | AMZN | 3 |
| AMD | 4 | ALGM | 2 | MSFT | 3 |
| ABCL | 1 | AVGO | 2 | BAC | 1 |
| CAT | 2 | COST | 2 | CRM | 2 |
| CVX | 2 | GE | 2 | GOOGL | 2 |
| JPM | 2 | META | 2 | VIX | 2 |
| DIA | 1 | GLD | 1 | HD | 1 |
| IEF | 1 | IWM | 1 | LLY | 1 |
| MA | 1 | NVDA | 1 | QQQ | 1 |
| TSLA | 1 |  |  |  |  |

```text
AAOI
AAPL
ABCL
AEHR
AG
ALAB
ALGM
AMAT
AMD
AMZN
AVGO
BAC
CAT
COST
CRM
CRWD
CVX
DIA
GE
GLD
GOOGL
HD
IEF
IWM
JPM
LLY
MA
META
MSFT
MU
NFLX
NVDA
PANW
PLTR
QQQ
TSLA
VIX
```

Caveats the archive must carry. (1) VIX appears in the census as a fire symbol with index-level prices (17.60 on 2025-11-10, 15.74 on 2025-12-12). VIX is an index, not a borrowable equity, and the IB shortstock file carries no borrow row for it. It is kept in the list for fidelity to the census; a missing archive row for VIX is the correct result, and no proxy (VIXY, VXX, UVXY) is named by any held record, so none is substituted. (2) DIA, GLD, IEF, IWM and QQQ are ETFs and carry ordinary IB borrow rows. (3) Routes tried: the ShortSide register and dig (no symbols), the desk sleeve spec in desk3/lazarus.py (no universe, feed-driven by design), the sleeve config in config/sleeves.json (empty params, no universe), the adapter adapters3/laz_s_1wlab.py (delegates to the engine, no symbols), the PASS2-C sleeve parameter report (no universe), and the replay run file, which named the census above.

## 2. tensor_swing: NAMED, 40 symbols, traded-symbols census (dynamic basket)

What it is. The Tensor flagship swing sleeve. Desk definition: muse-desk-v3/sleeves/tensor_swing.py, whose CONFIG declares universe as an empty tuple by design. It stages candidates only from context.extra tensor_signals, the Tensor engine output delivered through core Data, filtered to confidence at least 7, not extended, not already held, in engine rank order. There is no fixed universe anywhere in its spec, its adapter (adapters3/tensor_swing.py), or its sleeve config (empty params). The graded object in the ShortSide register is its live record, 3,778 entry fills, the largest live stream in the estate, verdict NEAR-INVERSION with the registered check at 20 forward entry dates.

Which side needs borrow. The sleeve stages longs only (its exit code states this in terms, and all 3,778 census fills are buys, dir +1). The inverted object shorts those same entries, so the borrow set is every symbol the sleeve has filled on. Borrow set equals the full census below.

Naming rule (dynamic). Any symbol the Tensor engine emits as a swing signal that passes the staging filters (confidence at least 7, not extended, priced entry, stop and target with positive per-share risk and, under the improve switch, reward at least equal to risk) can enter. The list is open in the same way as s_1wlab: price the census daily and append new filled symbols as they accrue.

Most recent held instance (the graded live census). Source: muse-desk-v3/state/dispatcher.jsonl and rotations .1 to .4, fill events with sleeve tensor_swing, counted exactly as pass2/work/shortside_compute.py constructs the live stream. Fill dates 2026-10-27 to 2026-11-12, 10 distinct fill dates. Counts are fill events per symbol (the sleeve re-enters names; ANF's 279 fills are 279 recorded entry fills, not 279 positions).

| Symbol | Fills | First fill | Last fill | Symbol | Fills | First fill | Last fill |
|---|---|---|---|---|---|---|---|
| ANF | 279 | 2026-10-27 | 2026-11-05 | AXTI | 274 | 2026-10-27 | 2026-11-12 |
| SOXL | 270 | 2026-10-27 | 2026-11-12 | CORZ | 198 | 2026-10-27 | 2026-11-11 |
| HUT | 195 | 2026-11-03 | 2026-11-11 | SHAZ | 193 | 2026-11-03 | 2026-11-11 |
| TTMI | 190 | 2026-10-27 | 2026-11-12 | ASPI | 186 | 2026-10-27 | 2026-11-09 |
| TSEM | 186 | 2026-10-27 | 2026-11-12 | FFIV | 171 | 2026-10-27 | 2026-10-27 |
| OUST | 171 | 2026-11-03 | 2026-11-05 | VRT | 148 | 2026-11-03 | 2026-11-12 |
| SKYQ | 122 | 2026-11-02 | 2026-11-09 | AG | 113 | 2026-11-04 | 2026-11-09 |
| OKLO | 104 | 2026-11-06 | 2026-11-10 | WDC | 94 | 2026-11-10 | 2026-11-12 |
| LITE | 88 | 2026-11-11 | 2026-11-12 | MU | 88 | 2026-11-11 | 2026-11-12 |
| SNDK | 88 | 2026-11-11 | 2026-11-12 | AAOI | 86 | 2026-11-11 | 2026-11-12 |
| CVNA | 82 | 2026-11-12 | 2026-11-12 | CLS | 47 | 2026-11-10 | 2026-11-12 |
| KEEL | 36 | 2026-11-03 | 2026-11-12 | WYFI | 32 | 2026-11-03 | 2026-11-10 |
| NBIS | 31 | 2026-11-10 | 2026-11-12 | IREN | 30 | 2026-11-06 | 2026-11-12 |
| FCEL | 27 | 2026-11-10 | 2026-11-12 | HIVE | 27 | 2026-11-10 | 2026-11-12 |
| USAR | 25 | 2026-11-10 | 2026-11-12 | ALAB | 24 | 2026-11-10 | 2026-11-12 |
| LASR | 24 | 2026-11-06 | 2026-11-10 | ARM | 23 | 2026-11-10 | 2026-11-12 |
| AEHR | 20 | 2026-11-03 | 2026-11-10 | CRDO | 20 | 2026-11-10 | 2026-11-12 |
| SATL | 20 | 2026-11-06 | 2026-11-10 | ARQQ | 19 | 2026-11-06 | 2026-11-09 |
| CRML | 16 | 2026-11-10 | 2026-11-10 | POET | 13 | 2026-11-09 | 2026-11-10 |
| TEM | 10 | 2026-11-09 | 2026-11-10 | VELO | 8 | 2026-11-10 | 2026-11-10 |

```text
AAOI
AEHR
AG
ALAB
ANF
ARM
ARQQ
ASPI
AXTI
CLS
CORZ
CRDO
CRML
CVNA
FCEL
FFIV
HIVE
HUT
IREN
KEEL
LASR
LITE
MU
NBIS
OKLO
OUST
POET
SATL
SHAZ
SKYQ
SNDK
SOXL
TEM
TSEM
TTMI
USAR
VELO
VRT
WDC
WYFI
```

Graded-subset note. The fwd5 inversion grade itself rests on 22 of these 40 symbols (AEHR, AG, ANF, ARQQ, ASPI, AXTI, CORZ, FFIV, HUT, IREN, KEEL, LASR, OKLO, OUST, SATL, SHAZ, SKYQ, SOXL, TSEM, TTMI, VRT, WYFI; 2,096 fills on 6 dates, recomputed in this pass). The other 18 symbols (AAOI, ALAB, ARM, CLS, CRDO, CRML, CVNA, FCEL, HIVE, LITE, MU, NBIS, POET, SNDK, TEM, USAR, VELO, WDC) first filled on 2026-11-09 or later, too close to the end of the stored bar series to price at fwd5. They are traded constituents all the same and are exactly the names the forward check will grade next, so the archive list keeps all 40.

Routes tried: the ShortSide register and dig (no symbols), the desk sleeve source (universe empty by design, engine-fed), its adapter and sleeve config (no universe), the PASS2-C parameter report (no universe; a separate Lane C read on a truncated stream), the Tensor bundle archives under pass2/work/tensor_regen (engine bundles for the aster_tensor consumer sleeves, a different stream from this sleeve's live fills, not used), and the dispatcher fill record, which named the census above and recounts exactly.

## 3. s_mn_pairs: NAMED, 6 symbols, fixed definition (3 pairs)

What it is. A market-neutral distance-pairs sleeve (Gatev distance method), family Lazarus/Q07/MN, unit MN catalog. Desk definition: muse-desk-v3/sleeves/s_mn_pairs.py. Its header states the catalog names no pairs and the desk pairs are declared in the sleeve itself; the fidelity ledger (muse-desk-v3/FIDELITY-LEDGER.md, s_mn_pairs row) records the same pairs as a desk-chosen universe. Rule: for each declared pair, the log-price spread is normalised over the trailing 60 sessions; at |z| of at least 2.0 it opens a 1,000 dollar pair, 500 dollars per leg, long the cheap leg and short the rich leg; both legs exit at |z| of at most 0.25. Maximum 3 pairs, 3,000 dollar slice. The graded object is the replay, 12 entries on 6 dates, verdict NEAR-INVERSION.

Which side needs borrow. Both postures need it. In the sleeve's own posture the rich leg of an open pair is short and pays borrow. In the inverted object the cheap leg is short instead. Which leg is rich flips with the sign of z, and the replay proves it: each of the four traded symbols appears in the entries as both a long cheap leg (dir +1) and a short rich leg (dir -1). The borrow set is therefore all six defined symbols, not one leg per pair.

Fixed list (the definition, complete). Source: PAIRS constant in muse-desk-v3/sleeves/s_mn_pairs.py, corroborated by the FIDELITY-LEDGER.md s_mn_pairs row.

Pairs: (KO, PEP), (XOM, CVX), (JPM, BAC).

```text
BAC
CVX
JPM
KO
PEP
XOM
```

Most recent held instance (the graded replay census). Source: pass2/work/runs/s_mn_pairs.json, entries array, entry dates 2026-05-15 to 2026-09-14, replay span 2025-11-10 to 2026-11-13, feed SYNTH-MN. 12 entries: 6 pair openings, each printing one cheap leg and one rich leg.

| Pair | Dates opened | Cheap and rich legs as printed |
|---|---|---|
| XOM, CVX | 2026-05-15, 2026-06-12, 2026-08-28 | CVX long with XOM short on 2026-05-15; XOM long with CVX short on the other two dates |
| JPM, BAC | 2026-06-10, 2026-07-06, 2026-09-14 | JPM long with BAC short on the first two dates; BAC long with JPM short on 2026-09-14 |

Per-symbol entry counts in the replay: BAC 3, CVX 3, JPM 3, XOM 3. KO and PEP never opened in the replay span, so they have no census rows; they stay in the archive list because the fixed definition can open them on any future session and the archive exists to price names before they are needed.

Routes tried: the ShortSide register and dig (pair legs not named), the desk sleeve source (fixed PAIRS found), the fidelity ledger (same pairs, corroborating), the sleeve config (no pairs, not needed once the source named them), and the replay run file (instance census above).

## 4. LS5: NAMED as a per-call rule with a 10-symbol historical instance list (no fixed list exists)

What it is. LS5 is a lead-stacking object, not a sleeve: the fade of band-framed forecast calls made in quiet macro windows (LEAD-STACKING.md LS5; LEAD-STACKING-REGISTER.jsonl rows STK-F5 and STK-F19; ShortSide register NEGATIVE-OBJECT row LS5). The cell is defined on the forecast corpus by two axis tags: A21 framing value numeric_band and A22 window value none_mentioned. It hit 10 of 26 calls against a 0.6567 base rate (z -2.922, family q 0.030). Its registered expression is a posture fade: when such a call prints, the book shadow-fades its stated direction, the called name shadow-shorted at probe size in the ghost book or the call's size cut to zero. Its registered forward check accrues A21 and A22 tags on forward calls from Mon 2026-11-16 and re-grades at 40 forward band-framed quiet-window rows.

Which side needs borrow. The shadow form pays no borrow at all, as the dig states. A live form pays borrow only on calls whose stated direction is long, where the fade is an actual short of the called name; calls stated in the down or range direction fade to a long or a size cut and pay no borrow. Because the called name and its direction are set per call, there is no fixed borrow list for LS5 and none can be written honestly. What the archive can do, and what this section gives it, is price every name the cell has actually called, and append each forward call's name on the day the call prints.

Naming rule (per call). The constituent of an LS5 event is the symbol field of that forecast row (the called name), for every row carrying A21 numeric_band and A22 none_mentioned. Forward rows enter the archive list on their call date under the same two tags.

Historical instance list (the 26 graded calls, 2026-11-03 to 2026-11-13). Source: retrospective_rows.jsonl, filtered exactly as the F5 test in pass2/stack_work/run_stacks.py, recount 26 rows and 10 hits. The symbol field names a single name on 18 of the 26 rows, giving 9 distinct symbols: SPY 6 rows, EW 3, NVDA 2, MU 2, SHOP 1, ELF 1, RKLB 1, EXPD 1, SOXX 1. The other 8 rows carry no symbol field. Six of those eight name a single instrument in their call text (SPY in FL-0154, FL-0185 and FL-0195; QQQ in FL-0155, FL-0186 and FL-0196), which adds QQQ as the tenth symbol. The last two are sector calls (FL-0136 and FL-0150) whose texts measure the semiconductor complex by SOXX against SPY, both already in the list. All 26 rows are thereby accounted for, and the list below is the called-name census of the graded cell, labelled as a census, not a definition.

```text
ELF
EW
EXPD
MU
NVDA
QQQ
RKLB
SHOP
SOXX
SPY
```

What is NOT named, stated exactly. Eight of the 26 graded rows (FL-0136, FL-0150, FL-0154, FL-0155, FL-0185, FL-0186, FL-0195, FL-0196) have an empty symbol field in retrospective_rows.jsonl; their called names were recovered from call text in this pass, as documented above, not from a structured field. The record that would name LS5 constituents structurally, for the historical rows and for every forward call, is a populated called-name symbol field on each forecast row of the forecast ledger (the FORECAST-LOG.md corpus that retrospective_rows.jsonl was built from, owned by the night-study and forecast grading lane, living at the forecast log and its retrospective extraction). Until that field is populated at extraction, LS5 naming depends on call-text reading, and the archive should treat the forward A21 and A22 accrual as incomplete for borrow purposes unless the symbol field is filled on the same row.

Routes tried: the ShortSide register and dig (called name varies per call, no names), LEAD-STACKING.md and its register (cell definition and counts, no names), the stack lane's own compute file pass2/stack_work/run_stacks.py (located the corpus and the exact F5 filter), and the forecast corpus retrospective_rows.jsonl itself, which named the census above.

## SUMMARY FOR THE ARCHIVE

| Object | Verdict | Count | Kind of naming | Short side |
|---|---|---|---|---|
| s_1wlab | NAMED | 37 symbols | Dynamic basket; naming rule plus graded replay census, span 2025-11-10 to 2026-11-13 | The inverted stream shorts all 80 long entries; every census symbol |
| tensor_swing | NAMED | 40 symbols | Dynamic basket; naming rule plus graded live fill census, 2026-10-27 to 2026-11-12 | The inverted stream shorts the sleeve's long fills; every census symbol |
| s_mn_pairs | NAMED | 6 symbols | Fixed definition, 3 declared pairs, plus replay instance (4 of 6 traded) | Rich leg short in the sleeve posture, cheap leg short in the inversion; all 6 symbols |
| LS5 | NAMED (rule plus instance) | 10 symbols | No fixed list by construction; per-call naming rule plus the 26-call historical census, 2026-11-03 to 2026-11-13 | Live form only, and only on long-stated calls; shadow form pays no borrow |

All four lists are open at the forward edge by design: the archive prices the 82 distinct symbols above daily from Mon 2026-11-16 and appends new names under the naming rule printed in each section (new s_1wlab fires, new tensor_swing fills, any s_mn_pairs pair opening including KO and PEP, and each forward LS5 call's called name).

STATUS: GREEN for the naming task. Evidence pointer: this file, with every census recomputed in-pass from its named source and recounted against SHORTSIDE-REGISTER.jsonl (80 of 80, 3,778 of 3,778 with its fwd5 subset at 2,096 of 2,096 on the same 6 dates, 12 of 12, 26 of 26 with 10 hits). Named open rows, carried in the sections above: VIX in the s_1wlab census has no borrow row by construction; KO and PEP are defined but untraded in the replay span; 18 tensor_swing symbols are traded but not yet fwd5-gradeable; LS5 has no fixed list and 8 of its 26 historical rows lack a structured symbol field, with the exact record that would cure that named in its section.
