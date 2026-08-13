# De-facade mathutils: stop re-exporting gacalc types

**Status:** DONE (2026-08-13) — executed within the 0.0.16 adoption pass. The 12 SuperBible
ports now import `Vector` straight from `gacalc.g3`; `mathutils` re-exports **no** gacalc type
(verified: `grep "mathutils import" ports src tests` returns no gacalc type/transform). The stale
`assignments/demo02/vec1.py` was left for `tasks/assignments-review.md` as noted. Committed in
Bill's `18a0f7b2`. Ready to archive alongside the adoption task.
**Priority:** 5
**Difficulty:** 2
**Created:** 2026-08-13

## Context

`src/modelviewprojection/mathutils.py`'s own docstring and `__all__` already declare it is
**not** a re-export facade — it exports only the graphics-specific math *defined* there
(`rotate`/`rotate_x/y/z`/`rotate_around`, `cosine`/`sine`/`abs_sin`, `find_normal`/
`plane_equation`/`distance_to_plane`, `ortho`/`perspective`/`cs_to_ndc_space_fn`,
`FunctionStack`/`fn_stack`/`push_transformation`) and imports gacalc's `Vector2`/`Vector3`/
`Bivector3` + the transform layer **internally** for its own signatures. Callers are told to
import gacalc types from gacalc directly.

**The docstring is 96% true — but one gacalc type still leaks.** Survey 2026-08-13:

- The transform layer (`translate`/`compose`/`InvertibleFunction`/`Linearity`/…) and `Vector2`
  are **not** pulled through mathutils by anyone. Good.
- **`Vector3` still leaks to 12 OpenGL-SuperBible ports**, each doing
  `from modelviewprojection.mathutils import Vector3, plane_equation` (or `Vector3, find_normal`)
  — co-importing the type with the helper only because both happen to sit in mathutils. It works
  solely because `Vector3` is a module-level name there, not because it's advertised in `__all__`.
- **1 stale assignment** (`assignments/demo02/vec1.py`) imports `Vector1, InvertibleFunction,
  compose, inverse, translate, uniform_scale` from mathutils — mathutils re-exports **none** of
  those now (no `Vector1` at all), so that file is already broken. It belongs to the separate
  `tasks/assignments-review.md` (Bill's call); **leave it out of this task.**

Finishing the de-facade makes mathutils carry zero gacalc types, matching its own docstring.

## The 12 straggler ports (all `ports/openglsuperbiblev4/`)

`chapt01/block/Block.py`, `chapt05/{litjet,shinyjet,sphereworld}/…`, `chapt05/shadow/shadow.py`,
`chapt06/{fogged,multisample,sphereworld}/…`, `chapt08/{pyramid,sphereworld}/…`,
`chapt09/sphereworld/…`, `chapt11/sphereworld/…`, `chapt19/SphereWorld32/SphereWorld32.py`.

(Re-grep at implementation time: `grep -rln "from modelviewprojection.mathutils import.*Vector3"
ports` — the count can drift.)

## The change (one edit per file)

    # before
    from modelviewprojection.mathutils import Vector3, plane_equation
    # after (post-0.0.16, direct-import / module-qualify approach)
    from gacalc.g3 import Vector          # Vector3 -> Vector, gacalc 0.0.16
    from modelviewprojection.mathutils import plane_equation

`shadow.py` uses the multi-line `import (Vector3, find_normal, plane_equation)` form — same split.

## Relationship to the 0.0.16 adoption

This is **not** a separate execution: under the chosen **direct-import / module-qualify**
approach (`tasks/adopt-unsuffixed-gacalc-graded-types.md`), mathutils itself switches to
`from gacalc.g3 import Vector` internally, at which point `from mathutils import Vector3` in these
12 ports **breaks and must be fixed in the same commit**. So these 12 edits happen *inside* the
adoption pass. This task exists to record the de-facade as a deliberate goal (mathutils ends up
re-exporting no gacalc type) and to enumerate the exact straggler set, so the adoption doesn't
miss them.

**Do NOT do this as a no-version-bump pre-step against 0.0.15** — it would touch the 12 files
twice (once to re-source `Vector3`, once to rename `Vector3`→`Vector`). One pass, one edit each.

## Verify

- After the adoption pass: `grep -rn "mathutils import" ports src tests | grep -iE
  "Vector|Bivector|Rotor|Scalar|InvertibleFunction|translate|compose|uniform_scale|Linearity"`
  returns **nothing** (no gacalc type or transform pulled through mathutils anywhere).
- `make test` green; the 12 ports still import their gacalc `Vector` + the mathutils helper.
