"""24 more scene types for motion graphics (docs/VARIETY_PLAN.md section 4). All code-drawn (HTML + inline SVG):
no pictures of real people, no logos, no brand names drawn (labels come from the narration's own words).

Each type: a fit test (how well a beat's words suit it, 0-1), the roles it serves, and a builder with 2 own
arrangements; with the frame (compose.FRAMES) that makes 4 layouts. register() adds them to the planner.

  ranking  process  cause_effect  pros_cons  checklist  before_after  split  scale  funnel  venn  donut  icon_grid
  table  phone  browser  chat  newspaper  ticker  calendar  countdown  magnifier  reaction  globe  route
"""

import math
import re

from . import design as D
from . import extras as X
from . import templates as T

OWN = 2                     # own arrangements per new type (x 2 with the frame = 4 layouts)


# ---------------------------------------------------------------------------------------------- helpers
def _box(ctx):
    return T._box(ctx)


def _esc(s):
    return T.esc(s)


def _phrase(text, n=3):
    p = T.key_phrase(text, n)
    return p or " ".join(X.picker_words(text)[:n]).upper() or text.upper()[:24]


def _clauses(text, k=4):
    parts = [p.strip(" ,.;:!?") for p in re.split(r",|;| then | and then | which | so that | so | but | because ",
                                                  " " + text + " ", flags=re.I)]
    parts = [p for p in parts if p and X.picker_words(p)]
    return parts[:k]


def _txt(el, text, x, y, w, size, color, font=None, align="center", extra=""):
    return (f'<div id="{el}" style="position:absolute;left:{int(x)}px;top:{int(y)}px;width:{int(w)}px;'
            f'text-align:{align};font-family:\'{font or T.HEAD}\';font-size:{int(size)}px;line-height:1.08;'
            f'color:{color};{extra}">{_esc(text)}</div>')


def _panel(el, x, y, w, h, bg, ink, radius=24, shadow=True, extra=""):
    sh = f"box-shadow:{max(6, int(w) // 40)}px {max(6, int(w) // 40)}px 0 {ink};" if shadow else ""
    return (f'<div id="{el}" style="position:absolute;left:{int(x)}px;top:{int(y)}px;width:{int(w)}px;'
            f'height:{int(h)}px;background:{bg};border:{max(4, int(w) // 90)}px solid {ink};border-radius:{radius}px;'
            f'box-sizing:border-box;{sh}{extra}"></div>')


def _in(sel, t, frm="{opacity: 0, y: 40}", to=None, dur=0.35, ease=None):
    to = to or f"{{opacity: 1, y: 0, duration: {dur}, ease: \"{ease or D.EASE_IN}\"}}"
    return f'tl.fromTo("{sel}", {frm}, {to}, {t:.2f});'


def _pop(sel, t, dur=0.4):
    return X._pop(sel, t, dur)


def _head(P, text, ctx, top):
    return X._head(P, text, ctx, top)


def _at(beat, text, default, ctx):
    return min(X._word_time(beat, text, default), max(0.3, ctx["dur"] - 0.5))


def _out(html, css, js, cues):
    return {"html": "".join(html), "css": css, "js": "\n".join(js), "cues": cues}


def _num(text):
    ns = [v for v, _a, _b in X.numbers(text) if not (1900 <= v <= 2099)]
    return ns


# ------------------------------------------------------------------------------------------------ builders
def ranking(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    items = X.list_items(beat["text"]) or _clauses(beat["text"], 4)
    items = [X._short(i, 2).upper() for i in items][:4] or [_phrase(beat["text"])]
    while len(items) < 3:
        items.append(["#2", "#3", "#4"][len(items) - 1])
    html, js, cues = [], [], []
    n = len(items)
    if v == 0:                                         # bars, longest first
        rh = (y1 - y0) / (n + 0.4)
        for k, it in enumerate(items):
            y = y0 + k * rh
            wbar = (x1 - x0) * (0.86 - 0.16 * k)
            html.append(_txt(f"{P}rk{k}", f"{k + 1}", x0, y, rh * 0.9, rh * 0.7, pal["ink"]))
            html.append(f'<div id="{P}bar{k}" style="position:absolute;left:{int(x0 + rh)}px;top:{int(y + rh * .12)}px;'
                        f'width:{int(wbar - rh)}px;height:{int(rh * .66)}px;background:{pal["pop"] if k == 0 else pal["soft"]};'
                        f'border:5px solid {pal["ink"]};border-radius:14px;box-sizing:border-box"></div>')
            html.append(_txt(f"{P}lb{k}", it, x0 + rh * 1.3, y + rh * .2, wbar - rh * 1.5, rh * .4, pal["ink"],
                             align="left"))
            t = 0.15 + 0.22 * k
            js.append(f'tl.fromTo("#{P}bar{k}", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.45, '
                      f'ease: "{D.EASE_IN}"}}, {t:.2f});')
            js += [_in(f"#{P}rk{k}", t), _in(f"#{P}lb{k}", t + 0.2, "{opacity: 0, x: -30}",
                                             f'{{opacity: 1, x: 0, duration: 0.3, ease: "{D.EASE_IN}"}}')]
            cues.append((t, "tick"))
    else:                                              # podium of three
        order = [1, 0, 2]
        cw = (x1 - x0) / 3.4
        for slot, k in enumerate(order):
            hgt = (y1 - y0) * [0.62, 0.45, 0.32][k]
            x = x0 + (x1 - x0) / 2 - cw * 1.5 + slot * cw * 1.02
            y = y1 - hgt
            html.append(_panel(f"{P}pd{k}", x, y, cw, hgt, pal["pop"] if k == 0 else pal["soft"], pal["ink"], 12))
            html.append(_txt(f"{P}rk{k}", str(k + 1), x, y + hgt * .15, cw, hgt * .4, pal["ink"]))
            html.append(_txt(f"{P}lb{k}", items[k], x - cw * .1, y - H * .075, cw * 1.2, H * .045, pal["ink"]))
            t = 0.2 + 0.25 * (2 - k)
            js.append(f'tl.fromTo("#{P}pd{k}", {{scaleY: 0, transformOrigin: "50% 100%"}}, {{scaleY: 1, duration: 0.45, '
                      f'ease: "{D.EASE_POP}"}}, {t:.2f});')
            js += [_pop(f"#{P}rk{k}", t + 0.2), _in(f"#{P}lb{k}", t + 0.3)]
            cues.append((t, "pop"))
    return _out(html, "", js, cues)


def process(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    steps = [X._short(s, 3).upper() for s in (_clauses(beat["text"], 4) or [beat["text"]])][:4]
    if len(steps) < 2:
        ws = X.picker_words(beat["text"])
        steps = [w.upper() for w in ws[:3]] or ["STEP", "NEXT"]
    n = len(steps)
    html, js, cues = [], [], []
    for k, st in enumerate(steps):
        if v == 0:                                     # a chain left -> right
            bw = (x1 - x0) / (n + (n - 1) * 0.35)
            bx, by, bh = x0 + k * bw * 1.35, y0 + (y1 - y0) * .3, (y1 - y0) * .36
        else:                                          # a staircase
            bw, bh = (x1 - x0) * .42, (y1 - y0) / (n + 0.8)
            bx, by = x0 + k * ((x1 - x0) - bw) / max(1, n - 1), y0 + k * bh * 1.15
        html.append(_panel(f"{P}st{k}", bx, by, bw, bh, "#FFFFFF", "#111111", 20))
        html.append(_txt(f"{P}sn{k}", f"{k + 1}", bx + 12, by - bh * .32, bh * .5, bh * .42, pal["pop"],
                         extra="text-shadow:3px 3px 0 #111111"))
        html.append(_txt(f"{P}sl{k}", st, bx + bw * .06, by + bh * .28, bw * .88,
                         min(bh * .3, T.fit(st, bw * .85, int(bh * .34), 20)), "#111111"))
        t = 0.15 + k * max(0.25, (ctx["dur"] - 0.6) / max(1, n))
        js += [_pop(f"#{P}st{k}", t), _in(f"#{P}sl{k}", t + 0.15), _pop(f"#{P}sn{k}", t + 0.1)]
        cues.append((t, "pop" if k else "swipe"))
        if k and v == 0:
            ax = bx - bw * .3
            html.append(_txt(f"{P}ar{k}", "→", ax, by + bh * .12, bw * .3, bh * .6, pal["ink"]))
            js.append(_in(f"#{P}ar{k}", t - 0.1, "{opacity: 0, x: -30}", '{opacity: 1, x: 0, duration: 0.25}'))
    return _out(html, "", js, cues)


CAUSE_SPLIT = re.compile(r"\b(because|so that|which means|that means|leads? to|led to|thanks to|due to|"
                         r"as a result|therefore|that's why|caused?|so)\b", re.I)


def cause_effect(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = CAUSE_SPLIT.search(beat["text"])
    a, b = (beat["text"][:m.start()], beat["text"][m.end():]) if m else (beat["text"], "")
    if m and m.group(1).lower() in ("because", "due to", "thanks to"):
        a, b = b, a                                    # "B because A": the cause is said second
    la, lb = _phrase(a or beat["text"], 3), _phrase(b or "the result", 3)
    html, js = [], []
    if v == 0:
        bw, bh = (x1 - x0) * .36, (y1 - y0) * .42
        boxes = [(x0, y0 + (y1 - y0) * .25), (x1 - bw, y0 + (y1 - y0) * .25)]
        arrow = (x0 + bw + 10, y0 + (y1 - y0) * .32, (x1 - x0) - 2 * bw - 20, bh * .7)
    else:
        bw, bh = (x1 - x0) * .55, (y1 - y0) * .3
        cx = (x0 + x1) / 2 - bw / 2
        boxes = [(cx, y0), (cx, y1 - bh)]
        arrow = (cx + bw / 2 - bh * .4, y0 + bh, bh * .8, (y1 - y0) - 2 * bh)
    tags = ["CAUSE", "EFFECT"]
    for k, ((bx, by), lab) in enumerate(zip(boxes, (la, lb))):
        html.append(_panel(f"{P}b{k}", bx, by, bw, bh, "#FFFFFF" if k == 0 else pal["pop"], "#111111", 22))
        html.append(_txt(f"{P}t{k}", tags[k], bx, by - H * .055, bw, H * .04, pal["ink"], T.BODY))
        html.append(_txt(f"{P}l{k}", lab, bx + bw * .06, by + bh * .3, bw * .88, T.fit(lab, bw * .85, int(bh * .3), 20),
                         "#111111"))
    t2 = _at(beat, b.split()[0] if b.split() else "", 0.7, ctx) if m else 0.7
    ax, ay, aw, ah = arrow
    rot = 0 if v == 0 else 90
    html.append(f'<svg id="{P}ar" style="position:absolute;left:{int(ax)}px;top:{int(ay)}px" width="{int(aw)}" '
                f'height="{int(ah)}" viewBox="0 0 100 60" preserveAspectRatio="none"><path id="{P}arp" '
                f'd="M5 30 L80 30 M65 12 L88 30 L65 48" fill="none" stroke="{pal["ink"]}" stroke-width="9" '
                f'stroke-linecap="round" style="stroke-dasharray:200;stroke-dashoffset:200" '
                f'transform="rotate({rot} 50 30)"/></svg>')
    js += [_pop(f"#{P}b0", 0.1), _in(f"#{P}l0", 0.25), _in(f"#{P}t0", 0.2),
           f'tl.to("#{P}arp", {{strokeDashoffset: 0, duration: 0.45, ease: "power2.out"}}, {max(0.4, t2 - 0.4):.2f});',
           _pop(f"#{P}b1", t2), _in(f"#{P}l1", t2 + 0.15), _in(f"#{P}t1", t2 + 0.1)]
    return _out(html, "", js, [(0.1, "pop"), (max(0.4, t2 - 0.4), "swipe"), (t2, "impact")])


PRO_SPLIT = re.compile(r"\b(but|however|yet|although|though|while|whereas|on the other hand)\b", re.I)


def pros_cons(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = PRO_SPLIT.search(beat["text"])
    a, b = (beat["text"][:m.start()], beat["text"][m.end():]) if m else (beat["text"], "")
    sides = [(_phrase(a, 3), "✓", "#1FC16B"), (_phrase(b or "the catch", 3), "✗", "#FF3347")]
    html, js = [], []
    t2 = _at(beat, (b.split() or [""])[0], 0.8, ctx) if m else 0.8
    for k, (lab, mark, col) in enumerate(sides):
        if v == 0:
            bw, bh = (x1 - x0) * .44, (y1 - y0) * .8
            bx, by = x0 + k * (x1 - x0) * .56, y0 + (y1 - y0) * .1
        else:
            bw, bh = (x1 - x0) * .8, (y1 - y0) * .4
            bx, by = x0 + (x1 - x0) * .1, y0 + k * (y1 - y0) * .55
        html.append(_panel(f"{P}c{k}", bx, by, bw, bh, "#FFFFFF", "#111111", 26))
        ms = bh * (.38 if v == 0 else .6)
        html.append(f'<div id="{P}m{k}" style="position:absolute;left:{int(bx + (bw - ms) / 2 if v == 0 else bx + bh * .2)}px;'
                    f'top:{int(by + bh * .1)}px;width:{int(ms)}px;height:{int(ms)}px;border-radius:50%;background:{col};'
                    f'color:#FFFFFF;font-family:\'{T.HEAD}\';font-size:{int(ms * .7)}px;line-height:{int(ms)}px;'
                    f'text-align:center">{mark}</div>')
        tx = (bx + bw * .06, by + bh * .6, bw * .88) if v == 0 else (bx + bh * .2 + ms + 20, by + bh * .3, bw - ms - bh * .4)
        html.append(_txt(f"{P}l{k}", lab, tx[0], tx[1], tx[2], T.fit(lab, tx[2] * .95, int(H * .07), 22), "#111111"))
        t = 0.12 if k == 0 else t2
        js += [_in(f"#{P}c{k}", t, "{opacity: 0, y: 80}"), _pop(f"#{P}m{k}", t + 0.15), _in(f"#{P}l{k}", t + 0.2)]
    return _out(html, "", js, [(0.25, "success"), (t2 + 0.15, "error")])


def checklist(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    items = X.list_items(beat["text"]) or _clauses(beat["text"], 4)
    items = [X._short(i, 3).upper() for i in items][:4] or [_phrase(beat["text"])]
    n = len(items)
    html, js, cues = [], [], []
    if v == 1:                                         # a clipboard
        html.append(_panel(f"{P}cb", x0 + (x1 - x0) * .18, y0 - H * .03, (x1 - x0) * .64, (y1 - y0) * 1.03,
                           "#FFFFFF", "#111111", 20))
        html.append(f'<div style="position:absolute;left:{int((x0 + x1) / 2 - W * .06)}px;top:{int(y0 - H * .06)}px;'
                    f'width:{int(W * .12)}px;height:{int(H * .06)}px;background:{pal["pop"]};border:5px solid #111111;'
                    f'border-radius:12px"></div>')
        js.append(_in(f"#{P}cb", 0.02, "{opacity: 0, y: 120, rotation: 4}"))
    rh = (y1 - y0) / (n + 0.5)
    lx = x0 + (x1 - x0) * (.25 if v == 1 else .12)
    ink = "#111111" if v == 1 else pal["ink"]
    for k, it in enumerate(items):
        y = y0 + rh * (k + .25)
        s = rh * .62
        html.append(f'<div id="{P}bx{k}" style="position:absolute;left:{int(lx)}px;top:{int(y)}px;width:{int(s)}px;'
                    f'height:{int(s)}px;border:6px solid {ink};border-radius:10px;box-sizing:border-box;'
                    f'background:{"#FFFFFF" if v == 0 else "transparent"}"></div>')
        html.append(_txt(f"{P}ck{k}", "✓", lx - s * .05, y - s * .35, s * 1.3, s * 1.2, "#1FC16B",
                         extra="text-shadow:2px 2px 0 #111111"))
        right = (x0 + (x1 - x0) * .78) if v == 1 else x1                 # stay on the clipboard
        tw = right - (lx + s * 1.4)
        html.append(_txt(f"{P}it{k}", it, lx + s * 1.4, y + s * .12, tw, T.fit(it, tw * .95, int(s * .7), 18), ink,
                         align="left"))
        t = 0.15 + k * max(0.3, (ctx["dur"] - 0.5) / max(1, n))
        js += [_in(f"#{P}bx{k}", t, "{opacity: 0, x: -40}", '{opacity: 1, x: 0, duration: 0.25}'),
               _in(f"#{P}it{k}", t + 0.05, "{opacity: 0, x: 40}", '{opacity: 1, x: 0, duration: 0.3}'),
               _pop(f"#{P}ck{k}", t + 0.3, 0.3)]
        cues.append((t + 0.3, "tick"))
    return _out(html, "", js, cues)


BA = re.compile(r"\b(before|after|used to|now|was|went from|from|to|then|today)\b", re.I)


def before_after(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = re.search(r"\b(now|after|today|then|to)\b", beat["text"], re.I)
    a, b = (beat["text"][:m.start()], beat["text"][m.end():]) if m else (beat["text"], "")
    la, lb = _phrase(a, 3) or "BEFORE", _phrase(b, 3) or "AFTER"
    html, js = [], []
    bw, bh = (x1 - x0), (y1 - y0) * .78
    by = y0 + (y1 - y0) * .1
    t2 = _at(beat, (b.split() or [""])[0], 0.9, ctx) if m else 0.9
    if v == 0:                                         # one panel, a slider wipes "after" over "before"
        html.append(_panel(f"{P}pa", x0, by, bw, bh, "#FFFFFF", "#111111", 24, False))
        html.append(_txt(f"{P}la", la, x0 + bw * .05, by + bh * .38, bw * .9, T.fit(la, bw * .8, int(bh * .26), 24), "#111111"))
        html.append(f'<div id="{P}pb" style="position:absolute;left:{x0}px;top:{int(by)}px;width:{bw}px;height:{int(bh)}px;'
                    f'background:{pal["pop"]};border:6px solid #111111;border-radius:24px;box-sizing:border-box;'
                    f'clip-path:inset(0 100% 0 0)"></div>')
        html.append(_txt(f"{P}lb", lb, x0 + bw * .05, by + bh * .38, bw * .9, T.fit(lb, bw * .8, int(bh * .26), 24),
                         "#111111", extra="clip-path:inset(0 100% 0 0)"))
        html.append(f'<div id="{P}sl" style="position:absolute;left:{x0}px;top:{int(by - 20)}px;width:10px;height:{int(bh + 40)}px;'
                    f'background:#111111;border-radius:6px"></div>')
        js += [_in(f"#{P}pa", 0.05), _in(f"#{P}la", 0.15),
               f'tl.to("#{P}pb, #{P}lb", {{clipPath: "inset(0 0% 0 0)", duration: 0.7, ease: "power2.inOut"}}, {t2:.2f});',
               f'tl.fromTo("#{P}sl", {{x: 0}}, {{x: {bw - 10}, duration: 0.7, ease: "power2.inOut"}}, {t2:.2f});']
        for k, tag in enumerate(("BEFORE", "AFTER")):
            html.append(_txt(f"{P}tg{k}", tag, x0 + k * bw * .7, by - H * .07, bw * .3, H * .045, pal["ink"], T.BODY))
            js.append(_in(f"#{P}tg{k}", 0.1 if k == 0 else t2))
    else:                                              # two cards with an arrow
        cw = bw * .4
        for k, (lab, tag) in enumerate(((la, "BEFORE"), (lb, "AFTER"))):
            cx = x0 + k * bw * .6
            html.append(_panel(f"{P}c{k}", cx, by, cw, bh, "#FFFFFF" if k == 0 else pal["pop"], "#111111", 24))
            html.append(_txt(f"{P}t{k}", tag, cx, by + bh * .08, cw, H * .04, "#111111", T.BODY))
            html.append(_txt(f"{P}l{k}", lab, cx + cw * .06, by + bh * .4, cw * .88, T.fit(lab, cw * .85, int(bh * .2), 20), "#111111"))
            t = 0.1 if k == 0 else t2
            js += [_in(f"#{P}c{k}", t, "{opacity: 0, rotation: -6, y: 60}"), _in(f"#{P}l{k}", t + .15), _in(f"#{P}t{k}", t + .1)]
        html.append(_txt(f"{P}ar", "➜", x0 + bw * .4, by + bh * .3, bw * .2, bh * .35, pal["ink"]))
        js.append(_pop(f"#{P}ar", t2 - 0.15))
    return _out(html, "", js, [(0.1, "paper"), (t2, "swipe")])


def split(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    sides = X.versus_sides(beat["text"])
    if sides:
        a, b = sides[0], sides[1]
    else:
        m = re.search(r"\b(while|whereas|and|but)\b", beat["text"], re.I)
        a, b = (beat["text"][:m.start()], beat["text"][m.end():]) if m else (beat["text"], "")
    la, lb = _phrase(a, 2), _phrase(b, 2) or "THE OTHER"
    html, js = [], []
    if v == 0:
        html.append(f'<div id="{P}l" style="position:absolute;left:0;top:0;width:{W // 2}px;height:{H}px;background:{pal["soft"]}"></div>'
                    f'<div id="{P}r" style="position:absolute;left:{W // 2}px;top:0;width:{W // 2}px;height:{H}px;background:{pal["pop"]}"></div>'
                    f'<div id="{P}ln" style="position:absolute;left:{W // 2 - 6}px;top:0;width:12px;height:{H}px;background:#111111"></div>')
        js += [f'tl.fromTo("#{P}l", {{x: {-W // 2}}}, {{x: 0, duration: 0.4, ease: "{D.EASE_IN}"}}, 0);',
               f'tl.fromTo("#{P}r", {{x: {W // 2}}}, {{x: 0, duration: 0.4, ease: "{D.EASE_IN}"}}, 0.1);',
               f'tl.fromTo("#{P}ln", {{scaleY: 0}}, {{scaleY: 1, duration: 0.35}}, 0.3);']
        pos = [(W * .06, H * .42, W * .38), (W * .56, H * .42, W * .38)]
    else:
        html.append(f'<svg id="{P}dg" style="position:absolute;left:0;top:0" width="{W}" height="{H}">'
                    f'<polygon points="0,0 {int(W * .62)},0 {int(W * .38)},{H} 0,{H}" fill="{pal["soft"]}"/>'
                    f'<polygon points="{int(W * .62)},0 {W},0 {W},{H} {int(W * .38)},{H}" fill="{pal["pop"]}"/>'
                    f'<line x1="{int(W * .62)}" y1="0" x2="{int(W * .38)}" y2="{H}" stroke="#111111" stroke-width="12"/></svg>')
        js.append(f'tl.fromTo("#{P}dg", {{clipPath: "inset(0 50% 0 50%)"}}, {{clipPath: "inset(0 0% 0 0%)", duration: 0.5, ease: "power3.out"}}, 0);')
        pos = [(W * .05, H * .3, W * .4), (W * .55, H * .58, W * .4)]
    t2 = _at(beat, (b.split() or [""])[0], 0.7, ctx)
    for k, (lab, (x, y, w)) in enumerate(zip((la, lb), pos)):
        html.append(_txt(f"{P}t{k}", lab, x, y, w, T.fit(lab, w * .9, int(H * .12), 30), "#111111"))
        js.append(_in(f"#{P}t{k}", 0.3 if k == 0 else t2, "{opacity: 0, scale: 0.6}",
                      f'{{opacity: 1, scale: 1, duration: 0.35, ease: "{D.EASE_POP}"}}'))
    return _out(html, "", js, [(0.05, "swipe"), (t2, "pop")])


def scale(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = re.search(r"\b(more than|less than|than|outweighs?|versus|vs|over|against)\b", beat["text"], re.I)
    a, b = (beat["text"][:m.start()], beat["text"][m.end():]) if m else (beat["text"], "")
    la, lb = _phrase(a, 2), _phrase(b, 2) or "THE REST"
    heavy_left = not re.search(r"\bless than|cheaper|lighter|fewer\b", beat["text"], re.I)
    cx, top = (x0 + x1) / 2, y0 + (y1 - y0) * .25
    arm = (x1 - x0) * .38
    ink = pal["ink"]
    html = [f'<div id="{P}post" style="position:absolute;left:{int(cx - 10)}px;top:{int(top)}px;width:20px;height:{int((y1 - top) * .9)}px;background:{ink};border-radius:8px"></div>',
            f'<div style="position:absolute;left:{int(cx - W * .08)}px;top:{int(y1 - H * .05)}px;width:{int(W * .16)}px;height:{int(H * .04)}px;background:{ink};border-radius:12px"></div>']
    pan = (x1 - x0) * (.22 if v == 0 else .18)
    beam = (f'<div id="{P}beam" style="position:absolute;left:{int(cx - arm)}px;top:{int(top)}px;width:{int(2 * arm)}px;height:0">'
            f'<div style="position:absolute;left:0;top:-8px;width:100%;height:16px;background:{ink};border-radius:8px"></div>')
    for k, lab in enumerate((la, lb)):
        px = (0 if k == 0 else 2 * arm) - pan / 2
        shape = "border-radius:0 0 50% 50%" if v == 0 else "border-radius:50%"
        beam += (f'<div style="position:absolute;left:{int(px)}px;top:{int(H * .05)}px;width:{int(pan)}px;height:{int(pan * (.45 if v == 0 else 1))}px;'
                 f'background:{pal["pop"] if k == 0 else "#FFFFFF"};border:6px solid #111111;box-sizing:border-box;{shape}"></div>'
                 f'<div style="position:absolute;left:{int(px - pan * .2)}px;top:{int(H * .05 + pan * (.5 if v == 0 else 1.05))}px;width:{int(pan * 1.4)}px;'
                 f'text-align:center;font-family:\'{T.HEAD}\';font-size:{T.fit(lab, pan * 1.3, int(H * .06), 20)}px;color:{ink}">{_esc(lab)}</div>')
    html.append(beam + "</div>")
    tilt = -9 if heavy_left else 9
    t2 = _at(beat, (b.split() or [""])[0], 0.8, ctx)
    js = [_in(f"#{P}post", 0.05, "{scaleY: 0, transformOrigin: \"50% 100%\"}", '{scaleY: 1, duration: 0.3}'),
          _in(f"#{P}beam", 0.15, "{opacity: 0, y: -40}"),
          f'tl.fromTo("#{P}beam", {{rotation: 0}}, {{rotation: {tilt}, duration: 0.8, ease: "elastic.out(1, 0.5)"}}, {t2:.2f});']
    return _out(html, "", js, [(0.15, "pop"), (t2, "boing")])


def funnel(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    ns = _num(beat["text"])
    labels = [f"{n:,.0f}" for n in sorted(ns, reverse=True)[:3]] or []
    words = [X._short(c, 2).upper() for c in _clauses(beat["text"], 3)]
    labels = (labels + words + ["ALL", "SOME", "FEW"])[:3]
    html, js, cues = [], [], []
    cx = (x0 + x1) / 2
    lh = (y1 - y0) / 3.3
    for k, lab in enumerate(labels):
        wtop = (x1 - x0) * (.9 - .25 * k)
        wbot = (x1 - x0) * (.9 - .25 * (k + 1))
        y = y0 + k * lh * 1.08
        if v == 0:
            pts = f"{cx - wtop / 2:.0f},0 {cx + wtop / 2:.0f},0 {cx + wbot / 2:.0f},{lh:.0f} {cx - wbot / 2:.0f},{lh:.0f}"
            html.append(f'<svg id="{P}f{k}" style="position:absolute;left:0;top:{int(y)}px" width="{W}" height="{int(lh)}">'
                        f'<polygon points="{pts}" fill="{[pal["pop"], pal["soft"], "#FFFFFF"][k]}" stroke="#111111" stroke-width="6"/></svg>')
        else:
            r = lh * .45 * (1 - .22 * k)
            html.append(f'<div id="{P}f{k}" style="position:absolute;left:{int(cx - wtop / 2)}px;top:{int(y)}px;width:{int(wtop)}px;'
                        f'height:{int(lh * .8)}px;border-radius:{int(r)}px;background:{[pal["pop"], pal["soft"], "#FFFFFF"][k]};'
                        f'border:6px solid #111111;box-sizing:border-box"></div>')
        html.append(_txt(f"{P}l{k}", lab, cx - wbot / 2, y + lh * .25, wbot, T.fit(lab, wbot * .9, int(lh * .45), 18), "#111111"))
        t = 0.12 + k * 0.3
        js += [_in(f"#{P}f{k}", t, "{opacity: 0, scaleX: 1.3}", f'{{opacity: 1, scaleX: 1, duration: 0.35, ease: "{D.EASE_POP}"}}'),
               _in(f"#{P}l{k}", t + 0.12)]
        cues.append((t, "pop"))
    return _out(html, "", js, cues)


def venn(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    ws = X.picker_words(beat["text"])
    la, lb = (ws[0].upper() if ws else "THIS"), (ws[1].upper() if len(ws) > 1 else "THAT")
    mid = (ws[2].upper() if len(ws) > 2 else "BOTH")
    r = (y1 - y0) * .42
    cx, cy = (x0 + x1) / 2, y0 + (y1 - y0) * .5
    off = r * .62
    pos = [(cx - off, cy), (cx + off, cy)] if v == 0 else [(cx, cy - off * .55), (cx, cy + off * .55)]
    html, js = [], []
    cols = [pal["pop"], "#FFFFFF"]
    for k, ((x, y), lab) in enumerate(zip(pos, (la, lb))):
        html.append(f'<div id="{P}c{k}" style="position:absolute;left:{int(x - r)}px;top:{int(y - r)}px;width:{int(2 * r)}px;'
                    f'height:{int(2 * r)}px;border-radius:50%;background:{cols[k]};opacity:.85;border:7px solid #111111;'
                    f'box-sizing:border-box;mix-blend-mode:multiply"></div>')
        lx = x - r * (.95 if (k == 0 and v == 0) else (-.15 if v == 0 else .5))
        ly = y - (r * .1 if v == 0 else (r * .75 if k == 0 else -r * .55))
        html.append(_txt(f"{P}l{k}", lab, lx, ly, r * .85, T.fit(lab, r * .8, int(r * .26), 18), "#111111"))
        js += [_pop(f"#{P}c{k}", 0.1 + 0.25 * k, 0.45), _in(f"#{P}l{k}", 0.3 + 0.25 * k)]
    html.append(_txt(f"{P}m", mid, cx - r * .45, cy - r * .12, r * .9, T.fit(mid, r * .8, int(r * .22), 16), "#111111",
                     extra="text-decoration:underline"))
    js.append(_pop(f"#{P}m", min(1.0, ctx["dur"] - 0.4)))
    return _out(html, "", js, [(0.1, "pop"), (0.35, "pop"), (min(1.0, ctx["dur"] - 0.4), "ding")])


def donut(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    pct = X.percent(beat["text"])
    pct = 50.0 if pct is None else pct
    r = (y1 - y0) * .4
    cx, cy = (x0 + x0 + (x1 - x0) * .62) / 2, (y0 + y1) / 2
    rr, stroke = (38, 20) if v == 0 else (22, 44)        # ring / pie (a 44-wide stroke on r 22 fills the disc)
    circ = 2 * math.pi * rr
    on = circ * pct / 100
    html = [f'<svg id="{P}d" style="position:absolute;left:{int(cx - r)}px;top:{int(cy - r)}px" width="{int(2 * r)}" height="{int(2 * r)}" viewBox="0 0 100 100">'
            f'<circle cx="50" cy="50" r="{rr + stroke / 2 + 2:.0f}" fill="{"#FFFFFF" if v == 0 else pal["soft"]}" stroke="#111111" stroke-width="3"/>'
            f'<circle cx="50" cy="50" r="{rr}" fill="none" stroke="{pal["soft"] if v == 0 else "#FFFFFF"}" stroke-width="{stroke}"/>'
            f'<circle id="{P}arc" cx="50" cy="50" r="{rr}" fill="none" stroke="{pal["pop"]}" stroke-width="{stroke}" '
            f'stroke-linecap="{"round" if v == 0 else "butt"}" transform="rotate(-90 50 50)" '
            f'style="stroke-dasharray:{on:.1f} {circ:.1f};stroke-dashoffset:{on:.1f}"/></svg>',
            _txt(f"{P}n", f"{pct:.0f}%", cx - r * .7, (cy - r * .3) if v == 0 else (cy + r * 1.02), r * 1.4,
                 r * (.5 if v == 0 else .34), "#111111" if v == 0 else pal["ink"])]
    lab = _phrase(beat["text"], 3)
    lx = x0 + (x1 - x0) * .64
    html.append(_txt(f"{P}l", lab, lx, cy - H * .08, x1 - lx, T.fit(lab, (x1 - lx) * .95, int(H * .09), 24), pal["ink"], align="left"))
    js = [_pop(f"#{P}d", 0.05, 0.4), f'tl.to("#{P}arc", {{strokeDashoffset: 0, duration: 0.9, ease: "power2.out"}}, 0.25);',
          _pop(f"#{P}n", 0.5), _in(f"#{P}l", 0.4, "{opacity: 0, x: 60}", '{opacity: 1, x: 0, duration: 0.35}')]
    return _out(html, "", js, [(0.25, "riser"), (1.1, "ding")])


def _ratio(text):
    m = re.search(r"\bone in (\w+)", text, re.I)
    if m:
        n = X.numbers(m.group(1))
        if n and n[0][0] > 1:
            return 1, int(min(20, n[0][0]))
    p = X.percent(text)
    if p is not None:
        return max(1, round(p / 10)), 10
    return None


def icon_grid(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    hit, total = _ratio(beat["text"]) or (3, 10)
    cols = 5 if total <= 10 else 10
    rows = math.ceil(total / cols)
    cell = min((x1 - x0) * .62 / cols, (y1 - y0) * .8 / rows)
    gx = x0
    html, js = [], []
    for k in range(total):
        x, y = gx + (k % cols) * cell, y0 + (y1 - y0) * .1 + (k // cols) * cell * 1.05
        col = pal["pop"] if k < hit else "#FFFFFF"
        if v == 0:                                   # little people (head + body)
            html.append(f'<div id="{P}g{k}" style="position:absolute;left:{int(x + cell * .2)}px;top:{int(y)}px;width:{int(cell * .6)}px;height:{int(cell)}px">'
                        f'<div style="position:absolute;left:{int(cell * .15)}px;top:0;width:{int(cell * .3)}px;height:{int(cell * .3)}px;border-radius:50%;background:{col};border:4px solid #111111;box-sizing:border-box"></div>'
                        f'<div style="position:absolute;left:0;top:{int(cell * .34)}px;width:{int(cell * .6)}px;height:{int(cell * .56)}px;border-radius:{int(cell * .3)}px {int(cell * .3)}px 8px 8px;background:{col};border:4px solid #111111;box-sizing:border-box"></div></div>')
        else:
            html.append(f'<div id="{P}g{k}" style="position:absolute;left:{int(x + 4)}px;top:{int(y + 4)}px;width:{int(cell * .86)}px;height:{int(cell * .86)}px;'
                        f'border-radius:12px;background:{col};border:4px solid #111111;box-sizing:border-box"></div>')
        js.append(_pop(f"#{P}g{k}", 0.08 + k * 0.04, 0.3))
    big = f"{hit} IN {total}"
    lx = x0 + (x1 - x0) * .66
    html.append(_txt(f"{P}b", big, lx, y0 + (y1 - y0) * .25, x1 - lx, T.fit(big, (x1 - lx), int(H * .14), 30), pal["ink"]))
    lab = _phrase(beat["text"], 3)
    html.append(_txt(f"{P}l", lab, lx, y0 + (y1 - y0) * .55, x1 - lx, T.fit(lab, (x1 - lx), int(H * .06), 18), pal["ink"], T.BODY))
    js += [_pop(f"#{P}b", 0.3 + total * 0.04), _in(f"#{P}l", 0.5 + total * 0.04)]
    return _out(html, "", js, [(0.08, "tick"), (0.3 + total * 0.04, "ding")])


SPEC = re.compile(r"\b(\d[\d,.]*|\w+) ?(gb|gigabytes?|tb|ram|hours?|cores?|inches|grams?|kilos?|watts?|mah|ghz|"
                  r"dollars?|rupees?|pounds?|euros?|percent|nits|hz|frames|fps|points?|apps?)\b", re.I)


def table(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    rows = []
    for m in SPEC.finditer(beat["text"]):
        val = m.group(1)
        n = X.numbers(val)
        val = f"{n[0][0]:,.0f}" if n else val
        rows.append((m.group(2).upper(), val))
    if not rows:
        rows = [(w.upper(), "✓") for w in X.picker_words(beat["text"])[:3]]
    rows = rows[:4]
    html, js, cues = [], [], []
    tw = (x1 - x0) * (.8 if v == 0 else .9)
    tx = x0 + ((x1 - x0) - tw) / 2
    head = _phrase(beat["text"], 3)
    rh = (y1 - y0) / (len(rows) + 1.6)
    if v == 0:
        html.append(_panel(f"{P}t", tx, y0, tw, rh * (len(rows) + 1.2), "#FFFFFF", "#111111", 18))
        html.append(f'<div style="position:absolute;left:{int(tx)}px;top:{int(y0)}px;width:{int(tw)}px;height:{int(rh)}px;background:{pal["pop"]};border:6px solid #111111;border-radius:18px 18px 0 0;box-sizing:border-box"></div>')
        html.append(_txt(f"{P}h", head, tx, y0 + rh * .2, tw, T.fit(head, tw * .9, int(rh * .5), 18), "#111111"))
        js.append(_in(f"#{P}t", 0.03, "{opacity: 0, y: 60}"))
        js.append(_in(f"#{P}h", 0.1))
    for k, (key, val) in enumerate(rows):
        y = y0 + rh * (k + 1.1)
        if v == 0:
            html.append(f'<div style="position:absolute;left:{int(tx + 20)}px;top:{int(y + rh * .95)}px;width:{int(tw - 40)}px;height:3px;background:#DDDDDD"></div>')
            html.append(_txt(f"{P}k{k}", key, tx + tw * .06, y + rh * .2, tw * .45, rh * .45, "#111111", T.BODY, "left"))
            html.append(_txt(f"{P}v{k}", val, tx + tw * .5, y + rh * .15, tw * .44, rh * .55, "#111111", align="right"))
        else:
            cw = tw / len(rows)
            cx = tx + k * cw
            html.append(_panel(f"{P}c{k}", cx + 10, y0 + rh * .5, cw - 20, rh * 3, "#FFFFFF", "#111111", 20))
            html.append(_txt(f"{P}v{k}", val, cx + 10, y0 + rh * 1.0, cw - 20, T.fit(val, cw * .8, int(rh * 1.1), 20), "#111111"))
            html.append(_txt(f"{P}k{k}", key, cx + 10, y0 + rh * 2.5, cw - 20, rh * .45, "#111111", T.BODY))
            js.append(_pop(f"#{P}c{k}", 0.1 + 0.2 * k))
        t = 0.25 + 0.2 * k
        js += [_in(f"#{P}k{k}", t), _in(f"#{P}v{k}", t + 0.1, "{opacity: 0, scale: 0.5}", f'{{opacity: 1, scale: 1, duration: 0.3, ease: "{D.EASE_POP}"}}')]
        cues.append((t + 0.1, "tick"))
    return _out(html, "", js, cues)


def phone(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    ph_h = (y1 - y0) * 1.05
    ph_w = ph_h * .5
    px, py = x0 + (x1 - x0) * (.12 if v == 0 else .58), y0 - (y1 - y0) * .03
    head = _phrase(beat["text"], 4)
    html = [f'<div id="{P}ph" style="position:absolute;left:{int(px)}px;top:{int(py)}px;width:{int(ph_w)}px;height:{int(ph_h)}px;'
            f'background:#1B1B22;border:8px solid #111111;border-radius:{int(ph_w * .16)}px;box-sizing:border-box;box-shadow:14px 14px 0 rgba(0,0,0,.25)">'
            f'<div style="position:absolute;left:6%;right:6%;top:3%;bottom:3%;background:{pal["soft"]};border-radius:{int(ph_w * .11)}px"></div>'
            f'<div style="position:absolute;left:38%;width:24%;top:4.5%;height:3%;background:#111111;border-radius:20px"></div></div>']
    js = [_in(f"#{P}ph", 0.02, "{opacity: 0, y: 160, rotation: -6}", f'{{opacity: 1, y: 0, rotation: 0, duration: 0.5, ease: "{D.EASE_IN}"}}')]
    nw = ph_w * .86
    for k in range(2 if v == 1 else 1):
        ny = py + ph_h * (.18 + .2 * k)
        nx = px + (ph_w - nw) / 2
        lab = head if k == 0 else _phrase(beat["text"][len(beat["text"]) // 2:], 3)
        html.append(f'<div id="{P}n{k}" style="position:absolute;left:{int(nx)}px;top:{int(ny)}px;width:{int(nw)}px;height:{int(ph_h * .15)}px;'
                    f'background:#FFFFFF;border:4px solid #111111;border-radius:22px;box-sizing:border-box">'
                    f'<div style="position:absolute;left:5%;top:22%;width:{int(ph_h * .07)}px;height:{int(ph_h * .07)}px;border-radius:12px;background:{pal["pop"]}"></div>'
                    f'<div style="position:absolute;left:30%;right:4%;top:18%;font-family:\'{T.HEAD}\';font-size:{T.fit(lab, nw * .65, int(ph_h * .05), 14)}px;color:#111111;line-height:1.05">{_esc(lab)}</div></div>')
        t = 0.45 + 0.35 * k
        js.append(_in(f"#{P}n{k}", t, "{opacity: 0, y: -60, scale: 0.9}", f'{{opacity: 1, y: 0, scale: 1, duration: 0.35, ease: "{D.EASE_POP}"}}'))
    tx = px + ph_w + W * .04 if v == 0 else x0
    tw = (x1 - tx) if v == 0 else (px - x0 - W * .04)
    big = _phrase(beat["text"], 2)
    html.append(_txt(f"{P}hd", big, tx, y0 + (y1 - y0) * .35, tw, T.fit(big, tw * .95, int(H * .13), 28), pal["ink"], align="left"))
    js.append(_in(f"#{P}hd", 0.55, "{opacity: 0, x: 60}", '{opacity: 1, x: 0, duration: 0.35}'))
    return _out(html, "", js, [(0.02, "swipe"), (0.45, "notification")])


def browser(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    bw, bh = (x1 - x0) * .92, (y1 - y0) * 1.0
    bx, by = x0 + (x1 - x0) * .04, y0 - (y1 - y0) * .02
    head = _phrase(beat["text"], 4)
    bar = bh * .1
    html = [f'<div id="{P}w" style="position:absolute;left:{int(bx)}px;top:{int(by)}px;width:{int(bw)}px;height:{int(bh)}px;background:#FFFFFF;'
            f'border:7px solid #111111;border-radius:22px;box-sizing:border-box;overflow:hidden;box-shadow:16px 16px 0 rgba(0,0,0,.22)">'
            f'<div style="position:absolute;left:0;right:0;top:0;height:{int(bar)}px;background:{pal["soft"]};border-bottom:5px solid #111111"></div>'
            + "".join(f'<div style="position:absolute;left:{int(bar * (.4 + .5 * k))}px;top:{int(bar * .32)}px;width:{int(bar * .36)}px;height:{int(bar * .36)}px;border-radius:50%;background:{c};border:3px solid #111111"></div>'
                      for k, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")))
            + (f'<div style="position:absolute;left:{int(bar * 2.2)}px;right:{int(bar * .6)}px;top:{int(bar * .22)}px;height:{int(bar * .56)}px;background:#FFFFFF;border:3px solid #111111;border-radius:30px"></div>' if v == 0 else "")
            + (f'<div style="position:absolute;left:0;top:{int(bar)}px;bottom:0;width:{int(bw * .22)}px;background:{pal["soft"]};border-right:5px solid #111111"></div>' if v == 1 else "")
            + "</div>"]
    js = [_in(f"#{P}w", 0.02, "{opacity: 0, scale: 0.8}", f'{{opacity: 1, scale: 1, duration: 0.45, ease: "{D.EASE_POP}"}}')]
    cx = bx + (bw * .26 if v == 1 else bw * .06)
    cw = bw - (cx - bx) - bw * .06
    html.append(_txt(f"{P}h", head, cx, by + bar * 1.6, cw, T.fit(head, cw * .95, int(bh * .14), 24), "#111111", align="left"))
    js.append(_in(f"#{P}h", 0.3))
    for k in range(3):
        y = by + bar * 1.6 + bh * (.22 + .13 * k)
        html.append(f'<div id="{P}r{k}" style="position:absolute;left:{int(cx)}px;top:{int(y)}px;width:{int(cw * (.9 - .2 * (k % 2)))}px;height:{int(bh * .07)}px;'
                    f'background:{pal["pop"] if k == 0 else "#E8E8E8"};border-radius:12px"></div>')
        js.append(f'tl.fromTo("#{P}r{k}", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.35, ease: "{D.EASE_IN}"}}, {0.45 + 0.12 * k:.2f});')
    if v == 0:                                       # a pointer clicking the first row
        html.append(_txt(f"{P}cur", "➤", cx + cw * .5, by + bh * .9, H * .08, H * .07, "#111111",
                         extra="transform:rotate(-120deg)"))
        js.append(f'tl.fromTo("#{P}cur", {{x: 200, y: 120, opacity: 0}}, {{x: 0, y: {-int(bh * .38)}, opacity: 1, duration: 0.6, ease: "power2.inOut"}}, 0.7);')
    return _out(html, "", js, [(0.02, "pop"), (1.25, "click")])


def chat(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    parts = _clauses(beat["text"], 3) or [beat["text"]]
    if len(parts) == 1:
        ws = beat["text"].split()
        parts = [" ".join(ws[:len(ws) // 2]), " ".join(ws[len(ws) // 2:])] if len(ws) > 5 else parts
    html, js, cues = [], [], []
    bh = (y1 - y0) / (len(parts) + .6)
    for k, ptxt in enumerate(parts):
        right = k % 2 == 1
        lab = X._short(ptxt, 5) if len(ptxt.split()) > 6 else ptxt
        lab = lab.strip().capitalize()
        bw = (x1 - x0) * .62
        ax = x1 - bh * .55 if right else x0
        bx = (ax - bw - 16) if right else (x0 + bh * .7)
        y = y0 + k * bh * 1.12
        html.append(f'<div id="{P}a{k}" style="position:absolute;left:{int(ax)}px;top:{int(y + bh * .2)}px;width:{int(bh * .5)}px;height:{int(bh * .5)}px;'
                    f'border-radius:50%;background:{pal["pop"] if right else "#FFFFFF"};border:5px solid #111111;box-sizing:border-box"></div>')
        style = (f"background:{pal['pop'] if right else '#FFFFFF'};border:5px solid #111111;"
                 f"border-radius:{'28px 28px 6px 28px' if right else '28px 28px 28px 6px'};" if v == 0 else
                 f"background:#FFFFFF;border-left:12px solid {pal['pop'] if right else '#111111'};border-radius:8px;")
        html.append(f'<div id="{P}b{k}" style="position:absolute;left:{int(bx)}px;top:{int(y)}px;width:{int(bw)}px;min-height:{int(bh * .8)}px;'
                    f'{style}box-sizing:border-box;padding:{int(bh * .14)}px {int(bh * .22)}px;font-family:\'{T.BODY}\';'
                    f'font-size:{T.fit(lab, bw * 1.6, int(bh * .26), 18, 0.5)}px;color:#111111;line-height:1.2">{_esc(lab)}</div>')
        t = _at(beat, ptxt, 0.12 + 0.5 * k, ctx)
        js += [_pop(f"#{P}a{k}", t, 0.3), _in(f"#{P}b{k}", t + 0.05, "{opacity: 0, scale: 0.6}",
                                             f'{{opacity: 1, scale: 1, duration: 0.3, ease: "{D.EASE_POP}"}}')]
        cues.append((t, "notification" if k == 0 else "pop"))
    return _out(html, "", js, cues)


def newspaper(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    head = _phrase(beat["text"], 4)
    pw, ph = (x1 - x0) * (.7 if v == 0 else .62), (y1 - y0) * 1.05
    px, py = x0 + ((x1 - x0) - pw) / 2, y0 - (y1 - y0) * .04
    html = [f'<div id="{P}p" style="position:absolute;left:{int(px)}px;top:{int(py)}px;width:{int(pw)}px;height:{int(ph)}px;background:#FBF8F0;'
            f'border:6px solid #111111;box-sizing:border-box;box-shadow:16px 16px 0 rgba(0,0,0,.25)">'
            f'<div style="position:absolute;left:4%;right:4%;top:3%;text-align:center;font-family:\'{T.HEAD}\';font-size:{int(ph * .085)}px;color:#111111;'
            f'border-bottom:5px double #111111;padding-bottom:1%">THE DAILY BRIEF</div>'
            f'<div style="position:absolute;left:4%;right:4%;top:19%;font-family:\'{T.HEAD}\';font-size:{T.fit(head, pw * .9, int(ph * .13), 24)}px;'
            f'color:#111111;line-height:1">{_esc(head)}</div>'
            + "".join(f'<div style="position:absolute;left:{4 + 31 * c}%;width:28%;top:{48 + 6 * r}%;height:2.4%;background:#BBBBBB;border-radius:4px"></div>'
                      for c in range(3) for r in range(7))
            + "</div>"]
    if v == 0:
        js = [f'tl.fromTo("#{P}p", {{scale: 0.1, rotation: 720, opacity: 0}}, {{scale: 1, rotation: -3, opacity: 1, duration: 0.7, ease: "power3.out"}}, 0.02);']
    else:
        js = [_in(f"#{P}p", 0.02, "{opacity: 0, y: 200, rotation: 8}", '{opacity: 1, y: 0, rotation: 2, duration: 0.5, ease: "back.out(1.6)"}')]
        html.append(f'<div id="{P}tag" style="position:absolute;left:{int(px - W * .03)}px;top:{int(py + ph * .1)}px;background:{pal["pop"]};'
                    f'border:5px solid #111111;font-family:\'{T.HEAD}\';font-size:{int(H * .045)}px;padding:.1em .5em;transform:rotate(-8deg);color:#111111">BREAKING</div>')
        js.append(_pop(f"#{P}tag", 0.55))
    return _out(html, "", js, [(0.02, "paper"), (0.6, "stamp")])


def ticker(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    up = not re.search(r"\b(fell|fall\w*|drop\w*|down|lost|los(e|s)|crash\w*|plung\w*|slump\w*|cut)\b", beat["text"], re.I)
    pct = X.percent(beat["text"])
    ns = _num(beat["text"])
    val = f"{'+' if up else '-'}{pct:.0f}%" if pct is not None else (f"{ns[0]:,.0f}" if ns else ("UP" if up else "DOWN"))
    col = "#1FC16B" if up else "#FF3347"
    lab = _phrase(beat["text"], 2)
    cw, chh = (x1 - x0) * .6, (y1 - y0) * .62
    cx, cy = x0 + ((x1 - x0) - cw) / 2, y0
    pts = [(k / 7, .5 + (.35 if not up else -.35) * (k / 7) + (.12 if k % 2 else -.08)) for k in range(8)]
    path = " ".join(f"{'M' if k == 0 else 'L'}{x * 100:.0f} {y * 60:.0f}" for k, (x, y) in enumerate(pts))
    html = [_panel(f"{P}c", cx, cy, cw, chh, "#FFFFFF", "#111111", 22),
            _txt(f"{P}l", lab, cx + cw * .05, cy + chh * .07, cw * .55, chh * .13, "#111111", align="left"),
            _txt(f"{P}v", val + (" ▲" if up else " ▼"), cx + cw * .5, cy + chh * .05, cw * .46, chh * .16, col, align="right"),
            f'<svg style="position:absolute;left:{int(cx + cw * .05)}px;top:{int(cy + chh * .3)}px" width="{int(cw * .9)}" height="{int(chh * .62)}" viewBox="0 0 100 60" preserveAspectRatio="none">'
            f'<path id="{P}ln" d="{path}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linejoin="round" style="stroke-dasharray:300;stroke-dashoffset:300"/></svg>']
    js = [_in(f"#{P}c", 0.02, "{opacity: 0, y: 60}"), _in(f"#{P}l", 0.15), _pop(f"#{P}v", 0.9),
          f'tl.to("#{P}ln", {{strokeDashoffset: 0, duration: 0.9, ease: "power1.inOut"}}, 0.2);']
    if v == 1 or True:                                # the tape under the card
        tape = "   ".join(f"{w.upper()} {'▲' if (k + up) % 2 else '▼'}" for k, w in enumerate(X.picker_words(beat["text"])[:6] or ["MARKET"]))
        html.append(f'<div style="position:absolute;left:0;width:{W}px;top:{int(y1 - (y1 - y0) * .2)}px;height:{int(H * .075)}px;background:#111111;overflow:hidden">'
                    f'<div id="{P}tp" style="white-space:nowrap;font-family:\'{T.HEAD}\';font-size:{int(H * .05)}px;color:{pal["hi"] if pal["hi"] != "#111111" else "#FFD21F"};line-height:{int(H * .075)}px">'
                    f'{_esc((tape + "      ") * 4)}</div></div>')
        js.append(f'tl.fromTo("#{P}tp", {{x: 0}}, {{x: {-int(W * (.5 if v == 0 else .8))}, duration: {max(1.5, ctx["dur"]):.2f}, ease: "none"}}, 0);')
    return _out(html, "", js, [(0.2, "riser" if up else "error"), (0.9, "cash" if up else "error")])


MONTHS = "january february march april may june july august september october november december".split()


def calendar(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    low = beat["text"].lower()
    month = next((m for m in MONTHS if re.search(rf"\b{m}\b", low)), None)
    day = next((int(v_) for v_, _a, _b in X.numbers(beat["text"]) if 1 <= v_ <= 31), None)
    ys = X.years(beat["text"])
    top = (month or ("YEAR" if ys else "THIS WEEK")).upper()
    day = day or 14
    html, js = [], []
    if v == 0:                                        # a month page with the day circled
        pw, ph = (x1 - x0) * .42, (y1 - y0) * 1.0
        px, py = x0 + (x1 - x0) * .05, y0 - (y1 - y0) * .02
        html.append(_panel(f"{P}pg", px, py, pw, ph, "#FFFFFF", "#111111", 18))
        html.append(f'<div style="position:absolute;left:{int(px)}px;top:{int(py)}px;width:{int(pw)}px;height:{int(ph * .2)}px;background:{pal["pop"]};border:6px solid #111111;border-radius:18px 18px 0 0;box-sizing:border-box"></div>')
        html.append(_txt(f"{P}m", top + (f" {ys[0]}" if ys else ""), px, py + ph * .04, pw, ph * .11, "#111111"))
        cell = pw / 7.4
        for d in range(1, 29):
            r, c = (d - 1) // 7, (d - 1) % 7
            hit = d == min(day, 28)
            html.append(f'<div id="{P}d{d}" style="position:absolute;left:{int(px + cell * (.2 + c))}px;top:{int(py + ph * .26 + r * cell * 1.05)}px;width:{int(cell * .9)}px;height:{int(cell * .9)}px;'
                        f'text-align:center;line-height:{int(cell * .9)}px;font-family:\'{T.BODY}\';font-size:{int(cell * .4)}px;color:#111111;'
                        f'{"border:5px solid " + pal["pop"] + ";border-radius:50%;box-sizing:border-box" if hit else ""}">{d}</div>')
        js += [_in(f"#{P}pg", 0.02, "{opacity: 0, rotationX: 80, transformPerspective: 900, transformOrigin: \"50% 0%\"}",
                   '{opacity: 1, rotationX: 0, duration: 0.5, ease: "power2.out"}'),
               _in(f"#{P}m", 0.2), _pop(f"#{P}d{min(day, 28)}", 0.6)]
        lab = _phrase(beat["text"], 3)
        lx = px + pw + W * .04
        html.append(_txt(f"{P}l", lab, lx, y0 + (y1 - y0) * .35, x1 - lx, T.fit(lab, (x1 - lx) * .95, int(H * .1), 24), pal["ink"], align="left"))
        js.append(_in(f"#{P}l", 0.45, "{opacity: 0, x: 60}", '{opacity: 1, x: 0, duration: 0.35}'))
    else:                                             # a week strip, one day lit
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        cw = (x1 - x0) / 7.3
        hit = day % 7
        for k, d in enumerate(days):
            cx = x0 + k * cw * 1.04
            html.append(_panel(f"{P}w{k}", cx, y0 + (y1 - y0) * .3, cw, cw * 1.3, pal["pop"] if k == hit else "#FFFFFF", "#111111", 16, k == hit))
            html.append(_txt(f"{P}t{k}", d, cx, y0 + (y1 - y0) * .3 + cw * .45, cw, cw * .3, "#111111"))
            js.append(_in(f"#{P}w{k}", 0.05 + 0.06 * k, "{opacity: 0, y: -50}", '{opacity: 1, y: 0, duration: 0.25}'))
            js.append(_in(f"#{P}t{k}", 0.1 + 0.06 * k))
        js.append(f'tl.fromTo("#{P}w{hit}", {{y: 0}}, {{y: -30, duration: 0.2, yoyo: true, repeat: 1, ease: "power2.out"}}, 0.8);')
        html.append(_txt(f"{P}m", top, x0, y0, x1 - x0, H * .09, pal["ink"]))
        js.append(_in(f"#{P}m", 0.1))
    return _out(html, "", js, [(0.02, "paper"), (0.6, "tick")])


def countdown(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = re.search(r"\b(\w+(?: \w+)?) (hours?|minutes?|seconds?|days?|weeks?|months?|years?)\b", beat["text"], re.I)
    n = X.numbers(m.group(1)) if m else []
    amount = int(n[-1][0]) if n else None
    unit = (m.group(2) if m else "hours").upper()
    lab = f"{amount} {unit}" if amount is not None else _phrase(beat["text"], 2)
    r = (y1 - y0) * .42
    cx, cy = x0 + (x1 - x0) * .3, (y0 + y1) / 2
    html, js = [], []
    if v == 0:                                        # an analog clock, the hand sweeping
        html.append(f'<div id="{P}ck" style="position:absolute;left:{int(cx - r)}px;top:{int(cy - r)}px;width:{int(2 * r)}px;height:{int(2 * r)}px;border-radius:50%;'
                    f'background:#FFFFFF;border:{int(r * .08)}px solid #111111;box-sizing:border-box">'
                    + "".join(f'<div style="position:absolute;left:{int(r - 6)}px;top:{int(r * .08)}px;width:12px;height:{int(r * .14)}px;background:#111111;transform-origin:6px {int(r * .92)}px;transform:rotate({a}deg)"></div>' for a in range(0, 360, 30))
                    + f'<div id="{P}hm" style="position:absolute;left:{int(r - 8)}px;top:{int(r * .3)}px;width:16px;height:{int(r * .7)}px;background:#111111;border-radius:8px;transform-origin:8px {int(r * .7)}px"></div>'
                    f'<div id="{P}hs" style="position:absolute;left:{int(r - 5)}px;top:{int(r * .16)}px;width:10px;height:{int(r * .84)}px;background:{pal["pop"]};border-radius:5px;transform-origin:5px {int(r * .84)}px"></div></div>')
        js += [_pop(f"#{P}ck", 0.02, 0.45),
               f'tl.fromTo("#{P}hs", {{rotation: 0}}, {{rotation: 720, duration: {max(1.2, ctx["dur"] - 0.2):.2f}, ease: "power1.inOut"}}, 0.2);',
               f'tl.fromTo("#{P}hm", {{rotation: 0}}, {{rotation: 60, duration: {max(1.2, ctx["dur"] - 0.2):.2f}, ease: "power1.inOut"}}, 0.2);']
    else:                                             # a digital counter
        start = amount or 10
        html.append(_panel(f"{P}pn", cx - r * 1.1, cy - r * .55, r * 2.2, r * 1.1, "#111111", "#111111", 24))
        html.append(f'<div id="{P}dg" style="position:absolute;left:{int(cx - r)}px;top:{int(cy - r * .4)}px;width:{int(2 * r)}px;text-align:center;'
                    f'font-family:\'{T.HEAD}\';font-size:{int(r * .7)}px;color:#FF3347;letter-spacing:.05em">00:00</div>')
        js += [_pop(f"#{P}pn", 0.02, 0.4),
               f'const cd = {{v: {start * 60}}}; tl.to(cd, {{v: {max(0, start * 60 - 37)}, duration: {max(1.2, ctx["dur"] - 0.3):.2f}, ease: "none", '
               f'onUpdate: () => {{ const s = Math.round(cd.v); document.querySelector("#{P}dg").textContent = '
               f'String(Math.floor(s / 60) % 100).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0"); }}}}, 0.2);']
    lx = x0 + (x1 - x0) * .62
    html.append(_txt(f"{P}l", lab, lx, cy - H * .07, x1 - lx, T.fit(lab, (x1 - lx) * .95, int(H * .11), 24), pal["ink"], align="left"))
    js.append(_in(f"#{P}l", 0.3, "{opacity: 0, x: 60}", '{opacity: 1, x: 0, duration: 0.35}'))
    return _out(html, "", js, [(0.2, "tick"), (0.8, "tick")])


def magnifier(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    head = _phrase(beat["text"], 3)
    dw, dh = (x1 - x0) * .78, (y1 - y0) * .9
    dx, dy = x0 + ((x1 - x0) - dw) / 2, y0
    html = [_panel(f"{P}doc", dx, dy, dw, dh, "#FFFFFF" if v == 0 else pal["soft"], "#111111", 18, True)]
    rows = 7
    for k in range(rows):
        if v == 0:
            html.append(f'<div style="position:absolute;left:{int(dx + dw * .07)}px;top:{int(dy + dh * (.1 + .12 * k))}px;width:{int(dw * (.86 - .1 * (k % 3)))}px;height:{int(dh * .04)}px;background:#D6D6D6;border-radius:6px"></div>')
        else:
            for c in range(9):
                html.append(f'<div style="position:absolute;left:{int(dx + dw * (.06 + .1 * c))}px;top:{int(dy + dh * (.08 + .12 * k))}px;width:{int(dw * .07)}px;height:{int(dh * .07)}px;background:#FFFFFF;border:2px solid #111111;border-radius:6px"></div>')
    lr = dh * .3
    tx, ty = dx + dw * .55, dy + dh * .45
    html.append(f'<div id="{P}lens" style="position:absolute;left:{int(tx - lr)}px;top:{int(ty - lr)}px;width:{int(2 * lr)}px;height:{int(2 * lr)}px">'
                f'<div style="position:absolute;inset:0;border-radius:50%;background:rgba(255,255,255,.92);border:{int(lr * .14)}px solid #111111;box-sizing:border-box"></div>'
                f'<div style="position:absolute;left:{int(lr * 1.6)}px;top:{int(lr * 1.6)}px;width:{int(lr * .26)}px;height:{int(lr * .9)}px;background:#111111;border-radius:12px;transform:rotate(-45deg);transform-origin:50% 0"></div>'
                f'<div style="position:absolute;left:{int(lr * .16)}px;top:{int(lr * .62)}px;width:{int(lr * 1.68)}px;text-align:center;font-family:\'{T.HEAD}\';'
                f'font-size:{T.fit(head, lr * 1.6, int(lr * .5), 16)}px;color:#111111;line-height:1">{_esc(head)}</div></div>')
    js = [_in(f"#{P}doc", 0.02, "{opacity: 0, y: 60}"),
          f'tl.fromTo("#{P}lens", {{x: {-int(dw * .45)}, y: {-int(dh * .25)}, scale: 0.6, opacity: 0}}, {{x: 0, y: 0, scale: 1, opacity: 1, duration: 0.8, ease: "power2.inOut"}}, 0.2);',
          f'tl.to("#{P}lens", {{scale: 1.12, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.out"}}, 1.0);']
    return _out(html, "", js, [(0.2, "swipe"), (1.0, "ding")])


def reaction(P, beat, ctx):
    W, H, pal, v, rnd = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN, ctx["rnd"]
    x0, x1, y0, y1 = _box(ctx)
    head = _phrase(beat["text"], 3)
    html = [_txt(f"{P}h", head, x0, y0 + (y1 - y0) * .35, x1 - x0, T.fit(head, (x1 - x0) * .8, int(H * .14), 30), pal["ink"],
                 extra=f"text-shadow:0 8px 0 {pal['soft']}")]
    js = [_pop(f"#{P}h", 0.1, 0.45)]
    marks = ["♥", "!", "★", "?!", "♥", "★", "!", "♥", "★", "!!"]
    cols = ["#FF3347", "#FFD21F", "#FFFFFF", "#2F6BFF", "#FF5DA2"]
    for k, mk in enumerate(marks):
        s = int(H * (.07 + rnd.random() * .06))
        ang = 2 * math.pi * k / len(marks) + rnd.random() * .3
        rx, ry = (x1 - x0) * .42, (y1 - y0) * .46
        cx, cy = (x0 + x1) / 2 + math.cos(ang) * rx, y0 + (y1 - y0) * .45 + math.sin(ang) * ry
        bub = (f"width:{s * 1.6:.0f}px;height:{s * 1.6:.0f}px;border-radius:50%;background:{cols[k % len(cols)]};"
               f"border:4px solid #111111;box-sizing:border-box;line-height:{s * 1.5:.0f}px;" if v == 0 else "")
        html.append(f'<div id="{P}r{k}" style="position:absolute;left:{int(cx - s * .8)}px;top:{int(cy - s * .8)}px;{bub}text-align:center;'
                    f'font-family:\'{T.HEAD}\';font-size:{s}px;color:{"#111111" if v == 0 else cols[k % len(cols)]};'
                    f'{"" if v == 0 else "text-shadow:3px 3px 0 #111111"}">{mk}</div>')
        t = 0.25 + k * 0.07
        if v == 0:
            js.append(f'tl.fromTo("#{P}r{k}", {{x: {int(((x0 + x1) / 2 - cx) * .9)}, y: {int((y0 + (y1 - y0) * .45 - cy) * .9)}, scale: 0}}, '
                      f'{{x: 0, y: 0, scale: 1, duration: 0.45, ease: "{D.EASE_POP}"}}, {t:.2f});')
        else:
            js.append(f'tl.fromTo("#{P}r{k}", {{y: {int(H * .25)}, opacity: 0}}, {{y: {-int(H * .1)}, opacity: 1, duration: {max(0.8, ctx["dur"] - t):.2f}, ease: "power1.out"}}, {t:.2f});')
    return _out(html, "", js, [(0.1, "impact"), (0.3, "crowd-gasp" if v == 0 else "pop")])


def globe(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    r = (y1 - y0) * .46
    cx, cy = x0 + (x1 - x0) * (.3 if v == 0 else .5), (y0 + y1) / 2
    mer = "".join(f'<ellipse class="{P}mer" cx="50" cy="50" rx="{rx}" ry="46" fill="none" stroke="#111111" stroke-width="1.6"/>'
                  for rx in (10, 24, 36))
    par = "".join(f'<line x1="{50 - math.sqrt(max(0, 46 ** 2 - (y - 50) ** 2)):.1f}" y1="{y}" x2="{50 + math.sqrt(max(0, 46 ** 2 - (y - 50) ** 2)):.1f}" y2="{y}" stroke="#111111" stroke-width="1.6"/>'
                  for y in (22, 36, 50, 64, 78))
    blobs = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{a}" ry="{b}" fill="#1FC16B" stroke="#111111" stroke-width="1.5"/>'
                    for x, y, a, b in ((34, 34, 12, 8), (60, 30, 9, 6), (56, 60, 14, 9), (30, 66, 7, 10)))
    html = [f'<svg id="{P}g" style="position:absolute;left:{int(cx - r)}px;top:{int(cy - r)}px" width="{int(2 * r)}" height="{int(2 * r)}" viewBox="0 0 100 100">'
            f'<circle cx="50" cy="50" r="46" fill="#2F6BFF" stroke="#111111" stroke-width="4"/>'
            f'<g id="{P}land">{blobs}</g>{mer}{par}</svg>']
    js = [_pop(f"#{P}g", 0.02, 0.5),
          f'tl.fromTo("#{P}land", {{x: -30}}, {{x: 30, duration: {max(1.2, ctx["dur"]):.2f}, ease: "none"}}, 0);']
    if v == 1:                                        # an orbit ring with a dot
        html.append(f'<div id="{P}orb" style="position:absolute;left:{int(cx - r * 1.35)}px;top:{int(cy - r * .4)}px;width:{int(r * 2.7)}px;height:{int(r * .8)}px;'
                    f'border:6px dashed {pal["ink"]};border-radius:50%;box-sizing:border-box;transform:rotate(-14deg)"></div>')
        js.append(f'tl.fromTo("#{P}orb", {{scale: 0.3, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.5, ease: "{D.EASE_POP}"}}, 0.25);')
        lab = _phrase(beat["text"], 3)
        html.append(_txt(f"{P}l", lab, x0, y0 - H * .02, x1 - x0, T.fit(lab, (x1 - x0) * .8, int(H * .09), 24), pal["ink"]))
    else:
        lab = _phrase(beat["text"], 3)
        lx = cx + r + W * .04
        html.append(_txt(f"{P}l", lab, lx, cy - H * .08, x1 - lx, T.fit(lab, (x1 - lx) * .95, int(H * .11), 24), pal["ink"], align="left"))
    js.append(_in(f"#{P}l", 0.35))
    return _out(html, "", js, [(0.02, "whoosh"), (0.4, "pop")])


def route(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    m = re.search(r"\bfrom (.+?) (?:to|into) (.+)", beat["text"], re.I)
    a, b = (_phrase(m.group(1), 2), _phrase(m.group(2), 2)) if m else (_phrase(beat["text"][:len(beat["text"]) // 2], 2),
                                                                          _phrase(beat["text"][len(beat["text"]) // 2:], 2))
    p0, p1 = (x0 + (x1 - x0) * .1, y0 + (y1 - y0) * .75), (x0 + (x1 - x0) * .88, y0 + (y1 - y0) * .3)
    if v == 0:
        d = f"M{p0[0]:.0f} {p0[1]:.0f} Q {(p0[0] + p1[0]) / 2:.0f} {y0 - (y1 - y0) * .2:.0f} {p1[0]:.0f} {p1[1]:.0f}"
    else:
        d = f"M{p0[0]:.0f} {p0[1]:.0f} L {(p0[0] + p1[0]) / 2:.0f} {p0[1]:.0f} L {(p0[0] + p1[0]) / 2:.0f} {p1[1]:.0f} L {p1[0]:.0f} {p1[1]:.0f}"
    html = [f'<svg style="position:absolute;left:0;top:0" width="{W}" height="{H}"><path id="{P}rt" d="{d}" fill="none" stroke="{pal["ink"]}" '
            f'stroke-width="12" stroke-linecap="round" stroke-dasharray="4 30" style="stroke-dashoffset:0"/>'
            f'<path id="{P}rm" d="{d}" fill="none" stroke="{pal["bg"]}" stroke-width="18" style="stroke-dasharray:3000;stroke-dashoffset:0"/></svg>']
    for k, ((x, y), lab) in enumerate(zip((p0, p1), (a, b))):
        s = H * .09
        html.append(f'<div id="{P}pin{k}" style="position:absolute;left:{int(x - s / 2)}px;top:{int(y - s * 1.1)}px;width:{int(s)}px;height:{int(s)}px;'
                    f'border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:{pal["pop"] if k else "#FFFFFF"};border:6px solid #111111;box-sizing:border-box"></div>')
        html.append(_txt(f"{P}l{k}", lab, x - W * .15, y + H * .02, W * .3, T.fit(lab, W * .28, int(H * .06), 18), pal["ink"]))
    t_end = max(0.9, min(ctx["dur"] - 0.4, 1.4))
    js = [_pop(f"#{P}pin0", 0.05), _in(f"#{P}l0", 0.15),
          f'tl.fromTo("#{P}rm", {{strokeDashoffset: 0}}, {{strokeDashoffset: -3000, duration: {t_end:.2f}, ease: "power1.inOut"}}, 0.25);',
          _pop(f"#{P}pin1", t_end), _in(f"#{P}l1", t_end + 0.1)]
    return _out(html, "", js, [(0.05, "pop"), (0.25, "whoosh"), (t_end, "ding")])


# ----------------------------------------------------------- format host scenes (fit any line; one format each)
def dashboard(P, beat, ctx):
    """Data Lab / Tech Desk: KPI tiles. The key phrase is the tile title; the mini charts are decoration only
    (no invented numbers)."""
    W, H, pal, v, rnd = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN, ctx["rnd"]
    x0, x1, y0, y1 = _box(ctx)
    head = _phrase(beat["text"], 3)
    html, js = [], []
    if v == 0:
        tiles = [(x0, y0, (x1 - x0) * .58, (y1 - y0) * .55, "big"), (x0 + (x1 - x0) * .62, y0, (x1 - x0) * .38, (y1 - y0) * .55, "ring"),
                 (x0, y0 + (y1 - y0) * .6, (x1 - x0) * .38, (y1 - y0) * .4, "bars"), (x0 + (x1 - x0) * .42, y0 + (y1 - y0) * .6, (x1 - x0) * .58, (y1 - y0) * .4, "line")]
    else:
        tiles = [(x0, y0 + (y1 - y0) * .05, x1 - x0, (y1 - y0) * .5, "big"), (x0, y0 + (y1 - y0) * .6, (x1 - x0) * .48, (y1 - y0) * .4, "line"),
                 (x0 + (x1 - x0) * .52, y0 + (y1 - y0) * .6, (x1 - x0) * .48, (y1 - y0) * .4, "bars")]
    for k, (tx, ty, tw, th, kind) in enumerate(tiles):
        html.append(_panel(f"{P}t{k}", tx, ty, tw - 12, th - 12, "#FFFFFF", "#111111", 18))
        ix, iy, iw, ih = tx + tw * .08, ty + th * .2, tw * .8, th * .6
        if kind == "big":
            html.append(_txt(f"{P}c{k}", head, ix, iy + ih * .2, iw, T.fit(head, iw * .95, int(ih * .45), 22), "#111111", align="left"))
        elif kind == "ring":
            r = min(iw, ih) * .45
            html.append(f'<svg id="{P}c{k}" style="position:absolute;left:{int(ix + iw / 2 - r)}px;top:{int(iy + ih / 2 - r)}px" width="{int(2 * r)}" height="{int(2 * r)}" viewBox="0 0 100 100">'
                        f'<circle cx="50" cy="50" r="38" fill="none" stroke="{pal["soft"]}" stroke-width="14"/>'
                        f'<circle id="{P}rg" cx="50" cy="50" r="38" fill="none" stroke="{pal["pop"]}" stroke-width="14" stroke-linecap="round" '
                        f'transform="rotate(-90 50 50)" style="stroke-dasharray:{150 + rnd.random() * 60:.0f} 239;stroke-dashoffset:239"/></svg>')
            js.append(f'tl.to("#{P}rg", {{strokeDashoffset: 0, duration: 0.9, ease: "power2.out"}}, {0.25 + 0.12 * k:.2f});')
        elif kind == "bars":
            n = 6
            for j in range(n):
                hh = ih * (.3 + .7 * rnd.random())
                html.append(f'<div id="{P}b{k}_{j}" style="position:absolute;left:{int(ix + j * iw / n)}px;top:{int(iy + ih - hh)}px;width:{int(iw / n * .7)}px;height:{int(hh)}px;'
                            f'background:{pal["pop"] if j == n - 1 else pal["soft"]};border-radius:6px"></div>')
                js.append(f'tl.fromTo("#{P}b{k}_{j}", {{scaleY: 0, transformOrigin: "50% 100%"}}, {{scaleY: 1, duration: 0.4, ease: "{D.EASE_IN}"}}, {0.3 + 0.05 * j:.2f});')
        else:
            pts = " ".join(f"{'M' if j == 0 else 'L'}{j * 100 / 9:.0f} {50 - 35 * (j / 9) + 12 * rnd.random() - 6:.0f}" for j in range(10))
            html.append(f'<svg style="position:absolute;left:{int(ix)}px;top:{int(iy)}px" width="{int(iw)}" height="{int(ih)}" viewBox="0 0 100 60" preserveAspectRatio="none">'
                        f'<path id="{P}ln{k}" d="{pts}" fill="none" stroke="{pal["pop"]}" stroke-width="3.5" style="stroke-dasharray:300;stroke-dashoffset:300"/></svg>')
            js.append(f'tl.to("#{P}ln{k}", {{strokeDashoffset: 0, duration: 0.9, ease: "power1.inOut"}}, {0.3 + 0.1 * k:.2f});')
        js.append(_in(f"#{P}t{k}", 0.04 + 0.08 * k, "{opacity: 0, y: 40}"))
        if kind == "big":
            js.append(_in(f"#{P}c{k}", 0.2))
    return _out(html, "", js, [(0.05, "tick"), (0.3, "riser")])


def terminal(P, beat, ctx):
    """Tech Desk: the key phrase typed into a code window, then a check line."""
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = _box(ctx)
    words = [w for w in re.sub(r"[^\w\s']", " ", beat["text"]).lower().split()][:9]
    cmd = ("$ " if v == 0 else "") + " ".join(words)
    ww, wh = (x1 - x0) * .9, (y1 - y0) * .95
    wx, wy = x0 + (x1 - x0) * .05, y0
    bar = wh * .1
    fs = T.fit(cmd, ww * 1.5, int(wh * .1), 18, 0.6)
    html = [f'<div id="{P}w" style="position:absolute;left:{int(wx)}px;top:{int(wy)}px;width:{int(ww)}px;height:{int(wh)}px;background:#0B0F17;'
            f'border:3px solid {pal["pop"]};border-radius:16px;box-sizing:border-box;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5)">'
            f'<div style="position:absolute;left:0;right:0;top:0;height:{int(bar)}px;background:#161C28"></div>'
            + "".join(f'<div style="position:absolute;left:{int(bar * (.4 + .5 * k))}px;top:{int(bar * .32)}px;width:{int(bar * .36)}px;height:{int(bar * .36)}px;border-radius:50%;background:{c}"></div>'
                      for k, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")))
            + (''.join(f'<div style="position:absolute;left:{int(bar * .3)}px;top:{int(bar * 1.4 + j * fs * 1.6)}px;font-family:\'{T.BODY}\';font-size:{int(fs * .8)}px;color:#4A5568">{j + 1}</div>' for j in range(5)) if v == 1 else "")
            + "</div>"]
    tx = wx + (bar * 1.2 if v == 1 else bar * .4)
    html.append(f'<div id="{P}cmd" style="position:absolute;left:{int(tx)}px;top:{int(wy + bar * 1.4)}px;width:{int(ww - (tx - wx) - bar * .4)}px;'
                f'font-family:\'{T.BODY}\';font-size:{fs}px;line-height:1.5;color:{pal["pop"]};white-space:pre-wrap"></div>')
    ok = "✓ " + _phrase(beat["text"], 2).lower()
    html.append(f'<div id="{P}ok" style="position:absolute;left:{int(tx)}px;top:{int(wy + wh * .7)}px;font-family:\'{T.BODY}\';font-size:{fs}px;color:#5CF0C8">{_esc(ok)}</div>')
    dur = min(1.4, max(0.6, ctx["dur"] - 0.8))
    js = [_in(f"#{P}w", 0.02, "{opacity: 0, scale: 0.92}", f'{{opacity: 1, scale: 1, duration: 0.35, ease: "{D.EASE_POP}"}}'),
          f'const ty = {{n: 0}}; const full = {cmd!r}; tl.to(ty, {{n: full.length, duration: {dur:.2f}, ease: "none", '
          f'onUpdate: () => {{ document.querySelector("#{P}cmd").textContent = full.slice(0, Math.round(ty.n)) + "▍"; }}}}, 0.25);',
          _in(f"#{P}ok", 0.3 + dur, "{opacity: 0, x: -20}", '{opacity: 1, x: 0, duration: 0.25}')]
    return _out(html, "", js, [(0.25, "typing"), (0.3 + dur, "keyboard-enter")])


def sticky(P, beat, ctx):
    """Paper Notebook: sticky notes taped to the page with the line's key words."""
    W, H, pal, v, rnd = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN, ctx["rnd"]
    x0, x1, y0, y1 = _box(ctx)
    cols = ["#FFE97A", "#B8F2D0", "#FFC2D1", "#BFD7FF"]
    notes = [_phrase(beat["text"], 3)] if v == 0 else [_phrase(c, 2) for c in (_clauses(beat["text"], 3) or [beat["text"]])][:3]
    if v == 1 and len(notes) < 2:
        notes.append(" ".join(X.picker_words(beat["text"])[-2:]).upper() or "NOTE")
    n = len(notes)
    html, js = [], []
    for k, note in enumerate(notes):
        sz = (y1 - y0) * (.85 if n == 1 else .6)
        nx = x0 + ((x1 - x0) - sz) / 2 if n == 1 else x0 + k * ((x1 - x0) - sz) / max(1, n - 1)
        ny = y0 + (0 if n == 1 else (k % 2) * (y1 - y0) * .3)
        rot = rnd.uniform(-5, 5)
        html.append(f'<div id="{P}n{k}" style="position:absolute;left:{int(nx)}px;top:{int(ny)}px;width:{int(sz)}px;height:{int(sz)}px;'
                    f'background:{cols[(k + int(rnd.random() * 4)) % 4]};transform:rotate({rot:.1f}deg);box-shadow:0 10px 18px rgba(0,0,0,.18)">'
                    f'<div style="position:absolute;left:35%;top:-6%;width:30%;height:12%;background:rgba(255,255,255,.55);transform:rotate(-4deg)"></div>'
                    f'<div style="position:absolute;left:8%;right:8%;top:22%;font-family:\'{T.HEAD}\';font-size:{T.fit(note, sz * 1.5, int(sz * .2), 18, 0.42)}px;'
                    f'line-height:1.05;color:#1F2A44;text-align:center">{_esc(note)}</div></div>')
        t = 0.1 + 0.3 * k
        js.append(f'tl.fromTo("#{P}n{k}", {{y: -120, opacity: 0, rotation: {rot - 12:.1f}}}, {{y: 0, opacity: 1, rotation: {rot:.1f}, duration: 0.45, ease: "back.out(1.6)"}}, {t:.2f});')
    if n > 1:
        js.append(f'/* notes in a row */')
    return _out(html, "", js, [(0.1, "paper")] + [(0.1 + 0.3 * k, "paper") for k in range(1, n)])


# ---------------------------------------------------------------------------------------------- planner specs
def _rx(p):
    c = re.compile(p, re.I)
    return lambda b, st: 1.0 if c.search(b["text"]) else 0.0


def _and(*fs, w=1.0):
    return lambda b, st: w * min(f(b, st) for f in fs)


def _or(*fs, w=1.0):
    return lambda b, st: w * max(f(b, st) for f in fs)


def _roles(*rs, w=1.0):
    return lambda b, st: w if set(rs) & st["roles"] else 0.0


def _generic(w):
    """A small base fit for any beat with a headline-worthy phrase (keeps the planner off the word scenes)."""
    return lambda b, st: w if len(X.picker_words(b["text"])) >= 2 else 0.0


_list = lambda b, st: 1.0 if X.list_items(b["text"]) else 0.0          # noqa: E731
_pct = lambda b, st: 1.0 if X.percent(b["text"]) is not None else 0.0  # noqa: E731
_two_clauses = lambda b, st: 1.0 if len(_clauses(b["text"], 4)) >= 2 else 0.0  # noqa: E731

SPECS = {
    "ranking": ({"list": 0.9, "comparison": 0.6, "statistic": 0.4}, True,
                _or(_and(_list, _rx(r"\b(top|most|biggest|largest|best|fastest|first|leaders?|ranks?|ranked|win\w*)\b")),
                    _rx(r"\b(number one|top (three|five|ten)|ranked|rankings?|leaderboard)\b"), w=0.85)),
    "process": ({"process": 1.0, "list": 0.5}, True,
                _and(_two_clauses, _or(_roles("process"), _rx(r"\b(then|next|after|step|first|finally)\b")), w=0.8)),
    "cause_effect": ({"cause": 1.0, "conclusion": 0.4}, True, _and(lambda b, st: 1.0 if CAUSE_SPLIT.search(b["text"]) else 0.0,
                                                                   lambda b, st: 1.0 if len(b["text"].split()) >= 6 else 0.0, w=0.8)),
    "pros_cons": ({"warning": 0.9, "comparison": 0.7}, True,
                  _and(lambda b, st: 1.0 if PRO_SPLIT.search(b["text"]) else 0.0,
                       lambda b, st: 1.0 if len(b["text"].split()) >= 6 else 0.0, w=0.75)),
    "checklist": ({"list": 1.0, "process": 0.5}, True,
                  _or(_list, _rx(r"\b(need|needs|must|should|have to|requires?|check)\b"), w=0.7)),
    "before_after": ({"timeline": 0.8, "comparison": 0.8}, True,
                     _rx(r"\b(before|after|used to|went from|from \w+ to|back then|nowadays|these days|now)\b")),
    "split": ({"comparison": 1.0}, True,
              _or(lambda b, st: 1.0 if X.versus_sides(b["text"]) else 0.0, _rx(r"\b(while|whereas|on the other hand)\b"), w=0.8)),
    "scale": ({"comparison": 0.9, "statistic": 0.4}, True,
              _rx(r"\b(more than|less than|outweighs?|heavier|lighter|worth|bigger than|cheaper than|costs? (more|less))\b")),
    "funnel": ({"statistic": 0.8, "process": 0.4}, True,
               _rx(r"\b(only|out of|down to|narrow\w*|remain\w*|left with|filter\w*|shrink\w*)\b")),
    "venn": ({"comparison": 0.7, "definition": 0.6}, True,
             _rx(r"\b(both|in common|overlap\w*|at the same time|combin\w*|mix of|as well as)\b")),
    "donut": ({"statistic": 1.0}, True, _pct),
    "icon_grid": ({"statistic": 1.0}, True, _or(_rx(r"\bone in \w+|\bout of (every )?\w+"), _pct, w=0.9)),
    "table": ({"statistic": 0.9, "comparison": 0.6}, True, lambda b, st: 1.0 if SPEC.search(b["text"]) else 0.0),
    "phone": ({"story": 0.7, "warning": 0.5}, False,
              _rx(r"\b(phones?|apps?|notifications?|texts?|messages?|alerts?|pings?|iphones?|android|smartphones?|screen)\b")),
    "browser": ({"story": 0.7, "definition": 0.5}, False,
                _rx(r"\b(websites?|web|online|browsers?|search\w*|downloads?|software|updates?|programs?|apps?|windows|"
                    r"internet|sites?|developers?|code)\b")),
    "chat": ({"question": 0.8, "story": 0.5}, False,
             _and(_rx(r"\b(said|says|asked|asks|told|tells|replied|answer\w*|ask|tell|say|people|users|customers)\b"),
                  lambda b, st: 1.0 if len(b["text"].split()) >= 6 else 0.0, w=0.75)),
    "newspaper": ({"story": 0.8, "quote": 0.6}, False,
                  _or(_rx(r"\b(reported|news|headlines?|announced|launched|unveiled|revealed|released|according to|"
                          r"reviews?|reviewers?|press)\b"), _generic(0.08))),
    "ticker": ({"statistic": 0.9}, True,
               _and(_rx(r"\b(stocks?|shares?|markets?|investors?|prices?|valuation|sales|revenue|profits?)\b"),
                    _or(_pct, _rx(r"\b(rose|rise|rising|fell|fall\w*|up|down|jump\w*|drop\w*|grew|grow\w*)\b")), w=0.9)),
    "calendar": ({"timeline": 1.0}, True,
                 _rx(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
                     r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|this week|next week|every day)\b")),
    "countdown": ({"statistic": 0.7, "timeline": 0.5}, True,
                  _rx(r"\b(\w+ (hours?|minutes?|seconds?)|deadline|countdown|all day|battery life|lasts?|clock)\b")),
    "magnifier": ({"definition": 0.9, "question": 0.5, "story": 0.4}, False,
                  _or(_rx(r"\b(details?|closer|look(ed|ing)? at|actually|fine print|hidden|notice\w*|spot\w*|benchmarks?|"
                          r"tests?|tested|measur\w*|examin\w*|inspect\w*|in fact)\b"), _generic(0.1))),
    "reaction": ({"conclusion": 0.6, "warning": 0.5, "story": 0.4}, False,
                 _or(_rx(r"\b(wow|shock\w*|loved?|hate[ds]?|viral|fans|everyone|reactions?|crazy|insane|angry|furious|"
                         r"excited|thrilled|disappoint\w*|amazing|surpris\w*)\b"),
                     lambda b, st: 0.06 if X.picker_words(b["text"]) and len(b["text"].split()) <= 6 else 0.0)),
    "globe": ({"story": 0.6, "statistic": 0.5}, True,
              _rx(r"\b(world|global\w*|worldwide|international\w*|everywhere|countries|planet|earth)\b")),
    "route": ({"process": 0.6, "story": 0.6}, True,
              _rx(r"\b(from \w+ (to|into) \w+|ship\w*|shipping|travel\w*|routes?|across|deliver\w*|moved? to|journey)\b")),
}
_any = lambda b, st: 0.12 if len(X.picker_words(b["text"])) >= 2 else 0.0      # noqa: E731
SPECS.update({
    "dashboard": ({"statistic": 0.7, "story": 0.5, "comparison": 0.4}, True, _any),
    "terminal": ({"story": 0.6, "process": 0.5, "definition": 0.5}, False, _any),
    "sticky": ({"story": 0.6, "list": 0.5, "conclusion": 0.5}, False, _any),
})
HOSTS = {"dashboard", "terminal", "sticky"}           # each format bans the ones that aren't its own
BUILDERS = {n: globals()[n] for n in SPECS}


def register():
    from . import planner as PL
    for name, (roles, data, fits) in SPECS.items():
        PL.register(name, {"roles": roles, "data": data, "fits": fits}, layouts=OWN * 2)
        PL.OWN_LAYOUTS[name] = OWN


def build(name, P, beat, ctx):
    return BUILDERS[name](P, beat, ctx)
