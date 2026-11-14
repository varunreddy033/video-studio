"""Premium motion blocks (19), rebuilt from measured reference clips. See README.md and ../SPECS.md.

    from premium import BLOCKS
    parts = BLOCKS["glass_quote"]["build"]("s7", {"W": 1920, "H": 1080, "quote": "..."})
    parts["html"], parts["css"], parts["js"], parts["cues"], parts["dur"]
"""
from . import blocks_a as A, blocks_b as B, blocks_c as C

# name -> builder, reference clip, recording time that equals block t=0, loops used for the comparison render
BLOCKS = {
    "glass_quote":    {"build": A.glass_quote,    "ref": "ex01", "ref_t0": 1.133,  "loops": 1},
    "card_pops":      {"build": A.card_pops,      "ref": "ex02", "ref_t0": 0.45,   "loops": 2},
    "card_wheel":     {"build": A.card_wheel,     "ref": "ex03", "ref_t0": 0.45,   "loops": 1},
    "morph_word":     {"build": A.morph_word,     "ref": "ex04", "ref_t0": 1.80,   "loops": 1},
    "pill_split":     {"build": A.pill_split,     "ref": "ex05", "ref_t0": 1.283,  "loops": 1},
    "card_flip":      {"build": A.card_flip,      "ref": "ex06", "ref_t0": 0.15,   "loops": 1},
    "word_slide":     {"build": A.word_slide,     "ref": "ex07", "ref_t0": -0.183, "loops": 2},
    "chart_card":     {"build": B.chart_card,     "ref": "ex08", "ref_t0": 1.38,   "loops": 1},
    "donut_card":     {"build": B.donut_card,     "ref": "ex09", "ref_t0": 1.95,   "loops": 1},
    "search_type":    {"build": B.search_type,    "ref": "ex10", "ref_t0": -1.65,  "loops": 2},
    "word_wheel":     {"build": B.word_wheel,     "ref": "ex11", "ref_t0": -0.03,  "loops": 5},
    "toggle":         {"build": B.toggle,         "ref": "ex12", "ref_t0": 0.337,   "loops": 1},
    "list_circle":    {"build": B.list_circle,    "ref": "ex13", "ref_t0": -0.737,  "loops": 2},
    "odometer":       {"build": C.odometer,       "ref": "ex14", "ref_t0": -0.20,  "loops": 2},
    "gradient_words": {"build": C.gradient_words, "ref": "ex15", "ref_t0": 0.60,   "loops": 1},
    "track_type":     {"build": C.track_type,     "ref": "ex16", "ref_t0": 0.32,   "loops": 1},
    "blur_zoom_type": {"build": C.blur_zoom_type, "ref": "ex17", "ref_t0": -0.35,  "loops": 2},
    "post_card":      {"build": C.post_card,      "ref": "ex18", "ref_t0": 0.68,   "loops": 1},
    "color_carousel": {"build": C.color_carousel, "ref": "ex19", "ref_t0": 0.0,    "loops": 2},
}
