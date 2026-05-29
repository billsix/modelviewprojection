# Move keyboard-driven rendering options to imgui controls (SuperBible ports)

**Status:** not-started — logged 2026-05-29 (Bill). Investigated the recent-commit set (below).
Confirm scope/conventions with Bill, then implement.

## Goal

Every port that uses **keyboard keys to change *how the scene is rendered*** (mode toggles,
shader/filter selection, shading model, fog, show-the-map debug views, pass counts, FBO on/off,
polygon-offset, etc.) should expose those as **imgui controls** (checkbox / radio / combo /
slider) instead of (or in addition to) keypresses. Applies to **all demos**, prioritizing the
ones just converted in the geometry-extraction work ([[extract-data-generation]]).

**Keep on the keyboard:** continuous *navigation* — camera/light position (`X`/`Y`/`Z`),
orbit/rotate (arrow keys), and `Esc`/quit (already also in the `_common` File→Quit menubar).
Those aren't "rendering options"; you don't drive a camera walk from a checkbox. (Open question
for Bill: should camera also get optional imgui sliders? Default assumption: no, leave nav on keys.)

## In-repo models to follow
- `chapt05/spot/spot.py` — already has an imgui panel: radio buttons for shade model (flat/smooth)
  and tessellation (low/med/high). This is the target pattern.
- `chapt09/texgen/texgen.py` — imgui radio for the texgen render mode.
- `_common.py` — `init_imgui(window)`, `draw_menubar(window, win_state)`, `WindowState`. Several
  shader demos below do **not** init imgui yet, so part of the work is adding the
  GlfwRenderer/init + per-frame `process_inputs()` / new-frame / render-draw-data plumbing
  (careful in the FBO demos: draw imgui to the default framebuffer, after the scene/FBO blit).

## Per-demo inventory (recent-commit set) — option keys → proposed widget

| Demo | Rendering-option keys (→ imgui) | Proposed widget | Nav keys (keep) |
|---|---|---|---|
| chapt14/shadowmap | `S` shadows on/off · `M` show shadow map · `C` control camera-vs-light · `F` polygon-offset factor ± | 2 checkboxes + 1 radio (camera/light) + slider (factor) | X/Y/Z move selected |
| chapt18/fboshadowmap | `S` shadows · `M` show map · `C` control · `F` offset ± · `+`/`-` (decode: map size/bias?) · `use_fbo` | checkboxes + radio + slider(s) | X/Y/Z, arrows |
| chapt15/shaders | `V` use vertex shader · `F` use fragment shader · `B` blink | 3 checkboxes | X/Y/Z |
| chapt16/vertexshaders | `1`–`0` select 1 of 10 shaders · arrows (light rotation?) | combo/radio (10 entries) | X/Y/Z (+ arrows if rotation) |
| chapt17/fragmentshaders | `1`–`7` select filter shader | combo (7) | arrows, X/Y/Z |
| chapt17/imageproc | `1`–`8` select filter · `P` then `1`–`5` = num passes | combo (8) + slider/int (passes 1–5) | arrows, X/Y/Z |
| chapt17/lighting | `1`–`4` select shader | radio/combo (4) | arrows, X/Y/Z |
| chapt18/fbodrawbuffers | `D` use draw buffers · `P` post-processing | 2 checkboxes | X/Y/Z, arrows |
| chapt18/fboenvmap | `E` use env map · `S` show env map · `F` use FBO | 3 checkboxes | X/Y/Z, arrows |

Note: most of these print state to stdout on each keypress (a CLI-ish affordance) — the imgui
control should replace that feedback too. `imageproc`'s "press P then a digit" two-step is
exactly the kind of hidden modal interaction imgui fixes.

Also pending bug task [[shadowmap-depth-discrimination]] proposes a NEW `D` toggle on the
shadow demos — coordinate: that toggle should be an imgui control under this task, not a key.

## Wider scope
Beyond the table: **audit `on_key` across all ~95 ports** for option-toggles (older demos too —
e.g. anything with flat/smooth, wireframe, fog, animation pause, mode cycling). The recent set
above is the priority; the rest follows the same treatment.

## Plan
1. Decode the few remaining ambiguous keys (`fboshadowmap` `+`/`-`; `vertexshaders` arrows) and
   finish the full-repo `on_key` audit.
2. Agree conventions with Bill: one imgui panel per demo (title = demo name, like spot's
   `imgui.begin("Spot")`); checkbox/radio/combo/slider mapping; keep nav on keys; replace stdout
   prints with the imgui state.
3. Add imgui infra (`_common.init_imgui`, GlfwRenderer, per-frame plumbing + menubar) to demos
   that lack it; in FBO demos render imgui last, to the default framebuffer.
4. Convert option-keys to widgets; remove the option-key branches (keep Esc + nav).
5. Bill verifies visually (needs a display).

## Relationship to existing plans (coordinate, don't duplicate)
- [`../plans/ports-replace-cli-with-imgui.md`](../plans/ports-replace-cli-with-imgui.md) — Phase 3
  "replace CLI args with imgui". This task is the keyboard-options analogue; likely the same effort.
- [`../plans/ports-keyboard-standardization.md`](../plans/ports-keyboard-standardization.md) —
  Phase 3 "one keyboard convention". Decide which keys *remain* (nav) here.
- [`../plans/ports-ux-pass.md`](../plans/ports-ux-pass.md) — umbrella; this fits its Phase 3.
