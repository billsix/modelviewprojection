# mvpVisualization shared-shader refactor

**Status:** in progress (started 2026-05-27)

## Goal

Eliminate the heavy copy-paste across the `mvpVisualization/*/` shader files by
promoting the genuinely shared shaders to the **top of `mvpVisualization/`** and
parametrizing the rest. Approved by Bill ("everything you suggest is fine, just
put the shared ones at the top of the mvpViz directory").

## Key finding driving the design

Shaders were named after the *object drawn* (triangle/ground/axis/cube/frustum),
but their real identity is **(color source) × (animated `project()`?)**:

- color source: per-vertex attr `color_in`, `uniform vec3 color`, or a hardcoded
  constant (gray ground / white cube+frustum)
- `project()`: identity (static) or a per-demo animated body

`project()` was byte-identical across triangle/axis/frustum within ortho, and
triangle==frustum within perspective. Perspective `axis.vert` had a **bug**
(used `max(1.0,…)` and never applied the interpolation ratios → axes snapped
instead of animating); unifying `project()` fixes it.

## End-state shader set (all at `mvpVisualization/` top level)

Vertex (2):
- `per_vertex_color.vert` — color from `color_in`; forward-declares
  `vec4 project(vec4)`, calls it in main.
- `uniform_color.vert` — color from `uniform vec3 color`; same project hook.

project() snippets (4), appended to the `.vert` at compile time:
- `project_identity.glsl` — `return cameraSpace;`
- `project_modelview2d.glsl`
- `project_ortho.glsl`
- `project_perspective.glsl`

Fragment / geometry (3):
- `passthrough.frag` — was `triangle.frag` (used by every non-geom pipeline)
- `passthrough_geom.frag` — was `frustum.frag` (reads `fColor`)
- `thick_lines.geom` — was `frustum.geom`

## `_pipeline.py` changes

- `_SHARED_DIR = dirname(abspath(__file__))`; shaders load from there (demos no
  longer carry shaders, so `compile_program`/`build_pipeline` drop the `pwd` arg).
- `compile_program(vert, frag, geom=None, project=None)` — if `project` given,
  append that snippet's source to the vertex source before compiling (GLSL 330
  has no `#include`; forward declaration in the `.vert` makes this valid).
- `build_pipeline(vert, frag, *, color, per_vertex_color, anim, screenspace,
  geom, project="project_identity.glsl")`.

## Per-pipeline mapping (vert / frag / project / color)

| demo | pipeline | vert | frag | project | color set to |
|---|---|---|---|---|---|
| coord/model/pushmatrix | triangle | per_vertex | passthrough | identity | (per-vertex) |
| " | ground | uniform | passthrough | identity | 0.1,0.1,0.1 |
| " | axis | uniform | passthrough | identity | per-axis |
| " | cube | uniform | passthrough | identity | 1,1,1 |
| modelview2d | triangle | per_vertex | passthrough | modelview2d | (pv) |
| " | ground | uniform | passthrough | identity | gray |
| " | axis | uniform | passthrough | modelview2d | per-axis |
| " | cube | uniform | passthrough | modelview2d | white |
| ortho | triangle | per_vertex | passthrough | ortho | (pv) |
| " | ground | uniform | passthrough | identity | gray |
| " | axis | uniform | passthrough | ortho | per-axis |
| " | cube | uniform | passthrough | identity | white |
| " | frustum | uniform | passthrough | ortho | white |
| perspective | triangle | per_vertex | passthrough | perspective | (pv) |
| " | ground | uniform | passthrough | identity | gray |
| " | axis | uniform | passthrough | perspective | per-axis (BUG FIX) |
| " | cube | uniform | passthrough | identity | white |
| " | frustum | uniform | passthrough_geom + thick_lines.geom | perspective | white |

`ground`/`cube`/`frustum` previously hardcoded their color in the shader; now they
set the `color` uniform in their `draw_*` (like `axis` already does). ground needs
gray added in all 6 draw_ground; ortho/persp draw_cube + all draw_frustum need
white added.

## Verification

- py_compile + pytest after each stage (done per stage).
- **GLSL compile + visual render is NOT verifiable in-container** (no GL/display).
  Bill must run each of the 6 demos on a display to confirm.

## Progress

- [x] create 9 shared shaders at top level (2 vert, 4 project snippets, 2 frag,
      1 geom)
- [x] refactor `_pipeline.py` (`_SHARED_DIR`, `compile_program(vert, frag,
      geom, project)` with snippet concatenation, `build_pipeline` drops `pwd`,
      adds `project=`)
- [x] rewrite 6 demos (pipeline calls + gray in draw_ground, white in
      ortho/persp draw_cube + draw_frustum)
- [x] delete 30 per-demo shaders
- [x] py_compile (7/7) + pytest (47/47); GLSL splice structurally verified
      (1 #version, fwd-decl + 1 defn, version first) for all 8 vert×project
      combos. **Staged — awaiting commit + Bill's on-display GL verification.**

## Notes for GL verification (what to eyeball per demo)

- ground renders dark gray (not black -> means u_color got set), cube/frustum
  white. paddles/square keep per-vertex colours; axes R/G/B.
- ortho + perspective: axes stay put through the projection animation (time is
  intentionally never uploaded to the axis program -- preserved), while
  paddles/square/frustum animate.
- perspective frustum: thick constant-width lines via thick_lines.geom; back
  edges stay visible under squash.
