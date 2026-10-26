# Verification

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

| Family | Cards | Rules read |
|---|---:|---:|
| [Ausar](verify/ausar.md) | 24 | 178 |
| [Lazarus](verify/lazarus.md) | 19 | 178 |
| [Femto-lean](verify/femto.md) | 45 | 384 |
| [Midna](verify/midna.md) | 15 | 81 |
| [Muse](verify/muse.md) | 12 | 164 |
| [APEX](verify/apex.md) | 33 | 335 |
| [Galath / GrokBot](verify/galath.md) | 8 | 108 |
| [Griffith](verify/griffith.md) | 23 | 180 |
| [Milkman](verify/milkman.md) | 33 | 269 |
| [Quant research](verify/quant_research.md) | 18 | 161 |
| [Tensor research](verify/tensor_research.md) | 13 | 105 |
| [Killed studies](verify/killed.md) | 10 | 86 |
| [Qullamaggie](verify/qullamaggie.md) | 3 | 35 |
| [Sable](verify/sable.md) | 2 | 31 |
| [SPAN](verify/span.md) | 1 | 20 |

## Copied code

Each file under `sleeves/<family>/` that is not Midna's is a copy of a master-desk file, byte for byte at commit `843ccb53ad15` unless the table says otherwise.

| This repo | Master desk | Changed |
|---|---|---|
| `sleeves/apex/apex.py` | `desk/sleeves/families/apex.py` |  |
| `sleeves/apex/apex_options.py` | `desk/sleeves/families/apex_options.py` |  |
| `sleeves/apex/feedlib/apex.py` | `desk/feedlib/apex.py` |  |
| `sleeves/apex/feedlib/apex_book.py` | `desk/feedlib/apex_book.py` |  |
| `sleeves/apex/feedlib/apex_rules.py` | `desk/feedlib/apex_rules.py` |  |
| `sleeves/apex/vendor/apex/__init__.py` | `desk/vendor/apex/__init__.py` |  |
| `sleeves/apex/vendor/apex/agents.py` | `desk/vendor/apex/agents.py` |  |
| `sleeves/apex/vendor/apex/backtest_options.py` | `desk/vendor/apex/backtest_options.py` |  |
| `sleeves/apex/vendor/apex/bs.py` | `desk/vendor/apex/bs.py` |  |
| `sleeves/apex/vendor/apex/engine.py` | `desk/vendor/apex/engine.py` |  |
| `sleeves/apex/vendor/apex/inventions.py` | `desk/vendor/apex/inventions.py` |  |
| `sleeves/apex/vendor/apex/opt_strategies.py` | `desk/vendor/apex/opt_strategies.py` |  |
| `sleeves/apex/vendor/apex/round3.py` | `desk/vendor/apex/round3.py` |  |
| `sleeves/apex/vendor/apex/series.py` | `desk/vendor/apex/series.py` |  |
| `sleeves/apex/vendor/apex/sim.py` | `desk/vendor/apex/sim.py` |  |
| `sleeves/apex/vendor/apex/strategies.py` | `desk/vendor/apex/strategies.py` |  |
| `sleeves/apex/vendor/apex/surface.py` | `desk/vendor/apex/surface.py` |  |
| `sleeves/apex/vendor/apex/surface_params.json` | `desk/vendor/apex/surface_params.json` |  |
| `sleeves/ausar/ausar_spot_recipes.py` | `desk/sleeves/families/ausar_spot_recipes.py` |  |
| `sleeves/ausar/r17_etf.py` | `desk/sleeves/families/r17_etf.py` |  |
| `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py` | `desk/vendor/ausar_ctx/backend/public_recipe_runtime.py` |  |
| `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py` | `desk/vendor/ausar_ctx/strategies/public_recipes/public_source_sleeves.py` |  |
| `sleeves/ausar/vendor/quant_r17/EXPERIMENT_PROTOCOL.json` | `desk/vendor/quant_r17/EXPERIMENT_PROTOCOL.json` | research-box host path neutralised (3) |
| `sleeves/ausar/vendor/quant_r17/run_ladder.py` | `desk/vendor/quant_r17/run_ladder.py` |  |
| `sleeves/femto/aurelia_ndx.py` | `desk/sleeves/femto/aurelia_ndx.py` |  |
| `sleeves/femto/blowoff_1h.py` | `desk/sleeves/femto/blowoff_1h.py` |  |
| `sleeves/femto/blowoff_d.py` | `desk/sleeves/femto/blowoff_d.py` |  |
| `sleeves/femto/compat.py` | `desk/sleeves/femto/compat.py` |  |
| `sleeves/femto/feedlib/aurelia.py` | `desk/feedlib/aurelia.py` |  |
| `sleeves/femto/feedlib/blowoff.py` | `desk/feedlib/blowoff.py` |  |
| `sleeves/femto/momentum.py` | `desk/sleeves/femto/momentum.py` |  |
| `sleeves/femto/momentum_rotation.py` | `desk/sleeves/femto/momentum_rotation.py` |  |
| `sleeves/femto/morning_dip.py` | `desk/sleeves/femto/morning_dip.py` |  |
| `sleeves/femto/phase_daily.py` | `desk/sleeves/femto/phase_daily.py` |  |
| `sleeves/femto/phoenix.py` | `desk/sleeves/femto/phoenix.py` | the owner's first name replaced by 'the owner' (2) |
| `sleeves/femto/qqq_put_ladder.py` | `desk/sleeves/femto/qqq_put_ladder.py` |  |
| `sleeves/femto/qullamaggie.py` | `desk/sleeves/femto/qullamaggie.py` |  |
| `sleeves/femto/qullamaggie_paper.py` | `desk/sleeves/femto/qullamaggie_paper.py` |  |
| `sleeves/femto/sleeve_core.py` | `desk/sleeves/femto/sleeve_core.py` |  |
| `sleeves/femto/vendor/aurelia/allocate.py` | `desk/vendor/aurelia/allocate.py` |  |
| `sleeves/femto/vendor/aurelia/features.py` | `desk/vendor/aurelia/features.py` |  |
| `sleeves/femto/vendor/aurelia/judgment.py` | `desk/vendor/aurelia/judgment.py` |  |
| `sleeves/femto/vendor/aurelia/plan.py` | `desk/vendor/aurelia/plan.py` |  |
| `sleeves/femto/vendor/aurelia/prism.py` | `desk/vendor/aurelia/prism.py` |  |
| `sleeves/femto/vendor/aurelia/put_ladder.py` | `desk/vendor/aurelia/put_ladder.py` |  |
| `sleeves/femto/vendor/aurelia/session.py` | `desk/vendor/aurelia/session.py` |  |
| `sleeves/femto/vendor/aurelia_qulla/desk.py` | `desk/vendor/aurelia_qulla/desk.py` |  |
| `sleeves/femto/vendor/old_desk_research/rsiobv.py` | `desk/vendor/old_desk_research/rsiobv.py` |  |
| `sleeves/femto/vendor/old_desk_research/run_r4_blowoff_standalone.py` | `desk/vendor/old_desk_research/run_r4_blowoff_standalone.py` | research-box host path neutralised (1) |
| `sleeves/galath/anna.py` | `desk/sleeves/galath/anna.py` |  |
| `sleeves/galath/book.py` | `desk/sleeves/galath/book.py` |  |
| `sleeves/galath/echo.py` | `desk/sleeves/galath/echo.py` |  |
| `sleeves/galath/galath.py` | `desk/sleeves/families/galath.py` |  |
| `sleeves/galath/grokbot.py` | `desk/sleeves/families/grokbot.py` (branch master-desk, commit `f650e4e0`) |  |
| `sleeves/galath/komar.py` | `desk/sleeves/galath/komar.py` |  |
| `sleeves/galath/levels.py` | `desk/sleeves/galath/levels.py` |  |
| `sleeves/galath/paper.py` | `desk/sleeves/galath/paper.py` |  |
| `sleeves/galath/prism.py` | `desk/sleeves/galath/prism.py` |  |
| `sleeves/galath/tensor.py` | `desk/sleeves/galath/tensor.py` |  |
| `sleeves/galath/v8math.py` | `desk/sleeves/v8math.py` |  |
| `sleeves/galath/vendor/cci_correction/cci_correction.py` | `desk/vendor/cci_correction/cci_correction.py` (branch master-desk, commit `f650e4e0`) |  |
| `sleeves/galath/vendor/galath/desk-store.ts` | `desk/vendor/galath/desk-store.ts` |  |
| `sleeves/galath/vendor/galath/folio-list.ts` | `desk/vendor/galath/folio-list.ts` |  |
| `sleeves/galath/vendor/galath/universe.ts` | `desk/vendor/galath/universe.ts` |  |
| `sleeves/galath/vendor/universes/old_desk/genome_universe_1838.txt` | `desk/vendor/universes/old_desk/genome_universe_1838.txt` |  |
| `sleeves/galath/wire.py` | `desk/sleeves/galath/wire.py` |  |
| `sleeves/griffith/event_research.py` | `desk/sleeves/families/event_research.py` |  |
| `sleeves/griffith/feedlib/griffith.py` | `desk/feedlib/griffith.py` |  |
| `sleeves/griffith/feedlib/griffith_earnings.py` | `desk/feedlib/griffith_earnings.py` |  |
| `sleeves/griffith/feedlib/griffith_intraday.py` | `desk/feedlib/griffith_intraday.py` |  |
| `sleeves/griffith/griffith.py` | `desk/sleeves/families/griffith.py` |  |
| `sleeves/griffith/griffith_factor.py` | `desk/sleeves/families/griffith_factor.py` |  |
| `sleeves/griffith/griffith_intraday.py` | `desk/sleeves/families/griffith_intraday.py` |  |
| `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` | `desk/vendor/griffith/r4_parallel_strategy_lab.py` |  |
| `sleeves/griffith/vendor/griffith/strategy_execution.py` | `desk/vendor/griffith/strategy_execution.py` |  |
| `sleeves/griffith/vendor/griffith/strategy_orchestrator.py` | `desk/vendor/griffith/strategy_orchestrator.py` |  |
| `sleeves/griffith/vendor/griffith/strategy_system.py` | `desk/vendor/griffith/strategy_system.py` |  |
| `sleeves/griffith/vendor/griffith/strategy_tournament.py` | `desk/vendor/griffith/strategy_tournament.py` |  |
| `sleeves/griffith/vendor/griffith/tensor_edge_strategy_spec.json` | `desk/vendor/griffith/tensor_edge_strategy_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json` | `desk/vendor/griffith/tensor_htf_holdout_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_htf_strategy_spec.json` | `desk/vendor/griffith/tensor_htf_strategy_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json` | `desk/vendor/griffith/tensor_htf_weekly_color_forward_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json` | `desk/vendor/griffith/tensor_htf_weekly_color_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json` | `desk/vendor/griffith/tensor_htf_weekly_cyan_spec.json` |  |
| `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json` | `desk/vendor/griffith/tensor_phenotype_registry.json` |  |
| `sleeves/griffith/vendor/griffith/universe.txt` | `desk/vendor/griffith/universe.txt` |  |
| `sleeves/griffith/vendor/griffith/validation_factory.py` | `desk/vendor/griffith/validation_factory.py` |  |
| `sleeves/killed/common.py` | `desk/sleeves/killed/common.py` |  |
| `sleeves/killed/daily.py` | `desk/sleeves/killed/daily.py` |  |
| `sleeves/killed/events.py` | `desk/sleeves/killed/events.py` |  |
| `sleeves/killed/feedlib/killed_data.py` | `desk/feedlib/killed_data.py` |  |
| `sleeves/killed/feedlib/m2.py` | `desk/feedlib/m2.py` | research-box host path neutralised (1) |
| `sleeves/killed/intraday.py` | `desk/sleeves/killed/intraday.py` |  |
| `sleeves/killed/killed_studies.py` | `desk/sleeves/families/killed_studies.py` |  |
| `sleeves/killed/pairs.py` | `desk/sleeves/killed/pairs.py` |  |
| `sleeves/killed/smcap.py` | `desk/sleeves/killed/smcap.py` |  |
| `sleeves/killed/vendor/midna_research/intraday_momentum_2026_10_02.py` | `desk/vendor/midna_research/intraday_momentum_2026_10_02.py` |  |
| `sleeves/killed/vendor/midna_research/pairs_backtest_dev.py` | `desk/vendor/midna_research/pairs_backtest_dev.py` | research-box host path neutralised (1) |
| `sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py` | `desk/vendor/midna_research/run_smcap_beta_52w.py` | research-box host path neutralised (2) |
| `sleeves/killed/vendor/universes/old_desk/basket.json` | `desk/vendor/universes/old_desk/basket.json` | the owner's first name replaced by 'the owner' (24); the owner's first name (lower case, in an id) replaced by 'owner' (1) |
| `sleeves/lazarus/galath_wait.py` | `desk/sleeves/families/galath_wait.py` |  |
| `sleeves/lazarus/galath_wait_feed.py` | `desk/sleeves/families/galath_wait_feed.py` |  |
| `sleeves/lazarus/lazarus.py` | `desk/sleeves/families/lazarus.py` | research-box host path neutralised (2) |
| `sleeves/lazarus/vendor/lazarus/cal.py` | `desk/vendor/lazarus/cal.py` |  |
| `sleeves/lazarus/vendor/lazarus/data.py` | `desk/vendor/lazarus/data.py` |  |
| `sleeves/lazarus/vendor/lazarus/gate.py` | `desk/vendor/lazarus/gate.py` |  |
| `sleeves/lazarus/vendor/lazarus/signals.py` | `desk/vendor/lazarus/signals.py` |  |
| `sleeves/lazarus/vendor/lazarus/sleeves.json` | `desk/vendor/lazarus/sleeves.json` | research-box host path neutralised (2) |
| `sleeves/midna/board.py` | `desk/sleeves/midna/board.py` |  |
| `sleeves/midna/common.py` | `desk/sleeves/midna/common.py` |  |
| `sleeves/midna/context.py` | `desk/sleeves/midna/context.py` |  |
| `sleeves/midna/forward.py` | `desk/sleeves/midna/forward.py` |  |
| `sleeves/midna/forward_scan.py` | `desk/sleeves/midna/forward_scan.py` |  |
| `sleeves/midna/hourly.py` | `desk/sleeves/midna/hourly.py` |  |
| `sleeves/midna/hyperliquid.py` | `desk/sleeves/midna/hyperliquid.py` |  |
| `sleeves/midna/ladder.py` | `desk/sleeves/midna/ladder.py` |  |
| `sleeves/midna/lanes.py` | `desk/sleeves/midna/lanes.py` |  |
| `sleeves/midna/midna.py` | `desk/sleeves/families/midna.py` |  |
| `sleeves/midna/midna_tensor.py` | `desk/sleeves/families/midna_tensor.py` |  |
| `sleeves/midna/qld.py` | `desk/sleeves/midna/qld.py` |  |
| `sleeves/midna/shadow.py` | `desk/sleeves/midna/shadow.py` |  |
| `sleeves/midna/vendor/midna/board_signals.py` | `desk/vendor/midna/board_signals.py` |  |
| `sleeves/milkman/__init__.py` | `desk/sleeves/milkman/__init__.py` |  |
| `sleeves/milkman/daily.py` | `desk/sleeves/milkman/daily.py` |  |
| `sleeves/milkman/galath.py` | `desk/sleeves/milkman/galath.py` |  |
| `sleeves/milkman/intraday.py` | `desk/sleeves/milkman/intraday.py` |  |
| `sleeves/milkman/milkman.py` | `desk/sleeves/families/milkman.py` |  |
| `sleeves/milkman/rules.py` | `desk/sleeves/milkman/rules.py` |  |
| `sleeves/milkman/vendor/milkman/__init__.py` | `desk/vendor/milkman/__init__.py` |  |
| `sleeves/milkman/vendor/milkman/crypto_universe.csv` | `desk/vendor/milkman/crypto_universe.csv` |  |
| `sleeves/milkman/vendor/milkman/dlib.py` | `desk/vendor/milkman/dlib.py` |  |
| `sleeves/milkman/vendor/milkman/dstrats.py` | `desk/vendor/milkman/dstrats.py` |  |
| `sleeves/milkman/vendor/milkman/mlib.py` | `desk/vendor/milkman/mlib.py` | research-box host path neutralised (2) |
| `sleeves/milkman/vendor/milkman/sector_proxy_map.csv` | `desk/vendor/milkman/sector_proxy_map.csv` |  |
| `sleeves/milkman/vendor/milkman/store_v1_1d_index.json` | `desk/vendor/milkman/store_v1_1d_index.json` |  |
| `sleeves/milkman/vendored.py` | `desk/sleeves/milkman/vendored.py` |  |
| `sleeves/muse/__init__.py` | `desk/sleeves/muse/__init__.py` |  |
| `sleeves/muse/core/data.py` | `desk/sleeves/muse/core/data.py` |  |
| `sleeves/muse/core/early_close.py` | `desk/sleeves/muse/core/early_close.py` |  |
| `sleeves/muse/core/em_1587.py` | `desk/sleeves/muse/core/em_1587.py` | research-box host path neutralised (1) |
| `sleeves/muse/core/raschke_rre/__init__.py` | `desk/sleeves/muse/core/raschke_rre/__init__.py` |  |
| `sleeves/muse/core/raschke_rre/admission.py` | `desk/sleeves/muse/core/raschke_rre/admission.py` |  |
| `sleeves/muse/core/raschke_rre/awareness.py` | `desk/sleeves/muse/core/raschke_rre/awareness.py` |  |
| `sleeves/muse/core/raschke_rre/raschke_core.py` | `desk/sleeves/muse/core/raschke_rre/raschke_core.py` |  |
| `sleeves/muse/core/raschke_rre/raschke_engine.py` | `desk/sleeves/muse/core/raschke_rre/raschke_engine.py` |  |
| `sleeves/muse/core/raschke_rre/router.py` | `desk/sleeves/muse/core/raschke_rre/router.py` |  |
| `sleeves/muse/core/saty_bars.py` | `desk/sleeves/muse/core/saty_bars.py` |  |
| `sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py` | `desk/sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py` | the owner's first name replaced by 'the owner' (1) |
| `sleeves/muse/core/saty_gpt_v02/risk_lots.py` | `desk/sleeves/muse/core/saty_gpt_v02/risk_lots.py` |  |
| `sleeves/muse/core/saty_gpt_v02/strategies.py` | `desk/sleeves/muse/core/saty_gpt_v02/strategies.py` |  |
| `sleeves/muse/core/saty_gpt_v03/risk_lots.py` | `desk/sleeves/muse/core/saty_gpt_v03/risk_lots.py` |  |
| `sleeves/muse/core/saty_gpt_v03/routing.py` | `desk/sleeves/muse/core/saty_gpt_v03/routing.py` |  |
| `sleeves/muse/core/saty_gpt_v03/strategies.py` | `desk/sleeves/muse/core/saty_gpt_v03/strategies.py` |  |
| `sleeves/muse/core/saty_indicators.py` | `desk/sleeves/muse/core/saty_indicators.py` | research-box host path neutralised (1) |
| `sleeves/muse/core/saty_primitives.py` | `desk/sleeves/muse/core/saty_primitives.py` | research-box host path neutralised (1) |
| `sleeves/muse/core/saty_reference.py` | `desk/sleeves/muse/core/saty_reference.py` |  |
| `sleeves/muse/core/sleeve.py` | `desk/sleeves/muse/core/sleeve.py` | the owner's first name replaced by 'the owner' (1) |
| `sleeves/muse/muse.py` | `desk/sleeves/families/muse.py` |  |
| `sleeves/muse/sleeves/po10_qqq.py` | `desk/sleeves/muse/sleeves/po10_qqq.py` |  |
| `sleeves/muse/sleeves/raschke_pf3.py` | `desk/sleeves/muse/sleeves/raschke_pf3.py` | the owner's first name replaced by 'the owner' (3) |
| `sleeves/quant_research/airt.py` | `desk/sleeves/quant_research/airt.py` |  |
| `sleeves/quant_research/alphagen_np.py` | `desk/sleeves/quant_research/alphagen_np.py` |  |
| `sleeves/quant_research/alphaqcm.py` | `desk/sleeves/quant_research/alphaqcm.py` |  |
| `sleeves/quant_research/bolt.py` | `desk/sleeves/quant_research/bolt.py` |  |
| `sleeves/quant_research/carm.py` | `desk/sleeves/quant_research/carm.py` |  |
| `sleeves/quant_research/cer.py` | `desk/sleeves/quant_research/cer.py` |  |
| `sleeves/quant_research/common.py` | `desk/sleeves/quant_research/common.py` |  |
| `sleeves/quant_research/cqr.py` | `desk/sleeves/quant_research/cqr.py` |  |
| `sleeves/quant_research/crd.py` | `desk/sleeves/quant_research/crd.py` |  |
| `sleeves/quant_research/crg.py` | `desk/sleeves/quant_research/crg.py` |  |
| `sleeves/quant_research/dropout_book.py` | `desk/sleeves/quant_research/dropout_book.py` |  |
| `sleeves/quant_research/factor_books.py` | `desk/sleeves/quant_research/factor_books.py` |  |
| `sleeves/quant_research/fastnumbers.py` | `desk/sleeves/quant_research/fastnumbers.py` |  |
| `sleeves/quant_research/feedlib/edgar_buyback.py` | `desk/feedlib/edgar_buyback.py` |  |
| `sleeves/quant_research/finrlx.py` | `desk/sleeves/quant_research/finrlx.py` |  |
| `sleeves/quant_research/lgbm_text.py` | `desk/sleeves/quant_research/lgbm_text.py` |  |
| `sleeves/quant_research/news121.py` | `desk/sleeves/quant_research/news121.py` |  |
| `sleeves/quant_research/quant_research.py` | `desk/sleeves/families/quant_research.py` |  |
| `sleeves/quant_research/r10.py` | `desk/sleeves/quant_research/r10.py` |  |
| `sleeves/quant_research/relay.py` | `desk/sleeves/quant_research/relay.py` |  |
| `sleeves/quant_research/scores.py` | `desk/sleeves/quant_research/scores.py` |  |
| `sleeves/quant_research/sed.py` | `desk/sleeves/quant_research/sed.py` |  |
| `sleeves/quant_research/sixai.py` | `desk/sleeves/quant_research/sixai.py` |  |
| `sleeves/quant_research/tcft.py` | `desk/sleeves/quant_research/tcft.py` |  |
| `sleeves/quant_research/uir.py` | `desk/sleeves/quant_research/uir.py` |  |
| `sleeves/quant_research/vendor/old_desk_research/structural_screen.py` | `desk/vendor/old_desk_research/structural_screen.py` | the owner's first name replaced by 'the owner' (2) |
| `sleeves/quant_research/vendor/quant_research/fastnumbers/prepare_events.py` | `desk/vendor/quant_research/fastnumbers/prepare_events.py` |  |
| `sleeves/quant_research/vendor/quant_research/fastnumbers/run_reconstruction.py` | `desk/vendor/quant_research/fastnumbers/run_reconstruction.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/airt/code/vendor/airt_r1.py` | `desk/vendor/quant_research/r10/airt/code/vendor/airt_r1.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/bolt/admission.py` | `desk/vendor/quant_research/r10/bolt/admission.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/carm/code/reference_kernel.py` | `desk/vendor/quant_research/r10/carm/code/reference_kernel.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/cer/reference_kernel_r10.py` | `desk/vendor/quant_research/r10/cer/reference_kernel_r10.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/cqr/queue_delta_r10.py` | `desk/vendor/quant_research/r10/cqr/queue_delta_r10.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/crd/crd_r10.py` | `desk/vendor/quant_research/r10/crd/crd_r10.py` |  |
| `sleeves/quant_research/vendor/quant_research/r10/tcft/code/execution.py` | `desk/vendor/quant_research/r10/tcft/code/execution.py` |  |
| `sleeves/quant_research/vendor/quant_research/sed/engine.py` | `desk/vendor/quant_research/sed/engine.py` |  |
| `sleeves/quant_research/vendor/quant_research/sixai/shared/dropout.py` | `desk/vendor/quant_research/sixai/shared/dropout.py` |  |
| `sleeves/qullamaggie/qullamaggie.py` | `desk/sleeves/families/qullamaggie.py` |  |
| `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py` | `desk/vendor/qullamaggie_pass3/desk_fixed.py` |  |
| `sleeves/sable/desk_scanner.py` | `desk/sleeves/sable/desk_scanner.py` |  |
| `sleeves/sable/feedlib/yahoo_spark.py` | `desk/feedlib/yahoo_spark.py` |  |
| `sleeves/sable/jsport.py` | `desk/sleeves/jsport.py` |  |
| `sleeves/sable/location_first.py` | `desk/sleeves/sable/location_first.py` |  |
| `sleeves/sable/runtime.py` | `desk/sleeves/sable/runtime.py` |  |
| `sleeves/sable/sable.py` | `desk/sleeves/families/sable.py` |  |
| `sleeves/sable/vendor/sable/catalog.mjs` | `desk/vendor/sable/catalog.mjs` |  |
| `sleeves/sable/vendor/sable/universe.ts` | `desk/vendor/sable/universe.ts` |  |
| `sleeves/span/feedlib/polymarket.py` | `desk/feedlib/polymarket.py` |  |
| `sleeves/span/prediction_markets.py` | `desk/sleeves/families/prediction_markets.py` |  |
| `sleeves/span/vendor/span_harvest/span_harvest_unified.py` | `desk/vendor/span_harvest/span_harvest_unified.py` |  |
| `sleeves/tensor_research/feedlib/canonical.py` | `desk/feedlib/canonical.py` |  |
| `sleeves/tensor_research/feedlib/canonical_alpaca.py` | `desk/feedlib/canonical_alpaca.py` |  |
| `sleeves/tensor_research/feedlib/tensor.py` | `desk/feedlib/tensor.py` |  |
| `sleeves/tensor_research/feedlib/tensor_features.py` | `desk/feedlib/tensor_features.py` |  |
| `sleeves/tensor_research/feedlib/tensor_research.mjs` | `desk/feedlib/tensor_research.mjs` |  |
| `sleeves/tensor_research/feedlib/tensor_research.py` | `desk/feedlib/tensor_research.py` |  |
| `sleeves/tensor_research/feedlib/tensor_research_hands.mjs` | `desk/feedlib/tensor_research_hands.mjs` |  |
| `sleeves/tensor_research/tensor_research.py` | `desk/sleeves/families/tensor_research.py` |  |
