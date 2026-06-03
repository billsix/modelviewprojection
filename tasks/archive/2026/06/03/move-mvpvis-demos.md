# Move the mvpVisualization demos into the package

**Status:** complete
**Completed:** 2026-06-03
**Started:** 2026-06-03

## Executed (2026-06-03)

- `git mv` the tree into `src/modelviewprojection/mvpvisualization/`, flattening each
  `<name>/<name>.py` → `<name>.py`; added `__init__.py`; removed the old shell (caches,
  `imgui.ini`, stray `#…#` autosaves).
- Rewrote all imports to absolute package form — no `sys.path.insert`, no `PWD`, no
  `# noqa: E402`: demos use `from modelviewprojection.mvpvisualization import cayley_gl,
  cayleygraph, cayleyscene` + `from modelviewprojection import pyMatrixStack as ms` +
  `from modelviewprojection.mathutils import …` + plain `import glfw` / `import OpenGL.GL`.
  `cayley_gl` imports `_pipeline` from the package; `cayleyscene` imports `cayleygraph` from
  the package; `cayleygraph` was already absolute. `_SHARED_DIR = dirname(__file__)` unchanged.
- Book prose (`.rst` source): updated run-commands to
  `python src/modelviewprojection/mvpvisualization/<name>.py` in ch10/17/19; repointed the two
  stale ch17 callouts (`demoAnimation.py`, `demoViewWorldTopLevel.py`) →
  `modelviewperspectiveprojection.py` (it animates both the placement and the camera-inversion
  those paragraphs describe); updated the `mvp_dict.pws` word to `mvpvisualization`.
- Tests: `test_cayley_graph.py` / `test_cayley_scene.py` import from
  `modelviewprojection.mvpvisualization`; deleted the now-obsolete `tests/conftest.py` path hack.
- Also updated live references outside the book: `CLAUDE.md` line 72, `tasks/codebase-overview.md`
  tree, and the credit comment in `ports/openglsuperbiblev4/_common.py`. Fixed two pre-existing
  ruff nits in `_pipeline.py` (`typing.Tuple`→`tuple`, a `print`) surfaced by moving it into the
  linted `src/` tree.

**Verified:** moved tree + tests py_compile + ruff clean; 85 headless tests pass via the package
path; no live `mvpVisualization/` references remain (only generated `_build/` and historical
`plans/` notes, intentionally left). Bill runs a demo or two by path to confirm GL. Note: the
`_common.py` import-sort nit is pre-existing in the PARKED ports tree, out of scope.

## Decisions (Bill, 2026-06-03)

1. **Subpackage name:** lowercase **`mvpvisualization`**.
2. **Run as scripts, not modules:** invoked by file path
   (`python src/modelviewprojection/mvpvisualization/<name>.py`), never
   `python -m …`. ⇒ demos must use **absolute** imports
   (`from modelviewprojection.mvpvisualization import cayley_gl`) — relative
   imports fail in a path-run `__main__`. (Works because `modelviewprojection`
   is already importable in Bill's env — same mechanism that makes today's
   `from modelviewprojection.mathutils import …` work.) No `main()` wrapper /
   console-scripts needed (the modules are never imported, only run).
3. **Non-editable installs don't matter:** keep `__file__`-relative shader loading
   as-is; NO `package-data` / `importlib.resources` work needed.
4. **Stale ch17 refs:** repoint `demoAnimation.py` / `demoViewWorldTopLevel.py` to
   the closest current demos (the animated `modelviewperspectiveprojection` and the
   interactive `coordinatesystems`).

## Goal

Move the `mvpVisualization/` demos (currently a sibling of `src/` at the repo
root) under `src/modelviewprojection/` so they ship as part of the installed
Python package; update the book's references to the new paths; and rewrite their
imports so there's no `sys.path` manipulation executed before the import
statements — now that the package itself is importable, the demos can use clean
top-of-file package imports.

## Findings (current state, 2026-06-03)

**Layout.** `mvpVisualization/` holds the engine modules (`cayley_gl.py`,
`cayleygraph.py`, `cayleyscene.py`, `_pipeline.py`), the **shared** shaders
(`*.glsl`, `*.vert`, `*.frag`, `*.geom`) at its top level, and seven per-demo
subdirs each containing only `<name>.py` (shaders are NOT per-demo). So the demo
dirs are vestigial — the tree can flatten on the move.

**Why the `sys.path` hack exists.** Every demo and `_pipeline.py` do
`sys.path.insert(0, os.path.dirname(PWD))` then `import cayley_gl` / `import
cayleygraph` / etc. The hack is purely to find those sibling modules (they're not
in the package) and to reach `modelviewprojection.mathutils` /
`...pyMatrixStack`. Once the engine modules live *inside* the package, the hack
is unnecessary and the `# noqa: E402` import-after-code goes away.

**Shaders load by `__file__`, not cwd.** `_pipeline.py` reads shaders from
`_SHARED_DIR = os.path.dirname(os.path.abspath(__file__))` via
`open(os.path.join(_SHARED_DIR, name))`. So they move cleanly with `_pipeline.py`
and work regardless of cwd — *provided* they're present next to it (true for an
editable install; needs package-data for a built wheel — see Open questions).

**The glfw/GL-before-imgui order is self-contained.** `cayley_gl` imports glfw,
then `OpenGL.GL`, then `imgui_bundle` in that order. Any demo that imports
`cayley_gl` gets the order satisfied internally, so demos can import glfw/GL at
the top in any order — the order constraint does NOT require the `sys.path`
prelude or the E402 dance.

**Book references** (source `.rst` only; `_build/` is generated, regenerate from
source — do not hand-edit):
- Prose "run python mvpVisualization/<name>/<name>.py": `ch10.rst:253`,
  `ch17.rst:87,114`, `ch19.rst:66`.
- `ch17.rst:189,205` point at `../mvpVisualization/demoAnimation.py` and
  `demoViewWorldTopLevel.py` — **these files don't exist** in the current tree
  (stale, predate the Cayley rewrite). Decide: repoint or remove.
- `mvp_dict.pws:204` is the spell-check dictionary entry "mvpVisualization"
  (harmless; update if the word disappears from prose).
- No `literalinclude` of mvpViz files — book only prose-references them. (Book
  demo source is included via `../../src/modelviewprojection/demoNN.py`, the
  pattern any future include of these would follow.)

**Packaging.** `pyproject.toml` uses `setuptools.packages.find where=["src"]`
(auto-discovers everything under `src/`). There is **no** `package-data` config,
so non-`.py` files (shaders) are not declared for wheels — a latent gap that
already affects `src/.../demo20/`'s `.vert/.frag`. Running from the editable repo
works because `__file__` points at the source tree.

**Precedent.** `src/modelviewprojection/demo20/` is a demo-with-shaders subdir of
the package already — the target pattern.

## Proposed target structure (flatten — shaders already shared)

```
src/modelviewprojection/mvpvisualization/
    __init__.py
    cayley_gl.py  cayleygraph.py  cayleyscene.py  _pipeline.py
    *.glsl  *.vert  *.frag  *.geom            # shared shaders (package data)
    model.py  pushmatrix.py  modelview.py  modelview2d.py
    modelvieworthoprojection.py  modelviewperspectiveprojection.py
    coordinatesystems.py
```

Imports become (no `sys.path`, no `PWD`, no E402):
- demos: `from modelviewprojection.mvpvisualization import cayley_gl, cayleygraph, cayleyscene`
  (or relative `from . import ...`); `from modelviewprojection import pyMatrixStack as ms`;
  `from modelviewprojection.mathutils import ...`; plain `import glfw`, `import OpenGL.GL as GL`.
- `_pipeline.py` / `cayley_gl.py`: drop the `sys.path.insert`; `from modelviewprojection
  import mathutils, pyMatrixStack` directly. `_SHARED_DIR = dirname(__file__)` unchanged.

Run with `python -m modelviewprojection.mvpvisualization.model` (and friends).
With an editable install, running by file path still works too, since
`modelviewprojection` resolves via the install rather than a path hack.

## Plan (finalized) — DONE

- [x] `git mv` the tree to `src/modelviewprojection/mvpvisualization/`, flattening each
      `<name>/<name>.py` to `<name>.py`; add `__init__.py`. Drop `__pycache__`, `imgui.ini`,
      and the stray `#…#` autosave (don't move those).
- [x] Rewrite imports to **absolute** package form in all 7 demos + `cayley_gl.py` +
      `cayleygraph.py` + `cayleyscene.py` + `_pipeline.py`: remove every `sys.path.insert` /
      `PWD` prelude, `from modelviewprojection.mvpvisualization import cayley_gl/cayleygraph/
      cayleyscene` (and `from modelviewprojection import mathutils, pyMatrixStack`), plain
      `import glfw` / `import OpenGL.GL as GL`; delete the `# noqa: E402` markers and the
      sys.path/order prelude comments. (`_SHARED_DIR = dirname(__file__)` stays.)
- [x] Update book prose run-commands to the new file path
      `python src/modelviewprojection/mvpvisualization/<name>.py`: `ch10.rst:253`,
      `ch17.rst:87,114`, `ch19.rst:66`. Repoint the stale `ch17.rst:189,205`
      (`demoAnimation.py` → `modelviewperspectiveprojection.py`;
      `demoViewWorldTopLevel.py` → `coordinatesystems.py`). Update `mvp_dict.pws` if the
      `mvpVisualization` spelling drops out of prose. Rebuild the book so `_build/` regenerates
      (don't hand-edit `_build/`).
- [x] Update `tests/conftest.py` (drop its `mvpVisualization` sys.path entry) and
      `tests/test_cayley_graph.py` / `tests/test_cayley_scene.py` to import from
      `modelviewprojection.mvpvisualization`. Confirm the 85 tests still pass.
- [x] py_compile + ruff across the moved tree; re-run tests; Bill runs a demo or two by path
      to visually confirm (GL needs a display).

(Dropped from the earlier draft per Bill's decisions: no `package-data`/wheel work
[#3], no `main()` wrapper / console-scripts / `python -m` [#2].)

## Notes / decisions

- **Flatten** the per-demo subdirs (they only hold one `.py` each; shaders are already
  shared) — simpler than mirroring the old dir-per-demo layout.
- Engine modules (`cayley_gl`, `cayleygraph`, `cayleyscene`, `_pipeline`) move WITH the demos
  into the same subpackage so the shared-shader `__file__` loading and the import order both
  keep working untouched.

## Open questions

All resolved — see **Decisions (Bill, 2026-06-03)** at the top.
