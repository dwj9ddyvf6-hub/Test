"""Build the best-setups document for a session (2026-10-15).

Wires the desk's own doors into the pure curator
(core/setups_curator.py): daily bars via tools.run_live's SIP door,
^VIX via the desk's one sanctioned Yahoo use. Read-only against the
desk state — it never writes into the live tree; the caller chooses
the output path.

Usage:
  python3 tools/build_setups.py --state-dir state --out setups.json
  python3 tools/build_setups.py --state-dir /path/to/state-copy \
      --session 2026-10-15 --out setups.json
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import setups_curator  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default="state",
                    help="desk state/ directory (ledger.jsonl + live/)")
    ap.add_argument("--session", default=None,
                    help="session date YYYY-MM-DD (default: latest in ledger)")
    ap.add_argument("--out", default=None,
                    help="write the setups JSON here (default: stdout)")
    args = ap.parse_args(argv)

    state_dir = pathlib.Path(args.state_dir)
    # Candidate symbols first (cheap ledger scan), so the bars fetch
    # covers exactly the candidates + the two index ETFs.
    probe = setups_curator.load_state(state_dir)
    rows = probe["ledger"]
    session = args.session
    if session is None:
        ss = [r.get("session") for r in rows if r.get("session")]
        session = max(ss) if ss else None
    syms = {"SPY", "QQQ"} | setups_curator.candidate_symbols(probe, session)

    from tools.run_live import alpaca_daily_bars, yahoo_vix
    bars = alpaca_daily_bars(sorted(syms), session=session)
    # The desk door returns full history; the curator needs the recent
    # window only — trim to the last 120 sessions per symbol.
    bars = {s: (b or [])[-120:] for s, b in bars.items()}

    vix = None
    got = yahoo_vix()
    if got:
        close, prev, as_of, _src = got
        vix = {"close": close,
               "change_pct": ((close / prev - 1.0) * 100.0) if prev else None,
               "as_of": as_of}

    doc = setups_curator.curate(state_dir, session=session,
                                daily_bars=bars, vix=vix, state=probe)
    text = json.dumps(doc, indent=1)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
        print(f"wrote {args.out}: {len(doc['setups'])} setups, "
              f"regime={doc['market_context']['regime']}, "
              f"session={doc['as_of']}")
        for s in doc["setups"][:10]:
            print(f"  #{s['rank']} {s['symbol']:<6} {s['score']:>3} "
                  f"{s['tier']:<8} {s['status']:<7} "
                  f"{', '.join(s['sources'])}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
