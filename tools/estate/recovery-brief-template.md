# Recovery brief template: interrupted-work recovery (Round-4)

Use verbatim structure for every workflow relaunch / resume brief.

## Fixed recovery note (open every resumed attempt with this, unedited)

> RECOVERY: This attempt resumes interrupted work. Inspect before acting:
> read the committed state on disk first, list what the prior attempt
> already did by its effects (files, commits, receipts), and do not repeat
> any effect already proven. When in doubt, treat an effect as done and
> verify, never redo blindly.

## Brief fields

- Prior run / attempt ID:
- Committed work to adopt, by path (fresh launches adopt by path; a stopped
  run is terminal and cannot be a resume source, a FAILED run can):
- Inputs the prior attempt never read (requeue ONLY these):
- Inputs already read / effects already landed (do NOT requeue):
- Scope and mandate: restated from the tracked item / goal record, not from
  any summary (authority is re-proven at resume, see AGENTS.md round-4 law).
- Proof required on the final state:

## Rules

1. Requeue only inputs never read.
2. Adopt committed work by path; never restart from zero when a tree exists.
3. The recovery note above opens the new attempt; it is not optional prose.

## Bounded checkpoint schema (round-5 items 38 and 39)

Structured checkpoint fields, each capped; a checkpoint over its total
budget is REJECTED, never silently truncated. Fields: objective / state /
evidence / decisions / pending. The checkpoint carries a content-hash key
(discipline 14), a stated cap, and a TTL.

## Handoff transaction (round-5 item 38)

A summary handoff uses its own one-shot capability store, structurally
outside the tool registry: token plus separate handoff id, TTL-bound,
exactly one waiter, second submission rejected, empty summary rejected,
consumed on delivery, aborted per trace. A handoff token can deliver a
summary and can never invoke a tool.
