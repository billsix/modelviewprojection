# Framebuffer↔NDC warp animation, bracketing the perspective visualization

**Status:** COMPLETE — bracket built, refined round by round, and signed off by the maintainer
("framebuffer bracket looks fine", 2026-09-17). Not archived this session at the maintainer's
request. A software-rasterizer follow-on (below) is to be created when this task is archived.
**Priority:** 6
**Difficulty:** 6
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>) — originally mis-scoped, see
"Scope correction".
**Retargeted + implemented:** 2026-09-16 (William Emerison Six <billsix@gmail.com>).
**Signed off:** 2026-09-17.

Each round was verified non-visually by the container gate (ruff + `ty` via `make format`, and
`test_cayley_scene.py` 15/15) and then run + committed by the maintainer, who verified the visual
result (GL runs need a display, which only the maintainer has).

## BLUF

Teach *why* the raster warps when the framebuffer's aspect ratio differs from NDC's, by
**showing it** rather than explaining it in words. In the interactive perspective visualization
(`mvpvisualization/modelviewperspectiveprojection.py`) the user configures **pixel dimensions**
(default **20×10**) in place of the raw aspect slider; the framebuffer draws as a wireframe pixel
grid in world space; and the existing demo is **bracketed**: a prologue morphs the flat grid → a
rectangular prism → the NDC cube (the 2:1 box squashing into the 1:1 cube is the lesson), the
existing demo then runs unchanged, and an epilogue re-shows the grid and warps NDC → prism →
framebuffer. Done = the bracketed animation runs, pixel dims are configurable and default 20×10,
and the warp is visibly non-uniform for a non-square grid.

## Goal

A student asked why the raster *warps* — the framebuffer's aspect ratio differs from NDC's. The
maintainer wanted to answer with this animation, not with words.

Maintainer's description, verbatim (2026-09-16): *"currently, at the beginning of the demo, it
starts with a NDC cube in 3D space. What I want done, is that when the user of this configures
stuff, like they can with the aspect ratio in the GUI, instead of doing that, I want them to be
able to select pixel dimensions, and I want it to default to 20 by 10, 20 horizontally, 10
vertically. and I want, the '2D' framebuffer, with those pixels, draw using lines, centered at
0,0,0, which each pixel being a 'square' (although it can be drawn just using lines). I want the
20 by 10 to be in world space, so unlike NDC which goes from -1 to 1 in all dimensions, this
should start, if configured 20x10, from -10 to 10 in the x and y. For the first step of the
animation, I want that to animate into a rectangular prism, with the lines for the pixels on the
front face and back face. I then want that to warp into NDC. once that happens, I want the lines
to represent the pixels to disappear, and it's like the normal beginning of the demo, unchanged.
Then, after the last step of the existing demo, I want those pixel boundary lines to reappear,
and for the whole scene to warp back to the prism of dimensions, say 20x10 (or whatever it's
configured to."

## Scope correction (2026-09-16)

The task was originally filed (2026-08-27) from a terse one-liner — *"Make framebuffer in
perspective, make it configurable, show at last stage, with test for clockwise like in the
notebook"* — and read as work on the **software rasterizer**
(`src/modelviewprojection/framebuffer/softwarerendering.py`) and its winding-predicate notebook.
The 2026-09-16 clarification showed the real target was the **interactive mvpvisualization demo**
(`mvpvisualization/modelviewperspectiveprojection.py`) — a different subsystem, with no clockwise
test involved. The task was retargeted; the software-rasterizer angle became the follow-on task
below. Prior investigation notes are kept at the bottom.

## Context — how the target demo works

Files (all under `src/modelviewprojection/`):

- `mvpvisualization/modelviewperspectiveprojection.py` — the program. Declares the `Scene`
  (spaces, edges, `to_ndc` list), owns the imgui menubar, the per-frame draw, and the run loop.
  The new UI and the animation brackets live here.
- `cayley/cayleyscene.py` — turns the declarative `Scene` into a `Timeline`/`Animation`. `to_ndc`
  is an ordered list of `InverseOperations` (CPU affine) and `NonInvertibleTransformation` (GPU
  squash/ortho, label + time-slot only). `step_duration=5.0`; timeline slots accumulate
  `dwell_before + step_duration`.
- `mvpvisualization/cayley_gl.py` — the GL shell: `Frustum`, `RectangularPrism`, `build_standard`,
  `StandardObjects`, and the line-mesh builders `_volume_edges` / `frustum_lines` /
  `rectangular_prism_lines`.
- `mvpvisualization/_pipeline.py` — `build_ndc_cube_vertices()` = the `[-1,1]³` reference cube
  (12 edges), drawn un-morphed by `draw_cube()`.
- `mvpvisualization/project_perspective.glsl` — the GPU squash. Now driven by a `squash_ratios`
  uniform (see "Timing made dynamic"); the final `scale_to_ndc` uses `right = top * aspect_ratio`,
  so x scales by `1/right`, y by `1/top` — the unequal x/y scale for a non-1:1 aspect is exactly
  the warp the student saw.

Reference docs for this subsystem: `tasks/reference/architecture-overview.md` (demo layout,
working constraints), `tasks/reference/gl-and-imgui-gotchas.md` (GL conventions, the `-1` uniform
sentinel, GL_LINES).

## The pedagogy (why the numbers matter)

- Framebuffer 20×10 → world extent x∈[−10, 10], y∈[−5, 5] → **aspect 2:1**.
- NDC → x∈[−1, 1], y∈[−1, 1] → **aspect 1:1**.
- Warping framebuffer-prism → NDC-cube is a non-uniform scale (x·1/10, y·1/5): x is squeezed more
  than y. That visible asymmetry is the answer to the student's question. A square grid (x and y
  both −10..10) would scale uniformly and show no warp — so the 2:1 default is load-bearing.

## What was built

- **Config UI.** A new "Framebuffer" menu holds two `imgui.input_int` fields (Width/Height px),
  default 20/10, clamped to [4, 40]. Below them a read-only `aspect = width / height` line shows
  both the float and the fraction, labeled so the orientation (width÷height) is unmistakable. The
  old "Frustum Aspect" slider was removed from the Camera menu; aspect is derived from W/H and
  rebuilt with the grid.
- **Framebuffer grid mesh.** `cayley_gl.framebuffer_grid_lines(w_px, h_px, half_w, half_h)` builds
  the prism form (grid on the front z=+1 and back z=−1 faces + four corner connectors) as one
  DYNAMIC-VBO mesh, rebuilt on a W/H change (`rebuild_framebuffer`). Flat vs prism is a z-scale of
  this one mesh, not a second mesh.
- **Prologue.** `grid_matrix(t)`: the flat grid starts with its bottom-left corner at the origin
  (x∈[0,W], y∈[0,H]), then (1) translates to centred, (2) warps x,y to the NDC square (x·2/W,
  y·2/H, flat at z=0), (3) extrudes z 0→1 to the NDC cube. The unequal x/y warp is the lesson.
- **Epilogue.** The grid re-shows and warps NDC → prism → framebuffer bottom-left origin,
  **linearly** (see "Epilogue curve"). The same transform is applied to the demo's own squashed
  geometry via a scoped view multiply, so grid and scene stay coincident.
- **Timeline.** The existing scene is driven by `demo_t = t − PROLOGUE_DUR`, and that same
  `demo_t` feeds the squash shader, so no shader retiming was needed. Global timeline: flat-grid
  hold → translate-to-centre → warp-to-NDC → extrude → existing demo (unchanged) → epilogue
  warp-back → hold. `DEMO_DUR` is read from `animation.timeline.duration`, and `PROLOGUE_DUR`
  from the phase constants, so both survive adding steps.
- **Graph-panel narration.** Prologue group "Framebuffer -> NDC" and epilogue group
  "NDC -> Framebuffer" were added to the "Towards NDC" tree, built from `cayleyscene.GuiGroup`/
  `GuiButton` in the demo so shared `cayleyscene.py` was left untouched (the brackets live in
  global time, outside the scene's demo-local timeline).

The brackets touched two files: `cayley_gl.py` (the `framebuffer_grid_lines` builder) and
`modelviewperspectiveprojection.py` (the constants, state, grid VBO/VAO + `rebuild_framebuffer`,
`grid_matrix`, the epilogue transform, `draw_grid`, the "Framebuffer" menu, the `demo_t`
rewiring, and the graph groups).

## Decisions

1. **y-extent:** the grid is x∈[−W/2, W/2], y∈[−H/2, H/2]. For 20×10 → x∈[−10, 10], y∈[−5, 5]
   (the 2:1-vs-NDC-1:1 contrast is the point).
2. **Prism depth:** after extrusion the prism spans z ∈ [−1, 1], matching NDC depth, so only x and
   y warp; z passes through. Fixed, not user-configurable — only W×H is user-facing.
3. **Unified aspect:** W/H drives the frustum `aspect_ratio` used by the existing squash as well as
   the framebuffer bracket. One number everywhere.
4. **Aspect display:** derived from W/H, read-only, shown as both float and fraction, labeled as
   width÷height (the maintainer notes he often forgets the orientation).
5. **Input widget/bounds:** `int` inputs, default 20/10, min 4, max 40.
6. **Software rasterizer:** deferred to the follow-on task below; not scaffolded here.

### Judgment calls the maintainer reviewed and accepted

1. **Not the ground grid.** The ground (`build_ground_vertices`) is a fixed 40×40 floor grid in
   the X-Z plane at y=−5; the framebuffer is a configurable W×H grid in the X-Y (screen) plane
   centred at the origin, with two faces + connectors forming the prism. Same idiom, different
   mesh — a new builder was warranted. (The maintainer asked "doesn't the ground already do
   this?"; it does not.)
2. **Flat↔prism as a z-scale of one prism mesh** (front and back coincide at z-scale 0 → reads as
   flat), rather than morphing two meshes.
3. **Epilogue = the reversed viewport transform.** Two phases: un-warp the aspect (NDC square →
   centred prism, `*W *H`), then translate centre → framebuffer **bottom-left origin** — i.e.
   `glViewport`'s `ndc*size/2 + size/2`, a scale AND an offset (the maintainer: "do the inverse of
   the translation, not just the inverse of the non-uniform scaling"). Applied to both the grid and
   the placed meshes via the view, so the scene ends inside the framebuffer prism at the bottom-left
   origin. The reference NDC cube stays at ±1 (contrast); ground/world-axis/camera stay at world
   scale.
4. **Grid colour** cyan `(0.2, 0.8, 1.0)` to stand apart from the white NDC cube; **pixel cells are
   1×1** (extent == pixel count), so 20×10 is 20 unit-squares across.

### Refinement rounds (the maintainer requested these one at a time, committing between each)

Recorded as the final state; where an approach was later changed, the supersession is noted.

- **A1 — framebuffer narration at the top of the panel.** The framebuffer expansion narration sits
  at the top of the Cayley Graph panel, above the existing trees.
- **A2 — prologue order: warp to NDC square first, then extrude in z.** `grid_matrix` warps x,y to
  the NDC square (flat at z=0), then extrudes z 0→1 to the NDC cube. Panel buttons relabeled to
  match.
- **A3 — the transformed framebuffer stays visible the whole time.** `grid_matrix`'s demo-phase
  branch returns the NDC-cube matrix (rather than hiding the grid), depth-cleared on top each
  frame, and the epilogue warps it (and the squashed scene) back out.
- **A5 — framebuffer starts bottom-left at the origin; translate-to-centre is prologue step 1.**
  Inserted before A4 at the maintainer's request. The flat grid starts with its bottom-left corner
  at (0,0,0); prologue step 1 translates it to centred, then A2's warp, then extrude. A "Translate
  to center" button was added as the first panel step. (The prologue is un-centred at the end via
  the epilogue's translate; only the prologue translate was requested.)
- **A6 / A8 — the grid morph is built with gacalc, not raw numpy.** Per the maintainer ("why are
  you using matrices? can't you use my gacalc functions?") and the new CLAUDE.md rule, the
  hand-built `_diag` + offset factors were replaced by three gacalc helpers — `_warp` (centred
  prism → NDC aspect scale), `_place` (centre → bottom-left origin), `_flatten` (prism → flat,
  forward-only) — composed with `compose`, animated with `.at()`, reversed with `inverse()`, and
  realized to a 4×4 only for GL upload (`cayleyscene.to_matrix`). Proven identical to the old numpy
  form by `tasks/adhoc/framebuffer-in-perspective/verify_gacalc_morph.py`; the gacalc `.at()` /
  `inverse` laws were verified in `.../probe_gacalc_at_inverse.py`.
- **A4 — the grid is drawn on the camera-as-object's NDC cube too.** When the camera-as-object is
  drawn, the framebuffer pixel grid is drawn on its NDC cube (held at the NDC form) right after the
  camera's `draw_cube()`.
- **A7 — "View From → Framebuffer".** A `FB_FOCUS = "framebuffer"` sentinel (not a `Space`); the
  menu item is enabled only once the framebuffer has settled back at its original bottom-left space
  (`state["time"] >= PROLOGUE_DUR + DEMO_DUR + EPILOGUE_WARP + EPILOGUE_TRANSLATE`, derived from
  the phase durations so it still means "after the framebuffer is home" if steps are added). When
  selected, `frame` orbits around the framebuffer's current centre. This added an `enabled=` param
  to `cayley_gl.menu_action`.
- **Epilogue curve — LINEAR.** The warp-back was briefly a reciprocal ease-in — a side effect of
  building it as `inverse(_warp).at(t)`, since `inverse(f).at(t) == inverse(f.at(t))` is a
  reciprocal curve, and the grid and scene had to share one transform to stay coincident (proven
  in `.../verify_at_inverse_equiv.py`). On the maintainer's call (my recommendation) it was
  switched to linear by building the NDC→framebuffer scale directly
  (`scale_non_uniform(hw, hh, 1).at(t)`), matching the linear forward prologue and reading as the
  plain scale-then-translate viewport transform. Still gacalc + `to_matrix` at the GL boundary; the
  rationale is in `_epilogue_ndc_to_fb`'s docstring, and grid and scene still share the one
  transform.

## Timing made dynamic — no hardcoded absolute times

**The bug:** the graph-panel squash buttons fired ~3s before the visual squash.

**Root cause** (from the archived `2026/06/03/cayley-graph-visualizations.md` + git history):
pre-refactor, the demo had a `StepNumber(Enum)` of `State(name, duration)` with
`calculate_start_times()` accumulating durations, which put the squash at 87 while
`project_perspective.glsl` hardcoded it at 90/95/100/105. That 3s drift was **original** — older
than the Cayley refactor, which faithfully carried it into `Timeline` (tests assert 87).
`Animation.gpu_progress` (the dynamic per-step progress) existed and was unit-tested but was wired
to no shader.

**Fix** (what the maintainer asked for — "add steps with durations, no hardcoded absolute times"):
`gpu_progress` was wired into the shader. `project_perspective.glsl` now takes a
`uniform vec4 squash_ratios` (one progress value per squash step) and has zero hardcoded times; the
demo sets `squash_ratios` each frame from `animation.gpu_progress(demo_t)` on the mesh + frustum
pipelines (the axis pipeline stays at 0, so axes never squash), and `_pipeline.Pipeline.u_squash`
caches the uniform location. `dwell_before` stays 10 (the earlier band-aid of 13 was reverted);
the timeline still computes 87 (tests unchanged, 15/15), and the visual squash now happens at 87
too, aligned with the buttons.

**Regression + fix — paddles/square/axis-tips vanished until the camera inverse.** Removing the
shader's `if(time<90)` identity guards looked safe ("ratio 0 ⇒ identity"), but `scale_x`/`scale_y`
compute `near_z/cameraSpace.z`, and the paddles, square, and axis tips sit in the z=0 plane until
the world→camera inverse lifts them off it; at z=0 that is `∞`, and `∞·0 = NaN`, so those vertices
got a NaN `gl_Position` and were dropped. The fix guards `scale_x`/`scale_y` on
`squash_ratios.x/.y > 0.0` (identity at ratio 0 without evaluating the divide) — NaN-safe and still
no hardcoded times. `translate`/`scale_to_ndc` have no vertex-z divide, so they stay unguarded.
Instrumentation confirming the reveal was logic-correct is in
`tasks/adhoc/framebuffer-in-perspective/dump_timeline.py`.

**Follow-on (not done):** `project_ortho.glsl` (modelvieworthoprojection) has the same hardcoded
90/95 pattern; the same treatment would fix it. Worth a separate task.

## Follow-on task (create when this task is archived)

Scaffold a separate task for the **software-rasterizer** angle of the original one-liner —
*"framebuffer in perspective … test for clockwise like in the notebook"* — targeting
`src/modelviewprojection/framebuffer/softwarerendering.py` and its `notebooksrc/framebuffer.py`
notebook (winding predicates `is_clockwise`/`is_counter_clockwise`, existing tests at
`tests/test_mathutils.py:208-214`). Status `proposed — needs go-ahead`. It is gated on this task
finishing, so it is not created yet.

## Adhoc scripts (kept under `tasks/adhoc/framebuffer-in-perspective/`)

- `verify_gacalc_morph.py` — proves the gacalc morph equals the old numpy form across samples.
- `probe_gacalc_at_inverse.py` — verifies the gacalc `.at()` (`1+(m-1)t` / `v·t`) and `inverse`
  laws.
- `verify_at_inverse_equiv.py` — proves grid and scene share one epilogue transform (no drift).
- `dump_timeline.py` — reconstructs the scene and prints the timeline vs the shader.

---

## Prior investigation (2026-08-27) — kept for the record, now superseded

The pre-retarget notes read the goal as software-rasterizer work:

- Software rasterizer: `src/modelviewprojection/framebuffer/softwarerendering.py`; its driving
  notebook is `src/modelviewprojection/notebooksrc/framebuffer.py` (a book toctree page between
  ch02–03).
- Winding predicates `is_clockwise`/`is_counter_clockwise` live there; unit tests exist at
  `tests/test_mathutils.py:208-214`, and a clockwise regression was added in archived
  `2026/05/26/fix-is-clockwise-recursion.md`.
- Reference: `tasks/reference/notable-subsystems.md §1` (rasterizer design),
  `tasks/reference/book-figures-and-images.md §3` (notebook pipeline).

These seed the software-rasterizer follow-on task above.
