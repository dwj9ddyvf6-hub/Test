// I/O only — the synchronous twin of workspace_fs.mjs: a source script that reads and writes under the absolute
// /workspace/ tree (Author-desk-backup's anna-phd-replay.mjs creates /workspace/.data/yahoo-daily at import) does so
// in the directory the runner names in globalThis.__Author_WORKSPACE__. Paths outside /workspace/ pass through.
// ts_resolve.mjs serves this module in place of node:fs to the named source files only.
import * as fs from "node:fs";
import path from "node:path";

const ROOT = "/workspace/";

function map(p) {
  if (typeof p !== "string" || !p.startsWith(ROOT)) return p;
  const base = globalThis.__Author_WORKSPACE__;
  if (!base) throw new Error("no workspace directory configured for " + p);
  return path.join(base, p.slice(ROOT.length));
}

export const readFileSync = (p, ...a) => fs.readFileSync(map(p), ...a);
export const writeFileSync = (p, ...a) => fs.writeFileSync(map(p), ...a);
export const mkdirSync = (p, ...a) => fs.mkdirSync(map(p), ...a);
export const existsSync = (p) => fs.existsSync(map(p));
export const readdirSync = (p, ...a) => fs.readdirSync(map(p), ...a);
export const statSync = (p, ...a) => fs.statSync(map(p), ...a);
export const appendFileSync = (p, ...a) => fs.appendFileSync(map(p), ...a);
export const renameSync = (a, b) => fs.renameSync(map(a), map(b));
export const unlinkSync = (p) => fs.unlinkSync(map(p));
export default { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync, appendFileSync, renameSync,
  unlinkSync };
