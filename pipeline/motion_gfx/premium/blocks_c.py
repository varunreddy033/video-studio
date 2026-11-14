"""Premium blocks 14-19 (measured from ex14..ex19; numbers in ../SPECS.md)."""
from .core import esc, stage, out, loop_js


# ------------------------------------------------------------------------------------------- 14 odometer
def odometer(P, ctx):
    """A counter whose last digit rolls up twice, then the whole number rolls to a bigger milestone with a label.
    ctx: start (int, e.g. 997), end_text ("1,000"), label, color, loops."""
    w, h, period = 990, 564, 3.0
    loops = ctx.get("loops", 1)
    start = int(ctx.get("start", 997))
    col = ctx.get("color", "#4f6ef2")
    head = str(start)[:-1]
    d0, d1, d2 = str(start)[-1], str(start + 1)[-1], str(start + 2)[-1]
    label = ctx.get("label", "Figma plugin installs")
    lab = "".join(f'<span style="display:inline-block;overflow:hidden;height:38px;vertical-align:top"><span class="{P}lw" style="display:inline-block">{esc(x)}&nbsp;</span></span>' for x in label.split(" "))
    inner = f"""
<div style="position:absolute;left:0;top:168px;width:{w}px;height:190px;overflow:hidden">
  <div id="{P}-A" style="position:absolute;left:0;top:35px;width:{w}px;height:120px;text-align:center;font:700 108px/120px Inter;letter-spacing:-.02em;color:{col};text-shadow:0 12px 20px rgba(79,110,242,.30)">
    <span>{esc(head)}</span><span style="display:inline-block;position:relative;width:.62em;height:120px;vertical-align:top;text-align:center">
      <span id="{P}-d0" class="{P}dg">{d0}</span><span id="{P}-d1" class="{P}dg">{d1}</span><span id="{P}-d2" class="{P}dg">{d2}</span></span>
  </div>
  <div id="{P}-B" style="position:absolute;left:0;top:20px;width:{w}px;height:150px;text-align:center;font:700 136px/150px Inter;letter-spacing:-.025em;color:{col};text-shadow:0 14px 22px rgba(79,110,242,.30)">{esc(ctx.get("end_text", "1,000"))}</div>
</div>
<div style="position:absolute;left:0;top:340px;width:{w}px;text-align:center;font:700 33px/38px Inter;letter-spacing:-.01em;color:#0c0c0e">{lab}</div>"""
    css = f".{P}dg {{ position:absolute; left:0; top:0; width:100%; }}"
    one = """
tl.set("#@P-A", {y: 0, autoAlpha: 1}, @o); tl.set("#@P-B", {y: 170, autoAlpha: 0}, @o); tl.set(".@Plw", {y: 40}, @o);
tl.set("#@P-d0", {y: -55}, @o); tl.set("#@P-d1", {y: 150}, @o); tl.set("#@P-d2", {y: 150}, @o);
tl.fromTo("#@P-d0", {y: -55}, {y: -175, duration: 0.36, ease: "power2.inOut", immediateRender: false}, @o + 0.04);
tl.fromTo("#@P-d1", {y: 150}, {y: 0, duration: 0.42, ease: "power2.inOut", immediateRender: false}, @o + 0.07);
tl.fromTo("#@P-d1", {y: 0}, {y: -9, duration: 0.12, ease: "power1.out", immediateRender: false}, @o + 0.55);
tl.fromTo("#@P-d1", {y: -9}, {y: -175, duration: 0.36, ease: "power2.inOut", immediateRender: false}, @o + 0.66);
tl.fromTo("#@P-d2", {y: 150}, {y: 0, duration: 0.42, ease: "power2.inOut", immediateRender: false}, @o + 0.69);
tl.fromTo("#@P-A", {y: 0, autoAlpha: 1}, {y: -165, autoAlpha: 1, duration: 0.50, ease: "power3.inOut", immediateRender: false}, @o + 1.33);
tl.fromTo("#@P-B", {y: 170, autoAlpha: 1}, {y: 0, autoAlpha: 1, duration: 0.50, ease: "power3.inOut", immediateRender: false}, @o + 1.35);
tl.fromTo(".@Plw", {y: 40}, {y: 0, duration: 0.22, ease: "power2.out", stagger: 0.085, immediateRender: false}, @o + 1.55);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.2, "tick"), (0.8, "tick"), (1.45, "success"))]
    return out(P, stage(P, ctx, w, h, "#ffffff", inner), css, loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 15 gradient_words
def _mix(a, b, t):
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def gradient_words(P, ctx):
    """A short phrase in a left-to-right colour gradient fades in word by word. ctx: text, colors (2), loops."""
    w, h, period = 1008, 532, 2.82
    loops = ctx.get("loops", 1)
    text = ctx.get("text", "4.5K Retina display")
    c0, c1 = ctx.get("colors", ["#5f8c86", "#c9da6c"])
    words, n, pos, sp = text.split(" "), len(text), 0, []
    for wd in words:
        a, b = pos / n, (pos + len(wd)) / n
        sp.append(f'<span class="{P}w" style="display:inline-block;background:linear-gradient(90deg,{_mix(c0, c1, a)},{_mix(c0, c1, b)});'
                  f'-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent">{esc(wd)}</span>')
        pos += len(wd) + 1
    inner = (f'<div style="position:absolute;left:0;top:226px;width:{w}px;text-align:center;font:500 69px/76px Inter;letter-spacing:-.015em;white-space:nowrap">'
             + '<span style="display:inline-block;width:.26em"></span>'.join(sp) + '</div>')
    one = ['tl.set(".@Pw", {autoAlpha: 0, y: -8}, @o);',
           f'tl.fromTo(".@Pw", {{autoAlpha: 0, y: -8}}, {{autoAlpha: 1, y: 0, duration: 0.75, ease: "power1.out", stagger: 0.15, immediateRender: false}}, @o + 0.43);']
    cues = [(k * period + 0.47, "swoosh-up") for k in range(loops)]
    return out(P, stage(P, ctx, w, h, "#ffffff", inner), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 16 track_type
TRACK_LS = [100, 80, 62, 48, 40, 32, 21, 13.5, 8, 3.75, 0.5, -1.5, -2.75, -3, -3, -2.6, -2.25, -1.9, -1.5, -1.1, -0.75, -0.4, -0.2, 0]   # px per gap, 33 ms
TRACK_X = [219, 102, 54, 22, -2, -18, -26, -30, -30, -26, -22, -18, -16, -13, -10, -7, -4, -3, -2, -1, 0]                               # px, 33 ms


def track_type(P, ctx):
    """Stacked bold caps type on letter by letter with very wide tracking that snaps tight with a little overshoot.
    ctx: lines, font (default Jost), size, loops."""
    w, h, period = 1030, 642, 1.70
    loops = ctx.get("loops", 2)
    lines = ctx.get("lines", ["HELLO", "MONDAY", "GOODBYE", "WEEKEND."])
    size, base = ctx.get("size", 129), ctx.get("tracking", -8.0)
    rows = []
    for i, line in enumerate(lines[:4]):
        ch = "".join(f'<span class="{P}c{i}" style="visibility:hidden">{esc(c)}</span>' for c in line)
        rows.append(f'<div id="{P}-l{i}" style="position:absolute;left:{62 if i else 66}px;top:{138 + 106 * i}px;height:106px;white-space:nowrap;'
                    f'font:800 {size}px/106px {ctx.get("font", "Jost")};letter-spacing:{base}px;color:#fff">{ch}</div>')
    one, t, cues = [], 0.0, []
    for i, line in enumerate(lines[:4]):
        one.append(f'tl.set("#@P-l{i}", {{letterSpacing: {base + 100}, x: 219}}, @o); tl.set(".@Pc{i}", {{autoAlpha: 0}}, @o);')
        one.append(f'tl.fromTo("#@P-l{i}", {{letterSpacing: {base + 100}}}, {{letterSpacing: {base}, duration: 0.767, ease: PMX.tab({TRACK_LS}), immediateRender: false}}, @o + {t:.3f});')
        one.append(f'tl.fromTo("#@P-l{i}", {{x: 219}}, {{x: 0, duration: 0.667, ease: PMX.tab({TRACK_X}), immediateRender: false}}, @o + {t:.3f});')
        for j in range(len(line)):
            one.append(f'tl.set(gsap.utils.toArray(".@Pc{i}")[{j}], {{autoAlpha: 1}}, @o + {t + 0.024 * j:.3f});')
        cues.append((t, "keyboard"))
        t += 0.024 * len(line)
    cues = [(k * period + a, s) for k in range(loops) for a, s in cues]
    return out(P, stage(P, ctx, w, h, "linear-gradient(180deg,#2e9cf5 0,#62b8f8 55%,#a9d9fb 100%)", "".join(rows)), "",
               loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 17 blur_zoom_type
def blur_zoom_type(P, ctx):
    """Close-up, blurred letters type on while the camera pulls back until the whole line is sharp and framed.
    ctx: lines (2), badge, color, bg, font, loops."""
    w, h, period = 980, 600, 2.117
    loops = ctx.get("loops", 2)
    lines = ctx.get("lines", ["Designed for", "your moments."])
    col = ctx.get("color", "#0f4d0b")
    rows, k = [], 0
    for line in lines[:2]:
        ch = "".join((f'<span class="{P}ch" style="display:inline-block;white-space:pre;visibility:hidden">{esc(c)}</span>' if c != " "
                      else '<span style="display:inline-block;width:.24em"></span>') for c in line)
        rows.append(f'<div style="white-space:nowrap">{ch}</div>')
    nchar = sum(len(x.replace(" ", "")) for x in lines[:2])
    inner = (f'<div id="{P}-zm" style="position:absolute;left:0;top:0;width:{w}px;height:{h}px;transform-origin:50% 52%">'
             f'<div style="position:absolute;left:0;top:204px;width:{w}px;text-align:center;font:900 90px/86px {ctx.get("font", "Nunito")};letter-spacing:-.035em;color:{col}">{"".join(rows)}</div>'
             f'<div id="{P}-bd" style="position:absolute;left:0;top:418px;width:{w}px;text-align:center;font:600 21px Inter;color:#111">'
             f'<span style="display:inline-block;width:27px;height:27px;border-radius:7px;background:#00d64f;vertical-align:-5px;margin-right:9px"></span>{esc(ctx.get("badge", "Your App"))}</div></div>')
    one = ['tl.set("#@P-zm", {scale: 1.75}, @o); tl.set(".@Pch, #@P-bd", {autoAlpha: 0}, @o);',
           'tl.fromTo("#@P-zm", {scale: 1.75}, {scale: 1, duration: 2.10, ease: PMX.cb(0.70, 0.59, 0.25, 0.77), immediateRender: false}, @o + 0.0);']
    for j in range(nchar):
        one.append(f'tl.fromTo(gsap.utils.toArray(".@Pch")[{j}], {{autoAlpha: 0, filter: "blur(22px)"}}, {{autoAlpha: 1, filter: "blur(0px)", duration: 0.16, ease: "power1.out", immediateRender: false}}, @o + {0.0 + 0.022 * j:.3f});')
    one.append('tl.fromTo("#@P-bd", {autoAlpha: 0, filter: "blur(10px)"}, {autoAlpha: 1, filter: "blur(0px)", duration: 0.22, ease: "power1.out", immediateRender: false}, @o + 0.45);')
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.03, "keyboard"), (0.1, "riser"))]
    return out(P, stage(P, ctx, w, h, ctx.get("bg", "#f1f1f3"), inner), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 18 post_card
POST_SCALE = [0.94, 0.965, 0.981, 0.995, 1.001, 1.006, 1.0097, 1.0097, 1.005, 1.001, 1.0]


def post_card(P, ctx):
    """A social post card pops in; avatar, name, then the text word by word; the card fades away.
    ctx: name, handle, text, meta, link, initials, loops."""
    w, h, period = 958, 814, 2.83
    loops = ctx.get("loops", 1)
    text = ctx.get("text", "This is the original component. Edit me to customize anything.")
    words = "".join(f'<span class="{P}w" style="display:inline-block;white-space:pre">{esc(x)} </span>' for x in text.split(" "))
    tick = ('<svg id="{P}-vf" viewBox="0 0 24 24" width="24" height="24" style="display:inline-block;vertical-align:-4px;margin-left:6px"><circle cx="12" cy="12" r="10" fill="#1d9bf0"/>'
            '<path d="M7.5 12.4l3 3 6-6.3" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>').replace("{P}", P)
    inner = f"""
<div id="{P}-cd" style="position:absolute;left:66px;top:242px;width:824px;height:380px;border-radius:12px;background:#fff;box-shadow:0 14px 40px rgba(0,40,90,.18);transform-origin:50% 50%;opacity:0">
  <div id="{P}-av" style="position:absolute;left:46px;top:44px;width:96px;height:96px;border-radius:50%;background:linear-gradient(135deg,#9ad0c2,#3b7a8c);display:flex;align-items:center;justify-content:center;font:700 34px Inter;color:#fff">{esc(ctx.get("initials", "JK"))}</div>
  <div style="position:absolute;left:160px;top:54px;height:36px;overflow:hidden"><div id="{P}-nm" style="font:700 27px/36px Inter;color:#0f1419;white-space:nowrap">{esc(ctx.get("name", "John Kappa"))}{tick}</div></div>
  <div style="position:absolute;left:160px;top:92px;height:34px;overflow:hidden"><div id="{P}-hd" style="font:400 24px/34px Inter;color:#6b7785">{esc(ctx.get("handle", "@johnkappa"))}</div></div>
  <div style="position:absolute;left:46px;top:170px;width:750px;font:400 37px/1.38 Inter;letter-spacing:-.01em;color:#0f1419">{words}</div>
  <div style="position:absolute;left:46px;top:306px;font:400 19px Inter;color:#6b7785">{esc(ctx.get("meta", "12:30 PM · Jun 21, 2021 · "))}<span style="color:#1d9bf0">{esc(ctx.get("link", "Web App"))}</span></div>
</div>"""
    one = f"""
tl.set("#@P-cd", {{autoAlpha: 0, scale: 0.94}}, @o); tl.set("#@P-av, #@P-vf", {{scale: 0}}, @o); tl.set("#@P-nm, #@P-hd", {{y: 34}}, @o); tl.set(".@Pw", {{autoAlpha: 0}}, @o);
tl.fromTo("#@P-cd", {{autoAlpha: 0}}, {{autoAlpha: 1, duration: 0.07, ease: "none", immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-cd", {{scale: 0.94}}, {{scale: 1, duration: 0.333, ease: PMX.tab({POST_SCALE}), immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-av", {{scale: 0}}, {{scale: 1, duration: 0.18, ease: "back.out(1.8)", immediateRender: false}}, @o + 0.07);
tl.fromTo("#@P-nm", {{y: 34}}, {{y: 0, duration: 0.14, ease: "power2.out", immediateRender: false}}, @o + 0.20);
tl.fromTo("#@P-hd", {{y: 34}}, {{y: 0, duration: 0.14, ease: "power2.out", immediateRender: false}}, @o + 0.23);
tl.fromTo("#@P-vf", {{scale: 0}}, {{scale: 1, duration: 0.14, ease: "back.out(2.5)", transformOrigin: "50% 50%", immediateRender: false}}, @o + 0.32);
tl.fromTo(".@Pw", {{autoAlpha: 0}}, {{autoAlpha: 1, duration: 0.16, ease: "none", stagger: 0.032, immediateRender: false}}, @o + 0.37);
tl.fromTo("#@P-cd", {{autoAlpha: 1, scale: 1}}, {{autoAlpha: 0, scale: 0.93, duration: 0.18, ease: "power1.in", immediateRender: false}}, @o + 2.42);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.0, "pop"), (0.37, "keyboard"), (2.42, "swipe"))]
    return out(P, stage(P, ctx, w, h, "linear-gradient(135deg,#43aef2 0,#2f9ae6 50%,#1a84d5 100%)", inner), "", loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 19 color_carousel
def color_carousel(P, ctx):
    """Tall rounded colour cards: the wide active card squeezes to a pill while the next one opens. ctx: cards =
    [(name, colour, rows)], steps (= loops), start (index of the first active card)."""
    w, h, period = 1038, 648, 1.383
    steps = ctx.get("loops", 2)
    cards = ctx.get("cards", [("Yellow", "#d9bc17", ("#D9BC17", "217 / 188 / 23", "0 / 13 / 89 / 15")), ("Lime", "#b5d92b", ("#B5D92B", "181 / 217 / 43", "17 / 0 / 80 / 15")),
                              ("Blue", "#1f3be0", ("#1F3BE0", "31 / 59 / 224", "86 / 74 / 0 / 12")), ("Purple", "#8800ff", ("#8800FF", "136 / 0 / 255", "47 / 100 / 0 / 0")),
                              ("Grey", "#a0a3c0", ("#A0A3C0", "160 / 163 / 192", "17 / 15 / 0 / 25"))])
    a0 = ctx.get("start", 2) + len(cards)                     # so there are cards to the left as well
    n = a0 + steps + 5

    def left(k):
        return 222 + 130 * k if k <= 0 else 836 + 130 * (k - 1)

    hs = []
    for i in range(a0 - 3, n):
        name, col, rows = cards[i % len(cards)]
        k = i - a0
        data = "".join(f'<div style="position:absolute;left:{x}px;bottom:{54 + 17 * (2 - r)}px;font:700 10px SpaceMono,monospace;letter-spacing:.06em;color:rgba(255,255,255,.62)">{esc(t)}</div>'
                       for x, col_ in ((66, ("HEX", "RGB", "CMYK")), (300, rows)) for r, t in enumerate(col_))
        hs.append(f'<div id="{P}-c{i}" style="position:absolute;left:{left(k)}px;top:20px;width:{600 if k == 0 else 116}px;height:600px;border-radius:58px;background:{col};overflow:hidden">'
                  f'<div id="{P}-t{i}" style="position:absolute;left:0;top:0;width:600px;height:600px;opacity:{1 if k == 0 else 0}">'
                  f'<div style="position:absolute;left:62px;top:34px;font:400 98px/1.1 Anton;color:#fff;letter-spacing:-.005em">{esc(name)}</div>{data}</div></div>')
    js, cues = [], []
    for s in range(steps):
        t = s * period + 0.283
        a = a0 + s
        for i in range(a0 - 3, n):
            k = i - a
            if -3 <= k <= 5:
                js.append(f'tl.fromTo("#{P}-c{i}", {{left: {left(k)}, width: {600 if k == 0 else 116}}}, {{left: {left(k - 1)}, width: {600 if k == 1 else 116}, duration: 1.017, ease: PMX.cb(0.52, -0.01, 0.01, 1.0), immediateRender: false}}, {t:.3f});')
        js.append(f'tl.fromTo("#{P}-t{a}", {{opacity: 1}}, {{opacity: 0, duration: 0.18, ease: "none", immediateRender: false}}, {t + 0.05:.3f});')
        js.append(f'tl.fromTo("#{P}-t{a + 1}", {{opacity: 0}}, {{opacity: 1, duration: 0.30, ease: "none", immediateRender: false}}, {t + 0.40:.3f});')
        cues.append((t + 0.2, "whoosh"))
    return out(P, stage(P, ctx, w, h, "#000", "".join(hs)), "", js, cues, period * steps, (w, h), steps)
