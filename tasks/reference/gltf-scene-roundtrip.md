# Round-tripping a demo scene through glTF (demo22b)

Durable notes on how the course round-trips a scene through a glTF 2.0 `.glb`
file, written when demo22b was built (2026-10-18). States what is true now; the
work record is `tasks/archive/2026/10/18/demo22b-gltf-roundtrip.md` and the code
is `src/modelviewprojection/demos/demo22b/`.

## What demo22b demonstrates

demo22b draws the demo22 scene with one thing changed: the **data drawn**
(geometry, textures, light) takes a round-trip through `scene.glb`, while the
**algorithm** (shaders, the two shadow techniques, the five stage toggles, the
camera, the per-face texture offset table) stays in app code. A real asset
format carries exactly the data and nothing else; the round-trip makes that
boundary concrete.

## Standalone, not shared with the ports

The glTF decode in `demo22b/export_scene.py` is **deliberately self-contained** —
demo22b imports nothing from the ports tree, so the course demos stand alone.
`export_scene.py` depends only on numpy / pygltflib / imageio — not the rest of
the mvp package — so it round-trips and unit-tests in isolation
(`python export_scene.py scene.glb`).

## The lossless-round-trip recipe (pygltflib)

- **Geometry**: de-interleave each mesh into three tightly-packed FLOAT accessors
  (POSITION / NORMAL / TEXCOORD_0), one bufferView each, `target=ARRAY_BUFFER`;
  re-interleave on read into the app's vertex layout. Give POSITION `min`/`max`
  (spec-required). Non-indexed matches a `glDrawArrays` demo. Because both sides
  are float32, the decoded array is **byte-identical** to the builder's output —
  assert that in a headless test (`np.array_equal`), no GPU needed.
- **Buffer**: one binary blob; 4-byte-align each segment; set
  `buffers[0].byteLength` and `gltf.set_binary_blob(blob)` before `save_binary`.
- **Textures**: glTF images must be PNG/JPEG. Convert the source TGA to PNG with
  imageio (`iio.imwrite("<bytes>", pixels, extension=".png")`) — lossless, so
  pixels survive. Embed as a bufferView image (`mimeType="image/png"`). Read back
  with `iio.imread(png_bytes, extension=".png")`.
- **Light**: `KHR_lights_punctual` directional lights have **no direction field**
  — the direction is the node's local −Z in world space. Orient the light with a
  node **4×4 matrix** (not TRS/quaternion; matches the matrix-era demos) whose +Z
  axis is "the direction toward the light"; recover it on read as the matrix's +Z
  column, then convert to azimuth/elevation. glTF matrices are column-major
  16-tuples — transpose (`reshape(4,4, order="F")`) on the way in and out.

## Gotchas settled here

- `pygltflib`'s `.name`, `.pbrMetallicRoughness`, etc. are `Optional`; ty flags
  them. Guard with `if x is not None:` (narrows the type) or an index fallback
  (`name or f"mesh_{i}"`) rather than `assert` (S-rule risk in `src`).
- A one-primitive mesh textured across several images by an app-side offset table
  (demo22's cube) can't reference all those textures through its single material.
  Parity-first keeps the offset table in the app and loads textures **by image
  name**; the unreferenced textures are glTF-Validator `UNUSED_OBJECT` at **INFO**
  severity — still spec-conformant. The clean fix is per-face primitives (stretch).
- `pygltflib` is a pure-Python dep in `requirements.txt`; a stale `make image`
  from before it was added won't have it. Rebuild the image to run demo22b.

See also: `tasks/reference/architecture-overview.md` (the demo arc),
`src/modelviewprojection/demos/demo22/demo22.py` (the parity source).
