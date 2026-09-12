#!/bin/bash
# ladder-S (stepping prover) control runs, back to back: 200-theorem pilot
# (P_S frozen from it), the prover-negative control on the same 200, then
# the 200-theorem test set. Sets come from attempts/controls-4242.json.
set -u
cd "$(dirname "$0")/.."
export KET_HOME=$HOME/code/quod/.ket
export PATH="$HOME/.elan/bin:$PATH"
PILOT=$(python3 -c "import json; print(','.join(json.load(open('attempts/controls-4242.json'))['pilot']))")
TEST=$(python3 -c "import json; print(','.join(json.load(open('attempts/controls-4242.json'))['test']))")
mkdir -p attempts/pilot-S attempts/pilot-S-neg attempts/test200-S
python3 -u scripts/attempt.py --corpus corpus/full-20260908b --prover step --only "$PILOT" --run-id pilot-S --out attempts/pilot-S --timeout 300 --start-timeout 900 > attempts/pilot-S/driver.log 2>&1
echo "pilot-S exit $?" >> attempts/pilot-S/driver.log
python3 -u scripts/attempt.py --corpus corpus/full-20260908b --prover step --negate --only "$PILOT" --run-id pilot-S-neg --out attempts/pilot-S-neg --timeout 300 --start-timeout 900 > attempts/pilot-S-neg/driver.log 2>&1
echo "pilot-S-neg exit $?" >> attempts/pilot-S-neg/driver.log
python3 -u scripts/attempt.py --corpus corpus/full-20260908b --prover step --only "$TEST" --run-id test200-S --out attempts/test200-S --timeout 300 --start-timeout 900 > attempts/test200-S/driver.log 2>&1
echo "test200-S exit $?" >> attempts/test200-S/driver.log
