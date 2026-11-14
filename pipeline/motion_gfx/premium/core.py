"""Premium motion blocks: shared helpers.

Every block is a builder   build(P, ctx) -> {"html", "css", "js", "cues", "dur", "native"}
in the SAME shape pipeline/motion_gfx/scenes.py uses (html + css + GSAP lines that run on a timeline called `tl`,
time 0 = the scene's start; cues = [(seconds, sfx kind)]).

  P    unique id prefix for the scene (ids are "<P>-xxx", classes "<P>x")
  ctx  {"W": 1920, "H": 1080, "loops": 1, ...content overrides per block (see each builder's docstring)}

A block is drawn at the reference clip's own pixel size inside "#<P>-st" and scaled to fit W x H (contain), so all
measured pixel values stay exactly as measured. Timings are the measured ones; `loops` repeats the cycle.
Only GSAP core is needed (no plugins): eases come from PMX.cb (cubic-bezier) and PMX.tab (measured sample tables).
"""
import html as _html

# --- runs once per page; safe to include in every scene -------------------------------------------------------
HELPERS_JS = r"""
const PMX = window.PMX || (window.PMX = {
  cb: function (x1, y1, x2, y2) {            // cubic-bezier(x1,y1,x2,y2) as a GSAP ease function
    return function (p) {
      if (p <= 0) return 0; if (p >= 1) return 1;
      let lo = 0, hi = 1, t = 0.5;
      for (let i = 0; i < 26; i++) { t = (lo + hi) / 2; const x = 3*(1-t)*(1-t)*t*x1 + 3*(1-t)*t*t*x2 + t*t*t; if (x < p) lo = t; else hi = t; }
      return 3*(1-t)*(1-t)*t*y1 + 3*(1-t)*t*t*y2 + t*t*t;
    };
  },
  tab: function (v) {                        // measured samples (equal time steps) -> ease, normalised first..last = 0..1
    const a = v[0], b = v[v.length - 1], n = v.length - 1;
    return function (p) {
      const f = Math.min(n, Math.max(0, p * n)), i = Math.min(n - 1, Math.floor(f));
      return ((v[i] + (v[i + 1] - v[i]) * (f - i)) - a) / (b - a);
    };
  }
});
"""


def esc(s):
    return _html.escape(str(s), quote=True)


def fit(ctx, w, h):
    W, H = ctx.get("W", 1920), ctx.get("H", 1080)
    return min(W / w, H / h)


def stage(P, ctx, w, h, bg, inner, bg_css=""):
    """Full-frame background + the native-size stage, scaled to fit and centred."""
    k = fit(ctx, w, h)
    return (f'<div id="{P}-bg" style="position:absolute;inset:0;background:{bg};{bg_css}"></div>'
            f'<div id="{P}-fit" style="position:absolute;left:50%;top:50%;width:0;height:0;transform:scale({k:.5f});">'
            f'<div id="{P}-st" style="position:absolute;left:{-w / 2}px;top:{-h / 2}px;width:{w}px;height:{h}px;'
            f'overflow:hidden;background:{bg};{bg_css}">{inner}</div></div>')


def out(P, html, css, js, cues, dur, native, loops=1):
    """js = list of lines (or one string). Adds the helper once and a guard so the scene always lasts `dur`."""
    body = js if isinstance(js, str) else "\n".join(js)
    body = HELPERS_JS + body + f'\ntl.set("#{P}-bg", {{}}, {dur:.3f});'
    return {"html": html, "css": css, "js": body, "cues": cues, "dur": dur, "native": native, "loops": loops}


def loop_js(template, period, loops, P):
    """Repeat one cycle's GSAP lines; '@o' in the template is the cycle's start time, '@P' the id prefix."""
    return "\n".join(template.replace("@o", f"{k * period:.4f}").replace("@P", P) for k in range(loops))


def spans(P, text, cls, mode="word"):
    """Split text into inline-block spans (words or characters). Returns (html, count)."""
    parts = text.split(" ") if mode == "word" else list(text)
    o = []
    for i, p in enumerate(parts):
        if mode == "char" and p == " ":
            o.append('<span style="display:inline-block;width:0.28em"></span>')
            continue
        o.append(f'<span class="{P}{cls}" style="display:inline-block;white-space:pre">{esc(p)}</span>'
                 + (" " if mode == "word" else ""))
    n = sum(1 for p in parts if not (mode == "char" and p == " "))
    return "".join(o), n


FONT_FACES = [     # (family, file, weight). Files live in assets/fonts (pipeline) or recreations/fonts (new, OFL).
    ("Inter", "InterVariable.ttf", "100 900"),
    ("Poppins", "Poppins-Regular.ttf", "400"),
    ("Poppins", "Poppins-Medium.ttf", "500"),
    ("Poppins", "Poppins-SemiBold.ttf", "600"),
    ("Jost", "Jost-wght.ttf", "100 900"),
    ("Nunito", "Nunito-wght.ttf", "200 1000"),
    ("Anton", "Anton-Regular.ttf", "400"),
    ("Modak", "Modak-Regular.ttf", "400"),
    ("Bagel Fat One", "BagelFatOne-Regular.ttf", "400"),
    ("SpaceMono", "SpaceMono-Bold.ttf", "700"),
]
