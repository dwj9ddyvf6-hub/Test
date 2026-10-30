"""Offline v0.4 operational regressions; no network or service activation."""
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from psychology_engine.core import Store
from psychology_engine.operations import health, backup
from psychology_engine.receipts import import_receipt
from psychology_engine.__main__ import main

T='2026-10-28T12:00:00+00:00'

def observation(**changes):
    r=dict(source='fixture',source_family='fixture',item_id='a',revision='1',event_time=T,
           publication_time=T,first_seen=T,entity='US_MARKET',horizon='1d',dimension='sentiment',
           units='balance',value=.5,max_age_hours=48,config_version='v1',access_status='fixture',
           provenance={k:T for k in ('provider_received_at','locally_received_at','extracted_at')})
    r['provenance']['source_population']='fixture';r.update(changes);return r

def receipt(captured='2026-10-28T12:00:00Z'):
    body=json.dumps({'items':[dict(project='en.wikipedia',article='Stock_market',access='all-access',
                                  agent='user',timestamp='2026102700',views=123)]})
    return dict(receipt_id='AUDIT_SYNTHETIC',source='wikimedia_attention',
                source_url='https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/Stock_market/daily/20261027/20261027',
                captured_at=captured,payload_utf8=body,payload_sha256=hashlib.sha256(body.encode()).hexdigest(),
                usage_scope='generated_fixture',redistribution_status='generated_fixture')

class OperationalIndependentTests(unittest.TestCase):
    def test_health_must_respect_latest_null_revision(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'db';s=Store(path);s.ingest([observation()],T,True)
            later='2026-10-28T13:00:00+00:00'
            s.ingest([observation(revision='2',value=None,first_seen=later,publication_time=later)],later,True)
            with s.db:s.db.execute('INSERT INTO runs VALUES (?,?,?,?)',(later,'fixture','ok','fixture'))
            self.assertEqual(s.snapshot(later,'US_MARKET','1d')['evidence'],[])
            result,code=health(path,['fixture'],later)
            s.close()
            self.assertNotEqual(code,0)
            self.assertFalse(result['sources']['fixture']['fresh_observation_present'])

    def test_capture_cannot_precede_completed_daily_observation(self):
        s=Store(':memory:')
        try:
            with self.assertRaises(ValueError):
                import_receipt(s,receipt('2026-10-27T12:00:00Z'),'2026-10-29T12:00:00Z')
            self.assertEqual(s.db.execute('SELECT count(*) FROM observations').fetchone()[0],0)
        finally:s.close()

    def test_backup_permissions_private_even_with_permissive_umask(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'db';target=Path(d)/'backup';s=Store(source);s.ingest([observation()],T,True)
            old=os.umask(0o022)
            try:backup(source,target)
            finally:os.umask(old);s.close()
            self.assertEqual(target.stat().st_mode & 0o077,0)

    def test_backup_restores_committed_wal_all_evidence_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'db';target=Path(d)/'backup';s=Store(source);s.ingest([observation()],T,True)
            snap=s.snapshot(T,'US_MARKET','1d');s.record_acquisition('fixture',T,b'fixture')
            backup(source,target)
            restored=Store(target)
            self.assertEqual(restored.snapshot(T,'US_MARKET','1d')['snapshot_id'],snap['snapshot_id'])
            self.assertEqual(restored.db.execute('SELECT count(*) FROM acquisitions').fetchone()[0],1)
            with self.assertRaises(FileExistsError):backup(source,target)
            restored.close();s.close()

    def test_receipt_cannot_backdate_local_availability_and_never_calls_http(self):
        s=Store(':memory:')
        try:
            with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('No HTTP permitted')):
                result=import_receipt(s,receipt(),'2026-10-29T12:00:00Z')
            self.assertEqual(result['outbound_requests'],0)
            self.assertFalse(result['live_collection_validated'])
            self.assertEqual(s.snapshot(T,'TOPIC:Stock_market','1d')['evidence'],[])
            evidence=s.snapshot('2026-10-29T12:00:00Z','TOPIC:Stock_market','1d')['evidence']
            self.assertEqual(len(evidence),1)
            self.assertEqual(evidence[0]['first_seen'],'2026-10-29T12:00:00+00:00')
        finally:s.close()

    def test_scheduled_one_shot_cannot_skip_permission_gate(self):
        with tempfile.TemporaryDirectory() as d:
            args=['psychology_engine','--db',str(Path(d)/'db'),'monitor','--source','fed_press','--cycles','1','--scheduled']
            with patch('sys.argv',args),patch('sys.stderr',io.StringIO()),patch('psychology_engine.__main__.collect') as collector:
                with self.assertRaises(SystemExit) as ex:main()
                self.assertEqual(ex.exception.code,2)
                collector.assert_not_called()

if __name__=='__main__':unittest.main()
