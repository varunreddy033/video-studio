"""The 13 places of blocky3d videos, laid out from the CC0 Kenney packs in assets/blocky3d (index.json).

Units: a person is 5 tall (1 unit ~ 0.35 m). The actors stand around x -6..6, z -4..6 facing +z (the camera side);
outdoor sets reach far along +z because running shots travel that way. Each prop: m = "<pack>/<model>", x, z,
r = turn in degrees, and the size it is scaled to: h = height or w = width (flat things like rugs). y = lift (things on
tables). Room sets also get procedural walls / floor (world.js). Everything is seeded by the set name, so a set looks
the same in every shot and every render.
"""

import json
import random
from functools import lru_cache

from .. import config as C

BASE = C.BASE_DIR / "assets" / "blocky3d"
ROOM = {"w": 26, "d": 22, "h": 9}       # rooms: x -13..13, back wall z -14, open towards the camera


@lru_cache(maxsize=1)
def _index():
    try:
        idx = json.loads((BASE / "index.json").read_text(encoding="utf-8"))
    except OSError:
        return {}
    out = {}
    for fmt in ("glb", "obj"):                      # GLB first; OBJ (furniture, space) only where there's no GLB
        for m in idx["models"]:
            if m["format"] == fmt:
                out.setdefault(m["id"], m["file"])
    return out


def studio(kind: str) -> dict:
    """Studio pack (assets/blocky3d/studio): {id: file} of its 'characters' or 'props'."""
    return {i.split("/", 1)[1]: f for i, f in _index().items()
            if i.startswith("studio/") and f.startswith(f"studio/models/{kind}/")}


def ready() -> bool:
    return bool(_index())


def _p(m, x, z, r=0, h=None, w=None, y=0.0):
    return {"m": m, "x": round(x, 2), "z": round(z, 2), "r": r, "h": h, "w": w, "y": y}


def _scatter(rng, models, n, xs, zs, keep_clear, h):
    out = []
    while len(out) < n:
        x, z = rng.uniform(*xs), rng.uniform(*zs)
        if keep_clear(x, z):
            continue
        out.append(_p(rng.choice(models), x, z, rng.choice((0, 90, 180, 270)), h=h * rng.uniform(0.85, 1.2)))
    return out


def _stage_clear(x, z):          # the actors' stage and the running lane up the middle
    return abs(x) < 10 and z > -12


def town_square(rng):
    p = []
    for k in range(7):
        p.append(_p(f"city_commercial/building-{'abcdefghijklmn'[rng.randrange(14)]}", -60 + k * 20, -72, 0,
                    h=rng.uniform(20, 32)))
    for k in range(8):
        for side in (-1, 1):
            p.append(_p(f"city_commercial/building-{'abcdefghijklmn'[rng.randrange(14)]}", side * 44, -44 + k * 22,
                        -90 * side, h=rng.uniform(18, 28)))
    for k in range(9):
        for side in (-1, 1):
            p.append(_p("city_suburban/tree-large", side * 26, -30 + k * 14, h=13))
            p.append(_p("city_roads/light-square", side * 30, -20 + k * 16, 90 * side, h=12))
    for side in (-1, 1):
        p.append(_p("holiday/bench", side * 16, -6, 90 * side, h=2.6))
        p.append(_p("city_commercial/detail-parasol-a", side * 14, -40, h=7))
    return {"ground": "paving", "props": p}


def street(rng, night=False):
    p = []
    houses = [f"city_suburban/building-type-{c}" for c in "abcdefghijklmnopqrstu"]
    for k in range(10):
        for side in (-1, 1):
            p.append(_p(rng.choice(houses), side * 26, -60 + k * 22, 90 * side, h=rng.uniform(17, 22)))
            tree = "graveyard/pine" if night else "city_suburban/tree-small"
            p.append(_p(tree, side * 17, -50 + k * 22, h=10 if not night else 14))
            p.append(_p("graveyard/lightpost-single" if night else "city_roads/light-curved",
                        side * 11, -40 + k * 22, -90 * side, h=12))
    cars = ["cars/sedan", "cars/taxi", "cars/suv", "cars/van", "cars/hatchback-sports"]
    for k in range(6):
        p.append(_p(rng.choice(cars), rng.choice((-8.5, 8.5)), -30 + k * 30, rng.choice((0, 180)), w=5))
    return {"ground": "road", "props": p}


def beach(rng):
    p = []
    palms = ["pirate/palm-detailed-straight", "pirate/palm-detailed-bend", "pirate/palm-straight", "pirate/palm-bend"]
    for k in range(12):
        side = -1 if k % 2 else 1
        p.append(_p(rng.choice(palms), side * rng.uniform(12, 34), -20 + k * 12, rng.randrange(360), h=rng.uniform(14, 19)))
    for k in range(8):
        p.append(_p(rng.choice(["pirate/rocks-sand-a", "pirate/rocks-sand-b", "pirate/rocks-sand-c"]),
                    rng.choice((-1, 1)) * rng.uniform(11, 30), rng.uniform(-24, 60), rng.randrange(360), h=2.5))
    p += [_p("pirate/boat-row-large", 14, -20, 30, w=9), _p("pirate/structure-platform-dock", -16, -30, 0, w=16),
          _p("survival/tent-canvas", -20, -10, 25, h=5), _p("pirate/chest", 11, -8, -20, h=2.2),
          _p("survival/campfire-pit", -13, -2, h=1.5)]
    return {"ground": "sand", "sea": True, "props": p}


def park(rng):
    p = []
    trees = ["nature/tree_oak", "nature/tree_default", "nature/tree_detailed", "nature/tree_fat"]
    p += _scatter(rng, trees, 26, (-45, 45), (-60, 110), _stage_clear, 15)
    p += _scatter(rng, ["nature/plant_bushLarge", "nature/plant_bush", "nature/plant_bushDetailed"], 18,
                  (-30, 30), (-30, 80), _stage_clear, 3)
    p += _scatter(rng, ["nature/flower_redA", "nature/flower_yellowA", "nature/flower_purpleA"], 30,
                  (-20, 20), (-20, 60), lambda x, z: abs(x) < 7 and z > -10, 1.2)
    for k in range(5):
        p.append(_p("holiday/bench", -11, -6 + k * 18, 90, h=2.6))
        p.append(_p("city_roads/light-curved", 11, k * 18, -90, h=12))
    return {"ground": "grass", "path": True, "props": p}


def forest(rng):
    p = _scatter(rng, ["nature/tree_cone_dark", "nature/tree_detailed_dark", "nature/tree_fat_darkh",
                       "nature/tree_default_dark", "nature/tree_cone"], 70, (-60, 60), (-80, 120),
                 lambda x, z: abs(x) < 8 and z > -10, 18)
    p += _scatter(rng, ["nature/rock_largeA", "nature/rock_largeC", "nature/stump_old", "nature/stump_round"], 20,
                  (-30, 30), (-30, 90), lambda x, z: abs(x) < 7 and z > -10, 3)
    p.append(_p("nature/campfire_logs", -6, -14, h=1.6))
    return {"ground": "forest", "props": p}


def arena(rng):
    p = []
    blocks = ["platformer/blockLarge", "platformer/crateStrong", "platformer/block", "platformer/blockHexagon"]
    p += _scatter(rng, blocks, 24, (-30, 30), (-40, 60), lambda x, z: abs(x) < 9 and z > -14, 6)
    p += [_p("platformer/flag", side * 14, z, h=10) for side in (-1, 1) for z in (-20, 0, 20, 40)]
    p += _scatter(rng, ["platformer/coinGold", "platformer/jewel", "platformer/heart"], 14, (-20, 20), (-20, 50),
                  lambda x, z: abs(x) < 6 and z > -8, 2)
    return {"ground": "arena", "walls": "arena", "props": p}


def space(rng):
    p = _scatter(rng, ["space/craterLarge", "space/crater", "space/meteorFull", "space/meteorHalf", "space/rocksTall",
                       "space/rocks"], 40, (-60, 60), (-80, 120), lambda x, z: abs(x) < 9 and z > -12, 4)
    p += [_p("space/satelliteDish", -20, -30, 20, h=14), _p("space/stationLarge", 26, -46, 0, h=16),
          _p("space/satelliteDishLarge", -40, -60, 30, h=20), _p("space/alien", 12, -14, -30, h=4)]
    return {"ground": "space", "stars": True, "props": p}


def farm(rng):
    """Fields of crops either side, the barn (drawn in world.js), a windmill, hay, sacks of grain, a cart."""
    p = []
    crops = ["nature/crops_cornStageD", "nature/crops_wheatStageB", "nature/crop_pumpkin", "nature/crop_carrot"]
    for side in (-1, 1):
        for row in range(6):
            for k in range(8):
                p.append(_p(crops[(row + (side > 0)) % len(crops)], side * (14 + row * 3.2), -30 + k * 7, h=2.6))
    p += [_p("fantasy_town/windmill", 26, -48, -20, h=26), _p("fantasy_town/cart", 9, -10, -25, w=6)]
    for k in range(7):
        p.append(_p("graveyard/hay-bale", -14 + rng.uniform(-3, 3), -14 + k * 1.6 - 6, rng.randrange(360), h=2.2))
        p.append(_p("food/bag", 6 + rng.uniform(-2.5, 2.5), -15 + rng.uniform(-2, 2), rng.randrange(360), h=1.6))
    for x in range(-30, 31, 6):
        p.append(_p("fantasy_town/fence", x, 14, 0, w=6))
    p += _scatter(rng, ["nature/tree_oak", "nature/tree_default"], 10, (-60, 60), (-80, -40), lambda x, z: False, 15)
    return {"ground": "grass", "barn": True, "props": p}


def market(rng):
    """Two rows of stalls piled with food, crates and barrels: the busy market of a what-if town."""
    p = []
    stalls = ["fantasy_town/stall", "fantasy_town/stall-green", "fantasy_town/stall-red"]
    food = ["food/apple", "food/bread", "food/pumpkin", "food/carrot", "food/watermelon", "food/cabbage", "food/banana"]
    for k in range(5):                         # behind and beside the stage only: high shots look down from +z
        for side in (-1, 1):
            x, z = side * 12, -46 + k * 9
            p.append(_p(stalls[(k + (side > 0)) % 3], x, z, 90 * side, h=7))
            for j in range(3):
                p.append(_p(rng.choice(food), x - side * 0.6, z - 1.5 + j * 1.5, rng.randrange(360), w=1.3, y=2.6))
            p.append(_p(rng.choice(["pirate/crate", "survival/barrel", "food/bag"]), x - side * 3, z + 2.5,
                        rng.randrange(360), h=2))
    p += _scatter(rng, ["platformer/coinGold"], 10, (-6, 6), (-20, 20), lambda x, z: abs(x) < 3, 0.9)
    p += [_p(f"city_suburban/building-type-{c}", (-1) ** i * 24, -40 + i * 18, -90 * (-1) ** i, h=18)
          for i, c in enumerate("acegikm")]
    return {"ground": "paving", "props": p}


def river(rng):
    """A river across the frame (world.js draws it and the broken bridge); a cart of grain on this bank, the
    village on the far bank."""
    p = [_p("fantasy_town/cart", -8, -6, 20, w=6)]
    for k in range(5):
        p.append(_p("food/bag", -8 + rng.uniform(-2, 2), -6 + rng.uniform(-1.5, 1.5), rng.randrange(360), h=1.4, y=1.2))
    for i, c in enumerate("bdfhjln"):
        p.append(_p(f"city_suburban/building-type-{c}", -42 + i * 14, -44 - (i % 2) * 6, 0, h=16))
    p += _scatter(rng, ["nature/tree_oak", "nature/tree_default", "nature/tree_detailed"], 16, (-55, 55), (-36, 60),
                  lambda x, z: -30 < z < -8 or (abs(x) < 10 and z > -8), 14)
    p += _scatter(rng, ["nature/rock_largeA", "nature/rock_largeC"], 6, (-30, 30), (-26, -12), lambda x, z: abs(x) < 6, 2.5)
    return {"ground": "grass", "river": True, "props": p}


def _room(props, wall="#f1e3cf", floor="wood", window=True, board=False):
    return {"ground": floor, "room": dict(ROOM, wall=wall, window=window, board=board), "props": props}


def bedroom(rng, dorm=False):
    if dorm:
        p = [_p("furniture/bedBunk", -9, -10, 0, h=6.5), _p("furniture/desk", 8, -11, 0, h=2.3),
             _p("furniture/laptop", 8, -11, 0, h=0.6, y=2.3), _p("furniture/chairDesk", 8, -8, 180, h=3),
             _p("furniture/lampSquareTable", 10, -12, 0, h=1.3, y=2.3), _p("furniture/cardboardBoxClosed", 11, -3, 20, h=1.6),
             _p("furniture/rugRectangle", 0, -4, 0, w=10), _p("furniture/bookcaseOpenLow", -1, -13, 0, h=3)]
        return _room(p, wall="#d9e4f2")
    p = [_p("furniture/bedSingle", -8, -9, 0, h=2.6), _p("furniture/pillow", -8, -12, 0, w=2.4, y=1.6),
         _p("furniture/desk", 8, -11, 0, h=2.3), _p("furniture/chairDesk", 8, -8, 180, h=3),
         _p("furniture/computerScreen", 8, -12, 0, h=1.5, y=2.3), _p("furniture/bookcaseOpen", 12, -4, -90, h=5.5),
         _p("furniture/lampRoundFloor", -12, -12, 0, h=5), _p("furniture/rugRound", 0, -3, 0, w=9),
         _p("furniture/pottedPlant", -12, -2, 0, h=3), _p("furniture/bear", -6, -8, 20, h=1.2, y=1.6)]
    return _room(p, wall="#f6d9e3")


def house_inside(rng):
    p = [_p("furniture/loungeSofa", -2, -11, 0, h=2.6), _p("furniture/tableCoffee", -2, -6, 0, h=1.3),
         _p("furniture/rugRectangle", -2, -6, 0, w=12), _p("furniture/lampSquareFloor", -9, -12, 0, h=5),
         _p("furniture/kitchenFridge", 11, -12, 0, h=5.4), _p("furniture/kitchenCabinet", 8, -12, 0, h=2.6),
         _p("furniture/kitchenStove", 5.5, -12, 0, h=2.6), _p("furniture/pottedPlant", -12, -3, 0, h=3.2),
         _p("furniture/bookcaseClosedWide", -12, -8, 90, h=5.5), _p("furniture/televisionModern", 11, -2, -90, h=2.2, y=2.2),
         _p("furniture/cabinetTelevision", 11, -2, -90, h=2.2)]
    return _room(p, wall="#efe6d2")


def classroom(rng):
    p = [_p("furniture/desk", 0, -11, 0, h=2.4), _p("furniture/chairDesk", 0, -12.5, 0, h=3),
         _p("furniture/books", 1, -11, 0, h=0.6, y=2.4), _p("furniture/bookcaseClosed", 12, -12, 0, h=6),
         _p("furniture/pottedPlant", -12, -12, 0, h=3.2)]
    for row in range(2):
        for col in (-9, -4.5, 4.5, 9):
            z = -4 - row * 4 if abs(col) > 5 else -7 - row * 4
            p += [_p("furniture/desk", col, z, 180, h=2.2), _p("furniture/chairDesk", col, z + 1.8, 180, h=2.8)]
    return _room(p, wall="#e9efe2", board=True)


def cafeteria(rng):
    p = []
    food = ["food/burger", "food/apple", "food/sandwich", "food/pizza", "food/donut", "food/fries", "food/cupcake"]
    for z in (-11, -5):
        for x in (-8, 8):
            p.append(_p("furniture/table", x, z, 0, h=2.3))
            for dx in (-2.5, 0, 2.5):
                p += [_p("furniture/chair", x + dx, z - 2.4, 0, h=3), _p("furniture/chair", x + dx, z + 2.4, 180, h=3)]
                p.append(_p(rng.choice(food), x + dx, z + rng.uniform(-0.6, 0.6), rng.randrange(360), w=1.1, y=2.3))
    p += [_p("furniture/kitchenFridge", 12, -13, 0, h=5.4), _p("furniture/kitchenBar", 0, -13, 0, h=3.2),
          _p("furniture/trashcan", -12, -12, 0, h=2.2)]
    return _room(p, wall="#fbe7c6", floor="tile", window=True)


BUILDERS = {"town_square": town_square, "street": street, "beach": beach, "house_inside": house_inside,
            "bedroom": bedroom, "classroom": classroom, "cafeteria": cafeteria, "park": park, "arena": arena,
            "forest": forest, "night_town": lambda rng: street(rng, night=True),
            "dorm_room": lambda rng: bedroom(rng, dorm=True), "space": space, "farm": farm, "market": market,
            "river": river}


def layout(name: str) -> dict:
    """{ground, room?, sea?, stars?, path?, walls?, props: [{file, x, z, r, h, w, y}], missing: [model ids]}."""
    idx = _index()
    lay = BUILDERS[name](random.Random(f"blocky3d:{name}"))
    props, missing = [], []
    for pr in lay["props"]:
        f = idx.get(pr["m"])
        if f:
            props.append(dict(pr, file=f))
        else:
            missing.append(pr["m"])
    return dict(lay, id=name, indoor="room" in lay, props=props, missing=sorted(set(missing)))
