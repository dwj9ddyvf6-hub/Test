# 01 — Requirements: accounts, APIs, data, compute, cost

Everything you need *before* writing code. Collect these and write the result into a `config/requirements_receipt.md` in your own repository (what you have, where secrets live, what quotas apply). Do not paste secrets into that file.

## 1.1 People and permissions

| need | why | notes |
|---|---|---|
| A **human operator** who owns the outcome | decisions about money, risk, publishing, deletion | agents advise and repair; they do not own risk |
| A written **authority list** | prevents scope creep | see `../AGENTS.md`; copy it into your repo and edit |
| A way for agents to **reach the human** | exceptions only | one channel; avoid pinging for routine repairs |

## 1.2 Accounts

1. **Source control host** (e.g. GitHub) with a *private* repository for the desk code and a second *private* location for state backups. Agents authenticate with a CLI login or a credential helper — **never** a token pasted into a file in the repo.
2. **A paper brokerage account** with an API that supports the order lifecycle you need: client order identity, lookup after timeouts, positions, fills, cancellations, and relevant order types. A separate test account can isolate experimental work. Keep credentials separate by account and service.
3. **A market-data source** with explicit feed, delay, coverage, adjustment, and licensing terms. Free and paid plans can both have gaps, limits, or restrictions. Record the actual entitlement and observed failure modes; a feed whose delay exceeds the strategy's freshness tolerance is unavailable for that decision.
4. **Optionally** a free-tier cloud function account for the failover worker (check quotas: write limits per day, CPU ms per invocation).
5. **Optionally** a static-hosting account for a read-only status page.

### 1.2.1 Buying power and account constraints
Buying power and margin treatment vary by jurisdiction, account type, instrument, broker, and time of day. Never infer overnight capacity from an intraday display. Read the broker's current account rules, apply the most restrictive relevant limit before sizing, and handle a rejection as a recorded outcome rather than retrying with a larger order. See `04` §4.7.

## 1.3 Compute

| option | pros | cons |
|---|---|---|
| Always-on small VPS / home server | simplest, predictable | you own patching and uptime |
| A VM that is **paused when idle** (some agent sandboxes) | free | **wall clock jumps, processes freeze, disk can roll back** — requires every defence in `07` |
| Containers with restart policy | easy supervision | health checks must reflect *progress* |
| Serverless only | no machine | hard for long jobs; good for failover only |

**Prototype sizing is workload-dependent.** A small daily/hourly paper service may start with modest compute, but measure peak memory, disk, data volume, concurrency, and recovery needs before choosing a host. A large cache or native ML worker can dominate resource use. Budget headroom and put a **resident-size cap with recycling** on long-lived workers.

Software: Python 3.10+ (3.11–3.12 safest for scientific wheels), `git`, `sqlite3`, a POSIX shell, `flock`, `setsid`. Optional: Node.js for a failover worker.

## 1.4 Data requirements (decide per sleeve)

For *every* data feed a sleeve reads, write down:

| field | example |
|---|---|
| source and endpoint class | "daily OHLCV from provider X" |
| **latency** | real-time / 15-min delayed / end of day + provisional |
| **completeness rule** | "bar counts only if close is non-null and low ≤ open,close ≤ high" |
| **freshness limit** | "bars older than 5 days are *missing*, not signals" |
| **calendar** | exchange tz, holidays, early closes (use a tz database, never fixed offsets) |
| **failure behaviour** | skip + alert (never guess) |
| **point-in-time safety** | no look-ahead: only data available at the decision time |
| **licence / terms** | some endpoints forbid automated use; some are geo-blocked — do **not** route around a geo-block |

Typical sources: equity bars (daily + intraday), a quote/last-trade, corporate-action data, an index-volatility level, a market calendar, optional alt-data. Crypto strategies additionally need exchange funding-rate / open-interest data; those providers may be region-blocked.

## 1.5 Cost

Costs vary by broker, feed entitlement, compute, storage, network transfer, and agent plan; free tiers can change or impose hard quotas. Price the complete workload, including overages and backups, and plan an *agent usage budget*:

* use cheap deterministic code for anything that does not need judgment (health checks, restarts, reconcile);
* wake an LLM only when a check finds an exception;
* make the wake-ups quiet when everything is healthy;
* know when your plan's limit resets and what happens when it is exhausted (see `07` §7.9).

## 1.6 Secrets inventory (names only; values never in git)

| secret | where it lives | who may read it |
|---|---|---|
| broker key/secret (per account) | file mode `0600` **outside every repository and sync root**, or the OS secret store | only the order-path process |
| data-provider API key | env var loaded from a `0600` file | data fetchers |
| failover worker auth token | cloud secret store + a local `0600` file | operator tooling |
| git credentials | CLI credential helper | git only |

Rules: the key file wins over a possibly stale shell environment; keys are never printed, logged, committed, or included in backups; a **presence check** (“is it set?”, never “what is it?”) is the only allowed diagnostic. More in `12_security.md`.

## 1.7 Requirements receipt template

Copy `../templates/requirements_receipt.md` into your repo and fill it. An agent that cannot fill a row has found a blocker; record it as BLOCKED rather than guessing.
