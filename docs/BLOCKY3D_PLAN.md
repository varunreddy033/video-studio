# Blocky 3D story style: reference analysis + plan (2026-11-17)

Status (2026-11-17, branch raju/blocky3d): step 1 spike, step 2 script format + Check, assets (24 CC0 Kenney packs,
assets/blocky3d) and step 5 renderer DONE; steps 3-4 done in a first version inside the renderer (own rig with 6 hair
styles, 5 shirt kinds, 9 faces + talking mouth, 16 actions; 13 sets laid out from the Kenney packs in
pipeline/blocky3d/sets.py; 4 grades). Step 7 partly: the Pictures picker offers Blocky 3D (no cast/set/grade tabs
yet). Step 8 (HUD counter) not started. The final tag syntax is docs/SCRIPT_FORMAT.md section 6.

Sources: 6 reels in output/references on Raju's Mac (copied from Downloads; output/ is gitignored, the videos are not ours).
Measured locally: ffprobe, ffmpeg scene cuts (scdet 12), whisper.cpp small (CPU) transcripts, EBU R128 loudness,
earshot timeline (v1), 24-frame contact sheets (*.sheet.jpg), consecutive-frame strips (strips.jpg).
Not measured: per-frame motion curves for every video, earshot on v2-v6, beat grids.

## 1. Measurements

| # | Account | Size / fps | Length | Cuts | Avg shot | Words/min | Loudness |
|---|---|---|---|---|---|---|---|
| v1 | craftee_films (island of girls) | 720x1280 / 60 | 36 s | 29 | 1.2 s | 315 | -14.1 |
| v2 | polystoriesdaily (IQ doubles) | 1080x1920 / 30 | 84 s | 29 | 2.8 s | ~20 (meme audio) | -14.3 |
| v3 | robloxstoriesevryday (camouflage game) | 720x1280 / 30 | 159 s | 108 | 1.5 s | 225 | -14.1 |
| v4 | robloxstoriesevryday (shadow world) | 720x1280 / 60 | 93 s | 74 | 1.2 s | 260 | -14.2 |
| v5 | btroll_monster (rain monsters) | 720x1280 / 30 | 63 s | 29 | 2.1 s | 195 | -14.1 |
| v6 | craftee_films (world gone but crush) | 720x1280 / 30 | 35 s | 32 | 1.1 s | 323 | -14.1 |

Everything is vertical 9:16 Shorts/Reels at -14 LUFS (same target as ours).

## 2. Style specs

### v1 + v6 craftee_films: "first-person what-if, blocky avatars, bright daylight"
- Category: first-person "I woke up and..." romance/comedy what-if with a twist ending, 35 s. Recurring hero
  (same green-striped shirt + spiky green hair in both videos = series identity).
- Look: blocky game avatars (box head/torso/limbs), flat textured clothes, painted faces with big emotive eyes;
  bright saturated sky blue + sand/grass; soft sun shadows, light bloom; low-poly sets (beach huts, palm trees,
  city streets, cafeteria, football field). Crowds of 300 extras = instanced avatars with varied clothes.
- In-world signs carry the plot: a stone tablet with pictograms (stick girl + boy -> rings), tally marks, a
  handwritten note in close-up. No UI overlays.
- Camera: mostly locked or a slow push-in at chest height, low angle on the hero, close-ups on the face for
  reactions, quick over-the-shoulder; rare tracking on runs. Hero idles (arm swing, breathing) so frames never die.
- Pacing: one shot per clause (~1.1-1.2 s), hard cuts, every noun shown literally ("cliff" -> on a cliff,
  "tree" -> shaken out of a tree). Hook = the world rule in the first 2-3 s.
- Captions: 2 lines, upper third, white bold sans, the key word in caps + green; switch per phrase.
- Audio: very fast, flat male VO (~320 wpm), trap / future-bass bed under it, LRA 1.2 LU (heavily compressed),
  a whoosh or pop ~60 ms after most cuts, sub-bass hits on reveals. Not cut to the beat.

### v3 + v4 robloxstoriesevryday: "In this world..." dark-rule stories, longer
- Category: "In this world, [deadly rule]" third-person adventure, 1.5-2.5 min, named characters, chapters of
  action. v3 daylight arena game show; v4 night, purple/blue grade, glowing purple eyes, shadow monster.
- Look: same blocky avatars, more varied cast; strong colour grading per story (v4 whole video tinted blue-violet,
  emissive purple accents, fog); colour-coded painted characters (v3: bodies painted to match walls).
- Camera: slow dollies and push-ins, high-angle crowd shots, low hero angles on monsters, a scoreboard prop
  counting 10 -> 1. Characters gesture (waves, points, falls).
- Captions: ONE word at a time, centred, white with a dark outline (word-by-word = our big_word idea).
- Audio: narration ~225-260 wpm, tense/cinematic bed (not measured in detail).

### v5 btroll_monster: "horror-lite rule story, foggy 2.5D look"
- Same avatar family, but a foggy, desaturated blue-grey world, low-poly town, rain streaks, a giant grey
  monster (a non-blocky creature model) towering in the fog.
- Camera: wide establishing shots high above, tracking behind the running kid, a crane pull-up, worm's-eye
  views up at the monster: the most "cinematic" of the six. Shots ~2 s.
- Captions: small white phrase, upper third. Narration ~195 wpm.

### v2 polystoriesdaily: "voxel 3D escalation counter"
- Category: "What if your IQ doubled every time you locked in?" a pure escalation reel, almost no narration
  (meme audio + music). Voxel/low-poly character in a dark dorm at 3 AM, warm desk lamp, emissive windows,
  equations glowing in the sky, the city lighting up, Earth from space, then a wireframe "simulation" shot.
- HUD overlay: big serif number (IQ 112 -> 1,677,721,600) top-left, small caps label, one italic line per beat.
- Camera: steady push-ins and pull-backs; the scale grows (desk -> campus -> city -> planet). ~2.8 s per beat.
- Looks rendered in Blender/Unity (soft GI, bloom); the same idea works in Three.js with emissive + bloom.

## 3. Cross-video comparison

Common to 5 of 6: blocky avatars with painted faces, low-poly sets, one literal shot per clause (1.1-2 s),
a "world rule" hook in the first sentence, a twist or payoff in the last 3-5 s, -14 LUFS, whoosh/pop on cuts,
fast narration (195-323 wpm vs our Kokoro default 155), vertical only.
They differ in: grade (bright day / night violet / fog), caption style (2-line highlight / 1 word / small phrase),
length (35 s - 2.5 min), camera (static push-ins vs cinematic tracking).
v2 adds a HUD counter overlay + escalating scale; it fits the same renderer as an overlay, not a separate type.

Animation categories found: (A) blocky game-world story (v1, v3-v6) and (B) 3D escalation what-if with a HUD
(v2). Both are covered by ONE new rendering method with options; no separate apps.

## 4. Recommended new rendering type: `rendering_method: blocky3d`

What makes them work (and what we must build): a small reusable cast, sets that can be re-dressed, an action
library, a camera grammar, one shot per clause, literal props, a strong grade per story.

Name note: never call it "Roblox" in the code, UI, titles or thumbnails, and don't copy Roblox's default faces,
logo, UI or signature avatars: Roblox is a trademark. The blocky-figure look itself is generic; our avatars,
faces and sets are our own.

### How a scene is produced (no LLM in the pipeline, like today)
Claude chat writes script.md in a new tag set (prompt E in docs/CLAUDE_SCRIPT_PROMPT.md). Draft:

```
type: short
rendering_method: blocky3d
cast: me = hero_green_stripes, crush = goth_girl, crowd = islanders x300
set: beach_day
grade: bright        (bright | night | fog | dusk)
captions: keyword_2line

[shot: me | idle | push_in]
I woke up on an island where only girls live.
[shot: crowd, me | chase | track_back | set=cliff]
On day one, they chased me off a cliff.
[sign: tablet | stick_girl + stick_boy -> rings]
And by island law...
[hud: IQ {n} | doubles]     (v2-style counter, optional)
```

The parser turns it into shots.json (one shot per tag, cut where its narration starts, exactly like visuals.py).

### Tech (recommended): Three.js scenes inside our existing HyperFrames render
- One HyperFrames project per video, one sub-composition per shot, each a Three.js canvas drawn from timeline time
  (the hf-seek protocol; deterministic, seeded). Same `hyperframes render` path as motion_gfx -> picture.mp4,
  then our existing captions, _mix_audio (voice + music + SFX), loudnorm -14, encoder, thumbnails.
- Avatars: procedural, ~6 boxes (R6-like rig: head, torso, 2 arms, 2 legs) with canvas textures for clothes
  (stripes, jacket, dress...) and a few blocky hair meshes. Faces = SVG decals with emotion states
  (neutral, happy, scared, angry, sad, smirk, shocked, eyes shut) and mouth shapes driven by Kokoro's phoneme
  timings (pipeline/presenter.py already computes them).
- Actions: code-defined keyframe clips on the rig (idle, walk, run, jump, fall, sit, lie, wave, point, carry,
  dance, scared, celebrate, climb, push), offset per limb (head leads, arms follow), springs from spring.py.
- Sets: CC0 low-poly kits (Kenney, Quaternius: city, nature, furniture, holiday; all CC0) stored in
  assets/library/models/<kit>/ with licence + tags (asset library rule), assembled into ~10 named sets
  (beach, city street, house interior, school/cafeteria, park, arena/stadium, night town, forest, dorm room,
  space/earth) as JSON layouts.
- Crowds: InstancedMesh with seeded clothes/colours (300 avatars cheap).
- Camera grammar: locked, push_in, pull_out, track (follow), orbit_slow, crane_up, low_angle, high_angle,
  over_shoulder, close_up, whip; picked per shot from the action when the tag gives none (like planner.cameras).
- Grades: presets/blocky_grades/<id>.json = sky, fog, light colours, shadow softness, bloom, LUT-like tint.
- Signs/notes/HUD: HTML/SVG layers over the canvas (we already draw these well in motion_gfx).
- Captions: new caption presets `keyword_2line` (v1/v6) + reuse big_word for one-word (v3/v4).
- Voice: Kokoro speed ~1.3-1.4 for the fast style (current Shorts presets are ~155 wpm).
- SFX: auto cues on cuts (whoosh/pop ~1-2 frames after the cut), hits on reveals; library already has them.

Why not Blender: better light, but 10-30 min per minute on a fanless Air, a second toolchain, no reuse of
HyperFrames/GSAP/critic. Keep it as a later option only if Three.js can't reach the look.

### Pipeline mapping (what becomes presets)
- presets/blocky_cast/<id>.json: avatar (skin, hair, shirt texture, pants, accessory, face set, voice).
- presets/blocky_sets/<id>.json: set layout (kit pieces + positions), default camera spots, time of day.
- presets/blocky_grades/<id>.json: the look.
- presets/captions: keyword_2line.
- Header keys: cast, set, grade (+ existing voice, music, captions, sfx, type). Check errors on unknown ids.
- job dir: output/jobs/<id>/blocky/ (shots.json, project, per-shot renders) -> resumable per shot.

## 5. Missing skills / tools (nothing installed; you decide)

| Tool | Purpose | Adds | Licence | Mac M5 | Install |
|---|---|---|---|---|---|
| three (npm, pinned) | 3D in the HyperFrames page | the renderer | MIT | yes (WebGL in headless Chromium) | root package.json + npm ci |
| postprocessing (npm) | bloom, SSAO, vignette | the "game engine" polish | Zlib | yes | npm |
| Kenney 3D kits | city, nature, furniture, holiday props | sets in days, not weeks | CC0 | n/a (files) | download once into assets/library/models |
| Quaternius packs | low-poly nature, town, monsters | creatures like v5's monster | CC0 | n/a | download once |
| Mixamo animations | mocap clips | NOT recommended: Adobe terms forbid redistributing the raw files in a repo; we write our own clips |
| A Three.js skill | patterns for Three.js | optional; hyperframes/references/runtimes.md + types/3d.md already cover seeking | - | - | find-skills "threejs" |

No new AI model needed. FLUX is not used by this style (optional later: AI sky/backdrop plates).

## 6. Roadmap (each step on its own branch, tested, like the motion graphics plan)

1. Spike (1-2 days): one 15 s vertical test outside the pipeline: one set, 2 avatars + a crowd of 100, run/idle/
   scared, 6 shots, 4 camera moves, bloom + shadows. Measure ms/frame on the M5 Air at 1080x1920.
   Go/no-go on the look before building more.
2. Parser + Check: header keys, [shot:] [sign:] [hud:] tags, shots.json, line-number errors, Check card.
3. Avatar system: rig, textures, hair, 8 faces, lip-flap from Kokoro phonemes, 15 action clips, 6 cast presets.
4. Sets: import 2 CC0 kits into the library, 6 set layouts, 3 grades (bright, night, fog).
5. Render path: rendering_method blocky3d in jobs.py -> HyperFrames render -> existing captions/audio/encode;
   critic (smoothness) on the result; per-shot cache.
6. Captions keyword_2line, SFX auto cues, prompt E for Claude chat, sample script docs/sample_blocky3d_script.md.
7. UI: Look & sound tabs for cast / set / grade, storyboard support later.
8. HUD overlay (v2 counter) + escalating-scale sets (city, earth).

## 7. Performance on the MacBook Air M5 16 GB (MEASURED, spike 2026-11-17)
- Spike (output/blocky3d_spike/make.py + project/assets/js/world.js, Three.js 0.170.0 in that folder only):
  11.4 s, 1080x1920, 30 fps, 6 shots, hero + 300 instanced crowd, town square, soft shadows, ACES tone mapping,
  2-line keyword captions: HyperFrames render 342 frames in 7.7 s = 22 ms/frame (auto workers, browser GPU);
  sound (voice + ducked music + whoosh per cut) + mux 0.4 s; -14.1 LUFS; frame critic: 0 dead frames, every
  shot 10/10. No bloom / SSAO yet (would cost more per frame).
- So a 60 s Short ~ 40-60 s of picture. Speed is not the risk; the look and the acting are.
- The render has to run outside Claude Code's sandbox (HyperFrames' lock in ~/.cache/hyperframes + the GPU).

## 8. Limits and risks
- Our pipeline has no 3D today: this is the largest build so far (~2-3 weeks of steps above).
- Headless WebGL speed/quality on the Air is the main unknown (spike first).
- Acting quality: hand-written clips look stiffer than a game engine's; mitigated by springs, limb offsets, idles.
- Scripts must name shots explicitly (no LLM in the pipeline): prompt E has to teach Claude chat the tag set.
- Story twists and the "literal shot per clause" density depend on the script, not the renderer.
- Trademark: no Roblox name/logo/default faces anywhere in output.
- Kokoro at speed 1.4 can slur; test before committing to the 300 wpm style.
- Vertical motion (Phase 8) isn't built for motion_gfx; this style is vertical-first, so it needs type: short sizes.
