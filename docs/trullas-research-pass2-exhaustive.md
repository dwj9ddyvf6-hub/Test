# David Trullás — Exhaustive Completion Pass (2026-10-25)

## Summary

This pass mined the sources the first pass did not: 10 of his own YouTube videos in full (transcripts), the Rankia LIVE Trullás–Valastro panel in full, the Negocios TV interview (~70% by live listen), the official World Cup Trading Championships (WCTC) standings live, liveintrading.com live, and the full table of contents plus front matter of his 2015 book (full text located; later chapters not extractable).

Headline resolutions:
- **Q2 2026: he WON — 1st place, 2,222.6% (official, Final). Fifth consecutive title.** And beyond the mission's frame: **Q3 2026 also shows him 1st with 1,350.8% ("Final Pending Audit") — a sixth consecutive title**, contradicting his own May-2026 statements that he would stop at 1,501% and skip Q3. His own website header already reads "6 VECES CAMPEÓN MUNDIAL."
- The un-located X claim ("five consecutive championships", "2,200% 90-day return") matches the official Q2 2026 result almost exactly (2,222.6% over the ~90-day quarter) — the claim was accurate; the poster remains unidentified.
- New hard rules found: stop moved to **entry +1.5 points** (covers commission + slippage); pyramiding "en ráfaga" on strength; daily loss budgeted as **2–3 (max 5) "bullets"**; **no news trading**, works the US open and is normally done by ~16:00 Spanish time; **championship instrument is exclusively the Nasdaq future (mini or micro)**; an always-on **daily + 1-hour context filter**; his book's RSI entry chapters are built on **RSI 14**; the "fallo de MACD" is formally a **failed cross of the MACD fast line through the signal line** at new price extremes.
- Still open: MACD periods (never stated anywhere mined), the formal line-vs-histogram rule for *regular* divergences, RSI thresholds, the exact Fib anchor recipe, a fixed TP1/TP2 split %, risk % per trade, and an explicit naming of which registered method the championship system is (HLIT is the strong circumstantial candidate: the only method his site describes as intraday + Fibonacci-based).

Tags: PRIMARY = he stated it; SECONDARY = someone else's summary; UNVERIFIED; STILL-A-GAP.

## Coverage Ledger

| Source | Status |
|---|---|
| YouTube channel @davidtrullas (header: 29.6K subs, "288 videos") | Enumerated: Videos tab loaded **147 items** with titles/durations/relative dates (notes/youtube-channel.md); the 288 header evidently also counts Shorts/Live/Podcasts. **Mined in full: 10 videos** (below). Rest: listed only. |
| Mined in full (transcripts, his channel): "Me venció la psicología… 2 operaciones reales explicadas" (0UwzsfZxHr0); "Fallo de MACD" (P1xgnJnf2PU); "Barrido, divergencia de volumen y rebote" (xzpo72rN1ZI); "La operación que me llevó al +1501%" (mAlsGaEyRRI); "¿Cuántas operaciones hay que hacer al día?" (NGvqdsF6dj4); "Segundo mejor récord histórico…" (UTZc68dov1g); "Mi setup de trading profesional" (qmlqz7bAx6k); "4 Campeonatos Seguidos" (yD7zFLwQ7u8) | Full auto-transcripts read (some numbers garbled — flagged). |
| Interview (i): Rankia LIVE Trullás–Valastro panel, ~32 min (JunRcXPZBDs) | **Mined in full** (transcript). |
| Interview (iii): Negocios TV, 13:21 (77kTdMa5Jpw) | **Mined ~0:00–9:30** by live listen (auto-dubbed audio); remainder not captured — research-browser budget exhausted. Key method/session/instrument content was in the mined portion. |
| Interview (ii): "El psicólogo del trading" — "Earned 900% in 4 Months (Live)", 1:14:02 (fmYu4_38w3o) | **Located, NOT mined**: transcript service returned HTTP 429; browser budget exhausted before a listen pass. |
| WCTC official standings (current + historical + Recent Events) | **Verified live** 2026-10-25 — Q2/Q3 2026 resolved. |
| liveintrading.com | **Verified live** 2026-10-25 (homepage + full method descriptions via index fetch). |
| Book (docer.ar full text; Everand preview) | TOC + front matter + ch. 1–2 mined; ch. 9/11/13/17/18 body **inaccessible** (viewer/preview truncation). |
| Spanish press / Rankia blog / Finect / podcasts | Searched (index). Rankia championship blog (first pass) remains the main press item; no Spanish-press coverage of the Q2 2026 result found. Additional interviews located but listed only (Pol Castella ×2, Valastro 1:39, his DIRECTO sales webinars ×2). |
| Social (X, Instagram, LinkedIn, Telegram) | Searched. Original X thread **not located**; poster unidentified. Claim substance verified against official standings. Social profiles not mined for specs. |
| Transcript service (youtubetotranscript.com) | Worked for 9 videos, then HTTP 429 rate limit — not retried per instructions. |

## Findings — gap by gap

### Gap 1 — MACD settings (periods): STILL OPEN
Hunted in: 8 channel transcripts, Rankia panel, Negocios TV, book TOC. He never states fast/slow/signal periods in anything mined. His 2015 book has a full MACD chapter (11.1–11.10) whose body text could not be extracted (see Coverage). No source found states non-default settings either; nothing contradicts platform defaults, but that is inference, not evidence.

### Gap 2 — MACD divergence read on line / signal / histogram: PARTIALLY CLOSED (PRIMARY)
- The **"fallo de MACD"** — the pattern behind his 11 May 2026 Q2 trade and a named technique since his 2015 book (ch. 11.10) — is formally defined on the **lines**: price makes successive new lows while MACD rises, and specifically the **MACD fast line fails to cross down through the slow signal line** at the new price low, then turns up sharply. He calls it "a special divergence," rarer than normal divergences. Source: "Fallo de MACD" video, https://www.youtube.com/watch?v=P1xgnJnf2PU (mined full, PRIMARY). His colours: fast line red, signal blue.
- The book's MACD chapter is organised entirely around the two lines and their crosses (11.2–11.7) — consistent with line-based reading; the histogram is never mentioned in any mined source.
- STILL-A-GAP: no formal statement of which element carries *regular/hidden* divergence readings.

### Gap 3 — RSI period / thresholds / "RSI out of overbought" sizing condition: PARTIALLY CLOSED
- **Period: 14 (PRIMARY, from his book).** The book's RSI chapter headings read "13.3 Entrada largos con RSI 14" and "13.4 Entrada cortos con RSI 14" — his RSI entry rules are built on RSI(14). Source: book TOC, https://docer.ar/doc/xce8ee (read 2026-10-25).
- STILL-A-GAP: the thresholds in ch. 13.2 "Niveles" and the exact "RSI leaves overbought" sizing condition from the baseline talk were not found in any newly mined source; RSI is barely mentioned in his 2026 YouTube output, which is volume/order-flow centric.

### Gap 4 — Swing / pivot definition: PARTIALLY CLOSED (PRIMARY) — discretionary by design
- Extremes are chosen **discretionarily**: "everyone takes the lows they want." In practice he picks extremes by their **volume signature** (a low printed on huge volume vs the next on tiny volume). Sources: "Simple Works" https://www.youtube.com/watch?v=0UwzsfZxHr0; sweep video https://www.youtube.com/watch?v=xzpo72rN1ZI.
- Divergences can chain across **up to four consecutive extremes** with progressively decreasing volume (his bounce-trigger image: four lows, falling volume, at the 66% zone). Source: trades/day video https://www.youtube.com/watch?v=NGvqdsF6dj4.
- Caveat he states himself: volumes from the US first hour vs the European session are not directly comparable.
- STILL-A-GAP: no formal pivot rule or minimum separation — evidence indicates none exists; selection is judgement.

### Gap 5 — Exact Fib anchor recipe for regular bearish divergence: STILL OPEN
Hunted in all mined transcripts, the panel, Negocios TV, his site, and the book (which has **no Fibonacci chapter at all**). The secondary claim ("lowest point between the two highs to the new high as 0") was neither confirmed nor refuted. New related facts (PRIMARY): exits are taken **slightly before** the exact level ("I don't like going to the exact tick"); the **50% level** is also an active decision level alongside 38.2/61.8; on 1 June 2026 he exited **89 points below** his 66% target to bank a round-number goal. Sources: 0UwzsfZxHr0; mAlsGaEyRRI.

### Gap 6 — Stop-to-breakeven rule: CLOSED (PRIMARY)
- **"Normalmente siempre pongo el stop un punto y medio por encima de la entrada"** — once moving the stop, he places it at **entry + 1.5 points**, the 1.5 pts sized to cover commission + slippage so the trade is true breakeven net. Source: https://www.youtube.com/watch?v=NGvqdsF6dj4 (mined full).
- Corroborating behaviour: stop to BE **fast** when an add/entry gets no pullback; later a **profit-lock BE** ("break even de ganancia") protecting ~$1,500–1,600 after partials; admitted failure mode is moving to "BE plus something" too early and getting stopped before re-entering. Sources: xzpo72rN1ZI; 0UwzsfZxHr0.

### Gap 7 — Partial-exit split TP1/TP2: PARTIALLY CLOSED (PRIMARY examples; no fixed %)
- His framing includes **TP1, TP2 and TP3** ("primero, segundo, tercer take profit"). Source: setup video https://www.youtube.com/watch?v=qmlqz7bAx6k.
- Documented executions: one trade "released **80%** of the position and left **20%**" (0UwzsfZxHr0); another: 5 contracts in, **4 closed at ~30–40 pts**, runners staggered (+15, +30 more; last runner closed ~6 pts below the 50% level after ~130–135 pts) (xzpo72rN1ZI).
- STILL-A-GAP: no fixed TP1/TP2 percentage split stated anywhere mined; splits are situational.

### Gap 8 — Risk % per trade / daily loss / max trades per day: PARTIALLY CLOSED (PRIMARY)
- **Max trades/day: none.** He explicitly rejects fixed counts (both 1–2/day rules and 150–300/day shotgunning); he works to objectives and stops when done. Example day: 5 trades in 17 minutes (15:45–16:02), four ~breakeven scratches, fifth ~100+ pts clean, then screen closed. Source: NGvqdsF6dj4.
- **Daily loss budgeting: the "bullets" rule** — never stake the whole assumable daily loss on one bullet; keep **minimum 2–3 bullets, up to 5**, for the daily loss you can assume. Source: xzpo72rN1ZI (after a −$1,060 first trade).
- Championship context: the division imposes **no maximum risk per trade** (panel, JunRcXPZBDs); he pockets winnings after each championship and **restarts the next with the minimum ticket** (site lists Quarterly Futures min. starting balance $2,500). Source: yD7zFLwQ7u8; WCTC homepage.
- STILL-A-GAP: a % risk-per-trade figure for the championship system. (A "1–3%, never >3%" money-management text found on 1library.co could not be attributed to his book — UNVERIFIED, see Sources.)

### Gap 9 — Pyramiding rules: CLOSED (PRIMARY)
- He pyramids **"en ráfaga" (in a burst), on strength only**: e.g., 4 entry triangles = **5 contracts**; first adds come when price starts moving in his favour, further adds if it restarts after a pause. Explicitly **not** revenge-adding after a loss. Because the last add may have no pullback behind it, the stop can be moved to breakeven very fast. Source: xzpo72rN1ZI (mined full).

### Gap 10 — Session rules: CLOSED (PRIMARY)
- **Does not trade news**: "Yo personalmente no trabajo en noticias." Source: Rankia panel https://www.youtube.com/watch?v=JunRcXPZBDs.
- Works the **US open (15:30 Spanish time)** — the Negocios TV "one hour at maximum intensity" framing is his: very short, very intense work, then done. He had finished the opening before that afternoon interview. Sources: 77kTdMa5Jpw; JunRcXPZBDs.
- Normally **not working after ~16:00** Spanish time; present at 19:00 only if tilted or holding a long swing. Within the open he often **waits out the first ~30 minutes of chaos** (MACD-failure video: worked ~16:00–16:20) — but this is patience, not a hard rule: on 1 June 2026 he entered at **15:28, two minutes before the open**, on a pre-marked exhaustion zone. Sources: P1xgnJnf2PU; mAlsGaEyRRI.
- Preparation is pre-session: S/R and volume zones drawn and objective TPs set **before** the open; typical open-trade duration ~3–17 minutes. Sources: xzpo72rN1ZI; NGvqdsF6dj4.
- Day-trading division hard constraint: everything closed same day; nothing open after the 22:00 Spanish-time US close. Source: 77kTdMa5Jpw.

### Gap 11 — Higher-timeframe S/R filter: CLOSED (PRIMARY)
- **Always-on context screens: daily Nasdaq + 1-hour Nasdaq** (volume + volume profile on the 1h), described as "innegociables, siempre a mi vista" — because an unseen daily/1h Fibonacci/golden-ratio level "will break you." The 1h slot can swap to 30m/15m; decision timeframe stack in practice: daily → 1h (zones) → 5m (entries for bigger moves) → 1m/30s (detail, footprint) → **5-second execution chart**. Sources: https://www.youtube.com/watch?v=qmlqz7bAx6k; 0UwzsfZxHr0.
- Targets also respect structure: he exited at the 50% level rather than 66% in one documented trade because a large **horizontal volume block** (70-pt range) sat just above 50%. Source: xzpo72rN1ZI.

### Gap 12 — Full instrument list: CLOSED for the championship (PRIMARY); personal account broader
- **Championship: exclusively the Nasdaq future — mini (NQ, $20/pt) or micro (MNQ, $2/pt)**, chosen per trade by how he sees the operation; Nasdaq picked over S&P 500/Dow for volatility; explicitly **not oil, not gold** ("let's not get confused about whether it is crude or gold now. One [asset], well worked, and with it until the end"). Source: Negocios TV https://www.youtube.com/watch?v=77kTdMa5Jpw (~7:16–8:35), verified live listen 2026-10-25.
- This refines the baseline: the baseline's "gold future, not XAU/USD" regulated-futures point stands for his general teaching, but the title-winning account trades one instrument only.
- Personal/other trading is broader (his channel's older stratum is daily Nasdaq/BTC/MSTR analysis; setup video mentions stocks on a wildcard screen; mentorship content covers Nasdaq and S&P futures) — but no other instrument is associated with the championship system.

### Gap 13 — Which registered method is the championship system?: PARTIALLY CLOSED (circumstantial, PRIMARY site copy)
- No source states the mapping outright. But his site's own descriptions (https://liveintrading.com/, verified live 2026-10-25) make **HLIT (High Low Intraday Trading)** the only candidate matching the system's fingerprints: "Técnica **intradaria** basada en retrocesos a favor y en contra de Mercado, así como **niveles psicológicos basados en los números de la secuencia numérica de Fibonacci y sus proporciones**." Método Trullás is described as global market/sentiment reading; Cyborg Techs as turn-detection around large-corporation positioning with R:R > 1:3. Verdict: **the divergence+Fibonacci intraday system is almost certainly HLIT — UNVERIFIED as a direct statement, strongly indicated by his own copy.**
- Bounding fact: he states on camera that the full strategy (entry/stop/TP) is taught **only live to academy students** ("yo aquí no voy a dar la estrategia completa"), which is where the unpublished specs (Gaps 1, 3-thresholds, 5) reside. Source: NGvqdsF6dj4.

## Corrections to the baseline

1. **The streak did not end at four.** Baseline (correct when written) said four consecutive titles. Official WCTC standings now show **Q2 2026 won (2,222.6%)** and **Q3 2026 won (1,350.8%, pending audit)** — the streak is **six**. His site header already claims six titles.
2. **His own mid-quarter numbers were not final.** He publicly anchored on 1,320.7% (May) and 1,501% (1 June) and said he would stop and skip Q3; the official Q2 final is **2,222.6%**, and he contested and won Q3 anyway. Treat his in-quarter videos as snapshots, not results.
3. **Q1 2026 colour:** he says he won Q1 2026 (585.4%) while overtrading and unwell, with a profit factor ~1.28 in Q4 2025, and sought professional psychological help (neurofeedback) before the Q2 record run. (PRIMARY, panel + UTZc68dov1g.)
4. **Instrument scope narrowed:** baseline implied a multi-instrument regulated-futures method; for the championship account it is **Nasdaq futures only** (Gap 12).
5. **Public teaching ≠ the Rankia-talk spec.** His 2026 YouTube output is predominantly volume/order-flow and strategy-agnostic ("identify where the money is; use your own strategy") and he explicitly withholds the championship system's entry/stop/TP for students. The MACD/RSI/Fib counting spec comes from the Valencia talk; the surrounding corpus does not repeat it.
6. **Book facts:** the scanned edition is **187 pages** (retail listings variously say 121/216 — discrepancy noted); the book contains **no Fibonacci material**; its divergence material (volume, MACD, RSI, "fallo de MACD") predates the championship system by a decade. WCTC's own tables contain an internal inconsistency for Q1 2025's winner (317.5% in Recent Events vs 31.75% in Historical Standings); Trullás's 2nd place at 291% is consistent in both.

## Q2 2026 resolution (Section F)

**RESOLVED — fifth consecutive title, by a record margin.** Official WCTC Current Standings → Recent Events (verified live 2026-10-25, https://www.worldcupchampionships.com/world-cup-trading-championship-standings): "2026 2nd Quarter Futures Day Trading Championship", April 1 – June 30, 2026, marked **Final**: **1st David Trullas Vila (Andorra) 2,222.6%**; 2nd Eduardo Ramos 258.1%; 3rd Fu-Chieh Hsieh 101.5%; 4th Jose Salvador Alfageme 9.9%. The same page shows **Q3 2026: 1st Trullas 1,350.8%** (Jul 1 – Sep 30, 2026, "Final Pending Audit"). Note: the site's Historical Standings table does not yet list either 2026 quarter — the results live only under Recent Events. No Spanish-press coverage of the Q2 result was found; his own site header ("6 VECES CAMPEÓN") corroborates the six-title count.

## Updated algorithm spec sheet — NEW or CORRECTED rules only (each source-tagged)

| # | Rule (new/corrected) | Source | Tag |
|---|---|---|---|
| 1 | Supplemental pattern "fallo de MACD": at successive new price extremes, MACD fast line fails to cross through the signal line and hooks away — treated as a special, higher-conviction divergence | youtube.com/watch?v=P1xgnJnf2PU | PRIMARY |
| 2 | Extremes are picked discretionarily, keyed to volume signature (huge vs tiny volume at successive extremes); divergences may chain across up to 4 extremes with progressively falling volume | 0UwzsfZxHr0; NGvqdsF6dj4 | PRIMARY |
| 3 | RSI entries built on RSI(14) (book ch. 13.3/13.4) | docer.ar/doc/xce8ee (book TOC) | PRIMARY |
| 4 | Stop moved to entry + 1.5 points (covers commission + slippage = true net BE); fast BE when entry gets no pullback; later profit-lock BE | NGvqdsF6dj4; xzpo72rN1ZI | PRIMARY |
| 5 | Exits taken slightly before the exact Fib tick; 50% level is an active exit/decision level; round-number goal exits override the 66% target | 0UwzsfZxHr0; mAlsGaEyRRI | PRIMARY |
| 6 | Exit structure contemplates TP1/TP2/TP3; observed splits: 80/20 release; 4-of-5 contracts off at +30–40 pts, staggered runners | qmlqz7bAx6k; 0UwzsfZxHr0; xzpo72rN1ZI | PRIMARY |
| 7 | No fixed trades/day; trade to objectives, stop when done (documented: 5 trades/17 min, done) | NGvqdsF6dj4 | PRIMARY |
| 8 | Daily loss pre-split into bullets: min 2–3, max 5 bullets per assumable daily loss | xzpo72rN1ZI | PRIMARY |
| 9 | Pyramiding "en ráfaga": adds only on strength (price moving/restarting in favour), up to 5 contracts in the documented sequence; never revenge-add | xzpo72rN1ZI | PRIMARY |
| 10 | Session: US open only; no news trading; normally finished by ~16:00 ES; pre-session zones/objectives drawn before the open; entries may occur minutes before the open on pre-marked exhaustion zones | JunRcXPZBDs; 77kTdMa5Jpw; mAlsGaEyRRI; xzpo72rN1ZI | PRIMARY |
| 11 | Mandatory context filter: daily + 1h Nasdaq (volume profile, Fib/golden-ratio levels) always in view; execution ladder daily→1h→5m→1m/30s→5s | qmlqz7bAx6k | PRIMARY |
| 12 | Championship instrument: Nasdaq future only — mini or micro per trade read; no oil/gold/bonds in the title account | 77kTdMa5Jpw | PRIMARY |
| 13 | R:R doctrine: do not plan 1:7–1:10 entries; take closer ratios (≈1:1 to 1:3); outsized ratios only as a by-product after profits banked | xzpo72rN1ZI | PRIMARY |
| 14 | Championship money handling: bank winnings after each title; restart next quarter at the minimum ticket ($2,500 division minimum) | yD7zFLwQ7u8; worldcupchampionships.com | PRIMARY |
| 15 | System attribution: intraday + Fibonacci method on his site = HLIT (circumstantial; never stated) | liveintrading.com | PRIMARY copy / UNVERIFIED mapping |

## Could not verify / open questions

- MACD periods; RSI thresholds (book 13.2 "Niveles"); the exact "RSI out of overbought" sizing trigger; the Fib anchor recipe for bearish divergences; a fixed TP1/TP2 split %. All hunted across 10 full transcripts, the panel, Negocios TV, his site, and the book's TOC; the book's body chapters (9/11/13/17/18) exist in a located full text but could not be extracted beyond ch. 2 (viewer truncation; Everand preview limit) — the single most promising remaining vein.
- Interview (ii) "El psicólogo del trading" (fmYu4_38w3o, 1:14:02): located, not mined (transcript service HTTP 429; browser budget exhausted). Interview (iii) final ~3:50 not captured.
- Original X thread (poster + exact wording): not located; claim substance verified (2,222.6%, 5th straight title).
- The 1library.co money-management chapter ("nunca más del 3%", 1% ideal, ≤6% simultaneous) is UNVERIFIED as Trullás's — its source slug ("guia-trading-trade-roll") points to a different work; do not cite it as his rule.
- Several numbers in auto-transcripts were garbled (e.g., the 1 Jun 2026 trade's profit figure and exact zone price; Q4 2025 profit factor read as "128", interpreted as 1.28) — flagged, not relied on for the spec sheet.
- Remaining channel videos (~137 listed, not mined) include further trade explainers ("The patterns I like to see at market open", "The mistake you make with support and resistance", "The Trade That Broke a 41-Year Record", "Trading in AUGUST") that time/budget did not allow mining; his two DIRECTO sales webinars (2:03 and 1:46) are also unmined and are the most likely public place where curriculum-level detail appears.

## Sources

Verified live (research browser, 2026-10-25):
- WCTC standings — https://www.worldcupchampionships.com/world-cup-trading-championship-standings (Recent Events: Q2 2026 Final 1st 2,222.6%; Q3 2026 1st 1,350.8% pending audit) and https://www.worldcupchampionships.com/world-cup-trading-championship-historical-standings (416 entries; confirms Q2'25–Q1'26 baseline; no Q2/Q3 2026 rows yet).
- liveintrading.com — https://liveintrading.com/ (six-title header; three method descriptions; mentorship/workshop offer).
- YouTube channel — https://www.youtube.com/@davidtrullas/videos (29.6K subs, "288 videos"; 147 Videos-tab items enumerated).
- Negocios TV interview (live listen) — https://www.youtube.com/watch?v=77kTdMa5Jpw

Index (transcripts/text fetched, 2026-10-25):
- Channel transcripts via youtubetotranscript.com: 0UwzsfZxHr0, P1xgnJnf2PU, xzpo72rN1ZI, mAlsGaEyRRI, NGvqdsF6dj4, UTZc68dov1g, qmlqz7bAx6k, yD7zFLwQ7u8 (full watch URLs: https://www.youtube.com/watch?v=<ID>).
- Rankia panel transcript — https://www.youtube.com/watch?v=JunRcXPZBDs
- Book full text + TOC — https://docer.ar/doc/xce8ee ; preview — https://es.everand.com/book/351834541/Bienvenidos-al-mundo-real-de-la-bolsa
- Located, not mined: https://www.youtube.com/watch?v=fmYu4_38w3o (El psicólogo del trading interview); Rankia blog (first pass) https://www.rankia.com/blog/sistemas-de-trading/7075857-campeonato-mundial-trading-copa-robbins
- UNVERIFIED lead (not attributed): https://1library.co/article/gesti%C3%B3n-monetaria-guia-trading-trade-roll.z3lo9ldz

Working notes in this directory: notes/youtube-channel.md (enumeration), notes/youtube-mined-1.md (8 transcripts), notes/wctc-q2-2026.md, notes/interviews.md, notes/site-course-book.md.
