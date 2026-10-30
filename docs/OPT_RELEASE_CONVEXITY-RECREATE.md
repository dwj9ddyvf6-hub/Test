# OPT_RELEASE_CONVEXITY: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "OPT_RELEASE_CONVEXITY", type volatility, family release_convexity. Algorithm grade PARTIAL, unresolved true. Accounting sources: femto land-wt config params. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "OPT_RELEASE_CONVEXITY" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: femto land-wt config params; alias record sources: ausar_deployed, femto_land_wt
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/free_opt_release.py + desk3/sleeves/free_opt_release.py + integration/free_opt_release_adapter.py; existing package docs/FREE_OPT_RELEASE-RECREATE.md.

## What this strategy is

No strategy description recorded in consulted sources. Type: volatility; family: release_convexity. Universe: not recorded in consulted sources. Asset class: not recorded. Timeframe: not recorded. Creator / source: not recorded. Style evidence in the accounting: Classification 2026-10-30: volatility (code evidence): Muse desk v3 desk3/strategies/free_opt_release.py read: it buys a straddle, one call and one put, only on a verified event session and exits the session after the event, a long volatility package

## Full algorithm

Accounting record: entry, exit and sizing rules were not recorded in the accounting's consulted sources (gaps listed there); its parameters hold only an empty symbol list. Its classification evidence is the identifying link to the code: the accounting's style evidence states that the desk v3 free_opt_release code was read and that it buys a straddle, one call and one put, only on a verified event session and exits the session after the event. The existing recreation package for that code in this repo (docs/FREE_OPT_RELEASE-RECREATE.md) records the full algorithm, summarised here in evaluation order:

1. Shared quote law: a quote is fresh only when source and receipt stamps are both present, neither more than 2 s in the future, source age <= 90 s, receipt age <= 30 s, receipt not earlier than source, and ask >= bid > 0. Exits are evaluated before entries. Entries are deduped per session. Virtual ledger account free_options, BUDGET_USD 100,000 pool; roster slice $10,000; SleeveConfig cadence_s=300, universe empty, risk_pct None. An ENH switch in context.extra (default ON) restores the pre-change rule exactly when OFF.
2. Entry: compute exits first; if already entered this session return exits only; require a fresh indicative quote; require a verified event for this session in extra events (session equal and verified true; the producer's event sources are CPI and the Employment Situation from FRED's release calendar and the FOMC statement from the Fed's calendar); require the package to have exactly 2 legs with rights exactly {call, put}, every leg with a symbol and a finite ask > 0; ENH integrity gate (default ON) refuses legs whose source stamps are more than 30 s apart, a missing/malformed leg stamp, or a leg stamp older than 90 s or more than 2 s in the future. Emit one enter intent per leg, qty_hint 1, price_hint round(leg ask, 2), reason naming FREE_OPT_RELEASE_V1 and buy_to_open. The producer's package selection (not in the strategy file): an ATM SPY straddle on the nearest expiry after the session that follows the event, within 45 days, 1 straddle, max loss / risk cap the natural debit, sent only while the market is open. The v3 adapter's ENH2 filter refuses a package whose legs' OCC expiries differ or are unparseable; exits are never filtered.
3. Exit: held positions grouped by entry_date; sessions held counts extra session_dates strictly after entry_date; exit is due when sessions held >= 1 or the session is on/after the earliest leg OCC expiry; before expiry every leg needs a two-sided quote or the group does not exit, at/past expiry that gate is bypassed; each leg exits at its full held quantity (long legs sell to close at the bid, short legs buy to close at the ask), reason session_after_event or expiry.

Where the accounting and this code differ in scope, the code is the truth for the free_opt_release implementation; the accounting's own entry/exit text for OPT_RELEASE_CONVEXITY itself is not in the record.

## Files in this repo

- This package: docs/OPT_RELEASE_CONVEXITY-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/free_opt_release.py + desk3/sleeves/free_opt_release.py + integration/free_opt_release_adapter.py; existing package docs/FREE_OPT_RELEASE-RECREATE.md

## Configuration

Per the existing package: roster slice capital_usd 10,000.0 / cash_usd 10,000.0; strategy virtual pool $100,000 (free_options); cadence 300 s; session 24h; flat_by_close false; bp_buffer_frac 0.02; params {} in the roster row (all parameters in the strategy code above); inputs options; parked false. Accounting-side configuration for OPT_RELEASE_CONVEXITY itself: symbols [] and status mode=unfunded_monitor, running=False (ausar_deployed record); no other accounting configuration is in the record.

## Data inputs

context.extra built from the snapshot: quote / quotes, package, events, session_dates and sleeve_state held records, per the existing package. Freshness is judged inside the strategy from quote source and receipt stamps.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- A quote 91 s old at source, 31 s old at receipt, more than 2 s in the future, crossed, or with bid <= 0 produces no entry.
- Entry requires a verified event dated this session, exactly 2 package legs with rights {call, put} and a positive finite ask on each leg.
- Leg source stamps more than 30 s apart produce no entry with the ENH switch ON and an entry with it OFF; legs expiring on different dates produce no entry at the adapter filter, while exits pass unfiltered.
- A served record with entry_date or last_exit_date equal to this session blocks a new entry; with session_dates one session after entry the whole package exits together (before expiry a missing or one-sided leg quote blocks the exit; at/past expiry it does not).
