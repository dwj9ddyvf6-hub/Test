"""Independent desired-behavior regression tests. Offline; no HTTP is performed.

Run from the implementation checkout:
  PYTHONPATH=. python -m unittest discover -s ../audit -p test_independent_regressions.py -v
Failures on v0.3 identify confirmed audit findings, not expected-success checks.
"""
import json
import math
import unittest
from psychology_engine.core import Store
from psychology_engine.adapters import collect
from psychology_engine.patterns import detect, forecast


def row(day, source='s', dimension='sentiment', units='balance', value=.1, hour=12, **kw):
    t=f'2026-10-{day:02d}T{hour:02d}:00:00+00:00'
    d=dict(access_status='fixture',source=source,source_family=source,item_id=str(day),revision='1',
           event_time=t,publication_time=t,first_seen=t,entity='US_MARKET',horizon='1d',
           dimension=dimension,units=units,value=value,max_age_hours=96,config_version='v1',
           provenance={'provider_received_at':t,'locally_received_at':t,'extracted_at':t,'source_population':'fixture'})
    d.update(kw)
    if dimension=='price_return':
        d['provenance']['market_context']=dict(instrument_id='US_MARKET',venue='fixture',calendar_version='v1',
            bar_end=t,bar_closed=True,price_adjustment_policy='none',provider_feed='fixture',
            quote_or_bar_available_at=t,data_age=0,market_context_version='v1')
    return d


class IndependentRegressions(unittest.TestCase):
    def setUp(self): self.s=Store(':memory:')
    def tearDown(self): self.s.close()

    def test_rss_normal_feed_update_preserves_old_items_and_ingests_new(self):
        class Reader:
            n=1
            def fetch(self,_):
                items=''.join(f'<item><guid>{i}</guid><title>Growth may improve {i}</title><pubDate>Wed, 28 Oct 2026 12:00:00 GMT</pubDate></item>' for i in range(self.n))
                return ('<rss><channel>'+items+'</channel></rss>').encode()
        reader=Reader()
        self.assertEqual(collect(self.s,'fed_press',reader)['status'],'ok')
        reader.n=2
        self.assertEqual(collect(self.s,'fed_press',reader)['status'],'ok')
        self.assertEqual(self.s.db.execute('SELECT count(*) FROM observations').fetchone()[0],4)

    def test_divergence_revalidates_aligned_sample_freshness_and_gaps(self):
        rows=[row(d,value=.6-i*.1) for i,d in enumerate([1,5,9,20,21,22])]
        rows += [row(d,source='price',dimension='price_return',units='decimal_return',value=.01) for d in [1,5,9]]
        rows += [row(d,source='price',dimension='price_return',units='decimal_return',value=.01,hour=13) for d in [20,21,22]]
        self.s.ingest(rows,'2026-10-22T14:00:00Z',True)
        p=[p for p in detect(self.s,'2026-10-22T14:00:00Z','US_MARKET','1d')['patterns'] if p['pattern']=='sentiment_price_divergence']
        self.assertTrue(p)
        self.assertTrue(all(x['status']=='abstain' for x in p))

    def test_revisions_do_not_erase_historical_forecast_origins(self):
        rows=[row(i,dimension='attention',units='article_daily_user_pageviews',value=100+i) for i in range(1,11)]
        self.s.ingest(rows,'2026-10-10T12:00:00Z',True)
        prior=forecast(self.s,'2026-10-10T12:00:00Z','US_MARKET','1d','s','attention','article_daily_user_pageviews')
        for r in rows:
            r['revision']='2'; r['publication_time']=r['first_seen']='2026-10-11T12:00:00Z'; r['value']+=1
            r['provenance'].update({k:'2026-10-11T12:00:00Z' for k in ('provider_received_at','locally_received_at','extracted_at')})
        self.s.ingest(rows,'2026-10-11T12:00:00Z',True)
        after=forecast(self.s,'2026-10-11T12:00:00Z','US_MARKET','1d','s','attention','article_daily_user_pageviews')
        self.assertGreaterEqual(after['walk_forward']['n'],prior['walk_forward']['n'])
        self.assertEqual(after['walk_forward']['predictions'][:len(prior['walk_forward']['predictions'])],prior['walk_forward']['predictions'])

    def test_proxy_score_does_not_bridge_configuration_versions(self):
        rows=[row(i,dimension='attention',units='article_daily_user_pageviews',value=100+i,config_version='v1' if i<=5 else 'v2') for i in range(1,11)]
        self.s.ingest(rows,'2026-10-10T12:00:00Z',True)
        f=forecast(self.s,'2026-10-10T12:00:00Z','US_MARKET','1d','s','attention','article_daily_user_pageviews')
        # Five observations per version: each becomes eligible only on its final
        # day. Neither version has a compatible held-out sixth observation.
        self.assertEqual(f['walk_forward']['n'],0)

    def test_finite_measurements_cannot_emit_infinity(self):
        rows=[row(28,source=s,dimension='stress',units='VIX_index_points',value=1e308) for s in ('a','b')]
        try:
            self.s.ingest(rows,'2026-10-28T12:00:00Z',True)
            snapshot=self.s.snapshot('2026-10-28T12:00:00Z','US_MARKET','1d')
        except ValueError:
            return  # An explicit finite-range rejection is also acceptable.
        for p in snapshot['state']['stress']['population_measures']:
            self.assertTrue(math.isfinite(p['value']))
        json.dumps(snapshot,allow_nan=False)


if __name__=='__main__': unittest.main()
