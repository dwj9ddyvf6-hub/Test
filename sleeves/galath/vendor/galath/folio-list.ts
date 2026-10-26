/**
 * Typefully waits for names. Galath provides the list. Scanner off.
 * Sunday 23 Aug 2026 book: Deep Reset screen, TA only, no buy/target.
 * Weekday after that: one long Target, no Buy, no Stop.
 */
export const SCANNER_DISABLED = true;
export const TYPEFULLY_AUTO_DISABLED = true;
export const WAIT_FOR_NAMES = true;
export const FOLIO_TA_ONLY = true;
export const SCANNER_OFF_WHY = "Scanner cancelled 22 Aug 2026. Never again.";
export const TYPEFULLY_AUTO_OFF_WHY = "Typefully waits for names. No auto book. No auto posts.";
export const TA_ONLY_WHY = "23 Aug: describe the chart. No Buy / Stop / Target on the tweet.";
export const FOLIO_TARGET_ONLY = true;
export const TARGET_ONLY_WHY = "Weekday: one long Target. No Buy. No Stop. Cap washouts.";

export const FOLIO_TICKERS = [
  "PGNY",
  "VTEX",
  "JBTM",
  "BIDU",
  "GRND",
  "RRX",
  "SARO",
  "RBA",
  "BRBR",
  "LINC",
  "OPLN",
  "KNF",
  "VMD",
  "LMB",
  "CASH",
  "BURL",
  "LEVI",
  "SKT",
  "AN",
  "ZTO",
  "PZZA",
  "CALY",
  "EYE",
  "XRAY",
  "AHCO",
  "PLTK",
  "YMM",
  "EVCM",
  "GOGO",
  "PAM",
] as const;

export type ResetLane = "capitulation" | "deep-base" | "reset";

export const FOLIO_RESET_LANE: Record<string, ResetLane> = {};

export const FOLIO_FIRST = ["PGNY", "VTEX", "JBTM", "BIDU", "GRND"] as const;

export function scannerOff(): boolean {
  return SCANNER_DISABLED;
}

export function typefullyAutoOff(): boolean {
  return TYPEFULLY_AUTO_DISABLED;
}

export function waitForNames(): boolean {
  return WAIT_FOR_NAMES;
}

function etDow() {
  const wd = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short" }).format(new Date());
  const map: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return map[wd] ?? 0;
}

export function folioTaOnly(): boolean {
  if (process.env.DESK_CARD_MODE === "target-only") return false;
  if (process.env.DESK_CARD_MODE === "ta-only") return true;
  if (!FOLIO_TA_ONLY) return false;
  return etDow() === 0;
}

export function folioTargetOnly(): boolean {
  if (process.env.DESK_CARD_MODE === "plan") return false;
  if (process.env.DESK_CARD_MODE === "ta-only") return false;
  return FOLIO_TARGET_ONLY && !folioTaOnly();
}

export type CardMode = "ta-only" | "target-only" | "plan";

export function cardMode(): CardMode {
  if (folioTaOnly()) return "ta-only";
  if (folioTargetOnly()) return "target-only";
  return "plan";
}

export function folioTickers(): string[] {
  return [...FOLIO_TICKERS];
}
