# Plan: fix mathutils LaTeX-repr bugs + error-string typos

**Status:** PARTIAL — items 1 (`uniform_scale` inverse LaTeX) & 3 ("Not invertible") done, committed `5f38f18` (2026-05-27); item 2 (`scale_non_uniform_2d/3d` malformed LaTeX) still TODO. **Type:** code (mathutils).
**Found during:** ch07–09 / ch10–12 drift audit. All verified by reading the source.

## Context
`InvertibleFunction` carries `latex_repr` / `latex_repr_inv` strings used to
render the transformation's math (and they will flow into the `inlinetex`
pipeline). Three of the scale functions have wrong or malformed LaTeX, and two
error messages have a typo. These are latent because nothing renders or tests
the inverse LaTeX yet.

## Bugs + fixes (`src/modelviewprojection/mathutils.py`)

1. **Line 615 — `uniform_scale` inverse LaTeX is wrong.**
   `inv_str: str = f"S_{{{-m}}}"` renders the inverse of scale-by-`m` as
   `S_{-m}` (negation) instead of `S_{1/m}` (reciprocal — which is what `f_inv`
   actually computes: `vector * (1.0/m)`). Fix to render the reciprocal, e.g.
   `f"S_{{1/{m}}}"` (or `S_{{{1.0/m}}}` if a numeric literal is preferred).

2. **Line 638 — `scale_non_uniform_2d` inverse LaTeX is malformed.**
   `f"S_{{<\\\frac{{1}}{{{m_x}}},\\\frac{{1}}{{{m_y}>}}"` has two defects:
   (a) `\\\frac` in an f-string is backslash + `\f` (a form-feed control char) +
   `rac`, not `\frac`; (b) the `>` is inside the brace group `{{{m_y}>}}` so it
   renders `\frac{1}{m_y>}` with the `<…>` never closed. Rewrite as a clean
   `S_{<\frac{1}{m_x},\frac{1}{m_y}>}` — use a raw f-string or double-escape
   correctly. **Check `scale_non_uniform_3d` (~line 728+) for the same pattern.**

3. **Lines 629 and 728 — error message typo.** Both read
   `"Note invertible.  Scaling factors cannot be zero."` → should be **"Not
   invertible."** (Line 610 in `uniform_scale` already has the correct wording —
   match it.)

## Verification
- `cd /mvp && python -c "from modelviewprojection.mathutils import uniform_scale, scale_non_uniform_2d; print(uniform_scale(2).latex_repr_inv); print(scale_non_uniform_2d(2,4).latex_repr_inv)"`
  and eyeball the strings (I can run this — no display needed).
- Optionally render the two LaTeX strings through the project's TeX path locally
  to confirm they compile (Bill, since `texExpToPng` isn't in my container).
- `pytest` + `ruff` stay green (no signature changes).
</content>
