# Run this desk as your own alert system

Everything in this repo was built to be *used*, not admired. This note covers
the two ways people actually use a system like this day to day:

1. As an **alert system** that watches the market for you and taps you on the
   shoulder only when something matters.
2. As a **replacement for the stack of expensive vendor services** that get
   advertised all over X, for roughly the cost of one LLM subscription.

## Part 1: The terminal on your home screen

The terminal is a set of plain web pages. Anything that can open a web page
can be your desk:

- **iPhone / iPad:** open the terminal in Safari, tap Share, then
  *Add to Home Screen*. It gets its own icon and opens full screen, like an
  app.
- **Android:** open it in Chrome, tap the menu, then *Add to Home screen*
  (or *Install app* where offered).
- **Desktop:** bookmark it, or pin the tab. The hub page is the front door;
  every tool and engine is one tap from it.

What you get from that one icon: your watchlists and boards, the flow and
dark-pool picture, expected moves around earnings, squeeze and short-volume
state, insider and 13F activity, and 30 forecast engines whose predictions
are written down before the fact and graded after it. No login wall, no
feed of other people's opinions, no upsell modal. It is a quiet instrument
panel, and that is the point.

## Part 2: Let the LLM be the notification layer

A page you have to remember to check is a page you will stop checking. The
pattern that works is the one this desk runs on: **the agent watches, and
you get pinged.**

There are two alert routes, and you can run either or both:

**Route A: scheduled reads.** Give your agent standing instructions to read
the terminal and the market on a rhythm and report in your chat, for
example:

- a pre-open read: overnight news on your names, earnings before the bell,
  the day's expected moves, anything your open positions need;
- a midday check: positions versus their invalidation levels, unusual flow
  in names you hold;
- a pre-close pass: anything that must be decided today, exits that are
  blocked or unfilled, stops that have not been confirmed;
- a close review and a weekly grading: what the system predicted, what
  happened, scored against the index benchmarks.

**Route B: event watches.** The agent checks conditions on an interval and
messages you only when one fires: a forecast engine issues a call on a name
you track, a position crosses its stop, an exit order fails or is rejected,
a data feed goes stale, an earnings date moves. The discipline that makes
this livable is a ping rule: *no blank pings.* You are contacted for a real
event or a decision, never for "nothing new." An alert system that cries
wolf gets muted, and a muted alert system is worse than none.

Browser push notifications from a hosted copy of the terminal are the third
option where your hosting supports them, but the agent route is stronger:
the message can carry the *so what* (the level, the size, the record of the
signal making the call), not just a badge on an icon.

## Part 3: Replicating the vendor stack

Scroll X for ten minutes and you will be sold the same six products under
twenty brand names. Here is what each one actually is underneath, what it
typically costs, and what the equivalent is in a system like this one.

### Options flow (the big one)

**What they sell:** a live feed of options prints flagged as sweeps,
blocks, unusual activity, with a "bullish / bearish" label. Typical cost:
about $40 to $150 a month, per platform.

**What it actually is:** the public options tape (OPRA), filtered and
relabelled. The filtering is code: print size versus open interest, prints
at or through the ask, multi-exchange sweeps, repeated prints in a name.

**The equivalent here:** the Flow Tape family (flow board, tape heatmap,
sweep wire, premium meter) built from the same print data your brokerage
API already gives you, plus the part the vendors leave out: every alert
family here is *graded*. A flow alert is a claim, and claims get scored
against what price did next. Vendors sell you the alerts; they do not sell
you their own report card.

**Honest limit:** a true real-time, full-market OPRA feed is a licensed
product. The brokerage-API route covers the names you actually trade, on a
snapshot cadence. For a swing trader that is the whole game; for a scalper
it is not, and no note should pretend otherwise.

### Dark pool and off-exchange data

**What they sell:** dark pool print levels, "whale" accumulation charts,
short-volume ratios. Often bundled at $50 to $100 a month, or sold as a
separate indicator.

**What it actually is:** FINRA publishes off-exchange and short-volume
files *for free*, daily. The vendor's contribution is downloading them and
drawing the chart.

**The equivalent here:** the dark-prints store and the Short Volume Ledger
read those same FINRA files directly, per name, every session, and keep
the history so the readings accumulate into something testable.

### Gamma exposure and dealer positioning (GEX)

**What they sell:** gamma flip levels, call and put walls, dealer hedging
maps. Commonly $75 to $200 a month as a standalone, with a great deal of
mystique in the marketing.

**What it actually is:** open interest by strike (which your brokerage's
options chain already carries), a pricing model for the Greeks, and
arithmetic: multiply, sign by an assumption about who is long, sum.

**The equivalent here:** the chain snapshots collect open interest per
strike every session, the gamma and pin tools do the same arithmetic in
the open, and the assumptions are printed on the page instead of hidden
behind the word "proprietary."

**Honest limit:** the sign assumption (who holds what) is a model, here
and at every vendor. Anyone who presents a gamma wall as a fact is selling
you the model as if it were the market.

### Expected move and earnings tools

**What they sell:** earnings calendars with implied moves, post-earnings
drift stats, "win rate" tables. Typically $30 to $100 a month or folded
into a scanner subscription.

**What it actually is:** the at-the-money straddle price divided by the
stock price, plus a table of past reactions. The straddle is sitting in
the options chain you already have.

**The equivalent here:** the earnings calendar re-checks dates on a
cadence, prices each upcoming report's expected move from a stored chain
snapshot (never estimated from historical volatility and passed off as the
market's number), and the drift engines write their forecasts down and get
graded on the outcome.

### Insider, 13F and "smart money" trackers

**What they sell:** alerts when insiders buy, maps of what famous funds
hold, cluster-buy signals. $25 to $100 a month is common.

**What it actually is:** SEC filings. Form 4s and 13Fs are public the
moment they are filed. EDGAR is free.

**The equivalent here:** the insider and filings lanes read EDGAR
directly, keep per-trade dates and roles (so a cluster is checkable rather
than asserted), and widen coverage as filings land. 13F data is a quarter
stale by law; here that lag is printed on the reading, not smoothed over.

### Scanners, indicators and signal sellers

**What they sell:** the glowing arrow. Buy and sell signals, squeeze
scanners, "AI" pattern detectors, at anywhere from $30 a month to four
figures a year, with a highlight reel instead of a track record.

**What it actually is:** a formula. Sometimes a good one. The formula is
almost never the expensive part; the expensive part is that you cannot see
it, cannot test it, and cannot check what it did on the days it was wrong.

**The equivalent here:** this repo holds 651 strategies with their
algorithms written out, and the terminal's forecast engines all run under
one rule the signal sellers will not touch: **ledger before display.** A
prediction is written to an append-only record before its horizon, and the
grade is computed from that record. A strategy that cannot survive that
treatment is labelled with what it actually is, including the ones that
were tested and buried, which stay in the catalog marked as killed so
nobody rebuilds them by accident.

### News and research wires

**What they sell:** headline wires, analyst-action feeds, sentiment
scores, $100 a month and up.

**What it actually is:** an API and a summarizer. Your brokerage likely
already includes a news API (Alpaca's, for example, is part of the data
package), and summarization is the thing your LLM subscription is *for*.

**The equivalent here:** a news lane on the brokerage feed, read by the
agent, filtered to your names, folded into the scheduled reads in Part 2
instead of arriving as 400 headlines an hour.

## Part 4: The cost math

Add the typical stack: flow platform, GEX tool, earnings tool, insider
tracker, scanner or signal service, news wire. You are at roughly **$300
to $700 a month**, for six logins, six partial views of the same market,
and zero shared memory between them.

The agent version is: one LLM subscription, brokerage accounts you already
have (their data APIs are part of the account), and free public sources
(FINRA, SEC EDGAR) read directly. The agent writes the filters, keeps the
stores, runs the grading, and carries the context between all of it,
because it is one system instead of six.

What the money genuinely cannot replicate, stated plainly:

- a licensed real-time full-market options tape;
- point-in-time, survivorship-free institutional databases (the long
  history vendors buy is real, and building your own takes time to
  accrue);
- someone else's support desk when it breaks at 9:31 in the morning.

What it does *better* than the stack: one record of every call the system
makes, graded in public; every assumption printed where you can read it;
alerts that know your positions, your stops and your rules, because they
come from your agent and not from a broadcast. The vendors sell you their
certainty. This sells you nothing, and shows its work.

## Where to start

- Build the desk itself: the three guides linked from this repo's front
  page (start with the reconciliation, it maps how they fit together),
  including a runnable skeleton with tests.
- Grade everything: adopt the ledger-before-display rule on day one. It
  is the single habit that separates a tool from a toy.
- Wire the alerts last but wire them early: a pre-open read, a pre-close
  pass, and a no-blank-pings rule will carry a surprising amount of the
  value in the first week.
