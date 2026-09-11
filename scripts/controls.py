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
import argparse, glob, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--pilot", type=int, default=50)
    ap.add_argument("--test", type=int, default=200)
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
    pilot, test = ordered[:args.pilot], ordered[args.pilot:args.pilot + args.test]
    manifests = sorted(glob.glob(os.path.join(args.corpus, "manifest-*.json")))
    out = {"rule": f"blake2b('{args.seed}:'+name) ascending over kind==theorem; first {args.pilot} pilot, next {args.test} test",
           "seed": args.seed, "corpus_manifest": os.path.basename(manifests[0]) if manifests else None,
           "theorems_in_corpus": len(names), "pilot": pilot, "test": test}
    os.makedirs(os.path.join(ROOT, "attempts"), exist_ok=True)
    p = os.path.join(ROOT, "attempts", f"controls-{args.seed}.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    print(f"controls: {len(pilot)} pilot + {len(test)} test from {len(names)} theorems -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
