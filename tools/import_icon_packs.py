"""
import_icon_packs.py  -  pinned npm icon packages -> assets/library/icons/<set>/ (docs/ASSET_PACKS_PLAN.md step 1)

    npm ci                                         (installs the pinned @iconify-json packages, package-lock.json)
    bin/python tools/import_icon_packs.py          import every pack in pipeline/icon_library.PACKS
    bin/python tools/import_icon_packs.py noto     only that pack
    bin/python tools/import_icon_packs.py --check  import nothing; exit 1 if a pack is missing or stale
    bin/python tools/import_icon_packs.py --discover 2.2.555
                                                   read EVERY Iconify set from @iconify/json@<version>'s
                                                   collections.json, sort them (import / refused + why, kind,
                                                   role) into assets/library/icons/packs.json, npm-install the
                                                   new ones at exact versions, then import everything

Kinds: illustration (colour illustration / emoji), flat (one-colour filled), line (one-colour stroke, Iconify tag
"Uses Stroke"), flag, map. Role "family" (can be a video's main icon family) = an illustration set of 1,000+ icons
in a general category (Emoji, UI Multicolor, High Detail Multicolor, Apps), not archived. Brand / logo sets (Iconify
categories Logos and Programming, "*-brands") are never imported, and icon names with brand / logo in them are
dropped from every pack (trademarks).

Every pack's licence (the package's own info.json) is checked against a strict allow-list: MIT, Apache-2.0, ISC,
CC0, public domain; CC BY 4.0 only with ALLOW_CC_BY=1 in .env. Anything else is REFUSED. Each imported pack gets
  assets/library/icons/<set>/icons.json   the icons (not in git: rebuilt from the pinned packages)
  assets/library/icons/<set>/LICENCE      the full licence text (in git)
and a row in assets/library/icons/CREDITS.md and the project's NOTICE file. Skin-tone variants are left out
(the default yellow one is kept), and only the fill + duotone weights of Phosphor and the 4x3 flags are taken.
Natural Earth country shapes come from motion/src/library/worldmap.json (tools/make_worldmap.py, public domain).
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import icon_library as L  # noqa: E402
from pipeline.util import PipelineError  # noqa: E402

PUBLIC_DOMAIN = """Natural Earth country shapes (1:110m Admin 0 - Countries)

Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com.

All versions of Natural Earth raster + vector map data found on its website are in the public domain. You may use
the maps in any manner, including modifying the content and design, electronic dissemination, and offset printing.
No permission is needed to use Natural Earth and crediting the authors is unnecessary.
Source: https://www.naturalearthdata.com/about/terms-of-use/
"""


IMPORT_ROLES = {"Emoji", "UI Multicolor", "High Detail Multicolor", "Apps"}
BRAND_CATEGORIES = {"Logos", "Programming"}
OLD_IDS = {v["npm"]: k for k, v in L.PACKS.items() if v.get("npm") and k in L.KINDS}   # the hand-picked packs


def _keep(set_id, name, names):
    if L.BRAND_NAME.search(name):
        return False
    if set_id == "phosphor":
        return name.endswith("-fill") or name.endswith("-duotone")
    if set_id == "flags":
        return name.endswith("-4x3")
    if set_id in ("noto", "twemoji"):
        return "skin-tone" not in name
    if set_id in ("fluent_flat", "fluent_color"):
        for s in L.SKIN:                          # "x-dark" is a skin tone only if "x" and "x-medium-dark" exist too
            if name.endswith(s) and name[:-len(s)] in names and name[:-len(s)] + "-medium-dark" in names:
                return False
    return True


def _get(url: str) -> str:
    """Downloads a small text file. curl first: on some networks Python's urllib waits ~30 s per request (it tries
    IPv6 before IPv4), which made importing ~180 packs take hours."""
    import shutil
    import subprocess
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", url)
    if m and not url.endswith("?raw"):
        # the same file through jsDelivr's GitHub mirror (raw.githubusercontent.com throttles long runs to ~75 s
        # a file); falls back to GitHub itself
        try:
            return _get(f"https://cdn.jsdelivr.net/gh/{m.group(1)}/{m.group(2)}@{m.group(3)}/{m.group(4)}")
        except Exception:  # noqa: BLE001
            return _get(url + "?raw")
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-sSfL", "--max-time", "30", "-A", "video-studio-setup", url],
                           capture_output=True, timeout=40)
        if r.returncode:
            raise PipelineError(r.stderr.decode("utf-8", "replace").strip() or f"curl exit {r.returncode}")
        return r.stdout.decode("utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": "video-studio-setup"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


def _raw_url(url: str) -> str:
    """github.com/<o>/<r>/blob/<ref>/<path> -> the raw file."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/(.+)$", url or "")
    return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else (url or "")


def _looks_like_licence(text: str) -> bool:
    head = text[:400].lower()
    return len(text) >= 200 and "<html" not in head and "<!doctype" not in head


def _licence_text(set_id, pack, dest: Path, info: dict = None) -> None:
    """The pack's own licence file; when upstream only links a licence page, the standard SPDX text of that licence
    with the pack's author and source on top."""
    if dest.exists() and dest.stat().st_size > 200:
        return
    url = pack.get("licence_url") or ""
    try:
        text = _get(url) if url else ""
    except Exception as e:  # noqa: BLE001
        text, err = "", e
    else:
        err = None
    if not _looks_like_licence(text) and info:
        spdx = (info.get("license") or {}).get("spdx", "")
        try:
            std = _get(f"https://raw.githubusercontent.com/spdx/license-list-data/main/text/{spdx}.txt")
        except Exception as e:  # noqa: BLE001
            std, err = "", e
        if _looks_like_licence(std):
            a = info.get("author") or {}
            text = (f"{info.get('name', set_id)} by {a.get('name', '?')} ({a.get('url', '')})\n"
                    f"Licence: {spdx}, as stated by the pack ({(info.get('license') or {}).get('url', '')}).\n"
                    f"Upstream links a licence page rather than a file, so this is the standard {spdx} text\n"
                    f"(SPDX license-list-data); the copyright holder is the author above.\n\n" + std)
    if not _looks_like_licence(text):
        raise PipelineError(f"{set_id}: couldn't get the licence text ({url}): {err or 'not a licence file'}. "
                            f"A pack is never imported without its LICENCE file.")
    dest.write_text(text, encoding="utf-8")


def import_npm(set_id: str) -> dict:
    pack = L.PACKS[set_id]
    src = L.NPM_DIR / pack["npm"]
    if not (src / "icons.json").exists():
        raise PipelineError(f"{set_id}: @iconify-json/{pack['npm']} isn't installed. Run in the project folder: npm ci")
    info = json.loads((src / "info.json").read_text(encoding="utf-8"))
    version = json.loads((src / "package.json").read_text(encoding="utf-8"))["version"]
    spdx = (info.get("license") or {}).get("spdx", "")
    L.check_licence(spdx, f"icon pack {set_id} (@iconify-json/{pack['npm']})")      # raises = refused
    data = json.loads((src / "icons.json").read_text(encoding="utf-8"))
    names = set(data["icons"])
    icons = {}
    for name, ic in data["icons"].items():
        if ic.get("hidden") or not _keep(set_id, name, names):
            continue
        row = {"b": ic["body"]}
        if ic.get("width") and ic["width"] != data.get("width"):
            row["w"] = ic["width"]
        if ic.get("height") and ic["height"] != data.get("height"):
            row["h"] = ic["height"]
        icons[name] = row
    out = L.ICONS_DIR / set_id
    out.mkdir(parents=True, exist_ok=True)
    _licence_text(set_id, pack, out / "LICENCE", info)
    meta = {"set": set_id, "label": pack["label"], "role": pack["role"], "kind": pack.get("kind", ""),
            "category": info.get("category", ""), "source": f"@iconify-json/{pack['npm']}@{version}",
            "upstream": (info.get("author") or {}).get("url", ""), "author": (info.get("author") or {}).get("name", ""),
            "licence": spdx, "licence_page": (info.get("license") or {}).get("url", ""),
            "attribution_required": L.ALLOWED[spdx] == "by", "width": data.get("width", 16),
            "height": data.get("height", data.get("width", 16)), "count": len(icons), "icons": icons}
    (out / "icons.json").write_text(json.dumps(meta, separators=(",", ":")), encoding="utf-8")
    return meta


def import_natural_earth() -> dict:
    src = ROOT / "motion" / "src" / "library" / "worldmap.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    L.check_licence("public-domain", "Natural Earth country shapes")
    icons = {}
    for c in data["countries"]:
        slug = re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-")
        icons[slug] = {"b": f'<path fill="currentColor" d="{c["d"]}"/>', "name": c["name"], "iso": c.get("iso", ""),
                       "d": c["d"], "label": c.get("label")}
    out = L.ICONS_DIR / "natural_earth"
    out.mkdir(parents=True, exist_ok=True)
    (out / "LICENCE").write_text(PUBLIC_DOMAIN, encoding="utf-8")
    meta = {"set": "natural_earth", "label": L.PACKS["natural_earth"]["label"], "role": "map",
            "source": "Natural Earth 1:110m admin 0 countries (tools/make_worldmap.py)",
            "upstream": "https://www.naturalearthdata.com", "author": "Natural Earth", "licence": "public-domain",
            "licence_page": "https://www.naturalearthdata.com/about/terms-of-use/", "attribution_required": False,
            "width": data["width"], "height": data["height"], "count": len(icons), "icons": icons}
    (out / "icons.json").write_text(json.dumps(meta, separators=(",", ":")), encoding="utf-8")
    return meta


def write_credits() -> None:
    """CREDITS.md + the icon block of NOTICE from the packs that are imported (their LICENCE files are in git)."""
    rows, notice = [], []
    for set_id in L.PACKS:
        p = L.ICONS_DIR / set_id / "icons.json"
        if not p.exists():
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        credit = "YES: added to every description automatically" if m["attribution_required"] else "not required"
        rows.append(f"| {set_id} | {m['label']} | {m.get('kind') or L.PACKS[set_id].get('kind', '')} | "
                    f"{L.PACKS[set_id]['role']} | {m['count']:,} | {m['licence']} | {m['author']} | {m['upstream']} | "
                    f"{m['source']} | {credit} | icons/{set_id}/LICENCE |")
        owner = "Public domain, made by" if m["licence"] == "public-domain" else "Copyright"
        notice.append(f"- {m['label']}: {owner} {m['author']}. Licence: {m['licence']} "
                      f"(assets/library/icons/{set_id}/LICENCE). Source: {m['upstream']}")
    (L.ICONS_DIR / "CREDITS.md").write_text(
        "# Icon packs in assets/library/icons\n\n"
        "Written by tools/import_icon_packs.py. Only packs whose licence is on the allow-list are imported: MIT,\n"
        "Apache-2.0, ISC, CC0, public domain; CC BY 4.0 only with ALLOW_CC_BY=1 in .env (credit line added to the\n"
        "video description automatically). Skipped on purpose: OpenMoji (CC BY-SA 4.0), brand logos, anything\n"
        "without a clear licence file. Emoji keywords for the search index: emojilib 4.0.3 (MIT) and\n"
        "unicode-emoji-json 0.9.0 (MIT). Search model: sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0).\n\n"
        "Kinds: illustration = colour illustration / emoji (only role 'family' can be a video's main icon family),\n"
        "flat = one-colour filled, line = one-colour stroke (small labels), flag, map. Brand / logo sets are never\n"
        "imported and icon names with brand / logo in them are dropped (trademarks).\n\n"
        "| Id | Pack | Kind | Role | Icons | Licence | Author | Upstream | Imported from | Credit in the video | Licence file |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n" + refused_table(), encoding="utf-8")
    # NOTICE is hand-written; only the block between the two marker lines belongs to this tool
    start, end = "ICON PACKS (written by tools/import_icon_packs.py; don't edit this block by hand)", "END OF ICON PACKS"
    block = (start + "\nUsed by the motion-graphics renderer. The icons are installed by setup.sh from pinned npm packages\n"
             "(not included in this repository); each pack's full licence text is included next to where it is imported.\n"
             + "\n".join(notice) +
             "\n- Noto Emoji is licensed under the Apache License, Version 2.0; those files may only be used in\n"
             "  compliance with that License (copy: assets/library/icons/noto/LICENCE).\n"
             "- Emoji keyword data for the icon search: emojilib (MIT), unicode-emoji-json (MIT). Search model:\n"
             "  sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0), downloaded by setup.sh.\n" + end)
    p = ROOT / "NOTICE"
    text = p.read_text(encoding="utf-8") if p.exists() else "Video Studio\n"
    if start in text and end in text:
        text = text[:text.index(start)] + block + text[text.index(end) + len(end):]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    p.write_text(text, encoding="utf-8")


def refused_table() -> str:
    reg = L.registry()
    ref = [(k, e) for k, e in (reg.get("sets") or {}).items() if e.get("decision") != "import"]
    if not ref:
        return ""
    return (f"\n## Refused Iconify sets (@iconify/json@{reg.get('iconify_json')}, tools/import_icon_packs.py --discover)\n\n"
            "| Iconify set | Name | Icons | Licence | Why |\n|---|---|---|---|---|\n"
            + "\n".join(f"| {e['npm']} | {e['label']} | {e['total']:,} | {e['licence']} | {e['reason']} |"
                         for k, e in sorted(ref, key=lambda kv: (kv[1]["reason"], kv[0]))) + "\n")


def stale(set_id: str) -> bool:
    p = L.ICONS_DIR / set_id / "icons.json"
    if not p.exists():
        return True
    npm = L.PACKS[set_id]["npm"]
    if not npm:
        return False
    v = json.loads((L.NPM_DIR / npm / "package.json").read_text(encoding="utf-8"))["version"] \
        if (L.NPM_DIR / npm / "package.json").exists() else "?"
    head = p.open(encoding="utf-8").read(400)
    return f"@iconify-json/{npm}@{v}" not in head


def classify(prefix: str, c: dict) -> dict:
    """One Iconify collection -> its packs.json entry (decision import / refused + reason, kind, role)."""
    spdx = (c.get("license") or {}).get("spdx", "")
    cat = c.get("category") or ("hidden" if c.get("hidden") else "")
    kind = ("flag" if cat == "Flags" else "illustration" if c.get("palette")
            else "line" if "Uses Stroke" in (c.get("tags") or []) else "flat")
    archive = cat in ("Archive / Unmaintained", "hidden") or bool(c.get("hidden"))
    role = {"flag": "flags", "line": "line", "flat": "flat"}.get(kind) or (
        "family" if cat in IMPORT_ROLES and c.get("total", 0) >= 1000 and not archive else "illustration")
    e = {"npm": prefix, "label": c.get("name", prefix), "total": c.get("total", 0), "licence": spdx or "unknown",
         "category": cat, "kind": kind, "role": role, "emoji": cat == "Emoji", "archive": archive,
         "author": (c.get("author") or {}).get("name", ""), "upstream": (c.get("author") or {}).get("url", ""),
         "licence_url": _raw_url((c.get("license") or {}).get("url", ""))}
    if cat in BRAND_CATEGORIES or re.search(r"(^|-)(brands?|logos?)(-|$)", prefix):
        e.update(decision="refused", reason=f"brand / logo set ({cat or 'brands'}): trademarks")
    elif spdx not in L.ALLOWED:
        e.update(decision="refused", reason=f"licence {spdx or 'unknown'} is not on the allow-list")
    elif L.ALLOWED[spdx] == "by" and not L.allow_cc_by():
        e.update(decision="refused", reason="CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic)")
    else:
        e.update(decision="import", reason="")
    return e


def discover(version: str) -> int:
    import subprocess
    cols = json.loads(_get(f"https://unpkg.com/@iconify/json@{version}/collections.json"))
    sets = {}
    for prefix, c in sorted(cols.items()):
        sid = OLD_IDS.get(prefix) or prefix.replace("-", "_")
        if sid in L.KINDS and OLD_IDS.get(prefix) != sid:
            sid = {"fluent_color": "fluent_ui_color"}.get(sid, sid + "_set")
        e = classify(prefix, c)
        if sid in L.KINDS:                     # hand-picked (pipeline/icon_library.PACKS): kept as they are
            e.update(hand_picked=True, kind=L.KINDS[sid], role=L.PACKS[sid]["role"])
        sets[sid] = e
    new = [e["npm"] for sid, e in sets.items() if e["decision"] == "import" and not e.get("hand_picked")
           and not (L.NPM_DIR / e["npm"] / "icons.json").exists()]
    if new:
        print(f"npm: installing {len(new)} new @iconify-json packages at exact versions ...")
        r = subprocess.run(["npm", "install", "--save-exact", "--no-audit", "--no-fund", "--loglevel=error",
                            *[f"@iconify-json/{n}" for n in new]], cwd=ROOT)
        if r.returncode:
            print("ERROR npm install failed")
            return 1
    L.REGISTRY.write_text(json.dumps({"iconify_json": version, "collections": len(cols), "sets": sets}, indent=1,
                                     ensure_ascii=False) + "\n", encoding="utf-8")
    imp = [e for e in sets.values() if e["decision"] == "import"]
    ref = [(sid, e) for sid, e in sets.items() if e["decision"] != "import"]
    print(f"packs.json: {len(cols)} Iconify sets in @iconify/json@{version}: {len(imp)} to import, {len(ref)} refused")
    by = {}
    for sid, e in ref:
        by.setdefault(e["reason"], []).append(sid)
    for why, ids in sorted(by.items(), key=lambda kv: -len(kv[1])):
        print(f"  refused {len(ids):>3}: {why}: {', '.join(sorted(ids))}")
    return 0


def main() -> int:
    if "--discover" in sys.argv:
        i = sys.argv.index("--discover")
        if i + 1 >= len(sys.argv):
            print("usage: --discover <@iconify/json version>, e.g. 2.2.555")
            return 1
        if discover(sys.argv[i + 1]):
            return 1
        import importlib
        importlib.reload(L)                                     # PACKS now includes the registry
        sys.argv = [sys.argv[0]]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want = args or list(L.PACKS)
    if "--check" in sys.argv:
        bad = [s for s in want if not L.PACKS[s].get("optional") and stale(s)]
        print("icon packs: " + ("up to date" if not bad else "missing or stale: " + ", ".join(bad)))
        return 1 if bad else 0
    failed = 0
    for set_id in want:
        if set_id not in L.PACKS:
            print(f"REFUSED {set_id}: not a known pack ({', '.join(L.PACKS)})")
            failed += 1
            continue
        try:
            m = import_natural_earth() if set_id == "natural_earth" else import_npm(set_id)
            size = (L.ICONS_DIR / set_id / "icons.json").stat().st_size / 1e6
            print(f"ok      {set_id}: {m['count']:,} icons, {m['licence']}, {size:.1f} MB ({m['source']})")
        except PipelineError as e:
            if L.PACKS[set_id].get("optional") and not args:
                print(f"skipped {set_id}: {e}")
            else:
                print(f"REFUSED {e}")
                failed += 1
    write_credits()
    L.load.cache_clear()
    print(f"credits: assets/library/icons/CREDITS.md and NOTICE written ({len(L.installed())} packs)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
