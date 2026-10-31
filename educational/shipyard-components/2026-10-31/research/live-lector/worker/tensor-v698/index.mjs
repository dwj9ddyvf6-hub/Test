import {
  annaEpochForTimestamp, selectEpochSeries, directionalVote, comparisonVote,
  signedVote, stochasticRsi, aroonSeries, directionalMovement, onBalanceVolume,
  slope, squeezeMomentumSeries, sma, ema, waveTrendSeries, wilderAtr,
} from './engine/frozen-v690/lib/anna-replica.mjs';

export const TENSOR_V698_VERSION = 'v698';
const CHANNELS = Object.freeze(['stoch','aroon','di','obv','squeeze','pivot','wave']);
const finite = Number.isFinite;

function invalid(status, detail) { return { status, value: null, detail }; }

function chartSessionDate(timestamp, timezone) {
  if (!Number.isFinite(timestamp)) return null;
  try {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone || 'UTC', year: 'numeric', month: '2-digit', day: '2-digit',
    }).formatToParts(new Date(timestamp));
    const fields = Object.fromEntries(parts.filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
    return fields.year && fields.month && fields.day ? `${fields.year}-${fields.month}-${fields.day}` : null;
  } catch {
    return null;
  }
}

/*
 * Calculate one frame from its own supplied completed OHLCV chart. The seven
 * vote bodies and their parameters are the pinned v698 Tensor helper bodies;
 * this adapter exposes only the state-only result needed by Best Setups.
 */
export function tensorV698Frame(chart, expectedSymbol, expectedInterval, now = Date.now()) {
  if (!chart) return invalid('not_supplied', `No ${expectedInterval} chart is attached.`);
  if (!['1h','1d','1wk'].includes(expectedInterval) || chart.symbol !== expectedSymbol || chart.interval !== expectedInterval)
    return invalid('not_supplied', 'The chart symbol or timeframe does not match the requested Tensor frame.');
  if (chart.input_status?.current === false || Number(chart.input_status?.missing_completed_periods) > 0)
    return invalid('stale', `The latest completed ${expectedInterval} candle is missing.`);
  const bars = chart.bars;
  const minimum = expectedInterval === '1wk' ? 4 : 35;
  if (!Array.isArray(bars) || bars.length < minimum)
    return invalid('insufficient_history', `${expectedInterval} Tensor needs ${minimum} completed candles; ${Array.isArray(bars) ? bars.length : 0} supplied.`);
  if (!Number.isFinite(now)) return invalid('not_supplied', 'The Tensor calculation clock is invalid.');
  const exactCompletion = Date.parse(chart.last_completed_at || '');
  const asOfText = String(chart.last_completed_at || chart.as_of || '');
  const asOf = Date.parse(asOfText);
  const dateOnlyAsOf = !Number.isFinite(exactCompletion) && /^\d{4}-\d{2}-\d{2}$/.test(asOfText);
  const maxAge = expectedInterval === '1h' ? 3 * 86400000 : expectedInterval === '1d' ? 4 * 86400000 : 14 * 86400000;
  if (!Number.isFinite(asOf) || asOf > now || now - asOf > maxAge)
    return invalid('stale', `The latest completed ${expectedInterval} Tensor candle is outside its freshness window.`);
  const received = Date.parse(chart.received_at || chart.observed_at || '');
  if (Number.isFinite(received) && received > now)
    return invalid('stale', 'The chart receipt clock is in the future.');
  let prior = 0;
  for (const bar of bars) {
    const time = Date.parse(bar?.[0]);
    const sessionDate = dateOnlyAsOf ? chartSessionDate(time, chart.timezone) : null;
    const afterAsOf = dateOnlyAsOf ? !sessionDate || sessionDate > asOfText : time > asOf;
    if (!Number.isFinite(time) || time <= prior || time > now || afterAsOf || !Array.isArray(bar) || bar.length < 6 ||
        ![1,2,3,4,5].every(index => typeof bar[index] === 'number' && finite(bar[index])) ||
        Math.min(bar[1],bar[2],bar[3],bar[4]) <= 0 || bar[5] < 0 ||
        bar[2] < Math.max(bar[1],bar[3],bar[4]) || bar[3] > Math.min(bar[1],bar[2],bar[4]))
      return invalid('not_supplied', `A ${expectedInterval} chart candle has invalid chronology or OHLCV geometry.`);
    prior = time;
  }
  const close = bars.map(bar => bar[4]), high = bars.map(bar => bar[2]), low = bars.map(bar => bar[3]), volume = bars.map(bar => bar[5]);
  const profiles = bars.map(bar => annaEpochForTimestamp(Date.parse(bar[0]) / 1000, chart.timezone || 'America/New_York'));
  const momentum = selectEpochSeries(profiles,
    squeezeMomentumSeries(high,low,close,sma(close,14),14,9),
    squeezeMomentumSeries(high,low,close,sma(close,20),20,10));
  const stoch = stochasticRsi(close,14,14,3,3), aroon = aroonSeries(high,low,14), di = directionalMovement(high,low,close,14);
  const obv = onBalanceVolume(close,volume), obvSlope = obv.map((_,index) => slope(obv,index,5));
  const ema8 = ema(close,8), ema21 = ema(close,21), wave = waveTrendSeries(high,low,close,10,21,4);
  const states = bars.map((bar,index) => {
    const momentumSlope = index > 0 && finite(momentum[index]) && finite(momentum[index-1]) ? momentum[index]-momentum[index-1] : null;
    const raw = [
      directionalVote(stoch.k[index],stoch.d[index],index > 0 ? stoch.k[index-1] : null),
      comparisonVote(aroon.up[index],aroon.down[index]),
      comparisonVote(di.plusDi[index],di.minusDi[index]),
      signedVote(obvSlope[index]),
      signedVote(finite(momentumSlope) && momentumSlope !== 0 ? momentumSlope : momentum[index]),
      comparisonVote(ema8[index],ema21[index]),
      comparisonVote(wave.wt1[index],wave.wt2[index]),
    ];
    const stateVotes = CHANNELS.map((id,slot) => ({ id, direction: raw[slot] === 1 ? 'bullish' : raw[slot] === -1 ? 'bearish' : 'neutral', available: raw[slot] !== null }));
    const bullishVotes = raw.filter(value => value === 1).length, bearishVotes = raw.filter(value => value === -1).length;
    return { at: bar[0], stateVotes, bullishVotes, bearishVotes, totalVotes: raw.filter(value => value !== null).length };
  });
  const recent = states.slice(-4), latest = recent.at(-1), balance = latest.bullishVotes - latest.bearishVotes;
  return { status:'measured', value:{
    version:TENSOR_V698_VERSION, symbol:expectedSymbol, interval:expectedInterval,
    as_of:chart.last_completed_at || chart.as_of, bullish_votes:latest.bullishVotes,
    bearish_votes:latest.bearishVotes, total_votes:latest.totalVotes, balance,
    strength:latest.totalVotes ? balance / latest.totalVotes : null,
    direction:balance > 0 ? 'bullish' : balance < 0 ? 'bearish' : 'neutral',
    components:latest.stateVotes, recent,
  }, detail:'' };
}
