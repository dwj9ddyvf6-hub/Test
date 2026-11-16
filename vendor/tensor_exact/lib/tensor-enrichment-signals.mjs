export const TENSOR_ENRICHMENT_SIGNAL_VERSION = "tensor-enrichment-signals/1.0.0";

export function buildTensorEnrichmentSignals(bar) {
  if (!bar || bar.barFinality !== "closed") return empty();
  const bull = Number(bar.bullishVotes || 0);
  const bear = Number(bar.bearishVotes || 0);
  const signals = [];
  if (bull >= 5 && bull - bear >= 4)
    signals.push(signal("consensus-buy", "▲", "#67f2b0", "below", "Bullish 5-of-7 consensus"));
  if (bear >= 5 && bear - bull >= 4)
    signals.push(signal("consensus-sell", "▼", "#ff6b78", "above", "Bearish 5-of-7 consensus"));

  const lifecycle = lifecycleState(bar, bull, bear);
  if (lifecycle)
    signals.push(signal(
      `state-${lifecycle.toLowerCase()}`,
      lifecycle,
      lifecycleColor(lifecycle),
      lifecycle === "C" || lifecycle === "D" ? "above" : "below",
      `${lifecycle} lifecycle state`,
    ));

  if (bar.primaryMarkers?.length === 0 && bull >= 5 && bar.fastState === "bullish" && bar.slowState !== "bullish")
    signals.push(signal("monitor-buy", "■", "#090b10", "below", "Monitor Buy: fast bullish edge awaiting slow clearance"));

  const range = Number(bar.high) - Number(bar.low);
  const lowerWick = Math.min(Number(bar.open), Number(bar.close)) - Number(bar.low);
  const upperWick = Number(bar.high) - Math.max(Number(bar.open), Number(bar.close));
  if (Number(bar.rvol) >= 1.5 && range > 0 && Math.max(lowerWick, upperWick) / range >= 0.42)
    signals.push(signal("participation-footprint", "✦", "#f7f4ff", lowerWick >= upperWick ? "below" : "above", "High-participation absorption/distribution footprint"));

  if (bar.primaryMarkers?.some(marker => marker.startsWith("buy")) && Number.isFinite(bar.bbUpper) && Number(bar.close) > Number(bar.bbUpper))
    signals.push(signal("extension-warning", "!", "#ffc857", "above", "Buy remains valid; location is extended above the envelope"));

  return {
    version: TENSOR_ENRICHMENT_SIGNAL_VERSION,
    provenance: "tensorContext",
    authority: "additive-overlay",
    usesFutureData: false,
    signals,
  };
}

function empty() {
  return { version: TENSOR_ENRICHMENT_SIGNAL_VERSION, provenance: "tensorContext", authority: "additive-overlay", usesFutureData: false, signals: [] };
}

function signal(id, symbol, color, side, label) {
  return { id, symbol, color, side, label, formulaVersion: TENSOR_ENRICHMENT_SIGNAL_VERSION, additive: true };
}

function lifecycleState(bar, bull, bear) {
  if (bar.activeCall === "bearish" && ["fresh", "reversed"].includes(bar.callLifecycle)) return "D";
  if (bar.activeCall === "bullish" && bear >= 4) return "C";
  if (bar.activeCall === "bullish" && ["fresh", "reinforced"].includes(bar.callLifecycle) && bull >= 5) return "P";
  if (!bar.activeCall && bar.squeezeOn === true && bull >= 4 && Number(bar.rvol || 0) >= 0.8) return "A";
  return null;
}

function lifecycleColor(state) {
  return state === "A" ? "#69e58f" : state === "P" ? "#62e8ff" : state === "C" ? "#ffc857" : "#ff5263";
}
