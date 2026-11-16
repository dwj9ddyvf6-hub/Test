"""EGRESS-1 blockers: the watchdog systemd unit must bridge the
runtime egress config into the watchdog (and the runner it launches).

System units do not import /etc/environment.d, so without an explicit
EnvironmentFile line the watchdog/runner have no proxy env and every
network producer fails closed ({}) in live cycles. The referenced file
is runtime-maintained and holds the egress proxy + CA config; only its
PATH may appear in the repo — never any value from it.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIT = os.path.join(ROOT, "desk3", "systemd", "muse-desk-v3-watchdog.service")
LINE = "EnvironmentFile=-/etc/environment.d/80-hatch-egress.conf"


def _service_section(text):
    in_service = False
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_service = s == "[Service]"
            continue
        if in_service:
            out.append(raw)
    return out


class TestEgressUnitBlockers(unittest.TestCase):
    def setUp(self):
        with open(UNIT) as fh:
            self.text = fh.read()

    def test_environmentfile_line_in_service_section(self):
        service = [l.strip() for l in _service_section(self.text)]
        self.assertIn(LINE, service)

    def test_environmentfile_is_optional_dash_form(self):
        # Leading dash: the unit must still start if the platform
        # file is ever absent.
        self.assertTrue(LINE.startswith("EnvironmentFile=-/"))

    def test_home_line_in_service_section(self):
        # EGRESS-1 (HOME half): the service env carries no HOME, so
        # ~-relative key paths (Alpaca key id, Coinalyze key) would
        # resolve to /root and miss; the unit pins the desk owner's
        # home explicitly.
        service = [l.strip() for l in _service_section(self.text)]
        self.assertIn("Environment=HOME=/home/hatch", service)

    def test_no_proxy_values_in_unit(self):
        # Only the file path may be referenced; no proxy URL/value
        # may be embedded in the repo unit.
        for token in ("http://", "https://", "HTTP_PROXY=", "HTTPS_PROXY=",
                      "ALL_PROXY=", "http_proxy=", "https_proxy="):
            if token in ("https://",):
                continue  # not applicable; URLs checked below
            self.assertNotIn(token, self.text)
        self.assertNotIn("://", self.text)


class TestNetfetchTransportBlockers(unittest.TestCase):
    """EGRESS-1 (transport half): urllib.request.urlopen sends
    ``Connection: close``, which the egress proxy truncates mid-body
    under the service context. Every in-cycle fetch module must route
    through desk3.netfetch (http.client) instead."""

    MODULES = ("producers3.py", "producers.py", "producers_g4.py",
               "warm.py", "broker.py")

    def test_modules_route_through_netfetch(self):
        for name in self.MODULES:
            with open(os.path.join(ROOT, "desk3", name)) as fh:
                src = fh.read()
            self.assertIn("netfetch", src, name)
            self.assertNotIn("urlopen", src, name)

    def test_netfetch_never_sets_connection_close(self):
        import re
        with open(os.path.join(ROOT, "desk3", "netfetch.py")) as fh:
            src = fh.read()
        # No code may set a Connection header (the docstring discusses
        # it in prose; a header assignment would be quoted).
        self.assertIsNone(re.search(r"""["']Connection["']\s*:""", src))
        self.assertIn("http.client", src)


if __name__ == "__main__":
    unittest.main()
