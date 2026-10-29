# Forecast Factory forecaster registry (P2, 2026-10-27)

Every candidate from the P2 sources, with its status. **registered** = implemented clean-room from its published definition, law-checked (laws.check, 200 histories) and searched; **deferred** = with its reason (data missing, forward-only, or not built in P2); **rejected** = with its reason.
Counts: registered 154, deferred 59, rejected 26 (total 239).


Sources read: EVIDENCE.md (docs/research/EVIDENCE.md on the memory worktree); scratchpad vendors/*.md §5 rows marked backtestable now; vendors/_muse_root.md (GENOME NOW rows); engine/PREDICTION_MAP.md. P1's own registered set (pick.A0–C0, odds.random, engine.har/veto/mom6, avoid.* ×10, feat.F3/N1/N7/F6/F7neg/N5neg) stays registered and is not repeated here; features and avoid enter the P2 search, picker/odds/engine stay on P1's replay path (event R targets and the per-bar 140-bar FB2 window).

Not covered: vendor files whose §5 has no backtestable-now row; _muse_root.md rows marked FWD or n/a; PREDICTION_MAP rows that restate an EVIDENCE row.

| id | status | source | definition or reason |
|---|---|---|---|
| `surv.rev1` | registered | EVIDENCE T2; PREDICTION_MAP U2 | survivors: targets up_excess_5, up_excess_20; sign +1; grade at birth B |
| `mom.r5` | registered | xcheck/composite C4 input | survivors: targets up_excess_5, up_excess_20; sign -1; grade at birth B |
| `mom.r126` | registered | EVIDENCE S10 | survivors: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `mom.r126_21` | registered | EVIDENCE S10; FB2 mom6 | survivors: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `mom.resid126` | registered | EVIDENCE S11 | survivors: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `mom.volscaled` | registered | EVIDENCE S11 | survivors: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `nvi.ema255` | registered | EVIDENCE S13 | survivors: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `veto.panic` | registered | PREDICTION_MAP D8; xcheck/predmap | survivors: targets up_excess_20, up_excess_60; sign -1; grade at birth B |
| `veto.spikemem` | registered | PREDICTION_MAP D17 | survivors: targets up_excess_20, up_excess_60; sign -1; grade at birth B |
| `veto.crashed` | registered | EVIDENCE A1 | survivors: targets up_excess_20, up_excess_60; sign -1; grade at birth B |
| `veto.pump100` | registered | PREDICTION_MAP D2 (A2b) | survivors: targets up_excess_20, up_excess_60; sign -1; grade at birth B |
| `veto.lod` | registered | EVIDENCE A9 | survivors: targets up_excess_5, up_excess_20; sign -1; grade at birth B |
| `veto.cgtph` | registered | EVIDENCE A4 | survivors: targets up_excess_5, up_excess_20; sign -1; grade at birth B |
| `veto.gapup10` | registered | EVIDENCE A12 | survivors: targets up_excess_5, up_excess_20; sign -1; grade at birth B |
| `vol.gex_pct` | registered | PREDICTION_MAP B13; vendors/squeezemetrics.md; vendors/spotgamma.md | regime: targets spy_rv_5, spy_rv_20, spy_rvx_20; sign -1; grade at birth C |
| `idx.dix_pct` | registered | vendors/squeezemetrics.md | regime: targets spy_ret_20, spy_ret_60; sign +1; grade at birth C |
| `vol.vix_ts` | registered | EVIDENCE V3; vendors/volsignals.md | regime: targets spy_rv_5, spy_rv_20, spy_rvx_20; sign +1; grade at birth B |
| `vol.vix_level` | registered | EVIDENCE V2 | regime: targets spy_rv_5, spy_rv_20, spy_rvx_20; sign +1; grade at birth B |
| `idx.vrp` | registered | EVIDENCE T3 | regime: targets spy_ret_20, spy_ret_60; sign +1; grade at birth B |
| `idx.skew_pct` | registered | vendors/volsignals.md | regime: targets spy_ret_20; sign -1; grade at birth B |
| `chk.cmf21` | registered | chaikin.md §9 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.dema_roc42` | registered | chaikin.md §9 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.vol30_90` | registered | chaikin.md §9 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.px_dema200` | registered | chaikin.md §9 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.rs126` | registered | chaikin.md §9 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.tech5` | registered | chaikin.md §5 F-CHK-1 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `chk.trendclip` | registered | chaikin.md §5 F-CHK-2 | vendors: targets up_excess_20, up_excess_60; sign -1; grade at birth NEW |
| `sf.fade` | registered | scalpflip-ea.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `sf.smart` | registered | scalpflip-ea.md §3 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `qc.streak` | registered | quantcharts.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign -1; grade at birth NEW |
| `ict.c2` | registered | ict2023trader-indicators.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `ict.c2cisd` | registered | ict2023trader-indicators.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `eg.gapfill` | registered | edgeful.md §3, §5 (daily variant) | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `eg.pdr_break` | registered | edgeful.md §3 (daily ORB/prior-range analogue) | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `cs.correction` | registered | correctionscope-ai.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `ap.regime` | registered | algopoint.md §3, §5 | vendors: targets realized_vol_20; sign +1; grade at birth NEW |
| `ap.trend` | registered | algopoint.md §3, §5 | vendors: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW |
| `sm.P` | registered | squeezemetrics.md §2, §5 | vendors: targets up_excess_20; sign +1; grade at birth NEW |
| `sm.V` | registered | squeezemetrics.md §2, §5 | vendors: targets realized_vol_20; sign +1; grade at birth NEW |
| `vol.garch` | registered | gexradar.md §5 | vendors: targets realized_vol_20; sign +1; grade at birth NEW |
| `risk.semidev` | registered | danelfin.md §5 F-DAN-3 | vendors: targets up_excess_20, up_excess_60; sign -1; grade at birth NEW |
| `sr.hi52` | registered | stockrover.md §5 F-SR-1 | vendors: targets up_excess_20, up_excess_60; sign +1; grade at birth NEW |
| `tai.pct` | registered | zeiierman.md §5 | vendors: targets realized_vol_20; sign +1; grade at birth NEW |
| `alt.antichase` | registered | altindex.md §5 | vendors: targets up_excess_20, up_excess_60; sign -1; grade at birth NEW |
| `xs.momdip` | registered | xcheck/composite C4 | xs: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `xs.n9_up` | registered | EVIDENCE S7 | xs: targets up_excess_20, up_excess_60; sign +1; grade at birth C |
| `xs.n9_reset` | registered | EVIDENCE S6 | xs: targets up_excess_20, up_excess_60; sign +1; grade at birth B |
| `s12.index_membership` | deferred | EVIDENCE S12 | data missing: no point-in-time S&P 500/600 membership in the desk data |
| `s14.r1_low_short_volume` | deferred | EVIDENCE S14 | data missing: FINRA daily short volume is not in the DEEP replay inputs (and FINRA terms risk R1) |
| `s15.gap_share_fear` | deferred | EVIDENCE S15 | not built in P2: the gap_share formula lives in the MRI ledger, which was not among the sources read |
| `s16.strong_close_iwm` | deferred | EVIDENCE S16 | not built in P2: IWM is not yet a law-checked market input of the per-name contract |
| `s17.filled_pullback_plan` | deferred | EVIDENCE S17 | not built in P2: a fill-model forecaster; the per-opportunity denominator (gates.per_opportunity) it needs ships in P2 |
| `s9.fear_personality` | deferred | EVIDENCE S9 | not built in P2: holdout-only evidence, a forward candidate (P) |
| `s25.obv_ad_split` | deferred | EVIDENCE S25 | not built in P2: grade C, the registered variant already went the wrong way (AD-12) |
| `a8.repeat_reverse_split` | deferred | EVIDENCE A8; PREDICTION_MAP D10, B8 | data missing: the raw-vs-adjusted split factor is not part of the law-checked bar arrays (c_raw is used for costs only) |
| `a11.heavily_shorted` | deferred | EVIDENCE A11 | data missing: FINRA short interest / short volume not in DEEP |
| `a12.earnings_gap` | deferred | EVIDENCE A12 | data missing: no point-in-time earnings calendar on DEEP; the gap leg alone is registered as veto.gapup10 |
| `a13.pre_earnings` | deferred | EVIDENCE A13 | data missing: no point-in-time earnings calendar on DEEP |
| `a6.stacked_warnings` | rejected | EVIDENCE A6 | combinations of registered vetoes; stacking is a portfolio question (P3 breadth), and triples are excluded from the search by design |
| `a10.broken_plus_bullish` | rejected | EVIDENCE A10 | a triple combination; triples are excluded from the search (Factory lesson, 0 of 9,861) |
| `a16.short_book` | rejected | EVIDENCE A16 | a monetisation (short book), not a forecast; graded X |
| `t1.fear_lift` | rejected | EVIDENCE T1 | a context (the fear dimension), not a forecaster: every cell is split by it |
| `t4.spy_rising_200` | rejected | EVIDENCE T4 | a context (the spy200 dimension), not a forecaster |
| `t6.credit_stress` | rejected | EVIDENCE T6 | FRED in a fitted model is barred by the owner's rule |
| `t8.qqq_bear_flip_tza` | deferred | EVIDENCE T8 | not built in P2: an index hedge timing rule with 3 OOS episodes; a P3 router question |
| `t9.buy_day_overnight` | deferred | EVIDENCE T9 | not built in P2: the market lane has no overnight-return target yet |
| `t10.calendar_fibonacci` | rejected | EVIDENCE T10 | ruled out (X) |
| `v7.hmm_kelly` | rejected | EVIDENCE V7; gexradar.md HMM | ruled out (X); the GEXRADAR filtered-HMM row is the same family |
| `exit.rules_e1_e5` | rejected | EVIDENCE E1-E5 | exit rules, not forecasts (the router and Lab arms own them) |
| `gestalt.rejection_memory` | deferred | gestalt ANALYSIS.md | data missing: the Tensor Deep Validation / Forensic reports are not available to the desk |
| `pm.n2_loud_spike_no_move` | deferred | PREDICTION_MAP N2 | forward-only: a NO-MOVE options route needs recorded chains (FACTORY §4.10); the realized-vol leg is covered by vol forecasters |
| `muse.g5_g8_grids` | rejected | _muse_root.md G5, G8 | position and order rules, not forecasters |
| `algoalpha.fomo_exhaustion` | rejected | algoalpha.md §5 | under-specified: 'fair value' is undefined and k, z are vendor examples only |
| `algopoint.hurst_ou` | deferred | algopoint.md §5 | not built in P2: lookback-adaptive OU bands, medium priority |
| `altindex.insider_congress` | deferred | altindex.md §5 | data missing: Form 4 / congressional history is not in the DEEP replay inputs |
| `apexquant.spring_utad` | rejected | apexquant.md §5 | the same daily sweep-and-reclaim primitive as ict.c2 (registered) |
| `azrael.em_band_containment` | deferred | azrael-1587.md, azrael-options.md Z1 | not built in P2: a calibration of the VIX/sqrt(252) band for the options router (P3/P4); not a ranking forecaster |
| `azrael.funded_range_gate` | deferred | azrael-1587.md; azrael-options.md Z2 | data missing: needs SPY 5-minute history beyond the desk's 2026 window |
| `azrael.three_ticker_break` | deferred | azrael-options.md Z3 | data missing: 5-minute SPY/QQQ history |
| `azrael.vix_regime_walls` | rejected | azrael-options.md Z4 | a context (the vix dimension) |
| `chaikin.full_20_factor` | deferred | chaikin.md §5 F-CHK-4 | data missing: point-in-time fundamentals, estimates and short interest |
| `chartprime.volume_order_blocks` | deferred | chartprime.md §5 | not built in P2: low priority; the cluster definition must be the desk's own |
| `coincodecap.signal_follower` | rejected | coincodecap.md §5 | crypto perps from a self-reported ledger: not a backtest |
| `danelfin.tree_ranker` | deferred | danelfin.md §5 F-DAN-1 | not built in P2: a fitted model; the combiner and calibration are P3 |
| `edgeful.gapfill_intraday` | deferred | edgeful.md §5 | data missing: intraday history (5-minute) is too short; the daily variant is registered as eg.gapfill |
| `edgeful.ib_orb_extension` | deferred | edgeful.md §5 | data missing: 5-minute history; the daily prior-range analogue is registered as eg.pdr_break |
| `gainzalgo.stump_booster` | deferred | gainzalgo.md §5 | not built in P2: a fitted model (P3 combiner) |
| `gammaedge.swing_filter` | deferred | gammaedge.md §5 | data missing: point-in-time market cap and the call-dominated (OI) leg is forward-only |
| `gammaedge.wheel_csp` | deferred | gammaedge.md §5 | forward-only: premium P&L needs option history |
| `gexradar.expansion_z` | deferred | gexradar.md §5 | not built in P2: depends on vol.garch, which is registered; a big_move target lane is P3 |
| `ict.cisd_1h_ltf` | deferred | ict2023trader-indicators.md §5 | data missing: 1H history starts 2026-03 (EVIDENCE AD-09); the daily C2+CISD is registered |
| `ict.stddev_targets` | rejected | ict2023trader-indicators.md §5 | exit levels, not a forecast |
| `insiderfinance.insider_cluster` | deferred | insiderfinance.md I1 | data missing: the Form 4 mirror is not part of the DEEP replay inputs |
| `kobeissi.setup_ledger` | rejected | kobeissi.md §5 | ex-post self-published commodity calls: selection risk, outside the desk's books |
| `leadr.conviction8` | rejected | leadrlabs.md §5 | already tested pre-registered (LDR-1, t 0.61): X |
| `lector.rs_percentrank` | rejected | lector-systems.md §5 | duplicate of chk.rs126 (relative strength vs SPY, registered) |
| `lector.rrr_etf` | deferred | lector-systems.md §5 | not built in P2: an ETF relative lane is not built |
| `levelfields.event_study` | deferred | levelfields.md §5 | data missing: EDGAR buyback / 8-K 5.02 event history is not in the DEEP inputs |
| `marketchameleon.hfv` | deferred | marketchameleon.md M1 | forward-only: the VE leg needs a historical chain mid |
| `marketcipher.oscillator_dot` | deferred | marketcipher.md §5 | data missing: specified on 1H bars |
| `menthorq.seasonality` | deferred | menthorq.md §5 | data missing: 20 years of history (DEEP holds 10) |
| `menthorq.iv_swing_bands` | deferred | menthorq.md §5 | forward-only per name (no IV history); the SPX leg is the VIX band calibration |
| `morgue.constituent_dix` | deferred | morgue-engine.md F3 | data missing: FINRA FNQC files are not in the DEEP inputs |
| `morgue.board_cohort` | deferred | morgue-engine.md F4 | not built in P2: needs a PIT universe membership audit |
| `optionalpha.pop_calibration` | deferred | optionalpha.md F1; optionstrat.md O1 | not built in P2: an options-router calibration (P3/P4), merged with OptionStrat O1 |
| `optionalpha.orb_bots` | deferred | optionalpha.md F4 | data missing: 1- or 5-minute SPY history |
| `prospero.short_pressure` | deferred | prospero.md §5 | data missing: FINRA short volume |
| `prospero.market_similarity` | rejected | prospero.md §5 | a context (beta), standard; not a forecaster |
| `quantix.backtest_live_haircut` | rejected | quantix.md §5 | a meta dataset for gate priors, not a forecaster |
| `quantumalgo.smc_confluence` | deferred | quantumalgo.md §5 | data missing: specified on 1H signals |
| `squeezemetrics.D_dark_ratio` | deferred | squeezemetrics.md §5 | data missing: FINRA daily short volume per ticker |
| `squeezemetrics.P_NN` | deferred | squeezemetrics.md §5 | forward-only: G needs OI history; the analogue search is P3 |
| `stockrover.sentiment_rest` | deferred | stockrover.md F-SR-1 | not built in P2: the 52-week-high leg is registered (sr.hi52); short interest is data missing |
| `survey.barchart_opinion` | deferred | survey.md §5 | not built in P2: the 13-indicator vote is not specified in the file read |
| `tickernerd.nine_family` | deferred | tickernerd.md F-TN-2 | data missing: six of nine families need fundamentals |
| `tradeideas.oddsmaker` | rejected | trade-ideas.md §5 | tooling, not a signal (the factory is this tool) |
| `trendspider.raindrop` | deferred | trendspider.md §5 | data missing: 1-minute SIP volume for the universe |
| `vectorvest.vst_rt` | rejected | vectorvest.md F-VV-1 | plain multi-horizon momentum: covered by mom.r126 / mom.volscaled |
| `zeiierman.nwo` | deferred | zeiierman.md §5 | not built in P2: medium priority |
| `zeiierman.feature_trio` | deferred | zeiierman.md §5 | not built in P2: inputs of a P3 combiner |
| `zeiierman.sweep_reclaim` | rejected | zeiierman.md §5 | duplicate of ict.c2 (registered) |
| `lector.2b` | registered | lector-systems.md §3 (CL4) | vendors2: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.naive20` | registered | lector-systems.md §5 (CL4 control) | vendors2: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.xatr_2c` | registered | lector-systems.md §3 (CL5) | vendors2: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.xatr_2d` | registered | lector-systems.md §3 (CL5) | vendors2: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.xatr_4c` | registered | lector-systems.md §3 (CL5) | vendors2: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `rsc.pf3` | registered | linda_raschke.md §3 (LR1) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `rsc.rotation` | registered | linda_raschke.md §3 (LR3) | vendors2: targets no_move_5, no_move_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `rsc.holygrail` | registered | linda_raschke.md §3 (LR4, AIQ 1997) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `rsc.turtle` | registered | linda_raschke.md §3 (LR4, TradingMarkets 2003) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.bos` | registered | luxalgo.md §3 SPEC (C15) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.choch` | registered | luxalgo.md §3 SPEC (C15) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.fvg` | registered | luxalgo.md §3 SPEC (C16, C17 touch) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.fvg_atr` | registered | luxalgo.md §3 (C16, C48 0.5 ATR minimum) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.fvg_half` | registered | luxalgo.md §3 (C17 50% mitigation) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.fvg_full` | registered | luxalgo.md §3 (C17 full mitigation) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.fvg_dist` | registered | luxalgo.md §3 (C17 distance feature) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.ifvg` | registered | luxalgo.md §3 (C21 inverse FVG) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.bos_fvg` | registered | luxalgo.md §3 SPEC (C15, C16) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lux.ob` | registered | quantumalgo.md / luxalgo.md (C18); readout the desk's | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `ez.sweepgap` | registered | ezalgo.md §3 (C74); thresholds the desk's | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `ap.stadapt` | registered | algopoint.md §3 (C42) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `ap.st3` | registered | algopoint.md §3 (C42 control arm) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `mc.wt` | registered | marketcipher.md §3 SPEC (C54) | vendors2: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `byb.atr_band5` | registered | bybit-apk.md §5 (V-bybit-2) | vendors2: targets no_move_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `byb.atr_band20` | registered | bybit-apk.md §5 (V-bybit-2) | vendors2: targets no_move_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gs.five` | registered | gridscalperea.md §3 (V-gs-1) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gs.five_sig` | registered | gridscalperea.md §3 (V-gs-1) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gs.ema` | registered | gridscalperea.md §5 (V-gs-1 arm) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gs.rsi` | registered | gridscalperea.md §5 (V-gs-1 arm) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `zer.macd200` | registered | zerith-macd-grid.md §3 (V-zerith-1) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qc.locstreak` | registered | quantcharts.md §3, §5 (V-qc-2) | vendors2: targets up_excess_5; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gex.entropy20` | registered | gexradar.md (A97) | vendors2: targets realized_vol_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `tjr.smt_qqq` | registered | tjr.md §5 (C83) | vendors2: targets spy_ret_5, spy_ret_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `tjr.smt_iwm` | registered | tjr.md §5 (C83) | vendors2: targets spy_ret_5, spy_ret_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `oft3r.macro5` | registered | study/fw.md macro_pillar (V-oft3r-2) | vendors2: targets spy_ret_20, spy_ret_60; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `oft3r.macro5_rv` | registered | study/fw.md macro_pillar (V-oft3r-2) | vendors2: targets spy_rv_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `composer.dualmom` | registered | composer.md (C116) | vendors2: targets spy_ret_20, rel_spy_bnd_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `survey.tv_technical_rating` | rejected | survey.md §5 (V-survey-2) | superseded: built as tv.osc, tv.ma and tv.rating (vendors3) from TradingView's Help Center vote table; this row is the old deferral |
| `vibe.factor_zoo` | deferred | vibe-trading.md §5 (V-vibe-4) | not built in P2: 30 per-name formulas are registered (a101.*, gtja.*, qlib.*, vendors3); the other 257 per-name ones are repeats of the same shape at other windows, and the cross-sectional ones (rank, scale, industry) wait for the xs lane |
| `oft3r.inflationary_flag` | deferred | study/fw.md macro_pillar (V-oft3r-2) | not built in P2: under-specified: the window of spy_tlt_corr and the definition of equity_bond.signal are not in the teardown (threshold 0.25 only) |
| `gridscalper.straddle_forecaster` | rejected | gridscalperea.md §5 (V-gs-3) | superseded: built as gs.straddle5 (vendors3), the trailing rate of the straddle label over completed outcomes |
| `composer.dualmom_12_1` | rejected | composer.md (C116) | superseded: built as composer.dualmom12_1 (vendors3), SPY vs BND 12-1 month dual momentum on the index lane |
| `gainzalgo.rulegate` | registered | GZ gainzalgo_replica.pine:34-60 (C25) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rs26` | registered | CH 1-Month Relative Strength.txt:15-31 (CL3) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rs78` | registered | CH 1-Month Relative Strength.txt:15-31 (CL3, N 78) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rs156` | registered | CH 1-Month Relative Strength.txt:15-31 (CL3, N 156) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rs_run15` | registered | CH 1-Month Relative Strength.txt:52-56 (CL3 alert) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rs_12of15` | registered | CH 1-Month Relative Strength.txt:58-64 (CL3 alert) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rrr_ratio` | registered | CH Relative Robustness Rotation.txt (CL7) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rrr_mom` | registered | CH Relative Robustness Rotation.txt (CL7) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.rrr_q` | registered | CH Relative Robustness Rotation.txt (CL7) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.nvars` | registered | CH Normalized Volatility Adjusted Relative Strength.txt:76-145 | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.nvars_fs` | registered | CH Normalized Volatility Adjusted Relative Strength.txt:152-163 | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_1a` | registered | CH Candles Stage Analysis.txt:52,105 | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_1b` | registered | CH Candles Stage Analysis.txt:67,107 | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_2a` | registered | CH Candles Stage Analysis.txt:101-102 | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_2b` | registered | CH Candles Stage Analysis.txt:48,101-102 (CL4, strict ladder) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_2c` | registered | CH Candles Stage Analysis.txt:58,93 (CL5) | vendors3: targets up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_2d` | registered | CH Candles Stage Analysis.txt:59,91 (CL5) | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_3a` | registered | CH Candles Stage Analysis.txt:65,97 | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_3b` | registered | CH Candles Stage Analysis.txt:66,99 | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_4a` | registered | CH Candles Stage Analysis.txt:103-104 | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_4b` | registered | CH Candles Stage Analysis.txt:49,103-104 | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.stg_4c` | registered | CH Candles Stage Analysis.txt:62,95 (CL5) | vendors3: targets up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.cgap` | registered | CH Unfilled Close-Adjusted Gaps.txt:20-112 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.cgap_dist` | registered | CH Unfilled Close-Adjusted Gaps.txt:48-62, 93-108 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.crsi_z` | registered | CH Calibrated RSI Position Zones.txt:232-251 | vendors3: targets up_excess_5, up_excess_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.crsi_cont` | registered | CH Calibrated RSI Position Zones.txt:379-389 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.crsi_early` | registered | CH Calibrated RSI Position Zones.txt:393-403 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.crsi_mr` | registered | CH Calibrated RSI Position Zones.txt:407-419 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.crsi_ctr` | registered | CH Calibrated RSI Position Zones.txt:422-432 | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `tv.osc` | registered | TV Technical Ratings Help Center, 11 oscillator votes (V-survey-2) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `tv.ma` | registered | TV Technical Ratings Help Center, 15 MA votes (V-survey-2) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `tv.rating` | registered | TV Pine library jDWyb5PG calcRatingAll (V-survey-2) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gs.straddle5` | registered | gridscalperea.md §5 (V-gs-3) | vendors3: targets realized_vol_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.006` | registered | Vibe-Trading zoo alpha101/alpha_006.py: -1 * correlation(open, volume, 10) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.007` | registered | Vibe-Trading zoo alpha101/alpha_007.py: (adv20<volume) ? (-ts_rank(abs(delta(close,7)),60) * sign(delta(close,7))) : -1 (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.009` | registered | Vibe-Trading zoo alpha101/alpha_009.py: 0<ts_min(d1,5) ? d1 : (ts_max(d1,5)<0 ? d1 : -d1), d1 = delta(close,1) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.012` | registered | Vibe-Trading zoo alpha101/alpha_012.py: sign(delta(volume,1)) * (-1 * delta(close,1)) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.021` | registered | Vibe-Trading zoo alpha101/alpha_021.py: Kakushadze #21 band-and-volume ladder (+-1) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.023` | registered | Vibe-Trading zoo alpha101/alpha_023.py: (sum(high,20)/20 < high) ? -1 * delta(high,2) : 0 (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.024` | registered | Vibe-Trading zoo alpha101/alpha_024.py: delta(sma100,100)/delay(close,100) <= 0.05 ? -(close - ts_min(close,100)) : -delta(close,3) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.026` | registered | Vibe-Trading zoo alpha101/alpha_026.py: -1 * ts_max(correlation(ts_rank(volume,5), ts_rank(high,5), 5), 3) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.035` | registered | Vibe-Trading zoo alpha101/alpha_035.py: ts_rank(volume,32) * (1 - ts_rank(close+high-low,16)) * (1 - ts_rank(returns,32)) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `a101.043` | registered | Vibe-Trading zoo alpha101/alpha_043.py: ts_rank(volume/adv20,20) * ts_rank(-1*delta(close,7),8) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.002` | registered | Vibe-Trading zoo gtja191/alpha_002.py: -1 * delta(((close-low)-(high-close))/(high-low), 1) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.003` | registered | Vibe-Trading zoo gtja191/alpha_003.py: sum over 6 of close - (close>delay ? min(low,delay) : max(high,delay)), 0 if unchanged (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.009` | registered | Vibe-Trading zoo gtja191/alpha_009.py: SMA(((high+low)/2-(delay(high)+delay(low))/2)*(high-low)/volume, 7, 2) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.011` | registered | Vibe-Trading zoo gtja191/alpha_011.py: sum(((close-low)-(high-close))/(high-low)*volume, 6) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.014` | registered | Vibe-Trading zoo gtja191/alpha_014.py: close - delay(close,5) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.015` | registered | Vibe-Trading zoo gtja191/alpha_015.py: open/delay(close,1) - 1 (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.018` | registered | Vibe-Trading zoo gtja191/alpha_018.py: close/delay(close,5) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.019` | registered | Vibe-Trading zoo gtja191/alpha_019.py: 5-day change over delay (down) or over close (up), 0 if equal (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.020` | registered | Vibe-Trading zoo gtja191/alpha_020.py: (close-delay(close,6))/delay(close,6) * 100 (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `gtja.021` | registered | Vibe-Trading zoo gtja191/alpha_021.py: regression slope of mean(close,6) on a 6-bar sequence (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.kmid` | registered | Vibe-Trading zoo qlib158/kmid.py: (close-open)/open (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.klen` | registered | Vibe-Trading zoo qlib158/klen.py: (high-low)/open (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.kmid2` | registered | Vibe-Trading zoo qlib158/kmid2.py: (close-open)/(high-low) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.kup` | registered | Vibe-Trading zoo qlib158/kup.py: (high - max(open,close))/open (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.kup2` | registered | Vibe-Trading zoo qlib158/kup2.py: (high - max(open,close))/(high-low) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.klow` | registered | Vibe-Trading zoo qlib158/klow.py: (min(open,close) - low)/open (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.klow2` | registered | Vibe-Trading zoo qlib158/klow2.py: (min(open,close) - low)/(high-low) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.ksft` | registered | Vibe-Trading zoo qlib158/ksft.py: (2*close-high-low)/open (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.ksft2` | registered | Vibe-Trading zoo qlib158/ksft2.py: (2*close-high-low)/(high-low) (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `qlib.roc20` | registered | Vibe-Trading zoo qlib158/roc20.py: delay(close,20)/close (V-vibe-4, MIT) | vendors3: targets up_excess_5, up_excess_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.vmr` | registered | CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10) | vendors3: targets spy_ret_20, spy_ret_60; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.vmr3` | registered | CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10, VVIX leg renormalised away) | vendors3: targets spy_ret_20, spy_ret_60; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.vmr_rv` | registered | CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10) | vendors3: targets spy_rv_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.vmr_risk` | registered | CH Market Action Pulse & VIX Mood Ring.txt:818-831 (CL9) | vendors3: targets spy_ret_20, spy_rv_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.pulse` | registered | CH Market Action Pulse & VIX Mood Ring.txt:225-375 (CL8) | vendors3: targets spy_ret_20, spy_ret_60; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.ram` | registered | CH Market Action Pulse & VIX Mood Ring.txt:803-877 (CL9) | vendors3: targets spy_ret_20, spy_rv_20; sign -1; grade at birth NEW; DISCOVERY-ONLY |
| `composer.dualmom12_1` | registered | composer.md (C116, 12-1 form) | vendors3: targets spy_ret_20; sign +1; grade at birth NEW; DISCOVERY-ONLY |
| `lector.em_gmm_regime` | deferred | CH Expectation Maximization Gaussian Mixture Regime.txt | not built in P2: the 42 KB mixture indicator needs a ported EM with its convergence rule and a label-switching rule, neither of which can be fixed without reading it line by line against a fixture |
| `lector.lod_intraday` | deferred | CH LoD Intraday Entry.txt; 30 min Pivot.txt | data missing: intraday bars (1H history starts 2026-03, EVIDENCE AD-09) |
| `lector.cot_net` | deferred | CH COT Net Positions.txt | data missing: the CFTC commitments-of-traders history is not in the DEEP inputs |
| `lector.nyse_tick` | deferred | CH Raschke-style NYSE TICK Intermediate Cycle.txt | data missing: the NYSE TICK index history |
| `lector.pulse_live` | deferred | CH Market Action Pulse & VIX Mood Ring.txt | data missing: Nasdaq and NYSE advancers/decliners history and the QQQE series are not in the DEEP inputs; lector.pulse and lector.ram abstain without them and are tested on fixtures |
| `luxalgo.fvg_double_opening_gap` | deferred | luxalgo.md (C21) | not built in P2: under-specified: LuxAlgo PAC is invite-only and no definition of a double FVG or an opening-gap zone is on disk; the inverse FVG is built (lux.ifvg) |


## Grade after the rerun (2026-10-27, docs/research/forecast-search-rerun-2026-10-27.md)

Grade A (replicated on the second dataset by the pre-registered strict rule) at the forecaster x target level, with the
cells graded A out of the cells run 1 promoted: `vol.garch` realized_vol_20 (48 of 88), `tai.pct` realized_vol_20 (7 of 21),
`vol.gex_pct` spy_rv_5 (2 of 5), `avoid.pump` up_excess_20 (2 of 77), `veto.gapup10` up_excess_5 (2 of 71) and up_excess_20 (1 of
55), `avoid.deadcat` up_excess_20 (1 of 65). Everything else stays grade B; 325 stock-direction cells are `confirmed`
(same sign, rerun holdout t >= 2, not strictly promoted on 15 months of discovery) and stay on probation in the book.
