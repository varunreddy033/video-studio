"""
import_character_pack.py  -  install a character pack zip made by tools/export_character_pack.py, after checking it.

    bin/python tools/import_character_pack.py sterling-pack-20261109.zip            (Mac)
    .\\Scripts\\python tools\\import_character_pack.py sterling-pack-20261109.zip     (Windows)

Checks, before anything is written:
  1 every file's SHA-256 matches manifest.json (a broken or half-copied zip is refused)
  2 pack.json is complete: master, every pose's mouths + blink + cutouts + alpha + eye box, every set
  3 the zip's character file matches docs/characters/<id>.md here (CHARACTER/STYLE/SEED drive how [act:] scenes
    look; a different file means a different-looking character). --force accepts the zip's version.
Then it unpacks into assets/characters/<id>/. An existing pack there is moved to assets/characters/_backup/
(never deleted), and only with --force.
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import characters  # noqa: E402

FORMAT = 1


def fail(msg):
    sys.exit(f"IMPORT REFUSED: {msg}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", help="the pack zip from export_character_pack.py")
    ap.add_argument("--force", action="store_true",
                    help="replace an existing pack (moved to _backup) / accept a different character file")
    a = ap.parse_args()
    zp = Path(a.zip)
    if not zp.exists():
        fail(f"no file {zp}")
    t0 = time.time()
    try:
        z = zipfile.ZipFile(zp)
    except zipfile.BadZipFile:
        fail(f"{zp.name} isn't a valid zip (damaged or not finished copying)")
    with z:
        names = set(z.namelist())
        for n in names:    # nothing may escape the pack folder
            pp = PurePosixPath(n)
            if pp.is_absolute() or ".." in pp.parts or "\\" in n or ":" in n:
                fail(f"unsafe path in zip: {n}")
        if "manifest.json" not in names:
            fail("no manifest.json (was this made by export_character_pack.py?)")
        man = json.loads(z.read("manifest.json"))
        if man.get("format") != FORMAT:
            fail(f"unknown pack format {man.get('format')}")
        name = man.get("character", "")
        try:
            characters.load.cache_clear()
        except AttributeError:
            pass
        if not name or not all(c.isalnum() or c in "_-" for c in name):
            fail(f"bad character id '{name}'")

        # 1 checksums
        extra = names - set(man["files"]) - {"manifest.json"}
        missing = set(man["files"]) - names
        if missing:
            fail(f"{len(missing)} files listed in the manifest are missing, e.g. {sorted(missing)[0]}")
        if extra:
            fail(f"files not in the manifest: {sorted(extra)[:3]}")
        for n, want in man["files"].items():
            h = hashlib.sha256()
            try:
                with z.open(n) as f:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        h.update(chunk)
            except (zipfile.BadZipFile, OSError) as e:
                fail(f"{n} can't be read ({e}): the zip is damaged; copy it again")
            if h.hexdigest() != want:
                fail(f"checksum mismatch for {n}: the zip is damaged; copy it again")
        print(f"checksums OK ({len(man['files'])} files)")

        # 2 pack.json completeness
        pack = json.loads(z.read("pack/pack.json"))
        if pack.get("character") != name:
            fail(f"pack.json is for '{pack.get('character')}', manifest says '{name}'")
        need = ["pack/master.png"]
        for pose, info in pack.get("poses", {}).items():
            if "dir" not in info or "eye_box" not in info:
                fail(f"pose '{pose}' isn't finished in pack.json")
            pd = f"pack/{info['dir']}"
            need += [f"{pd}/alpha.png", f"{pd}/blink_cut.png"] + [f"{pd}/{s}_cut.png" for s in characters.MOUTHS]
        if not pack.get("sets"):
            fail("pack.json has no sets")
        need += [f"pack/{st['file']}" for st in pack["sets"].values()]
        lost = [n for n in need if n not in names]
        if lost:
            fail(f"pack.json names files that aren't in the zip, e.g. {lost[:3]}")
        print(f"pack.json OK ({len(pack['poses'])} poses, {len(pack['sets'])} sets)")

        # 3 character file
        doc = characters.DOCS / f"{name}.md"
        zdoc = z.read("character.md")
        if doc.exists() and doc.read_bytes().replace(b"\r\n", b"\n") != zdoc.replace(b"\r\n", b"\n"):
            if not a.force:
                fail(f"docs/characters/{name}.md here differs from the one the pack was built from. "
                     f"Pull the repo (git pull) so both machines match, or use --force to install the zip's version")
            bdoc = doc.with_suffix(f".md.before-import-{time.strftime('%Y%m%d-%H%M%S')}")
            shutil.copy2(doc, bdoc)
            print(f"character file differs: kept yours as {bdoc.name}, installing the pack's version")
        dest = characters.pack_dir(name)
        if dest.exists() and any(dest.iterdir()):
            if not a.force:
                fail(f"assets/characters/{name}/ already exists. Add --force to replace it "
                     f"(the old one is moved to assets/characters/_backup/, not deleted)")

        # unpack into a temp folder next to the destination, then swap
        tmp = dest.parent / f".{name}-import"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        for n in sorted(names):
            if not n.startswith("pack/") or n.endswith("/"):
                continue
            out = tmp.joinpath(*PurePosixPath(n).parts[1:])
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
    if dest.exists() and any(dest.iterdir()):
        bk = dest.parent / "_backup" / f"{name}-{time.strftime('%Y%m%d-%H%M%S')}"
        bk.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(bk))
        print(f"old pack moved to {bk.relative_to(ROOT)}")
    elif dest.exists():
        dest.rmdir()
    tmp.rename(dest)
    if not doc.exists() or a.force:
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_bytes(zdoc)

    # final check with the renderer's own loader
    from pipeline import presenter
    presenter._pack.cache_clear()
    if not presenter.pack_ready(name):
        fail("unpacked, but the renderer doesn't see a finished pack (please report this)")
    print(f"imported {name} into assets/characters/{name}/ in {time.time() - t0:.0f}s. Ready to render.")


if __name__ == "__main__":
    main()
