"""Design system of the motion renderer: bright-pop palettes, fonts, easing and timing.

One motion personality for the whole channel ("Energetic", motion-design skill): fast entrances with overshoot,
exits quicker than entrances, a signature ease for 80 % of moves. Every scene gets a solid backdrop colour from a
rotation in which neighbours never repeat (color-motion skill: big flat fields, one ink, one highlight)."""

# backdrop, ink (text + figure lines), highlight (marker behind key words, number accents), soft (ambient shapes)
PALETTES = [
    {"name": "yellow", "bg": "#FFD21F", "ink": "#111111", "hi": "#FFFFFF", "pop": "#FF3347", "soft": "#FFE36E"},
    {"name": "red", "bg": "#FF3347", "ink": "#FFFFFF", "hi": "#111111", "pop": "#FFD21F", "soft": "#FF6A79"},
    {"name": "cream", "bg": "#FFF3D6", "ink": "#111111", "hi": "#FFD21F", "pop": "#FF3347", "soft": "#FFE6A8"},
    {"name": "blue", "bg": "#2F6BFF", "ink": "#FFFFFF", "hi": "#FFD21F", "pop": "#FFD21F", "soft": "#5B8CFF"},
    {"name": "green", "bg": "#1FC16B", "ink": "#FFFFFF", "hi": "#111111", "pop": "#FFF3D6", "soft": "#4ED48A"},
    {"name": "pink", "bg": "#FF5DA2", "ink": "#FFFFFF", "hi": "#111111", "pop": "#FFD21F", "soft": "#FF86BB"},
    {"name": "white", "bg": "#F4F4F0", "ink": "#111111", "hi": "#FFD21F", "pop": "#2F6BFF", "soft": "#E3E3DC"},
    {"name": "purple", "bg": "#7C4DFF", "ink": "#FFFFFF", "hi": "#FFD21F", "pop": "#FFD21F", "soft": "#9C78FF"},
]

# one palette SET per video (look rotation, history.py); scenes walk through the set's colours
PALETTE_SETS = {"pop": ["yellow", "red", "cream", "blue", "green", "pink", "white", "purple"],
                "warm": ["yellow", "red", "cream", "pink", "white"],
                "cool": ["blue", "green", "purple", "white", "cream"],
                "bold": ["red", "blue", "yellow", "green", "purple"]}

# fonts bundled in assets/fonts (SIL OFL), copied into every job
FONTS = {"display": ("Anton", "Anton-Regular.ttf", 400), "heavy": ("Barlow Black", "Barlow-Black.ttf", 900),
         "body": ("Poppins SemiBold", "Poppins-SemiBold.ttf", 600), "comic": ("Bangers", "Bangers-Regular.ttf", 400),
         "condensed": ("Barlow Condensed ExtraBold", "BarlowCondensed-ExtraBold.ttf", 800),
         "bold": ("Barlow Bold", "Barlow-Bold.ttf", 700)}

# the premium blocks' faces (pipeline/motion_gfx/premium/core.py FONT_FACES): copied into every motion project and
# declared in index.html like the fonts above ("Poppins" 400/500/600, Inter, Jost, Nunito, Modak, Bagel Fat One...)
from .premium.core import FONT_FACES as _PREMIUM_FACES  # noqa: E402
for _i, (_fam, _file, _w) in enumerate(_PREMIUM_FACES):
    FONTS.setdefault(f"premium_{_i}", (_fam, _file, _w))

# one font pairing per video: headline font (+ its caps width per character, for fit()) and body font
FONT_PAIRS = {"poster": {"head": "Anton", "char_w": 0.5, "body": "Poppins SemiBold"},
              "condensed": {"head": "Barlow Condensed ExtraBold", "char_w": 0.5, "body": "Barlow Bold"},
              "comic": {"head": "Bangers", "char_w": 0.55, "body": "Poppins SemiBold"}}

EASE_IN = "expo.out"            # signature entrance (kinetic-typography: cubic-bezier(0.16,1,0.3,1))
EASE_POP = "spring.snappy"      # closed-form spring (spring.py): 23 % overshoot, settles 0.56 s
EASE_SOFT = "power3.out"
EASE_OUT = "power2.in"          # exits: shorter and accelerating
WORD_IN = 0.32                  # one word's entrance (s)
STAGGER = 0.055                 # words shown together: 55 ms apart

TRANSITION = 0.32               # scene overlap for push / zoom / wipe / whip (s)
BEAT_MIN, BEAT_MAX = 1.2, 3.0   # a new picture every 1.2-3 s (beat-sync-editing)

# safe areas (shot-composition + hyperframes vertical.md). The caption chip owns the top-left corner.
SAFE = {"landscape": {"x0": 0.07, "x1": 0.93, "y0": 0.22, "y1": 0.93, "chip": (0.06, 0.07)},
        "vertical": {"x0": 0.08, "x1": 0.84, "y0": 0.20, "y1": 0.69, "chip": (0.07, 0.10)}}


def palette_order(n, seed=0, names=None):
    """n palette indexes where neighbours always differ (and so do scenes two apart, when possible).
    names = the video's palette set (PALETTE_SETS); default all eight."""
    allowed = [k for k, p in enumerate(PALETTES) if not names or p["name"] in names]
    m = len(allowed)
    step = 3 if m % 3 else 1                 # 3 is co-prime with 8, 5, 7: walks all colours, never repeats in a row
    out, k = [], seed % m
    for _ in range(n):
        out.append(allowed[k])
        k = (k + step) % m
    return out
