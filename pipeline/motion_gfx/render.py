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
from . import planner as PL
from . import formats as Fm
from . import design as D
from . import templates as T
from . import typography as TY
from . import storyboard as SB

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


def render(parsed: dict, job_dir: Path, mode: str, progress, regen: dict = None) -> dict:
    """mode: draft | final | storyboard (voice + scenes only: builds the project and the storyboard, no render).
    regen (storyboard mode): {"sid", "what": scene | layout | icon, "type", "query", "note"} = make another version
    of that one scene and leave it waiting for accept / reject (storyboard.py)."""
    t_start = time.time()
    job_dir = Path(job_dir).resolve()
    meta = parsed["meta"]
    log = lambda m: _log(job_dir, m)
    # module settings the last render left behind (fonts, typography, easing) are read by the look / format choice and
    # the beat split before this video sets its own: start every render from the import-time values, so the same
    # script makes the same project in a fresh server and after other renders (picture reuse depends on it)
    T.reset_look()
    TY.set_style("classic")
    Fm.apply_motion({})
    tools = hf.check_installed()
    fmt = meta["format"]
    W, H = C.SIZES[(fmt, "final")]
    OW, OH = C.SIZES[(fmt, "draft" if mode == "storyboard" else mode)]
    P = C.TYPES[meta.get("type", "full")]
    project = job_dir / "motion"
    work = job_dir / "work"
    crit_mode = (meta.get("critique") or "auto").strip().lower()
    reuse = None if mode == "storyboard" else \
        _reuse_candidate(project, work, mode, OW, OH, crit_mode)       # a finished picture of a failed render
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    warnings = []
    title = meta.get("title", "")
    log(f"=== {mode.upper()} render (motion graphics): '{title}'  {len(parsed['shots'])} shots, {W}x{H} -> {OW}x{OH}, "
        f"HyperFrames {tools['hyperframes']}, Node {tools['node']}, encoder {encoder.name()}")

    # 0 reserve this video's look in data/asset_history.json before anything else (videos queued or rendered at the
    #   same time then never share a look; docs/VARIETY_PLAN.md section 6)
    look = history.reserve(meta, title, job_dir.name, picker.estimate_beats(parsed))
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
    seed = int(hashlib.sha1(title.encode()).hexdigest()[:6], 16)
    beats = PL.rhythm(B.split(parsed, tl, spans), seed)          # bursts + breathers (docs/VARIETY_PLAN.md 5.4)
    T.set_look(look["fonts"])
    TY.set_style(look.get("typography", "classic"))
    show = Fm.get(look.get("format"))                            # the video's format (docs/VARIETY_PLAN.md 3)
    Fm.apply_motion(show)
    fseed = Fm.seed_of(title, look.get("format"))                # same script in another format = other choices
    order = D.palette_order(len(beats), fseed, D.PALETTE_SETS[look["palette"]])
    board = SB.Board(job_dir, W, H, log)
    seen = board.seen(history.recent(title), mode == "storyboard")      # frozen once the storyboard is in use
    log(f"  format: {show['label']}; look: icons {look['icons']}, palette {look['palette']}, fonts {look['fonts']}, {look['icon_style']} icons "
        f"(last videos: {len(seen['looks'])}); typography {TY.STYLE['label']} ({TY.STYLE['id']})")
    shutil.rmtree(project / "compositions", ignore_errors=True)
    compose.prepare(project, voice_wav)
    cues = []
    plan_meta = dict(meta, look_icons=look["icons"], format_weights=show["weights"], format_banned=show["banned"])
    sids = SB.scene_ids(beats)
    # the video's names, before anything is planned or built (picker.plan sets them too, but only midway: the first
    # plan of a process and every build from a stored plan would see the previous video's names)
    picker.set_names(beats)
    used_tpl, variants, info, plan = board.plan(
        [sids, [round(b["dur"], 2) for b in beats], look, fseed, {k: meta.get(k) for k in (
            "icons", "icons_pin", "icons_ban", "icon_reuse", "scene_order", "format", "type")}],
        lambda: picker.plan_video(beats, plan_meta, seen, fseed), mode == "storyboard")
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
    trans = PL.transitions(beats, used_tpl, fseed, show["transitions"], show["signature"], meta.get("transitions"))
    ents = PL.entrances(used_tpl, fseed, show["entrances"])
    cams = PL.cameras(beats, used_tpl, fseed, show.get("cameras"), meta.get("camera"))
    for i, sid in enumerate(sids):         # the storyboard's per-scene options (storyboard.save_opts) win over the plan
        o = SB.opts_of(board.state, sid)
        trans[i] = o.get("transition", trans[i]) if i else trans[i]
        ents[i], cams[i] = o.get("entrance", ents[i]), o.get("camera", cams[i])
        if "palette" in o:
            order[i] = next((k for k, p in enumerate(D.PALETTES) if p["name"] == o["palette"]), order[i])
        if o.get("template") == used_tpl[i] and "layout" in o:
            variants[i] = o["layout"]
    from . import transitions as Tr
    for i, b in enumerate(beats):          # overlap per transition (3D / film ones are longer), never > 45 % of a scene
        k = trans[i]
        b["ov"] = 0.0 if k == "cut" or i == 0 else round(min(Tr.overlap(k, D.TRANSITION), 0.45 * b["dur"],
                                                             0.45 * beats[i - 1]["dur"]), 3)
    built = {}
    vocab = []                                                   # content words of the video (the word wheel)
    for b in beats:
        for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", b["text"]):
            if w.lower() not in T.STOP and w.lower() not in T.WEAK and w.lower() not in {x.lower() for x in vocab}:
                vocab.append(w)
    n_text, chapter_now = 0, ""
    case_of = TY.case_map([b["text"] for b in beats] + [json.dumps(sh, ensure_ascii=False) for sh in parsed["shots"]])
    nt_at, chapter_at = {}, {}
    TEXT_TYPES = ("kinetic", "title", "figure", "chapter", "memo")

    def make(i, name, variant, inf, ic):
        """Builds scene i as one scene type + layout (the planned one, or another one for a regeneration)."""
        b = beats[i]
        pal = D.PALETTES[order[i]]
        ctx = {"W": W, "H": H, "fmt": fmt, "pal": pal, "dur": b["dur"], "shot": parsed["shots"][b["shot"]],
               "rnd": random.Random(seed + i), "icons": ic,
               "look": look, "variant": variant % PL.own_of(name), "years": video_years,
               "kicker": show["kicker"], "plain": show.get("ambient", True) is False, **inf}
        if name in TEXT_TYPES or b.get("chapter_card"):
            ctx["ty_entrance"] = SB.opts_of(board.state, sids[i]).get("text_entrance") or TY.entrance_for(nt_at[i], fseed)
        if vocab:
            r0 = (fseed + 7 * i) % len(vocab)
            ctx["ty_alts"] = [vocab[(r0 + 5 * k) % len(vocab)] for k in range(4)]
        ctx["ty_case"] = case_of
        P_ = compose.host(i) + "-"
        parts = Fm.restyle(T.build(name, P_, b, ctx), show)
        parts = TY.apply(parts, P_, pal, ctx, T.HEAD, i, len(beats), chapter_at[i] or title, show)
        return {"parts": parts, "pal": pal, "template": name, "variant": variant, "frame": b.get("frame"),
                "icons": [x["id"] for _s, x in sorted(ic.items())]}

    for i, b in enumerate(beats):
        b["transition"] = trans[i]
        b["entrance"] = ents[i]
        b["camera"] = cams[i]
        b["seed"] = fseed
        b["exit"] = trans[i + 1] if i + 1 < len(beats) else None
        b["exit_ov"] = beats[i + 1]["ov"] if i + 1 < len(beats) else 0.0
        b["frame"] = PL.frame_of(used_tpl[i], fseed, variants[i]) if show.get("frames", True) else None
        name = used_tpl[i]
        nt_at[i] = n_text
        if name in TEXT_TYPES or b.get("chapter_card"):
            n_text += 1
        chapter_now = b.get("chapter") or chapter_now
        chapter_at[i] = chapter_now
        # the storyboard: the user's version of this scene (if any) + manual edits, else the scene as generated
        parts, pal, name, variants[i] = board.resolve(i, sids[i], compose.host(i), b,
                                                      make(i, name, variants[i], info[i], icons.get(i, {})))
        used_tpl[i] = name
        built[i] = (parts, pal)
        (project / "compositions" / f"scene_{i + 1:03d}.html").write_text(
            compose.scene_file(i, b, parts, pal, b["ov"], W, H, show), encoding="utf-8")
        o = SB.opts_of(board.state, sids[i])
        for t, kind in (parts["cues"] if o.get("scene_sfx", True) else []):
            cues.append((b["start"] + t, show["sfx"].get(kind, kind)))
        if b["transition"] != "cut" and o.get("cut_sfx", True):
            cues.append((b["start"] - b["ov"] * 0.6, dict({"push": "swipe", "slide": "swipe", "push_up": "swoosh-up", "glitch": "glitch",
                                                  "flash": "impact", "fade": "swipe", "page": "paper"}, **Tr.SFX).get(b["transition"], "whoosh")))
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
        [dict({k: b[k] for k in ("shot", "kind", "index", "start", "end", "template", "transition", "camera", "text")},
              variant=b["variant"], icons=[x["id"] for _s, x in sorted(icons.get(i, {}).items())]) for i, b in enumerate(beats)],
        indent=1), encoding="utf-8")
    counts = {n: used_tpl.count(n) for n in sorted(set(used_tpl))}
    log(f"  {len(beats)} scenes (one every {total / max(1, len(beats)):.1f} s): " +
        ", ".join(f"{n} {c}" for n, c in counts.items()))
    vrep = V.report(used_tpl, [b["variant"] for b in beats], [b["transition"] for b in beats], beats,
                    seen.get("videos"), look, cams)
    log("  " + V.log_line(vrep))
    for i, r in enumerate(board.rows):     # what the cut / camera / palette of each scene are (the page shows them)
        r.update(transition=beats[i]["transition"], camera=beats[i]["camera"], entrance=beats[i]["entrance"],
                 palette=built[i][1].get("name"), sfx=len(built[i][0]["cues"]))
    board.finish([chapter_at[i] for i in range(len(beats))])
    SB.write_options(job_dir, fseed, [D.PALETTES[k]["name"] for k in sorted(set(order))])
    if regen:
        _regenerate(regen, board, beats, sids, make, plan_meta, seen, fseed, variants, info, icons, show, project, W, H, log)
    if mode == "storyboard":                                 # scenes only: the Storyboard page takes it from here
        history.finish_draft(title, V.fingerprint(vrep, look))
        shutil.rmtree(work, ignore_errors=True)
        log(f"STORYBOARD ready: {len(beats)} scenes in {time.time() - t_start:.0f}s")
        return {"mode": "storyboard", "scenes": len(beats), "duration_sec": round(total, 1),
                "render_seconds": round(time.time() - t_start), "templates": counts, "look": look}
    fp = _fingerprint(project)                       # the whole picture's input (script + look), before the critique
    video = work / "video.mp4"
    crit = None
    if reuse and reuse["fp"] == (_fingerprint(project, reuse["skip"]) if reuse["skip"] else fp) \
            and abs(reuse["duration"] - total) <= 0.5:
        shutil.move(reuse["path"], video)
        crit = _critique_summary(project)
        log(f"  picture reused: {reuse['why']}, {reuse['duration']:.1f} s at {OW}x{OH}: no HyperFrames render, "
            f"no critique")
        progress("checks", 1, 1)
    else:
        if reuse:
            reuse["path"].unlink(missing_ok=True)
            log("  a finished picture was found, but the script or look changed: rendering the picture again")
        crit = _picture(project, beats, built, W, H, OW, OH, show, mode, crit_mode, total, t_start, video, job_dir,
                        log, progress)
        (project / PICTURE).write_text(json.dumps({"mode": mode, "w": OW, "h": OH, "duration": media_duration(video),
                                                   "fp": fp, "critique": crit_mode}, indent=1), encoding="utf-8")
    return _finish(parsed, meta, tl, total, voice_wav, spans, beats, words, cap, chip, used_tpl, variants, plan,
                   icon_rep, counts, vrep, look, order, seen, cues, crit, video, work, project, P, OW, OH, mode, title,
                   warnings, t_start, job_dir, log, progress)


def _picture(project, beats, built, W, H, OW, OH, show, mode, crit_mode, total, t_start, video, job_dir, log, progress):
    """Steps 3-4: hyperframes check + snapshots, render, critique, (draft) scale -> work/video.mp4. Returns the
    critique summary."""
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
    if not _reuse_render(raw, beats, project, mode, total, job_dir, log):
        raw.unlink(missing_ok=True)
        code, out, err = hf.run(["render", "-o", raw, "--quality", QUALITY[mode], "--fps", C.FPS, "--workers",
                                 C.env("MOTION_WORKERS", "2"), "--quiet", "--strict"], project, log, f"{mode} render",
                                timeout=6 * 3600)
        if code != 0 or not raw.exists():
            raise PipelineError("HyperFrames render failed (motion/logs/hyperframes_render.log): " +
                                " | ".join((err or out).strip().splitlines()[-4:]))
    _write_sig(raw, project, mode)
    got = media_duration(raw)
    if abs(got - total) > 0.5:
        raise PipelineError(f"HyperFrames rendered {got:.1f} s but the video is {total:.1f} s long")
    log(f"  HyperFrames render: {got:.1f} s of video at {time.time() - t_start:.0f}s")
    crit = None
    if crit_mode != "off":                           # smooth-motion-studio step 5: watch every frame, fix, re-render
        progress("critique", 0, 1)
        raw, crit = _critique(raw, beats, built, project, W, H, show, mode, crit_mode, job_dir, log)
        log(f"  critique done at {time.time() - t_start:.0f}s")
    if (OW, OH) != (W, H):
        run(["ffmpeg", "-y", "-i", raw, "-an", "-vf", f"scale={OW}:{OH}:flags=lanczos", "-c:v", "libx264", "-preset",
             "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", video], job_dir, "draft scale")
    else:
        shutil.copy(raw, video)
    return crit


def _finish(parsed, meta, tl, total, voice_wav, spans, beats, words, cap, chip, used_tpl, variants, plan, icon_rep,
            counts, vrep, look, order, seen, cues, crit, video, work, project, P, OW, OH, mode, title, warnings, t_start,
            job_dir, log, progress):
    """Steps 5-6: captions, sound effects + music + -14 LUFS, final encode, history, result dict."""
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
                  beat_cuts=[b["start"] for b in beats[1:]],            # beat lock: the music starts on the cuts' grid
                  sfx_stale=set(seen["sfx"]), meta=dict(meta, music_stale=set(seen["music"])))
    rng = random.Random(title)
    norm, bgm, sfx_used, loud_in, music = assemble._mix_audio(parsed, tl, total, voice_wav, job_dir, warnings, rng)
    for bl in parsed.get("beat_lock") or []:
        log(f"  beat lock: {bl['track']} {bl['bpm']:.1f} BPM (grid fit {bl['grid_fit']:.0%}), starts {bl['offset']:.3f} s in: "
            f"cuts on the beat {bl['before']:.0%} -> {bl['after']:.0%}")
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
    (project / PICTURE).unlink(missing_ok=True)                  # the picture is in final.mp4 now
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
                       "variety": vrep, "critique": crit}}


PICTURE = "picture.json"   # motion/picture.json: what work/video.mp4 was made from (mode, size, fingerprint)


def _fingerprint(project: Path, skip=()) -> str:
    """Hash of everything the HyperFrames picture is made from (index.html, beats, icons, every scene file): the
    script, its voice timings and the look. skip = scene numbers (0-based) left out (scenes the critique rewrote)."""
    h = hashlib.sha256()
    files = [project / "index.html", project / "beats.json", project / "icons.json"] + \
        sorted((project / "compositions").glob("*.html"))
    for f in files:
        if f.parent.name == "compositions" and f.stem.startswith("scene_") and int(f.stem[6:]) - 1 in skip:
            continue
        h.update(f.relative_to(project).as_posix().encode() + b"\0")
        h.update(f.read_bytes() if f.exists() else b"<missing>")
    return h.hexdigest()


def _size(path: Path):
    import subprocess
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        w, h_ = p.stdout.strip().split(",")[:2]
        return int(w), int(h_)
    except ValueError:
        return None


def _reuse_candidate(project, work, mode, OW, OH, crit_mode):
    """A render that failed after its picture was finished left work/video.mp4. Keep it aside (motion/renders/
    reuse.mp4) with the fingerprint of what it was made from; render() uses it when the rebuilt project is the same.
    Renders from before motion/picture.json existed: the project files still on disk are the fingerprint, minus the
    scenes the critique rewrote (critique/report.json)."""
    v = work / "video.mp4"
    if not v.exists():                                      # set aside by a re-render that failed before using it
        v = project / "renders" / "reuse.mp4"
    if not v.exists() or _size(v) != (OW, OH):
        return None
    stamp, skip = project / PICTURE, []
    if stamp.exists():
        st = json.loads(stamp.read_text(encoding="utf-8"))
        if st.get("mode") != mode or st.get("critique") != crit_mode:
            return None
        fp, why = st["fp"], "same script and look as the last render"
    else:                                                   # older job: no stamp yet
        rep = project / "critique" / "report.json"
        if not (project / "renders" / f"{mode}.mp4").exists() or (crit_mode != "off") != rep.exists():
            return None
        if rep.exists():
            skip = json.loads(rep.read_text(encoding="utf-8")).get("fixed_scenes") or []
        fp, why = _fingerprint(project, skip), "same project files as the failed render"
    keep = project / "renders" / "reuse.mp4"
    keep.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(v, keep)
    return {"fp": fp, "skip": skip, "path": keep, "duration": media_duration(keep), "why": why}


def _critique_summary(project):
    rep = project / "critique" / "report.json"
    if not rep.exists():
        return None
    r = json.loads(rep.read_text(encoding="utf-8"))
    return {k: r.get(k) for k in ("mode", "passes", "first", "last", "fixed_scenes", "under", "pass_score")}


def _project_sig(project: Path, mode: str) -> dict:
    """What the picture is made of: the root page (timings, order) and every scene composition."""
    h = lambda p: hashlib.sha1(p.read_bytes()).hexdigest()  # noqa: E731
    comps = sorted((project / "compositions").glob("*.html"))
    return {"quality": QUALITY[mode], "fps": C.FPS, "index": h(project / "index.html"),
            "scenes": {p.name: h(p) for p in comps}}


def _write_sig(raw: Path, project: Path, mode: str) -> None:
    raw.with_suffix(".sig.json").write_text(json.dumps(_project_sig(project, mode)), encoding="utf-8")


def _reuse_render(raw: Path, beats, project: Path, mode: str, total: float, job_dir: Path, log) -> bool:
    """The storyboard workflow re-renders a video after a few scenes changed. When the last picture of this mode was
    made from the same root page, only the changed scenes' spans are rendered and spliced into it (the critique's
    frame-exact splice); with no change it is reused whole. False = render everything (also on any doubt)."""
    from . import critic as Cr
    sig_file = raw.with_suffix(".sig.json")
    try:
        old = json.loads(sig_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    now = _project_sig(project, mode)
    if not raw.exists() or any(old.get(k) != now[k] for k in ("quality", "fps", "index")) or \
            set(old.get("scenes") or {}) != set(now["scenes"]) or abs(media_duration(raw) - total) > 0.5:
        return False
    changed = sorted(int(re.search(r"scene_(\d+)", n).group(1)) - 1 for n, v in now["scenes"].items()
                     if n.startswith("scene_") and old["scenes"][n] != v)
    if any(old["scenes"][n] != v for n, v in now["scenes"].items() if not n.startswith("scene_")) or \
            len(changed) > max(1, int(0.4 * len(beats))):
        return False
    if not changed:
        log("  picture unchanged since the last render: reusing it (no HyperFrames render)")
        return True
    fps = float(C.FPS)
    rngs = Cr.spans([{"scene": k, "end": beats[k]["end"]} for k in changed], beats, fps, total)
    tmp = raw.parent / f"{mode}_partial"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    parts = []
    for k, (a, e, f0, f1) in enumerate(rngs):
        part = tmp / f"{k:02d}.mp4"
        code, _o, _e = hf.run(["render", "-o", part, "--quality", QUALITY[mode], "--fps", C.FPS, "--workers",
                               C.env("MOTION_WORKERS", "2"), "--start", f"{a:.4f}", "--end", f"{e:.4f}", "--quiet",
                               "--strict"], project, log, f"changed scenes {k + 1}/{len(rngs)}", timeout=3 * 3600)
        if code != 0 or not part.exists():
            log("  partial render failed; rendering the whole video")
            return False
        parts.append((f0, f1, part))
    spliced = tmp / "spliced.mp4"
    try:
        Cr.splice(raw, parts, fps, spliced, job_dir)
    except PipelineError:
        return False
    if abs(media_duration(spliced) - media_duration(raw)) > 1.5 / fps:
        log("  partial render changed the length; rendering the whole video")
        return False
    spliced.replace(raw)
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"  only scene(s) {', '.join(str(k + 1) for k in changed)} changed: re-rendered {len(rngs)} span(s), "
        f"{sum(f1 - f0 for _a, _e, f0, f1 in rngs)} of {int(total * fps)} frames, and spliced them in")
    return True


def _regenerate(regen, board, beats, sids, make, plan_meta, seen, fseed, variants, info, icons, show, project, W, H, log):
    """Another version of ONE scene (storyboard.py): the planner runs again with this scene's current type excluded
    (what: scene), or the same type gets its next layout (layout) / another picture (icon). Nothing else is touched:
    the result is stored as a pending version next to the current one."""
    from .. import icon_index as IX
    from . import planner as PL
    if regen["sid"] not in sids:
        raise PipelineError("that scene isn't in the storyboard any more (the script changed); open the storyboard again")
    i = sids.index(regen["sid"])
    b, hid, row = beats[i], compose.host(i), board.rows[i]
    what = regen.get("what") or "scene"
    cur = {"template": row["template"], "variant": row["variant"], "icons": row["icons"]}
    name, variant, inf, ic = cur["template"], cur["variant"], info[i], icons.get(i, {})
    tried = {v["template"] for v in row["versions"]} | {cur["template"]}
    ban = ", ".join(filter(None, [str(plan_meta.get("icons_ban") or "")] + cur["icons"]))
    if what == "scene":
        want = (regen.get("type") or "").strip().lower()
        excl = (set(PL.TYPES) - {want}) if want in PL.TYPES else tried
        names2, variants2, info2, plan2 = picker.plan_video(beats, dict(plan_meta, sb_exclude={i: excl}, icons_ban=ban),
                                                            seen, fseed)
        name, variant, inf = names2[i], variants2[i], info2[i]
        ic = {slot: dict(pk, uri=picker.data_uri(pk["id"]), sound=picker.sound_for(pk["id"]))
              for (bi, slot), pk in plan2["picks"].items() if bi == i}
    elif what == "layout":
        variant = (cur["variant"] + 1 + len([v for v in row["versions"] if v["template"] == name])) % max(1, PL.layouts_of(name))
    elif what == "icon" and not (regen.get("query") or "").strip():
        _n, _v, _i, plan2 = picker.plan_video(beats, dict(plan_meta, icons_ban=ban), seen, fseed)
        ic = {slot: dict(pk, uri=picker.data_uri(pk["id"]), sound=picker.sound_for(pk["id"]))
              for (bi, slot), pk in plan2["picks"].items() if bi == i} or ic
    q = (regen.get("query") or "").strip()
    if q and what in ("scene", "icon"):                      # the user's words -> the best icon of the library
        used = {x for r in board.rows for x in r["icons"]}
        fam = plan_meta.get("look_icons")
        hits = [h for h in IX.search(q, [fam] if fam else None, 12) if h["id"] not in used] or IX.search(q, None, 12)
        if hits:
            slot = min(ic) if ic else 0
            ic = {**ic, slot: {"id": hits[0]["id"], "score": hits[0]["score"], "how": "storyboard", "noun": q,
                               "uri": picker.data_uri(hits[0]["id"]), "sound": picker.sound_for(hits[0]["id"])}}
    keep_frame = b.get("frame")
    b["frame"] = PL.frame_of(name, fseed, variant) if show.get("frames", True) else None
    new = make(i, name, variant, inf, ic)
    html = compose.scene_file(i, b, new["parts"], new["pal"], b["ov"], W, H, show)
    b["frame"] = keep_frame
    st = board.state["scenes"].setdefault(regen["sid"], {"current": 0, "pending": None, "versions": [], "edits": {}})
    if st.get("pending") is not None:
        raise PipelineError("accept or reject the waiting version of this scene first")
    if not board.version(regen["sid"], row["current"]):      # keep what is there now (the generated original = v0)
        g = board.gen[i]
        b["frame"] = g["frame"]
        board.pin(i, regen["sid"], hid, row["current"], g,
                  compose.scene_file(i, b, g["parts"], g["pal"], b["ov"], W, H, show), "generated")
        b["frame"] = keep_frame
    n = max([v["n"] for v in st["versions"]] + [0]) + 1
    st = board.pin(i, regen["sid"], hid, n, new, html, "regenerated",
                   " / ".join(x for x in (what, regen.get("type"), q, regen.get("note")) if x))
    st["pending"] = n
    old_edit = st["edits"].get(str(row["current"]))
    if old_edit and old_edit.get("sig") == SB.sig_of(new["template"], new["variant"], new["frame"]):
        st["edits"][str(n)] = dict(old_edit)                  # same layout: text positions and styles carry over
    SB.save_state(board.job_dir, board.state)
    rows = SB.scenes(board.job_dir)
    rows[i].update(pending=n, versions=st["versions"])
    SB._write(SB.root(board.job_dir) / "scenes.json", rows)
    log(f"  storyboard: scene {i + 1} regenerated ({what}): {cur['template']}:{cur['variant']} -> {name}:{variant}, "
        f"icons {new['icons'] or '-'}; waiting as version {n}")


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


def _critique(raw, beats, built, project, W, H, show, mode, crit_mode, job_dir, log):
    """Score every scene (critic.py); scenes under 8 get a fix and only their spans are re-rendered and spliced in,
    up to critic.MAX_PASSES times (fixes escalate: the second pass gives a failing scene both fixes). Writes
    motion/critique/report.json + critique.png. critique: report = score only."""
    from . import critic as Cr
    out_dir = project / "critique"
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    t0 = time.time()
    fps, m = Cr.motion(raw)
    scenes = Cr.score(m, fps, beats)
    first = Cr.summary(scenes)
    log(f"  critique pass 1: {first['scenes']} scenes, mean {first['mean']}/10, lowest {first['min']}, "
        f"{first['under']} under {Cr.PASS_SCORE:g}, {first['dead_frames']} dead frames, {first['hitches']} hitches, "
        f"{first['jumps']} one-frame pops ({time.time() - t0:.0f} s)")
    passes, fixed = 1, set()
    total = len(m) / fps
    while crit_mode == "auto" and passes <= Cr.MAX_PASSES:
        bad = [s for s in scenes if s["score"] < Cr.PASS_SCORE and (s["fix"] or passes > 1)]
        if not bad:
            break
        for s in bad:
            b = beats[s["scene"]]
            want = set(s["fix"]) | ({"onset", "dead"} if passes > 1 else set())
            b["fix"] = sorted(set(b.get("fix") or []) | want)
            parts, pal = built[s["scene"]]
            (project / "compositions" / f"scene_{s['scene'] + 1:03d}.html").write_text(
                compose.scene_file(s["scene"], b, parts, pal, b["ov"], W, H, show), encoding="utf-8")
            fixed.add(s["scene"])
            log(f"    scene {s['scene'] + 1} ({b.get('template')}, {s['start']:.2f}-{s['end']:.2f} s) {s['score']}/10: "
                f"{'; '.join(s['notes']) or 'low score'} -> fix {', '.join(b['fix'])}")
        rngs = Cr.spans(bad, beats, fps, total)
        parts_out = []
        for k, (a, e, f0, f1) in enumerate(rngs):
            part = out_dir / f"pass{passes + 1}_{k:02d}.mp4"
            code, out, err = hf.run(["render", "-o", part, "--quality", QUALITY[mode], "--fps", C.FPS, "--workers",
                                     C.env("MOTION_WORKERS", "2"), "--start", f"{a:.4f}", "--end", f"{e:.4f}",
                                     "--quiet", "--strict"], project, log, f"critique re-render {k + 1}/{len(rngs)}",
                                    timeout=3 * 3600)
            if code != 0 or not part.exists():
                log(f"    re-render of {a:.2f}-{e:.2f} s failed; keeping the first render there")
                continue
            parts_out.append((f0, f1, part))
        if not parts_out:
            break
        spliced = out_dir / f"picture_pass{passes + 1}.mp4"
        Cr.splice(raw, parts_out, fps, spliced, job_dir)
        if abs(media_duration(spliced) - media_duration(raw)) > 1.5 / fps:
            log("    splice changed the length; keeping the first render")
            break
        raw = spliced
        passes += 1
        before = {s["scene"]: s["score"] for s in bad}
        fps, m = Cr.motion(raw)
        scenes = Cr.score(m, fps, beats)
        now = Cr.summary(scenes)
        gain = [next(x["score"] for x in scenes if x["scene"] == k) - v for k, v in before.items()]
        log(f"  critique pass {passes}: re-rendered {len(parts_out)} span(s) ({sum(f1 - f0 for f0, f1, _p in parts_out)} "
            f"frames), mean {now['mean']}/10, lowest {now['min']}, {now['under']} under {Cr.PASS_SCORE:g}, "
            f"{now['dead_frames']} dead frames")
        if gain and sum(gain) / len(gain) < 0.3:     # the fixes can't help these scenes (pauses built into the design)
            log(f"    fixes raised the re-rendered scenes by {sum(gain) / len(gain):+.2f} on average: no further passes")
            break
    last = Cr.summary(scenes)
    try:
        Cr.chart(m, fps, scenes, out_dir / "critique.png")
    except Exception as e:  # noqa: BLE001  (the chart is a picture for people; never lose a render over it)
        log(f"    critique chart failed: {e}")
    rep = {"mode": crit_mode, "passes": passes, "first": first, "last": last, "fixed_scenes": sorted(fixed),
           "pass_score": Cr.PASS_SCORE,
           "under": [{k: s[k] for k in ("scene", "start", "end", "score", "notes")} for s in scenes
                     if s["score"] < Cr.PASS_SCORE],
           "scenes": [{k: s[k] for k in ("scene", "start", "end", "score", "dead_frames", "onset_s", "hitches", "jumps")}
                      for s in scenes]}
    (out_dir / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return raw, {k: rep[k] for k in ("mode", "passes", "first", "last", "fixed_scenes", "under", "pass_score")}


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
