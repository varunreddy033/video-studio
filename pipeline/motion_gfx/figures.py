"""The stick-figure rig: anonymous cut-out characters in the reference style (round head, dot eyes, pill body,
thick stick limbs), drawn as SVG and moved joint by joint with GSAP (svgOrigin = the joint).

figure(P, n, ...) returns the SVG <g> of one figure in its own 300 x 520 space; pose_js() returns the tweens of a
pose on the scene timeline `tl`. Poses: idle, talk, point, shrug, shocked, walk, think, sneak, cheer, worried.
Outfits: plain, tie (an executive), spy (hat + shades), glasses. props() draws the objects the narration names."""

import random

# joints in the figure's own coordinates
SHOULDER_L, SHOULDER_R = (112, 178), (188, 178)
HIP = (150, 318)
NECK = (150, 150)


def figure(P, n, ink, body, outfit="plain", flip=False):
    """One figure as an SVG group (id P+'f'+n). Children ids: -all (whole), -torso (bobs), -head, -eyes, -mouth,
    -mouthO, -armL/-foreL, -armR/-foreR, -legL, -legR, -acc (accessories), -sweat."""
    f = f"{P}f{n}"
    sw = 11
    acc = ""
    if outfit == "tie":
        acc = (f'<path d="M150 158 L141 176 L150 236 L159 176 Z" fill="{ink}"/>'
               f'<path d="M136 156 L150 166 L164 156" fill="none" stroke="{ink}" stroke-width="6" stroke-linejoin="round"/>')
    elif outfit == "spy":
        acc = (f'<rect x="104" y="72" width="92" height="22" rx="10" fill="{ink}"/>'
               f'<path d="M84 52 Q150 30 216 52 L206 62 Q150 46 94 62 Z" fill="{ink}"/>'
               f'<path d="M110 20 Q150 -4 190 20 L196 54 L104 54 Z" fill="{ink}"/>'
               f'<rect x="108" y="40" width="84" height="9" fill="#FF3347"/>')
    elif outfit == "glasses":
        acc = (f'<circle cx="131" cy="86" r="15" fill="none" stroke="{ink}" stroke-width="6"/>'
               f'<circle cx="169" cy="86" r="15" fill="none" stroke="{ink}" stroke-width="6"/>'
               f'<line x1="146" y1="86" x2="154" y2="86" stroke="{ink}" stroke-width="6"/>')
    eyes = "" if outfit == "spy" else (f'<g id="{f}-eyes"><circle cx="132" cy="86" r="7" fill="{ink}"/>'
                                       f'<circle cx="168" cy="86" r="7" fill="{ink}"/></g>')
    tr = ' transform="translate(300 0) scale(-1 1)"' if flip else ""
    line = f'stroke="{ink}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    return f"""<g id="{f}-all"{tr}>
  <ellipse cx="150" cy="506" rx="78" ry="12" fill="{ink}" opacity="0.18"/>
  <g id="{f}-legL"><path d="M138 318 L118 412 L104 498 L80 500" {line}/></g>
  <g id="{f}-legR"><path d="M162 318 L182 412 L196 498 L220 500" {line}/></g>
  <g id="{f}-torso">
    <g id="{f}-armL"><path d="M112 178 L80 248" {line}/><g id="{f}-foreL"><path d="M80 248 L66 318" {line}/></g></g>
    <g id="{f}-armR"><path d="M188 178 L220 248" {line}/><g id="{f}-foreR"><path d="M220 248 L234 318" {line}/></g></g>
    <rect x="104" y="148" width="92" height="186" rx="46" fill="{body}" stroke="{ink}" stroke-width="{sw}"/>
    <g id="{f}-head">
      <circle cx="150" cy="88" r="56" fill="#FFFFFF" stroke="{ink}" stroke-width="{sw}"/>
      {eyes}
      <path id="{f}-mouth" d="M132 114 Q150 128 168 114" {line} stroke-width="8"/>
      <ellipse id="{f}-mouthO" cx="150" cy="120" rx="10" ry="13" fill="{ink}" opacity="0"/>
      <path id="{f}-sweat" d="M206 58 Q214 72 206 80 Q198 72 206 58 Z" fill="#5BC8FF" stroke="{ink}" stroke-width="4" opacity="0"/>
      <g id="{f}-acc">{acc}</g>
    </g>
  </g>
</g>"""


def _rot(sel, origin, a, b, t, d, ease="power3.out"):
    return (f'tl.fromTo("{sel}", {{rotation: {a}, svgOrigin: "{origin[0]} {origin[1]}"}}, '
            f'{{rotation: {b}, svgOrigin: "{origin[0]} {origin[1]}", duration: {d:.2f}, ease: "{ease}"}}, {t:.2f});')


def _set_rot(sel, origin, a, t):
    return f'tl.set("{sel}", {{rotation: {a}, svgOrigin: "{origin[0]} {origin[1]}"}}, {t:.2f});'


def pose_js(P, n, pose, dur, word_times, seed=0):
    """GSAP tweens (on `tl`, times in the scene) for one figure: the pose's main move on entry, then life
    (breathing bob, blinks, mouth on the spoken words). Returns (js, sfx cues [(t, kind)])."""
    f = f"#{P}f{n}"
    rnd = random.Random(seed)
    js, cues = [], []
    end = max(0.6, dur - 0.1)
    breath = 0.9 + rnd.random() * 0.3
    reps = max(0, int(end / breath) - 1)
    js.append(f'tl.fromTo("{f}-torso", {{y: 0}}, {{y: 6, duration: {breath:.2f}, ease: "sine.inOut", yoyo: true, '
              f'repeat: {reps}}}, 0.1);')
    t = 0.7 + rnd.random() * 0.6
    while t < end - 0.2:                                     # blinks every 1.6-2.6 s
        js.append(f'tl.fromTo("{f}-eyes", {{scaleY: 1, transformOrigin: "50% 50%"}}, {{scaleY: 0.12, duration: 0.07, '
                  f'yoyo: true, repeat: 1, ease: "none"}}, {t:.2f});')
        t += 1.6 + rnd.random()
    talk = pose in ("idle", "talk", "point", "shrug", "think", "cheer")
    if talk:                                                 # the mouth opens on the spoken words
        for w0, w1 in word_times[:14]:
            if w0 > end:
                break
            js.append(f'tl.fromTo("{f}-mouth", {{scaleY: 1, transformOrigin: "50% 0%"}}, {{scaleY: 2.2, duration: '
                      f'{max(0.06, (w1 - w0) / 2):.2f}, yoyo: true, repeat: 1, ease: "sine.inOut"}}, {max(0, w0):.2f});')
    if pose == "point":
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -118, 0.25, 0.45, "spring.snappy"))
        js.append(_rot(f"{f}-foreR", (220, 248), 0, -28, 0.35, 0.4))
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 12, 0.25, 0.5))
    elif pose == "shrug":
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 58, 0.25, 0.4, "spring.snappy"))
        js.append(_rot(f"{f}-foreL", (80, 248), 0, -95, 0.3, 0.4, "spring.snappy"))
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -58, 0.25, 0.4, "spring.snappy"))
        js.append(_rot(f"{f}-foreR", (220, 248), 0, 95, 0.3, 0.4, "spring.snappy"))
        js.append(_rot(f"{f}-head", NECK, 0, -9, 0.3, 0.4))
    elif pose == "shocked":
        js.append(f'tl.fromTo("{f}-all", {{y: 0}}, {{y: -46, duration: 0.18, ease: "power2.out", yoyo: true, '
                  f'repeat: 1}}, 0.18);')
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 150, 0.18, 0.3, "spring.bouncy"))
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -150, 0.18, 0.3, "spring.bouncy"))
        js.append(f'tl.set("{f}-mouth", {{opacity: 0}}, 0.2); tl.set("{f}-mouthO", {{opacity: 1}}, 0.2);')
        js.append(f'tl.fromTo("{f}-eyes", {{scale: 1, transformOrigin: "50% 50%"}}, {{scale: 1.5, duration: 0.2, '
                  f'ease: "spring.bouncy"}}, 0.2);')
        cues.append((0.18, "pop"))
    elif pose == "walk":
        steps = max(1, int(end / 0.36))
        js.append(_rot(f"{f}-legL", HIP, -18, 18, 0.0, 0.36, "sine.inOut").replace('ease: "sine.inOut"}',
                  f'ease: "sine.inOut", yoyo: true, repeat: {steps - 1}}}'))
        js.append(_rot(f"{f}-legR", HIP, 18, -18, 0.0, 0.36, "sine.inOut").replace('ease: "sine.inOut"}',
                  f'ease: "sine.inOut", yoyo: true, repeat: {steps - 1}}}'))
        js.append(_rot(f"{f}-armL", SHOULDER_L, 16, -16, 0.0, 0.36, "sine.inOut").replace('ease: "sine.inOut"}',
                  f'ease: "sine.inOut", yoyo: true, repeat: {steps - 1}}}'))
        js.append(_rot(f"{f}-armR", SHOULDER_R, -16, 16, 0.0, 0.36, "sine.inOut").replace('ease: "sine.inOut"}',
                  f'ease: "sine.inOut", yoyo: true, repeat: {steps - 1}}}'))
    elif pose == "sneak":
        steps = max(1, int(end / 0.5))
        cues.append((0.05, "heartbeat"))
        js.append(f'tl.fromTo("{f}-torso", {{scaleY: 1, transformOrigin: "50% 100%"}}, {{scaleY: 0.9, duration: 0.3, '
                  f'ease: "power2.out"}}, 0.05);')
        for side, sgn in (("legL", 1), ("legR", -1)):
            js.append(_rot(f"{f}-{side}", HIP, -12 * sgn, 12 * sgn, 0.0, 0.5, "sine.inOut").replace(
                'ease: "sine.inOut"}', f'ease: "sine.inOut", yoyo: true, repeat: {steps - 1}}}'))
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 70, 0.1, 0.4))
        js.append(_rot(f"{f}-foreL", (80, 248), 0, -100, 0.15, 0.4))
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -40, 0.1, 0.4))
    elif pose == "think":
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -32, 0.25, 0.45))
        js.append(_rot(f"{f}-foreR", (220, 248), 0, -148, 0.3, 0.45, "spring.snappy"))
        js.append(_rot(f"{f}-head", NECK, 0, 7, 0.3, 0.5))
    elif pose == "cheer":
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 160, 0.2, 0.35, "spring.bouncy"))
        js.append(_rot(f"{f}-armR", SHOULDER_R, 0, -160, 0.28, 0.35, "spring.bouncy"))
        js.append(f'tl.fromTo("{f}-all", {{y: 0}}, {{y: -26, duration: 0.2, ease: "power2.out", yoyo: true, '
                  f'repeat: {max(1, int(end / 0.4)) * 2 - 1}}}, 0.25);')
    elif pose == "worried":
        cues.append((0.45, "error"))
        js.append(_rot(f"{f}-head", NECK, 0, 10, 0.2, 0.5))
        js.append(_rot(f"{f}-armL", SHOULDER_L, 0, 26, 0.2, 0.5))
        js.append(_rot(f"{f}-foreL", (80, 248), 0, -120, 0.25, 0.5))
        js.append(f'tl.set("{f}-mouth", {{attr: {{d: "M132 122 Q150 108 168 122"}}}}, 0.2);')
        js.append(f'tl.fromTo("{f}-sweat", {{opacity: 0, y: -10}}, {{opacity: 1, y: 6, duration: 0.5, '
                  f'ease: "power2.in"}}, 0.5);')
    return "\n".join(js), cues


# ------------------------------------------------------------------------------------------------- props
def prop(P, name, ink, fill, accent):
    """One prop as an SVG group in a 240 x 240 box (id P+'p-'+name)."""
    i = f"{P}p-{name}"
    s = f'stroke="{ink}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"'
    body = {
        "chip": f'<rect x="50" y="50" width="140" height="140" rx="18" fill="{fill}" {s}/>'
                f'<rect x="85" y="85" width="70" height="70" rx="8" fill="{accent}" {s}/>'
                + "".join(f'<line x1="{x}" y1="22" x2="{x}" y2="50" {s}/><line x1="{x}" y1="190" x2="{x}" y2="218" {s}/>'
                          f'<line x1="22" y1="{x}" x2="50" y2="{x}" {s}/><line x1="190" y1="{x}" x2="218" y2="{x}" {s}/>'
                          for x in (80, 120, 160))
                + f'<text x="120" y="131" text-anchor="middle" font-family="Anton" font-size="34" fill="{ink}">GPU</text>',
        "heart": f'<path d="M120 206 C40 150 22 104 44 72 C66 40 108 46 120 80 C132 46 174 40 196 72 C218 104 200 150 120 206 Z" fill="#FF3347" {s}/>',
        "money": "".join(f'<rect x="{30 + o}" y="{70 + o}" width="170" height="96" rx="10" fill="#7BE495" {s}/>'
                         for o in (16, 8, 0))
                 + f'<circle cx="115" cy="118" r="28" fill="#FFFFFF" {s}/><text x="115" y="132" text-anchor="middle" '
                   f'font-family="Anton" font-size="38" fill="{ink}">$</text>',
        "coin": f'<circle cx="120" cy="120" r="88" fill="#FFD21F" {s}/><circle cx="120" cy="120" r="62" fill="none" {s}/>'
                f'<text x="120" y="146" text-anchor="middle" font-family="Anton" font-size="78" fill="{ink}">$</text>',
        "document": f'<path d="M50 20 H160 L198 58 V222 H50 Z" fill="#FFFFFF" {s}/><path d="M160 20 V58 H198" fill="none" {s}/>'
                    + "".join(f'<line x1="74" y1="{y}" x2="{174 if k % 3 else 140}" y2="{y}" {s} stroke-width="7"/>'
                              for k, y in enumerate((88, 112, 136, 160, 184))),
        "magnifier": f'<circle cx="100" cy="100" r="62" fill="#BFE8FF" {s}/><line x1="146" y1="146" x2="212" y2="212" {s} stroke-width="22"/>',
        "phone": f'<rect x="70" y="18" width="100" height="204" rx="20" fill="{ink}"/><rect x="82" y="40" width="76" height="150" rx="8" fill="{accent}"/>'
                 f'<circle cx="120" cy="206" r="7" fill="#FFFFFF"/>',
        "question": f'<text x="120" y="200" text-anchor="middle" font-family="Anton" font-size="220" fill="{accent}" '
                    f'stroke="{ink}" stroke-width="8" paint-order="stroke">?</text>',
        "exclaim": f'<text x="120" y="204" text-anchor="middle" font-family="Anton" font-size="230" fill="{accent}" '
                   f'stroke="{ink}" stroke-width="8" paint-order="stroke">!</text>',
        "globe": f'<circle cx="120" cy="120" r="96" fill="#5BC8FF" {s}/><path d="M60 80 Q90 60 110 86 Q100 120 70 116 Z M140 60 Q190 76 186 120 '
                 f'Q160 140 146 112 Z M120 160 Q160 160 150 200 Q120 206 112 180 Z" fill="#7BE495" {s} stroke-width="6"/>'
                 f'<ellipse cx="120" cy="120" rx="96" ry="34" fill="none" {s} stroke-width="5" opacity="0.5"/>',
        "building": f'<rect x="56" y="30" width="128" height="196" fill="{fill}" {s}/>'
                    + "".join(f'<rect x="{x}" y="{y}" width="26" height="26" fill="#BFE8FF" {s} stroke-width="5"/>'
                              for x in (78, 136) for y in (52, 96, 140))
                    + f'<rect x="100" y="180" width="40" height="46" fill="{ink}"/>',
        "lock": f'<path d="M78 110 V80 Q78 36 120 36 Q162 36 162 80 V110" fill="none" {s} stroke-width="16"/>'
                f'<rect x="54" y="106" width="132" height="110" rx="16" fill="#FFD21F" {s}/><circle cx="120" cy="154" r="14" fill="{ink}"/>',
        "camera": f'<rect x="26" y="70" width="188" height="130" rx="20" fill="{ink}"/><rect x="86" y="44" width="68" height="34" rx="6" fill="{ink}"/>'
                  f'<circle cx="120" cy="136" r="44" fill="{accent}" stroke="#FFFFFF" stroke-width="9"/>',
        "chart_up": f'<rect x="30" y="30" width="180" height="180" rx="16" fill="#FFFFFF" {s}/>'
                    f'<path d="M56 170 L100 126 L132 148 L186 72" fill="none" stroke="#1FC16B" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
                    f'<path d="M160 70 L188 70 L188 98" fill="none" stroke="#1FC16B" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>',
        "chart_down": f'<rect x="30" y="30" width="180" height="180" rx="16" fill="#FFFFFF" {s}/>'
                      f'<path d="M56 72 L100 116 L132 94 L186 170" fill="none" stroke="#FF3347" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
                      f'<path d="M160 172 L188 172 L188 144" fill="none" stroke="#FF3347" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>',
        "ship": f'<path d="M30 140 H210 L184 196 H56 Z" fill="{fill}" {s}/>'
                + "".join(f'<rect x="{x}" y="96" width="40" height="44" fill="{c}" {s} stroke-width="6"/>'
                          for x, c in ((56, "#FF3347"), (100, "#FFD21F"), (144, "#2F6BFF"))),
        "flag": f'<line x1="56" y1="20" x2="56" y2="226" {s}/><path d="M56 28 H196 L172 72 L196 116 H56 Z" fill="#FF3347" {s}/>',
        "eye": f'<path d="M20 120 Q120 30 220 120 Q120 210 20 120 Z" fill="#FFFFFF" {s}/><circle cx="120" cy="120" r="38" fill="{ink}"/>'
               f'<circle cx="134" cy="106" r="11" fill="#FFFFFF"/>',
    }.get(name)
    return f'<g id="{i}">{body}</g>' if body else ""


PROP_NAMES = ("chip", "heart", "money", "coin", "document", "magnifier", "phone", "question", "exclaim", "globe",
              "building", "lock", "camera", "chart_up", "chart_down", "ship", "flag", "eye")
