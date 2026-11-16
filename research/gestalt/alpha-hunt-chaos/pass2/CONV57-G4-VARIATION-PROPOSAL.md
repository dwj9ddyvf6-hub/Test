# TENSOR G4 VARIATION PROPOSAL (registered proposal, not a desk registration)

Written Sun 2026-11-15 by the Conversion Program's remainder lane, under the GUTTING AS VARIATION rule: a loosened form is proposed as an ADDITIONAL variation with its own id, replay counts, falsifier, and grade. The parent G4 conjunction is not edited, here or anywhere, by this document. Rostering, if it ever happens, is a desk-lane act taken on this proposal; nothing in this document arms anything.

## The parent, verbatim

G4 (recorded form, from the R19 register and the Ausar pb127-148 record set, extracted line by line by Lane C): entry signal is a week carrying the buy-green marker AND native_close at most 10 AND depth60 at least 70 AND ret60 at least 0 AND vol20 at least 0.09 AND dv20 at least $2M, with the family vol gate COOL (atr_ratio at most 1). Entry the first session after the signal week under the recorded delay/reserve policies; grading is per-entry forward excess versus QQQ.

## The anatomy that motivates a variation (rebuilt stream, 428 symbol-weeks, weeks ending 2026-09-04 to 2026-11-13, 40 of 41 tracker names; SHAZ unmeasurable on warmup)

Per-conjunct pass counts over the 428 rows (Lane C, recounted tonight from firestream_work/tensor_stream.jsonl):

| Conjunct | Passes |
|---|---:|
| buy-green marker | 0 |
| close at most 10 | 101 |
| depth60 at least 70 | 358 |
| ret60 at least 0 | 94 |
| vol20 at least 0.09 | 349 |
| dv20 at least $2M | 426 |
| COOL (atr_ratio at most 1) | 66 |

Joint counts, computed tonight from the same stream:

- Full parent conjunction: 0 qualifiers.
- All non-marker conjuncts including COOL: 0 rows. The COOL gate alone excludes every row that passes the other five non-marker conjuncts.
- All non-marker conjuncts excluding COOL: 13 rows (SKYQ 4, SATL 5, CRML 4 across the window). All 13 carry atr_ratio 1.03 to 1.72; none carries a buy marker (10 carry no marker, 1 sell-magenta, 2 sell-red across the wider near pool; in the 13-row pool the marked rows are 1 sell-magenta and 1 sell-red).
- The buy-green marker's only occurrence anywhere in the held record is 1 in the adjacent CADENCE-SWEEPS census window (426 symbol-weeks ending 2026-08-28 to 2026-11-06, per the tensor_rebuild validation gate); the emitted rebuilt stream, whose first week ends 2026-09-04, contains zero.

Read: the parent does not fail on one gate. It is bound by two independent near-zeros, the green marker state and the COOL temperature gate, and the rows that satisfy its price, depth, momentum, and volume core are uniformly ATR-hot small names. Any honest variation must say which of the two bindings it loosens, and a variation loosening only one of them still fires zero times on the held stream. That is priced per form below, not argued around.

## Candidate forms, replayed on the rebuilt stream

Marker adjacency is defined from the engine's own outputs on the same rows, so the rule is computable from the same weekly bundle the desk already produces: the buy-cyan rows on this stream (8 of 8) sit at bullishVotes 6 to 7 with bearishVotes 0 to 1. The adjacency signature is bullishVotes at least 6 AND bearishVotes at most 1 on a row carrying no buy marker.

- Form A, marker-adjacent only (COOL kept): qualifiers 0 of 428. The COOL gate excludes all 13 core-passing rows regardless of marker state. Dead on arrival; recorded so nobody has to re-derive it.
- Form B, COOL dropped only (buy-green marker kept): qualifiers 0 of 428 on the emitted stream. Dead on arrival on this span; the marker's single census-window occurrence keeps the form from being absurd in principle, but a variation that cannot fire on its own replay span has no grade to earn.
- Form C, marker-adjacent AND COOL dropped, every other conjunct exact: qualifiers 2 of 428. SKYQ, week ending 2026-09-11 (close 3.11, ret60 +161.3, bullishVotes 6, bearishVotes 1, atr_ratio 1.69) and CRML, week ending 2026-10-30 (close 7.16, ret60 +9.3, bullishVotes 6, bearishVotes 1, atr_ratio 1.035). Sensitivity, printed and not proposed: the same form at bullishVotes at least 5 yields the same 2 qualifiers (the bv 5 pool rows carry bearishVotes above 1); the count is not a threshold artifact at that step.

## The proposal

Proposed variation id: aster_tensor_g4_varmk (marker variation), a sleeve-layer variation beside the G4 parent, Tensor engine untouched.

Definition: a week qualifies when native_close at most 10 AND depth60 at least 70 AND ret60 at least 0 AND vol20 at least 0.09 AND dv20 at least $2M AND the marker element is satisfied in either of its two forms: the row carries the buy-green marker (the parent's own state, unchanged), OR the row carries no buy marker and prints the adjacency signature bullishVotes at least 6 with bearishVotes at most 1. The COOL gate does not apply to this variation. Entry, delay/reserve policies, and grading basis are the parent's recorded ones, unchanged.

What is loosened, named plainly: two elements, the marker state (green required, relaxed to green or its vote signature) and the temperature gate (COOL, dropped). What is NOT loosened: the price cap, the depth floor, the ret60 floor at 0, the vol floor, the dv floor, the universe, the entry timing, and the parent itself. The signal core that remains is the parent's price-depth-momentum-volume conjunction; this is a variation of the parent's firing conditions, not a different signal wearing its name.

Replay counts (this proposal's own, from the rebuilt stream): 2 qualifiers in 428 symbol-weeks (0.47 percent of rows), named above. The forward expectation set by the replay is roughly one qualifier per five months of bundles at this rate, which is why the falsifier below leads with the existence check rather than the return grade.

Falsifier: the uniform variation falsifier (retire if mean fwd5 excess versus QQQ is below 0 over the first 20 resolved forward fires), preceded by the existence question in CONV-56's form: one line per weekly bundle counting qualifying rows; zero qualifiers over a full quarter of forward bundles returns the variation to the desk as an open anatomy row, not a silent sleeve. At the replay rate, the 20-fire grade is a multi-year accrual and the proposal says so on its face; the existence check is the near-term instrument.

Counterweights, printed because the proposal must carry them: (1) the AVOIDANCE record on gate-dropping in this family (register[166]: ret60 gates are load-bearing) is honored by construction, since no ret60 element moves; the loosened elements are the marker and the temperature gate, and the C1 anatomy (CONV-56) showed the same COOL emptiness on the sibling conjunction, which is evidence the temperature gate is a family-wide firing suppressant, not proof that dropping it is safe. (2) Both replay qualifiers are ATR-hot microcaps (atr 1.69 and 1.035); the variation's forward fills, if any, will carry that slippage profile and the grade is on fills, not on the stream. (3) The adjacency signature is inferred from the buy-cyan rows' vote pattern; the single held buy-green row sits outside the emitted stream, so the signature's relation to green itself is unverified on held data, and the proposal labels the signature an adjacency hypothesis, not a recovered definition.

## What would unblock rostering

A desk-lane registration act on this proposal (its own config entry, blocker, and gate run, exactly as the F4 variations were registered and rostered), taken with this anatomy in hand. Until then the proposal stands as the registered form of the idea, and CONV-57's status records it.

STATUS: PROPOSAL REGISTERED (research side). Evidence pointer: this file; stream firestream_work/tensor_stream.jsonl (428 rows, recounted tonight); parent anatomy in pass2/FIRESTREAM-PLACEBO-GRAVEYARD.md, Tensor lane and Near object 1.
