# Move keyboard-driven rendering options to imgui controls (SuperBible ports)

**Status:** in-progress — full repo audit COMPLETE 2026-05-29 (see "Full audit" below): **16
demos need work** (GROUP A), ~19 already have imgui panels (GROUP B), rest are nav/quit-only.
Awaiting Bill's go-ahead on conventions/scope (see "Decisions to confirm") before editing.

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

## Full audit (2026-05-29) — COMPLETE

Read every demo's key handler + the functions the keys call, classifying each key as a RENDER
OPTION (→ imgui) vs NAVIGATION/quit (camera/object rotate/pan/zoom + Esc — stays on keyboard).

### GROUP A — needs imgui work (16 demos: has render-option keys, NO render-option panel)

| Demo | Render-option keys → action | Suggested widget(s) |
|---|---|---|
| chapt13/occquery | `O` occlusion-query on/off · `S` show bounding volumes · `M` help overlay | 2–3 checkboxes |
| chapt14/shadowmap | `S` shadows · `M` show shadow map · `C` control camera/light · `F` polygon-offset ± | 2 checkboxes + radio + slider |
| chapt15/shaders | `V` vertex shader on · `F` fragment shader on · `B` blink | 3 checkboxes |
| chapt16/vertexblend | `B` blending on · `S` show bones · LEFT/RIGHT influence (0..1) · UP/DOWN elbow bend (−150..150) | 2 checkboxes + 2 sliders |
| chapt16/vertexshaders | `1`–`0` select shader (10) · **LEFT/RIGHT = fog density only in FOG modes** · **X/Y/Z = squash-stretch only in STRETCH** | combo + conditional slider(s) |
| chapt17/fragmentshaders | `1`–`7` select filter · **LEFT/RIGHT = fog density only in FOG mode** | combo + conditional slider |
| chapt17/imageproc | `1`–`8` select filter · `P`-then-`1`–`5` num passes | combo + int slider (1–5) |
| chapt17/lighting | `1`–`4` select shader | radio/combo |
| chapt17/proctex | `1`–`3` select shader · UP/DOWN tessellation (rebuild) | radio + slider |
| chapt17/bumpmap | `1`–`3` shape · `B` bumpmap shader · `M` show-bump · `R`/`P` bumpmap texture | radio (shape) + radio (shader) + radio (texture) |
| chapt18/fbodrawbuffers | `D` draw buffers (MRT) · `P` post-processing | 2 checkboxes |
| chapt18/fboenvmap | `E` env map · `S` show env map · `F` use FBO | 3 checkboxes |
| chapt18/fboshadowmap | `S` shadows · `M` show map · `C` control camera/light · `F` use FBO · `+`/`-` polygon-offset | 3 checkboxes + radio + slider |
| chapt18/hdrbloom | `1`–`8` pipeline stop-point/debug view · UP/DOWN tess · `L` bloom limit ± · `P` pause | combo + 2 sliders + checkbox |
| chapt18/pixbufobj | `B` motion blur · `P` PBO usage · arrows = animation speed | 2 checkboxes + slider |
| chapt18/texfloat | `F1`–`F4` tone-map shader · `1`–`8` test texture | 2 combos |

**3 of these were NOT in the original recent-commit list** — surfaced by the full audit:
chapt17/bumpmap, chapt18/pixbufobj, chapt18/texfloat. (Note: bumpmap + vertexblend are on the
geometry-extraction *leave-alone* list, but that's unrelated — their render-OPTION keys are in
scope here.)

### GROUP B — already has a real imgui render-option panel (≈19, DONE, use as models)
Block (3D-effects radio), bounce (sliders + pause), star (polygon-mode radio + edge-flag),
triangle (depth/cull/outline checkboxes), ambient (color_edit3), **spot** (shade + tess radios),
smoother (AA checkbox), imaging (mode radio + histogram), operations (mode radio), pyramid
(tex-env/min/mag combos), tunnel (min-filter combo), anisotropic (filter combo + checkbox),
pointsprites (draw-mode radio), **texgen** (mode radio), florida (method radio), starrynight
(draw-mode radio), moons/planets/select (show-selection-buffer checkbox). None have orphaned
keyboard-only render options (block/bounce keep SPACE as an intentional *mirrored* accelerator).

### GROUP C — no render-option keys (nav/quit only, or stubs) → NO WORK
All chapt03 line/point demos (arrows only rotate the model; width/size/stipple are fixed
constants), the sphereworld family, atom/solar/jet/litjet/etc., the ch10 NURBS/bezier demos,
ch11 thunderbird/vbo/cubedx, the ch19–22 stubs and text overlays, etc.

### Decisions to confirm before editing (real branch points)
1. **Context-dependent keys** (chapt16/vertexshaders, chapt17/fragmentshaders): the SAME key is a
   render parameter in some shader modes (fog density, squash-stretch) and navigation in others.
   Can't naively migrate — either show the slider only in the relevant mode, or always show it.
2. **New toggles vs migration only**: chapt06/fogged (fog) and chapt06/multisample (MSAA) enable
   features *unconditionally* with no key — exposing on/off there would be *adding* controls, not
   migrating. In scope or not?
3. **Two-step combo**: imageproc `P`-then-digit → a single int slider.
4. **Coordinate** with [[shadowmap-depth-discrimination]] (its proposed `D` distinct-mode toggle
   should land as an imgui control here, not a key).
5. Keep navigation (camera/object rotate, pan, zoom) on the keyboard — only options move.

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
