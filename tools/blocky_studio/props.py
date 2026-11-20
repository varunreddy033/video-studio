"""Props and set pieces seen in the reference reels. Every builder returns a glb.Node, base at y=0, facing +Z."""
import math
import random

from glb import Node, Mat, transform, box, quad, cylinder, cone, sphere, hemisphere, torus
from characters import M
import textures as T

PROPS = {}   # id -> (builder, category, notes)


def prop(category, notes=""):
    def deco(fn):
        PROPS[fn.__name__] = (fn, category, notes)
        return fn
    return deco


def tex_mat(name, img, **kw):
    return Mat(name, tex=img, **kw)


WOOD = None


def wood_mat(name="wood", base=(150, 95, 55), seed=1):
    return M(name, tex=T.wood(base, seed=seed), rough=0.85)


# =========================================================================== sewing room / school

@prop("sewing_room", "White sewing machine")
def sewing_machine():
    n = Node("sewing_machine")
    w = M("plastic_white", "#f1f1ee", rough=0.4)
    g = M("metal_grey", "#9aa0a6", rough=0.35, metal=0.6)
    n.add(box(0.5, 0.06, 0.24), w, t=(0, 0.03, 0))
    n.add(box(0.12, 0.28, 0.2), w, t=(0.18, 0.2, 0))
    n.add(box(0.48, 0.1, 0.18), w, t=(0.0, 0.36, 0))
    n.add(box(0.08, 0.14, 0.12), w, t=(-0.2, 0.25, 0))
    n.add(cylinder(0.006, 0.08, 6), g, t=(-0.2, 0.14, 0.02))
    n.add(cylinder(0.05, 0.03, 16), g, t=(0.26, 0.3, 0), r=(0, 0, 90))
    n.add(cylinder(0.02, 0.05, 10), M("thread_red", "#d23b3b"), t=(0.05, 0.44, 0))
    n.add(box(0.2, 0.05, 0.005), M("dial_blue", "#4a7bd0"), t=(0.0, 0.36, 0.091))
    return n


@prop("sewing_room", "Antique treadle sewing table (wood + cast-iron legs)")
def sewing_table():
    n = Node("sewing_table")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    iron = M("cast_iron", "#1d1d1d", rough=0.5, metal=0.6)
    n.add(box(1.0, 0.06, 0.5), wd, t=(0, 0.78, 0))
    n.add(box(0.3, 0.2, 0.46), wd, t=(0.33, 0.65, 0))
    for sx in (-1, 1):
        n.add(box(0.04, 0.72, 0.04), iron, t=(sx * 0.45, 0.37, 0.2))
        n.add(box(0.04, 0.72, 0.04), iron, t=(sx * 0.45, 0.37, -0.2))
        n.add(torus(0.12, 0.012, 16, 6), iron, t=(sx * 0.45, 0.32, 0), r=(0, 90, 90))
    n.add(box(0.9, 0.03, 0.03), iron, t=(0, 0.12, 0))
    n.add(box(0.36, 0.03, 0.2), iron, t=(0, 0.06, 0.05))
    return n


@prop("sewing_room", "Dress-form mannequin")
def mannequin():
    n = Node("mannequin")
    fab = M("mannequin_fabric", "#efe6d8")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    n.add(cylinder(0.2, 0.03, 16), wd, t=(0, 0.015, 0))
    n.add(cylinder(0.02, 0.9, 8), wd, t=(0, 0.47, 0))
    n.add(transform(cylinder(0.17, 0.5, 12, r_top=0.2), s=(1, 1, 0.7)), fab, t=(0, 1.15, 0))
    n.add(transform(sphere(0.13, 10, 6), s=(1.4, 0.6, 0.9)), fab, t=(0, 1.42, 0))
    n.add(cylinder(0.03, 0.1, 8), wd, t=(0, 1.52, 0))
    return n


@prop("sewing_room", "Small doll in a pink ball gown")
def doll_pink_dress():
    n = Node("doll_pink_dress")
    pink = M("dress_pink", tex=T.dress_pink())
    skin = M("skin_doll", "#f6d6c0")
    hair = M("hair_blonde", "#f0c860")
    n.add(cone(0.11, 0.18, 12), pink, t=(0, 0.09, 0))
    n.add(box(0.07, 0.07, 0.05), pink, t=(0, 0.2, 0))
    n.add(box(0.07, 0.07, 0.07), skin, t=(0, 0.27, 0))
    n.add(box(0.08, 0.04, 0.08), hair, t=(0, 0.31, 0))
    n.add(box(0.08, 0.1, 0.02), hair, t=(0, 0.25, -0.035))
    for sx in (-1, 1):
        n.add(box(0.02, 0.07, 0.02), skin, t=(sx * 0.05, 0.19, 0))
    return n


@prop("sewing_room", "Yellow measuring tape (extended)")
def tape_measure():
    n = Node("tape_measure")
    n.add(box(0.08, 0.08, 0.04), M("tape_case", "#f2c230"), t=(0, 0.04, 0))
    n.add(box(0.6, 0.004, 0.02), M("tape_yellow", "#ffe066"), t=(0.34, 0.02, 0))
    return n


@prop("sewing_room", "Blue first-aid / bandage box")
def bandage_box():
    n = Node("bandage_box")
    n.add(box(0.25, 0.12, 0.16), M("box_blue", "#2f74d0"), t=(0, 0.06, 0))
    n.add(box(0.06, 0.02, 0.005), M("cross_white", "#ffffff"), t=(0, 0.07, 0.081))
    n.add(box(0.02, 0.06, 0.005), M("cross_white", "#ffffff"), t=(0, 0.07, 0.081))
    return n


@prop("sewing_room", "Fabric roll")
def fabric_roll():
    n = Node("fabric_roll")
    for i, c in enumerate(["#ff9fcf", "#9fd0ff", "#fff09f"]):
        n.add(cylinder(0.07, 0.8, 14), M(f"fabric_{c}", c), t=(0, 0.07, (i - 1) * 0.15), r=(0, 0, 90))
    return n


@prop("school", "Row of 4 school lockers")
def lockers():
    n = Node("lockers")
    teal = M("locker_teal", "#2eb3c7", rough=0.45, metal=0.3)
    dark = M("locker_vent", "#16707e")
    for i in range(4):
        x = (i - 1.5) * 0.42
        n.add(box(0.4, 1.8, 0.45), teal, t=(x, 0.9, 0))
        for k in range(3):
            n.add(box(0.26, 0.02, 0.005), dark, t=(x, 1.55 + k * 0.05, 0.226))
        n.add(box(0.03, 0.12, 0.01), dark, t=(x + 0.13, 1.0, 0.23))
    return n


@prop("school", "Student desk with chair")
def school_desk():
    n = Node("school_desk")
    top = wood_mat("wood_light", (205, 160, 100), 4)
    metal = M("metal_grey", "#9aa0a6", rough=0.35, metal=0.6)
    seat = M("chair_blue", "#2f6fd0")
    n.add(box(0.7, 0.04, 0.5), top, t=(0, 0.72, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            n.add(box(0.03, 0.7, 0.03), metal, t=(sx * 0.32, 0.35, sz * 0.22))
    n.add(box(0.42, 0.04, 0.4), seat, t=(0, 0.45, 0.5))
    n.add(box(0.42, 0.4, 0.04), seat, t=(0, 0.68, 0.7))
    for sx in (-1, 1):
        for sz in (0.32, 0.68):
            n.add(box(0.03, 0.45, 0.03), metal, t=(sx * 0.19, 0.22, sz))
    return n


@prop("school", "Chalkboard with wood frame ('History of Dust')")
def chalkboard():
    n = Node("chalkboard")
    frame = wood_mat("wood_light", (205, 160, 100), 4)
    img = T.chalkboard(["HISTORY OF DUST", "chapter 1: what is dust?", "chapter 2: more dust", "dust + dust = dust"])
    n.add(box(2.6, 1.4, 0.06), frame, t=(0, 1.5, 0))
    n.add(quad(2.45, 1.25), tex_mat("chalkboard_tex", img), t=(0, 1.5, 0.031))
    n.add(box(2.4, 0.04, 0.1), frame, t=(0, 0.83, 0.05))
    return n


@prop("school", "Teacher's wooden desk")
def teacher_desk():
    n = Node("teacher_desk")
    wd = wood_mat("wood_mid", (150, 95, 55), 5)
    n.add(box(1.4, 0.06, 0.7), wd, t=(0, 0.76, 0))
    n.add(box(1.36, 0.7, 0.04), wd, t=(0, 0.38, 0.32))
    for sx in (-1, 1):
        n.add(box(0.04, 0.73, 0.66), wd, t=(sx * 0.68, 0.37, 0))
    return n


@prop("school", "Trophy cup (gold)")
def trophy():
    n = Node("trophy")
    g = M("gold", "#f2c230", rough=0.25, metal=0.8)
    base = M("trophy_base", "#3a2a20")
    n.add(box(0.2, 0.08, 0.2), base, t=(0, 0.04, 0))
    n.add(cylinder(0.03, 0.12, 10), g, t=(0, 0.14, 0))
    n.add(cylinder(0.12, 0.2, 16, r_top=0.15), g, t=(0, 0.3, 0))
    for sx in (-1, 1):
        n.add(torus(0.05, 0.012, 14, 6), g, t=(sx * 0.15, 0.32, 0), r=(90, 0, 0))
    return n


@prop("school", "Front-page newspaper (double-sided flat sheet)")
def newspaper():
    n = Node("newspaper")
    img = T.newspaper("KID SEWS\nDOLL DRESSES!", "EXTRA! SPECIAL EDITION")
    n.add(box(0.42, 0.58, 0.004), M("paper", "#e8e6de"), t=(0, 0.29, 0))
    n.add(quad(0.42, 0.58), tex_mat("newspaper_tex", img), t=(0, 0.29, 0.0025))
    return n


@prop("school", "Wall tear-off calendar (swap page texture: textures/signs/calendar_*.png)")
def calendar():
    n = Node("calendar")
    n.add(box(0.42, 0.42, 0.03), M("calendar_back", "#c2262c"), t=(0, 0.21, 0))
    page = n.child("page", t=(0, 0.2, 0.017))
    page.add(quad(0.38, 0.38), tex_mat("calendar_page", T.calendar_page("NOVEMBER", "DAY 1")))
    page.extras = {"swap_texture_from": "textures/signs/calendar_*.png"}
    return n


@prop("school", "Picture book 'THE SUN' (open)")
def picture_book():
    n = Node("picture_book")
    cover = M("book_cover", "#2a8f6a")
    page_img = T.sign("THE SUN", bg=(250, 245, 230), fg=(240, 150, 30), w=512, h=512)
    n.add(box(0.5, 0.02, 0.34), cover, t=(0, 0.01, 0))
    for sx in (-1, 1):
        n.add(box(0.23, 0.02, 0.32), M("paper_page", "#fbf7ea"), t=(sx * 0.12, 0.03, 0), r=(0, 0, -sx * 6))
    n.add(quad(0.22, 0.3), tex_mat("book_page_tex", page_img), t=(0.12, 0.045, 0), r=(-90, 0, -6))
    return n


# =========================================================================== home

@prop("home", "Bed with pillow and blanket")
def bed():
    n = Node("bed")
    frame = wood_mat("wood_purple", (150, 110, 170), 6)
    n.add(box(1.1, 0.35, 2.1), frame, t=(0, 0.175, 0))
    n.add(box(1.0, 0.15, 2.0), M("mattress", "#f5f5f5"), t=(0, 0.42, 0))
    n.add(box(1.04, 0.08, 1.4), M("blanket_lilac", "#c5a3e0"), t=(0, 0.52, 0.32))
    n.add(box(0.6, 0.12, 0.35), M("pillow", "#ffffff"), t=(0, 0.55, -0.75))
    n.add(box(1.1, 0.8, 0.08), frame, t=(0, 0.4, -1.05))
    return n


@prop("home", "Handheld mirror")
def hand_mirror():
    n = Node("hand_mirror")
    g = M("gold", "#f2c230", rough=0.25, metal=0.8)
    n.add(transform(cylinder(0.12, 0.02, 20), r=(90, 0, 0)), g, t=(0, 0.3, 0))
    n.add(transform(cylinder(0.105, 0.022, 20), r=(90, 0, 0)), M("mirror_glass", "#cfe6f5", rough=0.05, metal=0.1, emissive="#9fc4e0", emissive_strength=0.4),
          t=(0, 0.3, 0.001))
    n.add(box(0.03, 0.2, 0.02), g, t=(0, 0.09, 0))
    return n


@prop("home", "Flashlight with visible light cone (cone is a separate node 'beam')")
def flashlight():
    n = Node("flashlight")
    n.add(transform(cylinder(0.025, 0.2, 12), r=(90, 0, 0)), M("flashlight_body", "#2a2a2a", metal=0.4), t=(0, 0, 0))
    n.add(transform(cylinder(0.04, 0.05, 12, r_top=0.026), r=(90, 0, 0)), M("flashlight_head", "#3a3a3a"), t=(0, 0, 0.12))
    beam = n.child("beam", t=(0, 0, 0.14))
    beam.add(transform(cone(0.45, 2.0, 20), r=(-90, 0, 0)), M("light_beam", "#fff6c8", alpha=0.25,
             emissive="#fff6c8", double=True, unlit=True), t=(0, 0, 1.0))
    n.add(transform(cylinder(0.036, 0.004, 12), r=(90, 0, 0)), M("bulb", "#ffffff", emissive="#fff3b0",
          emissive_strength=4), t=(0, 0, 0.146))
    return n


@prop("home", "Window with frame (night-lit variant via textures/surfaces/window_lit.png)")
def window():
    n = Node("window")
    f = M("frame_white", "#ffffff")
    n.add(box(1.0, 1.2, 0.08), f, t=(0, 0.6, 0))
    n.add(quad(0.9, 1.1), tex_mat("window_glass", T.window_grid(cols=2, rows=2)), t=(0, 0.6, 0.041))
    n.add(box(1.1, 0.06, 0.16), f, t=(0, 0.0, 0.05))
    for sx in (-1, 1):
        n.add(box(0.2, 1.2, 0.03), M("shutter_blue", "#2c4fb0"), t=(sx * 0.62, 0.6, 0.02))
    return n


@prop("home", "Sun-to-storm mood dial (wall gauge)")
def mood_dial():
    n = Node("mood_dial")
    n.add(transform(cylinder(0.5, 0.06, 32), r=(90, 0, 0)), M("gold_frame", "#f0b630", metal=0.6, rough=0.3), t=(0, 0.5, 0))
    n.add(transform(cylinder(0.44, 0.005, 32), r=(90, 0, 0)), tex_mat("dial_face", T.mood_dial()), t=(0, 0.5, 0.032))
    needle = n.child("needle", t=(0, 0.5, 0.045))
    needle.add(box(0.03, 0.36, 0.01), M("needle_red", "#d42020"), t=(0, 0.18, 0))
    needle.extras = {"rotate_z_to_set_mood": "0 = up, +90 = sunny side, -90 = storm side"}
    return n


@prop("home", "Glass of lemonade with straw")
def lemonade():
    n = Node("lemonade")
    n.add(cylinder(0.04, 0.12, 14), M("glass", "#e8f6ff", alpha=0.45, rough=0.05), t=(0, 0.06, 0))
    n.add(cylinder(0.036, 0.08, 14), M("lemonade", "#fff07a", alpha=0.8), t=(0, 0.045, 0))
    n.add(cylinder(0.004, 0.18, 6), M("straw_pink", "#ff6fae"), t=(0.01, 0.12, 0), r=(0, 0, -10))
    n.add(transform(cylinder(0.025, 0.006, 12), r=(90, 0, 0)), M("lemon", "#ffe14a"), t=(0.04, 0.12, 0.0))
    return n


# =========================================================================== town / exterior

@prop("town", "Round cartoon tree")
def tree_round():
    n = Node("tree_round")
    n.add(cylinder(0.18, 1.6, 10), M("bark", "#7a4a2a"), t=(0, 0.8, 0))
    leaf = M("leaves", "#5cb54a", rough=0.9)
    n.add(sphere(1.0, 14, 10), leaf, t=(0, 2.2, 0))
    n.add(sphere(0.7, 12, 8), leaf, t=(0.6, 1.9, 0.3))
    n.add(sphere(0.7, 12, 8), leaf, t=(-0.6, 2.0, -0.2))
    return n


@prop("town", "Round bush")
def bush():
    n = Node("bush")
    leaf = M("leaves", "#5cb54a", rough=0.9)
    n.add(hemisphere(0.5, 12, 5), leaf, t=(0, 0, 0))
    n.add(hemisphere(0.35, 12, 5), leaf, t=(0.4, 0, 0.1))
    return n


@prop("town", "Street lamp (emissive bulb)")
def street_lamp():
    n = Node("street_lamp")
    pole = M("lamp_pole", "#2a2d33", metal=0.5, rough=0.4)
    n.add(cylinder(0.12, 0.2, 10), pole, t=(0, 0.1, 0))
    n.add(cylinder(0.05, 3.6, 10), pole, t=(0, 1.9, 0))
    n.add(cylinder(0.2, 0.2, 10, r_top=0.08), pole, t=(0, 3.85, 0))
    n.add(sphere(0.15, 10, 8), M("lamp_bulb", "#fff2c0", emissive="#ffe08a", emissive_strength=6), t=(0, 3.68, 0))
    return n


@prop("town", "String of fairy lights (6 m, sagging)")
def string_lights():
    n = Node("string_lights")
    wire = M("wire", "#222222")
    cols = ["#ffd75e", "#ff6fae", "#7fd7ff", "#a0ff8a", "#ffb35e"]
    L = 6.0
    for i in range(24):
        x0 = -L / 2 + L * i / 24
        x1 = -L / 2 + L * (i + 1) / 24
        y0 = -0.6 * (1 - ((x0 / (L / 2)) ** 2))
        y1 = -0.6 * (1 - ((x1 / (L / 2)) ** 2))
        ln = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        n.add(box(ln, 0.01, 0.01), wire, t=((x0 + x1) / 2, (y0 + y1) / 2, 0), r=(0, 0, ang))
        if i % 2 == 0:
            c = cols[(i // 2) % len(cols)]
            n.add(sphere(0.045, 8, 6), M(f"bulb_{c}", c, emissive=c, emissive_strength=5), t=(x0, y0 - 0.06, 0))
    return n


@prop("town", "Wooden park bench")
def bench():
    n = Node("bench")
    wd = wood_mat("wood_mid", (150, 95, 55), 5)
    iron = M("cast_iron", "#1d1d1d", rough=0.5, metal=0.6)
    for k in range(3):
        n.add(box(1.6, 0.04, 0.12), wd, t=(0, 0.45, -0.15 + k * 0.14))
    for k in range(2):
        n.add(box(1.6, 0.1, 0.03), wd, t=(0, 0.65 + k * 0.14, -0.25), r=(-10, 0, 0))
    for sx in (-1, 1):
        n.add(box(0.05, 0.45, 0.4), iron, t=(sx * 0.7, 0.22, 0))
        n.add(box(0.05, 0.4, 0.05), iron, t=(sx * 0.7, 0.65, -0.24))
    return n


@prop("town", "White picket fence segment (2 m)")
def picket_fence():
    n = Node("picket_fence")
    w = M("paint_white", "#f7f7f7")
    for i in range(10):
        x = -0.9 + i * 0.2
        n.add(box(0.1, 0.8, 0.03), w, t=(x, 0.4, 0))
        n.add(transform(cone(0.07, 0.08, 4), r=(0, 45, 0)), w, t=(x, 0.84, 0), s=(1, 1, 0.3))
    for y in (0.25, 0.6):
        n.add(box(2.0, 0.07, 0.03), w, t=(0, y, -0.03))
    return n


@prop("town", "Fountain for the town plaza")
def fountain():
    n = Node("fountain")
    stone = M("stone_light", "#d8d4c8")
    water = M("water", "#4aa8e8", alpha=0.85, rough=0.05)
    n.add(cylinder(1.8, 0.5, 28), stone, t=(0, 0.25, 0))
    n.add(cylinder(1.6, 0.05, 28), water, t=(0, 0.46, 0))
    n.add(cylinder(0.2, 1.2, 12), stone, t=(0, 0.9, 0))
    n.add(cylinder(0.7, 0.15, 20, r_top=0.8), stone, t=(0, 1.5, 0))
    n.add(cylinder(0.65, 0.04, 20), water, t=(0, 1.57, 0))
    n.add(cylinder(0.1, 0.4, 10), stone, t=(0, 1.75, 0))
    n.add(cone(0.15, 0.4, 10), M("water_spout", "#bfe6ff", alpha=0.7, emissive="#bfe6ff", emissive_strength=0.3), t=(0, 2.1, 0))
    return n


@prop("town", "Compact car (pink / swap color material 'car_paint')")
def car():
    n = Node("car")
    paint = M("car_paint", "#f07ab0", rough=0.3, metal=0.3)
    glass = M("car_glass", "#9fd3f0", rough=0.05, alpha=0.8)
    tire = M("tire", "#1a1a1a")
    n.add(box(1.8, 0.55, 3.6), paint, t=(0, 0.6, 0))
    n.add(box(1.6, 0.55, 1.9), paint, t=(0, 1.15, -0.2))
    n.add(box(1.62, 0.42, 1.7), glass, t=(0, 1.15, -0.2))
    for sx in (-1, 1):
        for sz in (-1.15, 1.15):
            n.add(transform(cylinder(0.35, 0.25, 16), r=(0, 0, 90)), tire, t=(sx * 0.85, 0.35, sz))
        n.add(sphere(0.1, 8, 6), M("headlight", "#ffffff", emissive="#fff7c8", emissive_strength=3), t=(sx * 0.6, 0.65, 1.8))
        n.add(box(0.25, 0.12, 0.02), M("taillight", "#e02020", emissive="#e02020", emissive_strength=2), t=(sx * 0.6, 0.7, -1.81))
    return n


def _house(name, wall=(225, 225, 230), roof="#3a3f55", door="#c0282a", w=6.0, d=5.0, floors=2, lit=False):
    n = Node(name)
    wall_m = Mat(f"{name}_siding", tex=T.siding(wall))
    roof_m = M(f"roof_{roof}", roof, rough=0.9)
    trim = M("frame_white", "#ffffff")
    fh = 1.8
    H = fh * floors
    n.add(box(w, H, d), wall_m, t=(0, H / 2, 0))
    # gable roof from two slanted slabs
    ang = 32
    half = (w / 2) / math.cos(math.radians(ang))
    for sx in (-1, 1):
        n.add(box(half + 0.3, 0.12, d + 0.4), roof_m, t=(sx * w / 4, H + (w / 4) * math.tan(math.radians(ang)), 0),
              r=(0, 0, -sx * ang))
    # gable walls (triangles approximated by stacked boxes)
    rise = (w / 2) * math.tan(math.radians(ang))
    for k in range(6):
        hh = rise / 6
        ww = w * (1 - (k + 0.5) / 6)
        n.add(box(ww, hh, d - 0.05), wall_m, t=(0, H + hh * (k + 0.5), 0))
    win = Mat(f"window_{'lit' if lit else 'day'}", tex=T.window_grid(cols=3, rows=2, lit=lit),
              emissive="#ffd890" if lit else None, emissive_strength=1.5 if lit else 1.0)
    for f in range(floors):
        y = f * fh + fh * 0.55
        for x in (-w * 0.3, w * 0.3) if f == 0 else (-w * 0.3, 0, w * 0.3):
            n.add(box(1.2, 0.9, 0.08), trim, t=(x, y, d / 2 + 0.02))
            n.add(quad(1.05, 0.78), win, t=(x, y, d / 2 + 0.065))
            n.add(box(0.25, 0.95, 0.04), M("shutter_dark", "#1e2a44"), t=(x - 0.75, y, d / 2 + 0.03))
            n.add(box(0.25, 0.95, 0.04), M("shutter_dark", "#1e2a44"), t=(x + 0.75, y, d / 2 + 0.03))
    n.add(box(0.9, 1.6, 0.08), M(f"door_{door}", door), t=(0, 0.8, d / 2 + 0.03))
    n.add(sphere(0.05, 6, 4), M("gold", "#f2c230", rough=0.25, metal=0.8), t=(0.3, 0.8, d / 2 + 0.09))
    n.add(box(1.8, 0.1, 1.0), trim, t=(0, 2.0, d / 2 + 0.5))  # porch roof
    for sx in (-1, 1):
        n.add(box(0.1, 2.0, 0.1), trim, t=(sx * 0.85, 1.0, d / 2 + 0.95))
    n.add(box(1.8, 0.15, 1.0), M("step_grey", "#9a9a9a"), t=(0, 0.075, d / 2 + 0.5))
    return n


@prop("town", "Two-storey suburban house, white siding, blue roof")
def house_white():
    return _house("house_white", (232, 232, 236), "#3a3f55", "#c0282a")


@prop("town", "Two-storey house, pink siding")
def house_pink():
    return _house("house_pink", (245, 185, 205), "#8a4a64", "#ffffff")


@prop("town", "Two-storey house, sage green siding (sunrise house)")
def house_green():
    return _house("house_green", (150, 175, 130), "#2d3550", "#c0282a")


@prop("town", "Two-storey house, navy siding with lit windows (night)")
def house_navy_night():
    return _house("house_navy_night", (60, 80, 140), "#1f2438", "#e0b040", lit=True)


@prop("town", "One-storey grey house (rainy scenes)")
def house_grey_small():
    return _house("house_grey_small", (185, 185, 195), "#4a4a58", "#5a5a6a", floors=1)


def _shop(name, label, color, awning="#ffffff"):
    n = Node(name)
    body = M(f"shopwall_{color}", color, rough=0.8)
    n.add(box(4.0, 3.2, 3.0), body, t=(0, 1.6, 0))
    n.add(box(4.2, 0.2, 3.2), M("roof_trim", "#e8e8e8"), t=(0, 3.3, 0))
    n.add(quad(3.2, 0.6), Mat(f"sign_{name}", tex=T.sign(label, bg=(20, 30, 70), fg=(255, 255, 255)),
                              emissive="#ffffff", emissive_strength=0.6), t=(0, 2.75, 1.52))
    n.add(box(3.4, 0.6, 0.06), M("sign_board", "#141c40"), t=(0, 2.75, 1.48))
    n.add(quad(1.2, 1.2), Mat("shop_window_lit", tex=T.window_grid(cols=2, rows=2, lit=True), emissive="#ffd890",
                              emissive_strength=1.2), t=(-1.1, 1.3, 1.51))
    n.add(box(0.9, 1.9, 0.06), M("shop_door", "#1e1e24"), t=(0.9, 0.95, 1.5))
    n.add(transform(box(3.8, 0.06, 0.8), r=(25, 0, 0)), M(f"awning_{awning}", awning, double=True), t=(0, 2.25, 1.85))
    return n


@prop("town", "Shop: LAMPS & BULBS (blue)")
def shop_lamps():
    return _shop("shop_lamps", "LAMPS & BULBS", "#2c5fd4")


@prop("town", "Shop: MUSHROOMS (teal)")
def shop_mushrooms():
    return _shop("shop_mushrooms", "MUSHROOMS", "#1f7a74")


@prop("town", "Shop: CAFE (white)")
def shop_cafe():
    return _shop("shop_cafe", "Cafe~", "#e9e9ee", awning="#9ad0c8")


@prop("town", "Shop: blank sign (retexture 'sign_shop_blank')")
def shop_blank():
    return _shop("shop_blank", "SHOP", "#d06a3a")


@prop("town", "Power plant with two striped chimneys + glowing windows")
def power_plant():
    n = Node("power_plant")
    wall = M("plant_wall", "#c9ccd6")
    n.add(box(10, 3.5, 6), wall, t=(0, 1.75, 0))
    n.add(box(10.2, 0.25, 6.2), M("plant_roof", "#8a8f9c"), t=(0, 3.6, 0))
    for x in (-2.5, 2.5):
        for k in range(4):
            c = "#ffffff" if k % 2 == 0 else "#d23030"
            n.add(cylinder(0.55, 2.0, 16), M(f"chimney_{c}", c), t=(x, 4.6 + k * 2.0, -1.0))
    win = Mat("plant_window", "#ffffff", emissive="#e8f4ff", emissive_strength=2.5)
    for i in range(7):
        n.add(box(0.9, 0.7, 0.05), win, t=(-4.0 + i * 1.33, 1.4, 3.02))
    n.add(quad(4.0, 0.6), Mat("sign_power_plant", tex=T.sign("POWER PLANT", bg=(20, 30, 90), fg=(250, 220, 60)),
                              emissive="#ffffff", emissive_strength=0.8), t=(0, 2.8, 3.03))
    n.add(box(0.8, 1.0, 0.6), M("transformer_grey", "#7c818c"), t=(4.3, 0.5, 3.4))
    return n


@prop("town", "Cafeteria / school entrance doorway with sign")
def school_entrance():
    n = Node("school_entrance")
    n.add(box(6, 3.6, 0.4), M("school_wall", "#e4e8ee"), t=(0, 1.8, 0))
    n.add(box(2.2, 2.6, 0.45), M("door_frame_navy", "#1d3260"), t=(0, 1.3, 0))
    n.add(box(1.9, 2.4, 0.47), M("door_dark", "#0e1424"), t=(0, 1.2, 0))
    n.add(quad(2.8, 0.55), Mat("sign_cafeteria", tex=T.sign("CAFETERIA", bg=(250, 210, 40), fg=(30, 50, 120))),
          t=(0, 3.0, 0.22))
    return n


# =========================================================================== nature / sky

@prop("nature", "Glowing mushroom (emissive cap, swap color on 'mushroom_cap_*')")
def glow_mushroom():
    n = Node("glow_mushroom")
    n.add(cylinder(0.09, 0.6, 10, r_top=0.07), M("mushroom_stem", "#fff7ef", emissive="#fff3e8", emissive_strength=0.6),
          t=(0, 0.3, 0))
    n.add(hemisphere(0.35, 16, 6, squash=0.55), M("mushroom_cap_pink", "#ffc2f0", emissive="#ff9be8",
                                                  emissive_strength=2.0), t=(0, 0.58, 0))
    return n


@prop("nature", "Cluster of glowing mushrooms (pink / white / cyan)")
def mushroom_field():
    n = Node("mushroom_field")
    rnd = random.Random(8)
    caps = [("#ffc2f0", "#ff9be8"), ("#ffffff", "#e8f2ff"), ("#bff4ff", "#7fe6ff")]
    stem = M("mushroom_stem", "#fff7ef", emissive="#fff3e8", emissive_strength=0.6)
    for i in range(18):
        x, z = rnd.uniform(-2.5, 2.5), rnd.uniform(-2.5, 2.5)
        s = rnd.uniform(0.5, 1.4)
        c, e = caps[i % 3]
        n.add(cylinder(0.08 * s, 0.5 * s, 8, r_top=0.06 * s), stem, t=(x, 0.25 * s, z))
        n.add(hemisphere(0.3 * s, 12, 5, squash=0.55), M(f"mushroom_cap_{c}", c, emissive=e, emissive_strength=2.0),
              t=(x, 0.48 * s, z))
    n.add(box(6, 0.05, 6), M("soil", "#6b4a33"), t=(0, 0.025, 0))
    return n


@prop("nature", "Puffy cartoon cloud (sunset-tinted variant via material color)")
def cloud():
    n = Node("cloud")
    m = M("cloud_white", "#fff6ee", rough=1.0)
    for x, y, r in ((0, 0, 1.0), (1.0, -0.15, 0.75), (-1.0, -0.2, 0.7), (0.5, 0.35, 0.7), (-0.4, 0.3, 0.6)):
        n.add(sphere(r, 14, 10, squash=0.7), m, t=(x, y + 1.0, 0))
    return n


@prop("nature", "Storm cloud (dark)")
def storm_cloud():
    n = cloud()
    n.name = "storm_cloud"
    for mname in list(n.prims):
        mat, gs = n.prims.pop(mname)
        n.prims["cloud_storm"] = (M("cloud_storm", "#3b3f4e", rough=1.0), gs)
    return n


@prop("nature", "Sun disc (emissive)")
def sun():
    n = Node("sun")
    n.add(sphere(2.0, 20, 14), M("sun_core", "#fff3b0", emissive="#ffd860", emissive_strength=8, unlit=True), t=(0, 2, 0))
    return n


@prop("nature", "Full moon (emissive)")
def moon():
    n = Node("moon")
    n.add(sphere(1.5, 20, 14), M("moon_surface", "#e9eefc", emissive="#cfd9ff", emissive_strength=3), t=(0, 1.5, 0))
    return n


@prop("nature", "Lightning bolt (emissive, flat zig-zag)")
def lightning_bolt():
    n = Node("lightning_bolt")
    m = M("lightning", "#cdeeff", emissive="#9fe0ff", emissive_strength=10, unlit=True)
    pts = [(0, 8), (-0.8, 5.5), (0.4, 5.0), (-0.6, 2.4), (0.5, 1.9), (0, 0)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        ln = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        n.add(box(ln + 0.15, 0.25, 0.1), m, t=((x0 + x1) / 2, (y0 + y1) / 2, 0), r=(0, 0, ang))
    return n


@prop("nature", "Rock / boulder")
def rock():
    n = Node("rock")
    m = M("rock_grey", "#6f7480", rough=1.0)
    n.add(transform(sphere(0.6, 6, 4), s=(1.2, 0.7, 1.0)), m, t=(0, 0.3, 0))
    n.add(transform(sphere(0.35, 6, 4), s=(1, 0.8, 1)), m, t=(0.6, 0.2, 0.2))
    return n


@prop("nature", "Mountain peak (climbable, low-poly)")
def mountain():
    n = Node("mountain")
    n.add(cone(14, 18, 9), M("mountain_rock", "#4a4f5c", rough=1.0), t=(0, 9, 0))
    n.add(cone(4.4, 5.6, 9), M("snow", "#f4f6fb"), t=(0, 15.25, 0))
    return n


@prop("nature", "Ground tile 10x10 m grass")
def ground_grass():
    n = Node("ground_grass")
    g = T.grass()
    n.add(box(10, 0.1, 10, faces=("top",)), Mat("grass_tile", tex=g), t=(0, 0, 0))
    return n


@prop("town", "Road tile 8x8 m with centre dashes")
def road_tile():
    n = Node("road_tile")
    n.add(box(8, 0.1, 8, faces=("top",)), Mat("road_tex", tex=T.road()), t=(0, 0.0, 0))
    return n


@prop("town", "Sidewalk tile 2x8 m with curb")
def sidewalk():
    n = Node("sidewalk")
    n.add(box(2, 0.15, 8), Mat("sidewalk_tex", tex=T.tiles((210, 210, 214), (195, 195, 200), 2)), t=(0, 0.075, 0))
    return n


@prop("town", "Cobblestone plaza tile 8x8 m")
def plaza_tile():
    n = Node("plaza_tile")
    n.add(box(8, 0.1, 8, faces=("top",)), Mat("cobble_tex", tex=T.cobble()), t=(0, 0.0, 0))
    return n


# =========================================================================== stage / event

@prop("event", "Stage platform with purple backdrop and title")
def stage():
    n = Node("stage")
    n.add(box(8, 0.8, 4), M("stage_floor", "#2a1b3d"), t=(0, 0.4, 0))
    n.add(box(8, 4.5, 0.2), Mat("stage_backdrop", tex=T.sign("COSTUME CONTEST", bg=(120, 30, 140), fg=(255, 220, 245)),
                                emissive="#ffffff", emissive_strength=0.3), t=(0, 3.05, -2.0))
    for sx in (-1, 1):
        n.add(box(0.4, 4.5, 0.4), M("stage_pillar", "#d6b04a", metal=0.6, rough=0.3), t=(sx * 3.8, 3.05, -1.8))
    return n


@prop("event", "Audience bleacher (3 rows, seat crowd characters on it)")
def bleachers():
    n = Node("bleachers")
    m = M("bleacher_blue", "#3b4c8a")
    for k in range(3):
        n.add(box(8, 0.45, 0.8), m, t=(0, 0.225 + k * 0.45, -k * 0.8), s=(1, 1 + k * 1.0, 1))
    return n


@prop("event", "Microphone on stand")
def microphone():
    n = Node("microphone")
    blk = M("mic_black", "#141414", metal=0.5)
    n.add(cylinder(0.18, 0.03, 14), blk, t=(0, 0.015, 0))
    n.add(cylinder(0.015, 1.5, 8), blk, t=(0, 0.77, 0))
    n.add(sphere(0.05, 10, 8), M("mic_grille", "#9aa0a6", metal=0.8), t=(0, 1.57, 0.02))
    return n


@prop("fx", "Rain sheet (alpha plane, scroll the UVs downward to animate)")
def rain_sheet():
    n = Node("rain_sheet")
    n.add(quad(10, 10), Mat("rain", tex=T.rain_streaks(), double=True, unlit=True), t=(0, 5, 0))
    return n


@prop("fx", "Speech bubble 'GOOD MORNING!'")
def speech_bubble():
    n = Node("speech_bubble")
    n.add(quad(1.0, 0.5), Mat("bubble_good_morning", tex=T.speech_bubble("GOOD MORNING!"), double=True, unlit=True),
          t=(0, 0.25, 0))
    return n


@prop("fx", "Sun ray burst (god rays, additive)")
def sun_rays():
    n = Node("sun_rays")
    m = M("ray", "#fff2b0", alpha=0.25, emissive="#fff2b0", emissive_strength=2, double=True, unlit=True)
    for i in range(10):
        a = -60 + i * 13
        n.add(box(0.35, 12, 0.01), m, t=(math.sin(math.radians(a)) * 6, math.cos(math.radians(a)) * 6, 0), r=(0, 0, -a))
    return n
