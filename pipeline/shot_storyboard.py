"""Storyboard for every rendering method that isn't motion graphics (ai_image, blocky3d, explainer3d, neon).

A shot = one visual tag of script.md with the narration under it. The script stays the one source of truth: an edit
rewrites that shot's lines of script.md and is only kept when the script still passes Check. A draft / final then
re-renders as usual (ai_image reuses every cached image, so only changed shots cost time).

  shots(job_dir)            the shot list: tag lines, narration, timing (last render or estimate), picture
  save(job_dir, i, ...)     replace shot i's lines (refused when the script changed meanwhile or gets errors)
  new_image(job_dir, i)     [ai:]/[stock:] only: another version of the picture (| seed=N), made now, waits for
                            accept; versions are kept in storyboard/shots.json and stay cached
  decide(job_dir, i, ...)   accept / reject the waiting version, or use an earlier one
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import config as C, script_parser, visuals
from .util import PipelineError

TAG_RE = re.compile(r"\[(ai|stock):([^\]]*)\]")
AI_HELP = """Tags of AI-image videos (docs/SCRIPT_FORMAT.md):
    [ai: prompt | seed=N]          an AI image (seed=N = another version of the same prompt)
    [stock: words | seed=N]        an AI documentary photo
    [card: TEXT | small line]      a text card
    [number: 70 | label | prefix=$ suffix=B decimals=1]
    [quote: "words" | who said it]
    [chart: bar|line | title | A: 1, B: 2]
    [talk: pose | set | camera]  [act: description | wide/medium/close]   (character videos)
    [sfx: word]                    a sound effect where it stands
The narration under a tag is spoken while that shot is on screen."""


def _help(method: str) -> str:
    if method == "ai_image":
        return AI_HELP
    from importlib import import_module
    return (import_module(f"pipeline.{method}.script").__doc__ or "").strip()


def _parse(job_dir: Path):
    text = (job_dir / "script.md").read_text(encoding="utf-8")
    return text, script_parser.parse(text)


def _blocks(parsed) -> list:
    """(first line, last line) of each shot: its tag line down to the last narration line spoken under it."""
    out = []
    for i, sh in enumerate(parsed["shots"]):
        ends = [s.get("line_end", s["line"]) for s in parsed["segments"] if s.get("shot") == i]
        out.append((sh["line"], max([sh["line"]] + ends)))
    return out


def _timing(job_dir: Path) -> list:
    for mode in ("final", "draft"):
        p = job_dir / f"timeline_{mode}.json"
        if p.exists():
            return [dict(s, video=mode) for s in json.loads(p.read_text(encoding="utf-8")).get("shots", [])]
    return []


def _state(job_dir: Path) -> dict:
    p = job_dir / "storyboard" / "shots.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_state(job_dir: Path, st: dict) -> None:
    p = job_dir / "storyboard" / "shots.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(st, indent=1), encoding="utf-8")


def _image(job_dir: Path, parsed, sh, seed=None) -> Path:
    """Cache path of an [ai:]/[stock:] shot's final-size picture (seed None = the shot's own)."""
    W, H = C.SIZES[(parsed["meta"]["format"], "final")]
    prompt, stock, extra = visuals.shot_image(dict(sh, seed=sh.get("seed") if seed is None else seed))
    return visuals.ai_cache_path(prompt, W, H, job_dir, extra, style=parsed["meta"]["presets"]["art_style"], stock=stock)[0]


def _key(sh) -> str:
    """Identifies a shot's content (versions belong to a prompt, not to a position in the script)."""
    return hashlib.sha1(json.dumps([sh["type"], sh.get("prompt") or sh.get("query")]).encode()).hexdigest()[:12]


def shots(job_dir) -> dict:
    job_dir = Path(job_dir)
    text, parsed = _parse(job_dir)
    lines = text.split("\n")
    timing, st = _timing(job_dir), _state(job_dir)
    method = parsed["meta"].get("rendering_method", "ai_image")
    out = []
    for i, (sh, (a, b)) in enumerate(zip(parsed["shots"], _blocks(parsed))):
        t = timing[i] if i < len(timing) and timing[i].get("type") == sh["type"] else None
        row = {"i": i, "type": sh["type"], "line": a, "line_end": b, "text": "\n".join(lines[a - 1:b]),
               "narration": " ".join(s["text"] for s in parsed["segments"] if s.get("shot") == i),
               "start": t["start"] if t else sh.get("est_start", 0), "dur": t["dur"] if t else sh.get("est_dur", 0),
               "timed": bool(t), "fields": {k: v for k, v in sh.items()
                                            if k not in ("line", "first_segment", "est_start", "est_dur", "placeholder")}}
        if sh["type"] in ("ai", "stock"):
            v = st.get(_key(sh), {})
            row["seed"] = sh.get("seed", 0)
            row["versions"] = [{"seed": s, "ready": _image(job_dir, parsed, sh, s).exists()}
                               for s in sorted(set(v.get("seeds", []) + [row["seed"]]))]
            row["pending"] = v.get("pending")
        out.append(row)
    return {"method": method, "label": C.RENDERING_METHODS.get(method, method), "ok": parsed["ok"],
            "errors": parsed["errors"], "help": _help(method), "shots": out,
            "size": list(C.SIZES[(parsed["meta"]["format"], "final")]), "clip": bool(parsed["meta"].get("clip"))}


def save(job_dir, i: int, new_text: str, old_text: str) -> str:
    """The script with shot i's lines replaced; ValueError (with Check's messages) when it can't be saved."""
    job_dir = Path(job_dir)
    text, parsed = _parse(job_dir)
    if i >= len(parsed["shots"]):
        raise KeyError(i)
    a, b = _blocks(parsed)[i]
    lines = text.split("\n")
    if "\n".join(lines[a - 1:b]) != old_text:
        raise ValueError("the script changed since this page was loaded; reload the storyboard")
    out = "\n".join(lines[:a - 1] + new_text.strip("\n").split("\n") + lines[b:])
    p2 = script_parser.parse(out)
    if not p2["ok"]:
        raise ValueError("; ".join(f"line {e['line']}: {e['msg']}" for e in p2["errors"][:4]))
    return out


def _with_seed(text: str, parsed, i: int, seed: int) -> str:
    """The script with shot i's [ai:]/[stock:] tag carrying | seed=N (0 = the option removed)."""
    sh = parsed["shots"][i]
    lines = text.split("\n")
    line = lines[sh["line"] - 1]
    m = next((m for m in TAG_RE.finditer(line) if m.group(1) == sh["type"]), None)
    # shortcut: takes the first tag of this kind on the line; two [ai:] tags on one line would need a column index
    if not m:
        raise ValueError("couldn't find the shot's tag in the script")
    parts = [p.strip() for p in m.group(2).split("|") if not re.fullmatch(r"\s*seed\s*=\s*\d+\s*", p)]
    tag = f"[{sh['type']}: {' | '.join(parts + ([f'seed={seed}'] if seed else []))}]"
    lines[sh["line"] - 1] = line[:m.start()] + tag + line[m.end():]
    return "\n".join(lines)


def new_image(job_dir, i: int) -> None:
    """Makes the next version of shot i's picture now (the caller holds jobs.RENDER_LOCK)."""
    job_dir = Path(job_dir)
    _, parsed = _parse(job_dir)
    sh = parsed["shots"][i]
    if sh["type"] not in ("ai", "stock"):
        raise ValueError("only AI-image shots ([ai:] / [stock:]) have picture versions")
    st = _state(job_dir)
    v = st.setdefault(_key(sh), {"seeds": []})
    seed = max(v["seeds"] + [sh.get("seed", 0)]) + 1
    W, H = C.SIZES[(parsed["meta"]["format"], "final")]
    prompt, stock, extra = visuals.shot_image(dict(sh, seed=seed))
    try:
        visuals.ai_image(prompt, W, H, job_dir, extra, style=parsed["meta"]["presets"]["art_style"], stock=stock)
    finally:
        visuals.stop_image_worker()
    v["seeds"] = sorted(set(v["seeds"] + [sh.get("seed", 0), seed]))
    v["pending"] = seed
    _save_state(job_dir, st)


def decide(job_dir, i: int, action: str, seed=None):
    """accept / reject the waiting version, or use (an earlier) version {seed}. Returns the new script or None."""
    job_dir = Path(job_dir)
    text, parsed = _parse(job_dir)
    sh = parsed["shots"][i]
    st = _state(job_dir)
    v = st.get(_key(sh), {"seeds": []})
    if action == "reject":
        v["pending"] = None
        _save_state(job_dir, st)
        return None
    seed = v.get("pending") if action == "accept" else int(seed)
    if seed is None or (seed and seed not in v["seeds"]):
        raise ValueError("no such version")
    out = _with_seed(text, parsed, i, seed)
    v["pending"] = None
    st[_key(sh)] = v
    _save_state(job_dir, st)
    return out


def picture(job_dir, i: int, seed=None) -> Path:
    """A picture of shot i: its cached AI image (any version), else a frame of the last final/draft at the shot's
    middle (made once, cached), else None."""
    job_dir = Path(job_dir)
    _, parsed = _parse(job_dir)
    sh = parsed["shots"][i]
    if sh["type"] in ("ai", "stock"):
        p = _image(job_dir, parsed, sh, seed)
        if p.exists():
            return p
    t = next((x for x in _timing(job_dir)[i:i + 1] if x.get("type") == sh["type"]), None)
    if not t:
        return None
    video = job_dir / f"{t['video']}.mp4"
    if not video.exists():
        return None
    at = t["start"] + t["dur"] / 2
    key = hashlib.sha1(f"{video.stat().st_mtime_ns}:{at:.2f}".encode()).hexdigest()[:12]
    out = job_dir / "storyboard" / "frames" / f"{key}.jpg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=640:-2", "-q:v", "4", str(out)], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        if r.returncode or not out.exists():
            raise PipelineError(f"couldn't grab a frame: {r.stderr.strip()[-200:]}")
    return out
