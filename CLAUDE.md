# MVP — context for Claude

This is **modelviewprojection**, an OpenGL graphics course taught by William "Bill" Six (billsix@gmail.com) from his own codebase. The repo *is* the textbook (Sphinx book in `book/docs/`, one chapter per demo). Teaching philosophy is **"mistake-driven development"** (stated in README) — demos are deliberately procedural, with module-level globals, so students read top-to-bottom. Don't "clean up" by introducing classes/abstractions unless asked.

External sources Bill draws from: **OpenGL SuperBible v4** (main porting source — see `ports/openglsuperbiblev4/`), *Mathematics for 3D Game Programming*, *Computer Graphics: Principles and Practice*.

---

## Central abstraction — Cayley graphs + `InvertibleFunction`

The whole curriculum is built on **one substituted abstraction**: instead of 4×4 matrices, transformations are `InvertibleFunction`s on `Vector2`/`Vector3`, and coordinate systems form a **Cayley graph** where nodes are spaces and directed edges are these functions.

> **Note (2026-06-08):** `mathutils.py` is now a **façade over the `gacalc` geometric-algebra library** — `Vector2`/`Vector3` are gacalc's graded vector types (the old in-repo `Vector2D`/`Vector3D` were deleted), `InvertibleFunction`/`translate`/`compose`/`scale_non_uniform`/… come from `gacalc.transforms`, and rotations come from gacalc's `plane_rotation(a, b)` (gacalc ≥ 0.0.8) — `rotate`/`rotate_x/y/z` are direct bindings of it to the relevant basis-vector pairs (half-angle rotor sandwich under the hood; numeric θ stays float, no sympy leak). mvp keeps only the graphics-specific math (projections, plane geometry, `FunctionStack`; the orientation predicates live in `framebuffer/softwarerendering.py`, their sole consumer). The code migration is complete; the remaining book-prose work is `tasks/book-rotate-prose-update.md`.

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
- **demo21+**: OpenGL 3.3 Core, no fixed function. `matrix_stack` (`src/modelviewprojection/matrix_stack.py`) is a pure-Python reimplementation of the FF matrix stack with `MatrixStack.{model,view,projection,modelview,modelviewprojection}` and a `push_matrix(stack)` context manager; matrices uploaded as `mvpMatrix` uniform. `compile_program(vert, frag)` helper, VAO/VBO tracked in `all_vaos`/`all_vbos` for cleanup.
- **demo22**: Lighting (Lambert), planar shadows, texturing — staged across multiple render modes.

Modern style (demo20+): OpenGL 3.3 Core, shaders in separate `.vert`/`.frag` files in a `demos/demoNN/` subfolder, `matrix_stack` for matrices, `util.colorutils.Color4`, optional `imgui_bundle` controls.

Note (2026-06-03 restructure): the package is grouped — demos under `src/modelviewprojection/demos/`, helpers under `util/` (windowing, clipping, colorutils, cameracontrols, shading, nbplotutils, axes), the software framebuffer under `framebuffer/`; `mathutils.py` + `matrix_stack.py` stay at the package top. Imports are absolute (`from modelviewprojection.util.colorutils import …`); demos still run by path.

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

When porting, follow demo22's structure (subfolder with `.vert`/`.frag`/asset files, `compile_program()` helper, VAO/VBO tracked in `all_vaos`/`all_vbos`, `matrix_stack` for MVP). Confirm slot before writing code — pedagogical placement matters more than the port itself.

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
checks out the pinned SHA (`1bd78c0…` as of 2026-07-22 — carries the `--bg/--fg`
dvipng flags **and** the `\documentclass[varwidth]{standalone}` fix that lets the
book's display math — `\[…\]`, `align*` in ch04/ch06/ch14 — render; the prior
`fbbd9a3f…` used bare `standalone` and failed on those), and meson-builds it to
`/usr/local/bin/texExpToPng`. When the external tool changes, push the GitHub
mirror and **bump the SHA in the Dockerfile deliberately** — there is no vendored
copy to sync anymore (multivariate-math uses the identical scheme).

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
  - Audio is a **single-device software mixer on `miniaudio`** (`pgzero_gl/audio.py`,
    2026-07-09), not `pygame.mixer` (host SDL is broken) and no longer `just_playback` —
    its stream-per-voice model exhausted ALSA client slots and **blocked the game
    thread** (leadingedge's 41 engine samples; see
    `tasks/archive/2026/07/09/leadingedge-audio-clunk-and-freeze.md`). One
    `PlaybackDevice`, all voices mixed in the callback like pygame's channels:
    decoded-buffer voices with gapless loop wraparound and per-frame fade ramps,
    8-voice-per-Sound cap, music streamed in chunks. Headless → graceful no-op.
  - `geometry.Rect` is **integer-coord like `pygame.Rect`**; **`ZRect`** is the float
    variant, and **`Actor` uses `ZRect`** to keep sub-pixel positions.
  - **The games use `gacalc.g2.Vector2` / `gacalc.g3.Vector3` DIRECTLY**
    (2026-07-09; needs `gacalc>=0.0.8` — the release with `x`/`y`/`z`
    coordinate properties and quotient `/`). There is **no shim vector
    type** — `geometry.py` keeps only `Rect`/`ZRect` (the short-lived
    gacalc-backed subclass of 2026-07-08 was superseded the next day;
    see geometricalgebra `tasks/upgrade-rotation-and-ctc-vector-mapping.md`).
    The dialect mapping: `length`→`magnitude`, `dot`→`scalar_product`
    (float via `float(...)` at float-typed boundaries — gacalc returns
    `Coef`, which admits sympy), `rotate(deg)`→`plane_rotation(e_1, e_2)`
    (kinetix's module-level `_turn`), copies/`.pos` mixing via
    `Vector2(*x)` unpacking, in-place `normalize_ip`/`scale_to_length`
    → rebinding. Vector `*` scalar scales; two vectors is the geometric
    product; every game dot product is an explicit call (Bill, 2026-07-09).
    Shim position parameters (Actor pos setter, `screen.blit`) **unpack**
    (`x, y = pos`) rather than index, so they accept tuples AND gacalc
    vectors.
  - **gacalc vectors are MUTABLE, and the games mutate them in place** —
    `self.dir.x = -self.dir.x`, `self.vpos.y = …` (gacalc's generated types are
    `@dataclass(slots=True)` but deliberately not frozen; `x`/`y` are properties
    *with setters*). So **a vector in a shared location is one object aliased by
    every reader.** A default argument is the sharp edge: `def __init__(…,
    half_hit_area: Vector2 = Vector2(25, 20))` evaluates once at import, so every
    instance taking the default shares it. The fix is **two parts**: a named
    module-level constant for the default (`DEFAULT_HALF_HIT_AREA`), **and a copy on
    assignment** — `self.half_hit_area = Vector2(*half_hit_area)`.
    **The constant alone fixes nothing** — ruff's `B008` only flags *calls* in
    defaults, so a bare name silences the lint while the aliasing survives; the copy
    is the part that works. Don't "simplify" a `Vector2(*v)` assignment back to `v`.
    (Found 2026-07-18: `beatstreets`' `Player`/`EnemyVax`/`EnemyHoodie`/
    `EnemyScooterboy` all shared one `half_hit_area`; nothing mutated it, so it was a
    trap rather than a live bug — but this file mutates vectors in place constantly,
    so it was one line away.)
- History: `tasks/archive/2026/06/29/codetheclassics-types-and-docstrings.md`.

---

## Assignments (`assignments/`)

Student-facing exercises (`assignment1.py`, `assignment2-screenspace.py`,
`assignment3-strafe.py`, `demo02/`), runnable standalone. As of 2026-07-09
they are **covered by `format.sh`** (ruff check + format; `T201` exempted —
their printed output is the point), but their *content* predates the gacalc
migration: each carries a bespoke `Vertex2D` and raw GLFW boilerplate.
Modernization direction is an open task (`tasks/assignments-review.md`) —
don't "fix" their vocabulary ad hoc; the exercise design is Bill's call.

## The book includes code by MARKER, not by line number — so line numbers take care of themselves

**Every `literalinclude` in `book/docs/` selects code with `:start-after: doc-region-begin
<name>` / `:end-before: doc-region-end <name>` and renders it with `:lineno-match:`.**
Measured 2026-07-19: **174 `:lineno-match:`, zero `:lineno-start:`, zero `:lines:`** — not
one listing is pinned to a hardcoded line range.

**Consequence: editing a source file NEVER "breaks" the book's line numbers.** Sphinx
recomputes them from the markers at build time, so if you add 175 lines near the top of
`mathutils.py`, every later listing simply renders with its new, correct numbers. That is
the entire reason the markers exist. **Do not report a line-number shift as an impact, a
regression, or something needing repair — it is the design working.** (Claude did exactly
that on 2026-07-19 and Bill had to correct it.)

**What DOES change the book, and is worth checking before you edit:**

1. **Code text inside a published region** — adding a statement, or a **docstring**, to a
   function whose region the book includes. That lands verbatim in the chapter.
2. **Adding, moving, renaming, or deleting a region marker** — that changes which lines a
   chapter publishes, and a renamed marker breaks the include outright (Sphinx finds no
   anchor).
3. Prose citing a specific number, or an `:emphasize-lines:` — neither exists in this book
   today (checked 2026-07-19), so in practice only 1 and 2 apply.

So the check before editing a source file is **"is this text inside a published region?"**
— never "did the line numbers move?".

**Regions can be SPLIT, and begin/end need not share a name.** The two markers are
independent text anchors: in `demos/demo03.py`, `doc-region-begin square viewport` is
closed by `doc-region-end set to gray`. That is how a construct gets carved into several
published pieces with the parts between them left unpublished — e.g. publishing a
function's signature and body as two adjacent listings while skipping its docstring (25
back-to-back `literalinclude` pairs already appear in the book). Use this when a function
needs a docstring or doctests that students should not have to read.

**Some listings are included from GACALC's source, pulled in DOCS-ONLY (2026-07-20).** The
vector/transform math (`Vector2`/`Vector3`, `translate`, `uniform_scale`, `InvertibleFunction`,
`__call__`, `inverse`, add/subtract/mul) lives in the external **gacalc** library, not in this
repo. The book still shows that code by `literalinclude`-ing gacalc's own `doc-region` markers
from a copy of gacalc's source:

- **Two artifacts, both from PyPI, same version.** The **wheel** is the runtime dependency
  (`requirements.txt`, `gacalc==<X>`) — what the code imports. The **sdist** is the docs-only
  source: the `Dockerfile` (`ARG GACALC_VERSION`, must match the requirements pin) fetches the
  sdist and unpacks `src/gacalc/*.py` to `/opt/gacalc-src`. Nothing imports it; it is never on
  `sys.path`. The sdist is used, not a git clone, because it already contains the generated
  `g1/g2/g3/scalar.py` with markers baked in (no checkout, no code generation needed).
- **`entrypoint.sh` copies `/opt/gacalc-src/*.py` into `book/docs/_gacalc_src/`** (gitignored)
  before the build, so `literalinclude:: _gacalc_src/<mod>.py` can reach it. These listings
  caption `gacalc/<mod>.py`.
- **The doc-region checker moved INTO the container** for this reason: `_gacalc_src` only exists
  in the image, not on the host, so a host-side check can't resolve those anchors.
  `entrypoint.sh` runs `python tools/check_doc_regions.py` after populating the source and before
  `make html`; `make check-regions` is a container target that does the same. `html`/`all` no
  longer carry a host-side `check-regions` prerequisite.
- **To bump the gacalc version shown in the book:** bump BOTH `requirements.txt`'s `gacalc==`
  pin and the Dockerfile's `ARG GACALC_VERSION` to the same released version, then rebuild the
  image. gacalc's markers must exist in that release (they landed in gacalc 0.0.11).
- Editing the *content* of a gacalc-included listing means editing gacalc and releasing it —
  this repo only points at it. See `tasks/dangling-book-code-includes.md`.

## Coding standard (Python)

Written for humans and AI agents alike. **The standard is split in two** — what ruff
enforces mechanically (don't hand-review these; if `make format` is green they're done)
and the judgment calls ruff can't check (spend attention here). Adapted from the sibling
**geometricalgebra** repo's section of the same name; the two are deliberately separate
copies, so they may diverge where the projects differ.

### (a) Enforced by ruff

The `[tool.ruff.lint] select` in `pyproject.toml` gives PEP 8 layout (`E`), the Pyflakes
correctness tier (`F`), import sorting (`I`), modern unions (`UP007`/`UP035`), no
mutable/callable defaults (`B006`/`B008`), no unused loop var (`B007`), absolute imports
(`TID252`), no stray `print` (`T201`), non-crypto `random` / `shell=True`
(`S311`/`S602`), and **naming (`N`, pep8-naming)**. **`line-length = 80`** governs both
the formatter and E501 — 80 because the book is built as a PDF, where wider lines wrap
badly or run off the page. Treat a green ruff as authority on all of this.

**Every `per-file-ignores` entry carries its reason in `pyproject.toml`.** Read them
before "fixing" a flagged name — most are deliberate (below).

### (b) Judgment calls

- **An externally-defined name overrides the naming rules.** Where a name is dictated
  from outside — a framework superclass method being overridden, a protocol/dunder, a
  fixed callback or keyword — match it **exactly**; renaming unbinds it. Here that is
  `wxapp.py` / `wxapp2.py` (`OnPaint`, `OnTimer`, `InitGL`, `OnDraw`, `OnInit` — wx looks
  up those exact names; exempted from `N802` only) and wx's `attribList=` keyword. The
  exemption covers only the fixed name: locals inside those methods follow house style
  (hence `VBO` -> `vbo`, `attribList` -> `attrib_list` at the local).
- **Python naming wins over the book's mathematical shorthand — everywhere, including
  the demos.** The chapters' Cayley-graph edges are labelled in vector notation
  (`\vec{R}_<θ>`, `\vec{T}_<x,y>`, `\vec{S}_<s>`) and the demos used to alias
  `translate as T` / `rotate as R` / `uniform_scale as S` to match, with frustum bounds
  as `L,R,B,T,N,F` and a light position as `Lx,Ly,Lz,Lw`. **All of that is spelled out
  now**: `translate()`, `rotate()`, `uniform_scale()`, `left/right/bottom/top/near/far`,
  `light_x…light_w`.
  **The graph-to-code mapping is what makes this safe, so keep it.** Each affected demo
  carries a short comment above its imports reading the graph labels off against the
  function names. When you add a demo whose chapter has a diagram, add the same note —
  a student must be able to line the picture up with the source without guessing.
  The single remaining naming exemption is `N813` for `import … matrix_stack as ms`,
  and it is temporary: the fix is renaming the camelCase *module*
  (`tasks/archive/2026/07/19/rename-pymatrixstack-module.md`), which deletes the exemption at the source
  rather than suppressing it.
- **`m` and `b` are a deliberate, protected exception to the naming rules.**
  gacalc's `translate(b=...)` / `uniform_scale(m=...)` are named for `f(x) = m*x + b` —
  the intercept and the slope — so the transforms connect to an equation every student
  already knows. Teaching-facing code (demos, notebooks, assignments, the `.rst`
  examples) calls them **by keyword**; library internals may stay positional. **Do not
  rename them to `offset`/`factor`.**
- **Annotate generously — "when in doubt, annotate."** Signatures always; locals as much
  as is reasonable, including loop/unpack targets (declare the type on the line *above*;
  it does not reach comprehension variables). Read-only container params take
  `Mapping`/`Sequence`, not `dict`/`list`. **Don't fight the checker** — where an
  annotation makes `ty` worse, leave it inferred and say why at the site.
- **Inline a value used exactly once**, unless the name documents an otherwise-opaque
  expression. This *takes precedence* over "annotate generously": don't keep a single-use
  local just to give it a type.
- **What earns an extraction: duplication, or naming a phase — not reshaping control
  flow.** Settled 2026-07-18 (this replaces the earlier provisional "inner-fn first,
  guards below" wording, after trying it on three real functions):
  - **Module-level** when more than one caller needs it. In gacalc, one helper replaced
    the same lambda written out 9 times across 5 functions, and one shared function
    replaced three 58-line 91-93%-identical plot helpers (net -75 lines). Giving each
    function its own private nested copy would have been strictly worse.
  - **Nested** when the extracted part **closes over the enclosing parameters** and names
    a distinct phase. `cayley/cayleygraph.py:_route` is the worked example here: it
    splits into `breadth_first_parents` / `walk_back`, both closing over `a` and `b`, and
    its tail is then a three-case `match` that reads as the algorithm.
  - **Neither** when the helper would be used exactly once and exists only to reshape
    control flow or avoid mutating a local — that is "inline a single-use value" applied
    to functions.

  **The "guards at the bottom" shape is a consequence, not the goal.** What actually made
  `_route`'s tail clean was moving its "no path" error *into the search that discovers
  it*, not relocating guards. **Don't churn existing early-return code**, and a cheap
  top-of-function `raise` is always fine — `setup_window` (linear GL init) and the
  `graph_panel` / `imgui_menubar` family (one visibility guard each) were all examined
  and correctly left alone.
- **Prefer `match` + `case _` over an open-ended `if`/`elif` chain, for exhaustiveness.**
  A chain with no final `else` can fall through silently and the hole is invisible. **This
  repo has already been bitten:** `matrix_stack.get_current_matrix` was five `if`s with
  no `else`, annotated `-> np.ndarray`, and fell off the end returning `None` for any
  unhandled `MatrixStack` member — while every caller indexed the result. It is now a
  `match` with `case _: raise`. **Always write the `case _`**; a `match` without one has
  the same hole. See also `_route` in `cayley/cayleygraph.py`, whose tail is a three-case
  `match`. **Caveat:** `match` earns its keep on *structural* patterns; one whose every
  case is a boolean guard (`case (start, end) if start == end:`) is an `if`/`elif` in
  different syntax, justified only by the exhaustiveness argument — don't convert every
  two-branch conditional.
- **Use modern Python, and flag it proactively.** The container runs **3.14** and
  compatibility with older Pythons is **not** a concern. Prefer `match` over `if`/`elif`
  chains on an enum (with `case _:` making the fall-through explicit — see
  `matrix_stack.get_current_matrix`), `X | Y` unions and builtin generics, `@override`,
  `Self`, `TypeIs`, `enum.IntEnum` for a set of related constants (see
  `cayleygraph._DfsColor`, which replaced a bare `WHITE, GRAY, BLACK = 0, 1, 2`),
  `dataclass(slots=True, kw_only=True)`. When a newer feature would solve a problem in
  code you're touching, **say so** rather than silently preserving the old form.
- **Comments explain *why*, inline at the point they apply.** **Never leave a comment
  line holding a single word or fragment** — when a line runs long, reflow the whole
  paragraph, not the offending line.
- **New code vs existing code.** These shapes apply to *new* code; working code is not
  rewritten to chase them. (The 2026-07-18 sweep that brought the tree into compliance
  was a deliberate one-time exception, not the ongoing rule.)

### (c) mvp-specific — things a general Python standard would miss

- **Import order is semantically load-bearing, not cosmetic.** `glfw` and `OpenGL.GL`
  **must** import before `imgui_bundle` or PyOpenGL's context tracking fails at window
  setup; demos get imgui via `cayley_gl.imgui`, not their own import. See
  `cayley_gl.py:30-35`. isort must not reorder these.
- **GL constants are not `int`.** PyOpenGL constants are `IntConstant`, so annotating a
  GL enum parameter as `int` needs a checker suppression. Decide it **once** rather than
  copy-pasting `# ty: ignore` a fourth time — currently duplicated in `_pipeline.py`,
  `demo21.py`, `demo22.py`. Also: the repo mixes `# ty: ignore` and `# type: ignore`;
  prefer `# ty: ignore`, which is the checker actually running.
- **`-1` is the "uniform/attribute not present" sentinel**, and **each check must be
  justified independently** — gating one uniform's use on *another* uniform's presence
  caused a real bug (`cayley_gl.py:190-193` documents it).
- **All 4x4s are row-major, `M @ column_vector`; the transpose happens exactly at the
  `glUniformMatrix4fv` boundary** (`GL_TRUE`). Do not "fix" that flag.
- **Winding is CCW everywhere** and outward normals depend on it; any new geometry
  builder documents its winding.
- **Shaders resolve relative to the calling demo's directory** (`shader_dir`,
  keyword-only), never cwd. GLSL 330 has no `#include`, so composition is string
  concatenation (`_pipeline.py:183-196`).
- **GL resources are freed via a central registry, not RAII.** New code creates handles
  through `_pipeline`'s builders so `cleanup()` releases them; several older demos
  predate this and call a bare `glfw.terminate()`.
- **macOS Core Profile requires a non-zero VAO bound at all times** — the default VAO in
  `_pipeline.py:113-121` is deliberate, and `glBindVertexArray(0)` is never called.
- **`doc-region-begin` / `doc-region-end` comments are part of the book build.** A
  refactor that moves code must move its markers, and markers must not split a logical
  unit. `book/docs/*.rst` has **129** `literalinclude`s pointing into `demos/`.
- **Duplication across `demos/` is deliberate — "teach once, then share."** A demo may
  re-inline a helper when its chapter teaches it; `util/clipping.py`, `util/windowing.py`
  and `util/cameracontrols.py` document their own cases. Do not DRY the ~20 near-identical
  `Paddle`/`Camera` dataclasses without reading those notes.

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

**Math / `matrix_stack`:**
- `tasks/planar-shadow-matrix.md` — planar-shadow-projection 4×4 for `matrix_stack`; deliberately *not* an `InvertibleFunction` (rank-deficient). (`find_normal`/`plane_equation`/`distance_to_plane` already live in `mathutils.py`.)
- `tasks/rotate-around-axis.md` — `rotate_around_axis` decomposed as a sequence of axis-aligned rotations (Bill's pedagogy choice; don't drop Rodrigues on them).
- `tasks/face-normal-vector3d-io.md` — investigation (not started).

**Book / curriculum:**
- `tasks/book-rotate-prose-update.md` — **the remaining book-prose work** (Bill's to write): update rotate prose for `plane_rotation`, and it carries the old gacalc-math-migration Phase 4 (ch05/06/14 teach gacalc vectors as *the* vector type). The code phases are done and archived.
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
