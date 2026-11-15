"""The thumbnail brief: what a designed thumbnail says, taken from the script (docs/THUMBNAIL_PLAN.md section 2).

    brief(parsed) -> {"headline", "number", "number_label", "tag", "stamp", "icons", "pose", "versus", "look",
                      "type", "layout_pin", "notes"}

Every part has a header key that wins over the automatic choice: thumbnail:, thumbnail_number:, thumbnail_tag:,
thumbnail_stamp:, thumbnail_icons:, thumbnail_pose:, thumbnail_layout:. Same script = same brief (no randomness;
ties are broken by order in the script, the icon search is deterministic).
"""

import re

from .. import icon_library as L

# words whose most common icon means something else here (board of directors, Exchange the mail server ...)
AMBIG = {"board", "stay", "post", "cast", "pitch", "spring", "exchange", "window", "apple", "bear", "bull", "crane",
         "mint", "bank", "fan", "pupil", "seal", "date", "net", "tank", "suit"}
LAYOUTS = ("big_number", "face_off", "hero_icon", "stamp")
POSES = ("idle", "talk", "point", "shrug", "shocked", "walk", "think", "sneak", "cheer", "worried")
MAX_WORDS = 4            # big text (headline + number label) at most 4 words
STOP = set("a an the and or of to in on at for with by from as is are was were be it its this that".split())
SHOCK = re.compile(r"\b(quit|quits|gone|fired|fire[sd]?|crash\w*|collaps\w*|dead|dies|died|down|outage|broke\w*|"
                   r"shock\w*|banned|ban|recall\w*|lost|loses|fail\w*|leak\w*|hack\w*|breach\w*|bankrupt\w*|over)\b", re.I)
WIN = re.compile(r"\b(win\w*|won|record|rich\w*|millions?|billions?|cheap\w*|free|saves?|profit\w*|soar\w*|boom\w*)\b",
                 re.I)
VERSUS = re.compile(r"^\s*(.+?)\s+(?:vs\.?|versus|or|against)\s+(.+?)\s*\??$", re.I)
CATCH = re.compile(r"\b(catch|beat|beats|overtake|replace|kill|killer)\b", re.I)


def _words(text):
    return [w for w in re.split(r"\s+", (text or "").strip()) if w]


def short_text(text: str, n: int) -> str:
    """At most n words, upper case: leading articles go first, then the clause's key words (templates.key_phrase)."""
    from ..motion_gfx import templates as T
    ws = _words(text)
    while len(ws) > n and ws[0].lower().strip("'\"") in ("a", "an", "the"):
        ws = ws[1:]
    if len(ws) > n:
        q = text.strip().endswith("?")
        ws = (T.key_phrase(" ".join(ws), n) or " ".join(ws[:n])).split()[:n]
        if q and not ws[-1].endswith("?"):
            ws[-1] += "?"
    return " ".join(ws).upper()


def fmt_number(value: float, prefix: str = "", suffix: str = "", decimals: int = 0) -> str:
    """88 % -> 88%, 100000 + -> 100K+, 29990 $ -> $29,990, 2.5e9 -> 2.5B: short enough to be huge."""
    v = float(value)
    for div, unit in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(v) >= div and not suffix.strip().upper().startswith(unit):
            s = f"{v / div:.1f}".rstrip("0").rstrip(".")
            return f"{prefix}{s}{unit}{suffix}"
    if abs(v) >= 100000 and not prefix:
        s = f"{v / 1000:.0f}K"
        return f"{prefix}{s}{suffix}"
    s = f"{v:,.{decimals}f}" if abs(v) >= 10000 else f"{v:.{decimals}f}"
    return f"{prefix}{s}{suffix}"


def _number_label(label: str) -> str:
    """'percent: of Nvidia staff in a Blind poll said ...' -> 'OF STAFF' (names left out, up to 2 content words)."""
    from ..motion_gfx import picker as Pk
    text = label.split(":", 1)[1] if ":" in label else label
    text = re.sub(r"^\s*(percent|per cent|dollars?|rupees?|euros?|pounds?|%)\b", "", text, flags=re.I)
    out, content = [], 0
    for w in _words(Pk.without_names(text)):
        lw = w.lower().strip(",.;:!?\"'")
        if not lw:
            continue
        stop = lw in STOP or lw in ("said", "says", "who", "which")
        if stop and content:
            break
        if stop and out:
            continue
        out.append(lw)
        if not stop:
            content += 1
            if content == 2:
                break
    return " ".join(out).upper() if content else ""


def _striking_number(parsed: dict, headline: str):
    """(text, label) of the number the thumbnail shows: one named in the headline, else the [number:] tags in order
    of % > currency > any, else the first number spoken in the first 30 s."""
    nums = [sh for sh in parsed["shots"] if sh["type"] == "number"]
    hl = headline.replace(",", "")
    for sh in nums:
        v = f"{sh['value']:g}"
        if re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", hl):
            return fmt_number(sh["value"], sh.get("prefix", ""), sh.get("suffix", ""), sh.get("decimals", 0)), \
                _number_label(sh.get("label", ""))
    rank = lambda sh: (0 if "%" in sh.get("suffix", "") else 1 if re.search(r"[$₹€£]", sh.get("prefix", "")) else 2)  # noqa: E731
    if nums:
        sh = sorted(nums, key=lambda s: (rank(s), nums.index(s)))[0]
        return fmt_number(sh["value"], sh.get("prefix", ""), sh.get("suffix", ""), sh.get("decimals", 0)), \
            _number_label(sh.get("label", ""))
    from ..motion_gfx import extras as X
    for seg in parsed["segments"]:
        if seg.get("est_start", 0) > 30:
            break
        for val, a, b in X.numbers(seg["text"]):
            if val >= 2 and not X.years(seg["text"]):
                toks = X._tokens(seg["text"])
                pct = b + 1 < len(toks) and toks[b + 1].lower() in ("percent", "%")
                return fmt_number(val, "", "%" if pct else ""), ""
    return None, ""


def _tag(parsed: dict, headline: str) -> str:
    """The small pill on top: the first [card:] title that isn't the headline again, else a short form of the title."""
    hw = set(re.findall(r"[a-z0-9']+", headline.lower()))
    for sh in parsed["shots"]:
        if sh["type"] != "card":
            continue
        t = (sh.get("text") or "").strip().strip('"')
        tw = set(re.findall(r"[a-z0-9']+", t.lower()))
        if not t or len(t.split()) > 5 or (tw and len(tw & hw) / len(tw) >= 0.5):
            continue
        return t.upper()
    title = re.sub(r"#\w+", "", parsed["meta"].get("title", "")).strip()
    first = re.split(r"(?<=[.!?:])\s", title)[0].strip(" .:")
    return short_text(first, 5)


def _versus(meta: dict, headline: str):
    """(left, right) when the video is a face-off: 'X vs Y' / 'X or Y' in the headline or title, a 'x vs y' tag, or
    'can X catch Y'."""
    title = re.sub(r"#\w+", "", meta.get("title", "")).strip()
    for text in (headline, title):
        m = VERSUS.match(text or "")
        if m and len(m.group(1).split()) <= 3 and len(m.group(2).split()) <= 3:
            return m.group(1).strip(" ?").upper(), m.group(2).strip(" ?").upper()
    tags = meta.get("tags", "")
    for tag in (tags if isinstance(tags, list) else str(tags).split(",")):
        m = re.match(r"^\s*(.+?)\s+(?:vs\.?|versus)\s+(.+?)\s*$", tag, re.I)
        if m:
            return m.group(1).upper(), m.group(2).upper()
    m = re.search(r"\b(?:can|will)\s+(\w+(?:\s\w+)?)\s+(?:\w+\s+)?(?:catch|beat|overtake|replace)\s+(?:the\s+)?(\w+)", title, re.I)
    if m:
        return m.group(1).upper(), m.group(2).upper()
    return None


def _pose(text: str, versus) -> str:
    if versus:
        return "point"
    if "?" in text:
        return "think"
    if SHOCK.search(text):
        return "shocked"
    if WIN.search(text):
        return "cheer"
    return "talk"


def _icon_ids(meta: dict, family: str, words: list, n: int = 2, exclude=(), min_score: float = 0.5,
              ambig: bool = True) -> list:
    """The best icons of the video's family for these words: every word is searched (the picker's filters: no
    boring symbols, no question marks, no brand / logo names, no faces of people), and the n best-scoring
    different icons win. Earlier words count a little more (the headline comes first)."""
    from .. import icon_index as IX
    from ..motion_gfx import picker as Pk
    best = {}
    if ambig:
        words = [w for w in words if Pk.stem(w) not in AMBIG]
    for k, w in enumerate(words[:12]):
        q = Pk.HINTS.get(w, w)
        for r in IX.search(q, sets=[family], k=12):
            name = r["id"].split(":", 1)[1]
            if r["id"] in exclude or Pk.BORING.search(name) or Pk.is_question(r["id"]) or \
                    re.search(r"brand|logo|person|man-|woman|people|^technologist", name):
                continue
            sc = r["score"] - 0.01 * k
            if r["score"] >= min_score and sc > best.get(r["id"], -1):
                best[r["id"]] = sc
            break
    ranked = sorted(best.items(), key=lambda x: (-x[1], x[0]))
    # a second icon only when it fits about as well as the first (a weak match looks random on a cover)
    return [i for i, s in ranked if s >= ranked[0][1] - 0.08][:n] if ranked else []


def look_of(parsed: dict) -> dict:
    """The video's own look (format, palette set, fonts, icon family, icon style), read from the history without
    reserving anything: a video already in data/asset_history.json keeps its look, a new one gets the look its
    render would choose now."""
    from ..motion_gfx import history as Hs
    meta, title = parsed["meta"], parsed["meta"].get("title", "")
    old = (Hs.entry(title) or {}).get("look")
    if old and old.get("format"):
        look = dict(old)
        for k in ("icons", "palette", "fonts", "icon_style"):
            if (meta.get(k) or "").strip():
                look[k] = meta[k].strip().lower()
        return look
    try:
        from ..motion_gfx import picker as Pk
        beats = Pk.estimate_beats(parsed)
    except Exception:  # noqa: BLE001  (the look only needs the beats for the format's goal estimate)
        beats = None
    return Hs.choose_look(meta, title, beats)


def brief(parsed: dict, look: dict = None) -> dict:
    meta = parsed["meta"]
    look = look or look_of(parsed)
    notes = []
    title = re.sub(r"#\w+", "", meta.get("title", "")).strip()
    raw_head = (meta.get("thumbnail") or "").strip() or title
    headline = short_text(raw_head, MAX_WORDS)
    if headline != raw_head.upper():
        notes.append(f"headline shortened to {MAX_WORDS} words: {headline}")
    if (meta.get("thumbnail_number") or "").strip():
        number, label = meta["thumbnail_number"].strip().upper(), ""
    else:
        number, label = _striking_number(parsed, headline)
    # the number shown big is taken out of the headline ("88% SAID STAY" -> 88% + SAID STAY)
    head_wo = headline
    if number:
        bare = re.sub(r"[^\d.]", "", number)
        head_wo = re.sub(rf"\S*{re.escape(bare)}\S*\s*", "", headline.replace(",", ""), count=1).strip() if bare and \
            bare in headline.replace(",", "") else headline
    tag = (meta.get("thumbnail_tag") or "").strip().upper() or _tag(parsed, headline)
    stamp = (meta.get("thumbnail_stamp") or "").strip().upper()
    versus = _versus(meta, headline)
    family = look.get("icons") or "fluent_flat"
    if family not in L.usable_families():
        family = (L.usable_families() or ["fluent_flat"])[0]
    from ..motion_gfx import picker as Pk
    if (meta.get("thumbnail_icons") or "").strip():
        icons = [i for i in Pk.id_list(meta["thumbnail_icons"], family) if _exists(i)][:2]
        missing = [i for i in Pk.id_list(meta["thumbnail_icons"], family) if not _exists(i)]
        if missing:
            notes.append("thumbnail_icons: not in the library: " + ", ".join(missing))
    else:
        tags = meta.get("tags", "")
        tags = " ".join(tags) if isinstance(tags, list) else str(tags).replace(",", " ")
        try:
            nouns = Pk.topic_nouns(meta, Pk.estimate_beats(parsed))[:8]
        except Exception:  # noqa: BLE001
            nouns = []
        words = Pk.content_words(head_wo) + Pk.content_words(title) + nouns + Pk.content_words(tags)
        seen, uniq = set(), []
        for w in words:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
        icons = _icon_ids(meta, family, uniq, 2)
    vs_icons = []
    if versus:
        for side in versus:
            ws = Pk.content_words(side, names=True) or [side.lower()]
            got = _icon_ids(meta, family, [" ".join(ws)] + ws, 1, exclude=vs_icons, min_score=0.42, ambig=False) or \
                _icon_ids(meta, family, ["laptop computer", "trophy", "star"], 1, exclude=vs_icons, min_score=0.3)
            vs_icons += got[:1]
    pose = (meta.get("thumbnail_pose") or "").strip().lower() or _pose(f"{headline} {title}", versus)
    pin = (meta.get("thumbnail_layout") or "").strip().lower() or None
    return {"headline": head_wo or headline, "headline_full": headline, "number": number, "number_label": label,
            "tag": tag, "stamp": stamp, "icons": icons, "versus": list(versus) if versus else None,
            "versus_icons": vs_icons, "pose": pose, "look": look, "family": family, "layout_pin": pin,
            "type": meta.get("type", "full"), "title": title, "notes": notes}


def _exists(icon_id: str) -> bool:
    try:
        set_id, name = icon_id.split(":", 1)
        return set_id in L.installed() and name in L.load(set_id)["icons"]
    except (ValueError, Exception):  # noqa: BLE001
        return False
