// Read-only research tools for the site's existing MCP capability.
async function mcpRoute(request, env) {
  if (new URL(request.url).pathname !== "/mcp") return null;
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  let rpc;
  try { rpc = JSON.parse(await readBoundedBody(request, 64000)); }
  catch { return json({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }, 400); }
  const id = rpc?.id ?? null;
  if (rpc?.jsonrpc !== "2.0" || typeof rpc.method !== "string") return json({ jsonrpc: "2.0", id, error: { code: -32600, message: "Invalid request" } }, 400);
  if (rpc.method === "notifications/initialized") return new Response(null, { status: 202 });
  if (rpc.method === "ping") return json({ jsonrpc: "2.0", id, result: {} });
  if (rpc.method === "server/discover") return json({ jsonrpc: "2.0", id, result: { supportedVersions: ["2026-07-28"], capabilities: { tools: {} } } });
  if (rpc.method === "initialize") return json({ jsonrpc: "2.0", id, result: { protocolVersion: "2026-07-28", capabilities: { tools: {} }, serverInfo: { name: "Shipyard Research Terminal", version: "1.0.0" } } });
  if (rpc.method === "tools/list") {
    return json({ jsonrpc: "2.0", id, result: { tools: [
      { name: "shipyard_market_context", description: "Read public Chartlector market context and macro observations. Informational only.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true } },
      { name: "shipyard_alpaca_daily_bars", description: "Read split-adjusted daily IEX bars for one symbol. No account, order, or position data is exposed.", inputSchema: { type: "object", properties: { symbol: { type: "string", pattern: "^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$" }, days: { type: "integer", enum: [20, 60, 90, 180] } }, additionalProperties: false }, annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true } },
      { name: "shipyard_trade_brain_scan", description: "Run a read-only scan using Alpaca SIP stock quotes, IEX daily bars, a verified regular session, fresh modified indicative option quotes, and Alpaca-calculated Black-Scholes Greeks. Indicative prices are not executable quotes and option trades are delayed by 15 minutes. Never submits orders.", inputSchema: { type: "object", properties: { symbol: { type: "string", pattern: "^[A-Za-z][A-Za-z0-9.-]{0,9}$" } }, required: ["symbol"], additionalProperties: false }, annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true } },
      { name: "shipyard_morgue_readiness", description: "Read provenance, freshness metadata, and section presence for the public Morgue snapshot. No market values are returned.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true } },
    ] } });
  }
  if (rpc.method !== "tools/call") return json({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } }, 404);
  const name = rpc.params?.name;
  let response;
  if (name === "shipyard_market_context") {
    response = await contextRoute(new Request(new URL("/api/terminal/context", request.url), { method: "GET" }));
  } else if (name === "shipyard_alpaca_daily_bars") {
    const args = record(rpc.params?.arguments);
    const symbol = typeof args.symbol === "string" ? args.symbol : "SPY";
    const days = [20, 60, 90, 180].includes(args.days) ? args.days : 90;
    const target = new URL("/api/alpaca/bars", request.url);
    target.searchParams.set("symbol", symbol);
    target.searchParams.set("days", String(days));
    response = await alpacaRoute(new Request(target, { headers: { "cf-connecting-ip": request.headers.get("cf-connecting-ip") || "mcp" } }), env);
  } else if (name === "shipyard_trade_brain_scan") {
    const args = record(rpc.params?.arguments);
    const symbol = typeof args.symbol === "string" ? args.symbol : "";
    const target = new URL("/api/alpaca/brain/scan", request.url);
    target.searchParams.set("symbol", symbol);
    response = await alpacaRoute(new Request(target, { headers: { "cf-connecting-ip": request.headers.get("cf-connecting-ip") || "mcp" } }), env);
  } else if (name === "shipyard_morgue_readiness") {
    response = await morgueRoute(new Request(new URL("/api/research/morgue/readiness", request.url), { method: "GET" }));
  } else {
    return json({ jsonrpc: "2.0", id, error: { code: -32602, message: "Unknown or unavailable tool" } }, 404);
  }
  if (!response) return json({ jsonrpc: "2.0", id, error: { code: -32603, message: "Tool did not produce a response" } }, 502);
  const data = await response.json();
  return json({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: JSON.stringify(data) }], structuredContent: data, isError: !response.ok } });
}
