# OpenGL / imgui / GLFW gotchas (hard-won)

**Reference document** — the trap corpus accumulated porting ~100 SuperBible
demos and building the viz engine: each entry cost a debugging session to find.
Check here before writing or debugging any GL/imgui/GLFW code in this repo.
Not a task; update in place. Last updated 2026-07-30.

Sources are archived task docs, cited per entry. The repo-wide GL *conventions*
(row-major + transpose at upload, CCW winding, VAO-never-zero, the `-1`
uniform sentinel) live in `CLAUDE.md` › "Coding standard › (c) mvp-specific";
this doc is the failure modes.

---

## 1. imgui_bundle / GLFW integration

- **`GlfwRenderer(window)` installs its own GLFW key callback and does NOT
  chain.** Call `glfw.set_key_callback(window, on_key)` **after**
  `GlfwRenderer(window)`, or every callback-driven key dies silently. This
  regressed all 18 render-option ports at once; demos that *poll* keys
  escaped, which made it confusing. Same for `set_cursor_pos_callback`.
  (`tasks/archive/2026/06/01/ports-render-options-to-imgui.md`)
- **It also swallows the mouse-button callback.** Don't use
  `glfw.set_mouse_button_callback` at all — poll `glfw.get_mouse_button` per
  frame, edge-detect the press, and gate on
  `imgui.get_io().want_capture_mouse`. (same archive; used by the chapt12
  picking demos)
- **imgui's fixed-function GL2 backend draws with whatever texture state you
  left active.** Ending a scene with `GL_TEXTURE1` active + texgen + cube map
  on corrupted both the scene and the menubar (chapt09/multitexture). Reset to
  plain `GL_TEXTURE0`, texgen off, before imgui draws. A bound GLSL *program*
  makes a demo immune (fixed-function units don't govern then) — why
  vertexshaders was fine.
  (`tasks/archive/2026/06/01/ports-mirror-keyboard-in-imgui.md`)
- **Menubar conventions (Bill's call, 2026-05-29):** ports use a top menubar,
  not floating windows (`_common.draw_menubar` / `menu_action`). Menu items
  can't hold-to-repeat — movement items fire once per click and display their
  key in the shortcut column; holding the *key* gives continuous motion.
  Sliders/pickers live in a `begin_menu` submenu so the menu stays open while
  dragging. Some demos need render-state guards so the menubar isn't clipped
  (stencil demo disables `GL_STENCIL_TEST`; pstipple scopes
  `GL_POLYGON_STIPPLE`; single-buffered `single` draws imgui before
  `glFlush`). (same archive)
- **imgui-bundle is unpinned in `requirements.txt`**; a drifted bundled glfw
  once produced `undefined symbol: glfwGetX11Window`. Known-good wheel:
  **1.92.801**. Same symbol family as the `PYGLFW_LIBRARY` dual-lib fix in
  `design-decisions.md` › Wayland.
  (`tasks/archive/2026/07/09/crossproduct-tex-billboard-labels.md`)

## 2. Fixed-function GL (the SuperBible-era rules)

- **`GL_RESCALE_NORMAL` whenever `glScalef` runs at render time.**
  `glScalef(0.01)` scales the *normals* too, so `dot(N,L)` collapses and
  lighting goes near-black (bit thunderbird/thundergl/vbo). Related: the
  default `GL_SPECULAR` is black — no `glMaterialfv(GL_FRONT, GL_SPECULAR,…)`
  means no highlights — and `GL_LIGHT_MODEL_COLOR_CONTROL =
  GL_SEPARATE_SPECULAR_COLOR` keeps highlights untinted by the texture.
  (`tasks/archive/2026/05/26/HANDOFF-2026-05-13.md`, "standing patterns")
- **Bind the texture BEFORE `glTexParameteri`.** Params land on whatever is
  bound; with only level 0 uploaded and the default mipmapping min-filter the
  texture is *incomplete* and Mesa samples black (chapt13/occquery — the C++
  got away with it by operating on texture 0). (same)
- **Color picking replaces `glRenderMode(GL_SELECT)`** — Mesa's compat
  profile crashes on the select pipeline (especially GLU quadrics drawn in
  SELECT mode). Encode the pick id in the R byte, draw to the back buffer
  without swapping, `glReadPixels` one pixel, decode; HiDPI needs a
  cursor→framebuffer scale. `GL_FEEDBACK` bounding boxes → scan the
  framebuffer with numpy instead. (same)
- **`glAccum` is a hard error on Bill's Mesa** (no accumulation buffer;
  `GLError 1282` — chapt06/motionblur). (same)
- **dt-based animation always:** never `rot += constant` per frame; use a
  `*_PER_SEC` rate × dt from `time.monotonic()`. And accept `glfw.PRESS`
  **and** `glfw.REPEAT` for movement keys (matches GLUT auto-repeat), PRESS
  only for toggles. (same)
- **A frame-count animation clock (`t += 1/60` per frame) silently converts
  an fps drop into a wall-clock slowdown** — symptoms look like "the math got
  slower" when it's the clock. Use wall time.
  (`tasks/archive/2026/07/09/math-demos-section-crossproduct-and-proof.md`)

## 3. The planar-shadow matrix and clip-space `w` (a corrected belief)

**The SuperBible planar-shadow matrix is NOT sign-invariant in OpenGL** —
earlier notes claimed it was (projectively, `(p,w)` ≡ `(−p,−w)`), and that
claim is still sitting in `tasks/archive/2026/04/28/plane-and-normal-helpers.md`
and `HANDOFF-2026-04-28.md`. **It's wrong in practice** because clip testing
happens *before* the perspective divide: GL tests `−w ≤ x,y,z ≤ w`, which is
unsatisfiable for `w < 0`, so **every vertex is discarded — no error, no
warning, the shadow just vanishes.**

The matrix's bottom row makes every transformed vertex share the constant
`w = n·(−light.xyz)`, and it bites here specifically because **mvp's
`plane_equation` is CCW while SuperBible's `m3dGetPlaneEquation` is CW** — so
feeding mvp's plane into the textbook formula yields negative `w` for the
typical ground-plane/overhead-light setup.

Fix: `sign = 1.0 if (a*lx + b*ly + c*lz) > 0.0 else -1.0`, multiply the whole
4×4. Reference implementation: `make_planar_shadow_matrix` in
`ports/openglsuperbiblev4/chapt01/block/Block.py` (applied to the sphereworld
family and chapt19/SphereWorld32).

Diagnosis pattern worth copying: renders were pixel-identical, `glGetError()`
clean, `glGetFloatv(GL_MODELVIEW_MATRIX)` correct — the smoking gun was a
manual `M @ v` showing `w = −120`.
(`tasks/archive/2026/05/26/notes-planar-shadow-w-clipping.md`; live consumer:
`tasks/planar-shadow-matrix.md`)

## 4. Screen-space line thickness (why `frustum.geom` exists)

The perspective `project()` compresses back-edge X/Y by `near_z/far_z` (≈0.04
= 25× with the default −2/−50), so a world-space 0.05 cylinder radius goes
**sub-pixel** at the frustum's far face and the rasterizer stipples it. Fixed
with a geometry shader: take the line in clip space, compute the perpendicular
in *screen* space, scale by `u_thickness` (pixels), transform the offset back
through `inverseTranspose(matrix_ndc_to_screen)` and each endpoint's `w` —
a quad exactly `u_thickness` px wide at any depth/projection/animation state.
The ortho frustum kept cylinders (its squash is only ≈0.13); ground cylinders
could in principle hit the same at extreme angles — untested.
(`tasks/archive/2026/04/29/notes-screen-space-thickness-geom-shader.md`)

## 5. Cube maps, texture matrices, PBOs

- **`GL_REFLECTION_MAP` texgen computes eye-space coords.** For a
  world-anchored reflection under a *rotating* camera, inverse-rotate the
  camera yaw into the `GL_TEXTURE` matrix each frame. Trigger checklist:
  pure-translate cameras don't trigger it, object rotations don't either
  (thundergl/solar/atom fine); fboenvmap is immune because it regenerates the
  cube map per frame. **The `GL_TEXTURE` matrix stack is per texture unit** —
  `glActiveTexture` the cube map's unit first or you rotate the wrong one.
  (`tasks/archive/2026/06/01/cubemap-reflection-static.md`)
- **Size PBOs for real at setup.** hdrbloom allocated a 1-byte placeholder,
  and `change_size` only grew it *on change* — the startup call saw none, so
  a later `glTexImage2D` read 786 KB from a 1-byte buffer
  (`GL_INVALID_OPERATION`). Row pitch: `((width*3)+3) & ~0x3`.
  (`tasks/archive/2026/06/01/hdrbloom-pbo-sizing-crash.md`)
- **PyOpenGL's `None` to `glReadPixels`/`glTexImage2D` defeats a bound PBO.** The C
  code passes `(GLvoid*)0` = offset 0 into the buffer; PyOpenGL turns `None` into a
  freshly-allocated *client* array and passes its pointer, so GL reads that as a giant
  byte offset → `GL_INVALID_OPERATION (1282)`. Pass **`ctypes.c_void_p(0)`** for the
  offset-0 case. Two siblings from the same demo: the ring PBOs must come from
  `glGenBuffers` (not literal names `1/2/3`), and the map/attenuate helper must use
  stdlib **`ctypes.c_uint8`**, not `np.ctypes.c_uint8` (numpy has no `ctypes` attr).
  All three bit chapt18/pixbufobj. (`tasks/ports-pbo-floattex-runtime-crashes.md`)

## 6. Python-side traps

- **A port named like a stdlib module shadows it when run by path.**
  `chapt12/select/select.py`: the script dir lands on `sys.path[0]`, then
  `glfw.library` → `subprocess` → `import select` re-enters the demo
  mid-import and crashes inside imgui_bundle's asyncio chain. Fix: remove the
  script dir from `sys.path` right after the stdlib imports, before
  `import glfw`. The file can't be renamed (mirrors the upstream tree).
  (`tasks/archive/2026/05/26/HANDOFF-2026-05-13.md`)
- **gacalc's general transform layer can leak sympy into a hot path.** The
  generic `rotor_rotation` returns a symbolic `Gn` (~2.7 ms/edge) where the
  specialized `Vector.rotor_from_vectors(...).sandwich(...)` path stays float
  (~0.035 ms) — same family as the `plane_rotation` 25× entry in
  `design-decisions.md`, different API. If a viz demo's frame time collapses,
  check coefficient types first.
  (`tasks/archive/2026/07/09/math-demos-section-crossproduct-and-proof.md`)
- **After any bulk edit across demos, grep for the replaced names *inside
  function bodies*** — `py_compile`/`compile()` is not a gate for orphaned
  code; it fails only at runtime, per frame. For body-replacing rewrites use
  `libcst` (preserves comments/whitespace), not regex and not raw `ast`
  unparse. (`tasks/archive/2026/04/28/postmortem-phase2-attempt-1.md`,
  `2026/05/26/notes-2026-05-02-v4-camera-attempt-reverted.md`)
