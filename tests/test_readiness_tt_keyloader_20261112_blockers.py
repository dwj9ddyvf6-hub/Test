"""READINESS-TT-KEYLOADER-20261112 blockers (TT-KEY-LOADER-CURE).

Defect (2026-11-12 morning, proven live): a fresh TastyTrade
mint from ~/.config/muse-desk/tastytrade.key failed with HTTP
400 invalid_grant, "Client secret mismatch" — because at capture
time the file's client_secret field was EMPTY, and the ad-hoc
parse used by the session that read it masked the empty field
instead of failing. There was no canonical mint path at all:
every session hand-rolled its own read of the key file.

Cure: a canonical loader at
~/workspace/custom-connectors/custom.tastytrade/tt_mint.py with
an ANCHORED parse: every line must be one of the three known
fields in NAME=value form, all three fields are required, and
every value must be non-empty; any violation raises KeyFileError
naming the field and the defect BEFORE any HTTP call. The mint
follows CONNECTOR.md (POST /oauth/token, User-Agent
midna-desk/1.0 required).

Fail direction: before the cure the loader module does not
exist and this file errors on load; the empty-secret fixture is
the exact 2026-11-12 failure shape.
"""
import importlib.util
import os
import tempfile
import unittest

LOADER = os.path.expanduser(
    "~/workspace/custom-connectors/custom.tastytrade/tt_mint.py")


def _load():
    spec = importlib.util.spec_from_file_location("tt_mint", LOADER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GOOD = ("TASTYTRADE_CLIENT_ID=cid-fixture\n"
        "TASTYTRADE_CLIENT_SECRET=secret-fixture\n"
        "TASTYTRADE_REFRESH_TOKEN=rt-fixture\n")
EMPTY_SECRET = ("TASTYTRADE_CLIENT_ID=cid-fixture\n"
                "TASTYTRADE_CLIENT_SECRET=\n"
                "TASTYTRADE_REFRESH_TOKEN=rt-fixture\n")
MISSING_FIELD = ("TASTYTRADE_CLIENT_ID=cid-fixture\n"
                 "TASTYTRADE_REFRESH_TOKEN=rt-fixture\n")
UNANCHORED_LINE = ("TASTYTRADE_CLIENT_ID=cid-fixture\n"
                   "TASTYTRADE_CLIENT_SECRET=secret-fixture\n"
                   "TASTYTRADE_REFRESH_TOKEN=rt-fixture\n"
                   "NOTE=TASTYTRADE_CLIENT_SECRET=\n")


def _keyfile(body):
    fh = tempfile.NamedTemporaryFile("w", delete=False)
    fh.write(body)
    fh.close()
    return fh.name


class TestAnchoredParse(unittest.TestCase):
    def test_good_file_parses(self):
        mod = _load()
        vals = mod.load_key_file(_keyfile(GOOD))
        self.assertEqual(vals["TASTYTRADE_CLIENT_ID"], "cid-fixture")
        self.assertEqual(vals["TASTYTRADE_CLIENT_SECRET"],
                         "secret-fixture")
        self.assertEqual(vals["TASTYTRADE_REFRESH_TOKEN"],
                         "rt-fixture")

    def test_empty_secret_fails_loudly(self):
        mod = _load()
        with self.assertRaises(mod.KeyFileError) as cm:
            mod.load_key_file(_keyfile(EMPTY_SECRET))
        self.assertIn("TASTYTRADE_CLIENT_SECRET", str(cm.exception))

    def test_missing_field_fails_loudly(self):
        mod = _load()
        with self.assertRaises(mod.KeyFileError) as cm:
            mod.load_key_file(_keyfile(MISSING_FIELD))
        self.assertIn("TASTYTRADE_CLIENT_SECRET", str(cm.exception))

    def test_unanchored_line_fails_loudly(self):
        mod = _load()
        with self.assertRaises(mod.KeyFileError):
            mod.load_key_file(_keyfile(UNANCHORED_LINE))


if __name__ == "__main__":
    unittest.main()
