export const TENSOR_SWING_NOTIFICATION_VERSION = "tensor-swing-notification/0.2.0-watchlist-live";

function price(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "pending";
  return value >= 100 ? value.toFixed(2) : value >= 10 ? value.toFixed(2) : value.toFixed(3);
}

/** Returns a compact, deduplicable notification payload; it does not send it. */
export function buildTensorSwingNotification({ symbol, signal, url = "" } = {}) {
  if (!signal?.setup) return null;
  const ticker = String(symbol || "").trim().toUpperCase();
  const kind = signal.confirmed ? "confirmed" : "setup";
  const eventKey = `${ticker}:1h:swing:${signal.setupBarTimestamp || "unknown"}:${kind}`;
  const body = signal.confirmed
    ? signal.transition?.eligible
      ? `${ticker} · yellow floor + fast-ribbon reclaim · primary basket`
      : `${ticker} · ${signal.phenotype.toLowerCase()} · black square → green arrow · stop ${price(signal.invalidation)} · target ${price(signal.target)}`
    : `${ticker} · black square · waiting for green arrow`;
  return {
    version: TENSOR_SWING_NOTIFICATION_VERSION,
    kind,
    eventKey,
    title: signal.confirmed ? (signal.transition?.eligible ? "Tensor 1H Swing Transition" : "Tensor 1H swing") : "Tensor 1H setup",
    body,
    url,
    usesFutureData: false,
  };
}
