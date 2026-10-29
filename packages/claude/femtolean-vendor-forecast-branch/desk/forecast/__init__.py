"""The Forecast Factory (FACTORY.md, phase P1): contracts, a registry, target labels, a scorer, and adapters that wrap
the desk's existing pieces as forecasters.

SCOPE (InfinityBlade, 2026-10-27)
  Surface      desk/forecast/ (this package), tools/forecast_search.py, tests/test_forecast_*.py. Nothing else changes.
  Constraints  counterfactual and advisory: no sleeve, OMS, order, size or book module imports desk.forecast
               (tests/test_forecast_guard.py); point in time on closed bars (a decision at the close of d fills at the
               open of d+1); thresholds learned on discovery only and frozen with a sha256 pin (freeze.py); every name,
               no price or volume floor (a floor is a reproduction setting only, named as such); a bad-print guard
               (data.guard); wrapped modules are imported, never copied or edited (picker, odds, analysis).
  Outcome      every forecaster declares its contract and its laws; the scorer gives per-date IC, Newey-West t over
               dates, discovery/holdout with the embargo, BH over a run; the replay table and the fear-day IC reproduce.
  Proof        tests/test_forecast_*.py; tools/forecast_search.py --replay / --fear (numbers in its report).
  Edges        the split-adjusted daily cache (cache/bars.tar.xz alpaca_split/1d, a directory of the same JSON, or
               DEEP's bars.parquet through a config path); Cboe's VIX file; host CPU and disk.

Contracts (JSON, version CONTRACT = "forecast-1"): Forecaster, Target, Context, Forecast and Score below. Every
Forecaster declares its laws (point_in_time, deterministic, bounded, costed); registry.register refuses one whose
laws fail the law checker (laws.py)."""
import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Optional

VERSION = "forecast-p2-1"
CONTRACT = "forecast-1"

KINDS = ("rule", "score", "model", "vendor", "sleeve", "exec")
GRADES = ("A", "B", "C", "V", "X", "P", "NEW")
STATUSES = ("candidate", "promoted", "probation", "demoted", "killed")
TARGET_KINDS = ("up_excess", "down_excess", "p_drawdown", "no_move", "big_move", "realized_vol", "path",
                "time_to_move", "relative", "sleeve_pnl", "fill", "slippage")
BENCHMARKS = ("same_day_state_mean", "SPY", "sector", "random_same_name", "none")
LOSSES = ("brier", "logloss", "rank_ic", "qlike", "mae", "mean_r")
SPLITS = ("all", "disc", "hold", "forward") + tuple(f"wf_{k}" for k in range(1, 21))
LAWS = ("point_in_time", "deterministic", "bounded", "costed")

# the modules that may never import desk.forecast (tests/test_forecast_guard.py): every sleeve, the OMS, the books,
# the order router, the venues, the engine loop, the runner and the registry of sleeves
GUARDED = ("desk/sleeves/", "desk/oms.py", "desk/books.py", "desk/router.py", "desk/venues/", "desk/engine.py",
           "desk/runner.py", "desk/registry.py", "desk/ledger.py", "desk/contract.py")

# the sleeve-ensemble track (P1-S, tests/test_sleeve_ensemble.py): top-level desk modules and packages that must
# never import desk.forecast; it only reads the forward record and never changes a sleeve's decisions, sizes or orders
NO_IMPORT = ("desk/sleeves/", "desk/oms.py", "desk/books.py", "desk/engine.py", "desk/router.py", "desk/venues/",
             "desk/registry.py", "desk/feeds.py", "desk/runner.py", "desk/ledger.py")


class ContractError(ValueError):
    pass


def _need(cond, why):
    if not cond:
        raise ContractError(why)


@dataclass(frozen=True)
class Target:
    id: str
    kind: str
    horizon_d: int
    params: dict = field(default_factory=dict)
    benchmark: str = "same_day_state_mean"
    loss: str = "rank_ic"

    def __post_init__(self):
        _need(self.kind in TARGET_KINDS, f"target kind {self.kind!r}")
        _need(self.benchmark in BENCHMARKS, f"benchmark {self.benchmark!r}")
        _need(self.loss in LOSSES, f"loss {self.loss!r}")
        _need(isinstance(self.horizon_d, int) and self.horizon_d >= 1, "horizon_d >= 1")


@dataclass(frozen=True)
class Context:
    """a context cell: dims maps a dimension to its value ("all" when pooled); every dim is known at the close of d"""
    id: str
    dims: dict = field(default_factory=dict)

    @property
    def key(self):
        return "all" if not self.dims else "|".join(f"{k}={self.dims[k]}" for k in sorted(self.dims))


@dataclass(frozen=True)
class Laws:
    """the laws a forecaster declares; registry.register checks the first three on random histories (laws.py)
      point_in_time  its value at t is a function of bars 0..t (and the market at 0..t) only
      deterministic  two runs on the same input give bit-identical output
      bounded        every finite value lies in [lo, hi]; NaN only where data is missing, before `warmup` bars, or
                     on a declared abstention (`abstains`)
      costed         the cost model its scores are netted with (`cost`); "none" only for a target with no trade"""
    point_in_time: bool = True
    deterministic: bool = True
    bounded: tuple = (float("-inf"), float("inf"))
    warmup: int = 0
    abstains: bool = False
    costed: str = "own_name_half_spread"

    def __post_init__(self):
        lo, hi = self.bounded
        _need(lo <= hi, "bounded lo <= hi")
        _need(self.point_in_time and self.deterministic, "a forecaster must be point in time and deterministic")
        _need(bool(self.costed), "costed names its cost model")


@dataclass(frozen=True)
class Ledger:
    """the evidence-ledger fields (gestalt ANALYSIS.md "Where it goes further than us" 2, adopted in P2); every field
    is declared at registration and kept on the record, "unknown" until measured
      speed_decay    how fast the edge arrives and fades (horizon of the peak, half-life), e.g. "peak 5d"
      access_pit     how the inputs are known point in time: "closed bars", "revised history (non-PIT)", ...
      payer          whose trade pays the edge (forced seller, retail chaser, hedger, risk premium, ...)
      co_losses      what it loses together with (the crowded exposures it shares)
      holdable       can the desk hold the position the forecast implies (long only, veto, options paper only, ...)
      execution_net  the cost model its net effect is measured with ("measured" values land on its Scores)
      decisive_test  the one test that would refute it
      kill_rule      the forward rule that kills it (FACTORY.md §5 by default)
      trials         the number of cells tested for it in the run that graded it (set by search; 0 at birth)"""
    speed_decay: str = "unknown"
    access_pit: str = "closed bars"
    payer: str = "unknown"
    co_losses: str = "unknown"
    holdable: str = "long or veto (stock); never a single-name short book (EVIDENCE A16)"
    execution_net: str = "own-name Corwin-Schultz half-spread x 2.3 + 2 bp + square-root impact (costs.py)"
    decisive_test: str = "same-sign holdout from 2023 with block t >= 2 after BH over the whole run"
    kill_rule: str = "FACTORY.md §5: 250 forward dates with effect <= 0, or a significant wrong sign"
    trials: int = 0


LEDGER_FIELDS = ("speed_decay", "access_pit", "payer", "co_losses", "holdable", "execution_net", "decisive_test",
                 "kill_rule", "trials")


@dataclass(frozen=True)
class Forecaster:
    id: str
    version: str
    kind: str
    owner_module: str
    family: str
    targets: tuple
    laws: Laws
    contexts_declared: object = "all"
    history_ok: bool = True
    inputs: tuple = ()
    pit: bool = True
    frozen_sha: Optional[str] = None
    grade: str = "NEW"
    evidence: tuple = ()
    status: str = "candidate"
    sign: int = 1                         # +1: a higher value forecasts a higher target; -1 flips it
    note: str = ""
    ledger: Ledger = field(default_factory=Ledger)

    def __post_init__(self):
        _need(self.kind in KINDS, f"kind {self.kind!r}")
        _need(self.grade in GRADES, f"grade {self.grade!r}")
        _need(self.status in STATUSES, f"status {self.status!r}")
        _need(self.sign in (1, -1), "sign is +1 or -1")
        _need(self.pit, "pit must be true")
        _need(len(self.targets) >= 1, "at least one target")

    def to_json(self):
        d = asdict(self)
        d["contract"] = CONTRACT
        d["laws"]["bounded"] = [str(x) if x in (float("inf"), float("-inf")) else x for x in self.laws.bounded]
        return d


@dataclass(frozen=True)
class Forecast:
    fid: str
    forecaster: str
    version: str
    target: str
    context_cell: str
    sym: str
    as_of: str
    value: Optional[float]
    abstain: bool = False
    reason: str = ""
    inputs_hash: str = ""

    def __post_init__(self):
        _need(self.abstain == (self.value is None), "value is None exactly when the forecast abstains")
        _need(not self.abstain or bool(self.reason), "an abstention carries its reason")


@dataclass
class Score:
    forecaster: str
    target: str
    cell: str
    split: str
    n_obs: int
    n_dates: int
    ic: Optional[float] = None
    ic_t_clustered: Optional[float] = None
    t_eff: Optional[float] = None
    t_block: Optional[float] = None       # the gapped-block t whose p enters BH (score.block_t)
    hit: Optional[float] = None
    brier: Optional[float] = None
    brier_skill_vs_base: Optional[float] = None
    logloss: Optional[float] = None
    calib_slope: Optional[float] = None
    calib_err_by_decile: Optional[list] = None
    mean_excess_net: Optional[float] = None
    cost_bps: Optional[float] = None
    capacity_usd: Optional[float] = None
    p: Optional[float] = None
    q_bh: Optional[float] = None
    deflation_trials: Optional[int] = None
    first_date: Optional[str] = None
    last_date: Optional[str] = None
    status: str = "tested"               # tested | untested (under the cell minimum: logged, never a null)
    # P2 (gestalt ledger fields measured on the score, and the per-opportunity denominator)
    execution_net: Optional[float] = None  # the net effect after own-name costs (costs.py), per opportunity
    speed_decay: Optional[str] = None
    trials: Optional[int] = None           # cells tested in the run (= deflation_trials once BH has run)
    n_opportunities: Optional[int] = None  # every eligible opportunity, filled or not (gates.per_opportunity)
    fill_rate: Optional[float] = None
    capacity_note: Optional[str] = None

    def __post_init__(self):
        _need(self.split in SPLITS, f"split {self.split!r}")
        _need(self.status in ("tested", "untested"), f"status {self.status!r}")


def forecast_id(forecaster, version, target, sym, as_of):
    return hashlib.sha256(f"{forecaster}@{version}|{target}|{sym}|{as_of}".encode()).hexdigest()[:20]


def dumps(obj):
    """a contract object -> canonical JSON (sorted keys) carrying the contract version"""
    d = obj.to_json() if hasattr(obj, "to_json") else asdict(obj)
    d.setdefault("contract", CONTRACT)
    return json.dumps(d, sort_keys=True, default=str)
