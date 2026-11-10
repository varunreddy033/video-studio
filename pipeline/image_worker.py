"""
image_worker.py  -  keeps FLUX.2 klein 4B loaded and makes images on request (saves ~10 s per image).

Started by pipeline/visuals.py as a child process for the length of one render (or one character-pack build),
then stopped so its ~5 GB of memory goes back to the Mac. Protocol: one JSON object per line on stdin
  {"prompt": "...", "width": 1280, "height": 720, "steps": 4, "seed": 123, "out": "/path/img.png",
   "refs": ["/path/reference.png"]}          <- optional: reference image(s) -> uses the FLUX.2 edit model
and one JSON line per request on stdout: {"ok": true, "secs": 9.8} or {"ok": false, "error": "..."}.
Only one model is in memory at a time; switching between plain and reference mode reloads (about 1 s).
Usage: bin/python -m pipeline.image_worker <model repo or path> <base model name>
"""

import json
import sys
import time


def main():
    model_name, base_model = sys.argv[1], sys.argv[2]
    real_stdout = sys.stdout
    sys.stdout = sys.stderr          # anything mflux prints must not corrupt the protocol
    import mlx.core as mx
    from mflux.models.common.config.model_config import AVAILABLE_MODELS
    from mflux.models.common.resolution.config_resolution import ConfigResolution

    family = tuple(k for k in AVAILABLE_MODELS if k.startswith("flux2-") and k != base_model)
    config = ConfigResolution.resolve_restricted(model_name, base_model, model_path=model_name,
                                                 extra_keys=family, base_model=base_model)
    # MLX keeps freed GPU buffers for reuse; on a 16 GB Mac that pile-up pushes everything into swap.
    _set_cache_limit = getattr(mx, "set_cache_limit", None) or mx.metal.set_cache_limit
    _clear_cache = getattr(mx, "clear_cache", None) or mx.metal.clear_cache
    _set_cache_limit(512 * 1024 * 1024)
    loaded = {"kind": None, "model": None}

    def model_for(kind):
        if loaded["kind"] != kind:
            loaded["model"] = None
            _clear_cache()
            if kind == "edit":
                from mflux.models.flux2.variants.edit.flux2_klein_edit import Flux2KleinEdit
                loaded["model"] = Flux2KleinEdit(model_config=config, quantize=None, model_path=model_name)
            else:
                from mflux.models.flux2.variants import Flux2Klein
                loaded["model"] = Flux2Klein(model_config=config, quantize=None, model_path=model_name)
            loaded["kind"] = kind
        return loaded["model"]

    t0 = time.time()
    model_for("plain")
    print(json.dumps({"ready": True, "load_secs": round(time.time() - t0, 1)}), file=real_stdout, flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            refs = req.get("refs") or []
            t = time.time()
            kw = dict(seed=int(req["seed"]), prompt=req["prompt"], width=int(req["width"]), height=int(req["height"]),
                      guidance=1.0, num_inference_steps=int(req.get("steps", 4)), scheduler="flow_match_euler_discrete")
            if refs:
                kw["image_paths"] = refs
            image = model_for("edit" if refs else "plain").generate_image(**kw)
            image.save(path=req["out"], export_json_metadata=False)
            del image
            _clear_cache()
            reply = {"ok": True, "secs": round(time.time() - t, 1),
                     "peak_gb": round(mx.get_peak_memory() / 1e9, 2) if hasattr(mx, "get_peak_memory") else None}
        except Exception as e:  # report and keep serving
            reply = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        print(json.dumps(reply), file=real_stdout, flush=True)


if __name__ == "__main__":
    main()
