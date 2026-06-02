# Cayley-graph visualizations — make the graph a first-class data structure

**Status:** complete
**Completed:** 2026-06-03

> Consolidated summary of the 2026-06-02/03 work. (This replaces five
> intermediate task docs — datastructure, session log, pyMatrixStack inlining,
> imgui menubar, demo rename — whose step-by-step history is no longer accurate
> after the git history was squashed. This records the END STATE only.)

## Goal

The Cayley graph is the organizing metaphor of the whole course (nodes =
coordinate spaces, directed edges = invertible functions; to go between spaces
you trace a path, `compose` the edge functions, and `inverse` any edge walked
against its arrow — the ch02 rule). It existed only implicitly: as the order of
`compose([...])` calls and `push/pop` nesting. This work made it an explicit,
animatable data structure and rebuilt all seven `mvpVisualization/` demos on it.

**Scope: `mvpVisualization/` only** (plus the one enabling change in
`src/modelviewprojection/mathutils.py`). The book demos under `src/.../demoNN`
and `book/docs` were not touched.

## What exists now

### 1. Interpolable `InvertibleFunction` (`src/modelviewprojection/mathutils.py`)
- Optional `interpolate` law + `components` list on `InvertibleFunction`; `at(t)`
  returns the partially-applied function (identity at t=0, full at t=1), and
  `steps()` flattens a composite to its leaf primitives.
- Resolution order in `at`: the primitive's own law → recurse into `components`
  (set by `compose`) → step default. `inverse` propagates so it **commutes** with
  `at` (`inverse(f).at(t) == inverse(f.at(t))`), which is what lets an
  against-the-arrow composite edge (world→camera) animate smoothly.
- Laws on translate / rotate(_x/_y/_z) / uniform_scale / scale_non_uniform.
  Scale law is **linear** `1+(m-1)t` (matches the GLSL squash exactly).
- Backward compatible; the book demos still pass.

### 2. The graph + scene engine (`mvpVisualization/`)
- **`cayleygraph.py`** — immutable, acyclic, all-at-once: `CayleyGraph([Edge,...])`
  (no `add_edge`; constructor 3-colour-DFS rejects cycles). `Edge(src, dst, steps)`
  (frozen; node ids are per-demo `Space(Enum)` members). `path(a,b)` BFS-routes and
  auto-inverts edges walked backward; `Path.function()` / `.oriented_steps()`.
- **`cayleyscene.py`** — the animation script + derivations (pure data/math, headless):
  `CoordinateFrame` (a node placed in the scene + its geometry + dwell),
  `InverseOperations` (the world→camera "unwind", an affine inverse edge),
  `NonInvertibleTransformation` (the projective squash — see decision below),
  `Scene`, `Timeline` (assigns start/dur incl. dwells), `Animation` (live
  transforms, reveal lifecycle, the two imgui-tree data structures),
  `CameraControls` (edit a camera edge's Step.fn in place), and `to_matrix(f)`
  (affine `InvertibleFunction` → 4×4 for GL upload).
- **`cayley_gl.py`** — generic GL toolkit, **mechanism only**: window/imgui setup,
  orbit + flat-2D views, `StandardObjects` (standard pipelines + paddle/square/
  ground/axis/cube meshes + `draw_*`), `Frustum` / `RectangularPrism` view volumes,
  the menubar/window helpers, and `run_loop`. It owns no per-demo policy.

### 3. The seven demos (`mvpVisualization/<name>/<name>.py`)
These ARE the demos now (the Cayley versions replaced the pre-Cayley originals).
Each declares its `Space` enum + graph + scene and owns its own draw choreography,
imgui menubar, and reveal decisions; `cayley_gl` supplies the mechanisms.
- `model`, `pushmatrix` — object placement, static perspective, one tree.
- `modelview` — adds the world→camera unwind; full 3.3-core shader convert.
- `modelviewperspectiveprojection` — the full demo: camera-as-object with its
  perspective **frustum**, the GPU squash, both trees, editable virtual camera,
  frustum sliders, focus.
- `modelvieworthoprojection` — orthographic: a **rectangular-prism** view volume,
  ortho squash.
- `modelview2d` — flat 2D orthographic (head-on, no orbit; NDC checkbox zooms the
  ortho extent). Per-frame *graph paper* (each frame's local grid) and a flat ±10
  view volume that the ×1/10 squash scales onto the ±1 NDC square.
- `coordinatesystems` — the no-timeline interactive explorer: live slider params,
  focus buttons re-anchor the view by walking `path(world, space)`.

### 4. UI: controls in a menubar with keyboard shortcuts
Each demo's controls live in a top menubar (File / Playback / Camera / View From /
View / Scene as applicable), SuperBible-ports style: sliders/checkboxes inside
menus, `menu_action` for toggles/actions/radio (with shortcut hints + checkmarks).
The two function-composition trees live in a floating "Cayley Graph" panel toggled
by **View → Show Graph**. Keyboard: **Esc** quit, **F11** fullscreen (all);
**SPACE** pause, **R** restart, **G** graph (animated); **WASD** camera move
(perspective/ortho/2d); **N** NDC zoom (2d).

### 5. Demos use `pyMatrixStack` directly
No thin wrappers in the toolkit for matrix ops: callers use
`ms.set_to_identity_matrix` / `ms.set_current_matrix` / `ms.multiply` and GL calls
inline. (`_p.set_uniforms` already coerces to contiguous float32 at upload, so no
caller-side coercion is needed.)

## Decisions worth keeping

- **Interpolation lives on `InvertibleFunction`** (optional law); composites recurse
  via `components`/`steps()`, not a stored closure.
- **Scale interpolation is linear** `1+(m-1)t` — matches the shaders so the rewrite
  is pixel-identical and parity-testable.
- **The perspective/ortho squash stays a GPU shader step**, not an affine
  `InvertibleFunction` (it's projective). It's modelled as
  `NonInvertibleTransformation` and realized via the shader `time` uniform. This is
  the one documented seam in the "everything is an edge" abstraction.
- **Pauses are dwell annotations on nodes**, realized as `identity()` for D seconds
  (no nonsense self-loop edges in the graph).
- **Camera placement == object placement**: declare the camera edge once
  (camera→world); the world→camera "unwind" walks it backward → inverse. One graph
  generates the animation AND both imgui trees with no duplication — exactly the
  pedagogical hinge.
- **`Frustum` is perspective-only** (a truncated pyramid); the orthographic box is a
  separate **`RectangularPrism`**. "The ortho is not a frustum."

## Verification
85 headless tests pass (engine math/graph/scene), ruff clean. All seven demos
visually confirmed good by Bill (they need a display; the headless container can't
run GL). A headless old-vs-new numeric parity harness was scoped but deemed
optional and not built.
