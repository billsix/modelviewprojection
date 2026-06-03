# Mirror every keyboard control as a key-labeled imgui element

**Status:** complete
**Completed:** 2026-06-02

All 94 keyboard-input demos now have a top imgui menubar (decided as menubar,
not floating windows; see PIVOT + ROLLOUT COMPLETE below). Structurally
verified 2026-05-29; Bill spot-checked + committed 2026-06-02.

## Goal (Bill, 2026-05-29)

For **anything with keyboard input**, add an imgui element that performs the **same action**,
labeled to say (1) what it does and (2) which key does the same thing — e.g. a button
`Camera +X  (X)`. The keyboard keeps working; the panel mirrors it.

## Decisions confirmed (Bill, 2026-05-29)
- **Scope: ALL demos with keyboard input** (~90 ports), including the ~50 nav-only demos that
  currently have NO imgui panel (they each need imgui infra added).
- **Held/continuous keys → repeat while the button is held** (`imgui.is_item_active()`), so a
  camera-move/rotate button held down moves continuously like holding the key. Discrete actions
  and Quit fire once per click.
- Label convention: `"What it does (Key)"`. Keep the keyboard handlers too (additive).

## Foundation (done)
- `_common.control_button(label, action, *, hold=False)` — button that runs `action()`; `hold=True`
  repeats every frame it's held; else once per click. (in `_common.py`.)
- **Reference: `chapt17/lighting/lighting.py`** — the template. Pattern per demo:
  - `import _common` (alongside the existing sys.path insert).
  - module global `_window = None`, set `_window = window` in `main()` (the Quit button needs it).
  - small mutator fns for any globals the buttons change (lambdas can't rebind a global float;
    e.g. `_nudge_light(d)`, `_nudge_cam(axis, d)`), reused by BOTH `on_key` and the buttons.
  - in `imgui_panel()`: an `imgui.separator()` + `imgui.text("Controls (keyboard still works)")`
    then one `_common.control_button("Action (Key)", lambda: ..., hold=...)` per key, ending with
    `control_button("Quit  (Esc)", lambda: glfw.set_window_should_close(_window, True))`.
  - movement/rotation buttons use `hold=True`; toggles/quit use the default one-shot.
  - keep lines ≤88 cols (wrap the lambda to the next line).

## Batches
1. **The 18 render-option demos** (already have imgui panels) — ✅ **DONE 2026-05-29** (separate
   `Controls` window confirmed: all 18 compile, `import _common` + `_window` + balanced 2/2
   begin/end, no F-code lint). Covered lighting + occquery, shadowmap, shaders, vertexshaders,
   vertexblend, fragmentshaders, imageproc, proctex, bumpmap, fogged, multisample, fbodrawbuffers,
   fboenvmap, fboshadowmap, hdrbloom, pixbufobj (Quit-only), texfloat (cursor-probe arrows mirrored).
   Note: occquery/vertexblend/bumpmap/pixbufobj/texfloat lacked the sys.path insert — agents added it.
2. **GROUP B imgui demos** (19) — ✅ **DONE 2026-05-29**. spot, texgen, pyramid, tunnel,
   anisotropic, block, bounce, star, triangle, ambient, smoother, imaging, operations,
   pointsprites, florida, starrynight, moons, planets, select. Each got a separate `Controls`
   window (nav buttons where applicable, else Quit-only) AND the **set-key-callback-after-
   GlfwRenderer fix** (all 19 predated it — so this also repaired their Esc/nav keyboard).
   Verified: all compile, Controls/`_window`/`import _common` present, callback order correct,
   no NEW F-codes. (star/triangle/ambient turned out to have polled arrow-rotation → got rotate
   buttons; moons/planets/select have mouse picking, left alone; select.py uses `_PWD` due to the
   stdlib `select` name clash.) Pre-existing `F401 'math' unused` remains in pointsprites +
   starrynight (NOT from this change) — left as-is.
3. **GROUP C nav-only demos (~50)** (sphereworld family, atom/atom2/solar, ortho/perspect, ccube,
   jet/litjet/shinyjet, lines/points/stipple/strips, snowman, cubedx, thunderbird/thundergl/vbo,
   SphereWorld32, GLRect, fscreen, …): add full imgui infra (create_context + GlfwRenderer +
   per-frame plumbing + key callback AFTER GlfwRenderer) AND a Controls panel. Biggest batch.
   Stubs (ch19 GLView/RThread, ch20, ch22) have no real loop/keys — skip or Quit-only.

## PIVOT 2026-05-29 — menubar instead of floating windows (Bill's call)

After seeing the floating `Controls` windows, Bill chose to put **all controls in the top
menubar** instead. Menubars can't hold-to-repeat, so movement items run **once per click** and
show their key in the shortcut column (discovery); holding the **key** still does continuous
motion. New helper `_common.menu_action(label, key, action, *, selected=False)` — a `menu_item`
that runs the action on click, shows `key` in the shortcut column, and checks when `selected`.

**Prototype done + verified (compile, no F-codes, no floating windows):**
- `chapt17/lighting` — menubar: File→Quit · Shader menu (radio-checked items) · Controls menu
  (Light ±, Camera ±X/±Y/±Z, each showing its key). Replaced its two floating windows.
- `chapt05/sphereworld` — the pure-walk-around / no-imgui-yet case: added full imgui infra +
  menubar (File→Quit · Controls: Forward/Back/Turn left/right). Per-click fixed step; keyboard
  still continuous.

**Rollout implication:** batches 1 & 2 (the 37 demos already given floating `Controls` windows)
must be **redone as menubars**; batch 3 (~50) done as menubars directly. `control_button` becomes
obsolete once all are converted (remove then). Render-options with **sliders/combos** (hdrbloom
bloom, imageproc passes, texgen/pyramid combos, …) go INSIDE their menu (imgui supports widgets in
menus — works, slightly different feel). Bill approved the prototype 2026-05-29 → full pass underway.

**Full menubar rollout (Bill approved 2026-05-29):**
- **Wave 1 — batches 1 & 2 redone as menubars: ✅ DONE.** All 38 already-imgui demos (lighting +
  chapt05/sphereworld references + the 36 from batches 1&2) now use a single top menubar:
  File→Quit, render-options as menus (radio→checked `menu_action`; toggle→checkable `menu_item`;
  combo→per-option radio items; slider/color→widget inside a `begin_menu`/`end_menu`), and a
  Controls menu of `menu_action("Action","Key",…)` movement items (click=one step, key in the
  shortcut column). Verified: all compile, no leftover floating windows / `control_button` /
  `imgui_panel`, balanced menu begin/end, no new F-codes (pre-existing `F401 math` in
  pointsprites + starrynight left as-is). Convention notes: combos became per-option radio menus
  (cleaner than embedding `imgui.combo`); sliders/color sit in their own submenu so the menu stays
  open while dragging (mildly awkward UX, flagged).
- **Wave 2 — batch 3 (56 no-imgui demos): ✅ DONE 2026-05-29.** Added full imgui infra
  (create_context + GlfwRenderer after the framebuffer callback, key callback last, per-frame
  process_inputs/new_frame/imgui_menubar/render/draw_data, shutdown) + a menubar (File→Quit, and
  a Controls menu mirroring movement: arrow-rotate demos → Rotate up/down/left/right; walk-around
  demos → Forward/Back/Turn left/right; Esc-only demos → File→Quit only). The 3 already-imgui
  text demos (Text2D/Text3D/fonts) got a menubar WITHOUT a second context. Verified: 56/56
  compile, exactly one imgui context each, menubar + `_common` + `_window` present, menu begin/end
  balanced, no NEW F-codes (pre-existing unused `import math` remains in thunderbird/thundergl/vbo/
  Text3D — the conversion actually fixed Text3D's pre-existing unused `os`). Stubs (ch19 GLView/
  RThread, ch20 Carbon/Coco/FullScreen, ch22 ES_example) have no real loop — skipped.
  Per-demo render-state guards a couple agents added (so the menubar isn't clipped): stencil
  disables GL_STENCIL_TEST before imgui; pstipple scopes GL_POLYGON_STIPPLE to its polygon;
  single (single-buffered) draws imgui before glFlush; GLXBasics moved its cursor callback after
  GlfwRenderer.
- **Cleanup: ✅** `_common.control_button` removed (everything now uses `menu_action`).

## Post-rollout bug (2026-05-29): imgui clobbers leftover texture state
Bill found `chapt09/multitexture` lost its cube-map multitexturing once the menubar was added:
`render_scene` ended with `GL_TEXTURE1` active + texgen/cube-map on, and imgui's fixed-function
GL2 backend draws on the active unit → corrupts the scene + (can) garble the menubar. **Fixed
multitexture** (reset to a clean `GL_TEXTURE0`/no-texgen/no-cube state at the end of `render_scene`;
restored the menubar Bill had commented out). See auto-memory `feedback-imgui-leftover-texture-state`.
**Likely-affected siblings to sweep (pending Bill verifying the multitexture fix on a display first):**
texgen, cubemap, shadowmap, fboshadowmap, fboenvmap, thundergl, thunderbird, vbo, vertexshaders,
occquery, pixbufobj, hdrbloom — each uses texgen/cube/2nd-unit and may leave bad state before imgui.

### Sibling sweep result (2026-05-29, after Bill confirmed the multitexture fix)
Assessed every candidate's `render_scene` end state (texgen on? cube map on? secondary unit still active?):
- **FIXED** (left bad state) — same re-assert-then-disable pattern as multitexture:
  - `chapt09/cubemap` — re-assert cube map at top of render_scene; disable cube map + texgen at end (single unit 0).
  - `chapt09/texgen` — disable texgen at end (render_scene re-enables it each frame, so no re-assert needed).
  - `chapt18/pixbufobj` — multi-unit motion blur left TEXTURE2 active; re-assert 2D on units 1/2 at top, disable + reset to TEXTURE0 at end.
- **ALREADY SAFE** (no change — they already disable/reset before render_scene returns): thundergl
  (disables texgen+cube + resets unit 0), vbo, shadowmap, fboshadowmap, fboenvmap, occquery, hdrbloom.
  thunderbird wasn't actually affected (no texgen/cube).
- **`chapt16/vertexshaders` — ✅ confirmed working by Bill (2026-05-29), no fix needed.** THREELIGHTS
  mode leaves GL_TEXTURE_1D on units 1/2/3, but the bound GLSL program (not fixed-function texture
  units) governs rendering, so the menubar is fine. Left untouched.

**Texture-state sweep COMPLETE:** 4 fixed (multitexture, cubemap, texgen, pixbufobj), 7 already-safe,
vertexshaders confirmed fine. The whole menubar task is now done modulo Bill's commits.

## ✅ ROLLOUT COMPLETE 2026-05-29
Every keyboard-input demo (94 total: 38 Wave 1 + 56 Wave 2) now has a top imgui menubar mirroring
its controls (toggles/modes as menu items, movement as click-once items showing their key);
keyboard still works (held = continuous). Structurally verified throughout; **pending Bill's
commit + visual spot-check** (can't run a display in-container).

## Caveats
- Can't visually verify in-container (no display, imgui_bundle not installed) — Bill checks.
- Held-button speed may not exactly match the OS key-repeat rate; tunable per demo if it feels off.
- Many GROUP C demos drive nav via per-frame polling (`handle_*` with dt); their hold-buttons use
  a fixed per-frame step (not dt) — simpler and fine for a convenience control.
- Relationship: complements [[ports-render-options-to-imgui]] and the ports-ux-pass plans.
