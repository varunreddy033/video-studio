"""
visuals.py  -  one video clip (no audio, exact length) per shot.

  ai      FLUX.2 klein 4B on the Mac GPU (kept loaded by pipeline/image_worker.py) -> slow camera move
  stock   same as ai, styled as a real-world documentary photo (no stock video service is used)
          (draft mode: a labelled placeholder instead, so drafts take a minute, not ten)
  card / number / quote / chart   drawn with Pillow / matplotlib, animated in, then held
"""

import json
import math
import subprocess
import textwrap
import threading
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config as C
from .util import PipelineError, h, log, media_duration, run

_mflux_lock = threading.Lock()   # 16 GB RAM: never two image models at once


# ------------------------------------------------------------------ encoding ---
def enc_args(mode: str):
    """Identical settings for every clip so they can be joined without re-encoding.
    The encoder is auto-detected (pipeline/encoder.py): videotoolbox on the Mac, nvenc on NVIDIA, else libx264."""
    from . import encoder
    rate = "16M" if mode == "final" else "4M"   # intermediates; the final mux re-encodes once
    return [*encoder.args(rate), "-pix_fmt", "yuv420p", "-r", str(C.FPS), "-video_track_timescale", "90000", "-an"]


# --------------------------------------------------------------------- fonts ---
_fonts = {}


def font(kind: str, size: int):
    key = (kind, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(C.FONTS_DIR / C.FONT_FILES[kind]), size)
    return _fonts[key]


# Shorts: graphics are drawn inside a safe box (clear of the Shorts buttons) on the full-size background.
# Set per render thread by make_shot; background() then returns the matching piece of the full background.
_safe = threading.local()


def background(W: int, H: int) -> Image.Image:
    """Dark vertical gradient with a soft vignette."""
    full = getattr(_safe, "full", None)
    if full and (W, H) == full[2:]:
        return _background(*full[:2]).crop((0, 0, W, H))
    return _background(W, H)


def _background(W: int, H: int) -> Image.Image:
    top, bot = C.BG_TOP, C.BG_BOTTOM
    grad = Image.new("RGB", (1, 256))
    for y in range(256):
        t = y / 255
        grad.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    img = grad.resize((W, H))
    vign = Image.radial_gradient("L").resize((W, H))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(dark, img, vign.point(lambda v: int(v * 0.55)))


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, kind, max_w, max_h, start, min_size=18, spacing=1.12):
    size = start
    while size > min_size:
        f = font(kind, size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) * size * spacing <= max_h and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines, size
        size = int(size * 0.92)
    f = font(kind, min_size)
    return f, wrap(draw, text, f, max_w), min_size


def ease(t):  # ease-out cubic
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------- frame piping ---
def frames_to_clip(frames, n_anim: int, dur: float, W: int, H: int, out: Path, job_dir: Path, mode: str, what: str):
    """frames: generator of PIL images (n_anim of them); the last one is held until dur."""
    hold = max(0.0, dur - n_anim / C.FPS)
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(C.FPS), "-i", "-",
           "-vf", f"tpad=stop_mode=clone:stop_duration={hold:.3f},format=yuv420p", "-t", f"{dur:.3f}",
           *enc_args(mode), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for img in frames:
            p.stdin.write(img.convert("RGB").tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode(errors="replace")
    if p.wait() != 0:
        log(job_dir, f"FAILED: {what}\n  " + "\n  ".join(err.strip().splitlines()[-8:]))
        raise PipelineError(f"{what} failed: {err.strip().splitlines()[-1] if err.strip() else 'ffmpeg error'}")


# ---------------------------------------------------------------- graphics ---
def card_frames(shot, W, H):
    base = background(W, H)
    d0 = ImageDraw.Draw(base)
    pad = int(W * 0.1)
    f, lines, size = fit_text(d0, shot["text"].upper(), "heavy", W - 2 * pad, H * 0.42, int(H * 0.16))
    sub_f = font("medium", max(16, int(H * 0.045)))
    block_h = len(lines) * size * 1.08 + (size * 0.5 + sub_f.size * 1.6 if shot.get("sub") else 0)
    y0 = (H - block_h) / 2
    n = int(C.FPS * 0.5)
    for i in range(n):
        t = ease((i + 1) / n)
        img = base.copy()
        d = ImageDraw.Draw(img)
        alpha_col = tuple(int(c * t) for c in C.TEXT)
        y = y0 + (1 - t) * H * 0.04
        for ln in lines:
            d.text((W / 2, y), ln, font=f, fill=alpha_col, anchor="ma")
            y += size * 1.08
        bar_w = int(W * 0.12 * t)
        d.rectangle([W / 2 - bar_w, y + size * 0.15, W / 2 + bar_w, y + size * 0.15 + max(3, H * 0.008)], fill=C.ACCENT)
        if shot.get("sub"):
            d.text((W / 2, y + size * 0.5), shot["sub"], font=sub_f,
                   fill=tuple(int(c * t) for c in C.MUTED), anchor="ma")
        yield img
    return


def number_frames(shot, W, H, dur):
    base = background(W, H)
    val, dec = shot["value"], shot["decimals"]
    big = font("heavy", int(H * 0.26))
    lab = font("medium", max(16, int(H * 0.05)))
    n = int(C.FPS * min(1.8, max(0.6, dur * 0.6)))
    d0 = ImageDraw.Draw(base)
    label_lines = wrap(d0, shot.get("label", ""), lab, W * 0.8)
    for i in range(n):
        t = ease((i + 1) / n)
        v = val * t
        txt = f"{shot['prefix']}{v:,.{dec}f}{shot['suffix']}"
        img = base.copy()
        d = ImageDraw.Draw(img)
        d.text((W / 2, H * 0.45), txt, font=big, fill=C.ACCENT, anchor="mm")
        y = H * 0.45 + big.size * 0.62
        for ln in label_lines:
            d.text((W / 2, y), ln, font=lab, fill=tuple(int(c * min(1, t * 1.5)) for c in C.TEXT), anchor="ma")
            y += lab.size * 1.25
        yield img


def quote_frames(shot, W, H):
    base = background(W, H)
    d0 = ImageDraw.Draw(base)
    pad = int(W * 0.13)
    f, lines, size = fit_text(d0, shot["text"], "italic", W - 2 * pad, H * 0.5, int(H * 0.085), spacing=1.3)
    mark = font("heavy", int(H * 0.3))
    by_f = font("bold", max(16, int(H * 0.042)))
    block_h = len(lines) * size * 1.3
    y0 = (H - block_h) / 2
    n = int(C.FPS * 0.6)
    for i in range(n):
        t = ease((i + 1) / n)
        img = base.copy()
        d = ImageDraw.Draw(img)
        d.text((pad - size * 0.2, y0 - size * 0.35), "“", font=mark,
               fill=tuple(int(c * t) for c in C.ACCENT), anchor="ls")
        y = y0
        for ln in lines:
            d.text((pad, y), ln, font=f, fill=tuple(int(c * t) for c in C.TEXT))
            y += size * 1.3
        if shot.get("by"):
            d.text((pad, y + size * 0.4), "— " + shot["by"], font=by_f, fill=tuple(int(c * t) for c in C.MUTED))
        yield img


def chart_frames(shot, W, H):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_manager.fontManager.addfont(str(C.FONTS_DIR / C.FONT_FILES["bold"]))
    plt.rcParams["font.family"] = "Barlow"
    plt.rcParams["font.weight"] = "bold"
    labels = [k for k, _ in shot["data"]]
    vals = [v for _, v in shot["data"]]
    vmax = max(vals) if max(vals) > 0 else 1
    acc = tuple(c / 255 for c in C.ACCENT)
    txt = tuple(c / 255 for c in C.TEXT)
    mut = tuple(c / 255 for c in C.MUTED)
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    fig.patch.set_alpha(0)
    bottom = 0.30 if H > W else 0.24      # keep the x labels above the caption zone
    ax = fig.add_axes([0.1, bottom, 0.84, 0.80 - bottom])
    base = background(W, H)
    # title: wrapped and shrunk to fit (narrow vertical canvases), at most 2 lines
    title_f, title_lines, title_size = fit_text(ImageDraw.Draw(base), shot["title"], "heavy", W * 0.9,
                                                H * (0.12 if H > W else 0.09), int(H * (0.05 if H > W else 0.075)))
    unit = shot.get("unit", "")
    # labels must fit under their bar: shrink for long labels / many bars / narrow canvases (fs is in points)
    longest = max(len(str(k)) for k in labels)
    fs = max(8, min(H * 0.028, (0.84 * W / len(labels)) / (longest * 0.52) * 0.72))
    vfs = min(fs * 1.3, H * 0.034)       # the value above a bar / point reads a bit bigger than the label
    n = int(C.FPS * 1.3)
    for i in range(n):
        t = ease((i + 1) / n)
        ax.clear()
        ax.set_facecolor((0, 0, 0, 0))
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(mut)
        ax.tick_params(colors=txt, labelsize=fs, length=0)
        ax.set_yticks([])
        ax.set_ylim(0, vmax * 1.22)
        if shot["chart"] == "bar":
            bars = ax.bar(labels, [v * t for v in vals], color=acc, width=0.62)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + vmax * 0.03,
                        f"{v * t:,.{0 if float(v).is_integer() else 1}f}{unit}", ha="center", color=txt, fontsize=vfs)
        else:
            k = max(2, math.ceil(len(vals) * t))
            xs = list(range(len(vals)))
            ax.plot(xs[:k], vals[:k], color=acc, linewidth=max(2, H / 180))
            ax.scatter(xs[:k], vals[:k], color=acc, s=(H / 40) ** 2 / 4, zorder=3)
            ax.set_xticks(xs, labels)
            ax.set_xlim(-0.45, len(vals) - 0.55)     # room so the end labels aren't cut off
            ax.text(xs[k - 1], vals[k - 1] + vmax * 0.05, f"{vals[k - 1]:,.{0 if float(vals[k-1]).is_integer() else 1}f}{unit}",
                    ha="center", color=txt, fontsize=vfs)
        fig.canvas.draw()
        layer = Image.frombuffer("RGBA", fig.canvas.get_width_height(), bytes(fig.canvas.buffer_rgba()))
        img = base.copy()
        img.paste(layer, (0, 0), layer)
        d = ImageDraw.Draw(img)
        ty = H * 0.08
        for ln in title_lines:
            d.text((W / 2, ty), ln, font=title_f, fill=C.TEXT, anchor="ma")
            ty += title_size * 1.08
        yield img
    plt.close(fig)


def graphic_clip(shot, dur, W, H, out, job_dir, mode, safe=None):
    """safe = {"bottom": 0.2, "right": 0.12} (Shorts): the graphic is laid out in the box above/left of that."""
    if safe:
        sw = int(W * (1 - safe.get("right", 0))) // 2 * 2
        sh = int(H * (1 - safe.get("bottom", 0))) // 2 * 2
        _safe.full = (W, H, sw, sh)
        try:
            base = _background(W, H)
            inner = _graphic_frames(shot, dur, sw, sh)
            n, frames = inner

            def framed():
                for fr in frames:
                    img = base.copy()
                    img.paste(fr, (0, 0))
                    yield img
            frames_to_clip(framed(), n, dur, W, H, out, job_dir, mode, f"{shot['type']} graphic")
        finally:
            _safe.full = None
        return
    n, frames = _graphic_frames(shot, dur, W, H)
    frames_to_clip(frames, n, dur, W, H, out, job_dir, mode, f"{shot['type']} graphic")


def _graphic_frames(shot, dur, W, H):
    if shot["type"] == "card":
        frames, n = card_frames(shot, W, H), int(C.FPS * 0.5)
    elif shot["type"] == "number":
        n = int(C.FPS * min(1.8, max(0.6, dur * 0.6)))
        frames = number_frames(shot, W, H, dur)
    elif shot["type"] == "quote":
        frames, n = quote_frames(shot, W, H), int(C.FPS * 0.6)
    else:
        frames, n = chart_frames(shot, W, H), int(C.FPS * 1.3)
    return n, frames


# ------------------------------------------------------------------ AI images ---
class _ImageWorker:
    """FLUX.2 kept loaded in a child process (pipeline/image_worker.py) for one render."""

    def __init__(self):
        self.p = None

    def _start(self, job_dir: Path):
        import sys
        err = open(job_dir / "image_worker.log", "a", encoding="utf-8")
        self.p = subprocess.Popen([sys.executable, "-m", "pipeline.image_worker", C.LOCAL_IMAGE_MODEL,
                                   C.LOCAL_IMAGE_BASE], cwd=str(C.BASE_DIR), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=err, text=True)
        ready = self.p.stdout.readline()
        if not ready.strip().startswith('{"ready"'):
            self.stop()
            raise PipelineError("image worker did not start (see image_worker.log)")

    def generate(self, prompt, w, h_, seed, out: Path, job_dir: Path, refs=None, steps=None):
        if self.p is None or self.p.poll() is not None:
            self._start(job_dir)
        req = {"prompt": prompt, "width": w, "height": h_, "steps": steps or C.LOCAL_IMAGE_STEPS, "seed": seed,
               "out": str(out)}
        if refs:
            req["refs"] = [str(r) for r in refs]
        self.p.stdin.write(json.dumps(req) + "\n")
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            self.stop()
            raise PipelineError("image worker stopped unexpectedly (see image_worker.log)")
        reply = json.loads(line)
        if not reply.get("ok"):
            raise PipelineError(f"image worker: {reply.get('error')}")
        return reply

    def stop(self):
        if self.p is not None:
            try:
                self.p.stdin.close()
                self.p.wait(timeout=20)
            except Exception:
                self.p.kill()
            self.p = None


_worker = _ImageWorker()


def _file_hash(p) -> str:
    import hashlib as _hl
    return _hl.sha1(Path(p).read_bytes()).hexdigest()[:12]


def shared_image(prompt: str, w: int, h_: int, seed: int, log_dir: Path, refs=None, cooldown=None,
                 cached_only: bool = False) -> Path:
    """Generate (or reuse) one image in the SHARED cache (assets/cache/images), used by character packs and
    [act:] shots across all videos. refs = reference image paths (uses the FLUX.2 edit model, ~3x slower).
    After every NEW image the Mac rests for IMAGE_COOLDOWN seconds so the fanless Air doesn't throttle."""
    refs = [Path(r) for r in (refs or [])]
    key = h(prompt, w, h_, seed, C.LOCAL_IMAGE_MODEL, C.LOCAL_IMAGE_STEPS, *[_file_hash(r) for r in refs])
    out = C.SHARED_IMAGE_CACHE / f"{key}.png"
    if out.exists() and out.stat().st_size > 0:
        return out
    if cached_only:
        raise PipelineError(f"character image for '{prompt[:60]}' isn't in assets/cache/images")
    _need_image_model("this character image")
    C.SHARED_IMAGE_CACHE.mkdir(parents=True, exist_ok=True)
    with _mflux_lock:
        t0 = time.time()
        _worker.generate(prompt, w, h_, seed, out, log_dir, refs=refs)
        log(log_dir, f"  image {out.name} ({'ref' if refs else 'plain'}) in {time.time() - t0:.0f}s")
        time.sleep(C.IMAGE_COOLDOWN if cooldown is None else cooldown)
    if not out.exists():
        raise PipelineError("image generation finished but wrote no image")
    return out


PREVIEW_PROMPT = "an old stone harbour at dawn with fishing boats and gulls"
PREVIEW_SEED = 1000            # same seed for every style, so the previews differ only by style


def make_style_preview(style_id: str) -> Path:
    """assets/style_previews/<id>.jpg (720 px wide): the fixed test prompt in one art style, 1280x720.
    Uses the same image worker + lock as renders (never two image models at once) and frees it afterwards."""
    from . import presets
    _need_image_model("an art style preview")
    out = presets.preview_path(style_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".png")
    st = presets.load("art_styles", style_id)
    log_dir = C.BASE_DIR / "output"
    with _mflux_lock:
        t0 = time.time()
        try:
            _worker.generate(style_prompt(PREVIEW_PROMPT, style_id), 1280, 720, PREVIEW_SEED, tmp, log_dir,
                             steps=st["steps"])
        finally:
            _worker.stop()       # give the ~5 GB back right away
    if not tmp.exists():
        raise PipelineError("the image model finished but wrote no preview image")
    img = Image.open(tmp).convert("RGB")
    img.resize((720, round(img.height * 720 / img.width)), Image.LANCZOS).save(out, quality=88)
    tmp.unlink(missing_ok=True)
    log(log_dir, f"style preview {style_id} in {time.time() - t0:.0f}s")
    return out


def stop_image_worker():
    """Called at the end of every render so the model's ~5 GB goes back to the Mac."""
    with _mflux_lock:
        _worker.stop()


def _need_image_model(what: str):
    if not C.IMAGE_MODEL_AVAILABLE:
        raise PipelineError(f"{what} needs a NEW AI image, and the local image model (mflux/MLX) only runs on an "
                            f"Apple Silicon Mac. Render this one on the Mac, or use shots that are already cached "
                            f"(clip Shorts, [talk:] + graphics).")


def style_prompt(prompt: str, style_id=None, stock: bool = False) -> str:
    """The full image prompt for an [ai:] / [stock:] shot or an AI thumbnail in one art style
    (presets/art_styles/<id>.json): "prefix, prompt, stock_suffix (stock only), suffix" (empty parts left out).
    style None = doc_photo, whose suffix is config.IMAGE_STYLE (.env can still change it). doc_photo gives
    byte-for-byte the prompts made before art styles existed, so every cached image is still found."""
    from . import presets
    st = presets.load("art_styles", style_id or presets.DEFAULTS["art_styles"])
    suffix = C.IMAGE_STYLE if st["id"] == "doc_photo" else st["suffix"]
    parts = [st["prefix"], prompt, st["stock_suffix"] if stock else "", suffix]
    return ", ".join(p for p in parts if p)


def ai_cache_path(prompt: str, W: int, H: int, job_dir: Path, seed_extra: str = "", style=None,
                  stock: bool = False):
    """(cached image path, full prompt, generation size, steps) of an AI image; the file may not exist yet.
    The cache key is the same as before art styles: hash of (full prompt, size, model, steps, seed_extra)."""
    from . import presets
    gw, gh = (1280, 720) if W >= H else (720, 1280)
    full = style_prompt(prompt, style, stock)
    steps = presets.load("art_styles", style or presets.DEFAULTS["art_styles"])["steps"] or C.LOCAL_IMAGE_STEPS
    key = h(full, gw, gh, C.LOCAL_IMAGE_MODEL, steps, seed_extra)
    return job_dir / "cache" / f"ai_{key}.png", full, (gw, gh), steps


def ai_image(prompt: str, W: int, H: int, job_dir: Path, seed_extra: str = "", cached_only: bool = False,
             style=None, stock: bool = False) -> Path:
    """Generate (or reuse) an image. ~12-25 s on the M5 Air (model stays loaded during a render).
    prompt = the script's own words; style = art style preset id (None = doc_photo); stock = a [stock:] shot.
    cached_only=True: return the cached file or raise (clip Shorts never make new images)."""
    out, full, (gw, gh), steps = ai_cache_path(prompt, W, H, job_dir, seed_extra, style, stock)
    key = out.stem[3:]
    if out.exists() and out.stat().st_size > 0:
        return out
    if cached_only:
        raise PipelineError(f"AI image for '{prompt[:60]}' isn't in {job_dir.name}/cache (was the final made?)")
    _need_image_model("this [ai:]/[stock:] shot")
    out.parent.mkdir(exist_ok=True)
    seed = int(key[:7], 16)
    with _mflux_lock:
        t0 = time.time()
        try:
            _worker.generate(full, gw, gh, seed, out, job_dir, steps=steps)
        except Exception as e:   # fall back to one CLI call (slower, but independent)
            log(job_dir, f"  image worker failed ({e}); using the mflux command instead")
            _worker.stop()
            run([C.MFLUX_BIN, "--model", C.LOCAL_IMAGE_MODEL, "--base-model", C.LOCAL_IMAGE_BASE,
                 "--width", gw, "--height", gh, "--steps", steps, "--seed", seed,
                 "--prompt", full, "--output", out], job_dir, "AI image")
        log(job_dir, f"  AI image {out.name} in {time.time() - t0:.0f}s")
    if not out.exists():
        raise PipelineError("image generation finished but wrote no image")
    return out


def placeholder_image(label: str, text: str, W: int, H: int, job_dir: Path, note: str = "") -> Path:
    """Draft stand-in for an image: label, the prompt, and an optional note (the art style) under it."""
    out = job_dir / "cache" / f"ph_{h(label, text, W, H, note) if note else h(label, text, W, H)}.png"
    if out.exists():
        return out
    out.parent.mkdir(exist_ok=True)
    img = background(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([W * 0.04, H * 0.06, W * 0.96, H * 0.94], outline=C.MUTED, width=max(2, H // 270))
    d.text((W / 2, H * 0.2), label, font=font("heavy", int(H * 0.07)), fill=C.ACCENT, anchor="ma")
    f, lines, size = fit_text(d, text, "medium", W * 0.8, H * 0.5, int(H * 0.05))
    y = H * 0.36
    for ln in lines:
        d.text((W / 2, y), ln, font=f, fill=C.TEXT, anchor="ma")
        y += size * 1.25
    if note:
        d.text((W / 2, y + H * 0.03), note, font=font("medium", int(H * 0.04)), fill=C.MUTED, anchor="ma")
    img.save(out)
    return out


def ken_burns(img: Path, dur: float, idx: int, W: int, H: int, out: Path, job_dir: Path, mode: str):
    frames = int(math.ceil(dur * C.FPS)) + 1
    n = frames
    moves = [
        (f"1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),                       # push in
        ("1.1", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),                              # pan right
        (f"1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),                    # pull out
        ("1.12", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*(1-on/{n})"),                         # tilt up
        (f"1+0.1*on/{n}", f"(iw-iw/zoom)*on/{n}", f"(ih-ih/zoom)*on/{n}"),                # drift down-right + push
        ("1.1", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),                          # pan left
        ("1.12", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*on/{n}"),                             # tilt down
        (f"1.1-0.1*on/{n}", f"(iw-iw/zoom)*(1-on/{n})", f"(ih-ih/zoom)*(1-on/{n})"),      # drift up-left + pull
    ]
    z, x, y = moves[idx % len(moves)]
    up = 2 if mode == "final" else 1.5   # upscale first so the slow move doesn't jitter
    vf = (f"scale={int(W * up)}:{int(H * up)}:force_original_aspect_ratio=increase,crop={int(W * up)}:{int(H * up)},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={C.FPS},setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf, "-frames:v", frames, "-t", f"{dur:.3f}",
         *enc_args(mode), out], job_dir, "zoom/pan clip")


# ----------------------------------------------------------------- one shot ---
FRAMING_TEXT = {"wide": "wide shot showing the whole scene, the {noun} small in the frame",
                "medium": "medium shot from the waist up", "close": "close-up shot"}


def act_image(shot, char: dict, W: int, H: int, job_dir: Path, cached_only: bool = False) -> Path:
    """[act:] = the character in a scene: fixed SEED + CHARACTER + STYLE (10/10 consistent in the step-1 test).
    '| ref' on the tag also conditions on the master reference image (for a shot that drifts, ~3x slower)."""
    gw, gh = (1280, 720) if W >= H else (720, 1280)
    noun = (char.get("body") or {}).get("noun", "character")     # Sterling: "cat" (same prompts as before)
    framing = FRAMING_TEXT[shot["framing"]].format(noun=noun)
    prompt = (f"{char['character']}, {shot['prompt']}, {framing}. {char['style']}, "
              f"{'wide 16:9' if W >= H else 'tall 9:16'} shot")
    refs = None
    if shot.get("ref"):
        from .characters import pack_dir
        master = pack_dir(char["name"]) / "master.png"
        refs = [master] if master.exists() else None
        if refs:
            prompt = (f"The same {noun} character from the reference image, with the same face, "
                      f"{(char.get('body') or {}).get('fur', 'body')} and outfit. ") + prompt
    return shared_image(prompt, gw, gh, char["seed"], job_dir, refs=refs, cached_only=cached_only)


DRAFT_MOVE = {"dolly": 0, "vertigo": 0, "focus": 0, "truck": 1, "pull": 2, "tilt": 3, "handheld": 4, "orbit": 5}


def still_motion(img, dur, idx, W, H, out, job_dir, mode, camera=None):
    """Final: 2.5D depth parallax (Depth Anything V2 Small); draft or PARALLAX=off: flat zoom/pan.
    camera (the camera: header; unset / flat = the moves above, unchanged): off = a still frame, auto / a move name /
    a comma list = the 3D-feel depth moves of parallax.camera_clip (drafts show the nearest flat move)."""
    cam = (camera or "").strip().lower()
    if cam and cam != "flat":
        from .parallax import camera_move
        move = "off" if cam == "off" else camera_move(cam, idx)
        if move == "off":
            run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{H},setsar=1,format=yuv420p", "-r", str(C.FPS), "-t", f"{dur:.3f}", *enc_args(mode), out],
                job_dir, "still clip")
            return
        if mode == "final" and C.PARALLAX:
            from .parallax import camera_clip
            try:
                camera_clip(img, dur, idx, W, H, out, job_dir, mode, move)
                return
            except Exception as e:   # never lose a render over the depth effect
                log(job_dir, f"  camera {move} failed for clip {idx + 1} ({e}); using zoom/pan")
        ken_burns(img, dur, DRAFT_MOVE.get(move, idx), W, H, out, job_dir, mode)
        return
    if mode == "final" and C.PARALLAX:
        from .parallax import parallax_clip
        try:
            parallax_clip(img, dur, idx, W, H, out, job_dir, mode)
            return
        except Exception as e:   # never lose a render over the depth effect
            log(job_dir, f"  parallax failed for clip {idx + 1} ({e}); using zoom/pan")
    ken_burns(img, dur, idx, W, H, out, job_dir, mode)


def make_shot(shot, idx, dur, W, H, job_dir, mode, warnings, ctx=None):
    """Builds clip_XXX.mp4 for one shot and returns its path.
    ctx (for character videos): {"character": dict, "words": [[w, start, end, phonemes], ...], "t0": clip start}"""
    ctx = ctx or {}
    out = job_dir / "work" / f"clip_{idx:03d}.mp4"
    out.parent.mkdir(exist_ok=True)
    kind = shot["type"]
    char = ctx.get("character")
    if kind == "talk":
        from . import presenter
        if char and presenter.pack_ready(char["name"]):
            presenter.talk_clip(shot, idx, dur, ctx.get("words") or [], ctx.get("t0", 0.0), W, H, out, job_dir,
                                mode, char["name"])
            return out
        if mode != "draft":
            raise PipelineError(f"no finished character pack for {char['name'] if char else '?'}: "
                                f"run tools/make_character_pack.py first")
        img = placeholder_image(f"PRESENTER: {shot['pose']} @ {shot['set']}", "lip-synced presenter clip "
                                "(appears once the character pack is built)", W, H, job_dir)
        ken_burns(img, dur, idx, W, H, out, job_dir, mode)
        return out
    if kind == "act":
        if mode == "draft" or not char:
            img = placeholder_image(f"CHARACTER SCENE ({shot['framing']})", shot["prompt"], W, H, job_dir)
            ken_burns(img, dur, idx, W, H, out, job_dir, mode)
        else:
            still_motion(act_image(shot, char, W, H, job_dir), dur, idx, W, H, out, job_dir, mode, ctx.get("camera"))
        return out
    if kind in ("ai", "stock"):   # [stock: ...] = an AI image with the art style's stock words (doc_photo: a photo)
        style = ctx.get("art_style")
        prompt, stock = (shot["query"], True) if kind == "stock" else (shot["prompt"], False)
        if mode == "draft":   # the placeholder shows the script's prompt (as before) and the art style under it
            from . import presets
            st = presets.load("art_styles", style or presets.DEFAULTS["art_styles"])
            text = f"{prompt}, {st['stock_suffix']}" if stock and st["stock_suffix"] else prompt
            img = placeholder_image("AI IMAGE (made in the final render)", text, W, H, job_dir,
                                    note=f"Art style: {st['label']}")
        else:
            img = ai_image(prompt, W, H, job_dir, style=style, stock=stock)
        still_motion(img, dur, idx, W, H, out, job_dir, mode, ctx.get("camera"))
        return out
    graphic_clip(shot, dur, W, H, out, job_dir, mode, safe=ctx.get("safe"))
    return out
