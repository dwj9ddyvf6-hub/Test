// FE28's fixed public-source acquisition path. This is read-only and has no
// credentials. It never invokes the pinned FE28 scorer; unresolved source
// fields remain missing. Large XLSX handling is a strict bounded subset.
const SHIPYARD_FE28_POLICY = Object.freeze({
  id: 'FE28_TREASURY_BIS_BEA_PUBLIC_CAPTURE_V1', version: 1,
  treasury_years: 3, treasury_observations: 254,
  bis_flow: 'WS_TC', bis_version: '2.0', bis_key: 'Q.US.P.A.M.XDC.A',
  bis_dimensions: { frequency: 'Q', borrower_country: 'US', borrower_sector: 'P', lender_sector: 'A', valuation: 'M', unit_type: 'XDC', adjustment: 'A', unit_multiplier: '9', unit_measure: 'USD' },
  bea_url: 'https://apps.bea.gov/national/Release/XLS/Survey/Section1All_xls.xlsx',
  acquisition_request_bound: 7, source_timeout_ms: 8000,
  bis_release_max_age_seconds: 7776000, gdp_release_max_age_seconds: 7776000,
  max_treasury_bytes_per_year: 524288, max_bis_bytes: 524288,
  max_bea_compressed_bytes: 8388608, max_bea_uncompressed_bytes: 33554432,
});
function shipyardFE28Fail(code) { throw Error(code); }
function shipyardFE28Hex(bytes) { return [...bytes].map(x => x.toString(16).padStart(2, '0')).join(''); }
async function shipyardFE28Hash(bytes) { return shipyardFE28Hex(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))); }
function shipyardFE28ValidDate(value) { return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value + 'T00:00:00Z')) && new Date(value + 'T00:00:00Z').toISOString().slice(0, 10) === value; }
function shipyardFE28Year(value) { const n = Number(value); if (!Number.isInteger(n) || n < 1900 || n > 2200) shipyardFE28Fail('invalid_source_year'); return n; }
function shipyardFE28TextBytes(text, limit) { const bytes = new TextEncoder().encode(text); if (bytes.byteLength > limit) shipyardFE28Fail('source_body_too_large'); return bytes; }
const SHIPYARD_FE28_XML_ATOM='http://www.w3.org/2005/Atom';
const SHIPYARD_FE28_XML_TREASURY_DATA='http://schemas.microsoft.com/ado/2007/08/dataservices';
const SHIPYARD_FE28_XML_TREASURY_META='http://schemas.microsoft.com/ado/2007/08/dataservices/metadata';
const SHIPYARD_FE28_XML_SDMX_MESSAGE='http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message';
const SHIPYARD_FE28_XML_SDMX_COMMON='http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common';
const SHIPYARD_FE28_XML_XSI='http://www.w3.org/2001/XMLSchema-instance';
const SHIPYARD_FE28_XML_SS='http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/structurespecific';
const SHIPYARD_FE28_XML_MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const SHIPYARD_FE28_XML_REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const SHIPYARD_FE28_XML_PACKAGE='http://schemas.openxmlformats.org/package/2006/relationships';
const SHIPYARD_FE28_XML_XML='http://www.w3.org/XML/1998/namespace';
function shipyardFE28XmlDecode(text) {
  let out='',pos=0;
  while(true){
    const amp=text.indexOf('&',pos);if(amp<0){out+=text.slice(pos);break;}
    out+=text.slice(pos,amp);const end=text.indexOf(';',amp+1);if(end<0||end-amp>16)shipyardFE28Fail('public_xml_entity_invalid');
    const entity=text.slice(amp+1,end);let value;
    if(entity==='amp')value='&';else if(entity==='lt')value='<';else if(entity==='gt')value='>';
    else if(entity==='quot')value='"';else if(entity==='apos')value="'";
    else if(/^#\d+$/.test(entity)||/^#x[\da-f]+$/i.test(entity)){
      const cp=entity[1]==='x'?parseInt(entity.slice(2),16):Number(entity.slice(1));
      if(!Number.isInteger(cp)||cp<=0||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||(cp<0x20&&![9,10,13].includes(cp)))shipyardFE28Fail('public_xml_entity_invalid');
      value=String.fromCodePoint(cp);
    }else shipyardFE28Fail('public_xml_entity_invalid');
    out+=value;pos=end+1;
  }
  for(const char of out){const cp=char.codePointAt(0);if(cp===0||(cp<0x20&&![9,10,13].includes(cp))||(cp>=0xd800&&cp<=0xdfff))shipyardFE28Fail('public_xml_character_invalid');}
  return out;
}
// Bounded strict namespace-aware XML subset: no comments/CDATA/PIs/DTD/entities
// beyond predefined/numeric references. Build a tree so tag-looking strings in
// comments or nested text can never become source rows.
function shipyardFE28ParseXml(text){
  if(typeof text!=='string'||text.length>SHIPYARD_FE28_POLICY_MAX_XML)shipyardFE28Fail('public_xml_size_invalid');
  try{shipyardValidateXmlWellFormedness(text,{maxBytes:1024*1024,maxDepth:80,maxNodes:60000});}
  catch(error){
    if(error?.code==='unsupported_xml_comment_or_cdata')shipyardFE28Fail('public_xml_comment_unsupported');
    if(error?.code==='unsupported_xml_processing_instruction'||error?.code==='unsafe_xml_declaration')shipyardFE28Fail('public_xml_active_content_unsupported');
    if(error?.code==='xml_preflight_byte_limit_exceeded')shipyardFE28Fail('public_xml_size_invalid');
    if(error?.code==='xml_preflight_depth_limit_exceeded')shipyardFE28Fail('public_xml_depth_invalid');
    if(error?.code==='xml_preflight_node_limit_exceeded')shipyardFE28Fail('public_xml_node_limit');
    shipyardFE28Fail('public_xml_malformed');
  }
  let xml=text.startsWith('\uFEFF')?text.slice(1):text;
  if(xml.includes('<!--')||xml.includes('-->'))shipyardFE28Fail('public_xml_comment_unsupported');
  if(/<!\s*(?:DOCTYPE|ENTITY|\[CDATA\b)/i.test(xml))shipyardFE28Fail('public_xml_active_content_unsupported');
  if(xml.includes(']]>'))shipyardFE28Fail('public_xml_cdata_terminator_unsupported');
  if(xml.startsWith('<?xml')){
    const declaration=/^<\?xml\s+version=(['"])1\.0\1(?:\s+encoding=(['"])UTF-8\2)?(?:\s+standalone=(['"])(?:yes|no)\3)?\s*\?>/i.exec(xml);
    if(!declaration)shipyardFE28Fail('public_xml_declaration_invalid');xml=xml.slice(declaration[0].length);
  }
  if(xml.includes('<?'))shipyardFE28Fail('public_xml_processing_instruction_unsupported');
  const rootChildren=[],stack=[];let i=0,nodes=0,rootClosed=false;
  const namePattern=/^[A-Za-z_][A-Za-z0-9_.-]*(?::[A-Za-z_][A-Za-z0-9_.-]*)?$/;
  const split=(name,namespaces,isAttribute=false)=>{
    if(!namePattern.test(name))shipyardFE28Fail('public_xml_name_invalid');
    const parts=name.split(':');if(parts.length===2){if(!namespaces.has(parts[0]))shipyardFE28Fail('public_xml_prefix_unbound');return {local:parts[1],uri:namespaces.get(parts[0])};}
    return {local:parts[0],uri:isAttribute?'':(namespaces.get('')||'')};
  };
  const tagEnd=start=>{let quote='';for(let j=start+1;j<xml.length;j++){const c=xml[j];if(quote){if(c===quote)quote='';}else if(c==='"'||c==="'")quote=c;else if(c==='>')return j;}shipyardFE28Fail('public_xml_tag_unclosed');};
  while(i<xml.length){
    if(xml[i]!=='<'){
      const end=xml.indexOf('<',i),stop=end<0?xml.length:end,value=shipyardFE28XmlDecode(xml.slice(i,stop));
      if(!stack.length){if(value.trim())shipyardFE28Fail('public_xml_text_outside_root');}
      else stack.at(-1).node.text+=value;
      i=stop;continue;
    }
    if(xml.startsWith('</',i)){
      const end=tagEnd(i),raw=xml.slice(i,end+1),match=/^<\/([A-Za-z_][A-Za-z0-9_.:-]*)\s*>$/.exec(raw);
      if(!match||!stack.length||stack.at(-1).node.qname!==match[1])shipyardFE28Fail('public_xml_unbalanced_tags');
      stack.pop();i=end+1;if(!stack.length)rootClosed=true;continue;
    }
    if(xml.startsWith('<!',i)||xml.startsWith('<?',i))shipyardFE28Fail('public_xml_active_content_unsupported');
    const end=tagEnd(i),raw=xml.slice(i,end+1),opening=/^<([A-Za-z_][A-Za-z0-9_.:-]*)([\s\S]*)>$/.exec(raw);
    if(!opening||rootClosed)shipyardFE28Fail('public_xml_malformed_tag');
    const qname=opening[1];let tail=opening[2],selfClosing=false;
    if(/\/\s*$/.test(tail)){selfClosing=true;tail=tail.replace(/\/\s*$/,'');}
    const rawAttrs=[];let p=0;
    while(p<tail.length){const ws=/^\s+/.exec(tail.slice(p));if(!ws)shipyardFE28Fail('public_xml_attribute_spacing');p+=ws[0].length;if(p>=tail.length)break;
      const match=/^[A-Za-z_][A-Za-z0-9_.:-]*/.exec(tail.slice(p));if(!match)shipyardFE28Fail('public_xml_attribute_name_invalid');const name=match[0];p+=name.length;
      while(p<tail.length&&/\s/.test(tail[p]))p++;if(tail[p++]!=='=')shipyardFE28Fail('public_xml_attribute_invalid');while(p<tail.length&&/\s/.test(tail[p]))p++;
      const quote=tail[p++];if(quote!=='"'&&quote!=="'")shipyardFE28Fail('public_xml_attribute_invalid');const start=p;
      while(p<tail.length&&tail[p]!==quote){if(tail[p]==='<')shipyardFE28Fail('public_xml_attribute_invalid');p++;}
      if(p>=tail.length)shipyardFE28Fail('public_xml_attribute_unclosed');const value=shipyardFE28XmlDecode(tail.slice(start,p));p++;
      if(rawAttrs.some(a=>a.name===name))shipyardFE28Fail('public_xml_duplicate_attribute');rawAttrs.push({name,value});
    }
    const namespaces=new Map(stack.length?stack.at(-1).namespaces:[['xml',SHIPYARD_FE28_XML_XML]]);
    for(const attr of rawAttrs){if(attr.name==='xmlns')namespaces.set('',attr.value);else if(attr.name.startsWith('xmlns:')){
      const prefix=attr.name.slice(6);if(!namePattern.test(prefix)||prefix.includes(':')||prefix==='xmlns'||!attr.value
        ||(prefix==='xml'&&attr.value!==SHIPYARD_FE28_XML_XML)||(prefix!=='xml'&&attr.value===SHIPYARD_FE28_XML_XML)
        ||attr.value==='http://www.w3.org/2000/xmlns/')shipyardFE28Fail('public_xml_namespace_invalid');namespaces.set(prefix,attr.value);}}
    const expanded=split(qname,namespaces),attrs=new Map();
    for(const attr of rawAttrs){if(attr.name==='xmlns'||attr.name.startsWith('xmlns:'))continue;const resolved=split(attr.name,namespaces,true),key=resolved.uri+'\u0000'+resolved.local;if(attrs.has(key))shipyardFE28Fail('public_xml_duplicate_expanded_attribute');attrs.set(key,attr.value);}
    if(rawAttrs.length>64)shipyardFE28Fail('public_xml_attribute_limit');
    const node={qname,local:expanded.local,uri:expanded.uri,attrs,children:[],text:''};if(++nodes>40000)shipyardFE28Fail('public_xml_node_limit');
    if(stack.length)stack.at(-1).node.children.push(node);else rootChildren.push(node);
    if(rootChildren.length>1)shipyardFE28Fail('public_xml_multiple_roots');
    if(!selfClosing){stack.push({node,namespaces});if(stack.length>64)shipyardFE28Fail('public_xml_depth_limit');}
    else if(!stack.length)rootClosed=true;
    i=end+1;
  }
  if(rootChildren.length!==1||stack.length||!rootClosed)shipyardFE28Fail('public_xml_unbalanced_document');
  return rootChildren[0];
}
const shipyardFE28XmlChildren=(node,local,uri)=>{
  const named=node?.children.filter(child=>child.local===local)||[];
  if(named.some(child=>child.uri!==uri))shipyardFE28Fail('public_xml_namespace_collision');
  return named;
};
function shipyardFE28XmlChild(node,local,uri,{required=false}={}){const found=shipyardFE28XmlChildren(node,local,uri);if(found.length>1)shipyardFE28Fail(`public_xml_duplicate_${local}`);if(!found.length){if(required)shipyardFE28Fail(`public_xml_missing_${local}`);return null;}return found[0];}
const shipyardFE28XmlAttr=(node,local,uri='')=>node?.attrs?.get(uri+'\u0000'+local)??null;
function shipyardFE28XmlScalar(node){if(!node||node.children.length)shipyardFE28Fail('public_xml_scalar_nested');return node.text.trim();}
function shipyardFE28XmlOnlyWhitespace(node){if(node.text.trim())shipyardFE28Fail('public_xml_unexpected_text');}
const SHIPYARD_FE28_POLICY_MAX_XML=1024*1024;
function shipyardFE28ParseTreasury(xml, year) {
  if (typeof xml !== 'string' || xml.length > SHIPYARD_FE28_POLICY.max_treasury_bytes_per_year) shipyardFE28Fail('treasury_xml_schema_unverified');
  const root=shipyardFE28ParseXml(xml);
  if(root.local!=='feed'||root.uri!==SHIPYARD_FE28_XML_ATOM)shipyardFE28Fail('treasury_xml_schema_unverified');
  const title=shipyardFE28XmlChild(root,'title',SHIPYARD_FE28_XML_ATOM,{required:true});
  if(shipyardFE28XmlScalar(title)!=='DailyTreasuryYieldCurveRateData')shipyardFE28Fail('treasury_xml_schema_unverified');
  const rows = [], seen = new Set();
  if(root.children.some(child=>child.uri!==SHIPYARD_FE28_XML_ATOM))shipyardFE28Fail('treasury_feed_child_namespace_invalid');
  for (const entry of shipyardFE28XmlChildren(root,'entry',SHIPYARD_FE28_XML_ATOM)) {
    const content=shipyardFE28XmlChild(entry,'content',SHIPYARD_FE28_XML_ATOM,{required:true});
    const properties=shipyardFE28XmlChild(content,'properties',SHIPYARD_FE28_XML_TREASURY_META,{required:true});
    shipyardFE28XmlOnlyWhitespace(entry);shipyardFE28XmlOnlyWhitespace(content);shipyardFE28XmlOnlyWhitespace(properties);
    const values=new Map();for(const child of properties.children){if(child.uri!==SHIPYARD_FE28_XML_TREASURY_DATA||values.has(child.local))shipyardFE28Fail('treasury_property_namespace_or_duplicate');values.set(child.local,shipyardFE28XmlScalar(child));}
    const dateRaw=values.get('NEW_DATE'),dateMatch=/^(\d{4}-\d{2}-\d{2})(?:T00:00:00(?:\.\d+)?(?:Z)?)?$/.exec(dateRaw||'');
    const date=dateMatch?.[1],two=values.get('BC_2YEAR'),ten=values.get('BC_10YEAR');
    if (!date || date.slice(0, 4) !== String(year) || !shipyardFE28ValidDate(date) || seen.has(date)) shipyardFE28Fail('treasury_observation_date_invalid_or_duplicate');
    if (!two || !ten || !/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(two) || !/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(ten)) shipyardFE28Fail('treasury_required_maturity_missing');
    seen.add(date); rows.push({ date, two_year_pct: Number(two), ten_year_pct: Number(ten) });
  }
  rows.sort((a, b) => a.date.localeCompare(b.date));
  if (!rows.length || rows.length > 300) shipyardFE28Fail('treasury_year_coverage_invalid');
  return rows;
}
function shipyardFE28AssertXmlAttributes(node, allowed) {
  const accepted=new Set([...allowed].map(key=>key.includes('\u0000')?key:'\u0000'+key));
  for(const key of node.attrs.keys())if(!accepted.has(key))shipyardFE28Fail('public_xml_unexpected_attribute');
}
function shipyardFE28ParseBISXml(xml) {
  if (typeof xml !== 'string' || xml.length > SHIPYARD_FE28_POLICY.max_bis_bytes) shipyardFE28Fail('bis_sdmx_xml_schema_unverified');
  const root=shipyardFE28ParseXml(xml);
  if(root.local!=='StructureSpecificData'||root.uri!==SHIPYARD_FE28_XML_SDMX_MESSAGE)shipyardFE28Fail('bis_sdmx_xml_schema_unverified');
  const header=shipyardFE28XmlChild(root,'Header',SHIPYARD_FE28_XML_SDMX_MESSAGE,{required:true});
  const structure=shipyardFE28XmlChild(header,'Structure',SHIPYARD_FE28_XML_SDMX_MESSAGE,{required:true});
  const usage=shipyardFE28XmlChild(structure,'StructureUsage',SHIPYARD_FE28_XML_SDMX_COMMON,{required:true});
  const ref=shipyardFE28XmlChild(usage,'Ref','',{required:true});
  if(shipyardFE28XmlAttr(ref,'agencyID')!=='BIS'||shipyardFE28XmlAttr(ref,'id')!=='WS_TC'||shipyardFE28XmlAttr(ref,'version')!=='2.0')shipyardFE28Fail('bis_dataflow_identity_unverified');
  const datasets=shipyardFE28XmlChildren(root,'DataSet',SHIPYARD_FE28_XML_SDMX_MESSAGE);
  if(datasets.length!==1)shipyardFE28Fail('bis_dataset_not_unique');
  const dataset=datasets[0],groups=shipyardFE28XmlChildren(dataset,'Group',''),series=shipyardFE28XmlChildren(dataset,'Series','');
  if(groups.length!==1||series.length!==1||dataset.children.length!==2)shipyardFE28Fail('bis_series_not_unique');
  const group=groups[0],seriesNode=series[0],xsi=SHIPYARD_FE28_XML_XSI,ss=SHIPYARD_FE28_XML_SS;
  shipyardFE28AssertXmlAttributes(dataset,new Set(['COLLECTION',ss+'\u0000dataScope',ss+'\u0000structureRef',xsi+'\u0000type']));
  shipyardFE28AssertXmlAttributes(group,new Set(['BORROWERS_CTY','TC_BORROWERS','TC_LENDERS','VALUATION','UNIT_TYPE','TC_ADJUST','DECIMALS',xsi+'\u0000type']));
  shipyardFE28AssertXmlAttributes(seriesNode,new Set(['FREQ','BORROWERS_CTY','TC_BORROWERS','TC_LENDERS','VALUATION','UNIT_TYPE','TC_ADJUST','UNIT_MULT','UNIT_MEASURE','TITLE_TS',xsi+'\u0000type']));
  const expectedGroup={BORROWERS_CTY:'US',TC_BORROWERS:'P',TC_LENDERS:'A',VALUATION:'M',UNIT_TYPE:'XDC',TC_ADJUST:'A'};
  const expectedSeries={FREQ:'Q',...expectedGroup,UNIT_MULT:'9',UNIT_MEASURE:'USD'};
  for(const [key,value]of Object.entries(expectedGroup))if(shipyardFE28XmlAttr(group,key)!==value)shipyardFE28Fail('bis_series_dimension_mismatch');
  for(const [key,value]of Object.entries(expectedSeries))if(shipyardFE28XmlAttr(seriesNode,key)!==value)shipyardFE28Fail('bis_series_dimension_mismatch');
  if(!/^United States - Credit to Private non-financial sector from All sectors at Market value - domestic currency/i.test(shipyardFE28XmlAttr(seriesNode,'TITLE_TS')||''))shipyardFE28Fail('bis_series_title_unverified');
  shipyardFE28XmlOnlyWhitespace(dataset);shipyardFE28XmlOnlyWhitespace(group);shipyardFE28XmlOnlyWhitespace(seriesNode);
  if(seriesNode.children.some(child=>child.local!=='Obs'||child.uri!==''))shipyardFE28Fail('bis_observation_structure_invalid');
  const observations=seriesNode.children.map(obs=>{
    shipyardFE28AssertXmlAttributes(obs,new Set(['TIME_PERIOD','OBS_VALUE','OBS_STATUS','OBS_CONF']));
    if(obs.children.length||obs.text.trim())shipyardFE28Fail('bis_observation_structure_invalid');
    const quarter=shipyardFE28XmlAttr(obs,'TIME_PERIOD'),value=shipyardFE28XmlAttr(obs,'OBS_VALUE');
    if(!/^\d{4}-Q[1-4]$/.test(quarter||'')||!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(value||''))shipyardFE28Fail('bis_observation_schema_unverified');
    return {quarter,credit_stock:Number(value)};
  }).sort((a,b)=>a.quarter.localeCompare(b.quarter));
  if (observations.length < 43 || observations.length > 200
      || observations.some((row, i) => i && (row.quarter === observations[i - 1].quarter
        || shipyardFE28QuarterIndex(row.quarter) !== shipyardFE28QuarterIndex(observations[i - 1].quarter) + 1))) shipyardFE28Fail('bis_credit_history_not_exact');
  return observations;
}
function shipyardFE28HtmlText(html) {
  if (typeof html !== 'string' || html.length > 524288) shipyardFE28Fail('release_metadata_html_invalid');
  const withoutComments=html.replace(/<!--[\s\S]*?-->/g,' ');
  if(withoutComments.includes('<!--')||withoutComments.includes('-->'))shipyardFE28Fail('release_metadata_html_comment_invalid');
  return shipyardFE28HtmlUnescape(withoutComments.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ').replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n))).replace(/\s+/g, ' ').trim());
}
function shipyardFE28HtmlUnescape(text) { return text.replace(/&quot;/gi, '"').replace(/&apos;/gi, "'").replace(/&gt;/gi, '>').replace(/&lt;/gi, '<').replace(/&amp;/gi, '&'); }
function shipyardFE28DateISO(text) {
  const t = String(text || '').trim();
  let day, monthName, year, match;
  if ((match = /^(\d{1,2}) ([A-Za-z]+) (\d{4})$/.exec(t))) [, day, monthName, year] = match;
  else if ((match = /^([A-Za-z]+) (\d{1,2}), (\d{4})$/.exec(t))) [, monthName, day, year] = match;
  else shipyardFE28Fail('release_metadata_date_unrecognized');
  const months = ['january','february','march','april','may','june','july','august','september','october','november','december'];
  const month = months.indexOf(monthName.toLowerCase());
  const d = new Date(Date.UTC(Number(year), month, Number(day)));
  if (month < 0 || !Number.isFinite(d.getTime()) || d.getUTCFullYear() !== Number(year)
      || d.getUTCMonth() !== month || d.getUTCDate() !== Number(day)) shipyardFE28Fail('release_metadata_date_invalid');
  return d.toISOString().slice(0, 10);
}
function shipyardFE28ParseBISReleaseMetadata(html) {
  const text = shipyardFE28HtmlText(html);
  if (!/Credit to the non-financial sector/i.test(text)) shipyardFE28Fail('bis_release_topic_title_unverified');
  const last = /Last release date\s+(\d{1,2} [A-Za-z]+ \d{4})/i.exec(text)?.[1];
  const next = /Next release date\s+(\d{1,2} [A-Za-z]+ \d{4})/i.exec(text)?.[1];
  const lastISO = shipyardFE28DateISO(last), nextISO = shipyardFE28DateISO(next);
  if (nextISO <= lastISO) shipyardFE28Fail('bis_release_dates_not_ordered');
  return { topic: 'TOTAL_CREDIT', last_release_date: lastISO, next_release_date: nextISO,
    publication_clock_precision: 'official date only; exact time and per-quarter revisions not supplied' };
}
function shipyardFE28ParseBEAReleaseMetadata(html) {
  const text = shipyardFE28HtmlText(html);
  if (!/Gross Domestic Product/i.test(text)) shipyardFE28Fail('bea_release_topic_title_unverified');
  const dateText = /Current release:?\s*([A-Za-z]+ \d{1,2}, \d{4})/i.exec(text)?.[1];
  const date = shipyardFE28DateISO(dateText);
  const q = /GDP\s*\(Advance Estimate\),\s*(1st|2nd|3rd|4th)\s+Quarter\s+(\d{4})/i.exec(text);
  const ordinal = q ? ({1:1, 2:2, 3:3, 4:4})[Number(q[1][0])] : null;
  if (!q || !ordinal) shipyardFE28Fail('bea_current_gdp_quarter_unverified');
  return { dataset: 'BEA:GDP', current_release_date: date,
    latest_gdp_release_quarter: `${q[2]}-Q${ordinal}`,
    publication_clock_precision: 'current GDP release date only; per-quarter NIPA revisions not supplied by this page' };
}
function shipyardFE28DateAgeUpperBound(date, evaluationAt) {
  const age = (Date.parse(evaluationAt) - Date.parse(date + 'T00:00:00.000Z')) / 1000;
  if (!Number.isFinite(age) || age < 0) shipyardFE28Fail('release_date_after_evaluation');
  return age;
}
function shipyardFE28Crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) { crc ^= byte; for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0); }
  return (crc ^ 0xffffffff) >>> 0;
}
function shipyardFE28U16(bytes, at) { return bytes[at] | (bytes[at + 1] << 8); }
function shipyardFE28U32(bytes, at) { return (bytes[at] | (bytes[at + 1] << 8) | (bytes[at + 2] << 16) | (bytes[at + 3] << 24)) >>> 0; }
async function shipyardFE28Unzip(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length < 22 || bytes.length > SHIPYARD_FE28_POLICY.max_bea_compressed_bytes) shipyardFE28Fail('bea_xlsx_size_invalid');
  let eocd = -1; for (let i = bytes.length - 22, floor = Math.max(0, bytes.length - 65557); i >= floor; i--) if (shipyardFE28U32(bytes, i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0 || shipyardFE28U16(bytes, eocd + 4) || shipyardFE28U16(bytes, eocd + 6)
      || shipyardFE28U16(bytes, eocd + 8) !== shipyardFE28U16(bytes, eocd + 10)
      || eocd + 22 + shipyardFE28U16(bytes, eocd + 20) !== bytes.length) shipyardFE28Fail('bea_zip_directory_invalid');
  const count = shipyardFE28U16(bytes, eocd + 10), directorySize = shipyardFE28U32(bytes, eocd + 12), directoryAt = shipyardFE28U32(bytes, eocd + 16);
  if (!count || count > 512 || count === 0xffff || directorySize === 0xffffffff || directoryAt === 0xffffffff
      || directoryAt + directorySize !== eocd) shipyardFE28Fail('bea_zip_bounds_invalid');
  const entries = new Map(); let at = directoryAt, totalUncompressed = 0;
  for (let i = 0; i < count; i++) {
    if (shipyardFE28U32(bytes, at) !== 0x02014b50) shipyardFE28Fail('bea_zip_central_directory_corrupt');
    const flags = shipyardFE28U16(bytes, at + 8), method = shipyardFE28U16(bytes, at + 10), crc = shipyardFE28U32(bytes, at + 16);
    const compressedSize = shipyardFE28U32(bytes, at + 20), uncompressedSize = shipyardFE28U32(bytes, at + 24);
    const nameLength = shipyardFE28U16(bytes, at + 28), extraLength = shipyardFE28U16(bytes, at + 30), commentLength = shipyardFE28U16(bytes, at + 32), diskStart = shipyardFE28U16(bytes, at + 34), localAt = shipyardFE28U32(bytes, at + 42);
    if (at + 46 + nameLength + extraLength + commentLength > directoryAt + directorySize) shipyardFE28Fail('bea_zip_central_entry_bounds_invalid');
    const name = new TextDecoder('utf-8', { fatal: true }).decode(bytes.slice(at + 46, at + 46 + nameLength));
    const extraStart = at + 46 + nameLength;
    for (let x = extraStart; x < extraStart + extraLength;) {
      if (x + 4 > extraStart + extraLength) shipyardFE28Fail('bea_zip_extra_field_invalid');
      const id = shipyardFE28U16(bytes, x), length = shipyardFE28U16(bytes, x + 2);
      if (x + 4 + length > extraStart + extraLength || id === 0x0001) shipyardFE28Fail('bea_zip64_or_bad_extra_field');
      x += 4 + length;
    }
    at += 46 + nameLength + extraLength + commentLength;
    const pathParts = name.split('/').filter((part, index, parts) => !(index === parts.length - 1 && part === ''));
    if (!name || name.startsWith('/') || name.includes('\\') || name.includes(':') || /[\u0000-\u001f]/.test(name)
        || pathParts.some(part => !part || part === '.' || part === '..') || entries.has(name)
        || /(?:vbaProject|externalLinks|connections\.xml)/i.test(name) || (flags & 1) || (flags & 8)
        || ![0, 8].includes(method) || diskStart !== 0 || compressedSize === 0xffffffff
        || uncompressedSize === 0xffffffff || localAt === 0xffffffff) shipyardFE28Fail('bea_zip_entry_unsupported');
    totalUncompressed += uncompressedSize; if (totalUncompressed > SHIPYARD_FE28_POLICY.max_bea_uncompressed_bytes) shipyardFE28Fail('bea_zip_uncompressed_limit');
    entries.set(name, { name, flags, method, crc, compressedSize, uncompressedSize, localAt,
      extraStart, extraLength, centralEnd: at });
  }
  if (at !== directoryAt + directorySize) shipyardFE28Fail('bea_zip_central_directory_size_mismatch');
  const maxPartBytes = 2 * 1024 * 1024;
  const extract = async name => {
    const entry = entries.get(name);
    if (!entry || entry.uncompressedSize > maxPartBytes || entry.localAt + 30 > directoryAt
        || shipyardFE28U32(bytes, entry.localAt) !== 0x04034b50) shipyardFE28Fail('bea_zip_selected_part_invalid');
    const localFlags = shipyardFE28U16(bytes, entry.localAt + 6), localMethod = shipyardFE28U16(bytes, entry.localAt + 8);
    const localCrc = shipyardFE28U32(bytes, entry.localAt + 14), localCompressed = shipyardFE28U32(bytes, entry.localAt + 18), localUncompressed = shipyardFE28U32(bytes, entry.localAt + 22);
    const localNameLength = shipyardFE28U16(bytes, entry.localAt + 26), localExtraLength = shipyardFE28U16(bytes, entry.localAt + 28);
    const nameStart = entry.localAt + 30, start = nameStart + localNameLength + localExtraLength, end = start + entry.compressedSize;
    if (start > directoryAt || end > directoryAt || localFlags !== entry.flags || localMethod !== entry.method
        || localCrc !== entry.crc || localCompressed !== entry.compressedSize || localUncompressed !== entry.uncompressedSize
        || new TextDecoder('utf-8', { fatal: true }).decode(bytes.slice(nameStart, nameStart + localNameLength)) !== name) shipyardFE28Fail('bea_zip_local_central_mismatch');
    for (let x = nameStart + localNameLength; x < start;) {
      if (x + 4 > start) shipyardFE28Fail('bea_zip_local_extra_invalid');
      const id = shipyardFE28U16(bytes, x), length = shipyardFE28U16(bytes, x + 2);
      if (x + 4 + length > start || id === 0x0001) shipyardFE28Fail('bea_zip64_or_bad_local_extra');
      x += 4 + length;
    }
    const compressed = bytes.slice(start, end); let plain;
    if (entry.method === 0) plain = compressed;
    else {
      const reader = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader();
      const chunks = []; let size = 0;
      try {
        for (;;) {
          const { done, value } = await reader.read(); if (done) break;
          size += value.byteLength;
          if (size > maxPartBytes || size > entry.uncompressedSize) { await reader.cancel(); shipyardFE28Fail('bea_zip_inflate_limit'); }
          chunks.push(value);
        }
      } finally { reader.releaseLock(); }
      plain = new Uint8Array(size); let offset = 0; for (const chunk of chunks) { plain.set(chunk, offset); offset += chunk.byteLength; }
    }
    if (plain.length !== entry.uncompressedSize || shipyardFE28Crc32(plain) !== entry.crc) shipyardFE28Fail('bea_zip_crc_or_size_mismatch');
    const xml = new TextDecoder('utf-8', { fatal: true }).decode(plain);
    if (/<!DOCTYPE|<!ENTITY/i.test(xml)) shipyardFE28Fail('bea_xlsx_dtd_entity_rejected');
    return xml;
  };
  const wanted = new Map();
  for (const name of ['xl/workbook.xml', 'xl/_rels/workbook.xml.rels', 'xl/sharedStrings.xml']) wanted.set(name, await extract(name));
  const workbook = shipyardFE28ParseXml(wanted.get('xl/workbook.xml'));
  const relRoot = shipyardFE28ParseXml(wanted.get('xl/_rels/workbook.xml.rels'));
  if(workbook.local!=='workbook'||workbook.uri!==SHIPYARD_FE28_XML_MAIN||relRoot.local!=='Relationships'||relRoot.uri!==SHIPYARD_FE28_XML_PACKAGE)
    shipyardFE28Fail('bea_xlsx_package_schema_unverified');
  const sheets=shipyardFE28XmlChild(workbook,'sheets',SHIPYARD_FE28_XML_MAIN,{required:true});
  if(sheets.children.some(node=>node.local!=='sheet'||node.uri!==SHIPYARD_FE28_XML_MAIN))shipyardFE28Fail('bea_gdp_sheet_structure_invalid');
  const targetSheets=sheets.children.filter(node=>shipyardFE28XmlAttr(node,'name')==='T10105-Q');
  if(targetSheets.length!==1)shipyardFE28Fail('bea_gdp_sheet_not_unique');
  const relationshipId=shipyardFE28XmlAttr(targetSheets[0],'id',SHIPYARD_FE28_XML_REL);
  if(!relationshipId)shipyardFE28Fail('bea_gdp_sheet_link_unverified');
  if(relRoot.children.some(node=>node.local!=='Relationship'||node.uri!==SHIPYARD_FE28_XML_PACKAGE))shipyardFE28Fail('bea_xlsx_relationship_structure_invalid');
  const relIds=new Set(),relationships=relRoot.children.map(node=>{
    const id=shipyardFE28XmlAttr(node,'Id'),type=shipyardFE28XmlAttr(node,'Type'),target=shipyardFE28XmlAttr(node,'Target'),mode=shipyardFE28XmlAttr(node,'TargetMode');
    if(!id||!type||!target||relIds.has(id))shipyardFE28Fail('bea_xlsx_relationship_invalid');relIds.add(id);return {id,type,target,mode};
  }).filter(item=>item.id===relationshipId);
  if(relationships.length!==1||relationships[0].mode==='External'||relationships[0].type!==SHIPYARD_FE28_XML_REL+'/worksheet'
      ||!/^worksheets\/sheet\d+\.xml$/.test(relationships[0].target||''))shipyardFE28Fail('bea_gdp_sheet_link_unverified');
  const sheetPath=`xl/${relationships[0].target}`;
  wanted.set(sheetPath, await extract(sheetPath));
  return wanted;
}
function shipyardFE28Column(letters) {
  if(!/^[A-Z]{1,4}$/.test(letters||''))shipyardFE28Fail('bea_gdp_cell_coordinate_invalid');
  return [...letters].reduce((n,c)=>n*26+c.charCodeAt(0)-64,0)-1;
}
function shipyardFE28XlsxText(node){
  if(node.uri!==SHIPYARD_FE28_XML_MAIN||node.local!=='t'||node.children.length)shipyardFE28Fail('bea_xlsx_shared_string_invalid');
  return node.text;
}
function shipyardFE28SharedString(node){
  if(node.local!=='si'||node.uri!==SHIPYARD_FE28_XML_MAIN)shipyardFE28Fail('bea_xlsx_shared_string_invalid');
  let value='';for(const child of node.children){
    if(child.local==='t'&&child.uri===SHIPYARD_FE28_XML_MAIN)value+=shipyardFE28XlsxText(child);
    else if(child.local==='r'&&child.uri===SHIPYARD_FE28_XML_MAIN){
      const text=child.children.filter(item=>item.local==='t'&&item.uri===SHIPYARD_FE28_XML_MAIN);
      if(text.length!==1||child.children.some(item=>!['t','rPr'].includes(item.local)||item.uri!==SHIPYARD_FE28_XML_MAIN))shipyardFE28Fail('bea_xlsx_rich_text_unsupported');
      value+=shipyardFE28XlsxText(text[0]);
    }else shipyardFE28Fail('bea_xlsx_shared_string_structure_invalid');
  }
  return value;
}
function shipyardFE28CellValue(cell,sharedStrings){
  if(!cell)return null;
  if(cell.uri!==SHIPYARD_FE28_XML_MAIN||cell.local!=='c'||cell.children.some(child=>child.uri!==SHIPYARD_FE28_XML_MAIN||!['v','is','f'].includes(child.local)))shipyardFE28Fail('bea_xlsx_cell_structure_invalid');
  if(shipyardFE28XmlChildren(cell,'f',SHIPYARD_FE28_XML_MAIN).length)shipyardFE28Fail('bea_gdp_formula_cells_rejected');
  const vals=shipyardFE28XmlChildren(cell,'v',SHIPYARD_FE28_XML_MAIN),inline=shipyardFE28XmlChild(cell,'is',SHIPYARD_FE28_XML_MAIN);
  if(vals.length>1)shipyardFE28Fail('bea_xlsx_cell_value_duplicate');
  const type=shipyardFE28XmlAttr(cell,'t');
  if(inline){if(type!=='inlineStr'||vals.length)shipyardFE28Fail('bea_xlsx_cell_type_invalid');return inline.children.map(shipyardFE28XlsxText).join('');}
  if(!vals.length)return null;
  const raw=shipyardFE28XmlScalar(vals[0]).trim();
  if(type==='s'){
    if(!/^\d+$/.test(raw)||Number(raw)>=sharedStrings.length)shipyardFE28Fail('bea_xlsx_shared_string_index_invalid');
    return sharedStrings[Number(raw)];
  }
  if(type==='str')return raw;
  if(type&&type!=='n')shipyardFE28Fail('bea_xlsx_cell_type_unsupported');
  if(!/^[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?$/.test(raw))shipyardFE28Fail('bea_xlsx_numeric_cell_invalid');
  const value=Number(raw);if(!Number.isFinite(value))shipyardFE28Fail('bea_xlsx_numeric_cell_invalid');return value;
}
function shipyardFE28ParseQuarter(value) {
  const s = String(value || '').trim(); let m = /^(\d{4})\s*-?\s*Q([1-4])$/i.exec(s) || /^Q([1-4])\s*[- ]\s*(\d{4})$/i.exec(s);
  if (m) return m[1].length === 4 ? `${m[1]}-Q${m[2]}` : `${m[2]}-Q${m[1]}`;
  return null;
}
function shipyardFE28ParseBEA(archive) {
  const wb=shipyardFE28ParseXml(archive.get('xl/workbook.xml'));
  const relRoot=shipyardFE28ParseXml(archive.get('xl/_rels/workbook.xml.rels'));
  const sharedRoot=shipyardFE28ParseXml(archive.get('xl/sharedStrings.xml'));
  if(wb.local!=='workbook'||wb.uri!==SHIPYARD_FE28_XML_MAIN||relRoot.local!=='Relationships'||relRoot.uri!==SHIPYARD_FE28_XML_PACKAGE
      ||sharedRoot.local!=='sst'||sharedRoot.uri!==SHIPYARD_FE28_XML_MAIN)shipyardFE28Fail('bea_xlsx_root_schema_invalid');
  const sheets=shipyardFE28XmlChild(wb,'sheets',SHIPYARD_FE28_XML_MAIN,{required:true});
  if(sheets.children.some(node=>node.local!=='sheet'||node.uri!==SHIPYARD_FE28_XML_MAIN))shipyardFE28Fail('bea_xlsx_sheets_structure_invalid');
  const sheetCandidates=sheets.children.filter(node=>shipyardFE28XmlAttr(node,'name')==='T10105-Q');
  if(sheetCandidates.length!==1)shipyardFE28Fail('bea_gdp_table_1_1_5_not_unique');
  const relationId=shipyardFE28XmlAttr(sheetCandidates[0],'id',SHIPYARD_FE28_XML_REL);
  const relMatches=relRoot.children.filter(node=>shipyardFE28XmlAttr(node,'Id')===relationId);
  if(relMatches.length!==1||relMatches[0].local!=='Relationship'||relMatches[0].uri!==SHIPYARD_FE28_XML_PACKAGE
      ||shipyardFE28XmlAttr(relMatches[0],'Type')!==SHIPYARD_FE28_XML_REL+'/worksheet'||shipyardFE28XmlAttr(relMatches[0],'TargetMode')==='External')shipyardFE28Fail('bea_gdp_sheet_link_unverified');
  const target=shipyardFE28XmlAttr(relMatches[0],'Target');
  if(!/^worksheets\/sheet\d+\.xml$/.test(target||''))shipyardFE28Fail('bea_gdp_sheet_link_unverified');
  const sheetPath=`xl/${target}`;if(!archive.has(sheetPath))shipyardFE28Fail('bea_gdp_sheet_link_unverified');
  if(sharedRoot.children.some(node=>node.local!=='si'||node.uri!==SHIPYARD_FE28_XML_MAIN)||sharedRoot.children.length>100000)shipyardFE28Fail('bea_xlsx_shared_string_structure_invalid');
  const shared=sharedRoot.children.map(shipyardFE28SharedString);
  const sheet=shipyardFE28ParseXml(archive.get(sheetPath));
  if(sheet.local!=='worksheet'||sheet.uri!==SHIPYARD_FE28_XML_MAIN)shipyardFE28Fail('bea_xlsx_sheet_root_invalid');
  const data=shipyardFE28XmlChild(sheet,'sheetData',SHIPYARD_FE28_XML_MAIN,{required:true});
  if(data.children.some(node=>node.local!=='row'||node.uri!==SHIPYARD_FE28_XML_MAIN))shipyardFE28Fail('bea_xlsx_sheetdata_structure_invalid');
  const rows=[];let previousRow=0;
  for(const rowNode of data.children){
    shipyardFE28XmlOnlyWhitespace(rowNode);
    const rowNo=Number(shipyardFE28XmlAttr(rowNode,'r'));
    if(!Number.isInteger(rowNo)||rowNo<=previousRow||rowNo<1)shipyardFE28Fail('bea_xlsx_row_coordinate_invalid');previousRow=rowNo;
    if(rowNode.children.some(cell=>cell.local!=='c'||cell.uri!==SHIPYARD_FE28_XML_MAIN))shipyardFE28Fail('bea_xlsx_row_structure_invalid');
    const cells=new Map();let previousColumn=-1;
    for(const cell of rowNode.children){
      const ref=shipyardFE28XmlAttr(cell,'r'),match=/^([A-Z]{1,4})(\d+)$/.exec(ref||'');
      if(!match||Number(match[2])!==rowNo)shipyardFE28Fail('bea_xlsx_cell_coordinate_invalid');
      const column=shipyardFE28Column(match[1]);if(column<=previousColumn||cells.has(column))shipyardFE28Fail('bea_xlsx_cell_coordinate_duplicate_or_unsorted');previousColumn=column;
      cells.set(column,shipyardFE28CellValue(cell,shared));
    }
    rows.push(cells);
  }
  const allText = rows.flatMap(row => [...row.values()].filter(value => typeof value === 'string')).join(' ');
  const lowerText = allText.toLowerCase();
  const title = rows[0]?.get(0);
  if (typeof title !== 'string' || !/^Table 1\.1\.5\.\s*Gross Domestic Product$/i.test(title.trim())) shipyardFE28Fail('bea_gdp_table_title_unverified');
  if (!/\[Millions of dollars\]/i.test(allText) || !/seasonally adjusted at annual rates/i.test(lowerText)) shipyardFE28Fail('bea_gdp_units_unverified');
  const published = /\bData published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})\b/i.exec(allText)?.[1];
  const dataPublishedDate = shipyardFE28DateISO(published);
  const quarterHeaders = rows.map(row => {
    const values = [...row].map(([col, value]) => [col, shipyardFE28ParseQuarter(value)]).filter(([, quarter]) => quarter);
    return { row, values };
  }).filter(candidate => candidate.values.length >= 43).sort((a, b) => b.values.length - a.values.length);
  if (!quarterHeaders.length || (quarterHeaders[1] && quarterHeaders[1].values.length === quarterHeaders[0].values.length)) shipyardFE28Fail('bea_gdp_quarter_header_ambiguous');
  const quarterByColumn = new Map(quarterHeaders[0].values);
  const orderedHeaders = [...quarterByColumn.values()].sort((a, b) => shipyardFE28QuarterIndex(a) - shipyardFE28QuarterIndex(b));
  if (orderedHeaders.some((quarter, i) => i && shipyardFE28QuarterIndex(quarter) !== shipyardFE28QuarterIndex(orderedHeaders[i - 1]) + 1)) shipyardFE28Fail('bea_gdp_quarter_header_gap');
  const gdpRows = rows.filter(row => [...row.values()].some(value => typeof value === 'string' && value.trim().toLowerCase() === 'gross domestic product'));
  if (gdpRows.length !== 1) shipyardFE28Fail('bea_gdp_row_not_unique');
  const quarters = orderedHeaders.map(quarter => {
    const col = [...quarterByColumn].find(([, value]) => value === quarter)?.[0];
    const millions = gdpRows[0].get(col);
    if (typeof millions !== 'number' || !Number.isFinite(millions) || millions <= 0) shipyardFE28Fail('bea_gdp_value_missing_or_invalid');
    return { quarter, gdp_saar: millions / 1000 };
  });
  if (quarters.length < 43) shipyardFE28Fail('bea_gdp_quarter_history_unverified');
  return { rows: quarters, quarter_history_count: quarters.length,
    quarter_history_first_value: quarters[0].gdp_saar, quarter_history_latest_value: quarters.at(-1).gdp_saar,
    workbook_metadata: { worksheet: 'T10105-Q', table_title: title.trim(),
    raw_unit: 'millions_of_US_dollars_SAAR', normalized_unit: 'billions_of_US_dollars_SAAR',
    conversion: 'millions_divided_by_1000', data_published_date: dataPublishedDate,
    quarter_history_first: quarters[0].quarter, quarter_history_latest: quarters.at(-1).quarter } };
}
function shipyardFE28SecureXml(xml) {
  if (typeof xml !== 'string' || /<!DOCTYPE|<!ENTITY/i.test(xml)) shipyardFE28Fail('bea_xlsx_dtd_entity_rejected');
  return xml;
}
function shipyardFE28QuarterIndex(quarter) { const match = /^(\d{4})-Q([1-4])$/.exec(quarter || ''); if (!match) shipyardFE28Fail('invalid_quarter'); return Number(match[1]) * 4 + Number(match[2]) - 1; }
function shipyardFE28QuarterEndLowerBound(quarter) {
  const match = /^(\d{4})-Q([1-4])$/.exec(quarter || ''); if (!match) shipyardFE28Fail('invalid_quarter');
  return new Date(Date.UTC(Number(match[1]), Number(match[2]) * 3, 0)).toISOString().slice(0, 10) + 'T00:00:00.000Z';
}
function shipyardFE28Base() { return { schema: 'SHIPYARD_FE28_PUBLIC_SOURCE_V1', engine_id: 'FE28', feature_policy: SHIPYARD_FORECAST_FE2730_FEATURES.FE28_PUBLIC_POLICY,
  status: 'unavailable', diagnostic_only: true, features: {}, diagnostic_features: {},
  missing_features: ['curve_slope_z', 'curve_change_z', 'credit_impulse_z', 'macro_transition_score'], source_receipts: [],
  scorer_invoked: false, restrictions: { research_only: true, decision_eligible: false, order_submission_enabled: false,
    account_data_returned: false, historical_point_in_time_claim: false, calibrated_probability: null, quality_score: null, rights_attestation: null } }; }
async function shipyardForecastMacroFeatures(request, args = {}) {
  const started = Date.now(), out = shipyardFE28Base();
  if (!args || typeof args !== 'object' || Array.isArray(args) || Object.keys(args).length) return json({ ...out, status: 'invalid', error: 'invalid_arguments' }, 400);
  const deadline = started + 28000, receipts = []; out.source_receipts = receipts;
  // Keep parsed source rows only for this calculation. The MCP projection uses
  // bounded first/latest/count summaries and response hashes, never full tables.
  let bisRows=null,beaRows=null;
  const getText = async (url, host, operation, maxBytes, accept) => {
    if (new URL(url).hostname !== host || !url.startsWith(`https://${host}/`)) shipyardFE28Fail('source_host_not_allowlisted');
    if (Date.now() >= deadline || request.signal.aborted) shipyardFE28Fail('acquisition_deadline_exceeded');
    const requestedAt = new Date().toISOString();
    const response = await fetch(url, { method: 'GET', credentials: 'omit', cache: 'no-store', redirect: 'manual', headers: { accept }, signal: AbortSignal.any([request.signal, AbortSignal.timeout(Math.min(SHIPYARD_FE28_POLICY.source_timeout_ms, deadline - Date.now()))]) });
    const body = await readBoundedBody(response, maxBytes), receivedAt = new Date().toISOString(), bytes = new TextEncoder().encode(body);
    const receipt = { operation, request_url: url, requested_at: requestedAt, received_at: receivedAt, http_status: response.status,
      content_type: response.headers.get('content-type'), response_sha256: await shipyardFE28Hash(bytes),
      http_last_modified: response.headers.get('last-modified'), etag: response.headers.get('etag') };
    receipts.push(receipt);
    if (response.status !== 200) shipyardFE28Fail(`${operation}_http_${response.status}`);
    if (new URL(response.url || url).hostname !== host) shipyardFE28Fail(`${operation}_redirect_or_host_change`);
    return { body, bytes, receivedAt, receipt };
  };
  const getBinary = async (url, host, operation, maxBytes, accept) => {
    if (new URL(url).hostname !== host || !url.startsWith(`https://${host}/`)) shipyardFE28Fail('source_host_not_allowlisted');
    if (Date.now() >= deadline || request.signal.aborted) shipyardFE28Fail('acquisition_deadline_exceeded');
    const requestedAt = new Date().toISOString();
    const response = await fetch(url, { method: 'GET', credentials: 'omit', cache: 'no-store', redirect: 'manual', headers: { accept }, signal: AbortSignal.any([request.signal, AbortSignal.timeout(Math.min(SHIPYARD_FE28_POLICY.source_timeout_ms, deadline - Date.now()))]) });
    if (!response.body) shipyardFE28Fail(`${operation}_missing_body`);
    const reader = response.body.getReader(), chunks = []; let size = 0;
    for (;;) { const { done, value } = await reader.read(); if (done) break; size += value.byteLength;
      if (size > maxBytes) { await reader.cancel(); shipyardFE28Fail(`${operation}_body_too_large`); } chunks.push(value); }
    const bytes = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const receivedAt = new Date().toISOString(), type = response.headers.get('content-type') || '';
    const receipt = { operation, request_url: url, requested_at: requestedAt, received_at: receivedAt, http_status: response.status,
      content_type: type, response_sha256: await shipyardFE28Hash(bytes), http_last_modified: response.headers.get('last-modified'), etag: response.headers.get('etag') };
    receipts.push(receipt);
    if (response.status !== 200) shipyardFE28Fail(`${operation}_http_${response.status}`);
    if (new URL(response.url || url).hostname !== host) shipyardFE28Fail(`${operation}_redirect_or_host_change`);
    if (!/(?:spreadsheetml\.sheet|application\/zip|octet-stream)/i.test(type)) shipyardFE28Fail(`${operation}_content_type_unverified`);
    return { bytes, receivedAt, receipt };
  };
  try {
    const now = started, currentYear = new Date(now).getUTCFullYear(), years = [currentYear - 2, currentYear - 1, currentYear];
    const treasury = await Promise.all(years.map(async year => {
      const url = `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=${shipyardFE28Year(year)}`;
      const response = await getText(url, 'home.treasury.gov', `treasury_${year}`, SHIPYARD_FE28_POLICY.max_treasury_bytes_per_year, 'application/xml');
      return { year, rows: shipyardFE28ParseTreasury(response.body, year), received_at: response.receivedAt, source_sha256: response.receipt.response_sha256 };
    }));
    const merged = new Map(); for (const year of treasury) for (const row of year.rows) merged.set(row.date, { ...row, snapshot_id: 'pending', source_id: 'US_TREASURY_PAR_YIELD_CURVE',
      record_id: `YIELD-${row.date}`, source_url: 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve',
      source_sha256: year.source_sha256, unit: 'percentage_point', available_at: null, received_at: year.received_at,
      publication_at: null, clock_semantics: 'observation date retained; publication/availability unknown; raw capture receipt separate' });
    const treasuryRows = [...merged.values()].sort((a, b) => a.date.localeCompare(b.date)).slice(-254);
    const snapshotId = 'TREASURY-' + (await shipyardFE28Hash(shipyardFE28TextBytes(years.join('|') + '|' + treasury.map(x => x.source_sha256).join('|'), 1024)));
    for (const row of treasuryRows) row.snapshot_id = snapshotId;
    const curve = SHIPYARD_FORECAST_FE2730_FEATURES.computeFE28TreasuryCurveDiagnostic({ evaluation_at: new Date(Date.now()).toISOString(), observations: treasuryRows,
      snapshot_id: snapshotId, vintage_mode: 'current_latest_snapshot' });
    Object.assign(out.diagnostic_features, curve.diagnostic_features);
    out.treasury = { measurements: curve.measurements, source: curve.source, freshness: curve.freshness,
      diagnostic_only: true, original_freshness_gate_closed: true };
  } catch (error) { out.blockers ||= []; out.blockers.push(`treasury:${error?.message || 'unavailable'}`); }
  try {
    const evaluation = new Date(Date.now()), currentQuarter = `${evaluation.getUTCFullYear()}-Q${Math.floor(evaluation.getUTCMonth() / 3) + 1}`;
    const endYear = Number(currentQuarter.slice(0, 4)), startQuarter = `${endYear - 11}-Q1`;
    const url = `https://stats.bis.org/api/v1/data/WS_TC/Q.US.P.A.M.XDC.A/all?startPeriod=${startQuarter}&endPeriod=${currentQuarter}`;
    const response = await getText(url, 'stats.bis.org', 'bis_ws_tc_us_private_total_credit', SHIPYARD_FE28_POLICY.max_bis_bytes, 'application/xml');
    if (!/application\/xml|text\/xml/i.test(response.receipt.content_type || '')) shipyardFE28Fail('bis_sdmx_content_type_unverified');
    const data = shipyardFE28ParseBISXml(response.body).slice(-43);
    bisRows=data;
    out.bis_credit_capture = { source_id: 'BIS:WS_TC:Q.US.P.A.M.XDC.A', flow: 'WS_TC', version: '2.0', series_key: 'Q.US.P.A.M.XDC.A',
      identity: SHIPYARD_FE28_POLICY.bis_dimensions, unit: 'USD_billions', currency: 'USD', stock_timing: 'quarter-end',
      row_summary: { count: data.length, first_quarter: data[0]?.quarter ?? null, latest_quarter: data.at(-1)?.quarter ?? null,
        first_credit_stock: data[0]?.credit_stock ?? null, latest_credit_stock: data.at(-1)?.credit_stock ?? null,
        full_rows_in_mcp_response: false, vintage_status: 'current_revised_snapshot; publication/revision clock not provided by API capture' },
      source_sha256: response.receipt.response_sha256, received_at: response.receivedAt,
      source_url: 'https://data.bis.org/topics/TOTAL_CREDIT/BIS%2CWS_TC%2C2.0/Q.US.P.A.M.XDC.A',
      capture_url: url, response_content_type: response.receipt.content_type,
      rights_status: 'not independently attested' };
  } catch (error) { out.blockers ||= []; out.blockers.push(`bis:${error?.message || 'unavailable'}`); }
  try {
    const response = await getText('https://data.bis.org/topics/TOTAL_CREDIT', 'data.bis.org', 'bis_total_credit_release_metadata',
      524288, 'text/html');
    if (!/text\/html/i.test(response.receipt.content_type || '')) shipyardFE28Fail('bis_release_metadata_content_type_unverified');
    const metadata = shipyardFE28ParseBISReleaseMetadata(response.body);
    const evaluationAt = new Date(Date.now()).toISOString();
    const age = shipyardFE28DateAgeUpperBound(metadata.last_release_date, evaluationAt);
    out.bis_release_metadata = { ...metadata, source_url: 'https://data.bis.org/topics/TOTAL_CREDIT',
      response_sha256: response.receipt.response_sha256, captured_at: response.receivedAt,
      release_date_age_upper_bound_seconds: age, max_age_seconds: SHIPYARD_FE28_POLICY.bis_release_max_age_seconds,
      within_max_age_by_bound: age <= SHIPYARD_FE28_POLICY.bis_release_max_age_seconds,
      scope: 'dataset release clock only; not an independently pinned per-quarter value vintage' };
  } catch (error) { out.blockers ||= []; out.blockers.push(`bis_release_metadata:${error?.message || 'unavailable'}`); }
  try {
    const response = await getBinary(SHIPYARD_FE28_POLICY.bea_url, 'apps.bea.gov', 'bea_nipa_section_1',
      SHIPYARD_FE28_POLICY.max_bea_compressed_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    const gdp = shipyardFE28ParseBEA(await shipyardFE28Unzip(response.bytes));
    beaRows=gdp.rows;
    out.bea_gdp_capture = { source_id: 'BEA:NIPA:1.1.5', series_id: 'GDP', unit: 'billions_of_dollars_SAAR', currency: 'USD',
      row_summary: { count: gdp.quarter_history_count, first_quarter: gdp.workbook_metadata.quarter_history_first,
        latest_quarter: gdp.workbook_metadata.quarter_history_latest, first_gdp_saar: gdp.quarter_history_first_value,
        latest_gdp_saar: gdp.quarter_history_latest_value, retained_calculation_rows: gdp.rows.length,
        full_rows_in_mcp_response: false, vintage_status: 'current_revised_NIPA_snapshot; quarterly publication/revision clocks not provided by workbook' },
      workbook_metadata: { ...gdp.workbook_metadata, source_file_sha256: response.receipt.response_sha256,
        captured_at: response.receivedAt, publication_semantics: 'dataset-level current table publication date in this exact workbook; not per-quarter historical vintage' },
      source_sha256: response.receipt.response_sha256, received_at: response.receivedAt,
      http_last_modified: response.receipt.http_last_modified, source_url: SHIPYARD_FE28_POLICY.bea_url, rights_status: 'not independently attested' };
  } catch (error) { out.blockers ||= []; out.blockers.push(`bea:${error?.message || 'unavailable'}`); }
  try {
    const response = await getText('https://www.bea.gov/data/gdp/gross-domestic-product', 'www.bea.gov', 'bea_gdp_current_release_metadata',
      524288, 'text/html');
    if (!/text\/html/i.test(response.receipt.content_type || '')) shipyardFE28Fail('bea_release_metadata_content_type_unverified');
    const metadata = shipyardFE28ParseBEAReleaseMetadata(response.body);
    const evaluationAt = new Date(Date.now()).toISOString();
    const age = shipyardFE28DateAgeUpperBound(metadata.current_release_date, evaluationAt);
    const workbookLatestQuarter = out.bea_gdp_capture?.row_summary?.latest_quarter || null;
    const workbookPublishedDate = out.bea_gdp_capture?.workbook_metadata?.data_published_date || null;
    out.bea_release_metadata = { ...metadata, source_url: 'https://www.bea.gov/data/gdp/gross-domestic-product',
      response_sha256: response.receipt.response_sha256, captured_at: response.receivedAt,
      release_date_age_upper_bound_seconds: age, max_age_seconds: SHIPYARD_FE28_POLICY.gdp_release_max_age_seconds,
      within_max_age_by_bound: age <= SHIPYARD_FE28_POLICY.gdp_release_max_age_seconds,
      workbook_latest_quarter: workbookLatestQuarter,
      workbook_quarter_matches_release: workbookLatestQuarter === metadata.latest_gdp_release_quarter,
      workbook_published_date: workbookPublishedDate,
      workbook_publication_date_matches_page: workbookPublishedDate === metadata.current_release_date,
      scope: 'page date cross-checks dataset-level date parsed from exact hashed workbook; neither is a per-quarter NIPA revision/vintage' };
  } catch (error) { out.blockers ||= []; out.blockers.push(`bea_release_metadata:${error?.message || 'unavailable'}`); }
  if (out.bis_credit_capture && out.bea_gdp_capture && Array.isArray(bisRows) && Array.isArray(beaRows)) {
    try {
      const credit = new Map(bisRows.map(row => [row.quarter, row.credit_stock]));
      const gdp = new Map(beaRows.map(row => [row.quarter, row.gdp_saar]));
      const quarters = bisRows.map(row => row.quarter).filter(q => gdp.has(q)).slice(-43);
      if (quarters.length !== 43 || quarters.some((q, i) => i && shipyardFE28QuarterIndex(q) !== shipyardFE28QuarterIndex(quarters[i - 1]) + 1)) shipyardFE28Fail('bis_bea_quarter_identity_or_43_window_mismatch');
      const creditReceived = out.bis_credit_capture.received_at, gdpReceived = out.bea_gdp_capture.received_at;
      const qRows = quarters.map(quarter => ({ quarter, credit_stock: credit.get(quarter), gdp_saar: gdp.get(quarter), currency: 'USD',
        credit_source_id: 'BIS:F2.3', gdp_source_id: 'BEA:GDP', measure: 'private_nonfinancial_credit',
        credit_unit: 'local_currency_billions', gdp_unit: 'local_currency_billions_SAAR',
        credit_observed_at: shipyardFE28QuarterEndLowerBound(quarter), gdp_observed_at: shipyardFE28QuarterEndLowerBound(quarter),
        credit_snapshot_id: out.bis_credit_capture.source_sha256, gdp_snapshot_id: out.bea_gdp_capture.source_sha256,
        credit_record_id: `BIS-${quarter}`, gdp_record_id: `BEA-GDP-${quarter}`,
        credit_source_sha256: out.bis_credit_capture.source_sha256, gdp_source_sha256: out.bea_gdp_capture.source_sha256,
        credit_available_at: null, gdp_available_at: null,
        credit_publication_at: null, gdp_publication_at: null, credit_revision_at: null, gdp_revision_at: null,
        credit_clock_semantics: 'capture receipt; true per-quarter publication/revision clocks unknown',
        gdp_clock_semantics: 'capture receipt; true per-quarter publication/revision clocks unknown',
        credit_received_at: creditReceived, gdp_received_at: gdpReceived }));
      const diagnostic = SHIPYARD_FORECAST_FE2730_FEATURES.computeFE28CreditImpulseDiagnostic({ evaluation_at: new Date().toISOString(),
        quarters: qRows, credit_snapshot_id: out.bis_credit_capture.source_sha256,
        gdp_snapshot_id: out.bea_gdp_capture.source_sha256, vintage_mode: 'current_latest_snapshot' });
      out.diagnostic_features.credit_impulse_z = diagnostic.diagnostic_feature;
      out.credit_measurement = diagnostic.measurement; out.credit_source = diagnostic.source; out.credit_freshness = diagnostic.freshness;
      out.credit_source.joint_quarter_window={matched_quarters:quarters.length,first_quarter:quarters[0],latest_joint_quarter:quarters.at(-1),
        latest_bis_credit_quarter:out.bis_credit_capture.row_summary.latest_quarter,
        latest_bea_gdp_quarter:out.bea_gdp_capture.row_summary.latest_quarter,
        gdp_latest_lead_quarters:shipyardFE28QuarterIndex(out.bea_gdp_capture.row_summary.latest_quarter)-shipyardFE28QuarterIndex(out.bis_credit_capture.row_summary.latest_quarter),
        semantics:'strict identical-economic-quarter join; GDP periods after latest BIS credit observation are retained in its source summary but excluded from the credit calculation'};
      if (out.bis_release_metadata && out.bea_release_metadata) {
        const bisAge = out.bis_release_metadata.release_date_age_upper_bound_seconds;
        const beaSnapshotDate = out.bea_gdp_capture.workbook_metadata.data_published_date;
        const beaAge = shipyardFE28DateAgeUpperBound(beaSnapshotDate, new Date().toISOString());
        out.credit_source.dataset_release_age_upper_bound_seconds = Math.max(bisAge, beaAge);
        out.credit_source.dataset_release_date_bounds = { bis: out.bis_release_metadata.last_release_date,
          bea_workbook_publication_date: beaSnapshotDate, bea_page_current_gdp_release: out.bea_release_metadata.current_release_date,
          bea_page_matches_workbook_date: out.bea_release_metadata.workbook_publication_date_matches_page,
          bea_workbook_sha256: out.bea_gdp_capture.source_sha256,
          semantics: 'BIS dataset release date and BEA publication date parsed from the exact hashed workbook are lower bounds used as conservative dataset-snapshot age upper bounds; neither is a per-quarter availability or revision clock',
          bis_release_page_capture_is_not_atomic_with_data_snapshot: true };
        out.credit_freshness = { ...out.credit_freshness,
          dataset_release_age_upper_bound_seconds: Math.max(bisAge, beaAge),
          within_90day_dataset_release_age_by_bound: Math.max(bisAge, beaAge) <= SHIPYARD_FE28_POLICY.gdp_release_max_age_seconds,
          per_quarter_publication_gate: 'closed_unknown' };
      }
    } catch (error) { out.blockers ||= []; out.blockers.push(`credit_transform:${error?.message || 'unavailable'}`); }
  } else out.blockers?.push('credit_impulse_z_requires_verified_BIS_US_series_and_BEANominalGDP_join');
  out.blockers ||= [];
  if (['curve_slope_z', 'curve_change_z', 'credit_impulse_z'].every(key => typeof out.diagnostic_features[key] === 'number' && Number.isFinite(out.diagnostic_features[key]))) {
    try {
      const transition = SHIPYARD_FORECAST_FE2730_FEATURES.computeFE28TransitionRisk(out.diagnostic_features);
      out.diagnostic_features.macro_transition_score = transition.feature;
      out.transition_risk_measurement = transition.measurement;
    } catch (error) { out.blockers.push(`transition_risk:${error?.message || 'unavailable'}`); }
  } else out.blockers.push('macro_transition_score_requires_three_verified_same_cutoff_primitives');
  out.blockers.push('Treasury session calendar completeness is unverified; returned-row calculations are descriptive only',
    'Treasury publication clock remains unknown; age is a conservative observation-date upper bound and receipt does not reset it',
    'BIS/BEA per-quarter publication/revision clocks are unknown; dataset-level release dates do not replace row vintages',
    'NEW equal-weight transition index is not the lost original feature builder or a calibrated probability',
    'source redistribution/rights and full Python FeatureObservation quality gates not independently attested', 'research-only; original FE28 scorer never invoked');
  out.missing_features = ['curve_slope_z', 'curve_change_z', 'credit_impulse_z', 'macro_transition_score'];
  out.status = Object.keys(out.diagnostic_features).length ? 'partial_diagnostic' : 'unavailable';
  out.computed_at = new Date().toISOString(); out.acquisition = { request_bound: SHIPYARD_FE28_POLICY.acquisition_request_bound,
    requests_made: receipts.length, elapsed_ms: Date.now() - started, persistent_write: false, provider_credentials_used: false };
  return json(out);
}
