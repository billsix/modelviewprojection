# Plan: fix bugs in referenced demo code (demo14, demo21)

**Status:** complete
**Completed:** 2026-05-27 — demo14 `zero` + demo21 `os`/`sys` imports; committed `5f38f18`.
**Type:** code (demos).
**Found during:** ch13–15 and ch19–21 drift audits. Both verified.

## Bugs + fixes

1. **`src/modelviewprojection/demo14.py:42` — `zero` bound to the wrong vector.**
   `zero = Vector3D.e_3()` assigns the z-axis unit vector `(0,0,1)` to a name
   called `zero`. demo15.py:43 correctly uses `Vector3D.zero()`. Copy-paste slip.
   Fix: `zero = Vector3D.zero()`. **Check every use of `zero` in demo14.py** — if
   it's used as an origin/identity anywhere, the current code is silently wrong
   (offsets by one unit in z); if `zero` is unused, it's harmless but still wrong.

2. **`src/modelviewprojection/demo21/demo21.py` — missing imports.** Uses `sys`
   (lines 43, 83, 101, 113) and `os` (lines 46, 146, 148) but neither is
   imported (the import block at lines ~18-36 has ctypes/dataclasses/math/numpy/
   glfw/OpenGL/imgui but not `sys`/`os`). The module raises `NameError` as soon
   as `sys.exit()` / `os.path...` is hit. demo21.py is `literalinclude`d into
   **ch21**, so the chapter currently ships broken code. Fix: add `import os` and
   `import sys` to the import block. (Compare with demo20.py's imports.)

## Verification
- `python -c "import ast,sys; ast.parse(open('src/modelviewprojection/demo21/demo21.py').read())"` and
  a name-resolution check; confirm `sys`/`os` now imported.
- `pyflakes`/`ruff` on both files (ruff's F821 would flag undefined names).
- `grep -n "zero" src/modelviewprojection/demo14.py` to audit all uses before/after.
- Full demo execution needs a display → Bill.
</content>
