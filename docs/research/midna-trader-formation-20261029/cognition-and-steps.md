# Trader Cognition and the Complete Trade Step Sequence

### What a trader's mind must actually do, and every step a human executes for one trade, from before the open to the review days later

> **How to read this document.** This is a formation document, not a verdict document. Following the owner's standing correction on this exact kind of study (2026-10-28: "I didn't say grade them. I said learn."), the posture throughout is absorb and emulate first; judgments appear only where evidence forces them, and every load-bearing claim is separated into what is **proven** (replicated research, audited records, or arithmetic), what is **credible practitioner testimony** (masters stating their own practice, consistently, across independent interviews), and what is **lore** (widely repeated, plausible, and not established). Where those three disagree, the disagreement is named rather than smoothed over.

---

## SCOPE (InfinityBlade)

- **Surface (what this document covers):** (1) The cognitive faculties a discretionary / semi-systematic equity and equity-options swing trader must run, faculty by faculty, with the evidence for each and a drill for each. (2) The exhaustive, numbered, ordered sequence of steps for a single trade, from the evening before entry to the review weeks later, with each step tagged by type.
- **Constraints (what stays untouched):** No new strategy is invented here. The playbook, risk limits, and setups are taken as given from the master-trader study (`~/workspace/research_notes/master-traders-deep-dive-20261029-0229/report.md`) and the personal-quant operating plan (`~/workspace/personal-quant/PLAN.md`): five stock setups, four options expressions, 0.5% standard risk / 0.75% A+ / 0.25% probe, portfolio heat caps, R-multiple accounting, trade cards written before entry, journal rows written the same day. This document explains the mind that runs that system and the steps that system decomposes into. It does not retune the system.
- **Outcome (observable success):** A reader can (a) name each cognitive faculty, state its known failure mode, and point to the structural countermeasure for it; and (b) execute one complete trade by following Part 2 literally, step by step, without having to invent any intermediate step.
- **Proof:** Part 1 claims carry sources. Part 2 steps are checkable against the trade card and journal fields in Phase J; a step that leaves no trace in either artifact is flagged as a state/discipline step rather than a record step.
- **Edges (boundaries):** US equities and listed equity options, daily-bar swing horizon (days to weeks), human execution with broker orders placed in advance where possible. Intraday scalping, futures margin mechanics, and tax-lot accounting are noted only where they change a step. Simulated / paper trading follows the identical sequence; only the fill-pricing rule differs, and that difference is stated where it matters.

**Step-type tags used in Part 2:**

- **[J] Judgment:** a human estimate or recognition act. Cannot be fully mechanized; can be trained, bounded, and recorded.
- **[A] Arithmetic:** a calculation with a right answer. Must be computed, never eyeballed.
- **[D] Discipline:** an act whose content was decided in advance, in calm. In the moment it requires no judgment at all, only compliance. Most "psychology" failures in trading are [D] steps being re-opened as [J] steps under stress.
- Many steps are mixed, e.g. **[J+A]**. The first tag is the dominant one.

---

# PART 1: THE BRAIN

## 1.0 The job description nobody writes down

Strip the romance away and a trader's mind performs seven computational jobs, continuously, in a hostile environment:

1. **Estimate probabilities** for events that have no exact probabilities, only reference classes and partial information.
2. **Combine those probabilities with payoffs** into expected value, including costs, and compare unlike opportunities on that common scale.
3. **Recognize patterns** in price, volume, and context that have historically preceded favorable payoffs, while refusing patterns that are only stories.
4. **Allocate attention**, the scarcest resource in the system, across far more information than can be processed, without letting salience choose for it.
5. **Regulate its own state**, because the estimator, the recognizer, and the executor are the same wetware, and fear, greed, fatigue, and shame all rewrite its parameters in real time.
6. **Pre-commit** its calmer self's decisions so its stressed self has less to decide.
7. **Learn from feedback** that is noisy, delayed, and actively misleading, since good decisions lose and bad decisions win on a regular basis.

Every section below takes one faculty, states what the evidence says about how it actually works (including where the popular version is wrong), maps its characteristic failure in trading, and gives the countermeasure the masters and the adjacent elite fields converged on. The convergence is the striking finding of this whole study: traders, poker players, chess players, pilots, surgeons, firefighters, and intelligence forecasters, working independently, in different centuries in some cases, built strikingly similar machinery for the same seven jobs. That convergence is itself evidence. A practice invented once might be fashion; a practice invented five times under five different selection pressures is probably load-bearing.

## 1.1 Probabilistic thinking and base rates

### What it is

Probabilistic thinking is the habit of answering "how likely?" with a number, derived in a specific order: **first the outside view, then the inside view.**

The outside view asks: *in the reference class of situations like this one, how often did the outcome happen?* That frequency is the **base rate**. The inside view asks: *what is specific about this case that should move me off the base rate, and by how much?* Philip Tetlock's Good Judgment Project, the largest forecasting tournament ever run (thousands of volunteers competing against intelligence analysts and prediction markets on well-defined geopolitical questions, 2011 to 2015), found that its best forecasters, the "superforecasters," differ from ordinary experts in exactly this discipline. They start from base rates, adjust in small increments (typically 5 to 15 percentage points, not 40), and update frequently in small steps (2 to 5 points at a time) as evidence arrives, rather than planting a confident flag and defending it. Tetlock and Gardner, *Superforecasting* (2015); summary at https://vectree.io/pdf/c/superforecasting-philip-tetlock and the calibration discussion at https://www.convexly.app/blog/overconfidence-bias.

The trading translation is direct, and it is where most discretionary trading quietly fails. The relevant base rates for a swing trader are not macroeconomic; they are personal and setup-specific:

- Of my last N trades in this named setup, in this regime, what fraction reached +1R before hitting minus 1R? What fraction reached +2R, +3R?
- Of breakouts of this shape in leaders, historically, what fraction failed within five sessions? O'Neil's and Minervini's published teaching is, at bottom, base-rate research done by hand: study thousands of past big winners, record what they looked like *before* the move, and let the frequencies, not any single story, define the setup. David Ryan's formulation in the master-trader study is the purest statement: study historical models until you can recognize today's closest match. That is reference-class forecasting performed visually.
- Of gaps of this size on this kind of catalyst, what fraction held by the close? (The episodic-pivot rules in the playbook are a codified base rate: a neglected name, a 10%+ gap, huge early volume, holds its gap, is a different reference class from a gap in an already extended name, and the two classes have very different frequencies of follow-through.)

### The proven failure modes

**Base-rate neglect** is the default human setting. Presented with a vivid specific story (a charismatic CEO, a revolutionary product, a dramatic chart), people judge probability by the story's coherence and barely consult the frequency of success for the class. Kahneman and Tversky documented this in the 1970s; it has replicated ever since. In trading it appears as: sizing a biotech binary like a normal breakout because the story is compelling, or treating a parabolic short as routine because the last one worked.

**Overconfidence in stated probabilities** is the second failure, and it is measurable. The calibration literature surveyed by Lichtenstein, Fischhoff, and Phillips (1982) and confirmed by Moore and Healy's 2008 meta-analysis finds a stable pattern: when people say they are 90% confident, the event occurs roughly 70 to 80% of the time. There is no internal signal that distinguishes "true 90%" from "true 70%"; the feeling is identical. Only scored records reveal the gap. This is why §1.7 (calibration training) is not optional enrichment; it is the only known way to find out what your words "likely" and "almost certain" actually mean in frequencies.

**The hedgehog error.** Tetlock's earlier twenty-year study of expert political judgment (*Expert Political Judgment*, 2005) found that experts organized around one big theory ("hedgehogs") forecast worse than pluralistic, self-critical "foxes," and that the average expert was barely better than chance on long-range questions. The trading hedgehog is the one-framework trader: everything is a liquidity cycle, or everything is manipulation, or everything is the one indicator. The fox-like alternative the playbook adopts is structural: several independent confirmation families (price/setup, breadth, options flow, dealer positioning, short volume) that can disagree, with price and the setup deciding and the others setting size and trust, per the personal-quant plan's standing rules.

### The countermeasures

1. **No thesis without a reference class.** The trade card (Part 2, Step 34) forces one line: "Base rate: of my last __ trades like this, __ reached +2R; historical study says roughly __." If both numbers are blank, the trade is a probe at minimum size or it does not happen.
2. **Adjust small from the base rate.** A specific reason ("earnings acceleration is stronger than the typical case") earns a modest adjustment, not a doubling of conviction. Conviction expressed in size must be earned by the record, not by the vividness of the case.
3. **Update in small steps on schedule.** Probabilities are revised at defined checkpoints (the midday read, the pre-close pass in the personal-quant day), not continuously in response to every tick. Continuous updating feels diligent and functions as noise-chasing.
4. **Write the number down before the outcome.** A probability that exists only in memory will be retroactively edited by hindsight bias (§1.6). The card and the journal are the external memory that makes base-rate thinking auditable.

**Proven vs. lore.** Proven: base-rate neglect, overconfidence curves, superforecasters' small-adjustment behavior and superior Brier scores (0.15 to 0.20 typical for superforecasters on tournament questions, vs. 0.25 for chance on balanced binary questions). Lore: any specific claim that a given chart pattern "works 70% of the time" without a stated sample, market, and period. Treat all pattern frequencies, including the playbook's, as provisional until your own journal (Phase J and Phase K) has priced them.

## 1.2 Expected value under uncertainty

### The arithmetic that runs the whole enterprise

Expected value (EV) is the one equation trading cannot opt out of:

**EV per trade = (probability of win × average win) − (probability of loss × average loss) − costs.**

Van Tharp's R-multiple language, adopted wholesale in the playbook, is EV made operational. Define **R** as the dollar risk planned before entry: (entry price − stop price) × position size. Express every outcome as a multiple of R. Then expectancy = average R per trade over a sample, and the only three ways to improve a trading business are to raise average win in R, reduce average loss below 1R's worth of slippage and mistakes, or increase the frequency of positive-expectancy trades (Tharp's "opportunity factor": expectancy × frequency). The master-trader study's worked example deserves repeating because it breaks the most common intuition: six losers at −1R and winners of +0.5, +2, +3, +5R is a 40% win rate and a *positive* expectancy of +0.45R per trade. Add a single −3R mistake loss and expectancy drops to +0.25R. The mistake, not the win rate, was the expensive part.

Poker made this way of thinking famous outside trading. Annie Duke's *Thinking in Bets* (2018) frames every decision as a bet: state the probability, state the payoff, multiply. Her worked form is deliberately crude: a $50 call into a $300 pot with a 25% chance of winning has an expected return of 0.25 × $300 = $75 against a $50 cost, so the call is profitable *regardless of whether this particular hand wins*. The crudeness is the point: an approximate EV computed beats an exact narrative admired. Duke's companion concept, **"resulting"**, judging a decision's quality by its outcome, is the single most corrosive habit in any probabilistic field, and §1.7 and the review loop in Part 2 exist largely to fight it. Sources: https://fronterabrands.com/thinking-in-bets/ ; https://www.antoinebuteau.com/lessons-from-annie-duke/

### What is different about EV in markets (and why poker is only half the model)

Three complications separate market EV from poker EV, and a trader's mind must hold all three:

1. **The probabilities are estimated, not dealt.** In poker the deck is known; pot odds are arithmetic. In markets the "deck" (the true probability that this breakout follows through) is itself an estimate with error bars, usually wide ones. This is why the playbook sizes from *risk* (a controlled quantity) rather than from Kelly fractions computed on estimated edges (an uncontrolled one). Full Kelly on a mis-estimated edge is a ruin machine: Thorp's own teaching, preserved in the master-trader study, is fractional Kelly as a ceiling, then the *smaller* of that ceiling and a fixed-fractional budget of 0.5 to 1% per trade.
2. **The payoff distribution is skewed and path-dependent.** A swing trade is not a binary win/loss; it is a distribution with a managed left tail (the stop), a fat right tail if you let winners run (Qullamaggie's observation that his breakout winners can run 10 to 20× initial risk is what makes a ~30% win rate viable), and a middle that management decisions (partials, trailing stops) actively reshape. EV is therefore partly *manufactured by management*, not merely discovered at entry. This is the cognitive justification for the add/trim and exit steps in Part 2 being as detailed as the entry steps.
3. **Costs are certain while edges are hypothetical.** Spread, slippage, commissions, and the options bid/ask are paid on every trade at 100% probability. Barber and Odean's 66,465-household study (1991 to 1996) is the canonical demonstration: before costs, high-turnover and low-turnover households earned roughly the same; after costs, the most active quintile earned 11.4% a year against a 17.9% market, while the least active earned 18.5%. The entire gap was the trading itself. Every marginal trade idea must clear not zero but the cost hurdle, which is why "do nothing" is the default and the burden of proof sits on action. Sources: https://vaultwealth.com/resources/insights/how-overtrading-can-cost-you-returns/ ; https://www.stockopedia.com/content/overtrading-why-overconfidence-boredom-and-fear-can-wreck-returns-143982/

### The countermeasures

- **Think in R, never in dollars or percentages of price, during the trade.** Dollars trigger wealth emotions; R triggers process evaluation. "Down 0.4R on a planned trade" and "down $4,000" are the same fact with opposite effects on the next decision.
- **Require the EV sentence before entry.** "I estimate ~40% to reach +2.5R before −1R, based on [reference class]; EV ≈ +0.4R before costs; costs ≈ 0.05R." A trade that cannot produce this sentence is a feeling, and feelings are sized at zero.
- **Judge samples, not trades.** EV is a property of a *series*. A single trade has an outcome; only 30+ trades have an expectancy worth the name (Tharp's minimum), and 100 to 200 give a clear picture. Every review practice in Part 2 is built on this unit of analysis.

## 1.3 Pattern recognition vs. narrative fallacy

### Two systems, one skull

The most useful single distinction in this document: **pattern recognition is retrieval; narrative is construction.** They feel identical from the inside ("I see what's happening here") and they have opposite reliability profiles.

**Recognition** is what chess research measured. De Groot (1946/1965) and Chase and Simon (1973) showed that grandmasters do not calculate dramatically deeper than strong club players; they *recognize*. Shown a real game position for five seconds, a master reconstructs 20+ pieces nearly perfectly; shown a *random* position, the master performs no better than a beginner. The skill is a library, estimated at roughly 50,000 "chunks" (meaningful piece configurations), each of which, on recognition, suggests promising moves. Expertise is domain-specific, pattern-indexed, and useless outside the patterns it was trained on. Sources: https://www.chess.com/blog/ghefley/memory-chunking ; https://www.stargazers.co.in/chess/more

Gary Klein's Recognition-Primed Decision (RPD) model, built from studying fireground commanders (26 commanders, average 23 years of service, 156 decision points), found the same architecture in a second field: experts do not generate and compare option lists. They recognize the situation as an instance of a prototype, which primes a single plausible course of action; they mentally simulate it; if the simulation passes, they act; if it fails, they modify or move to the next recognized action. Recognition first, simulation second, comparison rarely. Source: https://idtips.substack.com/p/the-recognition-primed-decision-model

David Ryan, Dan Zanger, and Mark Minervini describe *exactly this* in trading language without citing either literature: study thousands of historical winners until the shapes live in memory (chunk library); scan hundreds of charts a night so recognition stays loaded (Zanger's ~400 charts); trade only the 2 to 4 named setups that match the library (RPD's prototype set). The discretionary lineage in the master-trader study is, cognitively, a chunking program. This is proven convergence, and it tells you how pattern skill is actually built: **volume of classified examples with feedback**, not insight, not indicators.

**Narrative** is the other system. Taleb named its trading form the **narrative fallacy**: the mind's compulsion to bind a sequence of facts into a causal story and then mistake the story's coherence for evidence. Pennington and Hastie's story-model research and the apophenia literature (perceiving meaningful connections in unrelated data; Whitson and Galinsky, 2008) describe the machinery: once a story template is active, confirming details are collected (confirmation bias, Nickerson, 1998), disconfirming details are discounted, and the resulting bundle *feels* like analysis. Sources: https://www.mdpi.com/2673-9461/6/2/17 ; https://averagingup.com/elementary-wordly-wisdom/cognitive-and-emotional-biases/ ; https://clearsignals.cloud/posts/why-smart-people-make-bad-decisions/

The market is a narrative-generating environment of unmatched richness: every price move acquires a headline explanation within minutes, every company has a story department (its investor-relations function), and every trader's feed is an industrial story supply. A story is not worthless; it is *unpriced*. The failure is not having a thesis narrative; it is letting narrative coherence substitute for the three questions that actually carry information: What is the base rate? What would prove this wrong, and at what price? What is the crowd already paying for this story (i.e., what is in the price)?

### The boundary condition that governs both

Kahneman and Klein, after a six-year adversarial collaboration, published their agreement in 2009 ("Conditions for Intuitive Expertise: A Failure to Disagree," *American Psychologist* 64(6): 515–526): intuitive expertise is trustworthy only when **(1) the environment has stable, learnable regularities (valid cues), and (2) the practitioner has had prolonged practice with rapid, unequivocal feedback.** Both men agreed that **subjective confidence is not evidence of validity**; people feel equally certain in low-validity environments (their examples include stock picking and long-range political forecasting) where confidence is worthless. Source: https://github.com/martinmontero/holmes/blob/HEAD/docs/research/wisdom-intuition-knowledge-judgment-v3.1.md

For a trader this is a precise, usable ruling, not a philosophy seminar:

- **High-validity subdomains of trading exist and intuition may be trusted there, after reps:** recognizing a familiar setup's shape and its failure shape; sensing that a tape is "wrong" for a name you have watched for years (Zanger's "they are my buddies"); execution feel (this spread is too wide, this fill is off). These have stable cues and fast feedback.
- **Low-validity subdomains dominate the P&L temptations:** predicting macro turns, calling tops and bottoms, forecasting earnings reactions, knowing what a central bank will do. Here intuition is narrative in a confident voice, and the correct cognitive posture is scenario tables and asymmetry (Druckenmiller's pound-trade construction: enumerate scenarios, price each, require the table to be lopsided) rather than recognition.
- **The practical test for any "gut" call:** Can I name the cue, state how many times I have seen it, and say what happened those times, from records? If yes, it is recognition and gets a hearing. If the answer is a story, it is narrative and gets a probe size at most.

### The countermeasures

1. **Name the pattern or strike the trade.** Every entry must cite a playbook setup by name. A setup name is a claim that this case matches a trained reference class. An unnamed trade is logged as what it is: an off-playbook trade, graded separately, and in the personal-quant system it simply does not occur.
2. **Write the failure shape, not just the success story.** For each setup the card records what its failure looks like (e.g., breakout reverses through the pivot on expanding volume within two sessions). Recognition libraries include failure chunks; narrative only includes the hero version.
3. **Seek the disconfirming fact deliberately.** One line on the card: "The strongest fact against this trade is ___." Medicine calls the failure to do this *premature closure* and found it the single most common cognitive error in diagnostic failure (§1.9.4). Trading's version is falling in love with the first interpretation of a chart.
4. **Keep stories on a leash of levels.** A story may generate a hypothesis; only a price level (entry trigger, invalidation) may generate a trade. Livermore's pivotal point is this rule in 1923 language: the story proposes, the pivot disposes, to borrow the hierarchy McMillan teaches for indicators.


## 1.4 Attention and information triage

### Attention is the binding constraint

Herbert Simon's dictum that a wealth of information creates a poverty of attention is the operating condition of modern trading. The trader's inputs on a single morning include index futures, breadth, sector rotation, rates, currencies, commodities, overnight news on every holding, earnings calendars, analyst actions, options flow, social feeds, and the positions themselves, each with live prices. Working memory holds roughly four chunks at once (Cowan's revision of Miller's 7±2). The gap between input supply and processing capacity is not a personal failing to be fixed by effort; it is a structural fact to be designed around. Every elite field in §1.9 designs around it the same way: **triage before analysis, most things deliberately never looked at.**

### How triage works when it works

Medicine's emergency department is the clearest model. Triage does not diagnose; it *sorts* by two questions: how bad could this be, and how time-sensitive is it? The output is an order of attention, not a set of conclusions. Aviation does the same with its scan discipline and its sterile-cockpit rule (no non-essential conversation below 10,000 feet): attention is protected by phase, not by willpower.

The personal-quant day in `PLAN.md` is a triage schedule wearing trading clothes, and it is worth seeing it that way:

- **07:00 desk health** sorts *machinery* before *markets*: is the system itself trustworthy today? (The aviation preflight, §1.9.3.)
- **08:00 pre-open read** runs in a fixed order (regime, then the day's board, then calendar, then candidates, then engines) so that context is loaded before candidates compete for attention. Order matters: candidates seen before regime get evaluated on their stories; candidates seen after regime get evaluated against it.
- **The execution window, midday read, and pre-close pass** are scheduled *re-triage points*, the only moments new decisions are licensed. Between them, attention is for monitoring defined triggers, not for browsing.
- **The 16:30 review** closes the loop while memory is fresh.

The design principle underneath: **attention is allocated by the schedule and the watchlist, both made in advance, never by the feed in real time.** Whatever shouts loudest (a moving ticker, a viral post, a red position) is, by the availability heuristic, what an un-designed mind will attend to; salience and importance correlate weakly and sometimes negatively in markets, where the loudest moves are usually the most crowded and the most fully priced.

### The specific attentional failure modes

- **Vigilance decrement.** Sustained monitoring degrades measurably within tens of minutes; a trader "watching" eight positions for six hours is, by the afternoon, watching none of them well. Countermeasure: replace continuous watching with **alerts at pre-written levels** (Darvas trading by telegram is the extreme, instructive case: his system needed only end-of-day quotes and resting stops, and the constraint was a feature). For a daily-bar swing trader, the correct monitoring technology is the alert and the resting order, not the eyeball.
- **Attentional capture by open P&L.** A flickering unrealized P&L is engineered to capture attention (it is the slot-machine element of the platform). It carries almost no decision-relevant information beyond what price-vs.-plan already says, and it taxes every other faculty in this document. Countermeasure: default screens show price vs. entry, stop, and target, not dollar P&L; P&L is reviewed at scheduled checkpoints.
- **Information snacking and thesis contamination.** Each additional article, post, and opinion consumed mid-trade is a small, unlogged revision to the thesis by whoever shouted last. Countermeasure: information intake about an open position is scheduled (midday, pre-close) and sourced from a defined list; new *thesis-relevant* facts are logged in the journal (Phase H, Step 68), which forces them to be weighed rather than absorbed.
- **Breadth neglect.** Under attentional load, the mind defaults to the single salient object (my stock) and drops the field (market stage, breadth, group). Weinstein's stage discipline and O'Neil's "M" are attentional prosthetics: three of four stocks follow the market, so the market check is placed *first* in every routine in Part 2, before any individual name is examined.

### Triage rules worth adopting verbatim

1. **Two-list discipline.** A *focus list* (today's actionable candidates with cards, typically 3 to 7 names) and a *watch list* (everything else interesting, reviewed at scheduled passes only). A name moves lists only at a scheduled pass. This is Zanger's funnel: 400 charts scanned at night, a handful traded by day.
2. **The three-question sort** for any new information: Does it change a level (entry, stop, target)? Does it change a probability enough to change size? Does it change the regime call? If none, it is entertainment and is consumed, if at all, outside trading hours.
3. **Sterile cockpit windows.** During the execution window (09:30 to 10:30 in the plan) and during order placement (Part 2, Phase G), no feeds, no chat, no second screen of opinions. Pilots do not improvise this; it is a rule with a name, and it exists because the industry measured what distraction costs.
4. **Pre-loaded context.** The reason the pre-open read exists is so that intraday attention is spent on *deviations from an expected picture* rather than on constructing the picture under fire. Klein's firefighters recognize situations against a pre-loaded library; the trader's equivalent is: know at the bell what a normal day for your names looks like, so the abnormal announces itself.

## 1.5 Emotional regulation: the five named storms

Emotion in trading is not noise added to a rational process; it is a set of specific, evolved programs, each with a trigger, a characteristic distortion, and a characteristic trade it produces. Naming them precisely matters because the countermeasure differs by storm. "Control your emotions" is useless advice; "this is the disposition effect, and the pre-written exit is the countermeasure" is usable. Mark Douglas's *Trading in the Zone* is the practitioner classic here; Brett Steenbarger's *The Psychology of Trading* and his later work add the coach's view that states are trainable and measurable rather than moral qualities. The academic anchors below are the proven layer.

### 1.5.1 Loss aversion and the disposition effect

**The finding (proven).** Prospect theory (Kahneman and Tversky, 1979; Tversky and Kahneman, 1992) established that losses weigh roughly 2.25 times as much as equivalent gains in human choice (popular summaries round to 2 to 2.5×). Shefrin and Statman (1985) predicted the consequence, and Odean (1998) measured it in real brokerage accounts: investors realize gains at a substantially higher rate than losses (in Odean's sample, the proportion of gains realized was about 14.8% vs. 9.8% for losses outside December), and the winners they sold went on to *outperform* the losers they kept by about 3.4 percentage points over the following year. This is the **disposition effect**: sell winners early to lock in the pleasure and avoid regret; hold losers to avoid the pain of making the loss real. It is the exact inversion of every master's exit doctrine (cut losses, let winners run), which is why that doctrine has to be structural (resting stops, pre-written partial rules) rather than aspirational.

**The trade it produces:** the portfolio slowly fills with losers ("my bag") while winners are harvested at +5% that would have paid +25%. The account feels busy and prudent and compounds negatively.

**Countermeasures:** invalidation defined *before* entry and placed as an order or an alert-plus-rule, not a hope; exits evaluated against the plan, not against the entry price (the market does not know your cost; anchoring to it is a second bias stacked on the first); journal grading that scores *execution* separately from outcome, so a correct loss is recorded as a success of the system (Tharp, Minervini, and Schwartz all teach this separation).

### 1.5.2 Recency and extrapolation

**The finding (proven).** People weight recent experience far beyond its statistical share. Malmendier's experience-effects research shows investors' lifetime risk-taking is shaped disproportionately by returns experienced recently and in their formative years; in the trading timescale, the same mechanism makes a setup "hot" after three wins and "broken" after three losses, when both streaks are well inside the setup's normal variance. Tversky and Kahneman's availability heuristic is the engine: recent, vivid outcomes come to mind easily and are therefore judged more probable. Sources: https://www.fsadvice.com.au/article/looking-backward-investing-forward-how-investor-experience-shapes-decision-making ; https://www.preprints.org/manuscript/202510.2175

**The trades it produces:** size creep after wins (the setup feels proven exactly when its sample is smallest and most favorable); strategy abandonment at the point of maximum drawdown, which for a positive-expectancy system is statistically the worst exit point; chasing last week's sector; and fighting the last war in risk management (over-hedging the risk that just hurt, naked to the next one).

**Countermeasures:** expectancy computed on fixed windows (last 30 / 100 trades by setup) and consulted *instead of* the felt sense of the last three trades; size changes allowed only at scheduled reviews (Friday grading, monthly review in the plan) and only within the ladder; a pre-written "normal pain" statement for each setup (Asness's practice for factor drawdowns: depth and duration that are *consistent with* the strategy working), so a normal drawdown is recognized as the strategy's weather, not its obituary.

### 1.5.3 FOMO (fear of missing out)

**The mechanism.** FOMO is loss aversion pointed at a counterfactual: the pain is not of losing money but of *watching others make it without you*. Social feeds industrialize the trigger by publishing only wins, only the best day, only the entry without the exit. Druckenmiller's most instructive confession is a FOMO trade: buying technology in early 2000 after arguing it was a bubble, because watching younger managers make money overrode his analysis, and losing heavily within weeks. His rule drawn from it: if you recognize a trade was done for emotional reasons, exit it on recognition; do not retrofit a thesis.

**The trade it produces:** late entries, extended from any defensible stop, so the FOMO trade carries the worst risk geometry in the book (chasing 5% past a pivot is precisely what O'Neil's 5% rule prohibits, because the stop distance and therefore the size math break); entries with no card, no stop, and no target, because the "analysis" was a price move.

**Countermeasures:** the card rule (no card, no trade) is the structural FOMO cure; a missed move generates a *watchlist entry and an alert*, converting envy into a plan for the next base or pullback (setups recur; Qullamaggie's continuation and Kell's crossback exist precisely to give the second entry a legitimate form); the episodic pivot is the one licensed same-day chase, and it is licensed because its six rules define it in advance. Note the asymmetry: FOMO says the opportunity is unique and expiring; the record says bases, pullbacks, and new leaders form continuously. The second statement is the proven one for a liquid market.

### 1.5.4 Revenge trading

**The mechanism.** After a loss, especially a loss perceived as unfair (a stop run by a wick, a gap through a level, a "should have won" trade), the goal of trading silently changes from *executing positive-expectancy trades* to *erasing the loss and the feeling*. Prospect theory predicts risk-seeking in the domain of losses: a trader down on the day will accept gambles he would refuse when flat, because getting back to zero has convex emotional value. Practitioner literature names the syndrome consistently: immediate re-entry, increased size, off-plan setups, shortened holding periods, and a session that converts one planned −1R into an unplanned −4R day. Sources: http://tronexo.com/psychology-mindset/trading-psychology/ ; https://tradetron.tech/blog/psychology-of-algorithmic-trading-how-emotions-affect-performance

**The trade it produces:** the day's second-worst pattern in any journal audit (after the disposition effect's slow bleed): a tight cluster of escalating, off-plan trades in the hour after a stop-out.

**Countermeasures (structural, in order of strength):** (1) a **daily loss limit with a hard stop on initiating new risk** (the playbook's −2R day rule): at the limit, the terminal closes, by rule decided in calm; (2) a **mandatory delay**: after any stop-out, no new entry for a defined interval (e.g., until the next scheduled decision point, midday) unless it was a pre-written card whose trigger independently fires; (3) the **counterfactual test** from the practitioner literature: "Would I take this trade, at this size, if the previous trade had never happened?" If the honest answer is no, the trade is revenge and is not taken; (4) journaling the loss *immediately*, which sounds soft and is not: writing the R result and the execution grade converts the loss from an open emotional loop into a closed record entry, and the revenge impulse measurably attaches to the open loop.

### 1.5.5 Euphoria and the winner's tilt

**The mechanism.** Winning streaks are as dangerous as losing streaks, through the opposite door: dopamine-mediated confidence, the hot-hand feeling, and self-attribution (wins prove skill; losses were luck). Marty Schwartz's rule is the master's formulation: "My biggest losses have always followed my largest profits," and his practice was to trade *smaller* after big wins and sometimes take a day off as the reward. Druckenmiller's streak doctrine rhymes: know when you are seeing the ball, but the dial-turning he describes happens *inside* a risk framework, and Kovner's is the binding constraint: if a position disturbs your emotional balance, it is too big by definition, whatever the spreadsheet says.

**The trades it produces:** size creep justified by "house money" (mental accounting: profits treated as less real than capital, although the market spends both identically); concentration creep; loosened stops ("give it room, we're up big"); and the first off-plan trade taken at maximum confidence, which is statistically where an unaudited trader's expectancy is lowest.

**Countermeasures:** size is set by the ladder and the setup grade, never by the recent P&L; a rule that size may only *increase* at scheduled reviews; after a large win (define it in advance, e.g., +3R day or a position closing at +5R+), the next trade's size is capped at standard regardless of grade; profits are swept mentally into "capital" at each close, because there is no house money, there is only money.

### 1.5.6 The remaining cast, briefly

- **Anchoring:** entry price, prior high, a round number, an analyst target, any first number becomes a magnet for judgment (Tversky and Kahneman's adjustment heuristic). Trading forms: refusing to sell below cost, "it was $100 last month" as an argument. Countermeasure: all decisions referenced to *levels in the plan and the current structure*, never to cost.
- **Sunk cost / commitment:** size or time already spent becomes a reason to continue (Duke's *Quit* catalogues the bias stack that produces failure to stop). Trading form: holding a broken thesis because of the research hours in it. Countermeasure: kill criteria written at entry (Phase D/E, Steps 35 and 38), phrased as observable events, not feelings.
- **Overconfidence:** the Barber and Odean result (§1.2) is its P&L statement. Countermeasure: calibration records (§1.7) and turnover awareness; if your trade count doubles, your burden of proof doubles with it.
- **Regret and hindsight:** after outcomes are known, the past looks predictable (hindsight bias), which manufactures false lessons ("I knew it") and false guilt ("I should have known"). Both corrupt the journal unless the journal was written *before* the outcome (§1.6).
- **Fear after a loss (the flinch):** skipping the next valid signal, or taking it at half size without a rule for doing so, which silently halves the system's expectancy while keeping its losses. Countermeasure: post-loss size is governed by the drawdown ladder (a written schedule), not by the flinch; if the ladder says standard size, standard size is the disciplined act.

### The meta-countermeasure: state as a position input

Every master above treats the trader's state as *data about position size*, not as a private matter. Soros used his back pain as a (fallible) signal that a position exceeded his understanding; Kovner closed positions that disturbed his balance; Schwartz shrank after extremes in either direction. The modern, less mystical form: a 10-second state check at defined moments (pre-open, before order submission, after a stop-out) rating sleep, agitation, and urge-to-act on a 1 to 5 scale, logged on the card. A state outside the normal band does not require a feeling-based debate; it invokes a pre-written rule (halve size, or stand down). Section 1.8 gives the evidence for why sleep alone justifies such a rule.

## 1.6 Decision hygiene: pre-commitment, checklists, pre-mortems

### The problem hygiene solves: noise

Kahneman, Sibony, and Sunstein's *Noise* (2021) documented that professional judgment varies wildly where it should not: insurance underwriters given identical cases set premiums differing by as much as 55%; judges, physicians, and hiring panels show the same unwanted variability, *within the same person on different occasions* as well as between people. A trader re-deciding the same setup on Monday and Thursday, rested and tired, calm and tilted, is a noise generator pointed at his own account. **Decision hygiene** is the set of practices that reduce noise without requiring the judge to become a different person: structure the inputs in a fixed order, score components independently before forming a global impression, use checklists for the steps that must never be skipped, and pre-commit to the decision rules that stress will otherwise renegotiate. Source: https://www.brijeshdalmia.com/books-reviews/

### Checklists: the evidence is embarrassingly strong

The WHO Surgical Safety Checklist study (Haynes, Gawande, et al., *New England Journal of Medicine*, 2009) introduced a 19-item checklist in eight hospitals across income levels and measured, in 7,688 patients: major complications fell from 11.0% to 7.0% (about one third), and inpatient deaths fell from 1.5% to 0.8% (over 40%). The checklist contained no new medical knowledge; every item was something the teams already knew. It worked by making omission, not ignorance, harder. Aviation's version is older: after the 1935 Boeing Model 299 crash (a superior aircraft lost because a gust lock was left engaged), the industry concluded that the new machines exceeded unaided memory and moved critical sequences onto challenge-and-response checklists that are used by the most experienced pilots most religiously. Sources: https://www.who.int/news/item/11-12-2010-checklist-helps-reduce-surgical-complications-deaths ; https://tallyfy.com/checklist-manifesto/

Gawande's distinction in *The Checklist Manifesto* matters for traders: a good checklist is short, is used at defined pause points, and items are **either do-confirm (verify a step already done) or read-do (perform the item as read)**. The trading checklists in Part 2 (pre-submission, Phase G; pre-close, Phase I) follow that form deliberately: they are not essays, they are 6 to 10 verifiable items at the two pause points where errors are irreversible.

What goes on a trading checklist is determined by your own error history, not by generic advice. The journal's lesson field (Phase J) is the checklist's author: any error class that appears twice graduates to a checklist item. This is the aviation model exactly: checklists are written by accident investigations, one item per way someone has already died. Your capital's accident investigations are in your journal.

### Pre-commitment: Ulysses contracts for traders

Pre-commitment means binding your future self while your present self is calm: resting stop orders rather than mental stops; bracket orders (entry + stop + target submitted as one structure) where the broker supports them; written size ladders that require a scheduled review to amend; daily loss limits enforced, where possible, by the platform rather than by resolve. The cognitive logic is Kahneman's two systems with the roles assigned correctly: let the slow, deliberative system (System 2, in the evening, with the journal open) make the decisions it is good at (structure, size, exits), and restrict the fast system (System 1, at 10:14 a.m., watching a red candle) to recognition and to executing the pre-made decisions. Every "mental stop" is a decision deliberately transferred from your best self to your worst. Kovner's rule, "I know where I'm getting out before I get in; that is the only way I can sleep," is pre-commitment described as a sleep aid, which it also is (§1.8).

### Pre-mortems: imagining failure while it is still cheap

Gary Klein's pre-mortem, popularized by Kahneman in *Thinking, Fast and Slow*: before committing, assume the decision has failed completely, set a date ("it is six months from now; this trade / this setup / this change was a disaster"), and write the history of how it happened, in 5 to 10 minutes, in concrete terms. The technique licenses doubts that optimism and social pressure suppress, and it converts vague unease into named, checkable risks. Sources: https://hub.cissychen.com/investing/decision-training-day27.en.html ; https://gov.capital/10-game-changing-strategies-to-stay-mentally-sharp-under-pressure-the-neuroscience-of-elite-financial-performance/

For a single swing trade, the pre-mortem is one card field and takes ninety seconds: "This trade lost −1R (or worse) because ___." Typical honest answers (the gap was into earnings I mis-dated; the group was rolling over while the stock had not yet; the stop sat inside the normal noise band so I was whipped out before the idea was tested) each map to a specific check or resize *before* entry. For larger commitments (adding a new setup, raising standard risk, starting an options premium program), the full Klein form applies at the Friday or monthly review. The honest limit, noted in the decision-training literature: a pre-mortem lists failure paths, not their probabilities; an imagined disaster is not a likely one. Use it to find fixable flaws and to write kill criteria, not as a veto generator.

### Decision journals: the anti-hindsight device

A decision journal records, *before the outcome is known*: the situation as seen, the options considered, the choice, the probabilities assigned, the expected outcome, and the author's state. Kahneman's warning is the reason for the "before" requirement: once you adopt a new view, you lose the ability to recall what you used to believe; memory rewrites the prior state to match the outcome. The trade card *is* a decision journal entry in compressed form, which is why the personal-quant plan's rule (every trade exists as a card written before entry and a journal row written the same day it closes, no exceptions) is a cognitive intervention, not record-keeping bureaucracy. Without the before-record, review (Phase K) degenerates into storytelling about outcomes; with it, review can score decisions.

## 1.7 Calibration training: learning what your probabilities mean

### Calibration is a trainable, measurable skill

Calibration asks: of all the times you said 70%, did the thing happen about 70% of the time? It is scored with the **Brier score**, the mean squared difference between stated probabilities and outcomes (0 = perfect, 0.25 = chance-level on balanced binary questions). Superforecasters sustain roughly 0.15 to 0.20 in tournament conditions; calibration error (ECE) for the best human forecasters runs around 0.03 to 0.05. The crucial facts for a trader: (1) calibration improves with **scored practice and prompt feedback**, weather forecasters being the classic well-calibrated profession precisely because they predict daily, in numbers, and are scored daily; (2) calibration does *not* improve from unscored experience, however extensive (Tetlock's hedgehog experts had decades of experience and poor calibration); (3) calibration and profit are related as survival, not as identity: calibration research on prediction-market wallets finds calibration's clearest value is in *position sizing*, preventing the terminal error of sizing a true-70% bet as if it were 90%. Source: https://www.convexly.app/blog/overconfidence-bias

### The trader's calibration program

Trading offers an unusually good calibration gymnasium, if the records are kept:

1. **Probabilities on every card.** Each trade card carries one explicit forecast, in a scoreable form: "P(reach +2R before −1R) = __%." Not "I like it," not a target price: a probability of a defined event by a defined horizon.
2. **Score in buckets at the weekly review.** After 30+ cards, bucket forecasts (30 to 40%, 40 to 50%, and so on) and compare stated vs. realized frequencies. The output is a personal calibration curve, and its usual first shape (stated 60s behaving like realized 40s) is the most valuable single page in a developing trader's records, because it reprices every future conviction.
3. **Score setups, not just self.** The same records yield per-setup base rates (§1.1) and per-regime splits, turning the journal into the reference-class library for future cards. This loop, card to score to base rate to better card, is the entire epistemic engine of the discretionary method. It is also precisely the machinery the forecast-engine program on this desk (ledger before display, fixed horizons, public grading) implements at system scale; the human trader's journal is the same idea at personal scale.
4. **Small-stakes reps.** Calibration trains fastest with many scored forecasts. Auxiliary reps that cost nothing: at each pre-open read, record two or three scored micro-forecasts (index closes above/below yesterday's high; a named event's outcome bucket) and score them at the close review. Fifty such reps a month build the probability muscle faster than trade frequency alone ever will, and they carry a side benefit: they teach, viscerally, how often a "70%" day surprises you.
5. **Separate calibration from resolution.** Brier scoring rewards both being calibrated *and* daring to move away from 50% when you know something (resolution). A trader who forecasts 50% on everything is perfectly safe and perfectly useless. The goal is calibrated boldness: extreme probabilities used rarely, earned by reference classes, and scored without mercy.

### What calibration changes in practice

Size. Once a trader knows his stated 75% is a realized 55%, Druckenmiller's "sizing is 70 to 80% of the equation" stops being a slogan and becomes arithmetic: the correct size for the *realized* probability is computed, and the chronic over-sizing that calibration ignorance produces disappears. Calibration also disciplines the A+ grade in the playbook (0.75% risk): an A+ should mean "a setup whose *recorded* base rate and my *recorded* calibration on such setups justify the step-up," not "this one feels special." Feelings of specialness are the uncalibrated variable.

## 1.8 Fatigue and state management: the hardware section

### What is proven, and what is pop psychology

Two popular claims need separating, because one survived replication and one largely did not.

**Ego depletion / "decision fatigue" as a fuel tank: weak evidence.** The claim that willpower is a depletable resource drained by each decision was tested in a large multi-lab Registered Replication Report (2,000+ participants, *Perspectives on Psychological Science*) and the effect failed to reproduce. Traders should therefore distrust the mystical version ("I've made my 35 decisions today") while keeping the practical observation underneath it: long, effortful, stressed days degrade later performance for more ordinary reasons (sleep loss, sustained-attention fatigue, hunger, emotional carryover). Source: https://daytradingtoolkit.com/beginners-guide/avoiding-day-trading-burnout

**Sleep loss: strong, replicated evidence, and worse than it feels.** Van Dongen et al. (2003, *Sleep*) restricted healthy adults to 4 or 6 hours of sleep for 14 days: attention and cognitive performance degraded steadily and cumulatively, with 6-hour restriction producing deficits equivalent to up to two nights of total deprivation by the end, *while participants' own sleepiness ratings plateaued after a few days*. That last clause is the dangerous one: chronic short sleep impairs you past your ability to notice the impairment. Palmer et al. (2024), a systematic review and meta-analysis of over 50 years of experimental sleep-loss research, confirms reliable harm to emotional functioning alongside attention and executive function. A trader-specific literature points the same way: discretion depends on sustained attention, restraint, and updating, the exact capacities sleep loss hits first. Sources: https://daytradingtoolkit.com/beginners-guide/avoiding-day-trading-burnout ; https://theobservermindset.substack.com/p/bad-sleep-makes-your-discretion-less

The trading translation is a rule, not a wellness tip: **a pre-committed sleep floor with a pre-committed consequence.** Example form used in practitioner risk frameworks: under 6 hours, no new discretionary risk today (systems and pre-placed orders may run; the impaired judge does not create new exposure). The rule must be pre-committed because, per Van Dongen, the impaired state includes impaired self-assessment; asking "do I feel okay to trade?" at 08:00 after a 4-hour night is asking the damaged instrument to certify itself.

### The rest of the state stack

- **Time of day and session structure.** Vigilance and self-control are generally best earlier in a rested day and degrade across long unbroken sessions. The personal-quant day already exploits this: the consequential cognitive work (cards, sizing) happens at 08:00, execution is front-loaded into the first hour, and afternoon sessions are for monitoring, pre-close decisions, and review, not for originating complex new analysis. Design your hardest thinking into your best hours; never schedule a playbook change for 15:40 on a Friday after a losing week.
- **Breaks and the vigilance decrement.** Short, real breaks (away from screens) partially restore sustained attention; continuous partial attention does not. The midday read is separated from the morning session by a genuine break in the plan for this reason.
- **Physical state.** Exercise, daylight, regular meals, and hydration are unglamorous and real: mild dehydration and glucose swings measurably impair cognition in laboratory work, and exercise is among the most reliable mood-regulation interventions known. Treat these as part of the trading infrastructure, maintained in winning and losing weeks alike, because losing weeks are when they are abandoned and when they are most load-bearing.
- **Tilt recognition and the circuit breaker.** Define your personal tilt signature in writing while calm (mine might be: checking P&L more than twice an hour; composing justifications for moving a stop; urge to "make it back today"). Any two signatures present = the pre-written consequence fires (no new entries until the next scheduled decision point; stops and planned exits still execute, because standing down never means abandoning risk control). This is the sterile-cockpit principle applied to emotion: the rule is invoked by checklist, not debated by the tilted party.
- **Life load.** Kell's six losing years and Livermore's collapses under personal distress teach the same lesson from opposite ends: a trader who *needs* this month's P&L (rent, debt, a point to prove) has a sizing distortion no technique can offset, and trading through acute life crises converts temporary personal trouble into permanent capital damage. The structural answers are boring and decisive: living expenses separated from trading capital (Livermore's trust arrangement, in modern dress), a hard rule for standing down during acute life events, and position sizes small enough that a maximum-loss day is an annoyance, not an emergency. Emotional regulation is mostly *arranged in advance*, at the level of accounts and calendars, not performed in the moment at the level of willpower.

## 1.9 How elite performers in adjacent fields structure the same faculties

Each field below is included because it isolated one faculty under extreme selection pressure and industrialized the solution. The transfer column is the point; the differences are stated too, because cargo-culting another field's rituals without its feedback structure is narrative fallacy in a uniform.

### 1.9.1 Chess: the library and the post-mortem

**Structures:** (a) expertise as a 50,000-chunk recognition library built by studying master games and one's own games (de Groot; Chase and Simon, §1.3); (b) the **post-game analysis ritual**: elite players analyze every serious game afterward, ideally first without an engine (recording their in-game reasoning, including the candidate moves they rejected and why) and only then with one, so the *reasoning*, not just the moves, gets audited; (c) candidate-move discipline: strong players generate a small set of plausible moves from recognition, then calculate; they do not calculate everything; (d) time management as an explicit resource: the clock is spent where the position is critical, and "critical position recognition" is itself a trained judgment.

**Transfers to trading:** study historical winners as chess players study master games (Ryan's drill); review trades first from your card and journal (your recorded reasoning) before looking at "what the chart did next" with hindsight (the engine); keep the candidate list small (named setups); spend analysis time disproportionately at critical junctures (entries, invalidations, earnings) and automate the rest.

**Does not transfer:** chess has perfect information, no luck, and a stable rule set for centuries; its feedback is nearly noiseless. Trading's environment validity is far lower (§1.3), so chess-grade confidence in recognition is unattainable and must not be imitated. Chess teaches the *training method*; it must not teach the *certainty*.

### 1.9.2 Poker: EV fluency, bankroll rules, and table selection

**Structures:** (a) every decision priced in EV against pot odds, in real time, as a habit of speech ("I'm getting 3 to 1, I need 25%"); (b) **bankroll management** as a professional absolute: play only stakes where your roll is many multiples of the maximum plausible downswing (the direct ancestor of fixed-fractional sizing and the Kelly discussion in §1.2); (c) **game/table selection** as a primary edge source (the best decision is often which game to sit in; the trading equivalent is regime and setup selection: most money is made by *choosing favorable conditions*, Weinstein's Stage 2 and Druckenmiller's liquidity regime, rather than by outplaying unfavorable ones); (d) tilt management as a named, studied specialty, including quitting a session while ahead in skill terms but impaired in state terms; (e) HUDs and databases in online poker: every hand recorded, statistics by position and situation reviewed offline (the journal, with better tooling).

**Transfers:** EV as the native language of the card; sizing as survival math; the legitimacy of *quitting* (walking away from a bad regime is a skill, Duke's *Quit* thesis); review by database query rather than by memory.

**Does not transfer:** poker's probabilities are computable from a known deck and its feedback volume is enormous (hundreds of hands a session vs. a swing trader's handful of trades a week). A trader gets far fewer, noisier reps, so a trader's process must extract more from each rep (hence the heavy journal) and must be far more suspicious of short-run results than a poker player's need be.

### 1.9.3 Aviation: checklists, sterile cockpits, and the non-punitive error culture

**Structures:** (a) checklists at pause points, challenge-and-response, used most faithfully by the most experienced (§1.6, with the B-17 origin); (b) **standard operating procedures** that define normal operations so completely that improvisation is itself a flagged event; (c) the **sterile cockpit** rule protecting attention in critical phases; (d) crew resource management: the junior officer is *required* to speak up, flattening authority gradients that suppress disconfirming information; (e) the Aviation Safety Reporting System: voluntary, confidential, non-punitive incident reporting, which made near-misses into a shared database instead of hidden shame, and is widely credited as a foundation of aviation's safety curve; (f) simulator training for rare catastrophic events, so the first time a pilot meets an engine fire is not with passengers aboard.

**Transfers:** trading checklists and SOPs (Part 2 is an SOP); sterile windows during execution; a personal "ASRS": near-misses (the stop you almost moved, the size you almost doubled) logged in the journal with the same seriousness as losses, because near-misses are free accident data; simulation for rare events: rehearse, in calm, the gap-down morning, the halted stock, the platform outage, the earnings surprise (Minervini's and Kovner's contingency rehearsal, §1.6 and Part 2 Step 12); and the cultural rule for self-review: the journal investigates *the system and the decision*, never prosecutes the person, because a punitive journal gets falsified or abandoned within a month.

**Does not transfer:** aviation's environment is engineered and its physics stable; two pilots flying the same approach *should* do the identical thing. Trading retains genuine judgment (§1.3's validity map); SOPs bound the judgment, they cannot replace it.

### 1.9.4 Medicine: differential diagnosis, premature closure, and M&M rounds

**Structures:** (a) the **differential diagnosis**: before settling, the clinician must list plausible alternatives and what evidence would distinguish them. Its absence is lethal and measured: Graber, Franklin, and Gordon's analysis of 100 internal-medicine diagnostic errors (*Archives of Internal Medicine*, 2005) found cognitive factors in 74% of cases, with **premature closure** (settling on the first plausible diagnosis and stopping the search) the most common single cognitive failure; broader reviews put cognitive factors as primary or contributory in over 75% of diagnostic errors, with diagnostic error affecting roughly 8 to 15% of hospital admissions in US estimates. Sources: https://www.deltapsychology.com/articles-for-doctors/clinical-decision-cognitive-biases ; https://www.mja.com.au/journal/2020/213/7/diagnostic-error-incidence-impacts-causes-and-preventive-strategies
(b) **cognitive timeouts**: a deliberate pause to ask "what else could this be, what doesn't fit, what's the worst case I might be missing?"; (c) **morbidity and mortality (M&M) rounds**: scheduled, structured, non-blame review of adverse outcomes and near misses, selecting cases for *lessons about cognitive and system issues*, with concrete "bottom lines" produced (Ottawa M&M model); (d) diagnostic checklists and second opinions as routine debiasing structure rather than admissions of weakness.

**Transfers, almost word for word:** the thesis step in Part 2 requires a mini-differential: the bull case, the bear case (strongest fact against), and the "what else could this chart be?" alternative (a distribution top can mimic a base; an episodic pivot can be a one-day wonder). The Friday grading and monthly review are M&M rounds: adverse trades and near-misses presented from the journal, analyzed for cognitive vs. system causes, closed with a bottom line that becomes next week's single focus rule. The cognitive timeout is the pre-submission checklist pause (Step 52).

**Does not transfer:** the physician's feedback, though imperfect, eventually arrives as a diagnosis confirmed or refuted; the trader's "diagnosis" (thesis) can be right and lose money or wrong and make it, permanently. Trading review must therefore grade the *reasoning against what was knowable at the time* (the card), which medicine can sometimes shortcut with the autopsy result. Traders get no autopsies; they get prices. This is another reason the before-record is sacred.

### 1.9.5 Fire and military command (brief, because §1.3 covered the theory)

Klein's fireground work adds two operational structures worth importing directly: **mental simulation as a go/no-go gate** (before acting, run the plan forward in imagination; if the simulation snags, the plan is revised or rejected; Part 2 Step 44 formalizes this as the pre-entry simulation), and **the commander's intent / mission command tradition** from military practice: orders state intent and constraints so completely that subordinates (here: your future, stressed self; or an automated order) can execute correctly without further communication. A bracket order with a stop, a target, and a time rule *is* mission command for a position: intent and boundaries, set by the calm commander, executed by whoever is on duty when the moment comes.

### 1.9.6 The convergence table

| Faculty | Trading form | Chess | Poker | Aviation | Medicine |
|---|---|---|---|---|---|
| Base rates | Setup expectancy from journal | Opening statistics | Hand-history database | Fleet reliability data | Disease prevalence (pre-test probability) |
| Pattern library | Historical winner study | 50,000 chunks | Hand-reading ranges | Type-rating experience | Illness scripts |
| Narrative guard | Named setup or no trade | Analysis before engine | Range, not a story about one hand | SOP over improvisation | Differential before diagnosis |
| Attention | Triage schedule, alerts | Clock discipline | Table selection | Sterile cockpit | Triage itself |
| Pre-commitment | Resting stops, brackets | (Limited analog) | Bankroll rules | Checklists, SOPs | Order sets, timeouts |
| Failure review | Friday grading in R | Post-game analysis | Database review | ASRS, accident investigation | M&M rounds |
| State rules | Sleep floor, loss limits | Rest between rounds | Quit the session | Duty-time regulations | Duty-hour limits |

Read the table's diagonal: every field independently concluded that **unaided, unstructured expert judgment is not the product; the structure around the judgment is the product.** That is the thesis of Part 1, and Part 2 is its implementation.

---

# PART 2: ALL OF THE STEPS

## 2.0 How to use this sequence

The sequence below follows **one trade** through its entire life. Steps are numbered continuously, 1 to 88, and ordered as they occur in time; phases group them for navigation. A trade that skips a step has not found a shortcut; it has created an unrecorded decision, and unrecorded decisions are where every failure mode in Part 1 lives.

Conventions:

- "The book" means total trading capital under this system. All percentages are of the book unless stated.
- R is defined at Step 40 and used thereafter. Nothing before Step 40 may commit capital.
- Worked numbers use the playbook's example scale where helpful: a $100,000 book, 0.5% standard risk = $500 = 1R. Substitute your own book size; the arithmetic is identical.
- Times follow the personal-quant day (America/New_York). A trader in another structure keeps the *order* and adjusts the clock.
- For options expressions, stock-specific steps have options variants noted inline; the sequence does not fork.

---

## Phase A: The evening before (preparation of self, book, and arena)

**Step 1. Close the previous day's loop first. [D]**
Before any preparation for tomorrow, confirm yesterday's journal rows are complete and yesterday's review actions are either done or explicitly carried forward. An open loop from yesterday (an unjournaled trade, an unexplained fill) is worked first. Preparation built on an unreconciled book is fiction.

**Step 2. Verify the book against the broker. [A]**
Read the broker's actual state: cash, buying power, positions, working orders, fills since the last check. Compare position by position against your records. Any discrepancy is resolved tonight, not discovered tomorrow mid-trade. (On this desk: check against the capital epoch and overnight fills, per the 07:00 health block; the evening version catches the same errors twelve hours earlier.)

**Step 3. Compute the book's vital signs. [A]**
Equity; drawdown from equity peak in %; current open heat (sum of all open positions' planned risk, in % and in R); realized R today and this week; unrealized R marked at the close. Write the five numbers at the top of tomorrow's page. These numbers, not feelings, determine which rung of the drawdown ladder you are on.

**Step 4. Apply the drawdown ladder to tomorrow's permissions. [D]**
Per the playbook: at −5% from peak, gross size × 0.75; at −10%, × 0.5 and A+ setups only; at −15%, stop, full review, restart at minimum size. Also apply the day/week breakers: a −2R day or a −4 to −5R week changes tomorrow's status (reduced size, or stand-down) *tonight*, while the decision is cheap. Write tomorrow's status word at the top of the page: FULL, REDUCED, A-ONLY, or OFF.

**Step 5. Check the human. [J+D]**
Rate, honestly, in writing: sleep last night (hours), physical state, emotional load (life events, conflicts, celebrations), urge to trade (boredom and "need to make it back" both count as high). Apply the pre-committed state rules from §1.8: e.g., under 6 hours of sleep, tomorrow is no-new-discretionary-risk; acute life crisis, tomorrow is OFF regardless of the book. This step is [D] in enforcement even though the rating is [J]: you report the state, the rule decides.

**Step 6. Review the calendar of the arena. [J]**
Tomorrow's scheduled events, in time order: macroeconomic releases (and their consensus and prior values), central bank speakers, Treasury auctions, index rebalances, expirations (weekly/monthly/quarterly, 0DTE environment), and any market holiday or early close in any market you trade. For each, note whether it is a *size event* (trade smaller or not at all around it), a *volatility event* (options pricing changes), or background. An unscheduled-event note is also written: what kind of surprise would most damage the current book?

**Step 7. Read the regime: market stage first. [J]**
Answer Weinstein's question in writing before looking at any individual stock: what stage is the market in (1 basing, 2 advancing, 3 topping, 4 declining), where are the indices vs. their 50-day and 200-day averages, and what did breadth do today (advance/decline, % of stocks above their 50-day, new highs vs. new lows, distribution or follow-through day count in O'Neil's terms)? Five lines maximum. This is the regime note the playbook requires, and its brevity is enforced so it actually gets written nightly.

**Step 8. Read the intermediate context. [J]**
Sector and group rotation (which groups lead, which are rolling over), volatility state (VIX level and term structure, IV percentile of the indices), dealer positioning / gamma regime for tomorrow if you use it (long-gamma pinning vs. short-gamma amplification expectation), credit and rates direction if they have been driving equities. One or two lines each, only where they would change a decision. Anything that would not change a decision is not written; the note is a decision document, not a market diary.

**Step 9. State the regime posture for tomorrow. [J+D]**
Compress Steps 7 and 8 into the week's posture word from the plan (PRESS, NORMAL, PROTECT) as it applies to tomorrow, with one sentence of justification. The posture sets tomorrow's defaults: maximum new trades, whether probes are allowed, whether overnight risk may be added, and which setup grades are tradeable. A posture that is not written does not exist, and tomorrow's excited self will assume PRESS.

**Step 10. Audit every open position against its plan. [J+D]**
For each open position, in its journal record: restate the thesis in one line, the invalidation, the stop's current location, the target(s) and partial rules, days held vs. expected holding period, upcoming events in the name (earnings date above all), and unrealized R. Then Tudor Jones's daily question, answered afresh: *assuming this position is wrong, where exactly does the plan exit, and is that exit still mechanically in place?* Any position whose thesis you can no longer state is flagged for exit at the open, by rule.

**Step 11. Move what the plan says to move, tonight, in the order system. [D]**
Trailing stops are raised where the plan's rules say so (never lowered, ever; a stop that moves down in this step reveals a thesis change that must be written as such and sized accordingly). Alerts are set or corrected. Any orders that should be working before the open (e.g., a stop on a position in a name reporting overnight) are placed tonight. Do not leave for the morning anything the evening can do; the morning is for new information, not for yesterday's clerical work.

**Step 12. Run the disaster rehearsal, 3 minutes. [J]**
Kovner / Minervini contingency practice (§1.6): pick the two worst plausible tomorrows for the current book (e.g., largest position gaps −8% on news; index breaks its 50-day on volume with your book fully long) and state, in writing, the exact actions for each. File it where tomorrow's self will see it. When the bad morning comes, you will execute a rehearsed plan instead of composing one while impaired.

**Step 13. Set the environment. [D]**
Workspace prepared tonight: platform layouts, watchlist columns (price vs. levels, not dollar P&L, per §1.4), phone silenced plan for the sterile windows, calendar reminders for the day's decision points (pre-open read, execution window, midday, pre-close). Friction is a strategy variable: every click between a trigger and an order is a place for a [D] step to be renegotiated.

**Step 14. Stop. [D]**
Preparation ends at a set time. No charts after the cutoff except by exception that is itself logged. Sleep is a position (Step 5 tomorrow depends on it), and the last trade of the evening session is the decision to protect tomorrow's instrument: you.

## Phase B: Pre-open (the morning of the trade)

**Step 15. State check, again, 30 seconds. [J+D]**
Sleep hours, body, mood, urge. Compare with Step 5's forecast; apply the state rules to produce today's final status word if it differs from last night's. Log all three lines (Step 5 rating, Step 15 rating, status word). Discrepancies across a month of these logs are calibration data about your own self-knowledge.

**Step 16. Desk / machinery health. [D]**
Broker connection, data feed sanity (are quotes live and plausible?), platform and order-routing status, any corporate actions overnight in held names (splits, symbol changes), and on an automated desk, the inspection verdict (READY / NOT READY, open defects named). No trading judgment is exercised on machinery that is not known-good (the plan's 07:00 rule). A defect found here converts the day to PROTECT until cleared.

**Step 17. Overnight tape: what actually happened. [J]**
Index futures vs. yesterday's close and vs. fair expectations; overseas markets; rates, dollar, oil, gold moves that matter to your names; the pre-market action in held positions and focus-list names. For each, one classification: *confirms* the regime note, *complicates* it, or *invalidates* it. Only the third category earns more than a line.

**Step 18. News audit on held and focus names. [J]**
Earnings released, guidance, analyst actions, regulatory or legal news, management changes, offerings / insider transactions, sector news. For each item: does it touch a thesis, a level, or an event date? Items that touch none are discarded on the spot (triage, §1.4). Items that touch a thesis go to that position's record *now*, with the action (hold per plan / tighten / exit at open) decided in this step, not at 09:47 under fire.

**Step 19. Gap and event repricing. [A+J]**
For any held name gapping materially: recompute the position's risk at the gapped price vs. its stop (a gap toward the stop shrinks remaining risk; a gap through it realizes more than 1R; record the expected slippage honestly). For any focus name gapping: recompute whether the setup still exists at the new price (an episodic pivot may have been *created* by the gap; a breakout candidate may have gapped beyond the 5% chase limit and been *destroyed* by it). Arithmetic first, then judgment about what the arithmetic means.

**Step 20. Revise the regime note if the morning earned it. [J]**
Update Steps 7 to 9 only on evidence, and mark the revision as a revision with its reason. Silent regime drift (the note quietly stops matching what you believe by 11:00) is a noise source; a marked revision is a decision that review can grade.

**Step 21. Build today's focus list. [J+D]**
From the standing watchlist, tonight's candidates, overnight developments, and open positions needing decisions, produce today's focus list: the small set (typically 3 to 7 names) that may receive capital or active management today, each with its card status (card complete / card needed / monitor only). Everything not on this list is, by rule, not traded today. The single exception is the fully-defined episodic pivot (Step 30), and even it must pass through card-writing (Phase D) before entry.

## Phase C: Watchlist construction and candidate work (the funnel)

*This phase runs nightly for tomorrow and is refreshed pre-open; it is written here once, in full, because its steps are where most trades are actually won or lost.*

**Step 22. Run the mechanical screens. [A+D]**
The playbook's quantitative gates, applied without discretion: trend template (Minervini's eight criteria), stage filter (Stage 2 only for longs), liquidity floor (dollar volume and options spread quality sufficient to enter and exit at your size for a small fraction of daily volume), relative strength vs. index and vs. group. Screens produce a *candidate pool*, typically dozens of names. A screen is a base-rate device: it defines the reference class inside which judgment will operate.

**Step 23. Apply the fundamental filter where the playbook requires it. [J+A]**
For the discretionary stock playbook: earnings and sales acceleration, margin trend, and a catalyst or "new" element (O'Neil's C, A, N), quality checks in the Asness sense (profitability, safety) as a coarse screen. Record pass/fail and the key figures; do not write essays. Names failing the filter are not "bad companies"; they are outside this reference class and go back to the watch pool.

**Step 24. The chart pass: pattern recognition, in bulk. [J]**
Review each surviving candidate's chart, weekly then daily, at reading speed (Zanger's and Ryan's drill: this is where the chunk library earns its keep). For each name, one of four verdicts, recorded: **(a) Setup present** (name the playbook setup and the pattern's stage within it, e.g., VCP, third contraction); **(b) Setup forming** (state what is missing and the level that would complete it; set the alert); **(c) No setup** (discard without regret); **(d) Setup failed / distribution** (remove or short-watchlist, per mandate). Speed is a feature here: recognition that requires ten minutes of squinting is usually narrative (§1.3).

**Step 25. Study the candidate against its historical models. [J]**
For each (a) verdict, compare against the library: the 2 or 3 closest historical examples of this setup in this kind of name (from your annotated collection, Ryan's method) and how they behaved: typical time to follow-through, typical failure shape, typical maximum favorable excursion in R. This is the reference-class step that feeds the base-rate line on the card (Step 34). If you cannot find your examples, your library, not the market, is the bottleneck; note it as homework, and grade the trade a probe at best.

**Step 26. Context check per candidate. [J]**
Group strength (is the group leading, and is this name leading within it?), the name's behavior during the last market pullback (held up = sponsorship; collapsed = distribution), short interest and recent short volume (fuel and risk, §7.1 of the master study), options flow if available (confirming, neutral, or contrary; never sufficient alone), and crowding (is this idea already everyone's trade? crowding does not veto, but it reprices the exit).

**Step 27. Event and earnings clearance. [A+D]**
For each candidate: exact earnings date and expected move; any other dated catalyst (FDA, investor day, lockup expiry, index event); days to event vs. intended holding period. Apply the playbook's earnings rule: no new naked stock position within 3 sessions of earnings unless the trade *is* the event trade (an EP, or a defined-risk options structure sized for full loss). Names failing clearance are deferred with their alert intact; deferral is a decision, recorded as such.

**Step 28. Rank and cut to the focus list. [J]**
Rank surviving candidates by: setup quality against its models, risk geometry (distance to invalidation as % and vs. ADR, tighter is better because it buys size at fixed R), regime fit, and correlation with the existing book. Cut to the focus-list size your attention budget allows (§1.4). The cut is a trade-quality act: five names you can manage perfectly beat fifteen you can manage approximately. Names cut today stay on the watchlist with alerts; nothing is lost by waiting, which is precisely what FOMO (§1.5.3) denies and the record refutes.

**Step 29. Write the one-line idea for each focus name. [J]**
Before any card is built (§Phase D), state the idea in one sentence of the form: "[Name] is [pattern/context]; if [trigger], then [expected behavior]; wrong if [invalidation]." If the sentence cannot be written, the idea is a mood. This sentence is also tomorrow's recognition cue: at the trigger, you will *recognize* the pre-written situation (RPD, §1.3) instead of inventing one.

**Step 30. Handle the intraday exception class explicitly. [D]**
Episodic pivots and true news shocks arrive unannounced and cannot pass through last night's funnel. The rule that governs them: they may enter today's focus list in real time *only* if they satisfy their full written definition (for an EP, the six rules: real surprise, neglected base, gap clears the range, huge early volume, entry through the opening-range high with stop at the day's low, stop distance ≤ 1× ADR) *and* a complete card (Phase D) is written before entry. An exception that skips the card is not an exception; it is an impulse with a story.

## Phase D: The trade card (idea formation made auditable)

*One card per trade. Written before entry. No card, no trade.*

**Step 31. Name the setup. [D]**
One of the playbook's named setups, or the trade does not proceed. The name selects the reference class, the entry rule, the stop rule, the management rules, and the journal's statistics bucket. (Current playbook names, master study §7.2: VCP Breakout; Breakout Continuation; Episodic Pivot; Cycle Continuation (Wedge Pop / Crossback / Base 'n Break); Stage 2 Pullback; and the options expressions A to D.)

**Step 32. Grade the setup. [J]**
A+, A, B, or Probe, against written grade criteria (pattern quality vs. models, regime fit, group leadership, catalyst clarity, risk geometry). The grade is not decoration: it sets the risk fraction at Step 41 (0.75% / 0.5% / 0.25% classes). Grading criteria live in the playbook document; if you find yourself grading by enthusiasm, return to Step 25's models and grade against them.

**Step 33. Write the thesis statement. [J]**
Three to five sentences, in the differential form borrowed from medicine (§1.9.4):
- **Primary thesis:** what is happening and why it should pay (who is buying/selling and why they will continue: institutions accumulating a leader, a re-rating after a surprise, a squeeze of crowded shorts).
- **Strongest fact against:** the best bear case, stated fairly (variant perception, Steinhardt: what consensus believes, what you believe instead, why, and the timeframe that will prove it).
- **Alternative reading:** what else this pattern could be (a base that is actually distribution; a breakout that is actually a climax), and what observation would distinguish them.
A thesis that cannot state its opposition has not been thought; it has been felt.

**Step 34. Write the base rate and the probability forecast. [A+J]**
Two entries (§1.1, §1.7): (a) the reference class frequency: "Setups like this in my record: N = __, reached +2R before −1R in __%; published/historical study suggests roughly __%." (b) This trade's forecast, adjusted small from the base rate for stated specifics: **P(reach target zone before invalidation) = __%**, plus, where useful, P(gap/event disruption) and the expected holding period in sessions. These numbers will be scored. Write them like it.

**Step 35. Define the catalyst and the timing. [J]**
Why now, in one of three honest forms: (a) a dated catalyst (earnings already reported (EP), a product/regulatory event on [date], a sector catalyst); (b) a technical timing event (the pivot, the opening-range high, the pullback turn), with the catalyst being institutional flow itself; or (c) no identifiable catalyst, which must be admitted and which lowers the grade (a pattern without a reason for *now* often resolves as *not yet*, at the cost of time and a stop's worth of noise). Also state the **time stop**: the date or session count by which, if the trade has not progressed, the thesis is considered failed on time even if price has not hit the stop (Bacon's "cut in days if the market does not confirm" is this rule in macro dress).

**Step 36. Run the pre-mortem on this card. [J]**
Ninety seconds, Klein's form (§1.6): "It is [time-stop date]. This trade closed at −1R or worse. The most likely story is: ___." Write the single most likely failure story, then check whether it is preventable *now* (mis-dated earnings, stop inside the noise band, group rolling over, size too big for the name's gap history). Fix what is fixable on the card; if the failure story is both likely and unfixable, the trade is declined and the decline is logged (declined trades are data; log them as zero-R journal rows under Step 75).

**Step 37. Check correlation and book fit. [A+J]**
Against the current book: same group/sector exposure, same factor (all high-beta momentum longs are one trade wearing several tickers, Kovner's correlation rule), shared event exposure (three names reporting the same week is a portfolio event, not three independent ones). Compute the book's heat *if this trade is added* (Step 42 does the arithmetic; this step supplies the judgment about what counts as correlated).

## Phase E: Risk definition and sizing (the arithmetic heart)

**Step 38. Define invalidation as a price structure, not a percentage. [J]**
The invalidation is the price behavior that proves the thesis wrong: below the low of the final VCP contraction; below the breakout day's low; a daily close below the pivot on expanding volume; below the pullback low. State it as an observable event with a level, and state *which* confirmation the setup's rule requires (intraday breach vs. closing breach), in writing, per the playbook's per-setup convention. A percent-from-entry stop ("−7%") is acceptable only where the playbook defines it so (O'Neil's rule); a structure-based stop is preferred wherever the chart offers one, because it ties the exit to the idea's falsification, not to an arbitrary pain threshold.

**Step 39. Set the stop price and the stop distance. [A]**
Stop price from Step 38. Stop distance = |entry trigger price − stop price|, in dollars and as a % of entry, and as a multiple of the name's ADR(20). Apply the geometry gates: Qullamaggie's rule (if stop distance > 1× ADR, the trade's asymmetry is gone; skip or restructure); the playbook's target that a VCP stop should be only a few % away; for options structures, the equivalent (max loss of the structure, or the underlying level that voids the structure's thesis, whichever management rule the playbook assigns).

**Step 40. Fix 1R in dollars. [A+D]**
1R = book equity × risk fraction for this trade's grade. Worked examples on a $100,000 book: standard 0.5% → **1R = $500**; A+ 0.75% → $750; Probe / deteriorating regime 0.25% → $250. Apply the drawdown-ladder multiplier from Step 4 (at −10% from peak, all fractions halve, so standard risk is effectively 0.25% until recovery). Write 1R on the card. This number is now fixed for the life of the trade; every later R statement refers to it, including after partial exits.

**Step 41. Compute position size from the stop. [A]**
Shares = 1R ÷ stop distance per share. Worked example (the master study's, on a $50,000 book at 0.75% for continuity): entry $80, stop $76, distance $4, 1R $375 → 93 shares ≈ $7,440 position ≈ 14.9% of book. Note what the formula does automatically: a wider stop buys fewer shares; risk is invariant, enthusiasm is not consulted. For options: contracts = 1R ÷ max loss per contract (for a defined-risk spread, (width − credit) × 100; the master study's example: a 5-wide credit spread collecting $1.20 has max loss $380 per contract, so at 1R = $375 the position is exactly 1 contract). Round *down*, always; rounding up is a size increase smuggled in as arithmetic.

**Step 42. Check the portfolio constraints. [A+D]**
Verify, with numbers on the card: (a) position size ≤ single-name cap (20% of book at cost; 30% only as a winner that grew there under a trailing stop); (b) new total heat = existing heat + this trade's risk ≤ heat cap for the regime (≤5% strong Stage 2, ≤3% transitional, ≤1.5% Stage 4 / PROTECT); (c) options aggregates if applicable (total short-premium max loss ≤ 3% of book; long-premium at risk ≤ 1%, excluding the separate annual tail budget); (d) correlated-cluster heat from Step 37 ≤ its limit. Any failure is resolved by shrinking the trade or declining it, never by amending the cap in the moment. Cap amendments live at monthly reviews only.

**Step 43. Price the trade: targets and expected value. [A+J]**
Write Target 1 (the partial-profit zone, typically +2R to +3R or the first supply level, whichever the setup's rule uses), Target 2 / runner objective (measured move, prior high, trailing rule), and the resulting reward:risk at entry. Then the EV sentence (§1.2) using Step 34's probability: EV ≈ P × (expected gain in R) − (1 − P) × 1R − costs in R. Apply Tudor Jones's screen loosely (he demands 5:1; the swing playbook's structure, partials at 2 to 3R plus a trailed runner, is how a lower headline ratio still manufactures asymmetry) and the playbook's floor: if honest EV after costs is not clearly positive, decline. Expected value computed on a fantasy probability is worthless, which is why Step 34 forced the probability to stand next to its base rate.

**Step 44. Mentally simulate the trade's life. [J]**
Klein's RPD gate (§1.9.5), run as a film, 60 seconds: the entry fills; the first hour; a normal pullback toward the pivot (does it breach the stop? should it?); the first target approaches (hands execute the partial rule without debate because it is written); a bad day in the market (does the plan hold, tighten, or exit?); the time stop arrives with the trade flat (exit, per Step 35). Any scene where you do not know what you would do is an unfinished card. Finish it now or decline the trade.

**Step 45. Write the management plan in full. [D]**
On the card, as imperatives addressed to your future self: entry order (Step 47 to 49), stop order/mechanism, partial rule (fraction and level), trailing rule (indicator and timeframe, e.g., close below 10-day / 20-day MA, or stop raised to breakeven after the Target 1 partial, per setup), add rule (Phase H's conditions, or "no adds" stated), event rule (what happens the session before earnings if still held), time stop (Step 35), and the exit-if-thesis-breaks condition (a non-price falsifier, e.g., guidance cut, group breakdown). When this step is complete, the trade no longer needs its author; it needs an operator. That is the design goal.

**Step 46. Final card review and signature. [D]**
Read the card once, end to end, as if it were another trader's and you were the risk manager (Steinhardt's morning-meeting posture: defend it under hostile questioning). Check: named setup, grade, thesis with opposition, base rate + probability, catalyst/timing + time stop, pre-mortem, invalidation, stop, 1R, size, constraints, targets, EV, management plan. Any blank = the card is not done. Time-stamp and file it. **The card's existence and timestamp are the proof that every prior step happened before entry, which is what makes the review in Phase K honest.**

## Phase F: Order selection (translating the plan into market instructions)

**Step 47. Choose the entry expression: stock or options structure. [J]**
If the mandate allows both, decide by the playbook's premium table (master study §7.4), not by habit: IV percentile low + dated catalyst + need for convexity → buy premium (debit vertical default; naked long only with a theta budget and an exit date); IV rich + range/exhaustion + no binary inside the trade's life → sell premium only winged and sized for a 2 to 3σ day; neither column clearly satisfied → stock, a debit vertical, or nothing. For options, also record: structure, strikes, expiry (with the rule for why that expiry: enough time for the thesis, not so much that you rent irrelevant months), the Greeks that dominate the position (delta now, theta per day, vega exposure), max loss, breakevens, and the IV percentile at entry. Natenberg's question must be answerable in one line: *what volatility am I buying or selling, at what price vs. what I expect to be realized?*

**Step 48. Choose the order type for entry. [J+D]**
The core menu and its guarantees (proven mechanics, not opinion): a **market order** guarantees execution, never price (it crosses the spread and walks the book in thin names; slippage is yours); a **limit order** guarantees price-or-better, never execution (the trade may run without you; partial fills are possible); a **stop (stop-market) order** sleeps until the trigger trades, then becomes a market order (the breakout-entry and protective-stop standard; it guarantees the trigger is honored, not the fill price; gaps fill through it); a **stop-limit order** guarantees price but can fail to execute entirely in a gap, which for a *protective* stop converts a controlled loss into an uncontrolled one, and is therefore generally wrong for stop-losses and occasionally right for entries where you refuse to chase. Match to the setup: pivot breakouts commonly use a stop-market buy just above the pivot (Darvas's buy-stop, modernized) or a limit with a pre-set chase ceiling; pullback entries use limits at the zone; opening-range-high entries (breakout/EP) use a stop at the ORH after the range forms. Write the choice and its reason on the card. Sources for the mechanics: https://fortraders.com/blog/understanding-order-types-market-limit-and-stop-orders ; https://cursa.app/en/page/forex-market-structure-how-currency-trading-works-in-practice

**Step 49. Set the order's parameters completely. [A+D]**
Price(s) (trigger, limit, chase ceiling), quantity (from Step 41, re-verified against the *actual* trigger price if it differs from the card's planning price; if the trigger moved, the size is recomputed, not reused), time-in-force (DAY vs. GTC, chosen deliberately: a GTC breakout stop is a standing instruction that survives your absence and your change of mood, which is usually the point; a DAY order is a decision to re-underwrite the trade tomorrow), and any attached structure (bracket / OCO: entry + stop + Target 1 as one submission where supported, which is pre-commitment in its purest mechanical form, §1.6). For options: limit price from the spread's mid with a pre-set walk-away (e.g., mid + $0.05 increments to a hard ceiling), never a market order in a wide series.

**Step 50. Pre-place what can be pre-placed. [D]**
If the entry is a resting stop or limit, place it now (pre-open or at card completion) rather than watching for the moment. Resting orders are Darvas's telegram: they convert a future emotional moment into a past clerical act. If the entry requires a live condition (ORH formation), set the alert at the trigger level *now* and write the exact order you will submit when it fires.

## Phase G: Placement and fill management

**Step 51. Enter the sterile window. [D]**
Order placement happens under §1.4's sterile-cockpit rule: no feeds, no chat, no second opinions mid-submission. The card is the only document open. Most fat-finger and wrong-account errors are attention errors, and this step is their countermeasure.

**Step 52. The pre-submission checklist (cognitive timeout). [D]**
Read-do, out loud if alone (§1.6, §1.9.4): (1) Ticker and direction correct? (2) Quantity equals Step 41's recomputed number? (3) Order type and prices equal Step 48/49? (4) Stop attached or its placement is the immediate next action after fill? (5) Earnings/event clearance still valid (Step 27 re-checked against any overnight news from Step 18)? (6) Heat after this fill within cap (Step 42)? (7) State check: am I executing the card, or am I executing a feeling that arrived after the card was signed? Any "no" stops the submission. This checklist is short because it was designed from error classes, and it grows only when the journal produces a new one (§1.6).

**Step 53. Submit, then verify the working order. [D+A]**
After submission, read the broker's order record back: symbol, side, quantity, type, prices, time-in-force. Confirm it matches the card *character by character* (the same read-back discipline as any safety-critical field). An order you have not read back is an intention, not an order. Note the order ID in the journal record.

**Step 54. Manage the unfilled order. [D+J]**
Rules decided now, not improvised at the trigger: if price approaches but does not trigger, nothing happens (the order is the plan). If price triggers a limit entry partially, the partial is the position (size rules already account for it; do not "complete" it by chasing). If price gaps through a stop-entry far beyond the chase ceiling, the trade is *missed by design*: cancel per the card's rule and log a missed trade as a zero-R journal row (Step 75); chasing a gap is how a 1R plan becomes a 2R loss with a story. If the setup invalidates before filling (price reaches the would-be stop first, pattern breaks), cancel the order *and record the cancellation*; a stale resting order on a dead setup is a liability masquerading as patience.

**Step 55. On fill: record the fill immediately. [A+D]**
Fill price(s), quantity, time, and slippage vs. the card's expected price (in cents and in R). Slippage is a cost statistic you own: aggregated monthly, it reprices your EV assumptions (Step 43) and your order-type choices (Step 48). In a simulated book, apply the book's fill rule instead and record it the same way (e.g., next 5-minute bar open after the decision timestamp plus a fixed slippage charge; the rule matters less than its consistent, lookahead-free application).

**Step 56. Place the protective stop now. [D]**
Immediately after the entry fill, before any other action, place or confirm the stop order from Step 39 (or, where the playbook's convention is a closing-basis stop, set the alert + the hard disaster stop beyond it, and write which is which). Verify by read-back (Step 53's discipline). Then place or confirm Target 1's partial order if the plan uses one. A position without a verified stop is not an open trade; it is an open emergency, and it is closed or protected before anything else happens, including lunch.

**Step 57. Update the book. [A]**
Recompute heat, name weight, cluster exposure, and cash with the new position at its *actual* fill and stop. If the fill's slippage changed the true risk beyond tolerance (e.g., risk is now 1.3R because the fill was far from plan), the correction is a size trim to restore planned risk, executed now, not a hope that it evens out.

**Step 58. Write the opening journal entry. [D]**
Same fields as the card, now with actuals: fill, stop in place (order ID), targets, 1R, state at entry, and one line: "What I will be watching for first:" (the earliest observable that confirms or denies the thesis, e.g., "follow-through volume in the first hour; a weak close today puts this on exit watch"). The trade is now fully born: card (before), orders (verified), journal (actuals). Everything after this is management of a documented position.

## Phase H: In-trade management (the trade's working life)

**Step 59. Monitor by exception, not by staring. [D]**
Default state: alerts at the trigger-relevant levels (stop approach, Target 1, thesis-relevant levels) and scheduled checks at the day's decision points (midday read, pre-close pass). Continuous watching is prohibited by design (§1.4's vigilance and capture problems) except in the first hour of an EP/breakout day where the setup's own rules require it. What you do at each scheduled check is Steps 60 to 65, in order.

**Step 60. Compare price behavior to the plan's expectations, not to your hopes. [J]**
The plan (Step 44's simulation, Step 58's first-watch line) defined what a healthy trade looks like: follow-through promptly (Minervini: a working breakout progresses), pullbacks that hold the pivot on contracting volume, closes in the top of the range. Score the actual behavior against those descriptors: *on plan / slow / wrong-shaped*. "Up" and "down" are not scores; a trade can be up and wrong-shaped (grinding on declining volume into supply) or down and on plan (an orderly pullback holding the pivot).

**Step 61. Re-underwrite the thesis at each check, briefly. [J]**
Tudor Jones's daily assumption, operationalized: if I had no position, would I enter here, at this price, with this stop? Three outcomes: *Yes* (hold per plan); *No, but the plan's invalidation has not triggered* (hold, but no adds, and flag the position; a position you would not enter but have not been stopped out of is a hold only because the plan, not the mood, governs); *The thesis is falsified by a non-price event* (Step 45's condition: guidance, group collapse, news) — exit per the event rule without waiting for the price stop, because the stop was priced for a thesis that no longer exists.

**Step 62. Manage the stop only upward, only by rule. [D]**
Stops move when the management plan's conditions are met (e.g., after the Target 1 partial, remaining stop to breakeven; trail under higher lows / the 10- or 20-day MA per the setup's rule, Kell's cycle transitions). Stops never move down, never widen for "room," never get removed "temporarily." A desire to widen a stop is information: it means the original risk definition is being renegotiated by the disposition effect (§1.5.1), and the correct response is to exit at the original stop or earlier, then re-underwrite the idea as a *new* card if it still attracts you tomorrow.

**Step 63. Execute adds only under the add rule. [D+J+A]**
Adds are permitted only when *all* of the playbook's conditions hold: the position is profitable (adds are never to a loser, Livermore / Tudor Jones, no exceptions and no "averaging into value" inside a momentum trade; Arnott-style rebalancing belongs to a different portfolio with its own money); a defined add trigger has occurred (a new base/pivot within the same trend, a Kell Crossback or Base 'n Break, a pullback-setup entry); the add is sized as its own trade (its own stop, its own R contribution, recomputed at Step 41's formula); and total position and heat remain within Step 42's caps *after* the add. The add gets its own card addendum and its own journal line; blended-average thinking ("my average is now $X") is anchoring (§1.5.6) and is banned from the record.

**Step 64. Execute trims and partials exactly as written. [D]**
At Target 1 or the strength condition (e.g., +2 to +3R, or 3 to 5 days into strength for Qullamaggie-style breakouts), sell the planned fraction (typically 1/3 to 1/2), apply the planned stop adjustment to the remainder, and record the partial fill and realized R immediately. The partial exists to convert paper asymmetry into realized asymmetry and to de-risk the runner emotionally (a position that has paid for itself is held with a steadier hand; that is a feature, honestly labeled as psychological as much as financial). Selling *more* than planned because it "feels toppy," or *skipping* the partial because "this one is different," are both plan violations and are logged as such even when they make money (§1.7: execution grade is independent of outcome).

**Step 65. Run the position through every event, every time. [D+J]**
Before any earnings print, major macro release, or known catalyst in a held name: restate the event rule from the card (hold full / trimmed to gap-safe size / exit before the print / options hedge), compute the gap math (Step 19: a 2× expected-move adverse gap must cost ≤ ~2R, else trim until it does), and execute the rule at the pre-close pass while there is still a market to act in (the plan's 15:00 block exists for this step). "I forgot it reported tonight" is a checklist failure (Step 52, item 5 exists because of this error class), and it is graded as one.

**Step 66. Apply the time stop. [D]**
When Step 35's date arrives: if the trade has not progressed (define "progressed" on the card: e.g., has not reached +1R or made a higher high within N sessions), exit or reduce per the rule, even if price has not hit the stop. Capital parked in a non-performing trade is not neutral; it carries heat, event risk, and attention cost, and its opportunity cost is the next setup. Time stops are how a swing trader manufactures turnover of *capital*, not of trades.

**Step 67. Watch the regime under the position. [J]**
A position's plan was written in a regime. At each check, note regime drift (index loses its 50-day, breadth deteriorates, group breaks). The playbook's response is graded, not binary: deteriorating regime → no adds, stops tightened to the next rule level, partials taken earlier; regime failure (Stage 4) → the book-level rule governs (heat to the PROTECT cap), which may force exits the individual charts have not yet signaled. Portfolio rules outrank position hopes, in writing, in advance.

**Step 68. Log the management trail. [D]**
Every management action (stop move, add, trim, event decision, time-stop decision) gets a timestamped journal line with its rule citation ("per card §trail: stop to breakeven after T1 partial"). Actions without rule citations are flagged in review as improvisations; their outcomes are graded separately, because an improvisation that pays is still a leak (it teaches the wrong lesson at full emotional volume).

## Phase I: Exit execution (the trade's death, handled as carefully as its birth)

**Step 69. Recognize the exit class. [D]**
Every exit is one of five, named in the journal: **(1) Stop exit** (invalidation triggered); **(2) Target/trailing exit** (plan's profit rule completed); **(3) Time exit** (Step 66); **(4) Thesis exit** (Step 61's falsification); **(5) Portfolio exit** (regime/heat/ladder rule, Step 67). Naming the class matters because each has its own statistics and its own typical error (stop exits: slippage and delay; target exits: premature full exits; thesis exits: lateness; portfolio exits: reluctance).

**Step 70. For stop exits, execute without a meeting. [D]**
If the stop is a resting order, it fires; your job is post-fill verification (Step 72). If the stop convention is close-based (the playbook assigns the convention per setup, Step 38), the close that triggers it produces an exit order for the next session's open or the same evening's after-hours where appropriate, placed *that evening* (Step 11's discipline), not reconsidered in the morning. If an intraday breach triggers an intraday-convention stop, exit in that session. The interval between "the plan says exit" and "the exit order exists" is the most expensive interval in retail trading; the system's design goal is that it be zero because the order already existed (Step 56) or mechanical because the rule fired at a scheduled check.

**Step 71. For discretionary-shaped exits (targets, thesis, portfolio), use the placement steps again. [D+A]**
Re-run Steps 51 to 53 in miniature (sterile moment, correct ticker/side/quantity, read-back). Exit orders get the same clerical respect as entries; a fat-fingered exit (wrong quantity, limit mispriced into a fast tape) is a real and recurring error class. Choose the order type by the same mechanics as Step 48: market when immediacy is the requirement and the name is liquid; limit with a chase floor when the exit is a profit-take into strength and price discipline matters more than certainty.

**Step 72. Verify the exit fill and the flat state. [A+D]**
Fill price, quantity, slippage vs. the triggering level (for stop exits, slippage beyond the stop is recorded separately: it is the honest price of gap/liquidity risk and it feeds sizing for event-prone names). Confirm the position is actually flat (or at the intended residual after a partial), confirm no orphan orders remain working on the name (a leftover stop or target on a flat position can re-open a position you think you closed; cancel and verify), and confirm any related options legs are closed as a unit, never one leg alone unless the card's structure rule says so.

**Step 73. Compute the trade's result in R, immediately. [A]**
Realized P&L ÷ Step 40's 1R = result in R, recorded to one decimal, including all partials, all costs, and slippage. Also record: holding period in sessions; maximum favorable excursion (MFE, in R, from the recorded path) and maximum adverse excursion (MAE, in R). MFE/MAE are the two most diagnostic numbers in your statistics (aggregated at Step 83): they show whether stops are inside the noise (MAE clustering just beyond −1R on eventual winners) and whether targets leave the trade's meat behind (MFE far beyond your capture).

**Step 74. Close the position's orders, alerts, and watch items. [D]**
Remove or repurpose alerts, file the final chart screenshot with entry/stop/exit marked, and move the name to its post-trade state on the watchlist (it may re-enter the funnel later as a new setup; it carries no privileges for having been owned; re-entry requires a new card, Phase D, in full).

## Phase J: Journaling (the trade becomes data)

*Phase J's fields are filled across the trade's life (Steps 46, 55, 58, 68, 73); this phase is the completion and quality pass, done the same day the trade closes, per the plan's non-negotiable rule.*

**Step 75. Complete the journal row. [D]**
One row per trade, fields per the master study's record-keeping standard, completed: date; ticker; setup (card name); regime at entry (Stage, breadth state, GEX/flow notes where used); entry, stop, target(s); shares/contracts and structure; 1R in dollars; options data if relevant (IV percentile, expected move, dominant Greeks); earnings date and distance at entry; exit(s) with classes (Step 69); result in R and dollars; holding period; MFE/MAE; screenshot link. A field left blank is a step in Phases A to I that did not happen; the journal thereby audits the whole sequence, which is its first job.

**Step 76. Grade execution separately from outcome. [J]**
Two grades: **Outcome** (R, already recorded) and **Execution** (A: card followed in every particular; B: minor deviation, named; C: material deviation, named). A +3R trade graded C (oversized, stop moved, got lucky) is a bad trade that made money and is reviewed as a problem; a −1R trade graded A is the system working and is reviewed as tuition at the planned price. This separation (Tharp, Minervini, Schwartz) is the single most important grading act in the document, because outcome-only grading trains resulting (§1.2) and manufactures both overconfidence and despair from noise.

**Step 77. Write the lesson in one line, and classify it. [J]**
One line only, in the form "Next time, when [situation], [action]." Classify the trade's dominant teaching: *setup* (the pattern behaved unusually), *selection* (wrong name for the pattern), *sizing* (R math or heat), *management* (stops/partials/adds), *state* (the human), *clerical* (orders/fills), or *none* (a clean trade with nothing to teach is a valid entry; manufacturing lessons from noise is narrative fallacy applied to oneself). The classification field is what makes the weekly review (Step 83) a query instead of a memoir.

**Step 78. Record state at exit and any near-miss. [D]**
Mood/state at exit (1 to 5, as Step 15), plus the aviation-style near-miss field (§1.9.3): anything that *almost* went wrong (almost forgot the earnings date, almost submitted the wrong quantity, felt the urge to move the stop at 14:20 and did not). Near-misses are logged with the same care as errors; they are the cheapest accident data that exists, and two occurrences of the same near-miss promote it to the checklist (Step 52) or to next week's focus rule.

**Step 79. Score the card's forecast. [A]**
Enter Step 34's probability forecast and its resolution (did the defined event occur?) into the calibration log (§1.7). One line per trade; the aggregation happens at review. Skipping this step because the trade "was obviously a winner/loser" is exactly the hindsight move the log exists to defeat.

## Phase K: The review loop (the trade teaches the next trade)

**Step 80. Same-evening review (5 minutes, day of exit). [J]**
While memory is warm: reread the card, then the journal row, then look at the chart. Answer three questions in writing: Did the market do what the thesis said, something else favorable, or something else unfavorable? Did I do what the card said? Is there any action item that cannot wait for the weekly review (a broken order pattern, a data error, a rule that produced an absurd result)? File the answers in the journal. This is the chess post-mortem done first without the engine: your reasoning, audited against your record, before hindsight reloads the chart.

**Step 81. Next-session review (2 minutes). [J]**
At the next pre-open, glance at the closed trade's name once: did the exit, whatever its class, look right with one more session's information? Record nothing unless the answer reveals a *rule-level* issue (e.g., stop convention systematically whipped by this name's volatility). This step's brevity is the point: it trains the discipline of looking once, learning the rule-level lesson if any, and not re-litigating exits, which is regret (§1.5.6) wearing a diligence costume. Exited names that run on without you are the tuition receipt for risk control; the journal's aggregate numbers, not individual might-have-beens, judge the exits.

**Step 82. Three-to-five-session review: the path audit. [A+J]**
Days later (schedule it at exit: a calendar tickler for exit + 3 to 5 sessions), record what the name did after your exit relative to your MFE/MAE and exit class: for stop exits, did price recover immediately (stop placement inside the noise is a pattern worth detecting across 20 trades, never a verdict from one); for target exits, did the runner logic capture the meat; for time exits, did the name finally move, and how long after? Enter two numbers (post-exit maximum favorable move in R within the window; days to it). Individual results change nothing; the aggregate (Steps 83 and 85) tunes stop conventions and partial fractions, at reviews, in writing.

**Step 83. Weekly grading (the Friday block). [A+J]**
The plan's Friday grading, executed on the journal as a database: expectancy by setup (mean R, N), win rate, average win vs. average loss in R, profit factor, % of losses exceeding −1R and their causes (any loss beyond −1.2R gets a named cause: gap, slippage, or rule break; the third is a defect, not a statistic), execution-grade distribution, heat at entry vs. outcome (the Schwartz test: does your size creep after wins?), calibration bucket check (§1.7), and the book vs. SPY and QQQ for the week (the house yardstick: % gain vs. both benchmarks, always both). Output, in writing: the week's **single most expensive mistake**, which becomes next week's **single focus rule** (Step 84). One focus rule at a time; a list of seven improvements is a plan to improve nothing.

**Step 84. Install the focus rule. [D]**
Write next week's focus rule where it will be seen at the moment it governs (top of the daily page; on the checklist if it is checklist-shaped; as an alert if it is level-shaped). Examples of well-formed focus rules: "No entry whose stop exceeds 0.8× ADR, no exceptions for A+." "Partials are taken at the level, not 'watched' after it." A focus rule is a one-week experiment with a named hypothesis, reviewed at the next Friday grading: kept (promoted to the playbook), revised, or dropped, on evidence.

**Step 85. Playbook maintenance at the weekly pass (small) and monthly review (full). [J+D]**
Weekly: re-stage every holding and watchlist name on weekly charts (Weinstein); bench or promote nothing on one week's data. Monthly (the plan's monthly letter, Druckenmiller/Asness form): full R-distribution review; expectancy by setup × regime with N's stated; a setup with negative expectancy over 30+ trades *in its correct regime* is benched for study (not traded smaller forever, not defended by narrative); sizing recalibration by §1.2's rule (the smaller of the fractional-Kelly ceiling from the live R-distribution and the fixed-fractional budget); options P&L decomposed (direction / volatility / theta) so a premium program knows what it is actually being paid for; and the one-page letter: what I own, why, what normal pain looks like from here, and what would change my mind. Rule changes are made here, dated, with reasons, and never midweek on a feeling (the plan's standing rule: strategy, sizing, and stops change by ruling, never by mood).

**Step 86. Feed the library. [D]**
File this period's instructive trades (best A-execution win, worst rule-break, cleanest failure of a good setup) into the historical-models collection with annotations (Step 25's resource). The library is the chunk collection (§1.3, §1.9.1); it grows only from curated, annotated examples, and this step is its curator. Once a quarter, prune: examples whose setups have been benched leave the active library for the archive, so recognition is trained on the current playbook, not on its ancestors.

**Step 87. State and process audit (monthly, honest). [J]**
Aggregate the state logs (Steps 5, 15, 58, 78): P&L and execution grades by sleep band, by urge rating, by day of week, by hour of entry. Most traders who run this query find at least one state that is measurably expensive (the sub-6-hour day, the post-argument morning, the Friday-afternoon origination). The finding becomes a rule through Step 85's process, not through self-criticism. This is Steenbarger's coaching insight industrialized: treat your own states as variables with data, and engineer around the expensive ones.

**Step 88. Benchmark and attribution close-out (monthly/quarterly). [A]**
Book return vs. SPY and QQQ over the period (and since inception), drawdown comparison, and a rough attribution: how much of the period's R came from which setup, which regime, stock vs. options expression. The point is not vanity metrics; it is the kill/keep evidence for Step 85 and the honest answer to the only question that ultimately matters: *is this process, as actually executed by this human, beating the index it could simply own, after costs, per unit of drawdown endured?* If the answer is no for a sustained, adequate sample, the process, the execution, or the fit is wrong, and the review's job is to say which, with the journal as evidence (Schwager's first distilled rule: the method must fit the person; a method the person cannot execute has an expectancy of its *executed* version, not its designed one).

## 2.1 The sequence compressed: one-page checklist form

For desk use, the 88 steps compress to the pause-point checklists (the long form above is the SOP that explains and justifies each item; §1.9.3's lesson is that both forms are needed):

- **Evening before:** book verified (2) · vitals + ladder status (3, 4) · self checked (5) · calendar + regime + posture (6 to 9) · positions re-underwritten, stops raised (10, 11) · disasters rehearsed (12) · environment set (13) · stop (14).
- **Pre-open:** state (15) · machinery (16) · overnight + news (17, 18) · gaps repriced (19) · focus list final (21).
- **Card:** setup named + graded (31, 32) · thesis with opposition (33) · base rate + probability (34) · catalyst + time stop (35) · pre-mortem (36) · correlation (37).
- **Risk:** invalidation (38) · stop + distance gates (39) · 1R (40) · size from stop (41) · caps (42) · targets + EV (43) · simulation (44) · management plan (45) · sign (46).
- **Order:** expression (47) · type (48) · parameters (49) · pre-place (50).
- **Submit:** sterile (51) · checklist (52) · submit + read back (53) · fill recorded (55) · stop placed + verified (56) · book updated (57) · journal opened (58).
- **Manage (scheduled checks only):** behavior vs. plan (60) · re-underwrite (61) · stop up only (62) · adds by rule (63) · partials as written (64) · events (65) · time stop (66) · regime (67) · log everything (68).
- **Exit:** class named (69) · execute (70, 71) · verify flat + no orphans (72) · R computed with MFE/MAE (73).
- **Close the loop:** journal complete + execution grade + one-line lesson + near-miss + forecast scored (75 to 79) · evening look (80) · next-day glance (81) · path audit at +3 to 5 sessions (82) · Friday grading + one focus rule (83, 84) · monthly letter, recalibration, library (85 to 88).

## 2.2 Where each faculty from Part 1 does its work in the sequence

| Faculty (Part 1) | Steps where it is exercised | Steps that protect it |
|---|---|---|
| Base rates / probability (§1.1) | 25, 34, 43 | 22 (screens define the class), 79, 83 |
| Expected value (§1.2) | 40 to 43 | 41 (size from stop), 57, 73 |
| Pattern vs. narrative (§1.3) | 24, 25, 29, 33 | 31 (named setup), 36, 38 |
| Attention / triage (§1.4) | 7, 8, 21, 28 | 13, 14, 51, 59 |
| Loss aversion / disposition (§1.5.1) | 62, 64, 70 | 38, 40, 56, 76 |
| Recency (§1.5.2) | 83, 85 | 4, 87 |
| FOMO (§1.5.3) | 28, 30 | 21, 46 (no card, no trade), 54 |
| Revenge (§1.5.4) | (the urge, at any stop-out) | 4 (day limit), 59, 68 |
| Euphoria (§1.5.5) | 63, 64 | 41, 42, 84 |
| Decision hygiene (§1.6) | 36, 45, 52 | 46, 49 (brackets), 56 |
| Calibration (§1.7) | 34, 79 | 83 (bucket scoring) |
| Fatigue / state (§1.8) | 5, 15 | 14, 87 |
| Adjacent-field structures (§1.9) | 12 (rehearsal), 33 (differential), 44 (simulation), 52 (timeout), 80 (post-mortem), 83 (M&M) | throughout |

## 2.3 A note on step counts and reality

Eighty-eight steps sounds like a burden until the timing is priced: Phases A and B are the plan's existing evening and pre-open blocks (about an hour combined, most of it Steps 22 to 28's funnel work that serves *all* of tomorrow's trades, not one). Phase D and E for a single card take 10 to 15 minutes once the library and screens are warm. Phase G takes two minutes. Phase H is minutes per scheduled check. Phase J is five minutes. Phase K is the Friday and monthly blocks the plan already reserves. The per-trade marginal cost of the full sequence is roughly 25 minutes of structured work, most of it before entry. Set against the measured costs it defends against (the disposition effect's ~3.4 percentage points a year in Odean's sample, the overtrading gap of ~6.5 points a year in Barber and Odean's most active quintile, a single −3R mistake cutting a sample's expectancy nearly in half in Tharp's example), the sequence is not overhead. It is, arithmetically, the highest-EV activity in the document.

The steps also degrade gracefully, which is a design requirement, not an accident: on a day when time collapses, the steps that may *never* be skipped are the load-bearing core: 2 (book verified), 5/15 (state + status), 31 (named setup), 34 (probability), 38 to 42 (invalidation, 1R, size, caps), 45 (management plan), 52 (checklist), 56 (stop verified), 75/76 (journal + execution grade). Everything else can compress; those cannot, because each of them is the countermeasure to a named, measured failure in Part 1.

---

## Sources

**Local (primary for the playbook and the operating day):**

- Master-trader study (discretionary lineage, options masters, quants, macro, Schwager distillation, playbook, risk limits): `~/workspace/research_notes/master-traders-deep-dive-20261029-0229/report.md`
- Personal-quant operating plan (the day and the week, trade cards, review cadence): `~/workspace/personal-quant/PLAN.md`

**Part 1 evidence base (web, as cited inline):**

- Tetlock and Gardner, *Superforecasting*; Good Judgment Project methods and Brier scoring: https://vectree.io/pdf/c/superforecasting-philip-tetlock ; calibration and overconfidence literature (Lichtenstein, Fischhoff and Phillips 1982; Moore and Healy 2008), superforecaster adjustment behavior, calibration as a sizing/survival variable: https://www.convexly.app/blog/overconfidence-bias
- Duke, *Thinking in Bets* (EV framing, resulting, decision vs. outcome): https://fronterabrands.com/thinking-in-bets/ ; https://www.antoinebuteau.com/lessons-from-annie-duke/
- Kahneman and Klein (2009), conditions for intuitive expertise; Klein's Recognition-Primed Decision model (fireground commander study): https://idtips.substack.com/p/the-recognition-primed-decision-model ; https://github.com/martinmontero/holmes/blob/HEAD/docs/research/wisdom-intuition-knowledge-judgment-v3.1.md
- Chess chunking (de Groot; Chase and Simon 1973; ~50,000 chunks; random-position control): https://www.chess.com/blog/ghefley/memory-chunking ; https://www.stargazers.co.in/chess/more
- Narrative fallacy, apophenia, confirmation bias (Taleb; Whitson and Galinsky 2008; Nickerson 1998): https://www.mdpi.com/2673-9461/6/2/17 ; https://averagingup.com/elementary-wordly-wisdom/cognitive-and-emotional-biases/ ; https://clearsignals.cloud/posts/why-smart-people-make-bad-decisions/
- Prospect theory loss aversion (~2.25×, Tversky and Kahneman 1992) and its trading expressions: https://tradetron.tech/blog/psychology-of-algorithmic-trading-how-emotions-affect-performance
- Disposition effect and overtrading (Odean 1998: gains realized ~14.8% vs. losses ~9.8%, sold winners outperforming held losers by ~3.4 pp; Barber and Odean 2000: 66,465 households, most active quintile 11.4% vs. 17.9% market): https://vaultwealth.com/resources/insights/how-overtrading-can-cost-you-returns/ ; https://www.stockopedia.com/content/overtrading-why-overconfidence-boredom-and-fear-can-wreck-returns-143982/ ; https://paperswithbacktest.com/api/paper/how-the-disposition-effect-and-momentum-impact-investment-professionals/pdf
- Revenge trading and FOMO mechanics: http://tronexo.com/psychology-mindset/trading-psychology/
- Recency and experience effects (Malmendier; availability): https://www.fsadvice.com.au/article/looking-backward-investing-forward-how-investor-experience-shapes-decision-making ; https://www.preprints.org/manuscript/202510.2175
- Noise and decision hygiene (Kahneman, Sibony and Sunstein; underwriter variability ~55%): https://www.brijeshdalmia.com/books-reviews/
- WHO Surgical Safety Checklist outcomes (Haynes/Gawande et al., NEJM 2009: complications 11.0% to 7.0%, deaths 1.5% to 0.8%, 7,688 patients, eight hospitals): https://www.who.int/news/item/11-12-2010-checklist-helps-reduce-surgical-complications-deaths ; https://tallyfy.com/checklist-manifesto/
- Pre-mortem (Klein, via Kahneman) and decision journals vs. hindsight bias: https://hub.cissychen.com/investing/decision-training-day27.en.html ; https://gov.capital/10-game-changing-strategies-to-stay-mentally-sharp-under-pressure-the-neuroscience-of-elite-financial-performance/
- Diagnostic error and premature closure (Graber, Franklin and Gordon 2005: cognitive factors in 74% of 100 cases; broader incidence and preventability reviews); M&M rounds structure (Ottawa model): https://www.deltapsychology.com/articles-for-doctors/clinical-decision-cognitive-biases ; https://www.mja.com.au/journal/2020/213/7/diagnostic-error-incidence-impacts-causes-and-preventive-strategies ; https://emsj.ca/wp-content/uploads/2017/09/CalderMM-Rounds-Guide-2012.pdf
- Sleep and fatigue (Van Dongen et al. 2003 cumulative restriction deficits and impaired self-assessment; Palmer et al. 2024 meta-analysis on sleep loss and emotion; ego-depletion replication failure, *Perspectives on Psychological Science* RRR): https://daytradingtoolkit.com/beginners-guide/avoiding-day-trading-burnout ; https://theobservermindset.substack.com/p/bad-sleep-makes-your-discretion-less
- Order-type mechanics (market/limit/stop/stop-limit guarantees, spread, slippage, partial fills): https://fortraders.com/blog/understanding-order-types-market-limit-and-stop-orders ; https://cursa.app/en/page/forex-market-structure-how-currency-trading-works-in-practice ; https://scope360.io/blog/trading-mechanics-explained-order-types-leverage-and-fees/

**Evidence-quality note.** The strongest claims above rest on replicated experimental work and large account-level datasets (prospect theory, disposition effect, overtrading costs, calibration curves, checklist outcomes, sleep restriction, chess chunking, diagnostic-error audits). Practitioner claims (masters' rules, revenge/FOMO syndromes, state-management practices) are labeled as testimony where they appear and are adopted here because independent masters converge on them *and* they are consistent with the proven layer, not because any single master's record proves them. Specific pattern frequencies and any forecast of this system's returns remain **unproven until the journal in Phase J/K prices them**, which is not a caveat appended for safety; it is the document's central claim about how a trader's mind should treat every claim, including its own.

*End.*
