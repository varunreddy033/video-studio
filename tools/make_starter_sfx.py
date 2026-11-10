"""Generate the starter sound-effect pack: assets/library/sfx/<kind>/starter_<kind>.wav

    bin/python tools/make_starter_sfx.py            (safe to re-run: same sounds every time)

Every sound is synthesised here from noise and sine waves (numpy only), so there is no licence to worry about.
They are simple on purpose: drop a better sound into the same folder and it is used instead of the starter one
(files named starter_* are only picked when the folder has nothing else).
"""

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C          # noqa: E402

SR = 44100


def t(dur):
    return np.arange(int(SR * dur)) / SR


def noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def env_exp(n, decay):
    """Exponential decay over n samples; decay = seconds to fall to 1/e."""
    return np.exp(-np.arange(n) / (SR * decay))


def fade(x, fin=0.004, fout=0.02):
    a, b = int(SR * fin), int(SR * fout)
    x = x.copy()
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def onepole_lp(x, hz):
    a = np.exp(-2 * np.pi * hz / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def bandpass_sweep(x, f_curve, q=2.5):
    """State-variable band-pass whose centre frequency follows f_curve (Hz per sample)."""
    low = band = 0.0
    y = np.empty_like(x)
    for i, v in enumerate(x):
        f = 2 * np.sin(np.pi * min(f_curve[i], SR / 6.5) / SR)
        high = v - low - band / q
        band += f * high
        low += f * band
        y[i] = band
    return y


def sweep_sine(f0, f1, dur, curve="exp"):
    n = int(SR * dur)
    k = np.linspace(0, 1, n)
    f = f0 * (f1 / f0) ** k if curve == "exp" else f0 + (f1 - f0) * k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def place(total, parts):
    """Mix [(start_s, samples), ...] into a buffer of total seconds."""
    out = np.zeros(int(SR * total))
    for start, x in parts:
        i = int(SR * start)
        x = x[: max(0, len(out) - i)]
        out[i:i + len(x)] += x
    return out


def key_click(seed, bright=1.0):
    n = int(SR * 0.03)
    click = noise(n, seed) * env_exp(n, 0.004) * bright
    click = click - onepole_lp(click, 1800)                      # keep the bright part
    thock = np.sin(2 * np.pi * (170 + 40 * (seed % 5)) * t(0.03)) * env_exp(n, 0.012) * 0.6
    return click + thock


def whoosh():
    n = int(SR * 0.75)
    k = np.linspace(0, 1, n)
    f = 350 + 3600 * np.sin(np.pi * k) ** 1.5                    # up, then back down
    body = bandpass_sweep(noise(n, 11), f, q=1.6)
    air = bandpass_sweep(noise(n, 12), f * 2.2, q=1.2) * 0.35
    return (body + air) * np.sin(np.pi * k) ** 1.8


def riser():
    dur = 1.6
    n = int(SR * dur)
    k = np.linspace(0, 1, n)
    f = 300 * (5200 / 300) ** k
    air = bandpass_sweep(noise(n, 21), f, q=2.2)
    tone = sweep_sine(180, 1400, dur) * 0.35 + sweep_sine(181.5, 1412, dur) * 0.35   # two detuned voices
    x = (air + tone) * k ** 2.2
    return fade(x, 0.01, 0.012)


def impact():
    dur = 1.1
    n = int(SR * dur)
    sub = sweep_sine(130, 38, dur) * env_exp(n, 0.28)
    body = sweep_sine(260, 70, dur) * env_exp(n, 0.09) * 0.5
    m = int(SR * 0.05)
    hit = onepole_lp(noise(m, 31), 2500) * env_exp(m, 0.012) * 0.9
    return place(dur, [(0, sub + body), (0, hit)])


def pop():
    dur = 0.16
    n = int(SR * dur)
    return sweep_sine(950, 260, dur) * env_exp(n, 0.035)


def ding():
    dur = 1.3
    n = int(SR * dur)
    base = 1318.5                                                # E6
    x = np.zeros(n)
    for mult, amp, decay in ((1, 1.0, 0.45), (2.76, 0.45, 0.22), (5.4, 0.25, 0.12), (8.93, 0.12, 0.06)):
        x += amp * np.sin(2 * np.pi * base * mult * t(dur)) * env_exp(n, decay)
    return x


def typing():
    rng = np.random.default_rng(61)
    parts, at = [], 0.02
    for i in range(10):
        parts.append((at, key_click(600 + i, 0.8 + 0.4 * rng.random())))
        at += 0.09 + 0.09 * rng.random()
    return place(at + 0.08, parts)


def click():
    return place(0.09, [(0.0, key_click(71, 1.2))])


def shutter():
    def burst(seed, dur, hz):
        m = int(SR * dur)
        x = noise(m, seed) * env_exp(m, dur / 3)
        return x - onepole_lp(x, hz)
    return place(0.36, [(0.0, burst(81, 0.05, 900)), (0.012, key_click(82, 1.0)),
                        (0.11, burst(83, 0.07, 1400) * 0.8), (0.125, key_click(84, 0.9))])


def glitch():
    rng = np.random.default_rng(91)
    parts, at = [], 0.0
    while at < 0.55:
        dur = 0.02 + 0.05 * rng.random()
        m = int(SR * dur)
        if rng.random() < 0.55:                                  # bit-crushed square tone
            f = rng.choice([220, 440, 660, 990, 1760, 3520])
            x = np.sign(np.sin(2 * np.pi * f * t(dur)))
            x = np.round(x * 3) / 3 * 0.6
        else:                                                    # sample-and-hold noise
            hold = int(rng.integers(4, 40))
            x = np.repeat(rng.uniform(-1, 1, m // hold + 1), hold)[:m] * 0.8
        parts.append((at, fade(x, 0.001, 0.002)))
        at += dur + (0.03 * rng.random() if rng.random() < 0.4 else 0.0)
    return place(at + 0.02, parts)


def cash():
    def bell(f, dur):
        m = int(SR * dur)
        return (np.sin(2 * np.pi * f * t(dur)) + 0.4 * np.sin(2 * np.pi * f * 2.41 * t(dur))) * env_exp(m, dur / 4)
    return place(0.95, [(0.0, key_click(101, 1.1)), (0.05, bell(2093, 0.4)), (0.17, bell(2637, 0.75))])


def heartbeat():
    def thump(f, amp):
        m = int(SR * 0.16)
        return sweep_sine(f, f * 0.6, 0.16) * env_exp(m, 0.045) * amp
    beat = [(0.0, thump(75, 1.0)), (0.26, thump(62, 0.75))]
    return place(1.75, beat + [(s + 0.9, x) for s, x in beat])


def tick():
    def one(f):
        m = int(SR * 0.025)
        return np.sin(2 * np.pi * f * t(0.025)) * env_exp(m, 0.004)
    return place(1.05, [(i * 0.25, one(2400 if i % 2 == 0 else 1900)) for i in range(4)])


def alert():
    def beep(f):
        return fade(np.sin(2 * np.pi * f * t(0.14)) + 0.3 * np.sin(2 * np.pi * f * 2 * t(0.14)), 0.005, 0.01)
    return place(0.75, [(0.0, beep(880)), (0.17, beep(660)), (0.4, beep(880)), (0.57, beep(660))])


KINDS = {"whoosh": whoosh, "riser": riser, "impact": impact, "pop": pop, "ding": ding, "typing": typing,
         "click": click, "shutter": shutter, "glitch": glitch, "cash": cash, "heartbeat": heartbeat, "tick": tick,
         "alert": alert}


TRIM = {"alert": -10, "glitch": -10, "pop": -5}                # peak level in dBFS (default -3)


def main():
    for kind, make in KINDS.items():
        x = fade(np.asarray(make(), dtype=np.float64))
        peak_db = TRIM.get(kind, -3)                              # dense sounds sit lower so all feel equally loud
        x = x / max(1e-9, np.abs(x).max()) * 10 ** (peak_db / 20)
        out = C.SFX_LIB / kind / f"starter_{kind}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out, x.astype(np.float32), SR, subtype="PCM_16")
        print(f"   {out.relative_to(C.BASE_DIR)}  {len(x) / SR:.2f} s")


if __name__ == "__main__":
    main()
