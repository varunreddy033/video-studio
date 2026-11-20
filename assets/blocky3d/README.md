# assets/blocky3d: assets of the blocky 3D story style

For `rendering_method: blocky3d` (docs/BLOCKY3D_PLAN.md, docs/SCRIPT_FORMAT.md section 6).

| Folder | What | Use it for |
|---|---|---|
| characters/ | blocky_characters (18 avatars, built-in animations: attack-kick-left, attack-kick-right, attack-melee-left, attack-melee-right, die, drive, emote-no, emote-yes, holding-both, holding-both-shoot, holding-left, holding-left-shoot, holding-right, holding-right-shoot, idle, interact-left, interact-right, pick-up, sit, sprint, static, walk, wheelchair-move-back, wheelchair-move-forward, wheelchair-move-left, wheelchair-move-right, wheelchair-sit), mini_characters (43), animated_characters_1 (FBX survivors + zombies, idle/run/jump) | the cast and crowds |
| city/ | commercial, suburban, roads, industrial, retro urban, building kit (walls, doors, windows), modular buildings | town_square, street, night_town, school and house exteriors, rooms built from walls |
| interiors/ | furniture (OBJ: beds, desks, kitchen, bathroom, office), mini shop, food (cakes, fruit, drinks) | bedroom, house_inside, classroom, cafeteria, shops |
| nature/ | nature kit (trees, rocks, camp), survival kit, pirate kit (palms, boats, docks) | park, forest, beach / island |
| vehicles/ | cars (police, taxi, trucks...), trains | streets, chases |
| themed/ | holiday (party, gifts), graveyard (horror, zombies), castle, space, platformer (arena / game show obstacles), fantasy town | arena, horror and "what if" worlds, space |
| music/ | YOUR background music, one folder per mood: funny, mystery, horror, emotional, hype, chill | the music bed (not in git) |

- index.json lists every model: id (pack/name), category, file, format (glb, obj, fbx), tags, animations.
- asset_check.jpg = 22 models from the packs rendered by our own Three.js + HyperFrames path (proof they load).
- The models are NOT in git (76 MB). On a new Mac: `bin/python tools/fetch_blocky3d_assets.py` (setup.sh runs it):
  downloads the pinned zips, checks SHA-256 + CC0 licence + every GLB's textures, rebuilds index.json.
  `--check` only verifies ("blocky3d assets: clean").
- Asset library rule: new models for this style go in as a new pack in packs.json (source URL, SHA-256, licence),
  never by hand, and nothing is deleted without asking.

## music/ (you add these)

Put tracks (mp3 / m4a / wav, 60 s or longer) in the mood folder that fits. This folder is gitignored, so licensed
tracks never reach GitHub.

**Read before using "trending Instagram audio":** almost all of it is commercial music. Instagram licenses it for
Reels on Instagram only; on YouTube the same song gets a Content ID claim (the owner takes the ad money, or the
video is muted or blocked in some countries). Safe sources for YouTube: the YouTube Audio Library, tracks you
bought a licence for, or CC0. Write where each track came from in music/SOURCES.md (file, source, licence), the
same way assets/library/music/CREDITS.md does.
