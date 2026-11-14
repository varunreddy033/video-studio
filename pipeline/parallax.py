"""
parallax.py  -  2.5D camera moves for stills (presenter plan, build step 5).

Depth Anything V2 **Small** (Apache-2.0; never Base/Large, which are non-commercial) estimates a depth map per image
(cached next to the image). The camera then moves through the picture with near things moving more than far things,
so a still feels like a real camera move instead of a flat zoom. Runs on the CPU (small model, ~1 s per image) so it
never fights the image model for the GPU.
"""

import hashlib
import math
import threading
from pathlib import Path

import numpy as np
from PIL import Image

from . import config as C
from .visuals import enc_args
from .util import log, run

DEPTH_MODEL = "depth-anything/Depth-Anything-V2-Small-hf"     # Apache-2.0 (Small only)
_pipe = None
_lock = threading.Lock()


def _depth_pipe():
    global _pipe
    if _pipe is None:
        from transformers import pipeline
        _pipe = pipeline("depth-estimation", model=DEPTH_MODEL, device="cpu")
    return _pipe


def depth_map(img_path: Path) -> np.ndarray:
    """0..1 float map, 1 = nearest. Cached as <image>.depth.npy (keyed by the image's content)."""
    key = hashlib.sha1(Path(img_path).read_bytes()).hexdigest()[:12]
    cache = C.SHARED_IMAGE_CACHE / "depth" / f"{key}.npy"
    if cache.exists():
        return np.load(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        out = _depth_pipe()(Image.open(img_path).convert("RGB"))
    d = np.asarray(out["predicted_depth"].squeeze().float().cpu().numpy() if hasattr(out["predicted_depth"], "cpu")
                   else out["depth"], dtype=np.float32)
    lo, hi = np.percentile(d, [2, 98])
    d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)       # Depth Anything outputs relative inverse depth: high = near
    np.save(cache, d)
    return d


MOVES = [  # (start zoom, end zoom, x pan fraction of width, y pan fraction of height)
    (1.00, 1.07, 0.00, 0.00),    # push in
    (1.04, 1.04, -0.025, 0.00),  # truck right (near layer slides more)
    (1.07, 1.00, 0.00, 0.00),    # pull out
    (1.04, 1.04, 0.025, 0.00),   # truck left
    (1.02, 1.07, -0.015, -0.01), # push in + drift
    (1.04, 1.04, 0.00, 0.02),    # crane down
]


def parallax_clip(img_path: Path, dur: float, idx: int, W: int, H: int, out: Path, job_dir: Path, mode: str):
    import cv2
    import subprocess
    src = Image.open(img_path).convert("RGB")
    over = 1.10                                     # overscan so edges never show
    sw, sh = int(W * over), int(H * over)
    s = max(sw / src.width, sh / src.height)
    src = src.resize((int(src.width * s + 0.5), int(src.height * s + 0.5)), Image.LANCZOS)
    x0, y0 = (src.width - sw) // 2, (src.height - sh) // 2
    src = np.asarray(src.crop((x0, y0, x0 + sw, y0 + sh)))
    d = depth_map(img_path)
    d = cv2.resize(d, (sw, sh))
    d = cv2.GaussianBlur(d, (0, 0), sigmaX=max(2, W / 240))      # soft depth -> no tearing at edges
    z0, z1, px, py = MOVES[idx % len(MOVES)]
    n = int(math.ceil(dur * C.FPS))
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    cxo, cyo = W / 2, H / 2
    near = cv2.resize(d, (W, H)).astype(np.float32)            # depth at output pixels (approximation)
    weight = 0.35 + 0.65 * near                                # far moves 35%, near moves 100%
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(C.FPS), "-i", "-",
           "-t", f"{dur:.3f}", "-vf", "format=yuv420p", *enc_args(mode), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for f in range(n):
            t = f / max(1, n - 1)
            e = 0.5 - 0.5 * math.cos(math.pi * t)                # ease in-out
            z = z0 + (z1 - z0) * e
            zeff = 1 + (z - 1) * weight
            dx = px * W * (e - 0.5) * 2 * weight
            dy = py * H * (e - 0.5) * 2 * weight
            mx = (gx - cxo) / zeff + cxo + (sw - W) / 2 - dx
            my = (gy - cyo) / zeff + cyo + (sh - H) / 2 - dy
            frame = cv2.remap(src, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            p.stdin.write(frame.tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode(errors="replace")
    if p.wait() != 0:
        log(job_dir, "FAILED: parallax clip\n  " + "\n  ".join(err.strip().splitlines()[-6:]))
        from .util import PipelineError
        raise PipelineError("parallax clip failed")


# ------------------------------------------------------------------------------------- camera: (header, opt-in)
CAMERA_AUTO = ["dolly", "truck", "orbit", "vertigo", "pull", "tilt", "focus", "handheld"]


def camera_move(camera: str, idx: int) -> str:
    """camera: header -> the move of shot idx (auto / a comma list cycle per shot)."""
    names = [x.strip() for x in str(camera).split(",") if x.strip()]
    if names in (["auto"], []):
        names = CAMERA_AUTO
    return names[idx % len(names)]


def camera_clip(img_path: Path, dur: float, idx: int, W: int, H: int, out: Path, job_dir: Path, mode: str, move: str):
    """3D-feel camera moves on one still from its depth map (Depth Anything V2 Small): near and far layers move by
    different amounts, orbit/tilt move them in opposite directions around the subject's depth, vertigo keeps the
    subject's size while the background falls away, focus racks the focus from the background to the subject."""
    import cv2
    import subprocess
    src = Image.open(img_path).convert("RGB")
    over = 1.14
    sw, sh = int(W * over), int(H * over)
    s = max(sw / src.width, sh / src.height)
    src = src.resize((int(src.width * s + 0.5), int(src.height * s + 0.5)), Image.LANCZOS)
    x0, y0 = (src.width - sw) // 2, (src.height - sh) // 2
    src = np.asarray(src.crop((x0, y0, x0 + sw, y0 + sh)))
    d = cv2.resize(depth_map(img_path), (sw, sh))
    d = cv2.GaussianBlur(d, (0, 0), sigmaX=max(2, W / 240))
    near = cv2.resize(d, (W, H)).astype(np.float32)
    focal = float(np.median(near[H // 4: 3 * H // 4, W // 4: 3 * W // 4]))     # the subject's depth (centre)
    rel = near - focal                                                          # >0 in front of the subject
    blur = cv2.GaussianBlur(src, (0, 0), sigmaX=max(3, W / 200)) if move == "focus" else None
    n = int(math.ceil(dur * C.FPS))
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    cx, cy = W / 2, H / 2
    ox, oy = (sw - W) / 2, (sh - H) / 2
    rng = np.random.default_rng(idx + 7)
    ph = rng.uniform(0, 6.28, 4)
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(C.FPS), "-i", "-",
           "-t", f"{dur:.3f}", "-vf", "format=yuv420p", *enc_args(mode), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for f in range(n):
            t = f / max(1, n - 1)
            e = 0.5 - 0.5 * math.cos(math.pi * t)
            zeff, dx, dy = np.float32(1.0), np.float32(0.0), np.float32(0.0)
            if move == "dolly":
                zeff = 1 + (0.10 * e) * (0.15 + 0.85 * near)
            elif move == "pull":
                zeff = 1 + (0.10 * (1 - e)) * (0.15 + 0.85 * near)
            elif move == "truck":
                zeff = np.float32(1.02)
                dx = 0.05 * W * (e - 0.5) * (0.2 + 0.8 * near)
            elif move == "orbit":
                zeff = 1.03 + 0.02 * e * near
                dx = 0.06 * W * (e - 0.5) * rel
            elif move == "tilt":
                zeff = np.float32(1.03)
                dy = 0.06 * H * (e - 0.5) * rel
            elif move == "vertigo":
                zeff = 1 + (0.13 * (1 - e)) * (1 - near) + 0.04 * e * near
            elif move == "focus":
                zeff = 1 + 0.04 * e * (0.3 + 0.7 * near)
            elif move == "handheld":
                zeff = 1.03 + 0.03 * t * (0.3 + 0.7 * near)
                sec = f / C.FPS
                dx = (0.004 * W * (math.sin(1.3 * sec + ph[0]) + 0.5 * math.sin(2.9 * sec + ph[1]))) * (0.5 + 0.5 * near)
                dy = (0.005 * H * (math.sin(1.1 * sec + ph[2]) + 0.5 * math.sin(2.3 * sec + ph[3]))) * (0.5 + 0.5 * near)
            mx = (gx - cx) / zeff + cx + ox - dx
            my = (gy - cy) / zeff + cy + oy - dy
            frame = cv2.remap(src, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if blur is not None:              # focus plane travels from the background (depth 0) to the subject
                f0 = 1.0 if focal < 0.5 else 0.0     # start on the depth farthest from the subject
                fz = f0 + (focal - f0) * min(1.0, e * 1.6)
                a = np.clip(np.abs(near - fz) * 3.0, 0, 1)[..., None]
                soft = cv2.remap(blur, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                frame = (frame * (1 - a) + soft * a).astype(np.uint8)
            p.stdin.write(np.ascontiguousarray(frame).tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode(errors="replace")
    if p.wait() != 0:
        log(job_dir, "FAILED: camera clip\n  " + "\n  ".join(err.strip().splitlines()[-6:]))
        from .util import PipelineError
        raise PipelineError("camera clip failed")
