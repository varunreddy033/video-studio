# Video types: two buttons on the dashboard

Status: BUILT (2026-11-09), see CLAUDE.md for timings. Decided: the dashboard has TWO buttons, **Make Short** and **Make full video**.
Both work the same on every machine I own (Mac and Legion run identical code, same repo, same roles), so I can
work on whichever laptop is with me.

## The two types
| | Full video | Short |
|---|---|---|
| Size | 1920x1080 (16:9) | 1080x1920 (9:16) |
| Length | 10-14 min | 30 s to 2 min (hard cap 2:00; YouTube allows 3:00, we stay under it) |
| Words | ~1500-2100 | ~75-300 |
| Hook | first 8 s | first 2 s, no intro, no "today we'll look at" |
| Picture changes | every 5-10 s | every 2.5-5 s |
| Chapters | yes (3+) | none |
| Music | per chapter, with crossfades | one track, no crossfade |
| Captions | bottom, standard size | bigger, placed higher: keep the bottom 20% and right 12% clear of the Shorts buttons |
| Ending | question for the comments | a line that loops back into the first line |
| Thumbnails | 3 options | 1 (Shorts mostly show a frame) |
| Upload pack | final.mp4, thumbs, metadata, chapters | final.mp4, 1 thumb, metadata, #Shorts in the description |

## Making a Short: two ways (both behind the same button)
1. **From scratch** — I paste a short script. Needs 0-2 new AI images when it's mostly Sterling talking
   (his pose pack is already built), so it is fast on any machine.
2. **From a video I already made** — pick a finished job + a start and end time. Reuses that job's cached
   images and voice, re-frames to vertical (keep the character centred, crop graphics to safe area),
   re-renders the captions vertically. NO new AI images, so it is fast everywhere.

## Script header
```
type: short            # short | full   (default: full)
clip_from: <job id>    # only for "from a video I already made"
clip_start: 4:12       # mm:ss
clip_end: 5:38
```
The Check page shows the type, the measured length and type-specific warnings (a Short over 2:00 is an ERROR,
under 15 s is an ERROR, a picture held longer than 6 s in a Short is a warning).

## Quick-topic Shorts: what works
One idea per Short. Open with the surprise, not the setup. Examples for this channel:
- "Nvidia fell nine percent in one day. Here's what actually caused it."
- "What does 730 billion dollars of AI spending actually buy?"
- "Three signs the AI bubble is about to pop."
Pattern: hook (2 s) -> the one fact (10-20 s) -> why it matters (20-40 s) -> the loop line.

## Both machines, same ability
Same repo, same code, same character packs. Each machine has its own .env, its own jobs and its own server;
nothing is shared at runtime. The only thing copied by hand is a character pack (201 MB, kept out of git):
`tools/export_character_pack.py <id>` makes a zip; the other machine imports it.
The Legion is better for Shorts and for clips (little or no new image generation, and it has fans).
The Mac is better for long videos (fast local image generation).
