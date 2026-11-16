# Forecast Factory port: provenance (2026-10-27)

Source: Femto-lean repo, branch `factory-p3`, `desk/forecast/` (Claude's
Forecast Factory), fetched via the program manifest at
`~/workspace/peer-execute-20261027/sources/MANIFEST.json` (group
`a_factory`). Installed under EXECUTE-SCOPE-2026-10-27 item 1 as
ADVISORY validation tooling only: nothing in dispatch, any sleeve,
sizing, or order path imports this package (guarded by
`tests/test_forecast_factory_20261027_blockers.py`).

## Landed byte-exact (sha256 equals the manifest)

- `__init__.py` 793dabf0fa3155dbaf3499818c9f8840b59ecd4e7983c1f0addd1356b2c3a04f (contracts: Forecaster, Target, Context, Laws, Ledger, Forecast, Score)
- `capacity.py` e34cac13e699b29b4a48fe0b07e0df42c4cc2fdd7994b603168d8f568e1c062e
- `contexts.py` 47d79bd1ad57393393522d035809690305aca256cfe675f0c6c9c3c32e07897d
- `costs.py` 1c50b36403d2b22a06084f559ae471183093423da163fc5c4b95804a574177a8
- `data.py` 95a31db16cc75824f04ff314c7743ef2f33286f6cb166b7f48015cc83cf64b08
- `freeze.py` 800a1b344f88a702dd8bd46f537be01b4d857559b16d86f16a2467d456fd0079
- `gates.py` b356f306aa9ebfbc89b9810fe2d9103c65ea0f7dbfc1eca0eb6ab114d006a60a
- `xs.py` acec16c61a411163aa5490c3e9ade80226ee9f8f0724c0d8223218cc1127aed1
- `REGISTRY.md` 402e90e963163de755740cda82fc589d83e9660e782ea261a0dbaf5811387403

## Landed with minimal import adaptation (marked PORT-ADAPT in-file)

- `laws.py`: `from .. import calendar as cal` becomes
  `from core import data as cal` (muse-desk-v3's own trading calendar;
  only `cal.is_trading_day` is used).
- `registry.py`: `declared()` builds `desk3.forecast.adapters.*` module
  paths instead of `desk.forecast.adapters.*`. The Registry class and
  law-check-on-register behavior are unchanged.
- `score.py`: Femto-lean's `desk.lab.stats` and `desk.picker.model` do
  not exist in muse-desk-v3. The three helpers used are local
  equivalents: `_t_sf` (Student-t survival function via scipy),
  `_bh` / `_qvalues` (Benjamini-Hochberg step-up). Constants
  `EMBARGO_DAYS = 45` and `Q = 0.10` are the values frozen in the same
  source package (`desk/forecast/search.py` lines 57-58).

## Deferred (OPEN, by name)

Not landed in this pass because they import Femto-lean desk modules
that have no muse-desk-v3 counterpart (`desk.picker`, `desk.odds`,
`desk.analysis`, `desk.lab`, `desk.ai`, `desk.terminal.odds`,
`desk.record_ext`, `desk.util`, `desk.calendar`):

- `adapters/` (all: _common, avoid, engine, features, odds, picker,
  regime, survivors, vendors, vendors2). Until they land,
  `registry.declared()` / `registry.build()` raise ModuleNotFoundError
  rather than silently registering a partial set.
- `search.py`, `search_deep.py`, `today.py`, `operator.py`,
  `portfolio.py`, `router.py`, `replicate.py`,
  `cards.py`, `promoted.py`, `targets.py`, `frozen/` artifacts.

## Ensemble addendum (2026-10-27, EXECUTE-SCOPE item 6)

Landed after this phase, as an advisory report generator only (no
book, OMS, dispatcher, or sleeve path imports it; guarded by
`tests/test_sleeve_ensemble_20261027_blockers.py`):

- `ensemble.py`: vendored from Femto-lean `desk/forecast/ensemble.py`
  (factory-p3, sha256 1aad409a570308de944c1e22443fe4f12832b6b8cb68f05ff43cdef4db08f890).
  Logic byte-identical below the header; three imports adapted
  (PORT-ADAPT in-file): `core.data` as the calendar, the local
  `evidence.py` below for `desk.learn.evidence`, and
  `ZoneInfo("America/New_York")` for ET.
- `evidence.py`: local equivalent of Femto-lean `desk/learn/evidence.py`
  (no v3 counterpart), implementing only the surfaces the ensemble
  uses (psr, expected_max_sr, _q, MIN_RETURNS=20) from the published
  Bailey & Lopez de Prado formulas.
- `sleeve_ensemble.py`: the CLI tool, vendored from Femto-lean
  `tools/sleeve_ensemble.py` (sha256 9a8d80dde58ecc65d934ce96b5ef8b4c8cfdfe44a7d1f9b8549dc72c02719f38),
  adapted: `--ref` git mode dropped (no desk-state branch here), the
  report page's short-record wording is driven by the report's own
  low-confidence flags, and a `--v3-state` probe mode reads
  muse-desk-v3's actual forward record read-only.
- Run of 2026-10-27: the v3 record cannot feed the ensemble honestly
  (no per-sleeve equity curves; 1 in-epoch session, 13 fills, 8
  sleeves). Evidence: `~/workspace/peer-execute-20261027/ENSEMBLE-RUN-2026-10-27.md`.
  OPEN by name: V3-BOOKS-RECORD (no per-sleeve daily equity/P&L record
  exists in v3 for any ensemble-class tool to read).
