Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_saty_research: Algorithm

## What it trades
A thin wrapper sleeve. The file
adapters3/aster_saty_research.py is the per-sleeve core:
evaluate() delegates to the shared engine
desk3/aster_batch16.py evaluate(), kind="saty". Plainly:
the authored source for this sleeve is ABSENT from the
archive (build map S4), so this sleeve is a TSV-as-spec
meta-ranker shell only; the 10 setup families are NOT
invented in the code. Candidates arrive pre-formed via
the saty_setups snapshot key, and no v3 producer emits
that key, so the sleeve is visibly UNFED / monitor-only
in production. The sleeve runs on the shared engine
desk3/aster_batch16.py. Sizing is on the $10,000 slice
(SLICE = 10000.0). Paper only.

## Spec and constants (desk3/aster_batch16.py)
kind="saty", inputs=("saty_setups", "quotes", "bars",
"positions"), cadence_s=600, session="rth", slice capital
$10,000. Risk per entry 0.25% of the slice ($25 = 1R;
halved for mean-reversion families); round-trip cost
estimate $0.02 per share; at most 3 entries per day;
daily loss limit 2R; open risk limit 2R with a 1R
correlated cap (single-instrument book: all SPY); quote
maximum age 5 seconds; entry deadline 15:40 ET; final
exit 15:50 ET. Instrument: SPY only.

## Entry rules
- Exits are evaluated first; if any exit is emitted the
  evaluation returns with no entry.
- No entry at or after 15:40 ET, after 3 entries today,
  or when the day's realised result is at or below -2R.
- A fresh two-sided SPY quote is required: the quote
  timestamp must be within 5 seconds of now (and not in
  the future), else the evaluation fails closed. Price is
  the quote mid, else the last 10-minute bar close.
- Open risk is summed over held positions as qty x
  |avg_price - invalidation|; a new entry is refused when
  open risk plus the new 1R would exceed the 1R
  correlated cap.
- A candidate must be a dict for SPY, with SPY not held,
  and with positive net room both at its planned entry
  and at the current price: net room = (distance to the
  first target - $0.02 per share) / (distance to
  invalidation), direction-aware; non-positive refuses.
- Ranking: net room at the current price descending,
  then context descending, then age_min ascending, then
  family name. If the best two candidates have opposite
  directions and equal top rank (within 1e-9), no entry
  is emitted (conflicting directions wait).
- Sizing: risk is $25 (halved when the family name marks
  mean reversion). Executable-risk sizing
  (ENH-B26-SATYEXEC-20261024, switch default ON): qty =
  int(risk_usd // |current price - invalidation|); with
  the switch OFF the planned entry price is used instead.
  qty < 1 emits nothing. One entry per evaluation.
- Entries are market, day intents on SPY, buy for a long
  candidate and sell (sell_to_open) for a short one, with
  the family, direction, net room, risk, invalidation and
  targets named in the reason.

## Exit rules
- Structural invalidation: the current price at or past
  the position's invalidation (at or below for a long, at
  or above for a short) sells/buys back the full position.
- Final exit deadline: at or after 15:50 ET any held
  position is closed in full.
- Target-1 scale: an unscaled position whose price
  reaches its first target is half closed (the full
  quantity when halving would give 0).
- Trail after scale: a scaled position whose price
  returns to its entry reference is closed in full
  (trail to breakeven after scale).
- Exits are market, day, sell_to_close (or buy_to_close
  for a short) intents.

## Data inputs
Declared inputs: saty_setups, quotes, bars, positions.
Producers named in desk3/aster_batch16.py:
saty_setup_families (60s freshness, outputs saty_setups),
quotes (60s), bars (900s), broker_readback (900s,
positions). The batch-16 note states run_live registers
only bars and broker_readback today, so saty_setups and
quotes have no live producer yet and the sleeve is
visibly UNFED rather than fake-fed.
