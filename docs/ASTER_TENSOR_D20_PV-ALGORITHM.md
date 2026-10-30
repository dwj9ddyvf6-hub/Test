Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_d20_pv: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_d20_pv.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/aster_batch16.py evaluate(), kind="d20",
model="price_volume". It is a frozen Tensor daily-20 tree
ensemble sleeve: each eligible symbol's last decision row
is scored by the frozen 100-tree ensemble vendored as data
under desk3/aster_d20_assets/ (hash-verified at load, no
refit; the Tensor engine itself is untouched), and a score
at or above the model's frozen threshold buys a 20-bar
hold. Sizing is on the $10,000 slice (SLICE = 10000.0).
Paper only. The sleeve runs on the shared engine
desk3/aster_batch16.py.

## Spec and constants (desk3/aster_batch16.py)
kind="d20", model="price_volume", inputs=("tensor_daily20",
"bars", "positions"), cadence_s=86400, session="rth",
slice capital $10,000. Hold 20 bars; slots 10; caps 0.10
of equity and 0.01 of dollar_volume20. Excluded symbols:
QQQ, SPY, B, GOLD. Model features: only the 6 price/volume columns (return20, return60,
atr_pct, rvol, log_dollar_volume20,
close_ema21_distance_atr).
Frozen asset integrity: the manifest SHA-256 and every
consumed asset hash are verified at load (1,817 canonical
symbols, phases checked); any integrity failure fails
closed with no intents.

## Entry rules
- The 20-bar exit is evaluated first; if any exit is
  emitted the evaluation returns with no entry.
- Decision gates for a symbol's candidate series, in the
  engine's order: a canonical anchor must exist for the
  symbol; the history must be non-empty; every row must
  carry the required native columns, match the symbol,
  have bar_index equal to its ordinal, and match the
  anchor origin timestamps; the symbol must not be
  excluded; at least 234 rows (index >= 233, warmup);
  native_status must be "ready"; the last close must be
  at least $5; dollar_volume20 must be at least
  $1,000,000; ATR14 must be positive; and the last row
  index modulo 20 must equal the symbol's canonical phase
  (SHA-256 of the symbol modulo 20).
- The frozen feature frame (the past-only 35-column
  transform for the tensor model; the 6 price/volume
  columns for the price_volume model) is computed, missing
  values are imputed with the model's frozen medians, and
  the score is the model baseline plus one leaf value per
  tree (100 trees). Selected means score >= the model's
  frozen threshold.
- Fresh-row gate (ENH-B26-D20FRESH-20261024, switch
  default ON; exits are never gated): when the symbol's
  1Day bars are present, a selected candidate whose last
  decision row predates the last bar by more than 4 days
  is refused. No bars means no evidence and the gate
  passes.
- Selected candidates are ranked by score descending,
  symbol ascending. Sizing: cap = min(equity x 0.10,
  dollar_volume20 x 0.01, available cash); shares =
  int(cap // close); fewer than 1 share emits nothing.
  At most 10 slots.
- Entries are market, day, buy_to_open intents at the
  decision row's close.

## Exit rules
- The only designed exit: a position held at least 20
  completed daily holding bars is sold in full, reason
  naming hold_20_bars. There is no price stop.
- Exits are market, day, sell_to_close intents, in full.

## Data inputs
Declared inputs: tensor_daily20, bars, positions.
Producers named in desk3/aster_batch16.py:
tensor_daily20_bundle (93600s freshness, outputs
tensor_daily20), bars (900s), broker_readback (900s,
positions). The batch-16 note states run_live registers
only bars and broker_readback today, so the
tensor_daily20 input has no live producer yet and the
sleeve is visibly UNFED on that input rather than
fake-fed.
