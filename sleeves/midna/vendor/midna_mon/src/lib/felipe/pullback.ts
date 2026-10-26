import { atr, ema, rsi } from "../lector/pine"

export type Day = { date: string; open: number; high: number; low: number; close: number }

export type PullbackSignal = {
  date: string
  entry: number
  stop: number
  target: number
  rsi: number
}

/** The nineteen funds named on the public Portfolio T page. */
export const FELIPE_ETFS = [
  "SPY", "QQQ", "IWM", "DIA", "MDY",
  "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLC",
  "SMH", "SOXX", "IBB", "XRT", "ITB",
] as const

export type StopMode = "week-low" | "week-atr" | "day-atr"
export type PathMode = "weekly" | "daily"

export type TradeResult = {
  entryDate: string
  exitDate: string
  ret: number
  r: number
  stopped: boolean
  partial: boolean
}

export type PullbackTrip = TradeResult & { sym: string }

export type PullbackPoint = { date: string; equity: number; exposure: number }

export type PullbackBook = {
  curve: PullbackPoint[]
  trips: PullbackTrip[]
  open: { sym: string; entryDate: string; ret: number }[]
  fired: number
  taken: number
  meanExposure: number
}

export type ForcedEntry = {
  sym: string
  date: string
  rsi: number
  entry?: number
  stop: number
  target: number
  deadline: string
}

export type PullbackOptions = {
  slots?: number
  weight?: number
  cost?: number
  oversold?: number | null
  partial?: number
  stop?: StopMode
  path?: PathMode
  entryFrom?: string
  entryTo?: string
  curveFrom?: string
  curveTo?: string
  entryLag?: boolean
  allowLeverage?: boolean
  forced?: ForcedEntry[]
}

type WorkingSignal = ForcedEntry

/** Weekly bars from daily sessions. Each bar is dated on its last session. */
export function toWeeks(days: Day[]): Day[] {
  const groups = new Map<string, Day>()
  for (const day of days) {
    const key = weekStart(day.date)
    const existing = groups.get(key)
    if (!existing) {
      groups.set(key, { date: day.date, open: day.open, high: day.high, low: day.low, close: day.close })
      continue
    }
    existing.high = Math.max(existing.high, day.high)
    existing.low = Math.min(existing.low, day.low)
    existing.close = day.close
    existing.date = day.date
  }
  return [...groups.values()].sort((a, b) => a.date.localeCompare(b.date))
}

/** Drops the unfinished week at the end of the file. A holiday week that already ended stays. */
export function completedWeeks(days: Day[]): Day[] {
  const weeks = toWeeks(cleanDays(days))
  const last = weeks[weeks.length - 1]
  if (last && weekday(last.date) !== 5) weeks.pop()
  return weeks
}

export function pullbackSignals(weeks: Day[], oversold: number | null = 40): PullbackSignal[] {
  if (weeks.length < 60) return []
  const closes = weeks.map((week) => week.close)
  const fast = ema(closes, 8)
  const mid = ema(closes, 20)
  const slow = ema(closes, 50)
  const strength = rsi(closes, 14)
  const out: PullbackSignal[] = []
  for (let i = 50; i < weeks.length; i += 1) {
    const signal = readingSignal(weeks[i], fast[i], mid[i], slow[i], strength[i], oversold)
    if (signal) out.push(signal)
  }
  return out
}

/**
 * One weekly pullback, checked on weekly bars, stop at the signal week's low.
 * A stop in a week beats a target in that same week.
 */
export function simulatePullback(weeks: Day[], signalIndex: number, cost = 0.001): TradeResult | null {
  const signal = weeks[signalIndex]
  if (!signal || !(signal.close > signal.low)) return null
  const entry = signal.close
  const stop = signal.low
  const risk = entry - stop
  const target = entry + risk
  let remaining = 1
  let multiple = 0
  let partial = false
  let stopped = false
  let exitDate = signal.date
  const last = Math.min(weeks.length - 1, signalIndex + 5)
  for (let i = signalIndex + 1; i <= last; i += 1) {
    const week = weeks[i]
    exitDate = week.date
    if (week.open <= stop) {
      multiple += remaining * (week.open / entry)
      remaining = 0
      stopped = true
      break
    }
    if (week.low <= stop) {
      multiple += remaining * (stop / entry)
      remaining = 0
      stopped = true
      break
    }
    if (!partial && week.high >= target) {
      multiple += 0.25 * (target / entry)
      remaining = 0.75
      partial = true
    }
    if (i === last && remaining > 0) {
      multiple += remaining * (week.close / entry)
      remaining = 0
    }
  }
  if (remaining > 0) return null
  const ret = (multiple * (1 - cost)) / (1 + cost) - 1
  const r = risk === 0 ? 0 : (multiple - 1) * entry / risk
  return { entryDate: signal.date, exitDate, ret, r, stopped, partial }
}

/**
 * The published weekly pullback without the next-week open. These caches have no open.
 * A low through the stop still exits at the stop. A high through the target still sells a quarter.
 */
export function simulatePullbackWithoutOpen(weeks: Day[], signalIndex: number, cost = 0.001): TradeResult | null {
  const signal = weeks[signalIndex]
  if (!signal || !(signal.close > signal.low)) return null
  const entry = signal.close
  const stop = signal.low
  const risk = entry - stop
  const target = entry + risk
  let remaining = 1
  let multiple = 0
  let partial = false
  let stopped = false
  let exitDate = signal.date
  const last = Math.min(weeks.length - 1, signalIndex + 5)
  for (let i = signalIndex + 1; i <= last; i += 1) {
    const week = weeks[i]
    exitDate = week.date
    if (week.low <= stop) {
      multiple += remaining * (stop / entry)
      remaining = 0
      stopped = true
      break
    }
    if (!partial && week.high >= target) {
      multiple += 0.25 * (target / entry)
      remaining = 0.75
      partial = true
    }
    if (i === last && remaining > 0) {
      multiple += remaining * (week.close / entry)
      remaining = 0
    }
  }
  if (remaining > 0) return null
  const ret = (multiple * (1 - cost)) / (1 + cost) - 1
  const r = risk === 0 ? 0 : (multiple - 1) * entry / risk
  return { entryDate: signal.date, exitDate, ret, r, stopped, partial }
}

export function runPullback(tapes: Record<string, Day[]>, options: PullbackOptions = {}): PullbackBook {
  const slots = options.slots ?? 10
  const weight = options.weight ?? 1 / slots
  const cost = options.cost ?? 0.001
  const partialFrac = options.partial ?? 0.25
  const stopMode = options.stop ?? "week-atr"
  const path = options.path ?? "daily"
  const entryFrom = options.entryFrom ?? "0000-01-01"
  const entryTo = options.entryTo ?? "9999-12-31"
  const curveFrom = options.curveFrom ?? entryFrom
  const curveTo = options.curveTo
  const entryLag = options.entryLag ?? false
  const allowLeverage = options.allowLeverage ?? false
  const oversold = options.oversold === undefined ? 40 : options.oversold

  const cleaned: Record<string, Day[]> = {}
  for (const [sym, days] of Object.entries(tapes)) cleaned[sym] = cleanDays(days)

  const signals = (options.forced ?? collectSignals(cleaned, oversold, stopMode)).filter(
    (signal) => signal.date >= entryFrom && signal.date < entryTo,
  )
  const byDate = new Map<string, WorkingSignal[]>()
  for (const signal of signals) {
    const list = byDate.get(signal.date) ?? []
    list.push(signal)
    byDate.set(signal.date, list)
  }

  const exec = new Map<string, Day[]>()
  const lookup = new Map<string, Map<string, Day>>()
  const weekEnds = new Set<string>()
  for (const [sym, days] of Object.entries(cleaned)) {
    const weeks = completedWeeks(days)
    for (const week of weeks) weekEnds.add(week.date)
    const bars = path === "weekly" ? weeks : days
    exec.set(sym, bars)
    lookup.set(sym, new Map(bars.map((bar) => [bar.date, bar])))
  }

  const lagByDate = new Map<string, WorkingSignal[]>()
  if (entryLag) {
    for (const [sym, bars] of exec) {
      const next = new Map<string, string>()
      for (let i = 0; i < bars.length - 1; i += 1) next.set(bars[i].date, bars[i + 1].date)
      for (const signal of signals) {
        if (signal.sym !== sym) continue
        const fill = next.get(signal.date)
        if (!fill) continue
        const list = lagByDate.get(fill) ?? []
        list.push(signal)
        lagByDate.set(fill, list)
      }
    }
  }

  const clock = [...new Set([...exec.values()].flatMap((bars) => bars.map((bar) => bar.date)))]
    .filter((date) => date >= curveFrom)
    .sort()

  type Position = {
    sym: string
    entry: number
    stop: number
    target: number
    entryDate: string
    activeAfter: string
    deadline: string
    notional: number
    remaining: number
    partial: boolean
    got: number
    grossOut: number
    last: number
    risk: number
  }

  const positions: Position[] = []
  const trips: PullbackTrip[] = []
  const daily: PullbackPoint[] = []
  let cash = 1
  let taken = 0

  const equityNow = () => {
    let value = cash
    for (const pos of positions) value += pos.remaining * pos.notional * (pos.last / pos.entry)
    return value
  }

  const finish = (pos: Position, px: number, exitDate: string, stopped: boolean) => {
    const slice = pos.remaining * pos.notional * (px / pos.entry)
    pos.grossOut += slice
    const fill = slice * (1 - cost)
    pos.got += fill
    cash += fill
    const paid = pos.notional * (1 + cost)
    const multiple = pos.notional === 0 ? 1 : pos.grossOut / pos.notional
    trips.push({
      sym: pos.sym,
      entryDate: pos.entryDate,
      exitDate,
      ret: paid === 0 ? 0 : pos.got / paid - 1,
      r: pos.risk === 0 ? 0 : (multiple - 1) * pos.entry / pos.risk,
      stopped,
      partial: pos.partial,
    })
  }

  const openAt = (signal: WorkingSignal, entry: number, stop: number, target: number, entryDate: string, activeAfter: string) => {
    const equity = equityNow()
    const wanted = equity * weight
    const budget = allowLeverage ? wanted : Math.min(wanted, Math.max(cash, 0))
    if (!(budget > 0) || !(entry > stop) || !(target > entry)) return
    const notional = budget / (1 + cost)
    cash -= budget
    taken += 1
    positions.push({
      sym: signal.sym,
      entry,
      stop,
      target,
      entryDate,
      activeAfter,
      deadline: signal.deadline,
      notional,
      remaining: 1,
      partial: false,
      got: 0,
      grossOut: 0,
      last: entry,
      risk: entry - stop,
    })
  }

  for (const date of clock) {
    const past = curveTo != null && date >= curveTo
    if (past && positions.length === 0) break

    if (entryLag && !past) {
      for (const signal of lagByDate.get(date) ?? []) {
        if (positions.some((pos) => pos.sym === signal.sym)) continue
        const bar = lookup.get(signal.sym)?.get(date)
        if (!bar) continue
        const placed = laggedPrices(signal, bar.open, stopMode)
        if (!placed) continue
        if (!(bar.open > placed.stop)) {
          const equity = equityNow()
          const wanted = equity * weight
          const budget = allowLeverage ? wanted : Math.min(wanted, Math.max(cash, 0))
          if (!(budget > 0)) continue
          const notional = budget / (1 + cost)
          const got = notional * (1 - cost)
          cash -= budget
          cash += got
          taken += 1
          trips.push({
            sym: signal.sym,
            entryDate: date,
            exitDate: date,
            ret: got / budget - 1,
            r: 0,
            stopped: true,
            partial: false,
          })
          continue
        }
        openAt(signal, placed.entry, placed.stop, placed.target, date, signal.date)
      }
    }

    for (let i = positions.length - 1; i >= 0; i -= 1) {
      const pos = positions[i]
      const bar = lookup.get(pos.sym)?.get(date)
      if (!bar || bar.date <= pos.activeAfter) continue
      pos.last = bar.close
      if (bar.open <= pos.stop) {
        finish(pos, bar.open, bar.date, true)
        positions.splice(i, 1)
        continue
      }
      if (bar.low <= pos.stop) {
        finish(pos, pos.stop, bar.date, true)
        positions.splice(i, 1)
        continue
      }
      if (!pos.partial && partialFrac > 0 && bar.high >= pos.target) {
        const slice = partialFrac * pos.notional * (pos.target / pos.entry)
        pos.grossOut += slice
        const fill = slice * (1 - cost)
        pos.got += fill
        cash += fill
        pos.remaining -= partialFrac
        pos.partial = true
      }
      if (pos.deadline && bar.date >= pos.deadline) {
        finish(pos, bar.close, bar.date, false)
        positions.splice(i, 1)
      }
    }

    if (!entryLag && !past && date >= entryFrom && date < entryTo) {
      const room = slots - positions.length
      if (room > 0) {
        const candidates = (byDate.get(date) ?? [])
          .filter((signal) => !positions.some((pos) => pos.sym === signal.sym))
          .sort((a, b) => a.rsi - b.rsi || a.sym.localeCompare(b.sym))
        for (const signal of candidates.slice(0, room)) {
          const entry = signal.entry ?? lookup.get(signal.sym)?.get(date)?.close
          if (entry == null) continue
          openAt(signal, entry, signal.stop, signal.target, date, date)
        }
      }
    }

    const equity = equityNow()
    let invested = 0
    for (const pos of positions) invested += pos.remaining * pos.notional * (pos.last / pos.entry)
    daily.push({ date, equity, exposure: equity > 0 ? invested / equity : 0 })
    if (past && positions.length === 0) break
  }

  const curve = sampleWeeks(daily, weekEnds)
  const open = positions.map((pos) => {
    const marked = pos.got + pos.remaining * pos.notional * (pos.last / pos.entry)
    const paid = pos.notional * (1 + cost)
    return { sym: pos.sym, entryDate: pos.entryDate, ret: paid === 0 ? 0 : marked / paid - 1 }
  })
  const meanExposure = curve.length ? curve.reduce((sum, point) => sum + point.exposure, 0) / curve.length : 0
  return { curve, trips, open, fired: signals.length, taken, meanExposure }
}

export function bookStats(curve: { date: string; equity: number }[]): { cagr: number; sharpe: number; maxDd: number; weeks: number } | null {
  if (curve.length < 5) return null
  const rets: number[] = []
  let peak = curve[0].equity
  let maxDd = 0
  for (let i = 1; i < curve.length; i += 1) {
    const prev = curve[i - 1].equity
    if (!(prev > 0) || !Number.isFinite(curve[i].equity)) return null
    rets.push(curve[i].equity / prev - 1)
    peak = Math.max(peak, curve[i].equity)
    maxDd = Math.min(maxDd, curve[i].equity / peak - 1)
  }
  const mean = rets.reduce((sum, value) => sum + value, 0) / rets.length
  const variance = rets.reduce((sum, value) => sum + (value - mean) ** 2, 0) / rets.length
  const years = rets.length / 52
  const end = curve[curve.length - 1].equity
  const start = curve[0].equity
  return {
    cagr: years > 0 && start > 0 && end > 0 ? (end / start) ** (1 / years) - 1 : 0,
    sharpe: variance > 0 ? (mean / Math.sqrt(variance)) * Math.sqrt(52) : 0,
    maxDd,
    weeks: rets.length,
  }
}

/** Buy and hold, marked on the sleeve's dates. No costs. */
export function buyHold(days: Day[], marks: { date: string }[]): { date: string; equity: number }[] {
  const cleaned = cleanDays(days)
  if (!cleaned.length || !marks.length) return []
  let last = cleaned[0].close
  let cursor = 0
  const closes = marks.map((mark) => {
    while (cursor < cleaned.length && cleaned[cursor].date <= mark.date) {
      last = cleaned[cursor].close
      cursor += 1
    }
    return last
  })
  const start = closes[0] || 1
  return marks.map((mark, index) => ({ date: mark.date, equity: closes[index] / start }))
}

export type QldBook = {
  curve: { date: string; equity: number }[]
  trips: { entryDate: string; exitDate: string; ret: number }[]
  open: boolean
}

/** Fully invested QLD while the prior completed QQQ week has EMA(12) above EMA(26). */
export function runQld(qqqDays: Day[], qldDays: Day[], options: { from?: string; to?: string; cost?: number } = {}): QldBook {
  const from = options.from ?? "0000-01-01"
  const to = options.to
  const cost = options.cost ?? 0.001
  const qqqWeeks = completedWeeks(qqqDays)
  const qldBy = new Map(completedWeeks(qldDays).map((week) => [weekStart(week.date), week]))
  const fast = ema(qqqWeeks.map((week) => week.close), 12)
  const slow = ema(qqqWeeks.map((week) => week.close), 26)
  const curve: { date: string; equity: number }[] = []
  const trips: { entryDate: string; exitDate: string; ret: number }[] = []
  let cash = 1
  let holding: { entry: number; notional: number; before: number; entryDate: string } | null = null

  for (let i = 1; i < qqqWeeks.length; i += 1) {
    const bar = qldBy.get(weekStart(qqqWeeks[i].date))
    if (!bar) continue
    if (bar.date < from) continue
    if (to != null && bar.date >= to) break
    const priorFast = fast[i - 1]
    const priorSlow = slow[i - 1]
    const on = priorFast != null && priorSlow != null && priorFast > priorSlow
    if (on && !holding && bar.open > 0) {
      const before = cash
      const notional = cash / (1 + cost)
      cash = 0
      holding = { entry: bar.open, notional, before, entryDate: bar.date }
    } else if (!on && holding) {
      cash = holding.notional * (bar.open / holding.entry) * (1 - cost)
      trips.push({ entryDate: holding.entryDate, exitDate: bar.date, ret: holding.before === 0 ? 0 : cash / holding.before - 1 })
      holding = null
    }
    const equity = holding ? holding.notional * (bar.close / holding.entry) + cash : cash
    curve.push({ date: bar.date, equity })
  }
  return { curve, trips, open: holding != null }
}

export function qldState(days: Day[]): { date: string; on: boolean; fast: number; slow: number } | null {
  const weeks = completedWeeks(days)
  if (weeks.length < 30) return null
  const fast = ema(weeks.map((week) => week.close), 12)
  const slow = ema(weeks.map((week) => week.close), 26)
  const i = weeks.length - 1
  const fastValue = fast[i]
  const slowValue = slow[i]
  if (fastValue == null || slowValue == null) return null
  return { date: weeks[i].date, on: fastValue > slowValue, fast: fastValue, slow: slowValue }
}

export function lastWeekState(days: Day[]): {
  date: string
  close: number
  low: number
  rsi: number | null
  atr: number | null
  stacked: boolean
  signal: boolean
} | null {
  const weeks = completedWeeks(days)
  if (weeks.length < 60) return null
  const closes = weeks.map((week) => week.close)
  const fast = ema(closes, 8)
  const mid = ema(closes, 20)
  const slow = ema(closes, 50)
  const strength = rsi(closes, 14)
  const range = atr(weeks, 5)
  const i = weeks.length - 1
  const week = weeks[i]
  const e8 = fast[i]
  const e20 = mid[i]
  const e50 = slow[i]
  const osc = strength[i]
  const stacked = e8 != null && e20 != null && e50 != null && e8 > e20 && e20 > e50 && week.close > e50
  return {
    date: week.date,
    close: week.close,
    low: week.low,
    rsi: osc,
    atr: range[i],
    stacked,
    signal: readingSignal(week, e8, e20, e50, osc, null) != null,
  }
}

function collectSignals(tapes: Record<string, Day[]>, oversold: number | null, stopMode: StopMode): WorkingSignal[] {
  const out: WorkingSignal[] = []
  for (const [sym, days] of Object.entries(tapes)) {
    const weeks = completedWeeks(days)
    const weeklyAtr = atr(weeks, 5)
    const dailyAtr = stopMode === "day-atr" ? atr(days, 5) : null
    const dailyAt = dailyAtr ? new Map(days.map((day, index) => [day.date, dailyAtr[index]])) : null
    const raw = pullbackSignals(weeks, oversold)
    for (const signal of raw) {
      const index = weeks.findIndex((week) => week.date === signal.date)
      if (index < 0) continue
      let stop = signal.stop
      let target = signal.target
      if (stopMode === "week-atr") {
        const width = weeklyAtr[index]
        if (width == null || !(width > 0)) continue
        stop = signal.entry - width
        target = signal.entry + width
      } else if (stopMode === "day-atr") {
        const width = dailyAt?.get(signal.date)
        if (width == null || !(width > 0)) continue
        stop = signal.entry - width
        target = signal.entry + width
      }
      if (!(signal.entry > stop) || !(target > signal.entry)) continue
      out.push({
        sym,
        date: signal.date,
        rsi: signal.rsi,
        entry: signal.entry,
        stop,
        target,
        deadline: weeks[index + 5]?.date ?? "",
      })
    }
  }
  return out
}

function readingSignal(
  week: Day,
  e8: number | null,
  e20: number | null,
  e50: number | null,
  osc: number | null,
  oversold: number | null,
): PullbackSignal | null {
  if (e8 == null || e20 == null || e50 == null) return null
  if (oversold != null && (osc == null || !(osc <= oversold))) return null
  if (!(e8 > e20 && e20 > e50)) return null
  if (!(week.close > e50)) return null
  if (!(week.low <= e8)) return null
  if (!(week.close > week.low)) return null
  const risk = week.close - week.low
  return { date: week.date, entry: week.close, stop: week.low, target: week.close + risk, rsi: osc ?? 50 }
}

function laggedPrices(signal: WorkingSignal, open: number, stopMode: StopMode): { entry: number; stop: number; target: number } | null {
  if (!(open > 0)) return null
  if (stopMode === "week-low") {
    const stop = signal.stop
    if (!(open > stop)) return { entry: open, stop, target: open }
    return { entry: open, stop, target: open + (open - stop) }
  }
  const width = signal.entry - signal.stop
  if (!(width > 0)) return null
  return { entry: open, stop: open - width, target: open + width }
}

function sampleWeeks(daily: PullbackPoint[], weekEnds: Set<string>): PullbackPoint[] {
  if (!daily.length) return []
  const sampled = daily.filter((point) => weekEnds.has(point.date))
  const last = daily[daily.length - 1]
  if (!sampled.length || sampled[sampled.length - 1].date !== last.date) sampled.push(last)
  return sampled
}

function cleanDays(days: Day[]): Day[] {
  const map = new Map<string, Day>()
  for (const day of days) {
    if (!(day.close > 0) || !(day.high > 0)) continue
    const open = day.open > 0 ? day.open : day.close
    const low = day.low > 0 ? day.low : Math.min(open, day.close)
    map.set(day.date, {
      date: day.date,
      open,
      high: Math.max(day.high, open, day.close, low),
      low: Math.min(low, open, day.close),
      close: day.close,
    })
  }
  return [...map.values()].sort((a, b) => a.date.localeCompare(b.date))
}

function weekStart(date: string): string {
  const [year, month, day] = date.split("-").map(Number)
  const utc = new Date(Date.UTC(year, month - 1, day))
  const dow = utc.getUTCDay()
  const offset = dow === 0 ? -6 : 1 - dow
  utc.setUTCDate(utc.getUTCDate() + offset)
  return utc.toISOString().slice(0, 10)
}

function weekday(date: string): number {
  const [year, month, day] = date.split("-").map(Number)
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay()
}
