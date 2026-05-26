# Plan: fix `is_clockwise` infinite recursion (+ test)

**Status:** complete
**Completed:** 2026-05-27 — fix + regression test `test_vec2_is_clockwise`; committed `5f38f18`.
**Type:** code bug (mathutils).
**Source finding:** `tasks/book-code-drift-ch1-6.md` item A1.

## Context
While auditing ch1–6 for doc/code drift I found a real code defect unrelated to
prose. `is_clockwise` calls itself instead of negating `is_counter_clockwise`,
so any call recurses until the stack overflows. It is not currently pulled into
any chapter (its `doc-region clockwise` marker is unused in ch1–6), and no test
exercises it, so it has stayed hidden. `is_counter_clockwise` and `is_parallel`
both have tests; `is_clockwise` does not.

## Change
`src/modelviewprojection/mathutils.py:705`
```python
# before
def is_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return not is_clockwise(v1, v2)
# after
def is_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return not is_counter_clockwise(v1, v2)
```
Keep the surrounding `doc-region-begin/end clockwise` markers intact.

## Test (new)
Add to `tests/test_mathutils.py` next to `test_vec2_is_counter_clockwise`
(~line 379). Using the natural basis: `e_2` is CCW from `e_1`.
```python
def test_vec2_is_clockwise():
    e_1, e_2 = Vector2D.e_1(), Vector2D.e_2()
    assert not is_clockwise(e_1, e_2)   # e_2 is counter-clockwise from e_1
    assert is_clockwise(e_2, e_1)       # e_1 is clockwise from e_2
```
Confirm `is_clockwise` is imported in the test module's import block (the file
already imports the other predicates).

## Verification
- `cd /mvp && pytest tests/test_mathutils.py -k clockwise -q` — both the new
  test and the existing CCW test pass. (I can run this; pytest needs no display.)
- `ruff check src/modelviewprojection/mathutils.py tests/test_mathutils.py`.
- Note: `entrypoint.sh` runs `pytest --exitfirst` at the top of the book build,
  so this also de-risks the build.
</content>
