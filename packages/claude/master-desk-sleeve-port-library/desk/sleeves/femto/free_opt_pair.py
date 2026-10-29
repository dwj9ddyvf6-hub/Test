"""FREE_OPT_PAIR — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's FREE_OPT_PAIR_V1 descendant (preserves OPT_STATIONARY_PAIR) restored on the
engine (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: desk/free_options.py evaluate / execute,
desk/option_packages.py submit_package / manage_exits, the frozen hedge of desk/option_inputs.py _hedge — the rules
vendored as desk/vendor/aurelia/free_options.py, the execution in free_opt_core, the hedge in
desk/feedlib/aurelia_options.py). Both exposures of a cross-underlying pair, only after a hedge ratio frozen from
prior closes.

  hedge .... SPY/QQQ: the last 61 common completed closes before the latest one — beta of QQQ's daily returns on
             SPY's, the residual's mean and (population) deviation — and the latest session's residual z;
             "signal" = |z| > 2. Attached as the package {"hedge": ...}, as the source's run() attached it.
  entry .... evaluate(): the indicative probe fresh (source <= 90 s, receipt <= 30 s, 2 s future tolerance, bid > 0,
             ask >= bid) and a package of exactly 2 legs on 2 underlyings with hedge_frozen set ->
             submit_package() while the market is open: once per package id; not a model test, deliverable, both
             legs fresh and within 30 s, its max loss inside its risk cap and the $100,000 pool; a coordinated
             package -> one order per leg at that leg's price (the ask bought / the bid sold), sent only when every
             leg has its side of the market (the source's local fill rejected the package at the first leg without
             it, after buying the legs before it at the ask and selling them back at the bid).
  exits .... the package's exit_at (the contract: ten sessions) once passed while the market is open; a failed leg
             closes the filled leg; legs on two underlyings close as one order each.

  legs ..... produced on the desk (the source's run() attached only {"hedge": ...}, so its row only ever waited):
             desk/feedlib/free_options_inputs.pair — once the frozen residual z leaves the +-2 band, both exposures
             toward the residual's mean: z > 2 (QQQ rich against beta x SPY) buys the QQQ ATM put and the SPY ATM
             call, z < -2 the QQQ ATM call and the SPY ATM put, on their nearest common 30-60 DTE expiry (the R17
             pair's option window) at least 7 days past the ten-session exit; 1 QQQ contract and round(beta x QQQ
             delta-dollars / SPY delta-dollars) SPY contracts (at least 1), hedge_frozen set; one package per signal
             session, one open package at a time; max loss = both premiums; exit_at 5 minutes before the close of
             the 10th session counting the entry's.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper.run passed
send=False when either fired); the Femto fences of the old desk's copy (no snapshot fetch, no option-inputs
refresh, sim packages); the missing-producer block (status monitor).
Named divergences: the legs producer above (the direction, contracts, expiry window and quantities: the source
names "both exposures after a hedge ratio frozen from prior closes" and nothing more); the decision moment is the
chains' latest receipt when the pass fetched them after its start; its own $100,000 book and pool (the source's
descendants shared one $100,000 pool); the hedge is
fit on the desk's completed split-adjusted daily closes, refreshed every session (the source fetched its raw SIP
history once, when empty, and never again — SPY and QQQ had no split in the window, so the closes agree); a package
that closes, or never opens, releases its risk reservation (the source never released one); the legs are orders
filled by the OMS (the source filled them in a local journal at the quote), and a leg that never fills closes the
filled one on the next pass; a due package closes through the OMS at its natural (the source booked the close at
the entry prices locally); a package whose exit_at has already passed when it is sent closes on the next pass; a
package with a leg that lacks its side of the market sends nothing (the source's journal bought the legs before it
at the ask and sold them back at the bid); a multi-leg package trades at the debit its journal booked and its legs'
quantity (the source's broker order carried the larger leg ask and quantity 1); the probe is the desk's chain; a
pass every 5 minutes of the session (the source evaluated every ~20-second cycle).

Inputs via context.extra:
  "quote"        the indicative probe {"symbol","bp","ap","t","received_at"}
  "package"      {"hedge": the frozen hedge}, with "legs" (QQQ and SPY), "hedge_frozen" and the package fields once
                 the residual leaves its band (free_options_inputs.pair)
  "pair"         the producer's {"reason"}
  "market_open"  the clock's is_open
  "legs" / "pending"  the sleeve's option positions and working orders
  "meta"         {"packages": {client id: record}}
  "decided_at"   the chains' latest receipt when later than the pass's clock (free_opt_core.moment_of)
"""
from .compat import BaseSleeve, SleeveConfig
from . import free_opt_core as C

SPEC_ID = "FREE_OPT_PAIR_V1"
ACCOUNT = "free_options"
BUDGET_USD = 100_000.0

CONFIG = SleeveConfig(
    sleeve_id="free_opt_pair", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def decide(bars, context):
    return C.decide_packages(SPEC_ID, context)


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_free_opt_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_free_opt_pass"] = memo
    return memo[1]


class FreeOptPair(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptPair().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    meta["packages"] = _pass(bars, context)["packages"]
    return meta


def monitor(mod, bars, context):
    r = _pass(bars, context)["row"]
    why = ((context.extra or {}).get("pair") or {}).get("reason")
    return [("SPY", "%s %s: %s%s" % (SPEC_ID, r["status"], r.get("reason") or "",
                                     " [%s]" % why if why and why != r.get("reason") else ""),
             {"status": r["status"]})]
