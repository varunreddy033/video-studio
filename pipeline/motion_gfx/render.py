"""The motion renderer (rendering_method: motion).

  voice     assemble._timeline / _voice_track / _shot_spans (the same Kokoro voice, cache and cut points)
  beats     beats.split: every shot becomes 1.2-3 s beats on the voice's clause breaks
  scenes    templates.pick + build per beat, palette rotation, transitions (compose.transition_for)
  project   compose: output/jobs/<id>/motion/ (index.html, compositions/, assets/), the caption chip overlay
  check     `hyperframes check` (lint + runtime), then snapshots of a few beats (hyperframes skill: never render
            what hasn't been checked and looked at)
  render    `hyperframes render` -> motion/renders/<mode>.mp4 (picture)
  finish    sound cues from the animation (sfx_timed, every file of a kind in turn), assemble._mix_audio (music +
            ducking + -14 LUFS), assemble.final_encode (captions: the chip is already in the picture)

Returns the same result dict as assemble.render, so jobs.py, thumbnails, metadata and the upload pack work as before.
"""

import hashlib
import json
import random
import re
import shutil
import time
from pathlib import Path

from PIL import Image

from .. import assemble, captions, encoder
from .. import config as C
from ..util import PipelineError, best_match, fmt_ts, log as _log, media_duration, run, sfx_files
from . import beats as B
from . import compose, hf, history, picker
from . import variety as V
from . import design as D
from . import templates as T

# a cue's kind -> what to use when the library has no such folder
FALLBACK = {"stamp": "impact", "tick": "click", "coin": "cash", "bubble": "pop", "swipe": "whoosh", "paper": "swipe",
            "typing": "click", "riser": "whoosh", "ding": "pop", "cash": "ding", "alert": "ding", "error": "impact",
            "glitch": "click", "shutter": "click", "heartbeat": "impact",
            "notification": "ding", "swoosh-up": "riser", "boing": "pop", "record-scratch": "glitch",
            "crowd-gasp": "impact", "keyboard-enter": "click", "coin-drop": "coin", "door": "impact",
            "crowd-cheer": "success", "success": "ding"}
GAIN = {"whoosh": 0.55, "swipe": 0.55, "pop": 0.6, "bubble": 0.55, "click": 0.6, "tick": 0.5, "impact": 0.75,
        "ding": 0.65, "cash": 0.7, "riser": 0.55, "paper": 0.6, "typing": 0.45, "alert": 0.5, "error": 0.55,
        "glitch": 0.5, "shutter": 0.6, "heartbeat": 0.6, "coin": 0.65, "stamp": 0.7, "notification": 0.55,
        "swoosh-up": 0.5, "boing": 0.55, "record-scratch": 0.5, "crowd-gasp": 0.5, "keyboard-enter": 0.55,
        "coin-drop": 0.6, "door": 0.6, "crowd-cheer": 0.45, "success": 0.55}
# sfx: header -> seconds between two animation effects. rich ~ 25 a minute (the references' density), auto ~ 15
GAPS = {"rich": 1.4, "auto": 2.2}
QUALITY = {"draft": "draft", "final": "standard"}


def _available(kind, files, cache):
    seen = set()
    while kind and kind not in seen:
        seen.add(kind)
        if kind not in cache:
            cache[kind] = best_match(kind, files) is not None
        if cache[kind]:
            return kind
        kind = FALLBACK.get(kind)
    return None


def plan_sound(cues, total, files, min_gap):
    """[(t, kind)] -> [{t, kind, gain}]: kinds mapped to what the library has, at least min_gap apart (the earlier
    cue wins), nothing after the end."""
    cache, out, last = {}, [], -9.0
    for t, kind in sorted(cues):
        k = _available(kind, files, cache)
        if not k or t < 0 or t > total - 0.2 or t - last < min_gap:
            continue
        out.append({"t": round(t, 3), "kind": k, "gain": GAIN.get(k, 0.6)})
        last = t
    return out


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    t_start = time.time()
    job_dir = Path(job_dir).resolve()
    meta = parsed["meta"]
    log = lambda m: _log(job_dir, m)
    tools = hf.check_installed()
    fmt = meta["format"]
    W, H = C.SIZES[(fmt, "final")]
    OW, OH = C.SIZES[(fmt, mode)]
    P = C.TYPES[meta.get("type", "full")]
    project = job_dir / "motion"
    work = job_dir / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    warnings = []
    title = meta.get("title", "")
    log(f"=== {mode.upper()} render (motion graphics): '{title}'  {len(parsed['shots'])} shots, {W}x{H} -> {OW}x{OH}, "
        f"HyperFrames {tools['hyperframes']}, Node {tools['node']}, encoder {encoder.name()}")

    # 0 reserve this video's look in data/asset_history.json before anything else (videos queued or rendered at the
    #   same time then never share a look; docs/VARIETY_PLAN.md section 6)
    look = history.reserve(meta, title, job_dir.name)
    # 1 voice + cut points (identical to the AI-image renderer)
    tl, total = assemble._timeline(parsed, job_dir, progress)
    if P["max_sec"] and total > P["max_sec"]:
        raise PipelineError(f"the voice is {fmt_ts(total)} long, over the {fmt_ts(P['max_sec'])} limit for a "
                            f"{P['label']}; cut some lines")
    voice_wav = assemble._voice_track(tl, total, job_dir)
    spans = assemble._shot_spans(parsed, tl, total)
    log(f"voice done: {fmt_ts(total)} ({total:.1f} s) in {time.time() - t_start:.0f}s")

    # 2 beats -> scenes
    progress("visuals", 0, 1)
    beats = B.split(parsed, tl, spans)
    seed = int(hashlib.sha1(title.encode()).hexdigest()[:6], 16)
    T.set_look(look["fonts"])
    order = D.palette_order(len(beats), seed, D.PALETTE_SETS[look["palette"]])
    seen = history.recent(title)
    log(f"  look: icons {look['icons']}, palette {look['palette']}, fonts {look['fonts']}, {look['icon_style']} icons "
        f"(last videos: {len(seen['looks'])})")
    shutil.rmtree(project / "compositions", ignore_errors=True)
    compose.prepare(project, voice_wav)
    cues = []
    used_tpl, variants, info, plan = picker.plan_video(beats, dict(meta, look_icons=look["icons"]), seen, seed)
    from . import extras as X
    video_years = sorted({y for b in beats for y in X.years(b["text"])})
    icons = {}
    for (bi, slot), pk in plan["picks"].items():
        icons.setdefault(bi, {})[slot] = dict(pk, uri=picker.data_uri(pk["id"]), sound=picker.sound_for(pk["id"]))
    icon_rep = plan["report"]
    (project / "icons.json").write_text(json.dumps(dict(icon_rep, pool=plan["pool"], nouns=plan["nouns"]), indent=1),
                                        encoding="utf-8")
    log(f"  icons ({plan['family']}): {icon_rep['icons']} different in {icon_rep['beats_with_icon']} of {len(beats)} scenes, "
        f"most used {icon_rep['most_used']['count']}x, question-style {icon_rep['question_style']}, "
        f"{icon_rep['from_pool']} from the topic pool of {icon_rep['pool_size']}, {len(icon_rep['without'])} scenes found none")
    for i, b in enumerate(beats):
        b["transition"] = compose.transition_for(beats, i)
        b["ov"] = 0.0 if b["transition"] == "cut" else D.TRANSITION
        name = used_tpl[i]
        pal = D.PALETTES[order[i]]
        ctx = {"W": W, "H": H, "fmt": fmt, "pal": pal, "dur": b["dur"], "shot": parsed["shots"][b["shot"]],
               "rnd": random.Random(seed + i), "icons": icons.get(i, {}),
               "look": look, "variant": variants[i], "years": video_years, **info[i]}
        P_ = compose.host(i) + "-"
        parts = T.build(name, P_, b, ctx)
        (project / "compositions" / f"scene_{i + 1:03d}.html").write_text(
            compose.scene_file(i, b, parts, pal, b["ov"], W, H), encoding="utf-8")
        for t, kind in parts["cues"]:
            cues.append((b["start"] + t, kind))
        if b["transition"] != "cut":
            cues.append((b["start"] - b["ov"] * 0.6, "swipe" if b["transition"] == "push" else "whoosh"))
        b["template"] = name
        b["variant"] = variants[i]
        progress("visuals", i + 1, len(beats))
    words = B.video_words(tl)
    cap = meta["presets"]["captions"]
    chip = cap == "chip"
    if chip:
        (project / "compositions" / "captions.html").write_text(
            compose.captions_file([w[:3] for w in words], total, W, H, fmt), encoding="utf-8")
    (project / "index.html").write_text(compose.index_file(beats, total, W, H, C.FPS, title, chip), encoding="utf-8")
    (project / "beats.json").write_text(json.dumps(
        [dict({k: b[k] for k in ("shot", "kind", "index", "start", "end", "template", "transition", "text")},
              variant=b["variant"], icons=[x["id"] for _s, x in sorted(icons.get(i, {}).items())]) for i, b in enumerate(beats)],
        indent=1), encoding="utf-8")
    counts = {n: used_tpl.count(n) for n in sorted(set(used_tpl))}
    log(f"  {len(beats)} scenes (one every {total / max(1, len(beats)):.1f} s): " +
        ", ".join(f"{n} {c}" for n, c in counts.items()))
    vrep = V.report(used_tpl, [b["variant"] for b in beats], [b["transition"] for b in beats], beats,
                    seen.get("videos"), look)
    log("  " + V.log_line(vrep))

    # 3 check + look (hyperframes skill)
    progress("checks", 0, 1)
    code, out, err = hf.run(["check", "--json", "--no-cache", "--no-craft", "--no-contrast", "--timeout", "90s"],
                            project, log, "check")
    rep = hf.json_out(out) or {}
    errs = [f for sec in ("lint", "runtime") for f in (rep.get(sec) or {}).get("findings", []) if f.get("severity") == "error"]
    if not rep:
        raise PipelineError("hyperframes check didn't run: " + " | ".join((err or out).strip().splitlines()[-3:]))
    if errs:
        raise PipelineError("the motion project has errors (see motion/logs/hyperframes_check.log): " +
                            "; ".join(f"{f.get('code')}: {f.get('message', '')[:120]}" for f in errs[:3]))
    nwarn = sum((rep.get(s) or {}).get("warningCount", 0) for s in ("lint", "runtime", "layout"))
    if nwarn:
        log(f"  hyperframes check: {nwarn} warning(s) (motion/logs/hyperframes_check.log)")
    picks = sorted({min(len(beats) - 1, int(len(beats) * f)) for f in (0.0, 0.15, 0.35, 0.55, 0.75, 0.92)})
    at = ",".join(f"{beats[k]['start'] + min(beats[k]['dur'] * 0.75, 1.4):.2f}" for k in picks)
    shutil.rmtree(project / "snapshots", ignore_errors=True)
    hf.run(["snapshot", "--at", at, "--no-end", "--json", "--timeout", "90000", "-o", project / "snapshots"], project, log,
           "snapshot")
    progress("checks", 1, 1)

    # 4 render
    progress("encoding", 0, 1)
    renders = project / "renders"
    renders.mkdir(exist_ok=True)
    raw = renders / f"{mode}.mp4"
    raw.unlink(missing_ok=True)
    code, out, err = hf.run(["render", "-o", raw, "--quality", QUALITY[mode], "--fps", C.FPS, "--workers",
                             C.env("MOTION_WORKERS", "2"), "--quiet", "--strict"], project, log, f"{mode} render",
                            timeout=6 * 3600)
    if code != 0 or not raw.exists():
        raise PipelineError("HyperFrames render failed (motion/logs/hyperframes_render.log): " +
                            " | ".join((err or out).strip().splitlines()[-4:]))
    got = media_duration(raw)
    if abs(got - total) > 0.5:
        raise PipelineError(f"HyperFrames rendered {got:.1f} s but the video is {total:.1f} s long")
    log(f"  HyperFrames render: {got:.1f} s of video at {time.time() - t_start:.0f}s")
    video = work / "video.mp4"
    if (OW, OH) != (W, H):
        run(["ffmpeg", "-y", "-i", raw, "-an", "-vf", f"scale={OW}:{OH}:flags=lanczos", "-c:v", "libx264", "-preset",
             "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", video], job_dir, "draft scale")
    else:
        shutil.copy(raw, video)

    # 5 captions (the chip is in the picture; other styles are burned as usual), sound, encode
    progress("captions")
    ass = job_dir / f"captions_{mode}.ass"
    cw = [[w[0], w[1], w[2], w[3]] for w in words]
    captions.write_ass(cw, OW, OH, ass, total, style=P["captions"], preset="none" if chip else cap)
    captions.write_srt(cw, job_dir / f"captions_{mode}.srt")
    progress("audio mix")
    mode_sfx = meta.get("sfx") or "auto"
    segs = [dict(s, sfx_auto=[], sfx=[] if mode_sfx == "off" else s["sfx"]) for s in parsed["segments"]]
    timed = plan_sound(cues, total, sfx_files(), GAPS[mode_sfx]) if mode_sfx in GAPS else []
    import soundfile as sf
    import numpy as np
    vpk = float(np.abs(sf.read(voice_wav, dtype="float32")[0]).max() or 0.5)
    for a in timed:                         # no effect peaks above the voice: keeps -14 LUFS reachable (true peak)
        a["limit"] = max(0.0625, min(1.0, vpk * 0.7))
    parsed = dict(parsed, segments=segs, sfx_timed=timed,           # the animation's cues replace sfx: auto rules
                  sfx_stale=set(seen["sfx"]), meta=dict(meta, music_stale=set(seen["music"])))
    rng = random.Random(title)
    norm, bgm, sfx_used, loud_in, music = assemble._mix_audio(parsed, tl, total, voice_wav, job_dir, warnings, rng)
    norm = _top_up(norm, job_dir)
    progress("encoding")
    out = job_dir / f"{mode}.mp4"
    assemble.final_encode(video, norm, ass, out, mode, total, job_dir)
    dur = media_duration(out)
    chapters = [{"title": c["title"], "start": 0.0 if c["segment"] == 0 else tl[c["segment"]]["start"]}
                for c in parsed["chapters"] if c["segment"] < len(tl)]
    (job_dir / f"timeline_{mode}.json").write_text(json.dumps(
        {"segments": [{"start": x["start"], "dur": x["dur"]} for x in tl],
         "shots": [{"shot": i, "type": parsed["shots"][i]["type"], "start": round(st, 2), "dur": round(d, 2)}
                   for i, (st, d) in enumerate(spans)],
         "beats": [{"start": b["start"], "dur": b["dur"], "template": b["template"]} for b in beats]}, indent=1),
        encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    if mode == "final":                                          # freshness for the next videos (data/, private)
        history.record(title, job_dir.name, {
            "look": look, "icons": sorted({pk["id"] for (bi, _s), pk in plan["picks"].items()}),
            "templates": sorted({f"{'title' if n == 'chapter' else n}:{v}" for n, v in zip(used_tpl, variants)}),
            "palettes": sorted({D.PALETTES[k]["name"] for k in order}),
            "fonts": [look["fonts"]], "music": sorted({m["track"] for m in music or []}),
            "sfx": sorted({u.split(" -> ")[-1] for u in sfx_used}), **V.fingerprint(vrep, look)})
    else:
        history.finish_draft(title, V.fingerprint(vrep, look))
    secs = time.time() - t_start
    n_sfx = len(sfx_used)
    log(f"sound effects: {n_sfx} ({n_sfx / max(1, total) * 60:.0f} a minute), "
        f"{len({u.split(' -> ')[-1] for u in sfx_used})} different files")
    log(f"DONE {out.name}: {fmt_ts(dur)}, {out.stat().st_size / 1e6:.1f} MB, rendered in {secs:.0f}s")
    return {"mode": mode, "file": out.name, "duration_sec": round(dur, 1), "size_mb": round(out.stat().st_size / 1e6, 1),
            "render_seconds": round(secs), "width": OW, "height": OH, "bgm": bgm.name if bgm else None,
            "sfx_used": sfx_used, "chapters": chapters, "warnings": warnings, "music": music,
            "type": meta.get("type", "full"), "encoder": encoder.name(), "loudness_before": loud_in,
            "loudness_target": C.TARGET_LUFS, "rendering_method": "motion",
            "motion": {"scenes": len(beats), "templates": counts, "look": look, "icons": {k: icon_rep[k] for k in ("family", "icons", "most_used", "question_style", "beats_with_icon")}, "sfx_per_min": round(n_sfx / max(1, total) * 60, 1),
                       "variety": vrep}}


def _loudness(path: Path, job_dir: Path, what: str):
    """(integrated LUFS, true peak dBTP) of an audio file, or (None, None)."""
    p = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], job_dir, what)
    txt = p.stderr.decode(errors="replace").split("Summary:")[-1]
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    tp = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", txt)
    return (float(i[-1]) if i else None), (float(tp[-1]) if tp and tp[-1] != "-inf" else None)


def _top_up(norm: Path, job_dir: Path) -> Path:
    """Linear loudnorm stops short of -14 LUFS when the mix's peaks would pass -1.5 dBTP (dense effects and music
    hits). Add the missing fraction of a dB and let a TRUE-PEAK limiter take the few peaks above it: the limiter
    runs on 4x oversampled audio, so the sharp inter-sample peaks of metallic hits (bells, stamps) are caught too.
    A sample-peak limiter let a cow bell through at +2.6 dBTP after AAC (2026-11-11, Mac test)."""
    lufs, tp = _loudness(norm, job_dir, "loudness check")
    if lufs is None:
        return norm
    short = max(0.0, C.TARGET_LUFS - lufs)
    if short < 0.1 and (tp is None or tp <= -1.5):
        return norm
    import soundfile as sf
    sr = sf.info(str(norm)).samplerate
    out = norm.with_name("mix_final.wav")
    run(["ffmpeg", "-y", "-i", norm, "-af",
         f"volume={min(short, 3.0):.2f}dB,aresample={sr * 4},"
         f"alimiter=limit=0.7943:attack=1:release=50:level=false,aresample={sr}",
         "-c:a", "pcm_s24le", out], job_dir, "loudness top-up")
    lufs2, tp2 = _loudness(out, job_dir, "loudness after top-up")
    _log(job_dir, f"  loudness top-up: +{short:.2f} dB, true-peak limit -2.0 dBTP (mix was {lufs:.1f} LUFS / "
                  f"{tp if tp is not None else float('nan'):+.1f} dBTP, now {lufs2:.1f} LUFS / "
                  f"{tp2 if tp2 is not None else float('nan'):+.1f} dBTP)")
    return out


def thumbnails(parsed: dict, job_dir: Path, final_video: Path):
    """3 thumbnail options from frames of the finished animation (thumbnails.py helpers, unchanged)."""
    from .. import thumbnails as TH
    meta = parsed["meta"]
    text = meta.get("thumbnail") or meta.get("title", "")
    tl = json.loads((job_dir / "timeline_final.json").read_text(encoding="utf-8"))
    beats = [b for b in tl.get("beats", []) if b["template"] in ("figure", "number", "memo")] or tl.get("beats") or \
        [{"start": 1.0, "dur": 1.0}]
    out = []
    for i, (frac, side) in enumerate(zip((0.1, 0.45, 0.8), ("left", "right", "left")), start=1):
        b = beats[min(len(beats) - 1, int(len(beats) * frac))]
        frame = job_dir / "cache" / f"thumb_frame_{i}.png"
        frame.parent.mkdir(exist_ok=True)
        # the lower 80 % of the frame: leaves out the caption chip in the top-left corner, keeps 16:9
        run(["ffmpeg", "-y", "-ss", f"{b['start'] + b['dur'] * 0.8:.2f}", "-i", final_video, "-frames:v", "1", "-vf",
             "crop=iw*0.8:ih*0.8:iw*0.1:ih*0.2", frame], job_dir, "thumbnail frame")
        img = TH._cover(Image.open(frame))
        img = TH._text_block(TH._shade(img, side), text, side) if i < 3 else TH._text_block(img, text, "left", band=True)
        p = job_dir / f"thumb_{i}.jpg"
        img.save(p, quality=92)
        out.append(p.name)
    _log(job_dir, f"thumbnails: {', '.join(out)} (frames of the animation)")
    return out
