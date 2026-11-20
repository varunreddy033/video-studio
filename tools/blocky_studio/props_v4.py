"""Video 4 (robot-battle city): fighting robots, arena, academy, city, forest-secret props."""
import math
import random

from glb import Node, Mat, transform, box, quad, cylinder, cone, sphere, hemisphere, torus
from characters import M
from props import prop, tex_mat
import textures as T


# =========================================================================== robot kit
# Hierarchy: <id> -> hips -> torso, neck->head, arm_L/arm_R (shoulder pivot), leg_L/leg_R or wheel

def _glow(c, s=4.0):
    return M(f"glow_{c}", c, emissive=c, emissive_strength=s)


def robot(rid, body, accent, glow, scale=1.0, fists=1.0, wheel=False, slim=False, ears=False,
          weapon=None, stone=False):
    root = Node(rid, s=(scale, scale, scale))
    root.extras = {"type": "robot"}
    rough = 1.0 if stone else 0.45
    metal = 0.0 if stone else 0.5
    bm = M(f"{rid}_body", body, rough=rough, metal=metal)
    am = M(f"{rid}_accent", accent, rough=rough, metal=metal)
    gm = M(f"stone_glow_{glow}", glow, emissive=glow, emissive_strength=1.5) if stone else _glow(glow)
    dark = M(f"{rid}_joint", "#2a2c33" if not stone else "#a8a294", rough=0.6, metal=metal)
    leg_h = 0.0 if wheel else 0.55
    hips = root.child("hips", t=(0, leg_h + (0.25 if wheel else 0), 0))
    tw = 0.45 if slim else 0.6
    torso = hips.child("torso")
    torso.add(box(tw, 0.5, 0.38), bm, t=(0, 0.3, 0))
    torso.add(box(tw * 0.9, 0.12, 0.4), am, t=(0, 0.08, 0))
    torso.add(transform(cylinder(0.09, 0.02, 16), r=(90, 0, 0)), gm, t=(0, 0.36, 0.2))  # core light
    torso.add(box(tw * 0.75, 0.04, 0.02), gm, t=(0, 0.2, 0.195))
    neck = hips.child("neck", t=(0, 0.55, 0))
    head = neck.child("head", t=(0, 0.17, 0))
    head.add(box(0.38, 0.3, 0.32), am)
    head.add(box(0.3, 0.09, 0.02), M("visor_black", "#0d0f14", rough=0.1), t=(0, 0.02, 0.165))
    for sx in (-1, 1):
        head.add(box(0.07, 0.05, 0.01), gm, t=(sx * 0.07, 0.02, 0.177))
    if ears:
        for sx in (-1, 1):
            head.add(box(0.06, 0.38, 0.06), am, t=(sx * 0.12, 0.33, 0), r=(0, 0, -sx * 18))
            head.add(box(0.03, 0.2, 0.065), gm, t=(sx * 0.13, 0.33, 0.005), r=(0, 0, -sx * 18))
    else:
        head.add(cylinder(0.012, 0.14, 6), dark, t=(0.1, 0.22, 0))
        head.add(sphere(0.03, 8, 6), gm, t=(0.1, 0.3, 0))
    aw = 0.14 if slim else 0.18
    for name, sx in (("L", 1), ("R", -1)):
        arm = hips.child(f"arm_{name}", t=(sx * (tw / 2 + aw / 2 + 0.03), 0.48, 0))
        arm.add(box(aw * 1.2, 0.14, 0.22), am, t=(0, 0.02, 0))  # shoulder pad
        arm.add(box(aw * 0.7, 0.3, aw * 0.7), dark, t=(0, -0.15, 0))
        fs = 0.2 * fists
        arm.add(box(fs, fs, fs), bm, t=(0, -0.3 - fs / 2 + 0.05, 0))
        arm.add(box(fs * 1.02, 0.03, fs * 1.02), gm, t=(0, -0.3 + 0.03, 0))
        if weapon == "saber" and name == "R":
            arm.add(cylinder(0.02, 0.12, 8), dark, t=(0, -0.38, 0.12), r=(90, 0, 0))
            arm.add(cylinder(0.025, 0.8, 10), M("saber_pink", "#ff4fa3", emissive="#ff4fa3", emissive_strength=6),
                    t=(0, -0.38, 0.55), r=(90, 0, 0))
    if wheel:
        wn = hips.child("wheel", t=(0, 0.0, 0))
        wn.add(transform(cylinder(0.22, 0.14, 20), r=(0, 0, 90)), M("tire", "#1a1a1a"), t=(0, 0, 0))
        wn.add(transform(cylinder(0.1, 0.16, 12), r=(0, 0, 90)), am, t=(0, 0, 0))
        torso.add(box(0.16, 0.12, 0.16), dark, t=(0, 0.0, 0))
    else:
        for name, sx in (("L", 1), ("R", -1)):
            leg = hips.child(f"leg_{name}", t=(sx * tw * 0.27, 0, 0))
            leg.add(box(0.15, 0.4, 0.15), dark, t=(0, -0.2, 0))
            leg.add(box(0.22, 0.14, 0.3), bm, t=(0, -0.48, 0.03))
            leg.add(box(0.2, 0.12, 0.2), am, t=(0, -0.22, 0.02))
    return root


ROBOTS = {
    "robot_helper_yellow": dict(body="#ffd21e", accent="#f7f2e6", glow="#4ad7ff", wheel=True, scale=0.8,
                                notes="Little one-wheel helper bot (the hero's eventual robot)"),
    "robot_brawler_orange": dict(body="#ff9a1e", accent="#ffd21e", glow="#ff5a2a", fists=1.6,
                                 notes="Chunky orange brawler with big fists"),
    "robot_tank_red": dict(body="#d8302c", accent="#2f323a", glow="#ff9a2a", fists=2.0, scale=1.25,
                           notes="Heavy red tank bot, oversized grey fists"),
    "robot_scout_purple": dict(body="#7b3fe0", accent="#2a2140", glow="#ff4fd8", slim=True,
                               notes="Slim purple scout with pink glow"),
    "robot_paladin_white": dict(body="#f4f1e8", accent="#ffd21e", glow="#ffe066", weapon="saber", scale=1.15,
                                notes="White/gold knight bot with pink energy saber"),
    "robot_titan_black": dict(body="#1d1f26", accent="#30333d", glow="#4ad7ff", ears=True, fists=1.5, scale=1.6,
                              notes="Titan Zero in its prime: black armour, cyan glow, antenna ears"),
    "robot_rookie_blue": dict(body="#2f7fd8", accent="#e8eef6", glow="#7dffb0", notes="Generic academy bot"),
    "robot_rookie_green": dict(body="#3fbf6a", accent="#22303a", glow="#ffe066", slim=True,
                               notes="Generic academy bot"),
}


def _register_robots():
    for rid, spec in ROBOTS.items():
        spec = dict(spec)
        notes = spec.pop("notes")

        def build(rid=rid, spec=spec):
            return robot(rid, **spec)
        build.__name__ = rid
        prop("robots", notes)(build)


_register_robots()


@prop("robots", "Titan Zero stone statue on pedestal with plaque (town square monument)")
def titan_zero_statue():
    n = Node("titan_zero_statue")
    stone = M("statue_stone", "#e4dccb", rough=1.0)
    n.add(box(3.0, 1.2, 3.0), stone, t=(0, 0.6, 0))
    n.add(box(2.6, 0.3, 2.6), stone, t=(0, 1.35, 0))
    n.add(quad(1.6, 0.6), tex_mat("plaque_titan", T.sign("TITAN ZERO", bg=(225, 215, 195), fg=(70, 60, 50),
                                                          serif=True)), t=(0, 0.6, 1.51))
    n.add(quad(0.7, 0.7), Mat("plaque_emblem", tex=T.emblem((200, 160, 60))), t=(0, 1.0, 1.515))
    bot = robot("titan_zero_stone", "#e4dccb", "#d6cdb9", "#d8c89c", scale=3.2, ears=True, fists=1.5, stone=True)
    bot.t = (0, 1.5, 0)
    n.attach(bot)
    return n


# =========================================================================== hospital

@prop("hospital", "Hospital bed with mint sheets and cyan glow strip")
def hospital_bed():
    n = Node("hospital_bed")
    w = M("plastic_white", "#f1f1ee", rough=0.4)
    n.add(box(1.0, 0.45, 2.0), w, t=(0, 0.45, 0))
    n.add(box(0.96, 0.15, 1.9), M("sheet_mint", "#cfe9d6"), t=(0, 0.75, 0.02))
    n.add(box(0.6, 0.12, 0.35), M("pillow", "#ffffff"), t=(0, 0.86, -0.7))
    n.add(box(1.02, 0.04, 2.02), _glow("#4ae8ff", 3), t=(0, 0.25, 0))
    n.add(box(1.0, 0.6, 0.08), w, t=(0, 0.95, -1.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            n.add(cylinder(0.04, 0.22, 8), M("metal_grey", "#9aa0a6", rough=0.35, metal=0.6), t=(sx * 0.42, 0.11, sz * 0.9))
    return n


@prop("hospital", "Heart-rate monitor on a stand")
def heart_monitor():
    n = Node("heart_monitor")
    g = M("metal_grey", "#9aa0a6", rough=0.35, metal=0.6)
    n.add(cylinder(0.2, 0.04, 14), g, t=(0, 0.02, 0))
    n.add(cylinder(0.025, 1.3, 8), g, t=(0, 0.67, 0))
    n.add(box(0.56, 0.38, 0.08), M("monitor_case", "#e8e8e8"), t=(0, 1.45, 0))
    n.add(quad(0.5, 0.31), Mat("ecg_screen", tex=T.ecg_screen(), emissive="#ffffff", emissive_strength=1.2),
          t=(0, 1.45, 0.041))
    return n


@prop("hospital", "Red neon wall sign 'NO ROBOT FOUND'")
def neon_no_robot():
    n = Node("neon_no_robot")
    n.add(box(1.4, 0.55, 0.06), M("neon_frame", "#2a0a10"), t=(0, 0.275, 0))
    n.add(quad(1.34, 0.5), Mat("neon_no_robot_tex", tex=T.neon_text("NO ROBOT\nFOUND"), emissive="#ffffff",
                               emissive_strength=1.5), t=(0, 0.275, 0.031))
    return n


# =========================================================================== arena / academy

@prop("arena", "Octagonal robot fight ring with glowing edge")
def fight_ring():
    n = Node("fight_ring")
    n.add(transform(cylinder(4.0, 0.4, 8), r=(0, 22.5, 0)), M("ring_base", "#2b2f3a"), t=(0, 0.2, 0))
    n.add(transform(cylinder(3.8, 0.02, 8), r=(0, 22.5, 0)), M("ring_floor", "#5cc8ff", rough=0.3), t=(0, 0.41, 0))
    n.add(transform(torus(3.85, 0.05, 8, 6), r=(0, 22.5, 0)), _glow("#ff4fd8", 5), t=(0, 0.42, 0))
    n.add(transform(torus(1.2, 0.03, 32, 6), r=(0, 0, 0)), _glow("#ffffff", 3), t=(0, 0.425, 0))
    return n


@prop("arena", "Stadium stand section with seated crowd blocks")
def stadium_stand():
    n = Node("stadium_stand")
    seat = M("stand_grey", "#5a6070")
    rnd = random.Random(4)
    cols = ["#e04848", "#4aa0e0", "#ffd21e", "#3fbf6a", "#a060d0", "#f08a30", "#f0f0f0"]
    for k in range(6):
        n.add(box(12, 0.5, 1.0), seat, t=(0, 0.25 + k * 0.5, -k * 1.0), s=(1, 1 + k * 1.0, 1))
        for i in range(16):
            c = rnd.choice(cols)
            x = -5.6 + i * 0.75
            y = (k + 1) * 0.5
            n.add(box(0.35, 0.45, 0.25), M(f"fan_{c}", c), t=(x, y + 0.22, -k * 1.0))
            n.add(box(0.3, 0.3, 0.3), M("fan_skin", "#f2cfa8"), t=(x, y + 0.6, -k * 1.0))
    return n


@prop("arena", "MEGA ARENA entrance gate with gold towers")
def mega_arena_gate():
    n = Node("mega_arena_gate")
    w = M("arena_white", "#f4f2ee")
    gold = M("gold", "#f2c230", rough=0.25, metal=0.8)
    n.add(box(10, 5, 2), w, t=(0, 2.5, 0))
    n.add(box(4, 3.5, 2.1), M("gate_glass", "#7fd0ff", emissive="#7fd0ff", emissive_strength=0.6), t=(0, 1.75, 0))
    n.add(quad(5, 0.8), tex_mat("sign_mega_arena", T.sign("MEGA ARENA", bg=(120, 90, 40), fg=(255, 240, 200),
                                                         serif=True)), t=(0, 4.2, 1.01))
    for sx in (-1, 1):
        n.add(box(1.4, 7, 1.4), w, t=(sx * 5.2, 3.5, 0))
        n.add(cone(0.9, 1.6, 4), gold, t=(sx * 5.2, 7.8, 0), r=(0, 45, 0))
        n.add(box(1.42, 0.12, 1.42), _glow("#4ae8ff", 3), t=(sx * 5.2, 6.0, 0))
    return n


@prop("academy", "ROBOT ACADEMY building facade with banners")
def robot_academy():
    n = Node("robot_academy")
    w = M("academy_white", "#f6f6f8")
    n.add(box(12, 7, 6), w, t=(0, 3.5, 0))
    n.add(box(12.4, 0.5, 6.4), M("academy_trim", "#2a3f9a"), t=(0, 7.2, 0))
    n.add(box(4, 3.4, 0.2), M("academy_door", "#2a3f9a"), t=(0, 1.7, 3.0))
    n.add(quad(5, 0.8), tex_mat("sign_robot_academy", T.sign("ROBOT ACADEMY", bg=(40, 60, 160), fg=(255, 230, 120),
                                                            serif=True, border=(255, 210, 40))), t=(0, 4.2, 3.01))
    n.add(quad(2.2, 2.2), Mat("academy_emblem", tex=T.emblem((255, 200, 30), crown=True)), t=(0, 6.0, 3.02))
    for sx in (-1, 1):
        n.add(box(1.0, 2.0, 0.05), M("banner_navy", "#1d2f80", double=True), t=(sx * 3.5, 4.0, 3.05))
        n.add(quad(0.8, 0.8), Mat("banner_emblem", tex=T.emblem((255, 200, 30))), t=(sx * 3.5, 4.2, 3.08))
    return n


@prop("academy", "Rankings board (TYLER / KENDRA / BROCK), swap 'ranking_tex'")
def ranking_board():
    n = Node("ranking_board")
    n.add(box(1.6, 1.6, 0.1), M("board_frame", "#141a3a"), t=(0, 0.8, 0))
    n.add(quad(1.5, 1.5), Mat("ranking_tex", tex=T.ranking_board(), emissive="#ffffff", emissive_strength=0.6),
          t=(0, 0.8, 0.051))
    return n


@prop("academy", "Robot upgrade terminal (glowing screen kiosk)")
def upgrade_terminal():
    n = Node("upgrade_terminal")
    case = M("kiosk_navy", "#1a2350", metal=0.4, rough=0.3)
    n.add(box(0.8, 2.0, 0.5), case, t=(0, 1.0, 0))
    n.add(quad(0.66, 1.2), Mat("kiosk_screen", tex=T.ecg_screen(320, 512, (120, 220, 255)), emissive="#ffffff",
                               emissive_strength=1.2), t=(0, 1.25, 0.251))
    n.add(box(0.82, 0.05, 0.52), _glow("#ff4fd8", 4), t=(0, 2.0, 0))
    n.add(box(0.82, 0.05, 0.52), _glow("#4ae8ff", 4), t=(0, 0.05, 0))
    return n


@prop("academy", "Hall of Fame wall: WINS 100 / LOSSES 0 + trophies")
def hall_of_fame():
    n = Node("hall_of_fame")
    n.add(box(2.2, 2.2, 0.12), M("hof_wood", "#2a1a0e"), t=(0, 1.1, 0))
    n.add(quad(2.0, 2.0), Mat("hof_tex", tex=T.hall_of_fame(), emissive="#ffe0a0", emissive_strength=0.4),
          t=(0, 1.1, 0.061))
    return n


@prop("arena", "Gold coin (spin it) - also used for 'dollars' shots")
def gold_coin():
    n = Node("gold_coin")
    n.add(transform(cylinder(0.15, 0.03, 24), r=(90, 0, 0)), M("gold", "#f2c230", rough=0.25, metal=0.8), t=(0, 0.15, 0))
    n.add(transform(cylinder(0.11, 0.035, 24), r=(90, 0, 0)), M("gold_inner", "#ffe066", rough=0.3, metal=0.7),
          t=(0, 0.15, 0))
    return n


@prop("arena", "Pile of gold coins")
def coin_pile():
    n = Node("coin_pile")
    rnd = random.Random(2)
    g = M("gold", "#f2c230", rough=0.25, metal=0.8)
    for i in range(40):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 0.5) ** 0.7
        h = max(0.0, 0.35 - r * 0.6)
        n.add(cylinder(0.12, 0.025, 16), g, t=(math.cos(a) * r, rnd.uniform(0, h) + 0.0125, math.sin(a) * r),
              r=(rnd.uniform(-25, 25), 0, rnd.uniform(-25, 25)))
    return n


@prop("arena", "Pink energy orb / power-up (emissive)")
def energy_orb():
    n = Node("energy_orb")
    n.add(sphere(0.3, 16, 12), M("orb_core", "#ffd0f0", emissive="#ff7fd8", emissive_strength=6), t=(0, 0.3, 0))
    n.add(sphere(0.45, 16, 12), M("orb_shell", "#ff7fd8", alpha=0.25, emissive="#ff7fd8", emissive_strength=1,
                                  unlit=True), t=(0, 0.3, 0))
    return n


@prop("arena", "Flag banner on pole with Titan emblem")
def emblem_banner():
    n = Node("emblem_banner")
    n.add(cylinder(0.05, 4, 8), M("pole_white", "#eeeeee", metal=0.4), t=(0, 2, 0))
    n.add(box(1.0, 1.5, 0.03), M("banner_navy", "#1d2f80", double=True), t=(0.55, 3.1, 0))
    n.add(quad(0.8, 0.8), Mat("banner_emblem", tex=T.emblem((255, 200, 30))), t=(0.55, 3.15, 0.02))
    return n


# =========================================================================== city

def _tower(name, color, h, w=4.0, seed=0):
    n = Node(name)
    img = T.skyscraper(tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)), seed=seed)
    m = Mat(f"{name}_facade", tex=img)
    for f in ("front", "back", "left", "right"):
        n.add(box(w, h, w, faces=(f,)), m, t=(0, h / 2, 0))
    n.add(box(w, 0.2, w, faces=("top",)), M("roof_grey", "#7a7f8c"), t=(0, h, 0))
    n.add(box(w * 0.4, 1.0, w * 0.4), M("roof_grey", "#7a7f8c"), t=(0, h + 0.5, 0))
    return n


@prop("city", "Skyscraper, blue glass (20 m)")
def skyscraper_blue():
    return _tower("skyscraper_blue", "#3f86e6", 20, seed=1)


@prop("city", "Skyscraper, pink (26 m)")
def skyscraper_pink():
    return _tower("skyscraper_pink", "#e87aa8", 26, seed=2)


@prop("city", "Skyscraper, yellow (16 m)")
def skyscraper_yellow():
    return _tower("skyscraper_yellow", "#f2c53a", 16, seed=3)


@prop("city", "Skyscraper, purple (30 m)")
def skyscraper_purple():
    return _tower("skyscraper_purple", "#8a5ad8", 30, w=5, seed=4)


@prop("city", "Yellow hover-bus / flying ship")
def hover_ship():
    n = Node("hover_ship")
    y = M("ship_yellow", "#ffd21e", rough=0.35, metal=0.2)
    n.add(transform(sphere(1.0, 16, 10), s=(2.2, 0.7, 1.2)), y, t=(0, 1.2, 0))
    n.add(transform(cylinder(1.5, 0.3, 20), s=(1.6, 1, 0.9)), M("ship_navy", "#1d2f80"), t=(0, 0.7, 0))
    n.add(transform(torus(1.5, 0.06, 28, 6), s=(1.6, 1, 0.9)), _glow("#4ae8ff", 5), t=(0, 0.55, 0))
    for sx in (-1, 1):
        n.add(transform(sphere(0.3, 10, 8), s=(1, 0.6, 1)), M("ship_window", "#bfe6ff", emissive="#bfe6ff",
                                                             emissive_strength=1), t=(sx * 0.8, 1.45, 0.75))
    return n


# =========================================================================== forest secret

@prop("forest", "Tall forest tree (straight trunk, round crown)")
def forest_tree_tall():
    n = Node("forest_tree_tall")
    n.add(cylinder(0.35, 9, 10, r_top=0.28), M("bark_dark", "#5a3c26"), t=(0, 4.5, 0))
    leaf = M("leaves_deep", "#4caa3c", rough=0.9)
    for x, y, z, r in ((0, 9.5, 0, 2.0), (1.4, 8.8, 0.4, 1.5), (-1.3, 9.0, -0.3, 1.5), (0.2, 10.6, 0.3, 1.3)):
        n.add(sphere(r, 12, 8), leaf, t=(x, y, z))
    return n


@prop("forest", "Mossy fallen log")
def mossy_log():
    n = Node("mossy_log")
    n.add(transform(cylinder(0.5, 4.0, 12), r=(0, 0, 90)), Mat("moss_tex", tex=T.moss()), t=(0, 0.5, 0))
    n.add(transform(cylinder(0.42, 4.02, 12), r=(0, 0, 90)), M("log_end", "#9a6a3c"), t=(0, 0.5, 0), s=(1, 1, 1))
    return n


@prop("forest", "Spotted white mushroom (black dots)")
def spotted_mushroom():
    n = Node("spotted_mushroom")
    n.add(cylinder(0.1, 0.3, 10), M("mushroom_stem", "#fff7ef", emissive="#fff3e8", emissive_strength=0.6), t=(0, 0.15, 0))
    n.add(hemisphere(0.28, 16, 6, squash=0.8), Mat("spotted_cap", tex=T.soccer_ball()), t=(0, 0.28, 0))
    return n


def _seal(name, rgb):
    n = Node(name)
    n.add(cylinder(1.6, 0.15, 32), M("seal_stone", "#2a3f8a", rough=0.6), t=(0, 0.075, 0))
    n.add(quad(2.8, 2.8), Mat(f"{name}_glow", tex=T.emblem(rgb), emissive="#ffffff", emissive_strength=4, unlit=True),
          t=(0, 0.16, 0), r=(-90, 0, 0))
    return n


@prop("forest", "Glowing cyan Titan emblem floor seal (hidden underground plate)")
def emblem_seal_cyan():
    return _seal("emblem_seal_cyan", (80, 220, 255))


@prop("forest", "Red 'turned evil' Titan emblem floor seal")
def emblem_seal_red():
    return _seal("emblem_seal_red", (255, 80, 60))


@prop("sport", "Soccer ball (white with black dots)")
def soccer_ball():
    n = Node("soccer_ball")
    n.add(sphere(0.12, 16, 12), Mat("soccer_tex", tex=T.soccer_ball()), t=(0, 0.12, 0))
    return n


@prop("sport", "Soccer goal (white frame + net)")
def soccer_goal():
    n = Node("soccer_goal")
    w = M("paint_white", "#f7f7f7")
    for sx in (-1, 1):
        n.add(cylinder(0.06, 2.2, 8), w, t=(sx * 3.0, 1.1, 0))
        n.add(cylinder(0.04, 2.2, 8), w, t=(sx * 3.0, 1.1, -1.5), r=(0, 0, 0))
    n.add(transform(cylinder(0.06, 6.0, 8), r=(0, 0, 90)), w, t=(0, 2.2, 0))
    n.add(box(6.0, 2.2, 0.01), M("net", "#ffffff", alpha=0.3, double=True), t=(0, 1.1, -1.5))
    return n
