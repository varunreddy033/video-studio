"""
motion.py  -  `style: motion` renderer (docs/MOTION_PLAN.md). The classic renderer (assemble.py) is not touched.

  1 voice      the classic voice step (Kokoro, cached) -> word timings
  2 assets     images (FLUX, cached; drafts use placeholders) and lip-synced [talk:] clips, made in Python,
               ONE image job at a time; the image model is stopped before step 4 (never FLUX + Remotion together)
  3 timeline   timeline.json (docs/MOTION_TIMELINE.md): scenes, layers, cues tied to word indexes -> frames
  4 picture    Remotion (motion/) renders the video only, with MOTION_CONCURRENCY browser tabs
  5 audio      the classic mix: voice + ducked music + sfx -> two-pass loudnorm to -14 LUFS
  6 mux        picture + audio -> draft.mp4 / final.mp4 (no re-encode of the picture)
Every stage is timed; the job page shows the times.
"""

import json
import os
import random
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import assemble, captions, visuals
from . import config as C
from .util import PipelineError, fmt_ts, log, media_duration, run

MOTION_DIR = C.BASE_DIR / "motion"
FPS = 30
W, H = 1920, 1080                 # the timeline is always 1080p; drafts render at --scale 0.5
TRANSITION = 18                    # frames
SCENE_PALETTE_TINTS = ["#16294A", "#1A2440", "#132643", "#182A45"]


def npx() -> str:
    for cand in (shutil.which("npx"), "/opt/homebrew/opt/node@22/bin/npx", "/usr/local/opt/node@22/bin/npx"):
        if cand and Path(cand).exists():
            return cand
    raise PipelineError("Node.js isn't installed (motion style needs it): run bash setup.sh")


def _link(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)              # same disk: instant, no copy
    except OSError:
        shutil.copy2(src, dst)


# ------------------------------------------------------------------------------------------ assets ---
def _assets(parsed, tl, spans, all_words, job_dir: Path, public: Path, mode: str, progress, warnings):
    """Per shot: the file Remotion shows (relative to the public dir), or None for code-drawn graphics."""
    meta = parsed["meta"]
    char = meta.get("character_data")
    style = (meta.get("presets") or {}).get("art_style")
    out = {}
    shots = parsed["shots"]
    need = [i for i, s in enumerate(shots) if s["type"] in ("ai", "stock", "act", "talk")]
    for n, i in enumerate(need):
        progress("images + presenter", n, len(need))
        sh, (t0, dur) = shots[i], spans[i]
        kind = sh["type"]
        if kind == "talk":
            from . import presenter
            if char and presenter.pack_ready(char["name"]):
                clip = public / "assets" / f"talk_{i:03d}.mp4"
                clip.parent.mkdir(parents=True, exist_ok=True)
                cw, ch = (W, H) if mode == "final" else (W // 2, H // 2)      # drafts render at half size
                presenter.talk_clip(sh, i, dur, all_words, t0, cw, ch, clip, job_dir, mode, char["name"])
                out[i] = {"type": "video", "src": f"assets/{clip.name}"}
                continue
            if mode != "draft":
                raise PipelineError(f"no finished character pack for {char['name'] if char else '?'}")
            img = visuals.placeholder_image(f"PRESENTER: {sh['pose']} @ {sh['set']}",
                                            "lip-synced presenter clip (appears once the pack is built)", W, H, job_dir)
        elif kind == "act":
            if mode == "draft" or not char:
                img = visuals.placeholder_image(f"CHARACTER SCENE ({sh['framing']})", sh["prompt"], W, H, job_dir)
            else:
                img = visuals.act_image(sh, char, W, H, job_dir)
        else:
            prompt, stock = (sh["query"], True) if kind == "stock" else (sh["prompt"], False)
            if mode == "draft":
                img = visuals.placeholder_image("AI IMAGE (made in the final render)", prompt, W, H, job_dir)
            else:
                img = visuals.ai_image(prompt, W, H, job_dir, style=style, stock=stock)   # same cache as classic
        dst = public / "assets" / f"img_{i:03d}{Path(img).suffix}"
        _link(Path(img), dst)
        out[i] = {"type": "image", "src": f"assets/{dst.name}"}
    progress("images + presenter", len(need), len(need))
    visuals.stop_image_worker()        # frees ~5 GB and the GPU before Remotion starts
    return out


# ---------------------------------------------------------------------------------------- timeline ---
def _transition(k: int, kinds):
    """Phase-2 chooser (phase 4 replaces it): push from the right, every 4th scene a push from the bottom,
    never the same twice in a row when the next scene is a graphic."""
    if k == 0:
        return None
    if k % 4 == 3:
        return {"type": "push", "dir": "from-bottom", "frames": TRANSITION}
    return {"type": "push", "dir": "from-right", "frames": TRANSITION}


def build_timeline(parsed, tl, spans, total, assets) -> dict:
    """Classic shot tags -> timeline v1 (one scene per shot). Phase 3's v3 tags ([scene:], [+ ...]) build richer
    scenes on the same contract."""
    words = []
    for si, s in enumerate(tl):
        for wd in s["words"]:
            st = s["start"] + wd[1]
            words.append({"w": wd[0], "s": round(st, 3), "e": round(s["start"] + wd[2], 3), "seg": si,
                          "frame": round(st * FPS)})
    dur_frames = round(total * FPS)
    # scene k: from its shot's start frame; it lasts until the next scene starts + the transition overlap
    starts = [round(st * FPS) for st, _ in spans]
    scenes = []
    for k, sh in enumerate(parsed["shots"]):
        frm = starts[k]
        nxt = starts[k + 1] if k + 1 < len(starts) else dur_frames
        trans = _transition(k, None)
        begin = frm - (trans["frames"] if trans else 0)
        frames = nxt - begin
        first_word = next((wi for wi, w in enumerate(words) if w["frame"] >= frm - 2), None)

        def cue(offset_frames=0, word=None):
            f = (words[word]["frame"] if word is not None else frm + offset_frames) - begin
            return {"frame": max(0, f), **({"word": word} if word is not None else {})}

        el = {"id": f"e{k}", "box": {"x": 0, "y": 0, "w": W, "h": H}}
        kind = sh["type"]
        if k in assets:
            a = assets[k]
            el.update(type=a["type"], props={"src": a["src"], "move": k}, enter={"frame": 0, "anim": "none"})
        elif kind == "card":
            el.update(type="card", props={"text": sh["text"], "sub": sh.get("sub", "")}, enter={**cue(2), "anim": "pop"})
        elif kind == "number":
            # count up over the first ~1.5 s of its narration
            el.update(type="number", props={"value": sh["value"], "decimals": sh["decimals"], "prefix": sh["prefix"],
                                            "suffix": sh["suffix"], "label": sh.get("label", ""), "countFrames": 45},
                      enter={**(cue(word=first_word) if first_word is not None else cue(2)), "anim": "pop"})
        elif kind == "quote":
            el.update(type="quote", props={"text": sh["text"], "by": sh.get("by", "")}, enter={**cue(2), "anim": "fade"})
        elif kind == "chart":
            el.update(type="chart", props={"kind": sh["chart"], "title": sh["title"], "data": sh["data"],
                                           "unit": sh.get("unit", "")}, enter={**cue(2), "anim": "pop"})
        else:
            raise PipelineError(f"motion style can't show a [{kind}:] shot yet")
        scenes.append({"id": f"s{k}", "from": begin, "frames": frames, "transition": trans,
                       "background": {"tint": SCENE_PALETTE_TINTS[k % len(SCENE_PALETTE_TINTS)]},
                       "elements": [el]})
    return {"version": 1, "fps": FPS, "width": W, "height": H, "durationFrames": dur_frames,
            "palette": parsed["meta"].get("palette") or "navy", "words": words,
            "captions": {"show": True, "style": (parsed["meta"].get("presets") or {}).get("captions", "amber_word")},
            "scenes": scenes}


# -------------------------------------------------------------------------------------- the render ---
def _remotion(timeline_path: Path, public: Path, out: Path, mode: str, job_dir: Path, progress):
    conc = str(C.MOTION_CONCURRENCY)
    cmd = [npx(), "remotion", "render", "src/index.ts", "Motion", str(out), f"--props={timeline_path}",
           f"--public-dir={public}", f"--concurrency={conc}", "--codec=h264",
           f"--crf={18 if mode == 'final' else 26}", "--log=info"]
    if mode == "draft":
        cmd.append("--scale=0.5")
    p = subprocess.Popen(cmd, cwd=MOTION_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-25:]
        m = re.search(r"Rendered\s+(\d+)/(\d+)", line) or re.search(r"\b(\d+)/(\d+)\b", line)
        if m and int(m.group(2)) > 10:
            progress("picture (Remotion)", int(m.group(1)), int(m.group(2)))
    if p.wait() != 0 or not out.exists():
        log(job_dir, "FAILED: Remotion render\n  " + "\n  ".join(tail[-12:]))
        raise PipelineError("Remotion render failed: " + (tail[-1] if tail else "no output"))


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    t_start = time.time()
    stages = {}
    job_dir = Path(job_dir).resolve()
    meta = parsed["meta"]
    work = job_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    public = work / "motion_public"
    for f in (MOTION_DIR / "public" / "fonts").iterdir():
        _link(f, public / "fonts" / f.name)
    rng = random.Random(meta.get("title", ""))          # same music pick as classic
    warnings = []
    log(job_dir, f"=== MOTION {mode.upper()} render: '{meta.get('title')}'  {len(parsed['segments'])} segments, "
                 f"{len(parsed['shots'])} shots")

    t = time.time()
    tl, total = assemble._timeline(parsed, job_dir, progress)
    voice_wav = assemble._voice_track(tl, total, job_dir)
    spans = assemble._shot_spans(parsed, tl, total)
    all_words = [[wd[0], s["start"] + wd[1], s["start"] + wd[2], wd[3] if len(wd) > 3 else ""]
                 for s in tl for wd in s["words"]]
    stages["voice"] = time.time() - t

    t = time.time()
    assets = _assets(parsed, tl, spans, all_words, job_dir, public, mode, progress, warnings)
    stages["images + presenter"] = time.time() - t

    t = time.time()
    timeline = build_timeline(parsed, tl, spans, total, assets)
    tpath = work / "timeline.json"
    tpath.write_text(json.dumps(timeline), encoding="utf-8")
    (job_dir / f"motion_timeline_{mode}.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    stages["timeline"] = time.time() - t

    t = time.time()
    progress("picture (Remotion)", 0, timeline["durationFrames"])
    picture = work / "picture.mp4"
    _remotion(tpath, public, picture, mode, job_dir, progress)
    stages["picture (Remotion)"] = time.time() - t
    log(job_dir, f"picture done: {timeline['durationFrames']} frames in {stages['picture (Remotion)']:.0f}s "
                 f"(concurrency {C.MOTION_CONCURRENCY})")

    t = time.time()
    progress("audio mix")
    norm, bgm, sfx_used, loud_in, music = assemble._mix_audio(parsed, tl, total, voice_wav, job_dir, warnings, rng)
    words = [[wd[0], s["start"] + wd[1], s["start"] + wd[2], si] for si, s in enumerate(tl) for wd in s["words"]]
    captions.write_srt(words, job_dir / f"captions_{mode}.srt")      # for YouTube's subtitles upload
    stages["audio mix"] = time.time() - t

    t = time.time()
    progress("mux")
    out = job_dir / f"{mode}.mp4"
    run(["ffmpeg", "-y", "-i", picture, "-i", norm, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", out.name], job_dir, "mux",
        cwd=job_dir)
    dur = media_duration(out)
    stages["mux"] = time.time() - t

    chapters = [{"title": c["title"], "start": 0.0 if c["segment"] == 0 else tl[c["segment"]]["start"]}
                for c in parsed["chapters"] if c["segment"] < len(tl)]
    shots = [{"shot": i, "type": parsed["shots"][i]["type"], "start": round(st, 2), "dur": round(d, 2)}
             for i, (st, d) in enumerate(spans)]
    (job_dir / f"timeline_{mode}.json").write_text(json.dumps(
        {"segments": [{"start": s["start"], "dur": s["dur"]} for s in tl], "shots": shots}, indent=1), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    secs = time.time() - t_start
    log(job_dir, "stages: " + ", ".join(f"{k} {v:.0f}s" for k, v in stages.items()))
    log(job_dir, f"DONE {out.name}: {fmt_ts(dur)}, {out.stat().st_size / 1e6:.1f} MB, rendered in {secs:.0f}s")
    scale = 0.5 if mode == "draft" else 1
    return {"mode": mode, "file": out.name, "duration_sec": round(dur, 1), "size_mb": round(out.stat().st_size / 1e6, 1),
            "render_seconds": round(secs), "width": int(W * scale), "height": int(H * scale),
            "bgm": bgm.name if bgm else None, "sfx_used": sfx_used, "chapters": chapters, "warnings": warnings,
            "music": music, "type": meta.get("type", "full"), "style": "motion", "encoder": "remotion (libx264)",
            "loudness_before": loud_in, "loudness_target": C.TARGET_LUFS,
            "stages": {k: round(v, 1) for k, v in stages.items()}}
