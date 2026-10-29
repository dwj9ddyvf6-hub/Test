"""The Morgue Engine, ported into the desk as a first-class component (owner, 2026-10-27).

Silicon's research/morgue-engine (Muse's design, assembled from vendor teardowns) was a set of scripts that wrote JSON
beside themselves. Here it is a package whose producers are host jobs (desk/jobs.py: morgue_preopen, morgue_postclose,
morgue_inst) and whose consumer is the edition (edition.py: the `morgue` key, schema in docs/research/MORGUE_SCHEMA.md).

Design laws, kept from the original and enforced by tests/test_morgue_*.py:
  1. The engine MEASURES; it does not trade. Nothing here sends an order or changes a sleeve.
  2. Append-only ledger (ledger.py): every card is written to it, with an inputs hash, BEFORE it is shown; a card whose
     hash the ledger does not hold is not shown (edition.py).
  3. Completed sessions only: no forming bar is ever read.
  4. Every value carries as_of, source, delay and status ok / stale / no_data with a reason; a number that cannot be
     computed is null with the reason, never a constant.
  5. Liquidity is capacity, not a filter (owner, 2026-10-27): nothing here removes a name for being thin.

Producers (pure functions first, a thin job around each; all injectable so a test runs without a network or keys):
  bs          Black-Scholes price, greeks, implied volatility
  map_gex     the dealer gamma map (SpotGamma's published construction) of SPY, QQQ, IWM from Alpaca's chains
  map_dix     DIX from FINRA's FNQC short-volume files: per ETF, constituent-weighted index, roster-wide
  tape        per-print option flow scoring (NBBO side, premium, sweeps, heat, opening or closing)
  board       the confluence board over the genome roster, features and leaves (board_features), cache-only bars
  inst_*      the institutional leaves: Form 4 insiders, 13F ownership and activity, short interest
  scorecards  fixed 1d / 5d / 21d grading of the ledger's board rows and map cards; wall_study the wall research cut
  studies     gap fill, opening range, earnings, squeeze, state vectors: pure functions; studies_feed gives them real
              inputs (Muse's daily cycle passed them none: bars_by_symbol={} in studies_card.main, so only fixtures ever
              produced a number; that defect is fixed here and tested)
  cycle       the daily rhythm (preopen about 08:46 ET, postclose about 16:46 ET) as functions the jobs call
State: state/morgue/ (the ledger, the cards, the point-in-time short-interest store: recorded by tools/state_sync) and
cache/morgue/ (downloads and per-name caches, not recorded)."""
import os

ROOT_LAW = "The engine measures; it does not trade."
FUNDS = ("SPY", "QQQ", "IWM")
STATE = os.path.join("state", "morgue")
CACHE = os.path.join("cache", "morgue")


def state_dir(root):
    return os.path.join(root, STATE)


def cache_dir(root):
    return os.path.join(root, CACHE)


def state_path(root, name):
    return os.path.join(root, STATE, name)


def cache_path(root, *parts):
    return os.path.join(root, CACHE, *parts)


def stamp(status, as_of=None, source=None, delay=None, reason=None, **kw):
    """the contract's stamp (docs/research/MORGUE_SCHEMA.md section 2) as a dict; reason only when not ok"""
    out = {"status": status}
    if status != "ok":
        out["reason"] = reason or "no reason given"
    out.update(as_of=as_of, source=source, delay=delay)
    out.update(kw)
    return out


def no_data(reason, as_of=None, source=None, delay=None, **kw):
    return stamp("no_data", as_of, source, delay, reason, **kw)
