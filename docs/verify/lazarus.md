# Verification: Lazarus

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

## [Tensor tracker lanes (1H / 1D / 1W)](../../strategies/lazarus/lz-tracker.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker fire marked tradeable on the lane's timeframe, on Yahoo canonical bars, within the last 5 sessions. | `sleeves/lazarus/vendor/lazarus/signals.py:20-33`<br>`sleeves/lazarus/lazarus.py:304-313` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: the tracker's calibrated hold (max bars) and stop for that fire. | `sleeves/lazarus/vendor/lazarus/signals.py:30-31` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: 1H: $1,725 a position, 30 slots, $51,750; 1D: $1,725, 5 slots, $8,625; 1W: $1,410, 14 slots, $17,877; dv20 floor $1M, cap 1% of dv20. | `sleeves/lazarus/vendor/lazarus/sleeves.json:17-168` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Galath's tracker fire files (latest fires + 5-session log); Yahoo daily bars; desk quotes. | `sleeves/lazarus/lazarus.py:474-503` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:17-168` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |
| Midna lanes on the same tracker fires | master-desk `desk/feedlib/midna_fires.py:118`<br>master-desk `desk/feedlib/midna_fires.py:188-200`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:5201-5305` |

## [Daily Cyan desk feed](../../strategies/lazarus/lz-daily-cyan.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1D Cyan full or covered lab book fire (rule search or boosted trees). | master-desk `desk/vendor/galath_research/DESK_INTEGRATION/lab_live/desk_feed.py:92-100` |
| Entry: Size class by PIT band: small = core, micro = core at 0.52×, mid/large = logged only; covered-only fires trade at test size. | master-desk `desk/vendor/galath_research/DESK_INTEGRATION/lab_live/desk_feed.py:93-96`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:169-225` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 21 sessions from the fill. | master-desk `desk/vendor/galath_research/DESK_INTEGRATION/lab_live/desk_feed.py:98`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:169-225` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $700 core small, $364 core micro, $230 test; 68 slots, $12,500; cap 5% of dv20, floor $100k. | `sleeves/lazarus/vendor/lazarus/sleeves.json:169-225` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's daily book outputs; Yahoo daily bars. | `sleeves/lazarus/lazarus.py:474-503` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:169-225` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Weekly Cyan tier A](../../strategies/lazarus/lz-weekly-cyan-tier-a.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1W Cyan fire whose tier is A: small band (core lane 1wa), micro band, or mid/large band (unified tier). | master-desk `desk/vendor/galath_research/DESK_INTEGRATION/lab_live/desk_feed.py:122-126`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:104-119` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 52 weeks. | master-desk `desk/vendor/galath_research/DESK_INTEGRATION/lab_live/desk_feed.py:125`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:115-118` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position: 1wa 17 slots / $17,250 (cap 5% dv20); micro 1 slot; mid/large 7 slots. | `sleeves/lazarus/vendor/lazarus/sleeves.json:226-278`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:482-585` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger tags; PIT SEC shares for the band. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:104-113` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:226-278` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Daily Green under $5](../../strategies/lazarus/lz-daily-green-under5.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1D Green fire with close < $5. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:120-123` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 40 sessions. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:123` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, 2 slots, $2,789. | `sleeves/lazarus/vendor/lazarus/sleeves.json:586-637` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger fires. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:85-100` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:586-637` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Weekly Green tier A small](../../strategies/lazarus/lz-weekly-green-small.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1W Green ue_tag with unified tier A (dv20 ≥ $100k) and split-corrected PIT band small. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:186-200` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 52 weeks. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:200` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, 2 slots, $2,696. | `sleeves/lazarus/vendor/lazarus/sleeves.json:740-794` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger tags; PIT SEC shares. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:186-197` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:740-794` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Moonshot weekly lane](../../strategies/lazarus/lz-moonshot.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1W Cyan or Green fire with close ≤ $14.94, 60-week depth ≥ 70, dv20 ≥ $1M; tier A first on ties. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:34`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:132-149` |
| Entry: Midna's book: a weekly buy-cyan fire with close ≤ $14.94 and 60-week depth ≥ 70.35, ≤ 10 days old, not seen before; fewer than 10 open. | `sleeves/midna/shadow.py:31-34`<br>`sleeves/midna/shadow.py:132-184` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 52 weeks. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:147` |
| Exit: Midna's book: closes at the first regular-hours print after its 78th week; no stop. | `sleeves/midna/shadow.py:120-131`<br>`sleeves/midna/shadow.py:132-184` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, 2 slots, $2,581. Midna's book: floor(min(cash, $1,000) / price). | `sleeves/lazarus/vendor/lazarus/sleeves.json:795-850`<br>`sleeves/midna/shadow.py:132-184` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger fires and ue_tag values. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:138-142` |
| Data: Midna's book: the hourly watch's weekly moonshot fires. | master-desk `desk/feedlib/midna_watch.py:13-14` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:795-850` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |
| Midna v3 `s_mn_moonshot`: 390-session hold, no stop | `sleeves/s_mn_moonshot.py:20`<br>`sleeves/s_mn_moonshot.py:52-57` |

## [Lab 1D Green trees](../../strategies/lazarus/lz-lab-1d-green-trees.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1D-green-full lab book fire picked by the boosted trees. | `sleeves/lazarus/vendor/lazarus/signals.py:49` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 21 sessions from the fill. | `sleeves/lazarus/vendor/lazarus/signals.py:49`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:329-379` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, 8 slots, $8,320. | `sleeves/lazarus/vendor/lazarus/sleeves.json:329-379` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's book outputs. | `sleeves/lazarus/vendor/lazarus/signals.py:34-56` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:329-379` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Lab 1W Cyan books](../../strategies/lazarus/lz-lab-1w-cyan-books.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1W-cyan-full or 1W-cyan-covered lab book fire. | `sleeves/lazarus/vendor/lazarus/signals.py:50` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 126 sessions from the fill. | `sleeves/lazarus/vendor/lazarus/signals.py:50`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:380-430` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000, 1 slot. | `sleeves/lazarus/vendor/lazarus/sleeves.json:380-430` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's book outputs. | `sleeves/lazarus/vendor/lazarus/signals.py:34-56` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:380-430` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Lab 1W Swing covered](../../strategies/lazarus/lz-lab-1w-swing.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1W-swing-covered lab fire from the rule search. | `sleeves/lazarus/vendor/lazarus/signals.py:51` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 126 sessions from the fill. | `sleeves/lazarus/vendor/lazarus/signals.py:51`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:431-481` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000, 1 slot. | `sleeves/lazarus/vendor/lazarus/sleeves.json:431-481` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's book outputs. | `sleeves/lazarus/vendor/lazarus/signals.py:34-56` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:431-481` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Lab rule books (1D / 1W)](../../strategies/lazarus/lz-lab-rules.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a lab fire that matches a frozen rule; the rule's horizon H (default 21 daily or 126 weekly). | `sleeves/lazarus/vendor/lazarus/signals.py:52-54` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit H + 1 sessions from the fill. | `sleeves/lazarus/vendor/lazarus/signals.py:53-54`<br>`sleeves/lazarus/vendor/lazarus/sleeves.json:638-739` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position: 1D 73 slots / $73,616; 1W 1 slot. | `sleeves/lazarus/vendor/lazarus/sleeves.json:638-739` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's book outputs and frozen rule ids. | `sleeves/lazarus/vendor/lazarus/signals.py:34-56` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:638-739` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |

## [Q07 Tensor alt-data confluence cells](../../strategies/lazarus/lz-q07.md)

| Rule | Read from |
|---|---|
| Entry: Cell = lane × hold × band × tags, e.g. `Q07-w_cyan-H52-small-cheap5+wiki_cov`; a fire trades only when every tag of its cell is true (a missing input is no fire). | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_q07.py:18-38`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_q07.py:43-48`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_q07.py:103-110` |
| Entry: Tags: tierA (unified tier A), deep70 (60-week depth ≥ 70), cheap5 (close < $5), mom6 (126-day return ≥ the frozen 67th percentile), stress_vix20 (VIX ≥ 20), wiki_cov / wiki_low / wiki_spike2 (Wikipedia attention), insider2, ats_z1 (FINRA ATS z ≥ 1), gamma_low. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_q07.py:85-102`<br>master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:170-173` |
| Entry: Index lanes trade the union of their cells: `lz_q07_wiki` (the wiki cells), `lz_q07_ins2` (the insider cells). | `sleeves/lazarus/lazarus.py:166-187` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 52 or 78 weeks. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:182-184` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, mostly 1 slot per cell; the index lanes take the paper-test K = min(20, ⌈20 × H / 126⌉). | `sleeves/lazarus/vendor/lazarus/sleeves.json:1325-1376`<br>`sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker weekly fires, the w_swing feed, and the alt-data nightlies (Wikipedia, insider, FINRA, options market). Off since 2026-10-19, so these lanes are blocked. | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:150-160`<br>`sleeves/lazarus/lazarus.py:272-298` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:905-1012` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |
| Midna v3 Q07 readings | `desk3/q07_engine.py:31-34`<br>`desk3/q07_engine.py:70-96`<br>`desk3/q07_engine.py:153-154` |
| Swing stress cell | master-desk `desk/vendor/galath_research/shadow/paper_sleeve/sleeve_feed.py:160-168` |

## [Q14 under-$5 weekly book](../../strategies/lazarus/lz-wait-q14.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1W Cyan or Green fire with tier A and close ≤ $5.00; the entry limit is capped at $5.00. | `sleeves/lazarus/galath_wait_feed.py:82`<br>`sleeves/lazarus/galath_wait_feed.py:189-209`<br>`sleeves/lazarus/lazarus.py:374-375` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, exit at the close of the 78th weekly bar. | `sleeves/lazarus/galath_wait_feed.py:82`<br>`sleeves/lazarus/lazarus.py:192-201` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = min(20, ⌈20 × 390 / 126⌉) = 20 slots. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger (1W fires, ue_tag tiers). | `sleeves/lazarus/galath_wait_feed.py:162-188` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1013-1064` |

## [Intraweek early entry](../../strategies/lazarus/lz-wait-intraweek.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a provisional 1W marker on the developing week (day 1-4), one fire per symbol-week. | `sleeves/lazarus/galath_wait_feed.py:451-476` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, exit at the close of the fire Friday + 52 weeks. | `sleeves/lazarus/galath_wait_feed.py:470`<br>`sleeves/lazarus/lazarus.py:192-201` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = 20. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker Yahoo weeks plus the partial week from closed daily bars. | `sleeves/lazarus/galath_wait_feed.py:451-460` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1065-1116` |

## [CHASE weekly lane](../../strategies/lazarus/lz-wait-chase.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1W Cyan fire whose 126-day momentum ranks ≥ 0.90 against the liquid cross-section and whose drawdown from the 63-day high is above -5%. | `sleeves/lazarus/galath_wait_feed.py:85`<br>`sleeves/lazarus/galath_wait_feed.py:328-395` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 52 weeks. | `sleeves/lazarus/galath_wait_feed.py:85`<br>`sleeves/lazarus/galath_wait_feed.py:386` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = 20. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger; the tracker engine's daily store for the cross-section. | `sleeves/lazarus/galath_wait_feed.py:309-327` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1117-1168` |

## [OLX R1/R2 books](../../strategies/lazarus/lz-wait-olx.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a lab fire of one of the frozen OLX R1/R2 rule ids. | `sleeves/lazarus/galath_wait_feed.py:396-430` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, exit after the rule's H sessions (H + 1 from the fill). | `sleeves/lazarus/galath_wait_feed.py:424-430`<br>`sleeves/lazarus/lazarus.py:192-201` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = 20. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's OLX job outputs. | `sleeves/lazarus/galath_wait_feed.py:440-450` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1169-1220` |

## [R2 Daily Cyan extended](../../strategies/lazarus/lz-wait-r2-dcyan.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a 1D-cyan-covered rule-search fire from the live lab. | `sleeves/lazarus/galath_wait_feed.py:431-439` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, 21 sessions from the fill. | `sleeves/lazarus/lazarus.py:192-201` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = min(20, ⌈20 × 21 / 126⌉) = 4. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The lab's book outputs. | `sleeves/lazarus/galath_wait_feed.py:440-450` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1221-1272` |

## [FLOW short volume / FTD / dark pool](../../strategies/lazarus/lz-wait-flow.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a tracker 1D Green fire, dv20 ≥ $100k, PIT band small, $5 ≤ close < $20, and the 5-file mean of FINRA short volume / total volume ≥ 0.447678 (files ≤ 7 days old). | `sleeves/lazarus/galath_wait_feed.py:83-84`<br>`sleeves/lazarus/galath_wait_feed.py:210-277` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, exit at the close of D + 60. | `sleeves/lazarus/galath_wait_feed.py:83`<br>`sleeves/lazarus/galath_wait_feed.py:272`<br>`sleeves/lazarus/lazarus.py:192-201` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position; K = 10. | `sleeves/lazarus/lazarus.py:158-163`<br>`sleeves/lazarus/lazarus.py:222-239` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Tracker ledger; FINRA Reg SHO daily short-volume files. | `sleeves/lazarus/galath_wait_feed.py:492-517` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:1273-1324` |

## [ChartsLector breakout leaders (small caps)](../../strategies/lazarus/cl-qm-small.md)

| Rule | Read from |
|---|---|
| Entry: Screen: ADR(14) ≥ 4%, EMA10 ≥ EMA20 ≥ SMA50 ≥ SMA150, close ≥ EMA20, 60-day volume > 300k; it turns on today. | master-desk `desk/vendor/chartslector/cl_core.py:26-31`<br>master-desk `desk/vendor/chartslector/cl_live_fires.py:72-73` |
| Entry: Then (close - SMA50) / ATR14 < 4, close ≥ $5, dv20 ≥ $100k, not an ETF, band small. | master-desk `desk/vendor/chartslector/cl_live_fires.py:74`<br>master-desk `desk/vendor/chartslector/cl_live_fires.py:93-96` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 90 sessions. | master-desk `desk/vendor/chartslector/cl_live_fires.py:14`<br>master-desk `desk/vendor/chartslector/cl_live_fires.py:21` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000 a position, 14 slots, $14,491. | `sleeves/lazarus/vendor/lazarus/sleeves.json:3933-3984` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: The tracker engine's daily store; PIT SEC shares for the band. | master-desk `desk/vendor/chartslector/cl_live_fires.py:22-41` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:3933-3984` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |
| Midna v3 reading | `sleeves/lazarus/s_cl_qm_small.py:1-12` |

## [ChartsLector market-fear rebound (QQQ)](../../strategies/lazarus/cl-vmr-qqq.md)

| Rule | Read from |
|---|---|
| Entry: Composite = 0.35 VIX score + 0.25 term (VIX / VIX3M) + 0.25 SKEW + 0.15 VVIX, each scored 0-100; fire at ≤ 35 at the close, then a 5-session cooldown. | master-desk `desk/vendor/chartslector/cl_core.py:32-47`<br>master-desk `desk/vendor/chartslector/cl_live_fires.py:101-107` |
| Entry: Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol. | `sleeves/lazarus/lazarus.py:352-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:28-36` |
| Exit: Plan: no stop, time exit 5 sessions. | master-desk `desk/vendor/chartslector/cl_live_fires.py:14`<br>master-desk `desk/vendor/chartslector/cl_live_fires.py:106` |
| Exit: Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%. | `sleeves/lazarus/lazarus.py:400-437` |
| Sizing: $1,000, 1 slot. | `sleeves/lazarus/vendor/lazarus/sleeves.json:3985-4037` |
| Sizing: Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped. | `sleeves/lazarus/lazarus.py:378-398`<br>`sleeves/lazarus/vendor/lazarus/gate.py:37-54` |
| Data: Cboe VIX, VIX3M, VVIX and SKEW daily files; QQQ daily bars. | `sleeves/lazarus/lazarus.py:505-546` |
| Lane parameters | `sleeves/lazarus/vendor/lazarus/sleeves.json:3985-4037` |
| Midna v3 lane specs, QQQ-down gate, 15% stop, capital/slots sizing | `desk3/lazarus.py:18-68`<br>`desk3/lazarus.py:235-247`<br>`desk3/lazarus.py:261`<br>`desk3/lazarus.py:318-333`<br>`desk3/lazarus.py:365` |
| Midna v3 reading | `sleeves/lazarus/s_cl_vmr_qqq.py:1-14` |
