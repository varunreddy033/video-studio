"""
motion_timeline.py  -  v3 script (script_v3.py) -> timeline.json (docs/MOTION_TIMELINE.md).

Cues are (segment, token) pairs. Two timing sources fill them in:
  real      Kokoro's word timings for the render, aligned to the script's words (difflib), so a pop lands on its word
  estimate  words spread evenly over each segment's estimated length (Check-page previews, no voice needed)
Layout: every element gets a box in a 1920x1080 frame from its place (left / 2 of 4 / over door / 30%,60% ...),
its kind's default size and its size word.
"""

import difflib
import re

from . import script_v3 as V3

FPS, W, H = 30, 1920, 1080
FLOOR = 900
TRANSITION = 18
# default size (w, h) and resting place of each kind; 'stand' kinds sit on the floor, others float
KIND_BOX = {
    "door": (230, 410, "stand"), "coin": (120, 134, "stand"), "coins": (330, 300, "stand"),
    "bubble": (360, 360, "float"), "question": (130, 130, "float"), "exclamation": (130, 130, "float"),
    "calendar": (300, 380, "float"), "arrow": (420, 160, "float"), "gen": (420, 420, "float"),
    "number": (900, 420, "float"), "chart": (1300, 640, "float"), "quote": (1400, 520, "float"),
    "card": (1400, 480, "float"), "char": (420, 620, "stand"), "label": (300, 80, "float"),
}
SIZE_K = {"tiny": 0.5, "small": 0.75, "medium": 1.0, "large": 1.3, "big": 1.3, "huge": 1.7}
SIDE_X = {"left": 0.22, "right": 0.78, "center": 0.5, "top-left": 0.22, "top-right": 0.78, "bottom-left": 0.22,
          "bottom-right": 0.78, "top": 0.5, "bottom": 0.5, "floor": 0.5, "sky": 0.5}
TINTS = ["#16294A", "#1A2440", "#132643", "#182A45", "#1B2440", "#14284A"]
COLORS = ["accent", "teal", "sky", "coral", "good", "bad"]


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


# ------------------------------------------------------------------------------------------ timing ---
class RealTiming:
    """Script tokens -> Kokoro word times. tl = assemble._timeline() output."""

    def __init__(self, segments, tl):
        self.map = []
        for k, seg in enumerate(segments):
            toks = [_norm(t) for t in V3.tokens(seg["text"])]
            kw = tl[k]["words"]
            kn = [_norm(w[0]) for w in kw]
            m = [None] * len(toks)
            for a, b, size in difflib.SequenceMatcher(None, toks, kn, autojunk=False).get_matching_blocks():
                for j in range(size):
                    m[a + j] = b + j
            # unmatched tokens: take the next matched Kokoro word (or the last word)
            nxt = len(kw) - 1
            for j in range(len(toks) - 1, -1, -1):
                if m[j] is None:
                    m[j] = nxt
                else:
                    nxt = m[j]
            self.map.append((tl[k]["start"], kw, m))

    def time(self, cue):
        start, kw, m = self.map[cue["seg"]]
        if not kw:
            return start
        if cue["tok"] >= len(m):
            return start + kw[-1][2]
        return start + kw[max(0, min(len(kw) - 1, m[cue["tok"]]))][1]

    def words_after(self, cue, until):
        """(text, seconds) of the spoken words from a cue to an absolute time, in order."""
        out = []
        for k in range(cue["seg"], len(self.map)):
            start, kw, m = self.map[k]
            first = m[cue["tok"]] if k == cue["seg"] and cue["tok"] < len(m) else (len(kw) if k == cue["seg"] else 0)
            for w in kw[first:]:
                t = start + w[1]
                if t > until:
                    return out
                out.append((w[0], t))
        return out


class EstimateTiming:
    """Even spread over the parser's estimated segment lengths (no voice): previews and Check."""

    def __init__(self, segments):
        self.segs = segments

    def time(self, cue):
        seg = self.segs[cue["seg"]]
        n = max(1, len(V3.tokens(seg["text"])))
        return seg["est_start"] + seg["est_dur"] * min(cue["tok"], n) / n

    def words_after(self, cue, until):
        out = []
        for k in range(cue["seg"], len(self.segs)):
            seg = self.segs[k]
            toks = V3.tokens(seg["text"])
            n = max(1, len(toks))
            first = cue["tok"] if k == cue["seg"] else 0
            for j in range(first, len(toks)):
                t = seg["est_start"] + seg["est_dur"] * j / n
                if t > until:
                    return out
                out.append((toks[j], t))
        return out


# ------------------------------------------------------------------------------------------ layout ---
def _box(ev, placed, auto_i, char_side=None):
    kind = ev.get("kind") or ("char" if ev["op"] == "char" else "label")
    bw, bh, rest = KIND_BOX.get(kind, (300, 300, "float"))
    k = SIZE_K.get(ev.get("size") or "medium", 1.0)
    if kind in ("number", "chart", "quote", "card") and not ev.get("place"):
        k *= 1.0
    bw, bh = bw * k, bh * k
    pl = ev.get("place") or {}
    y_bottom = FLOOR if rest == "stand" else 560 + bh / 2
    if "slot" in pl:
        # slots share the free width: the presenter's side is kept clear
        lo, span = (0.36, 0.56) if char_side == "left" else (0.08, 0.56) if char_side == "right" else (0.14, 0.72)
        x = W * (lo + span * (pl["slot"] - 0.5) / pl["of"])
    elif "side" in pl:
        x = W * SIDE_X[pl["side"]]
        if pl["side"].startswith("top") or pl["side"] == "sky":
            y_bottom = 380 + bh / 2
        elif pl["side"].startswith("bottom") or pl["side"] == "floor":
            y_bottom = FLOOR
    elif "over" in pl:
        tgt = _find(placed, pl["over"])
        if tgt:
            x = tgt["box"]["x"] + tgt["box"]["w"] / 2
            y_bottom = tgt["box"]["y"] - 10
        else:
            x = W / 2
    elif "x" in pl:
        x, y_bottom = W * pl["x"], H * pl["y"] + bh / 2
    else:
        x = W * [0.5, 0.3, 0.7, 0.18, 0.82][auto_i % 5]
        if char_side == "left" and kind != "char":
            x = W * 0.6
        elif char_side == "right" and kind != "char":
            x = W * 0.4
    bx, by = x - bw / 2, y_bottom - bh
    bx = min(max(bx, 30), W - 30 - bw) if bw < W - 60 else (W - bw) / 2      # keep it inside the frame
    by = min(max(by, 150 if kind not in ("char",) else 60), H - 20 - bh) if bh < H - 170 else by
    return {"x": round(bx), "y": round(by), "w": round(bw), "h": round(bh)}


def _find(elements, target: str):
    """Most recent element matching an id, a kind, or 'kind: text'."""
    t = (target or "").strip().lower()
    if not t:
        return None
    kind, _, text = t.partition(":")
    kind, text = kind.strip(), text.strip()
    for el in reversed(elements):
        if el["id"] == t or (el.get("kind") == kind and (not text or (el["props"].get("text") or "").lower() == text)):
            return el
        if t == "char" and el["type"] == "char":
            return el
    return None


# ---------------------------------------------------------------------------------------- timeline ---
def build(parsed, timing, scene_spans, total, assets, words_out=None, palette="navy"):
    """scene_spans = [(start_s, dur_s)] per scene (shot). assets = {scene_index: {...}} for full-frame scenes,
    plus assets["chars"][pose] / assets["gens"][text] = {"src": ...} when available."""
    shots = parsed["shots"]
    dur_frames = round(total * FPS)
    starts = [round(st * FPS) for st, _ in scene_spans]
    scenes, prev_elements = [], []
    carried_char = None                # the presenter stays in the next scene until [- char] / [char: ... | off]
    for k, sh in enumerate(shots):
        frm = starts[k]
        nxt = starts[k + 1] if k + 1 < len(starts) else dur_frames
        tr = _transition(sh.get("from"), k, scenes, prev_elements)
        begin = frm - (tr["frames"] if tr and tr["type"] != "cut" else 0)
        local = lambda sec: max(0, round(sec * FPS) - begin)  # noqa: E731
        elements, headline = [], None
        if sh["type"] in ("talk", "ai", "stock"):
            a = assets.get(k) or {"type": "card", "props": {"text": sh["type"].upper(), "sub": "(preview)"}}
            elements.append({"id": f"s{k}_full", "type": a["type"], "props": {**a.get("props", {}), "move": k},
                             "box": {"x": 0, "y": 0, "w": W, "h": H}, "enter": {"frame": 0, "anim": "none"}})
        auto_i, color_i = 0, 0
        has_head = any(e["op"] == "head" for e in sh.get("events", []))
        first_seg = sh.get("first_segment")
        drops_char = any(e["op"] in ("remove", "char_off") and (e.get("target") in (None, "char")) and
                         e.get("cue", {}).get("seg") == first_seg and e.get("cue", {}).get("tok") == 0
                         for e in sh.get("events", []))
        if carried_char and sh["type"] == "scene" and not drops_char:
            elements.append({**carried_char, "id": f"s{k}_char_carry", "enter": {"frame": 0, "anim": "none"}})
        char_side = (carried_char or {}).get("_place", {}).get("side")
        for ev in sh.get("events", []):
            if "cue" not in ev:
                continue
            t = timing.time(ev["cue"])
            f = max(0, local(t) - 2)                                  # land just before the word
            cue = {"frame": f, "seg": ev["cue"]["seg"], "tok": ev["cue"]["tok"]}
            op = ev["op"]
            if op == "head":
                end_s = (scene_spans[k][0] + scene_spans[k][1])
                spoken = timing.words_after(ev["cue"], end_s)
                headline = {"appear": max(0, f - 6), "words": _head_words(ev["text"], spoken, local, f)}
            elif op == "add":
                box = _box(ev, elements, auto_i, char_side)
                if not ev.get("place"):
                    auto_i += 1
                el = {"id": ev.get("id") or f"s{k}_{ev['kind']}_{len(elements)}", "kind": ev["kind"],
                      "box": box, "enter": {**cue, "anim": ev.get("anim") or _default_anim(ev["kind"])}}
                if ev["kind"] in ("number", "chart", "quote", "card"):
                    el.update(type=ev["kind"], props=dict(ev.get("data") or {}))
                    if ev["kind"] == "number":
                        el["props"]["countFrames"] = 40
                    if ev["kind"] == "chart":
                        el["props"]["kind"] = el["props"].pop("chart", "bar")
                        el["props"]["hideTitle"] = has_head             # the headline pill says it already
                elif ev["kind"] == "gen":
                    g = (assets.get("gens") or {}).get(ev["text"])
                    el.update(type="gen", props={"text": ev["text"], **({"src": g["src"]} if g else {})})
                else:
                    color = ev["opts"].get("color") or COLORS[color_i % len(COLORS)]
                    color_i += 1
                    el.update(type="prop", props={"kind": ev["kind"], "text": ev.get("text", ""), "color": color,
                                                  **{k2: v for k2, v in ev["opts"].items() if k2 != "color"}})
                elements.append(el)
            elif op == "remove":
                tgt = _find([e for e in elements if "exit" not in e], ev["target"])
                if tgt:
                    tgt["exit"] = {"frame": f, "anim": "fade"}
            elif op in ("char", "char_off"):
                cur = next((e for e in reversed(elements) if e["type"] == "char" and "exit" not in e), None)
                if cur:
                    cur["exit"] = {"frame": f, "anim": "none" if op == "char" else "fade"}
                if op == "char":
                    place = ev.get("place") or (cur and cur.get("_place")) or {"side": "left"}
                    char_side = place.get("side")
                    box = _box({**ev, "kind": "char", "place": place}, elements, 0)
                    c = (assets.get("chars") or {}).get(ev["pose"])
                    elements.append({"id": f"s{k}_char_{len(elements)}", "type": "char", "kind": "char", "_place": place,
                                     "box": box, "props": {"pose": ev["pose"], **({"src": c["src"]} if c else {})},
                                     "enter": {**cue, "anim": "none" if cur else "slide"}})
            elif op == "label":
                tgt = _find(elements, ev["target"]) if ev.get("target") else (elements[-1] if elements else None)
                if tgt:
                    bx = tgt["box"]
                    px, py = bx["x"] + bx["w"] / 2, max(bx["y"] - 12, 235)     # stay under the headline pill
                else:
                    px, py = W / 2, 300
                elements.append({"id": f"s{k}_label_{len(elements)}", "type": "label", "kind": "label",
                                 "box": {"x": round(px), "y": round(py), "w": 0, "h": 0},
                                 "props": {"text": ev["text"]}, "enter": {**cue, "anim": "pop"}})
        live_char = next((e for e in reversed(elements) if e["type"] == "char"), None)
        carried_char = None if (live_char is None or "exit" in live_char) else \
            {kk: vv for kk, vv in live_char.items() if kk not in ("exit",)}
        if carried_char is not None:
            carried_char = {**carried_char, "_place": live_char.get("_place") or {"side": "left"}}
        for e in elements:
            e.pop("_place", None)
        scenes.append({"id": f"s{k}", "from": begin, "frames": nxt - begin, "transition": tr,
                       "name": sh.get("name"), "line": sh.get("line"),
                       "background": {"tint": TINTS[k % len(TINTS)], "name": sh.get("name")},
                       **({"headline": headline} if headline else {}), "elements": elements})
        prev_elements = elements
    return {"version": 1, "fps": FPS, "width": W, "height": H, "durationFrames": dur_frames, "palette": palette,
            "words": words_out or [], "captions": {"show": False, "style": "none"}, "scenes": scenes}


def _default_anim(kind):
    return {"door": "grow", "coins": "grow", "chart": "pop", "number": "pop", "quote": "fade", "card": "pop",
            "arrow": "draw", "calendar": "drop"}.get(kind, "pop")


NUMBER_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
                "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
                "billion", "trillion", "half", "quarter"}


def _head_words(text, spoken, local, appear):
    """Headline words light up when the same word is spoken. A word with digits ("$730", "5.5%") lights on the
    first spoken number word ("seven", "five"). Words never spoken follow their neighbours."""
    hw = text.split()
    sp = [(_norm(w), local(t)) for w, t in spoken]
    times = [None] * len(hw)
    j = 0
    for i, w in enumerate(hw):
        n = _norm(w)
        digits = bool(re.search(r"\d", w))
        for jj in range(j, len(sp)):
            if n and (sp[jj][0] == n or (digits and sp[jj][0] in NUMBER_WORDS)):
                times[i], j = sp[jj][1], jj + 1
                break
    last = appear + 8
    for i in range(len(hw)):                       # fill gaps in order
        if times[i] is None:
            nxt = next((times[x] for x in range(i + 1, len(hw)) if times[x] is not None), None)
            times[i] = last + 4 if nxt is None else max(last + 2, min(nxt - 2, last + 4))
        last = times[i]
    return [{"text": w, "frame": int(t)} for w, t in zip(hw, times)]


def _transition(frm, k, scenes, prev_elements):
    """Scene k's arrival. Explicit 'from:' wins; otherwise a chooser varies them (phase 4 widens the set)."""
    if k == 0:
        return None
    if frm:
        if frm["type"] == "zoom":
            tgt = _find(prev_elements, frm.get("target") or "") if prev_elements else None
            if tgt:
                b = tgt["box"]
                x, y = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
            else:
                x, y = W / 2, H / 2
            return {"type": "zoom", "x": round(x), "y": round(y), "frames": TRANSITION + 4}
        if frm["type"] == "push":
            return {"type": "push", "dir": frm["dir"], "frames": TRANSITION}
        if frm["type"] == "cut":
            return {"type": "cut", "frames": 0}
        return {"type": frm["type"], "frames": TRANSITION}
    cycle = ["from-right", "from-right", "from-bottom", "from-right", "from-left", "from-top"]
    last = scenes[-1]["transition"] if scenes else None
    d = cycle[k % len(cycle)]
    if last and last.get("type") == "push" and last.get("dir") == d:
        d = cycle[(k + 1) % len(cycle)]
    return {"type": "push", "dir": d, "frames": TRANSITION}
