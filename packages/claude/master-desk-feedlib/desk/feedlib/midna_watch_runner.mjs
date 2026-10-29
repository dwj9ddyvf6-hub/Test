/**
 * Midna's hourly watch engine step (scripts/tensor-watch.mjs closedBars + enrich, @ cursor/lector-desk-f184): the
 * production replica quant-research/Author-research/real_engine/lib/anna-replica.mjs and
 * tensor-enrichment-signals.mjs of the Midna repo, vendored byte-exact under desk/vendor/midna/real_engine/ and executed
 * from there, unmodified.
 *
 * stdin  {jobs: [{key, interval: "1h"|"1d"|"1wk", payload: <Yahoo chart JSON>, now: epoch seconds}]}
 * stdout {out: {key: rows}}, the closed replica bars (closedBars) as
 *   1h   [timestamp, close, consensusBuy (0/1), monitorBuy (0/1)]            (enrich(bar))
 *   1d   [timestamp, open, close, slowState === "bearish" (0/1)]
 *   1wk  [timestamp, close, high, low, primaryMarkers includes "buy-cyan" (0/1)]
 * closedBars(payload, interval) = parseYahooReplicaHistory(payload, meta.symbol, interval, now) with displayBars 1e9,
 * buildAnnaReplica, barFinality "closed" — the watch's own code, with its clock (Date.now) set to the job's `now`.
 */
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const HERE = path.dirname(fileURLToPath(import.meta.url))
const LIB = path.join(HERE, "..", "vendor", "midna", "real_engine", "lib")
const { parseYahooReplicaHistory, buildAnnaReplica } = await import(path.join(LIB, "anna-replica.mjs"))
const { buildTensorEnrichmentSignals } = await import(path.join(LIB, "tensor-enrichment-signals.mjs"))

function closedBars(payload, interval, nowSec) {
  const meta = payload?.chart?.result?.[0]?.meta
  if (!meta?.symbol) return []
  const hist = parseYahooReplicaHistory(payload, meta.symbol, interval, nowSec)
  if (!hist) return []
  hist.displayBars = 1e9
  const rep = buildAnnaReplica(hist)
  if (!rep?.bars?.length) return []
  return rep.bars.filter((bar) => bar.barFinality === "closed")
}

const input = JSON.parse(fs.readFileSync(0, "utf8"))
const out = {}
for (const job of input.jobs) {
  let bars = []
  try {
    bars = closedBars(job.payload, job.interval, Math.floor(job.now))
  } catch (e) {
    out[job.key] = { error: String(e && e.message || e) }
    continue
  }
  if (job.interval === "1h") {
    out[job.key] = bars.map((bar) => {
      const ids = new Set(buildTensorEnrichmentSignals(bar).signals.map((item) => item.id))
      return [Number(bar.timestamp), Number(bar.close), ids.has("consensus-buy") ? 1 : 0, ids.has("monitor-buy") ? 1 : 0]
    })
  } else if (job.interval === "1d") {
    out[job.key] = bars.map((bar) => [Number(bar.timestamp), Number(bar.open), Number(bar.close),
      bar.slowState === "bearish" ? 1 : 0])
  } else {
    out[job.key] = bars.map((bar) => [Number(bar.timestamp), Number(bar.close), Number(bar.high), Number(bar.low),
      (bar.primaryMarkers || []).includes("buy-cyan") ? 1 : 0])
  }
}
process.stdout.write(JSON.stringify({ out }))
