"""Download free sound effects from Openverse (openverse.org) into assets/library/sfx/<kind>/.

    bin/python tools/fetch_sfx_openverse.py                 3 sounds for every kind below (-n 8: top up to 8)
    bin/python tools/fetch_sfx_openverse.py whoosh pop -n 5  only these kinds, 5 each
    bin/python tools/fetch_sfx_openverse.py --query "door slam" --kind door

Only CC0 (public domain) sounds are taken: free for monetised videos, no credit needed. Each download is listed in
assets/library/sfx/CREDITS.md anyway (title, author, source page) so every file can be traced.
No account or key: Openverse allows 20 searches a minute and 200 a day without one, so the tool pauses between
searches. Files are named ov_<id>_<title>.mp3; a kind that already has enough ov_ files is skipped.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C          # noqa: E402

API = "https://api.openverse.org/v1/audio/"
UA = {"User-Agent": "video-studio-sfx-fetch/1.0"}
# kind -> (search words, shortest ms, longest ms)
KINDS = {
    "whoosh": ("whoosh swoosh", 200, 1500), "riser": ("riser build up", 800, 4000),
    "impact": ("impact boom hit", 300, 3000), "pop": ("pop", 60, 700), "ding": ("ding bell notification", 200, 2500),
    "cash": ("cash register", 300, 3000), "typing": ("keyboard typing", 600, 4000), "click": ("click button", 40, 500),
    "shutter": ("camera shutter", 100, 1200), "glitch": ("glitch digital", 200, 2500),
    "heartbeat": ("heartbeat", 600, 4000), "tick": ("clock tick", 300, 3000), "alert": ("alert beep warning", 200, 2500),
    "paper": ("paper page turn", 200, 2000), "stamp": ("stamp thud", 100, 1500), "swipe": ("swipe slide", 100, 900),
    "bubble": ("bubble pop", 60, 900), "success": ("success chime", 300, 2500), "error": ("error buzz wrong", 200, 2000),
    "coin": ("coin", 100, 1500),
    # added for the asset packs plan (docs/ASSET_PACKS_PLAN.md section 6)
    "notification": ("notification sound", 150, 2000), "swoosh-up": ("swoosh up rising whoosh", 200, 2000),
    "boing": ("boing spring cartoon", 150, 1800), "record-scratch": ("record scratch vinyl", 150, 2500),
    "crowd-gasp": ("crowd gasp", 400, 3500), "keyboard-enter": ("keyboard enter key", 60, 800),
    "coin-drop": ("coin drop", 150, 2500), "door": ("door close", 200, 3000),
    "crowd-cheer": ("crowd cheer applause", 600, 4000),
}


def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        data = r.read()
    return data if binary else json.loads(data.decode())


def search(words, lo, hi, want):
    q = urllib.parse.urlencode({"q": words, "license": "cc0", "page_size": 20})
    out = []
    for r in get(f"{API}?{q}").get("results", []):
        d = r.get("duration") or 0
        if r.get("license") == "cc0" and lo <= d <= hi and (r.get("filetype") or "mp3") in ("mp3", "wav", "ogg", "flac"):
            out.append(r)
        if len(out) >= want:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kinds", nargs="*")
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("--query")
    ap.add_argument("--kind")
    a = ap.parse_args()
    jobs = {a.kind: (a.query, 60, 4000)} if a.query and a.kind else {k: KINDS[k] for k in (a.kinds or KINDS)}
    credits = C.SFX_LIB / "CREDITS.md"
    lines = credits.read_text(encoding="utf-8").splitlines() if credits.exists() else [
        "# Sound effect credits", "",
        "Downloaded by tools/fetch_sfx_openverse.py from Openverse. All CC0 1.0 (public domain): no credit required.", "",
        "| File | Title | Author | Source |", "|---|---|---|---|"]
    first = True
    for kind, (words, lo, hi) in jobs.items():
        folder = C.SFX_LIB / kind
        folder.mkdir(parents=True, exist_ok=True)
        have = len(list(folder.glob("ov_*")))
        if have >= a.n:
            print(f"   {kind}: already has {have}")
            continue
        if not first:
            time.sleep(3.2)                                  # stay under 20 searches a minute
        first = False
        try:
            found = search(words, lo, hi, a.n * 3)
        except Exception as e:
            print(f"   {kind}: search failed ({e})")
            continue
        got = have
        for r in found:
            if got >= a.n:
                break
            slug = re.sub(r"[^a-z0-9]+", "_", (r.get("title") or "sound").lower()).strip("_")[:40]
            name = f"ov_{r['id'][:8]}_{slug}.{r.get('filetype') or 'mp3'}"
            if (folder / name).exists():
                continue
            try:
                data = get(r["url"], binary=True)
            except Exception as e:
                if "403" in str(e):
                    print(f"   {kind}: the sound host ({urllib.parse.urlparse(r['url']).netloc}) refused the download "
                          f"from this network (403). Run this tool on the Mac at home, not on a server. Stopping.")
                    _save(credits, lines)
                    sys.exit(1)
                print(f"   {kind}: download failed ({e})")
                continue
            if len(data) < 2000:
                continue
            (folder / name).write_bytes(data)
            lines.append(f"| {kind}/{name} | {(r.get('title') or '').replace('|', ' ')} | {r.get('creator') or '?'} | "
                         f"{r.get('foreign_landing_url') or r.get('detail_url')} |")
            got += 1
        print(f"   {kind}: {got - have} new ({got} in the folder)")
    _save(credits, lines)


def _save(credits, lines):
    if any(l.startswith("| ") and "/ov_" in l for l in lines):     # only once something was downloaded
        credits.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
