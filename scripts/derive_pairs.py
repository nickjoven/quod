#!/usr/bin/env python3
"""derive_pairs.py <corpus_dir> [--no-ket]

Pure-Python derivations from a declarations corpus (no Lean run):
  iff_pairs.jsonl    records whose head is Iff, with the walker's lhs/rhs
  gloss_pairs.jsonl  records with a docstring: (docstring, canonical_type, lock)

Each output carries the source manifest's run_id; outputs are ket-put and
appended to the manifest as derived artifacts (a new manifest file per
derivation — append-only, never rewritten in place).
"""
import glob, hashlib, json, os, subprocess, sys

KET_HOME = os.environ.get("KET_HOME", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".ket"))


def ket_put_file(path: str) -> str:
    r = subprocess.run(["ket", "--home", KET_HOME, "put", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ket put {path} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    corpus_dir = sys.argv[1]
    use_ket = "--no-ket" not in sys.argv
    manifests = sorted(glob.glob(os.path.join(corpus_dir, "manifest-*.json")))
    if not manifests:
        sys.exit(f"no manifest in {corpus_dir}")
    manifest = json.load(open(manifests[-1]))

    iff_path = os.path.join(corpus_dir, "iff_pairs.jsonl")
    gloss_path = os.path.join(corpus_dir, "gloss_pairs.jsonl")
    n_iff = n_gloss = 0
    with open(iff_path, "w") as iff_f, open(gloss_path, "w") as gloss_f:
        for shard in manifest["shards"]:
            for line in open(os.path.join(corpus_dir, shard["file"])):
                rec = json.loads(line)
                if rec.get("iff_lhs") is not None:
                    iff_f.write(json.dumps({
                        "name": rec["name"], "module": rec["module"], "lock": rec["lock"],
                        "hypotheses": rec["hypotheses"],
                        "lhs": rec["iff_lhs"], "rhs": rec["iff_rhs"],
                    }, ensure_ascii=False) + "\n")
                    n_iff += 1
                if rec.get("docstring"):
                    gloss_f.write(json.dumps({
                        "name": rec["name"], "module": rec["module"], "lock": rec["lock"],
                        "docstring": rec["docstring"],
                        "canonical_type": rec["canonical_type"],
                    }, ensure_ascii=False) + "\n")
                    n_gloss += 1

    derived = {"source_run_id": manifest["run_id"], "derived": []}
    for path, n in ((iff_path, n_iff), (gloss_path, n_gloss)):
        entry = {"file": os.path.basename(path), "records": n,
                 "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
        if use_ket:
            entry["cid"] = ket_put_file(path)
        derived["derived"].append(entry)
    out = os.path.join(corpus_dir, f"manifest-derived-{manifest['run_id']}.json")
    with open(out, "w") as f:
        json.dump(derived, f, indent=1)
    if use_ket:
        print(f"derived manifest CID: {ket_put_file(out)}")
    print(f"iff_pairs {n_iff}, gloss_pairs {n_gloss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
