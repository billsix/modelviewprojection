# Investigate: rewrite the book's matplotlib-plot transforms to use gacalc

**Status:** investigating (2026-08-03) — deliverable is a feasibility opinion
**Priority:** 4
**Difficulty:** 5

## Goal

Bill made a **custom composable-transformation library for the book's matplotlib plots
*before* gacalc existed**. Now that `mathutils.py` is a gacalc façade and gacalc provides
`InvertibleFunction` / `translate` / `rotate` / `plane_rotation` / compose, investigate whether
the plot code can be rewritten to use gacalc instead of the bespoke transforms — and **tell Bill
whether it's feasible** (not necessarily do it yet).

## Where the code is (found 2026-08-03)

- `src/modelviewprojection/plotsforbook/plotutils/mpltransformations.py` — **the prime suspect**:
  the custom "composable transformations" for plotting.
- `src/modelviewprojection/plotsforbook/plotutils/matplotgraphs.py`
- `src/modelviewprojection/plotsforbook/generate_plots.py`
- `src/modelviewprojection/util/nbplotutils.py` (notebook plot helpers)
- `src/modelviewprojection/notebooksrc/ndc.py`

## What to determine (the feasibility questions)

1. What does `mpltransformations.py` actually provide — the transform primitives, their
   compose/inverse model, and the value type they operate on (2D points? numpy arrays?).
2. Does gacalc's transform layer cover those operations (translate/scale/rotate/compose/inverse
   on `Vector2`)? Where are the gaps (e.g. matplotlib wants `(x,y)` arrays; gacalc uses
   `Vector2` — is the `*v` unpacking / `_to_xy` bridge enough)?
3. Would the rewrite preserve the *rendered output* (the plots must look the same — verify by
   diffing generated PNGs before/after, per the "derive the before mechanically" rule)?
4. Pedagogical fit: mvp already teaches gacalc transforms; using them in the plot code would make
   the book's plotting consistent with its own math. Any reason NOT to (e.g. gacalc is a heavier
   dep for a plotting util, or the bespoke code does something gacalc can't)?

## Deliverable

A feasibility writeup (feasible / not / partially, with the gaps and an effort estimate), plus a
recommendation. If feasible and low-risk, sketch the migration; do NOT do the full rewrite until
Bill signs off.

## Feasibility assessment (2026-08-03)

**Verdict: feasible, low-to-moderate risk. Recommend doing it, on a branch, gated by a
before/after pixel diff.** gacalc covers every primitive the bespoke library provides, the
exact same migration was *already done* for the notebook plotting util (`nbplotutils.py`),
and gacalc has *already upstreamed* the one non-trivial piece (the intermediate-composition
animation logic). No book prose changes.

### Scope is smaller than the task framing suggests

Two of the five listed files are **already on gacalc** — `util/nbplotutils.py` and
`notebooksrc/ndc.py` import `gacalc.g2.Vector2` + `gacalc.transforms`
(`InvertibleFunction`/`compose`/`scale_non_uniform`/`translate`/`identity`) and operate on
`list[Vector2]`. The bespoke `mpltransformations.py` has exactly **two** consumers left:
- `plotutils/matplotgraphs.py` — a small standalone demo module (draws a rotated grid).
- `plotsforbook/generate_plots.py` — the real work: the `generate_plots_for_book`
  console-script that emits every book SVG (translation-*, rotate*, scale, covariance,
  circle, ortho2d, inverse-ortho2d).

### What `mpltransformations.py` actually is

- **Value type:** matplotlib *parallel arrays* — a `PlotTransform` is
  `Callable[[xs, ys], Iterable[(xs, ys)]]` (`Axis = Sequence[float]`). It transforms a whole
  axis-pair at once via `map_matplotlib_data` (a `zip(*map(f, zip(*axes)))` splat/unsplat).
- **Primitives:** `translate(tx, ty)`, `scale(sx, sy)`, `rotate(angle)` (raw
  `x·cosθ − y·sinθ`, `x·sinθ + y·cosθ`), and `compose(*transforms)` applied **right-to-left**.
- **No inverse** in the library — "backwards" is done by consumers reversing the procedures
  list (`generate_plots.py`'s `forwards`/`backwards` + `accumulate_transformation`).

### gacalc coverage — full 1:1, numerically verified

| bespoke (arrays)            | gacalc (`Vector2`)                                        |
|-----------------------------|-----------------------------------------------------------|
| `translate(tx, ty)`         | `translate(b=tx*e_1 + ty*e_2)`                            |
| `scale(sx, sy)`             | `scale_non_uniform(sx, sy)`                               |
| `rotate(θ)`                 | `plane_rotation(Vector2.e_1, Vector2.e_2)(θ)` — **already bound as `mathutils.rotate`** |
| `compose(t1, t2, t3)`       | `compose([t1, t2, t3])` — same right-to-left order        |
| `accumulate_transformation` | `gacalc.transforms.compose_intermediate_fns_and_fn(fns, relative_basis=…)` |

Verified numerically (`plane_rotation` half-angle rotor vs the raw formula): agree to
**~4e-16 / ~9e-16** (last-ULP float noise) at 0.1°, 45°, −65°; `compose([scale, translate])`
reproduces the bespoke `(4, 0)`. gacalc's `compose_intermediate_fns_and_fn` docstring even
says it was *"ported from the author's modelviewprojection book"* — `accumulate_transformation`
can be **deleted**, not reimplemented (its `forwards`/`backwards` map onto the `relative_basis`
flag).

### The gaps (all already solved, once, in `nbplotutils.py`)

1. **Value type — arrays vs `Vector2`.** matplotlib's `plt.plot` wants `(xs, ys)`; gacalc
   works on `Vector2`. Bridge = build `x*e_1 + y*e_2`, apply `fn`, read back
   `fn(v).coeff_e_1 / .coeff_e_2`. `nbplotutils.py` is the working template (its `_xy()`
   helper + `[fn(vec).coeff_e_1 for vec in vecs]` plotting). `generate_plots.py`'s
   `Geometry.points` becomes `list[Vector2]` instead of a `(xs, ys)` tuple.
2. **sympy `Float` leakage.** Rotations can carry sympy coefficients; cast with `float(...)`
   / `list(v)` at the matplotlib boundary (documented in `nbplotutils._xy`). gacalc 0.0.14's
   numeric-preservation guard already keeps a *float* θ on a float pipeline, so this is a
   one-line cast, not a real obstacle.
3. **forwards/backwards frame semantics — the one real correctness risk.**
   `accumulate_transformation`'s two modes yield different intermediate frames (its doctests
   pin exact states). Mapping mvp's `forwards` onto gacalc's `relative_basis` and confirming
   it reproduces the *same* per-frame sequence is the thing to verify carefully. The pixel
   diff (below) catches any mismatch.

### No book-prose impact, no new dependency

- The book **does not `literalinclude`** `mpltransformations.py` or `generate_plots.py`; its
  transform listings come from `_gacalc_src/transforms.py` (gacalc's own source), and it
  depends on these files only through the **generated SVGs** (`.. figure::`). So deleting the
  bespoke module — and its exact-float doctests, and `matplotgraphs._rotate_point`'s doctests
  — changes no chapter text.
- gacalc is **already a hard dependency** (`requirements.txt` `gacalc==0.0.14`, imported all
  over the package incl. `nbplotutils.py`), so "heavier dep for a plotting util" does not
  apply — nothing new is pulled in.

### Output-preservation plan (per "derive the before mechanically")

`generate_plots.py` writes SVG (vector); the book rasterizes to PNG for LaTeX. Float noise
means SVGs won't be byte-identical, so compare **pixels**:
1. On `master`, run `generate_plots_for_book`, keep the ~40 SVGs.
2. On the branch, regenerate.
3. Rasterize both sets to PNG at a fixed DPI and diff (`compare -metric AE a.png b.png`, or
   numpy abs-diff) — expect ~zero differing pixels; investigate any figure that isn't.
Do the same one-figure smoke check for `matplotgraphs.py`.

### Effort & recommendation

- `matplotgraphs.py`: ~30 min (swap the four calls, drop `_rotate_point` doctests).
- `generate_plots.py`: the bulk — delete `accumulate_transformation` for gacalc's
  `compose_intermediate_fns_and_fn`, convert `Geometry.points` to `list[Vector2]`, add the
  (xs,ys)↔`Vector2` plotting bridge, map `forwards/backwards` → `relative_basis`. ~half a day.
- Verification harness: ~1 hour.
- **Total: ~1 day.** Recommend proceeding on a branch with the pixel-diff gate as the
  acceptance test. It deletes bespoke code, makes the book's plotting speak the same math the
  book teaches, and gacalc's API was literally built to receive it. Flag for Bill only the
  frame-semantics mapping (`relative_basis`), which is the single place a rewrite could
  silently change a figure.

## Notes

- Origin: Bill (2026-08-03), side note while at work: "I had originally made those composable
  transformations custom library back before I had gacalc. investigate, and tell me if you think
  it's feasible."
- Cross-ref: gacalc's transform layer is `github.com/billsix/geometricalgebra`
  (`src/gacalc/transforms.py`); mvp's façade is `mathutils.py`.
