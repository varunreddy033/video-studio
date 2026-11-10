"""
captions.py  -  word-by-word highlighted captions as an .ass subtitle file (burned in by FFmpeg/libass).
Shows a short phrase at a time; the word being spoken is amber, the rest white.
"""

from pathlib import Path

from . import config as C


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    hh = int(t // 3600)
    mm = int(t % 3600 // 60)
    ss = t % 60
    return f"{hh}:{mm:02d}:{ss:05.2f}"


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def _groups(words, max_words, max_chars):
    """Split [[word, start, end, seg_index], ...] into short phrases."""
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            gap = w[1] - prev[2]
            text_len = sum(len(x[0]) + 1 for x in cur) + len(w[0])
            if (len(cur) >= max_words or text_len > max_chars or gap > 0.45 or w[3] != prev[3]
                    or prev[0][-1:] in ".?!:;"):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def write_ass(words, W: int, H: int, out: Path, total: float, style: str = "standard"):
    """style 'standard' (full videos) or 'short': bigger words, placed higher, and kept out of the bottom 20% and
    the right 12% where YouTube draws the Shorts buttons and description."""
    vertical = H > W
    margin_l = margin_r = int(W * 0.06)
    if style == "short":
        safe = C.TYPES["short"]["safe"]
        size = int(H * 0.062)
        margin_v = int(H * (safe["bottom"] + 0.04))
        margin_l, margin_r = int(W * 0.05), int(W * (safe["right"] + 0.03))
        max_words, max_chars = 3, 14
    else:
        size = int(H * (0.042 if vertical else 0.066))
        margin_v = int(H * (0.17 if vertical else 0.075))   # vertical: on the presenter's blazer, below card labels
        max_words, max_chars = (3, 18) if vertical else (6, 34)
    outline = max(2, int(size * 0.09))
    r, g, b = C.ACCENT
    hi = f"&H00{b:02X}{g:02X}{r:02X}&"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{C.CAPTION_FONT},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{outline},{max(1, outline // 2)},2,{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    groups = _groups(words, max_words, max_chars)
    for gi, grp in enumerate(groups):
        nxt = groups[gi + 1][0][1] if gi + 1 < len(groups) else total
        g_end = min(grp[-1][2] + 0.35, nxt)
        for wi, w in enumerate(grp):
            start = w[1]
            end = grp[wi + 1][1] if wi + 1 < len(grp) else g_end
            if end - start < 0.02:
                continue
            parts = []
            for k, x in enumerate(grp):
                t = _esc(x[0])
                parts.append("{\\c" + hi + "}" + t + "{\\c&H00FFFFFF&}" if k == wi else t)
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Word,,0,0,0,,{' '.join(parts)}")
    out.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return len(groups)


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
