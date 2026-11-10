"""
encoder.py  -  picks the H.264 encoder this machine can actually use, once per process.

  Mac (Apple Silicon)        h264_videotoolbox   hardware, fast, keeps the fanless Air cool
  Windows/Linux + NVIDIA     h264_nvenc          hardware (e.g. the Legion's RTX GPU)
  anything else              libx264             software, works everywhere (slower)

Each candidate is tried with a tiny real test encode (an encoder can be listed by FFmpeg but still fail, e.g.
nvenc without an NVIDIA driver). Force one with VIDEO_ENCODER=libx264 (or h264_nvenc / h264_videotoolbox) in .env.
"""

import shutil
import subprocess
import sys
import threading

from . import config as C

CANDIDATES = (["h264_videotoolbox"] if sys.platform == "darwin" else []) + ["h264_nvenc", "libx264"]
_chosen = None
_lock = threading.Lock()


def _works(name: str) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i",
                        "color=c=black:s=256x256:r=30:d=0.2", "-frames:v", "5", "-c:v", name,
                        "-pix_fmt", "yuv420p", "-f", "null", "-"], capture_output=True)
    return p.returncode == 0


def name() -> str:
    """The encoder in use (detected on first call)."""
    global _chosen
    with _lock:
        if _chosen is None:
            forced = C.VIDEO_ENCODER
            if forced:
                if not _works(forced):
                    raise RuntimeError(f"VIDEO_ENCODER={forced} (from .env) doesn't work with this FFmpeg")
                _chosen = forced
            else:
                _chosen = next((c for c in CANDIDATES if _works(c)), "libx264")
        return _chosen


def args(bitrate: str, final: bool = False) -> list:
    """FFmpeg video-codec arguments for one encode at a target bitrate (e.g. '10M').
    final=True = the one encode viewers see (slower, better preset on software x264)."""
    enc = name()
    rate = ["-b:v", bitrate, "-maxrate", bitrate]
    if enc == "h264_videotoolbox":
        return ["-c:v", enc, *rate, "-profile:v", "high"]
    if enc == "h264_nvenc":
        return ["-c:v", enc, "-preset", "p5", "-rc", "vbr", *rate, "-bufsize", bitrate, "-profile:v", "high"]
    # libx264: bitrate-capped, 'medium' for the final, 'veryfast' for intermediate clips
    return ["-c:v", "libx264", "-preset", "medium" if final else "veryfast", *rate, "-bufsize", bitrate,
            "-profile:v", "high"]
