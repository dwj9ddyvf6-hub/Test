import json
import unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from psychology_engine.core import Store
from psychology_engine.adapters import collect
from psychology_engine.evaluation import evaluate
from psychology_engine.patterns import detect,forecast
from test_engine import obs,T

class AuditTests(unittest.TestCase):
    def test_identical_text_distinct_units_and_entities(self):
        s=Store(':memory:')
        s.ingest([obs(text='bullish',units='balance'),obs(text='bullish',units='percent',value=50),obs(text='bullish',entity='OTHER')],T,True)
        self.assertEqual(len(s.snapshot(T,'US_MARKET','1d')['evidence']),2)
        self.assertEqual(len(s.snapshot(T,'OTHER','1d')['evidence']),1);s.close()
    def test_null_and_nonstring_identifiers_rejected(self):
        for key in ('source','item_id','revision','source_family','units','config_version','entity','horizon'):
            for value in (None,'', '  ',12,False):
                s=Store(':memory:')
                with self.assertRaises(ValueError):s.ingest([obs(**{key:value})],T,True)
                s.close()
    def test_late_old_revision_does_not_replace_newer_publication(self):
        s=Store(':memory:');s.ingest([obs()],T,True)
        s.ingest([obs(revision='old',value=-.9,publication_time='2026-10-27T12:00:00Z',first_seen='2026-10-28T13:00:00Z')],'2026-10-28T13:00:00Z',True)
        self.assertEqual(s.snapshot('2026-10-28T13:00:00Z','US_MARKET','1d')['state']['sentiment']['measures']['balance'],.5);s.close()
    def test_malformed_response_is_failure(self):
        class Reader:
            def fetch(self,source):return b'<html>Maintenance</html>'
        for source in ('fed_press','cboe_vix','frbsf_news','wikimedia_attention'):
            s=Store(':memory:');self.assertEqual(collect(s,source,Reader())['status'],'failed');s.close()
    def test_gap_cost_regression(self):
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())[:8]
        for r in rows:r['target']=.01
        with patch('psychology_engine.evaluation.fit_predict',return_value=.01):result=evaluate(rows,min_train=5,cost_bps=5)
        self.assertEqual(result['metrics']['price_only']['n'],3)
        self.assertAlmostEqual(result['metrics']['price_only']['sum_net_return'],.027)
    def test_mixed_entities_and_overflow_rejected(self):
        rows=json.loads(Path('fixtures/evaluation_synthetic.json').read_text())
        rows[0]['entity']='OTHER'
        with self.assertRaises(ValueError):evaluate(rows)
        rows[0]['entity']=rows[1]['entity'];rows[0]['target']=1e308
        with self.assertRaises(ValueError):evaluate(rows)
    def temporal(self,backfilled=False):
        s=Store(':memory:');start=datetime(2026,10,10,12,tzinfo=timezone.utc)
        rows=[]
        for i in range(10):
            t=(start+timedelta(days=i)).isoformat()
            rows.append(obs(source='article',source_family='article',item_id=str(i),event_time=t,publication_time=t,
                            first_seen=t,dimension='attention',units='article_daily_user_pageviews',value=100 if i<7 else 300,max_age_hours=96))
        end=rows[-1]['first_seen']
        if backfilled:
            for r in rows:r['publication_time']=end;r['first_seen']=end
        s.ingest(rows,end,True)
        return s,end
    def test_pattern_and_forecast_have_evidence(self):
        s,end=self.temporal();result=detect(s,end,'US_MARKET','1d')
        att=[p for p in result['patterns'] if p['pattern']=='attention_acceleration'][0]
        self.assertEqual(att['status'],'watch');self.assertEqual(len(att['evidence_ids']),6)
        f=forecast(s,end,'US_MARKET','1d','article','attention','article_daily_user_pageviews')
        self.assertEqual(f['status'],'research_forecast');self.assertGreater(f['walk_forward']['n'],0)
        self.assertFalse(f['orders_allowed']);s.close()
    def test_backfilled_archive_has_no_proxy_backtest(self):
        s,end=self.temporal(True)
        f=forecast(s,end,'US_MARKET','1d','article','attention','article_daily_user_pageviews')
        self.assertEqual(f['walk_forward']['n'],0);s.close()
    def test_single_family_abstention(self):
        s=Store(':memory:');s.ingest([obs()],T,True)
        self.assertEqual(s.snapshot(T,'US_MARKET','1d')['decision']['action'],'abstain_insufficient_source_diversity');s.close()
