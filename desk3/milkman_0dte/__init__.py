"""Milkman 0DTE SPX install package (MILKMAN-0DTE-INSTALL-20261027).

milkman_0dte.py is the vendored Femto-lean sleeve, byte-exact against
the program fetch manifest (see PROVENANCE.md). It is a provenance
artifact: nothing in the live desk imports it (its framework —
Femto-lean's desk.contract / desk.data — has no muse-desk-v3
counterpart). The live, v3-native expression of the same authored
rules is sleeves/milkman_0dte.py, wired through
adapters/milkman_0dte.py + adapters3/milkman_0dte.py.

MILKMAN-0DTE-PORT-20261116: intraday.py + mlib.py are the vendored
byte-exact Milkman intraday study and its library (provenance
artifacts, same standing as the vendored sleeve), and
intraday_study.py is their live v3-native port — the study the
vendored sleeve imports as desk/sleeves/milkman/intraday.py,
recovered and ported to close PROVENANCE gap 1 (see PROVENANCE.md).

spx_probe.py is the one adapted file: the source probe re-expressed
against muse-desk-v3's own Alpaca producer functions and credential
route, keeping the source's record schema, constants, and verdict
rules. It is the evidence path for ever un-parking the sleeve.
"""
