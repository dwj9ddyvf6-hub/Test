import assert from 'node:assert/strict';
import {deflateRawSync} from 'node:zlib';

export const FE06_TICKERS=['XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU'];
export const FE06_ISINS=['US81369Y8527','US81369Y4070','US81369Y3080','US81369Y5069','US81369Y6059','US81369Y2090','US81369Y7040','US81369Y1001','US81369Y8600','US81369Y8030','US81369Y8865'];
export const FE06_SPLIT_TICKERS=['XLK','XLY','XLE','XLU','XLB'];
export const FE06_SPLIT_DATE='2025-12-05';
const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

export function fe06Dates(end='2026-10-29',count=254){
  const dates=[],cursor=new Date(end+'T00:00:00Z');
  while(dates.length<count){const day=cursor.getUTCDay();if(day!==0&&day!==6)dates.push(cursor.toISOString().slice(0,10));cursor.setUTCDate(cursor.getUTCDate()-1);}
  return dates.reverse();
}
export function fe06SourceCalendar(dates,{lagDate='2026-10-30'}={}){
  const all=[...dates,lagDate];
  return all.map(date=>({date,open:'09:30',close:date==='2025-11-28'?'13:00':'16:00'}));
}
function excelDate(date){const [year,month,day]=date.split('-').map(Number);return `${String(day).padStart(2,'0')}-${monthNames[month-1]}-${year}`;}
function cell(ref,type,value){return `<c r="${ref}" t="${type}"><v>${value}</v></c>`;}
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
function zip(files,{corrupt=false}={}){
  const local=[],central=[];let offset=0;
  for(const [name,content] of files){const nameBytes=Buffer.from(name),raw=Buffer.from(content),compressed=deflateRawSync(raw),crc=crc32(raw);
    const lh=Buffer.alloc(30);lh.writeUInt32LE(0x04034b50,0);lh.writeUInt16LE(20,4);lh.writeUInt16LE(0,6);lh.writeUInt16LE(8,8);lh.writeUInt32LE(crc,14);lh.writeUInt32LE(compressed.length,18);lh.writeUInt32LE(raw.length,22);lh.writeUInt16LE(nameBytes.length,26);
    local.push(lh,nameBytes,compressed);const ch=Buffer.alloc(46);ch.writeUInt32LE(0x02014b50,0);ch.writeUInt16LE(20,4);ch.writeUInt16LE(20,6);ch.writeUInt16LE(8,10);ch.writeUInt32LE(corrupt&&name==='xl/sharedStrings.xml'?(crc^1)>>>0:crc,16);ch.writeUInt32LE(compressed.length,20);ch.writeUInt32LE(raw.length,24);ch.writeUInt16LE(nameBytes.length,28);ch.writeUInt32LE(offset,42);central.push(ch,nameBytes);offset+=lh.length+nameBytes.length+compressed.length;
  }
  const centralBytes=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(files.length,8);end.writeUInt16LE(files.length,10);end.writeUInt32LE(centralBytes.length,12);end.writeUInt32LE(offset,16);
  return Buffer.concat([...local,centralBytes,end]);
}
export function fe06Records(index=0,{cashDistribution=false,unsupportedSplit=false,constantShares=false}={}){
  const dates=fe06Dates(),records=[];let adjustedNav=100+index,shares=1_000_000+index*10000,splitFactor=1;
  for(let i=0;i<dates.length;i++){
    const date=dates[i];let split=date===FE06_SPLIT_DATE&&FE06_SPLIT_TICKERS.includes(FE06_TICKERS[index]);if(unsupportedSplit&&date==='2026-06-01')split=true;
    if(i>0){const drift=(index-5)*0.00011,noise=(((i+index*3)%7)-3)*0.000025;adjustedNav*=1+drift+noise;
      if(split)splitFactor*=2;
      if(!constantShares&&!split){const delta=((i*37+index*11)%31)-15;shares=Math.max(100000,shares+delta*100);}
      else if(split)shares*=2;
    }
    let nav=adjustedNav/splitFactor;
    if(cashDistribution&&index===4&&i===dates.length-1){nav*=0.9;}
    if(unsupportedSplit&&date==='2026-06-01'){const prev=records.at(-1);nav=prev.nav/2;shares=prev.shares*2;}
    if(cashDistribution&&index===4&&i===dates.length-1)shares=records.at(-1).shares;
    const navText=nav.toFixed(6),sharesText=String(Math.trunc(shares)),assetsText=(Number(navText)*Number(sharesText)).toFixed(2);
    records.push({date,nav:navText,shares:sharesText,assets:assetsText,source_row:i+5});
  }
  return records;
}
export function fe06Workbook(ticker,records,{missingSharesAt=null,zeroAssetsAt=null,breachAssetsAt=null,duplicateDateAt=null,externalWorksheetRelations=true,doctype=false,macro=false,corrupt=false,extraEntries=[],commentRowAt=null,commentXmlPart=null,foreignRowAt=null,mismatchCellRowAt=null,malformedXmlStart=false}={}){
  if(duplicateDateAt){const at=records.findIndex(row=>row.date===duplicateDateAt);assert.ok(at>0);records[at].date=records[at-1].date;}
  const strings=[ticker,'Date','NAV','Shares Outstanding','Total Net Assets',...(missingSharesAt!==null?['-']:[]),...records.map(row=>excelDate(row.date))],indices=new Map(strings.map((v,i)=>[v,i]));
  const header=[cell('A4','s',indices.get('Date')),cell('B4','s',indices.get('NAV')),cell('C4','s',indices.get('Shares Outstanding')),cell('D4','s',indices.get('Total Net Assets'))].join('');
  const rows=[`<row r="2">${cell('B2','s',indices.get(ticker))}</row>`,`<row r="4">${header}</row>`];
  const reversed=[...records].reverse();for(let i=0;i<reversed.length;i++){
    const row=reversed[i],rowNo=i+5,dateIndex=indices.get(excelDate(row.date)),cells=[cell(`A${rowNo}`,'s',dateIndex),cell(`B${rowNo}`,'n',row.nav)];
    if(missingSharesAt===row.date)cells.push(cell(`C${rowNo}`,'s',indices.get('-')));else cells.push(cell(`C${rowNo}`,'n',row.shares));
    let assets=row.assets;if(zeroAssetsAt===row.date)assets='0';if(breachAssetsAt===row.date)assets=(Number(row.assets)*1.01).toFixed(2);cells.push(cell(`D${rowNo}`,'n',assets));
    let markup=`<row r="${rowNo}">${cells.join('')}</row>`;
    if(row.date===commentRowAt)rows.push(`<!--${markup}-->`);
    else if(row.date===foreignRowAt)rows.push(`<evil:row xmlns:evil="urn:attacker" r="${rowNo}">${cells.join('')}</evil:row>`);
    else if(row.date===mismatchCellRowAt)rows.push(markup.replace(new RegExp(`([A-Z]+)${rowNo}\"` ,'g'),(_m,col)=>`${col}${rowNo+1}\"`));
    else rows.push(markup);
  }
  const shared=`<?xml version="1.0" encoding="UTF-8"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">${strings.map(value=>`<si><t>${value}</t></si>`).join('')}</sst>`;
  const workbook=`<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="navhist" sheetId="1" r:id="rId1"/></sheets></workbook>`;
  const rels=`<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>`;
  const rootRels=`<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="xl/workbook.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"/></Relationships>`;
  const ct=`<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>`;
  let sheet=`<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${rows.join('')}</sheetData></worksheet>`;
  if(malformedXmlStart)sheet=sheet.replace('<row r="5"','< row r="5"');
  const worksheetRels=externalWorksheetRelations?`<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="hyperlink1" Target="https://example.invalid/not-followed" TargetMode="External" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"/></Relationships>`:null;
  const files=[['[Content_Types].xml',ct],['_rels/.rels',rootRels],['xl/workbook.xml',doctype?'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+workbook:workbook],['xl/_rels/workbook.xml.rels',rels],['xl/sharedStrings.xml',shared],['xl/worksheets/sheet1.xml',sheet]];
  if(worksheetRels)files.push(['xl/worksheets/_rels/sheet1.xml.rels',worksheetRels]);if(macro)files.push(['xl/vbaProject.bin','macro']);files.push(...extraEntries);if(commentXmlPart){const target=files.findIndex(([name])=>name===commentXmlPart);assert.notEqual(target,-1);files[target][1]=files[target][1].replace(/<([^!?][^>]*)>/,match=>`<!--spoofed-tag-->${match}`);}return zip(files,{corrupt});
}
export function fe06UniverseBooks(options={}){
  return Object.fromEntries(FE06_TICKERS.map((ticker,index)=>[ticker,fe06Workbook(ticker,fe06Records(index,options),options)]));
}
