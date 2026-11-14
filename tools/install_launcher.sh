#!/usr/bin/env bash
# Make the Desktop launcher "Video Studio.command" for THIS copy of the project (safe to re-run; it only rewrites
# that one file). Double-clicking it runs tools/launch_video_studio.sh: update to GitHub main, restart Video Studio,
# check it, open the browser.
#
#   bash tools/install_launcher.sh             -> ~/Desktop/Video Studio.command
#   bash tools/install_launcher.sh remove      -> deletes that one Desktop file
set -euo pipefail
P="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # the project folder (one up from tools/)
OUT="$HOME/Desktop/Video Studio.command"

if [ "${1:-}" = "remove" ]; then
  rm -f "$OUT"
  echo "Removed $OUT"
  exit 0
fi

cat > "$OUT" <<EOF
#!/bin/bash
# Video Studio launcher for $P
# (made by tools/install_launcher.sh; re-run that to remake it). Double-click: update to GitHub main, restart
# Video Studio, check it, open the browser. Stops with a message instead of overwriting unsaved work.
REPO="$P"
S="\$REPO/tools/launch_video_studio.sh"
TMP=""
if [ ! -f "\$S" ]; then
  # this copy is on a branch without the launcher script: run GitHub main's copy of it
  TMP="\$(mktemp -t vs_launch)"
  if ! git -C "\$REPO" show origin/main:tools/launch_video_studio.sh > "\$TMP" 2>/dev/null; then
    echo "The launcher script isn't in \$REPO (this branch) or on GitHub main yet."
    echo "Ask Claude to merge the launcher PR, or switch the project folder to the branch that has it."
    rm -f "\$TMP"
    read -n 1 -s -r -p "Press any key to close this window."; echo
    exit 1
  fi
  S="\$TMP"
fi
VS_REPO="\$REPO" bash "\$S"
rc=\$?
[ -n "\$TMP" ] && rm -f "\$TMP"
if [ \$rc -ne 0 ]; then
  echo
  read -n 1 -s -r -p "Something went wrong (see the message above). Press any key to close this window."
  echo
fi
exit \$rc
EOF
chmod +x "$OUT"
echo "ok: $OUT (runs $P/tools/launch_video_studio.sh)"
