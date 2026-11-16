# FIDELITY LEDGER — muse-desk-v3 Lazarus sleeves
Created 2026-10-24 (batch 9 creates this file; earlier batches scope-noted in V3-SCOPE 3.5).

## Substitution (all batch-9 lanes)
CSV fire file shadow/paper_sleeve/live/midna/midna_fires_v1.json lives in the desk-research, unreachable from this box (V3-SCOPE 3.4 probe). These lanes are built as fire-consumers against the desk's equivalent Tensor bundle producer: view["tensor"] (or midna_fires/extra channel in fixtures) carrying validated fires {sleeve_id,symbol,family,timeframe,date,price}. Signal generation stays upstream; desk code does gates, sizing ($1,000/slot, 1 slot), and exits. Fail-closed on absent/stale (>10d) fires.

| sleeve | catalog sketch | missing/underspecified | reading adopted |
|---|---|---|---|
| s_mn_w_cyan_breadth | Tensor 1W Cyan + breadth filter; no stop; 126 sessions; 1/$1,000 | breadth threshold/source unspecified | breadth_pct from extra (producer: market breadth); require >=0.50 |
| s_mn_w_cyan_vix | Tensor 1W Cyan in mid-VIX; no stop; 252 sessions; 1/$1,000 | mid-VIX band unspecified | 12 <= VIX <= 25 (extra vix_close or VIX bars) |
| s_mn_d_green_band | Tensor 1D Green, $10-20; no stop; 21 sessions; 1/$1,000 | none material | price in [10,20] at fire |
| s_mn_w_green_smh | Tensor 1W Green when SMH calm; no stop; 126 sessions; 1/$1,000 | calm definition unspecified | SMH abs 20-session return <=5% (or extra smh_calm bool) |
| s_mn_hourly_1w | Tensor weekly signal (Midna rules); 15% stop or 52 weeks; 1/$1,000 | name says hourly, catalog timeframe is 1W — catalog wins; family unspecified | accept any Tensor family on 1W; hold 260 sessions (=52w); -15% stop |

## Lazarus batch 1 (2026-10-24) — 1h, 1d, 1w, 1dc, 1wa, s_1dg, s_1wlab, s_1wsw, s_1wc_micro, s_1wc_ml
Common: the desk-research unreachable (V3-SCOPE 3.4); all ten are fire-consumers on the desk's lazarus_fire_ingest / Tensor-bundle equivalent producer (INPUTS=lazarus_fires,bars,positions) — substitution recorded per task instruction. Fire schema assumed: sleeve_id, symbol, fired_at, price, optional target_price/horizon_sessions/cap_tier/signal_tier/family/ml_pick/qqq_red/stock_red; tier/cap/family enforced when present, sleeve-specific routing implies them when absent.
| sleeve | catalog rule implemented | underspecification + reading |
|---|---|---|
| 1h | Tensor hourly, buy within 30m when QQQ+stock red, 30 slots $51,750 | Exit "calibrated plan per signal" not enumerated: reading = fire target_price else 5-session time exit, target/horizon persisted at entry in sleeve state. No stop in catalog => none applied. |
| 1d | QQQ-down, +20% exit, partial +30% then trail, 40 sessions, 15% stop, 6 slots $10,350 | Partial = sell half at +30% (qty>1); "then trail" has no trail % specified => remainder exits at +20% rule/time/stop on later evals. |
| 1w | QQQ-down, 15% stop, else 52 weeks, 15 slots $19,287 | 52 weeks = 252 sessions. |
| 1dc | Daily Cyan QQQ-down, no stop, time exit at signal horizon, 68 slots $12,500 | Horizon absent in catalog: fire horizon_sessions else default 21 sessions. |
| 1wa | 1W Cyan tier-A small, QQQ-down, 15% stop, 52w, 17 slots $17,250 | As 1w + tier/cap filters when fire carries them. |
| s_1dg | Boosted-tree pick on 1D Green, next open, no stop, 21 sessions, 17 slots $17,000 | Tree internals upstream (fire-consumer freeze); ml_pick=False fires refused. "Next open" = next desk cycle market entry. |
| s_1wlab | Four 1W Cyan books as one, next open after week, 15% stop, 126 sessions, 22 slots $22,000 | Book boundaries upstream; fires routed to this sleeve_id traded as one book. |
| s_1wsw | Rule-search 1W Swing QQQ-down, 15% stop, 126 sessions, 1 slot $1,000 | Rule set upstream (fire-consumer). |
| s_1wc_micro | 1W Cyan tier-A micro, 15% stop, 52w, 1 slot $1,000 | Tier/cap enforced when present. |
| s_1wc_ml | 1W Cyan tier-A mid/large, 15% stop, 52w, 4 slots $4,000 | cap_tier in {mid,large,midlarge,mid/large}. |
Fidelity verdict: PARTIAL — faithful to every catalog-specified field; fire schema + 1h exit plan + 1d trail % are documented readings, not source-verified.

## Lazarus batch 6 — Q07 alt-data confluence lanes (2026-10-24)
Source record for all ten: CSV row (feed = sleeve_feed composer,
tracker ledger + alt-data tags, sleeve_fires_v1.json) + catalog
section 4.1 family rule (Tensor 1W family signal in cap band, named
filters, buy only on a QQQ-down day within 5 sessions of signal, exit
on 15% stop or at the 52/78-week horizon, 1 slot at $1,000). No
the desk-research source code for these lanes is reachable from this
box; the lanes are authored against that family rule, not ported.
- Feed substitution (recorded per task instruction): the CSV's
  sleeve_fires_v1.json composer is not produced on this box; lanes
  consume the v3 snapshot producer key "sleeve_fires" (producer
  "sleeve_feed", desk3/lazarus_batch6.py) carrying the same content —
  per-sleeve fire rows with alt-data tags (insider_buys,
  wiki_views_30d, cap_band, mcap_usd, signal_date). Until a warm
  supplies it the lanes report UNFED, never silently abstain.
- Underspecified tokens — readings adopted (all ten lanes):
  deep70 = close <= 70% of trailing 252-session high (>=30% drawdown);
  wcov = Wikipedia coverage present (wiki_views_30d > 0);
  wlow = low Wikipedia attention (wiki_views_30d < 1000);
  mom6 = positive 6-month momentum (close vs 126 sessions ago);
  ins2 = >=2 insider buys; cheap5 = close < $5; vix20 = VIX >= 20
  (snapshot "vix" producer key). Cap bands: mi < $300M, sm
  $300M-$2B, ml >= $2B market cap.
- s_q07w_g52_sm_ins2_wcov: GREEN family, 52w, small, ins2+wcov. Live.
- s_q07w_g78_mi_cheap5_deep70_ins2: GREEN, 78w, micro, cheap5+deep70+ins2. Live.
- s_q07w_g52_ml_ins2_wlow: GREEN, 52w, mid/large, ins2+wlow. Live.
- s_q07w_s78_sm_cheap5_ins2_vix20: SWING, 78w, small, cheap5+ins2+vix20. Lazarus Disabled -> parked.
- s_q07w_s52_sm_cheap5_ins2_vix20: SWING, 52w, small, cheap5+ins2+vix20. Disabled -> parked.
- s_q07w_s78_mi_cheap5_ins2_mom6: SWING, 78w, micro, cheap5+ins2+mom6. Disabled -> parked.
- s_q07w_s78_ml_deep70_ins2_vix20: SWING, 78w, mid/large, deep70+ins2+vix20. Disabled -> parked.
- s_q07w_s52_ml_deep70_ins2_vix20: SWING, 52w, mid/large, deep70+ins2+vix20. Disabled -> parked.
- s_q07w_s78_sm_deep70_ins2: SWING, 78w, small, deep70+ins2. Disabled -> parked.
- s_q07w_s52_sm_cheap5_deep70_ins2: SWING, 52w, small, cheap5+deep70+ins2. Disabled -> parked.

## LAZ4 — Q07 Green/Swing batch 4 (2026-10-24)
Substitution (all 10 lanes): CSV fire file
shadow/paper_sleeve/live/sleeve_fires_v1.json (sleeve_feed composer:
tracker ledger + alt-data tags) lives in the desk-research, unreachable
from this box (V3-SCOPE §3.4). Lanes consume the v3 snapshot "fires"
key (research-lane ingest contract) produced by the desk's composer /
Tensor-bundle equivalent; no fresh fires => fail closed.
Underspecification + readings (catalog §4.1 gives the family rule
only; per-lane filter thresholds are NOT in either source):
- deep70: read as price at/below 70% of trailing high (>=30% pullback);
  explicit composer tag wins, else computed from bars.
- wcov: Wikipedia coverage = wiki_cov tag true or wiki_views > 0.
- wlow: wiki_low tag true (no numeric threshold in sources).
- tierA: tier == "A" / tier_a tag. ats_z1: dark-pool ats_z >= 1.0.
  mom6: mom6_pct > 0, else 126-session return > 0. cheap5: price < $5.
- A filter with no tag evidence and no computable value fails closed.
- "Within 5 sessions": counted on QQQ bar dates when the signal date
  is inside the bar window, else calendar estimate (5/7 days).
- Exits: 15% stop + horizon time exit only (catalog states no other).
- Swing lanes are CSV-off/catalog Disabled => parked=true in config;
  entries refused in-engine too, exits still managed. Exceptions
  preserved: s78_sm_cheap5 $1,194/1 slot; s78_sm_deep70 $2,265/2 slots.
Per-lane fidelity: g52_sm_deep70_wcov PARTIAL (rule faithful, filter
thresholds are readings); g78_sm_tierA_wcov PARTIAL; g78_sm_deep70_wcov
PARTIAL; g52_ml_tierA_wcov PARTIAL; g78_ml_tierA_wcov PARTIAL;
g52_ml_ats_z1_mom6_wlow PARTIAL (ats/mom6/wiki-low all tag readings);
s52_sm_cheap5_wcov PARTIAL (parked); s52_sm_deep70_wcov PARTIAL
(parked); s78_sm_cheap5_wcov PARTIAL (parked); s78_sm_deep70_wcov
PARTIAL (parked, 2-slot exception preserved).

## LAZ-B7 — batch 7 (2026-10-24): Q07 swing x5, ChartsLector x2, Midna x3

Shared substitutions: CSV fire files (sleeve_fires_v1.json composer,
midna_fires_v1.json) live in the desk-research, unreachable (§3.4).
These lanes consume the desk's equivalent snapshot products:
`tensor_fires` {SYM: family+date} (Tensor bundle producer),
`midna_signals` / `hedge_signal` (Tensor-bundle signal products),
`alt_data` tags {insider_buys, wiki, gamma_low, ats_z, mcap_band}.
Unproduced keys => registry UNFED, never silent. "Within 5 sessions
of the signal" read as fire age 0–7 calendar days; sizing = whole
shares at floor(slot / last close); unaffordable slot refuses.

| sleeve | catalog sketch | missing/underspecified | reading adopted |
|---|---|---|---|
| s_q07w_s78_ml_deep70_glow_ins2 | 1W Swing mid/large deep70+low gamma+ins2; QQQ-down; 15% stop or 78w; 1/$1,000; Disabled→parked | deep70 threshold, gamma source unnamed | deep70 = close ≤ 30% of trailing-252 high; gamma_low = alt tag |
| s_q07w_s52_ml_ins2_mom6_vix20 | Swing mid/large ins2+mom6+VIX≥20; 52w; budget $1,984 exception; Disabled→parked | slot count for $1,984 unstated | 2 slots × $1,000, slice $1,984 in config; mom6 = 126-session return > 0 |
| s_q07w_s52_ml_ins2_mom6_wlow | Swing mid/large ins2+mom6+low Wikipedia; 52w; 1/$1,000; Disabled→parked | Wikipedia "low" threshold unnamed | alt wiki class tag == "low" |
| s_q07w_s78_mi_ats_z1_cheap5 | Swing micro ATS z≥1 + <$5; 78w; 1/$1,000; Disabled→parked | ATS z window unnamed | ats_z tag ≥ 1.0; cheap5 = close < $5 |
| s_q07w_s78_mi_ats_z1_mom6 | Swing micro ATS z≥1 + mom6; 78w; 1/$1,000; Disabled→parked | ATS z window unnamed | ats_z ≥ 1.0; mom6 > 0 (126 sessions) |
| s_cl_qm_small | ChartsLector Qullamaggie breakout leaders, small caps, ≥$5, not over-extended, QQQ-down; NO stop; out 90 sessions; 8/$8,000; Live | breakout / over-extended undefined; cl_live screens unreachable | breakout = close > prior-20-session high; over-extended = close > 1.25× SMA20 refuses; band via alt tag; computed from desk daily bars (screen substitution) |
| s_cl_vmr_qqq | VIX Mood Ring ≤35 buys QQQ next open; NO stop; out 5 sessions; 1/$1,000; Live | Mood Ring definition beyond ≤35 not given | gauge = ^VIX close (sanctioned Yahoo price-only); intent at last close, dispatcher takes next print |
| s_mn_hourly | Tensor hourly signal (Midna rules); 15% stop or 60 bars; 12/$12,000; Live | Midna branch signal files unreachable | fire-consumer over Tensor-bundle hourly product (`midna_signals`); held bars counted on 1Hour bars |
| s_mn_nostop | Same hourly signal, NO stop; 60-bar time exit; 1/$1,000; Live | same signal gap | identical consumer, stop disabled; fixture proves −20% does not exit, 60 bars does |
| s_mn_hedge | QQQ hedge on → TZA at 30% weight; off / max 20 sessions; 1/$1,000; Live | "30% weight" base unstated | 30% of the sleeve's $1,000 budget ($300); signal via `hedge_signal` |

## LAZ-B5 — Q07 batch 5 (10 lanes, shared engine desk3/lazarus_q07.py)
Substitution (all 10): CSV fire file shadow/paper_sleeve/live/sleeve_fires_v1.json (sleeve_feed composer: Tensor tracker ledger + alt-data tags) lives in the desk-research, unreachable from this box (V3-SCOPE §3.4). Lanes are fire-consumers on the v3 snapshot "fires" key (producer sleeve_feed_composer / lazarus_fire_ingest contract) — the desk-equivalent of the composer feed; no Tensor-bundle substitution was needed because Q07 signal composition is upstream by design. Fail-closed on absent/stale (>5 sessions) fires.
Underspecification (all Q07): the catalog names filters but gives no numeric definitions. Readings adopted (shared with batches 4/6 where they overlap): deep70 = explicit tag, else drawdown_from_high >= 0.30, else price <= 0.70 x 52w high, else price <= 70% of trailing bar high; cheap5 = price < $5; ins2 = insider_buys >= 2; mom6 = 6m return > 0 (numeric tag) else 126-session bar return > 0; vix20 = VIX >= 20 (fire tag, else VIX bars); wlow = wiki_low tag or wiki_attention == "low"; wcov = wiki_cov/wiki_coverage/wiki_views > 0 or wiki_attention in {covered, high, spike}. Missing filter evidence refuses (never assumed).
| sleeve | family/band/horizon | filters | status |
|---|---|---|---|
| s_q07w_s52_ml_deep70_wlow | swing/ml/52w | deep70, wlow | CSV off -> parked (exits managed) |
| s_q07w_s52_ml_deep70_vix20_wlow | swing/ml/52w | deep70, vix20, wlow | CSV off -> parked |
| s_q07w_s78_ml_deep70_wcov | swing/ml/78w | deep70, wcov | CSV off -> parked; catalog notes a 6-slot/$6,563 exception for this lane — NOT adopted: the §4.1 table row for this lane in the consolidated catalog extract carries no per-lane slot note in the copy in hand beyond the family standard; recorded here as an open fidelity risk, standard 1 slot/$1,000 used |
| s_q07w_s78_ml_deep70_mom6_wlow | swing/ml/78w | deep70, mom6, wlow | CSV off -> parked |
| s_q07w_c52_sm_cheap5_ins2_mom6 | cyan/sm/52w | cheap5, ins2, mom6 | ON |
| s_q07w_c78_sm_deep70_ins2_vix20 | cyan/sm/78w | deep70, ins2, vix20 | ON |
| s_q07w_c78_sm_ins2_mom6_vix20 | cyan/sm/78w | ins2, mom6, vix20 | ON |
| s_q07w_g78_sm_deep70_ins2 | green/sm/78w | deep70, ins2 | ON |
| s_q07w_g52_sm_deep70_ins2_vix20 | green/sm/52w | deep70, ins2, vix20 | ON |
| s_q07w_g78_sm_cheap5_ins2 | green/sm/78w | cheap5, ins2 | ON |
Shared-engine note: batch 5 extends desk3/lazarus_q07.py (batch 4's engine) additively — cyan family, ins2/vix20 filters, cap_band/fired_at key aliases, SYM|1d bar keys, sleeve_id fire binding. Batch 4's exact-SPECS blocker was cured to a subset+distinctness assertion (it would otherwise fail every later Q07 batch by design).

## Batch 3 (LAZ3-1) — Q07 cyan/green tierA & wiki lanes (all CSV ON / Live, 1 slot @ $1,000)
Substitution (all 10): the desk-research fire file `shadow/paper_sleeve/live/sleeve_fires_v1.json` unreachable from this box (V3-SCOPE §3.4); lanes are fire-consumers over the shared `desk3/lazarus_q07.py` engine fed by the desk's sleeve_feed composer producer (`view["fires"]`, tracker ledger + alt-data tags) — the desk's equivalent Tensor bundle/composer product. Fail-closed on absent/stale fires, missing tags, or no QQQ-down day.
Underspecified readings: tierA = tags tier=="A" (or tier_a true); wcov = wiki_cov true (or wiki_views>0); wlow = wiki_low true; wspike2 = wiki_spike2 true or wiki_spike>=2.0 (name's "2" read as 2x spike; catalog says slot count for s_q07w_c52_ml_mom6_wspike2 was not captured — standard 1 slot @ $1,000 adopted from its captured $1,000 budget); mom6 = 6m return >0 (tag mom6/mom6_pct/ret_6m, else 126-session bar return); deep70 = deep70 tag, else price <=70% of trailing high; horizon = calendar weeks (52w=364d, 78w=546d) from entry date; fire age = sessions via QQQ bar dates, calendar-weekday approximation when bar dates are absent; entry price = fire price else last bar close; qty = floor($1,000/price).

| sleeve | family/band/horizon | filters | fidelity risk |
|---|---|---|---|
| s_q07w_c78_sm_tierA_wcov | cyan/small/78w | tierA+wcov | per-lane exit variance (catalog §3.5); readings above |
| s_q07w_c52_ml_tierA_wcov | cyan/midlarge/52w | tierA+wcov | same |
| s_q07w_c52_ml_tierA_wlow | cyan/midlarge/52w | tierA+wlow | same |
| s_q07w_c52_ml_mom6_tierA_wlow | cyan/midlarge/52w | mom6+tierA+wlow | same |
| s_q07w_c52_ml_mom6_wspike2 | cyan/midlarge/52w | mom6+wspike2 | slot count not captured upstream; 1 @ $1,000 adopted |
| s_q07w_c78_ml_tierA_wcov | cyan/midlarge/78w | tierA+wcov | readings above |
| s_q07w_c78_ml_tierA_wlow | cyan/midlarge/78w | tierA+wlow | same |
| s_q07w_c78_ml_mom6_tierA_wlow | cyan/midlarge/78w | mom6+tierA+wlow | same |
| s_q07w_c78_ml_deep70_tierA_wlow | cyan/midlarge/78w | deep70+tierA+wlow | deep70 threshold reading (<=70% of high) |
| s_q07w_g52_sm_tierA_wcov | green/small/52w | tierA+wcov | readings above |

## Lazarus batch 8 — s_mn_* strategy ports (2026-10-24)
Source: CSV rows (producer sleeve_midna, midna_fires_v1.json) + catalog
§4.2 rule table (one line per sleeve) + §5.1 cross-walk. Unlike the
fire lanes, eight of these ten carry a complete computable rule in the
catalog, so they are authored as genuine bar-computing sleeves fed by
the desk bars producer (not fire-consumers); the two whose signal is an
upstream model/pick (moonshot, kronos) are fire-consumers on
lazarus_fire_ingest (view["fires"]) — substitution for the unreachable
midna_fires_v1.json recorded here. All ten CSV status ON; catalog
Shadow for kronos + the three opt_* = paper-tracked only, which v3
(paper-only) satisfies unparked.
| sleeve | catalog rule implemented | underspecification + reading |
|---|---|---|
| s_mn_moonshot | Upstream pick at 1% weight; no stop; out at 78 weeks; 1 slot $1,000 | Pick generation upstream/unreachable: fire-consumer freeze; 78w = 390 sessions; the $1,000 slot IS the 1% weight on the TEST book; fresh fire <=7d else fail-closed |
| s_mn_kronos | Top-4 Kronos forecast names; rebalance on forecast change, min 5-day hold; $2,000 | Model internals upstream: fires carry ranked forecast (rank or score); catalog "2 slots" conflicts with "top 4 names" — named rule wins, 4 x $500; no fresh forecast = hold, no churn |
| s_mn_macd | MACD crosses up / crosses down; 1 slot $1,000 | MACD parameters unstated: classic 12/26/9 on daily closes; multi-name same-day cross: strongest histogram wins |
| s_mn_vwap | Price crosses above/below VWAP; 1 slot $1,000 | VWAP window unstated on a 1D lane: 20-session rolling VWAP (desk's standing daily form, cf. ema_vwap) |
| s_mn_faber | Hold any of five ETFs above 10-month average; exit below; $3,000 | Five ETFs unnamed: classic Faber GTAA-5 (SPY/EFA/EEM/VNQ/AGG); 10-month = 210 sessions; catalog "3 slots" conflicts with hold-any-of-five — hold-all reading, equal $600/ETF |
| s_mn_reversal | Buy last month's worst large caps; monthly rotation/21 sessions; 3 slots $3,000 | Universe = snapshot bars (producer large-cap set), no tickers named; worst = lowest prior-21-session return; exit at 21 sessions held, then refill |
| s_mn_pairs | Distance pairs, spread 2 sd wide; exit on revert to mean; 3 slots $3,000 | Pairs unnamed: desk pairs KO/PEP, XOM/CVX, JPM/BAC; 60-session log-spread z; exit |z|<=0.25 (revert band); $500/leg |
| s_mn_opt_turtle | Turtle breakout in listed options; Turtle exit; $1,000, Shadow | Vehicle unstated: long calls 21-75 DTE strike-nearest-spot (laz8_opt, spread gate 30%); Turtle exit = 10-day low or 2-ATR stop vs entry-day close |
| s_mn_opt_reversal | Reversal in listed options; rotation exit; $1,000, Shadow | Long call on the single worst name (equity form runs 3, options form catalog slots=1); exit at 21 sessions |
| s_mn_opt_pairs | Pairs in listed options; exit spread reverts; $1,000, Shadow | Long put rich leg + long call cheap leg, $500 premium/leg; same z rule/exit as s_mn_pairs |
Fidelity verdict: PARTIAL — every catalog-specified field implemented
and fixture-proven (tests/test_lazarus_batch8_blockers.py, 21 tests);
the readings above are documented, not source-verified, and the two
fire-consumer lanes are UNVERIFIED against real upstream fires (none
reachable from this box).

## LAZ2 — Lazarus batch 2 (2026-10-24): inventory / frozen-rules / moonshot / Q07 cyan-small

Substitution (all 10 lanes): CSV fire files live in the desk-research,
unreachable from this box (V3-SCOPE §3.4). Lanes are fire-consumers:
the 6 inventory/rules sleeves consume the desk's Tensor-bundle-equivalent
fire channel via desk3.lazarus (view["lazarus_fires"]); the 4 Q07 lanes
consume the sleeve_feed composer channel via desk3.lazarus_q07
(view["fires"]). Signal generation stays upstream; desk code does
filters, sizing, stops and time exits. Fail-closed on absent/stale fires.

| sleeve | catalog sketch | missing/underspecified | reading adopted |
|---|---|---|---|
| s_1dgp5 | 1D Green, stocks < $5, QQQ-down rule; no stop, out at 40 sessions; 1 slot $1,000; Live | fire schema for the composer channel | family/price carried on the fire; QQQ-down from fire qqq_red or QQQ bars; price < $5 strict |
| s_rules_1d | 43 frozen Tensor rules, daily, buy at next close; exit at rule horizon + 1 session; 44 slots $44,000; Live | the 43 rules themselves (upstream, per V3-SCOPE §3.5 freeze route) | pure fire-consumer: per-fire horizon_sessions, exit at horizon+1 (engine horizon_plus_one); default horizon 21 (+1) when a fire omits it |
| s_rules_1w | frozen rules weekly + QQQ-down; exit horizon + 1, 15% stop; 6 slots $6,000; Live | same as s_rules_1d | same freeze; default horizon 26 (+1) |
| s_1wg_small | 1W Green tier-A small caps; 15% stop, else 52 weeks; 2 slots $2,696; Shadow (CSV off => parked) | 52 weeks in sessions | 252 sessions (batch-1 1w convention); tier/cap enforced when the fire carries them |
| s_moonshot | 1W Cyan, price <= $14.94, deep 60-day pullback, held as 10 names at 1% weight; 15% stop, else 52 weeks; $2,581; Shadow (parked) | catalog table says "2 slots" while its text says "held as 10 names at 1% weight" — contradictory | 10-name basket governs (slots=10, per-name $258.10); deep60 = explicit fire tag (deep60/deep_pullback60), fail-closed without it |
| s_1wsw_stress | 1W Swing, stocks < $5, deep pullback, VIX 20+; 15% stop, else 52 weeks; 1 slot $1,335; Disabled, "no live source yet" (parked) | "deep pullback" depth and the missing live source | deep = fire tag deep/deep70; VIX from fire tag, fail-closed when absent; parked until a source exists — fidelity UNVERIFIED against live fires |
| s_q07w_c52_sm_cheap5_wcov | Q07 Cyan small, cheap5 + wiki coverage, H52; Live | — (family rule §4.1 complete) | shared Q07 engine reading: cheap5 = price < $5, wcov = wiki_cov tag |
| s_q07w_c52_sm_deep70_wcov | Q07 Cyan small, deep70 + wiki coverage, H52; Live | deep70 depth definition | engine reading: explicit deep70 tag, else price <= 70% of trailing high in bars |
| s_q07w_c52_sm_tierA_wcov | Q07 Cyan small, tierA + wiki coverage, H52; Live | — | tier == "A" (or tier_a tag) + wiki_cov tag |
| s_q07w_c78_sm_deep70_wcov | Q07 Cyan small, deep70 + wiki coverage, H78; Live | as c52 deep70 | as c52 deep70, horizon 78 weeks |

## ASTER-B10 — etf batch 10 (2026-10-24)
Source status: staged archive (~/.scratch-ausar-archive) ABSENT on this box at build time — sleeves built from the TSV spec (education_* fields, exact per-row parameters) + ASTER-BUILD-MAP §6 etf rows, the fallback the map prescribes for missing pieces. FIDELITY DIFFED (HARDEN batch-1, 2026-10-24): archive r19_etf.py read directly at ~/workspace/.scratch-ausar-archive/handoff-20261024. One discrepancy found and cured: LEADER1 eligibility/scoring — v3 ranked >=127-bar symbols by simple return; source _scores requires the 252-session window and scores log(close[-1]/close[-127]). Cured in desk3/aster_etf.py (eligibility >=252, log score); remaining readings (monthly entry-month, NAV, uncapped gross 1.5, buy-hold no-exit) stand as the v3 snapshot translation, fixture-proven. Verdict upgraded: source-diffed, PARTIAL only for live OPRA/quotes producer proof.
Assumptions recorded: (1) LEADER1 basket = etf_rules universe from build-map §4 [QQQ,SPY,SMH,XLB,XLC,XLE,XLF,XLI,XLK,XLP,XLRE,XLU,XLV,XLY]; score = 126-session return close[-1]/close[-127]-1, ties alphabetical. (2) Monthly sleeves act on initial allocation or when a holding's entry month != session month (no sleeve state store in v3 adapter contract). (3) Account net value = extra account_value/net_value else slice capital $10,000. (4) Sizing price = last completed bar close; IEX quotes declared as input but not required (bars producer is the fed path). (5) Buy-and-hold sleeves have NO designed exit (spec: holds fixed shares, no target/calendar exit) — proven by fixture (price halved + new month => no intents); their "exit" is operator liquidation only. (6) gross 1.5 targets emitted uncapped ($15,000 on $10k slice); dispatcher BP check governs.

## ASTER-B13 (batch 13, TSV 126-135) — TSV-as-spec (staged archive absent on this box)
- `aster_link_nfs_norm_vol` (R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_VOLUME1PCT): entry = completed 4h close > prior-20 high + actually-available funding < 0; qty = min(1% of preceding 4h volume, slice cash/price); exits = funding >= 0 (normalization) OR deadline. ASSUMPTION: normalization max deadline = 96h (longest family deadline; TSV names only "the installed maximum deadline"); deadline fires without funding (TSV rule). Declares input `funding` — no v3 funding producer exists yet, so the sleeve is visibly UNFED in the registry, never fake-fed.
- Tensor BETA/C1 (TSV 127-135): consume canonical Tensor v698 products via the v3 Tensor bundle fire channel (engine untouched). C1 gates exactly per TSV: buy-cyan, price<=5, ret60>=31, vol20>=0.07, ADV>=$2M. ASSUMPTION CORRECTED (HARDEN batch-1, 2026-10-24): the TSV reading cool<1/hot>=1 was WRONG at atr_ratio==1.0; archive r19_tensor.passes is source-exact (atr_ratio<=1)==(vol=='cool') — cured in desk3/aster_batch13.py, matching batch 14. Exit = 52nd-week deadline modelled as 260 sessions; no stop/target per TSV; proven by fixture (a -75% move at session 10 does NOT exit). ASSUMPTION: delay/reserve wait = fire age >=1 calendar day (session granularity unavailable in fixtures); reserve sleeves additionally sell the QQQ reserve leg (sized to the $400 ticket) when a qualified entry fires, per TSV reserve exit rule. Ticket $4,000->$400 on the $10k slice; 25 slots; duplicate-symbol refusal.
- Proof: tests/test_aster_batch13_blockers.py 14/14 GREEN, fail-first proven (13 errors with engine removed); E2E round-trip to flat on FakeBroker via Dispatcher for aster_tensor_c1_cash_all_25 (Tensor family) and fixture exits for the crypto family.

## ASTER-B2 — pead / core_reserve / recovery RSI2 (2026-10-24)
Source: archive r19_options.py (recovery_signal/rsi2, build_pead_event/pead_signal, _select_contracts, _entry_intent, _exit_intents, core QQQ init) + options_rules.json books. Ported faithfully: RSI2 smoothing verbatim; 200-session SMA gate; PEAD surprise <= 20th pct of >=200 priors, spot>=5, mean20 DV>=$1M, entry at event+3 sessions, PUT; DTE/delta bands per book; debit/premium caps per book; exits = planned hold (pead 10, recovery/core 5), pre-expiry guard, touch-only +2% recovery exit (FIXED sleeves proven NOT to touch-exit).
Assumptions recorded: (1) option fee $0.65/contract/leg — source reads snapshot option_fees.per_contract_per_fill, which no v3 producer supplies yet. (2) PEAD event fields (surprise/threshold/spot_at_signal/mean20_dollar_volume/entry_session) are producer-precomputed equivalents of build_pead_event outputs; engine also accepts prior_surprises and computes the source quantile itself. (3) Core QQQ leg: source emits once at 95% of capital and has NO exit rule for it — preserved as-is (buy-hold core), not an oversight. (4) Session counting for exits uses position sessions_held / bar-count from opened_at. Verdict: PARTIAL (fixture-proven; live OPRA/earnings producers unwired => UNFED).

## ASTER-B6 — Aster batch 6 (2026-10-24): NFS ADA x9 + absorption ENJ x1
Archive staged tree ABSENT at build time — built from TSV spec. FIDELITY DIFFED (HARDEN batch-1, 2026-10-24) against r19_crypto.py at ~/workspace/.scratch-ausar-archive/handoff-20261024: NO code discrepancy — 96h deadline for all non-fixed16 policies source-confirmed (exit_due_at rule), normalization_failure condition + execution delay confirmed under v3 bar-start convention. Verdict upgraded: source-diffed; PARTIAL only for the unwired funding producer (UNFED by name).
- Entry NFS (TSV-verbatim): completed 4h close > highest high of prior 20 bars + observed funding < 0; missing funding refuses (never assumed).
- Entry absorption (TSV book-5 logic verbatim): shock bar vol>2xEMA20 incl., close<open, close<EMA50 incl.; next bar bullish close > shock midpoint; >=300 bars.
- ASSUMPTION (recorded): structural policies (lost_breakout / normalization / normalization_failure) carry the installed 96h maximum deadline (TSV names only "the installed maximum deadline"); normalization_failure delay = signal bar start +4h bar +4h delay.
- Sizing: fullcash = slice cash net 10bp fee; volume1pct = min(fullcash, 1% of preceding 4h bar volume in base units). Whole-unit floor applied: v3 dispatcher rejects fractional qty for ADAUSDT/ENJUSDT (not fractional symbols).
- Inputs (bars, funding, positions): funding producer (Binance fundingRate capture, map §4) not yet wired => sleeves visibly UNFED in registry, never fake-fed.

## ASTER-B14 (batch 14, TSV 136-145) — source-exact from archive r19_tensor
Archive WAS present this pass at ~/workspace/.scratch-ausar-archive/handoff-20261024 (other batches looked under ~/.scratch); passes()/evaluate() in source/backend/r19_tensor.py + tensor/RULES.json weekly books read directly.
- G4 gates exactly per passes(): buy-green marker, native_close<=10, depth60>=70, ret60>=0, vol20>=0.09, dv20>=2e6. C1: buy-cyan, close<=5, ret60>=31, vol20>=0.07, dv20>=2e6.
- Volatility split SOURCE-EXACT: (atr_ratio<=1)==(vol=='cool') — cool includes atr==1.0, hot is atr>1. This differs from batch 13's recorded assumption (cool<1/hot>=1); batch 14 follows the source code.
- Capital modes per evaluate(): entry session after signal_end, +1 session for delay/reserve; reserve sells QQQ leg sized to the ticket before entry. Tickets: source $10,000 (10 slots)/$4,000 (25 slots) on $100k book -> $1,000/$400 on $10k slice.
- ONLY designed exit: 52-week scheduled exit (position exit_at deadline; modelled as sessions_held>=260 like batch 13, plus explicit exit_at honoured). No stop/profit cap per RULES risk text — fixture proves a -75% move at session 10 does NOT exit.
- Inputs tensor/bars/positions via tensor_bundle producer (Tensor ENGINE untouched, consumed at sleeve layer). Fidelity PARTIAL only in that the live Tensor bundle fire shape is the v3 ingest contract, as in batch 13.

## ASTER-B8 — batch 8 (2026-10-24): NFS ENJUSDT x7 + ETF x3
Source: archive r19_crypto.py / r19_etf.py + crypto_rules.json /
etf_rules.json + TSV education fields (map batch 8, TSV 76-85).
Engine desk3/aster_batch8.py; adapters3/aster_enj_nfs_* + aster_etf_*.
- Crypto UNFED by design: the live perp funding feed is the named
  missing piece (map §4); sleeves declare inputs (bars, funding,
  positions) and no v3 funding producer is registered, so the
  registry marks them UNFED — never fake-fed.
- Readings: (1) the archive's 4h entry delay + quote-receipt/depth
  machinery is the source runtime's execution layer — the v3 sleeve
  evaluates the completed signal bar, the dispatcher takes the next
  print (shared with batches 6/13). (2) Structural policies
  (lost_breakout / normalization / normalization_failure) carry the
  installed 96h maximum deadline per TSV orders text. (3) fullcash
  sizing = slice cash x (1 - 10bp fee) / price. (4) normalization_
  failure execution delay: trigger bar end + 4h. (5) ETF NAV = slice
  capital / extra account_value (batch-10 reading); monthly due =
  flat, rebalance_due, or holdings' entry month != session month.
- ETF gross 1.5 (core25_m150): target $15,000 on the $10k slice is
  preserved in the sleeve; the dispatcher BP check governs fills.
- Verdict: PARTIAL — rules fixture-proven (28 blockers); live funding
  feed + live paper proof are later phases.

## ASTER-B9 — batch 9 (2026-10-24): R19 ETF leader family x10 (TSV 86-95)
Source: archive READ DIRECTLY this pass at ~/workspace/.scratch-ausar-archive/handoff-20261024 — source/backend/r19_etf.py (select/_scores/_evaluate) + source/strategies/r19/etf_rules.json books. Engine desk3/aster_etf_b9.py (batch-scoped; batch 10's desk3/aster_etf.py serves different sleeve ids).
- Selection SOURCE-EXACT: score = log(close[-1]/close[-127]) over the last 252 sessions; eligibility >=252 sessions; ties alphabetical; EXSMH1 drops SMH before ranking; INTERVAL* uses the archive interval rule verbatim (robust leader iff its low beats all other highs; else incumbent if possible; else QQQ; secondary eligible set != primary set => refuse). CORE25 weights: leader 0.25 / QQQ 0.75.
- DRIFT1 + INTERVAL_DRIFT1: selected == incumbent (largest held by value, or position metadata) and held => NO intents (unchanged-share holding, archive `retain`).
- Targets: floor(weight x gross x NAV / last close), NAV = slice cash + held value at last close; gross NEVER capped in-sleeve (M150 = $15,000 target on $10,000 slice; dispatcher BP governs).
- Monthly: positions carrying signal_month == latest bar month do not rebalance (reading of archive last_completed_signal, carried on position metadata — same convention as batch 8/10 entry-month readings). Sell-then-settle: any above-target holding => only sells this eval (archive MONTHLY_TARGET_SELL_THEN_SETTLE). No stop/target by design; the designed exit is the next monthly selection.
- Window: 09:35-09:40 ET enforced when a clock time is known (aware stamps converted to ET, naive read as ET, date-only ungated) — archive _calendar.
- UNFED by design: INTERVAL x6 declare bars_secondary (YAHOO histories); no v3 producer produces it, so the registry marks them UNFED — never fake-fed. Single-source x4 are FED on bars+positions.
- Verdict: PARTIAL — rules fixture-proven (tests/test_aster_batch9_blockers.py, 11 tests: entries incl. uncapped M150 qty, EXSMH exclusion + leader control, interval refusal/robust/ambiguous->QQQ, CORE25 75/25, drift retain x2, rotation sell-then-settle, same-month hold, window + <252-history refusals, config/INPUTS, FakeBroker+Dispatcher E2E entry->rotation->flat); live paper proof is a later phase.

## ASTER-B7 — R19 crypto ENJUSDT batch 7 (2026-10-24)
Source status: archive READ directly (~/workspace/.scratch-ausar-archive/handoff-20261024/source/backend/r19_crypto.py, strategies/absorption/signals.py, strategies/r19/crypto_rules.json) — source-based port, not TSV-only. 10 sleeves, books 66-75 (SM ids R19_ENJUSDT_* per ASTER-BUILD-MAP): absorption_base fixed16 volume1pct; absorption_negative_funding fixed16 fullcash+volume1pct; absorption_nonnegative_funding fixed16 fullcash+volume1pct; breakout_base fixed16 fullcash+volume1pct; negative_funding_squeeze fixed16 fullcash+volume1pct, fixed96 fullcash. $10,000 slice each.
- Absorption: signals.py EMA recurrence (vol EMA20, close EMA50, current-inclusive), shock at last-but-one bar, confirmation at last bar, >=300 completed bars (source indicator_count>=300).
- Funding filters exactly per source _signal: neg families require observed rate <0; nonnegative requires >=0; missing funding never assumed 0; breakout_base/absorption_base are funding-off controls and do NOT declare the funding input (they cannot be vetoed by a funding outage, per source).
- ASSUMPTION (runtime translation, cf. B6): source entry_delay 4h + 300s window + observed quote/depth/last-trade clocks and step-size lot rounding are producer/dispatcher-layer mechanics; the sleeve evaluates the latest completed-bar signal on its snapshot and sizes off the signal close (fullcash = cash/(price*(1+10bp fee)); volume1pct = min(fullcash, 1% of preceding 4h bar volume)).
- Funding sleeves declare ("bars","funding","positions") and land UNFED until the v3 Binance funding producer (ASTER-BUILD-MAP §4) lands — never fake-fed. Controls declare ("bars","positions").
- PLATFORM NOTE (open, dispatch layer, not a sleeve defect): the v3 intent validator treats only USD/-USD symbol forms as fractional, so source-faithful fractional fullcash quantities for *USDT symbols are rejected qty_not_whole at dispatch; whole-qty arms (volume1pct fixtures) round-trip on the FakeBroker. Named here for the dispatcher/symbol-mapping owner.
- Exits: fixed deadline only (this batch's designed exit); deadline fires with bars/funding missing, per source.

## ASTER-B11 — batch 11 (2026-10-24): SPY etf x3 + LINKUSDT crypto x7
Source status: staged archive FOUND on this box at ~/workspace/.scratch-ausar-archive/handoff-20261024 (siblings looked in ~/.scratch-ausar-archive). Rules source-verified against r19_etf.py+etf_rules.json and r19_crypto.py+absorption/signals.py+crypto_rules.json; fidelity HIGH for rule math, PARTIAL only for the v3 snapshot translation below.
- ETF: SPY_HOLD_FULL (BUY_HOLD, gross 1.0, {SPY:1}, no designed exit — operator liquidation only, proven by fixture); SPY_MONTHLY gross 0.98 / 1.5 ({SPY:1}). Reuses the batch-10 desk3/aster_etf.py engine (specs registered additively by desk3/aster_batch11.py); inherits its readings: 09:35-09:40 ET window, whole shares floor(gross*equity/price), sells before buys, monthly = initial allocation or holding entry-month != session month, gross 1.5 emitted uncapped (dispatcher BP governs).
- Crypto (desk3/aster_b11_crypto.py): absorption = prior-bar bear shock (vol>2*EMA20 incl., close<open, close<EMA50 incl.) + current-bar confirm (close>open, close>shock midpoint), >=300 bars; negative variant requires observed funding<0, nonnegative requires funding>=0, base is the funding-OFF control (funding never gates, per archive _signal). breakout_base = close>prior-20 high, funding never gates. Exit for all 7 arms = fixed16 deadline only (archive exit_policy fixed16; deadline fires with bars/funding missing). Sizing: fullcash = slice cash net 10bp fee; volume1pct = min(fullcash, 1% of preceding bar volume).
- Assumptions (snapshot translation, same reading as batch 6): (1) archive's 4h entry delay + 5-min window and quote/depth gates are runtime-form, translated to signal-bar entry on the v3 snapshot (bars/funding/positions producers); (2) archive known_funding settlement/receipt chronology is the funding producer's contract — the sleeve consumes the producer's latest rate value; funding-gated sleeves are UNFED until that producer lands, never fake-fed.

## ASTER-B3 — Aster batch 3 (2026-10-24): recovery RSI2 vertical x4, tensor_leaps x2, recovery VWAP20 long x4 (TSV 26-35)
Source: staged archive `source/backend/r19_options.py` +
`source/strategies/r19/options_rules.json` books (read directly;
204-exact verified archive). Engine desk3/aster_batch3.py ports
recovery_signal (archive Wilder recursion verbatim), _select_contracts,
_entry_intent sizing/caps, _exit_session/_session_exit_due and the
_exit_intents rule set. Exit-day reading: archive sessions[hold-1]
with sessions[0]=entry session (entry day = session 1, per the TSV
exit summary) => 5-session exit lands on the Friday of the entry
week for a Monday entry.
| sleeve | book | fidelity |
|---|---|---|
| aster_rec_rsi2_vertical_fixed_a/_b | OPT_RSI2_VERTICAL_FIXED_A/B | FAITHFUL — RSI2<10 + close>SMA200, vertical debit/width caps 0.60/0.45, fixed 5-session exit |
| aster_rec_rsi2_vertical_touch_a/_b | OPT_RSI2_VERTICAL_TOUCH_A/B | FAITHFUL — touch exit bid>=entry_spot*1.02 (fresh sip) else deadline |
| aster_tensor_leaps_a/_b | OPT_TENSOR_LEAPS_A/B | FAITHFUL — qualified native G4 event bridge consumed at sleeve layer; DTE 540-720, delta 0.6-0.8, premium/spot<=0.5, 365-day checkpoint + original G4 deadline/event exits |
| aster_rec_vwap20_long_fixed_a/_b | OPT_VWAP20_LONG_FIXED_A/B | FAITHFUL — close<=0.98*VWAP20 typical-price + close>SMA200, long call, premium/spot caps 0.025/0.015 |
| aster_rec_vwap20_long_touch_a/_b | OPT_VWAP20_LONG_TOUCH_A/B | FAITHFUL — as above + touch exit |
Assumptions recorded (exact): (1) Fee schedule: archive reads
snapshot option_fees.per_contract_per_fill; fixtures supply it
($0.65). A fee-less snapshot falls back to the books' fee_bps=15 on
the package debit — a named constant, recorded in intent metadata
(per_leg_fee); the live desk stays UNFED regardless. (2) Sizing
equity/cash = the $10k slice (map §3); the archive's
initial*0.05-outstanding cap uses the slice as initial. (3) B-tier
($50) risk budgets afford a package only when debit+fees <= ~$49 —
a direct consequence of source sizing + the slice convention
(source B books carried $500 on $100k); proven, not patched over.
(4) Unpriceable compulsory exits emit no intent (v3 intents carry
no blocker channel); the obligation remains visible via the held
position in the terminal/journal, matching earlier batches' posture.
UNFED: producers options_chain (OPRA), quotes, tensor G4 events do
not exist in v3 yet — registry marks all 10 UNFED by name.
Verdict: PARTIAL — fixture-proven faithful port; live proof awaits
the OPRA/G4 producers and an RTH session.

## ASTER-B12 — Aster batch 12 (2026-10-24): breakout_base LINK vol + NFS LINK x9
Source-verified against the staged archive (~/workspace/.scratch-ausar-archive/handoff-20261024): r19_crypto.py (_signal/evaluate) + crypto_rules.json. Rows TSV 116-125, SM ids R19_LINKUSDT_BREAKOUT_BASE_FIXED16_VOLUME1PCT + R19_LINKUSDT_NEGATIVE_FUNDING_SQUEEZE_{FIXED16,FIXED96,LOST_BREAKOUT,NORMALIZATION_FAILURE,NORMALIZATION}_{FULLCASH,VOLUME1PCT} (normalization fullcash only in this batch; volume arm is batch 13's aster_link_nfs_norm_vol).
- Entry: completed 4h close > highest high of prior 20 bars; NFS additionally latest actually-observed funding < 0 (archive known_funding: settled+received before decision, <=12h old at signal close — the producer input carries the observed rate). breakout_base is the funding-OFF control (archive passes funding=None): it declares NO funding input and enters on positive/missing funding, proven by fixture contrast with NFS refusals on the same views.
- Exits: fixed16/fixed96 deadlines from entry; structural arms carry the archive's installed 96h deadline (candidate exit_due = entry_due + 96 for every non-fixed16 policy — source code, not an assumption) and it fires with bars/funding missing. Structural triggers (archive): lost_breakout close < stored breakout level; normalization funding >= 0; normalization_failure funding >= 0 AND close < lowest low of prior 3 bars; executable no earlier than trigger-bar close + 4h (archive execute_at) — fixtures prove both the fire and the not-before-delay refusal for every structural arm.
- Sizing translations (established desk readings, batches 6/11): fullcash = slice cash net of 10bp fee (archive: cash/(ask*(1+fee)) — the net-of-fee form differs by <0.2% and is kept for cross-batch consistency); volume1pct = min(fullcash, 1% of the preceding 4h bar's volume) (archive: volume of the entry interval following the signal bar; snapshot form uses the bar preceding the signal bar). Shared primitives (_bars/_funding/_now/_breakout) imported from the batch-11 engine — one source of truth.
- Inputs: NFS (bars, funding, positions); breakout (bars, positions). No v3 funding producer is wired yet => NFS sleeves land visibly UNFED, never fake-fed. Fractional USDT qty: desk3/models.py now accepts bare USDT spot pairs as fractional (landed in a parallel batch and exercised by this batch's E2E blockers).
- Proof: tests/test_aster_batch12_blockers.py 27/27 GREEN, fail-first proven (25 failed pre-build / with engine removed); FakeBroker E2E round-trips to flat for BOTH families (NFS fixed16 fullcash, breakout fixed16 volume1pct).

## ASTER-B15 — Aster batch 15 (2026-10-24): G4 hot/reserve/red-timeout + timing cloud/hourly/overnight

Source: staged archive `source/backend/r19_tensor.py` (G4 `passes()`,
`evaluate()`), `source/backend/r19_timing.py` (`hourly_signal`,
`cloud_signal`, `overnight_signal`, `evaluate()`), and
`source/strategies/r19/tensor/RULES.json` books R19_TENSOR_G4_HOT_DELAY_25,
R19_TENSOR_G4_HOT_RESERVE_25, R19_TENSOR_G4_RED_TIMEOUT_25,
R19_TIMING_CLOUD_{BASE,AGGRESSIVE}, R19_TIMING_HOUR_FLOOR{0,1}_DELAY{0,1},
R19_TIMING_OVERNIGHT_25BP. Engine: desk3/aster_batch15.py; adapters3
wrappers; $10,000 slice (G4 ticket $400, timing notional/risk fractions
on the slice). Tensor ENGINE untouched.

| sleeve | reading adopted |
|---|---|
| aster_r19_tensor_g4_hot_delay_25 | G4 passes(): buy-green, close<=10, depth60>=70, ret60>=0, vol20>=.09, dv20>=2e6, hot = atr_ratio>1; entry 2nd session after signal week (delay=1); ticket $400; ONLY exit = 52-week scheduled exit (archive: no stop/target) |
| aster_r19_tensor_g4_hot_reserve_25 | as delay, plus archive reserve mode: weekly idle-cash QQQ purchase at first session open, QQQ funding sale the session before entry sized to the ticket shortage |
| aster_r19_tensor_g4_red_timeout_25 | wait up to 5 sessions after signal: enter next session after a QQQ red day with symbol close <=1.02x signal close, else timeout entry after the 5th session; wait expires at the 6th session |
| aster_r19_timing_cloud_base / _aggressive | archive cloud_signal verbatim (hourly EMA34>EMA50 last 3; 10m EMA5/12 frozen-cloud reclaim episode; stop = episode low - 0.1 ATR; target = prior-session high; entry refused when target < 2R); exit_at = min(+100min, 15:50 ET); base risk .0025/notional .1, aggressive .005/.2 |
| aster_r19_timing_hour_floor{0,1}_delay{0,1} | archive hourly_signal: v625 swing confirmed, score>=8, no bearish conflict, stop<close<target, TRANSITION filters, delay-bar geometry-death check, stop floor = min(native stop, entry - floor*ATR14); exits stop/target/20-bar deadline |
| aster_r19_timing_overnight_25bp | archive overnight_signal: 12:30->14:30 ET return >= 80th pct of prior 126+ sessions (last 252), entry window 15:30-15:35 ET, exit at next session open; fee_bps 25 |

Assumptions recorded (exact):
1. G4 features/markers arrive as `tensor_fires` (desk Tensor bundle
   product, the archive's the desk_v615 weekly analysis); the sleeve
   re-applies `passes()` thresholds itself. Sessions come from the
   snapshot session list (archive `calendar_sessions` equivalent).
   The 52-week exit fires on the exit session date (archive: that
   session's close minus 5 min — the v3 sleeve has no intraday clock
   for this daily book; same session, documented).
2. Reserve fill-confirmation: the archive reconciles the QQQ reserve
   order against the ledger on later evaluations; the sleeve marks
   the reserve week once a QQQ position is read back (or the week
   passes) — same observable states, no double-buy.
3. Hourly swing geometry is consumed via the `timing_signals` input.
   NO v3 producer emits it yet, so the four hourly sleeves land
   visibly UNFED (declared in INPUTS + config; blocker
   test_hourly_unfed_by_producer_absence pins this) — never fake-fed.
4. Cloud prior-session high = last completed daily bar high in the
   snapshot; the archive's split-transform adjustment of that high is
   not ported (no intraday binding transforms in the v3 snapshot).
5. Overnight "full session" gate: the archive requires a 16:00 ET
   close in the calendar; the v3 session list carries regular
   sessions only, so listed weekday sessions are treated as full.
6. Quotes: the archive demands a <=2s native quote; v3 views carry no
   quote-age stamp, so the sleeve uses the view quote when present
   and the last completed bar close otherwise (never invents a price).

Fidelity verdict: PARTIAL — every archive rule above is implemented
and fixture-proven (tests/test_aster_batch15_blockers.py, 36 tests,
fail-first proven); hourly lanes UNFED until a timing_signals
producer lands, and live-fire fidelity is UNVERIFIED (no live
Tensor bundle fires reachable in fixtures).

## ASTER-B5 — Aster batch 5 (2026-10-24): public RSI2 + R19 ADAUSDT spot (10 sleeves)
Sources (archive, hash-verified at intake): r19_crypto.py (evaluate/
_signal/known_funding), absorption/signals.py (Decimal EMA absorption),
crypto_rules.json (UTC 4h, entry delay 4h, entry window 300s, fee
10bp/side, arms fullcash/volume1pct), public_source_sleeves.py
tomazetti_rsi2 + TOMAZETTI_RSI2.pine, TSV params (book 46 window
2009-01-01..2030-12-29 ET-stamped, stop disabled).
Engine: aster_sleeves/_common.py; thin sleeves aster_sleeves/<id>.py;
registry desk3/aster_b5.py; slice $10,000 standard (map §3).
Translations/assumptions (exact):
- Entry delay: archive enters 4h after the signal bar closes inside a
  300s window. v3 bar translation: signal read on the second-to-last
  completed 4h bar; the last completed bar IS the entry interval (its
  volume supplies volume1pct, as the archive's prior-entry-interval
  rule); entry fires only 0-300s after that bar closes.
- Sizing price: entry interval's close (archive sizes on the fresh
  ask at due time; quote/spread/last-trade transport gates are the
  v3 dispatcher's, not the sleeve's). RSI2 sizing: floor(cash/close),
  no fee deduction (no fee_bps in the book-46 params; SPOT100 = full
  available cash). R19 sizing includes the 10bp fee in the divisor.
- Quantities floor to whole ADA (v3 intent contract: fractional qty
  only for fractional-symbol forms; ADAUSDT is not one) — conservative
  reading of the archive step_size flooring.
- Funding: archive known_funding ported (settled<=signal close,
  settled<=received<=now, <=12h old, observed_public_endpoint). The
  funding producer (Binance fundingRate capture, map §4) is NOT yet a
  v3 producer: the 5 funding-conditioned sleeves declare `funding`
  and land UNFED live, never fake-fed. Missing funding at evaluate()
  refuses (never assumed zero — book 51's explicit rule).
- Fixed-16 exit: deadline = position exit_due_at if carried, else
  opened_at+16h; fires with no bars/funding present (archive rule:
  deadline remains active through missing data). A position with no
  saved deadline/opened_at never gets an invented exit.
- RSI2 exit is the recipe close (close>SMA5) only; stop disabled in
  source and here. RSI2 entry also enforces the archive 300s
  decision window after the last completed hourly bar.
Per-sleeve verdict: PARTIAL-faithful — every archive rule implemented
and fixture-proven (tests/test_aster_b5_blockers.py, 13 tests);
live proof awaits the funding producer (5 sleeves UNFED by design)
and an RTH/24h paper session read-back.

## ASTER-B1 — Aster batch 1 (2026-10-24): public_recipe / tensor recovery / absorption / native_trend / opening_gamma

Source: staged archive at ~/workspace/.scratch-ausar-archive/handoff-20261024/source
(read-only; located via ~/workspace/.scratch-ausar-archive — the intake
blocker's ~/.scratch-ausar-archive path does not exist on this box).
Engine: desk3/aster_batch1.py; adapters3/aster_*.py; $10,000 slice each.

| sleeve | archive source | fidelity |
|---|---|---|
| aster_rsi2_1d | trader_signals.py trader_rsi2_public_v1 + rules-v1.json | FAITHFUL: Wilder RSI2<=5, close>sma200, close<sma5; exit close>sma5 or 10 bars; NO initial stop; 15-ETF universe; min 252 bars; sizing cap min(.1eq,.01DV20,cash) whole shares (trader_runtime) |
| aster_squeeze_1d | trader_signals.py trader_squeeze20_public_v1 | FAITHFUL: BB20/KC20 release, momentum>0 rising (linreg endpoint), prior-20-high break; exits close<ema20 / momentum<=0 / initial 2ATR stop / 20 bars; risk cap floor(.005eq/2ATR) |
| aster_tensor_h1_recovery / aster_tensor_w1_recovery | tensor_strategy.py StateRepairPolicy R11 + tensor_engine.py panel shape | FAITHFUL at the sleeve layer: 4-bar panel, repair>=2, >=2/7 channels increasing (adjacent-transition reading of the R11 policy, superseding the TSV's first-vs-last phrasing), total_votes==7 both ends, close>=5, DV20>=$1M, ATR>0, excluded {SPY,QQQ,B,GOLD}, min 234 source bars when bar_index present, cooldown 20 native bars, exit entry+20, sizing floor(min(.1eq,.01DV20,cash)/(px*1.001)), rank repair+.01bal+.001clip(OBV/vol,-10,10). Consumes view["tensor"] Tensor-bundle products; ENGINE untouched; no tensor producer output => UNFED |
| aster_abs_enj_4h / aster_abs_link_4h | absorption/signals.py advance() + rules-v1.json | FAITHFUL: Decimal EMA(20 vol / 50 price, current-inclusive), shock = vol>2*EMA & bearish & close<EMA50, confirmation next bar bullish & close>shock midpoint; 300-bar warmup; sizing full slice cash incl. 10bp fee (qty=cash/(px*1.001), fractional); exit at confirmation completion +16h, never resets (state-persisted deadline; opened_at+16h fallback) |
| aster_native_btc_eth_sma200 / aster_native_eth_sma200 | prospective_native.py + prospective_native_math.py | FAITHFUL: gate close strictly > inclusive SMA200 (needs 200 closes); weights BTC .5/ETH .5 and ETH 1.0; fee 0.002 fee-funded rebalance() bisection ported (single-asset book solves the same equation on its own dimension); sells before buys; fractional Coinbase-product quantities |
| aster_open_gamma_a / aster_open_gamma_b | r19_options.py opening_gamma + options_rules.json OPT_OPENING_GAMMA_A/B | FAITHFUL: causal R5 prior-afternoon + completed first-5min (return<0) + break below first-5min low; _opening_event_clocks causality incl. session identity and 5s break-quote freshness; window 09:35<=ET<09:45; long puts; A: DTE 0-2, premium cap 2.5%, risk 2.0% ($200); B: DTE 7-14, cap 1.5%, risk 0.5% ($50); delta 0.50-0.65, contract pick (expiry, |delta-mid|, |strike-spot|, symbol) per _select_contracts; exit flat 10:00 ET entry day, overdue stays due, expiry obligation earlier |

Assumptions recorded (exact):
- Trader per-order fee in trader_runtime sizing is a desk policy value not
  in the archive rules; v3 uses fee=0 in the (cap-fee)/price share count.
- Opening-gamma per-contract fee: archive reads snapshot
  option_fees.per_contract_per_fill (not in the rules book); v3 models it
  as fee_bps 15 on premium (per = debit*1.0015) per the book's fee_bps.
- Opening-gamma spot for the premium cap comes from the snapshot quotes
  mid when present, else the event's observed_break_price.
- Native dust threshold $0.01 on rebalance deltas (archive tolerance is
  an accounting invariant, not a trade threshold).
- Tensor/opening/absorption holding clocks prefer explicit position
  fields (bars_held/sessions_held/entry_bar_index/opened_at), then
  bar-count after opened_at, then the sleeve state file.
Fidelity verdict: GREEN on fixtures for all 10 (tests/test_aster_batch1_blockers.py,
29 tests); live producer wiring for tensor bundle / opening events is the
named missing piece — those sleeves are UNFED until their producers land.

## ASTER-B4 — recovery VWAP20 vertical / xsp_pcs / public_recipe spot (2026-10-24)
Source: archive r19_options.py (recovery_signal VWAP20 arm, select_xsp_legs/_xsp/_weekly_atr14/_xsp_digital, _exit_intents) + options_rules.json books OPT_VWAP20_VERTICAL_{FIXED,TOUCH}_{A,B} (DTE 14-21, delta 0.5-0.6, hold 5, A risk .02/max_debit_width .6, B risk .005/.45) and OPT_XSP_{CALM,GRADED}_{A,B} (risk .03/.01, no DTE/delta in book — snapshot-supplied, per map §4); public_source_sleeves.py source_features ai_volume/iu_body + Pine sources. Engine desk3/aster_b4.py reuses the batch-2 verified _select_contracts/_entry_intent translation for the recovery books.
- VWAP20 signal verbatim: >=200 completed sessions, close > SMA200 and close <= 0.98 * VWAP20 (typical price, last 20 sessions). Exits: planned 5-session, pre-expiry guard, touch-only +2% underlying recovery (FIXED books proven NOT to touch-exit).
- XSP verbatim: first-session-of-week 10:00-10:05 ET window; prior-week state must end at the previous session; >=26 prior weekly digitals; digital from adjacent-put mids; skip at >= p75 (both structures) and >= median (calm); strike targets prior_close - weekly-ATR14 * (1.0/1.236 short; long exactly 5 below short for calm, 1.618/1.786 factor for graded); sizing min(risk/max-loss, cash/width, displayed sizes), max loss = width - credit + 2 leg fees. ONLY exit = European cash settlement at weekly PM expiry (settle-flagged exit intent; no price stop exists in source/TSV). Consequence recorded: on the $10k slice the B books (1% = $100) refuse whenever max loss > $100 (proven: loss $251.30 refuses, $81.30 fills) — that is the source sizing rule applied to the slice, not a defect.
- public_recipe: SPOT100 long-only adaptation per TSV — ai_volume bearish counterpart and iu_body bearish strong-body are EXITS, never short entries (spot, no leverage); LINK exit_bars=5 counted in completed bars held; ENJ trailing stop = source ATR14 x2 geometry reconstructed deterministically from post-entry bars (starts avg-2*ATR, ratchets close-2*ATR, tested on the last bar's low against the stop formed by prior bars). ASSUMPTION (recorded): bar interval = 4h completed bars (the v2 fwd sleeves for these same Pine sources ran 4Hour; neither TSV nor Pine names an interval). Sizing 100% of slice cash, whole units (LINKUSDT/ENJUSDT are not fractional-symbol forms in the v3 intent contract).
- Fee $0.65/contract/leg: batch-2 recorded assumption (source reads snapshot option_fees, unproduced in v3).
- Named missing producers (map §4): index-regime + XSP chain producer — xsp sleeves declare input `xsp_state`, unproduced, so they land visibly UNFED (blocker-proven); OPRA chain for the recovery books is the same `options` input posture as batch 2. Verdict: PARTIAL (fixture-proven; live producers unwired).

## ASTER-B16 — Aster batch 16 (2026-10-24): overnight 5bp, Donchian55, Tensor daily20 x2, saty_research shell

Sources: staged archive `source/backend/r19_timing.py` + `strategies/r19/tensor/RULES.json` (R19_TIMING_OVERNIGHT_5BP), `source/backend/trader_signals.py` + `trader_runtime.py` (TRADER_DONCHIAN55), `source/backend/tensor_daily_models.py` + `strategies/tensor_daily20/models/*` (D20_TENSOR / D20_PV), TSV-as-spec for saty_research (source absent, map S4). Engine: desk3/aster_batch16.py; adapters3 wrappers; $10,000 slice throughout. Tensor ENGINE untouched.

| sleeve | reading adopted |
|---|---|
| aster_r19_timing_overnight_5bp | Archive book verified byte-compared against the 25BP book: identical universe (frozen 42), kind, risk 0.0025, notional 0.1, slots 8 — ONLY fee_bps differs (5 vs 25). Port delegates to batch 15's single r19_timing implementation with fee_bps=5 (no second implementation of the signal/exit logic). Entry 15:30-15:35 ET on 12:30->14:30 return >= 80th percentile of prior 126+ sessions; ONLY exit = scheduled next-session open. Inputs bars/positions/quotes -> UNFED until the quotes producer lands (same posture as the 25bp twin). |
| aster_trader_donchian55 | Frozen rules doc verbatim: 15-ETF universe, >=252 daily bars, entry close > prior-55 high AND close > SMA200, rank (close-prior55)/ATR14 desc then symbol; sizing whole shares = min(0.1x equity, 0.01x DV20, cash) capped by 0.5% risk / (2x ATR14) per trader_runtime._entry; exits = close < prior-20 low, close < SMA200, initial 2ATR stop anchored to the entry fill, 126 completed holding bars. ASSUMPTIONS: (1) the observed-quote stop is evaluated at the sleeve layer on the last completed daily close, with the stop carried on the position read-back (`stop_price`, set from the entry intent); the source's execution manager owned the live quote stop. (2) Sizing price = signal close (source re-quotes at the next open within 300s; the v3 dispatcher owns execution pricing). |
| aster_tensor_d20_tensor / aster_tensor_d20_pv | Archive tensor_daily_models ported at the sleeve layer: canonical native feature rows in via the `tensor_daily20` snapshot key; feature_frame (35-col past-only transform), eligibility gates in archive order (excluded symbols, >=234 bars, native ready, close >= $5, DV20 >= $1M, ATR > 0, bar_index % 20 == canonical phase), frozen 100-tree ensembles with median imputation, prediction >= frozen threshold (PV 0.00698557, TENSOR 0.00612296), rank score desc/symbol, caps 0.1x equity / 0.01x DV20, 10 slots. ONLY exit = 20 completed holding bars (no stop/target by design; fixture proves a -50% close at bar 10 does NOT exit). Model artifacts vendored as data (desk3/aster_d20_assets/: MANIFEST.json sha256 pinned to the source-code constant 9be2845e..., price_volume.json, price_volume_plus_tensor.json, DAILY_SOURCE_ANCHORS.json — all hashes re-verified at load; tamper fails closed). Model math proven against the archive's exported estimator oracles (all vectors, both models) and against archive evaluate_daily20 scores on the fixture recipe (PV 0.032837683351856994, TENSOR 0.010204886593293511). ASSUMPTIONS: (1) rows must begin at the canonical anchor origin (archive: no phase rebasing); the per-symbol cooldown_until_index (decision bar + 20) coincides with the 20-bar hold exit and is not separately stateful at the sleeve layer. (2) No v3 producer emits tensor_daily20 rows yet -> both sleeves visibly UNFED, never fake-fed. |
| aster_saty_research | SOURCE ABSENT (map S4). TSV-as-spec meta-ranker SHELL only — the 10 setup families are NOT invented; pre-formed candidates arrive via `saty_setups` (no producer -> UNFED/monitor-only). Shell owns exactly the TSV-named mechanics: ranking by cost-adjusted net target room (T1 room minus $0.02/share, over planned risk), then context, then age; conflicting equal-ranked directions wait; risk 0.25% of slice ($25 = 1R), half for mean-reversion families; <=3 entries/day; entries halt at -2R realized; open risk <= 2R total and <= 1R correlated (single-instrument SPY book, so the 1R cluster cap binds); 5s quote freshness fail-closed; no entries in the last 20 min; exits = structural invalidation, T1 scale (half), final exit 10 min before close. ASSUMPTIONS: (1) mean-reversion identified by family name containing mean_reversion/meanrev/mean-reversion (TSV names no family list). (2) Post-scale trail = breakeven at the entry price (TSV: "tighten the remaining-share trail", no numeric trail given). (3) Session close = 16:00 ET (deadlines 15:40/15:50). (4) Day state (entries_today, realized_r_today) arrives via `saty_state`; absent state reads as zeros for entries but quote freshness still gates. |
