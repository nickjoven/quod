#!/bin/bash
# tier B pilot launcher. Credentials come from ~/code/quod/.env (gitignored):
# VALID = API key, SPACE = workspace id. They are mapped into the SDK's
# variables for THIS process only; nothing here prints or stores them.
set -u
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
export ANTHROPIC_API_KEY="$VALID" ANTHROPIC_WORKSPACE_ID="$SPACE"
unset VALID SPACE
export KET_HOME=$HOME/code/quod/.ket PATH="$HOME/.elan/bin:$PATH"
exec python3 -u scripts/attempt_b.py --controls attempts/controls-1337.json --which pilot \
  --corpus corpus/full-20260908b --run-id pilot-B --out attempts/pilot-B \
  --model claude-opus-5 --effort high --rounds 16 --cap-cents 6000 \
  --price-in 2.5 --price-out 12.5 --timeout 300 --start-timeout 900 "$@"
