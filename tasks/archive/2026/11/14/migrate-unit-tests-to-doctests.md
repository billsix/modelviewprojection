# Migrate unit tests into doctests where they read well

**Created:** 2026-10-27 (William Emerison Six <billsix@gmail.com>). **Done:** 2026-11-14.

## Outcome

The migration was mostly consolidation: the library docstrings already carried doctests for most
of what `tests/test_mathutils.py` asserted. Thirteen of its 22 tests were deleted after four
doctests were extended to cover what they checked, and `pytest.ini` now collects every importable
module under `src/` instead of an allowlist. `make test` went from 70 to 57 items (doctest items
are counted per docstring, so the number of checked examples went up, not down).

## What changed

- **`pytest.ini`: exclusion list instead of allowlist.** `testpaths = tests src` plus
  `--ignore`/`--ignore-glob` in `addopts` for `demos/`, `notebooksrc/`, `mvpvisualization/` and
  `wxapp*.py`. The planned full collapse to plain `testpaths = src tests` was tried and does not
  work: the 47 demos end their imports with `if __name__ != "__main__": sys.exit(...)` on purpose
  (so a chapter's listing reads as a flat program), and a `sys.exit` at import kills pytest with
  `INTERNALERROR ... SystemExit`. With the exclusion list, `pgzero_gl/` and `graphingcalculator/`
  are now collected too (they import cleanly headless and hold no doctests yet), so a doctest added
  to any library module runs with no config edit. The stale pointer to
  `tasks/doctests-everywhere.md` went away with the old comment.
- **Doctests extended** (each now asserts what the deleted test asserted):
  `find_normal` (a 2x2 triangle's normal has length 4), `plane_equation` (a point on the plane
  satisfies `normal . P + d == 0`), `ortho` (the prism centre maps to the NDC origin; the transform
  is `Linearity.AFFINE`), `perspective` (`Linearity.NONLINEAR`), and
  `framebuffer.softwarerendering.is_parallel_and_same_orientation` (a nearly parallel pair is
  `False`).
- **Deleted from `tests/test_mathutils.py`**, as covered by the doctests: `rotate_around_a_point`,
  `cosine_and_sine`, `abs_sin`, `is_parallel_and_same_orientation`,
  `is_counter_clockwise_and_clockwise`, the three `find_normal` tests, `plane_equation_points_satisfy_it`,
  `distance_to_plane_signed`, the two `ortho` tests, `perspective_is_nonlinear_and_invertible`.
- **Doctest bindings annotated** (house rule: a doctest models the house style) in `mathutils.py`,
  `framebuffer/softwarerendering.py`, `util/colorutils.py` and `util/shading.py`.
- **Inbound pointers fixed:** `tasks/framebuffer-software-rasterizer-clockwise.md` and
  `tasks/mathutils-helpers-via-gacalc.md` cited deleted tests.

## What stays a plain test, and why

- `tests/test_mathutils.py` rotate tests (`rotate`, `rotate_x/_y/_z`): those are module-level
  `plane_rotation(...)` closures documented by book-region `#` comments; a closure's `__module__`
  is gacalc, so `DocTestFinder` never visits it, and the checks are tolerance-based. Their module
  docstring says so.
- `test_function_stack_push_pop`: the source of a `literalinclude` in `book/docs/ch16.rst`.
- The two `to_matrix` tests: `numpy.allclose` and `pytest.raises`.
- `tests/test_firstclassfunctions.py`: both tests are `literalinclude` sources (book doc-regions).
- `tests/test_gl_vector_unpacking.py`: a regression guard on gacalc's iteration contract that
  `CLAUDE.md` cites; an internal invariant, not book material.
- `tests/test_check_doc_regions.py` (parametrized, tests a `tools/` script),
  `test_ctc_actor_field_collisions.py` (an invariant over the CtC ports),
  `test_demo22b_gltf_roundtrip.py` (`tmp_path` fixture, parametrized).

## Judgment calls

- The shared rule keeps tolerance-based tests plain. Here the doctests already print rounded
  values (`round(float(c), 6)`), which is an exact check of the same assertion, so the duplicated
  `isclose` tests were deleted; tolerance-based tests with no doctest home stayed.

## Verification

`pytest` in the project image: 57 passed under the default `-m "not slow"` and under `-m ""`;
`make test`, `make format` and `make type-check` green (see the work commit).

## Cross-repo

The lessons (the inverse `__main__` guard and the exclusion-list `testpaths`, factory-built
attributes having no doctest home, a rounded doctest retiring a tolerance test) were appended to
`tasks/reference/doctests-by-default.md` in github.com/billsix/runClaudeInContainer and copied to
the byte-identical runCrushInContainer mirror; staged there, not committed.
