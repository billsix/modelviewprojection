# Cube-map reflection on the sphere doesn't update as the camera moves

**Status:** complete
**Completed:** 2026-06-01

Fix applied across the four suspect files. Sweep finished 2026-06-01.

## Per-file outcome

| File | Outcome | Notes |
|------|---------|-------|
| `chapt09/cubemap/cubemap.py` | ✅ already fixed | Found during the imgui texture-state sweep (2026-05-29). `render_scene` wraps the sphere draw in `glMatrixMode(GL_TEXTURE)` + `glRotatef(degrees(camera_yaw), 0, 1, 0)` (lines ~145–153). |
| `chapt09/multitexture/multitexture.py` | ✅ fix applied 2026-06-01 | Same pattern as cubemap.py, but on TEXTURE1's matrix stack — `glMatrixMode(GL_TEXTURE)` is per-unit; TEXTURE1 is already the active unit at the sphere draw, so the rotation lands on the cube map's matrix without disturbing TU0's color-map matrix. Six new lines around `draw_sphere_multitex()`. |
| `chapt09/texgen/texgen.py` | N/A | No cube map (uses 2D textures with `GL_OBJECT_LINEAR` / `GL_EYE_LINEAR` / `GL_SPHERE_MAP`). The `y_rot` here is model-rotation, not a walk camera. |
| `chapt11/thundergl/thundergl.py` | N/A | Has `GL_REFLECTION_MAP` on TU1 cube map, **but** `x_rot`/`y_rot` rotate the jet (model), not the camera. The skybox is drawn **before** the rotation block (`thundergl.py:206`, before the `glPushMatrix()` at 208), so the skybox is in world/eye space and stays aligned with eye space → reflection tracks naturally. Same situation as the solar/atom demos. |
| `chapt18/fboenvmap/fboenvmap.py` | N/A | Camera moves in XYZ only, no yaw. And the cube map is **regenerated each frame** by rendering the scene from the reflective object's POV (`regenerate_env_map`, ~`fboenvmap.py:169-188`), which makes the inverse-rotate question moot regardless. |

## The bug pattern (for future reference)

Cube-map *reflection* mapping (`GL_REFLECTION_MAP` texgen on `GL_TEXTURE_CUBE_MAP`)
computes texture coords in **eye space**. For the reflected environment to stay
fixed in the world while the camera moves (i.e. to look like a real mirror), the
classic SuperBible technique inverse-rotates the camera's yaw into the
`GL_TEXTURE` matrix each frame — so the eye-space reflection vector is rotated
back into world space before sampling the cube map.

**Diagnostic checklist** when adding a new cube-map demo or auditing one:
- Is `GL_TEXTURE_CUBE_MAP` enabled and `GL_REFLECTION_MAP` set on S/T/R?
- Does the camera **rotate** (not just translate)? Look for `apply_camera_transform`
  with a `glRotatef(-camera_yaw, 0, 1, 0)` — pure translate cameras don't trigger
  the bug, and model rotations don't either (the eye/world frames stay aligned).
- If yes to both: the sphere draw must be wrapped in `glMatrixMode(GL_TEXTURE)` +
  `glPushMatrix()` + `glRotatef(degrees(camera_yaw), 0, 1, 0)` + draw +
  `glPopMatrix()` + `glMatrixMode(GL_MODELVIEW)`. In multitex cases, the cube
  map's `glActiveTexture` unit must be active before the matrix-mode switch
  (the `GL_TEXTURE` stack is per-unit).

## Verification

Bill runs in-container. Visible-only check:

1. Walk + yaw in `chapt09/multitexture/multitexture.py`. The tarnished sphere's
   reflected environment should stay anchored to the world (same six cube-map
   faces in the same world directions as you turn), not slide with the view.
2. Compare against `chapt09/cubemap/cubemap.py` (already-fixed reference) — the
   two should feel the same when walking.
3. No regressions expected in `texgen` / `thundergl` / `fboenvmap` (untouched).
