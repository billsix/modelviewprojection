# Plan: explain the natural basis (`e_1`/`e_2`/`e_3`) in the book

**Status:** complete — 2026-05-27.
**2D:** `define vector2d basis` doc-region in `mathutils.py` (`e_1`/`e_2`/`zero`)
+ a "The Natural Basis" subsection in `ch05` (before paddle instantiation)
introducing them and the `a*e_1 + b*e_2` form (scalar·vector via `__rmul__` +
addition via `__add__`).
**3D:** `define vector3d basis` doc-region + a note in `ch14` (after the
`Vector3D` class) introducing `e_3` along z and the `a*e_1 + b*e_2 + c*e_3` form.
Verified: doc-region integrity clean across ch01–21, `pytest` 47/47.
**Type:** book prose + mathutils doc-region markers.
**Effort:** medium (writing, in Bill's voice). **Headline drift item.**
**Source finding:** `tasks/book-code-drift-ch1-6.md` item B2; `TODO.org` line 1
("make code explannations for e_1, e_2, e_3").

## Context
The code defines the natural-basis unit vectors as static methods —
`Vector1D.e_1()`, `Vector2D.e_1()/e_2()`, `Vector3D.e_1()/e_2()/e_3()` — plus
`.zero()` on each, at `src/modelviewprojection/mathutils.py:210-258`. The
demos lean on them: `demo05.py:36-37` binds `e_1 = Vector2D.e_1()` /
`e_2 = Vector2D.e_2()` and defines every paddle vertex as a linear combination
(`-0.1 * e_1 + -0.3 * e_2`, …); `demo06.py` does the same in modelspace
(`-1 * e_1 + -3 * e_2`). Those exact lines are pulled into **ch05** ("Instantiation
of the Paddles") and **ch06** (~line 717). But the prose **never** introduces
`e_1`/`e_2`, "natural basis", scalar·vector, or vector addition at that point —
the reader meets `Vector2D.e_1()` cold. (`mathutils.py:471,531` docstrings
already use the term "natural basis".)

This is the pedagogically important one: the whole point of the course is
building vectors from composable pieces, and the basis is where "a vector is a
scaled sum of `e_1`/`e_2`" should click.

**Scope note (from the ch7–21 audit, 2026-05-27):** this omission is not local to
ch05/06 — `e_1`/`e_2`/`e_3` are used unexplained in essentially every demo
through ch18 (ch07, ch10–12, ch16–18 all confirmed). Introducing the 2D basis in
ch05/06 (below) resolves the bulk; add the 3D `e_3` introduction at the ch16 jump
to 3D. This single plan closes the "natural basis" omission listed in all three
drift trackers (`tasks/book-code-drift-ch1-6.md`, `…-ch7-15.md`, `…-ch16-21.md`).

## Changes

### 1. Add doc-region markers in `mathutils.py` so the methods can be shown
Wrap the basis + zero static methods so a `literalinclude` can pull just them.
Suggested labels (one set per dimension, or a single 2D set if we only show 2D):
- around `Vector2D.e_1()/e_2()/zero()` (`mathutils.py:226-235`):
  `# doc-region-begin define natural basis 2d` … `# doc-region-end …`
- optionally the same around the `Vector3D` set (`:245-258`) for a later 3D chapter.
Markers are comments only — no behavior change.

### 2. New subsection in `ch05.rst` ("Instantiation of the Paddles", ~line 148)
Before the paddle-instantiation `literalinclude`, add a short subsection that:
- introduces `e_1`/`e_2` as the **natural basis** — the unit step along x and y
  (tie to Bill's number-line framing: `e_1` is "one unit in x");
- shows them via the new `literalinclude` region;
- explains `scalar * e_1` (reuse of the `__rmul__`/`__mul__` already covered in
  `mathhomework1.rst`) and that adding scaled basis vectors reconstructs any
  vector: `(a, b) == a * e_1 + b * e_2`;
- explains `.zero()` as the origin / additive identity.
Then the existing bullet ("vertices are now defined as relative distances…")
reads naturally. Keep Bill's voice: coordinate-free intuition first, coordinates
"for when the work has to get done."

### 3. One-line callback in `ch06.rst` (~line 730)
The existing bullet "paddles are using modelspace coordinates instead of NDC" can
gain a half-sentence noting the vertices are the same `a * e_1 + b * e_2` form,
now in modelspace units — no need to re-teach.

## Notes / decisions to confirm with Bill
- **Scope:** introduce only 2D (`e_1`/`e_2`) in ch05/06; defer `e_3` to the 3D
  chapter (ch16+)? Recommended — matches the demo arc.
- Whether to also add a small figure (the two basis arrows at the origin). Bill's
  `TODO.org` ch06 list already wants "add colored components mult by (1,0) and
  (0,1)" — this overlaps; coordinate so we don't double-author.

## Verification
- Prose-only + comment-marker change → `pytest` and `ruff` still green.
- New `literalinclude` region resolves (no "Cannot find region" Sphinx error):
  verify the `start-after`/`end-before` labels match the markers exactly. I
  cannot run the doc build (`texExpToPng` absent), so Bill confirms via
  `make html` that the new region renders and the basis section reads well.
</content>
