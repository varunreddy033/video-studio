"""Self-critique loop for motion graphics (smooth-motion-studio method, step 5).

After HyperFrames renders the picture, every frame is watched: a frame is DEAD when nothing on screen moves. Each
scene (cut to cut) gets a 0-10 score; scenes under PASS_SCORE get a fix (compose.life_js: "onset" = a spring settle
on the cut, "dead" = a breathing float for the whole scene), only their time spans are re-rendered with
`hyperframes render --start/--end` and spliced back into the picture, then everything is scored again.

  motion(video)                       per-frame motion (mean pixel change vs the previous frame, 0-255, 320 px grey)
  score(motion, fps, cuts, beats)     [{scene, start, end, score, dead_frames, longest_dead_s, onset_s, ..., fix}]
  chart(motion, fps, scenes, path)    critique.png: green moving / red dead frames, the score above each scene
  splice(raw, parts, fps, out, job_dir)  replace frame ranges of raw with re-rendered parts
"""
import json
import subprocess
from pathlib import Path

import numpy as np

DEAD = 0.08            # mean pixel change (0-255) below this = nothing moves
PASS_SCORE = 8.0
TAIL = 0.7             # seconds before the next cut that belong to its transition
MAX_PASSES = 2         # fix + re-render passes after the first render (3 passes in all)


def motion(video) -> tuple:
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                            "stream=width,height,r_frame_rate", "-of", "json", str(video)], capture_output=True, text=True)
    s = json.loads(probe.stdout)["streams"][0]
    num, den = map(float, s["r_frame_rate"].split("/"))
    w = 320
    h = int(round(s["height"] * w / s["width"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale={w}:{h},format=gray", "-f",
                          "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) if len(fr) > 1 else np.zeros(0)
    return num / den, np.concatenate([[d[0] if len(d) else 0.0], d])


def _scene(m, fps):
    body = m[2:] if len(m) > 4 else m
    dead = body < DEAD
    run = best = 0
    for x in dead:
        run = run + 1 if x else 0
        best = max(best, run)
    longest = best / fps
    moving = np.nonzero(m > DEAD)[0]
    onset = (moving[0] / fps) if len(moving) else len(m) / fps
    mv = m[m > DEAD]
    cv = float(np.std(mv) / (np.mean(mv) + 1e-6)) if len(mv) > 5 else 1.0
    hitches = sum(1 for i in range(1, len(m) - 1) if m[i] < DEAD * 0.5 and m[i - 1] > 3 * DEAD and m[i + 1] > 3 * DEAD)
    jumps = 0
    tail = int(round(TAIL * fps))
    for i in range(3, max(3, len(m) - tail) - 1):
        loc = float(np.median(m[max(0, i - 8):i + 8]))
        if m[i] > max(3.0, 5 * loc) and m[i - 1] < 2 * loc + 0.5 and m[i + 1] < 2 * loc + 0.5:
            jumps += 1
    share = float(dead.mean()) if len(dead) else 0.0
    s = 10 - 4 * share
    s -= 3 if longest > 2 else 2 if longest > 1 else 1 if longest > 0.5 else 0
    s -= 1 if onset > 0.25 else 0
    s -= 1 if cv < 0.15 else 0
    s -= min(2, hitches) + min(2, jumps)
    fix, notes = set(), []
    if share > 0.2 or longest > 0.5:
        fix.add("dead")
        notes.append(f"{int(dead.sum())} dead frames, nothing moves for {longest:.1f} s")
    if onset > 0.25:
        fix.add("onset")
        notes.append(f"first motion {onset:.2f} s after the cut")
    if cv < 0.15:
        fix.add("dead")
        notes.append("motion at one constant speed")
    if hitches:
        notes.append(f"{hitches} hitch(es)")
    if jumps:
        notes.append(f"{jumps} one-frame pop(s)")
    return {"score": round(max(0.0, min(10.0, s)), 1), "dead_frames": int(dead.sum()), "longest_dead_s": round(longest, 2),
            "onset_s": round(onset, 2), "motion_cv": round(cv, 2), "hitches": hitches, "jumps": jumps,
            "fix": sorted(fix), "notes": notes}


def score(m, fps, beats) -> list:
    """One entry per beat-scene (cuts = the beats' starts; the incoming transition's overlap before a cut belongs to
    the scene before it, so it is cut at the narration start like the cut point)."""
    total = len(m) / fps
    out = []
    for i, b in enumerate(beats):
        a = b["start"]
        e = beats[i + 1]["start"] if i + 1 < len(beats) else total
        f0, f1 = int(round(a * fps)), min(len(m), int(round(e * fps)))
        if f1 - f0 < 3:
            continue
        out.append(dict(_scene(m[f0:f1], fps), scene=i, start=round(a, 3), end=round(e, 3), f0=f0, f1=f1))
    return out


def summary(scenes) -> dict:
    if not scenes:
        return {"scenes": 0}
    sc = [s["score"] for s in scenes]
    return {"scenes": len(scenes), "mean": round(float(np.mean(sc)), 2), "min": min(sc),
            "under": sum(1 for x in sc if x < PASS_SCORE), "dead_frames": int(sum(s["dead_frames"] for s in scenes)),
            "hitches": int(sum(s["hitches"] for s in scenes)), "jumps": int(sum(s["jumps"] for s in scenes))}


def chart(m, fps, scenes, path, per_row=24):
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(Path(path).parent / ".mpl"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = max(1, -(-len(scenes) // per_row))
    fig, axes = plt.subplots(rows, per_row, figsize=(per_row * 0.9, rows * 1.6), sharey=True, squeeze=False)
    top = float(np.percentile(m, 98)) or 1.0
    for k, ax in enumerate(axes.flat):
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        if k >= len(scenes):
            continue
        s = scenes[k]
        seg = m[s["f0"]:s["f1"]]
        ax.bar(range(len(seg)), np.minimum(seg, top), width=1.0, color=["#2E9E5B" if v > DEAD else "#E0533D" for v in seg])
        ok = s["score"] >= PASS_SCORE
        ax.set_title(f"{s['score']:.0f}", fontsize=8, color="#2E9E5B" if ok else "#E0533D", fontweight="bold")
    fig.tight_layout(pad=0.3)
    fig.savefig(path, dpi=90)
    plt.close(fig)


def spans(scenes, beats, fps, total) -> list:
    """Time ranges to re-render for the failing scenes: from the scene's own transition start to its end, merged
    when they touch. Returned on whole frames: [(start_s, end_s, f0, f1)]."""
    rngs = []
    for s in scenes:
        b = beats[s["scene"]]
        a = max(0.0, b["start"] - b.get("ov", 0.0))
        e = s["end"]
        nb = beats[s["scene"] + 1] if s["scene"] + 1 < len(beats) else None
        if nb:                                     # include the next scene's transition (it shows this scene leaving)
            e = min(total, nb["start"])
        f0, f1 = int(np.floor(a * fps)), int(np.ceil(e * fps))
        if rngs and f0 <= rngs[-1][1] + 1:
            rngs[-1][1] = max(rngs[-1][1], f1)
        else:
            rngs.append([f0, f1])
    return [(f0 / fps, f1 / fps, f0, f1) for f0, f1 in rngs]


def splice(raw: Path, parts: list, fps: float, out: Path, job_dir: Path):
    """parts = [(f0, f1, part.mp4)] in frame order; frames [f0, f1) of raw are replaced by the part's first f1-f0
    frames. One re-encode at near-lossless quality (the final encode re-encodes anyway)."""
    from ..util import run
    inputs, fc, labels, cur = ["-i", str(raw)], [], [], 0
    n_split = len(parts) + 1
    fc.append(f"[0:v]split={n_split}" + "".join(f"[r{k}]" for k in range(n_split)))
    for k, (f0, f1, p) in enumerate(parts):
        inputs += ["-i", str(p)]
        fc.append(f"[r{k}]trim=start_frame={cur}:end_frame={f0},setpts=PTS-STARTPTS[a{k}]")
        fc.append(f"[{k + 1}:v]trim=end_frame={f1 - f0},setpts=PTS-STARTPTS,format=yuv420p[p{k}]")
        labels += [f"[a{k}]", f"[p{k}]"]
        cur = f1
    fc.append(f"[r{len(parts)}]trim=start_frame={cur},setpts=PTS-STARTPTS[z]")
    labels.append("[z]")
    fc.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0,fps={fps:g},format=yuv420p[v]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]", "-an", "-c:v", "libx264", "-preset",
         "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", str(out)], job_dir, "critique splice")
