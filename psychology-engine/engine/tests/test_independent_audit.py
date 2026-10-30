import json,math,unittest
from psychology_engine.core import Store
from psychology_engine.adapters import collect
from psychology_engine.patterns import detect,forecast

def row(day,source='s',dimension='sentiment',units='balance',value=.1,hour=12,**kw):
    t=f'2026-10-{day:02d}T{hour:02d}:00:00+00:00'
    d=dict(access_status='fixture',source=source,source_family=source,item_id=str(day),revision='1',event_time=t,publication_time=t,first_seen=t,entity='US_MARKET',horizon='1d',dimension=dimension,units=units,value=value,max_age_hours=96,config_version='v1',provenance={'provider_received_at':t,'locally_received_at':t,'extracted_at':t,'source_population':'fixture'})
    d.update(kw)
    if dimension=='price_return':
        d['provenance']['market_context']=dict(instrument_id='US_MARKET',venue='fixture',calendar_version='v1',bar_end=t,bar_closed=True,price_adjustment_policy='none',provider_feed='fixture',quote_or_bar_available_at=t,data_age=0,market_context_version='v1')
    return d

class IndependentAuditTests(unittest.TestCase):
    def test_rss_feed_growth_keeps_item_revision_immutable(self):
        class Reader:
            n=1
            def fetch(self,_):return ('<rss><channel>'+''.join(f'<item><guid>{i}</guid><title>Growth may improve {i}</title><pubDate>Wed, 28 Oct 2026 12:00:00 GMT</pubDate></item>' for i in range(self.n))+'</channel></rss>').encode()
        s=Store(':memory:');reader=Reader()
        self.assertEqual(collect(s,'fed_press',reader)['inserted'],2)
        reader.n=2
        result=collect(s,'fed_press',reader)
        self.assertEqual(result['status'],'ok');self.assertEqual(result['inserted'],2);self.assertEqual(result['duplicates'],2)
        self.assertEqual(s.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],4)
        self.assertEqual(s.db.execute('SELECT COUNT(DISTINCT body_sha256) FROM acquisitions').fetchone()[0],2);s.close()
    def test_stale_aligned_divergence_abstains(self):
        s=Store(':memory:');rows=[row(day,value=.6-i*.1) for i,day in enumerate([1,5,9,20,21,22])]
        rows += [row(day,source='price',dimension='price_return',units='decimal_return',value=.01) for day in [1,5,9]]
        rows += [row(day,source='price',dimension='price_return',units='decimal_return',value=.01,hour=13) for day in [20,21,22]]
        s.ingest(rows,'2026-10-22T14:00:00Z',True)
        p=[x for x in detect(s,'2026-10-22T14:00:00Z','US_MARKET','1d')['patterns'] if x['pattern']=='sentiment_price_divergence']
        self.assertTrue(p);self.assertTrue(all(x['status']=='abstain' for x in p));s.close()
    def test_revisions_do_not_erase_old_origins_or_scores(self):
        s=Store(':memory:');rows=[row(i,dimension='attention',units='article_daily_user_pageviews',value=100+i) for i in range(1,11)]
        s.ingest(rows,'2026-10-10T12:00:00Z',True)
        args=('US_MARKET','1d','s','attention','article_daily_user_pageviews')
        before=forecast(s,'2026-10-10T12:00:00Z',*args)
        for r in rows:
            r['revision']='2';r['publication_time']=r['first_seen']='2026-10-11T12:00:00Z'
            r['provenance'].update({k:r['first_seen'] for k in ('provider_received_at','locally_received_at','extracted_at')});r['value']+=1
        s.ingest(rows,'2026-10-11T12:00:00Z',True)
        after=forecast(s,'2026-10-11T12:00:00Z',*args)
        self.assertEqual(before['walk_forward']['n'],5)
        self.assertEqual(before['walk_forward']['predictions'],after['walk_forward']['predictions']);s.close()
    def test_config_and_population_boundaries_not_scored(self):
        for boundary in ('config','population','model'):
            s=Store(':memory:');rows=[row(i,dimension='attention',units='article_daily_user_pageviews',value=100+i) for i in range(1,11)]
            for r in rows[5:]:
                if boundary=='config':r['config_version']='v2'
                elif boundary=='population':r['provenance']['source_population']='new_population'
                else:r['provenance']['measurement_model_version']='model-v2'
            s.ingest(rows,'2026-10-10T12:00:00Z',True)
            f=forecast(s,'2026-10-10T12:00:00Z','US_MARKET','1d','s','attention','article_daily_user_pageviews')
            self.assertEqual(f['walk_forward']['n'],0)
            self.assertEqual(len(f['walk_forward']['incomparable']),1);s.close()
    def test_stable_aggregation_of_extreme_finite_values(self):
        s=Store(':memory:');s.ingest([row(28,value=1e308,units='custom'),row(28,source='b',value=1e308,units='custom')],'2026-10-28T12:00:00Z',True)
        result=s.snapshot('2026-10-28T12:00:00Z','US_MARKET','1d')
        value=result['state']['sentiment']['measures']['custom'];self.assertTrue(math.isfinite(value));self.assertEqual(value,1e308)
        json.dumps(result,allow_nan=False);s.close()
    def test_incompatible_models_do_not_generate_disagreement(self):
        s=Store(':memory:');a=row(28,value=.5);b=row(28,source='other',value=-.5)
        a['provenance']['measurement_model_version']='a';b['provenance']['measurement_model_version']='b'
        s.ingest([a,b],'2026-10-28T12:00:00Z',True)
        patterns=detect(s,'2026-10-28T12:00:00Z','US_MARKET','1d')['patterns']
        self.assertTrue(all(p['status']=='abstain' for p in patterns if p['pattern']=='source_disagreement'));s.close()
