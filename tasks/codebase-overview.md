# Codebase overview — modelviewprojection (Claude's edification notes)

> Durable orientation notes for myself. Written 2026-05-26. The repo also has a
> rich `CLAUDE.md` (read it first) and detailed specs in `plans/`. This file is
> the "how is the code actually laid out and what is it for" companion to those.

## What this project is

`modelviewprojection` is **Bill Six's OpenGL graphics course, and the repo *is*
the textbook.** A Sphinx book lives in `book/docs/` (one `.rst` chapter per
demo), and the runnable demos live in `src/modelviewprojection/`. Teaching
philosophy: **"mistake-driven development"** — demos are deliberately
procedural with module-level globals so students read top-to-bottom. Do **not**
refactor into classes/abstractions unless asked.

The pedagogical hook: instead of 4×4 matrices, transformations are
`InvertibleFunction`s and coordinate systems form a **Cayley graph** (nodes =
spaces, directed edges = invertible functions between spaces). Students learn
everything via "function composition" + "inverse" with no linear-algebra
prerequisite. Matrices don't appear until demo19 (fixed-function GL), by which
point they're framed as the same idea executed on the GPU.

## Repository layout

```
src/modelviewprojection/
  mathutils.py        # THE core abstraction (see below). ~1050 lines.
  pyMatrixStack.py    # Pure-Python reimpl of the GL fixed-function matrix stack
  colorutils.py       # Color4 etc.
  nbplotutils.py, softwarerendering.py, wxapp*.py  # support / older bits
  demo01.py ... demo19e.py        # single-file demos (2D -> 3D -> fixed-func GL)
  demo20/ demo21/ demo22/         # OpenGL 3.3 Core demos: subfolder w/ .vert/.frag (+ .tga assets)
  demo22a/ demo23/ demo24/        # modernized SuperBible ports: pyramid / litjet / sphereworld
  notebooksrc/        # framebuffer.py, ndc.py, plot2d.py — jupytext % scripts -> .ipynb at build
  plotsforbook/       # matplotlib figure generation for the book

book/docs/            # the Sphinx book
  ch01.rst .. ch21.rst, intro/perspective/glossary/api/... ; index.rst toctree
  conf.py             # inlinetex_default_size=150 knob; _ext on sys.path
  _ext/inlinetex.py   # custom Sphinx ext: renders LaTeX -> PNG via Bill's texExpToPng (for EPUB)
  _static/            # generated PNGs, screenshots, tex_exp_to_png/ C tool source
  Makefile            # make html / latexpdf / epub

assignments/          # student assignments (assignment1, assignment2-screenspace, assignment3-strafe)
mvpVisualization/     # interactive pedagogical aids (coordinatesystems/, pushmatrix/, ...) — NOT demos
ports/openglsuperbiblev4/  # 1:1 SuperBible 4e -> Python port tree (PARKED this session)
tests/                # test_mathutils.py (big), test_firstclassfunctions.py
plans/                # detailed specs + dated HANDOFF-*.md notes (repo's durable notes home)
tasks/                # THIS dir — lightweight session task tracker (global CLAUDE.md convention)
```

## The core abstraction (`src/modelviewprojection/mathutils.py`)

- `Vector` -> `Vector1D` -> `Vector2D` -> `Vector3D` dataclass hierarchy with
  `__add__`/`__sub__`/`__mul__`/`__neg__`/dot etc.
- `InvertibleFunction[V]` = `(func, inverse, latex_repr, latex_repr_inv)`.
  `__call__` runs forward; `inverse(f)` swaps fwd/inv; `f1 @ f2` = `compose([f1, f2])`.
- Transform primitives: `translate`, `uniform_scale`, `scale_non_uniform_2d/3d`,
  `rotate` (2D), `rotate_90_degrees`, `rotate_around`, `rotate_x/y/z` (3D),
  `ortho`, `perspective`, `cs_to_ndc_space_fn`, `identity`.
- Composition: `compose(list)` traverses a path; `inverse(...)` walks an edge
  backwards; plus `compose_intermediate_fns*` variants for visualizations.
- Geometry helpers (added 2026-04-28): `find_normal`, `plane_equation`,
  `distance_to_plane` on `Vector3D`, CCW winding convention.
- `FunctionStack` + module-level `fn_stack` = Python analogue of the GL matrix
  stack: `push`/`pop`/`modelspace_to_ndc_fn()` (= `compose(stack)`) and the
  `push_transformation(f)` context manager.

`pyMatrixStack.py` is the demo20+ counterpart: a real 4×4 numpy matrix stack
(`MatrixStack` enum: model/view/projection/modelview/modelviewprojection) with
`rotate_x/y/z`, `translate`, `scale`, `ortho`, `perspective`, `multiply`, and a
`push_matrix(stack)` context manager. Matrices upload as the `mvpMatrix` uniform.

## Demo arc (don't invent new scenes — extend the paddle/square/ground Pong scene)

- **01–06** 2D immediate-mode (`glBegin`/`glEnd`), composition via `mathutils`.
- **07** Pong paddles introduced (the running scene). **12** matrix-stack concept.
- **16** jump to 3D. **19** fixed-function GL 2.1 (first real matrices, hidden
  behind familiar API). **19a–e** SuperBible fixed-func ports (axes3d/atom/solar/sphereworld).
- **20** fixed-func MVP + trivial pass-through shader (shader compilation only).
- **21+** OpenGL 3.3 Core, no fixed function; `pyMatrixStack` for MVP,
  `compile_program(vert, frag)`, VAOs/VBOs tracked in `all_vaos`/`all_vbos`.
- **22** lighting (Lambert) + planar shadows + texturing.
- **22a/23/24** modernized ports now present in code: pyramid / litjet /
  sphereworld. **NOTE:** these have no book chapters yet (index.rst toctree
  stops at ch21) — possible future curriculum work.

## Build / run pipeline (and my container constraints)

The book builds **inside a podman container** (`Dockerfile` + `Makefile`).
`entrypoint/entrypoint.sh` runs the real pipeline:
1. `pytest --exitfirst` (build aborts if tests fail).
2. `jupytext` converts `notebooksrc/*.py` % scripts into `.ipynb` in both
   `notebooks/` and `book/docs/`.
3. editable install, then in `book/docs/`: `make html` → `make latexpdf` →
   `make epub`; outputs copied to `/output/modelviewprojection/`.

`make html` / `make latexpdf` / `make epub` (from `book/docs/Makefile`) are the
real targets. The root `Makefile` is podman orchestration (`make shell`,
`make html`, `make image`).

**What I (Claude in this container) can and cannot do:**
- ✅ Read/edit code, run `pytest`, run `ruff`, run the AST/hash logic in
  `inlinetex.py`, `git add` to stage.
- ❌ **No commits** (Bill commits + GPG-signs outside the container).
- ❌ **No graphical / display / GL demos** — needs X/Wayland; Bill verifies those.
- ❌ **`texExpToPng` is not installed here** — only the podman *build* container
  has it (built via meson from `_static/tex_exp_to_png/`). So I can write the
  inlinetex extension but can't smoke-test its PNG rendering; only Bill's
  `make html` exercises the full doc build.
- ❌ Auto-mode classifier blocks me from `rm -rf` of pre-existing paths (e.g.
  clearing a stale `_build/latex/`); Bill has to.

## Authoritative sources / conventions

- Book chapters (`book/docs/chNN.rst`) own the terminology: *Cayley graph*,
  *space*, *modelspace→NDC*, *invertible function* — never linear-algebra vocab.
- External porting source: **OpenGL SuperBible 4e** (`ports/openglsuperbiblev4/`).
- `ruff` lint config in `pyproject.toml`; `entrypoint/format.sh` for formatting.
- TODO.org (root) = Bill's running curriculum/chapter to-do list (lots of small
  per-chapter edits). `TODO` (root) = a single one-liner.
</content>
</invoke>
