You write YouTube Shorts for a faceless channel. There is no presenter, host or mascot: the narrator is an unnamed
voice, and the pictures are AI images plus number / text cards. Write ONE Short about:

TOPIC: <one surprising fact or idea, e.g. "Nvidia fell nine percent in one day. Here's what caused it.">
MY ANGLE: <optional>

STEP 1, research. Search the web. List every fact you use with its source (publication, date, link).
STEP 2, the script, as ONE markdown code block in exactly this format:

---
title: <max 90 characters, ends with #Shorts>
type: short
rendering_method: ai_image
music: <one mood: calm, dark, emotional, epic, mystery, tech, tense, uplifting>
art_style: doc_photo
thumbnail: <2-4 words, ALL CAPS>
tags: <6-10 comma separated tags>
description: |
  <one sentence>
  Sources: <publication, date: link>
---

[ai: <the most striking picture of the surprise, vertical framing>]
<the surprise itself, in the first 2 seconds: no intro, no "today we'll look at">
[number: 9 | percent: what it measures | suffix=%]
<the one fact>
[ai: <...>]
<...>

RULES (Video Studio's Check enforces the numbers)
- 75-220 spoken words = 30-90 seconds. Over 2:00 or under 15 s is an error.
- Pattern: hook (2 s) -> the one fact (10-20 s) -> why it matters (20-40 s) -> the loop line.
- One idea only. No chapters (no "## " headings). No format: line (a Short is always vertical).
- Change the picture every 2.5-5 seconds (6-12 words); Check warns above 6 s.
- About half the shots are [ai: prompt]: one detailed prompt about WHAT is in the picture (subject, setting,
  camera angle, lighting, mood), framed for a tall 9:16 picture. Don't name a look or medium (the art_style: line
  adds it). NO text, letters, numbers, logos, screens with words, or real people's faces (silhouettes, hands,
  crowds from behind). Never repeat a prompt.
- The other half: [number: 3.2 | label | prefix=$ suffix=T], [card: BIG TEXT | small line],
  [chart: bar | title | label: number, label: number], [quote: exact words | who said it, where] (real quotes only).
  Every tag must be followed by narration.
- The LAST line must loop back into the FIRST line (so the replay sounds continuous). No sign-off, no
  "subscribe", no question for the comments.
- Facts only from your research list; numbers written as words in the narration; no stage directions, no emojis.
