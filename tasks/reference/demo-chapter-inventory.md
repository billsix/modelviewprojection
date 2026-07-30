# Demo ↔ chapter inventory

**Reference document** — the precise mapping between the numbered demos and
the book chapters, the demos that have **no** chapter (and the header-comment
convention that compensates), and the shared-helper adoption ledger. Not a
task; update in place. Last updated 2026-07-30.

`CLAUDE.md` › "Pedagogical arc" has the narrative; this doc is the checkable
table. Measured from `literalinclude` targets in `book/docs/*.rst` and the
demo imports, 2026-07-30.

---

## 1. The chapter map

ch01–ch21 map 1:1 to demo01–demo21, with **two exceptions**:

- **`ch12.rst` includes demo11 AND demo12** (the chapter contrasts them).
- **`ch16.rst` includes demo14, demo16, `mathutils.py`, AND
  `tests/test_mathutils.py`** (the Lambda Stack chapter quotes the
  FunctionStack source and its test examples — so those two non-demo files
  are book-published).

Chapter titles (from the `.rst` headings):

| ch | title | ch | title |
|---|---|---|---|
| 01 | Opening a Window | 12 | Rotate the Square |
| 02 | Draw A Rectangle | 13 | Rotate the Square Around Paddle 1 |
| 03 | Window Resizing and Proportionality | 14 | Adding Depth — Z axis |
| 04 | Moving the Paddles — Keyboard Input | 15 | Adding Depth — Enable Depth Buffer |
| 05 | Add Translate Method to Vector | 16 | Lambda Stack |
| 06 | Modelspace | 17 | Moving Camera in 3D Space |
| 07 | Rotations | 18 | 3D Perspective |
| 08 | Rotation Fix Attempt 1 | 19 | Matrix Stacks |
| 09 | Rotation Fixed — Sequence of Transformations | 20 | Shaders |
| 10 | Camera Space | 21 | OpenGL3.3 Core Profile |
| 11 | Relative Objects | | |

Non-chapter pages in the toctree: the executed notebooks `framebuffer` and
`ndc` sit **between ch02 and ch03**; `perspective` (math prose, zero
literalincludes) follows ch21; then homework/project pages, `miscellany`
(which quotes `tests/test_firstclassfunctions.py`), and `plot2d`.

**The toctree stops at ch21.** ch21 itself is unfinished (an empty "The Event
Loop" heading; no prose for `compile_program`, VAO/VBO, or the `mvpMatrix`
upload), ch20 is thin, and TODO.org sketches a planned ch22 (= ch21 + color
as a uniform). See "state of the book" in
`tasks/reference/book-and-docs-pipeline.md`.

## 2. Nine demos have NO chapter — and their headers ARE the docs

`demo19a`–`demo19e`, `demo22`, `demo22a`, `demo23`, `demo24` are not
referenced by any chapter. **The compensating convention (unwritten until
now): un-chaptered demos carry a 12–15-line descriptive header comment; the
chaptered ones carry 0–5 lines** (the chapter is their documentation, plus
the short graph-label→function-name note in demo05–07). `demo19d.py`'s header
is the exemplar — it explains the branching hierarchy and even suggests an
experiment ("Try removing one of the inner glPopMatrix calls…").

**Consequences:**
- Do not trim those headers in a comment-cleanup pass — for these nine files
  the header is the only documentation a student gets.
- These nine can be refactored with **zero book risk** (no literalinclude
  points at them) — the flip side of the 129-includes-point-at-demos number.
- SuperBible origin of the 19-series: 19a=axes3d, 19b=atom, 19c=solar,
  **19d=the chapter-12 "moons" example (branching planets/moons hierarchy,
  picking code omitted — 19d's own header says so)**, 19e=sphereworld.
  CLAUDE.md's mapping omits 19d. demo22=Block;
  demo22a=pyramid, demo23=litjet, demo24=sphereworld-modernized — **the
   2026-04-27 wishlist is implemented**, each as a `demoNN/` subfolder with
  its own shaders and textures.

## 3. Import-map boundaries (the arc, checkable)

- **`mathutils` is imported by demo07–demo18 and nothing after** — demo19+
  switch to fixed-function GL / `matrix_stack`. That import boundary *is* the
  "matrices finally exist" line in the arc.
- **`matrix_stack` is imported by demo21, 22, 22a, 23, 24** (the 3.3-Core
  era).
- **demo21, demo22, and demo24 import
  `modelviewprojection.mvpvisualization._pipeline`** — a *private* module of
  the visualization package. The teaching demos depend on the viz engine, not
  the reverse; this is the live constraint that keeps the parked
  demos-out-of-package move parked (the engine must stay importable —
  `design-decisions.md` › "Moving the runnable demos out …").

## 4. Shared-helper ledger (`util/`)

Each module's docstring names its introducing demo and exceptions (CLAUDE.md's
"teach once, then share"); this is the measured adoption table:

| util module | introduced by | demo consumers | deliberate private copies |
|---|---|---|---|
| `windowing` (`on_key`) | demo01 / ch01 | 29 files (demo02 onward) | demo01 (the chapter dissects it) |
| `clipping` (`draw_in_square_viewport`) | demo03 / ch03 | 21 files | demo03 (annotated copy); demo19e (different background color) |
| `cameracontrols` (`walk_around_camera`) | demo19 (inline, teach-once) | 11 files: 19a–19e, 20–24 | demo19 inline; demo17/18 keep their own — they teach the `InvertibleFunction` camera |
| `colorutils` (`Color4`) | demo05 era | 18 files | — |
| `shading` | demo22 | demo22, 22a, 23 | — |
| `axes` | demo19a | demo19a only | — |
| `nbplotutils` | — | **none** — sole consumer is `notebooksrc/plot2d.py`; not a demo helper despite its location | — |

Notes: `cameracontrols`' own docstring still names only "20, 21, 22, 22a, 23,
24, and 19e" — 19a–19d were converted from orbit to walk-around later
(`tasks/archive/2026/06/01/dedup-handle-inputs.md`) and now use it too; the
docstring undercounts. Only ch03 *teaches* `draw_in_square_viewport` and only
ch04 shows the call — the other chapters' demos just use it
(`tasks/extract-duplicated-demo-helpers.md` measured this).

The remaining known duplication (`on_key` 30 copies pre-dedup, `handle_inputs`
21 copies / 18 variants — KEPT by design, the key wiring is the lesson) is
tracked in `tasks/extract-duplicated-demo-helpers.md`.

## 5. Adjacent traps

- `notebooksrc/framebuffer.py` (a book notebook source) is a different thing
  from the `framebuffer/` package (the software rasterizer). Same word, two
  subsystems.
- Two `assignments/` files are book-published (`assignment1.py` →
  `programmingproj1.rst`; `demo02/vec1.py` → `mathhomework1.rst`), so they're
  under the doc-region marker regime like the demos.
- Marker names repeat **across** demo files on purpose (`draw paddle 1` in 14
  files) — each chapter includes from its own file, so names are scoped by
  target path. The checker's within-file collision scan is the right scope;
  don't "fix" cross-file reuse.
