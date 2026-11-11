"""
assemble.py  -  script.md (parsed) -> draft.mp4 or final.mp4

  1 voice     Kokoro per segment (cached) -> one voice track with exact timings
  2 visuals   one clip per shot, cut exactly where its narration starts (AI images one at a time,
              graphics and encodes in parallel)
  3 join      clips -> video.mp4 (no re-encode)
  4 captions  word-by-word .ass from Kokoro word timings
  5 audio     voice + ducked music + sound effects -> loudness normalised to -14 LUFS
  6 encode    burn captions (bundled font), auto-detected encoder (videotoolbox / nvenc / libx264)

Video type (type: full | short, config.TYPES) sets the captions, the safe area, the music and the ending.
"""

import json
import random
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import soundfile as sf

from . import config as C
from . import captions, encoder, visuals, voice
from .util import PipelineError, SfxPicker, best_match, best_matches, fmt_ts, log, media_duration, music_files, run, sfx_files

SR = voice.SR


def _timeline(parsed, job_dir, progress):
    segs = parsed["segments"]
    meta = parsed["meta"]
    t, out = 0.0, []
    for k, seg in enumerate(segs):
        progress("voice", k, len(segs))
        wav, dur, words = voice.synth(seg["text"], meta["voice"], meta["speed"], job_dir)
        if k > 0:
            t += C.GAP_AFTER_PARAGRAPH if seg["new_paragraph"] else C.GAP_IN_PARAGRAPH
        t += seg["pause_before"]
        out.append({"start": t, "dur": dur, "wav": wav, "words": words})
        t += dur
    progress("voice", len(segs), len(segs))
    tail = C.TYPES[meta.get("type", "full")]["tail_sec"]   # full: a little air; Short: tight, so it loops
    return out, t + tail


def _voice_track(tl, total, job_dir):
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for s in tl:
        a, sr = sf.read(s["wav"], dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        i = int(s["start"] * SR)
        track[i:i + len(a)] += a[: max(0, len(track) - i)]
    path = job_dir / "work" / "voice.wav"
    sf.write(path, track[: int(total * SR)], SR)
    return path


def _shot_spans(parsed, tl, total):
    """Each shot runs from just before its first words until the next shot starts."""
    starts = []
    for k, sh in enumerate(parsed["shots"]):
        seg_i = sh.get("first_segment", 0)
        starts.append(0.0 if k == 0 else max(0.0, tl[seg_i]["start"] - 0.06))
    spans = []
    for k, st in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else total
        spans.append((st, max(0.2, end - st)))
    return spans


def music_tracks(meta, rng):
    """music: one name, or several separated by commas (full videos: one per chapter, in order, repeating)."""
    if meta.get("music_off"):                        # music: none
        return []
    files = music_files(60)
    if C.BGM_FILE and (C.BGM_DIR / C.BGM_FILE).exists():
        return [C.BGM_DIR / C.BGM_FILE]
    names = [n.strip() for n in (meta.get("music") or "").split(",") if n.strip()] or [""]
    out = []
    stale = meta.get("music_stale")                  # motion graphics: tracks of the last videos go last
    for n in names:
        if stale:
            cands = best_matches(n, files) or ([] if n else sorted(files))
            fresh = [c for c in cands if c.name not in stale and c not in out] or cands
            f = rng.choice(sorted(fresh)) if fresh else best_match(n, files, fallback_random=True, rng=rng)
        else:
            f = best_match(n, files, fallback_random=True, rng=rng)
        if f and f not in out:
            out.append(f)
    return out


def loudnorm(src: Path, dst: Path, job_dir: Path):
    """Two-pass linear loudness normalisation to TARGET_LUFS (YouTube plays at about -14). Returns input LUFS."""
    p = run(["ffmpeg", "-hide_banner", "-i", src, "-af",
             f"loudnorm=I={C.TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
            job_dir, "loudness measure")
    err = p.stderr.decode(errors="replace")
    m = json.loads(err[err.rfind("{"): err.rfind("}") + 1])
    run(["ffmpeg", "-y", "-i", src, "-af",
         f"loudnorm=I={C.TARGET_LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
         f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
         f"linear=true,aresample=48000", "-c:a", "pcm_s16le", dst], job_dir, "loudness normalise")
    return float(m["input_i"])


def _mix_audio(parsed, tl, total, voice_wav, job_dir, warnings, rng):
    work = job_dir / "work"
    P = C.TYPES[parsed["meta"].get("type", "full")]
    tracks = music_tracks(parsed["meta"], rng)
    bgm = tracks[0] if tracks else None
    sfx_all = sfx_files()
    inputs = ["-i", voice_wav]
    fc = ["[0:a]aresample=48000,aformat=channel_layouts=mono,asplit=2[voice][key]"]
    mix = ["[voice]"]
    k = 1
    fade_out = P["music_fade_out"]
    # music pieces: [(start, end, track)]. Full videos with several tracks change track at each chapter.
    pieces = [(0.0, total, bgm)] if bgm else []
    starts = sorted({0.0 if c["segment"] == 0 else tl[c["segment"]]["start"]
                     for c in parsed["chapters"] if c["segment"] < len(tl)})
    if bgm and P["chapters"] and len(tracks) > 1 and len(starts) > 1:
        starts[0] = 0.0
        bounds = starts + [total]
        pieces = [(bounds[i], bounds[i + 1], tracks[i % len(tracks)]) for i in range(len(starts))]
    XF = 3.0   # crossfade at a chapter change
    if pieces:
        labels = []
        for i, (a, b, f) in enumerate(pieces):
            last = i == len(pieces) - 1
            ln = (b - a) + (0 if last else XF)
            fin = "afade=t=in:d=1.5" if i == 0 else f"afade=t=in:d={XF}"
            fout = f"afade=t=out:st={max(0, ln - fade_out):.3f}:d={fade_out}" if last else \
                f"afade=t=out:st={max(0, ln - XF):.3f}:d={XF}"
            ms = int(a * 1000)
            inputs += ["-stream_loop", "-1", "-i", f]
            fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{ln:.3f},asetpts=PTS-STARTPTS,"
                      f"{fin},{fout},adelay={ms}|{ms}[m{i}]")
            labels.append(f"[m{i}]")
            k += 1
        if len(labels) > 1:
            fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
                      f"volume={C.BGM_VOLUME},atrim=0:{total:.3f}[bgmraw]")
        else:
            fc.append(f"[m0]volume={C.BGM_VOLUME},atrim=0:{total:.3f}[bgmraw]")
        fc.append("[bgmraw][key]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[bgm]")
        mix.append("[bgm]")
    else:
        fc[0] = "[0:a]aresample=48000,aformat=channel_layouts=mono[voice]"
        if not parsed["meta"].get("music_off"):
            warnings.append("no music files (>= 60 s) in assets/library/music or assets/audio/bgm")
    used = []
    picker = SfxPicker(sfx_all, rng, parsed.get("sfx_stale"))   # each file of a kind in turn (no file 3x in a row)
    for seg, s in zip(parsed["segments"], tl):
        for cue in seg["sfx"]:
            f = picker.pick(cue)
            if not f:
                continue
            ms = int(max(0, s["start"] - 0.15) * 1000)
            inputs += ["-i", f]
            fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{C.SFX_MAX_SEC},"
                      f"afade=t=out:st={max(0.0, C.SFX_MAX_SEC - 0.5)}:d=0.5,volume={C.SFX_VOLUME},"
                      f"adelay={ms}|{ms}[s{k}]")
            mix.append(f"[s{k}]")
            used.append(f"{cue} -> {f.name}")
            k += 1
        for a in seg.get("sfx_auto") or []:              # sfx: auto (pipeline/sfx.py)
            f = picker.pick(a["kind"])
            if not f:
                continue
            ms = int(max(0, s["start"] - a["lead"]) * 1000)
            inputs += ["-i", f]
            fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{C.SFX_MAX_SEC},"
                      f"afade=t=out:st={max(0.0, C.SFX_MAX_SEC - 0.5)}:d=0.5,volume={C.SFX_VOLUME * a['gain']:.3f},"
                      f"adelay={ms}|{ms}[s{k}]")
            mix.append(f"[s{k}]")
            used.append(f"auto {a['kind']} -> {f.name}")
            k += 1
    for a in parsed.get("sfx_timed") or []:              # the motion renderer: cues at exact animation moments
        f = picker.pick(a["kind"])
        if not f:
            continue
        ms = int(max(0, a["t"]) * 1000)
        inputs += ["-i", f]
        lim = f",alimiter=limit={a['limit']:.4f}:attack=1:release=60:level=false" if a.get("limit") else ""
        fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{C.SFX_MAX_SEC},"
                  f"afade=t=out:st={max(0.0, C.SFX_MAX_SEC - 0.5)}:d=0.5,volume={C.SFX_VOLUME * a['gain']:.3f}{lim},"
                  f"adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]")
        used.append(f"{a['t']:.1f}s {a['kind']} -> {f.name}")
        k += 1
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,"
              f"aformat=channel_layouts=stereo[aout]")
    mixed = work / "mix.wav"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[aout]", "-t", f"{total:.3f}",
         "-c:a", "pcm_s16le", mixed], job_dir, "audio mix")
    norm = work / "mix_norm.wav"
    loud_in = loudnorm(mixed, norm, job_dir)
    music = [{"start": round(a, 2), "track": f.name} for a, b, f in pieces]
    return norm, bgm, used, loud_in, music


def join_clips(clips, video: Path, job_dir: Path):
    lst = video.parent / "clips.txt"
    # forward slashes: FFmpeg's concat list reads the same on Windows and macOS
    lst.write_text("".join(f"file '{Path(c).resolve().as_posix()}'\n" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], job_dir, "join clips")


def final_encode(video: Path, audio: Path, ass: Path, out: Path, mode: str, total: float, job_dir: Path):
    """Burn the captions (bundled font) and mux the audio. Runs inside job_dir so every path in the filter is
    relative (no drive letters or colons to escape on Windows)."""
    import os
    fonts = Path(os.path.relpath(C.FONTS_DIR, job_dir)).as_posix()
    sub = Path(os.path.relpath(ass, job_dir)).as_posix()
    run(["ffmpeg", "-y", "-i", video, "-i", audio, "-vf", f"ass={sub}:fontsdir={fonts}", "-map", "0:v", "-map", "1:a",
         *encoder.args(C.VIDEO_BITRATE[mode], final=True), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", out.name], job_dir, "final encode",
        cwd=job_dir)


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    """mode = 'draft' (fast check, AI images as placeholders) or 'final' (upload quality)."""
    t_start = time.time()
    job_dir = Path(job_dir).resolve()
    meta = parsed["meta"]
    W, H = C.SIZES[(meta["format"], mode)]
    work = job_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    rng = random.Random(meta.get("title", ""))   # same music choice in draft and final
    warnings = []
    log(job_dir, f"=== {mode.upper()} render: '{meta.get('title')}'  {len(parsed['segments'])} segments, "
                 f"{len(parsed['shots'])} shots, {W}x{H}")

    stages, t_stage = {}, time.time()        # per-stage seconds, shown on the job page (timing only)

    def lap(name):
        nonlocal t_stage
        stages[name] = round(time.time() - t_stage, 1)
        t_stage = time.time()

    # 1 voice + timeline
    tl, total = _timeline(parsed, job_dir, progress)
    P = C.TYPES[meta.get("type", "full")]
    if P["max_sec"] and total > P["max_sec"]:
        raise PipelineError(f"the voice is {fmt_ts(total)} long, over the {fmt_ts(P['max_sec'])} limit for a "
                            f"{P['label']}; cut some lines")
    voice_wav = _voice_track(tl, total, job_dir)
    log(job_dir, f"voice done: {fmt_ts(total)} ({total:.1f} s) in {time.time() - t_start:.0f}s")
    lap("voice")

    # 2 visuals
    spans = _shot_spans(parsed, tl, total)
    all_words = [[wd[0], s["start"] + wd[1], s["start"] + wd[2], wd[3] if len(wd) > 3 else ""]
                 for s in tl for wd in s["words"]]
    char = meta.get("character_data")
    clips = [None] * len(spans)
    order = list(range(len(spans)))
    done = 0
    progress("visuals", 0, len(spans))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(visuals.make_shot, parsed["shots"][i], i, spans[i][1], W, H, job_dir, mode,
                            warnings, {"character": char, "words": all_words, "t0": spans[i][0],
                                       "safe": P.get("safe"),
                                       "art_style": meta["presets"]["art_style"]}): i for i in order}
        for f in as_completed(futs):
            clips[futs[f]] = f.result()
            done += 1
            progress("visuals", done, len(spans))
    log(job_dir, f"visuals done ({len(spans)} shots) at {time.time() - t_start:.0f}s")

    # 3 join
    video = work / "video.mp4"
    join_clips(clips, video, job_dir)
    lap("visuals")

    # 4 captions
    progress("captions")
    words = []
    for si, s in enumerate(tl):
        for wd in s["words"]:
            words.append([wd[0], s["start"] + wd[1], s["start"] + wd[2], si])
    ass = job_dir / f"captions_{mode}.ass"
    captions.write_ass(words, W, H, ass, total, style=P["captions"], preset=meta["presets"]["captions"])
    captions.write_srt(words, job_dir / f"captions_{mode}.srt")
    lap("captions")

    # 5 audio
    progress("audio mix")
    norm, bgm, sfx_used, loud_in, music = _mix_audio(parsed, tl, total, voice_wav, job_dir, warnings, rng)
    lap("audio mix")

    # 6 encode
    progress("encoding")
    out = job_dir / f"{mode}.mp4"
    final_encode(video, norm, ass, out, mode, total, job_dir)
    dur = media_duration(out)
    lap("encode")

    chapters = []
    for c in parsed["chapters"]:
        if c["segment"] < len(tl):
            chapters.append({"title": c["title"], "start": 0.0 if c["segment"] == 0 else tl[c["segment"]]["start"]})
    timings = [{"shot": i, "type": parsed["shots"][i]["type"], "start": round(st, 2), "dur": round(d, 2)}
               for i, (st, d) in enumerate(spans)]
    (job_dir / f"timeline_{mode}.json").write_text(json.dumps(
        {"segments": [{"start": s["start"], "dur": s["dur"]} for s in tl], "shots": timings}, indent=1), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)   # cache/ (voice, stock, AI images) is kept for the next render
    secs = time.time() - t_start
    log(job_dir, f"DONE {out.name}: {fmt_ts(dur)}, {out.stat().st_size / 1e6:.1f} MB, rendered in {secs:.0f}s")
    return {"mode": mode, "file": out.name, "duration_sec": round(dur, 1), "size_mb": round(out.stat().st_size / 1e6, 1),
            "render_seconds": round(secs), "width": W, "height": H, "bgm": bgm.name if bgm else None,
            "sfx_used": sfx_used, "chapters": chapters, "warnings": warnings, "music": music,
            "type": meta.get("type", "full"), "encoder": encoder.name(),
            "loudness_before": loud_in, "loudness_target": C.TARGET_LUFS, "stages": stages, "style": "classic"}
