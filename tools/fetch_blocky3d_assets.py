"""Download the CC0 3D packs of the blocky3d style into assets/blocky3d/<category>/<pack>/ and index them.

    bin/python tools/fetch_blocky3d_assets.py           # download what's missing, verify, (re)build index.json
    bin/python tools/fetch_blocky3d_assets.py --check   # verify only (exit 1 if a pack is missing or changed)

Sources: Kenney's packs (CC0 1.0, kenney.nl) as published by Kenney on OpenGameArt, pinned by URL + SHA-256 in
assets/blocky3d/packs.json. Zips are cached in output/blocky3d_cache/. Kept per pack: the models (GLB, else OBJ+MTL,
animated-characters: FBX + skins), their Textures/, License.txt, preview.png. The models are not in git (rebuilt by
this tool / setup.sh); packs.json, README.md and CREDITS.md are.
"""

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "assets" / "blocky3d"
CACHE = ROOT / "output" / "blocky3d_cache"
PACKS = BASE / "packs.json"
MODEL_EXT = {".glb", ".gltf", ".bin", ".obj", ".mtl", ".fbx"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def words(name: str):
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", Path(name).stem)
    return [w for w in re.split(r"[\s_\-().]+", name.lower()) if w and not w.isdigit() and len(w) > 1]


def model_dir(names):
    """The folder of the best format in a Kenney zip: GLB, else glTF, else OBJ, else FBX."""
    for ext in (".glb", ".gltf", ".obj", ".fbx"):
        dirs = sorted({n.rsplit("/", 1)[0] if "/" in n else "" for n in names if n.lower().endswith(ext)})
        if dirs:
            return ext, dirs
    raise SystemExit("no 3D models in this zip")


def glb_info(path: Path):
    """(ok, animation names) from a GLB's JSON chunk; ok = valid header + every external file present."""
    b = path.read_bytes()
    if b[:4] != b"glTF" or struct.unpack("<I", b[8:12])[0] != len(b):
        return False, []
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    uris = [x["uri"] for x in j.get("images", []) + j.get("buffers", []) if "uri" in x]
    ok = all((path.parent / u).exists() for u in uris if not u.startswith("data:"))
    return ok, [a.get("name", "") for a in j.get("animations", [])]


def extract(pack, zpath: Path, dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "models").mkdir(parents=True)
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        if pack.get("keep"):                       # explicit folders (animated characters: Model/, Animations/, Skins/)
            take = [n for n in names if n.split("/")[0] in pack["keep"] and not n.lower().endswith(".svg")]
            strip = ""
        else:
            ext, dirs = model_dir(names)
            d = dirs[0]
            strip = d + "/" if d else ""
            take = [n for n in names if n.startswith(strip) and "/" not in n[len(strip):]
                    and Path(n).suffix.lower() in MODEL_EXT]
            take += [n for n in names if n.startswith(strip + "Textures/") and n.lower().endswith(".png")]
            if ext in (".obj", ".fbx"):            # OBJ packs keep textures beside the models
                take += [n for n in names if n.startswith(strip) and "/" not in n[len(strip):]
                         and n.lower().endswith(".png")]
        for n in sorted(set(take)):
            out = dest / "models" / n[len(strip):]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(n))
        lic = next(n for n in names if n.lower().endswith("license.txt"))
        (dest / "License.txt").write_bytes(z.read(lic))
        prev = next((n for n in names if "/" not in n and n.lower().startswith("preview") and n.endswith(".png")), None)
        if prev:
            (dest / "preview.png").write_bytes(z.read(prev))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    spec = json.loads(PACKS.read_text(encoding="utf-8"))
    CACHE.mkdir(parents=True, exist_ok=True)
    problems, packs_out, models_out = [], [], []
    for p in spec["packs"]:
        if p.get("build"):                         # own pack made by code (no download): build it when missing
            dest = BASE / p["dir"]
            if not a.check and not (dest / "models").is_dir():
                print(f"build {p['id']} ...")
                subprocess.run([sys.executable, "-I", str(ROOT / p["build"])], check=True)
            zpath = None
        else:
            dest = BASE / p["category"] / p["id"]
            zpath = CACHE / p["zip"]
        if zpath and not a.check and not zpath.exists():
            print(f"download {p['id']} ...")
            req = urllib.request.Request(p["url"], headers={"User-Agent": "video-studio-asset-fetch"})
            with urllib.request.urlopen(req, timeout=120) as r, open(zpath, "wb") as f:
                shutil.copyfileobj(r, f)
        if zpath and zpath.exists() and sha256(zpath) != p["sha256"]:
            problems.append(f"{p['id']}: {zpath.name} SHA-256 differs from packs.json (changed upstream?)")
            continue
        if zpath and not a.check and zpath.exists() and not (dest / "License.txt").exists():
            extract(p, zpath, dest)
        if not (dest / "License.txt").exists():
            problems.append(f"{p['id']}: not downloaded yet ({dest.relative_to(ROOT)})")
            continue
        lic = (dest / "License.txt").read_text(encoding="utf-8", errors="replace")
        if p["licence"] == "CC0-1.0" and "CC0" not in lic and "Creative Commons Zero" not in lic:
            problems.append(f"{p['id']}: License.txt doesn't say CC0")
        n = 0
        for f in sorted((dest / "models").rglob("*")):
            if f.suffix.lower() not in {".glb", ".gltf", ".obj", ".fbx"} or (p.get("keep") and f.parent.name == "Skins"):
                continue
            ok, anims = glb_info(f) if f.suffix.lower() == ".glb" else (True, [])
            if not ok:
                problems.append(f"{p['id']}: {f.name} is not a valid GLB or misses a texture")
            n += 1
            models_out.append({"id": f"{p['id']}/{f.stem}", "pack": p["id"], "category": p["category"],
                               "file": f.relative_to(BASE).as_posix(), "format": f.suffix.lower()[1:],
                               "tags": sorted(set(words(f.name)) | set(p["tags"])), "animations": anims})
        packs_out.append({k: p[k] for k in ("id", "category", "title", "page", "author", "licence", "tags")} |
                         {"models": n, "preview": (dest / "preview.png").relative_to(BASE).as_posix()
                          if (dest / "preview.png").exists() else None})
    if not a.check:
        (BASE / "index.json").write_text(json.dumps({"packs": packs_out, "models": models_out}, indent=1),
                                         encoding="utf-8")
    size = sum(f.stat().st_size for f in BASE.rglob("*") if f.is_file()) / 1e6
    print(f"blocky3d assets: {len(packs_out)} packs, {len(models_out)} models, {size:.1f} MB")
    for m in problems:
        print("  PROBLEM", m)
    print("blocky3d assets: clean" if not problems else "blocky3d assets: PROBLEMS")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
