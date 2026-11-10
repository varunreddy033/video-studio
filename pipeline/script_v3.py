"""
script_v3.py  -  the body of a `style: motion` script (docs/SCRIPT_FORMAT.md, "Motion style").

    [scene: name | from: right]        a new scene; how the camera arrives (right left top bottom | zoom <id> | cut)
    [char: pose | left]                the presenter (Sterling Flat) in the scene; lip-sync is automatic
    [+ door: FUND | 1 of 4 | grow]     add an element at the next spoken word: kind[: text] | place | animation
    [+ gen: white wired earphones | right | slide]   an AI-made flat prop (phase 5), cached
    [- door: FUND] / [- bubble]        remove an element at the next word
    [head: FOUR DOORS INTO YOUR MONEY] the headline pill; its words light up as they are spoken
    [label: TOP 10 = 40% | door: FUND] a label tag pointing at an element
    [number: ...] [chart: ...] [quote: ...] [card: ...]   in-scene data elements (classic syntax)
    [talk: pose | set]                 Sterling full screen, as its own scene (punchy moments)
    [ai: ...] [stock: ...]             a full-frame picture as its own scene
    [sfx: ...] [pause: ...] and ## chapters work as in classic scripts.

Every cue is stored as (segment, token): the n-th word of that segment's narration. The renderer maps it onto
Kokoro's real word timings (pipeline/motion.py), so a pop lands exactly on its word.
"""

import json
import re

from . import config as C
from . import script_parser as SP

WORD_RE = re.compile(r"[A-Za-z0-9']+")
ANIMS = {"pop", "grow", "slide", "fade", "draw", "drop", "none", "count", "shake"}
SIZES = {"tiny", "small", "medium", "large", "big", "huge"}
SIDES = {"left", "right", "center", "centre", "top", "bottom", "top-left", "top-right", "bottom-left",
         "bottom-right", "middle", "floor", "sky"}
FROM_DIRS = {"right": "from-right", "left": "from-left", "top": "from-top", "bottom": "from-bottom"}
# element kinds the renderer draws: motion/src/library/catalog.json (shared with Remotion)
CATALOG = json.loads((C.BASE_DIR / "motion" / "src" / "library" / "catalog.json").read_text(encoding="utf-8"))
DATA_KINDS = {"number", "chart", "quote", "card"}                 # classic syntax, as in-scene elements
NEW_DATA = {"pie", "compare", "ranking", "map"}                   # motion-only data components
SCENE_SHOTS = {"talk", "ai", "stock"}
PROPS = set(CATALOG["props"]) | {"label"}


def _pairs(text: str, line: int, err, what: str):
    """'A: 40, B: 35' -> [["A", 40.0], ["B", 35.0]] (values may carry $ , %)."""
    out = []
    for item in [x for x in text.split(",") if x.strip()]:
        if ":" not in item:
            err(line, f"[{what}: ...] items look like 'label: number', got '{item.strip()}'")
            return None
        k, v = item.rsplit(":", 1)
        try:
            out.append([k.strip(), float(v.strip().replace("$", "").replace("%", "").replace(",", ""))])
        except ValueError:
            err(line, f"[{what}: ...] '{v.strip()}' is not a number")
            return None
    return out


def _new_data(kind: str, arg: str, line: int, err):
    """[pie: title | A: 40, B: 60 | place]  [ranking: title | A: 3, B: 5 | place]
       [compare: LEFT LABEL: $13B | RIGHT LABEL: $38.5B | place]  [map: India, China | pin=37.77,-122.42 | place]"""
    parts = [x.strip() for x in arg.split("|")]
    place = size = anim = None
    keep, opts = [], {}
    for j, p in enumerate(parts):
        low = p.lower()
        if j and low in ANIMS:
            anim = low
        elif j and low in SIZES:
            size = low
        elif j and _position(p) and not re.search(r"[a-z]{3,}\s*:", low):
            place = _position(p)
        elif j and re.fullmatch(r"[a-z_]+\s*=.+", p, re.I):
            k, v = p.split("=", 1)
            opts[k.strip().lower()] = v.strip()
        else:
            keep.append(p)
    data = {}
    if kind in ("pie", "ranking"):
        if len(keep) < 2:
            err(line, f"[{kind}: title | label: number, label: number, ...]")
            return None
        pairs = _pairs(keep[1], line, err, kind)
        if not pairs or len(pairs) < 2:
            if pairs is not None:
                err(line, f"[{kind}: ...] needs at least 2 items")
            return None
        data = {"title": keep[0], "data": pairs, "unit": opts.get("unit", "")}
    elif kind == "compare":
        if len(keep) < 2:
            err(line, "[compare: LEFT LABEL: value | RIGHT LABEL: value]")
            return None
        sides = []
        for side in keep[:2]:
            m = re.fullmatch(r"(.+?):\s*([^\d\-+]*)([-+]?[\d,]*\.?\d+)(.*)", side)
            if not m:
                err(line, f"[compare: ...] each side looks like 'Label: $13B', got '{side}'")
                return None
            sides.append([m.group(1).strip(), float(m.group(3).replace(",", "")),
                          (m.group(2) + "{v}" + m.group(4)).strip()])
        data = {"left": sides[0], "right": sides[1], "title": keep[2] if len(keep) > 2 else ""}
    else:   # map
        countries = [c.strip() for c in keep[0].split(",") if c.strip()]
        data = {"countries": countries, "pin": opts.get("pin", ""), "pinLabel": opts.get("label", "")}
    return {"op": "add", "kind": kind, "text": "", "id": None, "place": place, "anim": anim, "size": size,
            "opts": {}, "data": data, "line": line}


def tokens(text: str):
    return WORD_RE.findall(SP._clean(text))


def _position(part: str):
    p = part.strip().lower()
    if p in SIDES:
        return {"side": "center" if p in ("centre", "middle") else p}
    m = re.fullmatch(r"(\d+)\s*of\s*(\d+)", p)
    if m and 1 <= int(m.group(1)) <= int(m.group(2)) <= 12:
        return {"slot": int(m.group(1)), "of": int(m.group(2))}
    m = re.fullmatch(r"over\s+(.+)", p)
    if m:
        return {"over": m.group(1).strip()}
    m = re.fullmatch(r"(\d{1,3})%?\s*,\s*(\d{1,3})%?", p)
    if m:
        return {"x": int(m.group(1)) / 100, "y": int(m.group(2)) / 100}
    return None


def _element(arg: str, line: int, err):
    """'door: FUND #fund | 1 of 4 | grow | color=teal' -> element dict."""
    parts = [x.strip() for x in arg.split("|")]
    head = parts[0]
    m = re.fullmatch(r"([a-z][a-z0-9_-]*)\s*(?::\s*(.*))?", head, re.I | re.S)
    if not m:
        err(line, f"[+ {arg}]: start with what to add, like [+ door: FUND | 1 of 4 | grow]")
        return None
    kind, text = m.group(1).lower(), (m.group(2) or "").strip()
    eid = None
    mm = re.search(r"\s#([A-Za-z0-9_-]+)\s*$", " " + text)
    if mm:
        eid, text = mm.group(1).lower(), text[: len(text) - len(mm.group(0)) + 1].strip()
    el = {"kind": kind, "text": text, "id": eid, "place": None, "anim": None, "size": None, "opts": {}, "line": line}
    for p in parts[1:]:
        if not p:
            continue
        low = p.lower()
        if low in ANIMS:
            el["anim"] = low
        elif low in SIZES:
            el["size"] = low
        elif "=" in p and re.fullmatch(r"[a-z_]+\s*=\s*\S.*", p, re.I):
            k, v = p.split("=", 1)
            el["opts"][k.strip().lower()] = v.strip()
        elif _position(p):
            el["place"] = _position(p)
        else:
            err(line, f"[+ {kind}: ...]: don't know '{p}'. Use a place (left, right, center, 2 of 4, over char), "
                      f"an animation ({', '.join(sorted(ANIMS))}) or a size ({', '.join(sorted(SIZES))})")
    if kind == "gen" and not text:
        err(line, "[+ gen: ...] needs a description of the prop, like [+ gen: a pair of white wired earphones]")
    return el


def parse_body(lines, start, meta, err, warn):
    """Returns (segments, shots, chapters). shots = one entry per scene (type 'scene', or 'talk'/'ai'/'stock' for
    full-frame scenes), each with first_segment and its events, so the classic voice/timeline code works unchanged."""
    segments, shots, chapters = [], [], []
    section = ""
    pending_sfx, pending_pause = [], 0.0
    para_open = False
    pending_events = []           # events waiting for the next spoken word
    open_scene = None             # a scene tag waiting for its first narration

    def new_scene(sc):
        nonlocal open_scene, para_open
        if open_scene is not None and open_scene.get("first_segment") is None:
            warn(open_scene["line"], "this scene has no narration, so it is skipped")
        open_scene = sc
        para_open = False

    def add_text(chunk, line):
        nonlocal pending_sfx, pending_pause, para_open, open_scene, pending_events
        chunk = SP._clean(chunk)
        if not chunk:
            return
        if open_scene is None and not shots:
            err(line, "narration starts before any scene. Put a [scene: ...] tag above it")
            open_scene = {"type": "scene", "name": "plain", "from": None, "line": line, "events": []}
        starting = open_scene is not None and open_scene.get("first_segment") is None
        if starting:
            open_scene["first_segment"] = len(segments)
            shots.append(open_scene)
        sc_idx = len(shots) - 1
        same = segments and not starting and para_open and not pending_sfx and not pending_pause
        if same:
            seg = segments[-1]
            tok0 = len(tokens(seg["text"]))
            seg["text"] += " " + chunk
            seg["line_end"] = line
        else:
            seg = {"text": chunk, "line": line, "line_end": line, "shot": sc_idx, "section": section,
                   "sfx": pending_sfx, "pause_before": pending_pause, "new_paragraph": not para_open}
            segments.append(seg)
            tok0 = 0
            pending_sfx, pending_pause = [], 0.0
        para_open = True
        for ev in pending_events:          # cue = the first word of this chunk
            ev["cue"] = {"seg": len(segments) - 1, "tok": tok0}
            shots[sc_idx]["events"].append(ev)
        pending_events = []

    for i in range(start, len(lines)):
        ln = i + 1
        s = lines[i].rstrip().strip()
        if not s:
            para_open = False
            continue
        if s.startswith("<!--") or s.startswith("//"):
            continue
        if re.match(r"^#{1,3}\s", s):
            section = s.lstrip("#").strip()
            chapters.append({"title": section, "line": ln, "segment": len(segments)})
            para_open = False
            continue
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            para_open = False
            continue
        pos = 0
        for m in re.finditer(r"\[\s*([+-])\s*([^\]]*)\]|\[(\w+)\s*:\s*([^\]]*)\]", s):
            add_text(s[pos:m.start()], ln)
            pos = m.end()
            if m.group(1):                                  # [+ ...] / [- ...]
                op, arg = m.group(1), m.group(2).strip()
                if not arg:
                    err(ln, f"[{op}] needs something: [+ door: FUND | grow] or [- door]")
                    continue
                if op == "+":
                    el = _element(arg, ln, err)
                    if el:
                        pending_events.append({"op": "add", **el})
                else:
                    pending_events.append({"op": "remove", "target": arg.lower(), "line": ln})
                continue
            kind, arg = m.group(3).lower(), m.group(4).strip()
            if kind == "scene":
                parts = [x.strip() for x in arg.split("|")]
                name = (parts[0] or "plain").lower()
                frm, opts = None, {}
                for p in parts[1:]:
                    low = p.lower()
                    mm = re.fullmatch(r"from\s*:\s*(.+)", low)
                    if mm:
                        v = mm.group(1).strip()
                        if v in FROM_DIRS:
                            frm = {"type": "push", "dir": FROM_DIRS[v]}
                        elif v == "cut":
                            frm = {"type": "cut"}
                        elif v.startswith("zoom"):
                            frm = {"type": "zoom", "target": v[4:].strip() or None}
                        elif v in ("iris", "whip", "fade"):
                            frm = {"type": v}
                        else:
                            err(ln, f"[scene: ... | from: {v}]: use right, left, top, bottom, zoom <element>, "
                                    f"iris, whip, fade or cut")
                    elif "=" in p:
                        k, v = p.split("=", 1)
                        opts[k.strip().lower()] = v.strip()
                    else:
                        err(ln, f"[scene: {name} | ...]: don't know '{p}' (use from: right, or palette=light)")
                new_scene({"type": "scene", "name": name, "from": frm, "opts": opts, "line": ln, "events": []})
            elif kind in SCENE_SHOTS:
                sh = SP._parse_visual(kind, arg, ln, [])
                if sh is None:
                    err(ln, f"[{kind}: {arg}] isn't valid")
                    continue
                sh.update(events=[], name=kind, **{"from": None})
                new_scene(sh)
            elif kind == "char":
                parts = [x.strip() for x in arg.split("|")]
                ev = {"op": "char", "pose": (parts[0] or "neutral").lower(), "place": None, "size": None, "line": ln}
                for p in parts[1:]:
                    if p.lower() in SIZES:
                        ev["size"] = p.lower()
                    elif _position(p):
                        ev["place"] = _position(p)
                    elif p.lower() in ("off", "out", "hide"):
                        ev["op"] = "char_off"
                    else:
                        err(ln, f"[char: {parts[0]} | {p}]: use a place (left, right, center) or a size")
                pending_events.append(ev)
            elif kind == "head":
                if not arg:
                    err(ln, "[head: ...] needs the headline text")
                    continue
                pending_events.append({"op": "head", "text": arg, "line": ln})
            elif kind == "label":
                parts = [x.strip() for x in arg.split("|")]
                ev = {"op": "label", "text": parts[0], "target": (parts[1].lower() if len(parts) > 1 else None),
                      "place": _position(parts[2]) if len(parts) > 2 else None, "line": ln}
                pending_events.append(ev)
            elif kind in DATA_KINDS:
                # place / size / animation words are ours; the rest is the classic [number:]/[chart:]... syntax
                parts = [x.strip() for x in arg.split("|")]
                keep, place, size, anim = [parts[0]], None, None, None
                for j, p in enumerate(parts[1:], start=1):
                    low = p.lower()
                    if low in ANIMS:
                        anim = low
                    elif low in SIZES:
                        size = low
                    elif _position(p) and (kind != "chart" or j >= 3):      # chart: type | title | data | place
                        place = _position(p)
                    else:
                        keep.append(p)
                errs = []
                sh = SP._parse_visual(kind, " | ".join(keep), ln, errs)
                for e in errs:
                    err(e["line"], e["msg"])
                if sh:
                    data = {k: v for k, v in sh.items() if k not in ("type", "line")}
                    pending_events.append({"op": "add", "kind": kind, "text": sh.get("text", ""), "id": None,
                                           "place": place, "anim": anim, "size": size, "opts": {}, "data": data,
                                           "line": ln})
            elif kind in NEW_DATA:
                ev = _new_data(kind, arg, ln, err)
                if ev:
                    pending_events.append(ev)
            elif kind == "sfx":
                if arg:
                    pending_sfx.append(arg)
            elif kind == "pause":
                try:
                    pending_pause += max(0.0, min(5.0, float(arg.rstrip("s"))))
                except ValueError:
                    err(ln, f"[pause: ...] needs seconds, like [pause: 1.5], got '{arg}'")
            elif kind in ("act", "card"):
                err(ln, f"[{kind}: ...] is a classic tag; in motion scripts use [+ ...] elements and [scene: ...]")
            else:
                err(ln, f"unknown tag [{kind}: ...] in a motion script. Use [scene:], [char:], [+ ...], [- ...], "
                        f"[head:], [label:], [number:], [chart:], [pie:], [compare:], [ranking:], [map:], [quote:], "
                        f"[talk:], [sfx:], [pause:]")
        add_text(s[pos:], ln)
    if pending_events:
        warn(pending_events[0]["line"], "these tags have no narration after them, so they never appear")
    if open_scene is not None and open_scene.get("first_segment") is None:
        warn(open_scene["line"], "the last scene has no narration, so it is skipped")
    return segments, shots, chapters


def check(meta, segments, shots, warn, err, wps):
    """Motion pacing rules (MOTION_PLAN.md): something changes at least every 3 s, a new scene every 6-15 s,
    a headline in every scene, transitions vary. Returns per-scene estimates for the Check page."""
    char = meta.get("character_data")
    seg_t = {}
    for k, seg in enumerate(segments):
        seg_t[k] = (seg["est_start"], seg["est_dur"], max(1, len(tokens(seg["text"]))))

    def est(cue):
        st, dur, n = seg_t[cue["seg"]]
        return st + dur * min(cue["tok"], n) / n

    out = []
    prev_tr = []
    for k, sh in enumerate(shots):
        segs = [s for s in segments if s["shot"] == k]
        start = segs[0]["est_start"]
        end = segs[-1]["est_start"] + segs[-1]["est_dur"]
        dur = end - start
        evs = sh.get("events", [])
        kinds = [e.get("kind") or e["op"] for e in evs]
        full = sh["type"] in SCENE_SHOTS
        if not full:
            if dur > 15:
                warn(sh["line"], f"this scene runs ~{dur:.0f} s; motion scenes work best at 6-15 s. Start a new "
                                 f"[scene: ...] inside it")
            elif dur < 4 and k + 1 < len(shots):
                warn(sh["line"], f"this scene is only ~{dur:.0f} s; at least 6 s lets its elements land")
            if not any(e["op"] == "head" for e in evs):
                warn(sh["line"], "no [head: ...] in this scene: every scene should have a headline pill")
            times = sorted([start] + [est(e["cue"]) for e in evs if "cue" in e] + [end])
            gaps = [(times[j + 1] - times[j], times[j]) for j in range(len(times) - 1)]
            long_gap = max(gaps, default=(0, start))
            if long_gap[0] > 3.5:
                warn(sh["line"], f"nothing new appears for ~{long_gap[0]:.0f} s in this scene (from about "
                                 f"{int(long_gap[1] // 60)}:{int(long_gap[1] % 60):02d}); add a [+ ...] or [label: ...] "
                                 f"every 3 s or so")
        for e in evs:
            if e["op"] in ("char", "char_off") and not char:
                err(e["line"], "[char: ...] needs a presenter: add 'character: sterling_flat' (or another) to the header")
            if e["op"] == "char" and char and e["pose"] not in char["poses"]:
                err(e["line"], f"pose '{e['pose']}' isn't in {char['name']}'s poses: {', '.join(char['poses'])}")
            if e["op"] == "add" and e["kind"] not in PROPS | DATA_KINDS | NEW_DATA | {"gen"}:
                warn(e["line"], f"'{e['kind']}' isn't in the prop library yet; it's drawn as a labelled placeholder")
        if sh["type"] == "talk" and not char:
            err(sh["line"], "[talk: ...] needs a presenter: add 'character: <name>' to the header")
        tr = sh.get("from")
        trk = (tr or {}).get("type", "auto") + (tr or {}).get("dir", "")
        if k > 0 and tr and len(prev_tr) >= 2 and prev_tr[-1] == trk and prev_tr[-2] == trk:
            warn(sh["line"], "three scenes in a row arrive the same way; vary the transitions (from: left, top, "
                             "zoom <element>...)")
        if k > 0:
            prev_tr.append(trk)
        out.append({"index": k, "line": sh["line"], "name": sh.get("name"), "type": sh["type"],
                    "est_start": round(start, 1), "est_dur": round(dur, 1),
                    "transition": tr, "elements": len([e for e in evs if e["op"] == "add"]),
                    "headline": next((e["text"] for e in evs if e["op"] == "head"), ""), "kinds": kinds})
    return out
