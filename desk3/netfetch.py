"""Shared HTTP fetch for the desk's network producers (EGRESS-1).

Why this exists: every desk fetch used to go through
urllib.request.urlopen, which unconditionally sends
``Connection: close`` on the origin request. Through this VM's
runtime egress proxy, a ``Connection: close`` request gets its
response stream cut mid-body when the caller runs under the systemd
service context (proven 2026-10-25: urllib reads died with
IncompleteRead at random offsets — 0 to ~122 KB — while curl,
wget, requests/urllib3, and raw http.client transfers of the same
URLs completed; a manual socket test isolated the trigger to the
``Connection: close`` header alone: keep-alive / no header completed
137 KB, close truncated at ~76 KB). http.client does not add that
header, so all desk fetches route through here.

Semantics preserved from the urllib call sites: GET/POST with
headers and a timeout, JSON responses, redirects followed for GET,
an exception on HTTP >= 400 (callers fail closed on any exception),
proxy taken from the process environment (https_proxy / http_proxy,
set for the watchdog + runner by the unit's EnvironmentFile bridge
to the runtime-maintained egress file — values are never logged).
No proxy for hosts matching no_proxy.
"""
from __future__ import annotations

import base64
import http.client
import json
import os
import urllib.parse


class FetchError(Exception):
    """BROKER-422-BODY-20261027: carries the response BODY on HTTP
    errors. Before this cure the body was read and discarded here, so
    a broker 422 (whose body names the failing field) reached the
    journal as a bare status and the failing field was unknowable
    from desk records. The body is bounded and rides both the
    exception message (so every existing journal of str(error) gains
    it) and the .body attribute (machine-readable)."""

    def __init__(self, status, url, body=None):
        self.body = body
        msg = f"HTTP {status} for {url}"
        if body:
            msg += f" body={body}"
        super().__init__(msg)
        self.status = status


def _proxy_for(parsed):
    scheme = parsed.scheme.lower()
    key = "https_proxy" if scheme == "https" else "http_proxy"
    proxy = os.environ.get(key) or os.environ.get(key.upper())
    if not proxy:
        return None
    host = (parsed.hostname or "").lower()
    no_proxy = os.environ.get("no_proxy") or os.environ.get("NO_PROXY") or ""
    for token in no_proxy.split(","):
        token = token.strip().lower()
        if token and (token == "*" or host == token
                      or host.endswith("." + token.lstrip("."))):
            return None
    return urllib.parse.urlparse(proxy)


def _proxy_auth(proxy):
    if proxy is None or not proxy.username:
        return None
    raw = "%s:%s" % (urllib.parse.unquote(proxy.username),
                     urllib.parse.unquote(proxy.password or ""))
    return "Basic " + base64.b64encode(raw.encode()).decode()


def _open(parsed, timeout):
    """Return (connection, request_target) for the URL, tunnelled
    through the egress proxy when one is configured."""
    proxy = _proxy_for(parsed)
    is_https = parsed.scheme.lower() == "https"
    port = parsed.port or (443 if is_https else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    if proxy is None:
        cls = http.client.HTTPSConnection if is_https \
            else http.client.HTTPConnection
        return cls(parsed.hostname, port, timeout=timeout), path
    pport = proxy.port or 3128
    auth = _proxy_auth(proxy)
    if is_https:
        conn = http.client.HTTPSConnection(proxy.hostname, pport,
                                           timeout=timeout)
        tunnel_headers = {}
        if auth:
            tunnel_headers["Proxy-Authorization"] = auth
        conn.set_tunnel(parsed.hostname, port, headers=tunnel_headers)
        return conn, path
    conn = http.client.HTTPConnection(proxy.hostname, pport,
                                      timeout=timeout)
    return conn, parsed.geturl()


def fetch_bytes(url, headers=None, timeout=30, method="GET", body=None,
                _redirects=5):
    parsed = urllib.parse.urlparse(url)
    conn, target = _open(parsed, timeout)
    try:
        conn.request(method, target, body=body,
                     headers=dict(headers or {}))
        resp = conn.getresponse()
        status = resp.status
        location = resp.getheader("Location")
        data = resp.read()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if status in (301, 302, 303, 307, 308) and _redirects > 0 \
            and method == "GET" and location:
        return fetch_bytes(urllib.parse.urljoin(url, location),
                           headers=headers, timeout=timeout,
                           method="GET", body=None,
                           _redirects=_redirects - 1)
    if status >= 400:
        body = data.decode("utf-8", "replace").strip()[:2000] or None
        raise FetchError(status, url, body=body)
    return data


def fetch_json(url, headers=None, timeout=30, method="GET", body=None):
    return json.loads(fetch_bytes(url, headers=headers, timeout=timeout,
                                  method=method, body=body))
