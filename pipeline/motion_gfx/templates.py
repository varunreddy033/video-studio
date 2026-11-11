"""Scene templates of the motion renderer. Each build function returns
    {"html", "css", "js", "cues": [(t, kind), ...]}
for one beat: ids start with the scene prefix P, tweens go on `tl` at absolute times in the scene (0 = the beat's
first word), sound cues are times in the scene. Nothing is drawn under the caption chip (top-left) or outside
the action-safe box (design.SAFE).

  kinetic   the spoken words slam in one by one on their own timing, key words on a marker swipe
  figure    one or two stick figures acting out the beat, a prop popping in, a short headline
  number    a big number counting up with overshoot, a label pill, burst rays
  title     a card's words slamming in, a sub line on a pill (also chapter openers)
  quote     big quote marks, the quote's words revealed, the source on a pill
  chart     bars growing / a line drawing itself, values counting
  memo      a document sliding in, lines writing themselves, a stamp slamming down (REPORTED / DENIED ...)
"""

import html as _html
import random
import re

from . import design as D
from . import figures as F

STOP = set("a an the and or but of to in on at for with by from as is are was were be been it its this that these "
           "those he she they them his her their you your we our i me my so if then than not no do does did has have "
           "had will would can could should just also very about into over after before up down out who what when "
           "where why how which there here".split())

# narration words -> what a figure scene shows: (pose, outfit, props, two figures)
RULES = [
    (r"\b(spy|spies|spying|espionage|operative|agents?|intelligence|asset|covert)\b", ("sneak", "spy", ["eye"], False)),
    (r"\b(romanc\w*|romantic|relationship|love|dating|affair|close (ties|relationship)|honey ?trap)\b",
     ("talk", "plain", ["heart"], True)),
    (r"\b(chips?|gpus?|semiconductors?|processors?|ai hardware)\b", ("point", "tie", ["chip"], False)),
    (r"\b(china|chinese|beijing|singapore|export\w*|smuggl\w*|divert\w*|diversion|border|overseas)\b",
     ("point", "plain", ["globe", "ship"], False)),
    (r"\b(deni\w*|den(y|ies)|rejects?|dismiss\w*|groundless|debunk\w*|false)\b", ("shrug", "tie", ["exclaim"], False)),
    (r"\b(ceo|boss|chief|executives?|founder|billionaire)\b", ("talk", "tie", ["building"], False)),
    (r"\b(money|billions?|millions?|dollars?|profits?|revenue|cash|price)\b", ("cheer", "tie", ["money"], False)),
    (r"\b(warn\w*|risk\w*|danger\w*|alarm\w*|threat\w*)\b", ("worried", "plain", ["exclaim"], False)),
    (r"\b(shock\w*|surpris\w*|suddenly|bombshell|explosive)\b", ("shocked", "plain", ["exclaim"], False)),
    (r"\b(secret\w*|hidden|classified|locked|private)\b", ("sneak", "spy", ["lock"], False)),
    (r"\b(photos?|videos?|cameras?|pictures?|seen|footage|watch\w*)\b", ("point", "plain", ["camera"], False)),
    (r"\b(compan\w*|office|headquarters|firm|nvidia)\b", ("talk", "tie", ["building"], False)),
    (r"\b(ris\w*|surg\w*|soar\w*|grow\w*|record high)\b", ("cheer", "plain", ["chart_up"], False)),
    (r"\b(fall\w*|fell|drop\w*|crash\w*|plung\w*|los(e|s|ses|t))\b", ("worried", "plain", ["chart_down"], False)),
    (r"\b(why|how|what|who|question|wonder\w*|mystery)\b|\?", ("think", "plain", ["question"], False)),
    (r"\b(investigat\w*|probe|look(ed|ing)? into|evidence|search\w*)\b", ("think", "glasses", ["magnifier"], False)),
    (r"\b(talks?|talked|meet\w*|met|call\w*|messag\w*)\b", ("talk", "tie", ["phone"], True)),
]
RULES = [(re.compile(p, re.I), v) for p, v in RULES]
# the sound a prop makes when it pops in (spreads the library: every kind gets used)
PROP_SOUND = {"chip": "click", "heart": "ding", "money": "cash", "coin": "coin", "document": "paper", "magnifier": "swipe",
              "phone": "click", "question": "pop", "exclaim": "alert", "globe": "whoosh", "building": "impact",
              "lock": "click", "camera": "shutter", "chart_up": "riser", "chart_down": "error", "ship": "whoosh",
              "flag": "swipe", "eye": "glitch"}
MEMO_WORDS = re.compile(r"\b(report\w*|memo|documents?|files?|according|newspaper|times|journal|financial|"
                        r"cited|claims?|alleg\w*|says|said|told)\b", re.I)
DENY_WORDS = re.compile(r"\b(deni\w*|den(y|ies)|rejects?|dismiss\w*|groundless|debunk\w*)\b", re.I)


def esc(s):
    return _html.escape(str(s), quote=True)


def key_words(words, n=2):
    """The words worth a marker: numbers first, then names (capitalised, not first), then long content words."""
    clean = [(i, re.sub(r"[^\w$%.,'-]", "", w).strip(".,")) for i, w in enumerate(words)]
    clean = [(i, w) for i, w in clean if w]
    nums = [i for i, w in clean if re.search(r"\d", w)]
    names = [i for i, w in clean if i > 0 and w[:1].isupper() and w.lower() not in STOP]
    longs = sorted((i for i, w in clean if len(w) >= 6 and w.lower() not in STOP), key=lambda i: -len(clean[[c[0] for c in clean].index(i)][1]))
    out = []
    for i in nums + names + longs:
        if i not in out:
            out.append(i)
    return sorted(out[:n])


WEAK = set("said says say saying told tell called call claim claims claimed now then still even only really many much "
           "some any every all both each other another such same new way thing things lot get got make made used use "
           "going went come came take took like look looks want wants against while because although though named "
           "known reportedly allegedly".split())


def key_phrase(text, n=3):
    """A short headline from a beat's words: the best run of neighbouring important words (names count double),
    e.g. "a woman named Alice Huang" -> ALICE HUANG, "a romantic relationship" -> ROMANTIC RELATIONSHIP."""
    ws = [w.strip(".,;:!?\"'()") for w in text.split()]
    ws = [w for w in ws if w]

    def weight(k, w):
        lw = w.lower()
        if lw in STOP or lw in WEAK:
            return 0
        if re.search(r"\d", w):
            return 2
        if w[:1].isupper() and (k > 0 or w.isupper()):
            return 2
        return 1 if len(w) >= 3 else 0

    best, run = (0, 0, []), []
    for k, w in enumerate(ws + [""]):
        if w and weight(k, w):
            run.append((k, w))
            continue
        for a in range(len(run)):                      # every window of up to n words inside the run
            win = run[a:a + n]
            score = sum(weight(k2, w2) for k2, w2 in win)
            cand = (score, len(" ".join(x for _, x in win)), [x for _, x in win])
            if cand[:2] > best[:2]:
                best = cand
        run = []
    return " ".join(best[2]).upper()


# the video's font pairing (design.FONT_PAIRS), set once per render by set_look(); renders run one at a time
HEAD, BODY, CHAR_W = "Anton", "Poppins SemiBold", 0.5


def set_look(fonts: str) -> None:
    global HEAD, BODY, CHAR_W
    pair = D.FONT_PAIRS.get(fonts) or D.FONT_PAIRS["poster"]
    HEAD, BODY, CHAR_W = pair["head"], pair["body"], pair["char_w"]


def fit(text, max_w, max_size, min_size=40, char_w=None):
    """Font size (px) so the text fits max_w (the headline font's caps are ~CHAR_W em wide per character)."""
    char_w = char_w or CHAR_W
    n = max(1, len(text))
    return int(max(min_size, min(max_size, max_w / (n * char_w))))


def lines_of(words, max_chars):
    lines, cur = [], []
    for k, w in enumerate(words):
        if cur and sum(len(words[j]) + 1 for j in cur) + len(w) > max_chars:
            lines.append(cur)
            cur = []
        cur.append(k)
    return lines + ([cur] if cur else [])


def _box(ctx):
    W, H, S = ctx["W"], ctx["H"], D.SAFE[ctx["fmt"]]
    return int(W * S["x0"]), int(W * S["x1"]), int(H * S["y0"]), int(H * S["y1"])


def ambient(P, ctx, n=4):
    """Ambient layer: soft shapes drifting slowly (motion-design: background life, never competing)."""
    W, H, pal, rnd, dur = ctx["W"], ctx["H"], ctx["pal"], ctx["rnd"], ctx["dur"]
    html, js = [], []
    for k in range(n):
        r = int(min(W, H) * (0.08 + rnd.random() * 0.14))
        x, y = int(rnd.random() * W), int(rnd.random() * H)
        shape = rnd.choice(["circle", "ring", "plus"])
        if shape == "circle":
            el = f'<div id="{P}amb{k}" class="amb" style="left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{pal["soft"]}"></div>'
        elif shape == "ring":
            el = (f'<div id="{P}amb{k}" class="amb" style="left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;'
                  f'border-radius:50%;border:{max(8, r // 6)}px solid {pal["soft"]}"></div>')
        else:
            el = (f'<div id="{P}amb{k}" class="amb plus" style="left:{x - r // 2}px;top:{y - r // 2}px;width:{r}px;height:{r}px;'
                  f'color:{pal["soft"]};font-size:{r}px">+</div>')
        html.append(el)
        dx, dy, rot = rnd.randint(-60, 60), rnd.randint(-50, 50), rnd.randint(-40, 40)
        js.append(f'tl.fromTo("#{P}amb{k}", {{x: 0, y: 0, rotation: 0, opacity: 0}}, {{x: {dx}, y: {dy}, rotation: {rot}, '
                  f'opacity: 1, duration: {max(1.0, dur):.2f}, ease: "none"}}, 0);')
    css = (f".amb {{ position:absolute; }} .plus {{ font-family:'{HEAD}'; line-height:1; text-align:center; }}")
    html = [h.replace('class="amb', 'data-layout-ignore class="amb') for h in html]
    return "\n".join(html), css, "\n".join(js)


def _words_rel(beat):
    return [(w[0], w[1] - beat["start"], w[2] - beat["start"]) for w in beat["words"]]


# --------------------------------------------------------------------------------------------- kinetic words
def kinetic(P, beat, ctx):
    W, H, pal = ctx["W"], ctx["H"], ctx["pal"]
    x0, x1, y0, y1 = _box(ctx)
    ws = _words_rel(beat)
    if not ws:
        return title(P, beat, ctx, text=key_phrase(beat["text"]) or "…", sub="")
    words = [w[0].upper() for w in ws]
    max_chars = 13 if ctx["fmt"] == "landscape" else 9
    lines = lines_of(words, max_chars)
    longest = max(sum(len(words[j]) + 1 for j in ln) for ln in lines)
    size = fit("x" * longest, (x1 - x0) * 0.92, int(H * (0.2 if ctx["fmt"] == "landscape" else 0.1)), int(H * 0.05))
    size = min(size, int((y1 - y0) / (len(lines) * 1.08)))
    keys = set(key_words([w[0] for w in ws]))
    html_lines = []
    for ln in lines:
        spans = []
        for j in ln:
            cls = "kw key" if j in keys else "kw"
            spans.append(f'<span class="{cls}" id="{P}w{j}"><span class="mk" id="{P}m{j}"></span>'
                         f'<span class="tx">{esc(words[j])}</span></span>')
        html_lines.append(f'<div class="ln">{" ".join(spans)}</div>')
    rot = ctx["rnd"].choice([-3, -2, 2, 3])
    html = (f'<div id="{P}kin" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{y0}px;height:{y1 - y0}px;'
            f'display:flex;flex-direction:column;justify-content:center;align-items:center">{"".join(html_lines)}</div>')
    css = (f"#{P}kin .ln {{ font-family:'{HEAD}'; font-size:{size}px; line-height:1.04; color:{pal['ink']}; "
           f"text-align:center; letter-spacing:-0.01em; white-space:nowrap; }}"
           f"#{P}kin .kw {{ display:inline-block; position:relative; margin:0 0.06em; }}"
           f"#{P}kin .tx {{ position:relative; }}"
           f"#{P}kin .key .tx {{ color:{'#FFFFFF' if pal['hi'] == '#111111' else '#111111'}; }}"
           f"#{P}kin .mk {{ position:absolute; left:-0.08em; right:-0.08em; top:0.04em; bottom:-0.02em; "
           f"background:{pal['hi']}; border-radius:0.08em; }}"
           f"#{P}kin .kw:not(.key) .mk {{ display:none; }}")
    js, cues = [], []
    last = 0.0
    for j, (w, t0, t1) in enumerate(ws):
        t = max(last + D.STAGGER, t0 - 0.04) if j else max(0.0, t0 - 0.04)
        last = t
        js.append(f'tl.fromTo("#{P}w{j}", {{opacity: 0, y: {int(size * 0.35)}, scale: 0.55, rotation: {rot}}}, '
                  f'{{opacity: 1, y: 0, scale: 1, rotation: 0, duration: {D.WORD_IN}, ease: "{D.EASE_POP}"}}, {t:.3f});')
        if j in keys:
            js.append(f'tl.fromTo("#{P}m{j}", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.28, '
                      f'ease: "{D.EASE_IN}"}}, {t + 0.06:.3f});')
            js.append(f'tl.fromTo("#{P}w{j}", {{scale: 1}}, {{scale: 1.1, duration: 0.12, yoyo: true, repeat: 1, '
                      f'ease: "power2.out"}}, {t + 0.3:.3f});')
            if not cues:
                cues.append((t + 0.05, ctx["rnd"].choice(["pop", "click"])))
    js.append(f'tl.fromTo("#{P}kin", {{scale: 1}}, {{scale: 1.04, duration: {max(0.5, ctx["dur"]):.2f}, ease: "none"}}, 0);')
    a_html, a_css, a_js = ambient(P, ctx, 3)
    return {"html": a_html + html, "css": a_css + css, "js": a_js + "\n" + "\n".join(js), "cues": cues}


# -------------------------------------------------------------------------------------------------- figures
def icon_html(el_id, icon, x, y, size, ctx, cls="prop"):
    """One library icon as a positioned picture. icon = {"id", "uri", ...} from the renderer's icon plan.
    Sticker style (the default look): white rounded badge, dark outline, soft drop shadow, so every icon reads on
    every backdrop colour. Plain: the icon alone with a soft shadow."""
    if (ctx.get("look") or {}).get("icon_style", "sticker") == "sticker":
        b = max(4, int(size * 0.035))
        deco = (f"background:#FFFFFF;border:{b}px solid #111111;border-radius:{int(size * 0.26)}px;"
                f"padding:{int(size * 0.13)}px;box-sizing:border-box;box-shadow:0 {int(size * 0.06)}px 0 rgba(0,0,0,0.22);")
    else:
        deco = f"filter:drop-shadow(0 {int(size * 0.04)}px {int(size * 0.03)}px rgba(0,0,0,0.25));"
    return (f'<img id="{el_id}" class="{cls}" alt="" src="{icon["uri"]}" style="left:{x}px;top:{y}px;width:{size}px;'
            f'height:{size}px;{deco}">')


def choose_figure(text):
    for rx, v in RULES:
        if rx.search(text):
            return v
    return ("talk", "plain", [], False)          # no default prop: the icon picker decides (picker.py)


def figure(P, beat, ctx, extra=""):
    W, H, pal, rnd, dur = ctx["W"], ctx["H"], ctx["pal"], ctx["rnd"], ctx["dur"]
    x0, x1, y0, y1 = _box(ctx)
    text = (beat["text"] + " " + extra).strip()
    pose, outfit, props, two = choose_figure(text)
    body_cols = ["#FFFFFF", "#111111", "#FF3347", "#2F6BFF", "#FFD21F", "#1FC16B"]
    body_cols = [c for c in body_cols if c != pal["bg"]] or ["#FFFFFF"]
    land = ctx["fmt"] == "landscape"
    fh = int((y1 - y0) * (1.0 if land else 0.56))
    fw = int(fh * 300 / 520)
    ground = y1 - int(H * 0.01)
    word_times = [(w[1] - beat["start"], w[2] - beat["start"]) for w in beat["words"]]
    parts, js, cues = [], [], []
    ink = "#111111"
    if two:
        xs = [x0 + int((x1 - x0) * 0.18), x0 + int((x1 - x0) * 0.82) - fw] if land else [x0, x1 - fw]
        outfits = [outfit, "spy" if re.search(r"spy|spies|operative|intelligence", text, re.I) else "plain"]
        for n, (fx, oft) in enumerate(zip(xs, outfits)):
            parts.append(f'<svg id="{P}fig{n}" class="fig" viewBox="0 0 300 520" style="left:{fx}px;top:{ground - fh}px;'
                         f'width:{fw}px;height:{fh}px">{F.figure(P, n, ink, rnd.choice(body_cols), oft, flip=n == 1)}</svg>')
            pj, pc = F.pose_js(P, n, "talk" if pose not in ("sneak", "shrug") else pose, dur,
                               word_times if n == 0 else word_times[1::2], seed=rnd.random())
            js.append(pj)
            cues += pc
            js.append(f'tl.fromTo("#{P}fig{n}", {{x: {-int(W * 0.25) if n == 0 else int(W * 0.25)}, opacity: 0}}, '
                      f'{{x: 0, opacity: 1, duration: 0.45, ease: "{D.EASE_IN}"}}, {0.05 + 0.08 * n:.2f});')
        cx = (x0 + x1) // 2
    else:
        fx = x0 + int((x1 - x0) * (0.1 if land else 0.0))
        sr = int(fh * 0.62)                                  # spotlight disc behind the figure (depth, fills the frame)
        parts.append(f'<div id="{P}spot" data-layout-ignore style="position:absolute;left:{fx + fw // 2 - sr}px;'
                     f'top:{ground - int(fh * 0.55) - sr}px;width:{2 * sr}px;height:{2 * sr}px;border-radius:50%;'
                     f'background:{pal["soft"]}"></div>')
        js.append(f'tl.fromTo("#{P}spot", {{scale: 0, transformOrigin: "50% 50%"}}, {{scale: 1, duration: 0.5, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
        parts.append(f'<svg id="{P}fig0" class="fig" viewBox="0 0 300 520" style="left:{fx}px;top:{ground - fh}px;'
                     f'width:{fw}px;height:{fh}px">{F.figure(P, 0, ink, rnd.choice(body_cols), outfit)}</svg>')
        pj, pc = F.pose_js(P, 0, pose, dur, word_times, seed=rnd.random())
        js.append(pj)
        cues += pc
        if pose in ("walk", "sneak"):
            js.append(f'tl.fromTo("#{P}fig0", {{x: {-int(W * 0.12)}}}, {{x: {int(W * 0.06)}, duration: {max(0.8, dur):.2f}, '
                      f'ease: "none"}}, 0);')
        else:
            js.append(f'tl.fromTo("#{P}fig0", {{y: {int(H * 0.45)}}}, {{y: 0, duration: 0.5, ease: "{D.EASE_POP}"}}, 0.02);')
        cx = fx + fw + (x1 - fx - fw) // 2 if land else (x0 + x1) // 2
    ps = int(min(W, H) * (0.3 if land else 0.24))
    icon = (ctx.get("icons") or {}).get(0)                   # the scene's icon, chosen for the whole video by picker.py
    if icon:
        px = cx - ps // 2
        py = (y0 + int((y1 - y0) * 0.42)) if two else (y0 + int((y1 - y0) * 0.38))
        if not land:
            py = y0 + int((y1 - y0) * 0.05)
        parts.append(icon_html(f"{P}prop0", icon, px, py, ps, ctx))
        t = 0.32
        js.append(f'tl.fromTo("#{P}prop0", {{scale: 0, rotation: -25, transformOrigin: "50% 50%"}}, {{scale: 1, rotation: 0, '
                  f'duration: 0.42, ease: "{D.EASE_POP}"}}, {t:.2f});')
        js.append(f'tl.fromTo("#{P}prop0", {{y: 0}}, {{y: -12, duration: 0.8, ease: "sine.inOut", yoyo: true, '
                  f'repeat: {max(0, int(dur / 0.8) - 1)}}}, {t + 0.42:.2f});')
        cues.append((t + 0.02, icon.get("sound", "pop")))
    head = key_phrase(beat["text"], 3)
    if head:
        hs = fit(head, (x1 - x0) * (0.46 if land else 0.9), int(H * 0.11), int(H * 0.05))
        hx = (cx - int((x1 - x0) * 0.25)) if land and not two else x0
        hw = int((x1 - x0) * 0.5) if land and not two else (x1 - x0)
        hy = y0 - int(H * 0.02) if land else y1 - int(H * 0.02)
        hwords = head.split()
        spans = "".join(f'<span id="{P}h{j}" class="hw">{esc(w)}</span> ' for j, w in enumerate(hwords))
        parts.append(f'<div id="{P}head" style="position:absolute;left:{hx}px;width:{hw}px;top:{hy}px;text-align:center;'
                     f'font-family:\'{HEAD}\';font-size:{hs}px;line-height:1;color:{pal["ink"]}">{spans}</div>')
        for j in range(len(hwords)):
            js.append(f'tl.fromTo("#{P}h{j}", {{opacity: 0, y: {int(hs * 0.5)}}}, {{opacity: 1, y: 0, duration: 0.3, '
                      f'ease: "{D.EASE_IN}"}}, {0.12 + j * D.STAGGER:.3f});')
    css = f".fig, .prop {{ position:absolute; overflow:visible; }} .hw {{ display:inline-block; }}"
    a_html, a_css, a_js = ambient(P, ctx, 3)
    return {"html": a_html + "".join(parts), "css": a_css + css, "js": a_js + "\n" + "\n".join(js), "cues": cues}


# --------------------------------------------------------------------------------------------------- number
def number(P, beat, ctx):
    W, H, pal, sh, dur = ctx["W"], ctx["H"], ctx["pal"], ctx["shot"], ctx["dur"]
    x0, x1, y0, y1 = _box(ctx)
    val, dec = sh["value"], sh.get("decimals", 0)
    pre, suf = sh.get("prefix", ""), sh.get("suffix", "")
    final = f"{pre}{val:,.{dec}f}{suf}"
    size = fit(final, (x1 - x0) * 0.9, int(H * 0.36), int(H * 0.12), 0.55)
    label = (sh.get("label") or "").upper()
    cy = y0 + int((y1 - y0) * 0.42)
    rays = "".join(f'<div class="ray" style="transform:rotate({a}deg)"></div>' for a in range(0, 360, 30))
    html = (f'<div id="{P}rays" data-layout-ignore style="position:absolute;left:{W // 2}px;top:{cy}px;width:0;height:0">{rays}</div>'
            f'<div id="{P}num" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - int(size * 0.6)}px;'
            f'text-align:center;font-family:\'{HEAD}\';font-size:{size}px;line-height:1.1;color:{pal["ink"]};'
            f'text-shadow:0 {size // 28}px 0 rgba(0,0,0,0.18)"><span id="{P}numtx">{esc(pre)}0{esc(suf)}</span></div>')
    if label:
        ls = fit(label, (x1 - x0) * 0.7, int(H * 0.065), int(H * 0.035), 0.55)
        html += (f'<div style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy + int(size * 0.62)}px;'
                 f'text-align:center"><span id="{P}lab" style="display:inline-block;background:{pal["ink"]};color:{pal["bg"]};'
                 f'font-family:\'{BODY}\';font-size:{ls}px;padding:0.18em 0.7em;border-radius:999px">'
                 f'{esc(label)}</span></div>')
    css = (f"#{P}rays .ray {{ position:absolute; left:0; top:-10px; width:{int(max(W, H) * 0.7)}px; height:20px; "
           f"transform-origin:0 50%; background:linear-gradient(90deg, {pal['soft']}, rgba(255,255,255,0)); }}")
    count = 1.0
    js = [f'tl.fromTo("#{P}rays", {{rotation: 0, opacity: 0, scale: 0.6}}, {{rotation: 40, opacity: 1, scale: 1, '
          f'duration: {max(1, dur):.2f}, ease: "power1.out"}}, 0);',
          f'tl.fromTo("#{P}num", {{scale: 0.3, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.4, ease: "{D.EASE_POP}"}}, 0.05);',
          f'const cnt = {{v: 0}}; tl.to(cnt, {{v: {val}, duration: {count}, ease: "power2.out", onUpdate: () => {{ '
          f'document.querySelector("#{P}numtx").textContent = {pre!r} + cnt.v.toLocaleString("en-US", '
          f'{{minimumFractionDigits: {dec}, maximumFractionDigits: {dec}}}) + {suf!r}; }}}}, 0.1);',
          f'tl.fromTo("#{P}num", {{scale: 1}}, {{scale: 1.12, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out"}}, '
          f'{0.1 + count:.2f});']
    if label:
        js.append(f'tl.fromTo("#{P}lab", {{y: 60, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.35, ease: "{D.EASE_IN}"}}, 0.5);')
    money = bool(re.search(r"[$₹€£]", pre + suf))
    cues = [(0.1, "tick"), (0.1 + count, "cash" if money else "ding")]
    return {"html": html, "css": css, "js": "\n".join(js), "cues": cues}


# ---------------------------------------------------------------------------------------------------- title
def title(P, beat, ctx, text=None, sub=None, kicker=""):
    W, H, pal = ctx["W"], ctx["H"], ctx["pal"]
    x0, x1, y0, y1 = _box(ctx)
    sh = ctx["shot"]
    text = (text if text is not None else sh.get("text", "")).upper()
    sub = sub if sub is not None else sh.get("sub", "")
    words = text.split() or ["…"]
    lines = lines_of(words, 12 if ctx["fmt"] == "landscape" else 8)
    longest = max(sum(len(words[j]) + 1 for j in ln) for ln in lines)
    size = min(fit("x" * longest, (x1 - x0) * 0.92, int(H * 0.22), int(H * 0.06)), int((y1 - y0) * 0.62 / len(lines)))
    stripe_h = int(size * len(lines) * 1.15)
    cy = y0 + int((y1 - y0) * 0.45)
    lines_html = "".join("<div>" + " ".join(f'<span id="{P}t{j}" class="tw">{esc(words[j])}</span>' for j in ln)
                         + "</div>" for ln in lines)
    html = (f'<div id="{P}stripe" data-layout-allow-overflow style="position:absolute;left:-5%;width:110%;top:{cy - stripe_h // 2}px;height:{stripe_h}px;'
            f'background:{pal["soft"]}"></div>'
            + (f'<div id="{P}kick" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - stripe_h // 2 - int(H * 0.08)}px;'
               f'text-align:center;font-family:\'{BODY}\';font-size:{int(H * 0.035)}px;letter-spacing:0.3em;'
               f'color:{pal["ink"]}">{esc(kicker.upper())}</div>' if kicker else "")
            + f'<div id="{P}title" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy - stripe_h // 2 + int(size * 0.05)}px;'
              f'text-align:center;font-family:\'{HEAD}\';font-size:{size}px;line-height:1.08;color:{pal["ink"]}">{lines_html}</div>')
    if sub:
        ss = fit(sub, (x1 - x0) * 0.8, int(H * 0.06), int(H * 0.032), 0.52)
        html += (f'<div style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{cy + stripe_h // 2 + int(H * 0.03)}px;'
                 f'text-align:center"><span id="{P}sub" style="display:inline-block;background:{pal["ink"]};color:{pal["bg"]};'
                 f'font-family:\'{BODY}\';font-size:{ss}px;padding:0.2em 0.8em;border-radius:999px">{esc(sub)}</span></div>')
    css = f".tw {{ display:inline-block; margin:0 0.05em; }}"
    js = [f'tl.fromTo("#{P}stripe", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.35, ease: "{D.EASE_IN}"}}, 0);']
    if kicker:
        js.append(f'tl.fromTo("#{P}kick", {{opacity: 0, letterSpacing: "0.8em"}}, {{opacity: 1, letterSpacing: "0.3em", '
                  f'duration: 0.5, ease: "{D.EASE_IN}"}}, 0.05);')
    for j in range(len(words)):
        js.append(f'tl.fromTo("#{P}t{j}", {{opacity: 0, scale: 2.2, filter: "blur(10px)"}}, {{opacity: 1, scale: 1, '
                  f'filter: "blur(0px)", duration: 0.34, ease: "power4.out"}}, {0.12 + j * 0.07:.2f});')
    slam = 0.12 + (len(words) - 1) * 0.07 + 0.2
    js.append(f'tl.fromTo("#{P}title", {{y: 0}}, {{y: 10, duration: 0.06, yoyo: true, repeat: 3, ease: "none"}}, {slam:.2f});')
    if sub:
        js.append(f'tl.fromTo("#{P}sub", {{y: 50, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.35, ease: "{D.EASE_IN}"}}, '
                  f'{slam + 0.1:.2f});')
    return {"html": html, "css": css, "js": "\n".join(js), "cues": [(slam - 0.05, "impact")]}


# ---------------------------------------------------------------------------------------------------- quote
def quote(P, beat, ctx):
    W, H, pal, sh = ctx["W"], ctx["H"], ctx["pal"], ctx["shot"]
    x0, x1, y0, y1 = _box(ctx)
    words = sh["text"].split()
    size = fit(" " * 22, (x1 - x0) * 0.86, int(H * 0.085), int(H * 0.04), 0.48)
    spans = " ".join(f'<span id="{P}q{j}" class="qw">{esc(w)}</span>' for j, w in enumerate(words))
    html = (f'<div id="{P}card" style="position:absolute;box-sizing:border-box;left:{x0 + int((x1 - x0) * 0.04)}px;width:{int((x1 - x0) * 0.92)}px;'
            f'top:{y0 + int((y1 - y0) * 0.08)}px;padding:{int(size * 0.8)}px {int(size)}px;background:#FFFFFF;border:8px solid #111111;'
            f'border-radius:28px;box-shadow:14px 14px 0 #111111">'
            f'<div id="{P}qm" style="position:absolute;left:{int(size * 0.3)}px;top:{-int(size * 1.4)}px;font-family:\'{HEAD}\';'
            f'font-size:{int(size * 3)}px;color:{pal["pop"]};line-height:1">“</div>'
            f'<div style="font-family:\'{BODY}\';font-size:{size}px;line-height:1.25;color:#111111">{spans}</div>'
            + (f'<div style="margin-top:{int(size * 0.5)}px"><span id="{P}by" style="display:inline-block;background:#111111;'
               f'color:#FFFFFF;font-family:\'{BODY}\';font-size:{int(size * 0.6)}px;padding:0.2em 0.8em;'
               f'border-radius:999px">{esc(sh.get("by", ""))}</span></div>' if sh.get("by") else "")
            + "</div>")
    css = f".qw {{ display:inline-block; }}"
    js = [f'tl.fromTo("#{P}card", {{y: {int(H * 0.5)}, rotation: 4}}, {{y: 0, rotation: -1, duration: 0.5, ease: "{D.EASE_IN}"}}, 0);',
          f'tl.fromTo("#{P}qm", {{scale: 0, transformOrigin: "50% 80%"}}, {{scale: 1, duration: 0.4, ease: "{D.EASE_POP}"}}, 0.3);']
    for j in range(len(words)):
        js.append(f'tl.fromTo("#{P}q{j}", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: 0.2, ease: "power2.out"}}, '
                  f'{0.4 + j * 0.06:.2f});')
    if sh.get("by"):
        js.append(f'tl.fromTo("#{P}by", {{scale: 0}}, {{scale: 1, duration: 0.3, ease: "{D.EASE_POP}"}}, '
                  f'{0.5 + len(words) * 0.06:.2f});')
    return {"html": html, "css": css, "js": "\n".join(js), "cues": [(0.05, "paper"), (0.4, "typing")]}


# ---------------------------------------------------------------------------------------------------- chart
def chart(P, beat, ctx):
    W, H, pal, sh = ctx["W"], ctx["H"], ctx["pal"], ctx["shot"]
    x0, x1, y0, y1 = _box(ctx)
    data = sh["data"][:8]
    top = max(v for _, v in data) or 1
    ts = fit(sh["title"].upper(), (x1 - x0) * 0.8, int(H * 0.075), int(H * 0.04))
    area_top, area_bot = y0 + int(ts * 1.5), y1 - int(H * 0.08)
    n = len(data)
    slot = (x1 - x0) / n
    bw = int(slot * 0.62)
    cols = ["#111111", "#FFFFFF", pal["pop"], "#2F6BFF", "#1FC16B"]
    cols = [c for c in cols if c.upper() != pal["bg"].upper()]
    html = [f'<div id="{P}ct" style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{y0}px;text-align:center;'
            f'font-family:\'{HEAD}\';font-size:{ts}px;color:{pal["ink"]}">{esc(sh["title"].upper())}</div>',
            f'<div style="position:absolute;left:{x0}px;width:{x1 - x0}px;top:{area_bot}px;height:8px;background:{pal["ink"]}"></div>']
    js = [f'tl.fromTo("#{P}ct", {{opacity: 0, y: -30}}, {{opacity: 1, y: 0, duration: 0.35, ease: "{D.EASE_IN}"}}, 0);']
    unit = sh.get("unit", "")
    for k, (lab, v) in enumerate(data):
        h = int((area_bot - area_top - ts) * v / top)
        bx = int(x0 + slot * k + (slot - bw) / 2)
        c = cols[k % len(cols)]
        vs = int(min(bw * 0.45, H * 0.05))
        html.append(f'<div id="{P}b{k}" style="position:absolute;left:{bx}px;width:{bw}px;top:{area_bot - h}px;height:{h}px;'
                    f'background:{c};border:6px solid #111111;border-bottom:0;border-radius:14px 14px 0 0"></div>')
        html.append(f'<div id="{P}v{k}" style="position:absolute;left:{bx - 40}px;width:{bw + 80}px;top:{area_bot - h - vs * 1.4}px;'
                    f'text-align:center;font-family:\'{HEAD}\';font-size:{vs}px;color:{pal["ink"]}">{v:g}{esc(unit)}</div>')
        html.append(f'<div style="position:absolute;left:{bx - 40}px;width:{bw + 80}px;top:{area_bot + 14}px;text-align:center;'
                    f'font-family:\'{BODY}\';font-size:{int(vs * 0.7)}px;color:{pal["ink"]}">{esc(lab)}</div>')
        t = 0.3 + k * 0.12
        js.append(f'tl.fromTo("#{P}b{k}", {{scaleY: 0, transformOrigin: "50% 100%"}}, {{scaleY: 1, duration: 0.55, '
                  f'ease: "{D.EASE_POP}"}}, {t:.2f});')
        js.append(f'tl.fromTo("#{P}v{k}", {{opacity: 0, y: 20}}, {{opacity: 1, y: 0, duration: 0.25, ease: "power2.out"}}, '
                  f'{t + 0.4:.2f});')
    return {"html": "".join(html), "css": "", "js": "\n".join(js), "cues": [(0.25, "riser")]}


# ----------------------------------------------------------------------------------------------------- memo
def memo(P, beat, ctx):
    W, H, pal, rnd = ctx["W"], ctx["H"], ctx["pal"], ctx["rnd"]
    x0, x1, y0, y1 = _box(ctx)
    land = ctx["fmt"] == "landscape"
    dw = int((x1 - x0) * (0.36 if land else 0.8))
    dh = int((y1 - y0) * (0.9 if land else 0.56))
    dx = x0 + int((x1 - x0) * (0.04 if land else 0.1))
    stamp = "DENIED" if DENY_WORDS.search(beat["text"]) else rnd.choice(["REPORTED", "ALLEGED"])
    outlet = re.search(r"\b(New York Times|Financial Times|Wall Street Journal|Reuters|Bloomberg|BBC)\b", beat["text"])
    head = outlet.group(1).upper() if outlet else (key_phrase(beat["text"], 3) or "REPORT")
    hw = (x1 - x0) - dw - int(W * 0.06) if land else (x1 - x0)
    hs = fit(max(head.split(), key=len), hw * 0.95, int(H * 0.12), int(H * 0.05))
    kind_word = "REPORT" if re.search(r"report|times|journal|newspaper", beat["text"], re.I) else "MEMO"
    lines = "".join(f'<div id="{P}l{k}" class="ml" style="width:{rnd.randint(55, 95)}%"></div>' for k in range(7))
    html = (f'<div id="{P}doc" style="position:absolute;box-sizing:border-box;left:{dx}px;top:{y0}px;width:{dw}px;height:{dh}px;'
            f'background:#FFFFFF;border:8px solid #111111;border-radius:18px;box-shadow:16px 16px 0 #111111;'
            f'padding:{int(dh * 0.08)}px {int(dw * 0.1)}px">'
            f'<div style="font-family:\'{HEAD}\';font-size:{int(dh * 0.09)}px;color:#111111;letter-spacing:0.08em">{kind_word}</div>'
            f'<div style="height:6px;background:#111111;margin:{int(dh * 0.02)}px 0 {int(dh * 0.05)}px"></div>{lines}'
            f'<div id="{P}stamp" style="position:absolute;right:{int(dw * 0.08)}px;bottom:{int(dh * 0.12)}px;'
            f'font-family:\'{HEAD}\';font-size:{int(dh * 0.13)}px;color:#E0222F;border:8px solid #E0222F;border-radius:12px;'
            f'padding:0.02em 0.25em;letter-spacing:0.06em">{stamp}</div></div>'
            f'<div id="{P}mh" style="position:absolute;left:{dx + dw + int(W * 0.05) if land else x0}px;'
            f'width:{hw}px;top:{y0 + int(dh * 0.22) if land else y0 + dh + int(H * 0.03)}px;'
            f'font-family:\'{HEAD}\';font-size:{hs}px;line-height:1.02;color:{pal["ink"]}">'
            + "".join(f'<span id="{P}mw{j}" class="mw">{esc(w)}</span> ' for j, w in enumerate(head.split())) + "</div>")
    css = (f"#{P}doc .ml {{ height:{max(10, int(dh * 0.035))}px; background:#D6D6D0; border-radius:8px; "
           f"margin:{int(dh * 0.035)}px 0; }} .mw {{ display:inline-block; }}")
    js = [f'tl.fromTo("#{P}doc", {{x: {-int(W * 0.5)}, rotation: -14}}, {{x: 0, rotation: -3, duration: 0.5, '
          f'ease: "{D.EASE_IN}"}}, 0);']
    for k in range(7):
        js.append(f'tl.fromTo("#{P}l{k}", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.18, '
                  f'ease: "power2.out"}}, {0.35 + k * 0.07:.2f});')
    st = min(1.05, max(0.75, ctx["dur"] * 0.45))
    js.append(f'tl.fromTo("#{P}stamp", {{scale: 2.6, rotation: -24, opacity: 0}}, {{scale: 1, rotation: -12, opacity: 1, '
              f'duration: 0.22, ease: "power4.in"}}, {st:.2f});')
    js.append(f'tl.fromTo("#{P}doc", {{y: 0}}, {{y: 8, duration: 0.05, yoyo: true, repeat: 3, ease: "none"}}, {st + 0.22:.2f});')
    for j in range(len(head.split())):
        js.append(f'tl.fromTo("#{P}mw{j}", {{opacity: 0, x: 40}}, {{opacity: 1, x: 0, duration: 0.3, ease: "{D.EASE_IN}"}}, '
                  f'{0.2 + j * D.STAGGER:.3f});')
    return {"html": html, "css": css, "js": "\n".join(js), "cues": [(0.05, "paper"), (st + 0.18, "impact")]}


# --------------------------------------------------------------------------------------------- choice per beat
def pick(beat, k_in_shot):
    """Which template a beat gets: the shot's own kind on its first beat, then a rhythm that alternates picture
    types (figure, words, figure, memo when the words are about a report) so no two neighbours look alike."""
    kind, i = beat["kind"], beat["index"]
    if beat.get("chapter_card"):
        return "chapter"
    if i == 0 and kind in ("number", "quote", "chart", "card"):
        return {"number": "number", "quote": "quote", "chart": "chart", "card": "title"}[kind]
    if MEMO_WORDS.search(beat["text"]) and k_in_shot % 2 == 0:
        return "memo"
    return "figure" if (i + k_in_shot) % 2 == 0 else "kinetic"


def scene_names(beats):
    """The template of every beat of a video (pick + never the same picture type twice in a row)."""
    names, k_in_shot, last_shot = [], 0, -1
    for b in beats:
        k_in_shot = 0 if b["shot"] != last_shot else k_in_shot + 1
        last_shot = b["shot"]
        name = pick(b, k_in_shot)
        if names and name == names[-1] and name in ("figure", "kinetic", "memo"):
            name = "kinetic" if name != "kinetic" else "figure"
        names.append(name)
    return names


def build(name, P, beat, ctx):
    if name == "chapter":
        return title(P, beat, ctx, text=beat["chapter"], sub="", kicker="Chapter")
    if beat.get("chapter_card"):
        return title(P, beat, ctx, text=beat["chapter"], sub="", kicker="Chapter")
    return {"kinetic": kinetic, "figure": figure, "number": number, "title": title, "quote": quote, "chart": chart,
            "memo": memo}[name](P, beat, ctx)
