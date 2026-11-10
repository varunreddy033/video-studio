# script.md format

A script is plain text: a short header, then narration with shot tags.
Paste it into Video Studio (http://localhost:8765), press **Check**, then **Make draft**.

## 1. Header (between two `---` lines)

```
---
title: Is the AI Bubble About to Pop?        (required, max 100 characters)
description: |                                (optional, indent the lines below by 2 spaces)
  First paragraph of the YouTube description.
  Second paragraph.
  #AI #Stocks
tags: ai bubble, stock market, nvidia         (comma separated)
type: full                                    (full = 16:9 long video (default), short = 9:16 Short, 15 s-2:00)
music: misdirection, soaring                  (track names from assets/audio/bgm; full videos: one per
                                               chapter in this order, crossfaded; one name = one track)
voice: am_michael                             (optional: a voice preset id, or a Kokoro voice: am_adam, am_eric,
                                               bm_george, bm_lewis, af_heart ...)
speed: 1.0                                    (optional voice speed)
language: en                                  (optional preset keys, see "Presets" below)
captions: amber_word
art_style: doc_photo                          (look of the AI images: pick it in Video Studio after Check)
thumbnail: THE BUBBLE?                        (big thumbnail text, 2-4 words work best)
thumbnail_prompt: a giant glowing soap bubble over a city at night
---
```

`format:` (landscape / vertical) still works for full videos; a Short is always vertical.

### Presets (optional header keys)

Voice, captions, art style and music are presets: JSON files in `presets/<kind>/<id>.json` (the id is the file
name). Leave a key out and the default preset is used, which is exactly how videos looked before presets existed.

| Key | Folder | Default | Also accepts (old style, still works) |
|---|---|---|---|
| `language:` | languages of the voice presets | `en` | |
| `voice:` | `presets/voices/` | `en_us_michael` | a Kokoro voice id (`bm_george`); `character:` still sets its own voice |
| `captions:` | `presets/captions/` | `amber_word` | |
| `art_style:` | `presets/art_styles/` | `doc_photo` | |
| `music:` | `presets/music/` | `any` | track names from `assets/audio/bgm` (`misdirection, soaring`) |

A preset id that doesn't exist is an error at Check, and the message lists the valid ids. Every render writes
`output/jobs/<id>/job.json` with the presets it used and anything that overrode them (script, character, .env).
All of these are picked in Video Studio after **Check**, in the **Look & sound** card (tabs: Voice, Music,
Captions, Sound effects, Art style). A click writes the header line for you. Check all preset files with
`bin/python tools/check_presets.py`.

### Voice (`voice:`)

28 English Kokoro voices (20 American, 8 British), each `presets/voices/<id>.json`: `voice: en_us_heart`,
`voice: en_gb_george`... The Voice tab plays a sample of each (made on first click) and shows Kokoro's own quality
grade (A is best). A Kokoro id (`voice: bm_george`) still works, `speed:` still sets the pace, and a voice in the
header replaces a character's own voice.

### Captions (`captions:`)

| id | Look |
|---|---|
| `amber_word` (default) | short phrases, the spoken word turns amber |
| `big_word` | one heavy word at a time, popping in |
| `red_pop` | two tall words, the spoken one red |
| `soft_glow` | clean capitals with a soft glow |
| `karaoke_box` | a violet box jumps from word to word |
| `italic_punch` | slanted capitals, the spoken word yellow |
| `comic` | comic lettering, tilted |
| `serif` | small-caps serif |
| `pixel` | retro game lettering |
| `clean_lower` | friendly lowercase |
| `none` | nothing burned in (the .srt for YouTube is still made) |

Each style is a file in `presets/captions/` (font, colours, words per phrase, sizes for full videos / vertical /
Shorts); the fonts are in `assets/fonts` (all SIL Open Font License).

### Music (`music:`)

Tracks live in `assets/library/music/<mood>/` (in git; `assets/library/README.md` says how to upload) and in the
old `assets/audio/bgm`. `music: calm` = a random track of that mood (the same in draft and final), `music: track
name` = that track, `music: calm, tense, epic` = one per chapter (full videos), `music: none` = no music, no line
= any track.

### Sound effects (`sfx:`)

`sfx: script` (default) plays only the `[sfx: ...]` tags in the script. `sfx: auto` also places effects by fixed
rules (pipeline/sfx.py): whoosh on title cards and new chapters, ding / cash on numbers, typing on quotes, riser
on charts, and narration words like "crashed" (impact), "suddenly" (riser), "hacked" (glitch); at most one per
shot, at least 3 s apart. `sfx: off` plays none. Sounds are `assets/library/sfx/<kind>/` (13 starter sounds
included; your own file in a folder replaces the starter one).

### Art style (`art_style:`)

The look of every `[ai:]` and `[stock:]` image and the 2 AI thumbnails. After **Check**, Video Studio shows an
"Art style" card: click a style and it writes `art_style: <id>` into the header and checks again (on the new-video
screen and in a video's Script editor). Each tile can make a preview (~25 s, on the Mac, one at a time, not while
a video renders); previews are kept in `assets/style_previews/`.

| id | Look | Realistic* |
|---|---|---|
| `doc_photo` (default) | natural documentary photos (the look before art styles existed) | yes |
| `cinematic_film` | movie still: shallow depth of field, colour grade, grain | yes |
| `archival_bw` | old black-and-white press photos | yes |
| `dark_oil_painting` | moody old-master oil painting | no |
| `graphic_novel` | inked comic panels, flat shading, halftone | no |
| `noir_neon` | rainy night, magenta and cyan neon | yes |
| `isometric_3d` | miniature 3D dioramas | no |
| `paper_cut` | layered paper craft | no |

*Realistic styles: tick "Altered or synthetic content" in YouTube Studio. With a `character:`, the art style only
changes `[ai:]`/`[stock:]` shots; `[act:]` scenes and presenter thumbnails keep the character's own STYLE (Check
warns). A new style means new images, so the first final in it makes every AI image again (Check shows how
many are still to make). Each style is `presets/art_styles/<id>.json`: `prefix` + your prompt + `stock_suffix`
(`[stock:]` only) + `suffix`. In `doc_photo`, `.env IMAGE_STYLE` (if set) still replaces the suffix.

### Short from a video you already made (no body needed)
```
---
type: short
clip_from: 20261108-184222-d0b89e             (the finished video's job id)
clip_start: 6:51                              (minutes:seconds; the cut snaps to the gaps between words)
clip_end: 7:30
title: My take on the AI bubble #Shorts       (optional; default = the video's title + #Shorts)
---
```
The page does this for you: **Make Short → From a video I already made**.

### What changes with `type:` (docs/VIDEO_TYPES.md)
| | full | short |
|---|---|---|
| Size | 1920×1080 | 1080×1920 |
| Length | planned 10-14 min (warning outside 8-16) | 15 s to 2:00 (**error** outside that) |
| Picture held longer than | 12 s photo / 10 s graphic / 25 s talk = warning | 6 s photo or graphic / 10 s talk |
| Chapters | `## ` headings, 3+ | none (headings are ignored) |
| Hook / ending | first 8 s / question for the comments | first 2 s, no "today we'll..." / a line that loops back to the start |
| Music | per chapter, crossfaded | one track, short fade so it loops |
| Captions | bottom, standard | bigger, higher, clear of the bottom 20% and right 12% (Shorts buttons) |
| Thumbnails | 3 options | 1 vertical cover |
| Description | as written + chapters | + `#Shorts` |

## 2. Body

- `## Heading` starts a chapter. Put one before the first narration and use at least 3 so YouTube shows chapters.
- Every other line is **narration** (spoken by the voice). A blank line between paragraphs = a short breath.
- A **shot tag** on its own line (or in the middle of a line) changes the picture **exactly where the next
  words start**. The picture stays until the next shot tag.

### Shot tags

| Tag | What you get |
|---|---|
| `[ai: a giant soap bubble floating above a skyline at dusk, cinematic]` | An AI image (FLUX.2, made on the Mac) with a slow camera move (8 different moves). No text, logos or real people's faces. |
| `[stock: crowded city street at rush hour]` | The same, styled as a real-world documentary photo. Use it for everyday scenes. |
| `[card: THE REAL QUESTION \| small line under it]` | Big text card |
| `[number: 3.2 \| trillion dollars \| prefix=$ suffix=T]` | Animated count-up number (`$3.2T`, `45%` also work as the value) |
| `[quote: The exact quote. \| Who said it, where]` | Quote card. Only real, checked quotes. |
| `[chart: bar \| Title \| 2022: 0.4, 2023: 1.2, 2024: 3.3]` | Animated bar chart (`line` for a line chart; add `\| unit=%` for a unit) |

### Other tags

| Tag | What it does |
|---|---|
| `[sfx: whoosh]` | Sound effect at the next words (matched to file names in assets/audio/sfx) |
| `[pause: 1.5]` | Silence (seconds) before the next words |

### Presenter shots (needs `character:` in the header)

Add `character: sterling` to the header to load `docs/characters/sterling.md` (its CHARACTER and STYLE prompt
blocks, SEED, voice, poses and sets). The header's own `voice:` / `speed:` still win if you set them.

| Tag | What you get |
|---|---|
| `[talk: pointing \| studio]` | The character on camera, lip-synced to the narration, blinking and breathing, on a set. Poses: neutral, pointing, shrug, shocked, thinking, serious, laughing. Sets: studio, stage. Optional camera: `[talk: shocked \| studio \| zoom in]` (static, zoom in, zoom out). |
| `[act: sitting at a trading desk, looking worried \| medium]` | The character acting out the story in a scene (framing: wide, medium or close). Same character every time (fixed seed + CHARACTER + STYLE). |

Rules of thumb: open the video and every chapter with `[talk:]`; never more than 3 shots in a row without the
character (Check warns); `[talk:]` beats can run up to 25 s (Check warns above that), everything else 10-12 s.
Check shows the character's share of the runtime (aim for 50-70%).

## 3. Pacing rules that keep viewers watching

- Change the picture every **5-10 seconds** (about 13-25 spoken words). Check warns above 12 s.
- Mix shot types: roughly **65% AI images** (6-10 s each) and **35% cards, numbers, quotes and charts**
  (3-6 s each; they render instantly, so they also make the final faster).
- About **45-55 AI images per 10-minute video**. Each takes ~25 s in the final render, so a 10-minute video's
  final takes roughly 20-25 minutes. Every image is cached, so re-making a final only redoes changed shots.
- The first 8 seconds are the hook. End with a question for the comments.
- Write for the ear: short sentences, no abbreviations ("for example", not "e.g.").

## 4. Example

See `docs/sample_script.md` (the **Load sample** button in Video Studio).
