"""
jobs.py  -  one folder per video in output/jobs/<id>/ and a background queue that renders one at a time.

  state.json status:  script (saved + checked)  ->  queued  ->  rendering  ->  draft_ready / done
                      failed at any point (cache/ keeps voice, stock clips and AI images, so a retry resumes)
  files:  script.md, job.json (resolved presets, rewritten on every render), draft.mp4, final.mp4, thumb_1..3.jpg, metadata.txt, render.log, cache/
"""

import json
import queue
import re
import threading
import time
import traceback
import uuid
from pathlib import Path

from . import assemble, clip, presets, script_parser, thumbnails, visuals
from . import config as C
from .util import fmt_ts, log

_lock = threading.Lock()
# Held for a whole render, and by Check-page motion previews: the image model (FLUX) and Remotion never run at
# the same time, and only one heavy job uses the Mac at once.
RENDER_LOCK = threading.Lock()
_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
ID_RE = re.compile(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{6}")


def new_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def valid(job_id: str) -> bool:
    return bool(ID_RE.fullmatch(job_id or "")) and (C.JOBS_DIR / job_id).is_dir()


def jdir(job_id: str) -> Path:
    return C.JOBS_DIR / job_id


def read_state(job_id: str) -> dict:
    p = jdir(job_id) / "state.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:
        return {}


def set_state(job_id: str, **fields) -> dict:
    with _lock:
        d = jdir(job_id)
        d.mkdir(parents=True, exist_ok=True)
        st = read_state(job_id)
        st.update(fields, id=job_id, updated=time.time())
        st.setdefault("created", st["updated"])
        tmp = d / "state.json.tmp"
        tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
        tmp.replace(d / "state.json")
        return st


def ai_images_needed(parsed: dict, job_dir=None) -> dict:
    """AI images the FINAL makes in the chosen art style ([ai:]/[stock:] shots + the 2 AI thumbnails), and how
    many of them aren't in job_dir/cache yet (job_dir None = a new video: none are). [act:] images not counted."""
    meta = parsed["meta"]
    if meta.get("clip"):
        return {"total": 0, "new": 0}
    W, H = C.SIZES[(meta["format"], "final")]
    style = meta["presets"]["art_style"]
    d = Path(job_dir) if job_dir else C.JOBS_DIR / "_none_"
    paths = {visuals.ai_cache_path(s["query"] if s["type"] == "stock" else s["prompt"], W, H, d, style=style,
                                   stock=s["type"] == "stock")[0]
             for s in parsed["shots"] if s["type"] in ("ai", "stock")}
    if meta["type"] == "full" and not meta.get("character_data"):
        tp = thumbnails.thumb_prompt(parsed)
        paths |= {visuals.ai_cache_path(tp, thumbnails.TW, thumbnails.TH, d, f"thumb{i}", style=style)[0]
                  for i in (1, 2)}
    return {"total": len(paths), "new": sum(1 for p in paths if not (p.exists() and p.stat().st_size > 0))}


def check_summary(parsed: dict, job_dir=None) -> dict:
    """What the page shows after Check (no huge lists)."""
    out = _summary(parsed)
    try:
        if parsed["meta"].get("rendering_method") == "motion":
            raise presets.PresetError("motion graphics use no art style")
        st = presets.load("art_styles", parsed["meta"]["presets"]["art_style"])
        out["art_style"] = {"id": st["id"], "label": st["label"], "realistic": st["realistic"],
                            "images": ai_images_needed(parsed, job_dir)}
    except presets.PresetError:
        out["art_style"] = None
    try:
        cp = presets.load("captions", parsed["meta"]["presets"]["captions"])
        out["captions"] = {"id": cp["id"], "label": cp["label"], "enabled": cp.get("enabled", True)}
    except presets.PresetError:
        out["captions"] = None
    vid = parsed["meta"].get("voice")
    vp = next((v for v in presets.list("voices") if v.get("voice") == vid), None)
    out["voice"] = {"voice": vid, "preset": vp and vp["id"], "label": vp["label"] if vp else vid,
                    "speed": parsed["meta"].get("speed")}
    return out


def _summary(parsed: dict) -> dict:
    return {"ok": parsed["ok"], "errors": parsed["errors"], "warnings": parsed["warnings"],
            "stats": parsed["stats"], "meta": {k: v for k, v in parsed["meta"].items()},
            "chapters": [{"title": c["title"], "est_start": c["est_start"]} for c in parsed["chapters"]],
            "shots": [{k: v for k, v in s.items() if k in ("type", "line", "query", "prompt", "text", "sub", "by",
                                                         "value", "prefix", "suffix", "label", "title", "chart",
                                                         "data", "est_start", "est_dur")}
                      | {"narration": " ".join(seg["text"] for seg in parsed["segments"] if seg["shot"] == i)[:220]}
                      for i, s in enumerate(parsed["shots"])]}


def save_script(job_id: str, text: str) -> dict:
    jdir(job_id).mkdir(parents=True, exist_ok=True)
    (jdir(job_id) / "script.md").write_text(text, encoding="utf-8")
    parsed = script_parser.parse(text)
    summ = check_summary(parsed, jdir(job_id))
    st = read_state(job_id)
    fields = {"check": summ, "title": parsed["meta"].get("title") or "Untitled",
              "est_seconds": parsed["stats"]["est_seconds"], "format": parsed["meta"]["format"],
              "type": parsed["meta"]["type"], "clip": parsed["meta"].get("clip"),
              "rendering_method": parsed["meta"].get("rendering_method", "ai_image")}
    if st.get("status") not in ("queued", "rendering"):
        fields["status"] = st.get("status") if st.get("status") in ("draft_ready", "done") else "script"
    set_state(job_id, **fields)
    return summ


def create(text: str) -> str:
    job_id = new_id()
    save_script(job_id, text)
    return job_id


def enqueue(job_id: str, mode: str) -> str:
    st = read_state(job_id)
    if st.get("status") in ("queued", "rendering"):
        raise ValueError(f"already {st['status']}")
    if not (st.get("check") or {}).get("ok"):
        raise ValueError("the script has errors; fix them and press Check again")
    ahead = _queue.qsize() + sum(1 for j in list_jobs() if j.get("status") == "rendering")
    set_state(job_id, status="queued", mode=mode, stage=f"waiting ({ahead} ahead)" if ahead else "starting",
              done=0, total=0, error=None)
    _queue.put((job_id, mode))
    return job_id


def list_jobs():
    out = []
    for p in C.JOBS_DIR.glob("*/state.json"):
        st = read_state(p.parent.name)
        if st:
            out.append(st)
    out.sort(key=lambda j: j.get("created", 0), reverse=True)
    return out


def _metadata(parsed, result, thumbs) -> str:
    meta = parsed["meta"]
    P = C.TYPES[meta.get("type", "full")]
    desc = (meta.get("description") or "").strip()
    tags = meta.get("tags") or []
    if result.get("clip"):
        c = result["clip"]
        desc = desc or c.get("source_description", "")
        desc = (desc + "\n" if desc else "") + f"From the full video: {c['source_title']}"
        tags = tags or c.get("source_tags", [])
    if P["shorts_tag"] and "#shorts" not in desc.lower():
        desc = (desc + "\n" if desc else "") + "#Shorts"
    parts = [f"TITLE\n{meta.get('title', '')}\n", "DESCRIPTION", desc, ""]
    ch = result.get("chapters") or []
    if P["chapters"] and len(ch) >= 3:
        parts += ["Chapters"] + [f"{fmt_ts(c['start'])} {c['title']}" for c in ch] + [""]
    tracks = [m["track"] for m in result.get("music") or []] or ([result["bgm"]] if result.get("bgm") else [])
    for t in dict.fromkeys(tracks):
        track = (Path(t).stem.replace("---", "|").replace("-_-", ", ").replace("-", " ")
                 .replace("|", " - ").title())
        parts += [f"Music: {track} (YouTube Audio Library)", ""]
    disclosure = ("- Studio > Details > 'Altered or synthetic content': the pictures are animated drawings, not realistic: "
                  "answer NO (YES only if a scene makes a real person or event look real)."
                  if meta.get("rendering_method") == "motion" else
                  "- Studio > Details > 'Altered or synthetic content': answer YES (the pictures are AI-generated and realistic).")
    parts += ["TAGS", ", ".join(tags), "",
              "UPLOAD CHECKLIST",
              disclosure,
              ("- Short: upload from the YouTube app or Studio; pick thumb_1.jpg (or a frame) as the cover."
               if meta.get("type") == "short" else
               "- Thumbnails: upload thumb_1/2/3.jpg with 'Test & compare'." if thumbs else ""),
              "- Visibility: private first, watch it once on YouTube, then publish."]
    return "\n".join(p for p in parts if p is not None).strip() + "\n"


def _short_script(text: str) -> str:
    """Vertical Short = the header (format: vertical) + only the first chapter."""
    m = re.match(r"(---\n.*?\n---\n)(.*)", text, re.S)
    if not m:
        return ""
    header, body = m.group(1), m.group(2)
    header = re.sub(r"(?m)^(format|type|short):.*\n", "", header)
    header = header.replace("\n---\n", "\ntype: short\n---\n", 1)
    parts = re.split(r"(?m)^(?=## )", body)
    chapters = [p for p in parts if p.startswith("## ")]
    return header + "\n" + (chapters[0] if chapters else body)


def _upload_pack(d: Path, parsed, result, thumbs, short_info):
    import shutil
    import zipfile
    meta = parsed["meta"]
    if short_info:
        tags = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", t.title()) for t in (meta.get("tags") or [])[:3])
        (d / "short_metadata.txt").write_text(
            f"TITLE\n{meta.get('title', '')[:90]} #Shorts\n\nDESCRIPTION\n"
            f"{(meta.get('description') or '').strip().splitlines()[0] if meta.get('description') else ''}\n"
            f"Full video on the channel.\n{tags} #Shorts\n\nLENGTH\n{short_info['duration_sec']} s, 1080x1920\n", encoding="utf-8")
    files = ["final.mp4", "metadata.txt", "captions_final.srt", *thumbs]   # Shorts: thumbs = [thumb_1.jpg]
    if short_info:
        files += ["short.mp4", "short_metadata.txt"]
    zp = d / "upload_pack.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:     # videos don't compress; store = fast
        for f in files:
            if (d / f).exists():
                z.write(d / f, f)
    return zp.name


def _run(job_id: str, mode: str):
    d = jdir(job_id)
    text = (d / "script.md").read_text(encoding="utf-8")
    parsed = script_parser.parse(text)
    if not parsed["ok"]:
        raise ValueError("script has errors: " + "; ".join(e["msg"] for e in parsed["errors"][:3]))
    char = parsed["meta"].get("character_data")
    is_short = parsed["meta"]["type"] == "short"
    if char and mode == "final":
        # presenter videos need the finished pose/mouth pack; wait for it instead of failing (and don't
        # fight the pack build for the GPU)
        from . import presenter
        waited = time.time()
        while not presenter.pack_ready(char["name"]):
            set_state(job_id, status="rendering", mode=mode, done=0, total=0, error=None,
                      stage=f"waiting for {char['name'].title()}'s character pack "
                            f"({int(time.time() - waited) // 60} min so far). If it isn't building, start it in "
                            f"Terminal: bin/python tools/make_character_pack.py {char['name']}  (~2 h, plugged in). "
                            f"The final starts by itself when the pack is done.")
            time.sleep(30)
    set_state(job_id, status="rendering", mode=mode, stage="starting", done=0, total=0, error=None,
              render_started=time.time(), check=check_summary(parsed, d))
    presets.write_job(d, job_id, mode, parsed)
    log(d, "job.json: presets " + ", ".join(f"{k}={v}" for k, v in parsed["meta"]["presets"].items()))

    def progress(stage, done=0, total=0):
        set_state(job_id, stage=stage, done=done, total=total)

    gfx = parsed["meta"].get("rendering_method") == "motion"
    if parsed["meta"].get("clip"):
        result = clip.render(parsed, d, mode, progress)
    elif parsed["meta"].get("style") == "motion":
        from . import motion
        result = motion.render(parsed, d, mode, progress)
    elif gfx:
        from .motion_gfx import render as motion_render        # separate renderer; ai_image never loads it
        result = motion_render.render(parsed, d, mode, progress)
    else:
        result = assemble.render(parsed, d, mode, progress)
    thumbs = []
    if mode == "final":
        shots = json.loads((d / "timeline_final.json").read_text(encoding="utf-8"))["shots"]
        if gfx and not is_short:
            progress("thumbnails", 0, 3)
            from .motion_gfx import render as motion_render
            thumbs = motion_render.thumbnails(parsed, d, d / "final.mp4")
        elif is_short:
            progress("thumbnails", 0, 1)
            pick = next((t for t in shots if t["type"] in ("talk", "act", "ai", "stock")), shots[0] if shots else
                        {"start": 0.5, "dur": 1.0})
            thumbs = thumbnails.make_short(parsed, d, d / "final.mp4", pick["start"] + min(pick["dur"] / 2, 1.5))
        else:
            progress("thumbnails", 0, 3)
            first_visual = next((t for t in shots if t["type"] in ("ai", "stock")), {"start": 1.0, "dur": 1.0})
            thumbs = thumbnails.make(parsed, d, d / "final.mp4", first_visual["start"] + first_visual["dur"] / 2)
        (d / "metadata.txt").write_text(_metadata(parsed, result, thumbs), encoding="utf-8")
        short_info = None
        if (not is_short and parsed["meta"].get("character_data")
                and (parsed["meta"].get("short") or "yes").lower() != "no"):
            t_short = time.time()
            progress("short", 0, 1)
            sp = script_parser.parse(_short_script(text))
            if sp["ok"] and sp["segments"]:
                short_info = assemble.render(sp, d / "short", "final",
                                             lambda st, a=0, b=0: progress(f"short: {st}", a, b))
                import shutil
                shutil.copy(d / "short" / "final.mp4", d / "short.mp4")
                log(d, f"SHORT done: {short_info['duration_sec']} s vertical in {time.time() - t_short:.0f}s")
            else:
                log(d, "short skipped: " + "; ".join(e["msg"] for e in sp["errors"][:2]))
        progress("upload pack")
        pack_name = _upload_pack(d, parsed, result, thumbs, short_info)
        result["short"] = short_info and {k: short_info[k] for k in ("duration_sec", "render_seconds", "size_mb")}
        result["upload_pack"] = pack_name
    key = "draft" if mode == "draft" else "final"
    set_state(job_id, status="draft_ready" if mode == "draft" else "done", stage="finished",
              **{key: result}, thumbnails=thumbs if thumbs else read_state(job_id).get("thumbnails", []))


def _worker():
    while True:
        job_id, mode = _queue.get()
        try:
            with RENDER_LOCK:
                _run(job_id, mode)
        except Exception as e:
            log(jdir(job_id), "ERROR " + traceback.format_exc().strip().splitlines()[-1])
            set_state(job_id, status="failed", stage=f"{mode} render failed", error=f"{type(e).__name__}: {e}")
        finally:
            visuals.stop_image_worker()
            _queue.task_done()


def start_worker():
    for st in list_jobs():   # nothing is running after a restart
        if st.get("status") in ("queued", "rendering"):
            set_state(st["id"], status="failed", stage="interrupted (the server was restarted)",
                      error="The server stopped while this was rendering. Press the render button again; "
                            "finished voice and AI images are reused.")
    threading.Thread(target=_worker, daemon=True, name="render-worker").start()
