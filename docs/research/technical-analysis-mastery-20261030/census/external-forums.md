# External Census — Practitioner Forums and Communities
## Technical Analysis Mastery Program — 2026-10-30
### Area: Forums and communities (Reddit, Elite Trader, Forex Factory, TradingView Ideas)

**Posture:** Mastery study. Sources are inventoried for what they teach about *doing* chart reading: identification rules, drawing standards, reading order, and practice routines. Not a debunking pass.

**Access note (honesty):** 
- Elite Trader and Forex Factory pages were **read directly** via browser.open (full text retrieved 2026-10-30).
- TradingView Ideas index pages were **read directly**; individual idea pages are summarized from search-result excerpts and the index text.
- **Reddit (reddit.com) is blocked by browser policy** — direct open failed. Reddit material below comes from browser.search result excerpts, ChartExchange mirrors of Reddit posts, and secondary summaries. That limitation is flagged per-source. No Reddit page is claimed as directly read.

---

## 1. REDDIT

### 1.1 r/technicalanalysis
- **URL:** https://www.reddit.com/r/technicalanalysis/ (wiki: /r/technicalanalysis/wiki/index/ — not directly readable, blocked)
- **What it teaches:** Open chart-critique culture. Practitioners post annotated single-name and index charts and invite line-by-line challenge. Recurring curriculum in the wild: Wyckoff volume events, relative strength lines, multi-timeframe confirmation.
- **Identification / drawing rules extracted (via search + ChartExchange mirror):**
  - **Relative Strength line protocol:** Always name the benchmark and lookback. An RS line making a new high *before* price is read as quiet leadership. Check RS on a second timeframe — short-term RS up while weekly RS is still falling = bounce, not leadership change. Compare against SPY vs QQQ vs sector ETF (e.g. IGV for software); the choice changes the read.
  - **Wyckoff volume events, quantified:** A high-upvoted r/technicalanalysis post (mirrored on ChartExchange, Oct 2026) pre-registered mechanical definitions before testing: ES 5-min bars 2010–2026, price cut into waves with a volatility-scaled threshold (not fixed), volume totalled per wave, then five classic events detected — No Supply, No Demand, Shortening of Thrust, etc. Lesson for mastery: the community's best work *writes the definition and success criteria down before looking*, and reports that the edge did not transfer to BTC/gold/ETH — instrument-specific, not universal law.
  - **Bar-by-bar reading:** Size, shape, and position of each bar relative to prior bars; wicks, body location, and volume surge/divergence as confirmation. Pin bars, engulfing bars, inside bars read in sequence, not in isolation.
- **Practice routine:** Post your annotated chart for public critique; pre-register pattern definitions before backtesting a claim.
- **Limits:** Direct reading blocked in this census. High noise-to-signal; best technique is in highly-upvoted long-form posts, not the daily feed. No stable wiki text could be retrieved.

### 1.2 r/swingtrading
- **URL:** https://www.reddit.com/r/swingtrading/
- **What it teaches:** Multi-day to multi-week holds. The shared vocabulary is classic bases and breakouts, taught almost entirely through annotated chart examples.
- **Identification / drawing rules extracted (via widely cross-posted pattern canon that dominates the sub's education threads, e.g. the SakatasHomma annotated set):**
  - Every pattern is taught with the same 3-part annotation: **ENTRY / SL / TARGET printed on the chart.**
  - **Double Bottom:** Two lows at similar level; entry = breakout of neckline that also forms a higher swing high; SL = low of day or swing low on lower TF; target = neckline-to-bottom height projected up.
  - **VCP (Minervini Volatility Contraction Pattern):** Successive contractions left-to-right in (1) price range, (2) time, (3) volume. After 3–4 contractions with final contraction in single digits, buy above pivot / down-trendline; SL = swing low. "All triangles after an uptrend are VCPs" is the community shorthand.
  - **Flag:** Pole (prior uptrend) + mast/retracement; constructive only if volume dries up in the mast; entry = break of down-trendline *with* volume on breakout; target = pole length from breakout.
  - **Head & Shoulders:** Read as trend change HL-HH → LH-LL, marked explicitly on chart; neckline joins the two intervening lows; entry = neckline breakdown; target = head-to-neckline distance projected down. Volume tell: head on lower volume than left shoulder.
  - **Ascending Triangle / Flat Base / Cup & Handle / High Tight Flag:** Same template — horizontal resistance + rising or flat support, entry only on breakout with volume, SL at swing low.
  - **Broadening / megaphone:** Trade the reversal points at the rails, no breakout assumption.
- **What they check first:** Prior trend exists (patterns are meaningless without it), then contraction/volume dry-up, then pivot proximity.
- **Limits:** Blocked for direct reading. Pattern canon is repetitive and bullish-biased (long breakouts dominate); risk discussion is thinner than entry discussion.

### 1.3 r/Daytrading
- **URL:** https://www.reddit.com/r/Daytrading/
- **What it teaches:** Intraday process discipline more than patterns: pre-market levels, screenshot journaling, review routines.
- **Technique extracted:**
  - **Screenshot journal (community-standard method):** Don't write prose during the session. Keep all intraday drawings on the chart, mark start/stop times with vertical lines, note news times you stood aside for, note tendencies/errors/missed trades as text on the chart, then screenshot the whole day (1–3 shots). Record result in points/ticks/pips, *not dollars* (size-independent). Include 1–2 hours of pre-session price action for context.
  - **Nightly chart review (MapleStax routine, heavily circulated in day-trading communities):** (1) Review every trade that night; (2) top-down redraw — Daily → Hourly → 10m → 5m — drawing trend, S/R, S/D, pivots, flags you *missed live*; only the most obvious formations, to train live recognition speed; (3) plot your actual entries/exits onto the redrawn chart to see if you traded with or against the larger trend; (4) add live in-trade notes for psychology; (5) log exterior influences (index, news, FOMC, OPEX); (6) close with explicit improvement questions: chasing? FOMO entry? stop respected? over-confirming?
  - **Pre-market routine from the same school:** Chart the extended-hours channel before the open for reject/base levels; mark supply/demand zones pre-open; have contracts/setups pre-selected.
- **Limits:** Blocked for direct reading; material retrieved via search excerpts and thread-reader mirrors.

### 1.4 r/RealDayTrading (bonus — the most systematized Reddit trading community)
- **URL:** https://www.reddit.com/r/RealDayTrading/ (wiki is the curriculum)
- **Why included:** Assignment named three subs; this fourth is where Reddit's most explicit *reading protocol* lives and is constantly cross-referenced from r/Daytrading.
- **What it teaches:** Pete Stolcers / Hari Seldon system: market first, stock second, always relative to SPY.
- **Identification rules extracted:**
  - **Real Relative Strength (RRS):** `expectedPC = (mktPC / mktATR) * ATR`; `RRS = (PC − expectedPC) / ATR`. RRS > 0 = outperforming the market over the window, ATR-normalized so names are comparable. Used via Pine Screener to sort watchlists, not as a visual overlay. Lesson repeated in the wiki: understand *why* a pattern works, don't memorize shapes.
  - **Reading order:** (1) Market (SPY) direction and intraday posture first; (2) only trade stocks with real relative strength (longs) or weakness (shorts) vs SPY on both daily and intraday; (3) daily chart must agree (above/below key MAs, clean daily structure).
  - **Practice timeline the community prescribes:** Wiki + video study, then paper trade far earlier than beginners plan (around month 6, not month 8–9), accumulate *months of stats* before live size, start live with 1 share/contract.
- **Limits:** Blocked for direct reading; RRS formula verified via the TradingView Pine script that implements the wiki metric (read via search). Full system is partly paywalled (OneOption).

---

## 2. ELITE TRADER

### 2.1 "IronFist learns (the elusive) PRICE ACTION" — the canonical teaching thread
- **URL:** https://www.elitetrader.com/et/threads/in-this-thread-ironfist-learns-the-elusive-price-action.146764/page-35 — **READ directly**
- **What it teaches:** A complete discretionary price-action workstation and reading protocol, posted as a pay-it-forward lesson (2008, still referenced).
- **Reading protocol (verbatim structure):**
  - **Four charts always:** (1) very short TF of the stock — "get a feel for price action"; (2) medium TF — the trading chart, stared at most; (3) long TF of the stock — trend/direction; (4) long TF of the overall market, synced — market sentiment/direction.
  - **Chart dressing:** A couple of EMAs only, to stay oriented to direction. Candles in **shades of grey, not red/green**, deliberately to avoid color bias. Several horizontal lines on the long-TF charts; only a couple on the trading chart ("so I don't get wrapped around the axle").
  - **MA rule:** Find the MA *that specific equity respects* — on wild moves, in ranges, and on minor pullbacks — by trial and error; every equity "has a personality." Keep the MA *equivalent across timeframes* (e.g. 20 on 5-min ≈ 100 on 1-min) so timeframes don't contradict.
  - **Core heuristics:**
    - Long bars are **not tradable** unless already in, in the direction of the race.
    - Price repeatedly bumping its "butt" on support without breaking, and tending to move away = probably up. Mirror at resistance = probably down.
    - Price climbing up a respected MA = probably long; climbing down it = probably short — *if* market and time-of-day agree.
    - Every setup must have a **logical stop level** where you are "relatively sure the trade isn't working"; stop-out can become a reversal.
    - Always classify the day: inside/outside day, upside/downside day. Always account for time of day.
  - **Business routine:** Trading plan with entry/exit and money-management rules, daily/weekly/monthly goals, continuing education, and a **daily journal is paramount**.
- **Limits:** Equities/day-trading specific; discretionary and personality-based ("adopt one methodology, stick with it, evolve it into your own") — deliberately not mechanical.

### 2.2 "Naked Chart Trading and discussion"
- **URL:** https://www.elitetrader.com/et/threads/naked-chart-trading-and-discussion.371584/ — **READ directly**
- **What it teaches:** Pure price action, zero indicators. Strict reversal trading on Head & Shoulders / triple tops/bottoms, optimized for reward:risk so win rate matters less; avoids daily/weekly charts because stops get too wide.
- **Technique extracted:**
  - **Annotation in words on the chart:** Context first ("Context, Context, Context" — e.g. strongest vs weakest currency first). Then state trend, then the invalidation: "We're in a downtrend but made a higher high. Now we could make a double bottom but the immediate trend is still down. We would need to reverse to establish it."
  - **Framing a range:** Box the trading range; if price hugs the bottom of the range with lower highs, downside breakout is the likely outcome — don't buy it; short the rally to the range top instead.
  - **Directional Day Filter (DDF):** Take the first 5 minutes' average (for FX, 2–3am European open), plot it through the first 60 minutes; count how many bars' median price sits above vs below it to judge the day's trend; roughly equal = choppy/trendless day expected. Reinforced by where price *closes* the first hour relative to that average. Claimed 75–80% day-direction hit rate by its user. Can be done by eye to keep the chart naked.
  - **End-state minimalism (veteran post):** "Decades ago I started with thousands of indicators and triangles and rays and arcs and butterflies and Elliott waves and fibs. Now I have nothing except a zig-zag line."
- **Limits:** Thread is a practice journal, not a curriculum; method must be inferred from trade posts.

### 2.3 Jack Hershey SCT (Seamless Compound Trading) corpus
- **URLs:** https://www.elitetrader.com/et/threads/making-jh-sct-and-all-his-material-alive.320588/ ; https://www.elitetrader.com/et/threads/jack-hershey-method-emergency-exit-drill.76836/ ; Price/Volume Relationship thread (p.19) — via search excerpts
- **What it teaches:** The most formalized *annotation* system on any forum: continuous channel drawing on nested fractals with a price-volume relationship (PVR) read on every bar.
- **Drawing / reading rules:**
  - **Three nested channel levels at all times** — channels within channels within channels. Inner short-term channels drawn in unobtrusive grey and projected.
  - **Channel construction:** Pt1 → Pt2 → Pt3 forms the container; right trend line (RTL) and left/fanning line (LFT) bound the traverse. Dominant traverse = RTL to LFT; non-dominant = return.
  - **PVR (the core read):** Dominant price segments are supported by **increasing volume**; non-dominant segments by **decreasing volume**. Expect a volume **peak at Pt2** and a **trough at Pt3**. A volume trough + B2B (bar-to-bar direction change on volume) marks dominance flipping. When volume stops increasing and begins decreasing, price's driving force flips with it.
  - **Mode protocol:** At any moment the market Mode is CONTINUE (stay on the right side, keep extracting) or CHANGE (20–40 times a day on 5-min ES; reverse at the Failure-To-Traverse / FTT at the left channel line). Segments typically last 2–4 bars (10–20 min).
  - **Emergency Exit Drill:** If you miss the FTT reversal on the grey channel, reverse when the right channel line is breached (the breakout) as an emergency exit. Drill's real purpose stated explicitly: "more about doing good annotations of channels than anything else" — annotation accuracy *is* the skill. Hershey warns a full SCT day is initially impossible; one hour of correct annotation is an accomplishment; six mental drills build the stamina.
  - **Separate Hershey stock-selection method** (also on ET): Universe $10–$50, 500K+ daily volume; rank by volume dry-up (5-day avg volume < 50% of 30-day) and volume change; sort into 7s / 1s / 0s quality tiers.
- **Limits:** Notoriously dense private vocabulary (FTT, B2B, RTL/LFT, Gaussian volume formations); multi-year thread archaeology required. Treat as an annotation discipline exemplar, not a quick system.

### 2.4 "Beginner Question" / price action definition thread
- **URL:** https://www.elitetrader.com/et/threads/beginner-question.99119/page-3 — via search excerpt
- **Technique (the forum's most quoted definition):** "Price action is merely the relation of current price in relation to previous price — modern-day tape reading. You are comparing the open and/or close of the current bar to prior bars' opens and closes. Simply put, price action is the footprint of money. Swing highs and lows are price action. Higher highs, higher lows, lower highs, lower lows are all price action." Entries, exits, stops, and expected points per trade all derive from that relation. Companion advice: write down intrusive in-trade thoughts; journaling makes them recur less.

---

## 3. FOREX FACTORY

### 3.1 James16 Chart Thread (the foundational price-action thread, est. 2005)
- **URL:** Forex Factory, "James16 Chart Thread" (2,500+ pages). Read via the decoded summaries: https://www.scribd.com/document/94786443/James-16-Decoded and PriceActionNinja James16 guide (search excerpts); thread itself referenced from Elite Trader as FF's #2/#3 thread by replies (10,000+).
- **What it teaches:** Trade from a blank chart, daily/weekly timeframe, only at significant S/R, only with-trend ("buying the dip"; counter-trend entries called poorer quality). Position size 2–3% per trade.
- **Identification rules (precise — the thread's lasting contribution):**
  - **Pin Bar (Pinocchio Bar) — the flagship:** Long nose relative to the open/close/low; nose protrudes a long way from surrounding prices ("it sticks out"); open and close both clustered near one end of the bar. It is effectively a swing high/low rejection. Entry beyond the nose's opposite end; stop beyond the nose tip; classic target = 2× risk.
  - **BUOVB / BEOVB:** Bullish/Bearish Outside Vertical Bars — engulfing bars whose range engulfs the prior bar, traded as momentum reversals or continuations *at S/R*.
  - **DBLHC / DBHLC:** Double Bar Low with Higher Close / Double Bar High with Lower Close — two bars with matching lows (or highs), second bar closing higher (or lower); a quieter reversal tell.
  - **Inside Bars:** Compression inside prior bar's range; traded as breakout/continuation at confluence.
  - **Confluence rule:** A bar pattern alone is not a setup. It must cluster at a point of confluence: significant horizontal S/R, trendline, round number, Fibonacci level. 3–4 bar reversal clusters at such points are the entry.
  - **2B refinement (Victor Sperandeo pattern as developed in-thread):** Fast reaction at a double top/bottom (pin bar ideal, but a meaningful directional bar suffices) + divergence; if a BUOB/BEOB trigger doesn't fire within 5–6 bars of the first top/bottom, or the follow-through entry isn't triggered within 4 bars including the signal bar, cancel the order. Pin-bar triggers carry no such expiry.
- **Limits:** Original thread is unindexed and enormous; the method survives through decoded PDFs/summaries and a formerly paid ($129/mo) private group. Daily-TF only — not an intraday method.

### 3.2 Strat's PASR — "Strat's PASR Long Term, Stress Free Trading" + Terry's Journal
- **URLs:** https://www.forexfactory.com/thread/708441-strats-pasr-long-term-stress-free-trading ; https://www.forexfactory.com/thread/705590-terrys-journal — **Terry's Journal READ directly**; PASR thread via search excerpts. 15+ years on Forex Factory.
- **What it teaches:** PASR = Price Action Support Resistance. A rigid top-down hierarchy with its own chart grammar.
- **Drawing / reading rules:**
  - **Three timeframes, named roles:** **Big Boss** (monthly) → **Boss** (weekly) → **Worker** (daily). H4/H1 are management timeframes only.
  - **Control Candles:** A Big Boss or Boss candle at a price extreme whose range brackets subsequent action becomes the S/R frame. Box it on the chart (in Terry's journal: green box = Big Boss control candle, red box = Boss control candle). The **Weekly Control Candle (WCC)** stays in force until a weekly candle *closes* outside its range; that closing candle is **not** itself a new WCC — a new WCC forms only when the *following* weekly candle closes *within* the prior candle's range. Opens/closes are ignored when identifying WCC formation except for that close-outside rule.
  - **Strat Shadow:** The band formed by the EMA/SMA stack (incl. 18/72 cross noted on charts; 20 EMA and 200 EMA are the working lines). Price inside the shadow = expect a choppy, non-smooth swing; price rejecting the shadow + 200 EMA confluence = high-attention zone. The 9 EMA crossing/touching the shadow gauges momentum.
  - **Reading order per trade post (the journal template):** For each of Big Boss / Boss / Worker state: Strat Shadow direction (up/down, positive/negative), price structure (swing sequence, breaks, retests), then the trigger candle (Hammer, Shooting Star, BUEB/BUOB) *rejecting* a named level (shadow, WCC edge, 200 EMA, round number). Plan must state: entry (e.g. buy stop 3–6 pips above the BUEB), stop (same buffer below it, 78–160 pips on HTF trades is normal), TP1 = next timeframe's resistance / basic PASR partial, remainder held until *reverse PASR* signal.
  - **Review ritual:** End-of-week review post re-examining the control-candle frame: "Set BB control candle using its top and bottom along with daily Strat Shadow; watch PA at internal S/R (shadow, 200 EMA); fourth attempt at resistance succeeded and turned into support — now watch PA on all three timeframes at the next BB level; drop to H1/H4 only when price arrives there."
  - **Failed-signal inversion:** A failed Shooting Star or Hammer (price closes through it) is itself a tradable signal in the opposite direction.
- **Limits:** Requires learning the path in order (veterans refuse template requests: "learn and understand PASR before anything else"); Strat's own site has shut down, so Forex Factory is now the archive of record.

### 3.3 Candle Cartel
- **URL:** https://www.forexfactory.com/thread/1396448-candle-cartel — **READ directly** (active, 2026)
- **What it teaches:** A modern, majors-only price-action room. House rules encode the technique: no blind signals (reasoning mandatory), discussions must be clean, logical, and chart-based.
- **Technique extracted:**
  - **Top-down weekly post format (the room's standard artifact):** One post per pair walking Monthly → Weekly → Daily → 4H → 1H, one verdict per timeframe, then a single conclusion with the invalidation. Example retrieved: EUR/USD — Monthly "ranging in an overall uptrend"; Weekly "higher swing high then lower swing low, possible reversal"; Daily "strong rejection candle Friday + gap up, ambiguous"; 4H bullish vs 1H bearish → conclusion: downward correction likely but not started; cautious shorts unless price trades above Friday's high.
  - **Core doctrine (repeated by members):** "Every higher timeframe candle carries a tone, a message. Read across multiple timeframes and align those tones with the lower ones — that's how the full story comes together." Locking into one or two timeframes is named as the beginner failure.
  - **Journaling doctrine:** "Journal your reasoning, not just entries and exits. That's where real edge develops."
  - **Level discipline:** A resistance being tested for the 4th time after 3 clear reactions "deserves attention again before assuming a breakout"; stronger momentum on the 4th approach is noted as the thing that could change the read. FVGs and H4 opens (e.g. trading above/below the H4 open at a stated price) used as intraday bull/bear dividing lines.
- **Limits:** Young thread; educational value is in the format discipline, not a codified system.

### 3.4 "The Basics" / "The real Basics" — naked-chart observation school
- **URLs:** https://www.forexfactory.com/thread/959644-the-basics ; https://www.forexfactory.com/thread/959764-the-real-basics-how-to-start-and — via search excerpts
- **Technique:** The anti-indicator apprenticeship: (1) Watch a naked chart for a long time *without the pressure of making a decision*; paper and pencil, note what price does over and over. (2) Mark where price seemed to turn; when it returns, observe precisely: does it break, by how much, with what force, what happens after? If it holds, how far did it poke through before holding, and how fast did it reverse? (3) Only after that observation base, add the minimal grammar: candlestick patterns + fractals for S/R + Fibonacci for retracement/extension targets. Claim from a mentor quoted in-thread: "You need nothing more than price and manually drawn lines."
- **Related fixed-scale craft (from FF search corpus, "Dance"-style threads):** Lock the chart's y-scale by timeframe (quoted standard: 50p for M1, 100p for M5, 150p for M15, 200p for H1) so bar geometry stays comparable and the view of price action stays objective instead of auto-scaling to fit the narrative; judge EMA-constrainment bounces against that fixed geometry.
- **Limits:** Advice threads, not systems; value is the practice prescription.

### 3.5 NextElliott Momentum Cycle Suite thread (modern structured-reading exemplar)
- **URL:** https://www.forexfactory.com/thread/1417934-nextelliott-momentum-cycle-suite-cycle-momentum — via search excerpt
- **Technique:** A layered read printed on every chart example, in fixed order: **TREND → STRUCTURE → CYCLE → CONFIRMATION → HURDLE → ACTION.** Structure vocabulary: HPH/HPL/LPH/LPL (higher/lower pivot highs/lows). Two mastery distinctions repeated throughout: "Direction is not the same as trade location" and "Trend direction is not the same as entry timing" — a correct SELL read with a hurdle (support) too close becomes ACTION: PROTECT PROFIT / WATCH, not a new entry. The question taught: not "is this a sell?" but "is the sell sufficiently confirmed, and is there enough room for the trade?"
- **Limits:** Built around a proprietary MT4 suite; the transferable part is the reading order and the room-to-hurdle check.

---

## 4. TRADINGVIEW COMMUNITY (Ideas + Education)

### 4.1 The Ideas annotation convention (platform-wide)
- **URL:** https://www.tradingview.com/ideas/ (Education filter: /ideas/?type=education)
- **What it teaches:** TradingView is the world's largest annotated-chart corpus. Its house style is itself a drawing standard.
- **Conventions extracted across education ideas:**
  - **Structure of a publishable idea:** Bias statement first, then the marked chart (zones as rectangles, not lines), entry / stop / target drawn with the long-short position tool so R is visible, an explicit invalidation ("primary scenario remains bullish while price holds above the X support zone"), and scenario B. Video ideas add bar-by-bar narration.
  - **Bar Replay practice culture:** The community-standard drill: rewind with Bar Replay (future bars hidden), advance bar-by-bar or step-forward, *record entry and invalidation before revealing subsequent bars*, log entry/stop/target in a journal. Explicitly framed as the cure for hindsight bias. Community scripts extend it (e.g. "Tool for Practicing Trading" — a grey curtain hides everything after a chosen "Now"; step day-by-day/hour-by-hour).
  - **Use community ideas as a second opinion, not an oracle:** The expert-workflow guides built on TradingView repeat: find alternate interpretations of the same chart; never outsource the decision to the most persuasive author.

### 4.2 Support & Resistance education canon (multiple education authors)
- **URLs:** https://www.tradingview.com/ideas/supportandresistance/ ; India education hub summary read via search — **index READ directly (page 10)**
- **Drawing rules (consensus across the canon):**
  - **Zones, not lines — the #1 rule.** "Support/Resistance = Zone" (e.g. draw 24,480–24,530, not 24,500). Biggest beginner mistake is the exact thin line. Use a rectangle.
  - **How to draw correctly:** Work from the higher timeframe (1H/4H/Daily); mark swing highs and swing lows; require multiple touches (more touches = stronger level); a valid level needs at least 2 clear reactions and must be *obvious* — "if you have to squint, it's not a real level."
  - **Taxonomy taught:** (1) Horizontal S/R; (2) Dynamic S/R — 20/50/200 EMAs (50 EMA singled out as "the institutional dynamic support" in strong trends) and trendlines; (3) Psychological round numbers.
  - **Role reversal / flip:** Broken resistance becomes support, broken support becomes resistance; always watch the retest after the breakout.
  - **Usage template printed on ideas:** Buy near support → SL below support → target resistance (mirror for shorts). Never trade S/R alone: combine with market structure, trend direction, volume, candlestick confirmation.
  - **Day-trading key-level checklist (mingjong education series):** Previous day high/low, non-RTH (overnight) high/low, swing highs/lows from the last few days, and swings formed intraday on M3/M5. Mark them *before* the session.
  - **Supply/demand variant (mingjong):** Identify the zone by the *departure*: look for the big-spread bar where price accelerated away; volume confirms the zone's origin.
- **Limits:** Quality varies enormously; the Education tag and Editors' Picks are the filter, not the raw feed.

### 4.3 Trendline drawing standard (education ideas)
- **URLs:** TradingView education ideas on trendlines (mingjong "How to draw & interpret trendlines correctly" — index read; 3-touch posts via search)
- **Rules:**
  - **3-touch rule:** 1 touch = a point; 2 touches = a hypothesis; 3+ touches = a validated trendline. "Until the line has three rejections, it is not a tool — it is a guess." For support in an uptrend want ≥3 wick touches with bodies mostly above; mirror for resistance.
  - **Construction:** Uptrend line connects rising swing lows (the floor / demand line); downtrend line connects falling swing highs (the ceiling / supply line). Draw on the timeframe you trade. When violated, redraw to fit as many swing points as possible.
  - **Angle discipline:** Too steep = not a trend, "a chase / FOMO on a stick." Slow angle = sustainable, swing-friendly; medium angle = expect a sharper correction on break. Slope = pace of the trend; a break = change of pace.
  - **Break definition:** Not a touch, not one candle poking through — need acceptance/close and follow-through; fake pokes are expected.
  - **Obviousness test:** "The best trendlines are the obvious ones. If you need 10 zoom levels and a ruler, only you care." Use as context with confluence (S/R, range high/low, volume zones), never as a standalone religion.
  - **Channels for momentum (mingjong):** Parallel channel + up-thrust / up-wave beyond the channel to judge whether momentum is expanding or fading; fading momentum is the first weakness sign before any reversal call.

### 4.4 Wyckoff / VSA education line (mingjong and peers) and Pitchfork line (HowToChart)
- **URLs:** https://www.tradingview.com/ideas/supportandresistance/page-10/?type=education (read); https://www.tradingview.com/ideas/pitchfork/?type=education (via search)
- **Technique:**
  - **Range vs Trend recognition first (Fineight):** "The most crucial ability is to recognize if you are in a Trading Range or in a Trend. Every stage requires a different approach." Tool: swing highs/lows only. S/R taught as a *zone where you expect activity*; what matters is whether a breakout was *respected*, not whether price crossed a line by a few points.
  - **Analog reading (mingjong ES series):** Daily recap ideas compare the current structure bar-for-bar with a historical analog (e.g. Oct 2008 ES), name the Wyckoff events (selling climax, upthrust), state the target zone (which often coincides with the 50% retracement of the prior leg), and update the read every session as bars print — a public, dated, falsifiable journal.
  - **Andrews Pitchfork (median lines):** Anchor P0 at a significant high/low; P1/P2 are the next high/low; median line runs from P0 through the midpoint of P1–P2, parallels through P1 and P2. Price returns to the median in ~80% of cases (Andrews' claim as taught); failure to reach a line = Hagopian rule (reversal likely back the other way). Best practice taught: apply on higher timeframes for macro trend judgment; count interactions with median/extreme lines as dynamic S/R; optimal anchor sits between the high and low of the *next* trend leg.

### 4.5 Editors' Picks ecosystem and script authors (LuxAlgo, PineCoders, KioseffTrading, etc.)
- **URL:** https://www.tradingview.com/ideas/ (Editors' Picks author rosters, via search)
- **What it teaches:** Curation as curriculum. Monthly Editors' Pick author lists (LuxAlgo, KioseffTrading, Trendoscope, VasilyTrader, Akil Stokes, norok, QuantVue, and ~30 rotating authors/month) mark whose annotation to study. Script-side, LuxAlgo's open-source S/R work codifies the drawing rules: pivot-based levels that explicitly label the event on the chart — **Breakout / Test / Retest / Rejection** — with a cleanliness standard (limit displayed levels, ~5 as the "sweet spot," so the chart stays readable). Premium/Discount/Equilibrium zones from swing structure (SMC/ICT vocabulary: order blocks, fair value gaps, liquidity) are the dominant modern annotation dialect in the community.
- **Practice implication:** When an indicator draws a level, the community standard now requires it to also state *what price did there* (tested, rejected, broke, retested) — annotation of behavior, not just geometry.
- **Limits:** Editors' Picks skew to engagement; SMC/ICT vocabulary is fashionable and inconsistently defined between authors. Paid script tiers (LuxAlgo premium) gate some tooling, though core education ideas are free.

---

## 5. CROSS-COMMUNITY SYNTHESIS — TECHNIQUE THAT REPEATS EVERYWHERE

1. **Reading order is always top-down and outside-in:** Market/index first (or Big Boss timeframe / strongest-weakest currency), then higher-TF structure and zones, then lower-TF trigger. No community teaches trigger-first reading.
2. **Zones beat lines; obvious beats clever.** S/R as rectangles, levels requiring multiple clear reactions, trendlines requiring 3 touches, and the squint test appear independently on TradingView, Forex Factory, and Elite Trader.
3. **Context before pattern:** A pin bar / engulfing / hammer only counts at a pre-marked level with confluence (James16), inside a control-candle frame (PASR), or against a horizontal line drawn on a higher timeframe (Elite Trader). The pattern is the trigger; the level is the setup.
4. **Volume confirms the geometry:** Breakouts need volume expansion, bases need volume dry-up (Reddit swing canon, VCP), dominant traverses need rising volume and non-dominant ones falling volume (Hershey PVR), Wyckoff events are volume-defined (r/technicalanalysis).
5. **Every annotation carries its invalidation:** Entry/SL/target on the chart (Reddit swing), logical stop where "the trade isn't working" (IronFist), stop beyond the pin nose (James16), buffer beyond the trigger candle (PASR), scenario-killing close (Candle Cartel).
6. **Practice = hidden-future reps + screenshot journals + scheduled review:** Bar Replay bar-by-bar with decisions logged before reveal (TradingView), nightly top-down redraw with your fills plotted on it (r/Daytrading school), end-of-week control-candle review (PASR), screenshot-of-the-day journal in points not dollars (day-trading canon), and Hershey's annotation drills where drawing accuracy itself is the trained skill.
7. **Minimalism is the veteran end-state in every community:** Grey candles and two EMAs (IronFist), a single zig-zag (ET naked thread), blank chart + hand-drawn lines (FF Basics, James16). Communities treat indicator removal as a milestone, not a starting point — screen time on naked charts is prescribed *before* tools are added back.

## 6. SOURCE QUALITY / FRESHNESS NOTES
- **Evergreen canonical:** IronFist thread (2008), James16 (2005– ), Hershey SCT corpus (2000s–2010s), Strat PASR (15 yrs). Old but still the referenced originals; vocabulary must be learned to read them.
- **Currently active (verified 2026):** Candle Cartel (posts dated 2026), PASR thread (2026 trade posts), TradingView Education feed, r/technicalanalysis (Oct 2026 quantified Wyckoff post via mirror).
- **Blocked / indirect in this census:** All of Reddit (policy block — search/mirror only). James16 original thread (read via decoded summaries, not paginated directly). Individual TradingView idea pages beyond the index (search excerpts).
- **Paywalls encountered:** RealDayTrading full system (OneOption), James16 historical private group ($129/mo, defunct as a requirement — content is in the free thread/summaries), LuxAlgo premium scripts (core education free).
