Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# mk_zerodte_spx: Algorithm

## What it trades
The per-sleeve core packaged here is
adapters3/milkman_0dte.py, the v3 worker entrypoint for
mk_zerodte_spx: evaluate() rebuilds the v2 SleeveContext
from the cycle snapshot and delegates to
adapters/milkman_0dte.py, which in turn calls the strategy
in sleeves/milkman_0dte.py (the v3-native expression of
the authored Milkman 0DTE SPX sleeve). It trades SPX
same-day-expiry (0DTE) options, long premium only: a long
lane buys a call, a short lane buys a put, at the contract
whose absolute delta is nearest 0.40. The config row is
parked and the sleeve is INERT until a greeks-bearing SPX
0DTE chain is proven (see Data inputs): no probe record,
no entry, and the abstention names the reason "SPX 0DTE
chain not available". There is never a fallback to SPY
options or to a model price. The strategy logic below is
derived from sleeves/milkman_0dte.py.

## Spec and constants (sleeves/milkman_0dte.py)
Universe SPX only; cadence 60s; parked=True in the
strategy CONFIG. Premium per trade $2,500 in whole
contracts; maximum 4 open at once; daily stop -$10,000 on
the book's session P&L; target delta 0.40; maximum spread
20% of the ask; quote maximum age 180 seconds; no entry
in the last 30 minutes; hard flat 15 minutes before the
16:00 ET close; contract roots SPXW or SPX; lanes ESMON
and OPX4 are excluded (not expressed).

## Entry rules
- Session handling first: positions still open from a
  prior session are dropped and logged "expired: settled
  at the official SPX close". Outside regular hours
  (weekday 09:30 to 16:00 ET) the evaluation returns
  nothing.
- Daily stop: when the book's session P&L reaches
  -$10,000, everything held is flattened at the quoted
  bid and entries are blocked for the rest of the session.
  The same flattening happens inside the last 15 minutes
  before the close (hard exit).
- Lane exits are processed before entries (see below).
- Inert gate: unless the SPX probe verdict is available
  for SPX, no entry is emitted and the evaluation state
  is "inert" with the named reason. Inside the last 30
  minutes, no entry is emitted either.
- A lane signal {"key", "side"} is skipped when its key
  is an excluded lane, the key is already open or seen,
  or 4 positions are already open.
- Contract choice (pick_contract): among today's-expiry
  contracts of the lane's type (call for side > 0, put
  for side < 0) with root SPXW or SPX, keep only rows with
  a two-sided quote (bid > 0, ask >= bid), a quote age of
  at most 180 seconds, a spread of at most 20% of the
  ask, and a delta present (rows without a delta are
  never chosen from); pick the row whose |delta| is
  nearest 0.40, symbol ascending on ties. No qualifying
  row means no entry, with the reason logged.
- Sizing (contracts_for): whole contracts for the $2,500
  premium budget at the quoted ask (ask x 100 per
  contract); one contract is allowed when a single
  contract costs up to 1.5 budgets; otherwise 0 and no
  entry.
- Entries are limit orders at the quoted ask, buy_to_open,
  with the lane key, contract, quantity and ask/bid named
  in the reason.

## Exit rules
- Lane exit: when a lane key appears in lane_exits, its
  held contract is sold at the quoted bid, the key is
  marked done and the exit is logged.
- Daily stop and hard-exit flattening as above: every
  held SPX-root contract is sold at the quoted bid.
- Contracts held past expiry are dropped on the next
  session's first pass and logged "expired".
- Exits are sell_to_close intents.

## Data inputs
Declared INPUTS in the packaged entrypoint: bars,
positions, milkman_0dte_chain. Plainly: the
milkman_0dte_chain input (the SPX 0DTE chain with greeks)
has NO producer on this desk: the options producer serves
SPY/QQQ/IWM/XSP via feed=indicative, which carries no
greeks, and SPX is not in its underlying set; and the
adapter leaves lane_signals empty because the authored
intraday study that produces lane signals is not ported.
Both gaps are named in desk3/milkman_0dte/PROVENANCE.md.
The sleeve is therefore parked and UNFED by design, never
fake-fed, until a greeks-bearing SPX route is proven.
