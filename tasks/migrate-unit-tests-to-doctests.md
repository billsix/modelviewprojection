# Migrate unit tests into doctests where they read well

**Status:** proposed — needs go-ahead (criteria/inventory can start now; the migration is the bulk).
**Priority:** 5
**Difficulty:** 4
**Created:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)

## BLUF

Push as many of the `tests/` unit tests as reasonable **into doctests** in the library source
(`src/modelviewprojection/`), so a docstring example — which also shows up in the book — doubles as
the test. "Done" = the cases that read naturally as `>>> expr` → result live in the relevant
docstrings; the ones that must stay pytest are listed with a one-line reason each; `make test` is
green and still covers every migrated case.

**The collection mechanism already exists — this is migration plus one cleanup.** `pytest.ini`
already sets `addopts = -m "not slow" --doctest-modules`, so doctests in the collected library
modules already run under `make test`. The predecessor task that wired it is archived at
`tasks/archive/2026/07/19/doctests-everywhere.md` (and `demo-main-guards-and-dedent.md` the same day).

## Context (cold start)

- Repo: github.com/billsix/modelviewprojection (mvp). Python port + Sphinx book; a docstring
  example that no longer runs is a broken example *in the book* — doctests matter here.
- Test gate: `make test` → container → `pytest` (`Makefile:222`). Config in `pytest.ini`.
- **The `--doctest-modules` workaround to resolve first.** `pytest.ini` cannot use a blanket
  `testpaths = src tests` because `--doctest-modules` *imports* what it collects, and the
  `demos/`, `notebooksrc/`, `mvpvisualization/`, `wxapp*.py` scripts execute (or open windows /
  call `sys.exit()`) at import. So `testpaths` is an explicit allowlist of importable library
  modules (`cayley`, `framebuffer`, `util`, `mathutils.py`, `matrix_stack.py`). The pytest.ini
  comment says once every script has an `if __name__ == "__main__":` guard this collapses to
  `testpaths = src tests` and doctests anywhere get picked up automatically — and the main-guard
  task was archived 2026-07-19, so **step 1 is to verify whether the allowlist can now collapse.**

## Criteria — doctest vs stays pytest

Default to **doctest** for a short, deterministic `input → expected output` that documents the
function. **Keep pytest** when the test needs a debugger to understand the code, uses
fixtures/parametrization/`pytest.raises`, is a `slow`/symbolic case (mvp already marks these with
the `slow` marker), opens a window, or guards an internal invariant not meant for the book.

## Plan

1. Verify whether `testpaths` can collapse to `src tests` now that the demo main-guards landed;
   if so, do it (every module's doctests then run automatically).
2. Inventory `tests/` (≈10 files): classify migrate / keep (reason each keep).
3. Migrate the "migrate" set into the function/module docstrings; remove the redundant pytest case.
4. `make test` green (both the `not slow` default and `pytest -m ""`); doctest count up, pytest down.

## Notes

- Fix the stale pointer while here: `pytest.ini` references `tasks/doctests-everywhere.md`, which is
  now under `tasks/archive/2026/07/19/`.
- Part of a cross-repo "doctests by default" initiative. The shared convention + lessons now live in
  **`~/.claude/reference/doctests-by-default.md`** (canonical: github.com/billsix/runClaudeInContainer;
  read its `## Python` section first — it covers the `--doctest-modules` wiring, the
  import-time-execution trap, the consolidation hazards, and the keep-as-pytest exceptions).
- **Required on completion:** append anything new this migration taught to
  `doctests-by-default.md` (its `## Python` section, or the language-agnostic core if general) and
  re-sync the byte-identical runCrush mirror (`runCrushInContainer tasks/reference/doctests-by-default.md`).
