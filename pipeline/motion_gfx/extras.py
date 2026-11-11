"""Six more scene templates for motion graphics (docs/ASSET_PACKS_PLAN.md section 5), each with 3 layout variants.

  icon_list  "earbuds, cases and chargers"        3-4 icons with labels (row / checklist / tiles)
  versus     "wired or wireless", "X instead of Y" two icons face off (split screen / VS badge / stacked OR)
  pile       "thousands of", "thirteen pairs of"  one icon raining into a pile / filling a grid / bursting out
  timeline   a year ("twenty twenty-one", 2016)   the video's years on a line, this one lit (line / column / calendar)
  meter      "twenty percent", "seven out of ten", battery   a bar / a battery / a gauge filling to the value
  map_flag   a country ("Singapore", "Chinese")   world map with the country lit / zoomed in / big flag + inset map

trigger(beat, state) says which of them a narration beat asks for (the renderer's scene chooser calls it);
needs(i, beat, name) = the icons the scene wants from the picker (picker.py); build(name, P, beat, ctx) draws it.
Everything is deterministic: words -> trigger, the video's seed -> variant.
"""

import re
from functools import lru_cache

from .. import icon_library as L
from . import design as D
from . import templates as T

NEW = ("icon_list", "versus", "pile", "timeline", "meter", "map_flag")

# ------------------------------------------------------------------------------------------- spoken numbers
UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                       "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
SCALES = {"hundred": 100, "thousand": 1000, "million": 10 ** 6, "billion": 10 ** 9}


def _tokens(text):
    return [t for t in re.findall(r"[A-Za-z]+|\d[\d,.]*%?|%", text.replace("-", " "))]


def numbers(text):
    """[(value, first token, last token)] for spoken or written numbers: "two hundred and fifty" -> 250."""
    toks = [t.lower() for t in _tokens(text)]
    out, k = [], 0
    while k < len(toks):
        t = toks[k]
        if re.fullmatch(r"\d[\d,]*(\.\d+)?%?", t):
            try:
                out.append((float(t.rstrip("%").replace(",", "")), k, k))
            except ValueError:
                pass
            k += 1
            continue
        if t in UNITS or t in TENS:
            total, cur, j = 0, 0, k
            while j < len(toks) and (toks[j] in UNITS or toks[j] in TENS or toks[j] in SCALES or
                                     (toks[j] == "and" and j + 1 < len(toks) and (toks[j + 1] in UNITS or toks[j + 1] in TENS))):
                w = toks[j]
                if w in UNITS:
                    if cur % 10 or (0 < cur < 20 and cur % 10 == 0 and w != "zero" and cur >= 10 and cur not in TENS.values()):
                        break
                    cur += UNITS[w]
                elif w in TENS:
                    if cur % 100:
                        break
                    cur += TENS[w]
                elif w in SCALES:
                    cur = max(cur, 1) * SCALES[w]
                    if SCALES[w] >= 1000:
                        total, cur = total + cur, 0
                j += 1
            out.append((float(total + cur), k, j - 1))
            k = max(j, k + 1)
            continue
        k += 1
    return out


def years(text):
    """Years said in a clause: 2016, "twenty sixteen", "twenty twenty-one", "nineteen ninety-nine", "two thousand eight"."""
    toks = [t.lower() for t in _tokens(text)]
    out = []
    for t in toks:
        if re.fullmatch(r"(19|20)\d\d", t):
            out.append(int(t))
    k = 0
    while k < len(toks) - 1:
        a, b = toks[k], toks[k + 1]
        if a in ("twenty", "nineteen") and (b in UNITS and UNITS[b] >= 10 or b in TENS):
            n = UNITS.get(b) or TENS.get(b)
            step = 2
            if b in TENS and k + 2 < len(toks) and toks[k + 2] in UNITS and 0 < UNITS[toks[k + 2]] < 10:
                n += UNITS[toks[k + 2]]
                step = 3
            out.append((2000 if a == "twenty" else 1900) + n)
            k += step
            continue
        if a == "two" and b == "thousand":
            n, j = 0, k + 2
            if j < len(toks) and toks[j] == "and":
                j += 1
            if j < len(toks) and toks[j] in UNITS:
                n = UNITS[toks[j]]
            out.append(2000 + n)
            k = j + 1
            continue
        k += 1
    return [y for y in out if 1900 <= y <= 2099]


def percent(text):
    """The percentage a clause says ("twenty percent", "20%", "seven out of ten" -> 70), or None."""
    toks = [t.lower() for t in _tokens(text)]
    for val, a, b in numbers(text):
        if b + 1 < len(toks) and toks[b + 1] in ("percent", "per", "%") or toks[b].endswith("%"):
            return max(0.0, min(100.0, val))
        if b + 3 < len(toks) and toks[b + 1] == "out" and toks[b + 2] == "of":
            rest = [v for v, a2, _ in numbers(text) if a2 == b + 3]
            if rest and rest[0]:
                return max(0.0, min(100.0, 100 * val / rest[0]))
    return None


# ------------------------------------------------------------------------------------------------ countries
ALIASES = {"america": "us", "american": "us", "americans": "us", "u.s.": "us", "us": "us", "usa": "us",
           "chinese": "cn", "japanese": "jp", "indian": "in", "indians": "in", "british": "gb", "britain": "gb",
           "uk": "gb", "u.k.": "gb", "england": "gb", "korean": "kr", "korea": "kr", "russian": "ru", "german": "de",
           "french": "fr", "taiwanese": "tw", "canadian": "ca", "mexican": "mx", "brazilian": "br",
           "australian": "au", "italian": "it", "spanish": "es", "israeli": "il", "iranian": "ir",
           "ukrainian": "ua", "saudi": "sa", "singaporean": "sg", "vietnamese": "vn", "dutch": "nl", "swiss": "ch",
           "swedish": "se", "irish": "ie", "emirati": "ae", "dubai": "ae", "pakistani": "pk", "egyptian": "eg",
           "nigerian": "ng", "kenyan": "ke", "argentine": "ar", "polish": "pl", "norwegian": "no", "danish": "dk",
           "finnish": "fi", "thai": "th", "indonesian": "id", "malaysian": "my", "filipino": "ph"}
# country names that are usually something else in a sentence
SKIP = {"chad", "jersey", "guinea", "turkey", "georgia", "jordan", "niger", "china town", "panama", "cuba",
        "monaco", "malta", "iceland", "greenland", "guernsey", "dominica", "mali", "oman", "peru", "togo"}


@lru_cache(maxsize=1)
def country_table():
    """{lower-case name: (code, flag id, map slug or None, display name)} from the flag pack + Natural Earth."""
    from .. import icon_index as IX
    rows, _, _ = IX.load()
    ne = L.load("natural_earth")["icons"] if "natural_earth" in L.installed() else {}
    ne_by_name = {v["name"].lower(): k for k, v in ne.items()}
    out = {}
    for r in rows:
        if r["set"] != "flags" or len(r["words"]) < 3:
            continue
        code = r["name"][:-4]
        if "-" in code:
            continue
        name = " ".join(r["words"][:-2])
        slug = ne_by_name.get(name) or next((s for n, s in ne_by_name.items() if n.startswith(name + " ")), None)
        if code == "us":
            slug = "united-states-of-america"
        disp = ne[slug]["name"] if slug else name.title()
        if disp == "United States of America":
            disp = "United States"
        if name not in SKIP:
            out[name] = (code, r["id"], slug, disp)
    by_code = {v[0]: v for v in out.values()}
    for a, code in ALIASES.items():
        if code in by_code:
            out[a] = by_code[code]
    return out


def countries(text):
    """Countries named in a clause, in order (capitalised words only: "Turkey" the country, never "turkey")."""
    tab = country_table()
    found, seen = [], set()
    for m in re.finditer(r"\b(?:[A-Z][a-zA-Z.]*)(?:\s+(?:of\s+)?[A-Z][a-zA-Z.]*){0,3}", text):
        words = m.group(0).split()
        for n in range(len(words), 0, -1):                     # longest name inside the capitalised run first
            for a in range(0, len(words) - n + 1):
                key = " ".join(words[a:a + n]).lower().rstrip(".")
                key = {"us": "us"}.get(key, key)
                if key in tab and (key != "us" or words[a] in ("US", "U.S.", "U.S")) and tab[key][0] not in seen:
                    found.append(tab[key])
                    seen.add(tab[key][0])
    return found


# ------------------------------------------------------------------------------------------------ triggers
LIST_SPLIT = re.compile(r",\s*(?:and\s+|or\s+)?|\s+and\s+|\s+or\s+")
VERSUS = re.compile(r"\b(versus|vs\.?|instead of|compared (?:to|with)|rather than|or)\b", re.I)
PILE = re.compile(r"\b(thousands|millions|billions|hundreds|dozens|piles? of|stacks? of|tons of|lots of|so many|"
                  r"countless|all those)\b", re.I)
TIME_UNITS = set("year years month months week weeks day days hour hours minute minutes second seconds time times "
                 "percent decade decades".split())
COOLDOWN = 25.0          # seconds between two scenes of the same newer template (countries excepted)


def list_items(text):
    """3-4 short items of a spoken list ("earbuds, cases and chargers") or []."""
    body = re.sub(r"^\s*(?:and|or|but|so)\s+", "", text.strip().rstrip(".!?:;"), flags=re.I)
    if body.count(",") < 1:
        return []
    parts = [p.strip(" .") for p in LIST_SPLIT.split(body) if p and p.strip(" .")]
    parts = [p for p in parts if 1 <= len(p.split()) <= 4]
    items = [p for p in parts if picker_words(p)]
    return items[:4] if len(items) >= 3 and len(items) == len(parts) else []


def versus_sides(text):
    m = VERSUS.search(text)
    if not m:
        return None
    left, right = text[:m.start()].strip(" ,.?"), text[m.end():].strip(" ,.?")
    lw, rw = picker_words(left), picker_words(right)
    if not lw or not rw or len(left.split()) > 6 or len(right.split()) > 6:
        return None
    return left, right, m.group(1)


def pile_noun(text):
    m = PILE.search(text)
    if m:
        rest = picker_words(text[m.end():]) or picker_words(m.group(0))
        return rest[0] if rest else None
    for val, a, b in numbers(text):
        if 5 <= val <= 10 ** 9 and not years(text):
            after = " ".join(_tokens(text)[b + 1:])
            if (after.split() or [""])[0].lower() in TIME_UNITS:
                continue
            ws = picker_words(after)
            if ws and re.match(r"\w+s\b", after.lower()):
                return ws[-1] if ws[0] in ("pairs", "pair", "sets", "boxes") and len(ws) > 1 else ws[0]
    return None


def picker_words(text):
    from . import picker
    return picker.content_words(text)


def trigger(beat, state):
    """The new template a narration beat asks for, or None. state = what the video showed so far (countries)."""
    text = beat["text"]
    cs = [c for c in countries(text) if c[0] not in state.setdefault("countries", set())]
    if cs:
        return "map_flag"
    last = state.setdefault("last", {})
    ok = lambda n: beat["start"] - last.get(n, -1e9) >= COOLDOWN         # noqa: E731
    for name, test in (("timeline", lambda: years(text)),
                       ("meter", lambda: percent(text) is not None or re.search(r"\bbatter(y|ies)\b", text, re.I)),
                       ("versus", lambda: versus_sides(text)), ("icon_list", lambda: list_items(text)),
                       ("pile", lambda: pile_noun(text))):
        if ok(name) and test():
            return name
    return None


def remember(name, beat, state):
    state.setdefault("last", {})[name] = beat["start"]
    if name == "map_flag":
        for c in countries(beat["text"]):
            if c[0] not in state.setdefault("countries", set()):
                state["countries"].add(c[0])
                break


# ---------------------------------------------------------------------------------------------- icon needs
def _need(i, slot, beat, text, required, weight=1.0):
    from . import picker
    ws = picker.content_words(text)
    qs = [(text.lower(), weight)] + [(w, 0.94 * weight) for w in ws if picker.stem(w) not in picker.AMBIGUOUS]
    return {"beat": i, "slot": slot, "t": beat["start"], "queries": qs, "words": {picker.stem(w) for w in ws},
            "required": required, "text": text}


def needs(i, beat, name):
    text = beat["text"]
    if name == "icon_list":
        return [_need(i, k, beat, item, True) for k, item in enumerate(list_items(text))]
    if name == "versus":
        left, right, _ = versus_sides(text)
        return [_need(i, 0, beat, left, True), _need(i, 1, beat, right, True)]
    if name == "pile":
        return [_need(i, 0, beat, pile_noun(text) or text, True)]
    if name == "timeline":
        ws = picker_words(re.sub(r"\b(twenty|nineteen|thousand|year|years|back|since|until|in)\b", " ", text, flags=re.I))
        return [dict(_need(i, 0, beat, " ".join(ws[:3]), False), optional=True)] if ws else []
    return []


# ----------------------------------------------------------------------------------------------- drawing
def _head(P, text, ctx, top, size=None, align="center", left=None, width=None):
    """A headline in the video's headline font, words rising in one by one."""
    W, H, pal = ctx["W"], ctx["H"], ctx["pal"]
    x0, x1, _, _ = T._box(ctx)
    left = x0 if left is None else left
    width = (x1 - x0) if width is None else width
    words = (text or "").upper().split()
    if not words:
        return "", []
    size = size or T.fit(" ".join(words), width * 0.95, int(H * 0.085), int(H * 0.045))
    spans = "".join(f'<span id="{P}hd{j}" class="hw">{T.esc(w)}</span> ' for j, w in enumerate(words))
    html = (f'<div id="{P}hd" style="position:absolute;left:{left}px;width:{width}px;top:{top}px;text-align:{align};'
            f'font-family:\'{T.HEAD}\';font-size:{size}px;line-height:1.02;color:{pal["ink"]}">{spans}</div>')
    js = [f'tl.fromTo("#{P}hd{j}", {{opacity: 0, y: {int(size * 0.5)}}}, {{opacity: 1, y: 0, duration: 0.3, '
          f'ease: "{D.EASE_IN}"}}, {0.08 + j * D.STAGGER:.3f});' for j in range(len(words))]
    return html, js


def _label(el_id, text, x, y, w, size, ctx, pill=True):
    pal = ctx["pal"]
    style = (f"display:inline-block;background:{pal['ink']};color:{pal['bg']};padding:0.15em 0.6em;border-radius:999px;"
             if pill else f"color:{pal['ink']};")
    return (f'<div style="position:absolute;left:{x}px;width:{w}px;top:{y}px;text-align:center">'
            f'<span id="{el_id}" style="{style}font-family:\'{T.BODY}\';font-size:{size}px;white-space:nowrap">'
            f'{T.esc(text)}</span></div>')


def _pop(sel, t, dur=0.42):
    return (f'tl.fromTo("{sel}", {{scale: 0, rotation: -18, transformOrigin: "50% 50%"}}, {{scale: 1, rotation: 0, '
            f'duration: {dur}, ease: "{D.EASE_POP}"}}, {t:.2f});')


def _word_time(beat, text, default):
    """When the first word of `text` is spoken in the beat (seconds from the beat's start)."""
    first = re.sub(r"\W", "", (text.split() or [""])[0].lower())
    for w in beat["words"]:
        if re.sub(r"\W", "", w[0].lower()) == first:
            return max(0.05, w[1] - beat["start"] - 0.05)
    return default


def _short(text, n=3):
    ws = picker_words(text)
    return " ".join(ws[-n:]) if ws else text


def icon_list(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0)
    x0, x1, y0, y1 = T._box(ctx)
    items = list_items(beat["text"])
    icons = ctx.get("icons") or {}
    n = len(items)
    parts, js, cues = [], [], []
    ls = int(H * 0.04)
    for k, item in enumerate(items):
        t = min(_word_time(beat, item, 0.25 + 0.3 * k), max(0.3, ctx["dur"] - 0.6))
        if v == 0:                                            # a row of stickers, labels under them
            s = int(min((x1 - x0) / (n * 1.35), (y1 - y0) * 0.5))
            gap = ((x1 - x0) - n * s) / (n + 1)
            ix, iy = int(x0 + gap + k * (s + gap)), y0 + int((y1 - y0) * 0.18)
            lx, ly, lw = ix - int(gap * 0.4), iy + s + int(H * 0.03), s + int(gap * 0.8)
        elif v == 1:                                          # checklist: icon left, label right, one row each
            s = int(min((y1 - y0) / (n * 1.25), H * 0.17))
            ix, iy = x0 + int((x1 - x0) * 0.2), y0 + int(k * s * 1.25)
            lx, ly, lw = ix + s + int(W * 0.03), iy + int(s * 0.3), int((x1 - x0) * 0.5)
        else:                                                 # tiles: 2 x 2 (or a staircase of 3)
            s = int(min((x1 - x0) * 0.2, (y1 - y0) * 0.34))
            col, row = (k % 2, k // 2) if n == 4 else (k, k)
            cols = 2 if n == 4 else 3
            cw = (x1 - x0) / cols
            ix = int(x0 + cw * col + (cw - s) / 2)
            iy = int(y0 + row * ((y1 - y0) / (2 if n == 4 else 3.4)))
            lx, ly, lw = int(x0 + cw * col), iy + s + int(H * 0.015), int(cw)
        ic = icons.get(k)
        if ic:
            parts.append(T.icon_html(f"{P}i{k}", ic, ix, iy, s, ctx))
        if v == 1:
            parts.append(f'<div id="{P}lb{k}" style="position:absolute;left:{lx}px;top:{ly}px;width:{lw}px;'
                         f'font-family:\'{T.HEAD}\';font-size:{int(s * 0.36)}px;color:{pal["ink"]};white-space:nowrap">'
                         f'{T.esc(_short(item).upper())}</div>')
            js.append(f'tl.fromTo("#{P}lb{k}", {{opacity: 0, x: 60}}, {{opacity: 1, x: 0, duration: 0.3, '
                      f'ease: "{D.EASE_IN}"}}, {t + 0.12:.2f});')
        else:
            parts.append(_label(f"{P}lb{k}", _short(item).upper(), lx, ly, lw, ls, ctx))
            js.append(f'tl.fromTo("#{P}lb{k}", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.28, '
                      f'ease: "{D.EASE_IN}"}}, {t + 0.12:.2f});')
        js.append(_pop(f"#{P}i{k}", t))
        cues.append((t + 0.02, (ic or {}).get("sound", "pop") if k == 0 else "pop"))
    css = ".prop { position:absolute; } .hw { display:inline-block; }"
    a_html, a_css, a_js = T.ambient(P, ctx, 2)
    return {"html": a_html + "".join(parts), "css": a_css + css, "js": a_js + "\n" + "\n".join(js), "cues": cues}


def versus(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0)
    x0, x1, y0, y1 = T._box(ctx)
    left, right, word = versus_sides(beat["text"])
    icons = ctx.get("icons") or {}
    badge = "VS" if word.lower() in ("versus", "vs", "vs.", "compared to", "compared with") else "OR"
    parts, js = [], []
    t_r = min(_word_time(beat, right, 0.6), max(0.5, ctx["dur"] - 0.6))
    ls = int(H * 0.042)
    if v == 2:                                                # stacked: one above the other, OR pill between
        s = int((y1 - y0) * 0.3)
        cx = (x0 + x1) // 2
        pos = [(cx - s // 2, y0), (cx - s // 2, y1 - s)]
        labs = [(cx + s // 2 + int(W * 0.03), y0 + int(s * 0.35)), (cx + s // 2 + int(W * 0.03), y1 - s + int(s * 0.35))]
        bx, by, bs = cx - int(H * 0.06), (y0 + y1) // 2 - int(H * 0.06), int(H * 0.12)
    else:
        s = int(min((x1 - x0) * 0.24, (y1 - y0) * 0.5))
        qx = [x0 + int((x1 - x0) * 0.25) - s // 2, x0 + int((x1 - x0) * 0.75) - s // 2]
        top = y0 + int((y1 - y0) * (0.12 if v == 0 else 0.2))
        pos = [(qx[0], top), (qx[1], top)]
        labs = [(qx[0] - s // 2, top + s + int(H * 0.03)), (qx[1] - s // 2, top + s + int(H * 0.03))]
        bs = int(H * (0.16 if v == 1 else 0.12))
        bx, by = (x0 + x1) // 2 - bs // 2, top + s // 2 - bs // 2
    if v == 0:                                                # split screen: the right half in the soft colour
        parts.append(f'<div id="{P}half" data-layout-ignore style="position:absolute;left:{W // 2}px;top:0;width:{W // 2}px;'
                     f'height:{H}px;background:{pal["soft"]}"></div>')
        js.append(f'tl.fromTo("#{P}half", {{scaleX: 0, transformOrigin: "100% 50%"}}, {{scaleX: 1, duration: 0.4, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
    for k, (side, (ix, iy), (lx, ly)) in enumerate(zip((left, right), pos, labs)):
        ic = icons.get(k)
        if ic:
            parts.append(T.icon_html(f"{P}i{k}", ic, ix, iy, s, ctx))
        t = 0.15 if k == 0 else t_r
        if v == 2:
            parts.append(f'<div id="{P}lb{k}" style="position:absolute;left:{lx}px;top:{ly}px;font-family:\'{T.HEAD}\';'
                         f'font-size:{int(s * 0.28)}px;color:{pal["ink"]};white-space:nowrap">{T.esc(_short(side).upper())}</div>')
        else:
            parts.append(_label(f"{P}lb{k}", _short(side).upper(), lx, ly, 2 * s, ls, ctx))
        js.append(f'tl.fromTo("#{P}i{k}", {{x: {-int(W * 0.3) if k == 0 else int(W * 0.3)}, opacity: 0}}, {{x: 0, '
                  f'opacity: 1, duration: 0.45, ease: "{D.EASE_POP}"}}, {t:.2f});')
        js.append(f'tl.fromTo("#{P}lb{k}", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.28, ease: "{D.EASE_IN}"}}, '
                  f'{t + 0.15:.2f});')
    parts.append(f'<div id="{P}vs" style="position:absolute;left:{bx}px;top:{by}px;width:{bs}px;height:{bs}px;'
                 f'border-radius:50%;background:{pal["pop"]};border:{max(4, bs // 18)}px solid #111111;display:flex;'
                 f'align-items:center;justify-content:center;font-family:\'{T.HEAD}\';font-size:{int(bs * 0.42)}px;'
                 f'color:#111111">{badge}</div>')
    js.append(f'tl.fromTo("#{P}vs", {{scale: 0, rotation: 200}}, {{scale: 1, rotation: {-8 if v == 1 else 0}, duration: 0.4, '
              f'ease: "{D.EASE_POP}"}}, {max(0.3, t_r - 0.2):.2f});')
    if v == 1:                                                # the two icons nudge each other
        js.append(f'tl.fromTo("#{P}i0", {{x: 0}}, {{x: 18, duration: 0.12, yoyo: true, repeat: 3, ease: "power1.inOut"}}, '
                  f'{t_r + 0.5:.2f});')
    cues = [(0.15, (icons.get(0) or {}).get("sound", "swipe")), (max(0.3, t_r - 0.18), "impact"),
            (t_r, (icons.get(1) or {}).get("sound", "pop"))]
    return {"html": "".join(parts), "css": ".prop { position:absolute; }", "js": "\n".join(js), "cues": cues}


def pile(P, beat, ctx):
    W, H, pal, v, rnd = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0), ctx["rnd"]
    x0, x1, y0, y1 = T._box(ctx)
    ic = (ctx.get("icons") or {}).get(0)
    head = T.key_phrase(beat["text"], 3)
    h_html, h_js = _head(P, head, ctx, y0 - int(H * 0.02))
    parts, js = [h_html], list(h_js)
    top = y0 + int(H * 0.1)
    if v == 1:                                                # a grid filling up fast
        cols, rows = (8, 3) if ctx["fmt"] == "landscape" else (4, 5)
        s = int(min((x1 - x0) / (cols * 1.2), (y1 - top) / (rows * 1.2)))
        gx = x0 + ((x1 - x0) - cols * s * 1.2) / 2
        k = 0
        for r in range(rows):
            for c in range(cols):
                x, y = int(gx + c * s * 1.2), int(top + r * s * 1.2)
                parts.append(T.icon_html(f"{P}p{k}", ic, x, y, s, dict(ctx, look={"icon_style": "plain"})))
                js.append(_pop(f"#{P}p{k}", 0.25 + k * min(0.05, 1.2 / (cols * rows)), 0.3))
                k += 1
    else:
        n = 14
        s = int(min(W, H) * 0.16)
        for k in range(n):
            if v == 0:                                        # rain into a pile at the bottom
                x = int(x0 + rnd.random() * (x1 - x0 - s))
                y = int(y1 - s - (k // 5) * s * 0.55 - rnd.random() * s * 0.2)
                rot = rnd.randint(-35, 35)
                parts.append(T.icon_html(f"{P}p{k}", ic, x, y, s, dict(ctx, look={"icon_style": "plain"})))
                js.append(f'tl.fromTo("#{P}p{k}", {{y: {-int(H * 1.1)}, rotation: {rot * 3}}}, {{y: 0, rotation: {rot}, '
                          f'duration: 0.55, ease: "bounce.out"}}, {0.15 + k * 0.07:.2f});')
            else:                                             # burst out from the middle
                cx, cy = (x0 + x1) // 2 - s // 2, (top + y1) // 2 - s // 2
                ang = k / n * 6.283 + rnd.random() * 0.3
                import math
                r = (0.28 + rnd.random() * 0.17) * min(x1 - x0, (y1 - top) * 1.6)
                dx, dy = int(math.cos(ang) * r), int(math.sin(ang) * r * 0.55)
                parts.append(T.icon_html(f"{P}p{k}", ic, cx, cy, s, dict(ctx, look={"icon_style": "plain"})))
                js.append(f'tl.fromTo("#{P}p{k}", {{x: 0, y: 0, scale: 0.2, rotation: 0}}, {{x: {dx}, y: {dy}, scale: 1, '
                          f'rotation: {rnd.randint(-30, 30)}, duration: 0.6, ease: "{D.EASE_IN}"}}, {0.2 + k * 0.03:.2f});')
    cues = [(0.2, (ic or {}).get("sound", "pop")), (0.6, "pop" if v else "impact")]
    css = ".prop { position:absolute; } .hw { display:inline-block; }"
    return {"html": "".join(parts), "css": css, "js": "\n".join(js), "cues": cues}


def timeline(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0)
    x0, x1, y0, y1 = T._box(ctx)
    this = years(beat["text"])[0]
    all_years = sorted(set(ctx.get("years") or []) | {this})
    k_this = all_years.index(this)
    shown = all_years[max(0, k_this - 2):k_this + 3]
    ic = (ctx.get("icons") or {}).get(0)
    parts, js = [], []
    ys = int(H * 0.05)
    if v == 2:                                                # calendar page with the year
        cw, ch = int((x1 - x0) * 0.34), int((y1 - y0) * 0.78)
        cx, cy = (x0 + x1) // 2 - cw // 2, y0 + int((y1 - y0) * 0.08)
        prev = shown[shown.index(this) - 1] if shown.index(this) > 0 else this - 1
        parts.append(f'<div id="{P}cal" style="position:absolute;left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px;'
                     f'background:#FFFFFF;border:8px solid #111111;border-radius:22px;box-shadow:14px 14px 0 #111111;'
                     f'overflow:hidden"><div style="height:{int(ch * 0.22)}px;background:{pal["pop"]};border-bottom:8px solid #111111">'
                     f'</div><div id="{P}yr" style="position:absolute;left:0;right:0;top:{int(ch * 0.3)}px;text-align:center;'
                     f'font-family:\'{T.HEAD}\';font-size:{int(ch * 0.36)}px;color:#111111">{prev}</div></div>')
        js.append(f'tl.fromTo("#{P}cal", {{y: {int(H * 0.6)}, rotation: 6}}, {{y: 0, rotation: -2, duration: 0.5, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
        js.append(f'tl.fromTo("#{P}yr", {{rotationX: 0}}, {{rotationX: 90, duration: 0.15, ease: "power2.in", '
                  f'onComplete: () => {{ document.querySelector("#{P}yr").textContent = "{this}"; }}}}, 0.55);')
        js.append(f'tl.to("#{P}yr", {{rotationX: 0, duration: 0.2, ease: "{D.EASE_POP}"}}, 0.7);')
        js.append(f'tl.call(() => {{ document.querySelector("#{P}yr").textContent = "{this}"; }}, null, 0.71);')
        if ic:
            s = int(ch * 0.4)
            parts.append(T.icon_html(f"{P}ic", ic, cx + cw + int(W * 0.04), cy + int(ch * 0.3), s, ctx))
            js.append(_pop(f"#{P}ic", 0.85))
        return {"html": "".join(parts), "css": ".prop { position:absolute; }", "js": "\n".join(js),
                "cues": [(0.05, "swipe"), (0.55, "paper"), (0.85, "pop")]}
    vertical = v == 1
    n = len(shown)
    if vertical:
        lx = x0 + int((x1 - x0) * 0.32)
        parts.append(f'<div id="{P}ln" style="position:absolute;left:{lx - 5}px;top:{y0}px;width:10px;height:{y1 - y0}px;'
                     f'background:{pal["ink"]};border-radius:5px"></div>')
        js.append(f'tl.fromTo("#{P}ln", {{scaleY: 0, transformOrigin: "50% 0%"}}, {{scaleY: 1, duration: 0.5, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
    else:
        ly = y0 + int((y1 - y0) * 0.62)
        parts.append(f'<div id="{P}ln" style="position:absolute;left:{x0}px;top:{ly - 5}px;width:{x1 - x0}px;height:10px;'
                     f'background:{pal["ink"]};border-radius:5px"></div>')
        js.append(f'tl.fromTo("#{P}ln", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: 1, duration: 0.5, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
    for k, y in enumerate(shown):
        on = y == this
        d = int(H * (0.07 if on else 0.035))
        if vertical:
            px, py = lx - d // 2, y0 + int((y1 - y0) * (k + 0.5) / n) - d // 2
            tx, ty, tw, al = lx + int(W * 0.04), py + d // 2 - int(ys * (1.3 if on else 0.65)), int((x1 - x0) * 0.5), "left"
        else:
            px, py = x0 + int((x1 - x0) * (k + 0.5) / n) - d // 2, ly - d // 2
            tx, ty, tw, al = px + d // 2 - int((x1 - x0) / n / 2), ly + int(H * 0.06), int((x1 - x0) / n), "center"
        parts.append(f'<div id="{P}d{k}" style="position:absolute;left:{px}px;top:{py}px;width:{d}px;height:{d}px;'
                     f'border-radius:50%;background:{pal["pop"] if on else pal["bg"]};border:6px solid {pal["ink"]};'
                     f'box-sizing:border-box"></div>')
        parts.append(f'<div id="{P}y{k}" style="position:absolute;left:{tx}px;top:{ty}px;width:{tw}px;text-align:{al};'
                     f'font-family:\'{T.HEAD}\';font-size:{int(ys * (2.4 if on else 1.2))}px;line-height:1;'
                     f'color:{pal["ink"]};opacity:{1 if on else 0.6}">{y}</div>')
        t = 0.3 + k * 0.12
        js.append(_pop(f"#{P}d{k}", t, 0.3))
        js.append(f'tl.fromTo("#{P}y{k}", {{opacity: 0}}, {{opacity: {1 if on else 0.6}, duration: 0.3}}, {t + 0.08:.2f});')
        if on:
            js.append(f'tl.fromTo("#{P}d{k}", {{scale: 1}}, {{scale: 1.35, duration: 0.15, yoyo: true, repeat: 1}}, {t + 0.45:.2f});')
            if ic:
                s = int(H * 0.2)
                ix = (px + d // 2 - s // 2) if not vertical else x0 + int((x1 - x0) * 0.72)
                iy = (ly - s - int(H * 0.08)) if not vertical else py - s // 2
                parts.append(T.icon_html(f"{P}ic", ic, ix, iy, s, ctx))
                js.append(_pop(f"#{P}ic", t + 0.3))
    return {"html": "".join(parts), "css": ".prop { position:absolute; }", "js": "\n".join(js),
            "cues": [(0.05, "swipe"), (0.3 + shown.index(this) * 0.12, "ding")]}


def meter(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0)
    x0, x1, y0, y1 = T._box(ctx)
    val = percent(beat["text"])
    battery = bool(re.search(r"\bbatter(y|ies)\b", beat["text"], re.I))
    if val is None:
        val = 0.0 if re.search(r"\b(no|dead|empty|dies|died|flat)\b", beat["text"], re.I) else 12.0
    if battery:
        v = 1
    head = T.key_phrase(re.sub(r"\b\d+%?|\bpercent\b", " ", beat["text"], flags=re.I), 3)
    h_html, h_js = _head(P, head, ctx, y0)
    parts, js = [h_html], list(h_js)
    fill_col = "#E0222F" if val < 20 else ("#FFB800" if val < 50 else "#1FC16B")
    vs = int(H * 0.12)
    if v == 1:                                                # battery
        bw, bh = int((x1 - x0) * 0.46), int((y1 - y0) * 0.42)
        bx, by = (x0 + x1) // 2 - bw // 2, y0 + int((y1 - y0) * 0.3)
        parts.append(f'<div id="{P}bat" style="position:absolute;left:{bx}px;top:{by}px;width:{bw}px;height:{bh}px;'
                     f'border:12px solid #111111;border-radius:26px;background:#FFFFFF;box-sizing:border-box;padding:12px">'
                     f'<div id="{P}fill" style="width:100%;height:100%;border-radius:12px;background:{fill_col}"></div>'
                     f'<div style="position:absolute;right:-44px;top:30%;width:32px;height:40%;background:#111111;'
                     f'border-radius:0 10px 10px 0"></div></div>')
        js.append(f'tl.fromTo("#{P}bat", {{scale: 0.4, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.4, ease: "{D.EASE_POP}"}}, 0.05);')
        js.append(f'tl.fromTo("#{P}fill", {{scaleX: 1, transformOrigin: "0% 50%"}}, {{scaleX: {max(0.02, val / 100):.3f}, '
                  f'duration: 0.9, ease: "power2.inOut"}}, 0.4);')
        nx, ny, nw = bx, by + bh + int(H * 0.02), bw
    elif v == 2:                                              # half-circle gauge with a needle
        r = int(min((x1 - x0) * 0.28, (y1 - y0) * 0.5))
        cx, cy = (x0 + x1) // 2, y0 + int((y1 - y0) * 0.2) + r
        parts.append(f'<div style="position:absolute;left:{cx - r}px;top:{cy - r}px;width:{2 * r}px;height:{r}px;overflow:hidden">'
                     f'<div style="width:{2 * r}px;height:{2 * r}px;border-radius:50%;box-sizing:border-box;'
                     f'border:{int(r * 0.2)}px solid {pal["soft"]};border-top-color:{fill_col};border-left-color:{fill_col}"></div></div>')
        parts.append(f'<div id="{P}ndl" style="position:absolute;left:{cx - int(r * 0.9)}px;top:{cy - 7}px;width:{int(r * 0.9)}px;'
                     f'height:14px;background:#111111;border-radius:7px;transform-origin:100% 50%"></div>'
                     f'<div style="position:absolute;left:{cx - 22}px;top:{cy - 22}px;width:44px;height:44px;border-radius:50%;'
                     f'background:#111111"></div>')
        js.append(f'tl.fromTo("#{P}ndl", {{rotation: 0}}, {{rotation: {val * 1.8:.1f}, duration: 1.0, ease: "back.out(1.6)"}}, 0.3);')
        nx, ny, nw = x0, cy + int(H * 0.03), x1 - x0
    else:                                                     # progress bar
        bw, bh = int((x1 - x0) * 0.8), int(H * 0.09)
        bx, by = (x0 + x1) // 2 - bw // 2, y0 + int((y1 - y0) * 0.45)
        parts.append(f'<div style="position:absolute;left:{bx}px;top:{by}px;width:{bw}px;height:{bh}px;border-radius:{bh}px;'
                     f'background:{pal["soft"]};border:8px solid #111111;box-sizing:border-box;overflow:hidden">'
                     f'<div id="{P}fill" style="width:100%;height:100%;background:{fill_col}"></div></div>')
        js.append(f'tl.fromTo("#{P}fill", {{scaleX: 0, transformOrigin: "0% 50%"}}, {{scaleX: {val / 100:.3f}, duration: 0.9, '
                  f'ease: "power2.out"}}, 0.3);')
        nx, ny, nw = bx, by + bh + int(H * 0.03), bw
    parts.append(f'<div style="position:absolute;left:{nx}px;top:{ny}px;width:{nw}px;text-align:center;font-family:\'{T.HEAD}\';'
                 f'font-size:{vs}px;color:{pal["ink"]}"><span id="{P}val">0%</span></div>')
    js.append(f'const m{P.replace("-", "")} = {{v: 0}}; tl.to(m{P.replace("-", "")}, {{v: {val:.0f}, duration: 0.9, ease: "power2.out", '
              f'onUpdate: () => {{ document.querySelector("#{P}val").textContent = Math.round(m{P.replace("-", "")}.v) + "%"; }}}}, 0.3);')
    js.append(f'tl.call(() => {{ document.querySelector("#{P}val").textContent = "{val:.0f}%"; }}, null, 1.25);')
    cues = [(0.3, "tick"), (1.2, "alert" if val < 20 else "ding")]
    return {"html": "".join(parts), "css": ".hw { display:inline-block; }", "js": "\n".join(js), "cues": cues}


def _bbox(d):
    xs = [float(a) for a in re.findall(r"(-?\d+\.?\d*),", d)]
    ys = [float(b) for b in re.findall(r",(-?\d+\.?\d*)", d)]
    return (min(xs), min(ys), max(xs), max(ys)) if xs and ys else (0, 0, 1000, 460)


def map_flag(P, beat, ctx):
    W, H, pal, v = ctx["W"], ctx["H"], ctx["pal"], ctx.get("variant", 0)
    x0, x1, y0, y1 = T._box(ctx)
    code, flag_id, slug, name = (ctx.get("country") or countries(beat["text"])[0])
    ne = L.load("natural_earth") if "natural_earth" in L.installed() else None
    land = "#FFFFFF" if pal["ink"] == "#111111" else pal["soft"]
    parts, js = [], []
    mw = x1 - x0
    mh = int(mw * 460 / 1000)
    if mh > (y1 - y0):
        mh = y1 - y0
        mw = int(mh * 1000 / 460)
    mx, my = (x0 + x1) // 2 - mw // 2, y0 + ((y1 - y0) - mh) // 2
    if ne and v in (0, 1) or ne and v == 2:
        paths = []
        for s, c in ne["icons"].items():
            on = s == slug
            paths.append(f'<path d="{c["d"]}" fill="{pal["pop"] if on else land}" stroke="#111111" '
                         f'stroke-width="{1.2 if on else 0.6}"{f" id={chr(34)}{P}ctry{chr(34)}" if on else ""}/>')
        vb = "0 0 1000 460"
        if v == 2:                                            # small inset map in the corner
            mw, mh = int((x1 - x0) * 0.32), int((x1 - x0) * 0.32 * 0.46)
            mx, my = x1 - mw, y1 - mh
        parts.append(f'<svg id="{P}map" viewBox="{vb}" style="position:absolute;left:{mx}px;top:{my}px;width:{mw}px;'
                     f'height:{mh}px;overflow:visible">{"".join(paths)}</svg>')
        js.append(f'tl.fromTo("#{P}map", {{opacity: 0, scale: 0.92}}, {{opacity: 1, scale: 1, duration: 0.45, '
                  f'ease: "{D.EASE_IN}"}}, 0);')
        if slug and v == 1:                                   # zoom into the country
            bx0, by0, bx1, by1 = _bbox(ne["icons"][slug]["d"])
            bw, bh = max(8.0, bx1 - bx0), max(8.0, by1 - by0)
            z = max(1.4, min(6.0, 0.55 * min(1000 / bw, 460 / bh)))
            ccx, ccy = (bx0 + bx1) / 2 / 1000, (by0 + by1) / 2 / 460
            js.append(f'tl.to("#{P}map", {{scale: {z:.2f}, transformOrigin: "{ccx * 100:.1f}% {ccy * 100:.1f}%", '
                      f'x: {int((0.5 - ccx) * mw)}, y: {int((0.5 - ccy) * mh)}, duration: 1.1, ease: "power3.inOut"}}, 0.35);')
        if slug:
            js.append(f'tl.fromTo("#{P}ctry", {{opacity: 0.3}}, {{opacity: 1, duration: 0.15, yoyo: true, repeat: 3}}, 0.4);')
    flag_uri = f"data:image/svg+xml;base64," + __import__("base64").b64encode(L.svg(flag_id).encode()).decode()
    fw = int((x1 - x0) * (0.5 if v == 2 else 0.2))
    fh = int(fw * 0.75)
    fx, fy = ((x0 + x1) // 2 - fw // 2 - (int((x1 - x0) * 0.12) if v == 2 else 0), y0 + int((y1 - y0) * 0.08)) \
        if v == 2 else (x0, y1 - fh)
    parts.append(f'<img id="{P}flag" alt="" src="{flag_uri}" style="position:absolute;left:{fx}px;top:{fy}px;width:{fw}px;'
                 f'height:{fh}px;border:{max(5, fw // 40)}px solid #111111;border-radius:{max(8, fw // 20)}px;'
                 f'box-shadow:0 {fw // 24}px 0 rgba(0,0,0,0.22);object-fit:cover">')
    js.append(f'tl.fromTo("#{P}flag", {{scale: 0, rotation: -12, transformOrigin: "50% 50%"}}, {{scale: 1, rotation: -3, '
              f'duration: 0.45, ease: "{D.EASE_POP}"}}, {0.5 if v != 2 else 0.1:.2f});')
    if v == 2:
        js.append(f'tl.fromTo("#{P}flag", {{skewY: 0}}, {{skewY: 3, duration: 0.5, yoyo: true, repeat: '
                  f'{max(0, int(ctx["dur"] / 0.5) - 2)}, ease: "sine.inOut"}}, 0.6);')
    ns = T.fit(name.upper(), (x1 - x0) * 0.5, int(H * 0.09), int(H * 0.045))
    nx, ny = (fx, fy + fh + int(H * 0.02)) if v == 2 else (fx + fw + int(W * 0.02), y1 - int(ns * 1.2))
    parts.append(f'<div id="{P}nm" style="position:absolute;left:{nx}px;top:{ny}px;font-family:\'{T.HEAD}\';font-size:{ns}px;'
                 f'line-height:1;color:{pal["ink"]};white-space:nowrap"><span style="background:{pal["hi"]};'
                 f'color:{"#FFFFFF" if pal["hi"] == "#111111" else "#111111"};padding:0.06em 0.2em;border-radius:0.1em">'
                 f'{T.esc(name.upper())}</span></div>')
    js.append(f'tl.fromTo("#{P}nm", {{opacity: 0, x: -40}}, {{opacity: 1, x: 0, duration: 0.3, ease: "{D.EASE_IN}"}}, '
              f'{0.65 if v != 2 else 0.3:.2f});')
    return {"html": "".join(parts), "css": "", "js": "\n".join(js), "cues": [(0.05, "whoosh"), (0.5, "swipe")]}


def build(name, P, beat, ctx):
    return {"icon_list": icon_list, "versus": versus, "pile": pile, "timeline": timeline, "meter": meter,
            "map_flag": map_flag}[name](P, beat, ctx)
