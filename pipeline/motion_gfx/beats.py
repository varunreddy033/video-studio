"""Shots -> beats. A beat is one clause of the voice (1.2-3 s): the picture changes on every beat, which gives the
2-3 s rhythm of the reference explainers while the script keeps its 6-10 s shots.

Each beat: {shot, kind (the shot's type), index (0 = the shot's first beat), start, end, words: [[w, t0, t1]],
text, chapter (title, only on the first beat of a chapter)}. Times are seconds in the video."""

import re

from . import design as D

BREAK = re.compile(r"[,.;:!?—-]$")


def video_words(tl):
    """[[word, start, end, segment_index]] in video time, from assemble._timeline's output."""
    return [[w[0], s["start"] + w[1], s["start"] + w[2], si] for si, s in enumerate(tl) for w in s["words"]]


def split(parsed, tl, spans):
    words = video_words(tl)
    chapter_at = {c["segment"]: c["title"] for c in parsed["chapters"]}
    beats = []
    for k, sh in enumerate(parsed["shots"]):
        st, dur = spans[k]
        end = st + dur
        segs = [i for i, s in enumerate(parsed["segments"]) if s["shot"] == k]
        ws = [w for w in words if w[3] in segs]
        groups, cur = [], []
        for w in ws:
            cur.append(w)
            long_enough = cur[-1][2] - cur[0][1] >= D.BEAT_MIN
            if (BREAK.search(w[0]) and long_enough) or cur[-1][2] - cur[0][1] >= D.BEAT_MAX:
                groups.append(cur)
                cur = []
        if cur:
            if groups and cur[-1][2] - cur[0][1] < D.BEAT_MIN * 0.75:
                groups[-1] += cur                 # a short tail joins the beat before it
            else:
                groups.append(cur)
        if not groups:
            groups = [[]]
        for i, g in enumerate(groups):
            b0 = st if i == 0 else max(st, g[0][1] - 0.06)
            beats.append({"shot": k, "kind": sh["type"], "chart": sh.get("chart"), "index": i, "start": round(b0, 3), "words": [w[:3] for w in g],
                          "text": " ".join(w[0] for w in g),
                          "chapter": chapter_at.get(segs[0]) if i == 0 and segs and segs[0] > 0 else None})
        for i in range(len(beats) - len(groups), len(beats) - 1):
            beats[i]["end"] = beats[i + 1]["start"]
        beats[-1]["end"] = round(end, 3)
    beats = _chapter_cards(beats)
    for b in beats:
        b["dur"] = round(b["end"] - b["start"], 3)
    return beats


CHAPTER_CARD = 1.35       # a chapter title holds this long, then the beat carries on with its own picture


def _chapter_cards(beats):
    """A chapter's first beat becomes a short chapter card plus the rest of the beat (its shot's own template)."""
    out = []
    for b in beats:
        if b.get("chapter") and b["end"] - b["start"] > CHAPTER_CARD + 1.0:
            cut = b["start"] + CHAPTER_CARD
            card = dict(b, end=round(cut, 3), chapter_card=True, words=[w for w in b["words"] if w[1] < cut])
            card["text"] = " ".join(w[0] for w in card["words"])
            rest = dict(b, start=round(cut, 3), chapter=None, words=[w for w in b["words"] if w[1] >= cut])
            rest["text"] = " ".join(w[0] for w in rest["words"]) or b["text"]
            out += [card, rest]
        else:
            if b.get("chapter"):
                b["chapter_card"] = True
            out.append(b)
    return out
