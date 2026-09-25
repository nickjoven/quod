#!/usr/bin/env bash
# install.sh — compile quod's anchor modules at the Millennium registry pin.
#
# The registry clone (millennium/registry, gitignored) is the pin; its lakefile
# has one lean_lib, `Problems`, and is never edited. A quod-authored module
# therefore cannot be a `lake build` target there: each millennium/anchors/X.lean
# is copied to millennium/registry/Quod/Anchors/X.lean and compiled by hand
# under `lake env` into the clone's build dir, so that `import Quod.Anchors.X`
# resolves for anchor_check.py, axiom_gate.py and registry_import.py (which all
# run `lake env lean` in millennium/registry). Same mechanism as
# intake/openai-ns (Intake.UpstreamNavierStokes). A copy, not a symlink: lean
# realpaths the input to derive the module name and rejects a file outside cwd.
# Idempotent; one Lean process at a time. Run after scripts/bootstrap.sh millennium.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REG="$HERE/../registry"
export PATH="$HOME/.elan/bin:$PATH"
[ -f "$REG/lakefile.toml" ] || { echo "registry clone missing: run scripts/bootstrap.sh millennium" >&2; exit 1; }
OUT="$REG/.lake/build/lib/lean/Quod/Anchors"
mkdir -p "$REG/Quod/Anchors" "$OUT"
for src in "$HERE"/*.lean; do
  name="$(basename "$src" .lean)"
  cp "$src" "$REG/Quod/Anchors/$name.lean"
  ( cd "$REG" && lake env lean -o "$OUT/$name.olean" -i "$OUT/$name.ilean" "Quod/Anchors/$name.lean" )
  echo "compiled Quod.Anchors.$name -> $OUT/$name.olean"
done
