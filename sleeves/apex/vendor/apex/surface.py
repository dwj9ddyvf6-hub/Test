"""The model implied-volatility surface (desk/options/surface.py). PARAMS_PATH (source line 22, which
resolves next to the source tree's research/results) points at the vendored, byte-exact
surface_params.json of the same commit.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .series import aligned_close

PARAMS_PATH = Path(__file__).resolve().parent / "surface_params.json"


# >>> excerpt desk/options/surface.py lines 25-101 blob 0934f4b63e106f499ffaf72469398f989f4143e7 sha256 64ec9a1668e1e32c01cc37db44d9cd4109cf1a87a8ee12fa7ddcea387b84603b
@dataclass
class SurfaceParams:
    ts_gamma: float = 0.5
    m_grid: list = field(default_factory=lambda: [-4.0, -2.0, 0.0, 2.0, 3.0])
    t_grid: list = field(default_factory=lambda: [10.0, 30.0, 110.0])
    table: list = field(default_factory=lambda: [[1.25] * 3, [1.1] * 3, [0.9] * 3, [0.8] * 3, [0.85] * 3])
    level_shift: float = 0.0  # additive vol points (decimal) for stress tests
    ts_fallback: dict = field(default_factory=lambda: {"vix9d": [0.0, 0.15], "vix3m": [0.08, -0.17], "vix6m": [0.15, -0.31]})

    def save(self, path: Path = PARAMS_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=1))

    @classmethod
    def load(cls, path: Path = PARAMS_PATH) -> "SurfaceParams":
        if not path.exists():
            return cls()
        d = json.loads(path.read_text())
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def _interp_table(m: np.ndarray, Td: np.ndarray, m_grid: np.ndarray, t_grid: np.ndarray, table: np.ndarray) -> np.ndarray:
    mc = np.clip(m, m_grid[0], m_grid[-1])
    tc = np.clip(Td, t_grid[0], t_grid[-1])
    i = np.clip(np.searchsorted(m_grid, mc) - 1, 0, len(m_grid) - 2)
    j = np.clip(np.searchsorted(t_grid, tc) - 1, 0, len(t_grid) - 2)
    wm = (mc - m_grid[i]) / (m_grid[i + 1] - m_grid[i])
    wt = (tc - t_grid[j]) / (t_grid[j + 1] - t_grid[j])
    a = table[i, j] * (1 - wt) + table[i, j + 1] * wt
    b = table[i + 1, j] * (1 - wt) + table[i + 1, j + 1] * wt
    return a * (1 - wm) + b * wm


class Surface:
    def __init__(self, index: pd.DatetimeIndex, vol30_symbol: str = "^VXN", params: SurfaceParams | None = None,
                 vol30_fallback: pd.Series | None = None):
        self.index = index
        self.p = params or SurfaceParams.load()
        vol30 = aligned_close(vol30_symbol, index) / 100.0
        if vol30_fallback is not None:
            vol30 = vol30.where(vol30.notna(), vol30_fallback.reindex(index))
        self.vol30 = vol30
        vix = aligned_close("^VIX", index) / 100.0
        self.ratios = {}
        for key, sym in (("vix9d", "^VIX9D"), ("vix3m", "^VIX3M"), ("vix6m", "^VIX6M")):
            raw = aligned_close(sym, index) / 100.0
            first = raw.first_valid_index()
            ratio = raw / vix
            if first is not None:
                ratio[ratio.index < first] = np.nan
            a, b = self.p.ts_fallback[key]
            fallback = np.exp(a + b * np.log((vix / 0.20).clip(lower=0.05)))
            self.ratios[key] = ratio.where(ratio.notna(), fallback).clip(0.3, 2.5).fillna(1.0)
        self._m = np.asarray(self.p.m_grid, dtype=float)
        self._t = np.asarray(self.p.t_grid, dtype=float)
        self._tab = np.asarray(self.p.table, dtype=float)
        self._v = self.vol30.to_numpy(dtype=float)
        self._r = np.column_stack([self.ratios["vix9d"].to_numpy(), np.ones(len(index)),
                                   self.ratios["vix3m"].to_numpy(), self.ratios["vix6m"].to_numpy()])

    def ref_vol(self, t: int, T) -> np.ndarray:
        v = self._v[t]
        days = np.array([9.0, 30.0, 93.0, 183.0])
        rat = self._r[t] ** self.p.ts_gamma
        w = (v * rat) ** 2 * days / 365.0
        Td = np.clip(np.asarray(T, dtype=float) * 365.0, 1.0, None)
        wT = np.interp(Td, days, w)
        wT = np.where(Td < days[0], (v * rat[0]) ** 2 * Td / 365.0, wT)
        wT = np.where(Td > days[-1], (v * rat[-1]) ** 2 * Td / 365.0, wT)
        return np.sqrt(wT / (Td / 365.0))

    def iv(self, t: int, K, F, T) -> np.ndarray:
        K, F, T = (np.asarray(x, dtype=float) for x in (K, F, T))
        ref = self.ref_vol(t, T)
        m = np.log(K / F) / (ref * np.sqrt(np.maximum(T, 1e-6)))
        g = _interp_table(m, np.asarray(T * 365.0), self._m, self._t, self._tab)
        return np.maximum(ref * g + self.p.level_shift, 0.03)
