# Variety plan: every video its own identity, no scene type repeated to death

Status: PLAN (2026-11-11). Applies to rendering_method: motion (pipeline/motion_gfx).

## 1. What we measured (Windows vs MacBook final, job 20261111-125755-a5e140, 194 scenes)
| | Count | Share |
|---|---|---|
| figure (stick figure + icon + headline) | 85 | 44% |
| kinetic (words on a colour) | 75 | 39% |
| everything else (meter 8, number 8, title 6, memo 4, timeline 3, chart 3, quote 1, icon_list 1) | 34 | 17% |
| transitions: cut 94, push 89, whip 6, zoom 5 | | 94% cut/push |
Causes:
- `templates.pick()` alternates figure <-> kinetic for every beat after a shot's first one. The 6 richer templates only
  appear when exact trigger words occur ("versus", a year, a country...), with a 25 s cooldown.
- Each template has only 3 layouts; transitions are effectively two.
- Across videos only the "skin" changes (icon family 3 options, palette set 4, fonts 3, icon style 2). Scene types,
  rhythm, animations, transitions, figures, chapter cards are identical, so every video feels like the same show.
- Concurrency bug: data/asset_history.json is written when a FINAL finishes, so videos rendered at the same time
  can't see each other and can pick the same look.

## 2. Goal
1. **Inside a video**: no scene type is more than ~20% of scenes; any one scene type + layout appears at most 5-6
   times; at least 15 different scene types in a 10-minute video; no type twice in a row; no A-B-A-B patterns.
2. **Between videos**: each video gets its own **format** (a whole show package, not just colours), so two videos
   rendered side by side look like different shows, even on similar topics.

## 3. Formats: a show package per video
A format bundles everything below. 8 to start, each built and previewed:
| Format | World | Host device | Scene mix leans on | Motion + transitions |
|---|---|---|---|---|
| **Pop Poster** (today's look, refined) | bright solid colours, thick outlines | stick figures | figures, big numbers, versus | snappy pops, push + whip |
| **Tech Desk** | dark UI, glass panels, grid | cursor + app windows (no people) | browser/app windows, phone screens, notifications, spec tables, benchmarks | smooth slides, zoom into a window, glitch cut |
| **Newsroom** | white/red, headline bars, ticker | anchor desk silhouettes | headlines, tickers, lower thirds, quotes, maps | hard cuts, slide-in bars, flash wipe |
| **Data Lab** | deep navy, neon accents | none (data is the hero) | charts, counters, rankings, donut/pie, icon grids ("1 in 10") | draw-on lines, count-ups, zoom-through numbers |
| **Paper Notebook** | paper texture, doodles, tape | hand-drawn figures | sketch drawings that draw on, sticky notes, arrows, checklists | ink wipe, page flip, scribble reveals |
| **Case File** | dark noir, desk lamp, folders | silhouettes | memos, stamps, evidence boards with string, redactions, polaroids | slow push, flashlight reveal, stamp cuts |
| **Arcade Retro** | pixel/CRT, scanlines | pixel sprites | level/score cards, health bars (meters), versus screens, leaderboards | pixel wipe, screen shake, 8-bit stingers |
| **Blueprint** | blue grid, white line art | line figures | diagrams, exploded parts, process steps, cause-effect chains | line draw-on, grid zoom, measure-line reveals |
Each format defines: background treatment + texture, palette family, font pairing(s), icon family + treatment,
host device, scene-type weights, its own layouts for shared scene types, entrance-animation pool, easing set,
transition set (incl. a signature chapter transition), chapter card + intro/outro style, caption-free headline style,
SFX mapping (which sound kinds it prefers), music moods.
Within a format, seeded choices (palette, fonts, icon family, layout starts) keep every video unique.

Choice: `format: auto` (default) picks the format that fits the topic (embedding match of the script against each
format's description) AND was used least in the last 10 videos. Pin with `format: newsroom`. Channel tip: a channel
can restrict auto to 2-3 formats (`FORMATS_ALLOWED=` in .env) to keep a recognisable family look.

## 4. Scene library: from 9 types to ~30, each with 4-6 layouts
Existing: kinetic, figure, number, title, quote, chart, memo, icon_list, versus, pile, timeline, meter, map_flag.
New: ranking/leaderboard, step-by-step process, cause -> effect chain, pros/cons, checklist, before/after slider,
split screen, scale/balance (weighing two things), funnel, venn, donut/pie, icon grid ("1 in 10"), table/spec sheet,
phone screen + notification, browser/app window, chat bubbles (generic, no real people), newspaper headline,
stock ticker card, calendar, countdown/clock, magnifier zoom on a detail, emoji reaction burst, globe spin, route map.
Every scene type gets 4-6 layouts and an entrance-animation pool (pop, slide, draw-on, mask reveal, flip,
typewriter), chosen per scene from the format's motion language.

## 5. Scene planner (replaces the figure/kinetic alternation)
1. **Classify each beat's role** (deterministic: rules + the MiniLM embeddings we already have): statistic, comparison,
   list, process, cause-effect, timeline, quote, definition, story/example, question, warning, conclusion, transition line.
2. **Candidates**: each role maps to several scene types (comparison -> versus, split screen, scale, pros/cons, table...).
3. **Budget**: pick the best candidate that respects the caps: per type <= 20% of scenes, per type+layout <= 6 uses,
   never the same type twice in a row, no A-B-A-B, kinetic words <= 15% and only for punch lines.
4. **Rhythm**: vary beat length on purpose: a "burst" of quick 0.8-1.2 s scenes on hooks and reveals, a held
   "breather" scene (4-6 s, slow drift) about every 45 s, and each chapter shifting the dominant scene mix.
5. **Transitions**: 8-10 types per format, chosen by story relation (same point -> cut, next point -> push/slide,
   new chapter -> the format's signature transition, reveal -> zoom-through); no type above 35%.
6. Same script + same format = same video (seeded).

## 6. Across videos and concurrency
- **Reserve at job start**: when a render starts, write its format + look into data/asset_history.json with
  status "rendering"; recent() includes rendering jobs, so videos started at the same time always differ.
  Clear stale reservations after 24 h.
- **Similarity check**: compare a new video with the last 10 (format, palette, fonts, icon family, scene-type mix,
  transition mix) and warn on the Check page if it is too close to any of them, naming the closest one.

## 7. Reports (Check page + job page)
Scene-type distribution (bar), the most-used type + layout and its count, transition mix, number of different
scene types, longest stretch without a data scene, similarity score vs recent videos, the chosen format and why.

## 8. Build order
1. Concurrency fix (reserve at start) + variety report on the Check/job page (measure before changing).
2. Scene planner with roles, candidates, budget caps, rhythm, transition chooser (with today's templates).
3. 4-6 layouts + entrance pools for every existing scene type.
4. The new scene types (section 4).
5. Formats: build Pop Poster (refined) + 3 new (Tech Desk, Data Lab, Paper Notebook), then a 20-second preview
   reel of each on the same test script: STOP for Varun's approval of the formats.
6. The remaining 4 formats (Newsroom, Case File, Arcade Retro, Blueprint) + preview reel: STOP for approval.
7. Format auto-choice (topic fit + freshness), FORMATS_ALLOWED, similarity check.
8. Test: re-render the Windows vs MacBook script (acceptance below) and render it together with the EarPods
   script at the same time.

## 9. Acceptance
- Windows vs MacBook re-render: no scene type > 20%, no type + layout > 6 uses, >= 15 different scene types,
  >= 6 transition types, kinetic <= 15%.
- EarPods + Windows rendered at the same time: different formats, similarity below the warning threshold, and a
  side-by-side contact sheet (1 frame every 10 s) that a viewer would call two different shows.
