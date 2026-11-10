# timeline.json: the contract between Python and Remotion (style: motion)

Python (`pipeline/motion.py`) writes one `timeline.json` per render; Remotion (`motion/src/motion/`) draws exactly
what it says. Python owns everything that needs the voice, the image model or files: word timings, images,
presenter clips, audio. Remotion owns only the picture. Types: `motion/src/motion/types.ts` (keep both in sync).

All times are **frames** at `fps` (30). Every cue that belongs to a spoken word keeps the word's index too
(`word`), so a timeline can be checked against the narration; `frame` is what Remotion uses.

```jsonc
{
  "version": 1,
  "fps": 30, "width": 1920, "height": 1080,        // drafts are rendered with --scale 0.5
  "durationFrames": 903,
  "palette": "navy",
  "words": [ {"w": "There", "s": 0.85, "e": 0.97, "seg": 0, "frame": 26} ],   // the whole narration, seconds + frame
  "captions": {"show": true, "style": "amber_word"},                         // word captions (until a scene has a headline)
  "scenes": [
    {
      "id": "s0",
      "from": 0, "frames": 253,                   // absolute start frame, length incl. the incoming transition overlap
      "transition": {"type": "push", "dir": "from-right", "frames": 18},      // how this scene ARRIVES (none for s0)
      //   types: push (dir from-right|from-left|from-top|from-bottom), zoom (x, y px), cut
      "background": {"tint": "#16294A"},
      "headline": {"appear": 4, "words": [{"text": "FOUR", "word": 2, "frame": 62}]},   // optional
      "elements": [
        {
          "id": "e3", "type": "number",           // image | video | card | number | quote | chart | label | headline
          "props": {"value": -5.5, "decimals": 1, "suffix": "%", "label": "the Nasdaq's fall"},
          "box": {"x": 0, "y": 0, "w": 1920, "h": 1080},                    // where it sits (px)
          "enter": {"frame": 40, "word": 9, "anim": "pop"},                 // pop | grow | slide | fade | none
          "exit":  {"frame": 200, "anim": "fade"}                           // optional; else stays to the scene end
        }
      ]
    }
  ]
}
```

Element types in version 1 (phase 2; the v3 tags and the prop library in phases 3-4 add more):

| type | props |
|---|---|
| `image` | `src` (path inside the render's public dir), `move` (kenburns move index), `fit` cover/contain |
| `video` | `src` (a pre-rendered clip, e.g. a lip-synced `[talk:]` presenter clip), plays from its enter frame |
| `card` | `text`, `sub` |
| `number` | `value`, `decimals`, `prefix`, `suffix`, `label`, `countFrames` |
| `quote` | `text`, `by` |
| `chart` | `kind` bar/line, `title`, `data` [[label, value]...], `unit` |

Render: `npx remotion render src/index.ts Motion <out.mp4> --props=<timeline.json> --public-dir=<dir>
--concurrency=<MOTION_CONCURRENCY>`; video only. Python then muxes the classic audio mix (voice + ducked music +
sfx, two-pass loudnorm to -14 LUFS).

## Presenter puppet and labels (added 2026-11-10)
- `char` elements: `props.frames` = the pose's pictures (closed, slight, wide, o, e, mbp, blink; paths under the public
  dir), `props.mouth` = [[frame, shape], ...] from Kokoro's phoneme timings (scene-relative), `props.blinks` = [frame, ...],
  `props.poses` = [[frame, pose], ...] for pose switches inside a scene. Remotion stacks the pictures and shows one.
- `label` elements: `props.pointer` = "up" when the tag hangs under its target (default "down" = above it).
- `card` elements with a box narrower than 900 px are drawn as list tiles at box size (no scaling).
