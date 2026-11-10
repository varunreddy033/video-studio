# Project: faceless YouTube automation (Varun)

Read this first in every session. It is the single source of truth for how this
pipeline works and what has already been decided. Don't re-propose decisions
marked DECIDED unless I ask.

## How I want you to work
- I'm new to Claude Code and was burned by inconsistent, half-baked instructions before.
  Give complete, working code only: no placeholders, no "adjust this to your setup".
- Run commands yourself instead of telling me to copy-paste them. Ask before deleting files.
- One step at a time. Verify each step (run it, check output) before saying it's done.
- Don't recommend a different architecture unless something is truly broken. If it is, say why in 2-3 lines.
- Prices in Indian rupees.
- Git (DECIDED 2026-11-08; two repos since 2026-11-10): after every change that is tested and working, commit
  and push it to the PRIVATE repo https://github.com/varunreddy033/youtube-pipeline (branch main) without asking
  me first. Then run `bin/python tools/publish_public.py` (also without asking): it copies the public part to the
  PUBLIC repo https://github.com/varunreddy033/video-studio as one commit, and refuses if anything private would
  leak. Private repo = everything; public repo = everything except PRIVATE.md and the paths in .publicignore
  (scripts/, planning notes, old/, n8n/). Private details (real addresses, accounts) go ONLY in PRIVATE.md.
  One clear commit per finished step. Never commit .env, old/n8n_data_backup_*, output/, models/, assets/audio/
  (all in .gitignore). Run tools/check_secrets.sh before every commit. Don't push broken or untested code.

## Goal
- 1 hour of new content per day (2x30 or 3x20 min preferred over 6x10: fewer uploads, less template-y).
- I pick a trending topic each day and write the script with Claude (chat). Videos must be good enough that
  viewers like them and must not look mass-produced (YouTube "inauthentic content" policy judges the channel).
- Cost: Rs 0/month. Everything runs on the Mac or on free services.

## Machine
- MacBook Air M5, 16 GB unified memory, 512 GB, fanless (long heavy renders throttle).
- macOS user: varunreddy. Project folder: ~/youtube-pipeline (it is also a Python 3.11 venv:
  ~/youtube-pipeline/bin/python).
- Installed: Homebrew, ffmpeg-full 9.0.2 (linked as `ffmpeg`: libass, loudnorm, h264_videotoolbox), python@3.11,
  espeak-ng, whisper-cpp (`whisper-cli`) + models/ggml-small.bin, kokoro 0.9.4, mflux 0.24, Pillow 13,
  matplotlib 3.11. Docker Desktop UNINSTALLED 2026-11-08 (not needed). Old/unused: FastVideo repo, kokoro-mlx.
- Image model: Runpod/FLUX.2-klein-4B-mflux-4bit (4.62 GB, Apache-2.0) in ~/.cache/huggingface/hub.
  Kept loaded during a render by pipeline/image_worker.py: 18-28 s per 1280x720 image (slower when the Mac is
  hot or swapping; the old one-process-per-image way took 20-30 s). Peak memory ~5.4 GB, freed after each render.

## Architecture (DECIDED 2026-11-08, final): "script.md -> Video Studio"
```
Claude chat (docs/CLAUDE_SCRIPT_PROMPT.md)  ->  script.md (docs/SCRIPT_FORMAT.md)
Video Studio web app  http://localhost:8765  (render_server.py = Flask, ui/index.html = plain HTML/JS)
  paste script -> Check -> Draft -> Final -> download -> manual upload in YouTube Studio
pipeline/
  script_parser.py  script.md -> segments (narration between shot tags) + shots; errors/warnings with line numbers
  voice.py          Kokoro-82M (am_michael) per segment, word timings from Kokoro (whisper.cpp backup), cached
  visuals.py        one clip per shot, cut exactly where its narration starts:
                      [ai: ...]     FLUX.2 klein (image_worker.py) + 8 alternating camera moves (draft: placeholder)
                      [stock: ...]  same as ai, styled as a documentary photo (no stock service)
                      [card] [number] [quote] [chart]  Pillow/matplotlib frames, animated in, then held
  captions.py       word-by-word highlighted .ass captions (amber current word)
  assemble.py       timeline -> clips (3 parallel) -> join -> voice + ducked BGM (full: per chapter, crossfaded)
                    + SFX -> loudnorm -14 LUFS (2-pass, linear) -> burn captions (bundled font) -> encoder.py
  clip.py           clip Shorts: source job's voice cache + cached images, 9:16 re-frame, Short captions, no new AI
  encoder.py        auto-detects h264_videotoolbox (Mac) / h264_nvenc (NVIDIA) / libx264 (VIDEO_ENCODER= forces)
  thumbnails.py     3 options 1280x720: 2 AI images (thumbnail_prompt) + 1 video frame, big text
  jobs.py           output/jobs/<id>/state.json, one-at-a-time render queue, progress, resume via cache/
  config.py / util.py  settings from .env, shared helpers
```
Draft = 960x540, AI images as placeholders (30 s video renders in ~5-15 s).
Final = 1920x1080 10 Mbps, real AI images, thumbnails, metadata.txt (title, description, chapters,
music credit, tags, upload checklist). 30 s test video: final in 65 s + 45 s thumbnails.
Job files: script.md, draft.mp4, final.mp4, thumb_1..3.jpg, metadata.txt, render.log, cache/ (voice, stock, AI).

## Video types (DECIDED + BUILT 2026-11-09, docs/VIDEO_TYPES.md)
- Dashboard has TWO buttons: Make Short / Make full video. Header `type: short | full` (default full). Presets in
  config.TYPES (size, hold limits, length limits, chapters, music, tail, captions, safe area, thumbnails, #Shorts).
- Short: 1080x1920, 15 s-2:00 (ERROR at Check outside that, and the render re-checks the real voice length),
  picture > 6 s warning (talk > 10 s), no chapters, one music track with a 0.5 s fade + 0.3 s tail (loops),
  captions 6.2% of height, kept out of the bottom 20% / right 12% (Shorts buttons); graphics drawn in that safe box.
  1 vertical cover from a frame (no AI), metadata gets #Shorts, upload pack = final, cover, metadata, srt.
- Clip Short: `clip_from: <job id>`, `clip_start`/`clip_end` (mm:ss); cut snaps to word gaps; [talk:] re-rendered
  vertical (centred), stills cropped 9:16 around the nearest part of the depth map, graphics re-drawn, audio =
  the source final's mix for that span re-normalised. Refuses if any image/voice isn't cached. Cover text = the
  source's `thumbnail:`. Full videos: `music: a, b, c` = one track per chapter (in order), 3 s crossfades.
- Full character finals still make the first-chapter Short automatically (now as type: short).
- Cross-platform (Mac + Windows Legion, same repo): bundled Barlow fonts (OFL) in assets/fonts (captions:
  libass `fontsdir`, family "Barlow Condensed ExtraBold"; the Avenir system fonts are no longer used), encoder
  auto-detect, all text files UTF-8, FFmpeg paths relative/forward-slash, pack.json paths resolved per machine
  (characters.pack_path). New AI images still need the Mac (mflux = Apple Silicon); elsewhere they fail clearly.
- Character packs move between machines with tools/export_character_pack.py <id> -> output/character_packs/*.zip
  and tools/import_character_pack.py <zip> (SHA-256 per file, completeness vs pack.json, character file must
  match unless --force, existing pack moved to assets/characters/_backup/ only with --force).

## Presenter videos (DECIDED 2026-11-08, docs/PRESENTER_PLAN.md)
- Script header `character: sterling` loads docs/characters/sterling.md (CHARACTER, STYLE, SEED 1000, voice
  bm_george 0.95, 7 poses, sets studio/stage). Tags: `[talk: pose | set | camera]` = lip-synced presenter,
  `[act: description | wide/medium/close | ref]` = the character in a scene. Check warns: talk > 25 s, 4+ shots
  without the character, chapters not opening on [talk:].
- Character pack (one-time per character): `bin/python tools/make_character_pack.py <name>` ->
  assets/characters/<name>/ (master, poses, mouths slight/wide/o/e/mbp + blink pasted back with feathered masks,
  rembg u2net cutouts, sets, pack.json, contact_sheet.jpg). Manual swaps: assets/characters/<name>/overrides.json
  ({"neutral": "master", "<pose>": "A"/"B"}). Sterling: neutral = master (the generated neutral was full-body).
- Lip sync = Kokoro's own phoneme timings (pipeline/presenter.py). Rhubarb's macOS build is x86-only and Rosetta
  isn't installed (installing it is a system change), so Rhubarb is NOT used.
- [act:] = fixed SEED + CHARACTER + STYLE via the shared image cache (assets/cache/images, reused across videos),
  8 s cool-down per new image. Depth parallax on every still in finals: Depth Anything V2 Small (Apache-2.0 ONLY).
- Finals of character videos also make: vertical Short (first chapter), 3 thumbnails (scene, cutout on set,
  frame), captions_final.srt, upload_pack.zip. If the pack isn't built, the final waits for it.
- Characters: docs/characters/{sterling,miso,biscuit,nova}.md (miso = converted from the docs/CHARACTER.md bible,
  SEED 1300 new). Loader reads "Kokoro x, speed y" or "Voice: x, speed y", "Presenter poses:" or "Poses:" (with
  "name (description)" for extra poses), and bare set names (default description). Body words NOUN / LIMBS / FUR /
  OUTFIT / EARS fill the pack, [act:] and thumbnail prompts; Sterling's words reproduce his old prompts exactly
  (checked: all 63 pack prompts identical, all 15 [act:] images + thumbnail still cached). [talk: pose] without a
  set = the character's first set. pack_ready() also checks the images exist (pack.json alone is in git).
- Lessons: never mention a person ("behind him", "presenter") in set prompts (the model draws one; the builder now
  rewrites those words); "a single cat" in an [act:] prompt adds a second cat (describe the place instead);
  poses with shut eyes (laughing) need "keep the eyes shut" in mouth edits and no blink edit.
- The Mac MUST be on the charger with the lid open for long jobs: on battery with the lid closed it sleeps and
  everything stops (this cost ~6 hours overnight on 2026-11-08).

## Decisions and why (don't undo these)
- Scripts are written by me with Claude in chat, pasted as script.md. No LLM API in the pipeline (Rs 0, and I
  review every fact). The Gemini script writer is retired (old/script_gen_gemini.py).
- n8n is RETIRED (synchronous 30-min render call broke long videos). n8n/ folder kept for reference.
  Docker is uninstalled; the old n8n_data volume (workflow + saved Gemini/YouTube credentials) is backed up in
  old/n8n_data_backup_20261108.tar.gz (private file, keep it off the internet).
  old/render_server_v1.py and old/index_v1.html are the previous versions (nothing deleted).
- NO stock video (DECIDED 2026-11-08): Pexels paused new API keys. Visual mix: ~65% AI images (6-10 s each,
  ~45-55 per 10 min) + ~35% cards/numbers/quotes/charts (3-6 s, instant). Parser warns above 12 s per photo shot,
  10 s per graphic. A 10-min final takes ~20-25 min (images cached, so re-renders only redo changed shots).
- Local images only: FLUX.2 klein 4B. Never klein 9B (non-commercial license). Fal/cloud images dropped.
- Voice: Kokoro (free). ElevenLabs / Gemini TTS too expensive at 1 hour/day.
- Loudness -14 LUFS (YouTube's playback level; quiet videos are not boosted).
- Mac hardware encoder h264_videotoolbox for every encode on the Mac (fast, cooler on the fanless Air);
  encoder.py picks nvenc/libx264 on other machines.
- Server binds 127.0.0.1:8765. Port 8765, NOT 5000 (macOS AirPlay Receiver).
- ONLINE (DECIDED 2026-11-08): reachable from anywhere at https://<your-name>.<your-tailnet>.ts.net through
  Tailscale Funnel (each person sets their own: their own Tailscale account, hostname and tailnet; mine is in
  PRIVATE.md, private repo only; `tailscale ... funnel status` prints it). Free, fixed HTTPS address,
  no router/domain. tailscaled runs in userspace mode (no admin password), state in ~/Library/Application Support/vs-tailscale. Funnel forwards to 127.0.0.1:8765.
- Every page/API needs a login (pipeline/auth.py): users in data/users.json (scrypt hashes, data/ is private and
  gitignored), signed 14-day session cookie (Secure over https), X-VS header + Origin check against CSRF,
  5 wrong passwords for a username -> that username locked 15 min (visitor IPs are hidden by the tunnel), security headers, 2 MB request cap. First account via /setup with the
  one-time code printed in output/server.log. The admin can add/remove users on the Account screen.
  tools: 19-check security test passed. The X-Render-Token header (from .env) still works for curl on this Mac.
- Friend: runs HIS OWN copy on HIS OWN Mac with his own login and Tailscale address (docs/FRIEND_SETUP.md).
  He clones the public repo (or, with collaborator access, the private one). No shared server.
- Upload is manual in YouTube Studio: the API project is unverified (uploads forced private) and Studio
  has thumbnail A/B tests and the AI-content disclosure checkbox.
- Local Wan 2.1 video generation DROPPED (14B for image-to-video, NVIDIA-only tooling, far too slow on 16 GB).
- Script rules: no invented facts/quotes about real people, no text/logos/real faces in AI prompts.

## Accounts / keys (.env; I paste them myself, never in chat or code)
- HF_TOKEN: optional Hugging Face read token for model downloads.
- YouTube: the channel account, manual upload in Studio.
- Unused now: RENDER_TOKEN, FAL_KEY lines in .env (harmless). Backups: output/.env.backup-20261108(b).

## Assets
- assets/audio/bgm = music beds (only files >= 60 s are used). `music:` in script.md matches file-name words.
- assets/audio/sfx = short effects, matched to [sfx: word] by file-name words, capped at 2.5 s.
- Cleaned 2026-11-08: 17 files moved to assets/audio/_unused (9 choir *patrikios* tracks, 4 duplicates, 4 non-music
  sounds). bgm now has 7 tracks (The Grey Room: A Dyin' Breed, At All Costs, Drop of a Hat, Misdirection,
  Missed My Chance, Soaring; Jeremy Korpas: Elysian Fields). sfx has 3 typing sounds.
- `music:` matches words in file names, so use a track name (misdirection, soaring, elysian ...); mood words like
  'dark' match nothing and pick a random track.
- Still missing SFX: whoosh, sub-drop, riser, glitch, shutter (I download these from the YouTube Audio Library).

## Current status (update this section as we go)
- [x] setup.sh run, ffmpeg-full installed, setup.sh filter-check bug fixed (2026-11-08)
- [x] FLUX.2 klein 4B downloaded and benchmarked (2026-11-08)
- [x] Full pipeline built (2026-11-08): parser, voice + word timings, visuals (stock/AI/card/number/quote/chart),
      word captions, ducked mix, -14 LUFS, videotoolbox, thumbnails, job queue, Video Studio page.
      Tested in the browser with docs/sample_script.md: Check -> draft (14 s) -> final (65 s) -> 3 thumbnails
      -> metadata, loudness measured -14.0 LUFS.
- [x] Pexels removed (keys paused); [stock:] now makes an AI documentary photo. Image model kept loaded
      (image_worker.py) with MLX cache clearing. Re-tested in the browser: draft 7 s, final 64 s, thumbnails OK.
- [ ] Optional: paste HF_TOKEN into .env.
- [x] Quit Docker Desktop (2026-11-08, n8n container stopped with it). Swap in use 12.3 -> 7.9 GB, AI images
      22-28 s -> 18-19.5 s each. Keep Docker closed while rendering; a Mac restart clears the leftover swap.
- [x] Mac restarted (swap 7.9 GB -> 4 MB). Docker Desktop uninstalled (app, helpers, CLI, 1.9 GB n8n image,
      2.2 GB data; disk free 337 -> 341 GB). Only an empty macOS-protected stub folder remains.
- [x] Asset folders cleaned (2026-11-08).
- [ ] I add whoosh/riser/sub-drop/glitch/shutter SFX to assets/audio/sfx.
- [x] First real video (2026-11-08): scripts/2026-11-08-ai-bubble.md, job 20261108-142648-792e8d.
      9:16 long, 76 shots (55 AI images incl. thumbnails, 23 graphics), -14.0 LUFS. Draft 66-119 s.
      Final 26 min (images avg 27.9 s, max 33 s as the Mac heated up) + 1 min thumbnails. Not uploaded yet.
      Fixed: [number: ... | prefix=$ suffix=B] in one slot was parsed as a literal label.
- [ ] A 30-min video; time it (expect ~75-85 min final at ~28 s per image).
- [ ] Ask me before deleting ~1.8 GB of stale *.incomplete files in
      ~/.cache/huggingface/hub/models--Runpod--FLUX.2-klein-4B-mflux-4bit/blobs, and the test folders
      output/vtest, output/atest.
- [x] Login system + Account screen + online through Tailscale Funnel (2026-11-08). Account varunreddy (admin).
- [x] Auto-start installed (2026-11-08, I approved): launchd agents com.videostudio.server (caffeinate -is +
      render_server.py) and com.videostudio.tailscale (userspace tailscaled) in ~/Library/LaunchAgents.
      Start at login, restart on crash (tested), Funnel comes back by itself. Mac stays awake when plugged in.
- [x] Public address tested from outside (via Tailscale relay): login 200 with valid cert, everything else
      401/302/403 when logged out. Funnel doesn't pass the visitor's IP, so lockout is per username only.
- [ ] Friend: send docs/FRIEND_SETUP.md, add his GitHub username as a collaborator. Guide updated 2026-11-09:
      own repo as origin + mine as upstream (push DISABLED) + his URL in his CLAUDE.md git rule, his own
      character (miso/biscuit/nova or his own; Sterling is my brand), pack build ~2-2.5 h, keep-awake, both
      video types. setup.sh now installs + import-checks rembg, onnxruntime, transformers, opencv (ran clean here).
- [x] Code on GitHub (2026-11-08): private repo varunreddy033/youtube-pipeline, pushed after every verified change.
- [x] Public repo (2026-11-10): varunreddy033/video-studio, fresh history, filled only by tools/publish_public.py
      (leak checks: secrets, Tailscale/Gmail addresses, PRIVATE.md values, blocked files). The private repo's
      history was also scrubbed of the address + Gmail (backup: output/backups/); its 13 old commits are still
      reachable by ID on GitHub and a friend's private fork has the old history (details in PRIVATE.md), which is why the private repo
      stays private. check_secrets.sh blocks personal data outside PRIVATE.md / .publicignore paths.
- [x] Presenter build (2026-11-08/09), timings:
      step 1 format + parser: draft of the Sterling script 7:34 rendered in 102 s.
      step 2 Sterling pack: poses 13 min, 84 mouth/blink edits ~100 min of real work (55-75 s each + 8 s cool-down),
      cutouts ~1 min, sets ~3 min (wall clock 6.7 h because the Mac slept on battery). Fix rebuild (laughing +
      empty sets): 16 min. Pack images: 118 in the shared cache.
      steps 3-5: lip-sync test clip 4 s in 10 s; parallax 5 s 1080p clip in 11 s (first run +2 min model download).
      step 6 final (scripts/ai_bubble_sterling.md, job 20261108-184222-d0b89e): 7:44, 67 shots (27 talk, 15 act),
      -14.0 LUFS, 250 s with cached images (first full run ~35-45 min); Short 50 s in 38 s; thumbnails 1 s;
      upload_pack.zip 239 MB. Not uploaded yet (I upload from the web page).
- [x] docs/CLAUDE_SCRIPT_PROMPT.md: prompt A = Sterling presents (character:, [talk:], [act:], his persona and
      catchphrases, pacing + today's lessons), prompt B = no presenter. Prompt A's format passes Check clean.
- [ ] Packs for other characters (docs/characters/biscuit.md, nova.md) when needed (~2 h each, plugged in).
- [x] Video types (2026-11-09, docs/VIDEO_TYPES.md): type header + presets, two dashboard buttons, clip picker with
      preview, clip Shorts, pack export/import, cross-platform encoder + bundled fonts + UTF-8. Tested:
      Short from scratch (scripts/short_730_billion.md, job 20261109-121112-a44971): 37 s, draft 18 s, final 45 s
      incl. 1 new vertical [act:] image (21 s), later re-render 24 s; -14.0 LUFS; 1 cover; 4-file upload pack.
      Clip from the Sterling video made in the browser (job 20261109-120948-17c36f, 6:51-7:30 "My take"):
      38 s, rendered in 40 s, 0 new images. Earlier CLI clip 1:03-1:58: 55 s in 35 s, -14.0 LUFS.
      Full-video music per chapter + forced libx264 tested on the sample (-14.1 LUFS). Pack export 137 MB zip
      (112 files) in <1 s; import into a fresh copy at another path renders talk + card with libx264.
- [ ] Windows Legion setup not done or tested on Windows itself (setup.sh is Mac/Homebrew; needs Python 3.11,
      ffmpeg with libass, espeak-ng, the pip packages minus mflux). New AI images there need a diffusers backend.
- Later: YouTube API audit + automatic upload.

## Useful commands
- Public address: https://<your-name>.<your-tailnet>.ts.net, each person's own (see `... funnel status` below;
  needs the server + tailscaled running, Mac awake)
- Tailscale (this project's copy): `tailscale --socket="$HOME/Library/Application Support/vs-tailscale/tailscaled.sock" status`
  and `... funnel status`. Start the tunnel by hand: see docs/FRIEND_SETUP.md step 7 (same commands).
- Auto-start install/remove: `bash tools/install_autostart.sh` / `bash tools/install_autostart.sh remove`
- Copy a character pack to the other machine: `bin/python tools/export_character_pack.py sterling`, then there:
  `python tools/import_character_pack.py sterling-pack-<date>.zip` (add `--force` to replace an existing pack)
- Save + upload a finished change: `cd ~/youtube-pipeline && git add -A && bash tools/check_secrets.sh && git commit -m "..." && git push`
- Secret check before every commit (must say "clean"): `bash tools/check_secrets.sh`
- GitHub login (gh CLI, account varunreddy033): `gh auth status`. Commits use the no-reply email
  150993157+varunreddy033@users.noreply.github.com.
- Start Video Studio, then open http://localhost:8765 : `~/youtube-pipeline/bin/python ~/youtube-pipeline/render_server.py`
- Restart Video Studio (after code changes): `launchctl kickstart -k gui/$(id -u)/com.videostudio.server`
- Stop it until next login: `launchctl bootout gui/$(id -u)/com.videostudio.server` (killing the process just restarts it)
- Check a script from Terminal: `~/youtube-pipeline/bin/python -c "from pipeline import script_parser as P; import json,sys; r=P.parse(open(sys.argv[1]).read()); print(json.dumps(r['errors']+r['warnings'],indent=1))" script.md`
- Logs: output/server.log (server), output/jobs/<id>/render.log (one video)
