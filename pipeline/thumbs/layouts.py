"""The four thumbnail layouts, each in 16:9 (1280 x 720) and 9:16 (1080 x 1920) (docs/THUMBNAIL_PLAN.md section 3).

    big_number  huge number + headline + a small figure scene (the Nvidia cover)
    face_off    two big icon stickers split by a slanted VS bar
    hero_icon   one giant icon sticker, a stick figure reacting next to it, the headline on the other side
    stamp       headline + figure scene + a stamp across it (works without a number)

build(name, brief, theme, vertical) -> {"html", "texts": [{role, fill, bg, stroke}], "important": [roles]} or None
when the brief can't fill the layout (no number for big_number, no versus for face_off ...).
Coordinates keep the important text out of the 16:9 duration badge (bottom-right 22 % x 18 %) and, in 9:16, inside
the centre square y 420-1500 (Shorts covers are cropped to square / 4:5 in feeds).
"""

import re

from . import design as Ds

W169, H169 = 1280, 720
W916, H916 = 1080, 1920


def _auto_stamp(b) -> str:
    return b["stamp"] or "EXPLAINED"


def _texts(th, items):
    """Contrast specs: (role, fill, background behind it, outline share)."""
    worst_bg = Ds.mix(th["bg"], th["accent"], 0.22)          # the glow's brightest point
    out = []
    for role, fill, bg, stroke in items:
        out.append({"role": role, "fill": fill, "bg": bg or worst_bg, "stroke": stroke, "outline": th["outline"]})
    return out


def _spot(x, y, r, th):
    return (f'<div style="position:absolute;left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;'
            f'border-radius:50%;background:radial-gradient(circle, {th["accent"]}40, {th["accent"]}10 60%, transparent 72%)">'
            f'</div>')


def big_number(b, th, vertical):
    if not b["number"]:
        return None
    head, label = b["headline"], b["number_label"]
    if label and len(head.split()) + len(label.split()) > 4:
        label = ""
    hfont, nfont = th["head"], th["number"]
    parts, items = [], []
    if not vertical:
        if b["tag"]:
            parts.append(Ds.tag_pill(b["tag"], 0, 34, 760, 40, th, align="flex-start", x=50))
            items.append(("tag", Ds.WHITE, Ds.RED, 0))
        parts.append(_spot(1000, 360, 270, th))
        parts.append(Ds.text_box("number", b["number"], 36, 90, 780, 332, 380, nfont, th["accent"], th, stroke=0.035,
                                 glow=th["glow"]))
        items.append(("number", th["accent"], None, 0.035))
        y = 420
        if label:
            parts.append(Ds.text_box("label", label, 40, y, 770, 86, 76, hfont, th["accent_soft"], th, stroke=0.06))
            items.append(("label", th["accent_soft"], None, 0.06))
            y += 88
        parts.append(Ds.text_box("headline", head, 36, y, 790, 690 - y, 150, hfont, Ds.WHITE, th, stroke=0.07))
        items.append(("headline", Ds.WHITE, None, 0.07))
        parts.append(Ds.figure("figure", b["pose"], 890, 170, 410, th, prop=(b["icons"] or [None])[0], prop_size=120))
        if b["stamp"]:
            parts.append(Ds.stamp(b["stamp"], 846, 52, 400, 112, 80, th, rotate=-8))
            items.append(("stamp", Ds.STAMP, Ds.INK, 0))
        return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "number", "tag", "stamp", "label"]}
    if b["tag"]:
        parts.append(Ds.tag_pill(b["tag"], W916 // 2, 430, 940, 62, th))
        items.append(("tag", Ds.WHITE, Ds.RED, 0))
    parts.append(Ds.text_box("number", b["number"], 20, 500, 1040, 460, 560, nfont, th["accent"], th, stroke=0.035,
                             glow=th["glow"]))
    items.append(("number", th["accent"], None, 0.035))
    y = 968
    if label:
        parts.append(Ds.text_box("label", label, 60, y, 960, 104, 96, hfont, th["accent_soft"], th, stroke=0.06))
        items.append(("label", th["accent_soft"], None, 0.06))
        y += 106
    parts.append(Ds.text_box("headline", head, 30, y, 1020, 1300 - y, 190, hfont, Ds.WHITE, th, stroke=0.07))
    items.append(("headline", Ds.WHITE, None, 0.07))
    parts.append(_spot(420, 1600, 330, th))
    parts.append(Ds.figure("figure", b["pose"], 270, 1330, 520, th, prop=(b["icons"] or [None])[0], prop_size=150))
    if b["stamp"]:
        parts.append(Ds.stamp(b["stamp"], 580, 1336, 450, 116, 92, th, rotate=-8))
        items.append(("stamp", Ds.STAMP, Ds.INK, 0))
    return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "number", "tag", "stamp", "label"]}


def face_off(b, th, vertical):
    if not b["versus"] or len(b["versus_icons"]) < 2:
        return None
    (la, ra), (li, ri) = b["versus"], b["versus_icons"][:2]
    alt = th.get("accent2") or Ds.mix(th["accent"], "#FFFFFF", 0.3)
    hfont = th["head"]
    parts, items = [], []
    tint_l, tint_r = Ds.mix(th["base"], th["accent"], 0.32), Ds.mix(th["base"], alt, 0.22)
    if not vertical:
        parts.append(f'<div style="position:absolute;inset:0;background:{tint_l};clip-path:polygon(0 0,56% 0,44% 100%,0 100%)"></div>'
                     f'<div style="position:absolute;inset:0;background:{tint_r};clip-path:polygon(56% 0,100% 0,100% 100%,44% 100%)"></div>'
                     f'<div style="position:absolute;inset:0;background:{Ds.RED};clip-path:polygon(53.5% 0,58.5% 0,46.5% 100%,41.5% 100%)"></div>')
        if b["tag"]:
            parts.append(Ds.tag_pill(b["tag"], 0, 28, 700, 36, th, align="flex-start", x=44))
            items.append(("tag", Ds.WHITE, Ds.RED, 0))
        parts.append(Ds.sticker("icon_l", li, 130, 110, 290, th, rotate=-5))
        parts.append(Ds.sticker("icon_r", ri, 860, 110, 290, th, rotate=5))
        parts.append(Ds.text_box("side_l", la, 60, 418, 430, 74, 64, hfont, Ds.WHITE, th, stroke=0.08))
        parts.append(Ds.text_box("side_r", ra, 790, 418, 430, 74, 64, hfont, Ds.WHITE, th, stroke=0.08))
        items += [("side_l", Ds.WHITE, tint_l, 0.08), ("side_r", Ds.WHITE, tint_r, 0.08)]
        parts.append(f'<div data-role="vs" style="position:absolute;left:560px;top:190px;width:160px;height:160px;'
                     f'border-radius:50%;background:{Ds.RED};border:8px solid {Ds.INK};box-sizing:border-box;display:flex;'
                     f'align-items:center;justify-content:center;font-family:\'{hfont}\';font-size:76px;color:{Ds.WHITE};'
                     f'transform:rotate(-10deg);box-shadow:0 8px 0 {Ds.INK}">VS</div>')
        items.append(("vs", Ds.WHITE, Ds.RED, 0))
        parts.append(Ds.text_box("headline", b["headline_full"], 36, 520, 940, 180, 120, hfont, Ds.WHITE, th, stroke=0.07))
        items.append(("headline", Ds.WHITE, Ds.mix(tint_l, tint_r, 0.5), 0.07))
        return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "vs"]}
    parts.append(f'<div style="position:absolute;inset:0;background:{tint_l};clip-path:polygon(0 0,100% 0,100% 52%,0 60%)"></div>'
                 f'<div style="position:absolute;inset:0;background:{tint_r};clip-path:polygon(0 60%,100% 52%,100% 100%,0 100%)"></div>'
                 f'<div style="position:absolute;inset:0;background:{Ds.RED};clip-path:polygon(0 58.6%,100% 50.6%,100% 53.4%,0 61.4%)"></div>')
    if b["tag"]:
        parts.append(Ds.tag_pill(b["tag"], W916 // 2, 430, 940, 58, th))
        items.append(("tag", Ds.WHITE, Ds.RED, 0))
    parts.append(Ds.text_box("headline", b["headline_full"], 40, 520, 1000, 250, 170, hfont, Ds.WHITE, th, stroke=0.07))
    items.append(("headline", Ds.WHITE, tint_l, 0.07))
    parts.append(Ds.sticker("icon_l", li, 90, 790, 330, th, rotate=-5))
    parts.append(Ds.text_box("side_l", la, 450, 880, 560, 110, 90, hfont, Ds.WHITE, th, stroke=0.08))
    parts.append(Ds.sticker("icon_r", ri, 660, 1150, 330, th, rotate=5))
    parts.append(Ds.text_box("side_r", ra, 60, 1260, 560, 110, 90, hfont, Ds.WHITE, th, stroke=0.08))
    items += [("side_l", Ds.WHITE, tint_l, 0.08), ("side_r", Ds.WHITE, tint_r, 0.08)]
    parts.append(f'<div data-role="vs" style="position:absolute;left:440px;top:1020px;width:200px;height:200px;'
                 f'border-radius:50%;background:{Ds.RED};border:10px solid {Ds.INK};box-sizing:border-box;display:flex;'
                 f'align-items:center;justify-content:center;font-family:\'{hfont}\';font-size:96px;color:{Ds.WHITE};'
                 f'transform:rotate(-10deg);box-shadow:0 10px 0 {Ds.INK}">VS</div>')
    items.append(("vs", Ds.WHITE, Ds.RED, 0))
    parts.append(Ds.figure("figure", "point", 420, 1480, 400, th))
    return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "vs"]}


def hero_icon(b, th, vertical, second=False):
    if not b["icons"]:
        return None
    icon = b["icons"][1] if second and len(b["icons"]) > 1 else b["icons"][0]
    hfont = th["head"]
    parts, items = [], []
    pose = b["pose"] if b["pose"] not in ("walk", "sneak") else "point"
    if not vertical:
        mirror = second
        hx, ix, fx = (690, 120, 520) if mirror else (40, 720, 590)
        if b["tag"]:
            parts.append(Ds.tag_pill(b["tag"], 0, 44, 540, 38, th, align="flex-start", x=hx + 6))
            items.append(("tag", Ds.WHITE, Ds.RED, 0))
        parts.append(_spot(ix + 200, 320, 300, th))
        parts.append(Ds.sticker("icon", icon, ix, 100, 400, th, rotate=-4 if not mirror else 4))
        parts.append(Ds.text_box("headline", b["headline_full"], hx, 120, 550, 430, 150, hfont, Ds.WHITE, th, stroke=0.07,
                                 align="flex-start"))
        items.append(("headline", Ds.WHITE, None, 0.07))
        parts.append(Ds.figure("figure", pose, fx, 300, 290, th, flip=mirror))
        if b["stamp"]:
            sx = 700 if not mirror else 80
            parts.append(Ds.stamp(b["stamp"], sx, 470, 380, 100, 72, th, rotate=-8))
            items.append(("stamp", Ds.STAMP, Ds.INK, 0))
        return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "stamp"]}
    if b["tag"]:
        parts.append(Ds.tag_pill(b["tag"], W916 // 2, 430, 940, 60, th))
        items.append(("tag", Ds.WHITE, Ds.RED, 0))
    parts.append(Ds.text_box("headline", b["headline_full"], 30, 520, 1020, 400, 200, hfont, Ds.WHITE, th, stroke=0.07))
    items.append(("headline", Ds.WHITE, None, 0.07))
    parts.append(_spot(560, 1170, 340, th))
    parts.append(Ds.sticker("icon", icon, 340, 945, 440, th, rotate=-4))
    parts.append(Ds.figure("figure", pose, 70, 1270, 520, th))
    if b["stamp"]:
        parts.append(Ds.stamp(b["stamp"], 560, 1320, 450, 104, 84, th, rotate=-8))
        items.append(("stamp", Ds.STAMP, Ds.INK, 0))
    return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "stamp"]}


def stamp(b, th, vertical, second=False):
    """second = the mirrored spare: figure on the other side, the stamp tilted the other way."""
    word = _auto_stamp(b)
    hfont = th["head"]
    icons = b["icons"]
    parts, items = [], []
    if not vertical:
        if b["tag"]:
            parts.append(Ds.tag_pill(b["tag"], 0, 34, 700, 38, th, align="flex-start", x=46))
            items.append(("tag", Ds.WHITE, Ds.RED, 0))
        parts.append(Ds.text_box("headline", b["headline_full"], 36, 98, 1208, 250, 170, hfont, Ds.WHITE, th, stroke=0.07))
        items.append(("headline", Ds.WHITE, None, 0.07))
        fx, ix, sx, rot = (780, 600, 90, 7) if second else (180, 430, 610, -8)
        parts.append(_spot(fx + 120, 560, 230, th))
        parts.append(Ds.figure("figure", b["pose"], fx, 372, 330, th, flip=second, prop=icons[0] if icons else None,
                               prop_size=110))
        if len(icons) > 1:
            parts.append(Ds.sticker("icon", icons[1], ix, 430, 190, th, rotate=-rot))
        parts.append(Ds.stamp(word, sx, 404, 460, 118, 96, th, rotate=rot))
        items.append(("stamp", Ds.STAMP, Ds.INK, 0))
        return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "stamp"]}
    if b["tag"]:
        parts.append(Ds.tag_pill(b["tag"], W916 // 2, 430, 940, 60, th))
        items.append(("tag", Ds.WHITE, Ds.RED, 0))
    parts.append(Ds.text_box("headline", b["headline_full"], 30, 520, 1020, 430, 210, hfont, Ds.WHITE, th, stroke=0.07))
    items.append(("headline", Ds.WHITE, None, 0.07))
    parts.append(Ds.stamp(word, 150, 1020, 780, 180, 140, th, rotate=8 if second else -8))
    items.append(("stamp", Ds.STAMP, Ds.INK, 0))
    fx, ix = (520, 90) if second else (250, 680)
    parts.append(_spot(fx + 180, 1580, 330, th))
    parts.append(Ds.figure("figure", b["pose"], fx, 1290, 540, th, flip=second, prop=icons[0] if icons else None,
                           prop_size=160))
    if len(icons) > 1:
        parts.append(Ds.sticker("icon", icons[1], ix, 1330, 260, th, rotate=-6 if second else 6))
    return {"html": "".join(parts), "texts": _texts(th, items), "important": ["headline", "tag", "stamp"]}


BUILDERS = {"big_number": big_number, "face_off": face_off, "hero_icon": hero_icon, "stamp": stamp}


def fit_order(b) -> list:
    """Layouts that can be built for this brief, best fit first; thumbnail_layout: pins the first one."""
    score = {}
    if b["number"]:
        score["big_number"] = 3.0 if any(ch.isdigit() for ch in b["headline_full"]) else \
            (2.4 if re.search(r"[%$₹€£]", b["number"]) else 2.0)
    if b["versus"] and len(b["versus_icons"]) >= 2:
        score["face_off"] = 3.2 if any(w in b["headline_full"].split() for w in ("VS", "OR", "VERSUS")) else 2.6
    if b["icons"]:
        score["hero_icon"] = 1.8
    score["stamp"] = 2.8 if b["stamp"] else 1.2
    order = sorted(score, key=lambda k: (-score[k], list(BUILDERS).index(k)))
    pin = b.get("layout_pin")
    if pin in order:
        order.remove(pin)
        order.insert(0, pin)
    return order
