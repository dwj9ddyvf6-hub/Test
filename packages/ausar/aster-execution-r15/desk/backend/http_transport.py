"""Bounded synchronous HTTP entry point for the desk's thread workers.

The deadline covers connection, redirects, headers and the complete streamed
body. Requests run on one cancellable IO loop, with at most four resolver
threads. A slow DNS lookup may finish later, but its cancelled result cannot
open a connection or send a request after the caller's deadline.
"""
import asyncio
import math
import threading
import time
from queue import Empty, Queue
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout

import httpx


class ResponseTooLarge(ValueError):
    pass


_loop = None
_loop_lock = threading.Lock()


class _ResolverPool(ThreadPoolExecutor):
    """Four daemon resolver threads with no unbounded cancelled-work queue.

    The event loop requires a ThreadPoolExecutor instance. This implementation
    uses the public Future protocol and owns its workers instead of registering
    blocking DNS threads with the standard pool's interpreter-exit join hook.
    Resolver work is read-only; cancelled results cannot resume HTTP tasks.
    """
    def __init__(self):
        self._closed = threading.Event()
        self._guard = threading.Lock()
        self._slots = threading.BoundedSemaphore(4)
        self._work = Queue(maxsize=4)
        self._threads = [threading.Thread(target=self._worker, name="aster-http-resolver-" + str(i), daemon=True) for i in range(4)]
        for thread in self._threads:
            thread.start()

    def submit(self, fn, /, *args, **kwargs):
        with self._guard:
            if self._closed.is_set():
                raise RuntimeError("Resolver pool is closed")
            if not self._slots.acquire(blocking=False):
                raise OSError("Resolver capacity is unavailable")
            future = Future()
            self._work.put_nowait((future, fn, args, kwargs))
            return future

    def _worker(self):
        while True:
            try:
                future, fn, args, kwargs = self._work.get(timeout=0.1)
            except Empty:
                if self._closed.is_set():
                    return
                continue
            try:
                if future.set_running_or_notify_cancel():
                    try:
                        future.set_result(fn(*args, **kwargs))
                    except BaseException as exc:
                        future.set_exception(exc)
            finally:
                self._slots.release()

    def shutdown(self, wait=True, *, cancel_futures=False):
        with self._guard:
            self._closed.set()
            if cancel_futures:
                while True:
                    try:
                        future, _, _, _ = self._work.get_nowait()
                    except Empty:
                        break
                    future.cancel()
                    self._slots.release()
        if wait:
            for thread in self._threads:
                thread.join()


def _io_loop():
    global _loop
    with _loop_lock:
        if _loop is None:
            # asyncio.run waits for DNS executor shutdown after cancellation.
            # A shared loop avoids that unbounded per-call teardown and bounds
            # outstanding resolver threads even across repeated DNS failures.
            _loop = asyncio.new_event_loop()
            _loop.set_default_executor(_ResolverPool())
            threading.Thread(target=_loop.run_forever, name="aster-http-io", daemon=True).start()
        return _loop


def bounded_http(method, url, body=None, headers=None, *, timeout_seconds=8,
                 maximum_bytes=256000, follow_redirects=False):
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
        raise ValueError("HTTP deadline must be positive and finite")
    if isinstance(maximum_bytes, bool) or not isinstance(maximum_bytes, int) or maximum_bytes < 0:
        raise ValueError("HTTP response limit must be a nonnegative integer")

    started, finished = time.monotonic(), threading.Event()
    async def request():
        try:
            async with asyncio.timeout(timeout_seconds):
                async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=True,
                                             follow_redirects=follow_redirects) as client:
                    async with client.stream(method, url, content=body, headers=headers) as response:
                        received = bytearray()
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            received.extend(chunk)
                            if len(received) > maximum_bytes:
                                raise ResponseTooLarge("HTTP response exceeded its size limit")
                        return response.status_code, bytes(received)
        finally:
            finished.set()

    loop = _io_loop()
    if threading.current_thread().name == "aster-http-io":
        raise RuntimeError("The synchronous HTTP entry point cannot run on its IO loop")
    future = asyncio.run_coroutine_threadsafe(request(), loop)
    try:
        return future.result(timeout=max(0, timeout_seconds - (time.monotonic() - started)))
    except FutureTimeout:
        future.cancel()
        # Give cancellation a bounded cleanup window, never wait on resolver
        # shutdown. Timeout remains ambiguous for callers that transmitted.
        finished.wait(timeout=0.05)
        raise TimeoutError("HTTP request exceeded its overall deadline") from None
