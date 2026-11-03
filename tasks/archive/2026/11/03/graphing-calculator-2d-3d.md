# Graphing-calculator programs (2D and 3D) — DONE

**Status:** done (2026-11-03) — implemented and headless-verified. On-display visual/interaction
verification remains the maintainer's, per the repo's "Bill verifies anything requiring a display"
convention (not a blocker; the headless render is real evidence here because the graphers take
`imgui` via `cayley_gl` with `glfw` imported first, so the bundled-glfw import-order gotcha that
usually makes a headless sweep untrustworthy does not apply).
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Completed:** 2026-11-03 (William Emerison Six <billsix@gmail.com>, with Claude Opus 4.8)
**Follow-on (still open):** `tasks/graphing-calculator-3d-lit-mesh.md` — the triangle-mesh,
Blinn-Phong-lit (half-angle specular) version of the 3D surface, modelled on the v4 port.

## What was built

Two standalone, run-by-path programs under
**`src/modelviewprojection/graphingcalculator/`** that plot first-class Python functions the way a
graphing calculator does. Functions are authored in each program's source (no runtime equation
parser); the imgui menubar sets only the view. Both are GL 3.3 core, shader-based.

- **`grapher2d.py`** — plots a list of `f(x)` callables (sin, cos, a parabola, a cubic) over
  pannable/zoomable axes with tick marks and a grid. Controls menu: x/y center (pan), y
  half-height (zoom), tick/grid spacing; arrows pan, `-`/`=` zoom, `G` toggles the grid, `F11`
  fullscreen. The plot→NDC view is the course's **ortho edge** (`matrix_stack.ortho`).
- **`grapher3d.py`** — plots an `f(x,y)` height field (domain x→world x, y→world z, value→up/y) as
  a **wireframe mesh by default**, with a height-shaded solid as an opt-in toggle. Surface menu picks the function (saddle,
  paraboloid, ripple, waves); Controls menu sets the grid steps **dx** and **dy** (live rebuild)
  and toggles wireframe/solid; an orbit camera (left-drag / arrows / scroll) looks around it.
  Perspective via `cayley_gl.setup_orbit_view` (`matrix_stack.perspective`). Lighting was kept out
  of scope — it is the follow-on task.

## Design decisions (as built)

1. **Standalone programs**, not an edit of the book-published `assignments/assignment1.py` (which
   has the original immediate-mode GL 1.4 `f(x)` plotter). The assignment was left untouched; the
   graphers borrowed the *idea* of sampling a callable, not its GL style.
2. **Two separate programs** (2D, 3D), not one app with a mode toggle.
3. **Functions authored in source** as first-class callables; the only runtime UI is the view
   (pan/zoom/axes/ticks in 2D, dx/dy/surface/draw-mode in 3D), all via the imgui menubar.
4. **GL 3.3 core, shader-based.**
5. **Reused the shared course infra, not a private copy.** Only the `ports/` subtree is off-limits
   to import (it is supplemental). The graphers build on `mvpvisualization.cayley_gl` (window +
   imgui + GL context, orbit camera, menubar helpers `menu_action`/`toggle_fullscreen`/`WindowState`/
   `common_key`, `run_loop`) and `_pipeline` (the uniform-colour line pipeline + the
   per-vertex-colour pipeline for the height-shaded solid, the shared `uniform_color.vert` /
   `per_vertex_color.vert` / `passthrough.frag` shaders, and the VAO/VBO builders), with the view
   from `matrix_stack`. No grapher-specific shaders. Each grapher is ONE self-contained program
   file (the house style for demos/ports). The menubar follows the same convention the v4 port
   uses, so CLAUDE.md's GL/imgui section notes the reuse (and that only `ports/` is off-limits).

## gacalc (geometricalgebra) — no release needed for the half-vector/half-angle follow-on

Checked `github.com/billsix/geometricalgebra` for the lit follow-on's half-vector question.
**No new gacalc release is required.** Everything the Blinn-Phong math needs ships in the
**released** API (predates tag `v0.0.20`): `Vector.__add__`, `.normalize()`, `.magnitude()`,
`.scalar_product()` (the N·L dot), plus `rotor_from_vectors` / `transforms.rotor_for` for the
GA-rotor framing. The half vector `H = normalize(L + V)` and specular
`scalar_product(N, H) ** shininess` build from those — and in fact `H` lives in the GLSL fragment
shader on the GPU, so gacalc is not in that runtime path at all (it is CPU-side only, for the MVP
transforms and optionally mesh normals). gacalc separately has an `[Unreleased]` section with
accumulated additive features (pyproject already at 0.1.0), release-worthy on its own schedule but
not forced by this work. Terminology caveat carried into the follow-on: Blinn's half *vector*
(bisector of L and V) is not the GA rotor half-*angle* `cos(θ/2) + I sin(θ/2)`.

## Review fixes (2026-11-03, maintainer review before merge)

Two defects surfaced in the on-display review and were fixed on the same branch:

1. **2D curve "holes" at the sin/cos peaks.** Drawing each curve as one fixed set of 4000
   `GL_LINE_STRIP` vertices over `[-50, 50]` left sub-pixel segments where the curve runs
   near-horizontal (the extrema); GL's diamond-exit rasterisation drops those, so the curve looked
   dashed at every peak/trough. Fixed by (a) enabling `GL_LINE_SMOOTH` + alpha blending and
   (b) **resampling each curve to the visible x-window, one point per pixel column, whenever the
   view moves** — segments stay ~1px at every zoom, so the polyline is smooth zoomed in and gapless
   zoomed out (a fixed sample set over a fixed range cannot be both). Verified at the default view
   and held zoom-out.
2. **3D started as a solid surface, not a wireframe.** The agreed starting point was a bare
   wireframe mesh. `View3D.show_solid` now defaults to `False` (wireframe-only on launch); the
   height-shaded solid stays available via the Controls menu / `S`.

## Verification

Both programs: ruff-clean (line-length 80), ty-clean (modulo the host-only `glfw`
`_GLFWwindowPointerT` stub diagnostic that `mvpvisualization/modelview.py` also shows — the
container gate resolves it), and the local/module annotation checker clean. Rendered headless via
`tools/verify_render.sh` (12 frames, Xvfb `:99`): grapher2d drew all four curves in their exact
colours over the grid; grapher3d drew the saddle `x*y/4` as the expected hyperbolic paraboloid
(height-shaded solid + wireframe + 3D axes/ticks). The maintainer's on-display pass (pan/zoom,
menubar interaction, Wayland) is the remaining check.
