# Second Opinion — Evidence Families (False-Consensus / Dependency Table)

Provenance: Adopted 2026-10-28 by the owner's order, evaluation 05-EVALUATION.md section 2 item 6 and section 7 item 5.
Source: Codex (Ausar) SECOND-PASS-2026-10-27.md, Silicon repo dwj9ddyvf6-hub/Silicon, path research/rea-teardowns/synthesis/SECOND-PASS-2026-10-27.md, blob 76cecd3a33775af65ba5097b7a30727a502b0529, sha256 c9ef4509c48cc78476493890a74e184d888efcad480a4d8ebf077bd4b3491404, fetched 2026-10-28 via ghapi GET only. Local adopted copy at ~/workspace/opt/rea-teardowns/synthesis/SECOND-PASS-2026-10-27.md is byte-identical to the Silicon version (verified by sha256).
Status: This table is the analytical core of The Second Opinion (tool 18). It is adopted as a table, not as a graph engine (see ADOPTED-STANDARDS addendum on the evidence graph).

---

## Data dependency and false-consensus control

A dashboard can display many products while containing only a few independent information sources. Store the dependency lineage and group evidence by underlying primitive before counting confirmation.

| Apparent evidence | Shared primitive or dependency | Product rule |
|---|---|---|
| RSI, moving averages, breakout state, momentum rank, and chart patterns | Often the same daily or intraday OHLCV history | Treat as one price-derived evidence family unless the hypothesis defines a distinct, independently sourced event. Test incremental value after price/trend features are already present. |
| Sweep tags, premium totals, buyer/seller-side estimates, and flow alerts | The same options prints, condition codes, NBBO or latest-quote joins, and contract metadata | Deduplicate by contract/time/print identity where possible. Display raw print separately from side estimate and intent label. The current Tape’s latest-quote join is not historical NBBO-at-print. |
| GEX, gamma walls, zero-gamma, and dealer-positioning summaries | Option-chain OI and greeks plus a sign/positioning convention | Group these as one modeled options-inventory family. Publish the convention, dropped-contract coverage, OI vintage, and sensitivity to sign/Greek assumptions. Do not call the result observed dealer holdings. |
| Board confluence and vendor-style ratings | Overlapping price, volume, market-context, sector, fundamentals, or positioning leaves | Keep raw leaves and coverage. Compare the gate and score separately; do not count the Board and its inputs as independent votes. |
| News scans, event alerts, letters, and trade calls | Often the same public event or source story | Preserve original publication and ingestion timestamps. Cluster by catalyst and source chain before measuring incremental signal value. |
| 13F, insider transactions, short interest, and short volume | Distinct reporting processes with different publication delays and definitions | Never merge them into a generic “smart money” feature. Preserve filing/settlement/publication dates, float basis, and source-specific missingness. |
| Address labels, wallet flows, and exchange activity | On-chain transactions plus a vendor’s entity-attribution layer | Store chain data and attribution confidence separately. A label change should create a new version, not mutate historical interpretation. |

This directly changes product behavior: a “consensus” view should report **independent evidence families present**, not just the number of vendors or alerts agreeing.

---

Adopted product rule (from the source, verbatim in substance): a consensus view reports independent evidence families present, not the number of vendors or alerts agreeing.
