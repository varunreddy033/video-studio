"""
captions.py  -  word-by-word captions as an .ass subtitle file (burned in by FFmpeg/libass), drawn in a caption
style: presets/captions/<id>.json (font, colours, outline, how many words, what happens to the spoken word).
The default style amber_word writes byte-for-byte the file made before caption styles existed
(tools/check_presets.py checks that).

  highlight "word"  the phrase stays, the spoken word changes colour
  highlight "box"   the phrase stays, a coloured box sits behind the spoken word
  highlight "none"  the phrase is shown as it is (with max_words 1: one word at a time)
"""

import hashlib
import json
from pathlib import Path

from . import config as C
from . import presets

PREVIEWS = C.ASSETS / "caption_previews"       # small looping clips for the style picker (not in git)
PREVIEW_VERSION = "1"


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    hh = int(t // 3600)
    mm = int(t % 3600 // 60)
    ss = t % 60
    return f"{hh}:{mm:02d}:{ss:05.2f}"


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def _groups(words, max_words, max_chars, max_gap=0.45, break_after=".?!:;"):
    """Split [[word, start, end, seg_index], ...] into short phrases."""
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            gap = w[1] - prev[2]
            text_len = sum(len(x[0]) + 1 for x in cur) + len(w[0])
            if (len(cur) >= max_words or text_len > max_chars or gap > max_gap or w[3] != prev[3]
                    or prev[0][-1:] in break_after):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def _col(hex_colour: str, alpha: int = 0) -> str:
    """'#RRGGBB' -> ASS '&HAABBGGRR' (alpha 0 = solid, 255 = invisible)."""
    h = hex_colour.lstrip("#")
    return "&H" + f"{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _num(v: float) -> str:
    return f"{v:g}"


def _preset(preset):
    if isinstance(preset, dict):
        return preset
    return presets.load("captions", preset or presets.DEFAULTS["captions"])


def write_ass(words, W: int, H: int, out: Path, total: float, style: str = "standard", preset=None,
              scale: float = 1.0, margin_v: float = None):
    """style 'standard' (full videos) or 'short': bigger words, placed higher, and kept out of the bottom 20% and
    the right 12% where YouTube draws the Shorts buttons and description.
    preset = caption style id or its dict (None = the default). scale / margin_v are for the picker's preview."""
    p = _preset(preset)
    vertical = H > W
    L = p["layouts"]["short" if style == "short" else "vertical" if vertical else "landscape"]
    size = int(H * L["size"] * scale) if scale != 1.0 else int(H * L["size"])
    mv = int(H * (L["margin_v"] if margin_v is None else margin_v))
    margin_l, margin_r = int(W * L["margin_l"]), int(W * L["margin_r"])
    max_words, max_chars = L["max_words"], L["max_chars"]
    outline = max(p["outline_min_px"], int(size * p["outline_ratio"]))
    shadow = int(size * p["shadow_ratio"]) if "shadow_ratio" in p else max(1, outline // 2)
    primary = _col(p["text_colour"])
    hi = _col(p["highlight_colour"]) + "&"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{p["font"]},{size},{primary},{primary},{_col(p["outline_colour"])},{_col(p["shadow_colour"], p["shadow_transparency"])},{-1 if p["bold"] else 0},{-1 if p["italic"] else 0},0,0,100,100,{_num(size * p.get("spacing_ratio", 0))},{_num(p.get("angle", 0))},{3 if p.get("box_style") else 1},{outline},{shadow},{p.get("alignment", 2)},{margin_l},{margin_r},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if not p.get("enabled", True):                      # "No captions": a valid file with nothing in it
        out.write_text(head, encoding="utf-8")
        return 0
    case = {"upper": str.upper, "lower": str.lower}.get(p["case"], lambda t: t)
    blur = size * p.get("blur_ratio", 0)
    tag_blur = f"\\blur{_num(round(blur, 1))}" if blur else ""
    tag_pop = "\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)" if p.get("pop") else ""

    def pre(first: bool) -> str:
        tags = tag_blur + (tag_pop if first else "")
        return "{" + tags + "}" if tags else ""

    G = p["group"]
    groups = _groups(words, max_words, max_chars, G["max_gap_sec"], G["break_after"])
    for gi, grp in enumerate(groups):
        nxt = groups[gi + 1][0][1] if gi + 1 < len(groups) else total
        g_end = min(grp[-1][2] + G["linger_sec"], nxt)
        texts = [case(_esc(x[0])) for x in grp]
        if p["highlight"] == "none":
            if g_end - grp[0][1] >= G["min_word_sec"]:
                lines.append(f"Dialogue: 0,{_ass_time(grp[0][1])},{_ass_time(g_end)},Word,,0,0,0,,"
                             f"{pre(True)}{' '.join(texts)}")
            continue
        if p["highlight"] == "box":                     # the phrase on layer 1, the moving box under it on layer 0
            if g_end - grp[0][1] >= G["min_word_sec"]:
                lines.append(f"Dialogue: 1,{_ass_time(grp[0][1])},{_ass_time(g_end)},Word,,0,0,0,,"
                             f"{pre(True)}{' '.join(texts)}")
            box = _col(p["box_colour"]) + "&"
            pad = _num(round(size * p.get("box_pad_ratio", 0.16), 1))
        for wi, w in enumerate(grp):
            start = w[1]
            end = grp[wi + 1][1] if wi + 1 < len(grp) else g_end
            if end - start < G["min_word_sec"]:
                continue
            parts = []
            if p["highlight"] == "box":
                # same words, invisible, except the spoken one: drawn as a fat blob in the box colour
                for k, t in enumerate(texts):
                    parts.append(("{\\1a&H00&\\3a&H00&\\4a&HFF&\\1c" + box + "\\3c" + box + "\\bord" + pad + "\\blur0}"
                                  if k == wi else "{\\alpha&HFF&}") + t)
                lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Word,,0,0,0,,"
                             f"{pre(wi == 0 and bool(tag_pop))}{' '.join(parts)}")
                continue
            for k, t in enumerate(texts):
                parts.append("{\\c" + hi + "}" + t + "{\\c" + primary + "&}" if k == wi else t)
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Word,,0,0,0,,{pre(wi == 0)}{' '.join(parts)}")
    out.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return len(groups)


# ------------------------------------------------------------------ previews for the style picker ---
PREVIEW_TEXT = "This is how your captions will look in the video."


def preview_path(style_id: str) -> Path:
    p = presets.load("captions", style_id)
    key = hashlib.sha1(json.dumps([PREVIEW_VERSION, p], sort_keys=True).encode()).hexdigest()[:10]
    return PREVIEWS / f"{style_id}_{key}.mp4"


def make_preview(style_id: str) -> Path:
    """A 4.4 s looping clip (480x270) of the style on a neutral backdrop, drawn by the same code and libass as
    the real video. Cached per preset content: editing the preset file makes a new clip."""
    import subprocess

    from PIL import Image

    out = preview_path(style_id)
    if out.exists() and out.stat().st_size > 0:
        return out
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    for old in PREVIEWS.glob(f"{style_id}_*.mp4"):
        old.unlink(missing_ok=True)
    W, H, dur = 480, 270, 4.4
    words, t = [], 0.25
    for w in PREVIEW_TEXT.split():
        words.append([w, round(t, 2), round(t + 0.3, 2), 0])
        t += 0.38
    ass = PREVIEWS / f"{style_id}.ass"
    write_ass(words, W, H, ass, dur, preset=style_id, scale=2.3, margin_v=0.32)
    bg = PREVIEWS / "backdrop.png"
    if not bg.exists():
        img = Image.new("RGB", (W, H))
        px = img.load()
        for y in range(H):
            v = 58 + int(52 * y / H)
            for x in range(W):
                px[x, y] = (v, v + 2, v + 8)
        img.save(bg)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", bg.name, "-t", str(dur),
           "-vf", f"ass={ass.name}:fontsdir={Path(_rel(C.FONTS_DIR, PREVIEWS)).as_posix()}", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out.name]
    r = subprocess.run(cmd, cwd=str(PREVIEWS), capture_output=True, text=True)
    ass.unlink(missing_ok=True)
    if r.returncode != 0 or not out.exists():
        out.unlink(missing_ok=True)
        raise RuntimeError("caption preview failed: " + (r.stderr.strip().splitlines() or ["ffmpeg error"])[-1])
    return out


def _rel(path: Path, start: Path) -> str:
    import os
    return os.path.relpath(path, start)


def _srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    hh, ms = divmod(ms, 3600000)
    mm, ms = divmod(ms, 60000)
    ss, ms = divmod(ms, 1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def write_srt(words, out: Path, max_chars: int = 84):
    """Sentence-level captions file for YouTube (upload it as subtitles): up to two lines of ~42 characters."""
    cues, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x[0] for x in cur)
        if w[0][-1:] in ".?!" or len(text) >= max_chars:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    lines = []
    for i, c in enumerate(cues, 1):
        text = " ".join(x[0] for x in c)
        if len(text) > 42:   # split into two balanced lines
            mid = len(text) // 2
            cut = text.rfind(" ", 0, mid + 8)
            text = text[:cut] + "\n" + text[cut + 1:] if cut > 0 else text
        lines.append(f"{i}\n{_srt_time(c[0][1])} --> {_srt_time(c[-1][2] + 0.25)}\n{text}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return len(cues)
