# Femto-lean wiring and paper-run readiness

## Current status

The strategy source and runtime wiring are separated:

- This repository contains the Pine indicator, algorithm contract, research, and sleeve.
- Runtime integration is in [Femto-lean branch bb-rsi-live-readiness-20261024](https://github.com/dwj9ddyvf6-hub/Femto-lean/tree/bb-rsi-live-readiness-20261024).
- The sleeve is paper-enabled in code (CONFIG.parked=False). Its PR is still a draft and has not been merged or deployed. No paper orders have been sent from this work.

The Femto-lean broker path requires paper_only=true and uses Alpaca's paper endpoint; the broker code rejects other endpoint configuration. This makes the staged path a paper route. It does not validate the actual runtime host, credentials, account, or market-data entitlement.

## Runtime wiring

The branch adds a curated, editable 12-symbol US ETF universe; completed regular-session 1-hour bars and SIP quotes; held-symbol inclusion for exit monitoring; a persisted hourly cursor for entry deduplication; sleeve-specific fills/open-order state; and a dedicated 5-minute scan. The broad desk scan cadence remains unchanged.

New entries fail closed when required bars, quote, equity, bar-cursor, or order/fill lifecycle state is missing or stale. Each paper entry uses 0.25% of sleeve equity as base risk, with volatility/trend reductions, a 5% notional ceiling, a 15 bp spread ceiling, and one filled entry per session. The risk and notional caps apply to this sleeve; they are not portfolio-wide risk controls.

For open positions, the strategy rechecks the current fresh completed hourly bar on each five-minute scan, even when the entry cursor has already consumed that bar. It evaluates a primary stop, Bollinger-basis target, 24-bar time exit, and bearish divergence. A working protection stop does not mask these exits; core verifies cancellation before a strategy close. Active strategy closes suppress duplicates and block new entries until resolved. If one bar touches both stop and target, the stop is assumed first.

The broker-side stop is a GTC stop-market order and may execute beyond its trigger during gaps or fast markets. Target, time, and divergence exits are not broker-native OCO orders; they can be delayed until a completed hourly bar is observed by the next five-minute scan. Paper qualification must measure this latency and fill behavior.

## What has been verified here

Python compilation and synthetic exit-path checks passed against the Femto Intent contract. The checks cover stop protection not masking a target exit, exit evaluation after cursor consumption, close-order deduplication, re-entry blocking, missing order-state abstention, and conservative stop-first ordering.

No authenticated request, broker order, paper fill, or deployment was performed. This environment cannot verify the target host's secret source, Alpaca account ID/status, SIP entitlement, scheduler heartbeat, or post-restart reconciliation. These remain required before calling the running paper system operationally qualified.

## Paper-run checklist

Before the autonomous paper process is started:

1. Merge/deploy the staged branch only to the intended paper runner. Confirm config/live.json still has paper_only=true, the paper base URL, and the intended paper account ID.
2. Verify credentials resolve only from the paper secret source. Do not copy API keys into Git, logs, or chat.
3. Verify the Alpaca data source returns SIP quotes and completed 1-hour bars. If entitlement or freshness checks fail, entries should remain blocked. Alpaca's Basic equities plan may be IEX-only rather than SIP: [market-data plans](https://docs.alpaca.markets/us/docs/about-market-data-api).
4. Observe a clean startup and five-minute scheduler heartbeat. Confirm the BB scan ledger records its input times, active universe, candidate abstentions, order/fill IDs, and protection status.
5. Exercise paper order acceptance, partial fills, cancel/replace races, timeouts, restart recovery, stop cancellation, and close reconciliation before relying on unattended operation. A timeout must be reconciled by client-order ID before retrying.
6. Keep an operator kill switch available during the initial paper observation and review positions, open orders, and ledger state each session.

Paper fills are operational integration evidence, not proof of positive expectancy. Existing research found five candidate events across 268 sessions and did not model fills, exits, costs, or portfolio P&L.

## Separate real-money release gates

This paper route is not a live-money authorization. Real-money use requires a separate review and a fail-closed portfolio-wide risk gateway for account status, equity/buying power, total exposure, position count, daily loss, reconciliation, and account-wide kill switch; approved account-specific limits; a live endpoint/account-ID boundary; verified data access; and chronological fill-aware out-of-sample plus shadow/paper qualification. The current runtime does not satisfy those conditions.

Alpaca paper and live trading use separate credentials/endpoints, and paper fills do not reproduce all live conditions: [paper trading](https://docs.alpaca.markets/us/docs/paper-trading) · [order types and lifecycle](https://docs.alpaca.markets/us/docs/orders-at-alpaca).
