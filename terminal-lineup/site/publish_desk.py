#!/usr/bin/env python3
"""Publish the desk terminal surface inside the tools site root.

The desk page lives on the desk side (muse-desk-v3/terminal/: its
index.html plus the terminal_feed.json it fetches). The tools site is
served from this folder, so the shared navigation's Desk tab (last,
by the 2026-10-31 ruling) can only link truthfully to a copy served
from the same root. This producer makes that copy: both files are
copied byte for byte into site/desk/, and the copy is verified by
hash before this prints success. The desk side stays the source;
this folder is a publish copy, refreshed by refresh_hub.py.

Desk subject charts (cure 2026-10-31): the desk page was the one hub
page with no data.json and no chart. This producer now also builds
site/desk/data.json from the copied snapshot, carrying the subject
quantities the snapshot itself holds (the account readings, the open
positions aggregated from the per-strategy rows, and the capital
epoch the snapshot's evidence packet declares) plus the subject
charts record_surface.build_subject_chart builds from them. The
published index.html keeps the desk page's own content byte for byte
and gains only the shared chart wiring every other page carries
(shared.css, visual.css, shared.js, which loads the chart layer).
Both additions are rebuilt here on every publish, so they survive
republication; nothing is hand-edited into site/desk/.

Usage: python3 publish_desk.py
Exit 0 when both files are in place and hash-verified, the wiring
is in the published page, and data.json is written.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "muse-desk-v3" / "terminal"
FILES = ("index.html", "terminal_feed.json")

# Manifest sync (cure D-R2-01 root cause, 2026-11-01): this
# producer writes served files (desk/index.html, desk/data.json)
# but was the one served-tree writer that never imported
# terminal_common, so the shared manifest-sync hook (MANIFEST-
# SHARED-WRITE-20261031) never registered when it ran standalone
# (as test_charts_ia's producer proof runs it). A desk publish
# after the desk feed had advanced left asset-manifest.json
# stale, and every later manifest verifier (shipyard, smoke
# check) failed on desk/data.json until an unrelated terminal_
# common process happened to exit. Importing the shared module
# here puts this writer on the same write path as every other
# refresh script: at process exit the manifest is rebuilt if
# any served file changed.
try:
    import terminal_common as _tc  # noqa: F401 - registers sync
except ImportError:  # publish stays runnable standalone
    _tc = None

# The shared chart wiring, exactly as the authored pages carry it.
# Added to the published copy only; the desk source is untouched.
WIRING = ('<link rel="stylesheet" href="../shared.css">\n'
          '<link rel="stylesheet" href="../visual.css">\n'
          '<script src="../shared.js" defer></script>\n')


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) \
        else None


def aggregate_positions(feed):
    """Open positions from the snapshot, aggregated by symbol.

    The snapshot carries positions per strategy as {symbol, qty}
    rows (the desk page itself renders those). Quantities for the
    same symbol across strategies are summed and the holding
    strategies named. If no strategy row exists, account_positions
    rows are used when they carry the same two fields. No other
    position field (no market value, no unrealised profit or loss)
    exists in the snapshot, so none is carried or invented.
    """
    agg = {}
    for strat in feed.get("strategies") or []:
        for pos in strat.get("open_positions") or []:
            sym, qty = pos.get("symbol"), _num(pos.get("qty"))
            if not sym or qty is None:
                continue
            row = agg.setdefault(sym, {"symbol": sym, "qty": 0,
                                       "strategies": []})
            row["qty"] += qty
            name = strat.get("name")
            if name and name not in row["strategies"]:
                row["strategies"].append(name)
    if not agg:
        for pos in feed.get("account_positions") or []:
            sym, qty = pos.get("symbol"), _num(pos.get("qty"))
            if not sym or qty is None:
                continue
            row = agg.setdefault(sym, {"symbol": sym, "qty": 0,
                                       "strategies": []})
            row["qty"] += qty
    return sorted(agg.values(), key=lambda r: -abs(r["qty"]))


def build_data(feed):
    """The desk page's data.json, from its own snapshot only."""
    account = feed.get("account") or {}
    packet = feed.get("evidence_packet") or {}
    period = packet.get("period") or {}
    generated = feed.get("generated_at") or ""
    data = {
        "tool": "desk",
        "session": generated[:10],
        "published_at_utc": generated,
        "source": "desk snapshot terminal_feed.json, copied read-only "
                  "by publish_desk.py from muse-desk-v3/terminal/",
        "account": {k: account.get(k) for k in (
            "equity", "cash", "buying_power", "portfolio_value",
            "last_equity", "status")},
        "positions": aggregate_positions(feed),
        "positions_source": "strategies[].open_positions "
                            "(symbol, qty), aggregated by symbol",
        "epoch": {"starting_capital": packet.get("starting_capital"),
                  "start": period.get("start"),
                  "end": period.get("end")},
    }
    # Provenance stamp (HEALTH-R1-D17-20261031): every other
    # data.json on the site carries the provenance shape; the
    # desk copy built here carried none, so the two highest
    # trust surfaces were the two without provenance. The desk
    # figures are the desk's own filed snapshot record, stamped
    # in the same shape terminal_common uses.
    data["feed"] = "filed_records"
    data["price_basis"] = "session_record"
    data["execution_pricing"] = False
    data["provenance"] = {
        "feed": "filed_records",
        "price_basis": "session_record",
        "execution_pricing": False,
        "stamped_by": "publish_desk.py",
        "source_file": "muse-desk-v3/terminal/terminal_feed.json",
    }
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import record_surface
    data["subject_chart"] = record_surface.build_subject_chart(
        "desk", data)
    return data


PANEL_PATH = HERE.parents[1] / "morgue" / "data_cache" / "board_bt_bars.json"
JOURNAL_PATHS = (HERE.parents[1] / "muse-desk-v3" / "state"
                 / "dispatcher.jsonl.1",
                 HERE.parents[1] / "muse-desk-v3" / "state"
                 / "dispatcher.jsonl")


def closed_trades_from_journal(paths=JOURNAL_PATHS):
    """Closed trades paired from the desk dispatcher's own fill
    journal (GAP-7, 2026-11-02). Both journal generations are read
    in order (the rotated .1 first, then the live file) and fills
    are paired first in, first out per sleeve and symbol. A closed
    trade is returned only when its opening fills are also in the
    journal record; closing fills whose openings are not on record
    (positions opened before the journal record or carried in from
    the broker book) are counted in the returned meta, never given
    an invented entry price. Trades are aggregated per closing
    fill, with the volume-weighted average entry price."""
    from collections import defaultdict, deque
    fills = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") == "fill":
                fills.append(rec)
    fills.sort(key=lambda r: r["ts"])
    lots = defaultdict(deque)
    closed = {}
    unpaired = 0
    for idx, f in enumerate(fills):
        key = (f.get("sleeve"), f["symbol"])
        qty, px = float(f["qty"]), float(f["price"])
        direction = 1 if f["side"] == "buy" else -1
        intent = f.get("position_intent") or ""
        is_close = intent.endswith("_to_close") or (
            not intent and lots[key] and lots[key][0][0] != direction)
        if not is_close:
            lots[key].append([direction, qty, px, str(f["ts"])[:10]])
            continue
        remaining, paired = qty, 0.0
        while remaining > 1e-9 and lots[key] \
                and lots[key][0][0] != direction:
            lot = lots[key][0]
            take = min(remaining, lot[1])
            pnl = (px - lot[2]) * take if lot[0] == 1 \
                else (lot[2] - px) * take
            agg = closed.setdefault(idx, {
                "sleeve": key[0], "symbol": key[1], "qty": 0.0,
                "entry_cost": 0.0, "pnl": 0.0, "exit_px": px,
                "exit_date": str(f["ts"])[:10],
                "side": "long" if lot[0] == 1 else "short",
                "entry_first": lot[3], "entry_last": lot[3]})
            agg["qty"] += take
            agg["entry_cost"] += lot[2] * take
            agg["pnl"] += pnl
            agg["entry_last"] = lot[3]
            lot[1] -= take
            remaining -= take
            paired += take
            if lot[1] <= 1e-9:
                lots[key].popleft()
        if paired < qty - 1e-9:
            unpaired += 1
    trades = [{"sleeve": a["sleeve"], "symbol": a["symbol"],
               "side": a["side"], "qty": a["qty"],
               "entry_avg": round(a["entry_cost"] / a["qty"], 4),
               "exit_px": a["exit_px"], "exit_date": a["exit_date"],
               "entry_first": a["entry_first"],
               "entry_last": a["entry_last"],
               "pnl": round(a["pnl"], 2)}
              for a in closed.values()]
    trades.sort(key=lambda t: t["exit_date"])
    meta = {"fills_scanned": len(fills),
            "unpaired_close_fills": unpaired,
            "source": "desk dispatcher journal fill events "
                      "(state/dispatcher.jsonl.1 then "
                      "state/dispatcher.jsonl), paired first in "
                      "first out per sleeve and symbol"}
    return trades, meta
ATTRACTIONS_BEGIN = "<!-- AMAZING-ATTRACTIONS-BEGIN -->"
ATTRACTIONS_END = "<!-- AMAZING-ATTRACTIONS-END -->"


def build_attractions(feed):
    """AMAZING Build (2026-11-02): the GrokBot-standard desk attractions,
    from our real data only. Benchmark closes come from the board price
    panel on this box (the same panel the session-quality builder
    reads); the desk line carries only the equity readings the snapshot
    itself records (epoch start and the latest cycle), never an
    interpolated path. Positions carry qty and average price from
    account_positions, so heatmap tiles are sized by cost paid, not by
    an invented current value. Strategy scorecards are operational
    (status counts, money assigned, orders placed) because the feed
    carries no per-strategy return series and none is invented."""
    import html as _html
    account = feed.get("account") or {}
    packet = feed.get("evidence_packet") or {}
    period = packet.get("period") or {}
    start_date = str(period.get("start") or "")[:10]
    equity = _num(account.get("equity"))
    start_cap = _num(packet.get("starting_capital"))
    bench = {}
    small_caps = {}
    sessions = []
    try:
        panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
        for sym in ("SPY", "QQQ"):
            rows = [r for r in panel.get(sym) or []
                    if start_date and str(r[0]) >= start_date]
            if rows:
                base = rows[0][4]
                bench[sym] = [{"date": str(r[0]),
                               "pct": round((r[4] / base - 1) * 100, 3)}
                              for r in rows]
                sessions = [r["date"] for r in bench[sym]]
        # GAP-7 small caps: IWM rides the same panel and the same
        # rule as SPY and QQQ, so the desk can be read against small
        # caps over the identical window with no new data source.
        rows = [r for r in panel.get("IWM") or []
                if start_date and str(r[0]) >= start_date]
        if rows:
            base = rows[0][4]
            small_caps["IWM"] = [{"date": str(r[0]),
                                  "pct": round((r[4] / base - 1) * 100, 3)}
                                 for r in rows]
    except Exception:
        bench = {}
        small_caps = {}
    desk_pts = []
    if start_cap and equity and start_date:
        desk_pts = [{"date": start_date, "pct": 0.0},
                    {"date": str(feed.get("generated_at") or "")[:10],
                     "pct": round((equity / start_cap - 1) * 100, 3)}]
    positions = []
    total_cost = 0.0
    for pos in feed.get("account_positions") or []:
        qty, avg = _num(pos.get("qty")), _num(pos.get("avg_price"))
        if pos.get("symbol") and qty is not None and avg is not None:
            cost = abs(qty * avg)
            total_cost += cost
            positions.append({"symbol": pos["symbol"], "qty": qty,
                              "avg_price": avg, "cost": round(cost, 2)})
    for p in positions:
        p["share_pct"] = round(p["cost"] / total_cost * 100, 2) if total_cost else 0.0
    fams = {}
    for s in feed.get("strategies") or []:
        fam = s.get("family") or "other"
        row = fams.setdefault(fam, {"family": fam, "total": 0, "ready": 0,
                                    "waiting_for_data": 0, "paused": 0,
                                    "needs_attention": 0,
                                    "money_assigned": 0.0, "orders_placed": 0})
        row["total"] += 1
        st = s.get("status")
        if st == "Ready":
            row["ready"] += 1
        elif st == "Waiting for data":
            row["waiting_for_data"] += 1
        elif st == "Paused":
            row["paused"] += 1
        elif st == "Needs attention":
            row["needs_attention"] += 1
        row["money_assigned"] += _num(s.get("money_assigned")) or 0.0
        row["orders_placed"] += int(s.get("orders_placed") or 0)
    families = sorted(fams.values(), key=lambda r: (-r["total"], r["family"]))
    # GAP-7 closed trades: paired from the desk's own fill journal.
    try:
        trades, trades_meta = closed_trades_from_journal()
    except Exception:
        trades, trades_meta = [], {"fills_scanned": 0,
                                   "unpaired_close_fills": 0,
                                   "source": "journal unreadable"}
    data = {"benchmarks_pct": bench, "sessions": sessions,
            "small_caps_pct": small_caps,
            "closed_trades": trades, "closed_trades_meta": trades_meta,
            "desk_pct_points": desk_pts, "positions_cost": positions,
            "families": families,
            "window": {"start": start_date,
                       "end": str(feed.get("generated_at") or "")[:10]},
            "sources": {"benchmarks": "board price panel daily closes "
                        "(morgue/data_cache/board_bt_bars.json)",
                        "small_caps": "board price panel daily closes, "
                        "IWM, same panel and window as SPY and QQQ",
                        "closed_trades": trades_meta.get("source"),
                        "desk": "terminal_feed.json account equity vs "
                        "evidence_packet starting capital",
                        "positions": "terminal_feed.json account_positions "
                        "qty x avg_price (cost paid)",
                        "families": "terminal_feed.json strategies and "
                        "sleeve group counts"}}
    # --- lead chart SVG (percent, same window) ---
    def _chart():
        series = [(k, v, c) for k, v, c in
                  (("SPY", bench.get("SPY") or [], "#b06000"),
                   ("QQQ", bench.get("QQQ") or [], "#7a4fa3"))]
        if desk_pts:
            series.append(("Desk", desk_pts, "#0b3b46"))
        pts = [p["pct"] for _, v, _ in series for p in v]
        if not pts:
            return ""
        lo, hi = min(pts + [0.0]), max(pts + [0.0])
        span = (hi - lo) or 1.0
        lo -= span * 0.1; hi += span * 0.1; span = hi - lo
        W, H, L, R, T, B = 720, 240, 8, 8, 12, 22
        all_dates = sessions or [desk_pts[0]["date"], desk_pts[-1]["date"]]
        di = {d: i for i, d in enumerate(all_dates)}
        n = max(len(all_dates) - 1, 1)
        def X(d):
            i = di.get(d, n if d >= all_dates[-1] else 0)
            return L + (W - L - R) * i / n
        def Y(v):
            return T + (H - T - B) * (hi - v) / span
        out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
               f'aria-label="Desk versus SPY and QQQ, percent since '
               f'{_html.escape(start_date)}">']
        out.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W-R}" y2="{Y(0):.1f}" stroke="#cfe0da"/>')
        for name, v, c in series:
            if len(v) < 2:
                continue
            poly = " ".join(f"{X(p['date']):.1f},{Y(p['pct']):.1f}" for p in v)
            out.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.5" points="{poly}"/>')
            last = v[-1]
            out.append(f'<circle cx="{X(last["date"]):.1f}" cy="{Y(last["pct"]):.1f}" r="4" fill="{c}"/>')
            out.append(f'<text x="{max(X(last["date"])-118, L):.1f}" y="{Y(last["pct"])-8:.1f}" font-size="14" font-weight="700" fill="{c}">{name} {last["pct"]:+.2f}%</text>')
        out.append(f'<text x="{L}" y="{H-6}" font-size="12" fill="#5b7180">{_html.escape(all_dates[0])}</text>')
        out.append(f'<text x="{W-R-70}" y="{H-6}" font-size="12" fill="#5b7180">{_html.escape(all_dates[-1])}</text>')
        out.append("</svg>")
        return "".join(out)
    # --- GAP-7: desk vs small caps chart (IWM line + desk points) ---
    def _chart_small():
        iwm = small_caps.get("IWM") or []
        if not iwm:
            return ""
        dates = [p["date"] for p in iwm]
        series = [("IWM", iwm, "#1c6e4e")]
        if desk_pts:
            series.append(("Desk", desk_pts, "#0b3b46"))
        pts = [p["pct"] for _, v, _ in series for p in v]
        lo, hi = min(pts + [0.0]), max(pts + [0.0])
        span = (hi - lo) or 1.0
        lo -= span * 0.1; hi += span * 0.1; span = hi - lo
        W, H, L, R, T, B = 720, 240, 8, 8, 12, 22
        di = {d: i for i, d in enumerate(dates)}
        n = max(len(dates) - 1, 1)
        def X(d):
            i = di.get(d, n if d >= dates[-1] else 0)
            return L + (W - L - R) * i / n
        def Y(v):
            return T + (H - T - B) * (hi - v) / span
        out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
               f'aria-label="Desk versus small caps (IWM), percent since '
               f'{_html.escape(start_date)}">']
        out.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W-R}" y2="{Y(0):.1f}" stroke="#cfe0da"/>')
        for name, v, c in series:
            if len(v) < 2:
                continue
            poly = " ".join(f"{X(p['date']):.1f},{Y(p['pct']):.1f}" for p in v)
            out.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.5" points="{poly}"/>')
            last = v[-1]
            out.append(f'<circle cx="{X(last["date"]):.1f}" cy="{Y(last["pct"]):.1f}" r="4" fill="{c}"/>')
            out.append(f'<text x="{max(X(last["date"])-118, L):.1f}" y="{Y(last["pct"])-8:.1f}" font-size="14" font-weight="700" fill="{c}">{name} {last["pct"]:+.2f}%</text>')
        out.append(f'<text x="{L}" y="{H-6}" font-size="12" fill="#5b7180">{_html.escape(dates[0])}</text>')
        out.append(f'<text x="{W-R-70}" y="{H-6}" font-size="12" fill="#5b7180">{_html.escape(dates[-1])}</text>')
        out.append("</svg>")
        return "".join(out)
    small_card = ""
    if small_caps.get("IWM"):
        small_card = (
            '<section class="card"><div class="kicker">Small caps</div>'
            '<h2>Desk vs small caps</h2>'
            '<p class="muted">The same desk line read against small '
            'company stocks, tracked by the IWM fund, over the same '
            f'window from {_html.escape(start_date)}. The IWM line uses '
            'daily closes from the same price panel as SPY and QQQ. '
            'The desk line is the same two recorded equity readings '
            'as the chart above.</p>' + _chart_small() + '</section>\n')
    # --- GAP-7: closed trades log ----------------------------------
    trade_rows = "".join(
        f'<tr><td>{_html.escape(str(t["exit_date"]))}</td>'
        f'<td>{_html.escape(str(t["symbol"]))}</td>'
        f'<td>{_html.escape(str(t["sleeve"]))}</td>'
        f'<td>{_html.escape(str(t["side"]))}</td><td>{t["qty"]:g}</td>'
        f'<td>${t["entry_avg"]:,.2f}</td><td>${t["exit_px"]:,.2f}</td>'
        f'<td>{"+" if t["pnl"] >= 0 else "-"}${abs(t["pnl"]):,.2f}</td></tr>'
        for t in trades)
    unpaired = trades_meta.get("unpaired_close_fills") or 0
    closed_card = (
        '<section class="card"><div class="kicker">Finished trades</div>'
        '<h2>Closed trades</h2>'
        '<p class="muted">Trades the desk has opened and closed, '
        'paired from its own fill journal, first in first out. A '
        'trade is listed only when both its opening and closing '
        'fills are in the journal record. '
        f'{unpaired} closing fills closed positions whose opening '
        'fills are not in the journal record, so they are not '
        'listed here: their entry prices are not on record.</p>'
        + ('<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%">'
           '<tr><th align="left">Closed</th><th align="left">Symbol</th>'
           '<th align="left">Strategy</th><th align="left">Side</th>'
           '<th align="left">Qty</th><th align="left">Entry avg</th>'
           '<th align="left">Exit</th><th align="left">Gain</th></tr>'
           + trade_rows + '</table></div>'
           if trade_rows else
           '<p class="muted">No trade has both its opening and '
           'closing fills in the journal record yet.</p>')
        + '</section>\n')
    tiles = "".join(
        f'<div style="display:inline-block;margin:0 8px 8px 0;padding:12px 14px;border-radius:12px;background:rgba(9,137,121,{0.25 + 0.65 * (p["share_pct"] / 100 if positions else 0):.2f});color:#082d36;min-width:150px">'
        f'<b>{_html.escape(str(p["symbol"]))}</b><br>{p["qty"]:g} held at ${p["avg_price"]:,.2f}<br>'
        f'${p["cost"]:,.2f} paid ({p["share_pct"]:.1f}% of cost)</div>'
        for p in positions) or '<p class="muted">No open positions in the latest snapshot.</p>'
    fam_rows = "".join(
        f'<tr><td>{_html.escape(str(f["family"]))}</td><td>{f["total"]}</td>'
        f'<td>{f["ready"]}</td><td>{f["waiting_for_data"]}</td><td>{f["paused"]}</td>'
        f'<td>{f["needs_attention"]}</td><td>${f["money_assigned"]:,.0f}</td>'
        f'<td>{f["orders_placed"]}</td></tr>' for f in families)
    section = (
        ATTRACTIONS_BEGIN + "\n"
        '<section class="card"><div class="kicker">The yardstick</div>'
        '<h2>Desk vs SPY and QQQ</h2>'
        f'<p class="muted">Percent change over the same window, from {_html.escape(start_date)} '
        'to the latest snapshot. The index lines use daily closes. The desk line joins the two '
        'equity readings the snapshot itself records, at the start of the current capital period '
        'and at the latest check. Nothing between those two readings is on record, so nothing '
        'between them is drawn.</p>' + _chart() + '</section>\n'
        '<section class="card"><div class="kicker">Open positions</div>'
        '<h2>Open positions heatmap</h2>'
        '<p class="muted">One tile per open position, sized and shaded by the share of the '
        'total cost paid for open positions. Cost is quantity times the average price paid, '
        'from the latest snapshot.</p>' + tiles + '</section>\n'
        '<section class="card"><div class="kicker">Strategy scorecards</div>'
        '<h2>Breakdown by strategy group</h2>'
        '<p class="muted">How each group of strategies stands on the latest check: how many '
        'there are, how many are ready, waiting for data, paused, or needing attention, the '
        'money assigned to the group, and orders placed on the last check.</p>'
        '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%">'
        '<tr><th align="left">Group</th><th align="left">Total</th><th align="left">Ready</th>'
        '<th align="left">Waiting</th><th align="left">Paused</th><th align="left">Needs attention</th>'
        '<th align="left">Assigned</th><th align="left">Orders</th></tr>'
        + fam_rows + '</table></div></section>\n'
        + small_card + closed_card + ATTRACTIONS_END)
    return data, section


def publish():
    dest = HERE / "desk"
    dest.mkdir(exist_ok=True)
    copied = []
    for name in FILES:
        src = SOURCE / name
        if not src.exists():
            print(f"FAIL: desk source missing: {src}")
            return 1
        out = dest / name
        shutil.copyfile(src, out)
        if _sha(src) != _sha(out):
            print(f"FAIL: desk copy does not match source: {name}")
            return 1
        copied.append(name)
    # Shared chart wiring on the published copy only, added after
    # the byte-for-byte copy above is hash-verified.
    page_path = dest / "index.html"
    page = page_path.read_text(encoding="utf-8")
    changed = False
    if "../shared.js" not in page:
        if "</head>" not in page:
            print("FAIL: desk page has no </head> to wire charts into")
            return 1
        page = page.replace("</head>", WIRING + "</head>", 1)
        changed = True
    # Reader-copy style scrub on the published copy only (repair
    # 2026-10-31): the terminal's pages carry no em dashes (the
    # owner's style rule, pinned by test_visual_polish_20261030). The
    # desk source is outside this program's surface and stays
    # untouched; its one em dash, in the load-failure line, is
    # replaced here at publish time, the same place the copy gains
    # its chart wiring.
    if "—" in page:
        page = page.replace(" — ", ": ")
        changed = True
    if changed:
        page_path.write_text(page, encoding="utf-8")
    feed = json.loads((dest / "terminal_feed.json").read_text(
        encoding="utf-8"))
    # AMAZING attractions on the published copy (built above from the
    # copied snapshot and the board panel; idempotent via markers).
    try:
        attractions, section = build_attractions(feed)
        (dest / "attractions.json").write_text(
            json.dumps(attractions, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        page = page_path.read_text(encoding="utf-8")
        if ATTRACTIONS_BEGIN in page:
            pre, rest = page.split(ATTRACTIONS_BEGIN, 1)
            _, post = rest.split(ATTRACTIONS_END, 1)
            page = pre + section + post
        elif "</main>" in page:
            page = page.replace("</main>", section + "\n</main>", 1)
        page_path.write_text(page, encoding="utf-8")
    except Exception as exc:
        print(f"FAIL: desk attractions build failed: {exc}")
        return 1
    data = build_data(feed)
    (dest / "data.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    # Self-enrich tail (cure 2026-10-31, Wave 2): every other hub
    # page carries its record_surface block from enrich_all, but a
    # bare republication of the desk page must not strip it. The
    # enrich rebuilds the same subject charts from the same data
    # through the one builder, so the block and the charts agree.
    try:
        import record_surface as _rs
        if not _rs.enrich_file(dest / "data.json"):
            print("FAIL: desk data.json could not be enriched")
            return 1
    except Exception as exc:
        print(f"FAIL: desk self-enrich failed: {exc}")
        return 1
    print(f"desk published: site/desk/ ({', '.join(copied)}), "
          "hash-verified against muse-desk-v3/terminal/; "
          "chart wiring and data.json (subject charts) built from "
          "the copied snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(publish())
