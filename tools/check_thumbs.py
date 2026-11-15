"""
check_thumbs.py  -  tests of the designed thumbnails (docs/THUMBNAIL_PLAN.md "Test"). Must print "thumbs: clean".

    bin/python tools/check_thumbs.py

1. Builds the thumbnails of the five test scripts into output/thumb_tests/<script>/ (every option has passed the
   rules of section 4 inside the generator; this tool checks them again from the saved report and the JPGs):
   the Nvidia Short opens with big_number, the Microsoft Short has no stamp line, Tesla gets 3 different layouts,
   Windows vs MacBook has a face_off, and the sample works.
2. Builds every script a second time: the JPGs must be byte-identical.
3. Every option under 3 s, JPG under 2 MB, the right size (1280x720 / 1080x1920), 3 options per video (a Short =
   1 cover + 2 alternates).
4. The rules catch bad pictures: a check() self-test with a headline that is too small, an overlap, low contrast,
   text in the duration-badge corner, and a Short headline outside the centre square.
5. A missing Chromium raises ThumbsFailed (the final render then falls back to frame thumbnails).
Writes output/thumb_tests/contact_sheet.jpg (every option, its layout and its time).
"""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from pipeline import script_parser as P  # noqa: E402
from pipeline.thumbs import design as Ds, layouts as Ly, render as R  # noqa: E402

OUT = ROOT / "output" / "thumb_tests"
TESTS = [  # script, expectations
    ("scripts/2026-11-13-nvidia-ceo-staff-vs-board-short.md", {"short": True, "first": "big_number"}),
    ("scripts/2026-11-13-microsoft-outage-short.md", {"short": True, "no_stamp": True}),
    ("scripts/2026-11-14-tesla-cybercab-for-sale.md", {"short": False, "distinct": 3}),
    ("scripts/2026-11-11-windows-vs-macbook.md", {"short": False, "has": "face_off"}),
    ("docs/sample_motion_gfx_script.md", {"short": False}),
]
LIMIT_MS = 3000


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    problems, rows = [], []
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    for rel, exp in TESTS:
        name = Path(rel).stem
        parsed = P.parse((ROOT / rel).read_text(encoding="utf-8"))
        if parsed["errors"]:
            problems.append(f"{name}: script has errors: {parsed['errors'][:2]}")
            continue
        runs = []
        for k in (1, 2):
            d = OUT / name / f"run{k}"
            d.mkdir(parents=True)
            t0 = time.time()
            rep = R.build(parsed, d)
            runs.append((d, rep, time.time() - t0))
        (d1, rep, secs), (d2, rep2, _) = runs
        opts = rep["options"]
        layouts = [o["layout"] for o in opts]
        W, H = (1080, 1920) if exp["short"] else (1280, 720)
        if len(opts) != 3:
            problems.append(f"{name}: {len(opts)} options (want 3{' = cover + 2' if exp['short'] else ''}): "
                            f"{rep['failed']}")
        if exp.get("first") and (not layouts or layouts[0] != exp["first"]):
            problems.append(f"{name}: first layout {layouts[:1]} (want {exp['first']})")
        if exp.get("has") and exp["has"] not in layouts:
            problems.append(f"{name}: no {exp['has']} option ({layouts}; dropped: {rep['failed']})")
        if exp.get("distinct") and len({l.split()[0] for l in layouts}) < exp["distinct"]:
            problems.append(f"{name}: {len(set(layouts))} different layouts (want {exp['distinct']}): {layouts}")
        if exp.get("no_stamp") and rep["brief"]["stamp"]:
            problems.append(f"{name}: expected no thumbnail_stamp, brief has '{rep['brief']['stamp']}'")
        for o in opts:
            f1, f2 = d1 / o["file"], d2 / o["file"]
            im = Image.open(f1)
            if im.size != (W, H):
                problems.append(f"{name}/{o['file']}: size {im.size} (want {W}x{H})")
            if im.format != "JPEG" or f1.stat().st_size >= R.MAX_BYTES:
                problems.append(f"{name}/{o['file']}: {im.format} {f1.stat().st_size / 1e6:.2f} MB")
            if not f2.exists() or sha(f1) != sha(f2):
                problems.append(f"{name}/{o['file']}: second build is not byte-identical")
            if o["ms"] >= LIMIT_MS:
                problems.append(f"{name}/{o['file']}: {o['ms']} ms (limit {LIMIT_MS})")
            rows.append((name, o, f1, exp["short"]))
        if [o["layout"] for o in rep2["options"]] != layouts:
            problems.append(f"{name}: second build chose other layouts {[o['layout'] for o in rep2['options']]}")
        print(f"  {name}: " + ", ".join(f"{o['layout']} {o['ms']} ms" for o in opts) + f"  (whole build {secs:.1f} s"
              + (f"; dropped {', '.join(f['layout'] + ': ' + '; '.join(f['why']) for f in rep['failed'])}" if rep["failed"]
                 else "") + ")")
    problems += self_test()
    try:                                   # 5. no Chromium -> ThumbsFailed (the render falls back to frames)
        orig = R.chrome_path
        R.chrome_path = lambda: (_ for _ in ()).throw(R.ThumbsFailed("no chromium (test)"))
        try:
            R.build(P.parse((ROOT / TESTS[2][0]).read_text(encoding="utf-8")), OUT / "nochrome")
            problems.append("a missing Chromium did not raise ThumbsFailed")
        except R.ThumbsFailed:
            pass
        finally:
            R.chrome_path = orig
            shutil.rmtree(OUT / "nochrome", ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        problems.append(f"fallback test crashed: {e}")
    sheet(rows)
    ms = [o["ms"] for _, o, _, _ in rows]
    if ms:
        print(f"  time per option: average {sum(ms) / len(ms):.0f} ms, slowest {max(ms)} ms (limit {LIMIT_MS} ms); "
              f"contact sheet: {OUT / 'contact_sheet.jpg'}")
    for p in problems:
        print("  PROBLEM", p)
    print("thumbs: clean" if not problems else f"thumbs: {len(problems)} problem(s)")
    return 1 if problems else 0


def self_test() -> list:
    """The rules must reject bad pictures (check() on made-up measurements)."""
    out = []
    th = {"outline": Ds.INK}
    head = {"role": "headline", "x": 40, "y": 100, "w": 600, "h": 200, "cap": 120, "words": 3, "overflow": False}
    spec = {"texts": [{"role": "headline", "fill": "#FFFFFF", "bg": "#101010", "stroke": 0.07, "outline": Ds.INK}],
            "important": ["headline", "stamp"]}
    cases = {
        "tiny headline": ([dict(head, cap=40)], spec, False, "cap height"),
        "5 words": ([dict(head, words=5)], spec, False, "words"),
        "overlap": ([head, {"role": "stamp", "x": 500, "y": 150, "w": 300, "h": 100, "cap": 60, "words": 2}], spec,
                    False, "overlaps the headline"),
        "low contrast": ([head], {"texts": [{"role": "headline", "fill": "#777777", "bg": "#666666", "stroke": 0,
                                             "outline": Ds.INK}], "important": ["headline"]}, False, "contrast"),
        "badge corner": ([dict(head, x=1050, y=600, w=200, h=100)], spec, False, "duration-badge"),
        "short outside square": ([dict(head, x=40, y=200, w=1000, h=200, cap=150)], spec, True, "centre square"),
        "overflow": ([dict(head, overflow=True)], spec, False, "overflows"),
    }
    for label, (boxes, sp, vertical, want) in cases.items():
        W, H = (1080, 1920) if vertical else (1280, 720)
        why = R.check(boxes, sp, W, H, vertical)
        if not any(want in w for w in why):
            out.append(f"rule self-test '{label}' was not caught (got {why})")
    good = R.check([head], spec, 1280, 720, False)
    if good:
        out.append(f"rule self-test: a good headline failed: {good}")
    _ = th
    return out


def sheet(rows):
    """One contact sheet: every option of every test script with its layout and time."""
    if not rows:
        return
    font = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Barlow-Bold.ttf"), 22)
    big = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Barlow-Bold.ttf"), 30)
    lines, cur, last = [], [], None
    for r in rows:
        if r[0] != last and cur:
            lines.append(cur)
            cur = []
        cur.append(r)
        last = r[0]
    lines.append(cur)
    tiles = []
    for line in lines:
        ims = []
        for name, o, f, short in line:
            im = Image.open(f).convert("RGB")
            im = im.resize((260, 462) if short else (520, 292), Image.LANCZOS)
            cap = Image.new("RGB", (im.width, im.height + 34), (24, 24, 28))
            cap.paste(im, (0, 0))
            ImageDraw.Draw(cap).text((6, im.height + 5), f"{o['file']} · {o['layout']} · {o['ms']} ms", font=font,
                                     fill=(230, 230, 230))
            ims.append(cap)
        w = sum(i.width for i in ims) + 16 * (len(ims) - 1)
        h = max(i.height for i in ims) + 46
        row = Image.new("RGB", (w, h), (24, 24, 28))
        ImageDraw.Draw(row).text((0, 4), line[0][0], font=big, fill=(255, 210, 31))
        x = 0
        for i in ims:
            row.paste(i, (x, 46))
            x += i.width + 16
        tiles.append(row)
    W = max(t.width for t in tiles) + 48
    H = sum(t.height + 24 for t in tiles) + 48
    s = Image.new("RGB", (W, H), (24, 24, 28))
    y = 24
    for t in tiles:
        s.paste(t, (24, y))
        y += t.height + 24
    s.save(OUT / "contact_sheet.jpg", quality=88)


if __name__ == "__main__":
    sys.exit(main())
