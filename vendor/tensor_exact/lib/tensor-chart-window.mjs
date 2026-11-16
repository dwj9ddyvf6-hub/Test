// Keep the chart history contract in one small shared module so provider,
// worker, preview, and browser surfaces cannot drift apart.
export const TENSOR_CHART_BASE_DISPLAY_BARS = 80;
export const TENSOR_CHART_HISTORY_MULTIPLIER = 2;
export const TENSOR_CHART_DISPLAY_BARS =
  TENSOR_CHART_BASE_DISPLAY_BARS * TENSOR_CHART_HISTORY_MULTIPLIER;

export function tensorChartDisplayLimit(interval) {
  return String(interval).toLowerCase() === "1h"
    ? TENSOR_CHART_DISPLAY_BARS * 3
    : TENSOR_CHART_DISPLAY_BARS;
}

export function tensorChartDisplayBars(availableBars, interval) {
  const available = Math.max(0, Math.floor(Number(availableBars) || 0));
  return Math.min(tensorChartDisplayLimit(interval), available);
}
