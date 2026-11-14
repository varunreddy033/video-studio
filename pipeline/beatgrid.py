"""Beat lock for the music bed (smooth-motion-studio method, step 4).

Narrated videos cut on the spoken words, so the cuts can't move. What can move is where the music starts: the track
is started up to one beat later so that its beat grid lands on as many of the video's cuts as possible.

  grid(track)                      (bpm, first beat s, share of onsets on the grid) from the first 60 s, cached
  best_offset(track, cuts, start)  seconds to skip at the start of the track (0 <= offset < one beat) + the share of
                                   cuts within 40 ms of a beat before / after
"""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from . import config as C

TOL = 0.040            # a cut within 40 ms of a beat counts as on the beat
_CACHE = C.ASSETS / "cache" / "beatgrid2"


def _audio(path, sr=22050, secs=60):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-t", str(secs), "-vn", "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0, sr


def _onsets(x, sr, hop=256, n=1024):
    if len(x) < n * 4:
        return np.zeros(0)
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(n), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    pk = [i for i in range(1, len(flux) - 1) if flux[i] > 1.0 and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    return np.array([(p + 1) * hop / sr for p in pk])


def grid(track) -> tuple:
    track = Path(track)
    key = hashlib.sha1(f"{track.name}:{track.stat().st_size}".encode()).hexdigest()[:12]
    cache = _CACHE / f"{key}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return d["bpm"], d["first"], d["fit"]
    on = _onsets(*_audio(track))
    best = (-1.0, 120.0, 0.0, 0.0)
    if len(on) >= 20:
        for bpm in np.arange(70, 180.01, 0.5):
            T = 60 / bpm
            ph = np.angle(np.exp(2j * np.pi * on / T).sum())
            first = (ph / (2 * np.pi)) * T % T
            d = np.abs(((on - first + T / 2) % T) - T / 2)
            fit = float((d < 0.035).mean())
            excess = fit - 0.07 / T                   # minus what random onsets would score on this grid
            if excess > best[0] + 1e-9:
                best = (excess, float(bpm), float(first), fit)
    excess, bpm, first, _fit = best
    fit = max(0.0, excess)                            # "grid fit" = share of onsets on the beat ABOVE chance
    _CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"bpm": bpm, "first": first, "fit": fit, "track": track.name}))
    return bpm, first, fit


def _on(cuts, T, first, offset, start):
    """Share of cuts (video time) on the music's grid when the track starts at video time `start` skipping `offset`."""
    t = np.asarray(cuts) - start + offset            # track time of each cut
    d = np.abs(((t - first + T / 2) % T) - T / 2)
    return float((d < TOL).mean()) if len(t) else 0.0


def best_offset(track, cuts, start=0.0) -> dict:
    """Never more than one beat (<= 0.86 s at 70 BPM). A track whose grid is weak (fewer than 25 % more onsets on the
    beat than chance: ambient pads, rubato piano) is left at 0."""
    cuts = [c for c in cuts if c > start + 0.05]
    bpm, first, fit = grid(track)
    T = 60 / bpm
    before = _on(cuts, T, first, 0.0, start)
    if fit < 0.25 or len(cuts) < 4:
        return {"offset": 0.0, "bpm": bpm, "grid_fit": round(fit, 2), "before": round(before, 2), "after": round(before, 2)}
    cands = np.arange(0.0, T, 1 / 120)
    scores = [_on(cuts, T, first, o, start) for o in cands]
    k = int(np.argmax(scores))
    return {"offset": round(float(cands[k]), 4), "bpm": bpm, "grid_fit": round(fit, 2), "before": round(before, 2),
            "after": round(float(scores[k]), 2)}
