# Port every SuperBible v4 demo to Python under `/mvp/ports/openglsuperbiblev4/`

**Status:** the port itself is **COMPLETE** (2026-04-28): ~101 demo files
across chapt01–chapt22 — chapt01–18 real ports, chapt19 mostly real plus
Win32-MFC stubs, chapt20 (Apple) and chapt22 (GL ES) stubs, all
syntax-checked. **What remains open in this task is Bill's hardware
verification** (punchlist below). The follow-on UX work (walk-around camera,
etc.) is `tasks/ports-ux-pass.md`.

**The durable content this doc used to carry — the C++→Python translation
rulebook, the per-demo skeleton, the helper-replacement exemplar table, the
GLFrame unfolding rules, the math3d tier catalog, and the chapter/stub
inventory — was harvested (and de-staled: `Vector3D`→`Vector3`,
`pyMatrixStack`→`matrix_stack`, `np.matrix`→plain `ndarray`, and the
sign-invariant planar-shadow claim corrected) into
`tasks/reference/superbible-ports-guide.md` on 2026-07-30.** Read that, not
old revisions of this file, when porting.

## Open — issues to verify on first hardware run

The ports were syntax-checked but most have not been run on a display. Likely
first-run issues (2026-04-28 list; strike items as Bill verifies):

1. **`chapt04/sphereworld` camera direction** — `forward = (sin(yaw), 0,
   -cos(yaw))` derived from `glRotatef(yaw, 0,1,0)` applied to (0,0,-1). If
   arrow keys feel inverted, flip the sign of `move_step * sin/cos` in
   `handle_camera_keys()`.
2. **`chapt04/transform` rotation direction** — `rotation_matrix_about_axis`
   is standard Rodrigues; if rotation looks reversed, transpose (sign
   convention varies).
3. **`chapt03/single` flicker** — single-buffered behavior depends on the
   driver honoring `glfw.DOUBLEBUFFER = FALSE`; fall back to manual
   accumulation if the spiral doesn't persist.
4. **`chapt01/block` step 5 draws only front/top/right faces** — faithful to
   the C++; looks incomplete on purpose.
5. **`glRotatef` argument types** — wrap angles in `float()` if PyOpenGL
   raises `TypeError`.
6. **`glLightfv` buffer types** — tuples work elsewhere; switch to numpy
   arrays if PyOpenGL complains.

## Remaining open questions (for Bill)

- `chapt21/fonts` was ported (2 files exist in chapt21) — confirm it renders.
- The chapt20/chapt22 "skip entirely" plan became print-a-notice **stubs**
  instead; fine as-is?

## Definition of done (unchanged)

Every demo either ported or explicitly stubbed with a one-line reason (done);
Bill has visually verified the ports on his host (open).
