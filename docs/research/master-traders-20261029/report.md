# The Great Traders — A Masterclass in How They Actually Think and Operate

### For a working quant / swing / options trader: setups in detail, how they read the market, how they decide, size, enter, exit, and manage themselves — and how to practice it, in order, as one combined operating style

> Read this as a curriculum, not a ranking. Every trader below is a teacher. The question throughout is not *“should I believe them?”* but *“what exactly do they do, why does it make sense to them, what mental model is underneath it, and what drill would make that skill mine?”*

---

## How to Use This Masterclass

The greats do not share one strategy. They share a way of building a strategy:

1. **Study what has actually moved big before.** Livermore, O'Neil, Minervini, Zanger, Ryan and Qullamaggie all began by studying hundreds/thousands of past big winners, chart by chart, until the shapes lived in memory.
2. **Reduce that study to a small playbook** — 2–4 setups, named, with pictures in the mind.
3. **Define, before entry, where you are wrong,** and size from that distance.
4. **Let the market, not your opinion, tell you to get bigger** — add only to winners, sell into strength or trail, never average a loser.
5. **Keep score in risk units and review relentlessly,** so the playbook improves and your own tendencies become visible.

Everything below is an elaboration of those five moves, in different markets and languages: stocks, futures, currencies, options, and systematic portfolios.

**The practice sequence (preview, detailed in §7):**
First learn to survive and to read trend (Weinstein → Livermore → Kovner/Tharp). Then learn one stock playbook cold (O'Neil/Minervini/Kell/Qullamaggie — they are one lineage). Then learn sizing as a skill in itself (Tharp, Kelly in fractional form, Druckenmiller/Tudor Jones). Then learn options as *structures for expressing the same views with defined shape* (Natenberg → Saliba/McMillan → when to buy premium vs. sell it). Then learn the quant habit: write rules, test them, expect them to fade, diversify across independent bets (Thorp, Simons, Shaw, Asness, Arnott). Then learn macro as context, not prediction (Soros, Druckenmiller, Tudor Jones, Bacon, Kovner). Practice in that order.

---

## 1. Legendary Discretionary Stock / Swing Traders — One Lineage, Many Voices

This is a single family tree. Livermore → Darvas → O'Neil → Ryan / Zanger → Minervini → Ritchie II / Kell, with Weinstein giving it a stage vocabulary and Qullamaggie translating it for modern liquid momentum names. Learning them together is faster than learning them separately, because each one clarifies the others.

### 1.1 Jesse Livermore — Tape Reading, Pivotal Points, and Sitting

**Books:** *Reminiscences of a Stock Operator* (1923, Edwin Lefèvre, based on Livermore) and his own *How to Trade in Stocks* (1940).

**How he reads the market.** Price and volume *are* the news. Livermore started in bucket shops reading the tape — the stream of prices — and never stopped believing the tape tells you what insiders and institutions are doing before any story explains it. A stock acting right on good and bad news, holding up when the market falls, breaking a “pivotal point” on expanding activity: that is information. A stock that cannot rally on good news is telling you it is weak, whatever the story says.

**Mental model: trade only when precedents favor you, then sit.** His most quoted self-indictment, via Lefèvre: *“What beat me was not having brains enough to stick to my own game — that is, to play the market only when I was satisfied that precedents favored my play.”* And: *“It never was my thinking that made the big money for me. It always was my sitting.”*

Teach that in two parts:
- **Patience before the trade:** wait, in cash if necessary, for a pivotal point — a level whose break confirms the line of least resistance has changed. Do not anticipate it, do not trade in the middle of a range out of boredom.
- **Patience in the trade:** once a position taken in stages is showing a profit and the trend confirms, *sit tight*. The big money is in the big move, not in scalping fluctuations.

**Setups / execution in detail:**
- **Pivotal-point breakout:** Identify the key level (prior high/low, end of a reaction). First buy/sell only when price goes through it. That break is the market voting.
- **Probing / pyramiding:** Enter in tranches. First tranche is a test. If it shows a loss, out — the timing is wrong. If it shows a profit and the pivotal point holds, add a second, then a third tranche. *Never add to a loser.* He is explicit in *How to Trade in Stocks*: establish a stop before the trade, never sustain a loss of more than 10% of capital on a speculation, “profits take care of themselves but losses never do.”
- **Line of least resistance:** Before any trade, determine whether it is up, down, or sideways. Trade only in its direction. In a sideways market, the correct position is often no position.
- **Leading stocks / leading group:** Trade the leaders of the leading group, long or short. Laggards do not pay for the risk.

**Sizing and self-management — learn from the shape of his life, as he himself taught it.** Livermore made fortunes shorting the Panic of 1907 and the 1929 crash — the latter commonly retold at about $100 million — and also went through repeated bankruptcies (notably 1915, and finally 1934) and died in 1940. In his own writing the lessons he extracts are not “be bolder” but: do not trade on tips (his cotton loss after listening to another man's conviction is his own cautionary example in *Reminiscences*), do not trade every day, do not let a loss grow because you hope, and separate trading capital from living capital — he put money in trust for family precisely because, in his words to Lefèvre, a man can lose every cent he can lay his hands on. The drill he leaves you: *write your rules when calm, and treat breaking them — not losing money — as the failure.*

Sources: https://www.alphaexcapital.com/jesse-livermore ; https://www.oreilly.com/library/view/trade-like-an/9780470616536/9780470616536_cutting_losses_quickly.html

### 1.2 Nicolas Darvas — The Box: Let the Stock Tell You, From a Distance

**Book:** *How I Made $2,000,000 in the Stock Market* (1960). Darvas was a professional dancer touring the world, trading by telegram — that constraint *created* his method, and it is why it suits a daily-bar swing trader so well.

**How he reads the market.** Ignore tips, tipsheets, boardroom gossip, and his own earlier fundamental dabbling. A stock rising to new highs on rising volume, then consolidating calmly, is a stock under accumulation. He called his mature method “techno-fundamentalist”: use fundamentals only as a coarse filter for earnings momentum, then let price/volume decide everything about timing.

**The Darvas Box, step by step:**
1. Screen for stocks making new 52-week highs with expanding volume and strong recent earnings growth.
2. Watch the consolidation that follows a rise: note the highest price reached (top of box) and the lowest pullback price over several days/weeks (bottom of box). Darvas required the box to settle — typically a few days with price not making a new high — before it counted.
3. Place a buy-stop just above the top of the box. You are bought *only* if strength resumes.
4. Place a sell-stop just below the bottom of the box (later, below the bottom of each *new, higher* box as the stock stair-steps up). Each new box ratchets protection upward.
5. Pyramid as new boxes form above old ones. Sell automatically when a box breaks down — no deliberation, which for Darvas, thousands of miles away, was the point.

**Mental model:** *A system that removes intraday emotion.* Darvas checked quotes end-of-day, sent stop orders, and danced. The modern translation: set alerts/stops from the daily close, do not stare at a consolidating position into a bad decision.

Source: https://ww2.jacksonms.gov/browse/rFpxrs/2OK050/how_i__made_2000000__in__the_stock_market-nicolas__darvas.pdf

### 1.3 William O'Neil — CAN SLIM: Study Winners, Buy Strength, Cut at 7–8%

**Book:** *How to Make Money in Stocks*; founder of *Investor's Business Daily*.

**His research method is the lesson before the acronym.** O'Neil studied the biggest winners of every cycle back to the 1950s (in later editions, a century) and asked: *what did they look like just before the big move?* CAN SLIM is the answer, as a checklist:

- **C — Current earnings:** Quarterly EPS accelerating, typically +25% or more (the greats often far higher), with sales acceleration confirming it is real demand, not cost-cutting.
- **A — Annual earnings:** Strong 3–5 year growth, high ROE (17%+ in his teaching).
- **N — New:** New product/service, new management, new industry change — and technically, a new price high. “New” is a catalyst + a chart event.
- **S — Supply & demand:** Small-to-reasonable float, and above all, price up on big volume / down on light volume. Demand you can see.
- **L — Leader or laggard:** Buy the #1 or #2 stock in a leading group. Relative strength 80–90+. Never buy a laggard because it is “cheap” or “due.”
- **I — Institutional sponsorship:** Some quality funds owning / increasing — institutions move prices for months — but not so widely owned it is crowded and late.
- **M — Market direction:** Three of four stocks follow the market. O'Neil teaches follow-through days to confirm a new uptrend after a correction, and distribution days (index down on higher volume) as a warning to reduce exposure. *Most CAN SLIM buys should only be pressed in a confirmed uptrend.*

**Entry — the base and the pivot:**
Cup-with-handle, flat base, double bottom — at least ~7 weeks on a weekly chart for a cup, with a handle drifting *down* on light volume in the upper half. Buy point = pivot (top of handle/base + a small amount) on volume at least ~40–50% above average. Do not buy extended: more than ~5% past the pivot is chasing; the risk/reward and the stop math break.

**Exit — the part disciples say matters most:**
- **Hard loss rule: sell at 7–8% below cost, no exceptions, no averaging down.** “Letting your losses run is the most serious mistake made by most investors.”
- **Profit rule (starting point):** Take profits at 20–25% in 1–3 weeks for many leaders (exception: a stock up 20%+ in 1–3 weeks from a proper base is showing exceptional strength — hold at least 8 weeks in his teaching and reassess), and obey sell signals: climax top (biggest daily gain after a long run, on huge volume), break of the 10-week line on heavy volume after an extended advance, etc.

**Mental model:** *You will be wrong often; make being wrong cheap and being right count.* A 50% win rate with 7% losses and 25%+ winners is a powerful expectancy — if, and only if, the loss rule is absolute.

Sources: https://en.wikipedia.org/wiki/CAN_SLIM ; https://winchellhouse.com/2026/10/10/how-to-make-money-in-stocks/

### 1.4 David Ryan — O'Neil's Protégé: Historical Models in Your Head

Ryan worked at O'Neil & Co. for 17 years and won the U.S. Investing Championship three years running (1985–87, triple-digit returns each year, compounding to about 1,379% over the three years in the retelling in *Momentum Masters*).

**How he teaches learning:** *“I studied historical models of great winning stocks to ingrain in my mind what a stock looked like before it made a major move. I tried to get to the point where I was looking at the exact same things O'Neil did.”*

That is a drill, not a slogan:
- Print / save annotated charts of past superperformers at their buy points.
- Review the same set repeatedly until pattern recognition is instant.
- Each night, scan for *today's closest match* to those models, not for a novel idea.

**His additions:** tightness matters (quiet, tight price action near highs before a breakout = supply exhausted); look for persistent institutional accumulation — his “Ants” work tracks stocks rising steadily on consistently elevated volume over ~12–15 sessions, institutions building a position day after day rather than in one spike; earnings *and* sales acceleration together; sell when the character changes (a leader breaking down on volume after an extended run has told you the sponsorship is leaving).

Sources: https://www.turtletrader.com/trader-ryan/ ; https://deepvue.com/indicators/david-ryan-ants-indicator/

### 1.5 Dan Zanger — Pure Price and Volume, 400 Charts a Night

Former pool contractor; featured in *Fortune* in December 2000 (“My Stocks Are Up 10,000%!”) for turning about $10,775 into $18 million in 18 months in the late-1990s bull market, $42 million by 23 months in that account's story — told in *Momentum Masters* and in his *Stocks & Commodities* interview.

**His method, in his own words:** *“I use absolutely no indicators whatsoever. I simply rely on chart patterns, price, and volume.”* And: scroll ~400 stocks a night, daily bars, dissecting the volume bars as a “pressure factor” — *is it ready now, or does it need more time?*

**Setups:** Classic patterns (flags, triangles, channels, cup patterns) in high-volatility, in-play leaders, bought on the break of the pattern boundary on expanding volume, often intraday when the daily pattern completes. He learned the personality of his watchlist names — how a given stock typically shakes out, how far it typically runs — by watching the *same* names for years. “They are my buddies” is his phrase for that familiarity.

**Mental model for a modern trader:** Depth beats breadth of *tools*. One language (price/volume/pattern), read fluently on hundreds of charts a week, beats ten indicators read shallowly. The nightly 400-chart pass is the practice: it builds the pattern library Ryan talks about, and it produces tomorrow's short, focused list.

Sources: http://www.traders.com/Documentation/FEEDbk_docs/2003/08/Abstracts_new/Interview/interview.html ; https://pubhtml5.com/pklzi/jywe//basic/

### 1.6 Stan Weinstein — Stage Analysis: Know Which Stage You Are In

**Book:** *Secrets for Profiting in Bull and Bear Markets* (1988).

**The four stages (weekly charts, 30-week moving average is his compass):**
- **Stage 1 — Basing:** After a decline, price goes sideways around a flattening 30-week MA. Volume dries up, then expands on up-weeks. *Do not buy yet — there is no trend to ride. Build the watchlist.*
- **Stage 2 — Advancing:** Breakout above Stage 1 resistance on expanded volume, price above a now-rising 30-week MA, relative strength vs. the index turning up. *This is the only stage for longs.* Pullbacks to the rising MA / breakout level are secondary buys.
- **Stage 3 — Topping:** Price chops sideways after a big advance, 30-week MA flattens, heavy down-volume weeks appear, RS deteriorates. *Sell / tighten stops. Do not buy breakouts here.*
- **Stage 4 — Declining:** Breakdown below Stage 3 support, price below a falling 30-week MA. *No longs. This is the shorting stage for those who short, and the cash stage for everyone else.*

**Execution details modern summaries preserve from his teaching:** Enter on a weekly-confirmed Stage 2 breakout; initial stop just below the breakout level / most recent higher low; trail below higher lows; never buy far extended above the 30-week MA; check the *group* and the *market* stage as well as the stock — a Stage 2 stock in a Stage 4 market fights the tide.

**Why Minervini and everyone after him borrowed it:** Stage gives you a regime language. Before “do I buy?” ask “which stage is the market in, which stage is the group in, which stage is the stock in?” If the answers do not line up, size down or stand aside.

Sources: https://arongroups.co/forex-articles/stage-analysis-trading/ ; https://br.tradingview.com/chart/TSM/XThVT5Ud-Weinstein-Stage-Analysis/

### 1.7 Mark Minervini — SEPA® and the VCP: Precision Entry in Stage 2 Leaders

**Books:** *Trade Like a Stock Market Wizard*, *Think & Trade Like a Champion*. U.S. Investing Championship winner 1997 (+155% on a long-only stock account) and again 2021 in the $1M+ stock division (+334.8%).

**SEPA — Specific Entry Point Analysis — is a funnel, in this order:**
1. **Trend** — pass the Trend Template (below).
2. **Fundamentals** — accelerating earnings and sales (he looks for strong, preferably accelerating quarterly growth, expanding margins, a catalyst), in the O'Neil tradition.
3. **Catalyst** — something new driving institutional interest.
4. **Entry** — a precise pivot from a constructive base (the VCP, below).
5. **Risk** — defined *before* entry, small, and non-negotiable. If any funnel stage fails, there is no trade, however exciting the story.

**The Trend Template — memorize it as a pass/fail screen:**
1. Price above both 150-day and 200-day MAs.
2. 150-day MA above 200-day MA.
3. 200-day MA rising for at least 1 month, preferably 4–5.
4. 50-day MA above both 150- and 200-day MAs.
5. Price above 50-day MA.
6. Price at least 30% above its 52-week low.
7. Price within 25% of its 52-week high (closer is better).
8. Relative Strength rating ≥70, preferably 80s–90s.

Sources: https://de.tradingview.com/script/88aL78Qh-TwP-Mark-Minervini-Trend-Template-Criteria/ ; https://www.financialtechwiz.com/post/mark-minervini-trading-strategy/

**The Volatility Contraction Pattern (VCP) — his signature setup, taught in detail:**
A leader, already in a Stage 2 uptrend, consolidates in a series of progressively *smaller* pullbacks — e.g., –18%, then –12%, then –7%, then –3% — each on declining volume, with price tightening near highs. Each contraction is sellers exhausting and supply drying up; the footprint often looks like 2–6 contractions (2–6 “T”s) over a base of several weeks.
- **What you are seeing:** volatility and volume contracting = no distribution, holders unwilling to sell lower.
- **Pivot / entry:** buy as price breaks through the pivot (the high of the final, tightest contraction) on expanding volume.
- **Stop:** below the low of the final contraction — often only a few percent away, *which is the whole point*: a tight pivot gives you a small, defined risk and therefore a large position for a given dollar risk. Minervini teaches keeping average losses small (his general loss-cutting discipline is tighter than O'Neil's 7–8% in strong practice — cut quickly if a breakout fails, and never let a small loss become a large one) and working to keep the average loss well below the average gain.
- **Management:** A breakout that works should progress promptly. If it stalls, reverses through the pivot on volume, or the market weakens, reduce/exit. Sell some into strength / into extension, raise stops, and let a core ride while Stage 2 persists. He grades his own trades post-hoc, studies his winners *and* losers for whether they had the SEPA characteristics, and — famously — treats protecting his confidence and his “risk-adjusted” mindset as part of the system: trade smaller when out of sync, larger only when trades are working and the market is confirming.

**His performance mindset, from *Think & Trade Like a Champion*:** Think in terms of risk first (“how much can I lose?” before “how much can I make?”), keep a trading journal with statistics (batting average, average gain/loss, gain/loss ratio), and rehearse the plan — contingency plans for gap-downs, earnings, market breaks — *before* the open, so in the moment you execute rather than improvise.

### 1.8 Marty Schwartz — “Pit Bull”: From Being Right to Making Money

**Books:** *Market Wizards* interview; memoir *Pit Bull: Lessons from Wall Street's Champion Day Trader*. U.S. Investing Championship winner 1984, trading futures and options, famously consistent month after month in that era.

**The turn that made him:** He stopped trying to be *right* (his fundamental-analysis years losing money) and started following price. In his words as retold in every summary of *Pit Bull*: trading is not about being right, it is about making money — and those are different goals, because ego defends a position, while money management exits it.

**How he trades:**
- **Moving-average filter, stated as a rule:** “I try not to go against the moving averages; it is self-destructive.” He used a 10-period EMA as a bullish/bearish divider: above it, look long; below it, look short / stand aside.
- **Relative strength / divergence:** A stock/index that holds above its prior low when the market breaks its low is showing health — those divergences are what he hunts.
- **Know your “uncle point” before entry:** The loss level at which you are out, defined in advance, honored without negotiation.
- **Do not increase size right after big profits:** “My biggest losses have always followed my largest profits.” After a strong run, he taught playing *smaller*, even taking a day off as a reward — euphoria is a risk factor, not a permission slip.
- **Bottom-fishing is expensive gambling.** Buy strength, sell weakness; do not catch falling instruments because they feel cheap.

**Position construction note:** Schwartz used options and futures to control large exposure with a defined premium / margin at risk, sizing so a single trade risked only a small percent (summaries of his practice put it in the ~1–3% range, shrinking when out of rhythm). The transferable core is not the instrument, it is: *big exposure ≠ big risk, if the exit is defined and the size is set from the exit.*

Sources: https://www.turtletrader.com/trader-schwartz/ ; https://www.tradingeducators.com/blog-page/the-golden-rules-of-martin-s-schwartz?format=amp

### 1.9 Paul Tudor Jones — also here because every stock trader needs his defense

Full treatment in §4, but his stock-relevant rules belong in this lineage too: demand ~5:1 reward-to-risk so you can be wrong most of the time; use the 200-day MA as a regime line (“nothing good happens below it” in his teaching as retold); “losers average losers” — never add down; every day assume every position you have is wrong and know where you would get out. See §4.3.

### 1.10 Kristjan Kullamägi (Qullamaggie) — Breakouts, Episodic Pivots, Parabolic Shorts

Swedish momentum swing trader who streamed/recorded his trading extensively for years; his site and streams are the primary classroom. He credits Pradeep Bonde (Stockbee) for the episodic pivot, and O'Neil/Zanger/Livermore for the breakout lineage. His claimed journey ($3k into a nine-figure sum over a decade of momentum trading) is the backdrop; the *method* below is what to study.

**His universe filter:** Only the strongest, most in-play names. He scans for the top 1–2% of stocks by 1-, 3-, and 6-month performance — names appearing across all three lists are the current leaders — and requires enough daily range to pay for the risk: ADR (average daily range, 20-day) typically >4%. Quiet stocks are ignored entirely.

#### Setup 1 — Breakout (continuation) — his bread and butter
1. **Prior move:** +30–100%+ in the past 1–3 months. Non-negotiable — the stock is already a leader.
2. **Orderly consolidation:** 2–8 weeks (some summaries say 1–3 weeks for tighter flags) sideways, range tightening, higher lows, “surfing” the rising 10- and 20-day MAs.
3. **Entry:** Break of the consolidation / opening-range high (ORH) — the high of the first 1-, 5-, or 60-minute candle on the breakout day. Longer ORH = later, cleaner entry; shorter = earlier, noisier.
4. **Stop:** Low of the day, and *never wider than 1× ADR*. If the distance entry→day's low exceeds ADR, skip the trade — the asymmetry is gone.
5. **Size:** Risk 0.25–1% of account per trade (he traded nearer ~1–1.5% when small, ~0.5% or less as the account grew); position typically 10–20% of account, max ~30% overnight, sized *from* the stop: shares = (account × risk%) ÷ (entry − stop).
6. **Exit in two stages:** Sell 1/3 to 1/2 after 3–5 days into strength / at roughly +2–3R, move stop on the rest to breakeven, then trail with the 10-day (faster names) or 20-day MA — exit on first close below the trailing MA. In a strong market he notes winners in this setup can run 10–20× initial risk, which is why a ~30% win rate can still be very profitable: expectancy lives in the tail winner, protected by many small –1R losses.

Source: https://breakoutshappen.com/stock-news/how-to-trade-like-qullamaggie-setups-strategy-and-screener

#### Setup 2 — Episodic Pivot (EP)
A previously *neglected* stock — sideways/down for months — gaps up **10%+** on a genuine surprise: earnings far above expectations with strong (ideally triple-digit) revenue/EPS growth and raised guidance, an FDA decision, a major contract — with a full normal day's volume trading in the first 5–15 minutes.
- The six-rule version taught by Bonde/Kullamägi: (1) real surprise, (2) neglected beforehand — if it already ran +30% into the news, the surprise is spent, (3) the gap clears the recent range (“free air” — no overhead supply), (4) volume is the tell, (5) enter on the gap day through the opening-range high, stop at the day's low, skip if stop >1× ADR, (6) it holds its gap / closes strong — a weak close on the catalyst day is a warning, exit.
- Manage like a breakout: sell a portion into the first days' strength, trail the rest on 10/20-day MAs. The best EPs become multi-week/month leaders because institutions need weeks to build positions in a name they owned none of yesterday.

#### Setup 3 — Parabolic Short (advanced, smallest size)
A stock up 3–5 straight vertical days, +40–60%+ in a week, often gapping, far extended from its 10-day MA, in a name with no fresh fundamental justification for the speed. Short the first lower high intraday / break of the prior day's low, stop above the day's high, cover in pieces into a fall back toward the 10-day MA. He treats this as his riskiest setup: it fights momentum, so size is smallest, stop is absolute, and it is only for experienced hands. The long mirror (parabolic long into a capitulation flush) follows the same exhaustion logic in reverse.

**His process habits to copy:** Build the watchlist the night before with alerts at pivots; at the open, trade only the top few names; journal every trade; study thousands of historical examples of each setup (“studying past winners” is, again, the curriculum); sit out choppy / bearish markets in cash — most of his money, in his telling, was made in good market windows, defending in between.

Sources: https://sharepredictions.com/tools/qullamaggie-breakout-planner/ ; https://timelessmarkettheory.com/traders/kristjan-qullamaggie

### 1.11 Oliver Kell — The Cycle of Price Action

2020 U.S. Investing Championship winner in the under-$1M stock division (+941.1% that year). Book: *Victory in Stock Trading*.

**His map: every trending stock cycles around its 10- and 20-day EMAs.** Learn to locate where a stock is in the cycle, and you know what trade, if any, is available:

1. **Reversal Extension:** Price stretches far *below* the 10/20 EMAs in capitulation. Action: watch, do not short the hole, look for basing. This is Kell learning Livermore's patience at bottoms.
2. **Wedge Pop — “the money pattern”:** Price breaks out of a declining wedge / tight mini-base, often gapping back above the 10/20 EMAs. Action: earliest, most aggressive long entry, with the mini-base low as invalidation.
3. **EMA Crossback:** After the pop, price pulls back to touch/reclaim the rising 10/20 EMAs and holds. Action: add / enter with trend now confirmed — the MAs that were resistance are now support.
4. **Base 'n Break:** A 1–3 week tight consolidation along rising EMAs (flag/pennant/rectangle), then a break to new highs. Action: continuation buy, repeatedly, while the pattern repeats.
5. **Exhaustion Extension:** Price stretches far *above* the 10 EMA in a climactic, parabolic leg. Action: trim / take profits — reward-to-risk has flipped.
6. **Wedge Drop:** Price rolls over, breaks down through the 10 EMA after exhaustion. Action: exit remaining longs; a new down-cycle is starting.

**How he aligns timeframes:** Weekly for context/direction, daily for management, ~65-minute for execution timing. He looks, in his championship interviews, for innovative growth companies whose stocks *hold up best during corrections* — “stocks that don't want to go down” — relative strength during market weakness as the tell of the next leader. He has been open that his first six of ten years trading made no money: his lesson is that the cycle framework + risk discipline took years of reps, and position sizing / cutting quickly is what allowed him to survive long enough to learn it.

Sources: https://cyclesedge.substack.com/p/follow-the-cycle-of-price-action ; https://deepvue.com/screener/oliver-kell-screens/ ; https://www.bowdoin.edu/news/2021/03/oliver-kell-10-wins-national-investment-contest-posting-nearly-tenfold-returns.html ; https://kelltrading.com/

### 1.12 Mark Ritchie II and the Modern Championship Winners — What a Current Playbook Looks Like

Ritchie II (son of *Market Wizards* trader Mark Ritchie) is a co-panelist in *Momentum Masters* (Minervini, Ryan, Zanger, Ritchie II) and a Minervini-method practitioner — in TraderLion / Minervini Private Access teaching, he and Brandon Hedgepath are presented working from about $100k to over $20 million over 13+ years using Minervini's methodology, trading VCPs, pullback buys in Stage 2 uptrends, and “grand slam” continuation trades in leaders such as ARM / IREN / NBIS-type names in recent cycles, with universal stops and a never-move-a-stop-down rule.

Study the *roundtable*, not just an individual: in *Momentum Masters* the four masters, asked the same questions, converge in their answers on — trade only leading stocks in leading groups, earnings/sales strength behind the move, precise pivot entries, cut losses at a pre-set small percent and never argue, concentrate in your best ideas rather than diversifying into mediocrity, and do the nightly homework. Their disagreements are in flavor (Zanger: no indicators; Minervini/Ryan: fundamentals + charts; Ritchie II: a younger, more concentrated, faster version of Minervini), not in risk.

**What the U.S. Investing Championship as a whole teaches a learner** (results by year, $20k+ and $1M+ stock divisions):
- Winning years are *concentrated, high-turnover leadership trading*: typically 5–12 core positions at a time (not 50–100), 100–250 trades a year for swing-style winners like Minervini and Kell, pyramiding quickly into a Tesla-type winner and cutting losers immediately.
- Huge winning percentages cluster in strong bull years (Kell +941.1% in 2020; Minervini +334.8% in the $1M+ division in 2021; Goverdhan Gajjala +805.1% in the $20k+ division in 2023; Law Wai-Sum +353.9% $1M+ in 2024) and collapse toward capital preservation in bear years (2022 $1M+ stock winner: +13.5% in a –19.4% S&P year — *winning that year meant mostly not losing*).
- The lesson to internalize: **the same playbook has an on/off switch.** Championship trading is aggressive *when leadership is working* and defensive when it is not. Expecting championship-style returns in a Stage 4 market is misunderstanding the method.

Source: https://completetradersedge.com/us-investing-championship/

---

## 2. Options Masters — and How Practitioners Actually Use Each Options Strategy

Options are not a separate game. In the masters' hands they are *shapes*: a way to give a stock view a defined floor, a sold-insurance income stream, or a convex payoff that explodes only in the tails. Learn the shape first, the Greek that dominates it second, the trade last.

### 2.1 Sheldon Natenberg — Think in Volatility, Not in Price

**Book:** *Option Volatility and Pricing* — the floor trader's textbook.

**Core mental model:** An option's price is, above all, a forecast of future volatility. Direction (delta) is only one exposure. Every position is simultaneously long/short volatility (vega), long/short time decay (theta), and convex (gamma). A good options trader asks, before any trade: *What volatility am I buying/selling, at what price vs. what volatility do I expect to actually realize, and how will I adjust (hedge) as price, time, and implied volatility change?*

**Working framework to practice:**
- Distinguish **historical/realized volatility** (what the stock actually did), **implied volatility** (what the option price implies it will do), and **your forecast**. Edge, in Natenberg's world, lives only in the gap between implied and your (well-estimated) forecast — not in a hunch about direction alone.
- Know the surface: IV varies by strike (skew — index puts rich because crash insurance is in demand; single-name skew around events) and by expiry (term structure). A calendar, a vertical, a skew trade are all ways of buying the cheap part of the surface and selling the rich part.
- **Delta-hedging / adjustment is the trade, not an afterthought.** A market-maker / volatility trader buys an underpriced option, delta-hedges with stock, and re-hedges as gamma moves delta — “gamma scalping” — harvesting realized movement against the implied paid. For a swing trader the scaled-down version is: plan the adjustment *in advance* (if stock reaches X, I will roll / trim / convert to a spread), do not invent it under stress.
- Respect model limits: Black-Scholes assumes continuous hedging, constant vol, no jumps. Real markets gap, vol jumps, spreads widen. Natenberg's traders survive by sizing for the model's failure, not its elegance.

Source (summary of his framework): https://cpelectronicscorporate.com/fetch.php/papersCollection/qpi2n8/Sheldon_Natenberg_Option_Volatility_And_Pricing.pdf

### 2.2 Lawrence “Larry” McMillan — Structure Encyclopedia + Sentiment from Options Flow

**Book:** *Options as a Strategic Investment* (the encyclopedia of structures and when each fits) and *Profit with Options*; publisher of *The Option Strategist*.

**What to learn from McMillan in two layers:**
1. **Structure fluency:** For any view — bullish/bearish/neutral, high/low vol, fast/slow move — there is a structure whose payoff matches it, and a cheaper/richer way to build it (vertical vs. naked, calendar vs. diagonal, ratio with its extra tail risk understood). Drill: take one stock view each week and write out *five* ways to express it in options, with max loss, breakeven, and which Greek dominates each. That drill *is* McMillan.
2. **Options data as sentiment:** McMillan popularized equity put/call ratios (21-day moving average, and dollar-weighted versions) as contrary sentiment: extremes of put buying mark fear that, coupled with a price confirmation (support holding, index breaking a downtrend), has marked buyable lows; complacent call-chasing extremes warn the other way. His weekly method combines four families — price (SPX chart first), put/call, breadth oscillators, and volatility (VIX trend / term structure) — and requires *price to confirm* before acting on any indicator signal. That hierarchy — indicators propose, price disposes — is the transferable rule.

Sources: https://www.moneyshow.com/articles/optionsidea-29757/ ; http://www.tigersharktrading.com/articles/35427/1/The-McMillan-Options-Strategist-Weekly/Page1.html

### 2.3 Tony Saliba — Defined Risk, Tread Water, Be Ready for the Rare Spectacular Day

The only options trader in the original *Market Wizards*. Schwager's introduction stresses the combination: 70 consecutive months of profits over $100,000 in his telling of Saliba's floor career, built *not* on constant big wins but on “trying to do a little better than treading water day in, day out, while being positioned to take advantage of the rare spectacular trading opportunity” — Teledyne's explosion and the October 1987 crash being his two famous examples.

**Method (from *Market Wizards* and his later book *Managing Expectations*):**
- Trade **spreads** (verticals, butterflies, calendars) — defined-risk combinations — rather than naked options, so a catastrophic adverse move is a known loss, not a margin call.
- Manage the position as a **Greek portfolio**: know your aggregate delta, gamma, vega at all times; adjust (“trade around a core position”) as the underlying and IV move, rather than setting and forgetting.
- Homework is extensive and pre-market: theoretical values for every strike he might trade, so in a fast market he instantly knows what is cheap/rich without calculating.
- **Psychology:** After an early near-blowup on an oversized, unhedged position, he rebuilt with a rule that protection is always on. The Saliba mindset to copy: *consistency is the business; convexity is the bonus. Never trade in a way that a spectacular day for the market becomes a fatal day for you — position so it becomes a spectacular day for you.*

Sources: https://fliphtml5.com/lnym/nxba/JACK_SCHWAGER_-_MARKET_WIZARDS/186/ ; https://www.turtletrader.com/trader-saliba/

### 2.4 Jeff Augen — Volatility Distortions Around Known Calendars

**Book:** *The Volatility Edge in Options Trading*.

Augen's teaching: predictable calendars create predictable *distortions* in IV and spreads, and a prepared trader studies those distortions statistically rather than trading the event story.
- **Earnings IV ramp and crush:** IV rises in a measurable pattern into earnings and collapses after. Augen teaches building your own database — for a given name, how much does IV typically rise in the 10 days before earnings, how large is the typical actual move vs. implied, how do spreads widen — and only then choosing a structure (long premium well before the ramp and out before the event, short premium after, calendars that own the event month and sell the front, etc.).
- **Expiration cycle effects:** Pinning / hedging flows around expiration, weekend and month-end effects on spreads and decay — trade *with* the calendar's mechanics in mind, especially avoiding paying wide weekend spreads for theta you will not collect.
- **Parity / price distortions and VIX as a hedge instrument:** Occasional put-call parity dislocations, and using VIX options (with their futures-based pricing understood — VIX options price off VIX futures, not spot VIX) as portfolio tail insurance, sized as insurance, not as a directional bet.

The durable lesson is methodological: **build the toolset.** Augen wrote software to chart IV histories and price changes; the modern equivalent is a simple spreadsheet/notebook per watchlist name: IV percentile, earnings-date IV behavior, expected move vs. last 8 actual earnings moves. Without that history, every earnings trade is gambling; with it, it becomes a priced decision.

Source: https://www.goodreads.com/book/show/22500759

### 2.5 Nassim Taleb / Mark Spitznagel (Universa) — Convexity and the Barbell

**Books:** *Fooled by Randomness*, *The Black Swan*, *Antifragile*; Spitznagel, *The Dao of Capital* / *Safe Haven*.

**Mental model — convexity:** A payoff is convex if gains accelerate as the move gets bigger and losses are floored. Long, far out-of-the-money options are convex; short naked options are concave (small steady gains, accelerating losses). Taleb's career — profiting enormously on Black Monday 1987 as a floor options trader, then Empirica, then as adviser to Spitznagel's Universa — is organized around owning convexity cheaply and refusing concave payoffs, however seductive their win rate.

**The barbell, as a portfolio construction you can copy at small scale:**
- Most capital in the safest, most liquid assets you can find.
- A small, *budgeted* slice (Universa's client illustration commonly discussed is ~3% of a portfolio allocated to the tail strategy) in deep out-of-the-money puts / convex structures that bleed small premium in calm years.
- Nothing in the fragile middle (leveraged, “moderately risky” concave bets).

Universa's Q1 2020 illustration makes the arithmetic vivid in teaching: a reported +4,144% return for the tail strategy in that quarter meant a portfolio with ~3.3% in Universa and the rest in the S&P 500 could be roughly flat in a quarter the index fell ~12% on that measure — the hedge did not need to be large, it needed to be *convex*. In October 2008 Universa funds returned in the 65–115% range in retellings, and in calm years the strategy bleeds — that bleed is the insurance premium, budgeted in advance, not a surprise.

**Rules for a swing trader using this:** (1) Size tail hedges as an annual insurance budget (e.g., decide you will spend X% per year, accept it as a cost in good years). (2) Buy convexity when it is cheap (low IV percentile, quiet markets), not after a crash when everyone wants it. (3) Never finance convexity by selling other convexity / selling naked tails elsewhere in the portfolio — that cancels the shape you paid for. (4) Judge the hedge over a full cycle, never quarter by quarter.

Sources: https://hub.cissychen.com/investing/antifragile-day25.en.html ; https://yalibnan.com/2020/11/03/nassim-taleb-coronavirus-response-a-case-study-of-govt-incompetence-and-denial/ ; https://en.wikipedia.org/wiki/Nassim_Nicholas_Taleb

### 2.6 The Practitioner Playbook by Strategy — How Each One Is Actually Traded, and When a Master Reaches for It

Think of each row as: *what am I being paid for, what shape do I own, when does a master use it, how is it managed?*

**a) Variance Risk Premium (VRP) — selling insurance others overpay for, on average.**
Implied volatility has, on average across long histories, exceeded subsequent realized volatility — buyers pay up for protection / lottery payoffs. Bakshi & Kapadia (2003) showed it cleanly: delta-hedged long index option portfolios *lost* money on average (more so when vol was high) — the mirror image is that the seller was compensated. Coval & Shumway, and Carr & Wu, reach the same picture from raw returns and variance contracts.
- *How masters trade it:* Systematically, diversified, small, and delta-aware — never as a concentrated naked bet on one name into one event. Structures: cash-secured / fully collateralized index put writing, defined-risk put spreads, iron condors with wings bought, calendars. Size is set for the day vol triples, not for the average day.
- *When:* IV percentile / IV-vs-realized gap is rich, term structure is in contango, no imminent binary event you cannot model.
- *When not:* IV is cheap, a crash is underway and spreads are disorderly, or the position would force you to sell stock holdings at the lows to meet margin — that forced-selling is how a “premium harvesting” book becomes a concave blowup (see Niederhoffer in §5).

Source: https://www.theoptionpremium.com/p/the-variance-risk-premium-the-research-behind-why-selling-options-works

**b) Systematic put-writing (CBOE PUT) and buy-writing / covered calls (CBOE BXM) — the benchmark versions, learned as benchmarks.**
These rules-based indices are the cleanest classroom: PUT sells monthly at-the-money SPX puts, fully collateralized by T-bills; BXM holds the S&P 500 and sells monthly at-the-money calls against it.
- Long-run classroom numbers shift by window, which itself is a lesson — e.g., one long summary: PUT roughly matched the S&P 500's return (~9.5% vs. ~9.8% in that window) at about two-thirds the volatility (~10% vs. ~15%, beta ~0.56) and shallower drawdowns; BXM returned less (~8.5%) at ~11% vol, beta ~0.62. A Cboe-based update over a different window shows BXM ~8.5% since 1986 vs. ~11.2% for the total-return index, max drawdown –35.8% vs. –50.9%.
- *What a master learns from them:* Selling premium is a **risk-shape transformation, not free income** — you trade away the right tail (covered calls) or take on the left tail in a collateralized, sized way (put-writing) in exchange for smoother returns. Put-writing has tended to do better than buy-writing per unit of vol in these benchmarks (about +1.1%/yr PUT over BXM 1986–2015 in Israelov's study — with his elegant warning that put-call parity says much of that gap traces to a few hours of index-construction timing each month, so do not build a religion on it).
- *Practical use for a swing trader:* Covered calls only against stock you are genuinely willing to sell at the strike, in sideways-to-mildly-up, rich-IV conditions, preferably selling *above* a resistance / exhaustion extension (Kell's Stage 5) rather than capping a Stage 2 leader at the start of its run. Cash-secured puts (or put spreads) as a *paid limit order* to own a leader at a lower base — only at a price you wanted to buy the stock anyway, sized as if you will be assigned in a falling market, because sometimes you will.

Sources: https://quantpedia.com/putwrite-vs-buywrite-index-differences/ ; https://www.dividend.com/options-and-income-channel/is-options-upside-becoming-capped/

**c) Dispersion / correlation premium.**
Index IV embeds an implied correlation between constituents that has tended to exceed realized correlation (one practitioner summary of Cboe's DSPX dispersion index puts the long-run gap around ~7 correlation points: implied ~39.5% vs. realized ~32.5%). The trade: sell index volatility, buy a basket of single-name volatility (delta-hedged), profit when stocks move on their own stories rather than in lockstep.
- *For a personal trader,* full dispersion (50 names, delta-hedged daily) is an institutional desk trade — learn the *idea* and use its small-scale cousin: in earnings season, single names move idiosyncratically while the index stays calm — long single-name vol / short index vol in calendar/spread form expresses that, and the reverse (avoid selling single-name earnings vol while buying index protection in a macro panic, when correlations go to 1) is the risk lesson. In a crash, dispersion loses because correlation spikes — position any version for that day.

Sources: https://navnoorbawa.substack.com/p/how-hedge-funds-monetise-options ; https://quantpedia.com/strategies/dispersion-trading

**d) Delta-hedged option returns as a diagnostic.**
Even if you never run a delta-hedged book, use its logic as a lie detector: if you buy an option and hedge away direction in your *analysis* (what happens if the stock goes nowhere? if it moves but IV falls?), what is left is your vol bet. If you cannot state whether that remainder is favorable, you do not yet have an options trade — you have a stock opinion in an expensive wrapper. Buy the stock / a vertical instead, where the shape is clearer.

**e) Earnings-move strategies — trade the implied move, not the headline.**
Classroom procedure (Augen + practitioner data services teach the same routine):
1. Compute the implied earnings move: ATM straddle price ÷ stock price for the expiry just after earnings (mean implied move in academic samples ~5–6%).
2. Compare with the name's last 8–12 *actual* earnings moves (mean and median), and with its IV ramp pattern.
3. **Long straddle/strangle as a blanket earnings bet loses on average** — IV crush is why: e.g., a worked SOFI example, straddle bought at $3.56 with IV 143% was worth $2.40 the next morning despite a ~$1 up-gap, because IV fell to 103% and the move was smaller than the $3.56 priced in. A Market Chameleon MSFT study found the market overestimated the earnings move ~67% of the time over 12 quarters (implied 5.3% vs. actual 4.0%); long straddles lost ~12% per trade on average in that sample, long strangles ~22%, while defined-risk credit iron condors/butterflies centered on the expected range showed positive averages in that same sample.
4. Masters therefore express earnings views *selectively*: (i) buy premium *days before* the event to ride the IV ramp and exit *before* the announcement, (ii) take a directional debit vertical through earnings (defined risk, less vega damage than a naked long option), (iii) sell premium *after* the event when IV is still elevated but the binary is resolved and a new trend / episodic pivot is forming, or (iv) sell a defined-risk iron condor/butterfly *only* when implied >> the name's own historical actual moves *and* you are sized for a 2× expected-move outlier. The blanket rule “always buy/sell earnings vol” is not a master's rule in either direction; the conditional comparison is.

Sources: https://projectoption.com/learn/long-straddle ; https://marketchameleon.com/Instructional-Stock-and-Options-Trading-Videos/442/Microsoft-Earnings-Analysis-A-Deep-Dive-Using-Market-Chameleon ; https://www.mdpi.com/1911-8074/16/5/270

**f) 0DTE and gamma exposure (GEX) — context for intraday risk, a filter for swing traders.**
0DTE SPX options grew from ~5% of SPX option volume in 2016 to ~43% in 2023, ~50% in August 2023 (Cboe figures as summarized in practitioner research). Dealers hedging 0DTE gamma must buy/sell futures intraday: when dealers are net *short* gamma, their hedging amplifies moves (buy rallies, sell dips — Baltussen et al. document the resulting intraday momentum, especially into the last 30 minutes); when net *long* gamma, hedging dampens moves and pins price near large strikes.
- *How a daily-bar swing trader uses this, without becoming a 0DTE gambler:* (1) Treat GEX / 0DTE flow as a **volatility regime filter for the day**: short-gamma days are days a breakout is more likely to follow through intraday *and* days a stop can be run violently — size accordingly. Long-gamma / pinning days are days to expect failed breakouts and mean reversion into the close. (2) Do not hold unhedged short premium through a short-gamma squeeze day. (3) For entries, a swing breakout that is also riding dealer hedging flow (call buying pushing price through a high-gamma strike) has a tailwind — note it in the journal, do not chase it after the flow ends. 0DTE speculation itself, with gamma at its maximum and theta at its most brutal, is a specialist intraday business with defined-risk-only structures, never a substitute for the swing playbook.

Sources: https://cryptodaily.co.uk/2026/08/call-buying-rising-volatility-unusual-rally ; https://volatilitybox.com/research/0dte-options-and-volatility/

**g) The marketing patterns masters avoid (learn to recognize them in your own ideas):**
Selling naked strangles/puts on single names “for income” with no wings, no event check, and size set by premium collected; buying far-OTM weekly calls on a hunch because they are “cheap” (cheap in dollars, rich in IV, expiring worthless most of the time is still expensive); iron condors rolled indefinitely, doubling size to “get back” premium (turning a defined-risk trade into a martingale); earnings straddle buying with no implied-vs-actual comparison. Each violates a master above: Natenberg (no vol edge stated), Saliba (protection always on), Taleb (concave payoff), Tharp (size from risk, not from premium or hope).

---

## 3. Quants and Systematic Legends — The Habit of Writing It Down and Testing It

### 3.1 Ed Thorp — Kelly, Convertible/Warrant Arbitrage, and Statistical Arbitrage

**Books:** *Beat the Dealer* (blackjack), *Beat the Market* (with Sheen Kassouf), memoir *A Man for All Markets*.

**How he thinks:** Find a game where the odds can be *estimated*, bet only when the odds are in your favor, and bet a fraction of capital proportional to the edge — never so much that a losing streak, which *will* come, can ruin you. He learned Kelly's criterion from Claude Shannon at MIT in 1960 (Kelly 1956: bet the fraction that maximizes long-run log growth) and made it operational first at the blackjack table, then in markets.

**His market trades, as methods to study:**
- **Warrant / convertible arbitrage:** Price the warrant/convertible with a model (he built an early options pricing formula before Black-Scholes was published), buy the underpriced security, short the underlying to hedge delta, and earn the mispricing as the two converge — market-neutral, many independent small bets.
- **Statistical arbitrage at Princeton Newport Partners (1969–1988, with Jay Regan):** Hundreds of hedged, independent positions at once, each a small statistical edge, betas/currencies/rates hedged out. In his retelling, the fund compounded at roughly 15–19% a year depending on fee basis quoted (15.8% annualized with ~4.3% standard deviation in one widely cited summary, vs. ~10.1% for the market at ~17.3% vol), positive in 227 of 230 months with only 3 losing months, none worse than ~1% — the *shape* (smooth, hedged, diversified across independent bets) is the teaching point, even more than the level.
- **Index arbitrage / pairs and later systematic strategies** follow the same template: model, hedge the exposures you do not want, diversify across many instances, size by Kelly in *fractional* form.

**Fractional Kelly — the sizing lesson in full (see also §5):**
For a bet with win probability *p*, loss probability *q = 1–p*, and win/loss payoff *b*, full Kelly is *f\* = (bp − q) / b*. Example taught everywhere from Thorp onward: 55% win rate, 1.5:1 payoff → *f\** = 25% of capital at risk per bet — and full Kelly, even when the inputs are *exactly right*, expects a 50% drawdown with ~50% probability at some point (the mathematics: at full Kelly, probability of ever falling to fraction *x* of peak wealth is about *x*). Half-Kelly keeps roughly ~75% of the growth rate at about half the volatility; quarter-Kelly keeps ~44% of growth at a quarter of the volatility. And inputs are *never* exactly right — estimation error alone argues for a fraction (MacLean, Thorp & Ziemba's work formalizes shrinking toward ~2/3 Kelly or less when the edge estimate is noisy, before costs and regime change). Thorp's practice: diversify so no single Kelly bet is the portfolio, err on the side of caution, and treat “bet too much and you will almost certainly be ruined” (his interview title / refrain) as a law.

Sources: https://compoundingmyinterests.com/compounding-the-blog/tag/long+term+capital+management ; https://www.turbinefi.com/blog/position-sizing-risk-management-prediction-markets-2026 ; https://www.fxroboteasy.com/glossary/kelly-criterion

**The Madoff lesson Thorp teaches:** Asked in 1991 to review a portfolio, he checked Madoff's claimed options trades against actual market volume and concluded the trades could not have happened in the size claimed. Quant habit: *reconcile a claim with an independent data source.* Apply it to your own backtests first.

### 3.2 Jim Simons / Renaissance Technologies — Many Tiny Edges, Executed Without Argument

**Book:** Gregory Zuckerman, *The Man Who Solved the Market* — the fullest outside account, built on interviews with former employees.

**What the Medallion operation, as described by Zuckerman and by Simons in rare interviews, actually does:**
- **Short-horizon statistical patterns in liquid instruments**, traded automatically. Early Renaissance worked on currencies/commodities with models from Baum-Welch / hidden Markov ideas (Leonard Baum), then, after Peter Brown and Robert Mercer joined from IBM speech recognition in 1993, equities stat-arb at scale, using their language-modeling mindset: treat price streams as a signal to be predicted probabilistically, with *vast* clean historical data as the training set.
- **Win rate barely above a coin flip:** “We're right 50.75% of the time, but we're 100% right 50.75% of the time. You can make billions that way” — a line attributed to Mercer in Zuckerman's telling. Edge per trade is tiny; the business is *volume × tiny edge × relentless cost control × diversification*.
- **No discretionary override:** Simons, in a 2016 CNBC remark quoted widely: “I have no opinion on any stocks… The computer has its opinions and we slavishly follow them.” Models are debated fiercely *in research*; in production, they are executed.
- **Capacity respected as part of the strategy:** Medallion was closed to outside money in 1993, became employees-only in 2005, capped around ~$10B with profits distributed out — because short-horizon edges decay with size. Its gross/net figures in Zuckerman's account (~66% a year before fees, ~39% after its 5% + 44% fees, 1988–2018, generating over $100B in trading profits) illustrate what happens when tiny edges compound at limited capacity — and why a personal trader should *not* try to copy the trades (you do not have the data, execution, or cost structure) but *should* copy the organization: clean data first, test everything, never trade a pattern you cannot describe, cut strategies that stop working, keep capacity small relative to the edge.
- Renaissance's outside-investor funds (RIEF etc., longer horizon) have had far more ordinary, sometimes difficult years — itself a lesson Simons's colleagues state plainly: horizon and capacity change the product entirely.

Sources: https://winchellhouse.com/2025/08/01/what-is-the-medallion-fund/ ; https://www.readtrung.com/p/jim-simons-and-the-making-of-renaissance ; https://podcastnotes.org/crypto/the-investors-podcast-tip/jim-simons-the-greatest-investor-on-wall-street-gregory-zuckerman-on-the-investors-podcast-ep-273/

**What is *not* the lesson:** There is no secret indicator, no single formula, and no discretionary chart skill at Medallion to imitate. Former employees consistently describe an infrastructure achievement — data cleaning (Simons insisted on pristine, survivorship-free, error-checked data as a founding obsession), research culture (hire brilliant scientists with no finance background, share code, reward signals that work regardless of whose they are), and execution/cost engineering.

### 3.3 David Shaw / D. E. Shaw — Statistical Arbitrage as an Engineering Firm

Shaw, a Columbia computer-science professor recruited to Morgan Stanley's quantitative group, founded D. E. Shaw in 1988 applying parallel computing to relative-value mispricings.

**Method to study:** Equity statistical arbitrage in the Avellaneda-Lee tradition in modern form — model each stock's return as market/factor exposures plus a residual, trade residuals that have stretched and show signs of mean-reverting, hedged for factor exposures, across *thousands* of names so any single residual is noise and the portfolio is the signal. Plus convertible arbitrage, fixed-income relative value, and later a broad multi-strategy platform. Early-firm retellings put the stat-arb book at high-teens average returns with low market correlation in 1988–96, growing to a firm doing ~5% of NYSE volume on busy days by 1996, and a later Institutional Investor account put its equity/equity-linked book at ~24.9% average since July 1988 with ~9.8% vol and ~0.01 correlation to the S&P in that window.

**His 1998 teaching story, as he rebuilt from it:** A large financing arrangement with Bank of America (up to ~$1.6B credit, ~$1.3–1.4B drawn by mid-1998 in SEC-filing-based retellings) funded expanded fixed-income relative-value positions that required stable funding and orderly markets. Russia/LTCM broke both; the operation lost heavily (one detailed retelling: –73% on that capital pool, $372M loss) before recovering. Lesson he institutionalized: *a convergence trade is also a funding and liquidity trade.* For a personal trader the translation is humble and direct: a pairs/spread position that is “right” can still force you out if leverage, margin, or illiquidity decides your exit date. Size spreads for the funding stress, not the model.

Sources: https://navnoorbawa.substack.com/p/de-shaws-1998-crisis-how-a-372-million ; https://www.institutionalinvestor.com/article/2btgiowdmfyg7ib5snvnk/portfolio/come-together-statistical-arbitrage

### 3.4 Cliff Asness / AQR — Factors, Combined, With Humility About Each One

Asness (PhD under Eugene Fama at Chicago, dissertation on momentum) built AQR on a simple, researchable claim: **a few well-understood return drivers — value, momentum, quality/profitability, carry, defensive/low-risk — recur across asset classes and countries, and a diversified combination of them, implemented with cost and risk control, is more robust than any one alone.**

**Learn each factor as Asness's papers teach it:**
- **Value:** Cheap vs. expensive on price-to-fundamentals. Asness & Frazzini (“The Devil in HML's Details”) show construction matters: use *current* prices with lagged book values for a timelier value signal that pairs better with momentum.
- **Momentum (cross-sectional):** Winners of the past ~12 months (skipping the most recent month) tend to keep winning vs. losers — Jegadeesh & Titman (1993), extended across asset classes by Asness, Moskowitz & Pedersen (2013, “Value and Momentum Everywhere”: value and momentum are negatively correlated and each works across stocks, bonds, currencies, commodities — combining them roughly halves drawdowns vs. either alone in their samples).
- **Time-series momentum / trend:** Moskowitz, Ooi & Pedersen (2012): an asset's *own* past 12-month excess return predicts its next month, long if positive, short if negative, across 58 futures/forwards. Hurst, Ooi & Pedersen (“A Century of Evidence on Trend-Following Investing,” extending it to 1880 / 67 markets) found the hypothetical trend program positive in every decade in their backtest (gross ~20% a year, ~14.3% net of a hypothetical 2-and-20, Sharpe ~1.0 net in the 1903–2012 exhibit) — and AQR's own later live trend experience, like everyone's, has been far bumpier, with flat-to-difficult stretches in the 2010s. Both halves are the lesson: trend is a *crisis diversifier and a long-run driver in the data*, and it can still go a decade feeling broken. Position it as one sleeve, vol-targeted (AQR scales positions inversely to recent volatility, targeting constant risk per market), diversified across many markets, and never as a concentrated bet on one asset's trend.
- **Quality:** Profitable, growing, safe, well-managed firms earn a premium (Asness, Frazzini & Pedersen, “Quality Minus Junk”) — for a stock picker, this is the quant version of O'Neil/Minervini's earnings-quality filter.
- **Carry:** Assets with higher yield / roll tend to outperform low-carry assets across classes (Koijen et al. with Asness) — in options language, this is a cousin of harvesting VRP/term premia.

**Asness's temperament lesson:** He writes, publicly and repeatedly, through factor drawdowns (notably value's 2018–20 winter) explaining what the strategy owns, why a drawdown is *consistent with* a risk/behavioral premium rather than proof it vanished, and what would actually change his mind. Copy that: pre-write, for each sleeve you run, *what normal pain looks like* (depth, duration), so in the drawdown you are executing a plan, not having an identity crisis. And note his running debate with Arnott (below) on factor timing: Asness finds timing factors by their own valuations to be weak and mostly just more value exposure — a warning against cleverness layered on simplicity.

Sources: http://finglimpse.blogspot.com/2026/10/cliff-asness-professional-biography-for.html ; https://www.scribd.com/doc/128190136/A-Century-of-Evidence-on-Trend-Following ; https://www.fa-mag.com/news/smart-beta-war-rages-on-26514.html?print

### 3.5 Rob Arnott / Research Affiliates — Rebalancing as an Engine

Arnott's Fundamental Index (RAFI, 2004–05 with Jason Hsu) weights companies by economic footprint — sales, cash flow, dividends, book value — instead of market cap, and rebalances annually back to those weights.

**Mental model to internalize:** Cap-weighting automatically owns *more* of whatever got more expensive. Any price-independent anchor (fundamental weight, equal weight) does the opposite at every rebalance: it systematically trims what ran up and adds to what fell, relative to fundamentals. Arnott argues much of value's long-run payoff *is* that contrarian rebalancing: “the alpha comes from the rebalancing, not [only] from the cheapness of the stocks.” In his interviews: if price = fair value + a mean-reverting error, contra-trading the biggest errors has a structural payoff, and a fundamental anchor overweights stocks in proportion to their discount.

**Practice translation (even if you never buy a RAFI fund):**
- Give your portfolio a *rebalancing rule that contra-trades*: e.g., a core index sleeve rebalanced on a calendar/band rule, so you mechanically sell strength and buy weakness in the core, while your active swing book does the opposite (rides strength) — the two engines diversify each other.
- Be skeptical of any new factor/product whose recent success is mostly its own multiple expanding (Arnott's “smart beta is not very smart if it is performance chasing” warning): ask, *am I being paid for a risk/behavior, or am I just buying what already re-rated?*

Sources: https://informaconnect.com/inside-etfs-europe-qa-with-the-godfather-of-smart-beta/ ; http://ritholtz.com/2018/07/transcript-research-affiliates-rob-arnott/

### 3.6 How Quant Practitioners Think About a Signal's Life — McLean & Pontiff as a Working Habit

R. David McLean & Jeffrey Pontiff (2016, “Does Academic Research Destroy Stock Return Predictability?”) studied 97 published stock-return predictors: returns were ~26% lower out-of-sample (before publication — ordinary overfitting / data-mining correction) and a further ~32% lower after publication (for a combined ~58% decay vs. in-sample in many summaries), with less decay in illiquid, costly-to-arbitrage stocks.

Use this the way a desk uses it, as a *prior and a workflow*, not as a reason to do nothing:
- **Haircut every backtest in your head:** expect a new idea to deliver, live, perhaps half its backtest — size it accordingly until live trades earn it a promotion.
- **Ask why it should persist:** Is there a risk being compensated, a behavioral bias with limits to arbitrage, a structural flow (index, dealer hedging, tax, mandate) forcing the other side? Ideas with a *payer* persist longer than pure patterns.
- **Diversify across independent signals and retire decayed ones:** Harvey et al.'s “factor zoo” warning (hundreds of claimed factors, most failing a higher significance bar around t > 3) becomes a personal rule: require a new signal to work across time periods, across related tickers, and after realistic costs/slippage, before it gets real size.
- Momentum, value, quality and trend have been among the more durable families in replication work — which is why §3.4's combination, position-sized modestly, is a sensible quant core for a personal account, with eyes open about long flat stretches.

Sources: https://alphaarchitect.com/factor-premiums/ ; https://www.etf.com/sections/index-investor-corner/swedroe-factor-persistence-diversification?nopaging=1

---

## 4. Hedge Fund / Macro Greats — Thesis, Liquidity, and Knowing When to Press

Macro masters trade *the same* risk religion as the stock traders, at larger scale and in more liquid instruments, with one addition: they think explicitly about **liquidity and the policy reaction function** — who will be forced to buy/sell, and what a central bank / government will do when its constraints bind.

### 4.1 George Soros — Reflexivity: Prices Change the Fundamentals They Are Supposed to Reflect

**Books:** *The Alchemy of Finance* (his real-time experiment diary — read it for process, position by position, including where he was wrong), *Soros on Soros*.

**Reflexivity, taught as he uses it:**
Participants think about a situation they are also part of. Their biased perceptions move prices; prices, in turn, change the fundamentals (a rising stock lets a company raise cheap capital and *become* stronger; a falling currency raises import prices and debt burdens and *becomes* the crisis). Therefore markets are not a one-way reflection of fundamentals, but a two-way feedback loop that tends to produce *initially self-reinforcing, eventually self-defeating* sequences — boom/bust, not smooth equilibrium.

**How he trades a reflexive sequence:**
1. Identify a *flawed prevailing bias* + an underlying trend it is distorting (e.g., in 1992: the belief Britain could hold the ERM peg at a recession-level interest rate).
2. Take a position that profits if the feedback runs — and recognize the position itself, at Quantum's size, was part of the feedback.
3. Watch for the turning of the loop: when the self-reinforcing process becomes overstretched / the authorities' constraint binds, be ready to exit or reverse. He famously listened to his back pain as a (fallible, personal) signal that a position's character had changed — the transferable version is not mysticism, it is: *notice somatic/emotional alarms as data that your position size may exceed your understanding, and investigate them rather than suppressing them.*
4. **Survival rule, in his formulation:** First, survive. Speculation is about finding asymmetric situations and betting heavily *only* there — Quantum's retold record (roughly +30–32% a year 1969–2000 in most summaries, $1,000 → ~$4 million over that span, with two +100% years) came with years he was flat/defensive when no asymmetry was on offer.

**The 1992 pound trade as a worked example (with Druckenmiller):** Druckenmiller built a ~$1.5B short in sterling through the summer of 1992 on the asymmetry (see §4.2). Soros's contribution, in both men's retellings, was sizing: when the moment ripened in September, Soros urged going *far* larger — the fund's short reached roughly $10B notional — because downside if Britain held the peg was limited to carry / a small move, while the devaluation payoff was large. Britain left the ERM on 16 September 1992; Quantum profited about $1B on the trade in most accounts. Lesson: *asymmetry is a property of the structure (pegged price that can only really break one way), not a prediction of certainty.*

Sources: https://tradersummit.net/george-soros-theory-of-reflexivity/ ; https://globalwealthinsight.com/info/the_investment_odyssey_of_george_soros__strategies,_controversies_and_legacy_en_1753327221.html

### 4.2 Stanley Druckenmiller — Sizing Is 70–80% of the Equation

Duquesne (1981–2010, in his retelling never a down year, ~30% a year over 30 years) and lead portfolio manager of Quantum 1988–2000. He gives interviews freely now (Kirby, Sohn, university talks) — they are a masterclass in themselves.

**His own summary of what Soros taught him, repeated in nearly every interview:** *“It's not whether you're right or wrong that's important, but how much money you make when you're right and how much you lose when you're wrong.”* And: *“Sizing is probably 70 to 80% of the equation.”*

**How that becomes practice:**
- **Concentrate in high conviction, diversify away mediocrity:** “When I've looked at all the investors that have very large reputations — Buffett, Icahn, Soros — they all only have one thing in common… it is to make large concentrated bets where they have a lot of conviction. They're not buying 35 or 40 names.” And, quoting Twain approvingly: put your eggs in one basket and *watch the basket very carefully*. Concentration *with attention and a stop* is, in his framing, less risky than 40 names you cannot follow.
- **Liquidity first:** His mentor in Pittsburgh taught him: do not invest in the present; ask what will make people think *differently in 18–24 months*, and above all, **liquidity — central-bank policy and credit creation — moves markets more than earnings in the short-to-medium run.** His macro dashboard is earnings/valuation *conditioned on* the liquidity trend. If liquidity is tightening into weakness, he wants to be short / in cash even if valuations look cheap, and vice versa.
- **Trade your streak honestly:** “I believe in streaks. Sometimes you're seeing the ball, sometimes you're not, and one of my number one jobs is to know when I'm hot and when I'm not. When I'm hot, I need to turn the dial straight up. When you're cold, the last thing you should do is make big bets to get even — you need to turn yourself down.”
- **Asymmetric construction, worked:** His 1992 pound scenarios, as he laid them out: hold the peg → lose only carry (~3% worst case in his framing); adjust within ERM → +5–10% on the currency; fail to defend → +10–20%; panic → more. He took the trade *because the scenario table was lopsided*, before he knew the timing. Build that table, in writing, for every macro-sized position: four scenarios, price and P&L for each, and the exit if scenario 1 starts happening.
- **Cut and reverse without ego:** Druckenmiller's famous errors are part of his teaching — buying tech in early 2000 after arguing it was a bubble, losing heavily in weeks, because emotion (watching younger managers make money) overrode analysis. His rule drawn from it: if you did a trade for emotional reasons, exit it when you recognize that, do not dress it up as a thesis.

Sources: https://www.longriverinv.com/thought/druckenmiller-at-sohn-2022 ; https://github.com/upmkike/sanfi-data-science-ia-finanzas/blob/HEAD/dia6/03_druckenmiller.md ; https://inteliview.kr/en/insights/stories/stanley-druckenmiller-black-wednesday-1992

### 4.3 Paul Tudor Jones — Play Great Defense; 5:1 or Pass

Tudor Investment Corp., famous for calling / profiting from the October 1987 crash (his fund returned ~62% that year in most retellings, ~125%+ for 1987 overall in some accounts, by combining Elliott-wave / historical analog work on 1929 with disciplined intraday risk cutoffs as the crash unfolded).

**Rules he states in *Market Wizards* and in the 1987 “Trader” documentary, and repeats decades later:**
- *“The most important rule of trading is to play great defense, not great offense.”* And: *“Don't focus on making money; focus on protecting what you have.”*
- **5:1 minimum:** “I'm looking for 5:1 [reward:risk]. Five to one means I'm risking one dollar to make five. What five to one does is allow you to have a hit ratio of 20%. I can actually be a complete imbecile… wrong 80% of the time, and I'm still not going to lose.”
- **~1% risk per idea** in practitioner summaries of his practice, mental stops + time stops + price stops, reduced size when losing (“when I'm trading badly, I cut size; my size is constantly inversely proportional to how badly I'm doing” is the spirit of his *Market Wizards* account).
- **200-day MA as a life line:** He uses it across markets as a regime filter — be long above it, defensive / short below it.
- **“Every day I assume every position I have is wrong.”** Know the invalidation before the open, each day, afresh.
- **Never average losers:** the line associated with Jones (and with his mentor Eli Tullis's cotton-trading world) — losers average losers.
- **Tape response > news:** How a market responds to good/bad news tells you its internal health (a market that cannot rally on good news is shortable; one that will not fall on bad news is buyable) — Livermore's lesson, in macro form.

Sources: https://www.geckomode.ai/blog/paul-tudor-jones-risk-management ; https://forexmentoronline.com/8-paul-tudor-jones-quotes-that-will-change-your-trading/

### 4.4 Bruce Kovner — Undertrade, Undertrade, Undertrade

Caxton Associates (founded 1983). *Market Wizards* interview is the risk chapter to memorize.

**In his words:**
- *“Risk management is the most important thing to be well understood. Undertrade, undertrade, undertrade is my second piece of advice. Whatever you think your position ought to be, cut it at least in half.”*
- *“My experience with novice traders is that they trade three to five times too big. They are taking 5 to 10 percent risks on a trade when they should be taking 1 to 2 percent risks.”*
- *“Whenever I enter a position, I have a predetermined stop. That is the only way I can sleep. I know where I'm getting out before I get in. The position size on a trade is determined by the stop, and the stop is determined on a technical basis.”*
- **Correlation is position size:** *“If you have eight highly correlated positions, then you are really trading one position that is eight times as large.”* Evaluate risk at the portfolio level, always.
- **First rule:** Do not get caught in a situation where you can lose a great deal of money for reasons you do not understand.
- Fundamentals give the *why*, technicals give the *when* and the stop — he likened ignoring technicals to a doctor refusing to take a temperature. Imagine multiple scenarios for how a market could unfold and pre-plan responses (his “market future history” exercise) rather than anchoring on one forecast.
- If his emotional balance was disturbed by a position, he closed it — a position you cannot think clearly about is too big, by definition.

Source: http://www.turtletrader.com/trader-kovner/

### 4.5 Michael Steinhardt — Variant Perception and Intellectual Honesty on a Clock

Steinhardt Partners (1967–1995, ~24% a year net over 28 years in most retellings). Memoir: *No Bull*.

**His central concept: variant perception.** To earn excess return you must hold a well-founded view that is *different from consensus*, and be able to state, crisply: what consensus believes, what you believe instead, why you are right, and what timeframe will prove it. If you cannot state all four, you own a consensus position at active risk — cut it.

**Operating habits:** Trade actively around positions (he was far more trading-oriented than a buy-and-hold value manager — taking profits, re-establishing, shorting aggressively); demand that analysts defend a variant view under hostile questioning each morning; cut positions that are not working on their stated clock — a variant perception with no catalyst date is a hope. His difficult final years and his decision to close in 1995 and return capital are part of his own teaching about knowing when your style / energy no longer fits the market in front of you.

### 4.6 Julian Robertson — Long the Best, Short the Worst, and Avoid Big Losses

Tiger Management (1980–2000): started with $8.8M, grew to ~$21B at peak, compounding at 31.7% a year after fees over the life in his March 2000 closing letter to partners (vs. ~12.7% for the S&P 500 over the same span in that letter).

**Method:** Fundamental, research-intensive long/short equity, global in scope: own the 50 best companies you can find (strong management, durable competitive position, reasonable price) and short the 50 worst (broken models, bad management, overvalued on fading fundamentals). In his famous formulation: *“If the 50 best stocks you can find do not outperform the 50 worst, you should be in another business.”*

**Risk and character lessons from Tiger's arc, as Robertson himself framed the close:** “Avoid big losses. That's the way to really make money over the years.” Tiger stumbled badly from August 1998 (yen short losses, then being early — and heavily — against technology stocks it viewed as priced on “mouse clicks over fundamentals”), investors withdrew ~$7.7B, and Robertson chose to close in March 2000 rather than change the discipline — weeks before the Nasdaq peak vindicated much of the view, too late for a fund whose investors had left. For a learner the twin lessons are: (1) being right about value does not set the timing — position size and investor / margin staying power do; (2) a process you trust is worth protecting by *reducing* size in a hostile regime, rather than either doubling down or abandoning the process entirely. His other great legacy is people: the “Tiger Cubs” (Coleman, Laffont, Ainslie, Halvorsen, Mandel and others) were trained in his morning-meeting culture of defending fundamental theses and sizing by conviction *within* a risk budget.

Sources: https://aletteraday.substack.com/p/letter-78-julian-robertson-2000 ; https://www.daytrading.com/julian-robertson

### 4.7 Louis Bacon — Top-Down, Rates-Driven, Cut in Days

Moore Capital (founded 1989/90). Bacon is private; what is known comes from investor letters summarized in profiles, *More Money Than God* (Mallaby), and rare interviews.

**Method as described across those sources:** Top-down, interest-rate-driven macro — form a view on the policy/rate cycle in the US and Europe, express it in the most liquid rates, currency, equity-index and commodity instruments, trade *around* the theme actively (in and out as short-term price action confirms or contradicts), and **close losing trades after only a few days** if the market does not confirm. Moore compounded at roughly ~19% a year 1989–2012 in MoneyWeek's summary (with a severe 1994 reversal that saw large redemptions — again, survival and rebuilding are part of the record he learned from), at relatively low volatility for a macro fund — that smoothness *was* the product, achieved by cutting quickly rather than by being right more often.

**His shop lesson:** “We run a laissez-faire, entrepreneurial shop… we prefer to see what our traders want to have as their individual risk profiles, and then we fit our assets around those” — i.e., risk budgets are set per trader/style first, portfolio exposure is built around them, not imposed by gross notional. For a personal trader running multiple playbooks (swing stocks, options premium, trend sleeve), copy the structure: give each playbook its own risk budget and stop, and judge the portfolio by the *combination*, not by whichever sleeve is loudest today.

Sources: https://moneyweek.com/471075/the-worlds-greatest-investors-louis-bacon ; https://www.daytrading.com/louis-bacon ; https://triinv.substack.com/p/trader-profile-louis-bacon

---

## 5. Risk, Sizing, and Psychology — The Common Operating System

If you learn only one section, learn this one. Schwager's interviewees disagree about almost everything else; on this section they speak in one voice.

### 5.1 The Schwager Corpus, Distilled (*Market Wizards*, *The New Market Wizards*, *Stock Market Wizards*, *Hedge Fund Market Wizards*, *Unknown Market Wizards*)

Schwager himself, asked across decades what his interviewees share, gives the same answer the summaries of his books give:
1. **A method that fits the person.** Every wizard has an edge, but the edges are incompatible with each other (trend vs. mean reversion, discretionary vs. systematic, concentrated vs. diversified). What is universal is *fit*: they found / built a method matching their temperament and then did not abandon it in drawdowns.
2. **Risk control is religious.** Predetermined stops, sizing by risk, no single trade can hurt them badly. Many attribute success *primarily* to money management, not entry skill.
3. **Cut losses, let winners run** — the payoff distribution is asymmetric by design, in every style.
4. **Discipline and patience:** Wait for your setup; trading is mostly waiting. Overtrading is the universal amateur error.
5. **Independence:** They do their own work, ignore tips and consensus noise, and take full responsibility — no wizard blames the market, a broker, or another trader for a loss.
6. **They love the game and do enormous homework,** and they review losses as tuition: Schwager's traders almost all describe early blowups / long losing apprenticeships that taught the risk rules in §5.2–5.4 in the only way that sticks.

Sources: https://cmigo.com/default.aspx/threads/s8yUo3/Market-Wizards-By-Jack-Schwager.pdf

### 5.2 Van Tharp — R, Expectancy, and Position Sizing™ as the System

Psychologist and coach (interviewed by Schwager on trading psychology), author of *Trade Your Way to Financial Freedom* and *The Definitive Guide to Position Sizing*.

**Learn his language; it makes every other master's sizing talk precise:**
- **R = initial risk per trade** = (entry − stop) × position size, in dollars, decided *before* entry.
- Every result is recorded as an **R-multiple**: risk $200, make $500 → +2.5R; lose the planned $200 → –1R. A loss larger than –1R means a *mistake* (moved stop, oversize, gap — investigate which), regardless of the dollar amount.
- **Expectancy = average R per trade** over a sample (minimum ~30 trades to say anything, 100–200 for a clear picture). Example from his teaching literature: 6 losers at –1R, winners of +0.5, +2, +3, +5R → only 40% winners, yet total +4.5R, expectancy +0.45R/trade. Add one –3R mistake and expectancy falls to +0.25R — *your system expectancy minus the cost of your mistakes is what you actually trade.*
- **Opportunity factor:** Expectancy × frequency. A +1.0R system with 50 trades/year makes less than a +0.2R system with 500 trades/year — do not fetishize either number alone.
- **SQN (System Quality Number)** = (expectancy ÷ standard deviation of R) × √N — a compact way to compare systems and to know how aggressively they can be sized.
- **His marble-game demonstration:** Give 100 people the *same* sequence of trades (same entries/exits) and let each choose only position size. Typically about a third go bankrupt, a third lose, a third make a lot — with final equities from zero to over a million. *“Position sizing is more important than you think” is an understatement in his work: sizing is the variable that decides whether a positive-expectancy system compounds or dies.*
- **Sizing algorithms to know by name and use deliberately:** Percent-risk (fixed-fractional: risk X% per trade — the swing masters' method), percent-volatility (size inversely to ATR so each position contributes equal dollar vol), fixed-ratio, and Kelly/optimal-f in fractional form (§3.1). Choose one, write it down, and change it only in a scheduled review — never mid-drawdown, never mid-euphoria.

Sources: https://tradermarkus.com/van-k-tharp-trade-your-way-to-financial-freedom-review/ ; https://www.theoptionpremium.com/p/van-tharp-position-sizing-options-trading ; https://layer0firewall.com/blog/van-tharp-trading-psychology

**Worked sizing example (memorize the arithmetic):** Account $50,000, risk budget 0.75% = $375 per trade (1R). Stock entry $80, stop $76 (5% stop, ≈ within 1× ADR for a typical leader). Shares = $375 ÷ $4 = 93 shares ≈ $7,440 position (14.9% of account). If instead the stop had to be $72 (10%), the same 1R buys only 46 shares — *wide stop = small position, automatically.* For an options spread: 5-point-wide credit spread collecting $1.20 has max loss $3.80/share = $380/contract = ~1R at this budget, so the position is 1 contract — known before the order screen opens. That pre-computation, every time, is Tharp in practice.

### 5.3 Fractional Kelly in One Page (Thorp's Gift, Used Conservatively)

- Full Kelly maximizes log growth *if* you know the true odds. You do not.
- Full Kelly *expects* deep drawdowns (50% drawdown is a ~50% event, not a tail event, at full Kelly).
- Half-Kelly: ~75% of the growth, far smaller drawdowns. Quarter-Kelly: ~44% of the growth, roughly a quarter of the volatility.
- Practical translation used by systematic traders: Compute a rough Kelly from your *live* R-distribution (not a backtest fantasy), take **one-quarter to one-half of it as a ceiling**, then take the *smaller* of that ceiling and your fixed-fractional risk budget (0.5–1% per trade for a swing book). If the two disagree wildly, your R-sample is too small or your edge estimate is too optimistic — trust the smaller number.
- Never use Kelly to size a *single discretionary idea* (“high conviction = Kelly says 25%”). Kelly is a portfolio concept for repeated, estimated-similar bets. Druckenmiller-style concentration (§4.2) is a different, judgment-based practice, bounded by liquidity, scenario tables, and a stop — do not confuse the two and call concentration “Kelly.”

### 5.4 Drawdown Control — The Rules the Greats Actually State

Collect them as a single policy (this exact composite is the playbook in §7):
- **Per trade:** 0.5–1% risk (Qullamaggie, Minervini-style practice, Kovner's 1–2% ceiling for novices scaled down). No exceptions for “best idea ever.”
- **Per day / week:** Stop initiating new risk after –2R in a day or –4–5R in a week (Schwartz / prop-desk style circuit breakers in spirit). Review before re-engaging.
- **Portfolio heat:** Sum of open 1R risks + correlated exposure. Kovner's rule: correlated positions count as one big position. Cap total open heat at ~5–6% of account for a swing book (e.g., 6 positions × ~0.85% average), less in a Stage 4 / short-gamma market.
- **Drawdown ladder (Druckenmiller / Tudor Jones behavior, formalized):** At –5% from equity peak, cut gross size by ~25%. At –10%, cut by half and trade only A+ setups. At –15%, stop, do a full journal review, restart at minimum size only after the review identifies what changed (market regime? playbook drift? sizing drift?). *Never increase size to “get back” a drawdown — every blowup story below contains that sentence in some form.*
- **Gap / event risk:** Size overnight positions for a gap *through* the stop (earnings, macro prints). If a gap of 2× your stop distance would cost more than ~2R, the position is too big or needs an options hedge / defined-risk structure instead of stock.

### 5.5 Blowups as Teaching Stories — How the Greats Themselves Tell Them

The masters assign these stories the way medical schools assign case studies — study the mechanism until you can recognize it in yourself early.

- **LTCM (1998):** Brilliant convergence traders (Meriwether, Merton, Scholes) running relative-value spreads at ~25:1+ leverage on balance sheet, far more via derivatives. Spreads that “could not” widen much did, correlations of supposedly independent trades went to 1 in the Russia-crisis liquidity flight, positions were too large to exit, and funding decided the exit — a Fed-organized $3.6B private bailout unwound the fund, investors losing over 90%. Thorp's diagnosis (he declined to invest): it was “anti-Kelly” — levering up to “pick up nickels in front of a bulldozer,” with partners who, in his words, thought Kelly made no sense, and a culture of doubling into holes (martingale behavior). Mechanisms to watch in yourself: small edge × huge leverage, diversification that vanishes in stress, illiquidity disguised as safety.
  Source: https://www.quantt.co.uk/resources/long-term-capital-management-collapse
- **Victor Niederhoffer:** A brilliant statistical trader who blew up twice — 1997 (leveraged Thai equities + short S&P puts into the Asian crisis / October selloff; margin forced liquidation just before a rebound he would have survived unleveraged) and 2007 (Matador fund down >75% and closed, again with short-volatility / leveraged exposures into stress). Lessons his peers and later profiles draw, and that Ritholtz's summary phrases best: *“Being right is a luxury good. Solvency is a necessity… Your risk tolerance is irrelevant; your clearing broker's is the one that counts… Make a nickel ninety-five times and lose ten bucks once, and Sharpe will call you Warren Buffett right up until the ambulance arrives.”* Short premium with leverage is a concave business (Taleb's language) — its smooth years are the *measurement of hidden risk*, not proof of safety.
  Sources: https://ritholtz.com/2026/09/lessons-victor-niederhoffer/ ; https://www.ebc.com/forex/victor-niederhoffer-trading-losses
- **Livermore (again, deliberately):** The same man who *wrote* “never let a loss run” lost fortunes by breaking his own rules under tip influence, overtrading, and personal distress. The lesson is not hypocrisy — it is that *knowing* the rules is not a control. Controls are structural: stops placed in the market, size limits in the order system, capital segregated, a rule to stop trading when life / emotional state is impaired (Kovner closing positions when his balance was disturbed; Schwartz taking days off after big wins *and* losses).
- **Archegos / Amaranth-type patterns (the modern retellings traders study):** Concentrated, leveraged, opaque exposure becoming a large share of a market's float / open interest, so exit is no longer available at any reasonable price. Personal-scale version: a position that is >30% of your account in an illiquid name *is* that pattern, at your scale. Respect Qullamaggie's 30% overnight cap and Minervini's liquidity preference as hard constraints, not guidelines.

### 5.6 Psychology, Journaling, and Review — The Daily Practice of the Greats

- **Journal in R, with screenshots, same day.** Fields every master who teaches journaling converges on: date, setup name (from your playbook — if it has no name, it was not a playbook trade, log it as such), entry/stop/target and *reason*, size and 1R in dollars, market regime that day (Stage, breadth, index vs. 50/200-day), options context if relevant (IV percentile, GEX regime, earnings proximity), exit and R result, and two grades: *outcome* (R) and *execution* (did I follow the plan? A / B / C). Minervini, Tharp, and Schwartz all teach grading execution separately from outcome — a winning rule-break is a bad trade, a losing rule-follow is a good one.
- **Weekly review (1–2 hours, scheduled):** Compute expectancy by setup, win rate, average win/loss in R, largest loss and whether it exceeded 1R and why, heat/drawdown vs. the ladder in §5.4. Identify the *one* most expensive mistake of the week. That mistake becomes next week's single focus rule.
- **Monthly / quarterly review:** expectancy by regime (did the breakout playbook only work in Stage 2? — then add a regime gate, do not “fix” the setup), options P&L decomposed into directional / vol / theta components, factor/trend sleeve vs. its pre-written “normal pain” expectation (§3.4), and a sizing review: is live R-distribution still supporting current risk %?
- **Pre-mortem and contingency rehearsal (Minervini / Kovner):** Before the open, write what you will do if: your biggest position gaps –8%, the index breaks its 50-day on volume, IV doubles. Deciding in calm is the whole trick — “a decision made in advance doesn't have to be made in the heat of the moment, which is exactly when rules tend to disappear” (Tharp teaching summary).
- **State management:** Schwartz (smaller after big wins, days off), Druckenmiller (turn the dial down when cold, up when hot — *within* the risk ladder, never through it), Tudor Jones (assume you are wrong today), Kell (six flat years — build a life / income structure that lets you survive the apprenticeship without needing this month's trading to pay rent, because need is a sizing distortion).

---

## 6. Where the Greats Disagree — and How to Hold the Disagreement Productively

Disagreement between masters is not a problem to solve; it maps the *dimensions* along which you must make a personal, written choice.

| Dimension | One pole | Other pole | How a swing/options trader resolves it |
|---|---|---|---|
| Concentration | Druckenmiller / Soros / Robertson: concentrate in conviction, 5–12 names, press hard | Thorp / Simons / Shaw: diversify across hundreds of independent small bets | Concentrate *within* the discretionary swing book (5–10 names, §1), diversify *across playbooks* (swing + premium + trend/factor sleeve are independent engines) |
| Averaging / re-entry | Livermore / Tudor Jones: never average a loser, ever | Arnott / value rebalancers: systematically buy what fell vs. fundamentals | Never average a loser *inside a momentum trade*. Rebalancing a core allocation on a calendar rule is a different portfolio, with its own money — never let the rebalancer's logic excuse a broken swing trade |
| Fundamentals | O'Neil / Minervini / Robertson: earnings & quality are essential filters | Zanger / Darvas (late) / Kell: price and volume alone are enough | Use fundamentals as a *filter* (accelerating earnings/sales, quality) and price/volume as the *trigger*. Either alone is half of Livermore's heirs' method |
| Prediction | Soros / Druckenmiller: form a macro scenario, position for it | Simons / Thorp: no opinions, only estimated odds and models | Macro = scenarios + liquidity regime (a *context and sizing* input for swing trades), never a reason to override a stop or a Stage signal |
| Factor timing | Arnott: valuations can warn when a factor is crowded/expensive | Asness: timing factors is weak, mostly disguised value | Do not time factors tactically. Do use crowding/valuation as a *risk* flag to trim a sleeve that has re-rated enormously |
| Selling premium | VRP harvesters: sell rich insurance systematically | Taleb: own convexity, refuse concave payoffs | Sell premium only defined-risk, sized for a crash, *and* own a small convex tail sleeve — the two are a barbell together, either alone is half a philosophy |
| Stops | Discretionary masters: hard / mental stops at technical invalidation, honored intraday | Weinstein / systematic trend: weekly-close confirmation to avoid whipsaw | Stock swing trades: invalidation is a *daily close / intraday break of the pivot low* per Qullamaggie/Minervini practice — pick one per setup in writing. Portfolio sleeves: weekly/monthly rules. Mixing them mid-trade is the error |

---

## 7. Synthesis — One Combined Operating Style for a Modern US Equities + Equity-Options Swing Trader (Daily Bars, With Options Flow, GEX, Breadth, and Short-Volume Data)

### 7.1 The Combined Style, in One Paragraph

Trade like a Minervini/Qullamaggie/Kell stock picker (Stage 2 leaders, VCP / breakout / episodic pivot / Cycle-of-Price setups, pivot entries, small defined losses), size like Tharp/Kovner (fixed-fractional R, portfolio heat, undertrade), think about regimes like Weinstein/Druckenmiller/Tudor Jones (market Stage, liquidity/breadth, 200-day line — press in good regimes, defend in bad ones), express trades in options like Natenberg/Saliba (choose the structure whose vol/theta/gamma shape matches the view; defined risk by default; buy premium when vol is cheap and a catalyst is real, sell premium when vol is rich and the structure is winged), keep a small Taleb tail sleeve and a small systematic sleeve (trend/factor, Arnott-rebalanced core) so the portfolio is not one bet in three costumes, and run the whole thing on a Tharp/Schwager review cadence. Options flow, GEX, breadth, and short-volume data are *regime and confirmation inputs* in this style — they change size and structure choice, they do not replace the stock setup.

**How the modern data fits each master's language:**
- **Breadth** (advance/decline, % above 50-day, new highs/lows) = McMillan's breadth oscillators + O'Neil's M, quantified. Expanding breadth + follow-through = press swing longs. Narrowing breadth (index up, % above 50-day falling, new lows expanding) = distribution in O'Neil's language — reduce heat, tighten stops, favor defined-risk options over stock.
- **Options flow** (unusual call/put activity, put/call extremes) = McMillan's sentiment + Zanger's “pressure factor” in derivative form. Use it to *confirm* a leader (persistent call buying / put selling under a VCP breakout) or to flag complacency/fear extremes — never as a standalone entry (“someone bought calls” is not a setup).
- **GEX / 0DTE positioning** (§2.6f) = a daily volatility-regime note in the journal: long-gamma = expect pinning / failed breakouts (favor selling defined-risk premium, be patient with entries); short-gamma = expect follow-through and air pockets (favor breakout continuation, wider intraday ranges, smaller size per unit of conviction).
- **Short volume / short interest** = fuel + risk data. High short interest in a leader breaking out on an episodic pivot = potential squeeze fuel (and a reason an EP can run). High short volume *into* a failing breakout, or a heavily shorted illiquid name you are long, = gap risk — size down, prefer spreads. Never short a parabolic name *only* because short interest / borrow looks crowded — Qullamaggie's parabolic short requires the price trigger (first lower high / break of prior low), not the statistic.

### 7.2 The Playbook — Only These Setups, Each With a Written Card

Keep five stock setups and four options expressions. Every trade must name one.

**Stock setups (daily bars):**
1. **VCP Breakout (Minervini):** Trend Template pass, earnings/sales acceleration, VCP contractions, pivot entry on volume, stop < pivot low (target ≤5–7% risk on price, ≤1× ADR), sell 1/3–1/2 into +2–3R / 3–5 day strength, trail rest on 10/20-day.
2. **Breakout Continuation (Qullamaggie):** Prior +30–100% move, 2–8 week tight consolidation surfing 10/20-day, ORH entry, stop = day's low ≤1× ADR, same two-stage exit.
3. **Episodic Pivot (Qullamaggie/Bonde):** Neglected name, 10%+ gap on surprise, huge early volume, ORH entry day one, stop = day's low ≤1× ADR, partial into strength, trail.
4. **Cycle Continuation (Kell):** Wedge Pop (early, smaller size) → EMA Crossback (standard size) → Base 'n Break (add), with Exhaustion Extension = trim signal and Wedge Drop = exit signal for all Kell positions.
5. **Stage 2 Pullback (Weinstein/Minervini/Ryan):** Leader in confirmed Stage 2 pulls back to rising 20/50-day or to a prior breakout level on *contracting* volume, then turns up through a small pivot. Stop below the pullback low. This is the lowest-risk add-on / second entry, and the main setup in choppy-but-uptrending markets.

**Options expressions (choose by vol regime, §7.4):**
A. **Debit vertical** (bull call / bear put spread) — default directional expression through earnings or in low-to-normal IV.
B. **Long call/put or long straddle** — only when IV percentile is low, a dated catalyst exists, and implied move < your expected move for a stated reason (EP-type surprise potential). Size as a lottery with a budget, exit before the event unless the event *is* the thesis (Augen).
C. **Credit vertical / iron condor with bought wings** — when IV is rich (high percentile, IV >> recent realized), no binary event inside the trade's life, and price is in a defined range / at exhaustion. Profit target 50–75% of max credit, stop at ~2× credit or at technical invalidation, whichever first (Tharp-style management turns a near-zero raw expectancy defined-risk premium trade into a managed one — pre-write the targets).
D. **Cash-secured put / put spread as a paid entry** — only at a base price you have pre-committed to owning the stock, in size you would accept assignment on, in a Stage 1→2 name.

### 7.3 Daily and Weekly Operating Playbook

**Night before / pre-market (45–60 min — Darvas/Zanger/Minervini homework):**
1. Regime note (5 lines, in journal): Index Stage + vs. 50/200-day, breadth (net new highs, % above 50-day trend), distribution/follow-through count (O'Neil's M), VIX level + term structure, GEX regime for today, any macro print / earnings cluster that changes sizing.
2. Scan: Trend Template / Stage 2 screen → earnings-acceleration filter → tonight's candidates must match a §7.2 setup card. Build a focused list (5–15 names) with pivot, stop, 1R shares, and alert levels written for each. Qullamaggie's top-performer lists (1/3/6-month leaders) + Ryan's historical-model eye are the scan's second pass.
3. Earnings/flow pass: For each candidate, note earnings date (no new naked stock risk into earnings unless the setup *is* an EP / you have de-risked — Minervini-style practice is to trim into earnings unless profit cushion allows holding), IV percentile and expected move if options are contemplated, notable flow / short-interest flags.
4. Position review: For every open position, re-state today's invalidation (“assume it is wrong” — Tudor Jones) and whether trailing stops / profit targets need moving *up* (never down).

**Intraday (minimal — you trade daily bars):**
- Act only on alerts at pre-written pivots/stops. ORH entries for breakouts/EPs in the first hour; otherwise, entries near the close based on daily confirmation.
- No new setups invented intraday. If it was not on last night's list with a pivot and a stop, it is tomorrow's homework, not today's trade (exception: a genuine EP gap that meets all six rules — that setup is *defined* as a same-day trade, with its own card).
- Honor stops in the market, not in your head, for stock; for defined-risk spreads, honor the pre-written price/technical stop.

**Close (20 min):** Log every fill in R, screenshot every open position chart, update heat and drawdown-ladder status, write tomorrow's regime line if it changed.

**Weekly (1–2 hours, e.g., Saturday — Weinstein/Minervini review):**
- Weekly charts first: Re-stage every holding and every watchlist name (Stage 1–4). Sell list comes from Stage breaks, not from daily noise.
- Statistics: expectancy by setup, execution grades, largest mistake, heat/drawdown review (§5.6).
- Options book: decompose P&L (direction / vol / theta), check every short-premium position against its profit/stop targets, roll/close on schedule — never “extend and pretend.”
- Sleeve check: trend/factor sleeve and core rebalance bands; tail-hedge budget spent vs. planned for the year.
- Plan next week: earnings calendar for holdings/candidates, macro calendar, and the *one* focus rule from this week's most expensive mistake.

**Monthly:** Full R-distribution review, sizing recalibration (§5.3), playbook pruning (a setup with negative expectancy over 30+ trades in its correct regime is benched for study, not traded smaller forever), and a one-page letter to yourself — Druckenmiller/Asness style — stating what you own, why, what normal pain looks like, and what would change your mind.

### 7.4 When to Buy Premium vs. Sell Premium — The Decision Table the Masters Converge On

| Condition | Buy premium (long options / debit spreads) | Sell premium (credit spreads / condors, winged) |
|---|---|---|
| IV percentile (own history, 1 yr) | Low (<~30th) — options are cheap | High (>~60–70th) — insurance is rich |
| IV vs. recent realized vol | IV ≤ realized / expected catalyst move | IV >> realized, no catalyst pending |
| Catalyst | Dated, real, underpriced move potential (EP, FDA, earnings with implied < historical actual) | Binary already resolved, or no event in trade life |
| Price location | At a pivot / start of Stage 2 move (need convexity + delta) | At exhaustion extension, in a range, or at a base you want to own (put selling) |
| GEX / flow regime | Short-gamma / trending day favors long gamma follow-through | Long-gamma / pinning regime favors range premium |
| Structure default | Debit vertical first; naked long only with a theta budget and exit date | Always winged; size for a 2–3σ day, profit/stop targets pre-written |
| Timeframe | Days to a few weeks around the move | 20–45 DTE typical for swing premium, out well before expiry gamma explodes |

If neither column is clearly satisfied, the master's answer is *no options trade* — own the stock, own a vertical, or own nothing. Most days, for most setups, a debit vertical or plain stock is the cleanest expression; premium selling is a *regime* business, not a daily habit.

### 7.5 Risk Limits — One Page, Posted Above the Desk

- Risk per trade: **0.5%** standard, **0.75%** for A+ (all filters + regime confirming), **0.25%** for Wedge Pops, parabolic shorts, and any trade in a deteriorating regime. Absolute ceiling 1%.
- Total open heat: **≤5%** in a confirmed Stage 2 market with healthy breadth; **≤3%** in a transitional market; **≤1.5% / mostly cash** in Stage 4 or after a breadth thrust fails.
- Single-name cap: 20% of account at cost, 30% only as a *winner that grew there* with a trailing stop protecting at least breakeven (Qullamaggie's overnight cap, Minervini's concentration-with-protection).
- Options: Defined-risk by default. Aggregate max loss on all short-premium structures ≤3% of account. Long premium budget ≤1% at risk at any time (plus the separate annual tail-hedge budget, ~1–2% of portfolio per year spent deliberately, §2.5). No naked short options on single names. No position whose margin requirement can expand to force liquidation of other positions.
- Drawdown ladder: –5% → gross × 0.75. –10% → gross × 0.5, A+ only. –15% → stop, full review, restart small. (§5.4)
- Earnings: No new position within 3 sessions of earnings unless it is an EP or a defined-risk options structure sized as a full-loss-possible trade. Existing stock positions are trimmed to a size whose –2× expected-move gap costs ≤2R.
- Liquidity: Trade only names / options series where your full stop exit costs a small fraction of daily volume / open interest, with spreads tight enough that round-trip cost is a small fraction of 1R. If you cannot exit, you cannot size it — Kovner's first rule.

### 7.6 Record-Keeping Standard

One row per trade, one chart per trade, no exceptions — this database *is* your Simons/Thorp edge at personal scale:
`date | ticker | setup card | regime (Stage/breadth/GEX) | entry | stop | target(s) | shares/contracts & structure | 1R $ | IV%ile & expected move (options) | earnings date | exit(s) | R result | execution grade | screenshot link | one-line lesson`
Review queries you must be able to run at any review: expectancy by setup, by regime, by IV bucket, by holding period; % of losses exceeding 1R and their causes; average win / average loss in R; profit factor; heat at entry vs. outcome (does your sizing creep up after wins? — Schwartz's trap, measured).

### 7.7 Practice Curriculum — What to Practice, In What Order (12-Week Starter Cycle, Then Repeat at Larger Reps)

- **Weeks 1–2 — Survival and trend literacy.** Read Weinstein + Livermore's *How to Trade in Stocks*. Drill: stage 100 charts (market, groups, stocks) weekly; write Tudor Jones / Kovner risk page (§7.5) and use it with *paper* sizing calculations on real setups. No trading, or minimum size.
- **Weeks 3–4 — One setup only: VCP / Breakout.** Read Minervini, *Trade Like a Stock Market Wizard*. Nightly: Trend Template scan + 100-chart pattern pass (Ryan/Zanger drill). Trade only Setup 1/2, 0.25% risk, journal in R. Study 50 historical examples of the setup before increasing reps.
- **Weeks 5–6 — Add the Cycle and the Pullback.** Read Kell. Add Setups 4–5. Begin weekly statistics review; compute your first expectancy by setup (expect noise — 30 trades minimum before any conclusion).
- **Weeks 7–8 — Options as structure.** Read Natenberg (volatility chapters) + McMillan (structures for your views). Drill §2.2: five structures per view, on paper. Trade only debit verticals as alternatives to stock for two weeks; log IV percentile and expected move for every options trade.
- **Weeks 9–10 — Premium, tails, and earnings discipline.** Study §2.6 in full. Paper-trade one full earnings cycle with the implied-vs-actual table before risking capital on earnings structures. Set the annual tail budget and buy the first tail position *in a quiet market*.
- **Weeks 11–12 — Quant sleeve and macro context.** Build the systematic sleeve on paper / minimum size: a diversified trend rule (12-month time-series momentum, vol-scaled, across liquid ETFs/futures proxies) and/or a value+momentum+quality ETF tilt with an Arnott calendar rebalance for the core. Read Druckenmiller/Soros interviews and write your first monthly letter (§7.3). Full quarterly review: promote / bench setups by expectancy *in regime*, recalibrate size by the §5.3 rule (smaller of fractional-Kelly ceiling and fixed-fractional budget).
- **Ongoing, forever:** Nightly homework, weekly review, monthly letter, quarterly playbook review. That cadence — not a new indicator — is what every teacher in this report has in common.

---

## 8. The Distilled Rules — Ranked by How Universally the Greats Teach Them

1. **Define where you are wrong before you enter, and size from that distance.** (Livermore, Kovner, Minervini, Tharp, Qullamaggie, Saliba — unanimous.)
2. **Cut losses at a small, pre-set level and never average a loser; let winners run and add only to winners.** (O'Neil 7–8%, Livermore, Tudor Jones, Darvas, Druckenmiller.)
3. **Risk a small fixed fraction per trade — 0.5–1% — and cap total portfolio heat, counting correlated positions as one.** (Kovner, Tharp, Qullamaggie, Tudor Jones.)
4. **Trade only in the direction of the established trend / Stage 2, in leading stocks in leading groups, at a precise pivot on expanding volume.** (Weinstein, O'Neil, Minervini, Ryan, Zanger, Kell.)
5. **Wait — in cash if needed — for your setup. Most of trading is waiting; overtrading is the universal leak.** (Livermore, Schwager's wizards, Soros.)
6. **Asymmetry over accuracy: structure trades to make multiples of risk when right and lose ~1R when wrong (5:1 as an ideal, 2–3R partials as a practice), so a low win rate can still compound.** (Tudor Jones, Druckenmiller/Soros, Qullamaggie, Tharp expectancy math.)
7. **When you are trading well and the market confirms, press; when you are cold or the regime deteriorates, turn the dial down — never up to get even.** (Druckenmiller, Schwartz, Tudor Jones, Minervini.)
8. **Study historical big winners until the patterns are in memory, do the nightly chart homework, and keep score in R with execution grades.** (O'Neil, Ryan, Zanger, Minervini, Tharp.)
9. **In options, state your volatility bet explicitly: buy premium only when it is cheap against a real catalyst, sell it only rich, winged, and sized for a crash — and always know your Greeks / max loss.** (Natenberg, Saliba, McMillan, Augen, Taleb.)
10. **Own a little convexity for the tail and rebalance a core against extremes — survive the rare spectacular day and be positioned to benefit from it, instead of being ruined by it.** (Taleb/Saliba, Arnott, Soros.)
11. **Write rules down, test them, haircut backtests, diversify across independent bets/playbooks, and retire what stops working.** (Thorp, Simons, Shaw, Asness, McLean & Pontiff as a working habit.)
12. **Protect your state: if a position disturbs your ability to think, it is too big; after big wins as after big losses, shrink and reset.** (Kovner, Schwartz, Soros, Druckenmiller.)

---

## Sources — Books, Interviews, and Articles to Continue the Study

Each entry above cites its sources inline. The core reading list, in curriculum order:

- Livermore — *Reminiscences of a Stock Operator*; *How to Trade in Stocks*: https://www.alphaexcapital.com/jesse-livermore
- Darvas — *How I Made $2,000,000 in the Stock Market*: https://ww2.jacksonms.gov/browse/rFpxrs/2OK050/how_i__made_2000000__in__the_stock_market-nicolas__darvas.pdf
- Weinstein — Stage Analysis summary: https://arongroups.co/forex-articles/stage-analysis-trading/
- O'Neil — CAN SLIM: https://en.wikipedia.org/wiki/CAN_SLIM
- Minervini — Trend Template / SEPA / VCP: https://www.financialtechwiz.com/post/mark-minervini-trading-strategy/ ; https://de.tradingview.com/script/88aL78Qh-TwP-Mark-Minervini-Trend-Template-Criteria/
- Ryan / Zanger / Ritchie II — *Momentum Masters* excerpts: https://pubhtml5.com/pklzi/jywe//basic/ ; Ryan: https://www.turtletrader.com/trader-ryan/
- Zanger interview — price/volume only: http://www.traders.com/Documentation/FEEDbk_docs/2003/08/Abstracts_new/Interview/interview.html
- Schwartz — *Pit Bull* / *Market Wizards* rules: https://www.turtletrader.com/trader-schwartz/
- Qullamaggie — setups, sizing, exits: https://breakoutshappen.com/stock-news/how-to-trade-like-qullamaggie-setups-strategy-and-screener ; https://sharepredictions.com/tools/qullamaggie-breakout-planner/
- Kell — Cycle of Price Action: https://cyclesedge.substack.com/p/follow-the-cycle-of-price-action ; https://kelltrading.com/
- U.S. Investing Championship results by year: https://completetradersedge.com/us-investing-championship/
- Natenberg — volatility framework summary: https://cpelectronicscorporate.com/fetch.php/papersCollection/qpi2n8/Sheldon_Natenberg_Option_Volatility_And_Pricing.pdf
- McMillan — put/call and indicator method: https://www.moneyshow.com/articles/optionsidea-29757/
- Saliba — *Market Wizards* chapter: https://fliphtml5.com/lnym/nxba/JACK_SCHWAGER_-_MARKET_WIZARDS/186/
- Augen — *The Volatility Edge in Options Trading*: https://www.goodreads.com/book/show/22500759
- Taleb / Universa — convexity and barbell in practice: https://hub.cissychen.com/investing/antifragile-day25.en.html
- Variance risk premium — Bakshi & Kapadia and successors: https://www.theoptionpremium.com/p/the-variance-risk-premium-the-research-behind-why-selling-options-works
- Put-write / buy-write benchmarks: https://quantpedia.com/putwrite-vs-buywrite-index-differences/ ; https://www.dividend.com/options-and-income-channel/is-options-upside-becoming-capped/
- Dispersion / correlation premium: https://quantpedia.com/strategies/dispersion-trading
- Earnings straddle / IV crush worked examples: https://projectoption.com/learn/long-straddle ; https://marketchameleon.com/Instructional-Stock-and-Options-Trading-Videos/442/Microsoft-Earnings-Analysis-A-Deep-Dive-Using-Market-Chameleon
- 0DTE / dealer gamma: https://volatilitybox.com/research/0dte-options-and-volatility/
- Thorp / Kelly / Princeton Newport: https://compoundingmyinterests.com/compounding-the-blog/tag/long+term+capital+management ; fractional Kelly drawdown math: https://www.turbinefi.com/blog/position-sizing-risk-management-prediction-markets-2026
- Simons / Renaissance (Zuckerman account): https://www.readtrung.com/p/jim-simons-and-the-making-of-renaissance
- Shaw / statistical arbitrage and 1998: https://navnoorbawa.substack.com/p/de-shaws-1998-crisis-how-a-372-million ; https://www.institutionalinvestor.com/article/2btgiowdmfyg7ib5snvnk/portfolio/come-together-statistical-arbitrage
- Asness / AQR — factors and trend: http://finglimpse.blogspot.com/2026/10/cliff-asness-professional-biography-for.html ; century of trend: https://www.scribd.com/doc/128190136/A-Century-of-Evidence-on-Trend-Following
- Arnott — fundamental index / rebalancing: https://informaconnect.com/inside-etfs-europe-qa-with-the-godfather-of-smart-beta/ ; http://ritholtz.com/2018/07/transcript-research-affiliates-rob-arnott/
- Signal decay as a working prior (McLean & Pontiff): https://alphaarchitect.com/factor-premiums/
- Soros — reflexivity and Quantum: https://tradersummit.net/george-soros-theory-of-reflexivity/
- Druckenmiller — sizing, liquidity, streaks: https://www.longriverinv.com/thought/druckenmiller-at-sohn-2022
- Tudor Jones — defense and 5:1: https://www.geckomode.ai/blog/paul-tudor-jones-risk-management
- Kovner — undertrade, stops, correlation: http://www.turtletrader.com/trader-kovner/
- Robertson — closing letter, long best / short worst: https://aletteraday.substack.com/p/letter-78-julian-robertson-2000
- Bacon — Moore, rates-driven macro, fast cuts: https://moneyweek.com/471075/the-worlds-greatest-investors-louis-bacon
- Van Tharp — R, expectancy, sizing: https://tradermarkus.com/van-k-tharp-trade-your-way-to-financial-freedom-review/ ; https://layer0firewall.com/blog/van-tharp-trading-psychology
- Schwager — recurring themes across the *Market Wizards* books: https://cmigo.com/default.aspx/threads/s8yUo3/Market-Wizards-By-Jack-Schwager.pdf
- LTCM and Niederhoffer as risk case studies the masters themselves teach from: https://www.quantt.co.uk/resources/long-term-capital-management-collapse ; https://ritholtz.com/2026/09/lessons-victor-niederhoffer/

*End of masterclass report.*
