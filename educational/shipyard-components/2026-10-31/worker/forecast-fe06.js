// FE06 issuer-source adapter. The upstream scorer is intentionally untouched.
// No caller-provided URLs or rows are accepted: both source and universe are fixed.
const SHIPYARD_FE06_POLICY = Object.freeze({
  id: 'fe06-issuer-share-nav-flow-v1',
  version: '1.0.0',
  kind: 'NEW_DERIVED_PROXY_NOT_OBSERVED_VENDOR_FUND_FLOW',
  universe_policy: 'FIXED_CURRENT_11_SELECT_SECTOR_SPDR_ETFS_NOT_HISTORICAL_MEMBERSHIP',
  session_count: 254,
  flow_baseline_sessions: 252,
  momentum_lookback_sessions: 21,
  momentum_measure: 'NAV_price_return_split_adjusted_dividend_excluded',
  momentum_rank: 'target_ticker_ascending_average_ties_across_fixed_11; sample_zscore_of_ranks_ddof1',
  leadership_breadth: 'count_of_strictly_positive_21_session_NAV_returns_divided_by_11',
  dispersion: 'sample_sd_of_11_one_session_NAV_returns; z_vs_prior_252_daily_dispersions_ddof1',
  sector_flow: 'target_fund_prior252_zscore_of_estimated_flow_over_prior_assets',
  flow_formula: 'NAV_t*(shares_t-r_t*shares_t_minus_1)/assets_t_minus_1',
  default_split_policy: 'r=1 only under explicit ordinary-share-continuity assumption; suspicious unverified split signatures abstain',
  unsupported_split_signature_ratios: Object.freeze([2,3,4,1.5,5,10]),
  unsupported_split_signature_tolerance: 0.15,
  unsupported_split_signature_policy: 'heuristic only: inverse NAV/share jumps near listed ratios abstain; never infer or apply a split ratio; only the source-verified action ledger adjusts history',
  asset_reconciliation_tolerance: 0.001,
  max_age_seconds: 172800,
  source_cutoff_policy: 'latest_common_issuer_session_within_48h_not_required_to_equal_latest_completed_market_session',
  semantic_clock: 'issuer-defined regular NYSE close in America/New_York; publication time unknown',
  rights_status: 'issuer_redistribution_rights_not_established',
  decision_eligible: false,
  historical_point_in_time_available: false,
});
const SHIPYARD_FE06_POLICY_SHA256='5ce7c0aa0a4f36fe5b6890998638e9104461970318482246ae0581afe55717be';
const SHIPYARD_FE06_UNIVERSE = Object.freeze([
  {ticker:'XLC',isin:'US81369Y8527'}, {ticker:'XLY',isin:'US81369Y4070'},
  {ticker:'XLP',isin:'US81369Y3080'}, {ticker:'XLE',isin:'US81369Y5069'},
  {ticker:'XLF',isin:'US81369Y6059'}, {ticker:'XLV',isin:'US81369Y2090'},
  {ticker:'XLI',isin:'US81369Y7040'}, {ticker:'XLB',isin:'US81369Y1001'},
  {ticker:'XLRE',isin:'US81369Y8600'}, {ticker:'XLK',isin:'US81369Y8030'},
  {ticker:'XLU',isin:'US81369Y8865'},
]);
const SHIPYARD_FE06_ORIGIN='https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-';
const SHIPYARD_FE06_SOURCES=Object.freeze(Object.fromEntries(SHIPYARD_FE06_UNIVERSE.map(({ticker,isin})=>[ticker,Object.freeze({
  ticker,isin,url:SHIPYARD_FE06_ORIGIN+ticker.toLowerCase()+'.xlsx',sheet:'navhist',
})])));
const SHIPYARD_FE06_SPLITS=Object.freeze({
  '2025-12-05':Object.freeze({ratio_new_per_old:2,tickers:Object.freeze(['XLK','XLY','XLE','XLU','XLB']),
    source:'https://investors.statestreet.com/investor-news-events/press-releases/news-details/2025/State-Street-Investment-Management-Announces-Share-Splits-for-Five-Select-Sector-SPDR-ETFs/default.aspx',
    announced:'2025-11-20',verified_basis:'official announcement plus adjacent raw NAV/shares workbook records'}),
});
const SHIPYARD_FE06_LIMITS=Object.freeze({
  max_workbook_bytes:400*1024,max_entries:32,max_uncompressed_bytes:8*1024*1024,
  max_entry_bytes:3*1024*1024,max_rows:10000,max_shared_strings:10000,max_string_chars:8192,
  max_total_response_bytes:5*1024*1024,max_calendar_bytes:262144,max_calendar_rows:500,calendar_lookback_days:450,
  max_requests:12,request_timeout_ms:8000,total_timeout_ms:30000,
});
const SHIPYARD_FE06_RUNTIME={ingressRates:new Map(),coldRates:new Map(),cache:new Map(),inflight:new Map()};
const SHIPYARD_FE06_INGRESS={window_ms:60000,max_ingress_requests_per_ip:60,max_cold_acquisitions_per_ip:4,max_tracked_ips:1024,cache_ttl_ms:60000,max_cache_entries:4,max_cache_bytes:262144};

function shipyardFE06Fail(code){const error=new Error(code);error.code=code;throw error;}
function shipyardFE06CheckAbort(request){if(request?.signal?.aborted)shipyardFE06Fail('cancelled');}
function shipyardFE06U16(v,o){if(o<0||o+2>v.length)shipyardFE06Fail('xlsx_zip_invalid');return v.getUint16(o,true);}
function shipyardFE06U32(v,o){if(o<0||o+4>v.length)shipyardFE06Fail('xlsx_zip_invalid');return v.getUint32(o,true);}
function shipyardFE06CRC32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
async function shipyardFE06InflateRaw(compressed,expected){
  let stream;try{stream=new DecompressionStream('deflate-raw');}catch{shipyardFE06Fail('xlsx_deflate_raw_unsupported');}
  const reader=new Blob([compressed]).stream().pipeThrough(stream).getReader(),chunks=[];let size=0;
  try{for(;;){const part=await reader.read();if(part.done)break;size+=part.value.length;if(size>SHIPYARD_FE06_LIMITS.max_entry_bytes||size>expected)shipyardFE06Fail('xlsx_entry_size_limit');chunks.push(part.value);}}
  finally{try{reader.releaseLock();}catch{}}
  const out=new Uint8Array(size);let offset=0;for(const chunk of chunks){out.set(chunk,offset);offset+=chunk.length;}
  if(size!==expected)shipyardFE06Fail('xlsx_entry_size_mismatch');return out;
}
async function shipyardFE06ZipEntries(input){
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  if(bytes.length<22||bytes.length>SHIPYARD_FE06_LIMITS.max_workbook_bytes)shipyardFE06Fail('xlsx_compressed_size_limit');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),floor=Math.max(0,bytes.length-65557);let eocd=-1;
  for(let i=bytes.length-22;i>=floor;i--)if(shipyardFE06U32(view,i)===0x06054b50){eocd=i;break;}
  if(eocd<0)shipyardFE06Fail('xlsx_zip_directory_missing');
  const disk=shipyardFE06U16(view,eocd+4),cdDisk=shipyardFE06U16(view,eocd+6),diskCount=shipyardFE06U16(view,eocd+8),count=shipyardFE06U16(view,eocd+10),cdSize=shipyardFE06U32(view,eocd+12),cdOffset=shipyardFE06U32(view,eocd+16),comment=shipyardFE06U16(view,eocd+20);
  if(disk||cdDisk||diskCount!==count||count<1||count>SHIPYARD_FE06_LIMITS.max_entries||eocd+22+comment!==bytes.length||cdOffset+cdSize!==eocd)shipyardFE06Fail('xlsx_zip_layout_invalid');
  const entries=new Map();let p=cdOffset,totalUncompressed=0;
  for(let i=0;i<count;i++){
    if(shipyardFE06U32(view,p)!==0x02014b50)shipyardFE06Fail('xlsx_zip_directory_invalid');
    const flags=shipyardFE06U16(view,p+8),method=shipyardFE06U16(view,p+10),crc=shipyardFE06U32(view,p+16),compressedSize=shipyardFE06U32(view,p+20),size=shipyardFE06U32(view,p+24),nameLen=shipyardFE06U16(view,p+28),extraLen=shipyardFE06U16(view,p+30),commentLen=shipyardFE06U16(view,p+32),startDisk=shipyardFE06U16(view,p+34),localOffset=shipyardFE06U32(view,p+42);
    if((flags&0x41)||![0,8].includes(method)||startDisk||size===0xffffffff||compressedSize===0xffffffff||localOffset===0xffffffff||size>SHIPYARD_FE06_LIMITS.max_entry_bytes)shipyardFE06Fail('xlsx_zip_feature_unsupported');
    const rawName=bytes.subarray(p+46,p+46+nameLen);if(rawName.length!==nameLen)shipyardFE06Fail('xlsx_zip_directory_invalid');
    const name=new TextDecoder('utf-8',{fatal:true}).decode(rawName);
    if(!name||name.startsWith('/')||name.includes('\\')||name.split('/').includes('..')||/[\x00-\x1f]/.test(name)||entries.has(name))shipyardFE06Fail('xlsx_zip_path_invalid');
    if(/(?:vbaProject|externalLinks|connections|queryTables|embeddings|activeX)/i.test(name))shipyardFE06Fail('xlsx_active_content_unsupported');
    totalUncompressed+=size;if(totalUncompressed>SHIPYARD_FE06_LIMITS.max_uncompressed_bytes)shipyardFE06Fail('xlsx_uncompressed_size_limit');
    if(localOffset+30>bytes.length||shipyardFE06U32(view,localOffset)!==0x04034b50)shipyardFE06Fail('xlsx_local_header_invalid');
    const localNameLen=shipyardFE06U16(view,localOffset+26),localExtraLen=shipyardFE06U16(view,localOffset+28),localName=bytes.subarray(localOffset+30,localOffset+30+localNameLen);
    if(new TextDecoder('utf-8',{fatal:true}).decode(localName)!==name)shipyardFE06Fail('xlsx_local_header_invalid');
    const dataStart=localOffset+30+localNameLen+localExtraLen,dataEnd=dataStart+compressedSize;if(dataEnd>bytes.length)shipyardFE06Fail('xlsx_entry_out_of_bounds');
    entries.set(name,{method,crc,compressedSize,size,data:bytes.subarray(dataStart,dataEnd)});
    p+=46+nameLen+extraLen+commentLen;
  }
  if(p!==cdOffset+cdSize)shipyardFE06Fail('xlsx_zip_directory_invalid');
  const read=async name=>{
    const entry=entries.get(name);if(!entry)shipyardFE06Fail('xlsx_expected_entry_missing');
    const out=entry.method===0?entry.data:new Uint8Array(await shipyardFE06InflateRaw(entry.data,entry.size));
    if(out.length!==entry.size||shipyardFE06CRC32(out)!==entry.crc)shipyardFE06Fail('xlsx_entry_crc_mismatch');return out;
  };
  return {entries,read};
}
const SHIPYARD_FE06_XML_MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const SHIPYARD_FE06_XML_PACKAGE_REL='http://schemas.openxmlformats.org/package/2006/relationships';
const SHIPYARD_FE06_XML_OFFICE_REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const SHIPYARD_FE06_XML_NS='http://www.w3.org/XML/1998/namespace';
function shipyardFE06DecodeXML(text){
  if(typeof text!=='string'||/&(?!#x[0-9a-f]+;|#\d+;|amp;|lt;|gt;|quot;|apos;)/i.test(text))shipyardFE06Fail('xlsx_xml_entity_invalid');
  const decoded=text.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos);/gi,(_entity,code)=>{
    if(code==='amp')return '&';if(code==='lt')return '<';if(code==='gt')return '>';if(code==='quot')return '"';if(code==='apos')return "'";
    const n=code[1].toLowerCase()==='x'?parseInt(code.slice(2),16):parseInt(code.slice(1),10);
    if(!Number.isInteger(n)||n<=0||n>0x10ffff||(n>=0xd800&&n<=0xdfff)||(n<0x20&&![9,10,13].includes(n)))shipyardFE06Fail('xlsx_xml_entity_invalid');return String.fromCodePoint(n);
  });
  for(const char of decoded){const cp=char.codePointAt(0);if(cp===0||(cp<0x20&&![9,10,13].includes(cp))||(cp>=0xd800&&cp<=0xdfff))shipyardFE06Fail('xlsx_xml_entity_invalid');}
  return decoded;
}
// A deliberately small, bounded XML grammar for XLSX parts. DTDs, entities,
// comments, CDATA, and processing instructions are unsupported. Namespaces are
// resolved before any workbook/sheet structure is interpreted.
function shipyardFE06ParseXML(text){
  if(typeof text!=='string'||text.length>SHIPYARD_FE06_LIMITS.max_entry_bytes)shipyardFE06Fail('xlsx_xml_size_limit');
  try{shipyardValidateXmlWellFormedness(text,{maxBytes:3*1024*1024,maxDepth:80,maxNodes:60000,allowCdata:true});}
  catch(error){
    if(error?.code==='unsupported_xml_comment_or_cdata')shipyardFE06Fail('xlsx_xml_comments_unsupported');
    if(error?.code==='unsupported_xml_processing_instruction')shipyardFE06Fail('xlsx_xml_processing_instruction_unsupported');
    if(error?.code==='unsafe_xml_declaration')shipyardFE06Fail('xlsx_xml_active_content');
    if(error?.code==='xml_preflight_byte_limit_exceeded')shipyardFE06Fail('xlsx_xml_size_limit');
    if(error?.code==='xml_preflight_depth_limit_exceeded')shipyardFE06Fail('xlsx_xml_depth_limit');
    if(error?.code==='xml_preflight_node_limit_exceeded')shipyardFE06Fail('xlsx_xml_node_limit');
    shipyardFE06Fail('xlsx_xml_malformed');
  }
  if(text.charCodeAt(0)===0xfeff)text=text.slice(1);
  if(/<!--|-->/i.test(text))shipyardFE06Fail('xlsx_xml_comments_unsupported');
  if(/<!\s*(?:DOCTYPE|ENTITY)\b|\b(?:SYSTEM|PUBLIC)\s+["']/i.test(text))shipyardFE06Fail('xlsx_xml_active_content');
  const declaration=/^<\?xml\s+version=(["'])1\.0\1(?:\s+encoding=(["'])[A-Za-z][A-Za-z0-9._-]*\2)?(?:\s+standalone=(["'])(?:yes|no)\3)?\s*\?>/;
  if(text.startsWith('<?xml')){const match=text.match(declaration);if(!match)shipyardFE06Fail('xlsx_xml_processing_instruction_unsupported');text=text.slice(match[0].length);}
  if(text.includes('<?'))shipyardFE06Fail('xlsx_xml_processing_instruction_unsupported');
  const document={qname:'#document',local:'#document',uri:'',attrs:Object.create(null),children:[],text:''};
  const baseNs={xml:SHIPYARD_FE06_XML_NS},stack=[{node:document,ns:baseNs}],namePattern=/^[A-Za-z_][A-Za-z0-9_.:-]*$/;
  let i=0,nodes=0,rootClosed=false;
  const splitName=(raw,ns,isElement)=>{
    if(!namePattern.test(raw)||raw.startsWith(':')||raw.endsWith(':')||(raw.match(/:/g)||[]).length>1)shipyardFE06Fail('xlsx_xml_malformed_name');
    const parts=raw.split(':');if(parts.length===1)return {local:parts[0],uri:isElement?(ns['']||''):''};
    if(!ns[parts[0]])shipyardFE06Fail('xlsx_xml_namespace_unbound');return {local:parts[1],uri:ns[parts[0]]};
  };
  const tagEnd=start=>{let quote='';for(let j=start+1;j<text.length;j++){const c=text[j];if(quote){if(c===quote)quote='';}else if(c==='"'||c==="'")quote=c;else if(c==='>')return j;}shipyardFE06Fail('xlsx_xml_malformed_tag');};
  while(i<text.length){
    if(text.startsWith('<![CDATA[',i)){
      const parent=stack.at(-1)?.node;if(stack.length===1||parent?.uri!==SHIPYARD_FE06_XML_MAIN||!['oddFooter','evenFooter'].includes(parent.local))shipyardFE06Fail('xlsx_xml_cdata_unsupported');
      const end=text.indexOf(']]>',i+9);if(end<0)shipyardFE06Fail('xlsx_xml_cdata_unsupported');parent.text+=text.slice(i+9,end);i=end+3;continue;
    }
    if(text[i]!=='<'){
      const end=text.indexOf('<',i),stop=end<0?text.length:end,value=shipyardFE06DecodeXML(text.slice(i,stop));
      if(stack.length===1){if(value.trim())shipyardFE06Fail('xlsx_xml_text_outside_root');}else stack.at(-1).node.text+=value;
      i=stop;continue;
    }
    if(text.startsWith('<!',i)||text.startsWith('<?',i))shipyardFE06Fail('xlsx_xml_active_content');
    const end=tagEnd(i),raw=text.slice(i,end+1);i=end+1;
    if(raw.startsWith('</')){
      const match=/^<\/([A-Za-z_][A-Za-z0-9_.:-]*)\s*>$/.exec(raw);if(!match||stack.length===1||stack.at(-1).node.qname!==match[1])shipyardFE06Fail('xlsx_xml_unbalanced_tags');
      stack.pop();if(stack.length===1)rootClosed=true;continue;
    }
    const opening=/^<([A-Za-z_][A-Za-z0-9_.:-]*)([\s\S]*?)>$/.exec(raw);if(!opening)shipyardFE06Fail('xlsx_xml_malformed_tag');
    const rawName=opening[1];let tail=opening[2],selfClose=false;
    if(/\/\s*$/.test(tail)){selfClose=true;tail=tail.replace(/\/\s*$/,'');}
    if(rootClosed)shipyardFE06Fail('xlsx_xml_multiple_roots');
    const rawAttrs=[];let pos=0;
    while(pos<tail.length){
      const ws=/^\s+/.exec(tail.slice(pos));if(!ws)shipyardFE06Fail('xlsx_xml_malformed_attribute');pos+=ws[0].length;if(pos>=tail.length)break;
      const attrName=/^[A-Za-z_][A-Za-z0-9_.:-]*/.exec(tail.slice(pos));if(!attrName)shipyardFE06Fail('xlsx_xml_malformed_attribute');pos+=attrName[0].length;
      while(pos<tail.length&&/\s/.test(tail[pos]))pos++;if(tail[pos++]!=='=')shipyardFE06Fail('xlsx_xml_malformed_attribute');while(pos<tail.length&&/\s/.test(tail[pos]))pos++;
      const quote=tail[pos++];if(quote!=='"'&&quote!=="'")shipyardFE06Fail('xlsx_xml_malformed_attribute');const valueStart=pos;while(pos<tail.length&&tail[pos]!==quote){if(tail[pos]==='<')shipyardFE06Fail('xlsx_xml_malformed_attribute');pos++;}
      if(pos>=tail.length)shipyardFE06Fail('xlsx_xml_malformed_attribute');const value=shipyardFE06DecodeXML(tail.slice(valueStart,pos));pos++;
      if(rawAttrs.some(a=>a.name===attrName[0]))shipyardFE06Fail('xlsx_xml_duplicate_attribute');rawAttrs.push({name:attrName[0],value});
    }
    const ns={...stack.at(-1).ns};
    for(const a of rawAttrs){if(a.name==='xmlns')ns['']=a.value;else if(a.name.startsWith('xmlns:')){const prefix=a.name.slice(6);if(!/^[A-Za-z_][A-Za-z0-9_.-]*$/.test(prefix)||prefix==='xmlns'||!a.value||prefix==='xml'&&a.value!==SHIPYARD_FE06_XML_NS||prefix!=='xml'&&a.value===SHIPYARD_FE06_XML_NS)shipyardFE06Fail('xlsx_xml_namespace_invalid');ns[prefix]=a.value;}}
    const en=splitName(rawName,ns,true),attrs=Object.create(null);for(const a of rawAttrs){if(a.name==='xmlns'||a.name.startsWith('xmlns:'))continue;const at=splitName(a.name,ns,false),key=at.uri+'\u0000'+at.local;if(Object.hasOwn(attrs,key))shipyardFE06Fail('xlsx_xml_duplicate_attribute');attrs[key]=a.value;}
    const node={qname:rawName,local:en.local,uri:en.uri,attrs,children:[],text:''};stack.at(-1).node.children.push(node);if(++nodes>250000)shipyardFE06Fail('xlsx_xml_node_limit');
    if(!selfClose){stack.push({node,ns});if(stack.length>100)shipyardFE06Fail('xlsx_xml_depth_limit');}else if(stack.length===1)rootClosed=true;
  }
  const roots=document.children;if(roots.length!==1||stack.length!==1||!rootClosed)shipyardFE06Fail('xlsx_xml_unbalanced_tags');return roots[0];
}
function shipyardFE06XmlChildren(node,local,uri=SHIPYARD_FE06_XML_MAIN){return node?.children.filter(child=>typeof child==='object'&&child.local===local&&child.uri===uri)||[];}
function shipyardFE06XmlChild(node,local,uri=SHIPYARD_FE06_XML_MAIN,{required=false}={}){const found=shipyardFE06XmlChildren(node,local,uri);if(found.length>1)shipyardFE06Fail('xlsx_xml_duplicate_'+local);if(!found.length){if(required)shipyardFE06Fail('xlsx_xml_missing_'+local);return null;}return found[0];}
function shipyardFE06XmlAttr(node,local,uri=''){return node?.attrs?.[uri+'\u0000'+local]??null;}
function shipyardFE06XmlText(node){if(node.children.some(child=>typeof child==='object'))shipyardFE06Fail('xlsx_xml_nested_scalar');return node.text;}
function shipyardFE06SharedString(si){let out='';for(const child of si.children){if(child.local==='t'&&child.uri===SHIPYARD_FE06_XML_MAIN){out+=shipyardFE06XmlText(child);continue;}if(child.local==='r'&&child.uri===SHIPYARD_FE06_XML_MAIN){const ts=shipyardFE06XmlChildren(child,'t');if(ts.length!==1)shipyardFE06Fail('xlsx_shared_string_structure_invalid');out+=shipyardFE06XmlText(ts[0]);continue;}shipyardFE06Fail('xlsx_shared_string_structure_invalid');}return out;}
function shipyardFE06CellValue(cell,strings){
  if(!cell)return null;const type=shipyardFE06XmlAttr(cell,'t');if(shipyardFE06XmlChildren(cell,'f').length)shipyardFE06Fail('xlsx_formula_unsupported');
  const inline=shipyardFE06XmlChild(cell,'is'),values=shipyardFE06XmlChildren(cell,'v');
  if(inline){if(values.length||type!=='inlineStr')shipyardFE06Fail('xlsx_cell_structure_invalid');let out='';for(const child of inline.children){if(child.local==='t'&&child.uri===SHIPYARD_FE06_XML_MAIN)out+=shipyardFE06XmlText(child);else if(child.local==='r'&&child.uri===SHIPYARD_FE06_XML_MAIN){const ts=shipyardFE06XmlChildren(child,'t');if(ts.length!==1)shipyardFE06Fail('xlsx_cell_structure_invalid');out+=shipyardFE06XmlText(ts[0]);}else shipyardFE06Fail('xlsx_cell_structure_invalid');}return out;}
  if(values.length>1)shipyardFE06Fail('xlsx_cell_structure_invalid');if(!values.length)return null;const decoded=shipyardFE06XmlText(values[0]);
  if(type==='s'){if(!/^\d+$/.test(decoded)||Number(decoded)>=strings.length)shipyardFE06Fail('xlsx_shared_string_invalid');return strings[Number(decoded)];}
  if(type&&type!=='n'&&type!=='str')shipyardFE06Fail('xlsx_cell_type_unsupported');return decoded;
}
function shipyardFE06Decimal(input){
  if(typeof input!=='string'||input.length>48||!/^[-+]?(?:\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?$/.test(input))shipyardFE06Fail('xlsx_decimal_invalid');
  const m=/^([-+]?)(\d+)(?:\.(\d+))?(?:[eE]([-+]?\d+))?$/.exec(input),frac=m[3]||'',exp=Number(m[4]||0);if(!Number.isInteger(exp)||Math.abs(exp)>30)shipyardFE06Fail('xlsx_decimal_invalid');
  let coefficient=BigInt((m[1]==='-'?'-':'')+(m[2]+frac)),scale=frac.length-exp;
  if(scale<0){coefficient*=10n**BigInt(-scale);scale=0;}if(scale>30)shipyardFE06Fail('xlsx_decimal_scale_invalid');return {coefficient,scale};
}
function shipyardFE06Align(a,b){const scale=Math.max(a.scale,b.scale);return [{coefficient:a.coefficient*10n**BigInt(scale-a.scale),scale},{coefficient:b.coefficient*10n**BigInt(scale-b.scale),scale}];}
function shipyardFE06Mul(a,b){return {coefficient:a.coefficient*b.coefficient,scale:a.scale+b.scale};}
function shipyardFE06Sub(a,b){const [x,y]=shipyardFE06Align(a,b);return {coefficient:x.coefficient-y.coefficient,scale:x.scale};}
function shipyardFE06Scale(a,n){return {coefficient:a.coefficient*BigInt(n),scale:a.scale};}
function shipyardFE06DivideByInteger(a,n){if(!Number.isInteger(n)||n<=0)shipyardFE06Fail('decimal_divisor_invalid');let coefficient=a.coefficient,scale=a.scale;for(let i=0;i<30;i++){const divisor=BigInt(n);if(coefficient%divisor===0n)return {coefficient:coefficient/divisor,scale};coefficient*=10n;scale++;}shipyardFE06Fail('decimal_division_nonterminating');}
function shipyardFE06Num(a){return Number(a.coefficient)/10**a.scale;}
function shipyardFE06DecimalString(a){
  const negative=a.coefficient<0n,c=(negative?-a.coefficient:a.coefficient).toString(),scale=a.scale;
  if(scale===0)return (negative?'-':'')+c;const padded=c.padStart(scale+1,'0'),value=padded.slice(0,-scale)+'.'+padded.slice(-scale).replace(/0+$/,'');return (negative?'-':'')+value.replace(/\.$/,'');
}
function shipyardFE06IsoDate(value){
  if(typeof value!=='string')return null;const m=/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/.exec(value.trim());if(!m)return null;
  const months={jan:'01',feb:'02',mar:'03',apr:'04',may:'05',jun:'06',jul:'07',aug:'08',sep:'09',oct:'10',nov:'11',dec:'12'},month=months[m[2].toLowerCase()];if(!month)return null;
  const date=`${m[3]}-${month}-${m[1].padStart(2,'0')}`,ms=Date.parse(date+'T00:00:00Z');return Number.isFinite(ms)&&new Date(ms).toISOString().slice(0,10)===date?date:null;
}
function shipyardFE06NumericCell(value){if(value===null||value==='-'||value==='')return null;return shipyardFE06Decimal(value);}
async function shipyardFE06ParseWorkbook(input,expectedTicker,sourceUrl,sourceSha256,retrieval){
  const zip=await shipyardFE06ZipEntries(input),names=zip.entries;
  for(const name of names.keys())if(/(^|\/)(?:externalLinks|vbaProject|connections)(?:\/|\.|$)/i.test(name))shipyardFE06Fail('xlsx_active_content_unsupported');
  const decoder=new TextDecoder('utf-8',{fatal:true}),xmlDocs=new Map();
  // Validate every XML/relationship part before using any of its values. In
  // particular, never let tag-looking text inside comments or nested content
  // be interpreted as worksheet rows/cells.
  for(const name of names.keys())if(/\.(?:xml|rels)$/i.test(name)){
    const bytes=await zip.read(name);if(bytes.length>SHIPYARD_FE06_LIMITS.max_entry_bytes)shipyardFE06Fail('xlsx_xml_size_limit');
    xmlDocs.set(name,shipyardFE06ParseXML(decoder.decode(bytes)));
  }
  const doc=name=>{const value=xmlDocs.get(name);if(!value)shipyardFE06Fail('xlsx_expected_entry_missing');return value;};
  const workbook=doc('xl/workbook.xml');if(workbook.local!=='workbook'||workbook.uri!==SHIPYARD_FE06_XML_MAIN)shipyardFE06Fail('xlsx_sheet_identity_invalid');
  const sheets=shipyardFE06XmlChild(workbook,'sheets',SHIPYARD_FE06_XML_MAIN,{required:true}),sheetNodes=shipyardFE06XmlChildren(sheets,'sheet');
  if(sheets.children.some(child=>typeof child==='object'&&(child.local!=='sheet'||child.uri!==SHIPYARD_FE06_XML_MAIN))||sheetNodes.length!==1||shipyardFE06XmlAttr(sheetNodes[0],'name')!=='navhist'||shipyardFE06XmlAttr(sheetNodes[0],'id',SHIPYARD_FE06_XML_OFFICE_REL)!=='rId1')shipyardFE06Fail('xlsx_sheet_identity_invalid');
  const rels=doc('xl/_rels/workbook.xml.rels');if(rels.local!=='Relationships'||rels.uri!==SHIPYARD_FE06_XML_PACKAGE_REL)shipyardFE06Fail('xlsx_sheet_target_invalid');
  const relationships=rels.children.filter(child=>typeof child==='object'&&child.uri===SHIPYARD_FE06_XML_PACKAGE_REL&&child.local==='Relationship');
  if(rels.children.some(child=>typeof child==='object'&&(child.uri!==SHIPYARD_FE06_XML_PACKAGE_REL||child.local!=='Relationship')))shipyardFE06Fail('xlsx_sheet_target_invalid');
  const targetRels=relationships.filter(row=>shipyardFE06XmlAttr(row,'Id')==='rId1');
  if(targetRels.length!==1||shipyardFE06XmlAttr(targetRels[0],'Target')!=='worksheets/sheet1.xml'||shipyardFE06XmlAttr(targetRels[0],'TargetMode')==='External'||shipyardFE06XmlAttr(targetRels[0],'Type')!==SHIPYARD_FE06_XML_OFFICE_REL+'/worksheet')shipyardFE06Fail('xlsx_sheet_target_invalid');
  const ss=doc('xl/sharedStrings.xml');if(ss.local!=='sst'||ss.uri!==SHIPYARD_FE06_XML_MAIN)shipyardFE06Fail('xlsx_shared_string_structure_invalid');
  const siNodes=shipyardFE06XmlChildren(ss,'si');if(ss.children.some(child=>typeof child==='object'&&(child.uri!==SHIPYARD_FE06_XML_MAIN||child.local!=='si'))||siNodes.length>SHIPYARD_FE06_LIMITS.max_shared_strings)shipyardFE06Fail('xlsx_shared_string_count_limit');
  const strings=siNodes.map(si=>{const value=shipyardFE06SharedString(si);if(value.length>SHIPYARD_FE06_LIMITS.max_string_chars)shipyardFE06Fail('xlsx_shared_string_size_limit');return value;});
  const sheet=doc('xl/worksheets/sheet1.xml');if(sheet.local!=='worksheet'||sheet.uri!==SHIPYARD_FE06_XML_MAIN)shipyardFE06Fail('xlsx_sheet_identity_invalid');
  const dataNode=shipyardFE06XmlChild(sheet,'sheetData',SHIPYARD_FE06_XML_MAIN,{required:true});
  if(sheet.children.some(child=>typeof child==='object'&&(child.local==='sheetData'&&child.uri!==SHIPYARD_FE06_XML_MAIN)))shipyardFE06Fail('xlsx_sheetdata_missing');
  const rowNodes=shipyardFE06XmlChildren(dataNode,'row');if(dataNode.children.some(child=>typeof child==='object'&&(child.uri!==SHIPYARD_FE06_XML_MAIN||child.local!=='row')))shipyardFE06Fail('xlsx_sheetdata_structure_invalid');
  if(rowNodes.length>SHIPYARD_FE06_LIMITS.max_rows)shipyardFE06Fail('xlsx_row_limit');
  const rows=[];let previousDate='';const seen=new Set(),seenRowNumbers=new Set();let header=false,ticker='',previousRowNo=0;
  for(const rowNode of rowNodes){
    const rowNo=Number(shipyardFE06XmlAttr(rowNode,'r'));if(!Number.isInteger(rowNo)||rowNo<1||rowNo<=previousRowNo||seenRowNumbers.has(rowNo))shipyardFE06Fail('xlsx_row_index_invalid');previousRowNo=rowNo;seenRowNumbers.add(rowNo);
    const cellNodes=shipyardFE06XmlChildren(rowNode,'c');if(rowNode.children.some(child=>typeof child==='object'&&(child.uri!==SHIPYARD_FE06_XML_MAIN||child.local!=='c')))shipyardFE06Fail('xlsx_row_structure_invalid');
    const cells=new Map();for(const cell of cellNodes){
      const ref=shipyardFE06XmlAttr(cell,'r'),match=typeof ref==='string'?/^([A-Z]+)(\d+)$/.exec(ref):null;if(!match||Number(match[2])!==rowNo)shipyardFE06Fail('xlsx_cell_ref_invalid');
      const col=match[1];if(cells.has(col))shipyardFE06Fail('xlsx_duplicate_cell');cells.set(col,cell);
      if(shipyardFE06XmlChildren(cell,'f').length)shipyardFE06Fail('xlsx_formula_unsupported');
      if(cell.children.some(child=>typeof child==='object'&&(child.uri!==SHIPYARD_FE06_XML_MAIN||!['v','is','f'].includes(child.local))))shipyardFE06Fail('xlsx_cell_structure_invalid');
    }
    if(rowNo===2){ticker=shipyardFE06CellValue(cells.get('B'),strings);continue;}
    if(rowNo===4){const h=['A','B','C','D'].map(c=>shipyardFE06CellValue(cells.get(c),strings));if(h.join('|')!=='Date|NAV|Shares Outstanding|Total Net Assets')shipyardFE06Fail('xlsx_header_invalid');header=true;continue;}
    if(rowNo<5)continue;
    const date=shipyardFE06IsoDate(shipyardFE06CellValue(cells.get('A'),strings));if(!date)continue;
    if(seen.has(date)||(previousDate&&date>=previousDate))shipyardFE06Fail('xlsx_duplicate_or_unsorted_date');seen.add(date);previousDate=date;
    const nav=shipyardFE06NumericCell(shipyardFE06CellValue(cells.get('B'),strings)),shares=shipyardFE06NumericCell(shipyardFE06CellValue(cells.get('C'),strings)),assets=shipyardFE06NumericCell(shipyardFE06CellValue(cells.get('D'),strings));
    let quality='complete';if(!nav||!shares||!assets)quality='missing_required_value';
    else if(shipyardFE06Num(nav)<=0||shipyardFE06Num(shares)<=0||shipyardFE06Num(assets)<=0)quality='nonpositive_required_value';
    else {const residual=shipyardFE06Num(shipyardFE06Sub(shipyardFE06Mul(nav,shares),assets))/shipyardFE06Num(assets);if(!Number.isFinite(residual)||Math.abs(residual)>SHIPYARD_FE06_POLICY.asset_reconciliation_tolerance)quality='asset_reconciliation_breach';}
    rows.push({date,source_row:rowNo,nav,shares,assets,quality});
  }
  if(!header||ticker!==expectedTicker||rows.length<SHIPYARD_FE06_POLICY.session_count)shipyardFE06Fail('xlsx_issuer_or_coverage_invalid');
  return {ticker,isin:SHIPYARD_FE06_SOURCES[expectedTicker].isin,source_url:sourceUrl,source_sha256:sourceSha256,bytes:input.byteLength??input.length,retrieval,rows};
}
function shipyardFE06Mean(values){if(!values.length||values.some(x=>!Number.isFinite(x)))shipyardFE06Fail('feature_window_invalid');return values.reduce((a,b)=>a+b,0)/values.length;}
function shipyardFE06SampleSD(values){if(values.length<2||values.some(x=>!Number.isFinite(x)))shipyardFE06Fail('feature_window_invalid');const mean=shipyardFE06Mean(values);return Math.sqrt(values.reduce((s,x)=>s+(x-mean)**2,0)/(values.length-1));}
function shipyardFE06Z(value,history){const mean=shipyardFE06Mean(history),sd=shipyardFE06SampleSD(history);if(!(sd>0)&&Number.isFinite(sd))shipyardFE06Fail('zero_baseline_variance');if(!Number.isFinite(sd)||sd<=0)shipyardFE06Fail('zero_baseline_variance');return {z:(value-mean)/sd,mean,sd};}
function shipyardFE06SplitRatio(ticker,date){const action=SHIPYARD_FE06_SPLITS[date];return action&&action.tickers.includes(ticker)?action.ratio_new_per_old:1;}
function shipyardFE06CheckSplitSignature(ticker,current,previous,ratio){
  if(ratio!==1)return;
  const currentShares=shipyardFE06Num(current.shares),previousShares=shipyardFE06Num(previous.shares),priceRatio=shipyardFE06Num(current.nav)/shipyardFE06Num(previous.nav),shareRatio=currentShares/previousShares;
  if(!Number.isFinite(shareRatio)||!Number.isFinite(priceRatio))shipyardFE06Fail('unsupported_share_basis_change');
  const candidates=SHIPYARD_FE06_POLICY.unsupported_split_signature_ratios.flatMap(value=>[value,1/value]);
  const tolerance=SHIPYARD_FE06_POLICY.unsupported_split_signature_tolerance;
  for(const expectedShares of candidates){
    const expectedPrice=1/expectedShares;
    if(Math.abs(shareRatio/expectedShares-1)<=tolerance&&Math.abs(priceRatio/expectedPrice-1)<=tolerance)shipyardFE06Fail('unsupported_share_basis_change');
  }
}
function shipyardFE06DailyReturn(ticker,current,previous){
  const ratio=shipyardFE06SplitRatio(ticker,current.date);shipyardFE06CheckSplitSignature(ticker,current,previous,ratio);
  const prevNav=shipyardFE06Num(previous.nav)/ratio,ret=shipyardFE06Num(current.nav)/prevNav-1;if(!Number.isFinite(ret))shipyardFE06Fail('price_return_invalid');return ret;
}
function shipyardFE06RankZ(values){
  if(values.length!==SHIPYARD_FE06_UNIVERSE.length||values.some(v=>!Number.isFinite(v)))shipyardFE06Fail('momentum_universe_incomplete');
  const sorted=values.map((value,index)=>({value,index})).sort((a,b)=>a.value-b.value||a.index-b.index),ranks=Array(values.length);let i=0;
  while(i<sorted.length){let j=i+1;while(j<sorted.length&&sorted[j].value===sorted[i].value)j++;const avgRank=((i+1)+j)/2;for(let k=i;k<j;k++)ranks[sorted[k].index]=avgRank;i=j;}
  const mean=shipyardFE06Mean(ranks),sd=shipyardFE06SampleSD(ranks);if(!Number.isFinite(sd)||sd<=0)shipyardFE06Fail('zero_rank_dispersion');return {z:(ranks.map(r=>(r-mean)/sd)),ranks,mean,sd};
}
function shipyardFE06Derive(rowsByTicker,sessions,nowMs,receipts,targetTicker){
  const allDates=SHIPYARD_FE06_UNIVERSE.map(({ticker})=>new Set(rowsByTicker[ticker].rows.map(r=>r.date)));
  const common=[...allDates[0]].filter(date=>allDates.every(set=>set.has(date))).sort();if(common.length<SHIPYARD_FE06_POLICY.session_count)shipyardFE06Fail('common_session_coverage_short');
  const grid=common.slice(-SHIPYARD_FE06_POLICY.session_count),cutoff=grid.at(-1);
  for(const {ticker} of SHIPYARD_FE06_UNIVERSE)if(rowsByTicker[ticker].rows.at(0)?.date!==cutoff)shipyardFE06Fail('issuer_cutoff_mismatch');
  const calendar=sessions.filter(s=>s.date<=cutoff);const expected=calendar.slice(-SHIPYARD_FE06_POLICY.session_count).map(s=>s.date);
  if(expected.length!==SHIPYARD_FE06_POLICY.session_count||expected.some((date,i)=>date!==grid[i]))shipyardFE06Fail('official_calendar_mismatch');
  const dateIndex=new Map(grid.map((d,i)=>[d,i])),data={};
  for(const {ticker} of SHIPYARD_FE06_UNIVERSE){const byDate=new Map(rowsByTicker[ticker].rows.map(r=>[r.date,r]));data[ticker]=grid.map(date=>{
    const row=byDate.get(date);if(!row||row.quality!=='complete')shipyardFE06Fail('invalid_window_row:'+ticker+':'+date+':'+(row?.quality||'missing'));return row;
  });}
  const closeSession=sessions.find(s=>s.date===cutoff);if(!closeSession)shipyardFE06Fail('source_clock_session_missing');
  const observedAt=Date.parse(closeSession.close),expiry=observedAt+SHIPYARD_FE06_POLICY.max_age_seconds*1000,age=(nowMs-observedAt)/1000;
  if(!Number.isFinite(observedAt)||age<0)shipyardFE06Fail('future_source_timestamp');if(nowMs>=expiry)shipyardFE06Fail('source_data_stale');
  const latestCompleted=sessions.filter(s=>Date.parse(s.close)<=nowMs).at(-1);if(!latestCompleted)shipyardFE06Fail('latest_market_session_missing');
  const issuerLagSessions=sessions.filter(s=>s.date>cutoff&&s.date<=latestCompleted.date).length;
  const dailyDispersion=[],flowByTicker={},fundRows={};
  for(const {ticker,isin} of SHIPYARD_FE06_UNIVERSE){
    const fund=data[ticker],flows=[],returns=[];
    for(let i=1;i<fund.length;i++){
      const current=fund[i],previous=fund[i-1],ratio=shipyardFE06SplitRatio(ticker,current.date);shipyardFE06CheckSplitSignature(ticker,current,previous,ratio);
      const flowUsd=shipyardFE06Mul(current.nav,shipyardFE06Sub(current.shares,shipyardFE06Scale(previous.shares,ratio)));
      const normalized=shipyardFE06Num(flowUsd)/shipyardFE06Num(previous.assets);if(!Number.isFinite(normalized))shipyardFE06Fail('flow_normalization_invalid');
      flows.push(normalized);returns.push(shipyardFE06DailyReturn(ticker,current,previous));
    }
    const baseline=flows.slice(0,SHIPYARD_FE06_POLICY.flow_baseline_sessions),currentFlow=flows.at(-1),flowNorm=shipyardFE06Z(currentFlow,baseline),splitIntervals=[];
    for(let i=1;i<fund.length;i++){const eventRatio=shipyardFE06SplitRatio(ticker,fund[i].date);if(eventRatio===1)continue;const before=fund[i-1],after=fund[i],prevNavCurrentBasis=shipyardFE06DivideByInteger(before.nav,eventRatio),prevSharesCurrentBasis=shipyardFE06Scale(before.shares,eventRatio),rawPrevProduct=shipyardFE06Mul(before.nav,before.shares),adjustedPrevProduct=shipyardFE06Mul(prevNavCurrentBasis,prevSharesCurrentBasis);
      if(shipyardFE06DecimalString(rawPrevProduct)!==shipyardFE06DecimalString(adjustedPrevProduct))shipyardFE06Fail('corporate_action_aum_invariance_failed');
      splitIntervals.push({effective_date:after.date,ratio_new_per_old:eventRatio,source_previous_row:before.source_row,source_current_row:after.source_row,
        raw_previous_nav:shipyardFE06DecimalString(before.nav),raw_previous_shares:shipyardFE06DecimalString(before.shares),
        transformed_previous_nav:shipyardFE06DecimalString(prevNavCurrentBasis),transformed_previous_shares:shipyardFE06DecimalString(prevSharesCurrentBasis),
        previous_assets:shipyardFE06DecimalString(before.assets),previous_product_invariant_exact:true});
    }
    const ratio=shipyardFE06SplitRatio(ticker,cutoff),cur=fund.at(-1),prev=fund.at(-2);
    const exactFlow=shipyardFE06Mul(cur.nav,shipyardFE06Sub(cur.shares,shipyardFE06Scale(prev.shares,ratio)));
    const currentDailyReturn=returns.at(-1);
    flowByTicker[ticker]={z:flowNorm.z,current_normalized_flow:currentFlow,current_flow_usd:shipyardFE06DecimalString(exactFlow),
      baseline_mean:flowNorm.mean,baseline_sample_sd:flowNorm.sd,baseline_count:baseline.length,
      baseline_start:fund[1].date,baseline_end:fund.at(-2).date,split_ratio:ratio};
    fundRows[ticker]={ticker,isin,source_url:rowsByTicker[ticker].source_url,source_sha256:rowsByTicker[ticker].source_sha256,
      bytes:rowsByTicker[ticker].bytes,current:{date:cur.date,source_row:cur.source_row,nav:shipyardFE06DecimalString(cur.nav),shares:shipyardFE06DecimalString(cur.shares),assets:shipyardFE06DecimalString(cur.assets)},
      prior:{date:prev.date,source_row:prev.source_row,nav:shipyardFE06DecimalString(prev.nav),shares:shipyardFE06DecimalString(prev.shares),assets:shipyardFE06DecimalString(prev.assets)},
      flow:{...flowByTicker[ticker],split_action_intervals:splitIntervals},current_dividend_excluded_daily_return:currentDailyReturn,
      quality_exclusions:{rows_before_scored_window:rowsByTicker[ticker].rows.filter(row=>row.date<grid[0]).length,
        invalid_rows_before_scored_window:rowsByTicker[ticker].rows.filter(row=>row.date<grid[0]&&row.quality!=='complete').length,
        reasons:Object.fromEntries([...new Set(rowsByTicker[ticker].rows.filter(row=>row.date<grid[0]&&row.quality!=='complete').map(row=>row.quality))].map(reason=>[reason,rowsByTicker[ticker].rows.filter(row=>row.date<grid[0]&&row.quality===reason).length]))},
      publication_at:null,first_seen_at:rowsByTicker[ticker].retrieval.started_at};
  }
  for(let i=1;i<data[SHIPYARD_FE06_UNIVERSE[0].ticker].length;i++){
    const cross=SHIPYARD_FE06_UNIVERSE.map(({ticker})=>shipyardFE06DailyReturn(ticker,data[ticker][i],data[ticker][i-1]));dailyDispersion.push(shipyardFE06SampleSD(cross));
  }
  const dispersionHistory=dailyDispersion.slice(0,SHIPYARD_FE06_POLICY.flow_baseline_sessions),dispersionCurrent=dailyDispersion.at(-1),dispersion=shipyardFE06Z(dispersionCurrent,dispersionHistory);
  const momentumReturns=SHIPYARD_FE06_UNIVERSE.map(({ticker})=>{
    const fund=data[ticker],anchor=fund[fund.length-1-SHIPYARD_FE06_POLICY.momentum_lookback_sessions];let factor=1;
    for(let i=fund.length-SHIPYARD_FE06_POLICY.momentum_lookback_sessions;i<fund.length;i++)factor*=shipyardFE06SplitRatio(ticker,fund[i].date);
    return shipyardFE06Num(fund.at(-1).nav)/(shipyardFE06Num(anchor.nav)/factor)-1;
  });
  const targetIndex=SHIPYARD_FE06_UNIVERSE.findIndex(({ticker})=>ticker===targetTicker);if(targetIndex<0)shipyardFE06Fail('target_sector_not_allowlisted');
  const rank=shipyardFE06RankZ(momentumReturns),leadershipBreadth=momentumReturns.filter(x=>x>0).length/momentumReturns.length;
  const features={sector_momentum_rank_z:rank.z[targetIndex],leadership_breadth:leadershipBreadth,sector_dispersion_z:dispersion.z,sector_flow_z:flowByTicker[targetTicker].z};
  if(Object.values(features).some(x=>!Number.isFinite(x)))shipyardFE06Fail('feature_nonfinite');
  return {schema:'SHIPYARD_FE06_SOURCE_FORECAST_V1',status:'computed',engine_id:'FE06',feature_origin:'official_issuer_workbooks_new_derived_policy',feature_policy:SHIPYARD_FE06_POLICY,
    target_sector_symbol:targetTicker,features,coverage:{fixed_universe_size:SHIPYARD_FE06_UNIVERSE.length,complete_funds:Object.keys(data).length,session_count:grid.length,common_cutoff:cutoff,
      window_start:grid[0],window_end:grid.at(-1),official_calendar_sessions_matched:expected.length,missing_sessions:[],unexpected_sessions:[],
      flow_baseline_observations:SHIPYARD_FE06_POLICY.flow_baseline_sessions,dispersion_baseline_observations:dispersionHistory.length},
    source:{issuer:'State Street Global Advisors',clock_source:'SEC 2026 Select Sector SPDR Trust SAI; NAV determined at regular NYSE close',calendar_provider:'Alpaca US equity market calendar',timezone:'America/New_York',
      observed_at:closeSession.close,publication_at:null,first_seen_at:receipts.issuer_first_seen_at,source_age_seconds:age,
      latest_completed_market_session:latestCompleted.date,issuer_lag_sessions:issuerLagSessions,
      source_cutoff_rule:'Latest common issuer NAV date within the 48-hour semantic-close bound; may lag the latest official market session; never filled or relabeled.',
      freshness_expires_at:new Date(expiry).toISOString(),historical_availability:'unknown; current retrieval of historical rows does not establish historical vintages',
      source_receipts:receipts.workbooks,corporate_actions:[{effective_date:'2025-12-05',ratio_new_per_old:2,tickers:SHIPYARD_FE06_SPLITS['2025-12-05'].tickers,source_url:SHIPYARD_FE06_SPLITS['2025-12-05'].source}],
      source_rows:fundRows,momentum_returns:Object.fromEntries(SHIPYARD_FE06_UNIVERSE.map(({ticker},i)=>[ticker,momentumReturns[i]])),
      momentum_ranks:Object.fromEntries(SHIPYARD_FE06_UNIVERSE.map(({ticker},i)=>[ticker,rank.ranks[i]])),
      momentum_rank_z_by_ticker:Object.fromEntries(SHIPYARD_FE06_UNIVERSE.map(({ticker},i)=>[ticker,rank.z[i]])),
      dispersion:{current:dispersionCurrent,prior_mean:dispersion.mean,prior_sample_sd:dispersion.sd,baseline_start:grid[1],baseline_end:grid.at(-2),baseline_count:dispersionHistory.length},
      selection:'Fixed current plain Select Sector SPDR ETFs; no Premium Income variants; no historical membership assertion'},
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,calibrated_probability:null,
      observed_vendor_flow:false,volume_substituted:false,aum_change_substituted:false,redistribution_rights_established:false,historical_point_in_time_claim:false,
      exact_original_scorer_unchanged:true,source_downloads_bounded:true},freshness:{max_age_seconds:SHIPYARD_FE06_POLICY.max_age_seconds,status:'fresh_at_semantic_close'},
  };
}
async function shipyardFE06BoundedBytes(response,limit){
  if(!response?.ok||response.redirected)shipyardFE06Fail('source_http_unavailable');
  const header=response.headers?.get('content-length');if(header&&(!/^\d+$/.test(header)||Number(header)>limit))shipyardFE06Fail('source_body_size_limit');
  const reader=response.body?.getReader();if(!reader)shipyardFE06Fail('source_body_missing');const chunks=[];let size=0;
  try{for(;;){const part=await reader.read();if(part.done)break;size+=part.value.length;if(size>limit)shipyardFE06Fail('source_body_size_limit');chunks.push(part.value);}}
  finally{try{reader.releaseLock();}catch{}}
  const out=new Uint8Array(size);let offset=0;for(const part of chunks){out.set(part,offset);offset+=part.length;}return out;
}
async function shipyardFE06Hash(bytes){const hash=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');}
function shipyardFE06DateAt(ms){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ms));}
async function shipyardFE06GetCalendar(request,env,started,deadline){
  const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)shipyardFE06Fail('market_calendar_credentials_unavailable');
  const startDate=new Date(started-SHIPYARD_FE06_LIMITS.calendar_lookback_days*86400000).toISOString().slice(0,10),endDate=shipyardFE06DateAt(started),url=new URL('https://paper-api.alpaca.markets/v2/calendar');url.searchParams.set('start',startDate);url.searchParams.set('end',endDate);
  const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(SHIPYARD_FE06_LIMITS.request_timeout_ms)])});
  const bytes=await shipyardFE06BoundedBytes(response,SHIPYARD_FE06_LIMITS.max_calendar_bytes);let rows;try{rows=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}catch{shipyardFE06Fail('market_calendar_schema_invalid');}
  if(!Array.isArray(rows)||rows.length>SHIPYARD_FE06_LIMITS.max_calendar_rows)shipyardFE06Fail('market_calendar_schema_invalid');let previous='';
  const sessions=rows.map(row=>{
    if(!row||!shipyardCalendarDate(row.date)||row.date<startDate||row.date>endDate||row.date<=previous||typeof row.open!=='string'||typeof row.close!=='string'||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)shipyardFE06Fail('market_calendar_schema_invalid');previous=row.date;
    const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close);if(Date.parse(close)<=Date.parse(open))shipyardFE06Fail('market_calendar_schema_invalid');return {date:row.date,open,close,open_local:row.open,close_local:row.close};
  });
  if(Date.now()>=deadline)shipyardFE06Fail('acquisition_deadline_exceeded');return {sessions,source_url:url.origin+url.pathname+'?start='+startDate+'&end='+endDate,received_at:new Date().toISOString(),sha256:await shipyardFE06Hash(bytes),bytes:bytes.length};
}
async function shipyardFE06AcquireResponse(request,args,env){
  const started=Date.now(),deadline=started+SHIPYARD_FE06_LIMITS.total_timeout_ms,base={schema:'SHIPYARD_FE06_SOURCE_FORECAST_V1',engine_id:'FE06',feature_origin:'official_issuer_workbooks_new_derived_policy',feature_policy:SHIPYARD_FE06_POLICY,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,redistribution_rights_established:false,observed_vendor_flow:false}};
  if(!args||Object.keys(args).length!==2||args.engine_id!=='FE06'||!SHIPYARD_FE06_UNIVERSE.some(x=>x.ticker===args.symbol))return json({...base,status:'invalid',error:'invalid_arguments'},400);
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  let usedBytes=0;const receipts=[],rowsByTicker={};
  try{
    const calendar=await shipyardFE06GetCalendar(request,env,started,deadline),queue=[...SHIPYARD_FE06_UNIVERSE];usedBytes=calendar.bytes;
    const workers=Array.from({length:2},async()=>{while(queue.length){shipyardFE06CheckAbort(request);if(Date.now()>=deadline)shipyardFE06Fail('acquisition_deadline_exceeded');const {ticker}=queue.shift(),meta=SHIPYARD_FE06_SOURCES[ticker],captureStarted=new Date().toISOString();
      const response=await fetch(meta.url,{method:'GET',headers:{accept:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream'},redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(SHIPYARD_FE06_LIMITS.request_timeout_ms)])});
      const bytes=await shipyardFE06BoundedBytes(response,SHIPYARD_FE06_LIMITS.max_workbook_bytes);usedBytes+=bytes.length;if(usedBytes>SHIPYARD_FE06_LIMITS.max_total_response_bytes)shipyardFE06Fail('total_source_budget_exceeded');
      const hash=await shipyardFE06Hash(bytes),retrieval={started_at:captureStarted,completed_at:new Date().toISOString()};rowsByTicker[ticker]=await shipyardFE06ParseWorkbook(bytes,ticker,meta.url,hash,retrieval);
      receipts.push({ticker,isin:meta.isin,source_url:meta.url,retrieved_at_start:retrieval.started_at,retrieved_at_end:retrieval.completed_at,bytes:bytes.length,sha256:hash,source_rows:rowsByTicker[ticker].rows.length});
    }});
    await Promise.all(workers);if(receipts.length!==SHIPYARD_FE06_UNIVERSE.length||receipts.length+1>SHIPYARD_FE06_LIMITS.max_requests)shipyardFE06Fail('source_request_budget_exceeded');
    const firstSeen=receipts.map(x=>Date.parse(x.retrieved_at_start)).sort((a,b)=>a-b)[0],receipt={issuer_first_seen_at:new Date(firstSeen).toISOString(),workbooks:receipts.sort((a,b)=>SHIPYARD_FE06_UNIVERSE.findIndex(x=>x.ticker===a.ticker)-SHIPYARD_FE06_UNIVERSE.findIndex(x=>x.ticker===b.ticker))};
    const value=shipyardFE06Derive(rowsByTicker,calendar.sessions,Date.now(),receipt,args.symbol),computedAt=Date.now();if(request.signal.aborted)shipyardFE06Fail('cancelled');if(computedAt>=deadline)shipyardFE06Fail('acquisition_deadline_exceeded');
    value.computed_at=new Date(computedAt).toISOString();value.acquisition={request_count:receipts.length+1,request_bound:SHIPYARD_FE06_LIMITS.max_requests,concurrency_bound:2,
      response_bytes:usedBytes,source_bytes_bound:SHIPYARD_FE06_LIMITS.max_total_response_bytes,elapsed_ms:computedAt-started,deadline_ms:SHIPYARD_FE06_LIMITS.total_timeout_ms,
      calendar_receipt:{source_url:calendar.source_url,received_at:calendar.received_at,response_sha256:calendar.sha256,session_count:calendar.sessions.length,
        latest_completed_session:calendar.sessions.filter(row=>Date.parse(row.close)<=computedAt).at(-1)?.date??null}};value.scorer_method='unchanged Silicon FE06 numeric scorer';
    value.calculator_result=SHIPYARD_FORECAST_LOGIC.evaluateForecastEngine('FE06',value.features);
    if(new TextEncoder().encode(JSON.stringify(value)).length>48*1024)shipyardFE06Fail('feature_response_size_limit');return researchResponse(value);
  }catch(error){const known=['cancelled','market_calendar_credentials_unavailable','source_http_unavailable','source_body_size_limit','source_body_missing','source_schema_invalid','market_calendar_schema_invalid','xlsx_compressed_size_limit','xlsx_zip_directory_missing','xlsx_zip_layout_invalid','xlsx_zip_feature_unsupported','xlsx_zip_path_invalid','xlsx_uncompressed_size_limit','xlsx_entry_size_limit','xlsx_entry_size_mismatch','xlsx_entry_crc_mismatch','xlsx_local_header_invalid','xlsx_entry_out_of_bounds','xlsx_active_content_unsupported','xlsx_xml_active_content','xlsx_xml_entity_invalid','xlsx_xml_comments_unsupported','xlsx_xml_cdata_unsupported','xlsx_xml_processing_instruction_unsupported','xlsx_xml_namespace_unbound','xlsx_xml_namespace_invalid','xlsx_xml_malformed_name','xlsx_xml_malformed_tag','xlsx_xml_malformed_attribute','xlsx_xml_duplicate_attribute','xlsx_xml_unbalanced_tags','xlsx_xml_multiple_roots','xlsx_xml_text_outside_root','xlsx_xml_size_limit','xlsx_xml_node_limit','xlsx_xml_depth_limit','xlsx_xml_nested_scalar','xlsx_xml_duplicate_sheetData','xlsx_xml_missing_sheetData','xlsx_shared_string_structure_invalid','xlsx_cell_structure_invalid','xlsx_cell_type_unsupported','xlsx_row_structure_invalid','xlsx_sheetdata_structure_invalid','xlsx_expected_entry_missing','xlsx_sheet_identity_invalid','xlsx_sheet_target_invalid','xlsx_shared_string_count_limit','xlsx_shared_string_size_limit','xlsx_row_limit','xlsx_formula_unsupported','xlsx_sheetdata_missing','xlsx_header_invalid','xlsx_row_index_invalid','xlsx_cell_ref_invalid','xlsx_duplicate_cell','xlsx_decimal_invalid','xlsx_decimal_scale_invalid','xlsx_duplicate_or_unsorted_date','xlsx_issuer_or_coverage_invalid','common_session_coverage_short','issuer_cutoff_mismatch','official_calendar_mismatch','invalid_window_row','source_clock_session_missing','future_source_timestamp','source_data_stale','zero_baseline_variance','zero_rank_dispersion','unsupported_share_basis_change','corporate_action_aum_invariance_failed','acquisition_deadline_exceeded','total_source_budget_exceeded','source_request_budget_exceeded','feature_response_size_limit'];
    const code=known.find(item=>error?.code===item||String(error?.message||'').startsWith(item))||'source_acquisition_failed';return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:receipts,computed_at:new Date().toISOString(),acquisition:{request_bound:SHIPYARD_FE06_LIMITS.max_requests,elapsed_ms:Date.now()-started}},code==='cancelled'?408:503);
  }
}

function shipyardFE06ClientKey(request){
  const raw=request?.headers?.get?.('cf-connecting-ip')?.trim()||'';
  return raw&&raw.length<=64&&!/[\s,]/.test(raw)?raw:'__unknown_client__';
}
function shipyardFE06ChargeRate(map,client,nowMs,maxCount){
  for(const [key,row] of map)if(nowMs-row.started_at>=SHIPYARD_FE06_INGRESS.window_ms)map.delete(key);
  let row=map.get(client);if(!row||nowMs-row.started_at>=SHIPYARD_FE06_INGRESS.window_ms){row={started_at:nowMs,count:0};map.set(client,row);}
  if(row.count>=maxCount)return false;row.count++;
  while(map.size>SHIPYARD_FE06_INGRESS.max_tracked_ips){const oldest=[...map].sort((a,b)=>a[1].started_at-b[1].started_at)[0];if(!oldest)break;map.delete(oldest[0]);}
  return true;
}
function shipyardFE06ChargeIngress(request,nowMs){return shipyardFE06ChargeRate(SHIPYARD_FE06_RUNTIME.ingressRates,shipyardFE06ClientKey(request),nowMs,SHIPYARD_FE06_INGRESS.max_ingress_requests_per_ip);}
function shipyardFE06ChargeColdAcquisition(request,nowMs){return shipyardFE06ChargeRate(SHIPYARD_FE06_RUNTIME.coldRates,shipyardFE06ClientKey(request),nowMs,SHIPYARD_FE06_INGRESS.max_cold_acquisitions_per_ip);}
function shipyardFE06NextNYMidnight(nowMs){
  const date=shipyardFE06DateAt(nowMs),next=new Date(date+'T00:00:00Z');next.setUTCDate(next.getUTCDate()+1);
  return Date.parse(shipyardCalendarBoundary(next.toISOString().slice(0,10),'00:00'));
}
function shipyardFE06CacheKey(nowMs){
  const panel=SHIPYARD_FE06_UNIVERSE.map(row=>row.ticker+':'+row.isin).join(',');
  return [SHIPYARD_FE06_POLICY_SHA256,panel,JSON.stringify(SHIPYARD_FE06_SPLITS),shipyardFE06DateAt(nowMs)].join('|');
}
function shipyardFE06CacheGet(key,nowMs){
  const entry=SHIPYARD_FE06_RUNTIME.cache.get(key);if(!entry)return null;
  if(entry.expires_at<=nowMs||entry.ny_date!==shipyardFE06DateAt(nowMs)){SHIPYARD_FE06_RUNTIME.cache.delete(key);return null;}
  let value;try{value=JSON.parse(entry.json);}catch{SHIPYARD_FE06_RUNTIME.cache.delete(key);return null;}
  const sourceExpiry=Date.parse(value?.source?.freshness_expires_at),observed=Date.parse(value?.source?.observed_at);
  if(!Number.isFinite(sourceExpiry)||!Number.isFinite(observed)||nowMs<observed||nowMs>=sourceExpiry){SHIPYARD_FE06_RUNTIME.cache.delete(key);return null;}
  return {value,expires_at:entry.expires_at,size_bytes:entry.size_bytes};
}
function shipyardFE06CachePut(key,value,nowMs){
  if(value?.status!=='computed'||!value?.source?.observed_at)return;
  const sourceExpiry=Date.parse(value.source.freshness_expires_at),nyBoundary=shipyardFE06NextNYMidnight(nowMs),expiresAt=Math.min(nowMs+SHIPYARD_FE06_INGRESS.cache_ttl_ms,sourceExpiry,nyBoundary);
  if(!Number.isFinite(expiresAt)||expiresAt<=nowMs)return;
  const serialized=JSON.stringify(value),sizeBytes=new TextEncoder().encode(serialized).length;if(sizeBytes>SHIPYARD_FE06_INGRESS.max_cache_bytes)return;
  const cache=SHIPYARD_FE06_RUNTIME.cache;cache.set(key,{json:serialized,size_bytes:sizeBytes,expires_at:expiresAt,stored_at:nowMs,ny_date:shipyardFE06DateAt(nowMs)});
  const totalBytes=()=>[...cache.values()].reduce((sum,entry)=>sum+entry.size_bytes,0);
  while(cache.size>SHIPYARD_FE06_INGRESS.max_cache_entries||totalBytes()>SHIPYARD_FE06_INGRESS.max_cache_bytes){const oldest=[...cache].sort((a,b)=>a[1].stored_at-b[1].stored_at)[0];if(!oldest)break;cache.delete(oldest[0]);}
}
function shipyardFE06ProjectTarget(sourceValue,target,nowMs,cacheStatus,cacheExpiresAt){
  const value=JSON.parse(JSON.stringify(sourceValue)),rankZ=value.source?.momentum_rank_z_by_ticker?.[target],flowZ=value.source?.source_rows?.[target]?.flow?.z;
  if(!Number.isFinite(rankZ)||!Number.isFinite(flowZ))shipyardFE06Fail('cache_projection_unavailable');
  value.target_sector_symbol=target;value.features={sector_momentum_rank_z:rankZ,leadership_breadth:value.features.leadership_breadth,sector_dispersion_z:value.features.sector_dispersion_z,sector_flow_z:flowZ};
  const observed=Date.parse(value.source.observed_at),expiry=Date.parse(value.source.freshness_expires_at),age=(nowMs-observed)/1000;
  if(!Number.isFinite(age)||age<0||nowMs>=expiry)shipyardFE06Fail('source_data_stale');
  value.source.source_age_seconds=age;value.computed_at=new Date(nowMs).toISOString();
  value.calculator_result=SHIPYARD_FORECAST_LOGIC.evaluateForecastEngine('FE06',value.features);
  value.source_cache={status:cacheStatus,provider_requests_this_call:cacheStatus==='miss'?value.acquisition.request_count:0,
    source_capture_request_count:value.acquisition.request_count,source_observed_at:value.source.observed_at,source_first_seen_at:value.source.first_seen_at,
    expires_at:new Date(cacheExpiresAt).toISOString(),stored_result_bytes:null,raw_workbooks_cached:false};
  return value;
}
async function shipyardForecastFE06(request,args,env){
  const base={schema:'SHIPYARD_FE06_SOURCE_FORECAST_V1',engine_id:'FE06',feature_origin:'official_issuer_workbooks_new_derived_policy',feature_policy:SHIPYARD_FE06_POLICY,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,redistribution_rights_established:false,observed_vendor_flow:false}};
  if(!args||Object.keys(args).length!==2||args.engine_id!=='FE06'||!SHIPYARD_FE06_UNIVERSE.some(x=>x.ticker===args.symbol))return json({...base,status:'invalid',error:'invalid_arguments'},400);
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  const nowMs=Date.now();if(!shipyardFE06ChargeIngress(request,nowMs))return json({...base,status:'unavailable',error:'ingress_rate_limited',source_requests_made:0},429);
  const key=shipyardFE06CacheKey(nowMs),cached=shipyardFE06CacheGet(key,nowMs);
  if(cached){
    try{const value=shipyardFE06ProjectTarget(cached.value,args.symbol,nowMs,'hit',cached.expires_at);value.source_cache.stored_result_bytes=cached.size_bytes;return researchResponse(value);}
    catch(error){if(error?.code==='source_data_stale')SHIPYARD_FE06_RUNTIME.cache.delete(key);else return json({...base,status:'unavailable',error:'cache_projection_unavailable'},503);}
  }
  let promise=SHIPYARD_FE06_RUNTIME.inflight.get(key),owner=false;
  if(!promise){
    if(!shipyardFE06ChargeColdAcquisition(request,nowMs))return json({...base,status:'unavailable',error:'cold_source_rate_limited',source_requests_made:0},429);
    owner=true;promise=Promise.resolve().then(async()=>{
      const response=await shipyardFE06AcquireResponse(request,args,env);return {status:response.status,value:await response.json()};
    });SHIPYARD_FE06_RUNTIME.inflight.set(key,promise);
  }
  try{
    const result=await promise;if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
    if(result.status<200||result.status>=300)return json(result.value,result.status);
    const storedAt=Date.now();if(owner)shipyardFE06CachePut(key,result.value,storedAt);
    const entry=shipyardFE06CacheGet(key,storedAt),expiresAt=entry?.expires_at??Math.min(storedAt+SHIPYARD_FE06_INGRESS.cache_ttl_ms,Date.parse(result.value.source?.freshness_expires_at)||storedAt,shipyardFE06NextNYMidnight(storedAt));
    const cacheStatus=owner?'miss':'inflight_coalesced';
    const value=shipyardFE06ProjectTarget(result.value,args.symbol,storedAt,cacheStatus,expiresAt);
    if(cacheStatus==='inflight_coalesced')value.source_cache.provider_requests_this_call=0;
    if(entry)value.source_cache.stored_result_bytes=entry.size_bytes;
    if(new TextEncoder().encode(JSON.stringify(value)).length>48*1024)return json({...base,status:'unavailable',error:'feature_response_size_limit'},503);
    return researchResponse(value);
  }catch(error){
    const code=error?.code==='source_data_stale'?'source_data_stale':'source_acquisition_failed';
    return json({...base,status:'unavailable',error:code},503);
  }finally{if(owner&&SHIPYARD_FE06_RUNTIME.inflight.get(key)===promise)SHIPYARD_FE06_RUNTIME.inflight.delete(key);}
}
