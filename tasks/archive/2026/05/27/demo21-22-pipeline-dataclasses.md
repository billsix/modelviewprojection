# Refactor demo21 / demo22 — group pipeline state into dataclasses

**Status: complete — ported into master 2026-05-27** (the dataclass-grouped
pipeline state landed in `demo21.py`/`demo22.py` via the claudeCode pull; my
`on_key`→`windowing` and `light_dir_ws`→`shading` extractions re-applied on top).
Originally done 2026-05-01 on claudeCode, verified by Bill on Linux + macOS;
re-verify on master at leisure (GL/display, not runnable in the container).
The v7 aside below is just context — the dataclass refactor is **not** applied
to v7.

## Decisions made (2026-05-01, with Bill)

1. Keep the `u_` prefix on uniform fields (e.g. `triangle.u_mvp`).
2. Don't pin attribute locations via `layout(location=N)` qualifiers
   in shaders -- out of scope.
3. Preserve the `_using_shadow_map` flag in demo22 -- regrouping
   only, not control-flow rewriting.

## What landed

- **demo21**: 11 ungrouped globals (`triangle_program`, `u_triangle_mvp`,
  `triangle_attr_position`, `triangle_attr_color`, `ground_program`,
  `u_ground_mvp`, `ground_attr_position`) → 2 frozen dataclasses
  (`TrianglePipeline`, `GroundPipeline`) with builders
  (`_build_triangle_pipeline`, `_build_ground_pipeline`) and
  module-level instances (`triangle`, `ground`).
- **demo22**: ~30 ungrouped globals → 4 frozen pipeline dataclasses
  (`MainPipeline`, `ShadowDepthPipeline`, `BlockShadowPipeline`,
  `ShadowViewPipeline`) and one resources dataclass
  (`ShadowResources` for the FBO + 2 textures), with builders and
  instances (`main`, `shadow_depth`, `block_shadow`, `shadow_view`,
  `shadow_res`). Fixed two automation bugs along the way:
  double-prefixing inside dotted names (`block_shadow.main.u_*`
  collapsed back to `block_shadow.u_*`) and kwarg-name rewrites
  inside constructors (reverted with a small Python script). Final
  verification: zero remaining bare uses of any of the 30 old
  globals.

## Why

Demo21 and demo22 currently keep every per-pipeline piece of GL state at
module scope as individual `program: int`, `u_mvp: int`, `u_model: int`,
`u_flat: int`, … globals. Demo22 has **three** shader pipelines side by
side (`program` for the main lit pass, `block_shadow_program` for the
shadow-mapped pass, plus `shadow_depth_program` and
`shadow_view_program` for shadow-map generation and visualization), each
with its own fan of `u_bs_*` / `u_shadow_depth_*` / `u_sv_*` prefixes —
roughly **30 program/uniform globals** before the first frame is even
drawn.

The grouping is already conceptual ("these go with the block-shadow
pipeline, those go with the shadow-depth pipeline"), the prefix naming
is doing the work a struct should be doing. A dataclass per pipeline
would:

- Cut the count of module-level identifiers by ~5×.
- Make the relationship between a program and its uniform locations
  explicit instead of conventional (no more "is `u_bs_mvp` part of
  `block_shadow_program`?  yes, by prefix convention, sort of").
- Localize "I changed shader uniforms — where do I look?" to one
  dataclass definition instead of a scan of the file.
- Match the curriculum style: by demo21, students already know
  `@dataclass` from `mathutils.InvertibleFunction`. Continuing to use
  dataclasses for grouped state is consistent with the rest of the
  course, *not* introducing a new abstraction.

The constraint Bill set: **even if there's only one instance** of the
dataclass, that's fine — the goal is grouping, not multi-instancing. Don't
"upgrade" this to classes-with-methods; keep them plain data containers.

## Scope

**In scope:**

- `/mvp/src/modelviewprojection/demo21/demo21.py`
- `/mvp/src/modelviewprojection/demo22/demo22.py`

**Not in scope:**

- Demo01–20: no shader pipelines or only trivial ones; no win.
- The book chapters: dataclass refactor is curriculum-internal, not a
  pedagogical concept. Don't rewrite `book/docs/ch21.rst` /
  `ch22.rst`.
- Other ports (`/mvp/ports/openglsuperbiblev4`,
  `/mvp/ports/openglsuperbiblev7`): different style, those are
  faithful-translation ports of external books.

## Proposed shape

For each shader pipeline, one frozen=False dataclass that owns the
program id and its uniform locations. Initialize once at module load
the same way the globals do today; instances live at module scope.

### demo21 — two pipelines

Currently:

```python
triangle_program: int = compile_program("triangle.vert", "triangle.frag")
u_triangle_mvp: int = GL.glGetUniformLocation(triangle_program, "mvpMatrix")
triangle_attr_position: int = GL.glGetAttribLocation(triangle_program, "position")
triangle_attr_color: int = GL.glGetAttribLocation(triangle_program, "color_in")

ground_program: int = compile_program("ground.vert", "ground.frag")
u_ground_mvp: int = GL.glGetUniformLocation(ground_program, "mvpMatrix")
ground_attr_position: int = GL.glGetAttribLocation(ground_program, "position")
```

Becomes:

```python
@dataclass
class TrianglePipeline:
    program: int
    u_mvp: int
    attr_position: int
    attr_color: int

@dataclass
class GroundPipeline:
    program: int
    u_mvp: int
    attr_position: int

triangle = TrianglePipeline(
    program := compile_program("triangle.vert", "triangle.frag"),
    GL.glGetUniformLocation(program, "mvpMatrix"),
    GL.glGetAttribLocation(program, "position"),
    GL.glGetAttribLocation(program, "color_in"),
)

ground = GroundPipeline(
    program := compile_program("ground.vert", "ground.frag"),
    GL.glGetUniformLocation(program, "mvpMatrix"),
    GL.glGetAttribLocation(program, "position"),
)
```

Use sites change `u_triangle_mvp` → `triangle.u_mvp`, etc.

### demo22 — four pipelines

The file already has four implicit pipelines. Make them explicit:

- `MainPipeline` (`program`, the 9 main `u_*` uniforms) — the lit + textured pass that does NOT consume a shadow map.
- `BlockShadowPipeline` (`block_shadow_program`, the 11 `u_bs_*` uniforms) — same scene draws but consuming the shadow map.
- `ShadowDepthPipeline` (`shadow_depth_program`, `u_shadow_depth_lightMVP`) — depth-only render from the light's POV.
- `ShadowViewPipeline` (`shadow_view_program`, `u_sv_depth_tex`) — fullscreen quad sampling the depth texture for debug overlay.

Plus a separate **`ShadowResources`** dataclass that owns the FBO and
two depth-map textures (`shadow_fbo`, `shadow_depth_tex`,
`shadow_debug_tex`) — these are not pipeline state but they cluster
with the shadow code and are currently scattered across module scope.

Use sites are mostly inside `set_mvp_uniforms()`, `draw_floor()`,
`draw_cube()`, and `render_shadow_map()`. The `_using_shadow_map` flag
gates which pipeline's uniform-setting branch runs, so the rename
pattern is mechanical: `u_bs_mvp` → `block_shadow.u_mvp`.

## Sequencing

1. **demo21 first** — smaller surface (2 pipelines, ~12 globals). Land
   it, verify it still runs, capture lessons (does the walrus pattern
   above read well? does Bill prefer `triangle.program` or shorter
   names like `triangle.prog`?).
2. **demo22** — apply the agreed-on shape to all four pipelines and the
   shadow resources. Don't merge with the demo21 refactor; smaller PRs
   are easier to read and revert if a convention turns out wrong.

## What this is NOT

- Not a behavior change. No new uniforms, no new draw modes, no FBO
  format changes. Just regrouping existing state.
- Not a "use OOP" push. The dataclasses stay `@dataclass`, no methods.
  The free functions (`draw_floor`, `draw_cube`, `set_mvp_uniforms`)
  stay free functions. Bill's "mistake-driven, procedural by default"
  curriculum style is preserved.
- Not a generalization to other demos. Demo01–20 stay as they are.

## Open questions for Bill

1. **Naming**: `triangle.u_mvp` (keep the `u_` prefix as a hint that
   this is a uniform location) or `triangle.mvp` (shorter, but loses
   the hint)? The current globals all use `u_*`, suggesting the prefix
   is load-bearing for the curriculum. Recommend keeping it.
2. **Attribute locations**: in demo21 the attribute locations
   (`triangle_attr_position`, `ground_attr_position`) are part of the
   pipeline group. Should they be queried (current behavior) or pinned
   via `layout (location = 0)` qualifiers in the shaders? Pinning
   removes the need to track them at all. Out of scope for this plan,
   but worth flagging.
3. **`_using_shadow_map` flag in demo22**: today this gates whether
   `set_mvp_uniforms` writes to the main pipeline's uniforms or the
   block-shadow pipeline's. Should the dataclass refactor preserve
   that branch, or is this the right moment to split into
   `set_main_uniforms()` / `set_block_shadow_uniforms()`? Recommend
   preserving — the goal is regrouping, not rewriting control flow.
