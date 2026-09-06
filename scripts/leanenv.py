"""Shared: run `lean` with the project's `lake env` environment plus extra LEAN_PATH dirs."""
import os, subprocess

def lean_env(proj, extra_dirs=()):
    r = subprocess.run(["lake", "env", "env"], cwd=proj, capture_output=True, text=True, check=True)
    env = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    if extra_dirs:
        env["LEAN_PATH"] = os.pathsep.join(list(extra_dirs) + [env.get("LEAN_PATH", "")])
    return env

def run_lean(proj, path, extra_dirs=(), args=()):
    return subprocess.run(["lean", *args, path], cwd=proj, env=lean_env(proj, extra_dirs),
                          capture_output=True, text=True)

def extra_from_argv(argv):
    dirs = []
    for i, a in enumerate(argv):
        if a == "--extra-path" and i + 1 < len(argv): dirs.append(os.path.abspath(argv[i + 1]))
    return dirs
