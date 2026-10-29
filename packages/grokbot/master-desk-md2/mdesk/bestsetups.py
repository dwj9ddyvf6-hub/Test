"""Best Setups, used exactly as it is: its own decisions.json and its own ondemand.analyze(), imported from its source
directory (never copied, never modified). md2 only READS the returned decision and uses its conviction tier to order
candidates when a sleeve's slot cap binds - the same rule Lazarus uses (cloudflare/export_plans.py best_setups())."""
import sys, json, os, time, hashlib
BS = "/workspace/Trader-research/shadow/terminal/bestsetups"
TIER = {"Top": 0, "High": 1, "Medium": 2, "Low": 3}
CACHE = "/workspace/desk2/state/bs_cache"

def source_hash():
    h = hashlib.sha256()
    for f in sorted(os.listdir(BS)):
        if f.endswith(".py"): h.update(f.encode()); h.update(open(os.path.join(BS, f), "rb").read())
    return h.hexdigest()

def analyze(sym, asof=None):
    """the unmodified Best Setups per-ticker document."""
    if BS not in sys.path: sys.path.insert(0, BS)
    import ondemand
    return ondemand.analyze(sym, asof=asof)

def board():
    try: return json.load(open(f"{BS}/out/decisions.json")).get("decisions") or {}
    except Exception: return {}

def rank(syms, budget_s=120):
    """{sym: dict(tier, rank, label, zone, invalidation, target, rr, src)}; missing = not ranked (rank 4), never negative."""
    os.makedirs(CACHE, exist_ok=True); day = time.strftime("%F"); cp = f"{CACHE}/{day}.json"
    cache = json.load(open(cp)) if os.path.exists(cp) else {}; D = board(); out = {}; t0 = time.time(); dirty = False
    for s in sorted(set(syms)):
        d = D.get(s) or cache.get(s)
        if d is None and time.time() - t0 < budget_s:
            try: d = (analyze(s) or {}).get("decision") or {}
            except Exception as e: d = dict(error=type(e).__name__)
            cache[s] = d; dirty = True
        if not d or d.get("error"): continue
        out[s] = dict(tier=d.get("conviction"), rank=TIER.get(d.get("conviction"), 4), label=d.get("label"), zone=d.get("entry"),
                      invalidation=(d.get("invalidation") or {}).get("v"), target=(d.get("objective") or {}).get("v"), rr=d.get("rr"), src="board" if s in D else "ondemand")
    if dirty: tmp = cp + ".tmp"; json.dump(cache, open(tmp, "w")); os.replace(tmp, cp)
    return out
