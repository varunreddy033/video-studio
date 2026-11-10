# Presenter plan, step 1 results (2026-11-08)

Question: can FLUX.2 klein 4B in mflux 0.24 (a) keep one character consistent across 10 scenes using reference
images, and (b) edit only the mouth area? Placeholder character: cartoon cat in a navy blazer.
Contact sheet: `step1_contact_sheet.jpg`. Script: `tools/presenter_bench.py` (outputs in output/presenter_bench/).
Pipeline unchanged.

## What mflux can do
- `Flux2KleinEdit.generate_image(image_paths=[...])`: one or more reference images (CLI `mflux-generate-flux2-edit
  --image-paths`). Works with our 4-bit klein 4B model. No mask / inpainting option.

## A. Reference-conditioned scenes (1 reference, 10 scenes, 1280x720)
- Outfit kept: 10/10. Face and fur clearly the same cat: 7/10.
- Drift: rain and bubble scenes got a darker grey-blue head; the stage scene grew an orange calico patch.
- Close-up scene kept the reference's plain grey background (reference "leaks" when the framing matches it).
- Actions followed well and compositions were varied (wide, seated, walking).
- Speed: 67-80 s per image (avg 74 s), about 3x slower than plain generation.

## B. Fallback: fixed seed + detailed character prompt, no reference
- Outfit 10/10, face 10/10: the most consistent set, no drift.
- Shots are more alike (cat centred, front-on); the character is not the hand-picked candidate (different nose stripe):
  the look is defined by prompt + seed, not by an image.
- Speed: 24-34 s per image (avg 31 s).

## C. Mouth / eye edits of one presenter image (1024x1024)
- The edit changes only 0.3-0.6% of pixels outside the mouth (blink 1.8%, it changes the eyes). Pose, fur, blazer,
  background stay the same.
- Usable on the first try: slight open, wide open, E (teeth), blink. Closed and M/B/P look the same as the resting
  mouth (fine: the base has closed lips). O failed on the first prompt; a stronger prompt works (seed 3101), the other
  seed stuck the tongue out. So: 2-3 seeds per shape + a human pick.
- Pasting back only the mouth area (feathered ellipse) onto the untouched base: seamless, 0.0% change elsewhere, and it
  removes the small eye-highlight changes the raw edit makes. Use this for lip-sync frames (no flicker).
- Speed: 54-91 s per edit (avg 79 s).

## Recommendation for step 2 (character pack) and step 4 ([act:] shots)
1. Make the master reference with the SAME character prompt + seed we use for scenes, so presenter poses and story
   scenes are the same cat (in this test the hand-picked reference and the seed-only cat differ slightly).
2. [act:] scenes: default to fixed seed + detailed prompt (most consistent, 31 s); use the reference image only when
   a scene needs a specific pose or the prompt-only version drifts (74 s).
3. Mouth pack: generate each shape by edit from the pose image, 2-3 seeds each, Varun picks, then paste back the mouth
   area only. Rough one-time cost: 7 shapes x 7 poses x 2 seeds x ~80 s = about 2.2 hours.
4. The plan's sprite-overlay fallback for mouths is NOT needed.
