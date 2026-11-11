"""Blocker for CHAIN-COMPACT-PUBLISH-20261110.

chain-explorer/data.json reached 46.7 MB written at indent=2
against ~15 MB of content, over GitHub's Contents PUT ceiling
(proven working at 41.3 MB, refused at 46.7 MB on 2026-11-10) and
over the create-blob ceiling (refused in base64 and utf-8 probes
the same night), so the hourly sync to the Test repo died on it
three times (19:12 ET PUT 422, then blob POST 422 in the fallback).
The cure is at the producer: refresh_chain.py writes compact JSON;
the content and the byte-identity between the local file and the
published artifact are unchanged (consumers JSON.parse the file).

These checks pin: (1) the producer's write call is the compact
form and carries the dated cure marker (source assertions: this
test fails on the pre-cure file, whose dump used indent=2);
(2) the regenerated data.json on disk parses, is byte-smaller
than the REST publish ceiling band, and reserializes to itself
modulo key order and the trailing newline (i.e. it really is the
compact form of the same content).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCER = os.path.join(HERE, "refresh_chain.py")
DATA = os.path.join(HERE, "chain-explorer", "data.json")

# The Contents PUT route is proven at 41,298,704 bytes and refused
# at 46,715,772; keep the published file comfortably below the
# proven-working size.
CEILING = 40 * 1024 * 1024


def test_producer_writes_compact():
    src = open(PRODUCER, encoding="utf-8").read()
    assert "CHAIN-COMPACT-PUBLISH-20261110" in src
    assert 'json.dump(data, fh, separators=(",", ":"), sort_keys=True)' in src
    assert "json.dump(data, fh, indent" not in src


def test_published_file_is_compact_and_small():
    raw = open(DATA, "rb").read()
    assert len(raw) < CEILING, len(raw)
    data = json.loads(raw)
    compact = json.dumps(data, separators=(",", ":"),
                         sort_keys=True).encode() + b"\n"
    assert raw == compact, "file on disk is not the compact form"


if __name__ == "__main__":
    test_producer_writes_compact()
    test_published_file_is_compact_and_small()
    print("test_chain_compact_publish_20261110: all passed")
