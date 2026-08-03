# Plan: Planar shadow projection matrix in `matrix_stack`

**Status:** complete (2026-08-03). Bill's decision: **keep the directional
(parallel) shadow** — not the point-light perspective variant. Design rationale
harvested to `tasks/reference/design-decisions.md` › "The matrix / function stack".
(Module is `matrix_stack.py` now, not the old `pyMatrixStack`.)
**Priority:** 5
**Difficulty:** 4
**Completed:** 2026-08-03

**Reference implementation already in the codebase:** `chapt01/block/Block.py` has working inline `get_plane_equation()` and `make_planar_shadow_matrix(plane_eq, light_pos)` that returns a column-major flat 16-element numpy array, used via `glMultMatrixf`. Match those formulas (taken directly from `math3d.cpp:1026`) when implementing the `pyMatrixStack` version. The chapt01/block helpers will eventually be replaceable by `from modelviewprojection.mathutils import plane_equation` (Tier-1 task #5) and `from modelviewprojection.pyMatrixStack import planar_shadow` (this task) — until then the ports keep their inline copies.

## What

Add `m3dMakePlanarShadowMatrix` equivalent to `src/modelviewprojection/pyMatrixStack.py`. Builds a 4×4 matrix that projects geometry onto a plane along rays from a point light — the cheap "squish geometry into the floor" shadow trick from chapt05/shadow.cpp and chapt05/sphereworld.cpp.

## Why this lives in `pyMatrixStack` and not `mathutils.py`

The transform **collapses 3D → a 2D-on-a-plane subspace** — it has rank 3, not 4. There is no inverse. So it cannot be wrapped in `InvertibleFunction[V]`, which is the central abstraction in `mathutils.py`. Putting it in `pyMatrixStack` matches both:
- where it's actually used (demo22-and-after, all matrix-era)
- the pedagogical honesty: the shadow matrix is **not** an edge in the Cayley graph. The book chapter that introduces it should explicitly say so — that's the teaching moment.

## Signature (proposed)

```python
def planar_shadow(
    matrixStack: MatrixStack,
    plane_eq: tuple[float, float, float, float],   # (a, b, c, d) for ax+by+cz+d=0
    light_pos: tuple[float, float, float],          # point light in world space
) -> None:
    ...
```

Matches the in-place mutation idiom of `rotate_x`, `translate`, `scale`. The matrix is built and then `multiply`d into the current matrix at `matrixStack[-1]`. (Or it could replace `multiply(matrixStack, shadow_mat)` — TBD which fits the docstring style better; I'll mirror whichever existing function is closest.)

Why pass the plane as a 4-tuple rather than introducing a `Plane` class: matches SuperBible's API and the math literature. Vector4D is otherwise absent from mvp; adding it just for this is overkill.

## How — match Bill's documentation idiom

`pyMatrixStack` functions all have a docstring that:
1. Shows the matrix in row-major, 1-based notation
2. Shows the matrix multiplication worked out by hand
3. Then implements the in-place reduction

The shadow matrix has a clean derivation: for a plane `ax + by + cz + d = 0` with point light at `L = (Lx, Ly, Lz)`, project a point `P` along the line through `L` and `P` onto the plane. The 4×4 form (from `math3d.cpp:1026`) is:

```
[ b·dy + c·dz,    -b·dx,         -c·dx,                  -d·dx                  ]
[ -a·dy,          a·dx + c·dz,   -c·dy,                  -d·dy                  ]
[ -a·dz,          -b·dz,         a·dx + b·dy,            -d·dz                  ]
[ 0,              0,             0,                       a·dx + b·dy + c·dz   ]
```

where `dx = -Lx`, `dy = -Ly`, `dz = -Lz` (from SuperBible). Note column-major storage in numpy — implementation needs the transpose at write time.

The docstring should:
- Show the *derivation* (substitute the parametric line `P + t(L - P)` into the plane equation, solve for t, expand) — pedagogically, this is the punchline. A few lines of algebra.
- State explicitly: **this matrix has rank 3, is not invertible, and is not a Cayley graph edge.**
- Reference the book chapter that introduces it.

## Scope

- Add `planar_shadow(matrixStack, plane_eq, light_pos)` to `pyMatrixStack.py`.
- Don't yet wire it into any demo. (Demo22 already has a real shadow map; planar shadow is mentioned in comments but not used. A future task could add a demo that uses *only* the planar shadow trick, for chapter-aligned pedagogy.)
- Don't yet add a book chapter — that's a separate authoring task for Bill.

## Test plan

- Unit test: a known plane (e.g., y=0, plane_eq=(0,1,0,0)) and a known light (e.g., above the plane at (0, 5, 0)) should map an arbitrary point to the expected projected point — verify with one or two hand-computed cases via `pytest`.
- Determinant of the 4×4 must be 0 (rank deficiency).

## Open questions

- The signature uses tuples for `plane_eq` and `light_pos`. Should it instead take a `Vector3D` for the light and accept a `Vector4D`-shaped argument? Adding `Vector4D` to `mathutils.py` for this one use is probably not worth it; a 4-tuple is fine.
- Should the docstring derivation be written as a chapter aside, or as inline LaTeX in the docstring? Match the existing style — the existing functions use plain ASCII matrices, so likely the same.

## Work record (2026-08-03, autonomous session)

Implemented `planar_shadow(matrix_stack, plane_eq, light_pos)` in
`src/modelviewprojection/matrix_stack.py` (added just before `ortho`) and a new
test file `tests/test_matrix_stack.py` (the module had no test before).

**What it does.** Builds the SuperBible planar-shadow matrix and
**post-multiplies** it onto the current matrix, exactly like
`glMultMatrixf(shadow)` in `chapt01/block/Block.py`. Stored row-major
(`M @ column_vector`) per the module convention — i.e. the transpose of
Block.py's column-major flat buffer. Signature matches the plan:
`plane_eq=(a,b,c,d)`, `light_pos=(x,y,z)`, in-place mutation like `translate`.

**Faithfulness proof.** A scratch check plus `test_matches_block_reference`
confirm the row-major matrix is **byte-identical** (max abs diff `0.0`) to an
independent transcription of Block.py's reference (unsigned, `sign=+1`),
reinterpreted row-major. Rank/`det` and on-plane projection also asserted.

**Decisions made with discretion (flag for review):**

1. **Directional (parallel), not point-light (perspective).** The matrix the
   reference actually builds — and the one I matched — is the SuperBible `w = 0`
   *directional* shadow: the bottom row is zero, every vertex keeps the same
   `w`, and a point projects **straight along the light direction** (parallel
   projection), not along a ray fanning out from a finite point light. Block.py
   uses `v_light_pos = (…, 0.0)`, confirming directional. **This contradicts
   this plan's own "How" section**, which sketched the *point-light* derivation
   (`substitute P + t(L − P)`), a perspective shadow with a non-zero bottom row.
   I followed the "match math3d.cpp / Block.py" instruction (the authoritative
   reference) over the plan's derivation prose. **If you actually want the
   point-light perspective shadow, that is a different matrix and a one-line
   change to the bottom row — say so and I'll switch it.**
2. **Excluded Block.py's `sign` negation.** That flip is an mvp-specific
   CCW-winding / `w`-clipping rendering hack, not part of the canonical
   `m3dMakePlanarShadowMatrix`. The library builder produces the canonical
   matrix; the docstring documents the winding caveat and points at Block.py so
   a call site can negate if its winding needs `w > 0`.
3. **Param named `light_pos`** (matches SuperBible / Block.py API and the
   course vocabulary), with the docstring stating plainly it is used as a
   *direction*.

**Verification (this bare sandbox — no gacalc/glfw/GL):**
- `ruff check` + `ruff format --check --line-length=80`: clean on both files.
- `ty check` on both files: clean (module imports only numpy — no gacalc, so
  the "never ty against installed gacalc" trap does not apply here).
- `pytest tests/` (gacalc pip-installed for collection): **75 passed**, incl.
  the 5 new `test_matrix_stack.py` tests + the 2 `matrix_stack` doctests.
- **Not run:** the containerized `make format` gate and `make html` book build
  (heavy TeXLive/Sphinx — out of scope per session limits); the full
  `--doctest-modules` sweep (needs `glfw`/`tkinter`, absent here). None touch
  this change — it is purely additive (one new function, one new test file),
  no existing code edited.

**Out of scope, untouched (as the plan says):** not wired into any demo, no
book chapter. Block.py keeps its inline copy.
