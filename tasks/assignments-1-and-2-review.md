# Assignments 1 and 2 — decide their direction, then modernize the scaffold

**Status:** **DONE — closed 2026-09-09.** All four student-facing files are updated; the
remaining items are the two cross-cutting questions at the foot of this doc (solution management,
book cross-references), which are Bill's to answer and are not per-assignment work.
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
  `git show 3c161dfa:tasks/adhoc/assignments-review/verify.sh` (likewise `render_probe.py`) — it
  is the only headless way to prove one of these scripts renders, and it was used to gate all of
  assignment 1, 2 and 3. What it does and why is summarized in the archived task. **Two things to
  know if you recover it:** the version at that SHA prints the camera assuming demo18's 3-D shape
  (`position.z`, `rot_y`, `rot_x`) and so raises `AttributeError` on a 2-D `g2` camera — iterate
  `camera.position_ws` and `getattr`-guard the angles instead; and it treats a single-colour frame
  as failure, which is right for a demo but **wrong for assignment 2**, whose correct unsolved
  state is an empty window.
- **Both of these are harder to re-sync than assignment 3 was**, for different reasons — see below.

## Assignment 1 — `assignments/assignment1.py` — DONE 2026-09-09

**What it actually is (and this reframes the whole thing):** not a fill-in-the-blank exercise like
assignment 3, and not a copy of any demo. `book/docs/programmingproj1.rst` opens with *"Draw
whatever you'd like in NDC. The following from assignments/assignment1.py should get you started
with a bunch of example code."* — so it is a **worked-example gallery**: seven complete drawing
functions (quadrilateral, precomputed x², a generic `plot(fn, domain, interval)`, (x−½)², an
oscillating triangle, a lambda-plotted cosine, a circle), all called from the loop. There is no
hole to preserve and nothing to re-sync against.

**Correction to what this doc first said:** it claimed the GL boilerplate "is inside published
regions", and that was the stated reason to leave the file alone. **That was wrong.** All eight
`doc-region` markers start at `:90`; the local `on_key` and `draw_in_square_viewport` copies sit at
`:44-84`, *above* every marker. Swapping them for the shared helpers therefore has **no book
impact at all** — it was the safe change, not the risky one. (All eight markers are published, so
anything *inside* a region is a different matter — see below.)

**Done:**

1. **The shared helpers replace the local copies** — `from modelviewprojection.util.windowing
   import on_key` and `...util.clipping import draw_in_square_viewport`, matching every demo and
   what assignment 3 now does. The call site becomes `draw_in_square_viewport(window)`; that line
   *is* inside the published `event loop` region, but it is the same one-word change the 2026-06-01
   clipping dedup already made to 21 demos, and `:lineno-match:` reprints it automatically. Deletes
   ~30 lines, and takes the `min = ...` builtin shadow with it.
2. **A real doc bug fixed: the book called a quadrilateral a triangle.** The marker
   `doc-region-begin draw a triangle` wrapped `def draw_a_quadrilateral()`, which draws
   `GL_QUADS` — and the chapter rendered it under a **"Draw a triangle"** heading with the prose
   *"Draw a triangle that doesn't move"*. The code was the honest part, so the marker and the book
   were changed to say quadrilateral, not the other way round: zero pixels move, and the page stops
   contradicting its own listing. Marker renamed in both the `.py` and the two anchors in
   `programmingproj1.rst`, plus the heading and the sentence.
3. **A wrong output in a published comment fixed.** Inside the `generic plot function` region, the
   worked example read `>>> np.arange(.0,1.0,.2)` → `array([. , .2, .4, .6, .8])`. numpy prints
   `array([0. , 0.2, 0.4, 0.6, 0.8])` (checked). Input and output are both conventional now.

**Verified:** `ruff check` + `ruff format --check` clean; `py_compile` clean; **`check_doc_regions.py`
green in-container** (all anchors resolve, no collisions, no empty regions — the renamed anchor
lines up); and rendered before/after in the project image with the recovered harness. Every drawn
pixel is identical — five colours at 7500 / 7191 / 2551 / 497 / 435 counts, unchanged.

**The one visible change, deliberate:** the background goes from pure black to the demos' dark blue
`(0.0289, 0.071875, 0.0972)`, because the shared `util.clipping.draw_in_square_viewport` clears to
that while the local copy cleared to black. It makes the assignment match every demo in the course.
If it is unwanted the revert is to keep a local copy of that helper — but then the duplication is
back, so the honest fix would be a parameter on the shared one.

**Not done, and deliberately:** `tasks/graphing-calculator-2d-3d.md` still wants to *grow* this
file's `plot()` into a graphing calculator, and its open question 1 ("grow assignment1 in place, or
a new standalone program?") is untouched by the above — the cleanup neither helps nor blocks it.
Answer that there.

## Assignment 2 — `assignments/assignment2-screenspace.py` — DONE 2026-09-09

**The exercise is the two `ndc_to_screenspace_*` methods, and they were stubs** — both were
`return self`. This doc previously described them as the exercise's teaching *content*, which
implied they were written; they were not. So the file has the same shape as assignment 3: a working
scene with a hole, except here the hole is load-bearing enough that **nothing renders at all** until
the student fills it (NDC coordinates fed to a `gluOrtho2D(0, width, 0, height)` projection land
within a pixel of the corner). Verified: the pre-change file renders one flat background colour.

**What it is now:** demo11's scene and demo11's pipeline — `compose([uniform_scale(m=1/10),
inverse(translate(b=camera.position_ws)), compose([translate(b=paddle.position),
rotate(paddle.rotation)])])` — with the NDC→screen step removed. That is exactly what the
assignment always was; demo11 just reaches the screen via `draw_in_square_viewport` instead, so the
two now differ by precisely the thing being taught.

**Done:**

1. **`Vertex` → `gacalc.g2.Vector`**, and the transforms come from the course
   (`gacalc.transforms.translate` / `uniform_scale` / `compose` / `inverse`,
   `mathutils.rotate`), matching demo11 line for line. `colorutils.Color3` replaces the loose
   `r`/`g`/`b` floats; `util.windowing.on_key` replaces the local copy.
2. **The two stubs became free functions**, `ndc_to_screenspace_full_screen(ndc, width, height)`
   and `..._aspect_not_distorted(...)` — **forced, not preferred**: gacalc's `Vector` is
   `@typing.final` and frozen, so a student cannot hang a method on it. Free functions are also the
   course idiom (`mathutils`). Each keeps its `return ndc` hole under a `TODO`, with a docstring
   saying what the mapping must achieve without giving the formula.
3. **Frozen-vector rebinding** — `camera.position_ws.y += 1.0` and the paddle equivalents became
   `camera.position_ws += e_2` etc., the pattern every demo uses since gacalc 0.0.14.
4. **Dropped:** `from __future__ import annotations  # to appease Python 3.7-3.9` (floor is 3.13),
   the duplicated per-paddle `if KEEP_ASPECT_RATIO` branch (picked once per frame now), and a
   `minimum_framebuffer_dimension` that no longer had a reader — it was computed in the event loop
   where the mapping functions cannot see it, so pointing a student at it would have been a false
   hint; the header comment says "the smaller of width and height" instead.
5. **A header comment explains that an empty window is the expected starting state**, so nobody
   reports the assignment as broken. The exercise design itself is untouched.

**Verified:** ruff + format + `py_compile` clean; renders flat (correct) unsolved; and a solved
copy — both mappings implemented — renders the two paddles at 7500 px each, purple at x=−9 and
yellow at x=+9, matching demo11's scene.

## `assignments/demo02/vec1.py` — DONE 2026-09-09, and it was BROKEN

**This file could not run.** It opened with `from modelviewprojection.mathutils import
InvertibleFunction, Vector1, compose, inverse, translate, uniform_scale` — and `mathutils` stopped
re-exporting every one of those names on **2026-08-13**, when it was de-faced
(`tasks/archive/2026/08/13/defacade-mathutils-gacalc-reexports.md`). Confirmed in the project image:
`ImportError: cannot import name 'Vector1' from 'modelviewprojection.mathutils'`. It has been dead
for nearly a month, and **it is book-published** (`mathhomework1.rst`, 22 doc-region markers), so
the book has been showing code that cannot execute. This doc had it listed as "already migrated;
needs nothing" — wrong, and worth remembering as a lesson: an import line naming `mathutils` was
taken as evidence of being current, when it was the exact symptom of being stale.

Three eras of drift, all fixed:

- **imports** → `from gacalc.g1 import Vector, e_1` and `from gacalc.transforms import ...`.
- **`Vector1(x)` → `x * e_1`** — gacalc dropped the dimension suffix in 0.0.16, and the house rule
  is to build from the basis constants with every coefficient explicit. A markdown cell now
  introduces `e_1` before its first use, since a 1-D vector as `2.0 * e_1` is the notebook's first
  new idea.
- **`.is_close(...)` → `.isclose(..., rel_tol=1e-5, abs_tol=1e-5)`** — renamed in gacalc 0.0.15,
  where the tolerances also became `0.0`, i.e. exact. A bare `.isclose(x)` would have compared
  floats exactly and failed; a markdown cell explains why the tolerances are spelled out.
- Annotations are `InvertibleFunction[Vector]`, not bare (a bare generic degrades its parameter to
  `Any`).

**Verified in the image:** the notebook now runs every cell and stops precisely at the first assert
of the `work to do` region — the exercise hole, exactly as intended — where before it died at the
import. A solved copy (`fahrenheit_to_kelvin = compose([celsius_to_kelvin, fahrenheit_to_celsius])`,
`celsius_to_fahrenheit = inverse(fahrenheit_to_celsius)`, `kelvin_to_fahrenheit =
inverse(fahrenheit_to_kelvin)`) passes every assert. **`check_doc_regions.py` is green** — all 22
marker names were kept identical, so `mathhomework1.rst` needed no edit and its listings pick up the
new code automatically.

## Also in scope, unchanged from the original task

- **Solution management** — are these handed out as-is for students to fill in, and if so where do
  reference solutions live? Unanswered since 2026-07-09, and it applies to all three assignments
  including the now-finished assignment 3.
- **Book cross-references** — should a chapter point at the matching assignment where the concept
  lands? Also unanswered.

## Open questions

1. **Solution management** — where do reference solutions live, for all three assignments?
2. **Book cross-references** — should chapters link to the assignment that exercises them?

## Related

- `tasks/archive/2026/09/09/assignments-review.md` — the parent task; assignment 3's record and the
  method to copy.
- `tasks/graphing-calculator-2d-3d.md` — overlaps assignment 1 directly (question 1).
- `tasks/reference/demo-chapter-inventory.md` §5 — which assignments the book publishes.
