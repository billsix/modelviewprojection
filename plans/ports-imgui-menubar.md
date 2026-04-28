# Plan: ImGui menubar (Quit + Borderless Fullscreen) for every SuperBible port

**Status:** ✅ **done 2026-04-28** — task #33. Landed paired with task #34 (window-size). See [ports-ux-pass.md](ports-ux-pass.md) for the cross-task summary.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` only. *Not* the curriculum-side `/mvp/src/modelviewprojection/demoNN.py` files.

## What

Every SuperBible port should grow an `imgui_bundle` menubar with at minimum:
- **File → Quit** (or `Esc` equivalent)
- **View → Borderless Fullscreen** (toggle)

Pattern should be uniform across the tree so students reading any port know where to find the controls. Demos that already have ImGui controls (chapt19/Text2D, chapt19/Text3D, chapt21/fonts, anything reaching for imgui in this session's chapt18+) extend their existing imgui_bundle setup; demos that don't currently use ImGui need it added.

## Why

- Students should be able to reach every demo from a known menu instead of memorizing per-demo key bindings.
- Borderless fullscreen specifically because the original C++ window sizes (512x512, 800x600) are too small on modern displays — see [ports-window-size-1920x1080.md](ports-window-size-1920x1080.md) for the related sizing task.
- Quit option in addition to `Esc` because not every student tries Esc first.

## How (as built)

Helper module `/mvp/ports/openglsuperbiblev4/_common.py` provides:
- `resolve_default_window_size()` — picks 1920×1080 capped to monitor, or 90% of monitor on smaller displays.
- `init_imgui(window) -> GlfwRenderer` — creates ImGui context and binds the GLFW backend. Caller is responsible for `impl.shutdown()` at exit.
- `WindowState` — dataclass tracking the fullscreen toggle and the saved windowed geometry.
- `toggle_fullscreen(window, state)` — uses `glfw.set_window_monitor(window, monitor_or_None, ...)` (same API path as `chapt19/fscreen.py`'s `glfw.create_window(..., monitor, ...)`, just applied to a running window). NOT the GLFW_DECORATED+resize approach (initial implementation tried that; Bill confirmed the window only got bigger, not actually fullscreen).
- `draw_menubar(window, state)` — File→Quit (Esc shortcut), View→Fullscreen (with check mark). Mutates state on toggle, sets GLFW close flag on Quit.

Each demo imports it via:
```python
PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
```

Per-demo main-loop pattern:
```python
impl = _common.init_imgui(window)
win_state = _common.WindowState()
while not glfw.window_should_close(window):
    glfw.poll_events()
    impl.process_inputs()
    render_scene()
    imgui.new_frame()
    _common.draw_menubar(window, win_state)
    # demo's own imgui panels (if any) here
    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)
impl.shutdown()
glfw.terminate()
```

## What landed

- 100 .py files under `/mvp/ports/openglsuperbiblev4/`:
  - 1 hand-written smoke-test (`chapt15/shaders.py`) — done first, kept as the canonical reference.
  - 92 migrated by `/tmp/migrate_phase1.py` (script kept in `/tmp/` for reference; the migration is one-shot and not expected to re-run).
  - 7 platform stubs (chapt19/RThread, chapt19/GLView, chapt20/*, chapt22/ES_example) — skipped, they don't open a window.
- `chapt01/Block.py` got an extra imgui panel with radio buttons for the 6 realism stages. Bill flagged Block as the one demo where his expected imgui controls "didn't show up" — Block had no prior imgui content of its own (only Space-key-driven), so the menubar was the only thing rendering and that's apparently easy to miss visually. The radio-button panel makes the imgui presence obvious.
- All 100 files pass `python3 -m py_compile`. None hardware-verified beyond `chapt15/shaders.py` and `chapt01/Block.py` so far.

## Bugs hit during the bulk migration (resolved)

- Migration regex injected `()window = ...` on one line (missing trailing newline). Fixed via `/tmp/fix_phase1.py`.
- Migration's `add_shutdown` placed `impl.shutdown()` before the FIRST `glfw.terminate()`, which on most demos lives inside `if not window:` — `impl` doesn't exist there yet. Fixed via `/tmp/fix2_phase1.py` (removed misplaced lines) and `/tmp/fix3_phase1.py` (re-added at correct location, before final `glfw.terminate()`).
- `chapt05/shadow.py` had a multi-line `from modelviewprojection.mathutils import (...)` block where the migration's fallback PWD-insertion path wedged the new lines mid-paren. Fixed manually.

## Resolved open questions

- Helper module location: `/mvp/ports/openglsuperbiblev4/_common.py` (sibling of `chapt11/_thunderbird_data.py` but one level higher in the tree).
- "Borderless fullscreen" vs exclusive: ended up using exclusive fullscreen via `glfw.set_window_monitor`, since the GLFW_DECORATED + resize path didn't actually fullscreen on Bill's display. Menu label simplified to just "Fullscreen".
- Extra menubar items (FPS readout, demo title): deferred. The menubar today has only File→Quit and View→Fullscreen.
