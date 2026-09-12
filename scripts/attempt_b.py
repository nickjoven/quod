#!/usr/bin/env python3
"""attempt_b.py — tier B: a gate-verified LLM prover, batch-round protocol (ATTEMPTS.md rev 2 tier B).

  python3 scripts/attempt_b.py --controls attempts/controls-1337.json --which pilot
      --corpus corpus/full-20260908b --run-id pilot-B --model claude-opus-5
      --rounds 16 --cap-cents 6000 [--dry-run] [--no-ket]

Protocol (one run gives every prefix level):
  * round r = one Message Batch over the still-open demonstranda; each request
    carries the statement (name HIDDEN — the prover gets the proposition, not a
    pointer to its Mathlib proof), every earlier proposal and the Lean error it
    produced. Static system prefix under one cache_control breakpoint.
  * every proposal is replayed STEPWISE by AttemptWalk (CORPUS_SCRIPTS mode):
    per-tactic transitions (source=search, prover=tier-B, prover_config_cid,
    heartbeat_cap) and the first failing step's error for the next round.
  * a script that closes the goal goes through the UNCHANGED gates: kernel
    addDecl (walker), self-proof (name or same-lock constant -> rejected and
    counted as a failure for P), generated module, axiom triple, independent
    lean4checker. A demonstrandum drops out at its first gate-accepted proof;
    the round index of that proof gives P_B(1), P_B(4), P_B(16).
  * spend is tracked from `usage` on every batch result at the recorded prices;
    the driver halts BEFORE a round whose projected cost would cross the cap.
  * `stop_reason: refusal` is a recorded outcome. Credentials come only from
    ANTHROPIC_API_KEY in the environment; nothing here prints or stores it.
Manifest BEFORE the run (sealed): model, created_at (Models API), effort, cap,
levels, set CID, prompt CID, prices, runner sha256s. AFTER: P_B per level on
all demonstranda and on the tier-A-failed subset, spend in cents, refusals,
self-proof rejections, transition count.
"""
from __future__ import annotations

import argparse, glob, hashlib, json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_extract as ce   # noqa: E402
import calibrate as cal       # noqa: E402
import attempt as at          # noqa: E402  (selfproof_check, gate_shard, write_transitions, corpus_locks, parse_tagged)

ROOT, CALIB, SCRIPTS = ce.ROOT, ce.CALIB, ce.SCRIPTS
WALKER = os.path.join(SCRIPTS, "AttemptWalk.lean")
LEVELS = (1, 4, 16)

SYSTEM_PREFIX = """You are a Lean 4 proof assistant working against a FIXED pin: Lean 4 v4.28.0 with Mathlib at commit 8f9d9cff6bd728b17a24e163c9402775d9e6a365 (2026). Every theorem you are shown is stated exactly as it elaborates at that pin; `import Mathlib` is in scope and nothing else.

Rules:
1. Reply with ONLY the tactic proof — the body that follows `by` — as a single ```lean fenced block. No prose, no `theorem` header, no `by` keyword, no comments after the block.
2. The theorem's own name is hidden and unavailable. Do not use the search tactics `exact?`, `apply?`, `rw?`, `simp?`, `aesop?`, `hint`, `decide`-free `omega?` or anything that queries the library for a closing lemma: a proof that merely locates the library's copy of this statement is rejected as a self-proof. Cite specific Mathlib lemmas by name when you know them.
3. No `sorry`, no `admit`, no new axioms, no `native_decide`, no `unsafe`.
4. Start by introducing the binders (`intro` / `intros` / `rintro`); the goal is presented as a closed ∀-statement.
5. If an earlier proposal failed, you are shown the exact Lean error and the step it failed at; fix that step or change approach. Each reply must be a complete proof script, not a diff.
"""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_statements(corpus: str, names: set[str]) -> dict[str, dict]:
    out = {}
    for path in sorted(glob.glob(os.path.join(corpus, "declarations-*.jsonl"))):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r["name"] in names:
                    out[r["name"]] = r
    return out


def extract_script(text: str) -> str:
    m = re.search(r"```(?:lean4?|Lean)?\s*\n(.*?)```", text, re.S)
    body = m.group(1) if m else text
    lines = [l.rstrip() for l in body.strip("\n").splitlines()]
    if lines and re.match(r"^\s*by\s*$", lines[0]):
        lines = lines[1:]
    if lines and re.match(r"^\s*theorem\b", lines[0]):
        lines = lines[1:]
    # dedent uniformly
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[ind:] for l in lines).strip("\n")


def build_user_message(stmt: str, history: list[dict]) -> str:
    parts = [f"Prove this theorem at the pin. Reply with only the tactic block.\n\n```lean\ntheorem X : {stmt}\n```"]
    for h in history:
        parts.append(f"\n--- Round {h['round']} proposal ---\n```lean\n{h['script']}\n```\n"
                     f"Lean result: step {h['error_step']} ({h['err_class']}): {h['err']}")
    if history:
        parts.append("\nGive a corrected complete proof script.")
    return "\n".join(parts)


def run_walker_scripts(scripts_path: str, raw_path: str, err_path: str, heartbeats: int, timeout: int, startup: int):
    """One walker pass in CORPUS_SCRIPTS mode (file polling watchdog as the other runs)."""
    env = {"CORPUS_SCRIPTS": scripts_path, "ATTEMPT_HEARTBEATS": str(heartbeats)}
    ce.WALKER = WALKER
    status, hung = ce.run_segment(env, raw_path, err_path, inactivity=timeout, startup=startup)
    return status, hung


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", required=True)
    ap.add_argument("--which", choices=["pilot", "test"], default="pilot")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--tier-a-run", default=os.path.join(ROOT, "attempts", "pilot-A"),
                    help="tier-A run dir on the same set (for the tier-A-failed subset)")
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--rounds", type=int, default=16)
    ap.add_argument("--cap-cents", type=int, default=6000)
    ap.add_argument("--price-in", type=float, required=True, help="USD per Mtok input (batch rate) — recorded")
    ap.add_argument("--price-out", type=float, required=True, help="USD per Mtok output (batch rate) — recorded")
    ap.add_argument("--price-cache-write", type=float, default=None, help="USD per Mtok cache write (default 1.25x input)")
    ap.add_argument("--price-cache-read", type=float, default=None, help="USD per Mtok cache read (default 0.1x input)")
    ap.add_argument("--heartbeats", type=int, default=20_000_000)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--start-timeout", type=int, default=900)
    ap.add_argument("--poll", type=int, default=30)
    ap.add_argument("--no-ket", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="build the pre-manifest and round-1 requests; submit nothing")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    pin = args.price_in
    p_cw = args.price_cache_write if args.price_cache_write is not None else 1.25 * pin
    p_cr = args.price_cache_read if args.price_cache_read is not None else 0.10 * pin

    out_dir = args.out or os.path.join(ROOT, "attempts", args.run_id)
    os.makedirs(out_dir, exist_ok=True)

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

    # ---- the set, the statements, the tier-A baseline on the same set
    controls = json.load(open(args.controls))
    names = list(controls[args.which])
    stmts = load_statements(args.corpus, set(names))
    missing = [n for n in names if n not in stmts]
    if missing:
        sys.exit(f"{len(missing)} names not in the corpus: {missing[:3]}")
    tier_a_failed = set()
    ta = os.path.join(args.tier_a_run, "attempts.jsonl")
    if os.path.exists(ta):
        tier_a_failed = {a["demonstrandum"] for a in map(json.loads, open(ta)) if a.get("verdict") != "accepted"} & set(names)
    locks = at.corpus_locks(args.corpus)

    # ---- credentials + model identity (never printed)
    key_ok = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not key_ok and not args.dry_run:
        sys.exit("ANTHROPIC_API_KEY is not set in this environment; stopping (no key search).")
    client, created_at = None, None
    if key_ok:
        import anthropic
        client = anthropic.Anthropic()
        try:
            mi = client.models.retrieve(args.model)
            created_at = str(getattr(mi, "created_at", None))
        except Exception as e:  # noqa: BLE001
            if not args.dry_run:
                sys.exit(f"Models API lookup failed for {args.model}: {type(e).__name__}")
            created_at = f"lookup failed: {type(e).__name__}"

    prover = "tier-B"
    prover_config = {"prover": prover, "model": args.model, "model_created_at": created_at, "effort": args.effort,
                     "max_tokens": args.max_tokens, "rounds": args.rounds, "levels": list(LEVELS),
                     "protocol": "one batch per round over open demonstranda; full history of proposals + Lean errors; "
                                 "drop at first gate-accepted proof; stepwise replay via AttemptWalk CORPUS_SCRIPTS",
                     "system_prompt_sha256": sha256_bytes(SYSTEM_PREFIX.encode()),
                     "heartbeats_per_step": args.heartbeats, "walker_sha256": ce.sha256_file(WALKER),
                     "forbidden_tactics": ["exact?", "apply?", "rw?", "simp?", "aesop?", "hint", "sorry", "admit", "native_decide"],
                     "self_proof_gate": "name hidden; any accepted term using the demonstrandum's name or a same-lock constant is rejected: self-proof and counts as a failure for P"}
    prover_config_cid = put_bytes(json.dumps(prover_config, sort_keys=True).encode(), "prover_config")
    prompt_cid = put_bytes(SYSTEM_PREFIX.encode(), "system_prompt")
    set_cid = None if args.no_ket else ce.ket_put_file(args.controls)
    pre = {"run_id": args.run_id, "prover": prover, "prover_config": prover_config, "prover_config_cid": prover_config_cid,
           "cap_cents": args.cap_cents, "prices_usd_per_mtok": {"input": pin, "output": args.price_out, "cache_write": p_cw, "cache_read": p_cr},
           "set": {"controls": os.path.relpath(args.controls, ROOT), "which": args.which, "n": len(names),
                   "sha256": ce.sha256_file(args.controls), "cid": set_cid},
           "tier_a_failed_subset": sorted(tier_a_failed), "prompt_cid": prompt_cid, "pins": cal.verified_pins(),
           "scripts": {f: ce.sha256_file(os.path.join(SCRIPTS, f)) for f in sorted(os.listdir(SCRIPTS)) if f.endswith((".py", ".lean", ".sh"))},
           "sealed_before_run": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    pre_path = os.path.join(out_dir, f"manifest-pre-{args.run_id}.json")
    with open(pre_path, "w") as f:
        json.dump(pre, f, indent=1)
    pre_cid = None if args.no_ket else ce.ket_put_file(pre_path)
    print(f"pre-manifest sealed: {pre_path} CID {pre_cid} | set {len(names)} ({len(tier_a_failed)} tier-A-failed) | "
          f"model {args.model} created_at {created_at} | cap {args.cap_cents}c", file=sys.stderr, flush=True)

    # ---- state
    state = {n: {"history": [], "accepted_round": None, "verdict": None, "refusals": 0} for n in names}
    spent_cents = 0.0
    round_costs: list[float] = []
    usage_total = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    att_rows: list[dict] = []
    trans_sections = []
    refusals = selfproof_rejections = 0
    t0 = time.time()

    def round_requests(r: int, open_names: list[str]):
        reqs = []
        for i, n in enumerate(open_names):
            stmt = stmts[n].get("readable_pp") or stmts[n]["canonical_type"]
            params = {"model": args.model, "max_tokens": args.max_tokens,
                      "system": [{"type": "text", "text": SYSTEM_PREFIX, "cache_control": {"type": "ephemeral"}}],
                      "messages": [{"role": "user", "content": build_user_message(stmt, state[n]["history"])}]}
            if args.effort:
                params["output_config"] = {"effort": args.effort}
            reqs.append({"custom_id": f"{i}", "params": params})
        return reqs

    if args.dry_run:
        reqs = round_requests(1, names)
        est_in = sum(len(json.dumps(q["params"]["messages"])) // 4 for q in reqs) + len(SYSTEM_PREFIX) // 4
        est = (est_in * pin + len(reqs) * 1500 * args.price_out) / 1e6 * 100
        print(json.dumps({"dry_run": True, "round1_requests": len(reqs), "est_round1_input_tokens": est_in,
                          "est_round1_cents_at_1500_out_tokens_each": round(est, 1),
                          "sample_user_message": reqs[0]["params"]["messages"][0]["content"][:600]}, indent=1))
        return 0

    for r in range(1, args.rounds + 1):
        open_names = [n for n in names if state[n]["accepted_round"] is None]
        if not open_names:
            break
        # projected cost of this round: last round's per-request cost x requests x 1.2 (history grows)
        if round_costs:
            per_req = round_costs[-1][0] / max(round_costs[-1][1], 1)
            projected = spent_cents + per_req * len(open_names) * 1.2
            if projected > args.cap_cents:
                print(f"HALT before round {r}: projected {projected:.0f}c > cap {args.cap_cents}c", file=sys.stderr, flush=True)
                break
        reqs = round_requests(r, open_names)
        batch = client.messages.batches.create(requests=reqs)
        print(f"round {r}: batch {batch.id} over {len(reqs)} open demonstranda", file=sys.stderr, flush=True)
        while True:
            b = client.messages.batches.retrieve(batch.id)
            if b.processing_status == "ended":
                break
            time.sleep(args.poll)
        proposals, round_cost, n_req = [], 0.0, 0
        for res in client.messages.batches.results(batch.id):
            i = int(res.custom_id); n = open_names[i]
            n_req += 1
            rec = {"round": r, "demonstrandum": n, "batch_id": batch.id, "result_type": res.result.type}
            if res.result.type != "succeeded":
                rec["error"] = str(getattr(res.result, "error", ""))[:300]
                att_rows.append({**rec, "outcome": "no_proposal"})
                continue
            msg = res.result.message
            u = msg.usage
            cw = getattr(u, "cache_creation_input_tokens", 0) or 0
            cr = getattr(u, "cache_read_input_tokens", 0) or 0
            usage_total["input"] += u.input_tokens; usage_total["output"] += u.output_tokens
            usage_total["cache_write"] += cw; usage_total["cache_read"] += cr
            cost = (u.input_tokens * pin + u.output_tokens * args.price_out + cw * p_cw + cr * p_cr) / 1e6 * 100
            round_cost += cost
            rec.update({"stop_reason": msg.stop_reason, "usage": {"input": u.input_tokens, "output": u.output_tokens, "cache_write": cw, "cache_read": cr}, "cost_cents": round(cost, 3)})
            if msg.stop_reason == "refusal":
                refusals += 1; state[n]["refusals"] += 1
                att_rows.append({**rec, "outcome": "refusal"})
                state[n]["history"].append({"round": r, "script": "<refused>", "error_step": 0, "err_class": "refusal", "err": "the model declined to answer"})
                continue
            text = "".join(getattr(c, "text", "") for c in msg.content)
            script = extract_script(text)
            rec["script"] = script
            proposals.append({"id": f"{r}:{i}", "name": n, "script": script, "rec": rec})
        spent_cents += round_cost
        round_costs.append((round_cost, n_req))
        print(f"round {r}: {len(proposals)} proposals, {round_cost:.1f}c this round, {spent_cents:.1f}c total", file=sys.stderr, flush=True)
        if not proposals:
            continue
        # ---- stepwise replay + gates
        sp = os.path.join(out_dir, f"scripts-r{r}.jsonl")
        with open(sp, "w") as f:
            for p in proposals:
                f.write(json.dumps({"id": p["id"], "name": p["name"], "script": p["script"]}, ensure_ascii=False) + "\n")
        raw = os.path.join(out_dir, f"records-r{r}.raw"); err = os.path.join(out_dir, f"walker-r{r}.err")
        status, hung = run_walker_scripts(sp, raw, err, args.heartbeats, args.timeout, args.start_timeout)
        atts = {j["script_id"]: j for j in at.parse_atts(raw)}
        accepted = []
        for k, p in enumerate(proposals):
            a = atts.get(p["id"])
            rec = p["rec"]
            n = p["name"]
            if a is None:
                rec.update({"outcome": "no_proof_found", "err_class": "walker", "err": f"walker {status} (no record)"})
                state[n]["history"].append({"round": r, "script": p["script"], "error_step": 0, "err_class": "walker", "err": "the checker timed out on this script"})
                att_rows.append(rec); continue
            rec.update({kk: a.get(kk) for kk in ("outcome", "error_step", "err_class", "err", "script_steps", "steps_run", "aid", "used_consts", "axioms", "kernel_ok", "tactic")})
            rec["n_levels"] = a.get("n_levels", 0)
            if a["outcome"] != "accepted":
                state[n]["history"].append({"round": r, "script": p["script"], "error_step": a.get("error_step"), "err_class": a.get("err_class"), "err": (a.get("err") or "")[:1200]})
                att_rows.append(rec); continue
            ok, offenders = at.selfproof_check({"demonstrandum": n, "used_consts": a.get("used_consts", [])}, locks)
            rec["selfproof_ok"], rec["selfproof_offenders"] = ok, offenders
            if not ok:
                selfproof_rejections += 1
                rec["verdict"] = "rejected: self-proof"
                state[n]["history"].append({"round": r, "script": p["script"], "error_step": 0, "err_class": "self-proof",
                                            "err": f"rejected: the proof term uses the theorem itself or an equivalent library statement ({', '.join(offenders[:3])}); prove it from more basic lemmas"})
                att_rows.append(rec); continue
            rec["attempt_name"] = f"attempt_r{r}_{k}"; rec["demonstrandum"] = n
            accepted.append(rec)
        if accepted:
            batch_name = "B" + re.sub(r"[^0-9A-Za-z]", "", f"{args.run_id}r{r}")
            at.gate_shard(batch_name, accepted, False, args.heartbeats, put_bytes)
        for rec in accepted:
            n = rec["demonstrandum"]
            if rec.get("verdict") == "accepted":
                state[n]["accepted_round"] = r; state[n]["verdict"] = "accepted"
            else:
                state[n]["history"].append({"round": r, "script": rec["script"], "error_step": 0, "err_class": "gate", "err": f"external gate: {rec.get('verdict')} {(rec.get('build_err') or '')[:400]}"})
            att_rows.append(rec)
        # transitions of this round (aid restarts per walker pass, so per-round sections)
        for a in atts.values():
            a["demonstrandum"] = a["demonstrandum"]
        trans = at.write_transitions(os.path.join(out_dir, f"r{r}"), raw, list(atts.values()), locks, f"{args.run_id}-r{r}", prover, prover_config_cid,
                                     (lambda p: None) if args.no_ket else ce.ket_put_file)
        trans_sections.append({"round": r, **trans})
        print(f"round {r}: accepted so far {sum(1 for n in names if state[n]['accepted_round'])}/{len(names)}; transitions {trans['n_transitions']}", file=sys.stderr, flush=True)

    # ---- P_B per level (prefixes of the one run)
    def p_at(level, subset):
        return round(sum(1 for n in subset if state[n]["accepted_round"] and state[n]["accepted_round"] <= level) / max(len(subset), 1), 4)
    P = {f"P_B({L})": {"all": p_at(L, names), "tier_a_failed": p_at(L, sorted(tier_a_failed)) if tier_a_failed else None} for L in LEVELS}
    path = os.path.join(out_dir, "attempts.jsonl")
    with open(path, "w") as f:
        for rec in att_rows:
            rec.setdefault("prover", prover); rec.setdefault("prover_config_cid", prover_config_cid)
            rec.setdefault("source", "search"); rec.setdefault("predictor_cid", None)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    manifest = {**pre, "rounds_run": len(round_costs), "spend_cents": round(spent_cents, 1), "usage": usage_total,
                "round_costs_cents": [round(c, 1) for c, _ in round_costs], "refusals": refusals,
                "selfproof_rejections": selfproof_rejections, "P": P, "frozen": True,
                "accepted": {n: state[n]["accepted_round"] for n in names if state[n]["accepted_round"]},
                "transitions": {"n_transitions": sum(t["n_transitions"] for t in trans_sections), "rounds": trans_sections},
                "attempts_sha256": ce.sha256_file(path), "elapsed_s": round(time.time() - t0, 1)}
    if not args.no_ket:
        manifest["attempts_cid"] = ce.ket_put_file(path)
    man = os.path.join(out_dir, f"manifest-{args.run_id}.json")
    with open(man, "w") as f:
        json.dump(manifest, f, indent=1)
    if not args.no_ket:
        print(f"manifest CID: {ce.ket_put_file(man)}")
    print(f"tier B {args.run_id}: {P} | spend {spent_cents:.1f}c | refusals {refusals} | self-proof {selfproof_rejections}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
