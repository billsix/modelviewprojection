# Cube-map reflection on the sphere doesn't update as the camera moves

**Status:** partially resolved — found 2026-05-29 (during the imgui texture-state sweep) that
`chapt09/cubemap` ALREADY has the fix: `render_scene` wraps the sphere draw in a `GL_TEXTURE`
matrix `glRotatef(degrees(camera_yaw), 0,1,0)` ("inverse-rotate so reflections track the camera").
So cubemap is DONE. **`chapt09/multitexture` does NOT** have it — its cube-map reflection is on
texture unit 1 and won't track the camera; the same fix needs applying on unit 1's texture matrix
(wrap the sphere draw in `glActiveTexture(GL_TEXTURE1)` → `glMatrixMode(GL_TEXTURE)` → push →
rotate by camera_yaw → draw → pop → restore). `chapt09/texgen` is N/A (model-rotate, no walk
camera). Also check `chapt18/fboenvmap` / `chapt11/thundergl` (cube-map reflection) for the same.
Untested in-container — Bill verifies. NOT yet applied to multitexture (don't want to re-touch the
just-confirmed-working file blind without his go-ahead).

## Symptom

In the cube-map demos, the reflective sphere's texture (the mirrored environment)
**does not change as you walk the camera around** — the reflection looks glued in place
instead of tracking the view, so the sphere doesn't behave like a mirror.

## Affected demos (confirm during investigation)

- `ports/openglsuperbiblev4/chapt09/cubemap/cubemap.py` — sphere reflects a cube map via
  `glTexGen` reflection mapping; the skybox is a separate manually-textured cube.
- `ports/openglsuperbiblev4/chapt09/multitexture/multitexture.py` — cube-map reflection on
  texture unit 1 (color map on unit 0). Likely the same root cause.
- `ports/openglsuperbiblev4/chapt09/texgen/texgen.py` — has a `GL_SPHERE_MAP` mode; check
  whether it shows the analogous "reflection doesn't track the view" problem.

## First question: regression or pre-existing?

These ports were "syntax-checked, never hardware-verified" (see superbible-full-port plan),
and they only became runnable/visible during the geometry-extraction spot-checks. The sphere
in cubemap/multitexture was just converted to `_primitives.build_sphere` + `draw_mesh`
(see [[extract-data-generation]]). That conversion is emission-byte-identical (verified) and
keeps the same per-vertex `glNormal3f`, on which reflection texgen depends — so it *should*
be unrelated, but rule it in/out first:
- **Step 1:** `git stash` / check out the pre-conversion `cubemap.py` and run it. If the
  reflection is *also* static there, it's pre-existing (not the extraction). If it tracked
  the view before and not now, it IS the extraction — investigate the normal/texcoord emission.

## Leading hypothesis (pre-existing camera/texture-matrix issue)

Cube-map *reflection* mapping (`GL_REFLECTION_MAP`/`GL_NORMAL_MAP` texgen) computes texture
coords in **eye space**. For the reflected environment to stay fixed in the *world* while the
camera moves (i.e. to look like a real mirror), the classic GLTools/SuperBible technique loads
the **inverse of the camera's rotation** into the `GL_TEXTURE` matrix each frame, so the
eye-space reflection vector is rotated back into world space before sampling the cube map.

The walk-around camera in these ports was added later (UX pass: `apply_camera_transform`
= `glRotatef(-yaw)` + `glTranslatef(-pos)` on the MODELVIEW). If the demo never mirrors the
camera rotation into the texture matrix, then as you turn, the modelview changes but the
cube-map lookup doesn't compensate → the reflection appears static relative to the view.
Check `setup_rc` / `render_scene` for any `glMatrixMode(GL_TEXTURE)` handling; the original
`CubeMap.cpp` set the texture matrix from the camera each frame.

## Things to verify during investigation
- Which texgen mode each demo sets (`GL_REFLECTION_MAP` vs `GL_NORMAL_MAP` vs `GL_SPHERE_MAP`).
- Whether `GL_TEXTURE_CUBE_MAP` is enabled and texgen is enabled for S/T/R.
- Whether a `GL_TEXTURE`-matrix update tied to the camera is present or missing.
- Whether the camera transform is applied before/after the sphere's normals are consumed.

## Fix
Once root cause is confirmed, fix faithfully to `CubeMap.cpp` (mirror the camera rotation into
the texture matrix per frame, or whatever the original did). Keep the extracted-geometry
conversion intact. Re-verify by walking the camera and confirming the reflection tracks.
