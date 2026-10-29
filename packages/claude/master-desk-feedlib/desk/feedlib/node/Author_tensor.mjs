// Runs the Author desk's vendored Tensor stack (desk/vendor/Author_mon/src/lib, byte-exact, sha-pinned in
// desk/vendor/MANIFEST.json) unchanged, through its own entry points: analyzeSymbol(symbol, interval) (adapter.ts,
// with its 1d horizon frame) and, on the analysis' own admitted signal tape (adapter.ts frameBars), the Tensor 2
// replica (engine.ts buildTensorReplica). The frame is the request's `interval`: "1h" (the desk's, the owner's 1H
// decision 2026-10-18) or "5m" (the watch desk's default). On the 5m frame only — as the source runs them — the
// Green engine's events (green/engine.ts scanGreen + attachContext + eventFromFrame, gold.ts on GREEN prints:
// adapter.ts analyzeBars runs the engine on 5m alone) and readTensor0(symbol) (tensor0/read.ts reads 5m bars on a 5m
// clock).
// Only I/O is supplied: fetch serves the request's Yahoo chart results (the desk's tapes in the chart API's shape)
// and Date reads the pass clock.
//
// The location printer (anna-printer.ts) has no caller at this commit; it is composed here exactly as the source's
// own replica composed it (Author-desk-backup@3e93f984 src/lib/tensor/anna-replica.ts:214-319): consecutive closes
// above EMA200, the available bullish vote count, the bar's marker, applyPrinter written back before the next bar.
//
// The GREEN study (workdesk/green-study-io.ts, unchanged; on the 5m frame only) runs on its own I/O layer: its
// /workspace/ files live in the directory `study.workspace` names (workspace_fs.mjs serves node:fs/promises to that
// module only). On each pass a GREEN print on the newest completed 5m bar is snapshotted with recordGreenPrint and
// the next bar of a trial with maybeRecordGreenControl (the IO module's own entry points; the source left them
// unwired and backfilled
// from its timing tape); mode "study_eod" runs runGreenStudy(dateEt) — forward marks on the 1m tapes served for the
// day's names, SPY and their benches, controls, the report and Friday's week lock — as desk-autopilot.mjs did after
// 16:08 ET.
//
// stdin:  {"now": ms, "mode": "pass" | "study_eod", "interval": "1h" | "5m" (default "5m"),
//          "study": {"workspace": dir} | null,
//          "requests": [{"symbol", "charts": {"60m" | "5m": chartResult, "1d": chartResult}}],
//          "eod": {"dateEt", "charts": {symbol: chartResult (1m)}}}
// stdout: {"ok": true, "results": [{ok, symbol, ...}]} | {"ok": true, "study": {...}}
import { register } from "node:module";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const vendor = path.resolve(here, "..", "..", "vendor", "Author_mon");
register("./ts_resolve.mjs", import.meta.url, {
  data: {
    alias: { "@/": pathToFileURL(path.join(vendor, "src") + "/").href },
    redirect: [{ parent: "src/lib/workdesk/green-study-io.ts", specifier: "node:fs/promises", url: pathToFileURL(path.join(here, "workspace_fs.mjs")).href }],
  },
});

const RealDate = Date;
let NOW = RealDate.now();
class PassDate extends RealDate {
  constructor(...a) {
    if (a.length === 0) super(NOW);
    else super(...a);
  }
  static now() {
    return NOW;
  }
}
globalThis.Date = PassDate;

let CHARTS = {};
globalThis.fetch = async (url) => {
  const u = new URL(String(url));
  const sym = decodeURIComponent(u.pathname.split("/").pop());
  const r = CHARTS[`${sym}|${u.searchParams.get("interval")}`];
  if (!r) return new Response(JSON.stringify({ chart: { result: null, error: { description: "no tape served" } } }), { status: 404 });
  return new Response(JSON.stringify({ chart: { result: [r], error: null } }), { status: 200, headers: { "content-type": "application/json" } });
};

const lib = (p) => import(pathToFileURL(path.join(vendor, "src", "lib", p)).href);

function row(r) {
  if (!r) return null;
  return {
    t: r.bar.t, c: r.bar.c, marker: r.marker ?? null, signal: r.signal ?? null, location: r.location ?? null,
    regime: r.regime ?? null, glyphs: r.glyphs ?? [], bullShare: r.bullShare ?? null, resultant: r.resultant ?? null,
    coherence: r.coherence ?? null, utDir: r.utDir ?? null, ema200: r.ema200 ?? null,
  };
}

function lastWhere(xs, pred) {
  for (let i = xs.length - 1; i >= 0; i--) if (pred(xs[i], i)) return i;
  return -1;
}

const out = [];
try {
  const adapter = await lib("tensor/adapter.ts");
  const bars = await lib("tensor/bars.ts");
  const yahoo = await lib("tensor/yahoo.ts");
  const green = await lib("tensor/green/engine.ts");
  const engine = await lib("tensor/engine.ts");
  const printer = await lib("tensor/anna-printer.ts");
  const t0 = await lib("tensor0/read.ts");
  const inferred = await lib("tensor/inferred-weights.ts");
  const session = await lib("tensor/session.ts");
  const input = JSON.parse(readFileSync(0, "utf8"));
  NOW = Number(input.now) || RealDate.now();
  const IV = input.interval === "1h" ? "1h" : "5m";
  let io = null;
  if (input.study && input.study.workspace) {
    globalThis.__Author_WORKSPACE__ = input.study.workspace;
    io = await lib("workdesk/green-study-io.ts");
  }
  let studyEod = null;
  if (input.mode === "study_eod") {
    CHARTS = {};
    for (const [sym, res] of Object.entries((input.eod && input.eod.charts) || {})) CHARTS[`${sym}|1m`] = res;
    studyEod = await io.runGreenStudy(input.eod.dateEt);
  }
  const et = session.etParts(NOW);
  for (const req of studyEod ? [] : input.requests || []) {
    try {
      CHARTS = {};
      for (const [iv, res] of Object.entries(req.charts || {})) CHARTS[`${req.symbol}|${iv}`] = res;
      const a = await adapter.analyzeSymbol(req.symbol, IV);
      if (a.status === "UNAVAILABLE") {
        out.push({ ok: true, symbol: req.symbol, status: a.status, warnings: a.warnings });
        continue;
      }
      // the analysis' own signal tape (adapter.ts frameBars: the pre + regular session on 5m, regular on 1h)
      const pack = await yahoo.loadYahooBars(req.symbol, IV);
      const admitted = bars.admitBars(pack.bars, IV, NOW);
      const frame = IV === "5m" ? bars.keepSignalTape(admitted) : bars.keepRegular(admitted);
      // Green engine events on that tape (5m only)
      const frames = IV === "5m" ? green.attachContext(green.scanGreen(frame), frame) : [];
      const gi = lastWhere(frames, (f) => f.greenBuy || f.cyanBuy || f.redSell || f.magentaSell);
      const gev = gi >= 0 ? green.eventFromFrame(req.symbol, frames[gi], false, NOW, frame) : null;
      const bi = lastWhere(frames, (f) => f.greenBuy);
      const gold = bi >= 0 ? green.eventFromFrame(req.symbol, frames[bi], false, NOW, frame) : null;
      const glast = frames.length ? frames[frames.length - 1] : null;
      // Tensor 2 replica (engine.ts) and the location printer composed over it
      const rep = engine.buildTensorReplica(frame);
      let daysAbove = 0;
      let prevAbove = false;
      const printed = rep.map((r) => ({ ...r }));
      const snaps = [];
      for (let i = 1; i < printed.length; i++) {
        const r = printed[i];
        const available = r.votes.filter((v) => v.available);
        const bull = available.filter((v) => v.value === 1).length;
        const aboveNow = r.ema200 != null && r.bar.c > r.ema200;
        daysAbove = aboveNow ? daysAbove + 1 : 0;
        const before = r.marker ?? null;
        const snap = printer.classifyLocation(printed, i, daysAbove, prevAbove, bull, before);
        prevAbove = aboveNow;
        r.marker = printer.applyPrinter(before, snap);
        snaps.push({ i, t: r.bar.t, before, after: r.marker, snap });
      }
      const ti = lastWhere(rep, (r) => r.marker != null);
      const pLast = snaps.length ? snaps[snaps.length - 1] : null;
      // Tensor 0 on the provider tape (tensor0/read.ts; 5m only)
      const z = IV === "5m" ? await t0.readTensor0(req.symbol) : null;
      const zi = z ? lastWhere(z.frames, (f) => f.event != null) : -1;
      // inferred entry quality on this read's own process lines and code
      const lines = [a.eventLabel, a.locationLabel, a.gestaltSummary, ...(a.current?.glyphs ?? [])].filter(Boolean);
      const code = a.status;
      const ev = inferred.evidenceFromProcess(lines, code);
      // the GREEN study's live snapshots (green-study-io.ts recordGreenPrint / maybeRecordGreenControl)
      let study = null;
      if (io && IV === "5m") {
        const args = { analysis: a, dateEt: et.ymd, hour: et.hour, minute: et.minute, member: null };
        if (a.current?.marker === "GREEN_BUY") {
          const g = await io.recordGreenPrint(args);
          study = g ? { recorded: g.id, role: g.role, sleeves: g.sleeves, barAt: g.barAt } : null;
        } else {
          const c = await io.maybeRecordGreenControl(args);
          study = c ? { control: c.id, parentId: c.parentId, barAt: c.barAt } : null;
        }
      }
      out.push({
        ok: true,
        symbol: req.symbol,
        status: a.status,
        completedBarAt: a.completedBarAt,
        barCount: a.barCount,
        close: a.current?.bar?.c ?? null,
        qualified: a.qualified,
        vetoed: a.vetoed,
        vetoReason: a.vetoReason,
        epoch: a.epoch,
        eventLabel: a.eventLabel,
        locationLabel: a.locationLabel,
        current: row(a.current),
        context: a.current?.tensorContext ?? null,
        native: a.native,
        causalEvents: a.causalEvents.slice(-8),
        zones: a.zones.slice(-6),
        forecast: a.forecast,
        prognosis: a.prognosis,
        frames: a.frames,
        lifecycle: a.lifecycle ?? null,
        green: IV === "5m" ? {
          lastT: glast ? glast.t : null,
          lastBarCloseAt: glast ? glast.barCloseAt : null,
          event: gev,
          eventT: gi >= 0 ? frames[gi].t : null,
          votes: glast ? { B: glast.B, S: glast.S, N: glast.N, votes: glast.votes } : null,
          gold: gold ? { t: frames[bi].t, barCloseAt: gold.barCloseAt, close: gold.close, gold: gold.gold ?? null } : null,
        } : null,
        tensor2: { last: row(rep[rep.length - 1]), marker: ti >= 0 ? row(rep[ti]) : null },
        printer: pLast,
        tensor0: z ? { last: z.last, event: zi >= 0 ? z.frames[zi] : null, identity: z.identity } : null,
        inferred: { id: inferred.INFERRED_ID, process: lines, code, evidence: ev, score: inferred.inferredScore(ev), qualifies: inferred.inferredQualifies(ev) },
        study,
      });
    } catch (e) {
      out.push({ ok: false, symbol: req.symbol, error: String((e && e.message) || e).slice(0, 300) });
    }
  }
  process.stdout.write(JSON.stringify(studyEod ? { ok: true, study: studyEod } : { ok: true, results: out }) + "\n");
} catch (e) {
  process.stdout.write(JSON.stringify({ ok: false, error: String((e && e.stack) || e).slice(0, 1500) }) + "\n");
}
