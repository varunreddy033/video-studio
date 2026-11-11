# Working together on this repo (Varun + Raju)

We both push to this one repository: github.com/varunreddy033/youtube-pipeline. Nobody forks it, nobody keeps a
second copy as "upstream". These rules keep us from breaking each other's work. Claude Code follows the same rules
(they are also in CLAUDE.md), so you can simply ask it to "start a task", "open the PR" or "merge it".

## Every task, start to finish

1. **Get the latest code first.**
   ```bash
   cd ~/youtube-pipeline && git switch main && git pull --rebase
   ```
2. **Make a short branch for the task**, named after you and the task, for example `varun/style-tab` or
   `raju/arcade-fix`:
   ```bash
   git switch -c raju/arcade-fix
   ```
   One branch = one task. Keep it small; if a task grows, finish a part and start another branch.
3. **Work and commit on that branch.** Before every commit run the secret check; it must say `clean`:
   ```bash
   bash tools/check_secrets.sh && git commit -am "What changed, in one line"
   ```
4. **Test before you share.** All three must pass:
   - `bin/python tools/check_presets.py` says `presets: clean`
   - a draft of `docs/sample_motion_gfx_script.md` renders (Video Studio: New video, Load sample with Pictures =
     Motion graphics, Check, Draft first)
   - a draft of `docs/sample_script.md` renders (Load sample with Pictures = AI images)
5. **Open a pull request and merge it the same day** (squash = the whole branch becomes one clean commit on main,
   and the branch is deleted):
   ```bash
   git push -u origin HEAD
   gh pr create --fill
   gh pr merge --squash --delete-branch
   git switch main && git pull --rebase
   ```
   If the other person is working on the same files, tell them before you merge.
6. **Restart Video Studio** so it runs the new code:
   `launchctl kickstart -k gui/$(id -u)/com.videostudio.server`

## Never

- Never force-push `main` (`git push --force` on main deletes the other person's work).
- Never commit: `.env`, `data/` (logins), `output/` (videos), `models/`, the generated icon packs and search index
  (`assets/library/icons/*/icons.json`, `index.json`, `embeddings.npy`), character pack images, or licensed music
  (`assets/audio/`). `.gitignore` already keeps them out; don't force-add them.
- Never push code that doesn't work or wasn't tested (step 4).

## Your own notes: CLAUDE.local.md

`CLAUDE.md` is shared: how the pipeline works, decisions, status. Things that are only about **you** (your Mac,
your accounts, your Tailscale address, your to-dos) go in `CLAUDE.local.md` in the project folder. It is in
`.gitignore`, so it never leaves your Mac. Claude Code reads both files.

## If two of us changed the same lines

`git pull --rebase` (step 1) stops and names the file. Ask Claude Code to "resolve the conflict and keep both
changes", check the result, then `git rebase --continue`. If unsure, ask the other person.

## Only Varun

The public copy (github.com/varunreddy033/video-studio) is made by `tools/publish_public.py`, which only Varun runs.
`scripts/`, `PRIVATE.md` and the paths in `.publicignore` never go public.
