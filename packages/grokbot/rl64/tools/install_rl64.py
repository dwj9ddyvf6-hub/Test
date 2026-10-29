"""md2 2026-10-24 (Trader t181u 'Yes'): install the 64 Research Lab Q07 price-family weekly cells (CONFIRMED, fully specified in
DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.md/.csv) as TEST_MWJW paper sleeves. Additive only: adds playbook lanes (composer emits their fires
via sleeve_q07.cell_hits, the same generic path as the 49 existing s_q07w_* cells) and lz_engine sleeves.json rows. Undo copies written first.
Refuses any cell whose lane id or cell id already exists. Existing rows are never modified (L-146 scale factor untouched; new cells are 1 x $1k)."""
import json, csv, sys, os, shutil, hashlib, datetime
sys.path.insert(0, "/workspace/Trader-research/shadow/paper_sleeve"); import sleeve_q07 as Q
D2 = "/workspace/desk2"; PBP = "/workspace/Trader-research/shadow/paper_sleeve/sleeve_playbook.json"; SCP = f"{D2}/lz_engine/config/sleeves.json"
E_ = json.load(open(f"{D2}/evidence/research_lab_confirmed_vs_desk.json")); cells = [r["id"] for r in E_["unmapped"] if r["group"].startswith("B")]
P = {r["id"]: r for r in csv.DictReader(open("/workspace/Trader-research/DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv"))}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
PB = json.load(open(PBP)); SC = json.load(open(SCP))
os.makedirs(f"{D2}/evidence/undo", exist_ok=True)
for p, n in ((SCP, "sleeves.json.pre_rl64"), (PBP, "sleeve_playbook.json.pre_rl64")):
    dst = f"{D2}/evidence/undo/{n}"
    if not os.path.exists(dst): shutil.copy2(p, dst)
shutil.copy2(PBP, PBP.replace(".json", "_pre_rl64_1.0.14.json")) if not os.path.exists(PBP.replace(".json", "_pre_rl64_1.0.14.json")) else None
have_ids = set(PB["lanes"]) | {s["id"] for s in SC["sleeves"]}; have_cells = {v.get("q07_cell") for v in PB["lanes"].values()}
TPL_PB = PB["lanes"]["s_q07w_c52_sm_tierA_wcov"]; TPL_SC = next(s for s in SC["sleeves"] if s["id"] == "s_q07w_c52_sm_cheap5_wcov")
assert len(cells) == 64 and len(set(cells)) == 64
added, skipped = [], []
for cid in cells:
    c = Q.parse(cid); ln = Q.lane_short(cid); r = P.get(cid)
    if ln in have_ids or cid in have_cells: skipped.append((cid, "already on desk")); continue
    if r is None or r["verdict"] != "CONFIRMED" or set(c["tags"]) - {"tierA", "deep70", "cheap5", "mom6", "stress_vix20"} or (c["lane"] == "w_swing" and "tierA" in c["tags"]):
        skipped.append((cid, "not a fully specified CONFIRMED price-family cell")); continue
    H = c["H"]; lo, hi, mean = float(r["lo"]), float(r["hi"]), float(r["edge"]); label = f"Q07 {c['lane']} H{H} {c['band']} {'+'.join(c['tags'])} (test)"
    hold = f"hold = {H} weeks (W{H}; calendar weeks after the fire week, desk weekly time exit)"
    L = json.loads(json.dumps(TPL_PB))
    L.update(enabled=True, status="ready (md2 RL64 2026-10-24, Trader t181u)", version="1.0.15", public_name=label.replace(" (test)", ""), strategy_label=label,
             eligibility=dict(source=TPL_PB["eligibility"]["source"], families=[cid]), q07_cell=cid, q07_inputs_live=True, feed_dependency=[],
             cal_priority=round(-1 + lo / 1000, 4), q07_stats=dict(n=int(r["n"]), names=int(float(r["names"])), mean=round(mean, 2), lo=round(lo, 2), hi=round(hi, 2), q_fam=float(r["q_fam"]), verdict=r["verdict"]),
             wiki_rule=None, insider_rule=None, ats_rule=None,
             sources=[f"DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv {cid} (CONFIRMED; K {r['K']}; exit: {r['exit_rule']}; entry {r['entry']})",
                      f"CORPUS_AUDIT/out/Q07_confluence_cells.csv {'+'.join(c['tags'])} {c['lane']} H{H} {c['band']} red band: n {r['n']}, names {int(float(r['names']))}, edge +{mean:.1f} [{lo:.1f}, {hi:.1f}], q_fam {float(r['q_fam']):.3g}, CONFIRMED; px pool {r['px_edge'][:6] or 'n/a'} {r['px_verdict'][:40]}",
                      TPL_PB["sources"][2], "paper_sleeve/q07_inputs_v1_frozen.json (mom6 q67 pre-2020 per lane)"])
    L["exits"] = dict(TPL_PB["exits"], default=f"the sleeve feed fire's plan (no stop / time exit; {hold})")
    PB["lanes"][ln] = L
    S = json.loads(json.dumps(TPL_SC))
    S.update(id=ln, label=label, enabled=True, state="live", status_text=L["status"], source=dict(TPL_SC["source"], lane=ln), research=[x[:200] for x in L["sources"][:3]],
             flags=[f"md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"])
    S["exit"] = dict(TPL_SC["exit"], rule=f"the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; {hold})")
    S["sizing"] = dict(TPL_SC["sizing"], budget_usd=1000, max_slots=1)
    SC["sleeves"].append(S); added.append(ln); have_ids.add(ln)
PB["version"] = "1.0.15"
PB["changelog"].append(dict(version="1.0.15", at=now, by="Grok Bot (md2 RL64)", what=f"+{len(added)} Q07 price-family cell lanes (Q07_PRICE_FAMILY_PARAMS CONFIRMED, pure price tags); lanes only", why="Trader t181u: install the 64 Research Lab weekly cells as TEST paper sleeves"))
json.dump(PB, open(PBP + ".tmp", "w"), indent=1); os.replace(PBP + ".tmp", PBP)
SC["sources"]["TEST"] = dict(SC["sources"]["TEST"], version="1.0.15", sha256=sha(PBP))
json.dump(SC, open(SCP + ".tmp", "w"), indent=1); os.replace(SCP + ".tmp", SCP)
json.dump(dict(at=now, added=added, skipped=skipped, n_added=len(added)), open(f"{D2}/evidence/rl64_install.json", "w"), indent=1)
print(len(added), skipped)
