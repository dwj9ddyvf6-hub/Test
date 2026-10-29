import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { EVIDENCE_CONTRACT, EVIDENCE_CONTRACT_VERSION, SOURCE_REGISTRY_VERSION } from './evidence-contract.mjs';
import { MORGUE_FEED_PATH, summarizeMorgueReadiness, summarizeMorgueSnapshot } from './morgue-adapter.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 4173);
const host = '127.0.0.1';
let boundPort = port;
const apiBase = 'https://api.unusualwhales.com';
const hasApiKey = Boolean(process.env.UW_API_KEY?.trim());
const morgueFeedPath = path.resolve(here, '..', '..', MORGUE_FEED_PATH);

const mime = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.md', 'text/markdown; charset=utf-8'],
  ['.png', 'image/png'],
  ['.ico', 'image/x-icon'],
]);

const json = (res, status, body) => {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  res.end(JSON.stringify(body));
};

function onlyParams(url, allowed) {
  for (const key of url.searchParams.keys()) {
    if (!allowed.includes(key)) throw new Error(`Unsupported query parameter: ${key}`);
  }
  return new URLSearchParams([...url.searchParams.entries()]);
}

function safeTicker(value) {
  const ticker = String(value || '').toUpperCase();
  if (!/^[A-Z0-9.-]{1,10}$/.test(ticker)) throw new Error('Ticker must contain 1–10 letters, digits, dots, or hyphens.');
  return ticker;
}

function upstreamRequest(url) {
  if (!hasApiKey) return json(url.res, 503, { error: 'uw_api_key_not_configured', message: 'Set UW_API_KEY in the server environment to enable live reads.' });
  return fetch(url.href, {
    method: 'GET',
    headers: { Authorization: `Bearer ${process.env.UW_API_KEY.trim()}`, Accept: 'application/json' },
    signal: AbortSignal.timeout(12000),
    redirect: 'error',
  }).then(async (response) => {
    const maxBytes = 4 * 1024 * 1024;
    const declaredLength = Number(response.headers.get('content-length') || 0);
    if (declaredLength > maxBytes) {
      await response.body?.cancel();
      return json(url.res, 502, { error: 'upstream_response_too_large', message: 'The upstream response exceeded the 4 MiB local limit.' });
    }
    const reader = response.body?.getReader();
    const chunks = [];
    let size = 0;
    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > maxBytes) {
          await reader.cancel();
          return json(url.res, 502, { error: 'upstream_response_too_large', message: 'The upstream response exceeded the 4 MiB local limit.' });
        }
        chunks.push(Buffer.from(value));
      }
    }
    const text = Buffer.concat(chunks, size).toString('utf8');
    let body;
    try { body = JSON.parse(text); } catch { body = { message: 'The upstream returned a non-JSON response.' }; }
    json(url.res, response.status, body);
  }).catch((error) => {
    const timedOut = error?.name === 'TimeoutError' || error?.name === 'AbortError';
    json(url.res, timedOut ? 504 : 502, {
      error: timedOut ? 'upstream_timeout' : 'upstream_unavailable',
      message: timedOut ? 'The market-data request timed out.' : 'The market-data provider could not be reached.',
    });
  });
}

async function handleApi(req, res, url) {
  if (req.method !== 'GET') return json(res, 405, { error: 'method_not_allowed', message: 'This local connector accepts GET requests only.' });
  if (url.pathname === '/api/status') {
    return json(res, 200, {
      mode: hasApiKey ? 'configured' : 'demo',
      provider: hasApiKey ? 'Unusual Whales API' : 'Synthetic fixtures',
      server: { host, port: boundPort },
      keyConfigured: hasApiKey,
      evidenceContractVersion: EVIDENCE_CONTRACT_VERSION,
      sourceRegistryVersion: SOURCE_REGISTRY_VERSION,
      terminalIngestionEnabled: false,
      providerEntitlementVerified: false,
      allowedReads: ['market-tide', 'flow', 'gex', 'darkpool', 'news', 'movers'],
    });
  }
  if (url.pathname === '/api/health/readiness') {
    try {
      onlyParams(url, []);
    } catch (error) {
      return json(res, 400, { error: 'invalid_request', message: error.message });
    }
    try {
      const bytes = await readFile(morgueFeedPath);
      const snapshot = summarizeMorgueSnapshot(bytes);
      return json(res, 200, summarizeMorgueReadiness(snapshot));
    } catch (error) {
      const artifactStatus = error?.code === 'ENOENT' ? 'missing' : 'invalid';
      return json(res, 200, summarizeMorgueReadiness(null, {
        artifactStatus,
        reason: artifactStatus === 'missing'
          ? 'The local Morgue snapshot is not present.'
          : 'The local Morgue snapshot could not be validated.',
      }));
    }
  }
  if (url.pathname === '/api/evidence-contract') {
    return json(res, 200, EVIDENCE_CONTRACT);
  }
  if (url.pathname === '/api/engines/morgue/v1/snapshot') {
    try {
      onlyParams(url, []);
    } catch (error) {
      return json(res, 400, { error: 'invalid_request', message: error.message });
    }
    try {
      const bytes = await readFile(morgueFeedPath);
      return json(res, 200, summarizeMorgueSnapshot(bytes));
    } catch (error) {
      const status = error?.code === 'ENOENT' ? 503 : 502;
      return json(res, status, {
        error: status === 503 ? 'morgue_snapshot_unavailable' : 'morgue_snapshot_invalid',
        message: status === 503 ? 'The local Morgue snapshot is not present.' : 'The local Morgue snapshot could not be validated.',
      });
    }
  }
  if (!url.pathname.startsWith('/api/uw/')) return json(res, 404, { error: 'not_found' });

  const resource = url.pathname.slice('/api/uw/'.length);
  let target;
  try {
    switch (resource) {
      case 'market-tide': {
        const params = onlyParams(url, ['date', 'interval_5m']);
        if (params.has('date') && !/^\d{4}-\d{2}-\d{2}$/.test(params.get('date'))) throw new Error('date must use YYYY-MM-DD.');
        if (params.has('interval_5m') && !/^(true|false)$/.test(params.get('interval_5m'))) throw new Error('interval_5m must be true or false.');
        target = new URL('/api/market/market-tide', apiBase);
        target.search = params.toString();
        break;
      }
      case 'flow': {
        onlyParams(url, ['ticker']);
        target = new URL(`/api/stock/${safeTicker(url.searchParams.get('ticker'))}/flow-recent`, apiBase);
        break;
      }
      case 'gex': {
        onlyParams(url, ['ticker', 'date', 'source']);
        const params = new URLSearchParams();
        const date = url.searchParams.get('date');
        const source = url.searchParams.get('source');
        if (date && !/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error('date must use YYYY-MM-DD.');
        if (source && !['vol', 'oi'].includes(source)) throw new Error('source must be vol or oi.');
        if (date) params.set('date', date);
        if (source) params.set('source', source);
        target = new URL(`/api/stock/${safeTicker(url.searchParams.get('ticker'))}/gex-levels`, apiBase);
        target.search = params.toString();
        break;
      }
      case 'darkpool': {
        onlyParams(url, ['ticker']);
        const ticker = url.searchParams.get('ticker');
        target = new URL(ticker ? `/api/darkpool/${safeTicker(ticker)}` : '/api/darkpool/recent', apiBase);
        break;
      }
      case 'news': {
        onlyParams(url, ['ticker']);
        target = new URL('/api/news/headlines', apiBase);
        if (url.searchParams.has('ticker')) target.searchParams.set('ticker', safeTicker(url.searchParams.get('ticker')));
        break;
      }
      case 'movers': {
        onlyParams(url, []);
        target = new URL('/api/market/movers', apiBase);
        break;
      }
      default:
        return json(res, 404, { error: 'unsupported_read', message: 'That market-data route is not in the local read allowlist.' });
    }
  } catch (error) {
    return json(res, 400, { error: 'invalid_request', message: error.message });
  }

  return upstreamRequest({ href: target.href, res });
}

async function handle(req, res) {
  const url = new URL(req.url, `http://${host}:${boundPort}`);
  if (url.pathname.startsWith('/api/')) {
    const origin = req.headers.origin;
    const requestHost = String(req.headers.host || '').toLowerCase();
    const localHosts = new Set([`${host}:${boundPort}`, `localhost:${boundPort}`].map(v => v.toLowerCase()));
    if (!localHosts.has(requestHost)) return json(res, 403, { error: 'local_host_required' });
    if (origin) {
      try {
        const originUrl = new URL(origin);
        if (!['localhost', '127.0.0.1'].includes(originUrl.hostname) || originUrl.host.toLowerCase() !== requestHost) return json(res, 403, { error: 'local_origin_required' });
      } catch { return json(res, 403, { error: 'invalid_origin' }); }
    }
    return handleApi(req, res, url);
  }
  if (req.method !== 'GET' && req.method !== 'HEAD') return json(res, 405, { error: 'method_not_allowed' });

  let pathname;
  try { pathname = decodeURIComponent(url.pathname); } catch { return json(res, 400, { error: 'invalid_path' }); }
  if (pathname.includes('..') || pathname.includes('\0')) return json(res, 400, { error: 'invalid_path' });
  const researchFiles = {
    '/research/unusual_whales/PRODUCT_APPROXIMATION.md': 'PRODUCT_APPROXIMATION.md',
    '/research/unusual_whales/MICROSTRUCTURE_RESEARCH.md': 'MICROSTRUCTURE_RESEARCH.md',
  };
  const researchFile = researchFiles[pathname];
  const fileRoot = researchFile ? path.resolve(here, '..', '..') : here;
  const filePath = researchFile
    ? path.resolve(fileRoot, 'research', 'unusual_whales', researchFile)
    : path.resolve(here, `.${pathname === '/' ? '/index.html' : pathname}`);
  if (filePath !== fileRoot && !filePath.startsWith(`${fileRoot}${path.sep}`)) return json(res, 403, { error: 'forbidden' });
  try {
    const body = await readFile(filePath);
    res.writeHead(200, {
      'Content-Type': mime.get(path.extname(filePath).toLowerCase()) || 'application/octet-stream',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'",
      'Referrer-Policy': 'no-referrer',
    });
    if (req.method === 'HEAD') return res.end();
    res.end(body);
  } catch {
    json(res, 404, { error: 'not_found' });
  }
}

const server = createServer((req, res) => { void handle(req, res); });
server.listen(port, host, () => {
  boundPort = server.address().port;
  process.stdout.write(`Silicon Market Terminal: http://${host}:${boundPort}\n`);
  process.stdout.write(`Data provider: ${hasApiKey ? 'configured server-side' : 'synthetic demo mode'}\n`);
});
