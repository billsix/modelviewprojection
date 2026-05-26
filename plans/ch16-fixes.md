# Plan: ch16 (jump to 3D) fixes

**Status:** planned. **Type:** book prose + caption. **Effort:** small.
**Source:** ch16–18 drift audit (verified caption + name refs).

## Findings + changes (`book/docs/ch16.rst`)
1. **Line 194 — caption missing `.py`.** `:caption:
   src/modelviewprojection/mathutils` → `…/mathutils.py`.
2. **Line 184 — wrong name.** "through the `modelspace_to_ndc` method" — the
   FunctionStack method is **`modelspace_to_ndc_fn`**. → handled in
   `plans/fix-method-vs-function-wording.md`; listed here for completeness.
3. **Line 231 — `camera_space_to_ndc_space_fn`** vs mathutils
   **`cs_to_ndc_space_fn`** → also in the method-vs-function plan (verify whether
   a local wrapper uses the long name before changing).
4. **Line ~267 — broken/short sentence** (flagged in `TODO.org`: "Fix spacing on
   line 267 section"). The sentence ends mid-clause ("…the current space"). Finish
   the sentence / fix spacing. Confirm intended wording with Bill.

## Related (other plans)
- e_1/e_2/e_3 used but unexplained in ch16 → `plans/book-explain-natural-basis.md`.

## Verification
`grep -n "modelspace_to_ndc\b\|mathutils$" book/docs/ch16.rst`; read line 267 in
context. Bill renders via `make html`.
</content>
