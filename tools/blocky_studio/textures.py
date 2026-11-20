"""Procedural textures: blocky-avatar faces, outfit patterns, signs, calendars."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts", "ArchivoBlack-Regular.ttf")  # bundled, OFL
FONT_SERIF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts", "DMSerifDisplay-Regular.ttf")  # bundled, OFL
INK = (25, 20, 20, 255)
WHITE = (255, 255, 255, 255)
BLUSH = (255, 130, 150, 170)


def font(size, path=FONT_BOLD):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# --------------------------------------------------------------------------- faces
# 512x512 RGBA decal laid on the head's front face. Drawn at 2x and downsampled.

FACE_EXPRESSIONS = [
    "neutral", "smile", "happy", "laugh", "sleepy_blush", "sad", "crying", "scared",
    "shocked", "angry", "worried", "smug", "wink", "unimpressed", "love", "determined",
    "yelling", "nervous_sweat", "dizzy", "sleeping",
    "troll_grin", "screaming", "smirk", "blush_shy", "anime_smile", "anime_shocked", "anime_worried", "glare",
]


def face(expr, style="classic", lash=False):
    S = 1024
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = 26
    ex, ey, er = 300, 440, 62  # eye centre x offset from middle, y, radius
    cx = S // 2
    mouth_y = 690

    def eye_dot(x, y, r=er, white=False, pupil_dy=0):
        if white:
            d.ellipse([x - r * 1.25, y - r * 1.45, x + r * 1.25, y + r * 1.45], fill=WHITE, outline=INK, width=16)
            d.ellipse([x - r * 0.6, y - r * 0.6 + pupil_dy, x + r * 0.6, y + r * 0.6 + pupil_dy], fill=INK)
        else:
            d.ellipse([x - r * 0.75, y - r, x + r * 0.75, y + r], fill=INK)
            d.ellipse([x - r * 0.35, y - r * 0.75, x - r * 0.02, y - r * 0.3], fill=WHITE)
        if lash:
            d.line([x - r, y - r * 1.1, x - r * 1.5, y - r * 1.6], fill=INK, width=14)
            d.line([x + r, y - r * 1.1, x + r * 1.5, y - r * 1.6], fill=INK, width=14)

    def arc_eye(x, y, up=True, w=90):
        box = [x - w, y - 60, x + w, y + 60]
        d.arc(box, 200 if up else 20, 340 if up else 160, fill=INK, width=lw)

    def blush():
        for sx in (-1, 1):
            d.ellipse([cx + sx * 330 - 85, 560, cx + sx * 330 + 85, 625], fill=BLUSH)

    def brows(kind):
        for sx in (-1, 1):
            x = cx + sx * ex
            if kind == "angry":
                d.line([x - sx * 90, 300, x + sx * 70, 350], fill=INK, width=lw + 6)
            elif kind == "worried":
                d.line([x - sx * 90, 345, x + sx * 70, 300], fill=INK, width=lw)
            elif kind == "raised":
                d.arc([x - 90, 290, x + 90, 370], 200, 340, fill=INK, width=lw)
            elif kind == "flat":
                d.line([x - 80, 330, x + 80, 330], fill=INK, width=lw)

    L, R = cx - ex, cx + ex
    if expr == "neutral":
        eye_dot(L, ey); eye_dot(R, ey)
        d.line([cx - 70, mouth_y, cx + 70, mouth_y], fill=INK, width=lw)
    elif expr == "smile":
        eye_dot(L, ey); eye_dot(R, ey)
        d.arc([cx - 150, mouth_y - 130, cx + 150, mouth_y + 60], 20, 160, fill=INK, width=lw)
    elif expr == "happy":
        eye_dot(L, ey); eye_dot(R, ey)
        d.chord([cx - 160, mouth_y - 110, cx + 160, mouth_y + 110], 0, 180, fill=INK)
        d.chord([cx - 90, mouth_y + 30, cx + 90, mouth_y + 105], 0, 180, fill=(230, 80, 90, 255))
    elif expr == "laugh":
        for sx in (-1, 1):  # >  <
            x = cx + sx * ex
            d.line([x - sx * 70, ey - 60, x + sx * 50, ey], fill=INK, width=lw + 4)
            d.line([x + sx * 50, ey, x - sx * 70, ey + 60], fill=INK, width=lw + 4)
        d.chord([cx - 170, mouth_y - 120, cx + 170, mouth_y + 140], 0, 180, fill=INK)
        d.chord([cx - 100, mouth_y + 40, cx + 100, mouth_y + 135], 0, 180, fill=(230, 80, 90, 255))
        blush()
    elif expr == "sleepy_blush":
        arc_eye(L, ey + 20, up=False); arc_eye(R, ey + 20, up=False)
        d.arc([cx - 120, mouth_y - 110, cx + 120, mouth_y + 50], 20, 160, fill=INK, width=lw)
        blush()
    elif expr == "sad":
        brows("worried"); eye_dot(L, ey); eye_dot(R, ey)
        d.arc([cx - 120, mouth_y - 10, cx + 120, mouth_y + 140], 200, 340, fill=INK, width=lw)
    elif expr == "crying":
        brows("worried"); arc_eye(L, ey, up=False); arc_eye(R, ey, up=False)
        for x in (L, R):
            d.rounded_rectangle([x - 30, ey + 50, x + 30, ey + 300], 30, fill=(110, 190, 255, 230))
        d.arc([cx - 130, mouth_y - 10, cx + 130, mouth_y + 150], 200, 340, fill=INK, width=lw)
    elif expr == "scared":
        brows("worried"); eye_dot(L, ey, white=True, pupil_dy=10); eye_dot(R, ey, white=True, pupil_dy=10)
        d.ellipse([cx - 45, mouth_y - 10, cx + 45, mouth_y + 90], fill=INK)
    elif expr == "shocked":
        brows("raised"); eye_dot(L, ey, white=True); eye_dot(R, ey, white=True)
        d.ellipse([cx - 80, mouth_y - 50, cx + 80, mouth_y + 140], fill=INK)
        d.ellipse([cx - 45, mouth_y + 60, cx + 45, mouth_y + 125], fill=(230, 80, 90, 255))
    elif expr == "angry":
        brows("angry"); eye_dot(L, ey + 15, r=50); eye_dot(R, ey + 15, r=50)
        d.arc([cx - 120, mouth_y + 10, cx + 120, mouth_y + 140], 200, 340, fill=INK, width=lw)
    elif expr == "worried":
        brows("worried"); eye_dot(L, ey); eye_dot(R, ey)
        pts = [(cx - 130 + i * 52, mouth_y + (20 if i % 2 else -10)) for i in range(6)]
        d.line(pts, fill=INK, width=lw - 4, joint="curve")
    elif expr == "smug":
        brows("flat")
        for x in (L, R):
            d.chord([x - 75, ey - 60, x + 75, ey + 70], 0, 180, fill=INK)
        d.arc([cx - 40, mouth_y - 90, cx + 170, mouth_y + 40], 20, 120, fill=INK, width=lw)
    elif expr == "wink":
        eye_dot(L, ey); arc_eye(R, ey + 10, up=True)
        d.arc([cx - 150, mouth_y - 130, cx + 150, mouth_y + 60], 20, 160, fill=INK, width=lw)
        blush()
    elif expr == "unimpressed":
        for x in (L, R):
            d.chord([x - 75, ey - 60, x + 75, ey + 70], 0, 180, fill=INK)
            d.line([x - 85, ey - 5, x + 85, ey - 5], fill=INK, width=lw)
        d.line([cx - 60, mouth_y + 20, cx + 90, mouth_y + 10], fill=INK, width=lw)
    elif expr == "love":
        for x in (L, R):
            d.polygon([(x, ey + 75), (x - 85, ey - 5), (x - 45, ey - 65), (x, ey - 30),
                       (x + 45, ey - 65), (x + 85, ey - 5)], fill=(230, 40, 70, 255))
        d.arc([cx - 150, mouth_y - 130, cx + 150, mouth_y + 60], 20, 160, fill=INK, width=lw)
        blush()
    elif expr == "determined":
        brows("angry"); eye_dot(L, ey); eye_dot(R, ey)
        d.line([cx - 100, mouth_y + 20, cx + 100, mouth_y + 20], fill=INK, width=lw + 4)
    elif expr == "yelling":
        brows("angry"); eye_dot(L, ey, white=True); eye_dot(R, ey, white=True)
        d.rounded_rectangle([cx - 140, mouth_y - 60, cx + 140, mouth_y + 170], 70, fill=INK)
        d.rectangle([cx - 110, mouth_y - 50, cx + 110, mouth_y - 15], fill=WHITE)
    elif expr == "nervous_sweat":
        brows("worried"); eye_dot(L, ey); eye_dot(R, ey)
        d.line([cx - 110, mouth_y + 20, cx + 110, mouth_y + 20], fill=INK, width=lw)
        d.polygon([(870, 200), (830, 300), (910, 300)], fill=(110, 190, 255, 255))
        d.ellipse([828, 260, 912, 340], fill=(110, 190, 255, 255))
    elif expr == "dizzy":
        for x in (L, R):
            for k in range(3):
                r = 30 + k * 28
                d.arc([x - r, ey - r, x + r, ey + r], k * 90, k * 90 + 270, fill=INK, width=14)
        pts = [(cx - 120 + i * 48, mouth_y + (25 if i % 2 else 0)) for i in range(6)]
        d.line(pts, fill=INK, width=lw - 4)
    elif expr == "sleeping":
        arc_eye(L, ey + 20, up=False); arc_eye(R, ey + 20, up=False)
        d.ellipse([cx - 30, mouth_y, cx + 30, mouth_y + 50], outline=INK, width=16)
        f = font(150)
        d.text((800, 120), "z", font=f, fill=INK)
        d.text((880, 30), "z", font=font(100), fill=INK)
    elif expr == "troll_grin":
        brows("raised")
        for x in (L, R):
            d.ellipse([x - 70, ey - 40, x + 70, ey + 40], fill=WHITE, outline=INK, width=12)
            d.ellipse([x - 22, ey - 22, x + 22, ey + 22], fill=INK)
        d.chord([cx - 260, mouth_y - 150, cx + 260, mouth_y + 150], 0, 180, fill=INK)
        for i in range(8):
            x0 = cx - 230 + i * 58
            d.rectangle([x0, mouth_y + 4, x0 + 48, mouth_y + 60], fill=WHITE)
    elif expr == "screaming":
        brows("worried")
        for x in (L, R):
            d.ellipse([x - 95, ey - 95, x + 95, ey + 95], fill=WHITE, outline=INK, width=16)
            d.ellipse([x - 20, ey - 20, x + 20, ey + 20], fill=INK)
        d.ellipse([cx - 150, mouth_y - 80, cx + 150, mouth_y + 230], fill=INK)
        d.rectangle([cx - 110, mouth_y - 60, cx + 110, mouth_y - 20], fill=WHITE)
    elif expr == "smirk":
        brows("flat")
        for x in (L, R):
            d.chord([x - 75, ey - 50, x + 75, ey + 70], 0, 180, fill=INK)
        d.arc([cx - 200, mouth_y - 140, cx + 120, mouth_y + 60], 20, 110, fill=INK, width=lw)
    elif expr == "blush_shy":
        arc_eye(L, ey + 20, up=True); arc_eye(R, ey + 20, up=True)
        d.arc([cx - 90, mouth_y - 70, cx + 90, mouth_y + 40], 20, 160, fill=INK, width=lw - 4)
        for sx in (-1, 1):
            d.ellipse([cx + sx * 300 - 130, 520, cx + sx * 300 + 130, 640], fill=(255, 90, 120, 200))
    elif expr.startswith("anime_"):
        for x in (L, R):
            d.ellipse([x - 90, ey - 120, x + 90, ey + 110], fill=INK)
            d.ellipse([x - 50, ey - 90, x - 5, ey - 40], fill=WHITE)
            d.ellipse([x + 20, ey + 30, x + 45, ey + 55], fill=WHITE)
        if expr == "anime_smile":
            d.arc([cx - 110, mouth_y - 80, cx + 110, mouth_y + 60], 20, 160, fill=INK, width=lw - 4)
            blush()
        elif expr == "anime_shocked":
            d.ellipse([cx - 40, mouth_y, cx + 40, mouth_y + 90], fill=(170, 30, 40, 255), outline=INK, width=10)
            for sx in (-1, 1):
                d.ellipse([cx + sx * 330 - 50, 580, cx + sx * 330 + 50, 640], fill=(220, 40, 50, 230))
        else:
            for sx in (-1, 1):
                d.line([cx + sx * ex - sx * 100, 280, cx + sx * ex + sx * 60, 250], fill=INK, width=lw)
            d.arc([cx - 80, mouth_y + 10, cx + 80, mouth_y + 110], 200, 340, fill=INK, width=lw - 4)
    elif expr == "glare":
        brows("angry")
        for x in (L, R):
            d.ellipse([x - 80, ey - 35, x + 80, ey + 45], fill=WHITE, outline=INK, width=12)
            d.ellipse([x - 22, ey - 15, x + 22, ey + 30], fill=INK)
        d.line([cx - 70, mouth_y + 20, cx + 60, mouth_y + 10], fill=INK, width=lw)
    else:
        raise ValueError(expr)
    return im.resize((512, 512), Image.LANCZOS)


# --------------------------------------------------------------------------- outfits

def solid(color, size=64):
    return Image.new("RGB", (size, size), color)


def stripes(c1, c2, n=8, size=256, vertical=False):
    im = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(im)
    h = size / (n * 2)
    for i in range(n):
        y0 = int(i * 2 * h + h)
        if vertical:
            d.rectangle([y0, 0, int(y0 + h) - 1, size], fill=c2)
        else:
            d.rectangle([0, y0, size, int(y0 + h) - 1], fill=c2)
    return im


def plaid(base, line, size=256):
    im = Image.new("RGB", (size, size), base)
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(0, size, 42):
        d.rectangle([i, 0, i + 8, size], fill=line + (160,))
        d.rectangle([0, i, size, i + 8], fill=line + (160,))
        d.rectangle([i + 20, 0, i + 22, size], fill=(255, 255, 255, 90))
    return im


def hoodie_front(color, string=(240, 240, 240), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    dark = tuple(max(0, c - 40) for c in color)
    d.rounded_rectangle([50, 165, 206, 240], 12, fill=dark)  # pocket
    d.line([95, 0, 85, 110], fill=string, width=9)
    d.line([161, 0, 171, 110], fill=string, width=9)
    d.polygon([(70, 0), (186, 0), (128, 40)], fill=dark)  # collar dip
    return im


def suit_front(jacket, shirt=(245, 245, 245), tie=(25, 25, 25), size=256, bowtie=False, sparkle=False):
    im = Image.new("RGB", (size, size), jacket)
    d = ImageDraw.Draw(im)
    if sparkle:
        rnd = random.Random(4)
        for _ in range(900):
            x, y = rnd.randrange(size), rnd.randrange(size)
            c = rnd.choice([(255, 215, 90), (200, 150, 40), (255, 240, 170), (150, 100, 20)])
            d.rectangle([x, y, x + 3, y + 3], fill=c)
    d.polygon([(85, 0), (171, 0), (128, 150)], fill=shirt)
    if bowtie:
        d.polygon([(100, 15), (128, 30), (100, 45)], fill=tie)
        d.polygon([(156, 15), (128, 30), (156, 45)], fill=tie)
    else:
        d.polygon([(120, 10), (136, 10), (142, 120), (128, 140), (114, 120)], fill=tie)
    d.line([(85, 0), (128, 150)], fill=(0, 0, 0), width=4)
    d.line([(171, 0), (128, 150)], fill=(0, 0, 0), width=4)
    for y in (175, 215):
        d.ellipse([122, y, 134, y + 12], fill=(20, 20, 20))
    return im


def jersey(color, number="10", trim=(255, 255, 255), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, size, 14], fill=trim)
    d.text((size / 2, size / 2 + 10), number, font=font(120), fill=trim, anchor="mm")
    return im


def overalls(denim=(70, 100, 170), shirt=(220, 80, 50), size=256):
    im = Image.new("RGB", (size, size), shirt)
    d = ImageDraw.Draw(im)
    d.rectangle([60, 110, 196, size], fill=denim)
    d.rectangle([60, 0, 85, 115], fill=denim)
    d.rectangle([171, 0, 196, 115], fill=denim)
    for x in (72, 184):
        d.ellipse([x - 9, 100, x + 9, 118], fill=(230, 200, 80))
    return im


def pajama(color=(250, 170, 200), dot=(255, 255, 255), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    for y in range(10, size, 48):
        for x in range(10 + (y // 48 % 2) * 24, size, 48):
            d.ellipse([x, y, x + 12, y + 12], fill=dot)
    return im


def button_shirt(color=(240, 120, 40), btn=(250, 210, 60), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    light = tuple(min(255, c + 60) for c in color)
    d.polygon([(90, 0), (166, 0), (128, 60)], fill=light)
    for y in (90, 150, 210):
        d.ellipse([116, y, 140, y + 24], fill=btn)
    return im


def school_uniform(jacket=(30, 30, 35), shirt=(245, 245, 245), tie=(20, 20, 20), size=256):
    return suit_front(jacket, shirt, tie, size)


def dress_pink(size=256):
    im = Image.new("RGB", (size, size), (255, 170, 210))
    d = ImageDraw.Draw(im)
    for y in range(0, size, 40):
        d.line([(0, y + 20), (size, y + 20)], fill=(255, 220, 235), width=6)
    d.polygon([(100, 20), (128, 45), (100, 70)], fill=(230, 70, 140))
    d.polygon([(156, 20), (128, 45), (156, 70)], fill=(230, 70, 140))
    return im


def wood(base=(150, 95, 55), size=256, seed=1, planks=4):
    rnd = random.Random(seed)
    im = Image.new("RGB", (size, size), base)
    d = ImageDraw.Draw(im)
    for _ in range(140):
        y = rnd.randrange(size)
        c = tuple(max(0, min(255, v + rnd.randint(-22, 14))) for v in base)
        d.line([(0, y), (size, y + rnd.randint(-4, 4))], fill=c, width=rnd.randint(1, 3))
    for i in range(1, planks):
        y = i * size // planks
        d.line([(0, y), (size, y)], fill=tuple(int(v * 0.6) for v in base), width=3)
    return im


def brick(base=(170, 80, 60), mortar=(215, 205, 190), size=256):
    im = Image.new("RGB", (size, size), mortar)
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    bh, bw = 32, 64
    for r in range(size // bh):
        off = (r % 2) * bw // 2
        for c in range(-1, size // bw + 1):
            x = c * bw + off
            col = tuple(max(0, min(255, v + rnd.randint(-15, 15))) for v in base)
            d.rectangle([x + 3, r * bh + 3, x + bw - 3, r * bh + bh - 3], fill=col)
    return im


def siding(base=(225, 225, 230), size=256, rows=12):
    im = Image.new("RGB", (size, size), base)
    d = ImageDraw.Draw(im)
    for i in range(rows):
        y = i * size // rows
        d.line([(0, y), (size, y)], fill=tuple(int(v * 0.82) for v in base), width=3)
    return im


def window_grid(frame=(255, 255, 255), glass=(140, 190, 230), cols=3, rows=2, lit=False, size=256):
    im = Image.new("RGB", (size, size), frame)
    d = ImageDraw.Draw(im)
    g = (255, 225, 140) if lit else glass
    m = 14
    cw = (size - m * (cols + 1)) / cols
    ch = (size - m * (rows + 1)) / rows
    for r in range(rows):
        for c in range(cols):
            x = m + c * (cw + m); y = m + r * (ch + m)
            d.rectangle([x, y, x + cw, y + ch], fill=g)
            if not lit:
                d.line([(x + cw * 0.2, y + ch * 0.8), (x + cw * 0.6, y + ch * 0.2)], fill=(210, 235, 255), width=6)
    return im


def road(size=512):
    im = Image.new("RGB", (size, size), (70, 72, 78))
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for _ in range(1500):
        x, y = rnd.randrange(size), rnd.randrange(size)
        v = rnd.randint(60, 90)
        d.point((x, y), fill=(v, v, v + 4))
    for y in range(0, size, 128):
        d.rectangle([size // 2 - 8, y + 20, size // 2 + 8, y + 90], fill=(250, 205, 40))
    d.rectangle([12, 0, 22, size], fill=(235, 235, 235))
    d.rectangle([size - 22, 0, size - 12, size], fill=(235, 235, 235))
    return im


def tiles(c1=(200, 200, 205), c2=(175, 175, 182), n=4, size=256):
    im = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(im)
    s = size // n
    for i in range(n):
        for j in range(n):
            if (i + j) % 2:
                d.rectangle([i * s, j * s, i * s + s, j * s + s], fill=c2)
    return im


def cobble(base=(205, 190, 150), size=256):
    rnd = random.Random(11)
    im = Image.new("RGB", (size, size), tuple(int(v * 0.75) for v in base))
    d = ImageDraw.Draw(im)
    for y in range(0, size, 32):
        for x in range(-(y // 32 % 2) * 16, size, 32):
            col = tuple(max(0, min(255, v + rnd.randint(-18, 18))) for v in base)
            d.rounded_rectangle([x + 2, y + 2, x + 30, y + 30], 7, fill=col)
    return im


def grass(size=256):
    rnd = random.Random(5)
    im = Image.new("RGB", (size, size), (95, 170, 70))
    d = ImageDraw.Draw(im)
    for _ in range(900):
        x, y = rnd.randrange(size), rnd.randrange(size)
        g = rnd.randint(140, 195)
        d.line([(x, y), (x + rnd.randint(-2, 2), y - rnd.randint(3, 7))], fill=(80, g, 60))
    return im


# --------------------------------------------------------------------------- signs / graphics

def sign(text, bg=(30, 60, 160), fg=(255, 255, 255), w=1024, h=256, border=None, fsize=None, serif=False):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    if border:
        d.rectangle([8, 8, w - 9, h - 9], outline=border, width=12)
    fs = fsize or int(h * 0.42)
    f = font(fs, FONT_SERIF if serif else FONT_BOLD)
    while d.textlength(text, font=f) > w * 0.88 and fs > 10:
        fs -= 4; f = font(fs, FONT_SERIF if serif else FONT_BOLD)
    d.text((w / 2, h / 2), text, font=f, fill=fg, anchor="mm")
    return im


def calendar_page(month="NOVEMBER", big="DAY 1", size=512):
    im = Image.new("RGB", (size, size), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, size, 140], fill=(205, 40, 45))
    d.text((size / 2, 85), month, font=font(66), fill=WHITE, anchor="mm")
    for x in (130, size - 130):
        d.rounded_rectangle([x - 12, 0, x + 12, 50], 6, fill=(40, 40, 40))
    fs = 210
    f = font(fs)
    while d.textlength(big, font=f) > size * 0.86:
        fs -= 8; f = font(fs)
    d.text((size / 2, 330), big, font=f, fill=(20, 20, 20), anchor="mm")
    return im


def newspaper(headline="TOWN NEWS", sub="SPECIAL EDITION", size=(512, 700)):
    w, h = size
    im = Image.new("RGB", size, (232, 230, 222))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 50), "THE DAILY TOWN", font=font(46, FONT_SERIF), fill=(20, 20, 20), anchor="mm")
    d.line([(20, 85), (w - 20, 85)], fill=(20, 20, 20), width=3)
    d.text((w / 2, 102), sub, font=font(18, FONT_SERIF), fill=(60, 60, 60), anchor="mm")
    y = 150
    for line in headline.split("\n"):
        fs = 70
        f = font(fs)
        while d.textlength(line, font=f) > w - 50:
            fs -= 4; f = font(fs)
        d.text((w / 2, y), line, font=f, fill=(200, 25, 30), anchor="mm")
        y += fs + 8
    d.rectangle([30, y + 10, w // 2 - 10, h - 60], fill=(160, 160, 160))
    for ly in range(y + 15, h - 60, 22):
        d.rectangle([w // 2 + 10, ly, w - 30, ly + 10], fill=(40, 40, 40))
    return im


def mood_dial(size=512):
    """Sun-to-storm gauge face (half yellow, half purple)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    d.ellipse([10, 10, size - 10, size - 10], fill=(235, 175, 50))
    for i in range(90):
        t = i / 89
        col = (int(250 * (1 - t) + 90 * t), int(190 * (1 - t) + 60 * t), int(60 * (1 - t) + 120 * t))
        a0 = -90 + i * 2
        d.pieslice([40, 40, size - 40, size - 40], a0 - 90, a0 - 88, fill=col)
    for i in range(90):
        t = i / 89
        col = (int(250 * (1 - t) + 90 * t), int(190 * (1 - t) + 60 * t), int(60 * (1 - t) + 120 * t))
        d.pieslice([40, 40, size - 40, size - 40], -180 + i * 4, -176 + i * 4, fill=col)
    d.ellipse([140, 220, 200, 280], fill=(255, 235, 120))
    d.ellipse([320, 230, 380, 270], fill=(230, 230, 240))
    d.polygon([(350, 270), (335, 310), (352, 305), (340, 340), (370, 290), (352, 294)], fill=(255, 220, 40))
    d.ellipse([c - 22, c - 22, c + 22, c + 22], fill=(50, 30, 25))
    return im


def speech_bubble(text="GOOD MORNING!", w=512, h=256):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, w - 10, h - 60], 90, fill=WHITE, outline=INK, width=8)
    d.polygon([(w / 2 - 30, h - 64), (w / 2 + 30, h - 64), (w / 2, h - 8)], fill=WHITE)
    d.line([(w / 2 - 30, h - 62), (w / 2, h - 8), (w / 2 + 30, h - 62)], fill=INK, width=8)
    f = font(56)
    while d.textlength(text, font=f) > w - 80:
        f = font(f.size - 4)
    d.text((w / 2, (h - 50) / 2), text, font=f, fill=INK, anchor="mm")
    return im


def chalkboard(lines, size=(1024, 512)):
    im = Image.new("RGB", size, (40, 85, 55))
    d = ImageDraw.Draw(im)
    rnd = random.Random(2)
    for _ in range(200):
        x, y = rnd.randrange(size[0]), rnd.randrange(size[1])
        d.point((x, y), fill=(70, 115, 85))
    y = 50
    for i, ln in enumerate(lines):
        d.text((50, y), ln, font=font(64 if i == 0 else 40), fill=(240, 240, 230))
        y += 90 if i == 0 else 60
    return im


def poster(title="STARLIGHT", sub="PRINCESS", bg=(250, 150, 200), size=(256, 384)):
    im = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(im)
    w, h = size
    d.rectangle([10, 10, w - 10, h - 10], outline=(255, 255, 255), width=6)
    d.text((w / 2, 45), title, font=font(30), fill=(255, 255, 255), anchor="mm")
    d.ellipse([w / 2 - 50, 90, w / 2 + 50, 190], fill=(255, 220, 200))
    d.polygon([(w / 2 - 80, h - 70), (w / 2 + 80, h - 70), (w / 2, 180)], fill=(220, 60, 140))
    d.text((w / 2, h - 40), sub, font=font(30), fill=(255, 255, 255), anchor="mm")
    return im


def sky_gradient(top, bottom, w=64, h=512):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a * (1 - t) + b * t) for a, b in zip(top, bottom)))
    return im


def rain_streaks(w=512, h=512, n=260, seed=9):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rnd.randrange(w), rnd.randrange(h)
        l = rnd.randint(20, 55)
        d.line([(x, y), (x - l * 0.12, y + l)], fill=(220, 230, 255, rnd.randint(110, 200)), width=2)
    return im


def star_sky(w=1024, h=512, seed=3):
    rnd = random.Random(seed)
    im = sky_gradient((8, 10, 40), (35, 45, 110), w, h)
    d = ImageDraw.Draw(im)
    for _ in range(300):
        x, y = rnd.randrange(w), rnd.randrange(h)
        b = rnd.randint(150, 255)
        d.point((x, y), fill=(b, b, b))
    return im


def soft_glow(color=(255, 230, 150), size=256):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(size // 2, 0, -2):
        a = int(255 * (1 - r / (size / 2)) ** 2)
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=color + (a,))
    return im


def caption_card(word="TOWN", highlight=True, w=1024, h=256, yellow=False, color=None):
    """Example of the bold outlined caption style used in the references."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(150)
    fill = color + (255,) if color else (255, 214, 0, 255) if yellow else (60, 230, 60, 255) if highlight else WHITE
    d.text((w / 2, h / 2), word, font=f, fill=fill, anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0, 255))
    return im


def varsity_jacket(body=(208, 38, 46), sleeve=(245, 245, 245), size=256):
    im = Image.new("RGB", (size, size), body)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 50, size], fill=sleeve)
    d.rectangle([206, 0, size, size], fill=sleeve)
    d.rectangle([108, 0, 148, size], fill=(245, 245, 245))  # open front shows white tee
    d.rectangle([0, 230, size, size], fill=(30, 30, 40))     # ribbed hem
    for x in (98, 158):
        for y in (60, 120, 180):
            d.ellipse([x - 6, y, x + 6, y + 12], fill=(230, 230, 230))
    return im


def academy_tee(color=(47, 127, 216), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    d.ellipse([88, 70, 168, 150], outline=(255, 255, 255), width=12)
    d.rectangle([0, 0, size, 10], fill=(255, 255, 255))
    return im


def emblem(color=(80, 220, 255), size=512, crown=True):
    """Titan emblem: ring + lightning bolt + flame crown (transparent)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    d.ellipse([70, 110, size - 70, size - 30], outline=color + (255,), width=34)
    if crown:
        d.polygon([(150, 150), (180, 30), (220, 120), (256, 10), (292, 120), (332, 30), (362, 150)], fill=color + (255,))
    d.polygon([(290, 150), (200, 310), (262, 300), (220, 440), (330, 260), (268, 270), (318, 150)], fill=color + (255,))
    glow = im.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(glow, im)
    return out


def neon_text(text, color=(255, 60, 90), w=1024, h=384, bg=(60, 10, 20)):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, w - 11, h - 11], outline=color, width=10)
    lines = text.split("\n")
    fs = int(h / (len(lines) + 1))
    f = font(fs, FONT_SERIF)
    for i, ln in enumerate(lines):
        d.text((w / 2, h * (i + 1) / (len(lines) + 1)), ln, font=f, fill=(255, 220, 225), anchor="mm",
               stroke_width=3, stroke_fill=color)
    return im


def ranking_board(title="RANKINGS", names=("1  TYLER", "2  KENDRA", "3  BROCK"), w=512, h=512):
    im = Image.new("RGB", (w, h), (15, 20, 50))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], outline=(255, 210, 40), width=8)
    d.text((w / 2, 70), title, font=font(60, FONT_SERIF), fill=(255, 220, 60), anchor="mm")
    for i, n in enumerate(names):
        d.text((50, 160 + i * 90), n, font=font(54, FONT_SERIF), fill=(255, 255, 255))
    return im


def hall_of_fame(name="TITAN ZERO", wins="100", losses="0", w=512, h=512):
    im = Image.new("RGB", (w, h), (30, 20, 10))
    d = ImageDraw.Draw(im)
    gold = (235, 190, 90)
    d.text((w / 2, 50), f"{name} · HALL OF FAME", font=font(30, FONT_SERIF), fill=gold, anchor="mm")
    d.rectangle([40, 90, w - 40, 300], outline=gold, width=6)
    d.text((70, 150), "WINS:", font=font(40, FONT_SERIF), fill=(250, 240, 220), anchor="lm")
    d.text((w - 70, 150), wins, font=font(70, FONT_SERIF), fill=(255, 255, 255), anchor="rm")
    d.line([(60, 195), (w - 60, 195)], fill=gold, width=3)
    d.text((70, 250), "LOSSES:", font=font(40, FONT_SERIF), fill=(250, 240, 220), anchor="lm")
    d.text((w - 70, 250), losses, font=font(70, FONT_SERIF), fill=(255, 255, 255), anchor="rm")
    for r in range(3):
        for c in range(8):
            x, y = 50 + c * 58, 330 + r * 60
            d.polygon([(x, y), (x + 34, y), (x + 26, y + 26), (x + 8, y + 26)], fill=gold)
            d.rectangle([x + 14, y + 26, x + 20, y + 40], fill=gold)
            d.rectangle([x + 6, y + 40, x + 28, y + 46], fill=gold)
    return im


def ecg_screen(w=512, h=320, color=(60, 255, 140)):
    im = Image.new("RGB", (w, h), (10, 25, 30))
    d = ImageDraw.Draw(im)
    pts, x = [], 0
    while x < w:
        pts += [(x, 170), (x + 40, 170), (x + 55, 120), (x + 65, 230), (x + 78, 60), (x + 90, 200), (x + 100, 170)]
        x += 130
    d.line(pts, fill=color, width=6)
    d.polygon([(w - 70, 40), (w - 50, 20), (w - 30, 40), (w - 50, 65)], fill=(255, 80, 120))
    return im


def soccer_ball(size=512):
    im = Image.new("RGB", (size, size // 2), (245, 245, 245))
    d = ImageDraw.Draw(im)
    rnd = random.Random(21)
    for _ in range(34):
        x, y = rnd.randrange(size), rnd.randrange(30, size // 2 - 30)
        r = rnd.randint(9, 13)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(15, 15, 15))
    return im


def skyscraper(base=(70, 140, 230), win=(200, 235, 255), w=256, h=1024, seed=0):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(im)
    for y in range(12, h, 36):
        for x in range(12, w, 34):
            c = win if rnd.random() > 0.15 else tuple(int(v * 0.7) for v in base)
            d.rectangle([x, y, x + 20, y + 24], fill=c)
    return im


def moss(size=256):
    rnd = random.Random(31)
    im = Image.new("RGB", (size, size), (60, 150, 50))
    d = ImageDraw.Draw(im)
    for _ in range(500):
        x, y = rnd.randrange(size), rnd.randrange(size)
        r = rnd.randint(2, 7)
        c = rnd.choice([(80, 175, 60), (45, 120, 40), (150, 120, 50), (180, 70, 50), (100, 190, 70)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return im


def pixel_face_tee(color=(70, 170, 60), size=256):
    """Green pixel-noise tee with a yellow pixel smiley badge (original design)."""
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for y in range(0, size, 16):
        for x in range(0, size, 16):
            if rnd.random() < 0.25:
                v = rnd.randint(-25, 25)
                d.rectangle([x, y, x + 15, y + 15], fill=tuple(max(0, min(255, c + v)) for c in color))
    k = (255, 230, 60)
    d.rectangle([60, 50, 196, 186], fill=(30, 30, 30))
    d.rectangle([72, 62, 184, 174], fill=k)
    for x0 in (96, 144):
        d.rectangle([x0, 86, x0 + 16, 110], fill=(30, 30, 30))
    for x0, y0 in ((88, 130), (104, 146), (120, 146), (136, 146), (152, 130)):
        d.rectangle([x0, y0, x0 + 16, y0 + 16], fill=(30, 30, 30))
    return im


def text_tee(lines=("REAL MEN", "WEAR", "PINK"), color=(20, 20, 22), fg=(245, 245, 245), size=256):
    im = Image.new("RGB", (size, size), color)
    d = ImageDraw.Draw(im)
    y = 60
    for i, ln in enumerate(lines):
        fs = 44
        f = font(fs)
        d.text((size / 2, y), ln, font=f, fill=(255, 120, 180) if i == len(lines) - 1 else fg, anchor="mm")
        y += 54
    return im


def knit_stripes(size=256, seed=6):
    rnd = random.Random(seed)
    im = Image.new("RGB", (size, size), (80, 120, 60))
    d = ImageDraw.Draw(im)
    pal = [(70, 120, 60), (140, 170, 80), (220, 220, 200), (90, 90, 60), (180, 190, 120), (50, 90, 70)]
    y = 0
    while y < size:
        h = rnd.choice((6, 8, 10, 14))
        d.rectangle([0, y, size, y + h], fill=rnd.choice(pal))
        y += h
    for _ in range(1500):
        x, yy = rnd.randrange(size), rnd.randrange(size)
        d.point((x, yy), fill=(255, 255, 255))
    return im


def hearts_pattern(bg=(250, 240, 235), heart=(220, 30, 50), size=256):
    im = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(im)
    for yy in range(16, size, 64):
        for xx in range(16 + (yy // 64 % 2) * 32, size, 64):
            d.ellipse([xx, yy, xx + 16, yy + 16], fill=heart)
            d.ellipse([xx + 12, yy, xx + 28, yy + 16], fill=heart)
            d.polygon([(xx, yy + 10), (xx + 28, yy + 10), (xx + 14, yy + 28)], fill=heart)
    return im


def crest_blazer(jacket=(25, 25, 28), trim=(240, 240, 240), size=256):
    im = suit_front(jacket, (245, 245, 245), (90, 90, 95))
    d = ImageDraw.Draw(im)
    d.line([(85, 0), (128, 150)], fill=trim, width=5)
    d.line([(171, 0), (128, 150)], fill=trim, width=5)
    d.ellipse([170, 80, 220, 130], fill=(200, 30, 40), outline=(240, 200, 60), width=4)
    d.polygon([(195, 92), (205, 105), (195, 118), (185, 105)], fill=(240, 200, 60))
    return im


def patterned_pants(size=256):
    rnd = random.Random(8)
    im = Image.new("RGB", (size, size), (150, 150, 150))
    d = ImageDraw.Draw(im)
    for _ in range(400):
        x, y = rnd.randrange(size), rnd.randrange(size)
        v = rnd.choice([60, 90, 200, 230])
        d.rectangle([x, y, x + 6, y + 6], fill=(v, v, v))
    return im


def phone_chat(messages=("hi practice number", "you're the prettiest girl in school", "my brain shuts off whenever you smile",
                         "goodnight", "she laughed at my joke today"), title="Contact", w=360, h=720):
    im = Image.new("RGB", (w, h), (245, 240, 236))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(235, 230, 226))
    d.ellipse([w / 2 - 22, 12, w / 2 + 22, 56], fill=(220, 90, 70))
    d.text((w / 2, 72), title, font=font(18), fill=(30, 30, 30), anchor="mm")
    y = 120
    for m in messages:
        f = font(18)
        lines, cur = [], ""
        for word in m.split():
            if d.textlength(cur + " " + word, font=f) > w * 0.6:
                lines.append(cur); cur = word
            else:
                cur = (cur + " " + word).strip()
        lines.append(cur)
        bh = 18 + 24 * len(lines)
        d.rounded_rectangle([20, y, w * 0.72, y + bh], 16, fill=(225, 222, 220))
        for i, ln in enumerate(lines):
            d.text((34, y + 10 + i * 24), ln, font=f, fill=(20, 20, 20))
        y += bh + 22
    d.rounded_rectangle([16, h - 60, w - 16, h - 20], 20, outline=(200, 200, 200), width=2)
    return im


def sticky_note(lines=("practice #", "555-0143", "text me <3"), size=256):
    im = Image.new("RGB", (size, size), (255, 200, 220))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((size / 2, 60 + i * 70), ln, font=font(46 if i == 1 else 32), fill=(40, 30, 40), anchor="mm")
    return im


def composition_cover(size=(384, 512)):
    w, h = size
    rnd = random.Random(13)
    im = Image.new("RGB", size, (240, 240, 240))
    d = ImageDraw.Draw(im)
    for _ in range(2500):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r = rnd.randint(2, 7)
        d.ellipse([x, y, x + r, y + r * 0.6], fill=(15, 15, 15))
    d.rectangle([60, 70, w - 60, 200], fill=(250, 250, 250), outline=(20, 20, 20), width=3)
    d.text((w / 2, 100), "COMPOSITION", font=font(30), fill=(20, 20, 20), anchor="mm")
    for yy in (140, 165, 190):
        d.line([(80, yy), (w - 80, yy)], fill=(120, 120, 120), width=2)
    cx, cy = w / 2, 330
    for a in range(0, 360, 60):
        import math as _m
        d.ellipse([cx + 40 * _m.cos(_m.radians(a)) - 30, cy + 40 * _m.sin(_m.radians(a)) - 30,
                   cx + 40 * _m.cos(_m.radians(a)) + 30, cy + 40 * _m.sin(_m.radians(a)) + 30], fill=(240, 80, 150))
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(250, 220, 60))
    d.line([(cx, cy + 40), (cx - 10, h - 40)], fill=(60, 180, 60), width=10)
    return im


def lined_paper(lines=("compliments from me:", "1. pretty", "2. nice", "3. funny"), size=(384, 512)):
    w, h = size
    im = Image.new("RGB", size, (252, 252, 248))
    d = ImageDraw.Draw(im)
    for y in range(60, h, 32):
        d.line([(0, y), (w, y)], fill=(170, 200, 235), width=2)
    d.line([(50, 0), (50, h)], fill=(235, 140, 140), width=2)
    for i, ln in enumerate(lines):
        d.text((60, 36 + i * 32), ln, font=font(22), fill=(40, 60, 170))
    return im


def night_sky_poster(size=(384, 512)):
    w, h = size
    im = Image.new("RGB", size, (20, 30, 70))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 60), "THE NIGHT SKY", font=font(40), fill=(250, 210, 80), anchor="mm")
    d.arc([60, 180, 220, 400], 90, 270, fill=(240, 240, 240), width=24)
    d.ellipse([200, 220, 300, 320], fill=(240, 150, 60))
    d.rounded_rectangle([250, 160, 300, 260], 25, fill=(90, 170, 240))
    return im


def banner_picture_day(w=1024, h=256):
    im = Image.new("RGB", (w, h), (30, 60, 170))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 95), "PICTURE DAY", font=font(110), fill=(255, 255, 255), anchor="mm")
    d.text((w / 2, 195), "CLASS OF 2026", font=font(56), fill=(250, 210, 60), anchor="mm")
    return im


def bulletin_board(w=768, h=512):
    im = Image.new("RGB", (w, h), (200, 150, 95))
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for _ in range(800):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d.point((x, y), fill=(170, 120, 70))
    d.rectangle([40, 40, 420, 470], fill=(255, 255, 255))
    d.text((230, 140), "PICTURE", font=font(64), fill=(220, 60, 60), anchor="mm")
    d.text((230, 230), "DAY", font=font(90), fill=(220, 60, 60), anchor="mm")
    d.text((230, 330), "THIS FRIDAY", font=font(36), fill=(40, 40, 40), anchor="mm")
    d.text((230, 390), "SMILE!", font=font(36), fill=(240, 160, 40), anchor="mm")
    d.rectangle([460, 60, 730, 300], fill=(255, 255, 255))
    d.text((595, 150), "CHOIR", font=font(52), fill=(190, 70, 190), anchor="mm")
    d.text((595, 220), "TRYOUTS", font=font(38), fill=(190, 70, 190), anchor="mm")
    d.rectangle([480, 330, 700, 470], fill=(255, 240, 120))
    for i in range(4):
        d.line([(500, 360 + i * 28), (680, 360 + i * 28)], fill=(90, 90, 90), width=4)
    return im


def book_spines(w=512, h=256, seed=1):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), (90, 55, 30))
    d = ImageDraw.Draw(im)
    pal = [(180, 40, 40), (40, 90, 170), (230, 190, 60), (40, 130, 80), (120, 60, 150), (230, 120, 40), (30, 30, 30)]
    for shelf in range(2):
        y0 = shelf * h // 2 + 8
        x = 6
        while x < w - 10:
            bw = rnd.randint(12, 26)
            bh = rnd.randint(int(h * 0.3), int(h * 0.44))
            d.rectangle([x, y0 + (h // 2 - 14 - bh), x + bw, y0 + h // 2 - 14], fill=rnd.choice(pal))
            x += bw + 2
    return im


def photo_print(w=384, h=288):
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([14, 14, w - 14, h - 50], fill=(60, 90, 180))
    rnd = random.Random(4)
    for i in range(9):
        x = 30 + i * 37
        c = rnd.choice([(220, 60, 60), (250, 220, 60), (60, 200, 220), (40, 40, 40), (160, 80, 200)])
        d.rectangle([x, 120, x + 26, 220], fill=c)
        d.rectangle([x + 3, 92, x + 23, 118], fill=(245, 205, 160))
    d.text((w / 2, h - 28), "CLASS OF 2026", font=font(22), fill=(30, 30, 30), anchor="mm")
    return im


def museum_photo(w=360, h=640):
    im = Image.new("RGB", (w, h), (245, 240, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(0, 0, 0))
    d.text((w / 2, 70), "Class Trip", font=font(24), fill=(255, 255, 255), anchor="mm")
    d.rectangle([20, 160, w - 20, 220], fill=(170, 30, 40))
    d.text((w / 2, 190), "NATURAL HISTORY MUSEUM", font=font(20), fill=(255, 230, 200), anchor="mm")
    bone = (210, 180, 150)
    d.line([(60, 330), (300, 300)], fill=bone, width=14)
    for i in range(7):
        d.line([(100 + i * 28, 320 - i * 3), (100 + i * 28, 380 - i * 3)], fill=bone, width=6)
    d.line([(300, 300), (340, 260)], fill=bone, width=10)
    d.ellipse([320, 240, 360, 280], fill=bone)
    d.rectangle([0, 520, w, h], fill=(160, 30, 40))
    return im


def cash_bills(w=256, h=128):
    im = Image.new("RGB", (w, h), (140, 200, 140))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], outline=(40, 110, 50), width=6)
    d.ellipse([w / 2 - 34, h / 2 - 34, w / 2 + 34, h / 2 + 34], outline=(40, 110, 50), width=6)
    d.text((w / 2, h / 2), "$", font=font(52), fill=(40, 110, 50), anchor="mm")
    d.text((30, 30), "100", font=font(20), fill=(40, 110, 50), anchor="mm")
    return im
