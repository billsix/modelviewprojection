# Graphing-calculator programs (2D and 3D), building on the assignment function viewer

**Status:** proposed — needs go-ahead (design decided; a few open questions remain below)
**Priority:** 6
**Difficulty:** 5
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Design answered:** 2026-11-03 (William Emerison Six <billsix@gmail.com>) — the five original
open questions are now resolved under "Decisions" below; new open questions (location/naming,
book-published, GL version, menubar infra reuse) are at the bottom and still block coding.
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

## Open questions (new — these block coding)

1. **Where do the two programs live, and what are they named?** Options: a new top-level
   `graphingcalculator/` dir (sibling of `assignments/`, `ports/`); under the installed package at
   `src/modelviewprojection/graphingcalculator/` (run by path, like `mvpvisualization/`); or inside
   `assignments/` as new standalone scripts. Recommendation: **`src/modelviewprojection/graphingcalculator/`**
   with `grapher2d.py` + `grapher3d.py`, so they're part of the installed package and runnable by
   path like the existing `mvpvisualization/` aids — but your call.
2. **Are these book chapters, or just programs?** The repo *is* the textbook. Do you want these
   written up as book chapters (new `book/docs/chNN.rst` with `literalinclude` doc-regions), or
   kept as standalone programs with no book prose for now? (This decides whether I add
   doc-region markers as I write.)
3. **Which GL version / profile?** The modern demos / code-the-classics ports target **GL 3.3
   core**; some SuperBible ports go to 4.x. Recommendation: **3.3 core** (simplest modern baseline,
   matches code-the-classics). OK?
4. **Reuse the v4 menubar infra, or build fresh?** The v4 port has `_common.draw_view_menu` + the
   "Controls menu, never a floating window; F11 toggles fullscreen" convention
   (`tasks/reference/gl-and-imgui-gotchas.md`). These aren't v4 ports, so do you want them to
   **import and reuse `ports/openglsuperbiblev4/_common`**, or carry a small self-contained menubar
   helper of their own (no cross-import into the ports tree)? Recommendation: **self-contained** —
   keep the grapher independent of the ports subtree.
5. **gacalc for the transforms?** House rule says express transforms with gacalc and realize to a
   matrix only at upload. Confirm you want the graphers to follow that (ortho/camera as
   `InvertibleFunction`s via `cayleyscene.to_matrix`), rather than hand-built projection matrices —
   I'll default to **yes** unless you'd rather keep these two outside the Cayley-graph pedagogy.
