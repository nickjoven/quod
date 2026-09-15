#!/bin/bash
# Intake build at OpenAI's pin (step 1 of the intake scope). Wall clock recorded; nothing typed by hand.
set -u
cd "$(dirname "$0")"
export PATH="$HOME/.elan/bin:$PATH"
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ -f PIN-verified.txt ] && grep -q '^verified' PIN-verified.txt || { echo "PIN not verified; refusing"; exit 1; }
cd repo
elan toolchain install "$(cat lean-toolchain)" 2>&1 | tail -2
echo "toolchain $(lean --version) $(date -u +%H:%M:%SZ)"
lake exe cache get 2>&1 | tail -3
echo "cache done $(date -u +%H:%M:%SZ)"
# the two demonstranda live in ComparatorChallenges/NavierStokes.lean; their proofs in NavierStokes/ComparatorSolution.lean
taskset -c 0-5 lake build NavierStokes.ComparatorSolution ComparatorChallenges.NavierStokes 2>&1 | tail -40
echo "build exit ${PIPESTATUS[0]} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
