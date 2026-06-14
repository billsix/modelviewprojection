# Separate data generation from rendering in SuperBible v4 ports

**Status:** complete
**Completed:** 2026-05-29

Summary: Phase 1 (sphere builder + atom/atom2/solar), the
sphereworld family (9/9), the remaining sphere/torus users (chapt05/shadow, chapt09
cubemap/texgen/multitexture), the cone demos (chapt05/spot, chapt10/axes3d), AND the
ch14–18 shader scenes (9 demos). reflection verified by Bill.
chapt11/thundergl handled (Phase 6); chapt17/proctex + chapt18/hdrbloom done via dirty-flag
(Phase 7). **CONVERSION WORK COMPLETE** — a tree-wide grep confirms the only demos still
defining draw_solid_sphere/draw_torus/draw_solid_cone are the intended leave-alone set
(chapt04/transform+transformgl, chapt11/sphereworld [display-list], chapt12/select [2-arg torus],
chapt13/occquery, chapt17/bumpmap [TBN]). Remaining: **Bill's visual verification** of the
converted demos (only reflection confirmed so far) and a few open bug/UX tasks
([[cubemap-reflection-static]], [[shadowmap-depth-discrimination]], [[ports-render-options-to-imgui]]).
NOTE: `build_octahedron` was NOT created (see Phase 5 note). Archived 2026-05-29 at Bill's
request; his visual spot-checks were completed 2026-05-29 (see "Remaining before archive" below).

## Remaining before archive

The refactor itself is **done** — no more demos to convert, everything emission-verified
byte-identical, leave-alone set confirmed by grep. What's left is not coding on this task:

1. **Bill's visual spot-checks** of the converted demos (no display in-container; I can't do this).
   Confirmed so far: `reflection`. Recommended quick coverage: one from each cluster — an
   atom/solar, a sphereworld (e.g. ch06), a textured one (ch08/09 or cubemap/texgen), spot
   (cone + 3 tess levels), axes3d (cone+cylinder+disk), one shader scene (lighting), and
   proctex (UP/DOWN changes tessellation).
2. **Two converted demos can't be visually checked until pre-existing (non-extraction) bugs are
   fixed** — both tracked as their own tasks now, NOT part of this one:
   - `chapt06/motionblur` — `glAccum` has no accumulation buffer on Bill's Mesa (environmental;
     auto-memory `env-mvp-opengl-accum-buffer`). The converted sphere ran a full frame before the
     crash, so the geometry is fine; only the accum technique is blocked.
   - `chapt18/hdrbloom` — startup crash from a 1-byte after-glow PBO → [[hdrbloom-pbo-sizing-crash]].
3. **Unrelated follow-ups** discovered alongside this work (separate tasks, not blockers for
   archiving): [[cubemap-reflection-static]], [[shadowmap-depth-discrimination]],
   [[ports-render-options-to-imgui]].

**To close:** Bill commits the conversions, spot-checks per (1), then `/archive-task
extract-data-generation`. The bugs in (2)/(3) live on as their own tasks.

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
- 2026-05-28 (Phase 2): Added `build_torus(major,minor,n_major,n_minor)` and
  `build_ground(extent,step,y)` to `_primitives.py` (equivalence-verified: torus
  is an exact byte-match to the originals; ground positions match with all-up
  normals). Fully converted **chapt05/sphereworld** — sphere(s)+torus+ground all
  precomputed at import, replayed via `draw_mesh` in `draw_inhabitants`/
  `render_scene` (replayed twice/frame: shadow pass + lit pass). Bill to verify.
  Remaining sphereworld family: ch06/sphereworld, ch06/fogged, ch06/multisample
  (same plain-grid pattern); then reflection/motionblur (checkerboard ground has
  per-vertex color — needs handling), ch08/09 (textured torus+ground), ch04
  (GL_LINES ground + no-normal torus, likely unlit). Variant analysis showed the
  3 sphere "variants" are really 1 (math-identical; ch08/09 just adds the
  texcoord my builder already computes); torus has a no-normal outlier (ch04).
- 2026-05-28 (Phase 2 cont.): Converted the plain-grid trio — **chapt06/sphereworld**
  (spheres 21×11), **chapt06/fogged** and **chapt06/multisample** (spheres 17×9) —
  all sphere+torus+ground now precomputed + `draw_mesh`. compile-clean; no leftover
  draw_* refs; lint only the accepted I001 + pre-existing S311. 4 of the sphereworld
  family done (ch05 + these 3). Remaining family: reflection/motionblur (checkerboard
  ground w/ per-vertex color — `build_ground` doesn't cover it), ch08/09 (textured),
  ch04 (GL_LINES + no-normal torus, unlit).
- 2026-05-28 (Phase 2 textured): Converted **chapt08/sphereworld** (spheres 21×11)
  and **chapt09/sphereworld** (17×9). Added `tex_step` param to `build_ground`
  (default 0.0 = plain grid, unchanged for the 4 earlier demos; >0 = s/t-stepped
  textured grid). Sphere/torus use `draw_mesh(..., textured=True)`; `draw_ground`
  kept as a slim fn that does the `glBindTexture`/wrap-mode (per-frame state) then
  `draw_mesh(GROUND, textured=True)`. Equivalence-verified: textured sphere & ground
  EXACT; torus within 8.88e-16 (build_torus uses `a0+major_step` matching the ch05
  family; ch08/09 originals used `(i+1)*major_step` — mathematically identical,
  ≤1 ULP, visually irrelevant). 6 of 9 family demos done. Remaining: reflection +
  motionblur (checkerboard ground, per-vertex color), ch04 (GL_LINES + no-normal torus).
- 2026-05-28 (Phase 2 final — sphereworld family complete, 9/9): Converted the last
  three. Added `normals=False` to `draw_mesh` (skips `glNormal3f`, parallel to the
  `textured` flag) for unlit demos whose original generator emitted no normals.
  **chapt06/reflection** — sphere(0.1,17,9)+torus(0.35,0.15,61,37) → builders+`draw_mesh`.
  **chapt06/motionblur** — sphere(0.1,17,9) → builder (no torus); also dropped its now-unused
  `import math`. **chapt04/sphereworld** — sphere(0.1,13,26) (both the 50-field and the
  orbiting one) + torus(0.35,0.15,40,20) via `draw_mesh(TORUS, normals=False)`; this demo
  renders wireframe with lighting off (`glPolygonMode(GL_LINE)`).
  DECIDED (my call, per Bill's "whatever you think"): the **non-trig grounds stay local** —
  reflection/motionblur keep their checkerboard `draw_ground` (per-vertex `glColor4f`, only a
  `bounce%2` parity, no `sin`/`cos` to hoist) and ch04 keeps its `GL_LINES` line-grid ground
  (different primitive, also no trig). The trig (the whole point of the task) lives in the
  sphere/torus, which are now precomputed. Equivalence-verified by GL-stub recorder:
  reflection/motionblur/ch04 spheres BYTE-IDENTICAL; reflection torus within 8.88e-16 (same
  `(i+1)` vs `a0+step` ≤1-ULP as ch08/09); ch04 torus BYTE-IDENTICAL (it already used
  `a0+step`, and `normals=False` matches its no-normal emission). py_compile clean; ruff shows
  only the accepted I001 sibling-import + pre-existing S311. Bill to visually confirm the 3.
- 2026-05-29 (verification): Bill ran **chapt06/reflection** — renders correctly. ✅
  **chapt06/motionblur** crashes at `glAccum(GL_LOAD)` (GLError 1282) — this is the
  pre-existing accumulation-buffer limitation the file's header already warns about
  (Mesa gives no accum buffer), NOT the geometry change: `draw_mesh(SPHERE)` ran a full
  frame before the crash, and the commit didn't touch the `glAccum`/`render_scene` path.
  OPEN: whether to add a graceful no-blur fallback (gate on `glGetIntegerv(GL_ACCUM_RED_BITS)`)
  — left as-is for now (faithfulness tradeoff, Bill's call). chapt04/sphereworld not yet
  spot-checked. Env limitation recorded in auto-memory.
- 2026-05-29 (Phase 3 — remaining sphere/torus users, no new builder): Converted the
  four non-sphereworld demos that reuse the existing sphere/torus builders.
  **chapt05/shadow** — the only trig generator was the yellow light-marker
  `draw_solid_sphere(5.0,10,10)` (the jet is a hardcoded literal mesh, left as-is) →
  `build_sphere` + `draw_mesh`; dropped now-unused `import math`. **chapt09/cubemap** —
  reflective `sphere(0.75,41,41)`, no stored texcoords (cube-map texgen makes them) →
  `build_sphere` + `draw_mesh`. **chapt09/texgen** — `torus(0.35,0.15,61,37)`, no stored
  texcoords (texgen makes them) → `build_torus` + `draw_mesh`; dropped `import math`.
  **chapt09/multitexture** — `sphere(0.75,41,41)` puts its texcoord on TEXTURE0 via
  `glMultiTexCoord2f`, which `draw_mesh` (emits `glTexCoord2f`) can't express, so kept a
  slim local `draw_sphere_multitex()` that replays the precomputed `build_sphere` mesh with
  `glMultiTexCoord2f` (same slim-wrapper pattern as ch08/09's textured `draw_ground`).
  Equivalence-verified (GL-stub recorder): shadow + cubemap spheres BYTE-IDENTICAL;
  multitexture multitex sphere BYTE-IDENTICAL; texgen torus within 8.88e-16 (the same
  `(i+1)` vs `a0+step` ≤1-ULP as ch08/09/reflection). py_compile clean; no leftover
  draw_solid_sphere/draw_torus refs. Lint: accepted I001 sibling-import on all four, plus
  PRE-EXISTING E702 (semicolon `glTexCoord;glVertex` lines) in cubemap's `draw_skybox` (24)
  and texgen's hardcoded quad (4) — both in untouched code, not from this change.
  Remaining trig generators outside the leave-alone list: cone (chapt05/spot 4-arg w/ stacks,
  chapt10/axes3d 3-arg) and octahedron need NEW builders; plus the ch14–18 shader scenes and
  thundergl. Next phase: add `build_cone` (optional `stacks`) + `build_octahedron`, convert spot/axes3d.
- 2026-05-29 (Phase 4 — cones: chapt05/spot + chapt10/axes3d): The "one build_cone with an
  optional stacks param" idea from the plan was WRONG once I read the code — there are THREE
  distinct cone tessellations: (a) spot's 4-arg cone = multi-stack GL_QUAD_STRIP with a
  per-vertex *slant* normal + a base cap; (b) axes3d's 3-arg cone = a flat-normal GL_TRIANGLE_FAN
  body + a reversed base disk; (c) the ch14–18 shader-scene 3-arg cone = the SAME fan body as
  (b) but with NO disk. So `build_cone(base,height,slices)` now builds just the shared **fan
  body** (apex + base ring, one flat +Z normal) — serves axes3d's body now and all 8 shader
  scenes next phase. Added `draw_mesh(flat=True)`: emits one `glNormal3f` per band (from the
  band's first vertex) then the vertices, matching how the fan/disk originals set a single
  normal for the whole fan. spot's slant cone + cap and axes3d's base disk are demo-specific,
  so they're precomputed LOCALLY in those files (the cone-cap/disk replay via draw_mesh(flat);
  the slant cone via the default per-vertex draw_mesh). axes3d's cylinder rod emits ONE normal
  shared by each base+top vertex *pair* (neither draw_mesh mode fits), so axes3d keeps a tiny
  `_draw_cylinder()` replaying precomputed rings. spot's spheres ALL use swap_winding=True; its
  blue sphere has 3 imgui-selectable tessellations (7/15/50) → precomputed all three, no
  dirty-flag needed. Equivalence-verified (GL-stub recorder): EVERY piece BYTE-IDENTICAL
  (spot cone/cap/3 spheres/bulb; axes3d fan/disk/cylinder/sphere). py_compile clean; ruff only
  the accepted I001. **DEVIATED from plan: did NOT add `build_octahedron`** — its only callers
  are 4 ch14/ch18 shader scenes (none in this phase), so adding it now would be an unused
  builder; it lands with the shader-scene phase where its callers live.
- 2026-05-29 (Phase 5 — ch14–18 shader scenes, 9 demos): Converted shadowmap, shaders,
  vertexshaders, fragmentshaders, imageproc, lighting, fbodrawbuffers, fboenvmap, fboshadowmap.
  A survey confirmed all 9 copy-paste the SAME sphere/cone/torus generators (sphere & cone
  BYTE-IDENTICAL to the existing builders; torus the usual ≤1-ULP `(i+1)` variant). Params:
  sphere (25,50,50)+(25,32,32)+(20,32,32), cone (25,50,50), torus (16,8,50,50) — verified
  byte-identical (torus within 2.04e-14). `import math` dropped from the 7 that no longer need
  it (kept in shadowmap + fboshadowmap, which use it for shadow-FOV math). **DECISION: did NOT
  create `build_octahedron`, and dropped it from the plan entirely.** The octahedron (and the
  cube) are HARDCODED literal vertices with NO trig — MIXED-TRIVIAL, not a per-frame-trig case,
  so precomputing buys nothing; worse, the octahedron has 3 inconsistent variants across the 4
  files (per-vertex-normal with two different face lists, plus a per-face cross-product variant),
  so a shared builder couldn't even be byte-faithful. Cube + octahedron left exactly as-is.
  Verified: all 9 py_compile clean, ZERO leftover draw_solid_sphere/draw_torus/draw_solid_cone
  refs, no F-code lint (no undefined math, no unused imports); remaining lint is all pre-existing
  (E702/E701 semicolon skybox/octa/cube lines, T201 prints, E501, S311) + accepted I001. (Edits
  by a sub-agent against the exact byte-identical def block; I verified compile/refs/imports/diffs.)
- 2026-05-29 (Phase 6 — chapt11/thundergl): Investigated and found it was ALREADY
  data/render-separated, contrary to the audit's MIXED-HEAVY tag. The jet mesh
  (vertices/normals/face indices for body + glass) is parsed ONCE from body.cpp/glass.cpp by
  `_thunderbird_data.load_model` (which caches by directory) — there is NO per-frame trig;
  `draw_body`/`draw_glass` just index static numpy arrays and emit glNormal3fv/glVertex3fv. That
  immediate-mode replay of precomputed data IS this task's target state. The siblings thunderbird
  (display list) and vbo (VBO) "bake" it, but Bill's rule forbids introducing NEW display
  lists/VBOs, so those aren't options here. The ONLY in-scope issue: `model = load_model(PWD)`
  was called inside `render_scene` (cached, so parse-once, but the call sat in the render path).
  Fix: hoisted it to a module global `jet_model` loaded in `setup_rc`; `render_scene` now reads
  the global. Behavior-identical (setup runs before the loop; load_model was already cached).
  py_compile clean; ruff = accepted I001 + a PRE-EXISTING `F401 'math' imported but unused`
  (confirmed present in HEAD before this change — left as-is, not my cleanup to make; flag to Bill).
- 2026-05-29 (Phase 7 — dynamic-tess: chapt17/proctex + chapt18/hdrbloom): Both draw a single
  `draw_solid_sphere(50.0, tess, tess)` (standard, default winding, NO texcoords — the shaders
  generate the surface from position/normal) where `tess` is changed live by the UP/DOWN keys
  (+5 / −5, min 5). Applied the dirty-flag pattern: a module-level `sphere_mesh` plus a
  `rebuild_sphere()` that calls `build_sphere(50.0, tess, tess)` — invoked ONCE at import and
  again ONLY in the UP/DOWN key branches, so the sin/cos runs on the keypress, never per-frame.
  `render` replays via `draw_mesh(sphere_mesh)`. Dropped now-unused `import math` from both.
  Equivalence-verified BYTE-IDENTICAL at tess 75 (initial), 80 (changed), and 5 (min). py_compile
  clean; no leftover refs; no F-code lint (math removal clean); remaining lint all pre-existing
  (E702/E701/E501/T201 semicolon/print lines, one B007) + accepted I001.
- 2026-05-29 (completeness sweep): tree-wide grep for remaining generator DEFINITIONS returns only
  the leave-alone set (above) — confirming every in-scope trig demo is converted.
- 2026-05-29 (verification side-findings — NOT extraction bugs): Bill running the converted demos
  surfaced two PRE-EXISTING runtime bugs unrelated to this refactor (my diffs don't touch their
  code): (1) chapt06/motionblur — `glAccum` GLError 1282 (no accumulation buffer on Mesa;
  environmental, see [[env-mvp-opengl-accum-buffer]]); (2) chapt18/hdrbloom — `glTexImage2D`
  GLError 1282 in `final_pass`: the after-glow PBO is allocated 1 byte in `setup_rc` (line ~299)
  and only resized in `change_size` when the size *changes* from the initial, so at the default
  512×512 it's never grown; `final_pass` then reads 512×512×3 bytes from a 1-byte PBO. A real
  fixable port bug (size the PBO properly at setup), but out of scope for THIS task — should be its
  own task. Both block Bill's visual check of those two demos' converted spheres.
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
[`../tasks/extract-duplicated-demo-helpers.md`](../tasks/extract-duplicated-demo-helpers.md).

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
