"""Shared Saty reference implementation (D9 dedup cure).

Byte-identical copies previously lived at core/saty_gpt_v02/reference.py
and core/saty_gpt_v03/reference.py (551 LOC each, SHA256 1d0669258ca3).
The canonical implementation now lives ONCE in core/saty_reference.py;
this module re-exports it so existing import paths are preserved.
"""
from core import saty_reference as _r
import sys as _sys
_sys.modules[__name__].__dict__.update({k: v for k, v in vars(_r).items() if not k.startswith("__")})
