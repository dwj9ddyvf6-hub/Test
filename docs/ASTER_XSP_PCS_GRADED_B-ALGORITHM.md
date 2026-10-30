Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_xsp_pcs_graded_b: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_xsp_pcs_graded_b.py is the per-sleeve
core: evaluate() delegates to the shared engine desk3/aster_b4.py
evaluate(SLEEVE_ID, view, ctx), with INPUTS = INPUTS_XSP and
PRODUCERS = PRODUCERS_XSP taken from that engine. It sells a
weekly XSP put credit spread (PCS) whose strikes are set from the
prior week's close and weekly ATR14, gated by a prior-week
"digital" regime statistic. The sleeve runs on the shared engine
desk3/aster_b4.py (leg selection ports
r19_options.py::select_xsp_legs + _xsp + _weekly_atr14 +
_xsp_digital).

## Spec (from SPECS in desk3/aster_b4.py)
book="OPT_XSP_GRADED_B", family="xsp_pcs", structure="graded",
risk=0.01 (risk budget fraction of the $10,000 v3 slice).
- Inputs (INPUTS_XSP): options, positions, xsp_state.
- Fees: $0.65 per contract per leg (recorded assumption; the
  source reads a snapshot fee schedule no v3 producer supplies).

## Entry rules
- Entry only on the first session of the week, 10:00-10:05 ET.
  Entry-window clock (ENH-B13-XSP-ETWIN-20261024, switch default
  ON): timezone-aware stamps are converted to ET before the
  window test; OFF restores the raw string slice (the paired
  shadow control).
- Regime gate: the prior-week digital (from the mids of two
  adjacent same-expiry XSP puts) requires at least 26 distinct
  prior weekly observations, each in (0, 1), with the last 52
  used for percentiles; the current digital must be below the
  75th percentile, and for the "graded" structure
  there is no median skip (the graded structure trades in either regime, with strike distances set by the regime below).
- Strike targets: short strike targets prior_close - ATR14 * (1.0
  when the current digital is below the median (calm regime),
  1.236 otherwise). Long strike targets prior_close - ATR14 * (1.618 in the calm regime, 1.786 otherwise). The chosen
  contracts are the listed weekly-PM-expiry XSP puts nearest
  those targets.
- Credit must be positive: credit = (short bid - long ask) * 100.
  Max loss per package = width - credit + 2 leg fees, and must
  satisfy 0 < max loss < width.
- Sizing: qty = min(risk_budget / max_loss_per_package,
  cash / width, displayed sizes on both legs); qty < 1 emits
  nothing. One package per book: no entry while a package is
  held.

## Exit rules
- The source's ONLY exit: the European legs settle at the weekly
  PM expiry (official_PM_expiry); on or after the expiry session
  the package emits a settle exit intent. No earlier price stop
  exists in the source.

## Data inputs
Declared inputs: options, positions, xsp_state. Producers named
in the engine: bars (900s freshness), options_chain (900s,
outputs options), broker_readback (900s, positions),
xsp_index_regime (900s, outputs xsp_state). Inputs not produced
by v3 producers (OPRA chain, XSP index-regime state) leave this
sleeve UNFED in the registry, never fake-fed.
