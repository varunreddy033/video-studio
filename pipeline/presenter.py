"""
presenter.py  -  lip-synced presenter clips for [talk: pose | set | camera] shots (presenter plan, build step 3).

Mouth timing comes from Kokoro itself: for every spoken word it reports the exact phonemes (IPA) and their start/end,
so each phoneme maps straight to a mouth shape (the same shape set as Rhubarb Lip Sync: closed, M/B/P, ee-teeth,
open, wide, round). Rhubarb's macOS build is Intel-only and needs Rosetta, which this Mac doesn't have; Kokoro's own
timing is exact anyway (Rhubarb would have to guess it back from the audio).

Per frame: mouth shape + blink every 2-6 s + slow breathing (1.2% scale) + gentle sway, composited with a soft shadow
on the set, with an optional slow zoom. Pack: assets/characters/<name>/ (tools/make_character_pack.py).
"""

import json
import math
import random
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import characters
from . import config as C
from .util import PipelineError
from .visuals import frames_to_clip

SHAPES = ["closed", "slight", "wide", "o", "e", "mbp"]

# phoneme -> mouth shape (Kokoro/misaki IPA; capitals are misaki's diphthong letters)
_WIDE = set("aɑæɐ") | {"I", "W"}
_E = set("ɛeʌəɜɚ") | {"A"}
_O = set("ɔɒoɵuʊw") | {"O", "Q", "Y"}
_MBP = set("mbp")
_SLIGHT = set("iɪjtdszkgnŋʃʒθðhrlfvɹɾʧʤɡ")
_IGNORE = set("ˈˌːˑ.,!?;:-—'\" ")


def phoneme_shape(ph: str) -> str:
    if ph in _MBP:
        return "mbp"
    if ph in _WIDE:
        return "wide"
    if ph in _E:
        return "e"
    if ph in _O:
        return "o"
    return "slight"


def mouth_cues(words, t0: float, t1: float):
    """[(start, end, shape)] relative to t0, for words = [[word, start, end, phonemes], ...] in absolute time."""
    cues = []
    for wd in words:
        w, a, b = wd[0], wd[1], wd[2]
        ph = wd[3] if len(wd) > 3 else ""
        if b <= t0 or a >= t1:
            continue
        units = [c for c in ph if c not in _IGNORE] or [c for c in w.lower() if c.isalpha()]
        if not units:
            continue
        weights = [2.0 if phoneme_shape(c) in ("wide", "e", "o") else 1.0 for c in units]
        total = sum(weights)
        t = a
        for c, wt in zip(units, weights):
            d = (b - a) * wt / total
            cues.append((t - t0, t + d - t0, phoneme_shape(c) if ph else ("wide" if c in "aeiou" else "slight")))
            t += d
    # merge tiny cues so the mouth doesn't flicker (min ~2 frames)
    merged = []
    for s, e, shp in cues:
        if merged and (shp == merged[-1][2] or e - s < 0.06):
            merged[-1] = (merged[-1][0], e, merged[-1][2])
        else:
            merged.append((s, e, shp))
    return merged


def _shape_at(cues, t):
    for s, e, shp in cues:
        if s <= t < e:
            return shp
        if s > t:
            break
    return "closed"


@lru_cache(maxsize=4)
def _pack(name: str):
    d = characters.pack_dir(name)
    p = d / "pack.json"
    if not p.exists():
        raise PipelineError(f"no character pack for {name}: run tools/make_character_pack.py {name}")
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=32)
def _pose_frames(name: str, pose: str, target_h: int):
    """All mouth frames (+ blinking versions) of one pose, cropped to the character and scaled to target_h."""
    pack = _pack(name)
    if pose not in pack["poses"] or "dir" not in pack["poses"][pose]:
        raise PipelineError(f"pose '{pose}' isn't in {name}'s pack yet")
    info = pack["poses"][pose]
    pd = characters.pack_path(name, info["dir"])
    alpha = Image.open(pd / "alpha.png").convert("L")
    a = np.asarray(alpha)
    ys, xs = np.nonzero(a > 20)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    s = target_h / (box[3] - box[1])
    size = (max(1, int((box[2] - box[0]) * s)), target_h)
    eye_mask = Image.new("L", alpha.size, 0)
    ImageDraw.Draw(eye_mask).ellipse(info["eye_box"], fill=255)
    eye_mask = eye_mask.filter(ImageFilter.GaussianBlur(12))
    blink = Image.open(pd / "blink_cut.png").convert("RGBA")
    frames, blinks = {}, {}
    for shp in SHAPES:
        im = Image.open(pd / f"{shp}_cut.png").convert("RGBA")
        bl = Image.composite(blink, im, eye_mask)
        frames[shp] = im.crop(box).resize(size, Image.LANCZOS)
        blinks[shp] = bl.crop(box).resize(size, Image.LANCZOS)
    shadow_a = frames["closed"].split()[-1].filter(ImageFilter.GaussianBlur(max(10, target_h // 30)))
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow.putalpha(shadow_a.point(lambda v: int(v * 0.28)))      # soft contact shadow, not a ghost outline
    return frames, blinks, shadow


@lru_cache(maxsize=8)
def _set_image(name: str, set_name: str, W: int, H: int, margin: float):
    pack = _pack(name)
    if set_name not in pack.get("sets", {}):
        raise PipelineError(f"set '{set_name}' isn't in {name}'s pack yet")
    bg = Image.open(characters.pack_path(name, pack["sets"][set_name]["file"])).convert("RGB")
    bw, bh = int(W * margin), int(H * margin)
    s = max(bw / bg.width, bh / bg.height)
    bg = bg.resize((int(bg.width * s + 0.5), int(bg.height * s + 0.5)), Image.LANCZOS)
    x, y = (bg.width - bw) // 2, (bg.height - bh) // 2
    # a touch of blur on the set so the presenter stands out (shallow depth of field)
    return bg.crop((x, y, x + bw, y + bh)).filter(ImageFilter.GaussianBlur(1.6))


def talk_clip(shot, idx, dur, words, t0, W, H, out: Path, job_dir: Path, mode: str, character: str):
    """Render one lip-synced presenter clip. words: the video's words in absolute time; t0 = clip start."""
    vertical = H > W
    target_h = int(H * (0.62 if vertical else 0.9))
    frames, blinks, shadow = _pose_frames(character, shot["pose"], target_h)
    margin = 1.08
    bg = _set_image(character, shot["set"], W, H, margin)
    cues = mouth_cues(words, t0, t0 + dur)
    rng = random.Random(f"{character}|{idx}|{shot['pose']}")
    n = int(math.ceil(dur * C.FPS))
    # blink schedule: every 2-6 s, 4 frames each
    blink_frames, t = set(), rng.uniform(0.8, 2.5)
    while t < dur:
        f = int(t * C.FPS)
        blink_frames.update(range(f, f + 4))
        t += rng.uniform(2.0, 6.0)
    cw, chh = frames["closed"].size
    cx = W * (0.5 if vertical else (0.42 if shot["set"] == "stage" else 0.5))
    phase = rng.uniform(0, 6.28)
    cam = shot.get("camera", "static")

    def gen():
        for f in range(n):
            tt = f / C.FPS
            shp = _shape_at(cues, tt)
            src = (blinks if f in blink_frames else frames)[shp]
            breath = 1 + 0.012 * math.sin(2 * math.pi * tt / 3.6 + phase)
            sway = W * 0.004 * math.sin(2 * math.pi * tt / 6.3 + phase)
            sw, sh = int(cw * (1 + (breath - 1) * 0.5)), int(chh * breath)
            ch_img = src.resize((sw, sh), Image.BILINEAR)
            sd_img = shadow.resize((sw, sh), Image.BILINEAR)
            # camera: the whole picture slowly zooms (set + presenter)
            prog = tt / max(dur, 0.01)
            z = {"zoom in": 1 + 0.07 * prog, "zoom out": 1.07 - 0.07 * prog}.get(cam, 1.0)
            frame = bg.copy()
            fx = int((frame.width - W) / 2 + cx - sw / 2 + sway)
            fy = int(frame.height - (frame.height - H) / 2 - sh)
            frame.paste(sd_img, (fx + int(W * 0.005), fy + int(H * 0.006)), sd_img)
            frame.paste(ch_img, (fx, fy), ch_img)
            if z != 1.0 or margin != 1.0:
                vw, vh = W / z, H / z
                ox, oy = (frame.width - vw) / 2, (frame.height - vh) / 2
                frame = frame.resize((W, H), Image.BILINEAR, box=(ox, oy, ox + vw, oy + vh))
            yield frame

    frames_to_clip(gen(), n, dur, W, H, out, job_dir, mode, f"presenter clip {idx + 1}")


def pack_ready(character: str) -> bool:
    try:
        p = _pack.__wrapped__(character)
    except PipelineError:
        return False
    if not p.get("sets") or not all("dir" in v for v in p["poses"].values()):
        return False
    # pack.json is in git but the images aren't: only "ready" when the files are on THIS machine
    need = [characters.pack_path(character, v["dir"]) / "closed_cut.png" for v in p["poses"].values()]
    need += [characters.pack_path(character, s["file"]) for s in p["sets"].values()]
    return all(f.exists() for f in need)
