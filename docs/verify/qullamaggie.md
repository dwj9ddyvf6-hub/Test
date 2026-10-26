# Verification: Qullamaggie

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [Qullamaggie breakout](../../strategies/qullamaggie/qm-leader-breakout.md)

| Rule | Read from |
|---|---|
| Entry: Leader: the best of its 21-, 63- and 126-session return percentiles is ≥ 98% of the universe. | `sleeves/femto/qullamaggie.py:85-86`<br>`sleeves/femto/qullamaggie.py:130-157`<br>`sleeves/femto/qullamaggie.py:344-367`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:36`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:259-278`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:535-537` |
| Entry: Setup: the 63-session high ≥ 30% above the close 64 sessions back; 10-session base range ≤ 28% of the close; the late half no wider than the early half; base lows sloping up; ≥ 70% of base closes within 3% of the 10- or 20-day SMA; both SMAs rising over 3 sessions; 20-day dollar volume ≥ $5M. | `sleeves/femto/qullamaggie.py:87-96`<br>`sleeves/femto/qullamaggie.py:166-214`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:279-351`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:542-551` |
| Entry: Trigger: after the 5-minute opening range, price reaches max(opening-range high, base high); the stop is the lowest low before the trigger bar, and a stop wider than 1 ATR(20) skips the trade. | `sleeves/femto/qullamaggie.py:94-95`<br>`sleeves/femto/qullamaggie.py:217-235`<br>`sleeves/femto/qullamaggie.py:454-462`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:385-427`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:216-220` |
| Entry: Femto: enters at the next bar's open within 30 minutes of the trigger, never below the trigger. | `sleeves/femto/qullamaggie.py:108`<br>`sleeves/femto/qullamaggie.py:441-453` |
| Entry: Aurelia paper and pass-3: longs only while QQQ is risk-on (10-day SMA above the 20-day, both rising). | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:231-247`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:508-510`<br>`sleeves/femto/qullamaggie_paper.py:176-184` |
| Exit: Hard stop at the entry stop. | `sleeves/femto/qullamaggie.py:470-472`<br>`sleeves/femto/qullamaggie.py:531-533`<br>`sleeves/femto/qullamaggie_paper.py:355-357`<br>`sleeves/qullamaggie/qullamaggie.py:547` |
| Exit: After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:62-63`<br>`sleeves/qullamaggie/qullamaggie.py:261-262` |
| Exit: After 3 sessions, a close below the 10-day SMA (the 20-day when the close is more than 1.5 ATR above the 10-day) exits at the next open. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:64-66`<br>`sleeves/qullamaggie/qullamaggie.py:246-258` |
| Exit: Femto: the same scale and trail, decided on the last completed daily close. | `sleeves/femto/qullamaggie.py:97-100`<br>`sleeves/femto/qullamaggie.py:291-301`<br>`sleeves/femto/qullamaggie.py:507-544` |
| Sizing: 0.35% of the session's opening equity on the stressed loss per share: stop distance + the 95th-percentile adverse overnight gap (126 sessions) + round-trip friction; capped at 20% of equity per name, 100% gross, 25% per sector, 4% total open risk, 1% of 20-day dollar volume, 15 positions; a $100,000 book. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:46-56`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:201-229` |
| Sizing: Femto: the same stressed-loss sizing with 0.35% risk, 20% per name, 1% of 20-day share volume, 10 positions, 3 bps friction a side. | `sleeves/femto/qullamaggie.py:81-84`<br>`sleeves/femto/qullamaggie.py:274-288`<br>`sleeves/femto/qullamaggie.py:421`<br>master-desk `desk/sleeves/families/femto_specs.py:507` |
| Data: Split-adjusted daily bars of the genome (cached); today's 5-minute bars (Femto) or 1-minute tapes (paper, pass-3); QQQ daily bars. | master-desk `desk/sleeves/families/femto_specs.py:483-508`<br>master-desk `desk/sleeves/families/femto_specs.py:776-794`<br>`sleeves/qullamaggie/qullamaggie.py:271-289` |
| Public rule sources | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:85-90` |
| Aurelia engine defaults | `sleeves/femto/vendor/aurelia_qulla/desk.py:24-66` |
| Paper open-loss lock | `sleeves/femto/qullamaggie_paper.py:296-326` |
| Midna v3 wrappers | `sleeves/qullamaggie.py:1-13` |

## [Qullamaggie episodic pivot](../../strategies/qullamaggie/qm-episodic-pivot.md)

| Rule | Read from |
|---|---|
| Entry: Pool: 20-day dollar volume ≥ $5M and a 126-session return ≤ 30%, while QQQ is risk-on. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:55`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:60`<br>`sleeves/qullamaggie/qullamaggie.py:184-189` |
| Entry: Open: gap ≥ 10% over the last close and first-20-minute volume ≥ 0.5× the 20-day average. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:58-59`<br>`sleeves/qullamaggie/qullamaggie.py:192-199` |
| Entry: Catalyst: a verified 8-K / 6-K public before the trigger minute. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:61`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:455-479`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:569-606`<br>master-desk `desk/feedlib/qm_inputs.py:35`<br>master-desk `desk/feedlib/qm_inputs.py:186` |
| Entry: Trigger: from minute 20, price crosses the opening-range high; stop = the low before the trigger bar, within 1 ATR. | `sleeves/qullamaggie/qullamaggie.py:218-224`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:385-427`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:44` |
| Exit: Hard stop at the entry stop. | `sleeves/qullamaggie/qullamaggie.py:547` |
| Exit: After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:62-63`<br>`sleeves/qullamaggie/qullamaggie.py:261-262` |
| Exit: After 3 sessions, a close below the 10-day SMA (the 20-day when the close is more than 1.5 ATR above the 10-day) exits at the next open. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:64-66`<br>`sleeves/qullamaggie/qullamaggie.py:246-258` |
| Sizing: 0.35% of the session's opening equity on the stressed loss per share: stop distance + the 95th-percentile adverse overnight gap (126 sessions) + round-trip friction; capped at 20% of equity per name, 100% gross, 25% per sector, 4% total open risk, 1% of 20-day dollar volume, 15 positions; a $100,000 book. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:46-56`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:201-229` |
| Data: Genome daily bars, 1-minute tapes, SEC EDGAR current reports (acceptance time). | `sleeves/qullamaggie/qullamaggie.py:271-289`<br>master-desk `desk/feedlib/qm_inputs.py:132-146` |
| Public rule source | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:85-90` |

## [Qullamaggie parabolic short](../../strategies/qullamaggie/qm-parabolic-short.md)

| Rule | Read from |
|---|---|
| Entry: Setup: ≥ 3 consecutive up closes and a 3-session run ≥ 50% (≥ 300% at a market cap ≤ $300M); borrowable; $5M dollar volume. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:67-71`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:608-632`<br>`sleeves/qullamaggie/qullamaggie.py:202-215` |
| Entry: Trigger: a bar's low reaches the opening-range low and closes under the session VWAP; short at the next bar's open, stop = the high before the fill. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:428-453` |
| Exit: Hard stop at that high. | `sleeves/qullamaggie/qullamaggie.py:547` |
| Exit: Covers at max(10-day, 20-day SMA) of the completed closes. | `sleeves/qullamaggie/qullamaggie.py:227-231` |
| Exit: After the third session held, in profit: sells a third (at the close) and moves the stop to breakeven. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:62-63`<br>`sleeves/qullamaggie/qullamaggie.py:261-262` |
| Exit: After 3 sessions, a close above the 10-day SMA exits. | `sleeves/qullamaggie/qullamaggie.py:246-258` |
| Sizing: Half the long risk: 0.175% of opening equity on the stressed loss per share; the same caps. | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:658-661`<br>`sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:201-229` |
| Data: Genome daily bars, 1-minute tapes, EDGAR share counts for the market cap. | `sleeves/qullamaggie/qullamaggie.py:271-289`<br>master-desk `desk/feedlib/qm_inputs.py:244` |
| Public rule source | `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py:85-90` |
