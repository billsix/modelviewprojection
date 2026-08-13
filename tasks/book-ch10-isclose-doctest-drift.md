# ch10 book doctests use the pre-0.0.15 `is_close` (renamed + tolerances changed)

**Status:** proposed (2026-08-13) — needs go-ahead
**Priority:** 6
**Difficulty:** 2
**Created:** 2026-08-13

## Context

Found while doing the gacalc 0.0.16 unsuffixed-type book pass (`tasks/archive/2026/08/13/
adopt-unsuffixed-gacalc-graded-types.md`). ch10's four illustrative `.. code:: Python` doctests
call gacalc's **`is_close`**, which gacalc **0.0.15 renamed to `isclose`** *and* whose tolerances
**no longer default to `1e-5`** — both `rel_tol` and `abs_tol` now default to `0.0`, so a bare
`isclose(a, b)` is now **exact** equality. So these examples are doubly stale: wrong method name,
and (once renamed) they'd compare exactly and could read `False` where the old `1e-5` slop passed.

This is **separate drift from the 0.0.16 type rename** — it dates to the 0.0.15 bump, whose book
prose was deferred to `tasks/book-rotate-prose-update.md`. Left untouched in the 0.0.16 pass rather
than silently changing an example's numerical semantics.

Not build-breaking: `.rst` doctests are **not executed** by any gate (mvp's `pytest` runs
`--doctest-modules` over `src`/`tests` Python modules only, not `.rst`). So this is book-accuracy,
not a broken build.

## The four sites (`book/docs/ch10.rst`)

- `158`: `inverse(translate(b=b))(p).is_close(translate(b=-b)(p))`
- `178`: `inverse(rotate(angle))(p).is_close(rotate(-angle)(p))`
- `194`: `inverse(scale_non_uniform(2.0, 4.0))(p).is_close(` …
- `226`: `inverse(compose([f1, f2]))(p).is_close(` …

## Fix

`is_close(` → `isclose(`, and **add explicit tolerances** so the examples still pass under the
zero-default: `.isclose(<other>, rel_tol=1e-5, abs_tol=1e-5)` (matches the pattern used at the
36 migrated test sites in `tasks/archive/2026/08/04/gacalc-0015-isclose-tolerance-migration.md`).
Re-grep at implementation time (`grep -n "is_close" book/docs/*.rst`) — the count can drift.

## Verify

These aren't gated, so verify by hand: paste each doctest into a `gacalc==0.0.16` REPL and confirm
it prints `True` with the tolerances added. (Optional, larger: wire `.rst` doctests into the gate
via `sphinx.ext.doctest` / a `doctest-glob`, so book examples stop drifting silently — but that is
its own task, not this one.)
