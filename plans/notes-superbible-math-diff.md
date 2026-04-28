# Notes — Math concepts in /superbible's math3d that are missing from mvp's mathutils.py (Task 2)

> Self-notes from comparing `/superbible/examples/src/shared/math3d.{h,cpp}` against `/mvp/src/modelviewprojection/mathutils.py`. Future-Claude: this is a catalog only — Bill picks what to port. Verify against current `mathutils.py` before suggesting any of these are still missing; he may have added some since this was written.

## Method

For each `m3d*` function in `math3d.h`, asked:
1. Does mvp's `mathutils.py` (or `pyMatrixStack.py`) already have it?
2. Does SuperBible *use* it in a demo (vs. just defining it)?
3. Does it fit Bill's `InvertibleFunction[V]` abstraction, or does it need something else?

Skipped: trivial/duplicate ops (`Load`/`Copy`/`Add`/`Subtract`/`Scale` on vectors, identity matrices, transpose, multiply) — mvp has these via dataclass operators or numpy/`pyMatrixStack`. Skipped 4-vec versions of things mvp covers in 3D — homogeneous coords aren't part of Bill's pedagogy.

## Tier 1 — Missing and *load-bearing for demos Bill wants to port*

### `m3dMakePlanarShadowMatrix(M3DMatrix44 proj, planeEq, lightPos)` ⭐ Bill flagged this

`math3d.cpp:1026`. Builds a 4×4 matrix that projects geometry onto a plane along the rays from a point light. The matrix is **rank 3 — not invertible** (collapses a dimension).

Used in: chapt05/shadow.cpp, chapt05/sphereworld.cpp (the cheap-projection shadow trick — a second pass draws the geometry darkened, with this matrix multiplied in). Bill already references it in demo22 comments (`planar_shadow_matrix` is "still defined and book-referenced for the chapter, but is no longer used at runtime" — superseded by a real shadow map).

**Signature port:** `planar_shadow(plane_eq: Vector4D, light_pos: Vector3D) -> ???`. Returns a transform from world-space → world-space-collapsed-onto-plane.

**Fit with Bill's abstraction:** *Does not fit `InvertibleFunction`.* The whole point is dimensional collapse — there is no inverse. Two options:
1. Add a separate `NonInvertibleTransform` type (or just a plain callable `Vector3D -> Vector3D`). Pedagogically honest: shadows are *not* a coordinate-space conversion, they're a one-way projection.
2. Ship it only as a 4×4 matrix in `pyMatrixStack` (since by demo22+ we're using matrices anyway). Most pedagogically consistent with where it'd be used.

I'd push for option 2 — by the time the student needs planar shadows, they're already in the matrix-stack era, and the "not invertible → not a Cayley-graph edge" point is itself a teaching moment.

---

### `m3dRotationMatrix44(M3DMatrix44 m, angle, x, y, z)` — rotate around arbitrary axis

`math3d.cpp:194`. Rodrigues' formula. Builds a rotation about the unit vector (x,y,z).

mvp has only `rotate_x`, `rotate_y`, `rotate_z`. SuperBible uses arbitrary-axis rotation **constantly** in `GLFrame::RotateLocal*` and `GLFrame::RotateWorld` (chapt05+). Without it, porting any demo that uses `GLFrame` requires composing-out of axis rotations — possible but fights the source.

**Signature port:** `rotate_around_axis(axis: Vector3D, angle: float) -> InvertibleFunction[Vector3D]`. Inverse is straightforward: same axis, negated angle.

**Fit:** Perfect fit for `InvertibleFunction[Vector3D]`. Should be added if any GLFrame-using demo gets ported. Honestly, it's surprising it isn't there already.

---

### `m3dFindNormal(result, p1, p2, p3)` — face normal from three vertices

`math3d.cpp:763`. `cross(p1-p2, p2-p3)`. **Used in litjet for every face** to compute a per-face normal for lighting.

**Signature port:** `find_normal(p1: Vector3D, p2: Vector3D, p3: Vector3D) -> Vector3D`.

**Fit:** It's not a transform, it's just `(p1 - p2).cross(p2 - p3)` — a geometric helper. Mvp's `Vector3D.cross` already exists; this is a one-liner wrapper that names the operation. Worth adding as a free function in `mathutils.py`.

**Note:** Mvp could also derive normals analytically once and bake them into the geometry, sidestepping the function — but porting *litjet specifically* mirrors the source much more faithfully if `find_normal` is available.

---

### `m3dGetPlaneEquation(planeEq, p1, p2, p3)` — Ax + By + Cz + D = 0 from three points

`math3d.cpp:807`. Returns `Vector4D` with (A, B, C, D) the plane equation. Used to define a ground plane as input to `m3dMakePlanarShadowMatrix` and to `GLFrustum.TestSphere`.

**Signature port:** `plane_equation(p1, p2, p3) -> Vector4D` — but mvp doesn't have `Vector4D`. Could return `tuple[Vector3D, float]` (normal, d) which is more pedagogical anyway.

**Fit:** Pure geometry helper, not a transform. Pairs with `find_normal` and `planar_shadow`.

---

### `m3dGetDistanceToPlane(point, planeEq)` — signed distance

`math3d.h:702`. One-liner: `dot(point, planeNormal) + planeD`. Used in `GLFrustum.TestSphere` for frustum culling.

**Signature port:** trivial helper, complementary to `plane_equation`.

---

## Tier 2 — Missing, *might* matter depending on which demos get ported

### `m3dRaySphereTest(point, ray, sphereCenter, radius)` — ray vs sphere intersection

`math3d.cpp:914`. Returns negative if no hit, 0 if tangent, positive distance otherwise. Used in picking demos and frustum culling alternatives.

**Fit:** Not a transform. Just a free function. Returns `float | None` in Python (None for miss).

### `m3dClosestPointOnRay(out, rayOrigin, rayDir, point)` — projection of point onto ray

`math3d.cpp:1110`. Returns the closest point on the ray to a given point in space, plus the squared distance. Used in some interactive demos.

**Fit:** Free function.

### `m3dCalculateTangentBasis(triangle, texCoords, normal, vTangent)` — tangent vector for normal mapping

`math3d.cpp:966`. Computes a tangent vector given a triangle, its UVs, and a normal. **Required if Bill ever ports chapt17/bumpmap.**

**Fit:** Free function. Doesn't touch the InvertibleFunction story.

### `m3dSmoothStep(edge1, edge2, x)` — GLSL-style smoothstep

`math3d.cpp:1000`. Cubic interpolation. Easy to add (`numpy.clip` plus `t*t*(3 - 2*t)`). Used mostly in shaders, not in CPU code, so likely unnecessary on the Python side.

### `m3dCatmullRom(out, p0, p1, p2, p3, t)` — spline interpolation

`math3d.cpp:857`. Catmull-Rom interpolation between p1 and p2 with p0 and p3 as control. Useful for camera paths or animated splines. Not seen in any demo on Bill's wishlist.

### `GLFrustum.TestSphere(point, radius)` — frustum culling

In `glfrustum.h`. Builds 6 plane equations from the camera frustum and tests a sphere against each. Useful when porting `chapt19/SphereWorld32` (large numbers of objects). Composes from `plane_equation` + `distance_to_plane`.

---

## Tier 3 — Trivial in mvp's idiom, mention only if asked

These are operations math3d defines as standalone functions but mvp expresses inline:

| math3d | mvp equivalent |
|--------|----------------|
| `m3dGetVectorLength(v)` | `abs(v)` (already defined via `__abs__`) |
| `m3dGetVectorLengthSquared(v)` | `v.dot(v)` |
| `m3dGetDistance(a, b)` | `abs(a - b)` |
| `m3dGetDistanceSquared(a, b)` | `(a - b).dot(a - b)` |
| `m3dNormalizeVector(v)` | `v * (1.0 / abs(v))` — mvp has no in-place `.normalize()`, but `uniform_scale(1/abs(v))(v)` works |
| `m3dGetAngleBetweenVectors(u, v)` | `math.acos(cosine(u, v))` — mvp has `cosine` already |
| `m3dCloseEnough(a, b, eps)` | `numpy.isclose(a, b)` or `Vector.isclose` |

If Bill wants any of these as named primitives for pedagogical reasons, easy to add. Otherwise leave inline.

---

## Notable things math3d is also missing (just to note)

These would be expected in a "modern" math library but aren't in math3d either, so SuperBible doesn't pressure them:

- **Quaternions** — neither library has them. SuperBible relies on `GLFrame` (forward + up vectors) for orientations, which avoids the gimbal-lock issue without needing quats.
- **`lookAt(eye, center, up)`** — neither library exposes this directly. SuperBible uses `GLFrame::ApplyCameraTransform` (which is essentially lookAt-from-frame-vectors); mvp builds the equivalent from `inverse(translate(camera_pos))` + rotation `InvertibleFunction`s.
- **`frustum`/`perspectiveFov`** as standalone matrix builders — math3d has neither (relies on `glFrustum` / `gluPerspective`); mvp has `mathutils.perspective` which is already a richer API.

---

## Recommendation summary (for Bill's review — don't act on this without him)

If anything from this list gets added to `mathutils.py`, suggested order:
1. **`rotate_around_axis(axis, angle)`** — fits InvertibleFunction perfectly, unlocks porting any GLFrame-driven demo.
2. **`find_normal(p1, p2, p3)`** + **`plane_equation(p1, p2, p3)`** + **`distance_to_plane(point, plane)`** — small geometry utilities that go together; needed for litjet, planar shadows, frustum culling.
3. **`planar_shadow(plane, light)`** — *as a matrix in `pyMatrixStack`*, not as an `InvertibleFunction`. Important teaching moment about non-invertible transforms; should explicitly be flagged in the chapter as "this is *not* a Cayley graph edge."

Tier 2 items only on demand (port the demo that needs them, then add the helper).

## Open questions for Bill

- Is the `InvertibleFunction` story fundamental, or are there places where *non*-invertible transforms (planar shadows, view-projection-with-perspective-divide) are pedagogically important enough to introduce a sibling type? My read is yes — and the planar shadow demo is exactly the moment to introduce it.
- For arbitrary-axis rotation: is the missing primitive an oversight, or deliberate (does Bill prefer students to compose `rotate_x/y/z` as a stepping stone before introducing Rodrigues)?
