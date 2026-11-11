"""
presets.py  -  selectable presets for voice, captions, art style and music (presets/<kind>/<id>.json).

A preset id is its file name without .json. Every preset has a "label" (shown in the UI) and a "licence".
Script header keys pick them (all optional, a missing key = the default preset):

    language: en               (must match a voice preset's language)
    voice: en_us_michael       (a voice preset id, OR a Kokoro voice id like bm_george as before)
    captions: amber_word
    art_style: doc_photo
    music: any                 (a music preset id, OR track names from assets/audio/bgm as before)

The default presets reproduce today's config values exactly. Stages do not read presets yet (roadmap F2-F6):
for now they are resolved at Check and written to output/jobs/<id>/job.json on every render.
"""

import json
import re
import time
from pathlib import Path

from . import config as C

PRESETS_DIR = C.BASE_DIR / "presets"
KINDS = ("voices", "captions", "art_styles", "music", "niches")
DEFAULTS = {"voices": "en_us_michael", "captions": "amber_word", "art_styles": "doc_photo", "music": "any",
            "niches": "general"}
DEFAULT_LANGUAGE = "en"
HEADER_KEYS = {"voice": "voices", "captions": "captions", "art_style": "art_styles", "music": "music"}
DEFAULT_CHOSEN = {"language": DEFAULT_LANGUAGE, **{key: DEFAULTS[kind] for key, kind in HEADER_KEYS.items()}}
ID_RE = re.compile(r"[a-z0-9][a-z0-9_]*")
KOKORO_VOICE_RE = re.compile(r"[a-z][fm]_[a-z0-9]+")      # am_michael, bm_george, af_heart ...
COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{6}")


class PresetError(ValueError):
    pass


# ------------------------------------------------------------------ schema ---
# field -> type (or tuple of types); nested dicts are checked the same way.
NUM = (int, float)
LAYOUT = {"size": NUM, "margin_v": NUM, "margin_l": NUM, "margin_r": NUM, "max_words": int, "max_chars": int}
SCHEMA = {
    "voices": {"engine": str, "model": str, "language": str, "lang": str, "voice": str, "speed": NUM, "wpm": NUM},
    # caption style = how the burned-in words look (captions.write_ass). amber_word = the look before styles.
    "captions": {"description": str, "highlight": str, "case": str, "font": str, "font_file": str, "bold": bool,
                 "italic": bool, "text_colour": "colour",
                 "highlight_colour": "colour", "outline_colour": "colour", "shadow_colour": "colour",
                 "shadow_transparency": int, "outline_ratio": NUM, "outline_min_px": int, "position": str,
                 "group": {"max_gap_sec": NUM, "break_after": str, "linger_sec": NUM, "min_word_sec": NUM},
                 "layouts": {"landscape": LAYOUT, "vertical": LAYOUT, "short": LAYOUT},
                 "srt": {"max_chars": int, "line_chars": int}},
    # art style = words around every [ai:]/[stock:] prompt and the 2 AI thumbnails (visuals.style_prompt).
    # doc_photo = today's look; .env IMAGE_STYLE (if set) still replaces doc_photo's suffix.
    "art_styles": {"description": str, "prefix": str, "suffix": str, "stock_suffix": str, "realistic": bool,
                   "lora": "null", "lora_scale": NUM, "steps": "null|int"},
    "music": {"mode": str, "folder": str, "min_track_sec": NUM, "volume": NUM,
              "duck": {"threshold": NUM, "ratio": NUM, "attack_ms": NUM, "release_ms": NUM},
              "fade_in_sec": NUM, "chapter_crossfade_sec": NUM, "loudness_lufs": NUM},
    "niches": {"language": str, "voice": str, "captions": str, "art_style": str, "music": str},
}
# fields a preset may leave out (checked when present)
OPTIONAL = {
    "captions": {"enabled": bool, "box_style": bool, "alignment": int, "blur_ratio": NUM, "shadow_ratio": NUM, "spacing_ratio": NUM, "angle": NUM,
                 "pop": bool, "box_colour": "colour", "box_pad_ratio": NUM},
    "voices": {"description": str, "gender": str, "accent": str, "grade": str},
    # motion style (pipeline/props_gen.py): words for a cut-out prop and for a background set plate
    "art_styles": {"prop_suffix": str, "plate_suffix": str},
}
CHOICES = {("captions", "highlight"): ("word", "box", "none"), ("captions", "case"): ("as_is", "upper", "lower")}


def _rel(path: Path) -> str:
    try:
        return path.relative_to(C.BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def _check(data, schema, where, path, prefix=""):
    for field, want in schema.items():
        name = prefix + field
        if field not in data:
            raise PresetError(f"{where}: field '{name}' is missing")
        v = data[field]
        if isinstance(want, dict):
            if not isinstance(v, dict):
                raise PresetError(f"{where}: field '{name}' must be an object {{...}}")
            _check(v, want, where, path, name + ".")
        elif want == "null":
            if v is not None:
                raise PresetError(f"{where}: field '{name}' must be null for now (the image worker can't load "
                                  f"a LoRA yet), got {v!r}")
        elif want == "null|int":
            if v is not None and (isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 50):
                raise PresetError(f"{where}: field '{name}' must be null (= the default) or a whole number "
                                  f"1-50, got {v!r}")
        elif want == "colour":
            if not (isinstance(v, str) and COLOUR_RE.fullmatch(v)):
                raise PresetError(f"{where}: field '{name}' must be a colour like #FFB020, got {v!r}")
        else:
            types = want if isinstance(want, tuple) else (want,)
            if isinstance(v, bool) and bool not in types or not isinstance(v, types):
                tname = "number" if want is NUM else {str: "text", int: "whole number", bool: "true/false"}[want]
                raise PresetError(f"{where}: field '{name}' must be a {tname}, got {v!r}")


def validate(kind: str, pid: str, data) -> None:
    where = f"presets/{kind}/{pid}.json"
    if not isinstance(data, dict):
        raise PresetError(f"{where}: must be a JSON object {{...}}")
    for field in ("label", "licence"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise PresetError(f"{where}: field '{field}' is missing or empty")
    if "id" in data and data["id"] != pid:
        raise PresetError(f"{where}: field 'id' is {data['id']!r} but must equal the file name ({pid!r})")
    _check(data, SCHEMA[kind], where, where)
    _check(data, {f: t for f, t in OPTIONAL.get(kind, {}).items() if f in data}, where, where)
    if kind == "captions":
        if not (C.FONTS_DIR / data["font_file"]).exists():
            raise PresetError(f"{where}: font_file '{data['font_file']}' isn't in assets/fonts")
        if data["highlight"] == "box" and "box_colour" not in data:
            raise PresetError(f"{where}: highlight 'box' needs a 'box_colour'")
    for (k, field), allowed in CHOICES.items():
        if k == kind and data[field] not in allowed:
            raise PresetError(f"{where}: field '{field}' must be one of {', '.join(allowed)}, got {data[field]!r}")
    if kind == "niches":
        for key, k in HEADER_KEYS.items():
            if data[key] not in ids(k):
                raise PresetError(f"{where}: field '{key}' names '{data[key]}', which isn't in presets/{k}/ "
                                  f"(valid: {', '.join(ids(k))})")


# ------------------------------------------------------------------- files ---
def _kind(kind: str) -> str:
    if kind not in KINDS:
        raise PresetError(f"unknown preset kind '{kind}' (kinds: {', '.join(KINDS)})")
    return kind


def ids(kind: str):
    d = PRESETS_DIR / _kind(kind)
    return sorted(p.stem for p in d.glob("*.json") if ID_RE.fullmatch(p.stem)) if d.is_dir() else []


def load(kind: str, pid: str) -> dict:
    """One preset as a dict (+ "id"), schema-checked. Raises PresetError naming the file and field."""
    _kind(kind)
    if not ID_RE.fullmatch(pid or ""):
        raise PresetError(f"'{pid}' is not a valid {kind} preset id (valid: {', '.join(ids(kind))})")
    path = PRESETS_DIR / kind / f"{pid}.json"
    if not path.exists():
        raise PresetError(f"{_rel(path)} doesn't exist (valid {kind}: {', '.join(ids(kind))})")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise PresetError(f"{_rel(path)}: not valid JSON ({e})")
    validate(kind, pid, data)
    return {"id": pid, **data}


STYLE_PREVIEWS = C.ASSETS / "style_previews"     # assets/style_previews/<id>.jpg (gitignored, made on the Mac)


def preview_path(style_id: str) -> Path:
    return STYLE_PREVIEWS / f"{style_id}.jpg"


def list(kind: str):   # noqa: A001  (the brief's name: presets.list(kind))
    """[{id, label, description?}] for every valid preset of one kind (broken files are skipped;
    validate_all() reports them). Art styles also get realistic + preview_url (None until a preview is made)."""
    out = []
    for pid in sorted(ids(kind), key=lambda i: i != DEFAULTS[kind]):     # the default first
        try:
            p = load(kind, pid)
        except PresetError:
            continue
        item = {"id": pid, "label": p["label"]}
        if "description" in p:
            item["description"] = p["description"]
        if kind == "voices":
            item.update({k: p.get(k) for k in ("voice", "gender", "accent", "grade", "speed")})
        if kind == "art_styles":
            f = preview_path(pid)
            item["realistic"] = p["realistic"]
            item["preview_url"] = f"/api/art_styles/{pid}/preview.jpg?v={int(f.stat().st_mtime)}" if f.exists() else None
        out.append(item)
    return out


def validate_all():
    """Every preset file checked. Returns a list of error messages (empty = all good)."""
    errs = []
    for kind in KINDS:
        if DEFAULTS[kind] not in ids(kind):
            errs.append(f"presets/{kind}/{DEFAULTS[kind]}.json (the default) is missing")
        for pid in ids(kind):
            try:
                load(kind, pid)
            except PresetError as e:
                errs.append(str(e))
        for p in (PRESETS_DIR / kind).glob("*.json"):
            if not ID_RE.fullmatch(p.stem):
                errs.append(f"{_rel(p)}: file name must be lower-case letters, digits and _ only")
    return errs


def languages():
    return sorted({load("voices", v)["language"] for v in ids("voices")})


# ------------------------------------------------------------- script header ---
def resolve(header: dict, char=None):
    """Script header -> ({language, voice, captions, art_style, music} preset ids, overrides, errors).
    header = the front matter as written (before the parser fills in voice/speed). Old-style values keep working:
    voice: <Kokoro voice id> and music: <track names> are recorded as overrides of the default preset."""
    errors, overrides = [], {}
    chosen = {}

    def pick(key, value):
        kind = HEADER_KEYS[key]
        valid = ids(kind)
        if value in valid:
            try:
                load(kind, value)
            except PresetError as e:
                errors.append(str(e))
                return DEFAULTS[kind]
            return value
        errors.append(f"{key}: '{value}' isn't a preset in presets/{kind}/. Valid: {', '.join(valid)}")
        return DEFAULTS[kind]

    lang = (header.get("language") or DEFAULT_LANGUAGE).strip().lower()
    langs = languages()
    if lang not in langs:
        errors.append(f"language '{lang}' has no voice preset. Valid: {', '.join(langs)}")
        lang = DEFAULT_LANGUAGE
    chosen["language"] = lang

    voice = (header.get("voice") or "").strip()
    if voice and voice.lower() in ids("voices"):
        chosen["voice"] = pick("voice", voice.lower())
    else:
        chosen["voice"] = DEFAULTS["voices"]
        if voice and not KOKORO_VOICE_RE.fullmatch(voice):
            errors.append(f"voice '{voice}' is not a voice preset ({', '.join(ids('voices'))}) "
                          f"or a Kokoro voice id like am_michael")
    vp = load("voices", chosen["voice"]) if chosen["voice"] in ids("voices") else None
    if vp and vp["language"] != lang:
        errors.append(f"voice preset '{vp['id']}' speaks '{vp['language']}', but language is '{lang}'")

    for key in ("captions", "art_style"):
        v = (header.get(key) or "").strip().lower()
        chosen[key] = pick(key, v) if v else DEFAULTS[HEADER_KEYS[key]]

    music = (header.get("music") or "").strip()
    if music and music.lower() in ids("music"):
        chosen["music"] = pick("music", music.lower())
    else:
        chosen["music"] = DEFAULTS["music"]
        if music:   # old style: track names (matched against file names, as before)
            overrides["music"] = {"tracks": [n.strip() for n in music.split(",") if n.strip()],
                                  "from": "script music:"}
    return chosen, overrides, errors


def voice_settings(chosen: dict, header: dict, char=None):
    """(Kokoro voice id, speed, where they came from) for the parser, with today's priority:
    script voice:/speed:  >  character file  >  .env KOKORO_VOICE/KOKORO_SPEED (= the default preset's values).
    A voice PRESET id in voice: gives that preset's voice and speed (script speed: still wins)."""
    voice = (header.get("voice") or "").strip()
    speed = (header.get("speed") or "").strip()
    src = []
    if speed:
        src.append("script speed:")
    if voice and voice.lower() in ids("voices"):
        vp = load("voices", chosen["voice"])
        return vp["voice"], speed or str(vp["speed"]), src
    if voice:
        src.insert(0, "script voice:")
    if char:
        if not voice and char.get("voice"):
            voice = char["voice"]
            src.append(f"character {char['name']} voice")
        if not speed and char.get("speed"):
            speed = str(char["speed"])
            src.append(f"character {char['name']} speed")
    return voice or C.KOKORO_VOICE, speed, src


# ------------------------------------------------------------------ job.json ---
def _config_overrides(meta):
    """Where the values a render really uses differ from the presets (header, character or .env)."""
    out = {}
    vp = load("voices", meta["presets"]["voice"])
    diff = {k: meta[k] for k in ("voice", "speed") if meta.get(k) is not None and meta[k] != vp[k]}
    if diff:
        out["voice"] = {**diff, "from": ", ".join(meta.get("voice_from") or []) or ".env KOKORO_VOICE/KOKORO_SPEED"}
    ap = load("art_styles", meta["presets"]["art_style"])
    if ap["id"] == "doc_photo" and C.IMAGE_STYLE != ap["suffix"]:
        out["art_style"] = {"suffix": C.IMAGE_STYLE, "from": ".env IMAGE_STYLE"}
    mp = load("music", meta["presets"]["music"])
    m = dict((meta.get("preset_overrides") or {}).get("music") or {})
    env = {"volume": C.BGM_VOLUME, "loudness_lufs": C.TARGET_LUFS}
    diff = {k: v for k, v in env.items() if v != mp[k]}
    if C.BGM_FILE:
        diff["file"] = C.BGM_FILE
    if diff:
        m.update(diff)
        m["from"] = (m["from"] + " + " if m.get("from") else "") + ".env BGM_*/TARGET_LUFS"
    if m:
        out["music"] = m
    return out


def job_spec(job_id: str, mode: str, parsed: dict) -> dict:
    meta = parsed["meta"]
    chosen = meta["presets"]
    W, H = C.SIZES[(meta["format"], "final" if mode == "final" else "draft")]
    char = meta.get("character_data")
    return {
        "id": job_id,
        "mode": mode,
        "written": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "input": {"mode": "clip" if meta.get("clip") else "script", "script_path": "script.md", "niche": None,
                  "clip": meta.get("clip")},
        "type": meta["type"],
        "format": meta["format"],
        "title": meta.get("title", ""),
        "character": char["name"] if char else None,
        "language": chosen["language"],
        "presets": {
            "voice": load("voices", chosen["voice"]),
            "captions": load("captions", chosen["captions"]),
            "art_style": load("art_styles", chosen["art_style"]),
            "music": load("music", chosen["music"]),
        },
        "overrides": _config_overrides(meta),
        "rendering_method": meta.get("rendering_method", "ai_image"),
        "output": {"resolution": f"{W}x{H}", "fps": C.FPS, "video_bitrate": C.VIDEO_BITRATE[
            "final" if mode == "final" else "draft"]},
    }


def write_job(job_dir: Path, job_id: str, mode: str, parsed: dict) -> Path:
    out = job_dir / "job.json"
    tmp = job_dir / "job.json.tmp"
    tmp.write_text(json.dumps(job_spec(job_id, mode, parsed), indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(out)
    return out
