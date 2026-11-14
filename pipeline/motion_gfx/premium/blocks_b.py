"""Premium blocks 8-13 (measured from ex08..ex13; numbers in ../SPECS.md)."""
from .core import esc, stage, out, loop_js


def _smooth(pts):
    """Catmull-Rom through points -> SVG cubic path."""
    if len(pts) < 2:                                       # no line (e.g. no "predicted" series)
        return ""
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d)


# ------------------------------------------------------------------------------------------- 8 chart_card
CARD_W_IN = [0.05, 0.24, 0.45, 0.645, 0.745, 0.81, 0.855, 0.887, 0.91, 0.93, 0.947, 0.961, 0.972, 0.981, 0.988, 0.992, 0.996, 0.999, 1.0]
CARD_SCALE = [1.42, 1.353, 1.284, 1.2, 1.142, 1.1, 1.074, 1.053, 1.042, 1.032, 1.021, 1.016, 1.01, 1.005, 1.003, 1.001, 1.0]


def chart_card(P, ctx):
    """A line-chart card unfolds from a thin vertical line while settling from a zoom; two lines draw; the card folds away.
    ctx: title, series (list of y values 0-12), predicted (list), xlabels, legend, loops."""
    w, h, period = 1006, 694, 4.0
    loops = ctx.get("loops", 1)
    s1 = ctx.get("series", [4.6, 4.0, 4.3, 3.9, 5.0, 4.9, 6.0, 5.7, 6.8, 6.1, 4.9, 5.3, 4.6, 5.0])
    s2 = ctx.get("predicted", [5.7, 5.9, 6.7, 6.4, 5.4, 6.0, 5.6, 6.1, 5.8, 6.4, 6.8])
    x0, x1, yb, yt = 62, 432, 275, 113                       # plot box (card px); y for value 0 and 12

    def pts(v):
        return [(x0 + (x1 - x0) * i / (len(v) - 1) * (0.92 if v is s1 else 1.0), 232 - (val - 4.6) * 24) for i, val in enumerate(v)]
    grid = "".join(f'<line x1="{x0 - 8}" y1="{y}" x2="{x1 + 12}" y2="{y}" stroke="#cfe2c8" stroke-width="1"/>'
                   f'<text x="{x0 - 26}" y="{y + 3}" font-size="8" fill="#7d8f7b" font-family="Poppins">{lab}</text>'
                   for y, lab in zip((113, 167, 221, 275), ctx.get("ylabels", ("12", "8", "4", "0"))))
    xl = "".join(f'<text x="{x}" y="302" font-size="8" fill="#7d8f7b" font-family="Poppins" text-anchor="middle">{esc(t)}</text>'
                 for x, t in zip((112, 212, 312, 412), ctx.get("xlabels", ["06:00", "12:00", "18:00", "00:00"])))
    lg = ctx.get("legend", ["Dataset 1", "Predicted"])
    svg = f"""<svg width="478" height="380" viewBox="0 0 478 380" style="position:absolute;left:0;top:0">
<defs><clipPath id="{P}-k1"><rect id="{P}-r1" x="0" y="0" width="0" height="380"/></clipPath><clipPath id="{P}-k2"><rect id="{P}-r2" x="0" y="0" width="0" height="380"/></clipPath></defs>
<text x="34" y="52" font-size="22" font-family="Poppins" font-weight="500" fill="#1c2620">{esc(ctx.get("title", "Line chart"))}</text>
{grid}{xl}
<path d="{_smooth(pts(s2))}" fill="none" stroke="#7f9a85" stroke-width="1.4" stroke-dasharray="4 3" clip-path="url(#{P}-k2)"/>
<path d="{_smooth(pts(s1))}" fill="none" stroke="#18221c" stroke-width="1.8" stroke-linecap="round" clip-path="url(#{P}-k1)"/>
<line x1="178" y1="346" x2="188" y2="346" stroke="#18221c" stroke-width="2"/><text x="194" y="349" font-size="8" fill="#4d5b4f" font-family="Poppins">{esc(lg[0])}</text>
<line x1="258" y1="346" x2="270" y2="346" stroke="#7f9a85" stroke-width="1.6" stroke-dasharray="3 2"/><text x="276" y="349" font-size="8" fill="#4d5b4f" font-family="Poppins">{esc(lg[1])}</text>
</svg>"""
    inner = (f'<div id="{P}-sc" style="position:absolute;left:263px;top:152px;width:478px;height:380px;transform-origin:50% 50%">'
             f'<div id="{P}-cl" style="position:absolute;right:0;top:0;width:2px;height:380px;overflow:hidden;border-radius:22px;background:#e4f6dd;opacity:0">'
             f'<div id="{P}-ct" style="position:absolute;right:0;top:0;width:478px;height:380px">{svg}</div></div></div>')
    one = f"""
tl.set("#@P-cl", {{right: 0, left: "auto", width: 2, autoAlpha: 0}}, @o); tl.set("#@P-ct", {{right: 0, left: "auto"}}, @o);
tl.set("#@P-sc", {{scale: 1.42}}, @o); tl.set("#@P-r1, #@P-r2", {{attr: {{width: 0}}}}, @o);
tl.fromTo("#@P-cl", {{autoAlpha: 0}}, {{autoAlpha: 0.75, duration: 0.07, ease: "none", immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-cl", {{width: 2}}, {{width: 24, duration: 0.237, ease: "power1.in", immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-cl", {{width: 24}}, {{width: 478, duration: 0.60, ease: PMX.tab({CARD_W_IN}), immediateRender: false}}, @o + 0.237);
tl.fromTo("#@P-sc", {{scale: 1.42}}, {{scale: 1, duration: 0.533, ease: PMX.tab({CARD_SCALE}), immediateRender: false}}, @o + 0.253);
tl.fromTo("#@P-cl", {{autoAlpha: 0.75}}, {{autoAlpha: 1, duration: 0.27, ease: "none", immediateRender: false}}, @o + 0.32);
tl.fromTo("#@P-r2", {{attr: {{width: 0}}}}, {{attr: {{width: 478}}, duration: 0.85, ease: "sine.inOut", immediateRender: false}}, @o + 0.37);
tl.fromTo("#@P-r1", {{attr: {{width: 0}}}}, {{attr: {{width: 478}}, duration: 1.0, ease: "sine.inOut", immediateRender: false}}, @o + 0.42);
tl.set("#@P-cl", {{right: "auto", left: 0}}, @o + 2.42); tl.set("#@P-ct", {{right: "auto", left: 0}}, @o + 2.42);
tl.fromTo("#@P-cl", {{width: 478}}, {{width: 0, duration: 0.883, ease: PMX.cb(0.89, 0.0, 0.10, 1.0), immediateRender: false}}, @o + 2.42);
tl.set("#@P-cl", {{autoAlpha: 0}}, @o + 3.303);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.25, "whoosh"), (0.45, "tick"), (2.75, "swipe"))]
    return out(P, stage(P, ctx, w, h, "#12141a", inner), "", loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 9 donut_card
DONUT_W = [80, 103, 142, 178, 256, 460, 553, 597, 622, 636, 654, 662, 668, 672, 674]
DONUT_H = [140, 164, 199, 219, 267, 387, 447, 468, 485, 492, 502, 508, 511, 513, 514]


def donut_card(P, ctx):
    """A stats card grows from a small tile; three concentric arcs sweep in. ctx: title, sub, stats = [(value, of, label, colour)], loops."""
    w, h, period = 1024, 696, 4.0
    loops = ctx.get("loops", 1)
    stats = ctx.get("stats", [(335, 400, "Dataset 1", "#7b2ff7"), (80, 120, "Dataset 2", "#f0146e"), (45, 120, "Dataset 3", "#ffb300")])
    cx, cy, radii, sw = 476, 291, [78, 112, 146], 24
    rings, rows, one = [], [], []
    for i, (v, of, lab, col) in enumerate(stats[:3]):
        r = radii[i]
        C = 2 * 3.14159265 * r
        rings.append(f'<g id="{P}-g{i}"><circle id="{P}-t{i}" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#f1f1f3" stroke-width="{sw}" stroke-dasharray="{C:.2f}" stroke-dashoffset="{C:.2f}" transform="rotate(-90 {cx} {cy})"/>'
                     f'<circle id="{P}-a{i}" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{C:.2f}" stroke-dashoffset="{C:.2f}" transform="rotate(-90 {cx} {cy})"/></g>')
        y = 150 + 104 * i
        rows.append(f'<div class="{P}s" style="position:absolute;left:44px;top:{y}px"><span style="font:600 30px Poppins;color:#17171a">{v}</span>'
                    f'<span style="font:400 13px Poppins;color:#a0a0a8"> /{of}</span><div style="margin-top:4px;font:400 10px Poppins;color:#8b8b93">'
                    f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{col};margin-right:7px"></span>{esc(lab)}</div></div>')
        frac = v / of
        one.append(f'tl.set("#@P-a{i}, #@P-t{i}", {{attr: {{"stroke-dashoffset": {C:.2f}}}}}, @o); tl.set("#@P-g{i}", {{rotation: -70, svgOrigin: "{cx} {cy}"}}, @o);')
        one.append(f'tl.fromTo("#@P-t{i}", {{attr: {{"stroke-dashoffset": {C:.2f}}}}}, {{attr: {{"stroke-dashoffset": 0}}, duration: 0.55, ease: "power2.out", immediateRender: false}}, @o + {0.38 + 0.05 * i:.2f});')
        one.append(f'tl.fromTo("#@P-g{i}", {{rotation: -70, svgOrigin: "{cx} {cy}"}}, {{rotation: 0, svgOrigin: "{cx} {cy}", duration: 0.75, ease: "power2.out", immediateRender: false}}, @o + {0.40 + 0.06 * i:.2f});')
        one.append(f'tl.fromTo("#@P-a{i}", {{attr: {{"stroke-dashoffset": {C:.2f}}}}}, {{attr: {{"stroke-dashoffset": {C * (1 - frac):.2f}}}, duration: 0.70, ease: "power2.out", immediateRender: false}}, @o + {0.50 + 0.07 * i:.2f});')
        one.append(f'tl.fromTo("#@P-a{i}", {{attr: {{"stroke-dashoffset": {C * (1 - frac):.2f}}}}}, {{attr: {{"stroke-dashoffset": {C:.2f}}}, duration: 0.3, ease: "power2.in", immediateRender: false}}, @o + 2.32);')
        one.append(f'tl.fromTo("#@P-g{i}", {{rotation: 0, svgOrigin: "{cx} {cy}"}}, {{rotation: 150, svgOrigin: "{cx} {cy}", duration: 0.4, ease: "power2.in", immediateRender: false}}, @o + 2.28);')
    inner = (f'<div id="{P}-cd" style="position:absolute;left:513px;top:89px;width:80px;height:140px;transform:translateX(-50%);border-radius:14px;background:#fff;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.05);opacity:0">'
             f'<div id="{P}-in" style="position:absolute;left:50%;top:0;width:674px;height:514px;margin-left:-337px;transform-origin:50% 0%">'
             f'<div class="{P}s" style="position:absolute;left:44px;top:40px;font:600 15px Poppins;color:#17171a">{esc(ctx.get("title", "Donut Chart"))}'
             f'<div style="margin-top:6px;font:400 10px Poppins;color:#9a9aa2">{esc(ctx.get("sub", "Aug 2024 - Sept 2024"))}</div></div>'
             f'{"".join(rows)}<svg width="674" height="514" viewBox="0 0 674 514" style="position:absolute;left:0;top:0">{"".join(rings)}</svg></div></div>')
    head = f"""
tl.set("#@P-cd", {{width: 80, height: 140, autoAlpha: 0}}, @o); tl.set("#@P-in", {{scale: 0.12}}, @o); tl.set(".@Ps", {{autoAlpha: 0, x: -14}}, @o);
tl.fromTo("#@P-cd", {{autoAlpha: 0}}, {{autoAlpha: 1, duration: 0.08, ease: "none", immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-cd", {{width: 80}}, {{width: 674, duration: 0.70, ease: PMX.tab({DONUT_W}), immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-cd", {{height: 140}}, {{height: 514, duration: 0.70, ease: PMX.tab({DONUT_H}), immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-in", {{scale: 0.12}}, {{scale: 1, duration: 0.70, ease: PMX.tab({DONUT_W}), immediateRender: false}}, @o + 0.0);
tl.fromTo(".@Ps", {{autoAlpha: 0, x: -14}}, {{autoAlpha: 1, x: 0, duration: 0.3, ease: "power2.out", stagger: 0.2, immediateRender: false}}, @o + 0.36);
tl.fromTo("#@P-cd", {{autoAlpha: 1}}, {{autoAlpha: 0, duration: 0.27, ease: "power1.in", immediateRender: false}}, @o + 2.36);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.05, "pop"), (0.35, "riser"), (2.5, "swipe"))]
    return out(P, stage(P, ctx, w, h, "#f9f9f9", inner), "", loop_js(head + "\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 10 search_type
def search_type(P, ctx):
    """A round search button appears, stretches into a search bar, and a query types itself. ctx: query, loops."""
    w, h, period = 1130, 520, 4.0
    loops = ctx.get("loops", 1)
    q = ctx.get("query", "Best motion design tool")
    chars = "".join(f'<span class="{P}ch" style="visibility:hidden">{esc(c) if c != " " else "&nbsp;"}</span>' for c in q)
    mag = ('<svg viewBox="0 0 24 24" width="44" height="44" fill="none" stroke="#9b9ba2" stroke-width="2.0" stroke-linecap="round">'
           '<circle cx="10.5" cy="10.5" r="6.2"/><path d="M15.3 15.3L20 20"/></svg>')
    inner = (f'<div id="{P}-sb" style="position:absolute;left:558px;top:159.5px;width:115px;height:115px;margin-left:-57.5px;border-radius:58px;background:#fff;overflow:hidden;box-shadow:0 10px 30px rgba(20,20,40,.07);opacity:0">'
             f'<div style="position:absolute;left:35.5px;top:35.5px;width:44px;height:44px">{mag}</div>'
             f'<div style="position:absolute;left:118px;top:0;height:115px;white-space:nowrap;font:500 39px/115px Inter;letter-spacing:-.012em;color:#2c2c30">{chars}</div></div>')
    one = ['tl.set("#@P-sb", {width: 115, marginLeft: -57.5, autoAlpha: 0, scale: 0.6}, @o); tl.set(".@Pch", {autoAlpha: 0}, @o);',
           'tl.fromTo("#@P-sb", {autoAlpha: 0, scale: 0.6}, {autoAlpha: 1, scale: 1, duration: 0.25, ease: "back.out(1.4)", immediateRender: false}, @o + 0.0);',
           'tl.fromTo("#@P-sb", {width: 115, marginLeft: -57.5}, {width: 937, marginLeft: -468.5, duration: 0.883, ease: PMX.cb(0.35, 0.08, 0.0, 0.93), immediateRender: false}, @o + 0.367);']
    for i in range(len(q)):
        one.append(f'tl.set(gsap.utils.toArray(".@Pch")[{i}], {{autoAlpha: 1}}, @o + {0.875 + 0.0465 * i:.3f});')
    one.append('tl.fromTo("#@P-sb", {autoAlpha: 1, scale: 1}, {autoAlpha: 0, scale: 0.85, duration: 0.23, ease: "power2.in", immediateRender: false}, @o + 3.27);')
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.0, "pop"), (0.4, "swoosh-up"), (0.9, "keyboard"), (3.27, "swipe"))]
    return out(P, stage(P, ctx, w, h, "#efeff2", inner), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 11 word_wheel
WHEEL_Y = {-4: -410, -3: -330, -2: -235, -1: -127, 0: 0, 1: 111, 2: 211, 3: 295, 4: 365, 5: 425}
WHEEL_STEP = [0, 0.04, 0.33, 0.67, 0.82, 0.91, 0.955, 0.98, 0.99, 1.0]


def _wheel_state(d):
    a = abs(d)
    y = WHEEL_Y.get(d, 500 if d > 0 else -500)
    rot = (-7.5 * a) if d < 0 else (6.0 * a)
    x = -9 * d * d * 0.5 if d > 0 else 4 * a
    alpha = {0: 1, 1: 0.78, 2: 0.6, 3: 0.4, 4: 0.18}.get(a, 0)
    blur = {0: 0, 1: 5, 2: 8, 3: 10, 4: 12}.get(a, 13)
    col = "#ffffff" if d == 0 else "#d2d2d2"
    return f'{{y: {y}, rotation: {rot}, x: {x:.1f}, autoAlpha: {alpha}, filter: "blur({blur}px)", color: "{col}"}}'


def word_wheel(P, ctx):
    """A blurred, tilted column of words steps past a fixed arrow; the word at the arrow is sharp and white.
    ctx: words, steps (number of steps = loops)."""
    w, h, period = 1022, 564, 0.75
    steps = ctx.get("loops", 4)
    words = ctx.get("words", ["Moments", "Pulse", "Essence", "Memories", "Motion", "Emotion", "Direction", "Rhythm", "Versatile", "Life", "Journey", "Stories"])
    a0 = ctx.get("start", 2)
    n = a0 + steps + 6
    rows = "".join(f'<div class="{P}r" id="{P}-r{i}" style="position:absolute;left:292px;top:226px;height:104px;white-space:nowrap;font:600 97px/104px Poppins;letter-spacing:-.03em;color:#d2d2d2;transform-origin:-60px 50%;visibility:hidden">{esc(words[i % len(words)])}</div>'
                   for i in range(n))
    arrow = (f'<svg id="{P}-ar" viewBox="0 0 60 40" width="78" height="52" style="position:absolute;left:192px;top:252px" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M4 20h50M36 4l18 16-18 16"/></svg>')
    js = []
    for i in range(n):
        js.append(f'tl.set("#{P}-r{i}", {_wheel_state(i - a0)}, 0);')
    cues = []
    for s in range(steps):
        t = s * period + 0.145
        for i in range(n):
            d0 = i - (a0 + s)
            if -5 <= d0 <= 6:
                js.append(f'tl.fromTo("#{P}-r{i}", {_wheel_state(d0)}, Object.assign({_wheel_state(d0 - 1)}, {{duration: 0.45, ease: PMX.tab({WHEEL_STEP}), immediateRender: false}}), {t:.3f});')
        js.append(f'tl.fromTo("#{P}-ar", {{x: 0}}, {{x: 22, duration: 0.2, ease: "power2.out", immediateRender: false}}, {t:.3f});')
        js.append(f'tl.fromTo("#{P}-ar", {{x: 22}}, {{x: 0, duration: 0.23, ease: "power2.inOut", immediateRender: false}}, {t + 0.2:.3f});')
        cues.append((t + 0.05, "tick"))
    return out(P, stage(P, ctx, w, h, "#000", rows + arrow), "", js, cues, period * steps, (w, h), steps)


# ------------------------------------------------------------------------------------------- 12 toggle
TOG_ON_OFF = [0, 0.06, 0.09, 0.13, 0.19, 0.27, 0.36, 0.46, 0.57, 0.66, 0.73, 0.80, 0.85, 0.89, 0.93, 0.96, 0.98, 1.0]
TOG_OFF_ON = [1.0, 0.96, 0.90, 0.83, 0.71, 0.57, 0.44, 0.34, 0.27, 0.22, 0.17, 0.13, 0.10, 0.09, 0.06, 0.05, 0.03, 0.02, 0.0]


def toggle(P, ctx):
    """A glossy ON/OFF switch slides off, then back on. ctx: on, off (labels), color, loops."""
    w, h, period = 1056, 816, 8.0
    loops = ctx.get("loops", 1)
    green = ctx.get("color", "#3aa846")
    inner = f"""
<div id="{P}-tr" style="position:absolute;left:369px;top:388px;width:317px;height:48px;border-radius:24px;background:linear-gradient(90deg,{green},#59c05c);box-shadow:inset 0 2px 5px rgba(0,0,0,.18)"></div>
<div id="{P}-kn" style="position:absolute;left:335.5px;top:367px;width:137px;height:90px;border-radius:45px;background:linear-gradient(180deg,#ffffff,#e4e6e9);box-shadow:0 8px 16px rgba(0,0,0,.24),inset 0 -4px 7px rgba(0,0,0,.12)">
  <div id="{P}-ki" style="position:absolute;left:11px;top:11px;width:115px;height:68px;border-radius:34px;background:{green};box-shadow:inset 0 3px 8px rgba(0,0,0,.28)"></div>
  <div style="position:absolute;left:16px;top:8px;width:105px;height:26px;border-radius:26px;background:linear-gradient(180deg,rgba(255,255,255,.42),rgba(255,255,255,0))"></div>
  <div id="{P}-on" class="{P}lb">{esc(ctx.get("on", "ON"))}</div><div id="{P}-of" class="{P}lb" style="opacity:0">{esc(ctx.get("off", "OFF"))}</div>
</div>"""
    css = f".{P}lb {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font:600 22px Poppins; letter-spacing:.04em; color:#fff; }}"
    one = f"""
tl.set("#@P-kn", {{x: 0}}, @o); tl.set("#@P-ki", {{backgroundColor: "{green}", opacity: 1}}, @o); tl.set("#@P-on", {{opacity: 1}}, @o); tl.set("#@P-of", {{opacity: 0}}, @o);
tl.fromTo("#@P-tr", {{background: "linear-gradient(90deg,{green},#59c05c)"}}, {{background: "linear-gradient(90deg,#c9c9c9,#bdbdbd)", duration: 0.30, ease: "none", immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-ki", {{backgroundColor: "{green}"}}, {{backgroundColor: "#9a9a9a", duration: 0.30, ease: "none", immediateRender: false}}, @o + 0.03);
tl.fromTo("#@P-kn", {{x: 0}}, {{x: 230, duration: 0.85, ease: PMX.tab({TOG_ON_OFF}), immediateRender: false}}, @o + 0.0);
tl.fromTo("#@P-on", {{opacity: 1}}, {{opacity: 0, duration: 0.08, ease: "none", immediateRender: false}}, @o + 0.46);
tl.fromTo("#@P-of", {{opacity: 0}}, {{opacity: 1, duration: 0.08, ease: "none", immediateRender: false}}, @o + 0.48);
tl.fromTo("#@P-ki", {{opacity: 1}}, {{opacity: 0.5, duration: 0.2, ease: "none", immediateRender: false}}, @o + 0.63);
tl.fromTo("#@P-tr", {{background: "linear-gradient(90deg,#c9c9c9,#bdbdbd)"}}, {{background: "linear-gradient(90deg,{green},#59c05c)", duration: 0.30, ease: "none", immediateRender: false}}, @o + 3.63);
tl.fromTo("#@P-ki", {{backgroundColor: "#9a9a9a", opacity: 0.5}}, {{backgroundColor: "{green}", opacity: 1, duration: 0.30, ease: "none", immediateRender: false}}, @o + 3.63);
tl.fromTo("#@P-kn", {{x: 230}}, {{x: 0, duration: 0.90, ease: PMX.tab({TOG_OFF_ON}), immediateRender: false}}, @o + 3.83);
tl.fromTo("#@P-of", {{opacity: 1}}, {{opacity: 0, duration: 0.08, ease: "none", immediateRender: false}}, @o + 4.24);
tl.fromTo("#@P-on", {{opacity: 0}}, {{opacity: 1, duration: 0.08, ease: "none", immediateRender: false}}, @o + 4.26);
"""
    cues = [(k * period + t, "click") for k in range(loops) for t in (0.1, 3.9)]
    return out(P, stage(P, ctx, w, h, "linear-gradient(135deg,#fcfcfc 0,#e9eaec 45%,#d3d5d8 100%)", inner), css,
               loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 13 list_circle
def list_circle(P, ctx):
    """A soft gradient circle grows, list cards pop onto it, the list scrolls twice, everything shrinks away.
    ctx: items = [(title, subtitle, amount, colour)], loops."""
    w, h, period = 954, 810, 4.0
    loops = ctx.get("loops", 1)
    items = ctx.get("items", [("Birthday gift", "Revenue", "+ $100.00", "#ef6f6c"), ("Shoes", "Clothing", "- $79.00", "#5b5f66"),
                              ("Movie theater", "Entertainment", "- $15.00", "#2b2d31"), ("Sweater", "Clothing", "- $30.00", "#4b8fe2"),
                              ("Music", "Entertainment", "- $10.00", "#9aa0a8")])[:5]
    cards = []
    for i, (t, s, amt, col) in enumerate(items):
        plus = amt.strip().startswith("+")
        cards.append(
            f'<div class="{P}c" id="{P}-c{i}" style="position:absolute;left:252px;top:355px;width:450px;height:100px;border-radius:15px;background:#fff;box-shadow:0 10px 30px rgba(60,70,110,.10);visibility:hidden">'
            f'<div style="position:absolute;left:22px;top:28px;width:44px;height:44px;border-radius:50%;background:#f1f2f5"><div style="position:absolute;left:13px;top:13px;width:18px;height:18px;border-radius:5px;background:{col}"></div></div>'
            f'<div style="position:absolute;left:84px;top:22px;font:500 21px Poppins;color:#17181c">{esc(t)}</div>'
            f'<div style="position:absolute;left:84px;top:55px;font:400 16px Poppins;color:#9a9ca6">{esc(s)}</div>'
            f'<div style="position:absolute;right:22px;top:34px;height:32px;padding:0 13px;border-radius:9px;font:500 15px/32px Poppins;'
            f'background:{"#e3f8ee" if plus else "#f2f3f6"};color:{"#27b97c" if plus else "#6d7079"}">{esc(amt)}</div></div>')
    inner = (f'<div id="{P}-ci" style="position:absolute;left:227px;top:155px;width:500px;height:500px;border-radius:50%;background:linear-gradient(180deg,#c9c6f5 0,#c4dcf2 55%,#c5efd3 100%)"></div>'
             + "".join(cards))
    one = ['tl.set("#@P-ci", {scale: 0}, @o); tl.set(".@Pc", {autoAlpha: 0, scale: 0.8}, @o);',
           'tl.fromTo("#@P-ci", {scale: 0}, {scale: 1, duration: 0.47, ease: "power3.out", immediateRender: false}, @o + 0.0);']
    for i in range(3):
        one.append(f'tl.fromTo("#@P-c{i}", {{autoAlpha: 0, scale: 0.8, y: {(i - 1) * 120}}}, {{autoAlpha: 1, scale: 1, y: {(i - 1) * 120}, duration: 0.24, ease: "back.out(1.8)", immediateRender: false}}, @o + {0.17 + 0.075 * i:.3f});')
    for s, t in enumerate((1.14, 2.14)):
        top, new = s, s + 3
        one.append(f'tl.fromTo("#@P-c{top}", {{y: -120, scale: 1, autoAlpha: 1}}, {{y: -215, scale: 1.2, autoAlpha: 0, duration: 0.42, ease: "power2.inOut", immediateRender: false}}, @o + {t:.2f});')
        for j, c in enumerate((top + 1, top + 2)):
            one.append(f'tl.fromTo("#@P-c{c}", {{y: {j * 120}}}, {{y: {(j - 1) * 120}, duration: 0.53, ease: "power2.inOut", immediateRender: false}}, @o + {t:.2f});')
        one.append(f'tl.fromTo("#@P-c{new}", {{y: 215, scale: 0.85, autoAlpha: 0}}, {{y: 120, scale: 1, autoAlpha: 1, duration: 0.5, ease: "power2.inOut", immediateRender: false}}, @o + {t + 0.03:.2f});')
    for j, c in enumerate((2, 3, 4)):
        one.append(f'tl.fromTo("#@P-c{c}", {{scale: 1, autoAlpha: 1}}, {{scale: 0.8, autoAlpha: 0, duration: 0.16, ease: "power2.in", immediateRender: false}}, @o + {3.17 + 0.075 * j:.3f});')
    one.append('tl.fromTo("#@P-ci", {scale: 1}, {scale: 0, duration: 0.27, ease: "power2.in", immediateRender: false}, @o + 3.27);')
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.0, "swoosh-up"), (0.2, "pop"), (1.2, "swipe"), (2.2, "swipe"), (3.2, "whoosh"))]
    return out(P, stage(P, ctx, w, h, "#eff1f5", inner), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)
