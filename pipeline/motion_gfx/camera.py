"""Camera moves with a 3D feel for motion-graphics scenes (header camera:, docs/SCRIPT_FORMAT.md).

Every scene is drawn in three layers that the camera moves at different speeds (2.5D parallax):

  far   #<host>-far    the format's backdrop (+ soft depth dots on formats without one), moves least
  mid   #<host>-mid    the layout's frame (card / tilt / band / spot)
  near  #<host>-near   the scene's own content, moves most

The camera rig #<host>-cam holds mid + near, so a 3D rotation (orbit, tilt) turns them together while the far layer
turns less. Moves (one per scene):

  dolly     push in: near grows faster than mid, far barely moves
  pull      dolly out (the reverse)
  truck     slide sideways: the layers slide by different amounts (parallax)
  orbit     slow turn around the subject (rotationY with perspective) + counter-slide of the near layer
  tilt      crane: rotationX with perspective + vertical parallax
  handheld  small seeded drift and sway, slow push
  focus     rack focus: the content starts soft and sharpens while the backdrop goes soft
  vertigo   dolly zoom: the content grows while the backdrop falls away
  flat      the old 2D drift (scale 1 -> 1.035, breathers 1.09 + a slide): the look before cameras existed
  off       no camera move

camera: auto (default) picks per scene from the format's pool by the scene's job (planner.cameras); a name or a
comma list pins the move / the pool. Everything is GSAP on transforms (and a filter blur for focus only).
"""

import hashlib

MOVES = ["dolly", "pull", "truck", "orbit", "tilt", "handheld", "focus", "vertigo"]
SPECIAL = ["auto", "off", "flat"]
ALL = SPECIAL + MOVES
DEFAULT_POOL = ["dolly", "truck", "orbit", "handheld", "vertigo", "tilt", "pull", "focus"]
SHARE = 0.30                       # no move above this share of the scenes (auto)


def _h(*parts) -> int:
    return int(hashlib.sha1(":".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:8], 16)


def parse_setting(value) -> tuple:
    """camera: header -> (mode, pool, bad names). mode = auto | off | flat | pool."""
    raw = [x.strip().lower() for x in str(value or "").split(",") if x.strip()]
    if not raw or raw == ["auto"]:
        return "auto", None, []
    bad = [x for x in raw if x not in ALL]
    if len(raw) == 1 and raw[0] in ("off", "flat"):
        return raw[0], None, bad
    pool = [x for x in raw if x in MOVES]
    bad += [x for x in raw if x in SPECIAL]          # auto/off/flat can't be mixed into a list
    return "pool", pool or None, bad


def depth_html(hid: str, pal: dict, W: int, H: int, seed: int) -> str:
    """Soft depth dots for the far layer of formats that draw no backdrop: big circles near the edges in the palette's
    ambient colour, so the parallax has something to move against."""
    out = []
    spots = [(0.06, 0.18), (0.93, 0.12), (0.88, 0.86), (0.10, 0.84), (0.50, 0.04), (0.97, 0.50)]
    for k, (x, y) in enumerate(spots):
        r = int(H * (0.07 + (_h(seed, hid, k) % 100) / 100 * 0.10))
        ring = (_h(seed, hid, "ring", k) % 3) == 0
        style = (f"border:{max(4, W // 320)}px solid {pal['soft']};" if ring else f"background:{pal['soft']};")
        out.append(f'<div style="position:absolute;left:{int(W * x) - r}px;top:{int(H * y) - r}px;width:{2 * r}px;'
                   f'height:{2 * r}px;border-radius:50%;{style}opacity:.55"></div>')
    return "".join(out)


def js(kind: str, hid: str, length: float, W: int, H: int, breather: bool = False, seed: int = 0) -> str:
    """GSAP lines for one scene's camera (the scene timeline is called `scene`, time 0 = the host's start)."""
    L = f"{length:.2f}"
    far, mid, near, cam = (f"#{hid}-{x}" for x in ("far", "mid", "near", "cam"))
    P = int(W * 1.6)                                  # perspective distance (px)
    if kind == "flat":                                # the pre-camera drift, byte for byte
        return (f'scene.fromTo("{cam}", {{scale: 1, x: 0}}, {{scale: {1.09 if breather else 1.035}, x: '
                f'{-int(W * 0.02) if breather else 0}, transformOrigin: "50% 50%", duration: {L}, ease: '
                f'"{"sine.inOut" if breather else "none"}"}}, 0);')
    if kind in ("off", None, ""):
        return ""
    s = 1.6 if breather else 1.0                      # a held scene travels further
    e = '"sine.inOut"'

    def tw(sel, a, b, ease=e, dur=L, at="0"):
        return f'scene.fromTo("{sel}", {{{a}}}, {{{b}, duration: {dur}, ease: {ease}}}, {at});'
    if kind == "dolly":
        return "\n".join([tw(far, "scale: 1.04", f"scale: {1.04 + 0.02 * s:.3f}"),
                          tw(mid, "scale: 1", f"scale: {1 + 0.04 * s:.3f}"),
                          tw(near, "scale: 1, y: 0", f"scale: {1 + 0.075 * s:.3f}, y: {-int(H * 0.008 * s)}",
                             '"power1.inOut"')])
    if kind == "pull":
        return "\n".join([tw(far, f"scale: {1.04 + 0.02 * s:.3f}", "scale: 1.04"),
                          tw(mid, f"scale: {1 + 0.04 * s:.3f}", "scale: 1"),
                          tw(near, f"scale: {1 + 0.08 * s:.3f}, y: {-int(H * 0.008 * s)}", "scale: 1, y: 0",
                             '"power2.out"')])
    if kind == "truck":
        d = -1 if _h(seed, hid, "dir") % 2 else 1
        return "\n".join([tw(far, f"scale: 1.06, x: {int(d * W * 0.010 * s)}", f"scale: 1.06, x: {-int(d * W * 0.010 * s)}"),
                          tw(mid, f"x: {int(d * W * 0.016 * s)}", f"x: {-int(d * W * 0.016 * s)}"),
                          tw(near, f"scale: 1.02, x: {int(d * W * 0.024 * s)}", f"scale: 1.02, x: {-int(d * W * 0.024 * s)}")])
    if kind == "orbit":
        d = -1 if _h(seed, hid, "dir") % 2 else 1
        a = 5.0 * min(s, 1.3)
        return "\n".join([
            tw(cam, f"rotationY: {d * a:.1f}, scale: 1.03, transformPerspective: {P}, transformOrigin: \"50% 55%\"",
               f"rotationY: {-d * a * 0.8:.1f}, scale: 1.03"),
            tw(far, f"scale: 1.08, rotationY: {d * a * 0.4:.1f}, x: {-int(d * W * 0.012)}, transformPerspective: {P}",
               f"scale: 1.08, rotationY: {-d * a * 0.3:.1f}, x: {int(d * W * 0.012)}"),
            tw(near, f"x: {-int(d * W * 0.012)}", f"x: {int(d * W * 0.012)}")])
    if kind == "tilt":
        d = -1 if _h(seed, hid, "dir") % 2 else 1
        return "\n".join([
            tw(cam, f"rotationX: {d * 5}, scale: 1.04, transformPerspective: {P}, transformOrigin: \"50% 60%\"",
               f"rotationX: {-d * 2}, scale: 1.04", '"power1.out"'),
            tw(far, f"scale: 1.08, y: {int(d * H * 0.018)}", f"scale: 1.08, y: {-int(d * H * 0.012)}", '"power1.out"'),
            tw(near, f"y: {int(d * H * 0.014)}", f"y: {-int(d * H * 0.010)}", '"power1.out"')])
    if kind == "vertigo":
        return "\n".join([tw(far, "scale: 1.14", "scale: 1.0", '"power2.inOut"'),
                          tw(mid, "scale: 1", "scale: 1.03", '"power2.inOut"'),
                          tw(near, "scale: 0.97", f"scale: {1.05 + 0.02 * s:.3f}", '"power2.inOut"')])
    if kind == "focus":
        rack = min(0.9, max(0.45, length * 0.25))
        return "\n".join([
            tw(far, 'scale: 1.04, filter: "blur(0px)"', 'scale: 1.07, filter: "blur(6px)"', '"power2.inOut"',
               f"{rack:.2f}", "0.15"),
            tw(near, 'scale: 0.985, filter: "blur(7px)"', 'scale: 1, filter: "blur(0px)"', '"power2.inOut"',
               f"{rack:.2f}", "0.15"),
            f'scene.set("{near}", {{filter: "none"}}, {0.15 + rack + 0.01:.2f});',
            tw(cam, "scale: 1", "scale: 1.035", '"none"')])
    if kind == "handheld":
        out = [tw(cam, "scale: 1.03", f"scale: {1.03 + 0.03 * s:.3f}", '"none"')]
        t, k = 0.0, 0
        x0 = y0 = r0 = 0.0
        while t < length:
            step = 0.7 + (_h(seed, hid, "hh", k) % 40) / 100
            step = min(step, length - t) if length - t > 0.25 else step
            x1 = ((_h(seed, hid, "x", k) % 200) / 100 - 1) * W * 0.004
            y1 = ((_h(seed, hid, "y", k) % 200) / 100 - 1) * H * 0.005
            r1 = ((_h(seed, hid, "r", k) % 200) / 100 - 1) * 0.35
            out.append(f'scene.fromTo("{near}", {{x: {x0:.1f}, y: {y0:.1f}, rotation: {r0:.2f}}}, {{x: {x1:.1f}, '
                       f'y: {y1:.1f}, rotation: {r1:.2f}, duration: {step:.2f}, ease: "sine.inOut", immediateRender: '
                       f'{"true" if k == 0 else "false"}}}, {t:.2f});')
            out.append(f'scene.fromTo("{far}", {{x: {-x0 * 0.5:.1f}, y: {-y0 * 0.5:.1f}}}, {{x: {-x1 * 0.5:.1f}, '
                       f'y: {-y1 * 0.5:.1f}, duration: {step:.2f}, ease: "sine.inOut", immediateRender: '
                       f'{"true" if k == 0 else "false"}}}, {t:.2f});')
            x0, y0, r0 = x1, y1, r1
            t += step
            k += 1
        return "\n".join(out)
    return ""
