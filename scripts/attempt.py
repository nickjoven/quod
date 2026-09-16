#!/usr/bin/env python3
"""attempt.py --corpus <declarations corpus dir> [--only A,B,..] [--sample-mod N]
              [--limit N] [--negate] [--ladder rfl,decide,...] [--heartbeats N]
              [--run-id ID] [--out DIR] [--no-ket] [--timeout S] [--start-timeout S]

Phase-1 attempt driver (ATTEMPTS.md rev 2, scope §3-4). Runs AttemptWalk.lean
under corpus_extract's watchdog/resume machinery, then for every accepted
attempt:
  1. SELF-PROOF GATE (scope §2): the term's used constants may contain neither
     the demonstrandum's name nor any constant whose LOCK equals the
     demonstrandum's lock (locks from the declarations corpus). Recorded as
     `selfproof_ok`; a failure makes the attempt `rejected: self-proof`.
  2. Writes the surviving attempts into a generated module
     calib/Quod/Attempts/<Batch>.lean as
        theorem attempt_i : type_of% <D> := by <tactic>        (or ¬ (type_of% D))
     so the statement re-elaborates from the declaration itself (no pretty-
     print round-trip), and `lake build`s it.
  3. Runs the EXISTING gates unchanged on each attempt declaration:
     axiom_gate.py (via calibrate.axioms / axiom_verdict) and lean4checker
     (via calibrate.CHECKER, same invocation as calibrate.py).
  4. Records one attempt line + ket-puts proof/gate outputs; writes an
     append-only manifest whose CID is the attempt-corpus version.
Verdicts are exactly SEMANTICS.md's proof-verdict lattice; `no_proof_found`
is a distinct outcome tagged with prover + prover_config_cid, never a verdict.
--negate: prover-negative control. ANY accepted+gated ¬T HALTS the run.
"""
import argparse, glob, hashlib, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_extract as ce   # noqa: E402  (run_segment, normalize, lock_of, sha256_file, ket_put_file)
import calibrate as cal       # noqa: E402  (axioms, axiom_verdict, CHECKER, run, CALIB)

ROOT, CALIB, SCRIPTS = ce.ROOT, ce.CALIB, ce.SCRIPTS
WALKER = os.path.join(SCRIPTS, "AttemptWalk.lean")
ATT_DIR = os.path.join(CALIB, "Quod", "Attempts")


def corpus_locks(corpus_dir: str) -> dict[str, str]:
    locks = {}
    for path in sorted(glob.glob(os.path.join(corpus_dir, "declarations-*.jsonl"))):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                locks[r["name"]] = r["lock"]
    return locks


def parse_tagged(raw_path: str, tags: tuple[str, ...]):
    """(tag, json) for every well-formed `TAG\\t<json>` line of the walker output."""
    with open(raw_path, errors="replace") as f:
        for line in f:
            tag, sep, rest = line.partition("\t")
            if sep and tag in tags:
                try:
                    yield tag, json.loads(rest)
                except json.JSONDecodeError:
                    continue


def parse_atts(raw_path: str):
    for _, j in parse_tagged(raw_path, ("ATT",)):
        yield j


def write_transitions(out_dir: str, raw: str, atts: list[dict], locks: dict[str, str], run_id: str,
                      prover: str, prover_config_cid, put_file, shard: int = 10000) -> dict:
    """The transition corpus: every recorded tactic step of every attempt, with
    goal identities hashed exactly like locks (lock_of over the walker's
    canonical form), sharded under <out_dir>/transitions/ with per-shard sha256
    and CID. `on_accepted_path` = the step lies on the rung that the kernel
    accepted. A `budget` step is CENSORED (cap hit), never a cost. Returns the
    manifest section: counts, outcome distribution per ladder position,
    accepted-path fraction, shard table."""
    by_aid = {a["aid"]: a for a in atts if "aid" in a}
    tdir = os.path.join(out_dir, "transitions")
    os.makedirs(tdir, exist_ok=True)
    goals: dict[int, str] = {}
    grows, trows = [], []
    by_pos: dict[str, dict[str, int]] = {}
    for tag, j in parse_tagged(raw, ("GOAL", "TRANS")):
        if tag == "GOAL":
            lock, _ = ce.lock_of(ce.normalize(j["canonical"]))
            goals[j["gid"]] = lock
            grows.append({"lock": lock, "readable": j["readable"], "readable_truncated": j["readable_truncated"],
                          "canonical": j["canonical"]})
            continue
        a = by_aid.get(j["aid"])
        if a is None or j["before"] not in goals:
            continue
        after = j["after"]
        after_locks = after if isinstance(after, str) else [goals[g] for g in after if g in goals]
        outcome = ("budget" if j["err_class"] == "budget" else after if isinstance(after, str) else "open")
        if "path_sids" in a:      # stepping prover: the accepted path is a list of step ids
            on_path = a["outcome"] == "accepted" and a.get("verdict") in (None, "accepted") and j.get("sid") in set(a["path_sids"])
        else:
            on_path = a["outcome"] == "accepted" and a.get("verdict") in (None, "accepted") and (j["kind"] == "intros" or j["pos"] == a.get("accepted_pos"))
        key = f"{j['pos']}:{j['kind']}"
        by_pos.setdefault(key, {})[outcome] = by_pos.setdefault(key, {}).get(outcome, 0) + 1
        trows.append({"attempt_id": f"{run_id}:{j['aid']}", "demonstrandum": a["demonstrandum"],
                      "demonstrandum_lock": a.get("mutant_lock") or locks.get(a["demonstrandum"]),
                      "mutant_operator": a.get("mutant_operator"), "negated": bool(a.get("negated", False)),
                      "prover": prover, "prover_config_cid": prover_config_cid,
                      "source": "ladder" if prover == "ladder-A" else "search", "predictor_cid": None,
                      "pos": j["pos"], "kind": j["kind"], "tactic": j["tactic"],
                      "goal_before": goals[j["before"]], "goal_after": after_locks, "outcome": outcome,
                      "err_class": j["err_class"], "err": j["err"],
                      "heartbeats": j["heartbeats"], "heartbeat_cap": j["heartbeat_cap"],
                      "censored": j["err_class"] == "budget", "wall_ms": j["wall_ms"],
                      "on_accepted_path": on_path, "attempt_outcome": a["outcome"], "attempt_verdict": a.get("verdict")})
    shards = []
    for kind, rows in (("goals", grows), ("transitions", trows)):
        for i in range(0, max(len(rows), 1), shard):
            chunk = rows[i:i + shard]
            if not chunk:
                break
            p = os.path.join(tdir, f"{kind}-{i // shard:04d}.jsonl")
            with open(p, "w") as f:
                for r in chunk:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            shards.append({"file": os.path.relpath(p, out_dir), "kind": kind, "records": len(chunk),
                           "sha256": ce.sha256_file(p), "cid": put_file(p)})
    return {"n_transitions": len(trows), "n_goals": len(grows),
            "censored": sum(r["censored"] for r in trows),
            "on_accepted_path": sum(r["on_accepted_path"] for r in trows),
            "accepted_path_fraction": round(sum(r["on_accepted_path"] for r in trows) / len(trows), 4) if trows else None,
            "by_position": by_pos, "shards": shards}


def selfproof_check(att: dict, locks: dict[str, str]) -> tuple[bool, list[str]]:
    """False iff the proof uses a constant whose lock equals the DEMONSTRANDUM's
    lock (or, for a theorem attempt, the theorem's own name). For a MUTANT
    attempt the demonstrandum is the mutant — a different statement with its
    own lock — so using the parent theorem is legitimate proving, not self-proof;
    only a library constant with the mutant's lock would be."""
    d = att["demonstrandum"]
    if att.get("mutant_lock"):
        dlock = att["mutant_lock"]
        offenders = [c for c in att.get("used_consts", []) if locks.get(c) == dlock]
    else:
        dlock = locks.get(d)
        offenders = [c for c in att.get("used_consts", [])
                     if c == d or (dlock is not None and locks.get(c) == dlock)]
    return (len(offenders) == 0, offenders)


def corpus_mutants(mut_dir: str) -> dict[tuple[str, str], tuple[str, bool]]:
    out = {}
    for path in sorted(glob.glob(os.path.join(mut_dir, "mutants-*.jsonl"))):
        with open(path) as f:
            for line in f:
                m = json.loads(line)
                out[(m["parent"], m["operator"])] = (m["lock"], bool(m["elaborates"]))
    return out


HEADER = """import Quod.Mutate
open Lean Elab Term Meta in
/-- The declaration's statement, read from its ConstantInfo (no pretty-print
round-trip), with universe params instantiated as u_0.. — the theorem using
it declares matching universe binders. -/
elab "type_of_decl! " n:ident : term => do
  let ci ← getConstInfo n.getId
  let us := (List.range ci.levelParams.length).map fun i => mkLevelParam (Name.mkSimple s!"u_{i}")
  return ci.type.instantiateLevelParams ci.levelParams us

open Lean Elab Term Meta in
/-- A statement MUTANT of the declaration, rebuilt in-process by the same
shared operators that built the corpus (Quod.Mutate) — never round-tripped
through a pretty-printer. The driver has already verified its lock equals
the corpus record's. -/
elab "mutant_of_decl! " n:ident op:str : term => do
  let ci ← getConstInfo n.getId
  let us := (List.range ci.levelParams.length).map fun i => mkLevelParam (Name.mkSimple s!"u_{i}")
  match ← Quod.Mutate.mutantNamed ci.type op.getString with
  | some t => return t.instantiateLevelParams ci.levelParams us
  | none => throwError "no mutant {op.getString} of {n.getId}"

-- generated by scripts/attempt.py; one theorem per accepted attempt
set_option maxHeartbeats 400000
"""


BATCH_SIZE = 100   # attempts per generated gate module (blast radius of one build failure)


def write_batch_module(batch: str, atts: list[dict], negate: bool, heartbeats: int = 0
                       ) -> tuple[str, dict[int, str]]:
    """Generate calib/Quod/Attempts/<batch>.lean; returns (module name, line ->
    attempt_name). Each theorem is ONE source line so a build error maps to its
    attempt. `heartbeats` > 0 replays under the same elaboration budget the
    prover searched with (recorded in prover_config) — a budget, not a gate."""
    os.makedirs(ATT_DIR, exist_ok=True)
    lines, line_of = HEADER.split("\n"), {}
    for a in atts:
        n = int(a.get("n_levels", 0))
        univ = ".{" + ",".join(f"u_{i}" for i in range(n)) + "}" if n else ""
        if a.get("mutant_operator"):
            body = f'mutant_of_decl! {a["demonstrandum"]} "{a["mutant_operator"]}"'
        else:
            body = f"type_of_decl! {a['demonstrandum']}"
        stmt = f"¬ ({body})" if negate else body
        pre = f"set_option maxHeartbeats {heartbeats} in " if heartbeats else ""
        tac = a["tactic"]
        if "\n" not in tac:
            lines.append(f"{pre}theorem {a['attempt_name']}{univ} : {stmt} := by {tac}")
            line_of[len(lines)] = a["attempt_name"]
        else:
            # a multi-line script (script mode wraps it as "(line1\n line2 ...)"): put the body under
            # `by` on its own lines, indented, so Lean's column rule holds regardless of the header width
            body = tac[1:-1] if tac.startswith("(") and tac.endswith(")") else tac
            blines = body.split("\n")
            blines = [blines[0]] + [l[1:] if l.startswith(" ") else l for l in blines[1:]]
            lines.append(f"{pre}theorem {a['attempt_name']}{univ} : {stmt} := by")
            line_of[len(lines)] = a["attempt_name"]
            lines.extend("  " + l for l in blines)
        lines.append("")
    with open(os.path.join(ATT_DIR, f"{batch}.lean"), "w") as f:
        f.write("\n".join(lines))
    return f"Quod.Attempts.{batch}", line_of


def axioms_many(module: str, decls: list[str]) -> tuple[dict[str, dict], str]:
    """axiom_gate.py over many decls in ONE Lean process (the gate script already
    takes a decl list; calibrate.axioms is its one-decl case). -> ({decl: result}, raw)."""
    rc, out = cal.run(["python3", f"{cal.SCRIPTS}/axiom_gate.py", CALIB, module, *decls, "--json"])
    try:
        js = json.loads(out[out.index("{"):out.rindex("}") + 1])
        res = {r["decl"]: r for r in js["results"]}
    except Exception:
        res = {}
    return res, out


def gate_shard(batch: str, atts: list[dict], negate: bool, heartbeats: int, put_bytes) -> None:
    """External gates on one shard of in-process-accepted attempts, exactly as
    calibrate.py runs them: lake build -> axiom_gate.py -> lean4checker. A
    theorem that fails to BUILD is rejected individually (error line -> attempt)
    and the shard is rebuilt once without it; a second failure rejects the shard."""
    live = list(atts)
    module = None
    for round_ in (1, 2):
        module, line_of = write_batch_module(batch, live, negate, heartbeats)
        brc, bout = cal.run(["lake", "build", module], cwd=CALIB)
        if brc == 0:
            break
        errs: dict[str, list[str]] = {}
        starts = sorted(line_of)
        # lake prints `error: Quod/Attempts/<batch>.lean:LINE:COL: <msg>`
        for m in re.finditer(rf"error: [^\s:]*{re.escape(batch)}\.lean:(\d+):\d+: [^\n]*", bout):
            ln = int(m.group(1))
            owner = max((s for s in starts if s <= ln), default=None)
            if owner is not None:
                errs.setdefault(line_of[owner], []).append(m.group(0)[:300])
        if not errs or round_ == 2:
            for a in live:
                a["verdict"] = "rejected: batch build failed"
                a["build_err"] = bout[-400:]
            return
        for a in live:
            if a["attempt_name"] in errs:
                a["verdict"] = "rejected: batch build failed"
                a["build_err"] = "\n".join(errs[a["attempt_name"]])
        live = [a for a in live if a["attempt_name"] not in errs]
        if not live:
            return
    res, raw_ax = axioms_many(module, [a["attempt_name"] for a in live])
    acid = put_bytes(raw_ax.encode(), f"ax_{batch}")
    for a in live:
        ax = res.get(a["attempt_name"], {"ok": False, "extra": ["<lean error>"], "axioms": []})
        a["gate_axioms"] = ax.get("axioms")
        a["verdict"] = cal.axiom_verdict(ax)
        a["axioms_cid"] = acid
    if any(a["verdict"] == "accepted" for a in live):
        krc, kout = cal.run(["lake", "env", cal.CHECKER, module], cwd=CALIB)
        kcid = put_bytes(kout.encode(), f"checker_{batch}")
        for a in live:
            if a["verdict"] == "accepted":
                a["checker_rc"], a["checker_cid"] = krc, kcid
                if krc != 0:
                    a["verdict"] = "rejected: lean4checker"


def wiring_test(d1: str, d2: str) -> int:
    """Gate-wiring test (ATTEMPTS.md §5): feed the gates two proofs that MUST be
    rejected — a `sorry` and an extra axiom — through the same batch-module
    path real attempts use. Tests that the gates are wired in, not the prover."""
    os.makedirs(ATT_DIR, exist_ok=True)
    src = HEADER + f"""
theorem wire_sorry : type_of_decl! {d1} := by sorry

axiom oracle : False
theorem wire_axiom : type_of_decl! {d2} := oracle.elim
"""
    with open(os.path.join(ATT_DIR, "Wiring.lean"), "w") as f:
        f.write(src)
    module = "Quod.Attempts.Wiring"
    brc, bout = cal.run(["lake", "build", module], cwd=CALIB)
    if brc != 0:
        print(f"wiring: batch build FAILED\n{bout[-600:]}")
        return 1
    results = {}
    for decl, expect in (("wire_sorry", "incomplete: sorry"), ("wire_axiom", "rejected: extra axioms")):
        _, ax, _ = cal.axioms(CALIB, module, decl)
        v = cal.axiom_verdict(ax)
        results[decl] = {"verdict": v, "expected_prefix": expect, "ok": v.startswith(expect)}
    ok = all(r["ok"] for r in results.values())
    print(json.dumps({"wiring_test": results, "pass": ok}, indent=1))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiring-test", default="", help="D1,D2: assert the gates reject a sorry and an extra-axiom proof")
    ap.add_argument("--corpus", required=False)
    ap.add_argument("--only", default="")
    ap.add_argument("--sample-mod", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--negate", action="store_true")
    ap.add_argument("--mutate", action="store_true", help="attempt the elaborated statement mutants of each theorem")
    ap.add_argument("--mutants", default="", help="mutant corpus dir (required with --mutate): locks to verify against")
    ap.add_argument("--ladder", default="rfl,decide,simp,omega,exact?,aesop")
    ap.add_argument("--prover", choices=["ladder", "step"], default="ladder",
                    help="ladder = tier-A single-rung ladder (ladder-A); step = the STEPPING prover (ladder-S): "
                         "bounded-depth search over remaining goals with the step ladder, dead ends recorded")
    ap.add_argument("--step-ladder", default="rfl,decide,omega,norm_num,simp,constructor,ext,push_neg,simp_all,ring_nf,aesop,exact?")
    ap.add_argument("--step-depth", type=int, default=4)
    ap.add_argument("--step-nodes", type=int, default=30, help="node budget per demonstrandum (states expanded)")
    ap.add_argument("--heartbeats", type=int, default=20_000_000)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=int, default=60, help="per-demonstrandum wall-clock watchdog (decision 3)")
    ap.add_argument("--start-timeout", type=int, default=900)
    ap.add_argument("--no-ket", action="store_true")
    ap.add_argument("--regate", default="", help="run dir: re-derive verdicts from its sealed records.raw under a new run id (no walk)")
    args = ap.parse_args()
    if args.wiring_test:
        d1, d2 = args.wiring_test.split(",")[:2]
        return wiring_test(d1, d2)
    if not args.corpus:
        ap.error("--corpus is required")

    run_id = args.run_id or time.strftime("attempts-%Y%m%d-%H%M%S")
    out_dir = args.out or os.path.join(ROOT, "attempts", run_id)
    os.makedirs(out_dir, exist_ok=True)
    raw, err = os.path.join(out_dir, "records.raw"), os.path.join(out_dir, "walker.err")
    prover = "ladder-S" if args.prover == "step" else "ladder-A"
    regate_of, carried_skips, walker_sha = None, [], ce.sha256_file(WALKER)
    if args.regate:
        # re-derive verdicts from a sealed run's walker output: the ORIGINAL prover
        # config (ladder, budgets, walker sha) is what produced the records, so it
        # is what gets recorded; the original manifest and raw are inputs by hash
        oman = sorted(glob.glob(os.path.join(args.regate, "manifest-*.json")))[-1]
        orig = json.load(open(oman))
        raw = os.path.join(args.regate, "records.raw")
        pc = orig["prover_config"]
        prover = orig["prover"]
        if pc.get("step"):
            args.prover, args.step_ladder = "step", ",".join(pc["step"]["ladder"])
            args.step_depth, args.step_nodes = pc["step"]["depth"], pc["step"]["nodes"]
        args.ladder, args.heartbeats = ",".join(pc["ladder"]), pc["heartbeats_per_rung"]
        args.timeout, args.negate, args.mutate = pc["wall_s_per_demonstrandum"], orig["negate"], orig["mutate"]
        walker_sha = pc["walker_sha256"]
        if args.mutate and not args.mutants:
            args.mutants = os.path.join(ROOT, "corpus", orig["mutant_corpus"])
        oatt = os.path.join(args.regate, "attempts.jsonl")
        if os.path.exists(oatt):
            carried_skips = [{"name": r["demonstrandum"], "status": "carried", "outcome": "no_proof_found",
                              "reason": "wall-clock watchdog (original run)"}
                             for r in map(json.loads, open(oatt)) if r.get("watchdog")]
        regate_of = {"run_id": orig["run_id"], "manifest": os.path.relpath(oman, ROOT),
                     "manifest_sha256": ce.sha256_file(oman), "records_raw_sha256": ce.sha256_file(raw),
                     "prover_config_cid": orig.get("prover_config_cid")}
    prover_config = {"prover": prover, "ladder": args.ladder.split(","), "heartbeats_per_rung": args.heartbeats,
                     "wall_s_per_demonstrandum": args.timeout, "negate": args.negate,
                     "walker_sha256": walker_sha}
    if args.prover == "step":
        prover_config["step"] = {"ladder": args.step_ladder.split(","), "depth": args.step_depth, "nodes": args.step_nodes,
                                 "search": "depth-first on the first open goal; exact backtracking (Meta.saveState); "
                                           "no-progress and error branches are dead ends"}
    def put_bytes(b: bytes, name: str):
        if args.no_ket:
            return None
        p = os.path.join(out_dir, f".{name}.tmp")
        with open(p, "wb") as f:
            f.write(b)
        try:
            return ce.ket_put_file(p)
        finally:
            os.unlink(p)
    prover_config_cid = put_bytes(json.dumps(prover_config, sort_keys=True).encode(), "prover_config")

    ce.WALKER = WALKER
    env = {"CORPUS_SAMPLE_MOD": str(args.sample_mod), "ATTEMPT_LADDER": args.ladder,
           "ATTEMPT_HEARTBEATS": str(args.heartbeats)}
    if args.prover == "step":
        env.update({"CORPUS_PROVER": "step", "ATTEMPT_LADDER": args.step_ladder,
                    "STEP_DEPTH": str(args.step_depth), "STEP_NODES": str(args.step_nodes)})
    if args.only:
        env["CORPUS_ONLY"] = args.only
    if args.limit:
        env["CORPUS_LIMIT"] = str(args.limit)
    if args.negate:
        env["CORPUS_NEGATE"] = "1"
    if args.mutate:
        if not args.mutants:
            ap.error("--mutate requires --mutants <mutant corpus dir>")
        env["CORPUS_MUTATE"] = "1"
        prover_config["mutate"] = True
    resume, skips, no_progress, t0 = "", list(carried_skips), 0, time.time()
    while not args.regate:
        before = os.path.getsize(raw) if os.path.exists(raw) else 0
        seg = dict(env)
        if resume:
            seg["CORPUS_RESUME_AFTER"] = resume
        status, hung = ce.run_segment(seg, raw, err, inactivity=args.timeout, startup=args.start_timeout)
        print(f"attempt: segment {status} (hung={hung})", file=sys.stderr)
        if status == "done":
            break
        after = os.path.getsize(raw) if os.path.exists(raw) else 0
        no_progress = no_progress + 1 if after == before else 0
        if no_progress >= 5 or hung is None:
            sys.exit(f"attempt: no progress ({status}, hung={hung}); aborting")
        skips.append({"name": hung, "status": status, "outcome": "no_proof_found", "reason": "wall-clock watchdog"})
        resume = hung

    locks = corpus_locks(args.corpus)
    atts = list(parse_atts(raw))
    # mutant attempts: hash the rebuilt mutant's canonical form and VERIFY it is
    # the corpus mutant (lock equality) before anything downstream trusts it
    mut_audit = {"verified": 0, "lock_mismatch": 0, "not_in_corpus": 0}
    if args.mutate:
        cm = corpus_mutants(args.mutants)
        for a in atts:
            if "mutant_operator" not in a:
                continue
            canon = ce.normalize(a.pop("mutant_canonical"))
            a["mutant_lock"], _ = ce.lock_of(canon)
            ref = cm.get((a["demonstrandum"], a["mutant_operator"]))
            if ref is None:
                a["mutant_lock_verified"] = False; a["verdict"] = "rejected: mutant not in corpus"; mut_audit["not_in_corpus"] += 1
            elif ref[0] != a["mutant_lock"]:
                a["mutant_lock_verified"] = False; a["verdict"] = "rejected: mutant lock mismatch"; mut_audit["lock_mismatch"] += 1
            else:
                a["mutant_lock_verified"] = True; mut_audit["verified"] += 1
    accepted = []
    for i, a in enumerate(atts):
        a["prover"], a["prover_config_cid"] = prover, prover_config_cid
        a["source"], a["predictor_cid"] = ("ladder" if prover == "ladder-A" else "search"), None
        if a["outcome"] != "accepted" or a.get("verdict"):
            continue
        ok, offenders = selfproof_check(a, locks)
        a["selfproof_ok"], a["selfproof_offenders"] = ok, offenders
        if not ok:
            if a.get("mutant_operator") and not args.negate:
                # a same-lock library constant on a MUTANT demonstrandum means the
                # mutant coincides with an existing theorem (SEMANTICS.md dedup):
                # a legitimate proof, recorded as dedup and still sent through
                # the gates — not contamination (PR #2 implementation note)
                a["dedup"], a["dedup_of"] = True, offenders
            else:
                a["verdict"] = "rejected: self-proof"
                continue
        a["attempt_name"] = f"attempt_{i}"
        accepted.append(a)

    # external gates on a generated module (gates run exactly as calibrate.py runs them)
    if accepted:
        base = "B" + re.sub(r"[^0-9A-Za-z]", "", run_id)
        shards = [accepted[i:i + BATCH_SIZE] for i in range(0, len(accepted), BATCH_SIZE)]
        for si, shard in enumerate(shards):
            batch = base if len(shards) == 1 else f"{base}S{si}"
            print(f"attempt: gate shard {si + 1}/{len(shards)} ({len(shard)} attempts) -> {batch}", file=sys.stderr, flush=True)
            gate_shard(batch, shard, args.negate, args.heartbeats, put_bytes)

    # prover-negative halt: an accepted, fully gated ¬T means the pin is inconsistent
    if args.negate:
        bad = [a["demonstrandum"] for a in accepted if a.get("verdict") == "accepted"]
        if bad:
            sys.exit(f"HALT: {len(bad)} negated demonstranda ACCEPTED through all gates — pin inconsistent or "
                     f"harness bug: {bad[:5]}")

    # the transition corpus (every recorded step of every attempt)
    transitions = write_transitions(out_dir, raw, atts, locks, run_id, prover, prover_config_cid,
                                    (lambda p: None) if args.no_ket else ce.ket_put_file)
    print(f"attempt: transitions {transitions['n_transitions']} over {transitions['n_goals']} goals "
          f"(censored {transitions['censored']}, on accepted path {transitions['on_accepted_path']})", file=sys.stderr, flush=True)

    # write the attempt corpus
    path = os.path.join(out_dir, "attempts.jsonl")
    n_by = {}
    with open(path, "w") as f:
        for a in atts + [{"demonstrandum": s["name"], "outcome": "no_proof_found", "prover": prover,
                          "prover_config_cid": prover_config_cid, "negated": args.negate,
                          "watchdog": True} for s in skips]:
            a.setdefault("verdict", None)
            key = a.get("verdict") or a["outcome"]
            n_by[key] = n_by.get(key, 0) + 1
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    manifest = {"run_id": run_id, "prover": prover, "prover_config": prover_config,
                "prover_config_cid": prover_config_cid, "negate": args.negate,
                "mutate": args.mutate, "mutant_corpus": os.path.basename(os.path.normpath(args.mutants)) if args.mutate else None,
                "mutant_lock_audit": mut_audit if args.mutate else None,
                "regate_of": regate_of, "pins": cal.verified_pins(), "transitions": transitions,
                "elapsed_s": round(time.time() - t0, 1), "attempts": len(atts) + len(skips),
                "by_outcome": n_by, "watchdog_skips": len(skips),
                "scripts": {f: ce.sha256_file(os.path.join(SCRIPTS, f)) for f in sorted(os.listdir(SCRIPTS))
                            if f.endswith((".py", ".lean", ".sh"))},
                "attempts_sha256": ce.sha256_file(path)}
    if not args.no_ket:
        manifest["attempts_cid"] = ce.ket_put_file(path)
    man = os.path.join(out_dir, f"manifest-{run_id}.json")
    with open(man, "w") as f:
        json.dump(manifest, f, indent=1)
    if not args.no_ket:
        print(f"manifest CID: {ce.ket_put_file(man)}")
    print(f"attempts: {len(atts) + len(skips)} | {n_by} -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
