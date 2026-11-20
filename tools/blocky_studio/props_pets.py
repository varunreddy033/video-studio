"""Pets (with animatable part nodes), hatching eggs, founder statue, Stone Guardian."""
import math

from glb import Node, Mat, transform, box, quad, cylinder, cone, sphere, hemisphere, torus
from characters import M, character, HEAD, U
from props import prop
from props_v4 import robot
import textures as T


def _eye(n, x, y, z, r=0.03):
    n.add(sphere(r, 10, 8), M("eye_white", "#ffffff"), t=(x, y, z))
    n.add(sphere(r * 0.55, 8, 6), M("eye_black", "#111111"), t=(x, y, z + r * 0.6))


@prop("pets", "Snail (nodes: body, shell, eyestalk_L/R). Common tier")
def pet_snail(stone=False):
    n = Node("pet_snail" if not stone else "pet_snail_stone")
    skin = M("snail_skin" if not stone else "statue_stone", "#9cc46a" if not stone else "#cfc8b8", rough=0.6)
    shell_m = M("snail_shell" if not stone else "statue_stone", "#c47a3a" if not stone else "#cfc8b8", rough=0.5)
    stripe = M("snail_stripe" if not stone else "statue_stone_dark", "#7a4420" if not stone else "#b5ae9e")
    body = n.child("body")
    body.add(box(0.12, 0.07, 0.34), skin, t=(0, 0.035, 0.02))
    body.add(box(0.11, 0.09, 0.09), skin, t=(0, 0.07, 0.17))
    for side, sx in (("L", 1), ("R", -1)):
        st = body.child(f"eyestalk_{side}", t=(sx * 0.03, 0.11, 0.19))
        st.add(cylinder(0.008, 0.08, 6), skin, t=(0, 0.04, 0), r=(-10, 0, -sx * 10))
        if stone:
            st.add(sphere(0.016, 8, 6), skin, t=(sx * 0.008, 0.085, -0.01))
        else:
            _eye(st, sx * 0.008, 0.085, -0.005, 0.018)
    if not stone:
        body.add(box(0.04, 0.008, 0.005), M("snail_mouth", "#2a3a1a"), t=(0, 0.06, 0.216))
    shell = n.child("shell", t=(0, 0.06, -0.04))
    shell.add(transform(cylinder(0.11, 0.1, 18), r=(0, 0, 90)), shell_m, t=(0, 0.08, 0))
    shell.add(transform(torus(0.075, 0.018, 18, 6), r=(0, 0, 90)), stripe, t=(0.052, 0.08, 0))
    shell.add(transform(torus(0.035, 0.014, 14, 6), r=(0, 0, 90)), stripe, t=(0.053, 0.08, 0))
    shell.add(transform(torus(0.075, 0.018, 18, 6), r=(0, 0, 90)), stripe, t=(-0.052, 0.08, 0))
    return n


@prop("pets", "Baby dragon (nodes: wing_L/R, tail, head). Legendary tier")
def pet_dragon():
    n = Node("pet_dragon")
    red = M("dragon_red", "#d8352a", rough=0.5)
    belly = M("dragon_belly", "#ffc45a")
    horn = M("dragon_horn", "#f6ecd2")
    wingm = M("dragon_wing", "#ff7a3a", double=True)
    n.add(box(0.36, 0.34, 0.6), red, t=(0, 0.42, 0))
    n.add(box(0.28, 0.24, 0.02), belly, t=(0, 0.4, 0.3))
    for sx in (-1, 1):
        for sz in (-1, 1):
            n.add(box(0.1, 0.26, 0.1), red, t=(sx * 0.13, 0.13, sz * 0.2))
    head = n.child("head", t=(0, 0.66, 0.32))
    head.add(box(0.3, 0.26, 0.28), red, t=(0, 0.06, 0))
    head.add(box(0.22, 0.14, 0.18), red, t=(0, 0.0, 0.2))
    for sx in (-1, 1):
        head.add(cone(0.035, 0.16, 4), horn, t=(sx * 0.09, 0.26, -0.06), r=(-25, 45, 0))
        _eye(head, sx * 0.08, 0.1, 0.14, 0.035)
        head.add(box(0.03, 0.02, 0.01), M("nostril", "#5a1a10"), t=(sx * 0.05, 0.03, 0.295))
    for side, sx in (("L", 1), ("R", -1)):
        w = n.child(f"wing_{side}", t=(sx * 0.17, 0.55, -0.05))
        w.add(box(0.45, 0.02, 0.3), wingm, t=(sx * 0.22, 0.05, 0), r=(0, 0, sx * 20))
        w.add(box(0.04, 0.04, 0.32), red, t=(sx * 0.2, 0.12, 0), r=(0, 0, sx * 20))
    tail = n.child("tail", t=(0, 0.38, -0.3))
    for k in range(4):
        s = 1 - k * 0.2
        tail.add(box(0.14 * s, 0.12 * s, 0.16), red, t=(0, -0.03 * k, -0.08 - k * 0.15))
    tail.add(cone(0.06, 0.14, 4), M("dragon_tail_tip", "#ffc45a"), t=(0, -0.1, -0.7), r=(-90, 45, 0))
    for k in range(4):
        n.add(cone(0.04, 0.08, 4), belly, t=(0, 0.62, 0.2 - k * 0.14), r=(0, 45, 0))
    return n


@prop("pets", "Wolf (nodes: head, tail, leg_FL/FR/BL/BR). Epic tier")
def pet_wolf():
    n = Node("pet_wolf")
    fur = M("wolf_fur", "#8a93a6", rough=0.9)
    pale = M("wolf_pale", "#e6e9f0", rough=0.9)
    n.add(box(0.32, 0.3, 0.7), fur, t=(0, 0.5, 0))
    n.add(box(0.26, 0.2, 0.3), pale, t=(0, 0.42, 0.22))
    for name, sx, sz in (("FL", 1, 1), ("FR", -1, 1), ("BL", 1, -1), ("BR", -1, -1)):
        lg = n.child(f"leg_{name}", t=(sx * 0.1, 0.38, sz * 0.25))
        lg.add(box(0.1, 0.38, 0.1), fur, t=(0, -0.19, 0))
        lg.add(box(0.11, 0.05, 0.14), pale, t=(0, -0.36, 0.02))
    head = n.child("head", t=(0, 0.72, 0.38))
    head.add(box(0.28, 0.24, 0.26), fur, t=(0, 0, 0))
    head.add(box(0.14, 0.1, 0.18), pale, t=(0, -0.05, 0.2))
    head.add(box(0.05, 0.04, 0.03), M("nose_black", "#111111"), t=(0, -0.01, 0.3))
    for sx in (-1, 1):
        head.add(cone(0.05, 0.14, 4), fur, t=(sx * 0.08, 0.17, -0.04), r=(0, 45, 0))
        _eye(head, sx * 0.07, 0.04, 0.13, 0.03)
    tail = n.child("tail", t=(0, 0.6, -0.35))
    tail.add(box(0.1, 0.1, 0.35), fur, t=(0, 0.06, -0.15), r=(30, 0, 0))
    tail.add(box(0.1, 0.1, 0.1), pale, t=(0, 0.15, -0.32), r=(30, 0, 0))
    return n


@prop("pets", "Owl (nodes: wing_L/R, head). Rare tier")
def pet_owl():
    n = Node("pet_owl")
    br = M("owl_brown", "#8a5a34", rough=0.9)
    cream = M("owl_cream", "#f2e2c0")
    n.add(box(0.26, 0.3, 0.22), br, t=(0, 0.2, 0))
    n.add(box(0.18, 0.2, 0.02), cream, t=(0, 0.18, 0.11))
    head = n.child("head", t=(0, 0.35, 0))
    head.add(box(0.28, 0.18, 0.22), br, t=(0, 0.09, 0))
    for sx in (-1, 1):
        head.add(transform(cylinder(0.055, 0.01, 14), r=(90, 0, 0)), cream, t=(sx * 0.065, 0.1, 0.11))
        head.add(sphere(0.035, 10, 8), M("owl_eye", "#ffcc22"), t=(sx * 0.065, 0.1, 0.115))
        head.add(sphere(0.02, 8, 6), M("eye_black", "#111111"), t=(sx * 0.065, 0.1, 0.14))
        head.add(cone(0.03, 0.07, 4), br, t=(sx * 0.11, 0.2, 0), r=(0, 45, sx * -15))
    head.add(cone(0.02, 0.05, 4), M("beak", "#f2a33a"), t=(0, 0.05, 0.12), r=(90, 45, 0))
    for side, sx in (("L", 1), ("R", -1)):
        w = n.child(f"wing_{side}", t=(sx * 0.14, 0.3, 0))
        w.add(box(0.04, 0.24, 0.18), br, t=(0, -0.11, 0))
    for sx in (-1, 1):
        n.add(box(0.05, 0.04, 0.07), M("beak", "#f2a33a"), t=(sx * 0.06, 0.02, 0.05))
    return n


@prop("pets", "Bunny (Common/Rare filler pet)")
def pet_bunny():
    n = Node("pet_bunny")
    w = M("bunny_white", "#f6f2ee", rough=0.9)
    n.add(box(0.2, 0.18, 0.26), w, t=(0, 0.1, 0))
    head = n.child("head", t=(0, 0.2, 0.12))
    head.add(box(0.17, 0.15, 0.15), w, t=(0, 0.05, 0))
    for sx in (-1, 1):
        head.add(box(0.04, 0.18, 0.02), w, t=(sx * 0.04, 0.2, -0.02))
        head.add(box(0.025, 0.13, 0.005), M("ear_pink", "#ffb0c8"), t=(sx * 0.04, 0.2, -0.008))
        _eye(head, sx * 0.045, 0.07, 0.07, 0.018)
    n.add(sphere(0.04, 8, 6), w, t=(0, 0.12, -0.14))
    return n


@prop("pets", "Cat (Rare filler pet)")
def pet_cat():
    n = Node("pet_cat")
    o = M("cat_orange", "#f08a30", rough=0.9)
    n.add(box(0.18, 0.18, 0.38), o, t=(0, 0.2, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            n.add(box(0.06, 0.12, 0.06), o, t=(sx * 0.06, 0.06, sz * 0.13))
    head = n.child("head", t=(0, 0.32, 0.2))
    head.add(box(0.2, 0.17, 0.16), o)
    for sx in (-1, 1):
        head.add(cone(0.04, 0.08, 4), o, t=(sx * 0.06, 0.12, 0), r=(0, 45, 0))
        _eye(head, sx * 0.05, 0.02, 0.08, 0.022)
    tail = n.child("tail", t=(0, 0.26, -0.19))
    tail.add(box(0.04, 0.3, 0.04), o, t=(0, 0.14, -0.03), r=(-15, 0, 0))
    return n


def _egg(name, base, spot, glow):
    n = Node(name)
    m = Mat(f"{name}_shell", tex=_egg_tex(base, spot), emissive=glow, emissive_strength=0.25)
    bottom = n.child("bottom")
    bottom.add(transform(hemisphere(0.2, 18, 7), r=(180, 0, 0), s=(1, 1.15, 1)), m, t=(0, 0.23, 0))
    top = n.child("top", t=(0, 0.23, 0))
    top.add(transform(hemisphere(0.2, 18, 8), s=(1, 1.45, 1)), m)
    n.extras = {"note": "lift/tilt the 'top' node to crack the egg open"}
    return n


def _egg_tex(base, spot):
    from PIL import Image, ImageDraw
    import random
    rnd = random.Random(hash(base) & 0xffff)
    im = Image.new("RGB", (256, 128), base)
    d = ImageDraw.Draw(im)
    for _ in range(40):
        x, y, r = rnd.randrange(256), rnd.randrange(128), rnd.randint(3, 8)
        d.ellipse([x - r, y - r, x + r, y + r], fill=spot)
    return im


@prop("pets", "Hatching egg, common (grey) - nodes top/bottom")
def egg_common():
    return _egg("egg_common", (215, 210, 200), (160, 155, 145), "#ffffff")


@prop("pets", "Hatching egg, rare (blue)")
def egg_rare():
    return _egg("egg_rare", (110, 170, 240), (60, 110, 200), "#7fc4ff")


@prop("pets", "Hatching egg, epic (purple)")
def egg_epic():
    return _egg("egg_epic", (160, 100, 230), (110, 60, 180), "#c08aff")


@prop("pets", "Hatching egg, legendary (gold)")
def egg_legendary():
    return _egg("egg_legendary", (250, 200, 60), (220, 120, 30), "#ffd060")


@prop("pets", "Founder statue on pedestal - with a tiny stone snail on the shoulder")
def founder_statue():
    n = Node("founder_statue")
    stone = M("statue_stone", "#cfc8b8", rough=1.0)
    n.add(box(1.6, 1.2, 1.6), stone, t=(0, 0.6, 0))
    n.add(box(1.8, 0.15, 1.8), stone, t=(0, 1.27, 0))
    n.add(quad(1.3, 0.55), Mat("plaque_guardian", tex=T.sign("THE STONE GUARDIAN ONLY SEES WHAT MOVES FAST",
                                                            bg=(200, 180, 120), fg=(60, 45, 30), serif=True,
                                                            w=1024, h=420, border=(120, 90, 40))), t=(0, 0.65, 0.805))
    spec = dict(id="founder_stone", skin="#cfc8b8", face="determined", hair="side_part", hair_color="#c4bdac",
                torso_side="#cfc8b8", sleeves="#cfc8b8", pants="#c4bdac", shoes="#b8b1a0", scale=1.5,
                body_acc=[("cape", {"color": "#c4bdac"})])
    hero = character(spec)
    hero.t = (0, 1.345, 0)
    n.attach(hero)
    sn = pet_snail(stone=True)
    sn.t = (0.56, 1.345 + 4 * U * 1.5 - 0.01, 0.0)
    sn.s = (1.3, 1.3, 1.3)
    sn.r = (0, 90, 0)
    n.attach(sn)
    return n


@prop("pets", "Stone Guardian golem (giant). Glow materials 'stone_glow_*' = its 'awake' light")
def stone_guardian():
    g = robot("stone_guardian", "#9a9486", "#b3ad9f", "#ffb030", scale=4.0, fists=2.2, stone=True)
    return g
