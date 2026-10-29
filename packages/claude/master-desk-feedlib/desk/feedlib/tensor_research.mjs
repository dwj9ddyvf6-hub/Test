// tensor_research.mjs — batch runner for the Tensor research plane (desk/feedlib/tensor_research.py).
//
// Every value is computed by vendored source code, never a reimplementation:
//   engine     the desk's pinned production Tensor engine v698 (desk/vendor/old_desk_research/tensor_exact, hash-checked
//              by desk/feedlib/tensor.py before every batch): parseYahooReplicaHistory (the production Yahoo parse,
//              forming-bar inference included) and buildAnnaReplica
//   sidecar    FolioTend v619's research sidecar (genomes / phenotypes), the TypeScript file itself
//              (desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts, type-stripped by node)
//   swing615   FolioTend v615's 1H Swing signal + its notification event key (desk/vendor/foliotend_research/v615/lib)
//   swing698   the v698 1H Swing signal with its Swing Transition subtype, on the replica decorated by the production
//              native structural engine (app/lib/vector-structure.ts decorateVectorReplica + vector-engine.ts
//              analyzeVectorBars, v698 production snapshot)
//
// stdin  {jobs: [{symbol, interval: "1h"|"1d"|"1wk", payload?: <raw Yahoo chart JSON>, now?: epoch s,
//                 bars?: [{t,o,h,l,c,v}], views: [{name, window?: n, tail, sidecar?, swing615?, swing698?,
//                 decorate?: "never"|"always"|"on_confirmed"|"on_marker:<marker>", input?: bool}]}]}
//        (input: also return the view's input bars as [t, o, h, l, c, v] rows)
// stdout {ok, engineVersion, results: [{symbol, interval, ok, error?, parsed, lastT, latestBarOpen,
//                                       views: {name: {bars: [row...]}}}]}
import { ANNA_REPLICA_VERSION, buildAnnaReplica, parseYahooReplicaHistory } from "../vendor/old_desk_research/tensor_exact/lib/anna-replica.mjs";
import { tensorChartDisplayBars } from "../vendor/old_desk_research/tensor_exact/lib/tensor-chart-window.mjs";
import { buildTensorEnrichmentSignals } from "../vendor/old_desk_research/tensor_exact/lib/tensor-enrichment-signals.mjs";
import { buildTensorSwingSignal as swing698 } from "../vendor/old_desk_research/tensor_exact/lib/tensor-swing-signals.mjs";
import { buildTensorSwingSignal as swing615 } from "../vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs";
import { buildTensorSwingNotification as notice615 } from "../vendor/foliotend_research/v615/lib/tensor-swing-notification.mjs";

const LABEL = { "1wk": "one-week", "1d": "one-day", "1h": "one-hour" };
const FIELDS = ["timestamp", "barFinality", "open", "high", "low", "close", "volume", "primaryMarkers", "warningMarker",
  "dcbMarker", "weakMarker", "ema8", "ema13", "ema21", "ema34", "ema48", "ema200", "emaRibbon", "ribbonOrder",
  "ribbonSlope", "dotRsiMedium", "macdHistogram", "rvol", "adx", "plusDi", "minusDi", "squeezeOn", "bullishVotes",
  "bearishVotes", "totalVotes", "fastState", "slowState", "activeCall", "callLifecycle", "candleRegime", "bbUpper",
  "bbLower"];
let sidecarModule = null;
let structureModules = null;

async function sidecar() {
  sidecarModule ??= await import("../vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts");
  return sidecarModule;
}

async function structure() {
  if (!structureModules) {
    const [vs, ve, va] = await Promise.all([
      import("../vendor/old_desk_research/tensor_exact/app/lib/vector-structure.ts"),
      import("../vendor/old_desk_research/tensor_exact/app/lib/vector-engine.ts"),
      import("../vendor/old_desk_research/tensor_exact/app/lib/vector-replica-adapter.ts"),
    ]);
    structureModules = { vs, ve, va };
  }
  return structureModules;
}

// the production chart path (app/api/vector-chart/route.ts buildVectorChartReplicaFromCanonicalHistory): the native
// analysis over the calculation history, then decorateVectorReplica (gestalt not needed for bar-level locations)
async function decorate(replica, history, interval) {
  const { vs, ve, va } = await structure();
  const minimumBars = va.vectorReplicaMinimumBars(interval);
  const analysis = ve.analyzeVectorBars(history.bars.map((b) => ({ time: b.timestamp, open: b.open, high: b.high,
    low: b.low, close: b.close, volume: b.volume })), { minimumBars, requireEma200: minimumBars >= 200 });
  return vs.decorateVectorReplica(replica, history, analysis, { includeGestalt: false });
}

function slim(context) {
  if (!context) return null;
  const cycle = context.cycle || null;
  return { status: context.status ?? null, cycle: cycle ? { state: cycle.state ?? null, direction: cycle.direction ?? null,
    momentum: cycle.momentum ?? null, momentumAgreement: cycle.momentumAgreement ?? null, ageBars: cycle.ageBars ?? null,
    slowK: cycle.slowK ?? null, slowD: cycle.slowD ?? null } : null, primaryPattern: context.primaryPattern ?? null,
    higherTimeframe: context.higherTimeframe ?? null };
}

function location(value) {
  if (!value) return null;
  const zone = (z) => (z ? { low: z.low ?? null, high: z.high ?? null, strength: z.strength ?? null } : null);
  return { trigger: value.trigger ?? null, bias: value.bias ?? null, label: value.label ?? null, atr: value.atr ?? null,
    roomToSupplyAtr: value.roomToSupplyAtr ?? null, roomToDemandAtr: value.roomToDemandAtr ?? null,
    nearestDemand: zone(value.nearestDemand), nearestSupply: zone(value.nearestSupply),
    actionSignal: value.actionSignal ?? null };
}

function swingSummary(sig) {
  if (!sig) return null;
  return { setup: !!sig.setup, confirmed: !!sig.confirmed, confirmationAgeBars: sig.confirmationAgeBars ?? null,
    phenotype: sig.phenotype ?? null, confidence: sig.confidence ?? null, score: sig.score ?? null,
    target: sig.target ?? null, invalidation: sig.invalidation ?? null, bearishConflict: sig.bearishConflict ?? null,
    factors: sig.factors || [], setupBarTimestamp: sig.setupBarTimestamp ?? null,
    confirmationBarTimestamp: sig.confirmationBarTimestamp ?? null };
}

// the rejection-memory lane's extractor (quant-research-critical tensor_rejection_memory_v1 extract_tensor_features.mjs,
// its frozen recipe on this engine): full-history replica, native analysis (minimumBars 100 on 1d, EMA200 not
// required), the native per-bar location / ATR attached as the swing's structural location, the Swing per bar; the
// projected scalar columns native.py hands to the frozen acceptance module
async function nativeFull(history, symbol, interval) {
  const { ve } = await structure();
  const bars = history.bars;
  const replica = buildAnnaReplica({ ...history, displayBars: bars.length }, { latestOnly: false });
  if (!replica || replica.bars.length !== bars.length) throw new Error("full history extraction failed");
  const minimumBars = interval === "1wk" ? 60 : interval === "1d" ? 100 : 200;
  const analysis = ve.analyzeVectorBars(bars.map((b) => ({ ...b, time: b.timestamp })),
    { minimumBars, requireEma200: interval !== "1d" && interval !== "1wk" });
  const nativeByTime = new Map((analysis?.bars || []).map((b) => [b.time, b]));
  const studyBars = replica.bars.map((b) => {
    const n = nativeByTime.get(b.timestamp);
    return n ? { ...b, vectorStructuralLocation: { trigger: n.locationTrigger, atr: n.atr, trend: n.families.trend,
      momentum: n.families.momentum, participation: n.families.participation,
      volatilityReadiness: n.families.volatilityReadiness } } : b;
  });
  return studyBars.map((b, index) => {
    const n = nativeByTime.get(b.timestamp);
    const ribbon = Array.isArray(b.emaRibbon) ? b.emaRibbon : [];
    const markers = b.primaryMarkers || [];
    return [b.timestamp, b.close, b.high, b.ema48 ?? null, b.ema200 ?? null, ribbon[4] ?? null, ribbon[5] ?? null,
      ribbon[6] ?? null, ribbon[7] ?? null, n ? n.atr ?? null : null, markers.includes("buy-green"),
      markers.includes("buy-cyan"), !!swing698({ bars: studyBars, index, symbol }).confirmed, b.barFinality];
  });
}

// the Sable desk's completed-bar Tensor read (autopilot-desk src/lib/tensor/bridge.ts interpret over
// analyzeVectorReplicaBars(signalOnly)), analysed on the job's own interval: the source read completed five-minute
// bars; the desk reads the canonical one-hour series (the owner's 1H decision, 2026-10-18)
async function vectorRead(history, symbol, interval) {
  const { va } = await structure();
  const analysis = va.analyzeVectorReplicaBars({ symbol, interval, bars: history.bars.map((b) => ({ time: b.timestamp,
    open: b.open, high: b.high, low: b.low, close: b.close, volume: b.volume })), signalOnly: true });
  const c = analysis?.current || null;
  return { status: analysis?.status ?? "unavailable", modelVersion: analysis?.modelVersion ?? null,
    current: c ? { state: c.state ?? null, primaryMarkers: Array.isArray(c.primaryMarkers) ? c.primaryMarkers : [],
      goldDiamond: c.goldDiamond ? { qualifies: c.goldDiamond.qualifies === true, baseGreen: c.goldDiamond.baseGreen === true } : null,
      time: c.time ?? null, close: c.close ?? null } : null };
}

async function view(history, spec, symbol, interval) {
  if (spec.nativeFull) return { native: await nativeFull(history, symbol, interval) };
  if (spec.vectorRead) return { read: await vectorRead(history, symbol, interval) };
  const bars = spec.window ? history.bars.slice(-spec.window) : history.bars;
  const h = { ...history, bars, displayBars: tensorChartDisplayBars(bars.length, interval) };
  let replica = buildAnnaReplica(h, { latestOnly: false });
  if (!replica) throw new Error(`buildAnnaReplica returned null (${bars.length} bars)`);
  const tail = Math.max(1, Math.min(replica.bars.length, Math.floor(Number(spec.tail) || 1)));
  const start = replica.bars.length - tail;
  let side = null;
  if (spec.sidecar) side = (await sidecar()).calculateFolioTendSidecars(replica);
  // decoration (the production native structural location) when the view asks for it: always, when a Swing
  // confirms in the tail, or when the newest bar carries a given primary marker
  const mode = String(spec.decorate || "never");
  let decorated = false;
  let want = mode === "always";
  if (mode === "on_confirmed") {
    for (let i = start; i < replica.bars.length && !want; i += 1) {
      if (spec.swing615 && swing615({ bars: replica.bars, index: i, symbol, registry: {} }).confirmed) want = true;
      else if (spec.swing698 && swing698({ bars: replica.bars, index: i, symbol }).confirmed) want = true;
    }
  } else if (mode.startsWith("on_marker:")) {
    const last = replica.bars[replica.bars.length - 1];
    want = last?.barFinality === "closed" && (last.primaryMarkers || []).includes(mode.slice(10));
  }
  if (want) {
    replica = await decorate(replica, h, interval);
    decorated = true;
  }
  let s615 = null;
  if (spec.swing615) {
    s615 = [];
    for (let i = start; i < replica.bars.length; i += 1) {
      const sig = swing615({ bars: replica.bars, index: i, symbol, registry: {} });
      const note = sig.confirmed ? notice615({ symbol, signal: sig }) : null;
      s615.push({ ...swingSummary(sig), eventKey: note?.eventKey ?? null });
    }
  }
  let s698 = null;
  if (spec.swing698) {
    s698 = [];
    for (let i = start; i < replica.bars.length; i += 1) {
      const sig = swing698({ bars: replica.bars, index: i, symbol });
      const tr = sig.transition || {};
      s698.push({ ...swingSummary(sig), transition: { version: tr.version ?? null, qualifies: !!tr.qualifies,
        eligible: !!tr.eligible, basketTier: tr.basketTier ?? null, factors: tr.factors || [],
        confirmationBarTimestamp: tr.confirmationBarTimestamp ?? null } });
    }
  }
  const rows = [];
  for (let i = start; i < replica.bars.length; i += 1) {
    const bar = replica.bars[i];
    const row = {};
    for (const f of FIELDS) row[f] = bar[f] === undefined ? null : bar[f];
    row.tensorContext = slim(bar.tensorContext);
    if (decorated) row.vectorStructuralLocation = location(bar.vectorStructuralLocation);
    let ids = [];
    try { ids = buildTensorEnrichmentSignals(bar).signals.map((s) => s.id); } catch { ids = []; }
    row.enrichmentIds = ids;
    if (side) {
      const p = side[i]?.payload;
      row.sidecar = p ? { phenotypes: p.phenotypes.map((x) => x.id), genomes: p.genomes.map((x) => ({ id: x.id, score: x.score })) } : null;
    }
    if (s615) row.swing615 = s615[i - start];
    if (s698) row.swing698 = s698[i - start];
    rows.push(row);
  }
  const out = { bars: rows, decorated, replicaBars: replica.bars.length };
  if (spec.input) out.input = bars.map((b) => [b.timestamp, b.open, b.high, b.low, b.close, b.volume]);
  return out;
}

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const request = JSON.parse(Buffer.concat(chunks).toString("utf8"));
const results = [];
for (const job of request.jobs || []) {
  const symbol = String(job.symbol || "").toUpperCase();
  const interval = String(job.interval || "1d");
  try {
    let history;
    if (job.payload) {
      const now = Math.floor(Number(job.now) || Date.now() / 1000);
      history = parseYahooReplicaHistory(job.payload, symbol, interval, now);
      if (!history) throw new Error("the production Yahoo parse rejected the payload");
      history.symbol = symbol;
      if (history.latestBarOpen) {                       // completed bars only: the forming bar never enters
        history = { ...history, bars: history.bars.slice(0, -1), latestBarOpen: false };
      }
    } else {
      history = { symbol, currency: "USD", exchange: null, timezone: "America/New_York", interval,
        intervalLabel: LABEL[interval] || interval, latestBarOpen: false,
        bars: (job.bars || []).map((b) => ({ timestamp: Math.floor(Number(b.t)), open: Number(b.o), high: Number(b.h),
          low: Number(b.l), close: Number(b.c), volume: b.v == null ? 0 : Number(b.v) })) };
    }
    const views = {};
    for (const spec of job.views || [{ name: "all", tail: 1 }]) {
      try {
        views[spec.name] = await view(history, spec, symbol, interval);
      } catch (err) {
        views[spec.name] = { error: String(err && err.message || err) };
      }
    }
    results.push({ symbol, interval, ok: true, parsed: history.bars.length,
      lastT: history.bars.length ? history.bars[history.bars.length - 1].timestamp : null, views });
  } catch (err) {
    results.push({ symbol, interval, ok: false, error: String(err && err.message || err) });
  }
}
process.stdout.write(JSON.stringify({ ok: true, engineVersion: ANNA_REPLICA_VERSION, results }) + "\n");
