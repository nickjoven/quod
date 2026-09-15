#!/bin/bash
# rerun build.sh until it exits 0 (lake is incremental) or 6 attempts; record memory pressure and OOM kills
cd "$(dirname "$0")"
for i in 1 2 3 4 5 6; do
  while ! grep -q '^build exit' build.log 2>/dev/null; do sleep 60; done
  rc=$(grep '^build exit' build.log | tail -1 | awk '{print $3}')
  echo "attempt $i exit $rc $(date -u +%H:%M:%SZ) oom_kills=$(dmesg 2>/dev/null | grep -c 'Out of memory' || echo n/a)" >> supervise.log
  [ "$rc" = 0 ] && { echo "DONE" >> supervise.log; exit 0; }
  cp build.log "build.attempt$i.log"; ./build.sh > build.log 2>&1
done
echo "GAVE UP" >> supervise.log
