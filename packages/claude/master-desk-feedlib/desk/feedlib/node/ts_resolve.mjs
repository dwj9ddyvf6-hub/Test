// Module resolution for vendored TypeScript sources run unchanged under Node's type stripping: an extensionless
// relative specifier resolves to its .ts file, and a path alias the runner registers (initialize data
// {alias: {"@/": "<file URL of the vendored src/ root>"}}) resolves as the source's tsconfig `paths` did. A JSON
// module imported without an import attribute (as the sources' bundler allowed) loads as its default export. A
// runner may redirect one built-in for named source files only — I/O, never logic — (initialize data
// {redirect: [{parent: "<file name suffix>", specifier: "node:fs/promises", url: "<shim file URL>"}]}).
import { readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";

let ALIAS = {};
let REDIRECT = [];

export async function initialize(data) {
  ALIAS = (data && data.alias) || {};
  REDIRECT = (data && data.redirect) || [];
}

function isFile(url) {
  try {
    return statSync(fileURLToPath(url)).isFile();
  } catch {
    return false;
  }
}

function withTs(url) {
  for (const ext of ["", ".ts", ".mjs", ".js", "/index.ts"]) {
    const u = new URL(url.href + ext);
    if (isFile(u)) return u.href;
  }
  return null;
}

export async function resolve(specifier, context, next) {
  for (const r of REDIRECT) {
    if (specifier === r.specifier && context.parentURL && context.parentURL.endsWith(r.parent)) {
      return { url: r.url, shortCircuit: true };
    }
  }
  for (const [prefix, base] of Object.entries(ALIAS)) {
    if (specifier.startsWith(prefix)) {
      const hit = withTs(new URL(specifier.slice(prefix.length), base));
      if (hit) return next(hit, context);
    }
  }
  if ((specifier.startsWith("./") || specifier.startsWith("../")) && !/\.[cm]?[jt]s$/.test(specifier) &&
      !specifier.endsWith(".json") && context.parentURL) {
    const url = new URL(specifier + ".ts", context.parentURL);
    if (isFile(url)) return next(url.href, context);
  }
  return next(specifier, context);
}

export async function load(url, context, next) {
  if (url.startsWith("file:") && url.endsWith(".json") && !(context.importAttributes && context.importAttributes.type)) {
    const text = readFileSync(fileURLToPath(url), "utf8");
    return { format: "module", source: `export default ${text};`, shortCircuit: true };
  }
  return next(url, context);
}
