"""
motion_demo.py  -  phase 1 of docs/MOTION_PLAN.md: the 30-second hand-made look test.

    bin/python tools/motion_demo.py              voice + timings -> Remotion picture -> mix -> output/motion_demo.mp4
    bin/python tools/motion_demo.py --timing-only   only (re)write motion/src/demo/timing.json

1 voices the three demo scenes with Kokoro (bm_george, Sterling's voice) and writes their word timings to
  motion/src/demo/timing.json (the demo's scenes use them so every pop lands on its word)
2 renders the picture with Remotion (motion/, composition "Demo"), video only
3 mixes voice + ducked music (assets/audio/bgm, else assets/library/music) and normalises to -14 LUFS
4 muxes both into output/motion_demo.mp4 and prints how long each stage took
Narration facts are from scripts/ai_bubble_sterling.md (already checked).
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import assemble, voice  # noqa: E402
from pipeline import config as C  # noqa: E402
from pipeline.util import best_match, list_audio, run  # noqa: E402

FPS = 30
SCENES = [
    "There are four doors into your money. Your fund. Your pension. Your job. And your bills.",
    "Last Thursday, one of them slammed shut. The Nasdaq fell five and a half percent in a single day. "
    "Its worst day in nineteen months.",
    "So which door is next? And who is paying for all of this? Let's follow the money.",
]
LEAD, TAIL, GAP = 0.6, 2.2, 0.8          # silence before the first word, after the last, between scenes
TRANSITION = 0.6                          # seconds; the next scene's voice starts after the transition


def node_bin() -> str:
    for cand in (shutil.which("npx"), "/opt/homebrew/opt/node@22/bin/npx", "/usr/local/opt/node@22/bin/npx"):
        if cand and Path(cand).exists():
            return cand
    sys.exit("npx not found: install Node 22 (bash setup.sh does it)")


def main():
    t_all = time.time()
    work = ROOT / "output" / "motion_demo_work"
    work.mkdir(parents=True, exist_ok=True)
    (work / "cache").mkdir(exist_ok=True)
    times = {}

    # 1 voice + word timings, scene by scene, on one timeline
    t = time.time()
    scenes, clips, cursor = [], [], LEAD
    for i, text in enumerate(SCENES):
        wav, dur, words = voice.synth(text, "bm_george", 0.95, work)
        start = cursor
        scenes.append({"start": round(start, 3), "voiceDur": round(dur, 3),
                       "words": [{"w": w[0], "s": round(start + w[1], 3), "e": round(start + w[2], 3)} for w in words]})
        clips.append((wav, start))
        cursor = start + dur + (GAP + TRANSITION if i < len(SCENES) - 1 else TAIL)
    total = cursor
    # scene i lasts from its start (minus the incoming transition) to the next scene's start
    for i, sc in enumerate(scenes):
        begin = 0.0 if i == 0 else sc["start"] - TRANSITION
        end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
        sc["from"], sc["frames"] = round(begin * FPS), round((end - begin) * FPS)
    timing = {"fps": FPS, "total": round(total, 3), "transitionFrames": round(TRANSITION * FPS), "scenes": scenes}
    (ROOT / "motion" / "src" / "demo" / "timing.json").write_text(json.dumps(timing, indent=1), encoding="utf-8")
    times["voice"] = time.time() - t
    print(f"voice: {total:.1f} s of video, {sum(len(s['words']) for s in scenes)} words")
    if "--timing-only" in sys.argv:
        return

    # 2 picture (Remotion). Never while an image model is running: this script uses none.
    t = time.time()
    pic = work / "picture.mp4"
    p = subprocess.run([node_bin(), "remotion", "render", "src/index.ts", "Demo", str(pic), "--codec=h264",
                        "--crf=16", "--concurrency=4", "--log=error"], cwd=ROOT / "motion")
    if p.returncode != 0:
        sys.exit("Remotion render failed")
    times["picture (Remotion)"] = time.time() - t

    # 3 audio: voice track + ducked music, -14 LUFS
    t = time.time()
    import numpy as np
    import soundfile as sf
    sr = voice.SR
    track = np.zeros(int(total * sr) + sr, dtype=np.float32)
    for wav, start in clips:
        a, _ = sf.read(wav, dtype="float32")
        a = a.mean(axis=1) if a.ndim > 1 else a
        i = int(start * sr)
        track[i:i + len(a)] += a
    vwav = work / "voice.wav"
    sf.write(vwav, track[:int(total * sr)], sr)
    music = best_match("misdirection", list_audio(C.BGM_DIR, 60) or list_audio(C.ASSETS / "library" / "music", 60),
                       fallback_random=True)
    mixed = work / "mix.wav"
    if music:
        fc = (f"[0:a]aresample=48000,aformat=channel_layouts=mono,asplit=2[v][k];"
              f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={C.BGM_VOLUME},atrim=0:{total:.3f},"
              f"afade=t=in:d=1.0,afade=t=out:st={max(0, total - 2):.3f}:d=2[m];"
              f"[m][k]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[mb];"
              f"[v][mb]amix=inputs=2:duration=first:normalize=0,aformat=channel_layouts=stereo[a]")
        run(["ffmpeg", "-y", "-i", vwav, "-stream_loop", "-1", "-i", music, "-filter_complex", fc, "-map", "[a]",
             "-t", f"{total:.3f}", "-c:a", "pcm_s16le", mixed], work, "demo mix")
    else:
        run(["ffmpeg", "-y", "-i", vwav, "-ac", "2", "-ar", "48000", mixed], work, "demo mix")
    norm = work / "mix_norm.wav"
    lufs_in = assemble.loudnorm(mixed, norm, work)
    times["audio mix"] = time.time() - t

    # 4 mux (picture is already final quality: copy it)
    t = time.time()
    out = ROOT / "output" / "motion_demo.mp4"
    run(["ffmpeg", "-y", "-i", pic, "-i", norm, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], work, "mux")
    times["mux"] = time.time() - t
    print(f"music: {music.name if music else 'none'}; loudness in {lufs_in:.1f} LUFS -> {C.TARGET_LUFS}")
    for k, v in times.items():
        print(f"  {k:20s} {v:6.1f} s")
    print(f"DONE {out} ({total:.1f} s video) in {time.time() - t_all:.0f} s total")


if __name__ == "__main__":
    main()
