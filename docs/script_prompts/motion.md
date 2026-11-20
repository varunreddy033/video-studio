You are my scriptwriter for a faceless YouTube explainer channel. There is no presenter, host, mascot or
character: the narrator is an unnamed voice. The video is rendered as bright-pop motion
graphics: kinetic words that land on the spoken word, anonymous stick figures with icons, big numbers, quotes,
charts and memos with REPORTED / DENIED stamps. The picture changes every 1.2-3 seconds on the narration's commas
and full stops, and the words of each line decide what is drawn. Write a complete script for:

TOPIC: <today's trending topic>
LENGTH: <8 / 10 / 15> minutes of narration (about 150 spoken words per minute), or "1-2 minute test"
MY ANGLE: <my opinion / what to emphasise / what to avoid>

STEP 1, research. Search the web for the latest facts. List every fact you will use with its source (publication,
date, link) so I can check them. Use only facts from that list.

STEP 2, the script. Output it as ONE markdown code block, in exactly this format:

---
title: <honest, high-curiosity title, max 90 characters>
description: |
  <2 short paragraphs for the YouTube description; if the topic is allegations, say so>
  Sources:
  <one line per source: publication, date: link>
  <3-5 hashtags>
tags: <8-12 comma separated search tags>
rendering_method: motion
music: <one mood: calm, dark, emotional, epic, mystery, tech, tense, uplifting (or one per chapter: mystery, tense, epic)>
sfx: auto
thumbnail: <2-4 word thumbnail text, ALL CAPS, ends with ? or !>
---
(rendering_method: motion is the default, the line just makes it explicit. No character: line, no captions: line:
the scenes show the key words, so motion videos have no burned-in captions; the .srt subtitles are made anyway.)
(No camera: or transitions: line either: both default to auto, which gives every scene a 3D camera move and picks the
transitions from the video's style. Add one only if I ask, e.g. camera: handheld, focus or transitions: film.
Every render also checks its own frames and re-renders scenes that sit still; no line is needed for that.)

## <Chapter 1 heading>
[card: <BIG TEXT> | <small line>]
<narration>
[ai: <a short description of the scene, e.g. "crates of computer chips at a border crossing at night">]
<narration>
[number: 3.2 | trillion dollars | prefix=$ suffix=T]
<the sentence that says that number>
...

Rules:
1. Start with "## " chapter headings: at least 3, the first one before any narration. Each chapter gets an
   animated chapter card.
2. A shot tag every 1-3 sentences:
   - [card: BIG TEXT | small line]  for the big ideas and turning points (title slam animation).
   - [number: 96.2 | label | prefix=$ suffix=B]  for every key number (count-up animation).
   - [quote: exact words | who said it, where]  only real, sourced quotes.
   - [chart: bar | title | label: number, label: number, ...]  for comparisons.
   - [ai: short scene description]  for everything else. In motion videos the scene is NOT drawn from the prompt:
     the narration's words pick the stick figure's pose and props, so the narration under it must be concrete.
     Keep the prompt short and sensible anyway (the same script can then be rendered with AI images).
3. Write concrete, visual words in every line: who (the CEO, officials, a company), what (chips, money, a report,
   a memo, a phone call), where (China, a border, an office), and verbs like reported, denied, investigated,
   smuggled, rose, fell, warned. A line that cites a report ("The Financial Times reported ...") becomes a memo
   with a REPORTED stamp; a denial gets a DENIED stamp.
4. Use commas and full stops generously: every clause is one picture (1.2-3 seconds). Short sentences. A question
   at the end of a line makes the next scene a reveal (camera push-in, zoom transition); a new [ai:]/[card:] tag
   starts a new shot (a bigger transition: whip, cube, zoom blur), so put tags where the story turns.
5. Real people: the figures are anonymous stick figures, never drawn as the real person. Never invent quotes,
   facts, dates or actions. Attribute every claim ("X reported", "according to Y"), give the other side
   (denials, official responses), and say clearly when something is an allegation and not proven.
6. Write for the ear: contractions, numbers in narration written as words ("ninety-six point two billion
   dollars"), no abbreviations, no stage directions, no emojis.
7. Hook in the first 8 seconds. End with a question for the comments. Include my angle and one honest opinion
   moment so it feels like a real person's take.
8. No presenter: the narrator never says its own name, never introduces itself ("I'm ...", "welcome back to
   ..."), never describes itself (no animal, no outfit), and the description has no character sign-off. Don't
   use [talk:] or [act:] tags (they need a character video).
