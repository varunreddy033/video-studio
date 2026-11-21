"""All settings in one place. Values come from the project folder's .env (existing env vars win)."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


PORT = int(env("PORT", "8765"))                       # NOT 5000: macOS AirPlay Receiver uses it
HOST = env("HOST", "127.0.0.1")                       # this Mac only
RENDER_TOKEN = env("RENDER_TOKEN")

# images
LOCAL_IMAGE_MODEL = env("LOCAL_IMAGE_MODEL", "Runpod/FLUX.2-klein-4B-mflux-4bit")
LOCAL_IMAGE_BASE = env("LOCAL_IMAGE_BASE", "flux2-klein-4b")
LOCAL_IMAGE_STEPS = int(env("LOCAL_IMAGE_STEPS", "4"))
MFLUX_BIN = str(Path(sys.executable).parent / ("mflux-generate-flux2" + (".exe" if os.name == "nt" else "")))
# the local image model runs on Apple Silicon (MLX). Elsewhere, renders that only reuse cached images still work
# (clip Shorts, presenter Shorts with talk + graphics); a NEW AI image there stops with a clear message.
IMAGE_MODEL_AVAILABLE = sys.platform == "darwin" and Path(MFLUX_BIN).exists()
# words added to every [ai:]/[stock:] prompt in the doc_photo art style (presets/art_styles/doc_photo.json "suffix").
# Setting IMAGE_STYLE in .env still replaces it (old behaviour); other art styles use their own preset words.
IMAGE_STYLE_DEFAULT = "cinematic documentary photography, natural light, high detail, no text"
IMAGE_STYLE = env("IMAGE_STYLE", IMAGE_STYLE_DEFAULT)
SECONDS_PER_IMAGE = float(env("SECONDS_PER_IMAGE", "25"))   # measured on this M5 Air (12-28 s, depends on heat/RAM)
PARALLAX = env("PARALLAX", "on").lower() != "off"          # 2.5D depth camera moves on stills in finals
IMAGE_COOLDOWN = float(env("IMAGE_COOLDOWN", "8"))           # rest after each new image (fanless Mac, avoids throttling)

# voice
KOKORO_VOICE = env("KOKORO_VOICE", "am_michael")
KOKORO_SPEED = float(env("KOKORO_SPEED", "1.0"))
WHISPER_BIN = env("WHISPER_BIN", "whisper-cli")
_WHISPER_DEFAULT = str(BASE_DIR / "models" / "ggml-small.bin")
WHISPER_MODEL = os.path.expanduser(env("WHISPER_MODEL", _WHISPER_DEFAULT))
if not os.path.exists(WHISPER_MODEL) and os.path.exists(_WHISPER_DEFAULT):
    WHISPER_MODEL = _WHISPER_DEFAULT       # a .env written for another folder (old ~/youtube-pipeline path)

# mix
BGM_VOLUME = float(env("BGM_VOLUME", "0.18"))
SFX_VOLUME = float(env("SFX_VOLUME", "0.55"))
SFX_MAX_SEC = float(env("SFX_MAX_SEC", "2.5"))
BGM_FILE = env("BGM_FILE")
TARGET_LUFS = float(env("TARGET_LUFS", "-14"))
FPS = int(env("FPS", "30"))
# how the pictures are made (script header rendering_method:). motion = motion graphics (the default since
# 2026-11-11, .env DEFAULT_RENDERING_METHOD); ai_image = the original AI-image renderer. Scripts without the line
# that need AI images (character:, [talk:]/[act:], clip Shorts, style: motion) still get ai_image (script_parser).
RENDERING_METHODS = {"ai_image": "AI images", "motion": "Motion graphics", "blocky3d": "Blocky 3D",
                     "explainer3d": "3D explainer", "neon": "Neon motion", "series": "Web series"}
DEFAULT_RENDERING_METHOD = env("DEFAULT_RENDERING_METHOD", "motion").lower()
if DEFAULT_RENDERING_METHOD not in RENDERING_METHODS:
    DEFAULT_RENDERING_METHOD = "motion"
# Script kit per picture style (New video screen: "Prompt to give Claude" + "Load sample" follow the Pictures choice).
# prompts: kind (full | short) -> [(id, label)], id = docs/script_prompts/<id>.md, first = the one shown first;
# sample: kind -> docs/<file>. A kind that isn't listed falls back to "full". tools/check_script_kits.py checks that
# every style has both, the files exist and every sample passes Check with that style for both kinds.
SCRIPT_KITS = {
    "ai_image": {"prompts": {"full": [("ai_image", "No presenter"), ("ai_image_sterling", "Sterling presents")],
                             "short": [("ai_image_short", "No presenter"), ("ai_image_sterling_short", "Sterling Short")]},
                 "sample": {"full": "sample_script.md", "short": "sample_ai_image_short_script.md"}},
    "motion": {"prompts": {"full": [("motion", "Motion graphics")]},
               "sample": {"full": "sample_motion_gfx_script.md"}},
    "blocky3d": {"prompts": {"full": [("blocky3d", "Blocky 3D story")]},
                 "sample": {"full": "sample_blocky3d_script.md"}},
    "explainer3d": {"prompts": {"full": [("explainer3d", "3D explainer")]},
                    "sample": {"full": "sample_explainer3d_script.md"}},
    "neon": {"prompts": {"full": [("neon", "Neon motion")]},
             "sample": {"full": "sample_neon_script.md"}},
    # web series: the sample is series/sample-series/episodes/ep01.md (tools/check_series.py keeps the copy identical)
    "series": {"prompts": {"full": [("series", "Web series episode")]},
               "sample": {"full": "sample_series_script.md"}},
}
SCRIPT_PROMPTS_DIR = BASE_DIR / "docs" / "script_prompts"


def script_kit(method, kind="full"):
    """{prompts: [{id, label}], sample: file name} for one picture style and video kind (short | full)."""
    kit = SCRIPT_KITS[method]
    prompts = kit["prompts"].get(kind) or kit["prompts"]["full"]
    return {"prompts": [{"id": i, "label": l} for i, l in prompts],
            "sample": kit["sample"].get(kind) or kit["sample"]["full"]}
GAP_IN_PARAGRAPH = 0.12       # silence between voice segments of one paragraph (at a shot cut)
GAP_AFTER_PARAGRAPH = float(env("SCENE_PAD", "0.35"))
WORDS_PER_MIN = 155           # measured: Kokoro am_michael at speed 1.0

# paths
ASSETS = BASE_DIR / "assets"
BGM_DIR, SFX_DIR = ASSETS / "audio" / "bgm", ASSETS / "audio" / "sfx"
JOBS_DIR = BASE_DIR / "output" / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)
SHARED_IMAGE_CACHE = ASSETS / "cache" / "images"      # images reused across videos (character packs, [act:])
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
# asset library that IS in git (assets/library, uploaded through GitHub; see its README.md):
#   music/<mood>/<track>.mp3     the folder name is the mood (music: calm)
#   sfx/<kind>/<sound>.wav       the folder name is the kind ([sfx: whoosh]); starter_*.wav = generated starter pack
# The old local folders (assets/audio/bgm, assets/audio/sfx; not in git) keep working next to it.
LIBRARY = ASSETS / "library"
MUSIC_LIB, SFX_LIB = LIBRARY / "music", LIBRARY / "sfx"

# output sizes. draft = quick check (AI images replaced by labelled placeholders), final = upload quality
SIZES = {
    ("landscape", "final"): (1920, 1080), ("landscape", "draft"): (960, 540),
    ("vertical", "final"): (1080, 1920), ("vertical", "draft"): (540, 960),
}
VIDEO_BITRATE = {"final": "10M", "draft": "2500k"}
# style: motion (Remotion). Browser tabs rendering frames in parallel; 4 keeps the fanless Air cool enough.
MOTION_CONCURRENCY = int(env("MOTION_CONCURRENCY", "4"))
STYLES = ("classic", "motion")
PALETTES = ("navy", "light")              # motion/src/lib/theme.ts     # YouTube recommends ~8 Mbps for 1080p30

VIDEO_ENCODER = env("VIDEO_ENCODER")                   # empty = auto (videotoolbox / nvenc / libx264), see encoder.py

# video types (docs/VIDEO_TYPES.md). Check and render read their rules from here.
TYPES = {
    "full": {
        "label": "Full video", "format": "landscape",
        "hold_photo": 12, "hold_graphic": 10, "hold_talk": 25,   # warn when one picture stays longer (s)
        "min_sec": None, "max_sec": None, "plan_sec": (8 * 60, 16 * 60),   # outside plan = a warning only
        "chapters": True, "music": "per chapter, crossfaded", "tail_sec": 0.9, "music_fade_out": 3.0,
        "captions": "standard", "thumbnails": 3, "shorts_tag": False,
    },
    "short": {
        "label": "Short", "format": "vertical",
        "hold_photo": 6, "hold_graphic": 6, "hold_talk": 10,
        "min_sec": 15, "max_sec": 120, "plan_sec": (30, 120),     # YouTube allows 3:00; we stay under 2:00
        "chapters": False, "music": "one track", "tail_sec": 0.3, "music_fade_out": 0.5,   # short tail = loops
        "captions": "short", "thumbnails": 1, "shorts_tag": True,
        # Shorts buttons/description cover the bottom 20% and the right 12%: keep words and graphics out of it
        "safe": {"bottom": 0.20, "right": 0.12},
    },
}

# look: fonts are bundled in assets/fonts (Barlow, SIL Open Font License) so every machine draws the same thing
FONTS_DIR = ASSETS / "fonts"
FONT_FILES = {"heavy": "BarlowCondensed-ExtraBold.ttf", "bold": "Barlow-Bold.ttf",
              "medium": "Barlow-Medium.ttf", "italic": "Barlow-MediumItalic.ttf"}
CAPTION_FONT = "Barlow Condensed ExtraBold"   # libass matches the font file's own family name (in FONTS_DIR)
ACCENT = (255, 176, 32)       # amber highlight (captions, numbers, charts)
BG_TOP, BG_BOTTOM = (14, 17, 28), (34, 22, 48)
TEXT = (245, 245, 247)
MUTED = (170, 172, 184)
