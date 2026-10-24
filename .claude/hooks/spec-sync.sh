#!/usr/bin/env bash
# Stop hook: block finishing if the app HTML is newer than CLAUDE.md.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
[ -f trpf-view-sim-v4.html ] && [ -f CLAUDE.md ] || exit 0
if [ trpf-view-sim-v4.html -nt CLAUDE.md ]; then
  echo "trpf-view-sim-v4.html changed after CLAUDE.md: update CLAUDE.md to match before finishing." >&2
  exit 2
fi
exit 0
