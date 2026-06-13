# mvpViz demos fail when focusing on an object — root cause + fix plan

**Status:** root cause CONFIRMED (reproduces on released gacalc 0.0.3) — fix not yet applied
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

- [ ] **Immediate (mvp) — coerce to float at the numpy boundary.** In
      `cayleyscene.to_matrix` build the array as float (`np.array([...], dtype=float)`,
      or wrap each `coeff_*` in `float(...)`), and the same in
      `CameraControls.apply` (`cayleyscene.py:71`) and anywhere else a gacalc
      coefficient feeds numpy/GL. mvp already uses `float(...)` at some GL
      boundaries (e.g. `mathutils.py:265`) — extend that consistently. This
      unblocks the demos regardless of what gacalc returns.
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
- [ ] **Re-verify** every mvpViz demo's focus + camera path (esp.
      modelviewperspectiveprojection / modelvieworthoprojection, which invert
      matrices) after the fix.
- [ ] **Regression guard.** Add a headless test: build a `rotate_z`-containing focus
      path, `to_matrix`, assert `dtype == float` and that `np.linalg.inv` succeeds.
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
