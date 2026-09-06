#!/usr/bin/env bash
# bootstrap.sh — reproduce the pinned environments on a fresh machine.
#
# Everything this clones or builds is gitignored; the pins below are the
# record. Run from anywhere; idempotent. Needs: git, curl, python3 (+ pyyaml,
# optional blake3), elan (installed here if missing), ~20 GB disk, network.
#
#   scripts/bootstrap.sh            # both subprojects
#   scripts/bootstrap.sh crouzeix   # calibration pin only
#   scripts/bootstrap.sh millennium # registry pin only
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WHAT="${1:-all}"

# ---- pins (one per subproject; decision 3) --------------------------------
JIN_REPO=https://github.com/jinshanmu/CrouzeixConjecture
JIN_REV=f9d5c8d                       # lean v4.28.0, mathlib 8f9d9cff
CROUZEIX_TOOLCHAIN=leanprover/lean4:v4.28.0
CHECKER_REPO=https://github.com/leanprover/lean4checker
CHECKER_CROUZEIX_REV=v4.28.0          # tag
REG_REPO=https://github.com/lean-dojo/LeanMillenniumPrizeProblems
REG_REV=fd52071                       # lean v4.31.0, mathlib fabf563a7c, PhysLean 3dddd61e
CHECKER_MILL_REV=91a7f0e              # upstream master; no v4.31.0 release (OPEN.yml Q-20)
MILL_TOOLCHAIN=leanprover/lean4:v4.31.0

log() { printf '\n== %s\n' "$*"; }

need_elan() {
  if ! command -v elan >/dev/null 2>&1 && [ ! -x "$HOME/.elan/bin/elan" ]; then
    log "installing elan"
    curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none
  fi
  export PATH="$HOME/.elan/bin:$PATH"
}

clone_at() { # url dir rev
  local url=$1 dir=$2 rev=$3
  if [ ! -d "$dir/.git" ]; then git clone -q "$url" "$dir"; fi
  git -C "$dir" fetch -q --all --tags
  git -C "$dir" checkout -q "$rev"
  printf '   %s @ %s\n' "$dir" "$(git -C "$dir" rev-parse --short HEAD)"
}

crouzeix() {
  log "crouzeix pin: Jin's repo at $JIN_REV"
  clone_at "$JIN_REPO" "$ROOT/calib/jin" "$JIN_REV"
  ( cd "$ROOT/calib/jin/Lean" && lake exe cache get >/dev/null && lake build )
  log "lean4checker $CHECKER_CROUZEIX_REV"
  clone_at "$CHECKER_REPO" "$ROOT/calib/lean4checker" "$CHECKER_CROUZEIX_REV"
  ( cd "$ROOT/calib/lean4checker" && lake build >/dev/null )
  log "calibration project (Quod.*)"
  cp "$ROOT/calib/jin/Lean/lean-toolchain" "$ROOT/calib/lean-toolchain"
  ( cd "$ROOT/calib" && lake build )
  log "smoke test (Q-23): two controls, no ket"
  ( cd "$ROOT" && python3 scripts/calibrate.py --only N2,N9 --no-ket )
}

millennium() {
  log "millennium pin: lean-dojo registry at $REG_REV"
  clone_at "$REG_REPO" "$ROOT/millennium/registry" "$REG_REV"
  ( cd "$ROOT/millennium/registry" && lake exe cache get >/dev/null \
    && lake build Problems.PVersusNP.Millennium Problems.RiemannHypothesis.Millennium \
                  Problems.NavierStokes.Millennium Problems.Hodge.Millennium \
                  Problems.BirchSwinnertonDyer.Millennium Problems.Poincare.Millennium \
                  Problems.YangMills.HamiltonianSpectrum )
  log "lean4checker master $CHECKER_MILL_REV on $MILL_TOOLCHAIN (unreleased pairing, Q-20)"
  clone_at "$CHECKER_REPO" "$ROOT/millennium/lean4checker" "$CHECKER_MILL_REV"
  echo "$MILL_TOOLCHAIN" > "$ROOT/millennium/lean4checker/lean-toolchain"
  ( cd "$ROOT/millennium/lean4checker" && lake build >/dev/null )
  log "registry import (writes claims/millennium/*.yml; --no-ket if no ket store)"
  ( cd "$ROOT" && python3 scripts/registry_import.py --no-ket )
}

need_elan
python3 -c "import yaml" 2>/dev/null || { echo "pip install pyyaml (and optionally blake3)"; exit 2; }
case "$WHAT" in
  all) crouzeix; millennium ;;
  crouzeix) crouzeix ;;
  millennium) millennium ;;
  *) echo "usage: $0 [all|crouzeix|millennium]"; exit 2 ;;
esac
log "done. Full calibration: python3 scripts/calibrate.py   (about 15 min; needs ket for evidence CIDs, or --no-ket)"
