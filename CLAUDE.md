# Project: faceless YouTube automation (Varun + Raju)

Read this first in every session. It is the single source of truth for how this pipeline works and what has
already been decided; it is shared by Varun and Raju, who both push to this repo. Each
person also has a CLAUDE.local.md on their own Mac (gitignored): their machine, accounts and personal to-dos.
Don't re-propose decisions marked DECIDED unless the person you're working with asks.

## How to work (both of us)
- Give complete, working code only: no placeholders, no "adjust this to your setup".
- Run commands yourself instead of telling us to copy-paste them. Ask before deleting files.
- One step at a time. Verify each step (run it, check output) before saying it's done.
- Don't recommend a different architecture unless something is truly broken. If it is, say why in 2-3 lines.
- Prices in Indian rupees.
- Git (DECIDED 2026-11-11, shared repo; CONTRIBUTING.md says the same in plain words):
  - Always `git pull --rebase` first (on main, before starting a task).
  - One short branch per task, named <name>/<task> (varun/style-tab, raju/arcade-fix). Small commits on it.
  - When the task works: `bin/python tools/check_presets.py` (must say "presets: clean"), plus a draft of
    docs/sample_motion_gfx_script.md and of docs/sample_script.md (both must render), then open a PR with
    `gh pr create --fill`, and squash-merge it the same day (`gh pr merge --squash --delete-branch`), so the branch is
    deleted. Then `git switch main && git pull --rebase`.
  - Run `bash tools/check_secrets.sh` before every commit (must say "clean").
  - Never force-push main. Never commit .env, data/, output/, models/, the generated icon indexes and packs
    (assets/library/icons/*/icons.json, index.json, embeddings.npy), character pack images, or licensed music
    (assets/audio/); .gitignore already covers them, don't override it.
  - Don't push broken or untested code. Commit and push your own task branch without asking; merging the PR is part
    of finishing the task.
  - The public repo (varunreddy033/video-studio, tools/publish_public.py) is Varun's job only (his CLAUDE.local.md).
    scripts/, PRIVATE.md and the .publicignore paths never go public.

- Asset library rule (STANDING, 2026-11-11): "The asset library only grows. Any new icon, sound, music track or
  generated prop fetched or made for a video is stored in assets/library with its licence, source and tags,
  indexed, and offered to later videos. Nothing is deleted without asking me." ("me" = the person you're working with.)

## Goal
- 1 hour of new content per day (2x30 or 3x20 min preferred over 6x10: fewer uploads, less template-y).
- We pick a trending topic each day and write the script with Claude (chat). Videos must be good enough that
  viewers like them and must not look mass-produced (YouTube "inauthentic content" policy judges the channel).
- Cost: Rs 0/month. Everything runs on the Mac or on free services.

## Requirements (each person's own Mac; specifics in CLAUDE.local.md)
- Apple Silicon Mac (16 GB RAM recommended; fanless Airs throttle on long renders), macOS up to date, ~20 GB free.
- setup.sh installs everything: Homebrew packages (ffmpeg-full with libass / loudnorm / h264_videotoolbox,
  python@3.11, espeak-ng, whisper-cpp, Node 22), the venv in the project folder (bin/python), npm ci, the icon packs +
  index, the models.
- Image model: Runpod/FLUX.2-klein-4B-mflux-4bit (4.62 GB, Apache-2.0) in ~/.cache/huggingface/hub, kept loaded during
  a render by pipeline/image_worker.py: ~18-28 s per 1280x720 image on an M5 Air (slower when hot or swapping).
- Long jobs: plugged in, lid open (asleep = everything stops).

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
                                    prompt = style_prompt(prompt, art_style) (presets/art_styles, default doc_photo)
                      [stock: ...]  same as ai + the style's stock_suffix (doc_photo: a documentary photo)
                      [card] [number] [quote] [chart]  Pillow/matplotlib frames, animated in, then held
  captions.py       word-by-word .ass captions in the caption style (presets/captions; default amber_word)
  sfx.py            sfx: auto = rule-based sound effects per shot (no AI)
  assemble.py       timeline -> clips (3 parallel) -> join -> voice + ducked BGM (full: per chapter, crossfaded)
                    + SFX -> loudnorm -14 LUFS (2-pass, linear) -> burn captions (bundled font) -> encoder.py
  clip.py           clip Shorts: source job's voice cache + cached images, 9:16 re-frame, Short captions, no new AI
  encoder.py        auto-detects h264_videotoolbox (Mac) / h264_nvenc (NVIDIA) / libx264 (VIDEO_ENCODER= forces)
  motion.py         style: motion -> timeline.json (docs/MOTION_TIMELINE.md) -> Remotion (motion/) picture -> classic mix
motion/             Remotion 4 project (React/TS, pinned): MotionVideo renders any timeline; Demo = phase-1 look test
  thumbnails.py     3 options 1280x720: 2 AI images (thumbnail_prompt) + 1 video frame, big text
  jobs.py           output/jobs/<id>/state.json, one-at-a-time render queue, progress, resume via cache/
  config.py / util.py  settings from .env, shared helpers
  presets.py        presets/<kind>/<id>.json (voices, captions, art_styles, music, niches): list/load/schema check,
                    script header -> preset ids, output/jobs/<id>/job.json (resolved presets) on every render
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

## Presets (P0, BUILT 2026-11-09, docs/SCRIPT_FORMAT.md "Presets")
- presets/{voices,captions,art_styles,music,niches}/<id>.json, every file has "label" + "licence". Defaults:
  voice en_us_michael (Kokoro am_michael 1.0, 155 wpm), captions amber_word (all captions.py values),
  art_style doc_photo (IMAGE_STYLE + stock suffix + model/steps), music any (library, by name else random,
  volume 0.18, duck, -14 LUFS), niche general (bundles the other four; no header key yet).
- Header keys: language, voice, captions, art_style, music. Missing = default. Unknown id = Check ERROR (line 1)
  listing the valid ids. Old values keep working with the same priority: voice: <Kokoro id> (script > character >
  .env), music: <track names>. A voice preset id gives that preset's voice + speed (speed: still wins).
- Every render writes output/jobs/<id>/job.json: type, format, language, the full preset files, overrides
  (script/character/.env values that differ from the presets), output size. GET /api/presets = {kind: [{id, label}]}.
- Used by the render: art style (F6), captions, voice, music/sfx choices (Look & sound, below). Defaults must equal
  the original values: `bin/python tools/check_presets.py` (must say "presets: clean"; checks doc_photo prompts
  and that amber_word writes the original caption file byte for byte, against a frozen copy of the old code).

## Look & sound (BUILT 2026-11-10): voice, music, captions, sound effects in Video Studio
- DECIDED 2026-11-10: assets/library/ IS in git (music/SFX are uploaded through GitHub): music/<mood>/, sfx/<kind>/,
  README.md = what to upload. Folder name = how a file is found. assets/audio/ stays local + ignored and still works.
  13 starter SFX are synthesised by tools/make_starter_sfx.py (no licence; your own files in a folder win).
  Music: 28 tracks in assets/library/music/<mood>/ since 2026-11-11 (licence unknown, private repo only).
- UI: one "Look & sound" card after Check (new-video screen + Script editor), tabs Voice / Music / Captions /
  Sound effects / Art style; every click writes a header line (voice:, music:, captions:, sfx:, art_style:).
  Clip Shorts show only Captions.
- Captions (F4): 11 presets (amber_word default, big_word, red_pop, soft_glow, karaoke_box, italic_punch, comic,
  serif, pixel, clean_lower, none). captions.write_ass(preset=...); highlight word / box / none; box = the word
  drawn again under the text as a fat blob (libass has no per-word box). Fonts: Barlow, Anton, Bangers, Poppins,
  Cormorant SC, Press Start 2P (OFL, assets/fonts/licences). Preview clips: GET /api/captions/<id>/preview.mp4
  (same code + libass, cached in assets/caption_previews).
- Voices (F2, English only): 28 presets en_us_* / en_gb_* from Kokoro's VOICES.md (gender, accent, grade).
  GET /api/voices/<id>/preview.wav speaks one sentence once (assets/voice_previews). Other languages = F3, not done
  (needs lang codes in voice.py, fonts, word counting).
- Music (F5, library part): music: <mood> | <track words> | a, b, c | none. GET /api/music, /api/sfx,
  /api/audio/<key>/audio. Matching: most name words (synonyms), then exact cue words, then own files before
  starter_*; old flat folders match as before.
- SFX: header sfx: script (default) | auto | off. Auto cues are seg["sfx_auto"] (kind, lead, gain 0.8); whoosh
  starts 0.28 s before the cut, riser 1.2 s. Check stats list each cue and why.
- Tested 2026-11-10 (cloud copy): parser output identical on all 5 scripts; draft with music: calm + sfx: auto +
  voice: en_us_heart + captions: red_pop = -14.1 LUFS; all tabs driven in a headless browser. Not yet run on
  the Mac.

## Art styles (F6, BUILT 2026-11-09)
- presets/art_styles/<id>.json: id, label, description, prefix, suffix, stock_suffix, realistic, lora (null only:
  the worker can't load LoRAs), lora_scale, steps (null = 4), licence. 8 styles: doc_photo (default), cinematic_film,
  archival_bw, dark_oil_painting, graphic_novel, noir_neon, isometric_3d, paper_cut. Prompt words are our own text
  (I wrote them; the brief's table didn't come through), adapted from twri/sdxl_prompt_styler (MIT).
- ONE function visuals.style_prompt(prompt, style, stock) = "prefix, prompt, stock_suffix ([stock:] only), suffix".
  Used by [ai:]/[stock:] shots, the 2 AI thumbnails (thumbnails.thumb_prompt) and clip.py (with the SOURCE job's
  style). doc_photo suffix = config.IMAGE_STYLE (.env IMAGE_STYLE still overrides) -> byte-for-byte the old
  prompts, same cache keys (checked: 132 prompts/cache names of all 5 scripts identical to the old code).
- [act:] / [talk:] / character packs / presenter thumbnails keep the character's STYLE; character script +
  art_style: = Check warning. Draft placeholders print "Art style: <label>" under the prompt.
- Check summary: art_style {id, label, realistic, images: {total, new}} (new = not in the job's cache yet).
- API: GET /api/art_styles, POST /api/art_styles/<id>/preview (fixed prompt "an old stone harbour at dawn with
  fishing boats and gulls", seed 1000, 1280x720 -> assets/style_previews/<id>.jpg 720 px; 409 while a video
  renders or another preview runs; 400 off the Mac; never regenerates), GET /api/art_styles/<id>/preview.jpg.
- UI: "Art style" card after Check on the new-video screen and in the job's Script editor (tiles + preview
  button; a click writes art_style: into the header and re-checks / re-saves).

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
- Scripts are written by us with Claude in chat, pasted as script.md. No LLM API in the pipeline (Rs 0, and we
  review every fact). The Gemini script writer is retired (old/script_gen_gemini.py).
- n8n is RETIRED (synchronous 30-min render call broke long videos). n8n/ folder kept for reference.
  Docker isn't needed.
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
  Tailscale Funnel (each person sets their own: their own Tailscale account, hostname and tailnet;
  `tailscale ... funnel status` prints it). Free, fixed HTTPS address,
  no router/domain. tailscaled runs in userspace mode (no admin password), state in ~/Library/Application Support/vs-tailscale. Funnel forwards to 127.0.0.1:8765.
- Every page/API needs a login (pipeline/auth.py): users in data/users.json (scrypt hashes, data/ is private and
  gitignored), signed 14-day session cookie (Secure over https), X-VS header + Origin check against CSRF,
  5 wrong passwords for a username -> that username locked 15 min (visitor IPs are hidden by the tunnel), security headers, 2 MB request cap. First account via /setup with the
  one-time code printed in output/server.log. The admin can add/remove users on the Account screen.
  tools: 19-check security test passed. The X-Render-Token header (from .env) still works for curl on this Mac.
- Each person runs their OWN copy of this repo on their OWN Mac with their own login and Tailscale address
  (docs/FRIEND_SETUP.md: clone this repo as origin, no fork, no upstream). No shared server; the code is shared.
- Upload is manual in YouTube Studio: the API project is unverified (uploads forced private) and Studio
  has thumbnail A/B tests and the AI-content disclosure checkbox.
- Local Wan 2.1 video generation DROPPED (14B for image-to-video, NVIDIA-only tooling, far too slow on 16 GB).
- Script rules: no invented facts/quotes about real people, no text/logos/real faces in AI prompts.

## Accounts / keys
- .env on each Mac, pasted by its owner, never in chat, code or git: HF_TOKEN (optional), RENDER_TOKEN.

## Assets
- assets/library/ (in git, 2026-11-10): music/<mood>/ and sfx/<kind>/, see assets/library/README.md.
- assets/audio/bgm = music beds (only files >= 60 s are used). `music:` in script.md matches file-name words.
- assets/audio/sfx = short effects, matched to [sfx: word] by file-name words, capped at 2.5 s.
- Cleaned 2026-11-08: 17 files moved to assets/audio/_unused (9 choir *patrikios* tracks, 4 duplicates, 4 non-music
  sounds). bgm now has 7 tracks (The Grey Room: A Dyin' Breed, At All Costs, Drop of a Hat, Misdirection,
  Missed My Chance, Soaring; Jeremy Korpas: Elysian Fields). sfx has 3 typing sounds.
- `music:` matches words in file names, so use a track name (misdirection, soaring, elysian ...); mood words like
  'dark' match nothing and pick a random track.
- Since 2026-11-11 the library has 198 CC0 SFX in assets/library/sfx (tools/fetch_sfx_openverse.py).

## Current status (update this section as we go)
- [x] setup.sh run, ffmpeg-full installed, setup.sh filter-check bug fixed (2026-11-08)
- [x] FLUX.2 klein 4B downloaded and benchmarked (2026-11-08)
- [x] Full pipeline built (2026-11-08): parser, voice + word timings, visuals (stock/AI/card/number/quote/chart),
      word captions, ducked mix, -14 LUFS, videotoolbox, thumbnails, job queue, Video Studio page.
      Tested in the browser with docs/sample_script.md: Check -> draft (14 s) -> final (65 s) -> 3 thumbnails
      -> metadata, loudness measured -14.0 LUFS.
- [x] Pexels removed (keys paused); [stock:] now makes an AI documentary photo. Image model kept loaded
      (image_worker.py) with MLX cache clearing. Re-tested in the browser: draft 7 s, final 64 s, thumbnails OK.
- [x] First real video (2026-11-08): scripts/2026-11-08-ai-bubble.md, job 20261108-142648-792e8d.
      9:16 long, 76 shots (55 AI images incl. thumbnails, 23 graphics), -14.0 LUFS. Draft 66-119 s.
      Final 26 min (images avg 27.9 s, max 33 s as the Mac heated up) + 1 min thumbnails. Not uploaded yet.
      Fixed: [number: ... | prefix=$ suffix=B] in one slot was parsed as a literal label.
- [ ] A 30-min video; time it (expect ~75-85 min final at ~28 s per image).
- [x] Login system + Account screen + online through Tailscale Funnel (2026-11-08); auto-start via
      tools/install_autostart.sh (launchd: server + userspace tailscaled, restart on crash).
- [x] Code on GitHub (2026-11-08): private repo varunreddy033/youtube-pipeline. Shared with Raju (write access)
      since 2026-11-11: branches + PRs (CONTRIBUTING.md). Public copy varunreddy033/video-studio (Varun publishes).
- [x] Presenter build (2026-11-08/09), timings:
      step 1 format + parser: draft of the Sterling script 7:34 rendered in 102 s.
      step 2 Sterling pack: poses 13 min, 84 mouth/blink edits ~100 min of real work (55-75 s each + 8 s cool-down),
      cutouts ~1 min, sets ~3 min (wall clock 6.7 h because the Mac slept on battery). Fix rebuild (laughing +
      empty sets): 16 min. Pack images: 118 in the shared cache.
      steps 3-5: lip-sync test clip 4 s in 10 s; parallax 5 s 1080p clip in 11 s (first run +2 min model download).
      step 6 final (scripts/ai_bubble_sterling.md, job 20261108-184222-d0b89e): 7:44, 67 shots (27 talk, 15 act),
      -14.0 LUFS, 250 s with cached images (first full run ~35-45 min); Short 50 s in 38 s; thumbnails 1 s;
      upload_pack.zip 239 MB. Not uploaded yet.
- [x] docs/CLAUDE_SCRIPT_PROMPT.md: prompt A = Sterling presents (character:, [talk:], [act:], his persona and
      catchphrases, pacing + today's lessons), prompt B = no presenter. Prompt A's format passes Check clean.
- [ ] Packs for other characters (docs/characters/biscuit.md, nova.md) when needed (~2 h each, plugged in).
- [ ] MOTION style (docs/MOTION_PLAN.md, opt-in `style: motion`; classic stays the default and untouched):
  - [x] Phase 1 look test (2026-11-10): motion/ = Remotion 4.0.539 (React 18.3.1, TS 5.9.3, all pinned, lockfile),
        Node 22 via Homebrew (setup.sh installs it + npm ci + Remotion's headless browser). Montserrat (OFL) bundled.
        tools/motion_demo.py: Kokoro bm_george voice -> word timings (motion/src/demo/timing.json) -> Remotion picture
        -> voice + ducked music -> -14 LUFS -> output/motion_demo.mp4. 27.5 s demo, 3 scenes: 4 doors grow on their
        words with label tags + word-by-word headline pill; line chart draws while -5.5% counts, calendar page flips,
        shake on "slammed"; push-from-right with shadow band; zoom-through into the chart's red end dot; doors with
        "?" bubbles, coin pile, dashed arrow. Render: Remotion 16.4 s, total 19 s (concurrency 4). -14.0 LUFS.
        Approved 2026-11-10.
  - [x] Phase 2 bridge (2026-11-10): `style: motion` in the header -> pipeline/motion.py (jobs.py routes it; classic
        untouched apart from per-stage timings). Contract docs/MOTION_TIMELINE.md + motion/src/motion/types.ts:
        scenes (from/frames/transition/background/headline), elements with enter/exit cues = word index + frame.
        Python makes voice, FLUX images (same cache keys as classic), [talk:] clips, then STOPS the image worker,
        writes timeline.json, runs `remotion render ... Motion --props --public-dir --concurrency` (video only),
        mixes audio with the classic _mix_audio + loudnorm, muxes without re-encoding. Job page shows time per stage
        (classic too). Interim adapter: one scene per classic shot (phase 3's v3 tags replace it).
        Test, sample with style: motion: draft 35 s (Remotion 25 s at half size), final 106 s = 3 new AI images 58 s
        + Remotion 44 s for 903 frames + audio 3 s + mux 1 s; -14.1 LUFS; FLUX and Remotion never overlapped
        (checked every second). Concurrency on the M5 Air (825-frame demo): 2 tabs 23 s, 4 tabs 17 s, 6 tabs 17 s,
        8 tabs 18 s -> MOTION_CONCURRENCY=4 default. Classic re-check: sample passes Check, draft 13 s, old job's
        final 10 s with 0 new AI images, -14.1 LUFS.
  - [x] Phase 3 script v3 (2026-11-10): pipeline/script_v3.py parses motion bodies ([scene: | from:], [char:],
        [+ kind: text | place | anim | size], [- x], [head:], [label: | target], [+ gen:], in-scene
        [number:]/[chart:]/[quote:]/[card:] with a place, [talk:]/[ai:]/[stock:] as full-frame scenes, [sfx:]
        [pause:] ##). Cues = (segment, token); pipeline/motion_timeline.py aligns them to Kokoro's words (difflib)
        or to estimates (previews), lays out boxes (slots avoid the presenter's side, boxes clamped in frame,
        presenter carries into later scenes until [- char]), headline words light on their spoken word (digits on
        the first number word). Check: motion pacing (something new every 3 s, scenes 6-15 s, a headline per scene,
        varied transitions) + a scene list + "Show scene previews" (motion/scripts/stills.mjs: one bundle, one
        browser, renderStill per scene; ~2-3 s for 4 scenes; cached; refused while a render holds
        jobs.RENDER_LOCK, which every render now holds). Classic parser: body loop only skipped for style: motion;
        20/20 classic scripts parse byte-identically (snapshot compare). docs/SCRIPT_FORMAT.md section 5 +
        docs/sample_motion_script.md (36 s, 4 scenes, 15 elements): final 27-51 s (Remotion 25-47 s, varies with
        heat), -14.0 LUFS, every cue lands ~2 frames before its word. Until Sterling Flat (phase 6) [char:] shows the
        classic pack's pose cut-out. Phase-2 test job 20261110-183704-ccc7a6 (classic tags + style: motion) no
        longer passes Check (expected; ask before deleting it).
  - [x] Phase 4 library (2026-11-10): motion/src/library/catalog.json = the one list of kinds (Python + Remotion read
        it): 45 parametric SVG props in 8 groups (places, tech, ideas, money, things, signs...), each with its own idle
        motion and art bounds so it fills its box; data components line/bar chart, big number, calendar, pie,
        compare (VS), ranking, world map with pin (Natural Earth 110m, public domain, tools/make_worldmap.py,
        122 KB); headline pill + label tags; transitions push x4 with shadow band, zoom-through, iris, whip pan,
        fade, cut + a chooser (opening words: deeper -> zoom, fall -> drop from top, flashback -> from left, else
        mostly push right / whip / iris, never twice in a row); palettes navy + light (per scene: palette=light),
        onPanel text colour so pills and tags read on both. Contact sheet: tools/motion_library_sheet.py ->
        output/motion_library.mp4 (75 s: 3 prop pages, 7 data pages incl. light palette, 9 transitions), rendered
        in 39-41 s. Motion sample final 55 s (Remotion 50 s warm), -14.0 LUFS; classic draft 13 s, classic parse
        identical.
  - [x] Phase 5 flat art style (2026-11-10): presets/art_styles/flat_vector.json (+ optional prop_suffix /
        plate_suffix fields in presets.py). pipeline/props_gen.py: [+ gen: text] -> FLUX.2 klein 1024x1024 in
        flat_vector on white -> rembg u2net cut-out, trimmed -> assets/library/props/<slug>-<key>.png (+ .json);
        scene plates for 17 known names (city_night, office, trading_floor, server_room...) or | plate=<desc>
        -> 1280x720 -> assets/library/plates/. Both in git, made once in the first final, reused everywhere
        (drafts/previews never generate; Check counts what's missing for its estimate). Test: 2 props + 1 plate
        generated in 88 s (29-32 s each incl. cool-down), whole final 114 s; same final again 19 s, 0 generated.
        Remotion draws plates dimmed toward the palette with a slow drift. Lesson: the server must be restarted
        after code changes (a render ran the old code once).
  - [x] Phase 6 = 3D Sterling inside motion scenes (DECIDED 2026-11-10: no 2D conversion; quality first).
        [char:] is the normal 3D pack, lip-synced + blinking in Remotion (Placed.tsx CharView, pack mouth pictures,
        Kokoro phoneme timings), pose switches mid-scene; [act:]/[talk:]/[ai:] are full-frame motion scenes.
        Sterling Flat is PARKED (benchmark passed: docs/presenter_bench/RESULTS_FLAT.md, docs/characters/sterling_flat.md,
        tools/flat_bench.py, assets/characters/sterling_flat; ask before deleting).
        Layout rules added: slots shrink things to fit, small cards = tiles (2 x 2 for four), check/cross stamp on
        the prop, labels flip under a target when the top is taken, bigger numbers. New SVG props earphones, earbuds
        (the FLUX "gen" earphone cut-out came out as a white blob; SVG props are sharper and instant).
        First full motion video: scripts/2026-11-10-earpods-motion.md, job 20261110-205101-d56969: 8:55, 66 shots
        (29 scenes, 21 talk, 10 act, 6 ai), final 635 s = images/presenter 73 s (0 new AI images, cache seeded from
        the classic job) + Remotion 530 s for 16,064 frames + audio 26 s + mux 5 s; -14.0 LUFS; on battery.
        Feedback on this video pending. Known weak spots: thin white rim around the 3D cut-out on navy,
        scenes are navy-only (no plates used), [talk:] shots are the classic studio look.
  - [x] Weak-spot fixes for the EarPods motion video (2026-11-10, previews checked, FINAL NOT RE-RENDERED YET): puppet cut-outs get a clean edge (motion._clean_edge, PUPPET_VERSION 2, no white rim) + a soft glow
        behind the presenter; `plate=<known name>` works on any scene and shares one plate; 7 plates in
        assets/library/plates (city_night, city_day, home, stage, office, street, trading_floor), drawn blurred and
        dimmed; navy vignette on full-frame [talk:]/[ai:]/[act:] shots; narrow tiles taller; script got plates on 14
        scenes and pose switches/labels in slow stretches (Check: 1 pacing warning left, bose). Still to do: render
        the final plugged in and look at it; unbothered scene label touches the quote's last word.
- [x] MOTION GRAPHICS = Raju's stick-figure renderer, ported in (DECIDED 2026-11-11: this is the motion look
      going forward; the Remotion `style: motion` with Sterling stays in the code, parked). Header
      `rendering_method: motion` (UI: Pictures = Motion graphics). Code in pipeline/motion_gfx/ (his pipeline/motion/,
      renamed because pipeline/motion.py is the Remotion renderer): kinetic words, stick figures, numbers/charts/
      quotes/memos, caption chip (captions: chip), SFX on every beat, no AI images, no character:. HyperFrames 0.9.26 +
      GSAP 3.15.1 pinned in the ROOT package.json (`npm ci` in the project folder). Ported as a patch of his changes
      d3275cc..b09e3bf (NOT a history merge: his history still holds the scrubbed address). Not taken: his CLAUDE.md,
      .claude/skills (627 files), skills-lock.json. His docs: docs/MOTION_GFX_PLAN.md, sample
      docs/sample_motion_gfx_script.md (Load sample with Pictures = Motion graphics). Also from him: 28 music tracks in
      assets/library/music/<mood>/ (licence unknown -> in .publicignore, private repo only, until the source is
      confirmed), 46 SFX (assets/library/sfx/CREDITS.md), tools/fetch_sfx_openverse.py, sfx: rich.
      style: motion + rendering_method: motion together = Check error.
      Tests on the Mac 2026-11-11: presets clean; classic sample draft 13 s; Remotion sample draft 24 s; stick-figure
      sample draft 1:14 in 74 s; EarPods final scripts/2026-11-11-earpods-gfx.md, job 20261111-085018-292260: 8:53,
      209 scenes, 171 SFX, 611 s (HyperFrames 502 s). Weak spots seen: narration still says "I'm Sterling / a cat in
      a blazer", no earphone props, filler kinetic words, a near-empty frame around 6:05.
      Known issues from Raju's original Mac test (2026-11-11, pipeline/motion/ before the port; not re-checked in
      motion_gfx): ~18 harmless GSAP "target not found" warnings in hyperframes check (blink on some poses), the
      chip captions overlap for a moment when the text changes (chip is no longer the motion default), motion
      finals come out ~2.7 Mbps (flat colours; fine for YouTube, but below the 10 Mbps of ai_image finals).
- [x] ASSET PACKS for motion graphics (docs/ASSET_PACKS_PLAN.md, build order = its section 7; branch main):
  - [x] Step 1 importer (2026-11-11): pipeline/icon_library.py (PACKS, licence allow-list, svg(id), credit_lines) +
        tools/import_icon_packs.py (`--check` = stale test). Packs from pinned @iconify-json npm packages (root
        package.json): fluent_flat 1,594, fluent_color 1,590, noto 1,680, phosphor fill+duotone 3,024, tabler 6,287,
        flags 4x3 271, natural_earth 176 country shapes (from motion/src/library/worldmap.json). Skin tones dropped.
        assets/library/icons/<set>/icons.json is NOT in git (43 MB, rebuilt by setup.sh); LICENCE per pack +
        CREDITS.md + the "ICON PACKS" block of NOTICE are in git. Refused in tests: CC-BY-SA-4.0, GPL-3.0, OFL-1.1,
        unknown; twemoji (CC BY 4.0) only imports with ALLOW_CC_BY=1 (credit_lines() gives its description line).
        Noto is pinned to 1.2.7 ON PURPOSE: newer packages include files added after upstream replaced the Apache
        licence file with OFL-1.1 (not on the allow-list). Classic sample draft 14 s, presets clean.
  - [x] Step 2 index (2026-11-11): pipeline/icon_index.py + tools/build_icon_index.py -> assets/library/icons/
        index.json (14,622 rows: id, set, name, words, category, licence, has_colour, char) + embeddings.npy
        (11 MB, float16), both NOT in git, rebuilt automatically when the packs change (signature check), 32 s incl.
        the model download. Model sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0) pinned to revision 1110a243,
        run with transformers + mean pooling on the CPU (no sentence-transformers package needed). Keywords:
        emojilib 4.0.3 + unicode-emoji-json 0.9.0 (both MIT) instead of CLDR (Unicode licence isn't on the
        allow-list). `bin/python tools/icon_search.py "battery dies" [--set fluent_flat] [-n 10]`: low-battery
        first, 2 s, same result every run. Whole sentences search badly (the picker uses key nouns, step 3).
  - [x] Step 3 picker (2026-11-11): pipeline/motion_gfx/picker.py plan(beats, names, meta) for the whole video:
        topic pool (~20 topic words -> up to 60 icons), per-scene queries (key phrase, each content word, the clause,
        the old RULES prop as words), score = similarity + name-word bonus (-0.15 for look-alikes: chip/chipmunk) +
        pool bonus; global greedy best pairs >= 0.50, then >= 0.44, then the best unused pool icon >= 0.30; no
        repeats (icon_reuse), question-style <= 3 and 60 s apart, no "?"/"!" fallback (no icon -> kinetic scene).
        Icons drawn as <img> SVG data URIs (templates.icon_html). Header keys icons, icon_reuse, icons_pin, icons_ban
        (parser checks them). render.py writes motion/icons.json + a log line. Check page: "Icons" card
        (POST /api/motion/icons, GET /api/icons/<set>/<name>.svg) with pool, pick per scene, Pin/Ban. Old EarPods
        beats: 63 different icons in 95 figure scenes, 0 repeats, 0 question-style (was exclaim 73x). Sample draft
        79 s; classic sample draft 13 s; Remotion sample draft 29 s; presets clean.
  - [x] Step 4 looks (2026-11-11): pipeline/motion_gfx/history.py + data/asset_history.json (private): one entry per
        motion FINAL (look, icons, templates, palettes, fonts, music, sfx). Look per video = icon family (fluent_flat /
        fluent_color / noto) + palette set (design.PALETTE_SETS pop/warm/cool/bold) + font pair (design.FONT_PAIRS
        poster/condensed/comic) + icon_style (sticker = white badge, dark outline, shadow; plain); `look: auto` takes
        what the last 5 videos used least, a video already in the history keeps its look, `look: classic` = original.
        Header keys look, palette (motion gfx meaning), fonts, icon_style. Icons of the last 5 videos rank 0.05 lower.
        Templates read the fonts via templates.set_look (HEAD/BODY/CHAR_W). Sample draft 79 s (noto/bold/comic);
        classic draft 12 s; Remotion draft 26 s; presets clean. Draft renders never write the history.
  - [x] Step 5 templates (2026-11-11): pipeline/motion_gfx/extras.py: icon_list, versus, pile, timeline, meter,
        map_flag (Natural Earth shapes + flag pack), triggered by the words (countries incl. demonyms, spoken years,
        percentages, "X or/versus/instead of Y", lists, "thousands of"; 25 s cooldown per type, each country once).
        Every template (old 7 + new 6) has 3 layout variants (ctx["variant"]; templates.scene_variants rotates them,
        starting at the variant the last 5 videos used least). picker.plan_video settles templates + variants +
        icons together (a newer template whose required icons aren't found becomes words; kinetic scenes take an icon
        on a strong match only; names like Apple / Lily-Rose are left out of icon searches). beats.json now has
        variant + icons. Test reel (scratchpad all_templates.md, 2:54, 58 scenes): all 13 templates x variants
        rendered, hyperframes check 3 warnings, draft 171 s. Sample draft 81 s; classic 12 s; Remotion 26 s.
  - [x] Step 6 sound (2026-11-11): tools/fetch_sfx_openverse.py -n 8 + new kinds (notification, swoosh-up, boing,
        record-scratch, crowd-gasp, keyboard-enter, coin-drop, door, crowd-cheer): 198 CC0 files in
        assets/library/sfx (7.3 MB, 4-9 per kind, crowd-cheer 1), each in sfx/CREDITS.md; 7 wrong downloads (spoken
        "postage stamp" words, cymbal, doll laugh, disco clap) moved to the session scratchpad, not in git. Scenes cue
        the new kinds (memo stamp, coin-drop piles, boing versus, record-scratch on "But...", crowd-gasp on shocked
        figures, success/error meters). Freshness: SfxPicker(stale) + music_tracks(music_stale) put files/tracks of the
        last 5 motion videos last (classic unchanged). Music audit: assets/library/music/CREDITS.md (all 28 UNKNOWN
        licence, likely Pixabay = not on the allow-list); BLOCKED.txt (util.music_blocked) keeps 3 tagged covers out:
        dark/unsolved_mystery (Radiohead cover), dark/creepy_melody, dark/horror_piano. Test reel: 35 different SFX
        files in 50 effects (was 15), -14.2 LUFS; classic draft 13 s; Remotion 27 s; presets clean.
  - [x] Step 7 test (2026-11-11): EarPods final re-rendered, job 20261111-111507-480c21: 8:53, 209 scenes, 602 s
        (HyperFrames 494 s), -14.0 LUFS, look noto/warm/comic/sticker. 72 different icons, none twice, 2 question-style
        (white + red question mark): all three checks PASS. 157 SFX from 58 different files. Contact sheet old vs new:
        output/contact_sheets/earpods_old_vs_new.jpg (scratchpad contact_sheet.py). This final is the first entry in
        data/asset_history.json. Old job 20261111-085018-292260 kept (ask before deleting).
  - [x] Defaults + library (2026-11-11): motion graphics is the DEFAULT (.env DEFAULT_RENDERING_METHOD=motion; no
      rendering_method: line = motion, except character: / [talk:] / [act:] / clip_from / style: motion scripts,
      which get ai_image by themselves; docs/sample_script.md now says rendering_method: ai_image). Motion default
      captions: none (the scenes show the words; chip and the rest stay in the Captions tab; captions_final.srt is
      always made and in the upload pack); ai_image keeps amber_word. Check -> "Make final" (straight to the final)
      or "Draft first", on the new-video screen, a video's page and Shorts; last choice remembered per browser
      (localStorage vs.renderChoice). Prompt D in docs/CLAUDE_SCRIPT_PROMPT.md is the default, no presenter/name.
      Icons: tools/import_icon_packs.py --discover 2.2.555 sorted all 276 Iconify sets into
      assets/library/icons/packs.json (in git): 162 new sets imported (317,445 icons; total 169 packs, 331,496),
      108 refused (47 CC BY 4.0 = only with ALLOW_CC_BY=1, 30 brand/logo sets, 31 other licences). Kinds:
      illustration / flat / line / flag / map; only illustration "family" sets can be a video's main family;
      look: auto rotates fluent_flat, fluent_color, noto, noto_v1 only (emoji families with coverage >= the
      hand-picked ones); withicons_* / icon_park etc. only with icons:. Icon names with brand/logo are dropped.
      Picker: a topic word the family can't draw (Fluent/Noto have no chip) takes one icon from ONE companion
      colour set per video (picker._companion); ambiguous words with a hint are searched as the hint (chip ->
      computer chip). Index 54 s; index.json 63 MB + embeddings.npy 255 MB (mmap) + icons 329 MB +
      node_modules/@iconify-json 476 MB, none in git. Licence downloads use curl + jsDelivr's GitHub mirror
      (urllib waited 30 s a file here; raw.githubusercontent throttled to 75 s).
- [ ] VARIETY PLAN (docs/VARIETY_PLAN.md, build order = its section 8; rendering_method: motion only):
  - [x] Step 1 (2026-11-11): history.reserve() at the START of every motion render (draft or final) chooses the look
        and writes the entry with status "rendering" under a file lock (data/asset_history.lock); recent() sees
        reservations, so videos queued / rendered together never share a look (tested: 3 parallel processes -> 3
        different icon families; same title again keeps its look). Stale "rendering" entries ignored after 24 h;
        finished drafts stay as "draft". pipeline/motion_gfx/variety.py = the variety report (scene-type mix, most-used
        type + layout, transition mix, types, A-B-A-B, longest stretch without data, similarity to the last 10 videos,
        8 goals) in render.log, the job page and the Check page (Variety card). BASELINE, Windows vs MacBook final
        20261111-125755-a5e140: 10 types in 194 scenes, figure 43.8 %, kinetic 38.7 %, top layout figure:2 x29,
        4 transition types (cut 48.5 %), A-B-A-B 89, 91.8 s without a data scene: 0 of 8 goals.
        Regression: sample_script draft 12 s; motion sample draft 176 s.
  - [x] Step 2 (2026-11-11): pipeline/motion_gfx/planner.py replaces templates.scene_plan's figure/kinetic alternation:
        roles per beat (statistic, comparison, list, process, cause, timeline, quote, definition, story, question,
        warning, conclusion, transition), candidates per type with a fit test, budget (type <= 20 %, type+layout <= 6,
        kinetic <= 15 % for punch lines, never twice in a row, no A-B-A-B; relaxed in order when nothing fits), each
        chapter leaning on a seeded third of the types; rhythm = bursts on the hook / after chapter cards + a held
        breather (two calm beats merged, slow drift) every ~45 s; 13 transitions (cut, fade, push, slide, push_up,
        blinds, split, whip, zoom, zoom_out, flash, glitch, wipe = chapter signature) chosen by story relation,
        none above 35 %. Windows (Check estimate): 12 transition types (top 23 %), 0 same type twice, 3/8 goals; the
        scene mix stays figure 41 % / kinetic 37 % until step 4 adds types (today almost every beat can only be a
        figure or words). A figure without an icon still turns into words unless a neighbour is words.
        Regression: sample_script draft 11 s; motion sample draft 185 s, all 12 new transitions checked in frames.
  - [x] Step 3 (2026-11-11): every older scene type has 6 layouts = its 3 own arrangements, each also drawn with a frame
        (compose.FRAMES card / tilt / band / spot, one per type per video, seeded; layout = variant, frame when >= 3)
        + an entrance per scene (pop, rise, drop, mask, flip, skew, none; never twice in a row) on top of the
        template's own animation. Windows (estimate): top type+layout 25 -> 13 uses. Regression: sample_script draft
        11 s, motion sample draft 193 s, frames checked. Picker: the "ram" (sheep) emoji is never picked (it matched
        "chip"/memory in noto_v1).
  - [x] Step 4 (2026-11-11): pipeline/motion_gfx/scenes.py = 24 new code-drawn scene types (ranking, process,
        cause_effect, pros_cons, checklist, before_after, split, scale, funnel, venn, donut, icon_grid, table, phone,
        browser, chat, newspaper, ticker, calendar, countdown, magnifier, reaction, globe, route), each 2 arrangements x
        frame = 4 layouts, with a fit test + roles for the planner; + 3 format "host" scenes (dashboard, terminal,
        sticky) that fit any line. Figure scenes without an icon are re-planned instead of turning into words; words
        over their cap become a headline scene. Header scene_order: a, b, ... (test reels) forces types in turn.
        Windows (estimate, Pop Poster): 29-31 types, top type 19.8 %, top layout x6, 10-12 transitions, kinetic 14.7 %,
        A-B-A-B 0 = 8/8 goals. All 24 types checked in a forced reel (contact sheet). Fixed a thread race: the voice
        (Kokoro) and the icon search imported transformers at the same time -> "ImportError AlbertModel"; the server
        now imports it once at start. Fonts added: Patrick Hand + Space Mono (OFL, assets/fonts/licences).
        Formats scaffolding in the same commit (pipeline/motion_gfx/formats.py, header show:, default Pop Poster).
        Regression: sample_script draft 12 s; motion sample draft 216 s.
  - [x] Step 5 (2026-11-11), approved: pipeline/motion_gfx/formats.py, header
        show: (format: already means landscape/vertical) = pop_poster (default) | tech_desk | data_lab |
        paper_notebook. Per format: palette sets + font pairs (new: tech, lab, hand), icon style, card/line colours,
        line weight, shadow (offset / soft / glow), backdrop (none / UI grid + brackets / dot grid + glow / ruled paper
        + margin + tape) + hand-drawn wobble filter (paper), scene weights + banned types (no stick figures in Tech Desk /
        Data Lab), entrance pool, easing, transition groups + signature (wipe / glitch / zoom / page turn), SFX map,
        music moods, chapter kicker. Planner seed = title + format (Pop Poster keeps the title-only seed). Picker: words
        the video capitalises mid-sentence are names everywhere (no apple for "Apple changed..."), "running" is filler.
        Preview: output/previews/formats_1-4.mp4 (2 x 2, the Windows opening, 18 s) + formats_1-4_sheet.jpg.
        Regression: sample_script draft 9 s, presets clean.
  - [x] Step 6 (2026-11-11), approved: newsroom (white/red/navy, red top bar + LIVE
        + ticker band, flat panels, host lower_third = faceless anchor silhouette + lower-third bar, bars / flash
        transitions), case_file (noir, desk-lamp cone + vignette, manila cards, Cormorant SC + Courier Prime, host
        evidence = board with blank polaroids + red string + stamp, flashlight transition), arcade_retro (CRT scanlines,
        Press Start 2P, square corners, stepped easing, host level = LEVEL/STAGE card + health bar + coins, pixel iris
        + shake), blueprint (blue grid + title block, light lines on blue cards, host diagram = part + callout lines +
        dimension line, draw-on transition). Each format lists its own host scenes; every other format's hosts are
        banned automatically (formats.ALL_HOSTS). Font added: Courier Prime (OFL). Windows (estimate) per format:
        6-8 of 8 goals (Data Lab 4: a script with few numbers). Preview: output/previews/formats_5-8.mp4 + _sheet.jpg.
        Regression: sample_script draft 11 s, presets clean.
  - [x] Step 7 (2026-11-11): show: auto (default) = topic fit (MiniLM: title/tags/description vs each format's
        description) + 0.03 per variety goal the script meets in that format (planner-only plan of all 8, ~1 s) - 0.06
        per use in the last 10 videos; never the format of a video rendering right now; a re-render keeps its format.
        FORMATS_ALLOWED in .env (tested: pop_poster, blueprint -> blueprint). Similarity check: variety.similarity vs
        the last 10 fingerprints (look incl. format, scene mix, transition mix), warning above 0.72 on the Check page
        naming the closest video (tested: a copy of itself = 1.00 + warning). Check page: format, why, top fits.
        Picks: Windows -> tech_desk (8/8), EarPods -> case_file (6/8), Nvidia spy sample -> case_file, AI bubble ->
        newsroom. Bug fixed: entries from before reservations (no status) were treated as unfinished and the preview
        drafts overwrote the Windows final's look; restored from its final (backup output/backups/asset_history-*.json),
        and the two entries only my tests made (Nvidia sample draft, scene-types reel) removed.
  - [ ] Step 8 / final test (2026-11-11): Windows re-render, job 20261111-162738-976a6a, show: auto -> Tech Desk: 30 types
        in 187 scenes, top type kinetic 15.0 %, top type+layout 6, 8 transition types, kinetic 15.0 % = every acceptance
        number met; 7:41 in 1481 s. EarPods (job 20261111-162741-a1f91e) got Case File (different format, reserved at
        queue time) but the server restart stopped it mid-render: press Make final again, then make the 1-frame-every-10-s
        side-by-side contact sheet. Since then (committed untested; Varun tests): format + look
        reserved when a motion job is QUEUED (re-renders too, status "rendering", back to done/draft after);
        layouts = own arrangements x (plain + 4 frames) (15 older / 10 newer types); Style tab in Look & sound
        (Auto + 8 formats with preview strips from assets/format_previews, writes show:), GET /api/formats.
- [x] CAMERA + TRANSITIONS (2026-11-12, branch raju/camera-motion-transitions, docs/SCRIPT_FORMAT.md "Camera and
      transitions"): header `camera:` = auto (default) | off | flat (the old 2D drift) | dolly, pull, truck, orbit, tilt,
      handheld, focus, vertigo (one or a comma list); `transitions:` = auto | off | a set (3d, film, clean, glitch,
      popular) | a comma list. Bad values = Check error on the header line. Motion graphics: pipeline/motion_gfx/
      camera.py, every scene = 3 layers (far backdrop + soft depth dots on formats without a backdrop / mid frame / near
      content) moved by GSAP at different speeds, 3D rotation with perspective for orbit/tilt, blur for focus;
      planner.cameras picks per scene by job (reveal -> dolly/vertigo, quote/screens -> focus, breather -> orbit,
      burst -> handheld, chapter -> tilt) from the format's "cameras" pool, never twice in a row, <= 30 %.
      pipeline/motion_gfx/transitions.py: 13 new transitions that move BOTH scenes (exit on the outgoing host): whip_blur
      (SVG motion blur), zoom_blur, zoom_through, spin, light_leak, film_burn, rgb_split (SVG channel split), cube, flip,
      page_curl (incoming drawn under: index z-order), ink (mask), luma_wipe (mask), shape; longer overlaps per type;
      push/slide/push_up/whip now push the old scene out too. Each format got its own transition groups + camera pool.
      Variety report/Check card: camera mix + new transitions count. UI: Look & sound -> Camera tab, GET /api/camera.
      Classic ai_image: no camera: line = unchanged (sample draft pixel-identical to 2026-11-11, PSNR inf, same cache
      names); camera: set = parallax.camera_clip depth moves in finals (0.6-1.8 s per 3 s clip), nearest flat move in
      drafts, off = still. scene_order: now waits with strict data templates (timeline, meter, versus...) for a line
      that has the data (it crashed before). Tests on the Mac: reel of all 40 scene types + 13 new transitions + 8 moves
      (job 20261112-163851-f56b1b) 2:34 draft in 385 s, -14.2 LUFS, variety 8/8; motion sample draft 1:14 in 184 s,
      -14.1 LUFS, ~60 % more picture motion (median frame diff 0.46 -> 0.76); classic sample draft 7 s, -14.1 LUFS;
      presets clean. Final of the motion sample with camera auto (job 20261112-170918-87b685): 1:14 in 182 s, -14.2 LUFS, constant 30 fps (2225 frames), 0 frozen frames and 0 sudden jumps inside scenes, every held frame moves (median change 0.42).
- [x] Delete videos (2026-11-12, branch raju/delete-jobs): sidebar trash button per video (on hover) + Select… (Failed / Without final / All, Delete N); DELETE /api/jobs/<id>, POST /api/jobs/delete {ids}; jobs.delete MOVES the folder to ~/.Trash (output/deleted_jobs off the Mac), refuses queued / rendering jobs. Tested in the browser (single + select) and the refusal.
- [x] SMOOTH MOTION (2026-11-12, local branch raju/smooth-motion on top of raju/delete-jobs; the smooth-motion-studio
      skill in ~/.claude/skills, learned from two reference videos): pipeline/motion_gfx/spring.py = closed-form springs
      registered as GSAP eases spring.snappy (zeta 0.42, omega 17, settles 0.56 s) / soft / bouncy / firm
      (assets/js/springs.js in every motion project); all back.out/bounce eases and the formats' EASE_POP are springs
      now (arcade keeps steps). Every scene's frame + content (#<host>-life, wraps the camera rig) settle on a spring at
      the cut (not with camera: off / flat). pipeline/motion_gfx/critic.py = self-critique loop after the HyperFrames
      render: per-frame motion, a frame is dead when nothing moves, a score per scene (dead share, longest dead
      stretch, onset, constant speed, stutters, one-frame pops); scenes under 8 get fixes (onset = stronger spring
      settle on the cut, dead = slow float) and only their spans are re-rendered (hyperframes render --start/--end) and
      spliced in (frame-exact, checked by PSNR), up to 2 extra passes; motion/critique/report.json + critique.png,
      render.log lines, job page "Smoothness check" card. Header critique: auto (default) | report | off.
      pipeline/beatgrid.py: beat lock for the music bed: tempo from the first 60 s (onsets, score minus chance level),
      the track starts up to one beat late so its grid meets the most cuts (only tracks clearly on a grid; classic
      videos untouched, mixer command byte-identical). Tests (worktree, output/tests): motion sample draft 1:14 in
      117-191 s, critique 31 scenes mean 9.74 -> 9.82 / 9.84 -> 9.89, lowest 7.2 -> 8.5 / 7.8 -> 9.0, -14.1 LUFS;
      final with music: acid party: mean 9.85 -> 9.89, lowest 7.8 -> 8.9, beat lock 150 BPM, +0.283 s, cuts on the
      beat 17 % -> 33 %, -14.1 LUFS, true peak -0.5 dBTP, 30 fps / 2225 frames; skill critic on the delivered final:
      mean 9.9, lowest 9.1. Classic sample draft: picture PSNR inf vs 2026-11-11, audio bit-identical with the old
      and new assemble.py. Not pushed (Raju's rule: push / PR only when he asks).
- [x] PREMIUM BLOCKS in the pipeline (2026-11-13, same local branch raju/smooth-motion): the 19 blocks the
      premium-recreate session rebuilt from Raju's reference recordings (output/recreations, its RESULTS.md: 88 % average
      match) copied to pipeline/motion_gfx/premium/ and wired in by premium_scenes.py: fit tests + roles per block
      (punch lines -> track_type / word_slide / blur_zoom_type / gradient_words / morph_word / card_pops, numbers ->
      odometer, percentages -> donut_card, lists -> list_circle / word_wheel / color_carousel, searched -> search_type,
      posted -> post_card, turned off -> toggle, card -> card_flip, money -> card_wheel, cart -> pill_split), quote shots
      alternate quote / glass_quote and line charts chart / chart_card, a block is only picked when the line lasts 55 %
      of its cycle and (non-looping) not more than 1.6x + 0.5 s; every reference default text/name/brand/number is
      overridden; block backgrounds 8 % oversized (camera + settle never show an edge); card_flip / card_wheel no camera;
      chart_card axis = the data's min/max; morph_word keeps its dark background (its blend trick needs it).
      Fonts added (OFL, assets/fonts/licences): Poppins Regular/Medium, Jost, Nunito, Modak, Bagel Fat One, Inter
      (copied from raju/typography). Test reel output/tests/premium_reel.md (all 19 via scene_order): final 1:25 in 371 s,
      33 scenes, -14.1 LUFS, true peak -1.3 dBTP; critique mean 8.97 -> 9.14, 7 scenes under 8 by their own design
      (donut_card holds then fades out, short pauses in gradient_words / list_circle / post_card, card_pops' hard
      pop-ins). The normal motion sample now picks 7 premium text blocks by itself (variety 7/8).
      Fixed on the way: scene_order prefers a data block that fits the line.
- [x] TYPOGRAPHY (2026-11-12, branch raju/typography, docs/SCRIPT_FORMAT.md "Typography"): header `typography:` = auto
      (default) | swiss | outline_pop | extrude | gradient | neon | marker | editorial | classic (= the look before),
      motion graphics only; Check error on other values. pipeline/motion_gfx/typography.py: per style a font pair, case,
      text effect (clean / outline + hard shadow / 3D extrude / vertical gradient / neon glow / tilted marker boxes /
      italic + underline swipe), key-word emphasis and a pool of word entrances, one per text scene, rotating: pop, punch,
      letters, drop, mask, type (typewriter + caret), wheel (slot-machine roll through the video's own words), weight
      (variable-font sweep), scramble (glyphs settle), flicker. swiss = Raju's reference video (Inter, light words + one
      heavy red word, red full stop, hairline crosshair + mono corner labels, swiss colour set). Kinetic / title /
      figure / memo text use it directly; big headline text of every other scene type in the palette ink is tagged ty-h
      and gets the effect. auto = the format's pool (typography.POOLS), least used in the last 5 videos (look part
      "typography" in data/asset_history.json); styles with their own fonts/colours override fonts/palette unless
      pinned. Fonts added (OFL, licences in assets/fonts/licences): Inter (variable), Bebas Neue, Archivo Black, DM Serif
      Display + Italic; new font pairs swiss, impact, heavy, editorial. Caption presets swiss_type, outline_3d,
      editorial. UI: Look & sound -> Typography tab (live samples with the render's own CSS; GET /api/typography,
      /api/fonts/<file>). Tests on the Mac: 7 style test drafts (~26 s each, 63-75 s), frames checked; fixed a double
      painted gradient title and kinetic lines ignoring the effect colour. Motion sample draft 1:14 in 183 s (auto ->
      Case File + marker), -14.1 LUFS; classic sample draft 9 s, -14.1 LUFS, pixel-identical to 2026-11-11 (PSNR inf);
      presets clean. Overlaps raju/camera-motion-transitions in render.py, formats.py, script_parser.py,
      render_server.py, ui/index.html (merge by hand). Not on a final yet.
      Type Studio (same day, same branch): `show: type_studio` = kinetic typography as the picture (the reference's
      look all the way through): swiss/editorial type, swiss colours, no frames / ambient shapes, no figures / icons /
      app windows; 5 new host scene types in pipeline/motion_gfx/type_scenes.py (type_kicker, type_wheel, type_swap
      with backdrop colour flips, type_stack, type_sentence) + kinetic, titles and clean data scenes. As_is type styles
      restore the script's own capitals in every scene's labels (typography.restore_case). Preview strip
      assets/format_previews/type_studio.jpg. Test: Windows vs MacBook (title copy, job 20261112-184016-da3f84) 7:41
      draft in 1172 s, -14.0 LUFS, 14 scene types in 187, top type 19.8 %, kinetic 10.7 %, 0 same twice, 0 A-B-A-B;
      fixed a double caret (blink tween rendered early). Regression after it: classic sample draft 9 s, -14.1 LUFS,
      PSNR inf; motion sample draft 192 s, -14.1 LUFS; presets clean.
- [x] INTEGRATION (2026-11-13, branch raju/integrate-typography-smooth): raju/smooth-motion (camera + transitions,
      delete videos, smooth motion, premium blocks) and raju/typography (typography styles, Type Studio) merged with
      both histories kept; 7 conflicted files resolved by keeping both sides (critique re-renders reuse the scene AFTER
      the typography effect). Type Studio got the camera era's settings: spring.soft pop ease, calm camera pool
      (dolly, truck, pull, focus) and no camera depth dots (ambient: False). Tests: presets clean; 15 scripts parse
      exactly as on their own branch, 0 errors; classic sample draft 0:30 in 18 s, -14.1 LUFS, same timeline/captions
      as main; motion sample draft 1:14 in 97 s (Case File + marker, critique 9.8 -> 9.85); Type Studio draft 1:14 in
      248 s (critique 8.57 -> 8.75: its still type holds count as dead frames); premium reel draft 1:25 in 336 s
      (critique 8.97 -> 9.13, same as its branch). Backups: tags backup/raju-*-2026-11-13 +
      output/backups/feature-branches-2026-11-13.bundle.
- [x] ONE-CLICK LAUNCHER (2026-11-13, branch raju/studio-launcher): tools/launch_video_studio.sh + tools/install_launcher.sh
      -> ~/Desktop/Video Studio.command (absolute path of this copy). Checks: the service's WorkingDirectory = this folder,
      clean tree + no half merge, GitHub reachable, local main not ahead of origin/main, no render running (asks); then
      switch to main, git pull --ff-only origin main, npm ci if a package-lock changed (warns on setup.sh), kickstart
      com.videostudio.server, waits for /login 200/302 from the NEW pid (90 s), opens the browser. Tailscale read only.
      The script runs as one function so the pull can replace it while it runs; the launcher runs origin/main's copy
      when the folder's branch doesn't have it.
- [ ] Phase 8 vertical motion + motion Shorts (not started).
        Root .gitignore venv entries are now anchored (/bin/ /lib/ ...) so motion/src/lib is tracked.
- [x] Video types (2026-11-09, docs/VIDEO_TYPES.md): type header + presets, two dashboard buttons, clip picker with
      preview, clip Shorts, pack export/import, cross-platform encoder + bundled fonts + UTF-8. Tested:
      Short from scratch (scripts/short_730_billion.md, job 20261109-121112-a44971): 37 s, draft 18 s, final 45 s
      incl. 1 new vertical [act:] image (21 s), later re-render 24 s; -14.0 LUFS; 1 cover; 4-file upload pack.
      Clip from the Sterling video made in the browser (job 20261109-120948-17c36f, 6:51-7:30 "My take"):
      38 s, rendered in 40 s, 0 new images. Earlier CLI clip 1:03-1:58: 55 s in 35 s, -14.0 LUFS.
      Full-video music per chapter + forced libx264 tested on the sample (-14.1 LUFS). Pack export 137 MB zip
      (112 files) in <1 s; import into a fresh copy at another path renders talk + card with libx264.
- [x] P0 presets layer (2026-11-09, cloud test copy on Linux, libx264, no music files there): parser output identical
      to before on all 5 scripts; sample draft before/after: 30.1 s, 7 shots, same shot timings, same captions file,
      -14.3 LUFS both (voice only, no music); with the same voice cache the audio is bit-identical and the picture
      differs only by encoder noise (61.0 dB PSNR vs 60.8 dB between two runs of the OLD code). job.json written,
      `captions: nope` = line-1 error with the valid ids, Sterling script passes Check, /api/presets 401 logged out.
- [ ] P0 on the Mac: draft + final of docs/sample_script.md in the browser (finals need mflux; music there), check
      -14.0 LUFS and job.json, compare render.log with an earlier sample job.
- [x] F6 art styles (2026-11-09, cloud test copy on Linux): default prompts + cache keys identical to the old code,
      `art_style: nope` = line-1 error listing the 8 ids, Sterling + art_style = warning with [act:]/[talk:] shots
      unchanged, dark_oil_painting draft shows the style under each placeholder, picker tested in a headless
      browser (8 tiles, pick writes the header on both screens), preview API rules (400 off-Mac, 409 while
      rendering / second preview, a second click doesn't regenerate).
- [ ] F6 on the Mac: make the 8 previews from the UI; finals of the sample in doc_photo, dark_oil_painting,
      graphic_novel (3 different looks, -14.0 +-0.2 LUFS each); re-make an old final and a clip Short and check
      render.log says 0 new AI images (needs a job that already has a final on this Mac).
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
- Start a task: `cd ~/youtube-pipeline && git switch main && git pull --rebase && git switch -c <name>/<task>`
- Finish a task: `bash tools/check_secrets.sh && git commit -am "..." && git push -u origin HEAD && gh pr create --fill && gh pr merge --squash --delete-branch`, then `git switch main && git pull --rebase`
- Secret check before every commit (must say "clean"): `bash tools/check_secrets.sh`
- Preset check (must say "presets: clean"): `bin/python tools/check_presets.py`
- GitHub login (gh CLI, your own account): `gh auth status`.
- Start Video Studio, then open http://localhost:8765 : `~/youtube-pipeline/bin/python ~/youtube-pipeline/render_server.py`
- Restart Video Studio (after code changes): `launchctl kickstart -k gui/$(id -u)/com.videostudio.server`
- One click (update to GitHub main + restart + open): Desktop `Video Studio.command`, made once per Mac with
  `bash tools/install_launcher.sh` (runs tools/launch_video_studio.sh; stops on unsaved work, local-only commits on main
  or a running render unless you say y; never resets/stashes; never restarts Tailscale).
- Stop it until next login: `launchctl bootout gui/$(id -u)/com.videostudio.server` (killing the process just restarts it)
- Check a script from Terminal: `~/youtube-pipeline/bin/python -c "from pipeline import script_parser as P; import json,sys; r=P.parse(open(sys.argv[1]).read()); print(json.dumps(r['errors']+r['warnings'],indent=1))" script.md`
- Logs: output/server.log (server), output/jobs/<id>/render.log (one video)
