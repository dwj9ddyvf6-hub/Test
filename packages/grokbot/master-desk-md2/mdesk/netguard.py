"""Hard total deadline for an HTTP request (stuck-desk fix 2026-10-28, Trader t220u).
urllib's `timeout` is per socket operation: a stalled DNS lookup, a slow-drip body or a hung TLS handshake can still outlast it.
urlopen_read() runs the request on a daemon thread and gives up after `total` seconds (raises TimeoutError); the abandoned thread
ends on its own when its socket times out. Works from any thread (unlike signal alarms)."""
import threading, urllib.request

def urlopen_read(rq, timeout=20, total=None):
    total = total or timeout * 2
    box = {}
    def run():
        try:
            with urllib.request.urlopen(rq, timeout=timeout) as r: box["b"] = r.read()
        except BaseException as e: box["e"] = e
    t = threading.Thread(target=run, daemon=True); t.start(); t.join(total)
    if t.is_alive(): raise TimeoutError(f"hard deadline {total}s exceeded")
    if "e" in box: raise box["e"]
    return box["b"]
