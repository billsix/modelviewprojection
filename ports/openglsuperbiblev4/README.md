# OpenGL SuperBible v4 — Python ports

A faithful Python translation of every demo in **OpenGL SuperBible, 4th Edition** (Richard S. Wright Jr., 2007). Source tree layout mirrors the original: each demo lives at `chaptNN/<demoName>/<demoName>.py` and reads alongside the corresponding C++ source at `/superbible/examples/src/chaptNN/<demoName>/`.

## Why

In the second half of the modelviewprojection course, students read OpenGL SuperBible chapter by chapter without learning C++. These ports give them line-for-line Python they can read while working through the book.

This is **separate** from the curriculum demos at `/mvp/src/modelviewprojection/demoNN.py` — those are Bill's pedagogical arc (his idiom: `InvertibleFunction`, Cayley graphs, Pong scene re-used). The ports here are *faithful translations*, not re-pedagogizations. Some demos (Block, axes3d, atom, solar, sphereworld) appear in both trees with different intent.

## How to run a demo

```sh
python /mvp/ports/openglsuperbiblev4/chapt01/block/Block.py
```

Each port is a single self-contained script. Required Python packages match the rest of the mvp project: `glfw`, `PyOpenGL`, `numpy`, `imgui_bundle`, `imageio`. No extra dependencies.

## Translation rules

Mechanical, applied uniformly across every port:

| SuperBible C++ | Python port |
|---|---|
| GLUT (`glutInit`, `glutMainLoop`, `glutDisplayFunc`, `glutReshapeFunc`, `glutTimerFunc`) | GLFW polling loop |
| `glutKeyboardFunc` / `glutSpecialFunc` | `glfw.set_key_callback` or `glfw.get_key` polling |
| `glutCreateMenu`, `glutBitmapCharacter`, GLUI | `imgui_bundle` (Dear ImGui) overlays |
| `glutSolidCube` / `glutWireCube` / `glutSolidSphere` / etc. | inline draw calls (`glBegin`/`glEnd`) — no GLUT dependency |
| `M3DVector3f` (C array) | `numpy.ndarray`, or gacalc's `Vector3` where vector algebra is used |
| `M3DMatrix44f` + `glMultMatrixf` | plain `numpy.ndarray` (4×4, float32) + `glMultMatrixf` |
| `m3dFindNormal`, `m3dGetPlaneEquation`, `m3dGetDistanceToPlane` | `find_normal`, `plane_equation`, `distance_to_plane` from `modelviewprojection.mathutils` |
| `m3dMakePlanarShadowMatrix`, `m3dRotationMatrix44`, etc. | inline helper functions in the demo file |
| `gltLoadTGA` | `imageio.v3.imread` |
| `GLFrame` (camera or actor frame) | unfolded inline as `glRotatef` + `glTranslate` matching the frame's forward/up/origin — no Python `GLFrame` class |

Fixed-function stays fixed-function: when SuperBible uses `glPushMatrix` / `glRotatef` / `glLightfv` / `glBegin` / `glEnd`, the port does the same via PyOpenGL.

Shader-era chapters (chapt15+) keep SuperBible's `.vs`/`.fs` filename convention so students can find shaders by the names in the book.

## Conventions

- One Python file per demo, named the same as the C++ file (e.g. `Block.py` from `Block.cpp`).
- Asset files (`.tga`, `.obj`, etc.) copied verbatim into the demo folder.
- Shader pairs in a `shaders/` subfolder, named exactly as in SuperBible.
- Module-level globals (matching the procedural style of both SuperBible and the curriculum demos).
- Wayland workaround at the top of each file (`PYOPENGL_PLATFORM=x11`) since PyOpenGL has trouble with Wayland.

## What's stubbed rather than ported

These exist as `.py` files that print a notice and exit, so every upstream
demo has an entry in the tree:

- **chapt19/GLView, chapt19/RThread** — Win32 MFC dialog / WGL threading; the
  rest of chapt19 (GLRect, fscreen, SphereWorld32) is real, and Text2D/Text3D
  are re-done via imgui.
- **chapt20** (all 4) — deprecated Apple Carbon/Cocoa.
- **chapt22/ES_example** — OpenGL ES; doesn't map to the desktop GL stack
  used here.

## Status (as of 2026-07-30)

**The port is COMPLETE (2026-04-28): ~101 demo files across chapt01–chapt22**
(everything real except the stubs listed above), plus the shared
`_common.py` (window/imgui/menubar/camera machinery — 95 ports import it) and
`_primitives.py` (precomputed tessellation for ~30 immediate-mode demos).
All syntax-checked; **hardware verification is ongoing and is Bill's task** —
see the punchlist in `/mvp/tasks/superbible-full-port.md`. The walk-around
camera migration is in progress (`/mvp/tasks/ports-ux-pass.md`; only the
`chapt08/sphereworld` canary is wired so far).

The full translation rulebook (per-demo skeleton, GLUT→GLFW mapping, GLFrame
unfolding, helper exemplars, upstream source map) lives in
`/mvp/tasks/reference/superbible-ports-guide.md`.
