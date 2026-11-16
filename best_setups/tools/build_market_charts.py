"""Render the market panel's index charts (SPY + QQQ) for one
session (2026-10-15, visual pass).

The terminal's market panel leads with the charts the desk's
market read is built from — daily candles with the 20/50/200-day
averages and the recent swing high/low — rendered desk-side like
the setup charts (core/setup_brief.py: render_index_chart), in
the same dark palette. Bars come through the desk's own door
(tools/run_live.py: alpaca_daily_bars). Read-only against the
desk state; every output path is the caller's choice.

Publication pattern (see MERGE_PLAN.md section 9): charts are
files named <SYMBOL>-<session>.png in the same charts directory
as the setup charts, published in the same pass. The publisher
merges this tool's `market_charts` object into the feed's
market_context as `charts`:

    market_context.charts = {"spy": "setup-charts/SPY-<session>.png",
                             "qqq": "setup-charts/QQQ-<session>.png"}

If a chart cannot be rendered (bars too short), its key is simply
absent and the panel shows the index's figures without a chart —
nothing is fabricated.

Usage:
  python3 tools/build_market_charts.py --session 2026-10-15 \
      --charts-dir /path/to/setup-charts --out state/live/market_charts.json
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import setup_brief  # noqa: E402

INDEXES = (("SPY", "S&P 500 (SPY)"), ("QQQ", "Nasdaq 100 (QQQ)"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", required=True,
                    help="trading session, YYYY-MM-DD (ET)")
    ap.add_argument("--charts-dir", required=True,
                    help="directory to write chart PNGs into")
    ap.add_argument("--chart-prefix", default="setup-charts",
                    help="path prefix stored in the output "
                         "(relative to the terminal page)")
    ap.add_argument("--out", default=None,
                    help="write the market_charts JSON here "
                         "(default: stdout)")
    args = ap.parse_args(argv)

    from tools.run_live import alpaca_daily_bars
    syms = [s for s, _ in INDEXES]
    daily = alpaca_daily_bars(syms, session=args.session)
    daily = {s: (b or [])[-320:] for s, b in daily.items()}

    charts_dir = pathlib.Path(args.charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    charts = {}
    chart_closes = {}
    for sym, label in INDEXES:
        name = f"{sym}-{args.session}.png"
        path, panels, _drawn = setup_brief.render_index_chart(
            sym, label, daily.get(sym), charts_dir / name,
            as_of=args.session)
        if path:
            charts[sym.lower()] = f"{args.chart_prefix}/{name}"
            # V-22 (FIXALL 2026-10-19): stamp the close of the
            # very bars this chart was rendered from, so the
            # publisher can withhold a chart that contradicts
            # the feed's market panel instead of shipping both.
            _bars = daily.get(sym) or []
            if _bars:
                _last = _bars[-1]
                _c = (_last.get("c") if isinstance(_last, dict)
                      else getattr(_last, "c", None))
                if _c is not None:
                    chart_closes[sym.lower()] = float(_c)
        print(f"  index chart {sym:<4} -> "
              f"{charts.get(sym.lower()) or 'NONE (bars too short)'}")

    doc = {"as_of": args.session, "market_charts": charts,
           "chart_closes": chart_closes}
    text = json.dumps(doc, indent=1)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
        print(f"wrote {args.out}: {len(charts)} index charts, "
              f"session={args.session}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
