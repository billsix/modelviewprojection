# Can the renderer build its GPU matrix from gacalc transforms? (perf investigation)

**Status:** proposed — investigation; a **492× per-call regression measured**, so a fast path is needed before the renderer can use `to_matrix`. Needs go-ahead (maintainer, 2026-09-04).
**Priority:** 5
**Difficulty:** 4

## BLUF

The renderer draws each sprite by uploading a 4×4 matrix (`uModel`) built by hand from numpy
(`_translate(tx,ty) @ _scale(w,h)`). gacalc can build the **identical** matrix from the
maintainer's own transforms via `gacalc.transforms.to_matrix(translate(...) @
scale_non_uniform(...))` — **verified bit-for-bit identical** (2026-09-04). The catch: `to_matrix`
builds the matrix by probing gacalc `Vector`s (the basis + origin) each call, so it is
**~492× slower** than the hand-built numpy — **1669 µs vs 3.4 µs per call** (measured, mvp
container). The renderer builds one such matrix **per sprite per frame** (a hot loop), so a naive
swap would be a large frame-time regression. This task investigates whether there's a fast path;
until then, **the renderer keeps its hand-built numpy matrices.**

## Context (read first)

- **Where this came from:** `tasks/gacalc-transforms-for-rotate-translate.md` — the maintainer's
  wish to use his own gacalc math (and its `to_matrix` conversion) to build the renderer's GPU
  matrix, so there's one source of truth. He approved doing it "if you can use my math and my
  conversions" and asked for this perf task if there were performance implications. There are.
- **The measured facts (2026-09-04, mvp container):**
  - **Correctness:** `to_matrix(translate(b=g3.Vector(tx,ty,0)) @ scale_non_uniform(w,h,1),
    cls=g3.G)` returns the **exact same** 4×4 as `_translate(tx,ty) @ _scale(w,h)` (`np.allclose`
    True; same homogeneous shape; translation in the last column — mvp's convention).
  - **Perf:** hand-built ≈ **3.4 µs/call**; `to_matrix` ≈ **1669 µs/call** → **~492×**. The cost is
    gacalc `Vector` object creation + the basis/origin probing inside `to_matrix`, not numpy.
  - **The renderer's matrix has no rotation** — just translate + non-uniform scale — so the whole
    point of routing through gacalc (clean rotation composition) does not even apply here.
- **The hot path:** `renderer.py` `draw_image`/`filled_rect` build `model` per draw
  (`renderer.py:227`, `:253`), inlined into all 10 games. A ~50-sprite frame at 60 Hz is ~3000
  matrix builds/sec; at 1669 µs each that is ~5 ms/frame of pure matrix building (vs ~10 µs today).

## What to investigate

1. **Is there a fast `to_matrix` path?** e.g. a numeric-only backend that skips the symbolic-capable
   `Coef` machinery; or building the transform once and reusing a compiled/cached matrix builder.
   Ask upstream gacalc (the maintainer's own library) whether a fast numeric probe is feasible.
2. **Caching / structure exploitation:** the matrix STRUCTURE is fixed (translate+scale); only
   `tx,ty,w,h` vary per sprite. Could we build a parameterised fast path once and fill in 4 numbers
   per draw, keeping gacalc as the *definition* but not paying the probe cost per call?
3. **Restrict scope to where perf doesn't matter:** the **ortho projection** (`ortho_pixels`) is
   built **once per renderer**, not per draw — converting *that* to gacalc is free and a real
   "use my math" win. Same for any one-time matrix. The **per-draw** model matrix is the only hot
   spot.
4. **Rollout question:** even with a fast path, the change would touch the shim renderer **plus the
   10 inlined game copies** (or land via step 3 re-extract). Decide sequencing against
   `tasks/pgzero-gl-step3-reextract-library.md`.

## Recommendation (pending investigation)

- **Now:** keep the renderer's hand-built numpy matrices (the 492× rules out a naive swap).
- **Free win available anytime:** convert the **one-time** ortho projection to gacalc `to_matrix`
  (no per-frame cost) if a "use my math in the renderer" gesture is wanted.
- **Do the per-draw conversion only if** investigation #1/#2 finds a fast path (target: within ~2×
  of the hand-built build, or the frame-time delta is proven negligible on real hardware).

## Related

- `tasks/gacalc-transforms-for-rotate-translate.md` — the parent study (crux: `to_matrix` exists +
  is correct; this task owns the perf half).
- `tasks/pgzero-gl-step3-reextract-library.md` — where a renderer change would actually roll out.
- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — the renderer design.
