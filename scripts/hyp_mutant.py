#!/usr/bin/env python3
"""hyp_mutant.py <project_dir> <relative/File.lean> --delete "<exact text>" [--expect-fail]

Hypothesis-deletion mutant. Copies the file, deletes the given text (which
must occur exactly once), compiles both the original copy and the mutant
with `lake env lean` inside the project, and reports:

  original compiles: True/False
  mutant compiles:   True/False

The mutant is KILLED when the original compiles and the mutant does not:
the deleted hypothesis is load-bearing. A mutant that still compiles marks
a dead premise. Exit 0 killed; 1 survived (dead premise); 3 original does
not compile (the control is broken, nothing is learned); 2 usage.
"""
import os, subprocess, sys, tempfile


def compiles(proj, src):
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=proj, delete=False) as f:
        f.write(src); path = f.name
    try:
        r = subprocess.run(["lake", "env", "lean", path], cwd=proj, capture_output=True, text=True)
    finally:
        os.unlink(path)
    return r.returncode == 0, (r.stdout + r.stderr)[-1500:]


def main() -> int:
    a = sys.argv[1:]
    if len(a) < 4 or "--delete" not in a:
        print(__doc__); return 2
    proj, rel = a[0], a[1]
    text = a[a.index("--delete") + 1]
    src = open(os.path.join(proj, rel)).read()
    if src.count(text) != 1:
        print(f"delete text occurs {src.count(text)} times, need exactly 1"); return 2
    ok0, log0 = compiles(proj, src)
    if not ok0:
        print("original compiles: False"); print(log0); return 3
    ok1, log1 = compiles(proj, src.replace(text, "", 1))
    print(f"original compiles: True\nmutant compiles:   {ok1}   (deleted {text!r})")
    if ok1:
        print("mutant SURVIVED: dead premise"); return 1
    first = [l for l in log1.splitlines() if "error" in l][:3]
    print("mutant KILLED:", " | ".join(first) if first else "(compile failed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
