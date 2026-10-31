var SETUP_METHOD = "gestalt-brief-4";
var SETUP_HORIZONS = ["daily", "intraday", "weekly", "crypto"];
const SETUP_DATE_FORMATTERS=new Map();
function setupDateFormatter(locale,options){const key=locale+'|'+JSON.stringify(options);let formatter=SETUP_DATE_FORMATTERS.get(key);if(!formatter){formatter=new Intl.DateTimeFormat(locale,options);if(SETUP_DATE_FORMATTERS.size>=12)SETUP_DATE_FORMATTERS.clear();SETUP_DATE_FORMATTERS.set(key,formatter);}return formatter;}
var SETUP_FAMILIES = { G4: "tensor", C1: "tensor", BETA: "tensor", H1STATE: "tensor", WSTATE: "tensor", D20PV: "tensor", D20TENSOR: "tensor", tensor_leaps: "tensor", recovery: "recovery", pead: "earnings", xsp_pcs: "index_spread", opening_gamma: "opening", core_reserve: "allocation", etf: "allocation", hourly: "timing", cloud: "timing", overnight: "timing", native_trend: "trend", negative_funding_squeeze: "crypto_breakout", breakout_base: "crypto_breakout", absorption_negative_funding: "crypto_absorption", absorption_nonnegative_funding: "crypto_absorption", absorption_base: "crypto_absorption", public_recipe: "price_pattern", confirmed_absorption: "absorption" };
var SETUP_NATIVE_NAMES = { TRADER_DONCHIAN55: "Donchian 55-bar breakout", TRADER_RSI2: "RSI(2) pullback", TRADER_SQUEEZE20: "Bollinger/Keltner squeeze", D20PV: "Daily price-and-volume forecast", D20TENSOR: "Daily Tensor forecast", H1STATE: "Hourly Tensor state", WSTATE: "Weekly Tensor state" };
function setupStrategyName(family, fallback) {
  if (Object.hasOwn(SETUP_NATIVE_NAMES, family)) return SETUP_NATIVE_NAMES[family];
  return typeof fallback === "string" && /^[A-Za-z0-9][A-Za-z0-9 ()&+.,'/-]{0,79}$/.test(fallback) ? fallback : "Paper strategy";
}
function setupTime(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null;
  const day = value.slice(0, 10), calendar = /* @__PURE__ */ new Date(day + "T12:00:00Z");
  if (!Number.isFinite(calendar.getTime()) || calendar.toISOString().slice(0, 10) !== day) return null;
  const at = Date.parse(value);
  return Number.isFinite(at) ? at : null;
}
function setupDay(value) {
  const at = typeof value === "number" ? value : setupTime(value);
  if (at === null || !Number.isFinite(at)) return null;
  return setupDateFormatter("en-CA", { timeZone: "America/New_York" }).format(new Date(at));
}
function setupPublishedTime(value) {
  const iso = setupTime(value);
  if (iso !== null) return iso;
  const match = typeof value === "string" && value.match(/^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}) ET$/);
  if (!match) return null;
  const wall = setupTime(match[1] + "T" + match[2] + ":" + match[3] + ":00Z");
  if (wall === null) return null;
  const formatter = setupDateFormatter("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const matches = [4, 5].map((offset) => wall + offset * 36e5).filter((at) => {
    const p = Object.fromEntries(formatter.formatToParts(new Date(at)).map((x) => [x.type, x.value]));
    return p.year + "-" + p.month + "-" + p.day + " " + p.hour + ":" + p.minute === match[1] + " " + match[2] + ":" + match[3];
  });
  return matches.length === 1 ? matches[0] : null;
}
function setupCurrentDaily(day, now, market = null) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day || "")) return false;
  const source = /* @__PURE__ */ new Date(day + "T12:00:00Z"), today = setupDay(now);
  if (!Number.isFinite(source.getTime()) || source.toISOString().slice(0, 10) !== day || !today || day > today || [0, 6].includes(source.getUTCDay())) return false;
  if (day === today) return true;
  // A fresh verified calendar can witness a holiday gap. Never invent a
  // holiday or extend an older daily packet from elapsed time alone.
  if(market?.calendar_verified===true){
    const receipt=setupTime(market.at),open=setupTime(market.open),close=setupTime(market.close),previous=setupTime(market.previous_session_close);
    if([receipt,open,close,previous].every(x=>x!==null)&&receipt<=now&&now-receipt<=300000&&previous<=now&&previous<open&&open<close&&setupDay(open)>=today&&setupDay(open)===setupDay(close)&&day===setupDay(previous))return true;
  }
  const cursor = /* @__PURE__ */ new Date(today + "T12:00:00Z");
  do {
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  } while ([0, 6].includes(cursor.getUTCDay()));
  return day === cursor.toISOString().slice(0, 10);
}
function setupDailyPacketCurrent(packet, now, market = null) {
  const generated = setupPublishedTime(packet?.generated_at);
  return setupCurrentDaily(packet?.as_of, now, market) && generated !== null && generated <= now && setupDay(generated) >= packet.as_of;
}
