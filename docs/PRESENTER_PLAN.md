# Presenter upgrade: from "AI slideshow" to "a character explains it"

Status: PLAN (2026-11-08). Reference: MonkeyExplains, "Why Hasn't The AI Bubble Burst (Yet)?" (a recurring animal
character presents finance topics). We build OUR OWN character, never a copy of theirs. Still Rs 0, still script-first.

## 1. Why our 10-min video felt AI-ish
1. No main character: every shot was a different, random image, so nothing tied the video together.
2. Narration came from "nobody": a flat voice over pictures, not a personality talking to you.
3. Stills with Ken Burns zoom read as a slideshow; there was no real camera depth or movement.
4. Inconsistent style: every image had a different look.

## 2. The new format (3 layers, mixed in every video)
| Layer | Share of runtime | What you see | How (all free, local) |
|---|---|---|---|
| **A. Presenter on camera** | 20-30% (hook, chapter intros, "my take", outro) | The character facing the camera, talking with a moving mouth, blinking, breathing, in its own "studio" | Character pose pack (made once) + mouth shapes + Rhubarb Lip Sync (MIT) timing + compositing in FFmpeg/Pillow |
| **B. Character in the story** | 40-50% | The same character acting out the narration: at a trading desk, staring at a crashing chart, in a server farm | FLUX.2 klein 4B with the character's reference images (multi-reference conditioning, up to 3 refs) + fixed style; then 2.5D parallax (below) |
| **C. Evidence** | 20-30% | Charts, numbers, quotes, real stock footage | What we have now (Pexels, graphics) |

**2.5D parallax:** Depth Anything V2 **Small** (Apache-2.0; NOT Base/Large, which are non-commercial) makes a depth map
for each still. The camera then moves through the image with the foreground moving faster than the background,
so it looks like a real camera move instead of a zoom.

## 3. The character (designed once, used forever = the channel's brand)
We write a **Character Bible** together in claude.ai first (docs/CHARACTER.md):
- name, species (cat / brain / other), look, outfit, colours, art style (one only: e.g. "stylised 3D animated film look")
- personality, how it talks, catchphrases, opening line, sign-off
- the Kokoro voice that fits it (pick by ear from 5-6 candidates), speed
- the exact prompt block used in every image: `CHARACTER = "..."`, `STYLE = "..."`

**Character pack** (assets/character/, generated once, then hand-picked by Varun):
- 3 master reference images (front, three-quarter, full body) chosen from ~40 generations
- presenter poses (talking straight to camera): neutral, pointing, shrugging, shocked, thinking, laughing, serious
- for each presenter pose: 6 mouth shapes (closed, slightly open, wide open, O, E, M/B/P) made by editing only the
  mouth area (FLUX.2 klein edit with the pose as the base image), plus eyes-closed for blinking
- backgrounds cut out with rembg (MIT) so poses can be placed on any set
- 2-3 "sets": its studio/desk, a stage with a screen, a street/outdoor set

## 4. Script format additions (SCRIPT_FORMAT.md v2)
```
[talk: pointing | studio]            presenter on camera for this beat, lip-synced (pose | set)
[talk: shocked | screen, zoom in]    optional camera: zoom in / zoom out / static
[act: sitting at a trading desk, sweating, red charts on monitors behind | wide]
                                     character-in-scene shot (prompt gets CHARACTER + STYLE + references)
[act: ... | close]                   framing: wide / medium / close
```
Existing tags ([stock:], [chart:], [number:], [quote:], [text:], [image:]) keep working.
Rule of thumb: start with [talk:], never more than 3 non-character shots in a row, and [talk:] at every chapter start.

## 5. Script writing changes (docs/CLAUDE_SCRIPT_PROMPT.md)
- Written in the character's voice, first person ("Okay, so here's what nobody tells you about..."), with its catchphrases.
- The character reacts: jokes, asides, "wait, it gets worse". One personal take per video.
- Shorter lines in [talk:] beats (lip-sync looks best at 1-3 sentences per pose change).

## 6. Build order (Claude Code on the Mac; test each step)
1. Benchmark: FLUX.2 klein 4B multi-reference consistency (same character in 10 different scenes) and mouth-area
   editing in mflux. If mflux can't do references/edits, fall back to: a fixed seed + a very detailed character prompt,
   and draw mouth shapes as overlay sprites. Report the results with a contact sheet.
2. Character pack generator script (`tools/make_character_pack.py`): N candidates -> Varun picks -> poses -> mouths
   -> blink -> rembg cutouts -> assets/character/.
3. Rhubarb Lip Sync install + `pipeline/presenter.py`: voice wav -> mouth cues -> frame-by-frame composite (pose +
   mouth + random blink every 2-6 s + 1-2% breathing scale + slight sway) over the set -> clip.
4. `[act:]` shots: character-conditioned generation + shared cache.
5. Depth parallax for all stills (`pipeline/parallax.py`, Depth Anything V2 Small), replacing Ken Burns by default.
6. SCRIPT_FORMAT.md v2 + parser + Check report (character share %, warnings for long non-character runs).
7. A 60-second pilot script written together -> render -> compare with the reference video -> tune -> then a 10-min video.

## 7. Cost and time
- Rs 0. All models are local and commercially usable: FLUX.2 klein 4B (Apache-2.0), Depth Anything V2 Small
  (Apache-2.0), rembg (MIT), Rhubarb (MIT), Kokoro (Apache-2.0).
- One-time: character pack about 1-2 hours of generation + 30 min of picking.
- Per 10-min video: more images than before (~40-60 character scenes), about 20-30 min of image generation on the Mac,
  using the shared cache + cool-down. Presenter clips reuse the pack, so they cost almost nothing.

## 8. Later (paid, after the channel earns)
Real talking-head animation from one image + audio (e.g. Hedra, Kling Avatar / OmniHuman on Fal) for the [talk:] beats
only. Same script tags, a different engine switch.

## 9. Policy notes
- YouTube "altered or synthetic content" disclosure applies when the content looks realistic; a stylised cartoon
  character usually doesn't need it, a photoreal one may. Decide when choosing the style.
- An original, consistent character with a personality is a strong originality signal (good for the inauthentic-content review).
