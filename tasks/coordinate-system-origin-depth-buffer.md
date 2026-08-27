# Coordinate-system demo: make the origin subject to the depth buffer

**Status:** blocked
**Priority:** 6
**Difficulty:** 3
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (which origin; occlusion intent; target file).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Coordinate system demo, origin should be subject to depth buffer."*

Make the origin marker in the coordinate-system demo participate in the depth buffer (be occluded by
scene geometry) rather than drawing always-on-top.

## Context (investigation 2026-08-27)

- Target is the static explorer `src/modelviewprojection/mvpvisualization/coordinatesystems.py`
  (`tasks/reference/notable-subsystems.md §2c` — "the odd one out — no timeline").
- The big `mvpvisualization-pedagogy-plan.md §1` covers `coordinatesystems.py` improvements (focus-path
  overlay, per-space axes) but **not** this depth-test change — so this is a small standalone bugfix-style
  task, not part of that redesign. (`shadowmap-depth-discrimination.md` is a different depth concern.)

## Plan (draft — after questions)

- [ ] Depth-test the origin marker in `coordinatesystems.py` (per Q2/Q3).

## Open questions

1. **Which origin** — the world origin marker, or per-space axes at each node origin?
2. **"Subject to depth buffer"** — should it be *occluded* by scene geometry (it's currently drawn
   depth-test-off / always-on-top)?
3. Confirm the target is `mvpvisualization/coordinatesystems.py`.
