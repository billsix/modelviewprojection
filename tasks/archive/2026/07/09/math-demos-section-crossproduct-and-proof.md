# Math demos section + cross-product demo + its proof

> **ARCHIVED 2026-07-09, superseded by multivariate-math:** mvp's
> crossproduct demo was removed (Bill approved; see
> `remove-crossproduct-demo.md` in this archive dir). The demo, labels
> infra, and proof work continue in the multivariate-math repo.


> **ACTIVE BUG (2026-06-14) — read first if resuming:** the demo's
> relative-coordinate *plane* (graph paper) for the forward phases is drawn wrong;
> Bill is frustrated after many failed iterations and asked for a fresh-eyes
> restart. Full handoff + Bill's complaints + what was tried + the correct
> reference (the undo phases & the original) in
> **`tasks/crossproduct-relative-coordinates-rendering.md`**. The demo's
> `crossproduct.py` is left in its current (still-wrong) state on purpose.

**Status:** Phases 1-3 DONE + rotor/Cayley-graph refactor DONE + animation-faithful
`cross_product_stepwise` DONE + the StepNumber sequencing reduced to a lightweight
local timeline DONE (all 2026-06-14, rotor approach per Bill). The demo's alignment
animation walks the rotor graph (trig-free, **no `atan2`/`sin`/`cos`**) and the
`do_*`/ratio-ladder flag soup is gone (two helpers over `step_number`). Remaining is
optional: book wiring of the notebook, and (only if the shared-shape goal warrants)
generalizing `cayleyscene` so math demos use `Scene/Timeline/Animation` directly.
Written 2026-06-14 from a read of `multivariate-math/src/crossproduct/` and
`.../proofs/crossproduct.tex`.

## Landed 2026-06-14

- **Decision (Bill):** derive the cross product with **rotors**, *porting the
  proof's geometric method* (rotate a onto x, bring b into the x-y plane, read off
  the perpendicular, rotate back) -- each rotation a gacalc `rotor_from_vectors` +
  `sandwich`, not a rotation matrix.
- **Math core:** `src/modelviewprojection/mathdemos/crossproduct.py ::
  cross_product(a, b)` -- pure gacalc, symbolic-capable (numbers *or* sympy).
- **Proof, symbolic:** `tests/test_crossproduct.py` -- a fast numeric-eval tier
  (default) and a `@pytest.mark.slow` **free-symbol sympy proof** that it equals
  `a x b` for ALL a, b (~225s; `pytest.ini` gained the `slow` marker + default
  `-m "not slow"`).
- **Notebook (percent jupytext):** `src/modelviewprojection/notebooksrc/crossproduct.py`
  -- Part 1 the symbolic rotor derivation + proof; Part 2 step-by-step with gacalc
  `show_mult` per multiplication. Executes clean end-to-end.
- **Demo (first cut):** the same file's `main()` (run by path) -- mvpvisualization
  style: orbit camera + imgui + cayley_gl world axes + a/b/(a x b) as live colored
  vectors, recomputed via `cross_product`. GL imports are local so the math import
  stays headless. **Visuals unverified (display = Bill's).**
- Related gacalc task filed: `geometricalgebra/tasks/show-mult-expand-numerators-not-denominators.md`.

## Rigor: what is *proven* vs. *verified*

Three different claims get made about this work, at genuinely different levels of
rigor. Keeping them straight (don't call a numeric check a "proof"):

1. **PROVEN -- the symbolic cross-product identity (the one real proof).**
   `tests/test_crossproduct.py::test_cross_product_equals_analytic_symbolically`
   (the `@pytest.mark.slow` test) runs `cross_product` on **free sympy symbols**
   `a_x..b_z` and asserts, per component, `sympy.simplify(got - expected) == 0`,
   where `expected` is the analytic `(a_y b_z - a_z b_y, ...)`. That is a proof for
   **all** a, b: sympy denests the nested-rotor radicals and shows the rotor
   derivation is *identically* the cross product. ~minutes (the denesting is the
   cost). This is the only claim here that is a genuine all-inputs proof.

   - **Caveat -- the 3-rotor forms are NOT proven this way.**
     `cross_product_stepwise` and `cross_product_via_graph` use three nested rotors;
     their free-symbol `sympy.simplify` does **not** terminate in practical time (a
     single component ran >15 min unfinished in a probe). They are instead checked
     by **high-precision exact-integer evaluation** (`sympy.N(..., 30)` on
     `EXACT_CASES`) -- a strong check, **not** an all-inputs proof. Documented in
     the test. (Closed-form `cross_product` is the two-rotor form, which *is*
     tractable, hence it carries the real proof.)

2. **VERIFIED (numeric, sample inputs) -- the rotor/matrix bridge in the demo.**
   When the demo's rotations were wired to the rotor graph, it was checked headless
   that `to_matrix(R_axis.at(1))` *equals* the old `rotate_<axis>(angle)` matrix
   (`np.allclose`), that `.at(0)` is identity, and that the in-between / inverse /
   arrow matrices are valid rotations (orthonormal, det = 1) across the animation
   for both vector orderings. This is **numeric verification on sample vectors at
   the endpoints**, not a symbolic all-inputs proof -- the exact endpoint match is
   what justifies "the on-screen choreography is unchanged."

3. **EQUIVALENT BY CONSTRUCTION -- the StepNumber -> timeline refactor.**
   "Provably behavior-equivalent" there means the substitutions are *identities*:
   `reached(X)` is the definition of the old `do_*` latch (`step_number >= X`), and
   `step_progress(X)` is the old ratio ladder verbatim. Backed by a standalone
   step-machine simulation (correct 12-step walk, `vec3` built on entering
   `show_triangle`, instant steps don't reset the clock). Equivalent by
   construction + checked -- not a formal proof.

   In all of 2 and 3 the **visuals themselves are display-only** -- Bill verifies by
   running the demo; the headless checks bound *what can* go wrong, not the pixels.

## Performance -- later stages ran slower (investigated + FIXED 2026-06-14)

**Symptom (Bill):** as the demo's stages progressed, each stage took longer in
wall-clock time.  **Fixed** by caching completed-stage transforms (C) + a
wall-clock animation clock (B) -- details under "Fixes" below.

**Root causes (measured):**
1. **Frame-count animation clock.** `frame()` does `animation_time += 1/60` per
   frame -- it *assumes* 60 fps.  So any fps drop slows the animation in real time
   (each stage gates on `animation_time` reaching `seconds_per_operation`).  This is
   the amplifier.
2. **Per-frame realize cost grows with stages.** Every frame rebuilds each rotor via
   `.at()` and re-walks the whole growing `compose([...])` through `to_matrix`
   (several `set_model`s per frame).  Measured ~0.9 ms/frame early -> **~77 ms/frame
   (~13 fps)** at full alignment -> via #1 that becomes a big wall-clock slowdown.
3. **The rotor EDGES run in sympy, not float (~2.7 ms each).** The demo's edges are
   built by the transform-layer `rotor_rotation` (via `_rotor_edge`), which for these
   inputs returns gacalc's **general `Gn`** type (symbolic, dimension-agnostic, slow)
   -- whereas the *specialized* `Vector3.rotor_from_vectors(...).sandwich(...)` path
   that the closed-form `cross_product` uses stays fast `float` (~0.035 ms).  This is
   the dominant per-op multiplier.

**Tried and REVERTED -- "A", numeric basis (ineffective).** Hypothesis was that
rotating *to* the int-coeff constants `Vector3.e_1`/`e_2` promoted to sympy.  A
standalone `rotor_from_vectors(float, int_basis)` does promote -- BUT giving
`build_alignment_graph` a `numeric=True` float-basis option did **not** help: the
chained edges stay `sympy.Float` and ~2.7 ms regardless of basis, because the sympy
comes from `rotor_rotation` returning `Gn`, not from the basis.  Reverted.

**Fixes (C + B DONE 2026-06-14; gacalc-level deferred):**
- **C -- cache each stage's end-state transform (Bill's idea). DONE.** Transforms are
  still gacalc `InvertibleFunction`s, but realized to 4x4s (`to_matrix` = the
  function's action on the basis -- "values out of the InvertibleFunction" *are* the
  matrix columns) and multiplied in numpy.  The STATIC pieces (the `-90` coords, each
  completed rotor edge at full) are cached in `g.mcache` (reset in
  `rebuild_alignment`); **only the one actively-animating edge is realized fresh each
  frame** (`edge_M`: identity at ratio<=0, cached at >=1, fresh in between).  Note: it
  has to cache the *realized* value (matrix), not the composed function -- `to_matrix`
  re-walks the rotors regardless, and that realize (the slow `Gn` path) is the cost.
  **Measured: per-frame model build ~23 ms -> 0.5 ms (constant, was growing toward
  ~77 ms).**  Verified the cached-matrix model is `np.allclose` to the compose-based
  one for all 12 steps x fractions (behavior identical).
- **B -- wall-clock animation clock. DONE.** `frame()` now advances `animation_time`
  by real elapsed time (`glfw.get_time()` delta, clamped to 0.1 s so a hitch can't
  jump it) instead of `+= 1/60`; auto-rotate is likewise dt-scaled (~6 deg/s).  So a
  stage takes its `seconds_per_operation` in real seconds regardless of frame rate.
- **gacalc-level (possible, NOT now per Bill).** Make the transform-layer
  `rotor_rotation` return the specialized `Vector3`/`Rotor3` (fast float) instead of
  `Gn` for specialized inputs.  Source is in `/geometricalgebra`; could rebuild an
  updated gacalc into the mvp venv.  Bill: "not the path I want to go right now, but
  possible."  If done, the per-frame recompute becomes cheap on its own and C/B become
  optional -- but it's a gacalc change touching every consumer, so treat as its own
  task.

## Remaining

DONE 2026-06-14:
- **Faithful 12-step animated demo** (`main()`): the source's `StepNumber`
  choreography (rotate a onto x via z/y, b into the x-y plane via x, show triangle,
  project onto y-z, rotate y->z, undo, scale, show plane), all visuals (ground,
  unit circles, world + relative axes, vectors, triangle/projection/plane).
- **mvpvisualization solid look:** ground/circles as cylinders, vectors/axes as
  `build_axis_arrow_solid` cylinder+cone arrows, origin sphere -- one solid
  pipeline, no thin lines.
- **Controls moved into the menubar** (like the other mvp demos): File (Quit) /
  Animation (Next step, Restart, AutoPlay, Seconds/step, Draw Relative Coords) /
  Camera (Auto-Rotate, Radius, View-Down presets) / Vectors (edit a/b, Swap,
  Highlight a/b) / Highlight (x/y/z, x'/y'/z') / View (Fullscreen, Natural Basis).
- **Mouse-wheel zoom** works in both views, on independent state: perspective
  scrolls `camera.r`; the View-Down ORTHO presets scroll `ortho_extent` (the half-
  height of the ortho volume), so each view keeps its own zoom level.

### Phase -- rotor + Cayley-graph refactor of the demo (Bill)

The animated demo still drives the choreography with `ms.rotate_x/y/z` (axis
rotations on the matrix stack) parameterized by `atan2` angles, plus a hand-rolled
`StepNumber` machine. Refactor it to:
  1. **Build the rotations with rotors, not axis `rotate_*` + `atan2`.** Use
     `rotor_from_vectors` directly from the vectors (e.g. a rotor that carries the
     projection in the e1-e2 plane onto e1, then onto e1 fully; a rotor carrying
     `reject(b, a)` into the plane) -- the same vector-query style the closed-form
     `cross_product` uses (zero trig).
  2. **Drive it with the `cayley/` data structures** (`cayleygraph` + `cayleyscene`)
     like the other mvpvisualization demos: spaces = the successive frames, edges =
     the rotor steps, the timeline = the animation -- instead of the bespoke
     `StepNumber` + `do_*`/`draw_*` flag soup.
  Open question (same as before): **animation interpolation of rotors** -- confirm
  gacalc rotors interpolate / slerp for a partial (fraction-t) rotation, or derive
  one, so the stepped animation can use them in place of the interpolable
  `rotate_*`.

  **Progress 2026-06-14 -- core machinery DONE + verified (headless):**
  - `_rotor_edge(from, to)` -- an interpolable ROTOR `InvertibleFunction`
    (`rotor_rotation`, i.e. `rotor_from_vectors`+sandwich) whose `.at(t)` is a
    smooth partial rotation via a **rotor slerp** interpolate. (Answers the open
    question: `rotor_rotation`'s `.at(t)` returns identity without an `interpolate`,
    so we supply a slerp one.) Test: identity at t=0, full at t=1, genuine midpoint.
  - `build_alignment_graph(a, b)` -- a `cayleygraph.CayleyGraph` of rotor edges
    `world --R_1--> a_on_x --R_2--> b_in_xy`, built from the vectors' projections
    (rebuild when a/b change / on animation start, per Bill's note).
  - `cross_product_via_graph(a, b)` -- traces `b_in_xy -> world` (auto-inverting)
    on `cross_aligned = |a||b_perp| e_3`; test confirms it equals `a x b`.
  **Update 2026-06-14 (2) -- nlerp, not slerp.** `_rotor_edge.at(t)` was switched
  from a slerp (which used `acos`/`sin`) to an **nlerp** (linearly blend the start
  and target *directions*, rebuild the rotor) so the whole rotor/graph path is
  **trig-free** -- no `sin`/`cos`/`acos`/`atan2` anywhere. `build_alignment_graph`
  is now the three plane rotations `world --R_z--> a_in_xz --R_y--> a_on_x --R_x-->
  b_in_xy`, each `reject` (project onto a coordinate plane) + `rotor_from_vectors`.
  Notebook `notebooksrc/crossproduct.py` gained a **Part 3** demonstrating this
  project->rotor method.

  **DONE 2026-06-14 (3) -- demo animation now walks the graph.** `draw_scene`'s
  alignment rotations are wired to the rotor edges:
  - `restart()` / vector edits / swap call `rebuild_alignment()`, which builds the
    graph from the (run-fixed) vectors and caches the three forward edges + their
    `inverse()`s on `g` (`g.r_z/r_y/r_x` + `_inv`).
  - every alignment `ms.rotate_<axis>(+/-angle * ratio)` became
    `apply_rotor(edge, ratio)` = `ms.multiply(model, to_matrix(edge.at(ratio)))`
    -- forward edge for the `-angle` (align) calls, `inverse` edge for the
    `+angle` (undo / relative-frame / vec3-chain) calls.
  - `Vector.angle_y/angle_z`, `calc_angle_x`, and the dead `_alignment_steps` were
    deleted; `draw_vector` orients its `+Y` arrow with `rotor_rotation(e_2, v)`.
    The *only* `atan2` left in the file is in comments; **no trig in any
    derivation/transform.**
  - **Verified headless:** `to_matrix(R_axis.at(1))` equals the old
    `rotate_<axis>(angle)` matrix for each axis (so endpoints/choreography are
    identical); `.at(0)`=identity; intermediate + inverse + arrow matrices are all
    valid rotations across `t` for both vector orderings; compile / ruff / 3 fast
    tests pass. Visuals (the actual animation) are **display-only -- Bill verifies
    by running it**.

  (Update: as of DONE (5) below, the camera view, the `-90deg` "math coordinates"
  reorient, and the `90deg` y->z swing were ALSO moved into gacalc `compose`.  What
  stays on the matrix stack is only the projection squash and the tiny fixed
  per-mesh orientations in the draw helpers -- see (5).)

  **DONE 2026-06-14 (4) -- lightweight local timeline.** The `do_*`/ratio-ladder
  soup is gone (Bill chose a demo-local timeline over force-fitting
  `cayleyscene.Scene`, which is built for placement-tree + NDC-tail demos and
  doesn't fit this op-sequence-with-reveals demo).  `StepNumber` is kept as the
  ordered step list (the timeline's backbone); everything derived from it by hand
  was collapsed to two helpers over `g.step_number`:
  - `reached(step)` = `g.step_number.value >= step.value` -- replaced all 10
    `do_*` latch flags (`do_first_rotate` ... `do_scale`, `do_remove_ground`,
    `rotate_yz_90`, `project_onto_yz_plane`), which were each exactly that. Removed
    from `Globals` and from `advance_step`.
  - `step_progress(step)` = 0 before / `current_animation_ratio()` during / 1 after
    -- replaced the ~10 repeated `ratio = ... if step==X else 0.0 if ... else 1.0`
    ladders in `draw_scene` with one-liners.
  - `advance_step` collapsed from a 12-branch ladder to: bump to the next
    `StepNumber`, restart the clock (except the instant-reveal steps
    `show_triangle`/`show_plane`, which the source also didn't re-time), plus the
    one genuine side effect (build `vec3` from the model matrix on leaving
    `rotate_x`).
  Kept as genuine state: the six user-toggled `draw_*_relative_coordinates` flags
  (the Animation menu's "Draw Relative Coordinates", auto-cleared when a rotation
  finishes).  **Behavior-preserving** -- verified headless (compile / import / ruff
  / 4 fast tests) and by a standalone step-machine simulation (correct 12-step
  walk, `vec3` created on entering `show_triangle`, instant steps don't reset the
  clock, `reached`/`step_progress` match the old ladder semantics).  Visuals are
  display-only -- Bill verifies by running it.

  **Remaining (optional):** none for the sequencing.  The deeper "make this demo
  use `cayleyscene.Scene/Timeline/Animation` like the MVP visualizations" would
  require generalizing `cayleyscene` to a new op-sequence scene type (it currently
  models placement-tree + NDC-tail only); deferred unless the shared-shape goal
  for future math demos makes it worthwhile.

  **DONE 2026-06-14 (5) -- transforms composed in gacalc, not the matrix stack
  (Bill, "do as much as possible in gacalc"; pragmatic scope).** The model + view
  transforms are now built as gacalc `InvertibleFunction`s (`compose([...])` of
  rotors / `translate` / `scale_non_uniform` / `rotate_x`) and realized to a 4x4
  **only at upload** via `cayleyscene.to_matrix` + `set_current_matrix` -- the
  `mvpvisualization/model.py` idiom (`to_matrix(animation.transform(...))`).  The
  matrix stack is now just the upload buffer:
  - the old `ms.rotate_*/translate/scale/multiply/push_matrix` **accumulation** on
    the model is gone; `apply_rotor` (rotor->matrix->`ms.multiply`) was replaced by
    composing onto a running `model_fn` and `set_model(fn)` before each draw.
  - the camera/view is likewise `compose([...])` realized to the view matrix.
  - **Projection stays `ms.perspective`/`ms.ortho`** -- the perspective/ortho
    *squash* is NOT an affine `InvertibleFunction`, so `to_matrix` can't realize it
    (cayleyscene decision #4).  This is the one irreducible matrix-stack use.
  - Pragmatic scope (Bill's choice): the tiny FIXED per-mesh orientations inside
    the draw helpers (axis arrows' +/-90deg, the plane-mesh +/-90deg) stay local
    `ms.rotate` -- rendering trivia, not the scene/animation math.  (`draw_vector`'s
    arrow orientation is already a gacalc rotor.)
  - **Behavior-preserving, verified headless:** for ALL 12 steps x {0, 0.5, 1.0}
    the new gacalc-composed model AND vec3-chain matrices are `np.allclose` to the
    old `ms`-accumulation (and `compose` order was proven to match the stack's
    post-multiply).  compile / import / ruff / 4 fast tests pass.  Visuals are
    display-only -- Bill verifies by running it.

### Phase -- a second, animation-faithful `cross_product` (Bill) -- DONE 2026-06-14

Keep `cross_product` exactly as-is (Bill likes the single-rotor
`rotor_from_vectors(a -> e_1)` form). Add a SECOND function (e.g.
`cross_product_stepwise`) that computes `a x b` the way the **animation/proof**
does it: as three **plane** rotations built from **projections**, NOT one rotor
straight from a to e1.

**DONE:** `cross_product_stepwise(a, b)` added -- the explicit three-plane-rotation
form (project a onto e1-e2 -> rotor onto e1; rotate its e1-e3 part onto e1; project
b's perpendicular onto e2-e3 -> rotor onto e2; read off `|a||b_perp| e_3`; rotate
back), written inline so the body reads as the derivation. Trig-free (reject +
rotor_from_vectors), pure gacalc. It's the inline twin of the graph-walking
`cross_product_via_graph`; the demo animation walks the same three rotors via
`build_alignment_graph`. So there are now three comparable forms: closed
(`cross_product`), graph-traced (`cross_product_via_graph`), explicit-stepwise
(`cross_product_stepwise`).

**Test:** `test_cross_product_stepwise_integer_cases` -- exact-sympy coefficients
on `EXACT_CASES`, high-precision evalf (the tier `cross_product_via_graph` uses).
**No free-symbol slow proof** for the stepwise/graph forms: with three nested-rotor
radicals `sympy.simplify` does **not** terminate in practical time (a single
component ran >15 min unfinished in a probe), unlike the closed form's two-rotor
proof (which is the existing `@slow` test). Documented in the test. Bill wanted the
symbolic proof "to pass too"; the tractable symbolic check is the exact-integer
high-precision one -- the free-symbol version is infeasible for 3 nested rotors.

### Other
- Optional: wire `notebooksrc/crossproduct.py` into the book (jupytext conversion
  in `entrypoint.sh` + a toctree entry). NB: the symbolic proof cell is ~4 min, so
  every book build pays that (nb_execution_timeout is 600s, so it fits).
- The proof now *is* the rotor notebook, so the earlier "rewrite the LaTeX proof
  with rotors" idea is effectively done.

## Goal

Stand up a **general "math demos" section** in mvp, structured like
`src/modelviewprojection/mvpvisualization/` — i.e. built on the **Cayley-graph**
abstraction (`cayleygraph.py` + `cayleyscene.py`) the book already teaches — so
future math demos drop in with a consistent shape. The first demo is the
**cross product** (porting the multivariate-math animation), and its **LaTeX
proof** gets ported into the book in a new derivations section. Cross product is
the seed; the structure is the point (other math demos should fit even if they
aren't in any repo yet).

## What's in the source (multivariate-math)

**Demo — `src/crossproduct/` (~1100 LOC + assets):**
- `crossproduct.py` — glfw + **`imgui`** (not imgui_bundle) + PyOpenGL animation.
  Drives the derivation with a 12-member `StepNumber` enum (`beginning`,
  `rotate_z`, `rotate_y`, `rotate_x`, `show_triangle`, `project_onto_y`,
  `rotate_to_z`, `undo_rotate_x/y/z`, `scale_by_mag_a`, `show_plane`) plus a
  ~40-field `Globals` dataclass of `do_*` / `draw_*_relative_coordinates` flags,
  hand-toggled per step. imgui panels: **Cross Product** (per-step description via
  `match` on `StepNumber`), **Input Vectors** (`input_float3` for a, b + swap),
  **Camera** (auto-rotate, view-down-axis buttons, ortho toggle), **Time**
  (autoplay, restart, seconds-per-operation).
- `renderer.py` — its own harness: `compile_shader(vert,frag,geom)`,
  `do_draw_lines`, `do_draw_vector`, `do_draw_axis`, `do_draw_image`, `Camera`,
  `Vector`. **Duplicates** what mvp's `mvpvisualization/_pipeline.py` already does.
- `pyMatrixStack.py` — its **own** copy (mvp has `src/modelviewprojection/pyMatrixStack.py`).
- shaders: `lines.{vert,geom,frag}` (thick lines), `image.{vert,frag}` (textured
  billboards), and `images/` = `a/aprime/aprimeprime/b/bprimeprime/bprimeprimeprime/x/y/z.png`
  — the vector *labels* (a, a′, a″, b, …, x, y, z) drawn as textures in 3-space.

**Proof — `proofs/crossproduct.tex` (449 lines):** an `article` with custom
`problem`/`proof`/`theorem`/`lemma` environments and heavy `flalign`. It derives
a×b in exactly the demo's language: define `f_a^{zx}`, compose `f_{a'}^x ∘ f_a^{zx}`
to get `a''`, transform `b''`, apply `f_{b''}^{xy}`, project, undo the rotations,
scale by |a|. **The functions in the proof are the edges of the Cayley graph.**
(Sibling proofs `quaternions.tex`, `multivariatebasics.tex` exist — future
candidates for the same book section, out of scope here.)

## Target structure in mvp

mvp already has the machinery this needs, in `mvpvisualization/`:
- `cayleygraph.py` — immutable DAG; nodes = coordinate **spaces** (per-demo Enum),
  edges = sequences of interpolable `InvertibleFunction`s; `path()` composes /
  auto-inverts. Pure data/math, no GL, unit-testable.
- `cayleyscene.py` — turns a graph + declarative scene into an **animation**: a
  timeline, per-frame object transforms, the world→camera inverse, visibility, and
  the two imgui trees — *derived from the one graph, no hand-kept parallel state.*
- `cayley_gl.py` — the GL shell; `_pipeline.py` — shared procedural pipeline +
  shaders (`per_vertex_color.vert`, `thick_lines.geom`, `uniform_color.vert`,
  `project_*.glsl`).

**Proposed layout** (mirrors `mvpvisualization/`):
```
src/modelviewprojection/mathdemos/
    __init__.py
    crossproduct.py          # the demo: declares a CayleyGraph + scene, run by path
    crossproduct.vert/.geom  # only if it needs shaders beyond the shared set
    images/                  # a.png … z.png label textures (or render text instead)
```

### Design decision — RESOLVED: promote to neutral home (Bill, 2026-06-14)

Chosen: a neutral `src/modelviewprojection/cayley/` package; both
`mvpvisualization/` and `mathdemos/` import from it. (The alternative — importing
the machinery from `mvpvisualization/` — was rejected as the section is meant to
grow.)

## Phase 1 — scaffold the section — DONE (2026-06-14)

- Created `src/modelviewprojection/cayley/` (neutral home) and
  `src/modelviewprojection/mathdemos/` (the demos package), each with `__init__.py`.
- `git mv`'d the pure, GL-free machinery `cayleygraph.py` + `cayleyscene.py` into
  `cayley/`; fixed `cayleyscene`'s internal import.
- Repointed every importer to `modelviewprojection.cayley`: the 7 viz demos
  (`coordinatesystems`, `model`, `modelview`, `modelview2d`,
  `modelvieworthoprojection`, `modelviewperspectiveprojection`, `pushmatrix` — split
  their grouped import so `cayley_gl` still comes from `mvpvisualization`) and the 3
  tests (`test_cayley_graph`, `test_cayley_scene`, `test_focus_to_matrix`).
  `cayley_gl.py` needed no change (it imports only `_pipeline`, takes scenes as args).
- Verified in the container: `cayley.cayleygraph`/`cayleyscene` import; the 7 demos
  + `cayley_gl` py-compile; **full suite 58 passed**. The book references only the
  *demo* file paths (unmoved), so no book edits needed.

**Deferred to Phase 2 (intentional):** `_pipeline.py` was NOT moved. It's a mix of
general infra (window/camera/`compile_program`/`build_pipeline`/VAO/VBO) and
mvp-viz-specific geometry (cylinder/ndc-cube/axis-arrow builders). Rather than
blind-split the GL render core during scaffolding, extract only the genuinely
reusable infra into `cayley/pipeline.py` in Phase 2, informed by what the
cross-product demo actually needs (then repoint `cayley_gl`'s `_p` import).
- Also Phase 2: decide the image/billboard pipeline for the `.png` labels (port the
  source's `image.{vert,frag}` + `do_draw_image`, or render text) — `_pipeline.py`
  is currently line/triangle oriented.

## Phase 2 — port the cross-product demo as a Cayley scene

The real work is **re-expressing the hand-rolled state machine as a graph**, not a
line-by-line translation:
- **Nodes** = the coordinate frames the derivation passes through (natural basis →
  a-aligned frame after `f_a^{zx}` → after `f_{a'}^x` → b″ frame → …). **Edges** =
  the proof's `InvertibleFunction`s (`rotate_x/y/z`, `compose`, `inverse` from
  `mathutils`). The 12 `StepNumber` steps become the scene **timeline** over the
  graph's edge-substeps; the ~40 `Globals.do_*/draw_*` flags collapse into the
  scene's derived visibility/animation (the whole reason to use `cayleyscene`).
- **Math:** replace numpy/its vectors with mvp's **gacalc-based** `Vector3` +
  `InvertibleFunction` (`mathutils`). This is the natural representation — the proof
  is already in this language.
- **Rendering:** drop the vendored `renderer.py` + `pyMatrixStack.py`; use mvp's
  `pyMatrixStack.py`, `_pipeline.py`, and `mvpvisualization` shaders. Reuse the
  cylinder/thick-line visual style.
- **imgui:** port the four panels to **`imgui_bundle`** (mvp's binding; source uses
  `imgui`). Every adjustable parameter stays an imgui widget (input a/b, camera,
  autoplay/seconds-per-op, ortho, axis highlights).
- **Run by path** like the mvpvisualization demos
  (`python src/modelviewprojection/mathdemos/crossproduct.py`); part of the
  installed package. **No absolute paths** — load shaders/images via env var +
  sibling-walk + fallback (the ports convention).
- Add a `tests/` data-only test for the graph (the cross-product result for known
  a, b) — `cayleygraph` is unit-testable headless; rendering stays Bill's to verify.

## Phase 3 — port the proof into the book

- New book section for derivations. The toctree (`book/docs/index.rst`) already
  carries non-chapter sections (`mathhomework1`, `perspective`, `miscellany`), so
  add e.g. `derivations.rst` (or `crossproductderivation.rst`) as an appendix-style
  entry. Cross-link it from the cross-product demo and from the relevant chapter on
  composition.
- Convert `crossproduct.tex` → Sphinx: the custom `problem`/`proof`/`theorem`
  environments and `flalign` must map to the book's math tooling (the
  `math-dollar` / inline-tex extensions already in `conf.py`; see the done
  `archive/.../sphinx-*-inlinetex` work). This is the fiddly part — budget for it.
- Keep the proof's notation (`f_a^{zx}` etc.) consistent with the demo's edge names
  and the book's Cayley-graph vocabulary so proof ↔ demo read as one thing.

## Conventions to honor

- imgui widgets for every parameter; keyboard only as accelerator.
- No hardcoded absolute paths in the demo (env var + sibling-walk + sandbox fallback).
- gacalc `Vector3` / `InvertibleFunction` for the math; mvp `pyMatrixStack` + the
  shared pipeline/shaders for rendering; don't re-vendor `renderer.py`/`pyMatrixStack.py`.
- Build/package locally; Bill verifies anything needing a display.

## Future (not this task)
- Same section: `quaternions.tex`, `multivariatebasics.tex`, and further math demos
  (each a Cayley scene under `mathdemos/`).
