# Plan: fix `chapt14/shadowmap` (SuperBible v4 port) — shadows don't render

**Status:** NOT done — the one v4 demo that didn't land in the 2026-05-13
session (two diagnoses were tried and reverted by Bill). Brought into master
2026-05-27 alongside the v4 ports pull. Full session context:
[`HANDOFF-2026-05-13.md`](archive/2026/05/26/HANDOFF-2026-05-13.md).

## Symptom
`ports/openglsuperbiblev4/chapt14/shadowmap/shadowmap.py` — the shadow pass
produces no shadow. The depth/shadow map itself *is* generated (press **M** to
view it as grayscale); the failure is in the **texture-matrix math** that
projects the shadow map onto the scene.

## Current code (HEAD / reverted to pre-attempt state)
```python
bias_matrix = np.array([0.5,0,0,0, 0,0.5,0,0, 0,0,0.5,0, 0.5,0.5,0.5,1.0],
                       dtype=np.float32).reshape(4, 4)
proj = light_projection.reshape(4, 4)
mv   = light_modelview.reshape(4, 4)
m = (bias_matrix @ proj @ mv).T
texture_matrix = m.flatten().astype(np.float32)
```
The texture matrix is fed as four `glTexGenfv(GL_{S,T,R,Q}, GL_EYE_PLANE, ...)`
calls — chunks `[0:4]`, `[4:8]`, `[8:12]`, `[12:16]` must each be one **row** of
`bias · proj · mv` (S plane = row 0, etc.).

## What was tried and reverted (don't just re-try these)
- Reordering to `(mv @ proj @ bias_matrix).T` — Bill: "not working."
- Adding LEFT/RIGHT→X, UP/DOWN→Z arrow keys + `glfw.REPEAT` — couldn't be
  separated from the matrix bug, so its correctness is unknown.

## Do this FIRST next attempt — empirical math test (the step skipped last time)
Write a ~20-line scratch script:
1. `bias = identity`, `proj = translate(1,0,0)`, `mv = identity`.
2. Expected math matrix `bias · proj · mv == translate(1,0,0)`.
3. Run the candidate numpy expression.
4. Assert the flat result's S-plane (row 0) `== [1,0,0,1]`.

If it fails for identity-ish inputs the expression is wrong; if it passes those
but fails non-commuting cases, the multiply *order* is wrong. C++ reference:
`m3dMatrixMultiply44(P,A,B)` computes `P = A*B` column-major
(`m[col*4+row]`) — i.e. `bias * proj * mv` in math order
(`/sb/examples/src/shared/math3d.cpp:78-93`).

## Lower-priority follow-ups (same file)
- `glPolygonOffset(factor, 0.0)` uses `units=0` (matches C++); shadow acne may
  later need nonzero units.
- The `S` key toggles shadows off; while shadows never render, on/off look
  identical (confusing during debugging).

## Verification
`py_compile`; Bill runs it on his display (needs a GL context — not testable in
this container). Shadows should render and track the light; **M** should still
show the depth map.
