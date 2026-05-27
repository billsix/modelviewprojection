# Note: "upload" vs "set" for uniforms — terminology research

**Recorded 2026-05-02.** Task #42. Action taken: rename
`upload_mvp` → `set_mvp_uniforms` and `_upload_frustum` →
`_set_frustum_uniforms` in `mvpVisualization/`.  See "Action" section
at the bottom for the full diff list.

**In master 2026-05-27:** this rename arrived with the `mvpVisualization/` pull
(it was interleaved in those files with the VAO/VBO-separation refactor). Kept
here as the durable terminology rationale.

## Question

Is "upload" the right verb for `glUniform*` calls, or is something
else (set / write / specify / send / assign / update) more accurate
for the curriculum?

## Answer

**Use "set" for uniforms.** Reserve "upload" for `glBufferData` /
`glBufferSubData` and texture data transfers — operations that
actually move bytes from CPU memory into GPU-resident memory.

## Why

The two operations are conceptually different even though they look
similar at the call site.

### `glBufferData(...)` and friends — *upload* is correct

These move raw bytes into a GL buffer object that lives in GPU
memory.  On a discrete GPU, this typically involves a PCIe transfer.
The buffer object has a name (an integer id), the bytes are stored
at server side, and the CPU pointer is no longer authoritative.
"Upload" matches the cost model and matches Khronos terminology
(the spec literally talks about "uploading" pixel data via PBOs).

### `glUniform*(...)` — *set* is correct, "upload" is misleading

`glUniform*` modifies the **default uniform block** of the currently
bound program object.  This is *program state*, not GPU memory.  In
the spec's words (registry.khronos.org/OpenGL-Refpages/gl4/html/glUniform.xhtml):

> "**glUniform — Specify the value of a uniform variable for the
> current program object.**"

The verb in the spec is "specify".  Internally drivers usually
batch these into a constant buffer attached to the next draw call —
but the *call itself* doesn't transfer to GPU memory.  It's
effectively `program->uniforms[location] = value`.

Calling that "upload" overstates the cost and conflates two
different concepts:

| Operation       | Spec verb    | Cost model                    |
|-----------------|--------------|-------------------------------|
| `glBufferData`  | uploads      | PCIe transfer (expensive)     |
| `glTexImage2D`  | uploads      | PCIe transfer (expensive)     |
| `glUniform*`    | specifies / sets | driver-side state update (cheap, batched) |

For `GL_UNIFORM_BUFFER` (UBOs) — *those* are buffer objects, so
"upload UBO data" via `glBufferSubData` is again correct.  But the
default uniform block, accessed via `glUniform*`, is not a buffer.

## Survey of authoritative sources

- **Khronos refpages** (`glUniform`): "**Specify** the value of a
  uniform variable."  Never "upload".
- **OpenGL Programming Guide (Red Book), 8th ed.** uses **"set"** /
  **"associate values with"** for uniforms.  Reserves "upload" for
  buffer data and textures.
- **OpenGL SuperBible, 7th ed.** (Sellers/Wright/Haemel/Lipchak):
  "we use one of the `glUniform*()` functions to **set** its value"
  (chapter 5).  Uses "upload" in the same chapter for `glBufferData`.
- **NVIDIA / AMD developer docs** typically write "set the uniform"
  or "update the uniform value".
- **WebGL 2 spec**: same as desktop — `uniform4f` "sets the value of
  the uniform variable."

So **set** (or **specify**, more formally) is the standard.  No
authoritative source treats `glUniform*` as an "upload."

## Why the curriculum should follow

The MVP curriculum already had the right verb (`set_mvp_uniforms`)
in modern demos 22, 22a, 23, 24.  The visualizer side
(`mvpVisualization/_pipeline.py` + 6 demos) was the one place still
using `upload_mvp` / `_upload_frustum` — exactly the kind of
inconsistency that confuses students jumping between a curriculum
demo and its matching visualizer.

If a student walks into class having read the SuperBible (or the
spec, or NVIDIA's blog), they have "set" in their head.  Having a
function called `upload_mvp` makes them wonder whether something
materially different is happening — when in fact the call is
`glUniformMatrix4fv` three times in a row.

## Naming choice: `set_uniforms`, not `set_mvp_uniforms`

Bill's call (2026-05-02) after the first pass was to drop the `mvp`
qualifier entirely:

- The visualizer's function set M, V, P (three uniforms).
- The demo22 function sets MVP + model, plus optionally
  `shadowMatrix` when `_using_shadow_map` is on -- so the `mvp`
  prefix was already a bit of a lie.
- All these functions answer the same question: "set the per-frame
  uniforms this draw needs."  The function name should reflect that
  intent, not the specific list, since the list will keep changing
  as new demos add normals/lights/shadows.

So the final name everywhere is **`set_uniforms`**.  Each demo's
`set_uniforms` is allowed to know what its own pipeline needs --
just like `draw_floor` knows what the floor needs.

## What stays "upload"

Only operations that actually move bytes to GPU memory:

- `make_vbo(data)` — "Allocate a VBO and upload `data`."  ✓ stays.
- demo21/22's VBO docstrings — "upload time", "one upload, two
  VAOs", etc.  ✓ stay.
- demo23's "upload time so the jet fits..."  ✓ stays.

## Action taken

Two passes in this session.

**Pass 1** (visualizer-side `upload_mvp` → `set_mvp_uniforms`):

| File | Change |
|---|---|
| `mvpVisualization/_pipeline.py` | `def upload_mvp` → `def set_mvp_uniforms`; comments updated |
| `mvpVisualization/coordinatesystems/coordinatesystems.py` | 4× call-site renames |
| `mvpVisualization/model/model.py` | 4× call-site renames |
| `mvpVisualization/modelview2d/modelview2d.py` | 5× `upload_mvp` + `_upload_frustum` → `_set_frustum_uniforms` (3×) |
| `mvpVisualization/modelvieworthoprojection/modelvieworthoprojection.py` | 5× `upload_mvp` renames + comment "uniform uploaders" → "uniform setters" |
| `mvpVisualization/modelviewperspectiveprojection/modelviewperspectiveprojection.py` | 5× `upload_mvp` + comment update |
| `mvpVisualization/pushmatrix/pushmatrix.py` | 4× call-site renames |

**Pass 2** (`set_mvp_uniforms` → `set_uniforms` everywhere):

| File | Change |
|---|---|
| `mvpVisualization/_pipeline.py` | `def set_mvp_uniforms` → `def set_uniforms` |
| 6 visualizer demos | call-site renames (same files as pass 1) |
| `src/modelviewprojection/demo22/demo22.py` | `def set_mvp_uniforms` → `def set_uniforms` + 5× call-site renames |
| `src/modelviewprojection/demo22a/demo22a.py` | rename function + call sites |
| `src/modelviewprojection/demo23/demo23.py` | rename function + call sites |
| `src/modelviewprojection/demo24/demo24.py` | rename function + call sites |

No behavior change in either pass.  Pure rename.

`_set_frustum_uniforms` (the modelview2d-only helper for FOV/aspect/
near/far) stays as-is — `set_uniforms` is reserved for the M/V/P-and-
friends call common to every demo, and the frustum helper is a
private supplement.
