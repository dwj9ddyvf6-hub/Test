"""Hard deadlines for every network call.

Failure story: one slow request (no total deadline; the socket timeout only covers idle time)
stalled the whole trading pass for over an hour, so a time-based exit was missed. A
per-request *total* deadline plus a per-pass deadline fixes this class of failure.

Policy:
  * GET: retry a few times with backoff (network error, 429, 5xx). Honour Retry-After.
  * POST that creates an order: NEVER blind-retry. On a transport error the order may have
    landed; the caller must look the order up by client_order_id first (see broker.py).
"""
from __future__ import annotations
import concurrent.futures as cf
import time
import urllib.error
import urllib.request

_POOL = cf.ThreadPoolExecutor(max_workers=8, thread_name_prefix="netguard")


class DeadlineExceeded(Exception):
    pass


def urlopen_read(req: urllib.request.Request, total_deadline_s: float = 40.0) -> tuple[int, bytes, dict]:
    """Return (status, body, headers) or raise DeadlineExceeded. The *total* time is bounded."""
    def _do():
        try:
            with urllib.request.urlopen(req, timeout=min(total_deadline_s, 30)) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:  # 4xx/5xx still carry a status and body
            return e.code, e.read(), dict(e.headers or {})
    fut = _POOL.submit(_do)
    try:
        return fut.result(timeout=total_deadline_s)
    except cf.TimeoutError as e:
        raise DeadlineExceeded(f"{req.full_url} exceeded {total_deadline_s}s") from e


def get_with_retry(req, tries: int = 3, backoff=(1, 2, 4), total_deadline_s: float = 40.0, sleep=time.sleep):
    last = None
    for i in range(tries):
        try:
            status, body, hdr = urlopen_read(req, total_deadline_s)
            if status == 429 or status >= 500:
                wait = min(float(hdr.get("Retry-After", backoff[min(i, len(backoff) - 1)])), 10)
                last = RuntimeError(f"HTTP {status}")
                sleep(wait)
                continue
            return status, body, hdr
        except (DeadlineExceeded, urllib.error.URLError, OSError) as e:
            last = e
            sleep(backoff[min(i, len(backoff) - 1)])
    raise last


class PassDeadline:
    """Monotonic budget for one trading pass (monotonic: immune to wall-clock jumps)."""

    def __init__(self, seconds: float):
        self.end = time.monotonic() + seconds

    def left(self) -> float:
        return self.end - time.monotonic()

    def expired(self) -> bool:
        return self.left() <= 0
