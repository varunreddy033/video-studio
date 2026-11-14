"""Typography of the motion graphics renderer (rendering_method: motion): how on-screen words look and move.

One type style per video (header `typography:`, default auto). A style bundles
  fonts      a font pair (design.FONT_PAIRS) or None = keep the format's own fonts (pixel, hand, ...)
  case       upper | as_is (the Swiss and editorial styles keep the script's own capitals)
  effect     the headline treatment: clean, outline (thick stroke + hard shadow), extrude (3D block),
             gradient (vertical gradient fill), neon (glow), marker (key words on tilted boxes), editorial
  emphasis   how the key words of a line differ (numbers first, then names, then long words: templates.key_words):
             weight + accent colour, accent fill, italic + underline swipe, marker box
  entrances  the word animations this style rotates through, one per text scene, never twice in a row:
             pop, punch, letters, drop, mask, type (typewriter with a caret), wheel (slot-machine word roll),
             weight (variable-font weight sweep), scramble (glyphs settle into letters), flicker
  deco       swiss only: hairline crosshair + small mono corner labels (scene counter, chapter) when the format
             draws no backdrop of its own

auto = the format's pool (POOLS), the style the last 5 videos used least (history.choose_look). typography: classic
= the look from before this module (byte-for-byte the old scene code). Classic ai_image videos never use this.

Big headline text drawn by the other scene types (scenes.py, extras.py) gets the style's effect too: apply() tags
every text element in the headline font that is large and in the palette's ink colour (text on the backdrop).
"""

import re

from . import design as D

# ------------------------------------------------------------------------------------------------- fonts
D.FONTS.update({"inter": ("Inter", "InterVariable.ttf", "100 900"),          # variable: weight 100-900 (OFL)
                "bebas": ("Bebas Neue", "BebasNeue-Regular.ttf", 400),
                "archivo": ("Archivo Black", "ArchivoBlack-Regular.ttf", 400),
                "dmserif": ("DM Serif Display", "DMSerifDisplay-Regular.ttf", 400),
                "dmserif_i": ("DM Serif Display Italic", "DMSerifDisplay-Italic.ttf", 400)})
D.FONT_PAIRS.update({
    "swiss": {"head": "Inter", "char_w": 0.62, "body": "Inter"},
    "impact": {"head": "Bebas Neue", "char_w": 0.42, "body": "Barlow Bold"},
    "heavy": {"head": "Archivo Black", "char_w": 0.8, "body": "Poppins SemiBold"},
    "editorial": {"head": "DM Serif Display", "char_w": 0.6, "body": "Barlow Medium"},
})
D.FONTS.setdefault("medium", ("Barlow Medium", "Barlow-Medium.ttf", 500))

# the reference look (clean paper, ink, electric blue, sky, cream; one red accent)
D.PALETTES += [
    {"name": "sw_paper", "bg": "#F2F1EC", "ink": "#121212", "hi": "#FFD84D", "pop": "#E8213A", "soft": "#E2E0D8"},
    {"name": "sw_ink", "bg": "#17191F", "ink": "#F4F4F0", "hi": "#E8213A", "pop": "#FF3B5C", "soft": "#252832"},
    {"name": "sw_blue", "bg": "#2B2BEA", "ink": "#FFFFFF", "hi": "#FFD84D", "pop": "#FF5C7A", "soft": "#4545F0"},
    {"name": "sw_cream", "bg": "#F5E6C4", "ink": "#1A1A1A", "hi": "#FFFFFF", "pop": "#E8213A", "soft": "#EBD8AE"},
    {"name": "sw_sky", "bg": "#BFE2F2", "ink": "#121212", "hi": "#FFFFFF", "pop": "#E8213A", "soft": "#A8D4E8"},
]
D.PALETTE_SETS.update({"swiss": ["sw_paper", "sw_blue", "sw_ink", "sw_cream", "sw_sky"]})

# ------------------------------------------------------------------------------------------------- styles
STYLES = {
    "classic": {"label": "Classic", "description": "The look from before typography styles: poster caps, the old "
                "pop-in words and the yellow marker under key words.",
                "fonts": None, "case": "upper", "effect": "classic", "emphasis": "marker", "entrances": ["pop"]},
    "swiss": {"label": "Swiss kinetic", "description": "Clean Inter in the script's own capitals, light words and "
              "one heavy accent word, a red full stop, typewriter caret, slot-machine word roll, weight sweeps, "
              "hairline grid and mono corner labels.",
              "fonts": "swiss", "case": "as_is", "effect": "clean", "emphasis": "weight",
              "entrances": ["type", "wheel", "weight", "mask", "scramble"], "palette": "swiss", "deco": True},
    "outline_pop": {"label": "Outline pop", "description": "White letters with a thick dark outline and a hard "
                    "offset shadow, key words in the accent colour.",
                    "fonts": None, "case": "upper", "effect": "outline", "emphasis": "fill",
                    "entrances": ["pop", "punch", "letters", "drop"]},
    "extrude": {"label": "3D extrude", "description": "Letters with a solid 3D block side in the accent colour "
                "and a dark edge, key words flipped.", "fonts": None, "case": "upper", "effect": "extrude",
                "emphasis": "fill", "entrances": ["punch", "drop", "letters"]},
    "gradient": {"label": "Gradient", "description": "Tall condensed Bebas Neue filled with a vertical gradient "
                 "from the ink to the accent colour, words rising out of a mask.",
                 "fonts": "impact", "case": "upper", "effect": "gradient", "emphasis": "fill",
                 "entrances": ["mask", "letters", "punch"]},
    "neon": {"label": "Neon glow", "description": "Light letters with a soft coloured glow (best on dark formats), "
             "flicker and scramble entrances.", "fonts": None, "case": "upper", "effect": "neon",
             "emphasis": "fill", "entrances": ["flicker", "scramble", "type"]},
    "marker": {"label": "Marker boxes", "description": "Key words on tilted highlight boxes with a hard shadow, the "
               "rest plain.", "fonts": None, "case": "upper", "effect": "marker", "emphasis": "box",
               "entrances": ["pop", "mask", "letters"]},
    "editorial": {"label": "Editorial serif", "description": "DM Serif Display in the script's own capitals, the key "
                  "word in italic accent colour with an underline swipe.",
                  "fonts": "editorial", "case": "as_is", "effect": "editorial", "emphasis": "italic",
                  "entrances": ["mask", "letters", "type"]},
}
DEFAULT = "auto"

# which styles each format may take (auto rotates inside its pool)
POOLS = {"pop_poster": ["outline_pop", "extrude", "swiss", "marker", "gradient"],
         "tech_desk": ["swiss", "neon", "gradient"],
         "data_lab": ["neon", "swiss", "gradient"],
         "paper_notebook": ["marker", "outline_pop"],
         "newsroom": ["swiss", "editorial", "extrude"],
         "case_file": ["editorial", "neon", "marker"],
         "arcade_retro": ["extrude", "neon"],
         "blueprint": ["swiss", "outline_pop"]}

# extra font pairs the formats may rotate (look part "fonts"); formats.py keeps its own lists
EXTRA_FONTS = {"pop_poster": ["impact", "heavy"], "tech_desk": ["swiss"], "data_lab": ["impact"],
               "newsroom": ["impact", "swiss"], "blueprint": ["swiss"]}


def names() -> list:
    return list(STYLES)


def pool(fmt: str) -> list:
    return list(POOLS.get(fmt or "pop_poster") or POOLS["pop_poster"])


# ------------------------------------------------------------------------------------------------ the video's style
STYLE = dict(STYLES["classic"], id="classic")


def set_style(style_id: str) -> dict:
    """Sets the style for this render (renders run one at a time, like templates.set_look)."""
    global STYLE
    STYLE = dict(STYLES.get(style_id) or STYLES["classic"], id=style_id if style_id in STYLES else "classic")
    return STYLE


def classic() -> bool:
    return STYLE["id"] == "classic"


def case(text: str) -> str:
    return text.upper() if STYLE["case"] == "upper" else text


def size_k() -> float:
    """Headline size factor: strokes and 3D sides need a little room."""
    return {"outline": 0.92, "extrude": 0.9, "neon": 0.94}.get(STYLE["effect"], 1.0)


def entrance_for(i: int, seed: int) -> str:
    kinds = STYLE["entrances"]
    return kinds[(seed + i) % len(kinds)]


# --------------------------------------------------------------------------------------------------- markup
GLYPHS = "#%&@*+=/<>?!$■▲●◆✦"


def chars_html(word: str, cls: str = "ch") -> str:
    """A word split into letter spans (GSAP SplitText-style, done in Python so seeking is deterministic)."""
    out = []
    for c in word:
        if c == " ":
            out.append(" ")
        else:
            e = re.sub(r"[&<>\"]", lambda m: {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[m.group(0)], c)
            out.append(f'<span class="{cls}" data-c="{e}">{e}</span>')
    return "".join(out)


def word_html(word: str, kind: str, esc) -> str:
    """The inside of one word span: letters split when the entrance needs them, the Swiss style's final
    full stop / question mark in the accent colour."""
    tail = ""
    if STYLE.get("id") == "swiss" and re.search(r"[.?!]$", word) and len(word) > 1:
        word, tail = word[:-1], word[-1]
    split = kind in ("letters", "type", "scramble")
    body = chars_html(word) if split else esc(word)
    if tail:
        body += f'<span class="ty-dot{" ch" if split else ""}" data-c="{esc(tail)}">{esc(tail)}</span>'
    if kind == "type":
        body += '<span class="ty-caret"></span>'
    return body


def wheel_html(key: str, alts: list, esc) -> str:
    """Slot-machine roll: a column of other words of the video that rolls up and stops on the key word."""
    col = "".join(f'<span class="whw">{esc(a)}</span>' for a in alts) + f'<span class="whw">{esc(key)}</span>'
    return (f'<span class="whl"><span class="whsz">{esc(key)}</span><span class="whc" data-n="{len(alts)}">{col}'
            f'</span></span>')


# ------------------------------------------------------------------------------------------------- animation
def word_js(kind: str, sel: str, t: float, size: int, rot: int = 0, dur: float = 0.4, key: bool = False) -> list:
    """GSAP for one word (sel = its span) entering at t (scene time). Returns a list of statements."""
    E = D.EASE_IN
    ch = f"{sel} .ch"
    if kind == "punch":
        return [f'tl.fromTo("{sel}", {{opacity: 0, scale: 2.3, filter: "blur(10px)"}}, {{opacity: 1, scale: 1, '
                f'filter: "blur(0px)", duration: 0.34, ease: "power4.out"}}, {t:.3f});']
    if kind == "drop":
        return [f'tl.fromTo("{sel}", {{opacity: 0, y: {-int(size * 1.1)}}}, {{opacity: 1, y: 0, duration: 0.5, '
                f'ease: "bounce.out"}}, {t:.3f});']
    if kind == "mask":
        return [f'tl.fromTo("{sel}", {{clipPath: "inset(0% 0% 100% 0%)", y: {int(size * 0.6)}}}, '
                f'{{clipPath: "inset(-20% -10% -25% -10%)", y: 0, duration: 0.45, ease: "{E}"}}, {t:.3f});']
    if kind == "letters":
        return [f'tl.set("{sel}", {{opacity: 1}}, {t:.3f});',
                f'tl.fromTo("{ch}", {{opacity: 0, y: {int(size * 0.45)}, rotation: 8}}, {{opacity: 1, y: 0, rotation: 0, '
                f'duration: 0.32, ease: "back.out(2)", stagger: 0.028}}, {t:.3f});']
    if kind == "type":
        step = max(0.018, min(0.05, dur / 9))
        return [f'tl.set("{sel}", {{opacity: 1}}, {t:.3f});',
                f'tl.fromTo("{ch}", {{display: "none"}}, {{display: "inline", duration: 0.001, stagger: {step:.3f}}}, {t:.3f});',
                f'tl.set("{sel} .ty-caret", {{opacity: 1}}, {t:.3f});']
    if kind == "weight":
        w = 820 if key else 360
        return [f'tl.fromTo("{sel}", {{opacity: 0, fontWeight: 100, letterSpacing: "0.22em"}}, {{opacity: 1, '
                f'fontWeight: {w}, letterSpacing: "-0.02em", duration: 0.55, ease: "power3.out"}}, {t:.3f});']
    if kind == "scramble":
        return [f'tl.set("{sel}", {{opacity: 1}}, {t:.3f});',
                f'tl.fromTo("{ch}", {{opacity: 0}}, {{opacity: 1, duration: 0.05, stagger: 0.02}}, {t:.3f});',
                f'__scr("{sel}", {t:.3f}, 0.42);']
    if kind == "flicker":
        return [f'tl.fromTo("{sel}", {{opacity: 0}}, {{opacity: 1, duration: 0.3, ease: "steps(4)"}}, {t:.3f});',
                f'tl.fromTo("{sel}", {{opacity: 1}}, {{opacity: 0.25, duration: 0.04, yoyo: true, repeat: 3, '
                f'ease: "none"}}, {t + 0.32:.3f});']
    if kind == "wheel":                       # the word itself just appears; its column rolls (wheel_js)
        return [f'tl.fromTo("{sel}", {{opacity: 0}}, {{opacity: 1, duration: 0.15}}, {t:.3f});']
    # pop (the original kinetic entrance)
    return [f'tl.fromTo("{sel}", {{opacity: 0, y: {int(size * 0.35)}, scale: 0.55, rotation: {rot}}}, '
            f'{{opacity: 1, y: 0, scale: 1, rotation: 0, duration: {D.WORD_IN}, ease: "{D.EASE_POP}"}}, {t:.3f});']


def wheel_js(sel: str, t: float, n: int) -> list:
    return [f'tl.fromTo("{sel} .whc", {{yPercent: 0}}, {{yPercent: {-100 * n / (n + 1):.4f}, duration: 0.85, '
            f'ease: "power4.out"}}, {t:.3f});',
            f'tl.fromTo("{sel} .whw", {{opacity: 0.35}}, {{opacity: 1, duration: 0.2}}, {t + 0.7:.3f});']


def caret_off_js(sel: str, t: float) -> str:
    return f'tl.set("{sel} .ty-caret", {{opacity: 0}}, {t:.3f});'


def caret_blink_js(sel: str, t: float, until: float) -> str:
    n = max(1, int((until - t) / 0.5))
    return (f'tl.fromTo("{sel} .ty-caret", {{opacity: 1}}, {{opacity: 0, duration: 0.25, yoyo: true, repeat: {n}, '
            f'ease: "steps(1)", immediateRender: false}}, {t:.3f});')


def emphasis_js(sel: str, t: float) -> list:
    """The extra move of a key word after it lands (underline swipe, box swing, accent pulse)."""
    e = STYLE["emphasis"]
    if e == "italic":
        return [f'tl.fromTo("{sel}", {{backgroundSize: "0% 0.07em"}}, {{backgroundSize: "100% 0.07em", duration: 0.4, '
                f'ease: "{D.EASE_IN}"}}, {t + 0.2:.3f});']
    if e == "box":
        return [f'tl.fromTo("{sel}", {{rotation: 6}}, {{rotation: -2, duration: 0.4, ease: "back.out(3)"}}, {t + 0.05:.3f});']
    if e in ("fill", "weight"):
        return [f'tl.fromTo("{sel}", {{scale: 1}}, {{scale: 1.08, duration: 0.14, yoyo: true, repeat: 1, '
                f'ease: "power2.out"}}, {t + 0.3:.3f});']
    return []


SCRAMBLE_JS = ("function __scr(sel, at, d) { const G = " + repr(GLYPHS) + "; "
               "const els = Array.from(document.querySelectorAll(sel + ' .ch')); const n = els.length || 1; "
               "tl.to({p: 0}, {p: 1, duration: d, ease: 'none', onUpdate: function () { const p = this.progress(); "
               "els.forEach((e, k) => { e.textContent = p >= (k + 1) / n ? e.dataset.c : "
               "G[(k * 7 + Math.floor(p * 24)) % G.length]; }); }}, at); }\n")


# ---------------------------------------------------------------------------------------------------- CSS
def _contrast(hex_colour: str) -> str:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[k:k + 2], 16) for k in (0, 2, 4))
    return "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


def _accent(pal) -> str:
    return pal["pop"] if pal["pop"].upper() != pal["bg"].upper() else pal["hi"]


def css(pal: dict, scope: str = "") -> str:
    """The style's CSS for one scene: .ty-h = a headline, .ty-key = a key word, .ty-dot, .ty-caret, the wheel."""
    s = scope
    eff, acc, ink = STYLE["effect"], _accent(pal), pal["ink"]
    out = [f"{s} .ty-caret {{ display:inline-block; width:0.07em; height:0.82em; margin-left:0.05em; "
           f"vertical-align:-0.06em; background:{acc}; opacity:0; }}",
           f"{s} .ty-dot {{ color:{acc} !important; -webkit-text-fill-color:{acc}; }}",
           f"{s} .whl {{ position:relative; display:inline-block; overflow:hidden; vertical-align:bottom; "
           f"line-height:1.1; height:1.1em; }} {s} .whsz {{ visibility:hidden; }}",
           f"{s} .whc {{ position:absolute; left:0; right:0; top:0; display:flex; flex-direction:column; "
           f"align-items:center; }} {s} .whw {{ display:block; height:1.1em; white-space:nowrap; }}",
           f"{s} .ch {{ display:inline-block; }}"]
    if eff == "clean":
        out.append(f"{s} .ty-h {{ letter-spacing:-0.025em; font-weight:640; }} {s} .ty-h .ty-lt {{ font-weight:340; }}"
                   f"{s} .ty-h .ty-key {{ font-weight:820; color:{acc} !important; }}")
    elif eff == "outline":
        out.append(f"{s} .ty-h {{ color:#FFFFFF !important; -webkit-text-stroke:0.11em #111111; paint-order:stroke fill; "
                   f"text-shadow:0.06em 0.07em 0 #111111 !important; letter-spacing:0.01em; }}"
                   f"{s} .ty-h .ty-key {{ color:{acc if acc.upper() != '#FFFFFF' else pal['hi']} !important; }}")
    elif eff == "extrude":
        side = acc if acc.upper() != ink.upper() else pal["hi"]
        stack = ", ".join(f"{0.012 * k:.3f}em {0.012 * k:.3f}em 0 {side}" for k in range(1, 9))
        out.append(f"{s} .ty-h {{ color:{ink} !important; text-shadow:{stack}, 0.11em 0.11em 0 #111111, "
                   f"0.14em 0.16em 0.12em rgba(0,0,0,0.25) !important; }}"
                   f"{s} .ty-h .ty-key {{ color:{side} !important; text-shadow:" +
                   ", ".join(f"{0.012 * k:.3f}em {0.012 * k:.3f}em 0 {ink}" for k in range(1, 9)) +
                   ", 0.11em 0.11em 0 #111111 !important; }")
    elif eff == "gradient":
        g = f"linear-gradient(180deg, {ink} 0%, {ink} 38%, {acc} 100%)"
        gk = f"linear-gradient(180deg, {pal['hi']} 0%, {acc} 100%)"
        # only elements that hold text themselves (a clipped container would paint its children's text twice)
        leaf = f"{s} .ty-h:not(:has(span)), {s} .ty-h span:not(:has(span)):not(.mk):not(.ty-caret)"
        out.append(f"{leaf} {{ background-image:{g}; -webkit-background-clip:text; background-clip:text; "
                   f"-webkit-text-fill-color:transparent; }} {s} .ty-h {{ text-shadow:none !important; }}"
                   f"{s} .ty-h .ty-key:not(:has(span)), {s} .ty-h .ty-key span:not(:has(span)):not(.mk) "
                   f"{{ background-image:{gk}; }}"
                   f"{s} .ty-h .ty-dot {{ background-image:none; -webkit-text-fill-color:{acc}; }}")
    elif eff == "neon":
        glow = acc if acc.upper() != "#FFFFFF" else pal["hi"]
        light = "#FFFFFF" if _contrast(pal["bg"]) == "#FFFFFF" else ink
        out.append(f"{s} .ty-h {{ color:{light} !important; text-shadow:0 0 0.03em #FFFFFF, 0 0 0.1em {glow}, "
                   f"0 0 0.28em {glow}, 0 0 0.6em {glow} !important; }}"
                   f"{s} .ty-h .ty-key {{ color:{glow} !important; text-shadow:0 0 0.04em #FFFFFF, 0 0 0.14em {glow}, "
                   f"0 0 0.4em {glow} !important; }}")
    elif eff == "marker":
        box = pal["hi"] if pal["hi"].upper() != pal["bg"].upper() else acc
        out.append(f"{s} .ty-h .ty-key {{ display:inline-block; background:{box}; color:{_contrast(box)} !important; "
                   f"padding:0 0.14em; border-radius:0.08em; box-shadow:0.06em 0.07em 0 #111111; "
                   f"transform:rotate(-2deg); }}"
                   f"{s} .ty-h .ty-key .mk {{ display:none; }}")
    elif eff == "editorial":
        out.append(f"{s} .ty-h {{ letter-spacing:-0.01em; }}"
                   f"{s} .ty-h .ty-key {{ font-family:'DM Serif Display Italic' !important; color:{acc} !important; "
                   f"background-image:linear-gradient({acc},{acc}); background-repeat:no-repeat; "
                   f"background-position:0 94%; background-size:100% 0.07em; }}")
    return "\n".join(out)


# ------------------------------------------------------------------------------------- other scene types' text
_TEXT_EL = re.compile(r'<(div|span)([^>]*?)style="([^"]*?)"')


def tag_headlines(html: str, pal: dict, head: str, H: int) -> str:
    """Adds class ty-h to large text in the headline font drawn in the palette's ink (text on the backdrop)."""
    if classic() or STYLE["effect"] in ("marker",):
        return html
    min_px = int(H * 0.075)

    def fix(m):
        tag, attrs, style = m.group(1), m.group(2), m.group(3)
        if f"font-family:'{head}'" not in style.replace(", ", ","):
            return m.group(0)
        fs = re.search(r"font-size:(\d+)px", style)
        col = re.search(r"(?<![-\w])color:\s*(#[0-9A-Fa-f]{6})", style)
        if not fs or int(fs.group(1)) < min_px or not col or col.group(1).upper() != pal["ink"].upper():
            return m.group(0)
        if 'class="' in attrs:
            attrs = attrs.replace('class="', 'class="ty-h ', 1)
        else:
            attrs += ' class="ty-h"'
        return f'<{tag}{attrs}style="{style}"'
    return _TEXT_EL.sub(fix, html)


def deco_html(P: str, pal: dict, W: int, H: int, i: int, n: int, label: str) -> str:
    """Swiss deco: hairline crosshair through the frame centre + mono labels in two corners."""
    line = f"{'rgba(255,255,255,0.16)' if _contrast(pal['bg']) == '#FFFFFF' else 'rgba(0,0,0,0.13)'}"
    fs = max(12, int(H * 0.017))
    lab = re.sub(r"[<>&\"]", "", (label or "").upper())[:34]
    return (f'<div data-layout-ignore class="ty-deco" style="position:absolute;inset:0;pointer-events:none">'
            f'<div id="{P}tyx" style="position:absolute;left:0;right:0;top:{H // 2}px;height:1px;background:{line}"></div>'
            f'<div id="{P}tyy" style="position:absolute;top:0;bottom:0;left:{W // 2}px;width:1px;background:{line}"></div>'
            f'<div style="position:absolute;right:{int(W * 0.035)}px;top:{int(H * 0.05)}px;font-family:\'Space Mono\';'
            f'font-size:{fs}px;letter-spacing:0.12em;color:{pal["ink"]};opacity:0.55">{i + 1:02d} / {n:02d}</div>'
            f'<div style="position:absolute;left:{int(W * 0.035)}px;bottom:{int(H * 0.045)}px;font-family:\'Space Mono\';'
            f'font-size:{fs}px;letter-spacing:0.12em;color:{pal["ink"]};opacity:0.55">{lab}</div></div>')


def apply(parts: dict, P: str, pal: dict, ctx: dict, head: str, i: int, n: int, label: str, show: dict) -> dict:
    """Style the built scene: tag big headline text of every scene type, add the style's CSS, the scramble helper
    and (Swiss, formats without a backdrop) the hairline deco."""
    if classic():
        return parts
    H, W = ctx["H"], ctx["W"]
    html = tag_headlines(parts["html"], pal, head, H)
    if STYLE["case"] == "as_is" and ctx.get("ty_case"):
        html = restore_case(html, ctx["ty_case"])
    js = parts["js"]
    if "__scr(" in js:
        js = SCRAMBLE_JS + js
    if STYLE.get("deco") and not show.get("backdrop"):
        html = deco_html(P, pal, W, H, i, n, label) + html
        js += (f'\ntl.fromTo(["#{P}tyx", "#{P}tyy"], {{scaleX: 0, scaleY: 0}}, {{scaleX: 1, scaleY: 1, duration: 0.6, '
               f'ease: "power3.out"}}, 0);')
    return dict(parts, html=html, css=parts["css"] + "\n" + css(pal), js=js)


# ------------------------------------------------------------------------------- the UI's Typography tab
PREVIEW_PAL = {"classic": "yellow", "swiss": "sw_blue", "outline_pop": "yellow", "extrude": "blue",
               "gradient": "white", "neon": "lab_navy", "marker": "cream", "editorial": "case_noir"}


def preview(style_id: str) -> dict:
    """A still sample of one style for the UI tile: {css, html, bg} (the CSS is the render's own, scoped)."""
    global STYLE
    from . import formats  # noqa: F401  (registers the format palettes some previews use: lab_navy, case_noir)
    keep = STYLE
    try:
        st = set_style(style_id)
        pname = PREVIEW_PAL.get(style_id, "yellow")
        pal = next(p for p in D.PALETTES if p["name"] == pname)
        pair = D.FONT_PAIRS[st["fonts"]] if st.get("fonts") else D.FONT_PAIRS["poster"]
        scope = f"#typv-{style_id}"
        words = ["Every", "frame", "looks", "designed."] if st["case"] == "as_is" else ["EVERY", "FRAME", "LOOKS", "DESIGNED"]
        key = 3
        spans = []
        for j, w in enumerate(words):
            inner = word_html(w, "pop", lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;"))
            cls = "ty-key" if j == key else "ty-lt"
            if st["emphasis"] == "marker" and j == key:
                inner = (f'<span style="background:{pal["hi"]};color:{_contrast(pal["hi"])};padding:0 0.1em;'
                         f'border-radius:0.06em">{inner}</span>')
            spans.append(f'<span class="{cls}" style="display:inline-block">{inner}</span>')
        html = (f'<div class="ty-h" style="font-family:\'{pair["head"]}\';color:{pal["ink"]};font-size:34px;'
                f'line-height:1.08;text-align:center">{" ".join(spans)}</div>')
        css_txt = css(pal, scope) if style_id != "classic" else ""
        if style_id == "classic":
            css_txt = f"{scope} .ty-h {{ letter-spacing:-0.01em; }}"
        return {"id": style_id, "css": css_txt, "html": html, "bg": pal["bg"], "label": st["label"],
                "description": st["description"], "entrances": st["entrances"],
                "formats": [f for f, p in POOLS.items() if style_id in p]}
    finally:
        STYLE = keep


def font_files() -> dict:
    """family -> file of every bundled font the motion renderer uses (the UI loads them for the previews)."""
    return {fam: f for fam, f, _w in D.FONTS.values()}


# ----------------------------------------------------------------------------- normal capitals (as_is styles)
def case_map(texts) -> dict:
    """lower word -> how the script writes it inside sentences ("apple" -> "Apple", "ai" -> "AI"). Words seen only
    at a sentence start are kept lower case."""
    seen = {}
    for text in texts:
        for m in re.finditer(r"([.!?:]\s+|^)?([A-Za-z][A-Za-z'’-]*)", str(text or "")):
            if m.group(1) is not None:                      # first word of a sentence: its capital says nothing
                continue
            w = m.group(2)
            seen.setdefault(w.lower(), {}).setdefault(w, 0)
            seen[w.lower()][w] += 1
    return {k: max(v.items(), key=lambda kv: (kv[1], kv[0] != kv[0].lower()))[0] for k, v in seen.items()}


_NODE = re.compile(r">([^<>]*[A-Z][^<>]*)<")


def restore_case(html: str, cmap: dict) -> str:
    """ALL-CAPS text of the scene types (labels, cards, titles) back to the script's own capitals: words the script
    writes with a capital keep it, the first word of a label gets one, everything else lower case."""
    def node(m):
        txt = m.group(1)
        letters = [c for c in txt if c.isalpha()]
        if len(letters) < 2 or txt != txt.upper() or "&" in txt:
            return m.group(0)
        out, first = [], True
        for part in re.split(r"([A-Za-z][A-Za-z'’-]*)", txt):
            if part and part[0].isalpha():
                w = cmap.get(part.lower())
                if w is None:
                    w = part.lower()                              # (acronyms are in the script as written)
                if first:
                    w = w[:1].upper() + w[1:]
                    first = False
                out.append(w)
            else:
                out.append(part)
        return ">" + "".join(out) + "<"
    return _NODE.sub(node, html)
