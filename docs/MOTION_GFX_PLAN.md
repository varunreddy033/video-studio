# F10: motion graphics + rich sound (branch `f10-motion-sound`)

Status 2026-11-10: analysis and plan, plus the first sound pieces. The picture redesign is NOT built yet.

## 1. What the references do

Sources: two uploaded promos (frame-by-frame + audio measured here) and two long YouTube explainers
("Why the Stock Market Just Crashed", Paper Billions, 15 min; "What Happens to Your Money If the AI Bubble
Bursts", The Archivist, 10.5 min) analysed through vidIQ's video-watch (YouTube blocks downloads from the cloud
machine, so those two were not inspected frame by frame).

| | References | Our videos today |
|---|---|---|
| Picture | flat 2D vector scenes: simple characters (pill bodies, dot eyes, stick limbs), charts, maps, documents, big numbers on solid colour | AI photo held 6-10 s, then a dark card |
| Shot length | 2.5-5 s | 6-10 s |
| Something moves | every 1-2 s (pop-ins, counters, sliders, camera drift) | once per shot |
| Text | big numbers scale-pop with overshoot, counters tick, label pills slide in, keywords highlighted, handwritten title cards on black | static card, one fade |
| Transitions | mostly hard cuts; whip pans / pushes, zoom into an object, circle wipes | hard cuts only |
| Characters | cut-out puppets: bob, blink, arm gestures, face swaps | none (or the Sterling presenter) |
| Sound effects | 15-25 per minute: pops, clicks, whooshes, paper, cash register, stamps, plus scene sounds (train, door) | 0-6 per minute |
| Music | quiet steady lo-fi / synth bed, a little darker in crash sections | one bed |
| Captions | key phrase as a pill or caption chip that follows the voice | word captions at the bottom |

The two promos show the same language at Shorts speed: a scene change about every second, solid colour
backdrops (yellow, red, green, pink), one giant number or object per scene, and 80-90 bright sound hits a minute.

## 2. Built (2026-11-10): `rendering_method: motion`

Decisions taken (Raju, 2026-11-10): option A (hand-made HyperFrames templates, no AI pictures), bright pop look,
anonymous stick figures (no recurring host), reference-style caption chip at the top left.

How a motion video is made (all on the Mac, no network, no AI model; same script = same video):

1. Video Studio: pick **Pictures: Motion graphics** on the new-video screen (or write `rendering_method: motion`
   in the header). Check then defaults `captions: chip` and `sfx: auto`, hides the Art style tab, and skips the
   "picture held too long" warnings (motion shots change picture on every beat).
2. render_server -> jobs._run -> `pipeline/motion/render.py`:
   voice (Kokoro, same cache as always) -> timeline -> **beats** (beats.py: every shot cut into 1.2-3 s clauses on
   the voice's commas/full stops; a chapter's first beat starts with a 1.35 s chapter card) -> one **scene** per
   beat (templates.py) -> HyperFrames project in `output/jobs/<id>/motion/` -> `hyperframes check` (any lint or
   runtime error stops the render) -> 6 snapshots (`motion/snapshots/`) -> `hyperframes render` (local Chrome)
   -> the pipeline's own audio mix (voice + ducked music + timed SFX, -14 LUFS) and encoder (videotoolbox on the
   Mac) -> 3 thumbnails from frames + metadata + upload pack, as for every video.
3. Templates (picked from the shot tag and the narration words, never the same type twice in a row):
   kinetic words (each word lands on its spoken time, key words on a marker), stick figure(s) with a pose and
   props from 18 (chip, money, document, magnifier, globe, lock, camera, ship ...), big number (count-up),
   chapter/title slam, quote card, bar chart, memo/report with a DENIED / REPORTED / ALLEGED stamp.
4. Stick figures (figures.py): SVG rig (head, eyes, mouth, two-part arms, legs) moved with GSAP; poses idle, talk
   (mouth on the words), point, shrug, shocked, walk, sneak, think, cheer, worried; outfits plain, tie, spy,
   glasses. Anonymous on purpose: no faces of real people.
5. Look (design.py): 8 bright-pop palettes rotated so neighbouring scenes never share one, fonts Anton / Barlow /
   Poppins / Bangers (bundled, OFL), easing expo.out for text, back.out overshoot for pops.
6. Transitions (compose.py): cut inside a thought, push between beats of a shot, zoom / whip on a new shot,
   circle wipe on a new chapter (0.32 s overlap; the cut point stays where the narration starts).
7. Caption chip (`captions: chip`): white pill, top left, 2-4 words, the spoken word on a yellow marker, drawn by
   HyperFrames. Any other caption preset still works (burned in by libass as before).
8. Sound: every template and transition reports its own cues (pop-in, stamp, cash, paper, typing, whoosh/swipe,
   heartbeat for sneaking ...). `sfx: auto` keeps them >= 2.2 s apart, `sfx: rich` >= 1.4 s. A picker takes the
   least-used file of the best-matching library folder each time, so a video uses most of
   `assets/library/sfx/` instead of one file over and over. Each effect is limited to 70 % of the voice's peak.

How the installed skills are used: they are guidance for Claude, not programs, so the server can't "run" them.
Their rules are written into the code (see the table in `pipeline/motion/__init__.py`): hyperframes /
hyperframes-cli (render contract, check + snapshot first), kinetic-typography, motion-design,
animation-principles, shot-composition, beat-sync-editing, color-motion, ffmpeg-skill. Every render applies them
without Claude; new templates should be written with them open.

Draft = 960x540 (HyperFrames `--quality draft`), final = 1920x1080 or 1080x1920 for `type: short`.
Not supported with motion: `character:` scripts and `clip_from:` Shorts (Check error); `art_style:` is ignored
(Check warning).

## 3. Test (cloud copy, Linux, libx264, 2026-11-10)

`scripts/tests/motion_huang_spy_report.md` (reported allegations about Nvidia's CEO, every claim attributed):
final 1920x1080, 62.8 s, 24 scenes, -14.1 LUFS, peak -1.2 dB, 26 effects (25 a minute) from 18 different files,
music from `assets/library/music/mystery`, 3 thumbnails without the chip, upload pack. Every template also ran
on `docs/sample_script.md`. AI-image videos unchanged: parser output identical on all 5 scripts (new fields
only), `check_presets.py` clean, sample draft -14.1 LUFS.

Still to test on the Mac: the same script through the browser (draft + final), timing with videotoolbox.

## 4. Earlier on this branch

- `sfx: rich` for AI-image videos: an effect on almost every picture change (rotating whoosh / swipe / pop /
  click / bubble / paper) plus all `sfx: auto` rules.
- `tools/fetch_sfx_openverse.py`: CC0-only sound effects from Openverse into `assets/library/sfx/<kind>/`
  (no key; 20 searches a minute / 200 a day; CREDITS.md). Run on the Mac (Freesound refuses the cloud machine).
