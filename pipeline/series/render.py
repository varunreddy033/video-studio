"""Web-series episodes (rendering_method: series): the Blocky 3D engine at 16:9 with dialogue.

The voice, render, sound and encode steps are pipeline/three_video.py; the 3D world is pipeline/blocky3d/js/world.js
(its "web series" section). What this module adds:

  framing    one shot per spoken line, picked automatically: a two-shot when a scene opens and every few lines,
             the speaker's close-up otherwise, the listener's reaction for the second part of a long line, a wide
             shot for the narrator; `(close)`, `(two_shot)`, `(wide)`... in the script win
  blocking   [cast: KAI at left, ...] positions, everyone turned towards the others (cheated a little to camera)
  acting     each character's own face per line (their emotion), the speaker's mouth on their own words only,
             talk gestures for the speaker, small nods for the listener
  cards      a scene card (SCENE 1 / HARBOUR STREET / NIGHT) held over a wide shot before each scene
  subtitles  the line in the bottom third (the .srt is made as for every video)
"""

import html as _html
import json
from pathlib import Path

from .. import three_video
from ..blocky3d import render as B3R
from ..blocky3d import sets as SETS
from . import bible
from .script import POSITIONS

NAME, LABEL = "series", "web series"
JS_SRC = B3R.JS_SRC
FONTS = B3R.FONTS
REACT_AFTER = 4.2            # a line longer than this (s) cuts to the listener for its last part
TWO_EVERY = 4                # a two-shot every few dialogue lines of a scene
CARD_LEAD = 0.15             # the line's shot starts this long before its first word


def ready():
    return B3R.ready()


def _subtitles(words_by_line):
    """[(t0, t1, [words])] per line -> caption chunks of up to 7 words (two lines at most on 16:9)."""
    caps = []
    for words in words_by_line:
        chunk = []
        for k, w in enumerate(words):
            chunk.append(w)
            last = k == len(words) - 1
            if len(chunk) >= 7 or last or (len(chunk) >= 4 and w[0][-1:] in ".,!?"):
                t1 = chunk[-1][2] + 0.25 if last else words[k + 1][1]
                caps.append({"t0": round(chunk[0][1], 3), "t1": round(t1, 3),
                             "html": _html.escape(" ".join(x[0] for x in chunk))})
                chunk = []
    for a, b in zip(caps, caps[1:]):           # never two on screen
        a["t1"] = min(a["t1"], b["t0"])
    return caps


def _frame(sh, scene_people, counter, listener):
    """The framing of one dialogue line (see the module doc)."""
    if sh.get("frame"):
        return sh["frame"]
    if not sh.get("speaker"):
        return "wide" if counter["narr"] % 2 == 0 else ("two" if len(scene_people) > 1 else "medium")
    if len(scene_people) < 2:
        return "close" if counter["talk"] % 2 else "medium"
    if counter["talk"] == 0 or counter["talk"] % TWO_EVERY == 0:
        return "two"
    return "ots" if counter["talk"] % 3 == 1 and listener else "close"


def build(meta, parsed, spans, words, W, H, project, warnings):
    s = bible.load(meta["series"])
    scenes = meta["series_scenes"]
    cast = B3R.cast_data(meta["cast"])
    tl = parsed["timeline"]
    segs = parsed["segments"]
    seg_words = [[[w[0], round(tl[k]["start"] + w[1], 3), round(tl[k]["start"] + w[2], 3)] for w in tl[k]["words"]]
                 for k in range(len(tl))]
    speech_by = {}
    for k, seg in enumerate(segs):
        if seg.get("speaker"):
            speech_by.setdefault(seg["speaker"].lower(), []).extend([w[1], w[2]] for w in seg_words[k])
    out, mood = [], {}                       # mood: each character's last face in the scene (their listening face)
    counter = {"talk": 0, "narr": 0}
    cur_scene, last_speaker = -1, None
    for i, (sh, (st, d)) in enumerate(zip(parsed["shots"], spans)):
        sc = scenes[sh["scene"]]
        if sh["scene"] != cur_scene:
            cur_scene, last_speaker, mood = sh["scene"], None, {}
            counter = {"talk": 0, "narr": 0}
        people = [{"name": n.lower(), "x": POSITIONS[p][0], "z": POSITIONS[p][1]} for n, p in sc["blocking"]
                  if n.lower() in cast]
        names = [p["name"] for p in people]
        k = sh["first_segment"]
        line_start = tl[k]["start"] - CARD_LEAD
        end = st + d
        base = {"set": sc["set"], "grade": sc["grade"], "people": people, "seed": round(i * 0.37, 2)}
        if sh.get("scene_card"):
            # the card fills the pause before the scene's first line: from just after the last word of the line
            # before (that shot is cut short there) to just before the first word of this one
            c0 = 0.0 if k == 0 else min(line_start - 0.5, tl[k - 1]["start"] + tl[k - 1]["dur"] + 0.3)
            if out:
                out[-1]["end"] = round(c0, 3)
            out.append(dict(base, type="card", start=round(c0, 3), end=round(line_start, 3), frame="wide",
                            card={"number": sc["number"], "place": _place_name(s, sc), "time": sc["time"].title()}))
            st = line_start
        speaker = (sh.get("speaker") or "").lower() or None
        if speaker:
            mood[speaker] = sh.get("face") or "neutral"
        listener = next((n for n in [last_speaker] + names if n and n != speaker and n in names), None)
        faces = {n: mood.get(n, "neutral") for n in names}
        if sh["type"] in ("shot", "sign"):                  # an explicit Blocky 3D tag: drawn the Blocky 3D way
            out.append({"type": sh["type"], "start": round(st, 3), "end": round(end, 3), "who": sh.get("who", []),
                        "action": sh.get("action", "idle"), "camera": sh.get("camera", "auto"),
                        "set": sh.get("set") or sc["set"], "grade": sc["grade"], "face": sh.get("face", ""),
                        "sign": sh.get("sign", ""), "text": sh.get("text", ""), "seed": i * 0.37, "prop": sh.get("prop", "")})
        else:
            frame = _frame(sh, names, counter, listener)
            focus = speaker if speaker in names else (names[0] if names else None)
            line = dict(base, type="line", start=round(st, 3), end=round(end, 3), frame=frame, speaker=speaker,
                        focus=focus, listener=listener, faces=faces, body=sh.get("body", "talk"))
            ws = seg_words[k]
            split = None
            if speaker and listener and frame in ("close", "ots", "medium") and len(ws) > 6 and \
                    ws[-1][2] - ws[0][1] > REACT_AFTER:
                target = ws[0][1] + 0.62 * (ws[-1][2] - ws[0][1])
                split = min((w[1] for w in ws[3:-2]), key=lambda t: abs(t - target), default=None)
            if split:
                out.append(dict(line, end=round(split - 0.04, 3)))
                out.append(dict(line, start=round(split - 0.04, 3), frame="react", focus=listener))
            else:
                out.append(line)
            counter["talk" if speaker else "narr"] += 1
        if speaker:
            last_speaker = speaker
    used_sets = sorted({x["set"] for x in out})
    layouts = {name: SETS.layout(name) for name in used_sets}
    for name, lay in layouts.items():
        if lay["missing"]:
            warnings.append(f"set {name}: {len(lay['missing'])} model(s) missing from assets/blocky3d: "
                            f"{', '.join(lay['missing'][:4])}")
    studio_props = SETS.studio("props")
    props = {x["prop"]: studio_props[x["prop"]] for x in out if x.get("prop")}
    faces = sorted({f.name[5:-4] for f in (SETS.BASE / "studio/textures/faces").glob("face_*.png")}) \
        if any(c.get("model") for c in cast.values()) else []
    page_caps = not meta.get("captions")
    data = {"W": W, "H": H, "grade": scenes[0]["grade"] if scenes else "bright", "series": True, "cast": cast,
            "shots": out, "sets": layouts, "props": props, "studio_faces": faces, "speech": [[w[1], w[2]] for w in words],
            "speech_by": speech_by,
            "caps": _subtitles(seg_words) if page_caps else []}
    files = [p["file"] for lay in layouts.values() for p in lay["props"]]
    files += [c["model"] for c in cast.values() if c.get("model")] + list(props.values())
    files += [f"studio/textures/faces/face_{f}.png" for f in faces]
    n = three_video.copy_files(SETS.BASE, files, project / "models")
    total = max(x["end"] for x in out)
    frames = {}
    for x in out:
        frames[x.get("frame") or x["type"]] = frames.get(x.get("frame") or x["type"], 0) + 1
    line = (f"{len(out)} shots ({', '.join(f'{k} {v}' for k, v in sorted(frames.items()))}), {len(scenes)} scenes, "
            f"sets {', '.join(used_sets)}, {n} model files, voices {len(speech_by)} + narrator")
    summary = {"shots": len(out), "frames": frames, "scenes": len(scenes), "sets": used_sets, "models": n,
               "series": s["id"], "episode": meta.get("episode")}
    return data, _index_html(data, W, H, total, meta.get("title", "")), out, summary, line


def _place_name(s, sc):
    st = s["sets"].get(sc["set_id"]) if sc.get("set_id") else None
    return (st["name"] if st else sc["place"].replace("_", " ").title()).upper()


def _index_html(data, W, H, total, title):
    page = B3R._index_html(data, W, H, three_video.C.FPS, total, title)
    fs = int(H * 0.045)
    extra = f"""
#cap {{ top: auto; bottom: {int(H * 0.07)}px; width: {int(W * 0.74)}px; font-family: "Barlow-Black"; font-size: {fs}px;
  line-height: 1.18; -webkit-text-stroke: {max(3, fs // 9)}px #0b0b10; text-shadow: 0 {max(2, fs // 14)}px {max(4, fs // 5)}px rgba(0,0,0,.55); }}
#card {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 50% 55%, rgba(10,8,20,.35), rgba(10,8,20,.78)); opacity: 0; color: #fff; text-align: center; }}
#card .n {{ font-family: "SpaceMono-Bold"; font-size: {int(H * 0.03)}px; letter-spacing: .5em; color: #c9bbff; margin-left: .5em; }}
#card .p {{ font-family: "Barlow-Black"; font-size: {int(H * 0.115)}px; line-height: 1; margin: {int(H * 0.02)}px 0; letter-spacing: .02em; }}
#card .t {{ font-family: "SpaceMono-Bold"; font-size: {int(H * 0.028)}px; letter-spacing: .35em; color: #ffffffb3; margin-left: .35em; }}
#card .rule {{ width: {int(W * 0.14)}px; height: {max(2, int(H * 0.004))}px; background: #a78bfa; transform-origin: 50% 50%; }}
#bars i {{ position: absolute; left: 0; right: 0; height: {int(H * 0.06)}px; background: #000; }}
"""
    page = page.replace("</style>", extra + "</style>", 1)
    page = page.replace('<div id="cap"></div>',
                        '<div id="card"><div class="n" id="cardN"></div><div class="rule" id="cardR"></div>'
                        '<div class="p" id="cardP"></div><div class="t" id="cardT"></div></div>\n  <div id="cap"></div>', 1)
    return page


def cues(shots):
    """Sound: a low whoosh into every scene card, a pop on signs; dialogue cuts stay quiet (no whoosh per cut)."""
    out = [(x["start"] + 0.05, "whoosh") for x in shots if x["type"] == "card"]
    out += [(x["start"] + 0.05, "pop") for x in shots if x["type"] == "sign"]
    return out


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    import sys
    return three_video.render(sys.modules[__name__], parsed, job_dir, mode, progress)


def scene_list(parsed) -> list:
    """For tests / the Check page: [(scene number, place, grade, people)]."""
    return [(sc["number"], sc["place"], sc["grade"], [n for n, _ in sc["blocking"]]) for sc in parsed["meta"]["series_scenes"]]


def dump(data) -> str:
    return json.dumps(data)
