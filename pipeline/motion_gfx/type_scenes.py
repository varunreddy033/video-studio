"""Typographic scene types of the Type Studio format (show: type_studio): words are the picture.

  type_kicker    a small light kicker line over one big phrase (the reference's "We're / 10xvid")
  type_wheel     lead words + a slot-machine column of words that rolls and lands on the key word, neighbours faded
  type_swap      a fixed lead word, the next word swaps in on each spoken content word, the backdrop colour flips
  type_stack     the sentence stacked in short lines, light / heavy, each line rising out of a mask on its word
  type_sentence  the sentence typed word by word with a caret, key words turning heavy accent after they land

Each type has 2 arrangements (x the frames = 4 layouts) and is a format "host": only Type Studio uses them
(formats.ALL_HOSTS). Fonts, colours and effects come from the video's type style (typography.py).
"""

import re

from . import design as D
from . import extras as X
from . import templates as T
from . import typography as TY

OWN = 2


def _esc(s):
    return T.esc(s)


def _ws(beat):
    return T._words_rel(beat)


def _t(ws, k, lead=0.05):
    return max(0.0, ws[k][1] - lead) if ws else 0.0


def _content(words):
    return [k for k, w in enumerate(words)
            if len(re.sub(r"\W", "", w)) >= 3 and w.lower().strip(".,;:!?\"'") not in T.STOP | T.WEAK]


def _key(words):
    ks = T.key_words(words, 1)
    return ks[0] if ks else (_content(words) or [len(words) - 1])[-1]


def _cw():
    return T.CHAR_W * (0.86 if TY.STYLE["case"] == "as_is" else 1.0)


def _accent(pal):
    return TY._accent(pal)


# --------------------------------------------------------------------------------------------- type_kicker
def type_kicker(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = T._box(ctx)
    ws = _ws(beat)
    words = [TY.case(w[0]) for w in ws] or [TY.case(beat["text"])]
    phrase = T.key_phrase(" ".join(words), 3, upper=TY.STYLE["case"] == "upper").split() or words[-2:]
    low = [w.lower().strip(".,;:!?") for w in words]
    try:
        p0 = next(k for k in range(len(words)) if low[k:k + len(phrase)] == [p.lower().strip(".,;:!?") for p in phrase])
    except StopIteration:
        p0 = max(0, len(words) - len(phrase))
    kick = words[max(0, p0 - 4):p0]
    big = words[p0:p0 + len(phrase)] or words[-2:]
    size = T.fit(" ".join(big), (x1 - x0) * 0.92, int(H * 0.2), int(H * 0.07), _cw())
    ks = max(int(H * 0.03), int(size * 0.3))
    cy = (y0 + y1) // 2
    align = "center" if v == 0 else "left"
    left = x0 if v else x0
    tk = _t(ws, max(0, p0 - len(kick))) if kick else 0.05
    tb = max(tk + 0.35, _t(ws, p0)) if ws else 0.3
    spans = " ".join(f'<span id="{P}b{j}" class="tw {"ty-key" if j == len(big) - 1 and len(big) > 1 else ""}">'
                     f'{TY.word_html(w, "letters", _esc)}</span>' for j, w in enumerate(big))
    html = (f'<div id="{P}kk" class="ty-h" style="font-weight:340;position:absolute;left:{left}px;width:{x1 - x0}px;'
            f'top:{cy - int(size * 0.72) - ks}px;text-align:{align};font-family:\'{T.HEAD}\';font-size:{ks}px;'
            f'color:{pal["ink"]};line-height:1.1">{_esc(" ".join(kick))}</div>' if kick else "")
    if v == 1:
        html += (f'<div id="{P}rule" style="position:absolute;left:{x0}px;top:{cy - int(size * 0.62)}px;width:{int((x1 - x0) * 0.4)}px;'
                 f'height:{max(2, H // 400)}px;background:{_accent(pal)}"></div>')
    html += (f'<div id="{P}big" class="ty-h" style="position:absolute;left:{left}px;width:{x1 - x0}px;'
             f'top:{cy - int(size * 0.55)}px;text-align:{align};font-family:\'{T.HEAD}\';font-size:{size}px;'
             f'line-height:1.05;color:{pal["ink"]};white-space:nowrap">{spans}</div>')
    js = []
    if kick:
        js += TY.word_js("mask", f"#{P}kk", tk, ks)
    if v == 1:
        js.append(f'tl.fromTo("#{P}rule", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.5, '
                  f'ease: "power3.out"}}, {tk + 0.1:.2f});')
    for j in range(len(big)):
        tj = max(tb + j * 0.12, _t(ws, p0 + j)) if ws and p0 + j < len(ws) else tb + j * 0.12
        js += TY.word_js("letters", f"#{P}b{j}", tj, size)
        if j == len(big) - 1 and len(big) > 1:
            js += TY.emphasis_js(f"#{P}b{j}", tj)
    js.append(f'tl.fromTo("#{P}big", {{letterSpacing: "0.02em"}}, {{letterSpacing: "-0.03em", duration: {max(1.0, ctx["dur"]):.2f}, '
              f'ease: "none"}}, {tb:.2f});')
    return {"html": html, "css": ".tw { display:inline-block; margin:0 0.04em; }", "js": "\n".join(js),
            "cues": [(tb, "click")]}


# ---------------------------------------------------------------------------------------------- type_wheel
def type_wheel(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = T._box(ctx)
    ws = _ws(beat)
    words = [TY.case(w[0].strip(".,;:!?\"")) for w in ws] or [TY.case(beat["text"])]
    k = _key(words)
    lead = words[max(0, k - 3):k] or words[:1]
    key = words[k]
    alts = [TY.case(a) for a in ctx.get("ty_alts", []) if a.lower() != key.lower()]
    alts += [words[j] for j in _content(words) if j != k and words[j] not in alts]
    alts = alts[:5] or ["…"]
    rows = alts + [key]
    n = len(rows) - 1
    longest = max(len(" ".join(lead)) + max(len(r) for r in rows), 6)
    size = T.fit("x" * longest, (x1 - x0) * (0.9 if v == 0 else 0.7), int(H * 0.13), int(H * 0.05), _cw())
    rh = 1.18
    cy = (y0 + y1) // 2
    col = "".join(f'<div class="wr{" ty-key" if j == n else ""}" style="height:{rh}em">{_esc(r)}</div>' for j, r in enumerate(rows))
    win = (f'<div id="{P}win" style="position:relative;height:{3 * rh}em;overflow:hidden;'
           f'-webkit-mask-image:linear-gradient(transparent 0%, #000 38%, #000 62%, transparent 100%);'
           f'mask-image:linear-gradient(transparent 0%, #000 38%, #000 62%, transparent 100%)">'
           f'<div id="{P}col" style="position:absolute;left:0;right:0;top:{rh}em">{col}</div></div>')
    rpx = size * rh
    lead_html = f'<span id="{P}ld" class="ty-lt">{_esc(" ".join(lead))}</span>'
    if v == 0:
        html = (f'<div class="ty-h" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - int(size * rh * 1.5)}px;'
                f'display:flex;align-items:center;justify-content:center;gap:0.35em;font-family:\'{T.HEAD}\';'
                f'font-size:{size}px;line-height:{rh};color:{pal["ink"]}">'
                f'<div style="text-align:right">{lead_html}</div><div style="text-align:left;min-width:4em">{win}</div></div>')
    else:
        html = (f'<div class="ty-h" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - int(size * rh * 2)}px;'
                f'text-align:center;font-family:\'{T.HEAD}\';font-size:{size}px;line-height:{rh};color:{pal["ink"]}">'
                f'<div>{lead_html}</div><div style="display:flex;justify-content:center"><div style="min-width:5em">{win}</div></div></div>')
    css = (f"#{P}col .wr {{ opacity:0.32; font-weight:400; white-space:nowrap; }} "
           f"#{P}col .wr.ty-key {{ opacity:1; }}")
    tl0 = 0.05
    tland = max(tl0 + 0.25 + 0.13 * n, _t(ws, k, 0.08)) if ws else tl0 + 0.25 + 0.13 * n
    js = TY.word_js("mask", f"#{P}ld", tl0, size)
    step = (tland - tl0 - 0.2) / max(1, n)
    for j in range(1, n + 1):
        js.append(f'tl.to("#{P}col", {{y: {-j * rpx:.1f}, duration: {min(0.35, step * 0.9):.3f}, '
                  f'ease: "{"back.out(1.6)" if j == n else "power2.inOut"}"}}, {tl0 + 0.2 + (j - 1) * step:.3f});')
    js += TY.emphasis_js(f"#{P}col .ty-key", tland)
    return {"html": html, "css": css, "js": "\n".join(js), "cues": [(tl0 + 0.2, "tick"), (tland, "pop")]}


# ----------------------------------------------------------------------------------------------- type_swap
SWAP_BG = ["sw_blue", "sw_ink", "sw_cream", "sw_paper", "sw_sky"]


def type_swap(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = T._box(ctx)
    ws = _ws(beat)
    words = [TY.case(w[0].strip(".,;:!?\"")) for w in ws] or [TY.case(beat["text"])]
    cont = _content(words)
    if len(cont) < 2:
        cont = list(range(max(0, len(words) - 2), len(words)))
    lead = words[:cont[0]][-2:] or [words[cont[0]]]
    swaps = [k for k in cont if words[k] not in lead][:4] or cont[-1:]
    longest = max(len(words[k]) for k in swaps) + len(" ".join(lead)) + 1
    size = T.fit("x" * longest, (x1 - x0) * 0.9, int(H * 0.15), int(H * 0.05), _cw())
    cy = (y0 + y1) // 2
    pals = [p for name in SWAP_BG for p in D.PALETTES if p["name"] == name and p["bg"] != pal["bg"]]
    flashes = "".join(f'<div id="{P}bg{j}" data-layout-ignore style="position:absolute;left:-5%;top:-5%;width:110%;height:110%;'
                      f'background:{pals[j % len(pals)]["bg"]};opacity:0"></div>' for j in range(1, len(swaps))) if pals else ""
    slot = "".join(f'<span id="{P}s{j}" class="sw{" ty-key" if j == len(swaps) - 1 else ""}">{_esc(words[k])}</span>'
                   for j, k in enumerate(swaps))
    just = "center" if v == 0 else "flex-start"
    html = flashes + (
        f'<div id="{P}tx" class="ty-h" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - int(size * 0.6)}px;'
        f'display:flex;justify-content:{just};align-items:baseline;gap:0.3em;font-family:\'{T.HEAD}\';font-size:{size}px;'
        f'line-height:1.15;color:{pal["ink"]}"><span id="{P}ld" class="ty-lt">{_esc(" ".join(lead))}</span>'
        f'<span style="position:relative;display:inline-grid;overflow:hidden;padding:0 0.05em">{slot}</span></div>')
    css = f"#{P}tx .sw {{ grid-area:1/1; white-space:nowrap; font-weight:800; }}"
    js = TY.word_js("mask", f"#{P}ld", 0.05, size)
    cues = []
    for j, k in enumerate(swaps):
        t = max(0.25 + 0.4 * j, _t(ws, k, 0.06)) if ws else 0.25 + 0.4 * j
        js.append(f'tl.fromTo("#{P}s{j}", {{yPercent: 110, opacity: 0}}, {{yPercent: 0, opacity: 1, duration: 0.32, '
                  f'ease: "power4.out"}}, {t:.3f});')
        if j + 1 < len(swaps):
            t2 = max(0.25 + 0.4 * (j + 1), _t(ws, swaps[j + 1], 0.06)) if ws else 0.25 + 0.4 * (j + 1)
            js.append(f'tl.to("#{P}s{j}", {{yPercent: -110, opacity: 0, duration: 0.26, ease: "power3.in"}}, {t2 - 0.06:.3f});')
        if j >= 1 and pals:
            bg = pals[j % len(pals)]
            js.append(f'tl.set("#{P}bg{j}", {{opacity: 1}}, {t:.3f});')
            js.append(f'tl.set("#{P}tx", {{color: "{bg["ink"]}"}}, {t:.3f});')
            js.append(f'tl.set("#{P}s{j}", {{color: "{TY._accent(bg) if j == len(swaps) - 1 else bg["ink"]}"}}, {t:.3f});')
        cues.append((t, "click" if j else "swipe"))
    if len(swaps) == 1:
        js += TY.emphasis_js(f"#{P}s0", 0.3)
    return {"html": html, "css": css, "js": "\n".join(js), "cues": cues[:3]}


# ---------------------------------------------------------------------------------------------- type_stack
def type_stack(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = T._box(ctx)
    ws = _ws(beat)
    words = [TY.case(w[0]) for w in ws] or TY.case(beat["text"]).split()
    words = words[:14]
    lines = T.lines_of(words, 12)[:5]
    keys = set(T.key_words(words, 2))
    longest = max(sum(len(words[j]) + 1 for j in ln) for ln in lines)
    size = min(T.fit("x" * longest, (x1 - x0) * 0.8, int(H * 0.16), int(H * 0.05), _cw()),
               int((y1 - y0) / (len(lines) * 1.08)))
    align = "left" if v == 0 else "right"
    rows = []
    for li, ln in enumerate(lines):
        heavy = any(j in keys for j in ln)
        rows.append(f'<div id="{P}r{li}" class="{"ty-key" if heavy else "ty-lt"}" style="white-space:nowrap">'
                    + " ".join(_esc(words[j]) for j in ln) + "</div>")
    th = int(size * 1.06 * len(lines))
    top = (y0 + y1) // 2 - th // 2
    html = (f'<div id="{P}bar" style="position:absolute;{"left" if v == 0 else "right"}:{x0 - int(W * 0.02) if v == 0 else W - x1 - int(W * 0.02)}px;'
            f'top:{top}px;width:{max(3, W // 480)}px;height:{th}px;background:{_accent(pal)}"></div>'
            f'<div class="ty-h" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{top}px;text-align:{align};'
            f'font-family:\'{T.HEAD}\';font-size:{size}px;line-height:1.06;color:{pal["ink"]}">{"".join(rows)}</div>')
    js = [f'tl.fromTo("#{P}bar", {{scaleY: 0, transformOrigin: "50% 0%"}}, {{scaleY: 1, duration: 0.6, ease: "power3.out"}}, 0.02);']
    for li, ln in enumerate(lines):
        t = max(0.08 + 0.1 * li, _t(ws, ln[0], 0.06)) if ws else 0.08 + 0.18 * li
        js += TY.word_js("mask", f"#{P}r{li}", t, size)
    return {"html": html, "css": "", "js": "\n".join(js), "cues": [(0.05, "swipe")]}


# ------------------------------------------------------------------------------------------- type_sentence
def type_sentence(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0) % OWN
    x0, x1, y0, y1 = T._box(ctx)
    ws = _ws(beat)[:16]
    words = [TY.case(w[0]) for w in ws] or TY.case(beat["text"]).split()[:16]
    keys = set(T.key_words(words, 2))
    lines = T.lines_of(words, 22)
    longest = max(sum(len(words[j]) + 1 for j in ln) for ln in lines)
    size = min(T.fit("x" * longest, (x1 - x0) * 0.9, int(H * 0.1), int(H * 0.045), _cw()),
               int((y1 - y0) * 0.8 / (len(lines) * 1.15)))
    align = "center" if v == 0 else "left"
    html_lines = "".join("<div>" + " ".join(f'<span id="{P}w{j}" class="tw {"ty-lt" if j not in keys else ""}">'
                                            f'{TY.word_html(words[j], "type", _esc)}</span>' for j in ln) + "</div>"
                         for ln in lines)
    th = int(size * 1.15 * len(lines))
    top = (y0 + y1) // 2 - th // 2
    html = ""
    if v == 1:
        html += (f'<div id="{P}sq" style="position:absolute;left:{x0}px;top:{top - int(size * 0.9)}px;width:{int(size * 0.32)}px;'
                 f'height:{int(size * 0.32)}px;background:{_accent(pal)}"></div>')
    html += (f'<div class="ty-h" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{top}px;text-align:{align};'
             f'font-family:\'{T.HEAD}\';font-size:{size}px;line-height:1.15;color:{pal["ink"]}">{html_lines}</div>')
    js, starts = [], []
    for j in range(len(words)):
        t = max((starts[-1] + 0.05) if starts else 0.0, _t(ws, j, 0.03)) if ws else 0.1 + 0.18 * j
        starts.append(t)
        dur = (ws[j][2] - ws[j][1]) if ws else 0.18
        js += TY.word_js("type", f"#{P}w{j}", t, size, 0, max(0.12, dur))
        if j in keys:
            js.append(f'tl.to("#{P}w{j}", {{fontWeight: 800, color: "{_accent(pal)}", duration: 0.25, ease: "power2.out"}}, '
                      f'{t + max(0.15, dur):.3f});')
    for j in range(len(words) - 1):
        js.append(TY.caret_off_js(f"#{P}w{j}", starts[j + 1]))
    if words:
        js.append(TY.caret_blink_js(f"#{P}w{len(words) - 1}", starts[-1] + 0.3, max(starts[-1] + 0.8, ctx["dur"])))
    if v == 1:
        js.append(f'tl.fromTo("#{P}sq", {{scale: 0}}, {{scale: 1, duration: 0.3, ease: "back.out(2)"}}, 0.02);')
    return {"html": html, "css": ".tw { display:inline-block; margin:0 0.03em; }", "js": "\n".join(js),
            "cues": [(starts[0] if starts else 0, "typing")]}


# --------------------------------------------------------------------------------------------- registration
def _n_content(b):
    return len(_content(b["text"].split()))


SPECS = {
    "type_kicker": ({"transition": 1.0, "conclusion": 0.9, "question": 0.7, "definition": 0.6, "story": 0.4}, False,
                    lambda b, st: 0.7 if 2 <= len(b["text"].split()) <= 10 else (0.35 if _n_content(b) else 0.0)),
    "type_wheel": ({"list": 1.0, "comparison": 0.7, "story": 0.5, "statistic": 0.4}, False,
                   lambda b, st: 0.6 if _n_content(b) >= 2 else 0.0),
    "type_swap": ({"list": 0.9, "comparison": 0.8, "process": 0.6, "story": 0.4}, False,
                  lambda b, st: 0.65 if _n_content(b) >= 3 else 0.0),
    "type_stack": ({"story": 0.8, "cause": 0.7, "warning": 0.7, "conclusion": 0.5}, False,
                   lambda b, st: 0.6 if 4 <= len(b["text"].split()) <= 14 else 0.2),
    "type_sentence": ({"story": 0.9, "quote": 0.8, "definition": 0.7, "cause": 0.5}, False,
                      lambda b, st: 0.55 if len(b["text"].split()) >= 5 else 0.1),
}
HOSTS = set(SPECS)


def register():
    from . import planner as PL
    from . import scenes as S
    for name, (roles, data, fits) in SPECS.items():
        PL.register(name, {"roles": roles, "data": data, "fits": fits})
        PL.OWN_LAYOUTS[name] = OWN
        S.BUILDERS[name] = globals()[name]
        S.SPECS[name] = (roles, data, fits)
