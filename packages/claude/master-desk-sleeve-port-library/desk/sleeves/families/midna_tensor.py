"""midna_tensor — Midna's Tensor books (the Midna TypeScript desk and its Lazarus port), each restored on the engine
under its manifest sleeve_id from the pinned source (desk/sleeves/midna/*, parity receipts under
docs/receipts/parity/midna_*.json):

  midna_d_cyan_gbm / midna_d_green_band / midna_w_cyan_quiet_tape / midna_w_cyan_mid_vix / midna_w_green_calm_smh /
  midna_w_cyan_high_adx            forward.ts lab accounts over forward-scan.ts (the Tensor engine on the daily
                                   panel + the frozen v4 GBM) (forward.py, forward_scan.py)
  midna_w_cyan_moonshot            shadow.ts stepMoonshot on the hourly watch's weekly cyan moonshots (shadow.py)
  midna_hourly_playbook            rules.ts evaluatePass (playbook 1.0.0) on the hourly watch's 1H inbox (hourly.py)
  midna_nostop / midna_w_cyan_breadth / midna_hourly_1d / midna_hourly_1w
                                   the Lazarus Midna lanes s_mn_nostop / s_mn_w_cyan_breadth / s_mn_hourly_1d /
                                   s_mn_hourly_1w on the Lazarus runtime, fed by the sleeve_midna producer port
                                   (lanes.py, desk/feedlib/midna_fires.py; the hourly 1D / 1W lanes read the canonical
                                   tracker's latest_fires_v3.json + ledger under the Lazarus inputs root)

Producers run in-pass as feeds (FEEDS) reading cached results; the forward scan is this family's job (JOBS), the
hourly watch the midna family's. Each module docstring names its removed desk-wide gates and its named divergences."""
from ...feedlib import midna_fires, midna_forward, midna_panel, midna_watch
from ..midna import forward, hourly, lanes, shadow

FEEDS = {"midna_panel": midna_panel.feed_panel,
         "midna_forward_scan": midna_forward.feed_scan,
         "midna_watch": midna_watch.feed_watch,
         "midna_fires": midna_fires.feed_fires}

# the forward-lab scan runs the Node engine in its own job process (never inside the pass loop): after the close and
# before the open, every 15 minutes until the fresh panel's session is scanned
JOBS = {"midna_forward_scan": ("weekday:12345&et:16:20-23:59,weekday:12345&et:04:00-10:30", 900, midna_forward.job)}


def sleeves():
    return forward.sleeves() + [shadow.WeeklyCyanMoonshot(), hourly.HourlyPlaybook()] + lanes.sleeves()
