# Plan: ch10 (camera / inverse) fixes

**Status:** complete — all items done 2026-05-27:
3 prose typos (:120,:131,:257); `camera.x/y`→`camera.position_ws` (:363,:381);
and the 4 "inverse" code blocks (~:149-216) rewritten from the bogus
`v.translate(...)`/`v.scale(...)` method-chaining API (undefined `Vector`, free
vars, a missing paren) into **genuine runnable doctests**: each builds its
vectors from the natural basis (`e_1`/`e_2`) and proves the hand-written inverse
matches the built-in `inverse()` (via `.isclose()` for float-robustness). The
sequence case shows `compose([f1, f2])` ⇒ `compose([inverse(f2), inverse(f1)])`,
matching the `(A*B)⁻¹ = B⁻¹*A⁻¹` note above it. Verified: `python -m doctest
book/docs/ch10.rst` passes (ch05 too). **Type:** book prose + doctests.
**Source:** ch10–12 drift audit (verified: `camera.x/y` prose; doctest blocks).

## Findings + changes (`book/docs/ch10.rst`)

1. **Lines 363, 381 — wrong field names.** Both say "The camera's position is at
   `camera.x`, `camera.y`." The `Camera` dataclass (demo10.py) has a single field
   **`position_ws: Vector2D`** (used as `camera.position_ws`); there is no
   `camera.x`/`camera.y`. Rewrite to `camera.position_ws` (and its `.x`/`.y`
   components if needed).

2. **Lines ~149-216 — hand-written code blocks that won't run.** Several
   `.. code:: Python` blocks present a **method-chaining API that doesn't exist**:
   `v.translate(x,y)`, `v.rotate(theta)`, `v.scale(x,y)`, and a chained
   `v.scale(...).translate(Vector(...))`. Problems: `Vector2D` has no such
   methods (these are module functions returning `InvertibleFunction`s);
   `Vector` is undefined (should be `Vector2D`); free variables `x`/`y`; and
   **line ~216 is missing a closing `)`**. Replace with runnable examples using
   the real API — function composition, e.g.
   `compose([scale_non_uniform_2d(...), translate(Vector2D(...))])(v)` — and run
   them to capture true output. This overlaps the "method vs function" framing
   (`tasks/archive/fix-method-vs-function-wording.md`) but the fix here is rewriting
   executable examples, so keep it in this plan.

3. **Typos.** Line 120 "Imagine you a driving" → "you are driving"; line 131
   "following the the direction of each edges" → "the direction of each edge";
   line 257 "Bill, you said the the inverse" → "the inverse".

## Verification
- Run each rewritten example: `cd /mvp && python -c "..."` to confirm it executes
  and to capture the real repr before pasting into prose. (I can run these.)
- `grep -n "camera\.x\|the the\|you a driving" book/docs/ch10.rst` → empty after.
- Bill renders via `make html`.
</content>
