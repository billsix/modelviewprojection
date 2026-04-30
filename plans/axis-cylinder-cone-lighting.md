# Lighting for the cylinder+cone axes (deferred)

**Status: deferred 2026-04-30.** Bill verified the cylinder+cone axes look
correct on hardware; current shading is flat. He wants the lighted look
from the source demo eventually, just not today.

## Context

The cylinder+cone axis arrows in `demo19a.py`,
`mvpVisualization/modelview/modelview.py`, and the 6 mvpVisualization demos
(coordinatesystems, model, pushmatrix, modelview2d, modelvieworthoprojection,
modelviewperspectiveprojection) were ported from
`/mvp/ports/openglsuperbiblev4/chapt10/axes3d/axes3d.py` and double-thickness
applied (`rod_radius=0.05`, `cone_radius=0.12`).

The geometry helpers already emit per-vertex `glNormal3f` calls (cylinder
side: outward radial normal; cone tip: +Z; cone base disk: -Z; cylinder
bottom cap: -Z), so the meshes are lighting-ready. Nothing in the ported
code enables lighting though — the chapt10 source's `setup_rc()` (lines
103–119) did, and we did not copy that block. Result: solid cylinders with
no shading falloff, all one flat color.

## Reference: original lighting setup

From `/mvp/ports/openglsuperbiblev4/chapt10/axes3d/axes3d.py:103-119`:

```python
def setup_rc() -> None:
    white_light  = (0.05, 0.05, 0.05, 1.0)
    source_light = (0.25, 0.25, 0.25, 1.0)
    light_pos    = (-10.0, 5.0, 5.0, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, white_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT,  source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE,  source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
```

The crucial bit is `GL_COLOR_MATERIAL` + `glColorMaterial(GL_FRONT,
GL_AMBIENT_AND_DIFFUSE)`: each `glColor3f` call in the draw functions then
implicitly sets the material's ambient and diffuse, so the existing
red/green/blue + grayed-out logic keeps working with no other change.

## Option 1 — Cheap win: fixed-function demos

**Scope:** `demo19a.py` and `mvpVisualization/modelview/modelview.py` only.
~15 minutes total.

Both files are fixed-function (1.4 / 2.x), `glColor3f`-based. Drop the lighting
block above into each file's existing depth-setup region (right after the
existing `glEnable(GL_DEPTH_TEST)` line). The cylinder+cone normals already
in the helpers will produce the expected shading.

**Caveat — face culling:** The original demo enabled `GL_CULL_FACE`. Our ports
don't. Adding `GL_CULL_FACE` along with lighting requires the cylinder/cone
helpers' winding to be consistently CCW from the outside. The current
helpers were copied verbatim from chapt10 (which assumes CCW + culling), so
this should be safe — but spot-check after enabling. If culling produces
holes, swap two vertices in one of the triangle fans or skip culling.

### Files
- `/mvp/src/modelviewprojection/demo19a.py` — add the lighting block before
  the main loop. Keep `glColor3f` calls in `draw_unit_axes` as-is.
- `/mvp/mvpVisualization/modelview/modelview.py` — same, before the main loop.

### Verification
- Run each demo. Cylinders should show smooth shading (brighter on the
  side facing `(-10, 5, 5)`, darker on the opposite side). Cone tips should
  shade darker on the back face.
- Grayed-out axes (in `modelview.py`'s animation states) should still show
  gray-shaded (lit gray, not flat gray) because `GL_COLOR_MATERIAL` makes
  `glColor3f(0.5, 0.5, 0.5)` set the gray as the material color.

## Option 2 — Full polish: 6 mvpVisualization demos (3.3 Core, shaders)

**Scope:** the 6 shader-based mvpViz demos.

These don't have a fixed-function pipeline; they use `axis.vert +
triangle.frag` with a single `uniform vec3 color`. To light the axes:

1. **Add a normal vertex attribute.** Modify `_pipeline.build_axis_arrow_solid()`
   to also return per-vertex normals, OR add a parallel
   `build_axis_arrow_solid_normals()`. Cylinder side normal = outward radial
   `(c, 0, s)`; cone side normal = `(c, slope, s)` normalized (slope = base /
   length); cone base disk = `(0, -1, 0)`; cylinder bottom cap = `(0, -1, 0)`.
   (All in the +Y-pointing local frame after my Rx(-90) convention — verify
   normals after rotation.)

2. **New shader pair per demo dir** (or a shared one). Easiest is add
   `axis_lit.vert` and `axis_lit.frag` in each demo dir:
   - `axis_lit.vert`: takes `position` + `normal`, computes
     `world_normal = normalize(normal_matrix * normal)`,
     `world_pos = mMatrix * vec4(position, 1)`, passes both to frag plus the
     `uniform vec3 color`.
   - `axis_lit.frag`: per-pixel Lambert:
     ```glsl
     vec3 L = normalize(light_pos - world_pos);
     float lambert = max(dot(world_normal, L), 0.0);
     out_color = vec4(color * (ambient + lambert * diffuse), 1.0);
     ```
     `light_pos` / `ambient` / `diffuse` as uniforms (constants for now,
     matching chapt10's values: ambient=(0.25, 0.25, 0.25), diffuse=(0.25,
     0.25, 0.25), light at (-10, 5, 5)).

3. **`make_lit_lines_vao(positions, normals, attr_position, attr_normal)`** in
   `_pipeline.py` — analogous to `make_lines_vao` but with two VBOs.

4. **Rewire each demo's `_emit_axis`** to bind `axis_lit_program`, upload the
   light/material uniforms (or set them once at startup since they're
   constant), upload mvp+normal_matrix, draw `GL_TRIANGLES`. Keep the
   `grayed_out` branch — it still sets the `color` uniform to (0.5, 0.5,
   0.5).

5. **Animated demos** (modelview2d, ortho, perspective): the lit vert shader
   needs to apply the same `project()` morphing as `axis.vert`. Either
   include the `project()` block in `axis_lit.vert`, or factor it into a
   shared GLSL include — but the codebase doesn't currently use #include, so
   simplest is: 6 copies of `axis_lit.vert`, the 3 animated ones include the
   `project()` body.

### Files
- `/mvp/mvpVisualization/_pipeline.py` — add normals to
  `build_axis_arrow_solid()` (or a sibling builder), add `make_lit_lines_vao`.
- 6 × `axis_lit.vert` + 6 × `axis_lit.frag` (12 new shader files), one set
  per demo dir. Animated copies in modelview2d / ortho / perspective.
- 6 × demo Python files: replace the axis pipeline + `_emit_axis` with the
  lit version.

### Estimated effort
~80–120 LoC across the 6 Python files, ~12 new shader files.

### Reference
Demo22 already does Lambert lighting in shaders — model on
`/mvp/src/modelviewprojection/demo22/block.frag` for the lit-frag pattern.

### Verification
- Run each of the 6 demos. The cylinder+cone axes should show smooth
  shading; visually similar to the fixed-function demos (option 1) once
  done.
- Grayed-out callsites still produce gray-shaded (lit gray) axes.
- modelview2d still 2-axis (X+Y).
- Animated demos still apply `project()` morphing to the axes.
- Perspective's "Show Ground Axises" floating axis still lit and shaded.

## Recommendation

Do option 1 first when revisiting (cheap; immediate visual win for the
curriculum demo and the fixed-function outlier). Defer option 2 until after
the current Phase 2 (NDC cube as cylinders) and Phase 3 (ground as
cylinders) are done, since those will likely also want lighting and it's
worth designing the lit-axis pipeline once the full set of solid geometries
is settled.

## Out of scope

- Specular highlights / shininess (Phong vs Lambert). Demo22 uses Lambert;
  match.
- Per-light shadowing.
- Multiple lights.
