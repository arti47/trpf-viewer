#!/usr/bin/env bash
# Stop hook: block finishing if the app (HTML or geo.js data) changed without a matching CLAUDE.md update.
# Uses git (not mtimes, which checkout/merge rewrite): uncommitted HTML edits need CLAUDE.md edits too,
# and the last commit touching the HTML must not be newer than the last commit touching CLAUDE.md.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
C=CLAUDE.md
git rev-parse --git-dir >/dev/null 2>&1 && [ -f "$C" ] || exit 0
dirty() { ! git diff --quiet HEAD -- "$1" 2>/dev/null; }
tc=$(git log -1 --format=%ct -- "$C")
for H in trpf-view-sim-v4.html geo.js; do
  [ -f "$H" ] || continue
  if dirty "$H" && ! dirty "$C"; then
    echo "$H has uncommitted changes but $C does not: update CLAUDE.md to match before finishing." >&2; exit 2
  fi
  th=$(git log -1 --format=%ct -- "$H")
  if [ -n "$th" ] && [ -n "$tc" ] && [ "$th" -gt "$tc" ]; then
    echo "Last commit to $H is newer than last commit to $C: update CLAUDE.md to match before finishing." >&2; exit 2
  fi
done
exit 0
