"""Closed-form spring physics for motion graphics (smooth-motion-studio method, step 3).

    x(t) = 1 - e^(-zeta*omega*t) * (cos(wd*t) + (zeta*omega/wd) * sin(wd*t)),   wd = omega*sqrt(1 - zeta^2)
    settles (2 %) at ts = 4 / (zeta*omega)

The same maths is registered in the page as GSAP eases (assets/js/springs.js, loaded after GSAP), so any tween can
use ease: "spring.snappy" etc. An ease maps progress 0..1 onto the spring's own settle time, so the shape (overshoot,
one wobble, settle) is kept whatever the tween's duration; spring_duration() gives the natural duration.
"""
import math

SPRINGS = {                 # name: (zeta, omega)
    "snappy": (0.42, 17.0),     # UI pops, cards, chips: settles 0.56 s, 23 % overshoot
    "soft": (0.70, 11.0),       # big panels, camera settles: 0.52 s, 5 % overshoot
    "bouncy": (0.28, 14.0),     # icons, stamps: 1.0 s, 40 % overshoot, a visible wobble
    "firm": (1.00, 18.0),       # numbers / text that must not wobble: 0.22 s, no overshoot
}


def spring_at(t, zeta=0.42, omega=17.0):
    if t <= 0:
        return 0.0
    if zeta >= 1:
        return 1 - math.exp(-omega * t) * (1 + omega * t)
    wd = omega * math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + (zeta * omega / wd) * math.sin(wd * t))


def spring_duration(name_or_zeta="snappy", omega=None):
    zeta, w = SPRINGS[name_or_zeta] if isinstance(name_or_zeta, str) else (name_or_zeta, omega)
    return 4 / (min(zeta, 1) * w)


def overshoot(name="snappy"):
    zeta, _w = SPRINGS[name]
    return 0.0 if zeta >= 1 else math.exp(-zeta * math.pi / math.sqrt(1 - zeta * zeta))


JS = """/* closed-form springs (pipeline/motion_gfx/spring.py): gsap eases spring.snappy / soft / bouncy / firm */
(function () {
  function at(t, z, w) {
    if (t <= 0) return 0;
    if (z >= 1) return 1 - Math.exp(-w * t) * (1 + w * t);
    var wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  }
  var S = %SPRINGS%;
  Object.keys(S).forEach(function (k) {
    var z = S[k][0], w = S[k][1], ts = 4 / (Math.min(z, 1) * w);
    gsap.registerEase("spring." + k, function (p) { return p >= 1 ? 1 : at(p * ts, z, w); });
  });
})();
"""


def js() -> str:
    import json
    return JS.replace("%SPRINGS%", json.dumps({k: list(v) for k, v in SPRINGS.items()}))
