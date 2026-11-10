"""Small helpers shared by every pipeline step."""

import hashlib
import random
import re
import subprocess
import time
import wave
from pathlib import Path

from . import config as C


class PipelineError(Exception):
    pass


def log(job_dir: Path, msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(job_dir / "render.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, job_dir: Path, what: str, input_bytes=None, cwd=None):
    """Run a command; on failure raise with the tail of its error output."""
    p = subprocess.run([str(c) for c in cmd], capture_output=True, input=input_bytes, cwd=cwd)
    if p.returncode != 0:
        err = (p.stderr or p.stdout or b"").decode(errors="replace").strip().splitlines()[-12:]
        log(job_dir, f"FAILED: {what}\n  " + "\n  ".join(err))
        raise PipelineError(f"{what} failed: {' | '.join(err[-3:])}")
    return p


def h(*parts) -> str:
    """Short stable hash, used for cache file names."""
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / float(w.getframerate())


def media_duration(path: Path) -> float:
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def fmt_ts(sec: float) -> str:
    sec = int(sec)
    hh, rem = divmod(sec, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh}:{mm:02d}:{ss:02d}" if hh else f"{mm}:{ss:02d}"


# ------------------------------------------------- matching audio files by name words ---
SYNONYMS = {
    "whoosh": {"whoosh", "swoosh", "swish", "woosh", "swipe", "transition"},
    "glitch": {"glitch", "digital", "static", "distortion", "sizzle", "error"},
    "drop": {"drop", "sub", "boom", "impact", "hit", "bass", "thud"},
    "riser": {"riser", "rise", "build", "tension", "swell"},
    "shutter": {"shutter", "camera", "flash", "photo"},
    "click": {"click", "lock", "pop", "tick"},
    "typing": {"typing", "keyboard", "type"},
    "heartbeat": {"heartbeat", "heart", "pulse"},
    "gavel": {"gavel", "hammer", "knock"},
    "glass": {"glass", "shatter", "crack", "break", "fracture"},
    "electric": {"electric", "spark", "arc", "buzz", "zap"},
    "dark": {"dark", "ominous", "tension", "suspense", "drone", "noir"},
    "synth": {"synth", "synthwave", "cyber", "cyberpunk", "electronic"},
}
_STOP = {"low", "high", "deep", "fast", "slow", "the", "a", "and", "of", "sfx", "fx",
         "sound", "effect", "null", "none", "mp3", "wav"}


def _tokens(s: str) -> set:
    return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t and t not in _STOP}


def _expand(tokens: set) -> set:
    out = set(tokens)
    for t in tokens:
        for group in SYNONYMS.values():
            if t in group:
                out |= group
    return out


_dur_cache = {}


def list_audio(folder: Path, min_sec: float = 0.0):
    files = sorted(p for p in folder.glob("*") if p.suffix.lower() in C.AUDIO_EXT) if folder.exists() else []
    if min_sec:
        out = []
        for p in files:
            if p not in _dur_cache:
                _dur_cache[p] = media_duration(p)
            if _dur_cache[p] >= min_sec:
                out.append(p)
        files = out
    return files


def _lib_audio(root: Path):
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in C.AUDIO_EXT) if root.exists() else []


def _long_enough(files, min_sec: float):
    out = []
    for p in files:
        if p not in _dur_cache:
            _dur_cache[p] = media_duration(p)
        if _dur_cache[p] >= min_sec:
            out.append(p)
    return out


def music_files(min_sec: float = 60.0):
    """Every usable music track: assets/audio/bgm (local) + assets/library/music/<mood>/ (in git)."""
    return list_audio(C.BGM_DIR, min_sec) + _long_enough(_lib_audio(C.MUSIC_LIB), min_sec)


def sfx_files():
    """Every sound effect: assets/audio/sfx (local) + assets/library/sfx/<kind>/ (in git)."""
    return list_audio(C.SFX_DIR) + _lib_audio(C.SFX_LIB)


def audio_duration(p: Path) -> float:
    if p not in _dur_cache:
        _dur_cache[p] = media_duration(p)
    return _dur_cache[p]


def library_group(f: Path) -> str:
    """The mood / kind folder of a library file ('' for files outside the library or directly in music/ or sfx/)."""
    for root in (C.MUSIC_LIB, C.SFX_LIB):
        try:
            rel = Path(f).relative_to(root)
        except ValueError:
            continue
        return rel.parts[0] if len(rel.parts) > 1 else ""
    return ""


def _name_tokens(f: Path) -> set:
    """Words a file answers to: its name, and for library files also its folder (mood / kind)."""
    return _tokens(f.stem) | _tokens(library_group(f))


def is_starter(f: Path) -> bool:
    return Path(f).stem.startswith("starter_")


def best_match(cue: str, files, fallback_random=False, rng=random):
    """The file whose name words fit the cue best. Order: most matching words (synonyms count), then exact cue
    words before synonyms, then your own files before the generated starter pack; ties are picked by rng."""
    if not files:
        return None
    if cue:
        exact = _tokens(cue)
        want = _expand(exact)
        scored = []
        for f in files:
            t = _name_tokens(f)
            scored.append(((len(want & t), len(exact & t), not is_starter(f)), f))
        top = max(s for s, _ in scored)
        if top[0] > 0:
            return rng.choice([f for s, f in scored if s == top])
    return rng.choice(files) if fallback_random else None
