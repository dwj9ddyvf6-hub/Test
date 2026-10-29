"""The card's face in plain words: one rule set every edition passes through, so a later calibration cannot bring
jargon back onto the board (owner, 2026-10-21: simple, explicit, low-effort language; no internal terms).

plain(text)      -> the face sentence with technical clauses rewritten and chart-reading terms removed
clean(text)      -> the face sentence that fails closed: plain(), then a parenthetical that still holds a banned term
                    taken out, then a "; clause" that still holds one dropped; None when nothing plain is left (the
                    caller then builds the sentence from the call's own fields: compose.plain_gist)
violations(text) -> the banned terms still present (empty = clean); tests and compose.face_guard enforce it"""
import re

# technical clause -> what it means for someone deciding to buy (first match wins; order matters)
REWRITES = [
    # the buy zone's own words (a plan's why_zone): a wave zone or a retracement level, said as what it is
    (r"the 0\.\d+[–-]0\.\d+ retracement of (?:wave \d(?: \([^()]*\))?|the [^;()]+? (?:advance|rise|drop|decline))",
     "the usual pullback zone"),
    (r"the \d+(?:\.\d+)?% retracement of the [^;()]+? rise", "a common pullback level"),
    (r"the \d+(?:\.\d+)?% retracement of the [^;()]+? drop", "a common rebound level"),
    (r"it is (?:in|turning up from) its wave-[24] (?:buy )?zone(?: on the weekly chart)?", "it has pulled back to a level where buyers usually return"),
    (r"it is in a deep wave [24]", "it has pulled back further than usual"),
    (r"there is a breakaway gap up", "it jumped higher on heavy buying"),
    (r"there is a breakaway gap down", "it dropped sharply on heavy selling"),
    (r"it gapped up with the trend and has not looked back", "it jumped higher and has held the gain"),
    (r"it gapped (up|down)[^;.]*", r"it opened sharply \1"),
    (r"it has confirmed an? [^;.]*bottom", "it has formed a base and turned up"),
    (r"it has confirmed an? [^;.]*", "a buy pattern has completed"),
    (r"it is in phase \w+ of a Wyckoff \w+", "buyers are quietly stepping in"),
    (r"there is a bull flag", "it is resting after a strong run"),
    (r"it is oversold inside an uptrend", "it has dipped inside an uptrend"),
    (r"it has closed over its last swing high", "it has broken above its recent high"),
    (r"it has closed under its last swing low", "it has broken below its recent low"),
    (r"it is in a smooth, steady uptrend", "it is rising steadily"),
    (r"it is in an uptrend on every average", "it is in a strong uptrend"),
]
# words that never belong on a card's face (they stay in the expanded read and the glossary)
BANNED = ["wave-", "wave ", "Wyckoff", "Fibonacci", "retracement", "ATR", "divergence", "breakaway", "Nison",
          "swing high", "swing low", "weekly chart", "the desk", "fear day", "phase "]
_TAIL = re.compile(r"\s+on the weekly chart")


def plain(text):
    if not text:
        return text
    s = _TAIL.sub("", text)
    for pat, rep in REWRITES:
        s = re.sub(pat, rep, s, flags=re.I)
    return s


_PAREN = re.compile(r"\s*\((?:[^()]|\([^()]*\))*\)")     # a parenthetical, with one level of nesting inside it


def clean(text):
    """the face sentence in plain words, or None when no plain form is left (see the module docstring)"""
    s = plain(text or "")
    if not violations(s):
        return s
    s = _PAREN.sub(lambda m: "" if violations(m.group(0)) else m.group(0), s)
    if not violations(s):
        return s
    head, *rest = s.split("; ")
    s = "; ".join([head] + [r for r in rest if not violations(r)])
    if violations(s):
        return None
    return s if s.endswith(".") else s.rstrip(" ;,") + "."


def violations(text):
    low = (text or "").lower()
    return [b for b in BANNED if b.lower() in low]
