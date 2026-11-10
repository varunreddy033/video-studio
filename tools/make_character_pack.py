"""
make_character_pack.py  -  builds a presenter's pose/mouth/blink pack + sets (presenter plan, build step 2).

  bin/python tools/make_character_pack.py sterling            build (resumable: every image is in the shared cache)
  bin/python tools/make_character_pack.py sterling --sheet    only rebuild the contact sheet from pack.json

Recipe (from docs/presenter_bench/RESULTS.md):
  master    CHARACTER + STYLE + SEED, front, waist-up, mouth closed, plain background
  poses     2 candidates each: (A) fixed SEED + pose prompt, (B) edit of the master (same character by reference);
            auto-pick: closest to the master in colour, and the pose must actually differ from the master
  mouths    slight / wide / O / E / M-B-P + blink, edited from the picked pose, 2 seeds each; auto-pick: biggest
            change inside the mouth (eyes for blink) with the least change anywhere else; then ONLY the feathered
            mouth/eye area is pasted back onto the untouched pose (no flicker). closed = the pose itself
  cutouts   rembg (MIT, u2net model) alpha from the pose, reused for all its mouth frames
  sets      2 candidates per set; auto-pick: calmest centre (where the presenter stands)
Output: assets/characters/<name>/ (pose_<p>/..., set_<s>.png, pack.json, contact_sheet.jpg, build.log)
"""

import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import characters, visuals  # noqa: E402
from pipeline import config as C  # noqa: E402

# {paws}/{paw}, {ears_up}, {noun}, {fur}, {outfit}, {outfit_short} come from the character file's body words
# (docs/characters/<id>.md: NOUN, LIMBS, FUR, OUTFIT, EARS). With Sterling's words these are exactly the prompts
# his pack was built with, so his cached images stay valid.
POSE_TEXT = {
    "neutral": "standing straight, {paws} relaxed at its sides, calm friendly expression",
    "pointing": "pointing one {paw} toward the camera, confident knowing expression",
    "shrug": "shrugging with both {paws} raised palms up, eyebrows raised",
    "shocked": "shocked, eyes wide{ears_up}, both {paws} raised in surprise",
    "thinking": "thinking, one {paw} on its chin, eyes looking slightly up",
    "serious": "serious expression, {paws} folded in front of it, looking straight into the camera",
    "laughing": "laughing warmly with a big closed-mouth smile, eyes squinted with joy, one {paw} on its belly",
}
MOUTH_TEXT = {
    "slight": "the mouth slightly open as if starting to speak",
    "wide": "the mouth wide open as if saying 'ah'",
    "o": "the mouth open into a small, perfectly round dark circle, lips pushed forward and rounded as if saying 'ooh'",
    "e": "the mouth stretched wide showing teeth as if saying 'ee'",
    "mbp": "the lips pressed firmly together as if saying 'm'",
    "blink": "the eyes fully closed, mouth unchanged",
}
EYES_SHUT_POSES = {"laughing": "Keep the eyes exactly as they are, squinted shut with joy."}
EDIT_TAIL = ("Keep everything else exactly the same: same pose, same face, same {fur}, same {outfit_short}, "
             "same background, same lighting, same framing.")


def words(ch: dict) -> dict:
    b = ch.get("body") or {}
    limbs = b.get("limbs", "hands")
    outfit = b.get("outfit", "outfit")
    return {"paws": limbs, "paw": limbs[:-1] if limbs.endswith("s") else limbs, "noun": b.get("noun", "character"),
            "fur": b.get("fur", "body"), "outfit": outfit, "outfit_short": outfit.split()[-1],
            "ears_up": ", ears up" if b.get("ears") else ""}


def pose_desc(ch: dict, pose: str) -> str:
    if pose in POSE_TEXT:
        return POSE_TEXT[pose].format(**words(ch))
    extra = (ch.get("pose_desc") or {}).get(pose)     # e.g. Poses: ..., excited (both paws up)
    return f"{pose}, {extra}" if extra else pose


def prompts_for(ch: dict) -> dict:
    """Every pose/mouth prompt the builder sends (also used to check Sterling's prompts never change)."""
    w = words(ch)
    tail = EDIT_TAIL.format(**w)
    out = {}
    for pose in ch["poses"]:
        desc = pose_desc(ch, pose)
        out[f"A/{pose}"] = (f"{ch['character']}, {desc}, waist-up, facing the camera, mouth closed, plain light "
                            f"grey background, {ch['style']}")
        out[f"B/{pose}"] = (f"The same {w['noun']} character from the reference image, with the same face, "
                            f"{w['fur']} colours and {w['outfit']} outfit, now {desc}, waist-up, facing the camera, "
                            f"mouth closed, plain light grey background. {ch['style']}")
        eyes_note = EYES_SHUT_POSES.get(pose, "")
        for shape, text in MOUTH_TEXT.items():
            out[f"M/{pose}/{shape}"] = (
                f"Edit this image: change only the {w['noun']}'s mouth so it has {text}. {eyes_note} {tail}"
                .replace("  ", " ") if eyes_note else
                f"Edit this image: change only the {w['noun']}'s face so it has {text}. {tail}")
    return out
SIZE = 1024
SET_W, SET_H = 1280, 720


class Log:
    def __init__(self, d: Path):
        self.d, self.t0, self.times = d, time.time(), {}

    def __call__(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(self.d / "build.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def stage(self, name, t):
        self.times[name] = round(time.time() - t)
        self(f"== {name} done in {self.times[name] // 60} min {self.times[name] % 60} s")


def arr(p):
    return np.asarray(Image.open(p).convert("RGB").resize((SIZE, SIZE))).astype(np.int16)


def hist_corr(a, b):
    def h(x):
        q = (x // 32).reshape(-1, 3)
        idx = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
        v = np.bincount(idx, minlength=512).astype(float)
        return (v - v.mean()) / (v.std() + 1e-9)
    return float((h(a) * h(b)).mean())


def changed(a, b, thr=60):
    return np.abs(a - b).sum(2) > thr


def find_box(diff_mask, region, pad=0.25, min_frac=0.07):
    """Bounding box of the changed pixels inside region=(x0,y0,x1,y1) fractions; robust to stray pixels."""
    H, W = diff_mask.shape
    x0, y0, x1, y1 = int(region[0] * W), int(region[1] * H), int(region[2] * W), int(region[3] * H)
    ys, xs = np.nonzero(diff_mask[y0:y1, x0:x1])
    if len(xs) < 30:
        cx, cy, bw, bh = (x0 + x1) // 2, (y0 + y1) // 2, int(W * min_frac), int(H * min_frac)
    else:
        lx, hx = np.percentile(xs, [5, 95]) + x0
        ly, hy = np.percentile(ys, [5, 95]) + y0
        cx, cy = (lx + hx) / 2, (ly + hy) / 2
        bw = max((hx - lx) / 2 * (1 + pad), W * min_frac)
        bh = max((hy - ly) / 2 * (1 + pad), H * min_frac * 0.75)
    return [int(cx - bw), int(cy - bh), int(cx + bw), int(cy + bh)]


def locate_face(wide, blink, base):
    """Mouth and eye boxes from where the 'wide open' and 'blink' edits changed the MOST (edits also sprinkle
    small fur changes everywhere, so 'any change' is useless). Box sizes scale with the eye-to-mouth distance."""
    import cv2
    def heat(x):
        return cv2.GaussianBlur(np.abs(x - base).sum(2).astype(np.float32), (0, 0), 9)
    H = W = SIZE
    hm, he = heat(wide), heat(blink)
    # front-facing waist-up poses: the mouth is always in the lower-middle of the head (never at the eyes)
    r = hm[int(H * .36):int(H * .62), int(W * .32):int(W * .68)]
    my, mx = np.unravel_index(int(np.argmax(r)), r.shape)
    my, mx = my + int(H * .36), mx + int(W * .32)
    top = max(int(H * .08), my - int(H * .30))
    r = he[top:max(top + 10, my - int(H * .04)), int(W * .15):int(W * .85)]
    ey, ex = np.unravel_index(int(np.argmax(r)), r.shape)
    ey = ey + top
    d = int(np.clip(my - ey, H * .06, H * .22))
    mbox = [mx - int(1.15 * d), my - int(0.62 * d), mx + int(1.15 * d), my + int(0.62 * d)]
    ec = ey + int(0.15 * d)                       # the strongest blink change is the eyelid: centre a bit lower
    ebox = [mx - int(1.75 * d), ec - int(0.62 * d), mx + int(1.75 * d), ec + int(0.62 * d)]
    clip = lambda b: [int(max(0, b[0])), int(max(0, b[1])), int(min(W, b[2])), int(min(H, max(b[3], b[1] + 8)))]  # noqa: E731
    return clip(mbox), clip(ebox)


def box_mask(box, size=(SIZE, SIZE), blur=14):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))


def inside_outside(a, b, boxes):
    ch = changed(a, b)
    inside = np.zeros(ch.shape, bool)
    for x0, y0, x1, y1 in boxes:
        inside[max(0, y0):y1, max(0, x0):x1] = True
    return float(ch[inside].mean()) if inside.any() else 0.0, float(ch[~inside].mean())


def center_busyness(p):
    g = np.asarray(Image.open(p).convert("L").resize((320, 180))).astype(float)
    c = g[30:180, 100:220]
    return float(np.abs(np.diff(c, axis=0)).mean() + np.abs(np.diff(c, axis=1)).mean())


def build(name: str):
    ch = characters.load(name)
    out = characters.pack_dir(name)
    out.mkdir(parents=True, exist_ok=True)
    log = Log(out)
    pack = {"character": name, "doc": ch["doc"], "seed": ch["seed"], "size": SIZE, "poses": {}, "sets": {},
            "built": time.strftime("%Y-%m-%d %H:%M")}
    t_all = time.time()
    log(f"building pack for {name}: {len(ch['poses'])} poses, sets {list(ch['sets'])}")

    # 1 master reference
    t = time.time()
    master = visuals.shared_image(f"{ch['character']}, front view, waist-up, facing the camera, neutral friendly "
                                  f"expression, mouth closed, plain light grey background, {ch['style']}",
                                  SIZE, SIZE, ch["seed"], out)
    shutil.copy(master, out / "master.png")
    log.stage("master reference", t)
    M = arr(master)

    # 2 poses
    t = time.time()
    P = prompts_for(ch)
    for i, pose in enumerate(ch["poses"]):
        a = visuals.shared_image(P[f"A/{pose}"], SIZE, SIZE, ch["seed"], out)
        b = visuals.shared_image(P[f"B/{pose}"], SIZE, SIZE, ch["seed"] + 1 + i, out, refs=[master])
        scores = {}
        for tag, p in (("A", a), ("B", b)):
            X = arr(p)
            ident = hist_corr(X, M)
            moved = float(changed(X, M).mean())
            scores[tag] = {"file": str(p), "identity": round(ident, 3), "pose_change": round(moved, 3),
                           "score": round(ident - (0.5 if (pose != "neutral" and moved < 0.04) else 0), 3)}
        pick = max(scores, key=lambda k: scores[k]["score"])
        # manual swaps: assets/characters/<name>/overrides.json  {"neutral": "master", "shrug": "A", ...}
        ov = json.loads((out / "overrides.json").read_text(encoding="utf-8")).get(pose) if (out / "overrides.json").exists() else None
        if ov == "master":
            scores["M"] = {"file": str(master), "identity": 1.0, "pose_change": 0.0, "score": 1.0}
            pick = "M"
        elif ov in scores:
            pick = ov
        pack["poses"][pose] = {"candidates": scores, "pick": pick, "override": ov}
        log(f"  pose {pose}: A identity {scores['A']['identity']} / B {scores['B']['identity']} -> pick {pick}")
    log.stage(f"poses ({len(ch['poses'])} x 2 candidates)", t)

    # 3 mouths + blink, per picked pose
    t = time.time()
    for pose, info in pack["poses"].items():
        base_p = Path(info["candidates"][info["pick"]]["file"])
        pd = out / f"pose_{pose}"
        pd.mkdir(exist_ok=True)
        base_img = Image.open(base_p).convert("RGB").resize((SIZE, SIZE))
        base_img.save(pd / "closed.png")
        B = np.asarray(base_img).astype(np.int16)
        cands = {}
        eyes_note = EYES_SHUT_POSES.get(pose, "")
        for j, (shape, text) in enumerate(MOUTH_TEXT.items()):
            if shape == "blink" and eyes_note:       # eyes already shut in this pose: no blink edit
                cands[shape] = [pd / "closed.png", pd / "closed.png"]
                continue
            cands[shape] = [visuals.shared_image(P[f"M/{pose}/{shape}"], SIZE, SIZE, 3000 + 10 * j + k, out,
                                                 refs=[pd / "closed.png"])
                            for k in range(2)]
        # mouth box from the strongest 'wide' edit, eye box from the strongest 'blink' edit
        wide = max(cands["wide"], key=lambda p: changed(arr(p), B)[int(SIZE * .15):int(SIZE * .75)].mean())
        blink = max(cands["blink"], key=lambda p: changed(arr(p), B)[int(SIZE * .05):int(SIZE * .6)].mean())
        mbox, ebox = locate_face(arr(wide), arr(blink), B)
        picks = {}
        for shape, paths in cands.items():
            rows = []
            for k, p in enumerate(paths):
                X = arr(p)
                box = ebox if shape == "blink" else mbox
                ins, outs = inside_outside(X, B, [box])
                if shape == "mbp":
                    score = -5 * outs - 0.5 * ins
                else:
                    score = ins - 5 * outs
                rows.append({"file": str(p), "seed": 3000 + 10 * list(MOUTH_TEXT).index(shape) + k,
                             "inside": round(ins, 3), "outside": round(outs, 3), "score": round(score, 3)})
            best = max(range(len(rows)), key=lambda k: rows[k]["score"])
            # paste back ONLY the feathered mouth/eye area onto the untouched pose
            box = ebox if shape == "blink" else mbox
            edit = Image.open(rows[best]["file"]).convert("RGB").resize((SIZE, SIZE))
            Image.composite(edit, base_img, box_mask(box)).save(pd / f"{shape}.png")
            picks[shape] = {"candidates": rows, "pick": best}
        info.update({"mouth_box": mbox, "eye_box": ebox, "shapes": picks, "dir": str(pd)})
        log(f"  mouths for {pose}: mouth box {mbox}, eye box {ebox}, picks "
            + ", ".join(f"{s}:{'AB'[v['pick']]}" for s, v in picks.items()))
        json.dump(pack, open(out / "pack.json", "w", encoding="utf-8"), indent=1)
    log.stage("mouth shapes + blink (7 poses x 6 x 2 seeds)", t)

    # 4 cutouts (alpha from the pose, reused by every mouth frame)
    t = time.time()
    from rembg import new_session, remove
    sess = new_session("u2net")
    for pose, info in pack["poses"].items():
        pd = Path(info["dir"])
        alpha = remove(Image.open(pd / "closed.png").convert("RGB"), session=sess, only_mask=True)
        alpha = alpha.convert("L").filter(ImageFilter.GaussianBlur(0.8))
        alpha.save(pd / "alpha.png")
        for f in ["closed"] + list(MOUTH_TEXT):
            im = Image.open(pd / f"{f}.png").convert("RGB")
            rgba = im.copy()
            rgba.putalpha(alpha)
            rgba.save(pd / f"{f}_cut.png")
    log.stage("cutouts (rembg u2net)", t)

    # 5 sets
    t = time.time()
    for k, (sname, sdesc) in enumerate(ch["sets"].items()):
        # set descriptions are written for the scene ("a screen behind him"); a "him" makes the model draw a person
        import re as _re
        sdesc = _re.sub(r"\b(behind|in front of|next to|beside) (him|her|them)\b", "on the back wall", sdesc)
        sdesc = _re.sub(r"\b(him|her|he|she|presenter|host)\b", "", sdesc).strip(" ,")
        sdesc = _re.sub(rf"\b{_re.escape(ch['name'])}\b", "", sdesc, flags=_re.I).strip(" ,")   # "behind Miso"
        cs = [visuals.shared_image(f"Still-life interior photo of an unoccupied room: {sdesc}. The chair is empty, "
                                   f"wide shot, the middle of the room open and uncluttered, {ch['style']}",
                                   SET_W, SET_H, ch["seed"] + 200 + 10 * k + n, out) for n in range(2)]
        busy = [center_busyness(p) for p in cs]
        pick = int(np.argmin(busy))
        shutil.copy(cs[pick], out / f"set_{sname}.png")
        pack["sets"][sname] = {"candidates": [str(p) for p in cs], "centre_busyness": [round(b, 2) for b in busy],
                               "pick": pick, "file": str(out / f"set_{sname}.png")}
        log(f"  set {sname}: busyness {busy} -> pick {'AB'[pick]}")
    log.stage("sets", t)
    visuals.stop_image_worker()

    pack["timings_seconds"] = log.times
    pack["total_seconds"] = round(time.time() - t_all)
    json.dump(pack, open(out / "pack.json", "w", encoding="utf-8"), indent=1)
    log(f"PACK DONE in {pack['total_seconds'] // 60} min")
    sheet(name)


def preview(out: Path, pack: dict, pose: str, sname: str, W=1920, H=1080):
    bg = Image.open(out / f"set_{sname}.png").convert("RGB").resize((W, H))
    cut = Image.open(Path(pack["poses"][pose]["dir"]) / "closed_cut.png")
    a = np.asarray(cut.split()[-1])
    ys, xs = np.nonzero(a > 20)
    cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = H * 0.88 / cut.height
    cut = cut.resize((int(cut.width * s), int(cut.height * s)), Image.LANCZOS)
    bg.paste(cut, ((W - cut.width) // 2, H - cut.height), cut)
    return bg


def sheet(name: str):
    out = characters.pack_dir(name)
    pack = json.load(open(out / "pack.json", encoding="utf-8"))
    F = lambda s, i=8: ImageFont.truetype(C.FONT_CONDENSED, s, index=i)  # noqa: E731
    T = lambda s: ImageFont.truetype(C.FONT_TEXT, s, index=5)  # noqa: E731
    acc, wh, mu, bgc = (255, 176, 32), (240, 240, 244), (160, 160, 170), (18, 18, 22)
    poses = list(pack["poses"])
    shapes = ["closed", "slight", "wide", "o", "e", "mbp", "blink"]
    tile = 150
    W = 160 + tile * 13 + 40
    rows_h = 300 + 60 + (tile + 34) * len(poses) + 60 + 340
    S = Image.new("RGB", (W, rows_h), bgc)
    d = ImageDraw.Draw(S)
    d.text((24, 18), f"{name.title()} character pack: auto-picks outlined in amber. Approve, or tell me which to swap.",
           font=F(40), fill=wh)
    tt = pack.get("timings_seconds", {})
    d.text((24, 68), "Build time: " + ", ".join(f"{k} {v // 60}m{v % 60:02d}s" for k, v in tt.items())
           + f"   (total {pack.get('total_seconds', 0) // 60} min)", font=T(20), fill=mu)
    # master + pose candidates
    m = Image.open(out / "master.png").convert("RGB").resize((200, 200))
    S.paste(m, (24, 100))
    d.text((24, 306), "master", font=T(20), fill=mu)
    x = 250
    for pose in poses:
        info = pack["poses"][pose]
        for tag in ("A", "B"):
            im = Image.open(info["candidates"][tag]["file"]).convert("RGB").resize((96, 96))
            y = 100 + (0 if tag == "A" else 104)
            S.paste(im, (x, y))
            if info["pick"] == tag:
                d.rectangle([x - 3, y - 3, x + 98, y + 98], outline=acc, width=4)
        if info["pick"] == "M":
            d.text((x + 48, 288), "uses master", font=T(15), fill=acc, anchor="ma")
        d.text((x + 48, 310), pose, font=T(18), fill=wh, anchor="ma")
        x += 112
    d.text((x + 10, 120), "A = fixed seed", font=T(18), fill=mu)
    d.text((x + 10, 146), "B = edit of master", font=T(18), fill=mu)
    # mouth grids: per pose, picked shape (big) + the other candidate (small)
    y = 360
    for c, s in enumerate(shapes):
        d.text((160 + c * tile * 2 + tile, y), s.upper() if len(s) < 2 else {"mbp": "M/B/P"}.get(s, s),
               font=T(20), fill=acc, anchor="ma")
    y += 34
    for pose in poses:
        info = pack["poses"][pose]
        if "shapes" not in info:
            continue
        pd = Path(info["dir"])
        mb, eb = info["mouth_box"], info["eye_box"]
        crop = (min(mb[0], eb[0]) - 30, eb[1] - 30, max(mb[2], eb[2]) + 30, mb[3] + 30)
        d.text((24, y + tile // 2), pose, font=T(22), fill=wh, anchor="lm")
        for c, s in enumerate(shapes):
            im = Image.open(pd / f"{s}.png").convert("RGB").crop(crop).resize((tile, tile))
            xx = 160 + c * tile * 2
            S.paste(im, (xx, y))
            if s != "closed":
                rows = info["shapes"][s]["candidates"]
                other = rows[1 - info["shapes"][s]["pick"]]["file"]
                o = Image.open(other).convert("RGB").resize((SIZE, SIZE)).crop(crop).resize((tile - 40, tile - 40))
                S.paste(o, (xx + tile + 6, y + 20))
                d.text((xx + tile + 6 + (tile - 40) // 2, y + tile - 16), "other", font=T(14), fill=mu, anchor="ma")
        y += tile + 34
    # sets + preview composite
    y += 20
    xx = 24
    for sname, sinfo in pack.get("sets", {}).items():
        for n, p in enumerate(sinfo["candidates"]):
            im = Image.open(p).convert("RGB").resize((256, 144))
            S.paste(im, (xx, y))
            if n == sinfo["pick"]:
                d.rectangle([xx - 3, y - 3, xx + 258, y + 146], outline=acc, width=4)
            xx += 268
        d.text((xx - 268 - 4, y + 150), f"set: {sname}", font=T(18), fill=wh, anchor="ra")
    if pack.get("sets"):
        first_set = list(pack["sets"])[0]
        pv = preview(out, pack, "neutral" if "neutral" in pack["poses"] else poses[0], first_set).resize((512, 288))
        S.paste(pv, (xx + 30, y))
        d.text((xx + 30 + 256, y + 296), f"preview: neutral cut out on '{first_set}'", font=T(18), fill=wh, anchor="ma")
    S.save(out / "contact_sheet.jpg", quality=88)
    print("sheet:", out / "contact_sheet.jpg", S.size)


if __name__ == "__main__":
    n = sys.argv[1] if len(sys.argv) > 1 else "sterling"
    if "--sheet" in sys.argv:
        sheet(n)
    else:
        build(n)
