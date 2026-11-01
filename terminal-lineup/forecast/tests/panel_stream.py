"""Streaming reader for the DEEP panel JSON (cure D-R2-02,
2026-10-31).

The panel (~/workspace/morgue/data_cache/deep_bars.json) is a
1.1GB single-line JSON object mapping symbol -> rows. Loading it
whole with json.load builds ~237M Python objects and was
OOM-killed (SIGKILL) under the canonical suite runner even in
its own subprocess on this balloon-limited box (~2.8GB
effective), so the two deep-panel blockers could never pass as
written. The program discipline is to stream large files and
never load the panel whole; this reader does exactly that: it
parses one symbol's row list at a time with JSONDecoder,
refilling a bounded text buffer, so peak memory is one chunk
plus one symbol. It yields (symbol, rows) pairs in file order;
callers keep only the symbols they assert on and count the rest.
"""
import json

_CHUNK = 1 << 20
_DECODER = json.JSONDecoder()


def iter_panel(path):
    buf = ""
    pos = 0
    eof = False
    with open(path, encoding="utf-8") as fh:

        def refill():
            nonlocal buf, pos, eof
            if pos:
                buf = buf[pos:]
                pos = 0
            chunk = fh.read(_CHUNK)
            if chunk:
                buf += chunk
            else:
                eof = True

        def parse_at():
            """raw_decode at pos, refilling until the value is
            complete; a truncated composite always raises, so a
            retry with more buffer is safe."""
            nonlocal pos
            while True:
                try:
                    obj, end = _DECODER.raw_decode(buf, pos)
                    pos = end
                    return obj
                except json.JSONDecodeError:
                    if eof:
                        raise
                    refill()

        def skip_ws():
            nonlocal pos
            while True:
                while pos < len(buf) and buf[pos] in " \t\r\n":
                    pos += 1
                if pos < len(buf) or eof:
                    return
                refill()

        refill()
        skip_ws()
        assert buf[pos] == "{", "panel is not a JSON object"
        pos += 1
        while True:
            skip_ws()
            if pos < len(buf) and buf[pos] == "}":
                return
            if pos < len(buf) and buf[pos] == ",":
                pos += 1
                skip_ws()
            symbol = parse_at()
            skip_ws()
            assert buf[pos] == ":", "panel entry missing colon"
            pos += 1
            skip_ws()
            rows = parse_at()
            yield symbol, rows
