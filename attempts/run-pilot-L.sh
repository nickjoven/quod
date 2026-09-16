#!/bin/bash
# tier L launcher: a local llama.cpp server on the GPU (port from the homeserv table), then the
# batch-round protocol against it. No credentials, no spend; wall clock is the cost. Usage:
#   RUN_ID=pilot-L attempts/run-pilot-L.sh --which pilot --rounds 16 [extra attempt_b args]
set -u
cd "$(dirname "$0")/.."
export KET_HOME=$HOME/code/quod/.ket PATH="$HOME/.elan/bin:$PATH"
MODEL=${MODEL:-models/goedel-prover-v2-8b-q4km.json}
GGUF=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['file'])" "$MODEL")
SERVER=${SERVER:-$HOME/src/llama.cpp/build/bin/llama-server}
SLOTS=${SLOTS:-4}
PORT=$(homeserv-port claim llama-primary) || { echo "llama-primary port busy"; exit 1; }
"$SERVER" -m "$GGUF" --host 127.0.0.1 --port "$PORT" -ngl 99 -np "$SLOTS" -c $((8192 * SLOTS)) --log-disable > "attempts/${RUN_ID:-pilot-L}-server.log" 2>&1 &
SPID=$!
trap 'kill $SPID 2>/dev/null; homeserv-port release "$PORT" >/dev/null' EXIT
for i in $(seq 1 90); do curl -s "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break; sleep 2; done
curl -s "http://127.0.0.1:$PORT/health" | grep -q '"ok"' || { echo "server did not come up (see attempts/${RUN_ID:-pilot-L}-server.log)"; exit 1; }
exec python3 -u scripts/attempt_b.py --controls attempts/controls-2026.json --corpus corpus/full-20260908b \
  --run-id "${RUN_ID:-pilot-L}" --out "attempts/${RUN_ID:-pilot-L}" \
  --backend openai-compat --base-url "http://127.0.0.1:$PORT/v1" --model goedel-prover-v2-8b-q4km --weights "$MODEL" \
  --prover-name tier-L-goedel-v2-8b --prompt-style goedel --temperature 0.6 --repeat-penalty 1.1 --workers "$SLOTS" \
  --max-tokens 2000 --cap-cents 1 --timeout 300 --start-timeout 900 --tier-a-run /nonexistent "$@"
