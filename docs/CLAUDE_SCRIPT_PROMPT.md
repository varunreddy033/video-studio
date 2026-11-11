How to use: copy ONE prompt below (from its line of dashes to the next) into a Claude chat, fill in the TOPIC /
LENGTH / ANGLE lines, and paste Claude's script into Video Studio -> + New video -> Check. If Check shows errors or
warnings, paste them back to Claude and ask it to fix the script.

  A. STERLING PRESENTS   (recommended: our cat presenter on camera + acting out the story)
  B. NO PRESENTER        (documentary style: AI images + cards only)
  C. STERLING SHORT      (a 30-90 s vertical Short from scratch; for a Short cut from a finished video, use
                          Make Short -> From a video I already made instead: no script needed)
  D. MOTION GRAPHICS     (bright-pop animated explainer: kinetic words, stick figures, transitions, caption chip;
                          no AI images, fast to render. Example: docs/sample_motion_gfx_script.md)

================================================================================================================
A. STERLING PRESENTS
================================================================================================================

You are the head writer for "Sterling", an animated YouTube channel where a cartoon cat in a navy blazer explains
money, markets and tech. Write a complete, ready-to-render script for:

TOPIC: <today's trending topic>
LENGTH: <8 / 10 / 15> minutes of narration (Sterling speaks about 145 words per minute)
MY ANGLE: <my opinion / what to emphasise / what to avoid>

STEP 1, research. Search the web for the latest facts. List every fact you will use with its source (publication,
date, link) so I can check them. Use only facts from that list.

STEP 2, the script. Output it as ONE markdown code block, in exactly this format:

---
title: <honest, high-curiosity title, max 90 characters>
character: sterling
format: landscape
music: <one mood: calm, dark, emotional, epic, mystery, tech, tense, uplifting (or one per chapter: mystery, tense, epic)>
thumbnail: <2-4 word thumbnail text, ALL CAPS, ends with ? or !>
thumbnail_prompt: <Sterling's reaction + one striking background, e.g. "looking shocked in front of a huge red crashing chart">
tags: <8-12 comma separated search tags>
description: |
  <2-3 sentence hook for the YouTube description>
  Not financial advice. I'm a cat in a blazer.
  Sources:
  <one line per source: publication, date: link>
  <3-5 hashtags>
---

## <Chapter 1 heading>
[talk: neutral | studio]
<1-3 sentences Sterling says to camera>
[number: 5.5 | percent: what the number means | suffix=%]
<the sentence that says that number>
[act: <what Sterling is doing + where, e.g. sitting at a trading desk with monitors showing red charts, ears flat> | medium]
<narration while we see that scene>
[talk: pointing | studio]
<...>

WHO STERLING IS
- Calm, sharp, slightly dry. Explains like a smart friend, skeptical of hype, never shouts, never slapstick.
  Talks to "you" in first person ("Here's what nobody tells you...").
- Catchphrases: opening "Pull up a chair." Key line "Let's follow the money." Sign-off, the very last line:
  "Stay curious. Stay skeptical. I'm Sterling."
- One honest personal take per video ("Here's my take."), and at least one "but here's the catch" moment.

THE THREE SHOT TYPES (a shot tag changes the picture exactly where the next words start)
1. [talk: POSE | SET]  Sterling on camera, lip-synced. About 40% of shots.
   POSE: neutral, pointing, shrug, shocked, thinking, serious, laughing (pick the one that fits the line).
   SET: studio (default) or stage (for big reveals). Optional 3rd part: zoom in / zoom out.
   Each [talk:] beat is 1-3 sentences (max ~25 seconds). Every chapter STARTS with a [talk:].
2. [act: WHAT HE DOES + WHERE | wide / medium / close]  Sterling acting out the story. About 20-25% of shots,
   6-12 seconds each. Vary the framing (wide, medium, close).
   Describe ONLY his action, expression and the place: "standing in a long data center aisle with blue server lights,
   looking up at the towering racks". NEVER write "a cat", "another cat", "a single cat", "him", "her", "Sterling"
   or any other person or animal in an [act:] (the model adds extra characters). No readable text, logos, screens
   with words, or real people.
3. Evidence: about 35% of shots, 3-8 seconds each, for every key number, comparison and real quote.
   [number: 96.2 | label: what it measures | prefix=$ suffix=B]   (prefix/suffix optional, can share one slot)
   [card: BIG TEXT | small line]
   [chart: bar | title | label: number, label: number, label: number]   (or line)
   [quote: exact words | who said it, where]   (only real, sourced quotes)

PACING RULES (Video Studio's Check enforces these)
- Never more than 3 shots in a row without Sterling ([talk:] or [act:]).
- Change the picture at least every 12 seconds (about 30 spoken words); [talk:] beats may run up to 25 seconds.
- Every [number:], [card:], [chart:] or [quote:] must be followed by narration (a tag with no line after it is dropped).
- At least 3 chapters ("## " headings), the first one before any narration. The first 8 seconds are the hook.
- [sfx: typing] works now; other sound effects are optional: [sfx: whoosh|riser|sub-drop|glitch|click].
  [pause: 1] before a big reveal.

WRITING RULES
- Facts: only from your research list. Never invent quotes, statistics, dates or actions by real people. If something
  is uncertain, say so out loud or leave it out.
- Write for the ear: short sentences, contractions, numbers written as words in the narration ("ninety-six point two
  billion dollars"), no abbreviations ("for example", not "e.g."), no stage directions, no emojis.
- End with a question for the comments, then the sign-off line.
- Make it feel like a real person's take: include my angle.

================================================================================================================
B. NO PRESENTER (documentary style)
================================================================================================================

You are my scriptwriter for a faceless YouTube documentary channel. Write a complete script for:

TOPIC: <today's trending topic>
LENGTH: <10 / 20 / 30> minutes of narration (about 150 spoken words per minute)
MY ANGLE: <my opinion / what to emphasise / what to avoid>

First, research the topic (search the web if you can) and list the facts you will use, each with its source
and date, so I can check them. Then write the script.

Output the script as ONE markdown code block in exactly this format:

---
title: <honest, high-curiosity title, max 90 characters>
description: |
  <2 short paragraphs for the YouTube description>
  <3-5 hashtags>
tags: <8-12 comma separated search tags>
format: landscape
music: <one mood: calm, dark, emotional, epic, mystery, tech, tense, uplifting (or one per chapter: mystery, tense, epic)>
art_style: doc_photo
thumbnail: <2-4 word thumbnail text>
thumbnail_prompt: <one striking image idea for the thumbnail, no text in it>
---

## <Chapter 1 heading>
[ai: <detailed image prompt>]
<narration>
[card: <BIG TEXT> | <small line>]
<narration>
...

Rules:
1. Start with "## " chapter headings: at least 3, the first one before any narration.
2. Change the picture every 5-10 seconds (every 13-25 spoken words) with a shot tag:
   - [ai: prompt]  about 65% of shots (about 45-55 per 10 minutes), each on screen 6-10 seconds. One detailed
     prompt about WHAT is in the picture: subject, setting, camera angle, lighting, mood. Don't name a look or
     medium (photo, painting, comic...): the art_style: line adds that to every image, and I pick it later. Make neighbouring shots look different
     (wide / close-up / aerial / interior). NO text, letters, numbers, logos, screens with words, or real people's
     faces (show people as silhouettes, hands, crowds from behind). Never repeat a prompt word for word.
   - [card: BIG TEXT | small line], [number: 3.2 | label | prefix=$], [quote: exact words | who said it, where],
     [chart: bar | title | label: number, label: number, ...]  about 35% of shots, 3-6 seconds each, for every key
     fact, number, comparison and real quote. Every one must be followed by narration.
3. [sfx: whoosh|riser|sub-drop|glitch|shutter|typing|heartbeat|gavel|glass|electric|click] on about one shot in five,
   at moments of surprise. [pause: 1] before big reveals.
4. Facts: only facts from your research list. Never invent quotes, statistics, dates or actions by real people.
   If something is uncertain, say so in the narration or leave it out. Quotes must be real and attributed.
5. Write for the ear: short sentences, contractions, numbers in narration written as words
   ("three point two trillion dollars"), no abbreviations, no stage directions, no emojis.
6. Hook in the first 8 seconds. Each chapter ends pulling into the next. End with a question for the comments.
7. Make it feel like a real person's take: include my angle, and one or two moments of honest opinion.

================================================================================================================
C. STERLING SHORT (vertical, 30-90 seconds, from scratch)
================================================================================================================

You write YouTube Shorts for "Sterling", a cartoon cat in a navy blazer who explains money, markets and tech.
Calm, sharp, slightly dry, skeptical of hype. Write ONE Short about:

TOPIC: <one surprising fact or idea, e.g. "Nvidia fell nine percent in one day. Here's what caused it.">
MY ANGLE: <optional>

STEP 1, research. Search the web. List every fact you use with its source (publication, date, link).
STEP 2, the script, as ONE markdown code block in exactly this format:

---
title: <max 90 characters, ends with #Shorts>
type: short
character: sterling
music: <one mood: calm, dark, emotional, epic, mystery, tech, tense, uplifting (or one per chapter: mystery, tense, epic)>
thumbnail: <2-4 words, ALL CAPS>
tags: <6-10 comma separated tags>
description: |
  <one sentence>
  Not financial advice. I'm a cat in a blazer.
  Sources: <publication, date: link>
---

[talk: shocked | studio]
<the surprise itself, in the first 2 seconds: no intro, no "today we'll look at", no "Pull up a chair">
[number: 9 | percent: what it measures | suffix=%]
<the one fact>
[talk: pointing | studio]
<...>

RULES (Video Studio's Check enforces the numbers)
- 75-220 spoken words = 30-90 seconds. Over 2:00 or under 15 s is an error.
- Pattern: hook (2 s) -> the one fact (10-20 s) -> why it matters (20-40 s) -> the loop line.
- One idea only. No chapters (no "## " headings).
- Change the picture every 2.5-5 seconds (6-12 words); Check warns above 6 s ([talk:] up to 10 s).
- Mostly [talk: POSE | studio] (poses: neutral, pointing, shrug, shocked, thinking, serious, laughing) plus
  [number:] / [card:] / [chart:] for the facts. At most 2 [act: what he does + where | wide/medium/close]
  shots (each is a new AI image; describe only his action and the place, never "a cat", "him" or other people).
- The LAST line must loop back into the FIRST line (so the replay sounds continuous). No sign-off, no
  "subscribe", no question for the comments.
- Facts only from your research list; numbers written as words in the narration; no stage directions.

================================================================================================================
D. MOTION GRAPHICS (bright-pop animated explainer, no presenter, no AI images)
================================================================================================================

You are my scriptwriter for a faceless YouTube explainer channel. The video is rendered as bright-pop motion
graphics: kinetic words that land on the spoken word, anonymous stick figures with props, big numbers, quotes,
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
4. Use commas and full stops generously: every clause is one picture (1.2-3 seconds). Short sentences.
5. Real people: the figures are anonymous stick figures, never drawn as the real person. Never invent quotes,
   facts, dates or actions. Attribute every claim ("X reported", "according to Y"), give the other side
   (denials, official responses), and say clearly when something is an allegation and not proven.
6. Write for the ear: contractions, numbers in narration written as words ("ninety-six point two billion
   dollars"), no abbreviations, no stage directions, no emojis.
7. Hook in the first 8 seconds. End with a question for the comments. Include my angle and one honest opinion
   moment so it feels like a real person's take.
