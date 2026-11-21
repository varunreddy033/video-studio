# Video Studio UI redesign

Status: PLAN (2026-11-20, Varun). Branch: `varun/ui-redesign`. Target look: `docs/ui_redesign/ui_mockup.png`
(open `ui_mockup.html` in a browser for exact colours, sizes and spacing). Files: `ui/studio.css`, `ui/index.html`,
`ui/login.html`, `ui/storyboard.js` (keep every feature working; this is a design and layout change).

## Why
The current look (graphite + amber "edit bay", Jost + Barlow Condensed) reads as a cheap copy of a real product,
the job page buries the outputs under cards nobody reads, and everyday buttons compete with rarely used ones.

## 1. Look
- **Theme: lavender.** Light mode is the default: background `#f6f4ff`, panels white, lines `#e6e1fb`, ink `#1d1634`,
  muted `#6e678a`, accent `#7c5cff` (primary buttons: gradient `#7c5cff -> #9b7bff`, white text), soft accent
  `#ede8ff` with text `#5b3fe0`. Status colours: ok `#14915a`, info `#3b5bdb`, warn `#a15c00`, bad `#d03050`, each with a
  soft tint. Dark mode keeps the same tokens on `#120f1d` / panels `#1b1629` / accent `#a78bfa`. Every colour stays a
  CSS variable (as studio.css already does); no raw colours in index.html or storyboard.js.
- **Font: Plus Jakarta Sans** (SIL OFL) for everything: 800 for page titles, 700 for card titles, 600 for buttons,
  400/500 for text. Bundle the variable TTF in `ui/fonts/` with its OFL licence file (no Google Fonts link at runtime).
  Remove Jost and Barlow Condensed from the UI. Keep a monospace stack only for the script editor and logs.
- **Shapes:** radius 16 px on cards, 12 px on buttons and inputs, soft lavender shadow (see the mockup), 40 px button
  height (32 px small). Remove the "ambient" glow background and the tally-light dot.
- Every button has a clear hierarchy: one primary (filled lavender gradient) per area, secondary (white, lavender
  border), soft (lavender tint), and quiet text links. No orange anywhere.

## 2. Layout
- **Top bar** (64 px, sticky, translucent white): hamburger on the left, logo mark + "Video Studio", then on the
  right **"+ Short" (soft) and "+ Full video" (primary) side by side**. Nothing else in the top bar: the health
  chips (Images, Encoder, Voice, Music/SFX) and "Signed in as / Account / Log out" move into the menu.
- **Menu (the old sidebar), collapsible with the hamburger.** Open by default on wide screens (290 px, pushes the
  page), closed by default under 1100 px (slides over the page with a dim backdrop; Esc or a click outside closes it).
  The open/closed choice is remembered per browser (localStorage, wrapped in try/catch). A tree of sections, each one
  expandable, remembered too:
  1. **Recent videos** (open by default): the job list with a status dot (green final, lavender rendering with %,
     amber draft, red failed), title on one line with ellipsis, a second line with status and length or "Short".
     The current job is highlighted. The existing Select / bulk tools live in a small "Manage" link here.
  2. **Create**: Full video, Short from scratch, Short from a video I already made, Load a sample.
  3. **Studio**: the health info as quiet rows (Images, Voice, Encoder, Library counts), Theme (light / dark /
     system).
  4. **Account**: signed-in user, Account settings, People who can log in (admin), Log out.
- **Main column** max width 1180 px, 28/36 px padding, generous spacing between cards.

## 3. Job page, in this order
1. Title (one line, 26 px, 800), status pill, date, length and size; on the right: Storyboard and the render
   button(s).
2. The three steps (Script checked / Draft (optional) / Final + thumbnails) as a slim row.
3. While rendering: the progress card (stages as pills, a progress bar, time running, the last log lines in a
   collapsible "Show log").
4. **The video** (Draft / Final tabs when both exist), with Download video (primary) and Upload pack (.zip) under it,
   and the facts (length, size, made in) on the right.
5. **Right under the video, side by side:** **Thumbnails** (3 options or the Short cover + alternates, each with
   Download; Remake button) and **For YouTube Studio** split into Title / Description / Tags / Chapters fields, each
   with its own Copy, plus Copy all. Stack them on narrow screens.
6. Collapsed by default, one line each with a summary:
   - **Script** (word count, saved / unsaved). Opens the editor, Check & save, and the Look / Icons / Thumbnails
     cards. It opens automatically when the check has errors.
   - **Render details**: Smoothness check, Variety, time per stage, music used.
   - **Notes**: all warnings (see section 4), with the count in the summary.
   - **Render log** (only for failed jobs, open by default then).
- A failed job shows the error banner at the top in plain words, with "Try again" next to it.

## 4. Warnings
- Warnings never block anything (errors still do).
- **Once Make final (or Draft first) has been pressed for a job, its warnings are hidden**: no warning banners on the
  job page or under the video; they go into the collapsed **Notes** section ("3 warnings, hidden"). On the new-video
  screen, before the first render, warnings show as one collapsed line under the check result ("4 warnings, show"),
  not as a list that pushes the buttons down. Errors keep showing in full.

## 5. Other clean-ups (do them)
- New-video and Short screens: the same card style, the script editor with a light lavender focus ring, the sample
  and picture-style pickers as clean segmented controls, the two render buttons side by side at the bottom right.
- Toasts: bottom-centre pill, lavender, auto-hide.
- Empty states (no jobs yet, no thumbnails yet) with one helpful line and the right button.
- Login page in the same look.
- Storyboard (`storyboard.js`) uses the same tokens, font and buttons.
- Keyboard: Esc closes the menu, `/` focuses the job search in the menu (add a small search box above Recent
  videos).
- Accessibility: every icon-only button has an aria-label, focus rings are visible, text contrast at least 4.5:1 in
  both themes.

## Test (before the PR)
- Screenshots of the job page (finished video, rendering video, failed video), the new-video screen, a Short, the
  menu open and closed, light and dark, at 1440 px and 390 px wide. Compare with `ui_mockup.png`.
- Every existing action still works: new video, sample, check, draft, final, re-make, storyboard, remake thumbnails,
  copy buttons, downloads, upload pack, select/delete jobs, account, password change, log out.
- `bin/python tools/check_presets.py` clean, a draft of each sample script renders, `tools/check_secrets.sh` clean.
