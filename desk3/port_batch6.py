"""Batch-6 port registry: raschke_rre, red_day_reversal, rsi_meanrev,
rsi_meanrev_options, rule_1d_cyan_smallcap, rule_1d_green_tom,
rule_1h_cyan_raw, rule_1w_cyan_mom_adx, rule_1w_swing_beta_wt, saty_day.

Each row carries the v2 config row verbatim (same slice/cadence/session/
flat_by_close) plus its producer-registry declaration: the inputs the
sleeve's evaluate() consumes from the single snapshot. Producers are
registered once; a sleeve whose declared input is unproduced or stale
is UNFED at cycle start (registry contract), never silently abstaining.
Adapter modules live in desk_sleeves/ (module name == sleeve id);
strategies live byte-identical in sleeves/.
"""
from __future__ import annotations

# producer name -> (outputs, freshness_sla_s)
PRODUCERS = {
    "bars_daily": (("bars_1day",), 93600.0),
    "bars_hourly": (("bars_1hour",), 7200.0),
    "bars_intraday": (("bars_5min", "bars_1min"), 900.0),
    "positions": (("positions",), 900.0),
    "earnings": (("earnings",), 93600.0),
    "options": (("options_chains", "options_quotes"), 900.0),
    "rule_fires": (("rule_fires", "rule_fires_1h", "log_mcap",
                    "trading_days"), 93600.0),
    "session": (("session_fills", "latest_quotes"), 900.0),
}

# id -> (module, cadence_s, flat_by_close, flatten_time_et, session, inputs)
_ROWS = {
    "raschke_rre": (60, False, None, "rth",
                    # SLEEVE-FIRING-20261111: was "latest_quotes"; the
                    # adapter reads ctx.latest_quotes() -> view["quotes"],
                    # the live StockQuotes producer's key.
                    ("bars_5min", "positions", "session_fills", "quotes",
                     "macro_events")),
    "red_day_reversal": (300, False, None, "rth",
                         ("bars_1day", "positions")),
    "rsi_meanrev": (300, False, None, "rth",
                    ("bars_1day", "positions", "earnings")),
    "rsi_meanrev_options": (300, False, None, "rth",
                            ("bars_1day", "positions", "options_chain",
                             "options_quotes")),
    "rule_1d_cyan_smallcap": (300, False, None, "rth",
                              ("bars_1day", "positions", "rule_fires", "log_mcap")),
    "rule_1d_green_tom": (300, False, None, "rth",
                          ("bars_1day", "positions", "rule_fires", "trading_days")),
    "rule_1h_cyan_raw": (300, False, None, "rth",
                         ("bars_1hour", "bars_1day", "positions", "rule_fires_1h")),
    "rule_1w_cyan_mom_adx": (300, False, None, "rth",
                             ("bars_1day", "positions", "rule_fires")),
    "rule_1w_swing_beta_wt": (300, False, None, "rth",
                              ("bars_1day", "positions", "rule_fires")),
    "saty_day": (60, True, "15:55", "rth",
                 ("bars_5min", "bars_1min", "positions", "options_chain",
                  "options_quotes", "session_fills")),
}

SLEEVE_IDS = tuple(_ROWS.keys())


def config_rows():
    rows = []
    for sid, (cadence, flat, flat_t, session, inputs) in _ROWS.items():
        rows.append({
            "id": sid, "module": sid, "cadence_s": cadence, "parked": False,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": flat,
            "flatten_time_et": flat_t, "session": session, "timeout_s": None,
            "params": {}, "inputs": list(inputs),
            "adapter_dir": "desk_sleeves",
        })
    return rows


def register_into(desk, producer_fns=None):
    """Register batch-6 producers + sleeves on a desk3.cycle.Desk.
    producer_fns: {producer_name: callable(ctx)->{key: data}}; producers
    without a fn are registered in the registry only (their outputs stay
    unproduced until a warm supplies them => sleeves report UNFED)."""
    producer_fns = producer_fns or {}
    for name, (outputs, sla) in PRODUCERS.items():
        fn = producer_fns.get(name)
        if fn is not None:
            desk.add_producer(name, fn, outputs, sla)
        else:
            desk.registry.register_producer(name, outputs, sla)
    for row in config_rows():
        desk.add_sleeve(row["id"], row["module"], inputs=tuple(row["inputs"]),
                        cadence_s=row["cadence_s"],
                        slice_usd=row["slice"]["capital_usd"])
    return desk
