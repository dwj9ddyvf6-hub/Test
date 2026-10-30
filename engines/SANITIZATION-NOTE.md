# Sanitization note

Two engine files in this repo are sanitized copies, vendored under the
owner's standing ruling of 2026-10-29 to package everything, sanitized
where the privacy gate requires, with every sanitization disclosed:

- `engines/desk3/contract.py` (desk source: `desk3/contract.py`):
  1 redaction. Class of token redacted: a personal first-name token
  (privacy-gate pattern class `first_name`), located in a class
  docstring. It was replaced with a neutral placeholder.
- `engines/laz_sleeves/_common.py` (desk source: `laz_sleeves/_common.py`):
  1 redaction. Class of token redacted: a family codename token
  (privacy-gate pattern class `codename`), located in the module
  docstring. It was replaced with a neutral placeholder.

For both files the byte-identical original was refused by the privacy
gate before any write, and only the sanitized copy was saved.

Executable code is identical to the originals: no executable line was
changed. This was proven by stripping comments and docstrings from both
versions and comparing the resulting executable token streams and ASTs,
which match exactly. Only docstring text carrying the blocked token
differs.

The verbatim originals live on the desk, in the private desk source tree
at the desk paths named above.
