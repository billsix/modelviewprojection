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

Project structure
-----------------

| Path | What |
| --- | --- |
| `src/modelviewprojection/` | The package: `mathutils.py` (gacalc façade + graphics math), `pyMatrixStack.py`, `demos/`, `util/`, `framebuffer/`, `mvpvisualization/` |
| `ports/openglsuperbiblev4/` | ~104 Python ports of the SuperBible v4 examples |
| `book/docs/` | The Sphinx book (chapters `ch01`–`ch21`) |
| `assignments/` | Student assignments |
| `plans/` | Durable design specs; `tasks/` | short-lived work tracking |

See `CLAUDE.md` for the deep design context (the Cayley-graph abstraction, the
gacalc migration, the demo arc, and the SuperBible port plan).

Build the book
--------------
The book builds in a podman container:

```sh
make image     # build the container (Sphinx + TeX Live)
make html      # build the book (HTML/PDF/EPUB land under output/)
```
