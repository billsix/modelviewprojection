# Restructure src/ (and update the book) into a sensible directory layout

**Status:** complete
**Completed:** 2026-06-03
**Started:** 2026-06-03

## Decisions (Bill, 2026-06-03) + what was executed

1. `mathutils.py` + `pyMatrixStack.py` **kept at the package top** (not moved).
2. Directory name **`demos/`**.
3. `wxapp.py` / `wxapp2.py` / `wxapp2.xrc` **kept as-is at top**; `softwarerendering.py`
   moved to its own folder **`framebuffer/`** (it provides the virtual/software framebuffer).
4. **Hard break** old paths — no compat shims.
5. **Full move** done now.

**Executed:**
- `git mv` → `demos/` (demo01..demo19e + demo20..demo24 asset dirs), `util/` (windowing,
  clipping, colorutils, cameracontrols, shading, nbplotutils, axes), `framebuffer/`
  (softwarerendering); `__init__.py` added to each. Top now: `mathutils.py`,
  `pyMatrixStack.py`, `wxapp*`, `demos/`, `util/`, `framebuffer/`, `mvpvisualization/`,
  `notebooksrc/`, `plotsforbook/`.
- Rewrote imports for the moved modules (32 files in `src/` + `tests/`):
  `modelviewprojection.<u>` → `modelviewprojection.util.<u>`,
  `modelviewprojection.softwarerendering` → `modelviewprojection.framebuffer.softwarerendering`.
  mathutils/pyMatrixStack imports unchanged.
- Rewrote 272 book demo paths `src/modelviewprojection/demo…` →
  `…/demos/demo…` across 21 `.rst` source files (mathutils.py refs untouched; mvpvisualization
  refs already correct).
- Updated `tasks/codebase-overview.md` tree + `CLAUDE.md`.

**Verified:** **all 181 book `literalinclude` targets resolve** to existing files (the key
Sphinx-build guard); py_compile clean; **85 tests pass**; pure moved modules import via the new
paths. ruff shows **19 pre-existing** issues only (B008/S311/T201 in demo/notebook/plot teaching
code — NOT import-related, none introduced by this move).

**Book rebuilt fine** (Bill, 2026-06-03) — all moved paths resolve in the actual Sphinx build.
Remaining: changes are uncommitted (Bill commits). The 19 pre-existing ruff nits are separate
tech debt, out of scope here.

## Goal

Study `src/modelviewprojection/` and `book/`, propose a directory structure that
groups the package's files by role (demos together, utilities together, the core
abstraction together) instead of ~40 files flat in one directory, and plan the
migration — including rewriting the book's references to the moved paths and the
package's internal imports, then applying it.

## Study (current state, 2026-06-03)

`src/modelviewprojection/` is one flat directory of ~40 files + a few subdirs:

**By role:**
- **Core abstraction:** `mathutils.py` (THE central module — **130 import sites**),
  `pyMatrixStack.py` (7).
- **Utilities (imported by demos):** `windowing.py` (29), `clipping.py` (21),
  `colorutils.py` (18), `cameracontrols.py` (11), `softwarerendering.py` (8),
  `shading.py` (8), `nbplotutils.py` (4), `axes.py` (1).
- **Legacy / unused:** `wxapp.py`, `wxapp2.py` (0 import sites — old wx bits).
- **Demos (flat):** `demo01.py`–`demo19e.py` (24 single-file demos).
- **Demos (with assets, subdirs):** `demo20/` `demo21/` (shaders), `demo22/`
  `demo22a/` `demo23/` `demo24/` (shaders + `.tga` textures).
- **Already subpackages:** `mvpvisualization/` (12), `notebooksrc/`, `plotsforbook/` (4).

**Two cost centers a move touches:**
1. **Book references — 158 `literalinclude` directives** in `book/docs/*.rst` point at
   `../../src/modelviewprojection/...` (mostly the ~27 demo files at various line ranges,
   plus `mathutils.py`). Moving demos ⇒ rewrite those paths.
2. **Python imports — ~250 sites** of `from modelviewprojection.<module> import`. Moving a
   *utility/core* module into a subpackage rewrites every importer (mathutils alone = 130).
   **Key insight:** moving a *demo* does NOT change its imports (it still does
   `from modelviewprojection.mathutils import …`, and mathutils' location is unchanged) —
   so demo moves are cheap (book paths only); utility moves are expensive (import churn).

**Constraints:**
- It's an installed package; demos run by path. Absolute imports must still resolve →
  every new subdir needs `__init__.py`; `pyproject` `packages.find where=["src"]`
  auto-discovers them.
- demo20-24 load shaders/assets via `__file__`-relative `pwd` → assets move *with* the
  demo dir, no code change.
- `mvpvisualization/` already loads shaders demo-relative (done earlier today).

## Proposed structure

```
src/modelviewprojection/
  __init__.py
  mathutils.py            # core abstraction — KEEP AT TOP (130 importers; moving churns everything)
  pyMatrixStack.py        # core — keep at top (paired with mathutils, FF-stack reimpl)
  util/                   # the support modules
    __init__.py
    windowing.py  clipping.py  colorutils.py  cameracontrols.py
    shading.py  softwarerendering.py  nbplotutils.py  axes.py
  demos/                  # the book's runnable demos
    __init__.py
    demo01.py .. demo19e.py
    demo20/ .. demo24/    # (shaders + .tga assets move with them)
  mvpvisualization/       # interactive Cayley aids (already a subpackage) — leave as-is
  plotsforbook/  notebooksrc/   # already subpackages — leave as-is
  legacy/                 # wxapp.py, wxapp2.py  (or delete — see open questions)
    __init__.py
```

**Rationale / the one deliberate exception:** keep `mathutils.py` (and its partner
`pyMatrixStack.py`) at the package top rather than under `core/`. Moving `mathutils`
rewrites **130** import sites + a book reference for marginal tidiness; it's THE name
everything uses, so top-level is the right home. Everything else groups cleanly:
`util/` for the 8 helpers, `demos/` for the 30 demo files. (If you'd rather have a
`core/` too, that's the high-churn variant — see open questions.)

## Plan (once structure is confirmed)

- [ ] Re-scan for ALL src references beyond `literalinclude`: `:download:`, figure/image
      paths, `conf.py`, `Makefile`, README, and any cross-module imports. (literalinclude
      = 158 known; confirm nothing else points into src.)
- [ ] `git mv` the files into `util/` and `demos/` (+ `legacy/` if kept); add `__init__.py`
      to each new subpackage. Assets ride along with their demo subdirs.
- [ ] Rewrite Python imports for the MOVED modules only: `from modelviewprojection.<u>`
      → `from modelviewprojection.util.<u>` (windowing/clipping/colorutils/cameracontrols/
      shading/softwarerendering/nbplotutils/axes) across `src/`, `book/`, `tests/`. mathutils/
      pyMatrixStack imports unchanged (they stay top-level). Scripted; then ruff --fix sort.
- [ ] Rewrite the 158 book `literalinclude` paths: `../../src/modelviewprojection/demoNN`
      → `../../src/modelviewprojection/demos/demoNN` (and any util `literalinclude`). Scripted.
- [ ] Update `tasks/codebase-overview.md` tree + `CLAUDE.md` path mentions.
- [ ] py_compile the package; ruff; run the test suite; `make html` (or a dry doc build) to
      confirm every `literalinclude` still resolves (a wrong path fails the Sphinx build loudly).
- [ ] Bill spot-runs a demo or two by path + skims a rebuilt chapter.

## Notes / decisions

- Demo moves are cheap (book paths only); utility moves churn imports — but it's a one-time
  scripted rewrite and `make html` will catch any missed `literalinclude` hard.
- Keep `mvpvisualization/`, `plotsforbook/`, `notebooksrc/` where they are (already grouped).

## Open questions

- [ ] **`mathutils`/`pyMatrixStack`: keep at top (recommended, low churn) or move under a
      `core/` package (clean, but ~140 import rewrites + a book ref)?**
- [ ] **`demos/` vs `demo/`** as the directory name? (`demos/` reads better; either is fine.)
- [ ] **Legacy `wxapp.py` / `wxapp2.py` / `softwarerendering.py`:** keep under `legacy/`,
      keep in `util/`, or delete (0 importers for wxapp; softwarerendering has 8)? Which are
      actually still wanted?
- [ ] **Compat shims:** add re-exports in `__init__.py` so old `modelviewprojection.windowing`
      paths keep working, or hard-break (it's your tutorial repo; the book is the interface)?
- [ ] **Scope now:** do the full `util/` + `demos/` move, or start with just `demos/` (Bill's
      primary example — cheapest, book-paths-only) and group utilities in a later pass?
