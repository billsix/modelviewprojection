# 3D grapher — lit triangle-mesh surface (Blinn-Phong / half-angle)

**Status:** proposed — needs go-ahead (gated on the base 3D grapher landing first)
**Priority:** 7
**Difficulty:** 6
**Started:** 2026-11-03 (William Emerison Six <billsix@gmail.com>)
**Part of:** the graphing-calculator work — `tasks/graphing-calculator-2d-3d.md` (read that first).
**Depends on:** the base 3D `f(x,y)` grapher (wireframe/mesh) from that task existing.

## BLUF

Take the 3D `f(x,y)` height-field grapher and render its surface as a **solid triangle mesh with
Blinn-Phong lighting** — the half-angle (halfway-vector) specular model, not Phong's
reflection-vector model. This means: triangulate the height field, compute **normals** from it,
add a light, and shade in a core-profile shader. "Done" = the 3D grapher can render its surfaces
as lit, solid triangle meshes (alongside or instead of the wireframe), with a believable
specular highlight that tracks the light and view.

## Why a separate task

The base task (`graphing-calculator-2d-3d.md`) deliberately stops at **wireframe + mesh, no
lighting** so the first version lands small. Lighting adds a real chunk of net-new machinery
(normals, a light model, a lit shader, material params), so it gets its own commit boundary.

## Plan (draft)

- [ ] **Triangulate** the height field: emit two triangles per grid cell (CCW winding — house
      convention, `gl-and-imgui-gotchas.md` §7), indexed by an element buffer.
- [ ] **Normals** from the height field: per-vertex normals (average of adjacent face normals, or
      analytic from the partial derivatives `∂f/∂x`, `∂f/∂y` if the authored function is sampled
      finely). Decide per-vertex vs analytic in review.
- [ ] **Blinn-Phong lit shader** (core profile): diffuse `max(0, N·L)` + specular
      `pow(max(0, N·H), shininess)` where **H is the halfway vector** `normalize(L + V)` — this is
      the "half angles" model (Blinn-Phong), distinct from Phong's `R·V`.
      - Per-fragment is the target (smooth highlight); a per-vertex first cut is acceptable as a
        stepping stone.
- [ ] A single directional or point light; expose light direction / shininess in the menubar
      alongside the existing dx/dy + view controls.
- [ ] Keep wireframe available (toggle), so the lit surface and the mesh can be compared.

## Inspiration — the openglsuperbible v4 port (read before writing the shader)

- `ports/openglsuperbiblev4/chapt16/vertexshaders/shaders/specular.vs` — **per-vertex** half-vector:
  `vec3 H = normalize(L + normalize(-V.xyz)); float NdotH = max(0.0, dot(N, H));
  specular = pow(NdotH, specularExp)` with `specularExp = 128.0`. This is the canonical half-angle
  Blinn-Phong in the tree.
- `ports/openglsuperbiblev4/chapt17/lighting/shaders/specular.{vs,fs}` — the **per-fragment**
  version (interpolate N, L, V to the fragment shader; compute H and the lighting there). This is
  the shape to aim for.
- These v4 shaders use legacy `gl_ModelViewProjectionMatrix` / `gl_Normal` built-ins; port the
  *math* into the grapher's own core-profile shader with explicit `uniform`/`in` attributes
  (match whatever GL version the base grapher settles on).

## Open questions

1. **Per-vertex vs analytic normals** — compute normals by averaging adjacent triangle faces, or
   analytically from `∂f/∂x, ∂f/∂y` of the authored function? (Analytic is cleaner for smooth
   math surfaces; face-averaging is more general. Lean analytic given the inputs are known
   functions — confirm.)
2. **One light or several?** v4's `3lights` shader does three. Start with **one** directional
   light (simplest, clearest highlight), add more only if you want it — OK?
3. **Material controls** — expose shininess / light direction / colours in the menubar, or
   hard-code sensible defaults in source (consistent with "functions are authored, not typed at
   runtime")? Recommendation: a couple of menubar sliders for light dir + shininess, since those
   are *view*-like, not function definitions.
