#!/usr/bin/env python
# Copyright (c) 2026 William Emerison Six
#
# Codemod for tasks/cayley-gl-caller-owned-loop.md: replace each caller's
# one-line `cayley_gl.run_loop(...)` with a loop the caller owns, built from
# cayley_gl's frame steps. Idempotent: a converted file has no run_loop line,
# so a second run changes nothing.

"""Convert the 9 ``cayley_gl.run_loop`` callers to caller-owned loops.

Run from anywhere: ``python tasks/adhoc/cayley-gl-caller-owned-loop/convert_callers.py``.
"""

import pathlib

REPO: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
PKG: pathlib.Path = REPO / "src" / "modelviewprojection"

CALLERS: list[pathlib.Path] = [
    PKG / "mvpvisualization" / name
    for name in (
        "coordinatesystems.py",
        "model.py",
        "modelview.py",
        "modelview2d.py",
        "modelvieworthoprojection.py",
        "modelviewperspectiveprojection.py",
        "pushmatrix.py",
    )
] + [PKG / "graphingcalculator" / n for n in ("grapher2d.py", "grapher3d.py")]

OLD: str = "cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)\n"

NEW: str = """\
# The event loop.  The key callback goes in after cayley_gl.setup created the
# GlfwRenderer, so it replaces imgui's key handling.  The menubar is drawn
# after begin_frame and before the clear.
glfw.set_key_callback(window, on_key)
t_prev: float = glfw.get_time()
while not glfw.window_should_close(window):
    t_prev = cayley_gl.begin_frame(impl, t_prev)
    imgui_menubar()
    w, h = cayley_gl.clear_viewport(window)
    frame(w, h)
    cayley_gl.end_frame(window, impl)
cayley_gl.shutdown()
"""


def main() -> None:
    """Rewrite each caller that still has the ``run_loop`` line."""
    for path in CALLERS:
        text: str = path.read_text()
        match text.count(OLD):
            case 0:
                print(f"unchanged  {path.relative_to(REPO)}")
            case 1:
                path.write_text(text.replace(OLD, NEW))
                print(f"converted  {path.relative_to(REPO)}")
            case n:
                raise SystemExit(f"{path}: {n} run_loop lines, expected 1")


if __name__ == "__main__":
    main()
