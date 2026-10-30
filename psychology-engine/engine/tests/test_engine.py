import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from psychology_engine.core import Store, LexiconScorer
from psychology_engine.adapters import PublicReader, parse, collect
from psychology_engine.evaluation import evaluate

T='2026-10-28T12:00:00+00:00'

def obs(**kw):
    r=dict(source='survey_a',item_id='week1',revision='1',event_time=T,publication_time=T,
           first_seen=T,entity='US_MARKET',horizon='1d',dimension='sentiment',value=.5,
           units='balance',source_family='survey_a',access_status='fixture',max_age_hours=24,config_version='test')
    r.update(kw)
    r.setdefault('provenance',dict(provider_received_at=r['first_seen'],locally_received_at=r['first_seen'],extracted_at=r['first_seen'],source_population='Synthetic fixture population',entity_mapping_version='fixture-v1',license_and_retention_policy='Generated fixture'))
    return r

class EngineTests(unittest.TestCase):
    def setUp(self): self.store=Store(':memory:')
    def tearDown(self): self.store.close()
    def snap(self,t=T): return self.store.snapshot(t,'US_MARKET','1d')
    def put(self,rows,received=T): return self.store.ingest(rows,received,historical=True)
    def test_unknown_not_neutral(self):
        self.assertIsNone(self.snap()['state']['sentiment']['measures'])
        self.put([obs(value=None)])
        self.assertEqual(self.snap()['excluded'][0]['reason'],'unknown_value')
    def test_stale_and_unavailable(self):
        self.put([obs(),obs(item_id='2',access_status='unavailable')])
        self.assertEqual(self.snap()['excluded'][0]['reason'],'unavailable')
        self.assertIsNone(self.snap('2026-10-30T12:00:00Z')['state']['sentiment']['measures'])
    def test_future_rejected_atomically(self):
        with self.assertRaises(ValueError): self.put([obs(),obs(item_id='2',event_time='2027-01-01T00:00:00Z')])
        self.assertEqual(len(self.snap()['evidence']),0)
    def test_timezone_required(self):
        with self.assertRaises(ValueError): self.put([obs(event_time='2026-10-28')])
    def test_revision_asof(self):
        self.put([obs()])
        later='2026-10-28T13:00:00Z'
        self.put([obs(revision='2',value=-.5,first_seen=later,publication_time=later)],later)
        self.assertEqual(self.snap()['state']['sentiment']['measures']['balance'],.5)
        self.assertEqual(self.snap(later)['state']['sentiment']['measures']['balance'],-.5)
    def test_first_seen_gates(self):
        self.put([obs(first_seen='2026-10-28T13:00:00Z')],'2026-10-28T13:00:00Z')
        self.assertEqual(len(self.snap()['evidence']),0)
    def test_normal_import_does_not_backdate(self):
        self.store.ingest([obs()],received_at='2026-10-28T13:00:00Z')
        self.assertEqual(len(self.snap()['evidence']),0)
    def test_duplicate_and_collision(self):
        self.put([obs()]); self.assertEqual(self.put([obs()])['duplicates'],1)
        with self.assertRaises(ValueError): self.put([obs(value=.9)])
    def test_syndication(self):
        self.put([obs(text='Markets are bullish'),obs(source='copy',source_family='copy',text='Markets are bullish')])
        self.assertEqual(len(self.snap()['evidence']),1)
        self.assertEqual(self.snap()['excluded'][0]['reason'],'syndicated_duplicate')
    def test_different_units_separate(self):
        self.put([obs(),obs(item_id='2',units='percent',value=50)])
        self.assertEqual(len(self.snap()['state']['sentiment']['measures']),2)
    def test_restart_idempotency(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'test.sqlite')
            s=Store(path);s.ingest([obs()],T,True);s.close()
            s=Store(path);self.assertEqual(s.ingest([obs()],T,True)['duplicates'],1);s.close()
    def test_text_unknown_negation(self):
        scorer=LexiconScorer()
        self.assertIsNone(scorer.score('The meeting starts today')['sentiment'])
        self.assertEqual(scorer.score('not bullish')['sentiment'],-1)
    def test_rss_parser(self):
        body=b'<rss><channel><item><guid>1</guid><title>Growth may improve</title><pubDate>Wed, 28 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        rows=parse('fed_press',body,T)
        self.assertEqual(len(rows),2)
        self.store.ingest(rows,T)
        self.assertEqual(len(self.snap()['evidence']),2)
    def test_vix_conservative_publication(self):
        rows=parse('cboe_vix',b'DATE,OPEN,HIGH,LOW,CLOSE\n10/27/2026,18,19,17,18\n',T)
        self.assertEqual(rows[0]['publication_time'],T)
        self.assertEqual(rows[0]['dimension'],'stress')
    def test_failed_request_bounded_and_logged(self):
        class Failed:
            def fetch(self,source): raise urllib.error.URLError('failed')
        self.assertEqual(collect(self.store,'fed_press',Failed())['status'],'failed')
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM runs').fetchone()[0],1)
        calls=[]
        def fail(*a,**kw): calls.append(1);raise urllib.error.URLError('failed')
        with self.assertRaises(urllib.error.URLError): PublicReader(fail,lambda x:None)._get('https://example.invalid')
        self.assertEqual(len(calls),3)
    def test_no_retry_403(self):
        calls=[]
        def fail(*a,**kw): calls.append(1);raise urllib.error.HTTPError('x',403,'denied',{},None)
        with self.assertRaises(urllib.error.HTTPError): PublicReader(fail,lambda x:None)._get('https://example.invalid')
        self.assertEqual(len(calls),1)
    def test_evaluation_maturity_and_leakage(self):
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())
        result=evaluate(rows,min_train=5)
        self.assertGreater(result['metrics']['price_only']['n'],0)
        for p in result['predictions']: self.assertLess(p['train_last_label_end'],p['as_of'])
        rows[0]['feature_available_at']='2030-01-01T00:00:00Z'
        with self.assertRaises(ValueError): evaluate(rows,min_train=5)
    def test_nonfinite_input_rejected(self):
        for value in (float('nan'), float('inf')):
            with self.assertRaises(ValueError): self.put([obs(value=value)])
    def test_snapshot_repeatable(self):
        self.put([obs()])
        self.assertEqual(self.snap()['snapshot_id'],self.snap()['snapshot_id'])
    def test_horizon_isolation(self):
        self.put([obs(horizon='5d')])
        self.assertEqual(len(self.snap()['evidence']),0)
    def test_rate_limit_and_retry_after(self):
        calls=[]; sleeps=[]
        def fail(*a,**kw):
            calls.append(1)
            raise urllib.error.HTTPError('x',429,'slow',{'Retry-After':'120'},None)
        with self.assertRaises(urllib.error.HTTPError): PublicReader(fail,sleeps.append)._get('https://example.invalid')
        self.assertEqual(len(calls),1)
    def test_vix_collection_idempotent_and_revision(self):
        class Reader:
            value=18
            def fetch(self,source):
                return f'DATE,OPEN,HIGH,LOW,CLOSE\n10/27/2026,18,19,17,{self.value}\n'.encode()
        reader=Reader()
        self.assertEqual(collect(self.store,'cboe_vix',reader)['inserted'],1)
        self.assertEqual(collect(self.store,'cboe_vix',reader)['inserted'],0)
        reader.value=19
        self.assertEqual(collect(self.store,'cboe_vix',reader)['inserted'],1)
        reader.value=18
        self.assertEqual(collect(self.store,'cboe_vix',reader)['inserted'],1)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],3)
    def test_decision_no_orders(self):
        self.assertFalse(self.snap()['decision']['orders_allowed'])
        self.assertEqual(self.snap()['decision']['entry_authority'],'Tensor')

if __name__=='__main__': unittest.main()
