# Make cayley_gl a library: replace `run_loop` with functions the caller loops over

**Status:** in progress on branch `cayley-gl-caller-owned-loop` (go-ahead 2026-11-12)
**Priority:** 6
**Difficulty:** 3
**Created:** 2026-11-05 (William Emerison Six <billsix@gmail.com>)

## BLUF

`src/modelviewprojection/mvpvisualization/cayley_gl.py` is mostly library-shaped, but `run_loop` owns the event
loop and calls back into the caller's `frame`/`menubar`/`on_key`. That is the framework shape the maintainer
avoids ("I like libraries in general, not frameworks"). Replace `run_loop` with `begin_frame` /
`clear_viewport` / `end_frame` / `shutdown`, and have each of its 9 callers write its own `while` loop. Done
means `run_loop` is gone, each caller owns its loop, and every visualization and grapher looks and behaves the
same as before.

## Context (read first)

- `tasks/reference/library-not-framework-authorship-style.md`: the house rule.
- `cayley_gl.py` (773 lines). Its docstring already says "mechanism only". Callers call down into `setup`,
  `make_camera`, `orbit_input`, `setup_orbit_view`, `StandardObjects.draw_*`, `build_standard`, `render_tree`,
  `menu_action`, `toggle_fullscreen` and `common_key`.
- **The framework-shaped part is `run_loop(window, impl, frame, menubar, on_key, target_framerate)`.** In order,
  it: installs the key callback (after the GlfwRenderer; its docstring explains why that order matters);
  busy-waits to the frame rate; polls; calls `impl.process_inputs` and `imgui.new_frame`; calls `menubar()`;
  sets the viewport and clears; calls `frame(w, h)`; renders imgui and swaps. At the end it calls
  `_p.cleanup()` and `glfw.terminate()`.
- The 9 callers each make one `cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)` call:
  - seven visualizations in `mvpvisualization/`: `coordinatesystems`, `model`, `modelview`, `modelview2d`,
    `modelvieworthoprojection`, `modelviewperspectiveprojection`, `pushmatrix`;
  - two graphers: `graphingcalculator/grapher2d.py` and `grapher3d.py`.
- Other global state: `_pipeline.py`'s module-level `all_vaos` / `all_vbos` / `all_programs` registries and the
  global `matrix_stack.MatrixStack`. Callers keep state in module globals (e.g. `coordinatesystems.py`'s
  `state` dict and `win_state`).
- No `doc-region` markers in `mvpvisualization/`, `graphingcalculator/` or `cayley/`, so book listings are not
  affected (verify again before editing).

## Plan

1. In `cayley_gl.py`, add:
   - `begin_frame(window, impl, t_prev, fps) -> float`: wait, poll, process inputs, `imgui.new_frame`;
   - `clear_viewport(window) -> (w, h)`;
   - `end_frame(window, impl)`: imgui render and swap;
   - `shutdown()`: `_p.cleanup()`, then terminate.

   Each caller's loop then reads:

   ```python
   glfw.set_key_callback(window, on_key)   # after the GlfwRenderer is created
   t = glfw.get_time()
   while not glfw.window_should_close(window):
       t = cayley_gl.begin_frame(window, impl, t, 60)
       imgui_menubar()
       w, h = cayley_gl.clear_viewport(window)
       frame(w, h)
       cayley_gl.end_frame(window, impl)
   cayley_gl.shutdown()
   ```

   Keep `run_loop`'s order: menubar after `new_frame` and before the clear.
2. Convert the 9 callers one at a time, then delete `run_loop`. Estimated diff: about +70 lines across callers
   and about −35 in `cayley_gl`.
3. Update `cayley_gl.py`'s docstrings to describe the caller-owned loop, and the authorship-style reference doc
   if it cites `run_loop`.
4. Verify:
   - `make type-check` and `make test`.
   - Each of the 9 programs, headless under Xvfb with a screenshot after a few frames: it renders, the menubar
     responds, and Esc / fullscreen keys still work.

## Decisions

- Go-ahead to implement, on its own branch with incremental commits, then archive (William Emerison Six
  <billsix@gmail.com>, 2026-11-12).
- Leave `_pipeline`'s module-level registries (`all_vaos` / `all_vbos` / `all_programs`) as they are; moving
  them into an object returned by `setup` is out of scope. `shutdown()` frees them (William Emerison Six
  <billsix@gmail.com>, 2026-11-12).
