# Muse Desk — Architecture Brief for an LLM

Purpose: a single structured document from which a competent LLM can
scaffold a similar paper-trading research desk. Terms in §2 map the
system's internal vocabulary to the plain words used on reader
surfaces; reader surfaces must use the plain words only (§11).

## 1. System in one paragraph

A paper-trading research desk. ~60 autonomous strategy modules
("sleeves") each implement a pure signal function over price bars and
emit trade intents. One dispatcher turns intents into orders through
one broker transport to one Alpaca **paper** account. Every fill is
appended to one append-only ledger. Virtual-slice accounting divides
the single broker book back to strategies. A scheduler plus external
agent cron jobs run the desk on fixed cadences. A static public
terminal page, published to GitHub Pages every 5 minutes, renders a
snapshot built only from broker state + the ledger. A synthesis layer
("the Courtroom", §8) turns candidates into Best Setups cards with a
buy zone / invalidation / target, or publishes a held state with a
plain reason. Quality machinery: a dated bug log, gate-wired
regression blockers, twice-daily inspections, and a derived-state
integrity layer ("Ink", §10), live on the desk's main line.

## 2. Vocabulary map (internal → reader)

| Internal | Reader surface |
|---|---|
| sleeve | strategy (named by its record name) |
| intent | a strategy's wish to buy or sell (usually unstated; trades are narrated as facts) |
| ledger | the desk's permanent record |
| virtual slice | shares on paper, per strategy |
| curator / setups composer pipeline | never printed; setups are "the desk's" reads |
| grand synthesis / gestalt | the desk's combined read |
| family (scoring rollup) | plain family label, never the raw key |
| calibration / census / prior | never printed; rendered as one plain sentence in counts |
| GEX | a labeled model estimate of dealer positioning; context only |
| held / refusal | held, with a plain closed-vocabulary reason |

Banned on reader surfaces (non-exhaustive): curator, Grand Synthesis,
DIP_SCORE_SPEC, WYFI, Echo method, "Profit objective", "Paper only",
calibration, census, prior, raw sleeve/family keys, `source_hash`,
`config_hash`, `source_record_id`, desk-process nouns (consideration
sweep, staged direction, tie-break, the weighing, top voices, scoring
spec, zone band, the current pass). Exactly one "Paper account" badge
per page; no other disclaimer or hedging prose anywhere, including
method sections.

## 3. Core components

| Component | Contract |
|---|---|
| Sleeve contract | `SleeveConfig`; pure `signal(bars, slice_state, context) -> [Intent]`; exits are data (`ExitRule`); `Context` is injected and is the only clock a sleeve may read; self-describing registry discovered from the sleeves directory. |
| Conformance checker | Static AST check per sleeve file: FAIL on broker/HTTP/subprocess imports, file opens, system-clock reads, direct broker references. A non-conforming sleeve cannot register. |
| Data door | The one canonical bar source. Tensor bars only from a vendored, hash-pinned canonical feed; all other bars from Alpaca SIP with a ~20-minute recency clamp; Yahoo daily only for the ^VIX price; freshness labeled; non-finite values rejected. Volume on hourly-or-finer bars must be SIP (exchange-summary hourly volume is known-corrupt). |
| Dispatcher | The tick loop: refresh equity → per sleeve, data → signal → intents → submit → fills → ledger append + slice update. Exits are slice-clamped. Entries whose estimate exceeds the pass's broker buying power are desk-skipped (broker arithmetic mirrored; fail-open if the account is unreadable). Deterministic client order IDs derived from the intent; adopt-by-CID on retry so a duplicate submit cannot double-fill. Multi-leg option packages submit atomically. Side routing is fail-closed, never coerced. |
| Broker transport | The one Alpaca paper transport (paper base URL only; the live base URL is never constructed). Account, positions, orders, fills, equity; single-leg and multi-leg options submits; disaster-stop lifecycle. A dry stub exists for tests. |
| Credentials | Resolved at call time from a vault/surrogate store, keyed per provider (`custom.alpaca`, `custom.github`). No secret ever lives in either repo. |
| Risk (accounting only) | Virtual slices, sizing arithmetic sleeves may reference, exposure measurement. It never vetoes, brakes, or halts an order — a deliberate, documented doctrine: strategy rules decide trades; risk code measures and reports. Nightly reconciliation imports broker state as-is; differences are notes, never halts. |
| Gateway layer | Cross-cutting order-door machinery: held-for-orders pre-check, buying-power fairness, freshness contracts, snapshot input hash, reconciliation watermark, protection census, evaluation heartbeats, market-cap tiering. Records and decisions only; no strategy logic. |
| Ledger | One append-only JSONL file; flock + fsync per append; non-finite values rejected; torn final line is the only recoverable corruption. Nightly archive of older sessions to the archive branch of the desk repo of record. |
| State store | One JSON file per sleeve; atomic durable writes (temp file + fsync + rename); schema-validated; verbatim loads. |
| Scheduler | One in-desk runner that writes its own dead-man beats; claim-before-run cadence persistence; daily jobs anchored to America/New_York. The beat lists the registered job set, so a job census cannot drift from the code. External agent crons mirror the same jobs for wake/check duties (§7). |
| Feed builder | Builds the terminal snapshot (§6) and pushes it via the GitHub Contents API (GET sha → PUT base64). Skips the write when the input-hash fingerprint is unchanged. |
| Setups publisher | Enriches the snapshot with the board (§8) on the live push path only; fail-soft (any failed step leaves the plain snapshot publishable); one sanitizer choke point over the whole merged document before publish. |
| Static-docs publisher | Pushes fixed reader JSON (strategy descriptions, architecture summary, and any future explainer JSON) from single source files in the desk repo to the site repo. Manual on change — every new static document must be added to its file map in the same commit, or the published copy drifts. |
| GitHub mirror + backup | Nightly convergence of desk-repo history to its archive repo via the Git Data API, plus a full-desk backup job. A save counts only on post-push API read-back match; divergence files a named ledger defect row. |

## 4. Strategy population (shape, not a parts list)

60 modules, one file each, each with a written port/build spec.
Mix: a pinned third-party-style pattern engine family (engine code
vendored and hash-locked, never edited); several named external
systems ported faithfully (intraday and daily momentum, options box,
EMA trend, morning-dip); momentum/breakout and pullback/mean-reversion
families; rule-based and model-based systems; options income,
directional, and hedge sleeves; systematic allocation sleeves sharing
one pot; free-data sleeves (several are watch-only monitors that
record checks and never trade — stated plainly in their reader text);
forward-test sleeves; crypto sleeves. Reader dataset: one JSON entry
per strategy — name, summary, explainer of 80–130 words, instruments,
one category from a fixed 8-category taxonomy (all 8 used) — with a
gate test asserting the dataset covers the sleeves directory exactly
once. One strategy is parked with its reason recorded (its source
chain contains no rule for the pattern it was named for).

## 5. Trade flow (sequence)

1. Scheduler fires the scan tick (30 min) or exit sweep (5 min,
   exits-only mode; entries defer unconsumed).
2. Dispatcher refreshes broker equity and account state.
3. Per strategy: data door returns bars (or nothing — no bars, no
   signal); the pure signal function returns intents.
4. Buying-power gateway: an entry intent whose estimate exceeds this
   pass's broker buying power is desk-skipped and recorded.
5. Broker submit with deterministic client order ID; on retry,
   adopt-by-CID resolves the existing order instead of duplicating.
6. Fills return; ledger appends; virtual slices update.
7. Nightly reconcile: broker positions imported as-is; slices
   re-derived; differences filed as notes.

## 6. Terminal (public surface)

- Repo `dwj9ddyvf6-hub/Femto`, directory `docs/desk-terminal-live/`:
  a single static page (`index.html`) + service worker + web-app
  manifest + icons. Brand: title "Muse Desk", subtitle "A paper
  trading research desk", no byline names anywhere. Served via
  GitHub Pages; canonical URL declared in the page head.
- The page holds no numbers of its own. At load it fetches three
  JSON documents from the site root of the repo: the live feed
  (5-minute), the strategy dataset (static), and the architecture
  summary (static). New explainer material follows the same pattern:
  its own static JSON from a single desk-repo source file, or a
  standalone sibling page linked from the shell — never a new key in
  the trading feed.
- Feed snapshot (base layer, schema-validated): generation timestamps
  (UTC + ET), account block (whose held value is the signed sum of
  the published position rows — never equity minus cash), a
  positions-known flag, positions, position count, per-strategy
  standings, desk block (name, paper flag, strategy order), exposure,
  ledger counts, and an input-hash republication guard.
- Enrichment layer (merged only on the live push path): setups,
  entered setups, departures, completed setups, market context,
  scoring method note, the followed research feed's top list,
  timestamps, scorecard; plus on-demand reads (newest first, capped).
- Graceful degradation is a law: every panel hides or prints an
  honest unavailable state when its keys are absent, so partial
  enrichment is always safe to ship.
- Sanitizer choke point (`sanitize_published_feed`, applied to the
  whole merged document): strips internal hash/ID keys wherever they
  appear; phrase-level reader replacements; held briefs publish only
  the held state + plain reason (call, plan, branches, card all
  nulled); stop lines labeled by kind wherever two appear together
  ("Trading stop" / "Recorded stop — …" / "Disaster backstop — …");
  family keys always gain a plain label, falling back to a humanized
  name, never the raw key.
- Numbers law: every dollar total in the feed is the sum of the
  published rows of the same document (no parallel computation, no
  average-entry fallback); one name carries one 20-day exponential
  average, labeled as such — a second, different figure of the same
  name on one page is a contradiction defect.
- Shell discipline: the page's source of truth is a handoff copy in
  the desk repo, pinned by gate tests; the site-repo copy must equal
  it (a known drift here is an open defect until reconciled). The
  service worker carries a build placeholder; on shell publish, the
  placeholder is replaced with the first 12 hex characters of the
  SHA-256 of the pushed `index.html`, so any shell change renames the
  cache and the activate handler deletes older shell caches. The
  handoff copy always keeps the placeholder.
- Reader alerts: the page offers opt-in Web Push (VAPID public key in
  page config); the subscription + a pairing code are posted through
  a form relay; desk-side jobs poll for pairings and send top-tier
  alerts.

## 7. Cadence (both layers, one registry)

A generated charter roll is the single cadence source of truth,
built from the cron registry + the scheduler registrations parsed
from code; a gate-wired diff test fails on drift. Current shape:
17 external agent crons + 15 in-desk scheduler jobs.
The standing-queries job (§63) checks the followed universe
against standing questions every 30 minutes and files a note
only when a name newly matches.

| Job | Cadence |
|---|---|
| Feed publish | every 5 min (registered before the scan tick so a long scan cannot starve it) |
| Exit sweep | every 5 min |
| Heartbeat / dead-man | every 5 min |
| Top-tier reader pings | every 5 min |
| Scan tick | every 30 min |
| Standing queries | every 30 min |
| Options / gap-data refresh | every 30 min |
| Push-pairing poll | every 15 min |
| Premarket digest / premarket | 08:30 / 08:46 Mon–Fri ET |
| Followed research refresh | 18:06 daily |
| Market measurements | 18:12 daily |
| Nightly strategist reconcile | 18:15 Mon–Fri |
| Background gap products | 18:20 daily |
| Postmortem review | 19:00 daily |
| Drills | Sun 19:46 |
| Ledger archive | 23:30 daily |
| Night inspection | 00:15 daily |
| Backup (+ mirror read-back proof) | 01:46 daily |
| Morning inspection | 07:00 Mon–Fri, hard report deadline 08:40 |
| Inspection watchdogs | 08:45 Mon–Fri + 01:05 daily |

## 8. The synthesis behind Best Setups ("the Courtroom")

Frozen written contract; changes only via a proven defect or the
owner's ruling, recorded as numbered amendments.

- **Manifest:** a completeness list transcribed from the owner's
  written list, generated from the list itself and gate-diffed
  against the consideration registry — a registry edit that shrinks
  coverage fails the gate.
- **Experts:** 14 subject experts (patterns, structure, levels,
  trend, momentum, volume, divergences, stretch, candles/gaps, the
  pattern engine, the plan, options, company/market, chart-pattern
  read) + 4 special experts (visual chart read; market context —
  stance 0 by schema, never decisive; the desk's counted record;
  proofread). Each files signed testimony or a classified
  non-testimony: source impossible, source stale, reader not run,
  abstained, not applicable.
- **Arbiter:** the only weighing code. Composes the desk read from
  the docket alone — salience-weighted balance, structure-first
  tie-break, decisive vs considered bands. Refuses from a partial
  docket.
- **Refusal spine:** a brief whose docket, chart integrity, or record
  fails publishes the held state + a plain closed-vocabulary reason;
  plan fields are nulled at the publication boundary. Refusal gates
  publication only — never a trade.
- **Surface seal:** a code check that every printed price exists in
  the brief, the objective and invalidation are printed, nothing is
  truncated or doubled.
- **Production census:** runs over the actual briefs a build produced
  (never fixtures) and classifies every manifest item on every brief:
  value / allowed absence / violation.
- **Parity harness:** replays stored briefs through the weighing
  machinery to detect drift.
- **The call and the plan:** direction + final objective + evidence
  horizon + a conviction word from a fixed ladder. Plan words are
  exactly BUY ZONE / INVALIDATION / TARGET (+ FIRST TARGET). The
  trading stop keeps its own name and label. Logical reward-to-risk
  law: headline R is to the final objective (R to first target shown
  alongside); R < 1 does not board; a ladder's final rung is a
  recorded level, never a moving average's value; a sole projected
  objective caps conviction and is named as projected; every setup
  carries an expiry clock, and expiring untriggered is its own
  outcome class, not a loss.
- **Dealer-positioning estimate (GEX):** a labeled model estimate
  (Black–Scholes gamma, stated convention), context class, stance 0,
  never decisive.
- **Paid-data clones (§61):** copies of paid tools' published
  methods (dealer-positioning and options-flow figures of the
  DEX/VEX/CHEX kind) run as extra context voices. They are
  background only — they can inform a call, they can never make
  one. One of them reads executed options trades; no live record
  of those trades reaches the desk, so it files no view at all
  until one does.
- **Freshness contracts (§62):** every data product the synthesis
  consumes carries a written maximum age. Consumers check the
  product's own date against it and file any breach by name in
  their output — never silence, and never a block on a trade.
  The board publisher asserts the briefs product's own 26-hour
  contract at the board door.
- **Scorekeeping of the judges:** per-voice, per-class scorecards;
  process grade and outcome grade kept separate; blind-first review;
  an automatic leash — a voice with ≥30 scored calls and expectancy
  ≤ 0 drops one decisive-eligibility band, logged by name, restorable
  on its next 30 positive calls; the owner may override any
  application.
- **Historical pattern record:** one versioned data product at a
  single choke point. Current product: version v1, as of 2026-10-16;
  roster 1,838 names; signal span 2020-01-02 → 2026-10-16; Alpaca SIP
  split-adjusted daily bars; 364 cells. Slices under n=30 return
  counts only. Families with no lawful measured objective (8) file no
  rate. A missing, unstamped, or version-mismatched product files
  "unavailable" with the reason named. Hard line: it never backtests,
  ranks, promotes, or sizes any strategy, and never vetoes a trade.
- **Family realized record:** recomputed nightly from closed trades
  only — broker executed prices, first-in-first-out lots per
  strategy+symbol, era starting at the desk's 2026-10-14 cutover. An
  exit with no recorded price is excluded and counted, never
  approximated.
- **Charts:** every board chart draws the buy zone, invalidation,
  and targets labeled by role; the named pattern itself drawn; a
  dashed expected path into reserved future space; volume, RSI, and
  MACD panes with divergences drawn only where the record carries
  them. Chart conventions are re-checked fresh each improvement
  round against four studied published chart accounts.

## 9. Research loop

- Studies: ideas written down in advance, tested on data they were
  not built from, kept or discarded on the result; a clean rejection
  is a success.
- Improvement rounds for the synthesis: sets of 5 rounds × 20 fresh
  random names, names never repeating across rounds; every brief and
  chart visually audited by the lead against the studied chart
  conventions; defect *classes* cured at source with gate blockers
  before the next round; the next round's fresh names are the holdout
  proof.
- Strategy standing is earned from the live forward record only —
  never from backtests of the strategies themselves.

## 10. Ink — derived-state integrity layer (LIVE)

State today: landed on the desk's main line (merged 2026-10-21),
with a kernel and adapters (desk, intent, board, study, execution,
inspection, ledger, life), plus evidence files per landed wiring
phase. The terminal snapshot itself is filed through it: every
published total is an Ink desk-adapter keep derived from the
published rows, and a snapshot whose totals disagree with its rows
cannot be written or pushed (see §3, feed builder / §6). Describe it
as live and wired in; it still never gates dispatch (below).

Design: derived state is declared once as named definitions
("keeps"); the system maintains them; recomputation from sources is
the definition — any incremental strategy must equal it. Changes are
atomic transactions with declared reads/writes, enforced effects, and
commit-gating invariants: a failed invariant rolls the whole commit
back. Adapters file derived verdicts for surfaces that suffered
derived-state drift: an inspection READY verdict is derived from the
roll; a board face must equal its derived keep; a job counts as done
only when its artifact exists on disk; a cron "success" requires its
artifact; generated artifacts and saves must equal their derivations,
verified by read-back. Binding rail: Ink governs state integrity and
never gates dispatch — proven by a named gate test asserting the
trade path does not consult it.

Paid context modules (§61) are wired in, not in flight: the
clones run as background context voices in the synthesis (§8).
Freshness consumers (§62) and the standing-query job (§63) are
likewise live; see §7 and §8.

## 11. Design rules (the non-negotiables)

1. **Scope first, in writing:** surface (what changes), constraints
   (what stays untouched), outcome (observable success), proof (what
   evidence demonstrates it), edges (boundaries/dependencies).
2. **Minimum sufficient change at the source.** Preserve verified
   paths; never build a second source of truth to work around the
   first.
3. **No green without evidence from the final artifact.** Verdicts:
   GREEN (proven on the final state) / PARTIAL (bounded portion
   proven, rest named) / BLOCKED (needs authority, access, or input)
   / UNVERIFIED (changed but unproven). A worker's completion report
   is a claim until its evidence is checked. Final evidence must
   follow the last change.
4. **Route failure ≠ task impossibility.** Preserve the exact error,
   revise the hypothesis, try the highest-confidence alternative
   route. If the same class of action fails twice without a revised
   hypothesis, stop and reassess.
5. **Every fix ships twice:** a dated bug-log entry (severity, file,
   what broke, the fix; plus an investigated-and-cleared section) AND
   a named regression blocker test that fails on the old behaviour
   and passes on the new, wired into the one gate script. An unwired
   test does not count. A ratchet test recomputes blocker coverage
   every gate run: a new module or test without a wired blocker is
   red; exemption ledgers are dated, shrink-only, and stale entries
   fail.
6. **Twice-daily inspections cure, not just report:** per-strategy
   liveness roll (all named; silence is an open defect),
   malformed-emission census, desk-process audit (every cron + the
   in-desk scheduler), full suite + pinned-engine hashes. Cures land
   in-pass inside the rails; anything uncured is reported OPEN by
   name at the top. Containment is never reported as a cure.
7. **Absence is a defect:** watchdogs watch the inspections, the
   heartbeat, and the scheduler; a missing beat or report files
   itself.
8. **Broker is truth** for holdings; the ledger is truth for history;
   the page is a view, never a source.
9. **Fail closed on data, fail honest on surfaces:** no bars → no
   signal; a failed source leaves its fact absent, never synthesized;
   a panel with no data hides or says so.
10. **Reader surfaces (§2 + §6):** plain English by construction at
    the producer of each sentence — no downstream scrubber is the
    mechanism; one paper badge; totals are sums of printed rows;
    every number traces to its record.
11. **Hard rails:** the pinned pattern engine, strategy logic,
    sizing/risk parameters, and the trade path are never touched by
    publishing, explainer, or integrity work.

## 12. Repository layout patterns

```
desk-repo/
  core/            # the load-bearing modules of §3 (one door per kind)
  sleeves/         # one file per strategy
  ports/           # one written spec per strategy
  vendor/          # pinned feeds/engines, hash-checked, never edited
  config/          # reader datasets + static reader documents (JSON)
  tools/           # scheduler entry point, builders, publishers
  state/           # ledger, per-strategy state, snapshots (live, local)
  desk/            # bug logs, job registry, charter roll, handoffs,
                   # the gate script (run_regression_blockers.sh)
  tests/           # one blocker file per fix, all gate-wired
site-repo/
  docs/desk-terminal-live/   # the page, service worker, manifest, icons, setup charts
  docs/desk-terminal-feed.json
  docs/algorithms.json
  docs/architecture.json     # + any future explainer JSON, same pattern
```

## 13. Minimal viable desk (scaffold order)

1. One strategy as a pure function (prices in, wishes out).
2. One paper broker transport; keys in secure storage, never in code.
3. One dispatcher loop with deterministic order IDs.
4. One append-only record file, fsync per line.
5. One timer; one page that prints only broker + record, totals as
   sums of printed rows.
6. Then, in order: faster exit timer → per-strategy paper shares →
   nightly reconcile → heartbeat watched from outside → fail-closed
   data rule → more strategies under the same contract → the judging
   layer (§8) → guard-test gate + bug log → twice-daily inspections →
   derived-state integrity (§10).
