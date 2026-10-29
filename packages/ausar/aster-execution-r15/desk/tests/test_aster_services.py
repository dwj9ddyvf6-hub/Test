import importlib.util
import json
import os
import signal
import subprocess
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/'scripts/aster_services.py'
spec = importlib.util.spec_from_file_location('aster_services_test_module', SOURCE)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class ServiceCoordinatorTests(unittest.TestCase):
    def test_missing_companions_do_not_install_or_fund(self):
        with tempfile.TemporaryDirectory() as tmp:
            specs = module.installed_specs(tmp)
            self.assertEqual([s['name'] for s in specs], ['main'])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_prebuilt_container_needs_no_venv_or_npm_and_keeps_empty_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            specs = module.installed_specs(tmp, container_mode=True)
            self.assertEqual(specs[0]['argv'][:3], [sys.executable, '-m', 'uvicorn'])
            self.assertEqual([s['name'] for s in specs], ['main'])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_research_reads_actual_configured_main_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            primary=Path(tmp)/'owned-main.sqlite'
            projection={'native':{},'public_recipes':{},'original_research':{'registered':True,'status':'registered_unfunded_research','current_lineage_matches':True}}
            with patch.dict(module.os.environ, {'ASTER_DB_PATH':str(primary)}), patch('backend.prospective_projection.prospective_snapshot', return_value=projection):
                specs=module.installed_specs(tmp)
            research=next(s for s in specs if s['name']=='research')
            self.assertEqual(research['argv'][research['argv'].index('--operating-db')+1], str(primary))

    def test_real_registered_research_contract_and_status_cli_are_supported(self):
        import contextlib
        import io
        from backend.original_research_runtime import OriginalResearch, main, read_status
        with tempfile.TemporaryDirectory() as tmp, patch.dict(module.os.environ, {}, clear=True):
            primary = Path(tmp)/'aster.sqlite'
            collector = Path(tmp)/'original-research.sqlite'
            OriginalResearch(collector, primary)
            registered = read_status(collector)
            self.assertEqual(registered['status'], 'registered_unfunded_research')
            self.assertEqual(registered['funding'], 0)
            specs = module.installed_specs(tmp)
            self.assertIn('research', [s['name'] for s in specs])
            research = next(s for s in specs if s['name']=='research')
            # Exercise the real CLI parser with a read-only command, using the
            # exact launch flags. No network, financial simulation or orders.
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main(['status', *research['argv'][4:]])
            self.assertEqual(json.loads(output.getvalue())['funding'], 0)

    def test_optional_crash_recovers_and_required_crash_stops_all_owned_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp)/'crash.py'
            script.write_text('import time\ntime.sleep(.25)\nraise SystemExit(7)\n')
            long = [sys.executable, '-c', 'import time; time.sleep(30)']
            coordinator = module.ServiceCoordinator([
                {'name':'main','required':True,'argv':long},
                {'name':'optional','required':False,'argv':[sys.executable,str(script)]}],
                Path(tmp)/'status.json', cwd=tmp, poll_seconds=.01, initial_backoff=.03, maximum_backoff=.05, shutdown_seconds=.5)
            thread = threading.Thread(target=coordinator.run); thread.start()
            try:
                deadline = time.monotonic()+5
                while time.monotonic()<deadline and coordinator.states.get('optional',{}).get('attempts',0)<2:
                    time.sleep(.02)
                self.assertGreaterEqual(coordinator.states['optional']['attempts'], 2)
                coordinator.processes['main'].terminate()
                thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertTrue(all(p.poll() is not None for p in coordinator.processes.values()))
                result = json.loads((Path(tmp)/'status.json').read_text())
                self.assertEqual(result['installs_or_fundings'], 0)
                self.assertEqual(result['services']['main']['status'], 'stopped')
            finally:
                coordinator.stop.set(); thread.join(3)

    def test_explicit_stop_reaps_children_and_private_atomic_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            coordinator = module.ServiceCoordinator([{'name':'main','required':True,
                'argv':[sys.executable,'-c','import time; time.sleep(30)']}],
                Path(tmp)/'status.json', cwd=tmp, poll_seconds=.01, shutdown_seconds=.5)
            thread = threading.Thread(target=coordinator.run); thread.start()
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and not coordinator.processes:
                time.sleep(.01)
            coordinator.stop.set(); thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertIsNotNone(coordinator.processes['main'].poll())
            self.assertEqual((Path(tmp)/'status.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(tmp).glob('.services-*')), [])

    def test_unknown_or_duplicate_names_fail_before_process_start(self):
        with self.assertRaises(ValueError):
            module.ServiceCoordinator([{'name':'a','argv':['x']},{'name':'a','argv':['x']}], '/tmp/unused')


class CompanionHeartbeatTests(unittest.TestCase):
    CHILD = """
import fcntl,json,os,sys,time
from pathlib import Path
from datetime import datetime,timedelta,timezone
kind,age,record,lease,mode=sys.argv[1:]
age=float(age)
fd=open(lease,'a+')
fcntl.flock(fd,fcntl.LOCK_EX)
pid=os.getpid();birth=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
while True:
    stamp=(datetime.now(timezone.utc)-timedelta(seconds=age)).isoformat()
    value={'pid':pid}
    if kind=='native':value.update(process_start=birth,at=stamp,running=True,process_alive=True,stale=False)
    elif kind=='recipe':value.update(pid_birth_tick=birth,heartbeat_at=stamp,running=True,process_alive_with_matching_birth=True,stale=False,phase='running',interval_seconds=20)
    else:value.update(process_birth=birth,observed_at=stamp,active=True,pid_birth_matches=True,lease_held=True,state='sleeping',interval_seconds=300,stale_after_seconds=675)
    if mode=='foreign':value['pid']=int(os.environ['SYNTHETIC_FOREIGN_PID']);value['process_start']=os.environ['SYNTHETIC_FOREIGN_BIRTH']
    if mode=='birth':value['process_start']='999999999'
    temp=Path(record+'.tmp');temp.write_text(json.dumps(value));os.replace(temp,record)
    time.sleep(.02)
"""

    def coordinator(self, tmp, kind='native', age=0, mode='normal', reader=None):
        directory=Path(tmp);record=directory/'worker.json';lease=directory/'worker.lock'
        script=directory/'worker.py';script.write_text(self.CHILD)
        health={'kind':kind,'module':'backend.prospective_native','db':str(directory/'no-funding.sqlite'),
                'lease':str(lease),'interval_seconds':300 if kind=='research' else 20 if kind=='recipe' else 30}
        specs=[{'name':'main','required':True,'argv':[sys.executable,'-c','import time;time.sleep(30)']},
               {'name':'companion','required':False,'argv':[sys.executable,str(script),kind,str(age),str(record),str(lease),mode],'health':health}]
        if reader is None:
            reader=lambda spec,cwd,stop:json.loads(record.read_text())
        coordinator=module.ServiceCoordinator(specs,directory/'status.json',cwd=tmp,poll_seconds=.01,
                    initial_backoff=.04,maximum_backoff=.08,shutdown_seconds=.1,
                    startup_grace=.12,health_interval=.04,health_failures=2,status_reader=reader)
        return coordinator,record,lease

    def run_coordinator(self, c):
        failures=[]
        def run():
            try:c.run()
            except Exception as exc:failures.append(repr(exc))
        thread=threading.Thread(target=run);thread.start()
        return thread,failures

    def finish(self,c,thread,failures):
        c.stop.set();thread.join(3)
        self.assertFalse(thread.is_alive());self.assertEqual(failures,[])
        self.assertTrue(all(p.poll() is not None for p in c.processes.values()))

    def until(self,predicate,seconds=3):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            if predicate():return
            time.sleep(.01)
        self.fail('Synthetic process condition timed out')

    def test_stale_alive_owned_worker_is_reaped_and_restarted_after_two_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp,age=500)
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:record.exists())
                first=c.processes['companion'];first_pid=first.pid
                self.until(lambda:c.states['companion']['attempts']>=2)
                self.assertIsNotNone(first.poll());self.assertNotEqual(first_pid,c.processes['companion'].pid)
                self.assertEqual(c.states['main']['attempts'],1)
                self.assertGreaterEqual(c.states['companion']['health_recoveries'],1)
                self.assertEqual(c.states['companion']['last_health_failure'],'stale_or_future_heartbeat')
            finally:self.finish(c,thread,errors)

    def test_fresh_lease_held_worker_has_no_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp)
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:c.states.get('companion',{}).get('status')=='worker_healthy')
                time.sleep(.2)
                self.assertEqual(c.states['companion']['attempts'],1)
                self.assertEqual(c.states['companion']['health_recoveries'],0)
                self.assertTrue(module.owned_lease(lease,c.processes['companion'].pid))
            finally:self.finish(c,thread,errors)

    def test_original_research_600_second_heartbeat_honors_675_second_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp,kind='research',age=600)
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:c.states.get('companion',{}).get('status')=='worker_healthy')
                time.sleep(.2)
                self.assertEqual(c.states['companion']['attempts'],1)
                self.assertEqual(c.states['companion']['stale_after_seconds'],675)
                self.assertGreaterEqual(c.states['companion']['heartbeat_age_seconds'],600)
            finally:self.finish(c,thread,errors)

    def test_public_recipe_170_second_heartbeat_is_still_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp,kind='recipe',age=170)
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:c.states.get('companion',{}).get('status')=='worker_healthy')
                self.assertEqual(c.states['companion']['stale_after_seconds'],180)
                self.assertEqual(c.states['companion']['attempts'],1)
            finally:self.finish(c,thread,errors)

    def test_foreign_pid_receipt_only_recovers_own_child_and_leaves_foreign_alive(self):
        foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'SYNTHETIC_FOREIGN_PID':str(foreign.pid),'SYNTHETIC_FOREIGN_BIRTH':module.process_birth(foreign.pid)}):
                c,record,lease=self.coordinator(tmp,mode='foreign')
                thread,errors=self.run_coordinator(c)
                try:
                    self.until(lambda:c.states.get('companion',{}).get('attempts',0)>=2)
                    self.assertIsNone(foreign.poll())
                    self.assertEqual(c.states['companion']['last_health_failure'],'worker_ownership_mismatch')
                finally:self.finish(c,thread,errors)
                self.assertIsNone(foreign.poll())
        finally:foreign.terminate();foreign.wait(timeout=3)

    def test_same_pid_wrong_birth_receipt_cannot_authorize_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp,mode='birth')
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:c.states.get('companion',{}).get('attempts',0)>=2)
                self.assertEqual(c.states['companion']['last_health_failure'],'worker_ownership_mismatch')
            finally:self.finish(c,thread,errors)

    def test_released_lease_is_unhealthy_despite_fresh_worker_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,record,lease=self.coordinator(tmp)
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:c.states.get('companion',{}).get('status')=='worker_healthy')
                # An independent fresh receipt cannot replace OS lease ownership.
                foreign=Path(tmp)/'unheld.lock';foreign.write_text('')
                c.specs['companion']['health']['lease']=str(foreign)
                self.until(lambda:c.states['companion']['attempts']>=2)
                self.assertEqual(c.states['companion']['last_health_failure'],'worker_lease_not_owned')
            finally:self.finish(c,thread,errors)

    def test_startup_grace_and_single_failure_do_not_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def reader(spec,cwd,stop):
                calls.append(time.monotonic());raise ValueError('synthetic only')
            c,record,lease=self.coordinator(tmp,reader=reader)
            c.health_interval=.5;c.startup_grace=.3
            thread,errors=self.run_coordinator(c)
            try:
                self.until(lambda:record.exists())
                self.until(lambda:len(calls)==1)
                self.assertGreaterEqual(calls[0]-c.states['companion']['started_mono'],.3)
                self.assertEqual(c.states['companion']['health_failures'],1)
                self.assertEqual(c.states['companion']['attempts'],1)
            finally:self.finish(c,thread,errors)

    def test_actual_read_status_probe_is_readonly_and_cancellable_when_stalled(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);backend=directory/'backend';backend.mkdir();(backend/'__init__.py').write_text('')
            (backend/'prospective_native.py').write_text('import time\ndef read_status(path):time.sleep(30)\n')
            spec={'argv':[sys.executable],'health':{'module':'backend.prospective_native','db':str(directory/'missing.sqlite')}}
            stop=threading.Event();timer=threading.Timer(.15,stop.set);timer.start();started=time.monotonic()
            try:
                with self.assertRaises(ValueError):module.read_worker(spec,directory,stop,timeout=1)
                self.assertLess(time.monotonic()-started,1.1)
                self.assertFalse((directory/'missing.sqlite').exists())
            finally:timer.cancel()

    def test_projection_streaming_output_has_incremental_limit_and_bounded_reap(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);backend=directory/'backend';backend.mkdir();(backend/'__init__.py').write_text('')
            (backend/'prospective_native.py').write_text("import sys,time\nsys.stdout.write('x'*1000000);sys.stdout.flush();time.sleep(30)\ndef read_status(path):return {}\n")
            spec={'argv':[sys.executable],'health':{'module':'backend.prospective_native','db':str(directory/'missing.sqlite')}}
            started=time.monotonic()
            with self.assertRaisesRegex(ValueError,'output limit'):
                module.read_worker(spec,directory,threading.Event(),timeout=2)
            self.assertLess(time.monotonic()-started,1)
            self.assertFalse((directory/'missing.sqlite').exists())

    def test_fifo_lease_is_refused_without_open_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo=Path(tmp)/'lease.fifo';os.mkfifo(fifo)
            started=time.monotonic()
            self.assertFalse(module.owned_lease(fifo,os.getpid()))
            self.assertLess(time.monotonic()-started,.2)

    def test_actual_native_projection_missing_journal_stays_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'missing-native.sqlite'
            spec={'argv':[sys.executable],'health':{'module':'backend.prospective_native','db':str(path)}}
            worker=module.read_worker(spec,SOURCE.parents[1],threading.Event())
            self.assertEqual(worker,{'running':False});self.assertFalse(path.exists())

    def test_default_health_policy_and_registered_specs_match_worker_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=module.ServiceCoordinator([{'name':'main','required':True,'argv':['true']}],Path(tmp)/'status')
            self.assertEqual((c.startup_grace,c.health_interval,c.health_failures),(120,15,2))
            projection={'native':{'installed_count':2},'public_recipes':{'installed':True},'original_research':{'registered':True,'status':'registered_unfunded_research','current_lineage_matches':True}}
            with patch.dict(os.environ,{},clear=True),patch('backend.prospective_projection.prospective_snapshot',return_value=projection):
                specs=module.installed_specs(tmp)
            policies={s['name']:s.get('health') for s in specs}
            self.assertEqual(policies['research']['interval_seconds'],300)
            self.assertTrue(policies['research']['lease'].endswith('.collector.lock'))
            self.assertEqual(policies['native']['interval_seconds'],30)
            self.assertEqual(policies['recipe']['interval_seconds'],20)

    def test_container_healthcheck_uses_trusted_env_ipv6_and_custom_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);binpath=directory/'bin';binpath.mkdir()
            python=binpath/'python'
            python.write_text('#!'+sys.executable+'\nimport json,os,sys\nprint(json.dumps({"argv":sys.argv[1:],"cwd":os.getcwd(),"guard":os.environ.get("ASTER_SYNTHETIC_GUARD")}))\n')
            python.chmod(0o700)
            (directory/'.env').write_text("ASTER_HOST='::1'\nASTER_PORT=8991\nASTER_SYNTHETIC_GUARD='synthetic-value-only'\n")
            env={**os.environ,'ASTER_PROJECT_ROOT':tmp,'PATH':str(binpath)+':'+os.environ['PATH']}
            output=subprocess.run(['/bin/sh',str(SOURCE.parents[1]/'scripts/aster_healthcheck.sh')],env=env,capture_output=True,text=True,timeout=3)
            self.assertEqual(output.returncode,0,output.stderr)
            value=json.loads(output.stdout)
            self.assertEqual(value['cwd'],tmp)
            self.assertEqual(value['argv'],['scripts/monitor.py','--url','http://[::1]:8991','--maximum-age','180'])
            self.assertEqual(value['guard'],'synthetic-value-only')
            self.assertFalse((directory/'data').exists())

    def test_invalid_health_timing_fails_before_launch(self):
        for kwargs in ({'startup_grace':float('nan')},{'health_interval':0},{'health_failures':True},{'maximum_backoff':.1}):
            with self.assertRaises(ValueError):module.ServiceCoordinator([{'name':'main','argv':['true']}],'/tmp/not-written',**kwargs)


if __name__ == '__main__':
    unittest.main()
