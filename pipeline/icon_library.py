"""The icon library of the motion-graphics renderer (rendering_method: motion): assets/library/icons/.

  packs        PACKS: where each pack comes from (a pinned @iconify-json npm package, or Natural Earth), its role
  licences     check_licence(): a strict allow-list. Anything else is refused by the importer.
  storage      assets/library/icons/<set>/icons.json (made by tools/import_icon_packs.py, NOT in git: it is rebuilt
               from the pinned npm packages by setup.sh) + LICENCE (in git) + a row in CREDITS.md and NOTICE
  index        assets/library/icons/index.json + embeddings.npy (tools/build_icon_index.py)
  svg(id)      one icon as a standalone SVG string

An icon id is "<set>:<name>", e.g. "fluent_flat:low-battery".
"""

import json
from functools import lru_cache
from pathlib import Path

from . import config as C
from .util import PipelineError

ICONS_DIR = C.BASE_DIR / "assets" / "library" / "icons"
NPM_DIR = C.BASE_DIR / "node_modules" / "@iconify-json"
INDEX = ICONS_DIR / "index.json"
EMBED = ICONS_DIR / "embeddings.npy"

# SPDX id -> how the licence is treated. "by" = needs a credit line (only with ALLOW_CC_BY=1 in .env).
ALLOWED = {"MIT": "free", "Apache-2.0": "free", "ISC": "free", "CC0-1.0": "free", "public-domain": "free",
           "CC-BY-4.0": "by"}

# role "family": a full-colour illustration set, a video uses ONE of them. "line": small one-colour icons for
# bullets and labels. "flags": country flags. "map": country shapes.
PACKS = {
    "fluent_flat": {"npm": "fluent-emoji-flat", "label": "Fluent Emoji Flat", "role": "family", "emoji": True,
                    "licence_url": "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/LICENSE"},
    "fluent_color": {"npm": "fluent-emoji", "label": "Fluent Emoji Color", "role": "family", "emoji": True,
                     "licence_url": "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/LICENSE"},
    # Noto is pinned to 1.2.7 (2025-09) ON PURPOSE: upstream then had svg/LICENSE = Apache-2.0 next to the SVGs.
    # In 2026-09 upstream moved the SVGs and the only licence file left is OFL-1.1 (not on the allow-list), so
    # newer packages are not clearly Apache-2.0. Don't bump it without checking the licence again.
    "noto": {"npm": "noto", "label": "Noto Emoji", "role": "family", "emoji": True,
             "licence_url": "https://raw.githubusercontent.com/googlefonts/noto-emoji/5628587386/svg/LICENSE"},
    "phosphor": {"npm": "ph", "label": "Phosphor Icons (fill + duotone)", "role": "line",
                 "licence_url": "https://raw.githubusercontent.com/phosphor-icons/core/main/LICENSE"},
    "tabler": {"npm": "tabler", "label": "Tabler Icons", "role": "line",
               "licence_url": "https://raw.githubusercontent.com/tabler/tabler-icons/main/LICENSE"},
    "flags": {"npm": "flag", "label": "Flag Icons", "role": "flags",
              "licence_url": "https://raw.githubusercontent.com/lipis/flag-icons/main/LICENSE"},
    "natural_earth": {"npm": None, "label": "Natural Earth country shapes (1:110m)", "role": "map"},
    "twemoji": {"npm": "twemoji", "label": "Twemoji", "role": "family", "emoji": True, "optional": True,
                "licence_url": "https://raw.githubusercontent.com/jdecked/twemoji/main/LICENSE-GRAPHICS"},
}
FAMILIES = [k for k, v in PACKS.items() if v["role"] == "family"]
SKIN = ("-light", "-medium-light", "-medium", "-medium-dark", "-dark")


def allow_cc_by() -> bool:
    return C.env("ALLOW_CC_BY") == "1"


def check_licence(spdx: str, what: str) -> str:
    """Returns "free" or "by"; raises PipelineError for anything outside the allow-list."""
    kind = ALLOWED.get((spdx or "").strip())
    if kind is None:
        raise PipelineError(f"{what}: licence '{spdx or 'unknown'}' is not allowed. Allowed: MIT, Apache-2.0, ISC, "
                            f"CC0, public domain (and CC BY 4.0 only with ALLOW_CC_BY=1 in .env)")
    if kind == "by" and not allow_cc_by():
        raise PipelineError(f"{what}: licence {spdx} needs a credit line in every video description. It is only used "
                            f"with ALLOW_CC_BY=1 in .env (the credit is then added automatically)")
    return kind


def installed() -> list:
    """Ids of the packs imported on this machine."""
    return [k for k in PACKS if (ICONS_DIR / k / "icons.json").exists()]


def usable_families() -> list:
    """Imported illustration families a video may use (CC BY ones only while ALLOW_CC_BY=1)."""
    out = []
    for k in FAMILIES:
        if k in installed() and (ALLOWED.get(load(k)["licence"]) == "free" or allow_cc_by()):
            out.append(k)
    return out


@lru_cache(maxsize=None)
def load(set_id: str) -> dict:
    p = ICONS_DIR / set_id / "icons.json"
    if not p.exists():
        raise PipelineError(f"the icon pack '{set_id}' isn't imported on this machine. Run once in the project "
                            f"folder: npm ci && bin/python tools/import_icon_packs.py")
    return json.loads(p.read_text(encoding="utf-8"))


def svg(icon_id: str, colour: str = "#111111") -> str:
    """A standalone SVG of one icon. One-colour packs (currentColor) are drawn in `colour`."""
    set_id, name = icon_id.split(":", 1)
    pack = load(set_id)
    ic = pack["icons"].get(name)
    if ic is None:
        raise PipelineError(f"icon '{icon_id}' isn't in the library")
    w, h = ic.get("w", pack["width"]), ic.get("h", pack["height"])
    body = ic["b"].replace("currentColor", colour)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">{body}</svg>')


def credit_lines(set_ids) -> list:
    """The description credit a video owes for the packs it used (CC BY packs only)."""
    out = []
    for s in sorted(set(set_ids)):
        if s in installed() and ALLOWED.get(load(s)["licence"]) == "by":
            pk = load(s)
            out.append(f"Icons: {pk['label']} by {pk['author']}, licensed under {pk['licence']} ({pk['licence_page']})")
    return out
