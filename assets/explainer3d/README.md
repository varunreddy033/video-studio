# assets/explainer3d: models of the 3D explainer style

For `rendering_method: explainer3d` (docs/SCRIPT_FORMAT.md section 7). Own, original low-poly / stylised models built
from primitives in the explainer pack (2026-11-18): no ripped or branded assets, no real-person likenesses, no logos.
glTF binary, Y up, about metre scale, not rigged (named groups for posing). In git (6.8 MB).

| Folder | Models (id = file name) |
|---|---|
| characters/ | pictogram_person_red, pictogram_person_green, purple_titan (holds the gauntlet; groups Head, RightShoulder, RightElbow, LeftShoulder) |
| props/ | power_gauntlet (finger groups Index_1..3 ... Thumb_1..2, 6 emissive gems), smartphone, metal_bucket, kiddie_pool, chain_link, basketball, hospital_bed, chrome_faucet, oxygen_mask |
| food/ | apple, bread_loaf, fish, rice_bowl |
| space/ | earth, planet_titan |
| environment/ | power_pylon |

previews_sheet.jpg = every model rendered once.

**Licence note:** `purple_titan` and `power_gauntlet` are original models, but they are a look-alike of a famous film
villain and his glove. Using them with that character's name is fan-parody territory: fine for tests, risky for
monetised uploads (copyright / trademark claims). Prefer generic subjects in published videos.

Any blocky3d model works in this style too (`<pack>/<name>` ids from assets/blocky3d/index.json, e.g. `cars/police`,
`studio/trophy`). New models: add the .glb under the right folder here (own or CC0 only) and list it above.
