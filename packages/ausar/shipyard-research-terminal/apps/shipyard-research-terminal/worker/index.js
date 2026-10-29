const STATIC_ASSETS = __AUSAR_STATIC_ASSETS__;
const MAX_UPSTREAM_BODY_BYTES = 1024 * 1024;
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
  ".png": "image/png", ".webmanifest": "application/manifest+json",
};
function json(value, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store, max-age=0", "x-content-type-options": "nosniff" } });
}
function record(value) { return value && typeof value === "object" && !Array.isArray(value) ? value : {}; }
function finite(value) { return typeof value === "number" && Number.isFinite(value) && Math.abs(value) <= 1e18 ? value : null; }
function whole(value) { return Number.isSafeInteger(value) && value >= 0 ? value : null; }
function bounded(value, maximum, pattern = null) {
  if (typeof value !== "string" || value.length > maximum) return null;
  return !pattern || pattern.test(value) ? value : null;
}
function timestamp(value) {
  if (typeof value !== "string" || value.length > 64) return null;
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? new Date(milliseconds).toISOString() : null;
}
async function readBoundedBody(response, limit = MAX_UPSTREAM_BODY_BYTES) {
  const declared = Number(response.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > limit) throw new Error("response too large");
  if (!response.body) throw new Error("missing response body");
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) { await reader.cancel(); throw new Error("response too large"); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}
function decodeAsset(encoded) {
  const raw = atob(encoded);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes;
}
function staticResponse(request, pathname) {
  let path;
  try { path = decodeURIComponent(pathname); } catch { return new Response("Not found", { status: 404 }); }
  // Browsers and link unfurlers still request the conventional ICO path even
  // when the document declares the SVG icon. Serve the reviewed asset instead
  // of emitting a noisy 404 for a harmless legacy path.
  if (path === "/favicon.ico") path = "/favicon.svg";
  if (path === "/") path = "/index.html";
  if (path.endsWith("/")) path += "index.html";
  const asset = STATIC_ASSETS[path];
  if (!asset) return new Response("Not found", { status: 404, headers: { "cache-control": "no-store", "x-content-type-options": "nosniff" } });
  const extension = path.slice(path.lastIndexOf(".")).toLowerCase();
  const headers = {
    "content-type": MIME_TYPES[extension] || "application/octet-stream",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "cache-control": path === "/index.html" || path.endsWith(".js") || path.endsWith(".mjs") ? "no-cache" : "public, max-age=300",
  };
  return new Response(request.method === "HEAD" ? null : decodeAsset(asset), { headers });
}

// __TERMINAL__
// __ALPACA__
// __MORGUE__
// __MCP__

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (path.startsWith("/api/ausar/") || path === "/api/terminal/history" || path === "/operations.html") {
      return json({ error: "route_retired", message: "The paper-desk surface has been retired." }, 410);
    }
    const context = await contextRoute(request);
    if (context) return context;
    const alpaca = await alpacaRoute(request, env);
    if (alpaca) return alpaca;
    const morgue = await morgueRoute(request);
    if (morgue) return morgue;
    const mcp = await mcpRoute(request, env);
    if (mcp) return mcp;
    if (path === "/api/status") {
      if (request.method !== "GET" && request.method !== "HEAD") return json({ error: "method_not_allowed" }, 405);
      const configured = typeof env.ALPACA_API_KEY_ID === "string" && env.ALPACA_API_KEY_ID.length > 0
        && typeof env.ALPACA_API_SECRET_KEY === "string" && env.ALPACA_API_SECRET_KEY.length > 0;
      return json({ mode: configured ? "read_only" : "demo", provider: configured ? "Alpaca Market Data + Chartlector context" : "Chartlector context + local demo fixtures", keyConfigured: configured, allowedReads: ["alpaca-daily-bars", "chartlector-context"], accountData: false, orderAccess: false });
    }
    if (request.method !== "GET" && request.method !== "HEAD") return new Response("Method not allowed", { status: 405, headers: { allow: "GET, HEAD", "x-content-type-options": "nosniff" } });
    return staticResponse(request, path);
  },
};
