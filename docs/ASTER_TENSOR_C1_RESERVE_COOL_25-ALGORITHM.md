Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_c1_reserve_cool_25: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_c1_reserve_cool_25.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch13.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS = INPUTS_TENSOR and PRODUCERS taken from that engine. It is a
long-only equity sleeve that consumes canonical Tensor v698 buy
fires through the desk's Tensor bundle fire channel (the Tensor
ENGINE itself is untouched) and holds each position to a 52-week
deadline. Signal generation and position management are in that
engine; this sleeve implements no math of its own. The sleeve runs
on the shared engine desk3/aster_batch13.py.

## Spec (from SPECS in desk3/aster_batch13.py)
kind="tensor", family="C1", capital_mode="reserve",
volatility="cool". Engine constants: TICKET=400.0 (the source
book's $4,000 ticket scaled to the $10,000 v3 slice), SLOTS=25
distinct symbols, HOLD_SESSIONS=260.
- Inputs (INPUTS_TENSOR): tensor, bars, positions.

## Entry rules
- Exits are evaluated first; if any exit intent is emitted, no
  entry is evaluated in the same call. At most one entry per call.
- Fires are read from view["fires"], view["tensor"] (a list, or a
  dict with a "fires" list), or view["extra"]["fires"]. A fire
  carrying a different sleeve_id is ignored, as are symbols already
  held and fires with price <= 0.
- C1 pass gates (source r19_tensor.passes): the fire signal must
  be a buy-cyan event; price <= 5; ret60 >= 31; vol20 >= 0.07;
  average dollar volume (adv_usd / avg_dollar_volume) >= 2,000,000.
- Volatility split (source-exact, r19_tensor.passes): atr_ratio <= 1 is cool, atr_ratio > 1 is hot; this sleeve takes only "cool" fires (atr_ratio <= 1); a fire with no atr_ratio is skipped.
- Reserve mode timing: the fire date must be at least 1 day
  before the evaluation session (delay/reserve sleeves wait one
  extra session); a fire with no parseable date is not delayed.
- Execution-price revalidation (ENH-TENSOR13-REPRICE-20261024,
  switch default ON; OFF restores the fire-price rule exactly):
  when a current bar exists, the C1 price cap (<= 5) is
  revalidated against the latest close; a current close above 5
  refuses the entry (recorded as the paired shadow control), and
  sizing uses the latest close instead of the fire price.
- Sizing: qty = floor(400 / execution price); qty < 1 emits
  nothing. Orders are market, day, buy_to_open.
- Reserve funding: before the entry, if a QQQ position is held,
  an exit intent sells min(QQQ qty, floor(400 / QQQ price) or 1)
  shares of the QQQ reserve leg to fund the ticket.

## Exit rules
- The only designed exit is the 52-week deadline: a position whose
  age reaches 260 sessions held (sessions_held / age_sessions /
  held_sessions, or weeks_held x 5) is sold in full at the latest
  bar close (or avg_price when no bar is available). Age fields
  absent means age 0.
- No price stop and no profit cap (per the source TSV).
- The QQQ reserve leg is never deadline-exited by this sleeve; it
  exits only to fund an entry ticket (above).

## Data inputs
Declared inputs: tensor, bars, positions. Producers named in the
engine: bars (900s freshness), tensor_bundle (86400s, outputs
tensor), broker_readback (900s, positions).
