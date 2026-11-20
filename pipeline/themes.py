"""Storyboard themes: presets/storyboard_themes/<id>.json (docs/STORYBOARD_PLAN.md). Script header: theme: <id>.

A theme is configuration only. It bundles
  settings      default header values, per rendering method ("all" / "motion" / "ai_image"): show, typography,
                palette, fonts, icon_style, camera, transitions, captions, art_style, music, sfx. A line the script
                writes itself always wins. The stages keep reading the same header keys as before, so no stage knows
                about themes.
  scene_style   (optional, motion graphics) a scene design of its own: a base format (motion_gfx/formats.py) + its
                own colour palettes, fonts, card / line colours, line weight, shadow, backdrop, scene-type weights and
                bans, entrances, camera pool, transitions, chapter kicker, music moods. Registered as the format
                "theme_<id>", never picked by show: auto.
  supports      rendering methods and video formats the theme was made for (Check warns outside them).
theme: auto (the default, no settings) = the behaviour before themes."""

import hashlib
import json

from . import presets

KIND = "storyboard_themes"
SETTING_KEYS = {"show", "typography", "palette", "fonts", "icon_style", "camera", "transitions", "captions",
                "art_style", "music", "sfx", "look"}
STYLE_KEYS = {"base", "palettes", "fonts", "icon_style", "card", "line", "line_scale", "shadow", "backdrop", "rough",
              "frames", "ambient", "weights", "banned", "entrances", "ease", "transitions", "cameras", "signature",
              "sfx", "music", "kicker"}
SHADOWS = ("offset", "soft", "glow", "none")
BACKDROPS = (None, "grid", "dots", "news", "lamp", "crt", "blueprint", "ruled")


def format_id(theme_id: str) -> str:
    return f"theme_{theme_id}"


def check(pid: str, data: dict) -> None:
    """Theme-specific checks (presets.validate calls this). Colours and names end up in the scenes' CSS."""
    where = f"presets/{KIND}/{pid}.json"
    bad = lambda m: presets.PresetError(f"{where}: {m}")  # noqa: E731
    for group, vals in data["settings"].items():
        if group not in ("all", "motion", "ai_image") or not isinstance(vals, dict):
            raise bad(f"settings.{group}: use the groups all / motion / ai_image, each an object")
        for k, v in vals.items():
            if k not in SETTING_KEYS or not isinstance(v, str):
                raise bad(f"settings.{group}.{k}: must be text and one of {', '.join(sorted(SETTING_KEYS))}")
    st = data.get("scene_style")
    if not st:
        return
    from .motion_gfx import compose, camera, design as D, formats as Fm
    if set(st) - STYLE_KEYS:
        raise bad(f"scene_style: unknown field(s) {', '.join(sorted(set(st) - STYLE_KEYS))}")
    if st.get("base") not in Fm.FORMATS:
        raise bad(f"scene_style.base must be one of {', '.join(Fm.FORMATS)}")
    for p in st.get("palettes") or []:
        if not (isinstance(p, dict) and presets.ID_RE.fullmatch(str(p.get("name") or "")) and
                all(isinstance(p.get(k), str) and presets.COLOUR_RE.fullmatch(p[k]) for k in ("bg", "ink", "hi", "pop", "soft"))):
            raise bad("scene_style.palettes: each needs a name and the colours bg, ink, hi, pop, soft like #14233B")
    for k in ("card", "line"):
        if k in st and not (isinstance(st[k], str) and presets.COLOUR_RE.fullmatch(st[k])):
            raise bad(f"scene_style.{k} must be a colour like #FFFFFF")
    if st.get("shadow", "offset") not in SHADOWS or st.get("backdrop") not in BACKDROPS:
        raise bad(f"scene_style: shadow is one of {', '.join(SHADOWS)}; backdrop one of "
                  f"{', '.join(str(b) for b in BACKDROPS)}")
    for k, valid in (("fonts", D.FONT_PAIRS), ("entrances", compose.ENTRANCES), ("cameras", camera.MOVES),
                     ("icon_style", ("sticker", "plain"))):
        if any(x not in valid for x in st.get(k) or []):
            raise bad(f"scene_style.{k}: use only {', '.join(valid)}")
    if not isinstance(st.get("line_scale", 1.0), (int, float)) or not isinstance(st.get("weights", {}), dict):
        raise bad("scene_style: line_scale is a number, weights an object {scene type: number}")


def load(theme_id: str) -> dict:
    return presets.load(KIND, theme_id)


def version(theme: dict) -> str:
    """Changes whenever the theme file's content changes (job.json: which version a video was made with)."""
    body = {k: v for k, v in theme.items() if k != "id"}
    return f"{theme.get('version', 1)}-" + hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:8]


def defaults(theme: dict, method: str) -> dict:
    """Header values the theme sets for this rendering method."""
    s = theme.get("settings") or {}
    out = {**(s.get("all") or {}), **(s.get(method) or {})}
    if method == "motion" and theme.get("scene_style"):
        out["show"] = format_id(theme["id"])
    return out


def swatch(theme: dict) -> list:
    """Colours for the theme tile: its own palettes, else its format's."""
    try:
        from .motion_gfx import design as D, formats as Fm
        st = theme.get("scene_style") or {}
        pals = st.get("palettes")
        if not pals:
            show = ((theme.get("settings") or {}).get("motion") or {}).get("show")
            if not show:
                return []
            names = D.PALETTE_SETS[Fm.get(show)["palettes"][0]]
            pals = [p for n in names for p in D.PALETTES if p["name"] == n]
        return [[p["bg"], p["ink"], p["pop"]] for p in pals[:3]]
    except Exception:  # noqa: BLE001  (a tile without colours is fine)
        return []


def register(Fm) -> None:
    """Adds every theme's scene_style as the format theme_<id> (formats.py calls this once, when it is imported)."""
    from .motion_gfx import design as D, typography as TY
    for tid in presets.ids(KIND):
        try:
            th = load(tid)
        except presets.PresetError:
            continue                                   # tools/check_presets.py reports it
        st = th.get("scene_style")
        if not st:
            continue
        base, fid = Fm.FORMATS[st["base"]], format_id(tid)
        f = dict(base, label=th["label"], description=th["description"], theme=tid,
                 **{k: v for k, v in st.items() if k not in ("base", "palettes", "weights")})
        f["weights"] = dict(base["weights"], **(st.get("weights") or {}))
        if st.get("palettes"):
            have = {p["name"] for p in D.PALETTES}
            D.PALETTES += [dict(p) for p in st["palettes"] if p["name"] not in have]
            D.PALETTE_SETS[fid] = [p["name"] for p in st["palettes"]]
            f["palettes"] = [fid]
        Fm.EXTRA[fid] = f
        TY.POOLS[fid] = TY.pool(st["base"])
        if st["base"] in TY.EXTRA_FONTS:
            TY.EXTRA_FONTS[fid] = TY.EXTRA_FONTS[st["base"]]
