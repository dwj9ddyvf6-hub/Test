# Decisions API Incorporation Study — Quantitative Trading Research Operation

**Research date:** 2026-11-10. **Operation context:** nightly full-analysis chart studies on 100 stocks; a graded forecast ledger scored with Brier scores against climatology; dozens of forecast engines; audits of third-party trading-tool claims; weekly head-to-head grading of two AI analysts.

**Evidence flags used throughout:** **[verified live]** = read on the publisher's own page in the research browser on 2026-11-10. **[index]** = found via web-index search results / secondary summaries, not opened live. **[vendor claim]** = asserted by the seller or a launch customer, with no independent reproduction found. **[thin / contradicted]** = single, synthetic, non-peer-reviewed, or disputed source.

---

## Summary — the five answers in one page

1. **The Decisions API is real, GA, and narrow — and it does NOT claim its probabilities are calibrated.** GA 22 Oct 2026, `POST /v1/decisions`, only model `gpt-6-luna`, 1–400 typed questions per request over shared evidence, $0.10/1M uncached input tokens, $0.01 cached reads, $0.125 cache writes (30-min TTL), output free. The official guide calls the predicate result *"an estimate"* and tells you to set thresholds from *your own labelled examples* based on false-positive/false-negative costs. It publishes **no accuracy, calibration, ECE, or latency distribution figures**. The "about 10× faster than the Responses API" line is a **[vendor claim]** with no workload, p50/p95, or independent reproduction. A LangChain integration page calling the probabilities "calibrated" is **[contradicted]** by the guide itself. Treat every Decisions probability as an *uncalibrated score until your ledger proves otherwise, per question family*.

2. **LLM probabilities carry real discrimination but unreliable levels.** The best modern result pattern: models rank outcomes (AUC 0.61–0.72 in a 2026 post-cutoff benchmark) while stating probabilities too extreme (or, in retrieval forecasting systems, too timid) for that ranking — so a one-parameter shrinkage / Platt recalibration fitted on *disjoint* resolved data recovered a mean 0.0223 Brier. Verbalized confidence beat token probabilities by ~50% relative ECE in Tian et al. (2023), but factoid-QA calibration does not transfer to forecasting or chart judgment. Aggregation helps (ensembles, trimmed means, human+machine blends beat either alone); extremizing helps only when judges hold *diverse, independent* information — LLM judges sharing a model/prompt do not.

3. **The bitter lesson cuts both ways for this operation.** Search + learning at scale beat hand-crafted features in chess, Go, speech, vision, and now weather (GraphCast beat ECMWF HRES on >90% of 1,380 targets). But Sutton's own 2025 position is that LLMs are on the *human-knowledge* side of his lesson — they predict what a person would say, not what will happen. A Decisions judge becomes a bitter-lesson system only if the operation closes the loop with resolved-outcome learning (its ledger). In finance, the binding constraint on brute-force pattern search is not compute but multiple testing: 316 published factors by 2012 (Harvey–Liu–Zhu: require t ≥ 3.0), deflated Sharpe, White's Reality Check (7,846 rules), and genetic mining that went from in-sample Sharpe 4.1 to out-of-sample −0.3. **Scale the search only as fast as you scale the validation.**

4. **Typed-probability systems at scale are well-calibrated in aggregate and beatable in detail.** ~1.01 million prediction-market/forecasting-platform forecasts (PNAS 2026) were highly calibrated overall, with systematic domain biases. Superforecasters still lead LLMs on ForecastBench in the most recent uncontested readings (difficulty-adjusted Brier 0.081 vs 0.101 for the best LLM, Feb 2025; ~0.089 vs ~0.103, May 2026), 2026 "parity" claims are **[contradicted]** (frozen solo human baseline), Metaculus Pros have beaten bots in every quarterly tournament, and on Prophet Arena even the best LLM (Brier 0.184, beating the market's 0.187) returned only 0.943 per unit staked — *calibration ≠ profit after costs*, exactly the trading analogue.

5. **Engineering: the judge is an instrument, not an oracle.** Batch independent questions over shared evidence (dependent questions = separate requests); keep question wording frozen or your thresholds are void; fit two-band (act / review / reject) thresholds per question from labelled data and a cost matrix, never a default 0.5; add a per-family recalibration layer fitted only on resolved ledger outcomes; run a fixed ~200-item canary weekly to detect judge drift (you cannot pin a dated Decisions snapshot — none was found — so canary + recalibration + date-segmented ledgers are your only defence); blind and order-swap the weekly analyst grading against position/verbosity/self-preference bias; and log full provenance for every verdict so any number can be re-derived or disowned.

**Worked nightly cost (illustrative arithmetic, not a quote):** if one stock's evidence is ~20,000 input tokens, 100 stocks = 2M tokens = **$0.20/night uncached** at $0.10/1M. Re-asking a different question bank over the *same* stock evidence within the cache window costs ~$0.02 in cached reads after a $0.25 cache write for that 2M tokens — caching pays for re-interrogation of the same evidence, not for first-pass coverage of 100 different stocks.

---

## Findings

### 1. The Decisions API itself

#### 1.1 Status, timeline, and what it is

| Fact | Value | Basis |
|---|---|---|
| Endpoint | `POST /v1/decisions`; SDK `client.decisions.create(...)` | Guide + create-decision reference **[verified live]** |
| Model | `gpt-6-luna` — the *only* supported model; no way to trade up for accuracy inside the endpoint | Guide **[verified live]** |
| Limited preview | 29 Sep 2026 (DevDay) | Secondary launch coverage **[index]** |
| Public beta | 6 Oct 2026 — 200 questions/request, $0.10/1M flat, no cache charges | Changelog via secondaries **[index]** |
| GPT-Live integration | 15 Oct 2026 | Changelog via secondaries **[index]** |
| General availability | **22 Oct 2026** — 400 questions, prompt caching, JSON input, per-question images, hosted image URLs, conversation history, org usage reporting, Private Link | Guide + changelog **[verified live / index]** |
| Launch customers named | Box, Datadog, Ramp, Sierra, Speak | Launch coverage **[index, vendor claim]** |
| Luna model facts | Context window 1,050,000 tokens; max input 922,000; max output 128,000; knowledge cutoff 18 May 2026; launched 22 Sep 2026 | Model page via search **[index]** |
| Data controls | Zero Data Retention and HIPAA for eligible customers; data residency in all supported API regions; regional processing US and Europe (EEA + Switzerland) | Guide **[verified live]** |

Use Decisions when you need one of its three answer types; use Structured Outputs / Responses when you need a generated object, extracted fields, an explanation, or a tool call. The guide is explicit on that boundary. **[verified live]**

#### 1.2 Exact request schema

A request has three core parts, plus optional caching/safety controls (create-decision reference **[verified live]**):

- **`model`** — string, only `gpt-6-luna`.
- **`input`** — string, or an ordered array of messages, function calls and outputs, or custom tool calls and outputs. Each tool output must identify its matching call by `call_id`. This is the *shared evidence* for every question.
- **`questions`** — array, **minItems 1, maxItems 400**; each is a Predicate, Choice, or Score object; answers come back in the same order.
- **`prompt_cache_key`** — string, maxLength 64; partitions cache reuse by caller key.
- **`prompt_cache_options`** — `{mode, ttl}`; supported for gpt-5.6 and later; by default OpenAI chooses one implicit breakpoint; explicit breakpoints can be added per content block (`prompt_cache_breakpoint`), up to **4 breakpoints written per request**, with up to the **latest 80 breakpoints** considered for matching; `ttl` defaults to `30m`, *"which is currently the only supported value"* in the reference.
- **`safety_identifier`** — string, maxLength 128; opaque end-user identifier, never the authenticated identity.

There is **no** `temperature`, `reasoning`, `stream`, `store`, `tools`, or `text.format` on this endpoint (secondary API summaries **[index]**) — if a workflow needs reasoning traces or tools, it does not belong in Decisions.

**Input content by role** (guide **[verified live]**):

| Input item | Supported content |
|---|---|
| User message | Text, images, and JSON |
| Developer / system message | Input text only; system messages are treated as developer messages |
| Assistant message | Output text or refusals |
| Function / custom tool output | Text and images, associated with a matching tool call |

- **`input_json`** content part: pass a JSON object/array in `data` inside a *user* message only. Keys such as `role` or `image_url` inside `data` are ordinary data — they do not create messages or fetch images. JSON input does not change the response format.
- **Not supported:** files, audio, item references, `file_id` inputs.
- **Images:** inline base64 data URLs or (at GA) publicly accessible HTTP/HTTPS URLs. Question-specific images: set a question's `instructions` to a non-empty array of `input_text` / `input_image` parts (no message wrapper, no `role`); add one question per candidate image. **Image limit: 128 images per request total**, shared between `input` and question instructions — the *number* 128 comes from API-reference summaries / gateway docs **[index]**; the guide text itself says only that question images "share the request's image limits." Image `detail` options (`low`/`high`/`auto`/`original`) are reported by a gateway doc **[index, thin]**.
- *Implication for chart studies:* one stock = one request (evidence differs per stock). 100 stocks = 100 requests/night minimum, each carrying its chart image(s) + structured JSON via `input_json`. There is no way to batch 100 unrelated stocks into one request — questions in a request all evaluate the *same* input.

#### 1.3 Exact response schema — the three answer types

Response object: `Decision {answers, model, usage}`. Give each question a unique `name`; the API echoes it — match answers **by name, not only by position**. Any question can instead return a **refusal**: `{type: "refusal", name}` (name may be `null` if unnamed); other answers in the same response remain valid. Usage example in the reference: `input_tokens: 42, output_tokens: 0, total_tokens: 42`, with `input_tokens_details: {cached_tokens, cache_write_tokens}`. **[verified live]**

| Type | You supply | Answer contains | Guide example |
|---|---|---|---|
| `predicate` | `instructions`, `name` | `probability`: estimate 0–1 that the condition is true. **No confidence field** — the probability *is* the answer. | `visible_damage` → 0.92 |
| `choice` | `instructions`, `name`, `choices`: **2–255 unique** `{value, description}`; value is string or boolean (`true` and `"true"` are *distinct* values) | `choice` (one supplied value), `probabilities`: `[{value, probability}]` for every option, and a separate `confidence` | `department` → `"billing"`, probabilities 0.95/0.02/0.01/0.02, `confidence: 0.93` |
| `score` | `instructions`, `name`, `levels`: **2–10** ordered `{label, description}`, lowest→highest, indices from 0 | `score`: **probability-weighted average of level indices** (can fall between levels), `probabilities`: `[{value: index, label, probability}]`, and `confidence` | Levels 0/1/2 with probabilities 0.1/0.7/0.2 → `score: 1.1`, `confidence: 0.55` |

Rules the guide states: use `choice` for unordered categories, `score` for ordered levels; include a fallback such as `"other"` when categories may not cover the input; put independent questions in one request; **for decisions that depend on an earlier answer, send separate requests**; write questions around observable criteria, separate different concerns into different questions, give choices distinct meanings and adjacent score levels distinct criteria. A predicate probability of 0.5 means an even split between yes and no — it does **not** mean "medium"; that is what `score` is for (LangChain integration doc **[index]**, consistent with the guide).

#### 1.4 Pricing — full table, with the traps

Decisions charges **input tokens only; output tokens are $0** on `/v1/decisions` (general Luna Responses output is $0.50/1M short-context — do not confuse the two). **[verified live for the $0.10 + output-free + "cache rates match standard Luna" statements; detailed rates below are [index] from OpenAI pricing-page summaries checked 25 Oct – 9 Nov 2026]**

| Token type (per 1M) | Short context (≤272K input) | Long context (>272K input, *whole request* repriced) |
|---|---|---|
| Uncached input | **$0.10** | $0.20 |
| Cached input (read hit) | **$0.01** | $0.02 |
| Cache write, 30-min TTL | **$0.125** | $0.25 |
| Cache write, 12-hour TTL | $0.25 | $0.50 |
| Output (Decisions) | **$0** | $0 |

Traps, all material to this operation:

1. **A cache write costs more than an uncached call** (1.25× at 30-min, 2.5× at 12-hour). Caching only pays on reuse: write-once + read-once = 1.35× the cost of one uncached pass vs 2× for two uncached passes (OpenAI prompt-caching guide **[index]**).
2. **272K cliff:** crossing 272,000 input tokens reprices the *entire* request at long-context rates, not just the excess.
3. **Regional processing +10%** where used. Long-context and regional multipliers both apply per the guide.
4. **TTL contradiction [thin]:** pricing summaries list a 12-hour cache-write rate, but the create-decision reference says `ttl` defaults to `30m` *"which is currently the only supported value."* Budget on 30 minutes until OpenAI resolves this; do not design a nightly pipeline that assumes a 12-hour Decisions cache.
5. Beta pricing ($0.10 flat, no cache charges) is history — any October-early cost model is stale.
6. No Decisions row was found on the general pricing page by several reviewers; the $0.10 lives in the Decisions guide. Verify in your own `usage` object, not from blog tables.

**Prompt caching mechanics (Decisions-specific, guide [verified live]):** caching applies to the shared `input` prefix only — content in `questions`, including question images, is *outside* the reusable prefix and does not count toward the minimum. Default implicit breakpoint at the end of shared `input`. Reusable prefix must be **≥1,024 tokens**. Keep the prefix byte-identical across requests. Check `usage.input_tokens_details.cached_tokens` and `cache_write_tokens`; both are *included in* `usage.input_tokens` — do not add them again.

**Organisation usage reporting:** `GET /v1/organization/usage/decisions` with an admin API key (`api.usage.read`); filter/group by project, API key, model. `num_model_requests` counts **requests, not questions** — a 400-question request counts once, so question-level cost accounting must be done in your own logs. **[verified live]**

#### 1.5 Rate limits and tiers — no Decisions-specific limits exist

No Decisions-specific rate limits are published; the endpoint inherits **gpt-6-luna's** limits. On 6 Oct 2026 OpenAI simplified five paid tiers to three (Build / Launch / Grow) plus a geography-limited Free tier; organisations move up automatically as cumulative credit purchases cross thresholds. **[index — summaries of OpenAI's rate-limits guide checked 7–17 Oct 2026; verify on your own Limits page, as limits apply at both organisation and project level and are not an SLA]**

| Tier | Qualify (total credit purchases) | Monthly usage limit | Luna standard limits |
|---|---|---|---|
| Free | Allowed geography | $100 | — (see Limits page) |
| Build | $5 | $500 | 5,000 RPM / 2M TPM |
| Launch | $100 | $5,000 | 10,000 RPM / 10M TPM |
| Grow | $500 | $200,000 | 30,000 RPM / 180M TPM |

For this operation the limits are not the constraint: 100 nightly requests is trivial against even Build-tier RPM/TPM. The monthly *usage cap* is the real gate at scale if question banks or intraday re-runs grow — Grow's $200,000 ceiling requires only $500 of cumulative purchases, down from $1,000 under the old five-tier ladder.

#### 1.6 Latency — vendor claim only

- Guide: *"about 10× faster than the Responses API."* No comparison workload, regions, request sizes, processing tier, sample count, p50/p95, error rate, or raw traces are published. Multiple independent reviewers (AccessAllGPT, LLM Matchmaker, Masterprompting) explicitly note they did **not** run the endpoint. **[vendor claim]**
- Launch reporting derived from OpenAI / TechCrunch: response times **100–180 ms** vs 1–3 s for earlier workflows; demos ~150 ms; a forward target of 60 ms floated by the API product lead. Customer numbers, all via OpenAI launch material: Speak cut inter-action time **1.4 s → 0.13 s**; Datadog p95 ~40× faster on agent-command risk assessment; Ramp 4× faster and 30% lower cost on cost attribution; Sierra <280 ms p95 at ~90% lower cost per call. **[vendor claim — workload-specific, not a guarantee]**
- Counter-signal: a launch roundup reports the Artificial Analysis Decision Index ranking OpenAI's entry **8th and 14th** on two public indices, behind TypeSafe's Jev and others **[index, thin]**. Speed leadership in the category is not established.
- *Operational reading:* at nightly-batch scale latency is irrelevant; it matters only if the operation later moves Decisions into intraday or voice/agent loops. Measure your own p50/p95 by evidence size before believing any of the above — image-heavy chart requests will not behave like 447-token ticket-routing demos.

#### 1.7 Interpreting probabilities, confidence, and thresholds — what OpenAI does and does not say

What the guide **does** say **[verified live]**:

- Predicate: *"The `probability` is the model's estimate that the condition is true. Use it to flag photos for review based on a threshold you choose."*
- Choice/score answers return a probability distribution *and a separate `confidence` field* — see the guide's "Interpret the answers" guidance on setting thresholds.
- *"Use labeled examples from your application to set thresholds for routing, filtering, or review. Choose thresholds based on the cost of false positives and false negatives."*

What the guide **does not** say:

- **No formula or definition for `confidence`** was found in the guide or reference beyond it being a separate field. Do not assume `confidence` = top-option probability, and do not interpret it as "probability the answer is correct." (For the competing Jev model, its integrator docs state explicitly that confidence summarises *how concentrated the distribution is, not the chance the judgment is correct* — a useful prior for how to treat OpenAI's field until OpenAI defines it, but **not** an OpenAI statement.) **[thin for OpenAI]**
- **No calibration claim, no accuracy figures.** See §1.8.
- No published error-code catalogue in the guide (a reviewer advises writing handlers defensively) **[index]**.
- No dated model snapshot for Decisions was found — see §5.5: this is the single largest operational risk in the whole study.

#### 1.8 Are the probabilities calibrated? — Evidence: no claim, no data

This is the question the whole incorporation turns on, so it gets its own subsection.

- The guide describes predicate probability as *"an estimate from 0 to 1."* It **never** uses "calibrated" for Decisions, publishes no reliability diagram, ECE, Brier score, or benchmark accuracy, and directs users to validate on their own labelled data. One rate-limit reviewer summarised the guide bluntly: *"0 accuracy or calibration figures in the guide."*
- **Contradicted claim:** LangChain's Decisions integration page says the API *"returns typed answers and calibrated probabilities."* That word appears nowhere in OpenAI's guide/reference as read on 2026-11-10. Treat the LangChain phrasing as integrator marketing, not evidence. **[contradicted]**
- **Contrast with the competitor:** TypeSafe explicitly markets Jev as trained with "Reinforcement Learning for Calibrated Decisions (RLCD)" and defines calibration for it. OpenAI makes no equivalent training claim for Luna-on-Decisions — Luna is a general model *reconfigured* for the endpoint, per launch reporting, not a purpose-trained decision model. **[index]**
- **No independent calibration study of Decisions was found** — no third party in the reviewed material had called the live endpoint and scored its probabilities against outcomes at any scale. Every calibration number in §2 below is about *other* LLM probability elicitation methods and is, at best, a prior for what to expect.

**Conclusion for the ledger:** a Decisions predicate probability of 0.92 on "chart shows a bullish engulfing pattern" means "the model's estimate is 0.92." Whether events the model scores 0.9 actually occur ~90% of the time *on your question families* is an empirical question only your resolved ledger can answer — which is precisely the infrastructure this operation already has. That is the correct order of operations, and §5 turns it into a procedure.

---

### 2. The science of using LLM-produced probabilities as forecasts

#### 2.1 Calibration of verbalized vs token probabilities

- **Tian et al., "Just Ask for Calibration" (EMNLP 2023, arXiv:2305.14975):** for RLHF models (GPT-4, ChatGPT, Claude 1/2, Llama-2-70B-chat), **verbalized** confidences (the model states a number) were typically better calibrated than the model's **conditional token probabilities**, *"often reducing the expected calibration error by a relative 50%"* on TriviaQA, SciQ, and TruthfulQA. Synthesis notes put best-prompt GPT-4/Claude-2 ECE at ~0.03–0.04 on factoid QA with two-step or top-k elicitation. Caveats that matter here: (a) RLHF *worsens* token-probability calibration relative to base models; (b) models remained systematically overconfident in absolute terms; (c) all measurements are in-distribution factoid QA — nothing about forecasting, images, or finance. **[index]**
- **Kadavath et al., "Language Models (Mostly) Know What They Know" (2022, arXiv:2207.05221):** larger models are well-calibrated on multiple-choice and true/false questions *when formatted appropriately*; P(True) self-evaluation (generate an answer, then score the probability it is true) shows encouraging calibration and scaling; but P(IK) ("I know this") generalises only partially and *struggles with calibration on new tasks*. Lesson: calibration is **format- and distribution-dependent**, not a property of the model. A question-bank redesign is a calibration event. **[index]**
- **Token vs verbalized, applied to Decisions:** Decisions probabilities are neither classic logits nor free-text verbalizations — they are a third, undocumented elicitation channel. That is another reason §1.8's conclusion holds: the Tian/Kadavath results license optimism that the numbers *carry signal*, not that their *levels* are right.

#### 2.2 The discrimination-without-calibration pattern (the most important recent result for this operation)

**Whelan 2026 calibration benchmark [index, non-peer-reviewed but fully specified]:** 8 frontier models, 15 model-mode entries, 143 binary prediction-market questions resolved *after* every model's training cutoff, base rate 36.4% YES (climatology Brier = 0.2314).

- **0 of 15 entries significantly beat climatology** on raw Brier.
- Yet **every entry had genuine discrimination**: AUC 0.61–0.72, bootstrap intervals excluding chance in all 15 cases.
- Murphy decomposition: **resolution and reliability loss were roughly equal and opposite** — models rank outcomes correctly, then state probabilities *too extreme* for that ranking, and the two cancel.
- **One fitted parameter per model** — shrinkage of stated probabilities toward the base rate, fitted entirely on **205 disjoint held-out markets** and applied unchanged — improved all 15 entries by a **mean 0.0223 Brier** and put **11 of 15 significantly below out-of-sample climatology**, where 0 of 15 were before.

For a chart-study operation this is the central empirical expectation: **Decisions predicates will likely sort stocks better than chance long before their raw probabilities beat climatology.** Score raw *and* recalibrated forecasts separately in the ledger, or you will discard a useful engine for a fixable level error — or, worse, trade on unshrunk extremes.

#### 2.3 Proper scoring rules — the ledger's mathematics

- A scoring rule is **strictly proper** when expected score is uniquely optimised by reporting your true belief (Gneiting & Raftery 2007, JASA, "Strictly Proper Scoring Rules, Prediction, and Estimation"). The programme: *maximise sharpness subject to calibration* (Gneiting, Balabdaoui & Raftery 2007).
- **Brier score (Brier 1950):** BS = mean (p − o)², o ∈ {0,1}. 0 = perfect; always-50% on binary questions = 0.25. *Convention warning for the ledger:* some tournaments (original Good Judgment Project) sum the squared error over both outcomes, giving a 0–2 scale where always-50% = 0.5. ForecastBench-style scores in this report (e.g. 0.093) are on the 0–1 mean convention. Never compare numbers across conventions.
- **Log score:** −log p(outcome). Also strictly proper; penalises confident-and-wrong *unboundedly* (p→0 on a realised event → ∞), where Brier caps the damage at 1. Use log score as a secondary ledger metric specifically to catch engines that hide tail overconfidence inside a decent Brier — and use it in *audits* of third-party claims, where a single 0.99-and-wrong call should hurt.
- **Murphy (1973) decomposition:** BS = Reliability − Resolution + Uncertainty, where Uncertainty = base rate × (1 − base rate) = exactly the Brier score of **climatology** (always predicting the base rate). Hence **Brier Skill Score BSS = 1 − BS / BS_climatology**: BSS > 0 beats climatology, BSS = 0 is climatology, BSS < 0 is worse than knowing nothing but the base rate. Report all three components per engine per question family: reliability tells you if recalibration can save it; resolution tells you if there is signal worth saving; uncertainty tells you how hard the question set was. A constant base-rate forecast is *perfectly calibrated with zero resolution* — calibration alone proves nothing, which is also the correct rebuttal to vendor "well-calibrated" marketing (§4.1).
- **Diebold–Mariano-style tests** on per-question score differences are the standard for "is engine A actually better than engine B" rather than comparing two mean Briers by eye (referenced in the proper-scoring literature surveyed). With dozens of engines, pairwise winner-picking without a test and a multiple-comparison correction is factor mining in miniature (§3.4).

#### 2.4 Measured LLM forecasting results at scale

| Study | Design | Key numbers |
|---|---|---|
| Halawi et al., NeurIPS 2024 | Retrieval-augmented GPT-4 system, 914 test questions published after LM cutoffs, from 5 competitive forecasting platforms | System Brier **0.179** vs human crowd **0.149**; GPT-4 without retrieval **0.208**. System rarely outputs probabilities <0.1 or >0.9 (attenuation toward 0.5) |
| Schoenegger et al., Science Advances 2024 | 12-LLM ensemble ("silicon crowd"), 31 binary questions, vs 925 human forecasters, 3-month tournament | LLM-crowd median Brier **0.20** vs human crowd **0.19**, p = 0.850 — but n = 31 and the equivalence bound (±0.081) is so wide a constant-50% forecaster would also "qualify" **[thin by design]** |
| Prophet Arena, 2025 (arXiv:2510.17638) | 1,367 resolved events / 72,136 binary markets sourced live from Kalshi; Brier + calibration (ECE) + simulated market return | GPT-5 [with reasoning] Brier **0.184**, ECE **0.042**, avg return **0.943** vs market baseline **0.187 / 0.069 / 0.899**. Top-model Brier band 0.17–0.24; ECE ≤0.05 strong vs 0.05–0.20 weak. See §4.4 |
| ForecastBench, 2024–2026 | Dynamic, contamination-free benchmark (markets + platforms + datasets), superforecasters vs public vs LLMs | See §4.4 table |
| Merger-arbitrage LLMs, 2026 | Fine-tuned LLM system, 404 large deals, 42 countries, held-out, strict temporal integrity | Class-balanced Brier **0.151** vs Platt-scaled market-implied **0.199**, XGBoost **0.186**, frontier LLMs on identical context **0.201–0.259**. See §4.5 |

#### 2.5 Forecast combination, ensemble weighting, and extremizing

- **Bates & Granger (1969) → the forecast combination puzzle (Stock & Watson 2004; Smith & Wallis 2009):** combined forecasts beat single models, but **simple averages repeatedly beat estimated "optimal" weights**, because finite-sample error in estimating the weights eats the theoretical gain (improvements are small — a few % of MSFE — but consistently in the same direction). Default for this operation's dozens of engines: **equal-weight or median combination first**; earn the right to use fitted weights with out-of-sample evidence, per family.
- **Halawi blend result:** a **4:1 crowd-to-system weighted average scored Brier 0.146 — better than the crowd alone (0.149) or the system alone (0.179)** — because human and LM errors are partly independent. Trimmed-mean aggregation (drop extremes before averaging) also outperformed in their tests. Direct analogue: blend Decisions with your existing engines and any market/climatology anchor; do not replace them with it.
- **Schoenegger Study 2:** showing GPT-4 / Claude 2 the human median improved their accuracy **17–28%**, but **simply averaging human and machine forecasts beat either model "updating" on the human number** — LLMs anchor badly on a supplied aggregate. Pipeline rule: elicit independent forecasts first, combine mechanically; never feed one engine's output into another engine's prompt and call the result an ensemble.
- **Extremizing (Baron, Mellers, Tetlock, Stone & Ungar, Decision Analysis 2014; Satopää et al., Int. J. Forecasting 2014):** aggregated human forecasts are systematically too timid, for two reasons — end-of-scale compression (random error pushes averages toward 0.5) and each judge discounting the information *other* judges hold. Pushing the aggregate away from 0.5 in log-odds space fixes both. Satopää's single-parameter logit aggregator, on 1,300+ experts forecasting 69 geopolitical events, beat widely used aggregators and is robust *because* it has one parameter. Practitioner synthesis of the GJP work: extremizing factor ~**1.2–1.5 for regular teams, ~1.0 (none) for superforecaster teams** already sharing information.
  - **Boundary condition that governs LLM use:** extremizing assumes judges hold *diverse, partly independent* information. Multiple Decisions calls with the same model, same evidence, and near-identical prompts are maximally correlated — extremizing them manufactures confidence from repetition. Extremize across *genuinely different* engines/analysts/models; never across re-wordings of one question to one model. Note also the direction conflict in the literature: GJP crowds need extremizing *away* from 0.5, while Whelan's frontier models (§2.2) need shrinkage *toward* the base rate, and Halawi's system attenuates toward 0.5 on its own. **The correct transform is an empirical property of your ledger, per family — fit it, don't import it.**

#### 2.6 Known failure modes — checklist for question-bank design

1. **Overconfidence at the extremes** (Whelan §2.2; Tian: verbalized scores still inflated, especially on wrong answers). Mitigation: shrinkage/capping fitted on resolved data; Metaculus winners cap predictions and capping was the strongest within-winner differentiator (r = +0.48, p = 0.005) **[index]**.
2. **Attenuation / underconfidence** (Halawi: RLHF systems avoid <0.1 / >0.9; Prophet Arena: LLMs systematically *conservative* vs market at the extremes). Over- and under-confidence are both documented — in different elicitation regimes. Another reason no imported transform survives contact with your data.
3. **Acquiescence bias** (Schoenegger 2024): mean LLM predictions significantly above 50% despite an almost even split of resolutions — models find reasons *for* the proposition as worded. Mitigation: ask every predicate in both polarities on a sample ("pattern will resolve up" / "pattern will fail") and measure the inconsistency; balance YES-base-rate across the bank.
4. **Base-rate neglect / inside-view anchoring:** superforecasting protocol exists largely to fight this (outside view first). In the 2025 prompt study (38 prompts × 4 frontier models × 100 questions), **no prompt technique survived Benjamini–Hochberg correction**; the largest point improvements were frequency-format reasoning (−0.014 Brier) and base-rate-first (−0.011), and explicitly "Bayesian" prompts *hurt* (+0.005 to +0.015). Prompt craft is not a substitute for supplying the actual base rate as evidence and recalibrating after. **[index]**
5. **Anchoring on supplied numbers** (§2.5, Schoenegger Study 2): any market price, prior forecast, or analyst number placed in the evidence will pull the judge toward it. For clean engine comparisons, elicit blind; add anchors only as a deliberate, separately scored variant.
6. **Prompt / format sensitivity:** Kadavath (calibration is format-dependent), Tian (elicitation method changes ECE materially), Prophet Arena (prompt *variations* changed Brier by <0.01 for frontier reasoning models — reassuring for minor rewording, but question *semantics* changes remain calibration events). Freeze wording (§5).
7. **Leakage / contamination:** forecasting results inflate when questions or resolutions sit inside training data or retrieval is not time-boxed (Halawi restricted test questions to post-cutoff; a secondary synthesis cites a claim that 71% of date-filtered search queries may return post-cutoff pages **[thin]**). For nightly chart studies the analogue is look-ahead in the evidence pack itself: every datum in `input` must be timestamped ≤ the forecast timestamp, and that rule belongs in deterministic code, not in instructions to the model.
8. **Confidence–action disconnect:** models can state appropriate uncertainty and still not act on it under cost pressure (RiskEval-style findings **[index, thin]**). Decisions' design actually helps here — *your* code, not the model, applies thresholds and costs. Keep it that way.

#### 2.7 Statistical power — the ledger's binding constraint

Detecting a realistic **0.01–0.03 Brier edge requires hundreds to low-thousands of resolved questions per category** (practitioner synthesis of the forecasting literature **[index]**). Arithmetic for this operation: 100 stocks × ~250 nights = 25,000 resolutions/year *per question* if a question is asked nightly per stock — ample power per question family within weeks — but only ~250 resolutions/year for any *market-regime-conditional* slice (e.g. "on high-volatility days"), and far fewer for rare-event predicates. Design families so the slices you intend to act on reach n ≥ ~300 resolved before you fit weights, transforms, or thresholds to them; below that, pool, shrink, or wait.

---

### 3. The bitter lesson applied to prediction

#### 3.1 Sutton's argument, precisely

Rich Sutton, "The Bitter Lesson" (13 Mar 2019, incompleteideas.net): *"The biggest lesson that can be read from 70 years of AI research is that general methods that leverage computation are ultimately the most effective, and by a large margin."* The mechanism is the generalisation of Moore's law — computation per unit cost keeps falling, so methods that scale with compute eventually swamp methods that encode human knowledge, which help in the short term, then plateau and even inhibit progress by complicating the system. The two methods that scale arbitrarily are **search** and **learning**. His cases:

- **Chess:** hand-crafted grandmaster heuristics/opening knowledge → massive deep search (Deep Blue beat Kasparov, 1997).
- **Go:** human shape/intuition knowledge → search + self-play learning (AlphaGo beat Lee Sedol 4–1, 2016, beating other programs 99.8% of games; AlphaGo Zero then removed human game data entirely — tabula-rasa self-play surpassed the human-trained system).
- **Speech recognition:** hand-built phonetic/rule knowledge → statistical learning, then deep learning.
- **Computer vision:** hand-crafted features → learned representations.

#### 3.2 Where prediction has already obeyed the lesson — weather

Weather forecasting is the cleanest large-scale forecasting (not game) validation:

- **GraphCast (Science 2023):** a learned model trained on reanalysis data beat ECMWF's deterministic HRES on **>90% of 1,380 verification targets**, producing a 10-day global forecast in **under a minute** on one machine, with tropical-cyclone track improvements up to ~20%.
- **GenCast (Nature 2024):** the probabilistic successor beat ECMWF's ensemble (ENS) on **97.2% of 1,320 targets**, including extremes.
- **ECMWF AIFS** became operational in Feb 2025 — the first AI system in operational service at a major centre — with reported gains up to 20% on some measures at ~1,000× less energy per forecast.

**Boundary conditions visible even here:** GraphCast/GenCast are trained on ERA5 *reanalysis*, which is itself produced by physics-based assimilation; every major centre now runs AI and physics models **side-by-side and blends them**; and learned models still occasionally miss extreme, out-of-distribution events the physics models were built to handle. The lesson won on the *solver*, not by abolishing domain structure — the structure moved upstream into the data-generating process. **[index]**

#### 3.3 Counterarguments and boundary conditions

1. **Sutton against LLMs (2025).** In his widely reported Dwarkesh Patel interview (Sep 2025), Sutton called LLMs a "dead end": they learn from human-curated text to predict *what a person would say*, not *what will happen*; they have no goals, do not learn from the consequences of actions, and do not update from surprise at the world. Whether or not one accepts the conclusion, the implication for this study is sharp and unavoidable: **a frozen LLM judge is, by Sutton's own taxonomy, a human-knowledge method** — a compressed imitation of human judgment — not a search/learning method. It inherits the bitter lesson's prediction about such methods (short-term usefulness, plateau) *unless* the surrounding system supplies the learning loop: resolved outcomes → measured error → recalibration, reweighting, question retirement. That loop is the operation's ledger. The API provides the judge; only the operation can provide the lesson.
2. **Sample efficiency (Chollet 2019, "On the Measure of Intelligence").** Intelligence as *skill-acquisition efficiency* — skill gained per unit of priors + experience. ARC-style tasks are designed so humans generalise from 3–5 examples; brute scale "buys skill" on known tasks without demonstrating acquisition of *new* skill. Where data is scarce and non-repeatable (a specific regime, a specific corporate event), human structure and priors still win because there is nothing to scale over.
3. **Smoothness / structure dependence (working-paper synthesis [thin]):** in "nonsmooth" domains the scaling curve flattens early, and the right inductive biases, representations, and search strategies become prerequisites rather than luxuries — "the lesson is not equally bitter for all domains."
4. **Diminishing returns to brute scale:** mid-2020s commentary noted under the bitter-lesson literature argues architectural/memory efficiency increasingly dominates raw brute force as thermodynamic costs bind **[index, thin]**.
5. **The AlphaZero template's hidden prerequisites:** closed rules, a cheap perfect simulator, unlimited self-play, and instant verifiable outcomes. Financial markets offer *none* of these cleanly: no simulator (backtests are the contested artefact, §3.4), feedback is delayed and noisy, the "opponent" adapts, and the act of trading moves the environment. Monte Carlo / self-play logic transfers to *portfolio and execution simulation* far more safely than to *directional prediction*.

#### 3.4 Finance's specific refutation risk: non-stationarity + multiple testing

This is where naive bitter-lesson reasoning ("enumerate every pattern, let compute sort it out") has a documented body count.

**Non-stationarity and signal economics (López de Prado, *Advances in Financial Machine Learning*, 2018, and practitioner syntheses [index]):**

- Relationships shift across regimes; a model trained through 2019 deployed into March 2020 faced a conditional distribution it had never seen.
- Public-information signals are arbitraged away; residual daily-return predictability is tiny (R² ~0.01–0.02 at best in syntheses).
- Effective sample size is small: ~20 years of daily data contains perhaps 4–5 independent business cycles.
- Standard k-fold cross-validation leaks in financial time series; **purged + embargoed CV** is the minimum standard.
- Alpha decays *because* it is exploited — the environment is adversarial in a way Go and weather are not.

**Multiple testing / data snooping — the core literature:**

| Source | Finding | Operational rule |
|---|---|---|
| Harvey, Liu & Zhu, Rev. Financial Studies 2016 | **316 factors** had been published by 2012; most are likely false discoveries given the volume of testing (published + unpublished) | A new factor needs **t ≥ 3.0**, not 2.0; a Bonferroni calculation for ~300 tests at 5% gives ≈ **3.78** |
| Harvey & Liu 2015 (haircut Sharpe) | Backtested Sharpe ratios must be haircut for the number of trials; a ~50% haircut is a common rule-of-thumb magnitude, growing with trials | Never quote a mined strategy's raw Sharpe |
| Bailey & López de Prado 2014 (Deflated Sharpe Ratio, DSR) | Probability the true Sharpe > 0 after adjusting for **number of trials, sample length, skewness, kurtosis**; conventional significance requires **DSR > 0.95** | Report DSR alongside every backtest that was *selected* from a search |
| Bailey, Borwein, López de Prado & Zhu 2014 ("Pseudo-Mathematics and Financial Charlatanism") | Selection over many worthless strategies guarantees an impressive-looking winner; one synthesis: the best of 100 worthless strategies is expected to post an annualised Sharpe of ~**1.26** | A Sharpe without a trial count is an unnormalised statistic |
| White 2000 (Reality Check); Sullivan, Timmermann & White, J. Finance 1999 | Expanded Brock et al.'s 26 technical rules to a universe of **7,846 rules** on ~100 years of DJIA and bootstrap-tested the *best* rule against snooping bias; in-sample winners in 1897–1986 did not persist in the 1987–96 out-of-sample period in follow-up readings | Test the *maximum over the universe you actually searched*, not the winning rule in isolation |
| Hsu et al. re-examination with White's Reality Check | Universe expanded to **39,832 rules/strategies**: significant profitable rules found for NASDAQ Composite and Russell 2000, **not** for DJIA or S&P 500 | Even Reality-Check survival is index- and period-specific, not a licence |

**Large-scale automated mining — both sides, with numbers:**

- *The scale success template:* WorldQuant-style factor mining explicitly frames the business as mining "hundreds of thousands, millions and even billions" of formulaic alphas and combining individually weak alphas into a composite "mega-alpha"; Renaissance-style statistical arbitrage is described in secondary compilations as being right only ~50.75% of the time but across 150k–300k executions/day **[index, illustrative, not audited]**. The common structure: enormous numbers of *small, diversified, cheap-to-trade* bets, fast feedback, ruthless cost control, and combination rather than selection of a single winner.
- *The scale failure template:* a documented genetic-algorithm rule-mining run (200 generations over indicator/threshold/logic genes, fitness = in-sample Sharpe) produced **best in-sample Sharpe 4.1 → out-of-sample Sharpe −0.3**, and was killed by its own authors as "industrial-scale data snooping: searching millions of rule combinations guarantees a spectacular in-sample winner that is pure overfit." **[index, single case]**
- *Synthesis for Decisions-based chart studies:* asking 400 questions × 100 stocks × 250 nights = **10,000,000 predicate-resolutions per year**. That is a *forecasting* asset (power, §2.7) and simultaneously a *mining* liability: any pattern "discovered" by searching that ledger (e.g. "predicate X on sector Y on Tuesdays…") is a selection over a huge implicit trial count and must clear the same bars as factor mining — pre-registered families, holdout by *time*, DSR/Reality-Check-style adjustment, and a trial-count log. **The ledger must record how many hypotheses were tried, not just which ones worked — including by the AI analysts and by any automated question-bank generator.**

#### 3.5 What "bitter lesson" design actually looks like for this operation

1. Prefer **learned / enumerated breadth with mechanical scoring** over hand-tuned chart heuristics *for hypothesis generation* — Decisions question banks are cheap enumeration.
2. Spend the saved human effort on the **validation stack** (the part that does not scale itself): locked time-based holdouts, purged CV, DSR, climatology baselines, trial counting.
3. Keep **human structure where samples are thin**: question *design* (observable criteria, resolution definitions), regime taxonomy, cost models, and kill decisions.
4. Expect **plateau and decay**: schedule re-validation; a pattern engine is a wasting asset, not a discovery carved in stone.

---

### 4. Precedents for typed-probability judgment systems at scale

#### 4.1 Prediction markets and forecasting platforms — calibration at ~1M scale

**Dickerson et al., PNAS 2026 (doi:10.1073/pnas.2615627123) [index]:** **1,014,122 resolved contracts/questions**, Oct 2015 – Nov 2025, across **Polymarket, Kalshi, Manifold, and Metaculus** (real-money, virtual-currency, and reputation incentives), 12 domains, horizons from hours to years.

- **Aggregate calibration held:** events assigned probability p% occurred approximately p% of the time, across platforms and many domains.
- **Fine-grained analyses found systematic over- or under-estimation in several highly consequential areas** (Tel Aviv University summary highlights overestimation for conflict/geopolitics).
- Calibration was already strong early (evident after ~25% of a forecast's life); accuracy gains toward resolution came mainly from *resolution* (informativeness), not from becoming better calibrated.
- Authors' framing: large-scale aggregation contains meaningful information about uncertainty — and says **nothing about the reliability of any individual forecast**. Exactly the right mental model for a single Decisions call.

**PredScope 2026 [index, thin — non-peer-reviewed, author-acknowledged selection bias toward high-volume politics/economics markets]:** 542 resolved markets (Polymarket 298, Kalshi 156, Metaculus 88), Jan 2025 – Mar 2026: average calibration error **3.2 pp** overall, **1.8 pp** for $1M+-volume markets; volume-weighted median Brier **0.17**; best subcategory Kalshi Fed-rate markets: Brier **0.09**, calibration error 1.1 pp. On its election/economics subsets, markets scored Brier 0.14/0.11 vs Metaculus-top-2% superforecasters 0.13/0.14 — i.e. markets and elite humans are in the same band, trading the lead by domain.

**Horizon effect (Le preprint, via practitioner synthesis [index, thin]):** across 292M trades / 327k Kalshi + Polymarket contracts, mean calibration slope rises from **0.99 within 1 hour of resolution to 1.32 beyond one month** — prices are compressed toward 50% far from resolution (a 70¢ contract a month out corresponded to ~75% true probability; in politics, a 70¢ contract a week out to ~83%). **brier.fyi [index]** illustrates why timing definitions make cross-source Brier comparisons treacherous: it reports Brier **0.09 one month before close (n = 84,357)** and a **median midpoint Brier of 0.0256 (n = 671,732)** — different snapshots of the same markets, wildly different numbers. *Ledger rule: every Brier in your system must carry its forecast timestamp relative to resolution, or it is meaningless.*

**Kalshi / Metaculus as design precedents (not just benchmarks):** both work because questions are *binary or finite-choice, with explicit resolution criteria, a definite resolution source, and a definite close time*. That is the template for ledger-grade Decisions questions: "Will X close above Y on date Z per [named source]?" is resolvable; "Is this chart bullish?" is not — it is a *judgment* question, useful as an engine input, inadmissible as a forecast until it is tied to a resolvable outcome predicate. Keep those two question classes in separate ledger tables with separate scoring.

#### 4.2 Superforecasting — what the winning human system actually consisted of

- **Good Judgment Project (GJP), IARPA ACE tournament 2011–2015:** Tetlock & Mellers' team recruited ~5,000 volunteers (figures of 2,800–5,000 appear across sources depending on cohort definition), scored every forecast with Brier, and won so decisively that IARPA dropped the other four teams after year two. Contemporary reporting: GJP's best forecasters beat intelligence-community analysts *with classified access* by ~25–30% **[index — range varies by source]**.
- The measured ingredients (Mellers et al. 2014/2015): (1) brief probability **training**; (2) **teaming**; (3) **tracking** forecasters and weighting by past accuracy; (4) **aggregation with extremizing** (§2.5). No ingredient was "find smarter people and leave them alone."
- Background warning (Tetlock, *Expert Political Judgment*, 2005): 284 experts, 20,000+ forecasts since 1984 — the average expert barely beat chance. Unaided expert judgment is the *control group*, not the gold standard. This applies verbatim to unaided AI-analyst judgment, and to vendor demo judgments.
- **Superforecasting protocol as question-bank hygiene:** start from the outside view / base rate; decompose the question (Fermi-ize); update in small steps; put a fine-grained number on it; post-mortem every resolution. Each step maps to a pipeline feature in §5.

#### 4.3 LLM forecasting benchmarks — the parity debate, with both sides

**ForecastBench (Forecasting Research Institute; Karger, Tetlock et al., ICLR 2025, arXiv:2409.19839) [index]:** dynamic, contamination-free by construction (questions about future events from markets, platforms, and datasets; ~1,000 questions per round in later descriptions; LLMs compared with superforecasters and the public).

| Reading | Superforecasters | Public | Best LLM / AI system | Notes |
|---|---|---|---|---|
| Original study (Jul 2024 questions) | **0.093** | 0.107 | **0.111** (best of 17 LLMs) | AI trailed even the public |
| Feb 2025 update (difficulty-adjusted) | **0.081** | — | **0.101** (GPT-4.5) | Naive always-50% = 0.25; linear trend projected parity late 2026, 95% CI Dec 2025 – Jan 2028 |
| May 2026 leaderboard (Brier Index = (1−√Brier)×100) | Index **70.2** (≈ Brier 0.089) | — | DeepMind "green tree" Index **67.9** (≈ 0.103) | AI *leads on dataset questions*, *trails on market questions*; superforecasters still #1 overall **[index]** |
| Jul 2026 FRI announcement | — | — | Several systems (led by Cassi AI; incl. xAI, DeepMind) "statistically indistinguishable" from superforecaster level | **[contradicted — see below]** |
| Bridgewater AIA Labs, Nov 2025 (arXiv:2511.07678) | 0.0740 on market subset (one secondary reading) | — | **0.108** overall ForecastBench, difference vs superforecasters n.s. (p = 0.15); market subset **0.0753** | Single-lab agentic system: news search + supervisor reconciling forecasts + statistical (Platt) calibration. Without search, the same lineage scored **0.361 — worse than random** on its live benchmark per secondary synthesis |

**Why the July 2026 parity claim is contested [contradicted]:** Good Judgment Inc. notes the human comparator is a *frozen* baseline — a single July 2024 elicitation from superforecasters working mostly *alone*, without the teaming, discussion, and continuous updating that constitute most of the GJP edge (§4.2). Beating a frozen solo snapshot is not beating the superforecasting *system*. FRI itself stressed the benchmark is not saturated and announced a fresh superforecaster round. Treat "AI has matched superforecasters" as **unresolved**, and the May 2026 gap (~0.014 Brier on the index conversion) as the last uncontested reading.

**The beyond-Brier critique (Vaticinus 2026 preprint [index, thin — single preprint, human comparison rests on one released round]):** across **25 ForecastBench rounds (2024–2026), 370,972 resolved market forecasts, 342 model configurations**, the bias-corrected *incremental* information frontier LLMs add **beyond a liquid market price** is ~**0.001 nats**, with a non-positive trend across two years of scaling — while human superforecasters on the one released human round added ~**0.09 nats** (~75×, single-round caveat). Ranking by raw Brier on market questions largely crowns "the model that copied the price best." *Trading translation: matching the market's Brier is not an edge. An engine earns capital only on information beyond what's already in price — test Decisions predicates for incremental value over (a) climatology, (b) the stock's own recent returns / market state, and (c) your existing engines, in that order.*

**Prophet Arena (arXiv:2510.17638) [index]:** live benchmark, ~20 new Kalshi events/day, **1,367 resolved events / 72,136 markets**, scoring Brier, ECE, *and* simulated market return against market prices.

- GPT-5 [reasoning]: Brier **0.184**, ECE **0.042**, average return **0.943** — *better than the market baseline on all three* (0.187 / 0.069 / 0.899) — **and still below break-even (return < 1)**. Top-model ECE ≤0.05 vs 0.05–0.20 for weaker models: calibration separates models more than Brier does (top band only 0.17–0.24).
- LLMs are systematically **conservative vs the market at the extremes** of the probability spectrum.
- Robustness: Brier varied **<0.01** across concise/verbose/rewritten prompts; **self-consistency aggregation generally made accuracy worse** — a direct warning against "ask the same question five times and average" as a Decisions pipeline pattern for a single model.
- Markets beat LLMs close to resolution (they incorporate breaking news in minutes); LLMs are most competitive at longer horizons. Nightly (not intraday) cadence plays to the LLM side of that split.

**Metaculus AI Benchmark / FutureEval [index]:** quarterly Pro-vs-bot tournaments on shared, forward-looking questions (binary, numeric, multiple-choice). Synthesis of 11 Metaculus analyses (Oct 2024 – May 2026): **Pros beat bots in every tournament**, by head-to-head peer-score margins of **11.3 points (Q3 2024, p = 0.036), 17.7 (Q1 2025, p = 0.001), and 20.03 (p = 0.00001)**; as of May 2026 Pros still lead the ongoing FutureEval leaderboard over individual bots. What winning bots do: **86% of Fall 2025 winners ensemble/aggregate** multiple forecasts; scaffolded bots beat their own non-scaffolded baselines by 5–11 peer-score points/question; **Platt (logistic) recalibration improved bot Brier by 0.016 on binary and 0.005 on multiple-choice questions (p < 0.001)**; Phan et al. improved 0.0999 → 0.0934 with Platt scaling. Metaculus's own extrapolation for single-prompt bots vs Pros put parity around Jun 2027 **[index]**.

#### 4.4 A finance-domain precedent: fine-tuned LLM forecasting of merger outcomes

"Global Merger-Arbitrage Forecasting with Language Models" (2026 proceedings paper **[index]**): a *fine-tuned, domain-specific* LLM forecasting system on a held-out set of **404 large deals across 42 countries**, with strict temporal integrity:

- Class-balanced Brier **0.151** — **24% below** Platt-scaled market-implied probabilities (**0.199**), **19% below** XGBoost (**0.186**), and **25–42% below** frontier LLMs given identical context (**0.201–0.259**).
- Fine-tuning drove most of the gain; calibration error fell **0.089 → 0.039** with fine-tuning.
- The fine-tuned system's correlation with market-implied probabilities was only **0.36** (vs XGBoost 0.75) — its value was *independent* information, echoing the Vaticinus criterion (§4.3).

Lessons: (1) on a specialised, high-stakes financial task, *domain adaptation + structured deal features* beat general frontier models decisively — the opposite ordering from generic benchmarks; (2) a general judge like Luna should be expected to start at the "frontier models given identical context" end of that range (0.20+ Brier territory on hard financial binaries) until the operation's own recalibration/ensembling closes the gap; (3) low correlation with existing signals is a feature to *measure and prize*, not a defect.

#### 4.5 Commercial and open-source typed-judge systems

| System | Shape | Price / latency | Calibration position |
|---|---|---|---|
| **OpenAI Decisions** (this study) | Predicate / choice / score over shared evidence, images + JSON | $0.10/1M input, output free; "about 10× faster than Responses" **[vendor claim]** | **No calibration claim, no published accuracy** (§1.8) |
| **TypeSafe Jev** ("System One", launched 15 Sep 2026; $40M seed, DCVC-led, per secondary coverage) | Noul (≈predicate) / choice (≤255) / score (2–10) over a `state`; text-only at launch, no prose output | **$0.042/1M input**, output free; **70–500 ms** vendor-reported | Explicit claim: trained with **RLCD** for calibrated decisions; integrator docs define `confidence` as distribution *concentration*, not correctness probability. One workflow evaluation cited **67.8% label agreement** at $0.0004/case, 0.4 s **[index, thin]**. Caveats published by its own ecosystem: valid schema can still contain the wrong answer; does not treat state as hostile by default (prompt-injection can move answers) |
| **LLM-as-judge generally** (Zheng et al. 2023, MT-Bench) | A strong judge agreed with human preferences **>80%** of the time — about human–human agreement — *on general chat*, not on any specialised domain | Model-dependent | Agreement ≠ calibration; domain transfer is the open question (§5.4 biases) |
| **Forecasting-as-a-service** (e.g. FutureSearch, per 2026 pricing survey **[index, thin]**) | LLM research agents producing calibrated probability forecasts with reasoning | Deep-research agents ~1–11¢/operation; forecasters ~20–90¢ per researcher-row | Vendor-reported; audit with the same ledger discipline as any third-party claim (§5.6) |

**Precedent verdict:** typed-probability judging is now a *category* with at least two venture-scale entrants and one big-lab entrant within six weeks of each other (Sep–Oct 2026). Nobody in the category — including the one that claims calibration training — has published a large, independent, outcome-scored evaluation of calibration on financial or chart evidence. The operation's ledger would, if run properly, be among the first such evaluations anywhere. That is both the opportunity and the reason to distrust every demo.

---

### 5. Practical engineering patterns for batch judgment pipelines

#### 5.1 Structuring the question bank over shared evidence

Patterns that follow directly from the API contract (§1) and the forecasting science (§2):

1. **One request per evidence set; independent questions only.** Dependent questions ("if damaged, which repair class?") go in a second request conditioned on the first answer. Never simulate sequencing inside one batch.
2. **Three ledger classes, kept separate:**
   - *Resolvable forecast predicates* — tied to a named outcome, source, and date (Kalshi-style, §4.1). These earn Brier scores.
   - *Judgment predicates / choices / scores about present evidence* ("pattern X is present", "dominant regime is Y", graded rubric scores of an analyst's thesis). These earn *agreement/reliability* scores against human or deterministic ground truth where available, and earn forecast value only via a downstream resolvable predicate.
   - *Audit questions* — the same bank pointed at third-party tools' outputs (§5.6).
3. **Freeze the bank.** Question `name`, `instructions`, choice values/descriptions, and level labels/descriptions are *part of the instrument*. Any edit = a new question version = a new ledger series. AICassindra's GA practitioner guide is explicit: changing wording changes what the probability means and invalidates fitted thresholds. **[index]**
4. **Observable criteria, one concern per question, distinct adjacent levels, always a fallback.** Directly from the guide (§1.3). For scores: define levels so a human grader could sort examples into them; if humans can't, the model can't.
5. **Balance the bank against acquiescence bias:** include negatively-worded counterparts for a sample of predicates (§2.6.3) and track the YES-rate per question against its resolved base rate as a standing diagnostic.
6. **Correlated-error warning:** answers to many questions over the *same* evidence are **not independent** — misleading evidence (a mis-scaled chart, a stale datum) makes them wrong together. Agreement across 50 questions on one stock is one observation about that stock's evidence, not 50 confirmations. Ledger statistics must cluster by evidence set (stock-night), not treat question-resolutions as fully independent.
7. **Don't round scores.** A `score` is a weighted mean of indices; the actionable quantity is usually a *tail probability* from the returned distribution. Practitioner example: level probabilities 0.1/0.3/0.5/0.1 give score 1.6, but P(top-two levels) = 0.6 is what should meet a threshold. Store the **full probability vector** for every choice/score answer; the scalar is a display convenience. Two distributions [0,1,0] and [0.5,0,0.5] both score 1.0 and mean opposite things.
8. **Refusals are data.** Route refusals to review, count them per question, never coerce them to 0 / "no" / the fallback choice. A rising refusal rate is a drift signal (§5.4).

#### 5.2 Caching strategy

- **What caches:** only the shared `input` prefix (≥1,024 tokens, byte-identical), via the implicit breakpoint at the end of `input`, or explicit breakpoints (≤4/request) with `prompt_cache_key` partitioning. Questions are never part of the reusable prefix.
- **Design consequence for the nightly run:** first-pass coverage of 100 *different* stocks gets **no** cross-stock cache benefit (evidence differs). Caching pays in exactly three places: (a) **re-interrogation** — asking a second/third question bank over the same stock evidence within the TTL (design banks in waves around this: core bank, then follow-up banks for flagged stocks); (b) **shared static prefixes** — a market-regime document / methodology preamble placed *first and identically* in every request, with stock-specific evidence after the breakpoint, *if* the breakpoint placement lets the static part be the cached prefix (verify with `cached_tokens` in usage — do not assume); (c) **re-runs after failure** within the window.
- **TTL reality:** budget on **30 minutes** (§1.4, trap 4). That window suits wave-based nightly processing (all waves for a stock within ~30 min), not "cache tonight, re-use tomorrow."
- **Verify, don't assume:** log `cached_tokens` and `cache_write_tokens` per request; alert if the cached share collapses (a changed timestamp/header early in the prefix is the classic silent cache-killer — keep volatile metadata *out* of the prefix).
- **Cost governance:** a cache write is 1.25× an uncached pass; a workload that writes prefixes it never re-reads pays a 25% premium for nothing. Cache-hit rate belongs on the same dashboard as Brier.

#### 5.3 Threshold selection from labelled examples

The guide's rule — labelled examples + FP/FN costs — operationalised (worked practitioner example: AICassindra, 26 Oct 2026, **synthetic** 200-case companion example, no provider call — use the *method*, not the numbers, as evidence **[thin by construction]**):

1. **Two bands beat one cut.** Replace a single 0.5 threshold with deny ≤ low, act ≥ high, human/secondary review between. In the synthetic example (costs: wrong approve 40, wrong deny 25, review 3; model deliberately overconfident — top reliability bin averaged 0.962 predicted vs 0.894 actual): a 0.5 cut cost **1,125**; the fitted band (≤0.10 / ≥0.90, reviewing 54 of 200) cost **412**.
2. **Fit on one sample, judge on another.** A band fitted on the first 100 cases (which, correctly, refused all auto-approval) still cost **244 on the held-out 100 vs 720** for the 0.5 cut. Small labelled sets should produce *conservative* bands — that is the method working, not failing.
3. **Per-question thresholds, per-question reliability tables.** A threshold is a property of (question version × model × evidence mix). Global thresholds across a 400-question bank are meaningless.
4. **Gate choices on probability, not on the label.** A choice returned with top-option probability 0.71 goes to review even though "the model chose X." The returned label is the argmax, not a commitment.
5. **Refit triggers:** model change (including silent ones, §5.5), question edit, evidence-mix change, or a reliability-bin breach on resolved outcomes. Calendar-based refits alone will miss all four.
6. **Minimum data:** do not fit a band on fewer than ~100 labelled examples per question, and do not trust its tails until several hundred resolutions accumulate (§2.7). Until then, the band is review-everything with ranking — which is still valuable.

**Recalibration layer (separate from thresholds):** fit Platt (logistic) or single-parameter shrinkage/extremizing transforms *per question family* on resolved ledger outcomes only, with the transform fitted on a strictly earlier window than it is applied to. Evidence for the size of the prize: Platt improved Metaculus bots by **0.016 Brier** (binary, p < 0.001); shrinkage recovered **0.0223 Brier** across all 15 frontier-model entries in Whelan's study; Platt is the final stage of the AIA system that reached superforecaster-adjacent performance. Keep raw and recalibrated series in the ledger forever — the gap between them *is* your calibration diagnostic.

#### 5.4 Drift monitoring of the judge

Treat the judge as a measurement instrument (the LLM-judge handbook literature converges on this framing **[index]**):

- **Canary / anchor set:** a fixed set of ~**200 labelled items** spanning every question family, re-judged on a schedule (weekly is the handbook norm). A shift of **>2 points** on the canary with no input change = judge drift until proven otherwise. The canary must include chart images, not only text, if the production bank is image-based.
- **Five drift types, five different responses** (handbook taxonomy): *input-distribution* drift (your stocks/regimes changed — reweight reporting, maybe nothing else); *judge* drift (vendor changed the model — re-validate, recalibrate); *evaluation-standard / criteria* drift (your rubric evolved — version it, break the trend line honestly); *annotator* drift (your human labellers moved — retrain/recalibrate them); *concept* drift (the evidence→outcome relationship itself changed — the finance default, §3.4 — retire or refit the question).
- **Leading vs lagging vs anchored signals:** input-mix statistics move first (leading); fresh human-audit accuracy moves last (lagging); the canary is the anchored signal that separates "the world changed" from "the instrument changed." Run all three.
- **Standing human audit:** ~**100 judged items/month** re-graded by humans as ground truth, owned by whoever owns the ledger — not by whoever's engine is being graded.
- **Judge calibration gate before trust:** 200–300 human-labelled items per criterion; report judge–human Cohen's κ; automate only criteria where judge–human agreement ≥ human–human agreement.

**Bias controls specific to this operation's weekly analyst grading:**

| Bias | Evidence | Control |
|---|---|---|
| Position bias | Pairwise verdicts flip when order is swapped (Wang et al. 2023) | Grade each analyst's work in **both orders**; count a win only if it survives the swap, or score predicates/scores (not pairwise) wherever possible — a structural advantage of Decisions over chat judging |
| Verbosity bias | Longer answers win regardless of quality (AlpacaEval 2.0 added length control, Dubois et al. 2024) | Length-blind rubric questions; include an explicit "unsupported length / padding" score question; check score-vs-length correlation monthly |
| Self-preference | Judges favour outputs from their own model family (Zheng et al. 2023) | **Blind analyst identity** in the evidence (strip names/model tells); where feasible cross-check a sample with a different-family judge (e.g. Jev or a Responses/Chat judge) and report inter-judge disagreement |
| Judge drift | §5.5 | Canary + provenance + never mixing judge versions in one trend line |

#### 5.5 Model version pinning — the Decisions-specific risk

- **The risk is documented, not hypothetical:** Chen, Zaharia & Zou (2023, arXiv:2307.09009; Harvard Data Science Review 2024) ran identical tasks against GPT-4's March and June 2023 snapshots: prime/composite accuracy fell **84% → 51%** on the revised balanced test (the original 97.6% → 2.4% headline was a primes-only artefact, flagged by Narayanan & Kapoor — cite the revised numbers), and directly-executable code fell 52% → 10%, largely a markdown-wrapping *formatting* change (70% after stripping). The durable lesson is not "models get worse"; it is that **behaviour behind a stable name changes enough in three months to break pipelines and invalidate thresholds**, sometimes via formatting rather than capability.
- **Decisions aggravates this:** the endpoint accepts exactly one model identifier, `gpt-6-luna`, and **no dated snapshot identifier for Decisions was found in the guide, the create-decision reference, or the model page as read on 2026-11-10 [could not verify — §"Could not verify"]**. If OpenAI updates Luna behind the alias, a Decisions user may have *no pin to set*. Additional corroborating oddity: several reviewers note the gpt-6-luna model page's endpoint table did not list `/v1/decisions` at all in October — the guide and changelog are the only authoritative Decisions sources, so monitor those pages, not just the model page.
- **Mitigations available without a pin:** (1) record the response's echoed `model` field, request timestamp, and full usage object on *every* verdict — if the echo ever changes, your ledger can split cleanly at the break; (2) weekly canary (§5.4) sized to detect a ≥2-point shift; (3) treat any detected shift as a **judge migration**: dual-run is impossible against a retired alias, so instead re-score the entire calibration/canary baseline with the new judge, refit thresholds and recalibration, and **start a new trend line — never splice pre- and post-change scores into one series**; (4) keep a fallback judge integration (Responses with Structured Outputs, or Jev) warm enough that a silent Decisions change does not halt the nightly run; (5) watch the OpenAI changelog feed as an operational dependency, with an owner.

#### 5.6 Audit trails for probabilistic decisions — and auditing third parties

**Per-verdict provenance record (minimum):** evidence hash + evidence timestamp(s); question bank version + per-question instructions hash; model identifier *as sent and as echoed*; `prompt_cache_key` if used; full answer (including the complete probability vector and any refusal); usage object (input / cached / cache-write tokens); threshold-band version and recalibration-transform version applied; downstream action taken; resolution source, resolution timestamp, and outcome when known; Brier / log score once resolved. Cache verdicts keyed on (evidence hash, rubric/bank version, model) so a re-run returns stored verdicts instead of paying for — and possibly *changing* — fresh judgments (the build-cache pattern from the judge-handbook literature). Deterministic gates (price limits, timestamp checks, corporate-action flags) should decide everything they can *before* the model is consulted: those cases are free, reproducible, and never flip between runs.

**Auditing third-party trading-tool claims with the same apparatus** — demand, for any vendor claim:

1. Raw, timestamped forecasts (probabilities, not win/loss narratives) made *before* resolution, with the resolution source named in advance.
2. n resolved, by question family and period — plus the **trial count**: how many other questions/strategies were run and not shown (§3.4).
3. Brier **and** log score, **and** the Murphy decomposition, **and** BSS against *climatology computed on the same question set* — a Brier quoted without its climatology is unauditable, since 0.17 is excellent on one question mix and worse-than-baseline on another (§4.1).
4. The forecast timestamp relative to resolution for every score (§4.1, brier.fyi lesson).
5. Incremental value over price/existing signals (§4.3, Vaticinus criterion), net of costs — Prophet Arena's sub-break-even winner (return 0.943 despite beating the market's Brier) is the standing rebuttal to "accurate, therefore profitable."

A vendor who cannot produce (1)–(3) has not made a forecast claim; they have made a marketing claim. Decisions makes producing (1) trivially cheap for *your own* operation — hold yourselves to the standard you apply to vendors.

#### 5.7 Financial-workflow specifics

- **Timestamp discipline in code:** every evidence item carries an as-of time; a deterministic pre-filter rejects anything after the forecast timestamp. Do not delegate look-ahead prevention to instructions.
- **Resolution definitions in the bank itself:** each forecast predicate names its outcome source (e.g. official close), timezone, corporate-action adjustment, and tie/edge rules — written before the first run, changed only by version bump.
- **Trial-count accounting:** log every question asked, including exploratory and retired ones, with ask-counts. The ledger's *denominator* is a first-class table (§3.4).
- **Regime slicing with power discipline:** pre-register the regime taxonomy; do not fit per-regime transforms until the slice clears the n-threshold in §2.7; pool upward otherwise.
- **Purged validation for any fitted component:** thresholds, Platt maps, ensemble weights, and extremizing factors are all *fitted parameters* — fit them on earlier time, evaluate on later time, with an embargo at least as long as the forecast horizon.
- **Cost model in the loop:** thresholds derive from FP/FN/review costs (§5.3); for trading-adjacent actions the "review" band maps to "no position / existing engines decide," and the cost of a wrong auto-act must include spread, slippage, and the Prophet Arena lesson that even a market-beating Brier can lose money.

---

## Could not verify

1. **No definition or formula for the Decisions `confidence` field** in the official guide or create-decision reference as read on 2026-11-10. Any statement about what OpenAI's confidence *means* (concentration vs correctness) is inference from competitor docs, flagged [thin] where used.
2. **No dated model snapshot / pinning mechanism for Decisions** was found. It is possible one exists in account-level settings or newer docs; the mitigation stack in §5.5 assumes it does not.
3. **The 128-images-per-request limit** rests on secondary/gateway summaries; the guide states that question images share "the request's image limits" without giving the number in the text read.
4. **Rate-limit numbers** (Build/Launch/Grow RPM/TPM) come from secondary summaries of OpenAI's rate-limits guide (index only), checked by their authors 7–17 Oct 2026. Confirm on the organisation's own Limits page before relying on them.
5. **12-hour cache TTL for Decisions:** pricing summaries list a 12-hour write rate, but the API reference says 30m is currently the only supported `ttl` value. Unresolved contradiction in OpenAI's own materials as captured.
6. **No independent latency or accuracy measurement of the Decisions endpoint** exists in the reviewed material — every latency figure is vendor/customer launch material, and no third party had published an outcome-scored calibration study of Decisions probabilities. All §2 calibration numbers are from other elicitation methods/models.
7. **Several 2026 forecasting results are single-source or contested** and are flagged inline: July 2026 ForecastBench parity (contradicted), Vaticinus beyond-Brier preprint (single human round), Le horizon-effect preprint (via synthesis), PredScope market study (non-peer-reviewed, selection-biased), Whelan benchmark (non-peer-reviewed), AICassindra threshold example (synthetic, by design).
8. **GJP headcount and "beat classified analysts by X%"** vary across sources (2,800–5,000 forecasters; 25–30%); the qualitative result (won the tournament; aggregation ingredients measured) is consistent everywhere.
9. The mission premise described Decisions as returning "*a calibrated probability*" for predicates. **The sources do not support "calibrated" for this API** — see §1.8. The rest of the premise (endpoint, model, question types, 400-question cap, ~10× speed claim, $0.10/1M input, free output, caching on the shared-evidence prefix) is confirmed by the official guide.

---

## Sources

All URLs copied verbatim from search results / pages read on 2026-11-10. [verified live] = opened and read in the research browser; others are [index].

**Decisions API — primary**
- Decisions guide, OpenAI — https://developers.openai.com/api/docs/guides/decisions [verified live]
- Create a decision, OpenAI API Reference — https://developers.openai.com/api/reference/ruby/resources/decisions/methods/create [verified live]
- Prompt caching guide, OpenAI — https://developers.openai.com/api/docs/guides/prompt-caching [index]
- GPT-6 Luna model page, OpenAI — https://developers.openai.com/api/docs/models/gpt-6-luna?ref=hackernoon.com [index]

**Decisions API — secondary / practitioner**
- OpenAI Makes the Decisions API Generally Available, AccessAllGPT — https://www.accessallgpt.com/research/openai-decisions-api-general-availability-gpt-6-luna-pricing-limits
- What Is the OpenAI Decisions API?, Apidog — https://apidog.com/blog/openai-decisions-api/
- OpenAI's Decisions API: GA pricing, limits, and when to skip it, Pondero — https://pondero.ai/agents/guides/openai-decisions-api-guide/
- OpenAI's Decisions API Answers in 170 Milliseconds…, LLM Matchmaker — https://www.llmmatchmaker.com/blog/openai-decisions-api
- From Probabilities to Actions With the Decisions API, AICassindra — https://www.aicassindra.com/blogs/llm/openai_decisions_api_ga_thresholds.html [verified live]
- OpenAI Decisions API: Classify With Probabilities Using GPT-6 Luna, Masterprompting — https://masterprompting.net/blog/openai-decisions-api-classify-with-probabilities-gpt-6-luna
- OpenAI API tiers: Build, Launch and Grow, GrowthForgeAI — https://blog.growthforgeai.com/openai-api-tiers-build-launch-grow/
- OpenAI Decisions integration, LangChain docs — https://docs.langchain.com/oss/javascript/integrations/decision_models/openai
- What is Jev?, Braintrust — https://www.braintrust.dev/articles/what-is-jev

**LLM calibration and forecasting science**
- Tian et al. 2023, Just Ask for Calibration, arXiv — https://arxiv.org/abs/2305.14975 ; ACL Anthology — https://aclanthology.org/2023.emnlp-main.330/
- Kadavath et al. 2022, Language Models (Mostly) Know What They Know — https://arxiv.org/pdf/2207.05221
- Whelan 2026, Frontier Models Know More Than They Say (calibration benchmark) — https://www.henrywhelan.com/research/calibration-benchmark.html
- Schoenegger et al. 2024, Wisdom of the Silicon Crowd, arXiv HTML — https://arxiv.org/html/2402.19379v6/
- Prophet Arena / LLM-as-a-Prophet — https://www.alphaxiv.org/abs/2510.17638v2
- Metaculus 2026, AI Forecasting in 2026 (11-analysis synthesis) — https://www.metaculus.com/notebooks/43363/overview-of-ai-forecasting-research/
- ForecastBench summary, Primo — https://primo.ai/wiki/Predictive_Analytics
- AI vs Superforecasters: Parity Status May 2026, Parallect — https://www.parallect.ai/reports/ai-superforecaster-parity-may-2026-5d2e3f
- Beyond Brier (Vaticinus preprint) — https://vaticinus.com/beyond-brier-preprint.pdf
- Global Merger-Arbitrage Forecasting with Language Models (proceedings PDF) — https://storage.googleapis.com/lacuna-pdfs-lunar-airport-385023/pdfs/49/7c/497c78d3616b9ff8c2ad6eee152e25309aae471288cbc05a9e0248b0ea9347d9.pdf
- Superforecasting for traders (GJP summary) — https://www.macromomentumterminal.com/blog/superforecasting-for-traders

**Prediction markets**
- Dickerson et al. 2026, PNAS, PubMed record — https://pubmed.ncbi.nlm.nih.gov/42896054/
- Prediction Market Accuracy 2025–2026, PredScope — https://predscope.com/guide/prediction-market-accuracy-data
- Brier.fyi (cross-platform market Brier tracker) — https://brier.fyi/
- Prediction Markets concept synthesis (incl. PNAS study) — https://grimoire.cardboard-iguana.com/concepts/prediction-markets

**Bitter lesson, multiple testing, financial ML**
- Sutton 2019, The Bitter Lesson — http://www.incompleteideas.net/IncIdeas/BitterLesson.html
- Bitter lesson, Wikipedia — https://en.wikipedia.org/wiki/Bitter_lesson
- Multiple Testing Correction (Harvey–Liu–Zhu / deflated Sharpe synthesis) — https://sungchullee.github.io/financial_math_book_writing/ch24/limits_of_learning_in_finance/multiple_testing_correction/
- Sullivan, Timmermann & White 1999, Data-Snooping, Technical Trading Rule Performance, and the Bootstrap (PDF) — https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf
- Genetic-algorithm rule mining (killed experiment) — https://intel.hedonist.trading/research/genetic-algorithm-rule-mining/
- Baron et al. 2014, Two Reasons to Make Aggregated Probability Forecasts More Extreme (PDF) — https://dev-wharton-faculty.pantheonsite.io/wp-content/uploads/2015/07/2015---two-reasons-to-make-aggregated-probability-forecasts_1.pdf
- Satopää et al. 2014, Combining multiple probability predictions using a simple logit model (PDF) — https://daneshyari.com/article/preview/7408545.pdf

**Batch-judge engineering, drift, audit**
- How to build an LLM judge you can trust — https://www.prasad.tech/v2/blog/llm-judge-you-can-trust/
- Known biases of LLM-as-judge, and how to control for them — https://www.aiagentichandbook.com/questions/evals-4/
- Collecting Human Labels, Building LLM Judges… Handbook, Ch. 7 Operating — https://www.jiamingqu.com/techblog/human_data_llm_judge_handbook/ch7-operations.html
