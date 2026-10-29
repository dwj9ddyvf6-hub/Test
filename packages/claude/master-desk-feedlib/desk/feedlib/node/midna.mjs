// Runs the midna desk's monitored code unchanged (desk/vendor/midna_mon, byte-exact, sha-pinned; midna@43f08f96):
//   vwap   — the equity journal's readVwap (src/lib/equity/journal.ts:419-440): each COMPARE_UNIVERSE name's 15m
//            tape through sessionBars (journal.ts:442-463, reproduced below: it is not exported) and
//            src/lib/vwap/strategy.ts liveRead -> signal / pullback / trend / below;
//   felipe — the journal's readFelipe (journal.ts:396-417): src/lib/felipe/pullback.ts lastWeekState over each
//            FELIPE_ETFS daily tape (completed weeks, EMA 8 / 20 / 50, RSI 14, the weekly pullback signal) and
//            qldState on QQQ;
//   tsmom  — scripts/tsmom-forms.ts FORMS (lines 48-56, reproduced below: the script runs its study at import) on
//            the panel loadPanel builds (lines 231-268: each name's series aligned to SPY's sessions, NaN where a
//            session is missing, a name kept with >= 260 valid sessions), evaluated at the newest session.
// stdin:  {"now": ms, "vwap": [{symbol, rows: [{t, open, high, low, close, volume}]}], "felipe": [{symbol, days}],
//          "qqq": [days], "tsmom": [{symbol, rows: [[date, adj, close, high, low, vol]]}]}
// stdout: {"ok": true, "vwap": {sym: read}, "felipe": {sym: state}, "qld": state, "tsmom": {sym: {date, forms}}}
import { register } from "node:module";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

register("./ts_resolve.mjs", import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
const lib = (p) => import(pathToFileURL(path.resolve(here, "..", "..", "vendor", "midna_mon", "src", "lib", p)).href);

// rules.ts etParts (the fields sessionBars reads)
const FMT = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit",
  minute: "2-digit", second: "2-digit", weekday: "short", hourCycle: "h23",
});
function etParts(date) {
  const parts = Object.fromEntries(FMT.formatToParts(date).map((part) => [part.type, part.value]));
  const hour = Number(parts.hour === "24" ? "0" : parts.hour);
  const minute = Number(parts.minute);
  return { ymd: `${parts.year}-${parts.month}-${parts.day}`, minutesOfDay: hour * 60 + minute };
}

// journal.ts sessionBars
function sessionBars(rows, nowSec) {
  const map = new Map();
  for (const row of rows) {
    if (!(row.close > 0) || row.t + 15 * 60 > nowSec) continue;
    const when = etParts(new Date(row.t * 1000));
    if (when.minutesOfDay < 9 * 60 + 30 || when.minutesOfDay >= 16 * 60) continue;
    const bar = {
      date: when.ymd,
      minute: when.minutesOfDay,
      open: row.open > 0 ? row.open : row.close,
      high: Math.max(row.high, row.open || row.close, row.close),
      low: Math.min(row.low > 0 ? row.low : row.close, row.open || row.close, row.close),
      close: row.close,
      volume: row.volume > 0 ? row.volume : 0,
    };
    map.set(`${bar.date} ${bar.minute}`, bar);
  }
  return [...map.values()].sort((a, b) => a.date.localeCompare(b.date) || a.minute - b.minute);
}

try {
  const vwap = await lib("vwap/strategy.ts");
  const felipe = await lib("felipe/pullback.ts");
  const ts = await lib("research/tsmom.ts");
  const FORMS = [
    { id: "primary-12-1", signal: ts.sign12 },
    { id: "sign-6", signal: ts.sign6 },
    { id: "sign-6-and-12", signal: ts.sign6and12 },
    { id: "roc-12-1", signal: ts.sign12 },
    { id: "donchian-20", signal: ts.donchian20 },
    { id: "golden-cross", signal: ts.goldenCross },
    { id: "year-high", signal: ts.aboveYearHigh },
  ];
  const input = JSON.parse(readFileSync(0, "utf8"));
  const nowSec = Number(input.now) / 1000;
  const out = { ok: true, vwap: {}, felipe: {}, qld: null, tsmom: {} };
  for (const r of input.vwap || []) out.vwap[r.symbol] = vwap.liveRead(r.symbol, sessionBars(r.rows || [], nowSec));
  for (const r of input.felipe || []) out.felipe[r.symbol] = felipe.lastWeekState(r.days || []);
  if (input.qqq) out.qld = felipe.qldState(input.qqq);
  // loadPanel: SPY's sessions are the panel's dates
  const raw = new Map();
  for (const r of input.tsmom || []) {
    if ((r.rows || []).length < 260) continue;
    raw.set(r.symbol, r.rows.map((row) => ({ day: String(row[0]), row })));
  }
  const spy = raw.get("SPY");
  if (spy) {
    const dates = spy.map((row) => row.day);
    const index = new Map(dates.map((day, position) => [day, position]));
    const last = dates.length - 1;
    for (const [symbol, rows] of raw) {
      const blank = () => Array.from({ length: dates.length }, () => Number.NaN);
      const series = { adj: blank(), close: blank(), high: blank(), low: blank(), vol: blank() };
      let valid = 0;
      for (const item of rows) {
        const at = index.get(item.day);
        if (at == null) continue;
        const adj = item.row[1];
        const close = item.row[2];
        if (!(adj > 0) || !(close > 0)) continue;
        series.adj[at] = adj;
        series.close[at] = close;
        series.high[at] = item.row[3] > 0 ? item.row[3] : close;
        series.low[at] = item.row[4] > 0 ? item.row[4] : close;
        series.vol[at] = item.row[5] > 0 ? item.row[5] : 0;
        valid += 1;
      }
      if (valid < 260) continue;
      out.tsmom[symbol] = {
        date: dates[last],
        forms: FORMS.filter((f) => f.signal(series, last)).map((f) => f.id),
        ret252: ts.trailingReturn(series, last, 252),
        ret126: ts.trailingReturn(series, last, 126),
      };
    }
  }
  process.stdout.write(JSON.stringify(out) + "\n");
} catch (e) {
  process.stdout.write(JSON.stringify({ ok: false, error: String((e && e.stack) || e).slice(0, 1500) }) + "\n");
}
