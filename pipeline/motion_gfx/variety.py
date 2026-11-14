"""The variety report of a motion-graphics video (docs/VARIETY_PLAN.md section 7).

  report(names, variants, transitions, beats, seen)   numbers for the Check page, the job page and render.log

Scene type = the template name ("chapter" counts as its own type). Data scenes = the ones that show a fact as a
graphic (number, chart, meter, timeline, versus, pile, icon_list, map_flag and the data types added later).
The goal numbers (section 2/9) are in GOALS; the report says which ones a video meets.
"""

DATA_TYPES = {"number", "chart", "meter", "timeline", "versus", "pile", "icon_list", "map_flag", "ranking", "donut",
              "icon_grid", "table", "funnel", "scale", "before_after", "ticker", "countdown", "calendar", "pros_cons",
              "venn", "process", "cause_effect", "checklist", "split", "odometer", "donut_card", "chart_card", "list_circle",
              "word_wheel", "color_carousel"}
GOALS = {"max_type_share": 20, "max_type_layout": 6, "min_types": 15, "min_transitions": 6, "max_kinetic_share": 15,
         "max_transition_share": 35}


def _abab(names) -> int:
    """How many places show an A-B-A-B run (4 scenes alternating two types)."""
    return sum(1 for i in range(len(names) - 3)
               if names[i] == names[i + 2] and names[i + 1] == names[i + 3] and names[i] != names[i + 1])


def _new_transitions():
    from . import transitions as Tr
    return set(Tr.NEW)


def mix(names) -> dict:
    out = {}
    for n in names:
        out[n] = out.get(n, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def similarity(a: dict, b: dict) -> float:
    """0-1: how alike two videos are, from their stored variety fingerprints (format/look parts, scene-type mix,
    transition mix). 1 = the same show."""
    import math

    def cos(x, y):
        keys = set(x) | set(y)
        dot = sum(x.get(k, 0) * y.get(k, 0) for k in keys)
        nx, ny = math.sqrt(sum(v * v for v in x.values())), math.sqrt(sum(v * v for v in y.values()))
        return dot / (nx * ny) if nx and ny else 0.0
    la, lb = a.get("look") or {}, b.get("look") or {}
    parts = [k for k in ("format", "palette", "fonts", "icons", "icon_style")]
    same = [1.0 if (la.get(k) or a.get(k)) == (lb.get(k) or b.get(k)) and (la.get(k) or a.get(k)) else 0.0
            for k in parts]
    look = sum(same) / len(parts)
    scenes = cos(a.get("scene_mix") or {}, b.get("scene_mix") or {})
    trans = cos(a.get("transition_mix") or {}, b.get("transition_mix") or {})
    return round(0.4 * look + 0.4 * scenes + 0.2 * trans, 3)


def report(names, variants, transitions, beats, seen=None, look=None, cameras=None) -> dict:
    n = max(1, len(names))
    scenes = mix(names)
    layouts = mix([f"{a}:{b}" for a, b in zip(names, variants)])
    trans = mix(transitions)
    top = next(iter(scenes), "")
    top_layout = next(iter(layouts), "")
    # longest stretch (seconds) without a data scene
    longest, start = 0.0, (beats[0]["start"] if beats else 0.0)
    for b, nm in zip(beats, names):
        if nm in DATA_TYPES:
            longest = max(longest, b["start"] - start)
            start = b["end"]
    if beats:
        longest = max(longest, beats[-1]["end"] - start)
    twice = sum(1 for i in range(1, len(names)) if names[i] == names[i - 1])
    rep = {
        "scenes": len(names), "types": len(scenes), "scene_mix": scenes,
        "scene_share": {k: round(100 * v / n, 1) for k, v in scenes.items()},
        "top_type": {"type": top, "count": scenes.get(top, 0), "share": round(100 * scenes.get(top, 0) / n, 1)},
        "top_layout": {"layout": top_layout, "count": layouts.get(top_layout, 0)},
        "kinetic_share": round(100 * scenes.get("kinetic", 0) / n, 1),
        "transition_mix": trans, "transition_types": len(trans),
        "top_transition_share": round(100 * max(trans.values()) / max(1, len(transitions)), 1) if trans else 0.0,
        "same_type_twice": twice, "abab": _abab(names),
        "longest_without_data": round(longest, 1),
        "camera_mix": mix(cameras or []), "camera_types": len(set(cameras or [])),
        "new_transitions": sum(1 for t in transitions if t in _new_transitions()),
    }
    rep["goals"] = {
        "max_type_share": rep["top_type"]["share"] <= GOALS["max_type_share"],
        "max_type_layout": rep["top_layout"]["count"] <= GOALS["max_type_layout"],
        "min_types": rep["types"] >= GOALS["min_types"],
        "min_transitions": rep["transition_types"] >= GOALS["min_transitions"],
        "max_kinetic_share": rep["kinetic_share"] <= GOALS["max_kinetic_share"],
        "max_transition_share": rep["top_transition_share"] <= GOALS["max_transition_share"],
        "no_type_twice": twice == 0, "no_abab": rep["abab"] == 0,
    }
    rep["goals_met"] = sum(rep["goals"].values())
    rep["goals_total"] = len(rep["goals"])
    # closest recent video (seen = history.recent(title)["videos"])
    finger = {"look": look or {}, "scene_mix": scenes, "transition_mix": trans}
    close = [(similarity(finger, v), v.get("title", "?")) for v in (seen or [])]
    rep["closest"] = max(close) if close else None
    return rep


def fingerprint(rep: dict, look: dict) -> dict:
    """What the history keeps of a video for the next videos' similarity check."""
    return {"scene_mix": rep["scene_mix"], "transition_mix": rep["transition_mix"], "look": look}


def log_line(rep: dict) -> str:
    mixs = ", ".join(f"{k} {v}" for k, v in rep["scene_mix"].items())
    tr = ", ".join(f"{k} {v}" for k, v in rep["transition_mix"].items())
    return (f"variety: {rep['types']} scene types in {rep['scenes']} scenes, top {rep['top_type']['type']} "
            f"{rep['top_type']['share']}%, top layout {rep['top_layout']['layout']} x{rep['top_layout']['count']}, "
            f"kinetic {rep['kinetic_share']}%, {rep['transition_types']} transition types (top "
            f"{rep['top_transition_share']}%), same type twice in a row {rep['same_type_twice']}, A-B-A-B "
            f"{rep['abab']}, longest without data {rep['longest_without_data']} s, goals {rep['goals_met']}/"
            f"{rep['goals_total']}\n    scenes: {mixs}\n    transitions: {tr}"
            + (f"\n    cameras: " + ", ".join(f"{k} {v}" for k, v in rep.get("camera_mix", {}).items())
               if rep.get("camera_mix") else ""))
