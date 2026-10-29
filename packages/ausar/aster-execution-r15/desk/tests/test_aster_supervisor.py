"""Isolated synthetic-process tests: never start Aster, read its DB or touch its server."""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SUPERVISOR_PATH = Path(__file__).resolve().parents[1] / 'scripts/aster_supervisor.py'
spec = importlib.util.spec_from_file_location('aster_supervisor_test_target', SUPERVISOR_PATH)
supervisor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = supervisor
spec.loader.exec_module(supervisor)

CHILD_SOURCE = r'''
import http.server,json,os,signal,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
root=Path.cwd()
mode=root.joinpath('mode').read_text().strip()
port=int(root.joinpath('port').read_text())
countpath=root/'starts'
count=int(countpath.read_text())+1 if countpath.exists() else 1
countpath.write_text(str(count))
(root/'child.pid').write_text(str(os.getpid()))
(root/'seen_env').write_text(os.environ.get('ASTER_TEST_INHERITED_VALUE','missing'))
if mode=='crash': sys.exit(17)
if mode=='signal_crash': os.kill(os.getpid(),signal.SIGABRT)
if mode=='recover' and count==1: sys.exit(19)
if mode=='orphan_listener':
 orphan=os.fork()
 if orphan:
  time.sleep(.12)
  sys.exit(27)
 with (root/'orphan.pids').open('a') as handle: handle.write(str(os.getpid())+'\n')
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
if mode=='ignore_term': signal.signal(signal.SIGTERM,signal.SIG_IGN)
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  stamp=datetime.now(timezone.utc)
  if mode=='stale': stamp-=timedelta(seconds=30)
  payload={'autonomy':{'running':mode!='paused','worker_alive':mode!='dead_lease','heartbeat_at':stamp.isoformat(),
      'heartbeat_age_seconds':30 if mode=='stale' else 0,'progress_stale':mode=='slow_progress','healthy':mode!='slow_progress'}}
  raw=json.dumps(payload).encode()
  self.send_response(200);self.end_headers();self.wfile.write(raw)
 def log_message(self,*args): pass
if mode=='no_health':
 while True: time.sleep(.05)
server=http.server.HTTPServer(('127.0.0.1',port),Handler)
server.serve_forever(poll_interval=.02)
'''


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class SupervisorProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aster-supervisor-test-')
        self.root = Path(self.temp.name)
        (self.root / 'child.py').write_text(CHILD_SOURCE)
        (self.root / 'mode').write_text('healthy')
        self.port = free_port()
        (self.root / 'port').write_text(str(self.port))
        self.processes = []
        self.source_before = (self.root / 'child.py').read_bytes()

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            for handle in (process.stdout, process.stderr):
                if handle is not None:
                    handle.close()
        self.assertEqual((self.root / 'child.py').read_bytes(), self.source_before)
        self.temp.cleanup()

    def launch(self, mode='healthy', extra=(), env=None):
        (self.root / 'mode').write_text(mode)
        command = [sys.executable, str(SUPERVISOR_PATH), '--project-root', str(self.root),
                   '--health-url', f'http://127.0.0.1:{self.port}/api/health', '--source-file', 'child.py',
                   '--poll', '.02', '--health-interval', '.06', '--health-timeout', '.2',
                   '--heartbeat-limit', '.6', '--startup-grace', '.18', '--failure-limit', '1',
                   '--backoff-initial', '.06', '--backoff-max', '.12', '--stable-seconds', '.6',
                   '--shutdown-grace', '.15', '--kill-grace', '.5', '--max-restarts', '2', *extra,
                   '--', sys.executable, 'child.py']
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=env, start_new_session=True)
        self.processes.append(process)
        return process

    def events(self):
        path = self.root / 'data/aster-supervisor/aster-supervisor.jsonl'
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def until(self, predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.02)
        self.fail('Synthetic process did not reach expected condition')

    def wait_healthy(self):
        self.until(lambda: any(e['event'] == 'health_observation' and e['ok'] for e in self.events()))

    def test_child_crashes_restart_with_bounded_exponential_backoff(self):
        process = self.launch('crash')
        self.assertEqual(process.wait(timeout=4), supervisor.EX_TEMPFAIL)
        events = self.events()
        self.assertEqual([e['returncode'] for e in events if e['event'] == 'child_exited'], [17, 17, 17])
        self.assertEqual([e['seconds'] for e in events if e['event'] == 'restart_backoff'], [.06, .12])
        self.assertTrue(any(e['event'] == 'restart_budget_exhausted' for e in events))

    def test_os_signal_exit_is_recorded(self):
        # Signal diagnostics must not race the deliberately tiny health grace
        # used by health-failure fixtures when Python startup is contended.
        process = self.launch('signal_crash', extra=['--max-restarts', '1', '--startup-grace', '1'])
        self.assertEqual(process.wait(timeout=4), supervisor.EX_TEMPFAIL)
        exits = [e for e in self.events() if e['event'] == 'child_exited']
        self.assertEqual([e['exit_signal'] for e in exits], ['SIGABRT', 'SIGABRT'])
        self.assertEqual(exits[0]['returncode'], -signal.SIGABRT)

    def test_signal_diagnostics_survive_a_delayed_second_child_start(self):
        # Reproduce the full-suite race: only the second crash starts slowly.
        # Preserve both signal assertions; isolate exit diagnostics from an
        # unrelated no-listener health restart while importing Python modules.
        delayed = CHILD_SOURCE.replace("if mode=='signal_crash': os.kill(os.getpid(),signal.SIGABRT)",
            "if mode=='signal_crash':\n if count==2: time.sleep(.24)\n os.kill(os.getpid(),signal.SIGABRT)")
        (self.root/'child.py').write_text(delayed)
        self.source_before=delayed.encode()
        process=self.launch('signal_crash',extra=['--max-restarts','1','--startup-grace','1'])
        self.assertEqual(process.wait(timeout=4),supervisor.EX_TEMPFAIL)
        events=self.events()
        exits=[event for event in events if event['event']=='child_exited']
        self.assertEqual([event['exit_signal'] for event in exits],['SIGABRT','SIGABRT'])
        self.assertEqual([event['returncode'] for event in exits],[-signal.SIGABRT,-signal.SIGABRT])
        reasons=[event['reason'] for event in events if event['event']=='child_shutdown_requested']
        self.assertEqual(reasons,['process_exit','process_exit'])

    def test_recovery_gets_fresh_owned_health_and_sigterm_stops_group(self):
        process = self.launch('recover')
        self.wait_healthy()
        self.assertEqual((self.root / 'starts').read_text(), '2')
        child_pid = int((self.root / 'child.pid').read_text())
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(timeout=4), 0)
        self.assertIsNone(supervisor.proc_identity(child_pid))
        self.assertTrue(any(e['event'] == 'supervisor_stopped' for e in self.events()))
        status = json.loads((self.root / 'data/aster-supervisor/aster-supervisor.status.json').read_text())
        self.assertEqual(status['state'], 'stopped')
        self.assertEqual(status['source_fingerprints']['child.py']['sha256'], supervisor.sha256(self.root / 'child.py'))

    def test_stale_heartbeat_is_terminated_and_restarted(self):
        process = self.launch('stale', extra=['--max-restarts', '1'])
        self.assertEqual(process.wait(timeout=4), supervisor.EX_TEMPFAIL)
        events = self.events()
        self.assertTrue(any(e['event'] == 'restart_backoff' and e['reason'] == 'stale_heartbeat' for e in events))
        self.assertTrue(any(e['event'] == 'owned_group_signal' and e['signal'] == 'SIGTERM' for e in events))

    def test_expired_lease_is_unhealthy_even_with_fresh_heartbeat(self):
        process = self.launch('dead_lease', extra=['--max-restarts', '1'])
        self.assertEqual(process.wait(timeout=4), supervisor.EX_TEMPFAIL)
        self.assertTrue(any(e['event'] == 'restart_backoff' and e['reason'] == 'worker_lease_or_thread_unavailable' for e in self.events()))

    def test_singleton_contender_creates_no_child_or_diagnostic_events(self):
        first = self.launch()
        self.wait_healthy()
        starts = (self.root / 'starts').read_text()
        second = self.launch()
        self.assertEqual(second.wait(timeout=3), supervisor.EX_TEMPFAIL)
        self.assertEqual((self.root / 'starts').read_text(), starts)
        self.assertEqual(sum(e['event'] == 'supervisor_started' for e in self.events()), 1)
        self.assertIsNone(first.poll())

    def test_occupied_port_never_replaces_foreign_process(self):
        foreign = subprocess.Popen([sys.executable, '-c',
            'import socket,time,sys;s=socket.socket();s.bind(("127.0.0.1",int(sys.argv[1])));s.listen();time.sleep(8)', str(self.port)])
        self.processes.append(foreign)
        self.until(lambda: supervisor.port_occupied('127.0.0.1', self.port))
        process = self.launch()
        self.assertEqual(process.wait(timeout=3), supervisor.EX_CONFIG)
        self.assertIsNone(foreign.poll())
        self.assertFalse((self.root / 'child.pid').exists())
        self.assertFalse(any(e['event'] == 'owned_group_signal' for e in self.events()))

    def test_ignoring_sigterm_requires_bounded_own_group_kill(self):
        process = self.launch('ignore_term')
        self.wait_healthy()
        child = int((self.root / 'child.pid').read_text())
        started = time.monotonic()
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(timeout=3), 0)
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertIsNone(supervisor.proc_identity(child))
        self.assertEqual([e['signal'] for e in self.events() if e['event'] == 'owned_group_signal'], ['SIGTERM', 'SIGKILL'])

    def test_paused_operator_configuration_is_not_unpaused_or_restarted(self):
        process = self.launch('paused')
        self.wait_healthy()
        time.sleep(.3)
        self.assertEqual((self.root / 'starts').read_text(), '1')
        self.assertIsNone(process.poll())
        self.assertTrue(any(e.get('reason') == 'operator_paused' for e in self.events()))

    def test_slow_research_progress_is_reported_without_restart(self):
        process = self.launch('slow_progress')
        self.wait_healthy()
        time.sleep(.3)
        self.assertEqual((self.root / 'starts').read_text(), '1')
        self.assertTrue(any(e.get('progress_stale') is True for e in self.events()))
        self.assertIsNone(process.poll())

    def test_inherited_env_reaches_child_without_entering_diagnostics(self):
        secret = 'SyntheticCredential-do-not-log-51927'
        env = os.environ.copy()
        env['ASTER_TEST_INHERITED_VALUE'] = secret
        process = self.launch(env=env)
        self.wait_healthy()
        self.assertEqual((self.root / 'seen_env').read_text(), secret)
        for path in (self.root / 'data/aster-supervisor').iterdir():
            self.assertNotIn(secret, path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        process.send_signal(signal.SIGINT)
        self.assertEqual(process.wait(timeout=3), 0)

    def test_orphaned_descendant_is_owned_killed_and_reaped(self):
        process = self.launch('orphan_listener', extra=['--max-restarts','1'])
        self.assertEqual(process.wait(timeout=4), supervisor.EX_TEMPFAIL)
        pids = [int(v) for v in (self.root/'orphan.pids').read_text().splitlines()]
        self.assertEqual(len(pids),2)
        for pid in pids:
            self.assertIsNone(supervisor.proc_identity(pid))
        self.assertEqual(sum(e['event']=='owned_descendant_reaped' for e in self.events()),2)
        self.assertTrue(any(e['event']=='owned_group_signal' and e['signal']=='SIGKILL' for e in self.events()))

    def test_source_change_stops_own_child_and_blocks_restart(self):
        process = self.launch()
        self.wait_healthy()
        child=int((self.root/'child.pid').read_text())
        try:
            (self.root/'child.py').write_bytes(self.source_before+b'\n# changed code\n')
            self.assertEqual(process.wait(timeout=4),supervisor.EX_CONFIG)
            self.assertIsNone(supervisor.proc_identity(child))
            self.assertEqual((self.root/'starts').read_text(),'1')
            self.assertTrue(any(e['event']=='source_changed_restart_blocked' for e in self.events()))
        finally:
            (self.root/'child.py').write_bytes(self.source_before)

    def test_logging_failure_does_not_strand_child(self):
        runner=self.root/'fault_runner.py'
        runner.write_text("import importlib.util,sys\nfrom pathlib import Path\n"
            +f"spec=importlib.util.spec_from_file_location('sup_fault',{str(SUPERVISOR_PATH)!r})\n"
            +"m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)\n"
            +"cfg=m.Config(Path.cwd(),(sys.executable,'child.py'),health_url='http://127.0.0.1:'+(Path.cwd()/'port').read_text()+'/api/health',source_files=('child.py',),poll=.02,health_interval=.03,health_timeout=.2,startup_grace=.1,shutdown_grace=.1,kill_grace=.5)\n"
            +"obj=m.Supervisor(cfg);old=obj.emit\ndef fault(event,**kwargs):\n if event=='health_observation':raise OSError('synthetic write failure')\n old(event,**kwargs)\nobj.emit=fault\nraise SystemExit(obj.run())\n")
        process=subprocess.Popen([sys.executable,str(runner)],cwd=self.root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        self.processes.append(process)
        self.assertEqual(process.wait(timeout=4),supervisor.EX_TEMPFAIL)
        pid=int((self.root/'child.pid').read_text()) if (self.root/'child.pid').exists() else next(e['child_pid'] for e in self.events() if e['event']=='child_started')
        self.assertIsNone(supervisor.proc_identity(pid))
        self.assertTrue(any(e['event']=='child_shutdown_complete' for e in self.events()))

    def test_foreign_health_listener_is_never_queried_or_signaled(self):
        process=self.launch('no_health',extra=['--startup-grace','.4','--max-restarts','1'])
        self.until(lambda:(self.root/'child.pid').exists())
        foreign_source=self.root/'foreign.py'
        foreign_source.write_text("import http.server,sys\nfrom pathlib import Path\nclass H(http.server.BaseHTTPRequestHandler):\n def do_GET(self):\n  Path(sys.argv[2]).write_text('queried');self.send_response(200);self.end_headers();self.wfile.write(b'{}')\n def log_message(self,*args):pass\nhttp.server.HTTPServer(('127.0.0.1',int(sys.argv[1])),H).serve_forever()\n")
        foreign=subprocess.Popen([sys.executable,str(foreign_source),str(self.port),str(self.root/'foreign_queried')])
        self.processes.append(foreign)
        self.until(lambda:supervisor.port_occupied('127.0.0.1',self.port))
        self.assertEqual(process.wait(timeout=4),supervisor.EX_CONFIG)
        self.assertIsNone(foreign.poll())
        self.assertFalse((self.root/'foreign_queried').exists())
        self.assertTrue(any(e.get('reason')=='health_listener_not_owned_by_child_group' for e in self.events()))

    def test_all_custom_outputs_reject_source_paths_without_modification(self):
        path=self.root/'child.py'
        for option in ('--lock','--events','--status','--child-log'):
            with self.subTest(option=option):
                process=self.launch(extra=[option,str(path)])
                self.assertEqual(process.wait(timeout=3),supervisor.EX_CONFIG)
                self.assertEqual(path.read_bytes(),self.source_before)
        self.assertFalse((self.root/'child.pid').exists())

    def test_hardlink_receipt_alias_cannot_truncate_source(self):
        directory=self.root/'data/aster-supervisor'
        directory.mkdir(parents=True)
        path=directory/'aster-supervisor.lock'
        os.link(self.root/'child.py',path)
        process=self.launch()
        self.assertEqual(process.wait(timeout=3),supervisor.EX_CONFIG)
        self.assertEqual((self.root/'child.py').read_bytes(),self.source_before)
        self.assertFalse((self.root/'child.pid').exists())

    def test_selected_source_in_receipt_directory_cannot_be_lock(self):
        directory=self.root/'data/aster-supervisor'
        directory.mkdir(parents=True)
        selected=directory/'selected.py'
        original=b'# source that must remain untouched\n'
        selected.write_bytes(original)
        process=self.launch(extra=['--source-file','data/aster-supervisor/selected.py','--lock',str(selected)])
        self.assertEqual(process.wait(timeout=3),supervisor.EX_CONFIG)
        self.assertEqual(selected.read_bytes(),original)
        self.assertFalse((self.root/'child.pid').exists())

    def test_backoff_reaches_cap_and_never_exceeds_it(self):
        process=self.launch('crash',extra=['--max-restarts','3','--backoff-initial','.02','--backoff-max','.03'])
        self.assertEqual(process.wait(timeout=4),supervisor.EX_TEMPFAIL)
        self.assertEqual([e['seconds'] for e in self.events() if e['event']=='restart_backoff'],[.02,.03,.03])

    def test_inspect_starts_no_child_and_creates_no_outputs(self):
        result = subprocess.run([sys.executable, str(SUPERVISOR_PATH), '--project-root', str(self.root),
                                 '--source-file', 'child.py', '--inspect', '--', sys.executable, 'child.py'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertTrue(parsed['prepared_only'])
        self.assertFalse((self.root / 'data').exists())
        self.assertFalse((self.root / 'child.pid').exists())


class HealthContractTests(unittest.TestCase):
    def payload(self, **changes):
        values = {'running': True, 'worker_alive': True, 'heartbeat_at': datetime.now(timezone.utc).isoformat(),
                  'heartbeat_age_seconds': 0, 'healthy': True}
        values.update(changes)
        return {'autonomy': values}

    def test_future_heartbeat_is_rejected(self):
        result = supervisor.assess_health(self.payload(heartbeat_at=(datetime.now(timezone.utc)+timedelta(seconds=10)).isoformat()), 90)
        self.assertEqual(result['reason'], 'future_heartbeat')

    def test_naive_heartbeat_is_rejected(self):
        self.assertEqual(supervisor.assess_health(self.payload(heartbeat_at='2026-10-09T12:00:00'), 90)['reason'], 'invalid_heartbeat')

    def test_nan_and_boolean_age_are_rejected(self):
        for age in (float('nan'), float('inf'), True, None, '0'):
            with self.subTest(age=age):
                self.assertEqual(supervisor.assess_health(self.payload(heartbeat_age_seconds=age), 90)['reason'], 'invalid_heartbeat')

    def test_truthy_nonboolean_worker_flags_are_rejected(self):
        for changes in ({'running':'true'}, {'worker_alive':1}):
            self.assertEqual(supervisor.assess_health(self.payload(**changes), 90)['reason'], 'invalid_worker_flags')

    def test_health_url_rejects_remote_redirect_or_credential_targets(self):
        for url in ('https://127.0.0.1/api/health','http://localhost/api/health','http://evil.example/api/health',
                    'http://a:b@127.0.0.1/api/health','http://127.0.0.1/api/health?x=secret','http://127.0.0.1/other'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                supervisor.loopback_endpoint(url)

    def test_health_url_accepts_literal_ipv6_loopback(self):
        self.assertEqual(supervisor.loopback_endpoint('http://[::1]:8787/api/health'), ('::1',8787))

    def test_malformed_payload_is_rejected(self):
        for payload in (None, [], {}, {'autonomy':None}):
            self.assertFalse(supervisor.assess_health(payload,90)['ok'])

    def test_wrong_address_family_cannot_authorize_foreign_listener(self):
        v4=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        v4.bind(('127.0.0.1',0));v4.listen()
        port=v4.getsockname()[1]
        foreign=subprocess.Popen([sys.executable,'-c',
            'import socket,sys,time;s=socket.socket(socket.AF_INET6);s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1);s.bind(("::1",int(sys.argv[1])));s.listen();time.sleep(5)',str(port)])
        try:
            deadline=time.monotonic()+2
            while not supervisor.port_occupied('::1',port) and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue(supervisor.port_occupied('::1',port))
            own={os.getpid():supervisor.proc_identity(os.getpid())}
            self.assertTrue(supervisor.group_owns_listener(own,port,'127.0.0.1'))
            self.assertFalse(supervisor.group_owns_listener(own,port,'::1'))
        finally:
            v4.close();foreign.terminate();foreign.wait(timeout=3)

    def dribbling_server(self):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen()
        stop=threading.Event()
        def serve():
            connection=None
            try:
                connection,_=listener.accept()
                connection.recv(4096)
                connection.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 99999\r\n\r\n')
                while not stop.wait(.01):connection.sendall(b' ')
            except OSError:pass
            finally:
                if connection is not None:connection.close()
                listener.close()
        thread=threading.Thread(target=serve,daemon=True);thread.start()
        return listener.getsockname()[1],stop,thread

    def test_dribbling_response_cannot_extend_absolute_deadline(self):
        port,server_stop,thread=self.dribbling_server()
        started=time.monotonic()
        try:
            with self.assertRaises(TimeoutError):
                supervisor.bounded_health_request('127.0.0.1',port,.15,threading.Event())
            self.assertLess(time.monotonic()-started,.5)
        finally:
            server_stop.set();thread.join(timeout=1)

    def test_dribbling_response_is_cancelled_on_stop(self):
        port,server_stop,thread=self.dribbling_server()
        stop=threading.Event();timer=threading.Timer(.1,stop.set);timer.start()
        started=time.monotonic()
        try:
            with self.assertRaises(InterruptedError):
                supervisor.bounded_health_request('127.0.0.1',port,10,stop)
            self.assertLess(time.monotonic()-started,.5)
        finally:
            timer.cancel();server_stop.set();thread.join(timeout=1)

    def test_default_source_pins_include_coordinator_and_exclude_env(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'scripts').mkdir()
            (root/'run.sh').write_text('#!/bin/sh\nexit 0\n')
            (root/'scripts/aster_services.py').write_text('# companion coordinator v1\n')
            (root/'scripts/aster_launch.sh').write_text('#!/bin/sh\nexit 0\n')
            (root/'Dockerfile').write_text('FROM scratch\n')
            (root/'compose.yaml').write_text('services: {}\n')
            (root/'.env').write_text('ASTER_TEST_SECRET=synthetic-private-value\n')
            pins=supervisor.source_fingerprint(root)
            self.assertIn('scripts/aster_services.py',pins)
            self.assertIn('scripts/aster_launch.sh',pins)
            self.assertIn('Dockerfile',pins)
            self.assertIn('compose.yaml',pins)
            self.assertNotIn('.env',pins)
            self.assertNotIn('synthetic-private-value',json.dumps(pins))
            (root/'scripts/aster_services.py').write_text('# companion coordinator v2\n')
            self.assertNotEqual(pins,supervisor.source_fingerprint(root))

    def test_config_rejects_negative_nan_and_boolean_timers(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in (-1,float('nan'),True):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    supervisor.Config(Path(directory),(sys.executable,),poll=value).validated()


if __name__ == '__main__':
    unittest.main()
