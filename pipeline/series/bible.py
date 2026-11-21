"""A web series is a folder (docs/series/SERIES_PLAN.md section 2):

  series/<series-id>/
    series.md        the bible: title, logline, genre, tone, rating, world, narrator voice, season arc, themes
    cast/<id>.md     one file per character: the NAME used in scripts, role, look, voice (+ speed, effect), personality
    sets/<id>.md     the places of this series, each built on a Blocky 3D set, with its usual time of day
    episodes/epNN.md episode scripts (rendering_method: series, docs/SCRIPT_FORMAT.md section 9)

Every file is a `---` front matter (key: value, `key: |` + indented lines for long text) followed by free notes.
This module only reads and checks them; the episode parser is pipeline/series/script.py.
"""

import re
from pathlib import Path

from .. import config as C
from .. import presets
from . import voicefx

SERIES_DIR = C.BASE_DIR / "series"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
EP_RE = re.compile(r"^ep(\d{2,3})\.md$")
ROLES = ("hero", "villain", "ally", "civilian", "narrator")
STATUS = ("alive", "dead", "missing")
SERIES_KEYS = {"title", "logline", "genre", "tone", "rating", "world", "origin", "season_question", "arc", "themes",
               "narrator", "narrator_voice", "narrator_speed", "narrator_fx", "music", "colour"}
CAST_KEYS = {"name", "role", "look", "voice", "speed", "voice_fx", "colour", "personality", "speech", "catchphrase",
             "status", "powers", "arc", "intro"}
SET_KEYS = {"name", "base", "time", "mood", "description"}
TIME_GRADE = {"day": "bright", "morning": "bright", "noon": "bright", "afternoon": "bright", "dawn": "dusk",
              "sunrise": "dusk", "dusk": "dusk", "sunset": "dusk", "evening": "dusk", "night": "night",
              "midnight": "night", "fog": "fog", "mist": "fog"}


class SeriesError(Exception):
    pass


def front_matter(text: str):
    """-> (meta dict, body text, [(line, message)]) for the bible / cast / set files."""
    lines = text.replace("\r\n", "\n").split("\n")
    meta, errs = {}, []
    if not lines or lines[0].strip() != "---":
        return meta, text, [(1, "the file should start with a --- front matter block")]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return meta, "", [(1, "the front matter starts with --- but never ends with a second --- line")]
    key, block = None, []
    for i in range(1, end):
        raw = lines[i]
        if key and (raw.startswith("  ") or not raw.strip()):
            block.append(raw.strip())
            continue
        if key:
            meta[key] = "\n".join(block).strip()
            key, block = None, []
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if ":" not in raw:
            errs.append((i + 1, f"line should look like 'key: value': {raw.strip()}"))
            continue
        k, v = raw.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if v in ("|", ">"):
            key, block = k, []
        else:
            meta[k] = v.strip('"').strip("'")
    if key:
        meta[key] = "\n".join(block).strip()
    return meta, "\n".join(lines[end + 1:]).strip(), errs


def ids():
    return sorted(p.name for p in SERIES_DIR.iterdir() if p.is_dir() and (p / "series.md").exists()) \
        if SERIES_DIR.is_dir() else []


def _voice_ids():
    out = {}
    for pid in presets.ids("voices"):
        p = presets.load("voices", pid)
        out[pid] = (p["voice"], float(p.get("speed") or 1.0))
    return out


def _voice(raw, default_speed, voices):
    """'am_onyx' (Kokoro id) or 'en_us_onyx' (a voice preset) -> (kokoro id, speed) or (None, None)."""
    v = (raw or "").strip().lower()
    if v in voices:
        return voices[v][0], voices[v][1]
    if re.fullmatch(r"[ab][fm]_[a-z]+", v) and any(k == v for k, _ in voices.values()):
        return v, default_speed
    return None, None


def look_of(look: str):
    """cast `look:` -> ('preset', id) for presets/blocky_cast, ('studio', id) for a studio character, or (None, None)."""
    from ..blocky3d import sets as SETS
    lk = (look or "").strip().lower()
    if lk in presets.ids("blocky_cast"):
        return "preset", lk
    if lk in SETS.studio("characters"):
        return "studio", lk
    return None, None


def load(series_id: str) -> dict:
    """The whole series: {id, dir, meta, body, cast: {NAME: {...}}, sets: {id: {...}}, episodes: [...], problems}.
    problems = [(file, line, message)] (Check shows them as errors of the episode that uses this series)."""
    sid = (series_id or "").strip().lower()
    d = SERIES_DIR / sid
    if not ID_RE.match(sid) or not (d / "series.md").exists():
        raise SeriesError(f"series '{series_id}' doesn't exist (series/<id>/series.md); "
                          f"series here: {', '.join(ids()) or 'none yet'}")
    problems = []
    meta, body, errs = front_matter((d / "series.md").read_text(encoding="utf-8"))
    problems += [("series.md", ln, m) for ln, m in errs]
    problems += [("series.md", 1, f"unknown key '{k}' (allowed: {', '.join(sorted(SERIES_KEYS))})")
                 for k in meta if k not in SERIES_KEYS]
    voices = _voice_ids()
    nv, nsp = _voice(meta.get("narrator_voice") or "en_gb_george", 1.0, voices)
    if not nv:
        problems.append(("series.md", 1, f"narrator_voice '{meta.get('narrator_voice')}' isn't a Kokoro voice or a "
                                         f"voice preset (presets/voices/)"))
        nv, nsp = "bm_george", 1.0
    fx = (meta.get("narrator_fx") or "none").lower()
    if fx != "none" and fx not in voicefx.NAMES:
        problems.append(("series.md", 1, f"narrator_fx must be none or one of {', '.join(voicefx.NAMES)}"))
        fx = "none"
    narrator = {"on": (meta.get("narrator") or "on").lower() not in ("off", "no", "none"), "voice": nv,
                "speed": float(meta.get("narrator_speed") or nsp), "fx": fx}

    cast = {}
    for f in sorted((d / "cast").glob("*.md")):
        cm, cbody, cerr = front_matter(f.read_text(encoding="utf-8"))
        rel = f"cast/{f.name}"
        problems += [(rel, ln, m) for ln, m in cerr]
        problems += [(rel, 1, f"unknown key '{k}' (allowed: {', '.join(sorted(CAST_KEYS))})") for k in cm if k not in CAST_KEYS]
        name = (cm.get("name") or f.stem).strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]{0,23}", name) or name == "NARRATOR":
            problems.append((rel, 1, f"name '{name}' must be one word in capitals (it is how scripts write "
                                     f"'{name}: line'), and not NARRATOR"))
        kind, look = look_of(cm.get("look"))
        if not kind:
            problems.append((rel, 1, f"look '{cm.get('look')}' isn't a presets/blocky_cast id or a studio character "
                                     f"(assets/blocky3d/studio)"))
            kind, look = "preset", presets.DEFAULTS["blocky_cast"]
        try:
            speed0 = float(cm.get("speed") or 0) or None
        except ValueError:
            problems.append((rel, 1, "speed must be a number like 1.0"))
            speed0 = None
        v, sp = _voice(cm.get("voice"), 1.0, voices)
        if not v:
            problems.append((rel, 1, f"voice '{cm.get('voice')}' isn't a Kokoro voice (am_onyx) or a voice preset "
                                     f"(en_us_onyx); see presets/voices/"))
            v, sp = "am_michael", 1.0
        vfx = (cm.get("voice_fx") or "none").strip().lower()
        if vfx != "none" and vfx not in voicefx.NAMES:
            problems.append((rel, 1, f"voice_fx must be none or one of {', '.join(voicefx.NAMES)}, got '{vfx}'"))
            vfx = "none"
        role = (cm.get("role") or "civilian").strip().lower()
        if role not in ROLES:
            problems.append((rel, 1, f"role must be one of {', '.join(ROLES)}, got '{role}'"))
        status = (cm.get("status") or "alive").strip().lower()
        if status not in STATUS:
            problems.append((rel, 1, f"status must be one of {', '.join(STATUS)}, got '{status}'"))
        if name in cast:
            problems.append((rel, 1, f"two cast files use the name {name}"))
        cast[name] = {"id": f.stem, "file": rel, "name": name, "role": role, "look_kind": kind, "look": look,
                      "voice": v, "speed": speed0 or sp, "voice_fx": vfx, "status": status,
                      "colour": cm.get("colour") or "", "personality": cm.get("personality") or "",
                      "speech": cm.get("speech") or "", "catchphrase": cm.get("catchphrase") or "",
                      "powers": cm.get("powers") or "", "intro": cm.get("intro") or "", "notes": cbody}

    from ..blocky3d import script as B3S
    sets = {}
    for f in sorted((d / "sets").glob("*.md")):
        sm, sbody, serr = front_matter(f.read_text(encoding="utf-8"))
        rel = f"sets/{f.name}"
        problems += [(rel, ln, m) for ln, m in serr]
        problems += [(rel, 1, f"unknown key '{k}' (allowed: {', '.join(sorted(SET_KEYS))})") for k in sm if k not in SET_KEYS]
        base = (sm.get("base") or "").strip().lower()
        if base not in B3S.SETS:
            problems.append((rel, 1, f"base must be a Blocky 3D set ({', '.join(B3S.SETS)}), got '{base}'"))
            base = B3S.SETS[0]
        time_ = (sm.get("time") or "day").strip().lower()
        sets[f.stem.lower()] = {"id": f.stem.lower(), "file": rel, "name": sm.get("name") or f.stem.replace("_", " ").title(),
                                "base": base, "time": time_, "grade": TIME_GRADE.get(time_, "bright"),
                                "mood": sm.get("mood") or "", "description": sm.get("description") or sbody[:300]}

    arc = []
    for ln in (meta.get("arc") or "").split("\n"):
        m = re.match(r"^\s*(\d{1,3})\s*[:.)-]\s*(.+)$", ln)
        if m:
            title, _, summary = m.group(2).partition(" - ")
            arc.append({"episode": int(m.group(1)), "title": title.strip(), "summary": summary.strip()})
    episodes = []
    for f in sorted((d / "episodes").glob("ep*.md")):
        m = EP_RE.match(f.name)
        if not m:
            continue
        em, _, _ = front_matter(f.read_text(encoding="utf-8"))
        episodes.append({"file": f.name, "episode": int(m.group(1)), "title": em.get("title") or f.stem,
                         "path": f"series/{sid}/episodes/{f.name}"})
    return {"id": sid, "dir": d, "meta": meta, "body": body, "title": meta.get("title") or sid, "narrator": narrator,
            "cast": cast, "sets": sets, "arc": arc, "episodes": episodes, "problems": problems}


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:40].strip("-")
    return s if len(s) >= 2 else "series"


SERIES_TEMPLATE = """---
title: {title}
logline: {logline}
genre: superhero action
tone: hopeful with dark turns
rating: all-ages
world: |
  Where and when; the one rule that makes this world different.
season_question: What question does the last episode answer?
narrator_voice: en_gb_george
arc: |
  1: Episode one - what happens
music: mystery
---
Notes about the series (recurring themes, what it must never do).
"""


def create(title: str, logline: str = "") -> str:
    """A new series folder with a bible template; returns its id."""
    title = (title or "").strip()
    if not title:
        raise SeriesError("a series needs a title")
    if len(title) > 80:
        raise SeriesError("keep the series title under 80 characters")
    base, n = slug(title), 2
    sid = base
    while (SERIES_DIR / sid).exists():
        sid, n = f"{base}-{n}", n + 1
    d = SERIES_DIR / sid
    for sub in ("cast", "sets", "episodes"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "series.md").write_text(SERIES_TEMPLATE.format(title=title.replace("\n", " "),
                                                        logline=(logline or "One sentence: hero + goal + obstacle + stakes.").replace("\n", " ")),
                                 encoding="utf-8")
    return sid


def episode_template(s: dict) -> tuple:
    """(file name, text) of the next episode of series s."""
    n = max([e["episode"] for e in s["episodes"]] + [0]) + 1
    names = list(s["cast"])[:2] or ["HERO"]
    a, b = names[0], names[1] if len(names) > 1 else names[0]
    place = next(iter(s["sets"]), "street").upper()
    planned = next((x for x in s["arc"] if x["episode"] == n), None)
    title = planned["title"] if planned else f"Episode {n}"
    return f"ep{n:02d}.md", f"""---
series: {s['id']}
episode: {n}
title: {title}
type: episode
rendering_method: series
---
## SCENE 1 | {place} | NIGHT
[cast: {a} at left, {b} at right]
NARRATOR: One line that sets the scene.
{a} (determined): The first line of dialogue.
{b} (smirk): The answer.
"""


def save_episode(series_id: str, file: str, text: str) -> Path:
    s = load(series_id)
    if not EP_RE.match(file or ""):
        raise SeriesError("episode files are called ep01.md, ep02.md ...")
    if len(text) > 400_000:
        raise SeriesError("that episode is too long to save")
    p = s["dir"] / "episodes" / file
    p.write_text(text.replace("\r\n", "\n"), encoding="utf-8")
    return p
