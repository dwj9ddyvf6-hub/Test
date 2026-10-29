"""The desk's record as the lab reads it: state/ledger.jsonl read backwards from its last whole line to a window's
start, as desk/terminal/distill.py ledger_signals does (terminal branch): the cost follows the window, not the ledger's
length.
A line is parsed only when a byte test says it is one of the kinds below (and a signals line only when it carries an
enter, exit or target intent); everything else is skipped unparsed. A record's time is its pass's `at`.

  intents    [(at, sleeve, intent)]   enter / exit / target intents on a plain US stock or ETF ticker
  children   {child id: child record + at}
  fills      [fill record + at], each with its ledger seq (what a fill_correction names)
  corrected  {fill seq: fill_correction record}   the NBBO re-pricing of a fill (a migration, recorded later)
  exits      {child id: rule_exit record + at}    the engine's own exits (stop / target / time rules)
  ended      {child id: child_expired | child_void}   a child that ended unfilled (or partly filled)
  passes     [at] of every pass in the window
  opt_children / opt_fills   the same for single option contracts (inst OPT:), the option arms' record (exp1)
  lz_obs     [(at, lane, intent)]   the Lazarus lanes' fire outcome observations (fix1's FEED-01: kind signal, key
             lzo:<fire key>:<outcome>:<epoch>), FEED-05/06's record (desk/lab/lazarus.py)"""
import json
import os
import re
from datetime import datetime

PLAIN = re.compile(r"^[A-Z]{1,5}([.-][A-Z]{1,2})?$")      # a US stock or ETF ticker; never an option or a pair
_KINDS = {k: b'"kind": "%s"' % k.encode()
          for k in ("pass_start", "signals", "child", "fill", "fill_correction", "rule_exit", "child_expired",
                    "child_void")}
_OTHER = tuple(v for k, v in _KINDS.items() if k not in ("pass_start", "signals"))
_TRADES = (b'"kind": "enter"', b'"kind": "exit"', b'"kind": "target"')
_LZO = b'"key": "lzo:'                                   # a Lazarus fire outcome observation (FEED-01)
INTENT_KINDS = ("enter", "exit", "target")


def _ts(x):
    try:
        return datetime.fromisoformat(str(x)).timestamp()
    except (TypeError, ValueError):
        return None


def _loads(b):
    try:
        return json.loads(b)
    except ValueError:
        return None


def first_at(path):
    """the time of the ledger's first pass (its first line), or None"""
    try:
        with open(path, "rb") as f:
            line = f.readline()
    except OSError:
        return None
    r = _loads(line) if line.endswith(b"\n") else None
    return _ts((r or {}).get("at")) if r and r.get("kind") == "pass_start" else None


class Record:
    def __init__(self):
        self.intents, self.children, self.fills, self.corrected, self.exits, self.passes = [], {}, [], {}, {}, []
        self.ended = {}
        self.opt_children, self.opt_fills = {}, []
        self.lz_obs = []
        self.truncated = False                           # the read stopped at max_bytes before the window's start

    def add(self, at, r):
        k = r.get("kind")
        if k == "signals":
            for it in r.get("intents") or ():
                if it.get("kind") in INTENT_KINDS and it.get("asset") == "equity" \
                        and PLAIN.match(str(it.get("symbol") or "")) and it.get("side") in ("long", "short"):
                    self.intents.append((at, r.get("sleeve"), it))
                elif it.get("kind") == "signal" and str(it.get("key") or "").startswith("lzo:"):
                    self.lz_obs.append((at, r.get("sleeve"), it))
        elif k == "child":
            if str(r.get("inst") or "").startswith("EQ:"):
                self.children[r["child"]] = dict(r, at=at)
            elif str(r.get("inst") or "").startswith("OPT:"):
                self.opt_children[r["child"]] = dict(r, at=at)
        elif k == "fill":
            if str(r.get("inst") or "").startswith("EQ:"):
                self.fills.append(dict(r, at=at))
            elif str(r.get("inst") or "").startswith("OPT:"):
                self.opt_fills.append(dict(r, at=at))
        elif k == "fill_correction":
            self.corrected[r.get("fill_seq")] = r
        elif k == "rule_exit":
            self.exits[r.get("child")] = dict(r, at=at)
        elif k in ("child_expired", "child_void"):
            self.ended[r.get("child")] = k


def read(path, t_cut, chunk=1 << 22, max_bytes=2 << 30):
    """the Record of the passes that started at or after t_cut"""
    rec = Record()
    if not os.path.exists(path):
        return rec
    kept, stop = [], False
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        look = min(size, 1 << 20)
        f.seek(size - look)
        cut = f.read(look).rfind(b"\n")
        if cut < 0:
            return rec
        end = pos = size - look + cut + 1                # bytes after the last newline are not a record yet
        carry = b""
        while pos > 0 and not stop:
            if end - pos >= max_bytes:
                rec.truncated = True
                break
            step = min(chunk, pos)
            pos -= step
            f.seek(pos)
            lines = (f.read(step) + carry).split(b"\n")
            carry = lines.pop(0) if pos > 0 else b""
            for ln in reversed(lines):
                if _KINDS["pass_start"] in ln:
                    at = _ts((_loads(ln) or {}).get("at"))
                    if at is not None and at < t_cut:
                        stop = True
                        break
                    kept.append((True, at))
                elif _KINDS["signals"] in ln:
                    if any(t in ln for t in _TRADES) or _LZO in ln:
                        r = _loads(ln)
                        if r:
                            kept.append((False, r))
                elif any(t in ln for t in _OTHER):
                    r = _loads(ln)
                    if r:
                        kept.append((False, r))
    at = None
    for is_pass, v in reversed(kept):
        if is_pass:
            at = v
            if v is not None:
                rec.passes.append(v)
        elif at is not None:
            rec.add(at, v)
    return rec
