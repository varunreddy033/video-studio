# Motion style: from "Sterling + slides" to animated explainer

Status: PLAN (2026-11-10). Reference: Varun's screen recording of a flat 2D finance explainer (48 s, studied
frame by frame). Goal: videos that feel animated and alive, not a slideshow. Rs 0. The current pipeline stays
as `style: classic`; this adds `style: motion`.

## 1. What the reference actually does (and we don't)
| Technique | In the reference | In our videos now |
|---|---|---|
| **Camera-move transitions** | Scenes push off to the left while the next slides in from the right, with a soft dark shadow band on the edge. Some tilt (new scene drops in from the top). One **zooms through** an object: the camera dives into a jar's opening, and the inside of the jar becomes the next scene. It feels like one continuous world. | Hard cuts between full-screen pictures |
| **Elements animate one at a time, on the word** | Four doors grow in one by one as each is named, each with a label tag. A chart line draws itself while "-5.5%" counts up. A money pile shrinks. Question bubbles pop over heads. | One still per shot, with a slow zoom |
| **Headline pill** | An empty rounded pill appears at the top, then fills word by word in sync with the voice ("FOUR DOORS INTO YOUR MONEY."); unspoken words are greyed. No subtitles at all. | Subtitle captions at the bottom |
| **Something moves every 1-2 s** | Idle bob, blinking, small pops, labels sliding in | Mostly static between cuts |
| **One flat design system** | Flat 2D vector art, one palette per scene, subtle dashed-texture backgrounds, consistent bold rounded font (Montserrat-like) | 3D renders, AI photos and cards in different looks |
| **Characters are puppets inside the scene** | Small flat characters at the side or bottom, reacting (worried face, pointing) | Sterling full screen, or the story without him |

The look comes about 70% from motion (transitions, word-synced pop-ins, constant small movement) and 30% from art
consistency. Motion is pure code, so we can match it closely. Art quality grows with our prop library.

## 2. New architecture (style: motion)
```
script.md (v3 scene tags)  ->  parser  ->  timeline.json  (scenes, layers, element cues tied to word indexes)
                                   |
Python (unchanged roles): Kokoro voice + word timings, FLUX props/plates, rembg cutouts, music/SFX mix, loudnorm,
                          thumbnails, upload pack
                                   |
motion/  (Remotion project, React + TypeScript)  renders the PICTURE from timeline.json at 1080p
         -> video-only file  ->  FFmpeg muxes it with the mixed audio  ->  final.mp4
```
Remotion is free for individuals and teams of up to 3 people, commercial use included (check remotion.dev/license
again if this ever becomes a company with more than 3 people). It has built-in slide, wipe, flip, fade and clock-wipe
transitions, and custom transitions are supported.

### Building blocks (made once, reused in every video)
1. **Transitions** (custom presentations): push left/right/up/down with a shadow band, **zoom-through** (into any
   element, which becomes the next scene), iris, whip pan, match cut, and a plain cut. A chooser varies them, never the
   same twice in a row: "next point" = push from the right, "going deeper" = zoom-through, "consequence / fall" =
   drop from the top, "flashback" = push from the left.
2. **Element animations**: pop (scale with overshoot), grow from the floor, slide in, draw-on (SVG stroke), count-up,
   shrink, shake, fade, stagger for groups, plus idle float/bob/blink on everything.
3. **Headline pill**: empty pill appears, words fill in as they are spoken (matched to Kokoro word timings).
4. **Label tags**: small white tags that point at elements ("TOP 10 = 40%").
5. **Data components**: line chart (draws + end value counts), bar chart (bars grow), pie (fills), big number,
   calendar page (date flips), comparison split, ranking list, map with pin (Natural Earth, public domain).
6. **Prop library**: about 40 parametric SVG props written in code (coins, money stack/pyramid, bubble, doors,
   envelope, jar, lightbulb, question/exclamation bubbles, arrows, skyline, server rack, phone, laptop, chip,
   factory, bank, house, calendar, clock, magnifier, shield, crown, rocket, chart frame...). One palette file themes them.
7. **Generated props**: anything not in the library ("a pair of white wired earphones") is made by FLUX.2 klein in a
   new `flat_vector` art style, cut out with rembg, cached in assets/library/props/, and reused in later videos.
8. **Sets**: flat background plates (city at night, ocean, stage, office, street) from SVG patterns or FLUX flat style, no text.
9. **Sterling Flat**: a flat 2D version of Sterling (same design: grey-white cat, navy blazer, burgundy tie) as a
   puppet layer: poses, mouth shapes, blink, lip-synced from Kokoro's phoneme timings, placed anywhere in a scene at
   any size. Built with the existing pack tool using a flat STYLE block; a vector (SVG) puppet is the fallback if the
   image model can't keep a flat character consistent.

## 3. Script format v3 (only for style: motion)
```
---
style: motion
palette: navy                     (one palette per channel keeps the look consistent)
character: sterling_flat
---
## The bubble
[scene: city_night | from: top]                  new scene; how the camera arrives
[char: thinking | left]                          Sterling's pose and place (lip-sync is automatic)
The AI boom has built the biggest bubble in market history.
[+ bubble: AI | center | pop]                    add an element at the next word
[head: IS THE AI BUBBLE BURSTING?]               headline pill, fills as the words are spoken
Everyone is asking the same question.
[+ question | over char | pop]
[scene: doors | from: zoom bubble]               zoom through the bubble into the next scene
[+ door: FUND | 1 of 4 | grow] There are four doors into your money. Your fund,
[+ door: PENSION | 2 of 4 | grow] your pension,
[+ door: JOB | 3 of 4 | grow] your job,
[+ door: BILLS | 4 of 4 | grow] and your bills.
[+ gen: a pair of white wired earphones | right | slide]   AI-made flat prop, cached
[- bubble]                                       remove an element
```
[number:], [chart:] and [quote:] become in-scene elements. [talk:] (Sterling full screen) still works for punchy
moments. Claude (chat) writes v3 scripts directly; Claude Code gets a "storyboard" command that turns a plain
narration script into v3 for review.

Pacing rules (Check enforces): a new element or change at least every 3 s; a new scene every 6-15 s; a headline in
every scene; transitions vary.

## 4. Build order (each phase ends with something to watch)
1. **Look test first**: Remotion in motion/, then a 30-second hand-built demo of 3 scenes in this style (the doors
   with labels and a typing headline; a chart that draws while the number counts; a zoom-through and a push).
   No pipeline yet. Varun approves the look before anything else is built.
2. **Bridge**: timeline.json contract, Python -> Remotion render command (with concurrency), audio mux, timings on
   the job page.
3. **Parser + Check** for v3 tags, with one preview frame per scene on the Check page.
4. **Library**: 40 SVG props, data components, headline pill, label tags, idle motion, the transition set + chooser,
   2 palettes.
5. **Flat art style**: `flat_vector` preset for generated props and set plates, cutouts, prop cache.
6. **Sterling Flat**: benchmark flat consistency + mouth edits (as in presenter step 1), then build the pack and
   in-scene lip-sync.
7. **Real test**: re-make the EarPods video in motion style (Claude writes the v3 script), compare side by side.
8. **Shorts**: vertical layouts for the same scenes.

## 5. Rules
- Our own look: our palette, our props, Sterling. Never copy the reference channel's characters or designs.
- Keep `style: classic` working; motion is opt-in per script.
- Measure render time in phase 2 and log it on the job page.
