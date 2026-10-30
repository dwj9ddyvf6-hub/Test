# 12 — Security and secrets

## 12.1 Threat model (practical)
* **Accidental leak** of broker/data keys into git, logs, chat, backups, screenshots, status pages.
* **Prompt injection**: web pages, issue text, inbox notes, logs and tool output telling an agent to do something. They are **data**.
* **Over-permissive agents** doing destructive or external actions because a task text implied permission.
* **Account mix-ups** (paper vs live; main vs test).
* **Supply chain**: unpinned dependencies; copied scripts; vendored code changed.
* **Public status pages** leaking internal names, positions or infrastructure.

## 12.2 Secrets rules

1. Keys live in `0600` files **outside every repository and sync root** (or an OS/CI secret store). Never in `.env` files inside the repo, never in command lines, never in chat.
2. **Key files win over environment variables** in your own code: a stale value in a shell caused 401s on every call. Load, don't inherit.
3. Presence checks only: print "set / not set", never the value or its prefix. Print **lengths** at most in diagnostics.
4. `.gitignore`: `*.env`, `*_env`, `*alpaca*`, `*.bak_*`, state dirs. Backup scripts copy **tracked files only** plus an explicit allow-list of state.
5. **Secret scan** before every commit/push (regex for known key shapes, high-entropy strings, private-key headers, account-id patterns, email addresses, personal names if relevant). The scan is part of the regression harness *and* a pre-push hook *and* inside the backup script (refuse + exit non-zero).
6. If a secret reached a remote: rotate it **first**; then consider history removal (it does not un-leak). Scan every reachable ref and commit metadata; test old blob URLs; note caches and forks.
7. Secrets don't survive transit through some tooling (a secret was **redacted in transit** and arrived as a placeholder): verify by *behaviour* (an authenticated read-only call), never by printing.
8. Cloud worker secrets are stored in the platform's secret store; avoid duplicating them into a KV table; if you must, plan their removal.
9. A debug flag exposing a dev server on `0.0.0.0` is an open door; bind to `127.0.0.1`.

## 12.3 Access control
* Separate keys per account and per purpose (read-only data vs order key).
* The **order key** is readable only by the order-path process. Research code gets the read-only data key.
* Allow-list accounts; abort on identity mismatch (account suffix pin).
* Cloud failover token: random, rotatable, stored locally `0600`.
* Principle of least privilege for repo tokens (private repo write only).

## 12.4 Git and backups
* **Additive pushes only**: fetch, rebase/merge, push; never `--force`, never delete branches/tags/stashes without a human yes. A pre-push hook rejects deletions; the backup job undoes a deleting commit.
* Verify the remote after pushing: `git ls-remote <remote> <ref>` equals your local `HEAD`. A push that "worked" in the terminal but timed out is not durable.
* Private repo for state; no secrets, no raw broker account ids.
* A public repository (like this guide) contains **no** account ids, hostnames of private infrastructure, personal names, or positions.

## 12.5 Public/externally visible output
* A public status page must be **scrubbed**: no internal names, no stop levels if you consider them sensitive, no hedging jargon, no private infrastructure URLs; contract test with a deny-list.
* Do not claim performance you cannot prove; label as paper.
* Disclaimers once, clearly, not on every tile.

## 12.6 Autonomy limits (hard)
Agents never: enable live trading; place manual orders without an explicit human yes; delete data; force-push; send messages or post publicly on the human's behalf without approval; circumvent geo-blocks, rate limits meant to stop abuse, or terms of service; bring up a retired system.

A **declined or blocked action is final** — do not retry it through another tool.

## 12.7 Quick audit script ideas
* `tools/secret_scan.py` over tracked files, history, backups, evidence.
* `tools/audit_perms.sh`: key files mode ≤ 0600 and outside repos.
* `tools/audit_remote.sh`: list remotes, refs, ensure private visibility.
* `tools/audit_orders.py`: all broker orders in the last N days carry an allowed prefix.


## Addendum
A secret pasted into a chat is compromised: rotate it (P-108). Licensing, scraping and tenant-isolation boundaries are summarised in doc 17 (P-130).
