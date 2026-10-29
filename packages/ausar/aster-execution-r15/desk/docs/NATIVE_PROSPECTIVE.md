# Native Coinbase prospective paper companion

This companion operates two separate, long-only, fully cash-funded **local paper** books: `ETH_SMA200` and `BTC_ETH_SMA200`. Each receives $100,000 of virtual USD only through an explicit installation command. App construction and `read_status(db_path)` do not install, fund, start a worker or submit an order. The companion uses its own SQLite database and refuses the operating Aster database and files containing unrelated tables. It does not use an Alpaca account, broker credentials, or external order endpoints.

The first sleeve targets 100% ETH when the latest completed UTC daily ETH close is **strictly above** its inclusive 200-day simple moving average, otherwise cash. The second independently targets 50% BTC and 50% ETH, each with its own same gate; a failing asset's share remains cash. No leverage, shorts, parameter refitting, discretionary override or winner selection is added. The frozen R14 indicator and symmetric-price funding helpers are copied unchanged into `backend/prospective_native_math.py`; R15 retains the byte-identical original source and hash provenance. These standard trend mechanisms are not claimed as newly invented.

R14's Yahoo composite historical simulation is a research rationale, not Coinbase venue parity or a prospective return. At 20 basis points per side, historical 2021-01-01 through 2026-10-08 ETH and dual SMA sleeves recorded approximately 41.39% and 31.59% CAGR versus QQQ 16.91%, with substantial drawdowns; neither timing sleeve beat QQQ in the recent 2024 onward subwindow. Coinbase venue results must now be measured prospectively. There is no guarantee of future QQQ outperformance.

## Actual feed and timing

`CoinbasePublicFeed` uses only public HTTPS GET endpoints for the actual BTC-USD and ETH-USD products, their daily candles, and tickers. Product identities, base increments, price ticks, minimum market funds and trading status come from current responses. Every normalized bar, product and quote binds to an actual acquisition receipt containing request/receipt clocks, HTTP status, server Date, raw-payload hash and byte count. Raw UTF-8 response bodies are mandatory, and normalized product metadata, ticker bid/ask and last-trade time, selected candle timestamps and OHLCV must match their parsed raw response exactly. Capture artifacts retain those bodies. The companion database deduplicates them by SHA in `native_raw_sources`; journal receipt metadata points to these retained bodies, avoiding repeated candle payloads on each polling cycle. Missing actual published `min_market_funds` or ordinary-trading mode metadata fails closed; no venue minimum is guessed.

Exactly 200 contiguous, completed UTC daily periods are required. The most recent must complete at the current UTC midnight. No forming day is used, no retrospective archive is treated as contemporaneously received, and a vendor response dated before a candle completed cannot promote it to final. Both signals are acquired before either quote. Quote `as_of` is the actual local HTTP observation clock of that bid/ask snapshot. Coinbase ticker `market_trade_at` is a separate last-trade clock and must be at most 30 seconds old; it is not misrepresented as an exchange timestamp for the bid/ask. Every one of the six GET request starts must follow the current capture start; the complete acquisition must be at most 60 seconds old. Receipt age, source causal order, lot/tick identity and acquisition/server clocks are checked again after a database wait, and quote/entry expiry is checked at each fill.

New or increased positions execute only from **00:00:00 inclusive to 00:05:00 exclusive UTC**, after the just-completed source has genuinely been received. A missed opening creates an explicit expired cycle, never a backdated fill. A failed gate's owned reduction can execute at a genuinely received later quote outside that opening or while entries are disabled. That late exit is an explicit forward operational difference from R14's idealized next-opening historical convention. Unknown or stale source/quotes block decisions instead of manufacturing prices or source knowledge. A failure of either asset feed currently blocks the combined capture; it also delays dependent owned exits until usable observations return.

## Funding, fills and recovery

The local paper venue is fractional USD spot with immediately available **simulated** sale proceeds and zero cash interest. It is separate from the equity desk's T+1 cash book. A **declared simulation charge of 20 basis points per side** is applied to actual observed bid/ask prices; this is not a claim about the owner's Coinbase account fee tier. Buys use ask, sales bid, fee amounts round up to 0.00000001 USD, quantities floor to the actual product base increment, and orders below the product's minimum market funds do not fill. Sub-minimum owned dust can remain and is visible in positions. Lot floors and rounded fees can leave small target-weight differences.

Post-fee midpoint NAV determines funded targets. Reductions fill first; the book's actual local cash and quantities are then reread before increases. Buys are capped by actual available cash, never projected sale proceeds. SQLite transactions commit or roll back orders, fills, cash, positions, cycles and journal events together. Each book owns only its capital and positions. Synthetic interruption and concurrent-run tests verify no partial or duplicate financial effects. Restarting a completed day does not create new fills. Entry disabling preserves held exits; reinstalling preserves existing enable/disable state and never funds again.

The append-only journal is hash chained. Before a financial decision, its installation rules, explicit entry-enable authorization, funding and fill events are replayed and checked against owned book state, cash, quantities, orders and fills. Editing a table enable flag without its journaled authorization cannot create entries. Deterministically closed SQLite connections use rollback journaling; status reads do not create WAL shared-memory sidecars. Revision of a previously observed completed candle is retained as blocking evidence; original observed bars are not silently rewritten. Corrupted monetary state blocks trading. The worker catches failures, records them and retries from durable state without fabricating a repair. `serve` holds a separate process lock, records PID/process identity and heartbeat, and checks actual process existence for status.

Fills model immediate full execution of a declared market-sized paper trade at received top-of-book bid/ask. They do not prove exchange queue priority, available depth, partial-fill behavior or large-order market impact. There are no actual broker fills. A running process plus durable SQLite supports restart recovery; no host-boot service manager or host-reset persistence is claimed.

## Operator commands

From `/workspace/agentic-desk`, using a separate companion database:

```sh
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite status
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite install --enable
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite run
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite serve --interval 30
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite disable --book ETH_SMA200
.venv/bin/python -m backend.prospective_native --db data/native-prospective.sqlite enable --book ETH_SMA200
```

`ASTER_NATIVE_DB_PATH` overrides the companion default; it does not override `ASTER_DB_PATH`. `status` uses a read-only SQLite connection and does not create even a missing directory. `capture --output PATH` records contemporaneous public feeds without opening a financial database. SIGINT/SIGTERM stop `serve` cleanly, preserve durable state and mark its worker stopped. Root integrates the read-only API projection and explicitly installs/starts the companion after independent review; the implementation builder does not activate the operating companion.

## Verification scope

`tests/test_prospective_native.py` uses isolated, explicitly synthetic receipts and price paths to test execution, funding, gate parity, stale-source handling, atomic rollback, restart and owned exits. These software checks are not historical market samples or proof of profitability. R15 stores separate genuine Coinbase capture and operation receipts, copied-source provenance, test logs and independent review. Forward performance begins only when a genuinely timely paper fill occurs; an afternoon feed capture or virtual funding event is not a profitable trade.
