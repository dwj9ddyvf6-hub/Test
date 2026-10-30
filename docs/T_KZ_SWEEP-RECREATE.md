# t_kz_sweep: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "ICT killzone sweep & reclaim (JadeCap via the OtherSideBJ posts)", type mean reversion, family intraday_reversal_liquidity_sweep. Sole alias `t_kz_sweep`, recorded installed, source md2_catalog. The accounting records NO entry, exit or sizing text (all three are its recorded gaps; algorithm grade PARTIAL) and no universe/asset class/timeframe.
- Evidence in Test beyond the accounting: the code-derived/spec document `docs/T_KZ_SWEEP-ALGORITHM.md` and the running code `sleeves/t_kz_sweep.py` (class `KZSweep`), whose module docstring carries the creation specification and the kz-v2 edge fixes. The algorithm below is taken from those two Test documents and the code's own constants, which are the best evidence on file. The algorithm doc notes the Test copy was sanitized at 2 points to pass the public-repo privacy gate and that the private original in the master-desk repo (`mdesk/engines/kz_sweep.py`) is the verbatim source; that repo is not among the searched repos, and the sanitization points are not identified in the doc, so the Test copy is the code of record for this package.

## What this strategy is

An ICT killzone liquidity-sweep reversal sleeve: it fades a sweep of known liquidity levels (prior Globex day high/low, untouched day-minus-2 and day-minus-3 highs/lows, Asia, London and pre-open extremes) when price reclaims the level on a 15-minute close inside the 09:45-10:30 ET morning killzone. Long and short on QQQ/SPY (levels from NQ/ES futures), long-only on BTC-USD; hard flat at 12:00 ET, never overnight.

## Full algorithm

From `docs/T_KZ_SWEEP-ALGORITHM.md` and the constants and `signal_at` logic in `sleeves/t_kz_sweep.py`, in evaluation order:

1. Levels, built on 15-minute futures bars (NQ=F for QQQ, ES=F for SPY) or on BTC-USD itself, known before the 09:30 open of the Globex day (the Globex day rolls at 18:00 ET): prior Globex day high/low; day-minus-2 and day-minus-3 highs/lows, counted only while untouched up to the open; Asia session (20:00-00:00) extremes; London (02:00-05:00) extremes; pre-open extremes. At least 3 prior days of bars are required or there are no levels.
2. Window: only 15-minute bars closing inside 09:45-10:30 ET are traded.
3. Range-day stand-aside: if both the prior-day high and prior-day low have been swept by the candidate bar, no signal.
4. Trigger: exactly one side qualifies: a swept low level now below the close (a reclaim up, buy) or, when shorts are allowed, a swept high level now above the close (a reclaim down, sell); if both sides qualify, no signal. BTC-USD is long-only.
5. Stop: beyond the session extreme so far, buffered by 0.02% (BUF = 0.0002): stop = session low x (1 - 0.0002) for a buy, session high x (1 + 0.0002) for a sell.
6. Target: the nearest untouched opposite level whose reward-to-risk is at least 1.5 (MIN_RR); futures prices are translated to the traded ETF by percent distance from the signal close. If no opposite level clears the 1.5 floor, no trade.
7. Exit: the target, the stop, or the hard time exit at 12:00 ET, whichever comes first; never overnight. (A time exit executed more than 600 s after 12:00 ET of the fill day is recorded as a LATE exit in the ledger.)
8. Sizing and lane: shadow Test lane, 3 slots of $1,000 (principal $3,000, pos_usd 1000.0); adds are OFF (a slot stays $1k).
9. Policy version in code: POLICY "kz-v2" (v2 = the Edge Lab v3 review fixes: EDGE-1 revalidate, EDGE-2 decision log including abstentions, EDGE-3 source exits). Feed: Yahoo chart API 15-minute bars (prepost), cached to the sleeve's state feed directory, fetched only when needed (weekday 09:40-12:10 ET or cold cache); a stale mark (30 minutes or more) reads as no mark rather than a guess.

## Files in this repo

- This package: `docs/T_KZ_SWEEP-RECREATE.md`
- Algorithm/spec document: `docs/T_KZ_SWEEP-ALGORITHM.md`
- Running code (already in Test; nothing vendored for this package): `sleeves/t_kz_sweep.py` (class `KZSweep`, sid `t_kz_sweep`); the same code as packaged from the source is also at `packages/grokbot/master-desk-md2/mdesk/engines/kz_sweep.py` in this repo.
- Original source named in the algorithm doc: `mdesk/engines/kz_sweep.py` in the master-desk repo (not in this repo; the Test copy is sanitized at 2 points, per the doc).

## Configuration

From the code: UNIVERSE QQQ (levels NQ=F), SPY (levels ES=F), BTC-USD (own levels, long-only). Window 09:45-10:30 ET; time stop 12:00 ET; MIN_RR 1.5; BUF 0.0002; LOOKBACK 3 days; bar step 900 s; slots 3; principal $3,000; pos_usd $1,000; status installed; venue "test" (shadow lane); state: the feed cache directory and the append-only decision log named in the code (desk-runtime paths, not repo paths).

## Data inputs

Yahoo chart API 15-minute bars with pre/post session for NQ=F, ES=F and BTC-USD, 8-day range (code `_http`).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The sleeve is `sleeves/t_kz_sweep.py`; it imports the desk sleeve base (`Sleeve`, `Signal`) from its package (`from ..sleeve import Sleeve, Signal` in the packaged copy), so place it inside the desk sleeve package or provide that base module.
3. No third-party packages beyond the standard library are used by the code (urllib, json, zoneinfo).
4. Run it inside the desk's sleeve runner on its 15-minute cadence during the weekday window; it fetches and caches its own Yahoo feed and writes its decision log as configured in the code.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- With fewer than 3 prior days of bars, no levels and no signal are produced.
- A 15-minute bar closing at 09:45-10:30 ET that reclaims exactly one swept level, with an untouched opposite level at reward-to-risk at least 1.5, produces one signal carrying that level, entry at the close, the buffered session-extreme stop, and the target level.
- A day on which both prior-day extremes are swept produces no signal; a bar qualifying on both sides produces no signal.
- BTC-USD never produces a short signal.
- Any open position is exited at target, stop, or 12:00 ET, and never held overnight.
