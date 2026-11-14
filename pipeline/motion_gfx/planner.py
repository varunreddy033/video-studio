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


def shot_bound(b, seed=0):
    """The scene type a shot tag's own graphic gets: quote shots alternate classic quote card / glass_quote, line-chart
    shots classic chart / chart_card (premium blocks), seeded per shot."""
    name = SHOT_BOUND[b["kind"]]
    alt = {"quote": "glass_quote", "chart": "chart_card"}.get(name)
    from . import premium_scenes as PS
    if alt and alt in TYPES and (name != "chart" or b.get("chart") == "line") and PS.long_enough(alt, b) \
            and _h(seed, "alt", b["shot"]) % 2:
        return alt
    return name
LAYOUTS = {}               # name -> number of layouts (default 6 = 3 own arrangements x frame)
OWN_LAYOUTS = {}           # name -> own arrangements (default 3); layout >= own = the same arrangement in a frame
NO_FRAME = set()           # types drawn edge to edge (premium blocks): one layout, never a frame behind them
TYPE_SHARE = 0.20
KINETIC_SHARE = 0.15
LAYOUT_USES = 6


def layouts_of(name: str) -> int:
    """Layouts of a type = its own arrangements x (plain + the 4 frames of compose.FRAMES): 15 for the 13 older
    types (3 arrangements), 10 for the newer ones (2)."""
    return own_of(name) * (1 if name in NO_FRAME else 5)


def own_of(name: str) -> int:
    return OWN_LAYOUTS.get("title" if name == "chapter" else name, 3)


def frame_of(name: str, seed: int, variant: int = None) -> str:
    """The frame of a layout: none for layouts 0..own-1, then each block of `own` layouts in the next frame (the
    order of the 4 frames is seeded per type)."""
    from . import compose
    own = own_of(name)
    if name in NO_FRAME or (variant is not None and variant < own):
        return None
    k = 0 if variant is None else variant // own - 1
    return compose.FRAMES[(_h(seed, "frame", name) + k) % len(compose.FRAMES)]


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


STRICT = {"timeline", "meter", "versus", "icon_list", "pile", "map_flag", "memo",
          # premium blocks that show the line's own data (a number, a list, a search...) or only come from shot tags
          "glass_quote", "chart_card", "odometer", "donut_card", "list_circle", "word_wheel", "color_carousel",
          "search_type", "post_card", "toggle", "card_flip", "card_wheel", "pill_split"}


def forced(beats: list, order: list) -> tuple:
    """scene_order: test reels: the given types in turn on every beat that isn't a chapter card or a shot tag's own
    graphic. A type that can't draw a beat's words still gets it (it falls back to the beat's phrase)."""
    names, info, k, used = [], [], 0, set()
    for b in beats:
        if b.get("chapter_card"):
            names.append("chapter")
        elif b["index"] == 0 and b["kind"] in SHOT_BOUND:
            names.append(shot_bound(b))
        else:
            # the next type in the order that can draw this line; the strict data templates (they need a year, a
            # percent, two sides, a list...) wait for a line that has it
            queue = [order[(k + j) % len(order)] for j in range(len(order))]
            st = {"roles": roles(b), "countries": used}
            pick = next((t for t in queue if t in STRICT and t in TYPES and TYPES[t]["fits"](b, st) > 0), None) or \
                next((t for t in queue if t not in STRICT), None)       # a data type that fits this line goes first
            if pick is None:
                pick = next((t for t in ("figure", "kinetic") if t in queue), "kinetic")
            else:
                j = queue.index(pick)
                order = order[:]                       # move the picked type to position k (keeps the rest in turn)
                order.insert(k % len(order), order.pop((k + j) % len(order)))
            names.append(pick)
            k += 1
        extra = {}
        if names[-1] == "map_flag":
            c = next((c for c in X.countries(b["text"]) if c[0] not in used), None)
            if c:
                extra["country"] = c
                used.add(c[0])
            else:
                names[-1] = "globe"
        info.append(extra)
    return names, info


def plan(beats: list, seed: int = 0, exclude: dict = None, weights: dict = None, order: list = None) -> tuple:
    """(names, info) for every beat. exclude = {beat index: {types not allowed there}} (e.g. a figure whose icon
    wasn't found). weights = {type: extra weight} from the video's format (step 5)."""
    if order:
        return forced(beats, order)
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
            name = shot_bound(b, seed)
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
            banned = (exclude or {}).get(i, set())
            name = _choose(cands, names, used, cap, kcap, banned) or next(
                t for t in ("figure", "kinetic", "magnifier") if t not in banned)
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


def _choose(cands, names, used, cap, kcap, banned=()):
    """The best candidate that keeps the budget; the rules are relaxed one by one when none does."""
    prev = names[-1] if names else None

    def abab(t):
        return len(names) >= 3 and names[-2] == t and names[-1] == names[-3]

    kin_ok = lambda t: t != "kinetic" or used.get(t, 0) < kcap                          # noqa: E731
    lay_ok = lambda t: used.get(t, 0) < LAYOUT_USES * layouts_of(t)                      # noqa: E731
    rules = [
        lambda t: t != prev and not abab(t) and used.get(t, 0) < (kcap if t == "kinetic" else cap)
        and used.get(t, 0) < LAYOUT_USES * layouts_of(t),
        lambda t: t != prev and not abab(t) and used.get(t, 0) < (kcap if t == "kinetic" else cap) and lay_ok(t),
        lambda t: t != prev and not abab(t) and kin_ok(t) and lay_ok(t),
        lambda t: t != prev and not abab(t) and kin_ok(t),
        lambda t: t != prev and kin_ok(t),
        lambda t: t != prev and t != "kinetic",
        lambda t: t != prev,
    ]
    for ok in rules:
        for _s, t in cands:
            if ok(t):
                if t == "kinetic" and not kin_ok(t):      # words over their cap: a headline scene instead
                    for alt in ("reaction", "magnifier", "newspaper", "title_card"):
                        if alt != prev and alt in TYPES and alt not in banned and not abab(alt):
                            return alt
                return t
    # nothing but the previous type fits: take the least used other drawable type
    for t in ("figure", "kinetic", "magnifier", "memo"):
        if t != prev and t not in banned:
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
               "glitch", "wipe", "whip_blur", "zoom_blur", "zoom_through", "spin", "light_leak", "film_burn",
               "rgb_split", "cube", "flip", "page_curl", "ink", "luma_wipe", "shape"]
GROUPS = {"same": ["cut", "fade", "cut"],
          "next": ["push", "slide", "push_up", "blinds", "split", "luma_wipe", "shape"],
          "shot": ["whip_blur", "zoom_blur", "cube", "spin", "flash", "glitch", "push", "light_leak"],
          "reveal": ["zoom", "zoom_through", "zoom_out"],
          "chapter": ["wipe"]}
TRANSITION_SHARE = 0.35
# transitions: <set> in the header (a named set or a comma list of transition names)
TRANSITION_SETS = {
    "3d": ["cube", "flip", "page_curl", "spin", "zoom_through"],
    "film": ["light_leak", "film_burn", "whip_blur", "zoom_blur", "fade"],
    "clean": ["cut", "fade", "push", "slide", "luma_wipe"],
    "glitch": ["rgb_split", "glitch", "zoom_blur", "flash"],
    "popular": ["whip_blur", "zoom_blur", "zoom_through", "spin", "light_leak", "cube", "luma_wipe", "ink", "shape"],
}


def parse_transitions(value) -> tuple:
    """transitions: header -> (mode, allowed list or None, bad names). mode = auto | off | pool."""
    raw = [x.strip().lower() for x in str(value or "").split(",") if x.strip()]
    if not raw or raw == ["auto"]:
        return "auto", None, []
    if raw == ["off"]:
        return "off", None, []
    allowed, bad = [], []
    for x in raw:
        if x in TRANSITION_SETS:
            allowed += TRANSITION_SETS[x]
        elif x in _all_transitions():
            allowed.append(x)
        else:
            bad.append(x)
    return "pool", list(dict.fromkeys(allowed)) or None, bad


def _all_transitions():
    from . import transitions as Tr
    return Tr.ALL


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


def transitions(beats: list, names: list, seed: int = 0, groups: dict = None, signature: str = "wipe",
                choice=None) -> list:
    """choice = the transitions: header (auto = the format's groups, off = all cuts, a set/list = only those)."""
    mode, allowed, _bad = parse_transitions(choice)
    if mode == "off":
        return ["cut"] * len(beats)
    groups = dict(GROUPS, **(groups or {}))
    groups["chapter"] = [signature]
    if allowed:
        base = dict(groups)
        for k in list(groups):
            pool = list(dict.fromkeys(base[k] + GROUPS.get(k, [])))
            keep = [t for t in pool if t in allowed]
            groups[k] = keep or ([t for t in allowed if t != "cut"] or allowed)
        placed = {t for k in ("same", "next", "shot", "reveal") for t in groups[k]}
        rest = [t for t in allowed if t not in placed and t != "cut"]
        for k in ("next", "shot"):           # names the groups don't know go where scenes change
            groups[k] = groups[k] + rest
        if "cut" not in allowed:
            groups["same"] = [t for t in groups["same"] if t != "cut"] or groups["same"]
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


# ------------------------------------------------------------------------------------------------ cameras
CAMERA_BY_JOB = {           # what a scene does -> the moves that suit it (first = strongest fit)
    "reveal": ["dolly", "vertigo", "pull"],
    "chapter": ["tilt", "pull", "orbit"],
    "breather": ["orbit", "truck", "dolly"],
    "burst": ["handheld", "dolly", "truck"],
    "read": ["focus", "dolly", "truck"],
    "data": ["truck", "orbit", "dolly", "tilt"],
    "warning": ["vertigo", "handheld", "dolly"],
}
READ_TYPES = {"quote", "memo", "newspaper", "chat", "browser", "phone", "terminal", "sticky"}


def _camera_job(b, name):
    if b.get("chapter_card") or name == "chapter":
        return "chapter"
    if b.get("breather"):
        return "breather"
    if name in ("number", "chart", "meter", "countdown", "donut"):
        return "reveal"
    if name in READ_TYPES:
        return "read"
    if b.get("burst"):
        return "burst"
    from . import variety as V
    if name in V.DATA_TYPES:
        return "data"
    if "warning" in roles(b):
        return "warning"
    return None


def cameras(beats: list, names: list, seed: int = 0, pool: list = None, choice=None) -> list:
    """A camera move per scene (camera.py). choice = the camera: header: auto = by the scene's job inside the format's
    pool, off / flat = that everywhere, a name or list = only those. Never the same move twice in a row, no move
    above camera.SHARE of the scenes."""
    from . import camera as Cam
    mode, pinned, _bad = Cam.parse_setting(choice)
    if mode in ("off", "flat"):
        return [mode] * len(beats)
    pool = pinned or pool or Cam.DEFAULT_POOL
    if len(pool) == 1:
        return [pool[0]] * len(beats)
    cap = max(2, math.ceil(Cam.SHARE * max(1, len(beats))))
    out, used = [], {}
    for i, (b, nm) in enumerate(zip(beats, names)):
        job = _camera_job(b, nm)
        pref = [m for m in CAMERA_BY_JOB.get(job, []) if m in pool]
        start = _h(seed, "cam", i) % len(pool)
        rest = pool[start:] + pool[:start]
        order = pref + [m for m in rest if m not in pref]
        pick = next((m for m in order if (not out or m != out[-1]) and used.get(m, 0) < cap), None) or \
            next((m for m in order if not out or m != out[-1]), order[0])
        out.append(pick)
        used[pick] = used.get(pick, 0) + 1
    from . import premium_scenes as PS
    for i, nm in enumerate(names):
        if nm in PS.NO_CAMERA:
            out[i] = "off"
        elif nm in PS.NAMES and out[i] not in PS.SAFE_CAMERAS:
            out[i] = "pull" if (i and out[i - 1] == "dolly") else "dolly"
    return out


from . import scenes as _scenes  # noqa: E402  (the 24 newer scene types register themselves)
_scenes.register()
from . import premium_scenes as _premium  # noqa: E402  (the 19 premium blocks)
_premium.register()
from . import type_scenes as _type_scenes  # noqa: E402  (Type Studio's typographic scenes)
_type_scenes.register()
