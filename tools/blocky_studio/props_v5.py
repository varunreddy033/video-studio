"""Videos 5-7: house interior (family comedy), classroom romance, school crush (hallway, cafeteria, library)."""
import math

from glb import Node, Mat, transform, box, quad, cylinder, cone, sphere, hemisphere, torus
from characters import M
from props import prop, tex_mat, wood_mat
import textures as T


# =========================================================================== house interior

@prop("interior", "White six-panel interior door with frame and knob (pivot node 'door' at hinge)")
def interior_door():
    n = Node("interior_door")
    w = M("paint_white", "#f7f7f7")
    n.add(box(0.1, 2.15, 0.16), w, t=(-0.5, 1.075, 0))
    n.add(box(0.1, 2.15, 0.16), w, t=(0.5, 1.075, 0))
    n.add(box(1.1, 0.1, 0.16), w, t=(0, 2.2, 0))
    door = n.child("door", t=(-0.45, 0, 0))
    door.add(box(0.9, 2.1, 0.05), w, t=(0.45, 1.05, 0))
    panel = M("door_panel_shadow", "#e4e4e4")
    for row, (y, h) in enumerate(((1.75, 0.5), (1.05, 0.7), (0.35, 0.5))):
        for x in (0.25, 0.65):
            door.add(box(0.3, h, 0.01), panel, t=(x, y, 0.03))
    door.add(sphere(0.04, 8, 6), M("brass", "#c8a24a", metal=0.8, rough=0.3), t=(0.82, 1.0, 0.06))
    return n


@prop("interior", "Front door with tall glass side-panes (dark grey, letter slot)")
def front_door():
    n = Node("front_door")
    g = M("door_charcoal", "#3a3f48")
    n.add(box(1.0, 2.2, 0.08), g, t=(0, 1.1, 0))
    for x in (-0.18, 0.18):
        n.add(box(0.16, 1.2, 0.01), M("door_glass", "#9fb8c8", rough=0.05, metal=0.3), t=(x, 1.35, 0.045))
    n.add(box(0.3, 0.05, 0.02), M("brass", "#c8a24a", metal=0.8, rough=0.3), t=(0, 0.6, 0.05))
    n.add(box(0.03, 0.3, 0.05), M("handle_steel", "#bfc4c8", metal=0.9, rough=0.2), t=(0.4, 1.05, 0.07))
    n.add(box(1.2, 0.1, 0.12), M("paint_white", "#f7f7f7"), t=(0, 2.25, 0))
    return n


@prop("interior", "Straight staircase with white balusters and wood rail (rises along -Z)")
def staircase():
    n = Node("staircase")
    tread = wood_mat("wood_dark", (110, 65, 40), 2)
    riser = M("paint_white", "#f7f7f7")
    steps, rise, run = 14, 0.19, 0.27
    for i in range(steps):
        y = (i + 1) * rise
        n.add(box(1.1, 0.04, run + 0.03), tread, t=(0, y, -i * run))
        n.add(box(1.1, rise, 0.02), riser, t=(0, y - rise / 2, -i * run + run / 2))
        n.add(box(0.03, 0.85, 0.03), riser, t=(0.53, y + 0.42, -i * run))
    length = math.hypot(steps * rise, steps * run)
    ang = math.degrees(math.atan2(steps * rise, steps * run))
    n.add(box(0.07, 0.06, length), tread, t=(0.53, steps * rise / 2 + 0.88, -steps * run / 2 + run / 2), r=(ang, 0, 0))
    n.add(box(0.1, 1.2, 0.1), tread, t=(0.53, 0.6, run / 2))
    return n


@prop("interior", "Tall window with tied-back brown curtains and rod")
def curtained_window():
    n = Node("curtained_window")
    n.add(box(1.3, 2.0, 0.06), M("paint_white", "#f7f7f7"), t=(0, 1.5, 0))
    n.add(quad(1.2, 1.9), tex_mat("window_glass", T.window_grid(cols=3, rows=4)), t=(0, 1.5, 0.031))
    cur = M("curtain_brown", "#8a6a48", double=True)
    for sx in (-1, 1):
        n.add(transform(cylinder(0.2, 2.6, 8, r_top=0.14), s=(1, 1, 0.4)), cur, t=(sx * 0.82, 1.4, 0.12))
    n.add(transform(cylinder(0.02, 2.2, 8), r=(0, 0, 90)), M("brass", "#c8a24a", metal=0.8, rough=0.3), t=(0, 2.72, 0.14))
    return n


@prop("interior", "Wall sconce lamp (brass arm, glowing shade)")
def wall_sconce():
    n = Node("wall_sconce")
    b = M("brass", "#c8a24a", metal=0.8, rough=0.3)
    n.add(box(0.1, 0.18, 0.03), b, t=(0, 0, 0))
    n.add(torus(0.08, 0.012, 14, 6), b, t=(0, 0.02, 0.08), r=(0, 90, 0))
    n.add(cylinder(0.07, 0.14, 12, r_top=0.05), M("sconce_glass", "#fff4dc", emissive="#ffe8b0", emissive_strength=2),
          t=(0, 0.16, 0.12))
    return n


@prop("interior", "Side table with green table lamp")
def side_table_lamp():
    n = Node("side_table_lamp")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    n.add(box(0.9, 0.7, 0.45), wd, t=(0, 0.35, 0))
    n.add(cylinder(0.08, 0.3, 10, r_top=0.05), M("lamp_jade", "#4aa88a"), t=(0, 0.85, 0))
    n.add(cylinder(0.2, 0.22, 14, r_top=0.12), M("lampshade", "#f6efdc", emissive="#ffe8b0", emissive_strength=1.2),
          t=(0, 1.1, 0))
    return n


@prop("interior", "Hardwood floor tile 6x6 m")
def hardwood_floor():
    n = Node("hardwood_floor")
    n.add(box(6, 0.05, 6, faces=("top",)), Mat("hardwood_tex", tex=T.wood((120, 50, 30), seed=9, planks=8)))
    return n


@prop("interior", "Gift card / payment card (gold)")
def gift_card():
    n = Node("gift_card")
    n.add(box(0.09, 0.055, 0.004), M("card_gold", "#e8b93a", metal=0.5, rough=0.3), t=(0, 0.03, 0))
    n.add(box(0.07, 0.008, 0.001), M("card_stripe", "#7a5a10"), t=(0, 0.04, 0.0025))
    return n


@prop("interior", "Stack of cash bills")
def cash_stack():
    n = Node("cash_stack")
    m = Mat("cash_tex", tex=T.cash_bills())
    for i in range(6):
        n.add(box(0.16, 0.008, 0.07), m, t=(0, 0.004 + i * 0.009, 0), r=(0, (i % 3 - 1) * 4, 0))
    n.add(box(0.03, 0.06, 0.072), M("band_paper", "#f2e6c0"), t=(0, 0.03, 0))
    return n


# =========================================================================== classroom romance

@prop("classroom", "Wooden student desk + chair (cream metal legs)")
def wood_desk():
    n = Node("wood_desk")
    top = wood_mat("wood_mid", (150, 95, 55), 5)
    leg = M("metal_cream", "#e9e2d0", metal=0.4, rough=0.4)
    n.add(box(0.75, 0.05, 0.5), top, t=(0, 0.74, 0))
    n.add(box(0.7, 0.12, 0.45), top, t=(0, 0.65, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            n.add(box(0.04, 0.6, 0.04), leg, t=(sx * 0.33, 0.3, sz * 0.2))
    n.add(box(0.45, 0.04, 0.42), top, t=(0, 0.45, 0.55))
    n.add(box(0.45, 0.35, 0.04), top, t=(0, 0.72, 0.76))
    for sx in (-1, 1):
        for sz in (0.36, 0.74):
            n.add(box(0.03, 0.45, 0.03), leg, t=(sx * 0.2, 0.22, sz))
    return n


@prop("classroom", "Smartphone (screen node 'screen' - swap textures/signs/phone_*.png)")
def smartphone():
    n = Node("smartphone")
    n.add(box(0.075, 0.155, 0.009), M("phone_body", "#1e1e22", metal=0.4, rough=0.2), t=(0, 0.0775, 0))
    s = n.child("screen", t=(0, 0.0775, 0.0047))
    s.add(quad(0.068, 0.145), Mat("phone_screen", tex=T.phone_chat(), emissive="#ffffff", emissive_strength=0.8))
    return n


@prop("classroom", "Pink sticky note 'practice # 555-0143 text me'")
def sticky_note():
    n = Node("sticky_note")
    n.add(box(0.1, 0.1, 0.002), Mat("sticky_tex", tex=T.sticky_note()), t=(0, 0.05, 0))
    n.add(quad(0.1, 0.1), Mat("sticky_tex", tex=T.sticky_note()), t=(0, 0.05, 0.0012))
    return n


@prop("classroom", "Pink chocolate gift box with yellow ribbon")
def chocolate_box():
    n = Node("chocolate_box")
    n.add(box(0.3, 0.1, 0.22), M("gift_pink", "#ff6fae"), t=(0, 0.05, 0))
    rib = M("ribbon_yellow", "#ffd84a")
    n.add(box(0.31, 0.102, 0.03), rib, t=(0, 0.05, 0))
    n.add(box(0.03, 0.102, 0.23), rib, t=(0, 0.05, 0))
    for sx in (-1, 1):
        n.add(torus(0.035, 0.01, 12, 6), rib, t=(sx * 0.035, 0.11, 0), r=(90, 0, sx * 30))
    return n


@prop("classroom", "Striped popcorn bucket")
def popcorn_bucket():
    n = Node("popcorn_bucket")
    n.add(cylinder(0.07, 0.18, 12, r_top=0.09), Mat("popcorn_stripes", tex=T.stripes((240, 240, 240), (210, 40, 40), 6,
                                                                                    vertical=True)), t=(0, 0.09, 0))
    for i in range(10):
        a = i * 0.63
        n.add(sphere(0.025, 6, 4), M("popcorn", "#fff2c8"), t=(math.cos(a) * 0.05, 0.19 + (i % 3) * 0.015, math.sin(a) * 0.05))
    return n


@prop("classroom", "'NO PHONES IN CLASS' wall sign")
def sign_no_phones():
    n = Node("sign_no_phones")
    n.add(quad(0.6, 0.4), Mat("no_phones_tex", tex=T.sign("NO PHONES IN CLASS", bg=(255, 255, 255), fg=(200, 30, 30),
                                                         border=(200, 30, 30), w=768, h=512)), t=(0, 0.2, 0))
    return n


@prop("classroom", "'GO TIGERS' pennant banner")
def banner_go_tigers():
    n = Node("banner_go_tigers")
    n.add(quad(1.6, 0.4), Mat("go_tigers_tex", tex=T.sign("GO TIGERS", bg=(30, 30, 30), fg=(255, 140, 30))), t=(0, 0.2, 0))
    return n


@prop("classroom", "Cubby bookshelf with colourful books")
def bookshelf():
    n = Node("bookshelf")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    n.add(box(1.8, 2.0, 0.4), wd, t=(0, 1.0, -0.02))
    n.add(quad(1.7, 1.9), Mat("books_tex", tex=T.book_spines()), t=(0, 1.0, 0.181))
    return n


# =========================================================================== school hallway / cafeteria / library

@prop("school", "Row of 6 pale-blue hallway lockers")
def lockers_pale():
    n = Node("lockers_pale")
    m = M("locker_pale_blue", "#b9d8e8", rough=0.45, metal=0.3)
    dark = M("locker_vent_pale", "#86a8bc")
    for i in range(6):
        x = (i - 2.5) * 0.42
        n.add(box(0.4, 1.9, 0.45), m, t=(x, 0.95, 0))
        for k in range(3):
            n.add(box(0.26, 0.02, 0.005), dark, t=(x, 1.65 + k * 0.05, 0.226))
        n.add(box(0.03, 0.12, 0.01), dark, t=(x + 0.13, 1.0, 0.23))
    return n


@prop("school", "Ceiling light panel (emissive)")
def ceiling_light():
    n = Node("ceiling_light")
    n.add(box(1.2, 0.05, 0.6), M("ceiling_light_panel", "#ffffff", emissive="#ffffff", emissive_strength=3), t=(0, 0, 0))
    return n


@prop("school", "Cafeteria folding table with 6 round stools")
def cafeteria_table():
    n = Node("cafeteria_table")
    top = M("cafe_table_red", "#a83a2a", rough=0.5)
    leg = M("metal_grey", "#9aa0a6", rough=0.35, metal=0.6)
    stool = M("stool_blue", "#a8d4e8")
    n.add(box(3.0, 0.05, 0.8), top, t=(0, 0.76, 0))
    for sx in (-1, 1):
        n.add(box(0.05, 0.75, 0.6), leg, t=(sx * 1.3, 0.38, 0), r=(0, 0, sx * 12))
    for i in range(3):
        for sz in (-1, 1):
            x = (i - 1) * 1.0
            n.add(cylinder(0.18, 0.05, 14), stool, t=(x, 0.46, sz * 0.65))
            n.add(cylinder(0.025, 0.44, 8), leg, t=(x, 0.22, sz * 0.65))
            n.add(box(0.03, 0.03, 0.4), leg, t=(x, 0.12, sz * 0.45))
    return n


@prop("school", "Lunch tray with burger, fries, milkshake, ketchup + mustard")
def lunch_tray():
    n = Node("lunch_tray")
    n.add(box(0.45, 0.02, 0.32), M("tray_brown", "#7a5a3a"), t=(0, 0.01, 0))
    n.add(cylinder(0.07, 0.025, 14), M("bun", "#d9963c"), t=(-0.1, 0.035, 0.05))
    n.add(cylinder(0.072, 0.015, 14), M("patty", "#5a3220"), t=(-0.1, 0.055, 0.05))
    n.add(hemisphere(0.07, 14, 5, squash=0.6), M("bun", "#d9963c"), t=(-0.1, 0.063, 0.05))
    for i in range(6):
        n.add(box(0.01, 0.07, 0.01), M("fries", "#ffd25a"), t=(0.06 + i * 0.012, 0.055, -0.08), r=(0, 0, (i - 3) * 6))
    n.add(box(0.08, 0.05, 0.05), M("fries_box", "#d83a2a"), t=(0.09, 0.035, -0.08))
    n.add(cylinder(0.035, 0.13, 12, r_top=0.045), M("cup_white", "#f6f6f6"), t=(0.14, 0.075, 0.08))
    n.add(hemisphere(0.045, 12, 4), M("whipped", "#fff7f0"), t=(0.14, 0.14, 0.08))
    for x, c in ((-0.18, "#d81e1e"), (-0.12, "#ffd21e")):
        n.add(cylinder(0.022, 0.14, 10, r_top=0.018), M(f"bottle_{c}", c), t=(x, 0.09, -0.11))
        n.add(cone(0.012, 0.03, 8), M(f"bottle_{c}", c), t=(x, 0.175, -0.11))
    return n


@prop("school", "Round wooden library table with 4 chairs")
def library_table():
    n = Node("library_table")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    n.add(cylinder(0.8, 0.06, 24), wd, t=(0, 0.74, 0))
    n.add(cylinder(0.08, 0.7, 10), wd, t=(0, 0.36, 0))
    n.add(cylinder(0.4, 0.04, 16), wd, t=(0, 0.02, 0))
    for k in range(4):
        a = math.radians(45 + k * 90)
        x, z = math.sin(a) * 1.05, math.cos(a) * 1.05
        c = n.child(f"chair_{k}", t=(x, 0, z), r=(0, math.degrees(a) + 180, 0))
        c.add(box(0.42, 0.04, 0.42), wd, t=(0, 0.45, 0))
        c.add(box(0.42, 0.5, 0.04), wd, t=(0, 0.72, -0.2))
        for sx in (-1, 1):
            for sz in (-1, 1):
                c.add(box(0.035, 0.45, 0.035), wd, t=(sx * 0.18, 0.22, sz * 0.18))
    return n


@prop("school", "Tall library bookcase (red wall style)")
def library_bookcase():
    n = Node("library_bookcase")
    wd = wood_mat("wood_dark", (110, 65, 40), 2)
    n.add(box(2.0, 2.6, 0.4), wd, t=(0, 1.3, -0.02))
    for k in range(2):
        n.add(quad(1.9, 1.2), Mat(f"books_tex_{k}", tex=T.book_spines(seed=k + 3)), t=(0, 0.7 + k * 1.25, 0.181))
    return n


@prop("school", "Composition notebook with flower doodle (open-able: node 'cover')")
def composition_notebook():
    n = Node("composition_notebook")
    n.add(box(0.19, 0.012, 0.25), M("paper_page", "#fbf7ea"), t=(0, 0.008, 0))
    cover = n.child("cover", t=(-0.095, 0.016, 0))
    cover.add(box(0.19, 0.004, 0.25), M("comp_back", "#151515"), t=(0.095, 0, 0))
    cover.add(quad(0.19, 0.25), Mat("comp_cover", tex=T.composition_cover()), t=(0.095, 0.0025, 0), r=(-90, 0, 0))
    return n


@prop("school", "Sheet of lined notebook paper ('compliments' list)")
def notebook_paper():
    n = Node("notebook_paper")
    n.add(quad(0.21, 0.28), Mat("lined_paper_tex", tex=T.lined_paper(), double=True), t=(0, 0.001, 0), r=(-90, 0, 0))
    return n


@prop("school", "'THE NIGHT SKY' poster (lay on table or hang)")
def night_sky_poster():
    n = Node("night_sky_poster")
    n.add(quad(0.45, 0.6), Mat("night_sky_tex", tex=T.night_sky_poster(), double=True), t=(0, 0.3, 0))
    return n


@prop("school", "'PICTURE DAY - CLASS OF 2026' gym banner")
def banner_picture_day():
    n = Node("banner_picture_day")
    n.add(quad(4.0, 1.0), Mat("picture_day_tex", tex=T.banner_picture_day()), t=(0, 0.5, 0))
    return n


@prop("school", "Cork bulletin board (Picture Day / Choir Tryouts)")
def bulletin_board():
    n = Node("bulletin_board")
    n.add(box(1.6, 1.1, 0.04), M("board_frame_wood", "#8a5a30"), t=(0, 0.55, 0))
    n.add(quad(1.5, 1.0), Mat("bulletin_tex", tex=T.bulletin_board()), t=(0, 0.55, 0.021))
    return n


@prop("school", "Photographer's camera on tripod with flash")
def camera_tripod():
    n = Node("camera_tripod")
    blk = M("camera_black", "#1a1a1a", metal=0.4, rough=0.3)
    for k in range(3):
        a = math.radians(k * 120)
        n.add(cylinder(0.015, 1.3, 6), blk, t=(math.sin(a) * 0.2, 0.62, math.cos(a) * 0.2),
              r=(math.degrees(math.cos(a)) * -0.17, 0, math.degrees(math.sin(a)) * 0.17))
    n.add(box(0.25, 0.16, 0.12), blk, t=(0, 1.35, 0))
    n.add(transform(cylinder(0.05, 0.12, 14), r=(90, 0, 0)), M("lens_glass", "#334455", metal=0.8, rough=0.1), t=(0, 1.35, 0.11))
    n.add(box(0.1, 0.06, 0.06), M("flash_head", "#f8f8f8", emissive="#ffffff", emissive_strength=6), t=(0, 1.48, 0.02))
    return n


@prop("school", "Class photo print (handheld)")
def class_photo():
    n = Node("class_photo")
    n.add(quad(0.2, 0.15), Mat("class_photo_tex", tex=T.photo_print(), double=True), t=(0, 0.075, 0))
    return n


@prop("school", "Museum dinosaur skeleton (bone-colour, low poly)")
def dino_skeleton():
    n = Node("dino_skeleton")
    bone = M("bone", "#d8c6a8", rough=0.9)
    n.add(box(3.0, 0.2, 2.0), M("plinth_red", "#9a2a30"), t=(0, 0.1, 0))
    pts = [(-2.2, 1.2), (-1.4, 1.5), (-0.6, 1.8), (0.2, 1.9), (1.0, 2.1), (1.6, 2.6), (2.0, 3.0)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        ln = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        n.add(box(ln, 0.1, 0.1), bone, t=((x0 + x1) / 2, (y0 + y1) / 2, 0), r=(0, 0, ang))
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):
        n.add(torus(0.35, 0.025, 12, 4), bone, t=(x, 1.55, 0), r=(0, 0, 90), s=(1.2, 1, 1))
    n.add(box(0.6, 0.3, 0.3), bone, t=(2.25, 3.0, 0), r=(0, 0, -10))
    for sx in (-1, 1):
        n.add(box(0.1, 1.6, 0.1), bone, t=(-0.4, 0.95, sx * 0.3), r=(0, 0, 8))
        n.add(box(0.1, 1.8, 0.1), bone, t=(0.7, 1.05, sx * 0.3), r=(0, 0, -6))
        n.add(box(0.06, 0.6, 0.06), bone, t=(1.2, 1.8, sx * 0.25), r=(0, 0, 40))
    return n
