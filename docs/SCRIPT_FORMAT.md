# script.md format

A script is plain text: a short header, then narration with shot tags.
Paste it into Video Studio (http://localhost:8765) and press **Check**. When Check has no errors (warnings are
fine) two buttons appear: **Make final** goes straight to the final (video, thumbnails, metadata.txt,
captions_final.srt, upload pack), **Draft first** makes a quick low-resolution draft to review, then you press
Make final on the video's page. The same two buttons are on a video's page and for Shorts; the browser remembers
which one you used last and draws it as the main button.

Two ways to make the pictures (the **Pictures** menu on the new-video screen writes the header line for you):

| `rendering_method:` | Pictures | Samples (**Load sample** follows the Pictures menu) |
|---|---|---|
| `motion` (default, no line needed) | bright-pop motion graphics: kinetic words, stick figures, icons, transitions, sound on every beat, no burned-in captions | `docs/sample_motion_gfx_script.md` |
| `ai_image` | AI images with camera moves + cards, numbers, quotes, charts | `docs/sample_script.md` |

The same shot tags work for both, so one script can be rendered either way. The default comes from
`DEFAULT_RENDERING_METHOD` in `.env` (`motion`). A script without the line that only works with AI images
(`character:`, `[talk:]` / `[act:]`, `clip_from:`, `style: motion`) gets `ai_image` by itself.

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
rendering_method: motion                      (optional: motion (default) or ai_image, see the table above)
music: mystery, tense, epic                   (a mood folder of assets/library/music (calm, dark, emotional,
                                               epic, mystery, tech, tense, uplifting) or track names; full
                                               videos: one per chapter in this order, crossfaded)
sfx: auto                                     (optional: script / auto / rich / off; motion default auto)
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
| `captions:` | `presets/captions/` | `amber_word` (motion graphics: `none`) | |
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
| `amber_word` (default for `ai_image`) | short phrases, the spoken word turns amber |
| `big_word` | one heavy word at a time, popping in |
| `red_pop` | two tall words, the spoken one red |
| `soft_glow` | clean capitals with a soft glow |
| `karaoke_box` | a violet box jumps from word to word |
| `italic_punch` | slanted capitals, the spoken word yellow |
| `comic` | comic lettering, tilted |
| `serif` | small-caps serif |
| `pixel` | retro game lettering |
| `clean_lower` | friendly lowercase |
| `none` | nothing burned in (the .srt for YouTube is still made). Default for `rendering_method: motion`: its scenes already show the key words |
| `chip` | white pill at the top left, spoken word on a yellow marker (motion graphics; pick it in the Captions tab or write `captions: chip`) |

Every video gets `captions_final.srt` whatever the style (also `none`); it is in the upload pack for YouTube's
subtitles.

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
shot, at least 3 s apart. `sfx: rich` adds a light
sound on almost every picture change as well. With `rendering_method: motion` (default `auto` there) the
animations place the effects themselves: auto >= 2.2 s apart, rich >= 1.4 s, rotating through every file of a folder. `sfx: off` plays none. Sounds are `assets/library/sfx/<kind>/` (13 starter sounds
included; your own file in a folder replaces the starter one).

### Pictures (`rendering_method:`)

`rendering_method: ai_image` = AI images + graphics. `rendering_method: motion` (the default) = bright-pop
motion graphics: kinetic words, stick figures, numbers, charts, memos and transitions, a new picture every 1.2-3 s,
no AI images (docs/MOTION_GFX_PLAN.md). The same shot tags work; the narration words pick the figures' poses and props.
Not with `character:` or `clip_from:`. Video Studio: the "Pictures" menu on the new-video screen writes this line.

Formats (motion graphics only, docs/VARIETY_PLAN.md). Every video gets a whole show package: palettes, fonts, a
background treatment, which scene types it leans on, entrances, transitions (with a signature chapter
transition), sounds and music moods. `show: auto` (the default, no line needed) picks the format whose description fits the
title / tags / description best, plus a bonus for each variety goal the script meets in it, minus a penalty for each
use in the last 10 videos; it never takes the format of a video rendering at the same time, and a re-render keeps the
format it had. `show: <id>` pins one (the key is `show:` because `format:` already means landscape / vertical):
`pop_poster` (bright colours, stick figures), `tech_desk` (dark UI, app windows, phones, terminals, no people),
`data_lab` (navy + neon, charts, counters, dashboards, no people), `paper_notebook` (ruled paper, sticky notes,
checklists, hand-drawn wobble), `newsroom` (headline bars, lower thirds, ticker, anchor silhouette), `case_file` (noir
desk lamp, memos, evidence board), `arcade_retro` (pixel CRT, level cards, health bars), `blueprint` (blue grid,
line diagrams). `FORMATS_ALLOWED=tech_desk, data_lab` in .env limits auto to a channel's family of formats.
The Variety card on the Check page names the chosen format and why, and warns when the video is too similar to one
of the last 10 (similarity above 0.72).

Scene planner. The renderer picks a scene type per beat from ~37 (stick figure, kinetic words, number, chart, quote,
memo, map, timeline, meter, versus, pile, list, plus ranking, process, cause -> effect, pros/cons, checklist,
before/after, split screen, scale, funnel, venn, donut, icon grid, spec table, phone, browser window, chat, newspaper,
ticker, calendar, countdown, magnifier, reaction burst, globe, route map, and the format hosts dashboard / terminal /
sticky notes) by what each line does (statistic, comparison, list, process, cause, timeline...), with caps: no type
above 20 % of scenes, no type + layout above 6, words at most 15 %, never the same type twice in a row. Check shows
the result in the Variety card. `scene_order: ranking, donut, ...` (test reels only) forces types in turn.

Icons (motion graphics only). Each stick-figure scene shows one icon from the icon library
(assets/library/icons, docs/ASSET_PACKS_PLAN.md), chosen for the whole video at once: the script's topic words
make a pool of ~40-60 icons, every scene gets the best match for its own words, one icon is used once per video,
question/exclamation-style icons at most 3 times and one a minute, and a scene with no good match shows kinetic
words (there is no "?"/"!" fallback). Same script = same icons. After **Check**, the "Icons" card shows the pool, the
pick per scene and the repetition numbers; Pin / Ban write the lines below.

| Key | Meaning |
|---|---|
| `icons: fluent_flat` | icon family: `fluent_flat` (default), `fluent_color`, `noto` |
| `icon_reuse: 1` | how often one icon may appear in the video (1-5, default 1) |
| `icons_pin: low-battery, rocket` | icons to prefer (added to the pool, ranked higher); `set:name` for another set |
| `icons_ban: skull, pill` | icons never used in this video |
| `look: auto` | one look per video, rotating across videos (default): icon family, colour set, fonts. `classic` = the original look |
| `palette: pop` | colour set: `pop` (all 8 colours), `warm`, `cool`, `bold` |
| `fonts: poster` | font pairing: `poster` (Anton + Poppins), `condensed` (Barlow Condensed + Barlow), `comic` (Bangers + Poppins) |
| `icon_style: sticker` | `sticker` (white rounded badge, dark outline, shadow; default) or `plain` |

Scene types (motion graphics). Besides kinetic words, stick figures, numbers, charts, quotes, memos and title
cards, the narration's words start six more scene types: a **country** ("Singapore", "Chinese") = world map with the
country lit + its flag (each country once per video); a **year** ("twenty sixteen", 2021) = a timeline of the
video's years; a **percentage** ("twenty percent", "seven out of ten") or "battery" = a bar, battery or gauge;
**"X or Y" / "X versus Y" / "instead of"** = two icons face off; a **list** of 3-4 short items = a row of icons;
**"thousands of" / "thirteen pairs of"** = one icon raining into a pile. Each type waits 25 s before it shows again,
and every scene type has 3 layouts that take turns. Write the list or the comparison in one sentence to get them.

With `look: auto` each part not pinned is the one the last 5 finished videos used least (data/asset_history.json,
written after every final; icons used there rank a little lower too). A video already in that file keeps its look,
so re-rendering a script gives the same video.

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

| Tag | AI images (default) | Motion graphics (`rendering_method: motion`) |
|---|---|---|
| `[ai: a giant soap bubble floating above a skyline at dusk, cinematic]` | An AI image (FLUX.2, made on the Mac) with a slow camera move (8 different moves). No text, logos or real people's faces. | Animated scenes picked from the **narration words** (the prompt itself isn't drawn): stick figures with a pose and props (spy, chip, money, globe, heart, magnifier ...), kinetic words, memo/report with a stamp when the line cites a report. A new scene every 1.2-3 s. |
| `[stock: crowded city street at rush hour]` | The same, styled as a real-world documentary photo. Use it for everyday scenes. | Same as `[ai:]` |
| `[card: THE REAL QUESTION \| small line under it]` | Big text card | Title slam card, then kinetic words / figures for the rest of the line |
| `[number: 3.2 \| trillion dollars \| prefix=$ suffix=T]` | Animated count-up number (`$3.2T`, `45%` also work as the value) | Big count-up number with a label pill |
| `[quote: The exact quote. \| Who said it, where]` | Quote card. Only real, checked quotes. | Animated quote card |
| `[chart: bar \| Title \| 2022: 0.4, 2023: 1.2, 2024: 3.3]` | Animated bar chart (`line` for a line chart; add `\| unit=%` for a unit) | Animated bar chart |

In motion videos the words of each line decide the figure's pose and props, so write concrete words: "spy",
"chips", "China", "denied", "report", "money", "investigated". Lines that cite a report ("The New York Times
reported ...") become a memo with a REPORTED stamp; denials get a DENIED stamp. `character:` and `clip_from:`
can't be used with motion (Check error); `art_style:` is ignored.

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

### Pacing for motion videos

- Keep the usual shot tags every 1-3 sentences; the renderer cuts every shot into beats of 1.2-3 s on your
  commas and full stops, so commas matter: they are where the picture changes. Check doesn't warn about long
  shots in motion videos.
- Use a `[card:]` or `[number:]` for every big fact, `[quote:]` for real quotes; everything else can be `[ai:]`
  lines with clear, concrete narration.
- Draft = the real animation at 960x540 (about 2.5 minutes per minute of video on the Mac); final = 1080p at
  about the same speed. No AI images, so nothing gets slower when you change the script.

## 4. Example

- AI images: `docs/sample_script.md` (**Load sample** with Pictures = AI images).
- Motion graphics: `docs/sample_motion_gfx_script.md`, the Nvidia "honey trap" story (**Load sample** with
  Pictures = Motion graphics).

## 5. Motion style (`style: motion`)

`style: classic` (the default) is everything above: one picture per shot, captions at the bottom. **`style: motion`**
makes an animated explainer instead: flat scenes in one palette, elements that appear on the exact word they belong
to, a headline pill that fills in as it is spoken, camera-move transitions between scenes, and the presenter as a
small puppet inside the scene. The voice, music, sound effects, loudness, thumbnails and upload pack are the same.
It is opt-in per script; nothing changes for scripts without `style: motion`.

```
style: motion            (classic | motion)
palette: navy            (the colour set; one palette per channel keeps the look consistent)
character: sterling      (the presenter for [char:], [talk:] and [act:]; the normal 3D character pack is used)
```
Motion videos are landscape (16:9) for now; motion Shorts arrive later.

### Motion tags

| Tag | What it does |
|---|---|
| `[scene: name \| from: right]` | Starts a new scene. `from:` = how the camera arrives: `right` `left` `top` `bottom` (a push with a shadow band), `zoom <element>` (dive into an element of the previous scene, e.g. `zoom number`), `cut`. Without `from:`, the transitions vary by themselves. |
| `[head: TEXT]` | The headline pill at the top. It appears empty, then each word lights up when it is spoken (a word with digits like `$730` lights on the first spoken number word). One per scene. |
| `[+ kind: text \| place \| animation \| size]` | Adds an element **at the next spoken word**. Example: `[+ door: FUND \| 1 of 4 \| grow]`. |
| `[- kind]` or `[- kind: text]` | Removes that element at the next word (`[- char]` removes the presenter). |
| `[label: TEXT \| element]` | A white tag that points at an element: `[label: WORST DAY IN 19 MONTHS \| number]`. |
| `[char: pose \| place \| size]` | The presenter in the scene (`thinking`, `pointing`, `shrug`, ...). He stays in the next scenes until `[- char]`. He is lip-synced to the voice and blinks (the character pack's mouth and blink pictures, same timing as `[talk:]`); a second `[char: pose]` in a scene switches his pose on that word. |
| `[number: ...]` `[chart: ...]` `[quote: ...]` `[card: ...]` | The classic data tags, as elements inside the current scene. Add a place at the end: `[number: 5.5 \| label \| suffix=% \| right]`. |
| `[+ gen: a pair of white wired earphones \| right \| slide]` | A prop drawn by the AI image model in the flat style, cut out and cached for later videos (motion phase 5; until then a labelled placeholder). |
| `[talk: pose \| set]` | Sterling full screen, as its own scene, for punchy moments. |
| `[ai: ...]` `[stock: ...]` | A full-frame picture as its own scene (looks like classic; use sparingly). |
| `[sfx: ...]` `[pause: ...]` `## chapter` | As in classic scripts. |

**Places**: `left`, `center`, `right`, `top`, `bottom`, `top-left` ..., `2 of 4` (slots in a row, kept clear of
the presenter's side), `over <element>` (`over calendar`, `over door: fund`, `over char`), or `30%, 60%`.
**Animations**: `pop` (default), `grow` (up from the floor), `slide`, `fade`, `drop`, `draw`, `shake`, `none`.
**Sizes**: `tiny`, `small`, `medium`, `large`, `huge`. Elements are named by kind (`door`, `number`, `chart`),
by `kind: text` (`door: fund`), or by an id you give: `[+ door: FUND #fund | ...]`.

**The prop library** (45 props, all drawn in code in our palette, each with its own idle motion; list in
`motion/src/library/catalog.json`, preview in `output/motion_library.mp4`, made by `bin/python tools/motion_library_sheet.py`):
- **places**: `door`, `house`, `bank`, `factory`, `skyline`
- **tech**: `server`, `phone`, `laptop`, `chip`, `battery`, `gear`, `rocket`
- **ideas**: `lightbulb`, `magnifier`, `question`, `exclamation`, `bubble`, `target`, `cloud`
- **money**: `coin`, `coins`, `cash`, `piggy`, `wallet`, `creditcard`, `jar`, `briefcase`, `scale`
- **things**: `envelope`, `calendar`, `clock`, `hourglass`, `shield`, `lock`, `crown`, `trophy`, `globe`, `flag`, `megaphone`
- **signs**: `arrow`, `arrow_up`, `arrow_down`, `check`, `cross`, `warning`

Props take a colour: `[+ house | left | color=teal]` (accent, teal, sky, coral, good, bad, or a #hex). Any other kind is drawn as a
labelled placeholder.

**Generated props** `[+ gen: a pair of white wired earphones | right | slide]`: anything not in the library is drawn by
the local image model in the `flat_vector` art style (presets/art_styles/flat_vector.json) on a white background, cut
out with rembg, and kept in `assets/library/props/` (in git). It is made once, in the first final that needs it
(about 30 s), and reused by every later video and draft. Check shows how many are still to be made. Until then,
drafts and previews show a labelled placeholder. Describe one object, no text or logos: "a gold padlock", not
"the Apple logo".

**Set plates** (flat background scenes, also made once and kept in `assets/library/plates/`): a scene named one of
`city_night`, `city_day`, `ocean`, `stage`, `office`, `street`, `trading_floor`, `server_room`, `factory_floor`, `bank_hall`, `home`, `classroom`, `newsroom`, `space`, `desert`, `port`, `farm`
gets a plate behind it; any scene can have its own with `[scene: name | plate=a rainy harbour at dusk]`, and
`plate=no` turns it off. Other scene names use the plain code background.

**Data components** (in-scene, with a place at the end):
| Tag | Example |
|---|---|
| `[number: ...]` | `[number: 5.5 \| percent: the Nasdaq's fall \| suffix=% \| right]`, counts up |
| `[chart: bar or line \| title \| A: 1, B: 2 \| place]` | bars grow / the line draws; the title hides when the scene has a headline |
| `[pie: title \| A: 45, B: 35, C: 20 \| unit=%]` | slices sweep in, legend beside it |
| `[ranking: title \| A: 220, B: 200, C: 170 \| unit=B]` | sorted rows, rank badges, bars grow |
| `[compare: Revenue (2025): $13B \| Net loss (2025): $38.5B]` | two sides with VS; the bigger number gets the bigger circle |
| `[map: United States of America, Taiwan \| pin=37.77,-122.42 \| label=SAN FRANCISCO]` | countries fill in, a pin drops and pulses (Natural Earth, public domain) |
| `[quote: ...]` `[card: ...]` | as in classic scripts |

**Transitions**: `from: right / left / top / bottom` (push with a shadow band), `zoom <element>`, `iris`, `whip`, `fade`,
`cut`. Without `from:`, a chooser picks one from the new scene's first words, never the same twice in a row:
"inside / how does / why..." zooms through the previous scene's main element, "fell / crashed / then..." drops from
the top, "back in 2000 / years ago..." pushes from the left, and everything else is mostly a push from the right with
the occasional whip pan or iris.

**Palettes**: `palette: navy` (default) or `palette: light`, for the whole video; one scene can differ with
`[scene: name | palette=light]`.

### Layout notes (motion)
- `[act: ...]`, `[talk: ...]`, `[ai: ...]` work in motion scripts as full-frame scenes, with the same transitions.
- `n of m` slots share the free width (the presenter's side stays clear). Anything wider than its slot shrinks to fit.
  Small cards (`[card: TITLE | sub | 1 of 4 | small]`) become list tiles: one row, or a 2 x 2 grid for four.
- `[+ check | over x]` / `[+ cross | over x]` stamp ON the prop; other things placed `over x` sit above it.
- A label goes above its target; when something is already there it hangs below it. Labels never leave the frame.
- A prop without text can still carry an id: `[+ earphones #pods | center | drop | large]`.
- `x%, y%` = the centre of the thing, as a share of the frame (use it when slots don't fit).
- Number captions: write only the words under the number (`[number: 249 | AirPods Pro 3 | prefix=$ | 1 of 2]`).
- Library props added for this channel: `earphones` (white wired pair), `earbuds` (wireless case with two buds).

### Motion pacing rules (Check enforces them)
- Something new every ~3 s: an element, a label or a scene change (Check warns at 3.5 s).
- A new scene every 6-15 s.
- A headline in every scene.
- Vary the transitions (Check warns when three scenes in a row arrive the same way).

Check lists every scene (start, length, transition, headline, elements). **Show scene previews** draws one still
of each scene from estimated timings, in a few seconds, without making any AI image (pictures are placeholders).
Previews wait while a video is rendering.

### Full motion example (docs/sample_motion_script.md)
```
---
title: Four Doors Into Your Money (motion sample)
style: motion
palette: navy
character: sterling
music: misdirection
tags: ai bubble, stock market, motion sample
description: |
  A short sample of the motion style: scenes, elements that appear on their words, headlines and transitions.
  Facts from scripts/ai_bubble_sterling.md (Reuters / CNBC, Nov 2026).
---

## Four doors
[scene: doors]
[char: thinking | left | small]
[head: FOUR DOORS INTO YOUR MONEY]
There are four doors into your money.
[+ door: FUND | 1 of 4 | grow] Your fund.
[+ door: PENSION | 2 of 4 | grow] Your pension.
[+ door: JOB | 3 of 4 | grow] Your job.
[+ door: BILLS | 4 of 4 | grow] And your bills.

## The fall
[scene: chart | from: right]
[- char]
[head: THE NASDAQ FELL 5.5%]
[+ calendar: NOV 5 | left | drop] Last Thursday, one of them slammed shut.
[number: 5.5 | percent: the Nasdaq's fall in one day | suffix=% | right]
The Nasdaq fell five and a half percent
[label: IN ONE DAY | number] in a single day.
[+ exclamation | over calendar | pop] Its worst day in nineteen months.

## Who pays
[scene: spending | from: zoom number]
[head: $730 BILLION THIS YEAR]
[chart: bar | 2026 plans, $ billions (approx.) | Amazon: 220, Alphabet: 200, Microsoft: 170, Meta: 140 | left]
Amazon, Microsoft, Alphabet and Meta
[label: THE BIG FOUR | chart] are on track to spend about
[+ coins | right | grow] seven hundred and thirty billion dollars this year.
[label: ABOUT $2 BILLION A DAY | coins] That's roughly two billion dollars. Every single day.

## Next
[scene: next | from: top]
[char: shrug | left | small]
[head: WHICH DOOR IS NEXT?]
[+ door: FUND | 1 of 4 | grow | small] [+ door: PENSION | 2 of 4 | grow | small] So which door
[+ door: JOB | 3 of 4 | grow | small] [+ door: BILLS | 4 of 4 | grow | small] is next?
[+ question | over door: fund | pop] [+ question | over door: job | pop] Is it your fund, or your job?
[label: FOLLOW THE MONEY | door: bills] Let's follow the money.
```

