# Aster Desk assessment 8 October 2026

Preserved assessment of source commit `6c262bdc7b5d4e52439d59f338701ba19b62e2d6`, inspected at approximately 11:21–11:29 UTC. The owner requested that repairs be deferred. This assessment supplements the earlier audit; its new findings were not repaired in this assessment pass.

The desk has a substantial operational foundation, but its research, data and evaluation architecture needs considerably more work to meet the original ambition. Its strongest parts are accounting, execution ownership, recovery and evidence preservation. Its weakest part is the machinery for discovering and proving an edge.

All major components were reassessed and current files checked against the audit manifest. They match the version that passed 320 tests. Fresh inspection uncovered three defects those tests missed.

## Component assessment

| Area | What holds up | What materially limits it |
| --- | --- | --- |
| Accounting and execution | Independent books, atomic accounting, reservations, idempotent submissions and reconciliation are implemented. Unverified broker P&L is explicitly withheld. | Local fills use a last price and simple costs. There is no spread, liquidity, market-impact or borrowing model; complete broker activity/fees and corporate-action accounting are missing. |
| Autonomous operations | Durable jobs, leases, retries, exchange sessions, cancellation fences and restart recovery are real capabilities. | Collection, reconciliation, execution, research and notifications share a largely sequential path. Slow research/data work can delay execution and protection checks. |
| Market data | Provider timestamps, observation times, immutable revisions and corruption checks provide useful provenance. | Polling covers at most 16 symbols per pass. There is no streaming/consolidated quote service, historical universe membership or complete splits/dividends/delistings processing. |
| Agents | Operational roles perform actual audits, reconciliation, handoffs and bounded reviews. Model tools have clear authority limits. | Optional model reviews mainly annotate existing evidence. They cannot yet plan and execute a rigorous research programme or measure whether their conclusions improve decisions. |
| Research | Preregistration, source pins, append-only results, artifacts and durable dependency workflows are useful scaffolding. | Workflow tools collect sources, fetch bars, search the catalogue and package results. They do not run scientific experiments. Study results are entered by an operator. |
| Analytics and risk | Funding is separated from gains; comparisons require aligned observations; missing evidence produces withheld statistics. | There is no enforced walk-forward evaluation, multiple-testing control or candidate promotion process. Risk controls mainly cover exposure and drawdown, with limited portfolio concentration/stress analysis. |
| Charts and interface | Books, orders, evidence, operational status and uncertainty are presented coherently. | Charts are basic closing-price plots. Candles, volume, indicators, overlays and comparative study tools are absent. Raw JSON and free-form research fields impose substantial operator work. |
| Continuous operation | Backup/restore, monitoring and deployment examples exist and have verification evidence. | Permanent supervision, independent monitoring and scheduled off-host backups remain deployment work. Continuous availability is currently unproven. |

The biggest architectural gap is executable research. Tensor, technical-analysis, pattern/gestalt, tender and other research methodologies are not yet an executable analytical toolset inside this desk. Repository search helps locate work; it does not operationalize that work.

The future strategy contract records useful metadata, but does not enforce dataset boundaries, run experiments, verify results or govern promotion. Those capabilities can be built while keeping the strategy registry empty.

## Confirmed residual defects

1. **Protected stop-entry validation uses the wrong reference.** A synthetic example with a $10 quote, $20 buy-stop and $15 take-profit was accepted. After entry at $20, a subsequent $16 quote executed that target exit for a $4 loss per share before costs. Validation uses the current quote instead of the stop-entry trigger. Source: `backend/trading.py:571–582`. The symmetric short case was also reproduced. Evidence came from isolated temporary databases, explicit synthetic quotes and current production methods; no default desk trades or external requests occurred.
2. **Older active orders can disappear from oversight.** Snapshot selects the newest 1,000 intents before filtering active orders. An isolated reproduction using actual submission/cancellation methods contained one older queued order and 1,000 newer cancelled orders, but reported zero visible active orders. Execution still reads underlying records; dashboard counts and agent briefs can miss outstanding work. Sources: `backend/trading.py:633`, `frontend/src/Autonomy.tsx:66`, `backend/worker.py:333`.
3. **Standalone monitor lacks an overall request deadline.** Its ten-second setting is a socket-idle timeout. A finite loopback response trickling whitespace returned after 12.018 seconds and was accepted as healthy. Continued trickling could keep it waiting longer. The response read also has no byte limit. Source: `scripts/monitor.py:17–18`. The probe used the unmodified production monitor and contacted only a local synthetic server.

## Observed operational state

During this reassessment the local endpoint refused connections and no desk server process was running. Last stored autonomous heartbeat was 2026-10-08T08:10:12.464767+00:00. The reason for process cessation was not established. Database integrity was `ok`. Main book remained unfunded with no positions or trades; there were no registered studies or research workflows. No forward performance evidence existed to assess.

## Priorities for later repair and development

1. Repair the three defects and establish persistent supervision with independent failure detection.
2. Separate execution/protection work from slower research, collection and notification workloads.
3. Build point-in-time datasets, corporate-action accounting and measurable execution-cost assumptions.
4. Build reproducible experiment execution, feature calculations, holdout/walk-forward evaluation and evidence-based promotion gates.
5. Expand analytical tools and charts around that research pipeline.

The core is worth building on. The next major investment should be in trustworthy data and executable evaluation, allowing future strategy advantages to be tested against costs, changing markets and forward paper observations. No profitability or benchmark-outperformance claim is supported by the current desk evidence.

The symbol-list regex allegation considered during review was a false positive caused by shell/JSON escaping and was withdrawn. It is not a defect or repair item.
