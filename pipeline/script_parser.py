"""
script_parser.py  -  turns script.md into segments + shots, and checks it for problems.

Format (full guide: docs/SCRIPT_FORMAT.md):

    ---
    title: Is the AI Bubble About to Pop?
    description: |
      First paragraph of the YouTube description.
      #AI #Stocks
    tags: ai bubble, stock market, nvidia
    format: landscape            (or vertical)
    music: misdirection          (words matched against assets/audio/bgm file names)
    thumbnail: THE BUBBLE?       (big thumbnail text, default = title)
    thumbnail_prompt: a giant glowing soap bubble over a city at night
    ---

    ## Cold open                                   <- chapter heading
    [ai: aerial view of city traffic at night]     <- a shot starts here
    Everyone is talking about an AI bubble.        <- narration (spoken)
    [ai: a giant soap bubble above a skyline] [sfx: whoosh]
    But what does that actually mean?              <- cut happens exactly here

Shot tags:  [ai: image prompt]  [stock: subject] (= AI image styled as a documentary photo)
            [card: BIG TEXT | small line]
            [number: 3.2 | trillion dollars | prefix=$]  [quote: text | who said it]
            [chart: bar | title | 2022: 0.4, 2023: 1.2, 2024: 3.3]   (bar or line)
Other tags: [sfx: whoosh]  [pause: 1.5]
"""

import re

from . import config as C
from . import characters, presets, sfx
from .util import best_match, music_files, sfx_files

VISUAL = {"stock", "ai", "card", "number", "quote", "chart", "talk", "act"}
CHARACTER_SHOTS = {"talk", "act"}
FRAMINGS = ("wide", "medium", "close")
CAMERAS = ("static", "zoom in", "zoom out")
OTHER = {"sfx", "pause"}
TAG_RE = re.compile(r"\[(\w+)\s*:\s*([^\]]*)\]")
LINK_RE = re.compile(r"\[([^\]]+)\]\((?:https?://|www\.)[^)]+\)")
NUM_RE = re.compile(r"^[-+]?\d[\d,]*(\.\d+)?$")
BAD_AI_WORDS = re.compile(r"\b(text|words?|logo|sign(age)?|caption|letters?|written|headline|label)\b", re.I)
META_KEYS = {"title", "description", "tags", "format", "music", "voice", "speed", "thumbnail", "thumbnail_prompt",
             "character", "short", "type", "clip_from", "clip_start", "clip_end",
             "language", "captions", "art_style", "sfx", "style", "palette", "rendering_method",
             "icons", "icon_reuse", "icons_pin", "icons_ban",
             "look", "fonts", "icon_style", "scene_order", "show"}     # + voice / music: preset ids (presets/), see presets.py
INTRO_RE = re.compile(r"\b(today we('| a)re|today we will|in this video|welcome (back|to)|hey (guys|everyone)|"
                      r"before we (start|begin)|let's get started|let's dive in)\b", re.I)
OUTRO_RE = re.compile(r"\b(subscribe|like (and|&) subscribe|see you (next|in the)|thanks for watching|"
                      r"stay curious\. stay skeptical)\b", re.I)


def parse_ts(v):
    """'4:12' / '1:04:12' / '252' / '252.5' -> seconds (None if it isn't a time)."""
    v = (v or "").strip()
    if not re.fullmatch(r"\d+(:\d{1,2}){0,2}(\.\d+)?", v):
        return None
    parts = v.split(":")
    sec = 0.0
    for part in parts:
        sec = sec * 60 + float(part)
    return sec


def clip_source(job_id: str):
    """The finished source job of a clip Short: its state + paths, or (None, reason)."""
    import json as _json
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{6}", job_id or ""):
        return None, f"clip_from must be a job id like 20261108-184222-d0b89e, got '{job_id}'"
    d = C.JOBS_DIR / job_id
    try:
        st = _json.loads((d / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, f"no video with id {job_id} on this machine"
    if not (d / "final.mp4").exists() or not (d / "timeline_final.json").exists() or not (d / "script.md").exists():
        return None, f"{job_id} has no finished final video to clip from (make its final first)"
    return {"id": job_id, "dir": d, "state": st, "duration": (st.get("final") or {}).get("duration_sec") or 0,
            "title": st.get("title") or job_id}, None


def _clean(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = re.sub(r"(\*\*|__|\*|`)", "", text)
    text = re.sub(r"(?<!\w)_(?!\w)|(?<=\s)_|_(?=\s)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def _front_matter(lines):
    meta, errors, body_start = {}, [], 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            errors.append((1, "the front matter starts with --- but never ends with a second --- line"))
            return meta, errors, 0
        key, block = None, []
        for i in range(1, end):
            raw = lines[i]
            if key and (raw.startswith("  ") or not raw.strip()):
                block.append(raw.strip())
                continue
            if key:
                meta[key] = "\n".join(block).strip()
                key, block = None, []
            if not raw.strip() or raw.strip().startswith("#"):
                continue
            if ":" not in raw:
                errors.append((i + 1, f"front matter line should look like 'key: value': {raw.strip()}"))
                continue
            k, v = raw.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k not in META_KEYS:
                errors.append((i + 1, f"unknown front matter key '{k}' (allowed: {', '.join(sorted(META_KEYS))})"))
                continue
            if v in ("|", ">"):
                key, block = k, []
            else:
                meta[k] = v.strip('"').strip("'")
        if key:
            meta[key] = "\n".join(block).strip()
        body_start = end + 1
    return meta, errors, body_start


def _parse_visual(kind, arg, line, errors):
    parts = [p.strip() for p in arg.split("|")]
    if not parts[0]:
        errors.append({"line": line, "msg": f"[{kind}: ...] is empty"})
        return None
    shot = {"type": kind, "line": line}
    if kind == "stock":
        shot["query"] = parts[0]
    elif kind == "ai":
        shot["prompt"] = parts[0]
    elif kind == "card":
        shot["text"] = parts[0]
        shot["sub"] = parts[1] if len(parts) > 1 else ""
    elif kind == "quote":
        shot["text"] = parts[0].strip('"“”')
        shot["by"] = parts[1] if len(parts) > 1 else ""
    elif kind == "number":
        val = parts[0].replace(" ", "")
        opts = {}
        label_parts = []
        for p in parts[1:]:
            # options can share one slot: "prefix=$ suffix=B"
            pairs = re.findall(r"(prefix|suffix|decimals)\s*=\s*(\S*)", p)
            if pairs and not re.sub(r"(prefix|suffix|decimals)\s*=\s*\S*", "", p).strip():
                for k, v in pairs:
                    opts[k] = v
            else:
                label_parts.append(p)
        # allow "$3.2" or "45%" written directly in the value
        pre = re.match(r"^([^\d\-+]*)", val).group(1)
        suf = re.search(r"([^\d.,]*)$", val).group(1)
        num = val[len(pre):len(val) - len(suf) if suf else None]
        if not NUM_RE.match(num or ""):
            errors.append({"line": line, "msg": f"[number: ...] needs a number first, got '{parts[0]}'"})
            return None
        shot["value"] = float(num.replace(",", ""))
        shot["decimals"] = int(opts.get("decimals", len(num.split(".")[1]) if "." in num else 0))
        shot["prefix"] = opts.get("prefix", pre)
        shot["suffix"] = opts.get("suffix", suf)
        shot["label"] = " | ".join(label_parts)
    elif kind == "talk":
        shot["pose"] = parts[0].lower()
        shot["set"] = (parts[1] if len(parts) > 1 and parts[1] else "").lower()   # "" = the character's first set
        cam = (parts[2] if len(parts) > 2 and parts[2] else "static").lower()
        if cam not in CAMERAS:
            errors.append({"line": line, "msg": f"[talk: pose | set | camera]: camera must be one of {', '.join(CAMERAS)}"})
            return None
        shot["camera"] = cam
    elif kind == "act":
        shot["prompt"] = parts[0]
        fr = (parts[1] if len(parts) > 1 and parts[1] else "medium").lower()
        shot["ref"] = any(p.lower() == "ref" for p in parts[2:])
        if fr not in FRAMINGS:
            errors.append({"line": line, "msg": f"[act: description | framing]: framing must be wide, medium or close, got '{fr}'"})
            return None
        shot["framing"] = fr
    elif kind == "chart":
        if len(parts) < 3 or parts[0].lower() not in ("bar", "line"):
            errors.append({"line": line, "msg": "chart format: [chart: bar | title | A: 1, B: 2, C: 3] (bar or line)"})
            return None
        shot["chart"] = parts[0].lower()
        shot["title"] = parts[1]
        data = []
        for item in parts[2].split(","):
            if ":" not in item:
                errors.append({"line": line, "msg": f"chart data item '{item.strip()}' should look like 'label: number'"})
                return None
            k, v = item.rsplit(":", 1)
            v = v.strip().replace("$", "").replace("%", "").replace(",", "")
            try:
                data.append((k.strip(), float(v)))
            except ValueError:
                errors.append({"line": line, "msg": f"chart value '{v}' is not a number"})
                return None
        if len(data) < 2:
            errors.append({"line": line, "msg": "a chart needs at least 2 data points"})
            return None
        shot["data"] = data
        shot["unit"] = next((p.split("=", 1)[1].strip() for p in parts[3:] if p.startswith("unit=")), "")
    return shot


def parse(text: str) -> dict:
    """Returns {ok, errors, warnings, meta, segments, shots, chapters, stats}."""
    lines = text.replace("\r\n", "\n").split("\n")
    meta, fm_err, start = _front_matter(lines)
    errors = [{"line": ln, "msg": m} for ln, m in fm_err]
    warnings = []

    def err(line, msg):
        errors.append({"line": line, "msg": msg})

    def warn(line, msg):
        warnings.append({"line": line, "msg": msg})

    segments, shots, chapters = [], [], []
    section = ""
    pending_shot = None          # a visual tag waiting for its first narration
    pending_sfx, pending_pause = [], 0.0
    para_open = False

    def add_text(chunk, line):
        nonlocal pending_shot, pending_sfx, pending_pause, para_open
        chunk = _clean(chunk)
        if not chunk:
            return
        new_shot = pending_shot is not None
        if new_shot:
            pending_shot["first_segment"] = len(segments)
            shots.append(pending_shot)
            pending_shot = None
        if not shots:
            err(line, "narration starts before any shot. Put a shot tag like [ai: ...] or [card: ...] above it")
            shots.append({"type": "card", "text": meta.get("title", "…"), "sub": "", "line": line,
                          "first_segment": 0})
            new_shot = True
        if segments and not new_shot and para_open and not pending_sfx and not pending_pause:
            segments[-1]["text"] += " " + chunk      # same shot, same paragraph: one segment
            segments[-1]["line_end"] = line
            return
        segments.append({"text": chunk, "line": line, "line_end": line, "shot": len(shots) - 1,
                         "section": section, "sfx": pending_sfx, "pause_before": pending_pause,
                         "new_paragraph": not para_open})
        pending_sfx, pending_pause = [], 0.0
        para_open = True

    is_motion = (meta.get("style") or "").strip().lower() == "motion"
    if is_motion:                      # style: motion -> v3 scene tags (pipeline/script_v3.py)
        from . import script_v3
        segments, shots, chapters = script_v3.parse_body(lines, start, meta, err, warn)
    if not is_motion:
        for i in range(start, len(lines)):
            ln = i + 1
            raw = lines[i].rstrip()
            s = raw.strip()
            if not s:
                para_open = False
                continue
            if s.startswith("<!--") or s.startswith("//"):
                continue
            if re.match(r"^#{1,3}\s", s):
                section = s.lstrip("#").strip()
                chapters.append({"title": section, "line": ln, "segment": len(segments)})
                para_open = False
                continue
            if re.fullmatch(r"-{3,}|\*{3,}", s):
                para_open = False
                continue
            pos = 0
            for m in TAG_RE.finditer(s):
                add_text(s[pos:m.start()], ln)
                pos = m.end()
                kind, arg = m.group(1).lower(), m.group(2).strip()
                if kind in VISUAL:
                    if pending_shot is not None:
                        warn(ln, f"two shots in a row with no narration between them; "
                                 f"the {pending_shot['type']} shot from line {pending_shot['line']} is skipped")
                    shot = _parse_visual(kind, arg, ln, errors)
                    if shot:
                        pending_shot = shot
                elif kind == "sfx":
                    if arg:
                        pending_sfx.append(arg)
                elif kind == "pause":
                    try:
                        pending_pause += max(0.0, min(5.0, float(arg.rstrip("s"))))
                    except ValueError:
                        err(ln, f"[pause: ...] needs seconds, like [pause: 1.5], got '{arg}'")
                else:
                    err(ln, f"unknown tag [{kind}: ...]. Use one of: {', '.join(sorted(VISUAL | OTHER))}")
            add_text(s[pos:], ln)

        if pending_shot is not None:
            warn(pending_shot["line"], "the last shot tag has no narration after it, so it is not used")

    # ------------------------------------------------------------- checks
    if not meta.get("title"):
        err(1, "missing 'title:' in the front matter")
    elif len(meta["title"]) > 100:
        err(1, f"title is {len(meta['title'])} characters; YouTube allows 100")
    fmt_given = bool(meta.get("format"))
    fmt = (meta.get("format") or "landscape").lower()
    if fmt not in ("landscape", "vertical"):
        err(1, f"format must be landscape or vertical, got '{fmt}'")
        fmt = "landscape"
    meta["format"] = fmt
    meta["tags"] = [t.strip() for t in (meta.get("tags") or "").split(",") if t.strip()]
    if sum(len(t) for t in meta["tags"]) > 450:
        warn(1, "tags are longer than YouTube's 500 character limit; extra tags will be cut")
    char = None
    if meta.get("character"):
        try:
            char = characters.load(meta["character"])
        except characters.CharacterError as e:
            err(1, str(e))
    meta["character_data"] = char
    # presets (presets/<kind>/<id>.json). A missing key = the default preset (= today's config values).
    # voice: may also be a Kokoro voice id and music: track names, exactly as before.
    header = {k: meta.get(k) or "" for k in ("language", "voice", "speed", "captions", "art_style", "music")}
    try:
        chosen, p_over, p_err = presets.resolve(header, char)
        for m in p_err:
            err(1, m)
        voice, speed, meta["voice_from"] = presets.voice_settings(chosen, header, char)
    except presets.PresetError as e:   # a broken preset file
        err(1, str(e))
        chosen, p_over = dict(presets.DEFAULT_CHOSEN), {}
        voice, speed, meta["voice_from"] = meta.get("voice") or C.KOKORO_VOICE, meta.get("speed") or "", []
    meta["presets"], meta["preset_overrides"] = chosen, p_over
    if char and header["art_style"]:
        warn(1, f"art_style applies to [ai:]/[stock:] only; [act:] keeps the character style "
                f"({char['name']}'s STYLE), and so do the presenter thumbnails")
    if header["music"].lower() in presets.ids("music"):
        meta["music"] = ""            # a music preset, not a track name
    meta["music_off"] = header["music"].strip().lower() in ("none", "off", "no")
    if meta["music_off"]:
        meta["music"] = ""            # music: none = a video without background music
    meta["sfx_given"] = bool(meta.get("sfx"))
    sfx_mode = (meta.get("sfx") or "script").strip().lower()
    if sfx_mode not in ("script", "auto", "rich", "off"):
        err(1, f"sfx must be script (only the [sfx:] tags, the default), auto (Video Studio adds effects), rich "
               f"(an effect on almost every cut) or off, got '{sfx_mode}'")
        sfx_mode = "script"
    meta["sfx"] = sfx_mode
    try:
        meta["speed"] = float(speed or C.KOKORO_SPEED)
    except ValueError:
        err(1, "speed must be a number like 1.0")
        meta["speed"] = 1.0
    meta["voice"] = voice
    # ---------------------------------------------------------------- video type
    vtype = (meta.get("type") or "full").strip().lower()
    if vtype not in C.TYPES:
        err(1, f"type must be short or full, got '{vtype}'")
        vtype = "full"
    meta["type"] = vtype
    P = C.TYPES[vtype]
    if vtype == "short":
        if fmt_given and fmt != "vertical":
            err(1, "a Short is always vertical (9:16): remove 'format:' or set it to vertical")
        meta["format"] = "vertical"
    elif not fmt_given:
        meta["format"] = P["format"]
    # ---------------------------------------------------------------- style (classic = default, untouched)
    vstyle = (meta.get("style") or "classic").strip().lower()
    if vstyle not in C.STYLES:
        err(1, f"style must be classic or motion, got '{vstyle}'")
        vstyle = "classic"
    meta["style"] = vstyle
    if vstyle == "motion":
        pal = (meta.get("palette") or "navy").strip().lower()
        if pal not in C.PALETTES:
            err(1, f"palette must be one of {', '.join(C.PALETTES)}, got '{pal}'")
        meta["palette"] = pal
        if vtype == "short":
            err(1, "motion Shorts aren't built yet (motion plan phase 8); use style: classic for Shorts")
        if meta["format"] != "landscape":
            err(1, "style: motion is landscape (16:9) for now")
    clip = None
    if meta.get("clip_from") or meta.get("clip_start") or meta.get("clip_end"):
        if vtype != "short":
            err(1, "clip_from / clip_start / clip_end only work with 'type: short'")
        src, why = clip_source(meta.get("clip_from", "").strip())
        a, b = parse_ts(meta.get("clip_start")), parse_ts(meta.get("clip_end"))
        if not src:
            err(1, why)
        if a is None or b is None:
            err(1, "clip_start and clip_end need times like 4:12 (minutes:seconds)")
        elif b <= a:
            err(1, f"clip_end ({meta['clip_end']}) must be after clip_start ({meta['clip_start']})")
        elif src and src["duration"] and b > src["duration"] + 0.5:
            err(1, f"clip_end {meta['clip_end']} is past the end of that video ({int(src['duration'] // 60)}:"
                   f"{int(src['duration'] % 60):02d})")
        if src and a is not None and b is not None:
            clip = {"source": src["id"], "start": a, "end": b, "source_title": src["title"]}
            meta.setdefault("title", f"{src['title'][:80]} #Shorts")
            src_meta, _, _ = _front_matter((src["dir"] / "script.md").read_text(encoding="utf-8").split("\n"))
            if src_meta.get("thumbnail"):
                meta.setdefault("thumbnail", src_meta["thumbnail"])
        meta["clip"] = clip
        # the source's own narration and shots are used; nothing in this file's body is rendered
        errors[:] = [e for e in errors if not e["msg"].startswith(("narration starts before", "missing 'title:'"))]
        segments, shots, chapters = [], [], []
    meta["clip"] = clip
    # ---------------------------------------------------------------- rendering method
    rm = (meta.get("rendering_method") or "").strip().lower()
    meta["rendering_method_given"] = bool(rm)
    if not rm:
        # no line: the default (motion graphics), except scripts that only work with AI images
        needs_ai = (char or clip or vstyle == "motion" or any(sh["type"] in CHARACTER_SHOTS for sh in shots))
        rm = "ai_image" if needs_ai else C.DEFAULT_RENDERING_METHOD
    if rm not in C.RENDERING_METHODS:
        err(1, f"rendering_method must be one of {', '.join(C.RENDERING_METHODS)}, got '{rm}'")
        rm = "ai_image"
    meta["rendering_method"] = rm
    if rm == "motion" and (meta.get("style") or "").strip().lower() == "motion":
        err(1, "use either style: motion (animated scenes with the presenter) or rendering_method: motion "
               "(stick-figure motion graphics), not both")
    if rm == "motion":
        if char or any(sh["type"] in CHARACTER_SHOTS for sh in shots):
            err(1, "character videos ([talk:] / [act:]) need rendering_method: ai_image; motion graphics use "
                   "anonymous stick figures")
        if clip:
            err(1, "clip Shorts reuse a finished AI-image video: remove rendering_method: motion")
        if header["art_style"]:
            warn(1, "art_style applies to AI images only; motion graphics use the bright-pop palette")
        if not header["captions"]:
            # the scenes already show the key words; a caption chip would repeat them. The .srt is still made.
            meta["presets"]["captions"] = "none"
        if not (meta.get("sfx_given")):
            meta["sfx"] = "auto"                      # motion videos get the animation's own sounds by default
        fam = (meta.get("icons") or "").strip().lower()
        if fam:
            from . import icon_library as IL
            fams = IL.usable_families() or IL.FAMILIES
            if fam not in fams:
                err(1, f"icons must be one of {', '.join(fams)}, got '{fam}'")
        from .motion_gfx import design as MD
        from .motion_gfx import formats as MF                 # (adds the formats' palettes and fonts to design)
        fm = (meta.get("show") or "").strip().lower()       # the video's format (show package); format: = 16:9 / 9:16
        if fm and fm != "auto" and fm not in MF.FORMATS:
            err(1, f"show must be auto or one of {', '.join(MF.FORMATS)}, got '{fm}'")
        for key, valid in (("palette", list(MD.PALETTE_SETS)), ("fonts", list(MD.FONT_PAIRS)),
                           ("icon_style", ["sticker", "plain"]), ("look", ["auto", "classic"])):
            v = (meta.get(key) or "").strip().lower()
            if v and v not in valid:
                err(1, f"{key} must be one of {', '.join(valid)} for motion graphics, got '{v}'")
        order = [x.strip().lower() for x in str(meta.get("scene_order") or "").split(",") if x.strip()]
        if order:                                       # test / preview reels: these scene types in this order
            from .motion_gfx import planner as PLN
            bad = [x for x in order if x not in PLN.TYPES]
            if bad:
                err(1, f"scene_order: unknown scene type(s) {', '.join(bad)}; valid: {', '.join(sorted(PLN.TYPES))}")
            warn(1, "scene_order: forces scene types for a test reel (the planner's choices are switched off)")
        reuse = str(meta.get("icon_reuse") or "").strip()
        if reuse and not (reuse.isdigit() and 1 <= int(reuse) <= 5):
            err(1, f"icon_reuse must be a whole number from 1 to 5 (how often one icon may appear), got '{reuse}'")
    elif meta.get("palette") and vstyle != "motion":
        warn(1, "palette: only applies to style: motion and rendering_method: motion")
    if rm != "motion" and any(meta.get(k) for k in ("icons", "icon_reuse", "icons_pin", "icons_ban", "look", "fonts", "icon_style", "show")):
        warn(1, "icons / icon_reuse / icons_pin / icons_ban / look / fonts / icon_style only apply to "
                "rendering_method: motion")
    if not segments and not clip:
        err(start + 1, "no narration found")

    # durations (estimate; the real length comes from the voice)
    wps = C.WORDS_PER_MIN / 60 * meta["speed"]
    t = 0.0
    for seg in segments:
        seg["words"] = _words(seg["text"])
        t += seg["pause_before"] + (C.GAP_AFTER_PARAGRAPH if seg["new_paragraph"] and seg is not segments[0] else 0)
        seg["est_start"] = round(t, 2)
        seg["est_dur"] = round(seg["words"] / wps + C.GAP_IN_PARAGRAPH, 2)
        t += seg["est_dur"]
    total = t + C.GAP_AFTER_PARAGRAPH
    for k, sh in enumerate(shots):
        segs = [s for s in segments if s["shot"] == k]
        sh["est_start"] = segs[0]["est_start"] if segs else 0
        sh["est_dur"] = round(sum(s["est_dur"] + s["pause_before"] for s in segs), 1)
        limit = (P["hold_talk"] if sh["type"] == "talk" else P["hold_photo"] if sh["type"] in ("ai", "stock", "act")
                 else P["hold_graphic"])
        if sh["est_dur"] > limit and not is_motion and rm != "motion":      # motion scenes have their own pacing rules
            warn(sh["line"], f"this {sh['type']} shot stays on screen ~{sh['est_dur']:.0f} s; "
                             f"add another shot inside that narration so the picture changes")
        if sh["type"] in CHARACTER_SHOTS and not char:
            err(sh["line"], f"[{sh['type']}: ...] needs a presenter: add 'character: <name>' to the header")
        if sh["type"] == "talk" and not sh["set"]:
            sh["set"] = next(iter(char["sets"])) if char else "studio"
        if sh["type"] == "talk" and char:
            if sh["pose"] not in char["poses"]:
                err(sh["line"], f"pose '{sh['pose']}' isn't in {char['name']}'s pack: {', '.join(char['poses'])}")
            if sh["set"] not in char["sets"]:
                err(sh["line"], f"set '{sh['set']}' isn't defined for {char['name']}: {', '.join(char['sets'])}")
        if sh["type"] in ("ai", "stock", "act") and BAD_AI_WORDS.search(sh.get("prompt") or sh.get("query", "")):
            warn(sh["line"], "AI images can't draw readable text or logos; use a [card: ...] for words")
        if sh["type"] == "quote" and not sh["by"]:
            warn(sh["line"], "quote has no source; add | who said it (never invent quotes)")
    for seg in segments:
        if seg["words"] > 70 and not is_motion:
            warn(seg["line"], f"{seg['words']} words without a cut; split it with another shot tag")
        if re.search(r"\b(e\.g|i\.e|etc|vs)\.", seg["text"], re.I):
            warn(seg["line"], "abbreviations like e.g. / vs. sound odd when spoken; write them out")

    counts = {k: sum(1 for s in shots if s["type"] == k) for k in VISUAL}
    sfx_all = sfx_files()
    sfx_cues, sfx_missing = [], []
    if meta["sfx"] == "off":
        for seg in segments:
            seg["sfx"] = []
    elif meta["sfx"] in ("auto", "rich") and not clip and rm != "motion":   # motion: placed by the animation
        sfx_cues, sfx_missing = sfx.auto_cues(segments, shots, chapters, sfx_all, meta["sfx"])
    for seg in segments:
        for cue in seg["sfx"]:
            if not best_match(cue, sfx_all):
                warn(seg["line"], f"no sound effect matches '{cue}' (it will be skipped). Add one to "
                                  f"assets/library/sfx/<kind>/")
    tracks = music_files(60)
    music_items = [n.strip() for n in (meta.get("music") or "").split(",") if n.strip()]
    if meta.get("music") and not tracks:
        warn(1, "there are no music tracks yet (1 minute or longer): the video will have no music. Upload "
                "some to assets/library/music/<mood>/")
    elif len(music_items) <= 1:
        if meta.get("music") and not best_match(meta["music"], tracks):
            warn(1, f"no music track matches '{meta['music']}'; a random track will be used")
    else:
        for item in music_items:
            if not best_match(item, tracks):
                warn(1, f"no music track matches '{item}'; a random track will be used in its place")
    if chapters and not P["chapters"]:
        warn(chapters[0]["line"], "Shorts have no chapters; the ## headings are ignored")
    elif chapters:
        real = [c for c in chapters if c["segment"] < len(segments)]
        if len(real) < 3:
            warn(chapters[0]["line"], "YouTube needs at least 3 chapters (## headings) to show chapters")
        elif real[0]["segment"] != 0:
            warn(real[0]["line"], "the first ## heading must come before the first narration for chapters to work")
    prompts = [(s.get("prompt") or s.get("query", "")).strip().lower() for s in shots if s["type"] in ("ai", "stock")]
    dups = sorted({p for p in prompts if prompts.count(p) > 1})
    if dups:
        warn(1, "these image prompts repeat word for word, so they make the same picture: " + "; ".join(dups[:5]))

    if char and not is_motion:
        run, run_start = 0, None
        for sh in shots:
            if sh["type"] in CHARACTER_SHOTS:
                run = 0
                continue
            run += 1
            if run == 4:
                warn(sh["line"], f"4 shots in a row without {char['name']}; put a [talk:] or [act:] in between")
        for c in (chapters if P["chapters"] else []):
            first = next((sh for sh in shots if sh.get("first_segment", -1) >= c["segment"]), None)
            if first and first["type"] != "talk" and c["segment"] < len(segments):
                warn(c["line"], f"chapter '{c['title']}' doesn't start with {char['name']} on camera ([talk:])")
    char_secs = sum(sh["est_dur"] for sh in shots if sh["type"] in CHARACTER_SHOTS)
    talk_secs = sum(sh["est_dur"] for sh in shots if sh["type"] == "talk")
    ai_images = counts["ai"] + counts["stock"] + counts["act"]   # [stock:]/[act:] are made by the image model
    graphics = counts["card"] + counts["number"] + counts["quote"] + counts["chart"]
    if total > 120 and ai_images and ai_images / max(1, len(shots)) > 0.8:
        warn(1, f"{ai_images} of {len(shots)} shots are AI images; turning some key facts into "
                f"[card]/[number]/[chart] shots renders faster and keeps it varied")
    # ------------------------------------------------- per-type length, hook and ending
    if clip:
        total = max(0.0, clip["end"] - clip["start"])
    mins = lambda x: f"{int(x // 60)}:{int(x % 60):02d}"
    if P["max_sec"] and total > P["max_sec"]:
        err(1, f"a Short must be under {mins(P['max_sec'])}; this one is ~{mins(total)}. Cut it down")
    if P["min_sec"] and total < P["min_sec"]:
        err(1, f"a Short must be at least {P['min_sec']} s; this one is ~{total:.0f} s")
    lo, hi = P["plan_sec"]
    if not (P["max_sec"] and total > P["max_sec"]) and not (P["min_sec"] and total < P["min_sec"]) \
            and (total < lo or total > hi) and not clip:
        warn(1, f"{P['label']}s are planned at {mins(lo)}-{mins(hi)}; this one is ~{mins(total)}")
    if segments:
        first_text = " ".join(sg["text"] for sg in segments[:2])[:200]
        last_text = " ".join(sg["text"] for sg in segments[-3:])
        if vtype == "short":
            if INTRO_RE.search(first_text):
                warn(segments[0]["line"], "a Short has to hook in the first 2 seconds: open with the surprise, "
                                          "no intro like 'today we'll look at'")
            if OUTRO_RE.search(segments[-1]["text"]):
                warn(segments[-1]["line"], "end a Short on a line that loops back into the first line, "
                                           "not a sign-off or 'subscribe'")
        elif "?" not in last_text:
            warn(segments[-1]["line"], "end a full video with a question for the comments")
    stats = {
        "segments": len(segments), "shots": len(shots), "words": sum(s["words"] for s in segments),
        "est_seconds": round(total), "by_type": counts, "ai_images": ai_images, "graphics": graphics,
        "chapters": len(chapters), "avg_shot_seconds": round(total / max(1, len(shots)), 1),
        "est_draft_seconds": round(20 + total * 0.12),
        "est_final_seconds": round(40 + total * 0.35 + (ai_images + 2) * C.SECONDS_PER_IMAGE + talk_secs * 0.6),
        "character": char["name"] if char else None,
        "character_share": round(100 * char_secs / max(1.0, total)) if char else 0,
        "presenter_seconds": round(talk_secs),
        "type": vtype, "type_label": P["label"], "clip": clip, "style": vstyle,
        "rendering_method": rm, "rendering_method_label": C.RENDERING_METHODS[rm],
        "sfx": {"mode": meta["sfx"], "script": sum(len(s["sfx"]) for s in segments), "auto": len(sfx_cues),
                "cues": sfx_cues, "missing": sfx_missing},
        "music": {"off": meta["music_off"], "items": music_items, "tracks_available": len(tracks)},
    }
    if clip:
        stats.update(est_draft_seconds=round(10 + total * 0.4), est_final_seconds=round(15 + total * 1.2))
    if is_motion and segments:
        from . import script_v3
        scenes = script_v3.check(meta, segments, shots, warn, err, wps)
        from . import props_gen
        gens, plates = props_gen.missing({"shots": shots})      # only ones not cached yet
        pics = sum(1 for sh in shots if sh["type"] in ("ai", "stock"))
        stats.update(scenes=scenes, motion_elements=sum(sc["elements"] for sc in scenes), ai_images=gens + plates + pics,
                     new_props=gens, new_plates=plates,
                     est_draft_seconds=round(15 + total * 1.0),
                     est_final_seconds=round(20 + total * 1.6 + (gens + pics) * C.SECONDS_PER_IMAGE))
        errors.sort(key=lambda e: e["line"])
        warnings.sort(key=lambda w: w["line"])
    if rm == "motion":
        # no AI images; HyperFrames renders ~2.5 s per second of video on the M5 (2026-11-11: 62.8 s video,
        # draft 157 s, final 155 s); a new scene every ~2.6 s (beats.py)
        stats.update(est_draft_seconds=round(20 + total * 2.3), est_final_seconds=round(25 + total * 2.3),
                     motion_scenes=max(1, round(total / 2.6)))
    for c in chapters:
        c["est_start"] = segments[c["segment"]]["est_start"] if c["segment"] < len(segments) else total
    errors.sort(key=lambda e: e["line"])
    warnings.sort(key=lambda w: w["line"])
    return {"ok": not errors, "errors": errors, "warnings": warnings, "meta": meta,
            "segments": segments, "shots": shots, "chapters": chapters, "stats": stats}
