"""The storyboard of a motion-graphics job: output/jobs/<id>/storyboard/ (docs/STORYBOARD_PLAN.md).

  scenes.json            one row per scene, written by every build (what the Storyboard page lists)
  plan.json              the history snapshot the scenes were planned with; reused once the storyboard is in use, so
                         scenes nobody touched come out the same on every later build
  state.json             what the user did: per scene the current version, a pending regeneration, manual edits
  versions/<sid>/vN.json a pinned scene version (its built parts: css / html / js / sound cues, palette, type, layout)
  versions/<sid>/vN.html the same version as a finished scene composition (the page shows it without a build)

Scene id = hash of the scene's spoken words (+ a counter for repeats): it follows the scene when the script changes
around it. Element id = the element's own id without the scene prefix, plus child indexes ("kin", "p0/2").

Manual edits never change the generated HTML: they are an extra CSS block (+ a few lines of JS for text / pictures)
appended to the scene, so the GSAP timeline, ids and HyperFrames attributes stay as generated. Positions are stored
as fractions of the frame. An edit is only applied to the scene layout it was made on (type : layout : frame);
otherwise it is kept, reported as stale and not applied."""

import hashlib
import json
import re
import threading
import time
from pathlib import Path

LOCK = threading.RLock()
PATH_RE = re.compile(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*(?:/\d{1,3}){0,10}")
COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{6}")
ICON_RE = re.compile(r"[a-z0-9_]+:[a-z0-9_-]+")
MARK = ("/*sb-edits*/", "/*sb-end*/")
BLOCK_RE = re.compile(re.escape(MARK[0]) + r".*?" + re.escape(MARK[1]) + r"\n?", re.S)


def root(job_dir) -> Path:
    return Path(job_dir) / "storyboard"


def _read(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def load_state(job_dir) -> dict:
    return _read(root(job_dir) / "state.json", {"scenes": {}})


def save_state(job_dir, state) -> None:
    _write(root(job_dir) / "state.json", state)


def scenes(job_dir) -> list:
    return _read(root(job_dir) / "scenes.json", [])


def scene_ids(beats) -> list:
    seen, out = {}, []
    for b in beats:
        key = hashlib.sha1(re.sub(r"\W+", " ", b["text"].lower()).strip().encode()).hexdigest()[:10]
        seen[key] = seen.get(key, 0) + 1
        out.append(f"{key}-{seen[key]}")
    return out


def rehost(text: str, old: str, new: str) -> str:
    return text if old == new else re.sub(rf"\b{old}\b", new, text)


def sig_of(template, variant, frame) -> str:
    return f"{template}:{variant}:{frame or '-'}"


def fonts() -> list:
    from . import design as D, formats  # noqa: F401  (formats + typography register their fonts)
    return sorted({fam for fam, _f, _w in D.FONTS.values()})


# ------------------------------------------------------------------------------------------------------- edits
def clean_edits(raw) -> dict:
    """What the page sent -> only known fields with safe values (they are written into CSS / JS)."""
    num = lambda v, lo, hi: max(lo, min(hi, float(v)))  # noqa: E731
    out = {"els": {}}
    if isinstance(raw.get("bg"), str) and COLOUR_RE.fullmatch(raw["bg"]):
        out["bg"] = raw["bg"]
    allowed = set(fonts())
    for path, e in list((raw.get("els") or {}).items())[:200]:
        if not PATH_RE.fullmatch(str(path)) or not isinstance(e, dict):
            continue
        c = {}
        try:
            if "x" in e or "y" in e:
                c["mode"] = "abs" if e.get("mode") == "abs" else "rel"
                c["x"], c["y"] = round(num(e.get("x", 0), -3, 3), 5), round(num(e.get("y", 0), -3, 3), 5)
                c["base"] = [round(num(v, -20000, 20000), 2) for v in (list(e.get("base") or []) + [0, 0, 0, 0])[:4]]
            if "zoom" in e:
                c["zoom"] = round(num(e["zoom"], 0.05, 12), 4)
            if "fs" in e:
                c["fs"] = round(num(e["fs"], 0.004, 1.5), 5)
            if "z" in e:
                c["z"] = int(num(e["z"], -1000000, 1000000))
        except (TypeError, ValueError):
            continue
        if isinstance(e.get("color"), str) and COLOUR_RE.fullmatch(e["color"]):
            c["color"] = e["color"]
        if e.get("font") in allowed:
            c["font"] = e["font"]
        if e.get("align") in ("left", "center", "right"):
            c["align"] = e["align"]
        if e.get("hidden") is True:
            c["hidden"] = True
        if isinstance(e.get("text"), str):
            c["text"] = e["text"][:600]
        if isinstance(e.get("icon"), str) and ICON_RE.fullmatch(e["icon"]):
            c["icon"] = e["icon"]
        if c:
            out["els"][path] = c
    return out


def selector(hid: str, path: str) -> str:
    head, *idx = path.split("/")
    return f"#{hid}-{head}" + "".join(f" > :nth-child({int(k) + 1})" for k in idx)


def edit_blocks(hid: str, edit: dict, W: int, H: int) -> tuple:
    """(css, js) of a scene's manual edits, between markers. Empty strings when there is nothing to apply."""
    css, js = [], []
    if edit.get("bg"):
        css.append(f"#{hid}-stage {{ background: {edit['bg']} !important; }}")
    for path, e in (edit.get("els") or {}).items():
        sel, d = selector(hid, path), []
        if "x" in e:
            dx, dy, b = e["x"] * W, e["y"] * H, e["base"]
            if e["mode"] == "abs":
                d += [f"margin-left: {b[0] + dx:.2f}px", f"margin-top: {b[1] + dy:.2f}px",
                      f"margin-right: {b[2] - dx:.2f}px", f"margin-bottom: {b[3] - dy:.2f}px"]
            else:
                d += ["position: relative", f"left: {b[0] + dx:.2f}px", f"top: {b[1] + dy:.2f}px"]
        if "zoom" in e:
            d.append(f"zoom: {e['zoom']}")
        if "fs" in e:
            d.append(f"font-size: {e['fs'] * H:.2f}px")
        if "color" in e:
            d += [f"color: {e['color']}", f"-webkit-text-fill-color: {e['color']}"]
        if "font" in e:
            d.append(f'font-family: "{e["font"]}"')
        if "align" in e:
            d.append(f"text-align: {e['align']}")
        if "z" in e:
            d.append(f"z-index: {e['z']}")
        if e.get("hidden"):
            d.append("display: none")
        if d:
            css.append(f"{sel} {{ " + "; ".join(x + " !important" for x in d) + "; }")
        if "text" in e:
            js.append(f"(function () {{ var e = document.querySelector({json.dumps(sel)}); "
                      f"if (e) e.textContent = {json.dumps(e['text']).replace('<', chr(92) + 'u003c')}; }})();")
        if "icon" in e:
            from . import picker
            js.append(f"(function () {{ var e = document.querySelector({json.dumps(sel)}); "
                      f"if (e) e.setAttribute('src', {json.dumps(picker.data_uri(e['icon']))}); }})();")
    wrap = lambda lines: f"{MARK[0]}\n" + "\n".join(lines) + f"\n{MARK[1]}\n" if lines else ""  # noqa: E731
    return wrap(css), wrap(js)


def with_edits(parts: dict, hid: str, edit: dict, W: int, H: int) -> dict:
    css, js = edit_blocks(hid, edit, W, H)
    return dict(parts, css=parts["css"] + "\n" + css.rstrip("\n"), js=js + parts["js"]) if css or js else parts


def strip_edits(html: str) -> str:
    return BLOCK_RE.sub("", html)


def patch_html(html: str, hid: str, edit: dict, W: int, H: int) -> str:
    """A finished scene composition with its edit blocks replaced (the page saved an edit: no build needed)."""
    html = strip_edits(html)
    css, js = edit_blocks(hid, edit or {}, W, H)
    if css:
        html = html.replace("</style>", css + "</style>", 1)
    if js:
        html = html.replace("(function (tl) {\n", "(function (tl) {\n" + js, 1)
    return html


# ------------------------------------------------------------------------------------------------- during a build
class Board:
    """One build's view of the storyboard (render.py makes one per build)."""

    def __init__(self, job_dir, W, H, log=lambda m: None):
        self.dir, self.W, self.H, self.log = root(job_dir), W, H, log
        self.state = load_state(job_dir)
        self.job_dir = Path(job_dir)
        self.rows, self.gen, self.stale = [], {}, []

    def seen(self, fresh: dict, freeze: bool) -> dict:
        """The history snapshot to plan with: the stored one once the storyboard is in use, else today's (stored)."""
        plan = _read(self.dir / "plan.json", None)
        if plan and (plan.get("frozen") or self.state["scenes"]):
            return plan["seen"]
        _write(self.dir / "plan.json", {"seen": fresh, "frozen": bool(freeze), "written": time.strftime("%Y-%m-%d %H:%M")})
        return fresh

    def plan(self, key_parts, compute, freeze: bool):
        """(names, variants, info, icon plan) of the video. Planned once and stored; later builds of the same scenes
        and look reuse it, so a scene nobody touched is the same scene in every build (the planner's answer can
        differ between runs)."""
        key = hashlib.sha1(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()[:16]
        f = self.dir / "plan.json"
        p = _read(f, None) or {}
        if p.get("key") == key and p.get("plan") and (p.get("frozen") or self.state["scenes"]):
            names, variants, info, pl = p["plan"]
            return names, variants, info, dict(pl, picks={(bi, slot): pk for bi, slot, pk in pl["picks"]})
        names, variants, info, pl = compute()
        try:
            enc = json.loads(json.dumps([names, variants, info, dict(pl, picks=[[bi, slot, pk] for (bi, slot), pk in
                                                                                  pl["picks"].items()])], default=list))
            _write(f, dict(p, key=key, plan=enc, frozen=bool(freeze or p.get("frozen"))))
        except (TypeError, ValueError) as e:
            self.log(f"  storyboard: the plan could not be stored ({e}); scenes are planned again on every build")
        return names, variants, info, pl

    def version(self, sid, n):
        return _read(self.dir / "versions" / sid / f"v{n}.json", None)

    def resolve(self, i, sid, hid, beat, gen):
        """The scene to render: the user's current version (else the generated one) + its manual edits."""
        self.gen[i] = gen
        st = self.state["scenes"].get(sid) or {}
        cur = int(st.get("current") or 0)
        use = gen
        v = self.version(sid, cur) if st else None
        if v:
            use = dict(v, parts={k: (rehost(x, v["hid"], hid) if isinstance(x, str) else x) for k, x in v["parts"].items()})
            use["parts"]["cues"] = [tuple(c) for c in v["parts"].get("cues") or []]
            beat["frame"] = v.get("frame")
        sig = sig_of(use["template"], use["variant"], beat.get("frame"))
        edit = (st.get("edits") or {}).get(str(cur))
        applied = stale = False
        parts = use["parts"]
        if edit and (edit.get("els") or edit.get("bg")):
            if edit.get("sig") in (None, sig):
                parts, applied = with_edits(parts, hid, edit, self.W, self.H), True
            else:
                stale = True
                self.stale.append(i + 1)
        self.rows.append({"sid": sid, "n": i + 1, "hid": hid, "text": beat["text"], "start": round(beat["start"], 3),
                          "dur": round(beat["dur"], 3), "ov": beat.get("ov", 0.0), "template": use["template"],
                          "variant": use["variant"], "frame": beat.get("frame"), "sig": sig, "shot": beat["shot"],
                          "kind": beat.get("kind"), "icons": use.get("icons") or [], "current": cur,
                          "pending": st.get("pending"), "versions": st.get("versions") or [],
                          "edited": applied, "stale": stale, "regenerated": cur > 0})
        return parts, use["pal"], use["template"], use["variant"]

    def pin(self, i, sid, hid, n, data, html, source, note=""):
        """Stores a version (parts + composed html) and lists it in the state."""
        d = self.dir / "versions" / sid
        _write(d / f"v{n}.json", dict(data, hid=hid, n=n))
        (d / f"v{n}.html").write_text(html, encoding="utf-8")
        st = self.state["scenes"].setdefault(sid, {"current": 0, "pending": None, "versions": [], "edits": {}})
        st["versions"] = [x for x in st["versions"] if x["n"] != n] + [
            {"n": n, "source": source, "note": note, "template": data["template"], "variant": data["variant"],
             "icons": data.get("icons") or [], "created": time.strftime("%Y-%m-%d %H:%M")}]
        st["versions"].sort(key=lambda x: x["n"])
        return st

    def finish(self, chapters_at):
        for r, ch in zip(self.rows, chapters_at):
            r["chapter"] = ch
        _write(self.dir / "scenes.json", self.rows)
        if self.stale:
            self.log(f"  storyboard: manual edits of scene(s) {', '.join(map(str, self.stale))} were made on another "
                     f"layout and were NOT applied (kept; open the Storyboard to re-apply or reset them)")
        n_ed = sum(r["edited"] for r in self.rows)
        n_re = sum(r["regenerated"] for r in self.rows)
        if n_ed or n_re:
            self.log(f"  storyboard: {n_ed} scene(s) with manual edits, {n_re} on a regenerated version")


# -------------------------------------------------------------------------------------- between builds (the page)
def _row(job_dir, sid):
    return next((r for r in scenes(job_dir) if r["sid"] == sid), None)


def _scene_file(job_dir, row) -> Path:
    return Path(job_dir) / "motion" / "compositions" / f"scene_{row['n']:03d}.html"


def _size(job_dir):
    from .. import config as C
    spec = _read(Path(job_dir) / "job.json", {})
    return C.SIZES[(spec.get("format") or "landscape", "final")]


def _refresh_file(job_dir, row, st):
    """Writes the scene's composition from its current version + edits (after an edit / accept / restore)."""
    W, H = _size(job_dir)
    cur = int(st.get("current") or 0)
    vh = root(job_dir) / "versions" / row["sid"] / f"v{cur}.html"
    f = _scene_file(job_dir, row)
    if vh.exists():
        v = _read(vh.with_suffix(".json"), {})
        html = rehost(vh.read_text(encoding="utf-8"), v.get("hid", row["hid"]), row["hid"])
    else:
        html = f.read_text(encoding="utf-8")
    edit = (st.get("edits") or {}).get(str(cur)) or {}
    ok = edit.get("sig") in (None, row["sig"]) or vh.exists()
    f.write_text(patch_html(html, row["hid"], edit if ok else {}, W, H), encoding="utf-8")


def save_edits(job_dir, sid, raw) -> dict:
    """The page's edits of a scene's current version. An empty edit removes the entry."""
    with LOCK:
        row = _row(job_dir, sid)
        if not row:
            raise KeyError(sid)
        state = load_state(job_dir)
        st = state["scenes"].setdefault(sid, {"current": 0, "pending": None, "versions": [], "edits": {}})
        cur = str(int(st.get("current") or 0))
        edit = clean_edits(raw or {})
        if edit["els"] or edit.get("bg"):
            v = _read(root(job_dir) / "versions" / sid / f"v{cur}.json", None)
            edit["sig"] = sig_of(v["template"], v["variant"], v.get("frame")) if v else row["sig"]
            edit["saved"] = time.strftime("%Y-%m-%d %H:%M:%S")
            st["edits"][cur] = edit
        else:
            st["edits"].pop(cur, None)
        save_state(job_dir, state)
        _refresh_file(job_dir, row, st)
        rows = scenes(job_dir)
        for r in rows:
            if r["sid"] == sid:
                r["edited"], r["stale"] = cur in st["edits"], False
        _write(root(job_dir) / "scenes.json", rows)
        return st


def decide(job_dir, sid, action, n=None) -> dict:
    """accept / reject the pending regeneration, or restore version n."""
    with LOCK:
        row = _row(job_dir, sid)
        state = load_state(job_dir)
        st = state["scenes"].get(sid)
        if not row or not st:
            raise KeyError(sid)
        d = root(job_dir) / "versions" / sid
        if action in ("accept", "reject"):
            p = st.get("pending")
            if p is None:
                raise ValueError("nothing is waiting to be accepted")
            if action == "accept":
                st["current"] = p
            else:
                st["versions"] = [x for x in st["versions"] if x["n"] != p]
                st["edits"].pop(str(p), None)
                for ext in ("json", "html"):
                    (d / f"v{p}.{ext}").unlink(missing_ok=True)
            st["pending"] = None
        elif action == "restore":
            if not (d / f"v{int(n)}.html").exists():
                raise ValueError(f"version {n} doesn't exist")
            st["current"] = int(n)
        else:
            raise ValueError("action must be accept, reject or restore")
        save_state(job_dir, state)
        v = _read(d / f"v{st['current']}.json", None)
        rows = scenes(job_dir)
        for r in rows:
            if r["sid"] == sid:
                if v:
                    r.update(template=v["template"], variant=v["variant"], frame=v.get("frame"), icons=v.get("icons") or [],
                             sig=sig_of(v["template"], v["variant"], v.get("frame")))
                r.update(current=st["current"], pending=st["pending"], versions=st["versions"],
                         regenerated=st["current"] > 0, edited=str(st["current"]) in st["edits"], stale=False)
                row = r
        _write(root(job_dir) / "scenes.json", rows)
        _refresh_file(job_dir, row, st)
        return st


def frame_page(job_dir, job_id, sid, version=None, raw=False, base=None, width=None) -> str:
    """A scene as a page of its own (the editor canvas shows it in an <iframe>, posters are screenshots of it): the
    scene's real composition (same HTML, CSS, GSAP timeline as the render), paused; the parent page seeks it.
    base = the <base href> (default: the job's motion folder over HTTP); width = draw it scaled to that width (posters:
    the browser then paints a small picture instead of a full frame)."""
    from . import design as D, formats  # noqa: F401
    row = _row(job_dir, sid)
    if not row:
        raise KeyError(sid)
    W, H = _size(job_dir)
    hid = row["hid"]
    if version is None:
        html = _scene_file(job_dir, row).read_text(encoding="utf-8")
    else:
        d = root(job_dir) / "versions" / sid
        v = _read(d / f"v{int(version)}.json", {})
        html = rehost((d / f"v{int(version)}.html").read_text(encoding="utf-8"), v.get("hid", hid), hid)
        if not raw:
            edit = ((load_state(job_dir)["scenes"].get(sid) or {}).get("edits") or {}).get(str(int(version))) or {}
            html = patch_html(html, hid, edit, W, H)
    if raw:
        html = strip_edits(html)
    body = re.sub(r"^\s*<template>|</template>\s*$", "", html.strip())
    faces = "\n".join(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; src: url("assets/fonts/{f}"); }}'
                      for fam, f, w in D.FONTS.values())
    still = row["ov"] + min(row["dur"] * 0.75, 1.4)
    k = (width / W) if width else 1
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><base href="{base or f'/api/jobs/{job_id}/motion/'}">
<style>
{faces}
html, body {{ margin: 0; width: {round(W * k)}px; height: {round(H * k)}px; overflow: hidden; background: #111; }}
#sbhost {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; overflow: hidden;
  transform: scale({k:.5f}); transform-origin: 0 0; }}
</style>
<script src="assets/js/gsap.min.js"></script><script src="assets/js/springs.js"></script>
<script>window.__timelines = {{}}; window.SB = {{ hid: "{hid}", W: {W}, H: {H}, still: {still:.3f}, length: {row['dur'] + row['ov']:.3f} }};</script>
</head><body><div id="sbhost">
{body}
</div>
<script>
(function () {{
  var tl = window.__timelines["{hid}"];
  window.SB.tl = tl;
  window.SB.seek = function (t) {{ if (tl) tl.pause(Math.max(0, Math.min(window.SB.length, t))); }};
  window.fitAll = function () {{ window.SB.seek(window.SB.still); }};       // posters (thumbs/shoot.mjs calls it)
  var go = function () {{ window.SB.seek(window.SB.still); window.SB.ready = true;
    if (window.parent !== window) window.parent.postMessage({{ sbReady: "{sid}" }}, location.origin); }};
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(go, go);
}})();
</script></body></html>"""


def summary(job_dir) -> dict:
    """job.json "storyboard": what the user changed (ids, versions, edit counts)."""
    st = load_state(job_dir)["scenes"]
    rows = scenes(job_dir)
    return {"scenes": len(rows), "state_file": "storyboard/state.json", "scenes_file": "storyboard/scenes.json",
            "coordinates": "fractions of the frame width / height",
            "modified": [{"scene_id": sid, "scene": next((r["n"] for r in rows if r["sid"] == sid), None),
                          "current_version": s.get("current") or 0, "pending_version": s.get("pending"),
                          "versions": [v["n"] for v in s.get("versions") or []],
                          "edited_elements": sorted(((s.get("edits") or {}).get(str(s.get("current") or 0)) or {}).get("els") or {})}
                         for sid, s in st.items()]}


# ------------------------------------------------------------------------------------------- per-scene options
# Choices the planner makes per scene, set by hand on the Storyboard page. Stored in state.json scenes[sid]["opts"] and
# applied by every build (render.py) before the scene is composed: transition in (the cut into this scene, so it also
# sets the previous scene's exit), camera move, entrance, text entrance, palette, layout (arrangement + frame), and
# whether the cut and the scene play their sound effects. Layout / palette / text entrance shape the generated scene
# (a regenerated version keeps its own); transition, camera, entrance and sounds apply to every version.
def option_lists() -> dict:
    from . import camera as Cam, compose, design as D, planner as PL, typography as TY
    return {"transition": list(PL.TRANSITIONS), "camera": ["flat"] + list(Cam.MOVES), "entrance": list(compose.ENTRANCES),
            "text_entrance": sorted({e for st in TY.STYLES.values() for e in st["entrances"]}),
            "palette": [p["name"] for p in D.PALETTES]}


def clean_opts(raw) -> dict:
    """Validates the page's options (trust boundary): known names only, layout = an int for the type it was set on."""
    from . import planner as PL
    if not isinstance(raw, dict):
        raise ValueError("options must be an object")
    lists, out = option_lists(), {}
    for k, allowed in lists.items():
        v = raw.get(k)
        if v in (None, ""):
            continue
        if v not in allowed:
            raise ValueError(f"{k}: {v!r} isn't one of {', '.join(allowed)}")
        out[k] = v
    if raw.get("layout") not in (None, ""):
        t = raw.get("template")
        if t not in PL.TYPES or not isinstance(raw["layout"], int) or not 0 <= raw["layout"] < PL.layouts_of(t):
            raise ValueError("layout must be a layout number of the scene's type")
        out["layout"], out["template"] = raw["layout"], t
    for k in ("cut_sfx", "scene_sfx"):
        if raw.get(k) is False:
            out[k] = False
    return out


def save_opts(job_dir, sid, raw) -> dict:
    """The page's options of one scene; they take effect at the next build (the page queues a storyboard build)."""
    opts = clean_opts(raw)
    with LOCK:
        if not _row(job_dir, sid):
            raise KeyError(sid)
        state = load_state(job_dir)
        st = state["scenes"].setdefault(sid, {"current": 0, "pending": None, "versions": [], "edits": {}})
        if opts:
            st["opts"] = opts
        else:
            st.pop("opts", None)
        save_state(job_dir, state)
        return st


def opts_of(state: dict, sid: str) -> dict:
    return ((state.get("scenes") or {}).get(sid) or {}).get("opts") or {}


def write_options(job_dir, fseed: int, palettes: list) -> None:
    """options.json for the page: the lists above + what each layout number of every type looks like."""
    from . import planner as PL
    layouts = {t: [{"n": v, "arrangement": v % PL.own_of(t) + 1, "frame": PL.frame_of(t, fseed, v)}
                   for v in range(PL.layouts_of(t))] for t in sorted(PL.TYPES)}
    _write(root(job_dir) / "options.json", dict(option_lists(), layouts=layouts, video_palettes=palettes))


def options(job_dir) -> dict:
    from . import design as D
    o = _read(root(job_dir) / "options.json", None) or dict(option_lists(), layouts={}, video_palettes=[])
    o["palette_colours"] = {p["name"]: [p["bg"], p["ink"], p["pop"]] for p in D.PALETTES}
    return o


# ----------------------------------------------------------------------------------------------------- posters
# The scene grid shows a still picture per scene instead of a live page: a live 1080p scene costs the page ~0.5 s of
# painting (SVG filters, big shadows) and 30 of them froze it for ~20 s. A poster is a screenshot of frame_page at
# the scene's still moment, keyed by a hash of that page, so it is made again only when the scene changes.
POSTER_W = {"landscape": 560, "vertical": 300}
POSTER_LOCK = threading.Lock()


def _poster_key(job_dir, sid) -> str:
    return hashlib.sha1(frame_page(job_dir, "-", sid).encode()).hexdigest()[:12]


def poster_names(job_dir) -> dict:
    """{sid: poster file name if it is up to date, else None}."""
    d = root(job_dir) / "posters"
    out = {}
    for r in scenes(job_dir):
        try:
            name = f"{r['sid']}-{_poster_key(job_dir, r['sid'])}.jpg"
        except (KeyError, OSError):
            out[r["sid"]] = None
            continue
        out[r["sid"]] = name if (d / name).exists() else None
    return out


def make_posters(job_dir, sids=None) -> dict:
    """Screenshots the scenes whose poster is missing or out of date (one headless browser for all of them)."""
    from PIL import Image
    from ..thumbs import render as TR
    W, H = _size(job_dir)
    w = POSTER_W["vertical" if H > W else "landscape"]
    d = root(job_dir) / "posters"
    d.mkdir(parents=True, exist_ok=True)
    base = (Path(job_dir) / "motion").resolve().as_uri() + "/"
    with POSTER_LOCK:
        have = poster_names(job_dir)
        todo = [s for s, name in have.items() if not name and (sids is None or s in sids)]
        pages = []
        for sid in todo:
            html = d / f"_{sid}.html"
            html.write_text(frame_page(job_dir, "-", sid, base=base, width=w), encoding="utf-8")
            pages.append({"html": str(html), "png": str(d / f"_{sid}.png"), "w": w, "h": round(H * w / W), "sid": sid})
        if pages:
            try:
                shots = TR._shoot([{k: p[k] for k in ("html", "png", "w", "h")} for p in pages])
            finally:
                for p in pages:
                    Path(p["html"]).unlink(missing_ok=True)
            for p, shot in zip(pages, shots):
                png = Path(p["png"])
                if shot.get("error") or not png.exists():
                    continue
                for old in d.glob(f"{p['sid']}-*.jpg"):
                    old.unlink(missing_ok=True)
                Image.open(png).convert("RGB").save(d / f"{p['sid']}-{_poster_key(job_dir, p['sid'])}.jpg",
                                                    quality=84, optimize=True)
                png.unlink(missing_ok=True)
        (d / "shoot.json").unlink(missing_ok=True)
        return poster_names(job_dir)
