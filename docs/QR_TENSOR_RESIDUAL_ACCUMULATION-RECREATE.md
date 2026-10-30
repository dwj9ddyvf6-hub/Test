# qr-tensor-residual-accumulation: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "TRACE residual accumulation (daily)", type breakout, family quant_research, style "Residual accumulation breakout", universe "The Tensor research roster's liquid operating companies", asset class US equities, timeframe 1d, creator "TRACE, from the desk's ten-strategy repair review (R10) playbook, at the daily scale on the Tensor research roster". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `qr-tensor-residual-accumulation` (`docs/CATALOG.json`): status waiting (1), card `strategies/quant_research/qr-tensor-residual-accumulation.md`, master-desk row `qr_tensor_residual_accumulation`.
- Alias: `qr_tensor_residual_accumulation`.

## What this strategy is

TRACE residual accumulation (daily): buys a liquid stock whose residual volume pressure built inside a 20-session box before two closes broke above it, with 1.5 / 3 ATR barriers and a 20-session limit.

## Full algorithm

From `strategies/quant_research/qr-tensor-residual-accumulation.md` and `sleeves/tensor_research/tensor_research.py` (TRACE section, constants TRACE_BOX=20, TRACE_PATH=20, TRACE_FIT=60, TRACE_MAX_NAMES=15, TRACE_NAME_CAP=0.08, TRACE_RISK=0.0025, TRACE_MIN_NOTIONAL=1000, TRACE_HOLD=20, TRACE_COOLDOWN=20), in evaluation order:

1. Universe: the roster's operating companies with 252 daily and 72 weekly bars, a close at or above $10 and a 60-session median dollar volume at or above $50M.
2. Path: over the last 20 sessions, returns less a ridge fit on SPY and the name's sector ETF over the 60 sessions before; daily pressure = the close's place in its range times volume / the median of the 20 prior volumes (capped at plus or minus 5); q = cumulative pressure / sqrt(20), p = cumulative residual / (sigma times sqrt(20)).
3. Gate: pressure established first (q at or above 1, |p| at or below 0.5, the close inside the range of the 20 sessions before the window), then two closes running above that range's high within the last 3 sessions, and no close under its low since.
4. Order: the next session 09:35-09:45 ET, in symbol order, a limit at the close + 0.5 ATR(14) good until 09:45; no pyramiding; 20 sessions' cooldown after an exit.
5. Exit barriers, every pass: the bid at or below fill - 1.5 ATR, or at or above fill + 3 ATR.
6. Exit at 09:35-09:45 ET: 20 sessions held, or a renewal failure (the last 3 closes not above the prior closing high, a negative phase contrast and negative pressure over those 3 days); sold at the market.
7. Gap in the record in Test: the card and catalog name `desk/vendor/foliotend_research/trace/trace_r10.py` as a code path, and `tensor_research.py` imports it as `desk.vendor.foliotend_research.trace.trace_r10`; that module was not found in the Test tree searched for this package. The in-repo TRACE evaluation and execution code in `tensor_research.py` is present; a faithful recreation needs the trace_r10 module (residual_path and related helpers) from the original desk, or from its recorded source below. Do not invent it.

## Files in this repo

- This doc: `docs/QR_TENSOR_RESIDUAL_ACCUMULATION-RECREATE.md`
- Strategy card: `strategies/quant_research/qr-tensor-residual-accumulation.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py` (TRACE section; its header records the TRACE source as repo quant-research-backup, commit d170596b4d3f24712da933683ceb6d9ee95d6937, path `research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/trace/repair/trace_r10.py`; that path was not present in the quant-research-backup tree searched for this package)
- Rule lines: `docs/verify/quant_research.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. No distinct TRACE sleeve code was found in Silicon or Midna; the quant-research-backup tree search is recorded above.

## Configuration

- Universe: Tensor research roster's liquid operating companies (see algorithm step 1). Timeframe: 1d. Asset class: US equities.
- Book: $100,000. Sizing: shares = min(0.25% of NAV / 1.5 ATR, 8% of NAV / price, 0.5% of the 20-day average volume, the 25% sector room, the gross room, cash), at least $1,000; at most 15 names.
- Cadence in code: 120 s for the TRACE book (per `tensor_research.py`). State: lots, cooldown and planned session, per the code's state schema.

## Data inputs

- Split-adjusted daily bars (600 sessions) of the roster, SPY and the sector ETFs, read from the desk's cache after each close (per the card).

## Install and run

1. Clone the Test repo.
2. Read `strategies/quant_research/qr-tensor-residual-accumulation.md` and `docs/verify/quant_research.md`.
3. Open `sleeves/tensor_research/tensor_research.py` and locate the TRACE section (`trace_evaluate`, `job_trace` and the TRACE book).
4. Supply the missing `desk/vendor/foliotend_research/trace/trace_r10.py` module from the original desk / recorded source above; without it the TRACE evaluation cannot run as designed. Record its absence rather than substituting invented logic.
5. Provide 600 sessions of split-adjusted daily bars for the roster, SPY and sector ETFs.
6. Run daily after the close, with the 09:35-09:45 ET execution window, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- A name with close under $10 or 60-session median dollar volume under $50M is excluded.
- No entry unless q is at or above 1, |p| is at or below 0.5, and two closes above the prior 20-session range high occur within the last 3 sessions with no close under its low since.
- The buy limit is exactly close + 0.5 ATR(14), live only 09:35-09:45 ET, and sizing respects the min() formula, the $1,000 floor and the 15-name cap.
- Exit fires at fill - 1.5 ATR / fill + 3 ATR, at 20 sessions held, or on the recorded renewal failure; a 20-session cooldown follows an exit.
