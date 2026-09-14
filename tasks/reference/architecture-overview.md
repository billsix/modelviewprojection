# modelviewprojection — architecture & orientation

**Reference document** — the map of what mvp is and how its subsystems fit; read this first to get oriented. Not a task; update in place. Last updated 2026-07-30.

This complements — never restates — the repo's `CLAUDE.md` (the Cayley-graph abstraction, the demo arc, the coding standard, dependency-sync rules) and `README.md` (how to run a demo, build the book). Read those for the *why* and the *rules*; read this for the *shape of the tree* and *where things live*. Deeper subsystem docs are linked inline; when one exists, defer to it rather than duplicating.

---

## 1. What mvp is — a book *and* its verified code

modelviewprojection is **simultaneously a Sphinx textbook and a runnable Python package**. It teaches 3D graphics math (model → world → camera → NDC → screen) from the ground up, with no linear-algebra prerequisite, by replacing 4×4 matrices with **invertible functions** composed along a **Cayley graph** of coordinate spaces (see `CLAUDE.md` › "Central abstraction"). "Mistake-driven development": each numbered demo introduces exactly one new idea, so the code reads top-to-bottom (procedural, module-level globals — do **not** "clean this up" into classes).

The two halves and their relationship:

- **The book** — `book/docs/`, one reStructuredText chapter per demo (`ch01.rst … ch21.rst`, plus `intro.rst`, `perspective.rst`, `glossary.rst`, homework/project pages). Built with Sphinx → HTML/PDF/EPUB into `output/`.
- **The package** — `src/modelviewprojection/` (src-layout, installed as the `modelviewprojection` distribution; see `pyproject.toml`). The actual, tested, runnable code.

**The book listings are `literalinclude`d from the real source, not retyped.** Every code block in `book/docs/` selects code between `# doc-region-begin <name>` / `# doc-region-end <name>` comment markers in the source and renders with `:lineno-match:` — 174 marker-based includes, zero hardcoded line ranges (measured 2026-07-19). So editing source **never** breaks book line numbers (Sphinx recomputes them); what *does* change the book is editing text inside a published region, or adding/moving/renaming/deleting a marker. Full rules: `CLAUDE.md` › "The book includes code by MARKER". The end-to-end build/docs mechanics are documented separately in **`tasks/reference/book-and-docs-pipeline.md`** — go there for anything about the Sphinx pipeline, extensions, or the gacalc docs-only source injection.

---

## 2. The major subsystems

Everything importable lives under `src/modelviewprojection/`; the SuperBible and Code-the-Classics ports live in a separate top-level `ports/` tree (not part of the installed package).

### The math layer — `mathutils.py` (+ gacalc)
The graphics-specific math layer. As of the 2026-06 migration (and the 2026-08-13 de-facade) it is **not** a re-export façade: `Vector`, `InvertibleFunction`, `compose`/`inverse`/`translate`/`uniform_scale`/`scale_non_uniform` and rotations all come from the external **gacalc** library and are imported from gacalc directly by callers. `mathutils.py` keeps only what gacalc deliberately doesn't carry: angle-based 2D/axis rotations (`rotate`, `rotate_x/y/z`, `rotate_around`, built on gacalc's `plane_rotation`), the `ortho` / `perspective` / `cs_to_ndc_space_fn` projections, plane-geometry helpers (`find_normal` via wedge + dual, `plane_equation`, `distance_to_plane`), the `cosine`/`sine`/`abs_sin` angle helpers, and **`FunctionStack` + module-level `fn_stack`** — the pure-function analogue of OpenGL's matrix stack used through demos 01–18. See §3 for the gacalc relationship.

### `matrix_stack.py` — the real matrix stack (demo21+)
A pure-Python reimplementation of OpenGL's fixed-function matrix stack, introduced once the course reaches OpenGL 3.3 Core (demo21+), where matrices finally exist. `MatrixStack` enum (`model`/`view`/`projection`/`modelview`/`modelviewprojection`), a `push_matrix(stack)` context manager, and `rotate_*`/`translate`/`scale`/`ortho`/`perspective`/`multiply` operating on `numpy` 4×4 arrays. Deliberately mirrors the `FunctionStack` API shape the student already learned — "just like putting the identity function on the lambda stack." Matrices upload as the `mvpMatrix` uniform.

### The numbered demos — `demos/demo01.py … demo24` (the teaching spine)
The single most important subsystem: the same Pong-like scene (two paddles + a square defined relative to paddle1) re-implemented at progressively lower-level machinery, one new concept per demo. Arc (checkable chapter↔demo table in `tasks/reference/demo-chapter-inventory.md`): **01–06** 2D immediate-mode with function composition; **07** introduces the paddles; **12** the matrix-stack *concept* (still function-based); **16** jumps to 3D; **19** switches to OpenGL 2.1 fixed-function (first real matrices, hidden behind the familiar API), with `19a–19e` porting SuperBible examples; **20** adds a pass-through shader pair; **21+** OpenGL 3.3 Core with `matrix_stack`; **22/22a/23/24** lighting, planar shadows, texturing (later demos are `demoNN/` subfolders carrying their own `.vert`/`.frag`/assets). Near-identical code across demos is **deliberate** — the course shares a concept only after teaching it; don't DRY the `Paddle`/`Camera` copies. Don't propose new "scenes"—extend the paddle/square/ground scene unless there's a concept it can't demonstrate (e.g., spheres for lighting, complex meshes for normals).

### `mvpvisualization/` — interactive pipeline & coordinate-system visualizations
Pedagogical *aids*, not demos: standalone GLFW/ImGui programs that **show** the Cayley-graph traversal and MVP pipeline interactively (`coordinatesystems.py`, `model.py`, `modelview.py`, `modelview2d.py`, `modelvieworthoprojection.py`, `modelviewperspectiveprojection.py`, `pushmatrix.py`). Each is built on the Cayley-graph engine (§ below) via the shared GL toolkit `cayley_gl.py`. `_pipeline.py` owns the common boilerplate — window/ImGui setup, shader compilation (`compile_program`/`build_pipeline`, with per-demo `project_*.glsl` snippets appended to shared `.vert` shaders), VAO/VBO builders, the standard paddle/square/ground/axis/NDC-cube meshes, the orbit `Camera`, and `cleanup()`; each demo file keeps only its pipeline creation, `draw_*` functions, and main loop. Run by path (`python src/modelviewprojection/mvpvisualization/coordinatesystems.py`).

### `framebuffer/softwarerendering.py` — the software rasterizer
A from-scratch, no-OpenGL renderer used to teach what the GPU does: a `FrameBuffer` dataclass (backed by a PIL image, displayable inline in notebooks) with `screenspace_to_framebuffer`, `set_color`, and `draw_filled_triangle`. Carries the 2D **orientation predicates** (`is_counter_clockwise`, `is_clockwise`, `is_parallel_and_same_orientation`) — their sole consumer, which is why they live here rather than in `mathutils`.

### `cayley/` — the Cayley-graph engine
The data-structure realization of the book's central abstraction, with **no OpenGL** so it is pure and unit-testable. `cayleygraph.py`: an immutable, directed, acyclic graph whose nodes are coordinate **spaces** (per-demo `Enum`s) and whose edges are ordered sequences of *interpolable* `InvertibleFunction`s (`Step`/`Edge`/`Path`/`CayleyGraph`); `CayleyGraph.path(a, b)` breadth-first routes between spaces and composes the edge functions, auto-inverting any edge walked against its arrow — the chapter-02 rule executed instead of drawn. `cayleyscene.py` turns a graph + a declarative scene description into something the `mvpvisualization` GL demos render.

### `util/` — shared demo helpers
Small, focused, individually-documented modules the demos import: `axes.py` (unit basis gizmo, X/Y/Z red/green/blue), `windowing.py` (GLFW setup), `clipping.py` (near-plane clipping), `cameracontrols.py` (per-frame keyboard walk-around polling), `colorutils.py` (`Color4`, iterable so it unpacks into GL calls), `shading.py` (lighting/geometry helpers for the lighting-era demos), `shaderutils.py` (`set_mvp_uniforms`, the MVP+model uniform upload the shader-era demos share). Each documents its own case; several intentionally overlap with per-demo copies (see the demos note). The adoption ledger (which demo introduced each helper, who keeps private copies) is in `tasks/reference/demo-chapter-inventory.md`. **Caveat:** `nbplotutils.py` lives here but is *not* a demo helper — its sole consumer is `notebooksrc/plot2d.py` (the largest file in the directory; notebook plumbing, not demo code).

**Naming trap:** `notebooksrc/framebuffer.py` (a book notebook source) and the `framebuffer/` package (the software rasterizer) are two different things that share a word.

### `notebooksrc/` and `plotsforbook/` — figure/notebook generation
`notebooksrc/` — jupytext percent-format source (`plot2d.py`, `ndc.py`, `framebuffer.py`) for the book's interactive/notebook figures. `plotsforbook/generate_plots.py` (entry point `generate_plots_for_book`, see `pyproject.toml`) plus its `plotutils/` (grid lines, matplotlib graphs, transformation plots) — a build-time script that renders the static matplotlib figures the chapters embed.

### `ports/` — faithful ports from external graphics sources
Not part of the installed package; kept in mvp's style for teaching and as porting source material.
- **`ports/openglsuperbiblev4/`** — ~104 Python ports of the *OpenGL SuperBible v4* examples, organized by chapter (`chapt01 … chapt22`). The main source Bill draws demos from; some are already slotted into the numbered demos (`axes3d`→demo19a, `atom`→19b, `solar`→19c, `sphereworld`→19e, `Block`→demo22 — see `CLAUDE.md` › "SuperBible port plan").
- **`ports/codetheclassics/`** — ports of the *Code the Classics* (vol 1 & 2) games (boing, bunner, cavern, myriapod, soccer / avenger, beatstreets, eggzy, kinetix, leadingedge), each **one self-contained file** (its own inlined, tightened engine on GLFW + OpenGL 3.3 core; since 2026-09-05 — `tasks/reference/code-the-classics-tightening.md`). The old shared shim source, `src/modelviewprojection/pgzero_gl/`, stays in the package unused until step 3 of `tasks/pgzero-gl-inline-strip-reextract.md` (parked) decides its fate.

---

## 3. How gacalc is used

mvp depends on **gacalc** (the sibling geometric-algebra library, `github.com/billsix/geometricalgebra`) for all of its core vector algebra and the invertible-function transform layer: `Vector` (gacalc's graded vector type — `g2.Vector` in 2D, `g3.Vector` in 3D; the old in-repo `Vector2D`/`Vector3D` were deleted), `InvertibleFunction`, `compose`/`inverse`/`translate`/`uniform_scale`/`scale_non_uniform`, the `at`/`steps` animation layer, and `plane_rotation` (which mvp's `rotate`/`rotate_x/y/z` bind to specific basis-vector pairs). Callers import these from gacalc directly; `mathutils.py` is a graphics-math layer around them, not a re-export façade.

Two artifacts of the **same released version** are consumed, both from PyPI:
- **The wheel** is the runtime dependency — pinned in `requirements.txt` (`gacalc==0.0.20` as of 2026-09-08; the number moves with each bump, the lockstep rule below does not) — and is what the code imports.
- **The sdist** is pulled in **docs-only** so the book can `literalinclude` gacalc's own `doc-region` markers (the `Vector`/`translate`/`InvertibleFunction` listings the chapters show). The Dockerfile's `ARG GACALC_VERSION` (which must match the requirements pin) fetches the sdist, and `entrypoint.sh` copies its `src/gacalc/*.py` into `book/docs/_gacalc_src/` (gitignored) before the build. Nothing imports it; it is never on `sys.path`.

Editing the *content* of a gacalc-included listing means editing gacalc and releasing it — this repo only points at it. **The full mechanics (version-bump procedure, the in-container region checker, why the sdist not a git clone) live in `tasks/reference/book-and-docs-pipeline.md` and `CLAUDE.md` › "Some listings are included from GACALC's source"** — go there rather than relying on this summary.

---

## 4. Working constraints in the Claude container

(Relocated from the retired `tasks/codebase-overview.md`; the drift trackers
point here.)

- ✅ Read/edit code, run `pytest`/`ruff`/`ty` in-sandbox, `git add` to stage;
  nested-podman gates when the sandbox was launched with `NESTED_PODMAN=1`.
- ❌ **No commits** — Bill commits and GPG-signs outside the container.
- ❌ **No on-screen GL/display runs** — Bill verifies anything needing a real
  display (headless Xvfb/EGL tricks exist; see `tests-and-gates.md` §4 and the
  global CLAUDE.md's nested-container notes).
- ❌ **`texExpToPng` is not installed in the sandbox** — only the project's
  built image has it, so the full doc build is exercised via `make html` (or
  by Bill), never host-side.
- ❌ The auto-mode classifier blocks `rm -rf` of pre-existing paths (e.g.
  clearing a stale `_build/latex/`).

## 5. Where do I look for X

| Concern | Location |
| --- | --- |
| Vector algebra, `InvertibleFunction`, `compose`/`translate`/`uniform_scale` | external **gacalc** (`from gacalc.g2 import Vector`, `from gacalc.transforms import …`) |
| Rotations (angle-based), `ortho`/`perspective` projection math, plane geometry, `FunctionStack` | `src/modelviewprojection/mathutils.py` |
| The real 4×4 matrix stack (demo21+, OpenGL 3.3) | `src/modelviewprojection/matrix_stack.py` |
| A specific teaching demo | `src/modelviewprojection/demos/demoNN.py` (later ones: `demos/demoNN/demoNN.py` + shaders) |
| Interactive pipeline / coordinate-system visualizations | `src/modelviewprojection/mvpvisualization/` (shared setup in `_pipeline.py`, GL toolkit in `cayley_gl.py`) |
| The software rasterizer & 2D orientation predicates | `src/modelviewprojection/framebuffer/softwarerendering.py` |
| Cayley-graph data structure / path routing (no GL) | `src/modelviewprojection/cayley/cayleygraph.py` (`cayleyscene.py` for scene→render) |
| Shared demo helpers (axes, windowing, clipping, camera, colors, shading) | `src/modelviewprojection/util/` |
| Notebook / static book figure generation | `src/modelviewprojection/notebooksrc/` (jupytext), `plotsforbook/generate_plots.py` |
| A SuperBible example port | `ports/openglsuperbiblev4/chaptNN/<name>/<name>.py` |
| A Code-the-Classics game port (engine half + game half in one file) | `ports/codetheclassics/vol{1,2}/<game>/<game>.py`; gates in `tools/ctc_*` |
| The book chapters (prose + `literalinclude` markers) | `book/docs/chNN.rst` (config `book/docs/conf.py`) |
| The book build pipeline, doc-region mechanics, gacalc docs-source injection | **`tasks/reference/book-and-docs-pipeline.md`** |
| Figures, math images (`inlinetex`), notebook generation | **`tasks/reference/book-figures-and-images.md`** |
| Which demo pairs with which chapter; un-chaptered demos; util adoption ledger | **`tasks/reference/demo-chapter-inventory.md`** |
| Gates, contract tests, proof harnesses, ty/bulk-edit playbooks | **`tasks/reference/tests-and-gates.md`** |
| GL/imgui/GLFW failure modes | **`tasks/reference/gl-and-imgui-gotchas.md`** |
| SuperBible upstream map, translation rules, ports inventory | **`tasks/reference/superbible-ports-guide.md`** |
| Dependency pins (must stay in sync with Dockerfile) | `requirements.txt` + `CLAUDE.md` › "Keeping the Dockerfile, Makefile, and dependencies in sync" |
| Coding standard, naming exemptions, per-file ruff ignores | `CLAUDE.md` › "Coding standard (Python)" + `[tool.ruff]` in `pyproject.toml` |
| Build/run/test/format commands | `Makefile`, `README.md`, `CLAUDE.md` › "Dev environment" |
| Student exercises | `assignments/` (see §7) |

---

## 6. The central abstraction — reference detail

*(Relocated verbatim from `CLAUDE.md` › "Central abstraction — Cayley graphs + `InvertibleFunction`". §1 and §3 above carry the high-level framing and the gacalc relationship; this section is the reference detail that lived in `CLAUDE.md`.)*

**Rotations.** rotations from gacalc's `plane_rotation(a, b)` (gacalc ≥ 0.0.8) — `rotate`/`rotate_x/y/z` are direct bindings of it to the relevant basis-vector pairs (half-angle rotor sandwich under the hood; numeric θ stays float, no sympy leak).

**`mathutils.py` de-façade detail (gacalc 0.0.16).** gacalc **0.0.16 dropped the dimension suffix** (`Vector2`/`Vector3` → `Vector`, `Bivector3` → `Bivector`), so multi-dimension files module-qualify (`import gacalc.g2 as g2` → `g2.Vector`) and reprs are module-qualified (`g2.Vector(coeff_e_1=…)`).

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

## 7. Assignments (`assignments/`)

*(Relocated verbatim from `CLAUDE.md` › "Assignments (`assignments/`)".)*

Student-facing exercises (`assignment1.py`, `assignment2-screenspace.py`,
`assignment3-strafe.py`, `demo02/`), runnable standalone, **covered by
`format.sh`** since 2026-07-09 (ruff check + format; `T201` exempted — their
printed output is the point). **All four were brought up to date 2026-09-08/09**
— they use `gacalc` + `mathutils` and the shared `util/` helpers exactly as the
demos do. **Don't "fix" their vocabulary ad hoc — the exercise design is Bill's
call.** Record: `tasks/archive/2026/09/09/assignments-1-and-2-review.md` and
`tasks/archive/2026/09/09/assignments-review.md`.

- **Three of them carry a deliberate hole** — `assignment2-screenspace.py` (the
  two `ndc_to_screenspace_*` mappings), `assignment3-strafe.py` (strafe on
  Shift+Left/Right), `demo02/vec1.py` (three temperature conversions). Each was
  verified solvable; **leave the holes alone.** `assignment1.py` has none — the
  book asks the student to "draw whatever you'd like", so it is a worked-example
  gallery.
- **`assignment2` renders an empty window until its hole is filled** — that is
  correct, not a bug, and its header comment says so.
- **Checking one still renders:** `tools/verify_render.sh <script> [frames]
  [png] [hold-keys] [--allow-blank]` (needs `make image` and an `Xvfb :99`).
  It works on any GLFW script here — demos and visualizations too — and reports
  a colour histogram rather than demanding pixel-identity, which is
  `tools/ctc_verify_game.sh`'s job for the games. Pass `--allow-blank` for
  `assignment2-screenspace.py`, whose empty window is correct until its hole is
  filled.
- **No reference solutions exist anywhere, and where they should live is
  undecided.** Worth settling: `demo02/vec1.py` was unrunnable for a month
  (an `ImportError` from the 2026-08-13 mathutils de-facade) because nothing
  runs these files. vec1 is pure math and *can* be gated in the pytest suite;
  the three GL files open a window at import and cannot, so their only check is
  a manual headless render.
