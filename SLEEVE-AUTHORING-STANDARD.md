# Sleeve Authoring Standard: fill adoption (adoption T-317)

Landed 2026-11-03. Authoring-standard text only; no strategy, sizing, stop, or threshold change.

## Rule: every non-filled status is a distinct case, never a default

Partial fills and terminal states are where fill adoption breaks (31 hits across 9 files in the bug-log census, repeated per sleeve). Any sleeve or desk component that adopts broker fills MUST handle each status as its own case:

1. **Status-gated adoption.** Only a `filled` status promotes an entry to fully filled, at the full filled quantity.
2. **Terminal-with-partial-fill.** On a terminal status (filled, canceled, expired, rejected, or closed) carrying a partial fill, adopt exactly the filled portion; the unfilled remainder is closed, never booked, and never left as a zombie pending entry.
3. **Working partial fill.** A non-terminal partial fill books the filled portion as working and keeps the remainder pending under the same entry identity; it is never booked as a full fill.
4. **Uncertain submit.** When a submit raises or its outcome is uncertain, keep the pending entry and check the broker's open orders before any retry or clear; never clear the pending entry on the exception alone, and never resubmit blind (duplicate-order risk).
5. **No default fall-through.** Code that treats any status other than an explicitly handled one as "filled" or as "nothing happened" fails this standard. The unhandled status is logged by name as an open defect against the sleeve.

Proven fix shape, from the desk logs: status-gated adoption, filled portion adopted on terminal-with-fill, uncertain submit keeps the pending entry after an open-orders check.
