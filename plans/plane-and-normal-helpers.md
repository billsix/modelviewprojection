# Plan: `find_normal`, `plane_equation`, `distance_to_plane` in `mathutils.py`

**Status:** ✅ **completed 2026-04-28.** Functions live in `src/modelviewprojection/mathutils.py`, exported from `__all__`, with doctest + `tests/test_mathutils.py` coverage (44 → 46 tests). `chapt01/block/Block.py` now imports `plane_equation` from mathutils instead of defining a local copy.

**Convention chosen (differs from SuperBible):** mvp uses **CCW winding** consistently, matching `glFrontFace(GL_CCW)` in the curriculum. SuperBible's `m3dGetPlaneEquation` and `m3dFindNormal` actually use *different* conventions internally (CW for the former, CCW for the latter), so a one-to-one port wasn't really possible without picking. The CCW choice means `mathutils.plane_equation` returns a normal opposite in sign to `m3dGetPlaneEquation` — but the planar-shadow projection is sign-invariant on the plane equation (matrix and -matrix produce the same projective result after w-divide), so chapt01/block still renders the same shadow.

## What

Add three small geometric helpers to `src/modelviewprojection/mathutils.py`:

1. `find_normal(p1, p2, p3) -> Vector3D` — surface normal of a triangle (cross of edges).
2. `plane_equation(p1, p2, p3) -> tuple[Vector3D, float]` — `(normal, d)` such that `dot(normal, P) + d = 0` for all `P` on the plane.
3. `distance_to_plane(point, plane) -> float` — signed distance from a point to the plane, where `plane = (normal, d)`.

## Why mathutils.py and not pyMatrixStack

These are vector operations on `Vector3D`, not matrix transforms. They belong with `Vector3D.cross`, `Vector3D.dot`, and the existing free functions like `cosine`, `sine`, `is_counter_clockwise`. Putting them in pyMatrixStack would force a coupling between geometry helpers and the matrix abstraction that the rest of the course avoids.

Bill's instruction was "for 3, I trust you can figure out where to add them" — this is the placement that fits the existing module split.

## Why these three together

They compose: `plane_equation` calls `find_normal` (and computes `d`); `distance_to_plane` uses the output of `plane_equation`. Adding them in one go lets `find_normal` and `plane_equation` share a derivation in their docstrings.

## Signatures (proposed)

```python
def find_normal(p1: Vector3D, p2: Vector3D, p3: Vector3D) -> Vector3D:
    """The (unnormalized) normal of the triangle (p1, p2, p3), computed
    as cross product of two edges. CCW winding gives outward-facing
    normal in a right-handed coordinate system."""
    return (p1 - p2).cross(p2 - p3)


def plane_equation(
    p1: Vector3D, p2: Vector3D, p3: Vector3D
) -> tuple[Vector3D, float]:
    """The plane through three points, expressed as (normal, d) where
    dot(normal, P) + d == 0 for all points P on the plane. Normal is
    normalized; d is the signed offset from origin along the normal."""
    n = find_normal(p1, p2, p3)
    n_unit = n * (1.0 / abs(n))           # mvp idiom — no .normalize()
    d = -n_unit.dot(p1)
    return (n_unit, d)


def distance_to_plane(
    point: Vector3D, plane: tuple[Vector3D, float]
) -> float:
    """Signed distance from `point` to `plane`. Positive if `point` is
    on the side that `plane`'s normal points to."""
    normal, d = plane
    return normal.dot(point) + d
```

### Why a tuple, not a `Vector4D`

- mvp doesn't have `Vector4D`. Adding it just for plane equations is overkill — the use cases in the course are isolated (planar shadow + frustum culling).
- The tuple form is more pedagogically explicit: a plane is "a normal and an offset," not "four numbers in a row." Reading `normal, d = plane` documents itself; reading `plane[0:3]` doesn't.
- If/when `Vector4D` arrives later (e.g. for homogeneous coords, or because Bill ports a chapter that needs it), `plane_equation` can be re-typed without changing call sites that destructure.

### Whether `find_normal` should normalize

SuperBible's `m3dFindNormal` does **not** normalize — it leaves you the cross-product magnitude (which equals 2× triangle area, sometimes useful). `plane_equation` normalizes internally. Mirror that split: `find_normal` returns the raw cross product; `plane_equation` normalizes.

## Update `__all__`

Append `"find_normal"`, `"plane_equation"`, `"distance_to_plane"` to the `__all__` list at the top of `mathutils.py`.

## Tests (`tests/test_mathutils.py`)

- `find_normal` of three points on the XY plane returns `±Z` (sign determined by winding).
- `plane_equation` for three points on the XY plane returns `((0,0,±1), 0)`.
- `distance_to_plane` for the origin against an XY plane equation is 0; for `(0,0,5)` against `((0,0,1), 0)` is 5; for `(0,0,-5)` is -5.
- Non-axis-aligned plane: pick three points on `x + y + z = 1`, check normal is `(1,1,1)/√3` (up to sign), `d = -1/√3` (or matching sign).

## Scope

- Add the three functions to `mathutils.py`.
- Add unit tests in `tests/test_mathutils.py`.
- Don't yet *use* them anywhere — wiring them into a demo (e.g. litjet) is a separate task.

## Open questions

- Do we want a separate type like `@dataclass class Plane: normal: Vector3D; d: float` instead of a bare tuple? Pro: documents intent everywhere. Con: one more name to learn for very little payoff. Recommend bare tuple unless a third caller appears.
- Should `find_normal` return a normalized vector (matching the *intuitive* meaning of "normal vector") instead of mirroring SuperBible's unnormalized convention? Recommend mirroring SuperBible for direct portability — but this is a judgment call.
