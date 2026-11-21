"""Episode scripts of a web series (rendering_method: series, docs/SCRIPT_FORMAT.md section 9).

    ---
    series: sample-series          the folder series/<id>/ (bible, cast, sets)
    episode: 1
    title: The Spark
    type: episode                  16:9 (episode_short = a 9:16 side story: not built yet)
    rendering_method: series
    ---
    ## SCENE 1 | STREET | NIGHT    a scene: a place (sets/<id>.md or a Blocky 3D set) and a time (day, dusk, night, fog)
    [cast: KAI at left, VEX at right]        who is in the scene and where: left, right, centre, background,
                                             far_left, far_right (default: the order they speak in)
    NARRATOR: Three days after the blackout, the city still had no lights.
    KAI (angry, close): You shouldn't have come back.
    VEX (smirk): And miss your big night?

Every spoken line is one segment with the speaker's own voice (cast file: voice, speed, voice_fx) and one shot whose
framing the renderer picks (pipeline/series/render.py: speaker close-up, listener reaction, two-shot). `(emotion)`
sets the face and the delivery; a camera word in the brackets (close, medium, two_shot, wide, over_shoulder, low,
high) overrides the framing. [shot:] / [sign:] (Blocky 3D tags) replace the framing of the next line; [sfx:] and
[pause:] work as everywhere. [fight:] / [power:] / [action:] come with the action phase and are skipped for now.
"""

import re

from ..blocky3d import script as B3
from . import bible, voicefx

TAG_RE = re.compile(r"\[(\w+)\s*:\s*([^\]]*)\]")
SCENE_RE = re.compile(r"^##\s*SCENE\s+(\d+)\s*\|\s*([^|]+?)\s*(?:\|\s*(.+?))?\s*$", re.I)
LINE_RE = re.compile(r"^([A-Z][A-Z0-9_-]{0,23})\s*(?:\(([^)]*)\))?\s*:\s*(.*)$")
POSITIONS = {"left": (-3.0, 0.0), "right": (3.0, 0.0), "centre": (0.0, 0.6), "center": (0.0, 0.6),
             "background": (0.0, -6.5), "far_left": (-6.4, -1.2), "far_right": (6.4, -1.2),
             "back_left": (-3.6, -5.5), "back_right": (3.6, -5.5)}
AUTO_SPOTS = ("left", "right", "back_left", "back_right", "far_left", "far_right", "background")
# emotion -> (studio face, speed factor of the delivery, body: talk / scared / sad / cry, extra voice effect)
EMOTIONS = {
    "neutral": ("neutral", 1.0, "talk", ""), "calm": ("neutral", 0.96, "talk", ""), "happy": ("smile", 1.03, "talk", ""),
    "cheerful": ("smile", 1.05, "talk", ""), "laughing": ("laugh", 1.04, "talk", ""), "sad": ("sad", 0.92, "sad", ""),
    "quiet": ("worried", 0.94, "sad", ""), "angry": ("angry", 1.05, "talk", ""), "furious": ("yelling", 1.08, "talk", ""),
    "shouting": ("yelling", 1.06, "talk", ""), "scared": ("scared", 1.08, "scared", ""), "afraid": ("scared", 1.06, "scared", ""),
    "nervous": ("nervous_sweat", 1.05, "talk", ""), "worried": ("worried", 1.0, "talk", ""), "shocked": ("shocked", 1.03, "talk", ""),
    "surprised": ("anime_shocked", 1.03, "talk", ""), "smirk": ("smirk", 0.98, "talk", ""), "smug": ("smug", 0.97, "talk", ""),
    "determined": ("determined", 1.0, "talk", ""), "cold": ("glare", 0.94, "talk", ""), "menacing": ("glare", 0.9, "talk", ""),
    "tired": ("unimpressed", 0.9, "sad", ""), "bored": ("unimpressed", 0.94, "talk", ""), "crying": ("crying", 0.9, "cry", ""),
    "confused": ("anime_worried", 0.98, "talk", ""), "proud": ("smug", 1.0, "talk", ""), "hopeful": ("smile", 0.98, "talk", ""),
    "whispering": ("worried", 0.92, "talk", "whisper"), "whisper": ("worried", 0.92, "talk", "whisper"),
}
# the code-drawn rig (presets/blocky_cast looks) has 9 faces: the nearest one
RIG_FACE = {"smile": "happy", "laugh": "happy", "yelling": "angry", "nervous_sweat": "scared", "worried": "sad",
            "anime_shocked": "shocked", "anime_worried": "scared", "smug": "smirk", "determined": "angry", "glare": "angry",
            "unimpressed": "neutral"}
FRAMES = {"close": "close", "close_up": "close", "closeup": "close", "medium": "medium", "two_shot": "two",
          "two-shot": "two", "twoshot": "two", "wide": "wide", "over_shoulder": "ots", "ots": "ots", "low": "low",
          "low_angle": "low", "high": "high", "high_angle": "high"}
LATER = {"fight": "fights", "power": "super powers", "action": "single action beats"}
LONG_LINE = 25                # words (docs/series/SERIES_PLAN.md section 3)
CARD_SEC = 2.4                # the scene card is held this long before the scene's first line
TYPES_ALLOWED = ("episode",)


def _scene_place(raw, series, line, err):
    """SCENE header place -> (series set id or '', Blocky 3D base set, the set's own grade)."""
    key = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
    if series and key in series["sets"]:
        st = series["sets"][key]
        return key, st["base"], st["grade"]
    if key in B3.SETS:
        return "", key, None
    own = ", ".join(s.upper() for s in (series or {}).get("sets", {})) or "none yet"
    err(line, f"SCENE place '{raw.strip()}' isn't a set of this series (sets/: {own}) or a Blocky 3D set "
              f"({', '.join(s.upper() for s in B3.SETS)})")
    return "", B3.SETS[0], None


def _scene_time(raw, default, line, warn):
    words = [w.strip().lower() for w in re.split(r"[,/]", raw or "") if w.strip()]
    grade = default or "bright"
    for w in words:
        if w in bible.TIME_GRADE:
            grade = bible.TIME_GRADE[w]
        elif w in ("rain", "snow", "storm", "smoke", "ash"):
            warn(line, f"weather ({w}) comes with the sets phase (docs/series/SERIES_PLAN.md section 9, step 2); "
                       f"the scene is drawn without it for now")
        else:
            warn(line, f"time '{w}' isn't known; use day, dawn, dusk, night or fog")
    return grade


def _blocking(arg, cast, line, err):
    """'KAI at left, VEX at right' -> [(NAME, position)]."""
    out = []
    for item in [x.strip() for x in arg.split(",") if x.strip()]:
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)(?:\s+(?:at|in|on)\s+(?:the\s+)?([a-z_ ]+?))?(?:\s+facing\s+\w+)?$", item, re.I)
        if not m:
            err(line, f"[cast: ...]: '{item}' should look like 'KAI at left' (left, right, centre, background, "
                      f"far_left, far_right, back_left, back_right)")
            continue
        name = m.group(1).upper()
        pos = (m.group(2) or "").strip().lower().replace(" ", "_")
        if cast is not None and name not in cast:
            err(line, f"[cast: ...]: {name} isn't in this series' cast ({', '.join(cast) or 'no cast files yet'})")
            continue
        if pos and pos not in POSITIONS:
            err(line, f"[cast: ...]: position '{pos}' must be one of {', '.join(POSITIONS)}")
            pos = ""
        out.append((name, pos))
    return out


def _emotion_camera(raw, line, warn):
    emo, frame = "", ""
    for w in [x.strip().lower().replace(" ", "_") for x in (raw or "").split(",") if x.strip()]:
        if w in FRAMES:
            frame = FRAMES[w]
        elif w in EMOTIONS and not emo:
            emo = w
        else:
            warn(line, f"'({w})' isn't an emotion or a camera word: emotions {', '.join(sorted(EMOTIONS))}; "
                       f"cameras {', '.join(sorted(set(FRAMES)))}")
    return emo or "neutral", frame


def parse_body(lines, start, meta, err, warn):
    """-> (segments, shots, chapters) for script_parser.parse (same shapes as the classic body loop)."""
    series = None
    try:
        series = bible.load(meta.get("series") or "")
        for f, ln, m in series["problems"]:
            err(1, f"series/{series['id']}/{f} line {ln}: {m}")
    except bible.SeriesError as e:
        err(1, str(e))
    meta["series_data"] = series
    cast = series["cast"] if series else None
    narr = series["narrator"] if series else {"on": True, "voice": "bm_george", "speed": 1.0, "fx": "none"}
    segments, shots, chapters = [], [], []
    scene = None
    pending_shot, pending_sfx, pending_pause = None, [], 0.0
    last_speaker = None
    scenes = []

    def new_scene(num, raw_place, raw_time, ln):
        nonlocal scene, last_speaker
        sid, base, grade0 = _scene_place(raw_place, series, ln, err)
        grade = _scene_time(raw_time, grade0, ln, warn)
        scene = {"index": len(scenes), "number": num, "line": ln, "place": raw_place.strip().upper(), "set_id": sid,
                 "set": base, "time": (raw_time or "").strip().upper(), "grade": grade, "blocking": [], "speakers": [],
                 "card": True}
        scenes.append(scene)
        nice = series["sets"][sid]["name"] if sid else raw_place.strip().replace("_", " ").title()
        chapters.append({"title": f"Scene {num}: {nice}", "line": ln, "segment": len(segments)})
        last_speaker = None

    for i in range(start, len(lines)):
        ln = i + 1
        s = lines[i].strip()
        if not s or s.startswith("<!--") or s.startswith("//"):
            continue
        if s.startswith("#"):
            m = SCENE_RE.match(s)
            if m:
                new_scene(int(m.group(1)), m.group(2), m.group(3), ln)
            elif re.match(r"^##\s*TO BE CONTINUED", s, re.I):
                warn(ln, "the 'To be continued' card comes with episode packaging (plan step 4); skipped for now")
            else:
                err(ln, "a heading in an episode must be '## SCENE n | PLACE | TIME', e.g. ## SCENE 1 | STREET | NIGHT")
            continue
        if s.startswith("["):
            rest = s
            for m in TAG_RE.finditer(s):
                kind, arg = m.group(1).lower(), m.group(2).strip()
                if kind == "cast":
                    if scene is None:
                        err(ln, "[cast: ...] must come after a '## SCENE n | PLACE | TIME' heading")
                        continue
                    scene["blocking"] = _blocking(arg, cast, ln, err)
                elif kind in B3.TAGS:
                    sh = B3.parse_tag(kind, arg, ln, _ErrSink(err))
                    if sh:
                        pending_shot = sh
                elif kind == "sfx":
                    if arg:
                        pending_sfx.append(arg)
                elif kind == "pause":
                    try:
                        pending_pause += max(0.0, min(5.0, float(arg.rstrip("s"))))
                    except ValueError:
                        err(ln, f"[pause: ...] needs seconds, like [pause: 1.5], got '{arg}'")
                elif kind in LATER:
                    warn(ln, f"[{kind}: ...] ({LATER[kind]}) comes with the action phase (plan step 3); skipped for now")
                else:
                    err(ln, f"unknown tag [{kind}: ...] in an episode. Use [cast:], [shot:], [sign:], [sfx:], [pause:]")
            rest = TAG_RE.sub("", s).strip()
            if rest:
                err(ln, f"text after a tag on the same line: '{rest[:40]}'. Put dialogue on its own line as NAME: line")
            continue
        m = LINE_RE.match(s)
        if not m:
            err(ln, "every line of an episode is NAME (emotion): dialogue, NARRATOR: text, a [tag] or a ## SCENE "
                    f"heading; got '{s[:50]}'")
            continue
        who, paren, text = m.group(1), m.group(2), m.group(3).strip()
        inline_sfx = [a.strip() for k, a in TAG_RE.findall(text) if k.lower() == "sfx" and a.strip()]
        text = TAG_RE.sub("", text).strip()
        if not text:
            err(ln, f"{who}: has no words to say")
            continue
        if scene is None:
            err(ln, "dialogue starts before the first scene: add '## SCENE 1 | PLACE | TIME' above it")
            new_scene(1, B3.SETS[0], "day", ln)
        words = len(re.findall(r"[A-Za-z0-9']+", text))
        if who == "NARRATOR":
            if not narr["on"]:
                warn(ln, "this series has narrator: off in series.md; the NARRATOR line is still spoken")
            emo, frame = _emotion_camera(paren, ln, warn) if paren else ("neutral", "")
            voice, speed, fx, speaker = narr["voice"], narr["speed"], narr["fx"], None
            if words > LONG_LINE + 15:
                warn(ln, f"a {words}-word narrator line; split it (one idea per line keeps the pictures moving)")
        else:
            if cast is not None and who not in cast:
                err(ln, f"{who} isn't in this series' cast: add series/{series['id'] if series else '<id>'}/cast/"
                        f"{who.lower()}.md, or use one of: {', '.join(cast) or 'no cast files yet'}")
                continue
            c = cast[who] if cast else {"voice": "am_michael", "speed": 1.0, "voice_fx": "none", "status": "alive"}
            if c.get("status") == "dead":
                warn(ln, f"{who} is dead in the cast file (status: dead) but speaks here")
            emo, frame = _emotion_camera(paren, ln, warn)
            voice, speed, fx, speaker = c["voice"], c["speed"], c["voice_fx"], who
            if words > LONG_LINE:
                warn(ln, f"{who}'s line has {words} words; people speak in short lines: keep it under "
                         f"{LONG_LINE} or split it into two lines")
            if who not in scene["speakers"]:
                scene["speakers"].append(who)
        face, rate, body, extra_fx = EMOTIONS[emo]
        if extra_fx and fx in ("", "none"):
            fx = extra_fx
        pause = pending_pause + (CARD_SEC if scene["card"] else 0.0)
        new_par = speaker != last_speaker or bool(pending_pause)
        seg = {"text": text, "line": ln, "line_end": ln, "shot": len(shots), "section": scene["place"],
               "sfx": pending_sfx + inline_sfx, "pause_before": pause, "new_paragraph": new_par,
               "voice": voice, "speed": round(speed * rate, 3), "voice_fx": "" if fx == "none" else fx,
               "speaker": speaker, "emotion": emo}
        shot = pending_shot or {"type": "line", "line": ln}
        shot.update(first_segment=len(segments), scene=scene["index"], speaker=speaker, emotion=emo, body=body,
                    frame=frame, scene_card=scene["card"])
        if not shot.get("face"):                   # an explicit [shot: ... face=...] keeps its own face
            shot["face"] = face
        if shot["type"] == "shot":
            shot["set"] = shot.get("set") or scene["set"]
        segments.append(seg)
        shots.append(shot)
        scene["card"] = False
        pending_shot, pending_sfx, pending_pause = None, [], 0.0
        last_speaker = speaker
    if pending_shot is not None:
        warn(pending_shot["line"], "the last [shot:] / [sign:] has no line after it, so it is not used")
    # blocking: [cast:] first, then everyone who speaks in the scene and wasn't placed, in speaking order
    for sc in scenes:
        placed = {n for n, _ in sc["blocking"]}
        sc["blocking"] += [(n, "") for n in sc["speakers"] if n not in placed]
        used, spots = {p for _, p in sc["blocking"] if p}, []
        for n, p in sc["blocking"]:
            if not p:
                p = next((a for a in AUTO_SPOTS if a not in used), "background")
                used.add(p)
            spots.append((n, p))
        sc["blocking"] = spots
    meta["series_scenes"] = scenes
    return segments, shots, chapters


class _ErrSink(list):
    """B3.parse_tag appends {'line', 'msg'} dicts to a list; pass them on to err()."""
    def __init__(self, err):
        super().__init__()
        self._err = err

    def append(self, e):
        self._err(e["line"], e["msg"])


def check(meta, shots, segments, err, warn, key_line):
    """Header rules + the blocky 3D cast the renderer needs. Returns the Check page's series stats."""
    s = meta.get("series_data")
    t = (meta.get("series_type") or "episode").lower()
    if t not in TYPES_ALLOWED:
        err(key_line("type"), "type: episode_short (9:16 side stories) comes later; use type: episode")
    ep = str(meta.get("episode") or "").strip()
    if not ep.isdigit():
        err(key_line("episode"), "episode: needs the episode number, like episode: 1")
    for k in ("previously", "cold_open"):
        if meta.get(k) and meta[k].lower() not in ("no", "off", "none"):
            warn(key_line(k), f"{k}: comes with episode packaging (plan step 4); ignored for now")
    if meta.get("series_theme") and meta["series_theme"].lower() not in ("auto", "none", "off"):
        warn(key_line("theme"), "theme: (the series title card + sting) comes with episode packaging; ignored for now")
    scenes = meta.get("series_scenes") or []
    if not scenes:
        err(1, "an episode needs at least one '## SCENE n | PLACE | TIME' heading and some dialogue")
    if not segments:
        err(1, "an episode needs at least one spoken line (NAME: line or NARRATOR: line)")
    # the cast as Blocky 3D sees it (lower-case names; looks from the cast files)
    cast3 = {}
    if s:
        from ..blocky3d import sets as SETS
        studio = SETS.studio("characters")
        for name in {n for sc in scenes for n, _ in sc["blocking"]}:
            c = s["cast"].get(name)
            if not c:
                continue
            cast3[name.lower()] = ({"model": studio[c["look"]], "id": c["look"], "count": 1} if c["look_kind"] == "studio"
                                   else {"preset": c["look"], "count": 1})
    meta["cast"] = cast3
    meta["set"] = scenes[0]["set"] if scenes else B3.SETS[0]
    meta["grade"] = scenes[0]["grade"] if scenes else "bright"
    for sh in shots:
        if sh["type"] == "shot":
            missing = [w for w in sh["who"] if w not in cast3]
            if missing:
                err(sh["line"], f"[shot: ...]: {', '.join(missing)} isn't in this scene; put them in [cast: ...]")
        if sh.get("face") and s:
            c = s["cast"].get(sh.get("speaker") or "")
            if c and c["look_kind"] == "preset":
                sh["face"] = RIG_FACE.get(sh["face"], sh["face"])
    speakers = {}
    for seg in segments:
        k = seg["speaker"] or "NARRATOR"
        speakers[k] = speakers.get(k, 0) + 1
    voices = {}
    if s:
        voices = {n: {"voice": c["voice"], "speed": c["speed"], "fx": c["voice_fx"]} for n, c in s["cast"].items()}
        voices["NARRATOR"] = {"voice": s["narrator"]["voice"], "speed": s["narrator"]["speed"], "fx": s["narrator"]["fx"]}
    meta.pop("series_data", None)            # (has paths; the renderer loads the bible again from meta["series"])
    return {"series": s["id"] if s else "", "series_title": s["title"] if s else "", "episode": ep,
            "scenes": [{"number": sc["number"], "place": sc["place"], "time": sc["time"], "set": sc["set"],
                        "grade": sc["grade"], "cast": [f"{n} ({p})" for n, p in sc["blocking"]]} for sc in scenes],
            "lines": speakers, "voices": {k: v for k, v in voices.items() if k in speakers},
            "fx_names": list(voicefx.NAMES)}
