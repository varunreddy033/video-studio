"""Design pieces of the designed thumbnails: the colour theme (from the video's own look), contrast maths, a static
stick figure (motion_gfx/figures.py with the pose baked in), icon stickers, the tag pill and the stamp.

The theme follows the reference cover (output/thumbnails/2026-11-13-nvidia-ceo-staff-vs-board-cover.jpg): a dark
background tinted by ONE strong accent colour, white headline with a dark outline, the accent on the hero number,
a red tag on top and a red stamp. The accent and the background pattern come from the video's format and palette
set, so a cover looks like its video.
"""

import base64
import colorsys
import hashlib
import re

from .. import config as C
from .. import icon_library as L
from ..motion_gfx import design as MD
from ..motion_gfx import figures as F

RED = "#D91E2A"            # tag pill (white text on it: contrast 5.3)
STAMP = "#FF3B47"          # stamp ink on the dark background (contrast >= 5)
WHITE = "#FFFFFF"
INK = "#0B0B0D"


# ------------------------------------------------------------------------------------------------ colour maths
def _rgb(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(c: str) -> float:
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _hex(r, g, b) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(v * 255))) for v in (r, g, b)))


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex(*(x + (y - x) * t for x, y in zip(ra, rb)))


def _sat(c: str) -> float:
    h, l, s = colorsys.rgb_to_hls(*_rgb(c))
    return s * (1 - abs(2 * l - 1))


def _is_red(c: str) -> bool:
    h, l, s = colorsys.rgb_to_hls(*_rgb(c))
    return s > 0.35 and (h < 0.04 or h > 0.93)


# ------------------------------------------------------------------------------------------------ theme
HEAVY = ("Anton", "Barlow Condensed ExtraBold", "Bangers", "Bebas Neue", "Archivo Black")
HEAVY_FOR = {"hand": "Bangers", "case": "Bebas Neue", "arcade": "Archivo Black", "swiss": "Archivo Black",
             "editorial": "Anton"}
PATTERNS = {"pop_poster": "rays", "tech_desk": "grid", "data_lab": "dots", "paper_notebook": "ruled",
            "newsroom": "bars", "case_file": "spot", "arcade_retro": "scan", "blueprint": "grid",
            "type_studio": "none"}


def theme(look: dict, seed: str) -> dict:
    """Colours + fonts of one video's thumbnails. accent = the most saturated non-red colour of the video's palette
    set that reads on the dark background (contrast >= 4.5), picked by the title's hash among the best three."""
    names = MD.PALETTE_SETS.get(look.get("palette") or "pop") or MD.PALETTE_SETS["pop"]
    pals = [p for p in MD.PALETTES if p["name"] in names] or MD.PALETTES[:8]
    cols = []
    for p in pals:
        for k in ("bg", "pop", "hi", "soft", "ink"):
            c = p.get(k)
            if isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c) and c.upper() not in cols:
                cols.append(c.upper())
    dark = min(cols, key=luminance)
    base = dark if luminance(dark) < 0.03 else "#0C0D10"
    good = [c for c in cols if not _is_red(c) and _sat(c) > 0.3 and contrast(c, base) >= 4.5]
    good.sort(key=lambda c: (-_sat(c), c))
    if not good:
        good = ["#9DFF1E", "#FFD21F", "#38E1FF"]
    h = int(hashlib.sha1(seed.encode()).hexdigest()[:6], 16)
    accent = good[:3][h % min(3, len(good))]
    bg = mix(base, accent, 0.06)
    pair = MD.FONT_PAIRS.get(look.get("fonts") or "poster") or MD.FONT_PAIRS["poster"]
    # thumbnails need a heavy display face at 320 px wide: thin or very wide faces of a format take a heavy one
    head = pair["head"] if pair["head"] in HEAVY else HEAVY_FOR.get(look.get("fonts"), "Anton")
    return {"bg": bg, "base": base, "accent": accent, "accent_dim": mix(accent, base, 0.55),
            "accent_soft": mix(accent, WHITE, 0.72), "glow": accent, "ink": WHITE, "outline": INK,
            "head": head, "body": pair["body"], "number": head,
            "pattern": PATTERNS.get(look.get("format") or "pop_poster", "grid"),
            "icon_style": (look.get("icon_style") or "sticker"), "family": look.get("icons") or "fluent_flat"}


def font_faces() -> str:
    """@font-face for every bundled font (file:// URLs, no network)."""
    out = []
    for fam, f, w in MD.FONTS.values():
        p = (C.FONTS_DIR / f)
        if p.exists():
            out.append(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; src: url("{p.as_uri()}"); }}')
    for fam, f in (("Patrick Hand", "PatrickHand-Regular.ttf"), ("Space Mono", "SpaceMono-Bold.ttf"),
                   ("Cormorant SC", "CormorantSC-SemiBold.ttf"), ("Courier Prime", "CourierPrime-Bold.ttf"),
                   ("Press Start 2P", "PressStart2P-Regular.ttf"), ("Bebas Neue", "BebasNeue-Regular.ttf"),
                   ("Archivo Black", "ArchivoBlack-Regular.ttf"), ("DM Serif Display", "DMSerifDisplay-Regular.ttf"),
                   ("Inter", "InterVariable.ttf")):
        p = C.FONTS_DIR / f
        if p.exists():
            out.append(f'@font-face {{ font-family: "{fam}"; src: url("{p.as_uri()}"); }}')
    return "\n".join(out)


def background(th: dict, W: int, H: int) -> str:
    """Dark field + one accent glow + the format's pattern (grid, dots, ruled paper, scanlines ...)."""
    a = th["accent"]
    pat = th["pattern"]
    layer = ""
    if pat == "grid":
        s = max(40, W // 22)
        layer = (f"repeating-linear-gradient(0deg, {a}14 0 2px, transparent 2px {s}px),"
                 f"repeating-linear-gradient(90deg, {a}14 0 2px, transparent 2px {s}px),")
    elif pat == "dots":
        layer = f"radial-gradient({a}26 2px, transparent 3px) 0 0 / {max(28, W // 40)}px {max(28, W // 40)}px,"
    elif pat == "ruled":
        layer = f"repeating-linear-gradient(0deg, {a}18 0 2px, transparent 2px {max(36, H // 24)}px),"
    elif pat == "scan":
        layer = "repeating-linear-gradient(0deg, #00000055 0 2px, transparent 2px 5px),"
    elif pat == "rays":
        layer = f"repeating-conic-gradient(from 0deg at 50% 45%, {a}12 0 6deg, transparent 6deg 18deg),"
    elif pat == "bars":
        layer = f"linear-gradient(180deg, {RED} 0 {max(10, H // 70)}px, transparent {max(10, H // 70)}px),"
    glow = f"radial-gradient(ellipse 70% 55% at 50% 45%, {a}38, transparent 70%)"
    vign = "radial-gradient(ellipse at 50% 50%, transparent 55%, #000000AA 100%)"
    return (f'<div class="bg" style="position:absolute;inset:0;background:{vign},{glow},{layer}{th["bg"]}"></div>')


# ------------------------------------------------------------------------------------------------ text
TEXT_CSS = """
.t { position:absolute; display:flex; align-items:center; justify-content:center; text-align:center;
     line-height:0.98; white-space:normal; overflow:hidden; letter-spacing:0.005em; }
.t span { display:inline; }
.stroke { paint-order: stroke fill; -webkit-text-stroke: var(--sw) var(--sc); }
"""

FIT_JS = """
window.fitAll = function () {
  for (const el of document.querySelectorAll('[data-fit]')) {
    let s = parseFloat(el.dataset.fit), min = parseFloat(el.dataset.min || 10);
    el.style.fontSize = s + 'px';
    if (el.dataset.sw) el.style.setProperty('--sw', (s * parseFloat(el.dataset.sw)).toFixed(1) + 'px');
    let guard = 0;
    while ((el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) && s > min && guard++ < 200) {
      s = Math.max(min, s * 0.96);
      el.style.fontSize = s.toFixed(1) + 'px';
      if (el.dataset.sw) el.style.setProperty('--sw', (s * parseFloat(el.dataset.sw)).toFixed(1) + 'px');
    }
  }
};
"""


def text_box(role, text, x, y, w, h, size, font, colour, th, stroke=0.06, stroke_col=None, glow=None, align="center",
             rotate=0, extra="", min_size=None):
    """A text element that shrinks itself to fit its box (fit() in the page) and reports itself for the checks.
    stroke = outline width as a share of the font size (counts for contrast); glow = a soft shadow colour."""
    esc = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    shadow = f"text-shadow: 0 0 {int(size * 0.18)}px {glow}aa, 0 {max(2, int(size * 0.05))}px 0 {th['outline']};" \
        if glow else f"text-shadow: 0 {max(2, int(size * 0.05))}px 0 {th['outline']}99;"
    sc = stroke_col or th["outline"]
    words = len(text.split())
    return (f'<div class="t{" stroke" if stroke else ""}" data-role="{role}" data-text="1" data-words="{words}" '
            f'data-fit="{size}" data-min="{min_size or max(10, int(size * 0.35))}" data-sw="{stroke}" '
            f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-family:\'{font}\';font-size:{size}px;'
            f'color:{colour};--sc:{sc};--sw:{size * stroke:.1f}px;justify-content:{align};'
            f'text-align:{"left" if align == "flex-start" else "center"};{shadow}'
            f'{f"transform:rotate({rotate}deg);" if rotate else ""}{extra}">{esc}</div>')


def tag_pill(text, cx, y, maxw, size, th, align="center", x=None):
    """The small red pill on top (white text). Width follows the text (fit shrinks it when too long)."""
    esc = text.replace("&", "&amp;").replace("<", "&lt;")
    left = f"left:{x}px;" if x is not None else f"left:{cx - maxw // 2}px;"
    return (f'<div style="position:absolute;{left}top:{y}px;width:{maxw}px;display:flex;justify-content:{align}">'
            f'<div class="t" data-role="tag" data-text="1" data-fit="{size}" data-min="{int(size * 0.5)}" '
            f'style="position:relative;max-width:{maxw}px;height:{int(size * 1.5)}px;padding:0 {int(size * 0.55)}px;'
            f'background:{RED};color:{WHITE};border-radius:{int(size * 0.22)}px;font-family:\'{th["head"]}\';'
            f'font-size:{size}px;letter-spacing:0.04em;white-space:nowrap;'
            f'box-shadow:0 {int(size * 0.14)}px 0 #7A0E15">{esc}</div></div>')


def stamp(text, x, y, w, h, size, th, rotate=-8):
    esc = text.replace("&", "&amp;").replace("<", "&lt;")
    b = max(6, int(size * 0.09))
    return (f'<div class="t" data-role="stamp" data-text="1" data-fit="{size}" data-min="{int(size * 0.45)}" '
            f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;color:{STAMP};border:{b}px solid {STAMP};'
            f'border-radius:{int(size * 0.12)}px;font-family:\'{th["head"]}\';font-size:{size}px;'
            f'background:{INK};letter-spacing:0.03em;white-space:nowrap;'
            f'transform:rotate({rotate}deg);box-shadow:0 0 {int(size * 0.3)}px {STAMP}55">{esc}</div>')


# ------------------------------------------------------------------------------------------------ icons
def icon_uri(icon_id: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(L.svg(icon_id).encode("utf-8")).decode("ascii")


def sticker(role, icon_id, x, y, size, th, rotate=0, style=None):
    """An icon from the library: a white rounded badge with a dark outline (sticker) or plain with a glow."""
    style = style or th["icon_style"]
    if style == "sticker":
        b = max(5, int(size * 0.04))
        deco = (f"background:#FFFFFF;border:{b}px solid {INK};border-radius:{int(size * 0.24)}px;padding:{int(size * 0.12)}px;"
                f"box-sizing:border-box;box-shadow:0 {int(size * 0.06)}px 0 {INK}, 0 0 {int(size * 0.25)}px {th['accent']}66;")
    else:
        deco = f"filter:drop-shadow(0 0 {int(size * 0.08)}px {th['accent']}AA) drop-shadow(0 {int(size * 0.03)}px 0 {INK});"
    return (f'<img data-role="{role}" alt="" src="{icon_uri(icon_id)}" style="position:absolute;left:{x}px;top:{y}px;'
            f'width:{size}px;height:{size}px;{deco}{f"transform:rotate({rotate}deg);" if rotate else ""}">')


# ------------------------------------------------------------------------------------------------ figure
SH_L, SH_R, HIP, NECK = F.SHOULDER_L, F.SHOULDER_R, F.HIP, F.NECK
# pose -> {part: (angle, origin)}; angles as in figures.pose_js (GSAP rotation = SVG rotate, clockwise)
POSES = {
    "idle": {},
    "talk": {"armR": (-40, SH_R), "foreR": (-60, (220, 248))},
    "point": {"armR": (-118, SH_R), "foreR": (-28, (220, 248)), "armL": (12, SH_L)},
    "shrug": {"armL": (58, SH_L), "foreL": (-95, (80, 248)), "armR": (-58, SH_R), "foreR": (95, (220, 248)),
              "head": (-9, NECK)},
    "shocked": {"armL": (150, SH_L), "armR": (-150, SH_R)},
    "walk": {"legL": (14, HIP), "legR": (-14, HIP), "armL": (-18, SH_L), "armR": (-30, SH_R)},
    "think": {"armR": (-32, SH_R), "foreR": (-148, (220, 248)), "head": (7, NECK)},
    "sneak": {"armL": (70, SH_L), "foreL": (-100, (80, 248)), "armR": (-40, SH_R)},
    "cheer": {"armL": (160, SH_L), "armR": (-160, SH_R)},
    "worried": {"head": (10, NECK), "armL": (26, SH_L), "foreL": (-120, (80, 248))},
}
# where the right hand ends up in each pose (figure space 300 x 520): a held prop goes there
HAND = {"idle": (234, 318), "talk": (262, 230), "point": (300, 120), "shrug": (300, 170), "shocked": (330, 300),
        "walk": (250, 300), "think": (300, 260), "sneak": (230, 280), "cheer": (330, 300), "worried": (234, 318)}


def figure_svg(pose: str, body: str, ink: str = INK, flip: bool = False, outfit: str = "plain") -> str:
    """One stick figure (300 x 520 viewBox content) frozen in a pose."""
    g = F.figure("tf", 0, ink, body, outfit, flip=flip)
    for part, (ang, (ox, oy)) in POSES.get(pose, {}).items():
        g = g.replace(f'<g id="tff0-{part}">', f'<g id="tff0-{part}" transform="rotate({ang} {ox} {oy})">', 1)
    if pose == "shocked":
        g = g.replace('id="tff0-mouth"', 'id="tff0-mouth" opacity="0"').replace(
            'rx="10" ry="13" fill="' + ink + '" opacity="0"', 'rx="13" ry="17" fill="' + ink + '" opacity="1"')
        g = g.replace('r="7" fill', 'r="10" fill')
    elif pose == "worried":
        g = g.replace('d="M132 114 Q150 128 168 114"', 'd="M132 122 Q150 108 168 122"')
        g = g.replace('opacity="0"/>\n      <g id="tff0-acc">', 'opacity="1"/>\n      <g id="tff0-acc">')
    elif pose in ("cheer",):
        g = g.replace('d="M132 114 Q150 128 168 114"', 'd="M128 110 Q150 138 172 110"')
    return g


def figure(role, pose, x, y, h, th, flip=False, prop=None, prop_size=None):
    """A stick figure h px tall at (x, y), optionally holding an icon in its right hand."""
    w = int(h * 300 / 520)
    body = th["accent"]
    svg = (f'<svg data-role="{role}" viewBox="0 0 300 520" style="position:absolute;left:{x}px;top:{y}px;'
           f'width:{w}px;height:{h}px;overflow:visible;filter:drop-shadow(0 0 {int(h * 0.04)}px {th["accent"]}55)">'
           f'{figure_svg(pose, body, flip=flip)}</svg>')
    if prop:
        ps = prop_size or int(h * 0.3)
        hx, hy = HAND.get(pose, (234, 318))
        if flip:
            hx = 300 - hx
        px = x + int(hx * h / 520) - ps // 2
        py = y + int(hy * h / 520) - ps // 2
        svg += sticker("prop", prop, px, py, ps, th, rotate=-6 if not flip else 6)
    return svg


def page(W, H, th, body: str) -> str:
    return (f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_faces()}
html, body {{ margin:0; padding:0; width:{W}px; height:{H}px; overflow:hidden; background:{th['bg']}; }}
.stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}
{TEXT_CSS}
</style><script>{FIT_JS}</script></head><body><div class="stage">{background(th, W, H)}{body}</div></body></html>""")
