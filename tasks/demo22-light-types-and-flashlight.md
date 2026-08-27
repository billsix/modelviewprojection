# Demo22: directional light, light source, flashlight (spotlight)

**Status:** blocked
**Priority:** 6
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (three light *types*?; flashlight = spotlight
cone?; relationship to the viz-lighting demo).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Demo 22, directional light, light source, flashlight."*

## Context (investigation 2026-08-27) — partly already exists

- **demo22 already has a directional light** (`Lw==0`) and a **visible light marker** —
  `demos/demo22/demo22.py:1112` ("constant directional light"), `:1132` ("Lw==0 for a directional
  light"), light marker / cone around `:1042-1468`. The curriculum arc has demo22 = Lambert.
- The **imgui control to move demo22's light** is a separate active task: `demo22-light-radius-imgui.md`.
- Archived `2026/06/14/ports-visible-light-source.md` added the visible light marker across lit ports.
- **Net-new here is the "flashlight" (spotlight with cone falloff).** Directional light + light source
  already exist.
- **Overlaps `mvpvis-lighting-demo-half-angle.md` (bullet 7)** — decide if they're one effort.

## Plan (draft — after questions)

- [ ] Add a spotlight/flashlight (cone falloff) to demo22 (or demonstrate all three light types), reusing
      the existing directional-light + marker code; cross-link `demo22-light-radius-imgui.md`.

## Open questions

1. Are these three light **types** to demonstrate (directional / point / spot), given demo22 today is
   directional-only?
2. **"Flashlight"** = a spotlight with cone falloff — camera-attached or scene-placed?
3. **Relationship to bullet 7** (`mvpvis-lighting-demo-half-angle.md`) — same demo, or curriculum-demo22
   vs a new visualization demo?
