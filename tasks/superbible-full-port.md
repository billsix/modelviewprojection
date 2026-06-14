# Plan: Port every SuperBible v4 demo to Python under `/mvp/ports/openglsuperbiblev4/`

**Status:** active. This is the **top-level goal**. All other plans (planar shadow, rotate_around_axis, plane/normal helpers, tabled tier-2/3) are subsidiary infrastructure that supports specific demo ports.

## Goal

Produce a Python translation of the entire OpenGL SuperBible 4e example codebase, organized to mirror the SuperBible source tree, so Bill's students can read the SuperBible textbook in the second half of his class while reading along in Python — without having to learn C++.

## Why this exists (and how it differs from `/mvp/src/modelviewprojection/`)

Two parallel artifacts, two different purposes:

| | `/mvp/src/modelviewprojection/demoNN.py` | `/mvp/ports/openglsuperbiblev4/chaptNN/<demo>/` |
|---|---|---|
| Audience | First half of class — Bill's own pedagogical arc | Second half — students reading SuperBible book |
| Style | Bill's idiom — `InvertibleFunction`, Cayley graphs, mistake-driven sequencing | Faithful 1:1 translation of the C++ source |
| Scene | Pong (paddles + square + ground) re-used | Whatever scene the SuperBible demo uses |
| Math | `mathutils.py` `InvertibleFunction[V]` (early), `pyMatrixStack` (late) | Standard OpenGL matrix stacks (`glPushMatrix`/`glRotatef`); `mathutils.py` only where SuperBible uses non-matrix math (e.g. `m3dFindNormal`) |
| Curriculum role | The textbook | The reading companion |

**Existing overlap:** `demo19a–19e` and `demo22` are SuperBible ports (axes3d, atom, solar, sphereworld, Block) into the curriculum arc, in Bill's style. Those stay where they are. The `/mvp/ports/` versions are *separate, faithful* translations — students can compare the two sides if they want, but the ports tree must be self-contained and 1:1 with the book.

## Output structure

```
/mvp/ports/openglsuperbiblev4/
├── README.md                         # explains the project (what, why, how to run)
├── chaptNN/
│   └── <demoName>/
│       ├── <demoName>.py            # the port — Python, GLFW, ImGui where applicable
│       ├── <asset>.tga / .obj / etc.   # copied from SuperBible, unchanged
│       └── shaders/                  # only chapt17+, shader pairs as in SuperBible
│           ├── <name>.vs
│           └── <name>.fs
```

- Folder names mirror SuperBible exactly (`chapt05/litjet/`).
- Per-demo file is a single `.py` matching the demo name.
- Assets (TGA, MD2, OBJ, etc.) copied verbatim — they're loaded the same way; no need to re-encode.
- Shader files keep the SuperBible naming convention (`.vs`/`.fs`), **not** mvp's `.vert`/`.frag`. Reason: students are reading along in the book; the book references these filenames. (If this turns out wrong, easy global rename later.)

## Translation rules (C++ → Python)

The port is mechanical, not creative. Same rules every time:

### Window/context/event loop
| SuperBible (GLUT, callback-driven) | Python port (GLFW, polling loop) |
|---|---|
| `glutInit(&argc, argv)` + `glutInitDisplayMode(...)` + `glutCreateWindow(...)` | `glfw.init()` + `glfw.window_hint(...)` + `glfw.create_window(...)` |
| `glutDisplayFunc(RenderScene)` | call `RenderScene()` once per loop iteration |
| `glutReshapeFunc(ChangeSize)` | `glfw.set_framebuffer_size_callback(window, ChangeSize)` |
| `glutSpecialFunc(SpecialKeys)` | `glfw.get_key(window, glfw.KEY_*)` polled at top of loop |
| `glutTimerFunc(ms, fn, val)` | frame-rate limit in the loop (mvp pattern: `time_at_beginning_of_previous_frame + 1.0/60.0`) |
| `glutMainLoop()` | `while not glfw.window_should_close(window): ...` |
| `glutSwapBuffers()` | `glfw.swap_buffers(window)` |
| `glutPostRedisplay()` | no-op (we redraw every frame) |

### GUI — anything that's not basic windowing
| SuperBible | Python port |
|---|---|
| `glutCreateMenu` / `glutAddMenuEntry` (right-click menus) | ImGui control panel (`imgui.begin/end`, `imgui.combo` for menus, `imgui.checkbox`, etc.) |
| `glutBitmapCharacter` / GLUI text overlays | `imgui.text(...)` in an overlay window |
| Any custom GLUI dialog | ImGui equivalent |

### Math
| SuperBible math3d C function | Python translation |
|---|---|
| Vector ops on `M3DVector3f` (load/copy/add/sub/scale/dot/cross/length/normalize) | `Vector3D` from `mathutils.py` (with `__add__`, `__sub__`, `__mul__`, `.dot`, `.cross`, `__abs__`) |
| `m3dFindNormal`, `m3dGetPlaneEquation`, `m3dGetDistanceToPlane` | `find_normal`, `plane_equation`, `distance_to_plane` from `mathutils.py` (**Tier-1 task #5** must complete first) |
| `m3dRotationMatrix44(angle, x, y, z)` | direct `glRotatef(math.degrees(angle), x, y, z)` for fixed-function era; `pyMatrixStack.rotate_around_axis(...)` (**Tier-1 task #4**) for shader era |
| `m3dMakePlanarShadowMatrix` | `pyMatrixStack.planar_shadow(...)` (**Tier-1 task #3**) — but for the SuperBible-port, since fixed-function era uses GL matrix stack, build the 4×4 with the same logic and `glMultMatrixf` it directly. Don't introduce pyMatrixStack into a port that's faithful to fixed-function. |
| `m3dRaySphereTest`, `m3dClosestPointOnRay`, `m3dCalculateTangentBasis`, `GLFrustum.TestSphere` | tier-2 tasks #6, #7, #8, #9 — port the helper at the same time as the demo that needs it |
| `m3dMatrixMultiply44`, `m3dTransformVector*`, `m3dTransposeMatrix44`, etc. — wherever SuperBible builds a matrix manually then `glMultMatrixf`s it | use numpy directly (`np.matmul`, `np.transpose`); don't introduce a Python wrapper just for this |
| `M3DMatrix44f` standing alongside the GL matrix stack | numpy `np.matrix` of shape (4,4) `dtype=np.float32` — same convention as `pyMatrixStack` uses internally |

### Frames / cameras
| SuperBible | Python port |
|---|---|
| `GLFrame frameCamera` + `frameCamera.ApplyCameraTransform()` | unfold inline: `glRotatef(...); glTranslate(...)` matching the GLFrame's forward/up/origin. Don't introduce a `GLFrame` Python class — Bill's pedagogy avoids that abstraction. |
| `GLFrame` for an actor (placement) | inline `glTranslate(...)` + `glRotatef(...)` matching the actor's frame |
| `GLFrustum` | for the few demos that use it (sphereworld variants, frustum culling), introduce a small Python helper *only* when first needed; default is to inline the projection setup |

### OpenGL fixed-function vs shader era
- chapt01–16: **fixed function stays fixed function.** Use PyOpenGL's `glPushMatrix`, `glRotatef`, `glLightfv`, `glMaterial`, `glBegin`/`glVertex3fv`/`glEnd`, etc. exactly as SuperBible does. Don't VAO/VBO-ify.
- chapt17+: shaders. Use `OpenGL.GL.shaders.compileProgram` (mvp's existing pattern). Matrix uniforms still come from the fixed-function matrix stack (same as SuperBible), retrieved via `glGetFloatv(GL_MODELVIEW_MATRIX)` etc. and uploaded as uniforms.
- chapt19/SphereWorld32 and friends: SuperBible's "modern" port. Match its style.

### Imports / boilerplate
Every port file should start with the same skeleton (Bill's style):
```python
import os, sys, math
import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
# (chapt17+ adds:) import OpenGL.GL.shaders as shaders
# (any GUI:)         from imgui_bundle import imgui
#                    from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
import numpy as np
# (math, when used:) from modelviewprojection.mathutils import Vector3D, find_normal, ...

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv("PYOPENGL_PLATFORM"):
    os.environ["PYOPENGL_PLATFORM"] = "x11"
```

Module-level state, just like the existing demos. Procedural, no classes (matching mvp's "mistake-driven development" style, even though the originals are also procedural so this is mostly free).

## Translation patterns established (chapt01–09+ retrospective)

After porting 62 demos through chapt10 complete, the following patterns are settled. **New ports should match these unless there's a specific reason to deviate** — uniformity is part of why students can read across demos. Verified by `ast.parse` only; visual correctness is Bill's call. **All ports have Python type hints** (mechanically applied 2026-04-28 via `/tmp/add_types.py`-style regex pass; new ports should ship typed from the start — see signatures in the skeleton above).

### Patterns added since chapt05

- **`find_normal` / `plane_equation` from mathutils** for any demo doing per-face normals or planar shadows (chapt05/litjet, shadow, sphereworld, chapt06 variants, chapt08/pyramid).
- **Inline `make_planar_shadow_matrix`** in each demo that needs it. Will eventually be replaced by `pyMatrixStack.planar_shadow` (Tier-1 #3, still pending).
- **Inline `draw_solid_sphere`, `draw_torus`, `draw_solid_cone`, `draw_solid_cylinder`** — each demo that needs them includes its own helper. Not extracted to a shared module to keep ports self-contained for student reading.
- **Inline `transform_vector3` and `invert_matrix44`** for chapt08/toon's CPU-side light transformation.
- **OpenGL evaluators (glMap1f / glMap2f) for Bezier surfaces** — PyOpenGL exposes them directly; pass `np.float32` arrays.
- **Cube maps**: load 6 faces with `GL_TEXTURE_CUBE_MAP_*` targets; `glTexGeni(GL_REFLECTION_MAP)` works through PyOpenGL.
- **Multitexture**: `glActiveTexture(GL.GL_TEXTUREn)` + `glMultiTexCoordNf(GL.GL_TEXTUREn, ...)`.
- **TGA loading via imageio**: `iio.imread(path)`, then `np.flipud` for OpenGL bottom-up convention, then `np.ascontiguousarray(img, dtype=np.uint8)`. RGBA detected via `img.shape[2]`.

### Per-demo skeleton (this is the actual structure used)

```python
# <name>.py
# Brief one-line description.
# OpenGL SuperBible, Chapter NN
# Python port of <Name>.cpp by Richard S. Wright Jr.

import math, os, sys, time
import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU                # if gluPerspective / gluOrtho2D used
# Shader-era only:  import OpenGL.GL.shaders as shaders
# GUI-having demos: from imgui_bundle import imgui
#                   from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
import numpy as np                       # if matrices/buffers
# from modelviewprojection.mathutils import ...   # only when applicable

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv("PYOPENGL_PLATFORM"):
    os.environ["PYOPENGL_PLATFORM"] = "x11"

# --- module-level state (Python-typed) ---
x_rot: float = 0.0
y_rot: float = 0.0

# --- helpers (inline replacements for GLUT/gltools) ---

def render_scene() -> None: ...
def setup_rc() -> None:     ...
def change_size(w: int, h: int) -> None: ...

def on_framebuffer_size(_window, w: int, h: int) -> None: change_size(w, h)
def handle_special_keys(window) -> None:  # arrow keys polled, not callback
    global x_rot, y_rot
    ...
def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

def main() -> None:
    if not glfw.init(): sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Title", None, None)
    if not window: glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)
    setup_rc()
    w, h = glfw.get_framebuffer_size(window); change_size(w, h)
    while not glfw.window_should_close(window):
        glfw.poll_events()
        handle_special_keys(window)
        render_scene()
        glfw.swap_buffers(window)
    glfw.terminate()

if __name__ == "__main__":
    main()
```

### Animation loop (when original used `glutTimerFunc`)

Two-phase: a `tick()` advances state on a `time.monotonic()`-based interval; `render_scene()` is called every iteration so the window doesn't appear frozen.

```python
TICK_INTERVAL = 33.0 / 1000.0   # match original's timer interval
last_tick = time.monotonic()
while not glfw.window_should_close(window):
    glfw.poll_events()
    now = time.monotonic()
    if now - last_tick >= TICK_INTERVAL:
        tick()
        last_tick = now
    render_scene()
    glfw.swap_buffers(window)
```

### GLUT/gltools helper replacements

Inlined per-demo (not in a shared module — keeps each port readable top-to-bottom). Implementations to copy:

| GLUT/gltools call | Inline helper to use |
|---|---|
| `glutSolidCube(size)` | `draw_solid_cube(size)` — see `chapt01/block/Block.py` |
| `glutWireCube(size)` | `draw_wire_cube(size)` — see `chapt01/block/Block.py` |
| `glutSolidSphere(r, slices, stacks)` | `draw_solid_sphere(r, slices, stacks)` — see `chapt04/atom/atom.py` (GL_QUAD_STRIP per latitude band) |
| `gltDrawTorus(maj, min, nMaj, nMin)` | `draw_torus(...)` — see `chapt04/transformgl/transformgl.py` |
| `gltLoadTGA(path, ...)` | `load_tga_texture(path)` using `imageio.v3.imread` + `np.flipud` — see `chapt01/block/Block.py` |
| `m3dRotationMatrix44(angle, x, y, z)` | `rotation_matrix_about_axis(angle_rad, x, y, z)` — see `chapt04/transform/transform.py`. Returns column-major numpy float32 array. **Note:** this is a direct Rodrigues; Tier-1 task #4 wants the *curriculum* side (`pyMatrixStack.rotate_around_axis`) implemented as a *decomposition* of axis-aligned rotations, not direct Rodrigues. The ports tree's faithful translation does direct Rodrigues; the curriculum side does it differently. |
| `m3dTransformVector3(out, v, m)` | `transform_vector3(v, m)` — see `chapt04/transform/transform.py` |
| `m3dGetPlaneEquation(out, p1, p2, p3)` | `from modelviewprojection.mathutils import plane_equation` — returns `(Vector3D normal, float d)` in mvp's CCW convention (sign opposite to SuperBible's `m3dGetPlaneEquation`, but the planar-shadow matrix is sign-invariant). |
| `m3dFindNormal(out, p1, p2, p3)` | `from modelviewprojection.mathutils import find_normal` — returns unnormalized `Vector3D`. |
| `m3dGetDistanceToPlane(point, plane)` | `from modelviewprojection.mathutils import distance_to_plane`. |
| `m3dMakePlanarShadowMatrix(out, plane, light)` | `make_planar_shadow_matrix(plane_eq, light_pos)` returning column-major flat 16-element numpy array ready for `glMultMatrixf` — see `chapt01/block/Block.py`. Tier-1 task #3 will eventually live in `pyMatrixStack`. |

### GLFW translations from GLUT

| GLUT | GLFW |
|---|---|
| `glutDisplayFunc(RenderScene)` | call `render_scene()` once per loop iteration |
| `glutReshapeFunc(ChangeSize)` | `glfw.set_framebuffer_size_callback(window, on_framebuffer_size)` |
| `glutSpecialFunc(SpecialKeys)` (arrow keys) | poll `glfw.get_key(window, glfw.KEY_*)` in a `handle_special_keys(window)` called per-frame |
| `glutKeyboardFunc` (regular keys, edge-triggered) | use `glfw.set_key_callback(window, on_key)` so PRESS-vs-REPEAT is distinguishable |
| `glutTimerFunc(ms, fn, val)` | `time.monotonic()` tick loop above |
| `glutCreateMenu` / `glutAddMenuEntry` (right-click menus) | ImGui control panel; `imgui.radio_button` / `imgui.checkbox` / `imgui.combo` — see `chapt03/star/star.py` and `chapt03/triangle/triangle.py` |
| `glutMainLoop()` | `while not glfw.window_should_close(window): ...` |
| `glutSwapBuffers()` | `glfw.swap_buffers(window)` |
| `glutPostRedisplay()` | no-op (we redraw every frame) |
| `GLUT_SINGLE` | `glfw.window_hint(glfw.DOUBLEBUFFER, glfw.FALSE)` — see `chapt03/single/single.py` |
| `GLUT_STENCIL` | `glfw.window_hint(glfw.STENCIL_BITS, 8)` — see `chapt03/stencil/stencil.py` |
| `GLUT_MULTISAMPLE` | `glfw.window_hint(glfw.SAMPLES, 4)` |

### `GLFrame` unfolding

Don't introduce a Python `GLFrame` class. Track only the state the demo actually uses:
- For a Y-rotated camera (chapt04/sphereworld and similar): `camera_x, camera_y, camera_z, camera_yaw` globals + `apply_camera_transform()` = `glRotatef(-degrees(yaw), 0,1,0); glTranslatef(-x,-y,-z)`. See `chapt04/sphereworld/sphereworld.py`.
- For an actor with only a position: a list of `(x,y,z)` tuples; loop with `glPushMatrix; glTranslatef(*pos); draw; glPopMatrix`.
- If a demo actually uses GLFrame's full forward/up/right + arbitrary-axis rotations (e.g. chapt19/SphereWorld32), revisit at port time — may need a more capable inline helper.

### Open issues to verify on first hardware run

The ports were syntax-checked but not run. Issues likely to surface:

1. **`chapt04/sphereworld` camera direction.** I used `forward = (sin(yaw), 0, -cos(yaw))` based on glRotatef(yaw, 0,1,0) applied to (0,0,-1). If arrow keys feel inverted, flip the sign of `move_step * sin/cos` in `handle_camera_keys()`.
2. **`chapt04/transform` rotation direction.** The C++ uses `m3dDegToRad(yRot)` then `m3dRotationMatrix44`. My `rotation_matrix_about_axis` takes `angle_rad` and constructs the standard Rodrigues form. If rotation looks reversed, transpose the matrix (Rodrigues sign convention varies).
3. **`chapt03/single` flicker or non-persistent spiral.** Single-buffered `GLUT_SINGLE` behavior depends on the driver honoring `glfw.DOUBLEBUFFER = FALSE`. If the spiral disappears each frame, fall back to a manual back-buffer accumulation.
4. **`chapt01/block` step 5** intentionally only draws front/top/right faces of the textured cube (faithful to the C++). Looks visually incomplete — that's the original.
5. **`glRotatef` argument types.** PyOpenGL is mostly forgiving but if a `TypeError` shows up, wrap angle args in `float()`.
6. **`glLightfv` etc. expecting a buffer.** Tuples work in mvp's existing demos; if PyOpenGL complains, switch to numpy arrays.

## Phasing

Each phase ends with a checkpoint where Bill reviews a representative port before mass production continues.

### Phase 0 — Setup ✅ DONE
- [x] `/mvp/ports/openglsuperbiblev4/README.md` written.
- [x] Per-demo skeleton established (see "Translation patterns" above).
- [ ] Shader file extensions: still `.vs`/`.fs` planned, **not yet exercised** (no shader-era port yet — first will be chapt15).
- [x] Decided: ports run as scripts (`python /mvp/ports/.../demo.py`), no `pyproject.toml` entry points.

### Phase 1 — chapt01/block sign-off ✅ DONE
Block.py written and syntax-checks. **Awaiting hardware verification by Bill.** Open issues #1, #4, #5 above apply.

### Phase 2 — chapt02–06 ✅ DONE
- [x] chapt02 (3 demos)
- [x] chapt03 (12 demos -- the inventory said 13 but actual is 12)
- [x] chapt04 (8 demos)
- [x] chapt05 (9 demos) — uses `find_normal`, `plane_equation` from mathutils
- [x] chapt06 (6 demos)

### Phase 3 — Texturing era (chapt07–10)
- [x] chapt07 (4 demos: bitmaps, imageload, imaging, operations)
- [x] chapt08 (4 demos: pyramid, sphereworld, toon, tunnel)
- [x] chapt09 (6 demos: anisotropic, cubemap, multitexture, pointsprites, sphereworld, texgen)
- [x] chapt10 (9 demos: axes3d, bezier, bez3d, bezlit, snowman, nurbc, nurbs, nurbt, florida) — NURBS ports use PyOpenGL's Python-friendly `GLU.gluNurbsCurve`/`gluNurbsSurface`/`gluPwlCurve` (which auto-derive sizes from numpy array shapes — no need to pass explicit knot/control sizes like the C++ does). florida uses `GLU.gluNewTess` + `gluTessCallback` for polygon tessellation.

### Phase 4 — Late fixed-function (chapt11–14) — NOT STARTED
VBOs, queries, shadow mapping. Roughly 11 demos. Last fixed-function chapter. shadow mapping (chapt14) is meaty.

### Phase 5 — Shader era (chapt15–18)
First chapter with shaders (chapt15) through FBO/HDR (chapt18). Roughly 14 demos. Big era shift — shader compilation, uniform upload patterns.
- **First time** the `.vs`/`.fs` decision gets exercised. Confirm with Bill before starting chapt15.
- chapt18/hdrbloom uses **OpenEXR** for HDR images. Python equivalent: `imageio` already a dep, supports OpenEXR via plugins. May need investigation.

### Phase 6 — Modern (chapt19)
SphereWorld32 etc. — SuperBible's own "no fixed function" port. Roughly 7 demos. Some (Text2D, RThread, GLView) may not translate naturally. Triage on entry.

### Phase 7 — Triage / skip
- **chapt20** (Apple-specific Carbon/Cocoa) — **skip entirely**. Not relevant to the cross-platform Python codebase. Note in the ports README.
- **chapt21** (`GLXBasics`, `fonts`) — `GLXBasics` is X11-direct, redundant with GLFW. `fonts` is a font-rendering demo — port if simple, skip if not. Triage.
- **chapt22** (`ES_example`) — OpenGL ES sample. Skip; the GLES Python ecosystem doesn't match cleanly. Note in README.

## Definition of "done" for a single demo

A port is complete when:
1. The Python file exists at `/mvp/ports/openglsuperbiblev4/chaptNN/<demo>/<demo>.py`.
2. All assets (TGA, OBJ, etc.) are present in the same folder; shader files in `shaders/` if applicable.
3. The Python program runs (or fails only because of a display/audio/FUSE constraint that requires Bill's host).
4. Visually, it produces the same result as the SuperBible original — judged by Bill on his host.
5. The Python source is structurally close enough to the C++ that a student can read both side-by-side and follow the correspondence.

## Definition of "done" for the umbrella

Every chapter's demos are either ported, or explicitly noted as triaged-out in the ports README with a one-line reason. The ports tree has a top-level README explaining the project. Bill has signed off on phases 1–6 individually.

## Sub-task tracking

The umbrella task (next task) is the durable handle. Per-chapter tasks get created as each phase begins (created on demand, not all at once — avoids stale tasks). Tier-1 math tasks (#3, #4, #5) are prerequisites for *specific* demos, not for the umbrella; flagged inline above.

Tier-2 tabled tasks (#6, #7, #8, #9) get re-activated when the demo that needs them is reached:
- #6 (ray-sphere) → likely chapt12/select if it's mouse-picking
- #8 (tangent basis) → chapt17/bumpmap
- #9 (frustum sphere) → chapt19/SphereWorld32 if it does culling

Tier-3 task #10 stays tabled.

## Open questions for Bill

- Shader file extensions: `.vs`/`.fs` (book-faithful) vs `.vert`/`.frag` (mvp curriculum convention). Current plan: `.vs`/`.fs`. **Not yet exercised** — confirm before chapt15.
- ✅ Resolved: ports run as scripts, no `pyproject.toml` entries.
- `chapt20` and `chapt22` skip is my recommendation. Confirm?
- `chapt21/fonts` — port or skip?
- For each Phase, do you want a checkpoint where I show one port to you for review before continuing, or batch by chapter?
- ✅ Resolved: ports README explains GLUT→GLFW + GLUI→ImGui differences.
- **New, after chapt01–04:** Open issues #1–#6 in "Open issues to verify on first hardware run" above need Bill's eyes. Are any blockers, or push through chapt05+ and address them when Bill runs?
