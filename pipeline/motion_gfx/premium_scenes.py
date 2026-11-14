"""The 19 premium motion blocks (pipeline/motion_gfx/premium, rebuilt from Raju's reference recordings) as scene types
of the motion-graphics planner.

Each block draws its own full-frame background and runs on measured timings. This module
  - maps a beat's words into the block's ctx (every reference default is overridden, so no placeholder names,
    brands or fake numbers from the references reach a video),
  - picks how many cycles a block plays so it fills its beat (blocks that end empty never leave the frame blank),
  - makes the block's background 8 % larger than the frame, so camera moves and the spring settle on the cut never
    show an edge,
  - maps the blocks' sound cues onto the library's kinds,
  - registers fit tests + roles with the planner (planner.register) like scenes.py does.

Quote shots ([quote: ...]) alternate between the classic quote card and glass_quote; line-chart shots between the
classic chart and chart_card (planner.SHOT_ALT).
"""
import re

from . import extras as X
from .premium import BLOCKS

NAMES = list(BLOCKS)
NO_CAMERA = {"card_flip", "card_wheel"}                        # read better without a camera move (handover note)
SAFE_CAMERAS = {"dolly", "pull", "handheld", "off", "flat"}   # moves that never uncover the block's own background
DATA = {"odometer", "donut_card", "chart_card", "list_circle", "word_wheel", "color_carousel"}
CUE_MAP = {"keyboard": "typing"}
COLOURS = ["#ef6f6c", "#5b8cff", "#2fbf71", "#f5a524", "#8a5cf6", "#18b5c8"]
STOP = set("a an the and or but so of to in on at for with by from is are was were be been it its this that these those "
           "as than then there their they them we you your our i he she his her not no just very really also into over "
           "about after before what which who how why when where".split())


def _clean(t):
    return re.sub(r"[^\w%$'.,\- ]+", " ", t or "").strip()


def _content(text, n=None):
    ws = [w.strip(".,!?;:'\"") for w in _clean(text).split()]
    ws = [w for w in ws if w and w.lower() not in STOP]
    return ws[:n] if n else ws


def _chunks(words, k):
    """Split words into k nearly equal lines."""
    n = max(1, len(words))
    out, i = [], 0
    for j in range(k):
        m = round((j + 1) * n / k)
        out.append(" ".join(words[i:m]))
        i = m
    return [x for x in out if x]


def _loops(beat, period, cap=3):
    return max(1, min(cap, int(round(beat["dur"] / max(0.3, period)))))


def _first_number(text):
    for val, _a, _b in X.numbers(text):
        if val >= 10 and float(val).is_integer():
            return int(val)
    return None


SEARCH = re.compile(r"\b(search(?:ed|es|ing)?|google[ds]?|looked up|look up|typed)\b(.*)", re.I)
POST = re.compile(r"\b(post(?:ed|s)?|tweet(?:ed|s)?|wrote online|went viral|viral)\b", re.I)
TOGGLE = re.compile(r"\b(turn(?:ed|s)? (?:it )?(?:off|on)|switch(?:ed|es)? (?:off|on)|shut (?:it )?down|on or off|"
                    r"enable[ds]?|disable[ds]?)\b", re.I)
MONEY = re.compile(r"\b(dollars?|rupees?|euros?|pounds?|currenc\w*|pay(?:s|ing|ment)?|paid|price[sd]?|money|cash|bank)\b", re.I)
CARD = re.compile(r"\b(card|credit|debit|wallet|payment)s?\b", re.I)
CART = re.compile(r"\b(cart|buy(?:s|ing)?|bought|order(?:s|ed)?|shop(?:ping)?|checkout)\b", re.I)


# ---------------------------------------------------------------------------------------------- ctx per block
def ctx_for(name, beat, ctx):
    """The block's ctx from the beat (+ the scene ctx: W, H, pal, shot)."""
    text, sh, pal = beat.get("text") or "", ctx.get("shot") or {}, ctx["pal"]
    words = _content(text)
    caps = [w.upper() for w in words]
    c = {"W": ctx["W"], "H": ctx["H"]}
    if name == "glass_quote":
        q = sh.get("text") if sh.get("type") == "quote" else text
        c.update(quote=f"“{q.strip()}”", name=(sh.get("by") or "").strip(), role="", label="", loops=1)
    elif name == "card_pops":
        ls = (caps + ["", "", ""])[:3]
        c.update(lines=[x for x in ls if x] or ["NOW"], top="", bottom="", loops=_loops(beat, 0.6))
    elif name == "card_wheel":
        ws = (caps + caps)[:4] or ["NOW"]
        c.update(words=ws, tokens=[w[:4] for w in ws], loops=1)
    elif name == "morph_word":
        w = max(words, key=len) if words else "WOW"
        # the block's look is multiply + lighten blending: the background has to be darker than the word in every
        # colour channel, so it keeps its dark navy and only the word takes the palette colour
        c.update(word=w.upper()[:8], color=pal.get("pop", "#00b2ff"), bg="#11112a",
                 loops=_loops(beat, 2.22, 2))
    elif name == "pill_split":
        n = _first_number(text)
        c.update(label=" ".join(words[:2]).title() or "Order", count=str(n if n and n < 100 else len(words) % 9 + 1),
                 loops=1)
    elif name == "card_flip":
        c.update(word=(words[0] if words else "Pay")[:8].title(), back=(words[1] if len(words) > 1 else "")[:10].title(),
                 color=pal.get("pop", "#6a11ff"), loops=1)
    elif name == "word_slide":
        ls = _chunks(_clean(text).split()[:10], 4)              # the whole line (the words carry the meaning)
        while len(ls) < 4:
            ls.append("")
        c.update(blocks=[[ls[0], ls[1]], [ls[2], ls[3]]] if ls[2] else [[ls[0], ls[1]]], loops=1)
    elif name == "chart_card":
        data = sh.get("data") if sh.get("type") == "chart" else None
        vals = [v for _k, v in data] if data and len(data) > 1 else [1, 2, 3, 4]
        lo, hi = min(vals), max(vals)
        series = [round(2.81 + 6.75 * (v - lo) / ((hi - lo) or 1), 3) for v in vals]   # y 275 = min, y 113 = max (labels)
        labels = [k for k, _v in data] if data else []
        top = f"{hi:g}" if data else ""
        c.update(title=(sh.get("title") or " ".join(words[:4])).strip(), series=series, predicted=[],
                 ylabels=(top, "", "", f"{lo:g}" if data else ""),
                 xlabels=labels[:: max(1, len(labels) // 4)][:4], legend=[sh.get("title") or "", ""], loops=1)
    elif name == "donut_card":
        p = X.percent(text)
        p = 50 if p is None else max(1, min(100, int(round(p))))
        c.update(title=" ".join(words[:3]).title() or "Share", sub="",
                 stats=[(p, 100, " ".join(words[:2]).title() or "Share", pal.get("pop", "#7b2ff7"))], loops=1)
    elif name == "search_type":
        m = SEARCH.search(text)
        q = _clean(m.group(2) if m and m.group(2).strip() else text).strip(" .,")
        c.update(query=" ".join(q.split()[:7]) or "search", loops=1)
    elif name == "word_wheel":
        items = X.list_items(text) or words
        ws = [w.title() for w in items][:12] or ["Now"]
        while len(ws) < 8:
            ws = ws + ws
        c.update(words=ws[:12], loops=max(2, min(8, int(beat["dur"] / 0.75))), start=2)
    elif name == "toggle":
        c.update(on="ON", off="OFF", color=pal.get("pop", "#3aa846"), loops=1)
    elif name == "list_circle":
        items = X.list_items(text) or words[:4]
        c.update(items=[(it.title()[:22], "", "", COLOURS[k % len(COLOURS)]) for k, it in enumerate(items[:5])] or
                 [("Now", "", "", COLOURS[0])], loops=1)
    elif name == "odometer":
        n = _first_number(text) or 100
        c.update(start=max(0, n - 3), end_text=f"{n:,}", label=" ".join(words[:4]).title(),
                 color=pal.get("pop", "#4f6ef2"), loops=1)
    elif name == "gradient_words":
        c.update(text=" ".join(_clean(text).split()[:7]), loops=1)
    elif name == "track_type":
        ls = [w for w in caps if len(w) <= 10][:4] or ["NOW"]
        c.update(lines=ls, loops=_loops(beat, 1.7, 2))
    elif name == "blur_zoom_type":
        c.update(lines=_chunks(_clean(text).split()[:6], 2), badge="", loops=_loops(beat, 2.12, 2))
    elif name == "post_card":
        c.update(text=_clean(text)[:140], name="Post", handle="", initials="", meta="", link="", loops=1)
    elif name == "color_carousel":
        items = X.list_items(text) or words[:5]
        c.update(cards=[(it.title()[:14], COLOURS[k % len(COLOURS)], ("", "", "")) for k, it in enumerate(items[:6])]
                 or [("Now", COLOURS[0], ("", "", ""))], loops=max(1, min(6, int(beat["dur"] / 1.38))), start=0)
    return c


def build(name, P, beat, ctx):
    parts = BLOCKS[name]["build"](P, ctx_for(name, beat, ctx))
    # the block's full-frame background 8 % larger than the frame: camera moves + the cut's settle never show an edge
    parts["html"] = parts["html"].replace(f'id="{P}-bg" style="position:absolute;inset:0;',
                                          f'id="{P}-bg" style="position:absolute;inset:-8%;', 1)
    parts["cues"] = [(t, CUE_MAP.get(k, k)) for t, k in parts.get("cues") or []]
    return {"html": parts["html"], "css": parts["css"], "js": parts["js"], "cues": parts["cues"]}


# ------------------------------------------------------------------------------------- fit tests for the planner
def _words_n(b):
    return len((b.get("text") or "").split())


def _f_len(lo, hi, strength=0.5):
    return lambda b, st: strength if lo <= _words_n(b) <= hi else 0.0


SPECS = {   # name: (roles, fit test)
    "glass_quote": ({"quote": 1.0}, lambda b, st: 0.0),                  # quote shots only (planner.SHOT_ALT)
    "chart_card": ({"statistic": 0.6}, lambda b, st: 0.0),               # line-chart shots only
    "word_slide": ({"transition": 0.8, "conclusion": 0.7, "story": 0.4}, _f_len(4, 10, 0.45)),
    "track_type": ({"transition": 1.0, "conclusion": 0.8, "warning": 0.5}, _f_len(1, 4, 0.55)),
    "blur_zoom_type": ({"conclusion": 0.9, "transition": 0.7, "definition": 0.5}, _f_len(3, 7, 0.45)),
    "gradient_words": ({"conclusion": 0.8, "definition": 0.6, "story": 0.3}, _f_len(3, 6, 0.4)),
    "morph_word": ({"transition": 0.7, "warning": 0.5}, _f_len(1, 3, 0.3)),
    "card_pops": ({"transition": 0.7, "list": 0.4}, lambda b, st: 0.4 if b["start"] < 12 and 3 <= _words_n(b) <= 8
                   else 0.0),
    "odometer": ({"statistic": 1.0}, lambda b, st: 0.85 if _first_number(b.get("text")) and
                 X.percent(b.get("text") or "") is None else 0.0),
    "donut_card": ({"statistic": 0.9, "comparison": 0.4}, lambda b, st: 0.8 if X.percent(b.get("text") or "") is not None
                   else 0.0),
    "list_circle": ({"list": 1.0, "process": 0.5}, lambda b, st: 0.85 if X.list_items(b.get("text") or "") else 0.0),
    "word_wheel": ({"list": 0.8}, lambda b, st: 0.7 if X.list_items(b.get("text") or "") else 0.0),
    "color_carousel": ({"list": 0.7, "comparison": 0.4}, lambda b, st: 0.6 if X.list_items(b.get("text") or "")
                       else 0.0),
    "search_type": ({"question": 0.8, "story": 0.6}, lambda b, st: 0.95 if SEARCH.search(b.get("text") or "") else 0.0),
    "post_card": ({"story": 0.8, "quote": 0.5}, lambda b, st: 0.9 if POST.search(b.get("text") or "") else 0.0),
    "toggle": ({"warning": 0.6, "story": 0.5}, lambda b, st: 0.9 if TOGGLE.search(b.get("text") or "") else 0.0),
    "card_flip": ({"story": 0.6}, lambda b, st: 0.8 if CARD.search(b.get("text") or "") else 0.0),
    "card_wheel": ({"story": 0.5, "comparison": 0.4}, lambda b, st: 0.75 if MONEY.search(b.get("text") or "") else 0.0),
    "pill_split": ({"story": 0.5}, lambda b, st: 0.8 if CART.search(b.get("text") or "") else 0.0),
}


LOOPING = {"card_pops", "morph_word", "track_type", "blur_zoom_type", "word_wheel", "color_carousel"}   # ctx sets loops


def natural_dur(name) -> float:
    """One cycle of the block (seconds), measured from the reference."""
    if name not in _DUR:
        _DUR[name] = float(BLOCKS[name]["build"]("x", {"W": 1920, "H": 1080, "loops": 1})["dur"])
    return _DUR[name]


_DUR = {}


def long_enough(name, beat) -> bool:
    """A block needs most of its cycle to read (>= 55 %); a block that doesn't loop shouldn't sit finished for long
    (<= 1.6x its cycle + 0.5 s)."""
    d, nat = beat.get("dur") or (beat["end"] - beat["start"]), natural_dur(name)
    return d >= 0.55 * nat and (name in LOOPING or d <= 1.6 * nat + 0.5)


def _timed(name, fits):
    return lambda b, st: fits(b, st) if long_enough(name, b) else 0.0


def register():
    from . import planner as PL
    for name, (roles, fits) in SPECS.items():
        PL.register(name, {"roles": roles, "data": name in DATA, "fits": _timed(name, fits)})
        PL.OWN_LAYOUTS[name] = 1
        PL.NO_FRAME.add(name)
