# Motion phase 6 benchmark: Sterling Flat (2026-11-10)

Question: can FLUX.2 klein 4B keep a **flat 2D** Sterling (same design: grey-and-white cat, navy blazer, burgundy tie)
consistent across the 7 presenter poses, and edit only his mouth and eyes? Same method as presenter step 1
(RESULTS.md), using the pack builder's own prompts. Character file: docs/characters/sterling_flat.md (SEED 2000).
Contact sheet: `flat_contact_sheet.jpg`. Script: `tools/flat_bench.py` (images in the shared cache, results in
output/flat_bench/results.json).

## Results
| Test | Result |
|---|---|
| 4 master candidates (seed 2000-2003) | all four on-model and alike; seed 2000 (+0) is the cleanest: centred, symmetrical, tie and blazer crisp |
| Poses A (fixed seed + pose prompt) | 7/7 on-model, identity 0.97-1.00 vs the master; more variety (full body in neutral and laughing, a tail in 3) |
| Poses B (edit of the master) | 7/7 on-model, identity 0.98-1.00, same face, same proportions, same outfit in every pose: the most consistent set |
| Mouth + blink edits | slight, wide, O, E (teeth), M/B/P and blink all worked first try; only 0.7-1.0% of the picture changes outside the mouth/eyes |

Small flaws: B's neutral pose came out full-body (as with Sterling, so use the master for neutral); B's shocked pose
has darker grey paws; the O mouth is a small dark dot (reads fine at puppet size).

## Times on the M5 Air (on battery, 43% -> 33%)
masters 4 x ~21 s, poses A ~24 s each, poses B (edits) ~52 s each, mouth/blink edits ~52 s each, plus 8 s cool-down
after each: **19 minutes** for 25 images.

## What this means
A full pack (7 poses, 6 mouths + blink per pose, 2 tries each, cut-outs, 2 sets) is the same work as Sterling's:
about **1 h 40 min**, plugged in. Recommended picks: master = seed 2000, poses = B (edit of the master) with
`overrides.json {"neutral": "master"}`. The flat style keeps him more consistent than the 3D look did (B identity
0.98-1.00 here vs 0.79-0.96 for 3D Sterling), so the SVG-puppet fallback isn't needed.
