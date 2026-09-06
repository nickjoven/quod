#!/usr/bin/env python3
"""corpus_extract.py [--limit N] [--resume-after NAME] [--selftest [K]]
                     [--out DIR] [--run-id ID] [--no-ket] [--shard-size N]

Batch corpus extraction at the crouzeix pin (the Q-13 convergence): one Lean
process imports Mathlib once (scripts/CorpusWalk.lean) and emits one record
per declaration; this driver normalizes whitespace exactly as lock.py does,
computes the BLAKE3 lock over the normalized canonical type, shards JSONL,
and records an append-only manifest whose ket CID is the corpus version.

--selftest K cross-checks K random walker records field-by-field against the
per-declaration oracle scripts/lock.py and refuses anything under 100%
agreement. Run it before any full extraction; two copies of one
canonicalization pipeline exist (lock.py's embedded Lean and CorpusWalk.lean)
and this gate is what keeps them from drifting apart silently.

Exit 0 success; 1 selftest disagreement; 3 Lean failed.
"""
import argparse, hashlib, json, os, random, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIB = os.path.join(ROOT, "calib")
SCRIPTS = os.path.join(ROOT, "scripts")
WALKER = os.path.join(SCRIPTS, "CorpusWalk.lean")
KET_HOME = os.environ.get("KET_HOME", os.path.join(ROOT, ".ket"))


def normalize(canon: str) -> str:
    return re.sub(r"\s+", " ", canon).strip()


def lock_of(canon: str) -> tuple[str, str]:
    try:
        import blake3  # type: ignore
        return blake3.blake3(canon.encode()).hexdigest(), "blake3"
    except ImportError:
        return hashlib.blake2b(canon.encode(), digest_size=32).hexdigest(), "blake2b"


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def ket_put_file(path: str) -> str:
    r = subprocess.run(["ket", "--home", KET_HOME, "put", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ket put {path} failed (KET_HOME={KET_HOME}):\n{r.stderr.strip()}")
    return r.stdout.strip()


def run_walker(env_extra: dict, on_record) -> int:
    """Stream CorpusWalk output; call on_record(dict) per DECL line."""
    env = {**os.environ, **env_extra}
    proc = subprocess.Popen(["lake", "env", "lean", WALKER], cwd=CALIB, env=env,
                            stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    n = 0
    for line in proc.stdout:
        if line.startswith("DECL\t"):
            rec = json.loads(line[5:])
            rec["canonical_type"] = normalize(rec["canonical_type"])
            rec["lock"], rec["hash_algo"] = lock_of(rec["canonical_type"])
            on_record(rec)
            n += 1
    proc.wait()
    if proc.returncode != 0:
        sys.exit(3)
    return n


def selftest(k: int) -> int:
    """Field-exact agreement between the walker and lock.py on K random decls."""
    sample: list[dict] = []
    print(f"selftest: walking first {max(k * 20, 2000)} declarations for a sample pool",
          file=sys.stderr)
    pool: list[dict] = []
    run_walker({"CORPUS_LIMIT": str(max(k * 20, 2000))}, pool.append)
    rng = random.Random(1337)
    sample = rng.sample(pool, min(k, len(pool)))
    bad = 0
    for i, rec in enumerate(sample):
        r = subprocess.run(["python3", os.path.join(SCRIPTS, "lock.py"),
                            CALIB, rec["module"], rec["name"], "--json"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"MISMATCH {rec['name']}: lock.py failed:\n{r.stdout}{r.stderr}")
            bad += 1
            continue
        oracle = json.loads(r.stdout[r.stdout.index("{"):])
        checks = {
            "lock": (rec["lock"], oracle["lock"]),
            "canonical_type": (rec["canonical_type"], oracle["canonical_type"]),
            "kind": (rec["kind"], oracle["kind"]),
            "reduces_to_True": (rec["reduces_to_true"], oracle["reduces_to_True"]),
            "hypotheses": (rec["hypotheses"], [h["type"] for h in oracle["hypotheses"]]),
            "custom_constants": (sorted(rec["type_consts_custom"]),
                                 sorted(c["name"] for c in oracle["custom_constants"])),
        }
        misses = {f: (a, b) for f, (a, b) in checks.items() if a != b}
        if misses:
            bad += 1
            print(f"MISMATCH {rec['name']}:")
            for f, (a, b) in misses.items():
                print(f"  {f}: walker={a!r} oracle={b!r}")
        if (i + 1) % 10 == 0:
            print(f"selftest: {i + 1}/{len(sample)} checked, {bad} mismatches",
                  file=sys.stderr)
    print(f"selftest: {len(sample) - bad}/{len(sample)} field-exact")
    return 0 if bad == 0 else 1


def extract(args) -> int:
    run_id = args.run_id or time.strftime("%Y%m%d-%H%M%S")
    out_dir = args.out or os.path.join(ROOT, "corpus", run_id)
    os.makedirs(out_dir, exist_ok=True)
    shards, current, count = [], None, 0

    def rotate():
        nonlocal current
        if current:
            current.close()
            current = None

    def on_record(rec):
        nonlocal current, count
        if count % args.shard_size == 0:
            rotate()
            path = os.path.join(out_dir, f"declarations-{count // args.shard_size:04d}.jsonl")
            shards.append(path)
            current = open(path, "w")
        current.write(json.dumps(rec, ensure_ascii=False) + "\n")
        count += 1

    env = {}
    if args.limit:
        env["CORPUS_LIMIT"] = str(args.limit)
    if args.resume_after:
        env["CORPUS_RESUME_AFTER"] = args.resume_after
    t0 = time.time()
    run_walker(env, on_record)
    rotate()
    elapsed = round(time.time() - t0, 1)

    toolchain = open(os.path.join(CALIB, "lean-toolchain")).read().strip()
    manifest = {
        "run_id": run_id,
        "elapsed_s": elapsed,
        "records": count,
        "pin": {"lean_toolchain": toolchain, "crouzeix": {"mathlib": "8f9d9cff", "jin": "f9d5c8d"}},
        "scripts": {os.path.basename(p): sha256_file(p)
                    for p in sorted(os.path.join(SCRIPTS, f) for f in os.listdir(SCRIPTS)
                                    if f.endswith((".py", ".lean", ".sh")))},
        "ket_binary": sha256_file(subprocess.run(["which", "ket"], capture_output=True,
                                                 text=True).stdout.strip()) if not args.no_ket else None,
        "shards": [],
    }
    for path in shards:
        entry = {"file": os.path.basename(path),
                 "records": sum(1 for _ in open(path)),
                 "sha256": sha256_file(path)}
        if not args.no_ket:
            entry["cid"] = ket_put_file(path)
        manifest["shards"].append(entry)
    man_path = os.path.join(out_dir, f"manifest-{run_id}.json")
    with open(man_path, "w") as f:
        json.dump(manifest, f, indent=1)
    if not args.no_ket:
        print(f"manifest CID: {ket_put_file(man_path)}")
    print(f"extracted {count} records in {elapsed}s -> {out_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume-after", default="")
    ap.add_argument("--selftest", nargs="?", const=100, type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--shard-size", type=int, default=10_000)
    ap.add_argument("--no-ket", action="store_true")
    args = ap.parse_args()
    if args.selftest is not None:
        return selftest(args.selftest)
    return extract(args)


if __name__ == "__main__":
    sys.exit(main())
