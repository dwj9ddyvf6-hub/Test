# ON PAPER IMPLEMENTATION SPEC, 2026-11-15 (CV-3)

Sleeve: `on_focus29`, a paper sleeve on muse-desk-v3 expressing ON_focus29 in auction form.
Status of this document: build spec only. Nothing in this spec is built, landed, or proven.
The live desk tree is NOT touched tonight (Sun 2026-11-15). Monday 2026-11-16 staging is frozen.
This sleeve lands only in the desk lane's next cure window, by the gate path in section 11.
No em dashes are used in this document, per the owner's standing rule.

## 0. Plain language summary

A basket of 29 stocks has, on the estate's own exam, tended to rise between the market close
and the next market open. That tendency is worthless if the stocks are bought and sold by
crossing the quoted spread: the measured spread cost is larger than the tendency. It survives
only if every buy happens in the closing auction and every sell happens in the opening
auction, at the official auction prints. This spec builds exactly that, on paper: buy the
basket in the closing auction, sell it in the next opening auction, drop any name that
cannot use an auction that night rather than paying its spread, and grade every night
against the shadow accrual that already grades the find. If the numbers stop working, the
stop lines in section 12 say so in numbers, in advance.

## 1. Purpose and object

### 1.1 The object

A single new paper sleeve on the desk (repo muse-desk-v3, package desk3) that expresses the
ON_focus29 find in its auction form:

- Entry: Market-on-Close (MOC) orders, filled at the official closing auction prints.
- Exit: Market-on-Open (MOO) orders, filled at the official opening auction prints of the
  next session.
- One overnight hold per session. No intraday trading, no options expression, no shorting.
- Paper only, through the desk's existing PaperDoor. No live money path is created or used.

### 1.2 The find, with its numbers

Source reports: WAVE-4-2026-11-14.md and WAVE-5-2026-11-14.md in
research_notes/decisions-api-leverage-20261114/, and the production shadow accrual
keepgoing2/wave4/v1_shadow_accrual.py in the same tree.

- Wave 3 exam, ON_focus29 overnight leg (previous close to this open, equal weight):
  DSR 0.99994 at trial count 6.
- Wave 4 re-print at the pre-registered family trial count of 10: DSR 0.99910, PROMOTE.
  SPA 0.001 against SPY and 0.002 against QQQ at every count printed. The verdict fails at
  count 50 and at the pooled program bound of about 260, which is why the forward falsifier,
  not the historical exam, is the promotion gate.
- Wave 4 family exam, the overnight family as one family at combined count 45:
  PROMOTE, PBO 0.000, SPA 0.000 against SPY and 0.001 against QQQ. ON_focus29 inside it:
  DSR 0.9995, Sharpe 1.67, t 4.97, mean +0.165 percent per night, 2,229 sessions,
  2018-01-03 to 2026-11-13.
- Friction, measured in Wave 4 (keepgoing2/wave4/v1_friction.json, 10 sessions,
  2026-11-02 to 2026-11-13, SIP quotes and prints):
  - Basket gross, equal weight: +18.91bp per night (mean of per-name full-history means;
    the basket series itself prints +16.5bp).
  - Crossing form (quoted half-spread at close plus quoted half-spread at open):
    net -27.17bp per night. Dead. Median name crossing round trip 41.24bp. The accrual's
    crossing leg, as corrected by Wave 6, is the MEAN of the per-name medians: +46.076bp
    of cost. The +41.2bp figure cited before Wave 6 was the median of those medians and
    was mislabeled.
  - Auction form (MOC in, MOO out), bar-based: net +19.53bp per night. Basket-level signed
    print-versus-mid auction cost -0.6bp (prints landed a hair better than mid). Per-name
    auction medians on the wide names are mid-reference noise and are never used per name;
    only the basket level is cited.
- Wave 5 corrections, which this spec treats as governing:
  - The daily bar close IS the closing auction print: 60 of 60 name-sessions exact, 0.0bp,
    on the six CARRY names over the same 10 sessions.
  - The daily bar open is NOT the opening auction print: 4 of 60 exact, pooled mean signed
    gap +5.436bp (bar open above the opening cross print), and systematic in CRWV at a
    +28.765bp mean gap.
  - The six-name CARRY basket's true-print auction cost is a median of +5.845bp per session
    (mean +3.701bp), against Wave 4's bar-based -0.626bp on 29 names. On the same six names
    with Wave 4's prints the figure is -1.024bp, so the shift is print definition, not name
    set. Per-name true-print medians, with the mid-reference caveat on their face:
    SNDK +0.335, CRWV +30.140, RKLB -0.799, NVDA -3.683, AMD -2.159, MU -6.684bp.
  - Reading: the registered 5bp cost is about right for the CARRY basket in true prints,
    not conservative. The auction-only conclusion stands.

### 1.3 The registered falsifier the sleeve answers to

Registered in Wave 3, wired in Wave 4, hardened by the Wave 6 amendment:

- Instrument: keepgoing2/wave4/v1_shadow_accrual.py, ledger
  keepgoing2/wave4/on_focus29_shadow.jsonl beside it.
- Cron: on-focus29-shadow-accrual, weekdays 09:46 ET. Session 1 (Fri 2026-11-13 close to
  Mon 2026-11-16 open) records Mon 2026-11-16.
- Rule: 60 forward sessions from Mon 2026-11-16. Demotion if the mean overnight return of
  the equal-weight Focus 29 basket, net of 5bp per session, is not positive at session 60.
- The sleeve does not replace, re-grade, or edit this instrument. The sleeve is the paper
  implementation whose realized fills are graded BESIDE it (section 9). The family verdict
  at accrual session 60 governs the sleeve's continued existence (section 12).

## 2. Definitions mirrored from the production shadow accrual

The sleeve and its grading use the accrual's definitions exactly. Every item below was read
from keepgoing2/wave4/v1_shadow_accrual.py as amended by Wave 6 (2026-11-15).

- Basket: the module constant FOCUS, 29 names (section 3). The Focus 30 minus SIVE, because
  SIP serves no bars for SIVE.
- Anchor: ANCHOR = "2026-11-13", the last historical session. Forward legs are strictly
  after it.
- Leg: for one name and one session date D, leg return = open(D) / close(previous session)
  minus 1, from SIP split-adjusted daily bars. Gross for a session is the equal-weight mean
  of the name legs present, in bp: gross_bp = mean(legs) * 1e4.
- Registered cost: REGISTERED_COST_BP = 5.0. net5_bp = gross_bp - 5.0.
- Minimum names: MIN_NAMES = 10. A session with legs for fewer than 10 names is not a
  graded session.
- Skipped sessions (Wave 6, D4): a session with legs but fewer than MIN_NAMES names writes
  a marker row {"date", "skipped": true, "reason": "insufficient_names", "names_present"}
  instead of a graded row. Session counting and the verdict count only non-skipped rows.
- Symbols recorded (Wave 6, D5): every graded row carries "symbols", the sorted list of
  names in that session's basket, beside the "names" count.
- Multi-day legs (Wave 6, D3): a leg whose start bar is not the immediately preceding
  session of the union calendar built from the fetched bars is a multi-day leg. The row
  carries "multiday_names" (sorted) and "multiday_spans" ({name: span in union sessions}).
  Marking only: no leg is excluded and the computation is unchanged.
- Earnings flags (Wave 6, W6-3): every row carries "earnings_names" and "earnings_count",
  from keepgoing2/wave5/w5c_earnings_edgar.json, under the corpus convention that the event
  leg is the first overnight leg whose 09:30 ET open is strictly after the filing's
  acceptance timestamp. Recorded fields only; they change no computation. The corpus loads
  fail-soft.
- Friction legs recorded beside the registered leg: crossing_cost_bp and net_crossing_bp
  (crossing = mean of per-name median quoted round trips, +46.076bp on the Nov 2026
  measurement), auction_cost_bp and net_auction_bp (basket-level only, -0.626bp on the
  same measurement). measured_costs_bp() reads v1_friction.json at runtime through
  .get/None handling (Wave 6, D7), so a missing key yields a shorter list, never a crash.
- Verdict freeze (Wave 6, D6): the verdict is computed on the FIRST 60 non-skipped recorded
  sessions exactly and is frozen once reached. Sessions past 60 still record. The printed
  state reports "verdict_basis_sessions": 60 once frozen, and falsifier_verdict is either
  "SURVIVES: mean net of 5bp positive at 60 sessions" or
  "DEMOTED: mean net of 5bp not positive at 60 sessions". The zero case demotes.
- Idempotence: the accrual is idempotent by date and self-heals a missed morning on the
  next run. The sleeve's grading (section 9) copies this property.

## 3. Basket

focus29, the exact 29 names, in the accrual module's FOCUS order:

SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, COHR, LITE, CRDO,
ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, BE, OKLO, VST, CEG, XLE.

Cross-check performed for this spec: the same 29 names are the keys of
keepgoing2/wave3/focus_bars.json once its two control keys (SPY, QQQ) are removed. SPY and
QQQ are benchmarks and controls only; they are never held by this sleeve. SIVE is not in
the basket, is never ordered, and any intent naming SIVE is a defect (blocker B-06).

CARRY subset, named for monitoring and reporting, not for separate sizing:
SNDK, CRWV, RKLB, NVDA, AMD. MU is marginal. These are the only names whose Wave 4 gross
survives even the crossing stress case:

| Name | Gross/night | Crossing round trip | Net at crossing | Class |
|---|---|---|---|---|
| SNDK | +44.10bp | 15.39bp | +28.71bp | CARRY |
| CRWV | +41.08bp | 22.71bp | +18.37bp | CARRY |
| RKLB | +31.98bp | 21.50bp | +10.48bp | CARRY |
| NVDA | +15.51bp | 7.99bp | +7.52bp | CARRY |
| AMD | +17.79bp | 11.68bp | +6.11bp | CARRY |
| MU | +14.48bp | 11.88bp | +2.59bp | MARGINAL |

The other 23 names are class FRICTION-DEAD at crossing in Wave 4's table. At auction they
are held, because the auction measurement exists only at basket level (section 4.2).

## 4. Sleeve design

### 4.1 Registration

- Sleeve id: on_focus29.
- Module: desk3/sleeves/on_focus29.py, a native sleeve module following the shape of the
  existing native modules in that package (module-level INPUTS tuple, SLEEVE_ID constant,
  evaluate(view, ctx) returning intent dicts, ctx.log(...) for sleeve journal events, as in
  desk3/sleeves/gate_1h.py and desk3/sleeves/leaps_momentum.py).
- INPUTS = ("bars:*:1Min", "bars:*:1Day", "positions", "journal:self"). The bars pattern is
  the producer-registry pattern already in use (for example "bars:*:1Day" and
  "bars:QQQ:1Min" in config/sleeves.json rows).
- Config row in config/sleeves.json:
  {"id": "on_focus29", "module": "desk3.sleeves.on_focus29", "cadence_s": 300,
   "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
   "bp_buffer_frac": 0.02, "flat_by_close": false, "flatten_time_et": null,
   "params": {"basket": [the 29 names of section 3],
              "holidays_et": [the market holiday dates of section 4.3],
              "early_closes_et": {"2026-11-27": "13:00", "2026-12-24": "13:00"}},
   "inputs": ["bars:*:1Min", "bars:*:1Day", "positions", "journal:self"],
   "parked": false}
- Why session "24h" and not "rth": desk3/scheduler.py, function in_session, fires an "rth"
  sleeve only between 09:30 and 16:00 ET on weekdays, and a "24h" sleeve always. This
  sleeve's exit work happens at 19:05 ET and its fallback exit work at 08:30 ET, both
  outside the rth window. Registered as "rth" it would never be evaluated for those steps.
  The sleeve therefore registers "24h" at cadence 300 and gates every action by its own
  clock rules (section 4.3), which are the real control and are blocker-tested (B-02,
  B-09). flat_by_close stays false: the desk's flatten machinery is a crossed-exit path and
  this sleeve must never use it (section 5).

### 4.2 Full basket, not CARRY-only: the decision and its numbers

Decision: the sleeve holds the FULL basket, equal-weight target, every name that is
auction-eligible that night. CARRY-only was considered and refused, for these reasons,
each from the Wave 4 and Wave 5 numbers on file:

1. The falsifier grades the full basket. The accrual's gross is the equal-weight mean over
   the names present (up to 29, minimum 10). A CARRY-only sleeve would express a different
   object from the one under forward test, and its fills could not be graded against the
   accrual row for the same session without a second, unregistered definition.
2. The auction cost was measured at basket level only. Wave 4: basket auction cost -0.6bp,
   net at auction +19.53bp per night for the full basket. The accrual docstring and Wave 4
   both state that per-name auction medians are mid-reference noise on the wide names and
   are never used per name. There is no per-name auction evidence on which to cut 23 names.
3. The CARRY subset's own true-print number is worse, not better. Wave 5: the six-name
   CARRY basket's true-print auction cost is a +5.845bp median, against the 29-name
   bar-based -0.626bp, and CRWV's per-name true-print median is +30.140bp. Cutting to
   CARRY concentrates the sleeve in the one name with the largest measured print gap
   (CRWV, bar open versus opening print +28.765bp systematic).
4. The CARRY set answers a question this sleeve never asks. CARRY means "survives even if
   crossed". The sleeve never crosses (section 5). A name that loses auction access on a
   night is dropped for that night, which is the auction-form equivalent of the CARRY
   filter, applied per night from live facts instead of once from a 10-session table.

Grading still reports the CARRY subset's realized return beside the full basket's every
night (section 9), so the CARRY-only question keeps accruing forward evidence at no risk.

### 4.3 Clock: windows, cutoffs, holidays

All times America/New_York. C is the session's scheduled close: 16:00 on a regular session,
13:00 on an early-close session. The broker's auction submission rules, from Alpaca's order
documentation as read for this spec, are the hard constraints:

- A market order with time_in_force "cls" is a Market-on-Close order, eligible only in the
  closing auction. CLS orders submitted after 15:50 ET on a regular session (after C minus
  10 minutes in general) and before 19:00 ET are REJECTED by the broker. CLS orders
  submitted after 19:00 ET are queued for the FOLLOWING session's closing auction, which
  for this sleeve would be the wrong night's entry and is forbidden.
- A market order with time_in_force "opg" is a Market-on-Open order, eligible only in the
  opening auction. OPG orders submitted after 09:28 ET and before 19:00 ET are REJECTED.
  OPG orders submitted after 19:00 ET are queued for the following session's opening
  auction. That queueing is exactly what the primary exit window uses.

Regular-session timeline (C = 16:00):

| Window (ET) | Action |
|---|---|
| 15:00 to 15:39:59 | Eligibility and sizing preparation only (section 5.1, section 6). No orders. |
| 15:40:00 to 15:49:59 | MOC entry submission window. Every entry intent is submitted inside this window, tif "cls". |
| 15:50:00 | Hard cutoff. No cls submission at or after this time, ever. An entry not submitted by the cutoff is not entered that night. |
| 16:00 to 19:00 | Closing auction prints. Fill adoption from broker read-back at each cadence fire (section 4.5). No submissions of any kind. |
| 19:05 to 19:30 | Primary MOO exit submission window. One opg exit intent per adopted entry fill, for the filled quantity exactly. The broker queues these for the next session's opening auction. |
| 19:30 to next 08:00 | No submissions. Resting opg orders are left alone. |
| Next session 08:00 to 09:27:59 | Fallback MOO window, used only when a position is open, no resting opg order exists for it at the broker, and the primary window was missed. The open-orders check comes first, always (Sleeve Authoring Standard, rule 4). |
| Next session 09:28:00 | Hard cutoff for opg. No opg submission at or after this time. |
| Next session 09:30 to 09:46 | Opening auction prints. No submissions. |
| Next session from 09:46 | Exit fill adoption, flat check (section 4.5), grading inputs complete. |

Early-close sessions (C = 13:00; in the falsifier window: Fri 2026-11-27 and Thu
2026-12-24): the preparation window is C minus 60 minutes to C minus 21 minutes, and the
MOC submission window is [C minus 20 minutes, C minus 10 minutes), that is 12:40:00 to
12:49:59. The primary MOO window stays 19:05 to 19:30 the same evening, and the fallback
window and cutoffs the next session are unchanged. The cls cutoff on an early-close day
tracks the exchange close; the first early-close session after landing (2026-11-27 if the
sleeve is live by then, otherwise the next one) is a named verification item in section 11:
if the broker rejects a cls order submitted inside the shifted window, that is a defect
against this spec's cutoff assumption, journaled and reported, and never answered by
crossing.

Holidays and weekends: no entry, no exit submission, no plan lines. Market holidays in the
falsifier window, carried in the config params as holidays_et: 2026-11-26, 2026-12-25,
2027-01-01, 2027-01-18. (The accrual needs no holiday list: a holiday produces no bars and
therefore no row. The sleeve needs the list because it must not submit an opg order on a
holiday evening for an auction that does not exist the next morning; an opg order for a
position still open before a holiday is submitted on the last session evening before the
holiday or the morning of the next session, under the same windows, with the exit session
date set to the next session.)

Multi-day holds: if an exit misses its opening auction (section 4.5), the position is held
to the next session's opening auction under the same windows. The leg is then a multi-day
leg in fact; grading marks it the way the accrual marks multi-day legs (section 9), and the
sleeve's own stop line C (section 12) counts repeated misses.

### 4.4 Intent shapes

Entry intent, one per held name, submitted in the MOC window:

{"intent_id": "on_focus29-<entry_date>-moc-<SYM>", "kind": "entry", "symbol": "<SYM>",
 "side": "buy", "qty": <whole shares, integer, at least 1>, "order_type": "market",
 "time_in_force": "cls", "position_intent": "buy_to_open",
 "price_hint": <reference price from section 6.2>,
 "auction_deadline_et": "<entry_date>T15:50:00<ET offset for that date>",
 "reason": "on_focus29 auction entry session <entry_date> leg <SYM>"}

Exit intent, one per adopted entry fill, submitted in the primary or fallback MOO window:

{"intent_id": "on_focus29-<entry_date>-moo-<SYM>", "kind": "exit", "symbol": "<SYM>",
 "side": "sell", "qty": <filled quantity adopted, exactly>, "order_type": "market",
 "time_in_force": "opg", "position_intent": "sell_to_close",
 "price_hint": <adopted entry fill price>,
 "auction_deadline_et": "<exit_date>T09:28:00<ET offset for that date>",
 "reason": "on_focus29 auction exit entry <entry_date> leg <SYM>"}

Rules on the shapes:

- order_type is "market" in both. At Alpaca the auction form is carried by time_in_force
  ("cls" for close, "opg" for open) on a market order; there is no separate MOC or MOO
  order type on the wire. Section 7 names the desk changes this requires.
- qty is always a whole number of shares (section 6.3). No fractional quantity, no notional
  field, no limit_price, no stop_price, on any intent this sleeve emits.
- auction_deadline_et is a new intent field this sleeve introduces. The dispatcher ignores
  unknown intent fields today (validate_intent checks named fields only); build item zero
  (section 7) teaches the pending drain to honor it. No other sleeve's intents carry it,
  and no other sleeve's behavior changes.
- intent_id uniqueness follows the desk convention: client_order_id is built by
  desk3/models.py client_order_id(sleeve_id, intent_id) with its 127-char cap, unchanged.

### 4.5 Fill adoption and state

Adoption follows SLEEVE-AUTHORING-STANDARD.md (landed 2026-11-03) exactly:

- Only a broker read-back status of "filled" promotes a leg to fully filled, at the full
  filled quantity. The read-back of record is PaperDoor.get_order_by_client_id, the same
  interface the dispatcher's fill sweep uses.
- Terminal status with a partial fill (filled, canceled, expired, rejected, closed):
  adopt exactly the filled portion as the position; the unfilled remainder is closed,
  never booked, never left pending. An exit is then owed for the filled portion only.
- Working partial fill: book the filled portion, keep the remainder pending under the same
  intent identity.
- Uncertain submit (exception, unknown outcome): keep the pending entry, check the
  broker's open orders (PaperDoor.get_open_orders) before any retry or clear, never
  resubmit blind.
- Any status outside the handled set is logged by name as an open defect against the
  sleeve, never defaulted to filled or to nothing.

Working state: state/on_focus29/state.json under the desk root, rewritten atomically
(write to a temp file, then os.replace, the pattern desk3/scheduler.py uses for its own
state). Contents: open legs keyed by symbol, each {entry_date, qty_planned, qty_filled,
entry_client_order_id, entry_fill_price, exit_client_order_id, exit_state}, plus the
ineligibility latch set (section 5.1) and the sleeve's own session counter. The sleeve
journal is the audit record; the broker's positions read-back is the truth on any conflict
between state and book, and a conflict is journaled, never silently resolved.

Flat check: at the first cadence fire at or after 09:46 ET on the exit session, the sleeve
reads broker positions for its symbols. Expected flat. Any residual quantity is an exit
miss (section 5.2) and is re-queued for the next opening auction under section 4.3.

## 5. The never-crossed rule

### 5.1 The rule

A name that loses auction access on a night is dropped for that night. It is never crossed
into a spread, never replaced by a market order with tif "day", never replaced by a limit
order, and never chased the next morning. There is no code path in this sleeve that emits
an intent with order_type other than "market", or time_in_force other than "cls" (entry)
or "opg" (exit). Losing a name shrinks the basket for that night; it never changes the
execution form. This rule has no override flag, no params switch, and no manual exception
inside the sleeve. Turning the sleeve off is done by parking it in config, not by giving
it a crossed mode.

A name is auction-ineligible for a night when any of these observed facts holds at the
preparation window, or arises at submission:

1. No usable reference price: the name's latest 1Min bar in the snapshot is missing, or its
   timestamp is more than 15 minutes old at sizing time, or its close is not positive.
   Reason string: "no_price".
2. The symbol is in the sleeve's ineligibility latch: a prior auction order for the symbol
   drew a terminal broker verdict of the asset class (asset not found, asset not tradable,
   order not eligible for the auction), journaled at the time. The latch clears only by a
   desk-lane edit to the state file with a dated note, never by the sleeve itself.
   Reason string: "auction_ineligible_latched".
3. The broker terminally rejects this night's cls submission for the symbol (HTTP 422
   class, or a rejected order status on read-back). The name is dropped for the night and
   latched under rule 2. Reason string: "submit_rejected_terminal".
4. The name is halted in fact: the snapshot shows no trades and no quote movement for the
   name across the full preparation window while the session is otherwise live, or the
   broker rejects with a halt reason. Reason string: "halted_no_prints". (The desk has no
   dedicated halt feed; this rule is deliberately narrow, and a name that merely looks
   quiet keeps its order. The auction itself is the final arbiter: an order the auction
   does not fill is handled by section 5.2, not by prediction.)
5. The budget cannot cover one share of every eligible name (section 6.2, edge case):
   names are dropped in descending reference-price order until one share each fits.
   Reason string: "budget_cannot_cover_one_share_each".

Eligibility floor: if fewer than 10 names remain eligible (the accrual's MIN_NAMES), the
sleeve enters nothing that night. It writes the plan line with the drop list and stands
down. A night with no entry is a skipped night for the sleeve, mirroring the accrual's
skipped-session marker.

### 5.2 Drop mechanics and the journal lines

Entry side, per dropped name, written to the sleeve's own journal via ctx.log at the
moment of the drop, one line per name:

{"event": "on_name_dropped", "session": "<entry_date>", "symbol": "<SYM>",
 "stage": "entry", "reason": "<reason string from 5.1>", "detail": "<observed fact>"}

The night's plan line, written once when the entry plan is fixed (preparation window):

{"event": "on_entry_plan", "session": "<entry_date>", "names_planned": <n>,
 "symbols": [<sorted planned symbols>], "invested_usd": <planned cost>,
 "budget_usd": 9800.0, "dropped": [{"symbol": "<SYM>", "reason": "<reason>"}],
 "carry_present": [<the CARRY names among the planned symbols>]}

Exit side. An exit can miss in three ways, each with its own line and its own next step:

- MOO order terminal with zero fill (canceled, expired, rejected after the opening
  auction): the position stays open.
  {"event": "on_exit_missed", "session": "<exit_date>", "symbol": "<SYM>",
   "stage": "exit", "reason": "moo_unfilled", "qty_open": <qty>}
  Next step: re-queue one opg exit for the next session under section 4.3 windows. Never
  a day market order, never a limit order.
- MOO partial fill on a terminal status: adopt the filled part as exited; the remainder
  stays open.
  {"event": "on_exit_missed", "session": "<exit_date>", "symbol": "<SYM>",
   "stage": "exit", "reason": "moo_partial", "qty_open": <remaining qty>}
  Next step: as above, for the remaining quantity only.
- Exit submission window missed entirely (runner down, door down past the fallback
  cutoff): no order exists.
  {"event": "on_exit_missed", "session": "<exit_date>", "symbol": "<SYM>",
   "stage": "exit", "reason": "moo_window_missed", "qty_open": <qty>}
  Next step: as above. The miss counts toward stop line C (section 12) regardless of
  cause; cause is carried in the grading row, not used as an excuse.

Dispatcher-side journal evidence: every submission, rejection, and fill for this sleeve
also lands in the dispatcher journal through the existing dispatcher paths (intent_rejected
rows from Dispatcher._reject, fill rows from the fill sweep), under sleeve id on_focus29.
Grading (section 9) joins on those rows; the sleeve journal alone is never the only record.

## 6. Sizing

### 6.1 Rails inherited, none invented

The sleeve inherits the desk's existing rails. It creates no new risk rail, no new limit
system, and no new approval path.

- Slice: one desk slice of $10,000, the desk's standing per-sleeve convention
  (config/sleeves.json rows carry slice {"capital_usd": 10000.0, "cash_usd": 10000.0} for
  the native sleeves, for example the desk3.sleeves.free_* and desk3.sleeves.fwd_* rows).
  The dispatcher's per-sleeve virtual slice enforces it: Dispatcher.process_intent computes
  entry cost as price times qty times the cash multiplier, and rejects with
  "insufficient_slice_bp" when cost exceeds slice cash minus reservations.
- Buying-power buffer: bp_buffer_frac 0.02, the value on the desk's sleeve rows. The
  dispatcher reserves cost times (1 + bp_buffer_frac) per entry. The sleeve plans against
  an investable budget B = $9,800.00 so that planned cost times 1.02 stays inside the
  $10,000 slice: 9800 * 1.02 = 9996.00, which is inside 10000.00.
- Reconcile halt: a sleeve under reconcile halt is refused new entries by the dispatcher
  ("reconcile_halt") while exits always pass. The sleeve inherits this unchanged; an entry
  night lost to a halt is a skipped night, journaled from the dispatcher's reject rows.
- Paper only: PaperDoor enforces the paper base URL at construction and refuses live
  credentials at startup (desk3/broker.py, desk3/security.py assert_paper_only and
  assert_paper_url). The sleeve runs only through that door.
- Fill adoption: SLEEVE-AUTHORING-STANDARD.md, section 4.5 above.
- Charter Amendment 16 stress fractions: searched for in the desk tree for this spec and
  NOT found there. No file under desk3/ and no desk markdown read for this spec states a
  Charter Amendment 16 stress fraction. This sleeve is long-only listed equity with no
  options, no shorting, and no leverage, so no stress-fraction sizing is applied to it. If
  the desk lane holds the amendment text outside the desk tree, the lane checks this
  sleeve against it at landing and records the check in the BUGLOG entry; the sleeve's
  sizing does not change unless that check produces a smaller budget, in which case the
  smaller budget replaces B in section 6.2 and nowhere else.

### 6.2 The sizing algorithm (deterministic, buildable as written)

Inputs at the preparation window: the eligible name set E (section 5.1), and for each name
a reference price P, defined as the close of the name's latest 1Min bar in the snapshot at
sizing time, the same price written into the intent's price_hint, so the sleeve's plan and
the dispatcher's buying-power gate price the leg identically. Fallback when no 1Min bar
exists but a prior-session 1Day close does: the name is still dropped under rule 5.1.1
(no_price), because a day-old price cannot size an auction leg honestly. There is no
second fallback.

Target: equal weight. Target dollars per name T = B / |E|, with B = 9800.00.

Algorithm:

1. If the sum over E of P (one share each) is greater than B: drop names in descending P
   order (ties broken by symbol, ascending) under reason
   "budget_cannot_cover_one_share_each" until one share each fits. Recompute E and T.
   If |E| falls below 10, stand down under section 5.1's floor.
2. Start with qty = 1 share for every name in E. Spent = sum of P over E.
3. Repeat: among names whose current dollar weight qty * P is below T, pick the name with
   the largest dollar deficit T minus qty * P (ties broken by symbol, ascending). If
   Spent + P for that name is at most B, add one share to it and update Spent. If it does
   not fit, remove that name from this round's candidates and continue with the next
   largest deficit. Stop when no candidate can add a share within B.
4. The result is the plan: integer quantities, every eligible name at least 1 share, total
   planned cost at most B. Unspent cash (B minus Spent) stays in the slice as cash. It is
   never redistributed after the plan is fixed, and never spent on a crossed order.

Worked scale, from the 2026-11-13 closes in keepgoing2/wave3/focus_bars.json, for the
build lane's intuition only (not a rule): one share of each of the 29 names costs about
$7,012 in total, so step 1 does not bind at recent prices; the most expensive single leg,
SNDK at $885.01, is about 2.6 times the naive per-name target of $337.93 and stays at
1 share under the algorithm, while cheap names are topped up toward the target. The
resulting weight dispersion is a measured output, reported every night by grading
(section 9: invested fraction and max/min leg dollars), never hidden.

Exits do not size: exit qty is the adopted filled qty, exactly, per name.

### 6.3 Whole shares only: the fractional conflict, decided

The desk's fractional sizing cure (WS4, landed 2026-11-14) is real and is read in
desk3/models.py validate_intent: fractional quantities are lawful for equities, the budget
decides, there is no forced one-share floor, with two named exceptions (options contracts
are whole by instrument, and a fractional quantity cannot ride a limit order, because the
fractional door is market-only). That cure governs day market orders. It does not reach
this sleeve, for a broker fact: at Alpaca, fractional quantities are supported only on
orders with time_in_force "day" (the fractional trading documentation states fractional
support for market, limit, stop and stop-limit orders by setting time_in_force to day, and
the order documentation states a fractional qty is available for only market and day order
types). A fractional quantity with tif "cls" or "opg" is not a supported order shape and
would be rejected at the broker. The auction form therefore requires whole shares, and
section 6.2's one-share floor is not the killed forced floor revived: it is the smallest
unit the auction door accepts, applied only inside this sleeve, with the equal-weight
target approximated openly and its dispersion graded nightly. Build item zero adds the
matching fail-closed guard to validate_intent (section 7, item B0-2), so a fractional
auction intent from any future sleeve is refused by name at the desk, not at the broker.

## 7. Build item zero: MOC and MOO do not exist in the door today

Finding, from reading the desk tree for this spec: MOC and MOO are ABSENT from the desk.
Not partially present, not behind a flag. The evidence, file and symbol:

- desk3/models.py, validate_intent: order_type must be in ("market", "limit"), else
  IntentError "bad_order_type". time_in_force must be in ("day", "gtc"), else
  IntentError "bad_tif". The auction encodings "cls" and "opg" both fail here today.
  Every auction intent this sleeve emits would be rejected by Dispatcher.process_intent
  through Dispatcher._reject before any other gate.
- desk3/broker_dialect.py, broker_time_in_force(sym, tif): passes every tif through
  untouched except crypto "day", which becomes "gtc". It neither blocks nor translates
  "cls" or "opg" today; after B0-1 it must still pass them through for equities, which its
  current shape already does, so this file needs a blocker assertion, not a change.
- desk3/dispatcher.py, _preflight_violation: checks symbol shape, market-with-limit-price,
  crypto tif (must be "gtc" or "ioc"), and position_intent validity. It has no auction
  case today. The dispatcher's submit path (Dispatcher.process_intent, the submit loop)
  passes intent order_type and time_in_force generically to broker.submit_order, so no
  dispatcher submit change is needed for the wire itself.
- desk3/broker.py, PaperDoor.submit_order: builds the wire body as
  {"symbol", "side", "qty", "type": order_type, "time_in_force": time_in_force,
  "client_order_id", plus limit_price, position_intent and stop_price when set}. It
  forwards any order_type and tif string it is given. The door's wire path therefore
  needs NO change: once validation admits "cls" and "opg", the existing body carries them
  to the broker unchanged. Its one auction-relevant guard, the options market-hours
  refusal, is scoped to OCC symbols with market type and does not touch equities.
- desk3/broker.py, FakeBroker.submit_order: the test double's stored order dict carries
  symbol, side, qty, status, position_intent and stop_price, but NOT order_type and NOT
  time_in_force. Until it records them, no blocker can assert the auction shape from a
  read-back, and grading fixtures cannot prove what was submitted. This is part of build
  item zero, not a detail.

Build item zero is therefore a validation and test-double change, not a new door. Its
parts, in order, all inside the desk lane's cure window:

- B0-1. desk3/models.py validate_intent: admit time_in_force "cls" and "opg" for equity
  intents only. Conditions, all fail-closed with named IntentErrors: the symbol must not
  match OCC_RE (options keep ("day", "gtc") exactly as today); the symbol must not be a
  crypto pair (is_crypto_symbol in desk3/broker_dialect.py, or "/" in the symbol);
  order_type must be "market" (a limit-on-close or limit-on-open shape is not part of
  this spec and stays refused). New refusal names: "auction_tif_on_options",
  "auction_tif_on_crypto", "auction_tif_requires_market".
- B0-2. desk3/models.py validate_intent: extend the existing fractional guard. Today a
  fractional qty on a limit order raises "fractional_qty_limit_order". Add: a fractional
  qty with tif "cls" or "opg" raises "fractional_qty_auction_order" (section 6.3).
- B0-3. desk3/dispatcher.py _preflight_violation: add the mirror preflight case, so a
  cls/opg intent on an OCC or crypto symbol that somehow reaches the dispatcher is refused
  locally with "preflight_auction_tif_on_non_equity" and never reaches the wire. Defense
  in depth, matching the desk's existing door-preflight pattern.
- B0-4. desk3/dispatcher.py pending drain: an intent carrying auction_deadline_et whose
  deadline has passed at drain time is never submitted. The drain writes
  {"event": "auction_intent_expired", "intent_id", "sleeve", "symbol",
   "time_in_force", "auction_deadline_et"} to the dispatcher journal and closes the
  pending entry. This matters because the generic drain exists to retry intents across
  cycles (PendingStore in desk3/dispatcher.py), and a retried cls intent after 15:50
  would be broker-rejected, while one drained after 19:00 would queue for the wrong
  session's close. Intents without auction_deadline_et drain exactly as today.
- B0-5. desk3/broker.py FakeBroker.submit_order: record "type" (the order_type argument)
  and "time_in_force" in the stored order dict, and return them on read-back, in parity
  with the PaperDoor wire body. No PaperDoor change.
- B0-6. No change, asserted by blocker: broker_dialect.broker_time_in_force returns "cls"
  and "opg" unchanged for equity symbols, and Dispatcher.process_intent's tif rewrite for
  the wire (which calls broker_time_in_force) therefore carries them through.

## 8. Remaining build items

- B1. desk3/sleeves/on_focus29.py: the sleeve itself, per sections 4, 5 and 6. Pure clock
  and eligibility decisions are factored into module-level functions that take an explicit
  now argument, so blockers can drive them with fixture clocks without the runner.
- B2. Grading script and cron (section 9): keepgoing2/wave4/on_paper_grading.py, beside the
  accrual it grades against, writing keepgoing2/wave4/on_focus29_paper_grade.jsonl. Cron
  on-focus29-paper-grading, weekdays 10:15 ET, armed by the desk lane at landing and read
  back from the scheduler, the same arming standard the accrual crons were held to.
- B3. The config row of section 4.1 in config/sleeves.json, added in the same landing
  commit as B1, never before the blockers pass.
- B4. BUGLOG entry (section 11) and the regression gate run at the live path.
- Explicit non-items: no change to v1_shadow_accrual.py or its ledger; no change to any
  other sleeve; no change to PaperDoor; no new producer; no Tensor file; no saty file.

## 9. Grading wire

### 9.1 What is compared, every session

The grading script runs after the accrual's 09:46 ET run, at 10:15 ET on weekdays. It is
read-only on the desk: it reads the dispatcher journal generations (through
desk3/journal.py journal_generations and read_lines, the reader contract every journal
consumer uses), the sleeve's own journal, the accrual ledger
keepgoing2/wave4/on_focus29_shadow.jsonl, and the print companion file (section 9.2). It
writes one grade row per sleeve session to
keepgoing2/wave4/on_focus29_paper_grade.jsonl, idempotent by entry date: a rerun replaces
nothing and appends nothing for a date already graded, matching the accrual's idempotence.

Per sleeve session (entry date D, exit date D+1 session), the grade row carries:

- sleeve_gross_bp: the sleeve's realized overnight return in bp on invested capital:
  sum over filled legs of (exit_fill_price / entry_fill_price minus 1) times the leg's
  entry-dollar weight (entry qty times entry fill price, over total entry dollars),
  times 1e4. Fill prices are the broker read-back filled_avg_price values as journaled in
  fill rows, never bar prices.
- sleeve_net5_bp: sleeve_gross_bp minus 5.0, the registered cost, so the sleeve row and
  the accrual row carry the same net leg.
- accrual_gross_bp and accrual_net5_bp: copied from the accrual ledger row whose date is
  the exit date (the accrual dates a leg by its open date), for the same legs' session.
  If that row is a skipped marker or is absent, the grade row says so in
  "accrual_row": "skipped" or "absent" and the divergence fields are null. A missing
  accrual row is named, never filled in from bars by the grading script.
- divergence_bar_bp: sleeve_gross_bp minus accrual_gross_bp. Expected sources, in order:
  whole-share weight dispersion (section 6.2), the bar-open versus opening-print gap
  (Wave 5: pooled +5.436bp, CRWV +28.765bp), and dropped names. The row carries
  "names_filled", "names_in_accrual_row" (from the accrual row's "symbols"), and
  "weight_max_min_ratio" (largest leg dollars over smallest leg dollars in the sleeve's
  fills) so the sources can be told apart over time.
- carry_gross_bp: sleeve_gross_bp recomputed over the CARRY names only (section 3), same
  formula, beside the full-basket figure. Monitoring only.
- invested_fraction: total entry dollars over B (9800.0).
- multiday_names: legs whose exit date is not the next session after entry, marked the
  accrual's way (section 2), from the sleeve's own dates.
- earnings_names: copied from the accrual row for the exit date, so an event night is
  visible in the sleeve's grade without the sleeve reimplementing the corpus convention.
- order_shape_violations: a count, from the dispatcher journal, of this sleeve's submitted
  orders in the session whose type is not "market" or whose tif is not the window's
  expected value ("cls" for entries, "opg" for exits). Expected value: zero, always.
  Any nonzero count is stop line D (section 12), surfaced in the row, not buried.

### 9.2 The print companion (Wave 7 cell W6A-PRINT-COMPANION)

Wave 6 decided, on the record, that no auction-print gross leg is added inside the
accruals. Print truth is pursued by a separate offline capture: the companion auction-print
capture, filed beside the ledgers, never inside the accruals. This spec consumes that
companion; it does not build the capture (that is Wave 7 cell 2's work) and it does not
put prints into the accrual.

- Companion location and shape, as consumed here:
  keepgoing2/wave4/on_focus29_print_companion.jsonl, one row per session:
  {"date": "<open date>", "prints": {"<SYM>": {"close_print": <price>,
  "open_print": <price>}}}, prints identified from SIP trade condition codes, the route
  Wave 5 Lane A validated on the six CARRY names. If Wave 7 lands the companion under a
  different filename, the grading script's path constant is the only thing that changes.
- Fail-soft, copied from the accrual's earnings-corpus rule: a missing or unreadable
  companion file yields grade rows with the companion fields null and
  "companion": "missing" in the row, never a crash and never a blocked grade.
- companion_gross_bp: the equal-weight mean over names present in both the sleeve's fills
  and the companion row of (open_print / close_print minus 1), times 1e4. This is the
  true-print gross for the names the sleeve actually held.
- print_gap_bp: companion_gross_bp minus the accrual's gross recomputed over the same
  name subset. (The accrual row carries only the full-basket gross, so the grading script
  recomputes the subset gross from the same SIP daily bars route the accrual uses, and
  labels it "accrual_subset_gross_bp" in the row. The registered accrual row itself is
  never altered.) This field isolates the bar-versus-print measurement gap from the
  sleeve's own execution.
- realized_auction_cost_bp: companion_gross_bp minus sleeve_gross_bp recomputed
  equal-weight over the same subset (the row carries it as "sleeve_subset_gross_bp").
  This is the sleeve's realized auction cost against true prints, the number stop line A
  (section 12) reads. Wave 5's expectation for it, on the CARRY names, is a median near
  +5.845bp.
- fill_vs_print_bp: per name, entry leg (entry_fill_price / close_print minus 1) * 1e4
  and exit leg (open_print / exit_fill_price minus 1) * 1e4; the row carries the median
  absolute value across names for each leg. A sleeve truly filled at the auction prints
  reads zero on both, up to print-capture precision.

### 9.3 The threshold that reopens the friction question

The friction question ("does the auction form really cost about the registered 5bp?") is
reopened, as a named event and not a vibe, when any of these prints in the grade rows:

- FRICTION-REOPEN-1: the rolling 20-graded-session mean of realized_auction_cost_bp
  exceeds 10.0bp. (Twice the registered cost, sustained, means the 5bp premise is wrong
  in fact, whatever any single night did.)
- FRICTION-REOPEN-2: the rolling 20-graded-session mean of print_gap_bp exceeds 10.0bp in
  absolute value. (The bar-based falsifier and print truth have come apart by more than
  the Wave 5 pooled measurement of +5.436bp, doubled.)
- FRICTION-REOPEN-3: fill_vs_print_bp median absolute value exceeds 2.0bp on either leg
  in 5 consecutive graded sessions. (The sleeve is not actually receiving auction prints,
  which is an execution defect, not a market fact.)

A reopening writes "friction_reopened": "<which line>" into the grade row, is named at
the top of the desk lane's next report, and goes to the Triad with the grade rows behind
it. It does not by itself stop the sleeve; stop line A (section 12) is the stop. It is
never graded away by averaging over a longer window than the one stated.

## 10. Blocker tests

One file: tests/test_on_focus29_auction_20261115_blockers.py, discovered by the gate's
existing pattern (test_*_blockers.py under tests/). Written before the build items land,
run against the unbuilt seam first, and kept as the regression blocker afterwards. The
desk's standard applies: the test must fail on the old code and pass on the built code,
with the fail direction proven at least once (the W6-6 pattern: run on an unpatched copy,
record the failure counts, then run built).

- B-01, auction tif admitted for equity market intents.
  Claim: validate_intent accepts {"order_type": "market", "time_in_force": "cls"} and
  the same with "opg" for a plain equity symbol with whole qty.
  Fail-first: today both raise IntentError "bad_tif".
- B-02, no MOC submission outside the submission window.
  Claim: driving the sleeve's entry decision with fixture clocks emits zero entry intents
  at 15:39:59 ET, zero at 15:50:00 ET, zero at 19:05 ET, and the full plan inside
  15:40:00 to 15:49:59 ET, on a regular session fixture. On an early-close fixture the
  window is 12:40:00 to 12:49:59 ET and 15:40 ET emits nothing.
  Note on the claim's shape: Wave 4's report says orders "rest as MOC from 15:50 ET". Read
  against the broker's rule (section 4.3), 15:50 is the cutoff a cls submission must beat,
  not a time to submit at: a cls order submitted at or after 15:50 on a regular session is
  rejected, and one submitted after 19:00 queues for the wrong session. The binding,
  testable claim is therefore the window claim above. The orders do rest from submission
  until the closing auction prints at 16:00, which is what the Wave 4 sentence describes
  in substance.
- B-03, dropped name produces no order and a journal line.
  Claim: with a fixture snapshot in which one basket name has no current bar, evaluate in
  the MOC window emits no intent for that name, and the sleeve journal gains exactly one
  on_name_dropped line for it with reason "no_price", plus the on_entry_plan line listing
  it under "dropped".
- B-04, MOO exit for every MOC fill, at the filled quantity.
  Claim: for every adopted entry fill in a fixture (including a partial fill and a
  terminal-with-partial fill), exactly one opg exit intent exists by the end of the
  primary window, its qty equals the filled qty and nothing else, and a name with zero
  fill has no exit intent.
- B-05, sizing never exceeds the slice budget and never goes fractional.
  Claim: over fixture price sets (including the 2026-11-13 closes and an adversarial set
  with one name at $2,500), planned cost is at most 9800.00, planned cost times 1.02 is at
  most 10000.00, every planned qty is an integer of at least 1 for eligible names, and the
  dispatcher's slice gate accepts the plan's total reservation. In the adversarial set the
  budget edge rule of section 6.2 step 1 fires and is journaled.
- B-06, auction-ineligible and off-basket symbols fail closed.
  Claim: a latched symbol emits no intent and gains an on_name_dropped line with reason
  "auction_ineligible_latched"; SIVE emits no intent under any fixture; validate_intent
  raises "fractional_qty_auction_order" for a fractional qty with tif "cls",
  "auction_tif_on_options" for tif "opg" on an OCC symbol, and
  "auction_tif_requires_market" for tif "cls" with order_type "limit".
- B-07, the sleeve never submits any other order shape.
  Claim: across fixture clocks covering every window in section 4.3 (preparation, MOC,
  adoption, primary MOO, fallback MOO, midday, weekend, holiday), every intent the sleeve
  emits has order_type "market" and time_in_force in ("cls", "opg"), entries only "cls",
  exits only "opg", and no intent carries limit_price or a fractional qty.
- B-08, the pending drain never submits an expired auction intent.
  Claim: a PendingStore fixture holding a cls intent whose auction_deadline_et has passed
  drains to one auction_intent_expired dispatcher journal line, the broker double's
  submit_count does not move, and a control intent without auction_deadline_et drains
  exactly as today.
- B-09, MOO is never submitted inside the broker's forbidden band.
  Claim: with an open position and no resting opg order, evaluate emits zero opg intents
  at 09:29 ET and at 12:00 ET; emits the exit in the 19:05 to 19:30 primary window; and
  emits it in the 08:00 to 09:27:59 fallback window only when the primary window was
  missed and get_open_orders shows no resting opg order for the symbol.
- B-10, the test double records the auction shape.
  Claim: FakeBroker.submit_order with order_type "market" and time_in_force "cls" returns
  a read-back carrying "type": "market" and "time_in_force": "cls", and the same for
  "opg". Fail-first: today the stored order dict has neither key.
- B-11, grading joins accrual and companion, fail-soft.
  Claim: the grading script, on fixture journals plus a fixture accrual row plus a
  fixture companion row, writes exactly one grade row carrying sleeve_gross_bp,
  accrual_gross_bp, divergence_bar_bp, companion_gross_bp, print_gap_bp and
  realized_auction_cost_bp; with the companion file absent it still writes the row, with
  companion fields null and "companion": "missing"; a rerun appends nothing.

## 11. Gate path and landing window

Landing window: the desk lane's next cure window. Tonight (Sun 2026-11-15) this spec is
the only artifact; the live tree is not touched. Monday 2026-11-16 staging is frozen: no
part of this build is staged, patched onto a copy inside the live tree, or half-landed on
Monday. The shadow accrual's session 1 records Monday regardless; the sleeve's own first
session is the first regular session after its landing completes, and the sleeve's session
counter starts there. The family falsifier's 60 sessions run on the accrual's clock, not
the sleeve's.

The path, in order, no step skippable:

1. Fail-first. Write tests/test_on_focus29_auction_20261115_blockers.py (section 10). Run
   it against the unbuilt tree (a full copy of the desk tree, the W6-6 pattern, so the
   live tree stays untouched until landing). Record the failure counts in the landing
   BUGLOG entry: B-01, B-06 (validation parts) and B-10 must fail on the unbuilt seam, and
   the sleeve tests must fail on the absent module. A blocker that passes unbuilt is not
   a blocker; rewrite it before proceeding.
2. Build. Land B0-1 to B0-6, then B1, then B3 (config row last among code items). Minimum
   sufficient change: no file outside section 7 and section 8's list is edited.
3. Blockers pass. The blocker file passes in full on the built tree.
4. Full gate green at the live path. desk/run_regression_blockers.sh runs the whole
   blocker suite (its discovery is tests/test_*_blockers.py) and exits 0. The gate's own
   receipt (state/gate_receipts/, written on every run, pass or fail) is the evidence;
   a gate run on a copy does not substitute, per the W6-6 bounded partial, where the full
   clean gate at the live path was the owed item.
5. BUGLOG entry. In muse-desk-v3/BUGLOG_<landing date>.md (the dated bug log series at
   the repo root; the tasking's "desk/BUGLOG" path is that series), with: severity,
   files, what was missing (MOC and MOO inexpressible in the door path, section 7), the
   fix, the blocker file name, and its fail-first and pass counts. This build is a missing
   capability cured at the source, logged the same way the desk logs a defect.
6. Grading wire armed. B2's script lands beside the accrual; cron
   on-focus29-paper-grading is armed for weekdays 10:15 ET and read back from the
   scheduler before the sleeve's first session.
7. Runner restart under the watchdog. Restart through the desk's standing route
   (OPERATIONS.md: the watchdog runs as the boot-enabled systemd unit
   muse-desk-v3-watchdog.service, canonical copy in desk3/systemd/; the runner it
   supervises adopts the new config). Verify from state, not from the restart command:
   state/watchdog.json shows the runner alive on the new launch record, and the cycle feed
   names on_focus29 as FED with its inputs served, not UNFED.
8. First-session live proof. The sleeve's first session is proven only when ALL of these
   are read from the final state after that session completes:
   a. An on_entry_plan line in the sleeve journal, written inside the preparation window,
      with names_planned at least 10 and every drop carrying a reason.
   b. Dispatcher journal: every submitted order for sleeve on_focus29 in the session has
      type "market"; entries carry tif "cls" and were submitted inside the MOC window;
      zero orders of any other shape (the grade row's order_shape_violations is 0).
   c. Fill adoption matches the broker read-back share for share: adopted filled
      quantities equal PaperDoor.get_order_by_client_id filled quantities for every leg,
      partials handled per section 4.5.
   d. One opg exit intent per filled leg, submitted inside the primary window (or the
      fallback window, with the miss journaled).
   e. Flat check at or after 09:46 ET on the exit session: broker positions for the
      sleeve's symbols are zero, or every residual is journaled as on_exit_missed with a
      re-queued opg order resting.
   f. The grade row for the session exists in on_focus29_paper_grade.jsonl by 10:15 ET,
      joined to the accrual row for the exit date.
   g. No reconcile halt names on_focus29 for the session, and the slice's cash after exit
      equals its pre-entry cash plus realized P&L and fees within the reconcile tolerance
      the desk already uses.
   Until all seven read true, the sleeve's status is UNVERIFIED, and it is reported as
   UNVERIFIED, not as live. One proven session makes it live; it does not make it good.
   Good is section 12's business, over 60 sessions.

## 12. Falsifier and kill lines

### 12.1 The family falsifier governs

At accrual session 60, the verdict frozen on the first 60 non-skipped sessions decides:
mean net5_bp positive, the family SURVIVES; not positive, DEMOTED. On DEMOTED, whenever in
the sleeve's life that lands: the sleeve enters nothing from the next session on, exits
any open leg at the next opening auction under the usual windows, and once flat is parked
in config with the demotion named in its BUGLOG line. The sleeve does not argue with the
verdict, does not average past it, and does not re-register under a new name to escape it.
Before session 60 the sleeve takes no position on the family verdict either way; its
running grade rows are evidence, not a verdict.

### 12.2 The sleeve's own stop lines

Each line names its number, its window, and its action. "Halt entries" means: no new MOC
orders from the next session on, exits continue normally, the halt and its evidence are
reported at the top of the desk lane's next report and to the Triad, and entries resume
only when the line's cure is landed and proven, or the owner rules otherwise. A halted
sleeve is an open defect, not a resting state.

- Stop A, realized auction cost. Rolling 20 graded sessions: mean
  realized_auction_cost_bp (section 9.2) greater than 15.0bp. Halt entries.
  Basis: the registered cost is 5bp; Wave 5 measured the CARRY basket's true-print median
  at +5.845bp; the find's own history says the effect is alive at 5bp of friction and dead
  at 15bp. A sustained realized cost above 15bp means the paper implementation is paying
  the dead level, whatever the bar-based accrual says.
- Stop B, print-attributed divergence. Rolling 20 graded sessions: mean
  divergence_bar_bp greater than 12.0bp in the adverse direction (accrual above sleeve),
  with the companion attributing at least half of it to prints, that is mean print_gap_bp
  of at least 6.0bp over the same window. Halt entries and reopen the friction question
  (section 9.3) in the same report.
  Basis: 12bp is about two-thirds of the basket's +18.91bp gross; a sleeve that keeps
  less than a third of the graded gross for print reasons is not expressing the find.
- Stop C, operational failure. Any of: 3 consecutive graded sessions each carrying at
  least one on_exit_missed line; or 2 consecutive entry nights stood down by the
  eligibility floor (fewer than 10 eligible names); or any single session in which a
  position remains open 2 sessions after its entry (a leg that missed two opening
  auctions). Halt entries until the cause is cured at the source and proven on a fixture
  or a live session, per the desk's fix law.
- Stop D, order-shape violation. Any submitted order for this sleeve with type other than
  "market", or tif outside ("cls", "opg"), or an entry with tif "opg" or an exit with tif
  "cls", detected in grading (order_shape_violations above zero) or in any dispatcher
  journal read. Halt entries immediately, treat as a code defect: BUGLOG entry, blocker
  added or strengthened, cure before any further entry. This line has no window and no
  tolerance, because the never-crossed rule (section 5) has none.
- Stop E, weight collapse. Any entry night whose invested_fraction (section 9.1) is below
  0.70 is not entered at all: the plan is journaled and stood down before submission,
  because a basket with over 30 percent of its budget stranded by drops and one-share
  floors no longer resembles the equal-weight object under test. Two such nights in any
  10 sessions halt entries for review of the basket's tradability, with the drop reasons
  as the evidence.

### 12.3 What is not a stop line

- A losing night, or a losing week. The falsifier's horizon is 60 sessions; nothing in
  this sleeve stops on short-window P&L.
- The weekday/weekend split, earnings nights, and multi-day markings. These are recorded
  fields (sections 2 and 9), read at the falsifier's close, never sleeve-level gates.
- The options form. It was rejected on measured prices in Wave 4 (one weekend of theta
  costs 5 to 15 times the drift's delta capture on every leg priced) and is not part of
  this sleeve in any version.

## 13. Decisions made where the sources conflicted

1. MOC timing. Wave 4's sentence "orders rest as MOC from 15:50 ET" conflicts with the
   broker's cls rule (submissions after 15:50 ET on a regular session are rejected;
   submissions after 19:00 ET queue for the following session's close). Decision: 15:50
   is treated as the hard cutoff, and the submission window is 15:40:00 to 15:49:59 ET
   (shifted on early closes). The numbers that decided it are the broker's stated cutoff
   and rejection band; a spec that told the desk lane to submit at 15:50 would have built
   a sleeve whose first order is rejected. Blocker B-02 carries the corrected claim.
2. Fractional sizing versus the auction form. The desk's WS4 fractional cure (fractional
   quantities lawful, budget decides) conflicts with the broker's fractional rule
   (fractional qty only with time_in_force "day"). Decision: whole shares only inside
   this sleeve, equal weight approximated by section 6.2 and its dispersion graded
   nightly. The number that decided it: at the naive equal-weight target of $337.93 per
   name, 8 of the 29 names (AMAT, AMD, AVGO, LITE, MU, SMH, SNDK, TSM at 2026-11-13
   closes) cost more than one target each, so a floor-to-zero fractional-free sizing
   would have dropped all 8, including CARRY names SNDK and AMD, while a fractional
   sizing cannot ride the auction tif at all. The one-share floor plus top-up is the only
   sizing that keeps every eligible name in the auction.
3. Full basket versus CARRY-only. Decided for the full basket in section 4.2. The numbers
   that decided it: basket auction net +19.53bp per night (Wave 4, basket level, the only
   level measured); CARRY six-name true-print cost +5.845bp median (Wave 5), worse than
   the basket's bar-based -0.626bp; CRWV per-name print median +30.140bp. The falsifier
   grades the full basket, so the sleeve expresses the full basket.
4. Bar-based grading versus print truth. Wave 4's premise "the daily bar open and close
   are the auction prints" was corrected by Wave 5 (close: true, 60 of 60; open: false,
   4 of 60, pooled gap +5.436bp). Decision: the registered falsifier stays bar-based
   exactly as the accrual defines it (consistency with the 2,229-session exam series is
   why Wave 6 kept it), and print truth is graded beside it through the companion
   (section 9.2), never by editing the accrual. The sleeve's own stop lines read the
   print-based fields, because the sleeve's fills are prints, not bars.

## Appendix A. Grounding ledger

Every seam cited in this spec, as read for this spec on 2026-11-15. "Absent" means the
capability was searched for in the named place and not found; nothing absent is assumed
present anywhere in this spec.

- Shadow accrual, basket, anchor, legs, verdict, Wave 6 amendment fields:
  research_notes/decisions-api-leverage-20261114/keepgoing2/wave4/v1_shadow_accrual.py,
  module docstring and functions measured_costs_bp, load_earnings_events, is_event_leg,
  main. Constants read: FOCUS (29 names), ANCHOR "2026-11-13", TARGET_SESSIONS 60,
  REGISTERED_COST_BP 5.0, MIN_NAMES 10.
- Basket cross-check: keepgoing2/wave3/focus_bars.json keys (31 keys: the 29 names plus
  SPY and QQQ controls), and its 2026-11-13 close rows for the sizing scale in section 6.2.
- Wave 4 numbers: WAVE-4-2026-11-14.md sections V1 and V2, and keepgoing2/wave4/
  v1_friction.json (basket gross_mean_bp 18.907, net_crossing_bp_equal_weight -27.169,
  net_auction_bp_equal_weight 19.533, crossing_rt_bp_median_of_names 41.245).
- Wave 5 corrections: WAVE-5-2026-11-14.md section W5-1 (crossing mean of medians
  +46.076bp; bar close 60 of 60; bar open 4 of 60, pooled +5.436bp, CRWV +28.765bp; CARRY
  true-print median +5.845bp and the per-name medians).
- Wave 6 amendment and companion decision: WAVE-6-2026-11-15.md sections W6-1 (D1 to D7,
  D2 decision, W6A-PRINT-COMPANION as Wave 7 cell 2).
- Intent validation: desk3/models.py validate_intent (order types "market" and "limit"
  only; tif "day" and "gtc" only; fractional guard with "fractional_qty_limit_order";
  OCC_RE; is_fractional_symbol), client_order_id and client_order_id_untruncated.
- Door: desk3/broker.py PaperDoor.submit_order (wire body forwards type and
  time_in_force; options market-hours guard scoped to OCC plus market), PaperDoor
  get_order_by_client_id, get_open_orders, get_positions, get_account; FakeBroker
  submit_order and get_order_by_client_id (order dict lacks order_type and
  time_in_force today: absent, named in section 7).
- Dialect: desk3/broker_dialect.py broker_time_in_force, is_crypto_symbol,
  normalize_broker_symbol.
- Dispatcher: desk3/dispatcher.py Dispatcher.process_intent (validation through
  validate_intent, slice buying-power gate with "insufficient_slice_bp", reservation at
  cost times (1 + bp_buffer_frac), generic submit of order_type and time_in_force),
  Dispatcher._reject, _preflight_violation, slice_for (default bp_buffer_frac 0.02),
  PendingStore (durable pending intents across cycles).
- Scheduler session gating: desk3/scheduler.py in_session ("24h" always; otherwise
  09:30 to 16:00 ET weekdays), Scheduler.tick.
- Journals: desk3/journal.py append_line, read_lines, journal_generations,
  BatchedJournal.
- Sleeve shape precedent: desk3/sleeves/gate_1h.py and desk3/sleeves/leaps_momentum.py
  (INPUTS, SLEEVE_ID, evaluate(view, ctx), ctx.log); config/sleeves.json row shape
  (id, module, cadence_s, session, slice, bp_buffer_frac, flat_by_close,
  flatten_time_et, params, inputs, parked), including desk3.sleeves.* rows at slice
  10000.0.
- Fill adoption standard: muse-desk-v3/SLEEVE-AUTHORING-STANDARD.md, rules 1 to 5.
- Gate: muse-desk-v3/run_regression_blockers.sh (unittest discovery over
  tests/test_*_blockers.py; per-run receipt in state/gate_receipts/).
- Watchdog and restart route: muse-desk-v3/OPERATIONS.md (watchdog as systemd unit
  muse-desk-v3-watchdog.service, canonical copy in desk3/systemd/, status in
  state/watchdog.json), desk3/watchdog.py, desk3/run_live.py (loads config/sleeves.json).
- Broker auction and fractional rules: Alpaca order documentation (time_in_force values
  for equities: day, gtc, opg, cls, ioc, fok; opg and cls semantics and their submission
  cutoffs at 09:28 and 15:50 ET, with after-19:00 queueing) and Alpaca fractional trading
  documentation (fractional support tied to time_in_force "day"), both read on 2026-11-15
  for this spec.
- Charter Amendment 16: searched in the desk tree (desk3/ sources and the desk markdown
  read above) and not found there: absent from the desk tree as read. Section 6.1 states
  the consequence and the landing check.
