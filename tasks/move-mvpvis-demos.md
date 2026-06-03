# Move the mvpVisualization demos into the package

**Status:** in-progress (planning — not yet executed)
**Started:** 2026-06-03

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

## Plan

- [ ] `git mv mvpVisualization/* src/modelviewprojection/mvpvisualization/`, flattening
      each `<name>/<name>.py` to `<name>.py`; add `__init__.py`. Drop `__pycache__`,
      `imgui.ini`, and the stray `#…#` autosave.
- [ ] Rewrite imports in all 7 demos + `cayley_gl.py` + `cayleygraph.py` + `cayleyscene.py`
      + `_pipeline.py`: remove every `sys.path.insert` / `PWD` prelude; use package imports;
      delete the now-unneeded `# noqa: E402` markers and the order-comment.
- [ ] (Optional but recommended) wrap each demo's top-level window/`run_loop` code in a
      `def main(): ...` + `if __name__ == "__main__": main()`, so importing a demo module has
      no GL side effects. Enables `[project.scripts]` console entry points if wanted.
- [ ] Add `package-data` to `pyproject.toml` so shaders ship in wheels (covers the existing
      `demo20` gap too), e.g. `[tool.setuptools.package-data]` globbing
      `*.glsl/*.vert/*.frag/*.geom`. Consider `importlib.resources` if zip-safe installs matter.
- [ ] Update book prose paths: `ch10.rst`, `ch17.rst`, `ch19.rst` → new run command
      (`python -m modelviewprojection.mvpvisualization.<name>` or the new file path). Resolve
      the two stale `demoAnimation.py` / `demoViewWorldTopLevel.py` refs in ch17. Rebuild the
      book so `_build/` regenerates; update `mvp_dict.pws` if needed.
- [ ] Update `tests/conftest.py` (drops its `mvpVisualization` sys.path entry) and
      `tests/test_cayley_graph.py` / `tests/test_cayley_scene.py` to import from
      `modelviewprojection.mvpvisualization`. Confirm the 85 tests still pass.
- [ ] py_compile + ruff across the moved tree; re-run tests; Bill visual-runs a demo or two
      (GL needs a display).

## Notes / decisions

- **Flatten** the per-demo subdirs (they only hold one `.py` each; shaders are already
  shared) — simpler than mirroring the old dir-per-demo layout.
- Engine modules (`cayley_gl`, `cayleygraph`, `cayleyscene`, `_pipeline`) move WITH the demos
  into the same subpackage so the shared-shader `__file__` loading and the import order both
  keep working untouched.

## Open questions

- [ ] **Subpackage name:** `mvpvisualization` (lowercase, PEP-8) vs keep `mvpVisualization`?
      Lowercase is conventional for an importable package; the book prose can still say "the
      MVP visualizations."
- [ ] **How should students run them** — `python -m modelviewprojection.mvpvisualization.<name>`,
      a new file path, or console-script entry points (`mvp-modelview`, …)? Drives the book
      wording and whether we add `main()` wrappers + `[project.scripts]`.
- [ ] **Wheel correctness:** do we care about non-editable installs now (→ must add the
      shader package-data, and ideally `importlib.resources` loading), or is editable-from-repo
      the only supported mode for these demos (→ `__file__` loading is fine as-is)?
- [ ] The stale `ch17` references (`demoAnimation.py`, `demoViewWorldTopLevel.py`) — repoint to
      existing demos, or delete those callouts?
