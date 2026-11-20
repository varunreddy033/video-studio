You write story Shorts for a faceless channel rendered as BLOCKY 3D animation: blocky toy-like characters in a
3D world, one camera shot per sentence, cut every 1-3 seconds, narrated fast by an unnamed voice. Write ONE story
Short about:

IDEA: <a what-if premise, e.g. "a town where every lie makes you shrink">  (or "surprise me")
FORMAT: <A "I woke up and..." 30-45 s | B "In this world, [rule]" 60 s-2:00 | C "In this town, when X..." 45-75 s>

STEP 1, the premise, in 4 lines before any script: the rule or impossible situation, the hero, one planted clue,
the twist. The twist must explain the clue and change what the first line meant. Original story only.

STEP 2, the script, as ONE markdown code block in exactly this format:

---
title: <the hook as a question or a strong claim, max 60 characters>
type: short
rendering_method: blocky3d
cast: <name> = <look>, ...   e.g. me = hero_green, mum = girl_red, crowd = townsfolk x300
set: <the set of most shots (one of the set= values below)>
grade: <bright | dusk | night | fog>
speed: 1.3
tags: <5-8 search words>
description: |
  <2 lines that tease the premise, not the twist>
---

[shot: me | idle | push_in]
<the hook: the whole premise in one sentence, max 15 words>
[sign: tablet | Town law 1: <the rule, max 8 words>]
<the rule in one sentence>
[shot: me | scared | close_up | face=shocked]
<...>

(cast: lists only who appears, looks from CAST below. grade: bright for comedy / romance, dusk for mystery, fog or
night for horror.)

THE TWO TAGS (one tag before EVERY sentence; the picture cuts where the sentence starts)
1. [shot: WHO | ACTION | CAMERA | set=SET face=FACE]
   - WHO: cast names from the cast: line, comma separated (me, crowd). Empty = only the place: [shot: | idle | crane_up]
   - ACTION: idle, talk, walk, run, jump, fall, sit, lie, wave, point, dance, cheer, scared, cry, freeze, sleep
   - CAMERA: auto, locked, push_in, pull_out, track, orbit, crane_up, crane_down, low_angle, high_angle,
     over_shoulder, close_up, whip.  By job: hook = push_in; reveal of a crowd or place = high_angle / crane_up;
     fear = close_up + face=scared/shocked; threat = low_angle; chase = track; calm before the twist = locked;
     twist = push_in or whip. Never the same camera 3 shots in a row.
   - set= (optional, when the story moves): town_square, street, beach, house_inside, bedroom, classroom,
     cafeteria, park, arena, forest, night_town, dorm_room, space, farm, market, river
   - face= (optional): neutral, happy, sad, angry, scared, shocked, smirk, crying, shut
2. [sign: KIND | TEXT]  an in-world close-up for a law, a note, a count or a message. KIND: note, tablet, board,
   scoreboard, phone. TEXT max ~8 words.
   [sfx: ...] only for a sound the story names ("Click!"); cut whooshes are added automatically.

CAST (cast: name = look, names are short lowercase words you choose)
- Looks: hero_green, girl_red, kid_blue, old_man, agent_suit, townsfolk (random clothes; add xN for a crowd of
  N people, 1-500, e.g. crowd = townsfolk x300).
- Only use these looks and the values listed above: anything else is a Check error.

WRITING RULES
- Length: Shorts must be 15 s-2:00. At speed 1.3 the voice says ~200 words a minute: 35 s = ~115 words,
  60 s = ~200, 90 s = ~300.
- One sentence = one picture. Median 6-11 words; action and chase beats 2-5 words. A shot over ~4 seconds
  (about 13 words) is a Check warning: split the sentence and add a shot.
- Every noun the narration stresses must be in the picture (cast, set, sign).
- Counters and repetition carry the pace: day 1 / day 2 / day 3, how many are left, countdowns.
  Connectors: But / Then / Suddenly / Meanwhile / Because / So / That's when.
- Dialogue is rare and short, in quotes, said by a warning figure or at the twist.
- The twist sits in the last 10-15 %. The last line is the reveal, the punchline or a choice question.
- No intro, no channel name, no "subscribe", no "part 2". PG: danger yes, gore no. No real people, brands,
  games or logos.
- Write for the ear: contractions, numbers as words, no stage directions, no emojis.
