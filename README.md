ModelViewProjection
===================

http://billsix.github.io/modelviewprojection/intro.html

Learn how to build 3D graphics from the ground up. This codebase demonstrates how
to create objects, put them where you want them to go, view the scene with a camera
that can move, and project that 3D data onto a 2D screen.

The course is built on one pedagogical hook: instead of 4×4 matrices, transformations
are **invertible functions** and coordinate systems form a **Cayley graph** (nodes =
spaces, edges = transformations) — so you learn everything via function composition
and inverses, with no linear-algebra prerequisite. The math now lives in the
**gacalc** geometric-algebra library (wrapped by `mathutils.py`). The repo also
includes faithful Python ports of the **OpenGL SuperBible v4** examples under
`ports/openglsuperbiblev4/`.

For further reading (lighting, shadows, more explicit OpenGL):

1. OpenGL Redbook / Bluebook (and **OpenGL SuperBible v4** — it covers both fixed
   function and shaders)
2. *Mathematics for 3D Game Programming and Computer Graphics*
3. *Computer Graphics: Principles and Practice* (2nd ed., in C)

For ray tracing: *Physically Based Rendering*; *Ray Tracing from the Ground Up*.

Approach
--------
This book uses **"mistake-driven development"**: it shows, incrementally, how to
build a more complex graphics application — making mistakes along the way, then
fixing them. Demos are deliberately procedural (module-level globals) so they read
top-to-bottom.

Running a demo
--------------
Install Python 3 and `glfw`, then use a virtualenv:

```sh
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools
python -m pip install -e .
python src/modelviewprojection/demos/demo05.py
```

(On Windows, use the Visual Studio 2019 Developer Command Prompt for the venv steps.)

Math-demo labels (optional): install texExpToPng
------------------------------------------------
Some math visualizations (e.g. `src/modelviewprojection/mathdemos/crossproduct.py`)
annotate the vectors with LaTeX labels rendered by **texExpToPng** — a small C tool
(wrapping `latex` + `dvipng`) vendored at `book/docs/_static/tex_exp_to_png/`. The
labels are **optional**: if `texExpToPng` is not on your `PATH`, the demos run
normally, just without labels. (Inside the podman image it is already built by
`make image`; these steps are only for running demos directly on your host.)

Run the block for your platform from the **repo root** — copy, paste, enter:

**Fedora / RHEL**
```sh
sudo dnf install -y gcc glib2-devel meson ninja-build pkgconf-pkg-config \
                    texlive-scheme-basic texlive-standalone texlive-amsmath texlive-dvipng
meson setup /tmp/texexp-build book/docs/_static/tex_exp_to_png --prefix="$HOME/.local"
meson compile -C /tmp/texexp-build
meson install -C /tmp/texexp-build
export PATH="$HOME/.local/bin:$PATH"   # add this line to ~/.bashrc to make it permanent
texExpToPng --help                     # should list --bg and --fg
```

**Debian / Ubuntu**
```sh
sudo apt-get update && sudo apt-get install -y \
     build-essential libglib2.0-dev meson ninja-build pkg-config \
     texlive-latex-base texlive-latex-extra dvipng
meson setup /tmp/texexp-build book/docs/_static/tex_exp_to_png --prefix="$HOME/.local"
meson compile -C /tmp/texexp-build
meson install -C /tmp/texexp-build
export PATH="$HOME/.local/bin:$PATH"   # add this line to ~/.bashrc to make it permanent
texExpToPng --help                     # should list --bg and --fg
```

Verify it actually renders (this is the exact command the demo runs):
```sh
texExpToPng --exp '$\vec a \times \vec b$' --size 600 --fg "rgb 1 1 1" --bg Transparent --output /tmp/lbl.png
```
If `latex` errors about a missing `.sty`/`.cls`, install the matching `texlive-…`
(Fedora) / `texlive-…` (Debian) package and re-run.

Project structure
-----------------

| Path | What |
| --- | --- |
| `src/modelviewprojection/` | The package: `mathutils.py` (gacalc façade + graphics math), `matrix_stack.py`, `demos/`, `util/`, `framebuffer/`, `mvpvisualization/` |
| `ports/openglsuperbiblev4/` | ~104 Python ports of the SuperBible v4 examples |
| `book/docs/` | The Sphinx book (chapters `ch01`–`ch21`) |
| `assignments/` | Student assignments (standalone exercises; lint/format-gated by `format.sh`) |
| `tasks/` | Active work (one file per task); completed work under `tasks/archive/<YYYY>/<MM>/<DD>/` |

See `CLAUDE.md` for the deep design context (the Cayley-graph abstraction, the
gacalc migration, the demo arc, and the SuperBible port plan).

Build the book
--------------
The book builds in a podman container:

```sh
make image     # build the container (Sphinx + TeX Live)
make html      # build the book (HTML/PDF/EPUB land under output/)
```

Contributing
------------
Run the gate before sending a change:

```sh
make format    # ruff check --fix, ruff format, and ty over src/tests/ports
make test      # or: python -m pytest -q   (doctests in the library run too)
```

Most of PEP 8 is enforced mechanically by `ruff` (see `[tool.ruff]` in
`pyproject.toml`), so a green `make format` settles layout, imports, naming
(`pep8-naming`), and modern-union syntax. Two things about that config are worth
knowing before you fight it:

* **`line-length = 80`**, governing the formatter *and* `E501`. The book is built
  as a PDF, where wider lines wrap badly or run off the page.
* **Every `per-file-ignores` entry carries its reason inline.** Read it before
  "fixing" a name ruff flagged somewhere else. The main one is `wxapp*.py`, which
  keeps wxPython's `OnPaint`/`InitGL`/`OnDraw` because wx looks up those exact names.
  Python naming otherwise wins over mathematical shorthand, including in the demos:
  the chapters' Cayley-graph edges are labelled `\vec{R}`/`\vec{T}`/`\vec{S}`, but
  the code says `rotate()`/`translate()`/`uniform_scale()`, with a comment above each
  demo's imports mapping the diagram onto the source.

The judgment calls ruff can't check — annotation policy, function shape, when to
inline a single-use value, and the OpenGL-specific conventions (row-major matrices
with the transpose at the `glUniformMatrix4fv` boundary, CCW winding, the pinned
GL-import order, the `-1` "uniform not present" sentinel) — live in **`CLAUDE.md` ›
"Coding standard (Python)"**, which is the canonical source.

Two repo-specific things that surprise newcomers:

* **`doc-region-begin` / `doc-region-end` comments are part of the build.** The book
  excerpts code between them; a refactor that moves code must move its markers.
* **Duplication across `demos/` is often deliberate.** The course teaches a concept
  in one chapter and only then shares it; `util/clipping.py`, `util/windowing.py` and
  `util/cameracontrols.py` document their own cases. Don't DRY the near-identical
  `Paddle`/`Camera` classes without reading those notes.
