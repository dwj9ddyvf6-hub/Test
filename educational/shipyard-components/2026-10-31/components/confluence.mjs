// Manual-input scoring candidates; never a live or authenticated score feed.


export const confluenceCategories = [
  { key: 'relativeStrength', label: 'Relative strength', weight: 15, metrics: [['rsMarket', 'Broad-market relative return', 20], ['rsGrowth', 'Growth-market relative return', 10], ['rsSector', 'Sector-relative return', 15], ['peerRank', 'Industry / peer rank', 15], ['rsLine', 'RS-line trend', 15], ['downsideResilience', 'Downside resilience', 15], ['longMomentum', 'Long-term momentum', 10]] },
  { key: 'priceAction', label: 'Price action', weight: 18, metrics: [['trendStructure', 'Trend structure', 20], ['baseQuality', 'Base quality', 20], ['volContraction', 'Volatility contraction', 15], ['pullbackQuality', 'Pullback quality', 15], ['technicalRespect', 'Technical respect', 10], ['stageDevelopment', 'Stage development', 10], ['extension', 'Extension', 10]] },
  { key: 'volumeParticipation', label: 'Volume participation', weight: 15, metrics: [['relVolume', 'Relative volume', 20], ['dollarVolTrend', 'Dollar-volume trend', 10], ['accDist', 'Accumulation / distribution', 20], ['volPriceAgreement', 'Volume-price agreement', 20], ['pullbackVolume', 'Pullback volume', 15], ['participationBreadth', 'Participation breadth', 10], ['expansionReadiness', 'Expansion readiness', 5]] },
  { key: 'trendAlignment', label: 'Trend alignment', weight: 12, metrics: [['emaPosition', 'EMA position', 15], ['emaSlope', 'EMA slope', 15], ['dailyWeeklyAgreement', 'Daily / weekly agreement', 25], ['stageAlignment', 'Stage alignment', 15], ['htfLevelPosition', 'Higher-timeframe level position', 15], ['weeklyAccExhaustion', 'Weekly accumulation / exhaustion', 15]] },
  { key: 'supportResistance', label: 'Support / resistance', weight: 12, metrics: [['supportProximity', 'Support proximity', 20], ['roomToResistance', 'Room to resistance', 20], ['levelSignificance', 'Level significance', 20], ['srConversion', 'Support / resistance conversion', 15], ['tradeGeometry', 'Trade geometry', 20], ['chasePenalty', 'Chase penalty', 5]] },
  { key: 'sectorLeadership', label: 'Sector leadership', weight: 10, metrics: [['sectorStrength', 'Sector strength', 15], ['industryStrength', 'Industry strength', 15], ['capitalRotation', 'Capital rotation', 20], ['stockLeadership', 'Stock leadership', 20], ['peerConfirmation', 'Peer confirmation', 10], ['themeSympathy', 'Theme sympathy', 15], ['crowding', 'Crowding', 5]] },
  { key: 'institutionalPositioning', label: 'Institutional positioning', weight: 8, metrics: [['instOwnership', 'Institutional ownership', 15], ['instActivity', 'Institutional activity', 10], ['insiderActivity', 'Insider activity', 10], ['optionsPositioning', 'Options positioning', 25], ['dealerPositioning', 'Dealer positioning', 15], ['darkPool', 'Dark-pool activity', 15], ['shortPositioning', 'Short positioning', 10]] },
  { key: 'marketContext', label: 'Market context', weight: 10, metrics: [['marketRegime', 'Market regime', 20], ['marketBreadth', 'Market breadth', 20], ['indexAccDist', 'Index accumulation / distribution', 15], ['breakoutFollowThrough', 'Breakout follow-through', 15], ['riskAppetite', 'Risk appetite', 10], ['sectorRotation', 'Sector rotation', 10], ['macroEventRisk', 'Macro event risk', 5], ['indexConfirmation', 'Index confirmation', 5]] },
];

export const confluenceEffectiveCategories = [
  { key: 'relativeStrength', label: 'Relative strength', weight: 15, leaves: [['mom12_1', '12–1 momentum', 7.2], ['rsVsSpy', 'Relative strength vs S&P 500', 5.4]] },
  { key: 'priceAction', label: 'Price action & structure', weight: 18, leaves: [['macd', 'MACD / trend acceleration', 2.7], ['rsi', 'RSI / momentum extremes', 3.6]] },
  { key: 'volumeParticipation', label: 'Volume & participation', weight: 15, leaves: [['volAccum', 'Volume & accumulation', 4.5]] },
  { key: 'trendAlignment', label: 'Higher-timeframe alignment', weight: 12, leaves: [['maTrend', 'Moving-average trend', 3.6]] },
  { key: 'supportResistance', label: 'Key levels & trade geometry', weight: 12, leaves: [['supportResist', 'Support / resistance structure', 3.6]] },
  { key: 'sectorLeadership', label: 'Sector & theme leadership', weight: 10, leaves: [['sectorStrength', 'Sector strength', 3], ['factorFit', 'Factor-regime fit', 3]] },
  { key: 'institutionalPositioning', label: 'Positioning & ownership', weight: 8, leaves: [['insiderActivity', 'Insider activity', 3.75], ['institutionalTrend', 'Institutional ownership trends', 2.25], ['shortInterest', 'Short interest & borrow pressure', 3.75], ['optionsPositioning', 'Options positioning / put-call', 3], ['darkPool', 'Dark-pool / block activity', 2.25]] },
  { key: 'marketContext', label: 'Broader market context', weight: 10, externalFramework: true, leaves: [['macroEnv', 'Macro environment', 2.4], ['fedOutlook', 'Fed rates outlook', 1.8], ['volatilityFear', 'Volatility / fear', 1.8]] },
];

export function computeConfluenceCandidate(input = {}) {
  const scores = input.scores && typeof input.scores === 'object' ? input.scores : {};
  const errors = [];
  let coveredMetrics = 0;
  const metricCount = confluenceCategories.reduce((sum, category) => sum + category.metrics.length, 0);
  const categories = confluenceCategories.map(category => {
    let covered = 0;
    let weightedScore = 0;
    let availableWeight = 0;
    for (const [key, , weight] of category.metrics) {
      const raw = scores[key];
      if (raw === null || raw === undefined || String(raw).trim() === '') continue;
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0 || value > 100) {
        errors.push(`${key} must be a finite score from 0 to 100.`);
        continue;
      }
      covered += 1;
      coveredMetrics += 1;
      weightedScore += value * weight;
      availableWeight += weight;
    }
    const coverage = covered / category.metrics.length;
    const score = coverage < 0.6 || availableWeight === 0 ? null : weightedScore / availableWeight;
    const status = score === null ? 'no-data' : score >= 60 - 1e-9 ? 'confirming' : score < 45 - 1e-9 ? 'conflicting' : 'neutral';
    return { ...category, covered, designed: category.metrics.length, coverage, score, status };
  });

  const confidenceRaw = input.dataConfidence;
  let dataConfidence = null;
  if (confidenceRaw !== null && confidenceRaw !== undefined && String(confidenceRaw).trim() !== '') {
    dataConfidence = Number(confidenceRaw);
    if (!Number.isFinite(dataConfidence) || dataConfidence < 0 || dataConfidence > 100) errors.push('Data confidence must be a finite score from 0 to 100.');
  }
  const indexRaw = input.realIndexCount;
  let realIndexCount = null;
  if (indexRaw !== null && indexRaw !== undefined && String(indexRaw).trim() !== '') {
    realIndexCount = Number(indexRaw);
    if (!Number.isInteger(realIndexCount) || realIndexCount < 0) errors.push('Real index count must be a non-negative whole number.');
  }

  const measuredCategories = categories.filter(category => category.score !== null);
  const categoryWeightCovered = measuredCategories.reduce((sum, category) => sum + category.weight, 0);
  const score = categoryWeightCovered
    ? measuredCategories.reduce((sum, category) => sum + category.score * category.weight, 0) / categoryWeightCovered
    : null;
  const confirming = categories.filter(category => category.status === 'confirming').length;
  const grades = [[71, 'Exceptional'], [65, 'Strong'], [52, 'Positive'], [39, 'Mixed'], [30, 'Weak (High Risk)'], [0, 'Very Weak (Severe Risk)']];
  let grade = score === null ? null : (grades.find(([minimum]) => score >= minimum)?.[1] || 'Very Weak (Severe Risk)');
  if (grade && ((realIndexCount !== null && realIndexCount < 4) || (dataConfidence !== null && dataConfidence < 70))) {
    const gradeFloor = grades.findIndex(([, label]) => label === 'Mixed');
    const gradeIndex = grades.findIndex(([, label]) => label === grade);
    if (gradeIndex >= 0 && gradeIndex < gradeFloor) grade = 'Mixed';
  }

  const blockers = [];
  if (input.qualified !== true) blockers.push('Eligibility is not marked as met.');
  if (confirming < 5) blockers.push(`Only ${confirming} categories confirm; 5 are required.`);
  if (score === null || Math.round(score) < 65) blockers.push('The weighted score is below 65 or unavailable.');
  if (dataConfidence !== null && dataConfidence < 70) blockers.push('Data confidence is below 70.');
  const status = errors.length ? 'invalid-input' : score === null ? 'insufficient-data' : blockers.length ? 'not-qualified' : 'qualified';
  return { categories, coveredMetrics, metricCount, submetricCoverage: metricCount ? coveredMetrics / metricCount : 0, categoryWeightCovered, score, confirming, grade, dataConfidence, realIndexCount, blockers, errors, status };
}

export function computeConfluenceEffectiveCandidate(input = {}) {
  const scores = input.effectiveScores && typeof input.effectiveScores === 'object' ? input.effectiveScores : {};
  const errors = [];
  let coveredMetrics = 0;
  const metricCount = confluenceEffectiveCategories.filter(category => !category.externalFramework).reduce((sum, category) => sum + category.leaves.length, 0);
  const categories = confluenceEffectiveCategories.map(category => {
    if (category.externalFramework) {
      return { ...category, covered: 0, designed: category.leaves.length, coverage: 0, score: null, status: 'no-data' };
    }
    let covered = 0;
    let weightedScore = 0;
    let availableWeight = 0;
    for (const [key, , weight] of category.leaves) {
      const raw = scores[key];
      if (raw === null || raw === undefined || String(raw).trim() === '') continue;
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0 || value > 100) {
        errors.push(`${key} must be a finite score from 0 to 100.`);
        continue;
      }
      covered += 1;
      coveredMetrics += 1;
      weightedScore += value * weight;
      availableWeight += weight;
    }
    const coverage = covered / category.leaves.length;
    const score = coverage < 0.6 || availableWeight === 0 ? null : weightedScore / availableWeight;
    const status = score === null ? 'no-data' : score >= 60 - 1e-9 ? 'confirming' : score < 45 - 1e-9 ? 'conflicting' : 'neutral';
    return { ...category, covered, designed: category.leaves.length, coverage, score, status };
  });

  const confidenceRaw = input.dataConfidence;
  let dataConfidence = null;
  if (confidenceRaw !== null && confidenceRaw !== undefined && String(confidenceRaw).trim() !== '') {
    dataConfidence = Number(confidenceRaw);
    if (!Number.isFinite(dataConfidence) || dataConfidence < 0 || dataConfidence > 100) errors.push('Data confidence must be a finite score from 0 to 100.');
  }
  const indexRaw = input.realIndexCount;
  let realIndexCount = null;
  if (indexRaw !== null && indexRaw !== undefined && String(indexRaw).trim() !== '') {
    realIndexCount = Number(indexRaw);
    if (!Number.isInteger(realIndexCount) || realIndexCount < 0) errors.push('Real index count must be a non-negative whole number.');
  }

  const measuredCategories = categories.filter(category => category.score !== null);
  const categoryWeightCovered = measuredCategories.reduce((sum, category) => sum + category.weight, 0);
  const score = categoryWeightCovered
    ? measuredCategories.reduce((sum, category) => sum + category.score * category.weight, 0) / categoryWeightCovered
    : null;
  const confirming = categories.filter(category => category.status === 'confirming').length;
  const grades = [[71, 'Exceptional'], [65, 'Strong'], [52, 'Positive'], [39, 'Mixed'], [30, 'Weak (High Risk)'], [0, 'Very Weak (Severe Risk)']];
  let grade = score === null ? null : (grades.find(([minimum]) => score >= minimum)?.[1] || 'Very Weak (Severe Risk)');
  if (grade && ((realIndexCount !== null && realIndexCount < 4) || (dataConfidence !== null && dataConfidence < 70))) {
    const gradeFloor = grades.findIndex(([, label]) => label === 'Mixed');
    const gradeIndex = grades.findIndex(([, label]) => label === grade);
    if (gradeIndex >= 0 && gradeIndex < gradeFloor) grade = 'Mixed';
  }

  const blockers = [];
  if (input.qualified !== true) blockers.push('Eligibility is not marked as met.');
  if (confirming < 5) blockers.push(`Only ${confirming} categories confirm; 5 are required.`);
  if (score === null || Math.round(score) < 65) blockers.push('The weighted score is below 65 or unavailable.');
  if (dataConfidence !== null && dataConfidence < 70) blockers.push('Data confidence is below 70.');
  const status = errors.length ? 'invalid-input' : score === null ? 'insufficient-data' : blockers.length ? 'not-qualified' : 'qualified';
  return { categories, coveredMetrics, metricCount, submetricCoverage: metricCount ? coveredMetrics / metricCount : 0, categoryWeightCovered, score, confirming, grade, dataConfidence, realIndexCount, blockers, errors, status };
}
