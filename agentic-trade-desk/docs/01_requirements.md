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
2. **A paper brokerage account** with an API (examples: Alpaca paper trading; Interactive Brokers paper via its API; others). Prefer **two** paper accounts if you can: a "main" account for conservative sleeves and a "test" account for experimental sleeves. Keep their keys in separate files.
3. **A market-data source**. Free tiers exist (Yahoo-style endpoints, the broker's free IEX-quality feed) but have delays, gaps and rate limits. A paid consolidated feed is more reliable. *Whatever you choose, record its delay and its failure modes.* (A free index-volatility feed was 15 minutes delayed; treating it as real-time made a whole family of rules unable to fire.)
4. **Optionally** a free-tier cloud function account for the failover worker (check quotas: write limits per day, CPU ms per invocation).
5. **Optionally** a static-hosting account for a read-only status page.

### 1.2.1 Reg T, margin and what "buying power" means
A margin paper account advertises *intraday* buying power (commonly 4× equity for day trades) that **cannot be held overnight** (overnight is commonly 2× under US Regulation T-style rules). If you size lanes to the intraday number, orders will start being rejected for lack of buying power on heavy days. Size to **overnight capacity** (≈ 2× equity for a margin account, 1× for a cash account) and compute the overshoot explicitly. See `04` §4.7.

## 1.3 Compute

| option | pros | cons |
|---|---|---|
| Always-on small VPS / home server | simplest, predictable | you own patching and uptime |
| A VM that is **paused when idle** (some agent sandboxes) | free | **wall clock jumps, processes freeze, disk can roll back** — requires every defence in `07` |
| Containers with restart policy | easy supervision | health checks must reflect *progress* |
| Serverless only | no machine | hard for long jobs; good for failover only |

**Minimum**: 2 vCPU, 4 GB RAM, 20 GB disk for a desk of a few dozen daily/hourly sleeves. A large research cache or a ML worker can need much more: a long-lived worker with native memory grew to several GB and, together with other jobs, triggered kernel OOM kills. Budget RAM and put a **resident-size cap with recycling** on any long-lived worker.

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

A paper desk can run at **$0–$10/month** (free broker paper account, free data, free-tier cloud function, free git hosting). The real cost is **agent usage**: each agent wake-up consumes plan credits, and a weekly usage limit exhausted mid-day took three scheduled agent runs down in one incident. Plan a *usage budget*:

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
