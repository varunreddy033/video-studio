"""
render_server.py  -  Video Studio: the web app for the pipeline (local, or online through a tunnel)

  login -> paste script.md -> Check -> Make draft (fast) -> Make final (1080p + AI images + thumbnails) -> download

All video work happens in pipeline/ (see pipeline/jobs.py and pipeline/assemble.py).
Every page and API call needs a login (pipeline/auth.py). The first account is made at /setup with the
one-time code printed when the server starts.
Run:  ~/youtube-pipeline/bin/python ~/youtube-pipeline/render_server.py
"""

import re
import secrets
import shutil
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, redirect, request, send_file, session
from werkzeug.middleware.proxy_fix import ProxyFix

from pipeline import auth, encoder, jobs, script_parser
from pipeline import config as C
from pipeline.util import list_audio

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
FILE_RE = re.compile(r"(draft|final|short)\.mp4|thumb_[1-3]\.jpg|(short_)?metadata\.txt|script\.md|"
                     r"captions_(draft|final)\.(ass|srt)|upload_pack\.zip")
OPEN = {"/login", "/setup", "/api/login", "/api/setup", "/favicon.ico"}


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
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                               "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
                                               "media-src 'self' blob:; frame-ancestors 'none'; form-action 'self'")
    if request.scheme == "https":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    if request.path.startswith("/api/") or request.path in ("/login", "/setup", "/"):
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


@app.get("/docs/<name>")
def docs(name):
    name = {"sample": "sample_script.md"}.get(name, name)
    if name not in ("SCRIPT_FORMAT.md", "CLAUDE_SCRIPT_PROMPT.md", "sample_script.md"):
        abort(404)
    return send_file(C.BASE_DIR / "docs" / name, mimetype="text/plain; charset=utf-8")


@app.get("/health")
def health():
    return jsonify({
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "encoder": encoder.name(),
        "local_image_model": C.IMAGE_MODEL_AVAILABLE,
        "seconds_per_image": C.SECONDS_PER_IMAGE,
        "voice": C.KOKORO_VOICE,
        "music_tracks": len(list_audio(C.BGM_DIR, 60)),
        "sfx_files": len(list_audio(C.SFX_DIR)),
        "queue_busy": any(j.get("status") == "rendering" for j in jobs.list_jobs()),
    })


# ---------------------------------------------------------------------- jobs ---
@app.post("/api/check")
def check():
    text = (request.get_json(force=True) or {}).get("text", "")
    return jsonify(jobs.check_summary(script_parser.parse(text)))


@app.get("/api/jobs")
def list_jobs():
    keep = ("id", "title", "status", "stage", "done", "total", "mode", "created", "updated", "est_seconds", "format",
            "type")
    out = []
    for j in jobs.list_jobs():
        row = {k: j.get(k) for k in keep}
        row["duration"] = (j.get("final") or j.get("draft") or {}).get("duration_sec")
        row["has_draft"], row["has_final"] = bool(j.get("draft")), bool(j.get("final"))
        out.append(row)
    return jsonify(out)


@app.post("/api/jobs")
def create_job():
    body = request.get_json(force=True) or {}
    text = body.get("text", "")
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
    text = (request.get_json(force=True) or {}).get("text", "")
    if not text.strip():
        return jsonify({"error": "the script is empty"}), 400
    return jsonify(jobs.save_script(job_id, text))


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
    jobs.start_worker()
    print(f"Video Studio: open http://localhost:{C.PORT}", flush=True)
    code = auth.setup_code()
    if code:
        print(f"FIRST RUN: create your login at http://localhost:{C.PORT}/setup?code={code}", flush=True)
    app.run(host=C.HOST, port=C.PORT, threaded=True)
