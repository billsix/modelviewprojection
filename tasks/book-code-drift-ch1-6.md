# Task: book ↔ code drift in chapters 1–6

**Status:** investigation done (2026-05-26); fixes not yet made.
**Goal:** find places where `book/docs/ch0[1-6].rst` (+ `mathhomework1.rst`) prose
has drifted from the current code, after several months of commits. The
`literalinclude` code snippets are always live; the *prose around them* is what
goes stale.

## How chapters reference code (so you know what can drift)
Chapters pull code with `.. literalinclude:: <path>` + `:start-after:
doc-region-begin <label>` / `:end-before: doc-region-end <label>`. The included
snippet is always current. **Verified: no broken/missing doc-region labels in
ch01–06** (the inclusion wiring is sound). All drift below is in prose, captions,
or hand-written doctest blocks — none of which the build keeps in sync.

---

## A. Verified code bugs (fix in code, not just docs)

1. **`src/modelviewprojection/mathutils.py:705` — `is_clockwise` infinite
   recursion.** `def is_clockwise(...): return not is_clockwise(v1, v2)` calls
   itself → stack overflow. Should be `return not is_counter_clockwise(v1, v2)`.
   Has a `doc-region clockwise` marker (not currently pulled into any ch1–6, so
   no chapter shows the bug, but any caller crashes). No unit test covers it
   (`test_mathutils.py` has `is_parallel`/`is_counter_clockwise` tests but not
   `is_clockwise`).

## B. Verified doc↔code mismatches (the meat of this task)

2. **The natural-basis vectors `e_1`/`e_2`/`e_3` are never explained anywhere.**
   *(This is the low-hanging fruit Bill called out, and TODO.org line 1:
   "make code explannations for e_1, e_2, e_3".)*
   - Code: `Vector1D.e_1()`, `Vector2D.e_1()/e_2()`, `Vector3D.e_1()/e_2()/e_3()`
     (static methods returning unit vectors), plus `.zero()` on each class, in
     `mathutils.py:210-258`. Docstrings at `mathutils.py:471,531` even say
     "natural basis".
   - Books: **0 occurrences** of `e_1`/`e_2`/`e_3`/"natural basis"/"basis
     vector" across ch01–06, mathhomework1, perspective.
   - Yet the demos *use* them prominently: `demo05.py`/`demo06.py` instantiate
     paddle vertices as `-1 * e_1 + -3 * e_2` etc., and those exact lines are
     pulled into **ch05.rst** ("instantiate paddles") and **ch06.rst:717-723**.
     So the reader sees `Vector2D.e_1()` used with no introduction of what it is,
     no explanation of scalar-times-vector or vector addition at that point.
   - Fix shape: introduce `e_1`/`e_2` (and `.zero()`) where paddle vertices are
     first defined as linear combinations — ch05/ch06 — tying it to the vector
     `+` and scalar `*` operators.

3. **`ch05.rst:100` — wrong caption.** The `literalinclude` pulls from
   `../../src/modelviewprojection/mathutils.py` (the Vector class), but
   `:caption:` reads `src/modelviewprojection/demo05.py`. Caption should name
   `mathutils.py`.

4. **`ch05.rst:104-126` — false prose + non-runnable doctests.**
   - Prose (line ~104): "We added a translate method to the Vector class." There
     is **no** `.translate()` method on `Vector`. `translate(b)` is a
     module-level function (`mathutils.py:581`) returning an `InvertibleFunction`
     (it wraps `vector + b`).
   - Two `.. code:: Python` doctest blocks (lines ~110-126) do
     `from modelviewprojection.mathutils import Vector` then call
     `demo.Vector(x=1,y=2)` (undefined name `demo`) and `a.translate(...)`
     (nonexistent method). Neither runs. Correct usage:
     `translate(Vector2D(3,4))(Vector2D(1,2))`.
   - This is also a missed teaching moment: `translate` *is* vector addition
     wrapped as an invertible function — never stated.

## C. Verified prose typos (ch02/ch03), all real

5. `ch02.rst:77` "is a function sets" → "is a function that sets".
6. `ch02.rst:79` "Lets make" → "Let's make".
7. `ch02.rst:189` "the the programmer" → "the programmer".
8. `ch02.rst:464` "directed edge that you against." → sentence is truncated/broken.
9. `ch03.rst:185` "existing class to glClearColor" → "existing **call** to".
10. `ch03.rst:232` "mapped the the region" → "mapped **to** the region".

## D. Withdrawn — not actually drift (premise was wrong)

An earlier note suspected **ch06** of failing to explain `rotate`/`sine`/
`cosine`/etc. **This is not drift.** ch06 is titled **"Modelspace - Demo 06"**;
rotation is the subject of **ch07 ("Rotations - Demo 07")**, so ch06 correctly
defers it. The only ch06 issue is the unexplained basis usage, already covered
by item B2. (`rotate`'s elegant parallel/perpendicular decomposition is worth a
look in ch07+, but that's outside the ch1–6 scope and not tracked here.)

## Per-finding plans (one each, in `plans/`)
- A1 → [`archive/fix-is-clockwise-recursion.md`](archive/fix-is-clockwise-recursion.md) — ✅ DONE (committed 2026-05-27)
- B2 → [`../plans/book-explain-natural-basis.md`](../plans/book-explain-natural-basis.md) (headline)
- B3 + B4 → [`archive/ch05-translate-section-fixes.md`](archive/ch05-translate-section-fixes.md) — ✅ DONE (committed 2026-05-27)
- C → [`archive/ch02-ch03-prose-typos.md`](archive/ch02-ch03-prose-typos.md) — ✅ DONE (committed 2026-05-27)

## Suggested order when fixing
B2 (natural basis — the headline) → A1 (one-line code bug + a test) →
B3/B4 (ch05 caption + doctests) → C (typos, trivial).

## Notes
- I can edit code/rst and `git add` to stage, but **cannot commit** (Bill signs
  outside the container) and **cannot run the doc build** (`texExpToPng` absent).
- See `tasks/codebase-overview.md` for how the build/repo is wired.
</content>
