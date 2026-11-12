# Make cayley_gl a library: replace `run_loop` with functions the caller loops over

**Created:** 2026-11-05 (William Emerison Six <billsix@gmail.com>). **Done:** 2026-11-12, on branch
`cayley-gl-caller-owned-loop`.

## Summary

`src/modelviewprojection/mvpvisualization/cayley_gl.py` was library-shaped except for
`run_loop(window, impl, frame, menubar, on_key, target_framerate)`, which owned the event loop and called back
into each program's `frame` / `menubar` / `on_key`. That is the framework shape the maintainer avoids
(`tasks/reference/library-not-framework-authorship-style.md`). `run_loop` was replaced by four frame steps, and
each of its 9 callers now writes its own loop:

```python
glfw.set_key_callback(window, on_key)   # after cayley_gl.setup created the GlfwRenderer
t_prev: float = glfw.get_time()
while not glfw.window_should_close(window):
    t_prev = cayley_gl.begin_frame(impl, t_prev)
    imgui_menubar()
    w, h = cayley_gl.clear_viewport(window)
    frame(w, h)
    cayley_gl.end_frame(window, impl)
cayley_gl.shutdown()
```

- `begin_frame(impl, t_prev, target_framerate=60) -> float`: busy-waits to the frame rate, polls, runs
  `impl.process_inputs` and `imgui.new_frame`, and returns the frame's start time.
- `clear_viewport(window) -> (w, h)`: full-framebuffer viewport, clears color and depth.
- `end_frame(window, impl)`: renders imgui and swaps.
- `shutdown()`: `_p.cleanup()`, then `glfw.terminate()`.

The order is the one `run_loop` used: key callback after the GlfwRenderer (so it replaces imgui's key
handling), menubar after `new_frame` and before the clear.

Callers converted: `mvpvisualization/` `coordinatesystems`, `model`, `modelview`, `modelview2d`,
`modelvieworthoprojection`, `modelviewperspectiveprojection`, `pushmatrix`, and `graphingcalculator/`
`grapher2d`, `grapher3d`. The `cayley_gl` module docstring shows the loop; `CLAUDE.md`,
`tasks/reference/notable-subsystems.md` and `tasks/reference/gl-and-imgui-gotchas.md` name the frame steps.

## Decisions

- Go-ahead to implement on its own branch with incremental commits, then archive (William Emerison Six
  <billsix@gmail.com>, 2026-11-12).
- `_pipeline`'s module-level registries (`all_vaos` / `all_vbos` / `all_programs`) stayed as they are; moving
  them into an object returned by `setup` was out of scope. `shutdown()` frees them (William Emerison Six
  <billsix@gmail.com>, 2026-11-12).
- `begin_frame` takes no `window` argument, unlike the plan's `begin_frame(window, impl, t_prev, fps)`: none of
  its steps uses the window, and an unused parameter would only mislead.

## How it was done

1. Added the four frame steps beside `run_loop`.
2. Converted the 9 callers with a one-shot idempotent codemod (`convert_callers.py` under
   `tasks/adhoc/cayley-gl-caller-owned-loop/`, removed at archive; a second run reported every file unchanged).
3. Deleted `run_loop` and updated the docstring and docs.

## Verification

- Before converting, all 9 programs were rendered headless with `tools/verify_render.sh <script> 10 <png>`
  (Xvfb `:99`, image built with `BUILD_DOCS=0 USE_EMACS=0 USE_EPIX=0 USE_JUPYTER=0`). After the conversion,
  and again after deleting `run_loop`, every program's frame was pixel-identical to its "before" frame
  (ImageMagick `compare -metric AE` = 0) with identical colour histograms.
- `make test`: 112 passed.
- `make format` and `make type-check` (run as `make -o image …` against the existing image): ruff and the
  annotation checker clean; `ty` reported one diagnostic, in `tests/test_demo22b_gltf_roundtrip.py`, which this
  work did not touch: the unpinned dnf `ty` renamed the rule `unresolved-import` to `import-not-found`, so that
  file's `# ty: ignore[unresolved-import]` now warns.
- Not exercised headless: key handling (Esc, F11, per-demo keys) and menubar clicks, since the probe drives a
  fixed frame count. The key callback is installed by the same `glfw.set_key_callback` call, at the same point
  relative to the GlfwRenderer, as before.
