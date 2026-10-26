import { promises as fs } from "fs"
import path from "path"
import {
  aboveYearHigh,
  donchian20,
  equalWeights,
  goldenCross,
  jaccard,
  longShortWeights,
  pearson,
  sign12,
  sign6,
  sign6and12,
  trailingReturn,
  type Series,
} from "../src/lib/research/tsmom"

const ROOT = process.cwd()
const BAR = path.join(ROOT, "data/backtest/bars")
const TRAIN_END = "2022-12-31"
const HOLD_END = "2024-12-31"
const DIVERSIFIED = [
  "SPY", "QQQ", "IWM", "EFA", "EEM",
  "XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC",
  "TLT", "IEF", "HYG", "LQD",
  "GLD", "SLV", "USO", "UNG", "DBA", "DBC",
  "UUP", "FXE", "FXY", "FXB",
]

type Panel = Map<string, Series>
type Weights = Map<string, number>
type WindowName = "train" | "holdout" | "fresh"

type PathStats = { days: number; cagr: number; sharpe: number; maxDd: number }
type Scored = {
  id: string
  title: string
  net: Record<WindowName, PathStats | null>
  gross: Record<WindowName, PathStats | null>
  excess: Record<WindowName, PathStats | null>
  trips: Record<WindowName, number>
  coverage: number
  avgNames: number
  dates: string[]
  daily: number[]
}

const FORMS: Array<{ id: string; title: string; signal: (series: Series, index: number) => boolean }> = [
  { id: "primary-12-1", title: "Primary 12-1 sign, long or cash", signal: sign12 },
  { id: "sign-6", title: "Six-month sign, long or cash", signal: sign6 },
  { id: "sign-6-and-12", title: "Six-month and twelve-month both positive", signal: sign6and12 },
  { id: "roc-12-1", title: "Rate of change, same 12-1 ratio", signal: sign12 },
  { id: "donchian-20", title: "Donchian 20-session break", signal: donchian20 },
  { id: "golden-cross", title: "50-session average above 200", signal: goldenCross },
  { id: "year-high", title: "Close above the prior 252-session high", signal: aboveYearHigh },
]

function costBps(symbol: string, price: number): number {
  if (DIVERSIFIED.includes(symbol) || symbol === "SPY") return 5
  if (!(price > 0) || price < 5) return 50
  if (price < 20) return 25
  return 10
}

function dv20(series: Series, index: number): number | null {
  if (index < 19) return null
  let sum = 0
  let count = 0
  for (let cursor = index - 19; cursor <= index; cursor += 1) {
    const close = series.close[cursor]
    const volume = series.vol[cursor]
    if (close > 0 && volume > 0) {
      sum += close * volume
      count += 1
    }
  }
  if (count < 15) return null
  return sum / count
}

function liquid(series: Series, index: number): boolean {
  const price = series.close[index]
  const dollar = dv20(series, index)
  return price >= 5 && series.adj[index] > 0 && dollar != null && dollar >= 1_000_000
}

function sliceStats(dates: string[], rets: number[], from: string, to: string): PathStats | null {
  const picked: number[] = []
  for (let index = 0; index < rets.length; index += 1) {
    if (dates[index] > from && dates[index] <= to && Number.isFinite(rets[index])) picked.push(rets[index])
  }
  if (picked.length < 40) return null
  let equity = 1
  let peak = 1
  let maxDd = 0
  let sum = 0
  let sum2 = 0
  for (const ret of picked) {
    const step = Math.max(-0.99, ret)
    equity *= 1 + step
    peak = Math.max(peak, equity)
    maxDd = Math.min(maxDd, equity / peak - 1)
    sum += ret
    sum2 += ret * ret
  }
  const mean = sum / picked.length
  const variance = Math.max(0, sum2 / picked.length - mean * mean)
  const sharpe = variance > 0 ? (mean / Math.sqrt(variance)) * Math.sqrt(252) : 0
  const cagr = equity > 0 ? equity ** (252 / picked.length) - 1 : -1
  return { days: picked.length, cagr, sharpe, maxDd }
}

function windows(dates: string[], rets: number[]): Record<WindowName, PathStats | null> {
  return {
    train: sliceStats(dates, rets, "1900-01-01", TRAIN_END),
    holdout: sliceStats(dates, rets, TRAIN_END, HOLD_END),
    fresh: sliceStats(dates, rets, HOLD_END, "2100-01-01"),
  }
}

function windowOf(day: string): WindowName | null {
  if (day <= TRAIN_END) return "train"
  if (day <= HOLD_END) return "holdout"
  return "fresh"
}

function simulate(
  dates: string[],
  panel: Panel,
  every: number,
  signal: (index: number) => Weights,
): { dates: string[]; net: number[]; gross: number[]; trips: Record<WindowName, number>; coverage: number; avgNames: number } {
  const net: number[] = []
  const gross: number[] = []
  const outDates: string[] = []
  const trips: Record<WindowName, number> = { train: 0, holdout: 0, fresh: 0 }
  let weights: Weights = new Map()
  let exposed = 0
  let nameSum = 0
  let span = 0
  const last = dates.length - 1
  for (let index = 260; index < last; index += 1) {
    span += 1
    if ((index - 260) % every === 0) {
      const next = signal(index) ?? new Map()
      let cost = 0
      const symbols = new Set([...weights.keys(), ...next.keys()])
      for (const symbol of symbols) {
        const before = weights.get(symbol) ?? 0
        const after = next.get(symbol) ?? 0
        if (before !== 0 && after === 0) {
          const bucket = windowOf(dates[index + 1])
          if (bucket) trips[bucket] += 1
        }
        const price = panel.get(symbol)?.close[index] ?? 0
        cost += Math.abs(after - before) * (costBps(symbol, price) / 10_000)
      }
      weights = next
      net.push(-cost)
    } else {
      net.push(0)
    }
    gross.push(0)
    outDates.push(dates[index + 1])
    if (!weights.size) continue
    exposed += 1
    nameSum += weights.size
    let grossRet = 0
    let used = 0
    const live: Array<[number, number]> = []
    for (const [symbol, weight] of weights) {
      const series = panel.get(symbol)
      const prev = series?.adj[index]
      const next = series?.adj[index + 1]
      if (!(prev > 0) || !(next > 0)) continue
      live.push([weight, next / prev - 1])
      used += Math.abs(weight)
    }
    if (!live.length || !(used > 0)) continue
    const scale = [...weights.values()].reduce((sum, weight) => sum + Math.abs(weight), 0) / used
    for (const [weight, ret] of live) grossRet += weight * scale * ret
    gross[gross.length - 1] = grossRet
    net[net.length - 1] += grossRet
  }
  return {
    dates: outDates,
    net,
    gross,
    trips,
    coverage: span ? exposed / span : 0,
    avgNames: exposed ? nameSum / exposed : 0,
  }
}

function score(id: string, title: string, dates: string[], panel: Panel, every: number, signal: (index: number) => Weights, spyDaily: number[]): Scored {
  const path = simulate(dates, panel, every, signal)
  const excessDaily = path.net.map((ret, index) => ret - (spyDaily[index] ?? 0))
  return {
    id,
    title,
    net: windows(path.dates, path.net),
    gross: windows(path.dates, path.gross),
    excess: windows(path.dates, excessDaily),
    trips: path.trips,
    coverage: path.coverage,
    avgNames: path.avgNames,
    dates: path.dates,
    daily: path.net,
  }
}

function beats(rule: PathStats | null, spy: PathStats | null): boolean {
  if (!rule || !spy) return false
  return rule.cagr > spy.cagr && rule.sharpe > spy.sharpe
}

function clears(rule: Scored, spy: Scored): boolean {
  return beats(rule.net.holdout, spy.net.holdout) && beats(rule.net.fresh, spy.net.fresh) && rule.trips.fresh >= 30
}

async function loadNames(): Promise<string[]> {
  const text = await fs.readFile(path.join(ROOT, "quant-research/registry/names.csv"), "utf8")
  return text
    .trim()
    .split("\n")
    .slice(1)
    .map((line) => line.split(",")[0]?.trim() ?? "")
    .filter(Boolean)
}

async function loadPanel(symbols: string[]): Promise<Panel> {
  const raw = new Map<string, { day: string; row: number[] }[]>()
  for (const symbol of symbols) {
    try {
      const rows = JSON.parse(await fs.readFile(path.join(BAR, `${symbol.replaceAll("/", "_")}.json`), "utf8")) as number[][]
      if (rows.length < 260) continue
      raw.set(symbol, rows.map((row) => ({ day: String(row[0]), row })))
    } catch {
      /* a missing cache file is skipped */
    }
  }
  const spy = raw.get("SPY")
  if (!spy) throw new Error("SPY bars are missing")
  const dates = spy.map((row) => row.day)
  const index = new Map(dates.map((day, position) => [day, position]))
  const panel: Panel = new Map()
  for (const [symbol, rows] of raw) {
    const blank = () => Array.from({ length: dates.length }, () => Number.NaN)
    const series: Series = { adj: blank(), close: blank(), high: blank(), low: blank(), vol: blank() }
    let valid = 0
    for (const item of rows) {
      const at = index.get(item.day)
      if (at == null) continue
      const adj = item.row[1]
      const close = item.row[2]
      if (!(adj > 0) || !(close > 0)) continue
      series.adj[at] = adj
      series.close[at] = close
      series.high[at] = item.row[3] > 0 ? item.row[3] : close
      series.low[at] = item.row[4] > 0 ? item.row[4] : close
      series.vol[at] = item.row[5] > 0 ? item.row[5] : 0
      valid += 1
    }
    if (valid >= 260) panel.set(symbol, series)
  }
  return panel
}

function liquidNames(panel: Panel, stocks: string[], index: number): string[] {
  const names: string[] = []
  for (const symbol of stocks) {
    const series = panel.get(symbol)
    if (series && liquid(series, index)) names.push(symbol)
  }
  return names
}

function formLongs(panel: Panel, names: string[], index: number, signal: (series: Series, index: number) => boolean): string[] {
  const longs: string[] = []
  for (const symbol of names) {
    const series = panel.get(symbol)
    if (series && signal(series, index)) longs.push(symbol)
  }
  return longs
}

function rankLongs(panel: Panel, names: string[], index: number): string[] {
  const rows: Array<{ symbol: string; score: number }> = []
  for (const symbol of names) {
    const series = panel.get(symbol)
    if (!series) continue
    const score = trailingReturn(series, index, 126)
    if (score == null) continue
    rows.push({ symbol, score })
  }
  if (rows.length < 10) return []
  rows.sort((a, b) => b.score - a.score)
  const count = Math.max(1, Math.floor(rows.length * 0.1))
  return rows.slice(0, count).map((row) => row.symbol)
}

function pct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—"
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`
}

function num(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—"
  return value.toFixed(2)
}

function cell(stats: PathStats | null): string {
  if (!stats) return "—"
  return `${num(stats.sharpe)} / ${pct(stats.cagr)} / ${pct(stats.maxDd)}`
}

async function main() {
  const names = await loadNames()
  const symbols = [...new Set([...names, ...DIVERSIFIED, "SPY"])]
  const panel = await loadPanel(symbols)
  const spyRows = JSON.parse(await fs.readFile(path.join(BAR, "SPY.json"), "utf8")) as number[][]
  const dates = spyRows.map((row) => String(row[0]))
  const stocks = names.filter((symbol) => panel.has(symbol))
  const etfs = DIVERSIFIED.filter((symbol) => panel.has(symbol))
  const spyBook = score("spy", "Hold SPY", dates, panel, 63, () => equalWeights(["SPY"]), [])
  const spyDaily = spyBook.daily
  const liquidBook = score("liquid-ew", "Liquid equal weight", dates, panel, 21, (index) => equalWeights(liquidNames(panel, stocks, index)), spyDaily)
  const rows = FORMS.map((form) =>
    score(form.id, form.title, dates, panel, 21, (index) => equalWeights(formLongs(panel, liquidNames(panel, stocks, index), index, form.signal)), spyDaily),
  )
  const diversifiedFlat = score(
    "etf-12-1-flat",
    "ETF book, 12-1 sign, long or cash",
    dates,
    panel,
    21,
    (index) => equalWeights(formLongs(panel, etfs, index, sign12)),
    spyDaily,
  )
  const diversifiedShort = score(
    "etf-12-1-ls",
    "ETF book, 12-1 sign, long and short",
    dates,
    panel,
    21,
    (index) => {
      const longs: string[] = []
      const shorts: string[] = []
      for (const symbol of etfs) {
        const series = panel.get(symbol)
        if (!series) continue
        const value = trailingReturn(series, index - 21, 252)
        if (value == null) continue
        if (value > 0) longs.push(symbol)
        else shorts.push(symbol)
      }
      return longShortWeights(longs, shorts)
    },
    spyDaily,
  )
  const reference = score("csmom-126", "Funded cross-sectional 126-day, top tenth, every 63", dates, panel, 63, (index) => {
    return equalWeights(rankLongs(panel, liquidNames(panel, stocks, index), index))
  }, spyDaily)

  const primary = rows[0]
  const overlaps: Array<{ id: string; jaccard: number | null; corr: number | null; samples: number }> = []
  for (const form of FORMS) {
    const samples: number[] = []
    let used = 0
    for (let index = 260; index < dates.length - 1; index += 21) {
      const day = dates[index + 1]
      if (!day || day <= HOLD_END) continue
      const universe = liquidNames(panel, stocks, index)
      const left = formLongs(panel, universe, index, sign12)
      const right = formLongs(panel, universe, index, form.signal)
      const score = jaccard(left, right)
      if (score == null) continue
      samples.push(score)
      used += 1
    }
    const rule = rows.find((row) => row.id === form.id)
    let corr: number | null = null
    if (rule) {
      const xs: number[] = []
      const ys: number[] = []
      for (let index = 0; index < primary.dates.length; index += 1) {
        if (primary.dates[index] <= HOLD_END) continue
        xs.push(primary.daily[index])
        ys.push(rule.daily[index] ?? Number.NaN)
      }
      corr = pearson(xs, ys)
    }
    overlaps.push({
      id: form.id,
      jaccard: samples.length ? samples.reduce((sum, value) => sum + value, 0) / samples.length : null,
      corr,
      samples: used,
    })
  }

  const freshLong: number[] = []
  const freshEligible: number[] = []
  for (let index = 260; index < dates.length - 1; index += 21) {
    if (dates[index + 1] <= HOLD_END) continue
    const universe = liquidNames(panel, stocks, index)
    freshEligible.push(universe.length)
    freshLong.push(formLongs(panel, universe, index, sign12).length)
  }
  const mean = (values: number[]) => (values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0)

  const books = [spyBook, liquidBook, ...rows, diversifiedFlat, diversifiedShort, reference]
  const lines = [
    "# Time-series momentum forms, 7 October 2026",
    "",
    "The preregistration is `quant-research/reports/TSMOM_FORMS_PREREG_2026-10-07.md`. The forms below are that list. The train window did not pick one.",
    "",
    `Clock is SPY sessions ${dates[0]} through ${dates.at(-1)} (${dates.length} sessions). Names in the cache: ${stocks.length}. Diversified ETFs present: ${etfs.length} of ${DIVERSIFIED.length}. A signal on session i earns the next session. Costs match the October lab. No borrow fee is charged.`,
    "",
    "## Paths",
    "",
    "Sharpe / CAGR / max drawdown, after costs. Excess is the CAGR and Sharpe of the daily difference versus SPY. That excess column is a check. The bar is the path’s own CAGR and Sharpe against SPY’s.",
    "",
    "| Book | Holdout | Fresh | Holdout excess vs SPY | Fresh excess vs SPY | Fresh exits | Avg names | Clears the bar |",
    "| --- | --- | --- | --- | --- | --- | --- | --- |",
  ]
  for (const book of books) {
    const bar = book.id === "spy" || book.id === "liquid-ew" || book.id === "csmom-126" ? "reference" : clears(book, spyBook) ? "yes" : "no"
    const holdExcess = book.id === "spy" ? "0.00 / +0.0%" : `${num(book.excess.holdout?.sharpe)} / ${pct(book.excess.holdout?.cagr)}`
    const freshExcess = book.id === "spy" ? "0.00 / +0.0%" : `${num(book.excess.fresh?.sharpe)} / ${pct(book.excess.fresh?.cagr)}`
    lines.push(
      `| ${book.title} | ${cell(book.net.holdout)} | ${cell(book.net.fresh)} | ${holdExcess} | ${freshExcess} | ${book.trips.fresh} | ${book.avgNames.toFixed(1)} | ${bar} |`,
    )
  }
  lines.push("")
  lines.push("## Train, printed and not used")
  lines.push("")
  lines.push("| Book | Train Sharpe / CAGR / max DD | Train exits |")
  lines.push("| --- | --- | --- |")
  for (const book of books) lines.push(`| ${book.title} | ${cell(book.net.train)} | ${book.trips.train} |`)
  lines.push("")
  lines.push("## Same bet, or a different one")
  lines.push("")
  lines.push("Fresh-window overlap with the primary 12-1 long set. Jaccard is the share of the union held by both. Correlation is daily net return.")
  lines.push("")
  lines.push("| Form | Fresh Jaccard | Fresh correlation | Rebalances |")
  lines.push("| --- | --- | --- | --- |")
  for (const row of overlaps) lines.push(`| ${row.id} | ${num(row.jaccard)} | ${num(row.corr)} | ${row.samples} |`)
  lines.push("")
  lines.push(
    `In the fresh window the primary 12-1 rule was long ${mean(freshLong).toFixed(0)} names on average, out of ${mean(freshEligible).toFixed(0)} liquid names (${pct(mean(freshEligible) ? mean(freshLong) / mean(freshEligible) : null)} of the liquid book). The names column above is the full-sample average, from 2006 on.`,
  )
  lines.push("")
  const cleared = books.filter((book) => book.id !== "spy" && book.id !== "liquid-ew" && book.id !== "csmom-126" && clears(book, spyBook))
  const different = overlaps.filter((row) => row.id !== "primary-12-1" && row.id !== "roc-12-1" && (row.jaccard ?? 1) < 0.25)
  const cousins = overlaps.filter((row) => row.id !== "primary-12-1" && row.id !== "roc-12-1" && (row.corr ?? 0) >= 0.95)
  lines.push("## Reading")
  lines.push("")
  lines.push(
    `Rate of change at this horizon is the primary rule. Fresh Jaccard ${num(overlaps.find((row) => row.id === "roc-12-1")?.jaccard)} and correlation ${num(overlaps.find((row) => row.id === "roc-12-1")?.corr)}. It is the same path, not a second edge.`,
  )
  lines.push("")
  lines.push(
    cousins.length
      ? `Daily returns still move together for ${cousins.map((row) => row.id).join(", ")} (fresh correlation at least 0.95). Their long sets are not the same: Jaccard is the overlap column, and it is well below 1.`
      : "No other form had a fresh daily correlation of 0.95 or more with the primary.",
  )
  lines.push("")
  const differentBooks = different.map((row) => rows.find((book) => book.id === row.id)).filter((book): book is Scored => Boolean(book))
  lines.push(
    different.length
      ? `${different.map((row) => row.id).join(" and ")} are a different bet. Fresh Jaccard versus the primary is under 0.25. Fresh CAGR: ${differentBooks.map((book) => `${book.id} ${pct(book.net.fresh?.cagr)}`).join(", ")}.`
      : "Every listed form overlapped the primary long set.",
  )
  lines.push("")
  lines.push(
    `The primary was long about two-thirds of the liquid names in the fresh window, and that window was a bull market. Its fresh CAGR beat SPY. Its holdout CAGR was ${pct(rows[0]?.net.holdout?.cagr)} against SPY at ${pct(spyBook.net.holdout?.cagr)}, and the daily-difference CAGR in the holdout was ${pct(rows[0]?.excess.holdout?.cagr)}. ${cleared.length ? `${cleared.map((book) => book.title).join(", ")} cleared the bar.` : "No form cleared the bar: both later windows have to beat SPY on CAGR and on Sharpe, with at least 30 fresh exits."}`,
  )
  lines.push("")
  lines.push(
    `The long/short ETF book made ${pct(diversifiedShort.net.holdout?.cagr)} in the holdout and ${pct(diversifiedShort.net.fresh?.cagr)} in the fresh window. Borrow was not charged, so the loss is not a fee. Names flip from long to short without passing through zero, which is why the exit count stays at zero. The long-or-cash ETF book had ${diversifiedFlat.trips.fresh} fresh exits and did not beat SPY's fresh CAGR.`,
  )
  lines.push("")
  lines.push(
    `The funded cross-sectional row is a check on the accounting, not a candidate in this test. Holdout Sharpe ${num(reference.net.holdout?.sharpe)}, CAGR ${pct(reference.net.holdout?.cagr)}, drawdown ${pct(reference.net.holdout?.maxDd)}. The October lab printed 1.48 / +45.9% / −27.9% for that same cell.`,
  )
  lines.push("")
  lines.push("## What this does to the desk")
  lines.push("")
  lines.push("Nothing. Playbook 1.0.0 stays. The liquid 126-day cross-sectional book stays the funded context book. Index time-series momentum stays off. No forward account is opened from this file. No broker is armed.")
  lines.push("")
  lines.push("## Rerun")
  lines.push("")
  lines.push("```bash")
  lines.push("npx tsx scripts/tsmom-forms.ts")
  lines.push("```")
  lines.push("")
  const report = path.join(ROOT, "quant-research/reports/TSMOM_FORMS_2026-10-07.md")
  await fs.writeFile(report, `${lines.join("\n")}\n`)
  const summary = books.map((book) => ({
    id: book.id,
    title: book.title,
    holdout: book.net.holdout,
    fresh: book.net.fresh,
    excessHoldout: book.excess.holdout,
    excessFresh: book.excess.fresh,
    tripsFresh: book.trips.fresh,
    avgNames: book.avgNames,
    clears: book.id === "spy" || book.id === "liquid-ew" || book.id === "csmom-126" ? null : clears(book, spyBook),
  }))
  await fs.writeFile(
    path.join(ROOT, "quant-research/reports/TSMOM_FORMS_2026-10-07.json"),
    JSON.stringify({ overlaps, freshLongShare: mean(freshEligible) ? mean(freshLong) / mean(freshEligible) : null, books: summary }, null, 2),
  )
  console.log(`wrote ${report}`)
  for (const book of books) {
    console.log(`${book.id} hold ${pct(book.net.holdout?.cagr)} fresh ${pct(book.net.fresh?.cagr)} trips ${book.trips.fresh} bar ${book.id.startsWith("primary") || book.id.startsWith("sign") || book.id.startsWith("roc") || book.id.startsWith("don") || book.id.startsWith("gold") || book.id.startsWith("year") || book.id.startsWith("etf") ? clears(book, spyBook) : "ref"}`)
  }
}

if (process.argv[1]?.endsWith("tsmom-forms.ts")) void main()
