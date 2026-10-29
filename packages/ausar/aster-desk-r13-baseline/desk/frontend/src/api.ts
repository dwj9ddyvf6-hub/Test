export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const slowRead = path === '/research/collect' || path.startsWith('/market/bars/') || /^\/market\/revisions\/[^/]+\/continue$/.test(path);
  const response = await fetch(`/api${path}`, {
    method, headers: body === undefined ? undefined : {'Content-Type': 'application/json'},
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(slowRead ? 45000 : 15000),
  }).catch((error: unknown) => {
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new Error(method === 'GET' ? 'The data request timed out. Try refreshing the desk.' : 'The request timed out; its outcome is not yet confirmed. Refresh the desk before retrying.');
    }
    throw error;
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: {msg?: string; loc?: string[]}) => `${(item.loc || []).filter(x => x !== 'body').join('.')}: ${item.msg || 'Invalid value'}`).join('; ')
      : `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
