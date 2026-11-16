"""Bounded pool of persistent worker subprocesses (V3-SCOPE §7.1).
Pool size defaults to the measured core count. Each evaluation runs in a
worker under a HARD timeout: a timed-out or crashed worker is killed and
respawned, the sleeve records a 'wedged' verdict, and the pool and cycle
survive. Workers are recycled after a bounded number of evaluations
(native-memory hygiene). Worker env is stripped to the minimum: no
credentials, HOME/cwd inside the desk state root, no inherited secrets."""
from __future__ import annotations
import json, os, select, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECYCLE_AFTER = 200


def default_pool_size():
    return max(1, os.cpu_count() or 1)


def schedule_tasks(tasks, costs, size):
    """Greedy list scheduling (EFF-1): longest-known-cost first, each
    task to the currently least-loaded worker queue (ties broken by
    queue length). Costs are the pool's learned per-sleeve elapsed
    seconds from prior cycles; an unknown sleeve costs the median of
    the known ones (0 when nothing is known, which degenerates to a
    balanced count spread). Replaces round-robin-in-config-order,
    under which the worker that drew the slowest sleeve also carried
    ~half the remaining roster serially behind it."""
    known = sorted(float(v) for v in costs.values())
    default = known[len(known) // 2] if known else 0.0
    def cost(t):
        return float(costs.get(t["sleeve_id"], default))
    queues = [[] for _ in range(size)]
    loads = [0.0] * size
    for t in sorted(tasks, key=lambda t: -cost(t)):
        idx = min(range(size), key=lambda i: (loads[i], len(queues[i])))
        queues[idx].append(t)
        loads[idx] += cost(t)
    return queues


class _Worker:
    def __init__(self, pool):
        self.pool = pool
        self.tasks_done = 0
        self.spawn()

    def spawn(self):
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "PYTHONPATH": os.pathsep.join(
                   [ROOT, self.pool.sleeve_path] if self.pool.sleeve_path else [ROOT]),
               "HOME": self.pool.state_root,
               "DESK3_WORKER": "1"}
        os.makedirs(self.pool.state_root, exist_ok=True)
        self.proc = subprocess.Popen(
            [sys.executable, "-u", "-m", "desk3.worker"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            env=env, cwd=self.pool.state_root, text=True, bufsize=1)
        self._buf = ""

    def kill(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass

    def run_task(self, task, timeout_s):
        """Returns result dict; 'wedged' on timeout/crash (worker respawned)."""
        try:
            self.proc.stdin.write(json.dumps(task) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self.kill(); self.spawn()
            return {"sleeve_id": task["sleeve_id"], "status": "wedged",
                    "error": "worker_died_on_write", "intents": []}
        deadline = time.monotonic() + timeout_s
        fd = self.proc.stdout.fileno()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.kill(); self.spawn()
                return {"sleeve_id": task["sleeve_id"], "status": "wedged",
                        "error": f"timeout>{timeout_s}s", "intents": []}
            r, _, _ = select.select([fd], [], [], min(remaining, 0.25))
            if not r:
                if self.proc.poll() is not None:
                    self.kill(); self.spawn()
                    return {"sleeve_id": task["sleeve_id"], "status": "wedged",
                            "error": "worker_crashed", "intents": []}
                continue
            chunk = os.read(fd, 65536).decode(errors="replace")
            if not chunk:
                self.kill(); self.spawn()
                return {"sleeve_id": task["sleeve_id"], "status": "wedged",
                        "error": "worker_eof", "intents": []}
            self._buf += chunk
            if "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                self.tasks_done += 1
                if self.tasks_done >= RECYCLE_AFTER:
                    self.kill(); self.spawn(); self.tasks_done = 0
                return json.loads(line)


class WorkerPool:
    def __init__(self, size=None, sleeve_path=None, state_root=None,
                 timeout_s=30.0):
        self.size = size or default_pool_size()
        self.sleeve_path = sleeve_path
        self.state_root = os.path.abspath(state_root or os.path.join(ROOT, "state"))
        self.timeout_s = timeout_s
        self._workers = [_Worker(self) for _ in range(self.size)]
        self._closed = False
        self._costs = {}  # sleeve_id -> last non-wedged elapsed_s (EFF-1)

    def run(self, tasks, timeout_s=None):
        """Distribute tasks across workers (one thread per worker, serial
        per worker), scheduled by learned cost (EFF-1). Returns
        {sleeve_id: result}."""
        timeout_s = self.timeout_s if timeout_s is None else timeout_s
        results = {}
        queues = schedule_tasks(tasks, self._costs, self.size)

        def drain(idx, queue):
            w = self._workers[idx]
            for t in queue:
                t0 = time.monotonic()
                r = w.run_task(t, timeout_s)
                r.setdefault("elapsed_s", round(time.monotonic() - t0, 3))
                results[t["sleeve_id"]] = r
                if r.get("status") != "wedged":
                    self._costs[t["sleeve_id"]] = float(r["elapsed_s"])

        threads = [threading.Thread(target=drain, args=(i, q))
                   for i, q in enumerate(queues) if q]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        return results

    def close(self):
        if self._closed:
            return
        self._closed = True
        for w in self._workers:
            try:
                w.proc.stdin.close()
            except Exception:
                pass
            try:
                w.proc.wait(timeout=3)
            except Exception:
                w.kill()
