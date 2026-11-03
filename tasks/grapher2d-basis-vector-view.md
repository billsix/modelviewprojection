# 2D grapher — origin + e₁/e₂ basis-vector reference view

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 3
**Started:** 2026-11-03 (William Emerison Six <billsix@gmail.com>)
**Part of:** the graphing-calculator work — base graphers at
`src/modelviewprojection/graphingcalculator/` (done + merged;
`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).
**Related:** `tasks/graphing-calculator-latex-labels.md` — if that lands, the e₁/e₂ arrows can
carry rendered LaTeX labels.

## BLUF

Add a reference-frame display mode to `grapher2d.py` that draws the **origin as a white circle**
and the **basis vectors e₁ and e₂ as arrows** (e₁ red, e₂ green), as an alternative to the current
grid / axes-with-ticks backdrop. "Done" = the Controls menu can switch the plot's backdrop to the
origin-dot + e₁/e₂ arrows, mirroring the colour convention the 3D visualizations already use.

## Context (read first)

- `grapher2d.py` today: `View2D.show_grid` toggles the grid (key `G`); the x/y axes + tick marks
  are always drawn. It rolls its OWN flat line pipeline (`line_pipeline` = `uniform_color.vert` +
  `passthrough.frag`, position-only VAOs) and flat numpy mesh builders (`build_grid`,
  `build_axes_and_ticks`), drawn through `apply_ortho_view` (an ortho edge on the matrix stack).
  `draw_lines(vao, count, color, mode)` already takes a draw mode, so the same pipeline draws
  `GL_TRIANGLES` (filled heads/dot), not just `GL_LINES`.
- The course's basis-vector + origin convention is `cayley_gl.StandardObjects.draw_axis`
  (`cayley_gl.py:282-305`): **e₁/X = red** (base mesh rotated `rotate_z(-90°)`), **e₂/Y = green**
  (un-rotated +Y mesh), e₃/Z = blue, **origin = white sphere**. Arrow mesh is
  `_pipeline.build_axis_arrow_solid` (a +Y cylinder shaft + cone tip); origin is
  `_pipeline.build_origin_sphere_solid`.
- **Proven precedent:** `modelview2d.py:365` already calls `draw_axis()` under a head-on **ortho
  2D** view (`cayley_gl.setup_ortho_2d_view`). e₁ and e₂ lie in the view plane and read as arrows,
  the sphere reads as a white dot; e₃ (blue) foreshortens to a blob head-on, so a 2D basis view
  drops it. This is exactly the look the task wants.

## Decision: how to draw the 2D arrows (recommend B)

- **(A) Reuse the 3D solids.** Stand up the `axis_pipeline` + `build_axis_arrow_solid` /
  `build_origin_sphere_solid` VAOs (as `cayley_gl.build_standard` does) and emit only e₁, e₂, and
  the sphere. Matches the 3D visualizations pixel-for-pixel; but `draw_axis` always emits all three
  arrows + sphere, so it needs a trimmed variant, and the unit-length (1.0) arrow must be scaled up
  via the model matrix to show in the grapher's wide ortho window (`PLOT_HALF_RANGE = 50`,
  default `half_height = 8`).
- **(B) Flat 2D arrow in grapher2d's own pipeline (recommended).** A line shaft + a flat 3-vertex
  `GL_TRIANGLES` arrowhead coloured via the existing `line_pipeline`, plus a small filled circle
  (triangle fan) for the origin. Fits grapher2d's established flat-mesh style with the least new
  machinery and sidesteps the 3D-solid trim/scale issues. Colours still mirror the convention:
  e₁ red, e₂ green, origin white.

## Plan (draft — path B)

- [ ] A reference-frame **mode** on `View2D` (replace/extend `show_grid`): grid | axes+ticks |
      basis-vectors (see open question 1). Default stays grid.
- [ ] `build_basis_arrow(color, +x|+y)` → a shaft + a filled triangular head (`GL_TRIANGLES`),
      shaft length 1.0 in plot units, pointing along +x (e₁) / +y (e₂).
- [ ] `build_origin_dot()` → a small filled circle (triangle fan), white.
- [ ] Draw them in `frame()` when the mode is basis-vectors, **after the depth-clear** (same
      z-fighting rule as the curves — `tasks/reference/gl-and-imgui-gotchas.md` §8), through
      `apply_ortho_view`.
- [ ] Controls-menu entry to pick the mode; a key to cycle it (extend `G`).
- [ ] Headless-verify via `tools/verify_render.sh` (origin dot white, e₁ red along +x, e₂ green
      along +y).

## Decisions (batch go-ahead 2026-11-03, William Emerison Six <billsix@gmail.com>)

Options are logged under "Open questions" below; chosen for this pass:
1. **Mutually-exclusive 3-way backdrop mode** (grid | axes+ticks | basis), grid default, cycled
   by `G`.
2. **All geometry in world units**, mirroring the 3D `draw_axis` the request points at: unit-length
   arrows with a proportional triangular head, origin a small fixed-fraction dot — everything
   scales with zoom like the grid, and the mesh is static (no per-frame rescale). This refines the
   doc's earlier constant-screen-size lean; the 3D convention is the better model. Constant-screen
   sizing (open question 2) is logged as the alternative.
3. **Bare** in basis mode — origin dot + e₁/e₂ arrows only, no faint axes behind.
4. **No text labels** here; deferred to `tasks/graphing-calculator-latex-labels.md`.
5. Draw via **path B** (flat line+triangle arrow in grapher2d's own `line_pipeline`), per the
   "Decision" section above.

## Open questions

1. **Mode model.** Make the backdrop a 3-way **mutually-exclusive mode** (grid | axes+ticks |
   basis-vectors) — matching the "instead of" phrasing — or independent toggles so basis arrows can
   overlay the grid? Recommendation: a mode enum, grid as default, cycled by `G`.
2. **Arrow/dot sizing.** e₁/e₂ are unit vectors, so the shafts should be **length 1 in plot units**
   (they track the grid as you zoom). Should the arrowhead and origin dot also scale with zoom, or
   stay a constant screen size (a few px) like a calculator cursor? Recommendation: shaft = 1 plot
   unit (scales), head + dot a constant screen size.
3. **Keep axes/ticks under the basis view?** When showing basis vectors, also draw the faint
   axes+ticks behind them, or just the origin dot + two arrows on the bare background?
   Recommendation: bare — the arrows ARE the axes in this mode.
4. **Labels.** Draw `e₁`/`e₂` text labels next to the arrows? That depends on
   `tasks/graphing-calculator-latex-labels.md`; leave labels out of THIS task and let the labels
   task add them. OK?
