"""Milkman v2 study sleeves (quant-research-critical milkman-study/v2): the daily rules and the SPY intraday setups."""

# The desk's margin convention (desk/sleeves/families/apex.py MARGIN_RATE, the femto rows' margin_rate): Alpaca charges
# a debit balance 7.75% a year on a 360-day year; the engine's daily carry (desk/engine.py _carry) divides by 365.
# Every milkman book declares it (MAC-10): their fixed-notional event lanes run debits (mk_ema21deviationreversion
# held -$1.16M of cash on 2026-10-25) that carried no interest. Their sizes never read the book's cash.
MARGIN_RATE = 0.0775 * 365 / 360
