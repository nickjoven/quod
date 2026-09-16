#!/usr/bin/env python3
"""seal_tierL.py <run_dir> <out.json> — tier L pilot exit record under amendment A1 (Wilson 80% lower bound)."""
import json, math, os, re, sys, glob, collections
run = sys.argv[1]; out = sys.argv[2]
rid = os.path.basename(run.rstrip("/"))
man = json.load(open(os.path.join(run, f"manifest-{rid}.json")))
pre = json.load(open(os.path.join(run, f"manifest-pre-{rid}.json")))
rows = [json.loads(l) for l in open(os.path.join(run, "attempts.jsonl"))]
names = sorted({r["demonstrandum"] for r in rows}); n = len(names)
acc = man.get("accepted") or {}
rounds = max([r["round"] for r in rows] + [0])
def wilson_lo(k, n, z=1.2816):  # 80% two-sided -> z_{0.90}
    if n == 0: return None
    p = k / n; d = 1 + z*z/n
    c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return round((c - h)/d, 4)
levels = {}
for L in sorted({1, 4, 8, rounds}):
    k = sum(1 for v in acc.values() if v <= L)
    levels[f"P_L({L})"] = {"point": round(k/n, 4), "accepted": k, "n": n, "wilson80_lower": wilson_lo(k, n)}
by_round = collections.Counter(acc.values())
outc = collections.Counter(r["outcome"] for r in rows)
errc = collections.Counter(r.get("err_class") for r in rows if r["outcome"] != "accepted")
scripts = {}
for f in glob.glob(os.path.join(run, "scripts-r*.jsonl")):
    for l in open(f, errors="replace"):
        o = json.loads(l); scripts[o["id"]] = o["script"]
brace = sum(1 for s in scripts.values() if re.search(r"\{|\[", s.split("\n",1)[0]) and s.startswith("intro"))
sorry = sum(1 for s in scripts.values() if re.search(r"\bsorry\b", s))
step0_brace = sum(1 for r in rows if "invalid {...} notation" in (r.get("err") or ""))
wall = sum((r.get("wall_s") or 0) for r in rows)
rec = {
 "tier": "L", "prover": pre["prover"], "model": pre["prover_config"]["model"],
 "weights_cid": pre["prover_config"]["weights"]["cid"], "weights_sha256": pre["prover_config"]["weights"]["sha256"],
 "prompt_style": pre["prover_config"].get("prompt_style"), "max_tokens": pre["prover_config"].get("max_tokens"),
 "exit_condition": "1 (pilot under amendment A1: frame first, stratified pilot, P frozen at the Wilson 80% lower bound)",
 "pilot_run": rid, "set": pre["set"], "n": n, "rounds_run": rounds,
 "P_frozen": {k: v["wilson80_lower"] for k, v in levels.items()},
 "P_point": {k: v["point"] for k, v in levels.items()},
 "levels": levels,
 "accepted_by_round": {str(k): v for k, v in sorted(by_round.items())},
 "outcomes": dict(outc), "err_classes": dict(errc),
 "proposals": len(scripts), "proposals_with_signature_binders_in_intro": brace, "step0_invalid_brace_notation": step0_brace,
 "proposals_with_sorry": sorry,
 "spend_cents_total": 0.0, "gpu": "RTX 4070 (Y40), llama.cpp CUDA 12.8, -ngl 99 -np 4 -c 32768",
 "wall_s_generation_total": round(wall, 1),
 "refusals": 0, "selfproof_rejections": man.get("selfproof_rejections"),
 "selfproof_note": "the model naming the hidden theorem's own Mathlib constant (statement recognized, label recalled); caught by the gate",
 "batch_build_rejections": sum(1 for r in rows if r.get("verdict") == "rejected: batch build failed"),
 "batch_build_note": "walker-accepted, build-rejected (Q-28: simp argument recovery); 24 transition rows from these scripts carry on_accepted_path=true",
 "manifest_cid": (re.findall(r"manifest CID: ([0-9a-f]{64})", open(os.path.join(run, "driver.log")).read()) or [None])[-1], "pre_manifest_cid": (re.findall(r"pre-manifest sealed: \S+ CID ([0-9a-f]{64})", open(os.path.join(run, "driver.log")).read()) or [None])[0],
 "prover_config_cid": pre["prover_config_cid"], "attempts_cid": man.get("attempts_cid"),
 "transitions_total": (man.get("transitions") or {}).get("n_transitions"),
 "caveats": [
  "Q-28: 8 walker-accepted scripts failed the batch build (unknown simp lemma names logged, not thrown); the build verdict stands and they are not counted",
  "Q-27: the Goedel completion template re-introduces signature binders (`intro {α} [inst : C α] ...`); such proposals die at step 0, so P_L is a lower bound on the model's capability under this presentation",
  "goedel-nocot at max_tokens 3000 after the plan-first template truncated 44/50 at 2000 (first pilot-L attempt, stopped after round 1, not on record)",
  "P_L is prover-relative and pilot-only until test200-L runs on the frame minus the pilot (controls-2026 test)",
 ],
 "unproven": [x for x in names if x not in acc],
}
json.dump(rec, open(out, "w"), indent=1); print(json.dumps({k: rec[k] for k in ("n","rounds_run","P_frozen","P_point","accepted_by_round","outcomes","err_classes","proposals","proposals_with_signature_binders_in_intro","step0_invalid_brace_notation","proposals_with_sorry","manifest_cid")}, indent=1))
