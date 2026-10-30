# skeleton/ — generic reference code

Dependency-free Python 3.10+ (stdlib only). **Paper / simulated use only.** This is not a complete desk:
it is the smallest set of modules that encode the hard-won invariants in `../docs/`.

```
cd skeleton && python3 -m unittest discover -s tests -v      # 19 tests, all should pass
```

| module | invariant it encodes | doc |
|---|---|---|
| `deskkit/ids.py` | decision ids come from *data*, never from the pass clock; deterministic client order ids | 05, 10 (P-01) |
| `deskkit/ledger.py` | append-only, hash-chained, replayable event ledger | 06 |
| `deskkit/fsm.py` | position state machine with loud illegal transitions | 05 |
| `deskkit/store.py` | file lock + atomic write + add-only merge of foreign adoptions | 06, 10 (P-05) |
| `deskkit/netguard.py` | hard total deadline per request, GET-only retries, pass deadline | 07, 10 (P-08) |
| `deskkit/clock.py` | exchange tz, monotonic deadline, VM-pause jump detector | 07 |
| `deskkit/broker.py` | shadow vs paper broker, send-unknown vs refused, tick rounding, final states | 05 |
| `deskkit/caps.py` | lane slots (queued entries hold slots), budget vs overnight capacity | 04 |
| `deskkit/heartbeat.py` | progress-gated heartbeat, standby arbitration | 07 |
| `deskkit/reconcile.py` | book vs broker with pending tolerance, orphan import | 06 |
| `deskkit/alerts.py` | alert-don't-halt, deduped | 07 |
| `deskkit/gates.py` | allow / wait / skip; unknown ⇒ wait | 02, 05 |
| `deskkit/quotes.py` | reference-price fallback chain with tags | 05 |
| `deskkit/datahub.py` | Missing ≠ evidence; versioned bounded cache | 02, 08 |
| `deskkit/scheduler.py` | aligned ticks, one catch-up, guaranteed window pass | 07 |
| `deskkit/desk.py` | the pass: recover → exits → entries → reconcile, sleeve isolation | 02, 05 |
| `tools/secret_scan.py`, `tools/regress.py` | pre-push scan; harness where SKIP ≠ PASS | 08, 12 |
| `ops/ensure_desk.sh` | single-instance supervisor, TERM→KILL, setsid, VM-pause grace | 07 |
| `ops/mono_timeout.py` | monotonic timeout wrapper for long jobs | 07 |
| `ops/failover_worker_sketch.js` | cloud standby that trades only when the primary is stale | 07 |
| `ops/backup_additive.sh` | additive, retried, secret-scanned off-box backup | 12 |
