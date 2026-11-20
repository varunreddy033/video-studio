Prompts to give Claude, one per picture style (since 2026-11-19 each style has its own file).

In Video Studio: + New video (or Make Short -> From scratch), pick Pictures, then "Copy" next to "Prompt to give
Claude" copies that style's prompt and "Load sample" loads that style's sample. Paste the prompt into a Claude chat,
fill in the TOPIC / IDEA / ANGLE lines, paste Claude's script into Video Studio and press Check. If Check shows errors
or warnings, paste them back to Claude and ask it to fix the script.

| Pictures | Full video prompt | Short prompt | Sample (passes Check) |
|---|---|---|---|
| Motion graphics (default) | docs/script_prompts/motion.md (was prompt D) | same | docs/sample_motion_gfx_script.md |
| AI images, no presenter | docs/script_prompts/ai_image.md (was prompt B) | docs/script_prompts/ai_image_short.md | docs/sample_script.md / docs/sample_ai_image_short_script.md |
| AI images, Sterling presents | docs/script_prompts/ai_image_sterling.md (was prompt A) | docs/script_prompts/ai_image_sterling_short.md (was prompt C) | - |
| Blocky 3D (story Shorts) | docs/script_prompts/blocky3d.md | same | docs/sample_blocky3d_script.md |
| 3D explainer | docs/script_prompts/explainer3d.md | same | docs/sample_explainer3d_script.md |
| Neon motion | docs/script_prompts/neon.md | same | docs/sample_neon_script.md |

Which prompt and sample each style gets is set in pipeline/config.py SCRIPT_KITS; `bin/python tools/check_script_kits.py`
must say "script kits: clean" (every sample passes Check as its own style, as a full video and as a Short).

Motion graphics is what Video Studio makes when the header has no rendering_method: line, so every prompt writes the
line explicitly. The Sterling prompts are for the character channel only: never reuse his sign-offs or persona in
another style's script.
