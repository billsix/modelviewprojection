# Graphing-calculator programs (2D and 3D), building on the assignment function viewer

**Status:** proposed — **design complete, ready to implement on go-ahead** (all open questions resolved)
**Priority:** 6
**Difficulty:** 5
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Design answered:** 2026-11-03 (William Emerison Six <billsix@gmail.com>) — all open questions
(both the original five and the second round: location/naming, book-published, GL version, menubar
infra) are resolved under "Decisions" below. No open questions remain; awaiting the go-ahead to code.
**Follow-on:** `tasks/graphing-calculator-3d-lit-mesh.md` — the triangle-mesh, Blinn-Phong-lit
version of the 3D plotter (half-angle specular, modelled on the v4 port).

## BLUF

Build **two separate standalone programs** — a 2D `f(x)` grapher and a 3D `f(x,y)` surface
grapher — that feel like a familiar graphing calculator (axes, tick marks, zoom, pan). Functions
are **first-class Python callables written into the program source** (no runtime equation
parser); the only runtime UI is an **imgui menubar** for view settings (zoom/pan ranges, tick
spacing; and dx/dy grid resolution in 3D). Both are **shader-based** (modern core-profile GL),
not the immediate-mode GL 1.4 of `assignment1.py`. "Done" = both programs run, plot a small set
of authored functions correctly, and expose their view controls in the menubar. The lit/triangle
3D surface is explicitly **out of scope here** and lives in the follow-on task.

## Decisions (2026-11-03 — answers to the original Open questions)

1. **Standalone, not an edit of the assignment.** Two brand-new programs, free to borrow from
   `assignments/assignment1.py` as much as useful, but it is left alone (it is book-published as
   `programmingproj1.rst` — see Context — so we don't disturb it). Should **feel familiar to a
   graphing-calculator user**, and be **driven by Python functions, not by any GUI
   function-entry** — no equation textbox/parser.
2. **Two separate programs** — one 2D, one 3D. Not a single app with a mode toggle.
3. **No runtime function interactivity.** Functions are chosen at *authoring* time, as
   **first-class functions** in the source (a list of `Callable`s). Runtime UI is view-only:
   **zoom, pan, axes, and tick marks**, with **imgui controls in a menubar** to set them.
4. **Shader-based** modern GL (not fixed-function / GL 1.4).
5. **3D: start with wireframe and mesh**, with **dx and dy (grid sampling steps) configurable in
   the menubar**. A **follow-on task** covers rebuilding the surface out of **triangles with
   Blinn-Phong shading** (the half-angle / halfway-vector model) — see Follow-on below.

## Context (investigation 2026-08-27) — the 2D viewer already exists in the assignments

- **The 2D OpenGL math-function viewer is `assignments/assignment1.py`.** It already has a real
  arbitrary-function plotter: `plot(fn, domain, interval)` (def at `assignments/assignment1.py:146`;
  it samples via `np.arange` and draws `GL_LINES`), plus a hand-precomputed `f(x)=x²` version and a
  polar/parametric loop. Immediate-mode GL, context hinted **1.4**
  (`assignments/assignment1.py:36-37`). We **borrow its plotting idea**, not its GL style (we go
  shader-based per decision #4).
- It is **book-published**: `assignment1.py → programmingproj1.rst`
  (`tasks/reference/demo-chapter-inventory.md:119`, `book-and-docs-pipeline.md:79`). Because we
  build standalone (decision #1), we don't edit it and don't perturb the book.
- No 3D plotting exists anywhere in mvp yet — the 3D `f(x,y)` surface is net-new. Superseded task
  slug: `math-plotting-2d-and-3d.md`.

## Plan (draft — unblocks once the remaining Open questions are answered)

### 2D grapher — `f(x)`
- [ ] New standalone shader-based program. Authored input: a list of first-class functions to
      plot, each `Callable[[float], float]` with a label + colour (e.g. a small frozen list /
      dataclass table at module top).
- [ ] Render: axes, tick marks (labelled), a grid, and each function sampled over the current
      x-domain drawn as a line strip (VBO + a simple 2D shader; one draw per function).
- [ ] View model: zoom + pan (keyboard/mouse), with the current x-range / y-range and tick
      spacing also settable from the menubar. Pan/zoom just moves the orthographic view.
- [ ] Transforms via gacalc per house architecture (ortho view as an `InvertibleFunction`;
      realize to a matrix with `cayleyscene.to_matrix` only for the GL uniform) unless the GL
      version question (Q3 below) pushes us elsewhere — confirm in review.
- [ ] Menubar: a Controls menu for view settings + F11 fullscreen (match the v4 port convention —
      pending Q4 on whether to reuse `_common.draw_view_menu`).

### 3D grapher — `f(x,y)` surface (wireframe + mesh)
- [ ] New standalone shader-based program. Authored input: a list of `Callable[[float, float],
      float]` surfaces, each with a domain over (x, y).
- [ ] Build a height-field mesh over the domain sampled at **dx × dy** steps; draw as **wireframe
      and/or mesh** (`GL_LINES` / `GL_TRIANGLES`-as-wireframe, no lighting yet — flat/by-height
      colour).
- [ ] 3D axes + tick marks; an orbit/zoom/pan camera.
- [ ] Menubar: **dx and dy** (grid resolution) configurable live, plus the view/zoom/pan/tick
      controls and F11 fullscreen.
- [ ] Rebuild the mesh when dx/dy change.

## Follow-on (own task) — lit triangle-mesh 3D surface

`tasks/graphing-calculator-3d-lit-mesh.md`: take the 3D grapher's height field and render it as a
**solid triangle mesh with Blinn-Phong lighting** (the half-angle / halfway-vector specular model,
as opposed to Phong's reflection-vector model). Compute per-vertex (or per-face) **normals** from
the height field, add a light, and shade. **Inspiration: the openglsuperbible v4 port** —
`ports/openglsuperbiblev4/chapt16/vertexshaders/shaders/specular.vs` (per-vertex half-vector
`H = normalize(L + normalize(-V.xyz))`) and `chapt17/lighting/shaders/specular.{vs,fs}` (the
per-fragment version). That is exactly "whichever one does the half angles" — Blinn-Phong.

## Decisions — round 2 (2026-11-03, answers to the second-round questions)

1. **Location / naming: `src/modelviewprojection/graphingcalculator/`** with **`grapher2d.py`** +
   **`grapher3d.py`** — part of the installed package, run by path like the `mvpvisualization/`
   aids.
2. **Just programs for now** — no book chapters. Do **not** add `literalinclude` doc-region markers;
   these are standalone programs with no book prose yet. (A book write-up can be a later task.)
3. **GL 3.3 core profile** — matches the code-the-classics ports.
4. **Self-contained imgui menubar helper, mvp's own copy.** Do **not** import
   `ports/openglsuperbiblev4/_common`; the grapher carries its own small menubar helper (Controls
   menu for view settings, F11 fullscreen) inside `graphingcalculator/`, keeping it independent of
   the `ports/` subtree. It **must use imgui** for these controls. Because it is a deliberate copy
   of the same convention the v4 port implements in `_common.draw_view_menu`, the two can drift —
   mvp `CLAUDE.md` carries a drift-watch note so a future session reconciles them on purpose.
5. **Yes — gacalc for the transforms.** Ortho (2D) / camera (3D) are `InvertibleFunction`s;
   realize to a 4×4 with `cayleyscene.to_matrix` only at the GL uniform upload. No hand-built
   projection matrices.

## gacalc (geometricalgebra) — no release needed for this work (verified 2026-11-03)

Checked `github.com/billsix/geometricalgebra` (gacalc) for the half-vector / half-angle question
(raised for the lit follow-on). **No new gacalc release is required.** Everything the lighting math
needs is in the **released** API (predates tag `v0.0.20`): `Vector.__add__`, `.normalize()`,
`.magnitude()`, `.scalar_product()` (the N·L dot), plus `rotor_from_vectors` / `plane_rotation` /
`transforms.rotor_for` if we ever want the GA-rotor framing. The Blinn-Phong **half vector**
`H = normalize(L + V)` and specular `scalar_product(N, H) ** shininess` are built from those — and
in fact H is computed in the **GLSL fragment shader on the GPU**, so gacalc isn't even in that
runtime path; gacalc is used CPU-side only for the MVP transforms (decision #5) and optionally
mesh normals, all already supported. Full detail + the terminology caveat (Blinn's half *vector* ≠
the GA rotor half-*angle* `cos(θ/2)+I sin(θ/2)`) is in the follow-on task.
