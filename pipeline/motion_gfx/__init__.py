"""
motion  -  the motion-graphics renderer (script header `rendering_method: motion`, roadmap F10).

Bright-pop kinetic typography, anonymous stick figures and transitions, written as hand-made HTML/SVG/GSAP
templates and rendered by HyperFrames in local Chrome. No AI model draws anything: the script's shot tags and
narration pick the templates, and the voice's word timings place every word, pop and sound. Same script = same
video, and it runs fully on the Mac.

How the installed skills shape it (.claude/skills):
  hyperframes / hyperframes-cli   the render contract (paused timelines, fromTo, clip timing, check + snapshot
                                  before render), the 9:16 safe band, captions as one timed host
  kinetic-typography              word-granularity reveals, mask/clip reveals, ease-out-expo, 40-70 ms word staggers
  motion-design / animation-principles   one personality ("Energetic"): back.out overshoot 10-30 %, enter > exit,
                                  three layers per scene (primary text/figure, secondary props, ambient shapes)
  shot-composition                one focal point per scene, content inside the 90 % action-safe box, nothing
                                  under the caption chip
  beat-sync-editing / color-motion   a new picture every 1.2-3 s (one beat = one clause of the voice), palette
                                  rotation without neighbours repeating, transitions chosen by what changes
  ffmpeg-skill                    sound effects placed on the animation's own moments, layered under the voice

  design.py     palettes, fonts, easing, timing constants
  beats.py      shots -> beats (1.2-3 s each) from the voice's word timings
  figures.py    the stick-figure rig (SVG) and its poses / props
  templates.py  the scene templates (kinetic words, big number, title slam, quote, chart, memo + stamp, figures)
  compose.py    HyperFrames project: scenes, transitions, the caption chip overlay
  render.py     voice -> beats -> scenes -> hyperframes check/snapshot/render -> the pipeline's own mix + encode
"""
