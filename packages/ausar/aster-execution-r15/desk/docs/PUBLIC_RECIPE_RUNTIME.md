# Public recipe paper companion

Three independent spot research books execute the recovered public Pine recipes on native clocks: `PUBLIC_TOMAZETTI_RSI2_SPOT100` / ADAUSDT1h, `PUBLIC_IU_BODY_SPOT100` / ENJUSDT5m, and `PUBLIC_AI_VOLUME_SPOT100` / LINKUSDT4h. They use Binance production public market-data endpoints and virtual USDT cash. They are separate from the seven existing Aster sleeves and from the gated original TraderDev strategies. No broker/order API, account credential, deposit or live trade is used.

Application construction and `read_status(path)` install and fund nothing. Explicit operator installation creates three independently owned $100,000-equivalent **virtual USDT** books, with a recorded principal event for each. USDT and USD are not asserted interchangeable realized cash. Installation is idempotent and never refunds an existing book. Existing books require the explicit enable command to change their entry policy.

```sh
python -m backend.public_recipe_runtime install --db data/public-recipes.sqlite --enable
python -m backend.public_recipe_runtime status --db data/public-recipes.sqlite
python -m backend.public_recipe_runtime serve --db data/public-recipes.sqlite --interval 20
python -m backend.public_recipe_runtime disable --db data/public-recipes.sqlite
```

The root service coordinator may supervise the explicitly installed worker. The companion uses an exclusive `fcntl` worker lease, genuine PID/start-tick identity, atomic heartbeat receipts and graceful SIGTERM/SIGINT shutdown. Status verifies matching process birth and heartbeat age; a stopped process cannot be called autonomous. Daemon output contains bounded summaries. A feed outage records failure and retries on the next cycle.

## Frozen source and declared transfer

The reducer in `strategies/public_recipes/public_source_sleeves.py` is byte-identical to the reviewed R14 source, SHA256 `e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9edecc2d99722e6b`. The three recovered Pine files and source binding are adjacent. Hash mismatch refuses use. Pine compiler parity and original TraderDev parity have not been established.

- Tomazetti: RSI2<10, close>SMA200, SMA4(RSI2)<30; exit close>SMA5. Original whole strategy block has a2009–2020 bar-opening date window. This current variant explicitly extends its end input to2030-12-30T00:00UTC. Stops default off; source allocation100% equity.
- IU: confirmed body>4×[sum(body[0..20])/20], preserving the source21/20 arithmetic. First completed held bar anchors ATR14×2 stop to actual average entry; later held closes ratchet without loosening. Newly tightened stops need a strictly later observed quote.
- AI: volume>2×current-inclusiveEMA20(volume), candle direction and close/EMA50 trend alignment. Every qualifying signal resets then increments the counter, including a same-side signal while held. Exit at count5; source no-pyramid semantics retained.

AI and IU default source declarations omit explicit sizing. Their standard-default fixed1-unit historical cases are retained separately. Installed spot variants declare **100%-equity order intent**, long-only market/side transfer; actual displayed-depth partial fills can produce much smaller exposure. Unsupported short research decisions remain visible, and an opposite short decision can still flatten an owned long. No perpetual funding or borrow capability is invented; perpetual deployment remains pending production contract/funding/fee/margin inputs.

## Market receipt and execution contract

Production public requests use the desk's bounded HTTP transport: absolute8-second deadline, maximum256,000bytes, no redirects. UTC native candle completion must precede the actual HTTP receipt; forming rows are excluded. Existing first-seen native bars are immutable. Corrections, late interior backfills, missing bars and acquisition failures block new entries while healthy quotes retain owned stop/exit service. The exact EMA/Wilder recurrence persists separately from bounded checkpoint windows; trimming does not reseed indicators. Native source decisions and raw admitted candle rows remain append-only.

The bid/ask observation clock is the actual HTTP receipt. The endpoint does not provide an exchange quote timestamp. Latest exchange trade time is separately recorded and must be no more than60seconds old for entries. Quotes are fetched after bar acquisition. Current production spot metadata supplies the symbol, status, price tick, lot step, minimum quantity/notional and maximum quantity. Model costs explicitly debit10bps each side **in addition to observed bid/ask spread**; this is a hypothetical local paper cost policy, not an actual account fee receipt.

New entries require their **own originating completed candle**, current quote, actual processing clock and actual acknowledgement all strictly before origin completion+300seconds. A newer candle cannot extend an old target/order's window. Quotes must remain no more than10seconds old at processing and acknowledgement; contract/cost receipts must still be usable at acknowledgement. Expired, blocked or disabled unfilled entries receive owned cancellation acknowledgements. Disabling entries preserves positions, owed closes and quote stops.

Local fills use observed ask for purchases and bid for sales. Each receipt preserves `source_allocation_intended_qty`; the actual paper venue order is capped to current maximum order quantity and lot-floor, then acknowledged only up to actual displayed depth. A full-book target above a venue maximum can therefore produce a legal smaller order. Chunks below minimum quantity/notional are vetoed. Partial opening acknowledgement retains the measured fill and cancels its remainder; no automatic additions or pyramiding are invented. Partial owned closes continue against later genuinely fresh quotes using the original owned order. Accepted entry contract identity remains on positions so missing current metadata cannot strand a protective exit. These receipts describe local paper assumptions, not guaranteed venue execution, exchange liquidity across levels, or broker fills.

Each book's cash and position derive from its own accepted events. Initial install-enabled policy is bound to the principal event; subsequent explicit enable/disable actions append strict-boolean control events. The checkpoint binds SQL's exact integer0/1 flag, and full replay derives current entry authority from its recorded history. Direct flag edits cannot authorize entries. Full money/control-journal replay, event-chain hash, checkpoint/config/indicator hashes and native-source hash are verified on restart and read-only status; external database changes invalidate cached replay and force rechecking. A prototype schema lacking bound policy history is refused rather than guessing past authorization. This detects local inconsistency, without claiming that local editable files are an external tamper-proof audit system. Existing main-ledger names and foreign schemas/application identities are refused. Each accounting effect is transactional. No source bars, quotes or funding are backdated to an intended opening.

Idle quotes replace the latest observation rather than growing the immutable financial journal. Native admitted bars and financial decisions/fills/cancellations remain durable; raw native rows and decision quote bodies are deduplicated. Checkpoint tails remain bounded, with exact indicator recurrence and complete journal retained in SQLite. Host availability, storage capacity and ongoing public feed access remain operational dependencies.

## Research evidence

The registered R15 study includes20 strategy cases and12 passive controls on real native bars, January2024 through September2026. Source sizing and100% allocation overlays, spot transfers and perpetual venue transfers, and10/25bps hypothetical execution-cost cases are separate. Historical OHLC stops, zero-latency next-opening approximation and funding mark proxies/bounds are distinct from this actual-receipt paper runtime.

The positive LINK spot100% case returned14.20% versus LINK spot buy-and-hold−3.95%; QQQ returned83.26%. Its25bps stress returned−14.38%. The recovered RSI2 and IU counterparts did not beat QQQ in this registered period. These results do not reproduce the inaccessible leaderboard strategies or justify claiming future profitability. The full native records, funding gaps, receipts and limitations are in `research-archives/2026-10-09-aster-execution-r15/public-source-native-tests` when published.
