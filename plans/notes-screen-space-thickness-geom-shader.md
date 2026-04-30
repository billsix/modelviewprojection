# Note: the screen-space-thickness geometry shader

A small shout-out to Bill's `frustum.geom` (and its siblings in the
mvpVisualization tree).

When we ported the NDC cube and the frustum from "thick lines via geom
shader" to "solid cylinder geometry" during Phase 2 of the axis cylinder+cone
work, the frustum animation in
`/mvp/mvpVisualization/modelviewperspectiveprojection/modelviewperspectiveprojection.py`
revealed a problem: as the projection animation squashes back-edge X/Y by a
factor of `near_z / far_z` (≈ 25× compression with the default `near_z=-2`,
`far_z=-50`), the cylinders' world-space radius (0.05) becomes sub-pixel in
screen space. The rasterizer can't fill triangles smaller than a pixel
center; result is a stippled, broken-line appearance on the back edges
during the squash.

The original line-rendering pipeline did **not** have this problem, because
`frustum.geom` (and `axis.geom` / `cube.geom` / `ground.geom`) takes a line
in clip space, computes the orthogonal direction in **screen space**, and
emits a triangle-strip quad with constant **pixel** thickness. The output
quad's screen width is decoupled from world-space depth — back edges stay
exactly as visible as front edges, no matter how aggressive the projection
squash gets.

So the fix for the squash was to revert the perspective frustum specifically
back to the line + geometry-shader pipeline that was already there. The
geom shader (in
`/mvp/mvpVisualization/modelviewperspectiveprojection/frustum.geom`) does
the heavy lifting:

```glsl
vec4 unit_direction_of_line_screen =
    normalize(p2_screen - p1_screen);
vec4 thickness_orthogonal_direction_of_line_screen =
    vec4(u_thickness * vec2(-unit_direction_of_line_screen.y,
                            unit_direction_of_line_screen.x),
         unit_direction_of_line_screen.z, 0.0);
```

Two screen-space ops — normalize the line direction, take the perpendicular,
scale by `u_thickness` (pixel count) — and then the offset is transformed
back into clip space via `inverseTranspose(matrix_ndc_to_screen)` and the
homogeneous `w` of each endpoint. The resulting quad is *exactly*
`u_thickness` pixels wide regardless of camera distance, projection mode, or
animation state.

This trick is general-purpose. The other places in the codebase where
constant screen-space thickness matters (animated projection demos, the
NDC-space outline in modelview2d, anywhere a line could go sub-pixel) all
benefit from the same shader. It's the right tool for "lines that stay
visible at any depth" — a cleaner approach than the cylinder geometry for
animated/projected line work.

Credit: this is Bill's shader, predating the recent refactor. It came along
for free with the original line rendering, then we rediscovered why it's
load-bearing the moment we tried to replace it with cylinders during the
squash animation.
