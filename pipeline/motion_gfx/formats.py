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
        "weights": {"figure": 0.35, "versus": 0.3, "number": 0.15, "split": 0.25, "reaction": 0.25, "pros_cons": 0.15,
                    "scale": 0.25, "icon_list": 0.2, "pile": 0.2, "map_flag": 0.2},
        "banned": [], "hosts": [],
        "entrances": ["pop", "drop", "skew", "rise"],
        "ease": {"EASE_IN": "expo.out", "EASE_POP": "spring.snappy"},
        "transitions": {"same": ["cut", "cut", "fade"], "next": ["push", "slide", "push_up", "split", "shape"],
                        "shot": ["whip_blur", "zoom_blur", "spin", "cube", "flash", "push"], "reveal": ["zoom", "zoom_through"]},
        "cameras": ["dolly", "truck", "orbit", "handheld", "vertigo", "tilt", "pull"],
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
        "weights": {"browser": 0.5, "phone": 0.5, "table": 0.45, "ticker": 0.3, "magnifier": 0.25, "chat": 0.3,
                    "countdown": 0.25, "process": 0.2, "before_after": 0.2, "split": 0.2, "number": 0.1,
                    "terminal": 0.5, "dashboard": 0.3, "calendar": -0.2, "newspaper": -0.3},
        "banned": ["figure", "reaction", "pile"], "hosts": ["terminal", "dashboard"],
        "entrances": ["rise", "mask", "none", "pop"],
        "ease": {"EASE_IN": "power3.out", "EASE_POP": "spring.soft"},
        "transitions": {"same": ["cut", "fade"], "next": ["slide", "push", "blinds", "luma_wipe"],
                        "shot": ["zoom_blur", "rgb_split", "glitch", "cube", "slide"], "reveal": ["zoom", "zoom_through"]},
        "cameras": ["orbit", "truck", "dolly", "focus", "tilt"],
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
                    "dashboard": 0.55, "magnifier": -0.2, "calendar": -0.1},
        "banned": ["figure", "reaction", "browser", "phone", "chat", "newspaper"], "hosts": ["dashboard"],
        "entrances": ["mask", "rise", "none"],
        "ease": {"EASE_IN": "power3.out", "EASE_POP": "spring.soft"},
        "transitions": {"same": ["cut", "fade"], "next": ["push_up", "blinds", "split", "luma_wipe"],
                        "shot": ["zoom_blur", "flip", "cube", "zoom_out"], "reveal": ["zoom", "zoom_through"]},
        "cameras": ["orbit", "dolly", "vertigo", "truck", "pull"],
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
        "weights": {"figure": 0.3, "checklist": 0.45, "process": 0.4, "cause_effect": 0.4, "pros_cons": 0.35,
                    "venn": 0.35, "before_after": 0.25, "calendar": 0.15, "icon_list": 0.25, "route": 0.2,
                    "sticky": 0.55, "newspaper": -0.3, "magnifier": -0.1},
        "banned": ["ticker"], "hosts": ["sticky"],
        "entrances": ["drop", "rise", "flip"],
        "ease": {"EASE_IN": "power2.out", "EASE_POP": "spring.snappy"},
        "transitions": {"same": ["cut", "fade"], "next": ["slide", "push", "page"],
                        "shot": ["page_curl", "ink", "whip_blur", "slide"], "reveal": ["zoom", "ink"]},
        "cameras": ["handheld", "truck", "tilt", "dolly"],
        "signature": "page", "sfx": {"pop": "paper", "swipe": "paper", "whoosh": "paper", "click": "paper"},
        "music": ["calm", "uplifting"], "kicker": "Lesson",
    },
    "newsroom": {
        "label": "Newsroom",
        "description": "a TV news desk: white and red, headline bars, a ticker, lower thirds, quotes and maps, breaking "
                       "news, announcements, politics, business news, launches, what happened and what was said",
        "palettes": ["news_classic", "news_navy"], "fonts": ["news"],
        "icon_style": ["plain"], "card": "#FFFFFF", "line": "#141414", "line_scale": 0.7, "shadow": "none",
        "backdrop": "news", "rough": False,
        "weights": {"newspaper": 0.5, "ticker": 0.4, "quote": 0.35, "map_flag": 0.35, "globe": 0.3, "lower_third": 0.55,
                    "chat": 0.2, "calendar": 0.25, "timeline": 0.25, "split": 0.2, "magnifier": -0.2},
        "banned": ["figure", "reaction"], "hosts": ["lower_third"],
        "entrances": ["rise", "mask", "none"],
        "ease": {"EASE_IN": "power4.out", "EASE_POP": "spring.soft"},
        "transitions": {"same": ["cut", "cut"], "next": ["bars", "slide", "push"],
                        "shot": ["whip_blur", "flash", "cube", "luma_wipe"], "reveal": ["zoom_blur", "zoom"]},
        "cameras": ["truck", "dolly", "pull", "focus", "orbit"],
        "signature": "flash", "sfx": {"pop": "click", "boing": "click", "paper": "swipe"},
        "music": ["tense", "tech"], "kicker": "Report",
    },
    "case_file": {
        "label": "Case File",
        "description": "dark noir investigation: a desk lamp, folders, memos with stamps, an evidence board with red "
                       "string, redactions, polaroids, allegations, scandals, mysteries, crimes, leaks, spies, secrets",
        "palettes": ["case_noir", "case_slate"], "fonts": ["case"],
        "icon_style": ["plain"], "card": "#F1E6C8", "line": "#1C1712", "line_scale": 0.8, "shadow": "soft",
        "backdrop": "lamp", "rough": False,
        "weights": {"memo": 0.5, "evidence": 0.55, "magnifier": 0.4, "newspaper": 0.3, "quote": 0.35, "timeline": 0.3,
                    "map_flag": 0.3, "route": 0.3, "calendar": 0.2, "cause_effect": 0.25, "chat": 0.15},
        "banned": ["figure", "reaction", "icon_grid", "donut"], "hosts": ["evidence"],
        "entrances": ["mask", "none", "drop"],
        "ease": {"EASE_IN": "power2.out", "EASE_POP": "spring.soft"},
        "transitions": {"same": ["cut", "fade"], "next": ["fade", "slide", "flashlight"],
                        "shot": ["film_burn", "light_leak", "ink", "whip_blur"], "reveal": ["zoom_through", "zoom"]},
        "cameras": ["handheld", "focus", "dolly", "vertigo", "truck"],
        "signature": "flashlight", "sfx": {"pop": "paper", "boing": "stamp", "ding": "typing"},
        "music": ["mystery", "dark", "tense"], "kicker": "Exhibit",
    },
    "arcade_retro": {
        "label": "Arcade Retro",
        "description": "pixel CRT arcade with scanlines and pixel sprites: level and score cards, health bars, versus "
                       "screens, leaderboards, games, gaming, competitions, rivals, challenges, records and battles",
        "palettes": ["arc_night", "arc_green"], "fonts": ["arcade"],
        "icon_style": ["sticker"], "card": "#F8F8F8", "line": "#000000", "line_scale": 1.3, "shadow": "offset",
        "square": True, "backdrop": "crt", "rough": False,
        "weights": {"level": 0.55, "versus": 0.5, "ranking": 0.45, "meter": 0.4, "countdown": 0.3, "scale": 0.25,
                    "reaction": 0.3, "figure": 0.2, "split": 0.25, "number": 0.2, "checklist": 0.2},
        "banned": ["newspaper", "memo"], "hosts": ["level"],
        "entrances": ["pop", "drop", "none"],
        "ease": {"EASE_IN": "steps(6)", "EASE_POP": "steps(5)"},
        "transitions": {"same": ["cut", "cut"], "next": ["pixel", "push", "shake"],
                        "shot": ["rgb_split", "glitch", "spin", "flip"], "reveal": ["zoom", "zoom_blur"]},
        "cameras": ["dolly", "truck", "pull", "handheld"],
        "signature": "pixel", "sfx": {"swipe": "click", "whoosh": "glitch", "paper": "click"},
        "music": ["epic", "tech"], "kicker": "Level",
    },
    "blueprint": {
        "label": "Blueprint",
        "description": "an engineering blueprint: blue grid, white line art, diagrams, exploded parts, process steps, "
                       "cause and effect chains, how something works inside, engineering, design, manufacturing, science",
        "palettes": ["bp_classic", "bp_teal"], "fonts": ["blue"],
        "icon_style": ["plain"], "card": "#2A5CB0", "line": "#EAF2FF", "line_scale": 0.6, "shadow": "none",
        "backdrop": "blueprint", "rough": False,
        "weights": {"diagram": 0.55, "process": 0.5, "cause_effect": 0.45, "funnel": 0.3, "venn": 0.3,
                    "before_after": 0.3, "route": 0.25, "table": 0.25, "scale": 0.2, "figure": 0.1, "magnifier": 0.15},
        "banned": ["reaction", "newspaper", "chat", "phone"], "hosts": ["diagram"],
        "entrances": ["mask", "rise", "none"],
        "ease": {"EASE_IN": "power2.inOut", "EASE_POP": "spring.soft"},
        "transitions": {"same": ["cut", "fade"], "next": ["draw", "slide", "push_up"],
                        "shot": ["luma_wipe", "flip", "cube", "shape"], "reveal": ["zoom_through", "zoom"]},
        "cameras": ["orbit", "tilt", "truck", "pull", "dolly"],
        "signature": "draw", "sfx": {"pop": "click", "boing": "click", "paper": "click"},
        "music": ["calm", "tech"], "kicker": "Section",
    },
}
DEFAULT = "pop_poster"
ALL_HOSTS = {"terminal", "dashboard", "sticky", "lower_third", "evidence", "level", "diagram"}

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
    {"name": "news_white", "bg": "#F4F4F1", "ink": "#141414", "hi": "#FFD23F", "pop": "#D7263D", "soft": "#E3E3DC"},
    {"name": "news_red", "bg": "#C8102E", "ink": "#FFFFFF", "hi": "#FFD23F", "pop": "#FFD23F", "soft": "#D63A52"},
    {"name": "news_navy", "bg": "#13294B", "ink": "#FFFFFF", "hi": "#FFD23F", "pop": "#D7263D", "soft": "#1F3A66"},
    {"name": "news_grey", "bg": "#DCDCD6", "ink": "#141414", "hi": "#FFD23F", "pop": "#C8102E", "soft": "#CACAC2"},
    {"name": "case_noir", "bg": "#15110D", "ink": "#F1E6C8", "hi": "#C8A24A", "pop": "#B3261E", "soft": "#2A221A"},
    {"name": "case_slate", "bg": "#1A1D22", "ink": "#E8E4D8", "hi": "#D9B45A", "pop": "#A32020", "soft": "#2B2F36"},
    {"name": "case_brown", "bg": "#2E2318", "ink": "#F6EEDB", "hi": "#E0C070", "pop": "#B3261E", "soft": "#41331F"},
    {"name": "arc_night", "bg": "#0D0221", "ink": "#FFFFFF", "hi": "#FF2A6D", "pop": "#05D9E8", "soft": "#1E0B45"},
    {"name": "arc_green", "bg": "#071A0B", "ink": "#D7FFD9", "hi": "#FFE600", "pop": "#39FF14", "soft": "#12301A"},
    {"name": "arc_purple", "bg": "#2B0B3F", "ink": "#FFF4FF", "hi": "#FFB000", "pop": "#FF2A6D", "soft": "#3D1659"},
    {"name": "bp_blue", "bg": "#1F4E9C", "ink": "#F2F7FF", "hi": "#0E2F66", "pop": "#FF8A3D", "soft": "#2A5CB0"},
    {"name": "bp_deep", "bg": "#173E80", "ink": "#F2F7FF", "hi": "#0B2554", "pop": "#FF8A3D", "soft": "#22508F"},
    {"name": "bp_teal", "bg": "#0F5163", "ink": "#EFFBFF", "hi": "#08303B", "pop": "#FF9F43", "soft": "#186478"},
]
D.PALETTE_SETS.update({
    "tech_cyan": ["tech_cyan", "tech_navy", "tech_ink"], "tech_violet": ["tech_violet", "tech_navy", "tech_cyan"],
    "lab_neon": ["lab_navy", "lab_ink", "lab_deep"], "lab_sunset": ["lab_plum", "lab_navy", "lab_ink"],
    "paper_yellow": ["paper_cream", "paper_white", "paper_blue"], "paper_mint": ["paper_mint", "paper_cream", "paper_white"],
    "news_classic": ["news_white", "news_red", "news_grey"], "news_navy": ["news_navy", "news_white", "news_grey"],
    "case_noir": ["case_noir", "case_slate", "case_brown"], "case_slate": ["case_slate", "case_noir", "case_brown"],
    "arc_night": ["arc_night", "arc_purple", "arc_green"], "arc_green": ["arc_green", "arc_night", "arc_purple"],
    "bp_classic": ["bp_blue", "bp_deep", "bp_teal"], "bp_teal": ["bp_teal", "bp_blue", "bp_deep"],
})
D.FONTS.update({"hand": ("Patrick Hand", "PatrickHand-Regular.ttf", 400),
                "mono": ("Space Mono", "SpaceMono-Bold.ttf", 700),
                "courier": ("Courier Prime", "CourierPrime-Bold.ttf", 700),
                "cormorant": ("Cormorant SC", "CormorantSC-SemiBold.ttf", 600),
                "pixel": ("Press Start 2P", "PressStart2P-Regular.ttf", 400)})
D.FONT_PAIRS.update({
    "tech": {"head": "Barlow Condensed ExtraBold", "char_w": 0.5, "body": "Space Mono"},
    "lab": {"head": "Anton", "char_w": 0.5, "body": "Space Mono"},
    "hand": {"head": "Patrick Hand", "char_w": 0.46, "body": "Patrick Hand"},
    "news": {"head": "Barlow Condensed ExtraBold", "char_w": 0.48, "body": "Barlow Bold"},
    "case": {"head": "Cormorant SC", "char_w": 0.62, "body": "Courier Prime"},
    "arcade": {"head": "Press Start 2P", "char_w": 1.0, "body": "Space Mono"},
    "blue": {"head": "Barlow Condensed ExtraBold", "char_w": 0.5, "body": "Space Mono"},
})
POP_SETS = ["pop", "warm", "cool", "bold"]
POP_FONTS = ["poster", "condensed", "comic"]


def seed_of(title: str, fmt: str) -> int:
    """The planner's seed: the title AND the format, so one script in two formats makes different choices. Pop Poster
    keeps the title-only seed (videos made before formats re-render the same)."""
    import hashlib
    key = title if (fmt or DEFAULT) == DEFAULT else f"{title}|{fmt}"
    return int(hashlib.sha1(key.encode()).hexdigest()[:6], 16)


def get(name: str) -> dict:
    """A format with its effective banned list (its own bans + every other format's host scenes)."""
    f = FORMATS.get(name or DEFAULT) or FORMATS[DEFAULT]
    return dict(f, banned=sorted(set(f["banned"]) | (ALL_HOSTS - set(f.get("hosts") or []))))


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
    if card == "#FFFFFF" and line == "#111111" and k == 1.0 and shadow == "offset" and not fmt.get("square"):
        return parts

    def fix(s):
        s = re.sub(r"#FFFFFF", card, s, flags=re.I)
        s = re.sub(r"#111111", line, s, flags=re.I)
        if k != 1.0:
            s = re.sub(r"border(-\w+)?:(\d+)px solid", lambda m: f"border{m.group(1) or ''}:{max(2, round(int(m.group(2)) * k))}px solid", s)
        if shadow == "soft":
            s = re.sub(r"box-shadow:\s*(\d+)px (\d+)px 0 [^;\"]+", lambda m: f"box-shadow:0 {m.group(2)}px {int(m.group(2)) * 3}px rgba(0,0,0,0.45)", s)
        elif shadow == "none":
            s = re.sub(r"box-shadow:\s*\d+px \d+px 0 [^;\"]+;?", "", s)
        elif shadow == "glow":
            s = re.sub(r"box-shadow:\s*(\d+)px (\d+)px 0 [^;\"]+", lambda m: f"box-shadow:0 0 {int(m.group(2)) * 3}px rgba(33,243,255,0.35)", s)
        if fmt.get("square"):                    # Arcade: square pixel corners
            s = re.sub(r"border-radius:\s*\d+px(\s+\d+px){0,3}", "border-radius:0", s)
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
    if kind == "news":                       # Newsroom: a red top bar with a LIVE tag, a dark ticker band at the bottom
        return (f'<div style="position:absolute;left:0;right:0;top:0;height:{int(H * .05)}px;background:#C8102E"></div>'
                f'<div style="position:absolute;left:{int(W * .035)}px;top:{int(H * .01)}px;padding:0 .5em;background:#FFFFFF;'
                f'color:#C8102E;font-family:\'Barlow Condensed ExtraBold\';font-size:{int(H * .028)}px;line-height:{int(H * .03)}px">LIVE</div>'
                f'<div style="position:absolute;left:0;right:0;bottom:0;height:{int(H * .045)}px;background:#141414"></div>'
                f'<div style="position:absolute;left:0;width:{int(W * .14)}px;bottom:0;height:{int(H * .045)}px;background:#C8102E"></div>')
    if kind == "lamp":                       # Case File: a desk-lamp cone, a vignette, a folder edge
        return (f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse 55% 70% at 50% 0%,'
                f'rgba(255,220,150,0.16),transparent 70%)"></div>'
                f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 50%,transparent 55%,rgba(0,0,0,0.55))"></div>'
                f'<div style="position:absolute;left:{int(W * .04)}px;bottom:{-int(H * .02)}px;width:{int(W * .25)}px;height:{int(H * .06)}px;'
                f'background:#C9A86A;opacity:.35;border-radius:10px 10px 0 0"></div>')
    if kind == "crt":                        # Arcade: scanlines, a pixel frame, 1UP
        return (f'<div style="position:absolute;inset:0;background-image:repeating-linear-gradient(0deg,rgba(0,0,0,0.25) 0,'
                f'rgba(0,0,0,0.25) 2px,transparent 2px,transparent 5px)"></div>'
                f'<div style="position:absolute;inset:{int(H * .02)}px;border:{max(4, W // 300)}px dashed {pal["pop"]};opacity:.5"></div>'
                f'<div style="position:absolute;left:{int(W * .045)}px;top:{int(H * .045)}px;font-family:\'Press Start 2P\';'
                f'font-size:{int(H * .026)}px;color:{pal["hi"]}">1UP</div>')
    if kind == "blueprint":                  # Blueprint: fine + major grid, a title block in the corner
        g = max(30, W // 48)
        return (f'<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.08) 1px,'
                f'transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.08) 1px,transparent 1px),'
                f'linear-gradient(rgba(255,255,255,0.16) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,0.16) 2px,'
                f'transparent 2px);background-size:{g}px {g}px,{g}px {g}px,{g * 5}px {g * 5}px,{g * 5}px {g * 5}px"></div>'
                f'<div style="position:absolute;right:{int(W * .03)}px;bottom:{int(H * .04)}px;width:{int(W * .16)}px;'
                f'height:{int(H * .08)}px;border:2px solid rgba(255,255,255,0.6)"><div style="position:absolute;left:0;right:0;'
                f'top:50%;height:2px;background:rgba(255,255,255,0.6)"></div></div>')
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


# ------------------------------------------------------------------------------------- show: auto (step 7)
FRESH_PENALTY = 0.06       # per use of a format in the last 10 videos
SIMILAR_WARN = 0.72        # variety.similarity above this = Check warns (names the closest video)


def allowed() -> list:
    """FORMATS_ALLOWED=tech_desk, data_lab in .env limits show: auto to a channel's family of formats."""
    from .. import config as C
    want = [x.strip().lower() for x in C.env("FORMATS_ALLOWED").split(",") if x.strip()]
    return [f for f in FORMATS if f in want] or list(FORMATS)


def _topic_text(meta: dict, title: str) -> str:
    tags = meta.get("tags") or []
    tags = ", ".join(tags) if isinstance(tags, list) else str(tags)
    desc = re.sub(r"https?://\S+", " ", str(meta.get("description") or ""))
    desc = " ".join(line for line in desc.splitlines() if not re.match(r"\s*(sources?:|#)", line, re.I))
    return f"{title}. {tags}. {desc}"[:1200]


def topic_scores(meta: dict, title: str) -> dict:
    """{format: cosine similarity of the script's title/tags/description to the format's description}."""
    from .. import icon_index as IX
    names_ = list(FORMATS)
    vec = IX.embed([_topic_text(meta, title)] + [FORMATS[n]["description"] for n in names_])
    return {n: round(float(vec[0] @ vec[k + 1]), 4) for k, n in enumerate(names_)}


GOAL_BONUS = 0.03           # per variety goal the script meets in a format (planner-only estimate)


def goals_by_format(beats: list, title: str) -> dict:
    """{format: variety goals met} from a quick plan of the script in every format (no icon search)."""
    from . import planner as PL, variety as V
    out = {}
    for n in FORMATS:
        f = get(n)
        seed = seed_of(title, n)
        ex = {i: set(f["banned"]) for i in range(len(beats))}
        names_, _ = PL.plan(beats, seed, ex, f["weights"])
        tr = PL.transitions(beats, names_, seed, f["transitions"], f["signature"])
        out[n] = V.report(names_, PL.variants(names_, seed), tr, beats)["goals_met"]
    return out


def choose_auto(meta: dict, title: str, seen: dict, beats: list = None) -> str:
    """show: auto: topic fit + a bonus per variety goal the script meets in that format - a penalty for every use in
    the last 10 videos; never the format of a video that is rendering right now (two videos started together are
    always different shows)."""
    pool = allowed()
    try:
        goals = goals_by_format(beats, title) if beats else {}
    except Exception:  # noqa: BLE001
        goals = {}
    videos = (seen or {}).get("videos") or []
    used = [((v.get("look") or {}).get("format")) for v in videos]
    busy = {(v.get("look") or {}).get("format") for v in videos if v.get("status") == "rendering"}
    try:
        fit = topic_scores(meta, title)
    except Exception:  # noqa: BLE001  (no search model on this machine: freshness only)
        fit = {n: 0.0 for n in FORMATS}
    cands = [n for n in pool if n not in busy] or pool
    return max(sorted(cands), key=lambda n: fit.get(n, 0) + GOAL_BONUS * goals.get(n, 0) - FRESH_PENALTY * used.count(n))

from . import typography as _TY  # noqa: E402,F401  (registers the typography fonts, palettes and font pairs)

# Type Studio (2026-11-12): kinetic typography is the picture (Raju's reference video): words on flat colour, the
# Swiss type style, the typographic scene types of type_scenes.py as its hosts, a few clean data scenes, no figures,
# icons or app windows.
TYPE_HOSTS = ["type_kicker", "type_wheel", "type_swap", "type_stack", "type_sentence"]
FORMATS["type_studio"] = {
    "label": "Type Studio",
    "description": "minimal Swiss kinetic typography, big words on flat colour, typewriter text, rolling word lists, "
                   "ideas, opinions, explainers, advice, business, marketing, creators, design, productivity and "
                   "self improvement",
    "palettes": ["swiss"], "fonts": ["swiss"], "icon_style": ["plain"],
    "card": "#FFFFFF", "line": "#111111", "line_scale": 0.55, "shadow": "none", "backdrop": None, "rough": False,
    "frames": False, "ambient": False,
    "weights": {"type_kicker": 0.75, "type_wheel": 0.7, "type_swap": 0.7, "type_stack": 0.7, "type_sentence": 0.7,
                "kinetic": 0.35, "ranking": 0.1, "timeline": 0.1, "meter": 0.1, "donut": 0.05, "countdown": 0.05},
    "banned": ["figure", "reaction", "pile", "icon_list", "icon_grid", "memo", "newspaper", "phone", "browser", "chat",
               "ticker", "magnifier", "globe", "route", "map_flag", "calendar", "versus", "scale", "split"],
    "hosts": TYPE_HOSTS,
    "entrances": ["rise", "mask", "none", "none"],
    "ease": {"EASE_IN": "expo.out", "EASE_POP": "spring.soft"},       # smooth motion: springs, like every format
    "cameras": ["dolly", "truck", "pull", "focus"],                    # calm moves for flat type (no orbit/handheld)
    "transitions": {"same": ["cut", "cut", "fade"], "next": ["slide", "push", "blinds"],
                    "shot": ["push_up", "slide", "flash"], "reveal": ["zoom"]},
    "signature": "split", "sfx": {"boing": "click", "paper": "swipe"}, "music": ["tech", "calm", "uplifting"],
    "kicker": "Part",
}
ALL_HOSTS |= set(TYPE_HOSTS)
_TY.POOLS["type_studio"] = ["swiss", "editorial"]
