// Author_intraweek.mjs: the s_wait_intraweek partial-week detector (Author-research DESK_INTEGRATION/sleeve_specs/s_wait_intraweek,
// "What live needs" 1-2), run after the close on trading days by the Author_wait_feed job (desk/sleeves/families/Author_wait.py).
//
// Series per name = the completed weeks of the tracker's own Yahoo 1wk payload (<scratch>/shadow/work/data/1wk/<sym>.json, the 1W
// lane's input) + ONE provisional bar for the target week built from the tracker's closed daily bars (<scratch>/shadow/engine/1d/<sym>.csv)
// by the research builder (WEEKLY_GAPS g04a job(): open = the week's first open, high / low = max / min so far, close = the last close,
// volume = the sum so far, stamped at the week's Monday 00:00 ET like Yahoo; the tracker's own 1.14 weekly overlay rebuilds its current
// 1wk bar from the daily tape the same way). Yahoo's current-week rows (its stale week row and its separate live-session row) are dropped.
// The UNCHANGED production engine library (the research root's pinned real_engine/lib/anna-replica.mjs, imported read-only; the
// parse + build calls of real_engine/run_engine_live.mjs) evaluates it:
//   markers      the research definition (g04a / wg_intraweek.mjs): the provisional bar evaluated as the FINAL bar of the series (wall clock
//                = its week + 7 days, so the library treats it as closed, as the research clock did) -> primaryMarkers buy-cyan / buy-green;
//   provisional  the library's own live view of the same series (real wall clock: a developing week is "open"):
//                provisionalPrimaryMarkers ("developing weekly buy candidate") - recorded for the agreement count.
// Parity mode (--week YYYY-MM-DD, a Monday): that week's bar built from all its sessions (k = 5) as the final bar, for the comparison with the
// tracker's real 1W fires of that week (README "What live needs" 2).
//
// Replay (--asof YYYY-MM-DD): only the daily bars of sessions <= asof; the target week is asof's week (the live view's clock: asof 21:30 ET).
// usage: node Author_intraweek.mjs <anna-replica.mjs> <1wk payload dir> <engine 1d dir> <out.jsonl> [--now <epoch s>] [--week <monday>]
//        [--asof <YYYY-MM-DD>]
// out: one JSON line per name with daily bars in the target week:
//   {sym, monday, session, n_sessions, open, high, low, close, volume, markers, provisional, bull, bear}
import fs from "node:fs"
import path from "node:path"
import { pathToFileURL } from "node:url"

const a = process.argv.slice(2)
const [lib, wkDir, dDir, outF] = a
const opt = (k) => (a.indexOf(k) >= 0 ? a[a.indexOf(k) + 1] : null)
const ASOF = opt("--asof")
const WEEK_ARG = opt("--week")
const DAY = 24 * 3600
const { parseYahooReplicaHistory, buildAnnaReplica } = await import(pathToFileURL(path.resolve(lib)).href)

const FMT = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", weekday: "short", hour: "2-digit", hourCycle: "h23" })
function et(epoch) {
  const p = Object.fromEntries(FMT.formatToParts(new Date(epoch * 1000)).map((x) => [x.type, x.value]))
  return { date: `${p.year}-${p.month}-${p.day}`, wd: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(p.weekday) + 1, hour: Number(p.hour) }
}
function midnightET(date) {                       // epoch of 00:00 America/New_York on date (YYYY-MM-DD)
  const [y, m, d] = date.split("-").map(Number)
  for (const off of [4, 5]) { const t = Date.UTC(y, m - 1, d, off) / 1000; if (et(t).hour === 0 && et(t).date === date) return t }
  throw new Error(`no ET midnight for ${date}`)
}
function mondayOf(date) {
  const [y, m, d] = date.split("-").map(Number); const t = Date.UTC(y, m - 1, d) / 1000
  const wd = et(midnightET(date) + 12 * 3600).wd
  return new Date((t - (wd - 1) * DAY) * 1000).toISOString().slice(0, 10)
}

const NOW = opt("--now") ? Number(opt("--now")) : ASOF ? midnightET(ASOF) + 21.5 * 3600 : Math.floor(Date.now() / 1000)

function dailyRows(sym) {                          // the tracker's closed daily bars: [ts, o, h, l, c, v]
  const f = path.join(dDir, `${sym}.csv`)
  if (!fs.existsSync(f)) return []
  const lines = fs.readFileSync(f, "utf8").split("\n"); const cols = lines[0].split(",")
  const ix = ["timestamp", "open", "high", "low", "close", "volume", "barFinality"].map((c) => cols.indexOf(c))
  const out = []
  for (const line of lines.slice(-40)) {
    const x = line.split(","); if (x.length <= Math.max(...ix) || x[ix[6]] !== "closed") continue
    const r = ix.slice(0, 6).map((i) => Number(x[i])); if (r.slice(0, 5).every(Number.isFinite) && r[4] > 0 && r[1] > 0 && (!ASOF || et(r[0]).date <= ASOF)) out.push(r)
  }
  return out
}

function evaluate(payload, sym, now) {
  const h = parseYahooReplicaHistory(payload, sym, "1wk", now)
  if (!h) return null
  h.displayBars = 1e9
  const r = buildAnnaReplica(h)
  return r && r.bars && r.bars.length ? r.bars[r.bars.length - 1] : null
}

const rows = []
const stats = { files: 0, names: 0, evaluated: 0, markers: 0, provisional: 0, agree: 0, no_daily: 0, unreadable: 0, now: NOW, week: WEEK_ARG, asof: ASOF }
for (const f of fs.readdirSync(wkDir).filter((x) => x.endsWith(".json")).sort()) {
  stats.files += 1
  let p
  try { p = JSON.parse(fs.readFileSync(path.join(wkDir, f), "utf8")) } catch { stats.unreadable += 1; continue }
  const res = p?.chart?.result?.[0]; const sym = res?.meta?.symbol
  if (!sym || !Array.isArray(res.timestamp)) { stats.unreadable += 1; continue }
  stats.names += 1
  const daily = dailyRows(path.basename(f, ".json"))
  if (!daily.length) { stats.no_daily += 1; continue }
  const monday = WEEK_ARG || mondayOf(et(daily[daily.length - 1][0]).date)
  const w0 = midnightET(monday)
  const wk = daily.filter((r) => mondayOf(et(r[0]).date) === monday)
  if (!wk.length) { stats.no_daily += 1; continue }
  const bar = [w0, wk[0][1], Math.max(...wk.map((r) => r[2])), Math.min(...wk.map((r) => r[3])), wk[wk.length - 1][4], wk.reduce((s, r) => s + (Number.isFinite(r[5]) ? r[5] : 0), 0)]
  const q = res.indicators.quote[0]; const keep = res.timestamp.map((t, i) => (t < w0 ? i : -1)).filter((i) => i >= 0)
  const col = (k) => keep.map((i) => (q[k] || [])[i])
  const series = { chart: { result: [{ ...res, timestamp: [...keep.map((i) => res.timestamp[i]), bar[0]],
    indicators: { ...res.indicators, quote: [{ open: [...col("open"), bar[1]], high: [...col("high"), bar[2]], low: [...col("low"), bar[3]], close: [...col("close"), bar[4]], volume: [...col("volume"), bar[5]] }] } }] } }
  const fin = evaluate(series, sym, w0 + 7 * DAY + 3600)
  const live = WEEK_ARG ? fin : evaluate(series, sym, NOW)
  if (!fin || fin.timestamp !== w0) { stats.unreadable += 1; continue }
  stats.evaluated += 1
  const pick = (ms) => (ms || []).filter((m) => m === "buy-cyan" || m === "buy-green")
  const markers = pick(fin.primaryMarkers)
  const provisional = WEEK_ARG ? markers : (live && live.barFinality === "open" ? pick(live.provisionalPrimaryMarkers) : pick(live && live.primaryMarkers))
  if (markers.length) stats.markers += 1
  if (provisional.length) stats.provisional += 1
  if (markers.join("|") === provisional.join("|")) stats.agree += 1
  rows.push({ sym, monday, session: et(wk[wk.length - 1][0]).date, n_sessions: wk.length, open: bar[1], high: bar[2], low: bar[3], close: bar[4], volume: bar[5],
    markers, provisional, live_finality: live ? live.barFinality : null, bull: fin.bullishVotes, bear: fin.bearishVotes })
}
fs.writeFileSync(outF + ".tmp", rows.map((x) => JSON.stringify(x)).join("\n") + (rows.length ? "\n" : ""))
fs.renameSync(outF + ".tmp", outF)
console.log(JSON.stringify(stats))
