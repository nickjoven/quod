#!/usr/bin/env python3
"""lessons.py - query the cold lessons ledger (AGENTS.md item 8d).

Usage: lessons.py <keyword> [keyword ...]
       lessons.py --all

Matches keywords (case-insensitive substrings) against each
entry's TRIGGERS line and title; prints matching entries in full.
A registration's method block cites the L-n ids this returns.
Exit 0 with matches, 3 with none (so a wrapper can insist).
"""
import re
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
    text = open(root + "/LESSONS.md").read()
    entries = re.split(r"\n(?=## L-)", text)
    header, entries = entries[0], entries[1:]
    if "--all" in sys.argv:
        hits = entries
    else:
        keys = [k.lower() for k in sys.argv[1:]]
        hits = []
        for e in entries:
            m = re.search(r"TRIGGERS:(.*)", e)
            hay = (e.splitlines()[0] + " "
                   + (m.group(1) if m else "")).lower()
            if any(k in hay for k in keys):
                hits.append(e)
    if not hits:
        print("no lessons match; if the domain is genuinely new, "
              "say so in the registration's method block")
        sys.exit(3)
    for e in hits:
        print(e.rstrip() + "\n")
    ids = [e.split()[1] for e in hits]
    print("cite:", ", ".join(ids))


if __name__ == "__main__":
    main()
