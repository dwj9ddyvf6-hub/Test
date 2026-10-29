// Runs the Author desk's PhD replay replica unchanged: buildAnnaReplica(bars) exported by Author-desk-backup@3e93f984
// (branch gospel-2026-08-13) scripts/anna-phd-replay.mjs — the replay's own port of the Tensor math, indicators,
// seven votes, UT triggers and the location-overridden printer (default options, as replayMain calls it) — vendored
// byte-exact under desk/vendor/Author_gospel. Only I/O is supplied: the request's daily bars in the shape the
// script's fetchDaily builds ({t ms, o, h, l, c, v (null -> 0), session "regular"}), and the script's import-time
// mkdirSync of /workspace/.data/yahoo-daily lands in the runner's workspace directory (workspace_fs_sync.mjs serves
// node:fs to that script only). replayMain (the labeled-day census) is not run.
//
// stdin:  {"workspace": dir, "requests": [{"symbol", "bars": [...]}], "look": n}
// stdout: {"ok": true, "results": [{ok, symbol, n, last, print}]}
import { register } from "node:module";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const script = path.resolve(here, "..", "..", "vendor", "Author_gospel", "scripts", "anna-phd-replay.mjs");
register("./ts_resolve.mjs", import.meta.url, {
  data: { redirect: [{ parent: "scripts/anna-phd-replay.mjs", specifier: "node:fs", url: pathToFileURL(path.join(here, "workspace_fs_sync.mjs")).href }] },
});

const PRINT = new Set(["CYAN_BUY", "GREEN_BUY", "RED_SELL", "MAGENTA_SELL"]);

function row(r) {
  return r ? { t: r.bar.t, c: r.bar.c, marker: r.marker ?? null, location: r.location ?? null, signal: r.signal ?? null,
    regime: r.regime ?? null, glyphs: r.glyphs ?? [], bullShare: r.bullShare ?? null } : null;
}

const out = [];
try {
  const input = JSON.parse(readFileSync(0, "utf8"));
  globalThis.__Author_WORKSPACE__ = input.workspace;
  const phd = await import(pathToFileURL(script).href);
  for (const req of input.requests || []) {
    try {
      const replica = phd.buildAnnaReplica(req.bars);
      let pi = -1;
      for (let i = replica.length - 1; i >= Math.max(0, replica.length - (input.look || 260)); i--) {
        if (PRINT.has(replica[i].marker)) { pi = i; break; }
      }
      out.push({ ok: true, symbol: req.symbol, n: replica.length, last: row(replica[replica.length - 1]),
        print: pi >= 0 ? row(replica[pi]) : null });
    } catch (e) {
      out.push({ ok: false, symbol: req.symbol, error: String((e && e.message) || e).slice(0, 300) });
    }
  }
  process.stdout.write(JSON.stringify({ ok: true, results: out }) + "\n");
} catch (e) {
  process.stdout.write(JSON.stringify({ ok: false, error: String((e && e.stack) || e).slice(0, 1500) }) + "\n");
}
