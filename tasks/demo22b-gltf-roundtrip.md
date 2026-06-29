# demo22b — the demo22 scene, round-tripped through a glTF file

**Status:** proposed — needs go-ahead before any code is written
**Created:** 2026-06-29
**Area:** `src/modelviewprojection/demos/demo22b/` (new), `requirements.txt`, Dockerfile/Makefile dep-sync, book (later)

## Goal

A variant of demo22 that draws the **identical scene and pixels**, except the
"data that gets drawn" (geometry, materials, textures, the light, node
transforms) takes a round-trip through a **glTF 2.0 `.glb` file**:

1. At demo startup, a **helper script** (`export_scene.py`) builds the scene data
   and writes `scene.glb`.
2. The **main program** (`demo22b.py`) then *loads* `scene.glb`, rebuilds its
   VAOs/VBOs/textures from the decoded glTF, and renders with **full demo22
   parity** — all 5 stages, both shadow algorithms, the light sliders, the light
   marker, and the walk-around camera.

The teaching point: a real asset format encodes exactly the *data drawn* and
**nothing else** — shaders, render algorithms (planar shadow, shadow map), stage
toggles, and interaction all stay in app code. The round-trip makes the
data/algorithm boundary concrete.

## Decisions (from investigation + Bill, 2026-06-29)

- **Library: `pygltflib`** (pure-Python, no native deps) for both write and read.
  Chosen over a hand-rolled reader/writer.
- **Scope: full demo22 parity** — keep all 5 stages (wireframe → solid → lit →
  shadow → textured), both shadow techniques (planar + shadow-map), the az/el/
  radius sliders, the cone+bulb light marker, and the camera. Only the
  geometry/materials/textures/light come from the glTF.
- **Placement: `demo22b`** — sits beside demo22 as a direct A/B variant.
  (demo23 = litjet, demo24 = sphereworld capstone are already taken.)
- **Baked defaults (my call unless you object):**
  - **`.glb`** single self-contained binary, images embedded — not `.gltf`+`.bin`.
  - **Node transforms as glTF 4×4 matrices, not TRS/quaternions.** The course
    never teaches quaternions (demo22 uses Euler `rotate_x/y`; `src/` uses gacalc
    rotors); a 4×4 matrix node fits the matrix-era (demo19+) and avoids dragging
    quaternions in.
  - **Regenerate `scene.glb` every startup** (proves the round-trip live), and
    **gitignore it** as a build artifact.
  - **Textures → PNG, embedded in the glb.** glTF only permits PNG/JPEG images;
    demo22's are TGA. Convert with `imageio` (already a dep). The exporter reads
    demo22's existing `.tga` files (`../demo22/*.tga`) so the textures aren't
    duplicated on disk.

## What lives where (the data / algorithm split)

| demo22 element | glTF carries it? | How |
|---|---|---|
| cube_solid (36 verts, pos/normal/uv) | ✅ | mesh primitive, mode=TRIANGLES |
| cube_wire (24 verts, drawn `GL_LINES`) | ✅ | mesh primitive, **mode=LINES (1)** |
| floor (6 verts) | ✅ | mesh primitive, TRIANGLES |
| marker cone + bulb sphere | ✅ | two mesh primitives, unlit material |
| floor.tga, Block4/5/6.tga | ✅ | images (PNG, embedded), textures, samplers |
| flat colors / textured intent | ✅ | materials: `baseColorFactor` / `baseColorTexture`; `KHR_materials_unlit` for the marker |
| directional light (default az/el) | ✅ | `KHR_lights_punctual` directional light → loaded as the **initial** slider values |
| cube's `translate(-10,0,10)` | ✅ (optional) | node matrix — or keep in app (see stretch) |
| **5 stage toggles** | ❌ | app uniforms (`useLighting`/`useTexture`) |
| **planar-shadow matrix** | ❌ | recomputed each frame from the live light |
| **shadow-map FBO + depth pass** | ❌ | runtime two-pass technique |
| **shaders** (block.vert/frag + inline) | ❌ | glTF 2.0 carries no shaders; app supplies them |
| **sliders / camera / marker transform** | ❌ | runtime interaction (marker transform is light-dependent, can't bake) |

## Parity strategy — swap the data source, keep everything else

demo22b should keep demo22's render code essentially **verbatim** (same shaders,
same `MainPipeline`/`BlockShadowPipeline`/`ShadowDepthPipeline`/`ShadowViewPipeline`,
same stage logic, same `_make_interleaved_mesh`/`_interleaved_attribs`, same
8-float interleaved layout pinned to attribute slots 0/1/2). The **only** change:
the five `vertex_data` arrays that today come from `_build_cube_solid()` /
`_build_cube_wire_full()` / `_build_floor()` / `_build_marker_cone()` /
`_build_marker_sphere()` instead come from **decoding glTF accessors**.

Because meshes without real normals/uv (wireframe, marker) currently use
zero-filler to fill the 8-float layout, the exporter should write those zero
normal/uv accessors too — so the decoded arrays are byte-identical to the
`_build_*` outputs and the entire downstream pipeline is unchanged.

> Caveat for the per-face texturing (stage 4): demo22 binds 3 textures to 6
> face-subranges of the one cube VAO via a hardcoded offset table
> (`faces_to_draw = [(tex, 0), (tex, 6), …]`). For **parity-first**, keep the cube
> as one 36-vert primitive and keep that offset table in the app — the glTF is
> just the vertex store. (Modelling the cube as 6 primitives each with its own
> material is cleaner glTF but changes the draw structure; left as a stretch.)

## Proposed file layout

```
src/modelviewprojection/demos/demo22b/
├── demo22b.py        # run exporter at startup → load scene.glb → render (full demo22 parity)
├── export_scene.py   # helper: build meshes/materials/textures/light → scene.glb (pygltflib).
│                     #   also runnable standalone: `python export_scene.py scene.glb`
├── block.vert        # copied from demo22 (glTF carries no shaders; keep demo22b standalone)
├── block.frag        # copied from demo22
└── scene.glb         # GENERATED at runtime — gitignored
```
Textures are **not** copied here — `export_scene.py` reads `../demo22/*.tga` and
bakes PNG-converted copies into the glb.

## Implementation plan (after go-ahead)

1. **`export_scene.py`** — factor demo22's `_build_*` mesh builders into this
   module (import-shared or duplicated), then with pygltflib assemble: one buffer
   holding all interleaved vertex data + the 4 PNG image blobs; bufferViews +
   accessors (with correct `componentType`/`type`/`count`/`min`/`max`); meshes
   (cube_solid TRIANGLES, cube_wire LINES, floor, cone, bulb); materials
   (`baseColorFactor`, `baseColorTexture`, `KHR_materials_unlit` for the marker);
   images/textures/samplers; a `KHR_lights_punctual` directional light at the
   default az/el; nodes + a scene. `GLTF2.save_binary("scene.glb")`.
2. **Loader in `demo22b.py`** — `pygltflib.GLTF2().load("scene.glb")`, then a
   small decode helper that turns each accessor back into the float32 numpy
   array, reassembles the 8-float interleaved layout, and feeds
   `_make_interleaved_mesh()` exactly as demo22 does. Decode the 4 PNG images →
   `glTexImage2D` (adapt demo22's `load_texture` to take bytes/array instead of a
   path). Read the light → initial `light_az_deg`/`light_el_deg`.
3. **Render loop** — copy demo22's loop unchanged (stages, planar + shadow-map,
   marker, camera, imgui panel).
4. **Deps + repo sync** (see mvp `CLAUDE.md` "keeping Dockerfile/Makefile/deps in
   sync"): add `pygltflib` to **`requirements.txt`**. It's pure-Python with no
   native deps, so the Dockerfile's `pip install -e .` picks it up — **no distro
   package and no build-arg needed**. Add `scene.glb` (or `*.glb`) to
   `.gitignore`.
5. **Checks** — `ruff`/`ty`/`format.sh` clean. pygltflib ships partial type info;
   expect a few `# ty: ignore` at the decode boundary.

## Verification plan

- **Headless round-trip equality (no display needed, runs in the container):**
  build the 5 mesh arrays directly from the `_build_*` functions, export to a
  glb, load it back, and assert the decoded arrays are byte-identical
  (`np.array_equal`); assert each texture's decoded pixels equal the source TGA's
  (after the documented TGA→PNG conversion); assert the light direction and any
  baked node matrix round-trip. This proves the *data* is lossless without a GPU.
- **Validity:** reload the written glb with pygltflib (and, if available, the
  Khronos glTF-Validator) to confirm it's spec-conformant.
- **On-display parity (Bill verifies — per `CLAUDE.md`, GL windows aren't
  verifiable headless in the container):** demo22b should look pixel-identical to
  demo22 across all 5 stages and both shadow algorithms.

## Stretch / open questions (not blocking)

- **Per-face primitives + materials** for the cube (6 primitives, each its own
  material/texture) — cleaner glTF, lets stage 4 drop the hardcoded offset table,
  but changes the draw loop. Parity-first keeps one primitive.
- **Bake node transforms into glTF** (cube offset as a node matrix) vs keep them
  in app code. Parity-first keeps them in app; baking them is a nice extra glTF
  lesson.
- **Book chapter / curriculum framing** — if demo22b graduates from "variant" to
  taught content, it needs a `book/docs/chNN.rst`. Deferred until the demo exists
  and Bill decides it belongs in the arc.
- **A standalone `python export_scene.py scene.glb` inspection path** + dumping the
  glTF JSON for students to read — cheap to add, good teaching artifact.
