#!/usr/bin/env python3
"""models_register.py — the local model registry (LOCAL.md L1): weights by CID, license on record.

  python3 scripts/models_register.py add --name goedel-prover-v2-8b-q4 \\
      --url https://huggingface.co/<org>/<repo>/resolve/<rev>/<file>.gguf \\
      --source <org>/<repo>@<rev> --license <SPDX or text> --quant Q4_K_M --ctx 8192 [--sha256 <expected>]
  python3 scripts/models_register.py verify <name>      # re-hash the file, compare to the record
  python3 scripts/models_register.py list

A registry entry models/<name>.json records: the file's sha256 and ket CID, byte size, source repo and
revision, quantization, context length, license, and when it was registered. A prover config cites the
entry (attempt_b.py --weights models/<name>.json), so a tier L run names its weights the way every run
names its Mathlib pin. Nothing is downloaded without a --license value: admission is a recorded decision.
Weights live under models/weights/ (gitignored); only the JSON records are tracked.
"""
from __future__ import annotations

import argparse, hashlib, json, os, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models"); WEIGHTS = os.path.join(MODELS, "weights")


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def ket_put(p: str) -> str | None:
    r = subprocess.run(["ket", "put", p], capture_output=True, text=True)
    return r.stdout.strip().split()[-1] if r.returncode == 0 else None


def download(url: str, dst: str) -> None:
    tmp = dst + ".part"
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0); done = 0; last = 0
        for chunk in iter(lambda: r.read(1 << 22), b""):
            f.write(chunk); done += len(chunk)
            if total and done - last > (1 << 28):
                print(f"  {done / 1e9:.2f} / {total / 1e9:.2f} GB", file=sys.stderr, flush=True); last = done
    os.replace(tmp, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--name", required=True); a.add_argument("--url", default=""); a.add_argument("--file", default="", help="register a locally produced file instead of downloading"); a.add_argument("--source", required=True)
    a.add_argument("--license", required=True, help="the model's license as published (SPDX id or short text); admission is a decision")
    a.add_argument("--quant", default=""); a.add_argument("--ctx", type=int, default=0); a.add_argument("--sha256", default="")
    a.add_argument("--no-ket", action="store_true")
    v = sub.add_parser("verify"); v.add_argument("name")
    sub.add_parser("list")
    args = ap.parse_args()
    os.makedirs(WEIGHTS, exist_ok=True)

    if args.cmd == "add":
        if not args.url and not args.file:
            sys.exit("give --url or --file")
        dst = os.path.abspath(args.file) if args.file else os.path.join(WEIGHTS, os.path.basename(args.url.split("?")[0]))
        if not os.path.exists(dst):
            if not args.url: sys.exit(f"no such file: {dst}")
            print(f"downloading {args.url} -> {dst}", file=sys.stderr, flush=True); download(args.url, dst)
        sha = sha256_file(dst)
        if args.sha256 and sha != args.sha256:
            os.remove(dst); sys.exit(f"sha256 mismatch: got {sha}, expected {args.sha256}; file removed")
        rec = {"name": args.name, "file": os.path.relpath(dst, ROOT), "bytes": os.path.getsize(dst), "sha256": sha,
               "cid": None if args.no_ket else ket_put(dst), "source": args.source, "url": args.url or None,
               "quantization": args.quant, "context_length": args.ctx, "license": args.license,
               "registered": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "format": os.path.splitext(dst)[1].lstrip(".")}
        with open(os.path.join(MODELS, f"{args.name}.json"), "w") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps({k: rec[k] for k in ("name", "bytes", "sha256", "cid", "license")}, indent=1))
    elif args.cmd == "verify":
        rec = json.load(open(os.path.join(MODELS, f"{args.name}.json")))
        sha = sha256_file(os.path.join(ROOT, rec["file"]))
        print(args.name, "OK" if sha == rec["sha256"] else f"MISMATCH {sha} != {rec['sha256']}")
        return 0 if sha == rec["sha256"] else 1
    else:
        for f in sorted(os.listdir(MODELS)):
            if f.endswith(".json"):
                r = json.load(open(os.path.join(MODELS, f)))
                print(f"{r['name']:32s} {r['bytes'] / 1e9:5.2f} GB  {r['quantization'] or '-':8s} {r['license'][:24]:24s} cid {(r['cid'] or '-')[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
