# MVP — context for Claude

This is **modelviewprojection**, an OpenGL graphics course taught by William "Bill" Six (billsix@gmail.com) from his own codebase. The repo *is* the textbook (Sphinx book in `book/docs/`, one chapter per demo). Teaching philosophy is **"mistake-driven development"** (stated in README) — demos are deliberately procedural, with module-level globals, so students read top-to-bottom. Don't "clean up" by introducing classes/abstractions unless asked.

External sources Bill draws from: **OpenGL SuperBible v4** (main porting source — see `ports/openglsuperbiblev4/`), *Mathematics for 3D Game Programming*, *Computer Graphics: Principles and Practice*.

---

## Central abstraction — Cayley graphs + `InvertibleFunction`

The whole curriculum is built on **one substituted abstraction**: instead of 4×4 matrices, transformations are `InvertibleFunction`s on `Vector2`/`Vector3`, and coordinate systems form a **Cayley graph** where nodes are spaces and directed edges are these functions.

> **Note (2026-06-08):** `mathutils.py` is now a **façade over the `gacalc` geometric-algebra library** — `Vector2`/`Vector3` are gacalc's graded vector types (the old in-repo `Vector2D`/`Vector3D` were deleted), `InvertibleFunction`/`translate`/`compose`/`scale_non_uniform`/… come from `gacalc.transforms`, and rotations are built on rotors (`rotor_from_vectors` + the closed-form `sandwich`). mvp keeps only the graphics-specific math (projections, plane geometry, predicates, `FunctionStack`). Status + remaining work (Phase 4, the book) in `tasks/gacalc-math-migration.md`.

This substitution is the *point* of the course — it lets Bill explain everything (model→world→camera→NDC, push/pop, perspective) using only "function composition" and "inverse," with no linear-algebra prerequisite.

**The abstraction (in `src/modelviewprojection/mathutils.py`):**
- `InvertibleFunction[V]` = `(func, inverse, latex_repr, latex_repr_inv)`. `__call__` runs forward; `inverse(f)` swaps; `f1 @ f2` is `compose([f1, f2])`.
- Primitives: `translate(b)`, `uniform_scale(m)`, `scale_non_uniform(*factors)`, `rotate(θ)`, `rotate_x/y/z(θ)`, `rotate_around(θ, center)`, `ortho(...)`, `perspective(...)`, `cs_to_ndc_space_fn`, `identity()`.
- `compose(list)` traverses a path; `inverse(...)` walks an edge backwards. **No matrix appears anywhere in demos 01–18.**
- `FunctionStack` + module-level `fn_stack` = the Python analogue of OpenGL's matrix stack. `fn_stack.push(f)` / `fn_stack.pop()` / `fn_stack.modelspace_to_ndc_fn()` (= `compose(stack)`) / `push_transformation(f)` context manager.

**The Cayley graph framing (book chapters 02, 05, 07–10, 13, 16, 19):**
- Nodes = coordinate spaces (modelspace, world, camera, NDC, screen, …; nested spaces like "square space" defined relative to "paddle1 space").
- Directed edges = invertible functions converting *from one space to another*.
- To go between any two nodes: trace a path, `compose` the edge functions, `inverse` for any edge traversed against its arrow.
- Bill credits *Mathematics for 3D Game Programming* (Fig 1.3) for the seed; calls it Cayley graph after later reading abstract algebra. Camera placement = same operation as object placement, so the world↔camera arrow can be reversed — that's the pedagogical hinge.

---

## Pedagogical arc (demo01 → demo24)

The same Pong scene (two paddles + a square defined relative to paddle1) is re-implemented at progressively lower-level machinery. Each demo introduces *exactly one* new concept on top of the previous. Don't propose new "scenes" — extend the paddle/square/ground scene unless there's a concept it can't demonstrate (e.g., spheres for lighting, complex meshes for normals).

- **demo01–06**: 2D, immediate-mode (`glBegin`/`glEnd`), function composition via `mathutils.compose()`.
- **demo07**: Pong paddles introduced — the running scene used through the rest of the course.
- **demo12**: Matrix-stack concept introduced (still 2D, still function-based).
- **demo16**: Jump to 3D (`Vector3`, Z-axis, depth).
- **demo19**: Switch to OpenGL 2.1 fixed-function — `glMatrixMode`/`glLoadIdentity`/`glRotatef`/`glTranslate`/`gluPerspective`/`glPushMatrix`/`glPopMatrix`. *First time matrices exist*, but hidden behind the same API shape the student already learned. Comments say "just like putting the identity function on the lambda stack."
- **demo19a–19e**: SuperBible ports (axes3d, atom, solar, sphereworld) — all fixed-function 3D.
- **demo20**: Still fixed-function MVP calls, but with a trivial pass-through shader pair (`triangle.vert`/`.frag`) — introduces shader compilation only.
- **demo21+**: OpenGL 3.3 Core, no fixed function. `pyMatrixStack` (`src/modelviewprojection/pyMatrixStack.py`) is a pure-Python reimplementation of the FF matrix stack with `MatrixStack.{model,view,projection,modelview,modelviewprojection}` and a `push_matrix(stack)` context manager; matrices uploaded as `mvpMatrix` uniform. `compile_program(vert, frag)` helper, VAO/VBO tracked in `all_vaos`/`all_vbos` for cleanup.
- **demo22**: Lighting (Lambert), planar shadows, texturing — staged across multiple render modes.

Modern style (demo20+): OpenGL 3.3 Core, shaders in separate `.vert`/`.frag` files in a `demos/demoNN/` subfolder, `pyMatrixStack` for matrices, `util.colorutils.Color4`, optional `imgui_bundle` controls.

Note (2026-06-03 restructure): the package is grouped — demos under `src/modelviewprojection/demos/`, helpers under `util/` (windowing, clipping, colorutils, cameracontrols, shading, nbplotutils, axes), the software framebuffer under `framebuffer/`; `mathutils.py` + `pyMatrixStack.py` stay at the package top. Imports are absolute (`from modelviewprojection.util.colorutils import …`); demos still run by path.

---

## SuperBible port plan

**Already ported (do not re-port):**
- `axes3d` → demo19a (unit basis vector visualization)
- `atom` → demo19b
- `solar` → demo19c (sun/earth/moon nested frames)
- `sphereworld` → demo19e (FPS camera + random sphere field) — fixed-function 2.1 version using GLU spheres
- `Block` → demo22 (cube with lighting + planar shadow + texture)

**Stated wishlist (2026-04-27):** litjet, pyramid, sphereworld (modernized).

**Recommended slotting:**
- **pyramid** (textured pyramid) — gentler texturing intro than demo22's Block. Slot as **demo21b** or **demo22a**, *before* full Block complexity.
- **litjet** (lit jet plane) — advances lighting beyond demo22's Lambert: per-vertex normals on a complex mesh, specular/Phong. Slot as **demo23**.
- **sphereworld (modernized)** — demo19e covers the concept in fixed-function. A 3.3-Core, lit version → **demo24** or later, after litjet establishes the lighting model.

When porting, follow demo22's structure (subfolder with `.vert`/`.frag`/asset files, `compile_program()` helper, VAO/VBO tracked in `all_vaos`/`all_vbos`, `pyMatrixStack` for MVP). Confirm slot before writing code — pedagogical placement matters more than the port itself.

---

## How to apply

- When explaining or extending demos 01–18, *speak in terms of edges, paths, and inverses* — never "multiply matrices." When extending demo19+, the FF/shader matrix stack is the same idea, just executed on the GPU.
- When asked "why is this written this way?" the answer is almost always "to avoid introducing matrices before the student understands what the transformation is doing."
- The book chapters (`book/docs/chNN.rst`) are the authoritative source for terminology — use *Cayley graph*, *space*, *modelspace→NDC*, *invertible function*, not linear-algebra vocabulary.
- Reference the visualizations in `src/modelviewprojection/mvpvisualization/` (`coordinatesystems.py`, `pushmatrix.py`, `modelviewperspectiveprojection.py`) when the user wants to *show* the graph traversal interactively — those are pedagogical aids, not demos. They are part of the installed package (run by path, e.g. `python src/modelviewprojection/mvpvisualization/coordinatesystems.py`).
- Match the demo-era style (procedural, globals, inline comments explaining the *why*), not idiomatic modern Python. When porting from external sources, port *into* his style rather than preserving the source's structure.

---

## Dev environment

Bill's host is Fedora 43 (glibc 2.42). System SDL2 is the SDL2-compat shim on SDL3 — breaks SDL2-audio apps. I can build/package locally, but Bill verifies anything requiring a display, FUSE, or audio.

---

## Active plans

Plans live in `plans/`. At the start of a session, check `TaskList` against the plan files for status — the plan files are durable, the task IDs are not.

**Top-level goal:**
- [`plans/superbible-full-port.md`](plans/superbible-full-port.md) — **port the entire OpenGL SuperBible 4e example codebase to Python under `/mvp/ports/openglsuperbiblev4/`**, mirroring the SuperBible folder structure, so Bill's students can read the textbook in the second half of class while reading along in Python (no C++ required). Faithful 1:1 translation: GLFW (not GLUT), ImGui (not GLUT menus), fixed-function-stays-fixed-function, math in Bill's style only where it's not matrix-stack ops. **Status: COMPLETE** (2026-04-28). 101 .py files across chapt01–chapt22; chapt01–18 are real ports (~95 functional demos), chapt19 is mostly real ports plus stubs for the Win32 MFC demos that have no portable equivalent (Text2D/Text3D port the visual intent via imgui; RThread, GLView are stubbed), chapt20 (Apple Carbon/Cocoa), chapt22 (OpenGL ES) are all stubs since these target platform-specific APIs we can't reach from Python. All ports syntax-checked, none hardware-verified.

**Subsidiary plans (math / `pyMatrixStack`):**
- [`plans/planar-shadow-matrix.md`](plans/planar-shadow-matrix.md) — add planar-shadow-projection 4×4 to `pyMatrixStack` (curriculum side). Deliberately *not* an `InvertibleFunction` (rank-deficient).
- [`plans/rotate-around-axis.md`](plans/rotate-around-axis.md) — add `rotate_around_axis` to `pyMatrixStack`, *decomposed as a sequence of axis-aligned rotations* (Bill's pedagogy choice — derive arbitrary-axis rotation from rotations the student already knows; don't drop Rodrigues on them).
- [`plans/plane-and-normal-helpers.md`](plans/plane-and-normal-helpers.md) — ✅ **done 2026-04-28**. `find_normal`, `plane_equation`, `distance_to_plane` now live in `mathutils.py` as free functions on `Vector3`, with CCW winding convention (sign opposite to SuperBible's `m3dGetPlaneEquation` for plane normals, but planar-shadow matrices are sign-invariant). chapt01/block imports from mathutils. Used by chapt05/litjet, chapt05/shadow when those ports happen.

**Subsidiary plans (SuperBible ports — UX pass, recorded 2026-04-28):**
- [`plans/ports-ux-pass.md`](plans/ports-ux-pass.md) — **read first.** Umbrella plan with the phased execution order across the eight tasks below. **Phase 1 done; Phase 2 next.**
- [`plans/ports-imgui-menubar.md`](plans/ports-imgui-menubar.md) — ✅ done. Every port has imgui menubar (File→Quit, View→Fullscreen) via `_common.py`.
- [`plans/ports-window-size-1920x1080.md`](plans/ports-window-size-1920x1080.md) — ✅ done. Ports default to 1920×1080 (or 90% of monitor on smaller displays) via `_common.resolve_default_window_size()`.
- [`plans/ports-walkaround-camera.md`](plans/ports-walkaround-camera.md) — **NEXT (Phase 2).** Walk-around (demo22-style) camera for every 3D-space port; orbit/rotate-around only when justified.
- [`plans/ports-sphereworld-camera-fix.md`](plans/ports-sphereworld-camera-fix.md) — Phase 2 follow-up; specific instance of the walk-around camera task.
- [`plans/ports-keyboard-standardization.md`](plans/ports-keyboard-standardization.md) — Phase 3. Pick one keyboard convention (driven by demo22) and apply.
- [`plans/ports-replace-cli-with-imgui.md`](plans/ports-replace-cli-with-imgui.md) — Phase 3. Replace any CLI args in ports with imgui controls.
- [`plans/ports-visible-light-source.md`](plans/ports-visible-light-source.md) — Phase 3. Render a small visible marker at every light position (like demo22 does).
- [`plans/demo22-light-radius-imgui.md`](plans/demo22-light-radius-imgui.md) — *curriculum-side, not a port task*: add an imgui slider for demo22's light radius.

**Shared helper for ports tree (added 2026-04-28):** `/mvp/ports/openglsuperbiblev4/_common.py` — central place for `_common.resolve_default_window_size()`, `_common.init_imgui(window)`, `_common.WindowState`, `_common.draw_menubar(window, win_state)`, `_common.toggle_fullscreen(window, state)`. Future phases (Camera, light marker) will land here. Demo import pattern: `sys.path.insert(0, os.path.dirname(os.path.dirname(PWD))); import _common`.

**Reference:**
- [`plans/superbible-study.md`](plans/superbible-study.md) — umbrella for the /superbible study (both completed). Notes in [`notes-superbible-structure.md`](plans/notes-superbible-structure.md) and [`notes-superbible-math-diff.md`](plans/notes-superbible-math-diff.md).
- [`plans/HANDOFF-2026-04-28.md`](plans/HANDOFF-2026-04-28.md) — most recent session's stopping point. Lists exactly which demos got ported (57 across chapt01–09 + 4 of chapt10) and what to do first next session. Read this at session start if resuming SuperBible port work.
