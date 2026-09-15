#!/usr/bin/env python3
"""controls.py --corpus <declarations corpus dir> [--seed N] [--pilot 50] [--test 200]

Nominate the attempt-harness control sets (ATTEMPTS.md §5), as a recorded,
reproducible selection — never a hand-typed list:
  positive  theorems sampled by seeded hash order from the declarations
            corpus (kind == theorem); split into a PILOT set (used once to
            freeze P, decision 2) and a TEST set (the 200), disjoint.
  negative  the same theorems attempted as ¬T (run attempt.py --negate on
            the same names) — no separate nomination needed.
The selection rule and the corpus manifest it was drawn from are written into
attempts/controls-<seed>.json so the nomination is verifiable.
"""
import re, argparse, glob, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--pilot", type=int, default=50)
    ap.add_argument("--test", type=int, default=200)
    ap.add_argument("--frame", type=int, default=0,
                    help="AMENDMENT A1 (Q-26): nominate a test FRAME of this size first, then draw the pilot as a seeded, "
                         "depth-stratified subsample of it (needs --dag); the test set is the frame minus the pilot")
    ap.add_argument("--dag", default="", help="dag_depth.jsonl of the corpus (proof-DAG depth per declaration) for stratification")
    args = ap.parse_args()

    names = []
    for path in sorted(glob.glob(os.path.join(args.corpus, "declarations-*.jsonl"))):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r["kind"] == "theorem":
                    names.append(r["name"])
    # seeded hash order: deterministic, corpus-wide, no human choice
    key = lambda n: hashlib.blake2b(f"{args.seed}:{n}".encode(), digest_size=8).hexdigest()
    ordered = sorted(names, key=key)
    stratified = None
    if args.frame:
        # Amendment A1 (Q-26): frame first, pilot = seeded depth-stratified subsample of it, test = the rest
        import random
        frame = ordered[:args.frame]; fset = set(frame)
        depth, alld = {}, []
        for line in open(args.dag):
            r = json.loads(line)
            if r["depth"] is None:
                continue
            alld.append(r["depth"])
            if r["name"] in fset:
                depth[r["name"]] = r["depth"]
        alld.sort()
        bounds = [alld[int(len(alld) * q)] for q in (0.25, 0.5, 0.75)]
        strat = lambda n: sum(depth.get(n, bounds[1]) > b for b in bounds)
        by = {}
        for n in frame:
            by.setdefault(strat(n), []).append(n)
        rng = random.Random(args.seed)
        pilot = []
        for k in sorted(by):
            take = round(args.pilot * len(by[k]) / len(frame))
            pilot += rng.sample(sorted(by[k]), min(take, len(by[k])))
        pilot = sorted(pilot, key=key)[:args.pilot]; pset = set(pilot)
        test = [n for n in frame if n not in pset]
        stratified = {"frame": len(frame), "depth_quartile_bounds": bounds,
                      "frame_per_quartile": {f"q{k+1}": len(by.get(k, [])) for k in range(4)},
                      "pilot_per_quartile": {f"q{k+1}": sum(1 for n in pilot if strat(n) == k) for k in range(4)},
                      "dag_table": os.path.basename(args.dag),
                      "rule": "frame = first --frame names in seeded hash order; pilot = seeded random subsample of the frame, proportional "
                              "by proof-DAG depth quartile (corpus-wide bounds); test = frame minus pilot (Q-26, amendment A1)"}
    else:
        pilot, test = ordered[:args.pilot], ordered[args.pilot:args.pilot + args.test]
    # the CORPUS manifest (manifest-<run>.json), not a derived table's (manifest-dag-*, manifest-derived-*)
    manifests = sorted(p for p in glob.glob(os.path.join(args.corpus, "manifest-*.json")) if not re.search(r"manifest-(dag|derived)-", p))
    out = {"rule": (f"blake2b('{args.seed}:'+name) ascending over kind==theorem; frame of {args.frame}, stratified pilot of {args.pilot}, test = rest" if args.frame
                    else f"blake2b('{args.seed}:'+name) ascending over kind==theorem; first {args.pilot} pilot, next {args.test} test"),
           "seed": args.seed, "corpus_manifest": os.path.basename(manifests[0]) if manifests else None,
           "theorems_in_corpus": len(names), "pilot": pilot, "test": test, "stratified": stratified}
    os.makedirs(os.path.join(ROOT, "attempts"), exist_ok=True)
    p = os.path.join(ROOT, "attempts", f"controls-{args.seed}.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    print(f"controls: {len(pilot)} pilot + {len(test)} test from {len(names)} theorems -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
