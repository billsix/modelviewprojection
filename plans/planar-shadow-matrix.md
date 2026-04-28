# Plan: Planar shadow projection matrix in `pyMatrixStack`

**Status:** not started — research-only until Bill OKs the approach below.

**Reference implementation already in the codebase:** `chapt01/block/Block.py` has working inline `get_plane_equation()` and `make_planar_shadow_matrix(plane_eq, light_pos)` that returns a column-major flat 16-element numpy array, used via `glMultMatrixf`. Match those formulas (taken directly from `math3d.cpp:1026`) when implementing the `pyMatrixStack` version. The chapt01/block helpers will eventually be replaceable by `from modelviewprojection.mathutils import plane_equation` (Tier-1 task #5) and `from modelviewprojection.pyMatrixStack import planar_shadow` (this task) — until then the ports keep their inline copies.

## What

Add `m3dMakePlanarShadowMatrix` equivalent to `src/modelviewprojection/pyMatrixStack.py`. Builds a 4×4 matrix that projects geometry onto a plane along rays from a point light — the cheap "squish geometry into the floor" shadow trick from chapt05/shadow.cpp and chapt05/sphereworld.cpp.

## Why this lives in `pyMatrixStack` and not `mathutils.py`

The transform **collapses 3D → a 2D-on-a-plane subspace** — it has rank 3, not 4. There is no inverse. So it cannot be wrapped in `InvertibleFunction[V]`, which is the central abstraction in `mathutils.py`. Putting it in `pyMatrixStack` matches both:
- where it's actually used (demo22-and-after, all matrix-era)
- the pedagogical honesty: the shadow matrix is **not** an edge in the Cayley graph. The book chapter that introduces it should explicitly say so — that's the teaching moment.

## Signature (proposed)

```python
def planar_shadow(
    matrixStack: MatrixStack,
    plane_eq: tuple[float, float, float, float],   # (a, b, c, d) for ax+by+cz+d=0
    light_pos: tuple[float, float, float],          # point light in world space
) -> None:
    ...
```

Matches the in-place mutation idiom of `rotate_x`, `translate`, `scale`. The matrix is built and then `multiply`d into the current matrix at `matrixStack[-1]`. (Or it could replace `multiply(matrixStack, shadow_mat)` — TBD which fits the docstring style better; I'll mirror whichever existing function is closest.)

Why pass the plane as a 4-tuple rather than introducing a `Plane` class: matches SuperBible's API and the math literature. Vector4D is otherwise absent from mvp; adding it just for this is overkill.

## How — match Bill's documentation idiom

`pyMatrixStack` functions all have a docstring that:
1. Shows the matrix in row-major, 1-based notation
2. Shows the matrix multiplication worked out by hand
3. Then implements the in-place reduction

The shadow matrix has a clean derivation: for a plane `ax + by + cz + d = 0` with point light at `L = (Lx, Ly, Lz)`, project a point `P` along the line through `L` and `P` onto the plane. The 4×4 form (from `math3d.cpp:1026`) is:

```
[ b·dy + c·dz,    -b·dx,         -c·dx,                  -d·dx                  ]
[ -a·dy,          a·dx + c·dz,   -c·dy,                  -d·dy                  ]
[ -a·dz,          -b·dz,         a·dx + b·dy,            -d·dz                  ]
[ 0,              0,             0,                       a·dx + b·dy + c·dz   ]
```

where `dx = -Lx`, `dy = -Ly`, `dz = -Lz` (from SuperBible). Note column-major storage in numpy — implementation needs the transpose at write time.

The docstring should:
- Show the *derivation* (substitute the parametric line `P + t(L - P)` into the plane equation, solve for t, expand) — pedagogically, this is the punchline. A few lines of algebra.
- State explicitly: **this matrix has rank 3, is not invertible, and is not a Cayley graph edge.**
- Reference the book chapter that introduces it.

## Scope

- Add `planar_shadow(matrixStack, plane_eq, light_pos)` to `pyMatrixStack.py`.
- Don't yet wire it into any demo. (Demo22 already has a real shadow map; planar shadow is mentioned in comments but not used. A future task could add a demo that uses *only* the planar shadow trick, for chapter-aligned pedagogy.)
- Don't yet add a book chapter — that's a separate authoring task for Bill.

## Test plan

- Unit test: a known plane (e.g., y=0, plane_eq=(0,1,0,0)) and a known light (e.g., above the plane at (0, 5, 0)) should map an arbitrary point to the expected projected point — verify with one or two hand-computed cases via `pytest`.
- Determinant of the 4×4 must be 0 (rank deficiency).

## Open questions

- The signature uses tuples for `plane_eq` and `light_pos`. Should it instead take a `Vector3D` for the light and accept a `Vector4D`-shaped argument? Adding `Vector4D` to `mathutils.py` for this one use is probably not worth it; a 4-tuple is fine.
- Should the docstring derivation be written as a chapter aside, or as inline LaTeX in the docstring? Match the existing style — the existing functions use plain ASCII matrices, so likely the same.
