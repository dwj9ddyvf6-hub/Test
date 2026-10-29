// I/O only. The Author desk's server modules read and write their study files under the absolute /workspace/ tree
// (green-study-io.ts: /workspace/ledger/green/<date>.json, /workspace/.data/green-*.json); run under the desk, that
// tree is the directory the runner names in globalThis.__Author_WORKSPACE__ (the desk's cache). Paths outside
// /workspace/ pass through unchanged. ts_resolve.mjs serves this module in place of node:fs/promises to the named
// source files only.
import * as fsp from "node:fs/promises";
import path from "node:path";

const ROOT = "/workspace/";

function map(p) {
  if (typeof p !== "string" || !p.startsWith(ROOT)) return p;
  const base = globalThis.__Author_WORKSPACE__;
  if (!base) throw new Error("no workspace directory configured for " + p);
  return path.join(base, p.slice(ROOT.length));
}

export const readFile = (p, ...a) => fsp.readFile(map(p), ...a);
export const writeFile = (p, ...a) => fsp.writeFile(map(p), ...a);
export const mkdir = (p, ...a) => fsp.mkdir(map(p), ...a);
export const readdir = (p, ...a) => fsp.readdir(map(p), ...a);
export const stat = (p, ...a) => fsp.stat(map(p), ...a);
export const rename = (a, b, ...r) => fsp.rename(map(a), map(b), ...r);
export const unlink = (p, ...a) => fsp.unlink(map(p), ...a);
export const appendFile = (p, ...a) => fsp.appendFile(map(p), ...a);
export default { readFile, writeFile, mkdir, readdir, stat, rename, unlink, appendFile };
