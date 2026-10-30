import json
import unittest
from datetime import datetime,timedelta
from psychology_engine.core import Store
from psychology_engine.adapters import parse,source_config,endpoint
from psychology_engine.evaluation import evaluate

T='2026-10-28T12:00:00+00:00'
class AdditionalSourceTests(unittest.TestCase):
    def test_frbsf_publication_not_inferred_from_daily_date(self):
        rows=parse('frbsf_news',b'date,News Sentiment\n2026-10-26,0.12\n2026-10-27,NA\n',T)
        self.assertEqual(rows[0]['publication_time'],T)
        self.assertIsNone(rows[1]['value'])
        s=Store(':memory:');s.ingest(rows,T,True)
        self.assertEqual(len(s.snapshot('2026-10-27T12:00:00Z','US_MARKET','1d')['evidence']),0)
        self.assertEqual(len(s.snapshot(T,'US_MARKET','1d')['evidence']),1);s.close()
    def test_frbsf_schema_rejects_unknown_numeric_columns(self):
        with self.assertRaises(ValueError):parse('frbsf_news',b'date,unrelated\n2026-10-26,50\n',T)
    def wikibody(self,**kw):
        item=dict(project='en.wikipedia',article='Stock_market',access='all-access',agent='user',timestamp='2026102700',views=900)
        item.update(kw)
        return json.dumps({'items':[item]}).encode()
    def test_wikimedia_topic_entity_and_complete_day(self):
        row=parse('wikimedia_attention',self.wikibody(),T)[0]
        self.assertEqual(row['entity'],'TOPIC:Stock_market')
        self.assertEqual(row['event_time'],'2026-10-28T00:00:00+00:00')
        self.assertEqual(row['publication_time'],T)
        self.assertEqual(row['dimension'],'attention')
    def test_wikimedia_population_and_count_validation(self):
        for kw in ({'agent':'spider'},{'views':-2},{'views':True},{'article':'Other'}):
            with self.assertRaises(ValueError):parse('wikimedia_attention',self.wikibody(**kw),T)
    def test_incomplete_day_rejected_on_ingestion(self):
        rows=parse('wikimedia_attention',self.wikibody(timestamp='2026102800'),T)
        s=Store(':memory:')
        with self.assertRaises(ValueError):s.ingest(rows,T,True)
        s.close()
    def test_wikimedia_window_uses_completed_utc_days(self):
        self.assertTrue(endpoint(source_config()['wikimedia_attention'],T).endswith('/20261021/20261027'))
    def test_delayed_labels_not_used(self):
        from pathlib import Path
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())
        for r in rows[:20]:r['label_available_at']='2027-01-01T00:00:00Z'
        result=evaluate(rows,min_train=5)
        for p in result['predictions']:
            self.assertLess(p['train_last_label_available_at'],p['as_of'])
        self.assertGreaterEqual(result['predictions'][0]['as_of'],rows[25]['as_of'])
    def test_nonoverlapping_tests(self):
        from pathlib import Path
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())
        for r in rows:
            r['label_end']=(datetime.fromisoformat(r['as_of'])+timedelta(days=3)).isoformat()
            r['label_available_at']=r['label_end']
        result=evaluate(rows,min_train=5)
        predictions=result['predictions']
        self.assertTrue(predictions)
        for a,b in zip(predictions,predictions[1:]):self.assertGreaterEqual(b['as_of'],a['label_end'])
    def test_unknown_availability_rejected(self):
        from pathlib import Path
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())
        del rows[0]['label_available_at']
        with self.assertRaises(ValueError):evaluate(rows)
