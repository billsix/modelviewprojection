# Plan: Default SuperBible ports to 1920x1080 (or screen size)

**Status:** ✅ **done 2026-04-28** — task #34. Landed paired with task #33 (menubar). See [ports-ux-pass.md](ports-ux-pass.md) for cross-task context.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` only. *Not* the curriculum-side `/mvp/src/modelviewprojection/demoNN.py` files.

## What

SuperBible ports currently use the original C++ window sizes:
- 512×512 (chapt18 ports, chapt19/GLRect, chapt19/Text2D)
- 800×600 (chapt12 ports)
- 1024×768 (chapt15–17 ports)

These are too small on modern displays. Default new size should be ~1920×1080, or detect the primary monitor's video mode at startup and pick something reasonable (e.g., 80% of monitor size, or full size if borderless-fullscreen is the desired default).

## Why

Bill flagged these windows as "too small" while reviewing the ports. Larger default makes lighting / shadow / blur effects readable.

## How (as built)

`_common.resolve_default_window_size()` returns 1920×1080 if the primary monitor fits it; otherwise 90% of the monitor's video mode. Each migrated demo's `main()` calls this just before `glfw.create_window` and passes the result through `window_width, window_height`.

## What landed

- Every migrated port (92 files) now resolves the window size at startup from monitor info instead of using the original C++ literal (which ranged from 250×250 up to 1024×768).
- The View→Fullscreen toggle (from [ports-imgui-menubar.md](ports-imgui-menubar.md)) handles the rest: students can run windowed at 1920×1080 default, click Fullscreen to fill the monitor, click again to return.
- One demo with intentional asymmetric size — `chapt19/fscreen.py` — keeps its `glfw.create_window(monitor.size.width, monitor.size.height, title, monitor, ...)` exclusive-fullscreen-at-startup path. The migration injected `_common.resolve_default_window_size()` into the file but the values aren't used (fscreen ignores them). Acceptable — it's still consistent with the helper-import pattern even though the helper output is unused there.

## Resolved open questions

- 1920×1080 detection vs. hard-code: implemented detection (capped at 1920×1080 on big monitors, 90% on small).
- Fullscreen-by-default: NOT default. Windowed-at-1920×1080 is initial state; one menu click flips to fullscreen.
