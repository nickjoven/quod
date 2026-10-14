#!/usr/bin/env python3
"""reproduce.py — fresh-checkout reproduction of the openai-ns intake (github #8, deliverable 2).

    reproduce.py preflight
    reproduce.py integrity [--run DIR]
    reproduce.py run [--workdir DIR] [--run-id ID] [--workers 2] [--cpus 0-5]
                     [--toolchain-checker] [--chunk 4] [--resume] [--no-ket]

Three assurances, never conflated:

  preflight   The host can run this: toolchain manager, git, Python with blake3,
              memory, disk, no other Lean process on the box (one Lean process
              at a time), the pinned upstream reachable. Exit 4 when it cannot.

  integrity   ARTIFACT INTEGRITY ONLY. Every file the records cite is hashed
              afresh and compared with the recorded CID (BLAKE3 of the bytes,
              which is what ket stores) and sha256; the claims' evidence CIDs
              are checked against the index; RESULTS.json is checked against
              the checker log. Passing says the bytes on disk are the bytes the
              records describe. It says NOTHING about the proof: no Lean runs.
              Exit 0 when every byte matches, 1 otherwise, 3 when a cited file
              is absent and no substitute is tracked.

  run         FULL REPLAY into a new run directory. Clone the pinned commit,
              verify commit, toolchain, dependency revisions and statement-file
              hashes afresh (a prior PIN-verified.txt is never consulted), build
              the two targets, derive the proof's non-standard import closure
              from the environment, lock the four statements, run the axiom
              gate and the closure survey, build lean4checker at its pinned
              commit with the recorded one-line patch, replay the whole closure
              with it, optionally replay again with the toolchain's own
              `leanchecker` (no patch; runs in chunks), port the upstream
              statement and lock all 14 canonical forms on both sides, write
              claims and RESULTS.json from that evidence alone, and seal every
              file by CID in RUN.json. Historical records under evidence/ and
              RESULTS.json are never touched; the run has its own identity.
              Exit 0 on a complete accepted run; 1 when a command or a gate
              fails; 2 when the checkout does not match the pin; 3 when a
              required result is absent; 4 on preflight failure.

Status is computed by write_claims.py from the run's evidence; nothing here
types a status. Every CID is BLAKE3-256 of the file bytes, so the package is
verifiable with `b3sum` and no private store; when `ket` is on PATH the bytes
are also stored, and a store failure is a run failure, never a silent null.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, HERE)

PIN = json.load(open(os.path.join(HERE, "PIN.json")))
HIST_EVIDENCE = os.path.join(HERE, "evidence")
PATCH = os.path.join(HIST_EVIDENCE, "lean4checker-v4.34-patch.diff")
PORT = os.path.join(HERE, "port", "UpstreamNavierStokes.lean")
UPSTREAM_TRACKED = os.path.join(HIST_EVIDENCE, "upstream-8bf45ed7.lean")

LEAN4CHECKER_REPO = "https://github.com/leanprover/lean4checker"
LEAN4CHECKER_COMMIT = "91a7f0e8e9dffe927089f5a6edcfeeb8a0e07709"
LEAN4CHECKER_HIST_SHA256 = "f2fb235ab1583bd6286c1bfeb9c7d85eee30f4c7fdbea39e52243b69b53c9c63"
UPSTREAM_COMMIT = "8bf45ed7"
UPSTREAM_PATH = "FormalConjectures/Millenium/NavierStokes.lean"
UPSTREAM_RAW = f"https://raw.githubusercontent.com/google-deepmind/formal-conjectures/{UPSTREAM_COMMIT}/{UPSTREAM_PATH}"

CHALLENGE_MODULE = "ComparatorChallenges.NavierStokes"
SOLUTION_MODULE = "NavierStokes.ComparatorSolution"
DEMONSTRANDA = {"R3": "NavierStokes.Comparator.navier_stokes_breakdown_R3",
                "periodic": "NavierStokes.Comparator.navier_stokes_breakdown_periodic"}
PORT_MODULE = "Intake.UpstreamNavierStokes"
FIDELITY_DECLS = ["navier_stokes_breakdown_R3", "navier_stokes_breakdown_periodic",
                  "InitialVelocityConditionDecay.mk", "ForceConditionDecay.mk", "NavierStokesExistenceAndSmoothnessRn.mk",
                  "InitialVelocityConditionPeriodic.mk", "ForceConditionPeriodic.mk", "NavierStokesExistenceAndSmoothnessPeriodic.mk",
                  "InitialVelocityConditionDecay", "ForceConditionDecay", "NavierStokesExistenceAndSmoothnessRn",
                  "InitialVelocityConditionPeriodic", "ForceConditionPeriodic", "NavierStokesExistenceAndSmoothnessPeriodic"]
FIDELITY_SIDES = {"upstream": (PORT_MODULE, "NavierStokes.Upstream"), "adapted": (CHALLENGE_MODULE, "NavierStokes.Comparator")}

STD = ["Init", "Lean", "Std", "Mathlib", "Batteries", "Aesop", "Qq", "ProofWidgets", "Plausible",
       "ImportGraph", "LeanSearchClient", "Lake", "Cli"]

MIN_MEM_GB, MIN_DISK_GB = 16, 25

EXIT_STEP, EXIT_STALE, EXIT_MISSING, EXIT_PREFLIGHT = 1, 2, 3, 4


# ----------------------------------------------------------------------------- small helpers

def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(msg: str) -> None:
    print(f"{now()} {msg}", flush=True)


def sha256(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def b3(p: str) -> str:
    import blake3  # type: ignore
    return blake3.blake3(open(p, "rb").read()).hexdigest()


def b3_bytes(b: bytes) -> str:
    import blake3  # type: ignore
    return blake3.blake3(b).hexdigest()


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def jload_loose(p: str) -> dict:
    """Parse the JSON object in a file that may carry text before/after it (gate stdout)."""
    t = open(p).read()
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def tool_version(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr).strip().splitlines()[0] if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


def mem_total_gb() -> float:
    for l in open("/proc/meminfo"):
        if l.startswith("MemTotal:"):
            return int(l.split()[1]) / 1024 / 1024
    return 0.0


def disk_free_gb(path: str) -> float:
    return shutil.disk_usage(path).free / 1024 ** 3


def other_lean_processes() -> list[str]:
    """Lean-family processes on the box other than ours: comm-based, so the shell
    that runs this script never matches itself."""
    r = subprocess.run(["ps", "-eo", "pid,comm,args"], capture_output=True, text=True)
    out = []
    for l in r.stdout.splitlines()[1:]:
        parts = l.split(None, 2)
        if len(parts) >= 2 and parts[1] in ("lean", "lake", "lean4checker", "leanchecker"):
            out.append(l.strip()[:120])
    return out


def lean_path_env() -> dict:
    """elan's proxies first; the user's global git config ignored, since a clone/checkout/apply of pinned
    commits needs none of it and an old git rejects newer option values in it (recorded in RUN.json)."""
    return {**os.environ, "PATH": os.path.expanduser("~/.elan/bin") + os.pathsep + os.environ.get("PATH", ""),
            "GIT_CONFIG_GLOBAL": os.devnull}


# ----------------------------------------------------------------------------- pure checks (tested)

def check_file(path: str, expected: dict) -> dict:
    """Compare one on-disk file with the pin's recorded identity. Pure except for the read."""
    b = open(path, "rb").read()
    got = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "blake3": b3_bytes(b), "git_blob": git_blob(b)}
    mism = [k for k in ("bytes", "sha256", "blake3", "git_blob") if k in expected and expected[k] != got[k]]
    return {"path": expected.get("path", path), "got": got, "mismatch": mism, "ok": not mism}


def check_pin(head: str, toolchain: str, manifest: dict, files: dict[str, dict], pin: dict = PIN) -> dict:
    """The whole pin comparison as a pure function of what was read from the checkout.

    head       40-hex HEAD of the checkout
    toolchain  contents of lean-toolchain, stripped
    manifest   parsed lake-manifest.json
    files      {"statement_file": check_file(...), "challenge_spec": check_file(...)}
    """
    exp = pin["expected"]
    revs = {p["name"]: p.get("rev", "") for p in manifest.get("packages", [])}
    deps = {}
    for key, name in (("mathlib", "mathlib"), ("comparator", "Comparator"), ("lean4export", "lean4export")):
        want, got = exp[key], revs.get(name, "")
        deps[name] = {"expected": want, "got": got, "ok": got.startswith(want) and bool(want)}
    rep = {
        "commit": {"expected": pin["commit"], "got": head, "ok": head == pin["commit"]},
        "lean_toolchain": {"expected": exp["lean_toolchain"], "got": toolchain, "ok": toolchain == exp["lean_toolchain"]},
        "dependencies": deps,
        "files": files,
    }
    rep["ok"] = (rep["commit"]["ok"] and rep["lean_toolchain"]["ok"] and all(d["ok"] for d in deps.values())
                 and all(f["ok"] for f in files.values()))
    rep["failures"] = ([k for k in ("commit", "lean_toolchain") if not rep[k]["ok"]]
                       + [f"dependency {n}" for n, d in deps.items() if not d["ok"]]
                       + [f"file {k}: {' '.join(f['mismatch'])}" for k, f in files.items() if not f["ok"]])
    return rep


def nonstd_modules(names: list[str], std: list[str] = STD) -> list[str]:
    """Modules of an environment header that are not from the pinned standard libraries."""
    def is_std(m: str) -> bool:
        return any(m == s or m.startswith(s + ".") for s in std)
    return sorted({m for m in names if not is_std(m)})


def normalize_namespace(canonical: str, ns: str, target: str = "NavierStokes.__NS__") -> str:
    """Rewrite one side's namespace prefix to a neutral placeholder so the two
    canonical forms can be compared up to naming. `ns` is e.g. NavierStokes.Upstream."""
    return canonical.replace(ns + ".", target + ".")


def fidelity_rows(locks: dict[str, dict[str, dict]]) -> list[dict]:
    """locks = {"upstream": {decl: lock_json}, "adapted": {decl: lock_json}} -> rows as in fidelity.json."""
    rows = []
    for d in FIDELITY_DECLS:
        u, a = locks["upstream"].get(d), locks["adapted"].get(d)
        if not u or not a or "canonical_type" not in u or "canonical_type" not in a:
            rows.append({"decl": d, "raw_equal": None, "namespace_normalized_equal": None,
                         "lock_upstream": (u or {}).get("lock"), "lock_adapted": (a or {}).get("lock"), "missing": True})
            continue
        cu = normalize_namespace(u["canonical_type"], FIDELITY_SIDES["upstream"][1])
        ca = normalize_namespace(a["canonical_type"], FIDELITY_SIDES["adapted"][1])
        rows.append({"decl": d, "raw_equal": u["canonical_type"] == a["canonical_type"],
                     "namespace_normalized_equal": cu == ca, "lock_upstream": u["lock"], "lock_adapted": a["lock"]})
    return rows


def parse_checker_log(text: str) -> dict:
    m = re.search(r"^checker exit (\d+) (\S+)", text, re.M)
    mods = re.search(r"modules=(\d+)", text)
    sha = re.search(r"checker_sha256=([0-9a-f]{64})", text)
    return {"ran": m is not None, "exit": int(m.group(1)) if m else None, "finished": m.group(2) if m else None,
            "modules": int(mods.group(1)) if mods else None, "checker_sha256": sha.group(1) if sha else None}


# ----------------------------------------------------------------------------- preflight

def preflight(workdir: str | None = None, quiet: bool = False) -> dict:
    env = lean_path_env()
    rep = {"at": now(), "checks": {}, "tools": {}}
    c = rep["checks"]
    rep["tools"] = {
        "elan": tool_version(["elan", "--version"]) if shutil.which("elan", path=env["PATH"]) else None,
        "lake": shutil.which("lake", path=env["PATH"]),
        "git": tool_version(["git", "--version"]),
        "python": platform.python_version(),
        "ket": tool_version(["ket", "--version"]),
        "taskset": shutil.which("taskset"),
    }
    try:
        import blake3  # type: ignore  # noqa: F401
        rep["tools"]["blake3"] = getattr(blake3, "__version__", "present")
    except ImportError:
        rep["tools"]["blake3"] = None
    c["elan"] = rep["tools"]["elan"] is not None
    c["lake_proxy"] = rep["tools"]["lake"] is not None
    c["git"] = rep["tools"]["git"] is not None
    c["python>=3.10"] = sys.version_info >= (3, 10)
    c["blake3"] = rep["tools"]["blake3"] is not None
    rep["mem_total_gb"] = round(mem_total_gb(), 1)
    c[f"memory>={MIN_MEM_GB}GB"] = rep["mem_total_gb"] >= MIN_MEM_GB
    probe = workdir if workdir and os.path.isdir(workdir) else HERE
    rep["disk_free_gb"] = round(disk_free_gb(probe), 1)
    c[f"disk>={MIN_DISK_GB}GB"] = rep["disk_free_gb"] >= MIN_DISK_GB
    rep["other_lean_processes"] = other_lean_processes()
    c["no_other_lean_process"] = not rep["other_lean_processes"]
    r = subprocess.run(["git", "ls-remote", PIN["repo"], "HEAD"], capture_output=True, text=True, timeout=120)
    rep["upstream_head"] = r.stdout.split()[0] if r.returncode == 0 and r.stdout.split() else None
    c["upstream_reachable"] = rep["upstream_head"] is not None
    rep["upstream_head_is_pin"] = rep["upstream_head"] == PIN["commit"]
    rep["ok"] = all(c.values())
    if not quiet:
        for k, v in c.items():
            say(f"preflight {'ok  ' if v else 'FAIL'} {k}")
        say(f"preflight mem {rep['mem_total_gb']} GB, disk free {rep['disk_free_gb']} GB at {probe}, "
            f"upstream HEAD {rep['upstream_head']} ({'= pin' if rep['upstream_head_is_pin'] else 'moved since the pin; the pin is what is built'})")
    return rep


# ----------------------------------------------------------------------------- integrity (fast; no Lean)

def integrity(run_dir: str | None = None) -> int:
    """Hash every cited byte and compare with the records. Exit 0 only when all match."""
    base = run_dir or HERE
    cids_path = os.path.join(base, "evidence", "CIDS.json")
    results_path = os.path.join(base, "RESULTS.json")
    claims_dir = os.path.join(base, "claims") if run_dir else os.path.join(ROOT, "claims", "openai-ns")
    if not os.path.exists(cids_path) or not os.path.exists(results_path):
        say(f"integrity: missing {cids_path if not os.path.exists(cids_path) else results_path}")
        return EXIT_MISSING
    cids = json.load(open(cids_path))
    res = json.load(open(results_path))
    bad, absent, n = [], [], 0
    # the untracked historical port compiled inside repo/ is byte-identical to the tracked port file
    substitutes = {"repo/Intake/UpstreamNavierStokes.lean": "port/UpstreamNavierStokes.lean"}
    for rel, rec in cids.items():
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            if rel in substitutes and os.path.exists(os.path.join(base, substitutes[rel])):
                p = os.path.join(base, substitutes[rel]); rel = f"{rel} (via tracked {substitutes[rel]})"
            else:
                absent.append(rel); continue
        n += 1
        got_cid, got_sha = b3(p), sha256(p)
        if got_cid != rec.get("cid") or (rec.get("sha256") and got_sha != rec["sha256"]):
            bad.append(f"{rel}: cid {got_cid[:12]} vs recorded {str(rec.get('cid'))[:12]}")
    if res.get("evidence_cids") != cids:
        bad.append("RESULTS.json evidence_cids differs from evidence/CIDS.json")
    ck = res.get("checker") or {}
    cl = os.path.join(base, "evidence", "checker.log")
    if os.path.exists(cl):
        parsed = parse_checker_log(open(cl).read())
        if ck.get("log_sha256") and ck["log_sha256"] != sha256(cl): bad.append("checker.log sha256 differs from RESULTS.checker.log_sha256")
        if ck.get("log_cid") and ck["log_cid"] != b3(cl): bad.append("checker.log cid differs from RESULTS.checker.log_cid")
        if parsed["exit"] != ck.get("exit") or parsed["modules"] != ck.get("modules"):
            bad.append(f"checker.log says exit={parsed['exit']} modules={parsed['modules']}; RESULTS says exit={ck.get('exit')} modules={ck.get('modules')}")
        cm = os.path.join(base, "evidence", "checker-modules.txt")
        if os.path.exists(cm):
            k = len([l for l in open(cm).read().split() if l])
            if ck.get("modules") != k: bad.append(f"checker-modules.txt lists {k} modules; RESULTS.checker.modules={ck.get('modules')}")
    else:
        absent.append("evidence/checker.log")
    for st in (res.get("results") or {}).values():
        if st.get("status") in ("proven", "refuted") and not (ck.get("ran") and ck.get("exit") == 0):
            bad.append("a proven/refuted result without a passing checker replay in RESULTS.json")
    # claims: every cited evidence CID is in the index and the locks agree with the lock files
    import yaml
    for f in sorted(os.listdir(claims_dir)) if os.path.isdir(claims_dir) else []:
        if not f.endswith(".yml"): continue
        c = yaml.safe_load(open(os.path.join(claims_dir, f)))
        known = {v["cid"] for v in cids.values()} | {ck.get("log_cid")}
        for k, v in (c.get("evidence") or {}).items():
            if v is not None and v not in known: bad.append(f"{f}: evidence.{k} {v[:12]} not in the CID index")
        key = "R3" if c["id"].endswith("R3") else "periodic"
        lk = os.path.join(base, "evidence", f"lock-challenge_{key}.json")
        if os.path.exists(lk) and jload_loose(lk)["lock"] != c["lock"]: bad.append(f"{f}: lock differs from {os.path.basename(lk)}")
        if c.get("status") == "proven" and c.get("proof_verdict") != "accepted": bad.append(f"{f}: proven without an accepted verdict")
    # fidelity: the table must follow from the lock files by the recorded normalization
    fj = os.path.join(base, "evidence", "fidelity.json")
    fd = os.path.join(base, "evidence", "fidelity")
    if os.path.exists(fj) and os.path.isdir(fd):
        locks = {"upstream": {}, "adapted": {}}
        for side in locks:
            for d in FIDELITY_DECLS:
                p = os.path.join(fd, f"{side}--{d}.json")
                if os.path.exists(p): locks[side][d] = jload_loose(p)
        want = {r["decl"]: r for r in json.load(open(fj))["rows"]}
        for r in fidelity_rows(locks):
            w = want.get(r["decl"])
            if not w or any(w.get(k) != r.get(k) for k in ("raw_equal", "namespace_normalized_equal", "lock_upstream", "lock_adapted")):
                bad.append(f"fidelity row {r['decl']} does not follow from the lock files")
    say(f"integrity: {n} cited files hashed against {cids_path}")
    for a in absent: say(f"integrity: ABSENT {a} (cited by CID only; not on this checkout)")
    for b_ in bad: say(f"integrity: MISMATCH {b_}")
    say(f"integrity: RESULTS.json cid {b3(results_path)}")
    for f in sorted(os.listdir(claims_dir)) if os.path.isdir(claims_dir) else []:
        if f.endswith(".yml"): say(f"integrity: {f} cid {b3(os.path.join(claims_dir, f))}")
    if bad:
        say("integrity: FAIL — bytes differ from the records"); return EXIT_STEP
    if absent:
        say("integrity: INCOMPLETE — every present byte matches, but cited files are absent"); return EXIT_MISSING
    say("integrity: PASS — every cited byte matches its record. This is artifact integrity only: no Lean ran, "
        "nothing about the proof was checked; see `reproduce.py run` for the replay.")
    return 0


# ----------------------------------------------------------------------------- the run

class StepFailed(Exception):
    def __init__(self, name: str, rc: int | None, code: int = EXIT_STEP):
        super().__init__(f"{name} failed (rc={rc})"); self.name, self.rc, self.code = name, rc, code


class Run:
    def __init__(self, workdir: str, run_id: str, workers: int, cpus: str | None, toolchain_checker: bool,
                 chunk: int, resume: bool, use_ket: bool):
        self.workdir = os.path.abspath(workdir)
        self.E = os.path.join(self.workdir, "evidence")
        self.repo = os.path.join(self.workdir, "repo")
        self.checker_dir = os.path.join(self.workdir, "lean4checker")
        os.makedirs(self.E, exist_ok=True)
        self.env = lean_path_env()
        self.use_ket = use_ket and shutil.which("ket") is not None
        self.ket_home = os.environ.get("KET_HOME") or (os.path.join(ROOT, ".ket") if os.path.isdir(os.path.join(ROOT, ".ket")) else None)
        self.rec = {
            "intake": "openai-ns", "run_id": run_id, "started": now(), "finished": None, "status": "running", "failed_step": None,
            "pin": {"repo": PIN["repo"], "commit": PIN["commit"], **PIN["expected"]},
            "resumed": resume, "reused_steps": [],
            "resources": {"checker_workers": workers, "build_cpus": cpus, "lake_jobs_flag": None,
                          "toolchain_checker_chunk": chunk if toolchain_checker else None,
                          "nproc": os.cpu_count(), "mem_total_gb": round(mem_total_gb(), 1),
                          "disk_free_gb_before": round(disk_free_gb(self.workdir), 1), "disk_free_gb_after": None,
                          "workdir_gb": None,
                          "mathlib_cache_prewarmed": os.path.isdir(os.path.expanduser("~/.cache/mathlib")) and bool(os.listdir(os.path.expanduser("~/.cache/mathlib")))},
            "host": {"kernel": platform.release(), "machine": platform.machine(), "python": platform.python_version(),
                     "elan": None, "lean": None, "lake": None, "git": tool_version(["git", "--version"]),
                     "ket": tool_version(["ket", "--version"]), "ket_home": self.ket_home if self.use_ket else None},
            "steps": [], "pin_check": None, "closure": None, "checker": None, "toolchain_checker": None,
            "fidelity": None, "historical_agreement": {}, "results": None, "cids": None,
            "runner": {}, "exit_code": None,
        }
        self.workers, self.cpus, self.toolchain_checker, self.chunk, self.resume = workers, cpus, toolchain_checker, chunk, resume
        # a resumed run keeps every earlier attempt's record: its full-build timing is the measurement,
        # the incremental rebuild below is not
        if resume and os.path.exists(self.run_json):
            prior = json.load(open(self.run_json))
            self.rec["prior_attempts"] = prior.pop("prior_attempts", []) + [{k: prior.get(k) for k in
                                                                            ("run_id", "started", "finished", "status", "failed_step", "steps", "runner", "closure")}]
        self.save()

    # -- bookkeeping
    @property
    def run_json(self) -> str:
        return os.path.join(self.workdir, "RUN.json")

    def save(self) -> None:
        tmp = self.run_json + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.rec, f, indent=1)
        os.replace(tmp, self.run_json)

    def seal(self, path: str) -> str:
        """CID = BLAKE3 of the bytes; stored in ket too when available (must agree)."""
        cid = b3(path)
        if self.use_ket:
            env = {**os.environ, **({"KET_HOME": self.ket_home} if self.ket_home else {})}
            r = subprocess.run(["ket", "put", path], capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise StepFailed(f"ket put {os.path.relpath(path, self.workdir)}", r.returncode)
            got = r.stdout.strip().split()[-1]
            if got != cid:
                raise StepFailed(f"ket CID {got[:12]} != blake3 {cid[:12]} for {path}", None)
        return cid

    def step(self, name: str, cmd: list[str], cwd: str, log: str, must: bool = True, timeout: int | None = None,
             env: dict | None = None, stdin: str | None = None) -> dict:
        logp = os.path.join(self.E, log)
        say(f"step {name}: {' '.join(cmd[:6])}{' …' if len(cmd) > 6 else ''}  (cwd {os.path.relpath(cwd, self.workdir)}, log evidence/{log})")
        t0 = time.time(); start = now()
        with open(logp, "w") as lf:
            try:
                r = subprocess.run(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, env=env or self.env,
                                   timeout=timeout, input=stdin, text=True if stdin is not None else None)
                rc = r.returncode
            except subprocess.TimeoutExpired:
                rc = -1; lf.write(f"\nTIMEOUT after {timeout}s\n")
            except FileNotFoundError as e:
                rc = -2; lf.write(f"\n{e}\n")
        s = {"name": name, "cmd": cmd if len(" ".join(cmd)) < 2000 else cmd[:8] + [f"… ({len(cmd)} args)"],
             "cwd": os.path.relpath(cwd, self.workdir), "start": start, "end": now(), "seconds": round(time.time() - t0, 1),
             "rc": rc, "log": f"evidence/{log}", "log_sha256": sha256(logp), "log_cid": None}
        self.rec["steps"].append(s); self.save()
        say(f"step {name}: rc={rc} in {s['seconds']}s")
        if must and rc != 0:
            tail = open(logp, errors="replace").read()[-1500:]
            say(f"step {name} FAILED; log tail:\n{tail}")
            raise StepFailed(name, rc)
        return s

    def agree(self, key: str, value) -> None:
        self.rec["historical_agreement"][key] = value; self.save()

    # -- steps
    def fetch(self) -> None:
        if self.resume and os.path.isdir(os.path.join(self.repo, ".git")):
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, capture_output=True, text=True).stdout.strip()
            if head == PIN["commit"]:
                self.rec["reused_steps"].append("fetch"); say("fetch: existing checkout at the pin, reused"); return
            shutil.rmtree(self.repo)
        elif os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        self.step("clone", ["git", "clone", "--no-checkout", PIN["repo"], self.repo], self.workdir, "clone.log")
        self.step("checkout", ["git", "-c", "advice.detachedHead=false", "checkout", PIN["commit"]], self.repo, "checkout.log")

    def verify_pin(self) -> None:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, capture_output=True, text=True).stdout.strip()
        tc = open(os.path.join(self.repo, "lean-toolchain")).read().strip()
        manifest = json.load(open(os.path.join(self.repo, "lake-manifest.json")))
        files = {k: check_file(os.path.join(self.repo, PIN["expected"][k]["path"]), PIN["expected"][k])
                 for k in ("statement_file", "challenge_spec")}
        rep = check_pin(head, tc, manifest, files)
        rep["verified_at"] = now()
        rep["git_status_clean"] = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, capture_output=True, text=True).stdout.strip() == ""
        rep["lake_manifest_name"] = manifest.get("name")
        json.dump(rep, open(os.path.join(self.E, "pin-check.json"), "w"), indent=1)
        self.rec["pin_check"] = {"ok": rep["ok"], "failures": rep["failures"], "verified_at": rep["verified_at"]}
        self.save()
        say(f"pin check: {'ok' if rep['ok'] else 'STALE/MISMATCH ' + ', '.join(rep['failures'])}")
        if not rep["ok"]:
            raise StepFailed("verify_pin", None, EXIT_STALE)

    def toolchain(self) -> None:
        tc = PIN["expected"]["lean_toolchain"]
        self.step("elan_install", ["elan", "toolchain", "install", tc], self.repo, "toolchain.log")
        self.rec["host"]["elan"] = tool_version(["elan", "--version"])
        self.rec["host"]["lean"] = tool_version(["lake", "env", "lean", "--version"]) or tool_version(["lean", "--version"])
        self.rec["host"]["lake"] = tool_version(["lake", "--version"])
        if self.rec["host"]["lean"] and tc.split(":")[-1] not in self.rec["host"]["lean"]:
            raise StepFailed(f"lean --version {self.rec['host']['lean']!r} is not the pinned {tc}", None, EXIT_STALE)
        self.save()

    def build(self) -> None:
        self.step("cache_get", ["lake", "exe", "cache", "get"], self.repo, "cache.log", timeout=3600)
        cmd = ["lake", "build", SOLUTION_MODULE, CHALLENGE_MODULE]
        if self.cpus and shutil.which("taskset"):
            cmd = ["taskset", "-c", self.cpus] + cmd
        self.step("build", cmd, self.repo, "build.log", timeout=6 * 3600)

    def header_walk(self, imports: list[str], log: str) -> tuple[int, list[str]]:
        """Modules of the environment header after importing `imports`; (rc, names)."""
        from leanenv import run_lean
        src = ("".join(f"import {m}\n" for m in imports) + "open Lean\n"
               "run_meta do\n  let env ← getEnv\n  for m in env.header.moduleNames do\n    IO.println s!\"MOD {m}\"\n")
        with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=self.repo, delete=False) as f:
            f.write(src); path = f.name
        t0 = time.time()
        try:
            r = run_lean(self.repo, path)
        finally:
            os.unlink(path)
        logp = os.path.join(self.E, log)
        open(logp, "w").write(r.stdout + r.stderr)
        self.rec["steps"].append({"name": f"header_walk {' '.join(imports)}", "cmd": ["lake", "env", "lean", f"<import {' '.join(imports)}; header walk>"],
                                  "cwd": "repo", "start": None, "end": now(), "seconds": round(time.time() - t0, 1), "rc": r.returncode,
                                  "log": f"evidence/{log}", "log_sha256": sha256(logp), "log_cid": None})
        self.save()
        return r.returncode, [l.split(None, 1)[1] for l in r.stdout.splitlines() if l.startswith("MOD ")]

    def closure_modules(self) -> list[str]:
        """The proof's non-standard import closure = union of the two targets' headers, walked
        separately: the challenge module and the solution's definitions module declare the same
        names, so the two cannot be imported into one environment (Q-32); that fact is recorded."""
        rc_both, _ = self.header_walk([SOLUTION_MODULE, CHALLENGE_MODULE], "closure-modules-coimport.log")
        names: set[str] = set()
        for target, log in ((SOLUTION_MODULE, "closure-modules-solution.log"), (CHALLENGE_MODULE, "closure-modules-challenge.log")):
            rc, got = self.header_walk([target], log)
            if rc != 0:
                raise StepFailed(f"closure_modules ({target})", rc)
            names |= set(got)
        mods = nonstd_modules(sorted(names))
        if not mods or CHALLENGE_MODULE not in mods or SOLUTION_MODULE not in mods:
            raise StepFailed("closure_modules: the header walks did not list both targets", None, EXIT_MISSING)
        open(os.path.join(self.E, "closure-modules.txt"), "w").write("\n".join(mods) + "\n")
        hist = os.path.join(HIST_EVIDENCE, "checker-modules.txt")
        hist_set = set(open(hist).read().split()) if os.path.exists(hist) else set()
        self.rec["closure"] = {"modules": len(mods), "all_imported": len(names), "std_prefixes": STD,
                               "targets_coimportable": rc_both == 0,
                               "note": None if rc_both == 0 else "the challenge module and NavierStokes.ComparatorDefinitions declare the same names; "
                                                                 "see evidence/closure-modules-coimport.log (Q-32)"}
        self.agree("closure_modules", {"historical": len(hist_set), "now": len(mods), "same_set": hist_set == set(mods),
                                       "only_now": sorted(set(mods) - hist_set)[:20], "only_historical": sorted(hist_set - set(mods))[:20]})
        say(f"closure: {len(mods)} non-standard modules in the proof's import closure (historical 610, same set: {hist_set == set(mods)})")
        return mods

    def gate(self, script: str, args: list[str], out: str, must: bool = True) -> dict:
        s = self.step(os.path.splitext(out)[0], ["python3", os.path.join(SCRIPTS, script), self.repo, *args, "--json"],
                      self.repo, out, must=must, timeout=1800)
        return jload_loose(os.path.join(self.E, out)) if s["rc"] in (0, 1) else {}

    def locks_and_gates(self) -> None:
        for key, decl in DEMONSTRANDA.items():
            lc = self.gate("lock.py", [CHALLENGE_MODULE, decl], f"lock-challenge_{key}.json")
            ls = self.gate("lock.py", [SOLUTION_MODULE, decl], f"lock-solution_{key}.json")
            hist = jload_loose(os.path.join(HIST_EVIDENCE, f"lock-challenge_{key}.json"))["lock"]
            self.agree(f"lock_{key}", {"historical": hist, "now": lc.get("lock"), "equal": hist == lc.get("lock"),
                                       "offered_equal_now": lc.get("lock") == ls.get("lock")})
            say(f"lock {key}: challenge {str(lc.get('lock'))[:12]} offered {str(ls.get('lock'))[:12]} historical {hist[:12]}")
        # the axiom gate exits 1 when a declaration is outside the triple: that is a recorded rejection, not a crashed step
        self.gate("axiom_gate.py", [SOLUTION_MODULE, *DEMONSTRANDA.values()], "axioms-solution.json", must=False)
        rc = self.rec["steps"][-1]["rc"]
        if rc not in (0, 1):
            raise StepFailed("axioms-solution", rc)
        for key, decl in DEMONSTRANDA.items():
            self.gate("closure.py", [CHALLENGE_MODULE, decl], f"closure-challenge_{key}.json")

    def definitions(self) -> None:
        """Q-32: the names in the two statements are declared twice; compare what they mean.
        scripts/defs_digest.py on each side, per demonstrandum; equal digests required for `proven`."""
        import defs_digest as DD
        out = {}
        for key, decl in DEMONSTRANDA.items():
            sides = {}
            for side, mod in (("challenge", CHALLENGE_MODULE), ("solution", SOLUTION_MODULE)):
                f = f"definitions-{side}_{key}.json"
                self.step(f"definitions {side} {key}", ["python3", os.path.join(SCRIPTS, "defs_digest.py"), self.repo, mod, decl, "--json"],
                          self.repo, f, timeout=1800)
                sides[side] = jload_loose(os.path.join(self.E, f))
            cmp = DD.compare(sides["challenge"]["rows"], sides["solution"]["rows"])
            out[key] = {"demonstrandum": decl, "equal": cmp["equal"], "differ": cmp["differ"], "only_challenge": cmp["only_a"],
                        "only_solution": cmp["only_b"], "digest_challenge": cmp["digest_a"], "digest_solution": cmp["digest_b"],
                        "constants": len(sides["challenge"]["rows"]),
                        "modules_challenge": sides["challenge"]["modules"], "modules_solution": sides["solution"]["modules"],
                        "missing": sorted(set(sides["challenge"]["missing"]) | set(sides["solution"]["missing"]))}
            say(f"definitions {key}: {len(sides['challenge']['rows'])} constants, digests {'EQUAL' if cmp['equal'] else 'DIFFER ' + str(cmp['differ'][:5])}")
        rep = {"method": "scripts/defs_digest.py: every non-standard constant reachable from the statement through types, definition "
                         "values and constructor types, canonical pp.all type and value, BLAKE3 over the sorted rows (modules excluded); "
                         "computed in the challenge module's environment and in the solution module's environment",
               "all_equal": all(v["equal"] for v in out.values()), "per_demonstrandum": out}
        json.dump(rep, open(os.path.join(self.E, "definitions.json"), "w"), indent=1)
        self.rec["definitions"] = {"all_equal": rep["all_equal"], "constants": {k: v["constants"] for k, v in out.items()}}
        self.save()

    def build_lean4checker(self) -> str:
        binp = os.path.join(self.checker_dir, ".lake", "build", "bin", "lean4checker")
        if not (self.resume and os.path.isdir(os.path.join(self.checker_dir, ".git"))):
            if os.path.isdir(self.checker_dir): shutil.rmtree(self.checker_dir)
            self.step("lean4checker_clone", ["git", "clone", "--no-checkout", LEAN4CHECKER_REPO, self.checker_dir], self.workdir, "lean4checker-clone.log")
            self.step("lean4checker_checkout", ["git", "-c", "advice.detachedHead=false", "checkout", LEAN4CHECKER_COMMIT], self.checker_dir, "lean4checker-checkout.log")
            self.step("lean4checker_patch", ["git", "apply", "--verbose", PATCH], self.checker_dir, "lean4checker-patch.log")
        else:
            self.rec["reused_steps"].append("lean4checker_clone")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.checker_dir, capture_output=True, text=True).stdout.strip()
        tc = open(os.path.join(self.checker_dir, "lean-toolchain")).read().strip()
        if head != LEAN4CHECKER_COMMIT or tc != PIN["expected"]["lean_toolchain"]:
            raise StepFailed(f"lean4checker checkout {head[:12]} toolchain {tc} is not the recorded patched state", None, EXIT_STALE)
        diff = subprocess.run(["git", "diff"], cwd=self.checker_dir, capture_output=True, text=True).stdout
        open(os.path.join(self.E, "lean4checker-applied.diff"), "w").write(diff)
        self.step("lean4checker_build", ["lake", "build"], self.checker_dir, "lean4checker-build.log", timeout=3600)
        if not os.path.exists(binp):
            raise StepFailed("lean4checker binary absent after build", None, EXIT_MISSING)
        info = {"repo": LEAN4CHECKER_REPO, "commit": head, "lean_toolchain": tc, "patch": "evidence/lean4checker-applied.diff",
                "patch_equals_recorded": sha256(os.path.join(self.E, "lean4checker-applied.diff")) == sha256(PATCH) or diff.strip() == open(PATCH).read().strip(),
                "binary_sha256": sha256(binp), "binary_blake3": b3(binp), "binary_bytes": os.path.getsize(binp)}
        json.dump(info, open(os.path.join(self.E, "lean4checker-binary.json"), "w"), indent=1)
        self.agree("lean4checker_binary_sha256", {"historical": LEAN4CHECKER_HIST_SHA256, "now": info["binary_sha256"],
                                                  "equal": info["binary_sha256"] == LEAN4CHECKER_HIST_SHA256})
        say(f"lean4checker built: sha256 {info['binary_sha256'][:12]} (historical {LEAN4CHECKER_HIST_SHA256[:12]}, equal={info['binary_sha256'] == LEAN4CHECKER_HIST_SHA256})")
        return binp

    def replay(self, binp: str, mods: list[str]) -> None:
        logp = os.path.join(self.E, "checker.log")
        open(os.path.join(self.E, "checker-modules.txt"), "w").write("\n".join(mods) + "\n")
        bsha = sha256(binp)
        if self.resume and os.path.exists(logp):
            p = parse_checker_log(open(logp).read())
            if p["ran"] and p["exit"] == 0 and p["modules"] == len(mods) and p["checker_sha256"] == bsha:
                self.rec["reused_steps"].append("replay"); say("replay: complete passing log for this binary and module list, reused")
                self.rec["checker"] = {**p, "workers": self.workers, "reused": True}; self.save(); return
        header = f"start {now()} modules={len(mods)} checker_sha256={bsha} workers={self.workers}\n"
        open(logp, "w").write(header)
        cmd = ["lake", "env", binp, f"--num-workers={self.workers}", *mods]
        say(f"replay: lean4checker over {len(mods)} modules with {self.workers} workers (historical wall 79 min)")
        t0 = time.time(); start = now()
        with open(logp, "a") as lf:
            try:
                rc = subprocess.run(cmd, cwd=self.repo, stdout=lf, stderr=subprocess.STDOUT, env=self.env, timeout=12 * 3600).returncode
            except subprocess.TimeoutExpired:
                rc = -1; lf.write("\nTIMEOUT\n")
            lf.write(f"checker exit {rc} {now()}\n")
        s = {"name": "replay", "cmd": cmd[:4] + [f"… ({len(mods)} modules)"], "cwd": "repo", "start": start, "end": now(),
             "seconds": round(time.time() - t0, 1), "rc": rc, "log": "evidence/checker.log", "log_sha256": sha256(logp), "log_cid": None}
        self.rec["steps"].append(s)
        self.rec["checker"] = {**parse_checker_log(open(logp).read()), "workers": self.workers, "reused": False, "seconds": s["seconds"]}
        self.save()
        say(f"replay: exit {rc} in {s['seconds'] / 60:.1f} min")
        if rc != 0:
            raise StepFailed("replay", rc)

    def toolchain_replay(self, mods: list[str]) -> None:
        """Second, patch-free replay with the `leanchecker` the pinned toolchain ships (lean4checker upstreamed).
        Its source says it is 'not an external verifier, simply a tool to detect environment hacking'; it is
        recorded as a descriptor and never decides status. One process per chunk: it spawns a task per module."""
        d = os.path.join(self.E, "leanchecker"); os.makedirs(d, exist_ok=True)
        lcbin = subprocess.run(["lake", "env", "which", "leanchecker"], cwd=self.repo, capture_output=True, text=True, env=self.env).stdout.strip()
        if not lcbin or not os.path.exists(lcbin):
            self.rec["toolchain_checker"] = {"available": False}; self.save(); say("leanchecker: not in this toolchain; skipped"); return
        summary = os.path.join(d, "summary.log")
        open(summary, "w").write(f"start {now()} modules={len(mods)} chunk={self.chunk} leanchecker_sha256={sha256(lcbin)}\n")
        t0 = time.time(); failed = []; chunks = 0
        say(f"leanchecker: {len(mods)} modules in chunks of {self.chunk}")
        for i in range(0, len(mods), self.chunk):
            part = mods[i:i + self.chunk]; chunks += 1
            logp = os.path.join(d, f"chunk-{chunks}.log"); t1 = time.time()
            with open(logp, "w") as lf:
                try:
                    rc = subprocess.run(["lake", "env", lcbin, "-v", *part], cwd=self.repo, stdout=lf, stderr=subprocess.STDOUT, env=self.env, timeout=3600).returncode
                except subprocess.TimeoutExpired:
                    rc = -1; lf.write("\nTIMEOUT\n")
            if rc != 0: failed.append(chunks)
            open(summary, "a").write(f"chunk {chunks} n={len(part)} exit={rc} elapsed={time.time() - t1:.0f}s first={part[0]}\n")
            if chunks % 10 == 0:
                self.rec["toolchain_checker"] = {"available": True, "in_progress": True, "chunks_done": chunks, "failed_chunks": failed}; self.save()
                say(f"leanchecker: {chunks} chunks ({min(i + self.chunk, len(mods))}/{len(mods)} modules), {len(failed)} failed, {(time.time() - t0) / 60:.0f} min")
        rc = 0 if not failed else 1
        open(summary, "a").write(f"done {now()} chunks={chunks} failed_chunks={len(failed)} exit {rc}\n")
        self.rec["toolchain_checker"] = {"available": True, "in_progress": False, "binary": lcbin, "binary_sha256": sha256(lcbin), "modules": len(mods),
                                         "chunk": self.chunk, "chunks": chunks, "failed_chunks": failed, "exit": rc,
                                         "seconds": round(time.time() - t0, 1), "log": "evidence/leanchecker/summary.log",
                                         "caveat": "toolchain-shipped; its source calls itself 'not an external verifier'; descriptor only"}
        self.rec["steps"].append({"name": "toolchain_replay", "cmd": ["lake", "env", "leanchecker", "-v", f"<chunks of {self.chunk}>"], "cwd": "repo",
                                  "start": None, "end": now(), "seconds": round(time.time() - t0, 1), "rc": rc,
                                  "log": "evidence/leanchecker/summary.log", "log_sha256": sha256(summary), "log_cid": None})
        self.save()
        say(f"leanchecker: exit {rc}, {chunks} chunks, {len(failed)} failed, {(time.time() - t0) / 60:.1f} min")
        if rc != 0:
            raise StepFailed("toolchain_replay", rc)

    def fidelity(self) -> None:
        # 1. the upstream statement file at the commit OpenAI's file cites, fetched afresh and compared with the tracked copy
        t0 = time.time()
        try:
            with urllib.request.urlopen(UPSTREAM_RAW, timeout=60) as r:
                up = r.read()
        except Exception as e:  # noqa: BLE001
            raise StepFailed(f"fetch upstream {UPSTREAM_RAW}: {e}", None)
        tracked = open(UPSTREAM_TRACKED, "rb").read()
        fetch = {"url": UPSTREAM_RAW, "commit": UPSTREAM_COMMIT, "path": UPSTREAM_PATH, "bytes": len(up), "sha256": hashlib.sha256(up).hexdigest(),
                 "blake3": b3_bytes(up), "git_blob": git_blob(up), "equals_tracked_copy": up == tracked, "fetched_at": now()}
        open(os.path.join(self.E, "upstream-8bf45ed7.lean"), "wb").write(up)
        json.dump(fetch, open(os.path.join(self.E, "upstream-fetch.json"), "w"), indent=1)
        self.rec["steps"].append({"name": "upstream_fetch", "cmd": ["GET", UPSTREAM_RAW], "cwd": ".", "start": None, "end": now(),
                                  "seconds": round(time.time() - t0, 1), "rc": 0 if fetch["equals_tracked_copy"] else 1,
                                  "log": "evidence/upstream-fetch.json", "log_sha256": sha256(os.path.join(self.E, "upstream-fetch.json")), "log_cid": None})
        self.agree("upstream_file", {"equals_tracked_copy": fetch["equals_tracked_copy"], "git_blob": fetch["git_blob"]})
        if not fetch["equals_tracked_copy"]:
            raise StepFailed("upstream file at 8bf45ed7 differs from the tracked copy", None, EXIT_STALE)
        # 2. the port: tracked file copied into the checkout; its diff from upstream recorded; compiled under the pin
        os.makedirs(os.path.join(self.repo, "Intake"), exist_ok=True)
        shutil.copyfile(PORT, os.path.join(self.repo, "Intake", "UpstreamNavierStokes.lean"))
        r = subprocess.run(["diff", "-u", os.path.join(self.E, "upstream-8bf45ed7.lean"), PORT], capture_output=True, text=True)
        open(os.path.join(self.E, "port-diff.txt"), "w").write(r.stdout)
        changed = sorted(l for l in r.stdout.splitlines()[2:] if l[:1] in "+-")
        hist = os.path.join(HIST_EVIDENCE, "port-diff.txt")
        hist_changed = sorted(l for l in open(hist).read().splitlines() if l[:1] in "+-") if os.path.exists(hist) else []
        self.agree("port_diff", {"changed_lines": len(changed), "same_changed_lines_as_historical": changed == hist_changed})
        lib = os.path.join(self.repo, ".lake", "build", "lib", "lean", "Intake"); os.makedirs(lib, exist_ok=True)
        self.step("port_compile", ["lake", "env", "lean", "-o", os.path.join(lib, "UpstreamNavierStokes.olean"),
                                   "-i", os.path.join(lib, "UpstreamNavierStokes.ilean"), "Intake/UpstreamNavierStokes.lean"],
                  self.repo, "port-compile.log", timeout=1800)
        # 3. 28 locks, both sides, every canonical form
        fd = os.path.join(self.E, "fidelity"); os.makedirs(fd, exist_ok=True)
        locks: dict[str, dict[str, dict]] = {"upstream": {}, "adapted": {}}
        for side, (mod, ns) in FIDELITY_SIDES.items():
            for d in FIDELITY_DECLS:
                out = f"fidelity/{side}--{d}.json"
                self.step(f"fidelity_lock {side} {d}", ["python3", os.path.join(SCRIPTS, "lock.py"), self.repo, mod, f"{ns}.{d}", "--json"],
                          self.repo, out, timeout=900)
                locks[side][d] = jload_loose(os.path.join(self.E, out))
        rows = fidelity_rows(locks)
        fid = {"method": "same-pin port of the upstream statement file (import/attribute/notation/namespace changes only; evidence/port-diff.txt), "
                         "locked by scripts/lock.py on both sides; canonical pp.all forms compared raw and with the namespace prefix normalized. "
                         "A descriptor, never a status: the upstream file lives at another toolchain and quod never compares locks across pins (decision 3).",
               "upstream_source": {"repo": "https://github.com/google-deepmind/formal-conjectures", "commit": UPSTREAM_COMMIT, "path": UPSTREAM_PATH,
                                   "git_blob": fetch["git_blob"], "sha256": fetch["sha256"]},
               "port_diff": "evidence/port-diff.txt", "all_equal_after_namespace_normalization": all(r.get("namespace_normalized_equal") for r in rows),
               "rows": rows}
        json.dump(fid, open(os.path.join(self.E, "fidelity.json"), "w"), indent=1)
        hj = os.path.join(HIST_EVIDENCE, "fidelity.json")
        if os.path.exists(hj):
            hrows = {r["decl"]: r for r in json.load(open(hj))["rows"]}
            self.agree("fidelity", {"all_equal_now": fid["all_equal_after_namespace_normalization"],
                                    "locks_equal_to_historical": all(hrows.get(r["decl"], {}).get("lock_adapted") == r["lock_adapted"]
                                                                     and hrows.get(r["decl"], {}).get("lock_upstream") == r["lock_upstream"] for r in rows)})
        self.rec["fidelity"] = {"all_equal_after_namespace_normalization": fid["all_equal_after_namespace_normalization"], "rows": len(rows)}
        self.save()
        say(f"fidelity: all 14 canonical forms equal after namespace normalization = {fid['all_equal_after_namespace_normalization']}")

    def report(self) -> None:
        import write_claims as W
        cids = {}
        for dp, _, fs in os.walk(self.E):
            for f in sorted(fs):
                p = os.path.join(dp, f); rel = os.path.relpath(p, self.workdir)
                cids[rel] = {"cid": self.seal(p), "sha256": sha256(p), "bytes": os.path.getsize(p)}
        for s in self.rec["steps"]:
            if s.get("log") and s["log"] in cids: s["log_cid"] = cids[s["log"]]["cid"]
        # the intake's pin record is historical and tracked; its identity is cited, not copied
        cids["PIN.json"] = {"cid": self.seal(os.path.join(HERE, "PIN.json")), "sha256": sha256(os.path.join(HERE, "PIN.json")),
                            "bytes": os.path.getsize(os.path.join(HERE, "PIN.json")), "path": "intake/openai-ns/PIN.json"}
        json.dump(cids, open(os.path.join(self.E, "CIDS.json"), "w"), indent=1)
        cids_self = {"cid": self.seal(os.path.join(self.E, "CIDS.json")), "sha256": sha256(os.path.join(self.E, "CIDS.json")),
                     "bytes": os.path.getsize(os.path.join(self.E, "CIDS.json"))}
        build = next((s for s in self.rec["steps"] if s["name"] == "build"), None)
        out = W.write(evidence=self.E, pin=PIN, cids=cids,
                      out_results=os.path.join(self.workdir, "RESULTS.json"), out_claims=os.path.join(self.workdir, "claims"),
                      closure_modules=os.path.join(self.E, "closure-modules.txt"), checker_modules=os.path.join(self.E, "checker-modules.txt"),
                      build_info={"wall_seconds": build["seconds"] if build else None, "start": build["start"] if build else None,
                                  "end": build["end"] if build else None, "log_cid": cids.get("evidence/build.log", {}).get("cid")},
                      checker_desc=f"lean4checker {LEAN4CHECKER_COMMIT} (toolchain v4.29.0-rc8) on {PIN['expected']['lean_toolchain']} "
                                   "with the recorded one-line patch (evidence/lean4checker-applied.diff), built in this run",
                      workers=self.workers, toolchain_checker=self.rec.get("toolchain_checker"), run_id=self.rec["run_id"], ket=False)
        self.rec["results"] = out["results"]
        self.rec["cids"] = {"RESULTS.json": self.seal(os.path.join(self.workdir, "RESULTS.json")),
                            **{f"claims/{f}": self.seal(os.path.join(self.workdir, "claims", f)) for f in sorted(os.listdir(os.path.join(self.workdir, "claims")))},
                            "evidence/CIDS.json": cids_self["cid"]}
        self.rec["runner"] = {f: sha256(os.path.join(d, f)) for d, f in ((HERE, "reproduce.py"), (HERE, "write_claims.py"), (SCRIPTS, "lock.py"),
                                                                        (SCRIPTS, "axiom_gate.py"), (SCRIPTS, "closure.py"), (SCRIPTS, "leanenv.py"))}
        self.rec["runner"]["quod_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        self.rec["runner"]["quod_dirty"] = subprocess.run(["git", "status", "--porcelain", "--", "scripts", "intake/openai-ns/*.py"], cwd=ROOT,
                                                          capture_output=True, text=True).stdout.strip() != ""
        for k, v in out["results"].items():
            hist = {"OPENAI-NS-R3": "3608c95f250ae65119e583dc9e166a29bc3c5ba3e00d1bff14f90eb935c11952",
                    "OPENAI-NS-PERIODIC": "486545e22b09f274b47a8ee14e24a7ba3422be7c0888199430b2f931b84a03d0"}[k]
            self.agree(f"status_{k}", {"status": v["status"], "verdict": v["proof_verdict"], "lock_equals_historical": v["lock"] == hist})
        self.save()
        say(f"report: {json.dumps({k: v['status'] for k, v in out['results'].items()})}")

    def finish(self, status: str, failed_step: str | None, code: int) -> None:
        self.rec.update({"finished": now(), "status": status, "failed_step": failed_step, "exit_code": code})
        self.rec["resources"]["disk_free_gb_after"] = round(disk_free_gb(self.workdir), 1)
        try:
            self.rec["resources"]["workdir_gb"] = round(int(subprocess.run(["du", "-sk", self.workdir], capture_output=True, text=True).stdout.split()[0]) / 1024 / 1024, 1)
        except (ValueError, IndexError):
            pass
        self.save()
        say(f"run {self.rec['run_id']}: {status}{' at ' + failed_step if failed_step else ''}; RUN.json {os.path.relpath(self.run_json, ROOT)}")


LEAN_LOCK = os.environ.get("LEAN_LOCK", "/tmp/lock.lean")


def hold_lean_lock():
    """The fleet rule (homeserv/AGENTS.md): one Lean process per box, enforced cooperatively with
    `flock` on lock.lean. Block until it is ours and keep it for the whole run."""
    import fcntl
    fh = open(LEAN_LOCK, "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        say(f"lean lock {LEAN_LOCK} is held by another job; waiting (nothing runs until it is released)")
        fcntl.flock(fh, fcntl.LOCK_EX)
    say(f"lean lock {LEAN_LOCK} acquired")
    return fh


def run(args) -> int:
    run_id = args.run_id or "r-" + _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    workdir = args.workdir or os.path.join(HERE, "runs", run_id)
    os.makedirs(workdir, exist_ok=True)
    lock = hold_lean_lock()
    pf = preflight(workdir)
    json.dump(pf, open(os.path.join(workdir, "preflight.json"), "w"), indent=1)
    if not pf["ok"]:
        say("preflight failed; nothing was run"); return EXIT_PREFLIGHT
    R = Run(workdir, run_id, args.workers, args.cpus, args.toolchain_checker, args.chunk, args.resume, not args.no_ket)
    R.lock_fh = lock  # held until the process exits
    R.rec["resources"]["lean_lock"] = LEAN_LOCK
    os.environ["GIT_CONFIG_GLOBAL"] = os.devnull  # every git call in this process, not only the stepped ones
    R.rec["host"]["git_config_global"] = os.devnull
    R.rec["preflight"] = {"ok": True, "at": pf["at"], "upstream_head": pf["upstream_head"]}
    try:
        R.fetch(); R.verify_pin(); R.toolchain(); R.build()
        mods = R.closure_modules()
        R.locks_and_gates()
        R.definitions()
        binp = R.build_lean4checker()
        R.replay(binp, mods)
        if args.toolchain_checker:
            R.toolchain_replay(mods)
        R.fidelity()
        R.report()
        if R.rec["checker"] is None or R.rec["checker"].get("exit") != 0:
            raise StepFailed("checker result absent", None, EXIT_MISSING)
        rejected = [k for k, v in R.rec["results"].items() if v["proof_verdict"] != "accepted"]
        if rejected:
            R.finish("rejected", f"verdicts {rejected}", EXIT_STEP); return EXIT_STEP
        R.finish("ok", None, 0); return 0
    except StepFailed as e:
        R.finish("failed", e.name, e.code); return e.code
    except KeyboardInterrupt:
        R.finish("interrupted", "signal", EXIT_STEP); return EXIT_STEP


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("preflight", help="can this host run the replay?")
    pi = sub.add_parser("integrity", help="fast: bytes vs records; no Lean; not a replay")
    pi.add_argument("--run", help="a runs/<id> directory instead of the historical records")
    pr = sub.add_parser("run", help="full fresh-checkout replay into runs/<id>")
    pr.add_argument("--workdir"); pr.add_argument("--run-id")
    pr.add_argument("--workers", type=int, default=2, help="lean4checker --num-workers (2 on a 15-23 GB box)")
    pr.add_argument("--cpus", default="0-5", help="taskset CPU list for the build; '' for none")
    pr.add_argument("--toolchain-checker", action="store_true", help="also replay with the toolchain's leanchecker (chunked)")
    pr.add_argument("--chunk", type=int, default=4, help="modules per leanchecker process")
    pr.add_argument("--resume", action="store_true", help="reuse an existing checkout / passing replay in the workdir")
    pr.add_argument("--no-ket", action="store_true", help="do not store bytes in ket (CIDs are blake3 either way)")
    a = ap.parse_args()
    if a.mode == "preflight":
        return 0 if preflight()["ok"] else EXIT_PREFLIGHT
    if a.mode == "integrity":
        return integrity(a.run)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
