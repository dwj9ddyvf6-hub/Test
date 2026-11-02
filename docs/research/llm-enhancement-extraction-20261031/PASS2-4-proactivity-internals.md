# PASS 2 — Dive 4: Proactivity Internals (artifact-level extraction)

Date: 2026-10-31. Method: raw file reads from `raw.githubusercontent.com` plus GitHub API trees; no repo code installed or executed. Every quoted block names its source path. Long artifacts: complete structure plus load-bearing sections verbatim, compression noted. Pass 1 reference: `CLUSTER-3-proactivity.md` and `REPORT.md` §2.2 in this directory.

**Scope note on "any other concrete artifact inside that awesome list that pass 1 rated ADOPT-IDEA":** inside `tao-hpu/awesome-proactive-agents`, the only entries with a concrete, readable code/data artifact that pass 1 rated ADOPT-IDEA are the three in scope (the list + its pilot, ProactiveAgent, ProactiveEval). The other ADOPT-IDEA memory entries reachable from the list's Memory layer (Mem0) were deep-dived in pass 1 as platforms, not gate artifacts, and have no intervention-gate artifact to extract. PRISM, YETI, the temporal-graph trigger, and HoloAssist remain paper/dataset pointers with no standalone code repo found in pass 1 (logged there); nothing new was reachable in this pass either. That is a coverage fact, not a silent drop — see the coverage ledger at the end.

---

# 1. tao-hpu/awesome-proactive-agents — the pilot, completely

Sources: `pilot/pilot.py` (178 lines, read in full, reproduced in §1.2), `pilot/README.md`, `pilot/results.txt` (checked-in expected output, reproduced in §1.4), `README.md` (213 lines, read in full; gate-relevant sections in §1.5).

## 1.1 What pass 1 got right, and the one thing it overstated

Pass 1's summary of the seeding rule, the five policies, and the lambda sweep is accurate. The overstatement: pass 1 (and the repo README) frame the pilot as an implementation of `intervene ⇔ E[benefit] − E[cost] > θ`. **The pilot contains no θ variable and never evaluates that inequality.** There is no expectation estimate, no per-fire benefit/cost comparison, and no threshold parameter anywhere in `pilot.py`. What the pilot actually implements is the *evaluation* half of the thesis: a fixed cost-weighted score `score(λ) = Σbenefit − λ·Σcost` swept over λ, which lets a reader see *post hoc* at which interruption-price a policy beats silence. The decision half (a gate comparing an estimate against θ at fire time) exists only as (a) the README thesis sentence and (b) the hand-parameterised `cost-sensitive` policy, whose three constants (`DETECT_RECALL`, `FA_FRACTION`, `SUPPRESS`) are a detector model, not a threshold. Anyone rebuilding "the gate" from pass 1 alone would have built the wrong thing: the rebuildable artifact is a **scorer**, and the gate must be designed around it. This is the single most important correction in this dive.

## 1.2 `pilot/pilot.py` — full logic, faithfully reproduced

The file is 178 lines, standard library only (`json`, `random`, `sys`, `collections.defaultdict`). Constants, verbatim:

```python
ANNOT = sys.argv[1] if len(sys.argv) > 1 else "holoassist-annot.json"
SEED = 13
CADENCE = 10.0          # seconds between fires for the `always` policy
DETECT_RECALL = 0.7     # cost policy: chance of catching a MUST window
FA_FRACTION = 0.2       # cost policy: false fires as a fraction of always-rate
SUPPRESS = 0.9          # cost policy: chance of suppressing a MUST-NOT fire
LAMBDAS = [0.25, 0.5, 1.0, 2.0, 4.0]

MUST_CORRECTNESS = {"Wrong Action, corrected by instructor verbally",
                    "Wrong Action, not corrected"}
MAY_PURPOSES = {"instructor-start-conversation_follow-up instruction",
                "instructor-start-conversation_describing high-level instruction",
                "instructor-start-conversation_confirming the previous action"}
```

### Window seeding (`load_sessions`) — exact mechanics

For each session in the HoloAssist annotation JSON (`data-annotation-trainval-v1_1.json`, 117 MB, linked from `pilot/README.md`):

- `t0 = float(e["start"])`, `t1 = float(e.get("end", e["start"]))`; session end `T` is the max `t1` over all events. Sessions with `T == 0` are dropped.
- An event seeds a **MUST** window `(t0, t1)` iff `e["label"] == "Fine grained action"` **and** `e["attributes"]["Action Correctness"]` is exactly one of the two strings in `MUST_CORRECTNESS`.
- Else, if `e["label"] == "Conversation"`: let `p = e["attributes"].get("Conversation Purpose", "")`. If `p` is exactly one of the three strings in `MAY_PURPOSES` → **MAY** window. Else if `p.startswith("student-start-conversation")` → **MUST-NOT** window. (Prefix match, not equality — any student-initiated purpose qualifies.)
- Everything else seeds nothing. Windows are stored as three independent lists per session; **windows may overlap across types**, and overlap resolution happens at scoring time, not seeding time (see below).

Benefit/cost grades (from the module docstring, confirmed in `score`): MUST benefit `b = 4` ("task failure averted"), MAY benefit `b = 2`, MUST-NOT cost `c = 4`, base false-alarm cost `c = 1` anywhere else.

### Policies — exact fire generation

```python
def fires_always(sess, rng, cadence=CADENCE):
    return [t * cadence for t in range(int(sess["T"] / cadence) + 1)]

def fires_random(sess, rng):
    n = int(sess["T"] / CADENCE) + 1
    return sorted(rng.uniform(0, sess["T"]) for _ in range(n))

def fires_cost(sess, rng):
    out = []
    for (a, b) in sess["must"]:
        if rng.random() < DETECT_RECALL:
            out.append(rng.uniform(a, b))
    n_fa = int((int(sess["T"] / CADENCE) + 1) * FA_FRACTION)
    for _ in range(n_fa):
        out.append(rng.uniform(0, sess["T"]))
    kept = []
    for t in out:
        if inside(t, sess["mustnot"]) is not None and rng.random() < SUPPRESS:
            continue
        kept.append(t)
    return sorted(kept)
```

Details pass 1 did not state:

- `always` fires at `t = 0` and then every `cadence` seconds, `floor(T/cadence) + 1` fires per session. The two reported cadences are 1.0 s and 10.0 s (the 1 s variant is a lambda overriding the default argument).
- `random` fires **exactly the same count** as `always` at 10 s, uniform over `[0, T]` — it is a count-matched control, not an independent rate.
- `cost-sensitive` is a *simulated detector*, not a gate: for each MUST window it fires once, uniformly inside the window, with probability 0.7; it then adds false fires at 20% of the always-10 s count, uniform over the whole session (these can land anywhere, including inside MUST/MAY/MUST-NOT windows); finally each fire landing in a MUST-NOT window is independently suppressed with probability 0.9. It never looks at MAY windows when deciding to fire.
- `never` is `lambda s, r: []`.
- Each policy is scored with a **fresh** `random.Random(SEED)` (seed 13), so policies do not consume each other's randomness; output is deterministic and `results.txt` is the expected output.

### Scoring (`score`) — exact semantics (Section 8.3 of the survey, per the docstring)

```python
def inside(t, windows):
    for i, (a, b) in enumerate(windows):
        if a <= t <= b:
            return i
    return None

def score(sessions, policy, rng):
    tot = defaultdict(float)
    for sess in sessions:
        fires = policy(sess, rng)
        credited_must, credited_may = set(), set()
        for t in fires:
            im = inside(t, sess["must"])
            iy = inside(t, sess["may"])
            iv = inside(t, sess["mustnot"])
            if im is not None and im not in credited_must:
                credited_must.add(im)
                tot["benefit"] += 4
            elif iy is not None and iy not in credited_may and im is None:
                credited_may.add(iy)
                tot["benefit"] += 2
            if iv is not None:
                tot["cost"] += 4
                tot["violations"] += 1
            elif im is None and iy is None:
                tot["cost"] += 1
        tot["fires"] += len(fires)
        tot["must_hit"] += len(credited_must)
        tot["must_total"] += len(sess["must"])
    return tot
```

Load-bearing semantics, in order:

1. **Benefit accrues once per window, on the first in-window fire only** (the `credited_*` sets). Repeat fires inside an already-credited window earn nothing.
2. **MUST dominates MAY**: a fire inside both is credited as MUST (the MAY branch is an `elif` additionally guarded by `im is None`). A fire inside a MUST window never also credits an overlapping MAY window.
3. **Cost is per fire, independent of benefit**: a fire inside a MUST-NOT window pays 4 and increments `violations` *even if it also credited a benefit* (overlap is possible; benefit and violation are not mutually exclusive). A fire inside a MUST or MAY window (and not in MUST-NOT) pays 0 — "acceptable moments". Any other fire pays 1. Silence on MAY is never penalised (no term for missed MAY); there is also **no penalty term for a missed MUST** — a miss only shows up as lost benefit and lower recall.
4. **Reported metrics**: `recall = must_hit / must_total` (MAY hits do not count toward recall at all); `viol% = violations / fires` (NaN for `never`, printed as `--`); `score(λ) = benefit − λ·cost` for λ ∈ {0.25, 0.5, 1, 2, 4}.
5. `inside()` returns the **first** matching window index (linear scan, inclusive bounds `a <= t <= b`).

### Rebuild recipe (the gate design, as actually specified by the artifacts)

To rebuild this scorer for any proactive lane: (1) log a session timeline; (2) label windows MUST (a need where acting averts a failure, b=4), MAY (a moment where acting is welcome, b=2), MUST-NOT (a moment where acting is a violation, c=4), everything else c=1 per fire; (3) replay candidate policies as fire-time lists; (4) credit benefit once per window, MUST before MAY, charge cost per fire independently; (5) report fires, MUST recall, violation %, benefit, cost, and `benefit − λ·cost` at λ ∈ {0.25, 0.5, 1, 2, 4}; (6) a policy is only worth deploying at the λ that prices your real interruption cost — if `never` wins at that λ, silence is the correct policy. A live gate then needs the part the pilot does *not* supply: an estimator of P(this fire lands in a MUST window) and a θ. The pilot's contribution is proving the scorer separates policies (see results) and that the ranking *flips* with λ.

## 1.3 `pilot/README.md` — honesty clause (verbatim)

> It shows the metric suite is executable on seeded labels and separates always-speak (two cadences), never-speak, random, and a cost-sensitive policy, with the lambda sweep exposing the silence-optimal regime. It does not validate the labels themselves: the windows are seeded from existing annotations by the documented rule, not judged by humans, and inter-annotator agreement is the first deliverable of the human annotation phase, not of this pilot.

Run contract: download the 117 MB annotation file, `python3 pilot.py holoassist-annot.json`, standard library only, seed fixed at 13, output deterministic and matching `results.txt`.

## 1.4 `pilot/results.txt` — checked-in expected output (verbatim)

```
sessions=1758  hours=131.5  must=4144 (mean 3.3s)  may=21707  mustnot=3170 (mean 1.4s)
policy             fires  recall   viol%   benefit      cost     s@0.25      s@0.5      s@1.0      s@2.0      s@4.0
always (1s)       474350   0.962    0.82     53292    421044     -51969    -157230    -367752    -788796   -1630884
always (10s)       48226   0.292    0.84     14468     43263       3652      -7164     -28795     -72058    -158584
never                  0   0.000      --         0         0          0          0          0          0          0
random             48226   0.245    0.97     13434     42622       2778      -7877     -29188     -71810    -157054
cost-sensitive     11736   0.703    0.09     13602      7670      11684       9767       5932      -1738     -17078
```

Reading pass 1 did not do: corpus is 1,758 sessions / 131.5 hours; MUST windows average only **3.3 s** and MUST-NOT **1.4 s** (timing is a seconds-scale problem in this substrate); MAY windows outnumber MUST 5.2:1. The cost-sensitive policy fires 4.1× less than always-10 s, *more than doubles* its recall (0.703 vs 0.292 — because its fires are aimed at MUST windows rather than spread on a grid), and cuts violation rate ~9× (0.09% vs 0.84%). Crossover points: cost-sensitive beats `never` only for λ < 2; always-10 s beats `never` only at λ = 0.25. At λ = 4 every speaking policy is deeply negative — the silence-optimal regime is not an edge case, it is most of the high-λ table.

## 1.5 README gate-relevant text (verbatim extracts)

Thesis and taxonomy diagram (`README.md`):

> **Organizing thesis:** an intervention is a decision under uncertainty.
> `intervene ⇔ E[benefit of acting] − E[cost of interrupting] > θ`
> Every work below is placed by which part of that inequality it advances.

> 5. EVALUATION & SELF-IMPROVEMENT (the loop) — offline: timing precision/recall · annoyance benchmarks; online: accept / dismiss / "snooze 3 days" = reward events → feedback re-tunes θ (the smallest possible RL)

Feedback-depth table (`README.md` §5, verbatim):

| Level | Signal | Cost | Attribution |
|---|---|---|---|
| **L0 explicit** | accept / dismiss / snooze | free but sparse & biased | trivial |
| **L1 implicit behavioral** | did the user follow the suggestion; gaze dwell vs aversion; recovery time after interruption; undo | dense, no user effort | easy–moderate |
| **L2 outcome** | task completion delta, time saved, errors avoided | needs task instrumentation | delayed → credit assignment |
| **L3 long-term** | retention, trust, user disabling proactivity entirely (the ultimate negative reward) | population-level A/B only | hardest |

Maturity levels (`README.md` §5, verbatim):

> 1. **Log only**: feedback collected, never used (most products today).
> 2. **Threshold adaptation**: per-user, per-context updates to θ; one parameter, bandit-style. The smallest possible RL, and probably where always-on assistants should start.
> 3. **Policy learning**: a learned reward model over interventions (Proactive Agent is the offline version of this).

> The asymmetry that makes this hard: negative signals are cheap and abundant (every dismissal is one), while positive signals are weak and delayed. … this is why self-improvement is drawn inside the evaluation layer rather than as a sixth stage: the feedback edge is only as good as the measurement that defines it (`reward ⊆ eval`).

Decision-layer historical anchors the README prices explicitly (compressed; full table in `README.md` §2): Horvitz 1999 three-way policy (stay silent / ask / act) with the threshold rising with depth of focus; Iqbal & Horvitz 2007 field magnitude (~20-minute disruption arc per alert, 27% of suspended windows unresumed after two hours, 27 workers / 2,267 logged hours); InterruptMe 2014 path-dependence (sentiment more than halves after eight other notifications in the prior two hours); PRISM 2026 as "calibrated P(user acceptance) exceeds a threshold derived from asymmetric costs of missed help vs false alarms; −22.78% false alarms, +20.14% F1 on ProactiveBench" — i.e. PRISM is the one cited work that *does* implement an explicit θ-style gate, and it does so on ProactiveAgent's own benchmark.

## 1.6 Design invariants (awesome list + pilot)

- Benefit is window-scoped and single-credit; cost is fire-scoped and always charged. Never conflate the two units.
- A violation (MUST-NOT fire) is charged even when the same fire earns a benefit.
- Misses are priced as forgone benefit + recall loss, never as a direct cost — the scorer cannot express "you should have spoken" beyond recall.
- Policy ranking is λ-relative; reporting a single accuracy/score number is a category error in this design.
- Seeded labels are explicitly *not* human-judged ground truth (pilot README honesty clause).

## 1.7 Refined verdict

Pass 1 verdict stands (ADOPT-IDEA, cluster's top find) with one sharpening: **adopt the scorer verbatim in shape; do not claim the pilot implements θ.** The θ gate must be built (estimator + per-context threshold + L0 feedback adaptation), with PRISM's formulation (calibrated P(accept) vs asymmetric-cost threshold, on ProactiveBench) as the nearest published gate design. The pilot also gives a concrete default price table (4 / 2 / 4 / 1) and a concrete λ grid to start from, which pass 1 did not extract as reusable constants.

---

# 2. thunlp/ProactiveAgent — prompts, reward model, Gym, ProactiveBench construction

Sources read in full this pass: `agent/prompt.py`, `agent/ragent.py`, `agent/README.md`, `agent/components.py` (structure), `gym/components/activeagent.py`, `gym/components/reward.py`, `gym/components/environment.py`, `gym/components/user.py`, `gym/models/env.py`, `gym/models/user.py`, `gym/main.py`, `gym/example.yaml`, `eval/reward_model_template.py`, `eval/reward_model_scoring.py`, `eval/judge_agent_prediction.py`, `eval/calculate_agent_performance.py`, `eval/README.md`, `dataset/README.md`, `dataset/build_scenes.py`, `dataset/build_agent_trainset.py`, `dataset/build_reward_trainset.py`, `dataset/run_datagen.py`, `dataset/annotation/convert_annotations.py`, `dataset/calculate_human_agreement.py`, `dataset/seedtask.yaml` / `dataset/scenes.yaml` (structure + samples), `dataset/test_data/splits.json`, `dataset/reward_data/test_data.jsonl` (full, 120 rows) and `train_data.jsonl` (full, 1,629 rows; counts only).

## 2.1 The live agent prompt — `agent/prompt.py` (verbatim, complete)

```python
SYSTEM_PROMPT = \
'''<Role> You are a helpful assistant that provides proactive suggestions to the user.
</Role>
<Task> Understand what the user is doing and anticipate their needs based on events. Only propose assistance when you fully understand the user's actions. Use available operations to ensure the task is feasible. Execute the task if the user accepts your proposal. </Task>
<Format> Respond in the following JSON format:
{
    "Purpose": "The purpose of the user's last action.",
    "Thoughts": "Your thoughts on the user's actions.",
    "Proactive_Task": "Describe your proposed task, or set to `null` if no assistance is needed.",
    "Response": "Inform the user about your assistance if proposing a task.",
    "Operation": "The tool call format if you are going to execute a task."
}
</Format>
<Rules>
- Ensure the proposed task is relevant to the events. - Focus on the user's current needs and predict helpful tasks.
- Consider the timing of events.
- Only offer proactive assistance when necessary.
- Deduce the user's purpose and whether they need help based on event history.
- Set `Proactive_Task` to `null` if the user doesn't need help. Your `Proactive_Task` should be as short as possible. Best as a short phrase.
- Some Operations will be provided for you to use. You need to pick the best operation with the most suitable arguments if you propose a task, so that the opeation can be executed. You must select one operation if you propose a task.
- Set `Operation` to `null` if no task is proposed, else set the format as a string containing the name of the tool and the arguments joined by separator '&' like [func_name&param1=value1&param2=value2]. YOU MUST CHOOSE ONE OPERATION IF YOU PROPOSE A TASK.
- Pay attention to the user's feedback on your assistance in provious one turn: Try not to disturb the user when they ignore your assistance, and try another approach when they reject your assistance. Even the user accept your assistance, you should not propose some related tasks in the next turn.
</Rules>
<Format_example>
{
    "Purpose": "The user is trying to search for some best programming languges",
    "Thoughts": "Since the user is making a search query, I think I can offer help by calling the search tool.",
    "Proactive_Task": "Help search for best programming languages",
    "Response": "Do you want me to help you do the search job?",
    "Operation": "search&query=best+programming+languages"
}
</Format_example>
'''
```

Pass 1 missed / understated:

- The feedback taxonomy lives **only in one Rules sentence** (quoted above, including the source typos "provious"/"opeation"/"languges" — the prompt ships unproofread). There is no code implementing "propose less after ignore": the DemoAgent loop relies on the model reading this sentence plus the feedback event in history. The three-signal policy is a *prompt convention*, not a mechanism.
- `Operation` is a flat string protocol (`func&param=value&...`), not structured tool calling, and proposing a task **requires** selecting exactly one operation. A proposal without an executable operation is schema-invalid by instruction.
- The live loop (`agent/ragent.py`): `--interval` default **15 s**; PC mode requires `--chromes`; sensing is ActivityWatch buckets (`afk`, `window`, `web`, `vscode`) plus `pynput` keyboard/mouse splicing via `ActionListener` (`agent/README.md`); periods where the user is not focused on Chrome or VS Code are filtered out before the agent sees them.

## 2.2 The Gym agent prompt — `gym/components/activeagent.py` (verbatim) and the schema drift

```python
SYSTEM = """<Role> You are a helpful assistant that provides proactive suggestions to the user. </Role>

<Task> Understand what the user is doing and anticipate their needs based on events. Only propose assistance when you fully understand the user's actions. Use available operations to ensure the task is feasible. Execute the task if the user accepts your proposal. </Task>

<Format> Respond in the following JSON format:
{
    "Purpose": "The purpose of the user's last action.",
    "Thoughts": "Your thoughts on the user's actions.",
    "Proactive Task": "Describe your proposed task, or set to `null` if no assistance is needed.",
    "Response": "Inform the user about your assistance if proposing a task."
}
</Format>

<Rules>
- Ensure the proposed task is relevant to the events. - Focus on the user's current needs and predict helpful tasks.
- Consider the timing of events.
- Only offer proactive assistance when necessary.
- Deduce the user's purpose and whether they need help based on event history.
- Set `Proactive Task` to `null` if the user doesn't need help.
</Rules>"""

STEP_OBJ = {
    "Instructions": "Now analyze the history events and provide a task if you think the user needs your help.",
}

EXEC = """{
    "Instructions": "Decide what to do next by executing available actions.",
}
<Format>
Respond in the following JSON format:
{
    "Thoughts": "Your thoughts on the situation.",
    "Action": "The action to take next. Set to `null` if no action is needed or if the user rejects your proposal."
}
</Format>"""
```

**Schema drift pass 1 never reported:** the Gym/training schema uses the key **`"Proactive Task"` (with a space) and has no `Operation` field**; the live demo schema uses **`"Proactive_Task"` (underscore) plus `Operation`**. The reward model, the trainset builders, and all benchmark scoring use the Gym spelling; the shipped demo uses the other. `extrat_pred()` in `activeagent.py` normalises the string `"null"` to `None` for `"Proactive Task"` and `"Response"`. Any rebuild must pick one spelling — the artifacts disagree.

## 2.3 The reward gate loop — `gym/components/activeagent.py::step` + `gym/components/reward.py` (exact mechanics)

- The gate is **opt-in by environment variable**: only when `USE_ACTIVERM == "True"` is a `RewardModel` constructed and consulted. Otherwise the proposal is published ungated (`self.add(sinkChannels.agent.proactive, ..., silent = pred is None)` — a null proposal is added *silently*, i.e. logged but not surfaced).
- Judge call (`reward.py`): gathers all events, calls model **`activerm`** with `format_reward_instruction(obs, pred_task)` (§2.4), temperature `0.0`, rising to `0.4` on tenacity retries (`0.0 + 0.4 * (attempt_number > 1)`). Parses `{"thought", "judgement"}`; `is_accepted = (judgement == "accepted")`.
- Retry loop (verbatim core):

```python
retry_times = 3
while not res.is_accepted and retry_times > 0:
    step_obj["Previous Prediction"] = pred
    step_obj["Status"] = "Rejected"
    step_obj["User Feedback"] = res.thought
    step_obj["Instructions"] = f"Your previous prediction is rejected! You must make a different prediction."
    res = await self.cl.exec(..., completions_kwargs={"temperature": 0.8})
    pred = self.extrat_pred(res)
    res = await rm.judge(pred.get("Proactive Task", None))
    retry_times -= 1
if not res.is_accepted:
    self.logger.error("Prediction is rejected! Will Skip this step.")
    return
```

So: at most **3 regenerations at temperature 0.8**, each conditioned on the previous prediction + the judge's first-person thought + a must-differ instruction; total rejection after the budget = **silence for that step** (return without publishing). Note the judge also judges **null proposals** — a null can be rejected (that is the Missed-Need case), and the loop then forces the agent to propose *something different*, i.e. a task. Pass 1 described the retry loop but not that it applies symmetrically to nulls, nor the temperature schedule, nor that the gate is env-flag optional.
- Execution phase (`exec`): after acceptance, a separate loop prompts with `EXEC` and runs actions until the model returns `Action: null` (or the user rejects), then restores the `step` listener. Proposing and executing are separate prompt regimes.
- The simulated user (`gym/components/user.py::judge`) uses the **same** RewardModel when `USE_ACTIVERM` is set; otherwise the user-simulation LLM itself judges with prompt `"Do you accept the agent's proposal?"` returning the `Judge` model below. In Gym data generation, "user acceptance" and "reward gate" are therefore often *the same model* — a circularity worth naming when reusing Gym-generated data.

```python
# gym/models/user.py (verbatim)
class Judge(BaseModel):
    thought: str = Field(description="Your thought on the agent's proposal based on current events and what you are doing.")
    is_accepted: bool = Field(description="Whether you accept the agent's proposal or not.")
```

## 2.4 The reward model rubric — `eval/reward_model_template.py` (verbatim, complete)

```python
SYSTEM = '''<Task>
Evaluate the task proposed by the proactive assistant as the user.
</Task>

<Rule>
0. Analyze the current observation to understand your current situation and requirements.
1. If the proposed task is `null` (indicating no task is proposed under the current observation), follow these steps:
   - Accept the `null` task if you believe there is no need for a task.
   - Reject the `null` task if you believe a task is needed.
2. Minimize interruptions from the assistant by only accepting tasks that are valuable.
3. Evaluate the current observation and make a judgment on the proposed task accordingly.
</Rule>

<Format>
You should answer with following JSON format:
{
    "thought": "Give your thoughts first, then provide the judgement of the task.",
    "judgement": "accepted or rejected"
}
</Format>'''

def format_reward_instruction(obs, pred_task):
    inst_dict = {
        "Observations (Time Ascending)": obs,
        "Proposed Task": pred_task,
        "Instruction": "Now give your judgement. You should complete the reasoning process in first person."
    }
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(inst_dict, ...)}]
```

That is the **entire** rubric. Pass 1 called it a "reward model design and rubric" without noting how thin the rubric is: three operative rules, no scoring scale, no cost term, no per-category guidance; the judgement is binary, first-person role-play as the user, with the only normative pressure being rule 2 ("Minimize interruptions … only accepting tasks that are valuable"). All of the gate's discrimination power comes from **fine-tuning on human labels** (§2.5), not from the prompt. A prompted-only rebuild using this template should expect the published general-model numbers (GPT-4o F1 0.6704, FA-slice 0.0), not the fine-tuned 0.918.

## 2.5 Reward training-set construction — `dataset/build_reward_trainset.py` + `dataset/annotation/convert_annotations.py` (the part pass 1 missed entirely)

**Annotation → labels (`convert_annotations.py`, a notebook-style script, seed 42 for the split):**

- Annotators (Gradio app, `dataset/annotation/main.py`; annotator sees an event trace + candidate tasks, checks tasks in their favour or `Reject all`) produce per-trace labels. `parse_label`: `"Reject all"` → all-False; a list → True for checked indices.
- A candidate task becomes a training row only on a **≥2-of-3 majority** (`valid_true = sum >= 2` → `valid: True`, CD candidate; `valid_false = sum(1-a) >= 2` → `valid: False`, FA candidate).
- Null rows are synthesised from annotator behaviour: if any task was unanimously accepted (`help_needed = True`) and ≥2 annotators selected nothing, a row `{pred_task: None, valid: False, category: MN}` is added (help was needed, silence was wrong); if >0 annotators selected nothing and help was not unanimously needed, a row `{pred_task: None, valid: True, category: CR}` is added.
- **Test-set selection is agreement-gated**: per category, first take rows where all **3 annotators agree unanimously** with the label, up to 30; only if a category is short, fill with 2-of-3 majority rows. Result, verified by reading the shipped file: `dataset/reward_data/test_data.jsonl` = **120 rows, exactly 30 per category (MN / CR / CD / FA), 60 valid / 60 invalid**. Row schema (verbatim keys): `{"obs": [{"time", "event"}, ...], "pred_task": str|null, "valid": bool, "help_needed": bool, "annotation": [bool×3], "category": str}`.
- Training file, verified: `train_data.jsonl` = **1,629 rows, heavily imbalanced**: FA 913, CD 474, CR 149, MN 93. Human agreement is computed by `dataset/calculate_human_agreement.py` as the fraction of individual annotations equal to the majority `valid` label, over both files (script verbatim in repo; no checked-in number).
- Category definitions (`README.md`, verbatim): **MN** "the user needs help but the agent does not provide help"; **NR/CR** "the user does not need help and the agent does not prompt any help"; **CD** "the user needs help and the agent provides help"; **FA** "the user does not need help but the agent prompts help". (The README calls CR "Non-Response (NR)"; the code and data call it "Correct-Rejection (CR)". Another naming drift.)

**Labels → fine-tuning data (`build_reward_trainset.py`) — rationalisation, not direct SFT:**

1. **Balancing by upsampling**: `max_count = int(max(category_counts) / 5)`; any category below `max_count` is topped up with `random.choices` duplicates of its own rows before generation.
2. A teacher model (**Llama-3.1-70B**, served locally, model name `llama3.1-70b`) is given the observations, the proposed task, **and the human judgement** (`"User Judgement": "accepted"/"rejected"`), with the instruction: "You as the user have given the judgement to the proposed task. You should complete the reasoning process for your judgement in first person. Try to understand the decision and give same judgement." I.e. the teacher must *rationalise the known-correct label* in first person.
3. **Consistency filter**: the generated `thought` is re-judged by a separate check prompt ("generate the judgement by inferring the thought") sampled **5 times at temperature 0.8**; every sample must reproduce the same judgement, and the judgement must equal the human label, or the row is discarded (`ValueError` paths in `obtain_reason`).
4. Surviving rows are rewritten into the inference format of §2.4 (system + user with observations/task, assistant = the rationalised `{thought, judgement}`) and saved as `trainset_reward_llama.json` in LLaMA-Factory conversation format.

**Agent training-set construction (`dataset/build_agent_trainset.py`):** Gym event streams are replayed; at each agent turn `make_valid_prediction` samples the agent (temperature 0.8) and judges with the reward model, retrying with the rejection feedback object (`{"Previous Prediction", "Status": "Rejected", "User Feedback", "Instructions": "Your previous prediction is rejected! You must make a different prediction."}`) for up to **15 trials** (vs 3 in the live Gym loop — a second budget drift) until the reward model accepts; only accepted predictions enter the SFT data. Context is truncated by `cut_messages` (max 20,000 chars total, max 10,000 chars of agent responses, walking backwards from the newest message). The flywheel is therefore: *the reward model is both the data filter and, at eval time, the judge* — reported agent scores are agreement-with-the-reward-model by construction.

## 2.6 Gym pipeline — scenes, environment, user (structure + load-bearing prompts)

Pipeline (`dataset/README.md` + `gym/README.md` + `gym/main.py`): `seedtask.yaml` → `build_scenes.py` → scene YAMLs (`scenes.yaml` format = `gym/example.yaml` format) → `run_datagen.py` (ThreadPoolExecutor, 4 workers, one `gym.main` subprocess per scene) → per-scene `.jsonl` event streams in `dataset/agent_data/` → `build_agent_trainset.py` → agent SFT data. Gym components communicate over a CodeLinker EventSink with channels for events / activity / agent.proactive / agent.ops / env.status.

Scene YAML schema (from `gym/example.yaml`, structure verbatim, persona content paraphrased): top-level `environment:` with `agent_ops` (list of operation signatures, e.g. `terminal_run(command)`, `file.open(file_path, mode)`, `browser.open(url)`, `code_suggest_fix(error_message, code_snippet)` — 12 ops in the example), `description` (a paragraph describing a fictional office worker persona and setting — synthetic fixture data, not a real person), `entities` (named objects in the scene), `events_example` (20 short example events mixing user and agent actions); `eventSink: {out_file}`; `user:` with `description`, `goal`, `theme`.

`build_scenes.py` scene-generation system prompt (verbatim):

```
<Task>
You are tasked to generate realistic scenarios where a user might need assistance from an AI assistant. Always remember to keep the scene realistic and believable by including as much details as possible.
</Task>
<Rule>
- You will iteratively generate more information about the scene. Make sure each time you add a new detail, it is consistent with the previous details. Always generate new content based on the previous generated content.
- You can add as many details as you want, but make sure they are consistent with the previous details.
- Try to generate diverse details about the scene. You will be tasked to simulate events in the scene later.
</Rule>
```

The builder then runs a fixed 5-step iterative expansion (temperature 1.0, semaphore 8): scene description (profile / context / behavioural patterns / assistance cues / potential tasks) → tasks + user character → entities (3 guiding questions) → agent action space (must be "implementable and realistic for a text-and-vision model based agent", with detailed parameters/returns) → ≥10 example events (objective, single-event granularity, "include possible failures or unexpected events", explicitly including *meaningless* actions sampled from real traces) → structured JSON summarisation into the scene YAML schema. `seedtask.yaml` provides the seeds: task lists + real-captured `sample_events` per theme (coding assistant, writing, daily life).

Environment simulator (`gym/components/environment.py`): system prompt requires objective, entity-consistent event generation with "occasional failures or unexpected events for realism"; each step samples **5 example events**, swaps the subject (User↔Agent string replacement) to match the latest activity's source, and generates follow-on events with per-event `deltatime` (seconds) advancing a simulated clock (`EnvironmentSetting.time`, format `M-D H:M:S`). All Gym data models are Pydantic schemas in `gym/models/env.py` (`Operation`, `EntityStatus`, `EntityUpdate`, `EnvironmentSetting`, `Events`) and `gym/models/user.py` (`UserInfo`, `Activity{is_finished, act}`, `Judge`) — the schemas are the contract; generation is structured-output against them.

User simulator (`gym/components/user.py`): system prompt (verbatim core): "Generate human-like activities with distinct characteristics and identities… Respond like a real user; don't be overly predictable… Critically evaluate the received information, as it may not always be accurate." Defaults: `adapt_times=2` environment-adaptation rounds, `action_times=7` action steps per scene (listener `max_emit_time` caps).

## 2.7 ProactiveBench — what the benchmark actually is (numbers reconciled)

Three different sizes circulate and pass 1 used only the largest:

- **6,790 events** (`README.md` data table): 136 instances (46 coding / 46 writing / 44 daily life) with 2,275 / 2,354 / 2,161 events. This is the *event corpus* size, not the scored test-set size.
- **227 events** (`eval/README.md`, verbatim: "Currently, the test set contains `227` events", three categories: coding, writing, daily life) — the ProactiveBench test set as shipped for agent evaluation.
- **120 rows** — the *reward model's* test set (§2.5), balanced 30×4. The headline **F1 0.918 / accuracy 0.9167** is measured on these 120 rows, not on 6,790 or 227.

Agent evaluation flow (`eval/README.md` + scripts): `eval/script.py` runs the candidate model over test traces → `judge_agent_prediction.py` sends each prediction to the reward model (`activellama`, semaphore 32, up to 10 tenacity attempts, temperature 0.5 after attempt 2; a missing/empty `agent_response` is normalised to `[None]`) → `calculate_agent_performance.py` scores **only the splits in `dataset/test_data/splits.json`**, which are `real_average` / `real_coding` / `real_writing` over 12 files (`code_11..16.json`, `writing_11..16.json`) — note: **no daily-life split exists in the shipped splits file**, despite the three-category description.

Metric definitions (`eval/calculate_agent_performance.py::calculate_scores`, verbatim logic): for each event, zip `agent_response` with reward-model `judgement`: pred non-null + judge-accept → TP; pred non-null + judge-reject → FP; pred null + judge-accept(null) → TN; pred null + judge-reject(null) → FN. Then `Recall = TP/(TP+FN)`, `Precision = TP/(TP+FP)`, `Accuracy = (TP+TN)/(all)`, **`False-Alarm = FP/(TP+FP)` — i.e. FA ≡ 1 − Precision, not a false-positive rate over negatives**, `Accept Rate = tasks_accepted/tasks_proposed` (numerically identical to Precision in this code). This definitional point matters: the widely quoted "GPT-4o false-alarm 51.85%" is exactly `1 − 48.15% precision` from the README table (GPT-4o: recall 98.11%, precision 48.15%, F1 64.60%; Qwen2-7B-Proactive: recall 100%, precision 49.78%, F1 66.47%; LLaMA-3.1-8B-Proactive: F1 66.25%). Reward-model comparison table (`README.md`): GPT-4o per-category MN 0.0333 / NR 1.0000 / CD 1.0000 / **FA 0.0000**, accuracy 0.5083, F1 0.6704; fine-tuned model MN 0.8000 / NR 0.8667 / CD 1.0000 / FA 1.0000, accuracy 0.9167, F1 0.9180. GPT-4o's failure is specifically: it almost never recognises a missed need (MN 3.3%) and never recognises a false alarm (FA 0%) — it accepts nearly everything, which is why its recall is 1.0 and its precision ~0.50.

## 2.8 Design invariants (ProactiveAgent)

- Null is a judged action, not an absence of action: silence can be accepted (CR/TN) or rejected (MN/FN) by the same gate that judges proposals.
- The gate's authority comes from human majority labels (≥2/3; test rows preferentially unanimous), distilled via label-conditioned rationalisation + a 5-sample thought/judgement consistency filter — not from the rubric text.
- Rejection is informative and bounded: judge thought is fed back verbatim, regeneration must differ, budget is finite (3 live / 15 in data generation), exhaustion = silence.
- Accept / reject / ignore are three distinct *human* signals with distinct instructed policy effects (execute / change approach / throttle + no related proposal next turn even after an accept) — but in the shipped demo this is prompt text, not enforced state.
- Evaluation is agreement with the reward model; the reward model is also the training-data filter. Scores are internally consistent, not independently grounded, except for the 120-row human-labelled reward test set.

## 2.9 Refined verdict

Pass 1 verdict stands (ADOPT-IDEA; do not adopt code/sensing) with three sharpenings. (1) A prompt-only rebuild of the reward gate using §2.4's template should be expected to perform at the *general-model* level (~0.67 F1, ~0 FA detection), because the published gate quality is a fine-tuning result; the transferable artifact is the **labelling + rationalisation + consistency-filter pipeline** (§2.5), which is the real design. (2) Quote benchmark sizes precisely: 6,790-event corpus / 227-event agent test set / 120-row reward test set; and quote False-Alarm as `1 − precision` under this repo's definition. (3) The schema drifts (`Proactive Task` vs `Proactive_Task`, CR vs NR, retry 3 vs 15) mean the repo cannot be treated as a single coherent spec — a rebuild must fix one spelling, one name, and one budget explicitly.

---

# 3. liutj9/ProactiveEval — full rubric text, both stages, plus generation pipeline

Sources read in full this pass: `readme.md`, `eval/README.md`, `eval/config.py`, `eval/config.yaml`, `eval/prompt/target_planning_prompt.py`, `eval/prompt/conversation_eval_prompt.py`, `eval/prompt/conversation_generation_prompt.py`, `eval/prompt/target_planning_eval_examples.py` (42 KB; structure + representative examples verbatim, rest compressed — noted where), `eval/target_generation.py`, `eval/target_planning_eval.py`, `eval/conversation_generation.py`, `eval/conversation_dialogue_eval.py`, `dataset/README.md`, all 18 dataset files (counts verified by parsing), `dataset_generation/prompt/data_generation_prompt.py`, `dataset_generation/prompt/data_refiement_prompt.py` (filename typo is in the repo), `dataset_generation/prompt/topic_tree_construction_prompt.py`, `eval/Human_Evaluation/` result files (sampled). Not present in the shipped tree despite being referenced by `eval/README.md`: `eval/prompt/` is present, but `eval/main.py` exists while the top-level `readme.md` quick-start names scripts (`target_generation.py` etc.) that live under `eval/` — paths are relative to `eval/`. No licence file exists (pass 1 finding confirmed).

## 3.1 Dataset — verified counts and schema

Six domains (spelling as in repo): `persuasion`, `system_operation`, `ambigious_instruction` [sic], `long-term_follow_up`, `glasses_assistant`, `recommendation`. Each domain ships `eval.json` = `fair.json` + `hard.json` (verified by parsing all 18 files):

| Domain | eval | fair | hard |
|---|---|---|---|
| persuasion | 77 | 31 | 46 |
| system_operation | 37 | 22 | 15 |
| ambigious_instruction | 57 | 20 | 37 |
| long-term_follow_up | 61 | 27 | 34 |
| glasses_assistant | 45 | 27 | 18 |
| recommendation | 51 | 30 | 21 |
| **Total** | **328** | **157** | **171** |

Pass 1's "328 scenarios across 6 domains" is confirmed exactly, and the fair/hard split (which pass 1 did not report) is a *refinement-difficulty* split produced by the generation pipeline (§3.5): hard items are the rewritten + noise-embedded variants.

Item schema (verbatim from a shipped item, content abridged only in the long prose fields):

```json
{
  "item": {
    "environment": {
      "user_information": "<multi-sentence dated log of user activities>",
      "trigger_factor": "<multi-sentence account of the assistant-side event/experience>"
    },
    "target": "Encourage the user to explore digital graphic design tools",
    "sub_target": [
      "Acknowledge the user's artistic approach and concerns about digital tools",
      "Introduce the possibilities digital tools offer for creative expansion",
      "Share examples of artists combining traditional and digital methods",
      "Recommend beginner-friendly tools suitable for their artistic vision"
    ],
    "topic": "{'Persuasive scenarios': {'Career Development': {'Work-Life Balance Strategies': 'Work Boundaries'}}}"
  }
}
```

Trigger-factor definitions per domain (`eval/config.py::_get_fixed_params`, verbatim):

- persuasion: "the trigger factor is assistant's information, ability, or experience."
- long-term_follow_up: "the trigger factor is a past conversation history that inspires the assistant proactively initiate conversation now."
- system_operation: "the trigger factor is the specific sequence of opeation behaviors currently captured from the user."
- ambigious_instruction: "the trigger factor is an instruction with vague elements and unclear user intention."
- glasses_assistant: "the trigger factor is either an external event the user perceives or the user's own state/behavior at that moment captured from a smart glasses."
- recommendation: "the trigger factor is assistant's preference, habits, or favors"

## 3.2 Stage 1 — Target Planning: generation prompt and full rubric

Generation prompt (`eval/prompt/target_planning_prompt.py::target_generation_prompt`, verbatim):

```
<Task>
Your task is to generate proactive dialogue target and sub_targets based on the provided environment.
The environment includes user information and trigger factor. User information consists of the background details exhibited by the user in the previous interaction. trigger factor is current received event, ambigious instruction, or self-task that need you to proactively initiate conversation.
The target should be the action that the assistant will proactively take to achieve a specific goal.
The sub_targets should be a plan including action list, which decompose target and show the process of the conversation AI guide the target to the user.
In this case, {trigger_description}
The target and each sub_target should be less than 10 words.
The number of sub_targets is 2-4.
</Task>
<Format>
Just return Target and sub_targets as **JSON** Format. The format is {{"Target":"", "sub_targets":["",""]}}
</Format>
<Input>
{env_str}
</Input>
```

(Note: the shipped dataset's own reference targets routinely exceed the 10-word constraint — e.g. the reference sub-targets in §3.1 run 11–13 words. The constraint binds the *model under test*, not the references.)

**The complete Target Planning rubric** (`target_planning_eval_prompt`, verbatim — this is the entire normative text):

```
<Task>
You are a helpful assistant. You will receive an envioronment, which includes user information and trigger factor. User information consists of the background details exhibited by the user. trigger factor is the cause that motivates the assistant's to proactively initiate conversation.  The target should be the action that the assistant will proactively take to achieve a specific goal. The sub-targets decompose target, showing the process of the conversation AI guide the target to the user. You need to evaluate the quality of the generated target, based on the reference target. Your generated score to the generated target should be 1-10. The higher the score, the better the target and sub-targets.
task description: {trigger_description}
</Task>
<Rule>
1. IMPORTANT: You should pay attention to the task description and the reference target to give your score.
2. If you think the generated target is better than the reference target, return 10.
3. If you think the generated target is worse than the reference target, return 1-9.
4. You should analyze the difference in action, specific entities, limited conditions between the generated target and the reference target, and give a reason for your score. And the reason should be 3-4 sentences.
</Rule>
<Received Information>
environment:{env_str}
</Received Information>
<Generation>
reference target: {generation_0}
generated target: {generation_1}
</Generation>
<Example>
{examples}
</Example>
<Format>
Just return a JSON Format as {{"reason":"(your compare process)", "score":(your score)}}
</Format>
```

Pass 1 missed how the rubric actually works: **the prompt text is deliberately thin (4 rules); the operative rubric is the per-domain few-shot example block** (`eval/prompt/target_planning_eval_examples.py`, ~42 KB, six variables: `persuasion_examples`, `ambigious_instruction_examples`, `long_term_follow_up_examples`, `system_operation_examples`, `glasses_assistant_examples`, `recommendation_examples`). Each domain block contains 2 environments × 4–5 candidate targets, each with an integer score and a reason paragraph. The scoring logic is taught by those examples, not stated in rules. Representative example (verbatim, from `system_operation_examples`; the pattern is identical across domains):

> generated target 2: {"Target":"Provide SwiftUI List tutorial", "sub_targets":["Suggest official documentation", "Recommend tutorial videos"]}
> score: 3
> reason: First, the tutorial provided by generated target 2 does not emphasize brevity, and it ultimately recommends a video, which may not align with the user's needs or could impose a cognitive load on the user. Additionally, this sub-target directly suggests referring to the official documentation without first asking the user if they need assistance (as mentioned in the reference) or offering tailored advice based on the user's mistakes. Furthermore, the two sub-targets are overly broad in scope.

And the anchor at the top of the scale (same block): a candidate that "not only provides a tutorial but also guides users to correct their code… directly points out syntax errors… and utilizes resources from the page the user already has open" scores **10** with reason "Compared to the reference, Generated Target 1 … making the content more comprehensive" — confirming rule 2 in practice: 10 means *beats the reference*, not *matches it*. Distilled scoring behaviour from the examples (compressed synthesis of all six blocks): deduct for acting instead of clarifying in the ambiguous-instruction domain (direct execution targets score 4–5 vs clarification targets 7–9); deduct for generic/broad sub-targets, for recommending tools/videos instead of helping now, for assuming entities not in the trigger (e.g. assuming copied text is code, score 5), for missing the consent/ask-first step the reference contains, and for omitting emotional acknowledgement in persuasion (scores drop 7→5). Reasons must compare **action, specific entities, limited conditions** (rule 4).

Evaluator mechanics (`eval/target_planning_eval.py`): judge is `gpt-4o-2024-11-20` by default (`eval/config.yaml`: judge temperature 0.0, evaluated-model temperature 0.0, `max_workers: 10`); output per item `{environment, target, generated_target, sub_target, generated_sub_target, score, reason}`; domain score = mean of item scores. Target generation (`eval/target_generation.py`) retries up to `max_retries: 5` until a parseable target with non-empty `sub_targets` is returned.

## 3.3 Stage 2 — Dialogue Guidance: generation setup and full rubric

**Simulated conversation** (`eval/conversation_generation.py` + `eval/prompt/conversation_generation_prompt.py`):

- The evaluated model plays the assistant from `System_role_prompt` (verbatim core): "Act as a proactive assistant… You need to guide the user effectively to the target based on the trigger factor and user information… your message should be 1-2 short and succinct sentences." A `System_role_prompt_no_target` variant (no target/sub-target given) exists for the without-target ablation.
- The **judge model (GPT-4o) also plays the simulated user** from `human_role_prompt`, conditioned on an agreeableness persona (`collaboration_type`): **High** ("highly agreeable but still discerning… can politely decline if something truly conflicts with your values"), **Mid** ("cautiously agreeable… frequently raise questions and concerns"), **Low** ("You do not like being bothered by others' messages. You tend to approach external conversations with suspicion and distrust… You are very reactive and will not ask any questions to push the conversation forward."). The file retains a commented-out harsher Low draft ("You extremely dislike being bothered… treat others with an angry temper") that was softened before release — evidence the Low persona was tuned down.
- Every item is run under **all three** collaboration types. Conversation caps: `max_turns: 6`, sliding `window_size: 6` (each side keeps system prompt + last 6 messages). After every exchange, a termination judge (`Judge_conversation_prompt`) ends the dialogue iff "The target and all of the sub-targets of assistant have been achieved" **and** "The user have no question to ask"; it continues if any sub-target is unachieved or any user question is unanswered. A `human_role_prompt_rejected` variant lets the simulated user return `{"choice": "Reject", …}` and refuse to reply — present in the prompt file but the shipped `conversation_generation.py` uses the non-rejecting `human_role_prompt`.

**The complete Dialogue Guidance rubric** (`eval/prompt/conversation_eval_prompt.py`, verbatim — both strings, including the duplicated Input block, which is a bug in the source, reproduced as-is):

```python
Guidance_Acc_evaluation_prompt_short = """
<Task>
You need to evaluate the guidance ability in the conversation. "Guidance" refers to the model's capacity to lead the conversation, gradually engage the user in the dialogue, and guide the user to reach the conversation's target. You are required to assign a score from 1 to 10 to assess the conversation, with a higher score indicating better guidance ability by the assistant.
<Task>
"""
Guidance_Acc_evaluation_input_prompt = """
<Input>
You received user information: {user_information}
You received trigger factor: {trigger_factor}
You received target: {target}
You received sub-target: {sub_target}
You received conversation: {conversation}
</Input>
<Input>
You received user information: {user_information}
You received trigger factor: {trigger_factor}
You received target: {target}
You received sub-target: {sub_target}
You received conversation: {conversation}
</Input>
<Guideline>
You should evaluate the conversation based on the following criteria, and give a int score between 1 and 10.
If there are some criteria not met, you should deduct 2-4 (extremely bad) points each criteria.
1. Multi-turn Interaction and Goal Progression (Effectiveness): You should check the target completion and the turns number. The assistant should initiate the conversation to spark user interest and engage in multiple rounds of interaction, gradually achieving sub-goals to reach the overall target. Deduct points if the assistant fails to achieve the goal, delivers all information in a single message, or limits the interaction to one turn.
2. Personalized Guidance (Personalization): You should check whether the assistant's guidance is personalized. The assistant's guidance should be tailored to the user's specific information and context, rather than offering generic recommendations.
3. Proactive Tone (Tone): You should check the assistant's tone. The assistant should adopt an active tone to initiate and drive the conversation, avoiding passive phrases (e.g., "It sounds like…").
4. Concise and Engaging Messages (Engagement): You should check each assistant's message length. Messages should suit the conversational context, be clear and concise to avoid overwhelming the user (each message should no more than 2 sentences or 50 words).
5. Natural Online Messaging Format (Naturalness): You should check the assistant's message format. Messages should resemble typical online communication, avoiding any leakage of metadata (e.g., "target," "sub-target," "turn n," etc.).
If there are any other issues can be improved, you can also deduct realted points.
</Guideline>
<Format>
Just return a Json {{"thought":"(your compute process within 100 words)", "score": (score between 1 and 10)}}
</Format>
"""
```

Scoring arithmetic, stated exactly: start from 10, **deduct 2–4 points per unmet criterion** ("extremely bad" in the source's parenthetical), across the 5 named criteria, plus discretionary deductions for other issues; output `{"thought" (≤100 words), "score"}`. Evaluator mechanics (`eval/conversation_dialogue_eval.py`): `max_attempts: 2`, parse failure → score 0 with the error as thought; aggregates are mean guidance score and mean turns per domain, plus the same means grouped by collaboration type (High/Mid/Low), written to `metrics_summary.csv` and `collaboration_type_metrics_summary.csv`. There is **no few-shot example block for Stage 2** — unlike Stage 1, the rubric text alone carries the standard. Human-vs-LLM agreement material ships in `eval/Human_Evaluation/` (paired `*_by_human_eval.json` / `*_by_llm_eval.json` for both stages plus two calculator scripts), which pass 1 did not mention; it is the repo's only judge-bias mitigation.

## 3.4 What the two stages share (config contract)

`eval/config.yaml` (complete structure): `evaluated_model {api_key, base_url, model_name, temperature: 0.0}`, `judge_model {…, model_name: "gpt-4o-2024-11-20", temperature: 0.0}`, `task: "all"` (options `target_planning | dialogue_guidance | all`), `output_folder_name {target_planning, dialogue_guidance}`, `version_num: 1`, `max_workers: 10`. Both stages are OpenAI-API-format only; the same judge model plays user, termination judge, and both scorers in Stage 2's default configuration — a single-model circularity symmetric to ProactiveAgent's.

## 3.5 Dataset generation pipeline — prompts pass 1 summarised, extracted here

Three phases (`dataset_generation/`):

1. **Topic tree** (`prompt/topic_tree_construction_prompt.py`, verbatim core): "Generate {n} sub-topics for the parent topic ({topic}). Each sub-topic should represent an area where an AI assistant needs to proactively initiate a dialogue…" Rules: noun/noun-phrase; must need proactive dialogue; immediate next level only; must be usable as a parent for further breakdown; diverse, no repeated words. Human-AI iterative: a researcher selects/modifies topics round by round in the terminal (`topic_tree_generation.py`); shipped trees are one JSONL per domain under `dataset_generation/topic_tree/`, and each dataset item's `topic` field is its root-to-leaf path string.
2. **Environment + target generation** (`prompt/data_generation_prompt.py`): `environment_generation_prompt` returns one `{"user_information", "trigger_factor"}` JSON per call, few-shot from `dataset_generation/examples/environment_generation_examples.json`; `target_generation_prompt` (generation-side twin of §3.2, with per-domain `Domain_Specific_Contents` descriptions — e.g. for ambigious_instruction: "The target in this domain should be to proactively inquire details or give clarification about the ambiguous content in the user's instruction, rather than passively and directly providing answers"); `target_ensemble_prompt` synthesises multiple candidate targets into one best target, judged on four aspects (verbatim): "1. The alignment to the environment… 2. The completeness of the sub-targets… 3. The interactivity and user-friendly of the sub-targets… 4. The redundancy of the sub-targets: They should actionable and not import too much information to disturb user", with target <10 words, sub-targets 2–4.
3. **Refinement** (`prompt/data_refiement_prompt.py`): (a) `target_test_prompt` + `evaluation_test_prompt` — a checker model generates its own target for the environment and a judge decides whether it conveys "the similar meaning of ground truth target" (`{"reason", "judge": "True"/"False"}`), used to grade item difficulty; (b) **rewrite prompts** convert abstract descriptions into concrete, observable behaviour under strict rules (verbatim core): "Convert Abstract to Concrete… Exclude Internal States: Do not include descriptions of internal thoughts, feelings, psychological speculations… The rewrite output should not include any subjective words (e.g., try, however, notice, etc.)… Add Plausible Details", plus a per-domain rule table for both user_information and trigger_factor (e.g. glasses_assistant: frame "strictly from the perspective of a visual sensor"; long-term_follow_up trigger: "Condense and informalize a past conversation history"); (c) **noise prompts** embed the original sentences *in the middle* of 3–4 added sentences of plausible, related, non-essential detail so "the original key information [is] less conspicuous"; (d) `final_check_prompt` — a multi-model reasonableness gate: the checker must consider whether *other* targets could be triggered by the environment and return True only if the current target is "the **best target** for the current scenario". The fair/hard split corresponds to this refinement gradient (rewritten/noised items are the hard set).

## 3.6 Design invariants (ProactiveEval)

- Two scores, never one: a correct target badly guided and a wrong target beautifully guided are different failures with different cures; the stages are scored by different instruments (relative-to-reference few-shot judgement vs absolute 5-criterion deduction).
- Stage 1's standard lives in examples, Stage 2's lives in rules — the repo demonstrates both rubric technologies side by side.
- Stage 1's ceiling is *reference-relative*: 10 is reserved for beating the reference; matching it caps below 10 by construction of rules 2–3.
- Stage 2 prices *form* as heavily as outcome: message length (>2 sentences / >50 words), metadata leakage, and passive phrasing are each independently deductible.
- The simulated user's resistance is a controlled variable (3 agreeableness levels × every item), so guidance scores are interpretable per resistance level.
- Difficulty is manufactured, not found: rewrite-to-concrete + middle-embedded noise + best-target checking is the whole fair→hard mechanism.

## 3.7 Refined verdict

Pass 1 verdict stands (ADOPT-IDEA, rubric only; SKIP code — unlicensed, single-day push pattern confirmed) with two changes in emphasis. (1) Pass 1 understated Stage 1: "score against a reference target" hides that the transferable artifact is the **42 KB few-shot calibration set pattern** — a hand-scored example bank per domain — without which the 4-rule prompt will not reproduce the repo's scoring behaviour. A native adoption should budget for writing the example bank, not just copying the prompt. (2) Pass 1 did not extract Stage 2's deduction arithmetic (start 10, −2 to −4 per failed criterion) or its form constraints (≤2 sentences / ≤50 words, no metadata leakage, no passive openers); those are the cheapest directly reusable pieces in this dive for scoring any proactive message before it is sent. The reasoning-models-degrade finding remains as pass 1 reported it; this pass adds that the finding rests on a single judge model that also plays the user, so it should be read as "under GPT-4o-as-user-and-judge", a caveat the repo's own Human_Evaluation folder partially offsets for scoring but not for user simulation.

---

# 4. Cross-source synthesis: the rebuildable gate (all three sources composed)

The three artifacts compose into one buildable design, each supplying what the others lack:

1. **Scorer (from the pilot, §1):** offline replay over logged timelines with MUST/MAY/MUST-NOT windows (b 4/2, c 4/1), single-credit benefit, per-fire cost, λ-swept reporting on λ ∈ {0.25, 0.5, 1, 2, 4}. Decides *whether a policy deserves to exist* at a stated interruption price.
2. **Gate (from ProactiveAgent, §2):** at fire time, a separate judge pass over (observations, proposed task-or-null) returning first-person `{thought, judgement}`; rejection feeds the thought back for a bounded number of *different* retries (pick one budget; the repo uses 3 live); exhaustion = silence; null is judged by the same gate. Gate quality comes from a labelled set built by majority vote with unanimity-preferred test rows, distilled by label-conditioned rationalisation + 5-sample consistency filtering — not from rubric prose.
3. **Quality rubric (from ProactiveEval, §3):** for interventions that pass the gate, score target correctness first (reference-relative, few-shot calibrated, 1–10, 10 = beats reference) and delivery second (start 10, −2…−4 per failed criterion: goal progression, personalisation, proactive tone, ≤2 sentences/≤50 words, no metadata leakage). Score per user-resistance level where simulation is used.
4. **Feedback adaptation (from the awesome README, §1.5):** log accept / dismiss / snooze as L0 events against (context, intervention); adapt per-context θ bandit-style (maturity level 2) before attempting any learned policy (level 3); treat "user disabled proactivity" as the ultimate negative reward (L3).

Known seams, stated plainly: the pilot's θ is never operationalised in code (PRISM, cited in the list, is the nearest published gate: calibrated P(accept) vs asymmetric-cost threshold); both learned-judge systems are circular at eval time (judge = data filter = scorer), anchored only by small human-labelled sets (120 rows; the Human_Evaluation pairs); both benchmarks' headline numbers are therefore agreement rates, and any native rebuild should keep a human-scored holdout the gate never trains on.

## 5. What pass 1 missed or understated — consolidated

1. The pilot implements a **scorer, not a θ gate**; no θ, no expectation, no threshold exists in `pilot.py` (§1.1).
2. Pilot mechanics pass 1 omitted: benefit single-credit per window, MUST-over-MAY precedence, violation charged even on benefit-earning fires, misses priced only via recall, count-matched random control, per-policy fresh RNG, MUST windows averaging 3.3 s (§1.2, §1.4).
3. ProactiveAgent's three-signal feedback policy is **one prompt sentence**, not code (§2.1); the reward gate is env-flag optional (§2.3).
4. The reward rubric is three rules; gate quality is a **fine-tuning + rationalisation pipeline** result, with an explicit balancing rule (upsample to max/5) and a 5-sample consistency filter (§2.4, §2.5).
5. Benchmark sizes conflated in pass 1's sources: 6,790 events (corpus) vs 227 (agent test set) vs 120 (reward test set, unanimity-preferred, balanced 30×4); False-Alarm is *defined* as FP/(TP+FP) = 1 − precision; shipped splits contain no daily-life split (§2.7).
6. Three internal drifts: `Proactive Task` vs `Proactive_Task`, CR vs NR naming, retry budget 3 vs 15 (§2.2, §2.5, §2.3).
7. ProactiveEval's Stage 1 rubric is **few-shot-carried** (42 KB example bank); its prompts alone do not reproduce its scores (§3.2). Stage 2's deduction arithmetic and form constraints were unextracted (§3.3). The fair/hard split is a manufactured refinement gradient (§3.1, §3.5), and a Human_Evaluation folder exists as partial judge-bias mitigation (§3.3).

## 6. Coverage ledger

Read in full: awesome `README.md`, `pilot/pilot.py`, `pilot/README.md`, `pilot/results.txt`; ProactiveAgent files listed in §2 preamble, both reward `.jsonl` files (counts + schema + samples), `splits.json`; ProactiveEval files listed in §3 preamble, all 18 dataset files (parsed for counts; 1 item reproduced). Compressed with note: ProactiveAgent `agent/components.py` (sensing plumbing; structure only — not gate-relevant), `scenes.yaml`/`seedtask.yaml` (structure + samples; bulk is fixture event lists), ProactiveEval few-shot bank (representative examples verbatim per domain pattern; the bank is repetitive by design), Human_Evaluation JSONs (sampled, not aggregated — no agreement coefficient is computed in the repo files read, and none is claimed here). Unreachable / absent, logged not dropped: PRISM, YETI, temporal-graph trigger, HoloAssist-as-repo (dataset download linked by the pilot, 117 MB, not fetched — the pilot's checked-in `results.txt` stands as its output record); ProactiveEval has no licence file; ProactiveAgent's Hugging Face model weights were not inspected (out of scope: no execution, weights are not text artifacts). No repo code was installed or executed at any point.

## 7. Verdicts, refined

- **tao-hpu/awesome-proactive-agents + pilot: ADOPT-IDEA (unchanged, sharpened).** Adopt the scorer shape and price table verbatim; treat θ as a build task, with PRISM's formulation as the reference gate.
- **thunlp/ProactiveAgent: ADOPT-IDEA (unchanged, sharpened).** The transferable core is the labelling → rationalisation → consistency-filter → fine-tuned-judge pipeline and the judged-null pattern; the prompt templates alone transfer at general-model quality (~0.67 F1), which the repo's own table proves.
- **liutj9/ProactiveEval: ADOPT-IDEA, rubric only (unchanged, deepened).** Adopt both rubrics *with* their carriers: Stage 1 requires a per-domain hand-scored example bank; Stage 2 transfers as-is, deduction arithmetic included. Code remains SKIP (unlicensed, unmaintained).
