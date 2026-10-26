"""Audited Qlib TopkDropout selection reference, with declared economic overlays.

Source: microsoft/qlib qlib/contrib/strategy/signal_strategy.py, retrieved
2026-10-08, TopkDropoutStrategy.generate_trade_decision. This is an independent
reference for candidate order, not a substitute for Qlib's exchange simulator.
Native defaults are method_buy='top', method_sell='bottom', only_tradable=False.
The extra prior-close eligible mask is a reconstruction constraint: disallowed
names cannot be new candidates and existing disallowed names rank as missing.
"""
from __future__ import annotations
import numpy as np


def select_topk_dropout(scores, symbols, held, eligible, executable,
                        held_sessions, topk, n_drop, min_hold=1,
                        only_tradable=False):
    """Return native planned candidates and the sales executable this session.

    `held` is actual positive-share indexes; `held_sessions` is a length-N array
    of completed holding steps (at order time). Missing held predictions rank
    last, as in Qlib's reindex(...).sort_values(ascending=False). min_hold and
    execution checks occur AFTER selecting bottom n_drop, without substitutes.
    Native buy count uses planned sales, before blocked-sale checks. New buy
    candidates never contain any current holding, including a planned sale.
    Ties use symbols deterministically; upstream pandas tie behavior is not a
    stable strategy promise. Zero drop is explicitly none, avoiding [-0:].
    """
    score = np.asarray(scores, dtype=float).copy()
    symbols = np.asarray(symbols).astype(str)
    eligible = np.asarray(eligible, dtype=bool)
    executable = np.asarray(executable, dtype=bool)
    held_sessions = np.asarray(held_sessions)
    held = list(map(int, held))
    score[~eligible] = np.nan

    def key(j):
        return (not np.isfinite(score[j]), -score[j] if np.isfinite(score[j]) else 0,
                symbols[j])

    def first(sequence, count):
        sequence = [j for j in sequence if executable[j]] if only_tradable else sequence
        return sequence[:max(0, int(count))]

    last = sorted(held, key=key)
    candidates = sorted([j for j in np.flatnonzero(eligible & np.isfinite(score))
                         if j not in held], key=key)
    today = first(candidates, n_drop + topk - len(last))
    combined = sorted(set(last) | set(today), key=key)
    bottom_pool = [j for j in combined if executable[j]] if only_tradable else combined
    bottom = bottom_pool[-int(n_drop):] if n_drop > 0 else []
    planned_sell = [j for j in last if j in bottom]
    planned_buy = today[:max(0, len(planned_sell) + topk - len(last))]
    actual_sell = [j for j in planned_sell
                   if executable[j] and held_sessions[j] >= min_hold]
    actual_buy = [j for j in planned_buy if executable[j]]
    return dict(last=last, today=today, combined=combined,
                planned_sell=planned_sell, actual_sell=actual_sell,
                planned_buy=planned_buy, actual_buy=actual_buy)


def dropout_buy_budget(cash, actual_sale_dollars, sell_bps=10,
                       buy_bps=10, risk_degree=.95):
    """Fee-affordable dollars after ACTUAL clipped sales, native cash risk rule.

    Return total buy notional, divided across the planned buys by caller. Qlib
    multiplies post-sale cash by risk_degree; buy-cost affordability is an
    explicit shared-ledger economic correction. Retained shares are untouched.
    """
    post_sale_cash = max(0., float(cash) + float(actual_sale_dollars) * (1 - sell_bps / 10000))
    return post_sale_cash * float(risk_degree) / (1 + buy_bps / 10000)
