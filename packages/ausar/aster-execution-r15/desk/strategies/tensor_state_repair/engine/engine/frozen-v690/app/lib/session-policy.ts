import {
  canonicalVenue,
  venueHintFromSymbol,
} from "./instrument-identity.ts";

export type MarketPhase =
  | "premarket"
  | "regular"
  | "after-hours"
  | "closed";

export type SessionInstrumentKind =
  | "us-security"
  | "foreign-security"
  | "crypto"
  | "continuous"
  | "unknown";

export type TimedMarketRow = {
  time: number;
};

export type SessionPolicy = {
  instrumentType?: string | null;
  exchange?: string | null;
  symbol?: string | null;
  exchangeTimezone?: string | null;
};

export type ExchangeSessionProfile = {
  kind: SessionInstrumentKind;
  venue: string;
  timeZone: string;
  regularOpenMinutes: number;
  regularCloseMinutes: number;
  premarketOpenMinutes: number | null;
  extendedCloseMinutes: number | null;
};

export type ExchangeClock = {
  dateKey: string;
  weekday: string;
  minutes: number;
};

const DAY_MS = 86_400_000;
export const DAILY_BAR_FINALIZATION_GRACE_MINUTES = 15;
const SECURITY_TYPES = ["EQUITY", "ETF", "ADR", "MUTUALFUND", "INDEX"];
const US_SESSION_VENUES = new Set([
  "NASDAQ",
  "NYSE",
  "NYSEAMERICAN",
  "NYSEARCA",
  "OTC",
  "BATS",
  "CBOE",
  "CBOEBZX",
  "IEX",
]);

const FOREIGN_SESSION_PROFILES: Readonly<Record<
  string,
  Omit<ExchangeSessionProfile, "kind">
>> = {
  STOCKHOLM: {
    venue: "STOCKHOLM",
    timeZone: "Europe/Stockholm",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  XETRA: {
    venue: "XETRA",
    timeZone: "Europe/Berlin",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  GERMANY: {
    venue: "GERMANY",
    timeZone: "Europe/Berlin",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  FRANKFURT: {
    venue: "FRANKFURT",
    timeZone: "Europe/Berlin",
    regularOpenMinutes: 8 * 60,
    regularCloseMinutes: 20 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TRADEGATE: {
    venue: "TRADEGATE",
    timeZone: "Europe/Berlin",
    regularOpenMinutes: 8 * 60,
    regularCloseMinutes: 22 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  LSE: {
    venue: "LSE",
    timeZone: "Europe/London",
    regularOpenMinutes: 8 * 60,
    regularCloseMinutes: 16 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  SIX: {
    venue: "SIX",
    timeZone: "Europe/Zurich",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  EURONEXT: {
    venue: "EURONEXT",
    timeZone: "Europe/Paris",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  EURONEXTPARIS: {
    venue: "EURONEXTPARIS",
    timeZone: "Europe/Paris",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  EURONEXTAMSTERDAM: {
    venue: "EURONEXTAMSTERDAM",
    timeZone: "Europe/Amsterdam",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  EURONEXTBRUSSELS: {
    venue: "EURONEXTBRUSSELS",
    timeZone: "Europe/Brussels",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  EURONEXTLISBON: {
    venue: "EURONEXTLISBON",
    timeZone: "Europe/Lisbon",
    regularOpenMinutes: 8 * 60,
    regularCloseMinutes: 16 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  OSLO: {
    venue: "OSLO",
    timeZone: "Europe/Oslo",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 16 * 60 + 20,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  COPENHAGEN: {
    venue: "COPENHAGEN",
    timeZone: "Europe/Copenhagen",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  HELSINKI: {
    venue: "HELSINKI",
    timeZone: "Europe/Helsinki",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 18 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  MADRID: {
    venue: "MADRID",
    timeZone: "Europe/Madrid",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  MILAN: {
    venue: "MILAN",
    timeZone: "Europe/Rome",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  VIENNA: {
    venue: "VIENNA",
    timeZone: "Europe/Vienna",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  ASX: {
    venue: "ASX",
    timeZone: "Australia/Sydney",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 16 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TSX: {
    venue: "TSX",
    timeZone: "America/Toronto",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 16 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TSXV: {
    venue: "TSXV",
    timeZone: "America/Toronto",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 16 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  HKEX: {
    venue: "HKEX",
    timeZone: "Asia/Hong_Kong",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 16 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TSE: {
    venue: "TSE",
    timeZone: "Asia/Tokyo",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  KRX: {
    venue: "KRX",
    timeZone: "Asia/Seoul",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  KOSDAQ: {
    venue: "KOSDAQ",
    timeZone: "Asia/Seoul",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  NSE: {
    venue: "NSE",
    timeZone: "Asia/Kolkata",
    regularOpenMinutes: 9 * 60 + 15,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  BSE: {
    venue: "BSE",
    timeZone: "Asia/Kolkata",
    regularOpenMinutes: 9 * 60 + 15,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  SSE: {
    venue: "SSE",
    timeZone: "Asia/Shanghai",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 15 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  SZSE: {
    venue: "SZSE",
    timeZone: "Asia/Shanghai",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 15 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  NZX: {
    venue: "NZX",
    timeZone: "Pacific/Auckland",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 16 * 60 + 45,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TWSE: {
    venue: "TWSE",
    timeZone: "Asia/Taipei",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 13 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TPEX: {
    venue: "TPEX",
    timeZone: "Asia/Taipei",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 13 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  B3: {
    venue: "B3",
    timeZone: "America/Sao_Paulo",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  JSE: {
    venue: "JSE",
    timeZone: "Africa/Johannesburg",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  SGX: {
    venue: "SGX",
    timeZone: "Asia/Singapore",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  SET: {
    venue: "SET",
    timeZone: "Asia/Bangkok",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 16 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  IDX: {
    venue: "IDX",
    timeZone: "Asia/Jakarta",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 16 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  KLSE: {
    venue: "KLSE",
    timeZone: "Asia/Kuala_Lumpur",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  TASE: {
    venue: "TASE",
    timeZone: "Asia/Jerusalem",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 17 * 60 + 35,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  BIST: {
    venue: "BIST",
    timeZone: "Europe/Istanbul",
    regularOpenMinutes: 10 * 60,
    regularCloseMinutes: 18 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  MOEX: {
    venue: "MOEX",
    timeZone: "Europe/Moscow",
    regularOpenMinutes: 9 * 60 + 50,
    regularCloseMinutes: 18 * 60 + 50,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  WSE: {
    venue: "WSE",
    timeZone: "Europe/Warsaw",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60 + 5,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  BUD: {
    venue: "BUD",
    timeZone: "Europe/Budapest",
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
  PSE: {
    venue: "PSE",
    timeZone: "Asia/Manila",
    regularOpenMinutes: 9 * 60 + 30,
    regularCloseMinutes: 15 * 60 + 30,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  },
};
// FolioTend's longest provider window is ten years. NYSE's modern 1:00 p.m.
// early-close convention is stable throughout that supported history; keep the
// lower bound explicit so this calendar does not make claims about older eras.
const NYSE_MODERN_EARLY_CLOSE_POLICY_START_YEAR = 2016;
// Exchange-announced exceptions belong here so signal evaluation remains
// deterministic and never depends on a live calendar request.
const NYSE_EARLY_CLOSE_ADDITIONS = new Set<string>();
const NYSE_EARLY_CLOSE_REMOVALS = new Set<string>();

function dateKeyFromParts(parts: Intl.DateTimeFormatPart[]) {
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

// Formatters are immutable and carry no account data. Reuse a bounded set:
// constructing ICU formatters for every historical bar exhausts native memory.
const clockFormatters = new Map<string, Intl.DateTimeFormat>();
const ZONED_DATE_TIME_CACHE_LIMIT = 1_024;
const zonedDateTimeCache = new Map<string, string>();
const EXCHANGE_CLOCK_CACHE_LIMIT = 4_096;
const exchangeClockCache = new Map<string, ExchangeClock>();
const US_MARKET_HOLIDAY_CACHE_LIMIT = 32;
const usMarketHolidayCache = new Map<number, ReadonlySet<string>>();
const NYSE_EARLY_CLOSE_CANDIDATE_CACHE_LIMIT = 64;
const nyseEarlyCloseCandidateCache = new Map<number, ReadonlySet<string>>();
function clockFormatter(timeZone: string) {
  const cached=clockFormatters.get(timeZone);
  if(cached) return cached;
  const formatter=new Intl.DateTimeFormat("en-US", {
    timeZone,weekday:"short",year:"numeric",month:"2-digit",day:"2-digit",
    hour:"2-digit",minute:"2-digit",hourCycle:"h23",
  });
  if(clockFormatters.size>=32) clockFormatters.delete(clockFormatters.keys().next().value!);
  clockFormatters.set(timeZone,formatter);
  return formatter;
}

function validTimeZone(value: unknown) {
  const timeZone = String(value || "").trim();
  if (!timeZone) return null;
  try {
    clockFormatter(timeZone);
    return timeZone;
  } catch {
    return null;
  }
}

function clockInTimeZone(date: Date, timeZone: string): ExchangeClock {
  // The clock contract intentionally exposes minute precision only. Reuse
  // identical timezone/minute conversions across symbols while returning a
  // fresh object so callers cannot mutate shared cache state.
  const cacheKey = `${timeZone}\u0000${Math.floor(date.getTime() / 60_000)}`;
  const cached = exchangeClockCache.get(cacheKey);
  if (cached) return { ...cached };
  const parts = clockFormatter(timeZone).formatToParts(date);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const clock = {
    dateKey: dateKeyFromParts(parts),
    weekday: value.weekday,
    minutes: Number(value.hour) * 60 + Number(value.minute),
  };
  if (exchangeClockCache.size >= EXCHANGE_CLOCK_CACHE_LIMIT)
    exchangeClockCache.delete(exchangeClockCache.keys().next().value!);
  exchangeClockCache.set(cacheKey, { ...clock });
  return clock;
}

export function newYorkClock(date = new Date()): ExchangeClock {
  return clockInTimeZone(date, "America/New_York");
}

/** Convert a civil date/minute in any supported IANA timezone to UTC. */
export function zonedDateTimeUtc(
  dateKey: string,
  minutes: number,
  timeZone: string,
) {
  const match = dateKey.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const resolvedTimeZone = validTimeZone(timeZone);
  if (
    !match ||
    !resolvedTimeZone ||
    !Number.isInteger(minutes) ||
    minutes < 0 ||
    minutes >= 1440
  )
    throw new Error("A valid date, minute, and IANA timezone are required.");
  const cacheKey = `${resolvedTimeZone}\u0000${dateKey}\u0000${minutes}`;
  const cached = zonedDateTimeCache.get(cacheKey);
  if (cached) return cached;
  const targetParts = {
    year: Number(match[1]),
    month: Number(match[2]),
    day: Number(match[3]),
    hour: Math.floor(minutes / 60),
    minute: minutes % 60,
  };
  const targetAsUtc = Date.UTC(
    targetParts.year,
    targetParts.month - 1,
    targetParts.day,
    targetParts.hour,
    targetParts.minute,
  );
  // An initial UTC guess is enough for the iterative offset correction below;
  // the loop then converges across DST transitions and half-hour zones.
  let instant = targetAsUtc;
  const formatter = clockFormatter(resolvedTimeZone);
  for (let iteration = 0; iteration < 4; iteration += 1) {
    const parts = Object.fromEntries(
      formatter
        .formatToParts(new Date(instant))
        .map((part) => [part.type, part.value]),
    );
    const observedAsUtc = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
    );
    const correction = targetAsUtc - observedAsUtc;
    instant += correction;
    if (Math.abs(correction) < 1_000) break;
  }
  const result = new Date(instant).toISOString();
  if (zonedDateTimeCache.size >= ZONED_DATE_TIME_CACHE_LIMIT)
    zonedDateTimeCache.delete(zonedDateTimeCache.keys().next().value!);
  zonedDateTimeCache.set(cacheKey, result);
  return result;
}

export function newYorkDateTimeUtc(
  dateKey: string,
  minutes: number,
) {
  return zonedDateTimeUtc(dateKey, minutes, "America/New_York");
}

export function marketPhase(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
): MarketPhase {
  const clock = newYorkClock(date);
  if (!isUsMarketDate(clock.dateKey, closedDates)) return "closed";
  const bounds = usMarketSessionBounds(clock.dateKey);
  if (clock.minutes >= 240 && clock.minutes < 570) return "premarket";
  if (
    clock.minutes >= 570 &&
    clock.minutes < bounds.regularCloseMinutes
  )
    return "regular";
  if (
    clock.minutes >= bounds.regularCloseMinutes &&
    clock.minutes < bounds.extendedCloseMinutes
  )
    return "after-hours";
  return "closed";
}

export function usMarketSessionBounds(dateKey: string) {
  const earlyClose = isScheduledNyseEarlyClose(dateKey);
  return {
    earlyClose,
    regularCloseMinutes: earlyClose ? 13 * 60 : 16 * 60,
    extendedCloseMinutes: earlyClose ? 17 * 60 : 20 * 60,
  };
}

function isScheduledNyseEarlyClose(dateKey: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/u.exec(dateKey);
  if (!match) return false;
  const year = Number(match[1]);
  if (year < NYSE_MODERN_EARLY_CLOSE_POLICY_START_YEAR) return false;
  if (NYSE_EARLY_CLOSE_REMOVALS.has(dateKey)) return false;
  if (NYSE_EARLY_CLOSE_ADDITIONS.has(dateKey))
    return isUsMarketDate(dateKey);

  // NYSE's published calendars identify three recurring half-day candidates:
  // July 3, the Friday after Thanksgiving, and Christmas Eve. They are early
  // closes only when they are themselves trading days; weekend and observed
  // full-holiday collisions stay closed through isUsMarketDate below.
  let candidates = nyseEarlyCloseCandidateCache.get(year);
  if (!candidates) {
    candidates = new Set([
      utcDateKeyFromParts(year, 6, 3),
      addDateKeyDays(nthWeekday(year, 10, 4, 4), 1),
      utcDateKeyFromParts(year, 11, 24),
    ]);
    if (nyseEarlyCloseCandidateCache.size >= NYSE_EARLY_CLOSE_CANDIDATE_CACHE_LIMIT)
      nyseEarlyCloseCandidateCache.delete(nyseEarlyCloseCandidateCache.keys().next().value!);
    nyseEarlyCloseCandidateCache.set(year, candidates);
  }
  const scheduled = candidates.has(dateKey);
  // A candidate that is a weekend or an observed full holiday must remain
  // closed; it must never be converted into a shortened trading session.
  return scheduled && isUsMarketDate(dateKey);
}

function utcDateKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

function addDateKeyDays(dateKey: string, days: number) {
  const date = new Date(`${dateKey}T12:00:00.000Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return utcDateKey(date);
}

const weekdayFormatter=new Intl.DateTimeFormat("en-US", {timeZone:"UTC",weekday:"short"});
function weekdayForDateKey(dateKey: string) {
  return weekdayFormatter.format(new Date(`${dateKey}T12:00:00.000Z`));
}

function utcDateKeyFromParts(year: number, month: number, day: number) {
  return new Date(Date.UTC(year, month, day)).toISOString().slice(0, 10);
}

function observedFixedHoliday(year: number, month: number, day: number) {
  const date = new Date(Date.UTC(year, month, day));
  const weekday = date.getUTCDay();
  if (weekday === 6) date.setUTCDate(date.getUTCDate() - 1);
  if (weekday === 0) date.setUTCDate(date.getUTCDate() + 1);
  return utcDateKey(date);
}

function observedNewYearsDay(year: number) {
  const date = new Date(Date.UTC(year, 0, 1));
  if (date.getUTCDay() === 6) return null;
  if (date.getUTCDay() === 0) date.setUTCDate(2);
  return utcDateKey(date);
}

function nthWeekday(
  year: number,
  month: number,
  weekday: number,
  occurrence: number,
) {
  const first = new Date(Date.UTC(year, month, 1));
  const offset = (weekday - first.getUTCDay() + 7) % 7;
  return utcDateKeyFromParts(year, month, 1 + offset + (occurrence - 1) * 7);
}

function lastWeekday(year: number, month: number, weekday: number) {
  const last = new Date(Date.UTC(year, month + 1, 0));
  last.setUTCDate(
    last.getUTCDate() - ((last.getUTCDay() - weekday + 7) % 7),
  );
  return utcDateKey(last);
}

function easterSunday(year: number) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31) - 1;
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month, day));
}

function usMarketHolidayDates(year: number) {
  const cached = usMarketHolidayCache.get(year);
  if (cached) return cached;
  const easter = easterSunday(year);
  easter.setUTCDate(easter.getUTCDate() - 2);
  const dates = [
    nthWeekday(year, 0, 1, 3),
    nthWeekday(year, 1, 1, 3),
    utcDateKey(easter),
    lastWeekday(year, 4, 1),
    observedFixedHoliday(year, 5, 19),
    observedFixedHoliday(year, 6, 4),
    nthWeekday(year, 8, 1, 1),
    nthWeekday(year, 10, 4, 4),
    observedFixedHoliday(year, 11, 25),
  ];
  const newYearsDay = observedNewYearsDay(year);
  if (newYearsDay) dates.push(newYearsDay);
  const holidays = new Set(dates);
  if (usMarketHolidayCache.size >= US_MARKET_HOLIDAY_CACHE_LIMIT)
    usMarketHolidayCache.delete(usMarketHolidayCache.keys().next().value!);
  usMarketHolidayCache.set(year, holidays);
  return holidays;
}

function isUsMarketHoliday(dateKey: string) {
  const year = Number(dateKey.slice(0, 4));
  if (!Number.isInteger(year)) return false;
  return (
    usMarketHolidayDates(year).has(dateKey) ||
    usMarketHolidayDates(year + 1).has(dateKey)
  );
}

export function isUsMarketDate(
  dateKey: string,
  closedDates: ReadonlySet<string> = new Set(),
) {
  const weekday = weekdayForDateKey(dateKey);
  return (
    weekday !== "Sat" &&
    weekday !== "Sun" &&
    !isUsMarketHoliday(dateKey) &&
    !closedDates.has(dateKey)
  );
}

function canonicalUsRegularSessionClose(
  value: string | null | undefined,
  closedDates: ReadonlySet<string>,
) {
  const timestamp = Date.parse(String(value || ""));
  if (!Number.isFinite(timestamp)) return null;
  const dateKey = newYorkClock(new Date(timestamp)).dateKey;
  if (!isUsMarketDate(dateKey, closedDates)) return null;
  const canonicalAt = newYorkDateTimeUtc(
    dateKey,
    usMarketSessionBounds(dateKey).regularCloseMinutes,
  );
  if (timestamp !== Date.parse(canonicalAt)) return null;
  return { dateKey, timestamp };
}

/**
 * Validates a retained US regular-session close against a later close using
 * New York calendar dates. Civil-date age, rather than elapsed milliseconds,
 * keeps an exact seven-day window stable across 167-hour spring-forward and
 * 169-hour fall-back weeks. Both endpoints must be actual canonical closes,
 * including the scheduled early-close time when applicable.
 */
export function isUsRegularSessionCloseWithinCalendarDays({
  targetBarAt,
  ceilingBarAt,
  maxCalendarDays,
  closedDates = new Set<string>(),
}: {
  targetBarAt: string | null | undefined;
  ceilingBarAt: string | null | undefined;
  maxCalendarDays: number;
  closedDates?: ReadonlySet<string>;
}) {
  if (!Number.isInteger(maxCalendarDays) || maxCalendarDays < 0)
    return false;
  const target = canonicalUsRegularSessionClose(
    targetBarAt,
    closedDates,
  );
  const ceiling = canonicalUsRegularSessionClose(
    ceilingBarAt,
    closedDates,
  );
  if (!target || !ceiling) return false;
  const targetDay = Date.parse(`${target.dateKey}T00:00:00.000Z`);
  const ceilingDay = Date.parse(`${ceiling.dateKey}T00:00:00.000Z`);
  const calendarDays = (ceilingDay - targetDay) / DAY_MS;
  return calendarDays >= 0 && calendarDays <= maxCalendarDays;
}

export function isExchangeRegularSessionCloseWithinCalendarDays({
  targetBarAt,
  ceilingBarAt,
  maxCalendarDays,
  policy = {},
  closedDates = new Set<string>(),
}: {
  targetBarAt: string | null | undefined;
  ceilingBarAt: string | null | undefined;
  maxCalendarDays: number;
  policy?: SessionPolicy;
  closedDates?: ReadonlySet<string>;
}) {
  if (!Number.isInteger(maxCalendarDays) || maxCalendarDays < 0) return false;
  const profile = exchangeSessionProfile(policy);
  if (
    !profile ||
    (profile.kind !== "us-security" && profile.kind !== "foreign-security")
  ) return false;
  const canonical = (value: string | null | undefined) => {
    const timestamp = Date.parse(String(value || ""));
    if (!Number.isFinite(timestamp)) return null;
    const clock = exchangeClock(new Date(timestamp), policy);
    if (!isExchangeMarketDate(clock.dateKey, policy, closedDates)) return null;
    const closeAt = exchangeDateTimeUtc(
      clock.dateKey,
      profile.regularCloseMinutes,
      policy,
    );
    return closeAt && Date.parse(closeAt) === timestamp
      ? { dateKey: clock.dateKey, timestamp }
      : null;
  };
  const target = canonical(targetBarAt);
  const ceiling = canonical(ceilingBarAt);
  if (!target || !ceiling) return false;
  const calendarDays = (
    Date.parse(`${ceiling.dateKey}T00:00:00.000Z`) -
    Date.parse(`${target.dateKey}T00:00:00.000Z`)
  ) / DAY_MS;
  return calendarDays >= 0 && calendarDays <= maxCalendarDays;
}

export function previousUsMarketDate(
  dateKey: string,
  closedDates: ReadonlySet<string> = new Set(),
) {
  let candidate = addDateKeyDays(dateKey, -1);
  while (!isUsMarketDate(candidate, closedDates))
    candidate = addDateKeyDays(candidate, -1);
  return candidate;
}

export function nextUsMarketDate(
  dateKey: string,
  closedDates: ReadonlySet<string> = new Set(),
) {
  let candidate = addDateKeyDays(dateKey, 1);
  while (!isUsMarketDate(candidate, closedDates))
    candidate = addDateKeyDays(candidate, 1);
  return candidate;
}

export function expectedLatestUsQuoteDate(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
) {
  const clock = newYorkClock(date);
  const phase = marketPhase(date, closedDates);
  if (phase === "regular" || phase === "after-hours") return clock.dateKey;
  if (
    phase === "closed" &&
    isUsMarketDate(clock.dateKey, closedDates) &&
    clock.minutes >= usMarketSessionBounds(clock.dateKey).regularCloseMinutes
  )
    return clock.dateKey;
  return previousUsMarketDate(clock.dateKey, closedDates);
}

export function expectedLatestCompletedUsSessionDate(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
) {
  const clock = newYorkClock(date);
  const bounds = usMarketSessionBounds(clock.dateKey);
  if (
    isUsMarketDate(clock.dateKey, closedDates) &&
    clock.minutes >=
      bounds.regularCloseMinutes + DAILY_BAR_FINALIZATION_GRACE_MINUTES
  )
    return clock.dateKey;
  return previousUsMarketDate(clock.dateKey, closedDates);
}

export function watchlistDevelopmentWindow(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
) {
  const clock = newYorkClock(date);
  const phase = marketPhase(date, closedDates);
  const startDateKey =
    phase === "after-hours" ||
    (phase === "closed" &&
      isUsMarketDate(clock.dateKey, closedDates) &&
      clock.minutes >= usMarketSessionBounds(clock.dateKey).regularCloseMinutes)
      ? clock.dateKey
      : previousUsMarketDate(clock.dateKey, closedDates);
  const startAt = newYorkDateTimeUtc(
    startDateKey,
    usMarketSessionBounds(startDateKey).regularCloseMinutes,
  );
  return {
    phase,
    startDateKey,
    startAt,
    boundary: "regular-close" as const,
  };
}

function normalizedInstrumentType(value: unknown) {
  return String(value || "").toUpperCase().replace(/[^A-Z]/g, "");
}

function normalizedVenue(value: unknown) {
  return canonicalVenue(value);
}

function isSecurityType(type: string) {
  return !type || SECURITY_TYPES.some(value => type.includes(value));
}

function profileForVenue(venue: string, kind: SessionInstrumentKind) {
  const profile = FOREIGN_SESSION_PROFILES[venue];
  return profile ? { ...profile, kind } : null;
}

function profileForTimezone(
  timeZone: string,
  venue: string,
  kind: SessionInstrumentKind,
) {
  const normalized = timeZone.toUpperCase();
  if (normalized === "AMERICA/NEW_YORK" || normalized === "US/EASTERN")
    return {
      kind: "us-security",
      venue: venue || "US",
      timeZone: "America/New_York",
      regularOpenMinutes: 9 * 60 + 30,
      regularCloseMinutes: 16 * 60,
      premarketOpenMinutes: 4 * 60,
      extendedCloseMinutes: 20 * 60,
    } satisfies ExchangeSessionProfile;
  return {
    kind,
    venue: venue || "OTHER",
    timeZone,
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
    premarketOpenMinutes: null,
    extendedCloseMinutes: null,
  } satisfies ExchangeSessionProfile;
}

/**
 * Resolve the calendar used by a market-data identity. Exchange metadata is
 * authoritative; the symbol suffix is a safe fallback for an as-yet
 * unresolved listing, and a valid provider timezone covers other major
 * venues without pretending they trade on the New York clock.
 */
export function exchangeSessionProfile(
  policy: SessionPolicy = {},
): ExchangeSessionProfile | null {
  const type = normalizedInstrumentType(policy.instrumentType);
  const symbol = String(policy.symbol || "").trim().toUpperCase();
  const venue = normalizedVenue(policy.exchange || venueHintFromSymbol(symbol));
  if (type.includes("CRYPTO") || symbol.endsWith("-USD"))
    return {
      kind: "crypto",
      venue: venue || "CRYPTO",
      timeZone: "UTC",
      regularOpenMinutes: 0,
      regularCloseMinutes: 24 * 60,
      premarketOpenMinutes: null,
      extendedCloseMinutes: null,
    };
  if (
    type.includes("CURRENCY") ||
    type.includes("FUTURE") ||
    symbol.endsWith("=X") ||
    symbol.endsWith("=F")
  )
    return {
      kind: "continuous",
      venue: venue || "CONTINUOUS",
      timeZone: "UTC",
      regularOpenMinutes: 0,
      regularCloseMinutes: 24 * 60,
      premarketOpenMinutes: null,
      extendedCloseMinutes: null,
    };
  if (!isSecurityType(type)) return null;
  if (US_SESSION_VENUES.has(venue))
    return profileForTimezone(
      "America/New_York",
      venue,
      "us-security",
    );
  const foreign = profileForVenue(venue, "foreign-security");
  if (foreign) return foreign;
  const timeZone = validTimeZone(policy.exchangeTimezone);
  if (timeZone) return profileForTimezone(timeZone, venue, "foreign-security");
  return null;
}

export function sessionInstrumentKind(
  instrumentType: string | null = "",
  exchange: string | null = "",
  symbol: string | null = "",
  exchangeTimezone?: string | null,
): SessionInstrumentKind {
  return exchangeSessionProfile({
    instrumentType,
    exchange,
    symbol,
    exchangeTimezone,
  })?.kind || "unknown";
}

/** Resolve a venue-local phase without leaking New York session labels into
 * foreign listings. Foreign venues intentionally expose only regular/closed
 * because the provider feed does not carry a verified extended-hours contract
 * for those markets. */
export function exchangeMarketPhase(
  date = new Date(),
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
): MarketPhase {
  const profile = exchangeSessionProfile(policy);
  if (!profile || profile.kind === "us-security")
    return marketPhase(date, closedDates);
  if (profile.kind === "crypto" || profile.kind === "continuous")
    return "regular";
  const clock = exchangeClock(date, policy);
  const bounds = exchangeSessionBounds(clock.dateKey, policy);
  return bounds &&
      isExchangeMarketDate(clock.dateKey, policy, closedDates) &&
      clock.minutes >= bounds.regularOpenMinutes &&
      clock.minutes < bounds.regularCloseMinutes
    ? "regular"
    : "closed";
}

export function exchangeClock(
  date = new Date(),
  policy: SessionPolicy = {},
): ExchangeClock {
  const profile = exchangeSessionProfile(policy);
  return clockInTimeZone(date, profile?.timeZone || "America/New_York");
}

export function exchangeSessionBounds(
  dateKey: string,
  policy: SessionPolicy = {},
) {
  const profile = exchangeSessionProfile(policy);
  if (!profile) return null;
  if (profile.kind === "us-security") {
    const us = usMarketSessionBounds(dateKey);
    return {
      ...us,
      regularOpenMinutes: profile.regularOpenMinutes,
      premarketOpenMinutes: profile.premarketOpenMinutes,
    };
  }
  return {
    earlyClose: false,
    regularOpenMinutes: profile.regularOpenMinutes,
    regularCloseMinutes: profile.regularCloseMinutes,
    premarketOpenMinutes: profile.premarketOpenMinutes,
    extendedCloseMinutes: profile.extendedCloseMinutes,
  };
}

export function exchangeDateTimeUtc(
  dateKey: string,
  minutes: number,
  policy: SessionPolicy = {},
) {
  const profile = exchangeSessionProfile(policy);
  if (!profile) return null;
  return zonedDateTimeUtc(dateKey, minutes, profile.timeZone);
}

export function isExchangeMarketDate(
  dateKey: string,
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
) {
  const profile = exchangeSessionProfile(policy);
  if (!profile) return false;
  if (profile.kind === "us-security") return isUsMarketDate(dateKey, closedDates);
  if (profile.kind === "crypto" || profile.kind === "continuous") return true;
  const weekday = weekdayForDateKey(dateKey);
  return weekday !== "Sat" && weekday !== "Sun" && !closedDates.has(dateKey);
}

export function previousExchangeMarketDate(
  dateKey: string,
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
) {
  let candidate = addDateKeyDays(dateKey, -1);
  while (!isExchangeMarketDate(candidate, policy, closedDates))
    candidate = addDateKeyDays(candidate, -1);
  return candidate;
}

export function nextExchangeMarketDate(
  dateKey: string,
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
) {
  let candidate = addDateKeyDays(dateKey, 1);
  while (!isExchangeMarketDate(candidate, policy, closedDates))
    candidate = addDateKeyDays(candidate, 1);
  return candidate;
}

export function expectedLatestExchangeSessionDate(
  date = new Date(),
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
) {
  const profile = exchangeSessionProfile(policy);
  if (!profile) return null;
  if (profile.kind === "us-security")
    return expectedLatestUsQuoteDate(date, closedDates);
  if (profile.kind === "crypto" || profile.kind === "continuous")
    return utcDateKey(date);
  const clock = exchangeClock(date, policy);
  return isExchangeMarketDate(clock.dateKey, policy, closedDates) &&
      clock.minutes >= profile.regularOpenMinutes
    ? clock.dateKey
    : previousExchangeMarketDate(clock.dateKey, policy, closedDates);
}

export function expectedLatestCompletedExchangeSessionDate(
  date = new Date(),
  policy: SessionPolicy = {},
  closedDates: ReadonlySet<string> = new Set(),
) {
  const profile = exchangeSessionProfile(policy);
  if (!profile) return null;
  if (profile.kind === "us-security")
    return expectedLatestCompletedUsSessionDate(date, closedDates);
  if (profile.kind === "crypto")
    return addDateKeyDays(utcDateKey(date), -1);
  if (profile.kind === "continuous") return null;
  const clock = exchangeClock(date, policy);
  const bounds = exchangeSessionBounds(clock.dateKey, policy);
  return bounds &&
      isExchangeMarketDate(clock.dateKey, policy, closedDates) &&
      clock.minutes >=
        bounds.regularCloseMinutes + DAILY_BAR_FINALIZATION_GRACE_MINUTES
    ? clock.dateKey
    : previousExchangeMarketDate(clock.dateKey, policy, closedDates);
}

function rowDateKey(
  unixSeconds: number,
  kind: SessionInstrumentKind,
  timeZone = "America/New_York",
) {
  const date = new Date(unixSeconds * 1000);
  if (kind === "crypto" || kind === "continuous") return utcDateKey(date);
  return clockInTimeZone(date, timeZone).dateKey;
}

export function marketSessionDateKey(
  unixSeconds: number,
  policy: SessionPolicy = {},
) {
  if (!Number.isFinite(unixSeconds) || unixSeconds <= 0) return null;
  const profile = exchangeSessionProfile(policy);
  if (!profile || profile.kind === "unknown") return null;
  return rowDateKey(unixSeconds, profile.kind, profile.timeZone);
}

export function completedSessionCloseAt(
  unixSeconds: number,
  policy: SessionPolicy = {},
) {
  const dateKey = marketSessionDateKey(unixSeconds, policy);
  if (!dateKey) return null;
  const profile = exchangeSessionProfile(policy);
  if (!profile) return null;
  if (profile.kind === "us-security")
    return newYorkDateTimeUtc(
      dateKey,
      usMarketSessionBounds(dateKey).regularCloseMinutes,
    );
  if (profile.kind === "foreign-security")
    return zonedDateTimeUtc(
      dateKey,
      profile.regularCloseMinutes,
      profile.timeZone,
    );
  const kind = profile.kind;
  if (kind === "crypto" || kind === "continuous") {
    const nextDate = addDateKeyDays(dateKey, 1);
    return `${nextDate}T00:00:00.000Z`;
  }
  return null;
}

export function completedSessionIsFinalized(
  unixSeconds: number,
  policy: SessionPolicy = {},
  now = new Date(),
) {
  const closeAt = completedSessionCloseAt(unixSeconds, policy);
  if (!closeAt) return false;
  const kind = exchangeSessionProfile(policy)?.kind;
  const graceMinutes =
    kind === "us-security" || kind === "foreign-security"
      ? DAILY_BAR_FINALIZATION_GRACE_MINUTES
      : 0;
  return (
    now.getTime() >=
    Date.parse(closeAt) + graceMinutes * 60_000
  );
}

export function completedDailyRows<T extends TimedMarketRow>(
  rows: T[],
  {
    now = new Date(),
    instrumentType = "",
    exchange = "",
    symbol = "",
    exchangeTimezone = null,
    closedDates = new Set<string>(),
  }: {
    now?: Date;
    instrumentType?: string | null;
    exchange?: string | null;
    symbol?: string | null;
    exchangeTimezone?: string | null;
    closedDates?: ReadonlySet<string>;
  } = {},
) {
  if (!rows.length) return { rows, partialBarExcluded: false };
  const policy = { instrumentType, exchange, symbol, exchangeTimezone };
  const profile = exchangeSessionProfile(policy);
  const kind = profile?.kind || "unknown";
  if (kind === "unknown") return { rows, partialBarExcluded: false };
  const latest = rows.at(-1)!;
  const latestDateKey = rowDateKey(
    latest.time,
    kind,
    profile?.timeZone,
  );
  let partial = false;
  if (kind === "crypto" || kind === "continuous") {
    partial = latestDateKey === utcDateKey(now);
  } else if (kind === "us-security") {
    const clock = newYorkClock(now);
    const bounds = usMarketSessionBounds(clock.dateKey);
    const currentSessionFinalized =
      isUsMarketDate(clock.dateKey, closedDates) &&
      clock.minutes >=
        bounds.regularCloseMinutes + DAILY_BAR_FINALIZATION_GRACE_MINUTES;
    partial =
      latestDateKey === clock.dateKey &&
      !currentSessionFinalized;
  } else if (kind === "foreign-security") {
    const clock = exchangeClock(now, policy);
    const bounds = exchangeSessionBounds(clock.dateKey, policy);
    const currentSessionFinalized = Boolean(
      bounds &&
      isExchangeMarketDate(clock.dateKey, policy, closedDates) &&
      clock.minutes >=
        bounds.regularCloseMinutes + DAILY_BAR_FINALIZATION_GRACE_MINUTES,
    );
    partial =
      latestDateKey === clock.dateKey &&
      !currentSessionFinalized;
  }
  return {
    rows: partial ? rows.slice(0, -1) : rows,
    partialBarExcluded: partial,
  };
}

function marketSessionsBetween(
  startDateKey: string,
  endDateKey: string,
  closedDates: ReadonlySet<string>,
  policy: SessionPolicy = {},
) {
  if (startDateKey >= endDateKey) return 0;
  const kind = exchangeSessionProfile(policy)?.kind;
  let count = 0;
  let cursor = addDateKeyDays(startDateKey, 1);
  while (cursor <= endDateKey) {
    if (
      kind === "foreign-security"
        ? isExchangeMarketDate(cursor, policy, closedDates)
        : isUsMarketDate(cursor, closedDates)
    ) count += 1;
    cursor = addDateKeyDays(cursor, 1);
  }
  return count;
}

export function evaluateQuoteFreshness({
  marketTime,
  now = new Date(),
  instrumentType = "",
  exchange = "",
  symbol = "",
  exchangeTimezone = null,
  closedDates = new Set<string>(),
}: {
  marketTime?: string | number | null;
  now?: Date;
  instrumentType?: string | null;
  exchange?: string | null;
  symbol?: string | null;
  exchangeTimezone?: string | null;
  closedDates?: ReadonlySet<string>;
}) {
  const timestamp =
    typeof marketTime === "number"
      ? marketTime * 1000
      : marketTime
        ? new Date(marketTime).getTime()
        : Number.NaN;
  if (!Number.isFinite(timestamp))
    return {
      state: "quarantined" as const,
      stale: true,
      ageMs: null,
      sessionLag: null,
      reason: "The provider did not supply a valid market timestamp.",
    };
  const ageMs = now.getTime() - timestamp;
  if (ageMs < -5 * 60_000)
    return {
      state: "quarantined" as const,
      stale: true,
      ageMs,
      sessionLag: null,
      reason: "The provider timestamp is materially in the future.",
    };
  const policy = { instrumentType, exchange, symbol, exchangeTimezone };
  const kind = exchangeSessionProfile(policy)?.kind || "unknown";
  if (kind === "crypto" || kind === "continuous") {
    // These CME/CBOT/COMEX/NYMEX contracts close Friday 17:00 ET and
    // reopen Sunday 18:00 ET. Do not age a Friday close through the weekend
    // as if it were a 24/7 crypto feed. Unknown contracts retain the strict
    // wall-clock gate; holiday early closes are not guessed here.
    // https://www.cmegroup.com/education/lessons/product-e-mini-s-and-p
    const weekendFuture = /^(ES|NQ|YM|RTY|NKD|GC|SI|HG|CL|ZN|6E|6J)=F$/u.test(String(symbol).toUpperCase());
    const clock = newYorkClock(now);
    const weekendClosed = weekendFuture && (
      (clock.weekday === "Fri" && clock.minutes >= 17 * 60) ||
      clock.weekday === "Sat" ||
      (clock.weekday === "Sun" && clock.minutes < 18 * 60)
    );
    let freshnessAgeMs = ageMs;
    if (weekendClosed) {
      const friday = addDateKeyDays(clock.dateKey, clock.weekday === "Sat" ? -1 : clock.weekday === "Sun" ? -2 : 0);
      const quoteClock = newYorkClock(new Date(timestamp));
      // The last quote must belong to Friday and be within two hours of
      // its actual close. Thursday data must never become "current".
      freshnessAgeMs = quoteClock.dateKey === friday
        ? Math.max(0, 17 * 60 - quoteClock.minutes) * 60_000
        : Number.POSITIVE_INFINITY;
    }
    const stale = freshnessAgeMs > 2 * 60 * 60_000;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      ageMs,
      sessionLag: null,
      reason: weekendClosed && !stale
        ? "The futures quote covers Friday's close; the market is closed for the weekend."
        : stale
        ? `The ${kind === "crypto" ? "crypto" : "continuous-market"} quote is more than two hours old.`
        : `The ${kind === "crypto" ? "crypto" : "continuous-market"} quote is current within the two-hour freshness gate.`,
    };
  }
  if (kind === "us-security") {
    const quoteClock = newYorkClock(new Date(timestamp));
    const clock = newYorkClock(now);
    const phase = marketPhase(now, closedDates);
    const bounds = usMarketSessionBounds(clock.dateKey);
    const sameTradingDate = quoteClock.dateKey === clock.dateKey;
    const extendedQuoteIsCurrent =
      sameTradingDate &&
      ageMs <= 30 * 60_000 &&
      ((phase === "premarket" &&
        quoteClock.minutes >= 240 &&
        quoteClock.minutes < 570) ||
        (phase === "after-hours" &&
          quoteClock.minutes >= bounds.regularCloseMinutes &&
          quoteClock.minutes < bounds.extendedCloseMinutes));
    if (extendedQuoteIsCurrent)
      return {
        state: "fresh" as const,
        stale: false,
        ageMs,
        sessionLag: 0,
        reason:
          phase === "premarket"
            ? "The provider premarket quote is current within the thirty-minute freshness gate."
            : "The provider after-hours quote is current within the thirty-minute freshness gate.",
      };
    const quoteDateKey = newYorkClock(new Date(timestamp)).dateKey;
    const expectedDateKey = expectedLatestUsQuoteDate(now, closedDates);
    const sessionLag = marketSessionsBetween(
      quoteDateKey,
      expectedDateKey,
      closedDates,
    );
    const intradayStale =
      phase === "regular" &&
      quoteDateKey === clock.dateKey &&
      ageMs > 30 * 60_000;
    const stale =
      quoteDateKey > expectedDateKey || sessionLag > 0 || intradayStale;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      ageMs,
      sessionLag,
      reason:
        quoteDateKey > expectedDateKey
          ? "The quote date is ahead of the expected market session."
          : stale
            ? intradayStale
              ? "The regular-session quote is more than 30 minutes old."
              : `The quote is ${sessionLag} completed market session${sessionLag === 1 ? "" : "s"} behind.`
            : "The quote covers the latest expected market session.",
    };
  }
  if (kind === "foreign-security") {
    const profile = exchangeSessionProfile(policy);
    const quoteClock = exchangeClock(new Date(timestamp), policy);
    const clock = exchangeClock(now, policy);
    const expectedDateKey = expectedLatestExchangeSessionDate(
      now,
      policy,
      closedDates,
    );
    if (!profile || !expectedDateKey) {
      return {
        state: "quarantined" as const,
        stale: true,
        ageMs,
        sessionLag: null,
        reason: "The listing venue did not resolve to a supported exchange session.",
      };
    }
    const phase =
      isExchangeMarketDate(clock.dateKey, policy, closedDates) &&
      clock.minutes >= profile.regularOpenMinutes &&
      clock.minutes < profile.regularCloseMinutes
        ? "regular"
        : "closed";
    const sameTradingDate = quoteClock.dateKey === clock.dateKey;
    const currentSessionIsFresh =
      phase === "regular" &&
      sameTradingDate &&
      quoteClock.minutes >= profile.regularOpenMinutes &&
      quoteClock.minutes < profile.regularCloseMinutes &&
      ageMs <= 30 * 60_000;
    if (currentSessionIsFresh)
      return {
        state: "fresh" as const,
        stale: false,
        ageMs,
        sessionLag: 0,
        reason: "The foreign-exchange quote is current within the thirty-minute freshness gate.",
      };
    const sessionLag = marketSessionsBetween(
      quoteClock.dateKey,
      expectedDateKey,
      closedDates,
      policy,
    );
    const intradayStale =
      phase === "regular" &&
      sameTradingDate &&
      ageMs > 30 * 60_000;
    const stale =
      quoteClock.dateKey > expectedDateKey ||
      sessionLag > 0 ||
      intradayStale;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      ageMs,
      sessionLag,
      reason:
        quoteClock.dateKey > expectedDateKey
          ? "The quote date is ahead of the expected exchange session."
          : stale
            ? intradayStale
              ? "The foreign-session quote is more than 30 minutes old."
              : `The quote is ${sessionLag} completed exchange session${sessionLag === 1 ? "" : "s"} behind.`
            : "The quote covers the latest expected exchange session.",
    };
  }
  const stale = ageMs > 4 * DAY_MS;
  return {
    state: stale ? ("stale" as const) : ("fresh" as const),
    stale,
    ageMs,
    sessionLag: null,
    reason: stale
      ? "The quote exceeded the fallback four-day freshness gate."
      : "The quote passed the fallback freshness gate.",
  };
}

export function evaluateCompletedSeriesFreshness({
  completedSessionTime,
  now = new Date(),
  instrumentType = "",
  exchange = "",
  symbol = "",
  exchangeTimezone = null,
  closedDates = new Set<string>(),
}: {
  completedSessionTime?: string | number | null;
  now?: Date;
  instrumentType?: string | null;
  exchange?: string | null;
  symbol?: string | null;
  exchangeTimezone?: string | null;
  closedDates?: ReadonlySet<string>;
}) {
  const timestamp =
    typeof completedSessionTime === "number"
      ? completedSessionTime * 1000
      : completedSessionTime
        ? new Date(completedSessionTime).getTime()
        : Number.NaN;
  if (!Number.isFinite(timestamp))
    return {
      state: "quarantined" as const,
      stale: true,
      sessionLag: null,
      reason: "The completed series has no valid session timestamp.",
    };
  const policy = { instrumentType, exchange, symbol, exchangeTimezone };
  const kind = exchangeSessionProfile(policy)?.kind || "unknown";
  if (kind === "crypto") {
    const completedDate = utcDateKey(new Date(timestamp));
    const expected = addDateKeyDays(utcDateKey(now), -1);
    const stale = completedDate < expected || completedDate > expected;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      sessionLag: stale ? 1 : 0,
      reason: stale
        ? `The latest completed crypto day is ${completedDate}; ${expected} was expected.`
        : "The completed crypto series covers the latest expected UTC day.",
    };
  }
  if (kind === "continuous")
    return {
      state: "quarantined" as const,
      stale: true,
      sessionLag: null,
      reason:
        "Completed-session policy for this continuous market is not configured.",
    };
  if (kind === "us-security") {
    const completedDate = newYorkClock(new Date(timestamp)).dateKey;
    const expected = expectedLatestCompletedUsSessionDate(now, closedDates);
    const sessionLag = marketSessionsBetween(
      completedDate,
      expected,
      closedDates,
    );
    const stale = completedDate > expected || sessionLag > 0;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      sessionLag,
      reason:
        completedDate > expected
          ? "The completed-session timestamp is ahead of the expected session."
          : stale
            ? `The technical series is ${sessionLag} completed market session${sessionLag === 1 ? "" : "s"} behind.`
            : "The technical series covers the latest expected completed session.",
    };
  }
  if (kind === "foreign-security") {
    const completedDate = exchangeClock(new Date(timestamp), policy).dateKey;
    const expected = expectedLatestCompletedExchangeSessionDate(
      now,
      policy,
      closedDates,
    );
    if (!expected) {
      return {
        state: "quarantined" as const,
        stale: true,
        sessionLag: null,
        reason: "The listing venue did not resolve to a supported exchange session.",
      };
    }
    const sessionLag = marketSessionsBetween(
      completedDate,
      expected,
      closedDates,
      policy,
    );
    const stale = completedDate > expected || sessionLag > 0;
    return {
      state: stale ? ("stale" as const) : ("fresh" as const),
      stale,
      sessionLag,
      reason:
        completedDate > expected
          ? "The completed-session timestamp is ahead of the expected exchange session."
          : stale
            ? `The technical series is ${sessionLag} completed exchange session${sessionLag === 1 ? "" : "s"} behind.`
            : "The technical series covers the latest expected completed exchange session.",
    };
  }
  return {
    state: "quarantined" as const,
    stale: true,
    sessionLag: null,
    reason: "No supported completed-session calendar was resolved.",
  };
}

export function extendedHoursVisibility(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
) {
  const phase = marketPhase(date, closedDates);
  return {
    phase,
    showPremarket: phase === "premarket",
    showAfterHours: phase === "after-hours",
  };
}

/**
 * After-hours observations remain useful as a timestamped end-of-session
 * display through midnight New York time. This is display retention only:
 * Tensor calculations and live ranking still require an active, fresh
 * after-hours observation.
 */
export function afterHoursDisplayAllowed(
  date = new Date(),
  closedDates: ReadonlySet<string> = new Set(),
) {
  const clock = newYorkClock(date);
  if (!isUsMarketDate(clock.dateKey, closedDates)) return false;
  const bounds = usMarketSessionBounds(clock.dateKey);
  return (
    clock.minutes >= bounds.regularCloseMinutes &&
    clock.minutes < 24 * 60
  );
}
