"""The muse-week sleeves (owner, 2026-10-25: "I want you to add the new 12 sleeves"), vendored byte for byte.

Layout = the source layout: sleeves/<name>.py are the strategy files and core/... the femto-lean core modules they
import (the indicator port, the saty_gpt_v02 / saty_gpt_v03 / raschke_rre engines, the sleeve contract). Every file is
the pinned source blob, unedited; PROVENANCE.json names its repo, ref, commit, path, git blob and sha256
(tests/test_muse_provenance.py holds the bytes to it). The execution adapter is desk/sleeves/families/muse.py.

The source files import their core as the top-level package `core` (`from core.sleeve import Intent`,
`from core import saty_bars as sb`, and inside functions too). Rather than rewrite a byte, the vendored modules load
under this package's own names (desk.sleeves.muse.core.saty_bars, desk.sleeves.muse.sleeves.saty_sol) with a
private import function: in their globals `__builtins__.__import__` maps an absolute `core` / `core.X` to
desk.sleeves.muse.core / desk.sleeves.muse.core.X and passes every other import through unchanged. Nothing is
aliased in sys.modules, so no other `core` (the femto tests' shim, for one) can shadow these modules or be shadowed
by them, and a function-level `from core import ...` resolves the same way at call time."""
import builtins
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = __name__                                  # desk.sleeves.muse
ROOTS = ("core", "sleeves")                        # the vendored trees under this package
_real_import = builtins.__import__


def _scoped_import(name, globals=None, locals=None, fromlist=(), level=0):
    """__import__ for the vendored modules: an absolute `core` import resolves inside this package."""
    if level == 0 and (name == "core" or name.startswith("core.")):
        mod = _real_import(PREFIX + "." + name, globals, locals, fromlist, 0)
        return mod if fromlist else sys.modules[PREFIX + ".core"]   # `import core.x` binds the package `core`
    return _real_import(name, globals, locals, fromlist, level)


SCOPED_BUILTINS = dict(builtins.__dict__, __import__=_scoped_import)


class _ScopedLoader(importlib.machinery.SourceFileLoader):
    def exec_module(self, module):
        module.__builtins__ = SCOPED_BUILTINS          # the module's functions inherit it from their globals
        super().exec_module(module)


class _ScopedFinder(importlib.abc.MetaPathFinder):
    """finds desk.sleeves.muse.core[.*] and desk.sleeves.muse.sleeves[.*] (and nothing else) in this folder."""

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(PREFIX + "."):
            return None
        rel = fullname[len(PREFIX) + 1:].split(".")
        if rel[0] not in ROOTS:
            return None
        base = os.path.join(HERE, *rel)
        if os.path.isfile(os.path.join(base, "__init__.py")):
            init = os.path.join(base, "__init__.py")
            return importlib.util.spec_from_file_location(fullname, init, loader=_ScopedLoader(fullname, init),
                                                          submodule_search_locations=[base])
        if os.path.isfile(base + ".py"):
            return importlib.util.spec_from_file_location(fullname, base + ".py",
                                                          loader=_ScopedLoader(fullname, base + ".py"))
        return None


if not any(isinstance(f, _ScopedFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _ScopedFinder())


def strategy_module(name):
    """the vendored strategy module sleeves/<name>.py (the import also binds the attribute `sleeves` here)"""
    return importlib.import_module(PREFIX + ".sleeves." + name)


def core_module(name):
    """a vendored core module, e.g. core_module("sleeve") -> desk.sleeves.muse.core.sleeve"""
    return importlib.import_module(PREFIX + ".core." + name)
