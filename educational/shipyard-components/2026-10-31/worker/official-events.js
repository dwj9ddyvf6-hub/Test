// On-demand public scheduled-release evidence. Never an all-market calendar or engine gate.
const SHIPYARD_EVENT_POLICY='OFFICIAL_SCHEDULED_MACRO_RESEARCH_V1';
const shipyardEventCache=new Map();
const shipyardEventMonthFormat=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit'});
const shipyardEventLocalFormat=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const shipyardEventMonths=['january','february','march','april','may','june','july','august','september','october','november','december'];
function shipyardEventMonth(now=Date.now()){
  const p=Object.fromEntries(shipyardEventMonthFormat.formatToParts(new Date(now)).map(p=>[p.type,p.value]));
  return `${p.year}-${p.month}`;
}
function shipyardEventNextMonth(month){return new Date(Date.UTC(Number(month.slice(0,4)),Number(month.slice(5,7)),1)).toISOString().slice(0,7);}
function shipyardEventArguments(args,now=Date.now()){
  return args&&typeof args==='object'&&!Array.isArray(args)&&Object.keys(args).every(k=>k==='month')&&(!('month'in args)||typeof args.month==='string'&&[shipyardEventMonth(now),shipyardEventNextMonth(shipyardEventMonth(now))].includes(args.month));
}
function shipyardEventLocal(date,time){
  if(!shipyardCalendarDate(date)||typeof time!=='string'||!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(time))throw Error('invalid_event_time');
  const local=time.length===5?time+':00':time,base=Date.parse(date+'T'+local+'Z'),matches=[];
  // Both current US Eastern offsets are checked against IANA rules; gaps and
  // ambiguous fall-back wall times are rejected, never silently guessed.
  for(const hours of [4,5]){
    const at=new Date(base+hours*3600000),p=Object.fromEntries(shipyardEventLocalFormat.formatToParts(at).map(p=>[p.type,p.value]));
    if(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`===date+'T'+local)matches.push(at.toISOString());
  }
  if(matches.length!==1)throw Error('ambiguous_or_nonexistent_event_time');return matches[0];
}
function shipyardEventText(value,max=350){
  if(typeof value!=='string'||!value.trim()||value.length>max||/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value))throw Error('invalid_event_text');return value.trim();
}
function shipyardEventIso(value){
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$/.test(value)||!shipyardCalendarDate(value.slice(0,10))||!Number.isFinite(Date.parse(value)))throw Error('invalid_event_time');
  if(!/^([01]\d|2[0-3]):[0-5]\d:[0-5]\d/.test(value.slice(11)))throw Error('invalid_event_time');return new Date(value).toISOString();
}
function shipyardEventInMonth(at,month){return shipyardEventMonth(Date.parse(at))===month;}
function shipyardParseBeaEvents(text,month){
  const data=JSON.parse(text);if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).length===0||Object.keys(data).length>100)throw Error('invalid_bea_schema');
  const events=[],seen=new Set();let total=0,duplicates=0;
  for(const [name,value]of Object.entries(data)){
    if(name==='file_last_updated'){if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?$/.test(value))throw Error('invalid_bea_revision');continue;}
    shipyardEventText(name);if(!value||!Array.isArray(value.release_dates)||value.release_dates.length>1000)throw Error('invalid_bea_schema');
    for(const original of value.release_dates){if(++total>4000)throw Error('event_row_limit');const at=shipyardEventIso(original),id=name+'|'+at;
      if(seen.has(id)){duplicates++;continue;}seen.add(id);
      if(shipyardEventInMonth(at,month))events.push({source_event_id:id,title:name,scheduled_at:at,original_time:original,time_status:'scheduled',source_revision:null,cancelled:false});
    }
  }
  if(total===0)throw Error('empty_source_schedule');return {events,parsed_rows:total,duplicates_coalesced:duplicates,source_revision_text:data.file_last_updated??null,source_revision_timezone:'unspecified; not interpreted as UTC',scope:'All categories and release dates present in BEA release_dates.json; not all economic events.',coverage_scope:'bea_release_date_json',scope_complete:true};
}
function shipyardParseBlsEvents(text,month){
  const unfolded=text.replace(/\r\n/g,'\n').replace(/\n[ \t]/g,'');
  if(!unfolded.startsWith('BEGIN:VCALENDAR\n')||!unfolded.trimEnd().endsWith('END:VCALENDAR'))throw Error('invalid_bls_calendar');
  const blocks=[...unfolded.matchAll(/BEGIN:VEVENT\n([\s\S]*?)\nEND:VEVENT/g)];
  if(!blocks.length||blocks.length>1500||(unfolded.match(/BEGIN:VEVENT/g)||[]).length!==blocks.length)throw Error('invalid_bls_calendar');
  const events=[],seen=new Map();let duplicates=0;
  for(const [,body]of blocks){
    const fields=new Map();for(const line of body.split('\n')){const colon=line.indexOf(':');if(colon<1)throw Error('invalid_bls_property');const key=line.slice(0,colon),value=line.slice(colon+1);if(fields.has(key))throw Error('duplicate_bls_property');fields.set(key,value);}
    if([...fields.keys()].some(k=>/^(RRULE|RDATE|EXDATE|RECURRENCE-ID)(?:;|$)/.test(k)))throw Error('unsupported_event_recurrence');
    const uid=shipyardEventText(fields.get('UID'),200),title=shipyardEventText(fields.get('SUMMARY')?.replace(/\\[nN]/g,' ').replace(/\\([,;\\])/g,'$1'));
    const starts=[...fields].filter(([k])=>k==='DTSTART'||k.startsWith('DTSTART;'));if(starts.length!==1)throw Error('invalid_bls_time');
    const [key,original]=starts[0],match=/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(Z?)$/.exec(original);if(!match)throw Error('invalid_bls_time');
    const date=`${match[1]}-${match[2]}-${match[3]}`,time=`${match[4]}:${match[5]}:${match[6]}`;
    let at;if(key==='DTSTART'&&match[7]==='Z')at=shipyardEventIso(date+'T'+time+'Z');else if(['DTSTART;TZID=US-Eastern','DTSTART;TZID=America/New_York'].includes(key)&&!match[7])at=shipyardEventLocal(date,time);else throw Error('unsupported_bls_timezone');
    const sequence=fields.get('SEQUENCE');if(sequence!==undefined&&!/^\d{1,9}$/.test(sequence))throw Error('invalid_event_revision');
    const status=fields.get('STATUS');if(status!==undefined&&!['CONFIRMED','TENTATIVE','CANCELLED'].includes(status))throw Error('invalid_event_status');
    const event={source_event_id:uid,title,scheduled_at:at,original_time:key+':'+original,time_status:status==='TENTATIVE'?'tentative':'scheduled',source_revision:sequence===undefined?null:Number(sequence),cancelled:status==='CANCELLED'};
    if(seen.has(uid)){if(JSON.stringify(seen.get(uid))!==JSON.stringify(event))throw Error('conflicting_event_uid');duplicates++;continue;}seen.set(uid,event);
    if(shipyardEventInMonth(at,month))events.push(event);
  }
  return {events,parsed_rows:blocks.length,duplicates_coalesced:duplicates,scope:'All events parsed from the published BLS calendar feed; the publisher says it covers most national-office releases, not every market-moving event.',coverage_scope:'bls_published_calendar',scope_complete:true};
}
function shipyardBlsPlain(value){
  const named={amp:'&',apos:"'",gt:'>',lt:'<',nbsp:' ',quot:'"'};
  return value.replace(/<br\s*\/?\s*>/gi,' ').replace(/<[^>]*>/g,' ').replace(/&(#(?:x[0-9a-f]+|[0-9]+)|[a-z][a-z0-9]+);/gi,(_,entity)=>{
    if(entity[0]==='#'){
      const hex=entity[1]?.toLowerCase()==='x',number=Number.parseInt(entity.slice(hex?2:1),hex?16:10);
      if(!Number.isInteger(number)||number<1||number>0x10ffff||number>=0xd800&&number<=0xdfff)throw Error('invalid_bls_entity');
      return String.fromCodePoint(number);
    }
    const decoded=named[entity.toLowerCase()];if(decoded===undefined)throw Error('unsupported_bls_entity');return decoded;
  }).replace(/\s+/g,' ').trim();
}
function shipyardParseBlsMonthlyList(text,month){
  if(typeof text!=='string'||text.length>524288)throw Error('invalid_bls_list');
  const monthName=shipyardEventMonths[Number(month.slice(5))-1],year=month.slice(0,4),expectedTitle=new RegExp(`<title>\\s*Schedule of Selected Releases for ${monthName} ${year}\\s*<\\/title>`,'i');
  if(!expectedTitle.test(text))throw Error('invalid_bls_list');
  const tables=[...text.matchAll(/<table\b[^>]*class=["']release-list["'][^>]*>([\s\S]*?)<\/table>/gi)];
  if(tables.length!==1)throw Error('invalid_bls_list');
  const rows=[...tables[0][1].matchAll(/<tr\b[^>]*class=["']release-list-(?:odd|even)-row["'][^>]*>([\s\S]*?)<\/tr>/gi)];
  if(!rows.length||rows.length>150||(tables[0][1].match(/<tr\b[^>]*class=["']release-list-/gi)||[]).length!==rows.length)throw Error('invalid_bls_list_rows');
  const weekdayNames=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const monthNumbers=new Map(shipyardEventMonths.map((name,index)=>[name,`-${String(index+1).padStart(2,'0')}-`]));
  const events=[],seen=new Set();let duplicates=0;
  for(const [rowIndex,rowMatch]of rows.entries()){
    const cells=[...rowMatch[1].matchAll(/<td\b[^>]*class=["'](date-cell|time-cell|desc-cell)["'][^>]*>([\s\S]*?)<\/td>/gi)];
    if(cells.length!==3||cells[0][1].toLowerCase()!=='date-cell'||cells[1][1].toLowerCase()!=='time-cell'||cells[2][1].toLowerCase()!=='desc-cell')throw Error('invalid_bls_list_row');
    const dateText=shipyardBlsPlain(cells[0][2]),dateMatch=/^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday), (January|February|March|April|May|June|July|August|September|October|November|December) (0?[1-9]|[12]\d|3[01]), (\d{4})$/.exec(dateText);
    if(!dateMatch)throw Error('invalid_bls_list_date');
    const date=`${dateMatch[4]}${monthNumbers.get(dateMatch[2].toLowerCase())}${String(Number(dateMatch[3])).padStart(2,'0')}`;
    if(date.slice(0,7)!==month||!shipyardCalendarDate(date)||weekdayNames[new Date(`${date}T00:00:00Z`).getUTCDay()]!==dateMatch[1])throw Error('invalid_bls_list_date');
    const timeText=shipyardBlsPlain(cells[1][2]),title=shipyardEventText(shipyardBlsPlain(cells[2][2]));
    let when={scheduled_at:null,original_time:null,time_status:'time_unknown'};
    if(timeText){
      const match=/^(0?[1-9]|1[0-2]):([0-5]\d)\s+(AM|PM)$/i.exec(timeText);if(!match)throw Error('invalid_bls_list_time');
      const hour24=(Number(match[1])%12)+(match[3].toLowerCase()==='pm'?12:0),time=`${String(hour24).padStart(2,'0')}:${match[2]}`;
      when={scheduled_at:shipyardEventLocal(date,time),original_time:timeText,time_status:'scheduled'};
    }
    const sourceEventId=`${date}|${when.original_time||'date-only'}|${title}`,key=sourceEventId.toLowerCase();
    if(seen.has(key)){duplicates++;continue;}seen.add(key);
    events.push({source_event_id:sourceEventId,title,scheduled_date:date,...when,source_revision:null,cancelled:false,row_index:rowIndex});
  }
  const revisionMatch=/<p\b[^>]*class=["']update["'][^>]*>\s*<strong>\s*Last Modified Date:\s*<\/strong>\s*([^<]+)/i.exec(text);
  return {events,parsed_rows:rows.length,duplicates_coalesced:duplicates,source_revision_text:revisionMatch?shipyardBlsPlain(revisionMatch[1]):null,source_revision_timezone:'America/New_York date only; not interpreted as an instant',scope:'All rows parsed from the published BLS monthly release list; the publisher says it covers most national-office releases, not every market-moving event.',coverage_scope:'bls_published_calendar',scope_complete:true};
}
function shipyardFedPlain(html){
  const entities={amp:'&',nbsp:' ',ntilde:'ñ',reg:'®',uuml:'ü'};
  return html.replace(/<!--[\s\S]*?-->/g,' ').replace(/<br\s*\/?\s*>/gi,' ').replace(/<[^>]*>/g,' ').replace(/&(#(?:x[0-9a-f]+|[0-9]+)|[a-z][a-z0-9]+);/gi,(_,entity)=>{
    if(entity[0]==='#'){
      const hex=entity[1]?.toLowerCase()==='x',number=Number.parseInt(entity.slice(hex?2:1),hex?16:10);
      if(!Number.isInteger(number)||number<1||number>0x10ffff||number>=0xd800&&number<=0xdfff)throw Error('invalid_fed_entity');
      return String.fromCodePoint(number);
    }
    const decoded=entities[entity.toLowerCase()];if(decoded===undefined)throw Error('unsupported_fed_entity');return decoded;
  }).replace(/\s+/g,' ').trim();
}
function shipyardFedTime(value,date){
  if(!value)return {scheduled_at:null,original_time:null,time_status:'time_unknown'};
  const match=/^(\d{1,2}):([0-5]\d)\s*([ap])\.?m\.?$/i.exec(value);
  if(!match)throw Error('invalid_fed_time');
  const hour=Number(match[1]);if(hour<1||hour>12)throw Error('invalid_fed_time');
  const hour24=(hour%12)+(match[3].toLowerCase()==='p'?12:0),at=shipyardEventLocal(date,`${String(hour24).padStart(2,'0')}:${match[2]}`);
  return {scheduled_at:at,original_time:value,time_status:'scheduled'};
}
function shipyardParseFederalReserveEvents(text,month){
  const expectedMonth=shipyardEventMonths[Number(month.slice(5))-1],expectedTitle=new RegExp(`<title>\\s*Federal Reserve Board\\s*-\\s*Calendar:\\s*${expectedMonth}\\s+${month.slice(0,4)}\\s*<\\/title>`,'i');
  if(typeof text!=='string'||text.length>524288||!/<html\b/i.test(text)||!expectedTitle.test(text)||!/<h4[^>]*>\s*Speeches\s*<\/h4>/i.test(text)||!/<div class="row cal-nojs__rowTitle">/i.test(text))throw Error('invalid_fed_calendar');
  const pattern=/<div class="panel panel-unstyled col-xs-12 col-sm-12 col-md-12">\s*<div class="panel-body">([\s\S]*?)<\/div>\s*<\/div>/g;
  const blocks=[...text.matchAll(pattern)],declared=(text.match(/class="panel panel-unstyled col-xs-12 col-sm-12 col-md-12"/g)||[]).length;
  if(blocks.length!==declared||blocks.length>600)throw Error('invalid_fed_calendar');
  const events=[],seen=new Set();let expanded=0;
  for(let rowIndex=0;rowIndex<blocks.length;rowIndex++){
    const body=blocks[rowIndex][1],columns=[...body.matchAll(/<div class="col-xs-(2|7|3)">([\s\S]*?)(?=<div class="col-xs-|$)/g)];
    if(columns.length!==3||columns[0][1]!=='2'||columns[1][1]!=='7'||columns[2][1]!=='3')throw Error('invalid_fed_calendar_row');
    const timeText=shipyardFedPlain(columns[0][2]),detail=columns[1][2],firstParagraph=/<p(?:\s[^>]*)?>([\s\S]*?)<\/p>/i.exec(detail);
    if(!firstParagraph)throw Error('invalid_fed_calendar_row');
    const title=shipyardEventText(shipyardFedPlain(firstParagraph[1])),dateText=shipyardFedPlain(columns[2][2]);
    if(title.length>240)throw Error('invalid_fed_calendar_row');
    if(!/^(?:[1-9]|[12]\d|3[01])(?:\s*,\s*(?:[1-9]|[12]\d|3[01]))*$/.test(dateText))throw Error('invalid_fed_calendar_date');
    const days=dateText.split(',').map(day=>Number(day.trim()));
    if(new Set(days).size!==days.length)throw Error('duplicate_fed_calendar_date');
    for(const day of days){
      if(++expanded>1200)throw Error('event_row_limit');
      const date=`${month}-${String(day).padStart(2,'0')}`;if(!shipyardCalendarDate(date))throw Error('invalid_fed_calendar_date');
      const when=shipyardFedTime(timeText,date),sourceEventId=`${month}|${rowIndex}|${day}|${title}`;
      if(seen.has(sourceEventId))throw Error('duplicate_fed_calendar_event');seen.add(sourceEventId);
      events.push({source_event_id:sourceEventId,title,scheduled_date:date,...when,source_revision:null,cancelled:false});
    }
  }
  return {events,parsed_rows:blocks.length,duplicates_coalesced:0,source_revision_text:null,scope:'All rows parsed from the Federal Reserve Board calendar for this month; not every market-moving event.',coverage_scope:'federal_reserve_board_monthly_calendar',scope_complete:true};
}
function shipyardEventLocalCentral(date,time){
  if(!shipyardCalendarDate(date)||typeof time!=='string'||!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(time))throw Error('invalid_event_time');
  const local=time.length===5?time+':00':time,base=Date.parse(date+'T'+local+'Z'),matches=[];
  for(const hours of [5,6]){
    const at=new Date(base+hours*3600000),p=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/Chicago',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(at).map(p=>[p.type,p.value]));
    if(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`===date+'T'+local)matches.push(at.toISOString());
  }
  if(matches.length!==1)throw Error('ambiguous_or_nonexistent_event_time');return matches[0];
}
function shipyardParseFredBlsReleaseCalendar(text,month,releaseId,title){
  const monthShort=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][Number(month.slice(5))-1],endDate=new Date(Date.UTC(Number(month.slice(0,4)),Number(month.slice(5,7)),0)).toISOString().slice(0,10);
  const expectedTitle=`<title>${monthShort}, ${month.slice(0,4)} Economic Release Calendar - ${title} | FRED | St. Louis Fed</title>`;
  if(typeof text!=='string'||text.length>524288||!/<html\b/i.test(text)||!text.includes(expectedTitle)
      ||!new RegExp(`id=[\"']rc-vs[\"'][^>]*value=[\"']${month}-01[\"']`).test(text)
      ||!new RegExp(`id=[\"']rc-ve[\"'][^>]*value=[\"']${endDate}[\"']`).test(text)
      ||!text.includes('All times are US Central Time.'))throw Error('invalid_fred_calendar');
  const events=[],seen=new Set();let currentDate=null,parsedRows=0;
  const rows=[...text.matchAll(/<tr\b[\s\S]*?<\/tr>/gi)];if(rows.length>500)throw Error('event_row_limit');
  for(const [rowIndex,rowMatch]of rows.entries()){
    const row=rowMatch[0],dateMatch=row.match(/<span[^>]*>\s*(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) (January|February|March|April|May|June|July|August|September|October|November|December) (0?[1-9]|[12]\d|3[01]), (\d{4})\s*<\/span>/i);
    if(dateMatch){
      const months=new Map(shipyardEventMonths.map((name,index)=>[name,`-${String(index+1).padStart(2,'0')}-`]));
      currentDate=`${dateMatch[4]}${months.get(dateMatch[2].toLowerCase())}${String(Number(dateMatch[3])).padStart(2,'0')}`;
      if(currentDate.slice(0,7)!==month||!shipyardCalendarDate(currentDate)||new Date(`${currentDate}T00:00:00Z`).toLocaleDateString('en-US',{weekday:'long',timeZone:'UTC'})!==dateMatch[1])throw Error('invalid_fred_calendar_date');
      continue;
    }
    const anchor=new RegExp(`<a\\b[^>]*href=[\"']/release\\?rid=${releaseId}[\"'][^>]*>([^<]+)<\\/a>`,'i').exec(row);
    if(!anchor)continue;
    if(!currentDate||++parsedRows>30||shipyardFedPlain(anchor[1])!==title)throw Error('invalid_fred_calendar_row');
    const timeCell=/<td\b[^>]*nowrap[^>]*>([\s\S]*?)<\/td>/i.exec(row),timeText=timeCell?shipyardFedPlain(timeCell[1]):'';
    const timeMatch=/^(0?[1-9]|1[0-2]):([0-5]\d)\s*(am|pm)$/i.exec(timeText);if(!timeMatch)throw Error('invalid_fred_calendar_time');
    const hour24=(Number(timeMatch[1])%12)+(timeMatch[3].toLowerCase()==='pm'?12:0),at=shipyardEventLocalCentral(currentDate,`${String(hour24).padStart(2,'0')}:${timeMatch[2]}`),sourceEventId=`FRED:${releaseId}:${currentDate}:${at}`;
    if(seen.has(sourceEventId))throw Error('duplicate_fred_calendar_event');seen.add(sourceEventId);
    events.push({source_event_id:sourceEventId,title,scheduled_at:at,scheduled_date:currentDate,original_time:timeText,time_status:'scheduled',release_id:releaseId,source_timezone:'America/Chicago',source_revision:null,cancelled:false});
  }
  const explicitEmpty=/id=["']release-dates-pager["'][^>]*>[\s\S]*?No release dates are available for the selected options\./i.test(text);
  if(!events.length&&!explicitEmpty||events.length&&explicitEmpty)throw Error('invalid_fred_calendar_rows');
  return {events,parsed_rows:parsedRows,duplicates_coalesced:0,scope:`FRED public release-calendar page for BLS release ${releaseId} (${title}); source clock America/Chicago.`,scope_complete:true,coverage_scope:'selected_bls_releases'};
}
async function shipyardEventHash(text){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join('');}
async function shipyardEventSource(request,source,url,month,parser){
  const base={source,url,status:'unavailable',received_at:null,source_last_modified:null,source_etag:null,original_publication_at:null,raw_sha256:null,events:[],parsed_rows:0,scope_complete:false};
  try{
    const headers={accept:source==='BEA'?'application/json':source==='BLS'&&url.endsWith('.ics')?'text/calendar':'text/html'};
    if(source==='BLS')headers['user-agent']='ShipyardResearchTerminal/1.0';
    const response=await fetch(url,{method:'GET',headers,redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(8000)])});
    base.http_status=response.status;if(!response.ok)throw Error('source_http_'+response.status);
    const text=await readBoundedBody(response,524288);base.received_at=new Date().toISOString();base.content_type=response.headers.get('content-type');
    base.source_last_modified=timestamp(response.headers.get('last-modified'));base.source_etag=bounded(response.headers.get('etag'),200);base.raw_sha256=await shipyardEventHash(text);
    const parsed=parser(text,month);if(parsed.events.length>150)throw Error('event_row_limit');
    for(const event of parsed.events){event.event_id=source.toLowerCase()+':'+await shipyardEventHash(event.source_event_id);event.source=source;event.source_url=url;event.available_at=base.received_at;event.historical_availability='unknown';}
    return {...base,...parsed,status:parsed.events.length?'parsed':'no_rows_in_requested_month',scope_complete:parsed.scope_complete===true,error:null};
  }catch(error){return {...base,checked_at:new Date().toISOString(),error:/^(source_http_\d{3}|invalid_|unsupported_|duplicate_|conflicting_|empty_|event_row_)/.test(error?.message||'')?error.message:'source_read_failed'};}
}
async function shipyardBlsEventSource(request,month){
  const primary=await shipyardEventSource(request,'BLS','https://www.bls.gov/schedule/news_release/bls.ics',month,shipyardParseBlsEvents);
  if(request.signal.aborted||primary.status!=='unavailable')return primary;
  const fallbackUrl=`https://www.bls.gov/schedule/${month.slice(0,4)}/${month.slice(5,7)}_sched_list.htm`;
  const fallback=await shipyardEventSource(request,'BLS',fallbackUrl,month,shipyardParseBlsMonthlyList);
  if(request.signal.aborted)return fallback;
  const attempt={url:primary.url,status:primary.status,http_status:primary.http_status,error:primary.error,checked_at:primary.checked_at};
  if(['parsed','no_rows_in_requested_month'].includes(fallback.status))return {...fallback,fallback_used:true,primary_attempt:attempt};
  const fred=await shipyardFredBlsEventSource(request,month);
  if(['parsed','no_rows_in_requested_month'].includes(fred.status))return {...fred,fallback_used:true,primary_attempt:attempt,bls_monthly_attempt:{url:fallback.url,status:fallback.status,http_status:fallback.http_status,error:fallback.error,checked_at:fallback.checked_at}};
  return {...primary,fallback_attempt:{url:fallback.url,status:fallback.status,http_status:fallback.http_status,error:fallback.error,checked_at:fallback.checked_at},
    fred_fallback:{status:fred.status,coverage_scope:fred.coverage_scope||null,scope_complete:fred.scope_complete===true,release_pages:fred.release_pages||[]},fallback_used:false};
}
async function shipyardFredBlsEventSource(request,month){
  const releases=[{id:10,title:'Consumer Price Index'},{id:11,title:'Employment Cost Index'},{id:46,title:'Producer Price Index'},{id:47,title:'Productivity and Costs'},{id:50,title:'Employment Situation'},{id:188,title:'U.S. Import and Export Price Indexes'},{id:192,title:'Job Openings and Labor Turnover Survey'}];
  const pages=await Promise.all(releases.map(async release=>{
    const url=`https://fred.stlouisfed.org/releases/calendar?view=month&y=${month.slice(0,4)}&m=${Number(month.slice(5,7))}&rid=${release.id}`;
    return {release,...await shipyardEventSource(request,'FRED',url,month,(text,requestedMonth)=>shipyardParseFredBlsReleaseCalendar(text,requestedMonth,release.id,release.title))};
  }));
  const ok=new Set(['parsed','no_rows_in_requested_month']),events=pages.flatMap(page=>page.events),complete=pages.length===releases.length&&pages.every(page=>ok.has(page.status)&&page.scope_complete===true),received=pages.map(page=>page.received_at).filter(Boolean).sort().at(-1)||null;
  const rawHash=complete?await shipyardEventHash(pages.map(page=>`${page.release.id}:${page.raw_sha256}`).join('|')):null;
  return {source:'FRED',url:'https://fred.stlouisfed.org/releases/calendar',status:complete?(events.length?'parsed':'no_rows_in_requested_month'):'unavailable',http_status:complete?200:pages.find(page=>!ok.has(page.status))?.http_status??null,received_at:received,source_last_modified:null,source_etag:null,original_publication_at:null,raw_sha256:rawHash,events,parsed_rows:pages.reduce((sum,page)=>sum+page.parsed_rows,0),duplicates_coalesced:0,scope:'Seven explicitly configured BLS releases from FRED public release calendars; this is a selected macro-release subset, not the full BLS schedule or all market events.',coverage_scope:'selected_bls_releases',scope_complete:complete,release_pages:pages.map(page=>({release_id:page.release.id,title:page.release.title,url:page.url,status:page.status,http_status:page.http_status,error:page.error,received_at:page.received_at,raw_sha256:page.raw_sha256,parsed_rows:page.parsed_rows})),error:complete?null:'selected_bls_release_calendar_incomplete'};
}
async function shipyardOfficialEvents(request,args={}){
  if(!shipyardEventArguments(args))return json({error:'invalid_current_or_next_month'},400);
  if(request.signal.aborted)return json({error:'cancelled'},408);
  const now=Date.now(),month=args.month||shipyardEventMonth(now),cached=shipyardEventCache.get(month);
  if(cached&&now-cached.created<cached.ttl)return json({...cached.value,served_at:new Date().toISOString(),cache_hit:true});
  if(!alpacaRateAllowed(request,now))return json({error:'rate_limited'},429);
  const fedUrl=`https://www.federalreserve.gov/newsevents/${month.slice(0,4)}-${shipyardEventMonths[Number(month.slice(5))-1]}.htm`;
  const sources=await Promise.all([
    shipyardBlsEventSource(request,month),
    shipyardEventSource(request,'BEA','https://apps.bea.gov/API/signup/release_dates.json',month,shipyardParseBeaEvents),
    shipyardEventSource(request,'Federal Reserve',fedUrl,month,shipyardParseFederalReserveEvents),
  ]);
  if(request.signal.aborted)return json({error:'cancelled'},408);
  const events=sources.flatMap(s=>s.events).sort((a,b)=>(a.scheduled_at||a.scheduled_date).localeCompare(b.scheduled_at||b.scheduled_date)||a.event_id.localeCompare(b.event_id));
  const completeStatuses=new Set(['parsed','no_rows_in_requested_month']),parsedAny=sources.some(s=>completeStatuses.has(s.status)),scopedComplete=sources.length===3&&sources.every(s=>completeStatuses.has(s.status)&&s.scope_complete===true);
  const received=new Date().toISOString(),value={schema:'SHIPYARD_OFFICIAL_EVENTS_V1',policy:SHIPYARD_EVENT_POLICY,month,timezone:'America/New_York',status:scopedComplete?'available_scoped':parsedAny?'partial':'unavailable',received_at:received,served_at:received,cache_hit:false,requested_interval:{start:shipyardEventLocal(month+'-01','00:00'),end_exclusive:shipyardEventLocal(shipyardEventNextMonth(month)+'-01','00:00')},sources:sources.map(({events,...source})=>source),events,event_count:events.length,restrictions:{decision_eligible:false,engine_gates_populated:false,events_clear:null,comprehensive_market_coverage:false,continuous_stream:false,historical_availability:'unknown; retrieval now does not establish prior availability',immutable_ledger_persisted:false,source_revisions_possible:true,exclusions:['company earnings','unscheduled news','Census','DOL weekly claims','Treasury auctions','ISM and private releases'],note:'Every configured source scope was read and parsed, but these schedules do not cover all market events and are not eligible to clear an RRE engine gate. Excluded or unlisted events remain unknown. HTTP Last-Modified/ETag are revision metadata, not first-publication evidence.'}};
  value.snapshot_hash=await shipyardEventHash(JSON.stringify({policy:value.policy,month,sources:value.sources,events}));
  shipyardEventCache.set(month,{created:Date.now(),ttl:value.status==='available_scoped'?300000:60000,value});
  for(const key of shipyardEventCache.keys())if(![shipyardEventMonth(),shipyardEventNextMonth(shipyardEventMonth())].includes(key))shipyardEventCache.delete(key);
  return json(value);
}
