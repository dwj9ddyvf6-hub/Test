"""Pinned Author-desk sources the Author parity harnesses run under Node 22 (git blob shas; node_pinned.stage reads each
from $Author_DESK when it is checked out there at that blob, else from $PARITY_BLOBS by sha), and the shared
deterministic daily-bar generator."""
import random

COMMIT = "652db7afcc4312b6bd44d41547ca0f73981fe3ff"
# the runtime import closure of the daily book pipeline (prism scan, buy-desk distill, admit-ticker, washout,
# bottom-screen, curl, select, sector-tape and what they import), @652db7af
BOOK_TS = {
    "src/lib/prism/ascend.ts": "bd616a752d0e00dc4a3584550272deb84c668863",
    "src/lib/prism/catalog.ts": "4d98cd3c30f4d43d60b01ba5d80899c7c0335bcf",
    "src/lib/prism/engines.ts": "bce9a09a195a3ce60239aa235349e4b34ec8f60a",
    "src/lib/prism/ether.ts": "87bf050323b7f2d663512ac191ab8416f9ec7b0c",
    "src/lib/prism/kernel.ts": "ef279262e81a4bd71a8e96b43234dbf103590ea6",
    "src/lib/prism/oracle.ts": "a659a918158f033ff3cbb747ec5af26c31dae2fc",
    "src/lib/prism/physics.ts": "c15ed45171c0fbb5e427a61ee72147a78b548598",
    "src/lib/prism/predicates.ts": "fe0388761bc75d1d0d1721b5476a1b7c49d8739f",
    "src/lib/prism/scan.ts": "eaef8ae7f69bd308a37076ecccc3c20e3f7b8319",
    "src/lib/tensor/indicators.ts": "04d1402b4e3c6db28c0b2447ec1fdb498a725fee",
    "src/lib/tensor/math.ts": "4add3a71847a6b9a7322b69e2a914ad290247e4a",
    "src/lib/tensor/session.ts": "7e6799c3bc18cbe1c5c7ecd9d3dbf1bdeb1b467b",
    "src/lib/voice/identities.ts": "789a704a4575c33ebc2478573765d620e92a5ea1",
    "src/lib/voice/retrieve.ts": "c323f20ace8709a586cf16dba8d8c73e9469a94c",
    "src/lib/workdesk/admit-ticker.ts": "2ba2130f275a125af190a396ed71337c8768181a",
    "src/lib/workdesk/after-hours.ts": "9366faf281fcb28b6f319060017a16e2b85114ff",
    "src/lib/workdesk/bottom-screen.ts": "a929d9f2a3615250fedbcd9d49f9f23d1b19f760",
    "src/lib/workdesk/buy-desk.ts": "b55128ddff2ca45e22d6ab35dd0956d6d3761295",
    "src/lib/workdesk/copy.ts": "2e0db8fb459e98bca01fecda2ced360a2b3a53d0",
    "src/lib/workdesk/curl.ts": "4ea3154b4918a28fbd86cc4611ec85ecb2e02b6e",
    "src/lib/workdesk/desk-post.ts": "f8ba5256a866685a0014c2fffcd66973b2b17ee8",
    "src/lib/workdesk/doctrine.ts": "59cf28537f2bd48fe5cc42fc82659de620afaaf0",
    "src/lib/workdesk/engage.ts": "10ecf44a4900b09ff389b8e6713e4c102cd8669d",
    "src/lib/workdesk/exit.ts": "9e496477d7b780f3b09da90f1ceba16f0d352ca2",
    "src/lib/workdesk/folio-novelty.ts": "efa996caea403313d72ff5f33a2d194c648294bb",
    "src/lib/workdesk/folio-voice.ts": "4b66fc0b575911e6d94afd92274a35eb42d53c6f",
    "src/lib/workdesk/fund-overlay.ts": "9eaff1c4700edf83e4708ce28b6b2d8f8d6c4076",
    "src/lib/workdesk/language-editor.ts": "0778b4b3beb69cc8ca7f54ccde820fe86dfcca46",
    "src/lib/workdesk/location-law.ts": "9b63af7b2d2a4f8c7959201917b85c33c6d96970",
    "src/lib/workdesk/public-doctrine.ts": "ec91ee8f131d6c36b875eb36bd54f3317534fac7",
    "src/lib/workdesk/scanner-prompt.ts": "ceca8d80f6208e0265738607700657a6ba0ab403",
    "src/lib/workdesk/sector-copy.ts": "4add373d414e018ae09586a912dfde0e999aa499",
    "src/lib/workdesk/sector-map.ts": "5f4d89903bef4fc6c7d3f4f1f55055101945d5d3",
    "src/lib/workdesk/sector-tape.ts": "5693b6d68c98177ecf276b8d8ac6796ce5c48713",
    "src/lib/workdesk/select.ts": "a5078c1d87b8a2dc0e1cd9e5a062126a4f038e1f",
    "src/lib/workdesk/tape-levels.ts": "5f214698eaf64a4a0ddd207f774d6efafa02ac19",
    "src/lib/workdesk/washout.ts": "d6d55212acc6206cb8cb9da94c0bbb67045c308b",
    "src/lib/workdesk/weekend-desk.ts": "9b4967d334534a67693df6061eeb2f82551d1dc6",
    "src/lib/workdesk/x-feedback.ts": "3d8de400843f9c8603f3bcaac93e1ea9dd72d92b",
}
# JSON the closure loads at module time (not checked out in the partial clone: fetched by blob into $PARITY_BLOBS)
BOOK_DATA = {
    "src/lib/voice/machine/situations.json": "e9fbbecd6c9191e25c4e84bf0e2f9f3b43c937bb",
    "src/lib/voice/machine/scanner-identities.lock.json": "871e0001b957894a70907e26069a889c8e76228c",
    "src/lib/voice/machine/manifest.json": "a9b92842b14ef40b5d8dde1c164a9f209044bf8e",
    "src/lib/voice/machine/contract.json": "ffd7e61fa18206ae95b1175e4fc47445a51c7144",
}
# komar-momentum@0.1.0: Author-desk @a4fc436c (removed at 3476c028)
KOMAR_COMMIT = "a4fc436cc2daa3b5853820550fdeac8a1e4956c7"
KOMAR_TS = {
    "src/lib/komar/types.ts": "534c501b2be8fe399ed9786b92eec74ad849c5d5",
    "src/lib/komar/math.ts": "3add1faaed6abe40b5d4bcaf9d0892611d7c08ce",
    "src/lib/komar/proxies.ts": "e54bb0a683ef91b04d7f84e490a64deacb1f7cdd",
    "src/lib/komar/screen.ts": "52023d6effe7315e73773248e15e37b35ee80ef5",
    "src/lib/komar/size.ts": "b83fa85479cba10c96287a0684424f5b34f9e4a7",
}
# the seven-vote Anna printer as it stood before Tensor 2.0 retired it: Author-desk @7683c7dd
ANNA_COMMIT = "7683c7dd5a"
ANNA_TS = {
    "src/lib/tensor/anna-replica.ts": "a769d404b30279286a8e7bc7f1884943f62e7734",
    "src/lib/tensor/anna-printer.ts": "63a0b153224d1afb55853f9e098f528599eb7080",
    "src/lib/tensor/anna-epochs.ts": "6f1091cb8d3cd98a5591f57e0e69277c95ca349e",
    "src/lib/tensor/indicators.ts": "04d1402b4e3c6db28c0b2447ec1fdb498a725fee",
    "src/lib/tensor/math.ts": "dca1b368d2e26c3a303186201ac34e05564f7d3d",
    "src/lib/tensor/doctrine.ts": "1742dcbb9ce7e0f5f83fd20e1d2191166a87b4dc",
    "src/lib/tensor/types.ts": "bac164c16e0b42c786d63feefba9ba7d37d117d0",
    "src/lib/tensor/session.ts": "ab961ce8fbe3ade2cb8145f7d47bb167eea5e12a",
}

DAY_MS = 86_400_000


def daily_bars(rnd, n, start_ms=None, stamp=None, px=None, regime=None):
    """n weekday daily bars (epoch ms at 04:00 UTC like Alpaca's or 13:30 UTC like Yahoo's), random-walk regimes:
    trends, washouts under the 50-day, tight coils, gaps; volume with climaxes and dry spells."""
    t = start_ms if start_ms is not None else 1_700_000_000_000 - (1_700_000_000_000 % DAY_MS) + rnd.randint(0, 500) * DAY_MS
    t = t - (t % DAY_MS) + (stamp if stamp is not None else rnd.choice([4 * 3600_000, 13 * 3600_000 + 30 * 60_000]))
    px = px if px is not None else rnd.choice([rnd.uniform(1, 12), rnd.uniform(8, 80), rnd.uniform(40, 600)])
    base_v = rnd.choice([rnd.uniform(5e4, 5e5), rnd.uniform(5e5, 2e7)])
    out = []
    drift, vol, left = 0.0, 0.02, 0
    for _ in range(n):
        while ((t // DAY_MS) + 4) % 7 in (5, 6):
            t += DAY_MS
        if left <= 0:
            kind = regime or rnd.choice(["trend", "trend", "drop", "coil", "chop", "rip"])
            drift = {"trend": rnd.uniform(0.0005, 0.004), "drop": rnd.uniform(-0.012, -0.003), "coil": 0.0,
                     "chop": rnd.uniform(-0.001, 0.001), "rip": rnd.uniform(0.006, 0.02)}[kind]
            vol = {"trend": rnd.uniform(0.01, 0.03), "drop": rnd.uniform(0.015, 0.04), "coil": rnd.uniform(0.004, 0.01),
                   "chop": rnd.uniform(0.01, 0.03), "rip": rnd.uniform(0.02, 0.05)}[kind]
            left = rnd.randint(5, 60)
        left -= 1
        gap = rnd.gauss(0, vol / 3) + (rnd.choice((-1, 1)) * rnd.uniform(0.03, 0.12) if rnd.random() < 0.02 else 0)
        o = max(0.05, px * (1 + gap))
        c = max(0.05, o * (1 + rnd.gauss(drift, vol)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = base_v * rnd.uniform(0.3, 1.8) * (rnd.uniform(2, 6) if rnd.random() < 0.04 else 1)
        dp = 4 if px < 1 else 2
        out.append({"t": t, "o": round(o, dp), "h": round(max(h, o, c), dp), "l": round(min(lo, o, c), dp),
                    "c": round(c, dp), "v": float(int(v))})
        px = c
        t += DAY_MS
    return out
