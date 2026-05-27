# Plan: ch18 (perspective / stack) fixes

**Status:** PARTIAL — "ration"→"ratio" (:225) done; the `:262` perspective-include caption fixed (`demo18.py`→`mathutils.py`); the `:248` Vector-class include was **removed entirely** by the doc-region relabel (see `tasks/archive/ch14-fixes.md`), replaced with a one-line `Vector3D` reference. Still open: the f1/f2/f3 + `Callable` content (item 3). **Type:** book prose + captions + content gaps.
**Source:** ch16–18 drift audit (verified captions).

## Findings + changes (`book/docs/ch18.rst`)
1. **Lines 248 and 262 — wrong captions.** Both `literalinclude`s pull from
   `mathutils.py` (Vector class @248, `perspective` @262) but `:caption:` says
   `src/modelviewprojection/demo18.py`. → set captions to
   `src/modelviewprojection/mathutils.py`. (Same recurring caption bug as ch05.)
2. **Line 225 — typo.** "aspect **ration**" → "aspect **ratio**".
3. **Content gap (TODO.org): f1/f2/f3 + `Callable`.** Event-loop sections
   (~266-287) use bare `f1`/`f2`/`f3` names with no explanation, and `TODO.org`
   asks to "Explain Callable, make example." Add the detail / a `Callable`
   example where these appear.

## Related
- e_1/e_2/e_3 omission, and `push_transformation` (deeply nested in demo18) →
  `tasks/archive/book-explain-natural-basis.md` and `plans/ch17-fixes.md` (introduce the
  context manager in ch17, the chapter where it first appears).

## Verification
Confirm the two captioned includes are indeed from mathutils.py
(`sed -n '244,264p' book/docs/ch18.rst`). `grep -n "ration" book/docs/ch18.rst`
→ empty after. Bill renders via `make html`.
</content>
