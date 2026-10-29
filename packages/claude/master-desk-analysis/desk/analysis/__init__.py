"""The analysis engine's forward screen, FB2 (docs/research/2026-10-25-engine/DESIGN.md; the research's PROGRAM2.md
Addenda 2-19, 2-19b and 2-19c).

Every completed session gets one immutable screen, state/analysis/screen/<session>.json.gz: one row per equity name
the desk holds daily bars for (the genome, every sleeve's declared names and the held names), with its tier, own
volatility, OW, the SEC-V veto probability P and the veto, the HAR volatility forecast and momentum 6-1. Each equity
long entry in the Execution Lab's tape carries its name's row (desk/lab/research.py).

Counterfactual only: nothing is blocked, and no sleeve, OMS, order, size or book path imports this package.

  engine_score_ref.py  the validator's reference scorer, vendored byte for byte (frozen.py pins its sha256)
  spec/engine_spec.json  the frozen spec deep2-engine-secv-1.0.0-final, vendored byte for byte (pinned likewise)
  frozen.py            the pins and the spec's load
  bars.py              one name's daily bars -> its point-in-time window and features (pure)
  listing.py           the spec's listing filter on Alpaca's asset list and Nasdaq Trader's ETF flags (pure)
  screen.py            one session's cross-section -> its rows: tiers, OW, P, veto, HAR, momentum (pure)
  store.py             the files under state/analysis/ and cache/analysis/
  job.py               the nightly jobs: analysis_inputs (bars and listing into the cache) and analysis_screen"""
SCREEN_VERSION = 1
FB2_START = "2026-10-27"         # FB2 counts from this session's close (PROGRAM2.md 2-19 s5, 2-19c)
