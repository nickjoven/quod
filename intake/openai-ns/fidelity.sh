#!/bin/bash
# Fidelity locks: the ported DeepMind statements and every custom structure's constructor type,
# on both sides, canonical strings compared with the namespace normalized. Evidence only; never a status.
set -u
cd "$(dirname "$0")/../.."
export PATH="$HOME/.elan/bin:$PATH"
P=intake/openai-ns/repo; E=intake/openai-ns/evidence/fidelity; mkdir -p "$E"
lock() { timeout 900 python3 scripts/lock.py "$P" "$1" "$2" --json > "$E/$3.json" 2>&1; }
for side in "Intake.UpstreamNavierStokes NavierStokes.Upstream upstream" "ComparatorChallenges.NavierStokes NavierStokes.Comparator adapted"; do
  read -r mod ns tag <<< "$side"
  for d in navier_stokes_breakdown_R3 navier_stokes_breakdown_periodic \
           InitialVelocityConditionDecay.mk ForceConditionDecay.mk NavierStokesExistenceAndSmoothnessRn.mk \
           InitialVelocityConditionPeriodic.mk ForceConditionPeriodic.mk NavierStokesExistenceAndSmoothnessPeriodic.mk \
           InitialVelocityConditionDecay ForceConditionDecay NavierStokesExistenceAndSmoothnessRn \
           InitialVelocityConditionPeriodic ForceConditionPeriodic NavierStokesExistenceAndSmoothnessPeriodic; do
    lock "$mod" "$ns.$d" "$tag--$d"
  done
done
echo "locks done $(date -u +%H:%M:%SZ)"
