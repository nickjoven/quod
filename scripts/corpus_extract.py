#!/usr/bin/env python3
"""corpus_extract.py [--limit N] [--resume-after NAME] [--selftest [K]]
                     [--out DIR] [--run-id ID] [--no-ket] [--shard-size N]
                     [--timeout S] [--start-timeout S]

Batch corpus extraction at the crouzeix pin (the Q-13 convergence): one Lean
process imports Mathlib once (scripts/CorpusWalk.lean) and writes one record
per declaration. This driver computes the BLAKE3 lock exactly as lock.py does,
shards the records to JSONL, and records an append-only manifest whose ket CID
is the corpus version.

The walker writes DECL records to `records.raw` (stdout) and START/progress
markers to `progress.raw` (stderr) via plain file redirection — no pipes, no
reader threads. The driver polls those files' growth:

  * A declaration whose `pp.all`/`whnf` explodes stalls the walker. If the raw
    files stop growing for --timeout seconds (--start-timeout during the
    initial Mathlib import, which produces no output), the walker is killed by
    process group, the hung declaration (the last START without a DECL) is
    recorded, and the run RESUMES past exactly that one. Skips are listed in
    the manifest — declarations quod cannot process in bounded time, a real
    finding, not a swallowed error.
  * A crash or reboot mid-run resumes from the records already on disk.

--selftest K cross-checks K random walker records field-by-field against the
per-declaration oracle scripts/lock.py; anything under 100% agreement fails.

Exit 0 success; 1 selftest disagreement; 3 no progress.
"""
import argparse, hashlib, json, os, re, signal, subprocess, sys, time

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
    r = subprocess.run(["ket", "--home", KET_HOME, "put", path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ket put {path} failed (KET_HOME={KET_HOME}):\n{r.stderr.strip()}")
    return r.stdout.strip()


def last_start(raw_path: str) -> str | None:
    """Name of the last declaration the walker announced (START) — the one to
    resume past when it hung. START markers are on stdout (records.raw)."""
    name = None
    if os.path.exists(raw_path):
        with open(raw_path, errors="replace") as f:
            for line in f:
                if line.startswith("START\t"):
                    name = line[6:].strip()
    return name


def run_segment(env_extra: dict, raw_path: str, err_path: str, *, inactivity: int, startup: int):
    """Run one walker pass, appending all walker output (DECL/START/INFO) to
    raw_path (stdout); err_path captures lake/lean diagnostics (stderr) for
    debugging only — the driver never depends on it (Lean's stderr is not
    reliably flushed to a file).

    Returns (status, hung_name). status: "done" (finished / limit / INFO done),
    "timeout" (raw stopped growing), "crashed" (nonzero exit unfinished).
    """
    # The walker writes records to CORPUS_OUT via an explicit, per-line-flushed
    # file handle (stdout/stderr redirection to a file does not flush until
    # exit here). stdout/stderr are captured to err_path for lake diagnostics.
    env = {**os.environ, **env_extra, "CORPUS_OUT": os.path.abspath(raw_path)}
    eo = open(err_path, "ab")
    try:
        proc = subprocess.Popen(["lake", "env", "lean", WALKER], cwd=CALIB, env=env,
                                stdout=eo, stderr=eo, stdin=subprocess.DEVNULL,
                                start_new_session=True)
    finally:
        eo.close()

    def kill_group():
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass

    def walker_done() -> bool:
        if not os.path.exists(raw_path):
            return False
        with open(raw_path, errors="replace") as f:
            return any(ln.startswith("INFO\tdone") for ln in f)

    # `started` must flip only when the walker produces ACTUAL output, so the
    # generous startup budget (which must cover the ~230s silent Mathlib import)
    # governs until then. Seeding last_size at 0 (not -1) is load-bearing: at -1
    # the first poll's size==0 counted as growth, flipped started immediately,
    # and the 90s inactivity budget then killed the walker mid-import every
    # segment ("timeout hung=None" loop) before a single record was written.
    last_size = 0
    last_change = time.time()
    started = False
    while True:
        rc = proc.poll()
        if rc is not None:
            return ("done" if (walker_done() or rc == 0) else "crashed", last_start(raw_path))
        size = os.path.getsize(raw_path) if os.path.exists(raw_path) else 0
        now = time.time()
        if size > last_size:
            last_size, last_change, started = size, now, True
        if now - last_change > (inactivity if started else startup):
            kill_group()
            time.sleep(1)
            return ("timeout", last_start(raw_path))
        time.sleep(3)


def parse_raw(raw_path: str):
    """Yield normalized+locked records from a records.raw file."""
    with open(raw_path, errors="replace") as f:
        for line in f:
            if not line.startswith("DECL\t"):
                continue
            try:
                rec = json.loads(line[5:])
            except json.JSONDecodeError:
                continue  # a torn final line from a killed walker; the record repeats on resume
            rec["canonical_type"] = normalize(rec["canonical_type"])
            rec["lock"], rec["hash_algo"] = lock_of(rec["canonical_type"])
            yield rec


def selftest(k: int) -> int:
    import tempfile, random
    limit = max(k * 20, 2000)
    with tempfile.TemporaryDirectory() as d:
        raw, err = os.path.join(d, "r"), os.path.join(d, "e")
        print(f"selftest: walking first {limit} declarations", file=sys.stderr)
        run_segment({"CORPUS_LIMIT": str(limit)}, raw, err, inactivity=180, startup=900)
        pool = list(parse_raw(raw))
    sample = random.Random(1337).sample(pool, min(k, len(pool)))
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
            print(f"selftest: {i + 1}/{len(sample)} checked, {bad} mismatches", file=sys.stderr)
    print(f"selftest: {len(sample) - bad}/{len(sample)} field-exact")
    return 0 if bad == 0 else 1


def extract(args) -> int:
    run_id = args.run_id or time.strftime("%Y%m%d-%H%M%S")
    out_dir = args.out or os.path.join(ROOT, "corpus", run_id)
    os.makedirs(out_dir, exist_ok=True)
    raw = os.path.join(out_dir, "records.raw")
    err = os.path.join(out_dir, "walker.err")

    # Resume across a crash/reboot from the last record already in records.raw.
    resume = args.resume_after
    if not resume and os.path.exists(raw):
        last = None
        for rec in parse_raw(raw):
            last = rec["name"]
        if last:
            resume = last
            print(f"corpus-extract: resuming after {last} "
                  f"({os.path.getsize(raw)} raw bytes on disk)", file=sys.stderr)

    if args.limit:
        env_limit = {"CORPUS_LIMIT": str(args.limit)}
    else:
        env_limit = {}

    skips: list[dict] = []
    no_progress = 0
    t0 = time.time()
    while True:
        before = os.path.getsize(raw) if os.path.exists(raw) else 0
        env = dict(env_limit)
        if resume:
            env["CORPUS_RESUME_AFTER"] = resume
        status, hung = run_segment(env, raw, err, inactivity=args.timeout, startup=args.start_timeout)
        print(f"corpus-extract: segment {status} (hung={hung})", file=sys.stderr)
        if status == "done":
            break
        after = os.path.getsize(raw) if os.path.exists(raw) else 0
        no_progress = no_progress + 1 if after == before else 0
        if no_progress >= 5:
            sys.exit(f"corpus-extract: 5 consecutive segments made no progress "
                     f"(last {status}, hung={hung}); aborting — systemic, not one bad decl")
        if hung is None:
            sys.exit(3)
        skips.append({"name": hung, "status": status})
        print(f"corpus-extract: skipping {hung} and resuming after it", file=sys.stderr)
        resume = hung

    # Parse records.raw into JSONL shards (dedup by name: a killed segment can
    # re-emit records already past on resume only if resume-after is off by a
    # boundary; keep the first occurrence).
    shards, count, seen = [], 0, set()
    shard_f = None
    for rec in parse_raw(raw):
        if rec["name"] in seen:
            continue
        seen.add(rec["name"])
        if count % args.shard_size == 0:
            if shard_f:
                shard_f.close()
            path = os.path.join(out_dir, f"declarations-{count // args.shard_size:04d}.jsonl")
            shards.append(path)
            shard_f = open(path, "w")
        shard_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        count += 1
    if shard_f:
        shard_f.close()
    elapsed = round(time.time() - t0, 1)

    toolchain = open(os.path.join(CALIB, "lean-toolchain")).read().strip()
    manifest = {
        "run_id": run_id, "elapsed_s": elapsed, "records": count, "skipped": skips,
        "pin": {"lean_toolchain": toolchain, "crouzeix": {"mathlib": "8f9d9cff", "jin": "f9d5c8d"}},
        "scripts": {f: sha256_file(os.path.join(SCRIPTS, f)) for f in sorted(os.listdir(SCRIPTS))
                    if f.endswith((".py", ".lean", ".sh"))},
        "ket_binary": (sha256_file(subprocess.run(["which", "ket"], capture_output=True, text=True)
                                   .stdout.strip()) if not args.no_ket else None),
        "shards": [],
    }
    for path in shards:
        entry = {"file": os.path.basename(path), "records": sum(1 for _ in open(path)),
                 "sha256": sha256_file(path)}
        if not args.no_ket:
            entry["cid"] = ket_put_file(path)
        manifest["shards"].append(entry)
    man_path = os.path.join(out_dir, f"manifest-{run_id}.json")
    with open(man_path, "w") as f:
        json.dump(manifest, f, indent=1)
    if not args.no_ket:
        print(f"manifest CID: {ket_put_file(man_path)}")
    print(f"extracted {count} records in {elapsed}s ({len(skips)} skipped) -> {out_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume-after", default="")
    ap.add_argument("--selftest", nargs="?", const=100, type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--shard-size", type=int, default=10_000)
    ap.add_argument("--timeout", type=int, default=90,
                    help="seconds of no raw-file growth before a declaration is deemed hung")
    ap.add_argument("--start-timeout", type=int, default=600,
                    help="seconds to allow for the initial Mathlib import (no output)")
    ap.add_argument("--no-ket", action="store_true")
    args = ap.parse_args()
    if args.selftest is not None:
        return selftest(args.selftest)
    return extract(args)


if __name__ == "__main__":
    sys.exit(main())
