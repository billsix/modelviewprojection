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
| `M3DVector3f` (C array) | `numpy.ndarray` or `Vector3D` from `modelviewprojection.mathutils` |
| `M3DMatrix44f` + `glMultMatrixf` | `numpy.matrix` + `glMultMatrixf` |
| `m3dFindNormal`, `m3dGetPlaneEquation`, `m3dMakePlanarShadowMatrix`, etc. | inline helper functions in the demo file (or `modelviewprojection.mathutils` once those land there) |
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

## What's not ported

- **chapt20** (Apple-specific Carbon/Cocoa demos) — skipped entirely; the originals depend on dead Apple frameworks.
- **chapt21/GLXBasics** — X11/GLX direct context creation; redundant with GLFW. Other chapt21 demos triaged on entry.
- **chapt22/ES_example** — OpenGL ES sample; the Python GLES ecosystem doesn't match the desktop GL stack used elsewhere in this tree.

## Status (as of 2026-04-28)

**Done (syntax-checked, not yet hardware-verified):**
- chapt01 — `block` (1 demo)
- chapt02 — `simple`, `glrect`, `bounce` (3 demos)
- chapt03 — `points`, `pointsz`, `lines`, `linesw`, `lstipple`, `lstrips`, `pstipple`, `single`, `scissor`, `star`, `stencil`, `triangle` (12 demos)
- chapt04 — `atom`, `atom2`, `solar`, `sphereworld`, `transform`, `transformgl`, `ortho`, `perspect` (8 demos)

**= 24 demos so far.** All pass `python -c "import ast; ast.parse(open(f).read())"`. None have been run on a display — Bill's task. See open issues #1–#6 in `/mvp/plans/superbible-full-port.md` for things to watch when first running.

See `/mvp/plans/superbible-full-port.md` for the umbrella plan, the established translation patterns (skeleton, GLUT→GLFW mapping, GLFrame unfolding, etc.), and remaining phases. `/mvp/plans/superbible-study.md` is the upstream research. Check `TaskList` in Claude Code for current status of each chapter.
