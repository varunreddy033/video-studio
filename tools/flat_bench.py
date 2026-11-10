"""
flat_bench.py  -  motion phase 6 benchmark: can FLUX.2 klein 4B keep a FLAT 2D Sterling consistent across poses,
and edit only his mouth/eyes? (Like presenter step 1, docs/presenter_bench/RESULTS.md, but in the flat style.)

    bin/python tools/flat_bench.py [master_seed]      -> output/flat_bench/ + docs/presenter_bench/flat_contact_sheet.jpg

Uses the pack builder's own prompts (tools/make_character_pack.py prompts_for) and scores, so what it shows is what a
real pack build would make:
  masters  4 candidates (SEED .. SEED+3), front, waist-up, mouth closed
  poses    7 poses x 2 ways: A = fixed seed + pose prompt, B = edit of the master (reference image)
  mouths   6 mouth shapes + blink, edited from the master; scored by how much changes outside the mouth/eyes
Every image goes through the shared image cache with the normal cool-down (one image at a time).
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import characters, visuals  # noqa: E402
from pipeline import config as C  # noqa: E402

spec = importlib.util.spec_from_file_location("mcp", ROOT / "tools" / "make_character_pack.py")
MCP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MCP)
OUT = ROOT / "output" / "flat_bench"
SHEET = ROOT / "docs" / "presenter_bench" / "flat_contact_sheet.jpg"
SIZE = MCP.SIZE


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ch = characters.load("sterling_flat")
    seed0 = int(sys.argv[1]) if len(sys.argv) > 1 else ch["seed"]
    t_all, times, res = time.time(), {}, {"character": "sterling_flat", "style": ch["style"]}
    log = lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)  # noqa: E731

    # 1 masters
    t = time.time()
    mprompt = (f"{ch['character']}, front view, waist-up, facing the camera, neutral friendly expression, mouth closed, "
               f"plain light grey background, {ch['style']}")
    masters = [visuals.shared_image(mprompt, SIZE, SIZE, seed0 + i, OUT) for i in range(4)]
    times["4 masters"] = time.time() - t
    log(f"masters done in {times['4 masters']:.0f}s")
    master = masters[0]
    M = MCP.arr(master)

    # 2 poses, both ways (the real builder's prompts)
    t = time.time()
    chs = {**ch, "seed": seed0}
    P = MCP.prompts_for(chs)
    poses = {}
    for i, pose in enumerate(ch["poses"]):
        a = visuals.shared_image(P[f"A/{pose}"], SIZE, SIZE, seed0, OUT)
        b = visuals.shared_image(P[f"B/{pose}"], SIZE, SIZE, seed0 + 1 + i, OUT, refs=[master])
        sc = {}
        for tag, pth in (("A", a), ("B", b)):
            X = MCP.arr(pth)
            sc[tag] = {"file": str(pth), "identity": round(MCP.hist_corr(X, M), 3),
                       "pose_change": round(float(MCP.changed(X, M).mean()), 3)}
        poses[pose] = sc
        log(f"  pose {pose}: A id {sc['A']['identity']} moved {sc['A']['pose_change']} | B id {sc['B']['identity']} moved {sc['B']['pose_change']}")
    times["14 poses"] = time.time() - t

    # 3 mouths + blink, edited from the master
    t = time.time()
    mouths = {}
    for j, (shape, text) in enumerate(MCP.MOUTH_TEXT.items()):
        mouths[shape] = visuals.shared_image(P[f"M/neutral/{shape}"], SIZE, SIZE, 3000 + 10 * j, OUT, refs=[master])
    B = MCP.arr(master).astype(np.int16)
    mbox, ebox = MCP.locate_face(MCP.arr(mouths["wide"]), MCP.arr(mouths["blink"]), B)
    mres = {}
    for shape, pth in mouths.items():
        ins, outs = MCP.inside_outside(MCP.arr(pth), B, [ebox if shape == "blink" else mbox])
        mres[shape] = {"file": str(pth), "inside": round(ins, 3), "outside": round(outs, 4)}
        log(f"  mouth {shape}: inside {ins:.3f}, outside {outs:.4f}")
    times["7 mouth/blink edits"] = time.time() - t
    visuals.stop_image_worker()

    res.update(seed=seed0, masters=[str(m) for m in masters], poses=poses, mouths=mres, mouth_box=mbox, eye_box=ebox,
               seconds={k: round(v) for k, v in times.items()}, total_seconds=round(time.time() - t_all))
    (OUT / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    sheet(ch, masters, poses, mouths, mres, mbox)
    log(f"DONE in {time.time() - t_all:.0f}s -> {SHEET}")


def sheet(ch, masters, poses, mouths, mres, mbox):  # noqa: C901
    cell, pad, lab = 300, 12, 44
    cols = 7
    rows = [("MASTER CANDIDATES (seed +0..+3)", [(Path(m), f"seed +{i}") for i, m in enumerate(masters)]),
            ("POSES A: fixed seed + pose prompt", [(Path(poses[p]["A"]["file"]), f"{p}  id {poses[p]['A']['identity']:.2f}") for p in poses]),
            ("POSES B: edit of master 0", [(Path(poses[p]["B"]["file"]), f"{p}  id {poses[p]['B']['identity']:.2f}") for p in poses]),
            ("MOUTH + BLINK EDITS of master 0 (outside change)", [(Path(mouths[s]), f"{s}  out {mres[s]['outside'] * 100:.1f}%") for s in mouths])]
    W = cols * (cell + pad) + pad
    H = sum(cell + lab + 40 for _ in rows) + 20
    img = Image.new("RGB", (W, H), (20, 26, 40))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(str(C.FONTS_DIR / C.FONT_FILES["heavy"]), 26)
    f2 = ImageFont.truetype(str(C.FONTS_DIR / C.FONT_FILES["medium"]), 20)
    y = 10
    for title, items in rows:
        d.text((pad, y), title, font=f1, fill=(255, 176, 32))
        y += 36
        for i, (p, txt) in enumerate(items):
            x = pad + i * (cell + pad)
            im = Image.open(p).convert("RGB").resize((cell, cell))
            img.paste(im, (x, y))
            d.text((x + 4, y + cell + 4), txt, font=f2, fill=(235, 235, 240))
        y += cell + lab
    # zoom on the mouth box of 3 edits so the lip-sync quality is visible
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    img.save(SHEET, quality=88)
    x0, y0, x1, y1 = mbox
    mouths = {"closed": masters[0], **mouths}           # closed = the master itself (no edit)
    crops = [Image.open(mouths[s]).convert("RGB").crop((x0 - 40, y0 - 40, x1 + 40, y1 + 40)).resize((260, 200))
             for s in ("closed", "slight", "wide", "o", "e", "mbp")]
    strip = Image.new("RGB", (6 * 270 + 10, 220), (20, 26, 40))
    for i, c in enumerate(crops):
        strip.paste(c, (10 + i * 270, 10))
    strip.save(OUT / "mouth_zoom.jpg", quality=90)


if __name__ == "__main__":
    main()
