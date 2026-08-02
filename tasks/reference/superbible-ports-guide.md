# SuperBible v4 ports — source map & translation guide

**Reference document** — the upstream C++ quarry (`/superbible/`), the settled
C++→Python translation rules, and the state of the `ports/openglsuperbiblev4/`
tree. Read this before porting, re-porting, or bulk-editing anything there.
Not a task; update in place. Last updated 2026-07-30.

The port itself is **complete** (2026-04-28, ~101 demo files, all chapters);
the live work is the UX pass (`tasks/ports-ux-pass.md`) and Bill's hardware
verification (punchlist in `tasks/superbible-full-port.md`). GL failure modes
learned during the port live in `tasks/reference/gl-and-imgui-gotchas.md`.

A full, verified map of the upstream C++ (framework, build, per-chapter, chapt18 deep-dive)
now lives in the source repo itself:
**github.com/billsix/OpenGLSuperBibleV4Code** under `tasks/reference/`.

---

## 0. Port fidelity — NOT every port renders identically to the C++ original

The `ports/` demos are faithful translations, but a few do **not** reproduce the original's
on-screen behaviour yet. Track each as its own task; known cases:

- **chapt18/pixbufobj — "multiple spinning images" on some hardware.** The C++ shows one
  motion-blurred rotating album; on Bill's hardware Mesa/GPU the port appears to show
  multiple overlapping copies. **Does NOT reproduce under the sandbox's software GL
  (llvmpipe)** — there the port renders one clean rotating album (window corners
  pixel-verified black, `CLAMP_TO_BORDER` working), and its draw-time GL state (units,
  bound textures, texture-matrix rotation, wrap mode, border colour, blend, viewport) is
  provably identical to the C++. So it looks **hardware/driver-specific** (a texture-matrix
  + multitexture + `CLAMP_TO_BORDER` edge case llvmpipe doesn't hit) or tied to interactive
  state. Tracked in `tasks/pixbufobj-port-fidelity.md`. (Its *separate* PBO-readback crash
  is already fixed — see `tasks/ports-pbo-floattex-runtime-crashes.md`.)

Add to this list as more divergences surface.

## 1. Why this tree exists (two artifacts, two purposes)

| | `src/modelviewprojection/demos/` | `ports/openglsuperbiblev4/` |
|---|---|---|
| Audience | first half of the course — Bill's arc | second half — students reading the SuperBible book |
| Style | Bill's idiom: `InvertibleFunction`, Cayley graphs | faithful 1:1 translation of the C++ |
| Scene | the Pong scene throughout | whatever the SuperBible demo draws |

demo19a–19e and demo22 are SuperBible material re-pedagogized *into* the
curriculum; the `ports/` versions are separate, faithful translations. Don't
conflate same-named demos (Block, sphereworld, atom, solar) across the two
trees.

## 2. The upstream source (`/superbible/`, when mounted)

- Layout: `examples/src/chaptNN/<demo>/<demo>.cpp` — one 200–400-line cpp per
  demo, no per-demo headers. `shared/` holds the support library every demo
  links: `math3d.{h,cpp}`, `gltools.{h,cpp}` (TGA loader, `gltDrawTorus`/
  `gltDrawSphere`/`gltDrawUnitAxes`, shader loader), `glframe.h` (`GLFrame`),
  `glfrustum.h`, `GLee` (pre-GLEW extension loader). Linux builds are one
  plain Makefile per demo.
- **Era split: chapt01–16 pure fixed-function; chapt17 is the first shader
  chapter** (adds `shaders/<name>.vs`/`.fs`); chapt19 is SuperBible's own
  "modern" Win32 port; chapt20 macOS; chapt22 GL ES.
- **`GLFrame` is the crux abstraction**: an orthonormal frame (origin +
  forward + up) used as both camera and per-object placement
  (`ApplyActorTransform`/`ApplyCameraTransform`). mvp has no analogue and
  Bill's pedagogy avoids unified frame abstractions — **unfold it** into the
  state the demo actually uses (position + yaw globals + an inline
  `apply_camera_transform()`; see `chapt04/sphereworld`). math3d has **no
  quaternions** (GLFrame's forward+up dodges gimbal lock), no `lookAt`, no
  standalone frustum builder — so nothing upstream forces those on us.
  (`tasks/archive/2026/04/28/notes-superbible-structure.md`)

### The math3d catalog (measured against mvp)

- **Ported and shared:** `m3dFindNormal`/`m3dGetPlaneEquation`/
  `m3dGetDistanceToPlane` → `mathutils.find_normal`/`plane_equation`/
  `distance_to_plane`.
- **Tier 2 — port with the demo that needs it, not before:**
  `m3dCalculateTangentBasis` → chapt17/bumpmap; `GLFrustum.TestSphere` →
  chapt19/SphereWorld32; `m3dRaySphereTest`/`m3dClosestPointOnRay` → picking.
  `m3dSmoothStep`/`m3dCatmullRom` judged not worth a CPU-side port.
- **Tier 3 — inline translations:** `m3dGetVectorLength` → `abs(v)`,
  `m3dNormalizeVector` → `v * (1/abs(v))`, matrix ops → numpy
  (`np.matmul`/`np.transpose` on plain `ndarray`s — **not** `np.matrix`).
  (`tasks/archive/2026/04/28/notes-superbible-math-diff.md`)

### The winding decision (why signs differ from the book)

SuperBible is internally inconsistent: `m3dGetPlaneEquation` winds **CW**,
`m3dFindNormal` winds **CCW** — a one-to-one port had to pick. mvp picked
**CCW everywhere** (matching `glFrontFace(GL_CCW)`). Consequences:
`find_normal` is deliberately unnormalized (length = 2× triangle area,
mirroring upstream); `plane_equation` normalizes; a plane is a bare
`(normal, d)` **tuple** by decision (not a `Plane` dataclass — "a normal and
an offset", revisit only if a third caller appears). And the CW/CCW flip is
exactly what makes the planar-shadow matrix produce negative clip-space `w`
with mvp's plane — **the shadow matrix is NOT sign-invariant**; see
`gl-and-imgui-gotchas.md` §3 (this corrects
`tasks/archive/2026/04/28/plane-and-normal-helpers.md`, which recorded the
sign-invariance belief before it was disproven).

## 3. Translation rules (the settled patterns)

Mechanical, uniform — new ports match these so students can read across demos.

- **Window/loop:** GLUT callbacks → GLFW polling loop. `glutDisplayFunc` →
  call per iteration; `glutSpecialFunc` → poll `glfw.get_key` per frame;
  `glutKeyboardFunc` → `glfw.set_key_callback` (PRESS vs REPEAT
  distinguishable); `glutTimerFunc(ms,…)` → a `time.monotonic()` tick loop
  (`tick()` on interval, render every iteration); `GLUT_SINGLE` →
  `window_hint(DOUBLEBUFFER, FALSE)`; `GLUT_STENCIL` →
  `window_hint(STENCIL_BITS, 8)`; `GLUT_MULTISAMPLE` →
  `window_hint(SAMPLES, 4)`.
- **GUI:** GLUT right-click menus / bitmap text → imgui via `_common`
  (menubar convention — see `gl-and-imgui-gotchas.md` §1).
- **Fixed-function stays fixed-function** (chapt01–16): `glPushMatrix`,
  `glRotatef`, `glBegin/glEnd` exactly as upstream — no VAO/VBO-ification, no
  display lists unless the C++ used them (Bill's constraint; `_primitives.py`
  only moves *when the tessellation trig runs*, not how drawing happens).
- **Shader era** (chapt17+): shader files keep the book's `.vs`/`.fs` names
  (students read along; mvp's `.vert`/`.frag` convention does not apply here).
- **Vectors:** the lit/shadow ports use `Vector3` + the plane helpers. Note:
  12 files currently import `Vector3` *through* `modelviewprojection.mathutils`
  — a leftover of the removed-facade era that works only incidentally
  (`mathutils` happens to import `Vector3` internally; `__all__` doesn't gate
  `from X import Y`). **New code imports `from gacalc.g3 import Vector3`**;
  the 12 existing sites are a known deviation, listed in
  `notable-subsystems.md` §4b — don't "fix" them unasked, but don't copy the
  pattern either.
- **Per-demo skeleton:** header comment (name, one-liner, "OpenGL SuperBible,
  Chapter NN", "Python port of <X>.cpp by Richard S. Wright Jr."), the
  Wayland guard (`PYOPENGL_PLATFORM=x11` when unset under a Wayland session),
  typed module-level state, `render_scene`/`setup_rc`/`change_size`, polling
  `handle_special_keys`, `main()` with the GLFW boilerplate, `__main__`
  guard. Procedural, no classes.

### Helper-replacement exemplars (copy from these files)

| Upstream call | Inline helper — exemplar |
|---|---|
| `glutSolidCube`/`glutWireCube` | `draw_solid_cube`/`draw_wire_cube` — `chapt01/block/Block.py` |
| `glutSolidSphere` | `draw_solid_sphere` — `chapt04/atom/atom.py` (QUAD_STRIP latitude bands) |
| `gltDrawTorus` | `draw_torus` — `chapt04/transformgl/transformgl.py` |
| `gltLoadTGA` | `load_tga_texture` (imageio + `np.flipud` + `ascontiguousarray`) — `chapt01/block/Block.py` |
| `m3dRotationMatrix44` | `rotation_matrix_about_axis` (direct Rodrigues) — `chapt04/transform/transform.py`. The *curriculum* side deliberately differs: `matrix_stack`'s planned `rotate_around_axis` is a decomposition into axis-aligned rotations (`tasks/rotate-around-axis.md`) |
| `m3dTransformVector3` | `transform_vector3` — `chapt04/transform/transform.py` |
| `m3dMakePlanarShadowMatrix` | `make_planar_shadow_matrix` (with the sign fix) — `chapt01/block/Block.py` |
| GLUT menus → imgui | `chapt03/star/star.py`, `chapt03/triangle/triangle.py` |
| NURBS / tessellation | PyOpenGL's `GLU.gluNurbsCurve`/`gluNurbsSurface` auto-derive sizes from numpy shapes; `gluNewTess` + callbacks — `chapt10/` |

Helpers stay **inlined per demo** (not shared) so each port reads
top-to-bottom — the deliberate exception is `_primitives.py`'s precomputed
tessellations and `_common.py`'s window/UI machinery.

## 4. State of the tree (measured 2026-07-30)

~101 demo `.py` files + `_common.py` + `_primitives.py`. Per chapter:
chapt01:1, 02:3, 03:12, 04:8, 05:9, 06:6, 07:4, 08:4, 09:6, 10:9, 11:7,
12:3, 13:1, 14:1, 15:1, 16:2, 17:5, 18:6, 19:7, 20:4, 21:2, 22:1.

- **Stub status:** chapt19 is mixed — `GLView` and `RThread` are
  print-a-notice stubs (Win32 MFC / WGL threading), `Text2D`/`Text3D` redone
  via imgui, `GLRect`/`fscreen`/`SphereWorld32` real ports. **chapt20: all 4
  are stubs** (deprecated Apple Carbon/Cocoa). **chapt22: the single
  `ES_example` is a stub** (GL ES). Everything else is a real port.
- **Adoption:** 95 files `import _common`; 30 use `_primitives`; 12 demos
  carry a `shaders/` subfolder.
- **Camera wiring:** `_common` now carries the full walk-around/orbit
  `Camera` (see `notable-subsystems.md` §4b), but only the canary
  (`chapt08/sphereworld`) is wired to it — the other 3D ports still have
  per-demo camera code. That migration is `tasks/ports-ux-pass.md` Phase 2;
  read `tasks/archive/2026/04/28/postmortem-phase2-attempt-1.md` before any
  bulk attempt.
- **None hardware-verified except what Bill has run** — the open punchlist
  (camera sign, Rodrigues transpose, single-buffer flicker, etc.) lives in
  `tasks/superbible-full-port.md`.
