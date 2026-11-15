# Designed thumbnails (replaces "a frame of the video + text")

Status: BUILT on branch `varun/thumbnail-generator` (2026-11-15), PR open for review. `bin/python tools/check_thumbs.py`
prints `thumbs: clean` (5 scripts, 15 options, ~0.2 s per option, byte-identical rebuilds).

## Problem
Motion videos and Shorts get thumbnails that are frames pulled out of the finished video (render.py `thumbnails()`,
thumbnails.py `make_short()`): whatever scene happens to be on screen, a random icon, half a word, with the
headline stuck on top. They don't look designed and don't make anyone click.

Target quality: `output/thumbnails/2026-11-13-nvidia-ceo-staff-vs-board-cover.jpg` (made by hand in Claude chat:
one huge number, 2-4 big words, a small red tag on top, one clear stick-figure scene that tells the story, a stamp,
the video's own icon style, dark background with one strong accent colour). The generator must make that kind of
picture automatically, for any script.

## What to build
1. **A designed thumbnail is drawn, not grabbed.** New module `pipeline/thumbs/` (design.py, layouts.py,
   render.py): it builds one HTML page per option from a small "brief" and screenshots it with the headless
   Chromium we already have (puppeteer-core, installed with hyperframes; no new dependency, no network). Fonts from
   assets/fonts, icons from the icon library (same licence allow-list, never brand logos, never real faces), stick
   figures and props from motion_gfx/figures.py (static pose).
2. **The brief (auto from the script, every part can be overridden in the header):**
   | Part | Auto source | Header key |
   |---|---|---|
   | headline (2-4 words, the big text) | `thumbnail:` | `thumbnail:` (exists) |
   | hero number | the most striking `[number:]` tag (or the first number in the first 30 s of narration) | `thumbnail_number: 88%` |
   | tag (small pill on top, 3-5 words) | first `[card:]` title, else a short form of the title | `thumbnail_tag: NVIDIA'S CEO JUST QUIT` |
   | stamp (optional, 1-3 words, red, rotated) | none | `thumbnail_stamp: HE'S GONE` |
   | hero icons (1-2) | the video's own icon plan: best icon matches for headline + title words | `thumbnail_icons: package, door` |
   | figure pose + prop | from the headline's mood (question = thinking, shock word = shocked, "vs" = pointing) | `thumbnail_pose: walking` |
   | look | the video's own look/format from history (palette, fonts, icon family) so cover and video match | - |
3. **Layouts (each in 16:9 1280x720 AND 9:16 1080x1920):**
   - `big_number`: huge number + headline + a small figure scene (the Nvidia cover).
   - `face_off`: two big icon stickers split by a slanted "VS" bar (titles with vs/versus/or).
   - `hero_icon`: one giant icon sticker, stick figure reacting next to it, headline on the other side.
   - `stamp`: headline + scene + stamp across it (works when there is no number).
   A full video gets **3 options with 3 different layouts** (for YouTube's Test & compare), a Short gets
   **1 cover + 2 alternates**. Order: the layout that fits the brief best first. Same script = same thumbnails
   (seeded). `thumbnail_layout: big_number` pins the first one.
4. **Rules every option must pass (checked in code, not by eye):**
   - Big text at most 4 words (tag and stamp are separate); headline cap height >= 18 px when the image is scaled to
     320x180 (16:9) or 180x320 (9:16), i.e. readable on a phone.
   - Text contrast ratio >= 4.5 against what is behind it (outline/shadow counts).
   - Safe areas. 16:9: nothing important in the bottom-right 22% x 18% (the duration badge). 9:16: headline, number
     and stamp inside the centre 1080x1080 square (y 420-1500), because Shorts covers get cropped to square / 4:5
     in feeds and on the channel page.
   - Nothing overflows or overlaps the headline (measure DOM boxes in the page before the screenshot).
   - JPG, quality 90, under 2 MB.
   - If an option fails, try the next layout; if everything fails, fall back to today's frame thumbnail and log why.
5. **Fast, and before the render.** Thumbnails no longer need the finished video, so:
   - After **Check**, a "Thumbnails" card shows the 3 (or 1+2) options in about 5 s, with the brief (headline,
     number, tag, stamp, icons, layout) as small editable fields that write the header keys above and re-check.
   - A video's page gets **Remake thumbnails** (no re-render).
   - The final render still writes thumb_1..3.jpg in the job folder exactly as today (upload pack unchanged).
6. **Scope.** motion (default) full videos and Shorts. `rendering_method: ai_image` keeps its current thumbnails
   (2 AI images + a frame); `thumbnail_mode: frames` brings the old frame thumbnails back for any video.
7. **Docs:** SCRIPT_FORMAT.md (new header keys + one example), VIDEO_TYPES.md (Shorts cover rules), this file's
   status line.

## Test (all on the branch, before the PR)
1. `tools/check_thumbs.py` (new): builds the thumbnails for these scripts and runs every rule above, then writes one
   contact sheet `output/thumb_tests/contact_sheet.jpg`:
   scripts/2026-11-13-nvidia-ceo-staff-vs-board-short.md (Short, big_number),
   scripts/2026-11-13-microsoft-outage-short.md (Short, no stamp),
   scripts/2026-11-14-tesla-cybercab-for-sale.md (full, 3 layouts),
   scripts/2026-11-11-windows-vs-macbook.md (full, face_off must appear),
   docs/sample_motion_gfx_script.md.
   It must print `thumbs: clean` and the time per option (target < 3 s each on the M5).
2. Same script twice = byte-identical JPGs.
3. The CONTRIBUTING.md tests: `bin/python tools/check_presets.py` = clean, a draft of
   docs/sample_motion_gfx_script.md and of docs/sample_script.md still render, one Short final renders with the new
   cover in its job folder.
4. `bash tools/check_secrets.sh` = clean before every commit.
