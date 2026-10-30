import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from psychology_engine.network import decision,check
from psychology_engine.operations import health,backup
from psychology_engine.core import Store
from test_engine import obs,T

class OperationsTests(unittest.TestCase):
    def policy(self,rules):return {'version':1,'http_network_policy':{'type':'restricted','egress_rules':rules}}
    def test_exact_host_case_and_no_suffix_bypass(self):
        p=self.policy([{'host':'EXAMPLE.ORG'}])
        self.assertTrue(decision('https://example.org/path',p)['allowed'])
        for url in ('https://example.org.evil.test/','https://sub.example.org/','https://example.org./','https://example.org:444/','http://example.org/'):
            self.assertFalse(decision(url,p)['allowed'])
    def test_unsupported_wildcards_methods_schemes_fail_closed(self):
        for rule in ({'host':'*.example.org'},{'host':'example.org','methods':['POST']},{'host':'https://example.org'},{'host':'example.org','scheme':'https'}):
            self.assertFalse(decision('https://example.org/',self.policy([rule]))['allowed'])
        self.assertFalse(decision('https://example.org/',self.policy([{'host':'example.org'}]),method='POST')['allowed'])
    def test_missing_unknown_policy_is_not_permission(self):
        for p in ({},{'version':2},self.policy([])):
            self.assertFalse(decision('https://example.org/',p)['allowed'])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):check('https://example.org/',str(Path(d)/'missing'))
    def test_actual_source_domains_denied_by_actual_policy(self):
        # Verify this supplied snapshot as test data, not a live environment requirement.
        p=self.policy([{'host':'github.com'},{'host':'pypi.org'}])
        for host in ('www.federalreserve.gov','www.frbsf.org','wikimedia.org','cdn.cboe.com','cdn-api.cboe.com'):
            self.assertFalse(decision('https://'+host+'/',p)['allowed'])
    def test_health_does_not_create_missing_database(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'none.sqlite';result,code=health(p,['survey_a'],T)
            self.assertEqual(code,1);self.assertFalse(p.exists())
    def test_consistent_backup_restart_and_readonly_health(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'store.sqlite';dest=Path(d)/'backup.sqlite';s=Store(p);s.ingest([obs()],T,True)
            with s.db:s.db.execute('INSERT INTO runs VALUES (?,?,?,?)',(T,'survey_a','ok','fixture'))
            self.assertEqual(health(p,['survey_a'],T)[1],0)
            self.assertEqual(backup(p,dest)['status'],'ok')
            restored=Store(dest);self.assertEqual(len(restored.snapshot(T,'US_MARKET','1d')['evidence']),1)
            self.assertEqual(restored.ingest([obs()],T,True)['duplicates'],1);restored.close()
            with self.assertRaises(FileExistsError):backup(p,dest)
            self.assertEqual(health(p,['survey_a'],'2026-11-01T12:00:00Z')[1],3);s.close()

    def test_health_latest_null_or_withdrawn_revision_invalidates_old_value(self):
        later='2026-10-28T13:00:00+00:00'
        for changes in ({'value':None},{'access_status':'unavailable'}):
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as d:
                p=Path(d)/'store.sqlite';s=Store(p);s.ingest([obs()],T,True)
                s.ingest([obs(revision='2',publication_time=later,first_seen=later,**changes)],later,True)
                with s.db:s.db.execute('INSERT INTO runs VALUES (?,?,?,?)',(later,'survey_a','ok','fixture'))
                result,code=health(p,['survey_a'],later)
                self.assertEqual(s.snapshot(later,'US_MARKET','1d')['evidence'],[])
                self.assertEqual(code,3);self.assertFalse(result['sources']['survey_a']['fresh_observation_present'])
                # The future revision must not invalidate an earlier cutoff.
                with s.db:s.db.execute('INSERT INTO runs VALUES (?,?,?,?)',(T,'survey_a','ok','fixture'))
                self.assertEqual(health(p,['survey_a'],T)[1],0);s.close()

    def test_backup_private_mode_and_no_change_to_existing_destination(self):
        import os,stat
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.sqlite';dest=Path(d)/'private.sqlite'
            s=Store(source);s.ingest([obs()],T,True);s.close()
            previous=os.umask(0o022)
            try:backup(source,dest)
            finally:os.umask(previous)
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode),0o600)
            existing=Path(d)/'existing';existing.write_text('untouched');existing.chmod(0o644)
            with self.assertRaises(FileExistsError):backup(source,existing)
            self.assertEqual(existing.read_text(),'untouched')
            self.assertEqual(stat.S_IMODE(existing.stat().st_mode),0o644)
