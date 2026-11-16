"""FORECAST-FACTORY-20261027 blockers: Claude's Forecast Factory core
(contracts, laws, registry, score, gates, freeze, xs, capacity, data,
costs, contexts) ported into desk3/forecast/ as ADVISORY validation
tooling (EXECUTE-SCOPE-2026-10-27 item 1; provenance and the deferred
adapters list live in desk3/forecast/PROVENANCE.md).

Fail directions (each proven at landing by temporary breakage):
  - a contract accepting an invalid target kind / sign -> red
  - a law-violating (look-ahead) compute registering -> red
  - the scorer losing its embargo or BH control -> red
  - any production path outside desk3/forecast importing the package
    (wiring it into dispatch or a sleeve decision) -> red
  - a byte-exact vendored module drifting from its manifest sha -> red
"""
import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from desk3.forecast import (CONTRACT, ContractError, Forecaster, Laws,
                            Ledger, Target)  # noqa: E402
from desk3.forecast import capacity, contexts, costs, data, freeze  # noqa: E402,F401
from desk3.forecast import gates, laws, registry, score, xs  # noqa: E402,F401

BYTE_EXACT = {
    "__init__.py": "793dabf0fa3155dbaf3499818c9f8840b59ecd4e7983c1f0addd1356b2c3a04f",
    "capacity.py": "e34cac13e699b29b4a48fe0b07e0df42c4cc2fdd7994b603168d8f568e1c062e",
    "contexts.py": "47d79bd1ad57393393522d035809690305aca256cfe675f0c6c9c3c32e07897d",
    "costs.py": "1c50b36403d2b22a06084f559ae471183093423da163fc5c4b95804a574177a8",
    "data.py": "95a31db16cc75824f04ff314c7743ef2f33286f6cb166b7f48015cc83cf64b08",
    "freeze.py": "800a1b344f88a702dd8bd46f537be01b4d857559b16d86f16a2467d456fd0079",
    "gates.py": "b356f306aa9ebfbc89b9810fe2d9103c65ea0f7dbfc1eca0eb6ab114d006a60a",
    "xs.py": "acec16c61a411163aa5490c3e9ade80226ee9f8f0724c0d8223218cc1127aed1",
    "REGISTRY.md": "402e90e963163de755740cda82fc589d83e9660e782ea261a0dbaf5811387403",
}


def _forecaster(fid="toy.r1", bounded=(-1.0, 1.0)):
    return Forecaster(id=fid, version="t1", kind="score",
                      owner_module="tests.toy", family="toy",
                      targets=("up_excess_20",),
                      laws=Laws(bounded=bounded, abstains=True),
                      ledger=Ledger())


def _toy_compute(a, mkt):
    """point-in-time, deterministic, bounded: 5d momentum sign, scaled."""
    c = np.asarray(a["c"], float)
    out = np.full(len(c), np.nan)
    if len(c) > 5:
        out[5:] = np.clip((c[5:] / c[:-5]) - 1.0, -1.0, 1.0)
    return {"toy.r1": out}


def _lookahead_compute(a, mkt):
    """violates point_in_time: value at t reads the final close."""
    c = np.asarray(a["c"], float)
    return {"toy.r1": np.full(len(c), float(c[-1] / c[0] - 1.0))}


def test_contracts_validate():
    assert CONTRACT == "forecast-1"
    t = Target(id="up20", kind="up_excess", horizon_d=20)
    assert t.loss == "rank_ic"
    for bad in (lambda: Target(id="x", kind="nope", horizon_d=1),
                lambda: Forecaster(id="x", version="1", kind="score",
                                   owner_module="m", family="f",
                                   targets=("up_excess_20",),
                                   laws=Laws(), sign=0)):
        try:
            bad()
        except ContractError:
            pass
        else:
            raise AssertionError("invalid contract accepted")


def test_vendored_hashes_match_manifest():
    root = os.path.join(HERE, "desk3", "forecast")
    for name, want in BYTE_EXACT.items():
        got = hashlib.sha256(open(os.path.join(root, name), "rb").read()).hexdigest()
        assert got == want, f"{name} drifted from its vendored source: {got}"


def test_registry_enforces_laws():
    reg = registry.Registry()
    ids = reg.register(_toy_compute, [_forecaster()], histories=3)
    assert ids == ["toy.r1"] and "toy.r1" in reg
    reg2 = registry.Registry()
    try:
        reg2.register(_lookahead_compute, [_forecaster()], histories=3)
    except registry.LawError:
        pass
    else:
        raise AssertionError("look-ahead forecaster registered: laws not enforced")
    try:
        reg.register(_toy_compute, [_forecaster()], histories=1)
    except registry.LawError:
        pass
    else:
        raise AssertionError("duplicate id registered")


def test_score_embargo_and_bh():
    dates = [f"2024-01-{d:02d}" for d in range(1, 29)] + \
            [f"2024-02-{d:02d}" for d in range(1, 29)]
    disc, hold, split = score.split_dates(dates, split="2024-02-01")
    assert split == "2024-02-01"
    assert not disc[len(dates) - 28 - 10]  # within 45d embargo of the split
    assert hold[-1] and not hold[0]
    assert score.EMBARGO_DAYS == 45 and score.Q == 0.10
    assert score._bh([0.001, 0.04, 0.5], 0.10) == [True, True, False]
    qs = score._qvalues({0: 0.001, 1: 0.04, 2: 0.5})
    assert qs[0] < qs[1] < qs[2]
    rng = np.random.default_rng(7)
    x = np.tile(rng.normal(size=30), 40)
    y = x + rng.normal(0, 0.01, size=len(x))
    dts = np.repeat([f"2024-03-{d:02d}" for d in range(1, 31)], 40)
    ud, ic, n = score.ic_by_date(x, y, dts)
    assert len(ud) == 30 and np.all(ic > 0.9) and np.all(n == 40)


def test_freeze_roundtrip_and_xs_bounds():
    payload = {"a": [1, 2, 3]}
    assert freeze.sha256(payload) == freeze.sha256({"a": [1, 2, 3]})
    for f in xs.FORECASTERS:
        lo, hi = f.laws.bounded
        assert lo <= hi


def test_advisory_only_no_production_imports():
    """The factory is advisory: no production module outside
    desk3/forecast may import it (dispatch and sleeves stay clean)."""
    offenders = []
    for root, _dirs, files in os.walk(HERE):
        rel = os.path.relpath(root, HERE)
        if rel.startswith(os.path.join("desk3", "forecast")) or \
                "__pycache__" in rel or rel.startswith(".git") or \
                rel.startswith("tests") or rel.startswith(".gate_tmp"):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            txt = open(os.path.join(root, fn), errors="ignore").read()
            if "desk3.forecast" in txt or "desk3 import forecast" in txt:
                offenders.append(os.path.join(rel, fn))
    assert not offenders, f"forecast factory wired into production: {offenders}"
