# Research rationale and decision provenance

This record preserves the useful analysis behind the six constructions: economic mechanisms, mathematical reasoning, alternatives, observed contradictions, choices, and remaining uncertainty. It is a research handoff, not a claim to contain a verbatim lifetime conversation archive.

## Why these six were constructed

The recovered work contained signals whose conventional expressions were disappointing or whose portfolio effects differed from their per-trade results. The constructive response was to change the decision or payoff that consumes the information. The organizing variables are entry timing, hedge timing, capital transfer, the exact liability sold, execution urgency, and the information needed to establish a contractual relationship.

| Construction | Transformation | Competing explanation | Observation that could distinguish it |
|---|---|---|---|
| C1 | Separate asset entry from hedge activation | Ordinary rebound beta | Paired benefit beyond prespecified fixed exposure and clock controls |
| C2 | Sell an upside interval after recovery, beside stock | Familiar option premium already fully compensates risk | Executable credit versus conditional liability and stock-only/cash alternatives |
| C3 | Let reversal and momentum govern sequential phases | Simply owning leaders throughout | Same-capital post-repair relative performance versus fixed-time switch and leadership-from-start |
| C4 | Apply magnitude information to routing | Spread/ordinary volatility already contains the information | Incremental intent-level value including partial/no fills and markouts |
| C5 | Acquire a fact that removes a settlement state | Unknown history incorrectly treated as absence | Complete stipulated-source history and independently checked contract implication |
| C6 | Forecast a band liability instead of a stock mean | Bearishness is already priced; tail premium is inadequate | Physical right-tail forecast versus actual spread credit and full costs |

## C1 discovery sequence and rejected shortcuts

The first local run tested eight policies: unhedged, fixed beta, five hedge-release rules, and a repeated market switch. The later amendment added four inverse policies that start unhedged and add the hedge after recovery/time signals. It was adaptive discovery after viewing the first outputs. Both design/result versions and both logs are preserved.

The highlighted two-positive-bar delayed hedge increased the mean versus immediate hedging in the reported partitions. It did not consistently outperform no hedge or a fractional hedge, and its paired intervals included zero. Its fifth-percentile outcomes were worse than the full hedge. A repeatedly switching rule lost in the middle partition. These comparisons remain in the full output rather than being hidden by the selected narrative.

The interpretation is a concrete phase-dependent candidate to investigate. It is not a claim that an immediate hedge was irrational or that the unhedged rebound is alpha. A portfolio may rationally buy protection even when its expected return is negative. The relevant objective must be stated.

The original signal family had already been searched. The follow-up's period labels do not produce independent holdouts. Its current-survivor universe and missing funding history limit generalization. Parent selection before the negative-BTC filter and the 72-hour spacing reused for 24-hour experiments must be carried forward into replication.

## Option reasoning retained

C2's terminal payoff restores unit slope above the upper strike but never restores the upside interval sold. Calling it 'keep all upside' would be false. Stock downside remains. The decision must be judged from the overlay time, excluding sunk gains shared by the alternatives.

C6 asks for expected band payout rather than average stock return or win rate. The supplied 90%-win counterexample has negative expectancy. The long upper call caps the modeled terminal liability but can itself be expensive. Borrow, exercise and financing economics do not disappear because the trade uses options. Exact contract terms and interim cash requirements can overturn an attractive terminal calculation.

The existing portfolio changes the burden of the liability. A stockholder's wealth rises in many states where a sold call spread pays; a short book may be harmed in those same states. A portfolio-specific reservation price can therefore differ from a standalone expected payout. No preference parameter or capital allocation has been invented here.

## Rotation and execution reasoning retained

Selection skill and portfolio performance are different. Idle capital, overlap, costs and beta can explain a gap. C3 compares capital from the same transition time to the same endpoint. It cannot add separately normalized profitable trades as though they were funded simultaneously. The archived failed SPY rotation is relevant context; it neither proves nor refutes this exact untested rule.

For C4, the correct unit is the pre-existing investment intent. Filled orders are a selected sample, and cheap partial fills can have large missed-opportunity costs. High volatility does not always favor a passive limit: it may increase the cost of waiting. A forecast must add information beyond price, spread and ordinary volatility to earn its routing complexity.

## Conditional-contract reasoning retained

A prior compiler's rejection of differing monitoring starts was conservative. The new construction asks which historical fact can make the relationship valid now. Higher-not-previously-hit under identical future observation rules is one sufficient fact; lower-already-hit is another. Unknown history retains the adverse state. An interval with no accessible observation is not an observed absence.

The expanded reference checks its declared semantic domain and history coverage metadata, but the caller still supplies the facts. A `verified` flag is not self-proving. Real voids, revisions, delayed settlement and leg execution belong in a larger model when applicable. No current quote or actual arbitrage is claimed.

## What is new in the handoff itself

The six mathematical/timing kernels, specs, contracts, data dictionary, portable paths, bundled raw inputs, and verification tools were added to make the research recoverable and buildable. The package creates no new empirical forecast for C2/C3/C4/C6 and adds no new market evidence to the C5 example. Its tests validate declared behavior. Reproducing C1 uses the same selected history and remains exploratory.

## Owner instructions and scope history

The owner requested broad invention from the repository research, then clarified that GitHub should be read-only during the invention pass. That pass and the detailed report were created locally. The latest instruction explicitly requests saving everything in grand detail to GitHub so another LLM can build the constructions. This package implements that latest authorization on separate research branches. Existing production branches and trading systems are outside the save's changes.

The archive preserves complete local research artifacts, source references, and this explicit rationale. Credentials and private authentication material are not research payload. No new API call or payment was necessary to perform this save.
