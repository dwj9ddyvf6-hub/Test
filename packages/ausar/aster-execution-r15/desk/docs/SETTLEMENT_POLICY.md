# Versioned local-paper settlement

New owned US-equity sales use `US_EQ_REGULAR_WAY_DTCC_2022_2026_V2`. Economic maturity counts **regular-way equity CNS settlement days**, with T+2 for trade dates before May 28, 2024 and T+1 thereafter. The dated processing calendar is separate from the exchange trading calendar. October 12, 2026 is an equity trading day with no settlement; an October 9 sale matures October 13. November 10, 2023 is a normal processing Friday because the Saturday Veterans holiday does not shift to Friday. Good Friday and July 3, 2026 are excluded for this product even when some DTC services remain available.

January 9, 2025 is the opposite distinction: DTCC cash/securities settlement remained open during national mourning while NYSE equities closed. A January 8 sale therefore has economic maturity January 9. The desk's **local-paper cash convention** releases at the first actual XNYS opening on or after maturity, January 10 in that case. This opening convention is a simulation policy, not evidence that real DTC end-of-day payment or a broker's actual buying power was available at that opening. Connected broker truth remains independent.

The reviewed normal calendar covers 2022–2026. Missing coverage, including a December 2026 trade requiring a 2027 maturity, fails closed before a local owned sale fill commits. Exceptional settlement outages also need new dated evidence and an explicitly versioned policy. Annual renewal must preserve older definitions and replay semantics. These changes do not alter strategy signals, holdings, entry risk or corporate-action entitlements.

## Recorded policy and historical compatibility

The original six-column `a_strategy_settlements` ledger remains intact. New sales append a policy receipt keyed by fill ID, with cycle, trade date, economic maturity, cash policy, release clock and calendar definition SHA-256. Reconciliation independently recalculates those terms and validates the receipt hash and version. Unknown, missing or changed post-rollout receipts block spending and fail reconciliation.

At the first new-code construction, one append-only rollout record captures the maximum **existing fill rowid**. All later owned sales require the new receipt. That boundary stops a deleted current receipt from masquerading as an old unversioned sale merely because its normal-day release date happens to match the older rule. Subsequent constructions retain that recorded boundary.

Existing unversioned rows below the rollout boundary are replayed under `LEGACY_NEXT_XNYS_OPEN_V1`, preserving both original `release_at` and any original `released_at`. Their spendable-cash boundary is the later of that original assertion and the corrected regular-way paper boundary. On a writer admission, the desk appends a hashed legacy-review record and journal event documenting this hold. It never silently rewrites an earlier assertion. Already marked-early cash remains withheld until the corrected boundary; any prior use of that cash requires a separate historical incident assessment, not a fabricated ledger correction.

Every relevant row is validated before any release update or legacy-review write. A read with `release=False` derives buying power without writing metadata. Paper sale cash remains part of ledger equity while it is withheld from spending. Ordinary unowned books retain their original behavior.

## Cutover audit

Before restarting, make a supported consistent backup; inspect the owned settlement count, oldest and latest source clocks, policy coverage, marker and receipt consistency, and any original early-released boundary. Preserve every existing financial row and journal event. In this pass, the read-only transaction at 19:36:51 UTC on October 9 observed ten fills, seven owned books and **zero strategy settlement rows**, so no existing sale boundary requires a compatibility hold at that observation. This is a dated snapshot, not a permanent assertion.

The 24 independently authored dated cases and six fail-closed cases are portable test fixtures. Ledger tests create new isolated databases and also instantiate the byte-identical retained R13 implementation to produce authentic synthetic legacy rows before loading the repaired implementation. They cover the bank-only holiday, T+2 transition, Carter maturity/release distinction, early markers, idempotent hold reviews, unknown versions, deleted receipts and atomic failure before sale accounting. No test writes the operating database or changes a running process.

Source provenance and old/new implementation bytes are retained in the R15 operations archive. Legacy direct DTCC URLs that returned 404 remain labelled HTML; successful current PDF receipts and separately rendered primary text retain their actual evidence modes.
