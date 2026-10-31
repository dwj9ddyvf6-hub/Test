// Owner-only, encrypted credential storage and read-only broker connections.
// The personal Tradier token is broad-access at the provider; routes here use
// it only for market-data GET endpoints. No broker order or account-write path
// is defined in this module.
const BROKER_SECRET_TABLE = "broker_credentials";
const BROKER_USER_AGENT = "shipyard-research-terminal/1.0";
const brokerConnectWindows = new Map();
const tastyAccessTokenCache = new Map();
const brokerVerificationCache = new Map();
const BROKER_VERIFICATION_MAX_AGE_MS = 60000;

function brokerCredentialError(error) {
  return ["broker_storage_unavailable", "broker_credentials_unreadable"].includes(error?.message)
    ? error.message : "broker_storage_unavailable";
}

async function brokerCredentialIdentity(provider, credentials) {
  const bytes = new TextEncoder().encode(JSON.stringify([provider, Object.keys(credentials).sort().map(key => [key, credentials[key]])]));
  return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function brokerRecordVerification(provider, credentials, status, scope) {
  const identity = await brokerCredentialIdentity(provider, credentials);
  brokerVerificationCache.set(identity, { status, scope, checkedAt: Date.now() });
  while (brokerVerificationCache.size > 16) brokerVerificationCache.delete(brokerVerificationCache.keys().next().value);
}

async function brokerRecordProviderFailure(provider, credentials, status, scope) {
  await brokerRecordVerification(provider, credentials, [401, 403].includes(status) ? "reauthorization_required" : "unavailable", scope);
}

function brokerB64(bytes) {
  let value = "";
  for (let index = 0; index < bytes.length; index += 0x8000) value += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  return btoa(value);
}

function brokerUnb64(value) {
  const raw = atob(value);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes;
}

async function brokerCryptoKey(env) {
  if (typeof env.BROKER_CREDENTIALS_ENCRYPTION_KEY !== "string") throw new Error("credential encryption is unavailable");
  const raw = brokerUnb64(env.BROKER_CREDENTIALS_ENCRYPTION_KEY);
  if (raw.byteLength !== 32) throw new Error("credential encryption is unavailable");
  return crypto.subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}

async function brokerEncrypt(env, credentials) {
  const key = await brokerCryptoKey(env);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode(JSON.stringify(credentials));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext);
  return { iv: brokerB64(iv), ciphertext: brokerB64(new Uint8Array(ciphertext)) };
}

async function brokerDecrypt(env, row) {
  if (!row || typeof row.iv !== "string" || typeof row.ciphertext !== "string") return null;
  const key = await brokerCryptoKey(env);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: brokerUnb64(row.iv) }, key, brokerUnb64(row.ciphertext));
  const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(plaintext));
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

async function brokerCredentialRow(env, provider) {
  if (!env.DB) return null;
  return env.DB.prepare(`SELECT provider,iv,ciphertext,verified_at,metadata_json,updated_at FROM ${BROKER_SECRET_TABLE} WHERE provider=?`).bind(provider).first();
}

async function brokerCredentials(env, provider) {
  let row;
  try { row = await brokerCredentialRow(env, provider); }
  catch { throw new Error("broker_storage_unavailable"); }
  return brokerCredentialsFromRow(env, provider, row);
}

// Return the exact encrypted-row snapshot used for an options read. updated_at
// is an opaque connection-write revision: never mutate it when recording
// provider denial state in its separate receipt table.
async function brokerCredentialSnapshot(env, provider) {
  let row;
  try { row = await brokerCredentialRow(env, provider); }
  catch { throw new Error("broker_storage_unavailable"); }
  const credentials = await brokerCredentialsFromRow(env, provider, row);
  if (!credentials) return null;
  if (typeof row?.updated_at !== "string" || !row.updated_at || row.updated_at.length > 64) {
    throw new Error("broker_credentials_unreadable");
  }
  return { credentials, connection_revision: row.updated_at };
}

async function brokerCredentialsFromRow(env, provider, row) {
  if (!row) return null;
  try {
    const credentials = await brokerDecrypt(env, row);
    const required = provider === "tradier" ? ["token"] : ["client_id", "client_secret", "refresh_token"];
    if (!credentials || required.some(key => typeof credentials[key] !== "string" || !credentials[key])) throw new Error();
    return credentials;
  } catch { throw new Error("broker_credentials_unreadable"); }
}

async function brokerStoreCredentials(env, provider, credentials, metadata) {
  if (!env.DB) throw new Error("credential storage is unavailable");
  const encrypted = await brokerEncrypt(env, credentials);
  const now = new Date().toISOString();
  const result = await env.DB.prepare(`INSERT INTO ${BROKER_SECRET_TABLE} (provider,iv,ciphertext,verified_at,metadata_json,updated_at) VALUES (?,?,?,?,?,?) ON CONFLICT(provider) DO UPDATE SET iv=excluded.iv,ciphertext=excluded.ciphertext,verified_at=excluded.verified_at,metadata_json=excluded.metadata_json,updated_at=excluded.updated_at`)
    .bind(provider, encrypted.iv, encrypted.ciphertext, now, JSON.stringify(metadata), now).run();
  if (result?.success === false) throw new Error("credential storage is unavailable");
  return now;
}

async function brokerStatus(env) {
  const providers = {
    tradier: { configured: false, connected: null, live_status: "not_configured", verified_at: null, last_checked_at: null, access: "market_data_only" },
    tastytrade: { configured: false, connected: null, live_status: "not_configured", verified_at: null, last_checked_at: null, visible_account_count: null, access: "read_only" },
  };
  if (!env.DB) return providers;
  try {
    const result = await env.DB.prepare(`SELECT provider,iv,ciphertext,verified_at,metadata_json FROM ${BROKER_SECRET_TABLE}`).all();
    for (const row of result.results || []) {
      if (!Object.hasOwn(providers, row.provider)) continue;
      providers[row.provider].configured = true;
      providers[row.provider].verified_at = typeof row.verified_at === "string" ? row.verified_at : null;
      let credentials;
      // Decrypt the same snapshot as its metadata; a concurrent reconnect must
      // not mix another identity's verification with this row's setup/count.
      try { credentials = await brokerCredentialsFromRow(env, row.provider, row); }
      catch (error) { providers[row.provider].live_status = brokerCredentialError(error); continue; }
      if (!credentials) continue;
      let metadata = {};
      try {
        const parsed = JSON.parse(row.metadata_json || "{}");
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) metadata = parsed;
      } catch {}
      const check = brokerVerificationCache.get(await brokerCredentialIdentity(row.provider, credentials));
      const age = check ? Date.now() - check.checkedAt : null;
      const status = check && (check.status !== "verified" || (age >= 0 && age <= BROKER_VERIFICATION_MAX_AGE_MS)) ? check.status : "unchecked";
      providers[row.provider] = {
        ...providers[row.provider], configured: true, connected: status === "unchecked" ? null : status === "verified", live_status: status,
        verified_at: typeof row.verified_at === "string" ? row.verified_at : null,
        last_checked_at: check ? new Date(check.checkedAt).toISOString() : null,
        verification_scope: check?.scope || null,
        verification_max_age_seconds: BROKER_VERIFICATION_MAX_AGE_MS / 1000,
        verification_note: "Status performs no provider request. Setup verification is historical; live verification is isolate-local and does not prove current quote freshness or ongoing entitlement.",
        ...(row.provider === "tastytrade" ? { visible_account_count: Number.isSafeInteger(metadata.visible_account_count) && metadata.visible_account_count >= 0 ? metadata.visible_account_count : null } : {}),
      };
    }
  } catch { for (const provider of Object.values(providers)) { provider.live_status = "broker_storage_unavailable"; provider.connected = null; } }
  return providers;
}

function brokerSameOrigin(request) {
  const origin = request.headers.get("origin");
  return origin === new URL(request.url).origin;
}

function brokerConnectAllowed(request) {
  const now = Date.now();
  const key = request.headers.get("cf-connecting-ip") || "owner-session";
  const prior = brokerConnectWindows.get(key);
  const window = !prior || now < prior.started || now - prior.started >= 60000 ? { started: now, count: 0 } : prior;
  window.count += 1;
  brokerConnectWindows.set(key, window);
  if (brokerConnectWindows.size > 128) brokerConnectWindows.delete(brokerConnectWindows.keys().next().value);
  return window.count <= 5;
}

async function brokerFetchJson(url, headers, body = null, timeoutMs = 9000) {
  try {
    const response = await fetch(url, {
      method: body === null ? "GET" : "POST", headers,
      ...(body === null ? {} : { body: JSON.stringify(body) }),
      signal: AbortSignal.timeout(timeoutMs), redirect: "manual",
    });
    let value = null;
    try { value = JSON.parse(await readBoundedBody(response, 512 * 1024)); } catch {}
    return { ok: response.ok, status: response.status, value };
  } catch { return { ok: false, status: 0, value: null }; }
}

async function brokerTradierRequest(token, pathname, query) {
  const url = new URL(`https://api.tradier.com/v1${pathname}`);
  for (const [key, value] of Object.entries(query || {})) url.searchParams.set(key, String(value));
  return brokerFetchJson(url.toString(), { authorization: `Bearer ${token}`, accept: "application/json" });
}

async function brokerTastyToken(env, credentials, useCache = true) {
  const identity = await brokerCredentialIdentity("tastytrade", credentials);
  const cached = useCache ? tastyAccessTokenCache.get(identity) : null;
  if (cached && cached.expiresAt > Date.now() + 30000) return { ok: true, status: 200, ...cached };
  const result = await brokerFetchJson("https://api.tastyworks.com/oauth/token", {
    "content-type": "application/json", accept: "application/json", "user-agent": BROKER_USER_AGENT,
  }, {
    grant_type: "refresh_token", refresh_token: credentials.refresh_token,
    client_id: credentials.client_id, client_secret: credentials.client_secret, scope: "read",
  });
  const accessToken = result.value?.access_token;
  const expiresIn = Number(result.value?.expires_in);
  if (!result.ok || typeof accessToken !== "string" || accessToken.length < 16 || !Number.isFinite(expiresIn) || expiresIn <= 0) return { ok: false, status: result.status };
  const token = { value: accessToken, expiresAt: Date.now() + Math.min(expiresIn, 900) * 1000 };
  if (useCache) brokerCacheTastyToken(identity, token);
  return { ok: true, status: result.status, ...token };
}

function brokerCacheTastyToken(identity, token) {
  tastyAccessTokenCache.set(identity, { value: token.value, expiresAt: token.expiresAt });
  while (tastyAccessTokenCache.size > 4) tastyAccessTokenCache.delete(tastyAccessTokenCache.keys().next().value);
}

async function brokerTastyAccounts(credentials, accessToken) {
  return brokerFetchJson("https://api.tastyworks.com/customers/me/accounts", {
    authorization: `Bearer ${accessToken}`, accept: "application/json", "user-agent": BROKER_USER_AGENT,
  });
}

function brokerTastyAccountCount(payload) {
  const items = payload?.data?.items ?? payload?.items;
  return Array.isArray(items) ? items.length : null;
}

function brokerUnixTimestamp(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  const milliseconds = numeric > 1e12 ? numeric : numeric * 1000;
  if (!Number.isFinite(milliseconds) || milliseconds > 8640000000000000) return null;
  try { return new Date(milliseconds).toISOString(); } catch { return null; }
}

function brokerTradierQuote(payload, symbol) {
  const raw = payload?.quotes?.quote;
  const quote = Array.isArray(raw) ? raw.find((item) => String(item?.symbol || "").toUpperCase() === symbol) : raw;
  if (!quote || String(quote.symbol || "").toUpperCase() !== symbol) return null;
  const bid = finite(quote.bid), ask = finite(quote.ask), last = finite(quote.last);
  const bidAt = brokerUnixTimestamp(quote.bid_date), askAt = brokerUnixTimestamp(quote.ask_date);
  const quoteAt = bidAt && askAt ? (Date.parse(bidAt) <= Date.parse(askAt) ? bidAt : askAt) : null;
  return {
    symbol, bid, ask, last,
    bid_size: finite(quote.bidsize), ask_size: finite(quote.asksize),
    bid_at: bidAt, ask_at: askAt, quote_at: quoteAt,
    quote_age_seconds: quoteAt ? Math.round((Date.now() - Date.parse(quoteAt)) / 1000) : null,
    last_at: brokerUnixTimestamp(quote.trade_date),
    source: "Tradier live brokerage quote",
  };
}

function brokerTradierQuoteFresh(quote, now = Date.now()) {
  return [quote?.bid_at, quote?.ask_at].every(at => {
    const age = (now - Date.parse(at || "")) / 1000;
    return Number.isFinite(age) && age >= -5 && age <= 90;
  });
}

async function brokerTradierOptionSetup(credentials, symbol, optionType, underlyingMid, sessionDate, invalidation, objective) {
  if (!credentials?.token) return { status: "unavailable", error: "tradier_not_connected", setup: null };
  const expiryResult = await brokerTradierRequest(credentials.token, "/markets/options/expirations", {
    symbol, includeAllRoots: "false", strikes: "false", contractSize: "true", expirationType: "true",
  });
  if (!expiryResult.ok) {
    await brokerRecordProviderFailure("tradier", credentials, expiryResult.status, "market_data_access");
    return { status: "unavailable", error: expiryResult.status === 429 ? "provider_rate_limited" : "tradier_expirations_unavailable", setup: null };
  }
  const expiryPayload = expiryResult.value?.expirations;
  if (expiryPayload !== null && (!expiryPayload || typeof expiryPayload !== "object" || Array.isArray(expiryPayload)
    || (!Object.hasOwn(expiryPayload, "date") && !Object.hasOwn(expiryPayload, "expiration")))) {
    await brokerRecordProviderFailure("tradier", credentials, 200, "market_data_access");
    return { status: "unavailable", error: "tradier_expirations_invalid_payload", setup: null };
  }
  await brokerRecordVerification("tradier", credentials, "verified", "market_data_access");
  const rawExpirations = expiryPayload?.date ?? expiryPayload?.expiration;
  const expirations = (Array.isArray(rawExpirations) ? rawExpirations : rawExpirations ? [rawExpirations] : [])
    .map((item) => typeof item === "string" ? item : item?.date)
    .filter(shipyardCalendarDate);
  const todayMs = Date.parse(`${sessionDate}T00:00:00Z`);
  const eligible = expirations.map((expiration) => ({
    expiration,
    dte: Math.floor((Date.parse(`${expiration}T00:00:00Z`) - todayMs) / 86400000),
  })).filter((item) => Number.isFinite(item.dte) && item.dte >= 21 && item.dte <= 45)
    .sort((a, b) => Math.abs(a.dte - 30) - Math.abs(b.dte - 30));
  if (!eligible.length) return { status: "no_contract", error: "tradier_no_expiration_in_window", setup: null };
  const pickedExpiry = eligible[0];
  const chainResult = await brokerTradierRequest(credentials.token, "/markets/options/chains", {
    symbol, expiration: pickedExpiry.expiration, greeks: "true",
  });
  if (!chainResult.ok) {
    await brokerRecordProviderFailure("tradier", credentials, chainResult.status, "market_data_access");
    return { status: "unavailable", error: chainResult.status === 429 ? "provider_rate_limited" : "tradier_chain_unavailable", setup: null };
  }
  const optionsPayload = chainResult.value?.options;
  if (optionsPayload !== null && (!optionsPayload || typeof optionsPayload !== "object" || Array.isArray(optionsPayload) || !Object.hasOwn(optionsPayload, "option"))) {
    await brokerRecordProviderFailure("tradier", credentials, 200, "market_data_access");
    return { status: "unavailable", error: "tradier_chain_invalid_payload", setup: null };
  }
  const rawOptions = optionsPayload?.option;
  const contracts = Array.isArray(rawOptions) ? rawOptions : rawOptions && typeof rawOptions === "object" ? [rawOptions] : [];
  await brokerRecordVerification("tradier", credentials, "verified", "market_data_access");
  const now = Date.now();
  const candidates = [];
  for (const contract of contracts) {
    const contractSymbol = typeof contract?.symbol === "string" ? contract.symbol.toUpperCase() : "";
    const occ = contractSymbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/);
    const encodedExpiration = occ ? `20${occ[2].slice(0, 2)}-${occ[2].slice(2, 4)}-${occ[2].slice(4, 6)}` : null;
    const expiration = contract?.expiration_date;
    const strike = finite(contract?.strike);
    const contractSize = finite(contract?.contract_size);
    const type = String(contract?.option_type || "").toLowerCase();
    const underlying = String(contract?.underlying || "").toUpperCase();
    const root = String(contract?.root_symbol || "").toUpperCase();
    if (!occ || occ[1] !== symbol || occ[3] !== (optionType === "call" ? "C" : "P")
      || !shipyardCalendarDate(encodedExpiration) || encodedExpiration !== expiration
      || expiration !== pickedExpiry.expiration || type !== optionType || underlying !== symbol || root !== symbol
      || strike === null || strike !== Number(occ[4]) / 1000 || contractSize !== 100
      || Math.abs(strike - underlyingMid) > underlyingMid * 0.2) continue;
    const quote = brokerTradierQuote({ quotes: { quote: contract } }, contractSymbol);
    const delta = finite(contract?.greeks?.delta);
    const iv = finite(contract?.greeks?.smv_vol);
    const greekAt = timestamp(contract?.greeks?.updated_at);
    const bidAt = quote?.bid_at ? Date.parse(quote.bid_at) : NaN;
    const askAt = quote?.ask_at ? Date.parse(quote.ask_at) : NaN;
    const quoteAtMs = Math.min(bidAt, askAt);
    const quoteAgeSeconds = (now - quoteAtMs) / 1000;
    const greekAgeSeconds = (now - Date.parse(greekAt || "")) / 1000;
    if (!quote || quote.bid === null || quote.ask === null || quote.bid <= 0 || quote.ask < quote.bid
      || !(quote.bid_size > 0) || !(quote.ask_size > 0)
      || !brokerTradierQuoteFresh(quote, now)
      || delta === null || (optionType === "call" ? delta <= 0 : delta >= 0)
      || iv === null || iv <= 0 || iv >= 5
      || !Number.isFinite(greekAgeSeconds) || greekAgeSeconds < -5 || greekAgeSeconds > 75 * 60) continue;
    const mid = (quote.bid + quote.ask) / 2;
    const spreadRatio = (quote.ask - quote.bid) / mid;
    const absoluteDelta = Math.abs(delta);
    if (!(mid > 0) || spreadRatio > 0.10 || absoluteDelta < 0.45 || absoluteDelta > 0.65) continue;
    candidates.push({ contract, quote, delta, iv, greekAt, greekAgeSeconds, quoteAtMs, quoteAgeSeconds, spreadRatio, mid, strike, absoluteDelta });
  }
  candidates.sort((a, b) => Math.abs(a.absoluteDelta - 0.55) - Math.abs(b.absoluteDelta - 0.55)
    || a.spreadRatio - b.spreadRatio
    || ((b.quote.bid_size + b.quote.ask_size) - (a.quote.bid_size + a.quote.ask_size)));
  const picked = candidates[0];
  if (!picked) return { status: "no_contract", error: "tradier_contracts_failed_quote_or_greek_quality", setup: null };
  const ask = picked.quote.ask;
  const midpoint = Math.round(picked.mid * 100) / 100;
  const oi = finite(picked.contract.open_interest);
  return {
    status: "connected", error: null,
    setup: {
      instrument: optionType, symbol: picked.contract.symbol, underlying: symbol,
      expiration: pickedExpiry.expiration, dte: pickedExpiry.dte, strike: picked.strike, multiplier: 100,
      indicative_midpoint_reference: midpoint, indicative_bid: picked.quote.bid, indicative_ask: ask,
      estimated_max_loss_per_contract_at_indicative_ask: Math.round(ask * 100 * 100) / 100,
      indicative_bid_size: picked.quote.bid_size, indicative_ask_size: picked.quote.ask_size,
      indicative_spread_percent: Math.round(picked.spreadRatio * 10000) / 100,
      delta: picked.delta, implied_volatility: picked.iv, greeks_method: "Tradier/ORATS provider Greek",
      greeks_as_of: picked.greekAt, greeks_age_minutes: Math.round(picked.greekAgeSeconds / 60),
      open_interest: oi, open_interest_as_of: null,
      quote_at: new Date(picked.quoteAtMs).toISOString(), bid_at: picked.quote.bid_at, ask_at: picked.quote.ask_at,
      quote_age_seconds: Math.round(picked.quoteAgeSeconds),
      feed: "tradier", price_basis: "tradier_live_bid_ask", execution_status: "broker_quote_required",
      invalidation, underlying_objective: objective,
      rationale: `Current Tradier bid and ask passed quote freshness, spread, standard 100-share contract, and symbol checks. Delta and implied volatility are Tradier/ORATS values timestamped ${picked.greekAt}; the provider refreshes these approximately hourly. Recheck both quote and Greek before using this candidate. No order is submitted.`,
    },
  };
}

async function brokerReadBody(request) {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") || "")) return null;
  try { return JSON.parse(await readBoundedBody(request, 12000)); } catch { return null; }
}

async function brokerConnectRoute(request, env) {
  const url = new URL(request.url);
  const prefix = "/api/brokers/connect/";
  if (!url.pathname.startsWith(prefix)) return null;
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  if (!brokerSameOrigin(request)) return json({ error: "same_origin_required" }, 403);
  if (!brokerConnectAllowed(request)) return json({ error: "too_many_attempts" }, 429);
  if (!env.DB || typeof env.BROKER_CREDENTIALS_ENCRYPTION_KEY !== "string") return json({ error: "secure_storage_not_ready" }, 503);
  const provider = url.pathname.slice(prefix.length);
  if (!new Set(["tradier", "tastytrade"]).has(provider)) return json({ error: "unknown_provider" }, 404);
  const body = await brokerReadBody(request);
  if (!body || typeof body !== "object" || Array.isArray(body)) return json({ error: "invalid_request" }, 400);

  if (provider === "tradier") {
    if (body.confirm_broad_token_access !== true) return json({ error: "confirmation_required" }, 400);
    const token = typeof body.token === "string" ? body.token.trim() : "";
    if (token.length < 16 || token.length > 4096 || /\s/.test(token)) return json({ error: "invalid_request" }, 400);
    const checked = await brokerTradierRequest(token, "/markets/quotes", { symbols: "SPY", greeks: "false" });
    if (checked.status === 401 || checked.status === 403) return json({ error: "tradier_authentication_failed" }, 400);
    const quote = checked.ok ? brokerTradierQuote(checked.value, "SPY") : null;
    if (!checked.ok || !quote) return json({ error: checked.status === 429 ? "provider_rate_limited" : "tradier_market_data_unavailable" }, 503);
    try {
      const verifiedAt = await brokerStoreCredentials(env, provider, { token }, { market_data_verified: true });
      await brokerRecordVerification(provider, { token }, "verified", "market_data_access");
      return json({ provider, status: "connected", verified_at: verifiedAt, access: "market_data_only" });
    } catch { return json({ error: "secure_storage_failed" }, 503); }
  }

  if (body.confirm_read_only_access !== true) return json({ error: "confirmation_required" }, 400);
  const credentials = {
    client_id: typeof body.client_id === "string" ? body.client_id.trim() : "",
    client_secret: typeof body.client_secret === "string" ? body.client_secret.trim() : "",
    refresh_token: typeof body.refresh_token === "string" ? body.refresh_token.trim() : "",
  };
  if (credentials.client_id.length < 4 || credentials.client_id.length > 512
    || credentials.client_secret.length < 8 || credentials.client_secret.length > 2048
    || credentials.refresh_token.length < 8 || credentials.refresh_token.length > 4096) return json({ error: "invalid_request" }, 400);
  // Candidate reconnect tokens must never replace the currently saved identity's cache.
  const accessToken = await brokerTastyToken(env, credentials, false);
  if (!accessToken.ok) return json({ error: [400, 401, 403].includes(accessToken.status) ? "tastytrade_authentication_failed" : "tastytrade_token_unavailable" }, [400, 401, 403].includes(accessToken.status) ? 400 : 503);
  const accounts = await brokerTastyAccounts(credentials, accessToken.value);
  const accountCount = accounts.ok ? brokerTastyAccountCount(accounts.value) : null;
  if (!accounts.ok || accountCount === null) return json({ error: accounts.status === 429 ? "provider_rate_limited" : "tastytrade_account_read_failed" }, 503);
  try {
    const verifiedAt = await brokerStoreCredentials(env, provider, credentials, { visible_account_count: accountCount });
    brokerCacheTastyToken(await brokerCredentialIdentity(provider, credentials), accessToken);
    await brokerRecordVerification(provider, credentials, "verified", "account_visibility");
    return json({ provider, status: "connected", verified_at: verifiedAt, visible_account_count: accountCount, access: "read_only" });
  } catch { return json({ error: "secure_storage_failed" }, 503); }
}

async function brokerApiRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname === "/api/brokers/status") {
    if (request.method !== "GET" && request.method !== "HEAD") return json({ error: "method_not_allowed" }, 405);
    return json({ providers: await brokerStatus(env) });
  }
  if (url.pathname === "/api/brokers/tastytrade/accounts") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    let credentials;
    try { credentials = await brokerCredentials(env, "tastytrade"); }
    catch (error) { return json({ provider: "tastytrade", status: "unavailable", error: brokerCredentialError(error) }, 503); }
    if (!credentials) return json({ provider: "tastytrade", status: "not_connected" }, 404);
    const accessToken = await brokerTastyToken(env, credentials);
    if (!accessToken.ok) {
      await brokerRecordProviderFailure("tastytrade", credentials, accessToken.status, "account_visibility");
      if ([401, 403].includes(accessToken.status)) tastyAccessTokenCache.delete(await brokerCredentialIdentity("tastytrade", credentials));
      return json({ provider: "tastytrade", status: [401, 403].includes(accessToken.status) ? "reauthorization_required" : "unavailable", error: "tastytrade_token_unavailable" }, 503);
    }
    const result = await brokerTastyAccounts(credentials, accessToken.value);
    const visibleAccountCount = result.ok ? brokerTastyAccountCount(result.value) : null;
    if (!result.ok || visibleAccountCount === null) {
      await brokerRecordProviderFailure("tastytrade", credentials, result.status, "account_visibility");
      if ([401, 403].includes(result.status)) tastyAccessTokenCache.delete(await brokerCredentialIdentity("tastytrade", credentials));
      return json({ provider: "tastytrade", status: [401, 403].includes(result.status) ? "reauthorization_required" : "unavailable" }, 503);
    }
    await brokerRecordVerification("tastytrade", credentials, "verified", "account_visibility");
    return json({ provider: "tastytrade", status: "connected", visible_account_count: visibleAccountCount, checked_at: new Date().toISOString() });
  }
  if (url.pathname === "/api/brokers/tradier/quote") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    const keys = [...url.searchParams.keys()];
    const symbol = (url.searchParams.get("symbol") || "").trim().toUpperCase();
    if (keys.length !== 1 || keys[0] !== "symbol" || !/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol)) return json({ error: "invalid_request" }, 400);
    let credentials;
    try { credentials = await brokerCredentials(env, "tradier"); }
    catch (error) { return json({ provider: "tradier", status: "unavailable", error: brokerCredentialError(error) }, 503); }
    if (!credentials?.token) return json({ provider: "tradier", status: "not_connected" }, 404);
    const result = await brokerTradierRequest(credentials.token, "/markets/quotes", { symbols: symbol, greeks: "false" });
    const quote = result.ok ? brokerTradierQuote(result.value, symbol) : null;
    if (!result.ok || !quote) {
      await brokerRecordProviderFailure("tradier", credentials, result.status, "market_data_access");
      return json({ provider: "tradier", status: [401, 403].includes(result.status) ? "reauthorization_required" : "unavailable" }, 503);
    }
    await brokerRecordVerification("tradier", credentials, "verified", "market_data_access");
    const age = quote.quote_age_seconds;
    if (quote.bid === null || quote.ask === null || quote.bid <= 0 || quote.ask < quote.bid
      || !brokerTradierQuoteFresh(quote)) {
      return json({ provider: "tradier", status: "stale", received_at: new Date().toISOString(), quote: { symbol, bid_at: quote.bid_at, ask_at: quote.ask_at, age_seconds: Number.isFinite(age) ? age : null } });
    }
    return json({ provider: "tradier", status: "available", received_at: new Date().toISOString(), quote });
  }
  return null;
}

