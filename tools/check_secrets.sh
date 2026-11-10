#!/usr/bin/env bash
# Run before every commit:      bash tools/check_secrets.sh
#   Looks at what is staged (git add) and fails if anything looks like a real key or token, or if personal data
#   (a Tailscale address, a Gmail address) is staged outside the private-only files listed in .publicignore.
# Full history:                 bash tools/check_secrets.sh --history
#   Scans EVERY commit on every branch (all diffs + every file name ever committed), and also reports personal
#   data, which editing files can't remove: it stays in old commits.
# (Each pattern needs real characters right after the prefix, so this file can't match itself.)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

SECRET_RE='RENDER_TOKEN=[0-9a-f]{16,}|FAL_KEY=[A-Za-z0-9:_-]{16,}|PEXELS_API_KEY=[A-Za-z0-9]{16,}|HF_TOKEN=hf_[A-Za-z0-9]{16,}|hf_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}'
BLOCKED_RE='(^|/)\.env($|\.)|n8n_data_backup|^output/|^models/|^assets/audio/|^data/|users\.json$'
PERSONAL_RE='[A-Za-z0-9-]+\.tail[0-9a-f]{6}\.ts\.net|[A-Za-z0-9._%+-]+@gmail\.com'

bad=0
if [ "${1:-}" = "--history" ]; then
  n=$(git rev-list --all | wc -l | tr -d ' ')
  echo "scanning full history: $n commits on all branches"
  files=$(git log --all --pretty=format: --name-only | sort -u | grep -E "$BLOCKED_RE" | grep -v '\.env\.example$')
  if [ -n "$files" ]; then echo "FOUND files that should never be committed:"; echo "$files"; bad=1; fi
  hits=$(git log --all -p --pretty=format:'@@commit %h %ad' --date=short | grep -E "^@@commit|$SECRET_RE" \
         | grep -B1 -E "$SECRET_RE" | grep -v '^--$')
  if [ -n "$hits" ]; then echo "FOUND something that looks like a secret:"; echo "$hits"; bad=1; fi
  personal=$(git log --all -p --pretty=format:'@@commit %h %ad %s' --date=short | grep -E "^@@commit|$PERSONAL_RE" \
             | grep -B1 -E "$PERSONAL_RE" | grep -v '^--$')
  if [ -n "$personal" ]; then
    echo "PERSONAL DATA in history (fine in the private repo; never publish this repo's history as-is):"
    echo "$personal" | cut -c1-200
    echo "  -> in the current files: $(git grep -l -I -E "$PERSONAL_RE" -- . | tr '\n' ' ')"
  fi
  if [ "$bad" -eq 0 ]; then echo "history secret check: clean (no keys, no blocked files)"; fi
  exit $bad
fi

blocked=$(git diff --cached --name-only | grep -E "$BLOCKED_RE" | grep -v '\.env\.example$')
if [ -n "$blocked" ]; then
  echo "BLOCKED: these files must never be committed:"; echo "$blocked"; bad=1
fi
hits=$(git diff --cached -U0 | grep -nE "$SECRET_RE")
if [ -n "$hits" ]; then
  echo "BLOCKED: staged changes contain something that looks like a secret:"; echo "$hits"; bad=1
fi

# personal data may only go in private-only paths (.publicignore, e.g. PRIVATE.md)
excl=()
if [ -f .publicignore ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="$(printf '%s' "$line" | tr -d '[:space:]')"
    [ -z "$line" ] && continue
    case "$line" in
      */) excl+=(":(exclude,glob)${line}**") ;;
      *)  excl+=(":(exclude,glob)${line}") ;;
    esac
  done < .publicignore
fi
personal=$(git diff --cached -U0 -- . ${excl[@]+"${excl[@]}"} | grep '^+' | grep -nE "$PERSONAL_RE")
if [ -n "$personal" ]; then
  echo "BLOCKED: personal data (Tailscale address / Gmail) staged outside the private-only files in"
  echo ".publicignore. Put it in PRIVATE.md instead:"; echo "$personal"; bad=1
fi

if [ "$bad" -eq 0 ]; then echo "secret check: clean"; fi
exit $bad
