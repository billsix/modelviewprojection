# Assignments 1 and 2 — decide their direction, then modernize the scaffold

**Status:** proposed — needs go-ahead on the direction per assignment
**Priority:** 6
**Difficulty:** 4
**Created:** 2026-09-09, carrying the unfinished half of `assignments-review.md` (archived
`tasks/archive/2026/09/09/assignments-review.md`) when assignment 3 was finished and that task
closed. The questions below are the originals, from Bill 2026-07-09: *"Take a look at the
assignments, and see how they should be updated relative to the other demos."*

## BLUF

`assignments/assignment3-strafe.py` was re-synced onto demo18 on 2026-09-08 and is done. The other
two student-facing assignments still carry pre-migration code, but **neither is a mechanical
re-sync the way assignment 3 was** — each needs a decision first, and they are different decisions.
Done = each assignment either modernized, re-scoped, or explicitly left alone with the reason
recorded.

## Context — read first

- **The precedent is `tasks/archive/2026/09/09/assignments-review.md`.** It records how assignment 3
  was handled: identify the demo it came from, re-sync onto that demo's *current* source, keep the
  exercise hole exactly where it was, and prove the result with the harness. Read its "Assignment 3
  — done" section before touching these two; the decisions taken there (hand the student the course
  vocabulary; keep the hole; drop dead scaffolding) are the template, not law.
- **The verification harness is gone from the tree but recoverable.** `verify.sh` +
  `render_probe.py` lived at `tasks/adhoc/assignments-review/`, were used to gate assignment 3, and
  were `git rm`'d with that task's archive (the sanctioned one-shot lifecycle). Recover with
  `git show 3c161dfa:tasks/adhoc/assignments-review/verify.sh` (likewise `render_probe.py`) if
  either of these assignments gets the same treatment — **it is worth recovering**, since it is the
  only headless way to prove one of these scripts renders. What it does and why is summarized in
  the archived task.
- **Both of these are harder to re-sync than assignment 3 was**, for different reasons — see below.

## Assignment 1 — `assignments/assignment1.py`

**The complication: it is BOOK-PUBLISHED.** It carries 16 `doc-region` markers and is
`literalinclude`d by `book/docs/programmingproj1.rst`
(`tasks/reference/demo-chapter-inventory.md` §5). So unlike assignment 3, editing it **changes a
printed page**, and any marker moved or renamed changes what that page shows.

**Its actual drift is mild.** It has **no** bespoke vector class — it is a 2D function plotter over
raw immediate-mode GL and numpy, with a real arbitrary-function `plot(fn, domain, interval)` at
`:177-191`. It does not use the vector/transform vocabulary at all, so the gacalc migration mostly
passed it by.

**Questions:** is there anything to change here beyond leaving it alone? If the answer is "modernize
the GL boilerplate to match the demos", note that the boilerplate is inside published regions.

**Related and NOT the same thing:** `tasks/graphing-calculator-2d-3d.md` proposes *growing* this
file's `plot()` into a graphing calculator — its open question 1 is exactly "grow assignment1 in
place, or a new standalone program?", and it flags the same book-published constraint. **Answer
that one and this one together**, or the two will contradict each other.

## Assignment 2 — `assignments/assignment2-screenspace.py`

**The complication: its bespoke `Vertex` IS the subject of the exercise.** It carries a hand-rolled
`Vertex` with `translate`/`scale`/`rotate` *plus* `ndc_to_screenspace_full_screen` and
`ndc_to_screenspace_aspect_not_distorted` (`:80-105`) — and those last two are the teaching content
of the exercise (NDC → screen space). Replacing the class wholesale with `gacalc.g2.Vector` would
delete the thing the assignment is about, which is **not** what happened to assignment 3 (there the
bespoke class was incidental scaffolding around a camera exercise).

So the question is narrower: should the *transform* methods (`translate`/`scale`/`rotate`) come
from gacalc while the two screenspace mappings stay hand-written and local? That would put the
student in the course vocabulary without dissolving the exercise.

**Also here:** `from __future__ import annotations  # to appease Python 3.7-3.9` — the repo floor is
3.13/3.14, so the shim and its comment are both wrong. That one is safe to delete regardless of the
direction chosen (this file has no `doc-region` markers and no chapter includes it).

## Also in scope, unchanged from the original task

- `assignments/demo02/vec1.py` — **already migrated**; it imports
  `modelviewprojection.mathutils` and needs nothing. It is book-published
  (`mathhomework1.rst`), so leave it alone unless a decision above forces a change.
- **Solution management** — are these handed out as-is for students to fill in, and if so where do
  reference solutions live? Unanswered since 2026-07-09, and it applies to all three assignments
  including the now-finished assignment 3.
- **Book cross-references** — should a chapter point at the matching assignment where the concept
  lands? Also unanswered.

## Open questions

1. **Assignment 1** — leave alone (recommended: its drift is mild and it is book-published), or
   modernize its GL boilerplate despite the published regions? Coordinate with
   `tasks/graphing-calculator-2d-3d.md`, which wants to grow the same file.
2. **Assignment 2** — take the transform methods from gacalc while keeping the two
   `ndc_to_screenspace_*` methods local and hand-written (recommended), replace the whole class, or
   leave it entirely?
3. **Solution management** — where do reference solutions live, for all three assignments?
4. **Book cross-references** — should chapters link to the assignment that exercises them?

## Related

- `tasks/archive/2026/09/09/assignments-review.md` — the parent task; assignment 3's record and the
  method to copy.
- `tasks/graphing-calculator-2d-3d.md` — overlaps assignment 1 directly (question 1).
- `tasks/reference/demo-chapter-inventory.md` §5 — which assignments the book publishes.
