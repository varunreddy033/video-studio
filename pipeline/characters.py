"""
characters.py  -  loads a presenter character from docs/characters/<name>.md

The character file is the source of truth (word for word): CHARACTER = "...", STYLE = "...", SEED = 1000,
"Kokoro <voice>, speed <x>", the presenter pose list and the sets ("name" (description)).
The generated pack lives in assets/characters/<name>/ (see tools/make_character_pack.py).
"""

import re
from functools import lru_cache

from . import config as C

DOCS = C.BASE_DIR / "docs" / "characters"
PACKS = C.BASE_DIR / "assets" / "characters"
DEFAULT_POSES = ["neutral", "pointing", "shrug", "shocked", "thinking", "serious", "laughing"]
MOUTHS = ["closed", "slight", "wide", "o", "e", "mbp"]      # closed = the pose image itself


class CharacterError(Exception):
    pass


def _quoted(text, key):
    m = re.search(rf"{key}\s*=\s*\"(.*?)\"", text, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


DEFAULT_SET_TEXT = {"stage": "a dark stage with one spotlight and a large screen",
                    "studio": "a cosy presenter studio with a desk, a warm lamp and a big wall screen"}


def _split_top(text: str):
    """Split 'a, b (x, y), c' on commas that aren't inside brackets."""
    out, cur, depth = [], "", 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _paragraph_after(text: str, label_re: str) -> str:
    """The text after a label like 'Sets:' up to the next blank line."""
    m = re.search(label_re, text)
    if not m:
        return ""
    rest = text[m.end():]
    return rest.split("\n\n", 1)[0]


@lru_cache(maxsize=8)
def load(name: str) -> dict:
    name = (name or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]{2,40}", name):
        raise CharacterError(f"bad character name '{name}'")
    path = DOCS / f"{name}.md"
    if not path.exists():
        raise CharacterError(f"no character file docs/characters/{name}.md")
    text = path.read_text(encoding="utf-8")
    char, style = _quoted(text, "CHARACTER"), _quoted(text, "STYLE")
    seed = re.search(r"SEED\s*=\s*(\d+)", text)
    if not char or not style or not seed:
        raise CharacterError(f"docs/characters/{name}.md needs CHARACTER = \"...\", STYLE = \"...\" and SEED = <number>")
    # voice: "Kokoro bm_george, speed 0.95" or "Voice: am_puck, speed 1.0"
    voice = re.search(r"(?:Kokoro|Voice:)\s+([a-z]{2}_[a-z]+)\s*,\s*speed\s*([\d.]+)", text)
    # poses: "Presenter poses (...): a, b, c" or "Poses: a, b, excited (both paws up)."
    pl = re.search(r"(?m)^(?:Presenter poses[^:\n]*|Poses):\s*([^\n]+)", text)
    poses, pose_desc = [], {}
    if pl:
        for item in _split_top(pl.group(1).rstrip(". ")):
            m = re.fullmatch(r"([a-z-]+)\s*(?:\((.*)\))?\.?", item.strip().lower())
            if m:
                poses.append(m.group(1))
                if m.group(2):
                    pose_desc[m.group(1)] = m.group(2).replace('"', "").strip()
    poses = poses or list(DEFAULT_POSES)
    # sets: '"studio" (description)' or a bare '"stage"' (gets a default description)
    sets = {}
    para = _paragraph_after(text, r"(?m)^Sets:")
    for m in re.finditer(r"\"([A-Za-z0-9_-]+)\"(?:\s*\(([^)]*)\))?", para):
        sets[m.group(1).lower()] = re.sub(r"\s+", " ", m.group(2)).strip() if m.group(2) else \
            DEFAULT_SET_TEXT.get(m.group(1).lower(), f"a {m.group(1).lower()} set")

    def key(k, default):
        mm = re.search(rf"(?m)^{k}\s*=\s*\"?([^\"\n]+?)\"?\s*(?:\(|$)", text)
        return mm.group(1).strip() if mm else default
    # words the image prompts use for this character's body (Sterling: cat / paws / fur / navy blazer)
    body = {"noun": key("NOUN", "character"), "limbs": key("LIMBS", "hands"), "fur": key("FUR", "body"),
            "outfit": key("OUTFIT", "outfit"), "ears": key("EARS", "no").lower().startswith("y")}
    return {"name": name, "character": char, "style": style, "seed": int(seed.group(1)),
            "voice": voice.group(1) if voice else None, "speed": float(voice.group(2)) if voice else None,
            "poses": poses, "pose_desc": pose_desc, "sets": sets or {"studio": DEFAULT_SET_TEXT["studio"]},
            "body": body, "doc": str(path)}


def pack_dir(name: str):
    return PACKS / name


def pack_path(name: str, p) -> "Path":
    """A file/folder named in pack.json, on THIS machine. pack.json may hold absolute paths from the machine that
    built the pack (/Users/... or C:\\...); everything after 'characters/<name>/' is taken relative to this
    machine's pack folder, so an imported pack works anywhere."""
    from pathlib import Path, PurePosixPath
    raw = str(p).replace("\\", "/")
    parts = PurePosixPath(raw).parts
    for i in range(len(parts) - 1):
        if parts[i] == "characters" and parts[i + 1] == name:
            return pack_dir(name).joinpath(*parts[i + 2:])
    q = Path(raw)
    return q if q.is_absolute() else pack_dir(name) / q
