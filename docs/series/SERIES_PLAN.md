# Web series + films in Video Studio (our own superhero franchise)

Status: PLAN (2026-11-21, Varun). Same repo, same studio: a new "Web series" mode next to today's videos. It reuses
everything we already have (Kokoro voices, HyperFrames, the Blocky 3D engine and its CC0 Kenney sets, the music/SFX
library, designed thumbnails, the upload pack) and adds what fiction needs: a series bible, recurring characters,
dialogue with many voices, acting, super powers, fights, sets and episode packaging.

Rule that never changes: everything is ORIGINAL. No Marvel/DC/anime characters, names, costumes, logos, catchphrases or
music. "Like Avengers" means the scale and the feeling, never the content.

## 1. Where it lives (UI)

- The top bar "+ New" opens a two-level choice:
  1. **Video** -> Full video | Short (today's flow, unchanged)
  2. **Web series** -> New episode of an existing series | New series
- Menu tree gets a **Series** section above Recent videos: each series expands to its episodes (status dot,
  "Ep 3: The Fall"), plus "Series bible", "Cast", "Sets", "New episode".
- A series page: poster/key art, logline, season arc as a strip of episode cards (written / rendered / published),
  cast grid (each character's look + voice, a "hear voice" button), and buttons: New episode, Edit bible, Render trailer.
- An episode page = today's job page (video, thumbnails, YouTube fields, script) plus "Previously on" and "Next
  episode" links.

## 2. Files: a series is a folder

```
series/<series-id>/
  series.md        logline, genre, tone, rating (all-ages / teen), world rules, season arc, recurring themes
  cast/<id>.md     one file per character: name, role (hero/villain/ally/civilian), look, powers, voice, personality,
                   speech style, catchphrase (original), arc per episode, alive/dead status (continuity)
  sets/<id>.md     locations used by this series (built on the Blocky 3D sets + new ones), time of day, mood
  episodes/ep01.md episode scripts (format below); ep00.md = the trailer
  art/             key art, logo, episode thumbnails (generated)
  continuity.json  written by Check: who knows what, who is where, injuries, deaths, items, open mysteries
```
`series/` is in git (scripts and bibles are ours); rendered episodes stay in output/ like every video.

## 3. Episode script format (extends the Blocky 3D format)

```
---
series: grid-guardians
episode: 3
title: The Fall
type: episode                 # 16:9; episode_short = a 9:16 Short cut or side story
rendering_method: series      # Blocky 3D engine + the series features below
previously: auto              # 20-40 s recap built from earlier episodes' key moments
cold_open: yes
theme: auto                   # the series' title card + theme sting
---
## SCENE 1 | ROOFTOP | NIGHT, RAIN
[cast: KAI at left, VEX at right]
NARRATOR: Three days after the blackout, the city still had no lights.
KAI (angry, close): You shouldn't have come back.
VEX (smirk): And miss your big night?
[fight: VEX dash -> KAI | KAI block | VEX kick -> KAI knockback | camera=shake]
KAI (determined): My turn.
[power: KAI lightning_beam -> VEX | VEX shield | slowmo 0.4 | camera=orbit]
[sfx: thunder]
## SCENE 2 | LAB | DAY
...
## TO BE CONTINUED | KAI's mask cracks
```
- `NAME (emotion, camera): line` = dialogue: the character's own voice, face and talking mouth, framed automatically
  (speaker close-up, listener reaction, two-shot every few lines). Emotion -> face + body language + voice delivery.
- `NARRATOR:` = the series narrator voice (optional, can be off for pure drama).
- `[cast: ...]` blocking: who is in the scene and where (left/right/centre/background, facing).
- `[fight: ...]` choreography: a chain of moves (section 5) separated by `|`, each `A move -> B` with B's reaction.
- `[power: A power -> B | B defence | slowmo | camera]` super powers (section 5).
- `[action: A move | camera]` single non-fight beats (walk in, sit, look away, fly up, land).
- `[shot: ...]`, `[sign: ...]`, `[sfx: ...]`, `[pause: ...]` keep working as in Blocky 3D.
- Check warns: a character not in the cast, a dead character speaking, a power the character doesn't have, a line
  longer than ~25 words, a scene with no action for more than ~20 s, an episode under 8 or over 20 minutes.

## 4. Characters (cast files -> 3D rig)

- Build on the Blocky 3D rig (own rig + 38 studio characters, 28 faces, talking mouth). Add a **superhero kit**:
  suits with original chest emblems (code-drawn shapes: bolt, ring, wave, shard, star, eye), capes (cloth sim or
  spring bones), masks/visors/helmets, gauntlets, boots, glowing eyes/lines, armour plates, hair and colours per
  character. A villain kit: long coats, horns/crowns, cracked armour, shadow aura.
- Every character keeps the same look in every episode (the cast file is the single source).
- Faces: the existing 9 + 28, plus fight faces (gritted teeth, shouting, hurt, exhausted, victorious).
- Voices: each character gets a Kokoro voice + speed + optional voice effect (ffmpeg): deep villain (pitch down),
  AI/robot (ring modulation + bit crush), echo (giant/cosmic), radio (comms), whisper. "Hear voice" on the cast page.

## 5. Action: fights, powers, VFX, camera

- **Move library** (keyframed on the rig, springs for weight): idle_guard, step, dash, jump, flip, fly_up, hover,
  fly_dash, land_hero (one knee), punch_jab, punch_heavy, uppercut, kick_front, kick_spin, block, parry, dodge_left,
  dodge_right, grab, throw, slam, knockback, stagger, fall, get_up, collapse, team_pose. Hit reactions are automatic.
- **Powers** (VFX in Three.js shaders/particles): energy_beam, lightning_beam, fireball, ice_shards, shockwave,
  shield_bubble, force_push, telekinesis_lift, teleport_blink, super_speed_trail, size_grow, invisibility,
  portal_open, ground_crack, healing_glow. Each power has a colour per character.
- **Impact language:** hit-stop (2-4 frames freeze), white impact flash, speed lines, screen shake, dust and debris,
  sparks, shockwave rings, slow motion, camera whip to the hit.
- **Destruction:** breakable props (walls, cars, windows, lamp posts) that crack/fly on knockback; craters.
- **Camera:** wide, two-shot, over-shoulder, close-up, extreme close-up (eyes), low hero angle, high villain angle,
  orbit around a clash, crane up for team shots, tracking for chases, dolly zoom for shock moments.
- **Choreography helper:** a `[fight:]` line with only the outcome ("KAI wins, VEX escapes") can be expanded by Check
  into a default 6-10 move chain the writer can then edit.

## 6. Sets

Use the existing Blocky 3D sets (night_town, street, space, arena, forest...) and add series sets built from the CC0
Kenney kits: rooftop_night, city_skyline, hero_hq, villain_lair, research_lab, metro_station, harbour, ruined_city,
sky_battle (clouds), orbit (planet below), interrogation_room, rooftop_sunrise (finales). Weather: rain, snow, fog,
smoke, ash. Time of day and grades: day, dusk, night, storm, apocalypse red.

## 7. Episode packaging

- Cold open (the hook, before the title), series title card + 5-8 s theme sting, "Previously on" (auto from earlier
  episodes: 3-5 key lines and shots), scene cards, end on a cliffhanger card "To be continued", a 10 s "Next time"
  tease built from the next episode's script when it exists, end screen space for YouTube cards.
- Series branding: one logo, one colour pair, one font pair; designed thumbnails use the series key art + the
  episode's main character + "EP 3" badge. Thumbnail rule still applies: evergreen hook + timely tag.
- Trailer (`ep00.md`): 60-90 s, built from the season's best lines and fights.
- Upload metadata: playlist name, episode number in the title ("Grid Guardians | Ep 3: The Fall"), description with
  "Previously" and "Next" links.

## 8. Assets to pull (licence allow-list as always: CC0 / public domain / MIT / Apache / OFL; anything else listed for
Varun to approve first; every download logged in assets/*/CREDITS.md with source URL and licence)

| Need | Source (check the licence page at download time) |
|---|---|
| City, sci-fi, space, nature, interior kits | Kenney.nl kits (CC0): City Kit (commercial/suburban/roads), Space Kit, Space Station Kit, Pirate/Castle kits for variety, Nature Kit (24 Kenney packs are already in assets/blocky3d; add only what's missing) |
| Particles and VFX textures | Kenney Particle Pack (CC0); code-drawn shaders for beams and shields |
| Fight and power sound effects | Kenney Impact Sounds, Sci-fi Sounds, Digital Audio (CC0); Freesound with the CC0 filter only; Pixabay sound effects (Pixabay licence, already used) |
| Epic, battle, tension, emotional music | YouTube Audio Library (manual download, safest), Pixabay Music; track licence + page URL in each track's .json |
| Fonts for title cards | Google Fonts under OFL (e.g. Bebas Neue, Orbitron, Russo One) |
| Ambience | rain, wind, city night, crowd, sirens: Freesound CC0, Pixabay |
Never: game rips, film audio, fan-made assets of existing heroes, anything "free for personal use only".

## 9. Build order (one PR per phase, each tested)

1. **Foundation:** series folder + bible/cast/sets files, the two-level "+ New" UI, series pages, the episode script
   format with `NAME (emotion):` dialogue, multi-voice cast + voice effects, automatic dialogue framing, 16:9
   Blocky 3D episodes, scene cards. Test: a 3-minute two-character dialogue scene with a narrator.
2. **Superhero kit + sets:** suits, capes, masks, emblems, glowing eyes, villain kit, the new sets and weather.
   Test: a cast line-up shot of 6 heroes + 2 villains on three sets, and a contact sheet.
3. **Action:** move library, powers, impact language, destruction, fight camera, `[fight:]`/`[power:]`/`[action:]`
   tags and Check rules. Test: a 60-second rooftop fight, 2 heroes vs 1 villain, 4 powers, and a frame-by-frame
   smoothness check.
4. **Packaging:** cold open, theme sting, previously-on, cliffhanger, next-time, trailer builder, series thumbnails,
   playlist metadata. Test: render ep00 (trailer) and ep01 of a sample series.
5. **Continuity:** continuity.json + Check rules across episodes; a "bible" view in the UI.
Assets for each phase are pulled in that phase.

## Appendix: series bible template (series.md)

```
title:            (working title)
logline:          one sentence: hero + goal + obstacle + stakes
genre / tone:     superhero action, PG-13, hopeful with dark turns
world:            where and when; the one rule that makes the world different
origin event:     what created the powers / the conflict
heroes:           4-6, each: power, flaw, wound, what they want vs what they need
villain(s):       the big villain (wants something understandable) + 1-2 lieutenants
season question:  the question episode 12 answers
arc (12 eps):     1-3 origins and the first defeat | 4-6 the team forms, first win | 7 midpoint twist |
                  8-9 betrayal and the fall | 10 lowest point | 11 the comeback | 12 the final battle + the hook for season 2
episode shape:    cold open, 3-4 scenes, one fight or set-piece, cliffhanger; 10-15 minutes
```
