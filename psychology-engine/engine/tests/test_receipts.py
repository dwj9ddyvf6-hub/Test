import hashlib,json,unittest
from unittest.mock import patch
from psychology_engine.core import Store
from psychology_engine.receipts import import_receipt

class ReceiptTests(unittest.TestCase):
    def receipt(self):
        payload=json.dumps({'items':[dict(project='en.wikipedia',article='Stock_market',access='all-access',agent='user',timestamp='2026102700',views=123)]})
        return dict(receipt_id='SYNTHETIC_TEST_ONLY',source='wikimedia_attention',source_url='https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Stock_market/daily/20261027/20261027',captured_at='2026-10-28T12:00:00Z',payload_utf8=payload,payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),usage_scope='generated_fixture',redistribution_status='generated_fixture')
    def test_receipt_import_no_network_and_no_backdating(self):
        s=Store(':memory:');receipt=self.receipt()
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network forbidden')):
            result=import_receipt(s,receipt,'2026-10-29T12:00:00Z')
            self.assertEqual(result['inserted'],1);self.assertEqual(result['outbound_requests'],0)
            self.assertEqual(len(s.snapshot('2026-10-28T12:00:00Z','TOPIC:Stock_market','1d')['evidence']),0)
            self.assertEqual(len(s.snapshot('2026-10-29T12:00:00Z','TOPIC:Stock_market','1d')['evidence']),1)
            self.assertEqual(import_receipt(s,receipt,'2026-10-29T13:00:00Z')['duplicates'],1)
        s.close()
    def test_checksum_and_future_capture_rejected(self):
        s=Store(':memory:');r=self.receipt();r['payload_sha256']='0'*64
        with self.assertRaises(ValueError):import_receipt(s,r,'2026-10-29T12:00:00Z')
        r=self.receipt();r['captured_at']='2027-01-01T00:00:00Z'
        with self.assertRaises(ValueError):import_receipt(s,r,'2026-10-29T12:00:00Z')
        s.close()

    def test_upstream_capture_cannot_precede_daily_completion(self):
        s=Store(':memory:');r=self.receipt();r['captured_at']='2026-10-27T12:00:00Z'
        with self.assertRaisesRegex(ValueError,'event_time occurs after upstream capture'):
            import_receipt(s,r,'2026-10-29T12:00:00Z')
        self.assertEqual(s.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],0)
        r['captured_at']='2026-10-28T00:00:00Z'
        self.assertEqual(import_receipt(s,r,'2026-10-29T12:00:00Z')['inserted'],1);s.close()

    def test_rss_publication_after_upstream_capture_rejected(self):
        s=Store(':memory:');r=self.receipt();body='<rss><channel><item><guid>test</guid><title>Growth improves</title><pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        r.update(source='fed_press',source_url='https://www.federalreserve.gov/feeds/press_all.xml',payload_utf8=body,payload_sha256=hashlib.sha256(body.encode()).hexdigest())
        with self.assertRaisesRegex(ValueError,'after upstream capture'):import_receipt(s,r,'2026-10-30T12:00:00Z')
        self.assertEqual(s.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],0);s.close()
