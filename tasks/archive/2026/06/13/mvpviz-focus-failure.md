# mvpViz demos fail when focusing on an object — root cause + fix plan

**Status:** complete (mvp scope — focus crash fixed & verified; gacalc-side improvement tracked separately in `[[magnitude-numeric-for-numeric-input]]`)
**Completed:** 2026-06-13
**Created:** 2026-06-13

## Symptom

mvpVisualization demos crash on focus / view-inverse. Actual traceback
(`modelviewperspectiveprojection.py:406`):

```
ms.multiply(ms.MatrixStack.view, np.linalg.inv(frame))
numpy._core._exceptions._UFuncInputCastingError:
  Cannot cast ufunc 'inv' input from dtype('O') to dtype('float64') with casting rule 'same_kind'
```

## Root cause (confirmed)

The matrix passed to `np.linalg.inv` is **`dtype=object`**, because its entries are
**sympy expressions, not Python floats**. Chain:

1. gacalc `MultiVectorBase.magnitude()` = `sympy.sqrt(magnitude_squared())`
   (`base.py:229`) — **always** returns a sympy expression, even for numeric input.
2. `rotate_z` / `rotate` go through `rotor_rotation` → `rotor_from_vectors`
   (`R = |from||to| + to·from`), so the rotor — and every vector it rotates —
   picks up **sympy** coefficients.
3. mvp's `cayleyscene.to_matrix` (`cayleyscene.py:419–438`) and
   `CameraControls.apply` (`cayleyscene.py:71`) build `np.array([...])` straight
   from those `coeff_*` values → the array is `dtype=object`.
4. `np.linalg.inv(frame)` (`modelviewperspectiveprojection.py:406`) and any numeric
   GL path can't operate on an object array → the cast error.

**Evidence (headless, against `pip install gacalc` == 0.0.3):**
- `rotate_z(0.7)(Vector3(1,0,0))` → coeff types `Float`, `Float`, `Zero` (sympy).
- `to_matrix(...)` → `M.dtype == object`; `np.linalg.inv(M)` raises the exact error;
  `M.astype(float)` then inverts fine.
- Reproduces against the gacalc **mvp actually imports** — the venv, which is also
  **0.0.3** (same as PyPI): rotated coeffs `Float/Float/Zero`, matrix `dtype=object`,
  `np.linalg.inv` raises, `.astype(float)` fixes it. So the bug is in the **pinned
  0.0.3** — introduced by the **migration to gacalc** (mvp's old `Vector3D` math
  returned plain floats; gacalc's `magnitude()` injects sympy), **not** a
  newer-gacalc regression.

### Why earlier theories were red herrings
- `to_matrix` itself never raised in repro because it doesn't invert — only the
  perspective demo's `np.linalg.inv` does. So "focus composition works" was
  misleading: it produces a *poisoned* (object-dtype) matrix.
- Positional `Vector3(x,y,z)` works on 0.0.3 — unrelated.
- The `AbstractMultiVector` → `MultiVectorBase` rename (gacalc `c5725e0`,
  **unreleased**) is a **separate, latent** break: it'll stop mvp importing once
  gacalc bumps past 0.0.3, but it is NOT this focus crash. Track it as a sub-item.

## Fix

Two layers; recommend doing the mvp one now and the gacalc one as the proper fix.

- [x] **Immediate (mvp) — coerce to float at the numpy boundary.** DONE:
      `cayleyscene.to_matrix` now builds `np.array([...], dtype=float)`
      (`cayleyscene.py:~437`). That was the one object-dtype source feeding
      `np.linalg.inv` (all `_pipeline.py` matrices already pass `dtype=np.float32`).
      `CameraControls.apply` (`cayleyscene.py:71`) builds no array itself — its
      rotations' sympy flows through `to_matrix`, now covered. Verified: focus
      matrix is `float64`, `np.linalg.inv` succeeds (round-trip err ~2e-16).
- [ ] **Proper (gacalc) — keep numeric magnitudes numeric.** Make `magnitude()` /
      the rotor path return a Python float for numeric input instead of always
      `sympy.sqrt` → sympy. Tracked on the gacalc side as
      `[[magnitude-numeric-for-numeric-input]]` (related: `[[magnitude-sympy-cast-to-coef]]`,
      `[[geometric-product-magnitude-proof]]`). Reduces the "sympy leaks into
      numeric pipelines" surprise at the source, for every gacalc consumer.

> **Decision — keep the mvp float-coercion permanently, even after gacalc is fixed.**
> The cast belongs at mvp's numpy/GL boundary regardless: numpy/OpenGL need
> `float64`; gacalc may legitimately return sympy in *symbolic* mode; `float(x)` is
> free when `x` is already a float; and it decouples mvp's rendering correctness
> from gacalc's internal numeric-vs-symbolic policy. The gacalc fix is
> complementary, not a replacement — so **fix mvp first (this unblocks the demos),
> then gacalc later, and do not revert the mvp change when gacalc lands.**
- [x] **Re-verify.** DONE: full mvp suite green (`pytest` → 55 passed). Also fixed
      two **pre-existing** failures in `tests/test_cayley_scene.py`
      (`test_to_matrix_realizes_affine_function`,
      `test_to_matrix_of_engine_transform_matches_point_application`) — they were
      already broken before this change (confirmed against the committed
      `to_matrix`): their assertion built `np.allclose(..., [want.coeff_e_1, …])`
      from the **sympy** `want` side, so `np.allclose` raised `isfinite`. Now the
      expected coeffs are wrapped in `float(...)`. (Real-display run of the GL
      demos still wants a human check on Bill's host.)
- [x] **Regression guard.** DONE: `tests/test_focus_to_matrix.py` builds a
      `rotate_z` focus path, asserts the matrix is `float64`, and that
      `np.linalg.inv` succeeds.
- [ ] **Sub-item (separate):** when gacalc releases the base-class rename, update
      mvp `mathutils.py` (`AbstractMultiVector` → `MultiVectorBase`, lines
      41/62/103/105) and bump the `gacalc>=` pin together.

## Notes / decisions

- Reproduced against `pip install gacalc` (0.0.3) per Bill's instruction — the
  released behavior mvp actually depends on. The object-dtype matrix is present
  there; only `np.linalg.inv` (perspective demo) turns it into a hard crash.
- mvp and gacalc are separate repos; the deeper fix lives in gacalc, the
  unblocking fix in mvp.
- gacalc's `Gn` eager-simplifies and `magnitude` uses `sympy.sqrt` by design — the
  gacalc fix must keep symbolic mode working while returning numbers for numeric
  input.

## Open questions

- Do the immediate float-coercion in mvp now (fast unblock), the gacalc
  numeric-magnitude fix, or both? (Recommended: both — mvp first.)
- Should `to_matrix` defensively assert/raise a clear error on non-float
  coefficients, so a future sympy leak fails loudly instead of deep in numpy?
