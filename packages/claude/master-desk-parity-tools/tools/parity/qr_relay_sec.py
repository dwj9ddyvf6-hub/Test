"""qr_relay_sec: the UIR / CRG source events -- relay.quarter_versions / surprise / decision_session on the current SEC
companyfacts and filing acceptances -- vs R3's recorded SOURCE_EVENTS (quant-research-backup@d170596b
research-archives/2026-10-08-alpha-extraction-r3/events/SOURCE_EVENTS.json, blob d51ed4fe: 84 events of CAT, DE,
MSFT from R2's current-vintage QUARTER_VERSIONS). SEC responses are cached on disk (SEC_CACHE) after one fetch.
Compared per (sender, quarter end): the accession, the acceptance time, the decision session and the surprise
(1e-9 relative); events present on one side only are diffs."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from . import write_receipt

SEC_CACHE = os.environ.get("SEC_CACHE", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/"
                                        "dl/sec")
R3_EVENTS = os.environ.get("R3_SOURCE_EVENTS", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/"
                                               "scratchpad/dl/r3/SOURCE_EVENTS.json")


def cached_fetch(url):
    from desk.data.http import get
    from desk.feedlib.edgar_buyback import user_agent
    os.makedirs(SEC_CACHE, exist_ok=True)
    p = os.path.join(SEC_CACHE, url.split("://", 1)[-1].replace("/", "_"))
    if os.path.exists(p):
        return json.load(open(p))
    doc = get(url, headers={"User-Agent": user_agent()}, timeout=60)
    with open(p, "w") as f:
        json.dump(doc, f)
    return doc


def run():
    import tempfile
    from desk.sleeves.quant_research import relay as R
    tmp = tempfile.mkdtemp(prefix="qr_relay_sec_")
    try:
        R.run(tmp, 0.0, fetch=cached_fetch)
        got = {(e["sender"], e["quarter_end"]): e for e in R.read_events(tmp)}
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    want = {(e["sender"], e["quarter_end"]): e for e in json.load(open(R3_EVENTS))}
    st = {"r3_events": len(want), "port_events": len(got), "matched": 0, "bad": 0, "only_r3": 0, "after_r3": 0,
          "counted": {"acceptance_clock": 0, "decision_moved_a_session": 0}}
    diffs = []
    last = max(e["decision_date"] for e in want.values())
    for k, w in sorted(want.items()):
        g = got.get(k)
        if g is None:
            st["only_r3"] += 1
            diffs.append({"event": k, "why": "missing in port"})
            continue
        same = (g["accession"] == w["accession"]
                and abs(g["surprise"] - w["surprise"]) <= 1e-9 * max(1.0, abs(w["surprise"])))
        ok = same and g["decision_date"] == w["decision_date"] and g["accepted_utc"][:19] == w["accepted_utc"][:19]
        if same and not ok:
            # R2 / R3 stored EDGAR's acceptance as the Eastern wall clock labelled UTC (4-5 hours early); the port
            # keeps the true UTC acceptance: named divergence `acceptance_clock`, the decision session can move to
            # the next close for a filing accepted between 16:00 ET and the mislabelled hour
            et = datetime.fromisoformat(g["accepted_utc"]).astimezone(ZoneInfo("America/New_York"))
            if et.strftime("%Y-%m-%dT%H:%M:%S") == w["accepted_utc"][:19]:
                st["counted"]["acceptance_clock"] += 1
                if g["decision_date"] != w["decision_date"]:
                    st["counted"]["decision_moved_a_session"] += 1
                    diffs.append({"event": k, "counted": "decision moved", "port": g["decision_date"],
                                  "r3": w["decision_date"]})
                st["matched"] += 1
                continue
        st["matched" if ok else "bad"] += 1
        if not ok:
            diffs.append({"event": k, "port": [g["accession"], g["decision_date"], g["surprise"], g["accepted_utc"]],
                          "r3": [w["accession"], w["decision_date"], w["surprise"], w["accepted_utc"]]})
    for k, g in got.items():
        if k not in want:
            if g["decision_date"] > last:
                st["after_r3"] += 1                                # newer filings than R3 saw: not diffs
            elif g["decision_date"] >= min(e["decision_date"] for e in want.values()):
                diffs.append({"event": k, "why": "only in port"})
                st["bad"] += 1
    cases = st["matched"] + st["bad"] + st["only_r3"]
    out = {"family": "quant_research", "sleeves": ["qr_unpricedinformationrelay", "qr_catalystresolutiongap"],
           "cases": cases, "identical": st["matched"], "n_diffs": cases - st["matched"], "detail": st,
           "diffs": diffs[:40], "sec_cache": SEC_CACHE,
           "method": "relay.run on the current SEC companyfacts / submissions vs R3's recorded source events"}
    write_receipt("qr_relay_sec", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["detail"]))
    for d in r["diffs"][:12]:
        print(d)
