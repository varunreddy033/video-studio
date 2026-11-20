"""Script format of rendering_method: blocky3d (docs/SCRIPT_FORMAT.md "Blocky 3D").

Header:
    cast: me = hero_green, crush = goth_girl, crowd = townsfolk x300     (name = presets/blocky_cast/<id> [x count])
    set: town_square        the default place of every shot
    grade: bright           the light / colour look: bright, dusk, night, fog

Body (one tag = one shot, cut where its narration starts, like [ai:]):
    [shot: who | action | camera | set=beach face=scared]
        who     cast names, comma list; empty = only the place
        action  what they do (ACTIONS), default idle
        camera  CAMERAS, default auto (the renderer picks one from the action)
    [sign: kind | text]     an in-world sign, note or board in close-up (SIGNS)

The vocabulary below is what the renderer must draw (plan steps 3-5); Check accepts nothing else.
"""

import re

from .. import presets

ACTIONS = ("idle", "talk", "walk", "run", "jump", "fall", "sit", "lie", "wave", "point", "dance", "cheer", "scared",
           "cry", "freeze", "sleep")
CAMERAS = ("auto", "locked", "push_in", "pull_out", "track", "orbit", "crane_up", "crane_down", "low_angle",
           "high_angle", "over_shoulder", "close_up", "whip")
FACES = ("neutral", "happy", "sad", "angry", "scared", "shocked", "smirk", "crying", "shut")
# extra faces of the studio characters (assets/blocky3d/studio/textures/faces); the code-drawn rig shows its nearest face
STUDIO_FACES = ("anime_shocked", "anime_smile", "anime_worried", "blush_shy", "determined", "dizzy", "glare", "laugh",
                "love", "nervous_sweat", "screaming", "sleeping", "sleepy_blush", "smile", "smug", "troll_grin",
                "unimpressed", "wink", "worried", "yelling")
SETS = ("town_square", "street", "beach", "house_inside", "bedroom", "classroom", "cafeteria", "park", "arena",
        "forest", "night_town", "dorm_room", "space", "farm", "market", "river")
GRADES = ("bright", "dusk", "night", "fog")
SIGNS = ("note", "tablet", "board", "scoreboard", "phone")
TAGS = ("shot", "sign")
OPTIONS = {"set": SETS, "face": FACES + STUDIO_FACES, "prop": None}       # prop: any studio prop id (checked later)
CAST_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*=\s*([a-z0-9_]+)(?:\s*x\s*(\d+))?$")
MAX_CROWD = 500
SHOT_WARN_SEC = 4.0          # the references cut every 1.1-2.8 s (output/references, 2026-11-17)


def parse_tag(kind, arg, line, errors):
    """[shot: ...] / [sign: ...] -> a shot dict (type 'shot' / 'sign'), or None after an error."""
    def bad(msg):
        errors.append({"line": line, "msg": msg})

    parts = [p.strip() for p in arg.split("|")]
    if kind == "sign":
        if len(parts) < 2 or not parts[1]:
            return bad(f"[sign: kind | text]: needs a kind ({', '.join(SIGNS)}) and the text, got '{arg}'")
        k = parts[0].lower()
        if k not in SIGNS:
            return bad(f"[sign: ...]: kind must be one of {', '.join(SIGNS)}, got '{parts[0]}'")
        return {"type": "sign", "line": line, "sign": k, "text": " | ".join(parts[1:])}
    opts, pos = {}, []
    for p in parts:
        pairs = re.findall(r"(\w+)\s*=\s*([\w/-]+)", p)
        if pairs and not re.sub(r"\w+\s*=\s*[\w/-]+", "", p).strip():
            for k, v in pairs:
                k, v = k.lower(), v.lower()
                if k not in OPTIONS:
                    return bad(f"[shot: ...]: unknown option '{k}='; use {', '.join(f'{o}=' for o in OPTIONS)}")
                if OPTIONS[k] is not None and v not in OPTIONS[k]:
                    return bad(f"[shot: ...]: {k} must be one of {', '.join(OPTIONS[k])}, got '{v}'")
                opts[k] = v
        else:
            pos.append(p)
    who = [w.strip().lower() for w in (pos[0] if pos else "").split(",") if w.strip()]
    action = (pos[1] if len(pos) > 1 and pos[1] else "idle").lower()
    camera = (pos[2] if len(pos) > 2 and pos[2] else "auto").lower().replace(" ", "_")
    if len(pos) > 3:
        return bad("[shot: who | action | camera | set=... face=...]: too many parts")
    if action not in ACTIONS:
        return bad(f"[shot: ...]: action must be one of {', '.join(ACTIONS)}, got '{action}'")
    if camera not in CAMERAS:
        return bad(f"[shot: ...]: camera must be one of {', '.join(CAMERAS)}, got '{camera}'")
    return {"type": "shot", "line": line, "who": who, "action": action, "camera": camera,
            "set": opts.get("set", ""), "face": opts.get("face", ""), "prop": opts.get("prop", "")}


def _cast(raw, line, err):
    """'me = hero_green, crowd = townsfolk x300' -> {name: {preset, count}}."""
    from . import sets as SETS_
    cast, valid, studio = {}, presets.ids("blocky_cast"), SETS_.studio("characters")
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        m = CAST_RE.match(item.lower())
        if not m:
            err(line, f"cast: '{item}' should look like 'name = preset' or 'crowd = preset x300'")
            continue
        name, pid, n = m.group(1), m.group(2), int(m.group(3) or 1)
        if pid not in valid and pid not in studio:
            err(line, f"cast: '{pid}' isn't a preset (presets/blocky_cast/: {', '.join(valid)}) or a studio character "
                      f"(assets/blocky3d/studio: {', '.join(sorted(studio)) or 'not built'})")
        if not 1 <= n <= MAX_CROWD:
            err(line, f"cast: {name} x{n}: a crowd is 1-{MAX_CROWD} people")
        if name in cast:
            err(line, f"cast: '{name}' is named twice")
        cast[name] = {"preset": pid, "count": n} if pid in valid else {"model": studio[pid], "id": pid, "count": n}
    return cast


def check(meta, shots, err, warn, key_line):
    """Header + shot rules for rendering_method: blocky3d. Returns the Check page's blocky3d stats."""
    from . import sets as SETS_
    cast = _cast(str(meta.get("cast") or ""), key_line("cast"), err)
    place = (meta.get("set") or "").strip().lower() or SETS[0]
    if place not in SETS:
        err(key_line("set"), f"set must be one of {', '.join(SETS)}, got '{place}'")
        place = SETS[0]
    grade = (meta.get("grade") or "").strip().lower() or GRADES[0]
    if grade not in GRADES:
        err(key_line("grade"), f"grade must be one of {', '.join(GRADES)}, got '{grade}'")
        grade = GRADES[0]
    meta.update(cast=cast, set=place, grade=grade)
    for sh in shots:
        if sh["type"] not in TAGS and not sh.get("placeholder"):    # (placeholder: narration before any tag)
            err(sh["line"], f"[{sh['type']}: ...] isn't used by blocky3d videos; use [shot: who | action | camera] "
                            f"or [sign: kind | text]")
            continue
        if sh["type"] == "shot":
            missing = [w for w in sh["who"] if w not in cast]
            if missing:
                err(sh["line"], f"[shot: ...]: {', '.join(missing)} isn't in the cast: header "
                                f"({', '.join(cast) or 'no cast: line yet'})")
            sh["set"] = sh["set"] or place
            if sh.get("prop") and sh["prop"] not in SETS_.studio("props"):
                err(sh["line"], f"[shot: ...]: prop={sh['prop']} isn't a studio prop (assets/blocky3d/studio/models/props)")
        if sh.get("est_dur", 0) > SHOT_WARN_SEC:
            warn(sh["line"], f"this shot stays on screen ~{sh['est_dur']:.0f} s; story Shorts cut every 1-3 s, "
                             f"add another [shot:] inside that narration")
    used = [sh for sh in shots if sh["type"] == "shot"]
    if used and not any(sh["who"] for sh in used):
        warn(1, "no shot shows anyone: put cast names in the first part of [shot: who | action | camera]")
    if not used:
        err(1, "a blocky3d video needs at least one [shot: ...]")
    return {"cast": {k: v.get("preset", v.get("id", "")) + (f" x{v['count']}" if v["count"] > 1 else "") for k, v in cast.items()},
            "set": place, "grade": grade, "sets": sorted({sh["set"] for sh in used}),
            "actions": sorted({sh["action"] for sh in used}), "signs": sum(1 for sh in shots if sh["type"] == "sign"),
            "crowd": sum(v["count"] for v in cast.values() if v["count"] > 1)}
