"""Self-check of the storyboard edit layer (no render):  bin/python tools/check_storyboard.py  -> "storyboard: clean"."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.motion_gfx import storyboard as SB  # noqa: E402

raw = {"bg": "red; } body { display:none", "els": {
    "kin": {"mode": "abs", "x": 0.1, "y": -0.05, "base": [1, 2, 3, 4], "zoom": 99, "color": "#12AB34", "font": "Nope",
            "text": '</script><b>"x"', "align": "middle", "z": "7"},
    "p0/2": {"x": 9, "y": 0, "fs": 0.05, "hidden": True},
    "a;b{}": {"x": 1}, "w0": "nope"}}
e = SB.clean_edits(raw)
assert "bg" not in e and set(e["els"]) == {"kin", "p0/2"}, e
k = e["els"]["kin"]
assert k["zoom"] == 12 and "font" not in k and "align" not in k and k["z"] == 7 and e["els"]["p0/2"]["x"] == 3
css, js = SB.edit_blocks("s004", e, 1920, 1080)
assert "#s004-kin { margin-left: 193.00px !important" in css and "#s004-p0 > :nth-child(3)" in css
assert "<" not in js and "\\u003c/script>" in js                  # text can't close the scene's <script>
assert "<" not in css
scene = "<template>\n<style>\n#root {}\n</style>\n<div></div>\n<script>\n(function (tl) {\ntl.to();\n})(tl);\n</script>\n</template>\n"
once = SB.patch_html(scene, "s004", e, 1920, 1080)
assert SB.patch_html(once, "s004", e, 1920, 1080) == once and SB.strip_edits(once) == scene
assert SB.rehost("#s004-a s0041 s004", "s004", "s010") == "#s010-a s0041 s010"
b = [{"text": "Hello, world."}, {"text": "hello world"}, {"text": "Other"}]
ids = SB.scene_ids(b)
assert ids[0][:10] == ids[1][:10] and ids[0] != ids[1] and ids[2] != ids[0]

# shot storyboard (ai_image / blocky3d / explainer3d / neon): edits rewrite only that shot's lines; seed versions
import tempfile
from pathlib import Path
from pipeline import shot_storyboard as SS
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    (d / "script.md").write_text("---\ntitle: T\nrendering_method: ai_image\n---\n\n## One\n\n[ai: a red door]\n"
                                 "The door opens slowly.\n[card: HELLO | small]\nA card appears here.\n", encoding="utf-8")
    r = SS.shots(d)
    assert r["ok"] and [s["type"] for s in r["shots"]] == ["ai", "card"] and r["shots"][0]["line_end"] == 9, r
    s0 = r["shots"][0]
    out = SS.save(d, 0, "[ai: a blue door]\nThe door opens fast.", s0["text"])
    assert "[ai: a blue door]\nThe door opens fast.\n[card: HELLO" in out and "red" not in out
    for bad_old, bad_new in ((s0["text"] + "x", "[ai: x]\nWords."), (s0["text"], "[ai: x | nope]\nWords.")):
        try:
            SS.save(d, 0, bad_new, bad_old)
            raise AssertionError("bad save accepted")
        except ValueError:
            pass
    text, parsed = SS._parse(d)
    assert "[ai: a red door | seed=3]" in SS._with_seed(text, parsed, 0, 3)
    p3 = SS.script_parser.parse(SS._with_seed(text, parsed, 0, 3))
    assert "[ai: a red door]" in SS._with_seed(SS._with_seed(text, parsed, 0, 3), p3, 0, 0)
    assert SS._image(d, parsed, parsed["shots"][0]) != SS._image(d, parsed, parsed["shots"][0], 3)   # seed = other cache
    assert SS.shots(d)["shots"][1].get("versions") is None                                             # cards: no versions
print("storyboard: clean")
