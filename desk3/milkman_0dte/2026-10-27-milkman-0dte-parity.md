# Milkman 0DTE SPX: parity and divergence note (2026-10-27, DEC-02a)

Source of the signals: milkman-study/v2 `21_intraday.py` / `22_intraday2.py` (pinned in `desk/sleeves/milkman/intraday.py`
SOURCE), through the desk's own `lane_trades` over the same SPY panel. Parity of the signals with the study is the
existing `tools/parity/milkman_intraday.py` harness; this sleeve calls the same functions and adds no detection.

Divergences from the study (the study has no options and no daily stop):
1. instrument: a same-day SPXW/SPX option (call on a long lane, put on a short lane) instead of SPY shares;
2. fills: the quoted ask in, a marketable limit under the quoted bid out; no model price anywhere;
3. size: $2,500 premium a trade, at most 4 open (the study: $10,000 notional a trade);
4. day end: flat 15 minutes before the close with limits (options have no MOC); a contract left at the expiry settles in
   cash in the engine (SPXW, PM-settled, S&P 500 close);
5. the -$10,000 daily stop (equity now less equity at the session's first pass) flattens and blocks entries for the session;
6. ESMON (extended hours) and OPX4 (ten-session hold) are not expressed.

Availability: `spx_chain_probe` (weekdays 11:05-13:30 ET) writes `state/probes/spx_0dte.json`; until it records
`available: true` the sleeve is inert with the reason "SPX 0DTE chain not available". Status: UNVERIFIED live.
