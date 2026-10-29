// Keep the chart history contract in one small shared module so provider,
// worker, preview, and browser surfaces cannot drift apart.
export const TENSOR_CHART_BASE_DISPLAY_BARS = 80;
export const TENSOR_CHART_HISTORY_MULTIPLIER = 2;
export const TENSOR_CHART_DISPLAY_BARS =
  TENSOR_CHART_BASE_DISPLAY_BARS * TENSOR_CHART_HISTORY_MULTIPLIER;

export function tensorChartDisplayBars(availableBars) {
  const available = Math.max(0, Math.floor(Number(availableBars) || 0));
  return Math.min(TENSOR_CHART_DISPLAY_BARS, available);
}
