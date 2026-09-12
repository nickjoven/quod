#!/bin/bash
# transition-emitting tier-A runs, back to back (one Lean process at a time):
# the 5,410 sample_mod-46 parent theorems, then their 6,152 elaborated mutants
set -u
cd "$(dirname "$0")/.."
export KET_HOME=$HOME/code/quod/.ket
python3 -u scripts/attempt.py --corpus corpus/full-20260908b --sample-mod 46 --run-id theorems-A-t1 --out attempts/theorems-A-t1 --timeout 120 --start-timeout 900 > attempts/theorems-A-t1/driver.log 2>&1
echo "theorems-A-t1 exit $?" >> attempts/theorems-A-t1/driver.log
python3 -u scripts/attempt.py --corpus corpus/full-20260908b --mutate --mutants corpus/mutants-20260911 --sample-mod 46 --run-id mutants-A-t1 --out attempts/mutants-A-t1 --timeout 120 --start-timeout 900 > attempts/mutants-A-t1/driver.log 2>&1
echo "mutants-A-t1 exit $?" >> attempts/mutants-A-t1/driver.log
