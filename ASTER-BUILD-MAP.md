# ASTER BUILD MAP — muse-desk-v3 (Aster adoption intake, 2026-10-24)

Status: PARTIAL by design — this is the intake/build map. No Aster sleeve is
built yet; every row below is UNVERIFIED until its batch lands with fixtures
and a gate-wired blocker.

## SCOPE
- Surface: the 155 genuinely-new Ausar/Aster catalog rows (TSV
  `~/workspace/user/files/sleeve-catalog.tsv`, census
  `AUSAR-ASTER-CENSUS-2026-10-24.md`) mapped to buildable v3 sleeves.
- Constraints: work only in muse-desk-v3; v2 read-only; staged archive
  read-only; paper only; Tensor ENGINE untouched (Aster Tensor rows consume
  Tensor products at the sleeve layer); Best Setups vendored tree untouched;
  saty_sol byte-pin untouched (not in this set).
- Outcome: every one of the 155 rows names its archive implementation
  file(s), or its named missing piece + fallback, plus its slice mapping,
  grouped into build batches.
- Proof: §1 archive re-verification (hashes recomputed in this pass);
  §2 coverage ledger (counts reconcile exactly); blocker
  `tests/test_aster_intake_blockers.py` (gate-discovered) re-checks this
  map's coverage, the batch partition, and — while the staged archive
  exists — the §1 hash verdict.
- Edges: live feeds (funding, earnings events, opening events, OPRA) are
  v3 producer inputs, not archive files; a sleeve whose producer is not
  yet wired is UNFED in the v3 registry, never fed invented data.

## 1. Archive re-verification — GREEN (recomputed 2026-10-24, this pass)
Staged archive: `~/.scratch-ausar-archive/handoff-20261024/` (read-only).
Method: SHA-256 + byte count of every entry in
`provenance/SOURCE_FILES_R25.json` (582 entries), resolving each path
against the tree roots `''`, `source/`, `sleeves/` (first existing wins);
plus every entry in `PACKAGE_MANIFEST.json`.
- R25 entries resolving to a file: 205. **Exact hash+size: 204.**
  Mismatches: **1 — `README.md` only** (the handoff's own README,
  sha256 `2a30ef64…` vs the source repo README `39bde3cc…` in R25):
  the known non-source difference. **Source mismatches: 0.**
- R25 entries absent from the handoff: 377 (582 − 204 exact − 1 README).
  This matches the package manifest's own accounting
  (204 present / 378 not-exactly-present / 0 mismatched), the 378th
  being that same README.
- `PACKAGE_MANIFEST.json`: **208/208 files exact** (204 source files +
  2 provenance files + the source-map + the handoff README), 0 missing.
- Source-map: 169 rows, 89 dependency files, 0 dependencies missing
  (per manifest, and every dependency path resolves under `source/`).

## 2. Coverage ledger
- TSV catalog: 160 rows = **155 genuinely new** + 5 duplicates
  (`midna_*` rows 9–13 → v2 `em_1587`, `po10_qqq`, `saty_day`,
  `saty_sol_0dte`, `saty_sol` — excluded here, already on the roster).
- Source-map: 169 rows = **154 mapped 1:1 to the 155** (assignments were
  matched against the archive rules books — `options_rules.json` books,
  `etf_rules.json` sleeves, `tensor/RULES.json` weekly/timing entries,
  `crypto_rules.json` family/capacity arms — not by name similarity)
  + **15 unmapped, all `unfunded_monitor`**: 6 options monitors
  (`OPT_OWN_IV_RESIDUAL`, `OPT_PARITY_MONITOR`, `OPT_RELEASE_CONVEXITY`,
  `OPT_STATIONARY_PAIR`, `OPT_TAIL_STATE`, `OPT_WHEEL_LIFECYCLE`) and
  9 crypto collectors (`R19_{ADA,ENJ,LINK}USDT_{BASIS_REPAIR,
  BREAKDOWN_BASE,CROWDED_LONG_FAILURE}_COLLECTOR`). Monitors/collectors
  have no TSV row and no order authority — they are NOT built as sleeves;
  they are named here so the ledger reconciles (154 + 15 = 169).
- The 155th row, `saty_research`, has **no source-map row and no file
  in the handoff** — see §4. (154 mapped + 1 unmapped = 155.)
- Row keys below are `<family>::<exact_variant>`. The catalog reuses
  variant text for 11 keys (recovery fixed/touch pairs, the two
  `native_trend`, `cloud`, and `overnight` rows): keys repeat exactly
  as the catalog repeats them, and the TSV row # + book + parameters
  in each table row disambiguate. 155 table rows, 144 distinct keys.

## 3. Slice convention (applies to every row)
Each Aster sleeve gets the standard v3 slice: **$10,000**
(`slice.capital_usd = slice.cash_usd = 10000`).
Book-relative sizing is preserved semantically, never copied as absolutes:
the source books ran on $100,000 initial capital (stated in
`options_rules.json`, `etf_rules.json`, and `tensor/RULES.json` books), so
every fraction of the source book is applied to the $10,000 slice and
every absolute source-book dollar amount is scaled by 1/10:
`entry_cap_equity`, `risk_fraction`, `notional`, `risk`, and
`gross_target` multiply the slice; C1/G4/BETA `ticket` $4,000 → $400 and
$10,000 → $1,000 per position; `core_fraction` 0.95 → $9,500 core /
`premium_reserve_fraction` 0.05 → $500 reserve; `target_weights`
percentages apply to the slice; crypto `fullcash` = the full slice cash
and `volume1pct` / `entry_cap_native_dv` are market-relative and stay
unchanged. Per-row mappings are in the tables. One flag: ETF
`gross_target` 1.5 rows were leveraged in the source book — the mapping
records a $15,000 target exposure on a $10,000 slice; the v3 dispatcher's
intent-time buying-power check governs execution and the sleeve must
never silently cap the target itself.

## 4. Named missing pieces + fallbacks (census PARTIAL gaps, re-checked against the archive)
- **saty_research (1 row) — SOURCE ABSENT.** Named missing piece: the
  strategy itself, `deployment/2026-10-23/saty-research-v030/` (README +
  `upstream-engine-v030-clean/provenance.json`) — not in the handoff,
  not in R25's present set; the 10 independent setup families'
  entry/invalidation rules exist nowhere in the TSV or archive.
  Fallback: **TSV-as-spec** for the meta-ranker shell only (ranking,
  0.25% risk, 3 entries/day, 2R limits, deadlines, 5s quote freshness);
  the sleeve stays UNFED/monitor-only until the v030 source arrives.
  Do NOT invent the 10 setup families.
- **Tensor lineage families (tensor, C1, G4, BETA, tensor_leaps,
  hourly swing):** the canonical v698 feature definitions the census
  flagged (buy-cyan, buy-green, M2 cohort, Tensor balance/votes, swing
  geometry) ARE in the archive (`r19_tensor.py`, `tensor/RULES.json`,
  `tensor_engine.py`, frozen daily models under
  `strategies/tensor_daily20/models/`). Build rule: consume them as
  **our own canonical Tensor v698 products at the sleeve layer** (the
  v3 Tensor bundle), exactly as the census lineage flags prescribe;
  the Tensor ENGINE is never modified or rebuilt.
- **public_recipe spot rows (3):** archive carries the adapter +
  all three Pine sources. Fallback/cross-check: the public TradingView
  originals named in the TSV (`AI Volume Strategy` by szymonsobkowiak,
  `IU BBB` by Shivam_Mandrai, `2-Period RSI (with filter)` by
  Tomazetti) — public sources for `public_recipe`, per the catalog's
  `family_external_sources`.
- **Crypto funding families (absorption_negative_funding,
  absorption_nonnegative_funding, negative_funding_squeeze — 42 rows):**
  rules complete in the archive; the named missing piece is the **live
  perp funding feed**. Archive `r19_crypto_data.py` implements the
  Binance futures `fundingRate` capture (with the HTTP-451 condition in
  `crypto_rules.json`: no alternate-venue substitution) — port that
  capture as the v3 funding producer; until it lands the sleeves are
  UNFED. This is the same feed named in desk logic-gap ruling #6.
- **pead (4):** named missing piece = the **earnings-occurrence feed**
  (archive `pead_signal` consumes snapshot `earnings_events`); wire the
  v3 earnings producer. The numeric response trigger the census found
  missing in the TSV is in `r19_options.py::pead_signal`.
- **opening_gamma (2):** named missing piece = the **opening-event
  producer** (snapshot `opening_reversal_events`: causal R5 + completed
  opening 5-min breaks). The window/break clocks the census found
  missing in the TSV are in `r19_options.py::_opening_event_clocks`
  (09:35–09:45 ET window, flat 10:00 ET).
- **xsp_pcs (4):** regime/spread construction lives in
  `r19_options.py`; the rules books carry no symbols/DTE/delta for XSP
  (snapshot-supplied candidates) — named missing piece = the
  **index-regime + XSP chain producer** (native index spot + OPRA).
- **recovery / core_reserve (18):** `R17/R18 options/CANDIDATES.json`
  are NOT in the handoff; their extracted content IS —
  `options_rules.json` books give universe [IWM, QQQ, SPY], DTE,
  delta, and (core_reserve) `core_fraction`/`premium_reserve_fraction`.
  Use the rules books as the authoritative substitute. Remaining named
  gap (core_reserve only): the core leg's instrument/rebalance rule is
  stated nowhere in the TSV; the book id `OPT_QQQ95_*` + the 0.95 core
  fraction are the archive's only core-leg facts — resolve from
  `r19_options.py` at build time, do not invent a core instrument.
- **etf basket rows (19 PARTIAL):** basket membership the census found
  missing in the TSV IS in `etf_rules.json` (universe: QQQ, SPY, SMH,
  XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY + QLD fund
  terms). No fallback needed.
- **cloud / overnight (4):** stop/target derivation (cloud) and the
  equity universe (overnight) missing from the TSV are in
  `r19_timing.py` + the `tensor/RULES.json` timing entries (frozen
  42-name enrollment, per-entry risk/notional/fee). No fallback needed.
- **Original Tensor daily/state rows (4):** frozen tree models +
  thresholds ARE in the archive (`tensor_daily20/models/*.joblib.gz` +
  exported JSON oracles). Build consumes the model artifacts as data;
  no refit.

## 5. Build batches (~10, family-grouped, TSV order)
- **Batch 1 (10):** `public_recipe::RSI2 dip rebound · 1d`, `public_recipe::Volatility-squeeze breakout · 1d`, `tensor::Hourly multi-indicator recovery · hourly`, `tensor::Weekly multi-indicator recovery · weekly`, `confirmed_absorption::Four-hour confirmed absorption · ENJUSDT`, `confirmed_absorption::Four-hour confirmed absorption · LINKUSDT`, `native_trend::Daily SMA200 spot allocation`, `native_trend::Daily SMA200 spot allocation`, `opening_gamma::Opening-range options · long, 2.0% risk`, `opening_gamma::Opening-range options · long, 0.5% risk`
- **Batch 2 (10):** `pead::Post-earnings response · long, 2.0% risk`, `pead::Post-earnings response · long, 0.5% risk`, `pead::Post-earnings response · vertical, 2.0% risk`, `pead::Post-earnings response · vertical, 0.5% risk`, `core_reserve::Core exposure plus option reserve · RSI2, long, 0.5% risk`, `core_reserve::Core exposure plus option reserve · RSI2, vertical, 0.5% risk`, `recovery::Options recovery · RSI2, long, 2.0% risk`, `recovery::Options recovery · RSI2, long, 0.5% risk`, `recovery::Options recovery · RSI2, long, 2.0% risk`, `recovery::Options recovery · RSI2, long, 0.5% risk`
- **Batch 3 (10):** `recovery::Options recovery · RSI2, vertical, 2.0% risk`, `recovery::Options recovery · RSI2, vertical, 0.5% risk`, `recovery::Options recovery · RSI2, vertical, 2.0% risk`, `recovery::Options recovery · RSI2, vertical, 0.5% risk`, `tensor_leaps::Tensor long-dated calls · long, 2.0% risk`, `tensor_leaps::Tensor long-dated calls · long, 0.5% risk`, `recovery::Options recovery · VWAP20, long, 2.0% risk`, `recovery::Options recovery · VWAP20, long, 0.5% risk`, `recovery::Options recovery · VWAP20, long, 2.0% risk`, `recovery::Options recovery · VWAP20, long, 0.5% risk`
- **Batch 4 (10):** `recovery::Options recovery · VWAP20, vertical, 2.0% risk`, `recovery::Options recovery · VWAP20, vertical, 0.5% risk`, `recovery::Options recovery · VWAP20, vertical, 2.0% risk`, `recovery::Options recovery · VWAP20, vertical, 0.5% risk`, `xsp_pcs::XSP put-credit spread · calm, 3.0% risk`, `xsp_pcs::XSP put-credit spread · calm, 1.0% risk`, `xsp_pcs::XSP put-credit spread · graded, 3.0% risk`, `xsp_pcs::XSP put-credit spread · graded, 1.0% risk`, `public_recipe::High-volume trend candle · LINKUSDT`, `public_recipe::Large-body momentum candle · ENJUSDT`
- **Batch 5 (10):** `public_recipe::Filtered RSI2 dip rebound · ADAUSDT`, `absorption_base::Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing`, `absorption_base::Confirmed absorption control · ADAUSDT, 16-hour hold, 1% volume cap`, `absorption_negative_funding::Absorption with negative funding · ADAUSDT, 16-hour hold, available-cash sizing`, `absorption_negative_funding::Absorption with negative funding · ADAUSDT, 16-hour hold, 1% volume cap`, `absorption_nonnegative_funding::Absorption with nonnegative funding · ADAUSDT, 16-hour hold, available-cash sizing`, `absorption_nonnegative_funding::Absorption with nonnegative funding · ADAUSDT, 16-hour hold, 1% volume cap`, `breakout_base::Price-only breakout control · ADAUSDT, 16-hour hold, available-cash sizing`, `breakout_base::Price-only breakout control · ADAUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 16-hour hold, available-cash sizing`
- **Batch 6 (10):** `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 96-hour hold, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 96-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, failed breakout exit, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, failed breakout exit, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset plus price failure, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset plus price failure, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset exit, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset exit, 1% volume cap`, `absorption_base::Confirmed absorption control · ENJUSDT, 16-hour hold, available-cash sizing`
- **Batch 7 (10):** `absorption_base::Confirmed absorption control · ENJUSDT, 16-hour hold, 1% volume cap`, `absorption_negative_funding::Absorption with negative funding · ENJUSDT, 16-hour hold, available-cash sizing`, `absorption_negative_funding::Absorption with negative funding · ENJUSDT, 16-hour hold, 1% volume cap`, `absorption_nonnegative_funding::Absorption with nonnegative funding · ENJUSDT, 16-hour hold, available-cash sizing`, `absorption_nonnegative_funding::Absorption with nonnegative funding · ENJUSDT, 16-hour hold, 1% volume cap`, `breakout_base::Price-only breakout control · ENJUSDT, 16-hour hold, available-cash sizing`, `breakout_base::Price-only breakout control · ENJUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 16-hour hold, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 96-hour hold, available-cash sizing`
- **Batch 8 (10):** `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 96-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, failed breakout exit, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, failed breakout exit, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset plus price failure, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset plus price failure, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset exit, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset exit, 1% volume cap`, `etf::QQQ core with a momentum tilt · 98% exposure`, `etf::QQQ core with a momentum tilt · 150% exposure`, `etf::ETF leader with unchanged-share holding · 98% exposure`
- **Batch 9 (10):** `etf::ETF leader with unchanged-share holding · 150% exposure`, `etf::ETF leader excluding semiconductors · 98% exposure`, `etf::ETF leader excluding semiconductors · 150% exposure`, `etf::ETF leader confirmed across two sources · 98% exposure`, `etf::ETF leader confirmed across two sources · 150% exposure`, `etf::QQQ core with a two-source momentum tilt · 98% exposure`, `etf::QQQ core with a two-source momentum tilt · 150% exposure`, `etf::Two-source ETF leader with unchanged-share holding · 98% exposure`, `etf::Two-source ETF leader with unchanged-share holding · 150% exposure`, `etf::ETF momentum leader · 98% exposure`
- **Batch 10 (10):** `etf::ETF momentum leader · 150% exposure`, `etf::QLD buy and hold · 100% exposure`, `etf::QLD monthly rebalance · 100% exposure`, `etf::QQQ buy and hold · 100% exposure`, `etf::QQQ monthly rebalance · 98% exposure`, `etf::QQQ monthly rebalance · 150% exposure`, `etf::QQQ and QLD equal-weight buy and hold · 100% exposure`, `etf::QQQ and QLD equal-weight monthly rebalance · 100% exposure`, `etf::Semiconductor ETF buy and hold · 98% exposure`, `etf::Semiconductor ETF buy and hold · 150% exposure`
- **Batch 11 (10):** `etf::S&P 500 ETF buy and hold · 100% exposure`, `etf::S&P 500 ETF monthly rebalance · 98% exposure`, `etf::S&P 500 ETF monthly rebalance · 150% exposure`, `absorption_base::Confirmed absorption control · LINKUSDT, 16-hour hold, available-cash sizing`, `absorption_base::Confirmed absorption control · LINKUSDT, 16-hour hold, 1% volume cap`, `absorption_negative_funding::Absorption with negative funding · LINKUSDT, 16-hour hold, available-cash sizing`, `absorption_negative_funding::Absorption with negative funding · LINKUSDT, 16-hour hold, 1% volume cap`, `absorption_nonnegative_funding::Absorption with nonnegative funding · LINKUSDT, 16-hour hold, available-cash sizing`, `absorption_nonnegative_funding::Absorption with nonnegative funding · LINKUSDT, 16-hour hold, 1% volume cap`, `breakout_base::Price-only breakout control · LINKUSDT, 16-hour hold, available-cash sizing`
- **Batch 12 (10):** `breakout_base::Price-only breakout control · LINKUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 16-hour hold, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 16-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 96-hour hold, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 96-hour hold, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, failed breakout exit, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, failed breakout exit, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset plus price failure, available-cash sizing`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset plus price failure, 1% volume cap`, `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset exit, available-cash sizing`
- **Batch 13 (10):** `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset exit, 1% volume cap`, `BETA::Tensor relative-market cohort · cash funded, all volatility, 25 positions`, `C1::Tensor cyan expansion · cash funded, all volatility, 25 positions`, `C1::Tensor cyan expansion · one-session delay, all volatility, 25 positions`, `C1::Tensor cyan expansion · QQQ reserve, all volatility, 25 positions`, `C1::Tensor cyan expansion · cash funded, quieter recent volatility, 25 positions`, `C1::Tensor cyan expansion · one-session delay, quieter recent volatility, 25 positions`, `C1::Tensor cyan expansion · QQQ reserve, quieter recent volatility, 25 positions`, `C1::Tensor cyan expansion · cash funded, higher recent volatility, 25 positions`, `C1::Tensor cyan expansion · one-session delay, higher recent volatility, 25 positions`
- **Batch 14 (10):** `C1::Tensor cyan expansion · QQQ reserve, higher recent volatility, 25 positions`, `G4::Tensor green value / recovery · cash funded, all volatility, 10 positions`, `G4::Tensor green value / recovery · cash funded, all volatility, 25 positions`, `G4::Tensor green value / recovery · one-session delay, all volatility, 25 positions`, `G4::Tensor green value / recovery · QQQ reserve, all volatility, 10 positions`, `G4::Tensor green value / recovery · QQQ reserve, all volatility, 25 positions`, `G4::Tensor green value / recovery · cash funded, quieter recent volatility, 25 positions`, `G4::Tensor green value / recovery · one-session delay, quieter recent volatility, 25 positions`, `G4::Tensor green value / recovery · QQQ reserve, quieter recent volatility, 25 positions`, `G4::Tensor green value / recovery · cash funded, higher recent volatility, 25 positions`
- **Batch 15 (10):** `G4::Tensor green value / recovery · one-session delay, higher recent volatility, 25 positions`, `G4::Tensor green value / recovery · QQQ reserve, higher recent volatility, 25 positions`, `G4::Tensor green value / recovery · dip-or-five-session wait, all volatility, 25 positions`, `cloud::Intraday EMA cloud reclaim`, `cloud::Intraday EMA cloud reclaim`, `hourly::Confirmed hourly swing · native stop, no extra bar delay`, `hourly::Confirmed hourly swing · native stop, one-bar delay`, `hourly::Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay`, `hourly::Confirmed hourly swing · minimum 1-ATR stop distance, one-bar delay`, `overnight::Strong-afternoon continuation`
- **Batch 16 (5):** `overnight::Strong-afternoon continuation`, `public_recipe::55-bar trend breakout · 1d`, `tensor::Daily price, volume and trend model · daily`, `tensor::Daily price and volume model · daily`, `saty_research::Saty Research v0.3 - SPY equity paper`

## 6. Per-row build map
Archive paths below are relative to the handoff root
(`source/...` = `source/` tree). `SM id` = source-map row id.

### public_recipe — source: daily rows (SM `TRADER_*`): `source/backend/trading.py`, `source/strategies/trader_catalogue/rules-v1.json`; spot rows (SM `PUBLIC_*_SPOT100`): `source/strategies/public_recipes/public_source_sleeves.py`, `source/backend/public_recipe_runtime.py`, and per-row Pine — LINK: `source/strategies/public_recipes/sources/AI_Volume_Strategy.pine`, ENJ: `source/strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine`, ADA: `source/strategies/public_recipes/sources/TOMAZETTI_RSI2.pine`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 1 | Paper book 1 | `public_recipe::RSI2 dip rebound · 1d` | TRADER_RSI2 | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |
| 2 | Paper book 2 | `public_recipe::Volatility-squeeze breakout · 1d` | TRADER_SQUEEZE20 | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |

### tensor — source: `source/backend/tensor_engine.py`, `source/backend/trading.py`, `source/strategies/tensor_state_repair/engine/{state_features,native_features}.mjs` (hourly/weekly); `source/backend/tensor_daily_models.py` + `source/strategies/tensor_daily20/models/*` (daily models)

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 3 | Paper book 3 | `tensor::Hourly multi-indicator recovery · hourly` | H1STATE | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |
| 4 | Paper book 4 | `tensor::Weekly multi-indicator recovery · weekly` | WSTATE | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |

### confirmed_absorption — source: `source/backend/absorption_runtime.py`, `source/strategies/absorption/signals.py`, `source/strategies/absorption/rules-v1.json`, `source/backend/public_recipe_runtime.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 5 | Paper book 5 | `confirmed_absorption::Four-hour confirmed absorption · ENJUSDT` | ABSORPTION_ENJUSDT_4H | full available slice cash incl. 10bp fee (source sizing) |
| 6 | Paper book 6 | `confirmed_absorption::Four-hour confirmed absorption · LINKUSDT` | ABSORPTION_LINKUSDT_4H | full available slice cash incl. 10bp fee (source sizing) |

### native_trend — source: `source/backend/prospective_native.py`, `source/backend/prospective_native_math.py`, `source/backend/prospective_projection.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 7 | Paper book 7 | `native_trend::Daily SMA200 spot allocation` | BTC_ETH_SMA200 | target weights applied to slice: Bitcoin 50%, Ether 50% of $10,000 |
| 8 | Paper book 8 | `native_trend::Daily SMA200 spot allocation` | ETH_SMA200 | target weights applied to slice: Ether 100% of $10,000 |

### opening_gamma — source: `source/backend/r19_options.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 14 | Paper book 14 | `opening_gamma::Opening-range options · long, 2.0% risk` | OPT_OPENING_GAMMA_A | risk_fraction 0.02×slice = $200 risk/entry |
| 15 | Paper book 15 | `opening_gamma::Opening-range options · long, 0.5% risk` | OPT_OPENING_GAMMA_B | risk_fraction 0.005×slice = $50 risk/entry |

### pead — source: `source/backend/r19_options.py` (`build_pead_event`/`pead_signal`), `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 16 | Paper book 16 | `pead::Post-earnings response · long, 2.0% risk` | OPT_PEAD_LONG_A | risk_fraction 0.02×slice = $200 risk/entry |
| 17 | Paper book 17 | `pead::Post-earnings response · long, 0.5% risk` | OPT_PEAD_LONG_B | risk_fraction 0.005×slice = $50 risk/entry |
| 18 | Paper book 18 | `pead::Post-earnings response · vertical, 2.0% risk` | OPT_PEAD_VERTICAL_A | risk_fraction 0.02×slice = $200 risk/entry |
| 19 | Paper book 19 | `pead::Post-earnings response · vertical, 0.5% risk` | OPT_PEAD_VERTICAL_B | risk_fraction 0.005×slice = $50 risk/entry |

### core_reserve — source: `source/backend/r19_options.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json` (book `OPT_QQQ95_*`)

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 20 | Paper book 20 | `core_reserve::Core exposure plus option reserve · RSI2, long, 0.5% risk` | OPT_QQQ95_RSI2_LONG | risk_fraction 0.005×slice = $50 risk/entry; core 0.95×slice = $9,500; premium reserve 0.05×slice = $500 (not interchangeable) |
| 21 | Paper book 21 | `core_reserve::Core exposure plus option reserve · RSI2, vertical, 0.5% risk` | OPT_QQQ95_RSI2_VERTICAL | risk_fraction 0.005×slice = $50 risk/entry; core 0.95×slice = $9,500; premium reserve 0.05×slice = $500 (not interchangeable) |

### recovery — source: `source/backend/r19_options.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 22 | Paper book 22 | `recovery::Options recovery · RSI2, long, 2.0% risk` | OPT_RSI2_LONG_FIXED_A | risk_fraction 0.02×slice = $200 risk/entry |
| 23 | Paper book 23 | `recovery::Options recovery · RSI2, long, 0.5% risk` | OPT_RSI2_LONG_FIXED_B | risk_fraction 0.005×slice = $50 risk/entry |
| 24 | Paper book 24 | `recovery::Options recovery · RSI2, long, 2.0% risk` | OPT_RSI2_LONG_TOUCH_A | risk_fraction 0.02×slice = $200 risk/entry |
| 25 | Paper book 25 | `recovery::Options recovery · RSI2, long, 0.5% risk` | OPT_RSI2_LONG_TOUCH_B | risk_fraction 0.005×slice = $50 risk/entry |
| 26 | Paper book 26 | `recovery::Options recovery · RSI2, vertical, 2.0% risk` | OPT_RSI2_VERTICAL_FIXED_A | risk_fraction 0.02×slice = $200 risk/entry |
| 27 | Paper book 27 | `recovery::Options recovery · RSI2, vertical, 0.5% risk` | OPT_RSI2_VERTICAL_FIXED_B | risk_fraction 0.005×slice = $50 risk/entry |
| 28 | Paper book 28 | `recovery::Options recovery · RSI2, vertical, 2.0% risk` | OPT_RSI2_VERTICAL_TOUCH_A | risk_fraction 0.02×slice = $200 risk/entry |
| 29 | Paper book 29 | `recovery::Options recovery · RSI2, vertical, 0.5% risk` | OPT_RSI2_VERTICAL_TOUCH_B | risk_fraction 0.005×slice = $50 risk/entry |

### tensor_leaps — source: `source/backend/r19_options.py`, `source/backend/r19_tensor.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 30 | Paper book 30 | `tensor_leaps::Tensor long-dated calls · long, 2.0% risk` | OPT_TENSOR_LEAPS_A | risk_fraction 0.02×slice = $200 risk/entry |
| 31 | Paper book 31 | `tensor_leaps::Tensor long-dated calls · long, 0.5% risk` | OPT_TENSOR_LEAPS_B | risk_fraction 0.005×slice = $50 risk/entry |

### recovery — source: `source/backend/r19_options.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 32 | Paper book 32 | `recovery::Options recovery · VWAP20, long, 2.0% risk` | OPT_VWAP20_LONG_FIXED_A | risk_fraction 0.02×slice = $200 risk/entry |
| 33 | Paper book 33 | `recovery::Options recovery · VWAP20, long, 0.5% risk` | OPT_VWAP20_LONG_FIXED_B | risk_fraction 0.005×slice = $50 risk/entry |
| 34 | Paper book 34 | `recovery::Options recovery · VWAP20, long, 2.0% risk` | OPT_VWAP20_LONG_TOUCH_A | risk_fraction 0.02×slice = $200 risk/entry |
| 35 | Paper book 35 | `recovery::Options recovery · VWAP20, long, 0.5% risk` | OPT_VWAP20_LONG_TOUCH_B | risk_fraction 0.005×slice = $50 risk/entry |
| 36 | Paper book 36 | `recovery::Options recovery · VWAP20, vertical, 2.0% risk` | OPT_VWAP20_VERTICAL_FIXED_A | risk_fraction 0.02×slice = $200 risk/entry |
| 37 | Paper book 37 | `recovery::Options recovery · VWAP20, vertical, 0.5% risk` | OPT_VWAP20_VERTICAL_FIXED_B | risk_fraction 0.005×slice = $50 risk/entry |
| 38 | Paper book 38 | `recovery::Options recovery · VWAP20, vertical, 2.0% risk` | OPT_VWAP20_VERTICAL_TOUCH_A | risk_fraction 0.02×slice = $200 risk/entry |
| 39 | Paper book 39 | `recovery::Options recovery · VWAP20, vertical, 0.5% risk` | OPT_VWAP20_VERTICAL_TOUCH_B | risk_fraction 0.005×slice = $50 risk/entry |

### xsp_pcs — source: `source/backend/r19_options.py`, `source/backend/r19_option_data.py`, `source/strategies/r19/options_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 40 | Paper book 40 | `xsp_pcs::XSP put-credit spread · calm, 3.0% risk` | OPT_XSP_CALM_A | risk_fraction 0.03×slice = $300 risk/entry |
| 41 | Paper book 41 | `xsp_pcs::XSP put-credit spread · calm, 1.0% risk` | OPT_XSP_CALM_B | risk_fraction 0.01×slice = $100 risk/entry |
| 42 | Paper book 42 | `xsp_pcs::XSP put-credit spread · graded, 3.0% risk` | OPT_XSP_GRADED_A | risk_fraction 0.03×slice = $300 risk/entry |
| 43 | Paper book 43 | `xsp_pcs::XSP put-credit spread · graded, 1.0% risk` | OPT_XSP_GRADED_B | risk_fraction 0.01×slice = $100 risk/entry |

### public_recipe — source: daily rows (SM `TRADER_*`): `source/backend/trading.py`, `source/strategies/trader_catalogue/rules-v1.json`; spot rows (SM `PUBLIC_*_SPOT100`): `source/strategies/public_recipes/public_source_sleeves.py`, `source/backend/public_recipe_runtime.py`, and per-row Pine — LINK: `source/strategies/public_recipes/sources/AI_Volume_Strategy.pine`, ENJ: `source/strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine`, ADA: `source/strategies/public_recipes/sources/TOMAZETTI_RSI2.pine`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 44 | Paper book 44 | `public_recipe::High-volume trend candle · LINKUSDT` | PUBLIC_AI_VOLUME_SPOT100 | SPOT100: full-slice spot allocation per `public_source_sleeves.py` |
| 45 | Paper book 45 | `public_recipe::Large-body momentum candle · ENJUSDT` | PUBLIC_IU_BODY_SPOT100 | SPOT100: full-slice spot allocation per `public_source_sleeves.py` |
| 46 | Paper book 46 | `public_recipe::Filtered RSI2 dip rebound · ADAUSDT` | PUBLIC_TOMAZETTI_RSI2_SPOT100 | SPOT100: full-slice spot allocation per `public_source_sleeves.py` |

### absorption_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 47 | Paper book 47 | `absorption_base::Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing` | R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 48 | Paper book 48 | `absorption_base::Confirmed absorption control · ADAUSDT, 16-hour hold, 1% volume cap` | R19_ADAUSDT_ABSORPTION_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_negative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 49 | Paper book 49 | `absorption_negative_funding::Absorption with negative funding · ADAUSDT, 16-hour hold, available-cash sizing` | R19_ADAUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 50 | Paper book 50 | `absorption_negative_funding::Absorption with negative funding · ADAUSDT, 16-hour hold, 1% volume cap` | R19_ADAUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_nonnegative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 51 | Paper book 51 | `absorption_nonnegative_funding::Absorption with nonnegative funding · ADAUSDT, 16-hour hold, available-cash sizing` | R19_ADAUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 52 | Paper book 52 | `absorption_nonnegative_funding::Absorption with nonnegative funding · ADAUSDT, 16-hour hold, 1% volume cap` | R19_ADAUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### breakout_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 53 | Paper book 53 | `breakout_base::Price-only breakout control · ADAUSDT, 16-hour hold, available-cash sizing` | R19_ADAUSDT_BREAKOUT_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 54 | Paper book 54 | `breakout_base::Price-only breakout control · ADAUSDT, 16-hour hold, 1% volume cap` | R19_ADAUSDT_BREAKOUT_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### negative_funding_squeeze — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 55 | Paper book 55 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 16-hour hold, available-cash sizing` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 56 | Paper book 56 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 16-hour hold, 1% volume cap` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 57 | Paper book 57 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 96-hour hold, available-cash sizing` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_FULLCASH | fullcash = full $10,000 slice cash |
| 58 | Paper book 58 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, 96-hour hold, 1% volume cap` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 59 | Paper book 59 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, failed breakout exit, available-cash sizing` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_FULLCASH | fullcash = full $10,000 slice cash |
| 60 | Paper book 60 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, failed breakout exit, 1% volume cap` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 61 | Paper book 61 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset plus price failure, available-cash sizing` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_FULLCASH | fullcash = full $10,000 slice cash |
| 62 | Paper book 62 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset plus price failure, 1% volume cap` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 63 | Paper book 63 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset exit, available-cash sizing` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FULLCASH | fullcash = full $10,000 slice cash |
| 64 | Paper book 64 | `negative_funding_squeeze::Negative-funding breakout · ADAUSDT, funding reset exit, 1% volume cap` | R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 65 | Paper book 65 | `absorption_base::Confirmed absorption control · ENJUSDT, 16-hour hold, available-cash sizing` | R19_ENJUSDT_ABSORPTION_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 66 | Paper book 66 | `absorption_base::Confirmed absorption control · ENJUSDT, 16-hour hold, 1% volume cap` | R19_ENJUSDT_ABSORPTION_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_negative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 67 | Paper book 67 | `absorption_negative_funding::Absorption with negative funding · ENJUSDT, 16-hour hold, available-cash sizing` | R19_ENJUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 68 | Paper book 68 | `absorption_negative_funding::Absorption with negative funding · ENJUSDT, 16-hour hold, 1% volume cap` | R19_ENJUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_nonnegative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 69 | Paper book 69 | `absorption_nonnegative_funding::Absorption with nonnegative funding · ENJUSDT, 16-hour hold, available-cash sizing` | R19_ENJUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 70 | Paper book 70 | `absorption_nonnegative_funding::Absorption with nonnegative funding · ENJUSDT, 16-hour hold, 1% volume cap` | R19_ENJUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### breakout_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 71 | Paper book 71 | `breakout_base::Price-only breakout control · ENJUSDT, 16-hour hold, available-cash sizing` | R19_ENJUSDT_BREAKOUT_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 72 | Paper book 72 | `breakout_base::Price-only breakout control · ENJUSDT, 16-hour hold, 1% volume cap` | R19_ENJUSDT_BREAKOUT_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### negative_funding_squeeze — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 73 | Paper book 73 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 16-hour hold, available-cash sizing` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 74 | Paper book 74 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 16-hour hold, 1% volume cap` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 75 | Paper book 75 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 96-hour hold, available-cash sizing` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_FULLCASH | fullcash = full $10,000 slice cash |
| 76 | Paper book 76 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, 96-hour hold, 1% volume cap` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 77 | Paper book 77 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, failed breakout exit, available-cash sizing` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_FULLCASH | fullcash = full $10,000 slice cash |
| 78 | Paper book 78 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, failed breakout exit, 1% volume cap` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 79 | Paper book 79 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset plus price failure, available-cash sizing` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_FULLCASH | fullcash = full $10,000 slice cash |
| 80 | Paper book 80 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset plus price failure, 1% volume cap` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 81 | Paper book 81 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset exit, available-cash sizing` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FULLCASH | fullcash = full $10,000 slice cash |
| 82 | Paper book 82 | `negative_funding_squeeze::Negative-funding breakout · ENJUSDT, funding reset exit, 1% volume cap` | R19_ENJUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### etf — source: `source/backend/r19_etf.py`, `source/backend/r19_etf_data.py`, `source/backend/r19_data.py`, `source/strategies/r19/etf_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 83 | Paper book 83 | `etf::QQQ core with a momentum tilt · 98% exposure` | R19_ETF_CORE25_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 84 | Paper book 84 | `etf::QQQ core with a momentum tilt · 150% exposure` | R19_ETF_CORE25_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 85 | Paper book 85 | `etf::ETF leader with unchanged-share holding · 98% exposure` | R19_ETF_DRIFT1_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 86 | Paper book 86 | `etf::ETF leader with unchanged-share holding · 150% exposure` | R19_ETF_DRIFT1_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 87 | Paper book 87 | `etf::ETF leader excluding semiconductors · 98% exposure` | R19_ETF_EXSMH1_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 88 | Paper book 88 | `etf::ETF leader excluding semiconductors · 150% exposure` | R19_ETF_EXSMH1_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 89 | Paper book 89 | `etf::ETF leader confirmed across two sources · 98% exposure` | R19_ETF_INTERVAL1_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 90 | Paper book 90 | `etf::ETF leader confirmed across two sources · 150% exposure` | R19_ETF_INTERVAL1_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 91 | Paper book 91 | `etf::QQQ core with a two-source momentum tilt · 98% exposure` | R19_ETF_INTERVAL_CORE25_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 92 | Paper book 92 | `etf::QQQ core with a two-source momentum tilt · 150% exposure` | R19_ETF_INTERVAL_CORE25_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 93 | Paper book 93 | `etf::Two-source ETF leader with unchanged-share holding · 98% exposure` | R19_ETF_INTERVAL_DRIFT1_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 94 | Paper book 94 | `etf::Two-source ETF leader with unchanged-share holding · 150% exposure` | R19_ETF_INTERVAL_DRIFT1_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 95 | Paper book 95 | `etf::ETF momentum leader · 98% exposure` | R19_ETF_LEADER1_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 96 | Paper book 96 | `etf::ETF momentum leader · 150% exposure` | R19_ETF_LEADER1_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 97 | Paper book 97 | `etf::QLD buy and hold · 100% exposure` | R19_ETF_QLD_ONLY_BUY_HOLD_C100 | gross_target 1×slice = $10,000 target exposure |
| 98 | Paper book 98 | `etf::QLD monthly rebalance · 100% exposure` | R19_ETF_QLD_ONLY_MONTHLY_C100 | gross_target 1×slice = $10,000 target exposure |
| 99 | Paper book 99 | `etf::QQQ buy and hold · 100% exposure` | R19_ETF_QQQ_HOLD_FULL_C100 | gross_target 1×slice = $10,000 target exposure |
| 100 | Paper book 100 | `etf::QQQ monthly rebalance · 98% exposure` | R19_ETF_QQQ_MONTHLY_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 101 | Paper book 101 | `etf::QQQ monthly rebalance · 150% exposure` | R19_ETF_QQQ_MONTHLY_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 102 | Paper book 102 | `etf::QQQ and QLD equal-weight buy and hold · 100% exposure` | R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100 | gross_target 1×slice = $10,000 target exposure |
| 103 | Paper book 103 | `etf::QQQ and QLD equal-weight monthly rebalance · 100% exposure` | R19_ETF_QQQ_QLD_50_50_MONTHLY_C100 | gross_target 1×slice = $10,000 target exposure |
| 104 | Paper book 104 | `etf::Semiconductor ETF buy and hold · 98% exposure` | R19_ETF_SMH_HOLD_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 105 | Paper book 105 | `etf::Semiconductor ETF buy and hold · 150% exposure` | R19_ETF_SMH_HOLD_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |
| 106 | Paper book 106 | `etf::S&P 500 ETF buy and hold · 100% exposure` | R19_ETF_SPY_HOLD_FULL_C100 | gross_target 1×slice = $10,000 target exposure |
| 107 | Paper book 107 | `etf::S&P 500 ETF monthly rebalance · 98% exposure` | R19_ETF_SPY_MONTHLY_C098 | gross_target 0.98×slice = $9,800 target exposure |
| 108 | Paper book 108 | `etf::S&P 500 ETF monthly rebalance · 150% exposure` | R19_ETF_SPY_MONTHLY_M150 | gross_target 1.5×slice = $15,000 target exposure (LEVERAGED in source book: >slice notional — dispatcher BP check governs, never silently capped in the sleeve) |

### absorption_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 109 | Paper book 109 | `absorption_base::Confirmed absorption control · LINKUSDT, 16-hour hold, available-cash sizing` | R19_LINKUSDT_ABSORPTION_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 110 | Paper book 110 | `absorption_base::Confirmed absorption control · LINKUSDT, 16-hour hold, 1% volume cap` | R19_LINKUSDT_ABSORPTION_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_negative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 111 | Paper book 111 | `absorption_negative_funding::Absorption with negative funding · LINKUSDT, 16-hour hold, available-cash sizing` | R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 112 | Paper book 112 | `absorption_negative_funding::Absorption with negative funding · LINKUSDT, 16-hour hold, 1% volume cap` | R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### absorption_nonnegative_funding — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`, `source/strategies/absorption/signals.py`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 113 | Paper book 113 | `absorption_nonnegative_funding::Absorption with nonnegative funding · LINKUSDT, 16-hour hold, available-cash sizing` | R19_LINKUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 114 | Paper book 114 | `absorption_nonnegative_funding::Absorption with nonnegative funding · LINKUSDT, 16-hour hold, 1% volume cap` | R19_LINKUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### breakout_base — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 115 | Paper book 115 | `breakout_base::Price-only breakout control · LINKUSDT, 16-hour hold, available-cash sizing` | R19_LINKUSDT_BREAKOUT_BASE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 116 | Paper book 116 | `breakout_base::Price-only breakout control · LINKUSDT, 16-hour hold, 1% volume cap` | R19_LINKUSDT_BREAKOUT_BASE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### negative_funding_squeeze — source: `source/backend/r19_crypto.py`, `source/backend/r19_crypto_data.py`, `source/strategies/r19/crypto_rules.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 117 | Paper book 117 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 16-hour hold, available-cash sizing` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_FULLCASH | fullcash = full $10,000 slice cash |
| 118 | Paper book 118 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 16-hour hold, 1% volume cap` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 119 | Paper book 119 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 96-hour hold, available-cash sizing` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_FULLCASH | fullcash = full $10,000 slice cash |
| 120 | Paper book 120 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, 96-hour hold, 1% volume cap` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED96_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 121 | Paper book 121 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, failed breakout exit, available-cash sizing` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_FULLCASH | fullcash = full $10,000 slice cash |
| 122 | Paper book 122 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, failed breakout exit, 1% volume cap` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_LOST_BREAKOUT_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 123 | Paper book 123 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset plus price failure, available-cash sizing` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_FULLCASH | fullcash = full $10,000 slice cash |
| 124 | Paper book 124 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset plus price failure, 1% volume cap` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FAILURE_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |
| 125 | Paper book 125 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset exit, available-cash sizing` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FULLCASH | fullcash = full $10,000 slice cash |
| 126 | Paper book 126 | `negative_funding_squeeze::Negative-funding breakout · LINKUSDT, funding reset exit, 1% volume cap` | R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_VOLUME1PCT | volume1pct = 1% of native volume (market-relative, unchanged) |

### BETA — source: `source/backend/r19_tensor.py`, `source/backend/r19_data.py`, `source/backend/r19_intraday_data.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 127 | Paper book 127 | `BETA::Tensor relative-market cohort · cash funded, all volatility, 25 positions` | R19_TENSOR_BETA_M2_52W_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |

### C1 — source: `source/backend/r19_tensor.py`, `source/backend/r19_data.py`, `source/backend/r19_intraday_data.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 128 | Paper book 128 | `C1::Tensor cyan expansion · cash funded, all volatility, 25 positions` | R19_TENSOR_C1_ALL_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 129 | Paper book 129 | `C1::Tensor cyan expansion · one-session delay, all volatility, 25 positions` | R19_TENSOR_C1_ALL_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 130 | Paper book 130 | `C1::Tensor cyan expansion · QQQ reserve, all volatility, 25 positions` | R19_TENSOR_C1_ALL_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 131 | Paper book 131 | `C1::Tensor cyan expansion · cash funded, quieter recent volatility, 25 positions` | R19_TENSOR_C1_COOL_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 132 | Paper book 132 | `C1::Tensor cyan expansion · one-session delay, quieter recent volatility, 25 positions` | R19_TENSOR_C1_COOL_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 133 | Paper book 133 | `C1::Tensor cyan expansion · QQQ reserve, quieter recent volatility, 25 positions` | R19_TENSOR_C1_COOL_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 134 | Paper book 134 | `C1::Tensor cyan expansion · cash funded, higher recent volatility, 25 positions` | R19_TENSOR_C1_HOT_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 135 | Paper book 135 | `C1::Tensor cyan expansion · one-session delay, higher recent volatility, 25 positions` | R19_TENSOR_C1_HOT_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 136 | Paper book 136 | `C1::Tensor cyan expansion · QQQ reserve, higher recent volatility, 25 positions` | R19_TENSOR_C1_HOT_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |

### G4 — source: `source/backend/r19_tensor.py`, `source/backend/r19_data.py`, `source/backend/r19_intraday_data.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 137 | Paper book 137 | `G4::Tensor green value / recovery · cash funded, all volatility, 10 positions` | R19_TENSOR_G4_ALL_CASH_10 | ticket $10,000 on $100k book = 10%×slice = $1,000/position |
| 138 | Paper book 138 | `G4::Tensor green value / recovery · cash funded, all volatility, 25 positions` | R19_TENSOR_G4_ALL_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 139 | Paper book 139 | `G4::Tensor green value / recovery · one-session delay, all volatility, 25 positions` | R19_TENSOR_G4_ALL_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 140 | Paper book 140 | `G4::Tensor green value / recovery · QQQ reserve, all volatility, 10 positions` | R19_TENSOR_G4_ALL_RESERVE_10 | ticket $10,000 on $100k book = 10%×slice = $1,000/position |
| 141 | Paper book 141 | `G4::Tensor green value / recovery · QQQ reserve, all volatility, 25 positions` | R19_TENSOR_G4_ALL_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 142 | Paper book 142 | `G4::Tensor green value / recovery · cash funded, quieter recent volatility, 25 positions` | R19_TENSOR_G4_COOL_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 143 | Paper book 143 | `G4::Tensor green value / recovery · one-session delay, quieter recent volatility, 25 positions` | R19_TENSOR_G4_COOL_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 144 | Paper book 144 | `G4::Tensor green value / recovery · QQQ reserve, quieter recent volatility, 25 positions` | R19_TENSOR_G4_COOL_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 145 | Paper book 145 | `G4::Tensor green value / recovery · cash funded, higher recent volatility, 25 positions` | R19_TENSOR_G4_HOT_CASH_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 146 | Paper book 146 | `G4::Tensor green value / recovery · one-session delay, higher recent volatility, 25 positions` | R19_TENSOR_G4_HOT_DELAY_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 147 | Paper book 147 | `G4::Tensor green value / recovery · QQQ reserve, higher recent volatility, 25 positions` | R19_TENSOR_G4_HOT_RESERVE_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |
| 148 | Paper book 148 | `G4::Tensor green value / recovery · dip-or-five-session wait, all volatility, 25 positions` | R19_TENSOR_G4_RED_TIMEOUT_25 | ticket $4,000 on $100k book = 4%×slice = $400/position |

### cloud — source: `source/backend/r19_timing.py`, `source/backend/r19_intraday_data.py`, `source/backend/r19_tensor.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 149 | Paper book 149 | `cloud::Intraday EMA cloud reclaim` | R19_TIMING_CLOUD_AGGRESSIVE | notional cap 0.2×slice = $2,000/position; risk 0.005×slice = $50/entry |
| 150 | Paper book 150 | `cloud::Intraday EMA cloud reclaim` | R19_TIMING_CLOUD_BASE | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |

### hourly — source: `source/backend/r19_timing.py`, `source/backend/r19_intraday_data.py`, `source/backend/r19_tensor.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 151 | Paper book 151 | `hourly::Confirmed hourly swing · native stop, no extra bar delay` | R19_TIMING_HOUR_FLOOR0_DELAY0 | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |
| 152 | Paper book 152 | `hourly::Confirmed hourly swing · native stop, one-bar delay` | R19_TIMING_HOUR_FLOOR0_DELAY1 | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |
| 153 | Paper book 153 | `hourly::Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay` | R19_TIMING_HOUR_FLOOR1_DELAY0 | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |
| 154 | Paper book 154 | `hourly::Confirmed hourly swing · minimum 1-ATR stop distance, one-bar delay` | R19_TIMING_HOUR_FLOOR1_DELAY1 | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |

### overnight — source: `source/backend/r19_timing.py`, `source/backend/r19_intraday_data.py`, `source/backend/r19_tensor.py`, `source/strategies/r19/tensor/RULES.json`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 155 | Paper book 155 | `overnight::Strong-afternoon continuation` | R19_TIMING_OVERNIGHT_25BP | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |
| 156 | Paper book 156 | `overnight::Strong-afternoon continuation` | R19_TIMING_OVERNIGHT_5BP | notional cap 0.1×slice = $1,000/position; risk 0.0025×slice = $25/entry |

### public_recipe — source: daily rows (SM `TRADER_*`): `source/backend/trading.py`, `source/strategies/trader_catalogue/rules-v1.json`; spot rows (SM `PUBLIC_*_SPOT100`): `source/strategies/public_recipes/public_source_sleeves.py`, `source/backend/public_recipe_runtime.py`, and per-row Pine — LINK: `source/strategies/public_recipes/sources/AI_Volume_Strategy.pine`, ENJ: `source/strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine`, ADA: `source/strategies/public_recipes/sources/TOMAZETTI_RSI2.pine`

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 157 | Paper book 157 | `public_recipe::55-bar trend breakout · 1d` | TRADER_DONCHIAN55 | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |

### tensor — source: `source/backend/tensor_engine.py`, `source/backend/trading.py`, `source/strategies/tensor_state_repair/engine/{state_features,native_features}.mjs` (hourly/weekly); `source/backend/tensor_daily_models.py` + `source/strategies/tensor_daily20/models/*` (daily models)

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 158 | Paper book 158 | `tensor::Daily price, volume and trend model · daily` | D20TENSOR | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |
| 159 | Paper book 159 | `tensor::Daily price and volume model · daily` | D20PV | entry cap 0.1×slice = $1,000/entry; native-DV cap 0.01 unchanged (market-relative); 10 slots |

### saty_research — source: NONE in the handoff (see §4)

| TSV # | Book | Row key | SM id | Slice mapping |
|---|---|---|---|---|
| 160 | Paper book 160 | `saty_research::Saty Research v0.3 - SPY equity paper` | — NONE — | paper capital $100,000 in TSV → slice $10,000; risk/entry 0.25%×slice = $25 (half for mean-reversion); R-multiple limits scale-free, unchanged |

## 7. Excluded from this map (named, not silently dropped)
- 5 TSV duplicates (`midna_*`, rows 9–13): already v2/v3 roster sleeves.
- 15 source-map unfunded monitors/collectors (§2): no TSV row, no order
  authority; not built as Aster sleeves.

## 8. Intake verdict
- Archive: GREEN (204 exact / 0 source mismatches; §1).
- Build map: PARTIAL — all 155 rows mapped or named-missing above;
  sleeve builds are later batches, each with its own fail-first blocker.
- Open by name: saty_research source (v030) absent; funding, earnings,
  opening-event, and XSP regime/chain producers not yet v3 producers
  (affected sleeves UNFED until wired).
