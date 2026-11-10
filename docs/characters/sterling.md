# Character: STERLING (grey-and-white cat in a navy blazer)

Status: ACTIVE for the first presenter video (2026-11-08). Built from the step-1 benchmark cat
(tools/presenter_bench.py, fixed-seed set B = 10/10 consistent). One character per video: a script picks it with
`character: sterling` in its header. Later characters (e.g. Miso, docs/CHARACTER.md) get their own file here.

## Who he is
- A calm, sharp, slightly dry cat in a suit who explains money and tech like a smart friend. Skeptical of hype.
  Never shouts, never slapstick. Talks to "you".
- Opening line: "Pull up a chair." Key line: "Let's follow the money." Sign-off: "Stay curious. Stay skeptical. I'm Sterling."

## Prompt blocks (word for word, from the benchmark)
CHARACTER = "a cartoon cat presenter with soft grey-and-white fur, big round amber eyes, a small pink nose,
wearing a tailored navy blue blazer over a crisp white shirt, a slim burgundy tie"
STYLE = "stylised 3D animated film look, soft studio lighting, clean shapes, vibrant but natural colours"
SEED = 1000 (the seed used for benchmark set B; keep it fixed for all [act:] shots unless a shot drifts)
Body words for the pack prompts: NOUN, LIMBS, FUR, OUTFIT, EARS (used in "the same cat character", "one paw on its chin", "same fur, same blazer").
NOUN = "cat"
LIMBS = "paws"
FUR = "fur"
OUTFIT = "navy blazer"
EARS = yes

## Voice
Kokoro bm_george, speed 0.95 (a calm British presenter). Alternatives to try by ear: bm_fable, am_michael.

## Pose pack (assets/characters/sterling/)
Master reference: front, waist-up, mouth closed, plain background, made with CHARACTER + STYLE + SEED.
Presenter poses (all facing the camera): neutral, pointing, shrug, shocked, thinking, serious, laughing.
Each pose: mouths closed / slight / wide / O / E / M-B-P (closed may reuse the base) + blink, made by edit and
pasted back with the feathered mouth/eye mask (as in the benchmark).
Sets: "studio" (a cosy finance studio: a wooden desk, warm lamp, bookshelf, a big wall screen behind him) and
"stage" (a dark stage, one spotlight, a large screen).
