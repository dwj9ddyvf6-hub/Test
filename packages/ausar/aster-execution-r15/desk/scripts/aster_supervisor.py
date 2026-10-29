#!/usr/bin/env python3
"""Own-child Aster process supervisor; standard library, Linux, no financial writes.

The supervisor has no broker/database authority. Start only after an operator has
coordinated stopping any earlier server. An occupied health port fails closed.
"""
from __future__ import annotations

import argparse
import ctypes
import fcntl
import errno
import hashlib
import json
import math
import os
import platform
import signal
import shutil
import select
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc
EX_CONFIG, EX_TEMPFAIL = 78, 75
MAX_HEALTH_BYTES = 2_000_000


def utcnow():
    return datetime.now(UTC).isoformat()


def sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def source_fingerprint(root, selected=()):
    root = Path(root).resolve()
    if selected:
        paths = [root / name for name in selected]
    else:
        paths = [root / 'run.sh']
        paths += list((root / 'scripts').rglob('*.py'))
        paths += list((root / 'scripts').rglob('*.sh'))
        paths += [p for p in (root / 'requirements.txt', root / 'requirements-lock.txt', root / 'frontend/package-lock.json') if p.exists()]
        paths += [root / name for name in ('Dockerfile', '.dockerignore', 'compose.yaml', 'compose.yml', 'docker-compose.yml', 'docker-compose.yaml') if (root / name).is_file()]
        paths += list((root / 'backend').rglob('*.py'))
        paths += [p for p in (root / 'strategies').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    result = {}
    for path in sorted(set(paths)):
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root) or not path.is_file() or path.name == '.env':
            raise ValueError('Source pins must be ordinary in-project non-secret files')
        relative = str(path.relative_to(root))
        result[relative] = {'sha256': sha256(path), 'bytes': path.stat().st_size, 'mode': stat.S_IMODE(path.stat().st_mode)}
    if not result:
        raise ValueError('At least one source pin is required')
    return result


def runtime_fingerprint():
    executable = Path(sys.executable).resolve()
    return {'python_version': platform.python_version(), 'python_executable': str(executable),
            'python_executable_sha256': sha256(executable), 'kernel': platform.release(), 'platform': sys.platform}


def proc_identity(pid):
    """Read only identity fields, never a process environment or command line."""
    try:
        data = (Path('/proc') / str(pid) / 'stat').read_text()
        fields = data[data.rfind(')') + 2:].split()
        return {'pid': pid, 'state': fields[0], 'ppid': int(fields[1]), 'pgid': int(fields[2]),
                'sid': int(fields[3]), 'start_ticks': int(fields[19])}
    except (OSError, ValueError, IndexError):
        return None


def group_members(pgid):
    result = {}
    for entry in Path('/proc').iterdir():
        if entry.name.isdecimal():
            item = proc_identity(int(entry.name))
            if item and item['pgid'] == pgid and item['sid'] == pgid:
                result[item['pid']] = item
    return result


def enable_subreaper():
    """Adopt/reap only orphaned descendants of this supervisor on Linux."""
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'Subreaper setup failed')
    enabled = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(enabled), 0, 0, 0) != 0 or enabled.value != 1:
        raise OSError('Subreaper setup was not confirmed')


def listener_inodes(port, host='127.0.0.1'):
    """Only listeners capable of serving this literal host and address family."""
    result = set()
    ipv6 = ':' in host
    name, family, wildcard = ('tcp6', socket.AF_INET6, '::') if ipv6 else ('tcp', socket.AF_INET, '0.0.0.0')
    try:
        lines = (Path('/proc/net') / name).read_text().splitlines()[1:]
    except OSError:
        return result
    for line in lines:
        try:
            fields = line.split()
            address, raw_port = fields[1].split(':')
            packed = bytes.fromhex(address)
            packed = b''.join(packed[i:i+4][::-1] for i in range(0, len(packed), 4))
            bound_host = socket.inet_ntop(family, packed)
            if fields[3] == '0A' and int(raw_port, 16) == port and bound_host in {host, wildcard}:
                result.add(fields[9])
        except (ValueError, IndexError, OSError):
            continue
    return result


def group_owns_listener(members, port, host='127.0.0.1'):
    targets = listener_inodes(port, host)
    owned = set()
    for pid in members:
        directory = Path('/proc') / str(pid) / 'fd'
        try:
            entries = list(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                target = os.readlink(entry)
            except OSError:
                continue
            if target.startswith('socket:['):
                owned.add(target[8:-1])
    # All matching listeners must be ours, including wildcard/SO_REUSEPORT
    # listeners; one own socket cannot authorize a competing foreign endpoint.
    return bool(targets) and targets.issubset(owned)


def loopback_endpoint(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', '::1'} or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment or parsed.path != '/api/health'):
        raise ValueError('Health must be credential-free HTTP on literal loopback /api/health')
    return parsed.hostname, parsed.port or 80


def port_occupied(host, port):
    family = socket.AF_INET6 if ':' in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as connection:
        connection.settimeout(.5)
        return connection.connect_ex((host, port)) == 0


class ConfigurationBlocked(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def bounded_health_request(host, port, timeout, stop_event):
    """Small strict HTTP client with an absolute deadline and cancellable I/O.

    Aster's JSON health endpoint uses Content-Length. Close-delimited HTTP/1.0
    fixtures are also supported. Transfer/content encodings are rejected rather
    than accepting ambiguous framing. No proxy, credentials or redirects.
    """
    deadline = time.monotonic() + timeout
    family = socket.AF_INET6 if ':' in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setblocking(False)

    def ready(read=False):
        while not stop_event.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Health deadline exceeded')
            readable, writable, _ = select.select([sock] if read else [], [] if read else [sock], [], min(remaining, .1))
            if readable or writable:
                return
        raise InterruptedError('Supervisor stopping')

    try:
        result = sock.connect_ex((host, port))
        if result not in {0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY}:
            raise OSError('Health connection failed')
        ready()
        if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
            raise OSError('Health connection failed')
        header_host = '[' + host + ']' if ':' in host else host
        request = ('GET /api/health HTTP/1.1\r\nHost: ' + header_host + ':' + str(port)
                   + '\r\nAccept: application/json\r\nConnection: close\r\n\r\n').encode('ascii')
        offset = 0
        while offset < len(request):
            ready()
            try:
                sent = sock.send(request[offset:])
            except BlockingIOError:
                continue
            if not sent:
                raise OSError('Health connection closed')
            offset += sent
        raw = bytearray()
        body_offset = None
        length = None
        while True:
            ready(read=True)
            try:
                part = sock.recv(16384)
            except BlockingIOError:
                continue
            if not part:
                if body_offset is None or length is not None and len(raw) - body_offset != length:
                    raise ValueError('Incomplete health response')
                break
            raw.extend(part)
            if body_offset is None:
                marker = raw.find(b'\r\n\r\n')
                if marker < 0:
                    if len(raw) > 8192:
                        raise ValueError('Health headers too large')
                    continue
                if marker > 8192:
                    raise ValueError('Health headers too large')
                lines = bytes(raw[:marker]).decode('ascii').split('\r\n')
                status_parts = lines[0].split()
                if len(status_parts) < 2 or status_parts[0] not in {'HTTP/1.0','HTTP/1.1'} or status_parts[1] != '200':
                    raise ValueError('Health status is not 200')
                headers = {}
                for line in lines[1:]:
                    name, separator, value = line.partition(':')
                    if not separator or name.lower() in headers:
                        raise ValueError('Invalid or duplicate health header')
                    headers[name.lower()] = value.strip()
                if 'transfer-encoding' in headers or headers.get('content-encoding','identity').lower() != 'identity':
                    raise ValueError('Encoded health response unsupported')
                if 'content-length' in headers:
                    if not headers['content-length'].isdecimal():
                        raise ValueError('Invalid health length')
                    length = int(headers['content-length'])
                    if length > MAX_HEALTH_BYTES:
                        raise ValueError('Health response too large')
                body_offset = marker + 4
            body_size = len(raw) - body_offset
            if body_size > MAX_HEALTH_BYTES or length is not None and body_size > length:
                raise ValueError('Health response too large or overframed')
            if length is not None and body_size == length:
                break
        return json.loads(bytes(raw[body_offset:]))
    finally:
        sock.close()


def assess_health(payload, heartbeat_limit, now=None):
    """Lease validity is the runtime's worker_alive field; recompute bar-free age.

    Do not restart a healthy thread because research/provider work is slow or an
    operator paused entries. Paused state still requires the operational worker's
    fresh heartbeat and valid lease (Aster renews them even while paused).
    """
    now = now or datetime.now(UTC)
    if not isinstance(payload, dict) or not isinstance(payload.get('autonomy'), dict):
        return {'ok': False, 'reason': 'invalid_health_schema'}
    item = payload['autonomy']
    if type(item.get('running')) is not bool or type(item.get('worker_alive')) is not bool:
        return {'ok': False, 'reason': 'invalid_worker_flags'}
    try:
        text = item.get('heartbeat_at')
        if not isinstance(text, str):
            raise ValueError
        heartbeat = datetime.fromisoformat(text.replace('Z', '+00:00'))
        if heartbeat.tzinfo is None:
            raise ValueError
        age = (now - heartbeat.astimezone(UTC)).total_seconds()
        reported = item.get('heartbeat_age_seconds')
        if type(reported) not in (int, float) or not math.isfinite(reported) or reported < -2:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        return {'ok': False, 'reason': 'invalid_heartbeat'}
    if age < -2:
        return {'ok': False, 'reason': 'future_heartbeat', 'heartbeat_age_seconds': age}
    if not item['worker_alive']:
        return {'ok': False, 'reason': 'worker_lease_or_thread_unavailable', 'heartbeat_age_seconds': age}
    if age > heartbeat_limit or reported > heartbeat_limit:
        return {'ok': False, 'reason': 'stale_heartbeat', 'heartbeat_age_seconds': age}
    return {'ok': True, 'reason': 'operator_paused' if not item['running'] else 'fresh_worker',
            'heartbeat_age_seconds': age, 'worker_alive': True, 'running': item['running'],
            'progress_stale': item.get('progress_stale') is True, 'desk_healthy': item.get('healthy') is True}


def verify_receipt_fd(fd):
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        os.close(fd)
        raise ValueError('Opened receipt is not a unique regular file')


def atomic_json(path, value):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class Config:
    root: Path
    command: tuple[str, ...]
    health_url: str = 'http://127.0.0.1:8787/api/health'
    lock: Path | None = None
    events: Path | None = None
    status: Path | None = None
    child_log: Path | None = None
    output_dir: Path | None = None
    source_files: tuple[str, ...] = ()
    startup_grace: float = 180
    poll: float = 1
    health_interval: float = 30
    health_timeout: float = 10
    heartbeat_limit: float = 90
    failure_limit: int = 3
    backoff_initial: float = 1
    backoff_max: float = 60
    stable_seconds: float = 300
    shutdown_grace: float = 30
    kill_grace: float = 5
    max_restarts: int = 0

    def validated(self):
        loopback_endpoint(self.health_url)
        if not self.root.is_dir() or not self.command or any(not isinstance(v, str) or not v or '\x00' in v for v in self.command):
            raise ValueError('Existing project root and nonempty argv required')
        for name in ('startup_grace', 'poll', 'health_interval', 'health_timeout', 'heartbeat_limit',
                     'backoff_initial', 'backoff_max', 'stable_seconds', 'shutdown_grace', 'kill_grace'):
            value = getattr(self, name)
            if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
                raise ValueError(name + ' must be finite and positive')
        if self.backoff_max < self.backoff_initial or type(self.failure_limit) is not int or self.failure_limit < 1:
            raise ValueError('Invalid retry settings')
        if type(self.max_restarts) is not int or self.max_restarts < 0:
            raise ValueError('max_restarts must be a nonnegative integer')
        if sys.platform != 'linux' or not Path('/proc/self/stat').exists():
            raise ValueError('Linux proc identity and listener ownership support are required')
        return self


class Supervisor:
    def __init__(self, config):
        self.config = config.validated()
        self.stop = threading.Event()
        self.stop_signal = None
        self.child = None
        self.known = {}
        self.tracked_descendants = {}
        self.lock_handle = None
        self.fingerprints = None
        self.supervisor_code_sha256 = sha256(Path(__file__))
        self.state = {'schema': 1, 'supervisor_pid': os.getpid(), 'started_at': utcnow(), 'state': 'constructed',
                      'financial_authority': 'none', 'host_reset_recovery': 'requires_external_container_or_host_orchestrator'}
        self.output_dir = (config.output_dir or config.root / 'data/aster-supervisor').resolve()
        root = config.root.resolve()
        if root.is_relative_to(self.output_dir) or (self.output_dir.is_relative_to(root) and
                (not self.output_dir.is_relative_to(root / 'data') or self.output_dir == root / 'data')):
            raise ValueError('Use a dedicated data subdirectory or external receipt volume')
        self.protected_sources = {(root / name).resolve() for name in source_fingerprint(root, config.source_files)}
        self.protected_sources.add(Path(__file__).resolve())
        for argument in config.command:
            candidate = Path(argument) if Path(argument).is_absolute() else root / argument
            if candidate.is_file():
                self.protected_sources.add(candidate.resolve())
        command_executable = shutil.which(config.command[0])
        if command_executable:
            self.protected_sources.add(Path(command_executable).resolve())
        self.paths = {name: getattr(config, name) or self.output_dir / ('aster-supervisor.' + suffix)
                      for name, suffix in [('lock', 'lock'), ('events', 'jsonl'), ('status', 'status.json'), ('child_log', 'child.log')]}
        if len({str(Path(p).resolve()) for p in self.paths.values()}) != len(self.paths):
            raise ValueError('Supervisor output paths must be distinct')
        for path in self.paths.values():
            self.validate_output(path)

    def validate_output(self, path):
        path = Path(path)
        resolved = path.resolve()
        if not resolved.is_relative_to(self.output_dir) or resolved == self.output_dir or path.is_symlink() or resolved in self.protected_sources:
            raise ValueError('Supervisor outputs must stay in the dedicated receipt directory')
        if path.name == '.env' or path.suffix in {'.sqlite', '.sqlite3', '.db', '.env'}:
            raise ValueError('Supervisor outputs cannot target financial state or credentials')
        if path.exists():
            metadata = path.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError('Supervisor outputs cannot be special files or hard-link aliases')

    def request_stop(self, signum, frame=None):
        self.stop_signal = signum
        self.stop.set()

    def emit(self, event, **fields):
        record = {'at': utcnow(), 'event': event, **fields}
        path = self.paths['events']
        self.validate_output(path)
        self.validate_output(self.paths['status'])
        if path.exists() and path.stat().st_size > 10_000_000:
            os.replace(path, path.with_suffix(path.suffix + '.1'))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        verify_receipt_fd(fd)
        with os.fdopen(fd, 'a') as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
            handle.flush()
        self.state.update(updated_at=record['at'], last_event=event)
        atomic_json(self.paths['status'], self.state)

    def emit_cleanup(self, event, **fields):
        # Loss of disk/logging must never prevent terminating our own child.
        try:
            self.emit(event, **fields)
        except (OSError, ValueError):
            pass

    def acquire(self):
        for path in self.paths.values():
            self.validate_output(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.paths['lock'], os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        verify_receipt_fd(fd)
        self.lock_handle = os.fdopen(fd, 'r+')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock_handle.close()
            self.lock_handle = None
            return False
        os.fchmod(fd, 0o600)
        self.lock_handle.seek(0)
        self.lock_handle.truncate()
        self.lock_handle.write(json.dumps({'schema': 1, 'supervisor_pid': os.getpid(), 'started_at': self.state['started_at']}))
        self.lock_handle.flush()
        return True

    def owned_members(self):
        if self.child is None:
            return {}
        group = group_members(self.child.pid)
        seeds = {pid for pid, old in self.known.items() if pid in group and group[pid]['start_ticks'] == old['start_ticks']}
        if not seeds:
            return {}
        # A live known member proves continuity of our group/session; unrelated
        # processes cannot join this session. Never use a PID file as authority.
        self.known = group
        self.tracked_descendants.update(group)
        return {pid: item for pid, item in group.items() if item['state'] != 'Z'}

    def signal_group(self, signum):
        members = self.owned_members()
        if not members:
            return False
        try:
            os.killpg(self.child.pid, signum)
        except ProcessLookupError:
            return False
        self.emit_cleanup('owned_group_signal', child_pid=self.child.pid, pgid=self.child.pid,
                  signal=signal.Signals(signum).name, owned_members=len(members))
        return True

    def shutdown_child(self, reason):
        if self.child is None:
            return
        self.emit_cleanup('child_shutdown_requested', reason=reason, child_pid=self.child.pid)
        self.signal_group(signal.SIGTERM)
        deadline = time.monotonic() + self.config.shutdown_grace
        while self.owned_members() and time.monotonic() < deadline:
            time.sleep(min(self.config.poll, .1))
        if self.owned_members():
            self.signal_group(signal.SIGKILL)
            deadline = time.monotonic() + self.config.kill_grace
            while self.owned_members() and time.monotonic() < deadline:
                time.sleep(min(self.config.poll, .1))
        try:
            self.child.wait(timeout=self.config.kill_grace)
        except subprocess.TimeoutExpired:
            self.emit_cleanup('child_reap_timeout', child_pid=self.child.pid)
            raise RuntimeError('Owned child did not terminate')
        leftovers = self.owned_members()
        for pid, identity in list(self.tracked_descendants.items()):
            if pid == self.child.pid:
                continue
            observed = proc_identity(pid)
            if observed is not None and observed['start_ticks'] != identity['start_ticks']:
                continue
            try:
                reaped, status = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                continue
            if reaped:
                self.emit_cleanup('owned_descendant_reaped', pid=pid, returncode=os.waitstatus_to_exitcode(status))
                del self.tracked_descendants[pid]
        self.emit_cleanup('child_shutdown_complete', child_pid=self.child.pid, returncode=self.child.returncode,
                  owned_members_remaining=len(leftovers))
        if leftovers:
            raise RuntimeError('Owned group remained after kill deadline')

    def start_child(self):
        cfg = self.config
        try:
            current = source_fingerprint(cfg.root, cfg.source_files)
        except (OSError, ValueError):
            raise ConfigurationBlocked('source_fingerprint_unavailable') from None
        if current != self.fingerprints:
            raise ConfigurationBlocked('source_fingerprint_changed')
        host, port = loopback_endpoint(cfg.health_url)
        if port_occupied(host, port):
            raise ConfigurationBlocked('health_port_occupied')
        path = self.paths['child_log']
        self.validate_output(path)
        if path.exists() and path.stat().st_size > 10_000_000:
            os.replace(path, path.with_suffix(path.suffix + '.1'))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        verify_receipt_fd(fd)
        with os.fdopen(fd, 'ab') as handle:
            os.fchmod(handle.fileno(), 0o600)
            # Inherit env unchanged. Default run.sh alone loads the project's .env.
            # Do not log argv, environment, health bodies or raw exception strings.
            self.child = subprocess.Popen(cfg.command, cwd=cfg.root, stdin=subprocess.DEVNULL,
                                          stdout=handle, stderr=handle, close_fds=True, start_new_session=True)
        identity = proc_identity(self.child.pid)
        self.known = {self.child.pid: identity} if identity and identity['pgid'] == self.child.pid and identity['sid'] == self.child.pid else {}
        self.tracked_descendants = dict(self.known)
        self.state.update(state='starting', child_pid=self.child.pid, child_pgid=self.child.pid, child_started_at=utcnow())
        self.emit('child_started', child_pid=self.child.pid, pgid=self.child.pid,
                  identity_start_ticks=identity['start_ticks'] if identity else None)

    def check_health(self):
        members = self.owned_members()
        host, port = loopback_endpoint(self.config.health_url)
        if not group_owns_listener(members, port, host):
            return {'ok': False, 'reason': 'health_listener_not_owned_by_child_group'}
        try:
            payload = bounded_health_request(host, port, self.config.health_timeout, self.stop)
            return assess_health(payload, self.config.heartbeat_limit)
        except (OSError, ValueError, TimeoutError):
            return {'ok': False, 'reason': 'health_request_failed'}

    def run(self):
        if not self.acquire():
            # No shared state/log writes by a losing singleton contender.
            return EX_TEMPFAIL
        attempts = 0
        failures = 0
        delay = self.config.backoff_initial
        try:
            enable_subreaper()
            self.state['orphan_descendant_reaping'] = 'linux_child_subreaper_confirmed'
            self.fingerprints = source_fingerprint(self.config.root, self.config.source_files)
            self.state.update(source_fingerprints=self.fingerprints, runtime=runtime_fingerprint(),
                              supervisor_source_sha256=self.supervisor_code_sha256,
                              command_argv_sha256=hashlib.sha256(json.dumps(self.config.command).encode()).hexdigest(),
                              project_root=str(self.config.root), health_url=self.config.health_url,
                              receipt_paths={key:str(value) for key,value in self.paths.items()},
                              env_policy='inherited unchanged; default run.sh loads .env; no environment values recorded')
            self.emit('supervisor_started', source_files=len(self.fingerprints))
            while not self.stop.is_set():
                try:
                    self.start_child()
                except (OSError, ValueError) as exc:
                    self.state['state'] = 'configuration_blocked'
                    self.emit('startup_blocked', exception_type=type(exc).__name__, reason=getattr(exc, 'reason', 'child_spawn_failed'))
                    return EX_CONFIG
                started = time.monotonic()
                next_health = started
                healthy_since = None
                failures = 0
                restart_reason = 'process_exit'
                while not self.stop.is_set():
                    self.owned_members()
                    returncode = self.child.poll()
                    if returncode is not None:
                        self.emit('child_exited', child_pid=self.child.pid, returncode=returncode,
                                  exit_signal=signal.Signals(-returncode).name if returncode < 0 and -returncode in signal.valid_signals() else None)
                        break
                    now = time.monotonic()
                    if now >= next_health:
                        try:
                            current = source_fingerprint(self.config.root, self.config.source_files)
                        except (OSError, ValueError):
                            current = None
                        if current != self.fingerprints or sha256(Path(__file__)) != self.supervisor_code_sha256:
                            self.state['state'] = 'source_changed'
                            self.emit('source_changed_restart_blocked')
                            self.shutdown_child('source_changed')
                            return EX_CONFIG
                        health = self.check_health()
                        self.state.update(last_health=health, state='running' if health['ok'] else 'health_degraded')
                        self.emit('health_observation', **health)
                        next_health = now + self.config.health_interval
                        if health['ok']:
                            failures = 0
                            self.state['state'] = 'running'
                            healthy_since = healthy_since or now
                            if now - healthy_since >= self.config.stable_seconds:
                                attempts, delay = 0, self.config.backoff_initial
                        else:
                            healthy_since = None
                            if now - started >= self.config.startup_grace:
                                failures += 1
                                if failures >= self.config.failure_limit:
                                    restart_reason = health['reason']
                                    break
                    self.stop.wait(self.config.poll)
                if self.stop.is_set():
                    break
                # Reap/clean all surviving members before starting another child.
                self.shutdown_child(restart_reason)
                attempts += 1
                self.state.update(state='backoff', consecutive_restarts=attempts)
                if self.config.max_restarts and attempts > self.config.max_restarts:
                    self.emit('restart_budget_exhausted', consecutive_restarts=attempts)
                    return EX_TEMPFAIL
                self.emit('restart_backoff', reason=restart_reason, seconds=delay, consecutive_restarts=attempts)
                if self.stop.wait(delay):
                    break
                delay = min(self.config.backoff_max, delay * 2)
            self.state['state'] = 'stopping'
            self.emit('supervisor_stop_requested', signal=signal.Signals(self.stop_signal).name if self.stop_signal else None)
            self.shutdown_child('supervisor_stop')
            self.state['state'] = 'stopped'
            self.emit('supervisor_stopped')
            return 0
        except Exception as exc:
            # No raw exception/body/env strings enter diagnostics.
            self.state['state'] = 'failed'
            self.emit_cleanup('supervisor_failed', exception_type=type(exc).__name__)
            if self.child is not None:
                try:
                    self.shutdown_child('supervisor_error')
                except RuntimeError:
                    pass
            return EX_TEMPFAIL
        finally:
            if self.lock_handle is not None:
                self.lock_handle.close()
                self.lock_handle = None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--health-url', default='http://127.0.0.1:8787/api/health')
    for name in ('lock', 'events', 'status', 'child-log'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--source-file', action='append', default=[])
    for name, default in [('startup-grace',180),('poll',1),('health-interval',30),('health-timeout',10),
                          ('heartbeat-limit',90),('backoff-initial',1),('backoff-max',60),('stable-seconds',300),
                          ('shutdown-grace',30),('kill-grace',5)]:
        parser.add_argument('--' + name, type=float, default=default)
    parser.add_argument('--failure-limit', type=int, default=3)
    parser.add_argument('--max-restarts', type=int, default=0)
    parser.add_argument('--inspect', action='store_true', help='Print safe config/source fingerprint; start no child and create no files')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Optional argv after --; default is existing project run.sh')
    args = vars(parser.parse_args(argv))
    inspect = args.pop('inspect')
    args['root'] = args.pop('project_root').resolve()
    args['source_files'] = tuple(args.pop('source_file'))
    command = args.pop('command')
    if command[:1] == ['--']:
        command = command[1:]
    args['command'] = tuple(command) or (str(args['root'] / 'run.sh'),)
    for name in ('lock', 'events', 'status', 'child_log', 'output_dir'):
        if args[name] is not None:
            args[name] = args[name].resolve()
    return Config(**args).validated(), inspect


def main(argv=None):
    try:
        config, inspect = parse_args(argv)
        if inspect:
            print(json.dumps({'prepared_only': True, 'source_fingerprints': source_fingerprint(config.root, config.source_files),
                              'runtime': runtime_fingerprint(), 'project_root': str(config.root), 'health_url': config.health_url,
                              'command_argv_sha256': hashlib.sha256(json.dumps(config.command).encode()).hexdigest()}, sort_keys=True, indent=2))
            return 0
        supervisor = Supervisor(config)
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(signum, supervisor.request_stop)
        return supervisor.run()
    except (ValueError, OSError):
        print('Invalid or inaccessible supervisor configuration; no existing process is replaced.', file=sys.stderr)
        return EX_CONFIG


if __name__ == '__main__':
    raise SystemExit(main())
