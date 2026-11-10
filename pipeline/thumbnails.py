"""
thumbnails.py  -  3 thumbnail options (1280x720 JPG) for YouTube Studio's A/B "Test & compare".
  1 + 2  two AI images of the thumbnail prompt (different seeds), text on the left / right
  3      a frame from the video itself, text on a solid colour band
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import config as C
from .util import log, run
from .visuals import ai_image, font, wrap

TW, TH = 1280, 720


def _cover(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    s = max(TW / img.width, TH / img.height)
    img = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    x, y = (img.width - TW) // 2, (img.height - TH) // 2
    return img.crop((x, y, x + TW, y + TH))


def _shade(img, side):
    """Darken the side where the text goes so it always reads."""
    grad = Image.new("L", (TW, 1))
    for x in range(TW):
        t = x / (TW - 1)
        v = (1 - t) if side == "left" else t
        grad.putpixel((x, 0), int(225 * max(0.0, min(1.0, (v - 0.15) / 0.6))))
    grad = grad.resize((TW, TH))
    return Image.composite(Image.new("RGB", (TW, TH), (0, 0, 0)), img, grad)


def _text_block(img, text, side, band=False):
    d = ImageDraw.Draw(img)
    words = text.upper().split()
    max_w = TW * (0.9 if band else 0.56)
    size = 150
    while size > 50:
        f = font("heavy", size)
        lines = wrap(d, " ".join(words), f, max_w)
        if len(lines) <= 3 and all(d.textlength(l, font=f) <= max_w for l in lines):
            break
        size -= 8
    f = font("heavy", size)
    lines = wrap(d, " ".join(words), f, max_w)
    lh = size * 1.02
    block_h = lh * len(lines)
    if band:
        y0 = TH - block_h - 70
        d.rectangle([0, y0 - 30, TW, TH], fill=(10, 10, 14))
        d.rectangle([0, y0 - 30, TW, y0 - 22], fill=C.ACCENT)
    else:
        y0 = (TH - block_h) / 2
    x = 70 if side == "left" or band else TW - 70
    anchor = "la" if side == "left" or band else "ra"
    for i, ln in enumerate(lines):
        fill = C.ACCENT if i == len(lines) - 1 and len(lines) > 1 else (255, 255, 255)
        d.text((x, y0 + i * lh), ln, font=f, fill=fill, anchor=anchor,
               stroke_width=max(4, size // 18), stroke_fill=(0, 0, 0))
    return img


def make_character(parsed: dict, job_dir: Path, final_video: Path, frame_time: float):
    """Presenter videos: (1) the character acting out thumbnail_prompt, text left; (2) the character's own shocked
    pose, big, on its set, text left; (3) a frame of the video with a text band."""
    import json
    import re as _re
    from .visuals import shared_image
    meta = parsed["meta"]
    char = meta["character_data"]
    text = meta.get("thumbnail") or meta.get("title", "")
    scene = meta.get("thumbnail_prompt") or "looking shocked at a huge red crashing stock chart"
    noun = (char.get("body") or {}).get("noun", "character")
    scene = _re.sub(rf"\b{char['name']}\b", f"the {noun}", scene, flags=_re.I)
    out = []
    img1 = shared_image(f"{char['character']}, {scene}, the {noun} on the right side of the frame, bold dramatic "
                        f"composition, strong contrast, empty space on the left. {char['style']}", TW, TH,
                        char["seed"], job_dir)
    bg = _cover(Image.open(img1)).filter(ImageFilter.UnsharpMask(radius=2, percent=60))
    _text_block(_shade(bg, "left"), text, "left").save(job_dir / "thumb_1.jpg", quality=92)
    out.append("thumb_1.jpg")
    from . import characters
    pack = json.loads((characters.pack_dir(char["name"]) / "pack.json").read_text(encoding="utf-8"))
    pose = "shocked" if "shocked" in pack["poses"] else next(iter(pack["poses"]))
    cut = Image.open(characters.pack_path(char["name"], pack["poses"][pose]["dir"]) / "closed_cut.png").convert("RGBA")
    a = cut.split()[-1].point(lambda v: 255 if v > 20 else 0)
    cut = cut.crop(a.getbbox())
    setp = characters.pack_path(char["name"], pack["sets"][next(iter(pack["sets"]))]["file"])
    bg2 = _cover(Image.open(setp)).filter(ImageFilter.GaussianBlur(3))
    s = TH * 1.05 / cut.height
    cut = cut.resize((int(cut.width * s), int(cut.height * s)), Image.LANCZOS)
    glow = Image.new("RGBA", bg2.size, (0, 0, 0, 0))
    ga = Image.new("L", bg2.size, 0)
    ga.paste(cut.split()[-1], (TW - cut.width + 40, TH - cut.height + 60))
    glow.putalpha(ga.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.8)))
    bg2 = _shade(bg2.convert("RGB"), "left").convert("RGBA")
    bg2.alpha_composite(Image.new("RGBA", bg2.size, (255, 176, 32, 0)))
    bg2.paste((255, 176, 32), (0, 0), glow)
    bg2.paste(cut, (TW - cut.width + 40, TH - cut.height + 60), cut)
    _text_block(bg2.convert("RGB"), text, "left").save(job_dir / "thumb_2.jpg", quality=92)
    out.append("thumb_2.jpg")
    frame = job_dir / "cache" / "thumb_frame.png"
    run(["ffmpeg", "-y", "-ss", f"{frame_time:.2f}", "-i", final_video, "-frames:v", "1", frame], job_dir, "thumbnail frame")
    _text_block(_cover(Image.open(frame)), text, "left", band=True).save(job_dir / "thumb_3.jpg", quality=92)
    out.append("thumb_3.jpg")
    log(job_dir, f"thumbnails: {', '.join(out)}")
    return out


def thumb_prompt(parsed: dict) -> str:
    """The prompt of the 2 AI thumbnails (before the art style words are added)."""
    meta = parsed["meta"]
    prompt = meta.get("thumbnail_prompt") or next(
        (s.get("prompt") or s.get("query") for s in parsed["shots"] if s["type"] in ("ai", "stock")), meta.get("title"))
    return f"{prompt}, bold dramatic composition, strong contrast, one clear subject, empty space for text"


def make(parsed: dict, job_dir: Path, final_video: Path, frame_time: float):
    meta = parsed["meta"]
    if meta.get("character_data"):
        return make_character(parsed, job_dir, final_video, frame_time)
    text = meta.get("thumbnail") or meta.get("title", "")
    prompt = thumb_prompt(parsed)
    out = []
    for i, side in enumerate(("left", "right"), start=1):
        bg = _cover(Image.open(ai_image(prompt, TW, TH, job_dir, seed_extra=f"thumb{i}",
                                        style=meta["presets"]["art_style"])))
        bg = bg.filter(ImageFilter.UnsharpMask(radius=2, percent=60))
        img = _text_block(_shade(bg, side), text, side)
        p = job_dir / f"thumb_{i}.jpg"
        img.save(p, quality=92)
        out.append(p.name)
    frame = job_dir / "cache" / "thumb_frame.png"
    run(["ffmpeg", "-y", "-ss", f"{frame_time:.2f}", "-i", final_video, "-frames:v", "1", frame], job_dir, "thumbnail frame")
    img = _text_block(_cover(Image.open(frame)), text, "left", band=True)
    p = job_dir / "thumb_3.jpg"
    img.save(p, quality=92)
    out.append(p.name)
    log(job_dir, f"thumbnails: {', '.join(out)}")
    return out


def make_short(parsed: dict, job_dir: Path, video: Path, frame_time: float):
    """Shorts: ONE vertical thumbnail (1080x1920) from a frame of the Short, big text in the upper half (the
    Shorts feed mostly shows a frame; this is the one you pick in Studio). No new AI image."""
    import re as _re
    meta = parsed["meta"]
    text = meta.get("thumbnail") or _re.sub(r"\s*#\w+", "", meta.get("title", "")).strip()
    frame = job_dir / "cache" / "thumb_frame.png"
    frame.parent.mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-ss", f"{frame_time:.2f}", "-i", video, "-frames:v", "1", "-vf",
         "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", frame], job_dir, "thumbnail frame")
    img = Image.open(frame).convert("RGB")
    W, H = img.size
    d = ImageDraw.Draw(img)
    words = text.upper().split()
    max_w = W * 0.84
    size = 170
    while size > 60:
        f = font("heavy", size)
        lines = wrap(d, " ".join(words), f, max_w)
        if len(lines) <= 4 and all(d.textlength(l, font=f) <= max_w for l in lines):
            break
        size -= 8
    f = font("heavy", size)
    lines = wrap(d, " ".join(words), f, max_w)
    lh = size * 1.02
    y0 = H * 0.12
    shade = Image.new("L", (1, H))
    for y in range(H):
        shade.putpixel((0, y), int(200 * max(0.0, 1 - y / (y0 + lh * len(lines) + H * 0.12))))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shade.resize((W, H)))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        fill = C.ACCENT if i == len(lines) - 1 and len(lines) > 1 else (255, 255, 255)
        d.text((W / 2, y0 + i * lh), ln, font=f, fill=fill, anchor="ma",
               stroke_width=max(4, size // 18), stroke_fill=(0, 0, 0))
    img.save(job_dir / "thumb_1.jpg", quality=92)
    log(job_dir, "thumbnail: thumb_1.jpg (vertical)")
    return ["thumb_1.jpg"]
