# 2D grapher — mouse drag-pan and wheel-zoom

**Status:** proposed — needs go-ahead (authorized into the 2026-11-03 grapher batch)
**Priority:** 6
**Difficulty:** 2
**Started:** 2026-11-03 (William Emerison Six <billsix@gmail.com>)
**Part of:** the graphing-calculator work — base graphers at
`src/modelviewprojection/graphingcalculator/` (done + merged;
`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).

## BLUF

Let `grapher2d.py` pan with a left-mouse drag and zoom with the mouse wheel, the way a graphing
calculator does — in addition to the existing keyboard controls (arrows pan, `-`/`=` zoom), not
replacing them. "Done" = left-drag slides the plot under the cursor and the wheel zooms, both
ignored while the pointer is over an imgui menu.

## Context (read first)

- `grapher2d.py` view is a `View2D` with `center_x`, `center_y`, `half_height` (zoom). Panning
  moves the center; zooming scales `half_height` (keyboard: `handle_pan_zoom_keys`, clamped to
  `[0.25, PLOT_HALF_RANGE]`). The ortho window is applied in `apply_ortho_view`
  (`half_w = half_height * aspect`, `aspect = w/h`). The curves resample to the visible window on
  any view change, so pan/zoom already trigger a correct rebuild.
- **Pattern to mirror for the drag:** `cayley_gl.orbit_input` (`cayley_gl.py:115-135`) polls
  `glfw.get_cursor_pos` + `glfw.get_mouse_button(MOUSE_BUTTON_LEFT)`, gates on
  `not imguiio.want_capture_mouse and prev_mouse`, computes the pixel delta, and returns the new
  mouse position (threaded through a module global, as `grapher3d` does with `mouse_prev`).
- **Pattern to mirror for the wheel:** `_pipeline.install_camera_scroll` (`_pipeline.py:184-203`)
  sets a `glfw.set_scroll_callback` that **chains any previous callback** (imgui installs one) and
  gates on `not imguiio.want_capture_mouse`. It is camera-specific (`camera.r`), so grapher2d needs
  a 2D-local scroll callback that scales `half_height` instead — there is no `Camera` object here.

## Decisions (options logged; chosen = recommendation, per the batch go-ahead)

1. **Drag-pan math.** Convert the pixel delta to world units with
   `world_per_px = 2*half_height / window_height` (same for x and y: the x scale is
   `2*half_w/width = 2*half_height*aspect/width = 2*half_height/height`). Pan is
   `center_x -= dx_px * world_per_px`, `center_y += dy_px * world_per_px` (screen-y is down, so the
   plot follows the cursor). **Chosen** over a fixed per-pixel step because it makes the grabbed
   point track the cursor at any zoom.
2. **Wheel-zoom target: center vs cursor.** Options: (a) zoom about the view **center** (simplest,
   matches the existing keyboard zoom), or (b) zoom about the **cursor** (keep the point under the
   pointer fixed, the Desmos feel). **Chosen: (a) center zoom** for this task — small and matches
   the keyboard behaviour; cursor-anchored zoom is logged as a nice follow-up (needs mapping the
   cursor pixel to a world point and re-centering so it stays fixed).
3. **Zoom factor.** `half_height *= 0.9 ** y_offset` per wheel notch (scroll up = zoom in), clamped
   to the same `[0.25, PLOT_HALF_RANGE]` as the keyboard path. **Chosen** for parity with the
   keyboard zoom's clamp.
4. **Keep keyboard controls.** Additive — the arrows/`-`/`=` keep working. **Chosen** (the request
   says "a person *can* use the mouse", not "replace the keys").

## Plan

- [ ] A module-global `mouse_prev: tuple[float, float] | None` (like `grapher3d`), and a
      `mouse_pan()` helper polled each frame (mirrors `orbit_input`): if LEFT is down and
      `not want_capture_mouse`, shift `center_x/center_y` by the world-converted delta; return the
      new cursor pos.
- [ ] A 2D scroll callback (mirrors `install_camera_scroll`'s chaining + `want_capture_mouse`
      gate) that scales `view.half_height` by `0.9 ** y_offset`, clamped; installed once after
      `cayley_gl.setup`.
- [ ] Call `mouse_pan()` in `frame()` alongside `handle_pan_zoom_keys()`.
- [ ] Headless-verify the program still renders (`tools/verify_render.sh`); mouse interaction
      itself is Bill's on-display pass.

## Open questions

1. **Cursor-anchored zoom now or later?** Recommendation: ship center-zoom now (decision 2a), log
   cursor-anchored as a follow-up. Override only if you want the Desmos feel in this pass.
