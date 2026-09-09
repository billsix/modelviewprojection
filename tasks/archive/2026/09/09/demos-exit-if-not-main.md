# Demos and visualizations: exit early when not run as `__main__`

**Status:** **DONE 2026-09-09** (Bill: "start it"). 37 files guarded by a saved, idempotent
codemod; all gates green and seven of them re-run headlessly to prove the guard did not break
them. **Archived 2026-09-09.** The durable half was harvested first: the guard's shape and why it
does *not* reshape the demos into `if __name__ == "__main__":` blocks →
`tasks/reference/library-not-framework-authorship-style.md`; the games-to-demos rollout →
`tasks/reference/code-the-classics-tightening.md` §3. The one-shot codemod
(`tasks/adhoc/demos-exit-if-not-main/add_main_guard.py`) was removed with this archive; it survives
in the work commit `0db11d26`.
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
- **Not a re-opening of the CLOSED main-guard plan.** `tasks/archive/2026/07/19/demo-main-guards-and-dedent.md`
  ("CLOSED — NOT NEEDED. Do not implement this plan") proposed something different: wrapping each
  demo's whole body under `if __name__ == "__main__":`, which reshapes 25 files and forces
  `:dedent:` on 129 book `literalinclude`s. **This task inserts one guard-and-exit line** before the
  first resource acquisition, outside any `doc-region`; no file changes shape and no book directive
  changes. The closed plan's premise was also different — it existed to collapse `pytest.ini`'s
  allow-list, which this task explicitly keeps (see the bullet above).

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

## What was done, and two corrections to the plan above

**The file count was 39; the correct set is 37.** The plan's glob,
`src/modelviewprojection/mvpvisualization/*.py`, sweeps in **`_pipeline.py` and `cayley_gl.py`** —
which are not visualizations at all but the **engine**, imported by all seven Cayley demos *and* by
demos 21, 22 and 24. Guarding those two would have made every one of those files exit on import.
They are excluded, and the codemod names them in an `ENGINE` set with the reason, so a future run
cannot pick them up by accident.

**demo01 needed a different insertion point, exactly as the plan warned.** Its
`if not glfw.init():` sits inside the `initialize glfw` doc-region, which ch01 publishes — so a
guard placed immediately above it would have printed in the chapter. The codemod walks back over an
unclosed region and inserts above the opening marker instead. demo01 is the only such file;
verified by scanning all 30 demos. No other file's acquisition line is inside a region, and the
seven visualizations carry no markers at all.

**Open question 1 answered:** `sys.exit(message)`, matching the games — the message explains itself
to whoever imported the file. Demos say "this is a demo, run it directly rather than importing it";
the visualizations say "visualization".

**Insertion points:** demos guard above `if not glfw.init():`; the visualizations have no
`glfw.init` of their own and acquire first at `cayley_gl.setup(...)`, which creates their window,
so the guard goes above that. The seven visualizations also needed `import sys` added.

## Verification (all run 2026-09-09)

- **`ruff check src` + `ruff format --check src`** clean; **`ty check src`** clean.
- **`tools/check_doc_regions.py` green** in-container — the demo01 placement holds.
- **`pytest` 104 passed.** `pytest.ini`'s allow-list is untouched, as the plan requires.
- **The guard fires on import** and opens no window — checked on demo01, demo02, demo22 and two
  visualizations via `runpy.run_path` without `run_name="__main__"`.
- **They still RUN**, which no checker can prove: demo02, demo11, demo18, demo22,
  coordinatesystems, model and modelviewperspectiveprojection all render headlessly via
  `tools/verify_render.sh`. (That tool takes `run_name="__main__"`, so the guard correctly lets it
  through.)
- **Not checked: `make html`.** The image here was built `BUILD_DOCS=0`, so a full book build was
  not possible. The doc-region checker covers the anchor half, and no published region's *text*
  changed — but the build itself is Bill's.

## Two bugs this pass produced, both caught by running the artifact

Worth recording, because both were invisible to ruff and ty:

1. **The first codemod inserted `import sys` inside a multi-line `from x import (…)` block**, and
   `mvpvisualization/model.py` stopped parsing. Cause: finding the last import by matching lines
   that *start with* `from ` — a continuation line looks like nothing in particular. Fixed by
   taking `max(end_lineno)` over the top-level `ast.Import`/`ast.ImportFrom` nodes, which is
   exactly rule 1 of the bulk-edit playbook in `tasks/reference/tests-and-gates.md` §6. All 37
   files were reverted and the corrected script re-run **once**, so the saved codemod reproduces
   its own diff from the original input.
2. **`tools/render_probe.py` assumed every demo's camera has `position_ws`.** demo22 and the Cayley
   visualizations use orbit cameras that do not, so the probe raised `AttributeError` *after*
   rendering fine. Hardened: the camera line is diagnostic output and must never fail a render
   check. (Its earlier sibling — assuming a 3-D `position.z` — was fixed the same day.)

## Open questions

1. ~~`sys.exit(message)` or a silent `sys.exit()`?~~ **Answered: the message**, matching the
   games.
