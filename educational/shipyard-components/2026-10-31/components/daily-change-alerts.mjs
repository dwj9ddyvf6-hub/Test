// Pure projection of the terminal's daily-change alert evaluator. Caller persists returned alerts.
export function evaluateChangeAlerts(alerts, feed, { selectCompletedDailyBars = null, now = new Date() } = {}) {
  const currentAlerts = Array.isArray(alerts) ? alerts : [];
  const returnedBars = Array.isArray(feed?.bars) ? feed.bars : [];
  const bars = selectCompletedDailyBars
    ? selectCompletedDailyBars(returnedBars, now, feed?.session_calendar).bars
    : returnedBars;
  if (bars.length < 2) return currentAlerts;
  const latest = bars.at(-1), previous = bars.at(-2);
  if (!(previous.close > 0) || !Number.isFinite(latest.close)) return currentAlerts;
  const changePct = (latest.close / previous.close - 1) * 100;
  return currentAlerts.map(alert => {
    if (alert.condition !== 'change' || alert.ticker !== feed.symbol) return alert;
    const lastEvaluation = { barAt: latest.at, changePct, matched: Math.abs(changePct) >= Number(alert.threshold) };
    return { ...alert, lastEvaluation };
  });
}
