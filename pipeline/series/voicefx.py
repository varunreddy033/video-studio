"""Voice effects of web-series characters (cast/<id>.md `voice_fx:`), applied to a Kokoro line with ffmpeg.

Every effect keeps the length and timing of the line (pitch changes use asetrate + atempo back), so Kokoro's word
timings still drive the mouth and the captions. The result sits next to the Kokoro wav in the job cache.

  deep     villain: pitch down ~3.5 semitones, a little low-end weight
  robot    AI / android: ring modulation + light bit crush + a short metallic comb
  echo     giant / cosmic: slightly lower pitch + a long hall echo
  radio    comms / phone: band-limited 350-3200 Hz, compressed, a touch of grit
  whisper  ffmpeg's "whisperization": random phases per FFT bin (keeps the words, loses the pitch), softer
"""

from pathlib import Path

from ..util import PipelineError, h, run

SR = 24000
FX = {
    "deep": "asetrate={sr}*0.82,aresample={sr},atempo=1.2195,bass=g=4:f=120,volume=1.1",
    "robot": "aeval='0.55*val(0)+0.75*val(0)*sin(2*PI*58*t)':c=same,acrusher=bits=9:mix=0.35:mode=log,"
             "aecho=0.8:0.6:6:0.35,volume=1.15",
    "echo": "asetrate={sr}*0.92,aresample={sr},atempo=1.087,aecho=0.8:0.75:180|420:0.42|0.25,volume=1.05",
    "radio": "highpass=f=350,lowpass=f=3200,acompressor=threshold=0.08:ratio=6:attack=5:release=80,"
             "acrusher=bits=12:mix=0.2,volume=1.6",
    "whisper": "afftfilt=real='hypot(re,im)*cos((random(0)*2-1)*2*3.14)':"
               "imag='hypot(re,im)*sin((random(1)*2-1)*2*3.14)':win_size=512:overlap=0.75,"
               "highpass=f=250,volume=1.8",
}
NAMES = tuple(FX)


def apply(wav: Path, fx: str, job_dir: Path) -> Path:
    """wav with the effect (cached by input file + effect). fx '' / none = the wav itself."""
    fx = (fx or "").strip().lower()
    if not fx or fx == "none":
        return wav
    if fx not in FX:
        raise PipelineError(f"unknown voice effect '{fx}' (valid: {', '.join(NAMES)})")
    out = wav.with_name(f"{wav.stem}_fx_{fx}_{h(wav.name, FX[fx], 'v1')[:8]}.wav")
    if out.exists() and out.stat().st_size > 0:
        return out
    tmp = out.with_suffix(".tmp.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", FX[fx].format(sr=SR), "-ar", str(SR), "-ac", "1",
         str(tmp)], job_dir, f"voice effect {fx}")
    tmp.replace(out)
    return out
