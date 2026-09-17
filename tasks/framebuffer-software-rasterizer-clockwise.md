# Software rasterizer: framebuffer in perspective + clockwise winding test

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 5
**Started:** 2026-09-17 (William Emerison Six <billsix@gmail.com>) — split out from
`tasks/archive/2026/09/17/framebuffer-in-perspective.md` on its completion.

## BLUF

The original 2026-08-27 one-liner behind the (now-complete) framebuffer bracket task —
*"Make framebuffer in perspective, make it configurable, show at last stage, with test for
clockwise like in the notebook"* — had a **software-rasterizer** angle that the interactive
mvpvisualization bracket did not cover. This task is that remainder: the software rasterizer
(`src/modelviewprojection/framebuffer/softwarerendering.py`) and its winding-predicate notebook.
It is unstarted and gated on the maintainer confirming it is still wanted (Q6 of the original
task).

## Context

- The interactive perspective visualization got its framebuffer↔NDC bracket in
  `tasks/archive/2026/09/17/framebuffer-in-perspective.md` (the retargeted work). That was a
  *different subsystem* from the software rasterizer, and the "test for clockwise" part was never
  in scope there — hence this split-out.
- Software rasterizer: `src/modelviewprojection/framebuffer/softwarerendering.py`; its driving
  notebook is `src/modelviewprojection/notebooksrc/framebuffer.py` (a book toctree page between
  ch02–03).
- Winding predicates `is_clockwise` / `is_counter_clockwise` live in the rasterizer path; unit
  tests exist at `tests/test_mathutils.py:208-214`, and a clockwise regression was fixed in
  archived `2026/05/26/fix-is-clockwise-recursion.md`.
- Reference: `tasks/reference/notable-subsystems.md §1` (rasterizer design),
  `tasks/reference/book-figures-and-images.md §3` (notebook pipeline).

## Open questions

1. **Is this still wanted at all?** The interactive bracket may have satisfied the maintainer's
   intent. Confirm before any code — if not wanted, archive this as declined.
2. **What "framebuffer in perspective" means for the software rasterizer specifically** (as
   opposed to the interactive demo already built) — the concrete deliverable is undefined until
   Q1 is a yes.
