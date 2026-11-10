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
voice: am_michael                             (optional: am_adam, am_eric, bm_george, bm_lewis, af_heart ...)
speed: 1.0                                    (optional voice speed)
thumbnail: THE BUBBLE?                        (big thumbnail text, 2-4 words work best)
thumbnail_prompt: a giant glowing soap bubble over a city at night
---
```

`format:` (landscape / vertical) still works for full videos; a Short is always vertical.

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
