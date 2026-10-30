"""Small public-source adapter set. No credentials, browser scraping or redirects."""
import csv
import hashlib
import io
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from .core import LexiconScorer, now
from .network import check as check_network

SOURCES = {
 'fed_press': {'url':'https://www.federalreserve.gov/feeds/press_all.xml', 'max_age_hours':168,
               'kind':'institutional_communication', 'cadence':'event_driven'},
 'cboe_vix': {'url':'https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv',
              'max_age_hours':96,'kind':'option_implied_risk_proxy','cadence':'daily'},
}
SOURCES.update({
 'frbsf_news': {'url':'https://www.frbsf.org/wp-content/uploads/news-sentiment-chart-2.csv',
                'max_age_hours':240, 'kind':'news_tone_index', 'cadence':'weekly_release_daily_observations'},
 'wikimedia_attention': {'url':'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Stock_market/daily/{start}/{end}',
                         'max_age_hours':96, 'kind':'article_pageviews_attention', 'cadence':'daily',
                         'entity':'TOPIC:Stock_market', 'lookback_days':7}
})
CONFIG_VERSION = '2026-10-30-v3'


def source_config(path=None):
    policies=json.loads(Path(__file__).with_name('source_policies.json').read_text())
    configs = {k:dict(v,config_version=CONFIG_VERSION,source_policy=policies[k],persistent_use_authorized=False) for k,v in SOURCES.items()}
    if path:
        overrides=json.loads(Path(path).read_text())
        for name,value in overrides.items():
            if name not in configs or not isinstance(value,dict) or not value.get('config_version'):
                raise ValueError('known source and explicit config_version required')
            configs[name].update(value)
    for value in configs.values():
        url=urllib.parse.urlparse(value['url'])
        if url.scheme!='https' or url.username or url.password or url.query:
            raise ValueError('public HTTPS endpoint without credentials or query required')
    return configs


def endpoint(config, collected_at=None):
    if '{start}' not in config['url']:
        return config['url']
    end=datetime.fromisoformat((collected_at or now()).replace('Z','+00:00')).astimezone(timezone.utc)-timedelta(days=1)
    days=int(config.get('lookback_days',7))
    if not 1<=days<=31: raise ValueError('lookback must be 1..31 days')
    start=end-timedelta(days=days-1)
    return config['url'].format(start=start.strftime('%Y%m%d'),end=end.strftime('%Y%m%d'))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise ValueError('redirect requires separately reviewed endpoint')


class PublicReader:
    def __init__(self, opener=None, sleeper=time.sleep, interval=2, retries=2, configs=None):
        if not 0 <= retries <= 3 or not 0 <= interval <= 60:
            raise ValueError('invalid bounded retry/rate settings')
        self.opener = opener or urllib.request.build_opener(NoRedirect()).open
        self.sleep, self.interval, self.retries = sleeper, interval, retries
        self.last = None
        self.configs = configs or source_config()

    def fetch(self, source):
        url = endpoint(self.configs[source])
        # Respect managed environment network policy before making a request.
        # This deployment policy is an application preflight, not a grant against
        # a managed sidecar. Managed environments always use their system snapshot.
        managed=Path('/etc/codex/network-policy.json')
        policy_path=str(managed) if managed.exists() else self.configs[source].get('deployment_policy_path','/etc/psychology-engine/network-policy.json')
        check_network(url,policy_path)
        ua=self.configs[source].get('user_agent')
        if source=='wikimedia_attention' and (not isinstance(ua,str) or not ('https://' in ua or '@' in ua)):
            raise PermissionError('Wikimedia requires operator-supplied public contact User-Agent for deployment')
        return self._get(url,user_agent=ua)

    def _get(self, url,user_agent=None):
        for attempt in range(self.retries+1):
            if self.last is not None:
                self.sleep(max(0,self.interval-(time.monotonic()-self.last)))
            self.last = time.monotonic()
            try:
                req = urllib.request.Request(url,headers={'User-Agent':user_agent or 'PsychologyEngineResearch/0.4.1','Accept':'text/csv, application/xml, text/xml'})
                with self.opener(req,timeout=15) as response:
                    body = response.read(8_000_001)
                    if len(body)>8_000_000:
                        raise ValueError('response exceeds size limit')
                    return body
            except urllib.error.HTTPError as e:
                if e.code not in (429,500,502,503,504) or attempt==self.retries:
                    raise
                # If server requests a longer pause than this bounded run permits, stop.
                retry_after = e.headers.get('Retry-After') if e.headers else None
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = (parsedate_to_datetime(retry_after)-datetime.now(timezone.utc)).total_seconds()
                    if delay > 60:
                        raise
                    self.sleep(max(0,delay))
                else:
                    self.sleep(min(2**attempt,60))
            except (urllib.error.URLError,TimeoutError):
                if attempt==self.retries:
                    raise
                self.sleep(min(2**attempt,60))


def parse(source, body, received_at=None, configs=None):
    received_at = received_at or now()
    config = (configs or source_config())[source]
    base = {'source':source,'source_family':source,'access_status':'public','entity':config.get('entity','US_MARKET'),
            'horizon':'1d','max_age_hours':config['max_age_hours'],'config_version':config['config_version'],
            'first_seen':received_at,'url':endpoint(config,received_at)}
    base['provenance']={'provider_received_at':received_at,'locally_received_at':received_at,'extracted_at':received_at,
                        'provider_received_at_basis':'direct_client_receipt_upper_bound_no_vendor_clock',
                        'source_population':config['source_policy']['original_observation'],'entity_mapping_version':config['config_version'],
                        'raw_content_hash':None,
                        'original_url':base['url'],'provider_id':source,'publisher':source,
                        'publication_time_basis':'publisher_RSS_timestamp' if source=='fed_press' else 'collection_upper_bound_unknown_source_release',
                        'license_and_retention_policy':config['source_policy']['license_and_redistribution'],
                        'publication_cadence':config['cadence'],
                        'source_access_status':config['source_policy']['access_status'],
                        'usage_scope':'bounded_research_probe_only' if not config.get('persistent_use_authorized') else 'operator_reviewed_scope',
                        'measurement_model_version':LexiconScorer.version if source=='fed_press' else 'publisher_measurement_version_unverified',
                        'missing_reason':'Public endpoint access is not a general redistribution or production license'}
    rows = []
    if source=='fed_press':
        scorer = LexiconScorer()
        root=ET.fromstring(body)
        if root.tag!='rss' or root.find('channel') is None: raise ValueError('malformed RSS response')
        items=root.findall('./channel/item')
        if not items: raise ValueError('empty RSS response requires review')
        for item in items:
            publication = parsedate_to_datetime(item.findtext('pubDate')).isoformat()
            title = item.findtext('title') or ''
            item_id = item.findtext('guid') or item.findtext('link') or title
            canonical=ET.canonicalize(ET.tostring(item,encoding='unicode').strip(),strip_text=True)
            item_hash=hashlib.sha256(canonical.encode()).hexdigest()
            item_provenance=dict(base['provenance'],raw_content_hash=item_hash,raw_content_hash_basis='canonical_RSS_item')
            revision = hashlib.sha256((item_hash+config['config_version']).encode()).hexdigest()
            scores = scorer.score(title)
            for dim in ('sentiment','uncertainty'):
                rows.append(dict(base,provenance=item_provenance,item_id=item_id,revision=revision,event_time=publication,
                                 publication_time=publication,dimension=dim,value=scores[dim],
                                 units='lexicon_score_v1' if dim=='sentiment' else 'uncertainty_token_fraction',text=title))
    elif source=='cboe_vix':
        # Historical close dates have no verified release timestamps. Conservatively
        # set publication/availability to retrieval time, preventing historical leakage.
        reader=csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
        if not reader.fieldnames or not {'DATE','CLOSE'}.issubset(reader.fieldnames): raise ValueError('malformed VIX response')
        for row in reader:
            date = datetime.strptime(row['DATE'],'%m/%d/%Y').replace(tzinfo=timezone.utc).isoformat()
            value = float(row['CLOSE'])
            rows.append(dict(base,item_id=row['DATE'],revision=str(value),event_time=date,
                             publication_time=received_at,dimension='stress',value=value,units='VIX_index_points',text=''))
    elif source=='frbsf_news':
        reader=csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
        # Explicit aliases permit common official chart exports, not arbitrary numeric columns.
        headers={h.strip().lower():h for h in (reader.fieldnames or [])}
        date_key=next((headers[k] for k in ('date','observation_date') if k in headers),None)
        value_key=next((headers[k] for k in ('news sentiment','news_sentiment','news sentiment index','sentiment') if k in headers),None)
        if not date_key or not value_key: raise ValueError('unrecognized FRBSF schema')
        for row in reader:
            raw_date=row[date_key].strip()
            date=None
            for fmt in ('%Y-%m-%d','%m/%d/%Y','%m/%d/%y'):
                try:
                    date=datetime.strptime(raw_date,fmt).replace(tzinfo=timezone.utc).isoformat();break
                except ValueError: pass
            if date is None: raise ValueError('unrecognized FRBSF date')
            raw=row[value_key].strip()
            value=None if raw in ('','NA','N/A','.') else float(raw)
            rows.append(dict(base,item_id=date,revision=str(value),event_time=date,
                             publication_time=received_at,dimension='sentiment',value=value,
                             units='FRBSF_news_sentiment_index',text=''))
    elif source=='wikimedia_attention':
        data=json.loads(body)
        if not isinstance(data.get('items'),list): raise ValueError('missing Wikimedia items')
        for item in data['items']:
            if item.get('agent')!='user' or item.get('access')!='all-access' or item.get('project')!='en.wikipedia':
                raise ValueError('unexpected Wikimedia population')
            if item.get('article')!='Stock_market': raise ValueError('unexpected Wikimedia article')
            date=datetime.strptime(str(item['timestamp']),'%Y%m%d%H').replace(tzinfo=timezone.utc)
            views=item['views']
            if isinstance(views,bool) or not isinstance(views,int) or views<0: raise ValueError('invalid pageview count')
            # Daily aggregate only exists after its UTC day has completed; publication
            # timestamp is not provided, so availability is conservatively retrieval.
            event_end=date+timedelta(days=1)
            rows.append(dict(base,item_id=str(item['timestamp']),revision=str(views),
                             event_time=event_end.isoformat(),publication_time=received_at,
                             dimension='attention',value=views,units='article_daily_user_pageviews',text=''))
    else:
        raise ValueError('unsupported source')
    for r in rows:
        if source!='fed_press':
            content={k:r[k] for k in ('source','item_id','event_time','dimension','value','units')}
            r['provenance']=dict(base['provenance'],raw_content_hash=hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest(),raw_content_hash_basis='canonical_source_row')
    if not rows: raise ValueError('empty source response requires review')
    return rows


def collect(store, source, reader=None, configs=None):
    try:
        body = (reader or PublicReader(configs=configs)).fetch(source)
        received_at=now()
        store.record_acquisition(source,received_at,body)
        rows = parse(source,body,received_at,configs=configs)
        if source in ('cboe_vix','frbsf_news','wikimedia_attention'):
            changed = []
            for r in rows:
                previous = store.db.execute('SELECT value,config_version FROM observations WHERE source=? AND item_id=? AND dimension=? AND entity=? AND horizon=? AND units=? ORDER BY first_seen DESC, ingest_time DESC LIMIT 1', (r['source'],r['item_id'],r['dimension'],r['entity'],r['horizon'],r['units'])).fetchone()
                if previous is None or previous['value'] != r['value'] or previous['config_version'] != r['config_version']:
                    r['revision'] = str(r['value']) + '@' + r['first_seen']
                    changed.append(r)
            rows = changed
        result = store.ingest(rows)
        store.log_run(source,'ok',json.dumps(result))
        return {'source':source,'status':'ok',**result}
    except Exception as exc:
        # Do not persist remote error bodies, credentials or request headers.
        store.log_run(source,'failed',type(exc).__name__)
        return {'source':source,'status':'failed','error_type':type(exc).__name__}
