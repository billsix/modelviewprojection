# Plan: fix ch05 "translate" section (caption + false "method" prose + broken doctests)

**Status:** planned. **Type:** book prose/correctness. **Effort:** small.
**Source finding:** `tasks/book-code-drift-ch1-6.md` items B3 + B4 (grouped — all
in the one ch05 "Data Structures" section, edited together).

## Context
`ch05.rst` (title: "Add Translate Method to Vector - Demo 05") frames `translate`
as a **method on `Vector`**. That framing is stale: in the current code
`translate(b)` is a module-level function (`mathutils.py:581`) that returns an
`InvertibleFunction` wrapping `vector + b`. There is no `Vector.translate`
method. The chapter's "Data Structures" section has three concrete defects.

## Defects + changes (all in `book/docs/ch05.rst`)

1. **Wrong caption — line 100.** The `literalinclude` (lines 94-100) pulls from
   `../../src/modelviewprojection/mathutils.py` but `:caption:` says
   `src/modelviewprojection/demo05.py`. → change caption to
   `src/modelviewprojection/mathutils.py`.

2. **False prose — line ~104.** "We added a translate method to the Vector
   class." → there is no such method. Rewrite to describe `translate` as a
   top-level invertible function that wraps vector addition (`translate(b)`
   returns a function shifting any vector by `b`). This also sets up ch06, which
   already says "Just like we made a top level invertible function called
   'translate' for addition" (`ch06.rst:694`) — so ch06 is already consistent;
   ch05 is the one out of step.

3. **Non-runnable doctests — lines ~110-126.** Two `.. code:: Python` blocks do
   `from modelviewprojection.mathutils import Vector`, then call
   `demo.Vector(x=1, y=2)` (`demo` is undefined) and `a.translate(...)` (no such
   method). Replace with runnable examples using the real API, e.g.:
   ```python
   >>> from modelviewprojection.mathutils import Vector2D, translate
   >>> shift = translate(Vector2D(x=3, y=4))
   >>> shift(Vector2D(x=1, y=2))
   Vector2D(x=4.0, y=6.0)
   ```
   Keep the existing point about keyword arguments (it's still valid) but anchor
   it to a real constructor call. Confirm the exact `repr` of the result before
   asserting it in prose (run it — see Verification).

## Optional (confirm with Bill)
The chapter **title** "Add Translate Method to Vector" carries the same stale
"method" framing. Consider retitling (e.g. "Add a Translate Function …"). Left
out of the default scope because retitling touches the toctree/cross-refs and is
a bigger editorial call than the in-body fixes.

## Verification
- Run the proposed doctest snippet to capture the exact repr:
  `cd /mvp && python -c "from modelviewprojection.mathutils import Vector2D, translate; print(translate(Vector2D(3,4))(Vector2D(1,2)))"`
  and paste the true output into the prose. (I can run this — no display needed.)
- `ruff` unaffected (rst-only). Bill confirms rendering via `make html`.
</content>
