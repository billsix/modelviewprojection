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
| `src/modelviewprojection/` | The package: `mathutils.py` (gacalc façade + graphics math), `pyMatrixStack.py`, `demos/`, `util/`, `framebuffer/`, `mvpvisualization/` |
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
