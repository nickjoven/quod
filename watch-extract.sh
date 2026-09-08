#!/usr/bin/env bash
# Liveness probe for the quod corpus extraction. Read-only; safe to run, stop,
# and rerun in any terminal. Follows the run by cmdline (not pid), so it keeps
# working across a --resume-after relaunch. Breaks with a verdict on every
# terminal state — a quiet death is never mistaken for "still running".
#
#   bash ~/code/quod/watch-extract.sh          # assumes a 15 GB cap
#   bash ~/code/quod/watch-extract.sh 24       # after a wsl --shutdown to 24 GB
set -u
QUOD="$HOME/code/quod"
PAT='corpus_extract.py'
CAP_GB="${1:-15}"
gb() { awk -v k="$1" 'BEGIN{printf "%.1f", k/1048576}'; }   # KB -> GB

while true; do
  clear 2>/dev/null || true
  pid=$(pgrep -f "$PAT" | head -1)
  leanpid=$(pgrep -f 'CorpusWalk.lean' | head -1)
  log=$(ls -t "$QUOD"/corpus/extract-*.log 2>/dev/null | head -1)
  outdir=$(ls -dt "$QUOD"/corpus/full-* 2>/dev/null | head -1)

  echo "== quod extraction liveness @ $(date '+%H:%M:%S') =="
  if [ -n "$pid" ]; then
    echo "STATE : RUNNING   driver pid $pid   elapsed $(ps -o etime= -p "$pid" | tr -d ' ')"
  else
    echo "STATE : no driver process"
  fi

  if [ -n "$leanpid" ]; then
    rss=$(ps -o rss= -p "$leanpid" | tr -d ' ')
    g=$(gb "$rss")
    pct=$(awk -v g="$g" -v c="$CAP_GB" 'BEGIN{printf "%.0f", 100*g/c}')
    echo "MEM   : lean $leanpid  ${g} GB / ${CAP_GB} GB cap  (${pct}%)"
  fi

  echo "RECORDS on disk: $(cat "$outdir"/*.jsonl 2>/dev/null | wc -l)"
  if [ -n "$log" ]; then
    grep -E 'declarations selected|[0-9]+/[0-9]+ *$' "$log" 2>/dev/null | tail -1 | sed 's/^/PROGRESS: /'
    echo "--- last log ---"; tail -2 "$log"
  fi

  # terminal states
  if [ -n "$log" ] && grep -q 'extracted ' "$log"; then
    echo; echo "== DONE =="; grep -E 'manifest CID|extracted ' "$log"; break
  fi
  if [ -z "$pid" ]; then
    echo; echo "== DRIVER GONE =="
    if [ -n "$log" ] && grep -qE 'lean exited|zero records|Traceback|OOM|Killed' "$log"; then
      echo "FAILED — cause:"; grep -E 'lean exited|zero records|Traceback|OOM|Killed' "$log" | tail -3
    else
      echo "vanished with no completion line (reboot / OOM-kill / manual kill?); last log above"
      echo "resume:  cd $QUOD && export PATH=\$HOME/.elan/bin:\$PATH KET_HOME=$QUOD/.ket"
      echo "         LAST=\$(cat $outdir/*.jsonl | tail -1 | python3 -c 'import json,sys;print(json.loads(sys.stdin.read())[\"name\"])')"
      echo "         python3 scripts/corpus_extract.py --resume-after \"\$LAST\" --out corpus/full-20260907-resume"
    fi
    break
  fi
  sleep 5
done
