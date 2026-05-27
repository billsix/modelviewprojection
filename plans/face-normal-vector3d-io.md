# Task: investigate `_face_normal` taking / returning `Vector3D`

**Status:** not started (investigation). **Type:** refactor of
`src/modelviewprojection/shading.py` + its callers. Follow-up to
[`shading-use-vector3d.md`](shading-use-vector3d.md) (Finding 1, done — made
`_face_normal` compute via `mathutils.find_normal` but **kept tuple in/out**).

## Question
Right now `_face_normal(a, b, c) -> tuple[float, float, float]` takes 3 tuples and
returns a tuple — so internally it wraps (`Vector3D(*a)`) and unwraps (`tuple(...)`)
around `find_normal`. Should it instead **take `Vector3D` args and return a
`Vector3D`**, dropping the wrap/unwrap and speaking the course's abstraction
end-to-end?

## Things to weigh (investigate before deciding)
1. **Is `_face_normal` even needed then?** With `Vector3D` in/out it becomes
   essentially `(1.0/abs(n)) * find_normal(p1, p2, p3)` — i.e. "`find_normal`
   normalized." Consider either (a) keep a thin `_face_normal` wrapper, or
   (b) drop it and add a `unit_normal()` (or a `normalize()`) helper to
   `mathutils` so demos call the abstraction directly. (b) is more in the spirit
   of the course.
2. **Caller impact — the crux.** Inspect how `demo22a`/`demo23` build their mesh
   vertices and consume the normal:
   - If the triangle corners are already `Vector3D`, passing them in is a clean win.
   - If they're tuples / numpy rows, and the normal ultimately feeds a
     `np.float32` vertex buffer or `glNormal3f`/uniform, then `Vector3D` in/out may
     just **relocate** the tuple↔Vector conversions to the call sites rather than
     remove them. Quantify which.
3. `Vector3D` has no `__getitem__`; callers that index the normal (`n[0]`) would
   need `.x/.y/.z` or unpacking (same gotcha as `light_dir_ws`).

## What to do
- Read the mesh-construction + normal-usage in `demo22a`/`demo23` (and any future
  litjet/shadow ports).
- Decide: Vector3D-in/out wrapper, vs. drop `_face_normal` for a `mathutils`
  `unit_normal`, vs. leave as-is (tuple) if it only moves conversions around.
- Propose to Bill before editing.

## Verification (when done)
Numeric equivalence to current `_face_normal` (assert within 1e-9 on the real jet
faces + random tris); `ruff`/`py_compile`/`pytest`; Bill runs the GL demos.
