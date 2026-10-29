# Master-Desk (md2) Desk Program Algorithm

Created by GrokBot.

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/master-desk, commit 8907005, mdesk/).

## What it is
GrokBot's multi-sleeve paper/shadow desk program (md2), the only active GrokBot desk from 2026-10-24, when it adopted the retired Lazarus book with 0 broker mismatches. The package is the full mdesk/ tree at the referenced head: 23 files.

## How it runs (from mdesk/desk.py and mdesk/registry.py)
- One scheduler pass: data once, then exits first, then manage, then plan (Best Setups when slots bind), then entries, then reconcile, then snapshot.
- The ledger is the single writer; ids are idempotent; a restart is a ledger replay. Positions are tracked by the book finite-state machine in mdesk/fsm.py (FLAT, PENDING, OPEN, EXITING).
- Orders go through the ShadowBroker in mdesk/broker.py; a broker refusal or void no longer burns a signal: entry attempts are bounded (ENTRY_TRIES = 3).
- The registry (mdesk/registry.py) loads every sleeve from every source desk (Ausar, Lazarus, Muse engines, plus the native kz_sweep and cci_corr engines), marks retired reimplementations exit-only, and dedupes cross-desk duplicates through its merge map so one running copy trades each strategy.
- Sleeve definitions share the sleeve/feed plumbing in mdesk/sleeve.py, mdesk/data.py, mdesk/ind.py and mdesk/warm.py; mdesk/main.py is the supervisor entry point, mdesk/publish.py emits the snapshot, and mdesk/netguard.py guards outbound requests (part of the stuck-desk fixes at this head).

## Files in this package
- packages/grokbot/master-desk-md2/mdesk/__init__.py
- packages/grokbot/master-desk-md2/mdesk/bestsetups.py
- packages/grokbot/master-desk-md2/mdesk/broker.py
- packages/grokbot/master-desk-md2/mdesk/data.py
- packages/grokbot/master-desk-md2/mdesk/desk.py
- packages/grokbot/master-desk-md2/mdesk/engines/__init__.py
- packages/grokbot/master-desk-md2/mdesk/engines/ausar.py
- packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py
- packages/grokbot/master-desk-md2/mdesk/engines/cci_corr.py
- packages/grokbot/master-desk-md2/mdesk/engines/kz_sweep.py
- packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py
- packages/grokbot/master-desk-md2/mdesk/engines/muse.py
- packages/grokbot/master-desk-md2/mdesk/fsm.py
- packages/grokbot/master-desk-md2/mdesk/funding_shadow.py
- packages/grokbot/master-desk-md2/mdesk/ind.py
- packages/grokbot/master-desk-md2/mdesk/ledger.py
- packages/grokbot/master-desk-md2/mdesk/main.py
- packages/grokbot/master-desk-md2/mdesk/netguard.py
- packages/grokbot/master-desk-md2/mdesk/publish.py
- packages/grokbot/master-desk-md2/mdesk/registry.py
- packages/grokbot/master-desk-md2/mdesk/secrets.py
- packages/grokbot/master-desk-md2/mdesk/sleeve.py
- packages/grokbot/master-desk-md2/mdesk/warm.py
- docs/MASTER-DESK-MD2-ALGORITHM.md (this file)

## Sanitization note
This copy was sanitized at 11 point(s) to pass the public-repo privacy gate; the private original in the source repo named in this doc is the verbatim source.
Sanitized files in this package:
- packages/grokbot/master-desk-md2/mdesk/bestsetups.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/broker.py: 2 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/engines/cci_corr.py: 2 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/engines/kz_sweep.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/engines/lazarus.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/engines/muse.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/main.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/netguard.py: 1 occurrence(s) replaced
- packages/grokbot/master-desk-md2/mdesk/warm.py: 1 occurrence(s) replaced
