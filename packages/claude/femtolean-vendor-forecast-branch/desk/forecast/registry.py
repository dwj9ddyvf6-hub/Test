"""The forecaster registry: id -> (Forecaster contract, its compute group). A group enters only after the law checker
passes every one of its forecasters (laws.check); a forecaster that fails a law cannot be registered.

  register(compute, forecasters)   checks the laws, then adds the group; LawError names each failure
  declared()                       every adapter's (compute, forecasters) as declared, before any check
  build(histories)                 a Registry holding every declared group that passes (it raises on the first that
                                   does not, so a broken adapter is never silently left out)"""
from . import Forecaster
from . import laws as L


class LawError(ValueError):
    pass


class Registry:
    def __init__(self):
        self.forecasters, self.compute = {}, {}

    def register(self, compute, forecasters, histories=L.HISTORIES, check=True):
        fs = list(forecasters)
        for f in fs:
            if not isinstance(f, Forecaster):
                raise LawError(f"{f!r} is not a Forecaster contract")
            if f.id in self.forecasters:
                raise LawError(f"{f.id} is already registered")
        if check:
            fails = L.check(compute, fs, histories)
            bad = {k: v for k, v in fails.items() if v}
            if bad:
                raise LawError("; ".join(f"{k}: {v[0]}" for k, v in sorted(bad.items())))
        for f in fs:
            self.forecasters[f.id] = f
            self.compute[f.id] = compute
        return [f.id for f in fs]

    def __contains__(self, fid):
        return fid in self.forecasters

    def __getitem__(self, fid):
        return self.forecasters[fid]

    def ids(self):
        return sorted(self.forecasters)


    def register_derived(self, fid):
        """a cross-sectional derived forecaster (xs.py): every input registered first, then its own check"""
        from . import xs
        f = next(x for x in xs.FORECASTERS if x.id == fid)
        miss = [i for i in f.inputs if i not in self.forecasters]
        if miss:
            raise LawError(f"{fid}: inputs not registered: {miss}")
        fails = xs.check(fid)
        if fails:
            raise LawError(f"{fid}: {fails[0]}")
        self.forecasters[fid] = f
        self.compute[fid] = None
        return fid


P1_GROUPS = ("picker", "odds", "engine", "avoid", "features")
P2_GROUPS = ("survivors", "regime", "vendors", "vendors2", "vendors3")


def declared(groups=P1_GROUPS + P2_GROUPS):
    import importlib
    return [(m.compute, m.FORECASTERS) for m in
            (importlib.import_module(f"desk.forecast.adapters.{g}") for g in groups)]


def build(histories=L.HISTORIES, groups=P1_GROUPS + P2_GROUPS, derived=True):
    reg = Registry()
    for compute, fs in declared(groups):
        reg.register(compute, fs, histories)
    if derived:
        from . import xs
        for f in xs.FORECASTERS:
            if all(i in reg for i in f.inputs):
                reg.register_derived(f.id)
    return reg
