"""Which icon every scene of a motion-graphics video shows (docs/ASSET_PACKS_PLAN.md section 3).

  topic pool     the script's key nouns -> the ~60 icons of the video's family that fit them best (shown on the
                 Check page; `icons_pin:` adds icons, `icons_ban:` removes them)
  ranking        every scene that wants an icon ("need") asks with its words: the key phrase, each content word, the
                 whole clause, and what the old RULES table knew (chips -> a computer chip). Score = sentence
                 similarity (icon_index) + a bonus when a spoken word IS the icon's name + a bonus for pool icons
  no repeats     one icon is used once in a video (`icon_reuse: 2` allows twice)
  cooldown       question-style icons (question / exclamation marks, thinking faces, shrugs, magnifiers ...) at most
                 one a minute and three in a video
  no default     a scene without a good match takes the best unused pool icon; when nothing is left it gets no icon
                 and the renderer shows kinetic words instead. There is no question-mark / exclamation fallback.
  freshness      icons of the last videos (data/asset_history.json, step 4) rank a little lower
  deterministic  scores are rounded, every tie is broken by scene order and icon id: same script = same icons

plan(beats, names, meta) is used by the renderer (real voice timings) and by the Check page (estimated timings).
"""

import base64
from functools import lru_cache
import re

from .. import icon_index as IX
from .. import icon_library as L
from ..util import PipelineError
from . import templates as T

DEFAULT_FAMILY = "fluent_flat"
MATCH_MIN = 0.50          # a scene's own match must score at least this
NEAR_MIN = 0.44           # second round, for scenes that found nothing: a looser match
POOL_MIN = 0.36           # a topic noun's icon must score at least this to enter the pool
POOL_SIZE = 60
POOL_PER_NOUN = 6         # for the 8 main nouns; the others give 2
POOL_FILL_MIN = 0.30      # a pool icon must fit the scene at least this much to fill it
NOUNS = 20
QUESTION_GAP = 60.0       # seconds between two question-style icons
QUESTION_MAX = 3
TOP_K = 40                # candidates kept per need

QUESTION = re.compile(r"question|exclamation|thinking|monocle|thought-balloon|shrug|raised-eyebrow|confused|puzzle|"
                      r"magnifying|raising-hand|interrobang|zany|exploding-head|face-with-open-mouth|astonished|"
                      r"hushed|anguished|flushed")
BORING = re.compile(
    r"^keycap|button|square|circle|diamond-|-diamond|oclock|-thirty$|triangle|arrow|^input-|^japanese|^flag|^ram$|"
    r"^(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces|ophiuchus)$|"
    r"^(man|woman|men|women|boy|girl|family|couple|kiss|people|person)-|^(man|woman|boy|girl|person)$|"
    r"-moon$|^moon-|^regional|^skin-tone|-skin-tone|^(red|blue|green|black|white|orange|yellow|purple|brown)-heart$|"
    r"^cl-|^sos-|^up-|^ng-|^ok-|^new-|^free-|^cool-|^id-|^vs-|^atm|^end-|^back-|^on-|^soon-|^top-|"
    r"^(hundred-points|anger-symbol|dotted-line-face|part-alternation-mark|wavy-dash|curly-loop|double-curly-loop|"
    r"eight-pointed-star|eight-spoked-asterisk|sparkle|copyright|registered|trade-mark|name-badge|"
    r"white-flower|diamond-with-a-dot|trident-emblem|fleur-de-lis|menorah|star-of-david|dotted-six-pointed-star|"
    r"om|wheel-of-dharma|yin-yang|latin-cross|orthodox-cross|star-and-crescent|peace-symbol|place-of-worship|"
    r"atom-symbol|khanda|medical-symbol|male-sign|female-sign|transgender-symbol|kaaba|mosque|synagogue|"
    r"hindu-temple|church|shinto-shrine|prayer-beads|pile-of-poo|middle-finger|bikini|briefs|lipstick|kiss-mark|"
    r"syringe|pill|drop-of-blood|coffin|funeral-urn|headstone|cigarette|water-pistol|bomb|pistol|dagger|"
    r"crossed-swords|baby-bottle|breast-feeding|pregnant-.*|toilet|roll-of-paper|plunger|condom)$")
FACES = ("Smileys & Emotion", "People & Body")          # ranked a little lower: a generic face/person rarely fits
NUMBER_WORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                   "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred "
                   "thousand million billion trillion first second third half percent".split())
FILLER = set("running runs thing things people person year years time times day days way ways lot kind sort part number "
             "something anything everything nothing someone anyone everyone right left back well let lets "
             "pull need know think thought want mean means point reason reasons story fact truth idea frankly "
             "meanwhile already never ever always actually simply exactly almost around between during without "
             "became become becomes started stopped put putting come comes goes going went gone getting gets "
             "used using uses made make makes took take takes found find finds little big small more most less "
             "least many few own sterling isnt dont doesnt cant wont didnt arent wasnt work works keep keeps explained explain here there week pair lost wearing wear wore worn thats youre theyre best better good great real true whole same other another every each still even just only also again last next new old".split())
# words that are also an icon's name but nearly never mean it (fly = the insect, shorts = the clothes ...)
AMBIGUOUS = set("fly short rose box jack case light right watch chip trap honey match bug cell mouse".split())
# what the old RULES table showed for a clause -> words to search with (question / exclaim are not searched)
HINTS = {"chip": "computer chip", "globe": "globe world", "ship": "cargo ship", "heart": "love heart",
         "building": "office building", "money": "money bag", "lock": "locked padlock", "camera": "camera photo",
         "chart_up": "chart increasing", "chart_down": "chart decreasing", "magnifier": "detective investigation",
         "phone": "mobile phone call", "eye": "spy detective"}
SOUNDS = [(r"coin", "coin-drop"), (r"money|dollar|bank|cash|credit|purse|gem", "cash"),
          (r"camera|video|film|movie", "shutter"), (r"phone|bell|envelope|e-mail|incoming|inbox", "notification"),
          (r"door", "door"), (r"trophy|medal|party|confetti|clapping|crown", "success"),
          (r"computer|laptop|keyboard|mouse|disk|plug|battery|headphone|radio|television|joystick", "click"),
          (r"warning|siren|prohibited|entry|skull|fire|collision|bell|alarm", "alert"),
          (r"chart|rocket|airplane|car|train|ship|bicycle|running|dashing|wind|comet", "whoosh"),
          (r"page|newspaper|scroll|memo|book|envelope|clipboard|receipt|label|file|card", "paper"),
          (r"trophy|medal|star|crown|party|confetti|sparkles|check|light-bulb|heart|ribbon", "ding"),
          (r"hammer|axe|pick|wrench|stamp|scissors|brick|rock|door|package", "impact")]


def stem(w: str) -> str:
    w = w.lower()
    for suf in ("'s", "’s"):
        if w.endswith(suf):
            w = w[:-2]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("es") and w[-3] in "sxz":
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


NAME = re.compile(r"\b[A-Z][a-z]+-[A-Z][a-z]+\b|(?<![.!?:]\s)(?<!^)\b[A-Z][a-z]+(?:[-'’][A-Za-z]+)*\b|\b[A-Z]{2,}[a-z]*\b")


import contextvars  # noqa: E402

# names the whole video capitalises mid-sentence ("Apple", "Windows"): names at the start of a clause too (plan() sets
# it per render / Check; a ContextVar so two threads never share it)
VIDEO_NAMES = contextvars.ContextVar("video_names", default=frozenset())


def video_names(texts) -> frozenset:
    out = set()
    for t in texts:
        for m in NAME.finditer(t.strip()):
            w = m.group(0)
            if w.lower() not in T.STOP and len(w) >= 3:
                out.add(w)
    return frozenset(out)


def without_names(text: str) -> str:
    """The clause without names: "Apple", "Lily-Rose Depp", "Bose" mean a company or a person, not an apple or a rose.
    A capitalised word counts as a name unless it starts the clause or a sentence; a word the video capitalises
    mid-sentence elsewhere (VIDEO_NAMES) is a name everywhere."""
    t = NAME.sub(" ", text.strip())
    known = VIDEO_NAMES.get()
    if known:
        t = re.sub(r"\b(" + "|".join(re.escape(w) for w in sorted(known)) + r")\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def content_words(text: str, names: bool = False) -> list:
    """The words of a clause worth searching an icon for, in spoken order (no repeats). Names are left out unless
    names=True."""
    out = []
    for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", text if names else without_names(text)):
        lw = w.lower().strip("'’-").replace("'", "").replace("’", "")
        if len(lw) < 3 or lw in T.STOP or lw in T.WEAK or lw in NUMBER_WORDS or lw in FILLER or stem(lw) in FILLER:
            continue
        if lw not in out:
            out.append(lw)
    return out


def is_question(icon_id: str) -> bool:
    return bool(QUESTION.search(icon_id.split(":", 1)[1]))


def sound_for(icon_id: str) -> str:
    name = icon_id.split(":", 1)[1]
    for rx, kind in SOUNDS:
        if re.search(rx, name):
            return kind
    return "pop"


def data_uri(icon_id: str, colour: str = "#111111") -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(L.svg(icon_id, colour).encode("utf-8")).decode("ascii")


def family_of(meta: dict) -> str:
    fam = (meta.get("icons") or "").strip().lower() or meta.get("look_icons") or DEFAULT_FAMILY
    usable = L.usable_families()
    if not usable:
        raise PipelineError("motion graphics need the icon packs, and none are imported on this machine. Run once in "
                            "the project folder: npm ci && bin/python tools/import_icon_packs.py")
    if fam not in usable:
        raise PipelineError(f"icons: '{fam}' isn't an imported icon family. Use one of: {', '.join(usable)}")
    return fam


def id_list(value, family: str) -> list:
    """`icons_pin:` / `icons_ban:` values -> icon ids ("low-battery, noto:rocket" -> ids; bare names = the family)."""
    out = []
    for part in re.split(r"[,\s]+", str(value or "").strip()):
        if part:
            out.append(part if ":" in part else f"{family}:{part}")
    return out


def figure_need(i: int, beat: dict) -> dict:
    """What a figure scene asks the picker for: one icon that shows what the clause is about."""
    text = beat["text"]
    qs = []
    phrase = " ".join(w for w in T.key_phrase(text, 3).lower().split() if w in content_words(text))
    if phrase:
        qs.append((phrase, 1.0))
    for w in content_words(text):
        if stem(w) not in AMBIGUOUS:
            qs.append((w, 0.94))
    if len(content_words(text)) >= 2:
        qs.append((without_names(text).strip(" .,;:!?").lower(), 0.86))
    for rx, (_pose, _outfit, props, _two) in T.RULES:
        if rx.search(text):
            qs += [(HINTS[p], 0.98) for p in props if p in HINTS]
            break
    return {"beat": i, "slot": 0, "t": beat["start"], "queries": qs, "words": {stem(w) for w in content_words(text)},
            "required": False, "text": text}


def topic_nouns(meta: dict, beats: list) -> list:
    """The ~18 words the video is about: title and tag words first, then the most repeated content words."""
    score, first = {}, {}
    order = 0

    def add(text, weight, with_names=False):
        nonlocal order
        for w in content_words(text, with_names):
            s = stem(w)
            score[s] = score.get(s, 0) + weight
            first.setdefault(s, order)
            order += 1

    caps, lower = {}, {}
    for b in beats:                                   # a word is a name when it is mostly said capitalised
        for m in NAME.finditer(b["text"]):
            for p in re.split(r"[-'’]", m.group(0)):
                caps[stem(p.lower())] = caps.get(stem(p.lower()), 0) + 1
        for w in re.findall(r"\b[a-z][a-z'’-]+\b", b["text"]):
            lower[stem(w)] = lower.get(stem(w), 0) + 1
    names = {w for w, c in caps.items() if c > lower.get(w, 0)}
    add(meta.get("title", ""), 3, True)
    add(str(meta.get("tags", "")).replace(",", " "), 2)
    for b in beats:
        add(b["text"], 1)
    for w in names:
        score.pop(w, None)
    keep = [w for w in score if score[w] >= 2 and len(w) >= 4 and (w not in AMBIGUOUS or w in HINTS)]
    keep.sort(key=lambda w: (-score[w], first[w], w))
    # an ambiguous word with a hint is searched as the hint ("chip" -> "computer chip", not a chipmunk)
    return [HINTS[w] if w in AMBIGUOUS else w for w in keep[:NOUNS]]


def _candidates(family: str, banned: set):
    rows, _emb, _pos = IX.load()
    out = []
    for i, r in enumerate(rows):
        if r["set"] != family or r["id"] in banned or BORING.search(r["name"]):
            continue
        if r["category"] in ("Flags",):
            continue
        out.append(i)
    if not out:
        raise PipelineError(f"the icon family '{family}' has no usable icons in the index. Run: "
                            f"bin/python tools/build_icon_index.py --force")
    return rows, out


COMPANION_MIN = 0.60       # a companion-set icon must fit a topic word at least this well
COMPANION_GAP = 0.45       # ... and the family's own best for that word must be under this


@lru_cache(maxsize=1)
def _sets_index():
    rows, _, _ = IX.load()
    out = {}
    for i, r in enumerate(rows):
        out.setdefault(r["set"], []).append(i)
    return out


def _companion(family: str, nouns: list, rows, emb, cand: list, banned: set):
    """Topic words the family can't draw (Fluent / Noto have no computer chip): one other colour illustration set
    per video lends its best icon for each such word. Returns (extra row indices, companion set id or None)."""
    import numpy as np
    if not nouns:
        return [], None
    vec = IX.embed(nouns)

    def bonus(n, ii):
        ws = {stem(n.split()[-1])}                 # the head word: "computer chip" -> chip (exact name word)
        return np.array([0.16 if ws & {stem(w) for w in rows[i]["name"].split("-")} else 0.0 for i in ii])
    fam_sc = vec @ np.asarray(emb[cand], dtype="float32").T
    fam = [float((fam_sc[j] + bonus(n, cand)).max()) for j, n in enumerate(nouns)]
    missing = [(n, v) for n, v, b in zip(nouns, vec, fam) if b < COMPANION_GAP and len(n) >= 4]
    if not missing:
        return [], None
    sets = [k for k, v in L.PACKS.items() if v.get("kind") == "illustration" and k != family and k in L.installed()
            and not v.get("archive") and v.get("category") != "Holiday / Seasonal"
            and L.ALLOWED.get(L.load(k)["licence"]) == "free"]
    idx = _sets_index()
    best_set, best_total, best_pick = None, 0.0, []
    for sid in sorted(sets):
        ii = [i for i in idx.get(sid, []) if rows[i]["id"] not in banned and not BORING.search(rows[i]["name"])]
        if not ii:
            continue
        sc = np.stack([v for _n, v in missing]) @ np.asarray(emb[ii], dtype="float32").T
        pick, total = [], 0.0
        for j, (n, _v) in enumerate(missing):
            row = (sc[j] + bonus(n, ii)).round(4)
            k = int(max(range(len(ii)), key=lambda q: (float(row[q]), -q)))
            if row[k] >= COMPANION_MIN:
                pick.append(ii[k])
                total += float(row[k])
        if total > best_total + 1e-6:
            best_set, best_total, best_pick = sid, total, pick
    return sorted(set(best_pick)), best_set


def plan(beats: list, names: list, meta: dict, history: dict = None, needs: list = None) -> dict:
    """Icons for a whole video.

    beats   the video's beats (text, start, end)            names  the template of every beat
    needs   optional extra needs from other templates (step 5); figure scenes are added here
    Returns {"family", "picks": {(beat, slot): {"id", "score", "how"}}, "pool": [...], "nouns": [...], "report": {...}}.
    """
    import numpy as np
    VIDEO_NAMES.set(video_names([" ".join(b["text"] for b in beats)]))     # joined: clause starts aren't starts
    family = family_of(meta)
    banned = set(id_list(meta.get("icons_ban"), family))
    pins = [p for p in id_list(meta.get("icons_pin"), family) if p not in banned]
    reuse = max(1, int(meta.get("icon_reuse") or 1))
    rows, cand = _candidates(family, banned)
    _, emb, pos = IX.load()
    extra, companion = _companion(family, topic_nouns(meta, beats), rows, emb, cand, banned)
    cand = cand + extra
    missing = [p for p in pins if p not in pos]
    if missing:
        raise PipelineError(f"icons_pin: no such icon: {', '.join(missing)}. Search with: "
                            f"bin/python tools/icon_search.py \"words\" --set {family}")
    cand_emb = np.asarray(emb[cand], dtype="float32")
    cand_ids = [rows[i]["id"] for i in cand]
    name_words = [{stem(w) for w in rows[i]["name"].split("-")} for i in cand]
    name_last = [stem(rows[i]["name"].split("-")[-1]) for i in cand]
    key_words = [{stem(w) for w in rows[i]["words"]} for i in cand]
    face = np.array([0.07 if rows[i]["category"] in FACES else 0.0 for i in cand], dtype="float32")
    stale = (history or {}).get("icons", {})
    fresh = np.array([0.05 if cid in stale else 0.0 for cid in cand_ids], dtype="float32")

    all_needs = list(needs or [])
    for i, (b, n) in enumerate(zip(beats, names)):
        if n == "figure":
            all_needs.append(figure_need(i, b))
        elif n == "kinetic" and not b.get("chapter_card"):    # words scenes take an icon only on a strong match
            all_needs.append(dict(figure_need(i, b), optional=True))
    all_needs.sort(key=lambda n: (n["beat"], n["slot"]))
    nouns = topic_nouns(meta, beats)

    texts = sorted({q for n in all_needs for q, _ in n["queries"]} | set(nouns))
    vec = IX.embed(texts) if texts else np.zeros((0, cand_emb.shape[1]), dtype="float32")
    at = {t: k for k, t in enumerate(texts)}
    sim = (vec @ cand_emb.T).round(4) if texts else np.zeros((0, len(cand)), dtype="float32")

    def lexical(words):
        out = np.zeros(len(cand), dtype="float32")
        for k in range(len(cand)):
            if any(w != nw and nw.startswith(w) and len(w) >= 3 for w in words for nw in name_words[k]) and \
                    not (words & name_words[k]):
                out[k] = -0.15                     # "chip" is not a chipmunk, "ear" is not an ear of corn
                continue
            hit = (words - AMBIGUOUS) & name_words[k]
            if hit and (len(name_words[k]) == 1 or name_last[k] in hit):
                out[k] = 0.16                      # "battery" said, the icon IS a battery
            elif hit:
                out[k] = 0.05
            elif (words - AMBIGUOUS) & key_words[k]:
                out[k] = 0.04
        return out

    # topic pool: round-robin over the nouns so every topic gets its best icons before any gets a fifth
    pool, pool_noun = [], {}
    per_noun = []
    for noun in nouns:
        sc = sim[at[noun]] + lexical({noun}) - face
        order = sorted(range(len(cand)), key=lambda k: (-float(sc[k]), cand_ids[k]))[:POOL_PER_NOUN]
        order = order[:POOL_PER_NOUN if len(per_noun) < 8 else 2]
        per_noun.append([(k, float(sc[k])) for k in order
                         if sc[k] >= POOL_MIN and not QUESTION.search(rows[cand[k]]["name"])])
    for rank in range(POOL_PER_NOUN):
        for noun, lst in zip(nouns, per_noun):
            if rank < len(lst) and len(pool) < POOL_SIZE and lst[rank][0] not in pool_noun:
                pool.append(lst[rank][0])
                pool_noun[lst[rank][0]] = noun
    k_of = {cid: k for k, cid in enumerate(cand_ids)}
    for p in pins:
        if p in k_of and k_of[p] not in pool_noun:
            pool.append(k_of[p])
            pool_noun[k_of[p]] = "pinned"
    in_pool = np.zeros(len(cand), dtype="float32")
    for k in pool:
        in_pool[k] = 0.04
    for p in pins:
        if p in k_of:
            in_pool[k_of[p]] = 0.12

    # every need's scores
    scored = []
    for n in all_needs:
        if not n["queries"]:
            scored.append(None)
            continue
        best = np.max(np.stack([sim[at[q]] * w for q, w in n["queries"]]), axis=0)
        opt = 0.03 if n.get("optional") else 0.0                 # scenes that need an icon choose first
        scored.append((best + lexical(n["words"]) + in_pool - face - fresh - opt).round(4))

    used, picks, q_times = {}, {}, []

    def allowed(k, t):
        if used.get(k, 0) >= reuse:
            return False
        if QUESTION.search(rows[cand[k]]["name"]):
            if len(q_times) >= QUESTION_MAX or any(abs(t - x) < QUESTION_GAP for x in q_times):
                return False
        return True

    def take(ni, k, score, how):
        n = all_needs[ni]
        used[k] = used.get(k, 0) + 1
        if QUESTION.search(rows[cand[k]]["name"]):
            q_times.append(n["t"])
        picks[(n["beat"], n["slot"])] = {"id": cand_ids[k], "score": round(float(score), 4), "how": how,
                                         "noun": pool_noun.get(k, "")}

    # 1 global greedy: the best (scene, icon) pairs first
    pairs = []
    for ni, sc in enumerate(scored):
        if sc is None:
            continue
        top = sorted(range(len(cand)), key=lambda k: (-float(sc[k]), cand_ids[k]))[:TOP_K]
        pairs += [(-float(sc[k]), ni, cand_ids[k], k) for k in top if sc[k] >= MATCH_MIN]
    pairs.sort()
    done = set()
    for neg, ni, _cid, k in pairs:
        if ni in done or not allowed(k, all_needs[ni]["t"]):
            continue
        take(ni, k, -neg, "match")
        done.add(ni)
    # 2 scenes that found nothing: a looser match, best pairs first
    pairs = []
    for ni, sc in enumerate(scored):
        if sc is None or ni in done:
            continue
        top = sorted(range(len(cand)), key=lambda k: (-float(sc[k]), cand_ids[k]))[:TOP_K]
        pairs += [(-float(sc[k]), ni, cand_ids[k], k) for k in top if sc[k] >= NEAR_MIN]
    pairs.sort()
    for neg, ni, _cid, k in pairs:
        if ni in done or all_needs[ni].get("optional") or not allowed(k, all_needs[ni]["t"]):
            continue
        take(ni, k, -neg, "near")
        done.add(ni)
    # 3 still nothing: the best unused pool icon for their words (scene order)
    for ni, n in enumerate(all_needs):
        if ni in done or n.get("optional"):
            continue
        sc = scored[ni]
        if sc is None:
            continue
        free = [k for k in pool if allowed(k, n["t"]) and sc[k] >= POOL_FILL_MIN]
        if not free:
            continue
        k = min(free, key=lambda k: (-float(sc[k]), cand_ids[k]))
        take(ni, k, float(sc[k]), "pool")
        done.add(ni)

    rep = report(beats, names, all_needs, picks, family, [cand_ids[k] for k in pool])
    rep["companion"] = companion
    return {"family": family, "picks": picks, "nouns": nouns, "companion": companion,
            "pool": [{"id": cand_ids[k], "noun": pool_noun[k]} for k in pool],
            "report": rep}


def plan_video(beats: list, meta: dict, seen: dict, seed: int):
    """Templates, layout variants and icons of a whole video, settled together (renderer and Check page).

    A newer template whose required icons can't all be found (a list item with no good icon) becomes plain kinetic
    words (or a figure scene when the neighbour is already words) and the icons are planned again; a figure scene
    without an icon becomes kinetic words. Returns (names, variants, info, plan)."""
    from . import extras as X
    from . import planner as PL
    exclude = {i: set(meta.get("format_banned") or []) for i in range(len(beats))}
    order = [x.strip().lower() for x in str(meta.get("scene_order") or "").split(",") if x.strip()] or None
    names, info = PL.plan(beats, seed, exclude, meta.get("format_weights"), order)
    p = None
    for _round in range(5):
        extra = [n for i, (b, nm) in enumerate(zip(beats, names)) if nm in X.NEW for n in X.needs(i, b, nm)]
        p = plan(beats, names, meta, seen, extra)
        changed = False
        for i, nm in enumerate(names):          # a scene whose icons weren't found: plan that beat again without it
            missing = (nm in X.NEW and any((i, n["slot"]) not in p["picks"] for n in extra
                                           if n["beat"] == i and n["required"])) or \
                      (nm == "figure" and (i, 0) not in p["picks"])
            if missing:
                exclude.setdefault(i, set()).add(nm)
                changed = True
        if not changed or order:
            break
        names, info = PL.plan(beats, seed, exclude, meta.get("format_weights"))
    for i, n in enumerate(names):            # still no icon for a figure scene -> kinetic words, if that keeps the
        if n == "figure" and (i, 0) not in p["picks"]:          # words cap and no two word scenes touch
            near = [names[j] for j in (i - 1, i + 1) if 0 <= j < len(names)]
            if "kinetic" not in near and names.count("kinetic") < max(1, int(PL.KINETIC_SHARE * len(names))):
                names[i] = "kinetic"
    for r in p["report"]["rows"]:
        r["template"] = names[r["beat"]]
    p["report"]["templates"] = {n: names.count(n) for n in sorted(set(names))}
    return names, PL.variants(names, seed, (seen or {}).get("templates")), info, p


def report(beats, names, needs, picks, family, pool, rows=None) -> dict:
    """The repetition report of the Check page and the render log."""
    counts = {}
    for p in picks.values():
        counts[p["id"]] = counts.get(p["id"], 0) + 1
    most = max(sorted(counts), key=lambda i: counts[i]) if counts else ""
    with_icon = {b for b, _ in picks}
    if rows is None:
        rows = []
        for n in needs:
            p = picks.get((n["beat"], n["slot"]))
            rows.append({"beat": n["beat"], "slot": n["slot"], "t": round(n["t"], 1), "text": n["text"],
                         "icon": p["id"] if p else "", "score": p["score"] if p else 0, "how": p["how"] if p else "none",
                         "template": names[n["beat"]]})
    else:
        rows = [r if (r["beat"], r.get("slot", 0)) in picks else dict(r, icon="", score=0, how="none") for r in rows]
    return {"family": family, "beats": len(beats), "wanted": len(needs), "icons": len(counts),
            "placed": len(picks), "most_used": {"id": most, "count": counts.get(most, 0)},
            "question_style": sum(c for i, c in counts.items() if is_question(i)),
            "question_ids": sorted(i for i in counts if is_question(i)),
            "beats_with_icon": len(with_icon), "percent_with_icon": round(100 * len(with_icon) / max(1, len(beats))),
            "matched": sum(1 for p in picks.values() if p["how"] in ("match", "near")),
            "from_pool": sum(1 for p in picks.values() if p["how"] == "pool"),
            "without": [r["beat"] for r in rows if not r["icon"]], "pool_used": sum(1 for i in pool if i in counts),
            "pool_size": len(pool), "rows": rows}


def estimate_beats(parsed: dict) -> list:
    """Beats for the Check page, before any voice exists: every segment's words spread evenly over its estimated
    time. The real render cuts on Kokoro's timings, so a few clauses split differently there."""
    from .. import assemble
    from . import beats as B
    tl = []
    for seg in parsed["segments"]:
        ws = seg["text"].split()
        step = seg["est_dur"] / max(1, len(ws))
        tl.append({"start": seg["est_start"], "dur": seg["est_dur"],
                   "words": [[w, k * step, (k + 1) * step * 0.98] for k, w in enumerate(ws)]})
    total = (tl[-1]["start"] + tl[-1]["dur"]) if tl else 0.0
    spans = assemble._shot_spans(parsed, tl, total)
    from . import planner as PL
    import hashlib
    seed = int(hashlib.sha1(parsed["meta"].get("title", "").encode()).hexdigest()[:6], 16)
    return PL.rhythm(B.split(parsed, tl, spans), seed)


def check_report(parsed: dict, history: dict = None) -> dict:
    """What the Check page shows for a motion-graphics script: pool, picks, repetition numbers (estimated cuts)."""
    from . import history as Hs
    import hashlib
    beats = estimate_beats(parsed)
    meta = parsed["meta"]
    title = meta.get("title", "")
    look = Hs.choose_look(meta, title, beats)
    seed = int(hashlib.sha1(title.encode()).hexdigest()[:6], 16)
    seen = Hs.recent(title) if history is None else history
    from . import formats as Fm
    show = Fm.get(look.get("format"))
    seed = Fm.seed_of(title, look.get("format"))
    names, variants, _info, p = plan_video(beats, dict(meta, look_icons=look["icons"], format_weights=show["weights"],
                                                      format_banned=show["banned"]), seen, seed)
    rep = p["report"]
    from . import planner as PL, variety
    trans = PL.transitions(beats, names, seed, show["transitions"], show["signature"])
    pin = (meta.get("show") or "").strip().lower()
    why = "pinned with show:" if pin and pin != "auto" else (
        "kept from this video's earlier render" if ((Hs.entry(title) or {}).get("look") or {}).get("format") else
        "best topic fit, used least in the last 10 videos")
    try:
        fit = Fm.topic_scores(meta, title)
        goals = Fm.goals_by_format(beats, title)
    except Exception:  # noqa: BLE001
        fit, goals = {}, {}
    rep["format"] = {"id": look.get("format"), "label": show["label"], "why": why, "allowed": Fm.allowed(),
                     "fit": dict(sorted(fit.items(), key=lambda kv: -kv[1])), "goals": goals}
    rep["variety"] = variety.report(names, variants, trans, beats, seen.get("videos"), look)
    cl = rep["variety"].get("closest")
    if cl and cl[0] > Fm.SIMILAR_WARN:
        rep["variety"]["warning"] = (f"This video is {cl[0]:.2f} similar to \u201c{cl[1]}\u201d (warning above "
                                     f"{Fm.SIMILAR_WARN}): pick another show: or look.")
    rep["look"] = look
    rep["pool"] = p["pool"]
    rep["nouns"] = p["nouns"]
    rep["pinned"] = id_list(parsed["meta"].get("icons_pin"), p["family"])
    rep["banned"] = id_list(parsed["meta"].get("icons_ban"), p["family"])
    return rep
