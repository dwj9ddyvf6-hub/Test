"""Blocker for ENRICH-COMPACT-PRESERVE-20261111 and
SHORTVOL-COMPACT-PUBLISH-20261111.

CHAIN-COMPACT-PUBLISH-20261110 cured chain-explorer at the
producer (refresh_chain.py writes compact) and the hourly sync
proved green at 2026-11-11T03:57:03Z with the file at 12,907,232
bytes. The cure did not hold: the shared enrich pass
(enrich_all.py, run at every lane close by lane_run.py and wired
into refresh_tools.py / refresh_engines.py) calls
record_surface.enrich_file and explanation.enrich_file on every
page, and both re-serialized at indent=2. A compact file never
equals record_surface's indent=2 comparison text, so it rewrote
(reproduced live: a content-identical compact reformat at
12,909,893 bytes went back to 46,715,795 bytes after one pre-cure
enrich_file call); explanation.enrich_file rewrites
unconditionally. The 00:12 ET sync then died on a 401 against the
same file and the 01:12 ET sync on the create-blob 422. Two more
files were on the same path: refresh_shortvol.py wrote
short-volume/data.json at indent=2 itself (37,760,718 bytes), and
refresh_aichartread.py wrote compact but immediately re-inflated
its own file via record_surface.enrich_slug in the same run
(35,926,290 bytes on disk).

The cure: terminal_common.dumps_like_existing serializes in the
style of the file being replaced (single-line stays compact,
everything else keeps the house indent=2 style), and
record_surface.enrich_file, explanation.enrich_file and
stamp_provenance.py all write through it; refresh_shortvol.py
writes compact like the other two producers. Content is
identical either way (consumers JSON.parse the files).

These checks pin: (1) the helper's behavior on synthetic input
(it does not exist on the pre-cure tree, so this leg fails
there); (2) the enrichers and the stamper write through the
helper and no longer force indent=2 in their write paths
(source assertions, absent on the pre-cure files); (3) all
three producers write the compact form with their cure markers;
(4) the three data files on disk parse, sit under the publish
ceiling band, and are byte-exactly the compact form of their
content (fails on the pre-cure tree, where chain-explorer was
46,715,795 bytes at indent=2).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Same band as test_chain_compact_publish_20261110: the Contents
# PUT route is proven at 41,298,704 bytes and refused at
# 46,715,772; keep every published file comfortably below it.
CEILING = 40 * 1024 * 1024

FILES = {
    "chain-explorer": "refresh_chain.py",
    "short-volume": "refresh_shortvol.py",
    "ai-chart-read": "refresh_aichartread.py",
}


def _body(src, name):
    start = src.index(f"def {name}")
    nxt = src.find("\ndef ", start + 1)
    return src[start:] if nxt == -1 else src[start:nxt]


def test_helper_preserves_style():
    import terminal_common as tc
    data = {"b": [1, 2, {"x": "y"}], "a": 1}
    compact_in = json.dumps(data, separators=(",", ":"),
                            sort_keys=True) + "\n"
    pretty_in = json.dumps(data, indent=2, sort_keys=True) + "\n"
    assert tc.dumps_like_existing(compact_in, data) == compact_in
    assert tc.dumps_like_existing(pretty_in, data) == pretty_in
    assert json.loads(tc.dumps_like_existing(compact_in, data)) == data


def test_enrichers_write_style_preserving():
    for fname in ("record_surface.py", "explanation.py"):
        src = open(os.path.join(HERE, fname), encoding="utf-8").read()
        body = _body(src, "enrich_file")
        assert "ENRICH-COMPACT-PRESERVE-20261111" in body, fname
        assert "dumps_like_existing" in body, fname
        assert "json.dumps(data, indent" not in body, fname
    src = open(os.path.join(HERE, "stamp_provenance.py"),
               encoding="utf-8").read()
    assert "ENRICH-COMPACT-PRESERVE-20261111" in src
    assert "dumps_like_existing" in src
    assert "json.dump(out, fh, indent" not in src


def test_producers_write_compact():
    for slug, fname in FILES.items():
        src = open(os.path.join(HERE, fname), encoding="utf-8").read()
        assert 'json.dump(data, fh, separators=(",", ":"), sort_keys=True)' in src, fname
        assert "json.dump(data, fh, indent" not in src, fname
    shortvol = open(os.path.join(HERE, "refresh_shortvol.py"),
                    encoding="utf-8").read()
    assert "SHORTVOL-COMPACT-PUBLISH-20261111" in shortvol


def test_files_compact_on_disk():
    for slug in FILES:
        raw = open(os.path.join(HERE, slug, "data.json"), "rb").read()
        assert len(raw) < CEILING, (slug, len(raw))
        data = json.loads(raw)
        compact = json.dumps(data, separators=(",", ":"),
                             sort_keys=True).encode() + b"\n"
        assert raw == compact, f"{slug}: file on disk is not the compact form"


if __name__ == "__main__":
    test_helper_preserves_style()
    test_enrichers_write_style_preserving()
    test_producers_write_compact()
    test_files_compact_on_disk()
    print("test_compact_publish_preserved_20261111: all passed")
