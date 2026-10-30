"""Immutable observations and conservative point-in-time feature assembly."""
import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from typing import Protocol

DIMENSIONS = ('sentiment', 'attention', 'uncertainty', 'disagreement', 'positioning', 'stress', 'narrative_change')


def utc(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('timezone required')
    return d.astimezone(timezone.utc)


def stamp(value):
    return utc(value).isoformat()


def stable_mean(values):
    values=list(values)
    if not values: raise ValueError('empty mean')
    if not all(math.isfinite(v) for v in values):raise ValueError('nonfinite aggregation input')
    scale=max(abs(v) for v in values)
    if scale==0:return 0.0
    result=max(-1.0,min(1.0,math.fsum(v/scale for v in values)/len(values)))*scale
    if not math.isfinite(result):raise ValueError('nonfinite aggregate')
    return result


def now():
    return datetime.now(timezone.utc).isoformat()


class NLPProvider(Protocol):
    version: str
    def score(self, text: str) -> dict: ...


class LexiconScorer:
    version = 'transparent-en-v1'
    positive = {'gain', 'growth', 'optimistic', 'bullish', 'improve', 'strong'}
    negative = {'loss', 'fear', 'bearish', 'weak', 'panic', 'decline'}
    uncertain = {'may', 'might', 'uncertain', 'risk', 'possibly', 'unknown'}

    def score(self, text):
        words = re.findall(r'[a-z]+', text.lower())
        matches = []
        for i, word in enumerate(words):
            val = 1 if word in self.positive else -1 if word in self.negative else 0
            if val:
                if any(w in {'not', 'never', 'no'} for w in words[max(0, i-3):i]):
                    val *= -1
                matches.append(val)
        return {'sentiment': sum(matches)/len(matches) if matches else None,
                'uncertainty': sum(w in self.uncertain for w in words)/len(words) if words else None,
                'matched_tokens': len(matches), 'model': self.version}


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        existing=self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='observations'").fetchone()
        if existing and self.db.execute('PRAGMA user_version').fetchone()[0] != 3:
            self.db.close()
            raise ValueError('legacy database schema: export and reimport into a new v3 database; no automatic rewriting')
        self.db.executescript('''
        PRAGMA user_version=3;
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS observations (
          id TEXT PRIMARY KEY, source TEXT, item_id TEXT, revision TEXT,
          event_time TEXT, publication_time TEXT, first_seen TEXT,
          entity TEXT, horizon TEXT, dimension TEXT, value REAL, units TEXT,
          source_family TEXT, access_status TEXT, url TEXT, text TEXT,
          fingerprint TEXT, max_age_hours REAL, config_version TEXT,
          ingest_time TEXT, available_at TEXT, provenance TEXT, UNIQUE(source,item_id,revision,dimension,entity,horizon,units));
        CREATE TABLE IF NOT EXISTS acquisitions (source TEXT, received_at TEXT, body_sha256 TEXT, bytes INTEGER, PRIMARY KEY(source,received_at,body_sha256));
        CREATE TABLE IF NOT EXISTS runs (time TEXT, source TEXT, status TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, as_of TEXT, payload TEXT);
        ''')

    def close(self):
        self.db.close()

    def ingest(self, rows, received_at=None, historical=False):
        """Historical mode trusts explicitly supplied first_seen; never infer it."""
        received_at = stamp(received_at or now())
        result = {'inserted': 0, 'duplicates': 0}
        with self.db:
            for item in rows:
                r = dict(item)
                required = ['source','item_id','revision','event_time','publication_time','entity',
                            'horizon','dimension','units','source_family','access_status','max_age_hours','config_version']
                for k in required:
                    if k not in r or r[k] is None or (k != 'max_age_hours' and (not isinstance(r[k],str) or not r[k].strip())):
                        raise ValueError('missing '+k)
                r['first_seen'] = stamp(r['first_seen']) if historical else received_at
                raw_provenance=r.get('provenance') or {}
                if isinstance(raw_provenance,str): raw_provenance=json.loads(raw_provenance)
                if not isinstance(raw_provenance,dict): raise ValueError('provenance must be an object')
                provenance=dict(raw_provenance)
                for clock in ('provider_received_at','locally_received_at','extracted_at'):
                    if historical and not provenance.get(clock): raise ValueError('historical provenance requires '+clock)
                    if not historical and clock=='provider_received_at' and not provenance.get(clock):
                        provenance['provider_received_at_basis']='local_import_receipt_upper_bound_no_vendor_clock'
                    provenance[clock]=stamp(provenance.get(clock) or received_at)
                    if utc(provenance[clock])>utc(received_at): raise ValueError('future provenance clock')
                if not historical:
                    provenance['locally_received_at']=received_at
                    provenance['extracted_at']=received_at
                if utc(provenance['extracted_at'])<utc(provenance['locally_received_at']): raise ValueError('extraction before local receipt')
                if utc(provenance['locally_received_at'])<utc(provenance['provider_received_at']): raise ValueError('local receipt before provider receipt')
                for k in ('event_time','publication_time'):
                    r[k] = stamp(r[k])
                if any(utc(r[k]) > utc(received_at) for k in ('event_time','publication_time','first_seen')):
                    raise ValueError('future observation timestamp')
                if utc(r['publication_time']) > utc(r['first_seen']):
                    raise ValueError('first_seen before publication')
                if r['dimension'] not in DIMENSIONS + ('price_return',):
                    raise ValueError('unsupported dimension')
                if isinstance(r['max_age_hours'],bool): raise ValueError('boolean freshness threshold')
                r['max_age_hours'] = float(r['max_age_hours'])
                if not math.isfinite(r['max_age_hours']) or r['max_age_hours'] <= 0:
                    raise ValueError('invalid freshness threshold')
                if isinstance(r.get('value'),bool): raise ValueError('boolean measurement')
                r['value'] = None if r.get('value') in (None, '') else float(r['value'])
                if r['value'] is not None and not math.isfinite(r['value']):
                    raise ValueError('nonfinite value')
                if r['value'] is not None:
                    if r['units'] in ('balance','lexicon_score_v1') and not -1<=r['value']<=1: raise ValueError('score out of range')
                    if r['units'] in ('uncertainty_token_fraction','fraction') and not 0<=r['value']<=1: raise ValueError('fraction out of range')
                    if r['units']=='VIX_index_points' and r['value']<0: raise ValueError('negative VIX')
                    if r['units']=='article_daily_user_pageviews' and (r['value']<0 or not r['value'].is_integer()): raise ValueError('invalid count')
                r['text'] = r.get('text', '')
                if not isinstance(r['text'],str) or not isinstance(r.get('url',''),str): raise ValueError('text and URL must be strings')
                r['url'] = r.get('url', '')
                # Across syndicated copies, deduplicate identical normalized text.
                content = re.sub(r'\s+', ' ', r['text'].lower()).strip()
                content = content or '|'.join(str(r[k]) for k in ('source_family','event_time','dimension','value','units'))
                r['fingerprint'] = hashlib.sha256(content.encode()).hexdigest()
                keys = ('source','item_id','revision','dimension','entity','horizon','units')
                r['id'] = hashlib.sha256(json.dumps([r[k] for k in keys]).encode()).hexdigest()
                r['ingest_time'] = received_at
                r['available_at']=max([r['publication_time'],r['first_seen']]+[provenance[k] for k in ('provider_received_at','locally_received_at','extracted_at')],key=utc)
                population=provenance.get('source_population')
                if population is not None and (not isinstance(population,str) or not population.strip()): raise ValueError('invalid source population')
                if r['dimension']=='positioning' and provenance.get('measurement_kind') not in ('reported_net_exposure','published_short_interest','reported_futures_position'):
                    raise ValueError('positioning requires verified measurement kind; short-sale volume and unsigned OI are not positions')
                if r['dimension']=='price_return':
                    context=provenance.get('market_context') or {}
                    required_context=('instrument_id','venue','calendar_version','bar_end','bar_closed','price_adjustment_policy','provider_feed','quote_or_bar_available_at','data_age','market_context_version')
                    if any(k not in context or context[k] is None for k in required_context): raise ValueError('missing market context')
                    for key in ('instrument_id','venue','calendar_version','price_adjustment_policy','provider_feed','market_context_version'):
                        if not isinstance(context[key],str) or not context[key].strip(): raise ValueError('invalid market context identifier')
                    if isinstance(context['data_age'],bool) or not isinstance(context['data_age'],(int,float)) or not math.isfinite(context['data_age']) or context['data_age']<0: raise ValueError('invalid market data age')
                    if context['bar_closed'] is not True: raise ValueError('unclosed price bar')
                    if context['instrument_id']!=r['entity']: raise ValueError('market context instrument mismatch')
                    if utc(context['bar_end'])!=utc(r['event_time']): raise ValueError('event time must be closed bar end')
                    if utc(context['quote_or_bar_available_at'])<utc(context['bar_end']): raise ValueError('bar available before close')
                    if utc(context['quote_or_bar_available_at'])>utc(received_at): raise ValueError('future bar availability')
                    r['available_at']=max(r['available_at'],stamp(context['quote_or_bar_available_at']),key=utc)
                provenance.setdefault('source_population',None)
                provenance.setdefault('entity_mapping_version',None)
                provenance.setdefault('license_and_retention_policy',None)
                provenance.setdefault('missing_reason','Unprovided provenance remains unknown; descriptive research only')
                r['provenance']=json.dumps(provenance,sort_keys=True)
                columns = [x[1] for x in self.db.execute('PRAGMA table_info(observations)')]
                existing = self.db.execute('SELECT * FROM observations WHERE id=?',(r['id'],)).fetchone()
                if existing:
                    # Same revision with changed values is a provider error, not a silent overwrite.
                    compare = [k for k in columns if k not in ('first_seen','ingest_time','available_at','provenance')]
                    prior_provenance=json.loads(existing['provenance'])
                    ignored_clocks={'provider_received_at','locally_received_at','extracted_at'}
                    metadata_changed={k:v for k,v in prior_provenance.items() if k not in ignored_clocks}!={k:v for k,v in provenance.items() if k not in ignored_clocks}
                    if any(existing[k] != r[k] for k in compare) or metadata_changed:
                        raise ValueError('revision collision: changed payload needs a new revision')
                    result['duplicates'] += 1
                else:
                    self.db.execute('INSERT INTO observations VALUES ('+','.join('?' for _ in columns)+')', [r[k] for k in columns])
                    result['inserted'] += 1
        return result

    def record_acquisition(self,source,received_at,body):
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO acquisitions VALUES (?,?,?,?)',(source,stamp(received_at),hashlib.sha256(body).hexdigest(),len(body)))

    def log_run(self, source, status, detail):
        with self.db:
            self.db.execute('INSERT INTO runs VALUES (?,?,?,?)', (now(),source,status,detail))

    def snapshot(self, as_of, entity, horizon):
        as_of = stamp(as_of)
        # Publication and first observation are both necessary. Imported historical
        # vintages are explicitly trusted by the operator, not verified by this query.
        rows = [dict(r) for r in self.db.execute('''SELECT * FROM observations
          WHERE first_seen<=? AND publication_time<=? AND event_time<=? AND available_at<=?
          AND entity=? AND horizon=? ORDER BY publication_time,first_seen,ingest_time,id''',
          (as_of,as_of,as_of,as_of,entity,horizon))]
        latest = {}
        for r in rows:
            latest[(r['source'],r['item_id'],r['dimension'],r['entity'],r['horizon'],r['units'])] = r
        evidence, excluded, seen = [], [], set()
        for r in latest.values():
            age = (utc(as_of)-utc(r['event_time'])).total_seconds()/3600
            reason = None
            if r['access_status'] not in ('public', 'licensed', 'user_import', 'fixture'):
                reason = 'unavailable'
            elif age > r['max_age_hours']:
                reason = 'stale'
            elif r['value'] is None:
                reason = 'unknown_value'
            key = (r['fingerprint'],r['dimension'],r['units'],r['entity'],r['horizon'])
            if not reason and key in seen:
                reason = 'syndicated_duplicate'
            if reason:
                excluded.append({'id':r['id'],'source':r['source'],'reason':reason})
            else:
                seen.add(key)
                evidence.append(r)
        state = {}
        for dimension in DIMENSIONS:
            selected = [r for r in evidence if r['dimension']==dimension]
            # No mean across heterogeneous units; source-family means prevent volume dominance.
            groups = {}
            for r in selected:
                population=json.loads(r['provenance']).get('source_population') or 'UNKNOWN_POPULATION'
                groups.setdefault((r['units'],population),{}).setdefault(r['source_family'],[]).append(r['value'])
            population_measures = [{'units':unit,'population':population,'value':stable_mean(stable_mean(v) for v in families.values())} for (unit,population),families in groups.items()]
            populations={p['population'] for p in population_measures}
            measures={p['units']:p['value'] for p in population_measures} if len(populations)==1 else {}
            if 'UNKNOWN_POPULATION' in populations: measures={}
            state[dimension] = {'measures': measures or None,'population_measures':population_measures, 'source_family_count':len({r['source_family'] for r in selected}),
                                'observations':len(selected),
                                'coverage':'unknown' if not selected else 'single_family' if len({r['source_family'] for r in selected})<2 else 'multiple_families_unverified_independence'}
        health={}
        for run in self.db.execute('SELECT * FROM runs WHERE time<=? ORDER BY time',(as_of,)):
            health[run['source']]={'status':run['status'],'checked_at':run['time'],'detail':run['detail']}
        payload = {'schema':'psychology-snapshot-v3','source_health':health,'as_of':as_of,'entity':entity,'horizon':horizon,
                   'state':state,'evidence':evidence,'excluded':excluded,
                   'decision':{'mode':'research_advisory','entry_authority':'Tensor','orders_allowed':False,
                   'action':('abstain_insufficient_evidence' if not evidence else 'abstain_insufficient_source_diversity' if len({r['source_family'] for r in evidence})<2 else 'review_evidence'),
                   'minimum_source_families':2,
                   'observed_source_families':len({r['source_family'] for r in evidence}),
                   'predictive_validation':'not_established','reason':'No calibrated trading mapping is enabled.'}}
        ident = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?,?)',(ident,as_of,json.dumps(payload)))
        return dict(payload,snapshot_id=ident)
