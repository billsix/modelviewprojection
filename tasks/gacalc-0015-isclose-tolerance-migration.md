# Migrate mvp tests off gacalc's removed `is_close` (0.0.15 renamed it to `isclose`)

**Status:** proposed — needs go-ahead (found 2026-08-04 during the basis-constant sweep)
**Priority:** high — `pytest` is red on master
**Difficulty:** 2

## Problem

gacalc 0.0.15 (the currently pinned version — `requirements.txt` line 3,
Dockerfile `ARG GACALC_VERSION=0.0.15`) made two changes to the closeness predicate on
its value types:

1. **Renamed** `is_close` → `isclose`.
2. **Changed the default tolerance to zero**: `isclose(self, other, rel_tol=0.0, abs_tol=0.0)`.
   With the defaults it is essentially `==`.

mvp calls the old `.is_close(other)` (single arg, relying on a nonzero default tolerance)
at **36 sites in 3 test files**:

- `tests/test_mathutils.py`
- `tests/test_cayley_graph.py`
- `tests/test_cayley_scene.py`

Result: `pytest` fails at collection/run — first as `AttributeError: 'Vector3' object has
no attribute 'is_close'`, and (if the name is naively renamed) as 9 zero-tolerance
floating-point comparison failures in the rotate/perspective/round-trip tests.

This is **independent of the `Vector2.e_1` → `e_1` sweep** done 2026-08-04
(`tasks/unqualify-graded-basis-imports.md`): that sweep touched no test file and no
`src/` code that calls `is_close`. It was merely *discovered* while running the suite to
verify the sweep.

## Why a bare rename is wrong

Verified 2026-08-04: `fn(inp).isclose(out)` returns `False` on a rotate result that is
correct to ~1e-16, because the default tolerance is 0. `fn(inp).isclose(out, abs_tol=1e-9)`
(and `rel_tol=1e-9`) returns `True`. So each call site needs an explicit tolerance.

## What to decide (Bill's call)

1. **Which tolerance** — a single `abs_tol=1e-9` (or `rel_tol`) applied uniformly, or
   per-test values? The rotate/perspective tests exercise `sin`/`cos` and matrix inverses,
   so `1e-9` absolute is comfortably above the observed error.
2. **Where the default should live** — gacalc's `isclose` default of `0.0` is surprising
   for a method named "isclose". Worth raising upstream
   (`github.com/billsix/geometricalgebra`): should the default be a small nonzero
   tolerance so callers don't each have to pass one? If gacalc changes the default, mvp's
   migration shrinks to a pure rename.

## Scope

36 mechanical edits across 3 test files once the tolerance policy is decided. No `src/`
changes needed (the library and demos do not call `is_close`).
