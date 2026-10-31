import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createHash } from 'node:crypto';
import {validateXmlWellFormedness} from '../research/forecast-features/xml-well-formedness-preflight-v1.mjs';
import * as features from '../research/forecast-features/fe27-30-public-v1.mjs';

const sha = value => createHash('sha256').update(value).digest('hex');
function zipStored(entries) {
  const locals = [], centrals = []; let offset = 0;
  for (const [name, value] of Object.entries(entries)) {
    const nameBytes = Buffer.from(name), data = Buffer.from(value), crc = crc32(data);
    const local = Buffer.alloc(30); local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4); local.writeUInt16LE(0, 6); local.writeUInt16LE(0, 8);
    local.writeUInt32LE(crc, 14); local.writeUInt32LE(data.length, 18); local.writeUInt32LE(data.length, 22); local.writeUInt16LE(nameBytes.length, 26); local.writeUInt16LE(0, 28);
    locals.push(local, nameBytes, data);
    const central = Buffer.alloc(46); central.writeUInt32LE(0x02014b50, 0); central.writeUInt16LE(20, 4); central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0, 8); central.writeUInt16LE(0, 10); central.writeUInt32LE(crc, 16); central.writeUInt32LE(data.length, 20); central.writeUInt32LE(data.length, 24);
    central.writeUInt16LE(nameBytes.length, 28); central.writeUInt16LE(0, 30); central.writeUInt16LE(0, 32); central.writeUInt16LE(0, 34); central.writeUInt16LE(0, 36);
    central.writeUInt32LE(0, 38); central.writeUInt32LE(offset, 42); centrals.push(central, nameBytes);
    offset += local.length + nameBytes.length + data.length;
  }
  const centralBytes = Buffer.concat(centrals), eocd = Buffer.alloc(22); eocd.writeUInt32LE(0x06054b50, 0); eocd.writeUInt16LE(Object.keys(entries).length, 8);
  eocd.writeUInt16LE(Object.keys(entries).length, 10); eocd.writeUInt32LE(centralBytes.length, 12); eocd.writeUInt32LE(offset, 16); eocd.writeUInt16LE(0, 20);
  return Buffer.concat([...locals, centralBytes, eocd]);
}
function crc32(bytes) { let crc = 0xffffffff; for (const byte of bytes) { crc ^= byte; for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0); } return (crc ^ 0xffffffff) >>> 0; }
function quarterRange(startYear, startQ, count) {
  let y = startYear, q = startQ, rows = [];
  for (let i = 0; i < count; i++) { rows.push(`${y}-Q${q}`); if (++q === 5) { q = 1; y++; } }
  return rows;
}
function beaWorkbook({ validUnits = true, count = 43, startYear = 2016, startQuarter = 1, fakeComment = false, coordinateSpoof = false } = {}) {
  const quarters = quarterRange(startYear, startQuarter, count), shared = ['Table 1.1.5. Gross Domestic Product', `[Millions of dollars] ${validUnits ? 'Seasonally adjusted at annual rates' : 'Not seasonally adjusted'}`, `Quarterly data from ${quarters[0]} to ${quarters.at(-1)}`, 'Bureau of Economic Analysis', 'Data published October 29, 2026', 'Line', 'Gross domestic product', 'A191RC', ...quarters];
  const sharedXml = `<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="${shared.length}" uniqueCount="${shared.length}">${shared.map(text => `<si><t>${text}</t></si>`).join('')}</sst>`;
  const rows = [];
  rows.push('<row r="1"><c r="A1" t="s"><v>0</v></c></row>');
  rows.push('<row r="2"><c r="A2" t="s"><v>1</v></c></row>');
  rows.push('<row r="3"><c r="A3" t="s"><v>2</v></c></row>');
  rows.push('<row r="4"><c r="A4" t="s"><v>3</v></c></row>');
  rows.push('<row r="5"><c r="A5" t="s"><v>4</v></c></row>');
  const header = quarters.map((q, i) => `<c r="${colName(i + 4)}8" t="s"><v>${8 + i}</v></c>`).join('');
  rows.push(`<row r="8"><c r="A8" t="s"><v>5</v></c>${header}</row>`);
  const values = quarters.map((_, i) => `<c r="${colName(i + 4)}9"><v>${(18000000 + i * 175000 + Math.sin(i * .3) * 18000).toFixed(3)}</v></c>`).join('');
  rows.push(`<row r="9"><c r="A9"><v>1</v></c><c r="B9" t="s"><v>6</v></c><c r="C9" t="s"><v>7</v></c>${values}${coordinateSpoof ? '<c r="A10"><v>0</v></c>' : ''}</row>`);
  const spoof = fakeComment ? '<!-- <row r="10"><c r="A10"><v>0</v></c></row> -->' : '';
  const sheet = `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${rows.join('')}</sheetData>${spoof}</worksheet>`;
  return zipStored({
    'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="T10105-Q" sheetId="11" r:id="rId11"/></sheets></workbook>',
    'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId11" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
    'xl/sharedStrings.xml': sharedXml,
    'xl/worksheets/sheet1.xml': sheet,
  });
}
function colName(n) { let s = ''; while (n) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; }
function treasuryXml(rows, { fakeComment = false } = {}) { const fake = fakeComment ? '<!-- <entry><content><m:properties><d:NEW_DATE>2025-12-31T00:00:00</d:NEW_DATE><d:BC_2YEAR>0</d:BC_2YEAR><d:BC_10YEAR>99</d:BC_10YEAR></m:properties></content></entry> -->' : ''; return `<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"><title type="text">DailyTreasuryYieldCurveRateData</title>${fake}${rows.map(({ date, i }) => `<entry><content type="application/xml"><m:properties><d:NEW_DATE m:type="Edm.DateTime">${date}T00:00:00</d:NEW_DATE><d:BC_2YEAR m:type="Edm.Double">${4.1 + Math.sin(i * .19) * .3}</d:BC_2YEAR><d:BC_10YEAR m:type="Edm.Double">${4.35 + Math.cos(i * .13) * .4}</d:BC_10YEAR></m:properties></content></entry>`).join('')}</feed>`; }
function treasuryRows(dropDate = null) {
  const perYear = new Map([[2024, []], [2025, []], [2026, []]]);
  let index = 0;
  for (let [year, endDate] of [[2024, '2024-12-31'], [2025, '2025-12-31'], [2026, '2026-10-30']]) {
    let date = Date.parse(`${year}-01-01T00:00:00Z`), end = Date.parse(`${endDate}T00:00:00Z`), rows = [];
    while (date <= end) {
      const day = new Date(date).getUTCDay(), isoDate = new Date(date).toISOString().slice(0, 10);
      if (day !== 0 && day !== 6) { if (isoDate !== dropDate) rows.push({ date: isoDate, i: index++ }); else index++; }
      date += 86400000;
    }
    perYear.set(year, rows);
  }
  return perYear;
}
function bisXml({ country = 'US', fakeComment = false, foreignNamespaceObs = false, startYear = 2016, startQuarter = 1, count = 43 } = {}) {
  const quarters = quarterRange(startYear, startQuarter, count);
  const fake = fakeComment ? '<!-- <Obs TIME_PERIOD="2026-Q3" OBS_VALUE="999999"/> -->' : '';
  const foreign = foreignNamespaceObs ? '<evil:Obs TIME_PERIOD="2026-Q3" OBS_VALUE="999999"/>' : '';
  return `<?xml version="1.0" encoding="UTF-8"?><message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common" xmlns:ss="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/structurespecific" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns1="urn:sdmx" xmlns:evil="urn:untrusted:spoof"><message:Header><message:Structure><common:StructureUsage><Ref agencyID="BIS" id="WS_TC" version="2.0"/></common:StructureUsage></message:Structure></message:Header><message:DataSet COLLECTION="E" ss:dataScope="DataStructure" xsi:type="ns1:DataSetType" ss:structureRef="BIS_WS_TC_2_0"><Group xsi:type="ns1:Sibling" BORROWERS_CTY="${country}" TC_BORROWERS="P" TC_LENDERS="A" VALUATION="M" UNIT_TYPE="XDC" TC_ADJUST="A" DECIMALS="3"/><Series FREQ="Q" BORROWERS_CTY="${country}" TC_BORROWERS="P" TC_LENDERS="A" VALUATION="M" UNIT_TYPE="XDC" TC_ADJUST="A" UNIT_MULT="9" UNIT_MEASURE="USD" TITLE_TS="United States - Credit to Private non-financial sector from All sectors at Market value - domestic currency">${fake}${foreign}${quarters.map((q, i) => `<Obs TIME_PERIOD="${q}" OBS_VALUE="${(21000 + i * 270 + Math.sin(i * .3) * 44).toFixed(3)}" OBS_STATUS="A" OBS_CONF="F"/>`).join('')}</Series></message:DataSet></message:StructureSpecificData>`;
}
function harness({ country = 'US', beaUnits = true, dropTreasuryDate = null, beaReleaseDate = 'October 29, 2026', fakeTreasuryComment = false, fakeBisComment = false, foreignNamespaceObs = false, fakeBeaComment = false, beaCoordinateSpoof = false, beaRows = 43, fakeReleaseComment = false } = {}) {
  const treasury = treasuryRows(dropTreasuryDate), xlsx = beaWorkbook({ validUnits: beaUnits, count: beaRows, fakeComment: fakeBeaComment, coordinateSpoof: beaCoordinateSpoof }), calls = [];
  const fakeFetch = async (url, init = {}) => {
    const parsed = new URL(url); calls.push({ url: parsed.toString(), init });
    if (parsed.hostname === 'home.treasury.gov') {
      const year = Number(parsed.searchParams.get('field_tdr_date_value'));
      return new Response(treasuryXml(treasury.get(year) || [], { fakeComment: fakeTreasuryComment }), { status: 200, headers: { 'content-type': 'application/xml' } });
    }
    if (parsed.hostname === 'stats.bis.org') return new Response(bisXml({ country, fakeComment: fakeBisComment, foreignNamespaceObs }), { status: 200, headers: { 'content-type': 'application/xml' } });
    if (parsed.hostname === 'data.bis.org') return new Response(`<html><h1>Credit to the non-financial sector</h1>${fakeReleaseComment ? '<!-- Last release date 1 January 1900 Next release date 2 January 1900 -->' : ''}<h2>Next release date</h2><p>7 December 2026</p><h2>Last release date</h2><p>14 September 2026</p></html>`, { status: 200, headers: { 'content-type': 'text/html; charset=utf-8' } });
    if (parsed.hostname === 'apps.bea.gov') return new Response(xlsx, { status: 200, headers: { 'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'last-modified': 'Sat, 31 Oct 2026 12:00:00 GMT', etag: '"synthetic-fixture"' } });
    if (parsed.hostname === 'www.bea.gov') return new Response(`<html><h1>Gross Domestic Product</h1>${fakeReleaseComment ? '<!-- GDP (Advance Estimate), 1st Quarter 1990 Current release: January 1, 1990 -->' : ''}<p>GDP (Advance Estimate), 3rd Quarter 2026</p><p>Current release: ${beaReleaseDate}</p></html>`, { status: 200, headers: { 'content-type': 'text/html; charset=utf-8' } });
    throw new Error('unexpected_host');
  };
  const context = vm.createContext({
    SHIPYARD_FORECAST_FE2730_FEATURES: features, shipyardValidateXmlWellFormedness: validateXmlWellFormedness, fetch: fakeFetch, crypto: globalThis.crypto,
    TextEncoder, TextDecoder, Uint8Array, DataView, Map, Set, Date, Number, String, Error, Object, Array, RegExp, Math,
    URL, Response, Blob, DecompressionStream, AbortSignal, Promise, JSON,
    json: (value, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } }),
    readBoundedBody: async (response, limit = 1024 * 1024) => {
      const bytes = new Uint8Array(await response.arrayBuffer()); if (bytes.byteLength > limit) throw new Error('response too large');
      return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    },
  });
  vm.runInContext(readFileSync(new URL('../worker/forecast-fe28.js', import.meta.url), 'utf8'), context);
  return { context, calls, request: { signal: new AbortController().signal } };
}

test('FE28 public adapter acquires only fixed public sources and produces bounded partial features without invoking scorer', async () => {
  const h = harness(), response = await h.context.shipyardForecastMacroFeatures(h.request, {}), out = await response.json();
  assert.equal(response.status, 200);
  assert.equal(out.status, 'partial_diagnostic');
  assert.equal(out.diagnostic_only, true);
  assert.equal(out.scorer_invoked, false);
  assert.deepEqual(out.features, {});
  assert.deepEqual(Object.keys(out.diagnostic_features).sort(), ['credit_impulse_z', 'curve_change_z', 'curve_slope_z', 'macro_transition_score'].sort());
  assert.deepEqual(out.missing_features, ['curve_slope_z', 'curve_change_z', 'credit_impulse_z', 'macro_transition_score']);
  assert.ok(out.diagnostic_features.macro_transition_score >= 0 && out.diagnostic_features.macro_transition_score <= 1);
  const stressIndex = (-out.diagnostic_features.curve_slope_z + out.diagnostic_features.curve_change_z - out.diagnostic_features.credit_impulse_z) / 3;
  assert.equal(out.transition_risk_measurement.stress_index, stressIndex);
  assert.equal(out.transition_risk_measurement.stress_index_unit, 'dimensionless_linear_composite_of_standardized_z_scores');
  assert.equal(out.transition_risk_measurement.score_feature, 'macro_transition_score');
  assert.equal(out.transition_risk_measurement.score_unit, 'bounded_heuristic_index_0_1');
  assert.equal(out.diagnostic_features.macro_transition_score, 0.5 + 0.5 * Math.tanh(stressIndex), 'unit-label correction leaves numeric transform unchanged');
  assert.match(out.feature_policy.transition_risk.output, /bounded heuristic index/);
  assert.equal(out.restrictions.decision_eligible, false);
  assert.equal(out.acquisition.requests_made, 7);
  assert.equal(h.calls.length, 7);
  assert.ok(h.calls.every(call => call.init.method === 'GET' && call.init.credentials === 'omit' && call.init.cache === 'no-store'
    && call.init.redirect === 'manual' && !('authorization' in call.init.headers)));
  assert.ok(h.calls.every(call => ['home.treasury.gov', 'stats.bis.org', 'data.bis.org', 'apps.bea.gov', 'www.bea.gov'].includes(new URL(call.url).hostname)));
  assert.equal(out.bis_credit_capture.source_id, 'BIS:WS_TC:Q.US.P.A.M.XDC.A');
  assert.equal(out.bis_credit_capture.identity.borrower_country, 'US');
  assert.equal(out.bis_credit_capture.row_summary.count, 43);
  assert.equal(out.bis_credit_capture.row_summary.latest_quarter, '2026-Q3');
  assert.equal(out.bis_credit_capture.rows, undefined);
  assert.equal(out.credit_source.quarter_clock_audit.at(-1).credit_publication_at, null);
  assert.equal(out.credit_source.quarter_clock_audit.at(-1).gdp_publication_at, null);
  assert.equal(out.credit_source.quarter_clock_audit.at(-1).credit_revision_at, null);
  assert.equal(out.credit_source.quarter_clock_audit.at(-1).credit_available_at, null);
  assert.equal(out.credit_source.source_age_seconds, null);
  assert.match(out.credit_source.source_age_status, /unknown/);
  assert.equal(out.treasury.source.available_at, null);
  assert.equal(out.treasury.source.publication_at, null);
  assert.ok(out.treasury.source.observed_date_age_upper_bound_seconds >= 0);
  assert.equal(out.treasury.freshness.gate_status, 'closed_for_scorer_input_until_independent_calendar_and_availability_validation');
  assert.equal(out.bea_gdp_capture.source_vintage_status, undefined);
  assert.equal(out.bea_gdp_capture.row_summary.vintage_status, 'current_revised_NIPA_snapshot; quarterly publication/revision clocks not provided by workbook');
  assert.equal(out.bea_gdp_capture.row_summary.count, 43);
  assert.equal(out.bea_gdp_capture.row_summary.latest_quarter, '2026-Q3');
  assert.equal(out.bea_gdp_capture.rows, undefined);
  assert.equal(out.bea_gdp_capture.workbook_metadata.worksheet, 'T10105-Q');
  assert.equal(out.bea_gdp_capture.workbook_metadata.raw_unit, 'millions_of_US_dollars_SAAR');
  assert.equal(out.bea_gdp_capture.workbook_metadata.normalized_unit, 'billions_of_US_dollars_SAAR');
  assert.equal(out.bea_gdp_capture.workbook_metadata.data_published_date, '2026-10-29');
  assert.equal(out.bea_gdp_capture.row_summary.latest_gdp_saar, 25350.605215);
  assert.equal(out.bis_release_metadata.last_release_date, '2026-09-14');
  assert.equal(out.bis_release_metadata.next_release_date, '2026-12-07');
  assert.ok(out.bis_release_metadata.release_date_age_upper_bound_seconds > 0);
  assert.equal(out.bea_release_metadata.current_release_date, '2026-10-29');
  assert.equal(out.bea_release_metadata.latest_gdp_release_quarter, '2026-Q3');
  assert.equal(out.bea_release_metadata.workbook_latest_quarter, '2026-Q3');
  assert.equal(out.bea_release_metadata.workbook_quarter_matches_release, true);
  assert.equal(out.bea_release_metadata.workbook_publication_date_matches_page, true);
  assert.ok(out.credit_source.dataset_release_age_upper_bound_seconds > 0);
  assert.equal(out.credit_source.dataset_release_date_bounds.bis_release_page_capture_is_not_atomic_with_data_snapshot, true);
  assert.equal(out.credit_source.dataset_release_date_bounds.bea_workbook_sha256, out.bea_gdp_capture.source_sha256);
  assert.equal(out.acquisition.persistent_write, false);
  assert.equal(out.acquisition.provider_credentials_used, false);
  assert.ok(out.blockers.some(item => /not the lost original feature builder/.test(item)));
  assert.ok(out.blockers.some(item => /Treasury session calendar completeness is unverified/.test(item)));
  assert.ok(!('calculator_result' in out));
});

test('FE28 unchanged Treasury payload refetch never resets observation age to receipt time', async () => {
  const h = harness();
  const first = await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json();
  await new Promise(resolve => setTimeout(resolve, 25));
  const second = await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json();
  assert.notEqual(first.treasury.source.received_at, second.treasury.source.received_at);
  assert.ok(first.treasury.source.observed_date_age_upper_bound_seconds > 86400);
  assert.ok(second.treasury.source.observed_date_age_upper_bound_seconds > 86400);
  assert.ok(second.treasury.source.observed_date_age_upper_bound_seconds
    > (Date.now() - Date.parse(second.treasury.source.received_at)) / 1000 + 86400);
  assert.deepEqual(first.diagnostic_features, second.diagnostic_features);
  assert.deepEqual(first.features, {});
  assert.deepEqual(second.features, {});
  assert.equal(first.treasury.source.available_at, null);
  assert.equal(second.treasury.source.available_at, null);
});

test('FE28 dropped Treasury history row changes only a diagnostic and cannot self-certify coverage', async () => {
  const baselineHarness = harness();
  const baseline = await (await baselineHarness.context.shipyardForecastMacroFeatures(baselineHarness.request, {})).json();
  const droppedHarness = harness({ dropTreasuryDate: '2025-12-01' });
  const dropped = await (await droppedHarness.context.shipyardForecastMacroFeatures(droppedHarness.request, {})).json();
  assert.equal(dropped.treasury.source.calendar_completeness, 'unverified: no independent Treasury publishing-session calendar was supplied');
  assert.notEqual(dropped.diagnostic_features.curve_slope_z, baseline.diagnostic_features.curve_slope_z);
  assert.deepEqual(dropped.features, {});
  assert.deepEqual(dropped.missing_features, ['curve_slope_z', 'curve_change_z', 'credit_impulse_z', 'macro_transition_score']);
  assert.equal(dropped.restrictions.decision_eligible, false);
  assert.ok(dropped.blockers.some(item => /calendar completeness is unverified/.test(item)));
});

test('FE28 adapter rejects the BIS aggregate-country key even if dates and values otherwise line up', async () => {
  const h = harness({ country: '5R' }), response = await h.context.shipyardForecastMacroFeatures(h.request, {}), out = await response.json();
  assert.equal(out.features.credit_impulse_z, undefined);
  assert.ok(out.missing_features.includes('credit_impulse_z'));
  assert.ok(out.blockers.some(item => /bis_series_dimension_mismatch/.test(item)));
  assert.equal(out.bis_credit_capture, undefined);
  assert.equal(out.features.credit_impulse_z, undefined);
});

test('FE28 adapter fails closed on an undocumented BEA units change and never calls scoring', async () => {
  const h = harness({ beaUnits: false }), response = await h.context.shipyardForecastMacroFeatures(h.request, {}), out = await response.json();
  assert.equal(out.features.credit_impulse_z, undefined);
  assert.ok(out.blockers.some(item => /bea_gdp_units_unverified/.test(item)));
  assert.ok(out.missing_features.includes('credit_impulse_z'));
  assert.equal(out.scorer_invoked, false);
});

test('FE28 BEA publication date is read from the hashed workbook rather than receipt or a disagreeing page', async () => {
  const h = harness({ beaReleaseDate: 'October 30, 2026' });
  const out = await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json();
  assert.equal(out.bea_gdp_capture.workbook_metadata.data_published_date, '2026-10-29');
  assert.equal(out.bea_gdp_capture.workbook_metadata.source_file_sha256, out.bea_gdp_capture.source_sha256);
  assert.equal(out.bea_release_metadata.current_release_date, '2026-10-30');
  assert.equal(out.bea_release_metadata.workbook_publication_date_matches_page, false);
  assert.equal(out.credit_source.dataset_release_date_bounds.bea_workbook_publication_date, '2026-10-29');
  assert.equal(out.credit_source.dataset_release_date_bounds.bea_workbook_sha256, out.bea_gdp_capture.source_sha256);
  assert.deepEqual(out.features, {});
});

test('FE28 strict XML rejects comment-tag spoofing, foreign namespaces and workbook coordinate mismatch', async () => {
  const treasury = await (async () => { const h = harness({ fakeTreasuryComment: true }); return await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json(); })();
  assert.equal(treasury.treasury, undefined);
  assert.equal(treasury.diagnostic_features.curve_slope_z, undefined);
  assert.ok(treasury.blockers.some(item => /treasury:public_xml_comment_unsupported/.test(item)));

  const bis = await (async () => { const h = harness({ fakeBisComment: true }); return await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json(); })();
  assert.equal(bis.bis_credit_capture, undefined);
  assert.equal(bis.diagnostic_features.credit_impulse_z, undefined);
  assert.ok(bis.blockers.some(item => /bis:public_xml_comment_unsupported/.test(item)));

  const namespace = await (async () => { const h = harness({ foreignNamespaceObs: true }); return await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json(); })();
  assert.equal(namespace.bis_credit_capture, undefined);
  assert.ok(namespace.blockers.some(item => /bis:bis_observation_structure_invalid/.test(item)));

  const beaComment = await (async () => { const h = harness({ fakeBeaComment: true }); return await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json(); })();
  assert.equal(beaComment.bea_gdp_capture, undefined);
  assert.ok(beaComment.blockers.some(item => /bea:public_xml_comment_unsupported/.test(item)));

  const coordinate = await (async () => { const h = harness({ beaCoordinateSpoof: true }); return await (await h.context.shipyardForecastMacroFeatures(h.request, {})).json(); })();
  assert.equal(coordinate.bea_gdp_capture, undefined);
  assert.ok(coordinate.blockers.some(item => /bea:bea_xlsx_cell_coordinate_invalid/.test(item)));
  for (const out of [treasury, bis, namespace, beaComment, coordinate]) {
    assert.deepEqual(out.features, {});
    assert.equal(out.scorer_invoked, false);
    assert.equal(out.restrictions.decision_eligible, false);
  }
});

test('FE28 HTML release metadata strips comments before extracting dates', async () => {
  const h=harness({fakeReleaseComment:true});
  const out=await (await h.context.shipyardForecastMacroFeatures(h.request,{})).json();
  assert.equal(out.bis_release_metadata.last_release_date,'2026-09-14');
  assert.equal(out.bis_release_metadata.next_release_date,'2026-12-07');
  assert.equal(out.bea_release_metadata.current_release_date,'2026-10-29');
  assert.equal(out.bea_release_metadata.latest_gdp_release_quarter,'2026-Q3');
  assert.equal(out.scorer_invoked,false);
});
