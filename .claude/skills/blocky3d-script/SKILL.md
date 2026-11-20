---
name: blocky3d-script
description: Write a blocky 3D story Short script (rendering_method: blocky3d) for Video Studio - "I woke up and...", "In this world, [rule]..." or "In this town, when it rains..." what-if stories with a twist, as script.md with [shot:] / [sign:] tags that pass Check. Use when asked for a blocky3d / blocky 3D / game-style / what-if story script, a story Short like the reference reels, or "write the next blocky video".
---

# Write a blocky 3D story Short

The output is one `scripts/<YYYY-MM-DD>-<slug>.md` that passes Check with 0 errors and 0 warnings, written in the
style of `references/style_guide.md` (read it first, every time). The picture vocabulary is code-owned:
`pipeline/blocky3d/script.py` (ACTIONS, CAMERAS, FACES, SETS, GRADES, SIGNS) and `presets/blocky_cast/`. Read both
before writing tags; never invent a value.

## 1. Pick the format and length (ask only if the person gave no hint)

| Format | Use for | Length | Words at speed 1.3 |
|---|---|---|---|
| A "I woke up and..." | comedy / romance what-if, first person | 30-45 s | 100-150 |
| B "In this world, [rule]" | game, survival, fantasy, named cast | 60 s - 2:00 | 200-380 |
| C "In this town, when X..." | rule horror-lite, newcomer breaks the rule | 45-75 s | 150-250 |

Shorts must be 15 s - 2:00 (Check errors outside that; the real voice length is re-checked at render).

## 2. Premise (before any sentence)

Write down in 4 lines: the rule / impossible situation, the hero, the planted clue, the twist. Check it:
- Original: not the plot, names or twist of a reference reel. Same *shape*, new idea.
- The twist explains the clue and changes what the first line meant. Test: would a viewer rewatch to spot the clue?
- PG, no real people, brands, games or logos (never "Roblox"), no invented facts presented as real.

## 3. Beat sheet

List the beats of the chosen format (style_guide.md "Three formats") with a word budget each. The hook is beat 1 and
<= 15 words. The twist sits in the last 10-15 %. The last line is the reveal, the punchline or a choice question.

## 4. Write narration + shots together

- One sentence (or one short clause) per tag. Each sentence must be filmable with the cast, a set and an action.
- `[shot: who | action | camera | set=... face=...]`: who = cast names; pick the action that shows the verb
  (run, fall, point, freeze, dance...); camera by job: hook = push_in; reveal of a crowd or place = high_angle /
  crane_up; fear = close_up + face=scared/shocked; threat or monster = low_angle; chase = track; calm before the
  twist = locked; twist reveal = push_in or whip.
- `[sign: kind | text]` for the rule, a note, a scoreboard count, a phone message. Max ~8 words of text.
- Vary cameras (never the same camera 3 shots in a row) and change the set when the story moves.
- `[sfx: ...]` only for a sound the story names (*Click!*); the renderer adds cut whooshes itself.

## 5. Header

```
---
title: <the hook as a question or a strong claim, <= 60 chars>
type: short
rendering_method: blocky3d
cast: <name> = <presets/blocky_cast id>, ..., crowd = townsfolk x<N>     (only who appears)
set: <the set of most shots>
grade: bright | dusk | night | fog          (comedy/romance bright, mystery dusk, horror fog or night)
speed: 1.3
tags: <5-8 search words>
description: |
  <2 lines that tease the premise, not the twist>
---
```

## 6. Check, fix, repeat

Save the file, then run (repo root):

```
bin/python -c "from pipeline import script_parser as P; import json,sys; r=P.parse(open(sys.argv[1]).read()); print(json.dumps({'ok': r['ok'], 'errors': r['errors'], 'warnings': r['warnings'], 'est_seconds': r['stats']['est_seconds']}, indent=1))" scripts/<file>.md
```

Fix every error and warning (a shot over ~4 s = split the sentence and add a shot). Then read it aloud once in your
head at a fast pace and cut any sentence that only explains.

## 7. Hand over

Give the person the file path, the format, the estimated length, the twist in one line, and the cast/sets used. Don't
render; renders are started from Video Studio.

## Checklist

- [ ] Hook <= 15 words, states the rule / situation, first sentence of the file.
- [ ] Median sentence <= 11 words; chase/action beats 2-6 words.
- [ ] Every sentence has its own [shot:] or [sign:]; every noun the narration stresses is in the picture.
- [ ] A counter or repetition drives the middle (days, people left, countdown).
- [ ] One clue planted before the last third; the twist pays it off.
- [ ] No CTA, no intro, no real names/brands/games; PG.
- [ ] Check: ok, 0 errors, 0 warnings; length inside the format's range.
