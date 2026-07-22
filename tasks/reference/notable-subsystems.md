# mvp notable subsystems

**Reference document** — deep notes on mvp's architecturally-distinct subsystems (software rasterizer, Cayley-graph engine, math-utils/gacalc layer, game ports). Not a task; update in place. Last updated 2026-07-21.

This is the "I need to work on X and X is weird" doc. It covers the parts of modelviewprojection that are *not* self-evident from a file skim. It deliberately does **not** restate the high-level architecture (`tasks/reference/architecture-overview.md`) or the book-build pipeline (`tasks/reference/book-and-docs-pipeline.md`), and it does not duplicate `CLAUDE.md` — it goes deeper on four subsystems and one supporting one.

The through-line worth holding in your head: **mvp is a course, and gacalc (the geometric-algebra library, `github.com/billsix/geometricalgebra`) is where the math actually lives.** mvp's transforms (`translate`, `rotate`, `perspective`, …) are gacalc `InvertibleFunction`s over `Vector3`/`Vector2`, not matrices. Almost every subsystem below is "some graphics thing, but expressed in gacalc's algebra instead of the usual linear-algebra way," and that is exactly what makes them non-obvious.

---

## 1. The software rasterizer — `framebuffer/softwarerendering.py`

**What it is.** A pure-Python, CPU, one-file triangle rasterizer that fills triangles into a numpy pixel array, for the *notebook* portion of the course (it imports `IPython.display` and renders to a `PIL.Image`). It is the "how does a GPU actually decide which pixels are inside a triangle" teaching artifact, done with no GPU and no shader — the edge-function / signed-area method, expressed in geometric algebra. `framebuffer/__init__.py` is **empty** (namespace only); all the code is in `softwarerendering.py`.

**Key pieces.**
- `FrameBuffer` (`@dataclass`) — wraps `_framebuffer: np.ndarray` of shape `(height, width, 3)` `uint8`. Note `__post_init__` fills it with `np.random.randint(...)` noise, not the clear colour — so you *see* uncleared framebuffer as static until `clear_framebuffer()` runs (a deliberate teaching visual). `.framebuffer` property hands back a `PIL.Image`; `show_framebuffer()` displays it inline in Jupyter.
- Three orientation predicates: `is_counter_clockwise(v1, v2)`, `is_clockwise(v1, v2)`, `is_parallel_and_same_orientation(v1, v2)`.
- `draw_filled_triangle(p1, p2, p3, color)` — the rasterizer proper.
- `screenspace_to_framebuffer(v)` / `set_color(v, color)` — coordinate conversion and the single pixel write.

**Non-obvious design points.**

- **The "cross product" is a gacalc wedge.** `is_counter_clockwise` is literally `float((v1 ^ v2).coefficient(Bivector2.e_12)) >= 0.0`. In 2D the bivector coefficient of `v1 ^ v2` *is* the signed area / 2D cross product / `|v1||v2|sin θ`. The code uses it **unnormalized on purpose** — dividing by magnitudes wouldn't change the sign but would blow up when a vector is zero (a pixel sitting exactly on a triangle vertex). This is the same wedge-as-signed-area idea as `mathutils.sine` (§3).

- **Boundary pixels are lit for either winding, by construction.** Both `is_counter_clockwise` (`>= 0`) and `is_clockwise` (`<= 0`) include the *zero-cross* (collinear / on-edge) case. So the fill test `if all(counter_clockwise_values) or all(clockwise_values)` lights a pixel whenever it's on the same side of all three edges **for CW-wound OR CCW-wound triangles**, and a pixel exactly on an edge/vertex (cross == 0 there) counts as both → it gets drawn regardless of winding. That is why the rasterizer needs no "which way is this triangle wound" branch.

- **Degenerate-triangle guard.** Before the fill loop: `if is_parallel_and_same_orientation(v2 - v1, v3 - v2): return`. A zero-length edge or same-direction-collinear vertices give zero area → cull instead of dividing by zero. **Gotcha:** an *anti-parallel* edge pair is also zero-area but is **not** caught here. `is_parallel_and_same_orientation` treats a zero-length vector as matching anything (returns `True`) so the guard always gets a definite answer.

- **The orientation predicates moved *here* (2026-07-09).** They used to live in `mathutils`; an audit found the rasterizer was the sole caller, so they were relocated next to their only consumer. If you're looking for them in `mathutils`, that's why they're not there.

- **Coordinate flip.** `screenspace_to_framebuffer` composes `translate((height-1)*e_2)` then `scale_non_uniform(1, -1)` — the OpenGL-style bottom-left-origin, y-up screen space to the array's top-left-origin, y-down. It uses the *same gacalc `compose`/`translate`/`scale_non_uniform`* the rest of the course uses, so the rasterizer is not a special coordinate island.

- **Iterating a `Vector2` yields its coords.** `x1, y1 = iter(self.screenspace_to_framebuffer(p1))` relies on gacalc's `__iter__` yielding coefficient values in blade order (see gacalc's "Iteration yields coefficient values" note). `set_color` reads `v.coeff_e_2` / `v.coeff_e_1` directly for the array index.

**Gotcha.** It's O(bbox area × 3 edge tests) per triangle in pure Python — fine for notebook-scale teaching images, not for anything real. `notebooksrc/framebuffer.py` is the notebook that drives it.

---

## 2. The Cayley-graph engine — `cayley/` + `mvpvisualization/cayley_gl.py`

**What it is.** The engine behind the `mvpvisualization` demos. It models the course's central lesson — *coordinate spaces connected by transforms, and you get from any space to any other by composing the transforms along a path, inverting any you walk backward* — as an **immutable directed acyclic graph** whose **edges are sequences of gacalc `InvertibleFunction`s**. Tracing a path composes the edge functions and auto-inverts against-arrow edges. This is "the chapter-02 rule, executed instead of drawn."

It is split into three layers, cleanly separated so the first two are unit-testable with **no display**:

| File | Layer | Role |
|---|---|---|
| `cayley/cayleygraph.py` | pure data + math | the graph, edges, path-tracing (BFS), orientation of steps |
| `cayley/cayleyscene.py` | pure data + math | turns a declarative `Scene` into a `Timeline` + `Animation` (per-frame transforms, imgui-tree data, 4×4 realization) |
| `mvpvisualization/cayley_gl.py` | GL/imgui | the reusable "mechanism only" GL shell (pipelines, meshes, orbit camera, loop runner, imgui widgets) |

### 2a. `cayleygraph.py` — the graph itself

- **`CayleyGraph(edges)`** — built from *all* its edges at once; **there is no `add_edge`**, the structure is immutable by design (these graphs aren't dynamically adjusted). Nodes are opaque hashables — the demos use a per-demo `enum.Enum` of coordinate spaces (`Space.world`, `Space.paddle1`, …). `node_label()` gives a readable name for an enum member or a string.
- **Acyclicity is validated at construction** via a classic 3-colour DFS (`_DfsColor.WHITE/GRAY/BLACK`), raising `ValueError` on a cycle. A cycle is rejected up front rather than looping forever when a path is later traced.
- **`Edge(src, dst, steps, realization="cpu")`** (`frozen=True`) — `steps` is a tuple of `Step`. It has a **custom `__init__`** (not `__post_init__`) so it can accept either `Step` objects or bare `(label, fn)` pairs and coerce both to `tuple[Step, ...]`, while the stored field stays typed `tuple[Step, ...]` for readers. Because it's frozen it uses `object.__setattr__`. `Edge.function()` returns `compose([s.fn for s in steps])` — **first step is outermost**, matching how the demos stack transforms. `realization` is `"cpu"` (matrix-stack, invertible) vs `"gpu"` (the projective squash that is deliberately *not* an `InvertibleFunction` — see §2b decision #4).
- **`Step`** (`@dataclass`, **not** frozen) — `label` (LaTeX-ish, e.g. `"R_z"`) + `fn` (an interpolable `InvertibleFunction`). `fn` is mutable **on purpose**: it's a transform *parameter* (the editable virtual camera rewrites it in place); the graph *structure* is what's immutable, not the numbers in a transform.
- **`_route(a, b)`** — shortest route over the *undirected* graph via BFS (acyclicity guarantees termination). This is a worked example of the CLAUDE.md "extract a phase" rule: it nests `breadth_first_parents()` (which **raises** `"no path"` from inside the search — the code that discovers unreachability reports it) and `walk_back()`, both closing over `a`/`b`. The top-level `match (a, b)` checks **both** endpoints for existence before searching, on purpose: an unknown node reported as "no path" would imply the space exists but is unreachable, when the real mistake is usually a typo'd enum member.
- **`Path`** — `oriented_steps()` yields `OrientedStep`s in reading/animation order: verbatim for a forward edge, **inverted and relabeled `^{-1}`** for an against-arrow edge. `Path.function()` composes the edge functions, inverting any against-arrow edge, with the src-incident edge innermost / dst-incident outermost (note the `reversed()`).

**Why it needs invertibility.** The whole engine *requires* `InvertibleFunction`, not just `ComposableFunction`: walking a path backward calls `inverse(s.fn)`. This is precisely the gacalc split ("mvp's Cayley-graph engine *requires* invertibility; it walks edges backward via `inverse`"). A non-invertible transform in an edge that gets walked backward is a type/runtime error, not a silent wrong answer. `inverse` also commutes with `.at(t)`, so an against-arrow edge still animates smoothly.

### 2b. `cayleyscene.py` — Scene → Timeline → Animation

This is the layer that turns *one declarative graph* into an animation, with **no hand-kept parallel structures**. Three things come out of a `Scene`:

1. the **object-placement tree** (modelspace → … → world): forward edges, animated in visit order;
2. the **toward-NDC tail**: the world→camera **inverse** (`InverseOperations`, affine, CPU — the "camera placed forward, world transforms via inverse" lesson) plus the projective squash/ortho (`NonInvertibleTransformation`, GPU/shader — **decision #4**: these steps are deliberately *not* `InvertibleFunction`s, each is just a label + time slot mapped to a shader `time` uniform);
3. the **two imgui trees**, which are just two traversal views of the same graph (`frame_tree` = "From World Space, Against Arrows, Read Bottom Up"; `ndc_tree` = "Towards NDC, With Arrows, Top Down").

- **`Timeline(scene)`** assigns every substep a `(start, dur)` slot. Slots are keyed by **`id(step)`** (`self._slot[id(s)]`) — which is why `Step` identity must be preserved when a camera rewrites `fn` in place (see `CameraControls` below). It answers per-node lifecycle questions (`axis_visible`, `geometry_visible`, `built_time`, `arrival_time`).
- **`Animation(scene, timeline)`** evaluates at a frame time: `transform(space, time)` gives the live modelspace→root transform (each substep at its own local `t` via `interp`, so a nested child rides on already-placed ancestors reading `at(1.0)`); `inverse_transform(time)` accumulates the world→camera inverse; `gpu_progress(time)` yields `(label, progress)` for the shader.
- **`CameraControls.apply()`** is the canonical "editable edge" pattern: it holds the three `Step`s of a `camera->world` edge (`[T, R_y, R_x]`) and rewrites each `step.fn` **in place** from live position/yaw/pitch, so the camera object and the world→camera inverse update together **while the Step identities (and thus the timeline slots keyed by `id`) stay valid.**
- **`interp(time, start, dur)`** — the ramp function (0 before `start`, linear to 1 over `dur`, clamped; `dur <= 0` is a step). Small and doctested; used everywhere for animation.
- **`to_matrix(f)`** — realizes an **affine** `InvertibleFunction` on `Vector3` as a 4×4 row-major numpy matrix for GL upload, by probing: columns are `f(e_i) - f(0)`, translation is `f(0)`. **Gotcha, load-bearing:** it forces `dtype=float`. gacalc coefficients can be sympy expressions (rotor magnitudes use `sympy.sqrt`), and without the cast numpy infers `dtype=object` and downstream `np.linalg.inv` / GL upload fail. **Not valid for the projective squash** (non-affine) — that stays a shader.

### 2c. `cayley_gl.py` — the GL shell (mechanism only)

- **Owns NO policy.** Explicitly the dissolution of an earlier `run(config)` god-function with feature flags. It provides reusable *mechanism*: `StandardObjects` (standard pipelines + meshes + `draw_*` helpers that read the current model matrix from `matrix_stack`), imgui widgets (`render_tree` / `gui_button`, which draw the composition operator `o` between successive buttons so a row reads as function composition), the orbit camera + input, window/menubar/fullscreen helpers, and `run_loop(...)`. The per-frame **choreography, the reveal/graying decisions, and which panels exist all live in each demo file**, not here.
- **`build_standard(...)`** builds triangle/ground/axis/cube pipelines + meshes and at most one view volume — a perspective `Frustum` OR an orthographic `RectangularPrism` (never both).
- **Import-order gotcha (documented at the top):** `glfw` + `OpenGL.GL` **must** import before `imgui_bundle`, or PyOpenGL's context tracking fails at window setup. Demos must get imgui via `cayley_gl.imgui`, not by importing `imgui_bundle` first.
- The GPU squash is injected via GLSL string concatenation, not `#include` — see `_pipeline.py` below.

### 2d. Supporting layer — `mvpvisualization/_pipeline.py`

Lower-level GL boilerplate that `cayley_gl` builds on (and that the standalone `modelview*.py` demos use directly): GLFW+imgui setup, shader compilation, VAO/VBO builders, standard mesh geometry, per-frame uniform upload, the `Pipeline` dataclass (cached uniform/attr locations), and `cleanup()`.
- **The `project_*.glsl` injection trick:** GLSL 330 has no `#include`, so `compile_program(..., project=...)` **appends** a `project_*.glsl` snippet to the vertex shader source before compiling — it supplies the body of a forward-declared `vec4 project(vec4)` that the two shared vertex shaders call. That's how each demo's projection *animation* (identity / ortho squash / perspective squash) is injected into the shared shaders.
- **M/V/P kept as three separate uniforms** (`u_m`/`u_v`/`u_p`), not a fused MVP, precisely so the stages can be shown independently — the whole pedagogical point of these demos.
- **macOS quirk (documented):** a non-zero default VAO is generated and left bound because Apple's Core Profile prohibits VAO 0 for any draw; Mesa/NVIDIA tolerate the violation, Apple does not.

**The demo progression** (`mvpvisualization/model.py` → `modelview.py` → `modelview2d.py` → `modelvieworthoprojection.py` → `modelviewperspectiveprojection.py`, plus `pushmatrix.py` and `coordinatesystems.py`) each **owns its choreography and imgui panel** and composes the `cayley_gl` mechanisms. `coordinatesystems.py` is the odd one out: **no timeline/morph** — it's the interactive explorer where every space is drawn at its full slider-driven transform and the "View From" buttons re-anchor by walking `path(world, space)` (against the placement arrows, i.e. the inverse). It's the cleanest short read for seeing the engine used end-to-end.

---

## 3. Math-utils / gacalc integration — `mathutils.py`

**What it is.** The graphics-specific math the course needs that gacalc deliberately does **not** carry. The single most important thing to know: **`mathutils` is NOT a re-export facade** (it used to be; the facade was removed). The vector algebra and the transform layer belong to gacalc, and everything imports them from gacalc **directly** — `from gacalc.g2 import Vector2`, `from gacalc.transforms import translate`, etc. `mathutils` merely imports the gacalc pieces it needs *internally*. Its `__all__` lists only the graphics math defined *here*. If you're tempted to add a `Vector3`/`translate` re-export to `mathutils`, don't — that's the anti-pattern that was removed.

**What lives here (and the non-obvious bits):**

- **`rotate` / `rotate_x` / `rotate_y` / `rotate_z` are module-level constants, not functions** — each is the result of calling gacalc's `plane_rotation(a, b, ...)` once at import. `plane_rotation` derives the rotation plane once (normalized wedge → unit bivector, cached in the closure); each `rotate(theta)` call then just assembles the half-angle rotor and sandwiches. Binding them per-call would re-derive the plane every time. So `rotate` is `Callable[[float], InvertibleFunction[Vector2]]`. The `rotate_*` naming maps to planes: `rotate_x` carries `e_2→e_3` (x axis fixed), `rotate_y` carries `e_3→e_1`, `rotate_z` carries `e_1→e_2`. **This is the sanctioned rotation API** — user code never hand-builds a rotor (see gacalc's "express rotations as `plane_rotation`" convention).
- **`rotate_around(angle, center)`** — `compose([translate(center), rotate(angle), translate(-center)])`; read right-to-left.
- **`cosine(v1, v2)` / `sine(v1, v2)` / `abs_sin(v1, v2)`** — angle helpers built on gacalc. `cosine` is the dot product normalized by both magnitudes (returns `nan`, not `ZeroDivisionError`, for a zero vector). `sine` is **signed** (2D): it reads the bivector coefficient of `v1 ^ v2` — "|v1||v2|sin θ IS the 2D wedge," the same signed-area fact the rasterizer uses. `abs_sin` is the 3D **unsigned** counterpart (`|a ^ b|` = area of the spanned bivector), unsigned because 3D has no single turn direction.
- **`find_normal(p1, p2, p3)`** — surface normal via GA: the cross product is the **dual of the wedge**, `a × b = (a ∧ b)*`. Wedge the two edge vectors into a bivector, take `.dual()`. Result is **not normalized** — its length is *twice the triangle area*. CCW winding (matching OpenGL `GL_CCW`) gives an outward normal; reversing winding flips it (how a renderer tells front from back). Rebuilds an explicit `Vector3(coeff_e_1=…)` from `n.coefficient(...)` to force plain floats.
- **`plane_equation(p1,p2,p3) -> (unit_normal, d)`** and **`distance_to_plane(point, plane)`** — the plane through three points as `n·P + d = 0`; distance is signed (which side the normal points toward), used by a clipper to keep/cut/discard.
- **`ortho(...)` and `perspective(...)`** — return `InvertibleFunction[Vector3]`. `ortho` is affine (`Linearity.AFFINE`). **`perspective` is `Linearity.NONLINEAR`** and provides an explicit `f_inv`: the perspective divide is *not* representable as a single affine matrix, so it is not recoverable by point-probing (`to_matrix` would silently produce garbage — this is why it must stay a shader in the Cayley engine). Its inverse un-scales by the *camera-space* z. `cs_to_ndc_space_fn` is the course's standard perspective preset.
- **`FunctionStack` + `push_transformation` + module-global `fn_stack`** — the Python analogue of OpenGL's matrix stack, but a stack of `InvertibleFunction`s. `modelspace_to_ndc_fn()` composes the whole stack; an empty stack composes to identity. `push_transformation` is a context manager whose `finally` pops **even if the block raises**, so a failed draw can't leave the stack unbalanced for every later frame.

**The `m`/`b` teaching-naming convention (protected).** gacalc's `translate(b=...)` and `uniform_scale(m=...)` are named for `f(x) = m*x + b` — `b` the intercept/shift, `m` the slope/stretch — so a student meets transforms through an equation they already know. **Do not "improve" these to `offset`/`factor`,** and call them by keyword in teaching code. This is enforced in gacalc; `mathutils` and the demos are downstream consumers of it.

**Note:** there is a *separate* legacy `matrix_stack.py` (`ms`) that is an actual **numpy-4×4 matrix** stack (`MatrixStack.model/view/projection`, `push_matrix`, `ortho`, `perspective`, `rotate_x`, `translate`, …). The GL demos drive *that* one for uniform upload; `mathutils.FunctionStack` is the `InvertibleFunction` analogue used in the algebra-first parts. Don't confuse the two — `ms.perspective` mutates a matrix on a stack; `mathutils.perspective` returns an `InvertibleFunction`.

---

## 4. The game ports — `ports/`

Two independent porting projects, both kept under `ports/` (not in the curriculum proper) because they are *faithful translations*, not re-pedagogizations of Bill's arc. They exist so students can read real graphics code in the second half of the course.

### 4a. `ports/codetheclassics/` — PyGame Zero → GLFW/OpenGL 3.3

**What it is.** Ports of the *Code the Classics* games (Raspberry Pi Press) from PyGame Zero to the GLFW + OpenGL 3.3 core stack the course ends on. Vol 1: boing, cavern, myriapod, bunner, soccer. Vol 2: eggzy, avenger, beatstreets, kinetix, leadingedge.

**The porting convention.** Each ported game is a **near-verbatim / byte-faithful copy of the original**; the only change is the import line — `from pgzero_gl import *` replaces `import pygame, pgzero, pgzrun` (plus a `sys.path` bootstrap). The whole trick is `pgzero_gl/`, a **compatibility shim** that reimplements the exact slice of the PyGame Zero API the games use.

**How the shim works (`pgzero_gl/`).**
- It provides the same magic globals PyGame Zero injects — `Actor`, `screen`, `keyboard`, `keys`, `sounds`, `music`, `images`, `Rect`, `mixer`, `go` — via `pgzero_gl/__init__.py`'s `*` export. **Vectors come from gacalc directly**, not re-exported by the shim (same rule as `mathutils`).
- It reproduces PyGame Zero's **top-left-origin, y-down pixel coordinate system** with an orthographic projection and draws every sprite as a textured quad, so the game's original pixel coordinates work unchanged.
- **Two interchangeable renderer backends, same picture:** `renderer.py` (default, GL 3.3 core + shaders — one program does sprites *and* flat primitives, switched by a `uUseTex` uniform × `uTint`) and `renderer_gl1.py` (fixed-function OpenGL 1.x, `glOrtho` + `glBegin/glEnd`, the demo19 era), selected with `PGZERO_GL=1`. Rationale: the 1.x path is the exact fixed-function era the book introduces, and runs on old/software/compat-only GL.
- `resources.py` — the important subtlety: images **decode to CPU RGBA immediately** (so `width`/`height`/masks work before the window exists — game objects are built at import time) but **upload their GL texture lazily on first draw** (the GL context doesn't exist yet at import).
- `runner.py` `go()` — reads `WIDTH`/`HEIGHT`/`TITLE`/`update`/`draw`/`on_*` from the calling game module, opens the window, runs a **fixed 60 Hz** loop.
- `audio.py` — `sounds`/`music` via `just_playback` (miniaudio), **best-effort**: silently no-ops with no audio device, like the originals. The `_MixerSound` wrapper pools decoded sounds by path and applies volume *per play* — because avenger constructs a `mixer.Sound` per distance-attenuated shot, and a naive one-Sound-per-call would leak miniaudio streams.

**Headless verification.** `_smoketest.py <game>` renders one frame to an offscreen EGL pbuffer (Mesa llvmpipe, no display/GPU), writes a PNG, and **exits non-zero if the frame is mostly black** — doubles as a CI guard. Env vars: `PGZERO_GL_INFO=1`, `PGZERO_MAX_FRAMES=N`.

**Licensing gotcha (real).** The upstream repos have **no license** → default all-rights-reserved. Original code/graphics/audio are © Raspberry Pi Press. These ports are included for educational use on Bill's authorization (2026-06-24); every file carries an attribution header. **If this tree is ever published, confirm redistribution permission with Raspberry Pi Press first.** (The `pgzero_gl` *shim itself* is Bill's clean-room LGPL-2.1 reimplementation — separate from the games.)

### 4b. `ports/openglsuperbiblev4/` — C++ SuperBible → Python

**What it is.** A faithful Python translation of the demos in *OpenGL SuperBible, 4th Ed.* (Wright, 2007), laid out mirroring the original tree (`chaptNN/<demo>/<demo>.py`), so students read line-for-line Python alongside the book's C++ without learning C++.

**Porting convention: mechanical and uniform.** GLUT → GLFW polling loop; GLUT menus/text → `imgui_bundle`; `glutSolidSphere` etc. → inline `glBegin`/`glEnd`; `M3DVector3f` → numpy or `Vector3D`; `m3dFindNormal` etc. → inline helpers. **Fixed-function stays fixed-function** — when SuperBible uses `glPushMatrix`/`glRotatef`/`glBegin`, the port does the same. Shader-era chapters (15+) keep the `.vs`/`.fs` filenames from the book. One self-contained script per demo; each prepends a Wayland workaround (`PYOPENGL_PLATFORM=x11`).

**Two shared support modules (note the leading underscore — not demos):**
- **`_primitives.py`** — precomputed procedural geometry (sphere, torus, ground, cone). The point: several ports re-ran their `sin`/`cos` tessellation *inside the per-frame draw*; the geometry is identical every frame, so this runs the trig **once** and replays stored vertices. **Bill's constraint (2026-05-28): no display lists or VBOs unless the C++ source already used them** — so it stays immediate-mode `glBegin`/`glEnd`; only *when* the trig runs changes, not *how* it draws. Depends only on `math` + `OpenGL.GL` (no glfw/imgui) so minimal demos can import it without the window machinery.
- **`_common.py`** — the window/UI machinery: window sizing, imgui setup, `WindowState` (fullscreen toggle), menubar, and a unified walk-around/orbit `Camera` (`position` + `rot_y` + `rot_x` — **Bill's terminology, NOT yaw/pitch**; set `focus_index >= 0` for orbital mode).

**Distinct from Code the Classics:** the SuperBible ports are *translations of a third-party book's C++*; the pgzero ports are *translations of third-party games' Python*. Neither uses the gacalc/Cayley idiom — they're faithful to their sources, which is the whole point of keeping them under `ports/`. (Some demo names — Block, sphereworld, atom, solar — appear in *both* the SuperBible ports and Bill's curriculum demos, with different intent; don't conflate them.)

---

## Cross-cutting gotchas

- **gacalc is a hard dependency (`github.com/billsix/geometricalgebra`).** Its generated modules (`g1.py`/`g2.py`/`g3.py`/`scalar.py`) are gitignored and produced by its generator. If `from gacalc.g2 import Vector2` fails, gacalc hasn't been generated/installed — that's a gacalc-side `make generate`, not an mvp bug.
- **Don't re-add facades.** Both `mathutils` and `pgzero_gl` had re-export facades that were deliberately removed; imports now say what they mean (`from gacalc… import`). Adding a convenience re-export re-introduces the anti-pattern.
- **Two stacks, two meanings.** `mathutils.FunctionStack` (composes `InvertibleFunction`s) vs `matrix_stack.py` / `ms` (composes numpy 4×4s). The Cayley GL shell drives the numpy one for uniform upload; the algebra-first material uses the function one.
- **The `id(step)`-keyed timeline** means Step identity is load-bearing: mutate a `Step.fn` in place (the editable-camera pattern), never replace the `Step` object, or its timeline slot is lost.
