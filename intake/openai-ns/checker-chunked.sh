#!/bin/bash
# Independent replay in bounded chunks: a fresh lean4checker process per CHUNK modules (memory), every exit recorded.
cd "$(dirname "$0")/repo"; export PATH="$HOME/.elan/bin:$PATH"
CHUNK=${CHUNK:-15}
grep -v '^Intake' ../evidence/closure-modules.txt > ../evidence/checker-modules.txt
total=$(wc -l < ../evidence/checker-modules.txt)
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) modules=$total chunk=$CHUNK checker_sha256=$(sha256sum ../lean4checker/.lake/build/bin/lean4checker | cut -d' ' -f1)" > ../evidence/checker-chunks.log
i=0; fail=0
while read -r -a mods; do
  i=$((i+1)); t0=$(date +%s)
  lake env ../lean4checker/.lake/build/bin/lean4checker "${mods[@]}" > "../evidence/checker-chunk-$i.log" 2>&1; rc=$?
  [ "$rc" = 0 ] || fail=$((fail+1))
  echo "chunk $i n=${#mods[@]} exit=$rc elapsed=$(( $(date +%s) - t0 ))s first=${mods[0]}" >> ../evidence/checker-chunks.log
done < <(xargs -n "$CHUNK" < ../evidence/checker-modules.txt)
echo "done $(date -u +%Y-%m-%dT%H:%M:%SZ) chunks=$i failed_chunks=$fail" >> ../evidence/checker-chunks.log
