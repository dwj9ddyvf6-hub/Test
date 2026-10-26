import type { Quote } from "./types";
import { CATALOG_TICKERS, ETF_TICKERS } from "./catalog.mjs";
import { sectorOf } from "./sectors.mjs";

export type SymbolMeta = {
  ticker: string;
  name: string;
  sector: string;
  kind: "stock" | "etf";
  base: number;
  atrPct: number;
  avgVolume: number;
};

const SEED: SymbolMeta[] = [
  { ticker: "AAPL", name: "Apple", sector: "Technology", kind: "stock", base: 228.4, atrPct: 1.6, avgVolume: 52_000_000 },
  { ticker: "MSFT", name: "Microsoft", sector: "Technology", kind: "stock", base: 428.1, atrPct: 1.4, avgVolume: 22_000_000 },
  { ticker: "NVDA", name: "NVIDIA", sector: "Semiconductors", kind: "stock", base: 131.2, atrPct: 2.8, avgVolume: 180_000_000 },
  { ticker: "AMZN", name: "Amazon", sector: "Consumer", kind: "stock", base: 186.7, atrPct: 1.9, avgVolume: 38_000_000 },
  { ticker: "GOOGL", name: "Alphabet", sector: "Technology", kind: "stock", base: 172.3, atrPct: 1.8, avgVolume: 28_000_000 },
  { ticker: "META", name: "Meta Platforms", sector: "Technology", kind: "stock", base: 548.9, atrPct: 2.1, avgVolume: 14_000_000 },
  { ticker: "AVGO", name: "Broadcom", sector: "Semiconductors", kind: "stock", base: 182.6, atrPct: 2.6, avgVolume: 21_000_000 },
  { ticker: "AMD", name: "AMD", sector: "Semiconductors", kind: "stock", base: 466.4, atrPct: 3.2, avgVolume: 45_000_000 },
  { ticker: "TSM", name: "TSMC", sector: "Semiconductors", kind: "stock", base: 180.0, atrPct: 2.4, avgVolume: 12_000_000 },
  { ticker: "MU", name: "Micron", sector: "Semiconductors", kind: "stock", base: 120.0, atrPct: 3.0, avgVolume: 20_000_000 },
  { ticker: "AMAT", name: "Applied Materials", sector: "Semiconductors", kind: "stock", base: 180.0, atrPct: 2.4, avgVolume: 6_000_000 },
  { ticker: "LRCX", name: "Lam Research", sector: "Semiconductors", kind: "stock", base: 90.0, atrPct: 2.6, avgVolume: 5_000_000 },
  { ticker: "QCOM", name: "Qualcomm", sector: "Semiconductors", kind: "stock", base: 160.0, atrPct: 2.2, avgVolume: 8_000_000 },
  { ticker: "SOXX", name: "iShares Semiconductor ETF", sector: "Semiconductors", kind: "etf", base: 250.0, atrPct: 2.2, avgVolume: 4_000_000 },
  { ticker: "JPM", name: "JPMorgan Chase", sector: "Financials", kind: "stock", base: 216.9, atrPct: 1.5, avgVolume: 9_200_000 },
  { ticker: "BAC", name: "Bank of America", sector: "Financials", kind: "stock", base: 40.0, atrPct: 1.6, avgVolume: 40_000_000 },
  { ticker: "GS", name: "Goldman Sachs", sector: "Financials", kind: "stock", base: 500.0, atrPct: 1.8, avgVolume: 2_200_000 },
  { ticker: "COST", name: "Costco", sector: "Consumer", kind: "stock", base: 918.5, atrPct: 1.3, avgVolume: 2_100_000 },
  { ticker: "UNH", name: "UnitedHealth", sector: "Healthcare", kind: "stock", base: 312.4, atrPct: 1.7, avgVolume: 6_400_000 },
  { ticker: "LLY", name: "Eli Lilly", sector: "Healthcare", kind: "stock", base: 764.2, atrPct: 2.2, avgVolume: 3_400_000 },
  { ticker: "V", name: "Visa", sector: "Financials", kind: "stock", base: 342.8, atrPct: 1.2, avgVolume: 6_100_000 },
  { ticker: "MA", name: "Mastercard", sector: "Financials", kind: "stock", base: 518.1, atrPct: 1.3, avgVolume: 2_600_000 },
  { ticker: "HD", name: "Home Depot", sector: "Consumer", kind: "stock", base: 398.6, atrPct: 1.5, avgVolume: 3_300_000 },
  { ticker: "WMT", name: "Walmart", sector: "Consumer", kind: "stock", base: 98.4, atrPct: 1.1, avgVolume: 16_000_000 },
  { ticker: "XOM", name: "Exxon Mobil", sector: "Energy", kind: "stock", base: 114.2, atrPct: 1.6, avgVolume: 14_000_000 },
  { ticker: "CVX", name: "Chevron", sector: "Energy", kind: "stock", base: 150.0, atrPct: 1.5, avgVolume: 8_000_000 },
  { ticker: "KO", name: "Coca-Cola", sector: "Consumer", kind: "stock", base: 70.0, atrPct: 1.1, avgVolume: 14_000_000 },
  { ticker: "PEP", name: "PepsiCo", sector: "Consumer", kind: "stock", base: 170.0, atrPct: 1.2, avgVolume: 6_000_000 },
  { ticker: "DIS", name: "Disney", sector: "Consumer", kind: "stock", base: 110.0, atrPct: 1.8, avgVolume: 10_000_000 },
  { ticker: "PFE", name: "Pfizer", sector: "Healthcare", kind: "stock", base: 25.0, atrPct: 1.7, avgVolume: 30_000_000 },
  { ticker: "ABBV", name: "AbbVie", sector: "Healthcare", kind: "stock", base: 180.0, atrPct: 1.5, avgVolume: 6_000_000 },
  { ticker: "BA", name: "Boeing", sector: "Industrials", kind: "stock", base: 180.0, atrPct: 2.2, avgVolume: 8_000_000 },
  { ticker: "NFLX", name: "Netflix", sector: "Technology", kind: "stock", base: 700.0, atrPct: 2.4, avgVolume: 4_000_000 },
  { ticker: "ORCL", name: "Oracle", sector: "Technology", kind: "stock", base: 140.0, atrPct: 2.0, avgVolume: 10_000_000 },
  { ticker: "CAT", name: "Caterpillar", sector: "Industrials", kind: "stock", base: 386.5, atrPct: 1.8, avgVolume: 2_800_000 },
  { ticker: "GE", name: "GE Aerospace", sector: "Industrials", kind: "stock", base: 196.8, atrPct: 1.9, avgVolume: 5_100_000 },
  { ticker: "HON", name: "Honeywell", sector: "Industrials", kind: "stock", base: 224.1, atrPct: 1.4, avgVolume: 2_900_000 },
  { ticker: "RTX", name: "RTX", sector: "Industrials", kind: "stock", base: 148.3, atrPct: 1.5, avgVolume: 5_400_000 },
  { ticker: "SPY", name: "S&P 500 ETF", sector: "Broad", kind: "etf", base: 562.4, atrPct: 0.9, avgVolume: 62_000_000 },
  { ticker: "QQQ", name: "Nasdaq 100 ETF", sector: "Technology", kind: "etf", base: 492.8, atrPct: 1.2, avgVolume: 38_000_000 },
  { ticker: "IWM", name: "Russell 2000 ETF", sector: "Broad", kind: "etf", base: 218.6, atrPct: 1.5, avgVolume: 28_000_000 },
  { ticker: "DIA", name: "Dow Jones ETF", sector: "Broad", kind: "etf", base: 438.2, atrPct: 0.8, avgVolume: 3_800_000 },
  { ticker: "XLK", name: "Technology Select", sector: "Technology", kind: "etf", base: 251.1, atrPct: 1.3, avgVolume: 6_200_000 },
  { ticker: "XLF", name: "Financial Select", sector: "Financials", kind: "etf", base: 48.7, atrPct: 1.1, avgVolume: 38_000_000 },
  { ticker: "XLE", name: "Energy Select", sector: "Energy", kind: "etf", base: 91.4, atrPct: 1.6, avgVolume: 14_000_000 },
  { ticker: "XLI", name: "Industrial Select", sector: "Industrials", kind: "etf", base: 182.3, atrPct: 1.0, avgVolume: 8_400_000 },
  { ticker: "XLU", name: "Utilities Select", sector: "Utilities", kind: "etf", base: 74.2, atrPct: 1.0, avgVolume: 12_000_000 },
  { ticker: "XLV", name: "Health Care Select", sector: "Healthcare", kind: "etf", base: 146.2, atrPct: 1.0, avgVolume: 7_100_000 },
  { ticker: "SMH", name: "Semiconductor ETF", sector: "Semiconductors", kind: "etf", base: 268.9, atrPct: 2.2, avgVolume: 7_800_000 },
  { ticker: "ICLN", name: "Clean Energy ETF", sector: "Clean Energy", kind: "etf", base: 14.8, atrPct: 2.4, avgVolume: 3_200_000 },
  { ticker: "TAN", name: "Solar ETF", sector: "Clean Energy", kind: "etf", base: 38.4, atrPct: 2.6, avgVolume: 1_100_000 },
  { ticker: "CRM", name: "Salesforce", sector: "Technology", kind: "stock", base: 278.4, atrPct: 2.0, avgVolume: 6_800_000 },
  { ticker: "ADBE", name: "Adobe", sector: "Technology", kind: "stock", base: 492.1, atrPct: 1.9, avgVolume: 3_400_000 },
  { ticker: "NOW", name: "ServiceNow", sector: "Technology", kind: "stock", base: 812.6, atrPct: 2.1, avgVolume: 1_600_000 },
  { ticker: "INTU", name: "Intuit", sector: "Technology", kind: "stock", base: 628.3, atrPct: 1.8, avgVolume: 1_400_000 },
  { ticker: "CRWD", name: "CrowdStrike", sector: "Technology", kind: "stock", base: 318.7, atrPct: 2.7, avgVolume: 4_200_000 },
  { ticker: "PANW", name: "Palo Alto", sector: "Technology", kind: "stock", base: 186.2, atrPct: 2.3, avgVolume: 5_100_000 },
  { ticker: "TLT", name: "20+ Year Treasury", sector: "Rates", kind: "etf", base: 92.6, atrPct: 1.1, avgVolume: 32_000_000 },
  { ticker: "GLD", name: "Gold Trust", sector: "Metals", kind: "etf", base: 248.3, atrPct: 1.0, avgVolume: 6_400_000 },
  { ticker: "VNQ", name: "Real Estate ETF", sector: "Real Estate", kind: "etf", base: 92.1, atrPct: 1.2, avgVolume: 4_200_000 },
];

const SEED_SET = new Set(SEED.map((row) => row.ticker));

export const UNIVERSE: SymbolMeta[] = [
  ...SEED,
  ...CATALOG_TICKERS.filter((ticker) => !SEED_SET.has(ticker)).map((ticker) => ({
    ticker,
    name: ticker,
    sector: sectorOf(ticker, ETF_TICKERS.has(ticker) ? "etf" : "stock"),
    kind: ETF_TICKERS.has(ticker) ? ("etf" as const) : ("stock" as const),
    base: 40,
    atrPct: 2.4,
    avgVolume: 1_000_000,
  })),
];

export const byTicker = Object.fromEntries(UNIVERSE.map((s) => [s.ticker, s]));

export const MEGA_CAPS = new Set([
  "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "LLY", "UNH", "JPM", "V", "MA", "TSLA", "BRK",
]);

export const SECTORS = [...new Set(UNIVERSE.map((s) => s.sector))].sort();

export function hashSeed(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function initialQuotes(now = Date.now()): Record<string, Quote> {
  const quotes: Record<string, Quote> = {};
  for (const s of UNIVERSE) {
    const rng = mulberry32(hashSeed(`${s.ticker}:open`));
    const drift = (rng() - 0.42) * 0.012;
    const price = round2(s.base * (1 + drift));
    const prevClose = round2(s.base);
    const atr = round2(price * (s.atrPct / 100));
    const open = round2(prevClose * (1 + (rng() - 0.5) * 0.006));
    const high = round2(Math.max(price, open) + atr * (0.15 + rng() * 0.35));
    const low = round2(Math.min(price, open) - atr * (0.1 + rng() * 0.3));
    const support = round2(price - atr * (1.1 + rng() * 0.7));
    const resistance = round2(price + atr * (1.0 + rng() * 0.8));
    quotes[s.ticker] = {
      ticker: s.ticker,
      name: s.name,
      sector: s.sector,
      kind: s.kind,
      price,
      prevClose,
      open,
      high,
      low,
      volume: Math.round(s.avgVolume * (0.55 + rng() * 0.7)),
      avgVolume: s.avgVolume,
      support,
      resistance,
      vwap: round2((open + price + high + low) / 4),
      rsi: round1(44 + rng() * 28),
      macdHist: round2((rng() - 0.45) * 0.8),
      atr,
      extensionAtr: round2((price - support) / atr),
    };
  }
  void now;
  return quotes;
}

export type Bar = { t: number; o: number; h: number; l: number; c: number; v: number };

export function dailyBars(ticker: string, days = 90, lastClose?: number): Bar[] {
  const meta = byTicker[ticker] ?? {
    ticker,
    name: ticker,
    sector: "Unclassified",
    kind: "stock" as const,
    base: 40,
    atrPct: 2.4,
    avgVolume: 1_000_000,
  };
  const rng = mulberry32(hashSeed(`${ticker}:daily:v2`));
  const end = lastClose ?? meta.base;
  const bars: Bar[] = [];
  let price = end / (1 + (rng() - 0.48) * 0.18);
  const now = new Date();
  now.setHours(16, 0, 0, 0);
  const cursor = new Date(now);
  const raw: Array<{ o: number; h: number; l: number; c: number; v: number }> = [];
  for (let i = 0; i < days + 8; i += 1) {
    const ret = (rng() - 0.48) * (meta.atrPct / 100) * 1.6;
    const o = price;
    const c = Math.max(0.5, o * (1 + ret));
    const w = o * (meta.atrPct / 100) * (0.4 + rng() * 0.8);
    const h = Math.max(o, c) + w * rng();
    const l = Math.min(o, c) - w * rng();
    raw.push({
      o,
      h,
      l,
      c,
      v: Math.round(meta.avgVolume * (0.5 + rng())),
    });
    price = c;
  }
  const scale = end / raw[raw.length - 1]!.c;
  for (let i = raw.length - 1; i >= 0 && bars.length < days; i -= 1) {
    while (cursor.getDay() === 0 || cursor.getDay() === 6) cursor.setDate(cursor.getDate() - 1);
    const b = raw[i]!;
    bars.unshift({
      t: cursor.getTime(),
      o: round2(b.o * scale),
      h: round2(b.h * scale),
      l: round2(b.l * scale),
      c: round2(b.c * scale),
      v: b.v,
    });
    cursor.setDate(cursor.getDate() - 1);
  }
  return bars;
}

export function fiveMinuteBars(ticker: string, count = 78, lastClose?: number): Bar[] {
  const meta = byTicker[ticker] ?? {
    ticker,
    name: ticker,
    sector: "Unclassified",
    kind: "stock" as const,
    base: 40,
    atrPct: 2.4,
    avgVolume: 1_000_000,
  };
  const rng = mulberry32(hashSeed(`${ticker}:5m:v2`));
  const end = lastClose ?? meta.base;
  const bars: Bar[] = [];
  let price = end * (1 - (rng() - 0.5) * 0.012);
  const now = Date.now();
  const step = 5 * 60 * 1000;
  const raw: Array<{ o: number; h: number; l: number; c: number; v: number }> = [];
  for (let i = 0; i < count; i += 1) {
    const ret = (rng() - 0.49) * (meta.atrPct / 100) * 0.22;
    const o = price;
    const c = Math.max(0.5, o * (1 + ret));
    const w = o * (meta.atrPct / 100) * 0.12 * (0.4 + rng());
    raw.push({
      o,
      h: Math.max(o, c) + w * rng(),
      l: Math.min(o, c) - w * rng(),
      c,
      v: Math.round((meta.avgVolume / 78) * (0.4 + rng())),
    });
    price = c;
  }
  const scale = end / raw[raw.length - 1]!.c;
  for (let i = 0; i < raw.length; i += 1) {
    const b = raw[i]!;
    bars.push({
      t: now - (raw.length - 1 - i) * step,
      o: round2(b.o * scale),
      h: round2(b.h * scale),
      l: round2(b.l * scale),
      c: round2(b.c * scale),
      v: b.v,
    });
  }
  return bars;
}

export function round2(n: number) {
  return Math.round(n * 100) / 100;
}

export function round1(n: number) {
  return Math.round(n * 10) / 10;
}
