# Separate data generation from rendering in SuperBible v4 ports

**Status:** in-progress — Phase 1 done (sphere builder + atom/atom2/solar). Bill to spot-check rendering; then sphereworld family next.

## Progress
- 2026-05-28: Created `ports/openglsuperbiblev4/_primitives.py` (lightweight,
  `math` + `OpenGL.GL` only — no imgui, so minimal demos stay minimal).
  `build_sphere(radius, slices, stacks, *, swap_winding=False)` precomputes the
  per-band vertices; `draw_mesh(mesh, *, textured=False)` replays them via the
  same immediate-mode `glBegin`/`glNormal`/`glTexCoord`/`glVertex` calls.
  (Name: Bill picked `draw_mesh` over `replay`, matching the `draw_*` convention.)
- 2026-05-28: Converted chapt04/atom, chapt04/atom2 (`swap_winding=False`),
  chapt04/solar (`swap_winding=True`). Verified: an emission-equivalence test
  (stubbing `OpenGL.GL`) proves `build_sphere`+`draw_mesh` emit a BYTE-IDENTICAL
  GL call sequence to each demo's original `draw_solid_sphere` (990 / 2142 calls
  per sphere). `py_compile` clean; `_primitives.py` ruff-clean; demos carry only
  the pre-existing `I001` sibling-import style (same as chapt11/thunderbird).
  Cannot run a display here, so Bill should visually confirm these 3 render
  identically before the pattern propagates to ~30 more files.
- NOTE discovered 2026-05-28: `_common.py` exists but NO demo imports it yet —
  the ports UX-pass menubar/camera wiring is not in master (the CLAUDE.md
  "Active plans" section is stale on this). `_primitives.py` is the first
  actually-imported shared module in the ports tree.
**Started:** 2026-05-28

## Goal

Audit `ports/openglsuperbiblev4/` to find demos that mix *data generation*
(building vertex/normal/index arrays, procedural meshes, image buffers) with
*data rendering* (per-frame draw calls), quantify how many do this, and — if it
makes pedagogical and practical sense — produce a plan to separate the two so
generation happens once at setup and rendering just replays prepared data.

## Audit results (2026-05-28)

Method: 5 parallel agents read every `.py` demo across chapt01–22 and classified
each by data source, when generation runs (setup-once vs per-frame), and a
verdict. ~94 real demos (+6 stubs).

| Verdict | Count | Meaning |
|---|---:|---|
| **MIXED-HEAVY** | **47** | Nontrivial geometry/image data regenerated *every frame* in the render path. Prime separation candidates. |
| MIXED-TRIVIAL | 29 | Only a handful of hardcoded verts inlined in the draw (glRectf, a literal cube/jet/quad). Fusion is harmless. |
| ALREADY-SEPARATED | 12 | Built once at setup → display list / VBO / vertex array / static image, render just draws. |
| GLU/DRIVER | 6 | Geometry made by `gluSphere`/`gluNurbs*`/tessellator — generation lives in the driver. |
| STUB | 6 | Win32 MFC / Apple Carbon-Cocoa / OpenGL ES — no portable port. |

Per-range MIXED-HEAVY: ch01–04 = 11 · ch05–09 = 17 · ch10–13 = 5 · ch14–18 = 13 · ch19–22 = 1.

### The dominant pattern (this is the whole story)

Almost every MIXED-HEAVY demo is fused by the **same root cause**: hand-written
immediate-mode primitive generators — `draw_solid_sphere`, `draw_torus`,
`draw_solid_cone`, `draw_ground` (and an octahedron) built from `sin`/`cos`
loops + `glBegin`/`glEnd` — are **copy-pasted across ~30+ demos and re-run inside
the per-frame `render_scene`**. No demo in ch01–09 or ch14–18 uses GLU quadrics;
they all reimplement the tessellation by hand and rebuild it every frame.

Heavy clusters:
- **`sphereworld` family** (ch04, ch05, ch06, ch06/fogged, ch06/multisample,
  ch06/reflection, ch06/motionblur, ch08, ch09): 30–50 spheres + a torus +
  ground grid tessellated every frame, several drawn a 2nd time for shadows.
  Sphere *positions* are correctly generated once; only the tessellation is
  per-frame.
- **ch14–18 shader demos** (shadowmap, shaders, vertexshaders, lighting,
  fragmentshaders, imageproc, proctex, bumpmap, fbo*, hdrbloom): same shared
  primitive set rebuilt per frame. Shaders/textures are setup-once; geometry is
  not. `fboenvmap` regenerates the scene **7×/frame** (6 cube faces + main).
- **`chapt13/occquery`** — worst case: up to 27 spheres at 100×100
  (~540k tris) regenerated via Python `sin`/`cos` loops every frame; the file's
  own comment notes single-digit fps. This is the proof that the immediate-mode
  rebuild is the real bottleneck.
- **`chapt04/transform` + `transformgl`** — torus regenerated each frame, and
  `transform.py` also does per-vertex CPU matrix math inline.
- **`chapt11/thundergl`** — re-emits the full jet mesh in immediate mode every
  frame, while its **siblings already show the fix**: `thunderbird` (display
  lists) and `vbo` (VBOs) bake the identical mesh once.
- **Image-pipeline**: `chapt07/imaging` (numpy convolution + histogram per
  frame); fbo/hdr post-process passes.

### The separated pattern already exists in-tree (this is key)

The "how" is already demonstrated by the ALREADY-SEPARATED demos, using
techniques the **book itself teaches**:
- Display lists: `chapt11/thunderbird`, `chapt11/sphereworld`,
  `chapt19/SphereWorld32` (build the mesh once in `setup_rc`, `glCallList` each frame).
- VBOs: `chapt11/vbo`. Vertex arrays + `glDrawElements`: `chapt11/cubedx`.
  Vertex arrays: `chapt11/starrynight`.
- Setup-once images: `chapt07/bitmaps`, `chapt07/imageload`, `chapt18/texfloat`.

### Genuinely dynamic (can't just bake — geometry changes per frame)
- `chapt17/proctex`, `chapt18/hdrbloom` — keyboard-adjustable tessellation.
- `chapt16/vertexblend` — live skinning weights from elbow/influence state.
- `chapt04/transform` — per-vertex CPU transform is the lesson.
- `chapt10/florida` — rebuilds a `gluNewTess` every frame.
- `chapt07/imaging` — the numpy image op *is* the per-frame work.

## Plan — one combined phase (decided with Bill 2026-05-28)

Approach (Bill's words): if a demo regenerates the *same exact* geometry every
frame via loops, precompute it into an array once and just iterate the array.
**No display lists or VBOs** unless the C++ source already uses them — so the
rendering mechanism stays immediate-mode `glBegin`/`glVertex`, only *when the
`sin`/`cos` runs* changes. Extraction + precompute happen together in one pass
(the shared generator IS the precompute step). occquery is explicitly left as-is.

Duplication confirmed by grep (2026-05-28): `draw_solid_sphere` ×30,
`draw_torus` ×23, `draw_solid_cone` ×11, `draw_ground` ×11,
`draw_solid_octahedron` ×4.

- [x] **Audit** (done, above).
- [ ] **Add shared geometry builders to the ports' shared module** (`_common.py`,
      or a sibling `_primitives.py` — TBD). Each builder runs the tessellation
      once and *returns* arrays of position + normal + texcoord. Signatures
      unify the common cases: `build_sphere(radius, slices, stacks)`,
      `build_torus(major, minor, n_major, n_minor)`,
      `build_cone(base, height, slices)`, `build_ground()`,
      `build_octahedron()`.
- [ ] **Convert each static-geometry demo:** call the builder once at setup,
      store the array; the per-frame draw iterates the stored array emitting the
      same `glBegin`/`glNormal`/`glTexCoord`/`glVertex` calls it does now. Demos
      emit only the attributes they use (plain-lit spheres skip texcoords;
      textured ones don't). Targets: atom, atom2, solar, all sphereworld clones
      (ch04/05/06/08/09 + fogged/multisample/reflection/motionblur), spot,
      cubemap, multitexture, texgen, the ch14–18 primitive scenes (shadowmap,
      shaders, vertexshaders, lighting, fragmentshaders, imageproc, fbo*),
      thundergl.
- [ ] **Do NOT merge these variants — leave per-demo:** `chapt17/bumpmap`
      `draw_torus` (computes TBN tangent basis), `chapt04/transform` `draw_torus`
      (per-vertex CPU matrix math = the lesson), `chapt12/select` `draw_torus`
      (2-arg), `chapt05/spot` cone (extra `stacks` param — give the builder an
      optional `stacks` or keep local).
- [ ] **Dynamic tess (precompute + dirty-flag, not every frame):**
      `chapt17/proctex`, `chapt18/hdrbloom` rebuild on the tess slider only;
      `chapt16/vertexblend` (live skinning) and `chapt07/imaging` (numpy op is
      the work) stay as-is.
- [ ] **Leave alone:** MIXED-TRIVIAL immediate-mode *teaching* demos (ch02–04
      lines/points/triangle/glrect/bounce, literal cube/jet/quad); ALREADY-
      SEPARATED, GLU/DRIVER, STUB demos; and **occquery** (Bill: leave as-is).

Overlaps the src/-side
[`../plans/extract-duplicated-demo-helpers.md`](../plans/extract-duplicated-demo-helpers.md).

## Notes / decisions
- **DECIDED 2026-05-28 (Bill):** no display lists (or VBOs) unless the C++ source
  already uses them. The demos that already use display lists (ch11 `thunderbird`,
  ch11 `sphereworld`, ch19 `SphereWorld32`) are faithful to their source and keep
  them; no NEW ones get introduced. → Separation = "precompute arrays at setup,
  replay via immediate mode" (Phase 2), not list/VBO baking.
- Faithfulness vs. performance: the C++ SuperBible regenerates via GLTools each
  frame, but C++ loops are ~free where Python's are not. Moving only the trig to
  setup (keeping immediate-mode rendering) is the minimal-deviation win.
- `_common.py` already exists as the ports' shared-helper module (added in the
  ports UX pass) — natural home for the extracted generators.

## Open questions (resolved 2026-05-28)
- ✅ Replay mechanism: precompute arrays at setup, iterate them via immediate
  mode each frame. Rendering mechanism unchanged.
- ✅ occquery: leave as-is.
- ✅ Granularity: one combined phase (extract + precompute together).
- Minor, my call unless Bill objects: builders live in `_common.py` vs a new
  `_primitives.py`. Leaning `_common.py` (established shared-helper home).
