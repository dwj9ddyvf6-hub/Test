Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_r19_timing_overnight_5bp: Algorithm

## What it trades
A thin wrapper sleeve. The file
adapters3/aster_r19_timing_overnight_5bp.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/aster_batch16.py evaluate(), which for this sleeve
calls desk3/aster_batch15.py _eval_timing() with the
aster_r19_timing_overnight_25bp spec copied and fee_bps
changed to 5 (the archive books differ only in fee_bps,
per the batch-16 engine docstring). It is an overnight
timing sleeve on a 42-symbol universe: a strong
12:30 to 14:30 ET 30-minute return day is bought near the
close and held overnight to the next session's 09:30 ET
open. Sizing is book-relative on the $10,000 slice
(SLICE = 10000.0). Paper only. The sleeve runs on the
shared engines desk3/aster_batch16.py and
desk3/aster_batch15.py.

## Spec
kind="overnight", risk=0.0025, notional=0.1, fee_bps=5,
slots=8, inputs=("bars", "positions", "quotes"),
cadence_s=300, session="rth", slice capital $10,000,
bp_buffer_frac 0.02 in the batch-16 config row.
Universe (UNIVERSE42 in desk3/aster_batch15.py): AAOI,
AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ,
CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR,
LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ,
SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC,
WYFI.

## Entry rules
- Exits are evaluated first; if any exit is emitted the
  evaluation returns with no entry.
- Entry window: only 15:30 <= ET clock < 15:35.
- Signal (overnight_signal in desk3/aster_batch15.py,
  computed from 30-minute bars at the sleeve layer): the
  day must be a weekday session in the session list; the
  day's 12:30 to 14:30 ET return (14:30 close / 12:30
  close - 1) must be at or above the 80th percentile of
  the same return over the prior sessions (at least 126
  history values required; the last 252 are used). At
  least 252 30-minute bars are required per symbol.
- Actionable time: the end of the 14:30 bar plus 30
  minutes; the entry is emitted only while now is within
  5 minutes of actionable_at.
- Price: the buy quote when available, else the last
  30-minute bar close; a missing or non-positive price
  skips the symbol. The overnight signal carries no stop
  or target, so no stop/target geometry check applies.
- Sizing: fee = 5 / 10000; budget = min(cash, $10,000 x
  0.1) = up to $1,000; qty = floor(budget / (price x
  (1 + fee))); qty <= 0 emits nothing. At most 8 slots.
- Execution enhancement (ENH entry-mid, switch default
  ON): when a two-sided quote exists, the entry becomes a
  limit order at the quote mid (rounded to 2 decimals)
  instead of a market order at the ask, with a paired
  spread-saved record on the intent.
- The entry intent carries exit_at = the next session's
  09:30 ET.

## Exit rules
- Exits are evaluated on the witnessed bid (sell quote,
  else the last 30-minute close): a bid at or below a
  recorded stop triggers observed_stop_trigger and a bid
  at or above a recorded target triggers
  observed_target (the overnight signal records neither,
  so in practice the scheduled exit governs).
- Scheduled time exit: at or after the position's
  exit_at (next session 09:30 ET), the position is sold
  in full, reason scheduled_time_exit.
- Execution enhancement for this sleeve's scheduled exit
  (switch default ON): when a two-sided quote exists, the
  exit becomes a limit order at the quote mid instead of
  a market order at the bid, with a paired record.
- Exits are sell_to_close intents, in full.

## Data inputs
Declared inputs: bars, positions, quotes. Producers named
in desk3/aster_batch16.py: bars (900s freshness), quotes
(60s), broker_readback (900s, positions). The batch-16
note states run_live registers only bars and
broker_readback today, so the quotes input has no live
producer yet and the sleeve is visibly UNFED on that
input rather than fake-fed.
