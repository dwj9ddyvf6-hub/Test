"""Midna (the Midna TypeScript desk, dwj9ddyvf6-hub/midna) — its own books, each restored on the engine under its
manifest sleeve_id from the pinned source, ported line for line (desk/sleeves/midna/*, parity receipts under
docs/receipts/parity/midna_*.json):

  midna_liquid_126_momentum        context.ts CONTEXT_RULE: the top decile of liquid names by 126-session return,
                                   re-ranked every 63 sessions (desk/sleeves/midna/context.py)
  midna_faber / midna_lc_prior_month_reversal / midna_distance_pair_shares
                                   quantpedia.ts books on the quantpedia-signals.py producer (quantpedia.py)
  midna_turtle_s1 / midna_macd_cci / midna_ema4_vwap
                                   board.ts books on the board-signals.py producer (board.py)
  midna_qqq_flip5_tza              shadow.ts stepHedge on the hourly watch's QQQ flip (shadow.py)
  midna_qld_weekly_timing          felipe/pullback.ts runQld, forward (qld.py)
  midna_qqq_csp_ladder             qqq-ladder.ts applyQqqLadder on the option-marks chains (ladder.py)
  midna_opt_turtle_atm_call / midna_opt_reversal_call_spread / midna_opt_distance_pair
                                   option-books.ts listed-option books (options.py)
  midna_hyperliquid_momentum_floor desk.ts / decide.ts Hyperliquid paper floor, watch armed, sim:kraken_futures
                                   (hyperliquid.py)
  midna_kronos_topk                kronos.ts TopkDropout on the Kronos-base forecast (kronos.py)

Producers run in-pass as feeds (FEEDS) or as family jobs (JOBS) instead of the source's file hand-offs; each
module docstring names its removed desk-wide gates and its named divergences."""
from ...feedlib import midna_hyperliquid, midna_kronos, midna_options, midna_panel, midna_qld, midna_signals, midna_watch
from ..midna import board, context, hyperliquid, kronos, ladder, options, qld, quantpedia, shadow

FEEDS = {"midna_panel": midna_panel.feed_panel,
         "midna_qp_signals": midna_signals.feed_qp,
         "midna_board_signals": midna_signals.feed_board,
         "midna_watch": midna_watch.feed_watch,
         "midna_qld_daily": midna_qld.feed_qld,
         "midna_option_marks": midna_options.feed_marks,
         "midna_hyperliquid": midna_hyperliquid.feed,
         "midna_kronos_forecast": midna_kronos.feed_forecast}

# the hourly watch (scripts/tensor-watch.mjs): the desk supervisor ran it at 10:31, 11:01, ... the close + 1 minute
# (its clock: midna_watch.cadence, due at each :01 / :31 after the last start);
# the option chains (scripts/option-marks.ts): rebuilt every 10 minutes of the session (the books read <= 20 minutes);
# the Kronos forecast (scripts/kronos-forecast.py): kicked at the passes of a weekday whenever one is due (every ten
# sessions)
JOBS = {"midna_watch": ("weekday:12345&et:10:31-16:10", 1800, midna_watch.job, midna_watch.cadence),
        "midna_option_marks": ("weekday:12345&et:09:31-16:00", 600, midna_options.job),
        "midna_kronos": ("weekday:12345&et:09:20-16:00", 1800, midna_kronos.job)}


def sleeves():
    return [context.LiquidMomentum()] + quantpedia.sleeves() + board.sleeves() + [shadow.QqqFlip5Tza()] + \
        [qld.QldWeeklyTiming(), ladder.QqqCspLadder()] + [options.OptionBook(i) for i in options.IDS] + \
        [hyperliquid.HyperliquidFloor(), kronos.KronosTopk()]
