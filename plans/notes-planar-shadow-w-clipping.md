# Planar shadow matrices: not sign-invariant under OpenGL clipping

**Status:** ✅ resolved — the sign-correcting fix described below is implemented
in `ports/openglsuperbiblev4/chapt01/block/Block.py`
(`make_planar_shadow_matrix`), pulled into master 2026-05-27. Kept in `plans/`
as a durable reference note (the gotcha still applies to any future
planar-shadow helper, e.g. curriculum-side `pyMatrixStack.planar_shadow`).

Durable technical note from the chapt01/block port. Applies to any
port that builds a planar shadow matrix — including the wishlisted
chapt05/shadow port and the curriculum-side
`pyMatrixStack.planar_shadow` (see plans/planar-shadow-matrix.md).

## The trap

The SuperBible planar shadow matrix `S(plane, light)` projects geometry
onto the ground plane along rays from the light. Its bottom row is
`(0, 0, 0, n · (-light.xyz))`, so every transformed vertex `(x,y,z,1)`
lands at clip-space `w = n · (-light.xyz)`, **regardless of the input
position**. That `w` is constant across the whole shadowed mesh.

In projective geometry, `(p, w)` and `(-p, -w)` are the same 3D point
after perspective divide. So flipping the sign of the plane normal
flips the sign of every entry of `S`, but the post-divide projection
is the same. The CLAUDE.md note that called planar-shadow matrices
"sign-invariant" was working from this observation.

**The observation is wrong in OpenGL** because clip-space testing
happens *before* perspective divide. The clip stage tests
`-w ≤ {x, y, z} ≤ w`. When `w < 0`, that inequality is unsatisfiable
for any finite `x, y, z`, and every vertex gets discarded. No GL
error, no warning — the shadow polygon just silently disappears.

## When it bites

- mvp's `mathutils.plane_equation` uses CCW winding. SuperBible's
  `m3dGetPlaneEquation` uses CW. The two differ in sign on the
  returned `(normal, d)`.
- Plug mvp's CCW plane equation into the textbook shadow-matrix
  formula and `n · (-light.xyz)` lands negative for a typical
  ground-plane / overhead-light setup. → All shadow vertices have
  `w < 0` → all clipped → no shadow visible.
- Plug SuperBible's CW plane equation in (or mirror the C++ port
  literally) and `w` lands positive. Shadow renders.

## Fix

Inside the shadow-matrix builder, check the sign of the constant
`w`-output and negate the entire matrix if needed:

```python
sign = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
# multiply every entry of the 4x4 by `sign`
```

This makes the helper robust to either plane-sign convention. The
same one-liner belongs in any other planar-shadow helper we add
(curriculum-side `pyMatrixStack.planar_shadow`, future port helpers,
etc.).

Reference implementation: `make_planar_shadow_matrix` in
`ports/openglsuperbiblev4/chapt01/block/Block.py`.

## How it was found

Block.py step 4 (lit cube + planar shadow) and step 3 (lit cube only)
rendered pixel-identical frames under headless Mesa — same red-cube
pixel count, same blue-floor count. No GL error from `glGetError()`.

The matrix was uploaded correctly: `glGetFloatv(GL_MODELVIEW_MATRIX)`
after `glMultMatrixf(shadow_mat)` returned exactly the matrix that
went in. Manual `M @ v` on a cube vertex gave `(x', y', z', -120)`
— `w = -120` was the smoking gun. Confirmed by monkey-patching the
helper to return `-shadow_mat`; shadow appeared immediately.
