#!/usr/bin/env python3
"""Coordinate Aster and explicitly installed independent companions.

All children retain the outer supervisor's owned process group. This program
installs/funds nothing, sends no broker requests and never joins ledgers.
"""
import argparse
import fcntl
import json
import math
import stat
import os
from pathlib import Path
import signal
import selectors
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
HEALTH_MODULES = {'backend.prospective_native', 'backend.public_recipe_runtime', 'backend.original_research_runtime'}
# Only a projection's small worker receipt crosses the pipe. No network call,
# constructor, installation, funding or financial state is performed here.
WORKER_QUERY = "import importlib,json,sys; s=importlib.import_module(sys.argv[1]).read_status(sys.argv[2]); j=json.dumps(s.get('worker'),allow_nan=False,separators=(',',':')); assert len(j)<=16384; print(j)"


def process_birth(pid):
    if type(pid) is not int or pid <= 0:
        return None
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def owned_lease(path, pid):
    """Observe an existing flock and its Linux holder; never create/write it."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            for line in Path('/proc/locks').read_text().splitlines():
                fields = line.split()
                if len(fields) < 6 or fields[1:4] != ['FLOCK', 'ADVISORY', 'WRITE']:
                    continue
                major, minor, inode = fields[5].split(':')
                if (int(fields[4]) == pid and int(inode) == info.st_ino
                        and int(major, 16) == os.major(info.st_dev)
                        and int(minor, 16) == os.minor(info.st_dev)):
                    return True
        return False
    except (OSError, ValueError):
        return False
    finally:
        os.close(fd)


def read_worker(spec, cwd, stop, timeout=5):
    """Bounded, cancellable read_status in an owned short-lived subprocess.

    A corrupt/locked journal or a stuck projection cannot stall this parent.
    The helper stays in the outer owned group, inherits env without logging it,
    and is always reaped. Its output contains worker fields only.
    """
    health = spec['health']
    if health['module'] not in HEALTH_MODULES:
        raise ValueError('Unknown worker projection')
    probe = subprocess.Popen([spec['argv'][0], '-B', '-c', WORKER_QUERY,
                              health['module'], str(health['db'])], cwd=cwd,
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, close_fds=True)
    deadline = time.monotonic() + timeout
    reader = selectors.DefaultSelector()
    reader.register(probe.stdout, selectors.EVENT_READ)
    os.set_blocking(probe.stdout.fileno(), False)
    output, eof = bytearray(), False
    try:
        while not stop.is_set() and time.monotonic() < deadline:
            remaining = max(.001, deadline-time.monotonic())
            if not eof:
                for _, _ in reader.select(min(.1, remaining)):
                    chunk = os.read(probe.stdout.fileno(), 16385-len(output))
                    if not chunk:
                        eof = True
                        reader.unregister(probe.stdout)
                        break
                    output.extend(chunk)
                    if len(output) > 16384:
                        raise ValueError('Worker projection output limit')
            else:
                stop.wait(min(.1, remaining))
            if eof and probe.poll() is not None:
                if probe.returncode != 0:
                    raise ValueError('Worker projection unavailable')
                worker = json.loads(output)
                if not isinstance(worker, dict):
                    raise ValueError('Worker receipt missing')
                return worker
        raise ValueError('Worker projection deadline or stop')
    finally:
        reader.close()
        if probe.poll() is None:
            probe.terminate()
            try:
                probe.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                probe.kill()
        probe.wait(timeout=5)
        if probe.stdout:
            probe.stdout.close()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_status(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError('Service status requires an ordinary file')
    fd, tmp = tempfile.mkstemp(prefix='.services-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, separators=(',', ':'), allow_nan=False)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def installed_specs(directory, container_mode=False):
    """Read projections only. Missing/corrupt components never become installs."""
    sys.path.insert(0, str(ROOT))
    from backend.prospective_projection import prospective_snapshot
    primary = Path(os.environ.get('ASTER_DB_PATH') or Path(directory)/'aster.sqlite').resolve()
    projection = prospective_snapshot(Path(directory) / primary.name)
    python = sys.executable if container_mode else str(ROOT / '.venv/bin/python')
    main_command = ([python, '-m', 'uvicorn', 'backend.app:app', '--host', os.environ.get('ASTER_HOST', '0.0.0.0'),
                     '--port', os.environ.get('ASTER_PORT', '8787')] if container_mode else [str(ROOT/'run.sh')])
    specs = [{'name':'main', 'required':True, 'argv':main_command}]
    definitions = [
        ('native', 'ASTER_NATIVE_DB_PATH', 'native-prospective.sqlite', 'backend.prospective_native', 'native'),
        ('public_recipes', 'ASTER_RECIPE_DB_PATH', 'public-recipes.sqlite', 'backend.public_recipe_runtime', 'recipe'),
        ('original_research', 'ASTER_ORIGINAL_RESEARCH_DB_PATH', 'original-research.sqlite', 'backend.original_research_runtime', 'research'),
    ]
    for key, variable, filename, module, name in definitions:
        current = projection[key]
        exists = current.get('installed') is True or current.get('installed_count', 0) > 0
        if key == 'original_research':
            exists = (current.get('registered') is True
                      and current.get('status') in {'registered_unfunded_research', 'collecting_unfunded_research'}
                      and current.get('current_lineage_matches') is True)
        if not exists:
            continue
        path = str(Path(os.environ.get(variable) or Path(directory)/filename).resolve())
        if key == 'native':
            command = [python, '-m', module, '--db', path, 'serve', '--interval', '30']
        elif key == 'public_recipes':
            command = [python, '-m', module, 'serve', '--db', path, '--interval', '20']
        else:
            command = [python, '-m', module, 'serve', '--db', path, '--operating-db', str(primary), '--interval', '300']
        specs.append({'name':name, 'required':False, 'argv':command,
                      'health':{'kind':name, 'module':module, 'db':path,
                                'interval_seconds':300 if name == 'research' else 30 if name == 'native' else 20,
                                'lease':path + ('.collector.lock' if name == 'research' else '.worker.lock')}})
    return specs


class ServiceCoordinator:
    def __init__(self, specs, status_path, cwd=ROOT, poll_seconds=.2,
                 initial_backoff=1, maximum_backoff=60, shutdown_seconds=15,
                 startup_grace=120, health_interval=15, health_failures=2,
                 status_reader=None):
        names = [s['name'] for s in specs]
        if len(names) != len(set(names)) or not specs or not all(s.get('argv') for s in specs):
            raise ValueError('Unique named service commands required')
        self.specs = {s['name']:dict(s) for s in specs}
        self.status_path, self.cwd = Path(status_path), Path(cwd)
        self.poll_seconds = poll_seconds
        self.initial_backoff, self.maximum_backoff = initial_backoff, maximum_backoff
        self.shutdown_seconds = shutdown_seconds
        numbers = (poll_seconds, initial_backoff, maximum_backoff, shutdown_seconds, startup_grace, health_interval)
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0 for x in numbers):
            raise ValueError('Positive finite coordinator timing required')
        if maximum_backoff < initial_backoff or type(health_failures) is not int or health_failures < 1:
            raise ValueError('Invalid backoff or failure count')
        self.startup_grace, self.health_interval, self.health_failures = startup_grace, health_interval, health_failures
        self.status_reader = status_reader or read_worker
        self.stop = threading.Event()
        self.processes, self.states = {}, {}

    def launch(self, name):
        spec = self.specs[name]
        # No shell, no detached sessions, no inherited listener/lease FDs.
        child = subprocess.Popen(spec['argv'], cwd=self.cwd, close_fds=True)
        self.processes[name] = child
        previous = self.states.get(name, {})
        self.states[name] = {'pid':child.pid, 'started_at':stamp(), 'started_mono':time.monotonic(),
            'attempts':previous.get('attempts', 0)+1, 'backoff':previous.get('backoff', self.initial_backoff),
            'required':bool(spec.get('required')), 'status':'process_started', 'next_attempt':None,
            'pid_birth':process_birth(child.pid), 'next_health':time.monotonic()+self.startup_grace,
            'health_failures':0, 'healthy_since':None,
            'health_recoveries':previous.get('health_recoveries', 0),
            'last_health_failure':previous.get('last_health_failure')}

    def snapshot(self):
        return {'at':stamp(), 'pid':os.getpid(), 'paper_only':True, 'installs_or_fundings':0,
            'recovery_scope':'Owned child exits and stale/mismatched companion heartbeat/lease recovery while coordinator and outer supervisor remain alive; no hostboot guarantee',
            'health_policy':{'startup_grace_seconds':self.startup_grace, 'check_interval_seconds':self.health_interval,
                             'consecutive_failures':self.health_failures, 'projection_deadline_seconds':5},
            'services':{name:{k:v for k,v in state.items() if k not in {'started_mono','next_attempt','next_health','healthy_since'}}
                        for name,state in self.states.items()}}

    def owned_child(self, name):
        child, state = self.processes[name], self.states[name]
        return (child.poll() is None and state['pid_birth'] is not None
                and process_birth(child.pid) == state['pid_birth'])

    def terminate_child(self, name):
        """Signal only this unreaped Popen child with matching birth identity."""
        child = self.processes[name]
        if self.owned_child(name):
            child.terminate()
        deadline = time.monotonic()+self.shutdown_seconds
        while child.poll() is None and time.monotonic() < deadline:
            try:
                child.wait(timeout=min(.1, max(.001, deadline-time.monotonic())))
            except subprocess.TimeoutExpired:
                pass
        if self.owned_child(name):
            child.kill()
        if child.poll() is None and not self.owned_child(name):
            raise RuntimeError('Owned child identity unavailable; no foreign signal authorized')
        child.wait(timeout=5)

    def health_reason(self, name, worker):
        """Validate independent projection fields against the owned child."""
        spec, child, state = self.specs[name], self.processes[name], self.states[name]
        health = spec['health']; kind = health['kind']
        keys = {'native':('process_start','at','running'),
                'recipe':('pid_birth_tick','heartbeat_at','running'),
                'research':('process_birth','observed_at','active')}
        if kind not in keys or not isinstance(worker, dict):
            return 'invalid_worker_receipt'
        birth_key, at_key, active_key = keys[kind]
        if (not self.owned_child(name) or type(worker.get('pid')) is not int or worker['pid'] != child.pid
                or worker.get(birth_key) != state['pid_birth']):
            return 'worker_ownership_mismatch'
        try:
            observed = datetime.fromisoformat(worker[at_key].replace('Z', '+00:00'))
            if observed.tzinfo is None:
                return 'invalid_heartbeat_clock'
            age = (datetime.now(timezone.utc)-observed).total_seconds()
            limit = 120
            if kind in {'recipe','research'}:
                interval = worker['interval_seconds']
                if (type(interval) not in (int, float) or not math.isfinite(interval)
                        or interval != health['interval_seconds']):
                    return 'worker_interval_mismatch'
                limit = max(180, 2*interval+30) if kind == 'recipe' else max(120, 2*interval+75)
                if kind == 'research' and worker.get('stale_after_seconds') != limit:
                    return 'worker_stale_policy_mismatch'
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
            return 'invalid_heartbeat_clock'
        state['heartbeat_age_seconds'], state['stale_after_seconds'] = age, limit
        if age < 0 or age > limit:
            return 'stale_or_future_heartbeat'
        if worker.get(active_key) is not True:
            return 'inactive_worker_receipt'
        if kind == 'native' and (worker.get('process_alive') is not True or worker.get('stale') is not False):
            return 'invalid_native_liveness'
        if kind == 'recipe' and (worker.get('process_alive_with_matching_birth') is not True
                                or worker.get('stale') is not False or worker.get('phase') != 'running'):
            return 'invalid_recipe_liveness'
        if kind == 'research' and (worker.get('pid_birth_matches') is not True
                                  or worker.get('lease_held') is not True or worker.get('state') not in {'sleeping','collecting'}):
            return 'invalid_research_liveness'
        if not owned_lease(health['lease'], child.pid):
            return 'worker_lease_not_owned'
        return None

    def check_health(self, name, now):
        spec, state = self.specs[name], self.states[name]
        if not spec.get('health'):
            if now-state['started_mono'] >= 300:
                state['backoff'] = self.initial_backoff
            state['status'] = 'process_alive'
            return
        if now < state['next_health']:
            state['status'] = 'health_startup_grace' if now-state['started_mono'] < self.startup_grace else state['status']
            return
        state['next_health'] = now+self.health_interval
        try:
            worker = self.status_reader(spec, self.cwd, self.stop)
            reason = self.health_reason(name, worker)
        except Exception:
            # Never export projection/DB bodies, environment or error text.
            reason = 'worker_projection_unavailable'
        if self.stop.is_set():
            return
        state['last_health_check_at'] = stamp()
        if reason is None:
            state['health_failures'] = 0
            state['healthy_since'] = state['healthy_since'] or now
            if now-state['healthy_since'] >= 300:
                state['backoff'] = self.initial_backoff
            state['status'] = 'worker_healthy'
        else:
            state['healthy_since'] = None
            state['health_failures'] += 1
            state['last_health_failure'] = reason
            state['status'] = 'worker_health_failure'
            if state['health_failures'] >= self.health_failures:
                self.terminate_child(name)
                state['health_recoveries'] += 1
                state.update(status='worker_health_recovery', exit_code=self.processes[name].returncode,
                             exited_at=stamp(), next_attempt=time.monotonic()+state['backoff'])

    def shutdown(self):
        # Send every own-child TERM first, then bound the total grace period.
        for name in self.processes:
            if self.owned_child(name):
                self.processes[name].terminate()
        deadline = time.monotonic()+self.shutdown_seconds
        while time.monotonic() < deadline and any(p.poll() is None for p in self.processes.values()):
            time.sleep(min(.1, max(0, deadline-time.monotonic())))
        for name, process in self.processes.items():
            if self.owned_child(name):
                process.kill()
            if process.poll() is None and not self.owned_child(name):
                raise RuntimeError('Owned child identity unavailable; no foreign signal authorized')
            process.wait(timeout=5)
        for state in self.states.values():
            state['status'] = 'stopped'

    def run(self):
        result = 0
        try:
            for name in self.specs:
                self.launch(name)
            last_write = 0
            while not self.stop.is_set():
                now = time.monotonic()
                for name, spec in self.specs.items():
                    child, state = self.processes[name], self.states[name]
                    code = child.poll()
                    if code is None:
                        self.check_health(name, now)
                        continue
                    if state['next_attempt'] is None:
                        state.update(status='process_exited', exit_code=code, exited_at=stamp())
                        if spec.get('required'):
                            # The outer supervisor must launch a fresh coherent
                            # group rather than leave companions without Aster.
                            result = 1; self.stop.set(); break
                        state['next_attempt'] = now+state['backoff']
                    if now >= state['next_attempt']:
                        state['backoff'] = min(self.maximum_backoff, state['backoff']*2)
                        self.launch(name)
                if now-last_write >= 1:
                    write_status(self.status_path, self.snapshot()); last_write = now
                self.stop.wait(self.poll_seconds)
        finally:
            self.shutdown()
            write_status(self.status_path, self.snapshot())
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('ASTER_DB_PATH') or ROOT/'data/aster.sqlite').parent)
    parser.add_argument('--container-mode', action='store_true', help='Use prebuilt image Python/frontend; no venv/npm setup')
    args = parser.parse_args()
    directory = args.data_dir.resolve()
    output = directory/'aster-services'
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output/'services.lock'
    fd = os.open(lock_path, os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return 75
        coordinator = ServiceCoordinator(installed_specs(directory, args.container_mode), output/'status.json')
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda signum, frame: coordinator.stop.set())
        return coordinator.run()
    finally:
        os.close(fd)


if __name__ == '__main__':
    raise SystemExit(main())
