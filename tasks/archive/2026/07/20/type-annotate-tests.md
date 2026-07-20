# Bring the tests up to the project's Python standard (annotations)

**Status:** **DONE 2026-07-20.** All test signatures typed; `ty check tests` clean.

**Created:** 2026-07-20
**Requested by:** Bill, 2026-07-20 — "update the tests to follow our python standards; I
think types were missing."

## The gap (measured 2026-07-20)

The `## Coding standard (Python)` section (CLAUDE.md) says **signatures — params + returns —
are the contract, so always annotate**. The tests do not:

- **7 test files**, **75 functions**; **63 missing a return annotation** (`-> None` on
  `test_*`), **13 params with no type**.
- Example (`tests/test_mathutils.py`): `def v2(x, y):`, `def v3(x, y, z):`,
  `def test_rotate_quarter_turn():` — the helpers lack param + return types, the tests lack
  `-> None`.

(For contrast, the sibling **geometricalgebra** repo keeps `ty check tests` fully clean —
its tests are annotated; mvp's are the ones behind.)

## What to do

Apply the standard to `tests/*.py`:

- **Every test function gets `-> None`** (pytest tests return nothing).
- **Helper functions get real signatures** — e.g.
  `def v2(x: float, y: float) -> Vector2:`, `def v3(x: float, y: float, z: float) -> Vector3:`
  (import `Vector2`/`Vector3` from gacalc directly, per the just-removed facade).
- **Locals: annotate as much as reasonable** (a declared type over none), skipping only pure
  noise (`n = 3`); don't fight the checker where it forces awkward edits (leave inferred and
  say why).
- **Externally-fixed names stay** — pytest fixtures/hooks (`setup_method`, a `conftest`
  fixture's name) keep their exact names; that's the framework boundary, not a naming choice.

## Verification

1. `ty check tests` clean (the goal — matches gacalc's tests).
2. `make format` (ruff) clean.
3. Full suite still green (annotations are inert at runtime, but confirm no import/typo slipped
   in — e.g. a wrong return type on a helper).
4. Re-measure: 0 functions missing a return annotation, 0 untyped params in `tests/`.

## Notes

- This is mostly mechanical (add `-> None`, type the handful of helpers), but the helper
  return types need a human eye (what does `v2` actually return — a `Vector2`? a `G2`?), so
  it is not a blind codemod.
- `pytest.ini` already runs doctests; those live in `src/`, not here, so this task is scoped
  to `tests/*.py` only.


## Outcome (2026-07-20)

- **`-> None` on every test function** (63 added), and on the void helper `assert_same_fn`.
- **Value-returning helpers typed:** `v2 -> Vector2` / `v3 -> Vector3` (params `float`),
  `i(t: float, start: float) -> float`, `factorial(n: int, f: typing.Callable) -> int`,
  `record_positional_args(*args: float) -> tuple[float, ...]`.
- **`assert_same_fn`** params typed `Callable[..., MultiVectorBase]` -- NOT
  `Callable[[MultiVectorBase], MultiVectorBase]`: Callable args are contravariant, so the
  concrete `.func` values passed (`Callable[[Vector3], Vector3]` etc.) are not assignable to
  the latter; `...` accepts them. (ty caught this -- 8 errors -- and it is fixed.)
- Imports added where referenced: `Callable` (collections.abc), `MultiVectorBase`
  (gacalc.base) in the two cayley test files.

**Result: 0 missing return annotations, 0 untyped params in `tests/`; `ty check tests`
clean; ruff clean; suite 96 green.**

**Locals deliberately left inferred.** The signatures were the gap Bill saw. Test locals
(`fn = rotate(...)`, `pairs = [...]`, `center = v2(2, 0)`) are single-use and
self-documenting; per the standard's "inline a value used exactly once / don't keep a local
just to type it," annotating hundreds of trivial test locals would be churn, not clarity.
ty is clean without them.


## Follow-up: local variables typed too (Bill, 2026-07-20)

After the signature pass, Bill asked for **local variables** in the tests to be typed as
well. Done: all ~177 local assignments + loop targets across the 7 files are annotated
(loop targets declared on the line above, per the standard).

**Method — a static "MonkeyType" via ty's `reveal_type`:** insert `reveal_type(x)` after
each assignment, run `ty` to get the inferred type, then clean/qualify and write it back.
Cleanups needed: `int | float` -> `float`, `Literal[True]` -> `bool`,
`ndarray[_AnyShape, dtype[Any]]` -> `np.ndarray`; bare library names qualified
(`ast.ClassDef`, `cayleygraph.OrientedStep`, ...); `[Unknown]` generics dropped to bare;
`enum.auto()` members skipped. The 6 locals ty infers as `Unknown` (from untyped upstream
like `animation.transform`) were hand-typed from the code (`Vector3` / `np.ndarray`).

**Result: 0 untyped local assignments (enum members excepted); `ty check tests` clean;
ruff clean; suite 96 green.** The reveal+annotate scripts are reusable (offered to save to
`tools/`).