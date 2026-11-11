"""The scene planner of motion graphics (docs/VARIETY_PLAN.md section 5). Replaces the old figure <-> kinetic
alternation of templates.pick().

  rhythm(beats, seed)          bursts of quick scenes on the hook and after chapter cards, a held "breather" scene
                               about every 45 s (two calm beats merged, slow drift)
  roles(beat)                  what a beat does: statistic, comparison, list, process, cause, timeline, quote,
                               definition, story, question, warning, conclusion, transition
  plan(beats, seed, ...)       one scene type per beat: candidates that fit the beat's words and roles, chosen under
                               the budget (type <= 20 % of scenes, type + layout <= 6 uses, kinetic <= 15 % and only for
                               punch lines, never the same type twice in a row, no A-B-A-B), each chapter leaning on a
                               different part of the mix
  transitions(beats, names)    8-10 transition types chosen by the story relation of two scenes, none above 35 %

Everything is seeded by the title: same script + same format = same video.
"""

import hashlib
import math
import re

from . import extras as X
from . import templates as T

# ------------------------------------------------------------------------------------------------- rhythm
BURST_UNTIL = 10.0        # the hook: scenes of the first 10 s are cut quicker
BURST_SPLIT = 2.0         # ... a beat longer than this is split in two there
BURST_MIN = 0.8
BREATHER_EVERY = 45.0     # a held scene about this often
BREATHER_LEN = (3.5, 6.5)


def _h(*parts) -> int:
    return int(hashlib.sha1(":".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:8], 16)


def _split_words(b):
    ws = b["words"]
    if len(ws) < 4:
        return None
    mid = (b["start"] + b["end"]) / 2
    k = min(range(1, len(ws)), key=lambda j: abs(ws[j][1] - mid))
    cut = max(b["start"] + BURST_MIN, min(b["end"] - BURST_MIN, ws[k][1] - 0.04))
    if cut - b["start"] < BURST_MIN or b["end"] - cut < BURST_MIN:
        return None
    a = dict(b, end=round(cut, 3), words=ws[:k], text=" ".join(w[0] for w in ws[:k]), burst=True)
    c = dict(b, start=round(cut, 3), words=ws[k:], text=" ".join(w[0] for w in ws[k:]), index=b["index"] + 0.5,
             chapter=None, chapter_card=False, burst=True)
    return a, c


def rhythm(beats: list, seed: int = 0) -> list:
    """The beats with bursts and breathers applied (new list; durations recomputed)."""
    out = []
    after_card = False
    for b in beats:
        hook = b["start"] < BURST_UNTIL or after_card
        after_card = bool(b.get("chapter_card"))
        if hook and not b.get("chapter_card") and b["end"] - b["start"] > BURST_SPLIT and b["kind"] not in (
                "number", "quote", "chart", "card") or (hook and b["index"] > 0 and b["end"] - b["start"] > BURST_SPLIT
                                                        and not b.get("chapter_card")):
            parts = _split_words(b)
            if parts:
                out += list(parts)
                continue
        out.append(dict(b))
    # breathers: merge two calm neighbours of one shot into one held scene, about every 45 s
    res, last = [], -BREATHER_EVERY * 0.6
    i = 0
    while i < len(out):
        b = out[i]
        nb = out[i + 1] if i + 1 < len(out) else None
        if (nb and b["start"] - last >= BREATHER_EVERY and b["shot"] == nb["shot"] and not b.get("chapter_card")
                and not nb.get("chapter_card") and not b.get("burst") and not nb.get("burst") and b["index"] > 0
                and BREATHER_LEN[0] <= nb["end"] - b["start"] <= BREATHER_LEN[1]):
            m = dict(b, end=nb["end"], words=b["words"] + nb["words"], text=(b["text"] + " " + nb["text"]).strip(),
                     breather=True)
            res.append(m)
            last = b["start"]
            i += 2
            continue
        res.append(b)
        i += 1
    for b in res:
        b["dur"] = round(b["end"] - b["start"], 3)
    return res


# -------------------------------------------------------------------------------------------------- roles
ROLE_RULES = [
    ("statistic", r"\b\d[\d,.]*\b|\bpercent\b|\b(hundred|thousand|million|billion|trillion|half|double|twice|"
                  r"times (more|less|faster|slower))\b"),
    ("comparison", r"\b(versus|vs\.?|compared|than|while|whereas|instead of|unlike|beats?|faster|slower|cheaper|"
                   r"better|worse|against)\b"),
    ("list", r"(\w+, \w+(,| and| or) \w+)|\b(first|second|third|three things|two things|several)\b"),
    ("process", r"\b(then|next|after that|step|finally|starts? with|first,)\b"),
    ("cause", r"\b(because|so that|which means|that means|leads? to|led to|thanks to|due to|as a result|therefore|"
              r"that's why|caused?)\b"),
    ("timeline", r"\b(19|20)\d\d\b|\b(nineteen|twenty) (\w+ )?\w+\b|\b(years? ago|last year|this year|since)\b"),
    ("definition", r"\b(is called|means|is a|is an|stands for|in other words)\b"),
    ("question", r"\?|\b(why|how come|what if|so what)\b"),
    ("warning", r"\b(but|warn\w*|risk\w*|problem\w*|careful|catch|danger\w*|downside|however)\b"),
    ("conclusion", r"\b(so|in the end|bottom line|verdict|overall|that's the|which is why|the answer)\b"),
]
ROLE_RULES = [(r, re.compile(p, re.I)) for r, p in ROLE_RULES]


def roles(beat) -> set:
    text = beat.get("text") or ""
    out = {r for r, rx in ROLE_RULES if rx.search(text)}
    if beat["kind"] == "quote":
        out.add("quote")
    if len(text.split()) <= 4 and not out:
        out.add("transition")
    if not out:
        out.add("story")
    return out


# ------------------------------------------------------------------------------------------- scene types
# name -> roles it serves (with weight), whether it shows data, how many layouts it has, the test that it can be
# drawn for this beat (returns a strength 0-1). Shot-bound types (number/quote/chart/title) come from the shot tag.
def _fits_memo(b, st):
    return 0.9 if T.MEMO_WORDS.search(b["text"]) else 0.0


def _fits_figure(b, st):
    return 0.55 if len(T.key_words([w[0] for w in b["words"]] or b["text"].split())) else 0.2


def _fits_kinetic(b, st):
    n = len(b["text"].split())
    punch = n <= 6 or b["text"].rstrip().endswith(("!", "?")) or "transition" in st["roles"] or \
        "conclusion" in st["roles"]
    return 0.6 if punch else 0.12


def _fits_country(b, st):
    return 1.0 if [c for c in X.countries(b["text"]) if c[0] not in st["countries"]] else 0.0


TYPES = {
    "figure": {"roles": {"story": 1.0, "question": 0.7, "warning": 0.6, "cause": 0.5, "definition": 0.5},
               "data": False, "fits": _fits_figure},
    "kinetic": {"roles": {"transition": 1.0, "conclusion": 0.8, "question": 0.6, "warning": 0.5}, "data": False,
                "fits": _fits_kinetic},
    "memo": {"roles": {"story": 0.6, "quote": 0.6, "warning": 0.5}, "data": False, "fits": _fits_memo},
    "map_flag": {"roles": {"story": 1.0, "comparison": 0.6, "timeline": 0.4}, "data": True, "fits": _fits_country},
    "timeline": {"roles": {"timeline": 1.0, "process": 0.5}, "data": True,
                 "fits": lambda b, st: 0.95 if X.years(b["text"]) else 0.0},
    "meter": {"roles": {"statistic": 1.0, "warning": 0.4}, "data": True,
              "fits": lambda b, st: 0.95 if (X.percent(b["text"]) is not None or
                                             re.search(r"\bbatter(y|ies)\b", b["text"], re.I)) else 0.0},
    "versus": {"roles": {"comparison": 1.0}, "data": True,
               "fits": lambda b, st: 0.95 if X.versus_sides(b["text"]) else 0.0},
    "icon_list": {"roles": {"list": 1.0, "process": 0.6}, "data": True,
                  "fits": lambda b, st: 0.9 if X.list_items(b["text"]) else 0.0},
    "pile": {"roles": {"statistic": 0.8}, "data": True,
             "fits": lambda b, st: 0.85 if X.pile_noun(b["text"]) else 0.0},
}
SHOT_BOUND = {"number": "number", "quote": "quote", "chart": "chart", "card": "title"}
LAYOUTS = {}               # name -> number of layouts (templates.layouts(); 3 until step 3)
TYPE_SHARE = 0.20
KINETIC_SHARE = 0.15
LAYOUT_USES = 6


def layouts_of(name: str) -> int:
    """Layouts of a type: the 13 older types have 6 (their 3 own arrangements, each also drawn in a frame)."""
    return LAYOUTS.get(name, 6)


def frame_of(name: str, seed: int) -> str:
    """The frame a type's layouts 3-5 use in this video (one per type, seeded)."""
    from . import compose
    return compose.FRAMES[_h(seed, "frame", name) % len(compose.FRAMES)]


def entrances(names: list, seed: int = 0, pool: list = None) -> list:
    """An entrance per scene from the pool (the format's motion language later), never the same twice in a row."""
    from . import compose
    pool = pool or compose.ENTRANCES
    out = []
    for i, n in enumerate(names):
        k = _h(seed, "ent", i) % len(pool)
        e = pool[k]
        if out and e == out[-1]:
            e = pool[(k + 1) % len(pool)]
        out.append(e)
    return out


def register(name: str, spec: dict, layouts: int = None) -> None:
    """New scene types add themselves here (step 4)."""
    TYPES[name] = spec
    if layouts:
        LAYOUTS[name] = layouts


def _chapter_lean(chapter_no: int, seed: int) -> dict:
    """Each chapter leans on a different part of the mix: a seeded boost for ~1/3 of the types."""
    names = sorted(TYPES)
    return {n: 0.15 for n in names if _h(seed, "lean", chapter_no, n) % 3 == 0}


def plan(beats: list, seed: int = 0, exclude: dict = None, weights: dict = None) -> tuple:
    """(names, info) for every beat. exclude = {beat index: {types not allowed there}} (e.g. a figure whose icon
    wasn't found). weights = {type: extra weight} from the video's format (step 5)."""
    n = len(beats)
    cap = max(2, math.floor(TYPE_SHARE * n))
    kcap = max(1, math.floor(KINETIC_SHARE * n))
    names, info, used = [], [], {}
    state = {"countries": set(), "last": {}}
    chapter_no = 0
    lean = _chapter_lean(0, seed)
    for i, b in enumerate(beats):
        extra = {}
        if b.get("chapter"):
            chapter_no += 1
            lean = _chapter_lean(chapter_no, seed)
        if b.get("chapter_card"):
            name = "chapter"
        elif b["index"] == 0 and b["kind"] in SHOT_BOUND:
            name = SHOT_BOUND[b["kind"]]
        else:
            st = {"roles": roles(b), "countries": state["countries"]}
            cands = []
            for t, spec in TYPES.items():
                if t in (exclude or {}).get(i, ()):
                    continue
                fit = spec["fits"](b, st)
                if fit <= 0:
                    continue
                role = max((spec["roles"].get(r, 0.0) for r in st["roles"]), default=0.0)
                score = fit * (0.5 + role) + lean.get(t, 0.0) + (weights or {}).get(t, 0.0) \
                    + (_h(seed, i, t) % 1000) / 1000 * 0.08
                cands.append((score, t))
            cands.sort(key=lambda x: (-x[0], x[1]))
            name = _choose(cands, names, used, cap, kcap) or "figure"
        if name == "map_flag":
            c = next((c for c in X.countries(b["text"]) if c[0] not in state["countries"]), None)
            if c is None:
                name = "figure"
            else:
                extra["country"] = c
                state["countries"].add(c[0])
        names.append(name)
        used[name] = used.get(name, 0) + 1
        info.append(extra)
    return names, info


def _choose(cands, names, used, cap, kcap):
    """The best candidate that keeps the budget; the rules are relaxed one by one when none does."""
    prev = names[-1] if names else None

    def abab(t):
        return len(names) >= 3 and names[-2] == t and names[-1] == names[-3]

    rules = [
        lambda t: t != prev and not abab(t) and used.get(t, 0) < (kcap if t == "kinetic" else cap)
        and used.get(t, 0) < LAYOUT_USES * layouts_of(t),
        lambda t: t != prev and used.get(t, 0) < (kcap if t == "kinetic" else cap),
        lambda t: t != prev and (t != "kinetic" or used.get(t, 0) < kcap),
        lambda t: t != prev,
    ]
    for ok in rules:
        for _s, t in cands:
            if ok(t):
                return t
    # nothing but the previous type fits: take the least used other drawable type
    for t in ("figure", "kinetic", "memo"):
        if t != prev:
            return t
    return None


def variants(names: list, seed: int = 0, recent: dict = None) -> list:
    """Layout per scene: each type walks through its layouts, starting where the last videos used it least."""
    count, out, start_of = {}, [], {}
    for n in names:
        base = "title" if n == "chapter" else n
        k = layouts_of(base)
        if base not in start_of:
            h = _h(seed, base)
            order = [(h + j) % k for j in range(k)]
            start_of[base] = min(order, key=lambda v: ((recent or {}).get(f"{base}:{v}", 0), order.index(v)))
        out.append((start_of[base] + count.get(base, 0)) % k)
        count[base] = count.get(base, 0) + 1
    return out


# -------------------------------------------------------------------------------------------- transitions
TRANSITIONS = ["cut", "fade", "push", "slide", "push_up", "blinds", "split", "whip", "zoom", "zoom_out", "flash",
               "glitch", "wipe"]
GROUPS = {"same": ["cut", "fade", "cut"],
          "next": ["push", "slide", "push_up", "blinds", "split"],
          "shot": ["whip", "zoom_out", "flash", "glitch", "push", "slide"],
          "reveal": ["zoom", "zoom_out"],
          "chapter": ["wipe"]}
TRANSITION_SHARE = 0.35


def relation(beats, names, i) -> str:
    b = beats[i]
    if b.get("chapter_card") or b.get("chapter"):
        return "chapter"
    prev = beats[i - 1]
    if names[i] in ("number", "chart", "meter") or prev["text"].rstrip().endswith("?"):
        return "reveal"
    if b["shot"] != prev["shot"]:
        return "shot"
    if not re.search(r"[.!?]$", prev["text"].rstrip()):
        return "same"
    return "next"


def transitions(beats: list, names: list, seed: int = 0, groups: dict = None, signature: str = "wipe") -> list:
    groups = dict(GROUPS, **(groups or {}))
    groups["chapter"] = [signature]
    out, used = [], {}
    n = max(1, len(beats))
    for i in range(len(beats)):
        if i == 0:
            out.append("cut")
            used["cut"] = used.get("cut", 0) + 1
            continue
        rel = relation(beats, names, i)
        opts = groups[rel]
        start = _h(seed, "tr", i) % len(opts)
        order = opts[start:] + opts[:start]
        pick = None
        for t in sorted(order, key=lambda t: (used.get(t, 0), order.index(t))):
            if rel == "chapter" or (used.get(t, 0) + 1) / n <= TRANSITION_SHARE and (not out or t != out[-1] or t == "cut"):
                pick = t
                break
        pick = pick or order[0]
        out.append(pick)
        used[pick] = used.get(pick, 0) + 1
    return out
