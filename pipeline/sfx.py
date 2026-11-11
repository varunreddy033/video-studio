"""
sfx.py  -  automatic sound effects (script header `sfx: auto`).

Rule-based, no AI: the same script always gets the same effects. For every shot it looks at
  1. words in the narration that name a sound ("crashed" -> impact, "suddenly" -> riser, "hacked" -> glitch ...)
  2. the kind of shot (title card -> whoosh, number -> ding or cash, quote -> typing, chart -> riser,
     a new chapter -> whoosh)
and places at most one effect per shot, never two closer than MIN_GAP seconds, never the same kind twice within
SAME_KIND_GAP seconds, and nothing where the script already has its own [sfx: ...] tag. Only kinds that have a
file (assets/library/sfx/<kind>/ or assets/audio/sfx) are used.
"""

import re

from .util import best_match

# density: auto = a few well-placed effects (about 4-6 a minute); rich = something on almost every cut, like
# animated explainers (15-20 a minute), still never the same sound twice in a row
DENSITY = {"auto": {"min_gap": 3.0, "same_kind_gap": 9.0, "every_shot": False},
           "rich": {"min_gap": 1.2, "same_kind_gap": 3.5, "every_shot": True}}
CUT_KINDS = ["whoosh", "swipe", "pop", "click", "bubble", "paper"]     # rich: rotated on plain picture changes
GAIN = 0.8               # automatic effects sit a little under the script's own [sfx:] tags

# kind -> how early it starts before the cut (s): a whoosh straddles the cut, a riser ends on it
LEAD = {"whoosh": 0.28, "riser": 1.2, "tick": 0.0, "typing": 0.0, "heartbeat": 0.0}
DEFAULT_LEAD = 0.12

# narration words -> kind (first match wins, most specific first)
KEYWORDS = [
    ("glitch", r"glitch\w*|hack(ed|ers?|ing)?|malware|virus(es)?|corrupt(ed)?|error"),
    ("alert", r"warn(ing|ed|s)?|alarm(s|ing)?|alert(s|ed)?|danger(ous)?|red flag"),
    ("heartbeat", r"fear(s|ed)?|afraid|panic(ked|king)?|terrif\w+|nervous|heart(beat)? (raced|pounding|stopped)"),
    ("impact", r"crash(ed|es|ing)?|collaps(e|ed|es|ing)|plung(e|ed|es|ing)|plummet(ed|s|ing)?|tank(ed|s|ing)?|"
               r"slam(med|s)?|smash(ed|es)?|wiped out|bankrupt\w*|explo(de|ded|sion)"),
    ("pop", r"pop(s|ped|ping)?|burst(s|ing)?"),
    ("riser", r"suddenly|overnight|surg(e|ed|es|ing)|soar(ed|s|ing)?|skyrocket(ed|s|ing)?|rocket(ed|s|ing)?|"
              r"boom(ed|s|ing)?|doubl(e|ed|es|ing)|tripl(e|ed|es|ing)|explosive"),
    ("shutter", r"photo(s|graph\w*)?|camera(s)?|snapshot(s)?|picture(s)?"),
    ("typing", r"typ(e|ed|ing)|email(s|ed)?|message(s|d)?|wrote|memo|tweet(s|ed)?|post(ed)? online"),
    ("click", r"click(s|ed|ing)?|button(s)?|switch(ed)? (on|off)"),
    ("tick", r"deadline(s)?|countdown|clock is ticking|running out of time|time is running out"),
    ("cash", r"cash(ed)?|payday|jackpot|paid out|profit(s)?|revenue|cost(s)? (\w+ )?(million|billion|trillion)"),
]
KEYWORDS = [(k, re.compile(rf"\b({p})\b", re.I)) for k, p in KEYWORDS]

# shot type -> kinds to try in order
BY_SHOT = {"card": ["whoosh", "stamp"], "quote": ["typing", "paper", "click"], "chart": ["riser", "whoosh"]}


def _has(kind, files, cache):
    if kind not in cache:
        cache[kind] = best_match(kind, files) is not None
    return cache[kind]


def auto_cues(segments, shots, chapters, files, density="auto"):
    """Adds seg["sfx_auto"] = [{"kind", "lead", "gain"}] to the first segment of chosen shots.
    Returns (cues, missing): cues = [{line, at, kind, why}] for the Check page, missing = kinds the rules wanted
    but that have no file."""
    D = DENSITY[density]
    MIN_GAP, SAME_KIND_GAP = D["min_gap"], D["same_kind_gap"]
    cache, cues, missing, rot = {}, [], set(), 0
    chapter_starts = {c["segment"] for c in chapters if c["segment"] > 0}
    last_at, last_kind_at = -99.0, {}
    for seg in segments:
        seg["sfx_auto"] = []
    for sh in shots:
        si = sh.get("first_segment")
        if si is None or si >= len(segments):
            continue
        seg = segments[si]
        if seg["sfx"]:                                   # the script's own effect wins
            last_at = seg["est_start"]
            continue
        want = []
        text = " ".join(s["text"] for s in segments if s["shot"] == shots.index(sh))
        for kind, rx in KEYWORDS:
            m = rx.search(text)
            if m:
                want.append((kind, f"the narration says \"{m.group(0)}\""))
                break
        if sh["type"] == "number":
            money = bool(re.search(r"[$₹€£]", sh.get("prefix", "") + sh.get("suffix", "")))
            want += [(k, "a number appears") for k in (["cash", "coin", "ding", "pop"] if money else ["ding", "pop"])]
        for k in BY_SHOT.get(sh["type"], []):
            want.append((k, {"card": "a title card appears", "quote": "a quote appears",
                             "chart": "a chart appears"}[sh["type"]]))
        if si in chapter_starts:
            want.append(("whoosh", "a new chapter starts"))
        if D["every_shot"] and sh["type"] != "talk":     # rich: a light sound on every picture change
            for i in range(len(CUT_KINDS)):
                want.append((CUT_KINDS[(rot + i) % len(CUT_KINDS)], "the picture changes"))
            rot += 1
        at = seg["est_start"]
        if not want or at - last_at < MIN_GAP or (at < 0.5 and sh["type"] not in ("card", "number")):
            continue
        for kind, why in want:
            if not _has(kind, files, cache):
                missing.add(kind)
                continue
            if at - last_kind_at.get(kind, -99.0) < SAME_KIND_GAP:
                continue
            seg["sfx_auto"].append({"kind": kind, "lead": LEAD.get(kind, DEFAULT_LEAD), "gain": GAIN})
            cues.append({"line": sh["line"], "at": round(at, 1), "kind": kind, "why": why})
            last_at, last_kind_at[kind] = at, at
            break
    return cues, sorted(missing)
