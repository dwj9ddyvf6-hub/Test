"""The Milkman v2 study's own daily code, vendored byte-exact (desk/vendor/milkman/: mlib.py 0e488ae7, dlib.py 026fbc64,
dstrats.py c1845e96 — quant-research-critical@0be4c575 milkman-study/v2/code) and loaded the way the study loaded it:
from its own directory, `from mlib import *` / `from dlib import *`.

dlib decorates its exit engines with numba's @njit (a compiler: the same Python semantics, compiled). numba is not a
desk dependency; when it is absent a stand-in module whose njit returns the function unchanged is registered, so
the engines run as the identical Python code."""
import importlib
import importlib.machinery
import importlib.util
import json
import os
import sys
import types

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor", "milkman")
_MODS = {}


def _numba_standin():
    if "numba" in sys.modules:                 # the real numba, or the stand-in registered by an earlier load
        return
    try:
        if importlib.util.find_spec("numba") is not None:
            return
    except (ImportError, ValueError):
        return
    nb = types.ModuleType("numba")
    nb.__spec__ = importlib.machinery.ModuleSpec("numba", None)   # find_spec("numba") stays answerable

    def njit(*a, **k):
        if a and callable(a[0]) and not k:
            return a[0]
        return lambda f: f
    nb.njit = njit
    nb.__desk_standin__ = True
    sys.modules["numba"] = nb


def load(name):
    """mlib / dlib / dstrats, imported from the vendor directory (their own sibling imports resolve there)."""
    if name not in _MODS:
        _numba_standin()
        if VENDOR not in sys.path:
            sys.path.insert(0, VENDOR)
        _MODS[name] = importlib.import_module(name)
        if os.path.dirname(os.path.abspath(_MODS[name].__file__)) != VENDOR:
            raise ImportError(f"{name} resolved outside the vendored milkman directory: {_MODS[name].__file__}")
    return _MODS[name]


def dstrats():
    return load("dstrats")


def univ_symbols():
    """the study's stock universe on this desk: the store_v1 1d survivors (galath-research/real_engine/store_v1/1d
    _index.json, quant-research-backup@d170596b blob 6ffe865c), sorted."""
    j = json.load(open(os.path.join(VENDOR, "store_v1_1d_index.json")))
    return tuple(sorted(j["files"]))
