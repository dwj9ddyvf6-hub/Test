# FIX LANE F2 — SHIM TYPE DEFECTS

SCOPE: Surface = shim/adapter extra-field stamps in muse-desk-v3 (desk3/sleeves/*.py, desk3/bridge.py, desk3/port4_bridge.py, adapters/, adapters3/) paired with their consumers (desk3/vendor/sleeves/*.py, desk3/strategies/*.py, sleeves/*.py). Constraints = Tensor engine and pins untouched, saty_sol byte-pin untouched, shim-side changes only, no vendor strategy logic rewritten. Outcome = iron_condor evaluates cleanly on sessions from 2026-09-01 and every same-class mismatch on the desk is cured or recorded checked-and-cleared. Proof = census table below, blocker tests fail-pre/pass-post, 19-session fixture replay crash-before/clean-after.

## THE KNOWN DEFECT, REPRODUCED BEFORE THE CURE

Fixture drive of `desk3.sleeves.iron_condor.evaluate` (snapshot view: NBIS 1Day bars + VIX 1Day bars, no params-extra vix), 19 sessions from 2026-09-01 (every weekday 2026-09-01..2026-09-14 plus weekly samples to 2026-11-13), pre-cure tree:

```
2026-09-01 CRASH TypeError: float() argument must be a string or a real number, not 'tuple'
... (all 19 sessions identical)
TOTAL sessions=19 ok=0 crash=19
```

Root cause: the shim's GAP-CURE stamped `derived["vix"] = (float(last), float(prev), date_iso, "cache")`, a 4-tuple, while the vendor strategy documents `extra["vix"]: float | None` and calls `float(vix)` (desk3/vendor/sleeves/iron_condor.py:417).

## SECOND DEFECT FOUND BY THE CENSUS DRIVE (masked by the first)

With the vix cure applied, the same drive on the LIVE options payload shape (desk3/producers.py `build_options_payload`: `chains {UND: [flat rows]}`, quotes {OCC:{bid,ask}}; same shape in runtime/options_warm.py generic windows) crashed on all 19 sessions:

```
CRASH AttributeError: 'list' object has no attribute 'get'   (19/19, full mode)
```

The shim merged the payload's chains dict through untouched, so `extra["chains"][SYM]` was a flat list; the vendor documents `{SYM: {"put": [...], "call": [...]}}` and `build_condor` calls `chain_by_kind.get("put")`. Same defect class, same shim, same field family — cured the same way.

## CENSUS TABLE (mechanically built: AST over stamp sites + consumer use sites, then per-pair verification against the consumer's documented contract)

Method: /tmp/census_f2.py (AST: every `extra[field]=` / `derived[field]=` / `setdefault` / dict-literal stamp in desk3/sleeves/*.py, desk3/bridge.py, desk3/port4_bridge.py — 58 stamp sites — plus consumer expectations from AST use sites in desk3/vendor/sleeves/*.py and desk3/strategies/*.py), extended by repo-wide grep for constructed-type stamps (`tuple(`, `float(`, `int(`, `str(`, list/dict literals) across adapters/, adapters3/, laz_sleeves/, aster_sleeves/, desk3/ and paired by hand against each consumer's documented contract where AST inference is ambiguous.

| # | field (shim → consumer) | stamped type | expected type | verdict |
|---|---|---|---|---|
| 1 | iron_condor `vix` (desk3/sleeves/iron_condor.py → vendor iron_condor) | 4-tuple (last, prev, date, "cache") | float \| None (`float(vix)`, vendor doc) | **MISMATCH — CURED** |
| 2 | iron_condor `chains` (same shim → vendor build_condor) | {SYM: [flat rows]} (live producer shape, merged untouched) | {SYM: {"put": [...], "call": [...]}} (vendor doc) | **MISMATCH — CURED** |
| 3 | iron_condor `quotes` | {OCC: {bid, ask}} | {OCC: {bid, ask}} | cleared |
| 4 | iron_condor `iv` | {SYM: float} (ctx.iv_history current) | {SYM: float} | cleared |
| 5 | iron_condor `iv_history` | {SYM: [float]} | {SYM: [stored IV obs]} | cleared |
| 6 | iron_condor `earnings_in_days` | {SYM: int days} (DictComp) | {SYM: int \| None} | cleared |
| 7 | iron_condor `sleeve_state` | {SYM: {"position": {...}}} (state_common) | same | cleared |
| 8 | leaps_momentum `chains` | {SYM: [flat rows]} | {SYM: [rows]} (vendor doc: calls list) | cleared — flat is correct here |
| 9 | leaps_momentum `quotes` | {OCC: {bid, ask}} | same | cleared |
| 10 | leaps_momentum `momentum_book` | {SYM: {"qty": float}} | dict (`.get`, membership) | cleared |
| 11 | leaps_momentum `momentum_book_age_days` | float \| None | float — vendor wraps `float(...)` in try/except, None fails closed by design | cleared |
| 12 | gate_1h `bars_1h` | {SYM: [bar dicts]} | {SYM: [bar dicts]} | cleared |
| 13 | gate_1h / leader_d / leader_sc `last_event` | {SYM: "YYYY-MM-DD"} | {SYM: "YYYY-MM-DD"} | cleared |
| 14 | gate_1h `last_entry_bar` | {SYM: float epoch \| None} | float — vendor `float(prev_t)` try-guarded | cleared |
| 15 | leader_sc `weekly` | {SYM: [bar dicts]} | {SYM: [bar dicts]} (`.items()`) | cleared |
| 16 | legends_ema `bars_15m_by_session` | [[bar, ...], ...] (list of sessions) | [[bar, ...], ...] (vendor doc) | cleared |
| 17 | legends_ema `daily_ranges` | [float] | [float] (`float(r)` per item) | cleared |
| 18 | legends_ema `legends_ema_exp_journal` | dict (serve_journal) | dict (vendor adopts dict stamps) | cleared |
| 19 | fwd_coinbase_sma200 `history` | [{date, close, complete, forming}] | list of records (vendor doc) | cleared |
| 20 | fwd_coinbase_sma200 `quote` | {as_of, bid, ask} dict | {as_of, bid, ask} dict | cleared |
| 21 | fwd_alpaca_ada_rsi2 / fwd_alpaca_link_ai_volume / fwd_coinbase_sma200 `held_qty` | float (held_map casts float) | float (`float(extra.get("held_qty") or 0)`; coinbase try-guards) | cleared |
| 22 | fwd_alpaca_ada_rsi2 / fwd_alpaca_link_ai_volume `entry_close_at` | str (ISO) | ISO string (string-compared in vendor decide) | cleared |
| 23 | free_kraken_enj_spot `book` | dict passthrough (kraken_inputs) | dict {bids, asks} (isinstance-guarded) | cleared |
| 24 | free_kraken_enj_spot `sleeve_state` | {SYM: {qty, entry_due_at}} or {SYM: {"position": {...}}} | consumer `_position` walks both served shapes by design | cleared |
| 25 | free_kraken_link_basis `basis` / `quote` | passthrough (kraken producer shapes) | dict shapes documented in strategy | cleared |
| 26 | free_kraken_link_breakdown / _crowded `quote` | passthrough dict | dict (`.get`) | cleared |
| 27 | free_kraken_link_crowded `funding_rates` | list passthrough (view kraken.funding rows) | [{timestamp, fundingRate}] (strategy doc) | cleared |
| 28 | free_opt_parity `parity_quotes` | chain["quotes"] (dict or list) | consumer `_normalize_quotes` accepts dict AND list explicitly | cleared |
| 29 | free_opt_parity `parity_spot` | float | float (`float(spot)`) | cleared |
| 30 | bridge.py / port4_bridge.py `cash` | float \| None (slice cash_usd) | float (`float(extra.get("cash") or 0)`, free_opt_wheel) | cleared |
| 31 | bridge.py / port4_bridge.py `session_dates` | [str "YYYY-MM-DD"] sorted | list of date strings (`extra.get(...) or []`, free_opt_*) | cleared |
| 32 | port4_bridge.py `last_exit_date` | str [:10] | date string | cleared |
| 33 | port4_bridge.py `last_rebalance` / `meta` | str / dict | str / dict (momentum_rotation) | cleared |
| 34 | bridge.py / port4_bridge.py `sleeve_state` / `sleeve_state_flat` | {SYM: {"position": {...}}} / {SYM: {qty, entry_due_at}} | consumers read the profile they are served (state_common / flat walkers) | cleared |
| 35 | bridge.py `held_qty` / `entry_close_at` | numeric qty / ISO str passthrough | no consumer in the bridge family reads held_qty (only port-4 fwd_* do, via their own stamps, row 21/22); type is numeric regardless | cleared |
| 36 | adapters/beatendown.py `vix` | 4-tuple (last, prev, date, "cache") | **tuple** — sleeves/beatendown.py documents `"vix": (close, prev, asof_iso, source)` and unpacks it | cleared — deliberately not a bug |
| 37 | adapters/confluence.py `vix` | 4-tuple | **tuple** — sleeves/confluence.py documents and unpacks the same tuple | cleared — deliberately not a bug |
| 38 | adapters/momentum.py `vix` | 4-tuple | **tuple** — sleeves/momentum.py documents `"vix": (close, prev_close, asof_iso, source)`, unpacks it | cleared — deliberately not a bug |
| 39 | adapters/vix_hedge.py `vix_closes` | [float] | [float, ...] (strategy doc) | cleared |
| 40 | adapters/vix_hedge.py `vix_hedge_import` | {occ, contracts int, expiry str, entry_premium float} | dict adopted whole (strategy doc) | cleared |
| 41 | adapters/spx_premium.py `chains` | payload chains {XSP: [rows]} | {"XSP": [rows]} (strategy doc) | cleared |
| 42 | adapters/earnings_buyback.py `scan_signals` / `scan_age_days` | list / float passthrough (buyback_scan product) | [rows] / float (strategy doc) | cleared |
| 43 | adapters/milkman_0dte.py `spx_probe` / `book_pnl` | {available bool, underlying, why} / float | same (strategy doc; book_pnl compared numerically) | cleared |
| 44 | adapters/shen_fade.py `fresh_quotes` | {OCC: {bp, ap, t}} | dict per OCC (consumer `.get(occ)`, isinstance dict) | cleared |
| 45 | adapters/saty_*.py `chains` / `quotes` / `fresh_quotes` (serve_options) | {SYM: [rows]} / {OCC: dict} | consumer `(extra.get("chains") or {}).get(SYM) or []` — list expected | cleared (saty_sol read-only; untouched) |
| 46 | adapters3/saty_gpt_v02.py `bars_10m` | {"SPY": [agg bars]} | dict {SYM: rows} (consumer isinstance dict check) | cleared |
| 47 | adapters/* `meta` (bb_rsi, trullas_*, grok_sr_spy, teddy_orb_spy, przm_*, bta_onebar_*, soxl_pm_breakout, ~15 adapters) | {last_evaluated_bar_by_symbol: dict} | dict (consumers read the same key) | cleared |
| 48 | adapters/bb_rsi_divergence.py `active_universe` / `session_orders` / `session_fills` / `latest_quote` / `bar_cursor_ready` | list / list / list / dict / bool | list iterated / list / list / quote dict / `is not True` bool check in sleeves/bb_rsi_divergence.py | cleared |

Census result: **48 field pairs checked; exactly 2 genuine mismatches (rows 1–2), both in desk3/sleeves/iron_condor.py; 46 checked-and-cleared.** Coverage: every stamp site in the port-4/bridge layer (58 AST sites), every constructed-type stamp in adapters/ + adapters3/, and the passthrough products those adapters forward. Passthrough stamps (producer-shaped values forwarded untouched) are cleared only where the consumer's documented/normalizing code accepts the producer's shape, as tabled.

## CURES (shim-side only; vendor strategy, Tensor engine/pins, saty_sol untouched)

File: `desk3/sleeves/iron_condor.py` (+37/−4 lines)

1. **vix**: `derived["vix"] = float(_vb[-1]["c"])` — the scalar last VIX close, matching the vendor's documented `float | None` contract.
2. **chains**: new `_chains_by_kind(rows)` helper in the shim; the chain merge now groups flat producer rows into `{"put": [...], "call": [...]}` per underlying (kind from the row's `right`/`type` field, else the OCC symbol's C/P designator). A chain already grouped by kind passes through untouched, so the params/fixture channel — which serves the documented shape and takes precedence via make_old_context setdefault — is byte-for-byte unchanged in behavior.

Commit: `5dbc57c` (on HEAD 2574393, which had landed over the task's stated 87a3956 during the run; message: "F2-SHIM-TYPES-20261115: cure iron_condor shim extra-field type defects …"). Committed files exactly: desk3/sleeves/iron_condor.py, tests/test_shim_type_f2_20261115_blockers.py, BUGLOG_2026-11-15.md (F2 section only — staged via the index so the parallel F3 lane's BUGLOG work was not swept in).. BUGLOG entry: BUGLOG_2026-11-15.md, section F2-SHIM-TYPES-20261115 (the repo's dated bug log lives at the repo root; there is no desk/ directory in this repo — the entry follows the standing root BUGLOG convention, including the deliberately-not-bugs section).

## REGRESSION BLOCKERS

File: `tests/test_shim_type_f2_20261115_blockers.py` — 6 tests:

- `test_vix_stamp_no_crash_from_2026_09_01`
- `test_vix_scalar_gate_actually_compares` (VIX 40 → no entry; VIX 20 → 4-leg entry: the cured scalar is really compared, not swallowed)
- `test_chains_live_flat_shape_reaches_build_condor`
- `test_chains_by_kind_grouping_and_occ_fallback`
- `test_replay_sessions_2026_09_01_onward_zero_crashes` (19 sessions × bare + full modes)
- `test_tuple_vix_consumers_checked_and_cleared` (guard: rows 36–38 stay tuple-correct)

Fail/pass proof:
- Cured tree: **6 passed** (pytest, 0.88s).
- Pre-cure: preserved copy of the pre-cure shim at /tmp/f2_precure/desk3/sleeves/iron_condor.py (sha256 dfcdf73cdcef65114ea3a93b339a3e9d34e4698e354e9b2a8bfcfb7945bef61b, taken before any edit) assembled into a symlink-farm shadow tree /tmp/f2_precure_tree (cured tree never overwritten): **5 failed, 1 passed** — failures are the defect signatures (TypeError at desk3/vendor/sleeves/iron_condor.py:417, AttributeError in build_condor, missing _chains_by_kind); the 1 pass is the checked-and-cleared guard, which passes both directions by design.
- Neighboring suites on the cured tree: test_port_batch4_blockers + test_sleeve_firing_20261111_blockers + test_iv_producer_20261114_blockers — **22 passed, 22 subtests passed** (includes the vendor byte-pin check: desk3/vendor/sleeves/iron_condor.py sha256 566bc90eef756a6f67532bfe6ad298f7c4e25b056c8359b5145c8c16bb0d48df, unchanged).

## IRON_CONDOR CRASH-BEFORE / CLEAN-AFTER EVIDENCE

Fixture drive (/tmp/f2_repro.py, same 19 sessions 2026-09-01..2026-11-13 in both modes):

| mode | pre-cure | cured |
|---|---|---|
| bare (VIX bars only) | 19 CRASH (TypeError float(tuple)) / 0 OK | 19 OK / 0 crash, intents=0 (no chains/IV served — fail-closed, as designed) |
| full (live-shaped chains + IV + earnings) | 19 CRASH (TypeError; after vix-only cure: 19 CRASH AttributeError list.get) | 19 OK / 0 crash, **intents=4** every session (the designed 4-leg condor fan-out fires) |

STATUS: GREEN — evidence from the final committed tree (5dbc57c, re-run after the commit, no post-test changes): blocker suite 6/6 passed; 19-session fixture replay from 2026-09-01 clean in both modes (bare: 19 OK/0 crash; full live-shaped: 19 OK/0 crash, 4-leg entry every session) against 19/19 crashes pre-cure; neighboring suites 22 passed; census of 48 pairs closed (2 cured, 46 checked-and-cleared) in the table above and in BUGLOG_2026-11-15.md §F2-SHIM-TYPES-20261115.
