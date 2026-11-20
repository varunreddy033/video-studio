"""Studio-sizzle blocks: rebuilt from the GSAP showcase of github.com/iart-ai/motion-skills (showcase.html, MIT,
commit 9b9ce04, (c) 2026 iart.ai). Only the motion is taken; every word comes from the script (no iart.ai / "Motion
Skills" text), the back.out eases are our closed-form springs (spring.py), and the random stagger is a seeded order
(HyperFrames renders frames in several tabs: Math.random would differ between them).

All six share the look: dark violet radial backdrop, three slowly drifting blurred colour blobs, film grain.
Unlike the measured premium blocks these don't loop: ctx["dur"] (the beat's length) stretches the hold, with a slow
drift so no frame is dead; the exit plays in the last 0.5 s when the beat is long enough.

  char_flip      small kicker + huge word: letters flip up in 3D, then spiral into a point
  serif_scatter  italic serif phrase: letters rise in a scattered order with a slant
  outline_slam   outline word slams in from 5x with blur from the centre + a screen shake
  three_beat     three words, three colours, three entrances (rise / slide / pop + bounce)
  crop_lockup    two-line lockup, corner crop marks snap in, amber rule, kicker
  signature_dot  closing word with an amber full stop that pops and pulses inside a crop frame
"""
import random

from .core import esc, out, stage

W0, H0 = 1920, 1080
INK, MUTED, AMBER, RED = "#f5f2ec", "#8a8597", "#ffb347", "#ff4d3d"
CYAN, VIOLET, PINK = "#38e8d8", "#8b5cff", "#ff5db1"
BG = "radial-gradient(130% 120% at 50% -10%, #181321 0%, #100d16 42%, #08070b 100%)"
GRAIN = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter "
         "id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3'/%3E%3C/filter%3E%3Crect "
         "width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")")
EXIT = 0.5


def _backdrop(P):
    blob = "position:absolute;border-radius:50%;filter:blur(70px);"
    return (f'<div id="{P}-ba" style="{blob}width:540px;height:540px;background:{VIOLET};opacity:.4;top:-12%;left:-8%"></div>'
            f'<div id="{P}-bb" style="{blob}width:475px;height:475px;background:{CYAN};opacity:.3;bottom:-14%;right:-10%"></div>'
            f'<div id="{P}-bc" style="{blob}width:367px;height:367px;background:{PINK};opacity:.26;top:55%;left:58%"></div>'
            f'<div style="position:absolute;inset:0;opacity:.07;mix-blend-mode:overlay;background-image:{GRAIN}"></div>')


def _drift(P, dur):
    return [f'tl.to("#{P}-ba", {{xPercent: 14, yPercent: 18, duration: {dur:.3f}, ease: "sine.inOut"}}, 0);',
            f'tl.to("#{P}-bb", {{xPercent: -18, yPercent: -12, duration: {dur:.3f}, ease: "sine.inOut"}}, 0);',
            f'tl.to("#{P}-bc", {{xPercent: -22, yPercent: 16, duration: {dur:.3f}, ease: "sine.inOut"}}, 0);']


def _chars(P, text, cls):
    """Letters as inline-block spans (class <P><cls>); spaces as fixed gaps."""
    return "".join(f'<span class="{P}{cls}" style="display:inline-block">{esc(c)}</span>' if c != " " else
                   '<span style="display:inline-block;width:.24em"></span>' for c in text)


def _size(text, cw, top, room=1640):
    """Font size so the line fits `room` px (cw = average glyph width in em)."""
    return int(min(top, room / max(1, len(text)) / cw))


def _line(inner, extra=""):
    return f'<div style="display:flex;justify-content:center;overflow:hidden;padding:.05em 0;{extra}">{inner}</div>'


def _kicker(P, text, kid="k", top=36):
    return (f'<div id="{P}-{kid}" style="font:900 {top}px Inter;letter-spacing:.45em;text-indent:.45em;'
            f'text-transform:uppercase;color:{MUTED};white-space:nowrap">{esc(text)}</div>') if text else ""


def _centre(P, inner):
    return (f'<div id="{P}-txt" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;text-align:center;perspective:1300px">{inner}</div>')


def _crops(P, fw=1020, fh=540, arm=70):
    """Four corner crop marks around a fw x fh box at the centre + the amber baseline rule."""
    css = f"position:absolute;width:{arm}px;height:{arm}px;"
    marks = []
    for cid, v, hz in (("tl", "top", "left"), ("tr", "top", "right"), ("bl", "bottom", "left"), ("br", "bottom", "right")):
        marks.append(f'<div id="{P}-c{cid}" style="{css}{v}:0;{hz}:0">'
                     f'<div style="position:absolute;{v}:0;{hz}:0;width:100%;height:3px;background:{INK}"></div>'
                     f'<div style="position:absolute;{v}:0;{hz}:0;width:3px;height:100%;background:{INK}"></div></div>')
    return (f'<div id="{P}-fr" style="position:absolute;left:{(W0 - fw) / 2}px;top:{(H0 - fh) / 2}px;width:{fw}px;'
            f'height:{fh}px">{"".join(marks)}</div>'
            f'<div id="{P}-rule" style="position:absolute;left:{(W0 - 760) / 2}px;top:{H0 / 2}px;width:760px;height:2px;'
            f'background:linear-gradient(90deg,transparent,{AMBER} 18%,{AMBER} 82%,transparent)"></div>')


def _crops_in(P, at):
    js = []
    for cid, x, y in (("tl", -34, -34), ("tr", 34, -34), ("bl", -34, 34), ("br", 34, 34)):
        js.append(f'tl.fromTo("#{P}-c{cid}", {{autoAlpha: 0, x: {x}, y: {y}, scale: 1.6}}, {{autoAlpha: 1, x: 0, y: 0, '
                  f'scale: 1, duration: 0.42, ease: "power4.out"}}, {at:.3f});')
    js.append(f'tl.fromTo("#{P}-rule", {{autoAlpha: 0, scaleX: 0}}, {{autoAlpha: 1, scaleX: 1, duration: 0.55, '
              f'ease: "power3.inOut"}}, {at + 0.13:.3f});')
    return js


def _finish(P, ctx, inner, js, cues, nat, exit_js):
    """Hold for the beat (slow push-in so the frame keeps moving), then the exit if there's room for it."""
    dur = max(nat, float(ctx.get("dur") or 0))
    hold = dur - nat
    js = _drift(P, dur) + js
    if hold > 0.05:
        js.append(f'tl.fromTo("#{P}-txt", {{scale: 1}}, {{scale: 1.035, duration: {dur - nat + 0.4:.3f}, ease: "sine.inOut"}}, '
                  f'{nat - 0.4:.3f});')
    if exit_js and dur >= nat + EXIT:
        js += exit_js(dur - EXIT)
        cues = cues + [(dur - EXIT, "whoosh")]
    return out(P, stage(P, ctx, W0, H0, BG, _backdrop(P) + inner), "", js, cues, dur, (W0, H0), 1)


# ------------------------------------------------------------------------------------------------ char_flip
def char_flip(P, ctx):
    """ctx: word, kicker, dur."""
    word = (ctx.get("word") or "MOTION").upper()[:12]
    size = _size(word, 0.8, 300)
    inner = _centre(P, _line(_kicker(P, ctx.get("kicker", ""))) +
                    _line(f'<div id="{P}-w" style="font:400 {size}px/0.8 \'Archivo Black\';letter-spacing:-.035em;'
                          f'color:{INK};white-space:nowrap">{_chars(P, word, "c")}</div>'))
    js = [f'tl.from("#{P}-k", {{yPercent: 100, opacity: 0, duration: 0.5, ease: "power4.out"}}, 0.05);' if ctx.get("kicker") else "",
          f'tl.from(".{P}c", {{yPercent: 120, rotationX: -90, opacity: 0, stagger: 0.05, duration: 0.7, ease: "spring.snappy"}}, 0.2);',
          f'tl.to("#{P}-w", {{letterSpacing: "0.02em", duration: 0.6, ease: "power4.out"}}, 0.9);']

    def ex(t):
        return [f'tl.to(gsap.utils.toArray(".{P}c, #{P}-k"), {{scale: 0, rotation: 160, opacity: 0, filter: "blur(6px)", '
                f'stagger: {{each: 0.025, from: "edges"}}, duration: 0.45, ease: "power3.in"}}, {t:.3f});']
    return _finish(P, ctx, inner, js, [(0.18, "whoosh"), (0.5, "pop")], 1.6, ex)


# ------------------------------------------------------------------------------------------------ serif_scatter
def serif_scatter(P, ctx):
    """ctx: text, color, dur."""
    text = (ctx.get("text") or "in every").strip()[:28]
    size = _size(text, 0.46, 210)
    n = len(text.replace(" ", ""))
    order = list(range(n))
    random.Random(text).shuffle(order)               # the reference's from:"random", fixed per line
    inner = _centre(P, _line(f'<div style="font:italic 500 {size}px/0.9 \'Fraunces Italic\';letter-spacing:-.03em;'
                             f'color:{ctx.get("color", AMBER)};white-space:nowrap">{_chars(P, text, "c")}</div>'))
    js = [f'tl.from(gsap.utils.toArray(".{P}c")[{j}], {{yPercent: 130, opacity: 0, skewY: 10, duration: 0.55, '
          f'ease: "power4.out"}}, {0.05 + 0.03 * k:.3f});' for j, k in enumerate(order)]

    def ex(t):
        return [f'tl.to(".{P}c", {{opacity: 0, yPercent: -70, scale: 0.6, stagger: {{each: 0.02, from: "edges"}}, '
                f'duration: 0.35, ease: "power3.in"}}, {t + 0.1:.3f});']
    return _finish(P, ctx, inner, js, [(0.05, "swipe")], 0.65 + 0.03 * n, ex)


# ------------------------------------------------------------------------------------------------ outline_slam
def outline_slam(P, ctx):
    """ctx: word, dur."""
    word = (ctx.get("word") or "FRAME").upper()[:12]
    size = _size(word, 0.5, 330)
    inner = _centre(P, _line(f'<div style="font:400 {size}px/0.84 Anton;letter-spacing:-.025em;color:transparent;'
                             f'-webkit-text-stroke:4px {INK};white-space:nowrap">{_chars(P, word, "c")}</div>'))
    js = [f'tl.from(".{P}c", {{scale: 5, opacity: 0, filter: "blur(20px)", stagger: {{each: 0.04, from: "center"}}, '
          f'duration: 0.5, ease: "power4.out"}}, 0.0);',
          f'tl.to("#{P}-st", {{x: 9, duration: 0.05, yoyo: true, repeat: 4, ease: "none"}}, 0.2);',
          f'tl.to("#{P}-st", {{x: 0, duration: 0.05, ease: "none"}}, 0.45);']

    def ex(t):
        return [f'tl.to(".{P}c", {{yPercent: 110, opacity: 0, rotationX: 90, stagger: {{each: 0.03, from: "end"}}, '
                f'duration: 0.4, ease: "power3.in"}}, {t:.3f});']
    return _finish(P, ctx, inner, js, [(0.18, "impact")], 0.5 + 0.04 * len(word), ex)


# ------------------------------------------------------------------------------------------------ three_beat
def three_beat(P, ctx):
    """ctx: words (3), dur."""
    words = [w.upper()[:12] for w in (ctx.get("words") or ["CREATE", "ANIMATE", "DELIVER"])][:3]
    size = min(_size(w, 0.5, 230) for w in words)
    cols = [CYAN, VIOLET, PINK]
    rows = "".join(_line(f'<div style="font:400 {size}px/0.84 Anton;letter-spacing:-.025em;color:{cols[i]};'
                         f'white-space:nowrap">{_chars(P, w, f"l{i}")}</div>') for i, w in enumerate(words))
    inner = _centre(P, rows)
    js = [f'tl.from(".{P}l0", {{yPercent: 120, opacity: 0, stagger: 0.04, duration: 0.45, ease: "power4.out"}}, 0.02);',
          f'tl.from(".{P}l1", {{xPercent: -120, opacity: 0, stagger: 0.04, duration: 0.45, ease: "power4.out"}}, 0.25);' if len(words) > 1 else "",
          f'tl.from(".{P}l2", {{scale: 2.2, opacity: 0, stagger: 0.03, duration: 0.5, ease: "spring.bouncy"}}, 0.5);' if len(words) > 2 else "",
          f'tl.to(".{P}l2", {{y: -7, duration: 0.08, yoyo: true, repeat: 3, stagger: 0.01, ease: "sine.inOut"}}, 0.95);' if len(words) > 2 else ""]

    def ex(t):
        return [f'tl.to(".{P}l0, .{P}l1, .{P}l2", {{opacity: 0, yPercent: 40, filter: "blur(8px)", stagger: 0.01, '
                f'duration: 0.3, ease: "power2.in"}}, {t + 0.1:.3f});']
    return _finish(P, ctx, inner, js, [(0.02, "pop"), (0.25, "pop"), (0.5, "pop")], 1.35, ex)


# ------------------------------------------------------------------------------------------------ crop_lockup
def crop_lockup(P, ctx):
    """ctx: lines (2), kicker, dur."""
    lines = [x.upper()[:24] for x in (ctx.get("lines") or ["MOTION", "SKILLS"]) if x][:2]
    size = min(_size(x, 0.8, 200, 1500) for x in lines)
    cols = [INK, AMBER]
    rows = "".join(_line(f'<div style="font:400 {size}px/0.82 \'Archivo Black\';letter-spacing:-.04em;color:{cols[i]};'
                         f'white-space:nowrap">{_chars(P, x, f"l{i}")}</div>') for i, x in enumerate(lines))
    inner = (_crops(P, 1020, max(540, int(size * 0.82 * len(lines) + 220))) +
             _centre(P, rows + _line(_kicker(P, ctx.get("kicker", "")), "margin-top:28px")) +
             f'<div id="{P}-fl" style="position:absolute;inset:0;background:{INK};opacity:0"></div>')
    js = _crops_in(P, 0.02) + [
        f'tl.from(".{P}l0", {{yPercent: 115, rotationX: -85, opacity: 0, stagger: 0.05, duration: 0.65, ease: "spring.snappy"}}, 0.0);',
        f'tl.from(".{P}l1", {{yPercent: 115, rotationX: -85, opacity: 0, stagger: 0.05, duration: 0.65, ease: "spring.snappy"}}, 0.2);',
        f'tl.from("#{P}-k", {{yPercent: 100, opacity: 0, duration: 0.5, ease: "power4.out"}}, 0.6);' if ctx.get("kicker") else "",
        f'tl.to("#{P}-fl", {{opacity: 0.3, duration: 0.06}}, 0.0);',
        f'tl.to("#{P}-fl", {{opacity: 0, duration: 0.3}}, 0.06);']

    def ex(t):
        return [f'tl.to(".{P}l0, .{P}l1", {{scale: 0, opacity: 0, filter: "blur(8px)", stagger: {{each: 0.02, from: "edges"}}, '
                f'duration: 0.4, ease: "power3.in"}}, {t:.3f});',
                f'tl.to("#{P}-fr, #{P}-rule, #{P}-k", {{autoAlpha: 0, duration: 0.4, ease: "power2.in"}}, {t:.3f});']
    return _finish(P, ctx, inner, js, [(0.0, "impact"), (0.2, "whoosh")], 1.4, ex)


# ------------------------------------------------------------------------------------------------ signature_dot
def signature_dot(P, ctx):
    """ctx: word, kicker, dur. The closing card: no exit."""
    word = (ctx.get("word") or "studio").lower()[:12]
    size = _size(word + ".", 0.62, 250, 1400)
    mark = (f'<div id="{P}-w" style="font:900 {size}px/0.82 Fraunces;letter-spacing:-.04em;color:{INK};white-space:nowrap">'
            f'{_chars(P, word, "c")}<span id="{P}-dot" style="display:inline-block;color:{AMBER}">.</span></div>')
    inner = (_crops(P, 1020, 540) +
             _centre(P, _line(mark) + _line(_kicker(P, ctx.get("kicker", "")), "margin-top:30px")))
    js = [f'tl.fromTo("#{P}-fr", {{autoAlpha: 0, scale: 1.18}}, {{autoAlpha: 1, scale: 1, duration: 0.7, ease: "power3.out"}}, 0.0);',
          f'tl.fromTo("#{P}-rule", {{autoAlpha: 0, scaleX: 0}}, {{autoAlpha: 1, scaleX: 1, duration: 0.6, ease: "power3.inOut"}}, 0.25);',
          f'tl.from(".{P}c", {{yPercent: 115, rotationX: -85, opacity: 0, stagger: 0.06, duration: 0.75, ease: "spring.snappy"}}, 0.0);',
          f'tl.from("#{P}-dot", {{scale: 0, duration: 0.5, ease: "spring.bouncy"}}, 0.5);',
          f'tl.to("#{P}-dot", {{scale: 1.3, duration: 0.45, yoyo: true, repeat: 1, ease: "sine.inOut"}}, 0.8);',
          f'tl.from("#{P}-k", {{yPercent: 100, opacity: 0, duration: 0.55, ease: "power4.out"}}, 0.6);' if ctx.get("kicker") else "",
          f'tl.to("#{P}-fr", {{scale: 1.015, duration: 1.5, ease: "sine.inOut"}}, 0.4);']
    for cid in ("tl", "tr", "bl", "br"):
        js.append(f'tl.set("#{P}-c{cid}", {{autoAlpha: 1}}, 0);')
    return _finish(P, ctx, inner, js, [(0.0, "whoosh"), (0.5, "pop"), (0.8, "ding")], 1.7, None)
