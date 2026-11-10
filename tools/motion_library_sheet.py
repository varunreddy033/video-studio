"""
motion_library_sheet.py  -  the motion library on video: every prop, every data component, both palettes, every
transition. Built as an ordinary timeline.json and drawn by the same Remotion composition as real videos.

    bin/python tools/motion_library_sheet.py          -> output/motion_library.mp4  (picture only)
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import motion  # noqa: E402
from pipeline import script_v3 as V3  # noqa: E402

FPS = 30
COLORS = ["accent", "teal", "sky", "coral", "good", "bad"]


def head(text, appear=4):
    return {"appear": appear, "words": [{"text": w, "frame": appear + 8 + 4 * i} for i, w in enumerate(text.split())]}


def el(eid, typ, box, frame, props, kind=None, anim="pop"):
    e = {"id": eid, "type": typ, "box": box, "enter": {"frame": frame, "anim": anim}, "props": props}
    if kind:
        e["kind"] = kind
    return e


def prop_pages():
    kinds = list(V3.CATALOG["props"])
    pages = []
    for start in range(0, len(kinds), 15):
        chunk = kinds[start:start + 15]
        els = []
        for i, k in enumerate(chunk):
            r, c = divmod(i, 5)
            cx, base = 192 + c * 384, 420 + r * 290
            spec = V3.CATALOG["props"][k]
            s = min(220 / spec["w"], 190 / spec["h"])
            w, h = round(spec["w"] * s), round(spec["h"] * s)
            box = {"x": round(cx - w / 2), "y": round(base - h), "w": w, "h": h}
            f = 6 + i * 4
            els.append(el(f"p{start + i}", "prop", box, f, {"kind": k, "text": "", "color": COLORS[i % 6]}, kind=k,
                          anim=spec["anim"] if spec["anim"] != "draw" else "pop"))
            els.append(el(f"l{start + i}", "label", {"x": cx, "y": base - h - 8, "w": 0, "h": 0}, f + 6, {"text": k},
                          kind="label"))
        pages.append({"name": f"props {start // 15 + 1}", "head": f"PROP LIBRARY {start // 15 + 1} OF 3",
                      "elements": els, "seconds": 5.5})
    return pages


def data_pages():
    full = {"x": 0, "y": 0, "w": 1920, "h": 1080}
    return [
        {"name": "line", "head": "LINE CHART  CALENDAR  BIG NUMBER", "seconds": 5, "elements": [
            el("cal", "prop", {"x": 80, "y": 300, "w": 280, "h": 360}, 4, {"kind": "calendar", "text": "NOV 5 THURSDAY"}, "calendar", "drop"),
            el("line", "chart", {"x": 400, "y": 250, "w": 1100, "h": 560}, 8, {"kind": "line", "title": "", "hideTitle": True,
               "data": [["Mon", 100], ["Tue", 104], ["Wed", 103], ["Thu", 109], ["Fri", 112], ["Sat", 101]]}),
            el("num", "number", {"x": 1360, "y": 380, "w": 520, "h": 300}, 20, {"value": -5.5, "decimals": 1, "suffix": "%",
               "label": "in one day", "countFrames": 40})]},
        {"name": "bar", "head": "BAR CHART", "seconds": 5, "elements": [
            el("bar", "chart", {"x": 160, "y": 190, "w": 1600, "h": 800}, 6, {"kind": "bar", "title": "", "hideTitle": True,
               "data": [["Amazon", 220], ["Alphabet", 200], ["Microsoft", 170], ["Meta", 140]]})]},
        {"name": "pie", "head": "PIE  AND  RANKING", "seconds": 5, "elements": [
            el("pie", "pie", {"x": 90, "y": 260, "w": 820, "h": 620}, 6, {"data": [["Chips", 45], ["Data centers", 35], ["Power", 20]], "unit": "%"}),
            el("rank", "ranking", {"x": 1000, "y": 270, "w": 860, "h": 600}, 10,
               {"data": [["Amazon", 220], ["Alphabet", 200], ["Microsoft", 170], ["Meta", 140], ["Oracle", 60]], "unit": "B"})]},
        {"name": "compare", "head": "COMPARISON", "seconds": 5, "elements": [
            el("cmp", "compare", {"x": 260, "y": 240, "w": 1400, "h": 640}, 6,
               {"left": ["Revenue (2025)", 13, "${v}B"], "right": ["Net loss (2025)", 38.5, "${v}B"]})]},
        {"name": "map", "head": "MAP WITH PIN", "seconds": 5.5, "elements": [
            el("map", "map", {"x": 160, "y": 200, "w": 1600, "h": 820}, 4,
               {"countries": ["United States of America", "Taiwan", "China"], "pin": "37.77,-122.42", "pinLabel": "SAN FRANCISCO"},
               anim="fade")]},
        {"name": "quote", "head": "QUOTE  CARD  LABEL TAGS", "seconds": 5, "elements": [
            el("q", "quote", {"x": 80, "y": 230, "w": 1100, "h": 520}, 6, {"text": "Stay curious. Stay skeptical.", "by": "Sterling"}),
            el("crd", "card", {"x": 1150, "y": 300, "w": 700, "h": 400}, 14, {"text": "$730B", "sub": "this year"}),
            el("lb1", "label", {"x": 1500, "y": 300, "w": 0, "h": 0}, 26, {"text": "A LABEL TAG"}, "label")]},
        {"name": "light", "head": "LIGHT PALETTE", "seconds": 5, "palette": "light", "elements": [
            el(f"d{i}", "prop", {"x": 430 + i * 300 - 100, "y": 470, "w": 200, "h": 360}, 6 + i * 6,
               {"kind": "door", "text": "", "color": COLORS[i]}, "door", "grow") for i in range(4)] + [
            el("cn", "prop", {"x": 1560, "y": 640, "w": 250, "h": 230}, 34, {"kind": "coins", "text": ""}, "coins", "grow"),
            el("lt", "label", {"x": 430, "y": 455, "w": 0, "h": 0}, 30, {"text": "FUND"}, "label")]},
    ]


TRANSITIONS = [
    ("PUSH FROM RIGHT", {"type": "push", "dir": "from-right", "frames": 18}),
    ("PUSH FROM LEFT", {"type": "push", "dir": "from-left", "frames": 18}),
    ("DROP FROM THE TOP", {"type": "push", "dir": "from-top", "frames": 18}),
    ("PUSH FROM BELOW", {"type": "push", "dir": "from-bottom", "frames": 18}),
    ("ZOOM-THROUGH", {"type": "zoom", "x": 960, "y": 600, "frames": 22}),
    ("IRIS", {"type": "iris", "frames": 22}),
    ("WHIP PAN", {"type": "whip", "frames": 14}),
    ("FADE", {"type": "fade", "frames": 16}),
    ("CUT", {"type": "cut", "frames": 0}),
]


def main():
    t0 = time.time()
    pages = prop_pages() + data_pages()
    for i, (name, tr) in enumerate(TRANSITIONS):
        kinds = ["rocket", "globe", "trophy", "lightbulb", "jar", "gear", "piggy", "clock", "crown"]
        pages.append({"name": name, "head": name, "seconds": 2.6, "transition": tr, "elements": [
            el(f"t{i}", "prop", {"x": 810, "y": 380, "w": 300, "h": 380}, 2, {"kind": kinds[i], "color": COLORS[i % 6]}, kinds[i])]})
    scenes, cursor = [], 0
    for k, pg in enumerate(pages):
        tr = pg.get("transition") or (None if k == 0 else {"type": "push", "dir": "from-right", "frames": 18})
        frames = round(pg["seconds"] * FPS)
        overlap = tr["frames"] if tr and tr["type"] != "cut" else 0
        begin = cursor - overlap
        scenes.append({"id": f"s{k}", "from": begin, "frames": frames + overlap, "transition": tr, "name": pg["name"],
                       **({"palette": pg["palette"]} if pg.get("palette") else {}),
                       "background": {"tint": "#FBF8F1" if pg.get("palette") == "light" else ["#16294A", "#1A2440", "#132643"][k % 3]},
                       "headline": head(pg["head"]), "elements": pg["elements"]})
        cursor += frames
    tl = {"version": 1, "fps": FPS, "width": 1920, "height": 1080, "durationFrames": cursor, "palette": "navy",
          "words": [], "captions": {"show": False, "style": "none"}, "scenes": scenes}
    work = ROOT / "output" / "motion_library_work"
    shutil.rmtree(work, ignore_errors=True)
    public = work / "public"
    for f in (motion.MOTION_DIR / "public" / "fonts").iterdir():
        motion._link(f, public / "fonts" / f.name)
    tpath = work / "timeline.json"
    tpath.write_text(json.dumps(tl), encoding="utf-8")
    out = ROOT / "output" / "motion_library.mp4"
    p = subprocess.run([motion.npx(), "remotion", "render", "src/index.ts", "Motion", str(out), f"--props={tpath}",
                        f"--public-dir={public}", "--concurrency=4", "--codec=h264", "--crf=18", "--log=error"],
                       cwd=motion.MOTION_DIR)
    if p.returncode != 0:
        sys.exit("render failed")
    shutil.rmtree(work, ignore_errors=True)
    n_props = len(V3.CATALOG["props"])
    print(f"{out}: {cursor / FPS:.0f} s, {n_props} props, {len(data_pages())} data pages, {len(TRANSITIONS)} transitions, "
          f"rendered in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
