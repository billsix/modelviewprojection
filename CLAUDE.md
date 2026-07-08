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
- **Passing a vector to immediate-mode GL: unpack it.** Write `GL.glVertex3f(*v)` / `GL.glVertex2f(*v)`, not `GL.glVertex3f(v.coeff_e_1, v.coeff_e_2, v.coeff_e_3)`. gacalc's `Vector2`/`Vector3` iterate their coordinates in `(e_1, e_2[, e_3])` order with exactly the right arity, so `*v` *is* the coordinate args (demos 05–18 use this). The iteration-order contract is guarded by `tests/test_gl_vector_unpacking.py`, so a gacalc upgrade that changed iteration order/arity fails there instead of the demos silently mis-drawing.

---

## Dev environment

Bill's host is Fedora 43 (glibc 2.42). System SDL2 is the SDL2-compat shim on SDL3 — breaks SDL2-audio apps. I can build/package locally, but Bill verifies anything requiring a display, FUSE, or audio.

---

## Keeping the Dockerfile, Makefile, and dependencies in sync

mvp's dependencies live in **a few places that must agree** — drift causes broken
image builds. When you touch one, check the others.

1. **`requirements.txt`** — the single source of truth for Python deps. `pyproject.toml`
   has `dynamic = ['dependencies']`, so `pip install -e .` reads `requirements.txt`.
   Needs **Python ≥ 3.13** (`gacalc>=0.0.4` requires it).
2. **`Dockerfile`** — installs the *distro* (`python3-*`) packages that cover the
   heavy/native deps (numpy, glfw, pyopengl, pillow, sympy, **wxpython**, matplotlib),
   then makes a `--system-site-packages` venv and `pip install`s the rest **minus
   wxpython** (`grep -v wxpython`). It also builds the **vendored** texExpToPng
   (`book/docs/_static/tex_exp_to_png/`) under `BUILD_DOCS`. Base image Fedora 44
   (Python 3.14).
3. **`Makefile`** ↔ **`Dockerfile` `ARG`s** — every `--build-arg X=$(X)` in the
   Makefile's `image` target must have a matching `ARG X` in the Dockerfile
   (Makefile defaults `1`, Dockerfile defaults `0`). A `[Warning] one or more build
   args were not consumed: [X]` means the Makefile passes `X` but the Dockerfile
   never declares it (that's why `USE_IMGUI` was removed — imgui-bundle comes from
   `requirements.txt`, not a build flag).

**texExpToPng is built from a SHA-pinned git clone** (unvendored 2026-07-08;
the old copy at `book/docs/_static/tex_exp_to_png/` is gone). The Dockerfile's
`BUILD_DOCS` block clones `https://github.com/billsix/tex-expression-to-png.git`,
checks out the pinned SHA (`fbbd9a3f…`, verified to carry the `--bg/--fg`
dvipng flags), and meson-builds it to `/usr/local/bin/texExpToPng`. When the
external tool changes, push the GitHub mirror and **bump the SHA in the
Dockerfile deliberately** — there is no vendored copy to sync anymore
(multivariate-math uses the identical scheme).

### How to resolve drift — and TEST it in a throwaway container

Don't guess package names; verify them in a clean Fedora container. Pattern:

```sh
# nested podman needs --cgroups=disabled; --rm so the container is ephemeral.
podman run --rm --cgroups=disabled -v "$(pwd)":/srcro:ro registry.fedoraproject.org/fedora:44 bash -c '
  cp -a /srcro /mvp && cd /mvp
  <install candidate deps>            # e.g. dnf install ...
  texExpToPng --exp "\$x^2\$" --size 200 --fg "rgb 1 1 1" --bg Transparent -o /tmp/x.png
'
```

- **On-screen GL can't be verified headless** in a nested container (no display /
  GPU / xauth) — verify via *package import* + *texExpToPng render*, not a window.
  (Getting the GUI to run in a container is its own task —
  `tasks/run-demos-in-container-wayland.md`.)
- **tmpfs:** the podman image store is a tmpfs (size varies — `df -h /var/lib/containers`,
  16 GB as of 2026-06-14). **`podman rmi` each test image when done** to reclaim it;
  `podman image prune -f` clears dangling layers.
- After changing `requirements.txt`: re-check whether a new heavy dep should be a
  *distro* package in the Dockerfile (vs left to pip), then re-run `make image` to
  confirm.

---

## Code-the-Classics ports (`ports/codetheclassics/`)

A separate subtree from the course: **`pgzero_gl/`**, a clean-room PyGame-Zero/pygame
compatibility shim on GLFW + OpenGL 3.3 core, plus **10 faithful game ports** under
`vol1/` and `vol2/` (BSD-2-Clause, © Eben Upton et al.).

- **Two different rule-sets.** The **games are behaviour-faithful ports** —
  **no behaviour changes** (same RNG call order, same update/draw order, same
  gameplay), but as of 2026-07-08 their *structure* may be modernized:
  dataclasses, `match`, type annotations, `@override`, precise callable types
  (see the `ctc-*` task series; this relaxes the old "no restructuring" rule —
  Bill's call). As of 2026-07-08 the games and the SuperBible ports are also
  **ruff-formatted** by `format.sh` (`ruff check ports --fix` + `ruff format
  ports`) — the old byte-faithful/no-ruff rule is fully retired. The **shim
  (`pgzero_gl/`) is our code** — it may get real bug fixes to reproduce
  pygame/pgzero APIs correctly.
- **Enforcement:** `entrypoint/format.sh` runs `ty check` on `pgzero_gl` + `vol1` + `vol2`.
- **Fidelity gotchas worth not rediscovering:**
  - Audio is **`just_playback`**, not `pygame.mixer` (host SDL is broken). It has **no
    finalizer**, so a dropped `Playback` leaks its miniaudio stream — `Sound`/`_Music`
    pool and reuse voices instead of creating-and-dropping.
  - `geometry.Rect` is **integer-coord like `pygame.Rect`**; **`ZRect`** is the float
    variant, and **`Actor` uses `ZRect`** to keep sub-pixel positions.
  - Vector `*` is the **dot product** for vector operands (pygame semantics), not
    component-wise scaling.
- History: `tasks/archive/2026/06/29/codetheclassics-types-and-docstrings.md`.

---

## Tasks

Active work lives in `tasks/` (one file per task); completed work is moved to
`tasks/archive/<YYYY>/<MM>/<DD>/`. There is **no longer a `plans/` directory or
session HANDOFF files** — those were folded into this `tasks/` + archive model.
The list below is the curated set of the notable ones; `tasks/` is authoritative.

**Top-level goal:**
- `tasks/superbible-full-port.md` — **port the entire OpenGL SuperBible 4e example
  codebase to Python under `/mvp/ports/openglsuperbiblev4/`**, mirroring the
  SuperBible folder structure (GLFW not GLUT, ImGui not GLUT menus,
  fixed-function-stays-fixed-function, Bill's math style only where it isn't
  matrix-stack ops). **The port itself is COMPLETE** (2026-04-28): 101 .py files
  across chapt01–22; chapt01–18 real ports (~95 demos), chapt19 mostly real plus
  Win32-MFC stubs (Text2D/Text3D via imgui; RThread/GLView stubbed), chapt20
  (Apple) and chapt22 (GL ES) all stubs; all syntax-checked, none hardware-verified.
  The remaining work is the UX pass below.

**SuperBible ports — UX pass (Phase 1 done; Phase 2 next):**
- `tasks/ports-ux-pass.md` — **read first.** Self-contained umbrella: the phased
  execution order *plus* the per-task detail (the old `ports-walkaround-camera`,
  `ports-sphereworld-camera-fix`, `ports-keyboard-standardization`,
  `ports-replace-cli-with-imgui`, `ports-visible-light-source` satellites are
  folded into the Phase 2 / Phase 3 sections — archived 2026-06-14). **NEXT** is
  Phase 2: walk-around (demo22-style) camera for every 3D-space port (orbit only
  when justified), with sphereworld as the canary. Phase 3 is keyboard
  standardization, CLI→imgui, and visible light markers.
- `tasks/demo22-light-radius-imgui.md` — *curriculum-side*: imgui slider for demo22's light radius.

Shared helper for the ports tree: `/mvp/ports/openglsuperbiblev4/_common.py` —
`resolve_default_window_size()`, `init_imgui(window)`, `WindowState`,
`draw_menubar(window, win_state)`, `toggle_fullscreen(window, state)` (imgui menubar
+ 1920×1080 default already landed here). Demo import pattern:
`sys.path.insert(0, os.path.dirname(os.path.dirname(PWD))); import _common`.

**Math / `pyMatrixStack`:**
- `tasks/planar-shadow-matrix.md` — planar-shadow-projection 4×4 for `pyMatrixStack`; deliberately *not* an `InvertibleFunction` (rank-deficient). (`find_normal`/`plane_equation`/`distance_to_plane` already live in `mathutils.py`.)
- `tasks/rotate-around-axis.md` — `rotate_around_axis` decomposed as a sequence of axis-aligned rotations (Bill's pedagogy choice; don't drop Rodrigues on them).
- `tasks/face-normal-vector3d-io.md` — investigation (not started).

**Book / curriculum:**
- `tasks/gacalc-math-migration.md` — **Phase 4 (the book) is the remaining high-risk step** (ch05/06/14 rewritten to teach gacalc vectors as *the* vector type).
- `tasks/book-code-drift-ch7-15.md` and `tasks/book-code-drift-ch16-21.md` — book-prose drift trackers (planned/partial), now self-contained: the per-chapter `chNN-fixes.md` satellites were folded into these and archived 2026-06-14.
- `tasks/v4-chapt14-shadowmap-fix.md` — the one v4 demo not yet landed.
- `tasks/extract-duplicated-demo-helpers.md` — in progress (helper dedup).
- `tasks/axis-cylinder-cone-lighting.md` — deferred.
- `tasks/jupyter-sh-exec-fix.md` — one-line fix to a no-op `exec` in `entrypoint/jupyter.sh`.

**Math demos (new):**
- `tasks/math-demos-section-crossproduct-and-proof.md` — **proposed.** Stand up a
  general "math demos" section structured like `mvpvisualization/` (built on the
  `cayleygraph.py`/`cayleyscene.py` Cayley-graph abstraction); first demo = the
  cross product (ported from multivariate-math, re-expressing its hand-rolled
  12-step `StepNumber` machine as a Cayley scene), plus porting its LaTeX proof
  into a new book derivations section.

(Other in-flight: `tasks/finish-pdf-epub-build.md`, `tasks/ports-pbo-floattex-runtime-crashes.md`, `tasks/shadowmap-depth-discrimination.md`; `tasks/codebase-overview.md` is a living orientation doc.)
