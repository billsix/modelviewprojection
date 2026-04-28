# Plan: `rotate_around_axis` in `pyMatrixStack`

**Status:** not started — research-only until Bill OKs the decomposition below.

**Reference implementation in the ports tree (NOT what to copy):** `chapt04/transform/transform.py` and `chapt04/transformgl/transformgl.py` have a `rotation_matrix_about_axis(angle_rad, x, y, z)` that does **direct Rodrigues** — that's the *faithful translation* of `m3dRotationMatrix44` in math3d.cpp. **This task wants the opposite** for the curriculum side: build arbitrary-axis rotation as a *composition of axis-aligned rotations* (`rotate_z` to align in XZ-plane, `rotate_y` to align with X, `rotate_x` for the actual rotation, then inverse to undo alignment) — Bill's pedagogical choice so students see arbitrary-axis rotation built from rotations they already know. The ports tree's direct Rodrigues stays as-is (the C++ does it that way, so the faithful translation should too); the curriculum side gets the decomposed version.

## What

Add a `rotate_around_axis(matrixStack, axis, angle)` to `src/modelviewprojection/pyMatrixStack.py` — equivalent to SuperBible's `m3dRotationMatrix44(angle, x, y, z)` and OpenGL's `glRotatef(angle, x, y, z)`.

Used heavily by `GLFrame::RotateLocal*`/`RotateWorld` in chapt05+. Without it, porting any `GLFrame`-driven demo (`sphereworld`, anything with an FPS camera) requires fighting the source.

## Why pyMatrixStack and not mathutils

Bill's instruction: "for tier one, update pyMatrixStack to have equivalent functionality, in my style." mathutils-side `rotate_x/y/z` already exists as `InvertibleFunction[Vector3D]`; the matrix-era equivalent goes in pyMatrixStack to match the demo era (19+) where SuperBible-style demos get ported.

(If Bill later wants the same in mathutils as `rotate_around_axis` returning `InvertibleFunction[Vector3D]`, the same decomposition works there — just with `compose([...])` instead of in-place matrix mutation. Note as future work.)

## Approach — decomposed, *not* Rodrigues

Bill's instruction: "have it be composed of a sequence of matrix multiplications. For instance, you can rotate the vector to the x axis, through 3 rotations, and the rotate around the x axis, and then rotate everything back."

Pedagogical goal: instead of dropping a 4×4 Rodrigues formula on the student, *derive* arbitrary-axis rotation as composition of axis-aligned rotations the student already knows. The student sees rotation about an arbitrary axis built from rotations about X, Y, Z — keeping with the "everything is a composition of simpler functions you've seen" spine of the course.

### Algorithm (sketch — refine with Bill)

Given a unit axis `a = (ax, ay, az)` and angle `θ`:

1. **Align `a` with +X** by composing axis-aligned rotations:
   - Compute α to rotate about Z so `a` lands in the XZ plane (sends `ay → 0`).
   - Compute β to rotate about Y so the rotated `a` lands on +X (sends `az → 0`).
   - (Bill mentioned **3** rotations in the alignment step; the natural derivation needs 2. Open question — see below. Possibilities: a third rotation that's intentionally a no-op for pedagogical symmetry, or a different decomposition I haven't seen yet.)
2. Apply `rotate_x(θ)` — the rotation about the now-aligned axis.
3. **Undo step 1** in reverse order, with negated angles: `rotate_y(-β)`, then `rotate_z(-α)`.

The final composition (left-to-right in OpenGL post-multiply order) is:

```
M  ←  M · Rz(α) · Ry(β) · Rx(θ) · Ry(-β) · Rz(-α)
```

Implementation can be either:
- **(a) Sequential application:** call existing `rotate_z`, `rotate_y`, `rotate_x` on the same stack in order. This is most pedagogical — the student sees that `rotate_around_axis` *is literally* a sequence of `rotate_z`/`rotate_y`/`rotate_x` calls.
- **(b) Build a single 4×4 matrix from the symbolic product, then `multiply` it in.** More efficient, less pedagogical.

Recommend (a) — efficiency is a non-goal for the course; the readable composition is the point.

## Signature (proposed)

```python
def rotate_around_axis(
    matrixStack: MatrixStack,
    axis: tuple[float, float, float],   # need not be a unit vector — normalize internally
    angle: float,                       # radians
) -> None:
    ...
```

Following the in-place mutation pattern of `rotate_x` etc.

## Docstring goals

Following the `pyMatrixStack` convention (the docstring explains the math by hand):

1. State the goal: rotate by `angle` about an arbitrary unit axis.
2. Show the alignment computation: how α and β are derived from `(ax, ay, az)`.
3. Show the composition: `Rz(α) · Ry(β) · Rx(θ) · Ry(-β) · Rz(-α)`.
4. Note that this is identical to (and a derivation of) Rodrigues' formula. Don't *show* Rodrigues; mention it exists.

## Scope

- Add `rotate_around_axis(matrixStack, axis, angle)` to `pyMatrixStack.py`.
- Add unit tests verifying:
  - `rotate_around_axis(stack, (1,0,0), θ)` matches `rotate_x(stack, θ)` (within float tolerance).
  - Same for Y and Z.
  - For a generic axis: rotating the axis itself yields the axis (eigenvector property).
  - Round-trip: `rotate_around_axis(stack, axis, θ)` followed by `rotate_around_axis(stack, axis, -θ)` is identity.

## Out of scope

- The mathutils-side `InvertibleFunction[Vector3D]` version. Defer until a demo earlier than demo19 needs arbitrary-axis rotation (unlikely — the Pong scene only uses Z-axis rotations through demo18).
- Caching alignment angles for an axis used many times in one frame. (Don't optimize.)

## Open questions

- **Why "3 rotations" for alignment?** Bill said "rotate the vector to the x axis, through 3 rotations." The standard alignment needs 2 (rotate-Z then rotate-Y). I'll start the plan with 2, but flag this — Bill might be remembering a 3-step decomposition I don't know, or might want a redundant third step for some pedagogical reason. Confirm before implementing.
- Bill's docstring style explains the matrix multiplication by hand. For this function, the student-facing math is the *composition derivation*, not the final 4×4 product. The docstring should reflect that — show the alignment, not the elements of the final matrix.
