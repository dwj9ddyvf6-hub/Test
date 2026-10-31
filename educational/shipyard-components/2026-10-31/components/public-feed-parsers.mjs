// Pure CSV/XML-shape parsers only. Network fetchers, route/cache code, URLs, and provider captures are excluded.

export function parseTreasuryFeed(text,receivedAt,throughDate,kind='nominal'){
 const real=kind==='real',title=real?'DailyTreasuryRealYieldCurveRateData':'DailyTreasuryYieldCurveRateData';if(typeof text!=='string'||text.length>150000||!new RegExp(`<title[^>]*>${title}<\\/title>`).test(text))return null;const cutoff=typeof throughDate==='string'?throughDate:new Date(throughDate).toISOString().slice(0,10),entries=[...text.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/g)].slice(-110),observations=[],seen=new Set();
 const field=(entry,name)=>{const escaped=name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),m=entry.match(new RegExp(`<d:${escaped}\\b[^>]*>([^<]*)<\\/d:${escaped}>`));return m?.[1]||null;},fields=real?{five_year:'TC_5YEAR',seven_year:'TC_7YEAR',ten_year:'TC_10YEAR',twenty_year:'TC_20YEAR',thirty_year:'TC_30YEAR'}:{one_month:'BC_1MONTH',two_month:'BC_2MONTH',three_month:'BC_3MONTH',four_month:'BC_4MONTH',six_month:'BC_6MONTH',one_year:'BC_1YEAR',two_year:'BC_2YEAR',three_year:'BC_3YEAR',five_year:'BC_5YEAR',seven_year:'BC_7YEAR',ten_year:'BC_10YEAR',twenty_year:'BC_20YEAR',thirty_year:'BC_30YEAR'},required=real?['five_year','ten_year','thirty_year']:['two_year','ten_year','thirty_year'];
 for(const match of entries){const entry=match[1],rawDate=field(entry,'NEW_DATE'),date=rawDate?.match(/^(\d{4}-\d{2}-\d{2})/i)?.[1];if(!date||date>cutoff||seen.has(date))continue;const values=Object.fromEntries(Object.entries(fields).map(([key,name])=>[key,(()=>{const value=field(entry,name)?.trim();return value&&/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(value)?Number(value):NaN;})()]).filter(([,value])=>Number.isFinite(value)));if(!required.every(key=>Number.isFinite(values[key])))continue;seen.add(date);observations.push({date,...values});}
 observations.sort((a,b)=>a.date.localeCompare(b.date));return observations.length?{source:'US Treasury',series_id:real?'daily_treasury_real_yield_curve':'daily_treasury_yield_curve',observations,received_at:receivedAt}:null;
}

export function parseTreasuryCurve(text,receivedAt,throughDate){return parseTreasuryFeed(text,receivedAt,throughDate,'nominal');}

export function parseTreasuryRealCurve(text,receivedAt,throughDate){return parseTreasuryFeed(text,receivedAt,throughDate,'real');}

export function parseFedDollarIndex(text,receivedAt,throughDate){
 if(typeof text!=='string'||text.length>12000||!text.includes('Nominal Broad Dollar Index')||!text.includes('H10/H10/JRXWTFB_N.B')||!text.includes('Time Period'))return null;
 const cutoff=typeof throughDate==='string'?throughDate:new Date(throughDate).toISOString().slice(0,10),observations=[],seen=new Set();
 for(const line of text.split(/\r?\n/)){const match=line.match(/^(\d{4}-\d{2}-\d{2}),([^,]+),([^,]+),([^,]+)$/);if(!match||match[1]>cutoff||seen.has(match[1]))continue;const values=match.slice(2).map(value=>value==='ND'||value==='.'?null:Number(value));if(!Number.isFinite(values[0])||values[0]<=0)continue;seen.add(match[1]);observations.push({date:match[1],broad:values[0],advanced:Number.isFinite(values[1])?values[1]:null,emerging:Number.isFinite(values[2])?values[2]:null});}
 observations.sort((a,b)=>a.date.localeCompare(b.date));return observations.length?{source:'Federal Reserve Board',series_id:'H10/H10/JRXWTFB_N.B',received_at:receivedAt,observations:observations.slice(-10)}:null;
}

export function parseCboeIndexCsv(text,index,receivedAt,throughDate){
 const allowed={VIX:'CLOSE',VIX3M:'CLOSE',VVIX:'VVIX',SKEW:'SKEW'},valueColumn=allowed[index];if(!valueColumn||typeof text!=='string'||text.length>600000)return null;
 const lines=text.replace(/^\uFEFF/,'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean);if(lines.length<2)return null;
 const header=lines[0].split(',').map(x=>x.trim().toUpperCase()),dateIndex=header.indexOf('DATE'),valueIndex=header.indexOf(valueColumn);if(dateIndex<0||valueIndex<0)return null;
 const cutoff=typeof throughDate==='string'?throughDate:new Date(throughDate).toISOString().slice(0,10),seen=new Set(),observations=[];
 for(const line of lines.slice(1)){const fields=line.split(',').map(x=>x.trim());if(fields.length!==header.length)continue;const match=fields[dateIndex].match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);if(!match)continue;const date=`${match[3]}-${String(match[1]).padStart(2,'0')}-${String(match[2]).padStart(2,'0')}`,clock=Date.parse(`${date}T00:00:00Z`),value=Number(fields[valueIndex]);if(!Number.isFinite(clock)||new Date(clock).toISOString().slice(0,10)!==date||date>cutoff||seen.has(date)||!Number.isFinite(value)||value<=0)continue;
  if(valueColumn==='CLOSE'){const open=Number(fields[header.indexOf('OPEN')]),high=Number(fields[header.indexOf('HIGH')]),low=Number(fields[header.indexOf('LOW')]);if(![open,high,low].every(Number.isFinite)||low>Math.min(open,value)||high<Math.max(open,value)||high<low)continue;}
  seen.add(date);observations.push({as_of:date,close:value,received_at:receivedAt});
 }
 observations.sort((a,b)=>a.as_of.localeCompare(b.as_of));return observations.length?{source:'Cboe Global Markets',index,observations:observations.slice(-260)}:null;
}
