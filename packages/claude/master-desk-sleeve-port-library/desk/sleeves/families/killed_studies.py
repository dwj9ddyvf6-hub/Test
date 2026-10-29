"""killed_studies - the Midna desk's killed research studies (midna@main 7969b522, workspace/alpaca-swing-desk/desk/
research, inventoried in resurrection/KILL_INVENTORY.md), each forward-tested on the engine exactly as the killed
formulation specified so the forward record re-checks the kill (desk/sleeves/killed/*):

  killed_golden_cross_spy        SPY 50/200 SMA cross, long/flat, all-in (daily.py)
  killed_leader1d_long           gated Leader-1d event, genome 1,838, long open t+1 -> close t+20, de-overlapped
  killed_leader1d_short          the same event on the 41-name basket, short open t+1 -> close t+20
  killed_naive_20d_breakout      strict 20d closing high, 41 names, long open t+1 -> close t+20
  killed_rsiobv_daily            RSIxOBV studies A/B/C on 19 names (divergence buckets, trendline overlays, RSI filters)
  killed_intraday_momentum_gao   SPY/QQQ sign(first-30-min) from 15:30 to the close (intraday.py)
  killed_rsiobv_intraday         BuR RSI STRONG/SUPERSTRONG 5m divergences, 8 names, 2h/4h/8h forwards
  killed_short_candidates        the six fade / inversion candidates on 30m + daily bars
  killed_pairs_distance_coint    top-20 SSD pairs, |z| 2.0 / 0.5 / 4.0 stop, half-year windows (pairs.py)
  killed_pairs_news_filtered     V1: |z| > 2.5 news-clean entries, 10-session time stop
  killed_pead_price_surprise     top-quintile SPY-adjusted [t-1, t+1] surprise, long t+2 open, 1/5/10/20d (events.py)
  killed_pead_spillover_scalp    earnings day with r_prev_net > +0.01%: buy the close, sell the next open
  killed_smcap_beta_52w          M2 qualifier weeks BEAT and SMALL and HIBETA, 52 weeks (smcap.py)

Removed (cutover doctrine), desk-wide only: the research protocol's own gate on paper trading (no paper sleeve after a
failed dev gate, or without a holdout pass and explicit approval - the forward test is what that gate withheld), and
on the short-side sleeves (Leader-1d short, pairs, short candidates, the RSIxOBV bear arms, the Gao short days) the
desk's long-only rail. Every study rule stays. Producers (desk/feedlib/killed_data.py) run as family jobs and are read
through FEEDS; the Leader-1d rows are the genome job's (cache/leader_events.json). Named divergences are listed in each
sleeve's params (named_divergences: the common execution three, then the sleeve's own)."""
import os

from ...feedlib import killed_data as KD
from ..killed import daily, events, intraday, pairs, smcap


def feed_leader_last(feeds, sleeve, now, arg=None):
    """the genome job's Leader-1d rows of the last completed session ({SYM: [date, score, gate]})."""
    from ...feedlib import leader
    root = os.path.dirname(feeds.hub.cache.root) if feeds.hub is not None else "cache"
    return leader.load_last_close(os.path.join(root, "leader_events.json"), now)


FEEDS = {"killed_leader_last": feed_leader_last,
         "killed_pead": KD.feed_pead,
         "killed_spillover": KD.feed_spillover,
         "killed_pairs": KD.feed_pairs,
         "killed_pairs_news": KD.feed_pairs_news,
         "killed_smcap": KD.feed_smcap}

JOBS = {"killed_pead": ("weekday:12345&et:16:25-23:30", 3600, KD.pead_job),
        "killed_spillover": ("weekday:12345&et:15:27-15:41", 240, KD.spillover_job),
        "killed_pairs_form": ("weekday:12345&et:16:30-23:30", 6 * 3600, KD.pairs_form_job),
        "killed_pairs_news": ("weekday:12345&close-75:close-40", 1800, KD.pairs_news_job),   # before every auction
        "killed_smcap": ("weekday:5&et:16:45-23:59", 1800, KD.smcap_job)}


def sleeves():
    return [daily.GoldenCrossSpy(), daily.Leader1dLong(), daily.Leader1dShort(), daily.Naive20dBreakout(),
            daily.RsiObvDaily(), intraday.IntradayMomentumGao(), intraday.RsiObvIntraday(),
            intraday.ShortCandidates(), pairs.PairsDistance(), pairs.PairsNewsFiltered(),
            events.PeadPriceSurprise(), events.PeadSpilloverScalp(), smcap.SmcapBeta52w()]
