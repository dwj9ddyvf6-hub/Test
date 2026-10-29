/**
 * Runs Midna's Tensor engine for the forward-lab scan (src/lib/equity/forward-scan.ts prepare()): the engine is
 * scripts/tensor/engine.mjs + engine-extra.mjs of the Midna repo (blobs 4d02997a / b7295399), byte-identical to the
 * copies vendored at desk/vendor/old_desk_research/dcg_scorer/ and executed from there, unmodified.
 *
 * stdin  {names: [{sym, day: [...], o: [...], h: [...], l: [...], c: [...], v: [...]}]}  (forward-scan validBars rows)
 * stdout {out: {sym: {n, d: Series, w: Series|null, wdays: [...], wlast: [...]}}}
 *   prepare(): indicators -> markers -> extras on the daily bars; weekly() (Monday weeks) and, when it has >= 10 bars,
 *   the same three layers on the weekly bars. Series carries what forward-scan's barBag / htfBag / marketBag read at
 *   the last bar (j = n - 1) plus the marker histories they scan. Non-finite numbers travel as null.
 */
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const HERE = path.dirname(fileURLToPath(import.meta.url))
const VENDOR = path.join(HERE, "..", "vendor", "old_desk_research", "dcg_scorer")
const { indicators, markers, weekly } = await import(path.join(VENDOR, "engine.mjs"))
const { extras } = await import(path.join(VENDOR, "engine-extra.mjs"))

const num = (x) => (typeof x === "number" && Number.isFinite(x) ? x : null)
const arr = (a) => Array.from(a, (x) => num(Number(x)))
const tail = (a, j, k) => {
  const out = []
  for (let i = Math.max(0, j - k + 1); i <= j; i += 1) out.push(num(Number(a[i])))
  return out
}

function series(ind, mk, ex) {
  const j = ind.n - 1
  const at = (a) => num(Number(a[j]))
  return {
    n: ind.n,
    atr14: at(ind.atr14), o: at(ind.o), c: at(ind.c), cprev: j > 0 ? num(Number(ind.c[j - 1])) : null, h: at(ind.h),
    l: at(ind.l), ema21: at(ind.ema21), ema200: at(ind.ema200), bull: at(ind.bull), slowj: at(ind.slow),
    fast: at(mk.fast), utstop: at(mk.ut.stop), stochK: at(ind.stochK), wt1: at(ind.wt1), wt2: at(ind.wt2),
    adx: at(ind.adx), plusDi: at(ind.plusDi), minusDi: at(ind.minusDi), squeezeOn: at(ind.squeezeOn), rvol: at(ind.rvol),
    votes: ind.votes.map((v) => num(Number(v[j]))),
    warning: at(ex.warning), weak: at(ex.weak), candle: at(ex.candle), dots: at(ex.dots), ribbon: at(ex.ribbon),
    ribbonWidth: at(ex.ribbonWidth), ribbonSlope: at(ex.ribbonSlope), macdHist: at(ex.macdHist), strat: at(ex.strat),
    ocState: at(ex.ocState), mcdxProfit: at(ex.mcdxProfit), mcdxLocked: at(ex.mcdxLocked), obvDiv: at(ex.obvDiv),
    activeCall: at(ex.activeCall), lifecycle: at(ex.lifecycle), lastPrimaryAge: at(ex.lastPrimaryAge),
    footprint: at(ex.footprint), extWarn: at(ex.extWarn), lifeState: at(ex.lifeState), swingScore: at(ex.swingScore),
    phenotype: at(ex.phenotype),
    ocGreenDot: tail(ex.ocGreenDot, j, 4), ocBlueTriangle: tail(ex.ocBlueTriangle, j, 4), ocBlood: tail(ex.ocBlood, j, 4),
    ocYellowX: tail(ex.ocYellowX, j, 4), dcbBuy: tail(ex.dcbBuy, j, 4),
    primaryDir: arr(mk.primaryDir), cyan: arr(mk.cyan), green: arr(mk.green), swingEvent: arr(mk.swingEvent),
    red: arr(mk.red), magenta: arr(mk.magenta), regime: arr(mk.ut.regime), consensus: arr(mk.consensus), slow: arr(ind.slow),
  }
}

const input = JSON.parse(fs.readFileSync(0, "utf8"))
const out = {}
for (const x of input.names) {
  const daily = { day: x.day, o: Float64Array.from(x.o), h: Float64Array.from(x.h), l: Float64Array.from(x.l),
    c: Float64Array.from(x.c), v: Float64Array.from(x.v) }
  const ind = indicators(daily)
  const mk = markers(ind)
  const ex = extras(ind, mk)
  const week = weekly(daily.day, daily.o, daily.h, daily.l, daily.c, daily.v)
  let w = null
  if (week.c.length >= 10) {
    const wBars = { day: week.day, o: Float64Array.from(week.o), h: Float64Array.from(week.h), l: Float64Array.from(week.l),
      c: Float64Array.from(week.c), v: Float64Array.from(week.v) }
    const wind = indicators(wBars)
    const wmk = markers(wind)
    w = series(wind, wmk, extras(wind, wmk))
  }
  out[x.sym] = { n: ind.n, d: series(ind, mk, ex), w, wlast: week.lastIndex }
}
process.stdout.write(JSON.stringify({ out }))
