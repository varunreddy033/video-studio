"""The shared engine of the Three.js renderers (rendering_method: blocky3d, explainer3d).

  voice     assemble._timeline / _voice_track / _shot_spans (the same Kokoro voice, cache and cut points)
  project   output/jobs/<id>/<style>/: the style's index.html + world.js, three 0.170 + loaders from node_modules,
            GSAP, the style's fonts and model files
  render    `hyperframes render` at the output size -> <style>/renders/<mode>.mp4 (picture only)
  finish    the style's sound cues (motion_gfx.render.plan_sound), assemble._mix_audio (music, ducking, -14 LUFS),
            assemble.final_encode, .srt, timeline_<mode>.json (shots + beats for the frame thumbnails)

A style module provides NAME, LABEL, JS_SRC (folder with world.js), FONTS, ready() -> error text or "",
build(meta, parsed, spans, words, W, H, project, warnings) -> (data, html, shots, summary, log line) and
cues(shots) -> [(t, sound kind)]. Returns the same result dict as assemble.render.
"""

import json
import random
import shutil
import time
from pathlib import Path

from . import assemble, captions, encoder
from . import config as C
from .util import PipelineError, fmt_ts, log as _log, media_duration, sfx_files
from .motion_gfx import hf

THREE = C.BASE_DIR / "node_modules" / "three"
LOADERS = ("loaders/GLTFLoader.js", "loaders/OBJLoader.js", "loaders/MTLLoader.js", "utils/BufferGeometryUtils.js")
QUALITY = {"draft": "draft", "final": "standard"}


def render(style, parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    t_start = time.time()
    job_dir = Path(job_dir).resolve()
    meta = parsed["meta"]
    log = lambda m: _log(job_dir, m)
    tools = hf.check_installed()
    if not (THREE / "build" / "three.module.js").exists():
        raise PipelineError(f"three.js isn't installed in this project. Run once in Terminal: cd {C.BASE_DIR} && npm ci")
    why = style.ready()
    if why:
        raise PipelineError(why)
    W, H = C.SIZES[(meta["format"], mode)]
    P = C.TYPES[meta.get("type", "full")]
    work = job_dir / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    warnings = []
    title = meta.get("title", "")
    log(f"=== {mode.upper()} render ({style.LABEL}): '{title}'  {len(parsed['shots'])} shots, {W}x{H}, "
        f"HyperFrames {tools['hyperframes']}, Node {tools['node']}, encoder {encoder.name()}")

    # 1 voice + cut points
    tl, total = assemble._timeline(parsed, job_dir, progress)
    if P["max_sec"] and total > P["max_sec"]:
        raise PipelineError(f"the voice is {fmt_ts(total)} long, over the {fmt_ts(P['max_sec'])} limit for a "
                            f"{P['label']}; cut some lines")
    voice_wav = assemble._voice_track(tl, total, job_dir)
    spans = assemble._shot_spans(parsed, tl, total)
    words = [[w[0], round(s["start"] + w[1], 3), round(s["start"] + w[2], 3), w[3] if len(w) > 3 else ""]
             for s in tl for w in s["words"]]

    # 2 project
    progress("scenes", 0, 1)
    project = job_dir / style.NAME
    for sub in ("assets/js/loaders", "assets/js/utils", "assets/fonts", "renders", "logs"):
        (project / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(THREE / "build" / "three.module.js", project / "assets/js/three.module.js")
    for f in LOADERS:
        shutil.copy(THREE / "examples" / "jsm" / f, project / "assets/js" / f)
    shutil.copy(hf.GSAP_JS, project / "assets/js/gsap.min.js")
    shutil.copy(style.JS_SRC / "world.js", project / "assets/js/world.js")
    for f in style.FONTS:
        shutil.copy(C.FONTS_DIR / f, project / "assets/fonts" / f)
    # (the voice timeline rides along for styles that need each line's own timing, e.g. web-series dialogue)
    data, html, shots, summary, line = style.build(meta, dict(parsed, timeline=tl), spans, words, W, H, project, warnings)
    (project / "index.html").write_text(html, encoding="utf-8")
    log(f"  project: {line}")
    progress("scenes", 1, 1)

    # 3 picture
    progress("encoding", 0, 1)
    raw = project / "renders" / f"{mode}.mp4"
    raw.unlink(missing_ok=True)
    t_pic = time.time()
    code, out, err = hf.run(["render", "-o", raw, "--quality", QUALITY[mode], "--fps", C.FPS, "--workers",
                             C.env("BLOCKY_WORKERS", "auto"), "--quiet"], project, log, f"{mode} render", timeout=3 * 3600)
    if code != 0 or not raw.exists():
        raise PipelineError(f"HyperFrames render failed ({style.NAME}/logs/hyperframes_render.log): " +
                            " | ".join((err or out).strip().splitlines()[-4:]))
    got = media_duration(raw)
    if abs(got - total) > 0.5:
        raise PipelineError(f"HyperFrames rendered {got:.1f} s but the video is {total:.1f} s long")
    frames = round(total * C.FPS)
    secs_pic = time.time() - t_pic
    log(f"  picture: {frames} frames in {secs_pic:.1f} s ({secs_pic * 1000 / max(1, frames):.0f} ms a frame)")
    video = work / "video.mp4"
    shutil.copy(raw, video)

    # 4 captions, sound, encode
    progress("captions")
    ass = job_dir / f"captions_{mode}.ass"
    cw = [w[:4] for w in words]
    page_caps = not meta.get("captions")            # no captions: line = the style's own captions, in the picture
    captions.write_ass(cw, W, H, ass, total, style=P["captions"], preset="none" if page_caps else meta["presets"]["captions"])
    captions.write_srt(cw, job_dir / f"captions_{mode}.srt")
    progress("audio mix")
    from .motion_gfx.render import plan_sound
    timed = plan_sound(style.cues(shots) if meta.get("sfx") != "off" else [], total, sfx_files(), 0.35)
    segs = [dict(s, sfx_auto=[], sfx=[] if meta.get("sfx") == "off" else s["sfx"]) for s in parsed["segments"]]
    mix = dict(parsed, segments=segs, sfx_timed=timed, meta=dict(meta))
    norm, bgm, sfx_used, loud_in, music = assemble._mix_audio(mix, tl, total, voice_wav, job_dir, warnings,
                                                              random.Random(title))
    progress("encoding")
    out = job_dir / f"{mode}.mp4"
    assemble.final_encode(video, norm, ass, out, mode, total, job_dir)
    dur = media_duration(out)
    (job_dir / f"timeline_{mode}.json").write_text(json.dumps(
        {"segments": [{"start": x["start"], "dur": x["dur"]} for x in tl],
         "shots": [{"shot": i, "type": s["type"], "start": round(st, 2), "dur": round(d, 2)}
                   for i, (s, (st, d)) in enumerate(zip(parsed["shots"], spans))],
         "beats": [{"start": round(st, 2), "dur": round(d, 2), "template": style.NAME} for st, d in spans]}, indent=1),
        encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    secs = time.time() - t_start
    log(f"sound effects: {len(sfx_used)}; music: {', '.join(m['track'] for m in music) or 'none'}")
    log(f"DONE {out.name}: {fmt_ts(dur)}, {out.stat().st_size / 1e6:.1f} MB, rendered in {secs:.0f}s")
    return {"mode": mode, "file": out.name, "duration_sec": round(dur, 1), "size_mb": round(out.stat().st_size / 1e6, 1),
            "render_seconds": round(secs), "width": W, "height": H, "bgm": bgm.name if bgm else None,
            "sfx_used": sfx_used, "chapters": [], "warnings": warnings, "music": music,
            "type": meta.get("type", "full"), "encoder": encoder.name(), "loudness_before": loud_in,
            "loudness_target": C.TARGET_LUFS, "rendering_method": style.NAME, style.NAME: summary}


def copy_files(base: Path, rel_files, dest: Path) -> int:
    """Copy model files (relative to base) into dest at the same relative paths, with the .mtl of an OBJ and the
    Textures/ folder next to a model when there is one. Returns the number of files."""
    done = set()
    for rel in rel_files:
        src = base / rel
        for f in [src] + ([src.with_suffix(".mtl")] if src.suffix == ".obj" else []):
            if f in done or not f.exists():
                continue
            out = dest / f.relative_to(base)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, out)
            done.add(f)
        tex = src.parent / "Textures"
        if tex.is_dir() and tex not in done:
            shutil.copytree(tex, dest / tex.relative_to(base), dirs_exist_ok=True)
            done.add(tex)
    return len([f for f in done if f.is_file()])
