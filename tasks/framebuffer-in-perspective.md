# Software framebuffer under perspective, configurable, shown as the last stage

**Status:** blocked
**Priority:** 6
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (what "in perspective"/"configurable" mean;
new pytest vs notebook cell).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Make framebuffer in perspective, make it configurable, show at last
stage, with test for clockwise like in the notebook."*

Run the software rasterizer under a perspective transform, make it configurable, show it as the final
pipeline stage, with a clockwise-winding test as in the notebook.

## Context (investigation 2026-08-27)

- Software rasterizer: `src/modelviewprojection/framebuffer/softwarerendering.py`; its driving notebook
  is `src/modelviewprojection/notebooksrc/framebuffer.py` (a book toctree page between ch02–03).
- Winding predicates `is_clockwise`/`is_counter_clockwise` live there; **unit tests already exist** at
  `tests/test_mathutils.py:208-214`, and a clockwise regression was added in archived
  `2026/05/26/fix-is-clockwise-recursion.md`.
- Reference: `tasks/reference/notable-subsystems.md §1` (rasterizer design — winding predicates,
  coordinate flip); `tasks/reference/book-figures-and-images.md §3` (notebook pipeline).
- No existing task covers running the rasterizer under a perspective transform / as a configurable last
  stage.

## Plan (draft — after questions)

- [ ] Feed the rasterizer NDC coords from `mathutils.perspective`; render as the final MVP stage (after
      `ndc.py`).
- [ ] Expose configuration (per Q2).
- [ ] Add/point at the clockwise test (Q3 — a test already exists at `test_mathutils.py:208`).

## Open questions

1. **"In perspective"** — feed the rasterizer NDC coords produced by `mathutils.perspective`, and show
   it as the final MVP stage (after `ndc.py`)?
2. **"Configurable"** — configurable *what*: resolution, winding, perspective params?
3. **"Test for clockwise like in the notebook"** — a *new* pytest, or a notebook cell? Note a clockwise
   unit test already exists (`tests/test_mathutils.py:208`).
