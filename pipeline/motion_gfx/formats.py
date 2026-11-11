"""Formats: one show package per video (docs/VARIETY_PLAN.md section 3). Motion graphics only.

A format bundles: palettes (design.PALETTES names, one set per format), font pairs, icon families + icon style,
the card / line colours its panels use, line weight and shadow style, a background treatment drawn under every
scene (+ an optional hand-drawn wobble), scene-type weights and banned types (the "host device": no stick figures
in Tech Desk / Data Lab), the entrance pool, easing, transition groups + a signature chapter transition, sound
mapping and music moods.

Within a format the seeded look (history.choose_look) picks one palette set, font pair and icon family, so two
videos of one format still differ. Header: show: pop_poster | tech_desk | data_lab | paper_notebook (step 7 adds
show: auto = topic fit + freshness). The key is show: because format: already means landscape / vertical. Everything is code-drawn; fonts are OFL (assets/fonts/licences).
"""

import re

from . import design as D

FORMATS = {
    "pop_poster": {
        "label": "Pop Poster",
        "description": "bright solid colours, thick outlines, stick figures acting out the story, big numbers, versus "
                       "face-offs, energetic explainer about people, money, drama, news and everyday life",
        "palettes": ["pop", "warm", "cool", "bold"], "fonts": ["poster", "condensed", "comic"],
        "icon_style": ["sticker"], "card": "#FFFFFF", "line": "#111111", "line_scale": 1.0, "shadow": "offset",
        "backdrop": None, "rough": False,
        "weights": {"figure": 0.15, "versus": 0.2, "number": 0.1, "split": 0.15, "reaction": 0.15, "pros_cons": 0.1,
                    "scale": 0.15, "icon_list": 0.1},
        "banned": ["dashboard", "terminal", "sticky"],
        "entrances": ["pop", "drop", "skew", "rise"],
        "ease": {"EASE_IN": "expo.out", "EASE_POP": "back.out(2.2)"},
        "transitions": {"same": ["cut", "cut", "fade"], "next": ["push", "slide", "push_up", "split"],
                        "shot": ["whip", "push", "zoom_out", "flash"], "reveal": ["zoom"]},
        "signature": "wipe", "sfx": {}, "music": ["uplifting", "tech"], "kicker": "Chapter",
    },
    "tech_desk": {
        "label": "Tech Desk",
        "description": "dark desktop UI with glass panels and a grid, app windows, browser tabs, phone screens, "
                       "notifications, spec sheets and benchmarks, about gadgets, software, laptops, chips, apps, AI "
                       "and the tech industry",
        "palettes": ["tech_cyan", "tech_violet"], "fonts": ["tech"],
        "icon_style": ["plain"], "card": "#EAF2FF", "line": "#0B1222", "line_scale": 0.55, "shadow": "soft",
        "backdrop": "grid", "rough": False,
        "weights": {"browser": 0.35, "phone": 0.35, "table": 0.35, "ticker": 0.25, "magnifier": 0.2, "chat": 0.15,
                    "countdown": 0.2, "process": 0.15, "before_after": 0.15, "split": 0.15, "number": 0.1,
                    "terminal": 0.35, "dashboard": 0.2},
        "banned": ["figure", "sticky"],
        "entrances": ["rise", "mask", "none", "pop"],
        "ease": {"EASE_IN": "power3.out", "EASE_POP": "back.out(1.4)"},
        "transitions": {"same": ["cut", "fade"], "next": ["slide", "push", "blinds"],
                        "shot": ["zoom", "glitch", "zoom_out", "slide"], "reveal": ["zoom"]},
        "signature": "glitch", "sfx": {"pop": "click", "swipe": "whoosh", "paper": "keyboard-enter", "boing": "click"},
        "music": ["tech", "calm"], "kicker": "Section",
    },
    "data_lab": {
        "label": "Data Lab",
        "description": "deep navy with neon accents, the data is the hero: charts, counters, rankings, donuts, icon "
                       "grids, percentages, prices, statistics, markets, economics, research and comparisons by numbers",
        "palettes": ["lab_neon", "lab_sunset"], "fonts": ["lab"],
        "icon_style": ["plain"], "card": "#E9FBFF", "line": "#070B26", "line_scale": 0.6, "shadow": "glow",
        "backdrop": "dots", "rough": False,
        "weights": {"chart": 0.3, "number": 0.3, "donut": 0.4, "icon_grid": 0.4, "ranking": 0.4, "table": 0.3,
                    "meter": 0.3, "funnel": 0.35, "ticker": 0.3, "timeline": 0.2, "scale": 0.2, "venn": 0.15,
                    "dashboard": 0.4},
        "banned": ["figure", "reaction", "browser", "phone", "chat", "newspaper", "terminal", "sticky"],
        "entrances": ["mask", "rise", "none"],
        "ease": {"EASE_IN": "power3.out", "EASE_POP": "back.out(1.2)"},
        "transitions": {"same": ["cut", "fade"], "next": ["push_up", "blinds", "split"],
                        "shot": ["zoom", "zoom_out", "push_up"], "reveal": ["zoom"]},
        "signature": "zoom", "sfx": {"pop": "tick", "boing": "tick", "paper": "tick"},
        "music": ["tech", "calm"], "kicker": "Part",
    },
    "paper_notebook": {
        "label": "Paper Notebook",
        "description": "a paper notebook with ruled lines, doodles, tape, sticky notes, arrows, checklists and "
                       "hand-drawn figures, a friendly teacher explaining how something works, habits, history, "
                       "advice, step by step lessons",
        "palettes": ["paper_yellow", "paper_mint"], "fonts": ["hand"],
        "icon_style": ["sticker"], "card": "#FFFDF5", "line": "#1F2A44", "line_scale": 0.8, "shadow": "offset",
        "backdrop": "ruled", "rough": True,
        "weights": {"figure": 0.2, "checklist": 0.4, "process": 0.35, "cause_effect": 0.35, "pros_cons": 0.3,
                    "venn": 0.3, "before_after": 0.2, "calendar": 0.15, "icon_list": 0.2, "route": 0.15,
                    "sticky": 0.4},
        "banned": ["ticker", "dashboard", "terminal"],
        "entrances": ["drop", "rise", "flip"],
        "ease": {"EASE_IN": "power2.out", "EASE_POP": "back.out(1.7)"},
        "transitions": {"same": ["cut", "fade"], "next": ["slide", "push", "page"],
                        "shot": ["page", "zoom_out", "slide"], "reveal": ["zoom_out"]},
        "signature": "page", "sfx": {"pop": "paper", "swipe": "paper", "whoosh": "paper", "click": "paper"},
        "music": ["calm", "uplifting"], "kicker": "Lesson",
    },
}
DEFAULT = "pop_poster"

# the palettes and font pairs the formats add to design.py
D.PALETTES += [
    {"name": "tech_cyan", "bg": "#0E1422", "ink": "#E9F1FF", "hi": "#3DDBFF", "pop": "#3DDBFF", "soft": "#1A2336"},
    {"name": "tech_navy", "bg": "#121A2C", "ink": "#F2F6FF", "hi": "#5CF0C8", "pop": "#5CF0C8", "soft": "#1E2942"},
    {"name": "tech_violet", "bg": "#130F24", "ink": "#F1EDFF", "hi": "#A98BFF", "pop": "#A98BFF", "soft": "#221B3D"},
    {"name": "tech_ink", "bg": "#0B1118", "ink": "#E6F4F1", "hi": "#FFC94D", "pop": "#FFC94D", "soft": "#18222D"},
    {"name": "lab_navy", "bg": "#0A1033", "ink": "#FFFFFF", "hi": "#21F3FF", "pop": "#FF3DCB", "soft": "#17205A"},
    {"name": "lab_ink", "bg": "#0D0B2B", "ink": "#F5F3FF", "hi": "#B6FF3B", "pop": "#21F3FF", "soft": "#1D1A4F"},
    {"name": "lab_plum", "bg": "#1A0B2E", "ink": "#FFF4FB", "hi": "#FF8A3D", "pop": "#FFD23D", "soft": "#2D1A4A"},
    {"name": "lab_deep", "bg": "#06162B", "ink": "#EFFFFB", "hi": "#3DFFB0", "pop": "#FF5E7E", "soft": "#10284A"},
    {"name": "paper_cream", "bg": "#FBF6E9", "ink": "#1F2A44", "hi": "#FFE066", "pop": "#FF6B6B", "soft": "#EFE5C9"},
    {"name": "paper_white", "bg": "#F7F5EF", "ink": "#22304A", "hi": "#FFD166", "pop": "#4D96FF", "soft": "#E7E2D4"},
    {"name": "paper_mint", "bg": "#EEF6EE", "ink": "#1E3330", "hi": "#B8F2D0", "pop": "#FF7A59", "soft": "#DCEBDC"},
    {"name": "paper_blue", "bg": "#EEF3FA", "ink": "#1D2B45", "hi": "#FFE08A", "pop": "#E8505B", "soft": "#DCE5F2"},
]
D.PALETTE_SETS.update({
    "tech_cyan": ["tech_cyan", "tech_navy", "tech_ink"], "tech_violet": ["tech_violet", "tech_navy", "tech_cyan"],
    "lab_neon": ["lab_navy", "lab_ink", "lab_deep"], "lab_sunset": ["lab_plum", "lab_navy", "lab_ink"],
    "paper_yellow": ["paper_cream", "paper_white", "paper_blue"], "paper_mint": ["paper_mint", "paper_cream", "paper_white"],
})
D.FONTS.update({"hand": ("Patrick Hand", "PatrickHand-Regular.ttf", 400),
                "mono": ("Space Mono", "SpaceMono-Bold.ttf", 700)})
D.FONT_PAIRS.update({
    "tech": {"head": "Barlow Condensed ExtraBold", "char_w": 0.5, "body": "Space Mono"},
    "lab": {"head": "Anton", "char_w": 0.5, "body": "Space Mono"},
    "hand": {"head": "Patrick Hand", "char_w": 0.46, "body": "Patrick Hand"},
})
POP_SETS = ["pop", "warm", "cool", "bold"]
POP_FONTS = ["poster", "condensed", "comic"]


def get(name: str) -> dict:
    return FORMATS.get(name or DEFAULT) or FORMATS[DEFAULT]


def names() -> list:
    return list(FORMATS)


# ------------------------------------------------------------------------------------------- applying a format
_ORIG_EASE = {"EASE_IN": D.EASE_IN, "EASE_POP": D.EASE_POP}


def apply_motion(fmt: dict) -> None:
    """Easing of the format, set before the scenes are built (templates read design.EASE_* when they build)."""
    for k, v in _ORIG_EASE.items():
        setattr(D, k, (fmt.get("ease") or {}).get(k, v))


def restyle(parts: dict, fmt: dict) -> dict:
    """The format's card / line colours, line weight and shadow style on a built scene (html + css)."""
    card, line, k, shadow = fmt["card"], fmt["line"], fmt["line_scale"], fmt["shadow"]
    if card == "#FFFFFF" and line == "#111111" and k == 1.0 and shadow == "offset":
        return parts

    def fix(s):
        s = re.sub(r"#FFFFFF", card, s, flags=re.I)
        s = re.sub(r"#111111", line, s, flags=re.I)
        if k != 1.0:
            s = re.sub(r"border(-\w+)?:(\d+)px solid", lambda m: f"border{m.group(1) or ''}:{max(2, round(int(m.group(2)) * k))}px solid", s)
        if shadow == "soft":
            s = re.sub(r"box-shadow:\s*(\d+)px (\d+)px 0 [^;\"]+", lambda m: f"box-shadow:0 {m.group(2)}px {int(m.group(2)) * 3}px rgba(0,0,0,0.45)", s)
        elif shadow == "glow":
            s = re.sub(r"box-shadow:\s*(\d+)px (\d+)px 0 [^;\"]+", lambda m: f"box-shadow:0 0 {int(m.group(2)) * 3}px rgba(33,243,255,0.35)", s)
        return s
    return dict(parts, html=fix(parts["html"]), css=fix(parts["css"]))


def backdrop_html(fmt: dict, pal: dict, W: int, H: int) -> str:
    kind = fmt.get("backdrop")
    if kind == "grid":                       # Tech Desk: a UI grid, corner brackets, a thin status bar
        g = max(40, W // 30)
        b = max(3, W // 640)
        return (f'<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.05) 1px,'
                f'transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.05) 1px,transparent 1px);'
                f'background-size:{g}px {g}px"></div>'
                f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(255,255,255,0.06),'
                f'rgba(0,0,0,0.35) 80%)"></div>'
                f'<div style="position:absolute;left:0;right:0;top:0;height:{int(H * .045)}px;background:rgba(255,255,255,0.05);'
                f'border-bottom:{b}px solid rgba(255,255,255,0.08)"></div>'
                + "".join(f'<div style="position:absolute;{v}:{int(H * .06)}px;{h_}:{int(W * .03)}px;width:{int(W * .03)}px;'
                          f'height:{int(W * .03)}px;border-{v}:{b * 2}px solid {pal["pop"]};border-{h_}:{b * 2}px solid {pal["pop"]};'
                          f'opacity:.7"></div>' for v in ("top", "bottom") for h_ in ("left", "right")))
    if kind == "dots":                       # Data Lab: a dot grid and a neon glow
        g = max(36, W // 40)
        return (f'<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,0.14) 2px,'
                f'transparent 2.5px);background-size:{g}px {g}px"></div>'
                f'<div style="position:absolute;left:{int(W * .55)}px;top:{-int(H * .3)}px;width:{int(W * .7)}px;'
                f'height:{int(W * .7)}px;border-radius:50%;background:radial-gradient({pal["pop"]}33,transparent 65%)"></div>'
                f'<div style="position:absolute;left:{int(W * .05)}px;right:{int(W * .05)}px;bottom:{int(H * .05)}px;'
                f'height:2px;background:rgba(255,255,255,0.18)"></div>')
    if kind == "ruled":                      # Paper Notebook: ruled lines, a red margin, a piece of tape
        g = max(36, H // 22)
        return (f'<div style="position:absolute;inset:0;background-image:repeating-linear-gradient(transparent 0,'
                f'transparent {g - 2}px,rgba(70,110,200,0.22) {g - 2}px,rgba(70,110,200,0.22) {g}px)"></div>'
                f'<div style="position:absolute;top:0;bottom:0;left:{int(W * .075)}px;width:3px;background:rgba(230,80,90,0.45)"></div>'
                f'<div style="position:absolute;left:{int(W * .80)}px;top:{int(H * .02)}px;width:{int(W * .12)}px;'
                f'height:{int(H * .055)}px;background:rgba(255,225,120,0.6);transform:rotate(6deg)"></div>')
    return ""


ROUGH_FILTER = ('<svg width="0" height="0" style="position:absolute"><filter id="rough"><feTurbulence type="fractalNoise" '
                'baseFrequency="0.035" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="4"/>'
                '</filter></svg>')
