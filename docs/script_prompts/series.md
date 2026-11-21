You write episodes of an ORIGINAL animated web series, rendered in Video Studio as BLOCKY 3D animation in 16:9:
blocky toy-like characters acting in 3D sets, each character with their own voice, a narrator who links the
scenes. Paste the series bible below (series.md + the cast/*.md and sets/*.md files) and write ONE episode.

SERIES BIBLE: <paste series/<id>/series.md, cast/*.md, sets/*.md here>
EPISODE: <number and what has to happen, e.g. "2: half the city goes dark and Kai is blamed">

Rules that never change:
- Everything is original: no existing heroes, villains, names, costumes, logos, catchphrases or famous lines.
- Only characters from the cast files speak. Names are written exactly as in their name: line, in capitals.
- People speak in short lines: at most 25 words a line, most lines 4-14 words. One thought per line.
- A scene is 6-20 lines. An episode is 3-5 scenes. Every scene changes something (a secret, a choice, a threat).
- The narrator links scenes and says what the pictures can't (time jumps, inner thoughts); max 2 lines in a row.
- End on a cliffhanger line that makes people want the next episode.

STEP 1, before the script, in 5 lines: the episode's question, what each main character wants in it, the turn
in the middle, the cliffhanger, and which earlier thread it pays off.

STEP 2, the script, as ONE markdown code block in exactly this format:

---
series: <the series id: the folder name>
episode: <number>
title: <the episode title, max 40 characters>
description: |
  <2 lines that tease the episode without spoiling the turn>
tags: <5-8 search words>
type: episode
rendering_method: series
music: <a mood: mystery, tense, epic, emotional, calm, dark, uplifting>
---
## SCENE 1 | <a set id from sets/, e.g. STREET> | <DAY, DAWN, DUSK, NIGHT or FOG>
[cast: <NAME> at left, <NAME> at right]
NARRATOR: <one line that sets the scene>
<NAME> (<emotion>): <line>
<NAME> (<emotion>, close): <line>

Dialogue: NAME (emotion, camera): line. Emotion is one of: neutral, calm, happy, cheerful, laughing, sad, quiet,
angry, furious, shouting, scared, afraid, nervous, worried, shocked, surprised, smirk, smug, determined, cold,
menacing, tired, bored, crying, confused, proud, hopeful, whispering. The camera word is optional and only for a
line that must be framed a certain way: close, medium, two_shot, wide, over_shoulder, low, high (the framing is
picked automatically otherwise).
[cast: ...] places people at the start of a scene: left, right, centre, background, far_left, far_right,
back_left, back_right. [sfx: thunder] adds a sound, [pause: 1.5] a silence. Don't write fights or super powers
yet ([fight:], [power:] come later); show tension through dialogue, faces and silences.
