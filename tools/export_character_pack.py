"""
export_character_pack.py  -  zip a finished character pack so another machine (e.g. the Windows Legion) can use it.

    bin/python tools/export_character_pack.py sterling
    -> output/character_packs/sterling-pack-20261109.zip   (~200 MB; PNGs are stored, not re-compressed)

The zip holds the pack folder (master, poses with mouths/blink/cutouts, sets, pack.json with paths made relative),
the character file docs/characters/<id>.md, and manifest.json with a SHA-256 for every file.
Import it on the other machine with:  python tools/import_character_pack.py <zip>
"""

import argparse
import hashlib
import json
import platform
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import characters  # noqa: E402

FORMAT = 1
SKIP_SUFFIXES = {".log"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def portable_pack(pack: dict, name: str) -> dict:
    """pack.json with every path relative to the pack folder (no /Users/... from this machine)."""
    def rel(p):
        q = characters.pack_path(name, p)
        try:
            return q.relative_to(characters.pack_dir(name)).as_posix()
        except ValueError:
            return Path(str(p)).name      # e.g. candidates in the shared image cache: name only
    out = json.loads(json.dumps(pack))
    out["doc"] = f"docs/characters/{name}.md"
    for pose in out.get("poses", {}).values():
        if "dir" in pose:
            pose["dir"] = rel(pose["dir"])
        for c in (pose.get("candidates") or {}).values():
            if isinstance(c, dict) and "file" in c:
                c["file"] = rel(c["file"])
        for shp in (pose.get("shapes") or {}).values():
            for c in (shp.get("candidates") or []) if isinstance(shp, dict) else []:
                if isinstance(c, dict) and "file" in c:
                    c["file"] = rel(c["file"])
    for st in out.get("sets", {}).values():
        if "file" in st:
            st["file"] = rel(st["file"])
        st["candidates"] = [rel(c) for c in st.get("candidates", [])]
    return out


def check_complete(name: str, pack: dict):
    """Every file the renderer needs, or a list of what's missing."""
    d = characters.pack_dir(name)
    need = [d / "master.png"]
    for pose, info in pack.get("poses", {}).items():
        if "dir" not in info:
            need.append(d / f"pose_{pose} (not built)")
            continue
        pd = characters.pack_path(name, info["dir"])
        need += [pd / "alpha.png", pd / "blink_cut.png"] + [pd / f"{s}_cut.png" for s in characters.MOUTHS]
    for st in pack.get("sets", {}).values():
        need.append(characters.pack_path(name, st["file"]))
    return [str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p) for p in need if not p.exists()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("character", help="character id, e.g. sterling")
    ap.add_argument("--out", default=str(ROOT / "output" / "character_packs"), help="folder for the zip")
    a = ap.parse_args()
    name = a.character.strip().lower()
    d = characters.pack_dir(name)
    doc = characters.DOCS / f"{name}.md"
    if not (d / "pack.json").exists():
        sys.exit(f"no pack for '{name}' (assets/characters/{name}/pack.json). Build it: tools/make_character_pack.py {name}")
    if not doc.exists():
        sys.exit(f"no character file docs/characters/{name}.md")
    pack = json.loads((d / "pack.json").read_text(encoding="utf-8"))
    missing = check_complete(name, pack)
    if missing:
        sys.exit("the pack isn't complete, missing:\n  " + "\n  ".join(missing[:20]))
    files = sorted(p for p in d.rglob("*") if p.is_file() and p.suffix not in SKIP_SUFFIXES
                   and p.name != "pack.json" and not p.name.startswith("."))
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    zp = out_dir / f"{name}-pack-{time.strftime('%Y%m%d')}.zip"
    t0 = time.time()
    manifest = {"format": FORMAT, "character": name, "exported": time.strftime("%Y-%m-%d %H:%M"),
                "exported_on": f"{platform.system()} {platform.machine()}", "files": {}}
    tmp = zp.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in files:
            arc = f"pack/{p.relative_to(d).as_posix()}"
            z.write(p, arc)
            manifest["files"][arc] = sha256(p)
        pj = json.dumps(portable_pack(pack, name), indent=1).encode("utf-8")
        z.writestr("pack/pack.json", pj)
        manifest["files"]["pack/pack.json"] = hashlib.sha256(pj).hexdigest()
        z.write(doc, "character.md")
        manifest["files"]["character.md"] = sha256(doc)
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
    tmp.replace(zp)
    print(f"exported {name}: {len(manifest['files'])} files, {zp.stat().st_size / 1e6:.0f} MB in {time.time() - t0:.0f}s")
    print(f"-> {zp}")
    print("On the other machine:  python tools/import_character_pack.py <that zip>")


if __name__ == "__main__":
    main()
