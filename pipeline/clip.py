"""
clip.py  -  a vertical Short cut from a video that's already finished ("from a video I already made").

  script header:  type: short / clip_from: <job id> / clip_start: 4:12 / clip_end: 5:38

Nothing new is generated: the source job's voice cache gives the exact word timings (so the cut lands between
words, and the presenter's lip sync is rebuilt), its AI images come from its cache/ and the shared image cache.
Every shot is re-framed for 9:16:
  [talk:]                 re-rendered vertical, the character centred (crisp, from the pose pack)
  [ai:] [stock:] [act:]   cropped to 9:16 around the subject (the nearest part of the depth map), then moved
  cards / numbers / ...   re-drawn vertical inside the Shorts safe area
Captions are re-made vertical in the Short style; the audio is the source's finished mix (voice + music + sfx)
for that span, faded at the edges and normalised to -14 LUFS again.
"""

import json
import shutil
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from . import assemble, captions, encoder, script_parser, visuals
from . import config as C
from .util import PipelineError, fmt_ts, h, log, media_duration, run


def _snap(words, a: float, b: float):
    """Move the cut points into the silence between words, so no word is chopped in half."""
    first = next((w for w in words if w[2] > a + 0.05), None)
    last = next((w for w in reversed(words) if w[1] < b - 0.05), None)
    if not first or not last or last[2] <= first[1]:
        raise PipelineError("there are no spoken words between clip_start and clip_end")
    prev_end = max([w[2] for w in words if w[2] <= first[1]] or [0.0])
    next_start = min([w[1] for w in words if w[1] >= last[2]] or [last[2] + 1.0])
    a2 = max(prev_end + 0.02, first[1] - 0.12, 0.0)
    b2 = min(next_start - 0.02, last[2] + 0.35)
    return a2, b2


def vertical_crop(img_path: Path, W: int, H: int, cache: Path) -> Path:
    """Crop a landscape still to W:H around its subject (weighted by the depth map: near = subject) and scale
    it to W x H. Cached per image + size."""
    out = cache / f"vcrop_{h(Path(img_path).name, W, H)}.png"
    if out.exists():
        return out
    from .parallax import depth_map
    im = Image.open(img_path).convert("RGB")
    cw = min(im.width, int(round(im.height * W / H)))
    try:
        d = depth_map(img_path)
        d = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).resize((im.width, im.height), Image.BILINEAR),
                       dtype=np.float32) / 255.0
        wt = np.clip(d - np.percentile(d, 60), 0, None) ** 2      # only the nearest ~40% counts
        col = wt.sum(axis=0)
        cx = float((col * np.arange(im.width)).sum() / col.sum()) if col.sum() > 0 else im.width / 2
    except Exception:
        cx = im.width / 2
    x0 = int(min(max(cx - cw / 2, 0), im.width - cw))
    crop = im.crop((x0, 0, x0 + cw, im.height)).resize((W, H), Image.LANCZOS)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    cache.mkdir(parents=True, exist_ok=True)
    crop.save(out)
    return out


def _still(shot, sp, src_dir: Path):
    """The cached landscape image of an [ai:]/[stock:]/[act:] shot (raises if it was never made)."""
    if shot["type"] == "act":
        return visuals.act_image(shot, sp["meta"]["character_data"], 1920, 1080, src_dir, cached_only=True)
    prompt = shot["prompt"] if shot["type"] == "ai" else f"{shot['query']}, real-world documentary photograph"
    return visuals.ai_image(prompt, 1920, 1080, src_dir, cached_only=True)


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    t_start = time.time()
    job_dir = Path(job_dir).resolve()
    clip = parsed["meta"]["clip"]
    src, why = script_parser.clip_source(clip["source"])
    if not src:
        raise PipelineError(why)
    src_dir = src["dir"]
    sp = script_parser.parse((src_dir / "script.md").read_text(encoding="utf-8"))
    if not sp["ok"]:
        raise PipelineError("the source video's script no longer passes Check")
    W, H = C.SIZES[("vertical", mode)]
    work = job_dir / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    log(job_dir, f"=== CLIP {mode.upper()}: {src['id']} {fmt_ts(clip['start'])}-{fmt_ts(clip['end'])} -> {W}x{H}")

    # 1 the source timeline, rebuilt from its voice cache (no new voice: every segment must be cached)
    progress("voice", 0, 1)
    tl, total = assemble._timeline(sp, src_dir, lambda *a: None)
    spans = assemble._shot_spans(sp, tl, total)
    ref = json.loads((src_dir / "timeline_final.json").read_text(encoding="utf-8"))
    drift = max(abs(s["start"] - r["start"]) for s, r in zip(tl, ref["segments"]))
    if drift > 0.05 or len(tl) != len(ref["segments"]):
        raise PipelineError(f"the source's voice timings changed since its final ({drift:.2f} s); re-make its final")
    words = [[wd[0], s["start"] + wd[1], s["start"] + wd[2], wd[3] if len(wd) > 3 else "", si]
             for si, s in enumerate(tl) for wd in s["words"]]
    a, b = _snap(words, clip["start"], min(clip["end"], total))
    dur = b - a
    P = C.TYPES["short"]
    if dur > P["max_sec"] + 0.5 or dur < P["min_sec"] - 0.5:
        raise PipelineError(f"the clip is {dur:.1f} s after snapping to words; a Short must be "
                            f"{P['min_sec']}-{P['max_sec']} s")
    log(job_dir, f"cut snapped to words: {a:.2f}-{b:.2f} s ({dur:.1f} s)")
    progress("voice", 1, 1)

    # 2 the shots inside the cut, each re-framed vertical
    pieces = []
    for i, (st, d) in enumerate(spans):
        s0, s1 = max(st, a), min(st + d, b)
        if s1 - s0 > 0.04:
            pieces.append([i, s0, s1])
    for k in range(len(pieces) - 1, 0, -1):          # a sliver under 0.4 s joins the shot before it
        if pieces[k][2] - pieces[k][1] < 0.4:
            pieces[k - 1][2] = pieces[k][2]
            del pieces[k]
    char = sp["meta"].get("character_data")
    if char and any(sp["shots"][i]["type"] == "talk" for i, _, _ in pieces):
        from . import presenter
        if not presenter.pack_ready(char["name"]):
            raise PipelineError(f"{char['name']}'s character pack isn't on this machine "
                                f"(import it: tools/import_character_pack.py)")
    abs_words = [w[:4] for w in words]
    clips = []
    progress("visuals", 0, len(pieces))
    for n, (i, s0, s1) in enumerate(pieces):
        shot, d = sp["shots"][i], s1 - s0
        out = work / f"clip_{n:03d}.mp4"
        if shot["type"] == "talk":
            from . import presenter
            presenter.talk_clip(shot, i, d, abs_words, s0, W, H, out, job_dir, mode, char["name"])
        elif shot["type"] in ("ai", "stock", "act"):
            img = vertical_crop(_still(shot, sp, src_dir), W, H, job_dir / "cache")
            visuals.still_motion(img, d, i, W, H, out, job_dir, mode)
        else:
            visuals.graphic_clip(shot, d, W, H, out, job_dir, mode, safe=P["safe"])
        clips.append(out)
        progress("visuals", n + 1, len(pieces))
    video = work / "video.mp4"
    assemble.join_clips(clips, video, job_dir)
    log(job_dir, f"visuals done ({len(pieces)} shots, no new AI images) at {time.time() - t_start:.0f}s")

    # 3 captions, Short style
    progress("captions")
    cw = [[w[0], w[1] - a, w[2] - a, w[4]] for w in words if w[1] >= a - 0.01 and w[2] <= b + 0.01]
    ass = job_dir / f"captions_{mode}.ass"
    captions.write_ass(cw, W, H, ass, dur, style="short")
    captions.write_srt(cw, job_dir / f"captions_{mode}.srt")

    # 4 audio: the source's finished mix for this span
    progress("audio mix")
    raw = work / "audio.wav"
    run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", src_dir / "final.mp4", "-vn",
         "-af", f"afade=t=in:d=0.04,afade=t=out:st={max(0, dur - 0.3):.3f}:d=0.3", "-ar", "48000",
         "-c:a", "pcm_s16le", raw], job_dir, "cut audio")
    norm = work / "audio_norm.wav"
    loud_in = assemble.loudnorm(raw, norm, job_dir)

    # 5 encode
    progress("encoding")
    out = job_dir / f"{mode}.mp4"
    assemble.final_encode(video, norm, ass, out, mode, dur, job_dir)
    real = media_duration(out)
    shots = []
    for i, s0, s1 in pieces:
        shots.append({"shot": i, "type": sp["shots"][i]["type"], "start": round(s0 - a, 2), "dur": round(s1 - s0, 2)})
    (job_dir / f"timeline_{mode}.json").write_text(json.dumps(
        {"segments": [], "shots": shots, "clip": {"source": src["id"], "start": a, "end": b}}, indent=1),
        encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    secs = time.time() - t_start
    log(job_dir, f"DONE {out.name}: {fmt_ts(real)}, {out.stat().st_size / 1e6:.1f} MB, rendered in {secs:.0f}s")
    src_music = (src["state"].get("final") or {}).get("bgm")
    return {"mode": mode, "file": out.name, "duration_sec": round(real, 1), "size_mb": round(out.stat().st_size / 1e6, 1),
            "render_seconds": round(secs), "width": W, "height": H, "bgm": src_music, "sfx_used": [],
            "chapters": [], "warnings": [], "music": [], "type": "short", "encoder": encoder.name(),
            "loudness_before": loud_in, "loudness_target": C.TARGET_LUFS,
            "clip": {"source": src["id"], "source_title": src["title"], "start": round(a, 2), "end": round(b, 2),
                     "shots": len(pieces), "source_tags": sp["meta"].get("tags") or [],
                     "source_description": (sp["meta"].get("description") or "").strip().split("\n")[0]}}
