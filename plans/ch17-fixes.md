# Plan: ch17 (camera rotation) fixes

**Status:** PARTIAL — wrong demo ref :41 ("demo17"→"demo18") fixed & staged 2026-05-27. Still open: explain `push_transformation` + `rotate_x/y/z` (item 2/3) and the diagrams (item 4). **Type:** book prose + content gaps.
**Source:** ch16–18 drift audit.

## Findings + changes (`book/docs/ch17.rst`)
1. **Line 41 — wrong demo reference.** "This will be fixed in demo17." but we are
   *in* demo17; perspective arrives in **demo18**. → "fixed in demo18".
2. **Content gap: `push_transformation` context manager unexplained.** demo17
   switches from demo16's manual `fn_stack.push()`/`fn_stack.pop()` to
   `with push_transformation(...):` (demo17.py ~248-309), a significant
   pedagogical shift that the prose never introduces. Add an explanation where the
   first `with` block appears.
3. **Content gap: `rotate_x`/`rotate_y`/`rotate_z` unexplained.** Used in demo17
   (imports ~35-37) but never named in prose; the chapter says "rotate around the
   x axis" without connecting to `rotate_x(...)`. Introduce them by name.
4. **Diagrams (TODO.org): "Fix two diagrams" + "Add third diagram."** ch17 has
   only 3 `figure` directives and no math diagrams; the camera-rotation geometry
   wants a diagram. Asset work — coordinate with Bill.

## Related
- e_1/e_2/e_3 omission → ✅ done, see `tasks/archive/book-explain-natural-basis.md`.
- `camera_space_to_ndc_space_fn` name ref (line 310) → ✅ done, see `tasks/archive/fix-method-vs-function-wording.md`.

## Verification
Read the demo17 `with push_transformation` blocks alongside the prose to place
the explanation. Prose/asset only. Bill renders via `make html`.
</content>
