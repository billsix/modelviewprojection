# Graphing-calculator program (2D and 3D), building on the assignment function viewer

**Status:** blocked
**Priority:** 6
**Difficulty:** 5
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (extend the assignment vs new standalone; one
program or two; interactivity/function input; GL style; 3D surface form). **Location resolved 2026-08-27:
this IS mvp work — the assignments' OpenGL math-function viewer, not the moved-out `mathdemos/`.**
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's clarified intent (2026-08-27): the two bullets *"2d math plotting in mathdemos"* and *"3d
math plotting in math demos"* actually mean — **look at the assignments; there's an OpenGL math-function
viewer for 2D; make a graphing-calculator program, in 2D and in 3D.**

Build a graphing-calculator-style program: 2D (plot `f(x)`, building on the existing viewer) and 3D
(plot `f(x,y)` as a surface).

## Context (investigation 2026-08-27) — the 2D viewer already exists in the assignments

- **The 2D OpenGL math-function viewer is `assignments/assignment1.py`.** It already has a real
  arbitrary-function plotter: `plot(fn: Callable[[float], float], domain: tuple[float,float], interval)`
  at `assignments/assignment1.py:177-191` (samples via `np.arange`, draws `GL_LINES`); it also has the
  hand-precomputed `f(x)=x²` version (`:105`) and a polar/parametric loop (`:258`). Immediate-mode GL,
  context hinted **1.4** (`:32-33`).
- It is **book-published**: `assignment1.py → programmingproj1.rst`
  (`tasks/reference/demo-chapter-inventory.md:119`, `book-and-docs-pipeline.md:79`); `demo02/vec1.py →
  mathhomework1.rst` is the other published assignment.
- **This corrects the earlier "mathdemos moved out" blocker** — that referred to a different, moved
  subsystem (`tasks/reference/notable-subsystems.md:106`). The graphing-calculator work is the
  assignments' function viewer, which is in mvp. Superseded task slug: `math-plotting-2d-and-3d.md`.
- No 3D plotting exists anywhere in mvp yet — the 3D `f(x,y)` surface is net-new.

## Plan (draft — after questions)

- [ ] **2D:** grow `assignment1.py`'s `plot(fn, domain, interval)` into a graphing-calculator (axes/grid,
      multiple functions, zoom/pan, maybe a function-input UI) — or a new standalone program that reuses
      it. Decide per Q1.
- [ ] **3D:** a new `f(x,y)` surface plotter (mesh/wireframe), net-new infrastructure.
- [ ] Decide 2D+3D as one program with a mode toggle, or two programs (Q2).

## Open questions

1. **Extend or new?** Grow `assignments/assignment1.py`'s `plot()` in place, or a new standalone
   graphing-calculator program that reuses it? (assignment1 is book-published, so growing it changes a
   published assignment — is that intended?)
2. **One program or two** — a single app doing 2D and 3D (mode toggle), or separate 2D and 3D programs?
3. **Interactivity / function input** — should the user type arbitrary functions at runtime (a
   parser/`eval`), or is it a fixed set of demo functions? Zoom/pan/axes expected?
4. **GL style** — stay immediate-mode fixed-function like assignment1 (GL 1.4, pedagogically simple), or
   modern shader-based GL?
5. **3D form** — `f(x,y)` height-field surface (wireframe/mesh), and/or parametric surfaces?
