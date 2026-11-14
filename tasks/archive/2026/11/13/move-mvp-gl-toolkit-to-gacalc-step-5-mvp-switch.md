# Step 5: switch mvp to the Cayley graph, GL toolkit and graphers that now live in gacalc

**Done:** 2026-11-13. **Created:** 2026-11-13 (William Emerison Six <billsix@gmail.com>).
**Part of:** gacalc's umbrella, github.com/billsix/geometricalgebra
`tasks/archive/2026/11/13/move-mvp-gl-toolkit-to-gacalc.md`. Its "What moved", Decisions and
"Notes for step 5" hold the cross-step reasoning; this was the only step whose work was in mvp.
**Depends on:** gacalc steps 1 to 4 (records in geometricalgebra
`tasks/archive/2026/11/13/move-mvp-gl-toolkit-to-gacalc-step-{1,2,3,4}-*.md`), released as gacalc
0.1.1.

## Outcome

mvp now uses gacalc's copies of the Cayley-graph engine (`gacalc.cayley`), the GL toolkit
(`gacalc.gl`: `matrix_stack`, `_pipeline`, `cayley_gl`, `labels`, the shaders at
`gacalc.gl.SHADER_DIR`) and the graphers, and none of the moved files remain in mvp. The two
grapher programs are short runners holding only mvp's function lists. All gates passed, and the
maintainer confirmed both graphers and the Cayley visualizations on the host display and in the
container.

## What changed

- **Pins.** `requirements.txt` went from `gacalc==0.0.20` to `gacalc[gl]==0.1.1`, and the
  Dockerfile's docs-only `ARG GACALC_VERSION` from 0.0.20 to 0.1.1. The regenerated
  `constraints.txt` changed only the gacalc line, because the `gl` extra's glfw, PyOpenGL,
  imgui-bundle and Pillow were already pinned at compatible versions. mvp keeps those four in its
  own `requirements.txt`, since the demos and `pgzero_gl` use them directly.
- **Deleted, 22 files** under `src/modelviewprojection/` and `tests/`: `cayley/` (the package,
  `cayleygraph.py`, `cayleyscene.py`), `matrix_stack.py`, `mvpvisualization/_pipeline.py`,
  `cayley_gl.py`, `labels.py`, the eleven `mvpvisualization` shaders, and the four tests that
  moved with them (`test_cayley_graph.py`, `test_cayley_scene.py`, `test_focus_to_matrix.py`,
  `test_matrix_stack.py`). `pytest.ini` dropped the two deleted modules from `testpaths`.
- **Imports, 16 files:** demo21, 22, 22a, 22b, 23 and 24; the seven visualizations in
  `mvpvisualization/`; `pgzero_gl/renderer.py` and `renderer_gl1.py`; `util/shaderutils.py`. The
  visualizations also dropped their `__file__`-based shader directory for
  `shader_dir=SHADER_DIR` (and the `import os` that only served it). A codemod did this:
  `tasks/adhoc/move-mvp-gl-toolkit-to-gacalc-step-5-mvp-switch/rewrite_imports.sh` (removed when
  this task was archived; it is in git history), idempotent (a second run changed nothing);
  `make format` then sorted the gacalc imports into the third-party block. `wxapp.py`'s local
  `GLenum` copy kept its reason, with its comment repointed.
- **Graphers.** `graphingcalculator/grapher2d.py` and `grapher3d.py` went from about 600 and 530
  lines to 54 and 60: mvp's `FUNCTIONS` / `SURFACES` lists, unchanged, passed to
  `gacalc.gl.grapher2d.run` / `grapher3d.run` with the same window titles.
- **Docs.** `CLAUDE.md` (the `to_matrix` rule, a new bullet saying the engine and toolkit live in
  gacalc and are changed there, the graphers' menubar note), `README.md`, and the reference docs
  that named the moved files: `architecture-overview.md`, `notable-subsystems.md`,
  `gl-and-imgui-gotchas.md` (a pointer to gacalc's `tasks/reference/gl-toolkit.md` at §8),
  `tests-and-gates.md`, `python-coding-standard-mvp.md`, `demo-chapter-inventory.md`,
  `lighting-and-shading.md`, `code-the-classics-tightening.md`,
  `library-not-framework-authorship-style.md` and `book-and-docs-pipeline.md`.
  `gacalc-transforms-in-the-renderer.md` turned out not to name any moved file. mvp keeps no
  `CHANGELOG.md`.

## Decisions

- **Regenerate the lock against the existing image, not with `make update-pins`.** That target
  depends on `image`, which would install the new requirement against the old lock and fail. The
  agent ran `update-pins`'s own `podman run` line against the existing image instead, then ran
  `make image`.
- **Import the shader directory by name**, added to the visualizations' existing `cayley_gl`
  import (`from gacalc.gl import SHADER_DIR, cayley_gl`), rather than a separate `import gacalc.gl`
  for `gacalc.gl.SHADER_DIR`.
- **Keep mvp's grapher function lists as they were** (plain-math lambdas), rather than adopting
  gacalc's example runners, which plot geometric-algebra quantities. The runners exist so each repo
  plots its own functions.
- **The pin jump needed no migration.** Measured before the release by installing 0.1.1 over the
  image's 0.0.20 in a throwaway container: 112 tests passed on both, and `ty` gave the same 22
  diagnostics on both. The 22 came from the stale host image (it predated the 2026-11-12 "venv copy
  wins" fix, so bare `pytest` there was the distro script); they were gone on the rebuilt image.

## Verification

- `make test`: 70 passed. The 42 fewer than before are exactly the moved tests: 36 test functions in
  the four deleted test files plus 6 doctest items in the moved modules.
- `make type-check` and `make format`: clean.
- `make check-regions`: anchors resolve, and every rewritten import line in demo21–24 lies outside
  a book doc-region, so the book's quoted code is unchanged. `make docs` built HTML, PDF and EPUB;
  its 139 warnings were all EPUB `unknown mimetype` notices for `_static` files.
- Headless `tools/verify_render.sh` (with `PROBE_DISPLAY` set to the running Xvfb) passed for
  `pushmatrix.py` (shaders loaded from `SHADER_DIR`), both graphers (curves and TeX labels drawn)
  and demo21.
- The maintainer ran both graphers and the Cayley visualizations on the host display and in the
  container (2026-11-13).
