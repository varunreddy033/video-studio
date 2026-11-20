# Storyboard themes + storyboard editor (roadmap F11, built 2026-11-17, branch raju/storyboard-editor)

No roadmap item covered this, so it is a new one: **F11** (F9 = HTML animation, F10 = motion graphics + sound).
Motion graphics only (`rendering_method: motion`); themes also set the art style / captions of AI-image videos.

## 1. What was already there (audit) and what is reused
| Need | Already in the code | Reused as |
|---|---|---|
| Storyboard | `motion_gfx/render.py` step 2: voice -> beats (`beats.py`) -> one scene per beat, planned by `picker.plan_video` + `planner.py`; `motion/beats.json` | the storyboard IS this list; `storyboard/scenes.json` adds ids + state |
| Scenes as HTML | `compose.scene_file`: one `<template>` per scene, every element with a stable id `sNNN-<name>`, GSAP timeline registered in `window.__timelines` | shown as they are in the editor; never flattened |
| Themes | 9 hard-coded "formats" (`formats.py`, header `show:`) + header keys typography / palette / fonts / camera / transitions / captions / art_style | a theme = a JSON bundle of those keys (+ an optional scene design of its own) |
| Presets | `presets/<kind>/<id>.json`, `presets.py` schema check, `job.json` | new kind `storyboard_themes` |
| Re-render part of a video | the critique's `hyperframes render --start/--end` + frame-exact `critic.splice` | changed scenes only are re-rendered |
| Scene editor, regeneration, versions | nothing (only Pin/Ban of icons on the Check page) | new |

## 2. Themes (`presets/storyboard_themes/<id>.json`, header `theme: <id>`, module `pipeline/themes.py`)
- `settings`: default header values per rendering method (`all` / `motion` / `ai_image`): show, typography, palette,
  fonts, icon_style, camera, transitions, captions, art_style, music, sfx. A line the script has itself wins.
  The stages keep reading the same header keys, so no stage has theme logic.
- `scene_style` (optional): a scene design of its own = a base format + own palettes (colours), fonts, card / line
  colours, line weight, shadow, backdrop, scene-type weights and bans (composition), entrances, cameras,
  transitions, chapter kicker, music moods. Registered as the format `theme_<id>`; never picked by `show: auto`.
- `supports`: rendering methods + video formats (Check warns outside them). `version` + a content hash go to job.json.
- 9 files: auto (= before themes, the default), documentary_cinematic, minimalist_editorial, modern_motion_graphics,
  illustrated_explainer, newspaper_editorial, dark_atmospheric, clean_corporate, scientific_visualization.
  A new theme = a new file; `bin/python tools/check_presets.py` checks it.
- UI: Look & sound -> **Theme** tab (new-video screen and a video's Script editor), and a Theme menu on the
  Storyboard page. `GET /api/themes`. job.json: `storyboard_theme` (the whole file, `config_version`, `applied`).

## 3. Storyboard data (`output/jobs/<id>/storyboard/`, module `pipeline/motion_gfx/storyboard.py`)
- `scenes.json`: a row per scene (scene id, number, line, start, length, type, layout, frame, pictures, current
  version, waiting version, edited / stale flags). Written by every build.
- `plan.json`: the plan (types, layouts, pictures) + the history snapshot it was made with. Reused while the scene
  lines and the look stay the same, so untouched scenes are identical in every later build.
- `state.json`: per scene: `current` version, `pending` version, `versions` list, `edits` per version.
- `versions/<scene id>/vN.json + .html`: a pinned version (built parts, palette, type, layout, pictures inline).
  v0 = the generated original, stored the first time a scene is regenerated. Pictures are inline, so no orphans.
- Scene id = hash of the scene's spoken words (+ counter): it follows the scene when the script changes around it.
- Element id = the element's own id without the scene prefix + child indexes (`kin`, `p0/2`).
- An edit = `{mode, x, y, base, zoom, fs, color, font, align, z, hidden, text}`; x / y / fs are fractions of the frame.
  Applied as a CSS block (+ 1 line of JS per text change) appended to the scene, between `/*sb-edits*/` markers:
  the generated HTML, ids, HyperFrames attributes and GSAP timeline are not touched (moves use margins / relative
  offsets and `zoom`, because GSAP owns `transform`).
- An edit belongs to the layout it was made on (type : layout : frame). On another layout it is kept, reported as
  stale (page + render.log) and NOT applied: nothing is overwritten silently.
- job.json: `storyboard` = scenes, modified scenes with versions and edited element ids.

## 4. Pipeline
- `render(..., mode="storyboard")` = voice + scenes only (jobs queue, `POST /api/jobs/<id>/storyboard`).
- Every build (storyboard, draft, final): per scene `Board.resolve` = the user's version (else generated) + edits.
- Regeneration (`POST .../scene/<sid>/regenerate`, a few seconds): the planner runs again with that scene's current
  type excluded (or a chosen type), or the same type gets its next layout, or only the picture changes (the words
  typed are an icon search). Only that scene is built; it waits as a pending version until Accept / Reject.
  Same layout = the manual edits carry over.
- Draft / final: when the last picture of that mode came from the same root page, only changed scenes are rendered
  and spliced in (`render._reuse_render`); nothing changed = the picture is reused. Any doubt = full render.

## 5. UI (`ui/storyboard.js`, opened with the Storyboard button on a motion video's page)
- Speed (2026-11-17, raju/studio-ui-redesign): the grid used to show every scene as a live 1080p page; one scene
  painted for ~0.55 s (SVG paper filter, big shadows), so 30 cards froze the page for ~20 s. Now each card is a
  poster: `storyboard/posters/<sid>-<hash>.jpg`, a screenshot of the scene's frame page at its still moment, made with
  the thumbnails' headless Chromium (`pipeline/thumbs/shoot.mjs`, one browser per batch, ~1.7 s for 31 scenes) and
  keyed by a hash of that page, so only changed scenes are shot again. `POST .../storyboard/posters` makes the
  missing ones, `GET .../storyboard/poster/<name>`. At most ONE live scene plays: the card under the mouse (hover
  preview) or the editor canvas. Dragging restyles once per screen frame. Opening and scrolling the grid now block
  the main thread for at most ~9 ms.
- Reel: the whole video as a strip above the grid and the editor, each scene as wide as it is long.
- Per-scene options (Scene and Cut + camera tabs in the editor): layout (arrangement + frame), colours (palette),
  text entrance, transition into the scene, camera move, scene entrance, whoosh on the cut, sound effects in the
  scene. Stored in `state.json` scenes[sid]["opts"] (`storyboard.save_opts`, validated against the known names),
  applied by every build in `render.py` right after the planner, so the cut also sets the previous scene's exit and
  overlap. `PUT .../storyboard/scene/<sid>/options` saves them and rebuilds the scenes at once (~1.5 s, voice and
  plan cached; untouched scenes stay identical). `storyboard/options.json` (written by every build) lists the
  choices and what each layout number of every type looks like. A regenerated version keeps its own layout,
  colours and text entrance (those controls are locked until version 0 is restored); transition, camera, entrance
  and sounds apply to every version.
- Grid: every scene as its poster, number, type, time, line, flags.
- Editor: scene list | canvas (click to select, drag to move, round handle to resize, arrow keys, Esc = group,
  double-click = inside, Delete = hide, undo / redo) + time scrubber and Play | properties (text, size, font size,
  font, colour, align, layer, hide, reset element, background, reset scene), Regenerate, Versions.
- Saves by itself (PUT `.../scene/<sid>`); survives refresh, reopening, other scenes' regeneration and re-renders.

## 6. Limits (2026-11-17)
- Motion graphics only. AI-image videos get the theme (art style, captions, camera) but no scene editor.
- No language model in the pipeline (decided earlier): "instructions" for a regeneration are a scene type, a layout
  step and words for the icon search, not free prose.
- Text edits work on single text elements; text that an animation types letter by letter (type / scramble) is
  overwritten by that animation while it runs.
- Parts of an SVG drawing are selected as the whole drawing. Rotated groups resize from an approximate corner.
