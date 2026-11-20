"""Script format of rendering_method: explainer3d (docs/SCRIPT_FORMAT.md section 7): clean CG "what if" explainers.

One tag = one scene, cut where its narration starts:
    [scene: subject | camera | bg=blue | title: WHAT IF? | meter: HUNGER 78 | chart: Food 1 2 2 2 / People 1 1.4 2 2.6 | count: x8]
        subject  a model id (assets/explainer3d/models: apple, earth, smartphone ... or a blocky3d id like cars/police),
                 crowd [N] [red|green|blue]  (pictogram people),  pile <model id> xN,  food  (apple, bread, fish, rice),
                 none  (only the background + overlays)
        camera   push_in (default), pull_out, orbit, dolly, top, close
        bg=      blue (default), deep, red, space, dusk, white
        title: / meter: / chart: / count:  overlays drawn over the scene
"""

import re

from .. import config as C

MODELS_DIR = C.BASE_DIR / "assets" / "explainer3d" / "models"
TAGS = ("scene",)
CAMERAS = ("push_in", "pull_out", "orbit", "dolly", "top", "close")
BGS = ("blue", "deep", "red", "space", "dusk", "white")
COLOURS = ("red", "green", "blue")
SHOT_WARN_SEC = 5.0


def is_scene(sh) -> bool:
    """An explainer [scene:] (style: motion scripts have [scene:] tags of their own, without a subject)."""
    return sh.get("type") == "scene" and "subject" in sh


def models() -> dict:
    """{id: file relative to the repo} of the explainer models + every blocky3d model (pack/name)."""
    out = {p.stem: p.relative_to(C.BASE_DIR).as_posix() for p in MODELS_DIR.rglob("*.glb")}
    from ..blocky3d import sets as B
    out.update({i: f"assets/blocky3d/{f}" for i, f in B._index().items()})
    return out


def _subject(text, bad):
    words = text.lower().split()
    if not words or words == ["none"]:
        return {"kind": "none"}
    if words[0] == "food":
        return {"kind": "food"}
    if words[0] == "crowd":
        n = next((int(w) for w in words[1:] if w.isdigit()), 200)
        col = next((w for w in words[1:] if w in COLOURS), "red")
        if not 1 <= n <= 800:
            return bad("[scene: crowd N]: N must be 1-800")
        return {"kind": "crowd", "n": n, "colour": col}
    if words[0] == "pile":
        m = re.fullmatch(r"pile\s+(\S+)\s+x(\d+)", text.strip().lower())
        if not m:
            return bad("[scene: pile <model> xN]: e.g. pile apple x8")
        return {"kind": "pile", "model": m.group(1), "n": int(m.group(2))}
    return {"kind": "model", "model": text.strip().lower()}


def parse_tag(kind, arg, line, errors):
    def bad(msg):
        errors.append({"line": line, "msg": msg})

    parts = [p.strip() for p in arg.split("|")]
    subj = _subject(parts[0], bad)
    if subj is None:
        return None
    shot = {"type": "scene", "line": line, "subject": subj, "camera": "push_in", "bg": "blue"}
    for p in parts[1:]:
        if not p:
            continue
        m = re.fullmatch(r"(title|meter|chart|count)\s*:\s*(.+)", p, re.I)
        if m:
            k, v = m.group(1).lower(), m.group(2).strip()
            if k == "meter":
                mm = re.fullmatch(r"(.+?)\s+(\d{1,3})\s*%?", v)
                if not mm or int(mm.group(2)) > 100:
                    return bad("[scene: ... | meter: LABEL 78]: a label and a percentage 0-100")
                v = {"label": mm.group(1).upper(), "value": int(mm.group(2))}
            if k == "chart":
                series = []
                for s in v.split("/"):
                    ws = s.split()
                    try:
                        series.append({"name": " ".join(w for w in ws if not re.fullmatch(r"[\d.]+", w)),
                                       "values": [float(w) for w in ws if re.fullmatch(r"[\d.]+", w)]})
                    except ValueError:
                        series = []
                    if not series or len(series[-1]["values"]) < 2:
                        return bad("[scene: ... | chart: Food 1 2 2 / People 1 1.5 2.4]: each line = a name and 2+ numbers")
                v = series[:3]
            shot[k] = v
        elif re.fullmatch(r"bg\s*=\s*\w+", p, re.I):
            v = p.split("=", 1)[1].strip().lower()
            if v not in BGS:
                return bad(f"[scene: ...]: bg must be one of {', '.join(BGS)}, got '{v}'")
            shot["bg"] = v
        elif p.lower().replace(" ", "_") in CAMERAS:
            shot["camera"] = p.lower().replace(" ", "_")
        else:
            return bad(f"[scene: subject | camera | bg=... | title: / meter: / chart: / count: ...]: don't know "
                       f"'{p}' (cameras: {', '.join(CAMERAS)})")
    return shot


def check(meta, shots, err, warn):
    known = models()
    for sh in shots:
        if not is_scene(sh) and not sh.get("placeholder"):
            err(sh["line"], f"[{sh['type']}: ...] isn't used by explainer3d videos; use [scene: subject | camera | ...]")
            continue
        s = sh.get("subject") or {}
        mid = s.get("model")
        if mid and mid not in known:
            err(sh["line"], f"[scene: ...]: no model '{mid}' (assets/explainer3d/models, or a blocky3d id like cars/police)")
        if sh.get("est_dur", 0) > SHOT_WARN_SEC:
            warn(sh["line"], f"this scene stays on screen ~{sh['est_dur']:.0f} s; explainers cut every 2-4 s, add another "
                             f"[scene:] inside that narration")
    used = [sh for sh in shots if is_scene(sh)]
    if not used:
        err(1, "an explainer3d video needs at least one [scene: ...]")
    return {"scenes": len(used), "subjects": sorted({(s["subject"].get("model") or s["subject"]["kind"]) for s in used}),
            "overlays": sum(1 for s in used for k in ("title", "meter", "chart", "count") if s.get(k))}
