# lz_s_mn_w_cyan_adx: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W cyan high ADX (Midna port)", type "forecast and ML models", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: no stop / time exit 126 sessions", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 126, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- This id is the forward-lab account midna_w_cyan_high_adx: rule lines in `docs/verify/midna.md` (the forward-lab section: weekly Cyan rules, up to 6 hits, hold 126, sizing floor((20,000 / 6) / (price x (1 + cost)))); the same frozen rule also runs as the lean-desk port `sleeves/rule_1w_cyan_mom_adx.py` with its card `strategies/femto/femto-rule-1w-cyan-mom-adx.md`, whose thresholds agree to the recorded precision.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A weekly Tensor Cyan rule account: it buys weekly cyan fires on thinner names whose 126-session return is at least about 44.5% and whose weekly ADX is at least about 25.8, and holds each name 126 sessions with no stop. One of the forward lab's six $20,000 accounts.

## Full algorithm

From `sleeves/midna/forward_scan.py` (FORWARD_SPECS entry w-cyan-adx, test _t_adx) and `sleeves/midna/forward.py`, in evaluation order:

1. Scan: for each name the forward scan builds daily and weekly rows from the panel; a hit requires the weekly state to be cyan (weeklyCyan true).
2. Rule test (_t_adx, ruleId V2-1W-CYAN-RAW-H126-f10092bc): log dollar-volume feature dv <= 7.35, 126-session return (mom) >= 0.445, weekly ADX >= 25.8. Any missing feature fails the test. (The lean-desk port of the same frozen rule records the thresholds at full precision: dv <= 7.350284290313721, mom >= 0.44456708133220685, ADX >= 25.795216751098632.)
3. Liquid filter (forward lab): last close at least $5 and 20-session mean dollar volume at least $1,000,000.
4. Staging: when the panel's session has been scanned, the account's staged list is replaced by its hits on names it does not hold, up to its free slots (6 - open); at most 6 hits per account.
5. Entry: regular hours from 10:00 ET, on a fresh panel, on the session right after the signal session (an older row is dropped): qty = floor((20,000 / 6) / (price x (1 + cost bps))) with price the ask (else last on the cost schedule) to the cent, capped by the cash.
6. Exit: the first such pass once the sessions after the entry day through the panel's session reach the hold: 126 sessions (holdSessions = 126; the accounting record agrees: no stop, stop_pct 99.0, time exit 126 sessions, hold counted from fill). No price stop.
7. Removed gates (recorded in forward.py's header, part of the port): the source desk's desk-wide red-day buy gate, its entry-block calendar/volatility gates and its 40% adverse circuit breaker are not part of this book.

## Files in this repo

- This doc: `docs/LZ_S_MN_W_CYAN_ADX-RECREATE.md`
- Code (already in Test): `sleeves/midna/forward.py` (forward-lab accounts; IDS w-cyan-adx = midna_w_cyan_high_adx), `sleeves/midna/forward_scan.py` (FORWARD_SPECS, _t_adx)
- Code (already in Test, lean-desk port of the same frozen rule): `sleeves/rule_1w_cyan_mom_adx.py`
- Strategy cards: `strategies/femto/femto-rule-1w-cyan-mom-adx.md` (the rule and its variants table, which names the forward-lab w-cyan-adx row)
- Rule lines: `docs/verify/midna.md` (forward-lab section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: the forward panel's names (the lean port's card records a 1,838-name genome universe); liquid filter close >= $5, dv20 >= $1,000,000.
- Account: $20,000; at most 6 positions; per-position budget $20,000 / 6 before cost.
- Rule: weekly cyan; dv <= 7.35; 126-session return >= 0.445; weekly ADX >= 25.8. Hold: 126 sessions; no stop.
- Cadence/state: one scan per session (cached for all six forward accounts); state is the staged list, the open positions with entry day, and cash.

## Data inputs

Midna's daily panel (daily bars plus the weekly Tensor states and the dv / mom / weekly ADX features computed in forward_scan.py); live quotes for entry pricing (fresh, at most 15 minutes old).

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_w_cyan_adx` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/midna/forward_scan.py`; confirm the w-cyan-adx FORWARD_SPECS entry (holdSessions 126) and the _t_adx thresholds (7.35 / 0.445 / 25.8). Open `sleeves/midna/forward.py` for staging, entry (from 10:00 ET on the session after the signal) and the 126-session exit. Serve the daily panel and fresh quotes and run one scan per session.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A weekly-cyan name with dv above 7.35, 126-session return below 0.445, or weekly ADX below 25.8 is not a hit; a missing feature also fails.
- A hit under $5 or under $1,000,000 dv20 is filtered out.
- No seventh position opens; staged hits replace the staged list only on a fresh scanned session.
- An entry is made only on the session right after the signal session, from 10:00 ET, with a fresh quote.
- A held name exits at 126 sessions from fill and is never stopped out on price before that.
