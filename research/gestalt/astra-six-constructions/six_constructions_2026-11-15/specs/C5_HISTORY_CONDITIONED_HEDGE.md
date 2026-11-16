# C5 — verified history changes valid contract hedges

**Evidence:** supplied-state derivation and enumeration, not a live arbitrage. **Reference:** `TouchRule`, `HistoryFact`, and `conditional_pair`. Original prototype and its hypothetical results are preserved in `original/`.

## Contracts and logical object

Two binary upper-touch contracts have thresholds KL<KH. Their original start times may differ. Both windows must already be active at the decision and share the future observation period/end, source, observation convention, inclusivity, currency and compatible payout/payment semantics. The elementary reference supports no void/revision exception states; a real contract with such states needs expansion.

Buy lower YES and higher NO. With $1 payouts, terminal payout is 1+L-H. Without established past facts, retain `(L,H)=(0,0),(1,0),(1,1),(0,1)`. The last state pays zero. It can arise if the higher target was hit during its earlier historical window but the lower contract never became true in its own window.

If complete matching history establishes that the higher target has never hit before the current decision, future higher YES implies future lower YES. The adverse `(0,1)` state disappears. A verified irreversible lower YES also establishes a floor regardless of the higher past. These are sufficient facts for the simple model, not a universal list of all semantic relationships.

## Input proof contract

Preserve rule source text and version/hash, timestamp/zone conversions, source ID, threshold convention, revisions, voids, settlement currency, payout and payment timing. A history fact needs truth value, coverage interval, source ID, evidence ID/hash and verification provenance. The reference requires complete matching historical coverage before accepting a supplied verified fact. Unverified inputs remain unknown. The caller is responsible for actual upstream proof; the Boolean flag cannot verify itself.

OHLC histories may establish a touch only when their observation source and interval boundaries match the contract. A missing interval, an interval partly before the monitoring start, a different exchange or a revised observation can change the permissible states. Do not fill gaps by assuming no event occurred. Resolve equality and time-zone boundaries explicitly.

## State compiler and economics

For each admissible past state, enumerate future touch states `(0,0),(1,0),(1,1)`. Terminal truth is past OR future for each contract. Preserve the union of all resulting terminal states. Compute every payout before ranking any candidate. A subset of convenient states is not a worst-case certificate.

Subtract both executable asks at the actual desired size, fees, impact and financeable capital cost on one cash-flow clock. The hypothetical asks 0.40 and 0.55 give worst net −0.95 with unknown past and +0.05 with higher-not-hit established, before omitted costs. These are supplied illustrations. The package's actual price archives end October 31, so they do not prove a complete November 15 history.

Different settlement dates require discounting/carry and cash-path feasibility. A positive-cost pair with a conditional floor is not automatically a self-financing arbitrage. Unfinished legs, a canceled/void market, and uncertain collateral must remain in the completion model.

## Build sequence and acceptance cases

1. Parse one real pair's rules into structured fields and preserve the texts.
2. Independently verify the implication or retain uncertainty. Gather the exact fact that changes its state set.
3. Compile all supported settlement states and compute the payoff vector.
4. Only then compare actual simultaneous executable asks/depth and complete costs.
5. Persist rule/history versions and expire/recompute the conclusion when they change.

Required cases: unknown history retains the zero payout; verified higher-not-hit removes it under compatible rules; lower-already-hit also bounds payout; unverified or incomplete history cannot certify a floor; different sources/end times and additional void states require a richer model. Unit-test success proves the model arithmetic, not the real facts or executable opportunity.
