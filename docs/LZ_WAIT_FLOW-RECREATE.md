# lz-wait-flow — Recreation Package

## Provenance

- Canonical name: FLOW short volume / FTD / dark pool; algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: lz_s_wait_flow, lz_wait_flow.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "FLOW short volume / FTD / dark pool" (also docs/ALL-SLEEVES.md); Test catalog entry 'lz-wait-flow' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; md2 catalog entry/exit/strategy text; alias record sources: md2_catalog, test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

- Sanitized for the public repo: 11 mention(s) of the originating research family name were replaced with a neutral placeholder; no rule, parameter, or code content was changed.

## What this strategy is

FLOW short volume / FTD / dark pool (WAIT lane s_wait_flow): buys small-band daily Green tracker fires priced $5 to under $20 with heavy FINRA short-sale volume, and holds 60 sessions. Family lazarus; type other; universe Tracker universe, small band; asset class US equities; timeframe 1d.

## Full algorithm

Signal producer: sleeves/lazarus/the family research line_wait_feed.py, function flow(L, band_fn, svr5_fn), constants FLOW = dict(min_dv20=100_000.0, band="small", px_lo=5.0, px_hi=20.0, svr5_min=0.447678, stale_days=7, hold_sessions=60, svr_window=5, svr_min_periods=3). Evaluation order:
1. Iterate the tracker ledger fires in sorted key order; keep only lane "1d" with signal "green".
2. close_D = the fire's lc2_tag values (ue_tag, then the fire record when absent); dv20 = the tag dv20. Skip if close_D is missing, dv20 is missing or < 100,000, or close_D is outside [5.0, 20.0).
3. PIT band: band_fn(sym, D, close_D) via the vendored sleeve_band module; skip unless the band is exactly "small" (unknown band fails closed).
4. svr5: for the symbol, svr = ShortVolume / TotalVolume per FINRA Reg SHO CNMS daily file; svr5 = the mean of the symbol's 5 newest rows on or before D (minimum 3 rows, else no fire). Skip if there is no row, if the newest row on or before D is more than 7 days old, or if svr5 < 0.447678. Source: ALTDATA_LIVE out/finra_svr_history.parquet when present and covering D, else FINRA's public CNMS daily files directly (cached); while the altdata producer is off, only cached files are read and the lane records why.
5. Emit a fire: lane s_wait_flow, unit wait-flow-D60, plan = plan(60, "sessions") (no stop / time exit 60 sessions), strategy text "FLOW short-volume cell (test)", limit mechanics per the execution section below.
Execution mechanics (strategies/lazarus card for this lane, master-desk lazarus.live_row mechanics it names):
- Entry: buy from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.
- Exit execution: time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.
- The fire plan itself (the family research line_wait_feed.py plan()) is: scheme 'no stop / time exit <N> <unit>', stop_pct 99.0, first_target_pct None, sell_fraction 1.0, rest 'time', exit_on_engine_sell False.
- Fire window / freshness (the family research line_wait_feed.py): WINDOW_SESSIONS = 5, FEED_MAX_AGE_H = 80; a lane whose input is missing keeps its previous fires whose fire day is inside the 5-session window and whose evidence is at most 80 h old (carry_forward), stamped carried_from, instead of losing them.
Accounting discrepancy (code is the truth): the ALL-SLEEVES accounting entry record for alias lz_s_wait_flow carries a generic fear_day execution config (policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day) and an exit record naming a 15% disaster stop with a 1-week hold unit. The code above implements neither: the wait_feed plan is no-stop with a 60-session time exit, and the strategy card in this repo (strategies/lazarus/lz-wait-flow.md) agrees with the code (no stop, exit at the close of D + 60). The accounting values are recorded here as the accounting record, not as the algorithm.
Accounting gap: sizing not recorded in any consulted source in the accounting; the strategy card in this repo records $1,000 a position, K = 10 (see Configuration).

## Files in this repo

- This package: `docs/LZ_WAIT_FLOW-RECREATE.md`
- Signal producer: `sleeves/lazarus/the family research line_wait_feed.py` (flow(), svr5_table(), parse_cnms(), FLOW constants, plan(), fire())
- Producer job: `sleeves/lazarus/the family research line_wait.py` (runs the feed composition; FINRA producer handling)
- Strategy card: `strategies/lazarus/lz-wait-flow.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md` (strategy entry "FLOW short volume / FTD / dark pool"); catalog entry `lz-wait-flow` in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/lazarus/the family research line_wait_feed.py, sleeves/lazarus/the family research line_wait.py, desk3/lazarus.py and strategies/lazarus/lz-wait-*.md in this repo, so no further repo was needed for code; trees of dwj9ddyvf6-hub/Silicon (21,337 entries), dwj9ddyvf6-hub/quant-research-backup (47,379 entries) and dwj9ddyvf6-hub/Midna (7,855 entries) were also listed and carry no lazarus WAIT-lane module). Code was already in Test, so nothing was vendored.

## Configuration

- Lane id s_wait_flow (aliases lz_s_wait_flow, lz_wait_flow); status in the Test catalog entry: blocked; strategy card status: blocked.
- FLOW constants as in the Full algorithm: min_dv20 100000, band small, price [5.0, 20.0), svr5_min 0.447678, stale_days 7, hold_sessions 60, svr_window 5, svr_min_periods 3.
- Sizing (strategy card): $1,000 a position; K = 10; fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data inputs

- Tracker ledger (1D Green fires with lc2/ue tags carrying close_D and dv20).
- PIT SEC band (vendored sleeve_band module).
- FINRA Reg SHO daily short-volume files (CNMS), via finra_svr_history.parquet when present, else the public CNMS files (cached).
- Output: shadow/paper_sleeve/live/wait_fires_v1.json (key fires_wait) consumed by the Lazarus live engine.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/lazarus/the family research line_wait_feed.py` and `sleeves/lazarus/the family research line_wait.py` at those paths with the vendored research modules the feed imports (shadow/paper_sleeve/sleeve_band.py, shadow/addons_sc.py, shadow/addons_sources_st.py) available on the research root.
3. Run the producer as a script: python the family research line_wait_feed.py --research <root>/inputs/lazarus --scratch <root>/cache/the family research line/scratch [--cache dir] [--now epoch]; it writes shadow/paper_sleeve/live/wait_fires_v1.json.
4. Run the desk cycle so the Lazarus live engine consumes the fires_wait file and applies the entry/exit execution mechanics above.
5. First evaluation: use a fixture ledger with one 1D Green small-band fire at $10.00, dv20 >= $100k and svr5 >= 0.447678 from files at most 7 days old, and confirm exactly one s_wait_flow fire with a 60-session no-stop plan is written.

## Verification

- Fixture above: exactly one fire, plan max_bars 60 sessions, stop_pct 99.0, rest time.
- Fixture with svr5 = 0.40, or the newest FINRA row 8 days before D, or fewer than 3 svr rows, or band not small, or close $20.00 or $4.99, or dv20 $99,999: no fire.
- Fixture with the FINRA input missing entirely: the lane keeps prior fires inside the 5-session / 80 h carry-forward window and reports input missing, rather than erasing them.
- A held position reaches D + 60 sessions: one full time exit per the execution mechanics; no price stop fires before it (plan stop_pct 99.0).
