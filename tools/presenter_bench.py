"""
Presenter plan, build step 1: benchmark only (not part of the pipeline).
Can FLUX.2 klein 4B (mflux 0.24) keep one character consistent across scenes, and edit just the mouth?

  bin/python tools/presenter_bench.py base          4 candidates of the character (txt2img)
  bin/python tools/presenter_bench.py refs  <ref>   10 scenes, conditioned on the reference image (edit model)
  bin/python tools/presenter_bench.py seed          10 scenes, fallback: fixed seed + detailed prompt (txt2img)
  bin/python tools/presenter_bench.py mouth <ref>   6 mouth shapes + eyes closed, edited from the reference
"""

import json
import sys
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output" / "presenter_bench"
MODEL = "Runpod/FLUX.2-klein-4B-mflux-4bit"
BASE = "flux2-klein-4b"

CHARACTER = ("a cartoon cat presenter with soft grey-and-white fur, big round amber eyes, a small pink nose, "
             "wearing a tailored navy blue blazer over a crisp white shirt, a slim burgundy tie")
STYLE = "stylised 3D animated film look, soft studio lighting, clean shapes, vibrant but natural colours"

SCENES = [
    "sitting at a trading desk with several monitors showing red falling charts, looking worried",
    "standing in a long data center aisle with blue server lights, pointing at the racks",
    "walking down a rainy city street at night holding an umbrella",
    "standing in front of a giant soap bubble floating over a city skyline at dusk",
    "reading a thick report at a wooden desk with a coffee mug, desk lamp on",
    "shrugging with both paws up in a bright modern office",
    "standing on a small stage in front of a large blank screen, presenting",
    "looking shocked, eyes wide, in a dim boardroom with empty chairs",
    "sitting on a park bench in autumn, thinking, chin on paw",
    "holding a single gold coin up close to the camera, curious expression",
]
MOUTHS = {
    "closed": "the mouth closed, lips relaxed",
    "slight": "the mouth slightly open as if starting to speak",
    "wide": "the mouth wide open as if saying 'ah'",
    "o": "the mouth in a small round 'O' shape",
    "e": "the mouth stretched wide showing teeth as if saying 'ee'",
    "mbp": "the lips pressed firmly together as if saying 'm'",
    "blink": "the eyes fully closed, mouth unchanged",
}


def clear():
    import mlx.core as mx
    (getattr(mx, "clear_cache", None) or mx.metal.clear_cache)()


def txt2img_model():
    from mflux.models.common.config.model_config import AVAILABLE_MODELS
    from mflux.models.common.resolution.config_resolution import ConfigResolution
    from mflux.models.flux2.variants import Flux2Klein
    fam = tuple(k for k in AVAILABLE_MODELS if k.startswith("flux2-") and k != BASE)
    cfg = ConfigResolution.resolve_restricted(MODEL, BASE, model_path=MODEL, extra_keys=fam, base_model=BASE)
    return Flux2Klein(model_config=cfg, quantize=None, model_path=MODEL)


def edit_model():
    from mflux.models.common.config.model_config import AVAILABLE_MODELS
    from mflux.models.common.resolution.config_resolution import ConfigResolution
    from mflux.models.flux2.variants.edit.flux2_klein_edit import Flux2KleinEdit
    fam = tuple(k for k in AVAILABLE_MODELS if k.startswith("flux2-") and k != BASE)
    cfg = ConfigResolution.resolve_restricted(MODEL, BASE, model_path=MODEL, extra_keys=fam, base_model=BASE)
    return Flux2KleinEdit(model_config=cfg, quantize=None, model_path=MODEL)


def gen(model, out: Path, prompt, w, h, seed, refs=None, log=None):
    t = time.time()
    kw = dict(seed=seed, prompt=prompt, width=w, height=h, guidance=1.0, num_inference_steps=4,
              scheduler="flow_match_euler_discrete")
    if refs is not None:
        kw["image_paths"] = [str(r) for r in refs]
    img = model.generate_image(**kw)
    img.save(path=str(out), export_json_metadata=False)
    del img
    clear()
    secs = round(time.time() - t, 1)
    print(f"  {out.name}: {secs}s", flush=True)
    if log is not None:
        log.append({"file": out.name, "secs": secs, "prompt": prompt})


def main():
    mode = sys.argv[1]
    d = OUT / mode
    d.mkdir(parents=True, exist_ok=True)
    log = []
    if mode == "base":
        m = txt2img_model()
        for i in range(4):
            gen(m, d / f"cand_{i}.png", f"{CHARACTER}, front view, waist-up, facing the camera, neutral friendly "
                f"expression, mouth closed, plain light grey background, {STYLE}", 1024, 1024, 1000 + i, log=log)
    elif mode == "refs":
        ref = Path(sys.argv[2])
        m = edit_model()
        for i, sc in enumerate(SCENES):
            gen(m, d / f"scene_{i:02d}.png", f"The same cat character from the reference image, with the same face, "
                f"fur colours and navy blazer outfit, {sc}. {STYLE}, wide 16:9 shot", 1280, 720, 2000 + i,
                refs=[ref], log=log)
    elif mode == "seed":
        m = txt2img_model()
        for i, sc in enumerate(SCENES):
            gen(m, d / f"scene_{i:02d}.png", f"{CHARACTER}, {sc}. {STYLE}, wide 16:9 shot", 1280, 720, 1000, log=log)
    elif mode == "mouth":
        ref = Path(sys.argv[2])
        from PIL import Image
        w, h = Image.open(ref).size
        m = edit_model()
        for name, change in MOUTHS.items():
            gen(m, d / f"mouth_{name}.png", f"Edit this image: change only the cat's face so it has {change}. Keep "
                f"everything else exactly the same: same pose, same fur, same blazer, same background, same lighting, "
                f"same framing.", w, h, 3000, refs=[ref], log=log)
    (d / "timings.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print("done", mode, "avg", round(sum(x["secs"] for x in log) / max(1, len(log)), 1), "s")


if __name__ == "__main__":
    main()
