export type CanonicalInstrumentType =
  | "equity"
  | "adr"
  | "etf"
  | "otc-equity"
  | "crypto"
  | "index"
  | "future"
  | "currency"
  | "mutual-fund"
  | "unknown";

export type IdentityCheck = {
  id: string;
  status: "pass" | "warn" | "fail" | "not-applicable";
  message: string;
  observed?: Record<string, string | number | boolean | null>;
};

export type InstrumentIdentityInput = {
  requestedSymbol: string;
  quoteSymbol?: string | null;
  historySymbol?: string | null;
  name?: string | null;
  quoteVenue?: string | null;
  metadataVenue?: string | null;
  historyVenue?: string | null;
  quoteCurrency?: string | null;
  historyCurrency?: string | null;
  providerInstrumentType?: string | null;
  metadataInstrumentType?: string | null;
  expectedProviderSymbol?: string | null;
  cik?: string | null;
};

export type CanonicalInstrumentIdentity = {
  symbol: string;
  name: string;
  venue: string;
  currency: string;
  instrumentType: CanonicalInstrumentType;
  shareClass: string | null;
  isAdr: boolean;
  cik: string | null;
  providerIds: {
    quoteSymbol: string | null;
    historySymbol: string | null;
  };
  state: "usable" | "partial" | "quarantined";
  conflicts: string[];
  warnings: string[];
  checks: IdentityCheck[];
};

export function normalizeInstrumentSymbol(value: unknown) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9.^=\/-]/g, "")
    .slice(0, 24);
}

/**
 * Explicit provider aliases are intentionally narrow. They preserve the
 * user-facing research-universe symbol while documenting the exact identifier
 * required by the historical-data provider.
 */
const PROVIDER_SYMBOL_ALIASES: Readonly<Record<string, string>> = {
  DRO: "DRO.AX",
  LPKF: "LPKFF",
  // SK hynix's Korea listing is KRX 000660. Keep SKHY as the readable
  // FolioTend symbol and accept the earlier screenshot typo SKHQ so both
  // identities use the same Korea OHLCV tape on every Tensor timeframe.
  SKHY: "000660.KS",
  SKHQ: "000660.KS",
  "000660": "000660.KS",
  // SKRKF is the OTCQB line for Selkirk Copper. Use the company's primary
  // TSX Venture tape for Tensor history and higher-timeframe calculations,
  // while retaining SKRKF as the user-facing symbol.
  SKRKF: "SCMI.V",
};

const PROVIDER_INTERVAL_SYMBOL_ALIASES: Readonly<Record<string, string>> = {
  // Tensor uses Sivers' Nasdaq Stockholm SIVE tape on every displayed frame.
  // Yahoo identifies that listing as SIVE.ST; SIVEF remains the watchlist
  // alias, without mixing OTC USD candles with Stockholm SEK candles.
  "SIVEF:5M": "SIVE.ST",
  "SIVEF:10M": "SIVE.ST",
  "SIVEF:1H": "SIVE.ST",
  "SIVEF:1D": "SIVE.ST",
  "SIVEF:1WK": "SIVE.ST",
};

const VERIFIED_PROVIDER_LISTING_METADATA: Readonly<
  Record<string, { venue: string; currency: string }>
> = {
  "SIVE.ST": { venue: "STOCKHOLM", currency: "SEK" },
};

export function providerSymbolFor(value: unknown) {
  const symbol = normalizeInstrumentSymbol(value);
  return PROVIDER_SYMBOL_ALIASES[symbol] || symbol;
}

export function providerSymbolForInterval(value: unknown, intervalValue: unknown) {
  const symbol = normalizeInstrumentSymbol(value);
  const interval = String(intervalValue || "").trim().toUpperCase();
  return PROVIDER_INTERVAL_SYMBOL_ALIASES[`${symbol}:${interval}`] || providerSymbolFor(symbol);
}

export function providerSymbolMatches(
  requestedValue: unknown,
  resolvedValue: unknown,
) {
  const requested = normalizeInstrumentSymbol(requestedValue);
  const resolved = normalizeInstrumentSymbol(resolvedValue);
  return Boolean(
    requested &&
      resolved &&
      (resolved === requested ||
        resolved === providerSymbolFor(requested)),
  );
}

export function providerSymbolMatchesInterval(
  requestedValue: unknown,
  resolvedValue: unknown,
  intervalValue: unknown,
) {
  const requested = normalizeInstrumentSymbol(requestedValue);
  const resolved = normalizeInstrumentSymbol(resolvedValue);
  const expected = providerSymbolForInterval(requested, intervalValue);
  return Boolean(
    requested && resolved &&
      (resolved === expected || (requested !== "SIVEF" && resolved === requested)),
  );
}

const CANONICAL_VENUE_ALIASES: Readonly<Record<string, string>> = {
  NMS: "NASDAQ",
  NCM: "NASDAQ",
  NGM: "NASDAQ",
  NASDAQ: "NASDAQ",
  NASDAQGS: "NASDAQ",
  NASDAQGM: "NASDAQ",
  NASDAQCM: "NASDAQ",
  NYQ: "NYSE",
  NYSE: "NYSE",
  ASE: "NYSEAMERICAN",
  NYSEAMERICAN: "NYSEAMERICAN",
  NYSEMKT: "NYSEAMERICAN",
  PCX: "NYSEARCA",
  NYSEARCA: "NYSEARCA",
  BATS: "BATS",
  BTS: "BATS",
  BATSTRADING: "BATS",
  PNK: "OTC",
  OTHEROTC: "OTC",
  OQB: "OTC",
  OQX: "OTC",
  OTC: "OTC",
  OTCQX: "OTC",
  OTCQB: "OTC",
  OTCMARKETS: "OTC",
  CCC: "CRYPTO",
  CCY: "CURRENCY",
  CME: "CME",
  CBOT: "CBOT",
  COMEX: "COMEX",
  NYMEX: "NYMEX",
  // Europe and the Nordics. Yahoo uses short venue codes while other
  // sources tend to report the exchange's full name; keep synonyms stable
  // before session and identity reconciliation compares them.
  STO: "STOCKHOLM",
  OMXSTO: "STOCKHOLM",
  NASDAQSTOCKHOLM: "STOCKHOLM",
  STOCKHOLM: "STOCKHOLM",
  STOCKHOLMSTOCKEXCHANGE: "STOCKHOLM",
  XETR: "XETRA",
  XETRA: "XETRA",
  // Yahoo commonly reports German primary listings as GER while other
  // responses spell the same venue Xetra. Keep the identity stable so a
  // quote/history response cannot be quarantined merely for naming it
  // differently.
  GER: "XETRA",
  GERMANY: "XETRA",
  FRANKFURTSTOCKEXCHANGE: "FRANKFURT",
  FRA: "FRANKFURT",
  FWB: "FRANKFURT",
  FRANKFURT: "FRANKFURT",
  TRADEGATE: "TRADEGATE",
  TG: "TRADEGATE",
  LSE: "LSE",
  LONDON: "LSE",
  SIX: "SIX",
  SWX: "SIX",
  EBS: "SIX",
  SIXSWISS: "SIX",
  EURONEXT: "EURONEXT",
  EURONEXTPARIS: "EURONEXTPARIS",
  PAR: "EURONEXTPARIS",
  EURONEXTAMSTERDAM: "EURONEXTAMSTERDAM",
  AMS: "EURONEXTAMSTERDAM",
  EURONEXTBRUSSELS: "EURONEXTBRUSSELS",
  BRU: "EURONEXTBRUSSELS",
  EURONEXTLISBON: "EURONEXTLISBON",
  LIS: "EURONEXTLISBON",
  OSL: "OSLO",
  OSLO: "OSLO",
  OMXCOP: "COPENHAGEN",
  CPH: "COPENHAGEN",
  COPENHAGEN: "COPENHAGEN",
  OMXHEX: "HELSINKI",
  HEL: "HELSINKI",
  HELSINKI: "HELSINKI",
  BME: "MADRID",
  MCE: "MADRID",
  MADRID: "MADRID",
  MIL: "MILAN",
  MILAN: "MILAN",
  VIE: "VIENNA",
  VIENNA: "VIENNA",
  // Other major venues supported by the provider and chart surface.
  ASX: "ASX",
  AUSTRALIA: "ASX",
  TSX: "TSX",
  TOR: "TSX",
  TSXV: "TSXV",
  VAN: "TSXV",
  TORONTO: "TSX",
  HKEX: "HKEX",
  HKG: "HKEX",
  HONGKONG: "HKEX",
  TSE: "TSE",
  JPX: "TSE",
  JPN: "TSE",
  TOKYO: "TSE",
  KRX: "KRX",
  KSC: "KRX",
  KSE: "KRX",
  KOSPI: "KRX",
  KOREAEXCHANGE: "KRX",
  KOREASTOCKEXCHANGE: "KRX",
  KOSDAQ: "KOSDAQ",
  NSE: "NSE",
  NSI: "NSE",
  BSE: "BSE",
  INDIA: "NSE",
  SSE: "SSE",
  SHH: "SSE",
  SZSE: "SZSE",
  SHZ: "SZSE",
  SHANGHAI: "SSE",
  SHENZHEN: "SZSE",
  OMX: "OMX",
  NZX: "NZX",
  NEWZEALAND: "NZX",
  TWSE: "TWSE",
  TAI: "TWSE",
  TPEX: "TPEX",
  TWO: "TPEX",
  TAIWAN: "TWSE",
  B3: "B3",
  BVMF: "B3",
  SAO: "B3",
  BRAZIL: "B3",
  JSE: "JSE",
  JNB: "JSE",
  JOHANNESBURG: "JSE",
  SGX: "SGX",
  SES: "SGX",
  SET: "SET",
  BKK: "SET",
  IDX: "IDX",
  JKT: "IDX",
  KLSE: "KLSE",
  KLS: "KLSE",
  TASE: "TASE",
  TASETA: "TASE",
  BIST: "BIST",
  IST: "BIST",
  MOEX: "MOEX",
  MCX: "MOEX",
  WSE: "WSE",
  WAR: "WSE",
  BUD: "BUD",
  PSE: "PSE",
  MANILA: "PSE",
};

// These lookup tables are shared by every session/bar evaluation. Keeping
// them out of canonicalVenue avoids rebuilding dozens of aliases per call.
const CANONICAL_VENUE_PATTERNS: ReadonlyArray<readonly [string, string]> = [
  ["STOCKHOLM", "STOCKHOLM"],
  ["OMXSTO", "STOCKHOLM"],
  ["COPENHAGEN", "COPENHAGEN"],
  ["OMXCOP", "COPENHAGEN"],
  ["HELSINKI", "HELSINKI"],
  ["OMXHEX", "HELSINKI"],
  ["XETRA", "XETRA"],
  ["FRANKFURT", "FRANKFURT"],
  ["TRADEGATE", "TRADEGATE"],
  ["LONDON", "LSE"],
  ["LSE", "LSE"],
  ["ZURICH", "SIX"],
  ["SIX", "SIX"],
  ["EURONEXTPARIS", "EURONEXTPARIS"],
  ["EURONEXTAMSTERDAM", "EURONEXTAMSTERDAM"],
  ["EURONEXTBRUSSELS", "EURONEXTBRUSSELS"],
  ["EURONEXTLISBON", "EURONEXTLISBON"],
  ["EURONEXT", "EURONEXT"],
  ["OSLO", "OSLO"],
  ["MADRID", "MADRID"],
  ["MILAN", "MILAN"],
  ["VIENNA", "VIENNA"],
  ["ASX", "ASX"],
  ["AUSTRALIA", "ASX"],
  ["TORONTO", "TSX"],
  ["TSXV", "TSXV"],
  ["TSX", "TSX"],
  ["HONGKONG", "HKEX"],
  ["HKEX", "HKEX"],
  ["TOKYO", "TSE"],
  ["TSE", "TSE"],
  ["KOSDAQ", "KOSDAQ"],
  ["KOSPI", "KRX"],
  ["KRX", "KRX"],
  ["KOREAEXCHANGE", "KRX"],
  ["KOREASTOCKEXCHANGE", "KRX"],
  ["SHANGHAI", "SSE"],
  ["SSE", "SSE"],
  ["SHENZHEN", "SZSE"],
  ["SZSE", "SZSE"],
  ["NEWZEALAND", "NZX"],
  ["NZX", "NZX"],
  ["TAIWAN", "TWSE"],
  ["TWSE", "TWSE"],
  ["TPEX", "TPEX"],
  ["BRAZIL", "B3"],
  ["BVMF", "B3"],
  ["JSE", "JSE"],
  ["JOHANNESBURG", "JSE"],
  ["SINGAPORE", "SGX"],
  ["SGX", "SGX"],
  ["THAILAND", "SET"],
  ["JAKARTA", "IDX"],
  ["KUALALUMPUR", "KLSE"],
  ["TELAVIV", "TASE"],
  ["ISTANBUL", "BIST"],
  ["MOSCOW", "MOEX"],
  ["WARSAW", "WSE"],
  ["BUDAPEST", "BUD"],
  ["MANILA", "PSE"],
  ["OTCQX", "OTC"],
  ["OTCQB", "OTC"],
  ["OTCMARKETS", "OTC"],
  ["OTC", "OTC"],
  ["NASDAQ", "NASDAQ"],
  ["NYSEARCA", "NYSEARCA"],
  ["NYSEAMERICAN", "NYSEAMERICAN"],
  ["NYSE", "NYSE"],
];

export function canonicalVenue(value: unknown) {
  const venue = String(value || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
  if (CANONICAL_VENUE_ALIASES[venue]) return CANONICAL_VENUE_ALIASES[venue];

  // Provider metadata is not consistent about whether it returns an exchange
  // code, a full exchange name, or a combined label such as
  // "NASDAQ OMX Stockholm". Resolve the foreign venue before the generic
  // NASDAQ/NYSE fallbacks so a listing is never put on the New York calendar
  // merely because its operator name contains NASDAQ.
  for (const [pattern, canonical] of CANONICAL_VENUE_PATTERNS) {
    if (venue.includes(pattern)) return canonical;
  }
  return venue;
}

/**
 * Infer a venue only from an exchange-suffixed symbol when the provider has
 * not supplied venue metadata yet. Bare symbols remain deliberately
 * ambiguous; a user can still preserve an exact venue with the suffix or a
 * provider-resolved listing.
 */
export function venueHintFromSymbol(value: unknown) {
  const symbol = normalizeInstrumentSymbol(value);
  const suffixes: Array<[string, string]> = [
    // Match the longest suffix first so .TWO is never truncated as .T.
    [".TWO", "TPEX"],
    [".ST", "STOCKHOLM"],
    [".DE", "XETRA"],
    [".F", "FRANKFURT"],
    [".L", "LSE"],
    [".SW", "SIX"],
    [".PA", "EURONEXTPARIS"],
    [".AS", "EURONEXTAMSTERDAM"],
    [".BR", "EURONEXTBRUSSELS"],
    [".LS", "EURONEXTLISBON"],
    [".OL", "OSLO"],
    [".CO", "COPENHAGEN"],
    [".HE", "HELSINKI"],
    [".MC", "MADRID"],
    [".MI", "MILAN"],
    [".VI", "VIENNA"],
    [".AX", "ASX"],
    [".TO", "TSX"],
    [".V", "TSXV"],
    [".HK", "HKEX"],
    [".KS", "KRX"],
    [".KQ", "KOSDAQ"],
    [".NS", "NSE"],
    [".BO", "BSE"],
    [".SS", "SSE"],
    [".SZ", "SZSE"],
    [".NZ", "NZX"],
    [".TW", "TWSE"],
    [".SA", "B3"],
    [".JO", "JSE"],
    [".T", "TSE"],
  ];
  return suffixes.find(([suffix]) => symbol.endsWith(suffix))?.[1] || null;
}

function canonicalCurrency(value: unknown) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z]/g, "")
    .slice(0, 8);
}

function shareClassFor(symbol: string) {
  const match = symbol.match(/^[A-Z0-9]+[.-]([A-Z])$/);
  return match?.[1] || null;
}

export function canonicalInstrumentType({
  symbol,
  venue,
  name,
  providerType,
}: {
  symbol: string;
  venue: string;
  name: string;
  providerType: string;
}): CanonicalInstrumentType {
  const kind = providerType.toUpperCase().replace(/[^A-Z]/g, "");
  const description = name.toUpperCase();
  if (kind.includes("CRYPTO") || symbol.endsWith("-USD")) return "crypto";
  if (
    kind.includes("ETF") ||
    /\bETF\b|EXCHANGE[- ]TRADED FUND/.test(description)
  )
    return "etf";
  if (kind.includes("INDEX") || symbol.startsWith("^")) return "index";
  if (kind.includes("CURRENCY") || symbol.endsWith("=X")) return "currency";
  if (kind.includes("FUTURE") || symbol.endsWith("=F")) return "future";
  if (kind.includes("MUTUALFUND")) return "mutual-fund";
  if (
    /\bADR\b|DEPOSITARY RECEIPT|DEPOSITORY RECEIPT/.test(description)
  )
    return "adr";
  if (venue === "OTC") return "otc-equity";
  if (kind.includes("EQUITY")) return "equity";
  return "unknown";
}

export function reconcileInstrumentIdentity(
  input: InstrumentIdentityInput,
): CanonicalInstrumentIdentity {
  const symbol = normalizeInstrumentSymbol(input.requestedSymbol);
  const quoteSymbol = normalizeInstrumentSymbol(input.quoteSymbol);
  const historySymbol = normalizeInstrumentSymbol(input.historySymbol);
  const quoteVenue = canonicalVenue(input.quoteVenue);
  const metadataVenue = canonicalVenue(input.metadataVenue);
  const historyVenue = canonicalVenue(input.historyVenue);
  const venues = [
    ...new Set([quoteVenue, metadataVenue, historyVenue].filter(Boolean)),
  ];
  const quoteCurrency = canonicalCurrency(input.quoteCurrency);
  const historyCurrency = canonicalCurrency(input.historyCurrency);
  const currencies = [
    ...new Set([quoteCurrency, historyCurrency].filter(Boolean)),
  ];
  const expectedProviderSymbol = normalizeInstrumentSymbol(
    input.expectedProviderSymbol,
  );
  const name = String(input.name || symbol).trim() || symbol;
  const providerType = String(
    input.metadataInstrumentType || input.providerInstrumentType || "",
  );
  // A Yahoo-style suffix is useful identity evidence when a provider omits
  // exchangeName (which happens for some OTC and foreign response shapes), but
  // it must never override an exchange explicitly supplied by a provider.
  const venue = venues[0] || venueHintFromSymbol(symbol) || "";
  const instrumentType = canonicalInstrumentType({
    symbol,
    venue,
    name,
    providerType,
  });
  const conflicts: string[] = [];
  const warnings: string[] = [];
  const checks: IdentityCheck[] = [];

  for (const [id, label, resolved] of [
    ["symbol.quote", "Quote", quoteSymbol],
    ["symbol.history", "Historical series", historySymbol],
  ] as const) {
    if (!resolved) {
      checks.push({
        id,
        status: "not-applicable",
        message: `${label} identity was unavailable.`,
      });
    } else if (
      expectedProviderSymbol
        ? resolved !== expectedProviderSymbol
        : !providerSymbolMatches(symbol, resolved)
    ) {
      conflicts.push(
        expectedProviderSymbol
          ? `${label} resolved to ${resolved} instead of the required provider listing ${expectedProviderSymbol}.`
          : `${label} resolved to ${resolved} instead of ${symbol}.`,
      );
      checks.push({
        id,
        status: "fail",
        message: `${label} symbol does not match the requested instrument.`,
        observed: { requested: symbol, resolved },
      });
    } else {
      checks.push({
        id,
        status: "pass",
        message:
          resolved === symbol
            ? `${label} symbol matches the requested instrument.`
            : `${label} resolved through the configured provider alias.`,
        observed:
          resolved === symbol
            ? { symbol }
            : { requested: symbol, providerSymbol: resolved },
      });
    }
  }

  const expectedListing = VERIFIED_PROVIDER_LISTING_METADATA[
    expectedProviderSymbol
  ];
  if (expectedListing) {
    const wrongVenues = venues.filter(value => value !== expectedListing.venue);
    if (wrongVenues.length) {
      conflicts.push(
        `Provider listing ${expectedProviderSymbol} resolved to ${wrongVenues.join(", ")} instead of ${expectedListing.venue}.`,
      );
      checks.push({
        id: "identity.primary-listing-venue",
        status: "fail",
        message: "Provider venue does not match the configured primary listing.",
        observed: {
          expected: expectedListing.venue,
          actual: wrongVenues.join(", "),
        },
      });
    } else if (venues.length) {
      checks.push({
        id: "identity.primary-listing-venue",
        status: "pass",
        message: "Provider venue matches the configured primary listing.",
        observed: { venue: expectedListing.venue },
      });
    }
    const wrongCurrencies = currencies.filter(
      value => value !== expectedListing.currency,
    );
    if (wrongCurrencies.length) {
      conflicts.push(
        `Provider listing ${expectedProviderSymbol} returned ${wrongCurrencies.join(", ")} instead of ${expectedListing.currency}.`,
      );
      checks.push({
        id: "identity.primary-listing-currency",
        status: "fail",
        message: "Provider currency does not match the configured primary listing.",
        observed: {
          expected: expectedListing.currency,
          actual: wrongCurrencies.join(", "),
        },
      });
    } else if (currencies.length) {
      checks.push({
        id: "identity.primary-listing-currency",
        status: "pass",
        message: "Provider currency matches the configured primary listing.",
        observed: { currency: expectedListing.currency },
      });
    }
  }

  if (venues.length > 1) {
    conflicts.push(`Venue disagreement: ${venues.join(", ")}.`);
    checks.push({
      id: "identity.venue",
      status: "fail",
      message: "Connected sources disagree on the listing venue.",
      observed: {
        quote: quoteVenue || null,
        metadata: metadataVenue || null,
        history: historyVenue || null,
      },
    });
  } else if (venues.length === 1) {
    checks.push({
      id: "identity.venue",
      status: "pass",
      message: "Connected sources agree on the listing venue.",
      observed: { venue },
    });
  } else {
    warnings.push("The listing venue is not currently verified.");
    checks.push({
      id: "identity.venue",
      status: "warn",
      message: "The listing venue is not currently verified.",
    });
  }

  if (currencies.length > 1) {
    conflicts.push(`Currency disagreement: ${currencies.join(", ")}.`);
    checks.push({
      id: "identity.currency",
      status: "fail",
      message: "Quote and historical-series currencies disagree.",
      observed: {
        quote: quoteCurrency || null,
        history: historyCurrency || null,
      },
    });
  } else if (currencies.length === 1) {
    checks.push({
      id: "identity.currency",
      status: "pass",
      message: "Connected sources agree on the trading currency.",
      observed: { currency: currencies[0] },
    });
  } else {
    warnings.push("The trading currency is not currently verified.");
    checks.push({
      id: "identity.currency",
      status: "warn",
      message: "The trading currency is not currently verified.",
    });
  }

  if (instrumentType === "unknown") {
    warnings.push("The instrument type is not currently verified.");
    checks.push({
      id: "identity.instrument-type",
      status: "warn",
      message: "The instrument type is not currently verified.",
    });
  } else {
    checks.push({
      id: "identity.instrument-type",
      status: "pass",
      message: `Instrument classified as ${instrumentType}.`,
      observed: { instrumentType },
    });
  }

  const cik = String(input.cik || "").replace(/\D/g, "").padStart(10, "0");
  return {
    symbol,
    name,
    venue,
    currency: currencies[0] || "",
    instrumentType,
    shareClass: shareClassFor(symbol),
    isAdr: instrumentType === "adr",
    cik: cik === "0000000000" ? null : cik,
    providerIds: {
      quoteSymbol: quoteSymbol || null,
      historySymbol: historySymbol || null,
    },
    state: conflicts.length
      ? "quarantined"
      : warnings.length
        ? "partial"
        : "usable",
    conflicts,
    warnings,
    checks,
  };
}
