import json
from pathlib import Path
import unittest
from psychology_engine.core import Store
from psychology_engine.contract import envelope
from psychology_engine.patterns import detect
from test_engine import obs,T

class ContractTests(unittest.TestCase):
    def test_extraction_completion_gates_snapshot_and_patterns(self):
        s=Store(':memory:');r=obs()
        r['provenance']['extracted_at']='2026-10-28T13:00:00Z'
        s.ingest([r],'2026-10-28T13:00:00Z',True)
        self.assertEqual(s.snapshot(T,'US_MARKET','1d')['evidence'],[])
        self.assertTrue(all(x['status']=='abstain' for x in detect(s,T,'US_MARKET','1d')['patterns']))
        self.assertEqual(len(s.snapshot('2026-10-28T13:00:00Z','US_MARKET','1d')['evidence']),1);s.close()
    def test_provider_receipt_after_cutoff(self):
        s=Store(':memory:');r=obs(first_seen='2026-10-28T13:00:00Z')
        s.ingest([r],'2026-10-28T13:00:00Z',True)
        self.assertEqual(s.snapshot(T,'US_MARKET','1d')['evidence'],[]);s.close()
    def test_historical_missing_clock_rejected(self):
        s=Store(':memory:');r=obs();del r['provenance']['extracted_at']
        with self.assertRaises(ValueError):s.ingest([r],T,True)
        s.close()
    def test_unclosed_price_bar_rejected(self):
        s=Store(':memory:');r=obs(dimension='price_return',units='decimal_return',value=.01)
        r['provenance']['market_context']=dict(instrument_id='US_MARKET',venue='synthetic',calendar_version='v1',bar_end=T,bar_closed=False,price_adjustment_policy='synthetic',provider_feed='fixture',quote_or_bar_available_at=T,data_age=0,market_context_version='v1')
        with self.assertRaises(ValueError):s.ingest([r],T,True)
        r['provenance']['market_context']['bar_closed']=True
        self.assertEqual(s.ingest([r],T,True)['inserted'],1);s.close()
    def test_short_sale_volume_not_position(self):
        s=Store(':memory:');r=obs(dimension='positioning',units='shares',value=50)
        r['provenance']['measurement_kind']='daily_short_sale_volume'
        with self.assertRaises(ValueError):s.ingest([r],T,True)
        s.close()
    def test_contract_output_fields_and_replay_clock(self):
        s=Store(':memory:');s.ingest([obs()],T,True)
        result=envelope(s.snapshot(T,'US_MARKET','1d'),'2026-10-28T14:00:00Z')
        contract=json.loads(Path('docs/research_companion/engine_contract.json').read_text())
        self.assertTrue(set(contract['output_contract']['required']).issubset(result))
        self.assertTrue(result['replay_only']);self.assertTrue(result['advisory']['not_an_order'])
        self.assertEqual(result['available_at'],'2026-10-28T14:00:00Z')
        self.assertEqual(result['forecast_distributions'],[]);s.close()
    def test_populations_not_silently_pooled(self):
        s=Store(':memory:');a=obs();b=obs(source='other',source_family='other',value=-.5)
        b['provenance']['source_population']='Other population'
        s.ingest([a,b],T,True);state=s.snapshot(T,'US_MARKET','1d')['state']['sentiment']
        self.assertIsNone(state['measures']);self.assertEqual(len(state['population_measures']),2);s.close()
    def test_100_duplicate_urls_do_not_strengthen_evidence(self):
        s=Store(':memory:')
        rows=[obs(source='copy'+str(i),source_family='copy'+str(i),text='Original bullish claim',url='https://example.org/'+str(i)) for i in range(100)]
        s.ingest(rows,T,True);snapshot=s.snapshot(T,'US_MARKET','1d')
        self.assertEqual(len(snapshot['evidence']),1)
        self.assertEqual(snapshot['decision']['observed_source_families'],1);s.close()
    def test_semantic_provenance_change_requires_revision(self):
        s=Store(':memory:');r=obs();s.ingest([r],T,True)
        r['provenance']['source_population']='Different population'
        with self.assertRaises(ValueError):s.ingest([r],T,True)
        s.close()
