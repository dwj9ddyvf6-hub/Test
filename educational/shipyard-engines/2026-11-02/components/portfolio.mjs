// CSV constructor and dated-snapshot rebalance schedule. Not an account/holdings connector.
import { parseCsvRows } from './shared/csv.mjs';
import { validProfileDate } from './shared/input-validation.mjs';

export function parseDanelfinCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Portfolio CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 10001) throw new Error('Use a header and between 1 and 10,000 candidate rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const column = (...aliases) => header.findIndex(name => aliases.includes(name));
  const indexes = {
    ticker: column('ticker', 'symbol', 'stocksymbol'),
    score: column('score', 'aiscore'),
    sector: column('sector', 'gicssector'),
    lowRisk: column('lowrisk', 'lowriskscore'),
    volume: column('avg3mvolume', 'average3mvolume', 'avg3monthvolume', 'average3monthvolume', 'avgvolume', 'averagevolume'),
    provenBuy: column('provenbuysignal', 'provenbuy', 'confirmedbuy', 'hasprovenbuysignal'),
    asOf: column('asof', 'date', 'snapshotdate', 'evaluationdate'),
    snapshotComplete: column('snapshotcomplete', 'exportcomplete', 'universeexportcomplete'),
  };
  const missing = ['ticker', 'score', 'sector', 'lowRisk', 'volume'].filter(key => indexes[key] < 0);
  if (missing.length) throw new Error(`Missing required CSV columns: ${missing.join(', ')}. Expected Ticker, Score, Sector, LowRisk, Avg3MVolume; ProvenBuySignal and AsOf are optional.`);
  const rows = [], seenSnapshotTickers = new Set(), dates = new Set(), completenessBySnapshot = new Map();
  let blankAsOf = false;
  const numberAt = (cells, index, label, rowNumber) => {
    const raw = String(cells[index] ?? '').trim().replace(/[$,%\s,]/g, '');
    const value = Number(raw);
    if (!raw || !Number.isFinite(value)) throw new Error(`Row ${rowNumber}: ${label} must be a finite number.`);
    return value;
  };
  for (let i = 1; i < table.length; i++) {
    const cells = table[i];
    if (!cells.some(value => String(value).trim())) continue;
    const rowNumber = i + 1;
    const ticker = String(cells[indexes.ticker] || '').trim().toUpperCase();
    if (!/^[A-Z0-9.^/-]{1,16}$/.test(ticker)) throw new Error(`Row ${rowNumber}: ticker/symbol is missing or invalid.`);
    let asOf = '';
    if (indexes.asOf >= 0) {
      const raw = String(cells[indexes.asOf] || '').trim();
      if (!raw) blankAsOf = true;
      else {
        const time = Date.parse(raw);
        if (!Number.isFinite(time)) throw new Error(`Row ${rowNumber}: AsOf/Date is not a readable date.`);
        asOf = new Date(time).toISOString().slice(0, 10);
        dates.add(asOf);
      }
    }
    let snapshotComplete = null;
    if (indexes.snapshotComplete >= 0) {
      const raw = String(cells[indexes.snapshotComplete] ?? '').trim().toLowerCase();
      if (['true', '1', 'yes', 'y', 'complete'].includes(raw)) snapshotComplete = true;
      else if (['false', '0', 'no', 'n', 'partial'].includes(raw)) snapshotComplete = false;
      else if (raw) throw new Error(`Row ${rowNumber}: SnapshotComplete must be true/false, yes/no, complete/partial, or blank.`);
      const key = asOf || 'UNDATED';
      if (completenessBySnapshot.has(key) && completenessBySnapshot.get(key) !== snapshotComplete) {
        throw new Error(`Row ${rowNumber}: SnapshotComplete must use one consistent value for ${asOf || 'the undated snapshot'}.`);
      }
      completenessBySnapshot.set(key, snapshotComplete);
    }
    const snapshotTickerKey = `${asOf || 'UNDATED'}|${ticker}`;
    if (seenSnapshotTickers.has(snapshotTickerKey)) throw new Error(`Row ${rowNumber}: duplicate ticker ${ticker} for ${asOf || 'the undated snapshot'}; use one row per symbol per snapshot.`);
    seenSnapshotTickers.add(snapshotTickerKey);
    const sector = String(cells[indexes.sector] || '').trim();
    if (!sector) throw new Error(`Row ${rowNumber}: sector is required.`);
    const score = numberAt(cells, indexes.score, 'Score', rowNumber);
    const lowRisk = numberAt(cells, indexes.lowRisk, 'LowRisk', rowNumber);
    const avg3mVolume = numberAt(cells, indexes.volume, 'Avg3MVolume', rowNumber);
    if (score < 1 || score > 10) throw new Error(`Row ${rowNumber}: Score must be between 1 and 10.`);
    if (lowRisk < 1 || lowRisk > 10) throw new Error(`Row ${rowNumber}: LowRisk must be between 1 and 10.`);
    if (avg3mVolume < 0) throw new Error(`Row ${rowNumber}: Avg3MVolume cannot be negative.`);
    let provenBuy = false;
    if (indexes.provenBuy >= 0) {
      const raw = String(cells[indexes.provenBuy] ?? '').trim().toLowerCase();
      if (['true', 'yes', '1', 'buy', 'confirmed'].includes(raw)) provenBuy = true;
      else if (!['', 'false', 'no', '0', 'none', 'no signal'].includes(raw)) throw new Error(`Row ${rowNumber}: ProvenBuySignal must be true/false, yes/no, or blank.`);
    }
    rows.push({ ticker, sector, score, lowRisk, avg3mVolume, provenBuy, asOf, snapshotComplete });
  }
  if (!rows.length) throw new Error('The CSV contains no candidate rows.');
  if (indexes.asOf >= 0 && dates.size && blankAsOf) throw new Error('Every row must include a valid AsOf/Date when any dated snapshots are present.');
  const snapshotDates = [...dates].sort();
  return {
    rows,
    provenBuyProvided: indexes.provenBuy >= 0,
    asOf: snapshotDates.at(-1) || '',
    startDate: snapshotDates[0] || '',
    snapshotDates,
  };
}

export function buildDanelfinPortfolio(rows, preferProvenBuy = true) {
  const eligible = [], rejected = [];
  const sectorMap = new Map();
  for (const row of rows) {
    const reasons = [];
    if (row.lowRisk < 5) reasons.push('Low Risk below 5');
    if (row.avg3mVolume <= 100000) reasons.push('3-month average volume is not above 100,000');
    if (reasons.length) rejected.push({ ...row, decision: reasons.join('; '), decisionCode: 'filtered', sectorRank: null, nameRank: null, sectorMean: null });
    else {
      eligible.push(row);
      const key = row.sector.toLowerCase();
      if (!sectorMap.has(key)) sectorMap.set(key, { key, name: row.sector, rows: [] });
      sectorMap.get(key).rows.push(row);
    }
  }
  const sectors = [...sectorMap.values()].map(group => ({
    ...group,
    meanScore: group.rows.reduce((sum, row) => sum + row.score, 0) / group.rows.length,
  })).sort((a, b) => b.meanScore - a.meanScore || a.name.localeCompare(b.name));
  sectors.forEach((sector, index) => { sector.rank = index + 1; sector.inPortfolio = index < 5; });
  const chosenSectorKeys = new Set(sectors.slice(0, 5).map(sector => sector.key));
  const chosen = [];
  const nonChosen = [];
  for (const sector of sectors) {
    const ranked = sector.rows.slice().sort((a, b) => {
      if (preferProvenBuy && a.provenBuy !== b.provenBuy) return Number(b.provenBuy) - Number(a.provenBuy);
      return b.score - a.score || a.ticker.localeCompare(b.ticker);
    });
    ranked.forEach((row, index) => {
      const item = { ...row, sectorRank: sector.rank, sectorMean: sector.meanScore, nameRank: index + 1 };
      if (!chosenSectorKeys.has(sector.key)) nonChosen.push({ ...item, decision: 'Sector outside the top five', decisionCode: 'sector-out' });
      else if (index < 5) chosen.push({ ...item, decision: 'Selected', decisionCode: 'selected' });
      else nonChosen.push({ ...item, decision: 'Reserve beyond five names for this sector', decisionCode: 'reserve' });
    });
  }
  const weightPct = chosen.length ? 100 / chosen.length : 0;
  chosen.forEach(row => { row.weightPct = weightPct; });
  const auditRows = [...chosen, ...nonChosen, ...rejected].sort((a, b) => {
    const sectorA = a.sectorRank ?? Number.MAX_SAFE_INTEGER, sectorB = b.sectorRank ?? Number.MAX_SAFE_INTEGER;
    return sectorA - sectorB || (a.nameRank ?? Number.MAX_SAFE_INTEGER) - (b.nameRank ?? Number.MAX_SAFE_INTEGER) || a.ticker.localeCompare(b.ticker);
  });
  return { eligible, sectors, chosen, auditRows, filteredCount: rejected.length, preferProvenBuy };
}

export function shiftDanelfinCalendarDate(dateValue, months) {
  if (!validProfileDate(dateValue) || !Number.isInteger(months)) return null;
  const [year, month, day] = dateValue.split('-').map(Number);
  const firstOfMonth = new Date(Date.UTC(year, month - 1, 1));
  firstOfMonth.setUTCMonth(firstOfMonth.getUTCMonth() + months);
  const targetYear = firstOfMonth.getUTCFullYear(), targetMonth = firstOfMonth.getUTCMonth();
  const lastDay = new Date(Date.UTC(targetYear, targetMonth + 1, 0)).getUTCDate();
  const result = new Date(Date.UTC(targetYear, targetMonth, Math.min(day, lastDay)));
  return result.toISOString().slice(0, 10);
}

export function buildDanelfinRebalancePlan(rows, startDate, preferProvenBuy = true) {
  const snapshots = new Map();
  for (const row of rows) {
    if (!validProfileDate(row.asOf)) continue;
    if (!snapshots.has(row.asOf)) snapshots.set(row.asOf, []);
    snapshots.get(row.asOf).push(row);
  }
  const snapshotDates = [...snapshots.keys()].sort();
  const inceptionDate = validProfileDate(startDate) ? startDate : snapshotDates[0] || '';
  if (!snapshotDates.length || !inceptionDate) return { status: 'NO_DATED_SNAPSHOTS', startDate: inceptionDate, snapshotDates, events: [], maxSnapshotAgeDays: 7 };

  const maxSnapshotAgeDays = 7;
  const lastSnapshotDate = snapshotDates.at(-1);
  const events = [];
  let priorTickers = [];
  for (let monthOffset = 0; monthOffset <= 1200; monthOffset += 3) {
    const dueDate = shiftDanelfinCalendarDate(inceptionDate, monthOffset);
    if (!dueDate) break;
    const snapshotDate = snapshotDates.filter(date => date <= dueDate).at(-1) || '';
    const ageDays = snapshotDate ? (Date.parse(`${dueDate}T00:00:00Z`) - Date.parse(`${snapshotDate}T00:00:00Z`)) / 86400000 : null;
    const annualWeightReviewDue = monthOffset === 0 || monthOffset % 12 === 0;
    if (!snapshotDate || ageDays > maxSnapshotAgeDays) {
      events.push({
        monthOffset, dueDate, snapshotDate, ageDays, status: 'NO_FRESH_SNAPSHOT',
        selectedTickers: [], addedTickers: [], removedTickers: [],
        annualWeightReviewDue, targetWeightPct: null,
      });
      if (dueDate > lastSnapshotDate) break;
      continue;
    }
    const snapshotRows = snapshots.get(snapshotDate);
    const snapshotCompleteness = snapshotRows[0]?.snapshotComplete;
    if (snapshotCompleteness !== true) {
      events.push({
        monthOffset, dueDate, snapshotDate, ageDays,
        status: snapshotCompleteness === false ? 'SNAPSHOT_DECLARED_PARTIAL' : 'SNAPSHOT_COMPLETENESS_UNKNOWN',
        selectedTickers: [], addedTickers: [], removedTickers: [],
        annualWeightReviewDue, targetWeightPct: null,
      });
      if (dueDate > lastSnapshotDate) break;
      continue;
    }
    const portfolio = buildDanelfinPortfolio(snapshotRows, preferProvenBuy);
    const selectedTickers = portfolio.chosen.map(row => row.ticker);
    const selectedSet = new Set(selectedTickers), priorSet = new Set(priorTickers);
    const addedTickers = selectedTickers.filter(ticker => !priorSet.has(ticker)).sort();
    const removedTickers = priorTickers.filter(ticker => !selectedSet.has(ticker)).sort();
    events.push({
      monthOffset, dueDate, snapshotDate, ageDays,
      status: monthOffset === 0 ? 'INITIAL_ALLOCATION' : 'MEMBERSHIP_REVIEW',
      selectedTickers, addedTickers, removedTickers,
      annualWeightReviewDue,
      targetWeightPct: annualWeightReviewDue && selectedTickers.length ? 100 / selectedTickers.length : null,
    });
    priorTickers = selectedTickers;
    if (dueDate > lastSnapshotDate) break;
  }
  return {
    status: events.some(event => event.status !== 'NO_FRESH_SNAPSHOT') ? 'READY' : 'NO_FRESH_SNAPSHOT',
    startDate: inceptionDate,
    lastSnapshotDate,
    maxSnapshotAgeDays,
    snapshotCount: snapshotDates.length,
    events,
  };
}
