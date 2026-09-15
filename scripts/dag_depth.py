"""dag_depth.py --corpus <declarations corpus dir> [--pairs <jsonl with a,b names>] [--no-ket]

The proof DAG of a corpus, derived from `proof_consts`: an edge d -> c for
every corpus declaration c that d's proof uses. Emits, sealed as a derived
table of the corpus:

  <corpus>/dag_depth.jsonl   one row per declaration: name, depth (longest
                             proof-dependency chain down to a declaration
                             whose proof uses no corpus declaration), n_deps
                             (in-corpus proof dependencies), n_dependents
  <corpus>/manifest-dag-<corpus>.json  counts, depth histogram, the table's
                             sha256 + CID, runner sha256

and, with --pairs, adds `dag_distance` to each pair: the length of the
shortest UNDIRECTED path between the two declarations in the proof DAG
(null if disconnected within --max-dist). Far-apart pairs that embed as
equivalent are the interesting S5 proposals; depth is the W0 curriculum axis.

Cycles cannot occur in a well-formed environment; a cycle found in the data
is reported, never silently broken.
"""

from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ket_put_file(p: str) -> str | None:
    r = subprocess.run(["ket", "put", p], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ket put failed for {p}: {r.stderr.strip()}")
    return r.stdout.strip().split()[-1]


def load_graph(corpus: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """name -> in-corpus proof dependencies (deduplicated, self-edges dropped)."""
    deps, module = {}, {}
    for path in sorted(glob.glob(os.path.join(corpus, "declarations-*.jsonl"))):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                deps[r["name"]] = r.get("proof_consts") or []
                module[r["name"]] = r.get("module")
    names = set(deps)
    for n, cs in deps.items():
        deps[n] = sorted({c for c in cs if c in names and c != n})
    return deps, module


def depths(deps: dict[str, list[str]]) -> tuple[dict[str, int], list[str]]:
    """Longest-path depth by iterative DFS (no recursion limit); returns the
    depths and any nodes found on a cycle (depth undefined -> excluded)."""
    depth: dict[str, int] = {}
    state: dict[str, int] = {}          # 1 = on stack, 2 = done
    cyclic: list[str] = []
    for root in deps:
        if root in state:
            continue
        stack = [(root, iter(deps[root]))]
        state[root] = 1
        while stack:
            n, it = stack[-1]
            advanced = False
            for c in it:
                s = state.get(c)
                if s is None:
                    state[c] = 1
                    stack.append((c, iter(deps[c])))
                    advanced = True
                    break
                if s == 1:
                    cyclic.append(c)
            if advanced:
                continue
            stack.pop()
            state[n] = 2
            depth[n] = 1 + max((depth.get(c, 0) for c in deps[n]), default=-1) if deps[n] else 0
    return depth, sorted(set(cyclic))


def undirected(deps: dict[str, list[str]]) -> dict[str, list[str]]:
    adj = collections.defaultdict(list)
    for n, cs in deps.items():
        for c in cs:
            adj[n].append(c)
            adj[c].append(n)
    return adj


def distance(adj: dict[str, list[str]], a: str, b: str, max_dist: int) -> int | None:
    if a == b:
        return 0
    seen, frontier = {a}, [a]
    for d in range(1, max_dist + 1):
        nxt = []
        for n in frontier:
            for m in adj.get(n, ()):
                if m == b:
                    return d
                if m not in seen:
                    seen.add(m)
                    nxt.append(m)
        frontier = nxt
        if not frontier:
            return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--pairs", default="", help="jsonl of {a, b, ...}; writes <pairs>.dag.jsonl with dag_distance")
    ap.add_argument("--max-dist", type=int, default=12)
    ap.add_argument("--no-ket", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    deps, module = load_graph(args.corpus)
    depth, cyclic = depths(deps)
    dependents = collections.Counter(c for cs in deps.values() for c in cs)
    table = os.path.join(args.corpus, "dag_depth.jsonl")
    hist = collections.Counter()
    with open(table, "w") as f:
        for n in sorted(deps):
            d = depth.get(n)
            hist[d] += 1
            f.write(json.dumps({"name": n, "module": module[n], "depth": d, "n_deps": len(deps[n]),
                                "n_dependents": dependents.get(n, 0)}) + "\n")
    put = (lambda p: None) if args.no_ket else ket_put_file
    man = {"corpus": os.path.basename(os.path.normpath(args.corpus)), "declarations": len(deps),
           "edges": sum(len(v) for v in deps.values()), "cyclic_nodes": cyclic,
           "depth_histogram": {str(k): v for k, v in sorted(hist.items(), key=lambda kv: (kv[0] is None, kv[0]))},
           "max_depth": max((d for d in depth.values()), default=0),
           "table": {"file": os.path.basename(table), "records": len(deps), "sha256": sha256_file(table), "cid": put(table)},
           "runner_sha256": sha256_file(os.path.abspath(__file__)), "elapsed_s": round(time.time() - t0, 1)}
    if args.pairs:
        adj = undirected(deps)
        out = args.pairs + ".dag.jsonl"
        n_pairs, n_conn = 0, 0
        with open(args.pairs) as f, open(out, "w") as g:
            for line in f:
                p = json.loads(line)
                dist = distance(adj, p["a"], p["b"], args.max_dist)
                n_pairs += 1
                n_conn += dist is not None
                p["dag_distance"] = dist
                p["depth_a"], p["depth_b"] = depth.get(p["a"]), depth.get(p["b"])
                g.write(json.dumps(p, ensure_ascii=False) + "\n")
        man["pairs"] = {"file": out, "n": n_pairs, "connected_within_max": n_conn, "max_dist": args.max_dist,
                        "sha256": sha256_file(out), "cid": put(out)}
    mp = os.path.join(args.corpus, f"manifest-dag-{man['corpus']}.json")
    with open(mp, "w") as f:
        json.dump(man, f, indent=1)
    man["manifest_cid"] = put(mp)
    print(json.dumps({k: man[k] for k in ("declarations", "edges", "max_depth", "cyclic_nodes", "elapsed_s")}),
          "| depth histogram:", dict(list(man["depth_histogram"].items())[:12]), "| manifest CID:", man["manifest_cid"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
