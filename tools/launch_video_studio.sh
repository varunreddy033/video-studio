#!/usr/bin/env bash
# One click: bring this Mac's Video Studio up to date with GitHub main, restart it, check it, open it.
#
#   bash tools/launch_video_studio.sh        (the Desktop "Video Studio.command" runs this; tools/install_launcher.sh makes it)
#
# What it does, in order (it stops with a clear message at the first problem):
#   1. checks the background service (com.videostudio.server) runs THIS folder
#   2. checks there is no unsaved work: changed or new files, an unfinished merge/rebase  -> stops, changes nothing
#   3. checks GitHub can be reached and fetches origin
#   4. stops if local main has commits GitHub doesn't have (they would never reach GitHub)
#   5. asks before restarting while a video is rendering or queued (a restart stops that render)
#   6. switches to main (other branches keep their commits) and runs git pull --ff-only origin main
#   7. runs npm ci when package-lock.json changed (HyperFrames / Remotion versions); warns when setup.sh changed
#   8. restarts com.videostudio.server, waits until /login answers (200 or 302) from the NEW process
#   9. opens http://localhost:<PORT> in the default browser
# Never: git reset, stash, clean, force-push, or touching Tailscale (the tunnel and its Funnel address stay as they are).
#
# The whole script is one function that runs only after bash has read the entire file, so the git pull below can
# replace this file safely while it runs.
set -uo pipefail

launch_video_studio() {
  local LABEL="com.videostudio.server" TS_LABEL="com.videostudio.tailscale"
  local P PLIST UIDN PORT PY
  export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
  # quiet git: no pager, no editor, never prompt in the Terminal (a login problem fails with a message instead)
  export GIT_PAGER=cat GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=20
  P="${VS_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  UIDN="$(id -u)"

  local B G R Y N
  if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; N=$'\033[0m'; else B= G= R= Y= N=; fi
  step() { printf '\n%s== %s%s\n' "$B" "$1" "$N"; }
  ok()   { printf '   %s✓%s %s\n' "$G" "$N" "$1"; }
  warn() { printf '   %s!%s %s\n' "$Y" "$N" "$1"; }
  die()  {
    printf '\n%s✗ %s%s\n' "$R$B" "$1" "$N"
    shift
    local line; for line in "$@"; do printf '  %s\n' "$line"; done
    printf '\n%sVideo Studio was NOT restarted by this run.%s\n' "$B" "$N"
    exit 1
  }

  printf '%sVideo Studio launcher%s  (%s)\n' "$B" "$N" "$P"

  # ------------------------------------------------------------------ 1. the service and this folder
  step "1/8 Background service"
  [ -d "$P/.git" ] || die "$P is not the project folder (no .git)." "Re-make the launcher: bash <project folder>/tools/install_launcher.sh"
  [ -f "$PLIST" ] || die "The background service isn't installed ($PLIST is missing)." \
    "Install it once: bash \"$P/tools/install_autostart.sh\""
  local WD
  WD="$(plutil -extract WorkingDirectory raw "$PLIST" 2>/dev/null || true)"
  if [ "$(cd "$WD" 2>/dev/null && pwd -P)" != "$(cd "$P" && pwd -P)" ]; then
    die "The background service runs a different folder than this launcher." \
      "service:  ${WD:-<not set>}" "launcher: $P" \
      "Point the service at the right copy (bash <that copy>/tools/install_autostart.sh) or re-make the launcher there."
  fi
  ok "$LABEL runs $P"
  PY="$P/bin/python"
  [ -x "$PY" ] || die "$PY is missing (the project's Python)." "Run setup.sh once in the project folder."
  PORT="$(grep -E '^[[:space:]]*PORT=' "$P/.env" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d ' "'"'"'\r')"
  PORT="${PORT:-8765}"

  cd "$P" || die "Can't open $P."
  command -v git >/dev/null || die "git isn't installed." "Install the Xcode command line tools: xcode-select --install"

  # ------------------------------------------------------------------ 2. unsaved work
  step "2/8 Unsaved work"
  local GD
  GD="$(git rev-parse --git-dir)"
  if [ -e "$GD/MERGE_HEAD" ] || [ -d "$GD/rebase-merge" ] || [ -d "$GD/rebase-apply" ] || [ -e "$GD/CHERRY_PICK_HEAD" ]; then
    die "A merge, rebase or cherry-pick is half done in $P." \
      "Finish or abort it first (ask Claude: \"finish the merge in my project folder\"). Nothing was changed."
  fi
  local DIRTY
  DIRTY="$(git status --porcelain)"
  if [ -n "$DIRTY" ]; then
    printf '%s\n' "$DIRTY" | head -20 | sed 's/^/     /'
    [ "$(printf '%s\n' "$DIRTY" | wc -l)" -gt 20 ] && echo "     ... and more"
    die "There are changed or new files in the project folder (listed above)." \
      "Nothing was changed, stashed or deleted. To continue, keep the work first:" \
      "  - commit it on a branch (ask Claude: \"commit my changes on a new branch\"), or" \
      "  - if you don't need it, ask Claude to look at it and undo it with you." \
      "Then double-click the launcher again."
  fi
  local CUR PREV
  CUR="$(git symbolic-ref --short -q HEAD || true)"
  PREV="$(git rev-parse HEAD)"
  if [ -z "$CUR" ] && [ -z "$(git branch --contains HEAD 2>/dev/null)" ]; then
    die "The folder is on a commit that belongs to no branch ($(git rev-parse --short HEAD))." \
      "Switching to main would leave it behind. Put it on a branch first: git switch -c raju/<name>"
  fi
  ok "no changed or new files (on ${CUR:-commit $(git rev-parse --short HEAD)})"

  # ------------------------------------------------------------------ 3. GitHub
  step "3/8 GitHub"
  git ls-remote --exit-code origin refs/heads/main >/dev/null 2>&1 \
    || die "Can't reach GitHub (origin = $(git remote get-url origin 2>/dev/null))." \
      "Check the internet connection and the GitHub login (gh auth status), then try again."
  git fetch --prune origin >/dev/null 2>&1 || die "git fetch from GitHub failed." "Try again in a minute; if it keeps failing: gh auth status"
  ok "fetched origin ($(git remote get-url origin))"

  # ------------------------------------------------------------------ 4. local main vs GitHub main
  step "4/8 Local main vs GitHub main"
  if git show-ref --verify --quiet refs/heads/main; then
    local AHEAD BEHIND
    AHEAD="$(git rev-list --count origin/main..main)"
    BEHIND="$(git rev-list --count main..origin/main)"
    if [ "$AHEAD" -gt 0 ]; then
      git log --oneline origin/main..main | head -10 | sed 's/^/     /'
      die "Local main has $AHEAD commit(s) that GitHub's main doesn't have (listed above)." \
        "They would never reach GitHub this way. Move them to a branch + PR (ask Claude), then try again." \
        "Nothing was changed."
    fi
    ok "local main is $BEHIND commit(s) behind GitHub, 0 ahead"
  else
    ok "no local main yet; it will be made from GitHub's main"
  fi

  # ------------------------------------------------------------------ 5. renders in progress
  step "5/8 Renders in progress"
  local TOKEN BUSY
  TOKEN="$(grep -E '^[[:space:]]*RENDER_TOKEN=' "$P/.env" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d ' "'"'"'\r')"
  BUSY="$(curl -s --max-time 5 -H "X-Render-Token: $TOKEN" -H "X-VS: 1" "http://127.0.0.1:$PORT/api/jobs" 2>/dev/null \
    | "$PY" -c 'import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for j in (d if isinstance(d, list) else d.get("jobs", [])):
    if j.get("status") in ("rendering", "queued"):
        print("%s: %s (%s)" % (j.get("status"), j.get("title") or j.get("id"), j.get("stage") or ""))' 2>/dev/null || true)"
  if [ -n "$BUSY" ]; then
    printf '%s\n' "$BUSY" | sed 's/^/     /'
    printf '   %sRestarting now STOPS these renders (press Make draft / final again afterwards).%s\n' "$Y" "$N"
    local ANS=""
    read -r -p "   Restart anyway? [y/N] " ANS || true
    case "$ANS" in y|Y|yes|YES) warn "restarting while rendering (you said yes)";;
      *) die "Stopped so the render can finish." "Nothing was changed. Double-click the launcher again when it's done.";; esac
  else
    ok "nothing rendering or queued"
  fi

  # ------------------------------------------------------------------ 6. switch to main + pull
  step "6/8 Update to GitHub main"
  if [ "$CUR" != "main" ]; then
    if git show-ref --verify --quiet refs/heads/main; then
      git switch main >/dev/null 2>&1 || die "Couldn't switch to main." "$(git switch main 2>&1 | tail -3)"
    else
      git switch -c main --track origin/main >/dev/null 2>&1 || die "Couldn't create main from GitHub."
    fi
    ok "switched from ${CUR:-a detached commit} to main (${CUR:-that commit} keeps its commits)"
  fi
  local PULL
  PULL="$(git pull --ff-only origin main 2>&1)" \
    || die "git pull --ff-only origin main failed (nothing was overwritten):" "$(printf '%s' "$PULL" | tail -5)"
  local NEW
  NEW="$(git rev-parse HEAD)"
  [ "$NEW" = "$(git rev-parse origin/main)" ] || die "Local main doesn't match GitHub's main after the pull." "Ask Claude to check the folder."
  if [ "$PREV" = "$NEW" ]; then
    ok "already up to date"
  elif git merge-base --is-ancestor "$PREV" "$NEW"; then
    ok "updated: $(git rev-list --count "$PREV..$NEW") new commit(s)"
    git log --oneline --no-decorate "$PREV..$NEW" | head -10 | sed 's/^/     /'
  else
    ok "the code is now GitHub's main (it was ${CUR:-commit} at $(git rev-parse --short "$PREV"); that branch is unchanged)"
  fi
  printf '   latest: %s\n' "$(git log -1 --format='%h %s (%cr, by %an)')"

  # ------------------------------------------------------------------ 7. dependencies
  step "7/8 Dependencies"
  local CHANGED
  CHANGED="$(git diff --name-only "$PREV" "$NEW" 2>/dev/null || true)"
  if printf '%s\n' "$CHANGED" | grep -qx 'package-lock.json'; then
    warn "package-lock.json changed: npm ci (HyperFrames / GSAP / icon packs)"
    npm ci --no-fund --no-audit --loglevel=error || die "npm ci failed in $P." "Check the internet connection and try again."
    ok "npm ci done"
  fi
  if printf '%s\n' "$CHANGED" | grep -qx 'motion/package-lock.json'; then
    warn "motion/package-lock.json changed: npm ci in motion/ (Remotion)"
    (cd "$P/motion" && npm ci --no-fund --no-audit --loglevel=error) || die "npm ci in motion/ failed." "Check the internet connection and try again."
    ok "npm ci in motion/ done"
  fi
  if printf '%s\n' "$CHANGED" | grep -qx 'setup.sh'; then
    warn "setup.sh changed: new tools or Python packages may be needed. When you have a few minutes: bash \"$P/setup.sh\""
  fi
  printf '%s\n' "$CHANGED" | grep -qE '^(package-lock\.json|motion/package-lock\.json|setup\.sh)$' || ok "no dependency changes"

  # ------------------------------------------------------------------ 8. restart + health check
  step "8/8 Restart Video Studio"
  local OLDPID NEWPID CODE i
  OLDPID="$(launchctl print "gui/$UIDN/$LABEL" 2>/dev/null | awk '/^\tpid = /{print $3; exit}')"
  if ! launchctl kickstart -k "gui/$UIDN/$LABEL" 2>/dev/null; then
    warn "the service wasn't loaded; loading it"
    launchctl bootstrap "gui/$UIDN" "$PLIST" 2>/dev/null || true
    launchctl kickstart -k "gui/$UIDN/$LABEL" 2>/dev/null || die "launchctl couldn't start $LABEL." \
      "See $P/output/server.log, or reinstall the service: bash \"$P/tools/install_autostart.sh\""
  fi
  printf '   waiting for http://127.0.0.1:%s/login ' "$PORT"
  CODE=""
  for i in $(seq 1 90); do
    NEWPID="$(launchctl print "gui/$UIDN/$LABEL" 2>/dev/null | awk '/^\tpid = /{print $3; exit}')"
    if [ -n "$NEWPID" ] && [ "$NEWPID" != "$OLDPID" ]; then
      CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:$PORT/login" 2>/dev/null || true)"
      if [ "$CODE" = "200" ] || [ "$CODE" = "302" ]; then break; fi
    fi
    printf '.'
    sleep 1
  done
  echo
  if [ "$CODE" != "200" ] && [ "$CODE" != "302" ]; then
    echo "   last lines of output/server.log:"
    tail -25 "$P/output/server.log" 2>/dev/null | sed 's/^/     /'
    die "Video Studio didn't come back within 90 s (last answer: ${CODE:-none})." \
      "The error is usually in the log lines above. Ask Claude to look at output/server.log."
  fi
  ok "running (pid $NEWPID), /login answered $CODE"

  # Tailscale: read only. Never restarted here, so the Funnel address stays the same.
  if launchctl print "gui/$UIDN/$TS_LABEL" 2>/dev/null | grep -q 'state = running'; then
    local SOCK URL
    SOCK="$HOME/Library/Application Support/vs-tailscale/tailscaled.sock"
    URL="$(tailscale --socket="$SOCK" funnel status 2>/dev/null | grep -oE 'https://[^ ]+' | head -1 || true)"
    ok "Tailscale tunnel running${URL:+: $URL}"
  else
    warn "the Tailscale tunnel service isn't running (Video Studio works on this Mac; the online address doesn't)."
  fi

  open "http://localhost:$PORT" 2>/dev/null || warn "couldn't open the browser; go to http://localhost:$PORT"
  printf '\n%s%s✓ Video Studio is up to date and running: http://localhost:%s%s\n' "$G" "$B" "$PORT" "$N"
  printf '  code: main %s  ·  this window can be closed.\n' "$(git rev-parse --short HEAD)"
}

launch_video_studio "$@"; exit $?
