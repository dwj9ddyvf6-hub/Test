# Ausar-archive rulebooks and forward recipe engine - Algorithm

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/codex-complete-archive (archive source, Agentic-Trading-Desk aurelia-paper-desk payload); the copies packaged here are the ported copies in the local femto-lean desk tree, which the index records as the working home.

## What it is

Two recovered rulebooks plus the recovered forward recipe engine, ported into the lean desk on 2026-10-15 (EA2a/EA2b):

- Rulebooks: config/options_rules.json (the archive options_rules.json) and config/aurelia_free_etf_rules.json (the archive strategies/r19/etf_rules.json), 36 rulebooks covering 26 sleeves, kept verbatim-shaped with the source's own monitor verdicts for the five free_opt books. core/etf_feeds.py (EtfProducer) serves all 26 ETF books through the verbatim r19_etf.select backend; core/options_feeds.py (OptionsProducer) supplies each free_opt sleeve's rulebook_book and the pair sleeve's frozen hedge. Sleeve carriers: sleeves/free_etf.py and the six sleeves/free_opt_*.py modules.
- Forward recipe engine: core/recipe_features.py is the recovered public-recipe feature engine (indicator helpers sma/ema/rma/rsi/atr, DEFAULTS, source_features, and the make_config parameter merge with unknown params rejected), differential-tested equal to the archive original. It serves the three public recipes (ai_volume, iu_body, tomazetti_rsi2) consumed by sleeves/fwd_alpaca_link_ai_volume.py, sleeves/fwd_alpaca_enj_iu_body.py, and sleeves/fwd_alpaca_ada_rsi2.py through core/crypto_feeds.py (FwdProducer). Bars are the source shape: dicts with open_at/close_at ISO times and open/high/low/close/volume.

## Files in this package

- `packages/ausar/ausar-archive-rulebooks/config/options_rules.json`
- `packages/ausar/ausar-archive-rulebooks/config/aurelia_free_etf_rules.json`
- `packages/ausar/ausar-archive-rulebooks/core/etf_feeds.py`
- `packages/ausar/ausar-archive-rulebooks/core/options_feeds.py`
- `packages/ausar/ausar-archive-rulebooks/core/crypto_feeds.py`
- `packages/ausar/ausar-archive-rulebooks/core/recipe_features.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_etf.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_own_iv.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_pair.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_parity.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_release.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_tail.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/free_opt_wheel.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/fwd_alpaca_ada_rsi2.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/fwd_alpaca_enj_iu_body.py`
- `packages/ausar/ausar-archive-rulebooks/sleeves/fwd_alpaca_link_ai_volume.py`
