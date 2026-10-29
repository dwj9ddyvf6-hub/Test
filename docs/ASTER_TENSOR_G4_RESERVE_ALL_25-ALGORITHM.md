Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_g4_reserve_all_25: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_g4_reserve_all_25.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch14.py evaluate(SLEEVE_ID, view, ctx), with INPUTS
and PRODUCERS taken from that engine. It is a long-only equity
sleeve that consumes canonical Tensor fires through the desk's
Tensor bundle channel (the Tensor ENGINE itself is untouched) and
holds each position to a 52-week deadline. Signal generation and
position management are in that engine; this sleeve implements no
math of its own. The sleeve runs on the shared engine
desk3/aster_batch14.py.

## Spec (from SPECS in desk3/aster_batch14.py)
family="G4", capital_mode="reserve", volatility="all",
slots=25, ticket=400.0 (the source book's ticket on a
$100k book scaled to the $10,000 v3 slice). Engine constant:
HOLD_SESSIONS=260.
- Inputs: tensor, bars, positions.

## Entry rules
- Exits are evaluated first; if any exit intent is emitted, no
  entry is evaluated in the same call. At most one entry per call.
- Fires are read from view["tensor"] (a list, or a dict with a
  "fires" list), view["fires"], or view["extra"]["fires"]. A fire
  carrying a different sleeve_id is ignored, as are symbols
  already held and fires with price <= 0.
- G4 pass gates (source r19_tensor.passes): 'buy-green' in the
  fire's primary markers (or 'green' in its signal); price <= 10;
  depth60 >= 70; ret60 >= 0; vol20 >= 0.09; average dollar volume
  (adv_usd / avg_dollar_volume / dv20) >= 2,000,000.
- Volatility split: none (volatility="all"); the fire's atr_ratio is not gated.
- Reserve mode timing: the fire date (date / fire_date / signal_end) must be at least 1 day before the evaluation session (entry session is the first session after signal end, +1 session for delay/reserve modes); a fire with no parseable date is not delayed.
- Execution-price revalidation
  (ENH-TENSOR14-REPRICE-20261024, switch default ON; OFF restores
  the fire-price rule exactly): when a current bar exists, the
  family price cap (<= 10) is revalidated against the latest
  close; a current close above the cap refuses the entry (recorded
  as the paired shadow control), and sizing uses the latest close
  instead of the fire price.
- Sizing: qty = floor(400 / execution price); qty < 1 emits
  nothing. Entries stop once 25 distinct symbols are held.
  Orders are market, day, buy_to_open.
- Reserve funding: before the entry, if a QQQ position is held, an exit intent sells min(QQQ qty, floor(400 / QQQ price) or 1) shares of the QQQ reserve leg to fund the ticket shortage.

## Exit rules
- The only designed exit is the 52-week deadline: a position is
  sold in full when its age reaches 260 sessions held
  (sessions_held / age_sessions / held_sessions, or weeks_held
  x 5), or when the session reaches the position's own exit_at /
  exit_deadline date when one is carried. Price used is the latest
  bar close (or avg_price when no bar is available).
- No stop and no profit cap (source RULES risk text).
- The QQQ reserve leg is never deadline-exited by this sleeve; it exits only to fund an entry ticket (above).

## Data inputs
Declared inputs: tensor, bars, positions. Producers named in the
engine: tensor_bundle (86400s freshness, outputs tensor), bars
(900s), broker_readback (900s, positions).
