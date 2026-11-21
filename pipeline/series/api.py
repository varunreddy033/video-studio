"""What the Video Studio page needs about web series (render_server.py /api/series...): the list for the menu, one
series for its page (bible, arc strip, cast grid, sets, episodes with their render status) and "hear voice".
"""

import re

from .. import config as C
from .. import jobs, presets, voice
from ..util import PipelineError, h
from . import bible, voicefx

PREVIEWS = C.BASE_DIR / "output" / "series_previews"          # made once per voice + speed + effect + text, not in git
STATUS_ORDER = {"done": 4, "draft_ready": 3, "rendering": 2, "queued": 2, "failed": 1, "script": 0}


def _jobs_by_episode():
    """{(series id, episode number): newest job state} from the jobs' own fields (jobs.save_script)."""
    out = {}
    for st in jobs.list_jobs():           # newest first
        sid, ep = st.get("series"), str(st.get("episode") or "")
        if sid and ep.isdigit() and (sid, int(ep)) not in out:
            out[(sid, int(ep))] = st
    return out


def _job_view(st):
    if not st:
        return None
    return {"id": st["id"], "status": st.get("status"), "mode": st.get("mode"), "done": st.get("done"),
            "total": st.get("total"), "stage": st.get("stage"),
            "duration": (st.get("final") or st.get("draft") or {}).get("duration_sec"),
            "has_final": bool(st.get("final")), "has_draft": bool(st.get("draft"))}


def _episodes(s, by_ep):
    eps = []
    for e in s["episodes"]:
        eps.append(dict(e, job=_job_view(by_ep.get((s["id"], e["episode"])))))
    return eps


def list_all():
    by_ep = _jobs_by_episode()
    out = []
    for sid in bible.ids():
        try:
            s = bible.load(sid)
        except bible.SeriesError as e:
            out.append({"id": sid, "title": sid, "error": str(e), "episodes": []})
            continue
        out.append({"id": sid, "title": s["title"], "logline": s["meta"].get("logline", ""),
                    "episodes": _episodes(s, by_ep), "cast": len(s["cast"]), "problems": len(s["problems"])})
    return out


def detail(series_id):
    s = bible.load(series_id)
    by_ep = _jobs_by_episode()
    eps = _episodes(s, by_ep)
    written = {e["episode"]: e for e in eps}
    arc = []
    for a in s["arc"]:
        e = written.get(a["episode"])
        j = (e or {}).get("job") or {}
        state = ("rendered" if j.get("has_final") else "draft" if j.get("has_draft")
                 else "rendering" if j.get("status") in ("queued", "rendering") else "written" if e else "planned")
        arc.append(dict(a, state=state, file=(e or {}).get("file"), job=j.get("id")))
    for n, e in written.items():                     # episodes that the arc doesn't list yet
        if not any(a["episode"] == n for a in s["arc"]):
            j = e.get("job") or {}
            arc.append({"episode": n, "title": e["title"], "summary": "", "file": e["file"], "job": j.get("id"),
                        "state": "rendered" if j.get("has_final") else "draft" if j.get("has_draft") else "written"})
    arc.sort(key=lambda a: a["episode"])
    from ..blocky3d import sets as SETS
    import json
    try:
        cat = {c["id"]: c for c in json.loads((SETS.BASE / "studio" / "catalog.json").read_text(encoding="utf-8"))["characters"]}
    except (OSError, KeyError, ValueError):
        cat = {}
    cast = []
    for c in s["cast"].values():
        look = {"kind": c["look_kind"], "id": c["look"]}
        if c["look_kind"] == "preset":
            p = presets.load("blocky_cast", c["look"])
            look.update(label=p.get("label"), skin=p.get("skin"), hair=p.get("hair_colour"), shirt=p.get("shirt_colour"),
                        shirt2=p.get("shirt_colour2"), pants=p.get("pants_colour"))
        else:
            look.update(label=c["look"].replace("_", " ").title(), notes=(cat.get(c["look"]) or {}).get("notes", ""),
                        face=(cat.get(c["look"]) or {}).get("default_face") or "neutral")
        cast.append({k: c[k] for k in ("id", "name", "role", "voice", "speed", "voice_fx", "status", "colour",
                                       "personality", "speech", "catchphrase", "powers", "intro")}
                    | {"look": look, "voice_url": f"/api/series/{s['id']}/cast/{c['id']}/voice.wav"})
    m = s["meta"]
    return {"id": s["id"], "title": s["title"], "logline": m.get("logline", ""), "genre": m.get("genre", ""),
            "tone": m.get("tone", ""), "rating": m.get("rating", ""), "world": m.get("world", ""),
            "season_question": m.get("season_question", ""), "colour": m.get("colour", ""),
            "narrator": dict(s["narrator"], voice_url=f"/api/series/{s['id']}/cast/narrator/voice.wav"),
            "arc": arc, "cast": cast, "sets": list(s["sets"].values()), "episodes": eps,
            "problems": [{"file": f, "line": ln, "msg": msg} for f, ln, msg in s["problems"]],
            "folder": f"series/{s['id']}/"}


def voice_preview(series_id, cast_id):
    """A spoken sample of one character (their intro or catchphrase) with their voice, speed and effect."""
    s = bible.load(series_id)
    if cast_id == "narrator":
        n = s["narrator"]
        text = (s["meta"].get("logline") or f"Previously on {s['title']}.")[:220]
        vid, speed, fx = n["voice"], n["speed"], n["fx"]
    else:
        c = next((c for c in s["cast"].values() if c["id"] == cast_id), None)
        if not c:
            raise bible.SeriesError(f"{cast_id} isn't in the cast of {series_id}")
        text = (c["intro"] or c["catchphrase"] or f"My name is {c['name'].title()}.")[:220]
        vid, speed, fx = c["voice"], c["speed"], c["voice_fx"]
    d = PREVIEWS / s["id"]
    (d / "cache").mkdir(parents=True, exist_ok=True)
    key = h(vid, speed, fx, text, "v1")
    out = d / f"{re.sub(r'[^a-z0-9_-]', '', cast_id)}_{key}.wav"
    if out.exists() and out.stat().st_size:
        return out
    wav, _dur, _w = voice.synth(text, vid, float(speed), d)
    res = voicefx.apply(wav, fx, d) if fx and fx != "none" else wav
    out.write_bytes(res.read_bytes())
    return out


__all__ = ["list_all", "detail", "voice_preview", "PipelineError"]
