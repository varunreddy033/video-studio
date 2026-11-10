"""Check every preset file (presets/<kind>/*.json) and that the default presets still equal today's config values.

    bin/python tools/check_presets.py        -> prints "presets: clean" or the problems (exit code 1)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import config as C          # noqa: E402
from pipeline import presets as P         # noqa: E402

problems = P.validate_all()
if not problems:
    d = {kind: P.load(kind, P.DEFAULTS[kind]) for kind in ("voices", "captions", "art_styles", "music")}
    safe = C.TYPES["short"]["safe"]
    r, g, b = C.ACCENT
    want = [
        ("voices", "voice", C.KOKORO_VOICE), ("voices", "speed", C.KOKORO_SPEED),
        ("voices", "wpm", C.WORDS_PER_MIN),
        ("captions", "font", C.CAPTION_FONT), ("captions", "font_file", C.FONT_FILES["heavy"]),
        ("captions", "highlight_colour", f"#{r:02X}{g:02X}{b:02X}"),
        ("captions", "layouts.short.margin_v", round(safe["bottom"] + 0.04, 4)),
        ("captions", "layouts.short.margin_r", round(safe["right"] + 0.03, 4)),
        ("art_styles", "suffix", C.IMAGE_STYLE_DEFAULT), ("art_styles", "prefix", ""),
        ("art_styles", "stock_suffix", "real-world documentary photograph"), ("art_styles", "steps", None),
        ("music", "volume", C.BGM_VOLUME), ("music", "loudness_lufs", C.TARGET_LUFS),
    ]
    for kind, field, value in want:
        got = d[kind]
        for part in field.split("."):
            got = got[part]
        if got != value:
            problems.append(f"presets/{kind}/{P.DEFAULTS[kind]}.json: '{field}' is {got!r} but the config uses "
                            f"{value!r} (default presets must equal today's values; check .env too)")
    # doc_photo must build byte-for-byte the prompts of the code before art styles (or cached images are lost)
    from pipeline import visuals as V
    for prompt, stock, want in (("x", False, f"x, {C.IMAGE_STYLE}"),
                                ("x", True, f"x, real-world documentary photograph, {C.IMAGE_STYLE}")):
        got = V.style_prompt(prompt, None, stock) if C.IMAGE_STYLE else None
        if C.IMAGE_STYLE and got != want:
            problems.append(f"style_prompt('{prompt}', doc_photo, stock={stock}) = {got!r}, expected {want!r}")
    if not (C.FONTS_DIR / d["captions"]["font_file"]).exists():
        problems.append(f"font file {d['captions']['font_file']} is missing from assets/fonts")



def _legacy_ass(words, W, H, total, style):
    """The caption file exactly as the code before caption styles wrote it (frozen copy, do not edit).
    The default caption style must reproduce it byte for byte, or every existing video changes its look."""
    def ts(t):
        t = max(0.0, t)
        return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

    def groups(max_words, max_chars):
        out, cur = [], []
        for w in words:
            if cur:
                prev = cur[-1]
                if (len(cur) >= max_words or sum(len(x[0]) + 1 for x in cur) + len(w[0]) > max_chars
                        or w[1] - prev[2] > 0.45 or w[3] != prev[3] or prev[0][-1:] in ".?!:;"):
                    out.append(cur)
                    cur = []
            cur.append(w)
        return out + ([cur] if cur else [])

    vertical = H > W
    margin_l = margin_r = int(W * 0.06)
    if style == "short":
        size, margin_v = int(H * 0.062), int(H * (0.20 + 0.04))
        margin_l, margin_r = int(W * 0.05), int(W * (0.12 + 0.03))
        max_words, max_chars = 3, 14
    else:
        size = int(H * (0.042 if vertical else 0.066))
        margin_v = int(H * (0.17 if vertical else 0.075))
        max_words, max_chars = (3, 18) if vertical else (6, 34)
    outline = max(2, int(size * 0.09))
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 2\n"
            f"ScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
            f"SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
            f"Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Word,Barlow Condensed ExtraBold,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,"
            f"100,0,0,1,{outline},{max(1, outline // 2)},2,{margin_l},{margin_r},{margin_v},1\n\n[Events]\n"
            f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines, gs = [], groups(max_words, max_chars)
    for gi, grp in enumerate(gs):
        g_end = min(grp[-1][2] + 0.35, gs[gi + 1][0][1] if gi + 1 < len(gs) else total)
        for wi, w in enumerate(grp):
            end = grp[wi + 1][1] if wi + 1 < len(grp) else g_end
            if end - w[1] < 0.02:
                continue
            parts = []
            for k, x in enumerate(grp):
                t = x[0].replace("\\", "").replace("{", "(").replace("}", ")")
                parts.append("{\\c&H0020B0FF&}" + t + "{\\c&H00FFFFFF&}" if k == wi else t)
            lines.append(f"Dialogue: 0,{ts(w[1])},{ts(end)},Word,,0,0,0,,{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


if not problems:
    import tempfile
    from pipeline import captions
    text = ("Everyone is talking about an AI bubble. But what does that actually mean? A bubble forms when prices "
            "climb far faster than the real value behind them: seventy {dollars} for something worth far less.")
    words, t = [], 0.0
    for i, w in enumerate(text.split()):
        words.append([w, round(t, 3), round(t + 0.21 + 0.03 * (len(w) % 4), 3), i // 9])
        t += 0.27 + (0.6 if w[-1:] in ".?" else 0.0) + (0.005 if i == 20 else 0.0)
    words.append(["end\\", round(t, 3), round(t + 0.01, 3), 99])
    with tempfile.TemporaryDirectory() as d:
        for W, H in ((1920, 1080), (960, 540), (1080, 1920), (540, 960)):
            for style in ("standard", "short"):
                f = Path(d) / "c.ass"
                captions.write_ass(words, W, H, f, t + 1, style=style)
                if f.read_text(encoding="utf-8") != _legacy_ass(words, W, H, t + 1, style):
                    problems.append(f"the default caption style no longer writes the original caption file "
                                    f"({W}x{H}, {style}): presets/captions/{P.DEFAULTS['captions']}.json or "
                                    f"pipeline/captions.py changed its look")

print("presets: clean" if not problems else "presets: PROBLEMS\n- " + "\n- ".join(problems))
sys.exit(1 if problems else 0)
