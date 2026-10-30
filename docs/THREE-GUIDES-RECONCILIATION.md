# Three Guides, One Desk: A Three-Way Reconciliation

*Scope. Surface: this document only; it maps three existing guides in this repository and records where a builder must decide consciously between them. Constraints: it changes none of the three guides and invents no rule any guide does not contain; every claim carries a pointer to the file and section it was checked in. Outcome: a reader pointed at this repository cold can tell which guide governs which question, what all three agree on, what only one teaches, and which differences are real decisions. Proof: each claim in Section 3 was verified present in its own guide and checked absent, or materially thinner, in the other two; each divergence in Section 4 rests on positions read, not inferred. Edges: this document reconciles guides, not desks; a running desk still answers to its own operator, frozen specifications, and broker read-back.*

Short names: **FG** is the field guide at `docs/AGENTIC-TRADE-DESK-GUIDE.md`; **KIT** is the operational kit rooted at `agentic-trade-desk/`, its chapters cited as KIT-00 through KIT-17; **CMP** is the companion build guide at `docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md`. A two-way reconciliation between KIT and CMP exists at KIT-17; this document supersedes nothing in it. It adds FG to the map, carries KIT-17's two decisions forward with FG's position added, and records further divergences.

---

## 1. The three guides at a glance

### 1.1 What each guide is

**FG: the field guide.** One file of about 172,000 bytes, fifteen sections plus an appendix. Its center of gravity is judgment under operation: scoping work, grading its own claims, keeping a roster and catalog honest, grading forecasts, behaving inside a multi-agent fleet. It is the only guide distilled explicitly from several desks at once (FG, introduction): a broker-backed paper desk, a fully simulated desk, a research operation, and a cross-desk auditing function, which shows in its preoccupations with cross-desk identity, contradictory reports, and published numbers. Its characteristic unit is the rule with its failure story attached (FG Sections 1.3, 3; the sixty-entry master list in Section 13). It carries templates (Section 14) and a staged build plan (Section 15), but no runnable code.

**KIT: the operational kit.** A directory, not a file: a README, an `AGENTS.md` of standing orders, eighteen chapters (KIT-00 to KIT-17), a runnable skeleton under `agentic-trade-desk/skeleton/`, and six templates under `agentic-trade-desk/templates/`. Its center of gravity is the running machine: one order path, deterministic order identity, an append-only ledger, reconciliation every pass, supervision that survives a paused or wiped host, and a standby failover. Its characteristic unit is the invariant with a guard test: the pitfalls catalog (KIT-10) holds 130 numbered entries in Symptom, Cause, Fix, Guard form, and the skeleton's tests exist so the invariants can be executed, not admired (KIT README; KIT-03 Step 3).

**CMP: the companion build guide.** One file of about 41,000 bytes, sixteen sections plus a glossary. Its center of gravity is architecture decided before code: what product is being built, which layer owns what, what an observation must carry, and what evidence each build stage has earned. It is the most taxonomy-driven of the three: six product modes (Section 1), a layered ownership model (Section 2), a six-row evidence table (Section 6), seven build phases (Section 14), acceptance checklists split by product type (Section 15).

### 1.2 Routing table: which guide for which task

| Task in front of you | Read first | Then read |
|---|---|---|
| First build, nothing exists yet | CMP Sections 1, 2, 14 | KIT-03 with the skeleton; FG Sections 2.4, 15 |
| Wiring the order path, ids, or retries | KIT-05; KIT-10 P-01 to P-04 | FG Section 8; CMP Section 8 |
| State, ledger, or reconciliation work | KIT-06 | FG Sections 4.8, 4.9; CMP Section 8 |
| Running the desk day to day | KIT-07 and KIT-11 | FG Section 11; CMP Section 11 |
| Research standards and backtest honesty | FG Sections 7.5, 7.6 | CMP Section 6; KIT-08 |
| Counting strategies across desks; catalog work | FG Sections 7.7, 7.9 | CMP Section 3; KIT-04 Section 4.11 |
| A forecast or signal product that will be published | FG Sections 4.9, 5 (rows 19, 28), 7.6, 12.10 | CMP Sections 5, 9, 10 |
| Data provider misbehaving or a field in doubt | FG Section 10 | KIT-10 theme F; CMP Section 5 |
| Deciding whether something is proven | CMP Section 6 | FG Sections 1.5, 3.1; KIT `AGENTS.md` Section 6; KIT-08 Section 8.4 |
| Anything involving live money | CMP Section 14 Phase G; Section 15 live checklist | FG Sections 1.2, 2.2; KIT README scope note |

---

## 2. Where all three agree: the shared invariants

Each invariant below was located in all three guides.

**One order path, and agents outside it.** Exactly one component may submit orders; everything else simulates or proposes. FG states it as an audit rule: broker submit, replace, and cancel callable from exactly one module (FG Sections 4.7, 13 entry 6). KIT makes it Principle P1, admitting a failover only under the same identity scheme while the primary is stale (KIT-00 P1; KIT-05 Section 5.1). CMP draws it as an architectural boundary: the research and agent layer does not write orders or protected policy (CMP Sections 2, 9).

**Identity derived from data, persisted before send.** Order identity comes from the decision that produced it (strategy, instrument, data bar or event, side, leg), never from wall-clock time or a restartable counter, and is durable before the network call (FG Section 8.1; KIT-00 P2; KIT-05 Section 5.2; CMP Section 8). Corollary, shared: a timeout is an unknown outcome, not a refusal; the next act is a lookup by the original identity, never a blind resend (FG Section 8.3; KIT-10 P-02).

**Append-only history; corrections are new records.** No guide permits rewriting the record to match the present. FG: compensations are appended as new truth; simulated fill corrections are additive notes, never edited rows (FG Sections 4.8, 2.3). KIT: the ledger is append-only and hash-chained, state a fold over it, a price correction a note event with old and new values (KIT-00 P3; KIT-06 Sections 6.1, 6.2). CMP: fills and fees are immutable events, positions and cash derived, provider corrections new revisions (CMP Sections 5, 8).

**Reconcile against the broker, and never trade to fix a mismatch.** The two books are compared on a cadence, disagreement is a named defect, and placing an order to make them match is forbidden in all three (FG Sections 4.8, 9.4; KIT-00 P4; KIT-06 Section 6.6, repair by add-only import; CMP Sections 2, 8). The scope of the resulting pause diverges, at D7; the prohibition is unanimous.

**Fail closed on entries; protect exits and ownership separately.** Missing, stale, or untrusted input blocks new exposure in all three, and no entry-side failure may erase a position, an exit obligation, or a protective order (FG Sections 3.4, 8.6, 9.3; KIT-00 P5; KIT-10 P-81; CMP Sections 5, 14). The exit policy under degraded data differs in emphasis, reconciled at D6.

**Frozen specifications; no invented rules.** A strategy is implemented from a specification frozen before measurement; a thin specification is a recorded gap, not an invitation to improvise (FG Sections 1.2, 7.2, 7.3; KIT-04 Sections 4.2, 4.3; CMP Sections 4, 6). All three require tried variants and the selection path recorded (FG Section 7.5; KIT-10 P-113; CMP Section 6 item 10).

**Risk decided outside strategy code, by versioned operator-ruled policy.** Strategies propose; a separate layer disposes; limits are versioned data, and changing them is an operator act (FG Sections 9.1, 9.2; KIT-04 Sections 4.5, 4.6; CMP Section 7). Whether that layer may resize an intent diverges, at D3.

**Paper before anything else; modes never mixed in one number.** All three are paper-first to the point of mechanism. FG requires the refusal of a live environment to live in code, proven by a scan (FG Section 1.2). KIT declares live out of scope and unimplemented (KIT README; KIT-00 Section 0.5). CMP forbids implicit promotion and requires the mode recorded in configuration, logs, and interface (CMP, "Start here" item 5; Section 1). Their taxonomies differ enough to cause a vocabulary collision, at D4; the rule does not differ.

**Evidence before any green word.** A completion claim is graded against the final artifact, at the boundary the claim names, after the last change. FG Sections 1.5 and 3.1 give the levels GREEN, PARTIAL, BLOCKED, UNVERIFIED. KIT states the same four as standing orders, adding that a command exiting zero is not evidence (KIT `AGENTS.md` Section 6; KIT-00 P7; KIT-08 Section 8.4). CMP uses PASS, FAIL, BLOCKED, UNVERIFIED and insists a test is evidence only about the exercised case (CMP Sections 1, 3). Reconciled at D5.

**Every cured bug leaves a guard and a record.** FG requires the cure at the source, a dated bug-log entry, and a named regression test wired into the gate, its fail direction proven (FG Sections 1.3, 11.3). KIT requires an invariant, a test, and a log row, and warns that a named blocker that never executes is itself a pitfall (KIT-00 P8; KIT-08 Section 8.3.1; KIT-10 P-67). CMP is thinnest here: negative tests and labeled synthetic fixtures (CMP Section 6), but no bug-log discipline.

**Saves and backups are proven by read-back and restore, not by sending.** FG Section 3.10 and Section 13 entry 41: a save is reported by its verifier's verdict over an enumerated set. KIT-06 Section 6.8 and KIT-07 Section 7.7: additive off-box backup, hash verification, a restore drill with a recorded result. CMP Sections 11 and 15: backup before upgrade and a proven restore.

**Secrets and personal data stay out of the record; public output is scanned.** FG Section 1.2 requires a mechanical scan in the write path before any public save. KIT-12 covers secrets, access control, and externally visible output, and the skeleton ships a secret-scan tool (`skeleton/tools/secret_scan.py`). CMP Section 12 sets the same boundary. All three treat retrieved documents as untrusted data (FG Section 12; KIT-09; CMP Section 9).

---

## 3. What each guide adds that the other two lack

Each claim was checked in both directions: present, in the cited place, in its own guide, and absent, or materially thinner, in the other two. Where the honest verdict is "thinner" rather than "absent", the sentence says so.

### 3.1 Only FG teaches these

**The deduplicated cross-desk accounting standard, with merge tiers and variant enumeration.** FG Sections 7.7 and 7.9 state a complete standard: enumerate identifiers from every source by name; build the crosswalk before any merge and verify it reproduces the census universe by key-set equality; flag scrape artifacts rather than dropping them; merge only under stated evidence tiers (documented grouping; exact identifier equality; mechanical identity corroborated by family and description), zero merges on judgment alone; keep unresolved identities unresolved, each with the fact that would settle it; mark algorithm descriptions partial wherever the source records only part of the rule set; publish tier counts beside any merged count. Variants fold into one catalog entry per strategy, every folded identifier preserved with a merged-into record (FG Section 7.7). KIT covers neighboring ground only: duplicate sleeves inside one desk (KIT-04 Section 4.4.1) and inflated counts (KIT-04 Section 4.11; KIT-10 P-49). CMP mentions the catalog as an index (CMP Section 3) and tried-variant recording for bias control (CMP Section 6 item 10), a research rule, not an accounting standard. Verdict: absent in KIT and CMP.

**Forecast honesty machinery: ledger before display, fixed-horizon grading, abstention as data.** Every published forecast or decision call is written to an append-only ledger before its horizon opens, graded at horizons stated in advance, every figure recomputable from the ledger alone (FG Sections 4.9, 5 rows 19 and 28, 7.6). Abstentions are rows with reason codes from a controlled vocabulary, refused at append time if uncoded, counted in the denominator where abstaining was the engine's choice; a taken event scored zero is a different row kind, and collapsing the two is named a corruption (FG Sections 7.6, 12.9). Kill criteria are pre-registered per engine (FG Sections 7.6, 15), and score semantics live in the data: an uncalibrated score stays null as a probability (FG Section 12.10). KIT has one adjacent pitfall (KIT-10 P-94) and no grading machinery. CMP requires model outputs to retain version, input hash, calibration period, and outcomes, and forbids presenting uncalibrated confidence as probability (CMP Section 9): genuine but thinner, governing labeling, not ledger-before-display grading. Verdict: machinery FG-only.

**The data-pitfall field manual.** FG Section 10 gives thirteen failures a full narrative each (symptom, root cause, detection, cure, prevention): corrupt vendor volume (10.1); bar endpoints returning nothing without a start parameter, then the earliest page rather than the latest (10.2); feed differences and fallback labeling (10.3); snapshots silently lacking greeks and implied volatility (10.4); chains without open interest (10.5); timezone and bar-anchor traps (10.6); stale display values and stale mirrors, including a stale cached copy masquerading as a publish outage (10.7); corporate actions (10.8); the two-shapes defect, hidden by empty fixtures (10.9); forming bars (10.10); import-time side effects (10.11); the silently stopped accrual lane (10.12); header and parameter exactness, including the broken probe that mimics a dead credential (10.13). KIT covers much of this in KIT-10 theme F and entries such as P-111 and P-116, in compressed guard form, without the detection narratives or the per-field probing method of FG Sections 5.1 and 6.4. CMP Section 5 states preventive controls and diagnoses none. Verdict: present in KIT thinner; in CMP only as contract.

### 3.2 Only KIT teaches these

**A runnable skeleton whose tests are the invariants.** Under `agentic-trade-desk/skeleton/`, the `deskkit` package implements the kit's claims in standard-library-only code: deterministic identifiers (`ids.py`), an append-only ledger (`ledger.py`), a locked, atomically replaced store with add-only merge (`store.py`), lane caps (`caps.py`), reservations (`reservation.py`), reconciliation (`reconcile.py`), a simulated broker (`broker.py`), heartbeat and clock discipline (`heartbeat.py`, `clock.py`), a network guard (`netguard.py`). Its tests (`skeleton/tests/test_deskkit.py`) carry the invariant tests the README and KIT-03 Step 3 cite, and a worked example (`skeleton/examples/run_example.py`, in KIT-13) demonstrates restart safety end to end. Neither FG nor CMP ships code: FG Section 14 offers templates, CMP Section 4 one configuration sketch, neither executable. Verdict: absent in FG and CMP.

**Supervision, failover, and host-failure operations at working depth.** KIT-07 has no counterpart: a failure model assuming pause, wipe, rollback, and kill (Sections 7.1, 7.2); supervision with resume-awareness (7.3, 7.4); the four named safety states with a recovery column (7.5.1); a ten-step build order for a cloud standby worker, from read-only dry running through heartbeat locking, exits first, entries only after a clean dry day and an explicit human yes, quota discipline, stop handling, and adoption of the standby's fills by the primary (7.6); and the five-minute "why is it not trading?" runbook (7.8). FG Section 11.4 covers restarts and watchdogs in a few pages and CMP Section 11 supervised hosting in one section; both thinner by an order of magnitude, and neither describes an order-capable standby. Verdict: thinner in FG and CMP.

**The compact 130-pitfall catalog as a citable index.** KIT-10's entries carry stable identifiers (P-01 to P-130) in ten themes, each in Symptom, Cause, Fix, Guard form, under a standing instruction to add a pitfall's guard test to the local suite before considering it handled. Its value is citability: other chapters reference entries by number, and KIT-17 maps CMP's failure table onto P-121 to P-130.FG Section 13 is a sixty-entry master list in rule form, at less than half the count; CMP Section 13 is a fourteen-row symptom table. Verdict: the catalog as an index is KIT-only.

**Ready-to-fill templates for the operating record.** The six files under `agentic-trade-desk/templates/` (bug-log row, coordination log, incident receipt, requirements receipt, runbook skeleton, sleeve card) are short, fielded, and tied to the chapters that consume them. Templates as a category are not KIT-only: FG Section 14 carries richer forms (sleeve specification, build brief, verification checklist, incident report, catalog entry, daily inspection). Unique to KIT are the requirements receipt and coordination log as fill-in forms, and the incident receipt's insistence on naming the first failed boundary. Verdict: category present in FG; those forms unique to KIT; absent in CMP.

### 3.3 Only CMP teaches these

**The six-mode product taxonomy.** CMP Section 1 distinguishes a research terminal, a scheduled research service, a strategy simulator, a local paper desk, a broker paper desk, and a live desk as distinct capabilities rather than versions of one another, the mode recorded in configuration, interfaces, logs, and the user interface. FG's scheme is coarser: three modes (simulated, shadow, live-paper) in FG Section 2.3, with no separate place for research-only products, CMP's first two modes. KIT's vocabulary recognizes shadow, paper, and live only (KIT-00 Section 0.5). Verdict: present in FG thinner and, on one term, conflicting (D4); absent in KIT.

**The evidence ladder: a table of what each layer cannot prove.** CMP Section 6 tabulates six evidence kinds (unit or property test; deterministic replay; historical backtest; simulated paper; broker paper; small live pilot) against what each can prove and, in a separate column, what it does not prove. No other guide states the negative column systematically. FG's maturity ladder (Section 2.4) orders levels of desk, not layers of evidence, and its proof doctrine (Sections 1.5, 3.1) grades claims without bounding each instrument. KIT-08 Section 8.3 gives a testing pyramid, ordering tests by cost and scope without saying what a passing layer fails to establish. Verdict: absent in FG and KIT as a bounded table; the caution is present in both, thinner.

**Provenance-bearing observations as a concrete schema.** CMP Section 5 specifies the fields a normalized observation must carry: instrument identity, display symbol, provider, feed, asset class, interval, source time, receipt time, first-permitted-use time, a completion flag, session identity, price basis, currency, revision identity, and a source receipt, the three timestamps explained separately, back-dating banned. KIT absorbed this lesson in KIT-17 Section 17.2 and as P-116, as a note rather than a schema to implement against. FG Sections 4.10 and 5.1 are both thinner than a field list. Verdict: schema CMP-only; lesson present in KIT thinner, because KIT-17 imported it.

**Coverage states as a named vocabulary for data gates.** CMP Section 5 requires explicit states (fresh, stale, incomplete, unavailable, unentitled, invalid, blocked), a gate naming which instruments, periods, fields, or entitlements are missing and what evidence would clear the block, and separated meanings of "no signal" (CMP Sections 1, 13). FG has named states for unfed strategies and accrual lanes (FG Sections 3.12, 4.2, 10.12), the same instinct applied to products. KIT carries the sharpest single case as P-129, without the general vocabulary. Verdict: vocabulary CMP-only; local instances in both others, thinner.

**Two named mechanisms the others achieve differently or not at all.** First, the transactional outbox: because a database commit and a network call cannot succeed together, the intent is persisted transactionally and a sender drains the outbox using the idempotent identity (CMP Section 8). FG and KIT reach the same safety by persist-before-send journal plus a class-aware pending queue (FG Sections 6.7, 8.5; KIT-05 Section 5.4; KIT-06 Section 6.4), so the outcome is shared but the named pattern is CMP's. Second, risk-policy versioning with compare-and-swap protection: an approved trial change is applied by comparing the policy hash, so a rollback cannot erase a newer operator decision (CMP Section 7). KIT knows the failure as P-126; FG requires limits versioned like specifications (FG Section 9.2). Verdict: outbox nominally CMP-only; compare-and-swap CMP-only as a mechanism.

---

## 4. Differences to decide consciously

D1 and D2 are carried forward from KIT-17 with FG's position added; D3 to D7 are new. Exactly one flat contradiction was found, and it is terminological: D4. No pair of guides prescribes opposite actions for the same situation under the same names, once scope is read carefully; the rest are differences of default, granularity, or emphasis.

### D1. Halt and kill-switch semantics (carried forward, FG added)

**CMP:** two switches, a global halt and a per-strategy halt, each with a reason and an operator identity (CMP Section 7). **KIT:** four deterministic states defined outside the language model: running; sleeve-degraded (only the affected sleeve's entries blocked); entry-paused desk-wide; emergency stop (only explicitly authorized risk-reducing actions continue, through a separately verified path), with effects on queued orders, exits, and protective orders specified in advance (KIT-07 Section 7.5.1; KIT-00 P5). **FG:** three switches: per-strategy halt (reconciliation halts are this switch thrown automatically); desk-wide entry halt (exits and data collection continue); and full stand-down, stopping dispatch entirely including desk-routed exits, broker-side protective stops remaining in place, reserved for book-integrity emergencies (FG Section 9.3).

The substantive difference is the deepest state: KIT still permits pre-authorized risk-reducing actions; FG permits no desk-routed exits at all. **Rule:** implement KIT's four states, the only version specified tightly enough to code and test, with FG's metadata (thrower, reason, evidence, clearing condition) on every transition, and drill them. Set the deepest state's exit behavior per desk, in writing, before the first session: default to KIT's, with instrument, account, quantity, identity, and price policy re-verified; adopt FG's stricter stand-down only if broker-side protective orders demonstrably cover every held position.

### D2. Live promotion scope (carried forward, FG added)

**CMP:** live is the final phase of a staged path (Phase G, CMP Section 14), gated by its own checklist: an explicit mandate naming account, capital, and allowed actions; re-approved risk limits, data entitlement, oversight, recovery, and kill switch; a small controlled pilot (CMP Sections 14, 15). **KIT:** live is out of scope and not implemented; the kit is paper-only, and the companion's live phase is a separate project requiring human, legal, and risk sign-off (KIT README; KIT-17 Section 17.1). **FG:** closer to KIT in effect. Paper-only status must be enforced in code at the broker door, a gate-wired scan proving no live endpoint string exists in the tree, so paper-first is a property of the artifact, not an intention (FG Section 1.2). Live money is outside the guide's scope and on the always-escalate list (FG Sections 1.4, 2.2).

**Rule:** treat live as a separate project, as all three in substance agree. CMP Phase G and its live checklist specify what that project's evidence must contain; they are a requirements list, not an authorization, and no guide may be cited as permission. Until then, FG's code-level enforcement is the standard: a door refusing a live environment at startup, and a scan proving the refusal real.

### D3. Sizing authority: may the risk layer resize an intent? (new)

**CMP:** the risk service may approve, resize, delay, or reject an intent under versioned policy (CMP Section 2). **FG:** the dispatcher refuses oversize intents rather than clipping them silently, because a clipped intent is a different trade from the one specified; the refusal is journaled (FG Section 9.1). Sizing is computed from risk: a defined risk unit against the strategy's stop, inside its slice and caps. **KIT:** closest to FG. Sizing is dollars per slot, whole shares that fit, at the limit price actually committed (KIT-04 Section 4.6). On concentration the quiet fix is forbidden: when several books buy one name in one pass, do not silently shrink sizes; emit a concentration alert (KIT-04 Section 4.5.2; KIT-10 P-47).

All three forbid a silent change to a trade; they differ on whether a policy-declared resize is normal (CMP), to be refused for a journaled rejection (FG), or, for concentration, replaced with visibility (KIT). **Rule:** default to FG and KIT: an intent exceeding its slice, cap, or budget is refused and journaled with values. A resize is permitted only where the frozen specification or versioned policy names the resize rule itself (round down to whole shares; place what fits above a one-share floor, sanctioned for short cash in KIT-04 Section 4.6), in which case it is part of the specified trade, computed deterministically, journaled with requested and executed size. Concentration is never a resizing trigger: it produces an alert and a count. Choose one idiom per strategy in its specification, and give every formula the two-input fixture FG Section 9.1 requires, so a formula that cannot vary is caught as a bug.

### D4. Mode vocabulary, and the one flat contradiction (new)

The word "shadow" denotes different systems. In FG it is observation-only: no matching, no fill, only a record of what would have been intended (FG Section 2.3). In KIT it is a simulated mode that does produce fills, at the last observed mark, with no broker contact (KIT-00 Section 0.5). A report saying "the sleeve ran in shadow" therefore asserts opposite things about whether fills exist, depending on which guide its author read: the only place in the three texts where the same term, in the same role, carries incompatible meanings. Resolution also differs: six modes in CMP (Section 1), three execution modes in FG (Section 2.3), a research-shadow-paper life in KIT (KIT-04 Section 4.3).

**Rule:** adopt CMP's six modes as the repository vocabulary, the only taxonomy that cannot confuse a research terminal with a desk. Retire the bare word "shadow" from reports, ledgers, and snapshots; translate legacy records on read, FG's shadow becoming "observation log", KIT's becoming "local simulation". Every ledger row, snapshot, and published figure carries its mode in CMP's terms (FG Section 2.3; KIT-00 Section 0.5; CMP Section 1).

### D5. What counts as proof, and the words a verdict is reported in (new)

**FG:** proof is outcome-level evidence from the final system state, after the last change: broker read-back, gate output on the final tree, read-back of the saved destination, counted live behavior (FG Sections 1.5, 3.1). Statuses are GREEN, PARTIAL, BLOCKED, UNVERIFIED, organized for whole-product work into an acceptance matrix with no green while any row is open (FG Section 1.3). **KIT:** the same four statuses as standing orders, with the boundary formulation: green only when the final artifact has been exercised at the boundary the claim names (for a push, verify the remote reference; for a backup, restore it; for a fix, reproduce the failure on the old code first) (KIT `AGENTS.md` Section 6; KIT-08 Section 8.4). **CMP:** statuses are PASS, FAIL, BLOCKED, UNVERIFIED (CMP Section 1), and its distinctive contribution is Section 6's bounding table: each evidence layer is credited only with what it can prove, a unit test, a replay, and a backtest each denied authority over broker acceptance, live fills, and profit.

Read carelessly, FG's maturity ladder and KIT's invariant tests can be taken to prove more than CMP's table allows: a fixture round trip against a simulated broker proves the round trip, not broker acceptance. Read together there is no conflict; CMP supplies the scope limit FG's and KIT's claims must be quoted with. **Rule:** report in the FG and KIT vocabulary; treat CMP's PASS as GREEN and its FAIL as a named non-green row, never a synonym for BLOCKED. Attach two fields to every green claim: the evidence layer (CMP Section 6) and the boundary exercised (KIT's sense). A claim whose layer cannot prove it is downgraded before it is reported. This document's scope statement was written under this rule.

### D6. Exit behavior when data is degraded (new, a difference of default)

**FG** is most permissive, deliberately: a due exit may refresh its own inputs and executes on the best available mark, labeled late if late, because an exit imprisoned by an entry freshness gate holds a position by accident (FG Section 8.6); its compensation is mandatory pre-flight, an exit matching no held broker position being refused locally and journaled. **KIT** states the same instinct as fault isolation (KIT-10 P-81), bounded by a validity floor: an exit still requires a valid instrument, account, quantity, order identity, price policy, and broker route, and where those cannot be verified the automated submission blocks and the contingency runbook governs (KIT-07 Section 7.5.1). **CMP** is most procedural: untrusted data blocks new entries, while exit obligations follow a separately reviewed policy written in advance, so an unavailable feed neither erases ownership nor abandons a position (CMP Section 5).

**Rule:** write the exit policy before the first session, as CMP requires; default to FG's (refresh inputs, proceed on the best available verified mark, labeled late), bound by KIT's validity floor (no verified instrument, account, quantity, identity, or route means no automated submission, ownership and protective orders preserved, operator alerted). Pre-flight against the broker book (FG Section 8.6) is unconditional.

### D7. Whose book is "the truth", and what a mismatch stops (new)

**KIT:** the ledger is truth and state is a fold (KIT-00 P3); the broker is the external truth for positions and orders (KIT-06 Section 6.1). On mismatch the reconciliation sketch alerts and does not trade (KIT-06 Section 6.6), while Principle P5 scopes the stop by failure class, refining the sketch from within the same kit. **FG:** truth is split by subject, the broker book the truth for money, the journal the truth for intent, disagreement a defect rather than a tie to break (FG Section 1.3); a per-strategy discrepancy halts that strategy's entries, exits passing, and a cash discrepancy halts entries desk-wide (FG Section 4.8), with restart a reconciliation event in fixed order, an unprotected-position sweep passing before entries re-enable. **CMP:** positions and cash derive from the ledger or a reconciled projection, the reconciler owning differences from the broker (CMP Sections 2, 8); it is least specific about what a mismatch stops.

**Rule:** quote truth claims with their subject attached, in FG's split form; the unqualified sentences "the ledger is truth" and "the broker is truth" are both incomplete and should not appear in a runbook. Apply FG's scoped consequences in preference to KIT-06 Section 6.6's unscoped "do not trade", which KIT-00 P5 already narrows. Add FG's restart order and KIT's add-only import (KIT-06 Section 6.7) as the repair path. A mismatch is never repaired by placing an order.

**Pitfall philosophy, the remaining difference of emphasis.** FG treats containment as a state that must never rest: a fence catching malformed output is legitimate only while a cure is built, every catch an open defect against the producer, and silence about an open problem itself a violation (FG Sections 3.8; Section 13 entries 13, 60). KIT is one step more procedural: a pitfall is handled when its guard test exists and its log row is written (KIT-10 headnote; KIT-00 P8), satisfiable in principle while the producer is merely guarded. CMP's failure table (Section 13) is preventive, pairing symptoms with controls and stating no cure-at-source mandate. Adopt FG's philosophy as governing, the strictest and compatible with both others: a guard test is evidence and a blocker, not a cure; a control is a design requirement, not a disposition of a live defect. A fenced but uncured defect is named as open at the top of every report until the cure lands and is proven.

---

## 5. Reading order, and the merged starter checklist

### 5.1 A combined reading order for an agent pointed at this repository cold

The order interleaves the three guides by the moment each becomes necessary.

1. **This reconciliation, Sections 1 and 4**. Learn the map and the seven decisions.
2. **CMP Sections 1 and 2.** Fix what is being built and who owns what; write the scope contract in FG's five-line form (FG Section 1.3).
3. **KIT `AGENTS.md`, then KIT-00.** The standing orders and nine principles are the operational constitution.
4. **FG Sections 1 to 3.** Authority limits, reporting levels, design principles.
5. **KIT-03 with the skeleton open**, running the invariant tests and the worked example (KIT-13).
6. **CMP Sections 3 to 5.** Reading a repository as evidence; specifying a sleeve; the provenance schema and coverage states, applied to the skeleton's data path.
7. **KIT-05 and KIT-06 together, then FG Sections 4 and 8.** KIT for mechanisms and guards, FG for the error taxonomy, exit pre-flight, and epoch rule.
8. **CMP Sections 6 to 8.** The evidence ladder, independent risk, durable ownership. Record the desk's positions on D3, D6, and D7 in the runbook here.
9. **KIT-04 and FG Sections 7 and 9.** Sleeve onboarding, lanes and caps, then the strategy lifecycle with variant accounting. Catalog work: read FG Sections 7.7 and 7.9 twice.
10. **KIT-07, KIT-11, and FG Section 11.** Operations: supervision, failover, checklists, inspection rhythm. Build the safety-state machine of D1 here and drill it.
11. **FG Section 10 alongside KIT-10.** The field manual narratively, the catalog by theme, component by component as each is designed.
12. **CMP Sections 9 to 12, KIT-09, KIT-12, and FG Section 12.** Agent workflows, terminal honesty, service boundaries, security.
13. **CMP Sections 14 and 15 with KIT-17 and this document's Section 4.** Phases and acceptance checklists read against the recorded decisions, progress claimed under D5's rule.
14. **FG Sections 13 to 15 and the appendix, last.** The master list as a review instrument, the templates as the record's forms, the one-page contract pinned where the operator will see it.

### 5.2 The merged one-page starter checklist

One item per phase, each from the guide that states it best, complete only when evidenced under D5's proof rule.

**Decide.** The product's mode is named from the six-mode taxonomy, and the scope contract exists in five-line form: Surface, Constraints, Outcome, Proof, Edges. (CMP Section 1; FG Section 1.3.)

**Bound the agent.** Standing orders written down: what the agent does without asking, what needs an explicit human yes, and paper-only enforcement in code rather than intention. (KIT `AGENTS.md`; FG Section 1.2.)

**Prove the toy.** One trivial sleeve runs end to end on the skeleton or its equivalent: signal, intent, simulated fill, exit, flat, and a mid-run restart that re-enters nothing. (KIT-03 Step 4; KIT-13; FG Section 2.4 Level 0.)

**Contract the data.** Every observation carries the provenance fields, the three timestamps are distinct, coverage states are named, and each provider is probed field by field first. (CMP Section 5; FG Sections 5.1, 6.4.)

**Freeze one sleeve.** A complete specification exists before code: identity, universe, entry and exit rules, sizing, refusal conditions, fill assumptions, pre-registered kill criteria, on a card that acts as a gate. (FG Section 14.1; KIT-04 Section 4.2; CMP Section 4.)

**Build the one path.** A single order component; deterministic identities persisted before send; a timeout treated as unknown and resolved by lookup; tests unable to reach the order path. (KIT-05; FG Section 8.)

**Ledger and reconcile.** An append-only ledger from which the book folds; reconciliation against the broker before dispatch, with scoped halt consequences and an adoption baseline from day one. (KIT-06; FG Section 4.8; D7.)

**Set risk outside the strategies.** Versioned limits enforced by a separate layer; oversize intents refused and journaled, never quietly clipped; the four safety states implemented, journaled, and drilled. (FG Section 9; KIT-07 Section 7.5.1; divergences D1, D3.)

**Operate it.** A supervisor judging liveness by effects, a heartbeat that means progress, off-box backups verified by an actual restore, and a written answer, reachable in minutes, to why the desk is not trading. (KIT-07; FG Section 11.)

**Grade honestly.** Statuses reported in the four-level vocabulary with evidence layer and boundary attached; backtests under stated assumptions against pre-registered benchmarks; published figures recomputable from their ledgers. (FG Sections 1.5, 7.5; CMP Section 6.)

**Publish nothing unledgered.** Any forecast product writes its calls to its ledger before its horizon opens, grades at fixed horizons, records abstentions with reason codes, and carries score semantics in its data. (FG Sections 4.9, 7.6, 12.10.)

**Count honestly.** One catalog entry per strategy with variants folded and identifiers preserved; any cross-desk total published only with its crosswalk, its merge-tier counts, and its unresolved entries still unresolved. (FG Sections 7.7, 7.9.)

**Close the loop on every defect.** Each bug leaves a cure at the source, a dated log entry, and a wired regression test proven to fail on the old code; anything fenced but uncured is named as open at the top of every report. (FG Sections 3.8, 11.3; KIT-00 P8.)

*End of the reconciliation. The three guides remain the authorities for their own material; where this map and a guide disagree about what that guide says, the guide is correct and the map should be fixed.*
