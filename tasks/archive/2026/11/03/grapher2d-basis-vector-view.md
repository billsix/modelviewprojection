# 2D grapher — origin + e₁/e₂ basis-vector reference view — DONE

**Status:** done (2026-11-03) — implemented and headless-verified (the BASIS render shows the
white origin dot + red e₁ / green e₂ arrows). On-display interaction is the maintainer's pass.
**Completed:** 2026-11-03 (William Emerison Six <billsix@gmail.com>, with Claude Opus 4.8)
**Part of:** the graphing-calculator work — base graphers under
`src/modelviewprojection/graphingcalculator/`
(`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).

## What was built

`grapher2d.py` gained a third **backdrop** behind the plotted curves, selectable from the Controls
menu and cycled by `G`:

- `View2D.show_grid` (a bool) became `View2D.backdrop`, a **`Backdrop` enum** — `GRID` (grid +
  axes + ticks, default), `AXES` (axes + ticks only), `BASIS` (the reference frame).
- **BASIS** draws the origin as a **white filled dot** (triangle fan) and e₁/e₂ as unit-vector
  **arrows** — e₁ red along +x, e₂ green along +y — mirroring the 3D `cayley_gl.draw_axis`
  colour/convention the request pointed at. Flat line shaft + a filled triangular head, plus the
  dot, all drawn through grapher2d's own uniform-colour `line_pipeline` (path B, below). The dot is
  drawn first so it stays on top at the origin where the shafts begin.
- All basis geometry is in **plot units** (unit-length arrows, proportional head, fixed-fraction
  dot), built once, so it scales with zoom like the grid. It is drawn as the backdrop — before the
  depth clear — so the curves always draw over it (same z-fighting rule as the base task,
  `tasks/reference/gl-and-imgui-gotchas.md` §8).

## Decisions (as built; alternatives were logged in the proposal)

1. **Mutually-exclusive 3-way backdrop** (grid | axes+ticks | basis), grid default, `G` cycles —
   over independent toggles.
2. **Geometry in plot units** (scales with zoom), mirroring the 3D `draw_axis`, over
   constant-screen-size arrows. Static mesh, no per-frame rescale.
3. **Bare** in basis mode — origin dot + e₁/e₂ only, no faint axes behind.
4. **No text labels** — deferred to `tasks/graphing-calculator-latex-labels.md`.
5. **Path B** — flat line+triangle arrows in grapher2d's own pipeline — over reusing the 3D
   cylinder+cone solids.
6. **`Backdrop` uses `enum.auto()`** (maintainer feedback mid-build): the member values carry no
   meaning, so `cycle_backdrop()` cycles via `list(Backdrop).index(...)`, never `.value`. This drove
   a new cross-project rule — "default to `enum.auto()` unless a value has an articulated external
   reason" — added to the shared Python coding standard (`python-coding-standard.md`, canonical in
   `github.com/billsix/runClaudeInContainer`, mirrored in `github.com/billsix/runCrushInContainer`).

## Verification

ruff-clean (80-col), ty-clean, annotation-checker clean (containerized gate, GATE_STATUS=0).
Rendered headless via `tools/verify_render.sh`: the default GRID backdrop is unchanged, and a
temporary BASIS default confirmed the white origin dot + red e₁ (→+x) / green e₂ (→+y) arrows with
the curves drawn over them. On-display interaction (cycling with `G`, the menu) is the maintainer's
pass.
