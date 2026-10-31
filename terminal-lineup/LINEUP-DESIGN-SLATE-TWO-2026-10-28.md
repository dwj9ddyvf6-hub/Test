# The Lineup, Slate Two: 20 More Free Terminal Tools (21 to 40)

Designed 2026-10-28 at the owner's direction ("Now design 20 more"), immediately after Slate One (tools 1 to 20, LINEUP-DESIGN-2026-10-28.md). Same rules: free in full, the useful tool standard, no padding, honesty on the face of every figure, The Record grades everything that publishes a call.

The discipline of this slate: Slate One took the proven engine and the obvious calculators. These twenty have to earn their slots from the rest of the corpus: the Morgue's data lanes (FINRA short volume, SEC company facts, chain archive), the parts of the vendor corpus Slate One did not use, and combinations that exist in no single vendor. Each entry names its proof status honestly: **built** (running code in the corpus), **partial** (machinery exists, assembly or a data route still to prove), or **route to prove** (the design is sound and the parts are named, but the live route has not been demonstrated). Nothing in this slate ships until its status is built and proven.

## Wave 5: the lanes (data the desk already collects, given faces)

### 21. Insider Wire
- **Job:** who inside the company is buying or selling: officer and director transactions, plainly listed, buys separated from sells, cluster buys flagged.
- **Moment:** when a name is on your screen and you want to know what the people who run it are doing. **Question:** are insiders putting their own money in?
- **Built from:** the InsiderFinance-class insider data harvested in the corpus, graded forward like everything else: insider clusters get followed on The Record.
- **Status:** partial. The data class is in the corpus; the live route and its delay must be proven before this ships.

### 22. Short Volume Ledger
- **Job:** for any ticker, how much of today's and recent volume was short, day by day.
- **Moment:** when a name is heavy or squeezing. **Question:** how much of this volume is borrowed shares?
- **Built from:** the Morgue's FINRA short-volume lane, already landed and collecting.
- **Status:** built at the lane level; the face is new.

### 23. Filings Wire
- **Job:** one ticker's SEC filings and reported numbers, digested: what was filed, when, and the headline figures, without opening a 200-page document.
- **Moment:** after a filing drops. **Question:** what did this company actually just report?
- **Built from:** the Morgue's SEC company-facts lane, already landed.
- **Status:** built at the lane level; the digest face is new.

### 24. Dark Prints
- **Job:** one ticker's dark pool picture: its DIX-style dark pressure reading and recent large off-exchange prints.
- **Moment:** when a name moves on no news. **Question:** what is the off-exchange tape doing in this name?
- **Built from:** the constituent DIX machinery turned per-ticker (Slate One's Map uses it at index level; this is the single-name job, a different moment and a different question).
- **Status:** partial. The construction exists; per-ticker coverage floors must be set and proven.

### 25. Chain Explorer
- **Job:** read a full options chain properly: strikes, expiries, open interest, volume, and computed greeks on every row.
- **Moment:** building any options idea. **Question:** what does this chain actually look like?
- **Built from:** the Morgue's chain analytics extension plus its Black-Scholes module (the same conventions the calculators use, so the numbers agree everywhere on the terminal).
- **Status:** partial. Chain archive and greeks exist; the indicative feed carries no greeks, so ours are computed and labelled computed, never presented as exchange figures.

## Wave 6: the volatility bench (options are priced in vol; these read it)

### 26. IV Weather
- **Job:** for one ticker, whether its implied volatility is cheap or rich for that name: current IV against its own history, plus the term structure shape.
- **Moment:** before buying or selling premium. **Question:** am I paying up for vol here?
- **Built from:** chain snapshots archived over time (the chain archive lane exists precisely so this history accrues), with the percentile method printed on the card.
- **Status:** partial, time-gated like the State Analogue: the history builds daily from the first chain snapshot.

### 27. Skew Lens
- **Job:** the shape of demand across strikes: how much more the market pays for downside protection than upside calls, in one picture.
- **Moment:** when a name feels fragile or euphoric. **Question:** which tail is the market paying for?
- **Built from:** the same chain data as the Explorer, a different job: shape, not level. (IV Weather answers how much; Skew Lens answers which side.)
- **Status:** partial, same chain foundation.

### 28. Premium Meter
- **Job:** implied move versus realized move: whether options are overpricing or underpricing what the stock actually does.
- **Moment:** before any premium trade, and after earnings. **Question:** is the premium fat or thin against reality?
- **Built from:** the premium-versus-realized comparison the peer terminal lists as "not measured." Ours measures it, per name, with the window printed.
- **Status:** route to prove. Needs the IV history from tool 26 plus realized vol from bars, both named; assembly is new.

### 29. Greeks Sketch
- **Job:** a multi-leg position's live sensitivities: delta, gamma, theta, vega, in dollars per day and per point, not just its expiration picture.
- **Moment:** while holding a spread. **Question:** what is this position doing to me today?
- **Built from:** the same Black-Scholes module as Payoff Sketch (tool 6 draws the expiration picture; this draws the living one). One pricing engine under both, so they can never disagree.
- **Status:** built at the engine level; the face is new.

### 30. Expiry Pin Watch
- **Job:** into a weekly expiration, where open interest says price may gravitate: the pin level and the interest walls around spot.
- **Moment:** Thursday and Friday. **Question:** where is the gravity into this expiry?
- **Built from:** chain open interest (the Map already builds walls from OI at index level; this is the per-expiry, per-name job).
- **Status:** partial. Labelled on its face as a positioning read, never a prediction; its calls grade on The Record like everything else.

## Wave 7: the market's body (context tools, one job each)

### 31. Breadth Meter
- **Job:** the market's health under the surface: percent of stocks above their 50 and 200-day averages, advancing versus declining, in one dial.
- **Moment:** any time the index looks fine and you do not believe it. **Question:** is this rally broad or narrow?
- **Built from:** the breadth machinery already running in the peer terminal's strip and the desk's universe data.
- **Status:** partial. The computation is proven elsewhere in the corpus; our face and our universe must be reconciled before shipping.

### 32. Sector Rotation
- **Job:** which sectors and themes are leading, lagging, and turning, over 5 and 21 sessions.
- **Moment:** weekly planning. **Question:** where is money rotating to and from?
- **Built from:** the sector and theme strength calculations in the corpus's terminal work, on our universe.
- **Status:** partial, same reconciliation note as Breadth.

### 33. Regime Dial
- **Job:** one plain sentence about what kind of market this is, backed by the handful of checks behind it, each shown.
- **Moment:** first click of the day, before the Map. **Question:** what kind of day is this likely to demand?
- **Built from:** the trend-check banner pattern proven on the peer terminal (checks pass/fail in the open, no black box). It describes the regime; it never forecasts.
- **Status:** partial. The pattern is proven; our check set must be named, frozen, and graded.

### 34. The Week Ahead
- **Job:** the macro calendar that matters: Fed, CPI, jobs, Treasury auctions, with dates and times in plain view.
- **Moment:** Sunday night and Monday morning. **Question:** what could move everything this week?
- **Built from:** the real 64-event macro calendar already integrated in the desk's research lanes.
- **Status:** built at the data level; the face is new.

### 35. Earnings Calendar
- **Job:** who reports, when, with the priced expected move attached to each name.
- **Moment:** planning the week. **Question:** whose report could move my names?
- **Built from:** the earnings study's name set plus Expected Move Map machinery (tool 7 measures one name; this is the schedule of all of them, a different job at a different moment).
- **Status:** partial. The calendar route must be proven; expected moves attach only where the chain supports them, and say so where it does not.

## Wave 8: the personal bench (the user's own names, no accounts)

### 36. Watchlist Pulse
- **Job:** your list of names, one strip each: price, the Board's gate verdict, tape tags, insider flags, all on one screen. The list lives in the link, never in an account.
- **Moment:** the daily check-in. **Question:** anything happening in my names?
- **Built from:** Slate One's engines pointed at a user-supplied list instead of the universe. Aggregation is the job: the engines exist, the personal view does not.
- **Status:** partial. Depends on tools 3, 4, and 21 being live.

### 37. Correlation Web
- **Job:** for a basket of names, which ones secretly move together: the twin and cluster map.
- **Moment:** before adding one more name to a basket. **Question:** am I actually diversified, or long the same trade five times?
- **Built from:** the correlation and twin-detection machinery from the sleeve ensemble work, turned from sleeves to stocks.
- **Status:** partial. The machinery is proven on sleeves; the stock version is an adaptation, labelled as such.

### 38. Unusual Volume
- **Job:** names trading abnormally heavy volume for themselves today, ranked by how abnormal.
- **Moment:** midday scan. **Question:** where is something happening that I have not heard about yet?
- **Built from:** the desk's volume machinery (SIP feed only, per the standing volume law; Yahoo hourly volume is corrupt and never used).
- **Status:** partial. Per-name baselines accrue daily.

### 39. Grade My Call
- **Job:** you make a call (ticker, direction, today), it goes on the public ledger with a timestamp that cannot be edited, and The Record grades it at 1, 5, and 21 sessions next to the terminal's own tools.
- **Moment:** when you want your own record kept honest. **Question:** how good are my calls, really, kept by someone who will not let me forget the losers?
- **Built from:** novel mechanism N1 (ledger-first grading) opened to the public. No vendor in the corpus grades its users' calls beside its own; this is the lineup's most social tool and its purest expression of the honesty product.
- **Status:** route to prove. The ledger machinery is built; the public submission surface is new and ships only with abuse limits stated on its face.

### 40. 13F Tracker
- **Job:** what large holders bought and sold last quarter, per ticker and per fund, from the quarterly filings.
- **Moment:** when you want to know who else owns this, and whether they are adding. **Question:** is big money accumulating or leaving?
- **Built from:** the 13F data already cached in the Morgue's evidence work, turned into a quarterly-refreshed face with the filing lag printed on its face (13F data is always weeks old, and the card says so).
- **Status:** partial. The data exists in bulk; the digest and refresh route are new.

## What this slate deliberately holds back

- **State Analogue extensions and the P_NN family** stay at tool 20 until the 126-session floor is met; no variants count toward the 40.
- **Forecast outputs** remain a research note, not a tool, per the analysis.
- **Anything requiring a paid data route** is excluded by the free ruling; where a route is frail (borrow fees, insider delay), the tool either waits or prints the gap on its face.

## Build sequence

Slate One first, in its wave order: its engines are the foundation this slate stands on (Watchlist Pulse needs the Board and Tape; Premium Meter needs IV Weather's history accruing, so chain snapshots start accruing now, during Slate One's build, even though the Meter ships in Wave 6). Within this slate: Wave 5 (the lanes, data already collecting), Wave 7 (context), Wave 6 (volatility, as its history matures), Wave 8 (personal) last, because it composes the rest.
