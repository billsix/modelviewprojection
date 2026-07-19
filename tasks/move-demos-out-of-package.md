# Move the runnable scripts out of the package, into top-level `demos/` + `visualizations/`

**Status:** **PARKED 2026-07-19 — NOT approved, do not start.** No files were moved.

Bill called this off the same day it was drafted, and the reason matters more than the
proposal: **this was goal drift.** The original goal was *"doctests always run as part of
the test suite"* — which was **already achieved** (see `tasks/archive/2026/07/19/doctests-everywhere.md`). Chasing
a supposed prerequisite led to a supposed prerequisite of *that*, and ended in a proposal
to restructure 40 files and 129 book references. Bill's words: *"I realized we were deep
in inception, forgetting about our original goal, and then doing a huge rewrite without
keeping the goal in sight."*

The document is kept only because the **measurements below are real and were expensive to
take** — if this is ever revisited, start from them rather than re-measuring. But it needs
a fresh, explicit decision on its own merits (student discoverability) first. The "yes"
answers recorded at the bottom were given to a hypothetical layout while the false
doctest-prerequisite framing was still on the table; **they are not approval to proceed.**

**Created:** 2026-07-19
**Supersedes:** `tasks/archive/2026/07/19/demo-main-guards-and-dedent.md` (closed as
not-needed)

## Goal

`src/` should hold **importable library code and nothing else** — the standard meaning of
the src layout. Today it also holds 31 runnable demo scripts, 8 interactive GUI teaching
aids, and 3 jupytext notebook sources.

**This is justified on student discoverability, NOT on doctests.** A student clones the
repo for a college course and should see `demos/` at the top level, not spelunk four
levels to `src/modelviewprojection/demos/`. The run command they type dozens of times
gets shorter too:

```sh
python demos/demo05.py        # vs. python src/modelviewprojection/demos/demo05.py
```

**It is NOT a prerequisite for anything.** `tasks/archive/2026/07/19/doctests-everywhere.md` is COMPLETE
— `pytest.ini`'s allow-list covers every library area in the repo. The move happens to
make that allow-list unnecessary (`testpaths = src tests` never looks outside `src/`),
but that is a **side effect**, not the reason. Do not resurrect the main-guard plan.

## Proposed layout

```
demos/                      # 31 student-run scripts        (flatten demo21/demo21.py -> demo21.py)
visualizations/             # 8 interactive GUI teaching aids
notebooks/                  # 3 jupytext sources            (open question 2)
src/modelviewprojection/    # library ONLY
```

**Only the runnable scripts move. Helpers stay.** `mvpvisualization/` is *not*
homogeneous — measured 2026-07-19:

| stays in the package (engine) | moves out (runnable) |
|---|---|
| `_pipeline.py` — imported by 4 visualizations **and** by `demos/demo21`, `demo22`, `demo24` (they pull `GLenum`) | the 8 scripts that call `cayley_gl.run_loop(...)` |
| `cayley_gl.py` — the GL engine | |
| `cayley/` (`cayleygraph.py`, `cayleyscene.py`) | |
| the 11 shader files (`*.glsl/.vert/.frag/.geom`) | |

## Measurements (2026-07-19)

- **40 files under `src/` execute on import**: 25 flat + 6 nested demos (31 total),
  8 GUI visualizations, 3 `notebooksrc/`. `wxapp.py`/`wxapp2.py` are already main-guarded.
- **181 `literalinclude` directives** in the book; **129 point at `demos/`**.
  `mvpvisualization/` and `notebooksrc/` have **0 book references**.
- **Nothing imports `demos/`**, and demos use only absolute `modelviewprojection.*`
  imports.
- `demos/` is inconsistently laid out — some flat (`demos/demo05.py`), some nested
  (`demos/demo21/demo21.py`). Flatten while touching the paths anyway (Bill, yes).

## Why the June 2026 `sys.path` problem does NOT come back

`tasks/archive/2026/06/03/move-mvpvis-demos.md` moved this tree *into* the package
precisely to kill `sys.path.insert` + `# noqa: E402`. That fix survives this move: it
worked because the scripts use **absolute** imports against an installed package, and
absolute imports resolve from any directory. Only moving the **engine** out would
reintroduce the hack — and the engine stays. Shaders load via `__file__` next to
`_pipeline.py`, so they travel with the engine and keep working.

## Cost

~129 `literalinclude` path edits, plus run-commands in `README.md:43` and ch10/ch17/ch19.
**Mechanical — no `:dedent:` needed, because no file changes shape.** No demo file is
edited at all.

## Open questions (blocking — do not start the move until answered)

1. **`[project.scripts]` entry points.** Bill asked for these; they are **incompatible**
   with the move. An entry point needs `importable.module.path:function`: after the move
   the scripts are not importable, and **0 of 31 demos define `main()`**. Adding one means
   indenting each demo's whole body into a function — more churn than the main guards just
   rejected, and it destroys the flat top-to-bottom script chapter 1 teaches and 129
   `literalinclude`s display. Options: **drop the entry points** (recommended — `python
   demos/demo05.py` is what `README.md` already teaches); keep demos inside the package so
   entry points remain possible (forfeits the move); or Makefile targets (`make demo05`)
   for short commands with no packaging.
   *Existing precedent for the working form: `pyproject.toml:90`,
   `generate_plots_for_book = "modelviewprojection.plotsforbook.generate_plots:main"`.*
2. **`notebooksrc/`** (3 jupytext sources) → top-level `notebooks/`? Recommended yes: they
   are neither library nor helper, nothing references them, and moving them makes `src/`
   purely importable so `testpaths = src tests` needs zero exceptions. Leaving them means
   one `--ignore` line forever.
3. **Stray Emacs autosave** committed at `src/modelviewprojection/cayley/#cayleygraph.py#`
   — delete? Unrelated to the move, noticed while measuring.

## Preferences expressed (Bill, 2026-07-19) — NOT approval to proceed

Given while the layout was hypothetical; see Status. If revived, re-confirm all of it.

1. Move the runnable scripts to top-level `demos/` + `visualizations/` — **yes**.
2. Flatten `demos/demo21/demo21.py` → `demos/demo21.py` — **yes**.
3. Helpers/engine stay in the package — **yes** ("only these main python files get moved").
