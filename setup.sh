#!/usr/bin/env bash
# One-time setup for the Mac render server. Safe to re-run.
# Usage:  bash ~/youtube-pipeline/setup.sh
set -euo pipefail
P="$HOME/youtube-pipeline"
PY="$P/bin/python"
cd "$P"

echo "== 1/5 Python venv"
if [ ! -x "$PY" ]; then python3.11 -m venv "$P"; fi
"$PY" -m pip install --upgrade pip -q
"$PY" -m pip install -q flask requests "kokoro>=0.9" soundfile numpy pillow matplotlib "mflux>=0.24"
# presenter characters: rembg (+ onnxruntime) cuts the character out of each pose (u2net, MIT);
# transformers runs Depth Anything V2 Small (Apache-2.0) for the 2.5D parallax; opencv does the parallax warp
"$PY" -m pip install -q "rembg>=2.0.50" onnxruntime "transformers>=4.45" opencv-python
echo "   ok: flask, requests, kokoro, soundfile, pillow, matplotlib, mflux, rembg, onnxruntime, transformers, opencv"

echo "== 2/5 System tools"
command -v ffmpeg >/dev/null || { brew install ffmpeg-full && brew link --force ffmpeg-full; }
command -v espeak-ng >/dev/null || brew install espeak-ng
command -v whisper-cli >/dev/null || brew install whisper-cpp
# No "grep -q" here: it exits early, ffmpeg gets SIGPIPE, and pipefail reports failure.
if ffmpeg -hide_banner -filters 2>/dev/null | grep -E '[[:space:]]subtitles[[:space:]]' >/dev/null; then
  echo "   ok: ffmpeg has the subtitles filter (captions will be burned in)"
else
  echo "   WARNING: your ffmpeg has no 'subtitles' filter -> captions can't be burned."
  echo "            Fix: brew uninstall ffmpeg && brew install ffmpeg-full   (then re-run this script)"
fi

echo "== 3/5 Whisper model"
mkdir -p "$P/models"
M="$P/models/ggml-small.bin"
if [ ! -s "$M" ] || [ "$(stat -f%z "$M")" -lt 400000000 ]; then
  echo "   downloading ggml-small.bin (~470 MB)..."
  curl -L --fail -o "$M" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
fi
echo "   ok: $(du -h "$M" | cut -f1) $M"

echo "== 4/5 Folders + .env"
mkdir -p "$P/assets/audio/bgm" "$P/assets/audio/sfx" "$P/output/jobs" "$P/docs"
if [ ! -f "$P/.env" ]; then
  cp "$P/.env.example" "$P/.env"
  TOKEN=$(openssl rand -hex 16)
  sed -i '' "s/^RENDER_TOKEN=.*/RENDER_TOKEN=$TOKEN/" "$P/.env"
  echo "   created .env"
  echo "   (no keys needed; HF_TOKEN in .env is optional)"
else
  echo "   .env already exists (not touched)"
fi
echo "   BGM files: $(ls "$P/assets/audio/bgm" | wc -l | tr -d ' ')   SFX files: $(ls "$P/assets/audio/sfx" | wc -l | tr -d ' ')"

echo "== 5/5 Kokoro warm-up (first run downloads the 82M model, ~1 min)"
"$PY" - <<'EOF'
from kokoro import KPipeline
import soundfile as sf, numpy as np, os
p = KPipeline(lang_code="a")
a = np.concatenate([x.numpy() if hasattr(x, "numpy") else x for _, _, x in p("Pipeline voice check.", voice="am_michael")])
out = os.path.expanduser("~/youtube-pipeline/output/voice_check.wav")
sf.write(out, a, 24000)
print("   ok: Kokoro works ->", out)
EOF

echo "== extra: image model (FLUX.2 klein 4B 4-bit, ~4.6 GB, one-time download, resumes if interrupted)"
HF_HUB_DISABLE_XET=1 "$PY" -c "from huggingface_hub import snapshot_download; snapshot_download('Runpod/FLUX.2-klein-4B-mflux-4bit', max_workers=4)" >/dev/null 2>&1 \
  && echo "   ok: image model present" || echo "   WARNING: image model download failed; re-run this script"
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -E 'h264_videotoolbox' >/dev/null; then
  echo "   ok: Mac hardware video encoder (h264_videotoolbox)"
else
  echo "   WARNING: ffmpeg has no h264_videotoolbox encoder"
fi

echo "== motion style: Node 22 + Remotion (versions pinned in motion/package.json + package-lock.json)"
command -v node >/dev/null || brew list node@22 >/dev/null 2>&1 || brew install node@22
NODE_BIN="$(brew --prefix node@22 2>/dev/null)/bin"
[ -x "$NODE_BIN/node" ] || NODE_BIN="$(dirname "$(command -v node)")"
( cd "$P/motion" && PATH="$NODE_BIN:$PATH" npm ci --no-audit --no-fund --loglevel=error ) \
  && echo "   ok: node $("$NODE_BIN/node" -v), remotion $(cd "$P/motion" && "$NODE_BIN/node" -p "require('remotion/package.json').version")" \
  || echo "   WARNING: npm ci in motion/ failed; re-run this script"
# Remotion's headless browser (one-time ~100 MB download, used to draw motion videos)
( cd "$P/motion" && PATH="$NODE_BIN:$PATH" npx remotion browser ensure >/dev/null 2>&1 ) \
  && echo "   ok: Remotion headless browser" || echo "   WARNING: Remotion browser download failed; re-run this script"

echo "== check: presenter + parallax libraries import"
"$PY" - <<'EOF'
import importlib, sys
bad = []
for mod in ("rembg", "onnxruntime", "transformers", "cv2", "torch", "kokoro", "mflux", "flask"):
    try:
        m = importlib.import_module(mod)
        print(f"   ok: {mod} {getattr(m, '__version__', '')}")
    except Exception as e:
        bad.append(mod)
        print(f"   FAILED: {mod}: {e}")
if not bad:
    from transformers import pipeline  # noqa: F401  (Depth Anything V2 Small loads through this on the first final)
    from rembg import new_session      # noqa: F401  (character cut-outs; u2net downloads on the first pack build)
sys.exit(1 if bad else 0)
EOF

echo "== extra: motion graphics renderer (rendering_method: motion; HyperFrames + GSAP, all local)"
NODE_MAJOR=$(node --version 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || echo 0)
if [ "${NODE_MAJOR:-0}" -lt 22 ]; then
  if command -v node >/dev/null; then brew upgrade node || brew install node; else brew install node; fi
fi
npm ci --no-fund --no-audit        # exactly the tested HyperFrames 0.9.26 + GSAP 3.15.1 (package-lock.json)
HF="$P/node_modules/.bin/hyperframes"
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1
"$HF" telemetry disable >/dev/null 2>&1 || true
"$HF" browser ensure >/dev/null 2>&1 && echo "   ok: HyperFrames $("$HF" --version), Node $(node --version), Chrome for rendering" \
  || echo "   WARNING: HyperFrames couldn't find or download Chrome; run: $HF browser ensure"

echo
echo "SETUP DONE. Start Video Studio with:"
echo "   $PY $P/render_server.py"
echo "then open http://localhost:8765"
