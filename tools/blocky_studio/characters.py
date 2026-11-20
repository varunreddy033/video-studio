"""Blocky avatar characters with a poseable node hierarchy.

Hierarchy (all pivots at joints, so rotating a node poses the limb):
  <id>                      root, feet at y=0, facing +Z
    hips                    y = 0.5
      torso                 (mesh)
      skirt                 (optional mesh)
      leg_L / leg_R         pivot at hip
      arm_L / arm_R         pivot at shoulder
      neck -> head          pivot at neck; head mesh, face decal ("face"), hair, accessories
"""
from glb import Node, Mat, transform, box, quad, cylinder, cone, sphere, hemisphere, torus
import textures as T

U = 0.25  # one "stud" in metres
HEAD = (1.7 * U, 1.6 * U, 1.6 * U)  # w, h, d

_mat_cache = {}


def M(name, color="#ffffff", **kw):
    key = (name, color, tuple(sorted((k, id(v) if k == "tex" else v) for k, v in kw.items())))
    if key not in _mat_cache:
        _mat_cache[key] = Mat(name, color, **kw)
    return _mat_cache[key]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- hair styles (relative to head centre)

def hair(head, style, color):
    if not style:
        return
    hw, hh, hd = HEAD
    m = M(f"hair_{color}", color, rough=0.9)
    top = hh / 2
    if style == "spiky":
        head.add(box(hw * 1.06, hh * 0.22, hd * 1.06), m, t=(0, top - hh * 0.05, 0))
        spikes = [(-0.5, 0.35, -15, 20), (-0.2, 0.45, 0, 25), (0.15, 0.4, 10, 15), (0.45, 0.3, 25, 20),
                  (-0.35, 0.3, -20, -15), (0.0, 0.35, 0, -25), (0.35, 0.3, 20, -20), (0, 0.5, 5, 0),
                  (-0.5, 0.2, -40, 0), (0.5, 0.2, 40, 0), (-0.1, 0.2, 0, 50), (0.25, 0.2, 10, 50)]
        for x, h, rz, rx in spikes:
            head.add(cone(hw * 0.2, hh * h * 1.4, seg=4), m,
                     t=(x * hw * 0.8, top + hh * h * 0.5, (rx / 60) * hd * 0.25), r=(rx, 45, rz))
        head.add(box(hw * 1.04, hh * 0.25, hd * 0.12), m, t=(0, top - hh * 0.15, hd * 0.5))  # fringe
    elif style == "messy":
        head.add(box(hw * 1.08, hh * 0.3, hd * 1.08), m, t=(0, top - hh * 0.02, -hd * 0.02))
        for i, x in enumerate((-0.38, -0.12, 0.14, 0.38)):
            head.add(box(hw * 0.28, hh * 0.32, hd * 0.12), m, t=(x * hw, top - hh * 0.2 - (i % 2) * hh * 0.05, hd * 0.5),
                     r=(0, 0, (i - 1.5) * 8))
        head.add(box(hw * 1.08, hh * 0.55, hd * 0.12), m, t=(0, top - hh * 0.32, -hd * 0.52))
        for sx in (-1, 1):
            head.add(box(hw * 0.1, hh * 0.45, hd * 0.9), m, t=(sx * hw * 0.53, top - hh * 0.25, -hd * 0.04))
    elif style == "side_part":
        head.add(box(hw * 1.06, hh * 0.24, hd * 1.06), m, t=(0, top + hh * 0.02, 0))
        head.add(box(hw * 0.7, hh * 0.18, hd * 0.2), m, t=(hw * 0.12, top - hh * 0.06, hd * 0.47), r=(0, 0, -6))
        head.add(box(hw * 1.06, hh * 0.45, hd * 0.1), m, t=(0, top - hh * 0.2, -hd * 0.52))
        for sx in (-1, 1):
            head.add(box(hw * 0.08, hh * 0.35, hd * 0.8), m, t=(sx * hw * 0.53, top - hh * 0.2, -hd * 0.05))
    elif style in ("long", "long_bangs", "pigtails", "wavy_long"):
        head.add(box(hw * 1.1, hh * 0.28, hd * 1.1), m, t=(0, top, 0))
        back_len = hh * (1.9 if style != "pigtails" else 1.1)
        head.add(box(hw * 1.12, back_len, hd * 0.25), m, t=(0, top - back_len / 2, -hd * 0.5))
        for sx in (-1, 1):
            head.add(box(hw * 0.16, back_len * 0.95, hd * 0.8), m, t=(sx * hw * 0.58, top - back_len * 0.47, -hd * 0.08))
        if style in ("long_bangs", "wavy_long"):
            for i, x in enumerate((-0.36, -0.12, 0.12, 0.36)):
                head.add(box(hw * 0.26, hh * 0.34, hd * 0.1), m, t=(x * hw, top - hh * 0.2, hd * 0.52),
                         r=(0, 0, (1.5 - i) * 5))
        else:
            head.add(box(hw * 1.1, hh * 0.18, hd * 0.1), m, t=(0, top - hh * 0.08, hd * 0.52))
        if style == "wavy_long":
            for sx in (-1, 1):
                for k in range(5):
                    head.add(box(hw * 0.22, hh * 0.28, hd * 0.22), m,
                             t=(sx * hw * 0.62, top - hh * (0.5 + k * 0.32), hd * 0.25), r=(0, 45 * (k % 2), 0))
        if style == "pigtails":
            for sx in (-1, 1):
                for k in range(4):
                    head.add(sphere(hw * 0.2, 8, 6), m, t=(sx * hw * 0.72, top - hh * (0.6 + k * 0.4), -hd * 0.1))
    elif style == "buzz":
        head.add(box(hw * 1.03, hh * 0.12, hd * 1.03), m, t=(0, top - hh * 0.03, 0))
    elif style == "curly":
        head.add(box(hw * 1.06, hh * 0.22, hd * 1.06), m, t=(0, top - hh * 0.02, 0))
        import random as _r
        rnd = _r.Random(12)
        for gx in range(4):
            for gz in range(4):
                x = (gx - 1.5) * hw * 0.27
                z = (gz - 1.5) * hd * 0.27
                sz = hw * rnd.uniform(0.26, 0.34)
                head.add(box(sz, sz * 0.8, sz), m, t=(x, top + hh * rnd.uniform(0.12, 0.24), z),
                         r=(rnd.uniform(-12, 12), rnd.uniform(0, 45), rnd.uniform(-12, 12)))
        head.add(box(hw * 1.06, hh * 0.5, hd * 0.12), m, t=(0, top - hh * 0.25, -hd * 0.5))
        for sx in (-1, 1):
            head.add(box(hw * 0.08, hh * 0.3, hd * 0.8), m, t=(sx * hw * 0.53, top - hh * 0.15, -hd * 0.05))
    elif style == "quiff":
        head.add(box(hw * 1.06, hh * 0.24, hd * 1.06), m, t=(0, top, 0))
        head.add(box(hw * 1.0, hh * 0.3, hd * 0.45), m, t=(0, top + hh * 0.18, hd * 0.28), r=(-15, 0, 0))
        head.add(box(hw * 1.06, hh * 0.45, hd * 0.1), m, t=(0, top - hh * 0.2, -hd * 0.52))
        for sx in (-1, 1):
            head.add(box(hw * 0.08, hh * 0.3, hd * 0.8), m, t=(sx * hw * 0.53, top - hh * 0.15, -hd * 0.05))
    elif style == "bald_sides":
        for sx in (-1, 1):
            head.add(box(hw * 0.1, hh * 0.35, hd * 0.5), m, t=(sx * hw * 0.53, top - hh * 0.38, -hd * 0.12))
        head.add(box(hw * 1.04, hh * 0.25, hd * 0.08), m, t=(0, top - hh * 0.4, -hd * 0.51))
    elif style == "ponytail":
        head.add(box(hw * 1.08, hh * 0.26, hd * 1.08), m, t=(0, top, 0))
        head.add(box(hw * 1.08, hh * 0.6, hd * 0.12), m, t=(0, top - hh * 0.3, -hd * 0.52))
        head.add(box(hw * 0.25, hh * 1.1, hd * 0.25), m, t=(0, top - hh * 0.55, -hd * 0.68), r=(10, 0, 0))
        for i, x in enumerate((-0.3, 0.0, 0.3)):
            head.add(box(hw * 0.32, hh * 0.25, hd * 0.1), m, t=(x * hw, top - hh * 0.18, hd * 0.52))
    elif style == "swoop":
        head.add(box(hw * 1.08, hh * 0.32, hd * 1.08), m, t=(0, top + hh * 0.04, 0))
        for i in range(5):
            head.add(box(hw * 0.32, hh * 0.22, hd * 0.25), m,
                     t=((i - 2) * hw * 0.22, top + hh * (0.12 + 0.05 * (i % 2)), hd * 0.35), r=(-25, 0, (i - 2) * 10))
        head.add(box(hw * 1.08, hh * 0.55, hd * 0.12), m, t=(0, top - hh * 0.28, -hd * 0.52))
        for sx in (-1, 1):
            head.add(box(hw * 0.1, hh * 0.45, hd * 0.85), m, t=(sx * hw * 0.54, top - hh * 0.2, -hd * 0.04))
    elif style == "bun":
        head.add(box(hw * 1.06, hh * 0.24, hd * 1.06), m, t=(0, top, 0))
        head.add(sphere(hw * 0.28, 10, 8), m, t=(0, top + hh * 0.2, -hd * 0.25))
        head.add(box(hw * 1.06, hh * 0.6, hd * 0.1), m, t=(0, top - hh * 0.3, -hd * 0.52))
    else:
        raise ValueError(style)


# ---------------------------------------------------------------- accessories

def accessory(head, kind, **kw):
    hw, hh, hd = HEAD
    top = hh / 2
    fz = hd / 2 + 0.006
    if kind == "sunglasses":
        m = M("sunglasses", "#111111", rough=0.2, metal=0.3)
        for sx in (-1, 1):
            head.add(box(hw * 0.32, hh * 0.18, 0.02), m, t=(sx * hw * 0.2, hh * 0.08, fz + 0.01))
        head.add(box(hw * 0.95, hh * 0.04, 0.02), m, t=(0, hh * 0.15, fz + 0.01))
    elif kind == "glasses":
        m = M("glasses_frame", kw.get("color", "#8a5a2b"), rough=0.4)
        for sx in (-1, 1):
            x = sx * hw * 0.2
            head.add(box(hw * 0.3, 0.012, 0.015), m, t=(x, hh * 0.18, fz + 0.01))
            head.add(box(hw * 0.3, 0.012, 0.015), m, t=(x, hh * 0.0, fz + 0.01))
            head.add(box(0.012, hh * 0.19, 0.015), m, t=(x - hw * 0.15, hh * 0.09, fz + 0.01))
            head.add(box(0.012, hh * 0.19, 0.015), m, t=(x + hw * 0.15, hh * 0.09, fz + 0.01))
        head.add(box(hw * 0.1, 0.012, 0.015), m, t=(0, hh * 0.12, fz + 0.01))
    elif kind == "mustache":
        m = M(f"hair_{kw.get('color', '#5a3a22')}", kw.get("color", "#5a3a22"), rough=0.9)
        head.add(box(hw * 0.45, hh * 0.09, 0.03), m, t=(0, -hh * 0.12, fz + 0.012))
        for sx in (-1, 1):
            head.add(box(hw * 0.12, hh * 0.08, 0.03), m, t=(sx * hw * 0.25, -hh * 0.16, fz + 0.012), r=(0, 0, sx * 25))
    elif kind == "straw_hat":
        m = M("straw", "#e8c56a", rough=0.95)
        band = M("hat_band", "#c0392b")
        head.add(cylinder(hw * 0.95, 0.02, 20), m, t=(0, top + 0.02, 0))
        head.add(cylinder(hw * 0.5, hh * 0.35, 16, r_top=hw * 0.45), m, t=(0, top + hh * 0.2, 0))
        head.add(cylinder(hw * 0.51, hh * 0.08, 16), band, t=(0, top + hh * 0.08, 0))
    elif kind == "tiara":
        m = M("gold", "#f2c230", rough=0.25, metal=0.8)
        gem = M("gem_pink", "#ff4fa3", rough=0.1, emissive="#ff4fa3", emissive_strength=0.4)
        head.add(box(hw * 0.8, hh * 0.06, hd * 0.06), m, t=(0, top + 0.02, hd * 0.3))
        for x, h in ((-0.3, 0.12), (-0.15, 0.18), (0, 0.26), (0.15, 0.18), (0.3, 0.12)):
            head.add(cone(hw * 0.06, hh * h, 4), m, t=(x * hw, top + 0.02 + hh * h / 2, hd * 0.3))
        head.add(sphere(hw * 0.05, 8, 6), gem, t=(0, top + hh * 0.08, hd * 0.33))
    elif kind == "cap":
        m = M(f"cap_{kw.get('color', '#d33')}", kw.get("color", "#d33333"))
        head.add(hemisphere(hw * 0.58, 16, 6, squash=0.55), m, t=(0, top - 0.01, 0), s=(1, 1, hd / hw))
        head.add(box(hw * 0.7, 0.015, hd * 0.45), m, t=(0, top - 0.01, hd * 0.62))
    elif kind == "top_hat":
        m = M("hat_black", "#151515", rough=0.5)
        band = M("hat_band_gold", "#d9a520", metal=0.6, rough=0.3)
        head.add(cylinder(hw * 0.75, 0.02, 20), m, t=(0, top + 0.01, 0))
        head.add(cylinder(hw * 0.45, hh * 0.9, 20), m, t=(0, top + hh * 0.45, 0))
        head.add(cylinder(hw * 0.46, hh * 0.12, 20), band, t=(0, top + hh * 0.08, 0))
    elif kind == "dino_hat":
        m = M("dino_hat_blue", kw.get("color", "#2aa8d8"), rough=0.8)
        spike = M("dino_spike", "#ffd21e")
        head.add(box(hw * 1.14, hh * 0.55, hd * 1.14), m, t=(0, top + hh * 0.05, -hd * 0.02))
        head.add(box(hw * 0.9, hh * 0.35, hd * 0.6), m, t=(0, top + hh * 0.35, hd * 0.15))  # snout bump
        for sx in (-1, 1):
            head.add(sphere(hw * 0.1, 10, 8), M("eye_white", "#ffffff"), t=(sx * hw * 0.32, top + hh * 0.3, hd * 0.5))
            head.add(sphere(hw * 0.06, 8, 6), M("eye_black", "#111111"), t=(sx * hw * 0.32, top + hh * 0.31, hd * 0.57))
        for i in range(4):
            head.add(cone(hw * 0.09, hh * 0.32, 4), spike, t=(0, top + hh * (0.45 - i * 0.12), hd * (0.05 - i * 0.22)),
                     r=(-20 - i * 18, 45, 0))
        head.add(box(hw * 1.15, hh * 0.08, hd * 0.12), M("dino_teeth", "#f2e6f8"), t=(0, top - hh * 0.18, hd * 0.53))
    elif kind == "scarf":
        m = M(f"scarf_{kw.get('color', '#c81e2a')}", kw.get("color", "#c81e2a"))
        head.add(box(hw * 0.95, hh * 0.22, hd * 0.95), m, t=(0, -hh / 2 - hh * 0.05, 0))
    elif kind == "headphones":
        m = M("headphones", "#222222")
        head.add(torus(hw * 0.58, 0.015, 20, 6), m, t=(0, top - 0.02, 0), r=(0, 0, 90), s=(1, 1, 0.4))
        for sx in (-1, 1):
            head.add(cylinder(hh * 0.18, 0.05, 12), m, t=(sx * hw * 0.55, 0, 0), r=(0, 0, 90))


def body_accessory(root_parts, kind, **kw):
    torso = root_parts["torso_node"]
    if kind == "backpack":
        m = M("backpack", kw.get("color", "#8a8f7a"))
        strap = M("backpack_strap", "#3b3b3b")
        torso.add(box(1.6 * U, 1.7 * U, 0.6 * U), m, t=(0, 3 * U - 2 * U, -0.8 * U))
        torso.add(box(1.2 * U, 0.6 * U, 0.2 * U), m, t=(0, 2.6 * U - 2 * U, -1.15 * U))
        for sx in (-1, 1):
            torso.add(box(0.2 * U, 2 * U, 0.06), strap, t=(sx * 0.55 * U, 3 * U - 2 * U, 0.52 * U))
        if kw.get("badge"):
            torso.add(transform(cylinder(0.35 * U, 0.02, 16), r=(90, 0, 0)), M("badge_navy", "#1d2f80"),
                      t=(0, 1.2 * U, -1.11 * U))
            torso.add(box(0.12 * U, 0.45 * U, 0.01), M("badge_bolt", "#ffd21e", emissive="#ffd21e",
                      emissive_strength=0.5), t=(0, 1.2 * U, -1.13 * U), r=(0, 0, 20))
    elif kind == "wings":
        m = M("wings", "#ffffff", rough=0.6, emissive="#ffe9a8", emissive_strength=0.3)
        for sx in (-1, 1):
            for k in range(4):
                torso.add(box(0.12, 0.6 * U * (4 - k) / 2, 0.03), m,
                          t=(sx * (0.5 * U + 0.11 * k), 3.6 * U - 2 * U - k * 0.06, -0.6 * U),
                          r=(0, sx * -20, sx * (-30 - k * 12)))
    elif kind == "cape":
        m = M(f"cape_{kw.get('color', '#b0182b')}", kw.get("color", "#b0182b"), double=True)
        torso.add(box(2 * U, 3.2 * U, 0.02), m, t=(0, 2.4 * U - 2 * U, -0.55 * U), r=(8, 0, 0))


# ---------------------------------------------------------------- character factory

def character(spec):
    cid = spec["id"]
    skin = M(f"skin_{spec['skin']}", spec["skin"], rough=0.7)
    scale = spec.get("scale", 1.0)
    root = Node(cid, s=(scale, scale, scale))
    root.extras = {"type": "character", "faces_dir": "textures/faces", "default_face": spec.get("face", "smile")}
    hips = root.child("hips", t=(0, 2 * U, 0))

    # torso ---------------------------------------------------------------------------------
    torso = hips.child("torso")
    front = spec.get("torso_front")
    side = spec.get("torso_side")
    side_mat = M(f"{cid}_shirt", tex=side) if hasattr(side, "save") else M(f"{cid}_shirt", side or "#888888")
    front_mat = M(f"{cid}_shirt_front", tex=front) if hasattr(front, "save") else side_mat
    tz = (0, 1 * U, 0)
    torso.add(box(2 * U, 2 * U, 1 * U, faces=("front",)), front_mat, t=tz)
    torso.add(box(2 * U, 2 * U, 1 * U, faces=("back", "left", "right", "top", "bottom")), side_mat, t=tz)
    parts = {"torso_node": torso}

    # skirt / dress -------------------------------------------------------------------------
    if spec.get("skirt") is not None:
        sk = spec["skirt"]
        sm = M(f"{cid}_skirt", tex=sk) if hasattr(sk, "save") else M(f"{cid}_skirt", sk)
        flare = spec.get("skirt_flare", 1.15)
        length = spec.get("skirt_len", 0.9)
        torso.add(transform(cylinder(1.45 * U * flare, length * U, 4, r_top=1.45 * U), r=(0, 45, 0)), sm,
                  t=(0, -length * U / 2 + 0.1 * U, 0), s=(1, 1, 0.55))

    # legs --------------------------------------------------------------------------------------
    pants = spec.get("pants", "#222222")
    pm = M(f"{cid}_pants", tex=pants) if hasattr(pants, "save") else M(f"{cid}_pants", pants)
    shoe = M(f"shoe_{spec.get('shoes', '#1a1a1a')}", spec.get("shoes", "#1a1a1a"))
    sock = spec.get("socks")
    for side_name, sx in (("L", 1), ("R", -1)):  # character's left is +X when facing +Z
        leg = hips.child(f"leg_{side_name}", t=(sx * 0.5 * U, 0, 0))
        if sock:
            leg.add(box(0.98 * U, 1.1 * U, 0.98 * U), pm, t=(0, -0.55 * U, 0))
            leg.add(box(1.0 * U, 0.65 * U, 1.0 * U), M(f"sock_{sock}", sock), t=(0, -1.4 * U, 0))
        else:
            leg.add(box(0.98 * U, 1.75 * U, 0.98 * U), pm, t=(0, -0.875 * U, 0))
        leg.add(box(1.0 * U, 0.25 * U, 1.1 * U), shoe, t=(0, -1.875 * U, 0.05 * U))

    # arms --------------------------------------------------------------------------------------
    sleeve = spec.get("sleeves", side)
    slm = M(f"{cid}_sleeve", tex=sleeve) if hasattr(sleeve, "save") else M(f"{cid}_sleeve", sleeve or "#888888")
    sleeve_len = spec.get("sleeve_len", 1.5)
    for side_name, sx in (("L", 1), ("R", -1)):
        arm = hips.child(f"arm_{side_name}", t=(sx * 1.5 * U, 1.75 * U, 0))
        arm.add(box(0.96 * U, sleeve_len * U, 0.96 * U), slm, t=(0, 0.25 * U - sleeve_len * U / 2, 0))
        hand_len = 2 * U - sleeve_len * U
        arm.add(box(0.92 * U, hand_len, 0.92 * U), skin, t=(0, 0.25 * U - sleeve_len * U - hand_len / 2, 0))

    # head --------------------------------------------------------------------------------------
    hw, hh, hd = HEAD
    neck = hips.child("neck", t=(0, 2 * U, 0))
    head = neck.child("head", t=(0, hh / 2, 0))
    head.add(box(hw, hh, hd), skin)
    face_img = T.face(spec.get("face", "smile"), lash=spec.get("lash", False))
    fnode = head.child("face", t=(0, 0, hd / 2 + 0.003))
    fnode.add(quad(hw * 0.95, hh * 0.95), Mat(f"face_{cid}", tex=face_img, rough=0.9))
    fnode.extras = {"swap_texture_from": "textures/faces/*.png"}
    hair(head, spec.get("hair"), spec.get("hair_color", "#3a2414"))
    for acc in spec.get("head_acc", []):
        name, kw = (acc, {}) if isinstance(acc, str) else acc
        accessory(head, name, **kw)
    for acc in spec.get("body_acc", []):
        name, kw = (acc, {}) if isinstance(acc, str) else acc
        body_accessory(parts, name, **kw)
    return root


def chicken():
    root = Node("chicken")
    root.extras = {"type": "creature"}
    white = M("feather_white", "#f3f1ee")
    beak = M("beak", "#f2a33a")
    comb = M("comb", "#d9342b")
    leg = M("chicken_leg", "#e8a33c")
    root.add(box(0.32, 0.3, 0.42), white, t=(0, 0.42, 0))
    root.add(box(0.2, 0.32, 0.2), white, t=(0, 0.68, 0.14))
    root.add(box(0.07, 0.05, 0.1), beak, t=(0, 0.7, 0.29))
    root.add(box(0.05, 0.08, 0.05), comb, t=(0, 0.66, 0.26))
    root.add(box(0.05, 0.08, 0.16), comb, t=(0, 0.87, 0.14))
    root.add(box(0.26, 0.22, 0.08), white, t=(0, 0.52, -0.24), r=(-30, 0, 0))
    for sx in (-1, 1):
        root.add(box(0.04, 0.16, 0.26), white, t=(sx * 0.18, 0.44, -0.02))
        root.add(box(0.04, 0.28, 0.04), leg, t=(sx * 0.08, 0.14, 0))
        root.add(box(0.1, 0.02, 0.12), leg, t=(sx * 0.08, 0.01, 0.03))
        root.add(box(0.03, 0.05, 0.01), M("eye_black", "#111111"), t=(sx * 0.1, 0.74, 0.245))
    return root


# ---------------------------------------------------------------- the cast (inspired by the reference reels)

def cast():
    C = []
    green_stripes = T.stripes((25, 25, 25), (60, 200, 60), n=7)
    C.append(dict(id="stripe_kid", skin="#f5d6b4", face="smile", hair="spiky", hair_color="#3fbf3f",
                  torso_side=green_stripes, torso_front=green_stripes, sleeves=green_stripes, pants="#151515",
                  shoes="#101010", notes="Recurring hero: spiky green hair, green/black striped tee, black pants"))
    uni = T.school_uniform()
    C.append(dict(id="goth_girl", skin="#e9c3a0", face="smug", lash=True, hair="long_bangs", hair_color="#141418",
                  torso_front=uni, torso_side="#1e1e23", sleeves="#1e1e23", pants="#e9c3a0",
                  skirt=T.plaid((45, 45, 50), (110, 110, 120)), socks="#f2f2f2", shoes="#0e0e0e",
                  notes="Love interest: long black hair, black blazer, plaid skirt, white socks"))
    C.append(dict(id="brunette_girl", skin="#f0c9a8", face="happy", lash=True, hair="wavy_long", hair_color="#4a2c1c",
                  torso_front=T.school_uniform((95, 60, 40)), torso_side="#5f3c28", sleeves="#5f3c28",
                  pants="#f0c9a8", skirt="#2b2220", socks="#f2f2f2", shoes="#151515",
                  notes="Brown-haired classmate, brown blazer, dark skirt"))
    C.append(dict(id="mayor", skin="#f2cfa8", face="yelling", hair="side_part", hair_color="#5a3a22",
                  head_acc=[("mustache", {"color": "#5a3a22"})], torso_front=T.suit_front((40, 40, 45)),
                  torso_side="#28282d", sleeves="#28282d", pants="#28282d",
                  notes="Town mayor: suit, side-part hair, mustache"))
    C.append(dict(id="businessman", skin="#f2cfa8", face="smile", hair="messy", hair_color="#b5532a",
                  torso_front=T.suit_front((35, 35, 40)), torso_side="#232328", sleeves="#232328", pants="#232328",
                  body_acc=[("backpack", {"color": "#8b8f80"})], notes="Ginger guy in suit with backpack"))
    C.append(dict(id="hoodie_boy", skin="#f6d3b0", face="shocked", hair="messy", hair_color="#5b3418",
                  torso_front=T.hoodie_front((250, 200, 30)), torso_side="#fac81e", sleeves="#fac81e",
                  sleeve_len=1.7, pants="#2b4fae", shoes="#20263a",
                  notes="Hero of the 'sun' reel: yellow hoodie, blue jeans, brown hair"))
    C.append(dict(id="old_man", skin="#f3c79a", face="sleepy_blush", hair=None,
                  head_acc=[("glasses", {"color": "#b4651e"})], torso_front=T.button_shirt(),
                  torso_side="#f07828", sleeves="#f07828", pants="#6b4a35", shoes="#3a2a20",
                  notes="Bald grandpa, orange button shirt, round glasses"))
    C.append(dict(id="pajama_girl", skin="#f6d0b2", face="laugh", lash=True, hair="pigtails", hair_color="#9a1f1a",
                  torso_front=T.pajama(), torso_side=T.pajama(), sleeves=T.pajama(), pants=T.pajama(),
                  shoes="#f6a7c8", sleeve_len=1.8, notes="Little sister: red curly pigtails, pink pajamas"))
    C.append(dict(id="farmer", skin="#e8b98e", face="neutral", hair="buzz", hair_color="#4a3020",
                  head_acc=["straw_hat"], torso_front=T.overalls(), torso_side="#dc5032", sleeves="#dc5032",
                  pants="#4664aa", shoes="#4a3020", notes="Mushroom farmer: straw hat, overalls"))
    C.append(dict(id="show_host", skin="#f2cfa8", face="happy", hair="side_part", hair_color="#c0541f",
                  torso_front=T.suit_front((200, 150, 40), bowtie=True, sparkle=True),
                  torso_side=T.suit_front((200, 150, 40), sparkle=True), sleeves=T.suit_front((200, 150, 40), sparkle=True),
                  pants="#111111", notes="Contest host: gold sequin tux, bow tie"))
    C.append(dict(id="athlete", skin="#6b3f26", face="determined", hair="buzz", hair_color="#1a1a1a",
                  torso_front=T.jersey((30, 50, 160)), torso_side="#1e32a0", sleeves="#1e32a0", sleeve_len=0.8,
                  pants="#d02a2a", socks="#f0f0f0", shoes="#f0f0f0", notes="Gym / sports kid: blue #10 jersey, red shorts"))
    C.append(dict(id="princess_costume", skin="#e9c3a0", face="love", lash=True, hair="long_bangs",
                  hair_color="#141418", head_acc=["tiara"], body_acc=["wings"], torso_front=T.dress_pink(),
                  torso_side="#ffaad2", sleeves="#ffc0dc", pants="#ffaad2", skirt=T.dress_pink(),
                  skirt_flare=1.6, skirt_len=1.6, shoes="#ff7fb5",
                  notes="Costume-contest look: pink frilly dress, tiara, angel wings"))
    C.append(dict(id="kid_green", skin="#f6d3b0", face="smile", hair="side_part", hair_color="#d39a4a",
                  torso_front=T.hoodie_front((70, 170, 110)), torso_side="#46aa6e", sleeves="#46aa6e",
                  pants="#4a4a52", scale=0.85, notes="Small kid, green hoodie (reading a picture book)"))
    tf = [("#e04848", "#3a3a8a", "#2b1a10", "messy"), ("#4aa0e0", "#2a2a2a", "#d8b04a", "bun"),
          ("#a060d0", "#444444", "#111111", "long"), ("#f08a30", "#335533", "#6b3a1a", "buzz"),
          ("#30b0a0", "#5a3a2a", "#1a1a1a", "side_part"), ("#e070a0", "#2a3a6a", "#7a2a1a", "pigtails")]
    skins = ["#f6d3b0", "#c68a5a", "#8a5634", "#f0c9a8", "#e8b98e", "#5c3a24"]
    for i, (shirt, pants, hc, hs) in enumerate(tf):
        C.append(dict(id=f"townsfolk_{i + 1}", skin=skins[i], face=["smile", "neutral", "happy", "worried", "smug", "laugh"][i],
                      hair=hs, hair_color=hc, torso_side=shirt, pants=pants, notes="Background crowd / townsperson"))
    # ---- videos 5-7 (house comedy, classroom romance, school crush)
    C.append(dict(id="hitman", skin="#f2cfa8", face="glare", hair="swoop", hair_color="#3a2414",
                  head_acc=["sunglasses"], torso_front=T.suit_front((22, 22, 26), tie=(200, 30, 30)),
                  torso_side="#16161a", sleeves="#16161a", pants="#16161a",
                  notes="Hired 'hitman': slick hair, sunglasses, black suit, red tie"))
    C.append(dict(id="little_brother", skin="#f6d3b0", face="troll_grin", hair="spiky", hair_color="#d9a24a",
                  torso_front=T.pixel_face_tee(), torso_side="#46aa3c", sleeves="#46aa3c", sleeve_len=0.8,
                  pants="#1a1f33", shoes="#f0f0f0", scale=0.8,
                  notes="Cheeky little brother: blond spikes, green pixel-smiley tee"))
    C.append(dict(id="dad_bald", skin="#f2cfa8", face="unimpressed", hair="bald_sides", hair_color="#5a3a22",
                  torso_front=T.suit_front((245, 245, 245), (245, 245, 245), (120, 70, 40)), torso_side="#f2f2f2",
                  sleeves="#f2f2f2", sleeve_len=1.0, pants="#5a4630", shoes="#2a1e14",
                  notes="Dad: bald with side tufts, white shirt, brown tie"))
    C.append(dict(id="narrator_glasses", skin="#f2cfa8", face="screaming", hair="bald_sides", hair_color="#3a2414",
                  head_acc=[("glasses", {"color": "#222222"})], torso_front=T.suit_front((22, 22, 26), (40, 90, 170),
                  (40, 90, 170)), torso_side="#16161a", sleeves="#16161a", pants="#16161a",
                  notes="Panicking older sibling: glasses, black jacket over blue tee"))
    C.append(dict(id="ginger_boy", skin="#f6d3b0", face="troll_grin", hair="messy", hair_color="#f06a1e",
                  torso_front=T.text_tee(), torso_side="#141416", sleeves="#141416", sleeve_len=0.9,
                  pants=T.hearts_pattern(), shoes="#f0f0f0",
                  notes="Lovesick ginger: 'REAL MEN WEAR PINK' tee, heart pajama pants"))
    C.append(dict(id="pink_hair_friend", skin="#f6d3b0", face="smirk", hair="spiky", hair_color="#f2a0b4",
                  head_acc=[("scarf", {"color": "#c81e2a"})], torso_front=T.suit_front((20, 20, 26), (200, 30, 40),
                  (200, 30, 40)), torso_side="#141418", sleeves="#141418", pants="#141418",
                  notes="Wingman: pink spiky hair, red scarf, dark jacket"))
    C.append(dict(id="crush_girl_pink", skin="#f6d3b0", face="blush_shy", lash=True, hair="long_bangs",
                  hair_color="#101014", torso_front=T.dress_pink(), torso_side="#ffc0d8", sleeves="#ffc0d8",
                  pants="#1e1e24", skirt="#1e1e24", shoes="#151515", notes="Crush: long black hair, pink top"))
    C.append(dict(id="dino_hat_kid", skin="#ffd21e", face="anime_worried", hair=None, head_acc=["dino_hat"],
                  torso_side="#16d0e8", sleeves="#ffd21e", sleeve_len=0.01, pants="#141414", shoes="#141414",
                  notes="Classic yellow-skin kid: cyan tee, black pants, blue dino hood with yellow spikes"))
    C.append(dict(id="sweater_boy", skin="#f6d3b0", face="shocked", hair="messy", hair_color="#5a3418",
                  torso_front=T.knit_stripes(), torso_side=T.knit_stripes(), sleeves=T.knit_stripes(),
                  pants=T.patterned_pants(), shoes="#2a2a2a", notes="Best friend: chunky striped knit sweater"))
    C.append(dict(id="uniform_girl", skin="#f0c9a8", face="anime_smile", lash=True, hair="long_bangs",
                  hair_color="#0c0c10", torso_front=T.crest_blazer(), torso_side="#18181c", sleeves="#18181c",
                  pants="#f0c9a8", skirt=T.plaid((60, 60, 66), (200, 200, 210)), socks="#f4f4f4", shoes="#0e0e0e",
                  notes="Crush in academy uniform: crest blazer, plaid skirt, knee socks"))
    C.append(dict(id="ponytail_girl", skin="#f6d3b0", face="anime_shocked", lash=True, hair="ponytail",
                  hair_color="#121216", torso_front=T.crest_blazer(), torso_side="#18181c", sleeves="#18181c",
                  pants="#f6d3b0", skirt=T.plaid((60, 60, 66), (200, 200, 210)), socks="#f4f4f4", shoes="#0e0e0e",
                  notes="Same uniform, ponytail (the 'new haircut' look)"))
    C.append(dict(id="blonde_girl", skin="#f6d3b0", face="happy", lash=True, hair="pigtails", hair_color="#f2d06a",
                  torso_side="#f4a8c8", sleeves="#f4a8c8", pants="#7a6aa8", notes="Blonde classmate, pink sweater"))

    # ---- video 4 (robot-battle city)
    C.append(dict(id="robot_kid", skin="#c08a5c", face="worried", hair="curly", hair_color="#4a2a16",
                  torso_front=T.hoodie_front((245, 195, 30), string=(40, 180, 140)), torso_side="#f5c31e",
                  sleeves="#f5c31e", sleeve_len=1.7, pants="#24346e", shoes="#d83a3a",
                  body_acc=[("backpack", {"color": "#2fae96", "badge": True})],
                  notes="Hero of the robot reel: curly hair, yellow hoodie, teal backpack with bolt badge, no robot"))
    C.append(dict(id="rival_blond", skin="#f6d6b8", face="smug", hair="quiff", hair_color="#f2d33a",
                  torso_front=T.varsity_jacket(), torso_side="#d0262e", sleeves="#d0262e", pants="#151a2a",
                  shoes="#f0f0f0", notes="Cocky rival: blond quiff, red/white varsity jacket"))
    C.append(dict(id="ringmaster", skin="#f2cfa8", face="happy", hair="side_part", hair_color="#3a2414",
                  head_acc=["top_hat"], torso_front=T.suit_front((20, 20, 24), tie=(200, 30, 30), bowtie=True),
                  torso_side="#16161a", sleeves="#16161a", pants="#16161a",
                  notes="Arena announcer: top hat, black tux, red bow tie"))
    for i, (sk, hs, hc) in enumerate((("#f6d3b0", "messy", "#6b3a1a"), ("#8a5634", "bun", "#151515"),
                                      ("#e8b98e", "quiff", "#f0c84a"))):
        C.append(dict(id=f"academy_student_{i + 1}", skin=sk, face=["determined", "smile", "smug"][i], hair=hs,
                      hair_color=hc, torso_front=T.academy_tee(), torso_side="#2f7fd8", sleeves="#2f7fd8",
                      pants="#1e2440", notes="Robot Academy student uniform (blue tee, ring logo)"))
    return C
