# lz_s_mn_w_green_smh: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna W green calm SMH (Midna port)", type "trend following", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: no stop / time exit 126 sessions", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 126, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- This id is the forward-lab account midna_w_green_calm_smh: rule lines in `docs/verify/midna.md` (forward-lab section). Its v3 form is the fire-consumer spec s_mn_w_green_smh in `desk3/lazarus_midna.py` (gate smh_calm), kept separate below.
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A weekly Tensor Green rule account gated on a calm SMH tape: it buys weekly green fires whose 63-session skew and SMH-minus-SPY relative return sit inside recorded bands, with no FOMC decision in the next five sessions, and holds 126 sessions with no stop. One of the forward lab's six $20,000 accounts.

## Full algorithm

A. Forward-lab book (`sleeves/midna/forward_scan.py` FORWARD_SPECS entry w-green-smh, test _t_green_smh; `sleeves/midna/forward.py`), in evaluation order:
1. A hit requires the weekly state to be green (weeklyGreen true).
2. Rule test (ruleId V4-1W-GREEN-TAIL-H126-ALL-fb459d4f): 63-session skew inside -0.680 to 0.472; SMH - SPY 63-session return inside -0.049 to 0.097; pre-FOMC feature = 0 (no FOMC decision within the next five sessions). Missing or out-of-band values fail.
3. Liquid filter: last close at least $5 and 20-session mean dollar volume at least $1,000,000.
4. Staging, entry and exit exactly as the forward lab's shared law: staged hits replace the staged list up to free slots (6 - open, at most 6 hits); entry in regular hours from 10:00 ET on a fresh panel on the session right after the signal session, qty = floor((20,000 / 6) / (price x (1 + cost bps))) capped by cash; exit at the first such pass once sessions from entry reach the hold of 126 (the accounting record agrees: no stop, time exit 126 sessions from fill).

B. v3 fire-consumer (`sleeves/s_mn_w_green_smh.py` delegating to `desk3/lazarus_midna.py`, SPECS entry s_mn_w_green_smh):
1. Spec: family green, timeframe 1W, hold 126 sessions, no stop, budget $1,000, gate smh_calm; at most 1 position (the engine returns nothing while a position is held).
2. Exits first: time exit at 126 sessions held (a 15% stop exists in the engine only when the spec names one; this spec's stop is None).
3. Entry: a fresh matching fire (family green, weekly timeframe, fire date aged 0 to 10 days), priced off the freshest close (the engine's ENH19 reprice, on by default), quantity = floor($1,000 / price), refused when the symbol's last bar lags the universe's latest bar by more than 4 days (ENH20).
4. Gate smh_calm: the extra flag smh_calm when supplied, else computed from SMH bars: the 20-session SMH return (last close / close 21 bars back - 1) must have absolute value at most 0.05; with under 21 SMH bars and no flag, the entry is refused.

## Files in this repo

- This doc: `docs/LZ_S_MN_W_GREEN_SMH-RECREATE.md`
- Code (already in Test): `sleeves/midna/forward.py` (IDS w-green-smh = midna_w_green_calm_smh), `sleeves/midna/forward_scan.py` (FORWARD_SPECS, _t_green_smh)
- Code (already in Test, v3 form): `sleeves/s_mn_w_green_smh.py`, `desk3/lazarus_midna.py` (SPECS s_mn_w_green_smh, gate smh_calm)
- Rule lines: `docs/verify/midna.md` (forward-lab section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: the forward panel's names; liquid filter close >= $5, dv20 >= $1,000,000.
- Forward account: $20,000; at most 6 positions; per-position $20,000 / 6 before cost. Hold 126 sessions; no stop.
- Rule bands: skew (63 sessions) -0.680 to 0.472; SMH - SPY (63 sessions) -0.049 to 0.097; pre-FOMC = 0.
- v3 form: $1,000 budget, 1 position, weekly green fires aged 0 to 10 days, SMH 20-session absolute return at most 5%.

## Data inputs

Midna's daily panel with weekly Tensor states and the skew / smhrel / prefomc features (forward_scan.py); live quotes for entry pricing. v3 form: Midna fires (view midna_fires / tensor bundle), daily and weekly bars, and SMH bars for the calm gate.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_w_green_smh` in `docs/ALL-SLEEVES.json`.
3. For the forward book, open `sleeves/midna/forward_scan.py` (the w-green-smh FORWARD_SPECS entry and _t_green_smh) and `sleeves/midna/forward.py`; serve the panel and fresh quotes, one scan per session. For the v3 form, open `desk3/lazarus_midna.py` SPECS['s_mn_w_green_smh'] and serve fires, bars and SMH bars to `evaluate`.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A weekly-green name with skew outside -0.680 to 0.472, SMH-SPY outside -0.049 to 0.097, or an FOMC decision inside five sessions is not a hit.
- No seventh forward position opens; entries happen only from 10:00 ET on the session after the signal, on a fresh panel.
- A held forward name exits at 126 sessions from fill and is never stopped out on price.
- In the v3 form, an entry is refused when SMH's 20-session absolute return exceeds 5% (and no explicit calm flag overrides it), and a second position never opens while one is held.
- The v3 time exit fires at exactly 126 sessions held.
