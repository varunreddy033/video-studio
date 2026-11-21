"""Check the web-series layer (pipeline/series, docs/SCRIPT_FORMAT.md section 9). Prints "series: clean" when:

  - every series in series/ loads without problems and every episode passes Check
  - docs/sample_series_script.md is the same file as series/sample-series/episodes/ep01.md (the Load-sample copy)
  - the episode Check rules fire: an unknown character and a too-long line, with their line numbers
  - every voice effect keeps a line's length within 0.5 s (word timings drive the mouths and captions)
  - a classic script still parses exactly as before (no series keys, no per-line voices)

    bin/python tools/check_series.py
"""

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import script_parser as P  # noqa: E402
from pipeline.series import bible, voicefx  # noqa: E402
from pipeline.util import media_duration  # noqa: E402

bad = []
for sid in bible.ids():
    s = bible.load(sid)
    bad += [f"series/{sid}/{f}:{ln}: {m}" for f, ln, m in s["problems"]]
    for e in s["episodes"]:
        r = P.parse((s["dir"] / "episodes" / e["file"]).read_text(encoding="utf-8"))
        bad += [f"{e['path']}:{x['line']}: {x['msg']}" for x in r["errors"]]
        if r["meta"]["rendering_method"] != "series" or r["meta"]["format"] != "landscape":
            bad.append(f"{e['path']}: should be a 16:9 series episode")
ep01 = ROOT / "series/sample-series/episodes/ep01.md"
sample = ROOT / "docs/sample_series_script.md"
if ep01.read_text(encoding="utf-8") != sample.read_text(encoding="utf-8"):
    bad.append("docs/sample_series_script.md differs from series/sample-series/episodes/ep01.md (copy it again)")
text = ep01.read_text(encoding="utf-8").replace("VEX (smug): The same", "MIRA (smug): The same", 1)
text = text.replace("KAI (nervous): Right. Cool.", "KAI (nervous): Right. Cool. " + "Very " * 30 + "cool.", 1)
msgs = {x["line"]: x["msg"] for x in P.parse(text)["errors"] + P.parse(text)["warnings"]}
if not any("MIRA isn't in this series' cast" in m for m in msgs.values()):
    bad.append("an unknown character (MIRA) wasn't reported")
if not any("words; people speak in short lines" in m for m in msgs.values()):
    bad.append("a too-long line wasn't reported")
# voice effects keep the timing
d = Path(tempfile.mkdtemp())
wav = d / "tone.wav"
import subprocess  # noqa: E402
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=220:d=2.5", "-ar", "24000", "-ac", "1", str(wav)], check=True)
for fx in voicefx.NAMES:
    got = media_duration(voicefx.apply(wav, fx, d))
    if abs(got - 2.5) > 0.5:
        bad.append(f"voice effect {fx} changes the length: 2.5 s -> {got:.2f} s")
shutil.rmtree(d, ignore_errors=True)
# a classic script: no per-line voice, nothing series-specific
r = P.parse((ROOT / "docs/sample_script.md").read_text(encoding="utf-8"))
if any("voice" in seg or "speaker" in seg for seg in r["segments"]) or r["meta"]["rendering_method"] == "series":
    bad.append("docs/sample_script.md picked up series fields")
for b in bad:
    print("PROBLEM", b)
print("series: clean" if not bad else f"series: {len(bad)} problem(s)")
sys.exit(1 if bad else 0)
