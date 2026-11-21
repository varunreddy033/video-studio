"""
render_server.py  -  Video Studio: the web app for the pipeline (local, or online through a tunnel)

  login -> paste script.md -> Check -> Make draft (fast) -> Make final (1080p + AI images + thumbnails) -> download

All video work happens in pipeline/ (see pipeline/jobs.py and pipeline/assemble.py).
Every page and API call needs a login (pipeline/auth.py). The first account is made at /setup with the
one-time code printed when the server starts.
Run:  bin/python render_server.py   (from the project folder)
"""

import json
import re
import secrets
import shutil
import threading
from datetime import timedelta
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, redirect, request, send_file, session
from werkzeug.middleware.proxy_fix import ProxyFix

from pipeline import auth, captions, encoder, jobs, presets, script_parser, visuals, voice
from pipeline import config as C
from pipeline.util import audio_duration, h as short_hash, is_starter, library_group, music_files, sfx_files

app = Flask(__name__)
# The tunnel (Tailscale Funnel / cloudflared) runs on this Mac and adds X-Forwarded-* headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SECRET_KEY=auth.secret_key(),
    SESSION_COOKIE_NAME="vs_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,          # scripts are text; nothing big is ever uploaded
)
MEDIA_PREVIEW = ("/preview.mp4", "/preview.wav", "/audio")
FILE_RE = re.compile(r"(draft|final|short)\.mp4|thumb_[1-3]\.jpg|(short_)?metadata\.txt|script\.md|"
                     r"captions_(draft|final)\.(ass|srt)|upload_pack\.zip")
SB_FRAME_RE = re.compile(r"/api/jobs/[0-9a-f-]+/storyboard/frame/[0-9a-f-]+")
UI_FONTS = ("PlusJakartaSans-wght.ttf",)    # the app's own type (OFL, ui/fonts/OFL.txt), also on the login page
OPEN = {"/login", "/setup", "/api/login", "/api/setup", "/favicon.ico", "/ui/studio.css"} | {f"/ui/fonts/{f}" for f in UI_FONTS}


# ------------------------------------------------------------------ security ---
def _user():
    name = session.get("user")
    return name if name and auth.exists(name) else None


@app.before_request
def guard():
    # secure cookie whenever the visitor came in over https (the tunnel)
    app.config["SESSION_COOKIE_SECURE"] = request.scheme == "https"
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # CSRF: only the Video Studio page sends this header; browsers block it cross-site without CORS
        if request.headers.get("X-VS") != "1":
            abort(403)
        origin = request.headers.get("Origin")
        if origin and urlparse(origin).netloc != request.host:
            abort(403)
    if request.path in OPEN:
        return None
    if C.RENDER_TOKEN and secrets.compare_digest(request.headers.get("X-Render-Token", ""), C.RENDER_TOKEN):
        return None   # scripts on this Mac (curl) can use the token from .env
    if _user():
        return None
    if request.path.startswith("/api/") or request.path == "/health":
        return jsonify({"error": "not logged in"}), 401
    return redirect("/setup" if not auth.has_users() else "/login")


@app.after_request
def headers(resp):
    frame = SB_FRAME_RE.fullmatch(request.path) is not None     # a storyboard scene, shown in an <iframe> of this page
    resp.headers["X-Frame-Options"] = "SAMEORIGIN" if frame else "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                               "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
                                               "media-src 'self' blob:; font-src 'self' data:; "
                                               "frame-ancestors " + ("'self'" if frame else "'none'") + "; form-action 'self'")
    if request.scheme == "https":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    if request.path.endswith(MEDIA_PREVIEW) and resp.status_code in (200, 206, 304):
        resp.headers["Cache-Control"] = "private, max-age=3600"     # preview clips / sounds: the ?v= changes with them
    elif request.path.startswith("/api/") or request.path in ("/login", "/setup", "/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


def _admin():
    if not auth.is_admin(_user() or ""):
        abort(403)


# --------------------------------------------------------------------- login ---
@app.get("/login")
def login_page():
    if not auth.has_users():
        return redirect("/setup")
    return send_file(C.BASE_DIR / "ui" / "login.html")


@app.get("/setup")
def setup_page():
    if auth.has_users():
        return redirect("/login")
    return send_file(C.BASE_DIR / "ui" / "login.html")


@app.post("/api/login")
def api_login():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("username") or "").strip().lower()
    wait = auth.locked_for(request.remote_addr or "?", name)
    if wait:
        return jsonify({"error": f"too many wrong tries; wait {int(wait // 60) + 1} min"}), 429
    if not auth.verify(request.remote_addr or "?", name, body.get("password") or ""):
        return jsonify({"error": "wrong username or password"}), 401
    session.clear()
    session["user"] = name
    session.permanent = True
    return jsonify({"ok": True})


@app.post("/api/setup")
def api_setup():
    if auth.has_users():
        return jsonify({"error": "setup is already done; log in instead"}), 409
    body = request.get_json(force=True, silent=True) or {}
    wait = auth.locked_for(request.remote_addr or "?", "setup")
    if wait:
        return jsonify({"error": f"too many wrong tries; wait {int(wait // 60) + 1} min"}), 429
    if not auth.use_setup_code((body.get("code") or "").strip()):
        auth.verify(request.remote_addr or "?", "setup", "")   # counts as a failed try
        return jsonify({"error": "wrong setup code (it's in output/server.log on the Mac)"}), 401
    name = (body.get("username") or "").strip().lower()
    try:
        auth.create(name, body.get("password") or "", admin=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    auth.finish_setup()
    session.clear()
    session["user"] = name
    session.permanent = True
    return jsonify({"ok": True})


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def api_me():
    name = _user()
    return jsonify({"user": name, "admin": auth.is_admin(name or "")})


@app.post("/api/password")
def api_password():
    body = request.get_json(force=True) or {}
    name = _user()
    if not name or not auth.verify(request.remote_addr or "?", name, body.get("current") or ""):
        return jsonify({"error": "current password is wrong"}), 401
    try:
        auth.set_password(name, body.get("new") or "")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.get("/api/users")
def api_users():
    _admin()
    return jsonify(auth.users())


@app.post("/api/users")
def api_add_user():
    _admin()
    body = request.get_json(force=True) or {}
    try:
        auth.create((body.get("username") or "").strip().lower(), body.get("password") or "", admin=False)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.delete("/api/users/<name>")
def api_delete_user(name):
    _admin()
    if name == _user():
        return jsonify({"error": "you can't delete yourself"}), 400
    try:
        auth.delete(name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


# --------------------------------------------------------------------- pages ---
@app.get("/")
def page():
    return send_file(C.BASE_DIR / "ui" / "index.html")


@app.get("/ui/storyboard.js")
def storyboard_js():
    resp = send_file(C.BASE_DIR / "ui" / "storyboard.js", mimetype="text/javascript")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/ui/studio.css")
def studio_css():
    resp = send_file(C.BASE_DIR / "ui" / "studio.css", mimetype="text/css")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.get("/ui/fonts/<name>")
def ui_font(name):
    if name not in UI_FONTS:
        abort(404)
    resp = send_file(C.BASE_DIR / "ui" / "fonts" / name, mimetype="font/ttf", conditional=True)
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


_SAMPLES = {k["sample"][kind] for k in C.SCRIPT_KITS.values() for kind in k["sample"]}


@app.get("/docs/<name>")
def docs(name):
    name = {"sample": "sample_script.md", "sample_motion": "sample_motion_gfx_script.md"}.get(name, name)
    if name not in {"SCRIPT_FORMAT.md", "CLAUDE_SCRIPT_PROMPT.md", "sample_motion_script.md"} | _SAMPLES:
        abort(404)
    return send_file(C.BASE_DIR / "docs" / name, mimetype="text/plain; charset=utf-8")


@app.get("/api/script_kit/<method>")
def script_kit(method):
    """The New video screen's prompt + sample for one picture style: ?kind=short|full (default full)."""
    if method not in C.SCRIPT_KITS:
        abort(404)
    kind = "short" if request.args.get("kind") == "short" else "full"
    kit = C.script_kit(method, kind)
    return jsonify({"method": method, "label": C.RENDERING_METHODS[method], "kind": kind,
                    "prompts": [dict(p, url=f"/docs/prompt/{p['id']}") for p in kit["prompts"]],
                    "sample_url": f"/docs/{kit['sample']}"})


@app.get("/docs/prompt/<pid>")
def script_prompt(pid):
    """A script-writing prompt to paste into a Claude chat (docs/script_prompts/<id>.md)."""
    ids = {i for k in C.SCRIPT_KITS.values() for ps in k["prompts"].values() for i, _ in ps}
    if pid not in ids:
        abort(404)
    return send_file(C.SCRIPT_PROMPTS_DIR / f"{pid}.md", mimetype="text/plain; charset=utf-8")


@app.get("/health")
def health():
    return jsonify({
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "encoder": encoder.name(),
        "local_image_model": C.IMAGE_MODEL_AVAILABLE,
        "seconds_per_image": C.SECONDS_PER_IMAGE,
        "default_rendering_method": C.DEFAULT_RENDERING_METHOD,
        "voice": C.KOKORO_VOICE,
        "music_tracks": len(music_files(60)),
        "sfx_files": len(sfx_files()),
        "queue_busy": any(j.get("status") == "rendering" for j in jobs.list_jobs()),
    })


# ---------------------------------------------------------------------- jobs ---
def _body() -> dict:
    """The request's JSON object ({} for anything else: a list, a number, no body)."""
    b = request.get_json(force=True, silent=True)
    return b if isinstance(b, dict) else {}


def _text() -> str:
    t = _body().get("text", "")
    return t if isinstance(t, str) else ""


@app.post("/api/check")
def check():
    text = _text()
    return jsonify(jobs.check_summary(script_parser.parse(text)))


_icon_lock = threading.Lock()      # the icon search model is loaded once; one report at a time


@app.post("/api/motion/icons")
def motion_icons():
    """Motion graphics: the icons the render would pick (topic pool + one per scene) and the repetition report.
    Uses the parser's estimated timings, so a few scene cuts differ from the real render."""
    from pipeline.motion_gfx import picker
    from pipeline.util import PipelineError
    parsed = script_parser.parse(_text())
    if parsed["meta"].get("rendering_method") != "motion":
        return jsonify({"error": "icons are only picked for rendering_method: motion"}), 400
    if parsed["errors"]:
        return jsonify({"error": "fix the script's errors first"}), 400
    try:
        with _icon_lock:
            return jsonify(picker.check_report(parsed))
    except PipelineError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/icons/<set_id>/<name>.svg")
def icon_svg(set_id, name):
    from pipeline import icon_library
    from pipeline.util import PipelineError
    if set_id not in icon_library.PACKS or not re.fullmatch(r"[a-z0-9-]+", name):
        abort(404)
    try:
        body = icon_library.svg(f"{set_id}:{name}")
    except PipelineError:
        abort(404)
    resp = app.response_class(body, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


_preview_lock = threading.Lock()   # one art style preview at a time
_caption_lock = threading.Lock()


def _audio_key(p):
    return short_hash("audio", p.resolve())


def _track_value(p):
    """What goes into the script's music: line for this file (its name words)."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9']+", " ", p.stem)).strip().lower()


@app.get("/api/music")
def music_library():
    """Music tracks (1 minute or longer) grouped by mood folder; 'other' = the old local folder / no mood."""
    groups = {}
    for p in music_files(60):
        groups.setdefault(library_group(p) or "other", []).append(
            {"label": p.stem, "value": _track_value(p), "seconds": round(audio_duration(p)),
             "url": f"/api/audio/{_audio_key(p)}/audio"})
    moods = sorted(d.name for d in C.MUSIC_LIB.iterdir() if d.is_dir()) if C.MUSIC_LIB.exists() else []
    return jsonify({"moods": [{"id": m, "tracks": groups.get(m, [])} for m in moods if m in groups or m != "other"]
                    + ([{"id": "other", "tracks": groups["other"]}] if "other" in groups else []),
                    "count": sum(len(v) for v in groups.values())})


@app.get("/api/sfx")
def sfx_library():
    """Sound-effect kinds (folders of assets/library/sfx) with their files; 'other' = the old local folder."""
    groups = {}
    for p in sfx_files():
        groups.setdefault(library_group(p) or "other", []).append(
            {"label": p.stem, "starter": is_starter(p), "url": f"/api/audio/{_audio_key(p)}/audio"})
    return jsonify([{"kind": k, "files": v, "starter_only": all(f["starter"] for f in v)}
                    for k, v in sorted(groups.items(), key=lambda kv: (kv[0] == "other", kv[0]))])


@app.get("/api/audio/<key>/audio")
def library_audio(key):
    """Plays one music / sound-effect file of the library (only files the two lists above contain)."""
    for p in music_files(0) + sfx_files():
        if _audio_key(p) == key:
            return send_file(p, conditional=True)
    abort(404)


GRADES = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F+", "F"]


@app.get("/api/voices")
def voices():
    """Voice presets (presets/voices): default first, then best grade first. preview_url plays a sample."""
    out = presets.list("voices")
    rank = lambda v: (v["id"] != presets.DEFAULTS["voices"],
                      GRADES.index(v["grade"]) if v.get("grade") in GRADES else len(GRADES), v["label"])
    for v in out:
        p = presets.load("voices", v["id"])
        v["preview_url"] = f"/api/voices/{v['id']}/preview.wav?v={voice.preview_path(p).stem[-12:]}"
    return jsonify(sorted(out, key=rank))


@app.get("/api/voices/<vid>/preview.wav")
def voice_preview(vid):
    if vid not in presets.ids("voices"):
        abort(404)
    try:
        f = voice.preview(presets.load("voices", vid))     # first time: a few seconds (Kokoro speaks one sentence)
    except Exception as e:
        return jsonify({"error": f"voice sample failed: {e}"}), 500
    return send_file(f, mimetype="audio/wav", conditional=True)


@app.get("/api/captions")
def caption_styles():
    """Caption styles (presets/captions) with the address of each one's preview clip."""
    out = []
    for c in presets.list("captions"):
        try:
            c["preview_url"] = f"/api/captions/{c['id']}/preview.mp4?v={captions.preview_path(c['id']).stem[-10:]}"
        except presets.PresetError:
            continue
        out.append(c)
    return jsonify(out)


@app.get("/api/captions/<cid>/preview.mp4")
def caption_preview(cid):
    if cid not in presets.ids("captions"):
        abort(404)
    try:
        with _caption_lock:
            f = captions.make_preview(cid)      # made once per style (about a second), then served from disk
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return send_file(f, mimetype="video/mp4", conditional=True)


@app.get("/api/formats")
def formats_list():
    """Motion-graphics formats (styles) for the Style tab: id, label, description, preview picture."""
    from pipeline.motion_gfx import formats as Fm
    return jsonify([{"id": k, "label": v["label"], "description": v["description"],
                     "preview_url": f"/api/formats/{k}/preview.jpg"} for k, v in Fm.FORMATS.items()])


@app.get("/api/camera")
def camera_options():
    """The Camera tab: camera moves and transition sets (descriptions for the tiles)."""
    from pipeline.motion_gfx import camera as Cam, planner as PL, transitions as Tr
    import re as _re
    doc = Cam.__doc__ + Tr.__doc__
    def about(name):
        m = _re.search(rf"^\s+{name}\s{{2,}}(.+)$", doc, _re.M)
        return m.group(1).strip() if m else ""
    return jsonify({"moves": [{"id": m, "description": about(m)} for m in Cam.MOVES],
                    "transition_sets": [{"id": k, "items": v} for k, v in PL.TRANSITION_SETS.items()],
                    "transitions": [{"id": t, "description": about(t)} for t in Tr.NEW]})


@app.get("/api/formats/<fid>/preview.jpg")
def format_preview(fid):
    from pipeline.motion_gfx import formats as Fm
    p = C.ASSETS / "format_previews" / f"{fid}.jpg"
    if fid not in Fm.FORMATS or not p.exists():
        abort(404)
    resp = send_file(p, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


@app.get("/api/typography")
def typography_list():
    """Motion-graphics type styles for the Typography tab: a live sample of each (the render's own CSS) + fonts."""
    try:
        return jsonify(_typography())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409


_typo_cache = None


def _typography() -> dict:
    """The type-style samples, built once. typography.preview() sets the renderer's global style while it draws a
    sample, so it must never run next to a render: built at start-up (before the render worker exists), or later
    only while no render holds jobs.RENDER_LOCK."""
    global _typo_cache
    if _typo_cache is None:
        from pipeline.motion_gfx import typography as TY
        if not jobs.RENDER_LOCK.acquire(blocking=False):
            raise RuntimeError("a video is rendering; the type samples load when it has finished")
        try:
            _typo_cache = {"styles": [TY.preview(k) for k in TY.STYLES],
                           "fonts": [{"family": fam, "url": f"/api/fonts/{f}"} for fam, f in TY.font_files().items()]}
        finally:
            jobs.RENDER_LOCK.release()
    return _typo_cache


@app.get("/api/fonts/<name>")
def font_file(name):
    from pipeline.motion_gfx import typography as TY
    if name not in set(TY.font_files().values()) or not (C.FONTS_DIR / name).exists():
        abort(404)
    resp = send_file(C.FONTS_DIR / name, mimetype="font/ttf")
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


@app.get("/api/art_styles")
def art_styles():
    return jsonify(presets.list("art_styles"))


@app.post("/api/art_styles/<sid>/preview")
def make_style_preview(sid):
    if sid not in presets.ids("art_styles"):
        return jsonify({"error": f"no art style '{sid}'"}), 404
    if presets.preview_path(sid).exists():          # made before: never regenerate
        return jsonify({"id": sid, "made": False, "preview_url": _preview_url(sid)})
    if not C.IMAGE_MODEL_AVAILABLE:
        return jsonify({"error": "Previews need the local image model (mflux), which only runs on an Apple "
                                 "Silicon Mac. Make them in Video Studio on the Mac."}), 400
    if any(j.get("status") in ("queued", "rendering") for j in jobs.list_jobs()):
        return jsonify({"error": "a video is rendering; make previews when it has finished"}), 409
    if not _preview_lock.acquire(blocking=False):
        return jsonify({"error": "another preview is being made; wait for it to finish"}), 409
    try:
        visuals.make_style_preview(sid)
    except Exception as e:
        return jsonify({"error": f"preview failed: {e}"}), 500
    finally:
        _preview_lock.release()
    return jsonify({"id": sid, "made": True, "preview_url": _preview_url(sid)})


def _preview_url(sid):
    return next((s["preview_url"] for s in presets.list("art_styles") if s["id"] == sid), None)


@app.get("/api/art_styles/<sid>/preview.jpg")
def style_preview_file(sid):
    if sid not in presets.ids("art_styles") or not presets.preview_path(sid).exists():
        abort(404)
    return send_file(presets.preview_path(sid), mimetype="image/jpeg", max_age=0)


@app.get("/api/presets")
def list_presets():
    """{kind: [{id, label}]} for every preset folder (presets/<kind>/*.json)."""
    return jsonify({kind: presets.list(kind) for kind in presets.KINDS})


PREVIEW_DIR = C.BASE_DIR / "output" / "previews"
PREVIEW_RE = re.compile(r"[0-9a-f]{16}")


@app.post("/api/preview")
def preview():
    """Motion scripts: one still per scene for the Check page (estimated timings, placeholder pictures, no image
    model). Cached per script text. Refused while a render is running (FLUX and Remotion never run together)."""
    import hashlib
    import json as _json
    text = _text()
    parsed = script_parser.parse(text)
    if parsed["meta"].get("style") != "motion":
        return jsonify({"error": "scene previews are for style: motion scripts"}), 400
    if not parsed["ok"]:
        return jsonify({"error": "fix the errors first, then show the previews"}), 400
    key = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    d = PREVIEW_DIR / key
    idx = d / "index.json"
    if idx.exists():
        return jsonify({"key": key, "scenes": _json.loads(idx.read_text(encoding="utf-8"))})
    if not jobs.RENDER_LOCK.acquire(blocking=False):
        return jsonify({"error": "a video is rendering right now; scene previews wait until it finishes"}), 409
    try:
        from pipeline import motion
        scenes = motion.preview(parsed, d)
    except Exception as e:      # noqa: BLE001  (show the reason on the page)
        return jsonify({"error": f"preview failed: {e}"}), 500
    finally:
        jobs.RENDER_LOCK.release()
    idx.write_text(_json.dumps(scenes), encoding="utf-8")
    return jsonify({"key": key, "scenes": scenes})


@app.get("/api/preview/<key>/<name>")
def preview_file(key, name):
    if not PREVIEW_RE.fullmatch(key) or not re.fullmatch(r"scene_\d{2}\.jpg", name):
        abort(404)
    p = PREVIEW_DIR / key / name
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="image/jpeg", max_age=3600)


# ---------------------------------------------------------------- web series (pipeline/series) ---
@app.get("/api/series")
def series_list():
    from pipeline.series import api as SA
    return jsonify(SA.list_all())


@app.post("/api/series")
def series_create():
    from pipeline.series import bible as SB
    body = request.get_json(silent=True) or {}
    try:
        sid = SB.create(str(body.get("title") or ""), str(body.get("logline") or ""))
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"id": sid})


@app.get("/api/series/<sid>")
def series_detail(sid):
    from pipeline.series import api as SA, bible as SB
    try:
        return jsonify(SA.detail(sid))
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 404


@app.get("/api/series/<sid>/new_episode")
def series_new_episode(sid):
    from pipeline.series import bible as SB
    try:
        name, text = SB.episode_template(SB.load(sid))
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify({"file": name, "text": text})


@app.get("/api/series/<sid>/episodes/<name>")
def series_episode(sid, name):
    from pipeline.series import bible as SB
    try:
        s = SB.load(sid)
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 404
    p = s["dir"] / "episodes" / name
    if not SB.EP_RE.match(name) or not p.is_file():
        abort(404)
    return jsonify({"file": name, "text": p.read_text(encoding="utf-8")})


@app.put("/api/series/<sid>/episodes/<name>")
def series_episode_save(sid, name):
    from pipeline.series import bible as SB
    body = request.get_json(silent=True) or {}
    try:
        SB.save_episode(sid, name, str(body.get("text") or ""))
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True, "path": f"series/{sid}/episodes/{name}"})


@app.get("/api/series/<sid>/cast/<cid>/voice.wav")
def series_voice(sid, cid):
    from pipeline.series import api as SA, bible as SB
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", cid):
        abort(404)
    try:
        f = SA.voice_preview(sid, cid)
    except SB.SeriesError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"voice sample failed: {e}"}), 500
    return send_file(f, mimetype="audio/wav", conditional=True)


@app.get("/api/series/face/<name>.png")
def series_face(name):
    """A studio character's face texture (the cast grid's portraits)."""
    from pipeline.blocky3d import sets as SETS
    if not re.fullmatch(r"[a-z_]{2,40}", name):
        abort(404)
    p = SETS.BASE / "studio" / "textures" / "faces" / f"face_{name}.png"
    if not p.is_file():
        abort(404)
    return send_file(p, mimetype="image/png", conditional=True)


@app.get("/api/jobs")
def list_jobs():
    keep = ("id", "title", "status", "stage", "done", "total", "mode", "created", "updated", "est_seconds", "format",
            "type", "rendering_method")
    out = []
    for j in jobs.list_jobs():
        row = {k: j.get(k) for k in keep}
        row["duration"] = (j.get("final") or j.get("draft") or {}).get("duration_sec")
        row["has_draft"], row["has_final"] = bool(j.get("draft")), bool(j.get("final"))
        out.append(row)
    return jsonify(out)


@app.post("/api/jobs")
def create_job():
    body = _body()
    text = _text()
    if not text.strip():
        return jsonify({"error": "paste a script first"}), 400
    job_id = jobs.create(text)
    jobs.set_state(job_id, owner=_user() or "token")
    if body.get("render"):
        try:
            jobs.enqueue(job_id, body["render"] if body["render"] in ("draft", "final") else "draft")
        except ValueError as e:
            return jsonify({"id": job_id, "error": str(e)}), 400
    return jsonify({"id": job_id})


@app.get("/api/finished")
def finished():
    """Finished full videos that a Short can be clipped from."""
    out = []
    for j in jobs.list_jobs():
        d = jobs.jdir(j["id"])
        if (j.get("type") or "full") != "full" or j.get("format") == "vertical" or not j.get("final"):
            continue
        if not ((d / "final.mp4").exists() and (d / "timeline_final.json").exists() and (d / "script.md").exists()):
            continue
        out.append({"id": j["id"], "title": j.get("title"), "duration": j["final"].get("duration_sec"),
                    "created": j.get("created"), "chapters": j["final"].get("chapters") or []})
    return jsonify(out)


def _ts(sec: float) -> str:
    sec = max(0.0, float(sec))
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


@app.post("/api/clips")
def make_clip():
    """'Make Short' -> 'from a video I already made': a clip Short from a finished job, rendered straight to final."""
    body = request.get_json(force=True) or {}
    src = body.get("source", "")
    if not jobs.valid(src):
        return jsonify({"error": "pick a finished video"}), 400
    try:
        a, b = float(body.get("start")), float(body.get("end"))
    except (TypeError, ValueError):
        return jsonify({"error": "start and end must be times in seconds"}), 400
    title = re.sub(r"[\r\n]+", " ", (body.get("title") or "").strip())[:100]
    text = "---\n" + (f"title: {title}\n" if title else "") + \
           f"type: short\nclip_from: {src}\nclip_start: {_ts(a)}\nclip_end: {_ts(b)}\n---\n"
    summ = jobs.check_summary(script_parser.parse(text))
    if not summ["ok"]:
        return jsonify({"error": "; ".join(e["msg"] for e in summ["errors"])}), 400
    job_id = jobs.create(text)
    jobs.set_state(job_id, owner=_user() or "token")
    try:
        jobs.enqueue(job_id, "final")
    except ValueError as e:
        return jsonify({"id": job_id, "error": str(e)}), 400
    return jsonify({"id": job_id})


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    if not jobs.valid(job_id):
        abort(404)
    st = jobs.read_state(job_id)
    d = jobs.jdir(job_id)
    st["script"] = (d / "script.md").read_text(encoding="utf-8") if (d / "script.md").exists() else ""
    st["files"] = sorted(p.name for p in d.iterdir() if p.is_file() and FILE_RE.fullmatch(p.name))
    st["metadata"] = (d / "metadata.txt").read_text(encoding="utf-8") if (d / "metadata.txt").exists() else ""
    st["log_tail"] = (d / "render.log").read_text(encoding="utf-8").splitlines()[-10:] if (d / "render.log").exists() else []
    return jsonify(st)


@app.put("/api/jobs/<job_id>/script")
def save_script(job_id):
    if not jobs.valid(job_id):
        abort(404)
    if jobs.read_state(job_id).get("status") in ("queued", "rendering"):
        return jsonify({"error": "wait until the render finishes before editing"}), 409
    text = _text()
    if not text.strip():
        return jsonify({"error": "the script is empty"}), 400
    return jsonify(jobs.save_script(job_id, text))


@app.delete("/api/jobs/<job_id>")
def delete_job(job_id):
    """Moves the video's folder to the Trash (Finder can put it back). Not while it is queued or rendering."""
    try:
        where = jobs.delete(job_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    print(f"job {job_id} moved to {where}", flush=True)
    return jsonify({"ok": True, "moved_to": where})


@app.post("/api/jobs/delete")
def delete_jobs():
    """Several at once: {"ids": [...]} -> {deleted: [...], skipped: [{id, reason}]}."""
    ids = (request.get_json(force=True, silent=True) or {}).get("ids") or []
    deleted, skipped = [], []
    for jid in ids[:500]:
        try:
            jobs.delete(str(jid))
            deleted.append(jid)
        except ValueError as e:
            skipped.append({"id": jid, "reason": str(e)})
    if deleted:
        print(f"{len(deleted)} job(s) moved to {jobs.trash_dir()}: {', '.join(deleted)}", flush=True)
    return jsonify({"deleted": deleted, "skipped": skipped})


@app.post("/api/jobs/<job_id>/render")
def render(job_id):
    if not jobs.valid(job_id):
        abort(404)
    mode = (request.get_json(force=True, silent=True) or {}).get("mode", "draft")
    if mode not in ("draft", "final"):
        return jsonify({"error": "mode must be draft or final"}), 400
    try:
        jobs.enqueue(job_id, mode)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    return jsonify({"ok": True})


# ------------------------------------------------------------------ storyboard ---
def _sb_job(job_id):
    if not jobs.valid(job_id) or not (jobs.jdir(job_id) / "script.md").exists():
        abort(404)
    return jobs.jdir(job_id)


def _sb_busy(job_id):
    return jobs.read_state(job_id).get("status") in ("queued", "rendering")


@app.get("/api/themes")
def themes_list():
    """Storyboard themes for the Theme tab (presets/storyboard_themes)."""
    return jsonify(presets.list("storyboard_themes"))


@app.get("/api/jobs/<job_id>/storyboard")
def storyboard_get(job_id):
    from pipeline.motion_gfx import storyboard as SB, planner as PL
    d = _sb_job(job_id)
    st = jobs.read_state(job_id)
    return jsonify({"scenes": SB.scenes(d), "state": SB.load_state(d)["scenes"], "fonts": SB.fonts(),
                    "types": sorted(PL.TYPES), "size": list(SB._size(d)), "built": (st.get("storyboard") or {}).get("built"),
                    "theme": (st.get("check") or {}).get("theme"), "busy": _sb_busy(job_id),
                    "options": SB.options(d), "posters": {} if _sb_busy(job_id) else SB.poster_names(d)})


@app.post("/api/jobs/<job_id>/storyboard")
def storyboard_build(job_id):
    """Queue a storyboard build: voice + scenes, no video render."""
    _sb_job(job_id)
    try:
        jobs.enqueue(job_id, "storyboard")
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    return jsonify({"ok": True})


@app.get("/api/jobs/<job_id>/storyboard/frame/<sid>")
def storyboard_frame(job_id, sid):
    from pipeline.motion_gfx import storyboard as SB
    d = _sb_job(job_id)
    v = request.args.get("v")
    try:
        html = SB.frame_page(d, job_id, sid, int(v) if v and v.isdigit() else None, request.args.get("raw") == "1")
    except (KeyError, OSError):
        abort(404)
    return Response(html, mimetype="text/html")


@app.get("/api/jobs/<job_id>/motion/assets/<path:name>")
def storyboard_asset(job_id, name):
    """Fonts and scripts of the job's HyperFrames project (the scene pages load them)."""
    d = _sb_job(job_id) / "motion" / "assets"
    p = (d / name).resolve()
    if not re.fullmatch(r"(js|fonts)/[A-Za-z0-9_.-]+", name) or d.resolve() not in p.parents or not p.is_file():
        abort(404)
    resp = send_file(p, conditional=True)
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp


@app.put("/api/jobs/<job_id>/storyboard/scene/<sid>")
def storyboard_edit(job_id, sid):
    """Save a scene's manual edits (positions, sizes, text, colours...)."""
    from pipeline.motion_gfx import storyboard as SB
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes before editing scenes"}), 409
    try:
        st = SB.save_edits(d, sid, request.get_json(force=True) or {})
    except KeyError:
        abort(404)
    presets_job = d / "job.json"
    if presets_job.exists():                               # keep job.json's "storyboard" block current
        spec = json.loads(presets_job.read_text(encoding="utf-8"))
        spec["storyboard"] = SB.summary(d)
        presets_job.write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True, "scene": st})


@app.put("/api/jobs/<job_id>/storyboard/scene/<sid>/options")
def storyboard_options(job_id, sid):
    """A scene's own choices (transition in, camera, entrance, text entrance, palette, layout, sounds), then the
    scenes are built again right away (voice and plan are cached: a few seconds; untouched scenes stay the same)."""
    from pipeline.motion_gfx import storyboard as SB
    from pipeline.util import PipelineError
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes before changing scenes"}), 409
    try:
        SB.save_opts(d, sid, request.get_json(force=True) or {})
        jobs.storyboard_regenerate(job_id, None)            # regen None = rebuild the scenes only
    except KeyError:
        abort(404)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PipelineError as e:
        return jsonify({"error": str(e)}), 409
    return storyboard_get(job_id)


@app.post("/api/jobs/<job_id>/storyboard/posters")
def storyboard_posters(job_id):
    """Makes the scene posters that are missing or out of date ({"sids": [...]} = only those); returns all names."""
    from pipeline.motion_gfx import storyboard as SB
    from pipeline.util import PipelineError
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "the scenes are being rebuilt"}), 409
    sids = (request.get_json(force=True, silent=True) or {}).get("sids")
    try:
        return jsonify(SB.make_posters(d, set(map(str, sids)) if isinstance(sids, list) else None))
    except PipelineError as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/jobs/<job_id>/storyboard/poster/<name>")
def storyboard_poster(job_id, name):
    d = _sb_job(job_id) / "storyboard" / "posters"
    if not re.fullmatch(r"[0-9a-f]+-\d+-[0-9a-f]{12}\.jpg", name) or not (d / name).is_file():
        abort(404)
    resp = send_file(d / name, mimetype="image/jpeg", conditional=True)
    resp.headers["Cache-Control"] = "private, max-age=31536000, immutable"   # the name changes with the scene
    return resp


@app.post("/api/jobs/<job_id>/storyboard/scene/<sid>/regenerate")
def storyboard_regen(job_id, sid):
    """Make another version of ONE scene; it waits for accept / reject. Other scenes are not touched."""
    from pipeline.util import PipelineError
    _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes"}), 409
    body = request.get_json(force=True) or {}
    regen = {"sid": sid, "what": body.get("what") if body.get("what") in ("scene", "layout", "icon") else "scene",
             "type": str(body.get("type") or "")[:40], "query": str(body.get("query") or "")[:120]}
    try:
        jobs.storyboard_regenerate(job_id, regen)
    except (ValueError, PipelineError) as e:
        return jsonify({"error": str(e)}), 409
    return storyboard_get(job_id)


@app.post("/api/jobs/<job_id>/storyboard/scene/<sid>/version")
def storyboard_version(job_id, sid):
    """accept / reject the waiting version, or restore an earlier one ({"action": ..., "n": 2})."""
    from pipeline.motion_gfx import storyboard as SB
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes"}), 409
    body = request.get_json(force=True) or {}
    try:
        SB.decide(d, sid, body.get("action"), body.get("n"))
    except KeyError:
        abort(404)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return storyboard_get(job_id)


# --------------------------------------------- shot storyboard (ai_image, blocky3d, explainer3d, neon) ---
@app.get("/api/jobs/<job_id>/shots")
def shots_get(job_id):
    from pipeline import shot_storyboard as SS
    d = _sb_job(job_id)
    return jsonify(dict(SS.shots(d), busy=_sb_busy(job_id)))


def _shot_script(job_id, text):
    """Saves a script the shot storyboard made (same path as the Script editor) and returns the new shot list."""
    jobs.save_script(job_id, text)
    return shots_get(job_id)


@app.put("/api/jobs/<job_id>/shots/<int:i>")
def shots_save(job_id, i):
    """Replace one shot's lines of script.md ({"text": new lines, "old": the lines as loaded})."""
    from pipeline import shot_storyboard as SS
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes before editing shots"}), 409
    body = request.get_json(force=True) or {}
    try:
        return _shot_script(job_id, SS.save(d, i, str(body.get("text") or ""), str(body.get("old") or "")))
    except (KeyError, IndexError):
        abort(404)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/jobs/<job_id>/shots/<int:i>/new_image")
def shots_new_image(job_id, i):
    """Another version of an [ai:]/[stock:] shot's picture, made now (~25 s); it waits for accept / reject."""
    from pipeline import shot_storyboard as SS
    from pipeline.util import PipelineError
    d = _sb_job(job_id)
    if _sb_busy(job_id) or not jobs.RENDER_LOCK.acquire(blocking=False):
        return jsonify({"error": "a video is rendering; make the new picture when it has finished"}), 409
    try:
        SS.new_image(d, i)
    except IndexError:
        abort(404)
    except (ValueError, PipelineError) as e:
        return jsonify({"error": str(e)}), 400
    finally:
        jobs.RENDER_LOCK.release()
    return shots_get(job_id)


@app.post("/api/jobs/<job_id>/shots/<int:i>/version")
def shots_version(job_id, i):
    """{"action": "accept" | "reject" | "use", "seed": N}: writes | seed=N into the shot's tag (accept / use)."""
    from pipeline import shot_storyboard as SS
    d = _sb_job(job_id)
    if _sb_busy(job_id):
        return jsonify({"error": "wait until the render finishes"}), 409
    body = request.get_json(force=True) or {}
    if body.get("action") not in ("accept", "reject", "use"):
        return jsonify({"error": "action must be accept, reject or use"}), 400
    try:
        text = SS.decide(d, i, body["action"], body.get("seed"))
    except IndexError:
        abort(404)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return _shot_script(job_id, text) if text else shots_get(job_id)


@app.get("/api/jobs/<job_id>/shots/<int:i>/picture")
def shots_picture(job_id, i):
    from pipeline import shot_storyboard as SS
    from pipeline.util import PipelineError
    d = _sb_job(job_id)
    seed = request.args.get("seed")
    try:
        p = SS.picture(d, i, int(seed) if seed and seed.isdigit() else None)
    except IndexError:
        abort(404)
    except PipelineError:
        p = None
    if not p:
        abort(404)
    resp = send_file(p, conditional=True)
    resp.headers["Cache-Control"] = "private, max-age=60"
    return resp


_thumbs_lock = threading.Lock()     # designed thumbnails: one Chromium batch at a time


@app.post("/api/thumbs")
def thumbs_preview():
    """Check page: the designed thumbnails of a motion-graphics script (3 options, or a Short's cover + 2), cached by
    the brief. Takes a few seconds the first time (headless Chromium), instantly after that."""
    from pipeline.thumbs import render as TR
    parsed = script_parser.parse(_text())
    if parsed["meta"].get("rendering_method") != "motion" or parsed["meta"].get("clip"):
        return jsonify({"error": "designed thumbnails are for motion-graphics videos and Shorts"}), 400
    if parsed["errors"]:
        return jsonify({"error": "fix the script's errors first"}), 400
    try:
        with _thumbs_lock:
            rep = TR.preview(parsed)
    except Exception as e:  # noqa: BLE001  (ThumbsFailed or a missing Chromium: say why on the card)
        return jsonify({"error": str(e)}), 400
    for o in rep["options"]:
        o["url"] = f"/api/thumbs/{rep['key']}/{o['file']}"
    return jsonify(rep)


@app.get("/api/thumbs/<key>/<name>")
def thumbs_file(key, name):
    from pipeline.thumbs import render as TR
    if not re.fullmatch(r"[0-9a-f]{16}", key) or not re.fullmatch(r"thumb_[1-3]\.jpg", name):
        abort(404)
    p = TR.PREVIEWS / key / name
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="image/jpeg", max_age=86400)


@app.post("/api/jobs/<job_id>/thumbnails")
def remake_thumbnails(job_id):
    if not jobs.valid(job_id):
        abort(404)
    try:
        with _thumbs_lock:
            rep = jobs.remake_thumbnails(job_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True, "options": rep["options"], "failed": rep["failed"], "seconds": rep["seconds"]})


@app.get("/api/jobs/<job_id>/file/<name>")
def get_file(job_id, name):
    if not jobs.valid(job_id) or not FILE_RE.fullmatch(name):
        abort(404)
    p = jobs.jdir(job_id) / name
    if not p.exists():
        abort(404)
    title = re.sub(r"[^A-Za-z0-9]+", "-", jobs.read_state(job_id).get("title") or job_id).strip("-")[:60]
    return send_file(p, conditional=True, as_attachment=request.args.get("download") == "1",
                     download_name=f"{title}-{name}")


if __name__ == "__main__":
    # transformers is imported lazily by the voice (Kokoro: AlbertModel) and by the icon search (Check page) in
    # different threads; two threads importing it at once leave one with a half-built module (ImportError
    # AlbertModel). Import it once here, before any thread runs.
    try:
        import transformers
        transformers.AlbertModel, transformers.AutoModel, transformers.AutoTokenizer  # noqa: B018 (load lazily-defined names)
    except Exception as e:  # noqa: BLE001
        print(f"transformers pre-import failed: {e}", flush=True)
    try:
        _typography()                      # before the render worker starts (see _typography)
    except Exception as e:  # noqa: BLE001
        print(f"typography samples not built yet: {e}", flush=True)
    jobs.start_worker()
    print(f"Video Studio: open http://localhost:{C.PORT}", flush=True)
    code = auth.setup_code()
    if code:
        print(f"FIRST RUN: create your login at http://localhost:{C.PORT}/setup?code={code}", flush=True)
    app.run(host=C.HOST, port=C.PORT, threaded=True)
