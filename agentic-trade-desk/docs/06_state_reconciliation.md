# 06 — State, ledger, reconciliation, persistence

## 6.1 Three stores, one truth

| store | role | write rule |
|---|---|---|
| **Ledger** (SQLite, append-only, hash-chained) | history of every intent, order, fill, alert, note, pass | append only; triggers block UPDATE/DELETE; corrections are `note` events |
| **Book/state** (JSON) | fast working copy: lots, queued entries, orders, seen-keys, caches | read-modify-write under an exclusive file lock; atomic replace; add-only merge of foreign adoptions |
| **Broker** | external truth for positions/orders | read-only except via the order path |

The **book is a fold of the ledger**: replaying fills must reproduce positions. Run `replay == live` in every pass (cheap) and in the nightly audit.

## 6.2 Ledger design

```sql
CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, payload TEXT, prev TEXT, hash TEXT);
CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
```
Event kinds (minimum): `pass_start`, `pass_end{book_sha}`, `intent`, `entry_sent`, `exit_sent`, `order_accepted`, `refused`, `send_unknown`, `fill{cid,qty,price,cumulative}`, `book_sync`, `blocked{why}`, `intent_skipped{why}`, `alert`, `note{corrects}`, `job{name,rc,secs}`, `suspend_detected`, `backup`.

* `fill` events are unique per `(cid, cumulative_qty)` so a re-read cannot double count.
* Record **why not** as events too: `blocked(lane_full)`, `wait(input_unknown)`, `skip(not_in_window)`. A per-fire reasons log (`decision_reasons_<day>.jsonl`) with one row per non-intent outcome turned "why isn't it trading?" from a day of archaeology into one query. Nothing reads it for control flow.
* Hash chain: `sha256(prev || kind || payload)`. Verify at startup and in the audit.
* **Never edit history.** A fill-price correction is a `note` with the old and new modelled price and the net effect; the original row stays.

### 6.2.1 SQLite on odd file systems
A backup copy that included the **WAL header** to a network/FUSE-mounted store produced "disk I/O error" on open. Fix: for copies, set `journal_mode=DELETE`, checkpoint, copy via SQLite's online backup API (or `VACUUM INTO`), **assert the header bytes** of the copy (journal flag bytes 18–19 not 2), then `integrity_check`. Keep the live DB on a local disk.

## 6.3 State file: locking, atomicity, merge

The failure: a second writer (backup/failover adoption) put new lots into the book **while the main loop held an older in-memory copy**; the main loop then saved and silently erased them. Fix (all three, see `skeleton/deskkit/store.py`):

1. **One exclusive file lock** around every read-modify-write (`fcntl.flock` on a sidecar `.lock`).
2. **Atomic replace**: write temp in the same directory, `fsync`, `os.replace`.
3. **Merge-back on save**: under the lock, re-read the file; for any entry whose `source` is a *foreign writer* and which the in-memory copy lacks, **add it**. Add-only: never delete or alter existing entries. Seen-key sets are unioned.

Foreign writers must do their own RMW **on a fresh load under the same lock** (`update(fn)`), never load → think → save.

Test (exists in skeleton): start a pass with an in-memory copy; let the foreign writer adopt a lot; save the old copy; assert the adopted lot survives. And a thread-concurrency test: N writers × M updates ⇒ N×M entries.

## 6.4 Intent journal and crash windows

A crash between "POST sent" and "state saved" is the classic gap. Close it with: ledger/state **saved before** the send and **after**, `pass_end` carrying `book_sha`, and a startup check `state hash == last pass_end` (alert on gap) followed by a first-pass **resync by client id**.

Also: the **fill-triggered backup** must run *after* that tick's fill and `book_sync` records have been appended; otherwise the backed-up state has fills but its ledger doesn't, and the restore drill fails verification.

## 6.5 Read-back cadence

Read back non-final orders **every pass** (5 min), writing a `book_sync` record with the new `book_sha` when anything changed. Hourly read-back left fills invisible for an hour, showed queued positions as open-with-zero-qty on the status page, and made reconcile flap.

## 6.6 Reconciliation algorithm

```text
for each (account, symbol):
    book = Σ book qty over all sleeves in that account
    brk  = broker position qty
    allowed range = [ book − pending_sell_qty , book + pending_buy_qty ]
    if brk not in range ± eps → ALERT(mismatch) ; do not trade
```
* Count `closing` (exit order working) as still held; count `entry_pending` as expected-to-arrive. A position with a working exit used to show as "broker ≠ book".
* Compare **per account**, summing across sleeves. Two sleeves may legitimately hold the same symbol; one sleeve holding the symbol must block only **itself** (not every other sleeve).
* Account identity pin: suffix/id from config must match the key's account; abort the pass otherwise.
* Known benign differences should be **explained once** in a file (for example, broker positions may aggregate multiple sleeve lots) and the check should understand the documented mapping.
* A check that compares against an *old* book after a cutover is itself a bug: point audit tools at the current book and the pending-order tolerance.

## 6.7 Broker-driven import (add-only)

Desk-owned orders that exist at the broker (by id prefix) but not in the book — because a standby placed them, the primary was down, or a crash lost the save — are **imported**: fill price, qty and stop come from the broker's order record; the owning sleeve comes from the plan or the id; the lot is marked `source=import`. This is idempotent (skip ids already in the book) and **add-only**.

## 6.8 Persistence and rollback

Some hosts roll the **disk** back to an earlier snapshot. Treat the local disk as a cache.

* Ledger + state are pushed off-box after every pass with orders/fills and on a timer, to a **private** `state-backup` branch (additive) and, if available, a second persistent store.
* Startup: if local state is missing or *older* than the backup (fewer ledger events), **restore keep-newer** (never delete), verify the hash chain, run a first pass that re-syncs by cid and reconciles.
* The **restore hook must live where the rollback cannot revert it** (in a persistent store), not in the script the rollback restores.
* **Restore drill**: restore into an empty dir; verify chain; replay; compare book hash with live; compare open-order set. Record `identical: true` in evidence. A backup that has never been restored is a hope.
* Restores re-apply file modes that matter (frozen specs read-only; scripts executable).

### 6.8.1 Mirror/refresh jobs that can destroy logs
A job that refreshed a documentation mirror by whole-tree copy wiped bug-log rows that had been written only in the mirror. Rule: mirror refresh copies **git HEAD only**, atomically per file, **never deletes**, and refuses (non-zero exit + alert) when a mirror file matches no version git ever committed. Logs are append-only and live in git.

## 6.9 Snapshots and the public view

Generate the status view from the snapshot, not by reading the ledger live in the UI. The snapshot reconciles: `total = realized + unrealized`; `unrealized` = sum of the position rows shown; `realized` = sum of the closed-trade list; equity = start + total; cash = equity − holdings. A broker's headline equity differs from the sum of shown rows by fill-rounding pennies — **decide which is the headline and make everything else derive from it**, otherwise the page shows a plug ("unrealized = total − realized") that disagrees with its own table. Off-session, don't mix an official-close basis for one panel with after-hours marks for another. Stamp every carried-forward value with *its own* date.

## 6.10 State checklist
- [ ] ledger append-only (trigger test), chain verifies
- [ ] state RMW under lock; atomic replace; merge test passes
- [ ] fills idempotent (replay twice → same book)
- [ ] read-back every pass; book_sync record
- [ ] reconcile with pending tolerance; account pin
- [ ] import of orphan desk orders tested offline
- [ ] off-box backup after fills (post-record) and on a timer
- [ ] restore drill recorded in evidence


## Addendum — truth at the writer and at the broker (from the archive review)

- **Every risk number is computed from broker truth** (or reconciled to it each pass). A cache once produced a phantom exposure that tripped a breaker and hid real positions; short legs were invisible (P-88). Reconcile intraday if it costs only two read calls — but the bigger win is surfacing mismatches *loudly* and locking the symbol.
- **All fills are recorded through one door**, with a test that fails on any bypass; reconcile **by fills** (not only positions) each day. A clean replay of the ledger proves nothing if a writer recorded around it (P-89).
- **Verify protective orders at the broker**, not in your own state; report coverage per lot (P-90).
- **Declare ownership of inherited positions** (adopt with an owner sleeve, or 'owned by no writer; never managed') (P-91).
- **Keep decision reasons** (reason, inputs, expiry) per fire (P-92). Ignore stale responses (P-93). Compare freshness with the last-consumed date and the book's birth (P-94). Derive 'previous close' from the daily series (P-95).
- A manual change at the broker is followed the same day by a state fix and a ledger note.
