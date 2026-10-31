import {deflateRawSync} from 'node:zlib';
import {selectFE05TopIssuerCohort,computeFE05BreadthMeasurements,buildFE05SourceForecast} from '../../research/forecast-features/fe05-spy-breadth-v1.mjs';

const TOTAL=99.9735,RESIDUAL=100-TOTAL,CASH=0.058971,CVR=0.000003,ELIGIBLE=TOTAL-CASH-CVR;
const xml=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');
function crc32(data){let crc=0xffffffff;for(const byte of data){crc^=byte;for(let k=0;k<8;k++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
function cusip(base){const value=ch=>ch>='0'&&ch<='9'?Number(ch):ch.charCodeAt(0)-55;let sum=0;for(let i=0;i<8;i++){const n=value(base[i])*(i%2===0?1:2);sum+=Math.floor(n/10)+n%10;}return base+String((10-sum%10)%10);}
function zipEntries(entries){
  const locals=[],centrals=[];let offset=0;
  for(const [name,source] of Object.entries(entries)){
    const filename=Buffer.from(name,'utf8'),raw=Buffer.from(source,'utf8'),compressed=deflateRawSync(raw),crc=crc32(raw);
    const local=Buffer.alloc(30);local.writeUInt32LE(0x04034b50,0);local.writeUInt16LE(20,4);local.writeUInt16LE(8,8);local.writeUInt32LE(crc,14);local.writeUInt32LE(compressed.length,18);local.writeUInt32LE(raw.length,22);local.writeUInt16LE(filename.length,26);
    locals.push(local,filename,compressed);
    const central=Buffer.alloc(46);central.writeUInt32LE(0x02014b50,0);central.writeUInt16LE(20,4);central.writeUInt16LE(20,6);central.writeUInt16LE(8,10);central.writeUInt32LE(crc,16);central.writeUInt32LE(compressed.length,20);central.writeUInt32LE(raw.length,24);central.writeUInt16LE(filename.length,28);central.writeUInt32LE(offset,42);
    centrals.push(central,filename);offset+=local.length+filename.length+compressed.length;
  }
  const centralBytes=Buffer.concat(centrals),localBytes=Buffer.concat(locals),end=Buffer.alloc(22),count=Object.keys(entries).length;
  end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(count,8);end.writeUInt16LE(count,10);end.writeUInt32LE(centralBytes.length,12);end.writeUInt32LE(localBytes.length,16);
  return new Uint8Array(Buffer.concat([localBytes,centralBytes,end]));
}

export function makeSyntheticHoldings(){
  const positions=[],prefixOf=i=>'A'+i.toString(36).toUpperCase().padStart(5,'0');let symbolNumber=1;
  for(let i=1;i<=502;i++){
    const issuerWeight=i<=25?5-(i-1)*0.2:(ELIGIBLE-65)/477;
    const numberOfLines=i===1?2:1;
    for(let issue=1;issue<=numberOfLines;issue++){
      const weight=numberOfLines===1?issuerWeight:issuerWeight*(issue===1?0.6:0.4),prefix=prefixOf(i);
      positions.push({source_row:6+positions.length,name:`SYNTHETIC ISSUER ${String(i).padStart(3,'0')}`,ticker:`S${String(symbolNumber).padStart(4,'0')}`,
        identifier:cusip(`${prefix}${String(issue).padStart(2,'0')}`),weight_percent:weight,sector:'-',local_currency:'USD'});symbolNumber++;
    }
  }
  positions.push({source_row:6+positions.length,name:'US DOLLAR',ticker:'-',identifier:'999USDZ92',weight_percent:CASH,sector:'-',local_currency:'USD'});
  positions.push({source_row:6+positions.length,name:'CONTRA HOLOGIC INCORPO',ticker:'2602335D',identifier:'436CVR021',weight_percent:CVR,sector:'-',local_currency:'USD'});
  if(positions.length!==505)throw Error('synthetic holdings shape');
  return {product:'SPY',as_of_date:'2026-10-29',as_of_granularity:'date_only',source_position_count:positions.length,
    position_weight_total_percent:TOTAL,unreconciled_weight_percent:RESIDUAL,positions};
}
export function makeSyntheticXlsx(holdings=makeSyntheticHoldings(),sharedPadding='',worksheetMutation=null,relationshipMutation=null){
  const strings=[],indices=new Map(),ss=value=>{value=String(value);if(!indices.has(value)){indices.set(value,strings.length);strings.push(value);}return indices.get(value);};
  const cells=(row,values)=>`<row r="${row}">${Object.entries(values).map(([col,value])=>value?.type==='number'?`<c r="${col}${row}" t="n"><v>${value.value}</v></c>`:`<c r="${col}${row}" t="s"><v>${ss(value?.value??value)}</v></c>`).join('')}</row>`;
  const row1=cells(1,{A:'Fund Name:',B:'State Street® SPDR® S&P 500® ETF Trust'}),row2=cells(2,{A:'Ticker Symbol:',B:'SPY'}),row3=cells(3,{A:'Holdings:',B:'As of 29-Oct-2026'});
  const header=cells(5,{A:'Name',B:'Ticker',C:'Identifier',D:'SEDOL',E:'Weight',F:'Sector',G:'Shares Held',H:'Local Currency'});
  const data=holdings.positions.map((p,i)=>cells(6+i,{A:p.name,B:p.ticker,C:p.identifier,D:'-',E:{type:'number',value:p.weight_percent},F:p.sector,G:{type:'number',value:1},H:p.local_currency})).join('');
  const footer=`<row r="511"/><row r="513"><c r="A513" t="s"><v>${ss('Official file disclosure')}</v></c><c r="B513"/><c r="C513"/><c r="D513"/><c r="E513"/><c r="F513"/><c r="G513"/><c r="H513"/></row>`;
  let xmlSheet=`<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${row1}${row2}${row3}<row r="4"/>${header}${data}${footer}</sheetData></worksheet>`;if(worksheetMutation)xmlSheet=worksheetMutation(xmlSheet);
  const shared=`<?xml version="1.0" encoding="UTF-8"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">${strings.map(value=>`<si><t>${xml(value)}</t></si>`).join('')}${sharedPadding?`<si><t>${sharedPadding}</t></si>`:''}</sst>`;
  const workbook='<?xml version="1.0" encoding="UTF-8"?><workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="holdings" sheetId="1" r:id="rId1"/></sheets></workbook>';
  let relationships='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>';if(relationshipMutation)relationships=relationshipMutation(relationships);
  return zipEntries({'xl/workbook.xml':workbook,'xl/_rels/workbook.xml.rels':relationships,'xl/sharedStrings.xml':shared,'xl/worksheets/sheet1.xml':xmlSheet});
}
export function makeCommentCounterfeitXlsx(){
  return makeSyntheticXlsx(makeSyntheticHoldings(),'',(sheet)=>{
    const row=sheet.match(/<row r="6">[\s\S]*?<\/row>/)?.[0];if(!row)throw Error('synthetic first position missing');
    const counterfeit=row.replace(/(<c r="E6" t="n"><v>)[^<]+/,(_,prefix)=>prefix+'7.0');return sheet.replace(row,`<!--${counterfeit}-->`);
  });
}
export function makeForeignNamespaceXlsx(){
  return makeSyntheticXlsx(makeSyntheticHoldings(),'',(sheet)=>sheet.replace('xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"','xmlns="urn:attacker:foreign-sheet"'));
}
export function makeBadWorkbookRelationshipXlsx(){
  return makeSyntheticXlsx(makeSyntheticHoldings(),' ',null,(rels)=>rels.replace('worksheets/sheet1.xml','worksheets/missing.xml'));
}
export function makeNestedCellValueXlsx(){
  return makeSyntheticXlsx(makeSyntheticHoldings(),'',(sheet)=>sheet.replace('<c r="E6" t="n"><v>','<c r="E6" t="n"><evil><v>7.772259</v></evil><v>'));
}
export function makeMismatchedCellRowXlsx(){
  return makeSyntheticXlsx(makeSyntheticHoldings(),'',(sheet)=>sheet.replace(/<row r="6">([\s\S]*?)<\/row>/,(_all,body)=>`<row r="6">${body.replace('r="A6"','r="A9999"')}</row>`));
}
export function makeCompressedXlsxBomb(){
  const bytes=makeSyntheticXlsx(makeSyntheticHoldings(),'x'.repeat(4*1024*1024+32)),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  for(let p=0;p+46<=bytes.length;p++)if(view.getUint32(p,true)===0x02014b50){
    const nameLength=view.getUint16(p+28,true),extraLength=view.getUint16(p+30,true),commentLength=view.getUint16(p+32,true),name=new TextDecoder().decode(bytes.slice(p+46,p+46+nameLength));
    if(name==='xl/sharedStrings.xml'){
      const local=view.getUint32(p+42,true);view.setUint32(p+24,4*1024*1024,true);view.setUint32(local+22,4*1024*1024,true);return bytes;
    }
    p+=45+nameLength+extraLength+commentLength;
  }
  throw Error('synthetic XLSX shared-string entry missing');
}
export function makeSyntheticDates(count=505,endDate='2026-10-29'){
  const out=[],d=new Date(endDate+'T12:00:00Z');while(out.length<count){const day=d.getUTCDay();if(day!==0&&day!==6)out.push(d.toISOString().slice(0,10));d.setUTCDate(d.getUTCDate()-1);}return out.reverse();
}
export function makeSyntheticCloses(symbols,dates){
  const out={};for(let j=0;j<symbols.length;j++){
    let price=100;const values=[price];
    for(let i=1;i<dates.length;i++){
      const r=0.0001*((i*7+j*3)%13-6)+0.0012*Math.sin((i+1)*(j+3)/17)+0.0004*Math.cos((i+5)*(j+7)/29);
      price*=Math.exp(r);values.push(price);
    }
    out[symbols[j]]=values;
  }
  return out;
}
export function makeSyntheticFE05Forecast({evaluationAt='2026-10-30T13:30:10.000Z',calendarEnd=null}={}){
  const holdings=makeSyntheticHoldings(),cohort=selectFE05TopIssuerCohort(holdings),dates=makeSyntheticDates(),
    symbols=[...cohort.symbols,'SPY'].sort(),closesBySymbol=makeSyntheticCloses(symbols,dates),features=computeFE05BreadthMeasurements(cohort,closesBySymbol,dates);
  // Friday morning permits a source effective date of Thursday to pass the
  // conservative date-only 48h bound without inventing an observation clock.
  const captureHash='a'.repeat(64),base=Date.parse(evaluationAt)-10000,evaluationDate=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(evaluationAt));
  const receipt=(operation,subject,offset,extra={})=>({operation,subject,request_started_at:new Date(base+offset).toISOString(),http_response_received_at:new Date(base+offset+500).toISOString(),
    received_at:new Date(base+offset+1000).toISOString(),response_sha256:captureHash,hash_serialization:'raw_response_bytes',http_status:200,...extra});
  const from=new Date(Date.parse(holdings.as_of_date+'T00:00:00Z')-800*86400000).toISOString().slice(0,10),calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');
  calendarUrl.searchParams.set('start',from);calendarUrl.searchParams.set('end',calendarEnd||evaluationDate);
  const calendarCapture=receipt('official_calendar','US_EQUITY',2000,{request_url:calendarUrl.toString()}),holdingsCapture=receipt('spy_holdings_xlsx','SPY',0,{request_url:'https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'});
  const bars=[];let rowsLeft=symbols.length*505;
  for(let page=1;rowsLeft>0;page++){
    const pageRows=Math.min(7000,rowsLeft);rowsLeft-=pageRows;const url=new URL('https://data.alpaca.markets/v2/stocks/bars');
    const query={symbols:symbols.join(','),timeframe:'1Day',start:dates[0]+'T05:00:00Z',end:holdings.as_of_date+'T23:59:59.999Z',feed:'iex',adjustment:'split',currency:'USD',asof:holdings.as_of_date,sort:'asc',limit:'7000',...(page>1?{page_token:'[continuation]'}:{})};
    for(const [k,v] of Object.entries(query))url.searchParams.set(k,v);
    bars.push(receipt('historical_multi_symbol_1Day_page','FE05_TOP25_ISSUER_COHORT',3000+(page-1)*1500,{request_url:url.toString(),page_index:page,provider_rows:pageRows,has_next_page:rowsLeft>0}));
  }
  const calendarDates=new Set(dates);for(let d=new Date(holdings.as_of_date+'T12:00:00.000Z');d.toISOString().slice(0,10)<evaluationDate;){d.setUTCDate(d.getUTCDate()+1);const weekday=d.getUTCDay();if(weekday!==0&&weekday!==6)calendarDates.add(d.toISOString().slice(0,10));}
  const calendarSessions=[...calendarDates].sort().filter(date=>date<=evaluationDate).map(date=>({date,open:date+'T13:30:00.000Z',close:date+'T20:00:00.000Z'}));
  return buildFE05SourceForecast({holdings,cohort,dates,closesBySymbol,calendarCapture,calendarSessions,holdingsCapture,barsCaptures:bars,evaluationAt});
}
