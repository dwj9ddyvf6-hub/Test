# Executable Tensor source adapter

`backend/tensor_engine.py` exposes `NativeBar`, `TensorFeature`,
`TensorSnapshot`, `TensorFeatureHistory`, `extract_tensor_features()` and
`extract_native_feature_rows()` and `extract_state_feature_rows()`. It reads a
full, caller-supplied completed OHLCV prefix and runs a pinned transport with
Node.js. It requests no market
data and submits no orders. Node 24 is used by the finite integration checks;
the adapter needs an available Node runtime and no npm dependencies.

`SOURCE_MANIFEST.json` now binds 26 source files: the 20-module frozen v690
closure, the exact instrumented helper derivative, two exact R11 wrappers,
the exact 93-column R11 exporter, and two new transports. The 24 scientific files
are byte-identical to sealed R11. The manifest itself is pinned by
`SOURCE_MANIFEST_SHA256` in the Python adapter; every dependency is verified
before execution. This establishes parity to the reconstructed v690 engine.
Identity with private original Anna source remains **not established**.

Clocks are positive integer UTC milliseconds in `NativeBar`. Bar starts must
be whole-second aligned. Completion must follow the bar start, and the
first-seen availability clock must satisfy `completed_at_ms <= usable_at_ms
<= as_of_ms`. Calendar aggregation, session completeness, source revisions,
canonical history origin and actual receipt timestamps belong to the caller.
The adapter retains the exact millisecond clocks in the snapshot. The exact
R11 exporter requires integer seconds, so its completion and availability
transport clocks round **up** to seconds; no fractional receipt is backdated.
This rounding changes transport metadata only, with exact millisecond
availability governing admissibility and order decisions. The caller may
supply `executable_at_ms` for the observed period open before completion;
the adapter never infers an exchange-calendar open.

The compact snapshot holds all seven signed channels in this fixed order:
`stoch, aroon, di, obv, squeeze, pivot, wave`, for the final four bars. A
channel is `+1`, `-1`, or unavailable (`None`); counts reconcile exactly.
`balance = bullish_votes - bearish_votes`. `increasing_vote_count` counts
channels with any adjacent numeric increase over those four bars; a null
comparison contributes no increase. This preserves the actual research rule,
including increases followed by reversals, rather than substituting an
endpoint comparison. Native readiness (35 bars, or 4 weekly bars) is
separate from financial readiness (`bar_index >= 233`, at least 234 bars).
Zero-volume bars are preserved as allowed by the frozen engine; negative
volume is invalid. The 20-bar dollar-volume mean includes the current
completed bar, exactly as in R11.

The full-history API returns all 93 exact exporter fields and ordinals from
zero at the supplied origin. There is no rolling-window truncation or hidden
origin reset. Frozen daily-model inference must separately require its bound
canonical origin and symbol phase. The caller receives a source-manifest
hash, canonical request hash, history origin and bar denominator in every
snapshot. Full and compact extraction bind the same canonical input hash.

Hourly and weekly STATE_REPAIR execution uses `extract_state_feature_rows()`.
It passes the entire canonical prefix to the unchanged `runTensorInternals()`
once, retains all seven signed vote channels and reconciled counts, and uses
the exact frozen ATR14 and OBV slope5 helper arrays. DV20 keeps the original
left-to-right 20-bar summation order. The short-history warming fallback uses
the identical frozen helpers and publishes no votes. This path omits unrelated
93-field exporter work, including its hourly swing and transition calculations;
it does not truncate history, rewrite a source formula, approximate a state,
or alter financial rules. Daily model extraction still uses the unchanged
93-column exporter.

State rows retain 26 original exporter columns plus seven audit fields:
`bar_id`, exact millisecond start/completion/availability clocks, the optional
observed executable-open clock, millisecond source origin, and reconciled vote
balance. Python authenticates every row's source OHLCV, clocks, ordinal,
readiness, signed votes, counts and finite measurements. Its final four states
must exactly equal the separately validated compact snapshot. State, full and
compact extraction produce the same canonical input hash for the same history.

Up to eight exclusive reusable Node workers amortize startup and JIT overhead.
Each request still recalculates the complete input prefix; workers do not cache
bars, source histories, signals or financial decisions. Every call verifies the
pinned manifest and full source closure before acquiring a worker. The
line-framed protocol has a bounded result size and one deadline covering worker
queueing, stdin transport and native response. Timeouts, broken workers and bad
framing discard the worker and fail closed; subsequent valid requests can use a
new worker. Worker processes terminate when their owning Python process exits.
No extra npm package is needed.

Malformed candles, future availability, invalid clocks, source mismatch,
missing Node, process failure, timeout and malformed results raise
`TensorEngineError`. A caller must abstain when this exception is raised.
The adapter never fabricates missing prices or a usable signal.

Finite fixtures contain actual archived AMD OHLCV and completion clocks:
330 hourly bars, 330 weekly bars and one full 2,513-bar daily history. The
source transport was the retained V1 replay file; **all V1 indicator fields
were discarded**. The reference fixture was calculated independently by the
sealed original V2 exporter for the first 330 bars in each frame. Fixture
provenance and hashes are in `fixtures/PROVENANCE.json`. Availability here
is the historical calendar-close proxy, not authenticated vendor receipt.
These fixtures check numerical and causal parity; they do not constitute a
new performance test.

Run the meaningful checks with:

```bash
python -m unittest tests.test_tensor_engine -v
python -m unittest tests.test_tensor_engine_state_fast -v
```

They compare every field to the original exporter, compare multiple complete
prefixes, wildly perturb later prices and volume, independently calculate
ATR/OBV slope/dollar volume, and exercise the failure and source-integrity
paths on isolated copies. Original R11 research files are never modified.

The fast-state checks compare every retained column over all real hourly and
weekly fixture rows, all readiness boundaries, complete prefixes and wildly
perturbed later bars; test first-seen millisecond clocks, concurrent mixed-frame
requests, worker timeout/recovery and deliberately inconsistent output; and,
when the restored cache is installed, compare every row of AMD's full
3,478-bar hourly history and its entire greedy opportunity clock. Timing
receipts measure operational throughput rather than trading profitability.
