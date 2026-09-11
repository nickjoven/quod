#!/usr/bin/env python3
"""mutant_extract.py --corpus <declarations corpus dir> [--sample-mod N]
                     [--limit N] [--out DIR] [--run-id ID] [--no-ket]
                     [--timeout S] [--start-timeout S]

Phase-3 mutant corpus driver: runs scripts/MutantWalk.lean under the same
watchdog / resume / explicit-file-output machinery as corpus_extract.py
(imported from it), then labels every mutant in Python:
  lock            BLAKE3 of the normalized mutated canonical form (lock.py rules)
  parent_lock     from the declarations corpus, by parent name
  lock_changed    lock != parent_lock
  elaborates      from Lean (Meta.isTypeCorrect, budgeted)
  gate_verdict    fixed-by-construction for proof-side mutants; null for
                  statement mutants (Phase-3b: sampled proof attempts)
Shards to mutants-NNNN.jsonl with an append-only manifest (CIDs when ket on).
"""
import argparse, glob, hashlib, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_extract as ce  # noqa: E402

ROOT, CALIB, SCRIPTS = ce.ROOT, ce.CALIB, ce.SCRIPTS
WALKER = os.path.join(SCRIPTS, "MutantWalk.lean")


def parent_locks(corpus_dir: str) -> dict[str, str]:
    locks = {}
    for path in sorted(glob.glob(os.path.join(corpus_dir, "declarations-*.jsonl"))):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                locks[r["name"]] = r["lock"]
    return locks


def parse_muts(raw_path: str):
    with open(raw_path, errors="replace") as f:
        for line in f:
            if line.startswith("MUT\t"):
                try:
                    yield json.loads(line[4:])
                except json.JSONDecodeError:
                    continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="declarations corpus dir (for parent locks)")
    ap.add_argument("--sample-mod", type=int, default=46)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--shard-size", type=int, default=10_000)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--start-timeout", type=int, default=600)
    ap.add_argument("--no-ket", action="store_true")
    args = ap.parse_args()

    run_id = args.run_id or time.strftime("mutants-%Y%m%d-%H%M%S")
    out_dir = args.out or os.path.join(ROOT, "corpus", run_id)
    os.makedirs(out_dir, exist_ok=True)
    raw, err = os.path.join(out_dir, "records.raw"), os.path.join(out_dir, "walker.err")

    # corpus_extract.run_segment launches WALKER = CorpusWalk; point it at ours.
    ce.WALKER = WALKER
    resume = ""
    if os.path.exists(raw):
        last = None
        with open(raw, errors="replace") as f:
            for line in f:
                if line.startswith("START\t"):
                    last = line[6:].strip()
        if last:
            resume = last
            print(f"mutant-extract: resuming after {last}", file=sys.stderr)
    env = {"CORPUS_SAMPLE_MOD": str(args.sample_mod)}
    if args.limit:
        env["CORPUS_LIMIT"] = str(args.limit)
    skips, t0, no_progress = [], time.time(), 0
    while True:
        before = os.path.getsize(raw) if os.path.exists(raw) else 0
        seg = dict(env)
        if resume:
            seg["CORPUS_RESUME_AFTER"] = resume
        status, hung = ce.run_segment(seg, raw, err, inactivity=args.timeout, startup=args.start_timeout)
        print(f"mutant-extract: segment {status} (hung={hung})", file=sys.stderr)
        if status == "done":
            break
        after = os.path.getsize(raw) if os.path.exists(raw) else 0
        no_progress = no_progress + 1 if after == before else 0
        if no_progress >= 5 or hung is None:
            sys.exit(f"mutant-extract: no progress ({status}, hung={hung}); aborting")
        skips.append({"name": hung, "status": status})
        resume = hung

    plocks = parent_locks(args.corpus)
    shards, count, shard_f, ops = [], 0, None, {}
    for m in parse_muts(raw):
        canon = ce.normalize(m["mutated_canonical"])
        lock, algo = ce.lock_of(canon)
        rec = {"parent": m["parent"], "module": m["module"], "operator": m["operator"],
               "mutated_canonical": canon, "mutated_readable": m["mutated_readable"],
               "lock": lock, "hash_algo": algo, "parent_lock": plocks.get(m["parent"]),
               "lock_changed": plocks.get(m["parent"]) != lock,
               "elaborates": m["elaborates"], "gate_verdict": m["gate_verdict"]}
        ops[m["operator"]] = ops.get(m["operator"], 0) + 1
        if count % args.shard_size == 0:
            if shard_f:
                shard_f.close()
            path = os.path.join(out_dir, f"mutants-{count // args.shard_size:04d}.jsonl")
            shards.append(path)
            shard_f = open(path, "w")
        shard_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        count += 1
    if shard_f:
        shard_f.close()

    manifest = {
        "run_id": run_id, "elapsed_s": round(time.time() - t0, 1), "records": count,
        "operators": ops, "skipped": skips, "sample_mod": args.sample_mod,
        "parent_corpus": os.path.basename(os.path.normpath(args.corpus)),
        "scripts": {f: ce.sha256_file(os.path.join(SCRIPTS, f)) for f in sorted(os.listdir(SCRIPTS))
                    if f.endswith((".py", ".lean", ".sh"))},
        "shards": [],
    }
    for path in shards:
        entry = {"file": os.path.basename(path), "records": sum(1 for _ in open(path)),
                 "sha256": ce.sha256_file(path)}
        if not args.no_ket:
            entry["cid"] = ce.ket_put_file(path)
        manifest["shards"].append(entry)
    man_path = os.path.join(out_dir, f"manifest-{run_id}.json")
    with open(man_path, "w") as f:
        json.dump(manifest, f, indent=1)
    if not args.no_ket:
        print(f"manifest CID: {ce.ket_put_file(man_path)}")
    print(f"extracted {count} mutants ({len(skips)} skipped) ops={ops} -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
