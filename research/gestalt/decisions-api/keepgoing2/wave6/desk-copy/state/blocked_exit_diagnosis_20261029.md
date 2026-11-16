# BLOCKED-EXIT DIAGNOSIS 2026-10-29 (phase: diagnose, NO cure code)

Read live 2026-10-29 21:10-21:35 UTC against paper account PA36X7WU3
(identity proven from the desk keys before any action, per
local-alpaca-paper skill). Desk runner is LIVE and cycling
(state/runner.json: pid 4940, cycle 5, ts 2026-10-29T21:08:13Z), so
counts move; snapshots below are timestamped.

## 1. Broker ground truth (21:10 UTC, re-verified 21:35 UTC)

- Account PA36X7WU3 ACTIVE, trading_blocked=false.
- equity $990,141.82 -> $988,497.57; cash $2,773,767.35 (short proceeds).
- buying_power (effective) $76,419.97 -> $64,177.78;
  regt_buying_power $0; non_marginable_buying_power $0.
- initial_margin $1,025,918.18 -> $1,026,740.30 (EXCEEDS equity by
  ~$36-38k); maintenance_margin ~$876-877k (cushion ~$111-114k);
  multiplier 4; SMA $2,394,038.81.
- Positions (ALL short, 7 names, short MV -$1,783,625.53 = 180% of
  equity; ~210% at the close-review snapshot):
  ANF -171 (-$28,215), AXTI -13,414 (-$778,012; 78.6% of equity at
  $58.00, 91% at the close-review price), CORZ -9,234 (-$129,277),
  FFIV -796 (-$289,314), SOXL -6,156 (-$555,394), TWST -7 (-$1,170),
  VSAT -27 (-$2,059).
- Open orders: 8 (NOT zero; the desk kept cycling after the close
  review was written). Six buy_to_close covers from
  aster_saty_research accepted 20:41-20:42 UTC (ANF 171, AXTI 13,414,
  FFIV 796, SOXL 6,156, TWST 7, VSAT 27), each fully reserving its
  position (qty_available=0 on those six names). Two CORZ
  sell_to_open 9,234 from aster_trader_donchian55 accepted 20:40 and
  21:00 UTC (would DOUBLE the CORZ short if filled at the open).

## 2. Desk queue ground truth (state/broker_pending.json)

- 828 live entries at 21:10 UTC (776 at the close review; the queue
  GREW ~52 during the evening because the runner keeps cycling).
  All session_date 2026-10-29. Attempts: median 3, max 378.
- By error: 826 x HTTP 403 code 40310000 "insufficient buying power";
  2 x HTTP 422 code 42210000 (ADAUSDT).
- By kind/side/intent: 782 x (exit, sell, sell_to_close);
  29 x (exit, buy, sell_to_close); 17 x (exit, sell, None).
- By sleeve: aster_trader_donchian55 623, s_mn_vwap 141,
  aster_saty_research 29, rest scattered.
- By symbol: FFIV 182, AXTI 165, CORZ 146, SOXL 124, TSEM 82,
  TTMI 82, ANF 12, LITE 12, TSLA 11, TWST 5, VSAT 5, ADAUSDT 2.
  NOTE: TSEM and TTMI have NO broker position at all; FFIV/AXTI/
  CORZ/SOXL broker positions are SHORT while the queued exits are
  sell_to_close (a LONG close). Exit qtys are sleeve-virtual, not
  broker: AXTI exits carry qty 7,011 vs broker -13,414; FFIV exits
  342 vs broker -796.
- Captured 403 bodies (229 with both fields): buying_power at
  rejection ranged $0.00-$91,105.83; every order's cost_basis
  exceeded it (min cost_basis/buying_power ratio 1.49). Examples:
  TSEM sell 3,762: cost_basis $709,099.40 vs BP $55,565.02;
  TTMI sell 6,156: $541,430.69 vs $55,176.70; CORZ sell 9,234:
  $134,105.41 vs $60,288.04.
- Dispatcher mechanics (desk3/dispatcher.py): process_intent treats
  ANY 403 as broker-unavailable/transient (DRAIN-CLASS-20261026,
  _broker_unavailable_class: status in (403,429) or >=500), retries
  in-call x3, persists to the pending store, drains at the start of
  every cycle with DRAIN_CAP=20 in store order. A 403 exit is NEVER
  terminal, so phantom exits retry forever within the session and
  fresh exits queue behind them.

## 3. The door strips the intent (code root)

desk3/broker.py PaperDoor.submit_order builds the wire body as
{symbol, side, qty, type, time_in_force, client_order_id,
limit_price?} — position_intent is NEVER sent, and stop_price is
never sent either (no protective stop can reach the broker through
this door). Alpaca therefore INFERS intent from side + the actual
broker position:
- buy vs short position -> buy_to_close (no buying-power charge);
- sell vs long position -> sell_to_close;
- sell vs short/flat position -> sell_to_open: a NEW short, charged
  full margin against buying power.

## 4. Mechanism experiments (paper, after close; every accepted
diagnostic order was cancelled and the cancellation read back;
final book verified unchanged, 8 desk orders intact)

- E4 (fresh reproduction, desk wire shape): TSEM sell 3,762 market
  day, NO position_intent -> 403 {"buying_power":"72620.78",
  "code":40310000, "cost_basis":"703287.11", "message":
  "insufficient buying power"}.
- E5 (one factor changed: + position_intent=sell_to_close): SAME
  order -> 422 {"code":42210000, "message":"position intent
  mismatch, inferred: sell_to_open, specified: sell_to_close"}.
  The broker states in writing that it infers sell_to_open for
  these exits, and with an explicit close intent the buying-power
  gate is replaced by position validation.
- E6 (size variation): TSEM sell 1, no intent -> ACCEPTED, broker
  stamped position_intent "sell_to_open"; cancelled, read back
  "canceled". Proves the 403 is a notional-vs-buying-power
  comparison, not a blanket block, and that the "exit" is executed
  by the broker as a new short entry when small enough to pass.
- E1/E2/E3 (CORZ covers: buy 1 no-intent; buy 9,234 with
  buy_to_close; buy 9,234 no-intent): ALL -> 403 code 40310000
  "potential wash trade detected. use complex orders",
  reject_reason "opposite side market/stop order exists",
  existing_order_id = the desk's own resting CORZ sell_to_open.
  Code 40310000 is shared by three distinct rejections (insufficient
  BP, wash trade, insufficient qty); the queue bodies are the BP
  variant, but TONIGHT the CORZ cover path is additionally blocked
  by the desk's own resting entry orders.
- E8 (vary type/TIF/extended-hours): CORZ buy 1 limit $14.50,
  extended_hours=true, buy_to_close -> same wash-trade 403.
- E7 (reservation): TWST buy 1 buy_to_close -> 403 40310000
  "insufficient qty available for order (requested: 1, available:
  0)", held_for_orders "7" — the desk's resting cover holds the
  whole position.
- Live positive control (not a diagnostic order): the six
  aster_saty_research buy-side covers were ACCEPTED at 20:41-20:42
  UTC including AXTI 13,414 (~$778k notional vs ~$76k buying
  power). Buy-side exits against short positions are inferred
  buy_to_close and are NOT charged against buying power. E4/E6
  prove submission-time validation is fully live after hours, so
  this acceptance is real evidence, not deferred checking.

## 5. ADAUSDT 422 pair

- Source: desk3/aster_crypto.py SPECS carry sym="ADAUSDT" (perp /
  Coinalyze funding namespace; funding symbols are ADAUSDT_PERP.A).
  evaluate() emits Intent(symbol="ADAUSDT", side="sell",
  position_intent="sell_to_close") verbatim; this family never got
  the broker-dialect translation that aster_batch1._broker_symbol
  got on 2026-10-27 (BTC-USD -> BTC/USD, crypto TIF day -> gtc).
- Correct Alpaca form: ADA/USD. E9a GET /v2/assets/ADA/USD ->
  active, tradable. E9b GET /v2/assets/ADAUSDT -> 404
  {"code":40410000,"message":"asset not found for ADAUSDT"}.
  E9c fresh desk-shape ADAUSDT sell 27 -> 422 {"code":42210000,
  "message":"asset \"ADAUSDT\" not found"} (reproduces the queue).
  E9d ADA/USD sell 27 gtc sell_to_close -> passes asset validation,
  fails 403 "insufficient balance for ADA (requested: 27,
  available: 0)": no ADA position exists at the broker.
- Deeper defect: aster_crypto.evaluate() iterates EVERY nonzero
  position in its view (poss list, aster_crypto.py line ~113) and
  stamps its own symbol on each exit with qty=abs(position qty),
  never filtering p.symbol == sym. The adapters3 view passes the
  full broker book as the positions list (adapters3/_snapshot_ctx:
  producer broker_readback; port/bridge ViewCtx passes a list
  positions object through unfiltered). In cycle 5 the two
  normalization sleeves emitted ADAUSDT exits carrying the qtys of
  FFIV (796), SOXL (6,156), TWST (7), VSAT (27) — dispatcher.jsonl
  holds 392 ADAUSDT events today. Even symbol-normalized, these
  exits are phantoms: the sleeves hold no ADA.
- Where normalization belongs: (a) at emission in aster_crypto —
  filter positions to the sleeve's own symbol and translate to the
  broker dialect (ADA/USD, gtc) following the aster_batch1
  precedent; (b) as defence at validate_intent / the door — a
  perp-namespace symbol must never reach the wire untranslated.

## 6. Causal answer (why risk-reducing orders get BP rejections)

The orders being rejected are risk-reducing only inside the
sleeves' virtual ledgers. At the broker they are not closes at all:

1. Sleeve virtual books diverged from the single netted broker
   account. 333 sleeves trade overlapping symbols into one account;
   entries net against each other at the broker while each sleeve
   keeps its own virtual position. donchian55 and s_mn_vwap believe
   they hold longs (TSEM 3,762, TTMI 6,156, FFIV, AXTI, CORZ, SOXL)
   that at the broker are shorts or nothing. Their exits are
   sell_to_close orders for positions the broker does not hold long.
2. The door drops position_intent (and stop_price) from the wire
   body, so the broker infers intent from side + real position:
   sell vs short/flat = sell_to_open (proven by E5's mismatch body).
   An opening short is margin-checked on full notional.
3. The account has no opening headroom: the margined short book
   grew to 180-210% of equity; initial margin ($1,026,740) exceeds
   equity ($988,498); regt buying power is exactly $0 and effective
   buying power swung $0-$91k intraday. Every queued exit's
   notional ($134k-$709k) exceeds it, so every one is refused
   40310000. This is the 2026-10-26 ORDER-403 class recurring on
   the new account: the account switch restored BP, the book
   consumed it again, and this time the BP wall is hit by EXIT
   traffic because of (1) and (2).
4. Dispatcher behaviour turns the wall into a flood: 403 is
   classified transient/broker-unavailable, never terminal, so 826
   phantom exits retry every cycle (attempts up to 378), grow the
   queue (776 -> 828 tonight), and FIFO-drain ahead of genuine
   exits. Meanwhile the entry side is still live: donchian55
   rested two CORZ sell_to_open orders tonight that now wash-block
   the only uncovered name's covers (E1/E2/E3/E8).
5. Genuine covers work: buy-side exits against the real shorts are
   inferred buy_to_close, bypass the BP check entirely (AXTI's
   $778k cover accepted against ~$76k BP), and six of seven names
   now have full covers resting for the open. The blocked names are
   exactly those whose exit traffic is sell-side phantom closes
   (CORZ) or already fully reserved by resting covers.

Status: DIAGNOSED, NOT CURED. Cure owed (next phase): wire
position_intent + stop_price through PaperDoor; validate/repair
exit intents against the broker book (an exit whose side/intent
contradicts the broker position must be reconciled to the real
close or terminally rejected, not retried as an opening order);
make the 403 class for exits terminal-or-reconciled instead of
infinite-retry; symbol-dialect translation + own-symbol position
filter for the aster_crypto family; address the resting CORZ
sell_to_open pair that wash-blocks covers. No strategy, sizing,
stop-design, threshold, roster or Tensor change is needed for any
of that: every defect above is in the order path and bookkeeping,
not in any sleeve's decisions.
