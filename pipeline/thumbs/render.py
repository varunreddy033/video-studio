"""Designed thumbnails: brief -> layouts -> HTML -> headless Chromium screenshot -> rule checks -> JPG.

    make(parsed, out_dir)       writes thumb_1..3.jpg (16:9 for full videos, 9:16 for Shorts: 1 cover + 2 alternates)
                                and returns the report {"options", "failed", "brief", "seconds"}
    preview(parsed)             the same into output/thumb_previews/<key>/ (cached), for the Check page

Every option must pass the rules of docs/THUMBNAIL_PLAN.md section 4 (big text <= 4 words, headline cap height >= 18 px
at 320 x 180 / 180 x 320, contrast >= 4.5, safe areas, no overflow, nothing over the headline, JPG q90 < 2 MB); an option
that fails is dropped and the next layout is tried. When nothing passes, make() raises ThumbsFailed and the caller uses
the old frame thumbnails. Same script = same JPGs (no randomness, fixed fonts, software rendering).
"""

import glob
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image

from .. import config as C
from ..util import PipelineError
from . import brief as Bf
from . import design as Ds
from . import layouts as Ly

VERSION = 3                                 # bump when the look changes: previews are cached by brief + version
SHOOT = Path(__file__).with_name("shoot.mjs")
PREVIEWS = C.BASE_DIR / "output" / "thumb_previews"
WANT = 3
MAX_BYTES = 2_000_000


class ThumbsFailed(PipelineError):
    pass


def chrome_path() -> str:
    """HyperFrames' headless Chromium (installed by setup.sh: npm ci + the first HyperFrames run)."""
    env = C.env("HYPERFRAMES_BROWSER_PATH")
    if env and Path(env).exists():
        return env
    exe = "chrome-headless-shell.exe" if os.name == "nt" else "chrome-headless-shell"
    found = sorted(glob.glob(str(Path.home() / ".cache" / "hyperframes" / "chrome" / "chrome-headless-shell" / "*" /
                                 "*" / exe)))
    if not found:
        raise ThumbsFailed("the headless Chromium isn't installed. Run once in the project folder: npm ci, then make "
                           "any motion-graphics draft (HyperFrames downloads it)")
    return found[-1]


def _shoot(pages: list) -> list:
    node = shutil.which("node")
    if not node:
        raise ThumbsFailed("Node.js isn't installed: brew install node")
    work = pages[0]["html"].rsplit("/", 1)[0]
    jobf = Path(work) / "shoot.json"
    jobf.write_text(json.dumps({"chrome": chrome_path(), "pages": pages}), encoding="utf-8")
    p = subprocess.run([node, str(SHOOT), str(jobf)], capture_output=True, text=True, cwd=str(C.BASE_DIR), timeout=180)
    if p.returncode != 0:
        raise ThumbsFailed("thumbnail screenshot failed: " + (p.stderr.strip().splitlines() or ["?"])[-1][:300])
    return json.loads(p.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------------------------------------------ rules
def _inter(a, b, pad=3):
    return not (a["x"] + a["w"] <= b["x"] + pad or b["x"] + b["w"] <= a["x"] + pad or
                a["y"] + a["h"] <= b["y"] + pad or b["y"] + b["h"] <= a["y"] + pad)


def check(boxes: list, spec: dict, W: int, H: int, vertical: bool, jpg: Path = None) -> list:
    """Every rule of the plan; returns the list of what failed (empty = pass)."""
    bad = []
    by = {}
    for bx in boxes:
        by.setdefault(bx["role"], []).append(bx)
    head = (by.get("headline") or [None])[0]
    if not head:
        return ["no headline"]
    words = (head.get("words") or 0) + sum(bx.get("words") or 0 for bx in by.get("label", []))
    if words > Bf.MAX_WORDS:
        bad.append(f"big text has {words} words (max {Bf.MAX_WORDS})")
    scale = (320 / W) if not vertical else (180 / W)
    cap = head["cap"] * scale
    if cap < 18:
        bad.append(f"headline cap height {cap:.1f} px at {'320x180' if not vertical else '180x320'} (min 18)")
    for t in spec["texts"]:
        c = Ds.contrast(t["fill"], t["bg"])
        if t["stroke"] >= 0.04:
            c = max(c, Ds.contrast(t["fill"], t["outline"]))
        if c < 4.5:
            bad.append(f"{t['role']} contrast {c:.2f} (min 4.5)")
    important = [bx for bx in boxes if bx["role"] in spec["important"]]
    if not vertical:
        zone = {"x": W * 0.78, "y": H * 0.82, "w": W * 0.22, "h": H * 0.18}
        for bx in important:
            if _inter(bx, zone, 0):
                bad.append(f"{bx['role']} is in the duration-badge corner")
    else:
        for bx in important:
            if bx["role"] in ("headline", "number", "stamp") and (bx["y"] < 420 - 2 or bx["y"] + bx["h"] > 1500 + 2):
                bad.append(f"{bx['role']} outside the centre square (y {bx['y']:.0f}-{bx['y'] + bx['h']:.0f})")
    for bx in boxes:
        if bx.get("overflow"):
            bad.append(f"{bx['role']} text overflows its box")
        if bx["role"] in spec["important"] or bx["role"] in ("label", "side_l", "side_r", "vs"):
            if bx["x"] < -2 or bx["y"] < -2 or bx["x"] + bx["w"] > W + 2 or bx["y"] + bx["h"] > H + 2:
                bad.append(f"{bx['role']} goes off the picture")
        if bx is not head and _inter(bx, head):
            bad.append(f"{bx['role']} overlaps the headline")
    if jpg is not None and jpg.exists() and jpg.stat().st_size >= MAX_BYTES:
        bad.append(f"JPG is {jpg.stat().st_size / 1e6:.2f} MB (max 2)")
    return sorted(set(bad))


# ------------------------------------------------------------------------------------------------ making
def _candidates(b: dict) -> list:
    order = Ly.fit_order(b)
    out = [(n, {}) for n in order]
    # spares, used only when fewer than 3 different layouts pass: mirrored versions
    if "hero_icon" in order:
        out.append(("hero_icon", {"second": True}))           # the second icon (or the same one), mirrored
    out.append(("stamp", {"second": True}))
    return out


def _theme(b: dict) -> dict:
    th = Ds.theme(b["look"], b["title"])
    names = [c for c in (Ds.mix(th["accent"], "#38E1FF", 0.6), "#FFD21F", "#38E1FF")
             if Ds.contrast(c, th["base"]) >= 4.5 and c != th["accent"]]
    th["accent2"] = names[0] if names else "#FFFFFF"
    return th


def build(parsed: dict, out_dir: Path, prefix: str = "thumb_", log=None) -> dict:
    """All candidate layouts drawn, shot and checked; the first WANT that pass are saved as prefix1..3.jpg."""
    t0 = time.time()
    out_dir = Path(out_dir).resolve()
    work = out_dir / "thumb_work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    b = Bf.brief(parsed)
    th = _theme(b)
    vertical = b["type"] == "short"
    W, H = (Ly.W916, Ly.H916) if vertical else (Ly.W169, Ly.H169)
    specs, pages = [], []
    for k, (name, kw) in enumerate(_candidates(b)):
        spec = Ly.BUILDERS[name](b, th, vertical, **kw)
        if not spec:
            continue
        html = work / f"c{k}_{name}.html"
        html.write_text(Ds.page(W, H, th, spec["html"]), encoding="utf-8")
        pages.append({"html": html.as_posix(), "png": (work / f"c{k}_{name}.png").as_posix(), "w": W, "h": H})
        specs.append((name, kw, spec))
    if not pages:
        raise ThumbsFailed("no layout fits this script")
    shots = _shoot(pages)
    options, failed = [], []
    for (name, kw, spec), shot in zip(specs, shots):
        label = name + (" (mirrored)" if kw.get("second") else "")
        if shot.get("error"):
            failed.append({"layout": label, "why": [shot["error"]]})
            continue
        jpg = work / (Path(shot["png"]).stem + ".jpg")
        t1 = time.time()
        Image.open(shot["png"]).convert("RGB").save(jpg, "JPEG", quality=90, optimize=False, progressive=False)
        why = check(shot["boxes"], spec, W, H, vertical, jpg)
        ms = shot["ms"] + int((time.time() - t1) * 1000)
        if why:
            failed.append({"layout": label, "why": why})
        else:
            options.append({"layout": label, "jpg": jpg, "ms": ms})
    # 3 options with different layouts first; a spare variant only when there aren't 3 layouts
    chosen = [o for o in options if "(" not in o["layout"]][:WANT]
    chosen += [o for o in options if o not in chosen][:WANT - len(chosen)]
    if not chosen:
        raise ThumbsFailed("every layout failed the rules: " + "; ".join(f"{f['layout']}: {', '.join(f['why'])}"
                                                                         for f in failed))
    files = []
    for k, o in enumerate(chosen, start=1):
        dst = out_dir / f"{prefix}{k}.jpg"
        shutil.copyfile(o["jpg"], dst)
        files.append({"file": dst.name, "layout": o["layout"], "ms": o["ms"], "kb": round(dst.stat().st_size / 1024)})
    for k in range(len(chosen) + 1, WANT + 1):                 # no stale option from an earlier run
        (out_dir / f"{prefix}{k}.jpg").unlink(missing_ok=True)
    rep = {"options": files, "failed": failed, "seconds": round(time.time() - t0, 2), "size": [W, H],
           "brief": {k: b[k] for k in ("headline", "headline_full", "number", "number_label", "tag", "stamp", "icons",
                                       "versus", "versus_icons", "pose", "family", "layout_pin", "notes")},
           "look": {k: b["look"].get(k) for k in ("format", "palette", "fonts", "icons", "icon_style")},
           "theme": {"accent": th["accent"], "bg": th["bg"], "head": th["head"]}}
    (out_dir / f"{prefix}report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    if log:
        log(f"thumbnails (designed, {'9:16' if vertical else '16:9'}): " +
            ", ".join(f"{o['file']} {o['layout']} {o['ms']} ms" for o in files) +
            (f"; dropped: " + "; ".join(f"{f['layout']} ({', '.join(f['why'])})" for f in failed) if failed else "") +
            f"; {rep['seconds']} s")
    return rep


def make(parsed: dict, job_dir: Path, log=None) -> list:
    """The final render's thumbnails: thumb_1..3.jpg in the job folder. Returns the file names."""
    rep = build(parsed, job_dir, "thumb_", log)
    return [o["file"] for o in rep["options"]]


def preview_key(parsed: dict) -> str:
    b = Bf.brief(parsed)
    raw = json.dumps({k: v for k, v in b.items() if k != "notes"}, sort_keys=True, default=str)
    return hashlib.sha1(f"v{VERSION}|{raw}".encode()).hexdigest()[:16]


def preview(parsed: dict) -> dict:
    """The Check page's options (cached by the brief: the same brief is drawn once)."""
    key = preview_key(parsed)
    d = PREVIEWS / key
    rp = d / "thumb_report.json"
    if rp.exists():
        rep = json.loads(rp.read_text(encoding="utf-8"))
        rep["cached"] = True
    else:
        d.mkdir(parents=True, exist_ok=True)
        rep = build(parsed, d, "thumb_")
        rep["cached"] = False
    rep["key"] = key
    return rep
