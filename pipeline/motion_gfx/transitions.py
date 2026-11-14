"""The newer, "popular" transitions of motion graphics (camera + transitions plan, 2026-11-12).

The older ones (cut, fade, push, slide, push_up, blinds, split, whip, zoom, zoom_out, flash, glitch, wipe, bars, draw,
flashlight, page, pixel, shake) only animate the incoming scene (compose._transition_js). These animate BOTH sides:
the incoming scene's stage enters (enter_js), the outgoing scene's stage leaves during the last `ov` seconds of its
host (exit_js), and some draw an effect layer above the incoming stage (overlay_html).

  whip_blur     whip pan with a directional motion blur on both scenes
  zoom_blur     the old scene zooms into a blur, the new one lands out of one
  zoom_through  the camera flies into the old scene's centre and out of the new one
  spin          spin blur: both scenes turn ~30 degrees through a blur
  light_leak    a warm film light leak sweeps across while the new scene fades up
  film_burn     the frame burns out to orange-white from one corner, the new scene appears under it
  rgb_split     chromatic RGB split + slice jitter (glitch with colour fringes)
  cube          3D cube turn (both faces around the cube's centre, with perspective)
  flip          3D card flip: the old scene turns edge-on, the new one turns in from the other side
  page_curl     the old page peels away to the left with a shading fold (the new scene lies UNDER it)
  ink           an ink blot grows from the centre and reveals the new scene (mask)
  luma_wipe     a soft feathered diagonal wipe (mask)
  shape         a diamond grows from the centre (shape mask reveal)

UNDER = transitions whose incoming scene is drawn below the outgoing one (compose.index_file z-order).
"""

NEW = ["whip_blur", "zoom_blur", "zoom_through", "spin", "light_leak", "film_burn", "rgb_split", "cube", "flip",
       "page_curl", "ink", "luma_wipe", "shape"]
OLD = ["cut", "fade", "push", "slide", "push_up", "blinds", "split", "whip", "zoom", "zoom_out", "flash", "glitch",
       "wipe", "bars", "draw", "flashlight", "page", "pixel", "shake"]
ALL = OLD + NEW
UNDER = {"page_curl"}
OVERLAP = {"cube": 0.5, "flip": 0.5, "page_curl": 0.55, "film_burn": 0.6, "light_leak": 0.55, "ink": 0.5,
           "luma_wipe": 0.45, "zoom_through": 0.4, "whip_blur": 0.3, "spin": 0.4, "zoom_blur": 0.36,
           "rgb_split": 0.36, "shape": 0.42}
SFX = {"whip_blur": "whoosh", "zoom_blur": "whoosh", "zoom_through": "swoosh-up", "spin": "whoosh",
       "light_leak": "swipe", "film_burn": "impact", "rgb_split": "glitch", "cube": "swipe", "flip": "swipe",
       "page_curl": "paper", "ink": "swoosh-up", "luma_wipe": "swipe", "shape": "pop"}

INK_SVG = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><g fill='black'>"
           "<circle cx='50' cy='50' r='30'/><circle cx='28' cy='38' r='16'/><circle cx='72' cy='34' r='14'/>"
           "<circle cx='70' cy='68' r='18'/><circle cx='32' cy='70' r='13'/><circle cx='50' cy='18' r='9'/>"
           "<circle cx='86' cy='52' r='8'/><circle cx='14' cy='56' r='9'/><circle cx='58' cy='86' r='7'/></g></svg>")


def overlap(kind: str, default: float) -> float:
    return OVERLAP.get(kind, default)


def defs_html(hid: str) -> str:
    """SVG filters a scene needs for its own enter / exit (ids carry the host so scenes never share one)."""
    return (f'<svg width="0" height="0" style="position:absolute"><defs>'
            f'<filter id="{hid}-mb" x="-20%" y="0%" width="140%" height="100%"><feGaussianBlur id="{hid}-mbg" '
            f'stdDeviation="0 0"/></filter>'
            f'<filter id="{hid}-rgb" x="-5%" y="0%" width="110%" height="100%">'
            f'<feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="r"/>'
            f'<feOffset id="{hid}-rgbr" in="r" dx="0" dy="0" result="ro"/>'
            f'<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0" result="g"/>'
            f'<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0" result="b"/>'
            f'<feOffset id="{hid}-rgbb" in="b" dx="0" dy="0" result="bo"/>'
            f'<feBlend in="ro" in2="g" mode="screen" result="rg"/><feBlend in="rg" in2="bo" mode="screen"/>'
            f'</filter></defs></svg>')


def overlay_html(kind: str, hid: str, W: int, H: int) -> str:
    """Effect layer above the incoming stage (inside the incoming scene's root)."""
    if kind == "light_leak":
        return (f'<div id="{hid}-fx" style="position:absolute;inset:-20%;pointer-events:none;opacity:0;'
                f'background:radial-gradient(ellipse 35% 60% at 30% 40%, rgba(255,250,230,.95), rgba(255,170,60,.75) 35%,'
                f' rgba(255,80,40,.35) 60%, rgba(255,60,40,0) 80%),radial-gradient(ellipse 30% 45% at 75% 65%, '
                f'rgba(255,120,170,.6), rgba(255,120,170,0) 70%)"></div>')
    if kind == "film_burn":
        return (f'<div id="{hid}-fx" style="position:absolute;inset:0;pointer-events:none;opacity:0;'
                f'background:radial-gradient(circle at 85% 15%, #FFFDF2 0%, #FFE08A 18%, #FF9A2E 38%, #E0441B 58%,'
                f' rgba(120,20,0,0) 78%);transform-origin:85% 15%"></div>')
    if kind == "page_curl":
        return ""
    return ""


def enter_js(kind: str, hid: str, ov: float, W: int, H: int) -> str:
    st = f"#{hid}-stage"
    d = f"{ov:.2f}"
    P = int(W * 1.6)
    if kind == "whip_blur":
        return (f'scene.set("{st}", {{filter: "url(#{hid}-mb)"}}, 0);\n'
                f'scene.fromTo("#{hid}-mbg", {{attr: {{stdDeviation: "{int(W * 0.03)} 0"}}}}, {{attr: {{stdDeviation: "0 0"}}, '
                f'duration: {d}, ease: "power3.out"}}, 0);\n'
                f'scene.fromTo("{st}", {{x: {int(W * 0.55)}}}, {{x: 0, duration: {d}, ease: "power3.out"}}, 0);\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov + 0.01:.2f});')
    if kind == "zoom_blur":
        return (f'scene.fromTo("{st}", {{scale: 1.4, filter: "blur(18px) brightness(1.5)", opacity: 0.2}}, '
                f'{{scale: 1, filter: "blur(0px) brightness(1)", opacity: 1, duration: {d}, ease: "power3.out"}}, 0);\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov + 0.01:.2f});')
    if kind == "zoom_through":
        return (f'scene.fromTo("{st}", {{scale: 0.35, opacity: 0, filter: "blur(10px)", transformOrigin: "50% 50%"}}, '
                f'{{scale: 1, opacity: 1, filter: "blur(0px)", duration: {d}, ease: "expo.out"}}, {ov * 0.25:.2f});\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov * 1.25 + 0.01:.2f});')
    if kind == "spin":
        return (f'scene.fromTo("{st}", {{rotation: 28, scale: 1.35, opacity: 0, filter: "blur(14px)"}}, '
                f'{{rotation: 0, scale: 1, opacity: 1, filter: "blur(0px)", duration: {d}, ease: "power3.out"}}, 0);\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov + 0.01:.2f});')
    if kind == "light_leak":
        fx = f"#{hid}-fx"
        return (f'scene.fromTo("{st}", {{opacity: 0}}, {{opacity: 1, duration: {ov * 0.6:.2f}, ease: "power1.inOut"}}, '
                f'{ov * 0.3:.2f});\n'
                f'scene.fromTo("{fx}", {{x: {-int(W * 0.5)}, opacity: 0}}, {{x: {int(W * 0.25)}, opacity: 1, '
                f'duration: {ov * 0.55:.2f}, ease: "power1.in"}}, 0);\n'
                f'scene.to("{fx}", {{x: {int(W * 0.7)}, opacity: 0, duration: {ov * 0.75:.2f}, ease: "power1.out"}}, '
                f'{ov * 0.55:.2f});')
    if kind == "film_burn":
        fx = f"#{hid}-fx"
        return (f'scene.fromTo("{st}", {{opacity: 0}}, {{opacity: 1, duration: 0.01}}, {ov * 0.5:.2f});\n'
                f'scene.fromTo("{fx}", {{scale: 0.2, opacity: 0}}, {{scale: 2.6, opacity: 1, duration: {ov * 0.5:.2f}, '
                f'ease: "power2.in"}}, 0);\n'
                f'scene.to("{fx}", {{opacity: 0, duration: {ov * 0.6:.2f}, ease: "power2.out"}}, {ov * 0.5:.2f});\n'
                f'scene.fromTo("{st}", {{filter: "sepia(0.8) brightness(1.8)"}}, {{filter: "sepia(0) brightness(1)", '
                f'duration: {ov * 0.6:.2f}, ease: "power2.out"}}, {ov * 0.5:.2f});\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov * 1.1 + 0.01:.2f});')
    if kind == "rgb_split":
        off = int(W * 0.022)
        return (f'scene.set("{st}", {{filter: "url(#{hid}-rgb)"}}, 0);\n'
                f'scene.fromTo("#{hid}-rgbr", {{attr: {{dx: {off}}}}}, {{attr: {{dx: 0}}, duration: {d}, ease: "steps(5)"}}, 0);\n'
                f'scene.fromTo("#{hid}-rgbb", {{attr: {{dx: {-off}}}}}, {{attr: {{dx: 0}}, duration: {d}, ease: "steps(5)"}}, 0);\n'
                f'scene.fromTo("{st}", {{clipPath: "inset(30% 0% 45% 0%)", x: {int(W * 0.03)}}}, {{clipPath: "inset(0% 0% 0% 0%)", '
                f'x: 0, duration: {d}, ease: "steps(4)"}}, 0);\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov + 0.01:.2f});')
    if kind == "cube":
        return (f'scene.fromTo("{st}", {{rotationY: 90, transformPerspective: {P}, transformOrigin: "50% 50% {-W // 2}px", '
                f'backfaceVisibility: "hidden"}}, {{rotationY: 0, duration: {d}, ease: "power2.inOut"}}, 0);')
    if kind == "flip":
        return (f'scene.fromTo("{st}", {{rotationY: -90, transformPerspective: {P}, transformOrigin: "50% 50%"}}, '
                f'{{rotationY: 0, duration: {ov / 2:.2f}, ease: "power2.out"}}, {ov / 2:.2f});')
    if kind == "page_curl":      # the new scene lies under the old page: it only lifts out of a shadow
        return (f'scene.fromTo("{st}", {{filter: "brightness(0.55)", scale: 0.98}}, {{filter: "brightness(1)", scale: 1, '
                f'duration: {d}, ease: "power2.out"}}, 0);\n'
                f'scene.set("{st}", {{filter: "none"}}, {ov + 0.01:.2f});')
    if kind == "ink":
        return (f'scene.fromTo("{st}", {{maskImage: "url(\\"{INK_SVG}\\")", webkitMaskImage: "url(\\"{INK_SVG}\\")", '
                f'maskRepeat: "no-repeat", webkitMaskRepeat: "no-repeat", maskPosition: "50% 50%", '
                f'webkitMaskPosition: "50% 50%", maskSize: "0% 0%", webkitMaskSize: "0% 0%"}}, '
                f'{{maskSize: "420% 420%", webkitMaskSize: "420% 420%", duration: {d}, ease: "power2.in"}}, 0);\n'
                f'scene.set("{st}", {{maskImage: "none", webkitMaskImage: "none"}}, {ov + 0.01:.2f});')
    if kind == "luma_wipe":
        g = "linear-gradient(110deg, #000 0%, #000 40%, rgba(0,0,0,0) 60%, rgba(0,0,0,0) 100%)"
        return (f'scene.fromTo("{st}", {{maskImage: "{g}", webkitMaskImage: "{g}", maskSize: "300% 100%", '
                f'webkitMaskSize: "300% 100%", maskRepeat: "no-repeat", webkitMaskRepeat: "no-repeat", '
                f'maskPosition: "100% 0%", webkitMaskPosition: "100% 0%"}}, {{maskPosition: "0% 0%", '
                f'webkitMaskPosition: "0% 0%", duration: {d}, ease: "power1.inOut"}}, 0);\n'
                f'scene.set("{st}", {{maskImage: "none", webkitMaskImage: "none"}}, {ov + 0.01:.2f});')
    if kind == "shape":
        return (f'scene.fromTo("{st}", {{clipPath: "polygon(50% 50%, 50% 50%, 50% 50%, 50% 50%)"}}, '
                f'{{clipPath: "polygon(50% -75%, 175% 50%, 50% 175%, -75% 50%)", duration: {d}, ease: "power3.in"}}, 0);\n'
                f'scene.set("{st}", {{clipPath: "none"}}, {ov + 0.01:.2f});')
    return ""


def exit_js(kind: str, hid: str, at: float, ov: float, W: int, H: int) -> str:
    """The outgoing scene's half of a transition: starts `at` (local time) and lasts `ov`."""
    st = f"#{hid}-stage"
    d, t = f"{ov:.2f}", f"{at:.3f}"
    P = int(W * 1.6)
    ir = "immediateRender: false"
    if kind == "whip_blur":
        return (f'scene.set("{st}", {{filter: "url(#{hid}-mb)"}}, {t});\n'
                f'scene.fromTo("#{hid}-mbg", {{attr: {{stdDeviation: "0 0"}}}}, {{attr: {{stdDeviation: "{int(W * 0.03)} 0"}}, '
                f'duration: {d}, ease: "power3.in", {ir}}}, {t});\n'
                f'scene.fromTo("{st}", {{x: 0}}, {{x: {-int(W * 0.55)}, duration: {d}, ease: "power3.in", {ir}}}, {t});')
    if kind == "zoom_blur":
        return (f'scene.fromTo("{st}", {{scale: 1, filter: "blur(0px)"}}, {{scale: 1.4, filter: "blur(18px)", duration: {d}, '
                f'ease: "power3.in", {ir}}}, {t});')
    if kind == "zoom_through":
        return (f'scene.fromTo("{st}", {{scale: 1, opacity: 1}}, {{scale: 3.2, opacity: 0, duration: {d}, ease: "power3.in", '
                f'transformOrigin: "50% 50%", {ir}}}, {t});')
    if kind == "spin":
        return (f'scene.fromTo("{st}", {{rotation: 0, scale: 1, filter: "blur(0px)"}}, {{rotation: -28, scale: 1.35, '
                f'filter: "blur(14px)", duration: {d}, ease: "power3.in", {ir}}}, {t});')
    if kind == "cube":
        return (f'scene.fromTo("{st}", {{rotationY: 0, transformPerspective: {P}, transformOrigin: "50% 50% {-W // 2}px", '
                f'backfaceVisibility: "hidden"}}, {{rotationY: -90, duration: {d}, ease: "power2.inOut", {ir}}}, {t});')
    if kind == "flip":
        return (f'scene.fromTo("{st}", {{rotationY: 0, transformPerspective: {P}, transformOrigin: "50% 50%"}}, '
                f'{{rotationY: 90, duration: {ov / 2:.2f}, ease: "power2.in", {ir}}}, {t});')
    if kind == "page_curl":
        return (f'scene.fromTo("{st}", {{rotationY: 0, transformPerspective: {P}, transformOrigin: "0% 50%", '
                f'boxShadow: "0px 0px 0px rgba(0,0,0,0)"}}, {{rotationY: -118, boxShadow: "{-int(W * 0.03)}px 0px '
                f'{int(W * 0.04)}px rgba(0,0,0,0.45)", duration: {d}, ease: "power2.inOut", {ir}}}, {t});\n'
                f'scene.fromTo("#{hid}-shade", {{opacity: 0}}, {{opacity: 0.6, duration: {d}, ease: "power1.in", {ir}}}, {t});')
    if kind == "rgb_split":
        return (f'scene.fromTo("{st}", {{x: 0}}, {{x: {-int(W * 0.03)}, duration: {d}, ease: "steps(3)", {ir}}}, {t});')
    # the older transitions get the outgoing half too (a real push moves both scenes)
    if kind == "push":
        return f'scene.fromTo("{st}", {{x: 0}}, {{x: {-W}, duration: {d}, ease: "power3.out", {ir}}}, {t});'
    if kind == "slide":
        return f'scene.fromTo("{st}", {{x: 0}}, {{x: {W}, duration: {d}, ease: "power3.out", {ir}}}, {t});'
    if kind == "push_up":
        return f'scene.fromTo("{st}", {{y: 0}}, {{y: {-H}, duration: {d}, ease: "power3.out", {ir}}}, {t});'
    if kind == "whip":
        return (f'scene.fromTo("{st}", {{x: 0, filter: "blur(0px)"}}, {{x: {int(W * 0.35)}, filter: "blur(24px)", '
                f'duration: {d}, ease: "power3.out", {ir}}}, {t});')
    return ""
