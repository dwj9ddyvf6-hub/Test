# 11 — Checklists

Copy these into your runbook. Each item should be answerable with a command or a file, not a feeling.

## 11.1 Pre-open (before the first session pass)

- [ ] Supervisor alive; loop alive; **heartbeat fresh and progress counter moved** since yesterday's close
- [ ] Last `pass_end` book hash == state hash; ledger chain verifies
- [ ] Mode is what you intend (`shadow` / `paper`); account allow-list unchanged; key files present (presence only)
- [ ] Broker reachable; account status ACTIVE; positions/orders counts read
- [ ] Reconcile = OK for every account (pending tolerated)
- [ ] Data fresh: bars through the previous close, producer files younger than their limits, vol-index feed ok
- [ ] Nightly jobs finished (completion records), rc == 0; verify/retry-once ran if not
- [ ] Calendar: market open today? early close? DST change this week?
- [ ] Disk/memory ok; no leftover temp dirs; no OOM kills in the last day
- [ ] Off-box backup newer than the last fill; restore drill < N days old
- [ ] Failover worker status: box_alive true; mode as intended; plan for today present and dated today
- [ ] Open alerts reviewed; any older than a day has an owner
- [ ] Quiet windows noted for today

## 11.2 Intraday (every wake-up)

- [ ] Heartbeat age < limit; if not → supervisor script revives (never an agent improvising)
- [ ] A pass ran in the last 10 minutes (aligned)
- [ ] Fills read back; reconcile OK
- [ ] Inside any critical window: a pass is **guaranteed**; no restarts
- [ ] Silent unless exception

## 11.3 Close / after close

- [ ] Close-window decisions logged with reasons (including waits and skips)
- [ ] Nightly close job started; limit set (monotonic); completion verified later
- [ ] Off-box backup after fills; verify the remote ref (e.g. `git ls-remote`)
- [ ] Daily snapshot/P&L row written; page published; publish failures alarmed
- [ ] Blocked-fire counts by lane recorded; any lane at cap vs caps config sanity
- [ ] Evidence written for any change made today (undo copies, tests, log rows)

## 11.4 Readiness drill (run on a COPY of live state; no orders)

1. Run dry passes at representative times: open, mid-session, the decision window with a *forced red* and a *forced green* market gate.
2. Assert: intents built for the forced-red case; none for forced-green; **no order sent** (mode dry / fake broker).
3. Check duplicates (0), refusals, lane budgets consumed, concentration alerts, sleeve errors (0).
4. Restart the loop in the drill and assert **no re-entry**.
5. Compare the drill's would-send set with the next real pass (when live).

## 11.5 Incident (something broke)

1. **Stabilize**: if the desk is trading wrongly, ask the human to stop it; otherwise leave it running. Don't make it worse (no manual orders).
2. **Preserve evidence**: copy logs, ledger tail, state, exact errors *before* restarting.
3. **State the contradiction**: expected vs observed, with timestamps.
4. **Find the first failed boundary** — trace upstream from the symptom. Classify: defect / wrong hypothesis / transport / dependency / permission / external / missing decision.
5. **Cheapest discriminating check** → hypothesis → minimum structural fix.
6. **Guard**: a test that fails on the old behaviour.
7. **Replay** the original path on the final artifact.
8. **Reconcile**: is the book == broker? any orders to adopt? any missing exits? Were any exits *missed* (time/stop) while down?
9. **Write** the bug-log row, the evidence file, and the runbook change.
10. **Report** only what needs the human: real harm, decisions needed. Mention short outages only if they mattered.

## 11.6 Change (any code/config change)

- [ ] Scope: surface, constraints, outcome, proof, edges written down
- [ ] Not inside a quiet window; claim logged; undo copy saved
- [ ] Minimum sufficient change at the demonstrated source
- [ ] Test written first (fails on old code)
- [ ] Full regression: 0 FAIL; SKIPs have reasons
- [ ] Secret scan clean; additive commit; remote verified
- [ ] Loop restarted *outside* quiet windows if code must reload (config hot-reloads)
- [ ] After restart: verify startup check (hash match), no duplicate ids, reconcile OK
- [ ] Bug-log row + evidence + runbook updated

## 11.7 New sleeve

- [ ] Card complete; origin pinned; fidelity/parity test
- [ ] Exit audit: terminates; time exit from fill; inputs available
- [ ] Data prerequisites present or sleeve is `blocked(reason)`
- [ ] Shadow first; lane config; concentration impact reviewed
- [ ] Rehearsal pass with the new sleeve; no sleeve errors; pass time still within budget
- [ ] Human yes for paper promotion

## 11.8 Retire a desk or component

- [ ] Kill every scheduler **and** the supervisor/launchers that would restart them
- [ ] Tombstone entry points; archive launchers (move, don't delete)
- [ ] Adopt positions and orders into the new book; exit-only for replaced sleeves
- [ ] Verify no old process alive after 5 minutes (they respawn)
- [ ] Update runbook; announce in the dead-drop

## 11.9 Weekly

- [ ] Restore drill; boot drill
- [ ] Blocked-reasons review; unused lanes; unexplained divergences
- [ ] Usage review for the agents themselves (limits, reset day)
- [ ] Rotate any key that appeared anywhere it should not have
- [ ] Review the open-items list and the kill ledger
