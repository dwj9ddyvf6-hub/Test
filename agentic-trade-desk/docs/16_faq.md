# 16 — FAQ and decision guide

**Which broker/data should I use?** Any broker with a paper account, an order API supporting client order ids and lookup by them, bracket/stop orders, and read access to orders/positions. Free data is fine for a paper desk if you record its delay and failure modes. Start with what you can get working end-to-end; abstract behind the `Broker` interface.

**How many sleeves should I start with?** One. Then three. A desk with hundreds of sleeves was only operable because of the inventory, exit audit, rehearsal and load tooling. Add sleeves at the rate you can add *evidence*.

**Shadow or paper first?** Shadow. Then paper with tiny size on one lane. Compare shadow and paper decisions for the same signals before widening.

**Should a failing monitor halt trading?** No. Alert. Per-trade stops are the only automatic halts. A human can say stop.

**What if the data provider is down at the decision window?** Entries `wait` (retry later in the window, drop only at the deadline); exits wait and alert; never guess a price. Use the quote chain with tagged fallbacks.

**How do I know the book equals the broker?** Reconcile every pass with pending-order tolerance; replay the ledger; compare hashes in the restore drill.

**When is it OK to cap a lane?** When you decide a risk or capacity limit. Record the decision, the date and who made it, keep the undo copy, and *measure what the cap blocks*. Reverse it if evidence shows valid signals are being starved.

**My sleeve never trades.** Check in this order: mode; window; market-condition gate; data freshness; lane cap; cash; refused orders; "already taken" keys; whether the strategy rarely fires by design. Read the per-fire reasons log.

**Backtest says +X%. Can I deploy?** Not on that evidence. Shadow forward, measure on fresh data, use the right statistic, count costs, and expect shrinkage. Most ideas die; that's the pipeline working.

**Why not let the LLM decide trades directly?** Model output is never parsed into an order. LLMs may *propose* sleeves, review diffs, summarize, repair infrastructure, and *explain*. Orders come from deterministic sleeve code through gates. This keeps behaviour testable, replayable and auditable.

**Can an agent run the desk 24/7?** The *desk* runs 24/7 (scripts). Agents wake on a schedule to check and repair. Don't make an LLM session the supervisor.

**What about options, shorts, crypto?** Model them honestly (options ×100, premium, intrinsic expiry; shorts cover with a buy; crypto 24/7 with its own data and geo constraints) or keep them shadow-only until the broker/data support them. Never mix them silently into an equities book.

**How do I handle a corporate action (split/dividend)?** Use adjusted data for signals and raw broker positions for the book; reconcile in shares; treat a share-count change with no fill as a corporate action alert, not a mismatch to "fix".

**How do I share work with another agent?** A dead-drop inbox file in a private repo, append-only, self-contained messages; see `09`.

**How do I know when I'm done?** When the pre-open checklist is green for three sessions without intervention, the restore drill and boot drill pass, and a fresh agent can resume from the files alone. Then keep improving the *evidence*, not the headline.

**Is any of this a recommendation to trade?** No. It is engineering guidance for paper-trading automation. See the risk note in `00` and `README.md`.
