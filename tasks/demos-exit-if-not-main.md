# Demos and visualizations: exit early when not run as `__main__`

**Status:** proposed — needs go-ahead (filed 2026-09-05 at the maintainer's request; not started)
**Priority:** 5
**Difficulty:** 3

## BLUF

Give every teaching demo (`src/modelviewprojection/demos/demoNN.py` and the `demoNN/demoNN.py`
subfolders) and every visualization (`src/modelviewprojection/mvpvisualization/*.py`) — 39 files
— the same import guard the tightened Code-the-Classics games now carry: before the first line
that acquires a resource (the GLFW window, the GL context, audio, a file), stop if the file is
being imported rather than run:

```python
if __name__ != "__main__":
    sys.exit("this is a demo, run it directly rather than importing it")
```

Rationale (maintainer, 2026-09-05): these files are programs, never modules, but a tool may load
a module for other reasons (pytest's doctest collection, an editor, an introspection script);
graphics, sound and OS resources should only be acquired when the file is actually the main
program. Done = every demo/visualization exits on import before opening a window, still runs
identically when executed, and the book build is unaffected.

## Context (read first)

- **Today none of them has any guard** (checked 2026-09-05: `grep -n __name__` over the 39 files
  is empty). Each demo does `if not glfw.init(): sys.exit()` and creates its window at module
  level, then runs its loop at module level — the library-not-framework shape
  (`tasks/reference/library-not-framework-authorship-style.md`), which this task keeps.
- **The guard's position is the whole point:** put it immediately before `glfw.init()` (or the
  first resource acquisition), after the imports and pure definitions, so the file's definitions
  stay importable but nothing below runs. The games' version, with its comment, is the template:
  `ports/codetheclassics/vol1/boing/boing.py` (section `# ===== window and GL context =====`).
- **The pytest doctest allow-list exists because of exactly this** (`pytest.ini`'s comment:
  "execute at import: demos/demo01.py calls sys.exit() … other demos/ and notebooksrc/ files
  enter their render loop, and mvpvisualization/ + wxapp*.py open windows"). With the guard,
  importing a demo raises `SystemExit` *deliberately* — which pytest's collector still treats as
  an INTERNALERROR, so **the allow-list must stay**; do not widen `--doctest-modules` to the
  demos as part of this. (`sys.exit` is the maintainer's chosen behaviour; a `return`-like
  no-op is not possible at module level.)
- **The book includes demo code by `doc-region` markers.** The guard must go OUTSIDE any published
  region (`CLAUDE.md` › "The book includes code by MARKER") — check each file's markers around
  `glfw.init()` before inserting; a guard inside a `doc-region` would be printed in a chapter.
- **`wxapp.py` / `wxapp2.py`** are framework-style (wx owns the loop) and out of scope here.

## Plan

1. For each of the 39 files, find the first resource-acquiring statement (normally
   `if not glfw.init():`) and insert the guard + a one-line comment above it, outside any
   `doc-region`. Add `import sys` where missing. A small codemod under `tasks/adhoc/` is
   appropriate (39 files, one shape) — save it, make it idempotent, run it twice.
2. Verify: `python -c "import runpy; runpy.run_path('src/modelviewprojection/demos/demo02.py')"`
   (a non-`__main__` run) exits with the message and opens no window; running a few demos under
   Xvfb (`tasks/reference/tests-and-gates.md`, headless GUI recipe) still renders; `make format`;
   `tools/check_doc_regions.py` unchanged; the book still builds (`make html`) since no region
   text changed.

## Open questions

1. `sys.exit(message)` (exit status 1, message on stderr) as in the games, or a silent `sys.exit()`
   as the demos already use for `glfw.init()` failures? *(Recommend the message — it explains
   itself to whoever imported the file.)*
