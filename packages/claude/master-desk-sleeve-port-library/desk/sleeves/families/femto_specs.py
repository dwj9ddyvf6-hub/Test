"""Per-sleeve wiring of the 60 Femto-lean sleeves (adapter: femto.py).

Each row is read from the sleeve's own docstring + the OLD desk's runner and cron (midna@7969b52
workspace/alpaca-swing-desk/<sleeve>.py and workspace/goals/alpaca-swing-trading-desk-paper/crons/):

  universe      the old runner's universe file, in its order (iteration order decides who gets capped slots)
  bars          (source, interval, n) of the series passed as `bars`; equity_split = the old desk's SIP
                adjustment=split daily bars (Yahoo OHLC without keys — also split-adjusted)
  schedule      the old cron's window (America/New_York); cadence keeps it to one decision per window
  extra         femto context.extra key -> ONE producer: "@builtin", "feed:<name>", a callable, or a literal
  engine_rules  femto exit-rule kinds the engine executes (the femto core executed only the stop)
  stop_pct      the disaster stop measured from the actual fill (old: GTC stop at fill x (1 - pct))
  target_pct    the take-profit measured from the actual fill (fill x (1 + pct))
  capital       the sleeve's starting book (default $100,000)
  margin_rate   annual interest on the book's debit balance (the engine's daily carry)
  old_desk      the old source this port is audited against (tools/parity receipts in docs/receipts/parity)

Sleeves whose producer does not exist yet stay wired but status "monitor" with the blocker named."""
import json
import os

from ...feedlib.earnings import Earnings
from ...feedlib.sentiment import Fear

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "..", "..", "vendor", "universes", "old_desk")


def _basket():
    """old desk basket.json, in file (rank) order — 41 names after the 2026-10-04 SIVEF removal."""
    with open(os.path.join(VENDOR, "basket.json")) as f:
        return tuple(s["symbol"] for s in json.load(f)["symbols"])


def _lines(name):
    with open(os.path.join(VENDOR, name)) as f:
        return tuple(l.strip() for l in f if l.strip() and not l.startswith("#"))


BASKET = _basket()


def _swing114():
    """old momentum universe: desk/sleeves/momentum/universe_swing_basket_v1.json (frozen 2026-09-30), + SPY."""
    with open(os.path.join(VENDOR, "universe_swing_basket_v1.json")) as f:
        syms = list(json.load(f)["symbols"])
    return tuple(syms + ([] if "SPY" in syms else ["SPY"]))


SWING114 = _swing114()
GENOME = tuple(dict.fromkeys(l.upper() for l in _lines("genome_universe_1838.txt")))   # old research genome
_QP_NAMES = ("NVDA", "AVGO", "META", "AMZN", "AAPL", "MSFT", "GOOGL", "TSLA", "AMD", "NFLX", "COST", "LLY", "JPM",
             "CAT", "GE", "PLTR", "CRWD", "AMAT", "MU", "PANW")             # aurelia_qulla_live NAMES
# the EDGAR buyback scan's universe (old cron desk-edgar-buyback-scan: sorted(basket.json | desk/phase_universe.txt),
# 73 names) — the scan reads them in this order, so its results (the earnings_buyback signals) come in it
EDGAR_UNIVERSE = tuple(sorted(set(BASKET) | set(_lines("phase_universe.txt"))))

OLD = "midna@7969b5229c46/workspace/alpaca-swing-desk/"

SPECS = {
    "donchian": {
        "old_desk": OLD + "donchian_sleeve.py",
        "universe": BASKET,
        "bars": ("equity_split", "1d", 160),          # 160: trail_level rebuilds every past 100-bar window
        "schedule": "open+62:open+72",               # cron donchian-sleeve-daily Mon-Fri 10:32 ET
        "cadence_s": 3600,
        "extra": {"universe": "@universe"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75
    },
    "rsi_meanrev": {
        "old_desk": OLD + "rsi_meanrev_sleeve.py",
        "universe": BASKET,                          # fallback; the live universe is the weekly meanrev watchlist
        "family": "meanrev",                         # old load_universe(): family watchlist when fresh (<= 8 days)
        "bars": ("equity_split", "1d", 360),         # old: SIP split-adjusted since now-520d (~357 sessions)
        "schedule": "rth&minute:3-8",                # cron rsi-meanrev-runner hourly at :03, quiet outside RTH
        "cadence_s": 1800,
        "extra": {"universe": "@universe"},
        "engine_rules": ("stop",),
        "stop_pct": 8.0,                             # GTC stop at fill x 0.92 (old place_stop_loss)
    },
    "rsi_meanrev_options": {
        "old_desk": OLD + "rsi_meanrev_options.py",
        "universe": BASKET,                          # old load_universe(): basket.json, in file order
        "bars": ("equity_split", "1d", 260),         # old fetch_daily_bars: SIP split-adjusted, limit 260, closed bars
        # cron rsi-meanrev-options-runner hourly at :31 around the clock (scan + reconcile): hourly at :31 in the session
        "schedule": "rth&minute:31-36",
        "cadence_s": 1800,
        "extra": {"universe": "@universe", "chains": "@chains:14-30:call", "option_quotes": "@option_quotes"},
        "engine_rules": (),                          # the sleeve's own exits (50% of max profit, 7 DTE, RSI(2) > 70)
    },
    "ema_vwap": {
        "old_desk": OLD + "ema_vwap_sleeve.py",
        "universe": BASKET,
        "bars": ("equity_split", "1d", 120),         # old fetch_daily tail(120)
        "schedule": "rth&minute:57-59,rth&minute:0-2",   # cron ema-vwap-runner hourly at :57
        "cadence_s": 1800,
        "extra": {"universe": "@universe"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75 (Decision #18)
    },
    "ema_vwap_options": {
        "old_desk": OLD + "ema_vwap_options.py",
        "universe": BASKET,                          # ema_vwap_sleeve.universe(): basket.json in file order
        "bars": ("equity_split", "1d", 120),         # ema_vwap_sleeve.fetch_daily: SIP split-adjusted, completed, tail(120)
        # cron ema-vwap-options-runner hourly at :31 around the clock (scan + reconcile): hourly at :31 in the session
        "schedule": "rth&minute:31-36",
        "cadence_s": 1800,
        "extra": {"universe": "@universe", "chains": "@chains:14-30:call", "option_quotes": "@option_quotes",
                  "closed_trades": "@closed_trades"},
        "engine_rules": (),                          # defined risk (no disaster stop): the sleeve's own exits
    },
    "red_day_reversal": {
        "old_desk": OLD + "red_day_reversal_sleeve.py",
        "universe": BASKET,
        "bars": ("equity_split", "1d", 220),         # old fetch_daily_bars limit 220
        "schedule": "rth&minute:43-48",              # cron red-day-reversal-runner hourly at :43
        "cadence_s": 1800,
        "quotes": {"source": "equity"},              # the intraday mark for exits (old: last 5-min close)
        "extra": {"universe": "@universe", "marks": "@marks", "earnings": "feed:earnings"},
        "engine_rules": (),                          # no broker stop: target/stop/time are the sleeve's own
    },
    "momentum_rotation": {
        "old_desk": OLD + "momentum_rotation_sleeve.py",
        "universe": BASKET,
        "bars": ("equity_split", "1d", 100),         # old fetch_daily tail(BARS_LIMIT = 100)
        "schedule": "weekday:1&et:09:35-09:45",      # cron momentum-rotation-runner Mon 09:35 ET (holidays too)
        "cadence_s": 3600,
        "extra": {"universe": "@universe", "last_rebalance": "@state:last_rebalance"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75
        "state_hook": lambda sl, view, private, last: _momrot_hook(sl, view, private, last),
    },
    "momentum": {
        "old_desk": OLD + "momentum_sleeve.py",
        "universe": SWING114,                        # frozen 114-name swing basket + SPY (old mode_rank)
        "bars": ("equity", "1d", 290),               # old: SIP adjustment=all, 420 calendar days (~290 sessions)
        "schedule": "open+35:open+45",               # cron momentum-sleeve-fill Mon-Fri 10:05 ET (rank 16:05 folded in)
        "cadence_s": 3600,
        "quotes": {"source": "equity"},              # fresh regular-hours mid for fills and the 40% breaker
        "extra": {"universe": "@universe", "quotes": "@quotes", "vix": "feed:vix_tuple", "meta": "@meta"},
        "engine_rules": (),                          # SPEC: no protective stop; the breaker is the sleeve's own
        "cost_bps_fn": lambda px: (10.0 if px >= 20 else 25.0 if px >= 5 else 50.0),   # SPEC modeled costs/side
    },
    "capitulation": {
        "old_desk": OLD + "capitulation_sleeve.py",
        "universe": BASKET,
        "bars": ("equity", "1d", 260),               # old _fetch_daily_bars_alpaca: SIP adjustment=all, limit 260
        # old sleeve_core.fetch_1h_bars: SIP 1Hour clock grid since (today - 15d) 00:00Z, then rth_1h_bars (09-15 ET)
        "extra_bars": {"1h": {"source": "sip_clock", "interval": "1h", "n": 400, "since_days": 15, "rth_grid": True}},
        "schedule": "minute:27-32",                  # cron capitulation-runner hourly at :27, around the clock
        "cadence_s": 1800,
        "extra": {"universe": "@universe", "bars_1h": "@bars:1h", "fear_ok": "feed:fear_ok"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75 (_arm_disaster_stop)
        "entry_window": "session",                   # an after-hours detection fills at the next open (old: queued)
    },
    "capitulation_options": {
        "old_desk": OLD + "capitulation_options.py",
        "universe": BASKET,                          # old load_basket(): basket.json, in file order
        "bars": ("equity", "1d", 260),               # old fetch_daily_bars: SIP adjustment=all, limit 260, completed
        # old sleeve_core.fetch_1h_bars(days=10): SIP 1Hour clock grid since (today - 15d) 00:00Z, then rth_1h_bars
        "extra_bars": {"1h": {"source": "sip_clock", "interval": "1h", "n": 400, "since_days": 15, "rth_grid": True}},
        # cron capitulation-options-runner hourly at :31: --mode scan (quiet outside 09:30-16:00 ET), then --mode
        # reconcile (fills, closes, the exits again); here the scan hourly at :31 in the session and the reconcile
        # as an exits-only echo pass minutes later
        "schedule": "rth&minute:31-35,!rth&minute:36-40",
        "cadence_s": 1800,
        "extra": {"universe": "@universe", "bars_1h": "@bars:1h", "chains": "@chains:0-7:call",
                  "option_quotes": "@option_quotes", "fear_ok": "feed:fear_ok",
                  "session_close": lambda sl, view, private, bars: _session_close(view.session),
                  "scan": lambda sl, view, private, bars: _scan_window(sl, view.now),
                  "entering": lambda sl, view, private, bars: _entries_in_flight(sl, view)},
        "engine_rules": (),                          # no disaster stop (the premium is the max loss): its own exits
    },
    "phoenix": {
        "old_desk": OLD + "phoenix_sleeve.py",
        "bars": ("equity_split", "1d", 400),         # old BARS_LIMIT 400, SIP adjustment=split, closed bars
        "schedule": "close-5:close+0",               # cron phoenix-sleeve-1555-entry 15:55 ET (MOC window pass)
        "cadence_s": 120,
        "quotes": {"source": "equity"},              # the 15:55 forming session read (o, last, volume)
        "extra": {"forming": "@forming", "broker_qty": "@broker_qty", "foreign_holders": "@foreign_holders",
                  "meta": "@meta", "closed_trades": "@closed_trades"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop 25% below the entry fill (#18)
    },
    "phase_daily": {
        "old_desk": OLD + "phase_daily.py",
        "universe": _lines("phase_universe.txt"),    # desk/phase_universe.txt, 48 names in file order
        "bars": ("equity_split", "1d", 500),         # old fetch_daily(n=500): SIP adjustment=split, completed bars
        # crons phase-daily 08:46 (pre-market: K5 stops, trail, scr3/breach arms, earnings flatten schedule),
        # phase-intraday every 5 min in RTH (NC nowcast, box-low kill) and its >= 15:55 flatten / re-entry pass
        "schedule": "premarket&et:08:46-08:59,rth,!close-5:close+0",
        "cadence_s": 300,
        "quotes": {"source": "equity"},              # forming daily bar (NC provisional bar), marks (re-entry)
        "extra": {"universe": "@universe", "earnings": "feed:earnings", "earnings_fresh": "feed:earnings_fresh",
                  "forming": "@forming", "marks": "@marks", "closed_trades": "@closed_trades",
                  "nyse_holidays": lambda sl, view, private, bars: _holiday_list(view.session),
                  "session_close": lambda sl, view, private, bars: _session_close(view.session)},
        "engine_rules": ("stop",),                   # box low (K5) / episode low (NC), ratcheted to the EMA50 trail
    },
    "legends_ema": {
        "old_desk": OLD + "legends_ema.py",
        "universe": ("QQQ",),
        "bars": ("equity_split", "1d", 40),          # old: SIP split-adjusted daily bars -> ATR14 of daily ranges
        # old: SIP 5-min bars bucketed to the 15m :00/:15/:30/:45 grid (setup + TP refresh); Yahoo 15m RTH bars
        # are that grid, consolidated, without the free-plan 15-minute SIP delay
        "extra_bars": {"15m": {"source": "yahoo", "interval": "15m", "n": 260}},
        # cron legends-ema-runner every 15 min in RTH; anchors: the open (entry window 09:30-09:45, retried
        # once), five minutes before an early close and 15:59 (the flat)
        "schedule": "rth,!open+1:open+5,!open+6:open+10,!close-5:close-4,!close-1:close+0",
        "cadence_s": 900,
        "quotes": {"source": "equity"},              # the open print (forming bar open)
        "extra": {"bars_15m": "@bars:15m", "forming": "@forming",
                  "nyse_holidays": lambda sl, view, private, bars: _holiday_list(view.session),
                  "session_close": lambda sl, view, private, bars: _session_close(view.session)},
        "engine_rules": ("stop_dist", "target"),     # stop 0.5 x ATR14 from the fill; TP at the (refreshed) EMA
    },
    "morning_dip": {
        "old_desk": OLD + "morning_dip.py",
        "universe": ("QQQ",),
        # old fetch_3min: 1-minute bars from 09:00 ET (pre-market included) -> 3-minute UTC-grid candles;
        # Yahoo 1m with the extended session (consolidated; the old IEX feed was the paper-plan stand-in)
        "bars": ("yahoo_ext", "1m", 420),
        # cron morning-dip-limit-runner every 3 min 10:00-12:00 ET; anchor: the 12:00 flat
        "schedule": "rth&et:09:59-12:00,!rth&et:12:00-12:01",
        "cadence_s": 180,
        "engine_rules": ("stop", "target", "time_bars"),   # bracket stop/target; 15-minute time stop
    },
    "snapback": {
        "old_desk": OLD + "snapback_sleeve.py",
        "universe": GENOME,                          # the genome; the rank's band is its bottom wk$vol decile
        "bars": ("equity_split", "1d", 300),         # 52 weeks + the 20-day spread window; weekly = daily by Monday
        "cache_only": True,                          # the genome job refreshes these after each close
        # crons snapback-rank Fri 16:35 (retried every 30 min until the genome carries Friday's bars) and
        # snapback-fill Mon 10:35
        "schedule": "weekday:5&et:16:35-23:59,weekday:1&et:10:35-10:50",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",                     # quotes for held names and the staged buys/sells only
        "extra": {"meta": "@meta", "quotes": "@quotes"},
        "engine_rules": (),                          # no stop; the 91-day due date is the exit
        "cost_bps": 150.0,                           # D5: 150bp/side modeled for these microcaps
    },
    "leader_d": {
        "old_desk": OLD + "leader_d_sleeve.py",
        "universe": GENOME,                          # the genome, >= 252 bars
        "bars": ("equity_split", "1d", 600),         # old GENOME_DAILY_CACHE keep=600 (SIP, adjustment=split)
        "cache_only": True,
        # crons leader-d-rank Mon-Fri 16:40 (once the genome job wrote today's frames) and leader-d-fill 10:40
        "schedule": "weekday:12345&et:16:40-23:59,weekday:12345&et:10:40-10:55",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "leader_events": "feed:leader_events"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75 (Decision #18)
        "cost_bps": 5.0,                             # 5bp/side modeled
    },
    "leader_sc": {
        "old_desk": OLD + "leader_sc_sleeve.py",
        "universe": GENOME,                          # the band is computed from it point-in-time
        "bars": ("equity_split", "1d", 600),
        "cache_only": True,
        "schedule": "weekday:12345&et:16:50-23:59,weekday:12345&et:10:50-11:05",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "leader_events": "feed:leader_events"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75
        "cost_bps": 150.0,                           # 150bp/side modeled (small-cap band)
    },
    "gate_1h": {
        "old_desk": OLD + "gate_1h_sleeve.py",
        "universe": BASKET,                          # the basket (basket.json, SIVEF already out)
        "bars": ("equity_split", "1d", 600),         # the genome cache (the job keeps it fresh)
        "cache_only": True,
        # old SIP 1Hour clock grid filtered to 09..15 ET bar starts (rth_1h_bars), completed bars
        "extra_bars": {"1h": {"source": "sip_clock", "interval": "1h", "n": 400, "rth_grid": True}},
        # crons gate-1h-sleeve-fill hourly :01 and gate-1h-sleeve-scan hourly :15, 10:00-15:59 ET (the scan
        # runs from :16: the free plan's SIP bars complete 16 minutes after their hour)
        "schedule": "rth&minute:1-6,rth&minute:16-21",
        "cadence_s": 600,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "universe": "@universe", "bars_1h": "@bars:1h",
                  "leader_events_last": "feed:leader_events_last"},
        "engine_rules": ("stop",),
        "stop_pct": 25.0,
        "cost_bps": 10.0,
    },
    "blowoff_d": {
        "old_desk": OLD + "blowoff_d_sleeve.py",
        "universe": GENOME,
        "bars": ("equity_split", "1d", 600),
        "cache_only": True,
        # crons blowoff-d-sleeve-rank Mon-Fri 16:30 (once the genome job wrote today's rows), -fill 10:30
        "schedule": "weekday:12345&et:16:30-23:59,weekday:12345&et:10:30-10:45",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "blowoff_events": "feed:blowoff_events"},
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "blowoff_1h": {
        "old_desk": OLD + "blowoff_1h_sleeve.py",
        "universe": BASKET,
        "extra_bars": {"1h": {"source": "sip_clock", "interval": "1h", "n": 400, "rth_grid": True}},
        # crons blowoff-1h-sleeve-scan hourly :10 and -fill hourly :40, 10:00-15:59 ET
        "schedule": "rth&minute:10-15,rth&minute:40-45",
        "cadence_s": 600,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "universe": "@universe", "bars_1h": "@bars:1h"},
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "donchian_crypto": {
        "old_desk": OLD + "donchian_crypto_sleeve.py",
        "universe": ("SOLUSD",),
        "asset": "crypto",
        "trade_symbols": {"SOLUSD": "SOL/USD"},            # Alpaca paper SOL/USD (the old execution venue)
        "bars": ("kraken", "15m", 120),                     # old fetch_15m_bars: Kraken public OHLC, last 120 closed
        # cron donchian-crypto-runner every 15m, anchored :00:56 — one pass per closed 15m bar, 24/7
        "schedule": "utc_bar:15+45:600",
        "cadence_s": 600,
        "engine_rules": (),
    },
    "ts_momentum_decile": {
        "old_desk": OLD + "ts_momentum_decile.py",
        "universe": GENOME,                          # the v2 panel's 1,838 genome names
        "bars": ("equity_split", "1d", 400),         # the rank sees the last 399 completed sessions (old keep=400)
        "cache_only": True,                          # the genome job refreshes these after each close
        # cron ts-momentum-decile dom 1-4 10:00 ET, self-gated on the first trading day, once per month: the
        # rank stages at 10:00, the next pass fills at fresh mids
        "schedule": "dom:1-4&weekday:12345&et:10:00-15:40",
        "cadence_s": 300,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",                     # held names + the staged buys
        "extra": {"meta": "@meta", "quotes": "@quotes",
                  "nyse_holidays": lambda sl, view, private, bars: _holiday_list(view.session)},
        "engine_rules": (),                          # no stop, no target: the monthly rebalance is the risk
        "cost_bps": 75.0,                            # the study cost the old ledger modeled (COST_BPS = 75)
    },
    "daily_cyan_gbm": {
        "old_desk": OLD + "daily_cyan_gbm_sleeve.py",
        "universe": (),                              # candidates arrive with the nightly DCG scoring file
        "bars": ("equity_split", "1d", 200),         # the held names' own bars: the hold count
        "cache_only": True,
        # crons daily-cyan-gbm rank 16:32 (here: once the nightly scoring file exists), fill 10:32 ET
        "schedule": "weekday:12345&et:16:32-23:59,weekday:12345&et:10:32-10:47",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "dcg": "feed:dcg"},
        "order": {"type": "market", "tif": "cls"},   # market-on-close: entry and exit at the session close
        "engine_rules": ("stop",),
        "stop_pct": 25.0,                            # GTC disaster stop at fill x 0.75 (Decision #18)
        "cost_bps": 10.0,
    },
    "rule_1d_cyan_smallcap": {
        "old_desk": OLD + "rule_1d_cyan_smallcap.py",
        "universe": (),                              # candidates arrive with the nightly DCG scoring file
        "bars": ("equity_split", "1d", 200),         # the held names' own bars: the hold count
        "cache_only": True,
        # crons rule-1d-cyan-smallcap rank 16:34 (here: once the nightly scoring file exists), fill 10:34 ET
        "schedule": "weekday:12345&et:16:34-23:59,weekday:12345&et:10:34-10:49",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "dcg": "feed:dcg"},
        "order": {"type": "market", "tif": "cls"},   # market-on-close: entry and exit at the session close
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "rule_1d_green_tom": {
        "old_desk": OLD + "rule_1d_green_tom.py",
        "universe": (),                              # candidates arrive with the nightly DCG scoring file
        "bars": ("equity_split", "1d", 200),         # the held names' own bars: the hold count
        "cache_only": True,
        # crons rule-1d-green-tom rank 16:36 (here: once the nightly scoring file exists), fill 10:36 ET
        "schedule": "weekday:12345&et:16:36-23:59,weekday:12345&et:10:36-10:51",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "dcg": "feed:dcg"},
        "order": {"type": "market", "tif": "cls"},   # market-on-close: entry and exit at the session close
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "rule_1w_cyan_mom_adx": {
        "old_desk": OLD + "rule_1w_cyan_mom_adx.py",
        "universe": (),                              # candidates arrive with the nightly DCG scoring file
        "bars": ("equity_split", "1d", 200),         # the held names' own bars: the hold count
        "cache_only": True,
        # crons rule-1w-cyan-mom-adx rank 16:38 (here: once the nightly scoring file exists), fill 10:38 ET
        "schedule": "weekday:12345&et:16:38-23:59,weekday:12345&et:10:38-10:53",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "dcg": "feed:dcg"},
        "order": {"type": "market", "tif": "cls"},   # market-on-close: entry and exit at the session close
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "rule_1w_swing_beta_wt": {
        "old_desk": OLD + "rule_1w_swing_beta_wt.py",
        "universe": (),                              # candidates arrive with the nightly DCG scoring file
        "bars": ("equity_split", "1d", 200),         # the held names' own bars: the hold count
        "cache_only": True,
        # crons rule-1w-swing-beta-wt rank 16:42 (here: once the nightly scoring file exists), fill 10:42 ET
        "schedule": "weekday:12345&et:16:42-23:59,weekday:12345&et:10:42-10:57",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "dcg": "feed:dcg"},
        "order": {"type": "market", "tif": "cls"},   # market-on-close: entry and exit at the session close
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "rule_1h_cyan_raw": {
        "old_desk": OLD + "rule_1h_cyan_raw.py",
        "universe": BASKET,                          # the old 41-name 1H basket
        "bars": ("equity_split", "1d", 60),          # the genome cache: the $1M dv20 desk filter
        "cache_only": True,
        # SIP 1Hour clock bars on the RTH grid (09..15 ET starts, closed) — the research's 1H series
        "extra_bars": {"1h": {"source": "sip_clock", "interval": "1h", "n": 1000, "rth_grid": True}},
        # crons rule-1h-cyan-raw-fill hourly :04 and -scan hourly :26, 10:00-15:59 ET
        "schedule": "rth&minute:4-9,rth&minute:26-31",
        "cadence_s": 900,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "bars_1h": "@bars:1h", "fires_1h": "feed:dcg_1h"},
        "engine_rules": (),
        "cost_bps": 10.0,
    },
    "confluence": {
        "old_desk": OLD + "confluence_sleeve.py",
        "universe": (),                              # the M2 job's qualifier file carries the week's candidates
        # crons confluence-sleeve-rank Fri 16:05 (here: once the M2 weekly job has written Friday's file) and
        # confluence-sleeve-fill Mon 10:02
        "schedule": "weekday:5&et:16:05-23:59,weekday:1&et:10:02-10:17",
        "cadence_s": 900,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",                     # held names + the staged buys / sells
        "extra": {"meta": "@meta", "quotes": "@quotes", "m2": "feed:m2", "vix": "feed:vix_tuple"},
        "engine_rules": (),                          # 13-week time exits only, sold in the Monday fill
        "cost_bps": 25.5,                            # the study cost: 51bp round trip, 25.5bp per side
    },
    "beatendown": {
        "old_desk": OLD + "beatendown_sleeve.py",
        "universe": (),
        # crons beatendown-sleeve-rank Fri 16:20 and beatendown-sleeve-fill Mon 10:20
        "schedule": "weekday:5&et:16:20-23:59,weekday:1&et:10:20-10:35",
        "cadence_s": 900,
        "quotes": {"source": "equity"},
        "quotes_for": "pending",
        "extra": {"meta": "@meta", "quotes": "@quotes", "m2": "feed:m2", "vix": "feed:vix_tuple",
                  "fear_ok": "feed:fear_ok"},
        "engine_rules": (),
        "cost_bps": 25.5,
    },
    "bilbo_options": {
        "old_desk": OLD + "bilbo_options.py",        # + bilbo_options_signals.py (vendored byte-identical)
        "universe": _lines("bilbo_options_universe.txt"),   # desk/bilbo_options_universe.txt: the 20, in file order
        # crons bilbo-options-exit-sweep every 5 min 09:30-16:05 ET and bilbo-options-entry-scan hourly at :22
        # (10:22-15:22): here a pass every 5 minutes of the session, one anchored at :22 of each hour 10-15 (the
        # scan's pass). bilbo-iv-nightly-snapshot (18:46) is research collection that no decision reads: not wired.
        "schedule": "rth,!rth&et:10:00-15:59&minute:22-26",
        "cadence_s": 300,
        "extra": {"universe": list(_lines("bilbo_options_universe.txt")), "meta": "@meta",
                  "chains": "@chains:0-60:call", "option_quotes": "@option_quotes",
                  # the scan's compression history (old: SIP 5-min bars 04:00-19:55 ET, split-adjusted, 60 days)
                  "bars_5m": lambda sl, view, private, bars: _bilbo_history(sl, view, private),
                  # the exit sweep's series (old: IEX real-time 5-min bars): the held calls' underlyings, Yahoo 5m
                  "bars_rth": lambda sl, view, private, bars: _held_underlying_bars(sl, view, "yahoo", "5m", 1400),
                  "orders": lambda sl, view, private, bars: _working_orders(view),
                  "session_close": lambda sl, view, private, bars: _session_close(view.session)},
        "engine_rules": (),                          # its exits are the sleeve's own (rail, time cap, box low, giveback)
    },
    "qullamaggie": {
        "old_desk": OLD + "qullamaggie_sleeve.py",
        "universe": GENOME,                          # the leader screen's genome (genome_universe_1838.txt)
        # the held names' completed daily bars (old get_daily_bars tail(150)): the manage law's closes / MAs
        "bars": ("equity_split", "1d", 150),
        "symbols_for": "held",
        "extra_bars": {
            # the screen's genome tape, read once per session (cache-only: the genome job refreshes it)
            "genome": {"source": "equity_split", "interval": "1d", "n": 150, "cache_only": True,
                       "symbols_for": "screen"},
            # today's 5-min RTH bars for the setups only — Yahoo 5m is consolidated and current (the old SIP
            # 5-min fetch was refused for the latest 15 minutes on the paper plan)
            "5m": {"source": "yahoo", "interval": "5m", "n": 100, "symbols_for": "watch"},
        },
        # crons qullamaggie-leader-screen Mon-Fri 08:45 and qullamaggie-enter-manage every 30 min in RTH; here
        # the screen pre-market and one pass 40 s after every 5-min bar close in the session
        "schedule": "premarket&et:08:45-09:24,rth&utc_bar:5+40:200",
        "cadence_s": 240,
        "quotes": {"source": "equity"},
        "quotes_for": "held+watch",                  # the live price for a forming next bar; held names' marks
        "extra": {"meta": "@meta", "quotes": "@quotes", "genome": "@bars:genome", "bars_5m": "@bars:5m",
                  "last_session": lambda sl, view, private, bars: _last_session(view.session)},
        "order": {"type": "market"},                 # old: market day buy / sells (the OMS: marketable limits)
        "engine_rules": ("stop",),                   # the GTC stop at the pre-trigger low, ratcheted to breakeven
        "cost_bps": 3.0,                             # [S3] 2bp slippage + 1bp commission per side
    },
    "tensor_swing": {
        "old_desk": OLD + "scan_and_trade.py",       # + engine/tensor_exact (vendored, hash-pinned v698)
        "universe": BASKET,                          # basket.json's active names (exploratory ARQQ/KVYO excluded)
        "bars": ("equity_split", "1d", 300),         # the structural screen's completed daily bars
        # cron alpaca-desk-scan every 30 min in RTH; the canonical 1H bars complete at :30, so one pass per
        # completed bar, 2-11 minutes after it closes (the 15:30 stub completes 16:30: read at the next open)
        "schedule": "rth&minute:32-41",
        "cadence_s": 1200,
        "extra": {"meta": "@meta", "tensor": "feed:tensor"},
        "engine_rules": ("stop", "target"),          # the bracket: GTC stop-loss and take-profit legs
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
        "state_hook": lambda sl, view, private, last: _tensor_receipt_hook(sl, view, private, last),
    },
    "tensor_red_dip": {
        "old_desk": OLD + "tensor_red_dip_sleeve.py",
        "universe": ("QQQ",) + BASKET,               # the fear gauge + the flagship's basket (its signals' names)
        "bars": ("equity_split", "1d", 5),           # the prior session's close (old: the last 5 IEX daily bars)
        # cron tensor-red-dip-runner every 30 min from 11:05 ET (:05 / :35 around the clock; its off-hours market
        # orders queued for the open): here a pass every 5 minutes of the session
        "schedule": "rth",
        "cadence_s": 300,
        "quotes": {"source": "equity"},
        # the day's price (exits, the red checks, sizing): IEX's mid only near the NBBO, else the last print (the
        # engine's mark rule; the old read the latest 1H IEX bar's running close, a trade)
        "extra": {"fresh": lambda sl, view, private, bars: _flagship_fresh(sl, view.session),
                  "quotes": "@quotes:near", "closed_trades": "@closed_trades",
                  "prev_session": lambda sl, view, private, bars: _last_session(view.session),
                  "nyse_holidays": lambda sl, view, private, bars: _holiday_list(view.session, back=1)},
        "order": {"type": "market"},                 # old: market day buys / sells (the OMS: marketable limits)
        "engine_rules": ("stop", "target", "time_bars"),   # -8% / +3% from the fill; the 3rd trading day
        "stop_pct": 8.0,                             # old: the runner-managed -8% stop
        "target_pct": 3.0,                           # old: the +3% sell-into-strength target
    },
    "leaps_momentum": {
        "old_desk": OLD + "leaps_momentum.py",
        "universe": SWING114,                        # the momentum sleeve's universe: its book is always inside it
        "bars": ("equity_split", "1d", 35),          # old _realized_vol_30d: fetch_daily_bars(limit=35), SIP split
        # cron leaps-momentum-runner hourly at :37 around the clock (mirror -> pmcc -> reconcile): here in the session
        "schedule": "rth&minute:37-42",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "extra": {"momentum": lambda sl, view, private, bars: _momentum_book(sl, "femto_momentum"),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_legs(sl),
                  "leaps_chains": "@chains:365-1500:call", "pmcc_chains": "@chains:25-38:call",
                  # the spot (the LEAPS strike, the PMCC 'tested' roll): IEX's mid only near the NBBO, else the last print
                  "option_quotes": "@option_quotes", "quotes": "@quotes:near"},
        "engine_rules": (),                          # its exits are the sleeve's own (rotation, 60 DTE, -30%, rolls)
    },
    "fear_premium": {
        "old_desk": OLD + "fear_premium_sleeve.py",
        "universe": BASKET + ("TQQQ", "QQQ"),        # the beta candidates (basket.json) + TQQQ + the QQQ benchmark
        "bars": ("equity_split", "1d", 90),          # old fetch_daily_bars(limit=90), SIP split-adjusted
        # cron fear-premium-runner hourly at :55 around the clock (scan + reconcile): hourly at :55 in the session
        "schedule": "rth&minute:55-59",
        "cadence_s": 1800,
        "extra": {"meta": "@meta", "chains": "@chains:25-35:put", "option_quotes": "@option_quotes",
                  "earnings": "feed:earnings", "earnings_fresh": "feed:earnings_fresh", "basket": list(BASKET)},
        "engine_rules": (),                          # the sleeve's own exits (50% profit, 8 days, 21 DTE)
    },
    "iron_condor": {
        "old_desk": OLD + "iron_condor_sleeve.py",
        "universe": ("ARQQ", "NBIS", "WYFI", "AEHR", "POET", "HIVE", "SNDK",
                     "IREN", "CORZ", "ARM", "AXTI", "DGXX", "VELO"),   # the old WATCHLIST, in its scan order
        "bars": ("equity_split", "1d", 5),           # old stock_price: fetch_daily_bars(limit=5), SIP split-adjusted
        # cron iron-condor-runner hourly at :31 around the clock (scan + reconcile): here hourly at :31 from 10:31
        "schedule": "rth&et:10:00-16:00&minute:31-36",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        # the spot (the deep-ITM guard, the ATM IV record, the $10 gate, strikes): IEX's mid only near the NBBO, else
        # the last print (the engine's mark rule)
        "extra": {"universe": "@universe", "meta": "@meta", "chains": "@chains:30-45", "option_quotes": "@option_quotes",
                  "quotes": "@quotes:near", "earnings": "feed:earnings", "earnings_fresh": "feed:earnings_fresh",
                  # old vix_close(): Yahoo ^VIX, the newest value (live while the market trades); None fails closed
                  "vix": lambda sl, view, private, bars: (view.market or {}).get("vix"),
                  # the IV-store backfill (desk/feedlib/iv_backfill.py, job iv_backfill): merged under the sleeve's
                  # own observations so the TRUE IV rank has its history from the first day
                  "iv_backfill": "feed:iv_backfill"},
        "engine_rules": (),                          # the sleeve's own exits (50%, 2x stop, 7 DTE, 21 days, ITM, earnings)
    },
    "vix_hedge": {
        "old_desk": OLD + "vix_hedge_sleeve.py",
        "universe": ("VXX",),
        "bars": ("equity_split", "1d", 30),          # the spot when no quote
        "extra_bars": {"vix": {"source": "yahoo", "interval": "1d", "n": 130, "symbols": ["^VIX"]}},
        # cron vix-hedge-runner hourly at :49 around the clock (scan + reconcile): here hourly at :49 in the session
        "schedule": "rth&minute:49-55",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},
        "extra": {"vix_closes": lambda sl, view, private, bars: _vix_closes(view),
                  "chain": "@chain:VXX:60-110:call", "option_quotes": "@option_quotes", "quotes": "@quotes"},
        "engine_rules": (),                          # its exits are the sleeve's own (mid, VIX, DTE)
    },
    "earnings_buyback": {
        "old_desk": OLD + "earnings_buyback_sleeve.py",
        "universe": EDGAR_UNIVERSE,                  # the EDGAR scan's names (the earnings calendar, spots, bars)
        "bars": ("equity_split", "1d", 5),           # the spot when no quote
        # cron earnings-buyback-runner hourly at :25 around the clock (scan + reconcile): hourly at :25 in the session
        "schedule": "rth&minute:25-30",
        "cadence_s": 1800,
        "quotes": {"source": "equity"},              # the spot (old: the newest SIP 1-hour bar's close)
        # the spot (the $10 gate, strikes): IEX's mid only near the NBBO, else the last print (the engine's mark rule)
        "extra": {"scan": "feed:buyback_scan", "earnings": "feed:earnings", "earnings_fresh": "feed:earnings_fresh",
                  "chains": "@chains:30-45:call", "option_quotes": "@option_quotes", "quotes": "@quotes:near",
                  "meta": "@meta", "closed_trades": "@closed_trades",
                  "sectors": lambda sl, view, private, bars: _risk_sectors()},
        "engine_rules": (),                          # defined risk: the sleeve's own exits (T+15, +/-50%, 5 DTE)
    },
    "spx_premium": {
        "old_desk": OLD + "spx_premium.py",
        "universe": ("XSP",),
        # the XSP level: S&P 500 index daily sessions (Yahoo) / 10, two years for a converged weekly ATR
        "extra_bars": {"spx": {"source": "yahoo", "interval": "1d", "n": 520, "symbols": ["^GSPC"]}},
        # cron spx-premium-entry Mon/Tue 10:07 ET (entry_day_ok gates the week's first session from 10:00)
        "schedule": "rth&weekday:12&et:10:00-10:59",
        "cadence_s": 600,
        "extra": {"meta": "@meta", "spx": "@bars:spx", "chain": "@chain:XSP:0-7:put",
                  "closed_trades": "@closed_trades",
                  "traded_dates": lambda sl, view, private, bars: _week_sessions(view.session)},
        "engine_rules": (),                          # no exit: held to the PM cash settlement (the engine settles)
    },
    "aurelia_ndx": {
        # the Aurelia paper desk as one book (its Nasdaq + gold sleeves; aurelia_gold's GLD rides here):
        # agentic-trading-desk aurelia-paper-desk @1720157f768e desk/paper.py + allocate / session / brain judgment
        "old_desk": "agentic-trading-desk@1720157f768e/desk/paper.py",
        "universe": ("QQQ", "TQQQ", "GLD", "BIL"),
        "bars": ("equity_split", "1d", 10),          # the finished session's closes (the plan's prices)
        "capital": 500_000.0,                        # the source's first staged plan (the old desk's flat book)
        # the supervisor's session opened 09:17 ET and sent once the market was open, until 15 minutes before
        # the close (moc_window); here a pass every 30 minutes of that window (one frozen plan per decision date)
        "schedule": "rth&close-400:close-20",
        "cadence_s": 1800,
        "extra": {"aurelia": "feed:aurelia", "meta": "@meta",
                  "clock": lambda sl, view, private, bars: _alpaca_clock(view.now)},
        "order": {"type": "market", "tif": "cls"},   # market-on-close, filled at the session's official close
        "margin_rate": 0.0775 * 365 / 360,           # Alpaca: debit x 7.75% / 360 per day (the carry is /365)
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "qqq_put_ladder": {
        # the Aurelia source desk's QQQ put ladder: agentic-trading-desk aurelia-paper-desk @1720157f768e
        # desk/ladder_broker.py sync() (inputs, sends) + desk/put_ladder.py (vendored: vendor/aurelia/put_ladder.py)
        "old_desk": "agentic-trading-desk@1720157f768e/desk/ladder_broker.py",
        "universe": ("QQQ",),
        "bars": ("equity_split", "1d", 10),          # QQQ's completed daily closes: the five-session change
        "capital": 1_000_000.0,                      # ~$190,000 secures a layer: the campaign's 12-contract cap binds
        # the supervisor synced the ladder every ~20 s and sent while the session was open until 15 minutes before
        # the close (moc_window), on chain quotes refetched every 15 minutes: a pass every 15 minutes of that window
        "schedule": "rth&close-400:close-15",
        "cadence_s": 900,
        "quotes": {"source": "equity"},
        "extra": {"chain": "@chain:QQQ:0-52:put", "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl), "quotes": "@quotes",
                  "cash": "@cash", "aurelia": "feed:aurelia", "meta": "@meta",
                  "session_close": lambda sl, view, private, bars: _session_close(view.session)},
        "engine_rules": (),                          # the ladder's own buy-backs and rolls
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    # the Aurelia source desk's free-paper option descendants (desk/free_options.py evaluate / execute,
    # desk/option_packages.py submit_package / manage_exits; vendored excerpts: vendor/aurelia/free_options.py).
    # free_paper.run() ran them on every supervisor cycle with market_open = the clock's is_open: a pass every
    # 5 minutes of the session. The inputs the source never produced (the straddle and pair packages, the release
    # calendar, the tail and wheel contracts) come from desk/feedlib/free_options_inputs.py on a chain fetched for the
    # decision; "decided_at" is that chain's receipt (free_opt_core.moment_of), always the last key.
    "free_opt_own_iv": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",
        "universe": ("SPY",),
        "bars": ("equity", "1d", 760),               # SPY's completed daily closes: the HAR-RV forecast's history
        "schedule": "rth",
        "cadence_s": 300,
        "extra": {"quote": lambda sl, view, private, bars: _indicative_probe(sl, view, "SPY", completed=True),
                  "market_open": lambda sl, view, private, bars: _market_open(view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl), "meta": "@meta",
                  "own_iv": lambda sl, view, private, bars: {k: v for k, v in _own_iv_plan(sl, view, private,
                                                                                              bars).items()
                                                             if k != "package"},
                  "package": lambda sl, view, private, bars: _own_iv_plan(sl, view, private, bars)["package"],
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY", completed=True)},
        "engine_rules": (),                          # the package's own exit_at; expiry is the engine's settlement
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_opt_pair": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",
        "universe": ("SPY",),
        "schedule": "rth",
        "cadence_s": 300,
        "extra": {"quote": lambda sl, view, private, bars: _indicative_probe(sl, view, "SPY", completed=True),
                  "hedge": "feed:frozen_hedge",
                  "market_open": lambda sl, view, private, bars: _market_open(view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl), "meta": "@meta",
                  "pair": lambda sl, view, private, bars: {"reason": _pair_plan(sl, view, private, bars)["reason"]},
                  "package": lambda sl, view, private, bars: _pair_plan(sl, view, private, bars)["package"],
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY", "QQQ", completed=True)},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_opt_parity": {
        # the model-test row as the source wrote it, and the economic action its research descendant defines
        # (FWD_RESEARCH_PARITY_V1 / FWD_PARITY_V1): the synchronized call / put / carry package on a positive residual
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",  # + research_descendants, forward_review
        "universe": ("SPY",),
        "schedule": "rth",
        "cadence_s": 300,
        "extra": {"market_open": lambda sl, view, private, bars: _market_open(view), "meta": "@meta",
                  "rate": "feed:tbill", "cash": "@cash",
                  "parity_chain": lambda sl, view, private, bars: _parity_chain(sl, view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "shares": lambda sl, view, private, bars: _shares(view),
                  "working": lambda sl, view, private, bars: _working_orders(view),
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY")},
        "engine_rules": (),                          # the package's own exits; expiry is the engine's settlement
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_opt_release": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",
        "universe": ("SPY",),
        "schedule": "rth",
        "cadence_s": 300,
        "extra": {"quote": lambda sl, view, private, bars: _indicative_probe(sl, view, "SPY", completed=True),
                  "market_open": lambda sl, view, private, bars: _market_open(view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl), "meta": "@meta",
                  "calendar": "feed:release_events",
                  "events": lambda sl, view, private, bars: _release_plan(sl, view, private, bars)["events"],
                  "release": lambda sl, view, private, bars: {k: v for k, v in _release_plan(sl, view, private,
                                                                                              bars).items()
                                                              if k not in ("package", "events")},
                  "package": lambda sl, view, private, bars: _release_plan(sl, view, private, bars)["package"],
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY", completed=True)},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_opt_tail": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",
        "universe": ("SPY",),
        "bars": ("equity_split", "1d", 5),           # SPY's last completed close: the session return's base
        "schedule": "rth",
        "cadence_s": 300,
        "quotes": {"source": "equity"},
        "extra": {"underlying_return": lambda sl, view, private, bars: _session_return(view, bars, "SPY"),
                  "market_open": lambda sl, view, private, bars: _market_open(view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl),
                  "option_quotes": "@option_quotes",
                  "held_sessions": lambda sl, view, private, bars: _held_sessions(view), "meta": "@meta",
                  "quote": lambda sl, view, private, bars: _contract_quote(sl, view, "tail"),
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY", completed=True)},
        "engine_rules": (),                          # the contract's exits (five sessions, 50% premium loss)
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_opt_wheel": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/free_options.py",  # + option_packages.wheel_apply
        "universe": ("SPY",),
        "schedule": "rth",
        "cadence_s": 300,
        "extra": {"cash": lambda sl, view, private, bars: _free_cash(sl, view),
                  "shares": lambda sl, view, private, bars: _shares(view),
                  "market_open": lambda sl, view, private, bars: _market_open(view),
                  "legs": lambda sl, view, private, bars: _option_legs(view),
                  "pending": lambda sl, view, private, bars: _pending_options(sl), "meta": "@meta",
                  "quote": lambda sl, view, private, bars: _contract_quote(sl, view, "put"),
                  "call_quote": lambda sl, view, private, bars: _contract_quote(sl, view, "call"),
                  "decided_at": lambda sl, view, private, bars: _decided_at(sl, view, "SPY", completed=True)},
        "engine_rules": (),                          # expiry and assignment are the engine's settlement
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "qullamaggie_paper": {
        "old_desk": OLD + "desk/aurelia_qulla_live.py",  # + aurelia_qulla_engine.py (vendored: aurelia_qulla/desk.py)
        "universe": ("QQQ",) + _QP_NAMES,            # the engine's market proxy + the carrier's 20 names
        "bars": ("equity_split", "1d", 300),         # the engine's daily frame (the carrier read Yahoo daily OHLC)
        # today's regular-session 1-minute tapes, for the watch list only (the carrier read Alpaca IEX minutes)
        "extra_bars": {"1m": {"source": "yahoo", "interval": "1m", "n": 400, "symbols_for": "watch"}},
        # the Aurelia supervisor's open / close windows; here: the screen pre-market, a pass every minute of the
        # session (entries at the next trade open), the 15:45 scale (market-on-close) and the after-close trail
        "schedule": "premarket&et:09:00-09:24,rth&utc_bar:1+10:45,!close-15:close-11,!after_close+25:after_close+45",
        "cadence_s": 45,
        "quotes": {"source": "equity"},
        "quotes_for": "held+watch",
        "extra": {"meta": "@meta", "quotes": "@quotes", "forming": "@forming", "cash": "@cash", "bars_1m": "@bars:1m",
                  "nyse_holidays": lambda sl, view, private, bars: _holiday_list(view.session, back=1),
                  "session_close": lambda sl, view, private, bars: _session_close(view.session),
                  "eod_session": lambda sl, view, private, bars: _eod_session(view.now)},
        "engine_rules": ("stop",),                   # the engine's hard stop, ratcheted to breakeven after the scale
        "cost_bps": 11.0,                            # the engine's 10bp slippage + 1bp commission per side
    },
    # -- the Aurelia source desk's crypto forward tests (agentic-trading-desk aurelia-paper-desk @1720157f768e) -------
    # Kraken ADA / LINK perpetual books on the sim venue at Kraken's public ticker: completed 4h trade candles (the
    # rule reads the last 22; the hub's chart lookback must stay under the API's 2,000-candle page); the source's
    # supervisor looped every ~20 s — here a pass every 5 minutes plus one at each 4h boundary (open(i+2) and the
    # 16-hour exits fall on it)
    "free_kraken_ada_breakdown": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_paper.py",   # + desk/kraken_clock.py (vendored)
        "universe": ("PF_ADAUSD",),
        "asset": "perp",
        "venue": "sim:kraken_futures",
        "bars": ("kraken_futures", "4h", 60),
        "schedule": "always,!utc_bar:240+0:300",
        "cadence_s": 300,
        "quotes": {"source": "kraken_futures"},
        "extra": {"quote": "@quote"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_kraken_link_breakdown": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_paper.py",
        "universe": ("PF_LINKUSD",),
        "asset": "perp",
        "venue": "sim:kraken_futures",
        "bars": ("kraken_futures", "4h", 60),
        "schedule": "always,!utc_bar:240+0:300",
        "cadence_s": 300,
        "quotes": {"source": "kraken_futures"},
        "extra": {"quote": "@quote"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_kraken_ada_crowded": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_paper.py",   # crowded() + the breakdown clock
        "universe": ("PF_ADAUSD",),
        "asset": "perp",
        "venue": "sim:kraken_futures",
        "bars": ("kraken_futures", "4h", 60),
        "schedule": "always,!utc_bar:240+0:300",
        "cadence_s": 300,
        "quotes": {"source": "kraken_futures"},
        "extra": {"quote": "@quote", "funding": "feed:kraken_funding:PF_ADAUSD"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_kraken_link_crowded": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_paper.py",
        "universe": ("PF_LINKUSD",),
        "asset": "perp",
        "venue": "sim:kraken_futures",
        "bars": ("kraken_futures", "4h", 60),
        "schedule": "always,!utc_bar:240+0:300",
        "cadence_s": 300,
        "quotes": {"source": "kraken_futures"},
        "extra": {"quote": "@quote", "funding": "feed:kraken_funding:PF_LINKUSD"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    # the basis books: the source's basis rule (kraken_history.basis_decision) traded as its research descendant states
    # it — equal-token long spot (sim:kraken) / short perpetual (sim:kraken_futures), unwound together at the prior
    # mean or after 42 completed 4h candles; the perpetual's last 800 completed candles cover the spot OHLC's retained
    # 720; a pass every 5 minutes (IOC legs at the live tickers, a lone leg closed promptly) plus one at each 4h boundary
    "free_kraken_ada_basis": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_history.py",  # + kraken_paper.run's basis row
        "universe": ("PF_ADAUSD",),
        "asset": "perp",
        "bars": ("kraken_futures", "4h", 800),
        "extra_bars": {"spot": {"source": "kraken", "interval": "4h", "n": 720, "symbols": ["ADAUSD"]}},
        "schedule": "always,!utc_bar:240+0:600",
        "cadence_s": 300,
        "extra": {"spot": "@bars:spot", "funding": "feed:kraken_funding:PF_ADAUSD",
                  "instruments": "feed:kraken_instruments", "meta": "@meta",
                  "spot_quote": lambda sl, view, private, bars: _venue_quote(sl, "kraken", "ADAUSD"),
                  "perp_quote": lambda sl, view, private, bars: _venue_quote(sl, "kraken_futures", "PF_ADAUSD")},
        "engine_rules": (),                          # the book's own two-leg unwind
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "free_kraken_link_basis": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/kraken_history.py",
        "universe": ("PF_LINKUSD",),
        "asset": "perp",
        "bars": ("kraken_futures", "4h", 800),
        "extra_bars": {"spot": {"source": "kraken", "interval": "4h", "n": 720, "symbols": ["LINKUSD"]}},
        "schedule": "always,!utc_bar:240+0:600",
        "cadence_s": 300,
        "extra": {"spot": "@bars:spot", "funding": "feed:kraken_funding:PF_LINKUSD",
                  "instruments": "feed:kraken_instruments", "meta": "@meta",
                  "spot_quote": lambda sl, view, private, bars: _venue_quote(sl, "kraken", "LINKUSD"),
                  "perp_quote": lambda sl, view, private, bars: _venue_quote(sl, "kraken_futures", "PF_LINKUSD")},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    # Alpaca USD forwards of the public spot recipes (desk/alpaca_forward.py as desk/forward_cycle.py ran it): a
    # decision only within 300 s of each completed bar's close, so passes run only then; the bars cover the source's
    # 40-day fetch window (the sleeve trims to it)
    "fwd_alpaca_ada_rsi2": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/alpaca_forward.py",  # + desk/forward_cycle.py
        "universe": ("ADA/USD",),
        "asset": "crypto",
        "bars": ("alpaca", "1h", 1000),
        "schedule": "utc_bar:60+0:300",
        "cadence_s": 60,
        "quotes": {"source": "alpaca"},
        "extra": {"quote": "@quote", "meta": "@meta"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    "fwd_alpaca_link_ai_volume": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/alpaca_forward.py",
        "universe": ("LINK/USD",),
        "asset": "crypto",
        "bars": ("alpaca", "4h", 260),
        "schedule": "utc_bar:240+0:300",
        "cadence_s": 60,
        "quotes": {"source": "alpaca"},
        "extra": {"quote": "@quote", "meta": "@meta"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    # Alpaca lists no ENJ/USD (HTTP 404): the book trades Kraken ENJUSD on the labelled sim venue, its recipe installed
    # (the iu_body entry through the forward's decide(), the recipe's ATR trailing stop); every pass checks the stop
    "fwd_alpaca_enj_iu_body": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/alpaca_forward.py",
        "universe": ("ENJUSD",),
        "asset": "spot",
        "venue": "sim:kraken",
        "bars": ("kraken", "5m", 300),
        "schedule": "always",
        "cadence_s": 60,
        "quotes": {"source": "kraken"},
        "extra": {"quote": "@quote", "meta": "@meta"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
    # the Coinbase daily sleeve: one decision per UTC day inside 00:00-00:05 UTC (forward_cycle ran it in its loop)
    "fwd_coinbase_sma200": {
        "old_desk": "agentic-trading-desk@1720157f768e/desk/forward_sleeves.py",  # + desk/coinbase_schedule.py (vendored)
        "universe": ("BTC-USD",),
        "asset": "spot",
        "venue": "sim:coinbase",
        "bars": ("coinbase", "1d", 300),
        "schedule": "utc_bar:1440+0:300",
        "cadence_s": 60,
        "quotes": {"source": "coinbase"},
        "extra": {"quote": "@quote", "meta": "@meta"},
        "engine_rules": (),
        "monitor": lambda mod, bars, ctx: mod.monitor(mod, bars, ctx),
    },
}


def _last_session(session):
    from ... import calendar as cal
    return cal.prev_trading_day(session).isoformat()


def _momentum_book(sl, sleeve_id):
    """another sleeve's live book as a signal: {"book": {SYM: {"qty": shares}} in the order its names filled,
    "ran_at": its last pass} (None when that sleeve has never held anything here)."""
    eng = getattr(sl, "engine", None)
    if eng is None:
        return None
    b = eng.books.books.get(sleeve_id)
    if b is None:
        return None
    book = {inst[3:]: {"qty": float(p["qty"])} for inst, p in b.positions.items()
            if inst.startswith("EQ:") and float(p.get("qty") or 0) > 0}
    return {"book": book, "ran_at": (eng.desk.get("last_run") or {}).get(sleeve_id)}


def _option_legs(view):
    """the sleeve's option contracts {OCC: {"qty", "avg", "opened_at", "meta": position_meta}}."""
    return {inst[4:]: {"qty": float(p["qty"]), "avg": float(p["avg"]), "opened_at": p.get("opened_at"),
                       "meta": dict((p.get("meta") or {}).get("position_meta") or {})}
            for inst, p in (view.positions or {}).items() if inst.startswith("OPT:")}


def _pending_legs(sl):
    """the sleeve's working orders, one row per contract (a package lists each leg): [{"action","occ","key"}]."""
    eng = getattr(sl, "engine", None)
    out = []
    if eng is None:
        return out
    for ch in eng.oms.live_children():
        if ch["sleeve"] != sl.CONFIG.sleeve_id:
            continue
        occs = [l["symbol"] for l in ch.get("legs") or []] or \
            ([ch["inst"][4:]] if str(ch.get("inst", "")).startswith("OPT:") else [])
        out += [{"action": ch["action"], "occ": o, "key": (ch.get("meta") or {}).get("signal_key")} for o in occs]
    return out


def _vix_closes(view):
    """the ^VIX daily closes ending at the live VIX: the completed sessions, then the session's running value
    (the old read Yahoo's daily series, whose newest close is the live VIX while the market trades)."""
    from ...util import et_date
    bl = ((view.extra or {}).get("bars_vix") or {}).get("^VIX") or []
    closes = [float(b["c"]) for b in bl if b.get("c")]
    live = (view.market or {}).get("vix")
    if live and (not bl or et_date(float(bl[-1]["t"])) < view.session):
        closes.append(float(live))
    return closes


def _week_sessions(session):
    """this ISO week's trading sessions (the desk calendar)."""
    from datetime import date, timedelta
    from ... import calendar as cal
    d = date.fromisoformat(session)
    mon = d - timedelta(days=d.weekday())
    return [(mon + timedelta(days=i)).isoformat() for i in range(5) if cal.is_trading_day(mon + timedelta(days=i))]


def _alpaca_clock(now):
    """the desk calendar in the Alpaca clock's shape (is_open, timestamp, next_close) for session.py's rules."""
    from datetime import datetime
    from ... import calendar as cal
    from ...util import ET
    d = cal._as_date(now)
    close = cal.session_close(d) if (cal.is_trading_day(d) and float(now) < cal.session_close(d)) else \
        cal.session_close(cal.next_trading_day(d))
    return {"is_open": bool(cal.is_rth(now)), "timestamp": datetime.fromtimestamp(float(now), tz=ET).isoformat(),
            "next_close": datetime.fromtimestamp(float(close), tz=ET).isoformat()}


def _flagship_fresh(sl, session):
    """the flagship's fresh signals of this session (tensor_swing meta.fresh_signals: its latest pass that held
    any TRADE / WATCH) — None until it has one today (the old: today's journal only)."""
    eng = getattr(sl, "engine", None)
    if eng is None:
        return None
    f = ((eng.store.sleeve_get("femto_tensor_swing") or {}).get("meta") or {}).get("fresh_signals") or {}
    return f if f.get("session") == session else None


def _holiday_list(session, back=0):
    from ... import calendar as cal
    y = int(session[:4])
    return sorted(d.isoformat() for yy in range(y - back, y + 2) for d in cal.holidays(yy))


def _eod_session(now):
    """the last session whose official close is final (20 minutes after its close)."""
    from ... import calendar as cal
    d = cal._as_date(now)
    if cal.is_trading_day(d) and float(now) >= cal.session_close(d) + 1200:
        return d.isoformat()
    return cal.prev_trading_day(d).isoformat()


def _session_close(session):
    from ... import calendar as cal
    return cal.session_close(session) if cal.is_trading_day(session) else None


def _scan_window(sl, now):
    """the pass is its schedule's plain window (the old cron's --mode scan), not only an anchored one (the
    reconcile echo: exits only)."""
    from ...schedule import is_open
    plain = ",".join(a for a in (sl.CONFIG.schedule or "").split(",") if a.strip() and not a.strip().startswith("!"))
    return bool(plain) and is_open(plain, now)


def _entries_in_flight(sl, view):
    """the femto symbols whose entry order still works (the old's awaiting fills: a partly filled buy is no
    position until its order finishes)."""
    return sorted({sl._femto_symbol(o["inst"]) for o in (view.extra or {}).get("pending_orders") or []
                   if o.get("action") == "enter"})


def _bilbo_history(sl, view, private):
    """bilbo_options' compression history, on its scan's pass only: SIP 5-minute bars with the extended session,
    split-adjusted, for the universe (old: alpaca_get_bars_5min --feed sip --adjustment split from 60 calendar days
    back, <= 45 sessions x 192 bars; the bar cache serves its newest 5,000). Without Alpaca keys: Yahoo's 5-minute bars
    with the pre/post session."""
    if not sl.mod.entry_due(view.now, (private or {}).get("meta") or {}):
        return None
    hub = getattr(getattr(sl, "engine", None), "hub", None)
    if hub is None:
        return None
    src = "equity_split" if getattr(hub, "alpaca", None) is not None else "yahoo_ext"
    return hub.bars(src, "5m", list(sl.CONFIG.universe), 8640)


def _held_underlying_bars(sl, view, source, interval, n):
    """bars of the underlyings of the option contracts the sleeve holds (an options sleeve's stock-keyed exits)."""
    from ...data.options import underlying_of
    hub = getattr(getattr(sl, "engine", None), "hub", None)
    syms = sorted({underlying_of(i.split(":", 1)[1]) for i in view.positions if i.startswith("OPT:")})
    return hub.bars(source, interval, syms, n) if (hub is not None and syms) else {}


def _working_orders(view):
    """the sleeve's live order children (inst, action, side, vqty, filled_v, signal_key): its entries and exits in
    flight."""
    return [dict(o) for o in (view.extra or {}).get("pending_orders") or []]


def canonical_receipt(feed, now):
    """EQ-05 (Edge audit 2026-10-25): what the canonical 1H feed served this pass, per symbol [status, last bar],
    against the newest bar a session could have completed by now: a symbol whose last bar is older lags, and its
    swings age in clock hours while they look fresh in bars. (The record of 10-16..10-23 held 51 decisions on bars
    of the same session; its 105 stale WATCHes were swings of the previous session read the next morning.)"""
    status, series, newest = feed.get("status") or {}, feed.get("series") or {}, feed.get("newest")
    per = {s: [status.get(s), int(series[s][-1]["t"]) if series.get(s) else None]
           for s in sorted(set(status) | set(series))}
    lag = [s for s, (_, t) in per.items() if t is None or (newest is not None and t < int(newest))]
    return {"at": float(now), "newest": newest, "symbols": per, "lagging": lag}


def _tensor_receipt_hook(sl, view, private, last):
    """tensor_swing's state: its meta (next_meta, the vendored port's) plus this pass's canonical_receipt, kept here so
    the pinned port is untouched (desk/sleeves/femto/PROVENANCE.json)."""
    feed = (last.get("extra") or {}).get("tensor")
    if isinstance(feed, dict):
        private["meta"] = dict(private.get("meta") or {}, canonical=canonical_receipt(feed, view.now))
    return private


def _momrot_hook(sl, view, private, last):
    """old daily_pass: after a due rebalance with any rankable symbol, last_rebalance = today (orders or not)."""
    mod = sl.mod
    if mod.rebalance_due(private.get("last_rebalance"), view.session):
        bars = {k: v for k, v in (last.get("bars") or {}).items() if v and len(v) >= mod.WARMUP_BARS + 1}
        if mod.compute_ranks(bars):
            private["last_rebalance"] = view.session
    return private

_EARN = {}


def _earnings_book(feeds):
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    if root not in _EARN:
        # in-pass refresh is bounded (5 symbols); the daily `earnings` job refreshes every universe in bulk
        _EARN[root] = Earnings(os.path.join(root, "earnings.json"), clock=feeds.clock, max_per_call=5)
    return _EARN[root]


def _universe_of(sleeve, now):
    return list(sleeve.universe_now(now)) if hasattr(sleeve, "universe_now") else list(sleeve.CONFIG.universe)


def feed_earnings(feeds, sleeve, now, arg):
    """{SYM: next earnings date | None (ETF)} for the sleeve's universe; unknown symbols absent."""
    return _earnings_book(feeds).calendar(_universe_of(sleeve, now))


def feed_earnings_fresh(feeds, sleeve, now, arg):
    return _earnings_book(feeds).fresh(_universe_of(sleeve, now))


def feed_vix_tuple(feeds, sleeve, now, arg):
    """the old fetch_vix shape: (last, previous session close, as-of session, source) — Yahoo ^VIX."""
    q = feeds.hub.quotes("yahoo", ["^VIX"]).get("^VIX") or {}
    if q.get("last") is None:
        return None
    return (float(q["last"]), q.get("prev_close"), q.get("session"), "yahoo")


_FEAR = Fear()


def feed_fear_ok(feeds, sleeve, now, arg):
    """old desk/sentiment.fear_gate_ok: composite >= 55 (FEAR+); unavailable -> True (fail-open)."""
    return _FEAR.gate_ok(now)


def feed_fear(feeds, sleeve, now, arg):
    return _FEAR.snapshot(now)


def feed_leader_events(feeds, sleeve, now, arg):
    """the genome job's leader-frame rows for this session's close (None until written)."""
    from ...feedlib import leader
    from ...util import et_date
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return leader.load(os.path.join(root, "leader_events.json"), et_date(now))


def feed_leader_events_last(feeds, sleeve, now, arg):
    """the leader-frame rows of the last completed session (intraday sleeves read yesterday's close)."""
    from ...feedlib import leader
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return leader.load_last_close(os.path.join(root, "leader_events.json"), now)


def feed_blowoff_events(feeds, sleeve, now, arg):
    """the genome job's last-close blowoff rows for this session (None until written)."""
    from ...feedlib import blowoff
    from ...util import et_date
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return blowoff.load(os.path.join(root, "blowoff_events.json"), et_date(now))


def feed_m2(feeds, sleeve, now, arg):
    """the M2 weekly job's qualifier file written for this rank day (None until written)."""
    from ...feedlib import m2
    from ...util import et_date
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return m2.load_file(os.path.join(root, "m2", "qualifiers.json"), et_date(now))


def feed_dcg(feeds, sleeve, now, arg):
    """the nightly DCG scoring file for this session (None until written)."""
    from ...feedlib import dcg
    from ...util import et_date
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return dcg.load_file(os.path.join(root, "dcg", "scores.json"), et_date(now))


def feed_dcg_1h(feeds, sleeve, now, arg):
    """rule_1h_cyan_raw's fires: the vendored 1H scorer over the basket's closed RTH-grid 1H bars and SMH's
    daily rows (the genome cache)."""
    from ...feedlib import dcg
    from .femto import _trim
    basket = list(sleeve.universe_now(now)) if hasattr(sleeve, "universe_now") else list(BASKET)
    h1 = feeds.hub.bars("sip_clock", "1h", basket, 1000)
    h1 = {s: _trim(bl, now, rth_grid=True) for s, bl in h1.items()}
    smh = feeds.hub.bars("equity_split", "1d", ["SMH"], 600, cache_only=True).get("SMH") or []
    return dcg.score_1h(h1, dcg.rows_of(smh))


def feed_tensor(feeds, sleeve, now, arg):
    """the Tensor engine over the sleeve's canonical 1H series (desk/feedlib/tensor.feed)."""
    from ...feedlib import tensor
    return tensor.feed(feeds, sleeve, now, arg)


def feed_aurelia(feeds, sleeve, now, arg):
    """the Aurelia signal on the last finished session (desk/feedlib/aurelia.feed)."""
    from ...feedlib import aurelia
    return aurelia.feed(feeds, sleeve, now, arg)


def feed_buyback_scan(feeds, sleeve, now, arg):
    """the newest EDGAR buyback scan {"file", "mtime", "scan"} (desk/feedlib/edgar_buyback.py; the edgar_buyback job
    writes one each weekday morning) — its scan_date and mtime travel with it, so the sleeve's own 8-day rule decides
    whether it is fresh; None until a scan exists."""
    from ...feedlib import edgar_buyback
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return edgar_buyback.load_latest(os.path.join(root, "edgar_buyback"))


_SECTORS = {}


def _risk_sectors():
    """the old desk/risk.py SECTORS map (vendored byte-identical: desk/vendor/old_desk_research/risk.py) — the
    earnings_buyback sleeve's own 'max 2 positions in one sector' rule reads it."""
    if not _SECTORS:
        import importlib.util
        path = os.path.join(HERE, "..", "..", "vendor", "old_desk_research", "risk.py")
        spec = importlib.util.spec_from_file_location("old_desk_risk_sectors", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _SECTORS.update(mod.SECTORS)
    return dict(_SECTORS)


# -- the Aurelia source desk's option sleeves (qqq_put_ladder, free_opt_*) ------------------------------------------
def _pending_options(sl):
    """the sleeve's working option orders, one row per contract: [{"action","occ","side","qty" (unfilled),"limit"
    (single-leg),"key","meta" (the entry's position_meta)}]."""
    eng = getattr(sl, "engine", None)
    out = []
    if eng is None:
        return out
    for ch in eng.oms.live_children():
        if ch["sleeve"] != sl.CONFIG.sleeve_id:
            continue
        rem = float(ch["vqty"]) - float(ch.get("filled_v") or 0.0)
        pm = dict((ch.get("meta") or {}).get("position_meta") or {})
        key = (ch.get("meta") or {}).get("signal_key")
        if ch.get("legs"):
            out += [{"action": ch["action"], "occ": l["symbol"], "side": l["side"], "qty": rem * int(l.get("ratio") or 1),
                     "limit": None, "key": key, "meta": pm} for l in ch["legs"]]
        elif str(ch.get("inst", "")).startswith("OPT:"):
            out.append({"action": ch["action"], "occ": ch["inst"][4:], "side": ch["side"], "qty": rem,
                        "limit": ch.get("limit"), "key": key, "meta": pm})
    return out


def _market_open(view):
    """the Alpaca clock's is_open: the desk calendar's regular session."""
    from ... import calendar as cal
    return bool(cal.is_rth(float(view.now)))


def _iso_utc(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


_CHAIN_NEEDS = {}


def free_opt_chain_needs():
    """the expirations the free-option decisions read from their whole-chain reads, as DTE windows (lo, hi; None:
    open), from the decisions' own windows (calendar days from the session, which in the regular session is the
    chain's DTE day): SPY from the nearest listed expiry (the indicative probe's first row: open below) through the
    furthest decision window — own-IV and the tail 21-35, the wheel 7-14, the release 1-45, the parity 1-45, the
    pair 30-60; QQQ the pair's 30-60. They bound the chain asked for only when chains are sliced
    (desk/data/options.py); the rows each read returns are unchanged."""
    if not _CHAIN_NEEDS:
        from ...feedlib import free_options_inputs as FI
        from ..femto import free_opt_parity as PAR
        hi = max(FI.OWN_IV_DTE[1], FI.TAIL_DTE[1], FI.WHEEL_DTE[1], FI.RELEASE_DTE_MAX, PAR.DTE[1], FI.PAIR_DTE[1])
        _CHAIN_NEEDS.update({"SPY": (None, hi), "QQQ": tuple(FI.PAIR_DTE)})
    return dict(_CHAIN_NEEDS)


def _indicative_probe(sl, view, underlying, completed=False):
    """free_options._probe/_snapshot: the indicative snapshot of the underlying's first option contract (Alpaca's
    limit-1 page: the nearest expiry, calls first, the lowest strike) as the monitor quote {"symbol": underlying,
    "t": its quote time, "received_at": when the desk fetched the chain, "bp", "ap"}; None without one. The chain is
    fetched for the decision (a receipt at most FRESH_S old), as the source fetched its snapshot every cycle.
    completed: the receipt is the served chain's completion (_receipt), not the hub's last load attempt."""
    from ...feedlib.free_options_inputs import FRESH_S
    opts = getattr(getattr(getattr(sl, "engine", None), "hub", None), "options", None)
    if opts is None:
        return None
    rows = opts.chain(underlying, now=view.now, max_age=FRESH_S, need=free_opt_chain_needs().get(underlying)) or []
    at = _receipt(opts, underlying, True) if completed else \
        ((getattr(opts, "health", None) or {}).get(underlying) or {}).get("at")
    if not rows or rows[0].get("t") is None or at is None:
        return None
    r = rows[0]
    return {"symbol": underlying, "t": _iso_utc(r["t"]), "received_at": _iso_utc(at), "bp": r.get("bid"),
            "ap": r.get("ask")}


def _per_pass(view, key, fn):
    """one producer result per sleeve pass (several context.extra keys read the same plan)."""
    memo = view.extra.setdefault("_free_opt_inputs", {}) if isinstance(view.extra, dict) else {}
    if key not in memo:
        memo[key] = fn()
    return memo[key]


def _receipt(opts, underlying, completed=False):
    """a chain's receipt: when its fetch completed (completed=True: the tail, the wheel, own-IV, pair and release,
    whose quotes carry times from during the fetch; the record of 2026-10-26 refused 269, 158 and 73 x 3 of their 406
    evaluations on the start), else when it started (received_at: femto_free_opt_parity's economic path keeps it
    until owner decision FEED-12a)."""
    if completed and hasattr(opts, "completed_at"):
        return opts.completed_at(underlying)
    return opts.received_at(underlying) if hasattr(opts, "received_at") else None


def _decision_chain(sl, view, underlying, completed=False):
    """(rows, received_at, spot) of the underlying's chain fetched at most FRESH_S before the decision (the desk's
    options cache serves every free_opt sleeve of the pass from one fetch); (None, None, None) without one. The spot
    is the chain's underlying price (CBOE), else the equity quote's mid. completed: the receipt is the fetch's
    completion (_receipt)."""
    from ...feedlib.free_options_inputs import FRESH_S
    hub = getattr(getattr(sl, "engine", None), "hub", None)
    opts = getattr(hub, "options", None)
    if opts is None:
        return None, None, None
    try:
        rows = opts.chain(underlying, now=view.now, max_age=FRESH_S, need=free_opt_chain_needs().get(underlying))
    except Exception:
        return None, None, None
    at = _receipt(opts, underlying, completed)
    if not rows or at is None or float(view.now) - float(at) > FRESH_S:
        return None, None, None
    spot = opts.spot(underlying) if hasattr(opts, "spot") else None
    if not spot:
        try:
            q = (hub.quotes(hub.equity_source(), [underlying]) or {}).get(underlying) or {}
        except Exception:
            q = {}
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        spot = (float(bid) + float(ask)) / 2 if bid and ask else last
    return rows, float(at), spot


def _decided_at(sl, view, *underlyings, completed=False):
    """the decision moment when the pass fetched its chains after it started: the latest receipt (free_opt_core
    moment_of; completed: the fetches' completion, _receipt); None otherwise."""
    opts = getattr(getattr(getattr(sl, "engine", None), "hub", None), "options", None)
    if opts is None or not hasattr(opts, "received_at"):
        return None
    got = [float(a) for a in (_receipt(opts, u, completed) for u in underlyings) if a]
    return max(got) if got and max(got) > float(view.now) else None


def _completed_closes(bars, sym, now):
    """the underlying's closes of completed sessions (the running session's bar is not a close yet)."""
    from ...feedlib.aurelia_options import closes, completed_through
    got = closes((bars or {}).get(sym), completed_through(now))
    return [got[d] for d in sorted(got)]


def _package_open(private):
    """a package of this book still holds its risk reservation (free_opt_core.reservations): one open package at a
    time, so no new one is offered."""
    from ..femto import free_opt_core as C
    return bool(C.reservations(((private or {}).get("meta") or {}).get("packages")))


def _own_iv_plan(sl, view, private, bars):
    """FREE_OPT_OWN_IV_V1's inputs (desk/feedlib/free_options_inputs.own_iv): the HAR-RV forecast, the straddle's IV and
    the package when the forecast exceeds it by 2 points."""
    def run():
        from ...feedlib import free_options_inputs as FI
        if not _market_open(view):
            return {"package": None, "reason": "the session is closed"}
        if _package_open(private):
            return {"package": None, "reason": "a package is open (one at a time)"}
        rows, at, spot = _decision_chain(sl, view, "SPY", completed=True)
        if rows is None:
            return {"package": None, "reason": "the SPY chain was not fetched"}
        return FI.own_iv(rows, at, spot, view.session, _completed_closes(bars, "SPY", view.now),
                         max(float(view.now), at))
    return _per_pass(view, "own_iv", run)


def _release_plan(sl, view, private, bars):
    """FREE_OPT_RELEASE_V1's inputs: the verified events of the session (feed release_events) and the straddle."""
    def run():
        from ...feedlib import free_options_inputs as FI
        events = list((view.extra or {}).get("release_events") or [])
        if not _market_open(view):
            return {"package": None, "events": events, "reason": "the session is closed"}
        if not FI.todays_events(events, view.session):
            return {"package": None, "events": events, "reason": "no verified public event for %s" % view.session}
        if _package_open(private):
            return {"package": None, "events": events, "reason": "a package is open (one at a time)"}
        rows, at, spot = _decision_chain(sl, view, "SPY", completed=True)
        if rows is None:
            return {"package": None, "events": events, "reason": "the SPY chain was not fetched"}
        return dict(FI.release(rows, at, spot, view.session, events, max(float(view.now), at)), events=events)
    return _per_pass(view, "release", run)


def _pair_plan(sl, view, private, bars):
    """FREE_OPT_PAIR_V1's package: the frozen hedge as the source attached it ({"hedge": ...}) and, once its residual
    leaves the band, the two legs (desk/feedlib/free_options_inputs.pair)."""
    def run():
        from ...feedlib import free_options_inputs as FI
        hedge = (view.extra or {}).get("frozen_hedge")
        base = {"hedge": hedge} if hedge else None
        if not hedge or not hedge.get("signal"):
            return {"package": base, "reason": (hedge or {}).get("reason") or "no frozen hedge"}
        if not _market_open(view):
            return {"package": base, "reason": "the session is closed"}
        if _package_open(private):
            return {"package": base, "reason": "a package is open (one at a time)"}
        packages = ((private or {}).get("meta") or {}).get("packages") or {}
        if "pair-%s" % hedge.get("signal_session") in packages:
            return {"package": base, "reason": "this signal session's package was already sent"}
        chains = {u: _decision_chain(sl, view, u, completed=True) for u in ("SPY", "QQQ")}
        stamps = [c[1] for c in chains.values() if c[1]]
        r = FI.pair(chains, hedge, view.session, max([float(view.now)] + stamps))
        return {"package": r["package"] or base, "reason": r["reason"]}
    return _per_pass(view, "pair", run)


def _parity_chain(sl, view):
    """FREE_OPT_PARITY_V1's snapshot: the SPY chain fetched for the decision and the underlying's bid / ask. A CBOE
    chain carries the underlying's quote in the same snapshot (one market time for every leg; the package then fills
    on sim:options at that snapshot); an Alpaca chain does not — the live equity quote stands beside the live
    indicative contracts, each with its own time, and the package takes the desk's default route. None without."""
    if not _market_open(view):
        return None
    rows, at, spot = _decision_chain(sl, view, "SPY")
    if rows is None:
        return None
    hub = sl.engine.hub
    q = (hub.options.quotes(["SPY"]) or {}).get("SPY") or {}
    if q.get("bid") and q.get("ask"):
        return {"rows": rows, "spot_bid": float(q["bid"]), "spot_ask": float(q["ask"]), "spot_t": q.get("t"),
                "spot_received_at": at, "received_at": at, "venue": "sim:options"}
    try:
        q = (hub.quotes(hub.equity_source(), ["SPY"]) or {}).get("SPY") or {}
    except Exception:
        q = {}
    if not q.get("bid") or not q.get("ask") or not q.get("t"):
        return None
    return {"rows": rows, "spot_bid": float(q["bid"]), "spot_ask": float(q["ask"]), "spot_t": float(q["t"]),
            "spot_received_at": float(q.get("_at") or q["t"]), "received_at": at, "venue": ""}


def _contract_quote(sl, view, kind):
    """the tail's put, or the wheel's put / covered call, from the decision chain (free_options_inputs.tail /
    wheel); None outside the session or without a qualifying contract."""
    from ...feedlib import free_options_inputs as FI
    if not _market_open(view):
        return None
    rows, at, spot = _decision_chain(sl, view, "SPY", completed=True)
    if rows is None:
        return None
    if kind == "tail":
        return FI.tail(rows, at, spot, view.session)
    return FI.wheel(rows, at, spot, view.session, kind)


def _hedge_package(view):
    """free_options.run(): package = {"hedge": the frozen hedge} when one is frozen, else None."""
    hedge = (view.extra or {}).get("frozen_hedge")
    return {"hedge": hedge} if hedge else None


def _session_return(view, bars, sym):
    """the underlying's session return: the live mid (else last) over its last completed daily close, - 1."""
    from datetime import datetime
    from ...util import ET
    q = (view.quotes or {}).get(sym) or {}
    bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
    px = (float(bid) + float(ask)) / 2 if bid and ask and float(ask) >= float(bid) > 0 else last
    prior = [b for b in (bars or {}).get(sym) or []
             if datetime.fromtimestamp(float(b["t"]), tz=ET).date().isoformat() < view.session]
    if not px or not prior or not prior[-1].get("c"):
        return None
    return float(px) / float(prior[-1]["c"]) - 1.0


def _held_sessions(view):
    """{OCC: trading sessions completed since the contract's fill (the fill session's own counts at its close)}."""
    from ... import calendar as cal
    return {inst[4:]: cal.trading_days_between(float(p.get("opened_at") or view.now), float(view.now))
            for inst, p in (view.positions or {}).items() if inst.startswith("OPT:")}


def _free_cash(sl, view):
    """the wheel's cash: the book's cash less the strike value of every short put it holds or is selling."""
    from ...data.options import occ_parse
    cash = float(view.cash)
    for inst, p in (view.positions or {}).items():
        if inst.startswith("OPT:") and float(p["qty"]) < 0:
            _, _, cp, k = occ_parse(inst[4:])
            cash -= k * 100.0 * -float(p["qty"]) if cp == "put" else 0.0
    for o in _pending_options(sl):
        if o["action"] == "enter" and o["side"] == "sell":
            _, _, cp, k = occ_parse(o["occ"])
            cash -= k * 100.0 * float(o["qty"]) if cp == "put" else 0.0
    return cash


def _shares(view):
    """{SYM: shares held} (an assignment delivers them)."""
    return {inst[3:]: float(p["qty"]) for inst, p in (view.positions or {}).items()
            if inst.startswith("EQ:") and float(p.get("qty") or 0)}


def _venue_quote(sl, source, sym):
    """a venue-native book's live ticker in the femto quote shape ({"bid","ask","bp","ap","last","t"}; the hub's
    batched quotes), None without one — the basis books read their spot and perpetual tickers side by side."""
    from .femto import _quote_row
    hub = getattr(getattr(sl, "engine", None), "hub", None)
    if hub is None:
        return None
    try:
        q = hub.quotes(source, [sym]).get(sym)
    except Exception:                              # an unreachable venue: no quote (the sleeve blocks its entry)
        return None
    return _quote_row(q) if q else None


def feed_frozen_hedge(feeds, sleeve, now, arg):
    """the SPY/QQQ hedge frozen from prior closes (desk/feedlib/aurelia_options.feed)."""
    from ...feedlib import aurelia_options
    return aurelia_options.feed(feeds, sleeve, now, arg)


def feed_kraken_funding(feeds, sleeve, now, arg):
    """kraken_funding:<PERPETUAL> — Kraken's hourly funding prints as the API lists them (desk/feedlib/kraken)."""
    from ...feedlib import kraken
    return kraken.funding(arg, now)


def feed_kraken_instruments(feeds, sleeve, now, arg):
    """kraken_instruments — the Kraken futures instrument list (desk/feedlib/kraken)."""
    from ...feedlib import kraken
    return kraken.instruments(now)


def feed_kraken_depth(feeds, sleeve, now, arg):
    """kraken_depth:<PAIR> — the Kraken spot book, count 5 (desk/feedlib/kraken)."""
    from ...feedlib import kraken
    return kraken.depth(arg, now)


FEEDS = {"aurelia": feed_aurelia, "vix_tuple": feed_vix_tuple, "tensor": (feed_tensor, {"per_sleeve": True}), "fear_ok": feed_fear_ok, "fear": feed_fear, "m2": feed_m2, "dcg": feed_dcg,
         "dcg_1h": feed_dcg_1h,
         "blowoff_events": feed_blowoff_events,
         "leader_events": feed_leader_events, "leader_events_last": feed_leader_events_last,
         "earnings": (feed_earnings, {"per_sleeve": True}),
         "earnings_fresh": (feed_earnings_fresh, {"per_sleeve": True}),
         "buyback_scan": feed_buyback_scan}
FEEDS["frozen_hedge"] = feed_frozen_hedge       # the Aurelia PAIR descendant's SPY/QQQ hedge (feedlib/aurelia_options)
FEEDS.update({"kraken_funding": feed_kraken_funding, "kraken_instruments": feed_kraken_instruments,
              "kraken_depth": feed_kraken_depth})


def feed_iv_backfill(feeds, sleeve, now, arg):
    """the iron condor's IV-store backfill {SYM: [[session, iv], ...]} (desk/feedlib/iv_backfill.py); {} until the
    iv_backfill job has written one."""
    from ...feedlib import iv_backfill
    root = os.path.dirname(os.path.dirname(feeds.hub.cache.root)) if feeds.hub is not None else "."
    return iv_backfill.load(root)


FEEDS["iv_backfill"] = feed_iv_backfill


def job_iv_backfill(engine):
    """the iron condor's IV history from Alpaca's historical option bars (needs Alpaca credentials): its own
    measurement recomputed per past session, written for the sleeve to merge under its own observations."""
    from ...feedlib import iv_backfill
    if engine.broker is None or engine.hub is None:
        return {"skipped": "no Alpaca credentials: the store warms up from the sleeve's own daily observations"}
    from datetime import datetime
    from ...util import ET
    universe = list(SPECS["iron_condor"]["universe"])
    bars = engine.hub.bars(engine.hub.equity_source(), "1d", universe, 400) or {}
    closes = {s: {datetime.fromtimestamp(float(b["t"]), tz=ET).date().isoformat(): float(b["c"]) for b in bl}
              for s, bl in bars.items()}
    store = iv_backfill.run(engine.broker, universe, closes)
    iv_backfill.write(engine.root, store, engine.clock())
    return {"names": len(store), "observations": sum(len(v) for v in store.values())}


def feed_release_events(feeds, sleeve, now, arg):
    """the verified public event timestamps (desk/feedlib/release_calendar.py): CPI and the Employment Situation from
    FRED's release calendar, the FOMC statements from the Fed's meeting calendar; [] until the job has written them."""
    from ...feedlib import release_calendar
    root = os.path.dirname(os.path.dirname(feeds.hub.cache.root)) if feeds.hub is not None else "."
    return release_calendar.load(root)


FEEDS["release_events"] = feed_release_events


def feed_tbill(feeds, sleeve, now, arg):
    """the 3-month T-bill rate (FRED DTB3, desk/feedlib/tbill.py): FREE_OPT_PARITY_V1's carry; None until cached."""
    from ...feedlib import tbill
    root = os.path.dirname(os.path.dirname(feeds.hub.cache.root)) if feeds.hub is not None else "."
    return tbill.load(root)


FEEDS["tbill"] = feed_tbill


def job_release_calendar(engine):
    """the release calendar FREE_OPT_RELEASE_V1 reads: this year's and next year's pages, parsed and cached."""
    from ...feedlib import release_calendar
    return release_calendar.job(engine.root, engine.clock())


def job_tbill(engine):
    """the parity carry's discount rate: FRED's DTB3 file, its newest observation cached."""
    from ...feedlib import tbill
    return tbill.job(engine.root, engine.clock())


# slow producers the loop launches beside its passes (desk/registry.family_jobs)
JOBS = {"iv_backfill": ("weekday:12345&et:08:00-09:20", 20 * 3600, job_iv_backfill),
        # the release calendar: five public pages, refreshed twice a day (at the loop's start, then every 12 hours)
        "release_calendar": ("always", 12 * 3600, job_release_calendar),
        # the T-bill rate: one public CSV, the same cadence
        "tbill_rate": ("always", 12 * 3600, job_tbill)}
