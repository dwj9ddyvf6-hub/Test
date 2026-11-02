// User-supplied options-activity CSV parser and completeness-aware descriptive metrics.
import { parseCsvRows } from './shared/csv.mjs';
import { normalizeTicker, validProfileDate } from './shared/input-validation.mjs';

export function parseEtClock(value) {
  const match = /^(?:([01]\d|2[0-3])):([0-5]\d)(?::([0-5]\d))?$/.exec(String(value || ''));
  return match ? Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3] || 0) : null;
}

export function parseBullflowSourceTimestamp(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  let milliseconds = null;
  if (/^\d{10}(?:\.\d+)?$/.test(raw)) milliseconds = Number(raw) * 1000;
  else if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$/.test(raw)) milliseconds = Date.parse(raw);
  return Number.isFinite(milliseconds) ? new Date(milliseconds) : null;
}

export function bullflowTimestampMatchesEt(eventTimestamp, date, timeValue) {
  if (!(eventTimestamp instanceof Date) || !Number.isFinite(eventTimestamp.getTime())) return false;
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  }).formatToParts(eventTimestamp).filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
  const expected = /^\d{4}-\d{2}-\d{2}$/.test(date) && parseEtClock(timeValue) !== null ? timeValue.split(':') : null;
  if (!expected) return false;
  const matches = parts.year === date.slice(0, 4) && parts.month === date.slice(5, 7) && parts.day === date.slice(8, 10)
    && parts.hour === expected[0] && parts.minute === expected[1];
  return matches && (expected.length < 3 || parts.second === expected[2]);
}

export function normalizeExecutionSide(value) {
  const side = String(value || '').trim().toLowerCase().replace(/[^a-z]/g, '');
  return ({ ask: 'ASK', atask: 'ASK', aboveask: 'ABOVE_ASK', aa: 'ABOVE_ASK', bid: 'BID', atbid: 'BID', belowbid: 'BELOW_BID', bb: 'BELOW_BID', mid: 'MID', midpoint: 'MID', atmid: 'MID', unknown: 'UNKNOWN', other: 'UNKNOWN' })[side] || null;
}

export function parseBullflowActivityCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Options activity CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 50001) throw new Error('Use a header and between 1 and 50,000 activity or coverage rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const column = (...aliases) => header.findIndex(name => aliases.includes(name));
  const ix = {
    date: column('date', 'sessiondate'), time: column('timeet', 'executiontimeet'), ticker: column('ticker', 'symbol'),
    contract: column('contract', 'optioncontract'), expiry: column('expiry', 'expiration', 'expirationdate'),
    type: column('type', 'optiontype', 'right'), strike: column('strike', 'strikeprice'),
    size: column('size', 'volume', 'contracts'), premium: column('premium', 'premiumusd', 'totalpremium', 'transactionpremium'),
    side: column('side', 'executionside'), tradeType: column('tradetype', 'tradekind'), oi: column('oi', 'openinterest'),
    available: column('available', 'sessionavailable', 'dataavailable'), cancelled: column('cancelled', 'iscancelled', 'canceled', 'iscanceled'),
    exportComplete: column('exportcomplete', 'querycomplete', 'sessioncomplete'), source: column('source', 'datasource', 'sourcename'),
    tradeId: column('tradeid', 'sourcerecordid', 'recordid', 'id'), sideSource: column('sidesource', 'sideprovenance'),
    sourceTimestamp: column('timestamp', 'sourcetimestamp', 'tradeeventtimestamp'),
  };
  const missing = ['date', 'time', 'ticker', 'contract', 'expiry', 'type', 'strike', 'size', 'premium', 'side', 'tradeType', 'oi'].filter(key => ix[key] < 0);
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(', ')}.`);
  const rows = [], sessions = new Map(), tradeIds = new Set();
  const cell = (cells, key) => String(cells[ix[key]] ?? '').trim();
  const sessionKey = (ticker, date) => `${ticker}|${date}`;
  const sessionFor = (ticker, date) => {
    const key = sessionKey(ticker, date);
    if (!sessions.has(key)) sessions.set(key, { ticker, date, available: true, exportComplete: null, explicitCoverage: false, source: '' });
    return sessions.get(key);
  };
  const number = (raw, name, rowNumber, optional = false) => {
    if (!raw && optional) return null;
    const value = Number(raw.replace(/[$,%\s,]/g, ''));
    if (!raw || !Number.isFinite(value)) throw new Error(`Row ${rowNumber}: ${name} must be a finite number.`);
    return value;
  };
  const bool = raw => {
    const value = String(raw || '').trim().toLowerCase();
    if (['true', '1', 'yes', 'y'].includes(value)) return true;
    if (['false', '0', 'no', 'n'].includes(value)) return false;
    return null;
  };
  for (let i = 1; i < table.length; i++) {
    const cells = table[i], rowNumber = i + 1;
    const date = cell(cells, 'date'), ticker = normalizeTicker(cell(cells, 'ticker'));
    if (!validProfileDate(date) || !ticker) throw new Error(`Row ${rowNumber}: Date must be YYYY-MM-DD and Ticker must be valid.`);
    const contract = cell(cells, 'contract');
    const sizeRaw = cell(cells, 'size');
    const size = sizeRaw ? number(sizeRaw, 'Size', rowNumber) : 0;
    const isCoverageMarker = !contract && size === 0;
    const availabilityRaw = ix.available < 0 ? '' : String(cells[ix.available] ?? '').trim();
    if (isCoverageMarker) {
      const marker = bool(availabilityRaw);
      if (marker === null) throw new Error(`Row ${rowNumber}: a zero-activity coverage row needs Available=true or false.`);
      const completeRaw = ix.exportComplete < 0 ? '' : cell(cells, 'exportComplete');
      const exportComplete = completeRaw ? bool(completeRaw) : null;
      if (completeRaw && exportComplete === null) throw new Error(`Row ${rowNumber}: ExportComplete must be true or false when provided.`);
      if (!marker && exportComplete === true) throw new Error(`Row ${rowNumber}: an unavailable session cannot be marked ExportComplete=true.`);
      const session = sessionFor(ticker, date);
      if (session.explicitCoverage) throw new Error(`Row ${rowNumber}: duplicate coverage declaration for ${ticker} ${date}.`);
      if (session.hasPrints && !marker) throw new Error(`Row ${rowNumber}: a session with print rows cannot be marked unavailable.`);
      session.available = marker;
      session.exportComplete = exportComplete;
      session.explicitCoverage = true;
      session.source = cell(cells, 'source') || session.source;
      continue;
    }
    if (!contract || contract.length > 100 || !Number.isSafeInteger(size) || size < 1 || size > 1e7) throw new Error(`Row ${rowNumber}: a print needs a contract and an integer Size from 1 to 10,000,000.`);
    if (availabilityRaw && bool(availabilityRaw) !== true) throw new Error(`Row ${rowNumber}: a print row must use Available=true.`);
    if (ix.exportComplete >= 0 && cell(cells, 'exportComplete')) throw new Error(`Row ${rowNumber}: declare ExportComplete on a coverage-only row, not a print row.`);
    const timeSeconds = parseEtClock(cell(cells, 'time'));
    const typeRaw = cell(cells, 'type').toUpperCase();
    const type = typeRaw === 'C' ? 'CALL' : typeRaw === 'P' ? 'PUT' : typeRaw;
    const side = normalizeExecutionSide(cell(cells, 'side'));
    const cancelledRaw = ix.cancelled < 0 ? '' : cell(cells, 'cancelled');
    const cancelled = cancelledRaw ? bool(cancelledRaw) : (ix.cancelled < 0 ? false : null);
    const strike = number(cell(cells, 'strike'), 'Strike', rowNumber);
    const premium = number(cell(cells, 'premium'), 'Premium', rowNumber);
    const openInterest = number(cell(cells, 'oi'), 'OpenInterest', rowNumber, true);
    const expiry = cell(cells, 'expiry');
    const source = cell(cells, 'source');
    if (/^(synthetic|sample|fixture)$/i.test(source.trim())) throw new Error(`Row ${rowNumber}: synthetic, sample, and fixture records are not accepted as market input.`);
    const tradeId = cell(cells, 'tradeId');
    const sourceTimestampRaw = ix.sourceTimestamp < 0 ? '' : cell(cells, 'sourceTimestamp');
    const sourceTimestamp = sourceTimestampRaw ? parseBullflowSourceTimestamp(sourceTimestampRaw) : null;
    const sideSource = (cell(cells, 'sideSource') || 'unknown').toUpperCase().replace(/[^A-Z]/g, '');
    const sideSourceValue = ({ VENDOR: 'VENDOR', USER: 'USER', INFERRED: 'INFERRED', UNKNOWN: 'UNKNOWN' })[sideSource];
    if (timeSeconds === null) throw new Error(`Row ${rowNumber}: TimeET must use HH:MM or HH:MM:SS.`);
    if (ix.sourceTimestamp >= 0 && (!sourceTimestampRaw || !sourceTimestamp)) throw new Error(`Row ${rowNumber}: Timestamp must be Unix seconds or ISO 8601 with an explicit UTC offset.`);
    if (sourceTimestamp && !bullflowTimestampMatchesEt(sourceTimestamp, date, cell(cells, 'time'))) throw new Error(`Row ${rowNumber}: Timestamp must match Date and TimeET in America/New_York.`);
    if (cancelled === null) throw new Error(`Row ${rowNumber}: Cancelled must be true or false when that column is present.`);
    if (!['CALL', 'PUT'].includes(type) || !side || !sideSourceValue || strike <= 0 || premium < 0 || (openInterest !== null && openInterest < 0)) throw new Error(`Row ${rowNumber}: check Type, Side, SideSource (vendor/user/inferred/unknown), positive Strike, nonnegative Premium, and OpenInterest.`);
    if (expiry && !validProfileDate(expiry)) throw new Error(`Row ${rowNumber}: Expiry must be YYYY-MM-DD or blank.`);
    const session = sessionFor(ticker, date);
    if (!session.available) throw new Error(`Row ${rowNumber}: a print row conflicts with an unavailable session declaration.`);
    session.hasPrints = true;
    session.source ||= source;
    if (tradeId) {
      if (tradeId.length > 160) throw new Error(`Row ${rowNumber}: TradeID must be 160 characters or fewer.`);
      const idKey = `${source.toLowerCase()}|${tradeId}`;
      if (tradeIds.has(idKey)) throw new Error(`Row ${rowNumber}: duplicate TradeID ${tradeId} for source ${source || 'unspecified'}.`);
      tradeIds.add(idKey);
    }
    rows.push({ sessionDate: date, timeSeconds, ticker, contract, expiry: expiry || '', type, strike, size, premium, side, sideSource: sideSourceValue, source: source || '', tradeId: tradeId || '', sourceTimestamp: sourceTimestampRaw || '', tradeType: cell(cells, 'tradeType').toUpperCase().replace(/[^A-Z0-9]/g, ''), openInterest, cancelled });
  }
  const sessionCoverage = Array.from(sessions.values()).map(({ hasPrints, ...session }) => session);
  return {
    rows,
    sessionCoverage,
    availableSessions: sessionCoverage.filter(item => item.available).map(({ available, exportComplete, explicitCoverage, source, ...item }) => ({ ...item, exportComplete })),
    cancellationStatusProvided: ix.cancelled >= 0,
    sideSourceProvided: ix.sideSource >= 0,
    sourceProvided: ix.source >= 0,
    tradeIdProvided: ix.tradeId >= 0,
    sourceTimestampProvided: ix.sourceTimestamp >= 0,
  };
}

export function calculateBullflowActivityProfile(model) {
  const { rows, ticker, asOfDate } = model;
  const cutoff = parseEtClock(model.asOfTime);
  const coverage = model.sessionCoverage || (model.availableSessions || []).map(item => ({ ...item, available: true, exportComplete: item.exportComplete ?? null }));
  const coverageByDate = new Map(coverage.filter(item => item.ticker === ticker).map(item => [item.date, item]));
  const targetCoverage = coverageByDate.get(asOfDate) || null;
  const targetAvailable = targetCoverage?.available === true;
  const targetComplete = targetCoverage?.exportComplete === true;
  const baselineDates = Array.from(new Set(coverage.filter(item => item.ticker === ticker && item.available === true && item.date < asOfDate).map(item => item.date))).sort((a, b) => b.localeCompare(a)).slice(0, 20);
  const baselineSet = new Set(baselineDates);
  const baselineByDate = new Map(baselineDates.map(date => [date, []]));
  for (const row of rows) if (!row.cancelled && row.ticker === ticker && baselineSet.has(row.sessionDate)) baselineByDate.get(row.sessionDate).push(row);
  const targetRows = targetAvailable ? rows.filter(row => !row.cancelled && row.ticker === ticker && row.sessionDate === asOfDate && row.timeSeconds <= cutoff) : [];
  const baselineCompleteCount = baselineDates.filter(date => coverageByDate.get(date)?.exportComplete === true).length;
  const baselinePartialCount = baselineDates.filter(date => coverageByDate.get(date)?.exportComplete === false).length;
  const baselineUnknownCount = baselineDates.length - baselineCompleteCount - baselinePartialCount;
  const baselineComplete = baselineDates.length === 20 && baselineCompleteCount === 20;
  const cancellationComplete = model.cancellationStatusProvided === true;
  const selectedInputComplete = targetAvailable && targetComplete && cancellationComplete;
  const inputComplete = selectedInputComplete && baselineComplete;
  const volume = (items, type, throughTime = null) => items.reduce((sum, row) => sum + (row.type === type && (throughTime === null || row.timeSeconds <= throughTime) ? row.size : 0), 0);
  const observedCallVolume = volume(targetRows, 'CALL'), observedPutVolume = volume(targetRows, 'PUT');
  const observedCallAskVolume = targetRows.reduce((sum, row) => sum + (row.type === 'CALL' && ['ASK', 'ABOVE_ASK'].includes(row.side) ? row.size : 0), 0);
  const completeCallVolume = selectedInputComplete ? observedCallVolume : null;
  const completePutVolume = selectedInputComplete ? observedPutVolume : null;
  const meanVolume = (type, intraday) => !baselineComplete ? null : baselineDates.reduce((sum, date) => sum + volume(baselineByDate.get(date), type, intraday ? cutoff : null), 0) / 20;
  const ratio = (current, baseline) => !inputComplete || current === null || baseline === null || baseline <= 0 ? null : current / baseline;
  const callIntradayRv = ratio(completeCallVolume, meanVolume('CALL', true));
  const putIntradayRv = ratio(completePutVolume, meanVolume('PUT', true));
  const callDailyRv = ratio(completeCallVolume, meanVolume('CALL', false));
  const putDailyRv = ratio(completePutVolume, meanVolume('PUT', false));
  const unknownCallSideSource = targetRows.some(row => row.type === 'CALL' && (row.sideSource || 'UNKNOWN') === 'UNKNOWN');
  const callAskShare = selectedInputComplete && !unknownCallSideSource && observedCallVolume > 0 ? observedCallAskVolume / observedCallVolume : null;
  const putCallRatio = selectedInputComplete && observedCallVolume > 0 ? observedPutVolume / observedCallVolume : null;
  const contractMap = new Map();
  let netDirectionalPremium = 0, totalPremium = 0;
  for (const row of targetRows) {
    totalPremium += row.premium;
    const multi = row.tradeType === 'MULTI' || row.tradeType === 'MULTILEG';
    if (!multi) {
      if (row.type === 'CALL' && ['ASK', 'ABOVE_ASK'].includes(row.side)) netDirectionalPremium += row.premium;
      if (row.type === 'CALL' && ['BID', 'BELOW_BID'].includes(row.side)) netDirectionalPremium -= row.premium;
      if (row.type === 'PUT' && ['ASK', 'ABOVE_ASK'].includes(row.side)) netDirectionalPremium -= row.premium;
      if (row.type === 'PUT' && ['BID', 'BELOW_BID'].includes(row.side)) netDirectionalPremium += row.premium;
    }
    const key = `${row.type}|${row.contract}`;
    const item = contractMap.get(key) || { contract: row.contract, type: row.type, expiry: row.expiry, strike: row.strike, volume: 0, premium: 0, openInterest: null, latestTime: -1 };
    item.volume += row.size;
    item.premium += row.premium;
    if (row.timeSeconds >= item.latestTime && row.openInterest !== null) { item.openInterest = row.openInterest; item.latestTime = row.timeSeconds; }
    contractMap.set(key, item);
  }
  const unusualContracts = Array.from(contractMap.values()).filter(item => item.openInterest > 0 && item.volume / item.openInterest > 1)
    .map(item => ({ ...item, ratio: item.volume / item.openInterest }))
    .sort((a, b) => b.ratio - a.ratio || b.premium - a.premium || a.contract.localeCompare(b.contract)).slice(0, 5);
  const unusualWeekly = Array.from(contractMap.values()).some(item => {
    if (!item.expiry || !(item.openInterest > 0)) return false;
    const dte = (Date.parse(`${item.expiry}T00:00:00Z`) - Date.parse(`${asOfDate}T00:00:00Z`)) / 86400000;
    return dte >= 0 && dte <= 7 && item.volume / item.openInterest >= 2;
  });
  const weeklyInputsUnknown = Array.from(contractMap.values()).some(item => {
    if (!item.expiry) return true;
    const dte = (Date.parse(`${item.expiry}T00:00:00Z`) - Date.parse(`${asOfDate}T00:00:00Z`)) / 86400000;
    return dte >= 0 && dte <= 7 && !(item.openInterest > 0);
  });
  const flags = [
    { name: 'CALL_VOLUME_SPIKE', active: callIntradayRv === null ? null : callIntradayRv >= 2, rule: 'Call intraday relative volume ≥ 2×' },
    { name: 'PUT_VOLUME_SPIKE', active: putIntradayRv === null ? null : putIntradayRv >= 2, rule: 'Put intraday relative volume ≥ 2×' },
    { name: 'CALL_BUYING_SURGE', active: callIntradayRv === null || callAskShare === null ? null : callIntradayRv >= 2 && callAskShare >= 0.7, rule: 'Call intraday relative volume ≥ 2× and ask/above-ask share ≥ 70%' },
    { name: 'UNUSUAL_WEEKLY_ACTIVITY', active: !selectedInputComplete ? null : unusualWeekly ? true : weeklyInputsUnknown ? null : false, rule: 'A 0–7 DTE contract has volume/open interest ≥ 2×' },
  ];
  const statuses = [];
  if (weeklyInputsUnknown) statuses.push('WEEKLY_CONTRACT_OI_OR_EXPIRY_UNKNOWN');
  if (!cancellationComplete) statuses.push('CANCELLATION_STATUS_NOT_PROVIDED');
  if (!targetAvailable) statuses.push('SELECTED_SESSION_UNAVAILABLE');
  if (targetAvailable && !targetComplete) statuses.push(targetCoverage?.exportComplete === false ? 'SELECTED_EXPORT_PARTIAL' : 'SELECTED_EXPORT_COMPLETENESS_UNKNOWN');
  if (baselineDates.length < 20) statuses.push('INSUFFICIENT_HISTORY');
  else if (!baselineComplete) statuses.push(baselinePartialCount ? 'BASELINE_EXPORT_PARTIAL' : 'BASELINE_EXPORT_COMPLETENESS_UNKNOWN');
  if (targetAvailable && targetRows.length === 0) statuses.push(targetComplete ? 'NO_PRINTS_THROUGH_AS_OF' : 'NO_PRINTS_IN_UNVERIFIED_EXPORT');
  const sideProvenanceCounts = Object.fromEntries(['VENDOR', 'USER', 'INFERRED', 'UNKNOWN'].map(source => [source, targetRows.filter(row => (row.sideSource || 'UNKNOWN') === source).length]));
  const sourceTimestampCount = targetRows.filter(row => row.sourceTimestamp).length;
  const directionalSidesAttributed = targetRows.filter(row => row.tradeType !== 'MULTI' && row.tradeType !== 'MULTILEG').every(row => (row.sideSource || 'UNKNOWN') !== 'UNKNOWN');
  const baselineRows = Array.from(baselineByDate.values()).flat();
  const rowSources = Array.from(new Set([
    ...targetRows.map(row => row.source),
    ...baselineRows.map(row => row.source),
    ...baselineDates.map(date => coverageByDate.get(date)?.source),
    targetCoverage?.source,
  ].map(source => String(source || '').trim()).filter(Boolean)));
  if (unknownCallSideSource) statuses.push('CALL_SIDE_PROVENANCE_UNKNOWN');
  if (!directionalSidesAttributed) statuses.push('DIRECTIONAL_SIDE_PROVENANCE_UNKNOWN');
  return {
    targetAvailable, targetComplete, targetRows, baselineCount: baselineDates.length,
    baselineCompleteCount, baselinePartialCount, baselineUnknownCount, inputComplete, selectedInputComplete,
    observedCallVolume, observedPutVolume, callVolume: completeCallVolume, putVolume: completePutVolume,
    callIntradayRv, putIntradayRv, callDailyRv, putDailyRv, callAskShare, putCallRatio,
    netDirectionalPremium: selectedInputComplete && directionalSidesAttributed ? netDirectionalPremium : null,
    totalPremium: selectedInputComplete ? totalPremium : null,
    sideProvenanceCounts, sourceTimestampCount, rowSources, statuses, flags, unusualContracts,
  };
}
