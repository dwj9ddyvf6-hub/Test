# Census: REA Master Index Sweep — Chart Reading & Technical Analysis Assets

Source swept: `~/workspace/rea-master-index/MASTER-INDEX.jsonl` (114,798 records, ~45 MB), streamed record-by-record with Python (never loaded whole). Fields searched per record: title, path, summary, vendor. Index repos: Femto-lean (70,148 records), local (23,505), Silicon (21,145).

Keywords (as assigned): chart, technical analysis, pattern, fibonacci, elliott, wyckoff, candlestick, divergence, trendline, support, resistance, vwap, macd, rsi, breakout, flag, triangle, wedge, channel, visual. Supporting terms added for the indicator category: candle, moving average, bollinger, "trend line".

## Counts

- Any keyword at all: 17,312 records (15.1% of the index)
- Chart / technical analysis / visual (general): 4,307 records | 1,857 unique repo+path
- Patterns & geometry (pattern, flag, triangle, wedge, channel, breakout): 8,400 records | 3,789 unique repo+path
- Indicators used visually (vwap, macd, rsi, moving average, bollinger): 4,121 records | 2,985 unique repo+path
- Candlesticks (candlestick, candle): 1,006 records | 368 unique repo+path
- Support / resistance / trendlines: 814 records | 580 unique repo+path
- Divergence: 434 records | 265 unique repo+path
- Elliott wave: 418 records | 142 unique repo+path
- Wyckoff: 136 records | 109 unique repo+path
- Fibonacci: 120 records | 102 unique repo+path

Honesty notes on the counts: categories overlap (one record can sit in several). Record counts are inflated by the same file indexed across many branches; unique repo+path is the truer asset count. Keyword noise exists: "support" also matches customer-support text, "flag" matches CLI flags, "channel" matches comms channels, and "candle" matches raw OHLC data plumbing, so the patterns and S/R totals overstate pure chart-reading material. Fibonacci, Elliott, and Wyckoff counts are nearly noise-free because the terms are unambiguous. The center of gravity is unmistakable: the Femto-lean branch `research/2026-10-20-eyes` (the "eyes" chart-reading program) and `allf/optnews` hold most of the strongest assets, and vendor teardowns in Silicon/local hold the external-method material (TheStrat, Milkman, Tradytics, FlashAlpha).

Format per line: name | location (repo/branch/path) | kind | what it is | why it matters for learning to read charts.

## Category 1 — Chart reading & visual grammar (general)

ChartsLector public footprint & visual grammar | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/chartslector/PUBLIC_FOOTPRINT.md | doc | Reverse-engineering of ChartsLector's public methods and the visual grammar of his annotated charts | A working chart reader's annotation language, distilled from real published reads
Chart-Reading Playbook (Echo Analysis & Max Williamson) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/echo-x2/raw/midna/PLAYBOOK_echo_max_2026-10-12.md | doc | Two practitioners' chart-reading method reverse-engineered into a playbook, incl. Elliott/Fib cycle positioning | The single richest "how a human actually reads a chart" document in the index
Echo Analysis system spec for the chart reader | Femto-lean / allf/optnews / docs/research/2026-10-18-terminal/ECHO_SYSTEM_SPEC.md | doc | Echo's chart system specified formally for a chart reader | Turns one trader's eye into explicit, teachable rules
Echo Analysis on X: how he reads charts | Femto-lean / allf/optnews / docs/research/2026-10-18-terminal/ECHO_X_POSTS.md | doc | Corpus of Echo's posted chart reads and trade calls | Worked examples of reads made in real time, not hindsight
Extraction: charts and visual UI across the corpus | Femto-lean / allf/optnews / docs/research/2026-10-18-terminal/extract-terminals-charts.md | doc | Cross-vendor extraction of chart displays and visual UI conventions (2026-10-18) | Shows how every major terminal presents charts; the comparative visual standard
Blind chart test protocol | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/blind/PROTOCOL.md | doc | Protocol: read each chart as a veteran trader would, with nothing but the chart | The training/evaluation method for pure visual reading skill, stripped of fundamentals and news
Blind round 2 registration | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/blind/REGISTERED.md | doc | Pre-registered second round of the blind chart test (2026-10-19) | Pre-registration discipline applied to chart reading: reads graded against outcomes, no retrofitting
Canon gaps: full focus on TA and chart reading | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/EXECUTION_MATRIX.md | doc | Section 9: the owner's canon-gap lists for technical analysis and chart reading (Addenda 2-16/2-16b) | Names exactly what the desk's chart canon was missing; the syllabus of gaps to close
LLM chart vision research | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/V5/RESEARCH_LLM_CHART_VISION.md | doc | Research on machine visual reading of charts (V5 eyes program) | Directly relevant to teaching an AI eye to inspect charts perceptually

## Category 2 — Patterns & geometry (flags, triangles, wedges, channels, breakouts)

pat: chart patterns and breakout quality | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/pat.md | doc | DEEP-2 spec of classic chart-pattern detection and breakout-quality grading | The desk's pattern taxonomy with a quality dimension, not just detection
patterns lab spec | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/lab/patterns.md | doc | Lab version of the classic-patterns and breakout-quality spec | Same taxonomy in experimental form, paired with measured outcomes
Pattern census vs Bulkowski | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/out2/CENSUS.md | doc | Desk pattern detectors benchmarked against Bulkowski's published pattern statistics | Grounds pattern reading in the canonical published base rates instead of folklore
PATTERNS.md master study | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/PATTERNS.md | doc | The 2026-10-19 pattern study: divergences/harmonics/pitchforks drawn as a chart reader draws them, Kepler Fibonacci test, pattern sections 2a-2p+ | The largest single pattern document in the index; geometry taught the way it is drawn
Breakout summary result sets (s11 family) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/r2/ev/out/s11/breakout_summary.json (+ _nd/_nx and s11_small variants) | data | Measured breakout outcomes across universes from the round-2 pattern evaluation | Evidence for which breakouts deserve trust, split by universe
Nightingale flags anatomy | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/genius3/anatomy/nightingale_flags.csv | data | Flag-pattern anatomy dataset (full and small-cap cuts) | Flag geometry measured bar by bar; the raw material for learning flag shapes
Board-level replay: pullbacks first, no breakouts in a weak market | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/results/rank_test2.md | test | Replay test of a board read that ranked pullbacks over breakouts in a weak tape | Teaches the market-context gate on pattern reading: same pattern, different regime, different verdict

## Category 3 — Candlesticks

candlesticks.py | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/src/vfl_desk_snapshot/desk/terminal/read/candlesticks.py | code | The desk terminal's candlestick-pattern reader module | Candle definitions as executable rules, readable as a definition list
cdl: candlestick detectors, key-level companions and gaps | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/cdl.md | doc | DEEP-2 write-up of the candle detectors and how candles pair with key levels and gaps | Candles taught in context (at levels, with gaps), not as isolated shape flashcards
candles lab spec | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/lab/candles.md | doc | Lab spec: candlestick detectors, key-level companions, gaps | The study version of the same material, tied to the lab outcome data
Candle event study | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/results/ev_candles.md | doc | Event study: candle-pattern events vs next sessions' returns net of SPY and the liquid mean | Which candle signals actually preceded movement, with t-stats
Candles & gaps data-matrix section | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/review/data_matrix.md (section 2.9) | doc | Review matrix entry for candles and gaps coverage | Maps what candle evidence exists and where it is thin

## Category 4 — Support, resistance, trendlines

Levels of Reclaim: The Real Support and Resistance | Silicon / main / research/rea-teardowns/thestrat/corpus/docs__levels-of-reclaim.md | doc | TheStrat's doctrine on reclaim levels as the real support/resistance | A complete external S/R doctrine from a levels-based method, in the vendor's own words
Support/resistance and supply/demand (Milkman manual) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/mm/text/trading-manual.txt (section 11.3) | doc | Milkman Trades manual chapter on S/R and supply/demand zones | Practitioner zone-drawing method from a working intraday trader
Trendlines (structure_build) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/lab/src/structure_build.py (mirrored in eyes/DEEP/vfl/src/vfl_structure_build.py) | code | Trendline/structure construction code in the patterns lab | Trendlines as an explicit algorithm: which pivots, which touches, what counts as a line
add_support_resistance_levels | Silicon / main / research/rea-teardowns/tradytics/assets/ticker.js (also local teardown copy) | code | Tradytics' production S/R level computation in their web client | How a commercial platform derives and draws levels automatically
Key Exposure Levels API (FlashAlpha) | local / workspace/opt/rea-teardowns/flashalpha/pages/docs-lab-api-levels.html | doc | FlashAlpha Lab API doc: support/resistance derived from options exposure | Levels from positioning rather than price history; a second, independent way to draw the map
Gamma Walls: Support and Resistance from Options Data | Silicon / main / research/rea-teardowns/profitbuilders/pages/blog_gex.txt | doc | ProfitBuilders explainer on gamma walls as S/R | The options-derived level concept in plain language
Frozen support and resistance (broadening formation indicator) | Silicon / main / research/rea-teardowns/thestrat/corpus/docs__quantifiable-broadening-formation-indicator.md | rule | TheStrat rule freezing broadening-formation lines into S/R | Shows how a pattern's geometry becomes the level map after the pattern completes

## Category 5 — Divergence

Divergences, harmonics and pitchforks (PATTERNS.md 2p) | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/PATTERNS.md | doc | Divergence section of the master pattern study, drawn as a chart reader draws them, via lab/ta_shapes | Divergence defined geometrically against price structure, not just oscillator squiggles
divergence.py | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/src/vfl_desk_snapshot/desk/terminal/read/divergence.py | code | The desk terminal's divergence reader module | Executable divergence definitions to learn from and test against
tsh: divergences, harmonics, pitchforks (catalog) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/out2/CATALOG.md | doc | DEEP catalog entry for the ta_shapes divergence/harmonic/pitchfork family | Index card for the whole shape family, with provenance
chartread.py divergences | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/grok-bestsetups/lzd/REBUILD/bestsetups/code/chartread.py | code | Grok-lane Best Setups chart reader: divergence detection inside a full chart read | Divergence as one voice inside a complete read, weighted against the rest
Band-touch RSI divergence | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/pub1/notes/readme_bbrsi_orig.md | doc | Original README for the Bollinger-band-touch RSI divergence read | A specific, named divergence setup with its own entry logic
SPX vs SPY Morning Divergence (Milkman) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/mm/raw/page_spx-spy-divergence.html | doc | Milkman Trades page on index-vs-ETF morning divergence | Cross-instrument divergence: the same concept one level up, used intraday
Divergences data-matrix section | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/review/data_matrix.md (section 2.7) | doc | Review matrix entry for divergence coverage | Maps the divergence evidence base and its gaps

## Category 6 — Elliott wave

Elliott wave reader (elliott.py) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/src/vfl_desk_snapshot/desk/terminal/read/elliott.py | code | The desk terminal's Elliott wave counting module | Wave rules made executable; the count discipline in code form
Elliott/Fib cycle positioning (Echo playbook section) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/echo-x2/raw/midna/PLAYBOOK_echo_max_2026-10-12.md | doc | Echo Analysis's Elliott/Fib cycle positioning as actually practiced | Elliott as a live positioning tool by a practitioner, not a textbook summary
Fibonacci relationships (EWP Ch. 4 review) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/review/elliott_targets.md | doc | Section A.5: Fibonacci relationships from Elliott Wave Principle Ch. 4 (wording flagged UNVERIFIED, standard content) | The wave-to-Fib target ratios, with an honesty flag on sourcing
Elliott wave slot (synthesis contract) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/review/femto-copy/core/SYNTHESIS_SPEC.md (section 8) | doc | Contract for how the Elliott read enters the desk's synthesis | Shows where wave analysis legitimately sits in a multi-lens read: advisory, not a gate
ELLIOTT_SPEC with S/R and Fibonacci co-location | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/grok-bestsetups/qrb-wt/cursor-shadow-rig/shadow/terminal/bestsetups/out/elliott_1016/ELLIOTT_SPEC.md | doc | Best Setups Elliott spec, incl. section 10.5: co-location with S/R zones and the one-year Fibonacci zone (text only) | Confluence discipline: wave targets only count where levels agree
Elliott method study (descriptive, no outcomes) | Femto-lean / research-archive / docs/research/archive-2026-10-27/inventory/S_aa_findings.md (section 1.2) | doc | Method study of Echo Analysis' Elliott-wave method, descriptive with no outcome claims | A careful read of the method itself, honestly labelled as unverified by outcomes
Elliott tests (test_elliott.py / deskread tests) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/grok-bestsetups/lzd/REBUILD/bestsetups/code/tests/test_elliott.py | test | Behavioural tests incl. "Elliott break opposes the lean" and "Elliott wired not gated" | Encodes the desk's ruling on Elliott's authority: it informs, it never vetoes

## Category 7 — Wyckoff

wyckoff.py / wyckoff_phase.py | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/DEEP/vfl/src/vfl_desk_snapshot/desk/terminal/read/wyckoff.py (+ wyckoff_phase.py) | code | The desk terminal's Wyckoff phase-reading modules | Accumulation/distribution phase logic as executable rules
Wyckoff section, PROTOCOL_V4_OL | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/PROTOCOL_V4_OL.md | doc | The eyes program's reading protocol, Wyckoff chapter (same file carries Elliott and Divergence chapters) | Wyckoff placed inside a complete chart-reading protocol, in reading order
_wyckoff_scan (chart_read.py) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/midna-engine/core/chart_read.py | code | Wyckoff scan inside Midna's chart_read engine | Phase scanning integrated into the master chart read
Wyckoff bars fixture (chart read mastery tests) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/midna-engine/tests/test_chart_read_mastery_20261015.py | test | _wyckoff_bars fixture in the 2026-10-15 chart-read mastery test suite | Canonical example bar sets for each phase: the closest thing to Wyckoff flashcards in the index
Wyckoff data-matrix section | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/review/data_matrix.md (section 2.10) | doc | Review matrix entry for Wyckoff coverage | Maps what Wyckoff evidence the desk actually holds
Wyckoff persona answers | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/eyes/personaanswers/wyckoff.jsonl | data | Persona-answer set on Wyckoff reading | Question/answer drill material in the method's own terms

## Category 8 — Fibonacci

Kepler's test: Fibonacci ratios are not a law of these markets | Femto-lean / allf/optnews / docs/research/2026-10-19-patterns/PATTERNS.md (section 2e2; tools/kepler.py) | doc | Statistical test of Fibonacci ratio claims on desk data | The essential sceptical counterweight: Fib levels taught with their measured (weak) evidence
Refutations: Fibonacci (TheStrat) | Silicon / main / research/rea-teardowns/thestrat/corpus/docs__refutations.md (section 1) | rule | TheStrat's published refutation of Fibonacci methods (bundle also refutes MAs, RSI, patterns, Elliott) | A levels-only school's case against Fib, kept beside the pro-Fib material for balance
M_fib (monitor desk) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/audit/E/snap/desk/sleeves/monitor/chatgpt_desk.py | code | Fibonacci module inside the ChatGPT-desk monitor sleeve | Fib retracement computation as actually deployed on the desk
overhead_fib (cursor-shadow-rig paper sleeve) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/audit/E/snap/desk/sleeves/cursor-shadow-rig/paper.py | code | Overhead-Fibonacci supply logic in the cursor-shadow-rig paper sleeve | Fib used as overhead-supply mapping, a concrete practitioner use
MK round 2: S24 Kepler Fibonacci result | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/patterns/r2/mk/RESULTS.md | doc | Round-2 results entry reporting the Kepler Fibonacci test outcome | The verdict record for the Fib test, next to the other round-2 pattern verdicts

## Category 9 — Indicators used visually (VWAP, MACD, RSI, moving averages, Bollinger)

Terminal read TA tests | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/audit/E/snap/tests/test_terminal_read_ta.py | test | Tests for the terminal read TA layer, incl. RSI boundary behaviour and Bollinger width on flat series | Pins the exact indicator definitions the desk's chart layer draws
ema_vwap_options.py and exit tests | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/audit/E/snap/desk/sleeves/femto/ema_vwap_options.py (+ tests/test_femto_ema_vwap_exits.py) | code | EMA/VWAP sleeve logic and its exit-test suite | VWAP and EMA as a combined visual regime: price vs VWAP, EMA slope, with exits defined
First-session lab: EMA/VWAP and RSI fixes | Femto-lean / allf/optnews / docs/research/2026-10-18-lab/FIRST-SESSION.md (section 1) | doc | Lab note recording femto_ema_vwap and femto_rsi_meanrev definition fixes (commits c22ca40, 35889c7) | Shows how indicator definitions get corrected against intraday reality; a lesson in not trusting default formulas
bbrsi notes (Bollinger + RSI) | Femto-lean / research/2026-10-20-eyes / docs/research/2026-10-20-eyes/scratch/pub1/notes/bbrsi_extra.md (+ readme_bbrsi_orig.md) | doc | Notes on the Bollinger-band/RSI combined read | Band position plus oscillator state as one visual read, incl. its divergence variant (Category 5)
Refutations: Moving Averages and the RSI (TheStrat) | Silicon / main / research/rea-teardowns/thestrat/corpus/docs__refutations (ui record) | doc | TheStrat's refutation bundle covering moving averages and RSI alongside Fib/patterns/Elliott | The sceptical case every indicator student should read once, from a working levels method

## What could not be reached / limits

- The index records carry titles and summaries only; the underlying files live in the Femto-lean, Silicon, and local teardown trees and were not opened for this sweep. Every "what it is" above is grounded in the index record's own title/summary, not in a fresh read of the file.
- MACD produced no strong dedicated asset: it appears inside general indicator bundles rather than as a named chart-reading method in any top-ranked record. That is a genuine gap in the corpus, reported as found.
- Buy zones, invalidations, targets, and expected-path annotation standards are not indexed under their own keywords in this index (they live in the Best Setups material, indexed mainly under pattern/chart paths, e.g. the EL
...[truncated 463 chars]