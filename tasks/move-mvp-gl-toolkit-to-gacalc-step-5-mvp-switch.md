# Step 5: switch mvp to the Cayley graph, GL toolkit and graphers that now live in gacalc

**Status:** blocked. Approved in outline (William Emerison Six <billsix@gmail.com>, 2026-11-13).
**Blocked on:** gacalc 0.1.1 published to PyPI. The maintainer runs `make release` in
github.com/billsix/geometricalgebra; steps 1 to 4 are committed there as 0.1.1, untagged.
**Recheck:** `pip index versions gacalc` (or `uv pip compile` against a requirements line
`gacalc==0.1.1`). Cleared when 0.1.1 is listed.
**Priority:** 4
**Difficulty:** 4
**Created:** 2026-11-13
**Part of:** gacalc's umbrella, github.com/billsix/geometricalgebra
`tasks/move-mvp-gl-toolkit-to-gacalc.md`. Read its Context, Decisions and step table first; this doc
is the only step whose work happens in mvp.
**Depends on:** gacalc steps 1 to 4, done 2026-11-13. Their records are in geometricalgebra
`tasks/archive/2026/11/13/move-mvp-gl-toolkit-to-gacalc-step-{1,2,3,4}-*.md`.

## BLUF

Once gacalc ships `gacalc.cayley`, `gacalc.gl` and the `gl` extra, mvp should use those copies and
delete its own:
- pin the new gacalc;
- rewrite the imports;
- remove the moved modules, shaders and tests;
- reduce `graphingcalculator/grapher2d.py` and `grapher3d.py` to short runners that pass mvp's
  function lists to `gacalc.gl.grapher2d.run` and `grapher3d.run`.

Done means mvp's gates pass (`make test`, `make type-check`, `make format`, and a `make docs` build
showing that the book's quoted code is unchanged) with none of the moved files left in mvp.

## Context

- **Files deleted** (all under `src/modelviewprojection/`):
  - `cayley/cayleygraph.py` and `cayley/cayleyscene.py`;
  - `matrix_stack.py`;
  - `mvpvisualization/_pipeline.py`, `cayley_gl.py` and `labels.py`;
  - the eleven shaders in `mvpvisualization/` (`*.vert`, `*.frag`, `*.geom`, `*.glsl`). The
    visualizations that stay (`model.py`, `modelview.py` and the rest) load them by passing their
    own directory as `shader_dir`. gacalc ships the same shaders as package data and exposes their
    directory as `gacalc.gl.SHADER_DIR`, so each such call changes to
    `shader_dir=gacalc.gl.SHADER_DIR` before the files are deleted. Grep for `shader_dir=` and for
    `__file__`-based shader paths (the graphers' `MVP_SHADER_DIR`).

  The tests go too: `tests/test_cayley_graph.py`, `test_cayley_scene.py`, `test_focus_to_matrix.py`
  and `test_matrix_stack.py`.
- **Files whose imports change** (found 2026-11-13 by grepping for `matrix_stack`, `mvpvisualization`
  and `cayley`; re-run that grep, since the list may have grown):
  - `demos/demo21`, `demo22`, `demo22a`, `demo22b`, `demo23` and `demo24`;
  - `mvpvisualization/coordinatesystems.py`, `model.py`, `modelview.py`, `modelview2d.py`,
    `modelvieworthoprojection.py`, `modelviewperspectiveprojection.py` and `pushmatrix.py`;
  - `pgzero_gl/renderer.py` and `renderer_gl1.py`;
  - `util/shaderutils.py` and `wxapp.py`.
- **Gotcha: the book quotes the demos.** If a `doc-region` the book `literalinclude`s contains an
  import line, the rendered book text changes. Run `make check-regions` (or
  `tools/check_doc_regions.py`) and read the affected pages. The book quotes none of the moved files
  themselves; `book/docs/ch02.rst` only shows the Cayley-graph figure.
- **The pin jump, 0.0.20 → 0.1.1, is safe for mvp's current code** (measured 2026-11-13; see
  "Findings"). It crosses gacalc's `## [0.1.0]` breaking changes, but nothing mvp uses broke.
  Regenerate the lock with `make update-pins`. The `Dockerfile`'s `ARG GACALC_VERSION=0.0.20` is a
  second pin: the
  docs-only gacalc sdist the book quotes from. Bump it in step with the first. Its copy step takes
  only `src/gacalc/*.py`, which matters only if the book ever quotes `gacalc.cayley` or `gacalc.gl`.
- **`to_matrix` moves too.** mvp's `CLAUDE.md` tells authors to realise a transform as a 4×4 with
  `cayleyscene.to_matrix(f)`. After the move that is `gacalc.cayley.cayleyscene.to_matrix`, so update
  that rule wherever it is quoted (`CLAUDE.md`, `tasks/reference/architecture-overview.md`).
- **mvp still needs its own GL dependencies.** The demos and `pgzero_gl` use glfw, PyOpenGL and
  imgui directly, so keep them in `requirements.txt`. Installing `gacalc[gl]` must not conflict with
  mvp's pins.
- **Docs that describe the moved code** and need rewriting to point at gacalc:
  - `CLAUDE.md` calls the Cayley graph and `InvertibleFunction` mvp's central abstraction;
  - `tasks/reference/architecture-overview.md` (the graphers paragraph and the Cayley layer);
  - `tasks/reference/gl-and-imgui-gotchas.md` sections 8 and 9: keep a pointer to gacalc's
    `tasks/reference/gl-toolkit.md`;
  - `tasks/reference/notable-subsystems.md`;
  - `tasks/reference/gacalc-transforms-in-the-renderer.md`.
- `mathutils.py` keeps `rotate_x`, `rotate_y` and `rotate_z` for the book. gacalc's moved code no
  longer uses them. The open question about re-expressing them is `tasks/mathutils-helpers-via-gacalc.md`.
- **What gacalc 0.1.1 actually provides** (steps 1 to 4, as built):
  - `gacalc.cayley.cayleygraph` and `.cayleyscene`;
  - `gacalc.gl.matrix_stack`, `._pipeline`, `.cayley_gl` and `.labels`;
  - `gacalc.gl.SHADER_DIR` (the eleven shaders);
  - `gacalc.gl.grapher2d.run(functions, title=…)` with `PlottedFunction`, and
    `gacalc.gl.grapher3d.run(surfaces, title=…)` with `Surface`;
  - the `gl` extra.

  Signatures are mvp's, with three small widenings: `to_matrix` takes
  `InvertibleFunction[Vector]`, and `make_vao` / `build_cylinders_for_edges` accept any `Sequence`.
  gacalc's runners (`examples/grapher2d.py`, `examples/grapher3d.py` there) show the runner shape.

## Findings (2026-11-13, before the release)

The agent ran mvp's suite and type check in a throwaway container from the host's
`localhost/modelviewprojection` image, mvp's working tree mounted at `/mvp`, nothing committed.
This was done twice: once on the image's own gacalc 0.0.20, and once with gacalc 0.1.1 installed
from geometricalgebra's checkout.
- **Tests:** 112 passed on both. A first run on 0.1.1 took 9 to 17 s, because a fresh install
  compiles the large generated modules once; steady state was 1.85 s, against 5.7 s for the
  0.0.20 baseline's single run. No slowdown.
- **`ty`:** identical on both. `src` has the same 22 diagnostics (17 `glfw._GLFWwindowPointerT`
  import-not-found, 3 unused-ignore, 2 not-subscriptable); `tests` and both code-the-classics
  trees are clean. So the jump adds no type errors. The 22 come from the stale image (next bullet),
  not from gacalc; confirm on a rebuilt image.
- **The host's mvp image predates the 2026-11-12 "venv copy wins" fix** (it was 27 hours old on
  2026-11-13). In it, bare `pytest` is the distro script and dies with `No module named 'gacalc'`.
  `python -m pytest` works. A host `make image` picks up the fix, and step 5 needs a rebuild anyway.

## Plan

1. Bump the gacalc pin in `requirements.txt` and `ARG GACALC_VERSION` to 0.1.1, run
   `make update-pins`, and run `make image`.
2. Rewrite the imports in the files listed above, delete the moved files, and write the two runners
   (each about 20 lines: mvp's current `FUNCTIONS` or `SURFACES` list and a `run(...)` call). gacalc's
   graphers still let imgui write `imgui.ini` to the working directory; mvp already gitignores it.
3. Run `make test`, `make type-check`, `make format` and `make check-regions`, then build the book.
4. Run both graphers and a Cayley demo (demo21 or later) on the host, and check that they look and
   behave as before.
5. Make the doc updates listed above, plus a `CHANGELOG.md` entry if mvp keeps one.
