"""Script format of rendering_method: neon (docs/SCRIPT_FORMAT.md section 8): neon kinetic-typography motion videos.

One tag = one scene, cut where its narration starts; things land on the spoken words of that scene:
    [neon: headline | HELL / YES.]                  stacked huge words (/ = next line), the last line lime
    [neon: logo | OPUS 5.5 | made with]             a lockup: small kicker + huge word between two sparks
    [neon: prompt | Create a *15-second* animation | PROMPT]   a UI window, the text typed as it is spoken
    [neon: nodes | Idea > Script > Video]           2-5 boxes joined by a glowing line, one per spoken beat
    [neon: stack | Layers, Keyframes, Graph editor] 2-6 tilted cards stacking up
    [neon: number | 5H | saved on every video]      a giant magenta number + label
    [neon: tunnel | CAMERA]                         a fly-through of neon frames around one word
    [neon: words | the letters *stretch* here]      a sentence word by word, *word* in a lime box
    [neon: endcard | MOTION | comment]              closing lockup + a call-to-action pill
"""

import re

TAGS = ("neon",)
KINDS = ("headline", "logo", "prompt", "nodes", "stack", "number", "tunnel", "words", "endcard")
SHOT_WARN_SEC = 6.0


def is_scene(sh) -> bool:
    return sh.get("type") == "neon"


def parse_tag(kind, arg, line, errors):
    def bad(msg):
        errors.append({"line": line, "msg": msg})

    parts = [p.strip() for p in arg.split("|")]
    k = parts[0].lower()
    if k not in KINDS:
        return bad(f"[neon: kind | text]: kind must be one of {', '.join(KINDS)}, got '{parts[0]}'")
    text = parts[1] if len(parts) > 1 else ""
    extra = parts[2] if len(parts) > 2 else ""
    if not text:
        return bad(f"[neon: {k} | text]: the text is missing")
    shot = {"type": "neon", "line": line, "kind": k, "text": text, "extra": extra}
    if k == "headline":
        shot["lines"] = [x.strip() for x in text.split("/") if x.strip()][:3]
    if k == "nodes":
        shot["items"] = [x.strip() for x in re.split(r">|->", text) if x.strip()]
        if not 2 <= len(shot["items"]) <= 5:
            return bad("[neon: nodes | A > B > C]: 2-5 boxes")
    if k == "stack":
        shot["items"] = [x.strip() for x in text.split(",") if x.strip()]
        if not 2 <= len(shot["items"]) <= 6:
            return bad("[neon: stack | a, b, c]: 2-6 cards")
    if k in ("number", "logo", "tunnel", "headline") and len(text) > 28:
        return bad(f"[neon: {k} | ...]: keep it short (28 characters at most), it is drawn huge")
    return shot


def check(meta, shots, err, warn):
    for sh in shots:
        if not is_scene(sh) and not sh.get("placeholder"):
            err(sh["line"], f"[{sh['type']}: ...] isn't used by neon videos; use [neon: kind | text]")
            continue
        if sh.get("est_dur", 0) > SHOT_WARN_SEC:
            warn(sh["line"], f"this scene stays on screen ~{sh['est_dur']:.0f} s; neon videos cut every 1-4 s, add "
                             f"another [neon:] inside that narration")
    used = [sh for sh in shots if is_scene(sh)]
    if not used:
        err(1, "a neon video needs at least one [neon: kind | text]")
    kinds = [s["kind"] for s in used]
    return {"scenes": len(used), "kinds": {k: kinds.count(k) for k in sorted(set(kinds))}}
