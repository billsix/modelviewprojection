# modelviewprojection — architecture & orientation

**Reference document** — the map of what mvp is and how its subsystems fit; read this first to get oriented. Not a task; update in place. Last updated 2026-07-21.

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
The graphics-specific math façade. As of the 2026-06 migration it is **not** a re-export facade: `Vector2`/`Vector3`, `InvertibleFunction`, `compose`/`inverse`/`translate`/`uniform_scale`/`scale_non_uniform` and rotations all come from the external **gacalc** library and are imported from gacalc directly by callers. `mathutils.py` keeps only what gacalc deliberately doesn't carry: angle-based 2D/axis rotations (`rotate`, `rotate_x/y/z`, `rotate_around`, built on gacalc's `plane_rotation`), the `ortho` / `perspective` / `cs_to_ndc_space_fn` projections, plane-geometry helpers (`find_normal` via wedge + dual, `plane_equation`, `distance_to_plane`), the `cosine`/`sine`/`abs_sin` angle helpers, and **`FunctionStack` + module-level `fn_stack`** — the pure-function analogue of OpenGL's matrix stack used through demos 01–18. See §3 for the gacalc relationship.

### `matrix_stack.py` — the real matrix stack (demo21+)
A pure-Python reimplementation of OpenGL's fixed-function matrix stack, introduced once the course reaches OpenGL 3.3 Core (demo21+), where matrices finally exist. `MatrixStack` enum (`model`/`view`/`projection`/`modelview`/`modelviewprojection`), a `push_matrix(stack)` context manager, and `rotate_*`/`translate`/`scale`/`ortho`/`perspective`/`multiply` operating on `numpy` 4×4 arrays. Deliberately mirrors the `FunctionStack` API shape the student already learned — "just like putting the identity function on the lambda stack." Matrices upload as the `mvpMatrix` uniform.

### The numbered demos — `demos/demo01.py … demo24` (the teaching spine)
The single most important subsystem: the same Pong-like scene (two paddles + a square defined relative to paddle1) re-implemented at progressively lower-level machinery, one new concept per demo. Arc (detail in `CLAUDE.md` › "Pedagogical arc"): **01–06** 2D immediate-mode with function composition; **07** introduces the paddles; **12** the matrix-stack *concept* (still function-based); **16** jumps to 3D; **19** switches to OpenGL 2.1 fixed-function (first real matrices, hidden behind the familiar API), with `19a–19e` porting SuperBible examples; **20** adds a pass-through shader pair; **21+** OpenGL 3.3 Core with `matrix_stack`; **22/22a/23/24** lighting, planar shadows, texturing (later demos are `demoNN/` subfolders carrying their own `.vert`/`.frag`/assets). Near-identical code across demos is **deliberate** — the course shares a concept only after teaching it; don't DRY the `Paddle`/`Camera` copies.

### `mvpvisualization/` — interactive pipeline & coordinate-system visualizations
Pedagogical *aids*, not demos: standalone GLFW/ImGui programs that **show** the Cayley-graph traversal and MVP pipeline interactively (`coordinatesystems.py`, `model.py`, `modelview.py`, `modelview2d.py`, `modelvieworthoprojection.py`, `modelviewperspectiveprojection.py`, `pushmatrix.py`). Each is built on the Cayley-graph engine (§ below) via the shared GL toolkit `cayley_gl.py`. `_pipeline.py` owns the common boilerplate — window/ImGui setup, shader compilation (`compile_program`/`build_pipeline`, with per-demo `project_*.glsl` snippets appended to shared `.vert` shaders), VAO/VBO builders, the standard paddle/square/ground/axis/NDC-cube meshes, the orbit `Camera`, and `cleanup()`; each demo file keeps only its pipeline creation, `draw_*` functions, and main loop. Run by path (`python src/modelviewprojection/mvpvisualization/coordinatesystems.py`).

### `framebuffer/softwarerendering.py` — the software rasterizer
A from-scratch, no-OpenGL renderer used to teach what the GPU does: a `FrameBuffer` dataclass (backed by a PIL image, displayable inline in notebooks) with `screenspace_to_framebuffer`, `set_color`, and `draw_filled_triangle`. Carries the 2D **orientation predicates** (`is_counter_clockwise`, `is_clockwise`, `is_parallel_and_same_orientation`) — their sole consumer, which is why they live here rather than in `mathutils`.

### `cayley/` — the Cayley-graph engine
The data-structure realization of the book's central abstraction, with **no OpenGL** so it is pure and unit-testable. `cayleygraph.py`: an immutable, directed, acyclic graph whose nodes are coordinate **spaces** (per-demo `Enum`s) and whose edges are ordered sequences of *interpolable* `InvertibleFunction`s (`Step`/`Edge`/`Path`/`CayleyGraph`); `CayleyGraph.path(a, b)` breadth-first routes between spaces and composes the edge functions, auto-inverting any edge walked against its arrow — the chapter-02 rule executed instead of drawn. `cayleyscene.py` turns a graph + a declarative scene description into something the `mvpvisualization` GL demos render.

### `util/` — shared demo helpers
Small, focused, individually-documented modules the demos import: `axes.py` (unit basis gizmo, X/Y/Z red/green/blue), `windowing.py` (GLFW setup), `clipping.py` (near-plane clipping), `cameracontrols.py` (per-frame keyboard walk-around polling), `colorutils.py` (`Color4`, iterable so it unpacks into GL calls), `shading.py` (lighting/geometry helpers for the lighting-era demos), `nbplotutils.py` (notebook plotting). Each documents its own case; several intentionally overlap with per-demo copies (see the demos note).

### `notebooksrc/` and `plotsforbook/` — figure/notebook generation
`notebooksrc/` — jupytext percent-format source (`plot2d.py`, `ndc.py`, `framebuffer.py`) for the book's interactive/notebook figures. `plotsforbook/generate_plots.py` (entry point `generate_plots_for_book`, see `pyproject.toml`) plus its `plotutils/` (grid lines, matplotlib graphs, transformation plots) — a build-time script that renders the static matplotlib figures the chapters embed.

### `ports/` — faithful ports from external graphics sources
Not part of the installed package; kept in mvp's style for teaching and as porting source material.
- **`ports/openglsuperbiblev4/`** — ~104 Python ports of the *OpenGL SuperBible v4* examples, organized by chapter (`chapt01 … chapt22`). The main source Bill draws demos from; some are already slotted into the numbered demos (`axes3d`→demo19a, `atom`→19b, `solar`→19c, `sphereworld`→19e, `Block`→demo22 — see `CLAUDE.md` › "SuperBible port plan").
- **`ports/codetheclassics/`** — ports of the *Code the Classics* (vol 1 & 2) games (boing, bunner, cavern, myriapod, soccer / avenger, beatstreets, eggzy, kinetix, leadingedge). Built on **`pgzero_gl/`**, an in-repo Pygame-Zero-compatible layer that renders through OpenGL and uses gacalc `Vector2`/`Vector3` (and their in-place mutability) throughout. These exercise the library as a real consumer; see `CLAUDE.md` › "Code-the-Classics ports".

---

## 3. How gacalc is used

mvp depends on **gacalc** (the sibling geometric-algebra library at `/foo/opt/geometricalgebra`) for all of its core vector algebra and the invertible-function transform layer: `Vector2`/`Vector3` (gacalc's graded vector types — the old in-repo `Vector2D`/`Vector3D` were deleted), `InvertibleFunction`, `compose`/`inverse`/`translate`/`uniform_scale`/`scale_non_uniform`, the `at`/`steps` animation layer, and `plane_rotation` (which mvp's `rotate`/`rotate_x/y/z` bind to specific basis-vector pairs). Callers import these from gacalc directly; `mathutils.py` is a graphics-math façade around them, not a re-export.

Two artifacts of the **same released version** are consumed, both from PyPI:
- **The wheel** is the runtime dependency — pinned in `requirements.txt` (`gacalc==0.0.11` at time of writing) — and is what the code imports.
- **The sdist** is pulled in **docs-only** so the book can `literalinclude` gacalc's own `doc-region` markers (the `Vector2`/`Vector3`/`translate`/`InvertibleFunction` listings the chapters show). The Dockerfile's `ARG GACALC_VERSION` (which must match the requirements pin) fetches the sdist, and `entrypoint.sh` copies its `src/gacalc/*.py` into `book/docs/_gacalc_src/` (gitignored) before the build. Nothing imports it; it is never on `sys.path`.

Editing the *content* of a gacalc-included listing means editing gacalc and releasing it — this repo only points at it. **The full mechanics (version-bump procedure, the in-container region checker, why the sdist not a git clone) live in `tasks/reference/book-and-docs-pipeline.md` and `CLAUDE.md` › "Some listings are included from GACALC's source"** — go there rather than relying on this summary.

---

## 4. Where do I look for X

| Concern | Location |
| --- | --- |
| Vector algebra, `InvertibleFunction`, `compose`/`translate`/`uniform_scale` | external **gacalc** (`from gacalc.g2 import Vector2`, `from gacalc.transforms import …`) |
| Rotations (angle-based), `ortho`/`perspective` projection math, plane geometry, `FunctionStack` | `src/modelviewprojection/mathutils.py` |
| The real 4×4 matrix stack (demo21+, OpenGL 3.3) | `src/modelviewprojection/matrix_stack.py` |
| A specific teaching demo | `src/modelviewprojection/demos/demoNN.py` (later ones: `demos/demoNN/demoNN.py` + shaders) |
| Interactive pipeline / coordinate-system visualizations | `src/modelviewprojection/mvpvisualization/` (shared setup in `_pipeline.py`, GL toolkit in `cayley_gl.py`) |
| The software rasterizer & 2D orientation predicates | `src/modelviewprojection/framebuffer/softwarerendering.py` |
| Cayley-graph data structure / path routing (no GL) | `src/modelviewprojection/cayley/cayleygraph.py` (`cayleyscene.py` for scene→render) |
| Shared demo helpers (axes, windowing, clipping, camera, colors, shading) | `src/modelviewprojection/util/` |
| Notebook / static book figure generation | `src/modelviewprojection/notebooksrc/` (jupytext), `plotsforbook/generate_plots.py` |
| A SuperBible example port | `ports/openglsuperbiblev4/chaptNN/<name>/<name>.py` |
| A Code-the-Classics game port (and its Pygame-Zero→GL layer) | `ports/codetheclassics/vol{1,2}/<game>/<game>.py` (layer: `pgzero_gl/`) |
| The book chapters (prose + `literalinclude` markers) | `book/docs/chNN.rst` (config `book/docs/conf.py`) |
| The book build pipeline, extensions, gacalc docs-source injection | **`tasks/reference/book-and-docs-pipeline.md`** |
| Dependency pins (must stay in sync with Dockerfile) | `requirements.txt` + `CLAUDE.md` › "Keeping the Dockerfile, Makefile, and dependencies in sync" |
| Coding standard, naming exemptions, per-file ruff ignores | `CLAUDE.md` › "Coding standard (Python)" + `[tool.ruff]` in `pyproject.toml` |
| Build/run/test/format commands | `Makefile`, `README.md`, `CLAUDE.md` › "Dev environment" |
| Student exercises | `assignments/` |
