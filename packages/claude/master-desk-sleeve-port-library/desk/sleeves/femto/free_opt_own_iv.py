"""FREE_OPT_OWN_IV — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's FREE_OPT_OWN_IV_V1 descendant (preserves OPT_OWN_IV_RESIDUAL) restored on the
engine (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: desk/free_options.py evaluate / execute and
desk/option_packages.py submit_package / manage_exits — the rules vendored as desk/vendor/aurelia/free_options.py,
the execution in free_opt_core). Buy the call AND the put together (a straddle) when a causal realized-volatility
forecast exceeds indicative IV by 2 points; one leg is never submitted alone.

  entry .... evaluate(): the indicative probe fresh (source <= 90 s, receipt <= 30 s, 2 s future tolerance, bid > 0,
             ask >= bid) and a package of exactly 2 legs, rights {call, put}, whose source stamps lie within 30 s
             -> submit_package() while the market is open: once per package id; not a model test, deliverable, both
             legs present and fresh, its max loss inside its risk cap and the $100,000 pool; broker_mleg -> one
             multi-leg order at the price the package journal booked (the call's and the put's asks).
  exits .... the package's exit_at (the contract: ten sessions or expiry) once passed while the market is open; at
             expiry the engine settles. Both legs close together.

  package .. produced on the desk (the source read own_iv_forecast and never wrote it; its run() attached only
             {"hedge": ...}): desk/feedlib/free_options_inputs.own_iv — the forecast is the source's own causal
             realized-volatility forecaster, desk/features.py har_vol_forecast unchanged (HAR-RV, Corsi 2009: OLS on
             the daily / 5-day / 22-day mean squared log returns, expanding window refit every 21 sessions after 504,
             EWMA 0.94 before, clipped 10-150%), over SPY's completed daily closes for the sessions to the straddle's
             expiry; the indicative IV is the mean of the straddle's two legs' IV on the desk's chain; the straddle
             is the ATM call and put of the nearest 21-35 DTE expiry at least 7 calendar days past the ten-session
             exit (FWD_RESEARCH_OWN_IV_V1), 1 package, max loss = the natural debit, its own risk cap (one open
             package at a time); exit_at 5 minutes before the close of the 10th session counting the entry's.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper.run passed
send=False when either fired); the Femto fences of the old desk's copy (no snapshot fetch, sim packages); the
missing-producer block (status monitor).
Named divergences: the package producer above (every contract rule, the forecast horizon = the straddle's sessions
to expiry where the source's own analyst used 5, the per-contract chain IV for the snapshot's impliedVolatility);
the decision moment is the chain's receipt when the pass fetched it after its start (the source decided on the
cycle's clock with the snapshot fetched at once); its own $100,000 book and pool (the source's descendants shared
one $100,000 pool); the package is
bought at the natural debit its journal booked (the source's multi-leg order carried the larger leg ask alone as
its limit, and quantity 1); a package that closes, or never opens, releases its risk reservation (the source never
released one); a due package closes through the OMS at its natural (the source booked the close at the entry
prices in a local journal and sent no order); a package whose exit_at has already passed when it is sent closes on
the next pass (the source booked both in one pass); a package the OMS never fills leaves the book and releases its
risk (the source's journal held it open from the broker's acknowledgement); a package with a leg that lacks its side
of the market sends nothing (the source's journal bought the legs before it at the ask and sold them back at the
bid); the probe is the desk's chain (received when the chain was fetched); a pass every 5 minutes of the session
(the source evaluated every ~20-second cycle).

Inputs via context.extra:
  "quote"        the indicative probe {"symbol","bp","ap","t","received_at"}
  "package"      the straddle package {"client_order_id","execution","legs":[{"symbol","right","side","quantity",
                 "bid","ask","source_at","received_at"} x2],"legs_required","max_loss","risk_cap","exit_at",...}
                 (free_options_inputs.own_iv; None while the forecast does not exceed the IV by 2 points)
  "own_iv"       the producer's record {"forecast","iv","expiration","horizon","reason"}
  "market_open"  the clock's is_open
  "legs" / "pending"  the sleeve's option positions and working orders
  "meta"         {"packages": {client id: record}}
  "decided_at"   the chain's receipt when later than the pass's clock (free_opt_core.moment_of)
"""
from .compat import BaseSleeve, SleeveConfig
from . import free_opt_core as C

SPEC_ID = "FREE_OPT_OWN_IV_V1"
ACCOUNT = "free_options"
BUDGET_USD = 100_000.0

CONFIG = SleeveConfig(
    sleeve_id="free_opt_own_iv", cadence_s=300, universe=(),
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


class FreeOptOwnIv(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptOwnIv().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    meta["packages"] = _pass(bars, context)["packages"]
    return meta


def monitor(mod, bars, context):
    r = _pass(bars, context)["row"]
    p = (context.extra or {}).get("own_iv") or {}
    why = p.get("why") or p.get("reason")              # the stable phrase: one record per state, numbers in meta
    return [("SPY", "%s %s: %s%s" % (SPEC_ID, r["status"], r.get("reason") or "", " [%s]" % why if why else ""),
             {"status": r["status"], "forecast": p.get("forecast"), "iv": p.get("iv"),
              "expiration": p.get("expiration"), "detail": p.get("reason")})]
