# Step 5: switch mvp to the Cayley graph, GL toolkit and graphers that now live in gacalc

**Status:** proposed, approved in outline (William Emerison Six <billsix@gmail.com>, 2026-11-13).
It waits for steps 1 to 4 and a published gacalc release.
**Priority:** 4
**Difficulty:** 5
**Created:** 2026-11-13
**Part of:** gacalc's umbrella, github.com/billsix/geometricalgebra
`tasks/move-mvp-gl-toolkit-to-gacalc.md`. Read its Context, Decisions and step table first; this doc
is the only step whose work happens in mvp.
**Depends on:** gacalc steps 1 to 4 (`tasks/move-mvp-gl-toolkit-to-gacalc-step-{1..4}-*.md` in
geometricalgebra), and a gacalc release that contains them, published to PyPI by the maintainer.

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
  - the ten shaders in `mvpvisualization/` (`*.vert`, `*.frag`, `*.glsl`). Before deleting them,
    check whether any mvp module that stays still loads a shader from that directory by path.

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
- **Gotcha: the pin jump.** `requirements.txt` pins `gacalc==0.0.20`. The new release comes after
  gacalc `0.1.0`, so this bump also crosses the breaking changes listed in gacalc's `CHANGELOG.md`
  under `## [0.1.0]`. Read them before switching any import. Regenerate the lock with
  `make update-pins`. The `Dockerfile`'s `ARG GACALC_VERSION=0.0.20` is a second pin: the
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

## Plan

1. Bump the gacalc pin, run `make update-pins`, and run `make image`.
2. Rewrite the imports in the files listed above, delete the moved files, and write the two runners
   (each about 20 lines: mvp's current `FUNCTIONS` or `SURFACES` list and a `run(...)` call). Keep
   `graphingcalculator/imgui.ini` only if step 4 kept writing it.
3. Run `make test`, `make type-check`, `make format` and `make check-regions`, then build the book.
4. Run both graphers and a Cayley demo (demo21 or later) on the host, and check that they look and
   behave as before.
5. Make the doc updates listed above, plus a `CHANGELOG.md` entry if mvp keeps one.
