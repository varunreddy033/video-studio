"""
voice.py  -  Kokoro-82M voiceover with per-word timings (for word-by-word captions).
Kokoro gives start/end times for every word; whisper.cpp is the backup if it ever doesn't.
Every segment is cached by (text, voice, speed), so the final render reuses the draft's voice.
"""

import json
import re
import threading
from pathlib import Path

import numpy as np
import soundfile as sf

from . import config as C
from .util import PipelineError, h, log, run

SR = 24000
_pipes = {}
_lock = threading.Lock()


def _pipeline(voice: str):
    lang = "b" if voice.startswith("b") else "a"     # b* = British, a* = American voices
    if lang not in _pipes:
        from kokoro import KPipeline
        _pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    return _pipes[lang]


def _whisper_words(wav: Path, job_dir: Path):
    """Backup word timings from whisper.cpp (one word per segment)."""
    wav16 = wav.with_suffix(".16k.wav")
    run(["ffmpeg", "-y", "-i", wav, "-ar", "16000", "-ac", "1", wav16], job_dir, "voice -> 16 kHz")
    base = wav.with_suffix("")
    run([C.WHISPER_BIN, "-m", C.WHISPER_MODEL, "-f", wav16, "-ml", "1", "-sow", "-oj", "-of", base, "-np"],
        job_dir, "whisper word timings")
    data = json.loads(Path(str(base) + ".json").read_text(encoding="utf-8"))
    words = []
    for seg in data.get("transcription", []):
        t = seg.get("text", "").strip()
        if t:
            words.append([t, seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000, ""])
    wav16.unlink(missing_ok=True)
    return words


def synth(text: str, voice: str, speed: float, job_dir: Path):
    """Returns (wav_path, duration_s, words) where words = [[word, start, end, phonemes], ...]
    (phonemes = Kokoro's IPA for that word, used for lip sync; "" when unknown)."""
    cache = job_dir / "cache"
    cache.mkdir(exist_ok=True)
    key = h(text, voice, speed, "kokoro-82m-v2")
    wav, meta = cache / f"voice_{key}.wav", cache / f"voice_{key}.json"
    if wav.exists() and meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        return wav, m["dur"], m["words"]
    chunks, words, offset, have_ts = [], [], 0.0, True
    with _lock:   # Kokoro isn't thread-safe; voice is fast anyway
        for res in _pipeline(voice)(text, voice=voice, speed=speed):
            audio = res.audio.numpy() if hasattr(res.audio, "numpy") else np.asarray(res.audio)
            for tok in (res.tokens or []):
                if tok.start_ts is None or tok.end_ts is None:
                    have_ts = False
                    continue
                t = tok.text.strip()
                if not t:
                    continue
                if not re.search(r"[A-Za-z0-9]", t) and words:   # punctuation: glue to the word before
                    words[-1][0] += t
                    continue
                words.append([t, round(offset + tok.start_ts, 3), round(offset + tok.end_ts, 3),
                              getattr(tok, "phonemes", "") or ""])
            chunks.append(audio)
            offset += len(audio) / SR
    if not chunks:
        raise PipelineError(f"Kokoro returned no audio for: {text[:60]}")
    a = np.concatenate(chunks).astype(np.float32)
    sf.write(wav, a, SR)
    dur = len(a) / SR
    if not words or not have_ts:
        log(job_dir, f"  no Kokoro word timings for '{text[:40]}...', using whisper")
        try:
            words = _whisper_words(wav, job_dir)
        except Exception as e:  # last resort: spread the words evenly
            log(job_dir, f"  whisper failed ({e}); spreading words evenly")
            ws = text.split()
            step = dur / max(1, len(ws))
            words = [[w, round(i * step, 3), round((i + 1) * step, 3), ""] for i, w in enumerate(ws)]
    meta.write_text(json.dumps({"dur": dur, "words": words}), encoding="utf-8")
    return wav, dur, words
