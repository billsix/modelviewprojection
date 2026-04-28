# Plan: Study /superbible to inform porting back into /mvp

Two-step study, **research only — no code changes** until both are reviewed with Bill.

The corresponding live tasks are tracked in Claude Code's task system (see `TaskList`). This file is the durable plan; the task IDs reset per session, so always re-derive task status from `TaskList` rather than from this document.

---

## Task 1 — Study general structure of /superbible C++ codebase

**Status:** completed → see [`notes-superbible-structure.md`](notes-superbible-structure.md)

**Goal:** Produce a structural map of the SuperBible C++ source tree so future sessions can quickly locate the right file when Bill wants to port a specific demo. **Not** a port plan, **not** a critique — just a layout summary.

**What to cover:**
- Build system (CMake? Make? what targets?)
- Framework / application base class — how a demo gets a window, GL context, event loop
- Per-demo file conventions: where the `main`/`init`/`render` lives, naming patterns
- Where shaders, textures, and other assets live relative to a demo
- The math library's location and how it's pulled in (header-only? linked?)
- Any shared utility headers (vmath, sb7, etc.) and what each provides at a high level

**Deliverable:** a section appended to this file titled "Structural map of /superbible" with bullet-point findings and a few representative file paths.

**Don't:** start porting, propose changes to /mvp, or comment on style.

---

## Task 2 — Identify math concepts in /superbible math library missing from mvp's `mathutils.py`

**Status:** completed → see [`notes-superbible-math-diff.md`](notes-superbible-math-diff.md).

**Goal:** Catalog operations the SuperBible math library has that Bill's `src/modelviewprojection/mathutils.py` doesn't.

**Known seed:** Bill mentioned **planar shadow projection** — projecting geometry onto a plane via a light position. Likely candidates beyond that: quaternions, `lookAt`, `frustum`, matrix-from-axis-angle, reflection, normal matrix, ray/plane intersection. Discover from the source, don't assume.

**For each missing concept, record:**
- Name and signature in SuperBible
- One-sentence description of what it does
- Where SuperBible uses it (which demo(s))
- Whether it fits Bill's `InvertibleFunction[V]` style or needs a different abstraction (some things — e.g., projection-onto-plane — collapse a dimension and aren't invertible; flag those explicitly)

**Deliverable:** a section appended to this file titled "Math concepts to consider porting" with the catalog.

**Don't:** add anything to `mathutils.py`. Don't decide which to port — that's Bill's call after reviewing the catalog.

---

## Findings

*(Sections below get filled in as tasks are completed. Empty until then.)*

### Structural map of /superbible

See [`notes-superbible-structure.md`](notes-superbible-structure.md). Summary:
- **Layout:** `/superbible/examples/src/chaptNN/<demo>/<demo>.cpp` (one cpp per demo, ~200–400 lines). `examples/src/shared/` holds the framework. Linux Makefiles in `examples/projects/linux/`.
- **Framework:** `gltools.{h,cpp}` (boilerplate + TGA + shader loader), `math3d.{h,cpp}` (vector/matrix/geometry library, all `m3d*` prefixed), `glframe.h` (`GLFrame` orthonormal frame used as both camera and per-object placement), `glfrustum.h`, `GLee.{h,c}` (extension autoloader).
- **Toolkit:** GLUT (callback-driven). MVP uses GLFW (polling).
- **Eras:** chapt01–16 fixed-function only; chapt17+ adds `shaders/<name>.vs`/`.fs` files and shader-loader calls in `SetupRC()`. Still uses fixed-function matrix stack throughout.
- **Build:** per-demo Makefile, every demo links `math3d.cpp` + `gltools.cpp` + `GLee.c` + its own `.cpp` against `-lglut -lGL -lGLU -lm`.

### Math concepts to consider porting

See [`notes-superbible-math-diff.md`](notes-superbible-math-diff.md). Tier 1 has been **green-lit by Bill (2026-04-28)** — see follow-up plans:

- [`planar-shadow-matrix.md`](planar-shadow-matrix.md) — add to `pyMatrixStack` as a 4×4 matrix (not invertible; deliberately *not* an `InvertibleFunction`).
- [`rotate-around-axis.md`](rotate-around-axis.md) — add to `pyMatrixStack`, **decomposed as a sequence of `rotate_z`/`rotate_y`/`rotate_x` calls**, not as a direct Rodrigues formula. Pedagogically: arbitrary-axis rotation is built from rotations the student already knows.
- [`plane-and-normal-helpers.md`](plane-and-normal-helpers.md) — `find_normal`, `plane_equation`, `distance_to_plane` go in `mathutils.py` (vector ops, not matrix ops).

Tier 2 and Tier 3 are tabled as parked tasks (status: pending, no plan files yet) — to be picked up only when a specific demo port needs them.

Top-tier overview (load-bearing for anything Bill wants to port):

1. **`m3dMakePlanarShadowMatrix(planeEq, lightPos)`** — the one Bill flagged. Projects geometry onto a plane via a light position. **Not invertible** (collapses a dimension), so it does *not* fit `InvertibleFunction`. Recommend adding it as a 4×4 matrix in `pyMatrixStack`, since it's only used in the matrix-era demos anyway — and the "this is not a Cayley graph edge" point is itself a teaching moment.
2. **`m3dRotationMatrix44(angle, x, y, z)` — rotation around arbitrary axis (Rodrigues).** Mvp has only `rotate_x/y/z`. Used heavily in `GLFrame::RotateLocal*`. Fits `InvertibleFunction[Vector3D]` perfectly.
3. **`m3dFindNormal(p1, p2, p3)`** + **`m3dGetPlaneEquation(p1, p2, p3)`** + **`m3dGetDistanceToPlane(p, plane)`** — small geometry helpers used in litjet (per-face normals), shadow setup, and frustum culling. All free functions, all one-liners on top of existing `Vector3D` ops.

Second-tier (port-on-demand): `m3dRaySphereTest`, `m3dClosestPointOnRay`, `m3dCalculateTangentBasis` (only for chapt17/bumpmap), `GLFrustum.TestSphere` (only for chapt19/SphereWorld32). `m3dSmoothStep` and `m3dCatmullRom` likely don't need a CPU-side port.

Trivial-in-mvp's-idiom: `m3dGetVectorLength` = `abs(v)`, `m3dGetDistance` = `abs(a-b)`, `m3dNormalizeVector` = `v * (1/abs(v))`, etc. — see notes.
