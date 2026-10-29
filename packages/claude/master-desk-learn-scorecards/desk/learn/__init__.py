"""The desk's learning layer — it measures, remembers and calibrates EXECUTION; it never edits a sleeve's
strategy (every sleeve is under forward test: its rules stay frozen, its record stays honest).

  attribution  per-sleeve forward record from the virtual books (P&L, trades, expectancy, drawdown, Sharpe,
               exits by reason, holding periods) and desk totals
  tca          fill quality from the OMS: slippage vs the decision reference by sleeve / asset / fill source
  scorecard    the old desk's graduation bar per sleeve (proposals for User, never a switch)
  calibrate    bounded, logged execution calibration (marketable-limit buffers per asset class) and the
               replica allocation across sleeves (equal, or evidence-weighted once a sleeve has a record)
  memory       the desk journal (one digest per session) + durable facts the desk learned
  health       self-awareness: liveness, missed windows, sleeve errors, data sources, jobs, ledger chain"""
