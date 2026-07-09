# Review the assignments against the modern demos; update or re-scope them

**Status:** proposed — needs go-ahead on the direction per assignment
**Created:** 2026-07-09 (Bill: "Take a look at the assignments, and see how
they should be updated relative to the other demos. For instance, one of
the assignments is just checking to see if they can figure out how to
strafe")

## What's there (survey 2026-07-09)

`assignments/` — four student-facing items, all runnable standalone:

- `assignment1.py` — raw GLFW + immediate-mode GL boilerplate, numpy.
- `assignment2-screenspace.py` — screen-space exercise; carries its own
  hand-rolled `Vertex2D` dataclass (add/translate/scalar-mul).
- `assignment3-strafe.py` — the strafe exercise Bill mentions; also
  carries its own `Vertex2D` with hand-written operators.
- `demo02/` — `vec1.py` + `plot2d.ipynb` (notebook pairing).

## The drift (why they need the look)

The assignments froze while the curriculum moved:

- **Their own vector type**: each ships a private `Vertex2D` with
  hand-rolled `__add__`/`__mul__`/`translate` — pre-dating the gacalc
  migration. The demos' single vector vocabulary is `gacalc.g2.Vector2`
  via `mathutils` (and rotation is now the plane+angle factory). An
  assignment teaching "figure out strafing" on a bespoke vector class no
  longer matches the course the student just read.
- **Stale compat shims**: `from __future__ import annotations  # to
  appease Python 3.7-3.9` — the repo floor is 3.13/3.14.
- **No shared helpers**: raw per-file GLFW/window/viewport boilerplate
  the demos have long since factored (and the ports' `_common.py`
  pattern).
- Newly under gate (2026-07-09): format.sh now ruff-checks/-formats
  `assignments/` (T201 exempted — printed output is the point), so
  they're at least lint-clean; content is the open question.

## Questions to settle per assignment (Bill's call)

1. Keep-as-exercise vs retire: is "can they figure out how to strafe"
   still the right exercise given where the demos are (strafing is
   camera-relative translation — post-gacalc it's one
   `translate(rotate(angle)(offset))` composition)? If kept, should the
   scaffold hand the student `mathutils` (Vector2, translate, rotate)
   instead of a bespoke `Vertex2D`?
2. Which demo does each assignment pair with, and should they live/point
   there (e.g. `demo02/` already mirrors a demo number)?
3. Solution management: are these handed out as-is (students fill in),
   and if so where do reference solutions live?
4. The book: should chapters reference the assignments at the point the
   matching concept lands?

## Suggested shape (once directions are chosen)

Per assignment: modernize the scaffold (gacalc/mathutils vocabulary,
shared window boilerplate, 3.13+ idioms), keep the *exercise* (the thing
the student must figure out) as the deliberately-missing piece, and gate
with format.sh + a definitions-style run (the exercise hole stubbed).
