# Separate VAO and VBO construction; default-bind a VAO at startup

**Status: complete — ported into master 2026-05-27.** Both halves landed:
the `mvpVisualization/` side (`_pipeline.py` + the viz demos) and the
`demo21.py`/`demo22.py` side were pulled from the `claudeCode` branch. (GL
verification is Bill's — not runnable in the container.) Original investigation
notes preserved below.

Plan rewritten after surveying actual code and getting
Bill's answers on the three open questions:

- **Layout description: `AttribSpec` dataclass** (tuples allowed as
  fields where reasonable, e.g. for the (size, stride, offset) bundle).
- **Default-VAO bind: inline + comment**, in every demo entry point.
  Same pattern in `_pipeline.py` for visualizations.
- **Sequencing: Move 1 in `_pipeline.py` + the visualization demos
  first**, so Bill can verify on macOS before any larger surface
  changes. Then Move 1 in demo21/22 (Linux-only validation), then
  Move 2 across the board.

## TL;DR — what the survey changed about my thinking

Bill's two stated motivations were "VAO is created for every VBO,
that's wasteful" and "the macOS visualizers wouldn't run because no
VAO was active during shader compilation." The survey (see
`Findings` below for file:line counts) shows:

- **VBO duplication is real but small.** demo21 has 4 redundant VBOs
  (paddle1 & paddle2 each have their own pos+color VBOs holding
  identical bytes). demo22 has *zero* byte duplication —
  `cube_solid_vao` is already shared across three pipelines (main lit,
  shadow-depth, shadow-map debug). `_pipeline.py` factories produce
  fresh VAO+VBO per call, but each visualization demo calls them with
  unique geometry. Net: **demo21 has the duplication; demo22 is
  already efficient.**
- **The macOS bug is real but the diagnosis was wrong.** Per Khronos
  spec + Apple's Core Profile enforcement: shader compilation
  (`glCompileShader`, `glLinkProgram`) does **not** require a VAO.
  Bill's "couldn't compile shaders" report is a misdiagnosis — the
  real failure is at `glVertexAttribPointer` /
  `glEnableVertexAttribArray` / draw calls, all of which require a
  non-zero VAO bound on macOS Core Profile (VAO 0 is prohibited).
- **The strongest concrete macOS-shape evidence is in demo22:1239–1244**,
  where the code explicitly binds `cube_solid_vao` "*to satisfy core
  profile*" before drawing a fullscreen quad whose vertices are
  hardcoded in the vertex shader. That's a workaround for not having a
  default-scratch-VAO available. With this refactor, that hack goes
  away.

So the refactor lands one big win (macOS support, plus killing the
"bind-something-just-to-satisfy-the-spec" hack) and one small win
(demo21 paddle deduplication). The "share one VBO across pipelines
with different layouts" is mostly *future capability* — current code
doesn't need it.

## What macOS requires (one-paragraph version, defensible)

> On macOS in OpenGL 3.3+ Core Profile, VAO 0 is **prohibited** — you
> cannot do anything vertex-related with the default-zero VAO. The
> calls that require a non-zero bound VAO are
> `glVertexAttribPointer`, `glEnableVertexAttribArray` /
> `glDisableVertexAttribArray`, and all `glDraw*` calls. Shader
> compilation and linking do *not* need a VAO. Apple's driver
> enforces this strictly; Mesa and NVIDIA tolerate the spec violation
> silently. The canonical fix: at startup, immediately after
> `glfw.make_context_current`, generate one VAO and bind it. Treat
> that VAO as the always-bound default; never call
> `glBindVertexArray(0)`. Code that needs a specific layout
> (`glBindVertexArray(my_vao)`) override-binds and the next bind
> takes over — there's never a moment without *some* VAO active.

## Findings (file:line)

### demo21.py — 4 VAOs, 6 VBOs, **2 byte-duplicate VBOs**

- L187–225: `make_colored_vao(pos, color)` — gens 1 VAO + 2 VBOs
  (separate position and color buffers).
- L297: `paddle1_vao = make_colored_vao(paddle_vertices, paddle1_color)`
- L299: `paddle2_vao = make_colored_vao(paddle_vertices, paddle2_color)`
  — *paddle_vertices is the same numpy array as for paddle1*. Two
  identical pos VBOs uploaded.
- L303: `square_vao = make_colored_vao(square_vertices, square_color)`
  — distinct geometry.
- L239–261: `make_ground_vao()` — 1 VAO + 1 pos VBO.

### demo22.py — 5 VAOs, 5 VBOs, **0 byte-duplicate VBOs, but one workaround**

- L672 `make_vao(vertex_data)` — creates a fresh VAO+VBO for an
  interleaved `[pos3, normal3, uv2]` array.
- L797: `cube_solid_vao` — used by **3 pipelines**: main lit
  (L1047/L1059/…), shadow-depth (L555 via `_draw_obj`), and shadow-map
  visualization (L1242 — see below). Already shared; no duplication.
- L798: `cube_wire_vao` — distinct geometry (wireframe edges).
- L821: `floor_vao` — used by main lit + shadow-depth. Already shared.
- L882: `marker_cone_vao`, L885: `marker_bulb_vao` — distinct.
- **L1239–1244** (the smoking gun for the macOS workaround):
  ```python
  # The fullscreen quad's vertices are baked into the VS, so we
  # just need any bound VAO to satisfy core profile.  Reuse the
  # cube VAO -- we ignore its attributes.
  GL.glBindVertexArray(cube_solid_vao)
  GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
  GL.glBindVertexArray(0)
  ```
  This is exactly the case the always-bound-default-VAO pattern
  cleans up.

### `mvpVisualization/_pipeline.py` — factories

- L206–250: `make_triangle_vao(positions, colors)` — 1 VAO + 2 VBOs
  per call, separate pos and color.
- L259–284: `make_lines_vao(positions)` — 1 VAO + 1 VBO per call.

### `mvpVisualization/<demo>/<demo>.py` — per-demo entry points

- All call `_p.make_triangle_vao` / `_p.make_lines_vao` — 6+ VAOs each
  with no byte duplication within a demo.
- **`modelviewperspectiveprojection.py:300–327`** — manually creates
  the frustum VAO/VBO (not via `_p`) so it can rebuild when imgui
  sliders change near/far/FOV. This is a third pattern: rebuild on
  parameter change. Worth preserving in the refactor.

### Startup ordering

In **both** demo21 and demo22, shader compilation happens *before* the
first `glBindVertexArray`. This is fine per spec (compilation needs no
VAO) but is the strongest evidence that Bill's user-reported macOS
"shader compile failed" was misdiagnosed: it cannot have been the
compile that failed. The likely actual failure is the first call to
`glVertexAttribPointer` inside `make_vao` if for any reason the
preceding `glBindVertexArray(vao)` didn't take effect on Apple's
implementation.

## Proposed refactor — three independent moves

These can land separately. Sequence them by risk (smallest → largest)
so each one validates the next.

### Move 1: Always-bound default VAO (smallest, fixes macOS)

Add **two lines** to each of `demo21.py`, `demo22.py`, and every
`mvpVisualization/<demo>/<demo>.py` (or, better, to a shared helper):

```python
_default_vao = GL.glGenVertexArrays(1)
GL.glBindVertexArray(_default_vao)
```

…immediately after `glfw.make_context_current(window)`, before any
shader compilation. Then **remove every `glBindVertexArray(0)` in the
codebase** (there are quite a few — see the survey grep). Code that
binds a specific VAO doesn't need to "unbind"; the next operation that
wants a clean slate can `glBindVertexArray(_default_vao)` explicitly.

The demo22 L1239–1244 workaround simplifies: bind the default VAO
instead of cube_solid_vao, drop the misleading comment.

**Surface area:** ~10 line additions, ~15 line deletions (the
`glBindVertexArray(0)` cleanup). No semantic change on Mesa/NVIDIA.
Unblocks macOS.

### Move 2: Separate VBO and VAO construction (the conceptual change)

Replace the `make_*_vao(data, …)` factories with two-step builders.
The layout description is a dataclass with named fields, not a raw
tuple — students should be able to read the call site without
counting positions:

```python
@dataclass(frozen=True)
class AttribSpec:
    vbo: int                # the VBO this attribute pulls from
    location: int           # shader attribute slot
    size: int               # 2/3/4 floats per vertex
    layout: tuple[int, int] # (stride_bytes, offset_bytes)


def make_vbo(data, usage=GL.GL_STATIC_DRAW) -> int:
    """Allocate a VBO and upload `data`. Touches no VAO state."""
    vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, usage)
    return vbo


def make_vao(attribs: list[AttribSpec]) -> int:
    """Build a VAO that reads each AttribSpec from its VBO."""
    vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(vao)
    for a in attribs:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, a.vbo)
        GL.glEnableVertexAttribArray(a.location)
        stride, offset = a.layout
        GL.glVertexAttribPointer(a.location, a.size, GL.GL_FLOAT, False,
                                 stride, ctypes.c_void_p(offset))
    return vao
```

The `(stride, offset)` pair stays as a tuple inside the dataclass
because the two are coupled — they describe one buffer-layout decision
together. Splitting them into separate `stride` and `offset` fields
would let a caller set just one consistently with one VBO and the
other consistent with another, which is a non-obvious foot-gun.

Use sites pull apart into two phases. demo21:

```python
# Old:
paddle1_vao, paddle1_count = make_colored_vao(paddle_vertices, paddle1_color)
paddle2_vao, paddle2_count = make_colored_vao(paddle_vertices, paddle2_color)

# New:
paddle_pos_vbo    = make_vbo(paddle_vertices)
paddle1_color_vbo = make_vbo(paddle1_color)
paddle2_color_vbo = make_vbo(paddle2_color)
paddle1_vao = make_vao([
    AttribSpec(vbo=paddle_pos_vbo,    location=0, size=3, layout=(0, 0)),
    AttribSpec(vbo=paddle1_color_vbo, location=1, size=4, layout=(0, 0)),
])
paddle2_vao = make_vao([
    AttribSpec(vbo=paddle_pos_vbo,    location=0, size=3, layout=(0, 0)),
    AttribSpec(vbo=paddle2_color_vbo, location=1, size=4, layout=(0, 0)),
])
```

→ One pos VBO instead of two; both paddles read from it. Same for
square. demo21 drops from 6 to 4 VBOs.

demo22 mostly doesn't change shape (already efficient) but reads
better — `cube_solid_vbo` and `cube_solid_vao` are visibly separate
objects so the "this VAO can also be used by the position-only
shadow-depth pipeline" sharing becomes legible at the source level.
demo22's interleaved layout becomes:

```python
cube_solid_vbo = make_vbo(_build_cube_solid())
STRIDE = 32  # 8 floats * 4 bytes
cube_solid_vao = make_vao([
    AttribSpec(vbo=cube_solid_vbo, location=0, size=3, layout=(STRIDE, 0)),   # pos
    AttribSpec(vbo=cube_solid_vbo, location=1, size=3, layout=(STRIDE, 12)),  # normal
    AttribSpec(vbo=cube_solid_vbo, location=2, size=2, layout=(STRIDE, 24)),  # uv
])
```

`_pipeline.py` gets the same split. Visualization demos consume the
same way.

### Move 3: Sweep `glBindVertexArray(0)` and audit draw paths

Once Move 1 is in, do a final sweep for any remaining
`glBindVertexArray(0)` calls and replace with the explicit default-VAO
bind (or just delete if the next draw will bind something specific).
Verify every `glDraw*` site has a `glBindVertexArray(non-zero)` upstream
in the same frame.

This is mechanical cleanup but worth doing as a separate step so it's
reviewable in isolation.

## Sequencing

1. **Move 1 in `mvpVisualization/_pipeline.py` + every
   `mvpVisualization/<demo>/<demo>.py`** — Bill verifies on macOS.
   Smallest change, biggest user-visible impact.
2. **Move 1 in demo21 and demo22** — same change, curriculum
   side. Doesn't unblock anything currently broken on Bill's Linux
   box but keeps the conventions consistent.
3. **Move 2 in `_pipeline.py` first** (one shared helper, multiple
   demos benefit) — verify visualizers still render.
4. **Move 2 in demo21** (smaller surface, paddle dedup is the
   visible win).
5. **Move 2 in demo22** (largest surface but mostly mechanical —
   no dedup wins, just clearer separation).
6. **Move 3** as a cleanup pass.

## What this does NOT touch

- v4 / v7 SuperBible ports. Those follow upstream's structure on
  purpose. The `_sb6m.Object.render()` path has its own VAO management
  inside the loader; out of scope.
- Index buffers (EBOs). The curriculum doesn't use them yet; if/when
  it does, extend `make_vao` to take an EBO parameter.
- DSA (`glCreateVertexArrays`, `glVertexArrayAttribFormat`). Curriculum
  is GL 3.3-Core, can't use 4.5+ APIs.

## Stacks with `#41` (pipeline dataclasses)

`#41` groups *programs + uniforms* into dataclasses; this plan groups
*meshes*. Doing this plan first means each pipeline dataclass already
knows which VAO to draw with. Doing `#41` first means the pipeline
dataclass has a place to hang its "default VAO for this pipeline"
field. Either order works; expect a 2-line touch-up to the dataclasses
once both are in.

## Decisions locked in (2026-05-01, with Bill)

1. **`AttribSpec` dataclass** with a `(stride, offset)` tuple field for
   the buffer layout coupling. Not raw 5-tuples.
2. **Inline default-VAO bind + `# macOS Core Profile`-style comment**
   in every demo entry point. `_pipeline.py` gets the same pattern.
3. `make_vao` takes a flat list of `AttribSpec`; one entry per
   shader attribute, regardless of whether multiple attribs share a
   VBO. The shared-VBO case shows up naturally as repeated `vbo=…` in
   the spec list.

## Sequencing (locked)

Phase A — macOS unblock:
1. ✅ **`mvpVisualization/_pipeline.py`** + 6 visualization demos
   (2026-05-01). Default-VAO bind added in `setup_window`; all 22+
   `glBindVertexArray(0)` calls along that path removed.
   **Verified working on Bill's macOS box.**
2. ✅ **`demo21.py` and `demo22.py`** (2026-05-01). Default-VAO bind
   inline, all 17 `BindVertexArray(0)` calls removed. The demo22
   L1239 workaround now binds `_default_vao` with a cleaner comment
   instead of "reuse cube VAO to satisfy core profile."

Phase B — conceptual refactor:
3. ✅ **`mvpVisualization/_pipeline.py`** (2026-05-01). `AttribSpec`
   dataclass + `make_vbo` + `make_vao(attribs)` added; existing
   `make_triangle_vao` / `make_lines_vao` rewritten as thin wrappers
   around them; the perspective demo's bespoke `_build_frustum_vao`
   migrated. Visualizers verified working on Linux + macOS.
4. ✅ **`demo21.py`** (2026-05-01). New primitives at module scope;
   `_color_array` and `_build_ground_vertices` factored out;
   `paddle1_vao` and `paddle2_vao` now share `paddle_pos_vbo`.
   VBO count: 7 → 6. Verified working on Linux + macOS.
5. ✅ **`demo22.py`** (2026-05-01). New primitives at module scope;
   the all-in-one `make_vao(vertex_data)` replaced by
   `_make_interleaved_mesh(vertex_data)` (a small wrapper around
   `make_vbo` + `make_vao(_interleaved_attribs(vbo))`). All 5 mesh
   sites migrated. No deduplication win but the
   AttribSpec-with-pinned-locations form makes the position/normal/uv
   layout legible at the source level.

Phase C — sweep:
6. ✅ **Final audit (2026-05-01).** Zero real `glBindVertexArray(0)`
   calls remain in the in-scope tree (curriculum demos +
   `mvpVisualization`); only teaching comments mention the unbind.
   All 38 `glDraw*` sites in scope verified to have a non-zero
   `glBindVertexArray(...)` upstream in the same function. Removed
   unused `all_vaos`/`all_vbos` registries from demo22 (they were
   dead code — demo22 doesn't have a GL-cleanup-before-terminate
   pass, unlike demo21). All three phases complete.
