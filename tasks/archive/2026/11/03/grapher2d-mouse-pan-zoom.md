# 2D grapher — mouse drag-pan and wheel-zoom — DONE

**Status:** done (2026-11-03) — implemented and headless-verified. The drag/wheel interaction on a
real display is the maintainer's pass (Bill verifies display-requiring things).
**Completed:** 2026-11-03 (William Emerison Six <billsix@gmail.com>, with Claude Opus 4.8)
**Part of:** the graphing-calculator work — base graphers under
`src/modelviewprojection/graphingcalculator/`
(`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).

## What was built

`grapher2d.py` now pans with a left-mouse drag and zooms with the mouse wheel, alongside the
existing keyboard controls (arrows pan, `-`/`=` zoom):

- **Drag-pan** — `mouse_pan(h)`, polled each frame (mirrors `cayley_gl.orbit_input`): while the
  left button is down and imgui doesn't own the mouse, the cursor's pixel delta converts to world
  units by `2*half_height / height` (the ortho window's world-per-pixel, equal on x and y) and
  shifts `center_x`/`center_y`, so the grabbed plot point tracks the cursor at any zoom. A module
  global `mouse_prev` holds the drag's previous position (reset when the button releases).
- **Wheel-zoom** — `install_scroll_zoom()` sets a glfw scroll callback (mirrors
  `_pipeline.install_camera_scroll`: chains imgui's prior callback, gates on `want_capture_mouse`)
  that scales `half_height` by `0.9**notch`, clamped to `[0.25, PLOT_HALF_RANGE]` (the keyboard
  zoom's range). Zoom is about the view center.

## Decisions (as built)

1. Pixel delta → world units via `2*half_height/height`, so the grabbed point tracks the cursor at
   any zoom — not a fixed per-pixel step.
2. **Center zoom**, not cursor-anchored — small and matches the keyboard zoom. Cursor-anchored
   (Desmos-style) zoom is logged as a follow-up: map the cursor pixel to a world point, then
   re-center so that point stays fixed under the wheel.
3. Zoom factor `0.9**notch`, same clamp as the keyboard path.
4. Mouse is **additive** — the keyboard pan/zoom still works.

## Verification

ruff-clean (80-col), ty-clean, annotation-checker clean (containerized gate, GATE_STATUS=0).
Rendered headless via `tools/verify_render.sh` — the program loads and draws with the scroll
callback + per-frame mouse poll installed. The drag/wheel interaction itself needs a display, so
that is the maintainer's pass.
