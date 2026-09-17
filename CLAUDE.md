# MVP — context for Claude

This is **modelviewprojection**, an OpenGL graphics course taught by William "Bill" Six (billsix@gmail.com) from his own codebase. The repo *is* the textbook (Sphinx book in `book/docs/`, one chapter per demo). Teaching philosophy is **"mistake-driven development"** (stated in README) — demos are deliberately procedural, with module-level globals, so students read top-to-bottom. Don't "clean up" by introducing classes/abstractions unless asked.

External sources Bill draws from: **OpenGL SuperBible v4** (main porting source — see `ports/openglsuperbiblev4/`), *Mathematics for 3D Game Programming*, *Computer Graphics: Principles and Practice*.

---

## Central abstraction — Cayley graphs + `InvertibleFunction`

Instead of 4×4 matrices, transformations are `InvertibleFunction`s on gacalc's `Vector` (`gacalc.g2.Vector` in 2D, `gacalc.g3.Vector` in 3D), and coordinate systems form a **Cayley graph**: nodes are spaces, directed edges are these functions. To go between two spaces you trace a path, `compose` the edge functions, and `inverse` any edge traversed against its arrow — **no matrix appears anywhere in demos 01–18**. This is the *point* of the course: everything (model→world→camera→NDC, push/pop, perspective) is explained with only "function composition" and "inverse," with no linear-algebra prerequisite.

- The vector/transform layer is the external **gacalc** library (`Vector`, `InvertibleFunction`, `translate`/`uniform_scale`/`scale_non_uniform`/`compose`/`rotate`/…). `mathutils.py` adds only the graphics-specific math (projections, plane geometry, `FunctionStack`) and is **not** a re-export façade — import gacalc types from gacalc directly (`from gacalc.g2 import Vector`).
- **If a transformation can be expressed with gacalc, express it with gacalc — never hand-roll it (or its inverse, or its interpolation) in raw numpy.** Build it from the gacalc primitives (`translate`/`uniform_scale`/`scale_non_uniform`/`rotate`/`compose`), reverse it with **`inverse(f)`** (not hand-computed reciprocal/negated factors), and animate it with **`f.at(t)`** (the built-in `1+(m-1)t` / `v·t` laws — not a hand-written `1+(m-1)*t` or reversed-ratio). Realize it to a 4×4 with `cayleyscene.to_matrix(f)` **only when GL needs a matrix** (uniform upload); otherwise keep it as the `InvertibleFunction` and apply it to `Vector`s directly. `to_matrix` handles the affine case (a projective squash stays a shader — decision #4). Reaching for `np.identity`/`np.diag`/hand-set matrix entries to move geometry is the smell this rule exists to catch.
- Full detail — the primitive list, the `FunctionStack`/`fn_stack` API, the gacalc-migration history, and the Cayley-graph framing — is in `tasks/reference/architecture-overview.md` (§1/§2/§6). Remaining book-prose work: `tasks/book-rotate-prose-update.md`.

---

## Pedagogical arc (demo01 → demo24)

The same Pong scene (two paddles + a square defined relative to paddle1) is re-implemented at progressively lower-level machinery, one new concept per demo. **Extend the paddle/square/ground scene — don't invent new "scenes"** unless a concept needs it (spheres for lighting, complex meshes for normals). The demo01→24 progression, the demo20+ modern style, and the 2026-06-03 package layout are in `tasks/reference/architecture-overview.md` §2 and `tasks/reference/demo-chapter-inventory.md`.

---

## SuperBible port plan

Which SuperBible demos are already in the curriculum (do not re-port), the wishlist status, and the demo22 structure to follow are in `tasks/reference/superbible-ports-guide.md`. **Confirm the slot before writing any port** — pedagogical placement matters more than the port itself.

---

## How to apply

- When explaining or extending demos 01–18, *speak in terms of edges, paths, and inverses* — never "multiply matrices." When extending demo19+, the FF/shader matrix stack is the same idea, just executed on the GPU.
- When asked "why is this written this way?" the answer is almost always "to avoid introducing matrices before the student understands what the transformation is doing."
- The book chapters (`book/docs/chNN.rst`) are the authoritative source for terminology — use *Cayley graph*, *space*, *modelspace→NDC*, *invertible function*, not linear-algebra vocabulary.
- Reference the visualizations in `src/modelviewprojection/mvpvisualization/` (`coordinatesystems.py`, `pushmatrix.py`, `modelviewperspectiveprojection.py`) when the user wants to *show* the graph traversal interactively — pedagogical aids, not demos; part of the installed package, run by path.
- Match the demo-era style (procedural, globals, inline comments explaining the *why*), not idiomatic modern Python. When porting from external sources, port *into* his style rather than preserving the source's structure.
- **Passing a vector to immediate-mode GL: unpack it** — `GL.glVertex3f(*v)`, not per-coordinate. gacalc's `Vector` iterates its coordinates in `(e_1, e_2[, e_3])` order with the right arity; the contract is guarded by `tests/test_gl_vector_unpacking.py`.

---

## Dev environment

Bill's host is Fedora 43 (glibc 2.42). System SDL2 is the SDL2-compat shim on SDL3 — breaks SDL2-audio apps. I can build/package locally, but Bill verifies anything requiring a display, FUSE, or audio. **Never edit the vendored `entrypoint/dotfiles/.emacs.d/elpa/` tree** — it is committed on purpose (refreshed only via `make update-emacs-packages`).

---

## Keeping the Dockerfile, Makefile, and dependencies in sync

Dependencies live in three places that must agree — drift breaks image builds, so check the others when you touch one:

1. **`requirements.txt`** — the single source of truth for Python deps (`pyproject.toml` is `dynamic`, so `pip install -e .` reads it; needs Python ≥ 3.13).
2. **`Dockerfile`** — installs the heavy/native deps as *distro* `python3-*` packages (numpy, glfw, pyopengl, pillow, sympy, wxpython, matplotlib), then makes a `--system-site-packages` venv and pip-installs the rest **minus wxpython**; builds the SHA-pinned texExpToPng under `BUILD_DOCS`; bakes JupyterLab defaults under `USE_JUPYTER`.
3. **`Makefile` ↔ `Dockerfile` `ARG`s** — every `--build-arg X=$(X)` needs a matching `ARG X` (Makefile defaults `1`, Dockerfile `0`); an "one or more build args were not consumed" warning means the ARG is missing.

The texExpToPng SHA-pin details (and the `--bg`/`--fg` + `\documentclass[varwidth]{standalone}` requirements the book needs), the JupyterLab-default mechanics, and the throwaway-container recipe for resolving dep drift are in `tasks/reference/notable-subsystems.md` and `tasks/reference/book-and-docs-pipeline.md`.

---

## Code-the-Classics ports (`ports/codetheclassics/`)

A separate subtree from the course: **10 faithful game ports** (11 files — boing also has `boing_gl1.py`) under `ports/codetheclassics/vol1/` and `vol2/`, each ONE self-contained file on GLFW + OpenGL 3.3 core with its engine half inlined — the library-not-framework style. Behaviour-faithful (same RNG/update/draw order), structure-free.

- **Read `tasks/reference/code-the-classics-tightening.md` before editing any game** — the file-shape standard, the gacalc dialect (`length`→`magnitude`, `dot`→`scalar_product`, `rotate(deg)`→`plane_rotation`, …), and the composition `@`-vs-`compose` rule.
- **Gates** (`tasks/reference/tests-and-gates.md`): `tools/ctc_verify_game.sh` (frame pixel identity vs a git ref), `tools/ctc_state_trace.py` + `tools/ctc_compare_traces.py` (seeded scripted-input state trace), `tools/ctc_profile_update.py` when something feels slow. All need Xvfb on `:99` + the nested image. Audio and the gamepad are never gated — play-test.
- **gacalc vectors are FROZEN** — change a coordinate by rebinding, never in place. `ty` catches `v.x = …` but **not** `v.x += …`, so a grep for `\.(x|y|z)\s*[-+*/]?=` is part of any audit after a bulk edit.
- Audio mixer, `Rect`/`IntRect`, gacalc costs, the shim inline/strip/re-extract history (step 3 parked), and the renderer's gacalc-transform matrices are in `tasks/reference/notable-subsystems.md`, `point-type-decision.md`, and `gacalc-transforms-in-the-renderer.md`.

---

## Assignments (`assignments/`)

Student-facing exercises, runnable standalone, covered by `format.sh` (`T201` exempted — their printed output is the point). **Three carry a deliberate hole** (`assignment2-screenspace.py`, `assignment3-strafe.py`, `demo02/vec1.py`) — each verified solvable, so **leave the holes alone**; and don't "fix" their vocabulary ad hoc (the exercise design is Bill's call). Check one still renders with `tools/verify_render.sh <script> [frames] [png] [hold-keys] [--allow-blank]` (needs `make image` + an Xvfb `:99`; `--allow-blank` for `assignment2`, whose empty window is correct until its hole is filled). Full inventory and the "no reference solutions / where they live is undecided" note: `tasks/reference/architecture-overview.md` §7.

---

## The book includes code by MARKER, not by line number

Every `literalinclude` in `book/docs/` selects code by `doc-region-begin`/`doc-region-end` markers rendered with `:lineno-match:` — so **editing a source file NEVER "breaks" the book's line numbers** (Sphinx recomputes them from the markers; do **not** report a line-number shift as an impact or regression). The check before editing a source file is **"is this text inside a published region?"**, never "did the line numbers move?". A refactor that moves code must move its markers. Some listings are pulled DOCS-ONLY from gacalc's sdist. Full mechanism (region-splitting, the gacalc sdist/`_gacalc_src` pipeline, `make check-regions`, how to bump the shown gacalc version): `tasks/reference/book-and-docs-pipeline.md` §2–3.

---

## Coding standard (Python)

The Python coding standard is the shared cross-project doc **`runClaudeInContainer/tasks/reference/python-coding-standard.md`** (canonical: github.com/billsix/runClaudeInContainer; mounted in every session at `~/.claude/reference/python-coding-standard.md`) — its "modelviewprojection-specific additions" section carries mvp's own rules and worked examples. A green `make format` means the mechanical (ruff) tier is done; spend attention on the judgment calls there.

A separate **`make type-check`** gate runs `ty` (src/tests/ports) plus `tools/check_local_annotations.py src tests` — an AST checker enforcing that **every local variable in `src` + `tests` carries an explicit annotation** (not just an inferred type). It exempts un-annotatable targets (tuple-unpack, `for`/`with`/`except`/comprehension/walrus, augmented, attribute/subscript, module- and class-body). `ports/**` is exempt from the local-annotation rule (faithful-port code). The checker lives only in `make type-check`, not `make format`.

The mvp invariants worth keeping in front of you:

- **`line-length = 80`** (not the shared default 88) — the book is built as a PDF, where wider lines wrap badly.
- **`m`/`b` are protected names** (`translate(b=…)`, `uniform_scale(m=…)` for `f(x) = m*x + b`) — call them by keyword in teaching code; don't rename to `offset`/`factor`.
- **Python naming wins over the book's `\vec{R}`/`\vec{T}`/`\vec{S}` shorthand** — spell out `translate`/`rotate`/`uniform_scale`, and keep each demo's graph-to-code mapping comment above its imports.
- **GL/shader gotchas and the repo-wide GL conventions** (import order, GL constants aren't `int`, the `-1` uniform sentinel, row-major + `GL_TRUE` at upload, CCW winding, GL-resource registry, VAO-never-zero, shader resolution) live in `tasks/reference/gl-and-imgui-gotchas.md` (§7 for the conventions, §§1–6 for the failure modes).

---

## Continuous integration

CI (`.github/workflows/`) is a **thin wrapper over the make/Dockerfile system**: every workflow is `checkout` → `make <target>`, with all build/check/release logic in make targets so it runs identically in CI and on a laptop (`CONTAINER_CMD` auto-detects podman→docker; runners are ubuntu-latest, which ships Docker). If CI needs a step, add it as a `make` target first (runnable locally), never as inline YAML. Phase 1 is `format-check.yml` = `make check-format` (runs `format`, then fails on a `git diff`). Roadmap (releases on tag → a container image to a registry + a release tarball of source + the three book forms) and rationale: `tasks/github-actions-format-ci.md`.

## Tasks

Active work lives in `tasks/` (one file per task — authoritative; the session-start scan surfaces it); durable knowledge in `tasks/reference/`; completed tasks are archived under `tasks/archive/<YYYY>/<MM>/<DD>/`. There is no `plans/` directory or session HANDOFF files. The SuperBible port itself is complete; its remaining UX work is tracked by the umbrella `tasks/ports-ux-pass.md` (read first). The gacalc version-bump history and other design rationale live in `tasks/reference/design-decisions.md`.
