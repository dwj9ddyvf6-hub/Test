export type Series = {
  adj: ArrayLike<number>
  close: ArrayLike<number>
  high: ArrayLike<number>
  low: ArrayLike<number>
  vol: ArrayLike<number>
}

/** Adjusted close at `end` over adjusted close `lookback` sessions earlier, minus one. A missing print is null. No fill. */
export function trailingReturn(series: Series, end: number, lookback: number): number | null {
  const start = end - lookback
  if (start < 0 || end < 0) return null
  const now = series.adj[end]
  const past = series.adj[start]
  if (!(now > 0) || !(past > 0)) return null
  return now / past - 1
}

export function adjustedHigh(series: Series, index: number): number | null {
  const close = series.close[index]
  const high = series.high[index]
  const adj = series.adj[index]
  if (!(close > 0) || !(high > 0) || !(adj > 0)) return null
  return high * (adj / close)
}

export function adjustedLow(series: Series, index: number): number | null {
  const close = series.close[index]
  const low = series.low[index]
  const adj = series.adj[index]
  if (!(close > 0) || !(low > 0) || !(adj > 0)) return null
  return low * (adj / close)
}

/** Highest adjusted high on [index-n, index-1]. Today's bar is not included. */
export function priorMaxHigh(series: Series, index: number, sessions: number): number | null {
  if (sessions < 1 || index - sessions < 0) return null
  let highest = -Infinity
  let count = 0
  for (let cursor = index - sessions; cursor <= index - 1; cursor += 1) {
    const high = adjustedHigh(series, cursor)
    if (high == null) continue
    highest = Math.max(highest, high)
    count += 1
  }
  if (count < Math.floor(sessions * 0.8)) return null
  return highest
}

export function sma(series: Series, index: number, sessions: number): number | null {
  if (sessions < 1 || index - sessions + 1 < 0) return null
  let sum = 0
  let count = 0
  for (let cursor = index - sessions + 1; cursor <= index; cursor += 1) {
    const price = series.adj[cursor]
    if (!(price > 0)) continue
    sum += price
    count += 1
  }
  if (count < Math.floor(sessions * 0.8)) return null
  return sum / count
}

export function positive(value: number | null): boolean {
  return value != null && value > 0
}

export function sign12(series: Series, index: number): boolean {
  return positive(trailingReturn(series, index - 21, 252))
}

export function sign6(series: Series, index: number): boolean {
  return positive(trailingReturn(series, index, 126))
}

export function sign6and12(series: Series, index: number): boolean {
  return positive(trailingReturn(series, index, 126)) && positive(trailingReturn(series, index, 252))
}

export function donchian20(series: Series, index: number): boolean {
  const high = priorMaxHigh(series, index, 20)
  return high != null && series.adj[index] > high
}

export function goldenCross(series: Series, index: number): boolean {
  const fast = sma(series, index, 50)
  const slow = sma(series, index, 200)
  return fast != null && slow != null && fast > slow
}

export function aboveYearHigh(series: Series, index: number): boolean {
  const high = priorMaxHigh(series, index, 252)
  return high != null && series.adj[index] > high
}

export function equalWeights(names: string[]): Map<string, number> {
  const weights = new Map<string, number>()
  if (!names.length) return weights
  const each = 1 / names.length
  for (const name of names) weights.set(name, each)
  return weights
}

/** Winners share +50%. Losers share −50%. An empty side stays cash and does not lever the other side. */
export function longShortWeights(longs: string[], shorts: string[]): Map<string, number> {
  const weights = new Map<string, number>()
  if (longs.length) {
    const each = 0.5 / longs.length
    for (const name of longs) weights.set(name, each)
  }
  if (shorts.length) {
    const each = -0.5 / shorts.length
    for (const name of shorts) weights.set(name, each)
  }
  return weights
}

export function jaccard(left: string[], right: string[]): number | null {
  const a = new Set(left)
  const b = new Set(right)
  if (!a.size && !b.size) return null
  let both = 0
  for (const name of a) if (b.has(name)) both += 1
  const union = a.size + b.size - both
  return union ? both / union : null
}

export type Side = -1 | 0 | 1

export function sign12Side(series: Series, index: number): Side {
  const value = trailingReturn(series, index - 21, 252)
  if (value == null || value === 0) return 0
  return value > 0 ? 1 : -1
}

export function sign6Side(series: Series, index: number): Side {
  const value = trailingReturn(series, index, 126)
  if (value == null || value === 0) return 0
  return value > 0 ? 1 : -1
}

export function sign6and12Side(series: Series, index: number): Side {
  const six = trailingReturn(series, index, 126)
  const year = trailingReturn(series, index, 252)
  if (six == null || year == null) return 0
  if (six > 0 && year > 0) return 1
  if (six < 0 && year < 0) return -1
  return 0
}

export function channelSide(series: Series, index: number, sessions: number): Side {
  const high = priorMaxHigh(series, index, sessions)
  const low = priorMinLow(series, index, sessions)
  const price = series.adj[index]
  if (!(price > 0) || high == null || low == null) return 0
  if (price > high) return 1
  if (price < low) return -1
  return 0
}

export function crossSide(series: Series, index: number): Side {
  const fast = sma(series, index, 50)
  const slow = sma(series, index, 200)
  if (fast == null || slow == null || fast === slow) return 0
  return fast > slow ? 1 : -1
}

export function yearSide(series: Series, index: number): Side {
  return channelSide(series, index, 252)
}

/** Past `sessions` daily simple returns, standard deviation. Not annualized. */
export function realizedVol(series: Series, index: number, sessions = 60): number | null {
  if (index - sessions < 0) return null
  let sum = 0
  let sum2 = 0
  let count = 0
  for (let cursor = index - sessions + 1; cursor <= index; cursor += 1) {
    const value = trailingReturn(series, cursor, 1)
    if (value == null) continue
    sum += value
    sum2 += value * value
    count += 1
  }
  if (count < Math.floor(sessions * 0.8)) return null
  const mean = sum / count
  const variance = sum2 / count - mean * mean
  if (!(variance > 0)) return null
  return Math.sqrt(variance)
}

/** A score in [-1, 1] over volatility, then gross exposure scaled to 1. */
export function scoreWeights(entries: Array<{ symbol: string; score: number; vol: number }>): Map<string, number> {
  const weights = new Map<string, number>()
  let gross = 0
  const raw: Array<{ symbol: string; weight: number }> = []
  for (const entry of entries) {
    if (!Number.isFinite(entry.score) || entry.score === 0 || !(entry.vol > 0)) continue
    const weight = entry.score / entry.vol
    raw.push({ symbol: entry.symbol, weight })
    gross += Math.abs(weight)
  }
  if (!(gross > 0)) return weights
  for (const entry of raw) weights.set(entry.symbol, entry.weight / gross)
  return weights
}

/** Sign over volatility, then gross exposure scaled to 1. An all-long tape is fully long. */
export function volScaledWeights(entries: Array<{ symbol: string; side: Side; vol: number }>): Map<string, number> {
  const weights = new Map<string, number>()
  let gross = 0
  const raw: Array<{ symbol: string; weight: number }> = []
  for (const entry of entries) {
    if (entry.side === 0 || !(entry.vol > 0)) continue
    const weight = entry.side / entry.vol
    raw.push({ symbol: entry.symbol, weight })
    gross += Math.abs(weight)
  }
  if (!(gross > 0)) return weights
  for (const entry of raw) weights.set(entry.symbol, entry.weight / gross)
  return weights
}

export function priorMinLow(series: Series, index: number, sessions: number): number | null {
  if (sessions < 1 || index - sessions < 0) return null
  let lowest = Infinity
  let count = 0
  for (let cursor = index - sessions; cursor <= index - 1; cursor += 1) {
    const low = adjustedLow(series, cursor)
    if (low == null) continue
    lowest = Math.min(lowest, low)
    count += 1
  }
  if (count < Math.floor(sessions * 0.8)) return null
  return lowest
}

export function compoundBlocks(returns: number[], every: number): number[] {
  const out: number[] = []
  if (every < 1) return out
  for (let start = 0; start + every <= returns.length; start += every) {
    let equity = 1
    let ok = true
    for (let step = 0; step < every; step += 1) {
      const value = returns[start + step]
      if (!Number.isFinite(value)) {
        ok = false
        break
      }
      equity *= 1 + value
    }
    if (ok) out.push(equity - 1)
  }
  return out
}

export function iidT(values: number[]): { n: number; mean: number; t: number } | null {
  const used = values.filter((value) => Number.isFinite(value))
  if (used.length < 8) return null
  const mean = used.reduce((sum, value) => sum + value, 0) / used.length
  let square = 0
  for (const value of used) square += (value - mean) ** 2
  const variance = square / (used.length - 1)
  if (!(variance > 0)) return null
  const se = Math.sqrt(variance / used.length)
  return { n: used.length, mean, t: mean / se }
}

/** Bartlett-kernel t-stat. Lag is in observations of the same series. */
export function neweyWestT(values: number[], lag: number): { n: number; mean: number; t: number } | null {
  const used = values.filter((value) => Number.isFinite(value))
  const count = used.length
  if (count < lag + 5 || lag < 0) return null
  const mean = used.reduce((sum, value) => sum + value, 0) / count
  const error = used.map((value) => value - mean)
  let variance = 0
  for (const value of error) variance += value * value
  variance /= count
  for (let step = 1; step <= lag; step += 1) {
    let gamma = 0
    for (let index = step; index < count; index += 1) gamma += error[index] * error[index - step]
    gamma /= count
    variance += 2 * (1 - step / (lag + 1)) * gamma
  }
  if (!(variance > 0)) return null
  const se = Math.sqrt(variance / count)
  return { n: count, mean, t: mean / se }
}

export function olsBeta(left: number[], right: number[]): number | null {
  const count = Math.min(left.length, right.length)
  let sumX = 0
  let sumY = 0
  let sumXX = 0
  let sumXY = 0
  let used = 0
  for (let index = 0; index < count; index += 1) {
    const x = right[index]
    const y = left[index]
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue
    sumX += x
    sumY += y
    sumXX += x * x
    sumXY += x * y
    used += 1
  }
  if (used < 20) return null
  const variance = sumXX / used - (sumX / used) ** 2
  if (!(variance > 0)) return null
  return (sumXY / used - (sumX / used) * (sumY / used)) / variance
}

export type DatedSlope = { a: number; b: number[] }

/** Ordinary least squares of y on a constant and the columns of x. A column with no variation returns null. */
export function olsFit(y: number[], columns: number[][]): DatedSlope | null {
  const rows = y.length
  const regressors = columns.length
  if (rows < regressors + 2) return null
  for (const column of columns) {
    if (column.length !== rows) return null
    const first = column[0]
    if (!column.some((value) => value !== first && Number.isFinite(value))) return null
  }
  const width = regressors + 1
  const xtx: number[][] = Array.from({ length: width }, () => Array.from({ length: width }, () => 0))
  const xty: number[] = Array.from({ length: width }, () => 0)
  for (let row = 0; row < rows; row += 1) {
    if (!Number.isFinite(y[row])) return null
    const point = [1, ...columns.map((column) => column[row])]
    if (point.some((value) => !Number.isFinite(value))) return null
    for (let col = 0; col < width; col += 1) {
      xty[col] += point[col] * y[row]
      for (let other = 0; other < width; other += 1) xtx[col][other] += point[col] * point[other]
    }
  }
  const beta = solve(xtx, xty)
  if (!beta) return null
  return { a: beta[0], b: beta.slice(1) }
}

function solve(matrix: number[][], target: number[]): number[] | null {
  const size = target.length
  const a = matrix.map((row, index) => [...row, target[index]])
  for (let col = 0; col < size; col += 1) {
    let pivot = col
    for (let row = col + 1; row < size; row += 1) if (Math.abs(a[row][col]) > Math.abs(a[pivot][col])) pivot = row
    if (!(Math.abs(a[pivot][col]) > 1e-12)) return null
    const swap = a[col]
    a[col] = a[pivot]
    a[pivot] = swap
    const scale = a[col][col]
    for (let other = col; other <= size; other += 1) a[col][other] /= scale
    for (let row = 0; row < size; row += 1) {
      if (row === col) continue
      const factor = a[row][col]
      for (let other = col; other <= size; other += 1) a[row][other] -= factor * a[col][other]
    }
  }
  return a.map((row) => row[size])
}

/** Average of date-by-date slopes. The t-stat is across dates, which is the dependence that matters. */
export function famaMacBeth(slopes: number[][]): { n: number; mean: number[]; t: number[] } | null {
  const used = slopes.filter((row) => row.length > 0 && row.every((value) => Number.isFinite(value)))
  if (used.length < 8) return null
  const width = used[0].length
  if (used.some((row) => row.length !== width)) return null
  const mean: number[] = []
  const t: number[] = []
  for (let col = 0; col < width; col += 1) {
    const values = used.map((row) => row[col])
    const avg = values.reduce((sum, value) => sum + value, 0) / values.length
    let square = 0
    for (const value of values) square += (value - avg) ** 2
    const variance = square / (values.length - 1)
    mean.push(avg)
    t.push(variance > 0 ? avg / Math.sqrt(variance / values.length) : avg === 0 ? 0 : Number.POSITIVE_INFINITY)
  }
  return { n: used.length, mean, t }
}

export function pearson(left: number[], right: number[]): number | null {
  const count = Math.min(left.length, right.length)
  if (count < 3) return null
  let sumX = 0
  let sumY = 0
  let sumXX = 0
  let sumYY = 0
  let sumXY = 0
  let used = 0
  for (let index = 0; index < count; index += 1) {
    const x = left[index]
    const y = right[index]
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue
    sumX += x
    sumY += y
    sumXX += x * x
    sumYY += y * y
    sumXY += x * y
    used += 1
  }
  if (used < 3) return null
  const cov = sumXY / used - (sumX / used) * (sumY / used)
  const vx = sumXX / used - (sumX / used) ** 2
  const vy = sumYY / used - (sumY / used) ** 2
  if (!(vx > 0) || !(vy > 0)) return null
  return cov / Math.sqrt(vx * vy)
}
